1. REGISTERED_DESIGN_CONFORMANCE
REGISTERED_DESIGN_CONFORMANCE=
CONFORMS_AFTER_EXACT_IDENTIFICATION_FREEZE_BELOW

The proposed G40 comparison is scientifically admissible. G39 has already isolated and retained a native-six-coordinate, no-carry actor while leaving two training-side objects unseparated: the true-current-state critic and the G31 realized-future-tail/direction-balanced credit package. Formal G39 showed that both function-matched training parameterizations accessed the source and that native-six training was noninferior; it supplied no ordinary-credit comparator.

The submitted G40 draft correctly freezes:

the native-six actor and actor information;

the true-current-state critic;

G32 capacity-8 fixed-process training;

G34-P0 fixed/random capacity-6/8/12 evaluation;

the primary sign convention U
G31
	​

−U
GAE1
	​

;

the 0.05 decision margin;

the five first-match outcomes;

H=48, K_search=0, and zero hypothetical search.

It also correctly states that auxiliary credit heads must be enumerated and that the design must be rejected if hidden actor/critic capacity remains unmatched.

The draft is not yet a complete frozen contract because it leaves open the baseline-head inventory, phase boundary, exact GAE target, auxiliary-head treatment, optimizer partition, seed law and evidence inventory. The contract below closes those fields.

One semantic correction is essential:

With λ=1 and terminal bootstrap zero, team GAE contains the complete realized discounted return. G40 therefore does not compare “future credit” against “primitive immediate credit.” It compares the G31 immediate/successor decomposition and direction-balanced gradient geometry against an ordinary single-stream Monte-Carlo-equivalent team GAE/PPO credit rule.

That distinction controls every permissible interpretation.

2. DESIGN_SCIENTIFIC_DISPOSITION
DESIGN_SCIENTIFIC_DISPOSITION=
IDENTIFIABLE_SHARED_FAST_ANCHOR_NATIVE_SIX_CREDIT_REDUCTION_G40_DESIGN

source_id=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_P0
training_arms=NATIVE6_G31|NATIVE6_TEAM_GAE1
design_compute=0
claim_level=source_local_second_phase_credit_package_reduction
end_to_end_GAE_from_random_initialization_claim=false
universal_temporal_credit_claim=false

A conclusion-bearing comparison can be frozen, but only as a shared-anchor branch comparison.

Exact scientific question

For each fresh replicate:

Train one common native-six checkpoint through the exact accepted G39 fast-access phase.

Clone that checkpoint, all critic and auxiliary-head tensors, and all buffers bitwise into two separately owned branch models.

Discard the common fast optimizer.

Start both branch optimizers empty.

Continue for the same number of paired updates using either:

the accepted G31 realized-tail/direction-balanced actor credit; or

ordinary shared-team GAE with γ=0.99,λ=1.

This isolates the specialized G31 branch-phase credit package. It avoids a second difference caused by giving G31 its accepted fast-access phase while forcing ordinary GAE to solve a different from-scratch optimization problem.

Positive claim ceiling

A result of:

ORDINARY_TEAM_GAE_CREDIT_SUFFICIENT_G40

may support only:

After the common accepted fast-access phase, ordinary single-stream team GAE1 is sufficient for the native-six G40-P0 route; the specialized realized-successor decomposition and direction-balanced branch phase may be deleted locally.

It may not establish:

that ordinary GAE learns the source from an independently initialized model without the common fast phase;

that future reward information is unnecessary;

that G31 was unnecessary on G17/G18;

that ordinary credit suffices on other delayed, partially observed or UAV sources.

Negative claim ceiling

A result of:

G31_REALIZED_TAIL_CREDIT_ADVANTAGE_G40

may support only:

Under the shared anchor, frozen Adam configuration, source and branch budget, G31’s specialized decomposition/gradient geometry supplies a finite-budget access or material utility advantage over the exact ordinary GAE1 null.

It may not establish universal temporal-credit necessity or prove that GAE’s return horizon is too short. With λ=1, both branch rules contain full-episode future-reward information.

