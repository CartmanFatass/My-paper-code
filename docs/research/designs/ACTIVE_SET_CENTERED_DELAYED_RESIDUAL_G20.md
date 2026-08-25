# Active-set-centered delayed residual G20

```text
status=NONFORMAL_CLOSED_NO_DELAYED_ACCESS
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G20 retains the G19 fast-anchor phase, frozen anchor, exact-zero delayed head,
state-only critics, source pair, budgets, SGD residual optimizer and absolute
first-match gates. It replaces global parameter-gradient projection with an
active-mask-only centering projection on the residual pre-squash action mean.

The proposal head is permutation equivariant and reads only current generic
policy features. The centered residual is added after the ordinary anchor mean
is computed and before the tanh-Gaussian distribution is formed. No source
label or environment-specific field is added.

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
g17_model=2619000
g17_train_ledger=2629000
g17_action=2639000
g17_evaluation_ledger=2649000
g17_evaluation_action=2659000
g18_model=2719000
g18_action=2739000
```

First-match outcomes retain the exact G19 thresholds:

1. `INVALID_ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_G20`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_CENTERED_RESIDUAL_G20`;
3. `NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_CENTERED_RESIDUAL_G20`; or
5. `NONFORMAL_ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_PROMISING_G20`.

Operational validity additionally requires residual active-sum error at most
`1e-6`, exact anchor identity, exact replay, lifecycle/source controls, finite
updates and nonzero residual exercise. Only branch 5 licenses formal design;
no branch supports UAV promotion.

## Proof-sized acceptance

- exact zero-residual equivalence in all three execution modes;
- active-coordinate centering and inactive exact zero across mixed masks;
- slot-permutation equivariance and padding independence;
- fast-anchor immutability after both source updates;
- residual-only successor actor gradients and isolated critic gradients;
- exact G17/G18 replay/lifecycle behavior;
- first-match precedence and frozen configuration.

## Implementation acceptance

The source-neutral implementation is
`ha_ctse_process/centered_residual_g20.py`; the paired runner is
`scripts/screen_active_set_centered_residual_g20.py`. The generic policy hook
returns `None` by default, so retained policies keep their exact path. G20
reuses the G19 anchor wrapper through an injected policy class and therefore
does not construct and discard a second actor or consume additional RNG draws.

On the registered CPU one-thread runtime, six focused tests and the retained
G17/G18/G19 proofs pass (36 total). They close exact zero-output execution in
sampled, deterministic and teacher modes, active-only centering, inactive exact
zero, permutation/padding invariance, replay at collection time, residual
exercise and bitwise anchor preservation. This accepts only the bounded screen;
it is not evidence of delayed access and does not authorize formal compute.

## Bounded screen disposition

The integrated screen is operationally valid with maximum replay and centering
error `2.91e-10` and exact anchor identity. G17 held-out utility remains
`0.94428`, but G18 anchor and final utility are both `0.58333`, gain and spike
utility are zero, and the first-match branch is
`NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20`. The exact centered
candidate is closed without tuning or formal/UAV promotion.
