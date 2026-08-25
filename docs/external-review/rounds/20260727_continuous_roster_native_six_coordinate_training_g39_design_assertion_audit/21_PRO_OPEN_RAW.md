1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=
IDENTIFIABLE_FUNCTION_MATCHED_NATIVE_SIX_TRAINING_G39_DESIGN

source_id=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_P0
training_arms=CONST10_FOLD6|NATIVE6_CS
fresh_paired_training=true
initial_policy_functions_equal=true
policy_function_classes_equal=true
parameter_count_equality=false_intended_treatment
const10_extra_trainable_scalars=136
native_standard_initialization_claim=false
task_level_history_necessity_identifiable=false

A conclusion-bearing comparison can be frozen.

G38 established that its constant-input ten-coordinate training route can be folded exactly into a true six-coordinate deployment actor: both arms passed access, all 45 fold-equivalence cells had zero recorded error, and the primary FULL10−FOLD6 CI95 was [-0.01008621, -0.00312729, 0.00841468]. The one explicit unresolved unit was that FOLD6 still trained with four constant columns, 136 redundant weights and their Adam states.

G39 tests precisely that unit:

Does the redundant constant-coordinate parameterization improve finite-budget optimization, or can an initially function-identical native six-coordinate graph learn the same registered capability without those parameters and without a post-training fold?

The comparison is identifying because the two actor parameterizations have the same representable policy-function class. The constant columns add no actor information and no additional policy expressivity; they only change optimization coordinates and Adam state.

A positive G39 result may support native-six training sufficiency only under the exact function-matched initialization, Adam configuration, source family and finite budget frozen below.

A negative result may support only a finite-budget optimization or access advantage for the redundant constant-input parameterization. It cannot establish:

history-information necessity;

six-coordinate function-class inadequacy;

optimizer-independent superiority;

equivalence or non-equivalence under another initialization or optimizer.

2. EXACT_CONST10_NATIVE6_GRAPHS_AND_TREATMENT
2.1 Shared actor information

For every active member i at step t, both arms receive the same varying actor vector:

x
i,t
	​

∈R
6
,

ordered as:

0:2  capability coordinates
2    anonymous presentation priority
3    current load
4    current target mix
5    log1p(active_count)

Both arms also receive the identical:

active mask
active-member aggregation
anonymous routing order
active-fraction autoregressive prefix

Neither arm reads the environment’s actual actor-side:

lifecycle age
previous action 0
previous action 1
normalized physical time

The centralized critic remains unchanged and receives the true registered six-coordinate critic state, including true normalized time. The environment continues to maintain age, previous actions and lifecycle ownership internally.

The G38 implementation already separates the six retained actor coordinates from the four removable fields and confines raw actor observations to two affine paths.

2.2 Registered constant

Freeze:

c=(
2
1
	​

,
2
1
	​

,
2
1
	​

,
47
24
	​

).

For active rows only:

CONST10_FOLD6 actor input = [x, c]
NATIVE6_CS actor input    = x

Inactive rows remain exactly zero. No actual-history value may be materialized, validated, hashed or copied by either arm’s actor-input path.

2.3 CONST10_FOLD6 graph

The constant route uses the accepted G38 graph.

Its only two raw-input affine maps are:

q
i,t
C
	​

=W
m
C
	​

[x
i,t
	​

,c]+b
m
C
	​

,W
m
C
	​

∈R
32×10
,

and:

r
i,t
C
	​

=W
r
C
	​

[x
i,t
	​

,c]+b
r
C
	​

,W
r
C
	​

∈R
2×10
.

The member affine is followed by the unchanged member-encoder tail. The action readout is added to the unchanged no-carry action graph.

No third raw-input path is permitted. In particular, raw actor input may not independently enter:

normalization;

context;

GRU gates;

delayed residual;

action head;

routing;

prefix construction;

critic;

immediate or successor baseline;

G31 credit computation.

The accepted G38 graph already identifies member_input: Linear(10,32) and current_readout: Linear(10,2) as the only raw-observation consumers.

2.4 NATIVE6_CS graph

The native route has the same downstream graph, widths, nonlinearities, action distribution, critic and credit modules, but its two raw-input affines are six-coordinate from initialization:

q
i,t
N
	​

=W
m
N
	​

x
i,t
	​

+b
m
N
	​

,W
m
N
	​

∈R
32×6
,
r
i,t
N
	​

=W
r
N
	​

x
i,t
	​

+b
r
N
	​

,W
r
N
	​

∈R
2×6
.

It has:

no constant-coordinate constructor
no ten-coordinate actor tensor
no donor or filler
no removable-column weights
no post-training fold

All modules after the two raw-input affines have the same key, shape and computation as CONST10_FOLD6.

2.5 Exact parameter treatment

