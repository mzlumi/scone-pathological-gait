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

# Deliverable 1: healthy gait

> *Please comment on the results obtained from the values of the objective
> functions and gait analysis tool after evaluating your solution. What can be
> improved in terms of gait properties (please elaborate)?*

**Optimization.** `HealthyGait.scone` was optimized for 50 generations. The
model first completed 10 s of walking at generation 15 (objective 1.17),
passed the 0.9 target at generation 20 (0.861), and reached its best value,
**0.780**, at generation 35. The last 15 generations brought no further
improvement, so the run had converged for this seed. The best solution is
`results/healthy/0035_1.021_0.780.par`.

| Measure | Weighted value | Raw value |
|---|---|---|
| Gait | 0 | step velocity 1.03 m/s over 17 steps (minimum 1.0) |
| Effort | 0.722 | cost of transport 7.22 J/(kg m) |
| DofLimits | 0 | knee limit torque 2.7 (left) and 2.8 Nm (right), below the 5 Nm threshold; ankle within range |
| HeadStabilityY | 0.022 | 0.088 |
| HeadStabilityX | 0.036 | 0.146 |
| **Total** | **0.780** | |

**Objective.** The model walks the whole 10 s slightly above the required
speed, so the gait term is zero, and 93 % of the objective is metabolic
effort. The cost of transport of 7.2 J/(kg m) is about twice the gross
metabolic cost measured in people walking at this speed (roughly 3 to 4
J/(kg m)), so the gait is stable but not efficient. The knee leans on its
extension limit (2.7 to 2.8 Nm of limit torque on every stance), which is
tolerated only because the joint limit measure ignores torques below 5 Nm.
Head accelerations stay small.

![Gait analysis of the healthy solution. Grey: normal range from SCONE Studio. Thin lines: individual left (blue) and right (red) cycles. Black: mean of 11 cycles.](../../results/figures/healthy_gait.png)

**Gait analysis.** Over 11 cycles the model walks at 1.01 m/s with a stride
of 1.26 m, a cadence of 96 steps/min and a stance phase of 66 % of the cycle.
The overall fit with the normal data is 72 %:

- **Pelvis and hip** are almost normal (fit 100 % and 97 %).
- **Knee** (fit 44 %): after a normal loading flexion of about 22 deg, the
  knee goes straight (0.7 deg at its least flexed) for the rest of stance,
  where people keep 5 to 10 deg of flexion. In swing it flexes to 80 deg
  instead of about 63 deg.
- **Ankle** (fit 69 %): the ankle plantarflexes quickly just after heel strike
  (foot slap, about -8 deg at 5 % of the cycle), dorsiflexes normally in
  midstance (peak 8 deg), but push-off is weak: the ankle only reaches -10 deg
  of plantarflexion, late (around 68 %), where people reach about -20 deg at
  62 %.
- **Ground reaction force** (fit 51 %): a sharp impact spike at heel strike,
  then a dip to about 0.5 body weight, and a second peak of 0.95 instead of
  about 1.1 body weight.

**What can be improved.**

1. *Push-off.* The weak plantarflexion and low second force peak show that
   the plantarflexors contribute little to propulsion; the long stance and the
   large swing knee and hip flexion suggest that the model compensates by
   pulling the leg forward from the hip. A stronger push-off would shorten
   stance and probably lower the cost of transport.
2. *Loading response.* The impact spike, the foot slap and the dip in the
   force come from a heel strike that is not cushioned: in people the
   tibialis anterior lowers the foot eccentrically and the knee flexes under
   load. Penalizing high vertical forces (SCONE's own tutorials add a measure
   on ground reaction forces above 1.5 body weight) would push the optimizer
   towards a softer landing.
3. *Knee in stance.* The straight, limit-loaded knee in midstance is not
   physiological. The joint limit measure could penalize any limit torque
   (threshold 0 instead of 5 Nm), or a small knee flexion target could be
   added.
4. *Swing knee flexion* is about 17 deg too large, which costs energy and
   reflects the hip driven gait above.
5. *Optimization.* CMA-ES finds a local optimum that depends on the initial
   guess and the random seed. Longer runs, restarts from different seeds and
   more realistic objectives (for example a target speed of 1.2 to 1.3 m/s,
   closer to preferred walking speed) would give a better gait. The model
   itself is limited too: it is planar, its foot is a single rigid segment
   without a toe joint, and the reflex controller has no feedforward
   component.
