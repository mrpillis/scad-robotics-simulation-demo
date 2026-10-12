"""Smoke tests for the SCAD teaching demos: the scene loads, the sensors make sense,
the autonomy stack reaches its goals, and the camera pipeline sees the beacon."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
import scad_sim as S  # noqa: E402

mujoco = S.mujoco


def test_scene_loads_with_expected_sensors():
    model, data = S.load()
    rover = S.Rover(model, data)
    for _ in range(250):  # let it settle on its wheels
        mujoco.mj_step(model, data)
    r = rover.read()
    assert model.nu == 2
    assert r.lidar.shape == (S.N_BEAMS,)
    assert math.isclose(r.yaw, math.pi / 4, abs_tol=1e-3)
    assert (r.lidar > 0.5).all(), "no beam should hit the robot itself"
    assert abs(r.accel[2] - 9.81) < 0.5


def test_differential_drive_kinematics():
    model, data = S.load()
    rover = S.Rover(model, data)
    left, right = rover.drive(0.0, 1.0)
    assert left < 0 < right and math.isclose(-left, right)
    left, right = rover.drive(10.0, 0.0)  # saturates at the motor limit
    assert math.isclose(left, S.MAX_WHEEL)


@pytest.mark.parametrize("goal", [(2.2, 2.2), (2.2, -2.2), (0.2, 2.4)])
def test_navigator_reaches_goal_without_collisions(goal):
    model, data = S.load()
    rover = S.Rover(model, data)
    rover.set_goal(*goal)
    nav = S.Navigator()
    bumps = 0
    for _ in range(int(25 / model.opt.timestep)):
        r = rover.read()
        v, w, info = nav(r, rover.goal)
        rover.drive(v, w)
        mujoco.mj_step(model, data)
        bumps += r.bumper > 0
        if info["dist"] < 0.15:
            break
    assert info["dist"] < 0.15
    assert bumps == 0


def test_domain_randomization_changes_physics():
    model, _ = S.load()
    before = model.geom("floor").friction[0]
    info = S.randomize(model, np.random.default_rng(0), 1.0)
    assert model.geom("floor").friction[0] == pytest.approx(info["floor_friction"])
    assert info["floor_friction"] != before


def test_camera_sees_beacon():
    model, data = S.load()
    rover = S.Rover(model, data)
    rover.set_goal(-1.2, -1.2)  # straight ahead of the starting pose
    mujoco.mj_forward(model, data)
    try:
        views = S.Views(model, 640, 360)
    except Exception as exc:  # no OpenGL available
        pytest.skip(f"rendering unavailable: {exc}")
    det = S.detect_beacon(views.rgb(data, "rover_cam", rays=False))
    views.close()
    assert det["found"] and abs(det["offset"]) < 0.2
