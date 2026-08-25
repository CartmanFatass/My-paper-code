1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=IDENTIFIABLE_BOUNDED_FACTORIZED_HISTORY_PROXY_COHERENCE_G37_DESIGN
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0
training=none
checkpoints=exact_formal_G35_CS_final_only
reference_execution=exact_formal_G36_joint_donor_read_only
claim_level=exact_checkpoint_cross_column_donor_coherence
architectural_input_deletion_claim=false
task_level_history_necessity_identifiable=false

A conclusion-bearing G37 comparison can be frozen.

The comparison is scientifically identifying only under this exact interpretation:

G37 tests whether the exact G35 CS final checkpoints require the shared-snapshot and shared-row-alignment coherence across the four G36 donor columns—age, previous-action-0, previous-action-1, and time—or whether four independently drawn active-count-conditioned donor marginals are sufficient.

G36 already established that the target episode’s actual coherent history bundle is replaceable by one independent but internally coherent source-valid donor snapshot. Its primary registered-minus-donor interval was [-0.002479, 0.000105, 0.003575], and every conclusion-bearing upper bound was below 0.007529 against the 0.05 margin. G36 expressly retained donor-internal joint coherence as the strongest remaining explanation.

G37 does not test every possible form of roster dependence. The frozen factorization below preserves each individual coordinate column’s complete active-count-conditioned donor distribution, including its within-column roster structure. In particular, a donor time column remains roster-shared when it was roster-shared in its source snapshot. G37 destroys the coupling between columns and their common member alignment, not all dependence inside each column.

A positive result may support only:

The exact checkpoints do not require the G36 donor’s cross-column joint coherence under the exact G37 factorized marginal law.

A negative result may support only:

That joint coherence, or distributional consistency supplied by it, is load-bearing for these checkpoints.

Neither result establishes task-level history necessity, global memorylessness, safe arbitrary noise, or architectural deletion.

2. EXACT_FACTORIZED_DONOR_LAW
2.1 Exact donor population

G37 reuses the byte-identical G36 donor-bank population and ordering. It does not create, rebalance, deduplicate, truncate, or reweight a new donor population.

For active count n, let:

B
n
	​

={B
n,s
	​

∈[0,1]
n×4
:s=0,…,K
n
	​

−1}

be the exact ordered G36 bank for that count, with columns:

k=0:normalized age,k=1:normalized previous action 0,k=2:normalized previous action 1,k=3:normalized time.

The bank population is generated in this immutable nesting order:

namespace      0,1,2
capacity       6,8,12
process        fixed,random
local episode  0..127
physical time  0..47

Each complete simultaneous active-roster snapshot is appended to the bank corresponding to its current active count. Snapshot weighting is therefore exactly the existing G36 snapshot-frequency weighting; G37 may not equalize capacities, processes, episodes, event phases, or physical times.

G36’s source code already constructs three namespaces over capacities 6/8/12, fixed and random processes, 128 episodes, and legal lifecycle algebra, then groups complete n×4 snapshots solely by active count.

The required active-count support remains exactly:

2,3,4,5,6,7,8,10

Every conclusion-bearing target count must have a nonempty B
n
	​

.

2.2 G36 joint-donor law

The accepted G36 joint donor, conditional on current active count n, has the following law:

Draw one snapshot index:

S∼Uniform{0,…,K
n
	​

−1}.

Draw one uniform row permutation:

Π∼Uniform(S
n
	​

).

Use:

J
j,k
	​

=B
n,S,Π(j),k
	​

j=0,…,n−1,k=0,…,3.

Thus all four columns share one snapshot identity and one member permutation. This is the exact coherence G37 intervenes on. The existing G36 tape selects one snapshot and applies one permutation to its complete rows.

2.3 G37 factorized law

For every target pre-action boundary with active count n, independently for each coordinate k∈{0,1,2,3}:

Draw a snapshot index with replacement:

S
k
	​

∼
ind
Uniform{0,…,K
n
	​

−1}.

Draw an independent uniform row permutation:

Π
k
	​

∼
ind
Uniform(S
n
	​

).

Construct the target active-row column:

F
j,k
	​

=B
n,S
k
	​

,Π
k
	​

(j),k
	​

.

The four S
k
	​

 and four Π
k
	​

 are mutually independent conditional on the tape address. Accidental equality—such as S
0
	​

=S
3
	​

