# HMASD evidence and scaling complexity policy

```text
policy_kind=user_authorized_hard_workflow_boundary
purpose=test_external_pro_ideas_without_unbounded_measurement_cost
nonformal_wall_clock_cap_minutes=20
formal_iteration_wall_clock_cap_hours=8
prelaunch_zero_compute_cost_bound=required
replicate_volume_cost_expression=O(episodes * events_per_episode * forks_per_event * steps_per_fork)
violation=NON_EXECUTABLE_EVIDENCE_DESIGN
violation_iteration_cost=0
override_authority=user_only_for_one_named_boundary
```

Ported 2026-07-26 from the HMASD-new reference policy by user direction. This
project's conclusion-bearing runs are evaluation-only audits (prefix replay
plus counterfactual fork continuations), so the dominant cost term is replicate
volume, expressed above; the caps and semantics are identical to the reference.

## Prelaunch gate

Before a Pro-proposed evidence action is frozen or implemented, the Project
Manager records a zero-compute upper bound for its total cost: episode count,
expected qualifying events, forks per event (all arms x limbs x
select/eval replicates), steps per fork (prefix replay + continuation horizon
+ guard), and the projected wall clock on the registered local CPU at the
intended sharding width. When constants are unknown, one microbenchmark of at
most 20 minutes may establish them.

- The complete nonformal exercise (smoke, probe, pilot) must finish within
  **20 minutes** on the registered local CPU. A smoke is sized to the minimum
  that proves the untested path — normally one episode per untested limb.
- One formal conclusion-bearing iteration, including resumes and pooling, must
  be projected to and capped at **eight hours** wall clock at the intended
  sharding width on that machine.

This gate closes inside the Stage A design audit (AGENTS.md, "Acceptance,
tests, and review"): the cost bound is part of the question put to External
Pro before freeze, so a contract whose frozen replicate volume cannot fit the
cap is never frozen in that form.

## On violation

A violation is `NON_EXECUTABLE_EVIDENCE_DESIGN`, not a scientific result and
not a failed iteration; it consumes zero conclusion-bearing iterations. The
Project Manager stops the offending realization at the smallest reproducer and
first chooses the cheapest bounded implementation that preserves the frozen
scientific predicate. It does not ask External Pro to design a solver or an
evidence search. Pro re-enters only if no bounded realization can preserve
that predicate — and then decides the scientific necessity or retirement of
the predicate itself, never the implementation.

Neither an active grant nor formal-compute authority overrides this policy;
only the user may grant one named exception with a replacement bound.

## Precedent

2026-07-26: the D7.S event-aligned joint audit as frozen (8 topologies x 16
episodes, n_select=4 / n_eval=8, ~48 forks per event at ~1,100–1,500 steps per
fork) projected to 2–4 days wall at 8-way sharding — a violation this policy
would have caught at freeze. The user closed the run rather than grant the
exception. The frozen contract's replicate volume returns to Pro as a
scientific-necessity question before any relaunch.
