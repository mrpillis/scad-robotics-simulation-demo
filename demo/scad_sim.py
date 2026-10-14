"""Shared toolkit for the SCAD Robotics Simulation Demo.

Everything the numbered demos need lives here so each demo file can stay short
enough to read aloud in class:

* ``Rover``        – wraps the MuJoCo model and turns raw sensordata into named readings
* controllers      – differential-drive kinematics, go-to-goal, lidar obstacle avoidance
* perception       – a tiny camera pipeline that finds the orange goal beacon
* ``Views``        – off-screen cameras (RGB + depth) and the sensor dashboard
* ``randomize``    – domain randomization for the sim-to-real discussion
* ``run_viewer``   – the interactive, real-time MuJoCo window used live in class

Only MuJoCo, NumPy, OpenCV and imageio are required.
"""

from __future__ import annotations

import math
import os
from functools import lru_cache
import platform
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Pick a headless OpenGL backend automatically when there is no display (servers, CI).
if platform.system() == "Linux" and not os.environ.get("DISPLAY") and "MUJOCO_GL" not in os.environ:
    os.environ["MUJOCO_GL"] = "egl"

import cv2
import imageio.v2 as imageio
import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUTPUT = HERE / "output"
SCENE = ASSETS / "scad_lab.xml"

BRAND = "SCAD  ×  Simulation for Robotics"
BRAND_SUB = "D. Pillis  ·  Robotics Professor Demo  ·  Savannah College of Art & Design"
GOLD = (33, 173, 237)  # BGR for OpenCV drawing (warm gold)
INK = (24, 22, 20)

# Rover geometry, matching scad_lab.xml
WHEEL_RADIUS = 0.07
TRACK_HALF = 0.135
MAX_WHEEL = 14.0  # rad/s
N_BEAMS = 15
BEAM_ANGLES = np.deg2rad(np.linspace(-105, 105, N_BEAMS))
LIDAR_MAX = 4.0


def ensure_output() -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    return OUTPUT


def load(path: Path | str = SCENE) -> tuple[mujoco.MjModel, mujoco.MjData]:
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return model, data


# --------------------------------------------------------------------------- sensing
@dataclass
class Readings:
    t: float
    x: float
    y: float
    yaw: float
    enc_left: float
    enc_right: float
    accel: np.ndarray
    gyro: np.ndarray
    bumper: float
    lidar: np.ndarray  # metres, LIDAR_MAX where nothing was hit
    extras: dict = field(default_factory=dict)


class Rover:
    """Named access to the rover's actuators and sensors.

    ``noise`` and ``latency_steps`` let the sim-to-real demo make the sensors
    behave more like real hardware.
    """

    def __init__(self, model, data, noise: float = 0.0, latency_steps: int = 0, seed: int = 0):
        self.m, self.d = model, data
        self.noise = noise
        self.latency_steps = latency_steps
        self.rng = np.random.default_rng(seed)
        self._queue: list[np.ndarray] = []
        self.goal_id = model.body("goal").mocapid[0]

    # -- actuation ---------------------------------------------------------
    def drive(self, v: float, w: float) -> tuple[float, float]:
        """Differential drive: body speed v (m/s) and turn rate w (rad/s) -> wheel speeds."""
        left = (v - w * TRACK_HALF) / WHEEL_RADIUS
        right = (v + w * TRACK_HALF) / WHEEL_RADIUS
        scale = max(1.0, abs(left) / MAX_WHEEL, abs(right) / MAX_WHEEL)
        left, right = left / scale, right / scale
        cmd = np.array([left, right])
        if self.latency_steps:
            self._queue.append(cmd)
            cmd = self._queue.pop(0) if len(self._queue) > self.latency_steps else np.zeros(2)
        self.d.ctrl[:2] = cmd
        return float(left), float(right)

    # -- goal ----------------------------------------------------------------
    @property
    def goal(self) -> np.ndarray:
        return self.d.mocap_pos[self.goal_id][:2].copy()

    def set_goal(self, x: float, y: float) -> None:
        self.d.mocap_pos[self.goal_id][:2] = (x, y)

    # -- sensing -------------------------------------------------------------
    def read(self) -> Readings:
        s = lambda name: self.d.sensor(name).data.copy()  # noqa: E731
        q = s("gt_quat")
        yaw = math.atan2(2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * (q[2] ** 2 + q[3] ** 2))
        pos = s("gt_pos")
        lidar = np.array([self.d.sensor(f"lidar_{i:02d}").data[0] for i in range(N_BEAMS)])
        lidar = np.where((lidar < 0) | (lidar > LIDAR_MAX), LIDAR_MAX, lidar)
        r = Readings(
            t=self.d.time, x=pos[0], y=pos[1], yaw=yaw,
            enc_left=float(s("enc_left")[0]), enc_right=float(s("enc_right")[0]),
            accel=s("imu_accel"), gyro=s("imu_gyro"), bumper=float(s("bumper")[0]), lidar=lidar,
        )
        if self.noise:
            n = self.noise
            r.x += self.rng.normal(0, 0.02 * n)
            r.y += self.rng.normal(0, 0.02 * n)
            r.yaw += self.rng.normal(0, 0.03 * n)
            r.accel = r.accel + self.rng.normal(0, 0.3 * n, 3)
            r.gyro = r.gyro + self.rng.normal(0, 0.05 * n, 3)
            r.lidar = np.clip(r.lidar + self.rng.normal(0, 0.03 * n, N_BEAMS), 0.0, LIDAR_MAX)
        return r


