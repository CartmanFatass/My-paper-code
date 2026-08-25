1. REGISTERED_DESIGN_CONFORMANCE
REGISTERED_DESIGN_CONFORMANCE=
CONFORMS_AFTER_EXACT_DIRECTION_ONLY_FREEZE_BELOW

reference_source_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_P0
design_audit_compute=0
H=48
K_search=0
hypothetical_transitions=0

The prerequisite scientific and implementation boundary is closed:

supported_route=
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_NO_SLOW

G41_design_outcome=SLOW_CRITIC_EXACTLY_REMOVABLE_G41
G41_code_science_alignment=ALIGNED

G41 retains the native-six actor, log_std, shared two-output immediate/successor baseline module, realized-successor target, independent channel normalization and direction-balanced actor update. It removes only the post-anchor standalone slow critic, its return loss, Adam state and value-output interface.

G40 supports the complete immediate/realized-successor, shared-baseline and direction-geometry package against TEAM-GAE1, but does not identify which internal component is individually load-bearing. G41 expressly leaves direction balancing, the realized-tail target, decomposition, baseline conditioning and per-channel normalization unresolved.

A G42 comparison is therefore identifying, but only if “direction balancing” is defined narrowly as the angular composition of the two already-formed actor-gradient streams. The registered per-update global actor-gradient norm must be retained as a nuisance control. Otherwise a nominal NO_DB arm would simultaneously change gradient direction and effective learning rate.

2. DESIGN_SCIENTIFIC_DISPOSITION
DESIGN_SCIENTIFIC_DISPOSITION=
IDENTIFIABLE_SCALE_MATCHED_DIRECTION_ONLY_ATTRIBUTION_G42_DESIGN

training_arms=
NATIVE6_G31_DB_NO_SLOW
|
NATIVE6_G31_RAW_SUM_SCALE_MATCHED_NO_SLOW

common_anchor_training=none_read_only_accepted_G40_anchors
treatment=actor_gradient_angular_composition_only
parameter_count_equal=true
optimizer_step_exposure_equal=true
Exact scientific distinction

For a fixed branch state and stored trajectory, let:

g
I
	​

∈R
p

be the complete actor-plus-log_std gradient produced by the accepted immediate channel, and let:

g
S
	​

∈R
p

be the corresponding gradient from the accepted realized-successor channel.

Both are computed using the exact G41:

immediate and successor targets;

detached shared-baseline outputs;

per-channel advantage normalization;

PPO clipping, likelihood factorization and entropy semantics;

actor-parameter ordering.

Shared-baseline gradients are excluded from g
I
	​

,g
S
	​

 and remain identical in construction in both arms. G41 establishes that these retained actor/head updates are independent of the deleted slow critic.

Registered arm
NATIVE6_G31_DB_NO_SLOW

uses the exact registered composition:

d
DB
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
Frozen non-direction-balanced null
NATIVE6_G31_RAW_SUM_SCALE_MATCHED_NO_SLOW

first forms the unbalanced raw sum:

r=g
I
	​

+g
S
	​

.

It may not:

normalize the two channel gradients separately;

use their cosine or dot product to change direction;

project one channel against the other;

clip conflict;

rotate, orthogonalize or sign-correct either channel;

tune channel weights.

Let:

m
DB
	​

=∥d
DB
	​

∥
2
	​


be computed in float64 over the frozen flattened actor-plus-log_std parameter order. The non-DB gradient is:

d
NO_DB
	​

=
⎩
⎨
⎧
	​

0,
m
DB
	​

∥r∥
2
	​

r
	​

,
	​

m
DB
	​

=0,
m
DB
	​

>0 ∧ ∥r∥
2
	​

>0.
	​


If:

m
DB
	​

>0and∥r∥
2
	​

=0,

the update is not scale-matchable by a scalar without inventing a new direction. The package must fail before the optimizer step as operationally invalid. It may not choose one channel as a fallback, perturb the sum, or convert the event into evidence for direction balancing.

The scale m
DB
	​

 is detached. The DB vector’s coordinates may not enter the null update. A counterfactual replacement of d
DB
	​

 by any vector with the same norm must leave d