The semantic parameter-key set is identical across arms. Only these two tensor shapes differ:

Tensor	CONST10_FOLD6	NATIVE6_CS	Difference
member-input weight	32×10	32×6	128
current-readout weight	2×10	2×6	8
Total			136

Bias dimensions remain identical.

Freeze:

trainable_parameter_count_CONST10
    = trainable_parameter_count_NATIVE6 + 136

parameter_tensor_count_CONST10
    = parameter_tensor_count_NATIVE6

semantic_parameter_key_order_CONST10
    = semantic_parameter_key_order_NATIVE6

The unequal scalar count is the intended scientific treatment. Prohibited attempts to equalize it include:

dummy parameters;

frozen padding weights;

widening another native module;

changing hidden width;

learning-rate rescaling;

extra native optimizer steps;

parameter-count-normalized loss coefficients.

2.6 Exact function-class equivalence

Partition each constant-route affine:

W
C
=[W
x
C
	​

W
c
C
	​

].

Define the fold map:

F(W
x
C
	​

,W
c
C
	​

,b
C
)=(W
x
C
	​

,b
C
+W
c
C
	​

c).

For every six-coordinate input x:

W
C
[x,c]+b
C
=W
x
C
	​

x+(b
C
+W
c
C
	​

c).

Conversely, every native affine (W
N
,b
N
) has a constant-route lift:

W
x
C
	​

=W
N
,W
c
C
	​

=0,b
C
=b
N
.

Therefore:

Π
CONST10(c)
	​

=Π
NATIVE6
	​

	​


for the frozen no-carry actor graph.

This rules out expressivity as an admissible explanation for a valid arm difference. G39 tests only finite-budget parameterization and optimizer geometry.

The same algebra was used in G38 to remove exactly 136 weights while preserving the complete deployed actor function.

3. FUNCTION_MATCHED_INITIALIZATION_AND_OPTIMIZER_STATE
3.1 Canonical initialization construction

For each replicate:

Initialize CONST10_FOLD6 once from the registered model seed.

Construct NATIVE6_CS deterministically from that state.

Do not independently sample a native actor initialization.

For the two raw-input affines:

W
m
N
	​

=W
m
C
	​

[:,0:6],
b
m
N
	​

=b
m
C
	​

+Last4(c,W
m
C
	​

[:,6:10]),
W
r
N
	​

=W
r
C
	​

[:,0:6],
b
r
N
	​

=b
r
C
	​

+Last4(c,W
r
C
	​

[:,6:10]).

Last4 is the frozen fixed-order operation:

(c
0
	​

w
0
	​

+c
1
	​

w
1
	​

)+(c
2
	​

w
2
	​

+c
3
	​

w
3
	​

).

Every unaffected actor, critic, baseline, buffer and log_std tensor is copied bitwise.

Any constructor RNG used temporarily to allocate the native module must have its state restored before source, action or later model RNG is used.

3.2 Zero-checkpoint identity

Before training:

Fold(CONST10_zero).state_dict
    == NATIVE6_zero.state_dict

bitwise for every tensor.

The pre-fold constant state and native state need not have equal shapes, but their folded/native deployment checkpoints must be byte-identical.

3.3 Forced initial forward equality

On the first paired capacity-8 batch, before any optimizer step, use identical:

six-coordinate actor inputs
active masks
critic states
zero hidden tensors
sampling noise
source ledgers

Require:

Quantity	Gate
critic and value tensors	bitwise equal
log_std	bitwise equal
pre-tanh means	max abs error <=1e-7
actions	max abs error <=1e-7
autoregressive prefix sums	max abs error <=1e-7
token log probabilities	max abs error <=1e-6
inactive actions/likelihoods	exact zero
next hidden state	exact zero
3.4 Forced initial trajectory equality

The first eight-episode training batch is collected for both arms before either update. It doubles as the initial trajectory audit and adds no extra environment interactions.

Require over all 48 steps:

source ledgers                  exact
active-mask traces              exact
critic-state traces             exact
membership edits                exact
roster-size traces              exact
reward traces                   max abs error <=1e-7
episode utilities               abs error <=1e-7
actions                         max abs error <=1e-7
pre-tanh actions                max abs error <=1e-7
prefix sums                     max abs error <=1e-7
token log probabilities         max abs error <=1e-6
lifecycle validity              exact

Failure of any initial function or trajectory gate is operational invalidity, not a scientific arm result.

3.5 Live-gradient and reparameterization audit

Using the actual inherited fast and return-to-go objectives on that first batch, before any update, every registered trainable group in both arms must have:

finite_gradient=true
max(fast_gradient_norm, rtg_gradient_norm)>1e-12

For each affected affine and each constant coordinate k∈{0,1,2,3}, require:

∇
W
x
C
	​

	​

L≈∇
W
N
	​