# --------------------------------------------------------------------------- control
def wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


def go_to_goal(r: Readings, goal: np.ndarray, v_max: float = 0.6) -> tuple[float, float]:
    """Proportional controller: turn toward the goal, slow down while turning and on arrival."""
    dx, dy = goal[0] - r.x, goal[1] - r.y
    dist = math.hypot(dx, dy)
    heading_err = wrap(math.atan2(dy, dx) - r.yaw)
    w = 2.5 * heading_err
    v = v_max * min(1.0, dist / 0.6) * max(0.0, math.cos(heading_err))
    return v, w


class OccupancyMap:
    """A 2-D occupancy grid built *only* from lidar hits (mapping, the "M" in SLAM).

    Pose comes from the simulator here; on a real robot it would come from
    odometry + localisation, which is exactly where sim and reality start to differ.
    """

    def __init__(self, half: float = 3.1, res: float = 0.05, robot_radius: float = 0.26):
        self.half, self.res = half, res
        self.n = int(round(2 * half / res))
        self.evidence = np.zeros((self.n, self.n), np.int16)  # + when a beam ends here, - when it passes through
        self.hits = np.zeros((self.n, self.n), np.uint8)
        r = int(math.ceil(robot_radius / res))
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        self.cost = np.zeros_like(self.hits)

    def cell(self, x: float, y: float) -> tuple[int, int]:
        i = int(np.clip((y + self.half) / self.res, 0, self.n - 1))
        j = int(np.clip((x + self.half) / self.res, 0, self.n - 1))
        return i, j

    def xy(self, i: int, j: int) -> tuple[float, float]:
        return (j + 0.5) * self.res - self.half, (i + 0.5) * self.res - self.half

    def update(self, r: Readings) -> None:
        """Add one lidar scan. Cells where beams end gain evidence, cells beams pass through lose it,
        so noisy one-off hits fade instead of cluttering the map."""
        ox = r.x + 0.08 * math.cos(r.yaw)
        oy = r.y + 0.08 * math.sin(r.yaw)
        o = self.cell(ox, oy)
        passed = np.zeros((self.n, self.n), np.uint8)
        ends = []
        for a, dist in zip(BEAM_ANGLES, r.lidar):
            e = self.cell(ox + dist * math.cos(r.yaw + a), oy + dist * math.sin(r.yaw + a))
            cv2.line(passed, (o[1], o[0]), (e[1], e[0]), 1, 1)
            if dist < LIDAR_MAX - 1e-3:
                ends.append(e)
        self.evidence -= passed.astype(np.int16)
        for e in ends:
            self.evidence[e] += 3
        np.clip(self.evidence, 0, 30, out=self.evidence)
        self.hits = (self.evidence >= 4).astype(np.uint8)
        self.cost = cv2.dilate(self.hits, self.kernel)

    def plan(self, start, goal) -> list[tuple[float, float]]:
        """A* over the inflated grid (8-connected). Returns waypoints in metres, or [] if no path."""
        import heapq

        s, g = self.cell(*start), self.cell(*goal)
        blocked = self.cost.astype(bool).copy()
        # the robot may already sit inside an inflated zone (e.g. next to a wall): free a small bubble
        cv2.circle(blocked.view(np.uint8), (s[1], s[0]), 4, 0, -1)
        blocked[g] = False
        steps = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
        h = lambda c: math.hypot(c[0] - g[0], c[1] - g[1])  # noqa: E731
        openq = [(h(s), 0.0, s)]
        came = {s: None}
        best = {s: 0.0}
        while openq:
            _, cost, c = heapq.heappop(openq)
            if c == g:
                break
            if cost > best.get(c, 1e9):
                continue
            for di, dj, w in steps:
                nb = (c[0] + di, c[1] + dj)
                if not (0 <= nb[0] < self.n and 0 <= nb[1] < self.n) or blocked[nb]:
                    continue
                nc = cost + w
                if nc < best.get(nb, 1e9):
                    best[nb] = nc
                    came[nb] = c
                    heapq.heappush(openq, (nc + h(nb), nc, nb))
        if g not in came:
            return []
        path, c = [], g
        while c is not None:
            path.append(self.xy(*c))
            c = came[c]
        return path[::-1]


