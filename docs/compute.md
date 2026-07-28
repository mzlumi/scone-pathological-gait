# Compute: hardware, timings and cost

Everything in this repository was simulated on one laptop. This page records
the machine, how fast SCONE ran on it, and what each optimization cost, so the
numbers in the report can be put in context and the runs can be planned
elsewhere.

## Machine and software

| Item | Value |
|---|---|
| Computer | Apple M5, 10 cores (4 performance, 6 efficiency), 16 GB RAM |
| Operating system | macOS 27.0.1 |
| Container runtime | OrbStack 2.2.3, Docker 29.4.0; Linux VM with 10 CPUs and 8 GB RAM |
| SCONE | 2.4.5-RC-2, Linux amd64 build from the scone-studio CI, OpenSim 3.3 backend |
| Emulation | amd64 image on an arm64 host, run through Rosetta inside OrbStack |
| Image size | 323 MB (`scone-headless:latest`) |
| Python tools | Python 3.12, NumPy, Matplotlib |

## Measured speed

All timings are for the planar `f0914m` model and a 10 s simulation.

| Measurement | Result |
|---|---|
| One healthy-gait simulation, machine idle | 5.1 to 5.9 s (1.7 to 2.0 times faster than real time) |
| One generation of 15 walking candidates, 10 threads | 19 s |
| One generation of 15 walking candidates, 3 threads | 23 s |
| One evaluation while several optimizations shared the machine | 7 to 37 s (0.27 to 1.4 times real time) |

The benchmark generations (4 generations warm started from the healthy
solution) gave **identical optimization histories with 3 and 10 threads**, so
results do not depend on the thread count, only the speed does.

Three things set the cost of a run more than the number of generations:

- **Parallel scaling is weak on this chip.** Going from 3 to 10 threads made a
  generation only about 20 % faster. Only 4 cores are performance cores, the
  rest are slower efficiency cores, and every thread runs under emulation.
  Running several optimizations side by side with 3 threads each used the
  machine better than one optimization with all 10.
- **Falling is cheap, stumbling is expensive.** A simulation stops as soon as
  the model falls, so early generations and runs that never learn to walk are
  fast. The generations around the moment a gait is found were the slowest:
  about 40 to 80 s per generation for the healthy run with the machine almost
  to itself, against 19 s for candidates close to the converged gait. The
  likely reason is OpenSim's variable-step integrator, which takes many small
  steps on stumbling, contact-heavy motions.
- **Sharing.** With 4 to 7 optimizations running at once, a generation took
  1 to 3 minutes of wall time per run.

An earlier estimate in the notebook ("about 22 s of CPU per simulation, 18
core hours per 200 generations") was based on timings taken while several runs
competed for the CPU. The idle measurements above replace it.

## Every optimization

Start times are UTC. Wall times run from the start to the last file the
optimizer wrote, with other runs sharing the machine most of the time, so they
are not comparable with each other. Generation counts are approximate for
runs that were stopped by hand, because `history.txt` is written in blocks of
10 generations.

| Run | Start | Generations | Wall time (h) | Outcome |
|---|---|---|---|---|
| Healthy | 07-16 05:58 | 50 | 1.9 | best 0.780 |
| Weakness x 0.25 | 07-16 06:25 | about 70 | 0.7 | never walked, stopped |
| Weakness x 0.5 | 07-16 06:25 | 200 | 6.1 | walked from generation 176, best 1.196 |
| Hyperreflexia, handout recipe | 07-16 06:25 | about 107 | 8.2 | best 1.295 |
| Hyperreflexia, KV 1.0 | 07-16 06:25 | about 101 | 7.9 | best 1.227 |
| Contracture x 0.95 | 07-16 07:10 | about 100 | 7.5 | best 1.146 |
| Crouch, hamstrings x 0.90 | 07-16 08:02 | about 150 | 2.1 | never walked, stopped |
| Weakness x 0.7 | 07-16 10:12 | about 100 | 4.5 | best 0.965 |
| Weakness x 0.5, warm start | 07-16 10:12 | about 112 | 4.3 | best 0.880 |
| Crouch, hamstrings x 0.90, warm start | 07-16 10:12 | 200 | 3.2 | never completed 10 s |
| Hyperreflexia, KV 0.3 | 07-16 12:39 | about 100 | 2.9 | best 1.330 |
| Crouch, hamstrings x 0.95, warm start | 07-16 13:40 | about 80 | 1.9 | best 0.958 |
| Hyperreflexia, KV 3.0 | 07-16 14:48 | 200 | 2.7 | falls at 9 s, best 14.2 |
| Contracture x 0.90 | 07-16 14:49 | about 150 | 3.5 | best 1.014 |
| Crouch, hamstrings and iliopsoas x 0.95, warm start | 07-16 15:43 | about 190 | 2.7 | best 0.859 |

## Totals

| Item | Value |
|---|---|
| Optimizations | 15 |
| Generations | about 1,900 |
| Simulations | about 28,000 (14 or 15 per generation) |
| Wall time of the whole campaign | about 12.5 h (07-16 05:58 to 07-16 18:29 UTC), with 2 to 7 runs in parallel |
| Raw optimization output | 66 MB (`results/runs/`, not committed) |
| Curated results and figures | 48 MB in the repository |
| Submission archive | 18 MB zipped (48 MB unpacked, 166 files) |

## Doing it faster

- **Native builds.** SCONE ships native Windows and Linux builds; on an x86
  machine there is no emulation layer.
- **Many runs, few threads each.** On this machine the best throughput came
  from 3 or 4 optimizations at 3 threads each.
- **Hyfydy.** SCONE can also use the Hyfydy simulator, which its author
  reports as 50 to 100 times faster than OpenSim. It needs a separate license,
  and the course model and results here use OpenSim 3.
- **Stop early.** Most pathological runs had flattened out well before 200
  generations; the convergence plot in the report shows where.
