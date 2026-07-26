1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=IDENTIFIABLE_EMPIRICAL_REACTIVE_REDUCTION_G35_DESIGN
source_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
primary_question=current_state_reduction_sufficiency_vs_recurrent_inductive_bias
task_level_recurrence_necessity_identifiable=false
fresh_paired_training=true
historical_G32_checkpoints=reference_only

A conclusion-bearing matched comparison can be frozen, but its scientific ceiling must be narrower than “recurrence is necessary.”

The G32/G34 task exposes the current load and target mix directly, and the registered constructive action is the current-state map

a
(0)
=2load−1,a
(1)
=2target_mix−1.

Lifecycle age, previous actions, active count, capabilities, action prefix, and true normalized time are also current actor inputs. Therefore an access-level policy exists without learned cross-step neural state.

Accordingly, G35 can identify either:

current-state reduction sufficiency under the frozen training and evaluation contract; or

a finite-budget recurrent inductive-bias advantage over an expressively adequate current-state arm.

It cannot prove a representational theorem that the task intrinsically requires recurrence. This narrower distinction directly resolves the ambiguity left by G34: its destructive reactive ablation was underpowered and simultaneously removed hidden state, age, and previous actions.

2. EXACT_MATCHED_ARMS
2.1 Common dimensions and modules

Freeze:

observation_dim=10
critic_state_dim=6
action_dim=2
actor_width=32
configured_training_capacity=8
evaluation_capacities=6|8|12

Both arms instantiate the same parameterized graph, with identical state-dict keys, tensor shapes, trainable masks, initialization, and parameter count:

current-member encoder;

active-set sum;

raw log1p(active_count);

context encoder;

deterministic anonymous routing order;

active-fraction autoregressive action prefix;

one common gated actor cell;

one common action head;

one common current-observation readout;

one shared diagonal log-standard-deviation parameter;

identical centralized slow critic;

identical G31 immediate and successor credit baselines.

The current policy already uses a two-layer member encoder, active-set context, a GRUCell, an autoregressive prefix-conditioned action head, tanh-Gaussian actions, and a centralized current-state critic.

2.2 Exact actor equations

For active lifecycle i at primitive step t, define:

e
i,t
	​

=MemberEnc(o
i,t
	​

)∈R
32
,
g
t
	​

=ContextEnc
	​

	​

j∈A
t
	​

∑
	​

e
j,t
	​

,log(1+∣A
t
	​

∣)
	​

	​

∈R
32
,

and let p
i,t
	​

∈R
2
 be the already registered active-fraction prefix before routing owner i.

The common gated-cell input is:

x
i,t
	​

=[e
i,t
	​

,g
t
	​

,p
i,t
	​

].

Both arms use the same current-state proxy in the cell’s hidden-input position:

q
i,t
	​

=e
i,t
	​

.

Let the nontrainable arm constant be:

c
REC
	​

=1,c
CS
	​

=0.

The common cell and action mean are:

u
i,t
	​

=GRUCell(x
i,t
	​

,q
i,t
	​

+c
a
	​

h
i,t
	​

),
μ
i,t
	​

=ActionHead([u
i,t
	​

,p
i,t
	​

])+Do
i,t
	​

,

where D:R
10
→R
2
 is a trainable linear current-observation readout present in both arms and initialized identically to zero.

The carried state is:

h
i,t+1
	​

=c
a
	​

u
i,t
	​


for an active lifecycle.

Thus:

REC arm: carries u
i,t
	​

 across primitive steps and temporary absence.

CS arm: discards u
i,t
	​

; its carried state is always exactly zero.

Both arms use every current observation, the same within-step autoregressive prefix, and the same trainable cell tensors.

At the forced initial state, where h
i,0
	​

=0, both arms produce exactly identical pre-tanh means, distributions, values, and actions under common noise.

The current-state arm is therefore functionally feedforward across primitive steps even though it shares the same gated-cell parameter tensors. The cell’s hidden-to-hidden weights are not dummy parameters in that arm: they receive the nonzero current proxy q
i,t
	​

.

2.3 Action distribution

Both arms use the existing distribution unchanged:

z
i,t
	​

∼N(μ
i,t
	​

,diag(exp(2logσ))),a
i,t
	​

=tanhz
i,t
	​

,

