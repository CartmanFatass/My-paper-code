G0_EXECUTABLE_ADDENDUM_GEOMETRY

physical_horizon_steps=500
physical_fleet_size=8
ground_users=30
ground_base_stations=1
fixed_altitude=true
battery_enabled=false
charging_enabled=false
terminal_loss_enabled=false

Let b be the existing ground-base-station world coordinate. This contract requires b to equal the rectangular map center. Let L=min(map_width,map_height). Failure of that equality or failure of the complete geometry support to remain inside the existing map is an exact realization failure; no clipping, projection, rejection sampling, or conditional resampling is permitted.

For every episode, independently sample phi~Uniform[0,2*pi). For z in {0,1,2}, define:

theta[z]=phi+2piz/3
u[z]=(cos(theta[z]),sin(theta[z]))
v[z]=(-sin(theta[z]),cos(theta[z]))
c[z]=b+0.300Lu[z]

The three hotspot centers are c[0], c[1], and c[2].

Each hotspot contains exactly ten users. For j in {0,...,9}, independently sample U[z,j],V[z,j]~Uniform[0,1) and set:

user_position[z,j]=c[z]+0.040Lsqrt(U[z,j])(cos(2piV[z,j]),sin(2pi*V[z,j]))

User positions remain fixed for the complete episode. Hotspot membership is an environment metric ledger only and is not supplied as an actor identity or desired assignment.

For s in {-1,+1}, define the six primary service targets:

primary[z,s]=c[z]+s0.040L*v[z]

Define the reserve-axis unit vector and the two reserve staging targets:

w=(cos(phi+pi/12),sin(phi+pi/12))
stage[s]=b+s0.050L*w

Define one inward oracle holding gate for every primary target:

gate[z,s]=primary[z,s]-0.060Lu[z]

For each of the eight target labels in
{primary[z,s]:z in {0,1,2},s in {-1,+1}} union
{stage[-1],stage[+1]},
independently sample Uq,Vq~Uniform[0,1) and set:

uav_perturbation[q]=0.002Lsqrt(Uq)(cos(2piVq),sin(2pi*Vq))
initial_uav_position[q]=q+uav_perturbation[q]
initial_uav_velocity[q]=(0,0)

All other initial physical fields use the unchanged S7-S1 defaults. There is no perturbation rejection, repair, clipping, or result-dependent redraw. A sampled support violation is INVALID_UAV_G0_REALIZATION.

After all target-owned positions and perturbations are instantiated, sample one uniform permutation over all 8! physical-slot assignments. The permutation changes storage ownership only. It must not change world-space positions, target coordinates, event probabilities, controller decisions, channel streams, or service outputs.

The event owner is uniform over the six lifecycles initially assigned to primary[z,s]. Event owner sampling occurs after physical-slot permutation but is target-owned rather than slot-index-owned.

Exactly one event is sampled:

event_cell=UNANNOUNCED_PRIMARY_TEMPORARY_LEAVE
event_owner=uniform_over_six_primary_lifecycles
event_onset=DiscreteUniform{180,...,220}
event_duration=DiscreteUniform{80,...,100}
announcement_lead_steps=0
detection_delay_steps=0
leave_timing=before_action_collection
leave_motion=position_hold_and_zero_velocity
leave_communication=disabled
leave_service_action=none
rejoin_timing=before_action_collection_at_O_plus_D
rejoin_lifecycle=new_epoch_same_physical_slot
rejoin_old_actor_state_inheritance=false
rejoin_old_action_rng_inheritance=false

The paired NO_EVENT counterpart retains the same sampled owner, onset, duration, geometry, slot permutation, user positions, initial perturbations, channel randomness, and every non-event source stream, but disables the LEAVE/REJOIN transition.

Independent RNG namespaces are required for phi, user positions, UAV perturbations, physical-slot permutation, channel randomness, event owner, event onset, and event duration. Controller-name-dependent environment reseeding is forbidden.

G0_EXECUTABLE_ADDENDUM_CONTROLS

Target coordinates and opaque lifecycle handles may be used internally to preserve target ownership. Neither physical-slot indices nor lifecycle-epoch numbers may enter a distance, priority, action feature, or tie decision.

Initial target ownership is the unique minimum-cost assignment from the eight current lifecycle rows to the eight nominal targets, minimizing:

sum_i ||initial_uav_position[i]-assigned_target[i]||^2

Rows are canonically ordered by their complete current anonymous physical content:

(x,y,vx,vy)

Targets are canonically ordered by:

(target_x,target_y)

If multiple assignments remain tied, select the lexicographically smallest target-coordinate sequence in that canonical row order. If two distinct lifecycles are bitwise identical in all allowed physical tie fields and a distinct selection remains necessary, the realization is invalid. Physical-slot index is never a fallback tie key.

The initial-assignment certificate must recover exactly two primary targets per hotspot and exactly two staging targets. Failure is INVALID_UAV_G0_REALIZATION.

The same-information constructive and no-reallocation controls use one common deterministic target-to-action transducer. It must be byte-identical, including every numeric parameter and the low-level safety/collision correction, to the common deterministic target tracker used by both closed formal G1 controls. It may read only current physical state, current service mask, and current world-space targets. It may not read controller name, future event fields, future channel fields, physical-slot identity, or lifecycle-epoch value.

The target-tracker qualification certificate must establish:

same current state bits plus same target map implies bitwise-identical raw actions;
same current state bits plus same target map implies bitwise-identical executed actions;
all actions lie in the unchanged Scenario-7 action support;
inactive lifecycles produce no action;
the same safety and collision correction is used for both controls;
the tracker is permutation-equivariant under lifecycle-row permutation;
no controller-specific parameter, branch, or target tolerance exists;
all tracker code and numeric parameters are frozen before any G0 behavioral row is produced.

If that exact common G1 transducer cannot be isolated or qualified, the realization is invalid. A new or tuned target tracker may not be selected after observing G0 behavior.

The mechanically qualified oracle may read the complete event owner, onset, duration, and rejoin ledger, plus the current complete physical state. It may not change physics, action bounds, collision rules, safety rules, users, channel draws, event timing, or the service mask. It may not teleport and may not train.

The oracle has exactly two target-schedule candidates, one for each lifecycle initially owning stage[-1] or stage[+1]. Thus K_search=2.

For reserve candidate r and failed target primary[z,s], the target schedule is:

before its certified latest departure: stage[r]
from certified latest departure until O: gate[z,s]
from O until O+D: primary[z,s]
from O+D until RETURN_READY: gate[z,s]
after RETURN_READY: stage[r]

All unaffected primary owners retain their initial primary targets. The other reserve retains its staging target.

For each reserve candidate, a mechanically certified minimum-time physical trajectory to gate[z,s] is generated under the unchanged dynamics, action support, and safety rules. The candidate generator may use the event ledger and exact kinematics but may not instantiate, consume, inspect, or rank by future channel or service randomness. Each of the two candidate trajectories is advanced at most once through H physical steps. Candidate selection minimizes, in order:

hard physical or safety violation count;
certified gate-arrival time;
certified event-window target-tracking error;
total path length;
stage target coordinates in lexicographic order.

No behavioral service metric is used to select the oracle candidate.

The oracle qualification certificate must establish all of the following:

both reserve candidates are evaluated;
each candidate obeys the exact registered target schedule;
each candidate trajectory is admissible under the unchanged physics and action support;
the selected candidate is the exact lexicographic winner;
future channel or service outputs are not read during candidate generation or selection;
moving an unaffected primary owner would create another vacant primary target, and the two reserve candidates are complete for the frozen one-reserve substitution source;
a failed qualified oracle row may therefore be interpreted as source infeasibility rather than planner failure;
candidate generation and evaluation are O(H*K_search), with K_search=2;
there is no nested rollout, replanning, tree search, beam search, MCTS, or adaptive candidate creation.

If the oracle qualification certificate is absent, incomplete, or failed, VALID=0 and the first-match result is INVALID_UAV_G0_REALIZATION. Oracle-certificate absence must never select INFEASIBLE_UAV_G0_SOURCE, ORACLE_ONLY_UAV_G0_SOURCE, or UNDERPOWERED_UAV_G0_SOURCE.

The same-information constructive control may read only:

the current unordered active roster;
current UAV positions and velocities;
current service availability;
current hotspot demand and delivered-rate measurements;
current channel and association state;
current ground-base-station, primary-target, gate, and staging geometry;
opaque lifecycle handles solely for state ownership.