—is permitted and must not be rejected or redrawn. Conditioning on distinct selected snapshots would alter the frozen marginal law.

The complete factorized active-roster bundle is:

F
n
	​

=
	​

F
0,0
	​

⋮
F
n−1,0
	​

	​

F
0,1
	​

⋮
F
n−1,1
	​

	​

F
0,2
	​

⋮
F
n−1,2
	​

	​

F
0,3
	​

⋮
F
n−1,3
	​

	​

	​

.

Rows are assigned, in order, to the target’s ascending active runtime-slot indices. Selection is conditioned only on n; the identity pattern of the active mask is used only for placement. All inactive actor rows remain exactly zero.

2.4 Exact marginal-preservation invariant

For each active count n and coordinate k, define the G36 column marginal:

M
n,k
	​

=Law(B
n,S,Π(⋅),k
	​

).

Because S
k
	​

 and Π
k
	​

 have exactly the same individual laws as S and Π,

F
⋅,k
	​

=
d
J
⋅,k
	​

∣n.

Therefore G37 preserves exactly:

the snapshot-uniform empirical distribution of each entire n-row column;

each target active row’s scalar empirical marginal for that coordinate;

the legal numeric support of every coordinate;

the within-column multiset and finite-population structure;

the G36 donor bank’s capacity/process/time frequency weighting.

No clipping, normalization, jitter, interpolation, rejection sampling, or post-selection is permitted after a column is drawn.

2.5 Exact coherence removed

G37 removes the following G36 couplings:

Shared snapshot coupling

S
0
	​

=S
1
	​

=S
2
	​

=S
3
	​


is replaced by independent S
k
	​

.

Shared member-permutation coupling

Π
0
	​

=Π
1
	​

=Π
2
	​

=Π
3
	​


is replaced by independent Π
k
	​

.

Within-row lifecycle coherence
A target row’s age, previous-action pair, and time no longer come from the same donor lifecycle at the same donor boundary.

Previous-action-pair coherence
Previous-action-0 and previous-action-1 may come from distinct donor snapshots and distinct donor members.

Roster-level cross-column configuration
The age vector, action-0 vector, action-1 vector, and time vector no longer form one jointly observed donor roster.

What G37 deliberately retains:

each coordinate’s own active-count-conditioned column law;

within-column dependencies among members;

the donor time column’s roster-shared structure where present;

independently occurring accidental cross-column matches.

Accordingly, the branch name JOINT_DONOR_COHERENCE_LOAD_BEARING_G37 refers specifically to cross-column shared-snapshot/shared-alignment coherence, not to every possible within-column roster dependence.

2.6 Actor-only application

The factorized bundle replaces only active actor coordinates 6:10.

actor coordinates 0:6      exact target values
actor coordinates 6:10     G37 factorized donor
inactive actor rows         exact zero
critic state                exact target state, unchanged
environment lifecycle       unchanged
checkpoint tensors          unchanged

The corrected G36 input path already constructs a fresh actor tensor from source coordinates :6 only before writing proxy coordinates 6:10; that no-read boundary remains mandatory.

3. SEED_OWNERSHIP_AND_REFERENCE_BINDING
3.1 Inherited G36 donor seeds

The exact G36 donor bank remains governed by:

donor_base_ledger_seed_base=10360000
donor_process_seed_base=10360100
donor_namespaces=3
donor_capacities=6|8|12
donor_processes=fixed|random
donor_episodes_per_capacity_process_namespace=128

These values and the resulting bank ordering are immutable.

3.2 New G37 factorization seeds

Freeze:

factorized_proxy_seed_base=10363000
bootstrap_seed=10364037
nonformal_seed_offset=900000

For formal replicate r∈{0,1,2}:

q
r
	​

=10363000+r.

For bounded nonformal execution:

q
r
nf
	​

=10363000+r+900000.

For coordinate k, use separate streams:

snapshot-selection stream = 2*k
row-permutation stream     = 2*k+1

The exact seed addresses are:

SeedSequence[q
r
	​

,C,e,t,n,2k]

for snapshot selection and:

SeedSequence[q
r
	​

,C,e,t,n,2k+1]

for row permutation, where:

C: configured capacity;

e: inherited episode ID;

t: physical call position 0..47;

n: current active count.

The physical call position is an RNG address only. Its target value is not read from actor history and is never inserted into the actor except through the independently selected donor time column.

