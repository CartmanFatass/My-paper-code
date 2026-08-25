# High-frequency roster churn G9 derivation

Date: 2026-07-23

## Starting evidence

Formal G8 establishes a usable prefix-normalized policy through N=40, but every
training and evaluation episode contains only three membership edits. Count
scale and event-time transport do not imply that lifecycle-owned recurrent
state composes under repeated leave/rejoin/join/terminal operations.

`CE-THREE-EVENT-SPECIALIZATION` allows the policy to work only for one
reduce-expand-reduce pattern. `CE-REJOIN-ONCE` allows hidden-state freeze/restore
to be correct once but unstable when the same lifecycle repeatedly leaves and
returns. `CE-LOAD-SEPARATED-CHURN` allows safe event-time tests to avoid edits
at short-wave boundaries.

## Smallest separating action

Freeze the three successful G8 final checkpoints and perform zero optimizer
steps. Keep the original Generic-SHORT reward, observation, wave distribution,
prefix-normalized policy, count range at or below N=16 and horizon 80. Replace
only the three-event membership schedule with eight edits in three domains:

1. `repeated_rejoin`: the same temporary group leaves and returns three times;
2. `load_proximal`: temporary, terminal and genuine joins occur at short-wave
   start/end boundaries;
3. `mixed_churn`: repeated temporary edits, genuine joins and terminal leaves
   compose in one episode.

Every domain must retain a constructive utility-one controller and actual-wave
demand computed from the post-membership active set. This is an independent
stress result, not a G8 rerun or a new training budget.

## Interpretation boundary

Success supports repeated churn robustness only for eight edits, N<=16 and the
registered profiles. Failure selects an event-adaptive training distribution or
lifecycle representation repair according to the first failed domain. It does
not relabel G8's N<=40 result. Asynchronous skill lifetime remains frozen.

```text
next_boundary=HIGH_FREQUENCY_ROSTER_CHURN_G9_EXECUTABLE_DEFINITION
training_operation=none_frozen_g8_checkpoint_import
conclusion_bearing_iteration=10
iterations_remaining_before_run=8
```