It may not read future event owner, onset, duration, rejoin time, future channel state, future user state, physical-slot identity, or lifecycle-epoch value.

Before the event, every primary owner tracks its initial primary target and both reserves track their staging targets.

At the first pre-action decision with active roster count seven, exactly one primary target must be vacant. The same-information control selects the reserve with minimum current squared Euclidean distance to that vacant primary target. Ties are resolved by current anonymous physical content and then staging-target coordinates. Physical-slot index is forbidden. The selected reserve immediately changes target to the vacant primary target. Every survivor retains its previous target ownership.

At rejoin, the new lifecycle is assigned the vacated primary target. The selected reserve changes target from the primary target to gate[z,s]. Define:

RETURN_READY(t)=1

if and only if all of the following hold:

t>=O+D+1;
the new lifecycle has been active at primary[z,s] for one complete physical step;
the current pre-action weakest-hotspot service is at least 0.90.

At the first RETURN_READY step, the selected reserve changes target from gate[z,s] to its original staging target. If RETURN_READY never occurs, it remains at gate[z,s]. No future service value is used.

The no-reallocation control receives the same current observation and service mask as the same-information control. It freezes every lifecycle's pre-event target ownership. During absence, the failed primary target remains vacant. No reserve or surviving primary lifecycle may change target because of active-count change, hotspot deficit, service deficit, or rejoin. At rejoin, the new lifecycle is assigned the vacated primary target; all survivor and reserve targets remain unchanged. Only the common low-level safety/collision correction may alter the executed motion.

In NO_EVENT, same-information and no-reallocation target maps, raw actions, executed actions, physical trajectories, service outputs, and controller-owned state must be bitwise identical for every episode and step.

All exact ownership certificates must establish:

LEAVE occurs before action collection;
the absent lifecycle has no service action, actor row, likelihood, or policy-loss authority;
the physical slot remains present and holds position with zero velocity;
rejoin creates a new lifecycle epoch;
the new lifecycle inherits no old actor state or action-noise stream;
every survivor retains bitwise-identical physical state, control state, target ownership, and RNG ownership;
physical-slot permutation only permutes internal records;
world-space targets, actions, trajectories, and service remain invariant under the corresponding permutation.

G0_EXECUTABLE_ADDENDUM_METRICS

For episode e, control x, hotspot z, and physical step t, let r[x,e,u,t] be the delivered user rate recorded by the unchanged environment after applying the step-t action and event mask. Define:

rho_z[x,e,t]=(1/10)*sum_{u in hotspot z} 1[r[x,e,u,t]>=1.0 Mbps]

Define weakest-hotspot service:

S[x,e,t]=min(rho_0[x,e,t],rho_1[x,e,t],rho_2[x,e,t])

For an EVENT episode with onset O and duration D, define the integer event-plus-recovery window:

W[e]={O,O+1,...,O+D+59}

Define normalized weakest-hotspot deficit:

d[x,e,t]=max(0,0.90-S[x,e,t])/0.90

Define event service:

J_event[x,e]=1-(1/|W[e]|)*sum_{t in W[e]} d[x,e,t]

Define ordinary service:

Q_ordinary[x,e]=(1/(500-|W[e]|))*sum_{t not in W[e]} S[x,e,t]

Define event-window minimum service:

M_event[x,e]=min_{t in W[e]} S[x,e,t]

Define continuous episode access:

A_control[x,e]=min(J_event[x,e]/0.90,Q_ordinary[x,e]/0.90)

Define the episode-level binary access indicator:

B_access[x,e]=1[A_control[x,e]>=1]

Define catastrophic service loss:

C_cat[x,e]=1 if S[x,e,t]<0.60 for at least 10 consecutive integer steps inside W[e], and 0 otherwise.

For NO_EVENT, define:

J_event[x,e]=1
Q_ordinary[x,e]=(1/500)*sum_{t=0}^{499} S[x,e,t]
M_event[x,e]=min_{t=0}^{499} S[x,e,t]
A_control[x,e]=Q_ordinary[x,e]/0.90
B_access[x,e]=1[Q_ordinary[x,e]>=0.90]
C_cat[x,e]=0

For the EVENT cell, define episode-paired same-information minus no-reallocation effects:

Delta_A[e]=A_control[sameinfo,e]-A_control[no_reallocation,e]
Delta_J[e]=J_event[sameinfo,e]-J_event[no_reallocation,e]
Delta_M[e]=M_event[sameinfo,e]-M_event[no_reallocation,e]

All paired deltas use the same episode ID, geometry, event ledger, initial state, users, channel randomness, and non-controller source streams.

Existing external reward, total throughput, global thirty-user QoS, distance, collision telemetry, and action effort are secondary diagnostics only. None enters A_control, B_access, C_cat, Delta_J, Delta_M, or any first-match gate.

G0_EXECUTABLE_ADDENDUM_ESTIMATION

Controls are denoted:

O=mechanically_qualified_oracle
S=same_information_constructive
N=no_reallocation

Cells are denoted:

E=UNANNOUNCED_PRIMARY_TEMPORARY_LEAVE
Z=NO_EVENT

Use exactly 128 paired episode IDs, numbered 0 through 127. Every control and both cells use the same episode-ID ledger. There are no training seeds, learned models, optimizer replicates, checkpoints, or hierarchical seed levels.

For every continuous episode quantity X, estimate its population mean by:

hat_mu(X)=(1/128)*sum_{e=0}^{127} X[e]

For Delta_A, Delta_J, and Delta_M, X[e] is the paired episode-level difference before averaging.

Continuous confidence bounds use exactly 10,000 paired whole-episode bootstrap resamples. A resample draws 128 episode IDs with replacement and uses the same sampled ID sequence for every control, cell, and paired delta.

The bootstrap index generator is PCG64 with seed 2026072901. One 10000-by-128 index matrix is generated once and reused for all continuous estimands. Recreating different bootstrap indices for different controls or gates is forbidden.

For a continuous estimator, sort the 10,000 bootstrap means:

x_(1)<=x_(2)<=...<=x_(10000)

Define one-sided 95 percent percentile bounds without interpolation:

BS_L95(X)=x_(500)
BS_U95(X)=x_(9500)

Binary access and catastrophe probabilities do not use bootstrap bounds. For a binary variable Y with k=sum_e Y[e] successes among n=128 episodes, define the one-sided 95 percent Clopper-Pearson bounds:

CP_L95(k,n)=0, if k=0
CP_L95(k,n)=BetaInv(0.05;k,n-k+1), otherwise

CP_U95(k,n)=1, if k=n
CP_U95(k,n)=BetaInv(0.95;k+1,n-k), otherwise

For B_access, success means B_access=1. For C_cat, success means C_cat=1.

All first-match comparisons use the following statuses.

ORACLE_PASS holds if all are true:

BS_L95(A_control[O,E])>=1
BS_L95(A_control[O,Z])>=1
CP_L95(B_access[O,E])>=0.90
CP_L95(B_access[O,Z])>=0.90
the oracle qualification and physical-feasibility certificates pass

ORACLE_FAIL holds if at least one is true:

BS_U95(A_control[O,E])<1
BS_U95(A_control[O,Z])<1
CP_U95(B_access[O,E])<0.90
CP_U95(B_access[O,Z])<0.90
the passed oracle qualification certificate supplies an exact physical impossibility result for the frozen source

ORACLE_OPEN holds if neither ORACLE_PASS nor ORACLE_FAIL holds.

SAMEINFO_PASS holds if all are true:

BS_L95(A_control[S,E])>=1
BS_L95(A_control[S,Z])>=1
CP_L95(B_access[S,E])>=0.90
CP_L95(B_access[S,Z])>=0.90
CP_U95(C_cat[S,E])<=0.05

SAMEINFO_FAIL holds if at least one is true:

BS_U95(A_control[S,E])<1
BS_U95(A_control[S,Z])<1
CP_U95(B_access[S,E])<0.90
CP_U95(B_access[S,Z])<0.90
CP_L95(C_cat[S,E])>0.05

SAMEINFO_OPEN holds if neither SAMEINFO_PASS nor SAMEINFO_FAIL holds.

CAUSAL_PASS holds if all are true:

BS_U95(A_control[N,E])<1
CP_U95(B_access[N,E])<0.90
BS_L95(Delta_J)>0
hat_mu(Delta_M)>=0.10
BS_L95(Delta_M)>0.05

CAUSAL_FAIL holds if at least one is true:

BS_L95(A_control[N,E])>=1
CP_L95(B_access[N,E])>=0.90
BS_U95(Delta_J)<=0
hat_mu(Delta_M)<0.10
BS_U95(Delta_M)<=0.05

CAUSAL_OPEN holds if neither CAUSAL_PASS nor CAUSAL_FAIL holds.

VALID=1 only if every source-law, episode-count, geometry-support, RNG-independence, pairing, target-assignment, target-tracker, oracle-qualification, action-support, information-visibility, ownership, survivor-continuity, permutation, NO_EVENT identity, metric-arithmetic, row-completeness, and provenance certificate passes.

Any missing metric row, non-finite value, unqualified oracle failure, controller-dependent environment reseeding, future-ledger leakage, action-support mismatch, or certificate ambiguity sets VALID=0.

All equality conventions are frozen:

oracle and same-information access lower-bound equality passes;
binary access lower-bound equality at 0.90 passes;
catastrophe upper-bound equality at 0.05 passes;
no-reallocation continuous upper-bound equality at 1 does not pass CAUSAL_PASS;
no-reallocation binary upper-bound equality at 0.90 does not pass CAUSAL_PASS;
Delta_J requires a strictly positive lower bound;
Delta_M requires a point estimate at least 0.10 and a lower bound strictly above 0.05.

No confidence method, tail probability, bootstrap seed, quantile rule, threshold, or inequality direction may be changed after any behavioral row is read.

G0_EXECUTABLE_ADDENDUM_FIRST_MATCH_TABLE

Evaluate rows from priority 1 through priority 6 and stop at the first match.

+----------+----------------------------------+---------------------------------------------------------------+
| Priority | Outcome | Exact first-match condition |
+----------+----------------------------------+---------------------------------------------------------------+
| 1 | INVALID_UAV_G0_REALIZATION | VALID=0 |
| 2 | INFEASIBLE_UAV_G0_SOURCE | VALID=1 and ORACLE_FAIL |
| 3 | ORACLE_ONLY_UAV_G0_SOURCE | VALID=1 and ORACLE_PASS and SAMEINFO_FAIL |
| 4 | NON_CAUSAL_UAV_G0_SOURCE | VALID=1 and ORACLE_PASS and SAMEINFO_PASS and CAUSAL_FAIL |
| 5 | UNDERPOWERED_UAV_G0_SOURCE | VALID=1 and |
| | | (ORACLE_OPEN or |
| | | (ORACLE_PASS and SAMEINFO_OPEN) or |
| | | (ORACLE_PASS and SAMEINFO_PASS and CAUSAL_OPEN)) |
| 6 | IDENTIFIED_UAV_G0_SOURCE | VALID=1 and ORACLE_PASS and SAMEINFO_PASS and CAUSAL_PASS |
+----------+----------------------------------+---------------------------------------------------------------+

INVALID_UAV_G0_REALIZATION produces no scientific update. Only the realization defect may be repaired under this frozen contract.

INFEASIBLE_UAV_G0_SOURCE closes this exact clustered-hotspot and reserve-staging source. It does not reject any learned algorithm.

ORACLE_ONLY_UAV_G0_SOURCE means the source is feasible with event-ledger knowledge but is not established as online reachable under the registered unexpected current-information contract. Learned training is not admitted.

NON_CAUSAL_UAV_G0_SOURCE means online constructive access is established but roster-triggered spatial reallocation is not established as necessary. Learned training is not admitted.

UNDERPOWERED_UAV_G0_SOURCE does not identify the source. Increasing episode count requires a new precision-only review; source geometry, controls, estimands, and margins remain frozen.

IDENTIFIED_UAV_G0_SOURCE supports only the proposition that this fixed-eight-asset, three-hotspot, single-unannounced-temporary-LEAVE/rejoin source is physically feasible, online reachable, and causally dependent on roster-triggered spatial reallocation under the registered physics and information contract.

G0_EXECUTABLE_ADDENDUM_PROTECTED_FIELDS

physical_fleet_size=8
hotspot_count=3
users_per_hotspot=10
temporary_leave_count_per_event_episode=1
temporary_rejoin_count_per_event_episode=1
event_is_unannounced=true
detection_delay_steps=0
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

G0_EXECUTABLE_ADDENDUM_DISPOSITION
G0_EXECUTABLE_ADDENDUM_DISPOSITION=READY_FOR_CODE_CONTRACT