The factorized tape cache key is:

(episode_id, physical_call_position, active_count)

within a tape object already bound to replicate and capacity.

The key excludes:

fixed versus random source identity;

deterministic versus stochastic mode;

active-member identities;

target event type;

target actual age or previous actions;

target load or target mix;

reward;

checkpoint outputs;

action-noise state.

Consequently:

deterministic and stochastic factorized cells reuse the exact same tape;

fixed and random factorized cells reuse the same tape whenever episode ID, call position, and active count agree;

source RNG, factorization RNG, bootstrap RNG, and action RNG are disjoint.

3.3 Exact G36 read-only reference

The joint side is read, not rerun.

G37 must bind the exact formal G36 package:

source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0
source_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
registered_branch=HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36
scientific_disposition=SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36
formal=true
operational_valid=true
replicates=3
capacities=6|8|12
episodes_per_cell=128

and the exact formal G36 evaluation digest:

g36_evaluation_sha256=
03b6ae2bca6f284524b442bd642dd306b8a8db7e6103d177e6982bfeea864bf6

It must also bind and validate the inherited G35 package:

g35_training_sha256=
30c6e75095502e9983c3c8e30b40c335e2304817b3fbc798c4798a58d15ca067

g35_evaluation_sha256=
fee215d449bb2a20609717864129b9df3631f0677637f4482e1e85e2685810fe

g35_analysis_sha256=
ed8a4559592b023ab617cddb86ee188a67098c3f72830f206a13b4539799adfa

These are the formal package identities reported by the completed G36 evidence.

G37 validation must:

invoke the existing formal G36 artifact validator;

recompute G36’s registered metrics and branch from its episode traces;

bind the exact G36 analysis file by digest;

bind each replicate-specific G35 CS final checkpoint digest;

reject any altered source, branch, episode inventory, process signature, trace, proxy digest, or checkpoint.

The G36 joint cells read as reference are:

CS_HISTORY_FREE_FIXED_DET
CS_HISTORY_FREE_FIXED_STOCH
CS_HISTORY_FREE_RANDOM_DET
CS_HISTORY_FREE_RANDOM_STOCH
3.4 New G37 factorized cells

The only new cells are:

CS_FACTORIZED_FIXED_DET
CS_FACTORIZED_FIXED_STOCH
CS_FACTORIZED_RANDOM_DET
CS_FACTORIZED_RANDOM_STOCH

For each replicate and capacity, the factorized evaluator strict-loads the same exact G35 CS final checkpoint used by G36 and preserves state before and after evaluation.

The factorized stochastic cells reuse the exact G35 member-owned action stream used by the corresponding G36 joint-reference cells. Deterministic and stochastic cells share the same factorized tape but not policy sampling mode.

4. ESTIMAND_CLAIM_CEILING_AND_GATES
4.1 Notation

Let:

J: accepted G36 joint-donor reference;

F: G37 factorized-donor execution;

s∈{fixed,random};

m∈{det,stoch};

C∈{6,8,12}.

For each paired episode:

Δ
s,m,C,r,e
U
	​

=U
s,m,C,r,e
J
	​

−U
s,m,C,r,e
F
	​

.

Positive values favor joint donor coherence.

The primary estimand is the equal-capacity-weighted random deterministic contrast:

Δ
coh
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

[U
random,det,C,r,e
J
	​

−U
random,det,C,r,e
F
	​

]
	​


Freeze:

δ
coh
	​

=0.05.
4.2 Positive claim ceiling

FACTORIZED_HISTORY_PROXY_SUFFICIENT_G37 may support only:

For the exact G35 CS final checkpoints, G32/G34 source family, capacities 6/8/12, horizon 48, exact G36 donor population, and exact G37 factorized seed law, shared cross-column snapshot/member coherence is not required for registered access and supplies no material benefit exceeding 0.05.

It may additionally support deployment with the exact factorized surrogate generator.

It may not support:

deletion of coordinates 6:10;

arbitrary marginal distributions;

arbitrary independent noise;

elimination of within-column roster structure;

individual redundancy of age, either previous-action field, or time;

global task memorylessness;

history independence after retraining;

critic-time deletion.

4.3 Negative claim ceiling

JOINT_DONOR_COHERENCE_LOAD_BEARING_G37 may support only:

The exact checkpoint depends materially on the G36 shared-snapshot/shared-alignment distribution relative to the frozen G37 factorized law.

