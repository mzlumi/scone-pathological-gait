# Lab notebook

A running log of what was tried, what went wrong and what was decided. Newest
entries at the bottom.

## Finding the handout and the course files

- The 2021 handout and the provided setup files were found in a public 2021
  student repository (see [`scone/README.md`](../scone/README.md) for how the
  inputs were checked). No later edition of the SCONE assignment is public, so
  the 2021 handout is the specification.
- The EPFL coursebook page timed out from this network, and the Internet
  Archive was offline at the time. Course facts in the README come from EPFL
  Graph Search, the STI master's option lists and the BioRob teaching page.

## Running SCONE without the desktop app

- The handout recommends SCONE on Windows. SimTK requires a login to download
  installers, but the handout also points to the binaries built by the SCONE
  GitHub Actions. The newest Linux package from `tgeijten/scone-studio`
  (SCONE 2.4.5-RC-2, OpenSim 3.3 backend) runs in an amd64 Ubuntu 24.04
  container under emulation on Apple silicon.
- `sconecmd -o scenario.scone` optimizes, `sconecmd -e best.par` evaluates.
  Extra `key=value` arguments override scenario settings.
- **Mistake 1.** The first test passed `max_generations=5`. SCONE printed
  `Warning, unused properties: max_generations` and kept optimizing with the
  default limit of 100000 generations. The test was left running for almost an
  hour before this was noticed. The override needs the full path from the root
  of the scenario: `CmaOptimizer.max_generations=5`.
- **Mistake 2.** The results folder was mounted at
  `/root/Documents/SCONE/results`, but SCONE 2.4 on Linux writes to
  `/root/SCONE/results`, so nothing appeared on the host. `scripts/scone.sh`
  now mounts `results/runs` there.
- **Mistake 3.** With OrbStack, `docker run --platform linux/amd64` on a
  locally built amd64 image tried to pull it from Docker Hub and failed. The
  image already has the right platform, so the flag was dropped from
  `docker run`.
- **Mistake 4.** The first evaluation passed `-r <name>.sto`. SCONE appends
  `.sto` itself, so the file came out as `<name>.sto.sto`. The runner now
  passes the `.par` path, which gives `<name>.par.sto`, the same name SCONE
  Studio uses, and saves the printed objective breakdown as `<name>.par.txt`.
- With `-s`, `sconecmd` output is block buffered when it goes to a file, so the
  log lags far behind. The file names in the results folder
  (`<generation>_<average>_<best>.par`) are the reliable progress indicator.
- Throughput: about 4.5 simulations per second in the first generations (the
  model falls quickly), dropping as the gait improves and each simulation runs
  the full 10 s.

## Planning the pathological runs

- Cost: one simulation of 10 s takes about 22 s of CPU under emulation, a
  generation has 15 simulations, so 200 generations cost about 18 core hours
  however the runs are scheduled. Several runs go side by side with 3 threads
  each, and a run can be stopped once it has plateaued (the handout asks to
  stop when the gait is good enough and never to exceed 200 generations).
- Sweep scenarios live in `scone/sweeps/`. The chosen value of each deliverable
  is copied into the file name the handout asks for (`Weakness.scone`,
  `Hyperreflexia.scone`, `Model.scone`) at the end.

### The hyperreflexia recipe lets the optimizer undo the impairment

The handout models hyperreflexia by changing the stance velocity reflex of
soleus and gastrocnemius from `KV = ~0.1<0,10>` to `KV = ~1.0<0,10>`. The
tilde makes KV a design parameter: CMA-ES starts it at 1.0 (with a spread of
10 percent of the mean) but can move it anywhere in [0, 10].

The healthy run shows what the optimizer does with these gains when it is
free to: by generation 21 the stance KV of soleus fell from 0.10 to 0.039 and
that of gastrocnemius from 0.10 to 0.005. Velocity feedback in the
plantarflexors costs effort and destabilizes the gait, so the optimizer
removes it. Starting at 1.0 only delays that.

A spastic patient cannot switch off their stretch reflex, so the impairment
should be a property of the model, not something the optimizer may tune. The
SCONE hyper-reflexia tutorial adds its extra reflex with constant gains for
the same reason. Both versions are run: `hyperreflexia_free1.0` follows the
handout literally and `hyperreflexia_fixed1.0` holds KV at 1.0.

### First batch: what happened

- **Healthy** (`HealthyGait.scone`, 50 generations): first full 10 s walk at
  generation 15, below the 0.9 target at generation 20, best 0.780 at
  generation 35, no improvement afterwards.
- **Weakness x 0.25 stopped.** After 60 generations the best objective was
  still about 94: the model fell within the first steps of every simulation
  and the optimizer had found nothing better since generation 0. At a quarter
  of normal plantarflexor strength the course controller, started from
  `InitParameters.par`, cannot find a stable gait within the budget. The run
  was stopped to free its cores. This is kept as a negative result rather
  than tried again with tricks.
- **Weakness x 0.5 is slow**: objective 59.9 after 54 generations, so it still
  falls before 10 s. Folder names in the 2021 student repository show the
  same pattern for their weakness run (stuck near 50 until generation 84,
  then walking), so it is left running.
- **The handout hyperreflexia recipe drifts as predicted**: by generation 17
  the free stance KV of soleus had already dropped from 1.0 to 0.48 (the
  gastrocnemius gain stayed near 1.0).
- Early evaluations at generation 13 to 17 already show toe walking in the
  plantarflexor contracture run and in both hyperreflexia runs: first contact
  on the toe spheres (contact index about 1.24) with the ankle 5 to 10 deg
  plantarflexed, no heel strike transient.
