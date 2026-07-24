# Adaptive anchored delayed residual G22

```text
status=PROTOTYPE_ACCEPTED_SCREEN_NEXT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G22 is G21 with one change: the delayed residual optimizer is Adam rather than
SGD. The residual remains unrestricted and unprojected; the trained fast actor
and exploration scale remain frozen; successor credit and state-only critics
are unchanged. Adam uses `lr=1e-3`, `betas=(0.9,0.999)`, `eps=1e-8`, zero
weight decay and `amsgrad=false` with fresh per-source state.

## Bounded screen

```text
replicates=1
num_envs=8
ppo_passes=2
g17_fast_updates=100
g17_delayed_updates=100
g18_fast_updates=100
g18_delayed_updates=300
g17_eval_episodes_per_domain=48
g18_slot_permutations=3
formal=false
```

Fresh screen seeds:

```text
g17_model=3019000
g17_train_ledger=3029000
g17_action=3039000
g17_evaluation_ledger=3049000
g17_evaluation_action=3059000
g18_model=3119000
g18_action=3139000
```

First-match outcomes retain the exact G19--G21 thresholds:

1. `INVALID_ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_G22`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_ADAPTIVE_RESIDUAL_G22`;
3. `NONFORMAL_NO_DELAYED_ACCESS_ADAPTIVE_RESIDUAL_G22`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_ADAPTIVE_RESIDUAL_G22`; or
5. `NONFORMAL_ADAPTIVE_ANCHORED_DELAYED_RESIDUAL_PROMISING_G22`.

Operational validity requires finite updates, exact anchor identity, replay at
most `1e-6`, exact inactive likelihood rows, source/lifecycle controls,
nonzero residual exercise and exact optimizer ownership. Only branch 5
licenses formal design; no branch supports UAV promotion.

## Proof-sized acceptance

- exact G21 policy equivalence and common-mode proofs;
- Adam defaults and residual-only parameter inventory;
- fresh optimizer state and bitwise anchor preservation;
- retained G17/G18 replay/lifecycle controls;
- frozen first-match precedence and configuration.

## Implementation acceptance

The active runner is `scripts/screen_adaptive_anchored_residual_g22.py` and
reuses the source-neutral residual implementation without duplication. Its
constructor registers exactly `model.residual_parameters()` in a fresh Adam
instance with the frozen defaults; critic and fast parameters are disjoint.

Six focused and 36 focused-plus-retained tests pass on the registered CPU
one-thread runtime. They retain exact zero-output/common-mode behavior, replay,
inactive rows and bitwise anchor preservation while proving optimizer identity
and empty initial state. This accepts only the bounded screen and does not
authorize formal compute or claim delayed access.
