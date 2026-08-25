G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT
ASCII_ADDENDUM_BEGIN

SECTION_1_GEOMETRY_AND_SOURCE

1.1 Fixed physical source

physical_horizon_steps=500
physical_fleet_size=8
ground_users=30
ground_base_stations=1
per_user_target_rate_mbps=1.0
weakest_hotspot_service_floor=0.90
fixed_altitude=true
battery_enabled=false
charging_enabled=false
temporary_failure_process_enabled=false
terminal_loss_enabled=false
learning_enabled=false
optimizer_enabled=false
checkpoint_enabled=false

Let the rectangular horizontal map be:

MAP=[x_min,x_max] x [y_min,y_max]

Define:

map_width=x_max-x_min
map_height=y_max-y_min
b=((x_min+x_max)/2,(y_min+y_max)/2)
L=min(map_width,map_height)

The sole ground base station must have horizontal coordinate exactly b. Failure of that equality is INVALID_UAV_G0_REALIZATION.

Let h0 be the exact unchanged S7-S1 fixed altitude at the frozen evidence source. Every initial UAV position and every primary, staging, and gate target has altitude h0. Vertical target error is therefore zero, and no controller may select another altitude. Any S7-S1 altitude or fixed-altitude drift is INVALID_UAV_G0_REALIZATION.

Continuous motion support, velocity and acceleration limits, collision handling, backhaul safety, radio propagation, association, routing, link-capacity computation, and delivered-rate computation are the unchanged S7-S1 mechanisms. No G0-specific replacement physics or reward term is permitted.

1.2 Episode rotation and hotspot coordinates

For each episode e, sample exactly one independent value:

phi[e]~Uniform[0,2*pi)

For z in {0,1,2}, define:

theta[e,z]=phi[e]+2piz/3
u[e,z]=(cos(theta[e,z]),sin(theta[e,z]))
v[e,z]=(-sin(theta[e,z]),cos(theta[e,z]))
hotspot_center[e,z]=b+0.300Lu[e,z]

There are exactly three hotspots.

1.3 User coordinates

Let U_z be the fixed set of ten users assigned to hotspot z.

For every z in {0,1,2} and j in {0,...,9}, independently sample:

U_user[e,z,j]~Uniform[0,1)
V_user[e,z,j]~Uniform[0,1)

Define:

user_radius[e,z,j]=0.040Lsqrt(U_user[e,z,j])
user_angle[e,z,j]=2piV_user[e,z,j]

user_position[e,z,j]=
hotspot_center[e,z]
+user_radius[e,z,j]
*(cos(user_angle[e,z,j]),sin(user_angle[e,z,j]))

All thirty users remain stationary for the complete 500-step episode.

Hotspot membership and user-to-hotspot labels are environment metric authority only. They are not actor identity, target ownership, desired assignment, or tie-breaking information.

1.4 Primary, staging, and gate coordinates

For s in {-1,+1}, define the six primary service targets:

primary[e,z,s]=hotspot_center[e,z]+s0.040L*v[e,z]

Define the reserve-axis unit vector:

w[e]=(cos(phi[e]+pi/12),sin(phi[e]+pi/12))

Define the two reserve staging targets:

stage[e,s]=b+s0.050L*w[e]

Define the inward gate associated with each primary:

gate[e,z,s]=primary[e,z,s]-0.060Lu[e,z]

The eight nominal initial target labels are exactly:

primary[e,0,-1]
primary[e,0,+1]
primary[e,1,-1]
primary[e,1,+1]
primary[e,2,-1]
primary[e,2,+1]
stage[e,-1]
stage[e,+1]

No additional primary, reserve, staging, gate, or relay coordinate exists.

1.5 Initial UAV perturbations

For each of the eight nominal initial target labels q, independently sample:

U_uav[e,q]~Uniform[0,1)
V_uav[e,q]~Uniform[0,1)

Define:

uav_perturb_radius[e,q]=0.002Lsqrt(U_uav[e,q])
uav_perturb_angle[e,q]=2piV_uav[e,q]

uav_perturbation[e,q]=
uav_perturb_radius[e,q]
*(cos(uav_perturb_angle[e,q]),sin(uav_perturb_angle[e,q]))

Define the target-owned initial physical row:

initial_uav_position[e,q]=
(q_x+uav_perturbation[e,q]_x,
q_y+uav_perturbation[e,q]_y,
h0)

initial_uav_velocity[e,q]=(0,0,0)

All unlisted initial physical fields use the exact unchanged S7-S1 defaults.

No clipping, projection, rejection sampling, conditional redraw, favorable resampling, or result-dependent repair is permitted.

1.6 Geometry-support failure rule

Before behavioral evidence is admissible, the geometry certificate must prove that the complete support of all of the following lies inside MAP:

all three hotspot centers
all three radius-0.040L user disks
all six primary targets
all six radius-0.002L primary perturbation disks
both staging targets
both radius-0.002*L staging perturbation disks
all six gate targets

The support certificate is evaluated under every phi in [0,2*pi), not only the sampled phi.

Any support failure is INVALID_UAV_G0_REALIZATION. It may not be repaired by clipping, projection, rejection sampling, redrawing phi, redrawing a user, redrawing a UAV perturbation, or changing a normalization constant.

The frozen map-normalization constants are exactly:

hotspot_radius_from_b=0.300
user_disk_radius=0.040
primary_tangent_offset=0.040
reserve_stage_radius_from_b=0.050
inward_gate_offset=0.060
initial_uav_perturbation_radius=0.002

All constants multiply L=min(map_width,map_height).

1.7 Physical-slot permutation

After all target-owned initial rows are generated, sample one uniform permutation over all 8! mappings from target-owned rows to physical storage rows.

The permutation changes storage location only. It must not change:

