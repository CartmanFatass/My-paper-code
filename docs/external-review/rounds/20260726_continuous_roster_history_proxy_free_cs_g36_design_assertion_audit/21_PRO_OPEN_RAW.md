1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=IDENTIFIABLE_BOUNDED_HISTORY_PROXY_SUBSTITUTION_G36_DESIGN
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0
training=none
checkpoints=exact_formal_G35_CS_final_only
claim_level=exact_checkpoint_plus_bounded_actor_sensor_substitution
architectural_input_deletion_claim=false

A conclusion-bearing G36 comparison can be frozen.

The scientific object is narrower than “the task is memoryless”:

For the exact three formal G35 CS final checkpoints, determine whether the actual normalized time, lifecycle age, and two previous-action values can be replaced at execution time by an independently generated, source-valid history-proxy bundle without losing registered access or more than 0.05 utility.

G35 already established that learned actor-state carry is not load-bearing in its exact P0 source, but it retained all four history-proxy coordinates. Both arms passed access, and the largest capacity-specific REC-over-CS upper bound was only 0.0054082, far below the frozen 0.05 margin. G36 therefore tests the next strictly smaller explanatory unit: dependence of the accepted CS checkpoints on the observed history-proxy bundle, not recurrence.

A positive result may support a bounded deployment-input reduction, but only in this exact form:

actual actor clock/age/previous-action inputs
    may be replaced by
the frozen G36 source-valid surrogate generator

It may not support:

deleting the four model coordinates or their learned weights;

filling them with arbitrary constants;

claiming invariance to every possible replacement distribution;

removing active masks, lifecycle ownership, current active count, or the environment’s lifecycle state;

claiming global task memorylessness.

2. EXACT_HISTORY_PROXY_INTERVENTION
2.1 Protected actor coordinates

The G32/G35 actor observation has ten coordinates:

Index	Field	G36 treatment
0:2	capability coordinates	unchanged
2	anonymous presentation priority	unchanged
3	current load	unchanged
4	current target mix	unchanged
5	log1p(active_count)	unchanged
6	lifecycle age divided by 48	replaced
7:9	previous actions mapped from [-1,1] to [0,1]	replaced
9	physical time divided by 47	replaced

The critic’s six fields, including its true physical-time coordinate, remain bitwise unchanged. The active mask, actor routing order, current-member encoding, active-set aggregate, and within-step active-fraction action prefix also remain unchanged. The actor and critic paths are separate: the critic output is not fed back as an actor input.

The intervention applies to actor observations only:

o
i,t,0:6
	​

=o
i,t,0:6
	​

,
o
i,t,6:10
	​

=
b
i,t
	​

=(
age
	​

i,t
	​

,
p
	​

i,t
(0)
	​

,
p
	​

i,t
(1)
	​

,
time
i,t
	​

).

Inactive rows remain exactly zero.

2.2 Why constants and the old G34 interventions are rejected

G36 must not reuse either of the earlier G34 interventions:

time_rotated changed both actor time and critic time;

reactive set age to zero and previous-action coordinates to 0.5, producing a fixed-point intervention rather than an on-support history-destruction control.

Those interventions answered different questions and cannot identify G36’s actor-only bundle reduction.

A constant such as:

age=0
previous_action=(0.5,0.5)
time=0

would also be rejected because it collapses all four fields onto a special JOIN/episode-start-like point. Failure could then reflect concentration on an unusual joint input rather than dependence on history information.

2.3 Source-valid donor snapshot bank

Freeze one donor-bank construction that preserves support while destroying target-history information.

Define a history-proxy bundle for one active lifecycle at a pre-action boundary:

b
i,t
	​

=(
48
age
i,t
	​

	​

,
2
a
i,t
prev,0
	​

+1
	​

,
2
a
i,t
prev,1
	​

+1
	​

,
47
t
	​

).

The donor bank is generated from fresh, non-evidence reference ledgers drawn from the exact G35 fixed and G34-P0 random source laws:

donor_namespaces=3
donor_capacities=6|8|12
donor_processes=fixed|random
donor_episodes_per_capacity_process_namespace=128
donor_base_ledger_seed_base=10360000
donor_process_seed_base=10360100

