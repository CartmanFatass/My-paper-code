# Ultra-scale open-roster G12 formal result

Date: 2026-07-23

The exact source `21046fcf9a67cd7503266284c02896ae85dafd62`
completed at `logs/formal_ultra_scale_g12_cpu_20260723_21046fc_r1`.

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
imported_g8_replicates=3
optimizer_steps=0
evaluation_cells=18
utility_values=1152
operational_valid=true
operational_errors=[]
branch=ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12
```

All three imported checkpoints, 18 replicate/domain/mode cells and 1,152
serialized utility values closed. Each checkpoint copy had maximum difference
zero, every model state remained exact, and source controls independently
closed the N=48, 64 and 80 schedules, wave requirements, eight membership
transactions, lifecycle freeze/restore and constructive utility one.

```text
edge_n48_deterministic_utility_ci95=[0.9251708984375,0.9513818884408604,0.9996534778225806]
far_n64_deterministic_utility_ci95=[0.923095703125,0.949975157620614,0.9987291837993421]
ultra_n80_deterministic_utility_ci95=[0.927001953125,0.952321846707433,0.999787805747299]
ultra_replicate_means=[0.927001953125,0.999787805747299,0.93017578125]
ultra_min_replicate_mean=0.927001953125
ultra_stochastic_mean=0.8973560290001418
```

Independent first-match evaluation reproduced
`ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12`. The frozen G8 policy therefore remains
usable through the registered N=80 scale/churn source with no retraining.

The result does not establish arbitrary N or arbitrary membership dynamics.
All episodes in each domain still share one hand-authored count/event schedule.
The nearest remaining counterexample is schedule memorization at the process
level. The next action randomizes valid event times, directions, magnitudes and
roster counts independently per episode while preserving the same task and
constructive controls.

```text
next_boundary=RANDOMIZED_ROSTER_PROCESS_G13_DERIVATION
conclusion_bearing_iteration=13
iterations_remaining_after_run=4
```