NO_DB
	​

 unchanged.

What the comparison identifies

The design identifies whether the registered angular rebalancing supplies finite-budget value after holding fixed:

two credit channels
their targets
their shared baseline
per-channel normalization
global actor-gradient norm
Adam exposure
source and trajectory law

It does not identify whether the scalar norm schedule associated with the registered operator is removable. The shadow DB calculation is a matched-control measurement, not an allowed source of coordinatewise direction for the null.

Accordingly, the positive scientific ceiling is:

Direction balancing, understood as the registered angular reorientation of the two normalized actor-gradient streams, is removable from the exact post-anchor G41 route under G42-P0 while retaining its registered global step-norm schedule.

A negative result may support only:

That angular direction balancing supplies a source-local finite-budget access or material-utility advantage over the exact scale-matched raw-sum null.

Neither result establishes the individual necessity of the realized-tail target, immediate/successor decomposition, shared-baseline conditioning, per-channel normalization, common fast anchor, recurrence or any transport direction.

Retain, delete and add
Object	G42 treatment
Accepted G40 common fast anchors	Retain read-only
G41 no-slow projection	Retain exactly
Native-six actor and no-carry semantics	Retain exactly
Shared true-state two-output baseline	Retain exactly
Immediate and realized-successor targets	Retain exactly
Per-channel normalization	Retain exactly
Actor/head Adam and PPO exposure	Retain exactly
Registered DB angular composition	Treatment arm
Scale-matched raw sum	Null arm
Trainable parameters	Add none
New observation, reward or source field	Add none
Slow critic	Absent in both arms
3. IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES
3.1 Unmatched learning-rate null

Using g
I
	​

+g
S
	​

 directly would generally change both direction and global norm. Any performance difference could then be explained by effective actor learning rate rather than direction balancing.

Closure: match the null’s global pre-Adam actor-gradient norm to the registered DB norm on every PPO pass.

3.2 DB-direction leakage through the scale control

A null that uses the DB vector itself, rather than only its detached scalar norm, has not removed direction balancing.

Closure: reconstruct the null from g
I
	​

+g
S
	​

 and a scalar only. Perturbing the shadow DB direction while preserving its norm must leave the null gradient bitwise unchanged.

3.3 Exact cancellation

A raw sum can be exactly zero while the registered DB output is nonzero. No scalar rescaling can preserve raw-sum direction and match the registered norm.

Closure: this pattern selects operational invalidity before the optimizer step. It cannot trigger the DB-advantage branch and cannot be repaired by a priority channel, epsilon vector or tuned mixing coefficient.

If m
DB
	​

=0, both arms submit an exact zero actor gradient regardless of the nonzero raw sum; this preserves the registered step scale. Shared-baseline losses continue identically.

3.4 Vacuous treatment

If the DB and raw-sum unit directions are always equal, the treatment is absent even though both algorithms run.

Require, for every formal anchor replicate, at least one branch update satisfying:

	​

∥d
DB
	​

∥
2
	​

d
DB
	​

	​

−
∥r∥
2
	​

r
	​

	​

2
	​

>10
−6
.

The nonformal package must demonstrate this once. If a formal replicate never activates the directional treatment, the package is operationally invalid rather than evidence of removability.

3.5 Dead credit channel

A channel with no finite live gradient would turn the comparison into a one-channel test.

Before the first optimizer step, require:

||g_I||_2 > 1e-12
||g_S||_2 > 1e-12
all gradient values finite
every registered actor group live in at least one channel
shared immediate-baseline group live
shared successor-baseline group live

The analytic actor class remains access-capable through current load and target mix; a valid failure therefore concerns finite-budget credit geometry, not absence of an expressible policy. The retained route is already supported as native-six and no-carry within the bounded source family.

3.6 Entropy or shared-term double counting

Moving entropy, likelihood normalization or another common actor term outside one arm’s channel construction would create a second credit change.

Closure: g
I
	​

 and g
S
	​

 are the exact vectors presented to the accepted G31 composition. G42 may not redistribute, deduplicate or reweight their internal terms.

3.7 Baseline-update mismatch

