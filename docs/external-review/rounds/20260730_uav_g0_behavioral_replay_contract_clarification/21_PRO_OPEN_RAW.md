G0_REPLAY_CONTRACT_DISPOSITION
G0_REPLAY_CONTRACT_DISPOSITION=POST_RETURN_READY_REPLAY_RULE

G0_REPLAY_CONTRACT_OBJECT

The registered oracle object is:

registered_oracle_object=(
two_sealed_prebehavior_candidate_traces,
immutable_candidate_ranking,
selected_candidate_id,
immutable_shared_channel_ledger,
frozen_RETURN_READY_branch_rule,
branch_aware_replay_certificate
)

Each of the two prebehavior candidate traces remains a realized trace generated exactly once before any behavioral service row exists.

During prebehavior candidate generation:

PREBEHAVIOR_RETURN_READY=UNOBSERVED

The selected reserve therefore follows the already frozen gate-hold fallback whenever the post-rejoin RETURN_READY predicate cannot yet be causally observed. Candidate generation may not synthesize, predict, estimate, impute, or inspect the future value or future activation time of RETURN_READY.

Both candidates are ranked only from their sealed prebehavior traces using the already frozen ranking keys:

hard physical or safety violation count
certified gate-arrival time
event-window target-tracking error
total path length
stage target coordinates

The ranking and selected_candidate_id become immutable before any behavioral service row is generated.

The selected behavioral oracle uses the same selected_candidate_id, same target schedule, same target-to-action transducer, same shared channel ledger, and same real S7-S1 guard. The only replay branch clarified here is the already frozen post-rejoin transition from gate to the selected reserve's original staging target.

For each behavioral episode, define:

R=min{t: RETURN_READY(t)=1 at the pre-action decision of physical step t}

RETURN_READY(t) is the already frozen predicate. It is evaluated only from information causally available before action collection at step t.

If the set is empty, define:

R=NONE

For the selected reserve, the post-rejoin target rule is exactly:

if R=NONE:
target=gate for every remaining physical step

if R is an integer:
target=gate for every step t<R target=original_stage for every step t>=R

The target change occurs before raw action construction at step R. It may not occur at R-1, after action construction at R, or at any step later than R.

After the transition at R, the selected reserve remains assigned to its original staging target. It may not return to the gate because of later service fluctuations.

For the diagnosed preserved episode:

selected_candidate=stage/+1
event_onset=191
rejoin_step=272
R=280

Therefore the complete step records through step 279 remain under literal prefix identity. The target, proposed action, guarded action, and resulting transition may first diverge at step 280.

The sealed prebehavior trace is not rewritten after R is observed. It remains the immutable trace used for candidate qualification and ranking. The behavioral trace is the causal execution of the frozen post-RETURN_READY branch.

G0_REPLAY_CONTRACT_INFORMATION_BOUNDARY

Prebehavior candidate generation and ranking may read only the information already allowed by the frozen oracle safety contract.

They may not read:

behavioral RETURN_READY values
future weakest-hotspot service
future per-user service
future association outcomes not required by the real guard
future delivered rate
future reward
future QoS
future catastrophe status
future access status
future G0 metrics
the behavioral value of R

The prebehavior trace must treat RETURN_READY as unobserved, not false as a scientific fact. Gate hold is the registered conservative fallback for an unresolved current-information condition.

The selected behavioral oracle may evaluate RETURN_READY(t) only at the pre-action boundary of step t using service information already produced by the completed behavioral history before step t.

No service quantity produced by the action at step t or by any later step may enter RETURN_READY(t).

Current behavioral service may be used only to evaluate the already frozen RETURN_READY predicate. It may not:

change selected_candidate_id
rerank the two reserve candidates
regenerate either candidate trace
alter any prebehavior ranking key
alter the immutable channel ledger
change the event ledger
change geometry
change safety rules
change collision rules
change the target-to-action transducer

The shared registered channel ledger remains immutable. Corresponding channel draw coordinates and draw blocks remain common to the prebehavior and behavioral executions.

The real S7-S1 guard remains active on every behavioral step, including step R and every step after R.

No post-RETURN_READY action is accepted merely because it follows the staging target. It must pass the same native channel update, connection construction, routing-path construction, link-capacity calculation, backhaul guard, collision rules, action support, and physical transition rules as every other action.

Behavioral service affects only the causal branch choice:

gate_hold
or
return_to_original_stage

It does not affect candidate ranking.

G0_REPLAY_CONTRACT_COMPARISON_RULE

Let:

P=sealed selected-candidate prebehavior fallback trace
B=selected-candidate behavioral trace

