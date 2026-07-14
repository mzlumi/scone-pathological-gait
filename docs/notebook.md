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
- Throughput: about 4.5 simulations per second in the first generations (the
  model falls quickly), dropping as the gait improves and each simulation runs
  the full 10 s.
