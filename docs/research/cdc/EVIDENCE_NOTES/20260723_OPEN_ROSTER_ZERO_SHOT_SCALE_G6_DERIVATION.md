# Open-roster zero-shot scale G6 derivation

Date: 2026-07-23

## Starting evidence

Formal G5 establishes a usable dynamic-roster MVP through held-out active count
nine and a capacity change from 10 to 12. It does not identify why the policy
works or how far the learned interface extrapolates. The trained actor receives
an active embedding sum plus a count feature normalized by the declared limit
16. The environment also used membership events at the same times in every
training and held-out profile.

G5 is closed. No G6 action may retrain, tune, rename or relabel it.

## Separating counterexamples

`CE-NEAR-COUNT-INTERPOLATION`: counts eight and nine may be close enough to
training count seven that the G5 result is local interpolation rather than a
useful open-roster interface.

`CE-FIXED-EVENT-CLOCK`: the policy may use the universal 20/40/60 event times as
a shortcut and fail when otherwise identical JOIN/leave operations occur at
unseen safe times.

`CE-SCALE-TIME-NONCOMPOSITION`: count-only and time-only transport may each work
while their combination fails because recurrent state, active-set magnitude
and membership edits interact.

`CE-POST-HOC-NORMALIZATION`: replacing the active sum with a mean before first
measuring the frozen checkpoint would confound diagnosis with repair. A
count-normalized correction is admissible only after the zero-shot evidence
locates a count-scale failure.

## Smallest separating action

Reuse the three frozen G5 final checkpoints with no optimizer step. Evaluate
three mutually interpretable domains:

1. `count_scale`: fixed 20/40/60 event times, unseen active counts through 16;
2. `event_time`: G5-held-out count range, unseen safe membership times;
3. `joint`: the far counts and unseen times combined.

Counts stop at 16 so the G5 observation mapping
`log1p(N)/log1p(16)` is unchanged and bounded. Horizon, wave windows, external
reward, primitive actions, observations, policy, checkpoint and task utility
remain frozen. Membership events are placed outside active short-wave windows;
constructive utility must remain exactly one.

This evaluation-only action is cheaper and more diagnostic than training a new
algorithm. Its first-match result determines the next correction:

- count failure selects count-normalized aggregation;
- time failure selects membership-time randomization/cue removal;
- joint-only failure selects explicit scale/event composition;
- full success retains G5 and advances to a harder dynamic-N task property.

## Iteration accounting

The derivation, implementation and nonformal exercise cost zero conclusion-
bearing iterations. A valid formal G6 evaluation consumes iteration 7. The
user-expanded twelve-round dynamic-roster chain then has ten rounds remaining.

```text
next_boundary=OPEN_ROSTER_ZERO_SHOT_SCALE_G6_EXECUTABLE_DEFINITION
asynchronous_skill_lifetime=frozen
formal_compute=authorized_after_contract_and_git_freeze
current_iterations_remaining=11
```
