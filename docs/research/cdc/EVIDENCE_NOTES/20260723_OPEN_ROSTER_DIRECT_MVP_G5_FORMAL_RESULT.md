# OPEN_ROSTER_DIRECT_MVP_G5 formal result

Date: 2026-07-23

```text
source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
result=USABLE_OPEN_ROSTER_DIRECT_G5
conclusion_bearing_iteration=6
iterations_remaining=11
```

## Evidence closure

The registered Luna-low experiment operator completed the exact foreground
pipeline once, with train, evaluate and analyze exit codes all zero and no
restart. Project Manager then independently closed the artifact references and
recomputed the frozen first-match selector.

The package contains three zero/final checkpoint pairs, three complete
250-update replicates, 480,000 total environment steps, 3,000 optimizer steps
and 24 evaluation cells of 128 episodes each. Every checkpoint reference
exists. Every replicate is finite, lifecycle-valid and has exact-zero replay
error. Training and evaluation both record CPU, one thread and the exact source
commit. All five source profiles have constructive utility 1. The 24 cells
uniquely cover every replicate, zero/final checkpoint, IID/held-out domain and
deterministic/stochastic combination.

## Registered result

| Quantity | Registered value |
|---|---:|
| IID deterministic utility CI95 | [0.9985352, 0.9994303, 1.0000000] |
| Held-out deterministic utility CI95 | [0.9828880, 0.9939927, 1.0000000] |
| Held-out replicate means | [1.0000000, 0.9828880, 0.9990900] |
| Held-out minimum replicate mean | 0.9828880 |
| Held-out stochastic utility mean | 0.9737068 |
| Held-out final-minus-zero CI95 | [0.4828880, 0.5434274, 0.6483043] |

The IID and held-out lower bounds exceed 0.90, the minimum replicate exceeds
0.85, stochastic utility exceeds 0.80 and the learning-gain lower bound is
positive. The independently recomputed first match therefore exactly equals:

```text
USABLE_OPEN_ROSTER_DIRECT_G5
```

## Scientific correction

`C-OPEN-ROSTER-DIRECT` is supported at MVP scope. A single shared recurrent
policy with lifecycle-owned state and parameter shapes independent of roster
capacity learned an absolutely usable policy across within-episode temporary
leave, rejoin, genuine join and terminal leave. The same checkpoints transfer
from training counts up to seven to held-out counts up to nine and from
capacity 10 to capacity 12.

This result does not establish comparative advantage, arbitrary-count scaling,
event-time robustness, EHC, skill selection or asynchronous skill lifetime.
The active-set sum may still become poorly conditioned far outside the trained
count range. The smallest next separating action is a zero-training derivation
for held-out count-scale and membership-event-time stress, using the closed G5
checkpoint without tuning or relabeling G5.

```text
scientific_disposition=closed_success_no_rerun_tuning_or_threshold_change
next_boundary=OPEN_ROSTER_ZERO_SHOT_SCALE_G6_DERIVATION
iterations_remaining=11
```
