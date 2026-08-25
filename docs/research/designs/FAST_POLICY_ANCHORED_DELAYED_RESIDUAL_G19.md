# Fast-policy-anchored delayed residual G19

```text
status=NONFORMAL_CLOSED_NO_DELAYED_ACCESS
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Executable algorithm boundary

`FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19` retains the G17 continuous-roster
actor as a trained-and-frozen fast path. A zero-initialized additive action-mean
head is the only actor component updated by delayed successor credit. The fast
actor, recurrent state transition, routing order, action factorization,
exploration scale, sources, rewards and observations are unchanged.

The residual update projects a delayed PPO gradient out of the conflicting
component of the immediate-reward PPO gradient in residual-parameter space.
The independent slow return critic and immediate/successor baselines remain
state-only. Critic losses never update fast or residual actor parameters.

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

Screen seeds are fixed before execution:

```text
g17_model=2419000
g17_train_ledger=2429000
g17_action=2439000
g17_evaluation_ledger=2449000
g17_evaluation_action=2459000
g18_model=2519000
g18_action=2539000
```

The screen reuses the G18 formal thresholds as single-screen point gates and
keeps the same first-match semantics:

1. `INVALID_FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19` on operational,
   replay, lifecycle, source-control, anchor-identity or projection failure;
2. `NONFORMAL_NO_G17_COMPATIBILITY_FAST_ANCHOR_G19` unless final G17 IID and
   held-out means are at least `0.90`, gain over zero at least `0.10`, minimum
   episode at least `0.80`, both mapping correlations at least `0.90`, and both
   MAEs at most `0.05`;
3. `NONFORMAL_NO_DELAYED_ACCESS_FAST_ANCHOR_G19` unless final G18 utility is at
   least `0.95`, gain over its frozen fast anchor at least `0.10`, and spike
   utility is at least `0.90`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_FAST_ANCHOR_G19` unless rotating-member
   low-phase effort share is at least `0.75`; or
5. `NONFORMAL_FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_PROMISING_G19`.

Only branch 5 licenses a formal runner. No branch supports a UAV claim. There
is no same-package retry or hyperparameter sweep.

## Proof-sized acceptance

- exact zero-residual anchor equivalence under deterministic, sampled and
  teacher-replay modes;
- fast-parameter and log-standard-deviation immutability after delayed updates;
- finite conflict projection with nonnegative post-projection dot product;
- critic/actor gradient ownership;
- exact replay and inactive-row zero on both G17 and G18;
- one finite update for each phase and exact phase/checkpoint state;
- first-match branch precedence.

Implementation may add one generic hook to `ContinuousRosterPolicy`, one active
G19 module, one bounded runner and focused tests. Closed G17/G18 runners remain
unchanged evidence at their Git commits; no compatibility adapter is required.

## Implementation acceptance

The bounded implementation uses Adam for the fast anchor and state-only
critics, and unpreconditioned SGD for the residual. SGD is required because a
positive scalar step preserves the projection's first-order sign; an Adam
preconditioner could rotate a projected gradient back into conflict.

Thirty focused and shared tests pass on the registered CPU runtime. The zero
residual exactly matches the base policy in all three execution modes. Fast
parameters remain bitwise fixed across delayed updates, both sources retain
exact replay/lifecycle behavior, and every tested projected gradient closes the
registered dot-product invariant. These checks licensed the bounded paired
screen recorded below.

## Bounded screen disposition

The integrated screen completed with exact replay, exact fast-anchor identity
and valid source controls. It preserved G17 held-out utility from `0.94473` to
`0.94641`, but G18 anchor and final utility were both `0.66667`, spike utility
was zero and delayed gain was zero. The frozen first-match branch is
`NONFORMAL_NO_DELAYED_ACCESS_FAST_ANCHOR_G19`.

The residual moved, but the batch-global projection did not expose the
member-redistribution direction required by the delayed source. This exact
candidate is closed without formal promotion or same-package repair.
