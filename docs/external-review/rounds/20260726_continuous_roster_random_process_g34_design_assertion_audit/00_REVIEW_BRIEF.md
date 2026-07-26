# G34 random-process design assertion audit brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
code_acceptance_owner=project_manager
review_mode=DESIGN_ASSERTION_AUDIT
round=20260726_continuous_roster_random_process_g34_design_assertion_audit
formal_compute_authority=none_in_this_round
conclusion_bearing_iteration_cost=0
```

## Purpose

External Pro selected exactly one successor after the user abandoned G33:

```text
selected_action_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34
next_boundary=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_DESIGN_ASSERTION_AUDIT
```

The selected distinction asks whether the frozen G31/G32 checkpoint transports
from G32's fixed membership events at steps 12, 24 and 36 to a bounded family of
episode-random membership processes, or whether G32 depends on that fixed
schedule. This round freezes or rejects the conclusion-bearing source before
implementation. It performs no training, simulation or formal compute.

## Inherited scientific boundary

Preserve all of the following:

```text
horizon=48
configured_capacity_family=6|8|12
packing_capacity_fixed_within_each_trajectory=true
checkpoint_source=exact_G32_final_checkpoints_trained_at_capacity_8
checkpoint_training_change=forbidden
optimizer_steps_in_G34=0
task_reward_and_continuous_service_semantics=unchanged_G32
learned_algorithm_and_parameterization=unchanged_G31_G32
new_credit_rule=forbidden
uav_scope=excluded
g33_and_derivatives=abandoned_by_user_no_reactivation
```

Success may support only bounded zero-shot process-law transport inside the
registered G34 support. It cannot establish arbitrary process laws, horizons,
capacities, UAV transport, recurrence necessity, G31-credit necessity or
algorithmic superiority.

## Current code facts

- `runtime_capacity_continuous_roster_g32.py` uses `HORIZON=48` and fixed
  `EVENT_TIMES=(12,24,36)`. The events are temporary leave, rejoin plus fresh
  join, and terminal leave.
- Existing capacity profiles bind initial, temporary-leave, fresh-join and
  terminal-leave cohort sizes. Member-owned RNG streams prevent padding rows
  from shifting an active member's capability or presentation stream.
- Every active actor sees current capability, presentation priority, load,
  target mix, `log1p(active_count)`, lifecycle age, previous action and absolute
  normalized time. The critic also sees current load, mix, active capability
  aggregate, `log1p(active_count)` and absolute normalized time.
- Current load and target mix change in four-step blocks and directly determine
  the constructive action. Therefore a random-process source must distinguish
  process transport from fixed-time or reactive current-demand shortcuts
  without silently changing the frozen checkpoint's observation interface.
- G32 already has strict checkpoint loading at capacities 6, 8 and 12, final
  and zero checkpoint cells, deterministic and selected stochastic evaluation,
  lifecycle checks, hierarchical confidence analysis and fail-closed artifact
  validation. These are implementation surfaces, not automatically adopted G34
  scientific fields.

## Local feasibility boundary

The selected predicate admits direct evaluation with one real 48-step
trajectory per registered episode and no hypothetical trajectory search:

```text
search_complexity=O(H)
intrinsic_K_search=0
hypothetical_transitions=0
nested_rollout_or_replanning=false
projected_nonformal_cap=within_20_minutes_subject_to_PM_measurement
projected_formal_cap=within_8_hours_subject_to_PM_prelaunch_measurement
```

PM found no code impossibility requiring a clarification. Exact random-process
support, controls, estimands, confidence gates and result branches remain
scientific choices and are intentionally not defaulted here.

## Workflow value test

This zero-compute audit prevents a fixed-schedule policy from being falsely
reported as process-law transport. The required indexed review is cheaper than
implementing and formally evaluating an unidentified random source. It is the
existing design-audit boundary, not a new workflow step.
