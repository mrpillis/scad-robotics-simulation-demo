"""Demo 3 - Sensors + perception pipeline: the robot drives itself.

The rover now *senses*: wheel encoders, IMU, bumper, a 15-beam lidar and an
RGB-D camera. The lidar feeds an occupancy map, A* plans a path through it,
and pure pursuit follows the path. Every signal is on one dashboard.

    python demo/03_sensor_dashboard.py              # live dashboard window (real time)
    python demo/03_sensor_dashboard.py --viewer     # MuJoCo 3-D window instead (use mjpython on macOS)
    python demo/03_sensor_dashboard.py --headless   # record demo/output/03_sensor_dashboard.mp4

Live dashboard keys:  g = new random goal   space = pause   q / Esc = quit

Talking points
- Sensor emulation: each panel is a simulated sensor; noise, range and rate are settings.
- Perception pipeline: lidar hits -> occupancy grid -> inflated cost map -> A* -> controller.
- Compare to Demo 2: same motors, same controller, but sensing turns a crash into a route.
"""

import argparse
import math
import time

import scad_sim as S  # import first: it selects a headless GL backend when needed

import cv2
import mujoco
import numpy as np


class Dashboard:
    def __init__(self, model):
        self.views = S.Views(model, 640, 360)
        self.imu = S.StripChart(["gyro z", "accel x / 5"], [(220, 60, 20), (30, 120, 220)], (-3, 3))
        self.enc = S.StripChart(["cmd L", "encoder L", "cmd R", "encoder R"],
                                [(160, 160, 160), (30, 120, 220), (230, 190, 120), (220, 60, 20)], (-15, 15))

    def push(self, r, cmd):
        self.imu.push([r.gyro[2], r.accel[0] / 5])
        self.enc.push([cmd[0], r.enc_left, cmd[1], r.enc_right])

    def frame(self, data, r, nav, goal, status):
        studio = self.views.rgb(data, "studio", rays=True)
        cam = self.views.rgb(data, "rover_cam", rays=False)
        depth = S.colorize_depth(self.views.depth(data, "rover_cam"))
        S._label(cam, "ONBOARD RGB CAMERA", (10, 24), (255, 255, 255), 0.55, 2)
        S._label(depth, "DEPTH CAMERA (near = bright)", (10, 24), (255, 255, 255), 0.55, 2)
        S._label(studio, status, (10, 24), (255, 255, 255), 0.55, 2)
        row2 = [depth, S.lidar_panel(r), S.map_panel(nav, r, goal)]
        row3 = [self.imu.draw("IMU (rad/s, m/s^2)"), self.enc.draw("WHEELS: command vs encoder (rad/s)")]
        return S.tile([[studio, cam], row2, row3])

    def close(self):
        self.views.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--viewer", action="store_true", help="use the MuJoCo 3-D viewer instead of the dashboard")
    ap.add_argument("--seconds", type=float, default=45.0)
    ap.add_argument("--goals", default="2.2,2.2;2.2,-2.2;-2.3,1.0",
                    help="semicolon-separated goal list for the headless run")
    a = ap.parse_args()

    model, data = S.load()
    rover = S.Rover(model, data)
    nav = S.Navigator()
    goals = [tuple(map(float, g.split(","))) for g in a.goals.split(";")]
    rover.set_goal(*goals[0])
    state = {"goal_i": 0, "cmd": (0.0, 0.0), "reached": 0}
    rng = np.random.default_rng(3)

    def control(m, d):
        r = rover.read()
        v, w, info = nav(r, rover.goal)
        state["cmd"] = rover.drive(v, w)
        state["r"], state["info"] = r, info
        if info["dist"] < 0.15:
            state["reached"] += 1
            state["goal_i"] = (state["goal_i"] + 1) % len(goals)
            nxt = goals[state["goal_i"]] if a.headless else tuple(rng.uniform(-2.4, 2.4, 2))
            rover.set_goal(*nxt)
        return r

    if a.viewer:
        S.run_viewer(model, data, step=lambda m, d: control(m, d))
        return

    dash = Dashboard(model)
    every = int(round(1 / 30 / model.opt.timestep))
    status = lambda: (f"t = {data.time:4.1f} s   goals reached: {state['reached']}   "  # noqa: E731
                      f"distance {state['info']['dist']:.2f} m")

    if a.headless:
        S.ensure_output()
        vid = S.Video(S.OUTPUT / "03_sensor_dashboard.mp4")
        for k in range(int(a.seconds / model.opt.timestep)):
            r = control(model, data)
            mujoco.mj_step(model, data)
            if k % every == 0:
                dash.push(r, state["cmd"])
                vid.add(S.brand(dash.frame(data, r, nav, rover.goal, status()), "Demo 3: sensors + autonomy"))
            if state["reached"] >= len(goals):
                break
        vid.close()
        cv2.imwrite(str(S.OUTPUT / "03_dashboard_still.png"),
                    cv2.cvtColor(S.brand(dash.frame(data, r, nav, rover.goal, status()), "Demo 3: sensors + autonomy"),
                                 cv2.COLOR_RGB2BGR))
        print(f"  image  -> demo/output/03_dashboard_still.png\n  goals reached: {state['reached']} in {data.time:.1f} s")
        dash.close()
        return

    # live: one OpenCV window, paced to wall-clock time
    win = "SCAD Robotics Simulation Demo - sensors"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    paused, t0, sim0 = False, time.perf_counter(), data.time
    while True:
        if not paused:
            target = sim0 + (time.perf_counter() - t0)
            while data.time < target:
                r = control(model, data)
                mujoco.mj_step(model, data)
            dash.push(r, state["cmd"])
            img = S.brand(dash.frame(data, r, nav, rover.goal, status()), "Demo 3: sensors + autonomy")
            cv2.imshow(win, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("g"):
            rover.set_goal(*rng.uniform(-2.4, 2.4, 2))
        if key == ord(" "):
            paused = not paused
            t0, sim0 = time.perf_counter(), data.time
    cv2.destroyAllWindows()
    dash.close()


if __name__ == "__main__":
    main()