L,
∇
b
C
	​

L≈∇
b
N
	​

L,
∇
W
c,k
C
	​

	​

L≈c
k
	​

∇
b
N
	​

L,

with maximum absolute relation error <=1e-6 for both the fast and RTG objectives.

Additionally:

all CONST10 removable columns live >1e-12
both NATIVE6 effective biases live >1e-12
all values finite

This verifies that the redundant columns are genuine trainable optimization coordinates rather than dead or decorative parameters.

3.6 Adam-state semantics

Both arms use separate Adam instances with identical hyperparameters:

beta1=0.9
beta2=0.999
eps=1e-8
weight_decay=0
gradient_clipping=none
minibatches=none

Before the first step:

optimizer_state_CONST10={}
optimizer_state_NATIVE6={}

The fast optimizer is discarded at the inherited phase transition. Both arms then instantiate fresh, empty direction-balanced actor and critic optimizers at the same boundary.

Equal optimizer exposure means:

The same number of semantically matched Adam.step() calls is made in every phase.

It does not mean equal scalar-parameter updates.

Per arm and replicate:

fast actor optimizer steps       = 200
RTG actor optimizer steps        = 200
RTG critic optimizer steps       = 200
total optimizer steps            = 600

The intentional treatment implies that each CONST actor optimizer owns:

136 additional trainable scalar weights
136 additional first-moment elements
136 additional second-moment elements

Across its 400 actor updates per replicate, CONST performs:

136×400=54,400

additional scalar-update events. Across three formal replicates:

163,200.

No budget compensation is applied. Those additional coordinates and moments are exactly what G39 tests.

4. PAIRED_TRAINING_AND_SEED_OWNERSHIP
4.1 Fresh seed block

Freeze:

model_initialization_seed_base=10391000
training_ledger_seed_base=10392000
training_action_seed_base=10393000
evaluation_base_ledger_seed_base=10394000
evaluation_process_seed_base=10395000
evaluation_action_seed_base=10396000
initial_gradient_probe_seed_base=10397000
bootstrap_seed=10398039
nonformal_seed_offset=900000

For formal replicate r∈{0,1,2}, add r once to every nonbootstrap seed.

For the bounded nonformal exercise, add 900000 to every seed, including the bootstrap seed.

4.2 Shared RNG ownership

Within a replicate, both arms share:

the canonical CONST initialization seed;

the deterministic initial-state projection;

G32 training episode IDs and ledgers;

training action-noise tensors;

G34 fixed/random evaluation base ledgers;

event-time tuples, event orders and profiles;

evaluation action-noise tensors;

bootstrap indices.

There is no arm-owned environment or action RNG.

The only arm-owned state is its optimizer state and evolving parameters.

Parameter-count inequality must not advance or shift:

training ledgers
evaluation ledgers
process assignments
action noise
bootstrap plan

The G32 source already uses episode/member-owned streams, and G34 pairs fixed and random branches through the same base ledger and action stream.

4.3 Formal training exposure

Per arm and replicate:

training_capacity=8
fast_updates=100
return_to_go_updates=100
environments_per_update=8
episode_length=48
ppo_passes=2
gamma=0.99
learning_rate=1e-3
initial_log_std=-1.0
checkpoint_selection=final_only
episode_exclusions=none

Both arm trajectories must be completely materialized before either optimizer is stepped.

The update procedure is:

paired trajectory collection
→ validate both trajectories
→ update CONST10
→ update NATIVE6

The update order is implementation-only provided:

no optimizer or model RNG is consumed;

no tensor, buffer or optimizer state is shared between arms;

changing update order in a proof-sized check leaves the mate’s inputs and update unchanged.

The inherited G35/G38 route already uses paired collection before either arm updates and the same 100/100, eight-environment, two-pass budget.

4.4 Actor information independence

Throughout collection, replay, gradient audit, PPO and evaluation, both arms may read only the six registered varying actor coordinates.

Required complete-run counters for both arms:

actual_age_read_count=0
actual_previous_action_read_count=0
actual_actor_time_read_count=0
donor_or_proxy_read_count=0

The critic retains its unchanged true-current-state input.

5. ESTIMAND_CLAIM_CEILING_AND_GATES
5.1 Policy and claim sets

Let:

Π
C
	​


be the policies generated by the CONST training route and subsequent exact fold, and let:

Π
N
	​


be policies trained natively through the six-coordinate graph.

Structurally:

Π
C
	​

=Π
N
	​

.

G39 therefore cannot identify an expressivity advantage. It can identify only a difference in finite-budget optimization or access probability induced by parameterization.

5.2 Episode estimands

For episode e:

U
e
	​

=
48
1
	​

t=0
∑
47
	​

r
e,t
	​

.

For the four G34 random event times t
j
	​

:

E
e
	​

=
j
min
	​

4
1
	​

t=t
j
	​

∑
t
j
	​

+3
	​

r
e,t
	​

.

For the five event-delimited segments S
j
	​

:

P
e
	​

=
j
min
	​

∣S
j
	​

∣
1
	​

t∈S
j
	​

∑
	​

r
e,t
	​

.

All quantities are recomputed from serialized 48-step reward and roster-size traces.

5.3 Arm-level access contract

For each arm a∈{C,N}, define pooled learned gain:

G
a
	​

=U
a,final,random,det
−U
a,zero,random,det
.

ACCESS_PASS(a) requires:

Fixed process

For every C∈{6,8,12}:

LCB
95
	​

(U
C
a,final,fixed,det
	​

)≥0.90.

Also:

LCB
95
	​

(U
a,final,fixed,stoch
)≥0.80,

pooled with equal capacity weight, and:

minimum fixed deterministic replicate mean >=0.85
Random process

For every capacity:

LCB
95
	​

(U
C
a,final,random,det
	​

)≥0.90,
LCB
95
	​

(E
C
a,final,random,det
	​

)≥0.85,
LCB
95
	​

(P
C
a,final,random,det
	​

)≥0.85,
LCB
95
	​

(U
C
a,final,random,det
	​

−U
C
a,final,fixed,det
	​

)≥−0.05.

Also:

LCB
95
	​

(U
a,final,random,stoch
)≥0.80,

and:

minimum random deterministic replicate mean >=0.85

Finally:

LCB
95
	​

(G
a
	​

)>0.

Equality passes at every non-strict floor. Learned gain is strict.

These preserve the G38 access contract, which separately checked fixed/random deterministic utility, stochastic utility, event windows, process segments, process transport, replicate stability and final-minus-zero learning.

5.4 Confident access failure

ACCESS_CONFIDENT_FAIL(a) holds if any corresponding:

deterministic utility UCB is below 0.90;

event-window or segment UCB is below 0.85;

stochastic utility UCB is below 0.80;

random-minus-fixed UCB is below −0.05;

learned-gain UCB is at or below zero;

minimum replicate mean is below 0.85.

Every other nonpassing access pattern is underpowered.

5.5 Primary optimization estimand

For paired final random deterministic episodes:

Δ
opt,C,r,e
	​

=U
C,r,e
CONST10_FOLD6
	​

−U
C,r,e
NATIVE6
	​

.

The equal-capacity-weighted primary estimand is:

Δ
opt
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
opt,C,r,e
	​

]
	​


Positive values favor the redundant constant-coordinate parameterization.

Freeze:

δ
opt
	​

=0.05.
5.6 Native-six noninferiority

Define corresponding CONST10_FOLD6 − NATIVE6 differences for:

fixed deterministic utility, per capacity;

random deterministic utility, per capacity;

fixed stochastic utility, pooled;

random stochastic utility, pooled;

random event-window utility, per capacity;

random process-segment utility, per capacity.

NATIVE_SIX_NONINFERIOR requires:

UCB
95
	​

(Δ
opt
	​

)≤0.05

and every registered component UCB is also at most 0.05.

Equality at 0.05 passes.

5.7 Native-six sufficiency claim

NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39 requires:

ACCESS_PASS(NATIVE6_CS)=true
NATIVE_SIX_NONINFERIOR=true
INITIAL_FUNCTION_MATCH_PASS=true

It supports only:

A natively six-coordinate actor trained from the frozen function-matched projected initialization is sufficient under G39-P0, so the constant columns, their Adam moments and the post-training fold may be deleted.

It does not establish:

equivalence under a conventional independent native initializer;

optimizer-independent equivalence;

another constant’s equivalence;

critic reduction;

credit reduction;

task-level memorylessness.

5.8 Constant-overparameterized advantage

Define:

MATERIAL_CONST_ADVANTAGE⟺LCB
95
	​

(Δ
opt
	​

)>0.05

and:

LCB
95
	​

(Δ
opt,C
	​

)>0∀C∈{6,8,12}.

CONSTANT_OVERPARAMETERIZED_TRAINING_ADVANTAGE_G39 requires:

ACCESS_PASS(CONST10_FOLD6)=true
and either:
    ACCESS_CONFIDENT_FAIL(NATIVE6_CS)=true
or:
    MATERIAL_CONST_ADVANTAGE=true

The result must state which subpredicate fired.

It supports only:

The 136 redundant constant-column parameters and their Adam moments provide a finite-budget optimization or access advantage under the frozen G39 Adam/source/budget contract.

It cannot establish:

history-information necessity;

native-six inexpressivity;

benefit under SGD, another Adam configuration or another budget.

5.9 Non-rescuing diagnostics

Report, but never branch on:

effective-bias trajectories;

