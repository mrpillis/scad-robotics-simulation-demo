"""Demo 2 - Basic robot control: drive a differential-drive rover.

Live (default) opens the real-time MuJoCo window:

    python demo/02_drive_the_robot.py          # Windows / Linux
    mjpython demo/02_drive_the_robot.py        # macOS (MuJoCo's viewer needs mjpython)

    Up / Down     faster / slower (m/s)
    Left / Right  turn left / right
    Page Down     stop
    Enter         autopilot on/off (proportional go-to-goal controller)
    Page Up       move the orange goal somewhere new
    Ctrl + right-drag on the rover   shove it (perturbation) and watch the controller recover

Headless records a scripted mission to demo/output/02_drive_the_robot.mp4 and a
trajectory plot, so there is always a fallback video:

    python demo/02_drive_the_robot.py --headless

Talking points
- Commands are body speeds (v, w); kinematics turn them into two wheel speeds.
- Each motor is a velocity servo: a controller *inside* the simulated hardware.
- The autopilot is ten lines of math (see scad_sim.go_to_goal). Change the gain, re-run.
"""

import argparse
import math

import scad_sim as S  # import first: it selects a headless GL backend when needed

import cv2
import numpy as np

KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT = 265, 264, 263, 262
KEY_ENTER, KEY_PAGE_UP, KEY_PAGE_DOWN = 257, 266, 267


class Teleop:
    def __init__(self, rover: S.Rover):
        self.rover = rover
        self.v = 0.0
        self.w = 0.0
        self.auto = False
        self.rng = np.random.default_rng(7)
        self._last_print = -1.0

    def key(self, code: int):
        if code == KEY_UP:
            self.v = min(0.8, self.v + 0.1)
        elif code == KEY_DOWN:
            self.v = max(-0.4, self.v - 0.1)
        elif code == KEY_LEFT:
            self.w = min(3.0, self.w + 0.5)
        elif code == KEY_RIGHT:
            self.w = max(-3.0, self.w - 0.5)
        elif code == KEY_PAGE_DOWN:
            self.v = self.w = 0.0
        elif code == KEY_ENTER:
            self.auto = not self.auto
            print(f"autopilot {'ON' if self.auto else 'OFF'}")
        elif code == KEY_PAGE_UP:
            gx, gy = self.rng.uniform(-2.5, 2.5, 2)
            self.rover.set_goal(gx, gy)
            print(f"new goal at ({gx:.2f}, {gy:.2f})")

    def step(self, model, data):
        r = self.rover.read()
        if self.auto:
            v, w = S.go_to_goal(r, self.rover.goal)
        else:
            v, w = self.v, self.w
        left, right = self.rover.drive(v, w)
        if data.time - self._last_print > 0.5:
            self._last_print = data.time
            print(f"t={data.time:5.1f}s  v={v:+.2f} m/s  w={w:+.2f} rad/s  "
                  f"wheels L={left:+5.1f} R={right:+5.1f} rad/s  pos=({r.x:+.2f},{r.y:+.2f})  "
                  f"yaw={math.degrees(r.yaw):+4.0f} deg")


def scripted_mission(t: float, r: S.Readings, rover: S.Rover):
    """Teleop-style moves first, then hand over to the autopilot."""
    if t < 2.0:
        return 0.5, 0.0, "manual: forward  v=0.5 m/s"
    if t < 3.2:
        return 0.3, 1.6, "manual: arc left  w=1.6 rad/s"
    if t < 4.2:
        return 0.0, -2.5, "manual: spin in place  w=-2.5 rad/s"
    v, w = S.go_to_goal(r, rover.goal)
    return v, w, "autopilot: proportional go-to-goal"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--seconds", type=float, default=14.0)
    a = ap.parse_args()

    model, data = S.load()
    rover = S.Rover(model, data)

    if not a.headless:
        tele = Teleop(rover)
        print(__doc__.split("Headless")[0])
        S.run_viewer(model, data, step=tele.step, key_callback=tele.key)
        return

    # headless: the default goal sits in the far corner, reachable without obstacle avoidance
    S.ensure_output()
    views = S.Views(model, 640, 360)
    vid = S.Video(S.OUTPUT / "02_drive_the_robot.mp4")
    every = int(round(1 / 30 / model.opt.timestep))
    path = []
    caption = ""
    for k in range(int(a.seconds / model.opt.timestep)):
        r = rover.read()
        v, w, caption = scripted_mission(data.time, r, rover)
        left, right = rover.drive(v, w)
        S.mujoco.mj_step(model, data)
        if k % 10 == 0:
            path.append((r.x, r.y))
        if k % every == 0:
            studio = views.rgb(data, "studio", rays=False)
            chase = views.rgb(data, "chase", rays=False)
            panel = np.full((150, 1280, 3), 250, np.uint8)
            S._label(panel, caption, (16, 34), (20, 20, 20), 0.7, 2)
            S._label(panel, f"command  v = {v:+.2f} m/s   w = {w:+.2f} rad/s", (16, 74), (60, 60, 60), 0.6)
            S._label(panel, f"wheels   left = {left:+5.1f} rad/s   right = {right:+5.1f} rad/s", (16, 108), (60, 60, 60), 0.6)
            dist = math.dist((r.x, r.y), rover.goal)
            S._label(panel, f"distance to goal {dist:4.2f} m", (900, 74), S.MAGENTA, 0.6, 2)
            vid.add(S.brand(S.tile([[studio, chase], [panel]]), f"Demo 2: basic control   t = {data.time:4.1f} s"))
    vid.close()

    # trajectory over the overhead camera
    top = views.rgb(data, "overhead", rays=False)
    views.close()
    h, w_ = top.shape[:2]
    # overhead cam: fovy 45 deg at 8.2 m -> half-height 3.397 m
    half = 8.2 * math.tan(math.radians(22.5))
    to_px = lambda x, y: (int(w_ / 2 + x / half * h / 2), int(h / 2 - y / half * h / 2))  # noqa: E731
    pts = np.array([to_px(x, y) for x, y in path], np.int32)
    img = top.copy()
    cv2.polylines(img, [pts], False, S.MAGENTA, 4, cv2.LINE_AA)
    cv2.circle(img, tuple(pts[0]), 7, (40, 40, 40), -1)
    out = S.OUTPUT / "02_trajectory.png"
    cv2.imwrite(str(out), cv2.cvtColor(S.brand(img, "Demo 2: path driven"), cv2.COLOR_RGB2BGR))
    print(f"  image  -> {out.relative_to(S.HERE.parent)}")
    print(f"  final distance to goal: {math.dist(path[-1], rover.goal):.2f} m")


if __name__ == "__main__":
    main()