Retain, replace, delete, add
Object	G40 treatment
Native-six actor and no-carry semantics	Retain exactly
Actor information, active set, count and prefix	Retain exactly
True-current-state critic	Retain exactly
Common fast-access phase	Retain and share before branching
G31 branch-phase credit	Treatment arm
Ordinary GAE1 branch-phase credit	Matched null
Immediate and successor auxiliary heads	Retain in both arms; shadow-only in GAE arm
New actor, critic or value capacity	None
New reward, observation or source field	None
Deployment module	None

The repository already records G31 as supported on its paired G17/G18 source while explicitly leaving its local necessity in the accepted native-six continuous-roster route open. G39’s success does not answer that question.

3. IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES
3.1 From-scratch phase confounding

Training G31 through its accepted fast phase while training the ordinary arm with GAE from initialization would change both:

the branch credit rule; and

the pre-branch optimization history.

A difference could not be attributed to the registered G31 branch package.

Frozen correction: one common fast checkpoint is trained once and cloned before the treatment begins.

This means G40 does not test end-to-end ordinary GAE from random initialization. That limitation is explicit, not hidden.

3.2 Auxiliary-head capacity confounding

G31 carries an immediate baseline and a successor baseline. Simply deleting them from the ordinary arm would change parameter count, optimizer state and auxiliary fitting capacity.

Frozen correction: both arms contain the same:

centralized_slow_critic
immediate_baseline
successor_baseline

with identical keys, shapes, initialization, trainable masks and optimizer membership.

In the ordinary arm, the immediate and successor heads are shadow heads:

they receive the same target definitions;

they receive the same number of optimizer steps;

their outputs never enter the ordinary actor advantage, critic target, policy forward pass, source, branch selector or evaluation metrics;

their parameters share no storage with the actor or slow critic;

their inputs are detached from all actor/critic parameters.

A proof-sized update must show that including versus omitting their losses leaves the ordinary actor and slow-critic update bitwise unchanged while the shadow heads themselves update.

Thus a G31 advantage cannot be attributed merely to two extra trainable heads.

3.3 Full-return information is present in both arms

For terminal bootstrap zero and λ=1,

A
t
GAE1
	​

=
ℓ=0
∑
H−1−t
	​

γ
ℓ
δ
t+ℓ
	​

=G
t
	​

−V(s
t
	​

).

The ordinary arm therefore receives the complete discounted team return. G40 separates:

single full-return advantage
versus
immediate/successor decomposition plus direction balancing

It does not separate:

future reward information
versus
no future reward information

A G31 win may reflect variance control, baseline conditioning or gradient geometry. It cannot be described simply as proof that “ordinary credit cannot see delayed consequences.”

3.4 Active-count scaling can create a false credit result

The same team advantage is broadcast to every active autoregressive action factor. If one arm averages over primitive steps while the other averages over active tokens, roster size changes the effective learning rate.

Frozen correction: both arms use the exact same inherited active-token mask, likelihood factorization, denominator and capacity weighting. The team advantage is calculated once per environment step and only then broadcast to active action factors. No division by active count, multiplication by active count or arm-specific normalization is permitted.

3.5 Privileged-critic interpretation

The ordinary actor advantage is built from the centralized true-state critic, whereas G31 uses its two auxiliary baselines for actor credit.

This is an intended credit-package difference, not an actor-information difference, because:

both arms contain the same critic and heads;

the actor observations remain identical;

the ordinary arm receives no critic state in its policy forward pass;

critic outputs affect the actor only through the detached GAE advantage.

A positive ordinary result does not establish that the centralized critic is unnecessary. A positive G31 result does not identify which critic or baseline input is semantically necessary.

3.6 Common-anchor sufficiency

The shared fast anchor may already be close to or above the absolute access boundary. In that case a positive ordinary branch could mean that ordinary GAE preserves an already learned controller rather than learning the capability from scratch.

That is compatible with the frozen positive claim: the specialized G31 branch phase is locally removable. It does not support a stronger from-scratch learning claim.

Anchor utility and branch-stage incremental gain may be reported as diagnostics, but they cannot alter the five-branch selector.

3.7 Source-level simpler explanation

