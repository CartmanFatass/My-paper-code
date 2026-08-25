# OPEN_ROSTER_ZERO_SHOT_SCALE_G6 formal result

Date: 2026-07-23

```text
source_commit=909ced01ee58e2690fd7cd0ec2da214e99203af5
run=logs/formal_open_roster_zero_shot_g6_cpu_20260723_909ced0_r1
checkpoint_source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
training_operation=none_frozen_g5_checkpoint_import
optimizer_steps=0
result=ROBUST_ZERO_SHOT_OPEN_ROSTER_G6
conclusion_bearing_iteration=7
iterations_remaining=10
```

## Evidence closure

The registered Luna-low operator completed the exact import, evaluate and
analyze commands once with all exit codes zero and no restart. Project Manager
then independently closed three imported update-250 checkpoints, 18 unique
replicate/domain/determinism cells and 2,304 evaluation episodes.

Every array contains 128 finite values in `[0,1]`; external mean recomputation
differs from serialized NumPy means by at most `1.23e-15`. Every model-state
difference is exactly zero. The G5 source, authorization token, CPU runtime,
formal branch and checkpoint contracts remain exact. All eight source-control
profiles have constructive utility one, exact roster schedules, actual-wave
demand, membership events, lifecycle states and terminal destruction.

## Registered result

| Quantity | Registered value |
|---|---:|
| Count-scale deterministic utility CI95 | [0.9294811, 0.9728004, 0.9990977] |
| Event-time deterministic utility CI95 | [0.9854642, 0.9951547, 1.0000000] |
| Joint deterministic utility CI95 | [0.9358802, 0.9763486, 0.9999524] |
| Joint replicate means | [0.9999524, 0.9358802, 0.9932133] |
| Joint minimum replicate mean | 0.9358802 |
| Joint stochastic utility mean | 0.9501188 |

All three lower bounds exceed 0.90, the minimum joint replicate exceeds 0.85
and joint stochastic mean exceeds 0.80. Independent first-match recomputation
therefore exactly returns `ROBUST_ZERO_SHOT_OPEN_ROSTER_G6`.

## Scientific correction

`CE-NEAR-COUNT-INTERPOLATION`, `CE-FIXED-EVENT-CLOCK` and
`CE-SCALE-TIME-NONCOMPOSITION` are rejected on the registered range. The frozen
G5 checkpoints remain usable through active count 16, varied safe event times
and their composition without any optimizer step. This is strong evidence that
the direct recurrent active-set interface is a stable dynamic-roster MVP.

The result stops exactly at the implementation's declared count-feature limit.
It does not support arbitrary N or counts above 16. Count-scale and joint lower
bounds are also lower than the event-time bound, making further scale transport
the sharper remaining question.

The smallest next action is a new zero-training, beyond-declared-count
derivation. It preserves the frozen G5 checkpoints and the exact count formula
while testing N above 16 before selecting a scale-free aggregation repair.

```text
scientific_disposition=closed_success_no_rerun_tuning_or_relabeling
next_boundary=BEYOND_DECLARED_COUNT_G7_DERIVATION
iterations_remaining=10
```