For donor namespace d∈{0,1,2}, add d once to each donor seed base.

No learned model, reward rollout, or policy action is used to build the bank. The source lifecycle is advanced by direct ledger algebra. At every donor pre-action boundary:

lifecycle age follows the exact active-step increment, temporary freeze, rejoin restoration, fresh reset, and terminal deletion semantics;

the donor previous action is the registered constructive action from that lifecycle’s most recent active decision;

if no previous active decision exists, its normalized previous-action pair is exactly (0.5, 0.5).

The registered constructive action is:

a
(0)
=2load−1,a
(1)
=2target_mix−1,

so its normalized previous-action coordinates are exactly the donor load and target mix at the most recent active action. Environment state increments age only for active rows and preserves the preceding action while a lifecycle is absent.

For each donor boundary, collect the complete simultaneous active-roster snapshot:

B=(b
1
	​

,…,b
n
	​

)

and place it in a bank B
n
	​

 indexed only by active count n.

Every donor snapshot must satisfy:

source_valid=true
all_rows_active=true
bundle_width=4
age_in_registered_support=true
previous_action_in_registered_action_support=true
time_in_registered_support=true

Every active count occurring in the conclusion-bearing G36 cells must have a nonempty donor bank. Failure is operational invalidity.

2.4 Target-side surrogate tape

Freeze:

proxy_assignment_seed_base=10361000
nonformal_seed_offset=900000

For formal replicate r, use 10361000 + r. For the bounded nonformal exercise, add 900000.

At each target pre-action boundary:

Read only the current active mask and current active count n. These are retained current inputs.

Select one donor snapshot from B
n
	​

 using an episode-addressed independent RNG.

Apply an independently sampled uniform permutation to its n donor rows.

Assign the permuted bundles bijectively to the target’s active actor rows.

Keep all inactive rows zero.

The selection tape is addressed by:

(replicate, capacity, episode_id, physical-call-position, active_count)

but its values are sampled independently of:

the target’s actual time;

actual lifecycle ages;

actual previous actions;

target membership-event identities;

target load or target mix;

reward;

checkpoint output;

stochastic action noise.

The same surrogate tape is reused for the deterministic and stochastic intervention cells belonging to the same replicate, capacity, episode, source process, and active-count trace. The stochastic cell separately reuses the exact G35 member-owned action-noise stream.

The donor bank is independent of all conclusion-bearing episode identities. Donor snapshots are therefore fixed intervention nuisance variables, not coupled bootstrap observations.

2.5 Information-destruction invariant

The binding invariant is:

B
i,t
	​

⊥(T
t
actual
	​

,A
i,t
actual
	​

,P
i,t
actual
	​

,H
i,0:t
target
	​

)∣(M
t
	​

,N
t
	​

),

where M
t
	​

 is the current active mask and N
t
	​

 the current active count.

Using the active count only to select a same-cardinality donor snapshot is permitted because active count is an explicitly retained current field. No additional episode- or lifecycle-history information may enter the transformed actor tensor.

2.6 What remains physically unchanged

The intervention does not alter:

the environment’s actual age or previous-action arrays;

membership edits or lifecycle ownership;

temporary freeze/rejoin, fresh reset, terminal deletion, or survivor continuity;

source ledgers;

current load, target mix, capability, priority, or active count;

the centralized critic input;

reward;

checkpoint parameters or buffers;

action support;

stochastic action streams;

checkpoint state before or after evaluation.

Thus G36 tests actor-input dependence, not a modified environment.

3. ESTIMAND_CLAIM_CEILING_AND_GATES
3.1 Notation

Let:

R: registered G35 CS execution;

X: G36 history-proxy-substituted execution;

s∈{F,R}: fixed or random membership process;

m∈{D,S}: deterministic or stochastic action mode;

C∈{6,8,12}: configured capacity.

For a paired episode:

Δ
s,m,C,r,e
U
	​

=U
s,m,C,r,e
R
	​

−U
s,m,C,r,e
X
	​

.

Positive values mean that the actual history-proxy bundle helped.

The primary estimand is equal-capacity-weighted random deterministic loss:

