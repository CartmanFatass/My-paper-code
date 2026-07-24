# Anchored dual-channel residual G23

```text
status=NONFORMAL_CLOSED_NO_DELAYED_ACCESS
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G23 retains G22's unrestricted residual, frozen fast actor, residual-only Adam,
state-only critics, source pair, budgets and gates. It replaces the
successor-only residual actor loss with the equal average of independently
normalized immediate and successor PPO losses. No delayed residual entropy
term is added.

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
g17_model=3219000
g17_train_ledger=3229000
g17_action=3239000
g17_evaluation_ledger=3249000
g17_evaluation_action=3259000
g18_model=3319000
g18_action=3339000
```

First-match outcomes retain the exact G19--G22 thresholds:

1. `INVALID_ANCHORED_DUAL_CHANNEL_RESIDUAL_G23`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_DUAL_CHANNEL_RESIDUAL_G23`;
3. `NONFORMAL_NO_DELAYED_ACCESS_DUAL_CHANNEL_RESIDUAL_G23`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_DUAL_CHANNEL_RESIDUAL_G23`; or
5. `NONFORMAL_ANCHORED_DUAL_CHANNEL_RESIDUAL_PROMISING_G23`.

Operational validity additionally requires exact channel weights,
residual-only optimizer/gradient ownership, finite updates, exact anchor,
replay at most `1e-6`, inactive exact zero and source/lifecycle controls. Only
branch 5 licenses formal design; no branch supports UAV promotion.

## Proof-sized acceptance

- separate channel normalization and exact equal-weight loss;
- residual-only actor gradient and fresh Adam ownership;
- bitwise fast-anchor/exploration preservation;
- retained policy/replay/lifecycle/source proofs;
- frozen configuration and first-match precedence.

## Implementation acceptance

The active implementation is `ha_ctse_process/dual_channel_residual_g23.py`
with paired runner `scripts/screen_anchored_dual_channel_residual_g23.py`.
Every delayed update reports both channel losses, their exact `0.5` weights and
the combined loss; the runner fails closed if the averaged-loss identity drifts
above `1e-7`.

Six focused and 36 focused-plus-retained tests pass on the registered CPU
one-thread runtime. They prove residual-only Adam/gradient ownership, separate
channel composition, exact frozen anchor, zero-output/common-mode behavior and
retained replay/lifecycle/source semantics. This accepts only the bounded
screen, not formal compute or delayed access.

## Bounded screen disposition

The integrated screen is operationally valid with exact channel identity,
replay and anchor preservation. G17 passes. G18 utility `0.95111`, gain
`0.25083` and rotating share `0.84993` pass, but spike utility `0.85332` misses
the frozen `0.90` floor. The first-match branch is
`NONFORMAL_NO_DELAYED_ACCESS_DUAL_CHANNEL_RESIDUAL_G23`. The exact local
residual representation is closed without tuning or formal/UAV promotion.