with the same Jacobian-corrected token likelihood, entropy, action support, routing order, and member-owned stochastic noise.

2.4 Critic and credit graph

The critic graph is exactly identical across arms:

V
t
	​

=Critic
	​

	​

j∈A
t
	​

∑
	​

e
j,t
	​

,log(1+∣A
t
	​

∣),s
t
critic
	​

	​

	​

.

It does not consume the actor’s carried hidden state.

The slow critic, immediate baseline, successor baseline, G31 realized-future-tail target, direction-balanced gradient composition, and optimizer partition are identical. G31’s successor target remains the detached discounted future reward tail excluding the current reward, with exact zero terminal tail.

2.5 Parameter-matching rule

Parameter matching is fail-closed:

state_dict_key_set_REC == state_dict_key_set_CS
state_dict_shape_map_REC == state_dict_shape_map_CS
trainable_parameter_count_REC == trainable_parameter_count_CS
trainable_parameter_mask_REC == trainable_parameter_mask_CS
initial_state_dict_REC == initial_state_dict_CS byte-for-byte

The carry constant c
a
	​

 is nontrainable metadata and is absent from the state dictionary.

Prohibited:

arm-specific width changes;

dummy or frozen parameters inserted only to equalize counts;

a larger feedforward trunk for CS;

an arm-specific residual or critic;

different log-standard deviations;

loading historical G32 weights into either causal arm.

The common readout D is not a second treatment: it is present, trainable, and identically initialized in both fresh arms.

2.6 Lifecycle boundary

For REC:

temporary leave freezes h
i
	​

;

rejoin restores it;

fresh join starts with h
i
	​

=0;

terminal leave deletes it before the current action;

unaffected survivors remain continuous.

For CS:

the carried hidden state is always zero;

age and previous-action fields still follow the exact environment lifecycle rules;

temporary leave/rejoin therefore affects its visible current state exactly as it affects REC.

The environment’s age, previous-action, active-mask, and roster semantics remain unchanged.

3. INFORMATION_SOURCE_AND_TRAINING
3.1 Immutable information contract

Both arms receive every registered current field:

Actor field	Both arms
capability coordinates	retained
anonymous presentation priority	retained
current load	retained
current target mix	retained
raw log1p(active_count)	retained
lifecycle active age	retained
two previous actions	retained
true normalized physical time	retained
active-fraction autoregressive prefix	retained
future membership process	forbidden
lifecycle identity as a learned feature	forbidden

The centralized critic receives the unchanged current load, target mix, active capability sums, raw log-count, and true normalized time. G35 changes neither source information nor reward.

3.2 Training source

Both arms train only on the unchanged G32 capacity-8 fixed process:

H=48
event_times=12|24|36
event_process=L|atomic_R_plus_J|T
train_profiles=
  train_4_3_6_5
  train_5_3_7_6
  train_6_4_8_6
reward=unchanged_relative_service_matching_utility

The registered profiles all contain temporary leave, rejoin plus fresh join, and terminal leave.

3.3 Held-out evaluation source

Both arms are evaluated on the unchanged G34-P0 paired fixed/random source:

capacities 6/8/12;

one each of L/R/J/T;

random event times in steps 5..43;

minimum five-step event separation;

no event at a multiple of four;

orders LRJT, LJRT, and JLRT;

exact paired fixed reference at 12/24/36;

shared base ledgers and member-owned action streams.

3.4 Fresh paired seed block

Freeze formal seed bases:

model_initialization_seed_base=10351000
training_ledger_seed_base=10352000
training_action_seed_base=10353000
evaluation_base_ledger_seed_base=10354000
evaluation_process_seed_base=10355000
evaluation_action_seed_base=10356000
initial_gradient_probe_seed_base=10357000
bootstrap_seed=10358035

For replicate r∈{0,1,2}, add r exactly once to every nonbootstrap seed.

The two arms within a replicate share:

initial parameter tensors;

training episode IDs;

environment ledgers;

member-owned action noise;

evaluation base ledgers;

G34 process signatures;

deterministic and stochastic evaluation noise.

Optimizer states are separate but identically initialized.

The bounded nonformal exercise adds 900000 to every seed, including its bootstrap seed, and cannot become formal evidence.

3.5 Formal training inventory

Per arm and replicate:

