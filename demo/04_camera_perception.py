"""Demo 4 - A camera perception pipeline, step by step.

No map and no ground-truth position this time: the rover only knows what its
camera sees. Each frame goes through a classic computer-vision pipeline

    RGB image -> HSV colour space -> threshold "orange" -> clean up -> largest blob
              -> bearing to the beacon -> steering command

and the rover searches (spins), turns to centre the beacon, and drives to it.

    python demo/04_camera_perception.py              # live pipeline window (real time)
    python demo/04_camera_perception.py --headless   # record demo/output/04_camera_perception.mp4

Talking points
- Simulation gives perfect labels for free (we know exactly where the beacon is),
  which is why it is used to generate training data for learned perception.
- Change lighting or the beacon colour in assets/scad_lab.xml and watch the threshold fail:
  that fragility is the sim-to-real "appearance gap" in miniature.
"""

import argparse
import math
import time

import scad_sim as S  # import first: it selects a headless GL backend when needed

import cv2
import mujoco
import numpy as np


class BeaconFollower:
    def __init__(self):
        self.state = "SEARCH"
        self.last_offset = 1.0
        self.t_final = None

    def __call__(self, det: dict, r: S.Readings) -> tuple[float, float]:
        front = float(np.min(r.lidar[np.abs(S.BEAM_ANGLES) < np.deg2rad(20)]))
        if self.state in ("FINAL APPROACH", "ARRIVED"):
            # the pad has slid under the camera: finish by dead reckoning (~0.5 m straight ahead)
            if r.t - self.t_final < 1.4:
                return 0.35, 0.0
            self.state = "ARRIVED"
            return 0.0, 0.0
        if det["found"]:
            self.last_offset = det["offset"]
            bottom = det["bbox"][1] + det["bbox"][3]
            if bottom > 352 and det["area"] > 6000 and abs(det["offset"]) < 0.15:
                self.state, self.t_final = "FINAL APPROACH", r.t  # pad reaches the bottom edge of the image
                return 0.35, 0.0
            self.state = "TRACK"
            w = -2.2 * det["offset"]  # beacon right of centre (offset > 0) -> turn right (w < 0)
            v = 0.45 * max(0.0, 1 - 1.6 * abs(det["offset"]))
            if front < 0.3:
                v = 0.0
            return v, w
        self.state = "SEARCH"
        return 0.0, 1.4 if self.last_offset <= 0 else -1.4  # spin toward where we last saw it


def pipeline_panels(rgb: np.ndarray, det: dict, follower: BeaconFollower, cmd) -> list[np.ndarray]:
    rgb = rgb.copy()
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hue = cv2.applyColorMap(hsv[:, :, 0] * 1, cv2.COLORMAP_HSV)
    hue = cv2.cvtColor(hue, cv2.COLOR_BGR2RGB)
    mask = cv2.cvtColor(det["mask"], cv2.COLOR_GRAY2RGB)
    out = rgb.copy()
    h, w = out.shape[:2]
    cv2.line(out, (w // 2, 0), (w // 2, h), (255, 255, 255), 1)
    if det["found"]:
        x, y, bw, bh = det["bbox"]
        cv2.rectangle(out, (x, y), (x + bw, y + bh), (0, 255, 120), 2)
        cx, cy = map(int, det["centroid"])
        cv2.arrowedLine(out, (w // 2, h - 30), (cx, h - 30), (0, 255, 120), 3, tipLength=0.2)
        S._label(out, f"offset {det['offset']:+.2f}   area {det['area']} px", (10, h - 50), (255, 255, 255), 0.55, 2)
    S._label(out, f"state: {follower.state}   v={cmd[0]:+.2f} m/s  w={cmd[1]:+.2f} rad/s", (10, h - 12), (255, 255, 255), 0.55, 2)
    for img, title in ((rgb, "1  CAMERA (RGB)"), (hue, "2  HSV (hue channel)"), (mask, "3  THRESHOLD orange + clean-up"),
                       (out, "4  DETECTION -> STEERING")):
        S._label(img, title, (10, 26), (255, 255, 255), 0.6, 2)
    return [rgb, hue, mask, out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--seconds", type=float, default=16.0)
    ap.add_argument("--goal", default="-2.3,1.0")
    a = ap.parse_args()

    model, data = S.load()
    rover = S.Rover(model, data)
    rover.set_goal(*map(float, a.goal.split(",")))
    mujoco.mj_forward(model, data)
    follower = BeaconFollower()
    views = S.Views(model, 640, 360)
    every = int(round(1 / 30 / model.opt.timestep))  # camera runs at 30 Hz, physics at 500 Hz
    cmd = (0.0, 0.0)

    def tick(k):
        nonlocal cmd
        r = rover.read()
        frame = None
        if k % every == 0:
            rgb = views.rgb(data, "rover_cam", rays=False)
            det = S.detect_beacon(rgb)
            cmd = follower(det, r)
            frame = (rgb, det)
        rover.drive(*cmd)
        mujoco.mj_step(model, data)
        return frame

    def compose(rgb, det):
        studio = views.rgb(data, "studio", rays=False)
        dist = math.dist((data.body("rover").xpos[0], data.body("rover").xpos[1]), rover.goal)
        S._label(studio, f"true distance to beacon {dist:4.2f} m (the robot does not know this)", (10, 26),
                 (255, 255, 255), 0.5, 2)
        p1, p2, p3, p4 = pipeline_panels(rgb, det, follower, cmd)
        return S.brand(S.tile([[p1, p2, p3], [p4, studio]]), f"Demo 4: camera perception   t = {data.time:4.1f} s")

    if a.headless:
        S.ensure_output()
        vid = S.Video(S.OUTPUT / "04_camera_perception.mp4")
        still_saved = False
        for k in range(int(a.seconds / model.opt.timestep)):
            f = tick(k)
            if f is not None:
                img = compose(*f)
                vid.add(img)
                if not still_saved and follower.state == "TRACK" and f[1].get("area", 0) > 1500:
                    cv2.imwrite(str(S.OUTPUT / "04_pipeline_still.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                    still_saved = True
            if follower.state == "ARRIVED" and data.time > 1:
                last = compose(*f) if f is not None else img
                for _ in range(30):
                    vid.add(last)
                break
        vid.close()
        views.close()
        dist = math.dist((data.body("rover").xpos[0], data.body("rover").xpos[1]), rover.goal)
        print(f"  image  -> demo/output/04_pipeline_still.png\n  final state {follower.state}, "
              f"true distance {dist:.2f} m after {data.time:.1f} s")
        return

    win = "SCAD Robotics Simulation Demo - perception"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    t0, k = time.perf_counter(), 0
    while True:
        f = tick(k)
        k += 1
        if f is not None:
            cv2.imshow(win, cv2.cvtColor(compose(*f), cv2.COLOR_RGB2BGR))
            lag = data.time - (time.perf_counter() - t0)
            key = cv2.waitKey(max(1, int(lag * 1000))) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("g"):  # move the beacon somewhere new
                rover.set_goal(*np.random.uniform(-2.4, 2.4, 2))
                follower.state = "SEARCH"
    cv2.destroyAllWindows()
    views.close()


if __name__ == "__main__":
    main()