A negative result cannot distinguish:

semantic temporal reasoning;

learned sensitivity to cross-coordinate correlations;

generic multivariate distribution-shift sensitivity;

dependence on one particular coordinate relationship;

task-level history necessity.

4.4 Factorized absolute-access gates

The factorized execution must pass every inherited G36 access requirement.

Fixed process

For each capacity:

LCB
95
	​

(U
fixed,det,C
F
	​

)≥0.90.

Pooled fixed stochastic:

LCB
95
	​

(U
fixed,stoch
F
	​

)≥0.80.

Minimum fixed deterministic replicate mean:

r
min
	​

U
fixed,det,r
F
	​

≥0.85.
Random process

For each capacity:

LCB
95
	​

(U
random,det,C
F
	​

)≥0.90,
LCB
95
	​

(E
random,det,C
F
	​

)≥0.85,
LCB
95
	​

(P
random,det,C
F
	​

)≥0.85,

where E is minimum four-step event-window utility and P is minimum event-delimited process-segment utility.

Factorized process transport:

LCB
95
	​

(U
random,det,C
F
	​

−U
fixed,det,C
F
	​

)≥−0.05.

Pooled random stochastic:

LCB
95
	​

(U
random,stoch
F
	​

)≥0.80.

Minimum random deterministic replicate mean:

r
min
	​

U
random,det,r
F
	​

≥0.85.

These are the same utility, stochastic, event-window, segment, transport, and replicate-stability boundaries used by G36.

Equality passes at all non-strict absolute floors.

4.5 Joint-minus-factorized noninferiority

Factorized sufficiency additionally requires:

Deterministic utility

For every capacity:

UCB
95
	​

(Δ
fixed,det,C
U
	​

)≤0.05,
UCB
95
	​

(Δ
random,det,C
U
	​

)≤0.05.
Stochastic utility

Equal-capacity-pooled:

UCB
95
	​

(Δ
fixed,stoch
U
	​

)≤0.05,
UCB
95
	​

(Δ
random,stoch
U
	​

)≤0.05.
Random local performance

For every capacity:

UCB
95
	​

(E
random,det,C
J
	​

−E
random,det,C
F
	​

)≤0.05,
UCB
95
	​

(P
random,det,C
J
	​

−P
random,det,C
F
	​

)≤0.05.
Primary estimand
UCB
95
	​

(Δ
coh
	​

)≤0.05.

Equality at 0.05 supports noninferiority.

4.6 Confident failure predicates

FACTORIZED_ACCESS_CONFIDENT_FAIL holds if any corresponding:

deterministic utility UCB is below 0.90;

event-window UCB is below 0.85;

process-segment UCB is below 0.85;

stochastic utility UCB is below 0.80;

random-minus-fixed UCB is below −0.05;

registered minimum replicate statistic is below 0.85.

MATERIAL_COHERENCE_LOSS holds if any of the following is strict:

LCB
95
	​

(Δ
coh
	​

)>0.05,

or any registered fixed/random deterministic capacity contrast, pooled stochastic contrast, event-window contrast, or process-segment contrast has:

LCB
95
	​

(Δ)>0.05.
4.7 Non-rescuing diagnostics

The following may be reported but cannot select or rescue a branch:

realized frequency with which two coordinate streams accidentally choose the same snapshot;

realized frequency of identical row permutations;

fraction of factorized rows that exactly match any legal G36 donor row;

cross-coordinate covariance or mutual-information estimates;

action-distribution displacement;

first-layer weights attached to coordinates 6:10;

event-type, active-count, or process-order strata.

No diagnostic may relabel an earlier first-match outcome.

5. PAIRING_CONFIDENCE_AND_EVIDENCE
5.1 Formal inventory

The G36 joint reference contributes no new transitions.

New G37 evidence:

replicates=3
capacities=6|8|12
factorized_cells_per_replicate_capacity=4
total_new_cells=36
episodes_per_cell=128
new_evaluation_episodes=4608
H=48
new_real_transitions=221184
training_transitions=0
optimizer_steps=0
episode_exclusions=none
bootstrap_resamples=10000

The inherited G36 package used the same three-replicate, capacity-6/8/12, 128-episode support and whole-episode confidence unit.

5.2 Exact pairing unit

The paired scientific unit is:

(replicate, capacity, process, action_mode, episode_id)

