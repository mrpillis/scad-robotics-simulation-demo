# 2 · Choosing a Platform

> *Compare industry-standard simulation platforms to help educators and researchers choose the right workflow.*
>
> *Evaluate simulation frameworks (e.g., Isaac Sim, Unity, etc) based on physics realism, GPU acceleration, and sensor fidelity.*

Contrasting leading platforms — NVIDIA Isaac Sim, mjlab (MuJoCo), and Unity — to
guide engine selection for specific research and classroom needs, with Gazebo,
Webots and Newton for context. Versions and requirements were checked in
October 2026; these tools move quickly, so confirm against the links before
adopting one for a course.

## The three criteria

**Physics realism** — how faithfully the engine reproduces contact, friction,
joints and motors. Watch for: stable stacking and grasping, joint limits that
do not "explode", and whether the time step has to be tiny to stay stable.

**GPU acceleration** — whether physics (not only graphics) runs on the GPU, so
that thousands of worlds can be stepped in parallel. This is what makes
reinforcement learning practical; it matters much less for a single robot in a
classroom.

**Sensor fidelity** — how close simulated sensors are to real ones. Ranges from
"perfect numbers" (ideal position, clean depth) through rasterised cameras and
ray-cast lidar to ray-traced cameras, lidar and radar with materials, noise
models and lens effects.

## At a glance

| | **NVIDIA Isaac Sim** (+ Isaac Lab) | **mjlab** (MuJoCo + MuJoCo Warp) | **Unity** (+ Robotics Hub, ML-Agents) |
| --- | --- | --- | --- |
| **Physics realism** | PhysX 5 articulations; Newton backend available in 6.0. Strong for rigid bodies, grasping, vehicles | MuJoCo: the reference for accurate, stable contact in control and RL research | PhysX `ArticulationBody`; tuned for games first. Good enough for interaction, weaker for precise contact |
| **GPU acceleration** | Yes — GPU physics; Isaac Lab runs thousands of parallel environments | Yes — MuJoCo Warp; thousands of parallel environments (NVIDIA GPU for training) | Graphics on GPU; physics on CPU. Parallel training via ML-Agents, at smaller scale |
| **Sensor fidelity** | Highest: RTX ray-traced cameras, lidar and radar; synthetic data with labels | Rasterised RGB-D cameras, ray-cast rangefinders, IMU, touch, force/torque | High-quality rendering (HDRP) for cameras; lidar and others via packages or custom scripts |
| **Hardware** | RTX GPU with ≥ 16 GB VRAM (6.0 minimum: RTX 4080), 32 GB RAM; Ubuntu 22.04/24.04 or Windows 11; no macOS | MuJoCo runs on any laptop (macOS, Windows, Linux). mjlab: NVIDIA GPU to train; macOS for evaluation only | Any recent laptop; macOS, Windows, Linux |
| **Formats** | OpenUSD; imports URDF, MJCF | MJCF (XML); URDF import | Unity scenes, FBX/OBJ; URDF Importer package |
| **ROS 2** | Built-in bridge | Through community packages | ROS-TCP-Connector |
| **License** | Isaac Sim source on GitHub (Apache 2.0) with Omniverse dependencies under NVIDIA terms | Apache 2.0 | Proprietary engine; free Personal tier, education licences |
| **Learning curve** | Steep: large application, USD concepts, heavy install | Moderate: Python + XML; mjlab adds the Isaac Lab "manager" API | Gentle for students who already know Unity |

## NVIDIA Isaac Sim and Isaac Lab

**What it is.** A robotics simulator built on NVIDIA Omniverse and OpenUSD.
Isaac Lab sits on top for robot learning (reinforcement and imitation learning).
Version 6.0 shipped in June 2026.

**Choose it when** you need photoreal sensor data — training a vision model on
synthetic images, testing a lidar pipeline, building a digital twin of a real
space — or large-scale learning with NVIDIA's tooling and robot assets.

**Watch out for** hardware: it needs an RTX workstation (no Apple Silicon, no
data-centre GPUs without RT cores), a large install, and time to learn USD.

**Why it matters at an art and design school.** OpenUSD began at Pixar as a
film-pipeline format. Students from animation, visual effects and games already
think in USD stages, layers and materials — the same scene description Isaac Sim uses.

Links: [docs](https://docs.isaacsim.omniverse.nvidia.com) ·
[requirements](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/installation/requirements.html) ·
[source](https://github.com/isaac-sim/IsaacSim) ·
[Isaac Lab](https://isaac-sim.github.io/IsaacLab)

## mjlab, MuJoCo and MuJoCo Warp

**What it is.** MuJoCo (Multi-Joint dynamics with Contact) is Google DeepMind's
open-source physics engine and the default in much control and RL research.
MuJoCo Warp runs it on NVIDIA GPUs. **mjlab** combines Isaac Lab's
manager-based API with MuJoCo Warp, so the Isaac Lab workflow runs on
lightweight, open MuJoCo physics (Zakka et al., 2026).

**Choose it when** contact dynamics matter (legged robots, manipulation), when
you want to read and edit the whole robot in one XML file, or when you teach on
laptops: plain MuJoCo installs with `pip install mujoco` on macOS, Windows and Linux.
This repository's demos use MuJoCo for exactly that reason.

**Watch out for** rendering: cameras are rasterised OpenGL, not ray-traced, so it
is not the tool for photoreal synthetic data. mjlab's GPU training needs an NVIDIA GPU.

```bash
uvx --from mjlab --refresh demo     # try mjlab without installing
pip install mujoco                  # plain MuJoCo, any laptop
```

Links: [MuJoCo docs](https://mujoco.readthedocs.io) ·
[mjlab](https://github.com/mujocolab/mjlab) ·
[mjlab paper](https://arxiv.org/abs/2601.22074) ·
[MuJoCo Warp](https://github.com/google-deepmind/mujoco_warp) ·
[MuJoCo Playground](https://playground.mujoco.org)

## Unity

**What it is.** A game engine with a large asset ecosystem and strong
real-time rendering. Unity's Robotics Hub provides a URDF Importer and a ROS-TCP
connector; ML-Agents adds reinforcement learning.

**Choose it when** the project is about people and experience: human–robot
interaction studies, VR/AR teleoperation, interactive installations,
visualising a robot's data, or a class of game-development students.

**Watch out for** contact-rich physics (game physics trades accuracy for speed),
and check activity on the robotics packages before building a course around them;
their published support targets older ROS and Unity versions.

Links: [Unity Robotics Hub](https://github.com/Unity-Technologies/Unity-Robotics-Hub) ·
[ML-Agents](https://github.com/Unity-Technologies/ml-agents)

## Also worth knowing

| Platform | One-line summary | Link |
| --- | --- | --- |
| **Gazebo** (Jetty, LTS to 2030) | The ROS 2 community's simulator; the natural choice when the course is "build a full ROS 2 robot stack" | [gazebosim.org](https://gazebosim.org) |
| **Webots** | Open-source, cross-platform, gentle learning curve, many robot models; good for first courses | [cyberbotics.com](https://cyberbotics.com) |
| **Newton** | New open-source GPU physics engine (NVIDIA, Google DeepMind, Disney Research; Linux Foundation, Apache 2.0) built on Warp with MuJoCo Warp as its main backend | [github.com/newton-physics/newton](https://github.com/newton-physics/newton) |

## A one-sentence summary for students

Use **Unity** when the experience matters most, **MuJoCo / mjlab** when the
physics and learning matter most, and **Isaac Sim** when the sensors and
photorealism matter most — and expect to combine them.