training_capacity=8
fast_updates=100
return_to_go_updates=100
environments_per_update=8
episode_length=48
ppo_passes=2
learning_rate=1e-3
gamma=0.99
initial_log_std=-1.0
optimizer=Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)
minibatches=none
checkpoint_selection=final_only
episode_exclusions=none

Each arm therefore receives:

200×8×48=76,800

environment transitions per replicate.

Across two arms and three replicates:

460,800

training transitions.

Optimizer exposure per arm/replicate is exactly:

200 fast-phase optimizer steps;

200 return-to-go actor optimizer steps;

200 return-to-go critic optimizer steps.

Total formal optimizer steps:

2×3×600=3,600.

These counts match the inherited G32 training exposure rather than giving either comparator more learning opportunity. The G32 formal configuration used 100 fast updates, 100 return-to-go updates, eight environments, two PPO passes, Adam at 10
−3
, and three replicates.

At every update:

materialize the paired episode batch and action-noise tensors;

collect both arms before updating either;

apply each arm’s own optimizer to the identical exposure;

record actual actor, critic, and baseline step counts separately.

Historical G32 checkpoints are not resumed.

3.6 Evaluation inventory

Per replicate:

three capacity-specific constructive-random source-control cells;

for each of two arms and each capacity 6/8/12:

ZERO_RANDOM_DET;

FINAL_FIXED_DET;

FINAL_FIXED_STOCH;

FINAL_RANDOM_DET;

FINAL_RANDOM_STOCH.

Therefore:

cells_per_replicate=33
formal_replicates=3
formal_total_cells=99
episodes_per_cell=128
formal_evaluation_episodes=12672
formal_evaluation_transitions=608256
evaluation_optimizer_steps=0

Every zero/final checkpoint is strict-loaded into the same arm mode at capacities 6/8/12, without adapters, slicing, remapping, or evaluation updates.

4. LEARNING_SIGNAL_OPTIMAL_POLICY_AND_WITNESSES
4.1 Forced-initial-state equality

Before training, for every replicate and paired initial batch:

REC_pre_tanh == CS_pre_tanh
REC_action_distribution == CS_action_distribution
REC_token_log_prob == CS_token_log_prob
REC_value == CS_value
REC_action_under_common_noise == CS_action_under_common_noise

within absolute tolerance 10
−7
.

This follows from byte-identical parameters and h
i,0
	​

=0, so the carry term is initially absent.

Failure is operational invalidity.

4.2 Live gradient-path audit

Before the first optimizer step, collect one paired eight-episode capacity-8 fixed-process batch using the registered training source.

Using the actual inherited losses, without a synthetic auxiliary objective, compute shadow gradients for:

member encoder;

context encoder;

gated-cell input weights;

gated-cell recurrent weights;

all gated-cell biases;

action head;

common current-observation readout D;

log_std;

centralized slow critic;

immediate baseline;

successor baseline.

For each trainable group in each arm, require:

gradient_is_finite=true
max(actual_fast_objective_gradient_norm,
    actual_return_to_go_objective_gradient_norm)>1e-12

No optimizer step occurs during this audit.

The CS arm’s recurrent-weight group has a live path because the common cell receives q
i,t
	​

=e
i,t
	​

 in its hidden-input position even though no learned state is carried across steps.

The design-audit contract requires live initial gradients and pass/fail witnesses before formal evidence is frozen.

4.3 Relevant policy sets and claim ceiling

Define:

Π
REC
	​


as the policies realizable by the common G35 graph with c=1, and

Π
CS
	​


as those realizable with c=0.

Both retain within-step autoregression and all current information. Only Π
REC
	​

 carries learned neural state between primitive steps.

Because current load and target mix directly specify an access-level action, the source cannot establish:

“every access-level policy requires recurrence.”

It can establish only:

Π
CS
	​

 is empirically sufficient under the frozen budget; or

the REC inductive bias produces a material finite-budget advantage under the frozen training distribution.

A positive REC branch must therefore be worded as recurrent-state inductive-bias advantage, not recurrence necessity.

4.4 Positive current-state representational witness

Set all common action-producing paths except D to zero, and set:

D
0,load
	​

=2,b
0
	​

=−1,
D
1,target_mix
	​

=2,b
1
	​

=−1.

Then the deterministic action is:

a
(0)
=tanh(2L−1),a
(1)
=tanh(2M−1),

