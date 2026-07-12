# SCONE setup files

This folder holds every SCONE input used in the project. The first group was
provided by the course. Everything else is derived from those files, as the
handout asks, and is described in the report.

## Provided by the course

| File | Content |
|---|---|
| `HealthyGait.scone` | Main scenario: CMA-ES optimizer, 10 s simulation, model, controller and measure |
| `Human0914.osim` | Planar OpenSim 3 gait model `f0914m` (9 degrees of freedom, 14 muscles), by Thomas Geijtenbeek after Geyer and Herr (2010) |
| `InitStateGait.sto` | Initial state of the forward simulation |
| `InitParameters.par` | Initial guess for the 40 controller and initial state parameters |
| `ControllerComplexGH.scone` | Geyer and Herr (2010) reflex controller with extra soleus and gastrocnemius velocity (V+) reflexes |
| `MeasureGait.scone` | Objective: gait (min 1.0 m/s), effort (Wang 2012 cost of transport), joint limits, head stability |

The handout calls the last two files `Measure.scone` and `InitialStateGait.sto`.
The files shipped with the 2021 material are named `MeasureGait.scone` and
`InitStateGait.sto`, and `HealthyGait.scone` refers to them by those names, so
those names are kept here.

### Where these copies come from

The original 2021 material was distributed on EPFL Moodle, which is not
public. The copies here were recovered from the public repository of a 2021
student, [RenardDesNeiges/AnMod_4](https://github.com/RenardDesNeiges/AnMod_4),
which kept the provided inputs next to their own work. Only the unmodified
inputs were taken. The student's report, results and pathological scenarios
were not used.

Two checks support that the copies match what the course handed out:

1. `config.scone`, which SCONE writes into a results folder when an
   optimization starts, was compared with the files here. The controller,
   measure and model settings are identical. The student's `HealthyGait.scone`
   contained one extra, commented out `Properties` block (their own edit for
   the weakness task), which was removed.
2. SCONE's CMA-ES optimizer uses a fixed random seed, so the same scenario
   samples the same candidates. Running `HealthyGait.scone` here improves at
   the same generations as the student's healthy run, with nearly the same
   values (SCONE writes them into the result file names):

   | Generation | This repository (SCONE 2.4.5, Linux) | 2021 student run |
   |---|---|---|
   | 0 | 95.636 | 95.634 |
   | 2 | 94.465 | 94.464 |
   | 3 | 64.853 | 64.615 |
   | 4 | 54.268 | 54.297 |

   The small drift, which grows as the optimization goes on, is expected from
   a different SCONE version and platform. A different setup file would
   change the values from generation 0.
