# Roster-Consistent Latent Exploration B2 r02

This isolated package binds exact closed science revision
`RCLE-B2-SCIENCE-20260814-02`. Source existence and deterministic tests do not
authorize a registered stochastic object. Every RNG, roster, initialization,
training, and evaluation path requires both a passing exact-B2-r02 deterministic
certificate and a live Root-issued direction lease.

The implementation uses one CPU worker, no GPU, at most 2 GiB memory, atomic
both-arm seed packets, and complete-12-seed-only inference. If a process is
interrupted before a seed packet is installed, later execution replays the same
counter-addressed PCG64 coordinates; no partial result is exposed or selected.

Static commands:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.roster_consistent_latent_exploration_b2 certificate --output C:/ABS/rcle-b2-r02-certificate.json
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.roster_consistent_latent_exploration_b2 resource-proposal
```

Production is intentionally unavailable without an external authorization JSON
containing the exact direction/revision/result root, all authorized frozen
seeds, one CPU, zero GPUs, memory at most 2048 MiB, a nonempty lease token and
stage boundary, and a current timezone-aware validity interval. The preferred
full entry point is `formal-run`; `run-seed` supports result-blind continuation
between atomic seeds. `analyze` refuses to operate without all 12 packets.