where:

L∈[0.30,0.70],M∈[0.25,0.75].

Writing:

e(L)=
2
1+tanh(2L−1)
	​

,m(M)=
2
1+tanh(2M−1)
	​

,

the one-step reward is:

1−
2
1
	​

(
	​

LM
e(L)m(M)
	​

−1
	​

+
	​

L(1−M)
e(L)(1−m(M))
	​

−1
	​

).

Over the complete registered load/mix support, its lower bound is:

0.94048>0.90.

Thus the CS class contains a deterministic current-state policy exceeding the absolute utility floor at every step, event window, and process segment, independent of roster count and capability scale. The current-state null cannot fail merely because the architecture lacks access-level expressivity.

This witness is not the initialization and is not a supplied controller during training.

4.5 Gate witnesses
Intended branch/gate	Smallest witness
common source access	registered constructive action gives U=E=P=1
current-state sufficiency	both arms realize the same current-state witness, giving Δ
rec
	​

=0
recurrent advantage	REC has utility 0.96, CS 0.90, with paired Δ
rec
	​

>0.05 and both source gates valid
common access failure	both arms emit zero served effort, giving utility 0
no learned gain	final and zero checkpoints are identical, giving gain 0
mixed/underpowered	paired Δ
rec
	​

 interval crosses 0.05, for example [0.03,0.07]

All registered denominators are nonzero:

episode utility: 48 steps;

each G34 event window: four steps;

each random-process segment: at least five steps;

every registered roster is nonempty.

5. ESTIMANDS_GATES_AND_CONFIDENCE
5.1 Per-episode quantities

Retain the G34 trace definitions.

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

For random event times t
1
	​

,…,t
4
	​

:

E
e
	​

=
j=1,…,4
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

For the five event-delimited process segments S
0
	​

,…,S
4
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

All quantities must be recomputed from serialized reward and actual roster-size traces before analysis.

5.2 Arm access predicates

For arm a∈{REC,CS}, define:

Δ
a,C
process
	​

=U
a,C
final,random
	​

−U
a,C
final,fixed
	​

,

and pooled learned gain:

G
a
	​

=U
a
final,random
	​

−U
a
zero,random
	​

.

ACCESS_PASS(a) requires all of:

Fixed-process controls

For every capacity C∈{6,8,12}:

LCB
95
	​

(U
a,C
final,fixed,det
	​

)≥0.90.

Pooled fixed stochastic:

LCB
95
	​

(U
a
final,fixed,stoch
	​

)≥0.80.

Minimum fixed deterministic replicate mean:

≥0.85.
Random-process access

For every capacity C:

LCB
95
	​

(U
a,C
final,random,det
	​

)≥0.90,
LCB
95
	​

(E
a,C
final,random,det
	​

)≥0.85,
LCB
95
	​

(P
a,C
final,random,det
	​

)≥0.85,
LCB
95
	​

(Δ
a,C
process
	​

)≥−0.05.

Pooled stochastic:

LCB
95
	​

(U
a
final,random,stoch
	​

)≥0.80.

Minimum random deterministic replicate mean:

≥0.85.

Pooled final-minus-zero gain:

LCB
95
	​

(G
a
	​

)>0.

Equality passes except for the strict learned-gain condition.

Operationally, access also requires:

exact parameter and exposure matching;

initial gradient audit;

finite updates;

inherited replay tolerance <=1e-6;

exact lifecycle ownership;

exact checkpoint phase counts;

zero evaluation optimizer steps;

exact trace recomputation.

5.3 Confident access failure

ACCESS_CONFIDENT_FAIL(a) holds if any corresponding:

utility/event/segment/stochastic upper bound is below its floor;

process-transport upper bound is below -0.05;

learned-gain upper bound is at or below zero;

registered minimum replicate mean is below 0.85.

Every other nonpassing pattern is access-underpowered.

5.4 Primary estimand

For capacity C, replicate r, and paired episode e:

Δ
rec,C,r,e
	​

=U
REC,C,r,e
final,random,det
	​

−U
CS,C,r,e
final,random,det
	​

.

The pooled primary estimand is equal-capacity weighted:

Δ
rec
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
rec,C,r,e
	​

].

Freeze the materiality/noninferiority margin:

δ
rec
	​

