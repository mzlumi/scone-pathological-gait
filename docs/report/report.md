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

# Deliverable 2: heel walking from plantarflexor weakness

> *Please comment on the results obtained from the values of the objective
> functions and gait analysis tool after evaluating your solution. What are
> the main kinematic adaptations when the plantar flexors are weakened (please
> elaborate)?*

**Setup.** `Weakness.scone` is `HealthyGait.scone` with the maximum isometric
force of soleus and gastrocnemius scaled on both legs and with
`Measure05.scone` (minimum speed 0.5 m/s). Three factors were tried with the
handout method (start from `InitParameters.par`, at most 200 generations):

| Factor | Outcome |
|---|---|
| 0.25 | never walked: best objective about 94 after 60 generations (the model falls in the first steps), stopped |
| **0.5** | **walked from generation 176, best 1.196 at generation 198. Chosen value** |
| 0.7 | walked from generation 19, best 0.965 at generation 99 |

As a check that the pattern does not depend on the optimizer's path, factor
0.5 was also optimized from the healthy solution (warm start, 112
generations, best 0.880). This is a deviation from the handout and is only
used for comparison.

| Measure | Healthy | x 0.7 | **x 0.5** | x 0.5 warm |
|---|---|---|---|---|
| Gait | 0 | 0 | **0** | 0 |
| Effort (cost of transport, J/(kg m)) | 0.722 (7.22) | 0.754 (7.54) | **0.852 (8.52)** | 0.801 (8.01) |
| DofLimits (knee limit torque, Nm) | 0 (2.7) | 0.129 (6.7) | **0.187 (9.4)** | 0 (2.9) |
| HeadStabilityY | 0.022 | 0.031 | **0.093** | 0.032 |
| HeadStabilityX | 0.036 | 0.051 | **0.064** | 0.047 |
| **Total** | 0.780 | 0.965 | **1.196** | 0.880 |
| Step velocity (m/s) | 1.03 | 0.87 | **0.63** | 0.85 |

**Objective.** The weakened model meets the lower speed requirement (0.63
m/s against 0.5 m/s), so the gait term stays at zero, but every other term
gets worse. Walking costs 18 % more energy per metre than in health even
though it is slower, the knee now presses against its extension limit hard
enough to be penalized (9.4 Nm, above the 5 Nm threshold), and vertical head
accelerations are four times larger. The convergence is the most telling
number: the weakened model needed 176 generations to find any gait that
does not fall, against 15 in health, and a quarter of the normal strength was
not enough at all. Plantarflexors are central to balance in this controller:
the soleus force reflex is what stops the shank from rotating forward over
the foot in stance.

![Mean gait cycles of the weakened models against the healthy solution. Grey: normal range.](../../results/figures/weakness_comparison.png)

![Gait analysis of the plantarflexor weakness x 0.5 solution (`Weakness.scone`).](../../results/figures/weakness_0.50_cold_gait.png)

| Metric | Healthy | x 0.7 | **x 0.5** | x 0.5 warm |
|---|---|---|---|---|
| Speed (m/s) | 1.01 | 0.86 | **0.65** | 0.84 |
| Stride length (m) | 1.26 | 1.28 | **1.08** | 1.14 |
| Cadence (steps/min) | 96 | 80 | **72** | 89 |
| Stance (% of cycle) | 66 | 69 | **75** | 71 |
| Ankle at contact (deg) | 4.6 | 9.8 | **10.1** | 16.1 |
| Peak dorsiflexion in stance (deg) | 8.4 | 12.6 | **13.2** | 18.0 |
| Peak plantarflexion (deg) | -10.2 | -4.6 | **-4.5** | -0.2 |
| Knee, least flexed in stance (deg) | 0.7 | -3.2 | **-8.3** | 1.4 |
| Foot contact index | 0.00 | -0.02 | **-0.01** | -0.05 |
| Overall fit (%) | 72 | 45 | **40** | 37 |

**Kinematic adaptations.** The weakened model walks on its heels:

1. *Excessive dorsiflexion.* The foot lands on the heel (contact index about
   0) with the ankle dorsiflexed by 10 deg instead of 5 deg, and the shank
   keeps rotating forward over the foot through stance, up to 13 deg of
   dorsiflexion (18 deg with the warm start) where the healthy model stops at
   8 deg. Weak plantarflexors cannot brake the forward rotation of the tibia
   in midstance and late stance.
2. *No push-off.* Healthy late stance ends with a quick plantarflexion to -10
   deg; with half the strength the ankle barely passes neutral (-4.5 deg,
   -0.2 deg with the warm start), so the "ankle rocker" that propels the body
   is lost. The second ground reaction force peak is replaced by a long,
   flat load, and stance stretches to 75 % of the cycle.
3. *Slow, short, careful steps.* Speed falls from 1.01 to 0.65 m/s, mostly
   through cadence (96 to 72 steps/min) and stride length (1.26 to 1.08 m).
4. *A knee strategy.* Without the soleus to hold the shank, the cold solution
   locks the knee in hyperextension through stance (-8 deg), letting the
   passive knee limit carry the load. The warm-started solution keeps the knee
   near straight but dorsiflexes even more and extends the hip less. Both are
   compensations for the missing ankle moment, and they show that the
   optimizer can land in different local optima for the same impairment.

The effects grow with the weakness: x 0.7 already shows every adaptation in a
milder form. These patterns match the calcaneal gait seen after
plantarflexor weakness, for example after over-lengthening of the Achilles
tendon in cerebral palsy, where excessive stance dorsiflexion and lost
push-off are the hallmark. Clinically the knee usually ends up flexed
(crouch) rather than hyperextended; the model's knee hyperextension is
allowed by its soft knee limit and by an objective that tolerates limit
torque.