world-space initial coordinates
nominal target coordinates
event-owner probabilities
controller target decisions
channel draw coordinates
channel draw blocks
world-space actions
physical trajectories
delivered service
metric rows

Physical storage row is never an actor feature, reserve-selection feature, candidate-ranking feature, or tie-breaking field.

1.8 Independent source namespaces and pairing

The following source variables use mutually independent RNG namespaces:

phi
user positions
initial UAV perturbations
physical-slot permutation
channel randomness
event owner
event onset
event duration

Controller name, control type, cell name, candidate identity, result branch, or observed performance may not reseed or advance a source namespace differently.

For each episode ID, all controls and both cells share the exact same:

phi
hotspot coordinates
user coordinates
nominal targets
initial perturbations
physical-slot permutation
channel ledger
event owner
event onset
event duration
all other non-event randomness

1.9 Event law

The sole event cell is:

E=UNANNOUNCED_PRIMARY_TEMPORARY_LEAVE

Exactly one event is sampled per E episode.

The event owner is uniform over the six current lifecycles that initially own primary targets. Owner sampling is target-owned and occurs after the storage permutation. Storage-row index is not owner-selection information.

Sample independently:

O[e]~DiscreteUniform{180,...,220}
D[e]~DiscreteUniform{80,...,100}

Define:

T_rejoin[e]=O[e]+D[e]

The affected lifecycle is service-active before step O[e].

LEAVE occurs before action collection at step O[e].

For every t in {O[e],...,O[e]+D[e]-1}, the affected physical asset:

remains present in its physical storage row
holds its position exactly
has velocity exactly zero
emits no communication service
emits no service-policy action
has no active actor row
has no action probability
has no policy-loss authority
is absent from the service-active roster

REJOIN occurs before action collection at step T_rejoin[e].

REJOIN preserves the current physical asset and physical state but creates a fresh lifecycle epoch in the same physical storage row.

The new epoch inherits neither old actor state nor the old action-noise stream.

Every unaffected survivor retains exactly its physical state, controller state, target ownership, lifecycle ownership, and RNG ownership.

announcement_lead_steps=0
detection_delay_steps=0

1.10 Paired no-event cell

The paired no-event cell is:

Z=NO_EVENT

Z retains the same sampled owner, O[e], D[e], geometry, initial state, storage permutation, channel ledger, and all non-event randomness as E.

Z disables only the service LEAVE and REJOIN lifecycle transition. The physical fleet remains eight and the service-active roster remains eight for all 500 steps.

SECTION_2_CONTROLS_ORACLE_AND_CERTIFICATES

2.1 Control names

O=mechanically_qualified_oracle
S=same_information_constructive
N=no_reallocation

All three controls are deterministic, evaluation-only controls.

They receive no learning, optimizer, checkpoint, training exposure, or result-dependent modification.

2.2 Anonymous initial target assignment

Let the eight current lifecycle rows be ordered canonically by the complete anonymous tuple:

(x,y,vx,vy)

using exact numeric ascending lexicographic order.

Let the eight nominal targets be ordered canonically by:

(target_x,target_y)

using exact numeric ascending lexicographic order.

Choose the assignment minimizing:

sum_i ||initial_uav_position_xy[i]-assigned_target_xy[i]||_2^2

If more than one assignment has the exact same minimum cost, choose the assignment whose sequence of assigned target-coordinate pairs is lexicographically smallest in canonical lifecycle-row order.

Physical storage row and lifecycle-epoch number are forbidden fallback keys.

If two distinct lifecycles are bitwise identical in every permitted anonymous row field and a distinct assignment remains necessary after the target-coordinate rule, the realization is invalid.

The assignment certificate must reconstruct exactly:

two primary owners for hotspot 0
two primary owners for hotspot 1
two primary owners for hotspot 2
one owner of stage[-1]
one owner of stage[+1]

Failure is INVALID_UAV_G0_REALIZATION.

2.3 Common deterministic target tracker

All three controls use one common deterministic target-to-action transducer.

The normative tracker is the byte-identical accepted-G1 deterministic target tracker, mechanically bound to evidence_source_commit:

45385faa81197bdb90c14f849eee17b999ca2f57

Its source identity is bound by the immutable accepted-G1 tracker source digest. The shared S7-S1 action-conversion, backhaul-safety, collision, and physical-transition methods are bound by their immutable shared-method digest.

No caller-supplied projection, controller-specific tolerance, controller-specific gain, controller-specific safety path, or controller-specific action conversion is permitted.

For active lifecycle i with current position p_i and target q_i, the accepted raw tracker uses the current target displacement and unchanged S7-S1 motion scales. Under the frozen fixed-altitude source its action has the form:

raw_action_i[0]=clip((q_i_x-p_i_x)/(max_speedtime_step),-1,1)
raw_action_i[1]=clip((q_i_y-p_i_y)/(max_speedtime_step),-1,1)
raw_action_i[2]=0
raw_action_i[3]=0

The qualification certificate must prove that this mathematical result is byte-identical to the accepted-G1 transducer output for every recorded target-tracker input.

Inactive lifecycles emit no action. Any dense storage representation must use an exact zero placeholder for inactive rows and must prove that the placeholder has no service, likelihood, or loss authority.

The executed action is the result of passing the raw action through the exact unchanged S7-S1 action conversion, backhaul safety guard, collision correction, action bounds, and physical transition path.

No post-transform clipping, alternate safety kernel, disabled guard, identity assumption, or post-hoc trajectory repair is permitted.

2.4 Target-tracker qualification certificate

Before any behavioral row is admissible, the common tracker certificate must prove:

