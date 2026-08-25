# Atomic count-shock G15 derivation

Date: 2026-07-23

## Separating question

Formal G12 establishes zero-training count transport through N=80, while G14
establishes count-invisible same-transaction cold-start cohort replacement.
Those results do not entail their composition. A policy can remain stable when
only count changes and when identity changes at fixed count, yet fail when the
same recurrent transition must absorb both a large new cohort and an abrupt
change in active-set normalization.

The smallest remaining interaction counterexample therefore uses one atomic
membership transaction with both positive terminal and fresh-join cohorts,
strictly unequal cohort sizes, and an immediate low/high count transition.

## Frozen correction

G15 keeps the three final G8 checkpoints and performs no training. Each episode
starts in a low-count band and executes six events at the same safe G14 times.
Targets alternate high, low, high, low, high, low. Every event replaces a
positive baseline cohort in addition to the count delta, so neither a pure join
nor a pure leave can satisfy the source.

```text
shock_moderate: capacity=128, low=[12,16], high=[24,32], turnover=[2,4]
shock_wide:     capacity=192, low=[28,32], high=[52,64], turnover=[4,6]
shock_ultra:    capacity=224, low=[40,48], high=[72,80], turnover=[6,8]
events=[9,24,32,40,49,64]
training_operation=none_frozen_g8_checkpoint_import
```

Keys that terminate never return; every joined key is previously unseen and
starts with zero hidden state. Exact event signatures, count trajectories,
wave demand, constructive utility, lifecycle states and model immutability are
required operational evidence.

## Decision relevance

Passage supports usability under the nearest composition of dynamic-count and
dynamic-identity stresses. Failure localizes a genuine interaction boundary
without revising G12 or G14. It cannot establish arbitrary capacity, arbitrary
event timing, N above 80, asynchronous skill lifetime, or comparative
advantage.

```text
selected_next_action=ATOMIC_COUNT_SHOCK_G15_IMPLEMENTATION_AND_NONFORMAL_ACCEPTANCE
conclusion_bearing_iteration_cost=0
iterations_remaining=2
```
