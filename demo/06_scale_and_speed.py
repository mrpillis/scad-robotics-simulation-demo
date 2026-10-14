"""Demo 6 - Why simulation scales: faster than real time, many worlds at once.

Measures how much robot "experience" this laptop can generate:

  1. one world, physics only (no rendering)  -> real-time factor
  2. one world, physics + a 640x360 camera    -> the cost of sensor rendering
  3. N worlds in parallel on the CPU cores    -> experience per wall-clock minute

    python demo/06_scale_and_speed.py
    python demo/06_scale_and_speed.py --workers 8 --seconds 20

Talking points
- A physical robot gives you 1 second of experience per second, and can break.
- CPU simulators give 10-1000x; GPU simulators (Isaac Lab, mjlab / MuJoCo Warp)
  run thousands of worlds in parallel, which is what makes reinforcement learning practical.
- Rendering is often the bottleneck: decide which sensors you really need.
"""

import argparse
import multiprocessing as mp
import os
import time

import scad_sim as S  # import first: it selects a headless GL backend when needed

import mujoco
import numpy as np


def physics_only(seconds: float, seed: int = 0) -> tuple[float, float]:
    model, data = S.load()
    rng = np.random.default_rng(seed)
    n = int(seconds / model.opt.timestep)
    t0 = time.perf_counter()
    for k in range(n):
        if k % 250 == 0:
            data.ctrl[:] = rng.uniform(-10, 10, 2)  # a random "policy"
        mujoco.mj_step(model, data)
    return data.time, time.perf_counter() - t0


def with_camera(seconds: float) -> tuple[float, float, int]:
    model, data = S.load()
    views = S.Views(model, 640, 360)
    n = int(seconds / model.opt.timestep)
    every = int(round(1 / 30 / model.opt.timestep))
    frames = 0
    t0 = time.perf_counter()
    for k in range(n):
        data.ctrl[:] = (8, 6)
        mujoco.mj_step(model, data)
        if k % every == 0:
            views.rgb(data, "rover_cam", rays=False)
            frames += 1
    wall = time.perf_counter() - t0
    views.close()
    return data.time, wall, frames


def _worker(args):
    seconds, seed = args
    return physics_only(seconds, seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=60.0, help="simulated seconds per world")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--no-camera", action="store_true")
    a = ap.parse_args()

    sim, wall = physics_only(a.seconds)
    rtf1 = sim / wall
    print(f"1) one world, physics only : {sim:5.1f} s simulated in {wall:5.2f} s  ->  {rtf1:6.0f}x real time")

    if not a.no_camera:
        sim_c, wall_c, frames = with_camera(min(a.seconds, 5.0))
        print(f"2) + 30 Hz onboard camera  : {sim_c:5.1f} s simulated in {wall_c:5.2f} s  ->  {sim_c / wall_c:6.1f}x real time"
              f"   ({frames / wall_c:.0f} frames/s rendered)")

    t0 = time.perf_counter()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        results = pool.map(_worker, [(a.seconds, i) for i in range(a.workers)])
    wall_p = time.perf_counter() - t0
    total = sum(r[0] for r in results)
    busy = max(r[1] for r in results)  # excludes the one-off cost of starting the worker processes
    print(f"3) {a.workers:2d} worlds in parallel    : {total:5.0f} s simulated in {busy:5.2f} s  ->  {total / busy:6.0f}x real time"
          f"   (+{wall_p - busy:.1f} s to start the workers)")
    per_min_h = total / busy * 60 / 3600
    print(f"\n   => this machine generates about {per_min_h:.1f} hours of robot experience per minute (physics only).")
    print("      A single physical robot generates 0.017 hours per minute, and needs charging.")


if __name__ == "__main__":
    main()
