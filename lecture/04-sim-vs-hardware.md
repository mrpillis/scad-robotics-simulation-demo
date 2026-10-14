# 4 · Simulation vs. Physical Hardware

> *Identify key advantages and constraints of running robotics algorithms in simulated environments versus physical hardware.*

## Side by side

| | Simulation | Physical hardware |
| --- | --- | --- |
| **Cost** | A laptop; marginal cost of one more robot is zero | Robots, spares, batteries, space, repairs |
| **Safety** | Crashes are free | Crashes break hardware and can hurt people |
| **Speed** | Faster than real time; Demo 6 measures 100×+ for one rover on a laptop CPU, far more in parallel on a GPU | Exactly real time, minus charging and resets |
| **Scale** | Thousands of parallel worlds | One robot, one world at a time |
| **Repeatability** | Same seed, same result | Never quite the same twice |
| **Observability** | Perfect ground truth: every position, force and contact | Only what your sensors and motion capture can measure |
| **Edge cases** | Created on demand (ice, sensor failure, a person stepping in) | Rare, dangerous or impossible to stage |
| **Fidelity** | A model: simplified contact, ideal motors, clean sensors | Reality, including everything you forgot to model |
| **Surprises** | Only the ones you programmed | Cable snags, glare, wheel wear, Wi-Fi drop-outs, heat |
| **Final validation** | Cannot certify a robot | The only place a robot is actually proven |

## Where simulations are usually wrong

- **Contact and friction.** One friction coefficient stands in for dust, wear, temperature and surface texture.
- **Actuators.** Real motors have backlash, current limits, heating and delay. In Demo 3 the encoder trace lags the command even in simulation; on hardware it is worse.
- **Sensing.** Real cameras have motion blur, exposure changes and lens distortion; real lidar misses glass and black surfaces.
- **Timing.** Real systems have latency and jitter between sensing and acting. Demo 5 adds 30 ms.
- **Unmodelled things.** Cables, deformable parts, people, other robots, the building's Wi-Fi.

Policies trained in simulation can also learn to **exploit** the simulator — a
physics glitch that gives free speed, a sensor that never fails. Those behaviours
disappear on hardware.

## Closing the gap

1. **Feedback over replay.** Closed-loop control corrects errors the model did not predict (Demo 5).
2. **Domain randomization.** Train and test across many plausible worlds so the real one is "just another sample" (Tobin et al., 2017).
3. **System identification.** Measure the real robot — mass, friction, motor response — and tune the simulator to match.
4. **Realistic sensor models.** Add noise, latency, dropout and limited range on purpose.
5. **Hardware in the loop and staged deployment.** Simulation → tethered or slow hardware tests → full deployment, with the same code at every stage.
6. **Keep the sim honest.** Every surprise on hardware becomes a new simulated test case.

## Rule of thumb for the classroom

**Simulate first, simulate most, test on hardware early and often.**
Use simulation to make mistakes cheaply and to learn concepts; use hardware to
learn humility, and to discover what the model was missing.