constant-column norms;

Adam moment norms;

first-step effective-bias update ratios;

training curves;

gradient cosine similarity;

final folded-parameter distance;

per-event or per-profile strata beyond registered gates;

comparison with historical G38 checkpoints.

6. PAIRING_CONFIDENCE_AND_EVIDENCE
6.1 Formal evaluation support

Freeze:

formal_replicates=3
capacities=6|8|12
episodes_per_cell=64
episode_exclusions=none

For every replicate and capacity:

draw 64 unique G34 time tuples;

retain one each of L/R/J/T;

preserve the three legal orders LRJT, LJRT, JLRT;

use order counts 22/21/21, rotating the 22-count order across replicates;

at capacity 8, use profile counts 22/21/21, rotating the 22-count profile across replicates through an independent stream;

over all three replicates, every order and every capacity-8 profile occurs exactly 64 times;

fixed and random branches share the same base ledger and episode identity.

This retains the G34-P0 process family while reducing the evidence inventory. G34’s defining source properties are held-out four-event times, at least five-step spacing, three legal orders and paired fixed/random base ledgers.

6.2 Evaluation cells

For each arm, replicate and capacity, evaluate exactly:

ZERO_RANDOM_DET
FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

Thus:

arms=2
cells_per_arm_capacity=5
cells_per_replicate=30
formal_total_cells=90

For CONST10_FOLD6, zero and final evidence uses the true folded six-coordinate checkpoints. Its pre-fold constant model exists only for the inherited one-trajectory fold-equivalence audit.

NATIVE6_CS is evaluated directly and has no fold path.

6.3 Formal inventory

Training:

2×3×200×8×48=460,800

real transitions.

Evaluation:

3×30×64×48=276,480

real transitions.

Total:

737,280
	​


Additional inventory:

formal_training_episodes=9600
formal_evaluation_episodes=5760
formal_optimizer_steps=3600
bootstrap_resamples=10000

This is materially below the G38 ceiling of 1,013,760 transitions while retaining all scientific cells.

6.4 Paired units

Training pair:

(replicate, phase, update, environment_slot, episode_id)

Evaluation pair:

(replicate, capacity, process, action_mode, episode_id)

Within a paired unit, preserve:

both arms;

zero/final mates;

fixed/random mates;

deterministic/stochastic mates;

ledgers;

event signatures;

member-owned action noise.

6.5 Confidence construction

Freeze:

bootstrap_seed=10398039
bootstrap_resamples=10000
confidence_interval=95_percent_percentile

Generate one hierarchical paired plan and reuse it for every absolute and comparative quantity:

Resample the three paired training replicates with replacement.

Within each selected replicate and capacity, resample all 64 whole episode IDs.

Retain every arm, checkpoint, process and action-mode mate for the selected episode.

Never independently resample members, time steps, events, arms, fixed/random branches, zero/final checkpoints or initialization paths.

Pooled quantities weight capacities 6, 8 and 12 equally.

7. WITNESSES_AND_IDENTIFIABILITY
Gate or branch	Smallest witness
Graph invalidity	A third raw-input path, a native ten-coordinate tensor, a dummy parameter or a parameter difference other than the two removable blocks
Initialization invalidity	Fold(CONST10_zero) differs from NATIVE6_zero, optimizer state is nonempty, or the first paired trajectory differs before an update
Live-treatment failure	Any constant column is detached/dead, native effective bias is dead, or the frozen gradient identities fail
Source/common-access failure	The constructive load/mix policy fails, or both arms confidently fail common access
Native-six sufficiency	Native access passes and CONST−NATIVE primary/component UCBs are all <=0.05
Constant-route advantage	CONST accesses and native confidently fails, or pooled CONST−NATIVE LCB is >0.05 with every capacity-specific LCB positive
Mixed/underpowered	Native accesses but Δ
opt
	​

 CI95 is [0.03,0.07], or a native absolute-access interval crosses its floor without confident failure
7.1 Access witness

The native policy class can ignore every field except current load and target mix and emit:

a
(0)
=tanh(2L−1),a
(1)
=tanh(2M−1).

This six-coordinate policy has a registered minimum utility of approximately 0.94048, above the 0.90 access floor. G38 used the same witness to establish that its reduced policy class is access-capable.

Therefore native failure cannot be attributed to lack of an access-capable function.

7.2 Exact optimization-only identifiability

Because:

Π
C
	​

=Π
N
	​

,

and because the initial deployed functions, critic, source, action noise and update counts are matched, a valid arm difference can be attributed only to the frozen finite-budget training parameterization, including:

redundant coordinates;

separate Adam moments;

effective-bias update geometry;

the resulting optimization trajectory.

It cannot be attributed to actor information or policy expressivity.

7.3 Remaining limitations

Even a native-six pass does not prove that:

an independently initialized native model is equivalent;

the result is optimizer independent;

a lower training budget would suffice;

the critic can lose time;

G31 credit is redundant;

other environments are history-free.

Even a CONST advantage does not prove that history fields are useful, because CONST never receives varying history fields.

8. FIRST_MATCH_TRUTH_TABLE

Define:

OPERATIONAL_VALID: exact graph inventory, parameter-count delta, function-matched initialization, empty optimizer state, gradient identities, paired exposure, finite updates, replay, lifecycle, checkpoints, traces, RNG, inventory and authority invariants pass.

SOURCE_VALID: exact G32/G34 laws, constructive witness, nonempty rosters, event support and denominators pass.

CONST_ACCESS_PASS, NATIVE_ACCESS_PASS: Section 5.3.

CONST_ACCESS_CONFIDENT_FAIL, NATIVE_ACCESS_CONFIDENT_FAIL: Section 5.4.

NATIVE_SIX_NONINFERIOR: Section 5.6.

MATERIAL_CONST_ADVANTAGE: Section 5.8.

Priority	Terminal branch	Exact predicate	Scientific update
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_TRAINING_G39	OPERATIONAL_VALID=false	No scientific update. Repair only the exact operational defect under the unchanged contract.
2	SOURCE_OR_COMMON_ACCESS_FAILURE_G39	Operationally valid and either SOURCE_VALID=false, or both CONST_ACCESS_CONFIDENT_FAIL=true and NATIVE_ACCESS_CONFIDENT_FAIL=true	Close this source/comparator package without interpreting optimizer geometry.
3	NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39	Source valid, NATIVE_ACCESS_PASS=true, NATIVE_SIX_NONINFERIOR=true, and initial function matching passes	Support native-six training under G39-P0 and delete constant columns, their Adam moments and the fold from the retained route.
4	CONSTANT_OVERPARAMETERIZED_TRAINING_ADVANTAGE_G39	Source valid, CONST_ACCESS_PASS=true, and either NATIVE_ACCESS_CONFIDENT_FAIL=true or MATERIAL_CONST_ADVANTAGE=true	Support a finite-budget optimization/access advantage for the redundant constant parameterization. Do not claim history necessity or native inexpressivity.
5	MIXED_UNDERPOWERED_NATIVE_SIX_TRAINING_G39	Every remaining valid pattern	Preserve both explanations and close G39-P0 without seed, budget, margin, initialization, optimizer, architecture or evidence-volume rescue.

Branch evaluation stops at the first match.

Equality semantics:

absolute access-floor equality       = pass
random-minus-fixed LCB = -0.05       = pass
learned-gain LCB > 0                  = strict
UCB(CONST-NATIVE) = 0.05              = noninferior pass
LCB(primary CONST-NATIVE) > 0.05      = material-advantage pass
initial numeric error = tolerance     = pass

No diagnostic may rescue or relabel an earlier branch.

9. EVIDENCE_COMPLEXITY_AND_AUTHORITY
9.1 Search complexity
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

There is no candidate search, rollout oracle, beam, tree or simulated counterfactual.

This lies strictly inside the project ceiling of O(H*K_search), fixed K_search<=16, no nested replanning and at most 16H hypothetical transitions.

9.2 Bounded nonformal preflight

Freeze:

replicates=1
arms=2
fast_updates_per_arm=10
return_to_go_updates_per_arm=10
environments_per_update=8
ppo_passes=2
evaluation_cells=30
evaluation_episodes_per_cell=6
bootstrap_resamples=250

The six evaluation episodes include each G34 order twice; capacity-8 profiles also occur twice each.

Training transitions:

2×20×8×48=15,360.

Evaluation transitions:

30×6×48=8,640.

Total:

24,000
	​


Optimizer steps:

120

The complete preflight must validate:

exact function-class graph inventory;

136-scalar parameter difference;

deterministic initialization projection;

bitwise folded-zero/native-zero identity;

full first-batch trajectory equality;

gradient identities and live paths;

empty and correctly separated Adam states;

paired collection before updates;

exact exposure;

source validity;

native and CONST checkpoint loading;

CONST fold closure;

all five result-branch witnesses;

formal wall-clock projection.

It may return only a nonformal completion or NON_EXECUTABLE_EVIDENCE_DESIGN.

The complete nonformal train/evaluate/analyze package must finish within:

1,200 seconds.
9.3 Formal wall-clock projection

Record separately:

T_train_nf
T_evaluate_nf
T_analyze_nf

Freeze:

T
projected,formal
	​

=1.25(30T
train,nf
	​

+32T
evaluate,nf
	​

+40T
analyze,nf
	​

).

The scale factors are exact:

training:   460800 / 15360 = 30
evaluation: 276480 / 8640  = 32
bootstrap:  10000 / 250    = 40