The shared baseline module resides in the same actor/head optimizer but its losses do not enter the direction-balancing norm. A null that rescales baseline gradients would change baseline learning as well as actor composition.

Closure: norm matching applies only to the actor-plus-log_std vector. Immediate- and successor-baseline losses, gradients, parameter order and Adam exposure remain inherited and untouched.

3.8 Adam coordinatewise geometry

Equal global gradient norm does not imply equal post-Adam parameter-delta norm because Adam is coordinatewise.

That is not a residual scale confound. The changed coordinate distribution and resulting moment trajectory are the causal consequence of changing gradient direction. Matching the post-Adam delta would require an additional optimizer-dependent transformation and would no longer isolate the registered operator.

3.9 Common-anchor dependence

G42 begins from the three accepted G40 common fast anchors. It does not test direction balancing from random initialization or remove the common fast phase.

A positive result concerns the post-anchor route only. A negative result cannot establish universal direction-balancing necessity.

3.10 Package interaction

G40 supported the full credit package, not direction balancing alone. A DB advantage in G42 may depend on interaction with:

realized-successor targeting;

separate channel normalization;

baseline conditioning;

the fixed source and Adam budget.

It supports a local causal contribution, not context-free necessity.

3.11 Source and transport boundaries

G42 does not extend:

H=48
configured capacities=6|8|12
G32 fixed process
G34-P0 bounded random process

Broader process, horizon and capacity directions remain separate. Non-G33 UAV transport remains parked behind constructive feasibility and source-identifiability requirements; G33 remains permanently abandoned.

3.12 Branch witnesses
Intended outcome	Minimal witness
Invalid	m
DB
	​

>0 but g
I
	​

+g
S
	​

=0; nonfinite scale; DB coordinates leak into the null; treatment never activates
Source/reference failure	Source invalid or the registered DB arm confidently fails the inherited access contract
Raw-sum sufficiency	Both arms access and every DB-minus-raw-sum UCB is <=0.05
DB advantage	DB accesses and raw sum confidently fails, or pooled DB-minus-raw-sum LCB is >0.05 with every capacity-specific LCB >0
Mixed	Raw-sum access or comparative intervals cross a registered boundary without confident failure or material advantage
4. CDC_PORTFOLIO_LEDGER_EDITS

This is a zero-compute design freeze. It changes no scientific status.

CONJECTURES.md
EDIT=NONE

C-CREDIT remains supported at package level by G40 and narrowed by G41. Direction balancing remains one unresolved internal component; G42 has not yet produced evidence.

RESEARCH_DIRECTION_LEDGER.md
STATUS_EDIT=NONE

Retain:

G31 internal component attribution=OPEN_UNTESTED

The mechanically recorded description may be narrowed to:

Markdown
| G31 direction-balancing angular composition | `OPEN_UNTESTED` |
  Under the accepted post-anchor G41 no-slow route, compare registered DB
  against an equal-channel raw sum whose global actor-gradient norm is matched
  on every PPO pass. All targets, baselines, normalization, actor information,
  source and optimizer exposure remain fixed. |
  No G42 formal result yet; the matched scalar norm schedule is a control and
  not itself attributed. |

No broader process, horizon, capacity, recurrence, UAV, lifetime or intrinsic-reward row changes.

IDEA_PORTFOLIO.md

Scientific rows remain unchanged. Conditional scheduling metadata may become:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_DESIGN_ASSERTION_AUDIT

design_disposition=
IDENTIFIABLE_SCALE_MATCHED_DIRECTION_ONLY_ATTRIBUTION_G42_DESIGN

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_ALIGNMENT_AUDIT

conclusion_bearing_iterations_consumed=31
iterations_remaining=6
CURRENT_WORK.md

After mechanical archival only:

last_completed_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_DESIGN_ASSERTION_AUDIT

active_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_ALIGNMENT_AUDIT

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_ALIGNMENT_AUDIT

g42_design_disposition=
IDENTIFIABLE_SCALE_MATCHED_DIRECTION_ONLY_ATTRIBUTION_G42_DESIGN

g42_treatment=
registered_DB_direction_vs_raw_sum_direction_with_registered_global_norm_match

