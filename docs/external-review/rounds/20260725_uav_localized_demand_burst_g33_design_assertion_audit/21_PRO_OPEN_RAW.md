1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=UNRESOLVED_UAV_BURST_G33_DESIGN

The localized-demand-burst family is not rejected, but the present evidence is insufficient to freeze it as an identifiable conclusion-bearing source.

The exact unresolved unit is:

There is no accepted executable upper bound excluding all relevant future-blind static or prepositioning policies from attaining the proposed burst-access floor.

A single NO_REALLOCATION controller would reject only one frozen pre-burst layout. It would not exclude:

a broadly dispersed static deployment;

a policy that prepositions before the burst using elapsed-time hazard;

a fixed layout optimized for all registered hotspot locations;

automatic reassociation or routing changes at unchanged UAV positions;

a policy that satisfies burst users by sacrificing ordinary users.

The project’s design-audit rule requires both a positive witness and a counterexample-resistant necessity argument before a conclusion-bearing source is frozen. A positive control that merely permits spatial reallocation is insufficient if another access-level solution can avoid it.

This caution is decision-relevant rather than procedural. Both previous UAV sources completed valid source screens but stopped before learned training because their constructive controls did not establish the intended source:

temporary-loss G1 had constructive J_event CI95 [0.8481, 0.8566, 0.8652], below its feasibility floor, and constructive-minus-no-reallocation was entirely negative;

the charge-rotation source also remained source-non-identifiable despite proactive rotation being load-bearing, because its constructive controller did not establish the absolute source contract.

Therefore:

IDENTIFIABLE_UAV_BURST_G33_DESIGN is not yet justified;

NON_IDENTIFIABLE_UAV_BURST_G33_DESIGN would be premature because the exact candidate below has not undergone a source-only witness audit;

the correct disposition is UNRESOLVED_UAV_BURST_G33_DESIGN.

The exact candidate below is frozen only as the sole object for the next source-witness audit. It is not yet an admitted learner benchmark.

2. EXACT_SOURCE_CONTRACT
2.1 Candidate identity
candidate_id=UAV_LOCALIZED_DEMAND_BURST_G33_P0
base_preset=S7-S1
physical_uavs=8
service_roster=constant_8
episode_steps=500
battery=false
charging=false
temporary_failure=false
ordinary_per_user_demand=1.0_Mbps
existing_external_reward_form=preserved
intrinsic_reward_change=forbidden

S7-S1 already fixes eight UAVs, thirty users, one ground base station, a 500-step episode, a 1 Mbps ordinary QoS target and a 0.90 team QoS target, with battery, charging and failure disabled.

The service roster remains exactly eight throughout the episode. G33 can test UAV control transport and spatial service reallocation; it cannot support a variable-membership claim.

2.2 Per-user offered demand and delivered service

Let the ordinary demand be:

q
0
	​

=10
6
 bps.

For user u, define the current offered demand and QoS target:

q
u
	​