The G32/G34 source exposes current load and target mix, and the retained native-six policy class already contains an access-capable direct current-state mapping. G39 established that the actor and training parameterization can access this source under G31, but it did not make G31 credit necessary.

Therefore:

ordinary GAE sufficiency is plausible;

G31 advantage remains empirically possible through finite-budget optimization;

neither outcome establishes a general theorem about temporal credit.

3.8 Required witnesses
Outcome	Smallest valid witness
Operational invalidity	Branch models differ before credit updates; a shadow head changes the ordinary actor; a target or optimizer count differs
Source/common-access failure	Source controls fail, or both final arms confidently fail an absolute access gate
Ordinary sufficiency	Ordinary arm passes all access gates and every G31-minus-ordinary UCB is <=0.05
G31 advantage	G31 accesses and ordinary confidently fails, or pooled LCB is >0.05 with every capacity-specific primary LCB >0
Mixed/underpowered	Ordinary access interval crosses a floor, or Δ
credit
	​

 CI crosses the 0.05 boundary
4. CDC_PORTFOLIO_LEDGER_EDITS

This is a zero-compute design result. It changes no supported, failed, source-invalid or out-of-scope scientific status.

CONJECTURES.md
EDIT=NONE

C-CREDIT already records that G31 is supported for G17/G18, while its local necessity in the native-six continuous-roster route remains untested and requires an information-, representation-, source- and exposure-matched comparator.

RESEARCH_DIRECTION_LEDGER.md

Retain the status:

OPEN_UNTESTED

Replace only the wording of the existing G40 row with the more exact open question:

Markdown
| G39 native-six continuous-roster 中 G31 branch credit package 的局部必要性/可替代性 | `OPEN_UNTESTED` | 每个 replicate 先训练一个共同的 G39 fast-access anchor 并 bitwise clone；随后仅比较 G31 realized-successor/direction-balanced branch 与 ordinary shared-team GAE(lambda=1) branch。actor、critic、三个 value/baseline heads、source、交互量、optimizer step、评价与置信单位完全匹配。 | lambda=1 的 ordinary null 同样包含完整 future return，因此该边界只能区分 specialized decomposition/gradient geometry，不能证明或否定普适未来信用；尚无正式结果。 |

The current ledger correctly preserves broader process/horizon/capacity, non-G33 UAV transport, recurrence, asynchronous lifetime and intrinsic-reward directions under their existing statuses.

IDEA_PORTFOLIO.md

The scientific rows remain unchanged. Replace only the scheduling metadata:

completed_action=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_FORMAL_ITERATION_30
source_family=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_P0
formal_disposition=NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39
scientific_disposition=SUPPORTED_RETAINED_NATIVE_SIX_COORDINATE_TRAINING_CONFIGURED_CAPACITY_BOUNDED_PROCESS_CONTINUOUS_ROSTER_G39
valid_result_disposition=CONTINUE
next_action=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_ALIGNMENT_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=30
iterations_remaining=7

This pointer is conditional on PM technical acceptance of an exact realization. It grants no implementation or compute authority. The current portfolio already retains G39 as the smallest actor route and identifies G40 as the active local credit question.

CURRENT_WORK.md

Mechanically record:

g40_design_disposition=IDENTIFIABLE_SHARED_FAST_ANCHOR_NATIVE_SIX_CREDIT_REDUCTION_G40_DESIGN
g40_claim_scope=G31_branch_decomposition_and_direction_balance_vs_team_GAE1_after_common_fast_anchor
g40_common_anchor=true
g40_shadow_head_match=true
g40_design_compute=0
g40_nonformal_transition_bound=20160
g40_formal_transition_bound=622080
g40_nonformal_optimizer_step_bound=100
g40_formal_optimizer_step_bound=3000
g40_next_boundary=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_ALIGNMENT_AUDIT
iterations_remaining=7
conclusion_bearing_iterations_consumed=30

The pushed active state already places G40 at the current design boundary with seven conclusion-bearing iterations remaining.

ALGORITHM_PRINCIPLES.md
EDIT=NONE

The existing requirements to match comparators, freeze credit authority before evidence, and prefer replacement over accumulation already cover G40.