the accepted-G1 tracker source digest matches
the shared S7-S1 action-method digest matches
same current-state bits plus same target-map bits produce byte-identical raw actions
same raw actions plus same complete guard inputs produce byte-identical executed actions
all raw and executed actions are within the unchanged action support
inactive lifecycles emit no action
fixed-altitude vertical actions are exactly zero
the fourth action coordinate is exactly zero
the same safety and collision path is used by O, S, and N
raw and executed actions are permutation-equivariant
no controller name, physical slot, lifecycle epoch, result, reward, or metric is read
all tracker and safety identities are frozen before behavioral rows

If the accepted-G1 tracker or exact shared S7-S1 correction cannot be isolated or qualified, VALID=0 and the first-match result is INVALID_UAV_G0_REALIZATION.

A replacement or tuned target tracker is prohibited.

2.5 Same-information constructive control

S may read only current information:

the current unordered active roster
current lifecycle ownership handles
current UAV positions and velocities
current service availability
current active count
current hotspot demand
current delivered-rate deficits
current channel and association state
current ground-BS geometry
current primary, staging, and gate coordinates

Opaque lifecycle handles may be used only to preserve target ownership.

S may not read:

future event owner
future event onset
future event duration
future rejoin time
future channel state
future association
future user service
future reward
future metric values
physical storage identity
lifecycle-epoch number as a decision feature
desired reserve identity supplied by the environment

Before LEAVE, every primary owner tracks its assigned primary and both reserve owners track their assigned staging targets.

At the first pre-action boundary with exactly seven service-active lifecycles:

exactly one primary target must be vacant
both reserve lifecycles must remain service-active

If either condition fails, the realization is invalid.

Let q_vacant be the vacant primary.

For each reserve r, define the selection tuple:

(
||current_position_xy[r]-q_vacant||_2^2,
current_x[r],
current_y[r],
current_vx[r],
current_vy[r],
original_stage_x[r],
original_stage_y[r]
)

Select the reserve with the lexicographically smallest tuple.

Physical storage row and lifecycle epoch are forbidden tie keys.

The selected reserve changes target to q_vacant before raw action construction at that first seven-active step.

Every unaffected primary owner and the unselected reserve retain their previous targets.

At REJOIN:

the fresh lifecycle is assigned q_vacant
the selected reserve changes target from q_vacant to the associated inward gate
all unaffected targets remain unchanged

The selected reserve remains at the gate until the causal RETURN_READY predicate first becomes true.

2.6 Causal RETURN_READY predicate

Let i_rejoin be the fresh lifecycle created at T_rejoin.

All lifecycle lookups must use:

lifecycle owner -> current target-owned internal row

A physical storage row may not index an internal-order lifecycle or safety record.

Define ACTIVE_AT_PRIMARY_PRE(i,t)=1 if and only if, at the pre-action boundary of step t:

lifecycle i is service-active
lifecycle i currently owns the registered vacant-primary target

No distance tolerance, smoothing, or storage-row shortcut is permitted.

Define COMPLETE_PRIMARY_STEP(i,t)=1 if and only if:

t>=T_rejoin+1
ACTIVE_AT_PRIMARY_PRE(i,t-1)=1
the executed service-active mask for completed step t-1 includes i
physical step t-1 completed
ACTIVE_AT_PRIMARY_PRE(i,t)=1

For t>=1, define the causal pre-action weakest-hotspot service:

S_pre(t)=min_z rho_z_after_completed_step(z,t-1)

where rho_z_after_completed_step(z,t-1) is computed from the delivered-rate row produced by completed physical step t-1.

No action, channel result, association result, delivered rate, reward, or service value produced at step t or later may enter S_pre(t).

Define:

RETURN_READY(t)=1

if and only if:

t>=T_rejoin+1
COMPLETE_PRIMARY_STEP(i_rejoin,t)=1
S_pre(t)>=0.90

Otherwise RETURN_READY(t)=0.

Define:

R=min{t: RETURN_READY(t)=1 at the pre-action boundary of step t}

If the set is empty, R=NONE.

There is no artificial delay, grace period, smoothing window, confirmation count, hysteresis, or first-differing-byte rule.

At R, the selected reserve changes target from the gate to its original staging target before raw action construction.

For all t<R, it retains the gate target.

For all t>=R, it retains the original staging target and may not return to the gate because of later service fluctuations.

The registered episode-0 fixture is:

episode_id=0
selected_candidate=stage/+1
event_onset=191
rejoin_step=272
S_pre(273)=1.0
return_ready_step=273
last_complete_cross_trace_identity_step=272
branchpoint_pre_action_step=273

Any stored or asserted episode-0 R other than 273 is invalid.

2.7 No-reallocation control

N receives the same current physical observation, active roster, active mask, current service information, current channel information, and geometry available to S.

N freezes every pre-event target ownership.

During LEAVE:

the failed primary remains vacant
no reserve changes target
no surviving primary changes target
active-count change does not change target ownership
hotspot deficit does not change target ownership
service deficit does not change target ownership

At REJOIN, the fresh lifecycle reacquires the failed owner's original primary target.

Every survivor and reserve retains its frozen target.

Only the common target tracker and unchanged low-level safety/collision correction may alter executed motion.

2.8 No-event target rules

In Z, S and N retain the initial six-primary/two-stage target map for all steps.

Their target maps, raw actions, executed actions, physical trajectories, service rows, and controller-owned states must be bitwise identical for all 500 steps.

The oracle receives the paired counterfactual owner, O, and D ledger and uses the same selected reserve and prebehavior target schedule as in E, while Z disables only the physical LEAVE/REJOIN transition.

Because no fresh rejoined lifecycle exists in Z, R=NONE for the oracle Z row and the selected reserve retains the post-O+D gate fallback.

This paired oracle-Z row tests whether the registered oracle motion and safety path can preserve no-event service without changing the event ledger or channel realization.

2.9 Oracle candidate set and schedule

The oracle candidate set is exactly:

candidate_minus=the lifecycle initially owning stage[-1]
candidate_plus=the lifecycle initially owning stage[+1]