g42_iterations_remaining=6

The current active state already records G42 as the scheduled design boundary, six remaining conclusion-bearing iterations, and no permission to reactivate G33.

ALGORITHM_PRINCIPLES.md
EDIT=NONE

G42 applies the existing matched-comparator and replacement-before-accumulation rules; it creates no new cross-experiment principle.

5. DESIGN_VALID_DISPOSITION
DESIGN_VALID_DISPOSITION=CONTINUE

conclusion_bearing_iteration_cost=0
conclusion_bearing_iterations_consumed=31
remaining_conclusion_bearing_iterations=6

The design is identifiable under the fail-closed scale rule above. The grant balance is not exhausted, and this exact G42 action remains executable within the evidence policy. Neither terminal disposition applies.

The disposition does not rank direction balancing as scientifically unique. Realized-tail attribution, channel decomposition, shared-baseline conditioning, per-channel normalization, common-anchor simplification, broader transport and an identifiable non-G33 UAV source remain live or parked under their previously frozen conditions. The post-G41 portfolio explicitly preserves them.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_ALIGNMENT_AUDIT

This boundary becomes eligible only after Code Project Manager independently realizes and technically accepts one exact pushed implementation of the contract below.

Its sole question will be:

Does the accepted realization preserve the exact G41 no-slow route, compute byte-identical immediate and successor actor-gradient streams, use the registered DB arm unchanged, instantiate the scale-matched raw-sum null without DB-direction leakage, fail closed on cancellation or vacuity, and preserve anchor provenance, baseline updates, optimizer exposure, paired source, confidence procedure and first-match semantics?

This disposition authorizes no implementation, Git action, nonformal run or formal run.

7. EXECUTABLE_DESIGN_BOUNDARY
7.1 Exact provenance and branch start

Use the three immutable accepted G40 common fast anchors already bound by G41:

accepted_anchor_replicates=0|1|2
accepted_anchor_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
projection_source_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9

For each replicate:

Validate the accepted G40 manifest identity and complete anchor-state digest.

Apply the aligned G41 no-slow projection.

Clone the retained actor, log_std, shared baseline module and buffers bitwise into the DB and raw-sum arms.

Create empty, separate actor/head Adam states.

Require zero shared tensor or optimizer storage.

Consume no model RNG during projection.

G41’s aligned index already binds the accepted anchors, retained state, no-slow checkpoint and actor/head update identity.

7.2 Exact branch graphs

Both arms contain exactly:

native-six actor
log_std
shared two-output immediate/successor baseline module
no learned cross-step carry
no standalone slow critic

Their:

semantic keys
tensor shapes
trainable masks
parameter counts
initial bytes
actor/head optimizer parameter order

must be equal.

No arm-specific head, scalar parameter, scheduler, temperature or learned mixing coefficient is permitted.

7.3 Exact channel construction

For each stored complete branch trajectory:

G
H
	​

=0,G
t
	​

=r
t
	​

+0.99G
t+1
	​

,
S
t
	​

=G
t+1
	​

.

The frozen advantages remain:

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

Each channel is normalized exactly once before both PPO passes, with the accepted zero-variance rule. Targets and normalized advantages are not recomputed between passes.

The immediate and successor PPO actor gradients are computed separately in the same registered parameter order:

g
I
	​

,g
S
	​

.

Baseline losses and gradients remain separate from actor composition.

7.4 Exact composition and scale gates

For each PPO pass:

DB arm:
    d_DB = exact registered G31 DB(g_I,g_S)

NO_DB arm:
    r = g_I + g_S
    m = ||d_DB_shadow||_2
    d_NO_DB = m * r / ||r||_2

Required invariants:

all gradients finite
DB shadow consumes no RNG
DB shadow creates no optimizer state
DB direction coordinates never enter d_NO_DB
d_NO_DB collinear with g_I+g_S
float64 global norm match absolute error <=1e-12
assigned-gradient norm error <=1e-6
baseline gradients unchanged by scale matching

Zero handling:

m_DB=0:
    d_NO_DB=0

m_DB>0 and ||g_I+g_S||=0:
    operational invalidity before optimizer step

