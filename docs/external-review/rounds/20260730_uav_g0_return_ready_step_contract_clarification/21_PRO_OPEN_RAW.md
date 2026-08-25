G0_RETURN_READY_STEP_DISPOSITION
G0_RETURN_READY_STEP_DISPOSITION=KEEP_CAUSAL_R_273

G0_RETURN_READY_STEP_PREDICATE

Let:

T_rejoin=O+D

For the diagnosed episode:

O=191
T_rejoin=272

Let i_rejoin be the new lifecycle epoch created in the same physical slot at the pre-action boundary of physical step T_rejoin.

All lifecycle-state lookups use lifecycle-owner mapping:

internal_row(i,t)=owner_to_internal_order_t[i]

A physical storage row is not an admissible substitute for internal_row(i,t). No storage-row value may directly index an internal-order safety or lifecycle record.

Define:

ACTIVE_AT_PRIMARY_PRE(i,t)=1

if and only if the correctly owner-mapped pre-action record for lifecycle i at physical step t reports both:

service_active=true
at_registered_primary=true

The meaning of at_registered_primary is unchanged. This clarification introduces no new distance tolerance, target tolerance, position test, or service semantic.

Define:

ONE_COMPLETE_PRIMARY_STEP(i,t)=1

if and only if all of the following hold:

t>=T_rejoin+1
ACTIVE_AT_PRIMARY_PRE(i,t-1)=1
the executed service-active mask for step t-1 includes lifecycle i
physical step t-1 completed
ACTIVE_AT_PRIMARY_PRE(i,t)=1

Thus the rejoin step itself may be the completed step. Because rejoin occurs before action collection at step T_rejoin, a lifecycle that is active at its registered primary throughout completed step T_rejoin satisfies the one-complete-step term at pre-action step T_rejoin+1.

Define the pre-action weakest-hotspot service:

S_pre(t)=min_z rho_z_after_step(t-1)

where rho_z_after_step(t-1) is the registered hotspot service value produced by the completed behavioral transition at physical step t-1 and stored before any target selection or action construction for physical step t.

No action, channel result, delivered-rate result, or service value produced at physical step t may enter S_pre(t).

The exact predicate is:

RETURN_READY(t)=1

if and only if all of the following hold:

t>=T_rejoin+1
ONE_COMPLETE_PRIMARY_STEP(i_rejoin,t)=1
S_pre(t)>=0.90

Otherwise:

RETURN_READY(t)=0

The causal return-ready step is:

R=min{t: RETURN_READY(t)=1 at the pre-action boundary of physical step t}

If the set is empty:

R=NONE

No fixed waiting period, grace period, smoothing window, hysteresis window, confirmation count, or additional post-rejoin delay is part of this predicate.

G0_RETURN_READY_STEP_ASSERTION

For the diagnosed episode:

selected_candidate=stage/+1
event_onset=191
rejoin_step=272

At the pre-action boundary of step 273:

273>=272+1
ACTIVE_AT_PRIMARY_PRE(i_rejoin,272)=1
the executed service-active mask for step 272 includes i_rejoin
physical step 272 completed
ACTIVE_AT_PRIMARY_PRE(i_rejoin,273)=1
S_pre(273)=1.0
S_pre(273)>=0.90

Therefore:

RETURN_READY(273)=1
R=273

The prior episode-specific assertion:

R=280

is replaced by:

R=273

The prior episode-specific assertion that complete prebehavior-versus-behavioral step records must remain identical through step 279 is replaced by:

complete step identity is required for every t<273
complete step identity is therefore required through step 272

At the pre-action boundary of step 273, before the target switch and before raw action construction, the branchpoint state must remain byte-identical under the existing branchpoint certificate.

At step 273, the behavioral target rule must perform exactly one change:

selected_reserve_target: gate -> original_stage

The change occurs before raw action construction for step 273.

The sealed prebehavior fallback trace retains:

selected_reserve_target=gate

The behavioral trace uses:

selected_reserve_target=original_stage

for step 273 and every later step.

The first authorized cross-trace endogenous divergence is step 273. Endogenous fields may remain accidentally byte-identical at step 273 because of clipping, guard intervention, or coincident actions, but this does not change R. R is determined by the causal predicate, not by the first differing byte.

The post-boundary branch-local replay rules begin at step 273.

No seven-step delay is permitted.

No service value is redefined.

No target, geometry, metric, confidence rule, candidate ranking key, or first-match threshold is changed.

G0_RETURN_READY_STEP_INFORMATION_BOUNDARY

RETURN_READY(t) is evaluated exactly once at the pre-action boundary of physical step t.

