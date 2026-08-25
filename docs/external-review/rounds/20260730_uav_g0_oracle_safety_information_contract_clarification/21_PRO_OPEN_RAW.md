G0_ORACLE_SAFETY_INFORMATION_DISPOSITION
G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=REGISTERED_LEDGER_ALLOWED

G0_ORACLE_SAFETY_INFORMATION_VISIBLE_FIELDS

The future-channel exception is limited to the mechanically qualified oracle safety evaluation. It does not change the same-information constructive controller, no-reallocation control, behavioral metrics, or any learned-policy information contract.

For each episode ID, freeze one immutable oracle safety ledger before either candidate is ranked and before any behavioral service row is generated.

The common ledger origin is the byte-exact complete environment state immediately before candidate-only advancement, including the byte-exact state of the G1 channel RNG namespace produced by:

_channel_rng=_namespace_random_state(environment_seed,3)

Both reserve candidates start from byte-identical clones of that complete pre-candidate state.

The safety subsystem may consume and record only these candidate-step fields:

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

The target-schedule generator retains its previously frozen visibility:

complete event owner, onset, duration, and rejoin ledger
current complete physical state
registered target geometry
unchanged dynamics and action limits

The target-schedule generator may not directly inspect:

shared_channel_draw_block
connections
routing_paths
link capacity
guard outcome
future user service
future association outcome
future delivered rate
future reward
future QoS
J_event
Q_ordinary
M_event
A_control
B_access
C_cat
any paired delta

The candidate ranker may read only the already frozen ranking keys:

hard physical or safety violation count
certified gate-arrival time
event-window target-tracking error
total path length
stage target coordinates

The ranker may not directly read or add a key derived from connections, routing_paths, link capacity, delivered service, reward, QoS, or any G0 metric. Channel and routing information may influence ranking only through the guarded physical trajectory and the already registered safety-violation key.

The two candidates share identical exogenous channel draw blocks at corresponding channel-update coordinates. Candidate-specific connections, routing_paths, link capacities, guarded actions, and resulting physical states may differ because their candidate trajectories differ.

The registration order is exact:

Freeze episode geometry, event ledger, initial physical state, slot permutation, service-mask schedule, and all RNG namespace states.

Freeze the complete channel RNG draw-address schema.

Materialize one immutable channel draw tape.

Advance each of the two candidates exactly once using the same draw tape and the real S7-S1 guard.

Seal both candidate safety traces.

Rank the sealed traces using only the frozen ranking keys.

Generate behavioral service rows only after candidate selection is immutable.

The ledger is independent of future behavioral service rows in the causal and registration sense: no behavioral service value exists or is visible when the ledger and candidate choice are frozen, and no service result can alter the channel tape, safety trace, or ranking. The later behavioral rows intentionally reuse the registered channel realization, so probabilistic independence is neither required nor claimed.

G0_ORACLE_SAFETY_INFORMATION_CERTIFICATE

The pre-behavior oracle safety certificate passes only if all of the following hold.

COMMON_PRESTATE_CERTIFICATE

Both candidates begin from byte-identical complete environment states except for the registered reserve-candidate identity and its resulting target schedule.

The common state includes identical geometry, users, event ledger, physical-slot permutation, service mask, physical state, channel RNG state, and every non-controller RNG state.

CHANNEL_DRAW_SCHEMA_CERTIFICATE

Every use of the channel RNG during candidate advancement is assigned an immutable coordinate:

(physical_step,channel_update_ordinal,rng_operation,shape,dtype)

The ordered coordinate schema must be identical for both candidates and independent of candidate identity, action, position, connection result, routing result, service result, and guard result.

If the RNG request count, order, operation, shape, or dtype can differ between candidates, the registered-ledger policy is not realized.

SHARED_DRAW_CERTIFICATE

At every corresponding channel-update coordinate, both candidates consume byte-identical channel draw blocks.

Candidate name, reserve identity, action, target, connection state, routing state, guard intervention, and behavioral outcome may not reseed, skip, redraw, or advance the shared tape differently.

REAL_GUARD_CERTIFICATE

Each candidate uses the unchanged registered S7-S1 channel update, connection construction, routing-path construction, link-capacity calculation, backhaul safety guard, collision rules, action support, and physical transition rules.

No channel-independent approximation, disabled guard, alternate capacity rule, post-hoc correction, or identity assumption is permitted.

The action that advances candidate physics is the real guard output, not the unguarded proposed action.

COMPLETE_GUARD_INPUT_CERTIFICATE

For every candidate step, the ledger records the exact native connections, routing_paths, and link-capacity values read by the real guard, in their native ordering, shape, dtype, and precision.

Every state value capable of changing the real guard output must either appear in the ledger or be covered by the byte-exact common prestate and deterministic transition certificate.

An unrecorded candidate-dependent guard input fails the certificate.

SAFETY_ONLY_VISIBILITY_CERTIFICATE