Δ
HP
	​

=
3
1
	​

C∈{6,8,12}
∑
	​

E
r,e
	​

[Δ
R,D,C,r,e
U
	​

].

Freeze the materiality/noninferiority margin:

δ
HP
	​

=0.05.
3.2 Claim ceiling

A passing result supports two nested statements.

Checkpoint-level statement:

The exact formal G35 CS final checkpoints do not require the actual history-proxy bundle for registered G32/G34 access; an independent source-valid surrogate bundle is sufficient within G36-P0.

Bounded deployment-input statement:

Within the same source, capacities, horizon, and checkpoint family, an actor deployment need not obtain the actual clock, lifecycle-age, or previous-action values. Those values may be replaced by the frozen G36 surrogate generator.

The deployment statement is legal only if artifact validation proves that:

actual_age_read_count=0
actual_previous_action_read_count=0
actual_actor_time_read_count=0
critic_transform_count=0
checkpoint_update_count=0

It remains a sensor-substitution result. It does not support reducing the model from ten actor coordinates to six, recompiling the learned tensors, or using an arbitrary filler distribution.

A failing result supports only:

The actual bundle or its target-context coherence is load-bearing for these exact checkpoints.

It cannot distinguish:

semantically useful temporal information;

reliance on correlations learned during training;

generic sensitivity to counterfactual input combinations.

It therefore cannot establish task-level history necessity.

3.3 Registered-baseline gate

Before interpreting G36, validation must independently establish that the referenced G35 artifact is exactly the accepted formal package:

source_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
registered_branch=CURRENT_STATE_REDUCTION_SUFFICIENT_G35
formal=true
operational_valid=true
arm=CS
checkpoint_kind=final
replicates=3
checkpoint_source_commit=f626dfd8a345ef670e08e601344b67e28ffb3563

The exact CS checkpoints must strict-load at capacities 6, 8, and 12, and their registered G35 cells must retain the accepted access predicates. G35’s formal CS stochastic LCB was 0.88288, learned-gain LCB was 0.27127, and its minimum random deterministic replicate mean was 0.94103.

No new zero-checkpoint cell is needed in G36. Learned competence is inherited from the exact validated G35 result; G36 is a checkpoint-interface intervention. Conclusion-bearing G36 utility must nevertheless pass every absolute access gate below.

3.4 Intervention absolute-access gates

INTERVENTION_ACCESS_PASS requires all of the following.

Fixed process

For every capacity C:

LCB
95
	​

(U
F,D,C
X
	​

)≥0.90.

Pooled fixed stochastic:

LCB
95
	​

(U
F,S
X
	​

)≥0.80.

Minimum fixed deterministic replicate mean:

r
min
	​

U
F,D,r
X
	​

≥0.85.
Random process

For every capacity C:

LCB
95
	​

(U
R,D,C
X
	​

)≥0.90,
LCB
95
	​

(E
R,D,C
X
	​

)≥0.85,
LCB
95
	​

(P
R,D,C
X
	​

)≥0.85,

where E is minimum four-step event-window utility and P is minimum event-delimited process-segment utility.

The intervention’s own random-minus-fixed transport must satisfy:

LCB
95
	​

(U
R,D,C
X
	​

−U
F,D,C
X
	​

)≥−0.05∀C.

Pooled random stochastic:

LCB
95
	​

(U
R,S
X
	​

)≥0.80.

Minimum random deterministic replicate mean:

r
min
	​

U
R,D,r
X
	​

≥0.85.

Equality passes at every non-strict floor.

The per-episode utility, event-window, and process-segment definitions remain the exact G34/G35 trace-derived quantities. The inherited G35 access contract uses these same utility, stochastic, local-window, process-transport, and replicate-stability floors.

3.5 Registered-minus-intervention noninferiority

A history-proxy-free sufficiency result additionally requires:

Deterministic utility
UCB
95
	​

(Δ
F,D,C
U
	​

)≤0.05,UCB
95
	​

(Δ
R,D,C
U
	​

)≤0.05

for every capacity C.

Stochastic utility
UCB
95
	​

(Δ
F,S
U
	​

)≤0.05,UCB
95
	​