5. DESIGN_VALID_DISPOSITION
DESIGN_VALID_DISPOSITION=CONTINUE
conclusion_bearing_iteration_cost=0
remaining_conclusion_bearing_iterations=7

The design is identifiable and executable within the active grant. No terminal disposition applies.

Preserved portfolio
Direction	State after G40 design audit	Advancement/reactivation condition
Native-six continuous-roster actor	SUPPORTED_RETAINED at G39	Remains the common actor basis
G31 branch credit reduction	Live; design frozen	Exact PM realization followed by code-science alignment
True-current-state critic reduction	Live, unscheduled	Isolate only after credit is resolved
Broader capacity/process/horizon transport	Live, unscheduled	Change one deployment axis at a time
Non-G33 UAV transport	Parked	Requires a feasible, load-bearing, source-identifiable UAV source
Recurrence/EHC	Parked	Requires task-relevant sequential information absent from current observations
C-BASE/C-COORD	Live outside this reduction	Requires representation-fixed access separation
Asynchronous skill lifetime and intrinsic reward	OUT_OF_SCOPE_FROZEN	Requires later explicit scope transition
G37 donor coherence	Parked historical question	Reactivate only if donor deployment returns
G33 lineage	Permanently frozen	No reactivation in this chain

Scheduling one next boundary is an attribution choice, not a claim that the other live directions are invalid. The role contract requires preservation of plural live and parked directions while only one resource-consuming action is scheduled.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_ALIGNMENT_AUDIT

Eligibility requires that PM first technically accept one exact pushed realization of the contract below.

The alignment audit’s sole scientific question will be:

Does the accepted implementation instantiate the shared fast anchor, bitwise branch clone, exact three-head inventory, shadow-head causal isolation, G31 target/decomposition semantics, ordinary GAE1 target, identical source and optimizer exposure, registered estimands, confidence construction and first-match order without introducing a second actor-, critic-, information- or capacity-changing route?

This response does not authorize PM realization, Git activity, a nonformal exercise or formal compute. External Pro owns the scientific contract but not code acceptance or execution.

7. EXECUTABLE_DESIGN_BOUNDARY
7.1 Exact arms and phase structure
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_P0

common_phase=COMMON_NATIVE6_FAST_ANCHOR
branch_arm_1=NATIVE6_G31
branch_arm_2=NATIVE6_TEAM_GAE1

For formal replicate r∈{0,1,2}:

Common phase
actor=NATIVE6_CS
capacity=8
source=unchanged_G32_fixed_process
fast_updates=100
environments_per_update=8
ppo_passes=2

Train one common anchor, not two nominally identical anchors.

After the final common update:

save the anchor state;

discard its optimizer;

clone every actor, critic, auxiliary-head, log_std and buffer tensor bitwise;

create two models with no shared tensor or buffer storage;

initialize every branch optimizer empty and separately owned.

Branch phase

Per arm:

branch_updates=100
environments_per_update=8
ppo_passes=2
checkpoint_selection=final_only

For each branch update:

Materialize both complete paired trajectories from the same exogenous ledgers and member-owned action-noise tensors.

Validate both before updating either.

Apply one actor step and one slow-critic step per PPO pass to each arm.

Do not carry optimizer state between arms.

Do not update either model during evaluation.

The common fast phase is part of both effective training histories but is counted once in actual environment interaction.

7.2 Exact model and head inventory

Both branch models contain exactly:

Module	Graph/input	G31 use	GAE1 use
Native-six actor	Exact accepted G39 actor	Policy	Policy
log_std	Exact accepted G39 tensor	Policy	Policy
Centralized slow critic V
ϕ
	​

(s
t
	​

)	Exact true-current-state graph	Value target; not G31 actor advantage	Value target and GAE actor advantage
Immediate baseline b
I
	​

(ξ
t
	​

)	Exact accepted G31 graph/input	Immediate actor advantage	Shadow only
Successor baseline b
S
	​

(ξ
t
	​

)	Exact accepted G31 graph/input	Successor actor advantage	Shadow only

There is no GAE-specific value head.

Fail-closed equalities:

state_dict_semantic_key_set_equal=true
state_dict_shape_map_equal=true
trainable_mask_equal=true
trainable_parameter_count_equal=true
initial_tensor_bytes_equal=true
optimizer_parameter_group_order_equal=true

The ordinary shadow heads must satisfy:

actor_forward_read_count=0
slow_critic_forward_read_count=0
branch_metric_read_count=0
checkpoint_selection_read_count=0
shared_parameter_storage_count=0

Their losses may update only their own parameters.

7.3 Exact return and target equations

Let r
t
	​

 be the single shared team reward, and let episode termination occur only after step H−1. Membership edits do not terminate or reset a return trace.

Freeze:

G
H
	​

=0,G
t
	​

=r
t
	​

+γG
t+1
	​

,γ=0.99.

Define the realized successor tail:

S
H−1
	​

=0,S
t
	​

=G
t+1
	​

=
k=t+1
∑
H−1
	​

γ
k−t−1
r
k
	​

.

All targets are computed after the complete real trajectory and detached before PPO optimization.

Shared slow-critic target

In both arms:

L
V
	​

=
2
1
	​

mean
e,t
	​

(V
ϕ
	​

(s
e,t
	​

)−G
e,t
	​

)
2
.

The critic target, reduction, optimizer, learning rate and number of steps are identical.

Shared auxiliary-head targets

In both arms:

L
I
	​

=
2
1
	​

mean(b
I
	​

(ξ
t
	​

)−r
t
	​

)
2
,
L
S
	​

=
2
1
	​

mean(b
S
	​

(ξ
t
	​

)−S
t
	​

)
2
.

The exact G31 masking and valid-row reduction are inherited without modification.

G31 actor credit

Freeze the exact accepted G31 semantics:

A
t
I
	​

=r
t
	​

−stopgrad(b
I
	​

(ξ
t
	​

)),
A
t
S
	​

=S
t
	​

−stopgrad(b
S
	​

(ξ
t
	​

)).

Each stream uses the exact accepted G31 centering, scaling, zero-variance handling, PPO clipping, entropy term and active-token denominator.

Let:

g
I
	​

=∇
θ
	​

L
PPO
	​

(A
I
),g
S
	​

=∇
θ
	​

L
PPO
	​

(A
S
).

The branch uses the byte-identical accepted G31 global direction-balancing operator:

g
G31
	​

=DB
G31
	​

(g
I
	​

,g
S
	​

).

Its norm convention, zero-gradient rule, numerical epsilon and assignment into Adam are inherited exactly; PM may not choose a new combiner.

There is one actor Adam.step() per PPO pass, not one step per stream.

Ordinary team GAE1 actor credit

Freeze:

δ
t
	​

=r
t
	​

+γ(1−d
t
	​

)V
ϕ
	​

(s
t+1
	​

)−V
ϕ
	​

(s
t
	​

),

where d
t
	​

=1 only at the episode terminal and the terminal bootstrap is exactly zero.

A
t
GAE1
	​

=
ℓ=0
∑
H−1−t
	​

(γλ)
ℓ
δ
t+ℓ
	​

,λ=1.

Numerically verify:

A
t
GAE1
	​

=G
t
	​

−V
ϕ
	​

(s
t
	​

)

within absolute tolerance 1e-6 before the first branch update and in every evidence artifact.

The raw GAE advantage is centered and scaled once using the same registered normalization helper and valid primitive-step rows used by the inherited PPO path. It is then broadcast unchanged to each active autoregressive action factor at that primitive step.

The ordinary actor loss is the exact inherited single-stream clipped PPO loss:

L
GAE
	​

=−mean
active factors
	​

[min(ρ
t
	​

A
t
	​

,clip(ρ
t
	​

,1−ϵ,1+ϵ)A
t
	​

)]+L
entropy
	​

,

using the exact inherited likelihood, clip, entropy and active-factor reduction.

There is:

no immediate/successor actor split;

no direction balancing;

no per-agent return;

no active-count multiplication or division;

no advantage recomputation between PPO passes.

7.4 Optimizer partition

Freeze the accepted G39 optimizer constants:

optimizer=Adam
beta1=0.9
beta2=0.999
eps=1e-8
weight_decay=0
learning_rate=1e-3
gradient_clipping=none
minibatches=none
Common phase