=0.05.
5.5 Current-state reduction sufficiency

Current-state reduction is supported iff:

ACCESS_PASS(CS)

and:

UCB
95
	​

(Δ
rec
	​

)≤0.05

and, for every capacity C:

UCB
95
	​

(Δ
rec,C
	​

)≤0.05.

Equality at 0.05 supports reduction sufficiency.

This explicitly classifies a current-state arm that is absolutely usable but slightly below REC by no more than five utility points as sufficient.

5.6 Recurrent-state inductive-bias advantage

A recurrent advantage is supported iff:

ACCESS_PASS(REC),
LCB
95
	​

(Δ
rec
	​

)>0.05,

and, for every capacity C:

LCB
95
	​

(Δ
rec,C
	​

)>0.

Both comparisons are strict.

This branch supports only a finite-budget advantage under G35-P0. It does not establish that recurrence is required by the optimal policy set.

5.7 Confidence construction

Freeze:

paired_replicates=3
capacities=6|8|12
evaluation_episodes_per_cell=128
bootstrap_resamples=10000
bootstrap_seed=10358035
confidence_interval=95_percent_percentile
checkpoint_selection=final_only
episode_exclusions=none

One paired hierarchical bootstrap plan is generated and reused for every registered estimand:

resample the three paired replicate blocks;

within each selected replicate and capacity, resample whole episode IDs;

retain both arms, zero/final, fixed/random, and deterministic/stochastic branches belonging to that episode;

never resample members, time rows, events, lifecycle rows, or arms independently.

No secondary annotation can rescue or overturn the primary branch.

6. FIRST_MATCH_TRUTH_TABLE

Define:

OPERATIONAL_VALID: all parameter, initialization, gradient, replay, optimizer-exposure, checkpoint, trace, RNG, lifecycle, finite-value, and cell-inventory invariants pass.

SOURCE_VALID: inherited G32/G34 source laws and constructive controls pass exactly.

REC_ACCESS_PASS, CS_ACCESS_PASS: Section 5.2.

REC_ACCESS_CONFIDENT_FAIL, CS_ACCESS_CONFIDENT_FAIL: Section 5.3.

CS_SUFFICIENT: Section 5.5.

REC_ADVANTAGE: Section 5.6.

Priority	Terminal result	Exact predicate	Scientific update
1	INVALID_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35	OPERATIONAL_VALID=false	No scientific update. Repair only the exact operational defect under the unchanged contract.
2	SOURCE_OR_COMMON_ACCESS_FAILURE_G35	Operationally valid and either SOURCE_VALID=false, or both REC_ACCESS_CONFIDENT_FAIL=true and CS_ACCESS_CONFIDENT_FAIL=true	Close this exact source/comparator package without choosing recurrence or current-state reduction.
3	CURRENT_STATE_REDUCTION_SUFFICIENT_G35	Source valid and CS_SUFFICIENT=true	Support the fully informed current-state controller as sufficient within G35-P0. Retire learned actor recurrence as load-bearing in this exact family, not globally.
4	RECURRENT_STATE_INDUCTIVE_BIAS_ADVANTAGE_G35	Source valid and REC_ADVANTAGE=true	Support a material finite-budget recurrent advantage under the frozen contract. Do not claim task-level recurrence necessity.
5	MIXED_UNDERPOWERED_REACTIVE_REDUCTION_G35	Every remaining valid pattern	Preserve both explanations and close the package without seed, budget, architecture, threshold, or margin rescue.

Branch evaluation stops at the first match.

Examples:

CS utility 0.93, REC utility 0.96, and UCB(Δ)=0.04 → CURRENT_STATE_REDUCTION_SUFFICIENT_G35.

CS utility 0.91, REC utility 0.97, and LCB(Δ)>0.05 with positive per-capacity lower bounds → RECURRENT_STATE_INDUCTIVE_BIAS_ADVANTAGE_G35.

Both arms pass but Δ CI is [0.03,0.07] → MIXED_UNDERPOWERED_REACTIVE_REDUCTION_G35.

No mapping diagnostic, parameter drift, training curve, or historical G32 checkpoint may relabel these branches.

7. EVIDENCE_COMPLEXITY
7.1 Search complexity
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

The action introduces no candidate search, rollout oracle, beam, tree, or simulated counterfactual. It is therefore below the project’s O(H*K_search) and 16H hypothetical-transition ceiling.