(Δ
R,S
U
	​

)≤0.05,

pooled with equal capacity weight.

Random-process local performance

For every capacity C:

UCB
95
	​

(E
R,D,C
R
	​

−E
R,D,C
X
	​

)≤0.05,
UCB
95
	​

(P
R,D,C
R
	​

−P
R,D,C
X
	​

)≤0.05.
Primary estimand
UCB
95
	​

(Δ
HP
	​

)≤0.05.

Equality at 0.05 supports noninferiority.

3.6 Confident intervention failure

INTERVENTION_ACCESS_CONFIDENT_FAIL holds if any corresponding:

utility, event-window, process-segment, or stochastic upper confidence bound is below its absolute floor;

random-minus-fixed upper confidence bound is below −0.05;

registered minimum replicate statistic is below 0.85.

MATERIAL_PROXY_LOSS holds if any of the following is strict:

LCB
95
	​

(Δ
HP
	​

)>0.05,
LCB
95
	​

(Δ
s,m,C
U
	​

)>0.05

for any registered deterministic capacity/source cell or pooled stochastic source cell, or:

LCB
95
	​

(E
R
−E
X
)>0.05orLCB
95
	​

(P
R
−P
X
)>0.05

for any random-process capacity.

3.7 Non-rescuing diagnostics

Report, but do not branch on:

pre-tanh mean difference;

deterministic action mean absolute difference;

stochastic action TV or Wasserstein-style paired displacement;

first-layer weights attached to indices 6:10;

performance stratified by event type, active count, or source order.

These diagnostics may localize sensitivity but cannot rescue or overturn the primary first-match result.

4. PAIRING_CONFIDENCE_AND_EVIDENCE
4.1 Existing registered evidence

The registered side of every contrast is read from the exact accepted G35 formal artifacts. It is not rerun.

G36 must bind:

the formal G35 training-manifest digest;

evaluation-manifest digest;

analysis result;

each replicate-specific CS final checkpoint digest;

each registered episode identity and process signature.

G35 already used paired episode identities, G32 fixed and G34-P0 random sources, capacities 6/8/12, deterministic/stochastic modes, and a whole-episode hierarchical bootstrap.

4.2 New conclusion-bearing cells

Only four new intervention cells are evaluated per replicate and capacity:

CS_HISTORY_FREE_FIXED_DET
CS_HISTORY_FREE_FIXED_STOCH
CS_HISTORY_FREE_RANDOM_DET
CS_HISTORY_FREE_RANDOM_STOCH

Therefore:

formal_replicates=3
capacities=3
new_cells_per_replicate_capacity=4
formal_total_new_cells=36
episodes_per_cell=128
formal_new_evaluation_episodes=4608
H=48
formal_real_transitions=221184
optimizer_steps=0
episode_exclusions=none

This uses the complete inherited 128-episode support. No post hoc episode subset is selected.

The registered G35 baseline contributes no new transitions.

4.3 Action and surrogate coupling

For every replicate, capacity, process, and episode:

the intervention uses the exact registered G35 source ledger;

the stochastic intervention uses the exact registered member-owned G35 action-noise stream;

deterministic and stochastic intervention cells share the same history-proxy tape;

fixed and random cells use the same tape whenever their current active count agrees;

source and action RNG states never advance the donor-bank or proxy-selection RNG;

donor-bank and proxy-selection RNG never advance source or action RNG.

4.4 Formal seed block

Freeze:

donor_base_ledger_seed_base=10360000
donor_process_seed_base=10360100
proxy_assignment_seed_base=10361000
bootstrap_seed=10362036
nonformal_seed_offset=900000

Replicate-specific formal proxy seeds add the replicate index exactly once.

4.5 Hierarchical confidence construction

Use exactly 10,000 percentile bootstrap resamples.

One paired plan is generated once and reused for every conclusion-bearing quantity:

Resample the three formal replicate blocks with replacement.

Within each selected replicate and capacity, resample all 128 whole episode IDs.

Retain the registered and intervention branches, fixed and random processes, deterministic and stochastic modes, reward traces, roster traces, and event/process summaries belonging to the selected episode.