Formal execution is scientifically admissible only if:

T
projected,formal
	​

≤28,800 seconds.

Failure is:

NON_EXECUTABLE_EVIDENCE_DESIGN

and consumes no scientific iteration. The governing policy separately caps nonformal work at 20 minutes and formal work at eight hours.

9.4 Required authority sequence

Before formal training:

PM technically accepts one exact implementation.

A commit-bound code-science index identifies every claim-bearing path.

External Pro returns ALIGNED from the G39 code-science audit.

One same-source bounded preflight validates all three artifacts and the projection.

The formal runner requires a dedicated G39 token bound to:

the aligned source commit;

training/evaluation/analysis preflight digests;

the frozen G39 configuration.

This response grants none of those execution authorities.

10. CODE_SCIENCE_MAPPING
Scientific field	Existing surface or minimal G39 symbol	Binding correspondence
CONST graph	G38 G38FoldableMatchedCSPolicy, _G38RawInputAffine	Preserve the accepted constant-input ten-coordinate training route and fixed-order effective-bias kernel.
Native graph	new G39NativeSixCSPolicy	Same downstream graph; exactly Linear(6,32) and Linear(6,2) raw-input maps; no filler or fold.
Pair construction	new make_g39_function_matched_pair	Initialize CONST once, derive native retained weights/effective biases, copy every unaffected tensor.
Function-class map	new g39_const_to_native_state	Implements (W
x
	​

,W
c
	​

,b)↦(W
x
	​

,b+W
c
	​

c).
Initialization audit	new g39_initial_function_audit	Verifies folded-zero/native-zero identity and complete first-batch trajectory equality.
Gradient relation	new g39_reparameterization_gradient_audit	Uses actual fast/RTG losses and verifies live gradients plus the frozen analytic relations.
Optimizer inventory	new g39_optimizer_state_audit	Verifies empty initial states, semantic group equality, 136 extra CONST scalars and phase-specific moment ownership.
Six-coordinate source	G38 observe_g38_actor_source and collector pattern	Both arms receive only source coordinates 0:6; CONST appends constants internally.
CONST fold	G38 fold_g38_constant_actor_checkpoint	Produces the deployed CONST six-coordinate zero/final checkpoints; no post-fold update.
Training source	G32 fixed capacity-8 source	Exact profiles, reward, lifecycle and episode/member-owned RNG.
Evaluation source	G34 process-ledger surface	Exact fixed/random capacities 6/8/12, held-out event law and paired noise.
G31 credit	inherited realized-future-tail optimizer	Identical targets, actor update, critics, passes and phase boundaries.
Estimands	new G39 analyzer over inherited G38 metrics	Computes access, learned gain and CONST−NATIVE paired contrasts from serialized traces.
Confidence	new g39_bootstrap_plan	Three replicate blocks, 64 whole episodes per capacity, seed 10398039, one reused paired plan.
First match	new select_g39_result_branch	Implements the exact Section 8 priority and strict/inclusive comparisons.
Preflight/authority	G38 formal-preflight pattern plus G39 inventory	Binds 24,000 nonformal and 737,280 formal transitions, stage times, artifacts, source commit and dedicated token.

The G38 code provides the accepted two-affine graph, six-coordinate source boundary, exact fold and paired-training surfaces on which the G39 realization can be based.

Scientific and frozen

the two graph definitions;

exact 136-scalar treatment;

function-class equality;

initialization projection;

gradient identities;

Adam-state semantics;

seed block;

training and evaluation exposure;

64-episode formal support;

primary estimand and 0.05 margin;

access gates;

bootstrap unit;

first-match order;

transition and wall-clock bounds.

Implementation-only

file and class names beyond the minimal symbols;

tensor storage;

vectorization;

batching;

serialization layout;

telemetry organization;

temporary constructor mechanics;

test-file organization;

update order, provided no shared state or RNG exists.

Scientifically nonconforming realizations include:

independently initializing NATIVE6;

giving NATIVE6 dummy parameters;

changing another width to equalize parameter count;

reading actual history in either arm;

using different ledgers or action noise;

sharing Adam state;

retaining a filler in native deployment;

comparing pre-fold CONST rather than folded CONST in evaluation;

changing learning rate, gradient clipping, credit, source or evidence volume;

adding a post hoc parameter-count-normalized threshold.

11. ONE_NEXT_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary becomes eligible only after PM technically accepts one exact pushed implementation.

Its sole scientific question is:

Does the accepted implementation instantiate the exact function-class-equivalent CONST10/NATIVE6 graphs, 136-scalar intended treatment, deterministic effective-bias initialization map, empty and separate Adam states, live gradient relations, six-coordinate source boundary, paired G32/G34 exposure, folded-CONST versus native evaluation, 64-episode confidence inventory, CONST−NATIVE estimands and frozen first-match semantics without introducing an actor-information, expressivity, source, credit, optimization-budget or evidence route?