nonfinite norm or scale:
    operational invalidity

No clipping, epsilon vector, fallback channel or scale cap is permitted.

7.5 Treatment-activation and learning-signal gate

Before the first branch optimizer step:

immediate actor gradient globally live >1e-12
successor actor gradient globally live >1e-12
every registered actor group live in at least one channel
immediate baseline group live >1e-12
successor baseline group live >1e-12
all values finite

Across the registered branch updates, each replicate must contain at least one valid update with unit-direction distance:

∥u
DB
	​

−u
RAW
	​

∥
2
	​

>10
−6
.

Both final branch checkpoints must differ from their common anchor in at least one actor parameter and one shared-baseline parameter. These are operational treatment gates, not performance diagnostics.

7.6 Paired training and seed ownership

Freeze:

branch_ledger_seed_base=10421000
branch_action_seed_base=10422000
branch_gradient_probe_seed_base=10423000

evaluation_base_ledger_seed_base=10424000
evaluation_process_seed_base=10425000
evaluation_action_seed_base=10426000

bootstrap_seed=10427042
nonformal_seed_offset=900000

For formal replicate r, add r exactly once to every nonbootstrap base. For nonformal execution, additionally add 900000 to every seed, including the bootstrap seed.

Both arms share:

accepted anchor
episode identities
source ledgers
member-owned action noise
evaluation ledgers
process signatures
evaluation action noise
bootstrap plan

Arm-owned:

model tensors after cloning
actor/head Adam state

Per arm and replicate:

branch_updates=100
environments_per_update=8
PPO_passes=2
checkpoint_selection=final_only
episode_exclusions=none

Both complete trajectories are materialized and validated before either arm updates. Branch update order is fixed as:

DB then NO_DB

after paired collection. Because all model/optimizer state and RNG are separate, a proof-sized order-swap guard must leave the mate’s inputs and update unchanged.

7.7 Evaluation source and cells

Retain the exact G34-P0 fixed/random source at capacities:

6|8|12

For each arm, replicate and capacity, evaluate exactly four final cells:

FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

No zero or anchor evaluation cell is needed: G42 is a post-anchor component-attribution comparison. Branch liveness and parameter departure replace a zero-to-final learning-gain gate.

Formal random support per replicate/capacity:

episodes_per_cell=48
unique_time_tuples=48
LRJT=16
LJRT=16
JLRT=16

At capacity 8, the three registered profiles also occur 16 times each. Fixed and random mates share base ledgers; deterministic and stochastic cells retain the registered process and action-stream coupling.

Nonformal uses six episodes per cell, two per legal order and, at capacity 8, two per registered profile.

7.8 Absolute-access contract

For each arm a:

Fixed process

For every capacity:

LCB
95
	​

(U
C
a,fixed,det
	​

)≥0.90.

Also:

LCB
95
	​

(U
a,fixed,stoch
)≥0.80

with equal capacity weight, and:

minimum fixed deterministic replicate mean >=0.85
Random process

For every capacity:

LCB
95
	​

(U
C
a,random,det
	​

)≥0.90,
LCB
95
	​

(E
C
a,random,det
	​

)≥0.85,
LCB
95
	​

(P
C
a,random,det
	​

)≥0.85,
LCB
95
	​

(U
C
a,random,det
	​

−U
C
a,fixed,det
	​

)≥−0.05.

Also:

LCB
95
	​

(U
a,random,stoch
)≥0.80,

and:

minimum random deterministic replicate mean >=0.85

Equality passes at every non-strict floor.

ACCESS_CONFIDENT_FAIL(a) uses the exact upper-confidence-bound dual of these predicates.

7.9 Primary and component estimands

For paired final random deterministic episodes:

Δ
DB,C,r,e
	​

=U
C,r,e
DB
	​

−U
C,r,e
NO_DB
	​

.

Primary:

Δ
DB
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
DB,C,r,e
	​

]
	​


Positive values favor direction balancing.

Freeze:

δ
DB
	​

=0.05.

Registered component contrasts are:

fixed deterministic utility, per capacity;

random deterministic utility, per capacity;