Candidate generation and ranking expose no future per-user service, association result not required by the guard, delivered rate, reward, QoS, hotspot metric, access indicator, catastrophe indicator, or first-match estimand.

If the real guard cannot be invoked and certified without making such behavioral service fields available to the generator or ranker, the certificate fails.

SEALED_BEFORE_RANKING_CERTIFICATE

The complete two-candidate safety ledger and its content digest are frozen before the ranking function is called.

No candidate may be extended, regenerated, repaired, or rerun after either candidate's ranking key is known.

FROZEN_RANKING_CERTIFICATE

The exact original lexicographic ranking remains:

hard physical or safety violation count
certified gate-arrival time
event-window target-tracking error
total path length
stage target coordinates

No channel, routing, capacity, service, reward, or metric quantity is inserted as an additional ranking key.

BEHAVIORAL_REPLAY_CERTIFICATE

The selected oracle behavioral row reuses the registered channel tape and unchanged real guard.

At every corresponding step, the registered and behavioral traces must agree byte-for-byte on channel draw coordinate, channel draw block, connections, routing_paths, guard-consumed link capacities, proposed action, guarded action, and resulting physical state, up to fields that are explicitly behavioral diagnostics and do not feed dynamics or safety.

A replay mismatch fails the certificate; it is not treated as stochastic oracle performance.

PAIRING_CERTIFICATE

The paired EVENT and NO_EVENT rows retain the originally frozen non-event randomness. The safety-ledger exception does not permit controller-name-dependent environment seeds or separate favorable channel draws.

OWNERSHIP_AND_PERMUTATION_CERTIFICATE

The registered safety ledger must preserve the existing ownership, survivor continuity, physical-slot permutation, and NO_EVENT identity certificates. Connections, routing paths, guard outcomes, and executed world-space actions must transform consistently under the registered physical-record permutation.

COMPLETENESS_CERTIFICATE

Both and only the two registered reserve candidates are evaluated. A qualified failure of both candidates under the real guard may support the existing oracle feasibility result semantics; an omitted candidate or an uncertified guard path may not.

G0_ORACLE_SAFETY_INFORMATION_FAILURE_SEMANTICS

Any of the following sets VALID=0 and selects the first-match result INVALID_UAV_G0_REALIZATION:

missing or incomplete oracle safety ledger
ledger generated after any behavioral service row is read
candidate-specific channel seeding
candidate-dependent channel draw-address schema
non-identical shared draw blocks at corresponding coordinates
unlogged guard input capable of changing guard behavior
direct target-generator access to channel, routing, or capacity fields
direct ranker access to channel, routing, capacity, or behavioral service fields
future reward, QoS, delivered-rate, hotspot-service, or G0-metric visibility
use of an approximate, disabled, substituted, or bypassed safety guard
ranking an unguarded trajectory
candidate regeneration or repair after ranking information is available
behavioral replay mismatch
ownership, permutation, pairing, or NO_EVENT certificate failure
failure to prove that both registered candidates were evaluated
failure to establish the complete pre-behavior oracle safety certificate

When any such certificate failure occurs, no INFEASIBLE_UAV_G0_SOURCE, ORACLE_ONLY_UAV_G0_SOURCE, NON_CAUSAL_UAV_G0_SOURCE, UNDERPOWERED_UAV_G0_SOURCE, or IDENTIFIED_UAV_G0_SOURCE result is admissible.

A fully certified real-guard intervention is not itself an invalid realization. If the immutable ledger proves that the real guard alters or blocks a candidate and the guarded candidate consequently fails arrival, tracking, safety, or service, that is valid physical evidence under the existing oracle and first-match rules.

A qualified behavioral oracle failure may select INFEASIBLE_UAV_G0_SOURCE only after the complete safety certificate establishes that the two-candidate search was exact, shared-ledger, real-guard, and complete. Lack of a certificate may never be reinterpreted as physical infeasibility or statistical underpower.

G0_ORACLE_SAFETY_INFORMATION_COMPLEXITY

K_search=2

Each reserve candidate is advanced at most once through H physical steps.

hypothetical_candidate_transitions<=2*H

candidate_generation_complexity=O(H*K_search)

channel_ledger_materialization_complexity=O(H)

candidate_safety_ledger_storage=O(H*K_search)

The fleet size and native guard-field widths remain fixed at eight assets, so recording connections, routing_paths, and guard-consumed capacities does not change the registered asymptotic search ceiling.

Generating the shared channel tape does not advance an additional hypothetical physical trajectory.

The selected candidate's later behavioral execution is the one real evidence trajectory and is not an additional search candidate.

The following remain forbidden:

nested rollout replanning
candidate regeneration at each real step
adaptive candidate creation
candidate-specific channel redraw
tree search
beam search
MCTS
search after behavioral service inspection
more than two reserve candidates

G0_ORACLE_SAFETY_INFORMATION_PROTECTED_FIELDS

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
same_information_future_channel_visibility=false
no_reallocation_future_channel_visibility=false
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
