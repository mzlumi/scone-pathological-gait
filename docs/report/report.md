---
title: "Predictive simulation of healthy and pathological gait with SCONE"
subtitle: "BIOENG-404 Analysis and Modelling of Locomotion, EPFL. SCONE assignment (2021 handout)"
author: "Parmida Mazloomi"
geometry: margin=2.2cm
fontsize: 10pt
colorlinks: true
---

# Setup

**Model.** `Human0914.osim` is a planar OpenSim 3 model with 9 degrees of
freedom (pelvis tilt, horizontal and vertical pelvis translation, hip, knee
and ankle on both legs) and 14 Hill-type muscles (hamstrings, gluteus maximus,
iliopsoas, vasti, gastrocnemius, soleus and tibialis anterior on each side).
Contact spheres at the heel and toes produce the ground reaction forces.

**Controller.** `ControllerComplexGH.scone` is the Geyer and Herr (2010)
reflex controller with extra velocity (V+) reflexes on soleus and
gastrocnemius. A state machine detects five gait phases per leg (early stance,
late stance, liftoff, swing, landing), and in each phase a set of reflexes of
the form
$u_m(t) = c_0 + k_l\,(l_m(t-\Delta t) - l_0) + k_v\,v_m(t-\Delta t) + k_f\,f_m(t-\Delta t)$
sets the muscle excitations. The 40 design parameters are reflex gains and
offsets plus initial joint angle offsets.

**Objective.** `MeasureGait.scone` adds up five measures:

| Measure | Weight | Penalizes |
|---|---|---|
| Gait | 100 | steps slower than `min_velocity`, and falling: the simulation stops when the centre of mass drops below 85 % of its initial height and the remaining time counts as standing still. Values below 0.05 count as 0 |
| Effort | 0.1 | metabolic cost of transport (Wang et al. 2012), in J/(kg m) |
| DofLimits | 0.1, 0.01 | ankle outside [-60, 60] deg; knee limit torque above 5 Nm |
| HeadStabilityY | 0.25 | vertical head acceleration beyond 0.5 g |
| HeadStabilityX | 0.25 | horizontal head acceleration beyond 0.25 g |

The gait term is roughly the fraction of the target speed that is missed,
averaged over the steps, so a model that walks the full 10 s at or above the
minimum speed scores 0 there. With the default
weights, a good healthy gait is dominated by the effort term.

**Optimization.** SCONE runs a 10 s forward simulation per candidate and
optimizes the parameters with CMA-ES (15 candidates per generation, 7
parents), starting from `InitParameters.par`.

**How the simulations were run.** The handout expects SCONE Studio on
Windows. Here the official Linux build of SCONE 2.4.5 (OpenSim 3.3 backend)
runs headless in Docker through its command line tool, so that every run can
be repeated from a terminal (`scripts/scone.sh`). The settings are identical
to the GUI. Evaluating a solution prints the objective broken down into its
measures, which is reported below for each best solution.

**Gait analysis.** SCONE Studio's Gait Analysis window was reimplemented in
Python (`src/scone_gait`), following its source code: gait cycles start at
foot contact (vertical ground reaction force above 0.001 body weight, stance
of at least 0.1 s), the first two and last cycles are dropped, every cycle is
resampled over 0 to 100 percent, and the mean curve is compared with the
normative band of SCONE Studio. The fit of one plot is
$100\,(1 - \overline{e_i / w_i})$, where $e_i$ is how far the mean lies
outside the band at the $i$-th normative sample and $w_i$ the band width; the
overall fit is the average over pelvis, hip, knee, ankle and ground reaction
force. A foot contact index locates the centre of pressure at initial contact
along the foot, from 0 at the heel to 1 at the metatarsal heads, to tell heel
strikes from forefoot strikes. Signs follow the SCONE plots: hip and knee
flexion positive, ankle dorsiflexion positive and plantarflexion negative.