Its permitted inputs are only:

T_rejoin from the frozen event ledger
the correctly owner-mapped lifecycle record at pre-action step t-1
the executed service-active mask from completed step t-1
the completion status of physical step t-1
the correctly owner-mapped lifecycle record at pre-action step t
S_pre(t) from completed physical step t-1

Its prohibited inputs include:

any service value produced by the action at step t
any channel result produced during step t
any association result produced during step t
any delivered rate produced during step t
any reward or QoS produced during step t
any value from step t+1 or later
future RETURN_READY values
the eventual first action or state byte that differs between traces
candidate ranking outcomes other than the already frozen selected_candidate_id
physical storage row used as an internal-order index
an inferred or inserted seven-step delay
a smoothed or retrospectively selected service window

Behavioral service may affect only the already frozen gate_hold versus return_to_original_stage branch.

Behavioral service may not:

rerank the two candidates
change selected_candidate_id
regenerate a candidate trace
alter a sealed prebehavior ranking key
alter the immutable shared channel ledger
change the real safety guard
change event timing
change lifecycle ownership
change geometry
change metrics
change confidence rules

The reconstruction mapping is frozen as:

lifecycle owner -> current internal-order row -> lifecycle safety record

The forbidden mapping is:

physical storage row -> internal-order safety record

Correcting the forbidden mapping is a mechanical realization correction. It does not authorize a different RETURN_READY predicate or a different R.

G0_RETURN_READY_STEP_FAILURE_SEMANTICS

Any of the following sets VALID=0 and selects:

INVALID_UAV_G0_REALIZATION

using a physical storage row to index an internal-order lifecycle or safety record
failure to resolve i_rejoin through the lifecycle-owner mapping
failure to reproduce the registered ACTIVE_AT_PRIMARY_PRE values
failure to reproduce S_pre(t) from the completed step t-1 history
using service generated at step t to evaluate RETURN_READY(t)
using future service or future state to evaluate RETURN_READY(t)
adding any fixed or adaptive delay after RETURN_READY first becomes true
requiring multiple consecutive service confirmations
using a smoothed service value instead of S_pre(t)
setting R to the first differing trace byte instead of the first true predicate step
setting R to any t later than the first pre-action step satisfying the predicate
changing the selected reserve target before R
failing to change the selected reserve target before raw action construction at R
changing the target after raw action construction at R
changing the selected reserve target more than once
returning the selected reserve from staging to the gate after R
failure of pre-R byte identity
failure of step-R pre-action branchpoint identity
failure of post-R branch-local replay
failure of shared-ledger identity
failure of real-guard evaluation
ownership certificate failure
survivor-continuity certificate failure
permutation certificate failure
pairing certificate failure
NO_EVENT identity certificate failure

For the diagnosed episode, any of the following is specifically invalid:

stored_R!=273
asserted_R=280
required_prefix_identity_through_step=279
behavioral_target_switch_step!=273

The corrected valid assertions are:

stored_R=273
required_complete_prefix_identity_through_step=272
required_branchpoint_identity_at_pre_action_step=273
behavioral_target_switch_before_raw_action_step=273

A failure under this clarification may not be interpreted as physical infeasibility, online inaccessibility, causal insufficiency, statistical underpower, or source identification.

When VALID=0, none of the following is admissible:

INFEASIBLE_UAV_G0_SOURCE
ORACLE_ONLY_UAV_G0_SOURCE
NON_CAUSAL_UAV_G0_SOURCE
UNDERPOWERED_UAV_G0_SOURCE
IDENTIFIED_UAV_G0_SOURCE

No source result exists until the corrected contract is mechanically realized and all existing certificates pass.

G0_RETURN_READY_STEP_PROTECTED_FIELDS

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
return_ready_service_source=completed_step_t_minus_1
return_ready_service_threshold=0.90
return_ready_required_completed_post_rejoin_steps=1
return_ready_artificial_delay_steps=0
return_ready_owner_mapping=lifecycle_owner_to_internal_order
storage_row_as_internal_order_index=false
candidate_reranking_after_behavior=false
postboundary_cross_trace_endogenous_identity=not_required
postboundary_branch_local_identity=required_bytewise
runtime_real_guard=required_every_step
episode_0_selected_candidate=stage/+1
episode_0_event_onset=191
episode_0_rejoin_step=272
episode_0_return_ready_step=273
episode_0_complete_prefix_identity_last_step=272
episode_0_branchpoint_pre_action_step=273
episode_0_first_authorized_endogenous_divergence_step=273
episode_0_prior_R_280_assertion=replaced
service_semantics=unchanged
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