fixed stochastic utility, equal-capacity pooled;

random stochastic utility, equal-capacity pooled;

random event-window utility, per capacity;

random process-segment utility, per capacity;

random-minus-fixed transport difference, per capacity.

NO_DB_NONINFERIOR requires every primary and component UCB to be at most 0.05.

MATERIAL_DB_ADVANTAGE requires:

LCB
95
	​

(Δ
DB
	​

)>0.05

and:

LCB
95
	​

(Δ
DB,C
	​

)>0∀C∈{6,8,12}.
7.10 Confidence construction

Freeze:

bootstrap_seed=10427042
formal_resamples=10000
nonformal_resamples=250
confidence_interval=95_percentile
episode_exclusions=none

Use one hierarchical paired plan for every absolute and comparative quantity:

Resample the three accepted-anchor replicate blocks with replacement.

Within each selected replicate and capacity, resample all 48 whole episode IDs.

Retain both arms, fixed/random mates and deterministic/stochastic mates.

Never independently resample members, time steps, events, gradient channels, arms or action factors.

Weight capacities 6, 8 and 12 equally.

7.11 Frozen first-match table
Priority	Terminal branch	Exact predicate
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42	Any provenance, graph, gradient, treatment-activation, scale, cancellation, optimizer, RNG, source-trace, confidence, inventory or authority invariant fails
2	SOURCE_OR_REFERENCE_ACCESS_FAILURE_G42	Operationally valid and source invalid, or the registered DB arm confidently fails absolute access
3	SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42	DB access passes, NO_DB access passes and every DB-minus-NO_DB primary/component UCB is <=0.05
4	DIRECTION_BALANCE_FINITE_BUDGET_ADVANTAGE_G42	DB access passes and either NO_DB confidently fails or MATERIAL_DB_ADVANTAGE=true
5	MIXED_UNDERPOWERED_DIRECTION_BALANCE_ATTRIBUTION_G42	Every remaining valid numerical pattern

Evaluation stops at the first match.

Equality rules:

absolute-floor equality                   = pass
random-minus-fixed LCB = -0.05            = pass
UCB(DB-NO_DB) = 0.05                       = noninferior pass
LCB(DB-NO_DB) > 0.05                       = material-advantage pass
unit-direction distance = 1e-6             = treatment active
assigned-gradient norm error = 1e-6        = scale gate pass

No channel norm, cosine, scale ratio, training curve or event stratum may rescue or relabel an earlier branch.

7.12 Smallest evidence inventory
Nonformal
accepted_anchor_replicates=1
branch_updates_per_arm=10
environments_per_update=8
PPO_passes=2

evaluation_arms=2
capacities=3
cells_per_arm_capacity=4
episodes_per_cell=6
bootstrap_resamples=250

Training transitions:

2×10×8×48=7,680.

Evaluation transitions:

2×3×4×6×48=6,912.

Total:

14,592
	​


real transitions.

Optimizer steps:

2×10×2=
40
	​

.
Formal
accepted_anchor_replicates=3
branch_updates_per_arm=100
environments_per_update=8
PPO_passes=2

evaluation_cells=72
episodes_per_cell=48
bootstrap_resamples=10000

Training transitions:

2×3×100×8×48=230,400.

Evaluation transitions:

72×48×48=165,888.

Total:

396,288
	​


real transitions.

Optimizer steps:

2×3×100×2=
1,200
	​

.

The common anchors are read-only accepted artifacts and contribute no new transitions or optimizer steps.

The 48-episode formal inventory is the smallest frozen here because it preserves exact 16/16/16 order and profile balance while reducing the G40 evaluation inventory by 25%. The allow-listed evidence supplies no precision result supporting a smaller access-gate inventory.

7.13 Wall-clock and complexity boundary
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

nonformal_wall_clock<=1200_seconds
formal_wall_clock<=28800_seconds

Record:

T_train_nonformal
T_evaluate_nonformal
T_analyze_nonformal

Freeze:

T
projected,formal
	​

=1.25(30T
train,nf
	​

+24T
evaluate,nf
	​

+40T
analyze,nf
	​

).

A cap violation is:

