# PREFIX_NORMALIZED_OPEN_ROSTER_G8 formal result

Date: 2026-07-23

```text
source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
replicates=3
updates_per_replicate=250
evaluation_cells=33
result=USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
conclusion_bearing_iteration=9
iterations_remaining=8
```

## Evidence closure

The registered Luna-low operator completed the exact fresh
`train -> evaluate -> analyze` pipeline once with all exit codes zero and no
restart. Project Manager independently closed three zero/final checkpoint
pairs, 33 exact cells, 4,224 utility outcomes and 12 source-control profiles.

All three training replicates complete 250 updates and 1,000 optimizer steps
with finite updates, exact lifecycle ownership and replay maximum error zero.
All outcome arrays have 128 finite values in `[0,1]`; external mean
recomputation differs from serialized values by at most `5.56e-16`. Evaluation
model drift is exactly zero in every cell. Source controls retain constructive
utility one and finite original count features through N=40. Source, token,
representation, CPU runtime, counts and checkpoint inventories are exact.

## Registered result

| Quantity | Registered value |
|---|---:|
| IID deterministic utility CI95 | [0.9432373, 0.9705811, 1.0000000] |
| Held-out deterministic utility CI95 | [0.9469604, 0.9669189, 1.0000000] |
| Moderate deterministic utility CI95 | [0.9321289, 0.9544279, 0.9989648] |
| Far deterministic utility CI95 | [0.9302979, 0.9531218, 0.9987087] |
| Joint deterministic utility CI95 | [0.9299927, 0.9534098, 1.0000000] |
| Joint replicate means | [0.9299927, 1.0000000, 0.9302368] |
| Joint stochastic utility mean | 0.8994221 |
| Joint final-minus-zero CI95 | [0.1707176, 0.4429891, 0.6406480] |

Every deterministic lower bound exceeds `0.90`; the minimum joint replicate
exceeds `0.85`; stochastic joint exceeds `0.80`; and learned gain is strictly
positive. Independent first-match recomputation therefore exactly returns
`USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8`.

## Scientific correction

Fresh training with `prefix_action_count/N` restores robust absolute usability
on the registered range through N=40 while leaving the G5 active embedding sum,
original out-of-range log-count coordinate, task and parameter shape unchanged.
This rejects the proposition that those retained quantities necessarily prevent
N=40 usability. Together with the matched nonformal screen, it supports raw
autoregressive prefix growth as a useful repair target, but it does not prove a
unique causal explanation across all seeds or tasks.

G7 remains a valid failure of frozen raw-prefix checkpoints; it is not rescued
or relabeled. G8 establishes absolute usability, not arbitrary-N scaling,
comparative advantage, high-frequency churn robustness or skill-lifetime
competence.

The smallest next action freezes the three G8 finals and changes only membership
event frequency/load proximity. This tests whether the usable N=40 interface
handles repeated lifecycle edits without confounding another algorithm change.

```text
scientific_disposition=closed_success_no_rerun_tuning_or_relabeling
next_boundary=HIGH_FREQUENCY_ROSTER_CHURN_G9_DERIVATION
iterations_remaining=8
```