(t)={
Mq
0
	​

,
q
0
	​

,
	​

u∈A, O≤t<O+D,
otherwise.
	​


Here:

O is burst onset;

D is burst duration;

M is the demand multiplier;

A is the affected user cohort selected at onset and held fixed until burst end.

Let C
u
	​

(t) be the end-to-end capacity already computed by Scenario 7. Define realized delivered traffic:

Y
u
	​

(t)=min(C
u
	​

(t),q
u
	​

(t)),

and per-user satisfaction:

s
u
	​

(t)=
q
u
	​

(t)
Y
u
	​

(t)
	​

=clip(
q
u
	​

(t)
C
u
	​

(t)
	​

,0,1).

The current Scenario-7 code already calculates satisfaction as clipped delivered rate divided by a scalar 1 Mbps target. G33 replaces that scalar by the current per-user vector q(t); it does not add a new reward component.

The underlying communication system remains unchanged:

association remains based on the current connection logic;

FDMA access bandwidth remains divided by physical UAV count and connected-user count;

access capacity remains determined by SINR and MCS;

per-UAV access capacity remains backhaul-scaled;

a user’s delivered capacity remains the best delivered UAV rate rather than a sum over UAVs.

Consequently, the burst changes the offered load and required service rate, not propagation, interference, connection selection, bandwidth allocation or routing. The packet simulator remains diagnostic and is not a conclusion-bearing burst mechanism.

2.3 External reward identity

Define the task utility:

ρ
t
	​

=
30
1
	​

u=1
∑
30
	​

s
u
	​

(t).

The existing Scenario-7 external reward remains:

r
t
	​

=ρ
t
	​

+γΦ
t+1
	​

−Φ
t
	​

,

with the existing terminal PBRS boundary. No burst bonus, hotspot reward, movement reward, assignment reward or reallocation reward is added.

The existing graph potential must use the same current vector q(t) in every per-user normalization. Leaving the graph potential at a fixed 1 Mbps denominator while the task utility uses q
u
	​

(t) would create a mismatched objective. The present implementation uses the same scalar QoS denominator in both task utility and graph potential, so the source-specific vector substitution must be applied consistently to both.

Since S7-S1 has no battery or charging, the return-risk, cutoff and depletion components remain inactive. The source does not alter reward weights or safety coefficients.

2.4 Exact burst profiles

The candidate uses one burst per disturbed episode.

Cell	Onset O	Duration D	Center law	Affected cohort	Multiplier M
NO_BURST	none	none	none	none	1.0
IID_BURST	discrete uniform 140..260	discrete uniform 40..80	uniform over all 30 users at onset	center plus its 7 nearest users, total 8	1.5 or 2.0, equiprobable
EARLY_LONG	discrete uniform 60..120	discrete uniform 90..120	uniform over all 30 users at onset	center plus its 9 nearest users, total 10	2.25
REMOTE_STRONG	discrete uniform 180..260	discrete uniform 70..110	uniform over the 8 users in the farthest spatial quartile from the ground BS at onset	center plus its 9 nearest users, total 10	2.50

These values preserve the previously proposed burst family while making its use conditional on the source-witness audit.

Selection details are exact:

all distances are horizontal Euclidean distances at the pre-action onset boundary;

the affected cohort is frozen at onset even though users continue moving;

distance ties are broken by physical user index in the environment ledger;

“farthest quartile” means the eight users with greatest horizontal distance to the nearest ground base station, with ledger-index tie breaking;

the burst begins before the action at step O;

ordinary demand resumes before the action at step O+D;

the recovery window is the sixty steps [O+D,O+D+60).

All registered recovery windows end before step 500.

2.5 RNG ownership

Use independent episode-addressed namespaces for:

burst onset;

burst duration;

multiplier;

center user;

ordinary user initialization and motion;

UAV and base-station initialization;

channel/environment state;

policy action noise;

control counterfactuals.

Every control and later learned arm receives the same episode ledger, user trajectory, channel realization and initial physical state. No burst draw may advance the user-motion, channel or action RNG.

2.6 Candidate closure rule

UAV_LOCALIZED_DEMAND_BURST_G33_P0 is one immutable candidate:

no post-witness multiplier change;

no duration or onset expansion;

no affected-cohort resize;

no reward or observation rescue;

no additional seeds to reverse a valid source conclusion.

If P0 is confidently non-identifiable, that exact candidate closes. A different burst law would require another scientific decision rather than being called a repair.

3. INFORMATION_AND_LEAKAGE
3.1 Actor information

The existing S7 actor’s local user record contains relative position, SINR, connection-to-self and serviced-by-any status, but no demand field. It also includes normalized physical time.

For G33, every visible local-user record becomes:

relative_x
relative_y
normalized_sinr
connected_to_self
serviced_by_any
normalized_current_demand
visibility_flag

where:

q
	​

u
	​

(t)=clip(
1.5
q
u
	​

(t)/q
0
	​

−1
	​

,0,1).

Thus:

ordinary demand maps to 0;

multiplier 1.5 maps to 1/3;

2.0 maps to 2/3;

2.25 maps to 5/6;

2.50 maps to 1.

The field is present only for users currently visible through the unchanged local-user observation rule. Padded user rows are all zero, including visibility_flag=0.

User rows are ordered by current physical content:

(distance, relative_x, relative_y, normalized_current_demand)

rather than by a user identifier. Exact duplicate rows are exchangeable.

The existing normalized physical-time field is removed from the G33 actor observation. No replacement burst clock is added.

3.2 Team observability predicate

For every disturbed episode, at the onset boundary:

∀u∈A,∃i∈{1,…,8} such that user u appears in UAV i’s current user records.

If any affected user is collectively unobserved at onset, that episode violates the source-information contract. The source screen must fail rather than attributing the resulting no-access to a learner.

This keeps demand sensing local while ensuring the team collectively receives the complete current burst demand.

3.3 Critic information

The current critic state already includes UAV positions and loads, per-user positions, velocities, connection status and best SINR, plus normalized physical time; it contains no demand vector.

The G33 critic receives:

the unchanged current physical network state;

the current per-user normalized demand paired with each current user record;

no normalized physical time;

no future burst variables.

The critic’s additional demand field is current task state, not an actor assignment or future oracle.

3.4 Prohibited information

Neither actor nor critic may receive:

future onset or burst-end time;

remaining burst duration;

future multiplier;

future affected cohort;

future user position or channel state;

burst center identity;

a demand-weighted centroid supplied as a separate field;

desired UAV-to-user assignment;

designated “burst UAV,” “relay UAV” or role label;

burst success, deficit, progress or recovery status;

external reward as an input;

stable UAV or user identity embedding.

A current nonordinary demand field necessarily reveals that a burst is active. It does not reveal which UAV should serve it.

3.5 Leakage-sensitive source probes

Before any learner is eligible, the source must establish exact equality under a fixed physical snapshot:

changing q(t) changes neither raw access capacity, raw backhaul capacity, connection matrix, routing path nor physical transition;

changing q(t) changes only:

admitted delivered traffic Y
u
	​

;

user satisfaction s
u
	​

;

task utility ρ
t
	​

;

the existing demand-normalized graph potential;

current demand observation fields;

no future ledger field is present in actor or critic tensors;

permuting physical user indices while preserving current physical records and demand values leaves anonymous actor inputs equivalent.

4. OPTIMAL_POLICY_NECESSITY_AND_COUNTEREXAMPLES
4.1 Relevant policy and behavior sets

Let Π
causal
	​

 be the set of policies measurable only with respect to the permitted current observation history.

Let Π
access
	​

⊆Π
causal
	​

 contain policies that satisfy every registered access and ordinary-service guardrail.

Define Π
static
	​

 as policies that may move before onset but, after observing the onset demand, do not change their physical target layout through the burst and recovery window.

The intended strong necessity claim would be:

π∈Π
static
	​

sup
	​

A(π)<1.

No allowed evidence currently proves this inequality.

4.2 Policy-specific motion mediation

For a particular controller or later learned policy π, define a paired onset-snapshot intervention:

natural branch: execute π normally;

motion-suppressed branch: execute the same policy and update its recurrent state, but replace all three UAV movement components by zero during burst and recovery;

keep user motion, channel state, connection/routing recomputation and every RNG draw paired.

This intervention distinguishes physical movement from automatic reassociation and routing changes.

A policy-specific reallocation claim requires:

A(π)≥1,
UCB
95
	​

(A(π
motionless
))<1,

and:

LCB
95
	​

(J
burst
	​

(π)−J
burst
	​

(π
motionless
))>0.10.

This establishes that that policy’s access depends on post-onset physical movement. It does not prove that every access-level policy must move.

4.3 Live causal explanations
A. Online spatial reallocation is genuinely load-bearing

Mechanism:

current localized demand
→ demand-responsive movement
→ altered access/backhaul geometry
→ higher affected-user delivered rate
→ burst and recovery access

Evidence that would raise it:

future-blind constructive access;

no-reallocation failure;

motion-suppressed failure;

ordinary-user guardrails;

later natural learned-policy mediation.

B. Broad static placement or prepositioning is sufficient

A policy may distribute UAVs so widely that all registered eight- or ten-user hotspots already meet the higher targets. It may also exploit the known onset support through recurrent step counting even after explicit time is removed.

Evidence that would raise it:

a full-ledger static target layout passes access;

no-reallocation or another nonadaptive control passes one or more burst profiles;

learned access survives motion suppression.

C. Automatic association and routing, rather than UAV movement, supplies the response

Current connections and widest-path routing are recomputed every physical step. A demand change can alter the utility of the unchanged topology even while user motion and automatic connection changes continue. If motion-suppressed access passes, the benchmark cannot identify spatial reallocation.

D. The source is inaccessible under current information or physics

The elevated target may be unreachable even under optimal legal motion, or the local observation contract may reveal the demand too late. A full-ledger oracle failure or a future-blind constructive failure would update the source, not G31/G32.

4.4 Additional concrete counterexamples

Ordinary-user sacrifice

A policy may move most UAVs toward affected users, raise affected-user satisfaction and collapse unaffected service. This is excluded only if unaffected and ordinary-service guardrails are conclusion-bearing.

Fixed hotspot memorization

A fixed spatial hotspot or a center correlated with the base station can be solved by a static layout. Hence center location must remain episode-random and held-out profiles must change its spatial distribution.

Actor assignment leakage

A global demand centroid, chosen-UAV field or stable user ordering could effectively tell the policy where or whom to serve.

Reward-only response

A score can change immediately when q
u
	​

 changes even though raw rates and positions do not. A utility difference alone is therefore not evidence of reallocation.

Graph-PBRS reduction

The existing graph potential can provide dense, current-demand-sensitive feedback. A later successful learner may be explained by ordinary recurrent PPO rather than G31’s realized-future-tail credit. The matched null must remain.

4.5 Bounded necessity options

Only two scientifically coherent claim forms remain:

N1_UNIVERSAL_REALLOCATION_NECESSITY

Claim:

π∈Π
static
	​

sup
	​

A(π)<1.

Requirement:

An executable upper bound covering the entire declared static/prepositioning policy class.

Status: unresolved.

N2_POLICY_MEDIATED_REALLOCATION

Claim:

A named current-only constructive controller or learned policy accesses P0, while its own no-reallocation and motion-suppressed continuations do not.

Requirement:

The paired intervention gates above.

Status: potentially identifiable, but materially narrower. It cannot be silently substituted for N1.

The next boundary will first attempt N1. If a complete upper bound cannot be supplied, a later Pro decision must explicitly narrow the claim to N2; Project Manager cannot make that change locally.

4.6 Strongest ordinary-MARL reduction

The strongest ordinary reduction is:

DIRECT_REC_GAE

It uses:

the same current actor and critic information;

the same capacity-generic continuous recurrent policy;

the same tanh-Gaussian action support;

the same parameter count;

the same environment interactions and PPO passes;

ordinary full-reward GAE;

no future-tail direction-balancing treatment.

The G31/G32 arm differs only by its registered realized-future-tail and direction-balanced credit path. G31 computes a detached discounted future return excluding the current reward; that mechanism remains source-neutral.

The source can establish UAV access even if DIRECT_REC_GAE is sufficient. It supports a G31-specific transport claim only if the matched ordinary null is separated after source identification.

5. CONTROLS_AND_MATCHED_NULL
5.1 Shared deterministic layout library

The following finite library is used by all scripted layout controls:

relay count:

r∈{1,2,3};

common altitude:

h∈{z
min
	​

,
2
z
min
	​

+z
max
	​

	​

,z
max
	​

};

service centroids:

deterministic demand-weighted k-means over current user positions;

k=8−r;

farthest-point deterministic initialization;

at most 30 iterations;

relay positions:

equally spaced on the line from the mean ground-BS position to the demand-weighted service-centroid mean;

UAV-to-slot assignment:

Hungarian minimum current travel distance;

candidate scoring:

exact current relaxed end-to-end service potential using the current q(t);

ties:

relay count, altitude and lexicographic target coordinates.

All UAV movement toward selected targets uses the unchanged legal continuous action and speed limits.

This library is a control definition, not a learned skill catalogue.

5.2 Controls
Control	Information	Behavior	Scientific role
FULL_LEDGER_REACHABILITY_ORACLE	Complete burst ledger and future user trajectory; current and future physical state under its own legal actions	May preposition before onset; at every step selects from the shared layout library using the complete remaining ledger	Physical/source reachability only
CURRENT_ONLY_ADAPTIVE_CONSTRUCTIVE	Full current physical state and current demand; no future burst or user/channel state	Recomputes the shared layout at every pre-action boundary and legally tracks current targets	Future-blind constructive access
NO_REALLOCATION	Same current information as constructive	Executes exactly the same actions as constructive before onset; at onset freezes the current target-slot assignment until recovery ends	Registered adaptive-versus-fixed contrast
MOTION_SUPPRESSED_CONTINUATION	Same policy state and observations as its parent branch	From onset through recovery, replaces movement components by zero; automatic user motion, channel, association and routing continue	Tests whether physical movement mediates value
STATIC_FULL_LEDGER_PREPOSITION	Complete burst ledger before onset	May legally preposition before onset using the shared library; target layout is frozen from onset through recovery	Strong counterexample to calendar/static claims within the registered layout family
NO_BURST_CONTROL	Ordinary current information	Same controller on paired no-burst ledger	Ordinary-service guardrail

None trains a model or receives optimizer exposure.

The common-action requirement for constructive and no-reallocation follows the useful control pattern already established in the charge source: both share the same initial targets and differ only at the registered intervention boundary.

5.3 Limit of the static control

STATIC_FULL_LEDGER_PREPOSITION is stronger than any future-blind static policy within the shared finite layout library because it knows the complete burst ledger.

However, its failure would not upper-bound arbitrary continuous static trajectories outside that library. Consequently:

its success is a decisive counterexample to N1;

its failure is necessary but not sufficient to prove N1.

A complete N1 audit must additionally provide either:

an exact global upper bound over the declared continuous static policy class; or

an explicit restriction of Π
static
	​

 to a finite class accepted as the scientific claim domain.

5.4 Later matched learned arms

Only after source identification may a learned comparison be frozen:

arm_1=DIRECT_REC_GAE
arm_2=G31_G32_RTG_DIRECTION_BALANCED

They must share:

current observations;

critic state;

model and hidden dimensions;

capacity-8 packing;

action distribution;

initial weights;

environment and burst ledgers;

environment interactions;

total actor and critic optimizer steps;

final-checkpoint-only selection;

deterministic and stochastic evaluation seeds.

NO_REALLOCATION is not a learned comparator. It is a source control.

The currently accepted continuous policy uses shared member encoding, active-set summation, log1p(active_count), lifecycle recurrence and normalized autoregressive prefixes. Those elements may be reused, but the existing toy evidence does not itself constitute UAV transport.

6. ESTIMANDS_GATES_AND_CONFIDENCE
6.1 Time windows

For a disturbed episode:

B=[O,O+D)

is the burst window,

R=[O+D,O+D+60)

is the recovery window, and

N=[0,O)∪[O+D+60,500)

is the ordinary window.

All are nonempty under P0.

6.2 Cohort-specific service

For affected cohort A:

ρ
t
A
	​

=
∣A∣
1
	​

u∈A
∑
	​

s
u
	​

(t).

For unaffected users:

ρ
t
U
	​

=
30−∣A∣
1
	​

u∈
/
A
∑
	​

s
u
	​

(t).

Whole-team utility remains:

ρ
t
	​

=
30
1
	​

u=1
∑
30
	​

s
u
	​

(t).
6.3 Deficit-normalized window score

For nonempty window X and service trace r
t
	​

, define:

J(X,r)=1−
∣X∣
1
	​

t∈X
∑
	​

0.90
max(0,0.90−r
t
	​

)
	​

.

Conclusion-bearing quantities are:

J
burst
	​

=J(B,ρ
A
),
J
recovery
	​

=J(R,ρ
A
),
Q
unaffected
	​

=
∣B∪R∣
1
	​

t∈B∪R
∑
	​

ρ
t
U
	​

,
Q
ordinary
	​

=
∣N∣
1
	​

t∈N
∑
	​

ρ
t
	​

.

For NO_BURST:

Q
no-burst
	​

=
500
1
	​

t=0
∑
499
	​

ρ
t
	​

.
6.4 Access score

For controller or later arm a and disturbed cell c:

A
a,c
	​

=min(
0.80
J
burst,a,c
	​

	​

,
0.80
J
recovery,a,c
	​

	​

,
0.90
Q
unaffected,a,c
	​

	​

,
0.90
Q
ordinary,a,c
	​

	​

).

For NO_BURST:

A
a,ordinary
	​

=
0.90
Q
no-burst,a
	​

	​

.

Equality at any floor passes.

6.5 Source-witness gates

For every one of IID_BURST, EARLY_LONG and REMOTE_STRONG:

Physical reachability
LCB
95
	​

(A
FULL_LEDGER
	​

)≥1.
Causal-information constructive access
LCB
95
	​

(A
CURRENT_ONLY
	​

)≥1.
No-reallocation failure
UCB
95
	​

(A
NO_REALLOCATION
	​

)<1,

and:

LCB
95
	​

(J
burst,CURRENT_ONLY
	​

−J
burst,NO_REALLOCATION
	​

)>0.10.
Movement mediation
UCB
95
	​

(A
MOTIONLESS
	​

)<1,

and:

LCB
95
	​

(J
burst,CURRENT_ONLY
	​

−J
burst,MOTIONLESS
	​

)>0.10.
Ordinary access
LCB
95
	​

(A
CURRENT_ONLY,ordinary
	​

)≥1.
Static-preposition counterexample

If:

LCB
95
	​

(A
STATIC_FULL_LEDGER
	​

)≥1,

N1 is refuted for P0.

A finite-library static failure does not by itself prove N1.

6.6 Structural source gates

Every source-witness episode must satisfy:

exact onset, duration, center, cohort and multiplier law;

exact demand/reward identity;

raw physical-capacity invariance under demand-only intervention;

complete affected-user collective visibility at onset;

no future or assignment leakage;

common pre-onset actions for constructive and no-reallocation;

exact paired onset snapshots;

complete recovery window;

finite nonzero denominators;

no source-control training or optimizer step.

6.7 Confidence construction

The source-only witness package uses:

replicate_namespaces=3
episode_ledgers_per_profile_per_replicate=128
profiles=NO_BURST|IID_BURST|EARLY_LONG|REMOTE_STRONG
bootstrap_resamples=10000
optimizer_steps=0
learned_models=0

Bootstrap procedure:

resample the three replicate namespaces;

within each selected replicate, resample whole episode IDs;

retain all controls, onset snapshots and counterfactual branches belonging to that episode;

never resample users, UAVs, time rows or counterfactual branches independently.

Point estimates below a floor with an interval crossing it are unresolved, not confident failures.

No learned exposure or later algorithmic first-match system is frozen until the source-design branch becomes identifiable.

7. FIRST_MATCH_TRUTH_TABLE

These are design-audit outcomes, not learner-result branches.

Priority	Audit result	Exact condition	Smallest scientific update
1	NON_IDENTIFIABLE_UAV_BURST_G33_DESIGN	Any hard structural contradiction is established: demand changes raw physics or adds a new reward term; future/assignment leakage exists; full-ledger oracle confidently fails access; current-only constructive confidently fails access; ordinary/unaffected guardrails confidently fail; no-reallocation confidently accesses; motion-suppressed continuation confidently accesses; a stronger full-ledger static/prepositioning policy accesses; or required denominators/support are invalid	Close exact candidate P0. Infer nothing about G31/G32 or ordinary MARL. No threshold, multiplier, duration, observation or seed rescue.
2	IDENTIFIABLE_UAV_BURST_G33_DESIGN	All demand, information, support, reachability, current-only access, no-reallocation, motion-mediation, ordinary-service and leakage gates pass, and either: (a) a valid upper bound covers the complete declared static/prepositioning policy class for N1; or (b) External Pro explicitly narrows the scientific claim to N2	Freeze the exact source and its narrowed claim. The source becomes eligible for code-science alignment; no learner conclusion follows.
3	UNRESOLVED_UAV_BURST_G33_DESIGN	Every remaining pattern, including missing positive/negative witnesses, confidence intervals crossing a gate, or failure to cover the full static/prepositioning class	Preserve the UAV-transport question and return only the unresolved scientific choice. Do not implement a learned run.

The current evidence matches branch 3 because:

no G33 constructive, no-reallocation, motion-suppressed or static-preposition result exists;

no complete upper bound over Π
static
	​

 has been supplied;

the finite candidate source has not yet demonstrated physical or causal-information access.

8. CODE_SCIENCE_ALIGNMENT

No implementation is authorized here. The following is the exact future code-science correspondence required if the candidate proceeds to a source-witness realization.

8.1 config_1.py

Must retain unchanged:

S7-S1 fleet and user counts;

episode length;

movement and radio parameters;

1 Mbps ordinary demand;

0.90 QoS target;

battery/charging/failure disablement;

existing reward variant and coefficients.

The burst distributions must not be hidden as tunable config defaults after source observation.

8.2 envs/pettingzoo/scenario7_energy_aware.py

The source-specific realization must:

own a current per-user demand vector q(t);

preserve raw end-to-end capacity calculation;

compute satisfaction using current q
u
	​

(t);

use the same q
u
	​

(t) in graph-potential normalization;

expose the exact current demand metrics;

preserve PBRS terminal semantics;

change no radio, routing, energy or movement equation.

The current code’s raw-rate pipeline is separable from the scalar QoS normalization, which makes this mapping structurally possible.

8.3 envs/pettingzoo/scenario_base.py

A source-specific observation builder must:

append current demand and visibility to local user rows;

retain current relative positions, SINR and service fields;

remove normalized physical time;

never expose center ID, affected-set ID, future end, duration or assignment;

add the current demand vector to critic state;

keep all ordinary physical observations otherwise unchanged.

The base actor and critic currently lack demand and include time, so silently reusing their existing tensors would violate the scientific contract.

8.4 Policy and credit code

continuous_roster_policy.py must remain an environment-neutral policy. Input widths may reflect the exact source observation, but no burst-specific latent, branch, hotspot head, role or scheduler may be added.

return_to_go_direction_balanced_full_actor_g31.py must retain its registered detached future-tail target and direction-balanced optimization. The source must not modify the credit formula to make the burst easier.

8.5 Required pre-learner probes

A code-science alignment audit must directly establish:

demand-only intervention leaves raw rates, connections, routing and physical transition unchanged;

reward and graph potential use the identical demand vector;

local demand observations and critic demand rows are exact;

physical time, future ledger and assignment fields are absent;

burst ledger and RNG ownership are episode-addressed and arm-paired;

onset and burst-end boundaries are pre-action;

affected-cohort selection and tie breaking are exact;

constructive and no-reallocation actions are identical before onset;

motion-suppressed continuations preserve every exogenous draw;

metric arithmetic, support gates and first-match witnesses are reachable.

The G2 code and tests provide a reusable pattern for episode-addressed ledgers, current-only views, paired controls, exact intervention boundaries and fail-closed source evidence; they do not provide positive evidence for G33.

8.6 Scientific versus implementation-only choices

Scientific and frozen for P0:

demand and delivered-service semantics;

burst profile values;

affected-cohort law;

actor and critic information;

removal of explicit time;

control definitions;

target-layout library;

metrics and thresholds;

confidence unit;

audit branch order;

claim distinction N1 versus N2.

Implementation-only, provided exact equivalence holds:

file and class names;

array storage and vectorization;

cache organization;

telemetry layout;

serialization format;

fresh integer seed values;

batch partitioning;

CPU process topology;

proof-sized test file organization.

9. ONE_NEXT_BOUNDARY
next_scientific_boundary=
UAV_LOCALIZED_DEMAND_BURST_G33_SOURCE_WITNESS_AND_STATIC_UPPER_BOUND_AUDIT
Exact question

Does candidate UAV_LOCALIZED_DEMAND_BURST_G33_P0 admit both a full-ledger physical-reachability controller and a future-blind current-only constructive controller, while excluding no-reallocation, motion-suppressed execution and the strongest executable static/prepositioning policy class without sacrificing unaffected or ordinary service?

Minimum evidence object

The boundary contains only:

the exact P0 source;

the six controls in Section 5;

three replicate namespaces;

128 paired episodes per registered profile;

the estimands and bootstrap in Section 6;

zero learned model;

zero optimizer step;

no G31 or ordinary-MARL comparison.

Mutually exclusive next outcomes

SOURCE_WITNESS_SUPPORTS_N1_G33
All source gates pass and a valid static/preposition upper bound covers the declared policy class. Return to External Pro for exact final source freeze.

SOURCE_WITNESS_SUPPORTS_ONLY_N2_G33
Reachability, future-blind access, no-reallocation and motion mediation pass, but the universal static upper bound cannot be completed. Return to External Pro for an explicit claim-narrowing decision; do not let PM adopt N2 implicitly.

SOURCE_WITNESS_REJECTS_P0_G33
Any confident structural source gate fails. Close P0 without multiplier, duration, observation, threshold, budget or seed rescue.

SOURCE_WITNESS_UNDERPOWERED_G33
A required interval crosses its boundary. Close the witness under its frozen package; do not extend it automatically.

This is the cheapest evidence that can change the current decision because it addresses the exact source-identification defect before any learner is created. It remains a scientific selection only and does not authorize implementation, Git operations, nonformal execution or formal compute.

10. 中文简报

本轮裁决是：

UNRESOLVED_UAV_BURST_G33_DESIGN

不是因为“局部需求突增”方向不可行，而是因为当前还缺一项承载性证明：

目前的 NO_REALLOCATION 只能证明某一个冻结布局较差，不能排除更强的静态铺开、提前预置或无需移动的 ordinary recurrent 策略。

因此，现在不能宣称“所有能通过 benchmark 的策略都必须在 burst 后进行空间重分配”。

本轮已经把唯一候选 P0 的其他科学字段固定下来：

保持 S7-S1 的 8 架 UAV、30 个用户、500 步和原有物理环境；

每个用户普通需求为 1 Mbps；

burst 用户的当前目标速率提高到 1.5–2.5 倍；

原始无线容量、连接、带宽和路由规则不变；

delivered traffic 为 min(容量, 当前需求)；

外部 reward 仍是原有 QoS utility 和 graph PBRS，不增加 burst 奖励、移动奖励或角色奖励；

actor 只能在当前本地用户记录中看到当前需求，不能看到未来 burst、剩余时长、中心 ID 或目标 UAV；

critic 只能看到当前需求向量；

显式 physical time 从 actor 和 critic 中删除；

service roster 始终为 8，所以本源不能证明 dynamic membership。

候选 burst 分布包括：

IID：8 个用户，1.5/2.0 倍；

early-long：10 个用户，2.25 倍；

remote-strong：10 个远端用户，2.50 倍。

正式 learner 之前必须先完成 source-only 证据：

完整未来 oracle 能达到物理 access；

不看未来的 constructive controller 也能达到 access；

no-reallocation 不能达到 access；

把 burst 后 UAV 移动强制为零时不能达到 access；

未受影响用户和普通时段服务不能被牺牲；

最强静态/预置策略也不能通过，或者明确把主张缩窄为“某个已测试策略的价值由移动中介”，而不再声称普遍必要性。

下一科学边界是：

UAV_LOCALIZED_DEMAND_BURST_G33_SOURCE_WITNESS_AND_STATIC_UPPER_BOUND_AUDIT

它只检查 source 与 controls，不训练 G31/G32，也不训练 ordinary MARL。若 P0 失败，就关闭这个精确源，不能通过放大 multiplier、延长 duration、增加 seed 或降低门槛来救援。

本回复只作科学裁决，不授权实现或计算。