For each unit, joint and factorized sides retain the same:

G35 CS final checkpoint;

G32/G34 source ledger;

local and global episode identity;

profile;

event times and order;

count trajectory;

lifecycle cohorts;

current fields 0:6;

critic state;

reward;

member-owned stochastic action noise.

Only the surrogate generation law changes.

5.3 Reference treatment

The G36 joint side is read from its exact formal artifact. Its reward, roster, event-window, and process-segment quantities are recomputed from its serialized 48-step traces before entering G37 analysis.

The factorized side serializes equivalent 48-step evidence. Summaries may not be trusted without trace recomputation.

The G36 reference donor tape and G37 factorized tape are fixed nuisance objects. They are not resampled independently from their corresponding episode rows.

5.4 Confidence construction

Use:

bootstrap_seed=10364037
bootstrap_resamples=10000
confidence_interval=95_percent_percentile

Generate one hierarchical paired plan and reuse it for every absolute and comparative quantity:

Resample the three paired replicate blocks with replacement.

Within each selected replicate and capacity, resample all 128 whole episode IDs.

Retain the corresponding:

G36 joint reference;

G37 factorized execution;

fixed and random processes;

deterministic and stochastic modes;

reward and roster traces;

event-window and process-segment values.

Never independently resample:

members;

time rows;

events;

lifecycle rows;

proxy columns;

joint and factorized branches;

fixed and random mates;

deterministic and stochastic mates.

Pooled values weight capacities 6, 8, and 12 equally.

No episode, seed, coordinate, event type, or donor draw may be excluded after observation.

6. WITNESSES_AND_IDENTIFIABILITY
6.1 Positive pass witness

Consider a checkpoint whose action-producing path ignores coordinates 6:10 and uses current load and target mix only:

a
(0)
=tanh(2L−1),a
(1)
=tanh(2M−1).

The previously registered current-state witness has minimum utility 0.94048 over the full load/mix support. For such a checkpoint:

U
J
=U
F
,E
J
=E
F
,P
J
=P
F
,

and:

Δ
coh
	​

=0.

All factorized access and noninferiority gates can therefore pass for their intended reason.

6.2 Confident-fail witness

Consider a checkpoint that emits the constructive action only when donor fields satisfy a source-coherent relation, for example:

48
age
	​

≤
47
time
	​

+
48
1
	​

,

and whose two previous-action coordinates satisfy a learned joint gate.

G36 joint snapshots generally preserve the legal lifecycle relationship between age and donor time and preserve the paired previous action. G37 factorization can combine:

age from one donor boundary;

previous-action-0 from another;

previous-action-1 from another;

time from another.

Every scalar remains in exact empirical donor support, but the joint gate may fail. If this causes absolute access failure or:

LCB
95
	​

(Δ
coh
	​

)>0.05,

the load-bearing branch is reachable for the intended reason.

6.3 Source/reference-failure witness

Any of the following reaches SOURCE_OR_G36_REFERENCE_FAILURE_G37:

the exact G36 formal branch cannot be reproduced;

the G36 evaluation digest or analysis digest differs;

the accepted G35 CS checkpoint binding fails;

the G36 reference cells do not retain their registered access;

inherited episode identities or process signatures do not close;

the exact G36 donor-bank population cannot be reconstructed.

No factorized result is interpreted when the reference is invalid.

6.4 Mixed/underpowered witness

Examples:

factorized absolute access passes
Delta_coh CI95=[0.03,0.07]

or:

factorized utility CI95 crosses 0.90
but its UCB remains above 0.90

Neither supports factorized sufficiency nor confidently identifies coherence loss.

6.5 Why this is not an out-of-support scalar test

Every factorized coordinate column comes directly from the exact G36 active-count-conditioned donor bank. Thus failure cannot be attributed to:

a coordinate outside [0,1];

an unseen marginal value;

a constant start-state vector;

invalid inactive rows;

a new active count.

The factorized joint tuple may be absent from the source’s joint empirical support by design. Therefore a negative result identifies dependence on joint distributional coherence, not merely univariate support—and still does not distinguish semantic temporal use from generic multivariate OOD sensitivity.

6.6 Identifiability ceiling

G37 identifies only the necessity or dispensability of:

shared donor snapshot
+ shared donor member permutation
across the four history-proxy columns

It does not identify:

any individual coordinate;

within-column member dependence;