Never resample:

members;

time steps;

events;

lifecycle rows;

actor modes;

proxy-bundle rows;

registered and intervention branches independently.

The donor bank and realized proxy tapes are fixed experimental nuisance objects and are not separately resampled.

Pooled estimands weight capacities 6, 8, and 12 equally, matching G35’s primary capacity aggregation. G35’s accepted confidence unit was paired replicate blocks followed by whole episode IDs, with no episode exclusion.

5. WITNESSES_AND_IDENTIFIABILITY
5.1 Positive pass witness

Use the already established current-readout witness:

set every history-proxy weight to zero;

use only current load and current target mix to produce:

a
(0)
=tanh(2L−1),a
(1)
=tanh(2M−1).

Its minimum utility over the complete registered load/mix support is:

0.94048>0.90.

Because its output is independent of actor coordinates 6:10, registered and history-proxy-substituted execution are exactly equal:

Δ
HP
	​

=0.

Thus the intervention can pass without relying on an impossible policy class, and it does not destroy the load/mix route needed for access.

5.2 Source-support witness

Every surrogate active-roster snapshot is taken from a valid source lifecycle under the exact constructive action.

It therefore preserves:

valid normalized time;

a time-consistent lifecycle-age pattern;

valid fresh-join (age=0, previous_action=(0.5,0.5)) rows;

valid survivor and rejoin ages;

previous actions inside the exact task action support;

a valid simultaneous active-count cardinality.

The intervention breaks the connection to the target’s history, not the legal support of the substituted coordinates.

5.3 Confident-fail witness

A checkpoint may use actual time or age to gate an otherwise correct load/mix mapping, for example:

if true_time agrees with trained phase:
    emit constructive action
else:
    emit low-effort action

Registered execution accesses. Independent donor-time execution fails absolute utility or yields:

LCB
95
	​

(Δ
HP
	​

)>0.05.

This reaches HISTORY_PROXY_BUNDLE_LOAD_BEARING_G36 for its intended reason.

The prior G34 recurrent checkpoint already supplied a concrete example of substantial exact-checkpoint sensitivity to the time coordinate: rotating time produced a utility interval below 0.90 and a control-minus-primary interval entirely below −0.05. That result was checkpoint-specific and did not establish task-level time necessity.

5.4 Mixed witness

For example:

intervention absolute gates pass
Delta_HP CI95=[0.03,0.07]

The intervention may be acceptable, but its upper bound exceeds the 0.05 noninferiority margin while its lower bound does not establish material loss. The correct branch is mixed/underpowered.

Another mixed case is an intervention utility interval crossing 0.90 without its upper bound falling below 0.90.

5.5 Identifiability ceiling

G36 identifies the bundle:

actual time
+ actual lifecycle age
+ actual previous action 0
+ actual previous action 1

It does not identify any member of that bundle separately.

A positive result means the actual bundle is replaceable for the exact checkpoints under the frozen donor law.

A negative result means one or more of the following is load-bearing:

actual temporal information;

actual action history;

lifecycle-phase information;

target-context coherence of those fields;

a learned correlation involving the bundle.

No result may be rewritten as “time alone matters” or “previous actions alone matter.”

5.6 Stronger deployment invariant

The bounded deployment-input reduction is accepted only if all of the following are mechanically proven:

The actor receives no actual value from indices 6:10.

The surrogate generator reads no target history except current active mask/count.

The critic remains unchanged.

Checkpoint tensors remain unchanged.

Every fixed/random, deterministic/stochastic, capacity, event-window, and process-segment gate passes.

Every registered-minus-intervention upper bound is at most 0.05.

If those conditions hold, actual clock/age/action-history sensors may be omitted provided that the exact frozen surrogate generator remains present.

This does not establish safe replacement by zeros, means, arbitrary noise, or a different donor distribution.

6. FIRST_MATCH_TRUTH_TABLE

Define:

OPERATIONAL_VALID: exact artifact, checkpoint, donor-bank, proxy-tape, actor-only transform, RNG, cell, trace, lifecycle, zero-step, and finite-value invariants pass.