K_search=2.

No unaffected primary owner is a candidate. Moving an unaffected primary would create another vacant primary and is outside the frozen one-reserve substitution source.

For candidate r, a mechanically qualified minimum common-tracker travel-step certificate determines n_gate[r], the minimum number of target-tracker steps required to reach the associated inward gate from the candidate's staging state under unchanged kinematics and action support.

The minimum-step certificate may read only:

current physical state
staging target
gate target
max_speed
time_step
fixed altitude
accepted common tracker

It may not read future service, reward, QoS, or G0 metrics.

Define:

latest_departure[r]=O-n_gate[r]

If latest_departure[r]<0, the oracle certificate fails.

The sealed prebehavior target schedule for candidate r is:

t<latest_departure[r]:
selected reserve target=stage[r]

latest_departure[r]<=t<O:
selected reserve target=gate

O<=t<O+D:
selected reserve target=vacant primary

t>=O+D:
selected reserve target=gate

All five unaffected primary owners retain their primary targets.

The failed primary owner retains its primary target before LEAVE, has no action while absent, and the fresh rejoined lifecycle owns that primary after REJOIN.

The unselected reserve retains its original staging target.

During prebehavior candidate generation:

PREBEHAVIOR_RETURN_READY=UNOBSERVED

The candidate may not predict, impute, synthesize, inspect, or rank by future RETURN_READY, future service, future reward, or future QoS.

2.10 Candidate ranking quantities

For candidate r, let p_pre[r,t] and p_post[r,t] be the selected reserve position immediately before and after the physical transition at step t in its sealed prebehavior trace.

Define:

violation_count[r]=
number of candidate steps with a hard physical violation,
safety violation, or real-guard safety deviation

Define gate_arrival_step[r] as the smallest pre-action step t satisfying:

latest_departure[r]<=t<=O
p_pre[r,t] is bitwise equal to gate

If no such step exists:

gate_arrival_step[r]=H+1

Define:

event_tracking_error[r]=
sum_{t=O}^{O+D-1}
||p_post_xy[r,t]-primary_xy||_2^2

Define:

path_length[r]=
sum_{t=0}^{H-1}
||p_post_xy[r,t]-p_pre_xy[r,t]||_2

Define the exact rank tuple:

(
violation_count[r],
gate_arrival_step[r],
event_tracking_error[r],
path_length[r],
original_stage_x[r],
original_stage_y[r]
)

The selected candidate is the lexicographically smallest rank tuple.

No service, reward, QoS, access, catastrophe, Delta, hotspot satisfaction, or result-branch quantity is a ranking key.

2.11 Shared immutable oracle safety ledger

For each episode ID, freeze one immutable shared oracle safety ledger before candidate ranking and before any behavioral service row exists.

Both candidates begin from byte-identical complete prestates except for candidate identity and the resulting candidate target schedule.

The complete prestate includes:

geometry
users
event ledger
physical-slot permutation
service-mask schedule
physical state
all environment RNG states
channel RNG state
all controller-independent state

Every use of channel randomness is assigned the immutable coordinate:

(
physical_step,
channel_update_ordinal,
rng_operation,
shape,
dtype
)

The ordered coordinate schema must be candidate-independent, action-independent, connection-independent, routing-independent, service-independent, and guard-independent.

Materialize one immutable channel draw tape.

At every corresponding coordinate, both candidates consume byte-identical channel draw blocks.

Candidate identity, action, position, connection result, routing result, guard intervention, service result, or metric result may not reseed, skip, redraw, or reorder the tape.

The target-schedule generator may not directly inspect:

channel draw blocks
connections
routing_paths
link capacities
guard outputs
future association
future delivered service
future reward
future QoS
G0 metrics

The safety subsystem may consume and seal only the fields needed to run and certify the real S7-S1 safety path:

physical_step
candidate_id
current_uav_positions
current_uav_velocities
current_service_mask
current_target_map
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
pre_action_context
common_transducer_evidence

The ranker may read only the five registered rank keys.

Channel and routing state may influence rank only indirectly through the real guarded trajectory and violation_count.

2.12 Required pre-action context

Every sealed safety step must contain an exact-schema pre_action_context binding:

all eight opaque lifecycle handles
all eight lifecycle epochs
the target-owned internal-row order
target ownership for every lifecycle
the event owner
the selected reserve owner
the unselected reserve owner
the five unaffected primary owners
the complete service-active mask
the explicitly empty controller-RNG inventory
content-addressed bindings to every environment RandomState in the immutable prestate
the fixed channel-tape coordinate state

The validator must reconstruct this context from the immutable source and common prestate.

Missing, stale, reordered, storage-indexed, caller-authored, or jointly tampered context is invalid.

2.13 Common transducer evidence per step

Every sealed step must bind:

current physical positions
current target map
current active mask
accepted-G1 tracker source identity
freshly recomputed raw tracker output
executed action mask
real guarded executed action

The validator must rerun the common transducer.

Attaching a stage-switch target schedule to unchanged gate-target raw actions is invalid unless the freshly recomputed accepted transducer independently produces those same raw-action bytes.

A coincident raw action at R is permitted only when the recomputed output is byte-identical. Candidate selection and R are determined by target identity and the causal predicate, not by the first differing action byte.

2.14 Oracle qualification certificate

ORACLE_CERT_PASS=1 only if all of the following hold:

exactly the two registered reserve candidates are present
both candidates start from the same qualified prestate
both candidates use the shared immutable channel tape
both candidates are advanced at most once through H steps
both candidates obey their exact target schedules
both candidates use the common accepted tracker
both candidates use the unchanged real S7-S1 safety and collision path
both candidate traces have complete guard-input evidence
both candidate traces have complete pre_action_context evidence
both candidate traces have complete common_transducer_evidence
both candidate traces are independently reproducible byte-for-byte
both candidates have violation_count=0
both candidates remain inside physical and action support
gate arrival and event tracking quantities are reconstructed from primitive rows
the selected candidate is the exact lexicographic winner
the five unaffected primary owners remain primary owners
the candidate generator has zero future-channel-selection reads
the candidate generator has zero future-service reads
the ranker has zero future-channel direct reads
the ranker has zero future-service reads
the candidate set is complete for the frozen one-reserve substitution source
candidate count is 2
candidate count is independent of H
candidate generation is O(H*K_search)
there is no nested rollout
there is no per-step replanning
there is no tree search
there is no beam search
there is no MCTS
there is no adaptive candidate creation
there is no post-result candidate regeneration
the selected behavioral branch passes branch-aware replay
ownership, survivor continuity, permutation, pairing, and provenance certificates pass

A stored passed flag or selected-candidate label cannot self-authorize the oracle. Every certificate field must be independently reconstructed.

2.15 Selected oracle behavioral branch

After the two sealed service-blind traces are ranked, freeze selected_candidate_id.

The selected behavioral E row uses:

the same selected candidate
the same initial state
the same target schedule before R
the same immutable channel tape
the same common target tracker
the same real S7-S1 guard
the same event ledger
the same lifecycle rules

For every t<R, its selected reserve target equals the sealed gate-hold target.

At R, before raw action construction, the behavioral target changes from gate to the selected reserve's original staging target.

For every t>=R, the behavioral target remains that staging target.

Current service may affect only this frozen gate-to-stage branch. It may not alter candidate ranking, selected_candidate_id, the channel ledger, or any prebehavior rank key.

2.16 Branch-aware replay certificate

Let:

P=sealed selected-candidate prebehavior fallback trace
B=selected-candidate behavioral trace

If R is an integer, P and B must agree byte-for-byte for every complete step t<R on:

physical_step
candidate_id
pre_action_context
current_uav_positions
current_uav_velocities
current_service_mask
current_target_map
common_transducer_evidence
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

Immediately before target selection and raw action construction at R, P and B must agree byte-for-byte on:

physical_step=R
selected_candidate_id
all lifecycle handles and epochs
target-owned internal-row mapping
current physical state
current service mask
event ownership
reserve ownership
all survivor ownership
all survivor controller state
all RNG ownership
all environment RNG states
shared channel coordinate state

The sole authorized initial semantic difference at R is:

P selected-reserve target=gate
B selected-reserve target=original_stage

For all t>=R, P and B must remain byte-identical on the shared exogenous ledger:

physical_step
selected_candidate_id
shared_channel_draw_coordinate
shared_channel_draw_block
event ledger
service-mask schedule
static user positions
static geometry
physical-slot permutation
RNG namespace ownership

For t>=R, cross-trace identity is not required for branch-endogenous fields:

current positions
current velocities
target-dependent raw actions
connections
routing_paths
guard-consumed link capacities
guard output
guarded actions
next positions
next velocities
delivered service

Instead:

P must independently self-replay byte-for-byte under its immutable gate-hold schedule.

B must independently self-replay byte-for-byte under the causal RETURN_READY stage-switch schedule.

The unchanged real S7-S1 guard must evaluate every P and B action.

If R=NONE, full P-versus-B byte identity is required for all 500 steps.

The first authorized divergence is the target change at causal R, even if the raw or guarded action bytes happen to remain equal at that step.

2.17 Oracle-certificate failure semantics

Any missing, incomplete, failed, inconsistent, or unreconstructable oracle qualification or branch-aware replay certificate sets:

VALID=0

and selects:

INVALID_UAV_G0_REALIZATION

This includes:

missing candidate
extra candidate
candidate-dependent reseeding
candidate-dependent channel draw schema
shared channel draw mismatch
unlogged guard input
future service visible during candidate generation or ranking
future reward or metric visible during candidate generation or ranking
changed or bypassed real guard
changed common tracker
safety deviation in a candidate trace
candidate reranking after service is visible
candidate regeneration after ranking
wrong lifecycle-owner/internal-row mapping
storage-row indexing of internal-order evidence
wrong RETURN_READY step
pre-R replay mismatch
branchpoint mismatch
post-R branch-local replay mismatch
ownership failure
survivor-continuity failure
permutation failure
pairing failure
provenance failure

When the oracle certificate is missing or fails, none of the following is admissible:

INFEASIBLE_UAV_G0_SOURCE
ORACLE_ONLY_UAV_G0_SOURCE
NON_CAUSAL_UAV_G0_SOURCE
UNDERPOWERED_UAV_G0_SOURCE
IDENTIFIED_UAV_G0_SOURCE

Certificate absence or failure may not be interpreted as physical infeasibility, online inaccessibility, causal failure, or statistical underpower.

Only a passed oracle qualification certificate may set an exact physical-impossibility flag.

SECTION_3_METRICS

3.1 Domains

Episode IDs:

e in EID={0,...,127}

Controls:

x in X={O,S,N}

Cells:

c in C={E,Z}

Physical steps:

t in T={0,...,499}

Hotspots:

z in {0,1,2}

Each hotspot user set U_z contains exactly ten users.

Let r[x,c,e,u,t] be the delivered rate in Mbps for user u after the unchanged environment applies the step-t action, event mask, association, routing, radio, and safety path.

3.2 Hotspot service

For every x, c, e, z, and t:

rho_z[x,c,e,t]=(1/10)*sum_{u in U_z} 1[r[x,c,e,u,t]>=1.0]

3.3 Weakest-hotspot service

For every x, c, e, and t:

S[x,c,e,t]=min_{z in {0,1,2}} rho_z[x,c,e,t]

3.4 Event window

For E episode e:

W[e]={O[e],O[e]+1,...,O[e]+D[e]+59}

Therefore:

|W[e]|=D[e]+60

Every W[e] lies completely inside T.

3.5 Normalized deficit

For every x, e, and t in W[e]:

d[x,e,t]=max(0,0.90-S[x,E,e,t])/0.90

3.6 Event service

For every x and E episode e:

J_event[x,E,e]=1-(1/|W[e]|)*sum_{t in W[e]} d[x,e,t]

For every x and Z episode e:

J_event[x,Z,e]=1

3.7 Ordinary service

For every x and E episode e:

Q_ordinary[x,E,e]=
(1/(500-|W[e]|))
*sum_{t in T and t not in W[e]} S[x,E,e,t]

For every x and Z episode e:

Q_ordinary[x,Z,e]=(1/500)*sum_{t=0}^{499} S[x,Z,e,t]

3.8 Event-window minimum service

For every x and E episode e:

M_event[x,E,e]=min_{t in W[e]} S[x,E,e,t]

For every x and Z episode e:

M_event[x,Z,e]=min_{t in T} S[x,Z,e,t]

3.9 Continuous access score

For every x and E episode e:

A_control[x,E,e]=
min(
J_event[x,E,e]/0.90,
Q_ordinary[x,E,e]/0.90
)

For every x and Z episode e:

A_control[x,Z,e]=Q_ordinary[x,Z,e]/0.90

3.10 Episode binary access indicator

For every x, c, and e:

B_access[x,c,e]=1[A_control[x,c,e]>=1]

3.11 Catastrophe

For every x and E episode e:

C_cat[x,E,e]=1

if and only if there exists an integer interval of at least ten consecutive steps wholly inside W[e] for which:

S[x,E,e,t]<0.60

at every step in that interval.

Otherwise:

C_cat[x,E,e]=0

For every x and Z episode e:

C_cat[x,Z,e]=0

3.12 Paired deltas

For each E episode e:

Delta_A[e]=A_control[S,E,e]-A_control[N,E,e]

Delta_J[e]=J_event[S,E,e]-J_event[N,E,e]

Delta_M[e]=M_event[S,E,e]-M_event[N,E,e]

Every paired delta uses the same episode ID, geometry, event ledger, initial state, users, channel ledger, and non-controller source streams.

3.13 Excluded diagnostics

External reward, total throughput, thirty-user global average QoS, distance, collision telemetry, action effort, and prior toy results are secondary diagnostics only.

They do not enter:

rho_z
S
J_event
Q_ordinary
M_event
A_control
B_access
C_cat
Delta_A
Delta_J
Delta_M
VALID
ORACLE status
SAMEINFO status
CAUSAL status
first-match selection

SECTION_4_ESTIMATION_CONFIDENCE_AND_STATUS

4.1 Episode inventory and pairing

Use exactly 128 episode IDs:

0,...,127

For each episode ID, require all six primitive traces in this exact inventory:

O,E
O,Z
S,E
S,Z
N,E
N,Z

No episode may substitute for another episode.

No time point is an independent sampling unit.

There are no training seeds, model seeds, optimizer replicates, checkpoint replicates, or hierarchical training levels.

4.2 Continuous point estimator

For every continuous episode quantity X[e], define:

hat_mu(X)=(1/128)*sum_{e=0}^{127} X[e]

For Delta_A, Delta_J, and Delta_M, compute the episode-paired difference first and then average the 128 differences.

4.3 Paired whole-episode bootstrap

Use exactly one generator:

numpy Generator(PCG64(2026072901))

Generate exactly one integer index matrix:

I shape=(10000,128)

with every I[b,j] sampled uniformly from {0,...,127} with replacement.

The same I is reused for every control, cell, continuous metric, and paired delta.

For bootstrap resample b:

hat_mu_b(X)=(1/128)*sum_{j=0}^{127} X[I[b,j]]

No resampling of individual time points, users, hotspots, or trace fragments is permitted.

No new bootstrap matrix may be generated for another gate.

4.4 Bootstrap quantile rule

Sort the 10,000 bootstrap estimates:

x_(1)<=x_(2)<=...<=x_(10000)

using one-based order-statistic notation.

Define without interpolation:

BS_L95(X)=x_(500)
BS_U95(X)=x_(9500)

Equivalently, zero-based array indices 499 and 9499 are used.

All continuous confidence gates use these bounds.

4.5 One-sided exact binomial bounds

For binary Y[e] with:

k=sum_{e=0}^{127} Y[e]
n=128

let BetaInv(p;a,b) be the p quantile of Beta(a,b).

Define:

CP_L95(k,n)=0 if k=0
CP_L95(k,n)=BetaInv(0.05;k,n-k+1) if k>0

CP_U95(k,n)=1 if k=n
CP_U95(k,n)=BetaInv(0.95;k+1,n-k) if k<n

B_access and C_cat use only these one-sided exact Clopper-Pearson bounds for their probability gates.

Bootstrap bounds do not replace binomial bounds for B_access or C_cat.

Binomial bounds do not replace bootstrap bounds for continuous A_control or paired continuous deltas.

4.6 Validity

VALID=1 only if every required certificate passes:

source-law certificate
episode-count certificate
geometry-support certificate
RNG-independence certificate
episode-pairing certificate
physical-slot permutation certificate
initial-target assignment certificate
physical-fleet/service-roster separation certificate
LEAVE timing certificate
REJOIN timing certificate
inactive-authority certificate
fresh-lifecycle certificate
survivor-continuity certificate
common-tracker certificate
action-support certificate
real-safety-path certificate
oracle safety-ledger certificate
oracle qualification certificate
branch-aware replay certificate
causal RETURN_READY certificate
lifecycle-owner/internal-row mapping certificate
same-information visibility certificate
no-reallocation visibility certificate
NO_EVENT S/N identity certificate
metric reconstruction certificate
row-completeness certificate
finite-value certificate
provenance certificate