class Navigator:
    """Sense -> map -> plan -> act, the classic autonomy loop.

    10 Hz      : each lidar scan updates the occupancy map
    every 0.25 s: A* re-plans a path to the goal on the inflated map
    every step : pure pursuit steers at a point 0.4 m along the path;
                 a lidar safety check and the bumper override everything
    """

    def __init__(self, v_max: float = 0.55, lookahead: float = 0.4, replan_every: float = 0.25):
        self.map = OccupancyMap()
        self.v_max, self.lookahead, self.replan_every = v_max, lookahead, replan_every
        self.path: list[tuple[float, float]] = []
        self._t_plan = -1e9
        self._t_scan = -1e9
        self.scan_hz = 10.0  # a typical 2-D lidar spins at 5-20 Hz

    def __call__(self, r: Readings, goal: np.ndarray) -> tuple[float, float, dict]:
        if r.t - self._t_scan >= 1.0 / self.scan_hz:
            self.map.update(r)
            self._t_scan = r.t
        if r.t - self._t_plan >= self.replan_every:
            self.path = self.map.plan((r.x, r.y), (float(goal[0]), float(goal[1])))
            self._t_plan = r.t
        # pure pursuit: first path point at least `lookahead` away
        target = np.asarray(goal, float)
        if self.path:
            pts = np.asarray(self.path)
            k = int(np.argmin(np.hypot(pts[:, 0] - r.x, pts[:, 1] - r.y)))
            ahead = np.nonzero(np.hypot(pts[k:, 0] - r.x, pts[k:, 1] - r.y) >= self.lookahead)[0]
            target = pts[k + ahead[0]] if len(ahead) else pts[-1]
        v, w = go_to_goal(r, target, self.v_max)
        dist = math.hypot(goal[0] - r.x, goal[1] - r.y)
        v *= min(1.0, dist / 0.4) / max(1e-6, min(1.0, math.hypot(target[0] - r.x, target[1] - r.y) / 0.6))
        v = min(v, self.v_max)
        front = float(np.min(r.lidar[np.abs(BEAM_ANGLES) < np.deg2rad(20)]))
        if front < 0.25:  # safety layer: never drive into something the lidar sees
            v = min(v, 0.0)
        if r.bumper > 0:
            v, w = -0.2, 1.5
        return v, w, {"target": target, "path": self.path, "front": front, "dist": dist}


# --------------------------------------------------------------------------- perception
def detect_beacon(rgb: np.ndarray) -> dict:
    """Classic perception pipeline: RGB -> HSV -> threshold -> blob -> bearing.

    Returns the mask and, when the orange beacon is visible, its normalised
    horizontal offset (-1 left ... +1 right) and apparent size.
    """
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, (5, 150, 120), (22, 255, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask)
    out = {"mask": mask, "found": False}
    if n > 1:
        i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area > 25:
            cx, cy = cents[i]
            x, y, w, h = stats[i, :4]
            out.update(found=True, offset=float(2 * cx / rgb.shape[1] - 1), area=area,
                       bbox=(int(x), int(y), int(w), int(h)), centroid=(float(cx), float(cy)))
    return out


