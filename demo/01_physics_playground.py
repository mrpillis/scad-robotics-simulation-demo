"""Demo 1 - Physics realism: same shapes, different materials.

Three lanes, three materials (foam, rubber, steel). In each lane a ball is
dropped and a block slides down a ramp. Mass (density), friction and contact
stiffness/damping are the only differences, and they change everything.

    python demo/01_physics_playground.py               # live, real-time window
    python demo/01_physics_playground.py --headless    # render demo/output/01_physics_playground.mp4
    python demo/01_physics_playground.py --timestep 0.03 --headless   # see what a too-large timestep does

Talking points
- A physics engine solves Newton's laws in small time steps (here 2 ms).
- "Realism" is a set of modelling choices: contact model, friction, restitution.
- Change one number on screen and re-run: that loop is why simulation is fast to teach with.
"""

import argparse

import scad_sim as S  # import first: it selects a headless GL backend when needed

import mujoco
import numpy as np

MATERIALS = {
    # name: (rgba, density kg/m^3, sliding friction, solref)
    # solref "timeconst dampratio" (soft, critically damped) or "-stiffness -damping" (springy)
    "foam":   ("1.0 0.9 0.0 1", 30,   1.0, "0.05 1.0"),
    "rubber": ("0.93 0.0 0.55 1", 1100, 1.1, "-20000 -40"),
    "steel":  ("0.16 0.67 0.89 1", 7850, 0.25, "0.004 1.0"),
}


def build_scene(timestep: float) -> str:
    lanes = []
    for i, (name, (rgba, dens, fric, solref)) in enumerate(MATERIALS.items()):
        x = (i - 1) * 1.3
        # ramp tilted 0.45 rad (about 26 deg) about x, high end away from the camera
        lanes.append(f"""
        <geom name="ramp_{name}" type="box" size="0.32 0.6 0.02" pos="{x} 0.6 0.35" euler="0.45 0 0" rgba="0.05 0.05 0.05 1" friction="{fric} 0.005 0.0001"/>
        <body name="ball_{name}" pos="{x} -0.7 1.6"><freejoint/>
          <geom type="sphere" size="0.12" rgba="{rgba}" density="{dens}" friction="{fric} 0.005 0.0001" solref="{solref}"/></body>
        <body name="block_{name}" pos="{x} 0.833 0.557" euler="0.45 0 0"><freejoint/>
          <geom type="box" size="0.1 0.1 0.06" rgba="{rgba}" density="{dens}" friction="{fric} 0.005 0.0001" solref="{solref}"/></body>""")
    return f"""
<mujoco model="physics_playground">
  <compiler angle="radian"/>
  <option timestep="{timestep}" integrator="implicitfast"/>
  <visual><global offwidth="1280" offheight="720"/><headlight ambient="0.4 0.4 0.4"/></visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.85 0.85 0.83" rgb2="0.75 0.75 0.73" width="256" height="256"/>
    <material name="grid" texture="grid" texrepeat="10 10"/>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="1.0 1.0 1.0" rgb2="0.8 0.8 0.8" width="256" height="256"/>
  </asset>
  <worldbody>
    <light pos="0 -2 5" dir="0 0.3 -1" castshadow="true"/>
    <geom name="floor" type="plane" size="4 3 0.1" material="grid"/>
    <camera name="front" pos="0 -4.6 1.7" xyaxes="1 0 0 0 0.3 0.954" fovy="45"/>
    {''.join(lanes)}
  </worldbody>
</mujoco>"""


LANE_COLORS = {"foam": S.ACC_ORANGE, "rubber": S.ACC_MAGENTA, "steel": S.ACC_BLUE}


def label_lanes(frame):
    h, w = frame.shape[:2]
    for i, name in enumerate(MATERIALS):
        x = int(w * (0.5 + 0.3 * (i - 1)))
        tw = S.text_width(name.upper(), 1.1, "display")
        S._label(frame, name.upper(), (x - tw // 2, h - 24), LANE_COLORS[name], 1.1, kind="display")
    return frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", help="record a video instead of opening a window")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--timestep", type=float, default=0.002)
    a = ap.parse_args()

    model = mujoco.MjModel.from_xml_string(build_scene(a.timestep))
    data = mujoco.MjData(model)
    print(f"timestep = {model.opt.timestep*1000:.1f} ms   bodies = {model.nbody}   materials = {list(MATERIALS)}")

    if not a.headless:
        S.run_viewer(model, data, step=lambda m, d: None, duration=None, camera="front")
        return

    S.ensure_output()
    views = S.Views(model, 960, 540)
    tag = "" if a.timestep == 0.002 else f"_dt{a.timestep:g}"
    vid = S.Video(S.OUTPUT / f"01_physics_playground{tag}.mp4")
    every = max(1, int(round(1 / 30 / model.opt.timestep)))
    peak = {n: 0.0 for n in MATERIALS}
    for k in range(int(a.seconds / model.opt.timestep)):
        mujoco.mj_step(model, data)
        for n in MATERIALS:
            if data.time > 0.9:  # after first impact: highest rebound
                peak[n] = max(peak[n], data.body(f"ball_{n}").xpos[2] - 0.12)
        if k % every == 0:
            f = label_lanes(views.rgb(data, "front", rays=False))
            vid.add(S.brand(f, f"Demo 1: physics realism   t = {data.time:4.2f} s   dt = {a.timestep*1000:g} ms"))
    vid.close()
    views.close()
    for n in MATERIALS:
        slid = 0.833 - data.body(f"block_{n}").xpos[1]
        print(f"  {n:7s} ball rebound peak {peak[n]:5.2f} m   block slid {slid:5.2f} m")
    if not np.all(np.isfinite(data.qpos)):
        print("  !! simulation diverged - the timestep is too large for these contacts")


if __name__ == "__main__":
    main()