Any missing row, non-finite value, caller-authored favorable summary, future-information leak, controller-dependent reseed, action mismatch, target mismatch, certificate ambiguity, or provenance mismatch sets VALID=0.

4.7 Oracle exact-impossibility precedence

Define ORACLE_IMPOSSIBLE=1 only when:

ORACLE_CERT_PASS=1

and the mechanically complete two-candidate certificate supplies an exact physical-impossibility conclusion under the frozen source, common tracker, real safety path, and candidate completeness proof.

A missing or failed oracle certificate sets VALID=0 and may not set ORACLE_IMPOSSIBLE.

ORACLE_IMPOSSIBLE has precedence over statistically favorable oracle rows.

4.8 ORACLE status

ORACLE_FAIL holds if VALID=1, ORACLE_CERT_PASS=1, and at least one of the following is true:

ORACLE_IMPOSSIBLE=1
BS_U95(A_control[O,E])<1
BS_U95(A_control[O,Z])<1
CP_U95(sum_e B_access[O,E,e],128)<0.90
CP_U95(sum_e B_access[O,Z,e],128)<0.90

ORACLE_PASS holds if VALID=1, ORACLE_CERT_PASS=1, ORACLE_IMPOSSIBLE=0, and all of the following are true:

BS_L95(A_control[O,E])>=1
BS_L95(A_control[O,Z])>=1
CP_L95(sum_e B_access[O,E,e],128)>=0.90
CP_L95(sum_e B_access[O,Z,e],128)>=0.90

ORACLE_OPEN holds if VALID=1, ORACLE_CERT_PASS=1, ORACLE_IMPOSSIBLE=0, and neither ORACLE_FAIL nor ORACLE_PASS holds.

4.9 SAMEINFO status

SAMEINFO_FAIL holds if VALID=1 and at least one of the following is true:

BS_U95(A_control[S,E])<1
BS_U95(A_control[S,Z])<1
CP_U95(sum_e B_access[S,E,e],128)<0.90
CP_U95(sum_e B_access[S,Z,e],128)<0.90
CP_L95(sum_e C_cat[S,E,e],128)>0.05

SAMEINFO_PASS holds if VALID=1 and all of the following are true:

BS_L95(A_control[S,E])>=1
BS_L95(A_control[S,Z])>=1
CP_L95(sum_e B_access[S,E,e],128)>=0.90
CP_L95(sum_e B_access[S,Z,e],128)>=0.90
CP_U95(sum_e C_cat[S,E,e],128)<=0.05

SAMEINFO_OPEN holds if VALID=1 and neither SAMEINFO_FAIL nor SAMEINFO_PASS holds.

4.10 CAUSAL status

CAUSAL_FAIL holds if VALID=1 and at least one of the following is true:

BS_L95(A_control[N,E])>=1
CP_L95(sum_e B_access[N,E,e],128)>=0.90
BS_U95(Delta_J)<=0
hat_mu(Delta_M)<0.10
BS_U95(Delta_M)<=0.05

CAUSAL_PASS holds if VALID=1 and all of the following are true:

BS_U95(A_control[N,E])<1
CP_U95(sum_e B_access[N,E,e],128)<0.90
BS_L95(Delta_J)>0
hat_mu(Delta_M)>=0.10
BS_L95(Delta_M)>0.05

CAUSAL_OPEN holds if VALID=1 and neither CAUSAL_FAIL nor CAUSAL_PASS holds.

4.11 Interval assignment by gate

The following use paired whole-episode bootstrap bounds:

A_control[O,E]
A_control[O,Z]
A_control[S,E]
A_control[S,Z]
A_control[N,E]
Delta_J
Delta_M

Delta_A is bootstrap-estimated and reported but is not a first-match gate.

J_event, Q_ordinary, and M_event for every control and cell are bootstrap-estimated and reported. Only the specific combinations named in ORACLE, SAMEINFO, and CAUSAL status definitions enter first-match selection.

The following use one-sided exact Clopper-Pearson bounds:

B_access[O,E]
B_access[O,Z]
B_access[S,E]
B_access[S,Z]
B_access[N,E]
C_cat[S,E]

4.12 Equality and strictness rules

The following equalities pass:

BS_L95(A_control[O,E])=1
BS_L95(A_control[O,Z])=1
BS_L95(A_control[S,E])=1
BS_L95(A_control[S,Z])=1
CP_L95(B_access probability)=0.90
CP_U95(C_cat[S,E] probability)=0.05
hat_mu(Delta_M)=0.10

The following require strict inequality:

BS_U95(A_control[N,E])<1
CP_U95(B_access[N,E] probability)<0.90
BS_L95(Delta_J)>0
BS_L95(Delta_M)>0.05

The following CAUSAL_FAIL boundaries are inclusive:

BS_L95(A_control[N,E])>=1
CP_L95(B_access[N,E] probability)>=0.90
BS_U95(Delta_J)<=0
hat_mu(Delta_M)<0.10
BS_U95(Delta_M)<=0.05

No confidence method, seed, quantile index, tail probability, threshold, inequality direction, or equality convention may change after any behavioral row is read.

SECTION_5_FIRST_MATCH_AND_PROTECTED_FIELDS

5.1 Stop-at-first-match rule

Evaluate priority rows from 1 through 6.

Stop immediately at the first matching row.

Do not evaluate, report, or use any lower-priority scientific branch after a higher-priority row matches.

