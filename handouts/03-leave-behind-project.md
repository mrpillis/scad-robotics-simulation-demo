# Handout 3 · Leave-Behind Project: "Teach a Robot to Find Its Way"

**Simulation for Robotics — SCAD · Savannah College of Art & Design — D. Pillis, Robotics Professor Demo**

Something to continue your learning after today. Everything runs on a laptop.
Choose **one track** at the end; Parts 1–3 are common to everyone.

```bash
git clone https://github.com/mrpillis/scad-robotics-simulation-demo && cd scad-robotics-simulation-demo
pip install -r requirements-demo.txt
python demo/03_sensor_dashboard.py
```

## Part 1 · Rebuild the room (about 1 hour)

Open `demo/assets/scad_lab.xml`.

1. Move two obstacles and add one of your own (a `box` or `cylinder` geom inside `<worldbody>`).
2. Change the floor's friction and the colours.
3. Run Demo 3 and press **g** for new goals. Does the robot still find its way?

*Deliverable:* a screenshot of your room and one sentence on what changed.

## Part 2 · Change the robot (about 1–2 hours)

1. Make the wheels 50 % larger. Update `WHEEL_RADIUS` in `demo/scad_sim.py` to match. What happens to top speed? To turning?
2. Remove five of the fifteen lidar beams (sites and sensors). Where does the robot start to fail?
3. Move the camera higher on the mast. What changes in Demo 4?

*Deliverable:* a short table: change → what you expected → what actually happened.

## Part 3 · Break it on purpose (about 1 hour)

Use `demo/05_sim_to_real_gap.py`.

1. Run with `--strength 2`. Which worlds fail, and why? (Look at the printed friction and motor values.)
2. In `scad_sim.Rover`, raise `latency_steps` until closed-loop control starts to fail. How many milliseconds is that?

*Deliverable:* one paragraph: what is the most important difference between your simulation and a real robot, and how would you test it?

## Part 4 · Choose a track (1–3 weeks)

### Track A · Studio (art, design, film, games)
Design an environment with a narrative — a gallery, a set, a public space — and
a robot whose path through it is part of the piece. Use the `studio` and `chase`
cameras (or add your own) to record a 30-second sequence. Optionally rebuild the
scene in Unity or Isaac Sim and compare the look and the behaviour.

### Track B · Engineering (control and perception)
Replace the orange-threshold detector in Demo 4 with something more robust:
detect a printed marker, or train a small classifier on images you render
yourself with automatic labels. Measure success across lighting changes.

### Track C · Research (learning and evaluation)
Pick one research question and answer it with experiments in simulation, e.g.
- How does lidar beam count trade off against success rate and path length?
- Can a learned policy (mjlab or MuJoCo Playground) match the A* planner here?
- Design a robot for the ArtifactArena ring (Demo 7) by hand, with an AI assistant, or both, and compare.

*Deliverable for all tracks:* a 3-minute video or presentation, your modified files,
and a one-page reflection: what simulation made possible, and what you would need
to test on real hardware.

## Assessment

| Criterion | Excellent | Developing |
| --- | --- | --- |
| **Process** | Changes are deliberate, documented and versioned | Changes are made but not explained |
| **Understanding** | Explains *why* the robot behaved as it did, using the vocabulary | Describes *what* happened only |
| **Sim-to-real thinking** | Names specific gaps and proposes a test for each | Mentions that reality is different |
| **Communication** | Clear visuals, readable files, concise reflection | Hard to follow or reproduce |
| **Ambition** | Goes beyond the starting code in a direction of your own | Stays within the examples |