Use the exact accepted G39 fast-optimizer parameter partition and objective. This phase is shared and lies outside the G40 treatment.

Branch phase

For each arm:

actor_credit_optimizer:
    native-six actor
    log_std
    immediate baseline
    successor baseline

slow_critic_optimizer:
    centralized slow critic only

Per PPO pass:

actor_credit_optimizer_steps=1
slow_critic_optimizer_steps=1

The G31 arm computes two policy-gradient streams before its one actor step. The ordinary arm computes one policy-gradient stream. This difference is an explicit part of the credit package and must be reported; it is not hidden evidence-volume equality.

Baseline-head gradients are assigned only to baseline parameters and are not included in the G31 direction-balancing norm.

7.5 Seed ownership

Freeze formal seed bases:

anchor_model_seed_base=10401000
anchor_ledger_seed_base=10402000
anchor_action_seed_base=10403000

branch_ledger_seed_base=10404000
branch_action_seed_base=10405000
branch_gradient_probe_seed_base=10406000

evaluation_base_ledger_seed_base=10407000
evaluation_process_seed_base=10408000
evaluation_action_seed_base=10409000

bootstrap_seed=10410040
nonformal_seed_offset=900000

For formal replicate r, add r exactly once to every nonbootstrap seed.

For nonformal execution, add 900000 to every seed, including the bootstrap seed.

Shared across the two branch arms:

anchor checkpoint;

branch episode IDs;

branch source ledgers;

branch member-owned action noise;

evaluation base ledgers;

process signatures;

evaluation action noise;

bootstrap plan.

Arm-owned:

branch model tensors after cloning;

actor/head optimizer state;

slow-critic optimizer state.

No parameter-count or gradient-computation difference may advance an environment, process, action or bootstrap RNG.

7.6 Initial and branch-start audits

Before the common phase:

source controls and constructive policy witness pass;

all registered trainable groups have a finite live gradient under the common fast objective.

At the branch boundary:

model_state_bytes_equal=true
buffer_bytes_equal=true
log_std_equal=true
optimizer_states_empty_and_separate=true
shared_tensor_storage_count=0

On the first paired branch batch, before either update, require:

Quantity	Gate
Actor pre-tanh means	max abs difference <=1e-7
Actions under common noise	<=1e-7
Token log probabilities	<=1e-6
Prefix sums	<=1e-7
Slow-critic values	bitwise equal
Immediate/successor predictions	bitwise equal
Reward, roster and lifecycle traces	exact/equivalent inherited gate
Carried actor hidden state	exact zero

Learning-signal gate:

every actor group is finite and live under the G31 actor objective;

every actor group is finite and live under the GAE1 actor objective;

slow critic is finite and live;

both auxiliary heads are finite and live in both arms;

the ordinary shadow-head independence counterfactual passes;

A
GAE1
=G−V passes within 1e-6.

A failure stops before the first branch optimizer step.

7.7 Evaluation inventory

For each branch arm, replicate and capacity, evaluate exactly:

ZERO_RANDOM_DET
FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

ZERO_RANDOM_DET is the common pre-training zero checkpoint, logically bound to both arms. It is not the fast-anchor checkpoint.

Formal:

replicates=3
capacities=6|8|12
arms=2
cells_per_arm_capacity=5
total_cells=90
episodes_per_cell=64

Retain the G39 process law:

64 unique G34 time tuples per replicate/capacity;

one each of L/R/J/T;

only LRJT, LJRT, JLRT;

rotating 22/21/21 order balance;

corresponding capacity-8 profile balance;

paired fixed/random base ledgers;

paired member-owned action streams.

Evaluation has zero optimizer steps.

7.8 Absolute access gates

For each arm a:

Fixed process

For every capacity:

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
minimum random deterministic replicate mean >=0.85

and pooled learned gain:

LCB
95
	​

(U
a,final,random,det
−U
a,zero,random,det
)>0.

Equality passes at every non-strict floor; learned gain remains strict.

Confident failure uses the exact upper-bound duals of these predicates.

7.9 Paired estimands

For paired final random deterministic episodes:

Δ
credit,C,r,e
	​

=U
C,r,e
NATIVE6_G31
	​

−U
C,r,e
NATIVE6_TEAM_GAE1
	​

.

Primary:

Δ
credit
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
credit,C,r,e
	​

]
	​


Positive values favor G31.

Freeze:

δ
credit
	​

=0.05.

Component contrasts:

fixed deterministic utility, per capacity;

random deterministic utility, per capacity;

fixed stochastic utility, equal-capacity pooled;

random stochastic utility, equal-capacity pooled;

random event-window utility, per capacity;

random process-segment utility, per capacity.

ORDINARY_NONINFERIOR requires every primary/component UCB <=0.05.

MATERIAL_G31_ADVANTAGE requires:

LCB
95
	​

(Δ
credit
	​

)>0.05

and:

LCB
95
	​

(Δ
credit,C
	​

)>0∀C∈{6,8,12}.
7.10 Confidence construction

Freeze:

bootstrap_resamples=10000
bootstrap_seed=10410040
confidence_interval=95_percentile
episode_exclusions=none

One plan is generated and reused for all absolute and paired quantities:

Resample the three common-anchor replicate blocks.

Within selected replicate and capacity, resample all 64 whole episode IDs.

Retain both credit arms, zero/final checkpoints, fixed/random mates and deterministic/stochastic mates.

Never independently resample members, time steps, events, arms, credit components or action factors.

Weight capacities 6, 8 and 12 equally in pooled estimands.

7.11 First-match truth table
Priority	Branch	Exact predicate
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40	Any source, clone, head inventory, shadow-independence, target, gradient, optimizer, checkpoint, trace, RNG, confidence or authority invariant fails
2	SOURCE_OR_COMMON_ACCESS_FAILURE_G40	Operationally valid and source invalid, or both arms confidently fail access
3	ORDINARY_TEAM_GAE_CREDIT_SUFFICIENT_G40	Ordinary arm passes access, every G31-minus-ordinary UCB is <=0.05, and branch-start equality passes
4	G31_REALIZED_TAIL_CREDIT_ADVANTAGE_G40	G31 passes access and either ordinary confidently fails or MATERIAL_G31_ADVANTAGE=true
5	MIXED_UNDERPOWERED_CREDIT_REDUCTION_G40	Every remaining valid numerical pattern

Evaluation stops at the first match.

Equality rules:

absolute-floor equality                  = pass
random-minus-fixed LCB = -0.05           = pass
UCB(G31-ordinary) = 0.05                 = noninferior pass
LCB(G31-ordinary) > 0.05                 = material-advantage pass
learned-gain LCB > 0                     = strict

No anchor diagnostic, training curve, gradient cosine, head loss, critic error or event stratum may rescue or relabel an earlier result.

7.12 Evidence complexity
Nonformal
replicates=1
common_fast_updates=10
branch_updates_per_arm=10
environments_per_update=8
ppo_passes=2
evaluation_cells=30
episodes_per_cell=6
bootstrap_resamples=250

Training:

10⋅8⋅48+2⋅10⋅8⋅48=11,520

transitions.

Evaluation:

30⋅6⋅48=8,640.

Total:

20,160
	​


real transitions.

Optimizer steps:

20+2(20+20)=
100
	​

.
Formal

Training:

3(100⋅8⋅48+2⋅100⋅8⋅48)=345,600.

Evaluation:

90⋅64⋅48=276,480.

Total:

622,080
	​


real transitions.

Optimizer steps:

3[200+2(200+200)]=
3,000
	​

.

Both are below the G39 envelope recorded in the question and design materials.

Freeze the nonformal projection:

T
projected,formal
	​

=1.25(30T
train,nf
	​

+32T
eval,nf
	​

+40T
analyze,nf
	​

).

Required boundaries:

H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

nonformal_wall_clock<=1200_seconds
formal_wall_clock<=28800_seconds

These satisfy the user-authorized evidence-complexity policy.

7.13 Scientific versus implementation-only fields

Scientifically frozen:

shared-anchor phase;

branch point and clone equality;

head inventory and shadow semantics;

target equations;

G31 operator identity;