NON_EXECUTABLE_EVIDENCE_DESIGN

with zero scientific iteration cost. It is not a direction-balance result. These limits remain within the user-authorized search and wall-clock policy.

7.14 Implementation-only degrees of freedom

Implementation-only:

file and class names;

tensor storage and batching;

serialization layout;

telemetry organization;

CPU kernel organization;

test-file placement;

update execution order after paired collection, provided all RNG and state are disjoint.

Scientifically frozen:

anchor identities;

no-slow graph;

channel gradients;

raw-sum null;

shadow scale rule;

zero/cancellation handling;

norm and activation gates;

seed ownership;

training and evaluation inventory;

access gates;

confidence unit;

first-match order;

evidence ceilings.

8. 中文简报
G42设计裁决=
IDENTIFIABLE_SCALE_MATCHED_DIRECTION_ONLY_ATTRIBUTION_G42_DESIGN

DESIGN_VALID_DISPOSITION=CONTINUE
本轮结论性迭代成本=0
剩余结论性轮次=6
G42 真正隔离什么

G41 当前保留的 post-anchor route 是：

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_NO_SLOW

其中仍有两条 actor credit：

immediate channel
realized-successor channel

两条 channel 已各自完成 target、baseline residual 和 normalization。G42 只改变它们最后如何合成 actor gradient。

DB arm：

d
DB
	​

=DB(g
I
	​

,g
S
	​

).

NO_DB arm：

r=g
I
	​

+g
S
	​

,

然后只用 DB 输出的标量全局范数做尺度匹配：

d
NO_DB
	​

=∥d
DB
	​

∥
∥g
I
	​

+g
S
	​

∥
g
I
	​

+g
S
	​

	​

.

NO_DB 不得使用 DB vector 的任何坐标，也不得做 cosine correction、projection、orthogonalization、单 channel 优先或权重调节。

因此本轮回答的是：

在保持每一步全局 actor-gradient norm 不变时，G31 的 angular direction rebalancing 是否有用？

它不回答 scalar norm schedule 是否也能删除。

零梯度与 cancellation
DB norm=0:
    NO_DB gradient=0

DB norm>0 且 raw sum=0:
    运行在 optimizer step 前 INVALID

不能临时选择 immediate 或 successor 作为 fallback，因为那会新增第二个科学机制。

正负分支
1 INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42
2 SOURCE_OR_REFERENCE_ACCESS_FAILURE_G42
3 SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42
4 DIRECTION_BALANCE_FINITE_BUDGET_ADVANTAGE_G42
5 MIXED_UNDERPOWERED_DIRECTION_BALANCE_ATTRIBUTION_G42

主差值：

Δ
DB
	​

=U
DB
	​

−U
NO_DB
	​

.

margin 仍为：

0.05

若两臂都通过 access，且全部 DB-minus-NO_DB UCB <=0.05，支持 scale-matched 方向平衡可删除。

若 DB 通过，而 NO_DB confident fail，或 pooled LCB >0.05 且三个 capacity 的 LCB 均 >0，支持 direction balancing 的有限预算优势。

最小证据

直接读取三个已接受 G40 fast anchors，不重新训练 anchor。

nonformal:
    14,592 real transitions
    40 optimizer steps
    24 cells
    250 bootstrap

formal:
    396,288 real transitions
    1,200 optimizer steps
    72 cells
    48 episodes/cell
    10,000 bootstrap

正式 48 episodes/cell 可形成三个 event order 和 capacity-8 三个 profile 的精确 16/16/16 平衡，比 G40 的 64 episodes 减少 25%。

CDC 与下一边界

本轮没有结果数据，因此：

CONJECTURES status 不变
RESEARCH_DIRECTION_LEDGER status 不变
IDEA_PORTFOLIO scientific rows 不变
G31 internal component attribution 仍为 OPEN_UNTESTED

下一边界仅为：

CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_ALIGNMENT_AUDIT

其他 G31 components、common fast anchor、broader process/horizon/capacity、可识别非 G33 UAV、recurrence/EHC 等方向继续保留。G33 永久冻结。本裁决不授权实现、Git、nonformal 或 formal compute。