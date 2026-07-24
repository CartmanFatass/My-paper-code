# Continuous service roster G17 bounded screen

Date: 2026-07-24

## Registered question

Does the fresh continuous-service toy provide enough bounded access evidence to
justify freezing a formal iteration-18 contract for the G8-derived dynamic
roster representation?

This is nonformal prototype evidence. It consumes zero conclusion-bearing
iterations and cannot be called UAV evidence.

## Closed operational evidence

- shared G17/UAV focused tests: 20 passed;
- constructive source utility: minimum `0.9999999704`;
- maximum teacher-replay, hidden, prefix and inactive-likelihood error: `0.0`;
- CPU-only PyTorch `2.7.0+cpu`, one thread;
- no G8, spatial or UAV checkpoint import.

Four fresh-from-zero screens used the same source, model and seeds:

| Screen | Updates | Initial log std | LR | Joint final | Gain | Effort corr. | Mix corr. |
|---|---:|---:|---:|---:|---:|---:|---:|
| pm1 | 60 | 0.0 | 3e-4 | 0.666111 | 0.174088 | not yet recorded | not yet recorded |
| pm2 | 180 | 0.0 | 3e-4 | 0.666179 | 0.174156 | not yet recorded | not yet recorded |
| pm3 | 100 | -1.0 | 3e-4 | 0.682109 | 0.190086 | 0.016610 | 0.113129 |
| pm4 | 100 | -1.5 | 1e-3 | 0.679362 | 0.187338 | 0.022790 | 0.174843 |

Every run is finite and learns a better constant operating point than its zero
checkpoint. None reaches the registered IID `0.80` or held-out `0.75` screen
floor. The tiny conditional correlations and predicted-action standard
deviations show that the apparent gain is not current-demand access.

## PM disposition

```text
prototype_disposition=NO_CONDITIONAL_PPO_ACCESS_G17_V1
more_budget=forbidden_by_plateau
more_exploration_scale_tuning=not_selected
formal_contract=not_frozen
formal_iteration_consumed=false
iterations_remaining=10
```

The source, shared core and exact replay remain useful. The smallest separating
action is a supervised constructive-action representation-fit probe using the
same model and observations. A successful fit isolates shared-reward PPO/credit
as the failed component; a failed fit retires the policy representation itself.
The probe is diagnostic only and does not select a scientific result.

The exact 200-step probe reduced full-dataset MSE from `0.0785263` to
`0.00100230`. It passed the relative reduction condition but missed the frozen
absolute `<=1e-3` condition. It is therefore
`BORDERLINE_REPRESENTATION_FIT_NOT_ACCEPTED_G17_V1`; no extra steps or threshold
rounding are used to rescue it.

The next bounded delta adds one environment-neutral current-observation linear
residual to the action mean. This adds only `observation_dim * action_dim +
action_dim` parameters, leaves the recurrent active-set/prefix path intact and
is disabled for the existing UAV wrapper. It must first pass the same exact
representation probe before any RL screen.