REGISTERED_SOURCE_ACCESS_VALID: the exact formal G35 source, CS final checkpoints, registered access predicates, and accepted branch validate.

INTERVENTION_ACCESS_PASS: every absolute gate in Section 3.4 passes.

INTERVENTION_ACCESS_CONFIDENT_FAIL: Section 3.6.

PROXY_NONINFERIOR: every registered-minus-intervention upper bound in Section 3.5 is at most 0.05.

MATERIAL_PROXY_LOSS: Section 3.6.

Priority	Terminal branch	Exact predicate	Smallest scientific update
1	INVALID_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36	OPERATIONAL_VALID=false	No scientific update. Repair only the exact operational corruption under the unchanged contract.
2	SOURCE_OR_REGISTERED_ACCESS_FAILURE_G36	Operationally valid and REGISTERED_SOURCE_ACCESS_VALID=false	Close this exact evidence package without interpreting the history-proxy intervention. Do not alter G35’s accepted result.
3	HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36	Registered source valid, INTERVENTION_ACCESS_PASS=true, and PROXY_NONINFERIOR=true	Support checkpoint-level independence from the actual bundle and the bounded actor-sensor substitution described above. Do not claim architectural coordinate deletion or global task memorylessness.
4	HISTORY_PROXY_BUNDLE_LOAD_BEARING_G36	Registered source valid and either INTERVENTION_ACCESS_CONFIDENT_FAIL=true or MATERIAL_PROXY_LOSS=true	Retain the actual/coherent proxy bundle as load-bearing for these exact checkpoints. Do not infer which field matters or that retrained policies require history.
5	MIXED_UNDERPOWERED_HISTORY_PROXY_G36	Every remaining valid numerical pattern	Preserve both explanations and close G36-P0 without seed, tape, margin, episode, source, or checkpoint rescue.

Branch evaluation stops at the first match.

Equality semantics:

absolute_floor equality       = pass
UCB(registered-intervention)=0.05 = noninferior pass
LCB(registered-intervention)>0.05 = material-loss pass
random-minus-fixed=-0.05      = transport pass

No descriptive action or weight diagnostic can relabel an earlier branch.

7. EVIDENCE_COMPLEXITY_AND_AUTHORITY
7.1 Search complexity
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

The donor bank is constructed by direct source-ledger algebra. It performs no hypothetical environment rollout and no candidate search.

This satisfies the project ceiling requiring fixed K_search, no nested replanning, and at most 16H hypothetical transitions.

7.2 Bounded nonformal preflight

Freeze:

replicates=1
capacities=6|8|12
intervention_cells_per_capacity=4
episodes_per_cell=8
bootstrap_resamples=250
optimizer_steps=0

Real transitions:

1×3×4×8×48=4,608.

The nonformal package must additionally validate:

exact G35 formal artifact and checkpoint binding;

complete donor-bank support for every active count;

target-history read count of zero;

actor-only transform;

identical deterministic/stochastic proxy tapes;

exact action-noise coupling;

zero checkpoint drift;

exact trace recomputation;

branch-witness arithmetic.

It may return only a nonformal completion or non-executable result.

The full nonformal evaluate/analyze package must finish within:

1,200 seconds.
7.3 Formal inventory
formal_replicates=3
formal_capacities=3
formal_intervention_cells=36
formal_episodes_per_cell=128
formal_evaluation_episodes=4608
formal_real_transitions=221184
formal_optimizer_steps=0
bootstrap_resamples=10000

This exactly reaches, but does not exceed, the user-provided 221,184 transition ceiling.

7.4 Wall-clock projection

The nonformal exercise records separately:

T_eval_nf
T_analysis_nf

The conservative formal projection is:

T
projected
	​

=1.25(48T
eval,nf
	​

+40T
analysis,nf
	​

).

The factor 48 is the exact formal/nonformal evaluation-volume ratio:

1×8
3×128
	​

=48,

and 40 is the bootstrap ratio:

250
10,000
	​

=40.

Formal evaluation is scientifically admissible only if:

T
projected
	​

≤28,800 seconds.

Failure is:

NON_EXECUTABLE_EVIDENCE_DESIGN