global shared time as a separate factor;

whether a retrained policy would adapt to factorization;

whether coordinates 6:10 can be deleted;

whether the task requires history.

7. FIRST_MATCH_TRUTH_TABLE

Define:

OPERATIONAL_VALID
Exact artifact, checkpoint, bank ordering, factorized seed/tape, actor-only transform, RNG, cell, trace, lifecycle, zero-step, finite-value, marginal-law, and authority invariants pass.

SOURCE_VALID
Exact G32 fixed and G34-P0 random source laws, episode support, process signatures, denominators, and lifecycle predicates pass.

G36_REFERENCE_VALID
Exact formal G36 package, accepted branch, G35 CS checkpoint binding, access metrics, traces, and digests validate.

FACTORIZED_ACCESS_PASS
Every absolute gate in Section 4.4 passes.

FACTORIZED_ACCESS_CONFIDENT_FAIL
The confident-failure dual in Section 4.6 holds.

COHERENCE_NONINFERIOR
Every joint-minus-factorized UCB in Section 4.5 is at most 0.05.

MATERIAL_COHERENCE_LOSS
Any strict lower-bound condition in Section 4.6 holds.

Priority	Terminal branch	Exact predicate	Smallest scientific update
1	INVALID_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37	OPERATIONAL_VALID=false	No scientific update. Repair only the exact operational corruption under the unchanged contract.
2	SOURCE_OR_G36_REFERENCE_FAILURE_G37	Operationally valid and either SOURCE_VALID=false or G36_REFERENCE_VALID=false	Close this exact evidence package without interpreting factorized donor coherence. Preserve G36 unchanged.
3	FACTORIZED_HISTORY_PROXY_SUFFICIENT_G37	Source/reference valid, FACTORIZED_ACCESS_PASS=true, and COHERENCE_NONINFERIOR=true	Support exact-checkpoint sufficiency of the frozen factorized marginal law. Retire shared cross-column donor coherence only inside G37-P0.
4	JOINT_DONOR_COHERENCE_LOAD_BEARING_G37	Source/reference valid and either FACTORIZED_ACCESS_CONFIDENT_FAIL=true or MATERIAL_COHERENCE_LOSS=true	Retain G36 shared-snapshot/shared-alignment coherence as load-bearing for these exact checkpoints relative to G37’s factorized law. Do not infer task-level history necessity.
5	MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37	Every remaining valid numerical pattern	Preserve both explanations and close G37-P0 without seed, margin, donor, episode, checkpoint, or evidence-volume rescue.

Branch evaluation stops at the first match.

Equality semantics:

absolute floor equality                 = pass
random-minus-fixed LCB = -0.05          = pass
UCB(joint-factorized) = 0.05            = noninferior pass
LCB(joint-factorized) > 0.05            = material-loss pass

No descriptive diagnostic may rescue or relabel an earlier branch.

8. EVIDENCE_COMPLEXITY_AND_AUTHORITY
8.1 Search complexity
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

The donor bank and factorized columns are produced by direct finite-array selection and permutation. They introduce no hypothetical environment trajectory or candidate search.

This is within the project’s hard evidence-complexity boundary.

8.2 Bounded nonformal preflight

Freeze:

replicates=1
capacities=6|8|12
factorized_cells_per_capacity=4
episodes_per_cell=8
bootstrap_resamples=250
optimizer_steps=0

New real transitions:

1×3×4×8×48=4,608.

The nonformal package must additionally validate:

exact formal G36 reference and artifact digests;

exact G35 CS checkpoint binding;

byte-identical G36 donor-bank population and ordering;

active-count coverage;

four independent coordinate streams;

exact coordinate marginal-law construction;

actor-only no-target-history reads;

fixed/random and deterministic/stochastic tape reuse;

paired action-noise digests;

zero checkpoint drift;

complete 48-step trace recomputation;

branch arithmetic and equality semantics.

It may return only:

NONFORMAL_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_COMPLETE

or:

NON_EXECUTABLE_EVIDENCE_DESIGN

The complete nonformal evaluate/analyze package must finish within 1,200 seconds.

8.3 Formal inventory
formal_replicates=3
formal_capacities=3
formal_factorized_cells=36
formal_episodes_per_cell=128
formal_evaluation_episodes=4608
formal_real_transitions=221184
formal_optimizer_steps=0
bootstrap_resamples=10000

