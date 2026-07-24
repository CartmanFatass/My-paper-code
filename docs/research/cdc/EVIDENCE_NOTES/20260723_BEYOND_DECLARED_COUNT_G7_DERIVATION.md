# Beyond-declared-count G7 derivation

Date: 2026-07-23

## Starting evidence

Formal G6 shows that the frozen G5 checkpoints transport through active count
16 and unseen membership-event times. Count-scale CI95 is
`[0.9294811, 0.9728004, 0.9990977]`; event-time transport is stronger. The
current count observation is `log1p(N)/log1p(16)` and the active context is a
sum. G6 stopped exactly at the declared denominator and profile limit.

## Counterexamples

`CE-DECLARED-LIMIT-AS-SUPPORT`: success through N=16 may only show that the
checkpoint operates within the explicitly normalized feature range `[0,1]`.

`CE-SUM-MAGNITUDE-EXTRAPOLATION`: active embedding sums can remain well behaved
through N=16 but saturate actor/critic layers at larger N.

`CE-MODERATE-VS-FAR-COLLAPSE`: a single extreme profile cannot distinguish a
gradual usable range from immediate failure just above the declared limit.

`CE-BEYOND-COUNT-TIME-INTERACTION`: beyond-limit counts may work at familiar
event times but fail when combined with unseen membership timing.

## Smallest separating action

Keep the three G5 final checkpoints, all weights, the original count formula,
Generic-SHORT semantics and optimizer exposure exactly frozen. Evaluate:

1. moderate beyond-limit counts through N=24 at 20/40/60;
2. far beyond-limit counts through N=40 at 20/40/60;
3. joint beyond-limit counts through N=40 at unseen safe event times.

Operational capacity rises to 48 but remains inactive padding. The profile
validator may admit N up to 40 only for this independent stress; it must not
change the G5 count feature. Constructive utility remains one and actual-wave
demand follows membership at each arrival.

The result selects the next algorithm action without conflation:

- moderate failure selects immediate scale-free mean/count repair;
- far-only failure identifies a finite reliable range and selects that repair;
- joint-only failure selects scale/time composition training;
- full success retains the direct checkpoint and moves to roster-churn stress.

## Iteration accounting

Derivation, implementation and nonformal acceptance consume no conclusion-
bearing iteration. A valid G7 formal evaluation is iteration 8 and leaves nine
rounds in the twelve-round chain.

```text
next_boundary=BEYOND_DECLARED_COUNT_G7_EXECUTABLE_DEFINITION
training_operation=none_frozen_g5_checkpoint_import
asynchronous_skill_lifetime=frozen
iterations_remaining=10
```