+----------+----------------------------------+--------------------------------------------------------------------------+
| Priority | Outcome | Complete condition |
+----------+----------------------------------+--------------------------------------------------------------------------+
| 1 | INVALID_UAV_G0_REALIZATION | VALID=0; ORACLE, SAMEINFO, and CAUSAL statuses are not scientifically |
| | | evaluated. |
+----------+----------------------------------+--------------------------------------------------------------------------+
| 2 | INFEASIBLE_UAV_G0_SOURCE | VALID=1 AND ORACLE=FAIL; SAMEINFO and CAUSAL are not read. |
+----------+----------------------------------+--------------------------------------------------------------------------+
| 3 | ORACLE_ONLY_UAV_G0_SOURCE | VALID=1 AND ORACLE=PASS AND SAMEINFO=FAIL; CAUSAL is not read. |
+----------+----------------------------------+--------------------------------------------------------------------------+
| 4 | NON_CAUSAL_UAV_G0_SOURCE | VALID=1 AND ORACLE=PASS AND SAMEINFO=PASS AND CAUSAL=FAIL. |
+----------+----------------------------------+--------------------------------------------------------------------------+
| 5 | UNDERPOWERED_UAV_G0_SOURCE | VALID=1 AND (ORACLE=OPEN OR (ORACLE=PASS AND SAMEINFO=OPEN) OR |
| | | (ORACLE=PASS AND SAMEINFO=PASS AND CAUSAL=OPEN)). |
+----------+----------------------------------+--------------------------------------------------------------------------+
| 6 | IDENTIFIED_UAV_G0_SOURCE | VALID=1 AND ORACLE=PASS AND SAMEINFO=PASS AND CAUSAL=PASS. |
+----------+----------------------------------+--------------------------------------------------------------------------+

5.2 Result meanings

INVALID_UAV_G0_REALIZATION produces no scientific update. Only the realization defect may be repaired under the frozen contract.

INFEASIBLE_UAV_G0_SOURCE closes only this exact clustered-hotspot and reserve-staging source. It does not reject a learned algorithm.

ORACLE_ONLY_UAV_G0_SOURCE means the source is feasible with registered oracle information but is not established as reachable under the current-information unexpected-event contract. Learned training is not admitted.

NON_CAUSAL_UAV_G0_SOURCE means same-information access is established but roster-triggered spatial reallocation is not established as necessary. Learned training is not admitted.

UNDERPOWERED_UAV_G0_SOURCE does not identify the source. Any episode-count increase requires a new precision-only clarification. Geometry, controls, metrics, margins, and confidence rules remain frozen.

IDENTIFIED_UAV_G0_SOURCE supports only this proposition:

The fixed-eight-asset, three-hotspot, single-unannounced-temporary-LEAVE/rejoin source is physically feasible, online reachable under the registered current-information contract, and causally dependent on roster-triggered spatial reallocation under the registered physics, safety, pairing, and inference rules.

It does not support:

learned-policy access
G49 UAV transport
roster-native superiority over fixed masking
variable-team-size generalization
charging rotation
terminal loss
replacement
repeated rejoin robustness
count-shock robustness
held-out process-law generalization
real-time deployment
UAV system robustness
safety certification
paper acceptance

5.3 Required protected-fields string

physical_fleet_8|three_hotspots|single_unannounced_temporary_leave_rejoin|no_learning|no_optimizer|no_checkpoint|128_paired_episode_ids|10000_bootstrap|ownership_and_permutation_certificates|O(H*K_search)_K_search_le_16|no_G51_merge

5.4 Additional frozen fields

physical_horizon_steps=500
ground_users=30
ground_base_stations=1
users_per_hotspot=10
event_cell_count=1
no_event_cell_count=1
event_owner_support=six_primary_lifecycles
event_onset_support=180_to_220_inclusive
event_duration_support=80_to_100_inclusive
announcement_lead_steps=0
detection_delay_steps=0
leave_timing=before_action_collection
rejoin_timing=before_action_collection_at_O_plus_D
rejoin_epoch=fresh
old_actor_state_inheritance=false
old_action_rng_inheritance=false
paired_episode_ids=128
episode_id_support=0_to_127_inclusive
bootstrap_resamples=10000
bootstrap_generator=PCG64
bootstrap_seed=2026072901
bootstrap_lower_order_statistic=500
bootstrap_upper_order_statistic=9500
binomial_interval=one_sided_95_percent_Clopper_Pearson
ownership_certificate=required_exact
permutation_certificate=required_exact
survivor_continuity_certificate=required_exact
no_event_identity_certificate=required_bitwise
common_tracker_certificate=required_exact
oracle_safety_ledger=required_immutable
oracle_candidate_count=2
K_search=2
K_search_ceiling=16
candidate_count_independent_of_H=true
hypothetical_candidate_transitions_ceiling=2H
evidence_search_complexity=O(HK_search)
nested_rollout_replanning=false
per_step_candidate_replanning=false
adaptive_candidate_creation=false
tree_search=false
beam_search=false
MCTS=false
candidate_reranking_after_behavior=false
candidate_regeneration_after_behavior=false
oracle_candidate_generation_service_visibility=false
oracle_candidate_ranking_service_visibility=false
oracle_runtime_current_service_visibility=RETURN_READY_only
prebehavior_RETURN_READY=UNOBSERVED
return_ready_artificial_delay_steps=0
return_ready_service_threshold=0.90
return_ready_required_completed_primary_steps=1
return_ready_owner_mapping=lifecycle_owner_to_internal_order
storage_row_as_internal_order_index=false
episode_0_return_ready_step=273
runtime_real_guard=required_every_step
post_R_cross_trace_endogenous_identity=not_required
post_R_branch_local_identity=required_bytewise
learning_enabled=false
learned_model_count=0
optimizer_enabled=false
optimizer_update_count=0
checkpoint_enabled=false
checkpoint_count=0
G51_merge=false
formal_execution_authorized=false
nonformal_scientific_execution_authorized=false
code_acceptance=false
paper_acceptance=false
claim_scope=SOURCE_IDENTIFIABILITY_G0_ONLY
scientific_iteration_cost=0

ASCII_ADDENDUM_END
