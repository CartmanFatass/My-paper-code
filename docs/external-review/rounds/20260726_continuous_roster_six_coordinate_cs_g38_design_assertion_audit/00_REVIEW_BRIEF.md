# G38 six-coordinate CS design assertion audit brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
code_acceptance_owner=project_manager
review_mode=DESIGN_ASSERTION_AUDIT
round=20260726_continuous_roster_six_coordinate_cs_g38_design_assertion_audit
selected_action=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT
formal_compute_authority=none_in_this_round
design_audit_compute=zero
conclusion_bearing_iteration_cost=0
```

## Purpose

G37-P0 closed mixed. Its factorized donor caused a positive average loss for
the exact coherent-input checkpoints, but neither the 0.05 materiality decision
nor capacity-8/12 deterministic access closed. External Pro retained the G36
coherent donor boundary and rejected evidence-volume rescue or further partial
donor-correlation peeling.

External Pro selected exactly one next action:

```text
CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT
```

This zero-compute round must freeze or reject a fresh paired comparison between
the full ten-coordinate no-carry actor and an otherwise matched actor trained
with coordinates 6:10 fixed, then exactly folded into a true six-coordinate
deployment actor. It grants no implementation, evaluation or formal-run
authority.

## Non-negotiable inherited boundary

```text
H=48
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

`FULL10_CS` receives all ten registered actor coordinates. `FOLD6_CS` uses the
same serialized training graph and parameter count but clamps coordinates 6:10
throughout training and evaluation to
`c=(1/2,1/2,1/2,24/47)`. Those constant coordinates must retain a live gradient
path during training. After training, every constant-coordinate affine
contribution must be folded exactly into the affected bias so the deployment
actor consumes only coordinates 0:6 with identical pre-tanh means, action
distributions and values. If exact folding is impossible in the accepted graph,
the comparison must be rejected rather than approximated.

## Feasibility and evidence economy

```text
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
formal_real_transitions_ceiling=1069056
formal_optimizer_steps_ceiling=3600
nonformal_wall_clock_cap_seconds=1200
formal_wall_clock_cap_seconds=28800
```

The primary direction is `FULL10_CS minus FOLD6_CS`, positive in favor of the
four varying history fields. A positive reduction branch may support only the
exact freshly trained folded architecture in this source family. A negative
branch may support only a finite-budget advantage for the varying inputs, not
task-level history necessity. External Pro must freeze the smallest exact
inventory, confidence plan, access gates, 0.05 margin, seeds and complete
first-match truth table before any implementation.
