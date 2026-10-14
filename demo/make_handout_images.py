"""Copy the latest demo renders into handouts/img/ for the handouts and lecture notes."""

import shutil
from pathlib import Path

import imageio.v3 as iio

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
IMG = HERE.parent / "handouts" / "img"
IMG.mkdir(parents=True, exist_ok=True)

frame = iio.imread(OUT / "01_physics_playground.mp4", index=45)  # rubber ball mid-bounce
iio.imwrite(IMG / "01_physics.png", frame)
for src, dst in [("02_trajectory.png", "02_trajectory.png"), ("03_dashboard_still.png", "03_dashboard.png"),
                 ("04_pipeline_still.png", "04_pipeline.png"), ("05_sim_to_real_gap.png", "05_sim_to_real.png")]:
    shutil.copy(OUT / src, IMG / dst)
print("handout images ->", IMG.relative_to(HERE.parent))