and is not a scientific result or consumed conclusion-bearing iteration. The governing policy caps the complete nonformal exercise at 20 minutes and the formal boundary at eight hours.

7.5 Required authority sequence

Before formal evaluation:

PM must technically accept one implementation of this exact contract.

A pushed commit-bound code-science index must identify every claim-bearing path.

The code-science alignment audit must return ALIGNED.

One exact bounded nonformal preflight from the same source commit must validate and project within the formal cap.

The future formal runner must require a dedicated G36 authority token and bind it to that exact aligned source and preflight.

This response supplies no such authority.

8. CODE_SCIENCE_MAPPING
Scientific field	Existing surface or one minimal new G36 symbol	Binding correspondence
Actor observation indices	RuntimeCapacityRosterEnv.observe	Preserve indices 0:6; replace active-row indices 6:10; inactive rows remain zero. The critic state is untouched.
Exact CS checkpoint	G35 runner checkpoint loader and accepted formal artifact validator	Strict-load only replicate-specific G35 CS/final checkpoints at capacities 6/8/12; bind exact source, phase exposure, and digest.
Zero learned carry	G35MatchedStateCarryActor with carry_mode=CS	Carried hidden storage remains exactly zero; G36 adds no actor-state treatment.
Fixed source	RuntimeCapacityRosterEnv and G32 ledger law	Exact G32 event process, reward, observations, and lifecycle ownership.
Random source	G35 make_process_ledgers and RandomProcessRosterEnv	Exact G34-P0 event-time, order, profile, cohort, and episode-pairing law.
Source-valid donor bank	minimal new symbol G36HistoryProxyDonorBank	Build full active-roster proxy snapshots from fresh fixed/random reference ledgers and constructive previous actions, grouped by active count.
Actor-only tape	minimal new symbol G36HistoryProxyTape	Episode-addressed selection and anonymous permutation; no actual time/age/previous-action input; same tape across deterministic/stochastic paired cells.
Actor transform	minimal new symbol apply_g36_actor_history_proxy_transform	Modify only active actor observation coordinates 6:10; return critic, source state, checkpoint, mask, and current fields unchanged.
Stochastic pairing	G32 member-owned action-noise generator and G35 evaluation seed block	Registered and intervention stochastic branches share the exact action-noise tensor.
Episode metrics	G34 trace-derived utility/event-window/process-segment functions	Recompute every conclusion-bearing value from serialized 48-step reward and roster traces.
Registered evidence binding	G35 artifact validators and manifest digests	Read exact formal G35 baseline cells rather than rerunning them; reject any source, branch, checkpoint, or episode mismatch.
Confidence	inherited whole-episode hierarchical plan, minimal G36 bootstrap wrapper	One seed, one paired replicate/episode plan, reused across all G36 contrasts.
First-match result	minimal new select_g36_result_branch	Implement the exact priority and strict/inclusive comparisons in Section 6.
Complexity and authority	minimal G36 configuration/preflight validator	Freeze 4,608 nonformal and 221,184 formal transitions, zero optimizer steps, projection formula, source binding, and formal-token gate.

Relevant existing implementation facts are:

the policy actor reads the ten-member observation through one shared member encoder and uses active-set aggregation plus a prefix-conditioned routing loop;

G32 writes age, normalized previous actions, and true time into actor coordinates 6:10;

G35 CS already keeps carried actor storage exactly zero.

Scientific and frozen

donor-bank law;

donor and tape seeds;

conditional-independence invariant;

actor coordinates;

actor-only transform;

exact checkpoints and baseline artifacts;

four-cell inventory;

estimands;

0.05 margin;

access and local-performance gates;

confidence unit;

branch order;

transition and wall-clock bounds.

Implementation-only

file and class names beyond the minimal scientific symbols;

array layout;

vectorization;

donor-bank caching;

serialization format;

telemetry layout;

batch partitioning;

proof-sized test-file organization.

An implementation that:

uses zeros or constants instead of the donor tape;

transforms the critic;

reads actual time, age, or previous actions to select the surrogate;

regenerates or retrains a checkpoint;

reruns only a selected subset of G35 episodes;

changes action noise;

adds per-field post hoc branches

