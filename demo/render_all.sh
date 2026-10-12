#!/usr/bin/env bash
# Record every demo to demo/output/ (fallback videos for the live session)
# and refresh the images used by the handouts. Takes a few minutes.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
$PY demo/01_physics_playground.py --headless
$PY demo/02_drive_the_robot.py --headless
$PY demo/03_sensor_dashboard.py --headless
$PY demo/04_camera_perception.py --headless
$PY demo/05_sim_to_real_gap.py
$PY demo/06_scale_and_speed.py --no-camera
if [[ "${WITH_ARENA:-0}" == "1" ]]; then $PY demo/07_robot_arena_match.py --headless --seconds 15; fi
$PY demo/make_handout_images.py
echo "done: see demo/output/ and handouts/img/"
