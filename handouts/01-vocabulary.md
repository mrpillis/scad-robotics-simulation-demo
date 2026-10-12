# Handout 1 · Vocabulary

**Simulation for Robotics — SCAD · Savannah College of Art & Design — D. Pillis, Robotics Professor Demo**

### Simulation and physics

| Term | Meaning |
| --- | --- |
| **Simulation** | Running a model of a robot and its world on a computer to predict what would happen in reality. |
| **Physics engine** | Software that computes motion from forces: gravity, contact, friction, motors. MuJoCo, PhysX and Newton are physics engines. |
| **Time step** | The small slice of time the engine advances per update (2 ms in the demos). Too large and contacts become unstable. |
| **Real-time factor** | Simulated seconds per wall-clock second. 100× means 100 s of robot experience every second. |
| **Rigid body** | An object assumed not to bend. Most robot links are modelled this way. |
| **Joint** | A connection that lets two bodies move relative to each other: hinge (rotates), slide (translates), free (6 degrees of freedom). |
| **Degrees of freedom (DoF)** | The number of independent ways something can move. A free-floating body has 6. |
| **Contact model** | How the engine decides that two objects touch and what forces they exchange. |
| **Friction coefficient** | A number describing how strongly surfaces resist sliding. Steel on a smooth floor is low; rubber is high. |
| **Restitution** | Bounciness: how much speed survives a collision. |
| **Collision geometry** | Simple shapes (boxes, spheres, capsules) used for physics, often separate from the detailed visual mesh. |
| **Actuator** | Anything that makes a robot move: a motor, a servo, a piston. |
| **Servo** | A motor with a built-in controller that holds a target position or velocity. |

### Describing robots and scenes

| Term | Meaning |
| --- | --- |
| **MJCF** | MuJoCo's XML format describing bodies, joints, actuators and sensors. `demo/assets/scad_lab.xml` is MJCF. |
| **URDF** | Unified Robot Description Format; the ROS standard XML for robot links and joints. |
| **OpenUSD** | Universal Scene Description; a scene format from Pixar's film pipeline, used by Isaac Sim and Omniverse. |
| **Digital twin** | A simulation kept closely matched to a specific real robot, room or factory. |
| **ROS 2** | Robot Operating System 2; the common middleware that connects sensors, algorithms and motors on real robots and in simulators. |

### Sensing and perception

| Term | Meaning |
| --- | --- |
| **Sensor emulation** | Producing the data a real sensor would produce, including its range, rate and noise. |
| **Encoder** | Measures how far or fast a wheel or joint has turned. |
| **IMU** | Inertial Measurement Unit: an accelerometer and a gyroscope measuring acceleration and rotation rate. |
| **Lidar** | A laser range sensor that measures distances along many beams; the demo rover has 15. |
| **RGB-D camera** | A camera that returns colour (RGB) and depth (D) for every pixel. |
| **Ground truth** | The exact, true state of the world, known in simulation and only estimated on hardware. |
| **Perception pipeline** | The chain of steps that turns raw sensor data into decisions, e.g. image → threshold → blob → bearing → steering. |
| **Occupancy grid** | A map divided into cells, each marked free or occupied; built from lidar in Demo 3. |
| **SLAM** | Simultaneous Localization and Mapping: building a map while working out where you are in it. |
| **Synthetic data** | Simulated images or scans with automatic labels, used to train perception models. |
| **Sensor fidelity** | How closely a simulated sensor matches the real one. Ray-traced sensors are higher fidelity than idealised ones. |

### Control and autonomy

| Term | Meaning |
| --- | --- |
| **Differential drive** | Steering by running left and right wheels at different speeds. |
| **Kinematics** | The geometry of motion, without forces: how wheel speeds become robot motion. |
| **Open-loop control** | Sending pre-planned commands without checking the result. |
| **Closed-loop (feedback) control** | Measuring the result and correcting continuously. |
| **Proportional (P) controller** | A feedback controller whose correction is proportional to the error. |
| **Path planning (A\*)** | Searching a map for the shortest collision-free route. |
| **Pure pursuit** | Following a path by steering toward a point a fixed distance ahead on it. |
| **Sense–plan–act loop** | The cycle at the heart of robot autonomy: read sensors, decide, move, repeat. |

### Sim-to-real and scale

| Term | Meaning |
| --- | --- |
| **Reality gap / sim-to-real gap** | The difference between simulated and real behaviour. |
| **Sim-to-real transfer** | Moving software developed in simulation onto a physical robot. |
| **Domain randomization** | Varying physics, visuals and sensors across many simulated worlds so software works in all of them — including the real one. |
| **System identification** | Measuring a real robot's properties to tune the simulator to match. |
| **Latency** | Delay between sensing and acting. |
| **Hardware-in-the-loop** | Testing real hardware components connected to a simulation. |
| **GPU acceleration** | Running physics (and rendering) on a graphics card to simulate thousands of worlds in parallel. |
| **Reinforcement learning (RL)** | Learning a controller by trial and error from rewards, usually inside a simulator. |
| **Parallel environments** | Many copies of a simulation stepped at once, for testing or training. |
