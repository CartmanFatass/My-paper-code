# G39 native six-coordinate training design assertion audit brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
code_acceptance_owner=project_manager
review_mode=DESIGN_ASSERTION_AUDIT
round=20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit
selected_action=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_DESIGN_ASSERTION_AUDIT
formal_compute_authority=none_in_this_round
design_audit_compute=zero
conclusion_bearing_iteration_cost=0
```

## Purpose

Formal G38 supports a freshly trained constant-input route that folds exactly
into a true six-coordinate deployment actor. Both FULL10 and FOLD6 pass access;
all 45 fold gates have exact zero recorded error, and FULL10-minus-FOLD6 CI95 is
`[-0.01008621, -0.00312729, 0.00841468]`. External Pro accepts that deployment
boundary but preserves one strongest limitation: FOLD6 was still trained through
four constant columns, 136 redundant affine weights and their separate Adam
states before folding.

External Pro returned `CONTINUE` and scheduled one current action:

```text
CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_DESIGN_ASSERTION_AUDIT
```

Scheduling G39 is an attribution decision, not scientific uniqueness. Credit,
broader process/horizon/capacity, non-G33 UAV transport, checkpoint coherence and
recurrence directions remain live or parked under their recorded conditions.
This zero-compute round must freeze or reject the smallest matched test of the
training-only constant-column parameterization. It grants no implementation,
evaluation or formal-run authority.

## Non-negotiable inherited boundary

```text
H=48
CONST10_FOLD6=accepted_G38_constant_input_training_then_exact_fold
NATIVE6_CS=six_coordinate_raw_input_affines_from_initialization
varying_actor_information=identical_six_coordinates
training_source=unchanged_G32_capacity8_fixed_process
evaluation_source=unchanged_G34_P0_fixed_and_random_capacity6_8_12
actor_carry=CS_zero
critic=unchanged_true_current_state
credit=unchanged_G31_realized_future_tail
reward=unchanged
action_distribution=unchanged
active_set_log_count_mask_prefix=unchanged
fresh_paired_training=true
checkpoint_selection=final_only
G33_reactivation=forbidden
```

The intentional scientific treatment is only the absence in `NATIVE6_CS` of
the four constant input columns, their 136 trainable weights, their independent
Adam moments and the post-training fold. Actor information, all graph widths
after the raw-input affines, critic capacity, credit, source, interactions, PPO
passes, optimizer-step exposure and final-checkpoint selection remain matched.

Initial functions must be matched. The retained six-coordinate weights are
copied, and each native bias must equal the associated constant-route effective
bias: `b_native = b_const + W_c c`, with
`c=(1/2,1/2,1/2,24/47)`. The audit must freeze exact RNG ownership, optimizer
state initialization and any treatment-induced parameter/update accounting.

## Feasibility and evidence economy

```text
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
nonformal_real_transitions_ceiling=26880
nonformal_optimizer_steps_ceiling=120
nonformal_wall_clock_cap_seconds=1200
formal_real_transitions_ceiling=1013760
formal_optimizer_steps_ceiling=3600
formal_wall_clock_cap_seconds=28800
```

The primary direction is `CONST10_FOLD6 minus NATIVE6_CS`, positive in favor of
the redundant constant-input parameterization. A native-six pass may support
only native-six training sufficiency inside G39-P0. A negative result may support
only a finite-budget optimization/access advantage for the frozen redundant
parameterization, not history necessity or six-coordinate inexpressivity.
External Pro must freeze the smallest conclusion-bearing inventory, confidence
plan, access gates, 0.05 margin, initialization mapping, parameter inventory,
optimizer-state semantics and complete first-match truth table before any code.
