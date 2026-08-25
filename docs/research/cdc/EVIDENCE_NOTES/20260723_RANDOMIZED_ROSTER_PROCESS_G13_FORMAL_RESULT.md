# Randomized roster-process G13 formal result

Date: 2026-07-23

The exact source `e3ffabb5e7d6207546c035552f7ed678af841e17`
completed at `logs/formal_random_roster_g13_cpu_20260723_e3ffabb_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=18
utility_values=864
source_control_rows=144
operational_valid=true
operational_errors=[]
branch=ROBUST_RANDOMIZED_ROSTER_PROCESS_G13
```

All 144 domain/episode source rows have unique identities and recomputed exact
event signatures. They collectively contain every temporary-leave, rejoin,
terminal-leave and join operation; every 12-event transition schedule, wave
requirement, constructive outcome and sampled lifecycle check closes. The 18
behavior cells contain 864 values, retain exact model state, and use three exact
copies of the frozen G8 finals with zero optimizer steps.

```text
random_moderate_deterministic_utility_ci95=[0.9249674479166666,0.9501330344342881,0.9994876449695314]
random_wide_deterministic_utility_ci95=[0.9270833333333334,0.9518953772001645,0.9995663399338266]
random_ultra_deterministic_utility_ci95=[0.9283854166666666,0.9527839583842549,0.9996279168194316]
random_ultra_replicate_means=[0.9283854166666666,0.9996279168194316,0.9303385416666666]
random_ultra_min_replicate_mean=0.9283854166666666
random_ultra_stochastic_mean=0.8892955279616425
```

Independent closure reproduced `ROBUST_RANDOMIZED_ROSTER_PROCESS_G13`.
Therefore the current algorithm's success is not limited to the fixed G9--G12
count schedules under this bounded episode-random process distribution.

The source still serializes removals and later additions into separate events.
It does not test a single membership transaction that terminates a large cohort
and introduces a cold-start cohort atomically while count stays constant. That
is the nearest dynamic-roster counterexample and the next bounded action.

```text
next_boundary=ATOMIC_COHORT_REPLACEMENT_G14_DERIVATION
conclusion_bearing_iteration=14
iterations_remaining_after_run=3
```