7.2 Exact bounded nonformal exercise
replicates=1
arms=2
fast_updates_per_arm=10
return_to_go_updates_per_arm=10
environments_per_update=8
ppo_passes=2
evaluation_cells=33
evaluation_episodes_per_cell=8
bootstrap_resamples=250

Real transitions:

T
train,nf
	​

=2×20×8×48=15,360,
T
eval,nf
	​

=33×8×48=12,672,
T
total,nf
	​

=28,032.

The complete nonformal train/evaluate/analyze exercise must finish within:

1,200 seconds.

It can return only a nonformal path-completion result.

7.3 Exact formal inventory

Training:

T
train,formal
	​

=2×3×200×8×48=460,800.

Evaluation:

T
eval,formal
	​

=99×128×48=608,256.

Total real transitions:

T
formal
	​

=1,069,056.

Additional inventory:

formal_training_episodes=9600
formal_evaluation_cells=99
formal_evaluation_episodes=12672
formal_optimizer_steps=3600
bootstrap_resamples=10000
7.4 Wall-clock projection gate

The bounded nonformal exercise must record separate:

T_train_nf
T_eval_nf
T_analysis_nf

The frozen conservative formal projection is:

T
projected,formal
	​

=1.25(30T
train,nf
	​

+48T
eval,nf
	​

+40T
analysis,nf
	​

).

Formal execution is scientifically admissible only if:

T
projected,formal
	​

≤28,800 seconds.

Failure is:

NON_EXECUTABLE_EVIDENCE_DESIGN

and is not an algorithm result or consumed scientific iteration. The project policy separately caps the nonformal exercise at 20 minutes and the formal iteration at eight hours.

8. CODE_SCIENCE_MAPPING
Scientific field	Existing surface or one minimal G35 symbol	Binding correspondence
common current encoding	ContinuousRosterPolicy.member_encoder	identical tensor, initialization, input, and gradient authority in both arms
active-set context	ContinuousRosterPolicy.context_encoder	same active-member sum and raw log-count
anonymous order and prefix	ContinuousRosterPolicy._routing_order and routing loop	identical ordering and active-fraction prefix
matched recurrence treatment	minimal new symbol G35MatchedStateCarryPolicy	implements u=GRUCell(x,e+ch), h
+
=cu, with nontrainable carry_mode
current-state access witness	common G35MatchedStateCarryPolicy.current_readout	one shared zero-initialized Linear(10,2) present and trainable in both arms
action distribution	inherited continuous policy distribution	identical tanh-Gaussian, log_std, likelihood, entropy, teacher replay, and noise
centralized critic	inherited capacity-independent critic	identical current-state critic; no actor carry input
G31 credit	compute_return_to_go_credit and optimize_return_to_go_direction_balanced_update	unchanged detached future tail and direction-balanced actor update in both arms
fixed training source	G32 make_ledger, collect_trajectory, and lifecycle environment	capacity-8 fixed process and member-owned streams unchanged
random held-out source	G34 make_process_ledgers and random/fixed environment dispatch	exact P0 times, orders, profiles, cohort ownership, and pairing
initial gradient audit	minimal new symbol g35_initial_gradient_audit	uses actual inherited objectives; no optimizer step or synthetic loss
paired training	minimal new symbol g35_train_paired_replicate	materializes one shared batch before either arm updates
estimands and bootstrap	minimal new G35 analyzer symbols	one whole-episode paired plan for arms, capacities, checkpoints, and process cells
first-match disposition	minimal new select_g35_result_branch	exact priority in Section 6
checkpoint identity	minimal G35 checkpoint schema	binds replicate, arm mode, phase exposure, capacity-independent state shapes, and final-only selection

The current code already provides the relevant member encoder, active-set aggregation, GRU routing, action distribution, and state-independent critic surfaces.

Scientific and frozen

the actor equations;

carry constants;

common current readout;

exact state-dict equality rule;

information fields;

training/evaluation sources;

seeds and exposure;

access gates;

Δ
rec
	​

;

0.05 margin;

confidence unit;

first-match order;

complexity inventory.

Implementation-only

file and class names beyond the minimal scientific symbol;

tensor storage;

vectorization;

batching layout;

serialization format;

telemetry organization;

