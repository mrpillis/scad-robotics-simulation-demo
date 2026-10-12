# 5 · Selecting Tools for Your Work

> *Select appropriate simulation tools tailored for specific coursework or advanced research projects.*

## Five questions

1. **What is the project about?** Experience and interaction · control and learning · sensing and perception · a full robot software stack.
2. **What hardware do students have?** Mixed laptops (including Macs) · a lab of NVIDIA RTX workstations · cloud GPUs.
3. **Will it go onto a real robot?** If yes, does that robot use ROS 2, and does its vendor ship a model for a particular simulator?
4. **How many runs are needed?** One robot watched live · hundreds of tests · millions of training episodes.
5. **How much setup time can the course afford?** One class session · a week · a semester.

## Decision guide

```text
Is photoreal sensor data the point (synthetic images, lidar, digital twin)?
 └─ yes ─► Isaac Sim  (needs RTX workstations)
 └─ no
    Is it reinforcement learning or contact-rich control at scale?
     └─ yes ─► mjlab / MuJoCo Warp  or  Isaac Lab
     └─ no
        Is it about people: interaction, VR/AR, installations, visualisation?
         └─ yes ─► Unity
         └─ no
            Is it a ROS 2 robot stack (navigation, SLAM, manipulation pipelines)?
             └─ yes ─► Gazebo
             └─ no ─► MuJoCo (Python) or Webots — fastest to start on any laptop
```

## Matching tools to coursework

| Course or project | Suggested tool | Why |
| --- | --- | --- |
| Introduction to robotics for designers and artists | MuJoCo (this repo) or Webots | Installs on any laptop in minutes; robots are readable files; immediate visual feedback |
| Interactive design, game development, immersive media | Unity | Students already know the editor; strong rendering; VR/AR and human–robot interaction |
| Animation and visual effects crossover (robot camera moves, performance robotics, previs) | Isaac Sim or Unity | OpenUSD (Isaac Sim) and Unity scenes fit existing film and game pipelines |
| Industrial design: testing a robot form before fabrication | MuJoCo | Mass, motor and stability checks straight from the design; fast iteration |
| Mobile robots with ROS 2 (navigation, mapping) | Gazebo | The ROS 2 community default; same launch files run on hardware |
| Advanced research: legged locomotion or manipulation learning | mjlab or Isaac Lab | GPU-parallel training, established sim-to-real workflows |
| Advanced research: perception, synthetic data, digital twins | Isaac Sim | Ray-traced sensors, automatic labels, USD scene assembly |
| Research on design and evaluation of robots themselves | MuJoCo + this repo's arena | Robots as code (MJCF + Python), automated verification and competition (ArtifactArena) |

## Practical advice

- **Start where the students are.** The best simulator for a class is the one that runs on every student's machine in the first session.
- **Keep the robot in a text file.** MJCF, URDF and USD can be versioned, diffed and reviewed like code.
- **Plan the hardware hand-off from day one.** Choose a simulator that has a model of the robot you will eventually use.
- **Budget for the install.** Isaac Sim needs a workstation and an afternoon; MuJoCo needs one `pip install`.
- **Combine tools.** Training in mjlab, visualising in Unity and validating in Isaac Sim is normal in research labs.
