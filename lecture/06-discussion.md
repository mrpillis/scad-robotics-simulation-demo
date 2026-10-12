# 6 · Discussion and Resources

> *Provide accessible learning resources and lead an open discussion to support practical adoption.*

The session concludes with an interactive Q&A and curated resource sharing for
immediate implementation.

## Discussion prompts

Use one or two to open the floor if questions are slow to start.

1. Which project in your own practice — a sculpture, a film shot, a game, a product — could a robot simulation help you prototype?
2. Demo 4 used a hand-tuned colour threshold. How would you make it work under the lighting in this room? What would you change in the simulation to test that?
3. When is a simulation *good enough* to trust? Who decides, and how would you check?
4. Simulation makes failure cheap. Does that change how you would teach a studio class with robots?
5. Physical robots are expensive; simulated ones are free. What do students lose if they never touch hardware?

## Questions the audience often asks

**Do I need an NVIDIA GPU?** Not to start. Everything in this repository runs on a
laptop CPU, including Macs. You need an NVIDIA RTX GPU for Isaac Sim, and an
NVIDIA GPU for large-scale training with mjlab or Isaac Lab.

**Which simulator should our department standardise on?** Usually two: a
lightweight one every student can run (MuJoCo or Webots) and one heavyweight
one in a lab for advanced projects (Isaac Sim or Isaac Lab). Unity where the
curriculum is already built around it.

**Can I bring my own 3-D models?** Yes. Meshes (OBJ, STL) load into MuJoCo;
USD and FBX into Isaac Sim and Unity. For physics, keep a simplified collision
shape separate from the detailed visual mesh.

**How do I get from this demo to a real robot?** Keep the controller code
identical; swap the simulated sensor readings for the robot's driver. ROS 2 is
the common layer that makes this swap routine.

**Is this AI?** The demos use classic robotics (kinematics, mapping, A*, feedback
control) so every step is visible. The same simulators are where learned
controllers and perception models are trained; the leave-behind project includes
a learning track.

## Handouts

| Handout | File |
| --- | --- |
| Vocabulary list | [handouts/01-vocabulary.md](../handouts/01-vocabulary.md) |
| Additional learning resources | [handouts/02-learning-resources.md](../handouts/02-learning-resources.md) |
| Leave-behind project | [handouts/03-leave-behind-project.md](../handouts/03-leave-behind-project.md) |
| Visual guide | [handouts/04-visual-guide.md](../handouts/04-visual-guide.md) |
| Printable set (PDF) | [handouts/print/SCAD_Robotics_Simulation_Handouts.pdf](../handouts/print/SCAD_Robotics_Simulation_Handouts.pdf) |