checkpoint file names;

proof-sized test-file organization.

Any implementation that replaces the exact carry treatment with width matching, parameter freezing, recurrent-state zeroing of a previously trained model, or removal of age/previous-action/time is scientifically nonconforming.

9. ONE_NEXT_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary becomes eligible only after PM has technically accepted one exact pushed implementation of the frozen contract.

Its sole scientific question is:

Does the accepted code instantiate the exact shared-parameter carry treatment, common current-state access path, fresh paired exposure, G31 credit identity, G32/G34 source pairing, registered estimands, 0.05 branch margin, whole-episode confidence procedure, and first-match semantics without introducing an arm-specific capacity, information, optimization, or checkpoint route?

It is a read-only conformance diff. It may not add or alter an arm, source, margin, seed, evidence volume, or result branch.

This disposition authorizes no implementation, Git operation, nonformal exercise, formal run, monitoring, or successor child.

10. 中文简报

本轮裁决是：

IDENTIFIABLE_EMPIRICAL_REACTIVE_REDUCTION_G35_DESIGN

G35 可以形成有效比较，但不能把问题写成“这个任务在理论上必须使用 recurrence”。

原因是当前 toy 已把：

current load；

target mix；

capability；

active count；

true time；

lifecycle age；

previous actions

全部暴露给 actor。仅凭当前 load 和 mix，就存在一个无跨步 hidden 的高分策略。因此 G35 能判断的是：

强 current-state/feedforward 方法是否已经足够；

在完全匹配的信息、参数量、credit 和训练预算下，recurrence 是否提供有限预算的学习优势。

两个 arm

两臂使用完全相同的参数、网络宽度、critic、G31 credit、action distribution 和 current observation。

唯一差别是一个不可训练的 carry 开关：

REC: carry=1
CS:  carry=0

共同 actor cell 为：

u
t
	​

=GRUCell(x
t
	​

,e
t
	​

+carry⋅h
t
	​

).

REC 把 u
t
	​

 带到下一步；CS 每一步都把 carried hidden 清零。两臂仍看到相同的 age、previous action 和 true time。

为了避免 CS 因表达力不足而失败，两臂共同拥有一个零初始化的 current-observation linear readout。它不是额外 treatment。用这个 readout，仅把 load 和 mix 映射到 pre-tanh mean，就能构造一个每步 reward 下界约为 0.94048 的无记忆策略，高于所有主要 access floor。

训练与评价

每个 arm、每个 replicate：

capacity 8；

100 fast updates；

100 return-to-go updates；

8 个完整 episode/update；

2 次 PPO pass；

Adam 1e-3；

完全相同的 G31 realized-future-tail credit。

正式规模：

3 paired replicates
2 arms
460800 training transitions
99 evaluation cells
608256 evaluation transitions
1069056 total real transitions

评价继续使用 G34-P0 的 fixed/random、capacity 6/8/12、deterministic/stochastic cells。

主估计量
Δ
rec
	​

=U
REC
	​

−U
CS
	​

.

materiality margin 固定为：

0.05.

若 CS 达到绝对 access，且 REC 相对 CS 的 95% 上界在 pooled 和每个 capacity 上都不超过 0.05，结果是：

CURRENT_STATE_REDUCTION_SUFFICIENT_G35

这包括“CS 略低于 REC、但差距不超过 5 个 utility point”的情况。

只有当 REC 达到 access、pooled 差距的下界严格大于 0.05，并且每个 capacity 的差距下界都严格大于零，才能得到：

RECURRENT_STATE_INDUCTIVE_BIAS_ADVANTAGE_G35

即使如此，也只能说明在该训练预算和 source 下 recurrence 有学习优势，不能说任务在理论上必须 recurrence。

其余正式分支为：

INVALID_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35
SOURCE_OR_COMMON_ACCESS_FAILURE_G35
MIXED_UNDERPOWERED_REACTIVE_REDUCTION_G35
复杂度
H=48
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

完整 nonformal 必须低于 20 分钟；基于分阶段实测的保守 formal 投影必须低于 8 小时，否则返回 NON_EXECUTABLE_EVIDENCE_DESIGN，而不是算法失败。

下一边界是：

CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_ALIGNMENT_AUDIT

本回复只冻结科学合同，不授权写代码、Git、非正式运行或正式计算。
