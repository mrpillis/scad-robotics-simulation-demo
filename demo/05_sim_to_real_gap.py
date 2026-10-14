"""Demo 5 - Sim vs. real: what changes when the world is not the model?

Reality never matches the simulator exactly: floors are dustier, motors weaker,
batteries heavier, sensors noisier and a little late. Domain randomization
samples many plausible "realities" and tests the same software in all of them.

We run two strategies in 12 randomized worlds:

  OPEN LOOP   replay the exact wheel commands that worked in the ideal simulator
  CLOSED LOOP the full sense -> map -> plan -> act stack from Demo 3, with noisy, delayed sensors

    python demo/05_sim_to_real_gap.py             # ~1 minute, writes demo/output/05_sim_to_real_gap.png
    python demo/05_sim_to_real_gap.py --worlds 30 --strength 1.5

Talking points
- A controller tuned in one perfect world is brittle (open loop scatters).
- Feedback + randomized training/testing make software survive the transfer.
- What simulation still cannot give you: wear, cable snags, lighting, people. Test on hardware too.
"""

import argparse
import math

import scad_sim as S  # import first: it selects a headless GL backend when needed

import cv2
import mujoco
import numpy as np

GOAL = (2.2, 2.2)


def run(strength: float, seed: int, mode: str, replay=None, seconds=25.0):
    model, data = S.load()
    info = S.randomize(model, np.random.default_rng(seed), strength) if seed >= 0 else {}
    noisy = seed >= 0
    rover = S.Rover(model, data, noise=strength if noisy else 0.0, latency_steps=15 if noisy else 0, seed=max(seed, 0))
    rover.set_goal(*GOAL)
    nav = S.Navigator()
    path, cmds, bumps, reached_t = [], [], 0, None
    n = int(seconds / model.opt.timestep)
    for k in range(n):
        r = rover.read()
        if mode == "closed":
            v, w, _ = nav(r, rover.goal)
            cmds.append((v, w))
        else:
            v, w = replay[k] if k < len(replay) else (0.0, 0.0)
        rover.drive(v, w)
        mujoco.mj_step(model, data)
        if k % 20 == 0:
            path.append(tuple(data.body("rover").xpos[:2]))
        bumps += data.sensor("bumper").data[0] > 0
        if reached_t is None and math.dist(data.body("rover").xpos[:2], GOAL) < 0.2:
            reached_t = data.time
            if mode == "closed" and seed < 0:
                break
    final = math.dist(data.body("rover").xpos[:2], GOAL)
    return {"path": path, "cmds": cmds, "reached": reached_t, "final": final, "bumps": int(bumps), "info": info}


def overhead_plot(results, title, color):
    model, data = S.load()
    data.mocap_pos[model.body("goal").mocapid[0]][:2] = GOAL
    model.geom("goal_beacon").rgba[3] = 0  # hide the hovering sphere in the top view
    mujoco.mj_forward(model, data)
    data.qpos[0:2] = (-10, -10)  # move the rover out of the shot
    mujoco.mj_forward(model, data)
    v = S.Views(model, 520, 520)
    img = v.rgb(data, "overhead", rays=False)
    v.close()
    h, w = img.shape[:2]
    half = 8.2 * math.tan(math.radians(22.5))
    to_px = lambda x, y: (int(w / 2 + x / half * h / 2), int(h / 2 - y / half * h / 2))  # noqa: E731
    for res in results[1:]:
        pts = np.array([to_px(*p) for p in res["path"]], np.int32)
        cv2.polylines(img, [pts], False, color, 2, cv2.LINE_AA)
        cv2.circle(img, tuple(pts[-1]), 5, (200, 30, 30) if res["final"] > 0.3 else (30, 160, 60), -1, cv2.LINE_AA)
    pts = np.array([to_px(*p) for p in results[0]["path"]], np.int32)
    cv2.polylines(img, [pts], False, (20, 20, 20), 3, cv2.LINE_AA)
    ok = sum(r["final"] < 0.3 for r in results[1:])
    banner = np.full((70, w, 3), 250, np.uint8)
    S._label(banner, title, (12, 28), (20, 20, 20), 0.7, 2)
    S._label(banner, f"reached goal in {ok}/{len(results) - 1} randomized worlds   (black = ideal sim)", (12, 56), (80, 80, 80), 0.5)
    return np.vstack([banner, img])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=12)
    ap.add_argument("--strength", type=float, default=1.0, help="how different from the model reality may be")
    a = ap.parse_args()

    print("ideal simulator: closed-loop run to record a command sequence ...")
    ideal = run(0, -1, "closed")
    replay = ideal["cmds"] + [(0.0, 0.0)] * 20000
    ideal_open = run(0, -1, "open", replay)
    print(f"  ideal: reached in {ideal['reached']:.1f} s; replaying its commands in the ideal sim ends "
          f"{ideal_open['final']:.2f} m from the goal")

    open_runs, closed_runs = [ideal_open], [ideal]
    print(f"\n{'world':>5} {'floor mu':>8} {'tire mu':>8} {'mass x':>6} {'motor L':>7} {'motor R':>7} |"
          f" {'open-loop miss':>14} | {'closed-loop':>12}")
    for i in range(a.worlds):
        o = run(a.strength, i, "open", replay)
        c = run(a.strength, i, "closed")
        open_runs.append(o)
        closed_runs.append(c)
        f = o["info"]
        cl = f"{c['reached']:.1f} s" if c["reached"] else f"miss {c['final']:.2f} m"
        print(f"{i:5d} {f['floor_friction']:8.2f} {f['tire_friction']:8.2f} {f['mass_scale']:6.2f} "
              f"{f['motor_left']:7.2f} {f['motor_right']:7.2f} | {o['final']:12.2f} m | {cl:>12}")

    left = overhead_plot(open_runs, "OPEN LOOP: replay the ideal commands", S.ULTRA)
    right = overhead_plot(closed_runs, "CLOSED LOOP: sense, map, plan, act", S.MAGENTA)
    S.ensure_output()
    img = S.brand(np.hstack([left, np.full((left.shape[0], 12, 3), 255, np.uint8), right]),
                  f"Demo 5: sim-to-real gap   {a.worlds} randomized worlds")
    out = S.OUTPUT / "05_sim_to_real_gap.png"
    cv2.imwrite(str(out), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"\n  image  -> {out.relative_to(S.HERE.parent)}")
    ok_o = sum(r["final"] < 0.3 for r in open_runs[1:])
    ok_c = sum(r["final"] < 0.3 for r in closed_runs[1:])
    print(f"  open loop reached the goal in {ok_o}/{a.worlds} worlds; closed loop in {ok_c}/{a.worlds}")


if __name__ == "__main__":
    main()
