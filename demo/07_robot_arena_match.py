"""Demo 7 (capstone) - A full robot competition built on the same engine.

This repository grew out of ArtifactArena (MIT CSAIL / MIT Media Lab), where robots
are designed as MuJoCo XML plus a Python controller and fight to push each other
off an elevated ring. It shows where the ideas of Demos 1-6 lead: a complete,
rule-checked simulation used for research and for a public competition.

    python demo/07_robot_arena_match.py                       # live 3-D window (mjpython on macOS)
    python demo/07_robot_arena_match.py --headless            # record demo/output/07_arena_match.mp4
    python demo/07_robot_arena_match.py --red pusher --blue octahedron --seconds 30

Bots: pusher, static, tetrahedron, hexahedron, octahedron, dodecahedron, icosahedron
(see mjarena/core/assets/baseline_bots/ - each is a robot.xml + controller.py you can edit).
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOTS = ROOT / "mjarena" / "core" / "assets" / "baseline_bots"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--red", default="pusher")
    ap.add_argument("--blue", default="tetrahedron")
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--headless", action="store_true")
    a = ap.parse_args()

    red, blue = BOTS / f"baseline-{a.red}", BOTS / f"baseline-{a.blue}"
    cmd = [sys.executable, str(ROOT / "run_episode_viewer.py"),
           "--red-morphology", str(red / "robot.xml"), "--red-policy", str(red / "controller.py"),
           "--blue-morphology", str(blue / "robot.xml"), "--blue-policy", str(blue / "controller.py"),
           "--match-time", str(a.seconds), "--n-rollouts", "1"]
    if a.headless:
        out = ROOT / "demo" / "output" / "07_arena_match.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd += ["--headless", "--camera", "tracking", "--video-path", str(out)]
    else:
        cmd += ["--camera", "free"]
    env = dict(os.environ)
    if platform.system() == "Linux" and not env.get("DISPLAY"):
        env.setdefault("MUJOCO_GL", "egl")  # headless OpenGL on servers
    print(" ".join(cmd))
    code = subprocess.call(cmd, cwd=ROOT, env=env)
    if a.headless:
        seeded = out.parent / "seed_0.mp4"  # the viewer names per-seed videos seed_<N>.mp4
        if seeded.exists():
            seeded.replace(out)
        print(f"  video  -> {out.relative_to(ROOT)}")
    sys.exit(code)


if __name__ == "__main__":
    main()