Define:

REPLAY_OK=
PREFIX_IDENTITY_OK
and BRANCHPOINT_IDENTITY_OK
and SHARED_LEDGER_IDENTITY_OK
and PREBEHAVIOR_SELF_REPLAY_OK
and BEHAVIORAL_SELF_REPLAY_OK
and TARGET_SWITCH_OK
and SAFETY_GUARD_OK

PREFIX_IDENTITY_OK

If R is an integer, then for every complete physical step t<R, P and B must agree byte-for-byte on:

physical_step
candidate_id
current_uav_positions
current_uav_velocities
current_service_mask
raw_candidate_action
shared_channel_draw_coordinate
shared_channel_draw_block
connections
routing_paths
exact_link_capacity_values_read_by_the_real_guard
real_guard_intervention_or_violation_output
guarded_executed_action
next_uav_positions
next_uav_velocities

If R=NONE, the same complete byte-identity requirement applies for every physical step in the episode.

BRANCHPOINT_IDENTITY_OK

If R is an integer, immediately before evaluating the target change and constructing the step-R raw action, P and B must agree byte-for-byte on:

physical_step=R
selected_candidate_id
current_uav_positions
current_uav_velocities
current_service_mask
event and lifecycle ownership state
survivor controller state
survivor RNG ownership
shared channel tape cursor
all non-controller RNG namespace states

The behavioral branch may then change only the selected reserve's target from gate to its original staging target.

At step R:

P retains target=gate
B changes target=original_stage

This target difference is the sole authorized cause of the initial semantic divergence.

SHARED_LEDGER_IDENTITY_OK

For every step t, including t>=R, P and B must continue to agree byte-for-byte on the exogenous registered fields:

physical_step
selected_candidate_id
shared_channel_draw_coordinate
shared_channel_draw_block
event ledger
service-mask schedule
static user positions
static geometry
physical-slot permutation ledger
RNG namespace ownership

Controller name, target branch, action, connection result, routing result, guard intervention, service result, or metric result may not reseed, skip, redraw, or reorder the shared channel tape.

POST_BOUNDARY_CROSS_TRACE_RULE

For t>=R, literal cross-trace equality is not required for these endogenous fields:

current_uav_positions
current_uav_velocities
raw_candidate_action
connections
routing_paths
exact_link_capacity_values_read_by_the_real_guard
real_guard_intervention_or_violation_output
guarded_executed_action
next_uav_positions
next_uav_velocities

These fields may diverge because B has changed its selected-reserve target while P retains the gate-hold fallback.

Their divergence is not a behavioral replay mismatch if all branch-local replay requirements pass.

PREBEHAVIOR_SELF_REPLAY_OK

An independent primitive reload of P from its registered initial state, immutable channel ledger, sealed gate-hold target sequence, and unchanged real guard must reproduce P byte-for-byte for every recorded safety field.

The prebehavior trace may not be regenerated from the behavioral branch.

BEHAVIORAL_SELF_REPLAY_OK

An independent primitive reload of B must begin from the same registered initial state and use:

the same selected_candidate_id
the same immutable channel ledger
the same target-to-action transducer
the same real S7-S1 guard
the same event ledger
the same service-mask schedule
the same ownership rules
the same frozen RETURN_READY predicate

For t<R, the reload must reproduce the common prefix.

At t=R, the reload must independently observe RETURN_READY(t)=1 from the completed causal behavioral history, change the selected reserve's target before action construction, and reproduce B.

For every t>=R, the reload must reproduce byte-for-byte within the behavioral branch:

the behavioral current physical state
the behavioral raw action
the behavioral connections
the behavioral routing_paths
the exact behavioral link-capacity values read by the real guard
the behavioral guard output
the behavioral guarded action
the behavioral next physical state

Branch-local byte identity replaces literal P-versus-B action and state identity after R.

TARGET_SWITCH_OK

TARGET_SWITCH_OK holds only if:

no target change occurs before R
the target changes exactly once
the change occurs before raw action construction at R
the changed target is the selected reserve's original staging target
no unaffected owner changes target
no reserve candidate is reselected
the target remains the staging target after R

If R=NONE, TARGET_SWITCH_OK requires that the selected reserve remain at the gate and that full P-versus-B trace identity hold through the complete episode.

SAFETY_GUARD_OK

The unchanged real S7-S1 guard must evaluate every P and B action.

A post-R guard intervention is valid physical behavior when its inputs and output pass branch-local exact replay.

