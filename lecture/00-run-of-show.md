# Run of Show — Simulation for Robotics

**SCAD · Savannah College of Art & Design — D. Pillis — Robotics Professor Demo**

A classroom presentation that moves from lecture to live demonstration and back,
the way a studio class would. Planned for about 55 minutes; the timings flex.

| Time | Segment | Mode | What happens | File |
| --- | --- | --- | --- | --- |
| 0:00 | Welcome, objectives | Lecture | Hand out the four handouts. State the learning objectives. | [README](../README.md#learning-objectives) |
| 0:03 | 1 · Why simulation | Lecture | Safe, scalable, cost-effective: the role of simulation in development, testing and education. | [01-why-simulation.md](01-why-simulation.md) |
| 0:12 | 2 · Choosing a platform | Lecture | Isaac Sim, mjlab / MuJoCo, Unity (plus Gazebo, Webots, Newton) on physics realism, GPU acceleration and sensor fidelity. | [02-choosing-a-platform.md](02-choosing-a-platform.md) |
| 0:22 | **Transition** | Lecture → Demo | "Let's stop talking about physics engines and open one." Switch to the terminal. | below |
| 0:23 | 3 · Live demo | Demo | Demos 1–5: physics, control, sensors, perception, sim-to-real. | [03-live-demo.md](03-live-demo.md) |
| 0:40 | **Transition** | Demo → Lecture | Leave Demo 5's figure on screen; it is the evidence for the next segment. | below |
| 0:41 | 4 · Simulation vs. hardware | Lecture | Advantages and constraints of running algorithms in simulation. | [04-sim-vs-hardware.md](04-sim-vs-hardware.md) |
| 0:46 | 5 · Selecting tools for your work | Lecture | Matching tools to coursework and to research projects. | [05-selecting-tools.md](05-selecting-tools.md) |
| 0:49 | 6 · Discussion and resources | Discussion | Open Q&A, the leave-behind project, curated resources. | [06-discussion.md](06-discussion.md) |

## Before class (15 minutes)

```bash
cd scad-robotics-simulation-demo
python demo/02_drive_the_robot.py     # opens? close it. (macOS: mjpython demo/02_drive_the_robot.py)
python demo/03_sensor_dashboard.py    # dashboard window opens? press q
bash demo/render_all.sh               # refresh the fallback videos in demo/output/
```

- Projector at 1920×1080; terminal font at 20 pt or larger.
- Open `demo/output/` in a file browser on a second desktop. If anything fails live,
  play the matching video from there and keep talking — the narration is the same.
- Print the handouts from `handouts/print/SCAD_Robotics_Simulation_Handouts.pdf`.

## The two transitions

The observers are watching for these moments, so script them.

**Lecture → demo (0:22).** End the platform comparison on the three criteria
(physics realism, GPU acceleration, sensor fidelity), then say:
*"Every one of those words is a setting in a file. I'll show you the file, change a number, and you'll see the robot behave differently."*
Open `demo/assets/scad_lab.xml` for ten seconds — the robot, its motors and its
sensors are about 150 lines of readable XML — then run Demo 1.

**Demo → lecture (0:40).** Demo 5 ends on a two-panel figure: the same robot
replaying "perfect" commands scatters across the room; the robot that senses and
re-plans reaches the goal almost every time. Leave it up and ask:
*"So, if simulation is never exactly right, why do we trust it at all?"*
That question opens Segment 4.

## Checking for understanding during the demo

Ask one question per demo before revealing the result:

1. Physics — "Which ball bounces highest? Which block slides?"
2. Control — "The autopilot is aimed at the goal. What's going to go wrong?" (it hits the blue box)
3. Sensors — "Which sensor told it the box was there?"
4. Perception — "If I turned the beacon green, what breaks?"
5. Sim-to-real — "Which strategy survives a dusty floor and a weak motor?"