The read-only G36 reference contributes zero new transitions.

8.4 Wall-clock projection

Record separately:

T_evaluate_nonformal
T_analyze_nonformal

Freeze the conservative projection:

T
projected,formal
	​

=1.25(48T
evaluate,nf
	​

+40T
analyze,nf
	​

).

Formal evaluation is admissible only if:

T
projected,formal
	​

≤28,800 seconds.

The nonformal total must also remain at or below 1,200 seconds. Exceeding either boundary returns NON_EXECUTABLE_EVIDENCE_DESIGN, costs zero scientific iterations, and is not an algorithm result. The project explicitly caps nonformal work at 20 minutes and formal work at eight hours.

8.5 Authority sequence

Before formal evaluation:

PM technically accepts one exact implementation.

A pushed commit-bound G37 code-science index identifies every claim-bearing path.

External Pro returns ALIGNED from the G37 code-science alignment audit.

One exact same-source-commit bounded preflight validates and projects within the cap.

The formal runner requires:

CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_FORMAL_AUTHORIZATION_V1

Formal artifacts bind both preflight digests, the exact G36 reference root, the G36/G35 artifact digests, and the aligned source commit.

This disposition supplies no implementation or formal authority.

9. CODE_SCIENCE_MAPPING
Scientific field	Existing surface or one minimal new G37 symbol	Binding correspondence
Exact donor population	G36HistoryProxyDonorBank	Reuse byte-identical bank values, ordering, seeds, source weighting, and active-count grouping.
Factorized column law	minimal new G37FactorizedHistoryProxyTape	Four independent snapshot selections and four independent row permutations under the exact seed law; cache excludes process and mode.
Marginal-law certificate	minimal new validate_g37_factorized_marginals	Verifies every coordinate column is an exact selected/permuted G36 donor column and no reweighting, clipping, or rejection occurs.
Actor-only input construction	build_g36_actor_input_without_history and apply_g36_actor_history_proxy_transform	Preserve actor 0:6, write G37 bundle to active 6:10, leave inactive rows zero, and never read target history fields.
Exact checkpoint	G36 runner’s _g35_reference and _load_cs_checkpoint	Strict-load exact replicate-specific G35 CS final checkpoints at capacities 6/8/12.
Joint-donor reference	minimal new g37_g36_reference using the G36 artifact validator	Read and validate the exact formal G36 package; do not rerun joint donor cells.
Fixed/random source	G35 make_process_ledgers, G32 fixed environment, and G34 random environment	Preserve exact episode identities, source values, event laws, count trajectories, and lifecycle ownership.
Factorized execution	minimal new evaluate_g37_factorized_history_proxy	Reuse G36 actor-only evaluator semantics with the factorized tape and unchanged critic/action stream.
Action-noise pairing	G35 formal evaluation seed block and G32 member-owned noise generator	New stochastic cells reproduce the exact G36 reference action-noise tensors.
Trace metrics	G34/G36 trace-evidence helpers	Recompute utility, event-window, process-segment, and roster predicates from serialized traces.
Confidence	minimal G37 wrapper over the G36 hierarchical-plan pattern	One paired replicate/whole-episode plan, seed 10364037, reused across every absolute and comparative estimand.
First-match result	minimal new select_g37_result_branch	Implements the exact priority and inclusive/strict comparisons in Section 7.
Preflight and authority	minimal G37 configuration/preflight validator	Freezes 4,608 nonformal and 221,184 formal transitions, source/reference digests, stage-time projection, and dedicated-token gate.

The existing G36 implementation already provides the exact donor-bank population, active-count-conditioned joint tape, actor-only no-read path, checkpoint/source binding, trace recomputation, paired confidence plan, and zero-training inventory that G37 must preserve.

Scientific and frozen

exact G36 bank population and order;

factorized column law;

active-count conditioning;

G37 seeds and stream ownership;

target-history independence;

joint-reference binding;

checkpoint and episode support;

four new cell identities;

pairing and action noise;

estimands and 0.05 margin;

access gates;

confidence unit;

branch order;

transition and wall-clock bounds.

Implementation-only

file and class names beyond the minimal symbols;

array storage;

vectorization;

donor-bank caching;

serialization format;

telemetry layout;

batching;

proof-sized test organization.

Scientifically nonconforming realizations include:

drawing four scalar constants instead of donor columns;

drawing all four columns from one snapshot;