It is a read-only conformance diff. It may not alter:

graph width;

initialization map;

optimizer;

source;

seed;

sample count;

margin;

confidence unit;

branch order.

This disposition authorizes no implementation, Git operation, nonformal exercise or formal computation.

12. 中文简报

本轮裁决是：

IDENTIFIABLE_FUNCTION_MATCHED_NATIVE_SIX_TRAINING_G39_DESIGN

G39 可以形成有效比较。

核心问题

G38 已证明：

FOLD6 不读取真实 age、previous actions、actor time；

训练后可以精确删除 136 个 weights；

最终得到真正六输入部署 actor；

FULL10 与 FOLD6 都达到 access；

FULL10−FOLD6 的 CI95 为：

[-0.01009, -0.00313, 0.00841]

但 G38 训练时仍保留：

4 个常量输入列
136 个冗余 trainable weights
这些 weights 的 Adam 一阶矩
这些 weights 的 Adam 二阶矩
训练后 fold 操作

G39 只检查这些训练期对象是否有用。

两个 arm
CONST10_FOLD6
    六个变化输入 + 四个固定常量
    两个十输入 affine
    训练后精确 fold

NATIVE6_CS
    只接收六个变化输入
    两个六输入 affine
    从初始化开始没有常量列
    不需要 fold

其余全部相同：

no-carry actor
hidden width
active-set aggregation
log active count
active mask
autoregressive prefix
critic
G31 credit
reward
source
action distribution
interaction count
PPO passes
optimizer-step count
函数类完全相同

对于 CONST affine：

W=[W
x
	​

,W
c
	​

].

native 参数固定为：

W
native
	​

=W
x
	​

,b
native
	​

=b+W
c
	​

c.

因此两种参数化能表示的 policy function class 完全相同：

Π
CONST10(c)
	​

=Π
NATIVE6
	​

.

所以，若 CONST 最终胜出，不能解释为“六输入表达力不足”，只能解释为：

在冻结的 Adam、source 和训练预算下，冗余常量列及其独立 moments 改善了有限预算优化。

初始化

每个 replicate 只随机初始化 CONST 一次。NATIVE 由 CONST 确定性投影得到：

native retained weights = CONST 前六列
native bias = CONST bias + CONST 后四列 × c

所有其他 actor、critic、baseline 和 log_std tensors bitwise copy。

训练前必须证明：

fold 后的 CONST zero checkpoint 与 NATIVE zero checkpoint bitwise 相同；

pre-tanh、actions、value、prefix、log-prob 相同；

第一个完整 8-episode、48-step paired trajectory 相同；

两个 optimizer state 都为空；

CONST 的 136 个额外参数具有真实非零梯度。

Optimizer exposure

两个 arm 的 Adam.step() 次数相同，但 scalar 更新数有意不同。

每个 replicate：

fast actor steps = 200
RTG actor steps  = 200
critic steps     = 200

CONST 每个 actor step 多更新 136 个 scalars。三 replicate 总计多出：

163200 scalar-update events

这不是待修复的不匹配，而是 G39 的科学 treatment。

主估计量
Δ
opt
	​

=U
CONST10_FOLD6
	​

−U
NATIVE6
	​

.

margin 固定为：

0.05.

若 NATIVE 达到完整 access，且 pooled 与每个 component 的 CONST−NATIVE UCB 都不超过 0.05：

NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39

若 CONST 达到 access，而 NATIVE confident fail，或 pooled 差值 LCB 严格大于 0.05 且每个 capacity 方向均为正：

CONSTANT_OVERPARAMETERIZED_TRAINING_ADVANTAGE_G39

完整分支为：

INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_TRAINING_G39
SOURCE_OR_COMMON_ACCESS_FAILURE_G39
NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39
CONSTANT_OVERPARAMETERIZED_TRAINING_ADVANTAGE_G39
MIXED_UNDERPOWERED_NATIVE_SIX_TRAINING_G39
最小证据规模

正式训练仍保留三个 training replicates，但将每个 evaluation cell 从 128 个 episode 降到 64 个：

formal training transitions   = 460800
formal evaluation transitions = 276480
formal total transitions      = 737280
formal optimizer steps        = 3600
formal cells                  = 90
bootstrap                     = 10000

nonformal preflight：

24000 transitions
120 optimizer steps
30 cells
6 episodes per cell
250 bootstrap

复杂度保持：

H=48
K_search=0
hypothetical transitions=0
nested rollout=false
replanning=false

nonformal 必须低于 20 分钟，formal 投影必须低于 8 小时。

下一边界是：

CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_ALIGNMENT_AUDIT

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码或计算。