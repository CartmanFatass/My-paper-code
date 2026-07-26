# G35 reactive-reduction design assertion audit brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
code_acceptance_owner=project_manager
review_mode=DESIGN_ASSERTION_AUDIT
round=20260726_continuous_roster_reactive_reduction_g35_design_assertion_audit
selected_action=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT
formal_compute_authority=none_in_this_round
design_audit_compute=zero
conclusion_bearing_iteration_cost=0
```

## Purpose

External Pro accepted G34 as bounded random-process checkpoint transport but
left one decision-relevant alternate explanation: the policy may primarily be a
true-time-conditioned current-state mapper rather than requiring learned
lifecycle recurrence. The existing reactive intervention is underpowered and
simultaneously removes hidden state, age and previous action, so it cannot
separate those mechanisms.

External Pro selected exactly one next action:

```text
CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT
```

This zero-compute round must freeze or reject a fresh paired recurrent versus
current-state/feedforward comparison before PM implements either arm. It grants
no training or formal-run authority.

## Non-negotiable inherited boundary

```text
H=48
train_source=unchanged_G32_capacity8_fixed_process
heldout_source=unchanged_G34_P0_fixed_and_random_capacity6_8_12_cells
reward=unchanged
true_time_field=retained_in_both_arms
lifecycle_age=retained_in_both_arms
previous_actions=retained_in_both_arms
current_load_target_mix_capability_active_count_and_action_prefix=retained_in_both_arms
centralized_critic_information=matched
credit=identical_G31_realized_future_tail
fresh_paired_training=required_for_both_arms
existing_G32_checkpoints=historical_reference_only
new_reward_or_intrinsic=forbidden
uav_scope=excluded
g33_and_derivatives=abandoned_no_reactivation
```

The only intended causal difference is whether the actor carries learned
recurrent hidden state across primitive steps and lifecycle boundaries. A null
that removes current information is inadmissible. A simultaneous credit change
is inadmissible.

## Current implementation facts

- `ContinuousRosterPolicy` encodes each current member observation, aggregates
  active members, uses an active-fraction action prefix and updates a per-member
  `GRUCell` before the actor head. The centralized critic consumes the same
  active-set context plus the current critic state.
- G32 observations expose current capability, presentation priority, load,
  target mix, active count, lifecycle age, previous action and normalized true
  time. The G35 current-state arm must retain them all.
- G31 supplies the frozen realized-future-tail and direction-balanced update.
  G35 changes no reward or credit rule.
- G32 supplies fresh capacity-8 training mechanics; G34 supplies fixed/random
  evaluation at capacities 6/8/12, trace-closed evidence and whole-episode
  confidence surfaces.
- G34 time rotation is load-bearing for the exact historical checkpoint, while
  its combined zero-history reactive ablation is underpowered. Neither result
  fixes the G35 comparator architecture, materiality margin or evidence volume.

These are reusable code facts, not authority for PM to choose scientific
defaults.

## Feasibility and evidence economy

The audit itself requires no trajectories:

```text
design_audit_compute=0
intrinsic_K_search=0
hypothetical_trajectory_bound=0
nested_rollout=false
replanning=false
```

The existing runners admit fresh paired training and direct 48-step evaluation
without hypothetical search. PM found no code impossibility requiring a
clarification. External Pro must freeze the smallest exact seed, training,
evaluation and bootstrap inventory whose projected nonformal run is at most 20
minutes and formal train/evaluate/analyze run is at most eight hours.

This audit prevents a destructive ablation from being misreported as evidence
for recurrence and prevents a representation difference from being confounded
with information or credit. It is cheaper than implementing and training an
unidentified comparator.