A post-R guard intervention may affect the behavioral trajectory and G0 behavioral metrics. It may not trigger candidate reranking or candidate regeneration.

The invariant replacing full-episode literal trace identity is therefore:

identical pre-R realized prefix
plus identical step-R pre-action branchpoint
plus identical shared exogenous ledger for all steps
plus byte-exact self-replay of each endogenous post-R branch
plus exact first-RETURN_READY target switching
plus unchanged real safety evaluation

G0_REPLAY_CONTRACT_FAILURE_SEMANTICS

Any of the following sets VALID=0 and selects:

INVALID_UAV_G0_REALIZATION

failure of any pre-R byte-identity field
failure of step-R pre-action branchpoint identity
target change before R
target change after action construction at R
target change later than R
failure to change the target when RETURN_READY first becomes true
target change to anything other than the selected reserve's original staging target
return from staging to gate after R
candidate reranking after behavioral service is visible
candidate regeneration after behavioral service is visible
candidate identity change
candidate-specific channel reseeding
shared channel coordinate mismatch
shared channel draw-block mismatch
shared channel tape reordering or skipping
future service visibility during candidate generation or ranking
use of step-t or future service to evaluate RETURN_READY(t)
prebehavior self-replay failure
behavioral branch-local self-replay failure
unrecorded behavioral guard input
changed, approximated, disabled, substituted, or bypassed real guard
behavioral action applied without real-guard evaluation
ownership certificate failure
survivor-continuity failure
permutation certificate failure
pairing certificate failure
NO_EVENT identity certificate failure
failure to establish REPLAY_OK

The expected post-R difference between P and B in target, raw action, guard-derived state, guarded action, or physical trajectory is not itself an invalid realization.

It is valid only when the first difference occurs at the exact step R authorized above and all branch-local replay and safety certificates pass.

If R=NONE, any P-versus-B target, action, guard-input, guard-output, or physical-state difference is an invalid realization.

If INVALID_UAV_G0_REALIZATION is selected under this contract, no result with any of the following dispositions is admissible:

INFEASIBLE_UAV_G0_SOURCE
ORACLE_ONLY_UAV_G0_SOURCE
NON_CAUSAL_UAV_G0_SOURCE
UNDERPOWERED_UAV_G0_SOURCE
IDENTIFIED_UAV_G0_SOURCE

A missing replay certificate may not be interpreted as oracle infeasibility, online inaccessibility, causal failure, underpower, or source identification.

G0_REPLAY_CONTRACT_PROTECTED_FIELDS

physical_horizon_steps=500
physical_fleet_size=8
hotspot_count=3
users_per_hotspot=10
temporary_leave_count_per_event_episode=1
temporary_rejoin_count_per_event_episode=1
event_is_unannounced=true
detection_delay_steps=0
geometry=unchanged
metrics=unchanged
confidence_rules=unchanged
first_match_rules=unchanged
same_information_constructive_control=unchanged
no_reallocation_control=unchanged
oracle_target_schedules=unchanged
oracle_ranking_keys=unchanged
learning_enabled=false
learned_model_count=0
optimizer_enabled=false
optimizer_update_count=0
checkpoint_enabled=false
checkpoint_count=0
paired_episode_ids=128
bootstrap_resamples=10000
ownership_certificate=required_exact
permutation_certificate=required_exact
no_event_identity_certificate=required_bitwise
oracle_qualification_certificate=required_before_behavioral_interpretation
oracle_future_channel_exception=safety_guard_only
oracle_direct_behavioral_service_visibility=false
oracle_candidate_generation_service_visibility=false
oracle_candidate_ranking_service_visibility=false
oracle_runtime_current_service_visibility=RETURN_READY_only
same_information_future_channel_visibility=false
no_reallocation_future_channel_visibility=false
prebehavior_candidate_trace=retained_immutable
prebehavior_RETURN_READY=UNOBSERVED
behavioral_target_switch_step=first_pre_action_step_with_RETURN_READY_true
candidate_reranking_after_behavior=false
postboundary_cross_trace_endogenous_identity=not_required
postboundary_branch_local_identity=required_bytewise
runtime_real_guard=required_every_step
evidence_search_complexity=O(HK_search)
K_search=2
K_search_ceiling=16
hypothetical_candidate_transitions_ceiling=2H
candidate_count_independent_of_H=true
nested_rollout_replanning=false
tree_search=false
beam_search=false
MCTS=false
G51_merge=false
formal_execution_authorized=false
code_acceptance=false
paper_acceptance=false
claim_scope=SOURCE_IDENTIFIABILITY_G0_ONLY
scientific_iteration_cost=0
