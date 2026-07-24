# Unconstrained anchored delayed residual G21

```text
status=NONFORMAL_CLOSED_NO_DELAYED_ACCESS
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G21 retains the G20 source pair, trained-and-frozen fast anchor, exact-zero
residual initialization, successor credit, state-only critics, SGD, budgets,
thresholds and first-match order. It removes the active-set centering and adds
no replacement projection. The delayed residual can therefore change both
relative member actions and their common mode. No reward, observation,
lifecycle, routing, factorization, RNG or source field changes.

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
g17_model=2819000
g17_train_ledger=2829000
g17_action=2839000
g17_evaluation_ledger=2849000
g17_evaluation_action=2859000
g18_model=2919000
g18_action=2939000
```

First-match outcomes retain the exact G19/G20 thresholds:

1. `INVALID_UNCONSTRAINED_ANCHORED_DELAYED_RESIDUAL_G21`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_UNCONSTRAINED_RESIDUAL_G21`;
3. `NONFORMAL_NO_DELAYED_ACCESS_UNCONSTRAINED_RESIDUAL_G21`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_UNCONSTRAINED_RESIDUAL_G21`; or
5. `NONFORMAL_UNCONSTRAINED_ANCHORED_DELAYED_RESIDUAL_PROMISING_G21`.

Operational validity requires finite updates, exact anchor identity, replay at
most `1e-6`, exact inactive likelihood rows, lifecycle/source controls and a
nonzero residual output layer. Only branch 5 licenses formal design. No branch
supports UAV promotion.

## Proof-sized acceptance

- exact zero-residual equivalence in sampled, deterministic and teacher modes;
- bitwise anchor and exploration-scale preservation after delayed updates;
- successor-only residual gradients and isolated critic gradients;
- exact inactive rows and registered replay/lifecycle controls;
- no centering or immediate-gradient projection in the delayed path;
- first-match precedence and frozen configuration.

## Implementation acceptance

`ha_ctse_process/unconstrained_residual_g21.py` supplies the thin successor-only
update over the retained frozen-anchor policy. The paired runner is
`scripts/screen_unconstrained_anchored_residual_g21.py`. There is no centering,
immediate-gradient projection, source-specific actor input or fast-parameter
update in the delayed path.

Five focused and 35 focused-plus-retained tests pass on the registered CPU
one-thread runtime. Exact zero-output equivalence closes sampled,
deterministic and teacher modes; an injected residual bias proves active
common-mode freedom while inactive rows remain exact zero; both sources close
replay and bitwise anchor identity after successor updates. The closed G20
execution code and unused generic hook are removed under the active-line-only
policy. This accepts only the bounded screen, not formal compute or a delayed
access conclusion.

## Bounded screen disposition

The integrated screen is operationally valid with exact replay and anchor
identity. G17 held-out utility remains `0.95253`; G18 changes from `0.57933` to
only `0.58333`, with gain `0.004` and zero spike utility. The first-match branch
is `NONFORMAL_NO_DELAYED_ACCESS_UNCONSTRAINED_RESIDUAL_G21`. The exact
unrestricted-SGD candidate is closed without tuning or formal/UAV promotion.