# --------------------------------------------------------------------------- rendering
class Views:
    """Off-screen renderers for any named camera, plus depth."""

    def __init__(self, model, width=640, height=360):
        self.m = model
        self.w, self.h = width, height
        self.r = mujoco.Renderer(model, height, width)
        self.opt_rays = mujoco.MjvOption()
        self.opt_rays.flags[mujoco.mjtVisFlag.mjVIS_RANGEFINDER] = 1
        self.opt_plain = mujoco.MjvOption()
        self.opt_plain.flags[mujoco.mjtVisFlag.mjVIS_RANGEFINDER] = 0

    def rgb(self, data, camera: str | int = "studio", rays: bool = True) -> np.ndarray:
        self.r.update_scene(data, camera=camera, scene_option=self.opt_rays if rays else self.opt_plain)
        return self.r.render().copy()

    def depth(self, data, camera: str = "rover_cam") -> np.ndarray:
        self.r.enable_depth_rendering()
        self.r.update_scene(data, camera=camera, scene_option=self.opt_plain)
        d = self.r.render().copy()
        self.r.disable_depth_rendering()
        return d

    def close(self):
        try:
            self.r.close()
        except Exception:
            pass


def colorize_depth(depth: np.ndarray, max_m: float = 5.0) -> np.ndarray:
    d = np.clip(depth / max_m, 0, 1)
    img = cv2.applyColorMap((255 * (1 - d)).astype(np.uint8), cv2.COLORMAP_INFERNO)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def lidar_panel(r: Readings, size=360) -> np.ndarray:
    img = np.full((size, size, 3), 250, np.uint8)
    c = (size // 2, int(size * 0.62))
    scale = (size * 0.55) / LIDAR_MAX
    for ring in (1, 2, 3, 4):
        cv2.circle(img, c, int(ring * scale), (215, 215, 215), 1, cv2.LINE_AA)
    for a, dist in zip(BEAM_ANGLES, r.lidar):
        # robot faces up the image; positive angle (left) is drawn on the left
        end = (int(c[0] - math.sin(a) * dist * scale), int(c[1] - math.cos(a) * dist * scale))
        hit = dist < LIDAR_MAX - 1e-3
        cv2.line(img, c, end, ULTRA if hit else (205, 205, 215), 2, cv2.LINE_AA)
        if hit:
            cv2.circle(img, end, 5, MAGENTA, -1, cv2.LINE_AA)
    cv2.rectangle(img, (c[0] - 9, c[1] - 12), (c[0] + 9, c[1] + 12), (30, 30, 30), -1)
    _label(img, "LIDAR  ·  15 BEAMS, 1 M RINGS", (10, 22), kind="bold")
    return img


class StripChart:
    """Rolling plot of a few signals (IMU, encoders)."""

    def __init__(self, names, colors, ylim, seconds=6.0, hz=30):
        self.names, self.colors, self.ylim = names, colors, ylim
        self.n = int(seconds * hz)
        self.buf = np.zeros((len(names), self.n))

    def push(self, values):
        self.buf = np.roll(self.buf, -1, axis=1)
        self.buf[:, -1] = values

    def draw(self, title, w=640, h=180) -> np.ndarray:
        img = np.full((h, w, 3), 250, np.uint8)
        lo, hi = self.ylim
        ys = lambda v: int(h - 10 - (np.clip(v, lo, hi) - lo) / (hi - lo) * (h - 40))  # noqa: E731
        cv2.line(img, (0, ys(0)), (w, ys(0)), (210, 210, 210), 1)
        xs = np.linspace(0, w - 1, self.n).astype(int)
        for k, col in enumerate(self.colors):
            pts = np.stack([xs, [ys(v) for v in self.buf[k]]], 1).astype(np.int32)
            cv2.polylines(img, [pts], False, col, 2, cv2.LINE_AA)
            _label(img, self.names[k], (10 + 130 * k, h - 12), col)
        _label(img, title.upper(), (10, 22), kind="bold")
        return img


FONTS = ASSETS / "fonts"
# Palette (RGB) from the presentation style sheet; accents follow the SCAD stripe colours.
TEXT = (102, 102, 102)       # #666666
SUBTITLE = (85, 85, 85)      # #555555
GREEN = (150, 163, 64)       # #96a340  links, active nav
BLUE = (51, 102, 153)        # #336699  active links
LINE = (234, 234, 234)       # #eaeaea
LINE2 = (204, 204, 204)      # #CCCCCC
ACC_GREEN = (76, 184, 72)      # #4CB848
ACC_YELLOW = (255, 230, 0)     # #FFE600
ACC_ORANGE = (247, 147, 30)    # #F7931E
ACC_BLUE = (41, 171, 226)      # #29ABE2
ACC_PURPLE = (146, 39, 143)    # #92278F
ACC_MAGENTA = (236, 0, 140)    # #EC008C
# names used by the demos
ULTRA, MAGENTA, SUN, TEAL, NIGHT = ACC_BLUE, ACC_MAGENTA, ACC_YELLOW, ACC_GREEN, (0, 0, 0)
WEIGHTS = {"regular": 400, "bold": 500, "display": 250, "serif": 250}


@lru_cache(maxsize=16)
def _font(kind: str, px: int):
    from PIL import ImageFont
    f = ImageFont.truetype(str(FONTS / "Montserrat[wght].ttf"), px)
    f.set_variation_by_axes([WEIGHTS.get(kind, 400)])
    return f


@lru_cache(maxsize=1024)
def _sprite(text: str, kind: str, px: int, color: tuple):
    """Render a text label once to an RGBA patch; reused every frame it appears."""
    from PIL import Image, ImageDraw
    f = _font(kind, px)
    l, t, r, b = f.getbbox(text)
    ascent = f.getmetrics()[0]
    im = Image.new("RGBA", (max(1, r + 2), ascent + max(0, b - ascent) + 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), text, font=f, fill=tuple(color) + (255,))
    arr = np.asarray(im)
    return arr[..., :3].astype(np.float32), arr[..., 3:].astype(np.float32) / 255.0, ascent


def text_width(text: str, scale: float = 0.5, kind: str = "regular") -> int:
    return int(_font(kind, max(8, int(round(scale * 30)))).getlength(text))


def _label(img, text, org, color=(40, 40, 40), scale=0.5, thick=1, kind=None):
    """Draw text with its baseline at org (same convention as cv2.putText), in Montserrat."""
    kind = kind or ("bold" if thick >= 2 else "regular")
    rgb, a, ascent = _sprite(str(text), kind, max(8, int(round(scale * 30))), tuple(int(c) for c in color))
    x, y = int(org[0]), int(org[1]) - ascent
    h, w = rgb.shape[:2]
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sub = img[y0:y1, x0:x1].astype(np.float32)
    rr, aa = rgb[y0 - y:y1 - y, x0 - x:x1 - x], a[y0 - y:y1 - y, x0 - x:x1 - x]
    img[y0:y1, x0:x1] = (sub * (1 - aa) + rr * aa).astype(np.uint8)


def brand(frame: np.ndarray, caption: str = "") -> np.ndarray:
    """Add the presentation title bar to a frame (RGB in, RGB out): pink field, thin black capitals."""
    h, w = frame.shape[:2]
    bar = np.zeros((66, w, 3), np.uint8)
    bar[:] = ACC_MAGENTA
    bar[-1:, :] = 0
    _label(bar, BRAND.upper(), (20, 33), (0, 0, 0), 0.82, kind="display")
    _label(bar, BRAND_SUB.upper(), (20, 54), (0, 0, 0), 0.4, kind="regular")
    if caption:
        tw = text_width(caption.upper(), 0.48, "bold")
        x0 = w - tw - 30
        bar[20:46, x0 - 10:w - 20] = 255
        _label(bar, caption.upper(), (x0, 39), (0, 0, 0), 0.48, kind="bold")
    return np.vstack([bar, frame])


def tile(rows: list[list[np.ndarray]]) -> np.ndarray:
    """Stack images into a grid, resizing each row to a common height and the grid to a common width."""
    out_rows = []
    for row in rows:
        h = min(im.shape[0] for im in row)
        resized = [cv2.resize(im, (int(im.shape[1] * h / im.shape[0]), h)) for im in row]
        out_rows.append(np.hstack(resized))
    w = min(r.shape[1] for r in out_rows)
    return np.vstack([cv2.resize(r, (w, int(r.shape[0] * w / r.shape[1]))) for r in out_rows])


class Video:
    def __init__(self, path: Path, fps: int = 30):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.w = imageio.get_writer(str(self.path), fps=fps, codec="libx264", quality=7,
                                    macro_block_size=8, ffmpeg_log_level="error")

    def add(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        self.w.append_data(frame[: h - h % 2, : w - w % 2])

    def close(self):
        self.w.close()
        print(f"  video  -> {self.path.relative_to(HERE.parent)}")


# --------------------------------------------------------------------------- sim-to-real
def randomize(model: mujoco.MjModel, rng: np.random.Generator, strength: float = 1.0) -> dict:
    """Domain randomization: perturb the physics the way reality differs from the CAD model."""
    s = strength
    info = {
        "floor_friction": float(np.clip(rng.normal(0.9, 0.25 * s), 0.3, 1.5)),
        "tire_friction": float(np.clip(rng.normal(1.2, 0.3 * s), 0.4, 2.0)),
        "mass_scale": float(np.clip(rng.normal(1.0, 0.2 * s), 0.6, 1.5)),
        "motor_left": float(np.clip(rng.normal(1.0, 0.12 * s), 0.6, 1.3)),
        "motor_right": float(np.clip(rng.normal(1.0, 0.12 * s), 0.6, 1.3)),
    }
    model.geom("floor").friction[0] = info["floor_friction"]
    model.geom("wheel_left").friction[0] = info["tire_friction"]
    model.geom("wheel_right").friction[0] = info["tire_friction"]
    model.body("rover").mass[0] *= info["mass_scale"]
    for name in ("motor_left", "motor_right"):
        a = model.actuator(name)
        a.gainprm[0] *= info[name]
        a.biasprm[2] *= info[name]
    return info


# --------------------------------------------------------------------------- interactive
def run_viewer(model, data, step, key_callback=None, duration: float | None = None, camera: str | None = None):
    """Open the real-time MuJoCo window and call ``step(model, data)`` once per physics step.

    The loop paces itself to wall-clock time so what the audience sees is real time.
    """
    import mujoco.viewer

    with mujoco.viewer.launch_passive(model, data, key_callback=key_callback) as v:
        v.opt.flags[mujoco.mjtVisFlag.mjVIS_RANGEFINDER] = 1
        if camera is not None:
            v.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
            v.cam.fixedcamid = model.camera(camera).id
        start = time.perf_counter()
        sim0 = data.time
        while v.is_running() and (duration is None or data.time - sim0 < duration):
            with v.lock():
                step(model, data)
                mujoco.mj_step(model, data)
            v.sync()
            lag = (data.time - sim0) - (time.perf_counter() - start)
            if lag > 0:
                time.sleep(lag)


def wants_headless(argv=None) -> bool:
    argv = sys.argv[1:] if argv is None else argv
    return "--headless" in argv or "--record" in argv


def map_panel(nav: "Navigator", r: Readings, goal, size=360) -> np.ndarray:
    """Draw the occupancy map the robot has built, its plan, and where it is."""
    m = nav.map
    img = np.full((m.n, m.n, 3), 250, np.uint8)
    img[m.cost > 0] = (215, 215, 215)
    img[m.hits > 0] = (40, 40, 40)
    img = np.ascontiguousarray(img[::-1])  # row 0 = +y at the top
    k = size / m.n
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_NEAREST)
    to_px = lambda x, y: (int((x + m.half) / m.res * k), int(size - (y + m.half) / m.res * k))  # noqa: E731
    if nav.path:
        pts = np.array([to_px(x, y) for x, y in nav.path], np.int32)
        cv2.polylines(img, [pts], False, MAGENTA, 3, cv2.LINE_AA)
    cv2.circle(img, to_px(*goal), 7, (255, 107, 0), -1, cv2.LINE_AA)
    c = to_px(r.x, r.y)
    tip = (int(c[0] + 14 * math.cos(r.yaw)), int(c[1] - 14 * math.sin(r.yaw)))
    cv2.circle(img, c, 6, (20, 20, 20), -1, cv2.LINE_AA)
    cv2.line(img, c, tip, (20, 20, 20), 2, cv2.LINE_AA)
    _label(img, "MAP FROM LIDAR + A* PLAN", (8, 20), kind="bold")
    return img