applying one common row permutation;

requiring selected snapshots to be distinct;

reweighting the donor bank;

sampling by target process, event, time, load, mix, or lifecycle identity;

altering the critic;

rerunning the G36 reference;

changing action noise;

adding per-coordinate post hoc branches.

10. ONE_NEXT_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary becomes eligible only after PM has technically accepted one exact pushed implementation.

Its sole scientific question is:

Does the accepted implementation instantiate the exact G36-bank-preserving four-column factorization, independent snapshot/permutation streams, target-history-independent actor-only substitution, exact read-only G36 reference, G35 checkpoint and episode binding, four-cell zero-training inventory, paired action streams, inherited access gates, joint-minus-factorized noninferiority estimands, whole-episode confidence plan, and first-match semantics frozen here, without creating another route to either conclusion-bearing branch?

It is a read-only contract diff. It may not add or alter a donor population, factorization law, seed, checkpoint, source, margin, evidence volume, confidence unit, or result branch.

This response authorizes no implementation, Git operation, nonformal exercise, formal evaluation, monitoring, or successor child.

11. 中文简报

本轮裁决是：

IDENTIFIABLE_BOUNDED_FACTORIZED_HISTORY_PROXY_COHERENCE_G37_DESIGN

G37 可以形成一个有效的零训练比较，但要精确说明它破坏的是什么。

G36 还保留了什么

G36 已证明，目标 episode 的真实：

time
lifecycle age
previous action 0
previous action 1

可以被一个独立的 source-valid donor snapshot 替换。

但 G36 一次抽取的是一个完整 donor roster snapshot，因此四列仍共享：

同一个 donor 时刻；

同一个 lifecycle snapshot；

同一个成员排列；

同一个 previous-action pair；

同一套 roster-level age/time/action 结构。

G37 检查的就是这层 joint coherence 是否仍然 load-bearing。

G37 factorized donor

对于当前 active count n，G36 bank 中每个样本是一个：

n×4

的完整 donor snapshot。

G37 对四列分别执行：

独立抽取一个 donor snapshot；

独立生成一个 active-row permutation；

只取该 snapshot 的一列；

将四列拼成新的 n×4 actor proxy。

因此：

age              来自 snapshot A
previous-action0 来自 snapshot B
previous-action1 来自 snapshot C
time             来自 snapshot D

每一列自身的 active-count-conditioned empirical distribution 与 G36 完全相同，但四列不再共享同一个 snapshot 或成员对应关系。

需要保留一个精确边界：

G37 破坏的是跨列的 shared-snapshot/shared-member coherence，不是每列内部的所有 roster dependence。

例如 time 列在 donor snapshot 中本来就是全 roster 共享值，G37 仍保留这一列内部结构。正结论不能写成“所有 roster-level history structure 都被消除”。

主估计量
Δ
coh
	​

=U
joint donor
	​

−U
factorized donor
	​

.

margin 固定为：

0.05.

factorized branch 必须同时满足：

fixed/random deterministic access；

fixed/random stochastic access；

random event-window；

process-segment；

random-minus-fixed transport；

replicate stability；

每个 capacity 与 pooled 的 joint-minus-factorized UCB 均不超过 0.05。

正负结论边界

若通过：

FACTORIZED_HISTORY_PROXY_SUFFICIENT_G37

只能说明：

对 exact G35 CS checkpoints，在冻结的 G37 factorized marginal law 下，不需要 G36 donor 的跨列 joint coherence。

不能说明：

四个模型坐标可以删除；

任意噪声安全；

time/age/previous action 分别无用；

task 全局 memoryless；

所有重新训练策略都不需要历史。

若失败：

JOINT_DONOR_COHERENCE_LOAD_BEARING_G37

只能说明：

exact checkpoints 依赖 G36 joint donor 的 coherence 或 distributional consistency。

不能说明 task 理论上需要历史，也不能确定是哪一个字段或哪一种关系在起作用。

证据规模
training=none
H=48
K_search=0
hypothetical transitions=0
new formal cells=36
new formal episodes=4608
new formal transitions=221184
optimizer steps=0
bootstrap=10000

nonformal 为 4,608 transitions，必须在 20 分钟内完成；正式 evaluate/analyze 必须投影并限制在 8 小时内。

下一边界是：

CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_CODE_SCIENCE_ALIGNMENT_AUDIT

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码或计算。