GAE1 equation and normalization;

active-token reduction;

optimizer partition and exposure;

seeds;

evaluation inventory;

estimands and thresholds;

confidence unit;

first-match order;

evidence bounds.

Implementation-only:

file and class names;

tensor storage;

vectorization and batching;

serialization layout;

telemetry format;

CPU kernel selection;

proof-test file organization;

update execution order, provided both trajectories exist before either update and no state or RNG is shared.

8. 中文简报

本轮设计裁决是：

IDENTIFIABLE_SHARED_FAST_ANCHOR_NATIVE_SIX_CREDIT_REDUCTION_G40_DESIGN

G40 可以形成有效比较，但必须把问题写得比“未来信用 vs 普通信用”更精确。

真正比较的对象

lambda=1 且 terminal bootstrap 为零时：

GAE1=完整折扣回报−V(s
t
	​

).

因此 ordinary arm 也看到了完整 future return。G40 真正比较的是：

G31:
    immediate/successor 分解
    两个 baseline
    realized successor tail
    direction-balanced actor gradient

versus

ordinary:
    一个 shared-team full-return GAE advantage
    一个标准 PPO actor gradient

它不能证明“未来奖励信息是否必要”，只能判断 G31 的分解、baseline conditioning 和 gradient geometry在当前 source 中是否仍有有限预算价值。

必须使用共同 fast anchor

每个 replicate 先训练一个共同的 G39 fast-access checkpoint，然后 bitwise clone 成两个 branch：

NATIVE6_G31
NATIVE6_TEAM_GAE1

两个 branch 从完全相同的 actor、critic、两个 auxiliary baselines 和 buffer 开始，optimizer state 都重新置空。

这样避免把“不同的前半程训练历史”错误归因于 credit。

正结果的边界因此是：

在共同 fast anchor 之后，ordinary GAE1 是否足以替换 G31 的 realized-tail/direction-balanced branch。

它不是“ordinary GAE 从随机初始化独立学会全部任务”的检验。

三个 value/baseline 模块

两臂都保留：

centralized slow critic
immediate baseline
successor baseline

ordinary arm 中，后两个是 shadow heads：

参数量和 optimizer exposure 与 G31 匹配；

继续拟合相同 immediate/successor targets；

但绝不能进入 ordinary actor advantage、critic、policy 或 branch selector；

它们必须与 actor/critic 参数完全不共享。

这关闭了“G31 只是多两个 head、参数更多”的解释。

主估计量
Δ
credit
	​

=U
G31
	​

−U
TEAM_GAE1
	​

.

margin：

0.05

正式分支保持：

INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40
SOURCE_OR_COMMON_ACCESS_FAILURE_G40
ORDINARY_TEAM_GAE_CREDIT_SUFFICIENT_G40
G31_REALIZED_TAIL_CREDIT_ADVANTAGE_G40
MIXED_UNDERPOWERED_CREDIT_REDUCTION_G40
最小证据规模

共同 fast phase 只真实运行一次，然后分支：

nonformal:
    20,160 real transitions
    100 optimizer steps
    30 cells
    250 bootstrap

formal:
    622,080 real transitions
    3,000 optimizer steps
    90 cells
    10,000 bootstrap

复杂度仍为：

H=48
K_search=0
hypothetical transitions=0
nested rollout=false
replanning=false

低于 G39 的正式上限。

CDC 状态

本轮没有正式计算，因此：

CONJECTURES scientific status = 不变
RESEARCH_DIRECTION_LEDGER status = OPEN_UNTESTED
IDEA_PORTFOLIO scientific rows = 不变
iterations remaining = 7

只把 G40 的开放问题精确化为“共同 fast anchor 后的 branch credit comparison”。

下一科学边界
CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_ALIGNMENT_AUDIT

该边界只有在 PM 独立完成并技术接受一个精确 pushed realization 后才具备资格。本裁决不授权实现、Git、nonformal 或 formal compute。

G33 及其所有衍生线继续永久冻结；critic reduction、broader process/horizon/capacity、可识别非 G33 UAV、recurrence/EHC 与 coordination 方向继续按既有条件保持 live 或 parked。