is scientifically nonconforming.

9. ONE_NEXT_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary becomes eligible only after PM has technically accepted one exact pushed implementation.

Its sole scientific question is:

Does the accepted code instantiate the source-valid donor snapshot bank, actual-history-independent actor-only substitution, exact formal G35 CS checkpoint and episode binding, four-cell zero-training inventory, paired action streams, registered access/noninferiority estimands, whole-episode confidence plan, and first-match semantics frozen here, without creating another route to a positive branch?

It is a read-only contract diff. It may not add or change a proxy distribution, checkpoint, source, margin, evidence volume, confidence unit, or result branch.

This disposition authorizes no implementation, Git operation, nonformal exercise, formal evaluation, monitoring, or successor child.

10. 中文简报

本轮裁决是：

IDENTIFIABLE_BOUNDED_HISTORY_PROXY_SUBSTITUTION_G36_DESIGN

G36 可以形成有效的零训练证据，但必须避免把 age、previous action 和 time 简单设成常数。常数会把所有输入集中到类似 episode 起点或 fresh JOIN 的特殊位置，失败时无法区分：

checkpoint 真正需要历史信息；

checkpoint 只是无法处理严重的输入分布偏移。

精确干预

G35 actor 的 10 个输入中：

0:2   capability
2     anonymous priority
3     current load
4     target mix
5     log active count
6     lifecycle age
7:9   two previous actions
9     normalized true time

G36 只替换 actor 的 6:10，其他全部保留；critic 仍然看到真实时间。

替代值来自一个独立的 source-valid donor bank：

用全新的 RNG namespace，按照原 G32 fixed 与 G34 random source law 生成参考 ledgers；

只通过 lifecycle ledger 代数构造每个 active roster snapshot；

donor 的 age/time 来自真实合法 lifecycle；

donor previous actions 来自 constructive load/mix action；

按 active count 建立 snapshot bank；

对每个目标 step 独立抽取一个同 cardinality snapshot，并随机置换到目标 active rows。

因此，每组替代值本身来自一个合法 source history，但与目标 episode 的真实 time、age 和 previous actions 独立。

可以支持什么

若所有门槛通过，G36 可以支持：

对精确 G35 CS final checkpoints，在注册 fixed/random、capacity 6/8/12、H=48 范围内，不需要向 actor 提供真实 time、age 和 previous-action sensors；这些值可以由冻结的 surrogate generator 替代。

它不能支持：

把模型从 10 维改成 6 维；

任意常数或任意噪声都可以；

task 全局 memoryless；

所有重新训练的策略都不需要历史；

lifecycle mask、JOIN/LEAVE/REJOIN 状态可以删除。

主估计量
Δ
HP
	​

=U
registered
	​

−U
history-free
	​

.

margin 固定为：

0.05.

history-free branch 必须：

fixed/random deterministic access 通过；

fixed/random stochastic access 通过；

random event-window 和 process-segment 通过；

random-minus-fixed transport 通过；

每个 capacity 及 pooled registered-minus-intervention UCB 均不超过 0.05。

正式分支为：

INVALID_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36
SOURCE_OR_REGISTERED_ACCESS_FAILURE_G36
HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36
HISTORY_PROXY_BUNDLE_LOAD_BEARING_G36
MIXED_UNDERPOWERED_HISTORY_PROXY_G36

负结果只能说明整个 bundle 或其与当前 context 的一致性对这些 checkpoint 有用，不能单独归因于 time、age 或 previous actions 中的某一个。

证据规模

不重新运行 registered baseline，只读取并绑定 G35 正式 artifacts。新执行仅有四类 intervention cell：

fixed deterministic
fixed stochastic
random deterministic
random stochastic

正式规模：

3 replicates
3 capacities
36 cells
128 episodes per cell
221184 real transitions
0 optimizer steps
H=48
K_search=0
hypothetical transitions=0

nonformal preflight 为 4,608 transitions，必须在 20 分钟内完成；正式投影必须低于 8 小时。

下一边界是：

CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_CODE_SCIENCE_ALIGNMENT_AUDIT

本回复只冻结科学合同，不授权代码、Git、非正式或正式评估。
