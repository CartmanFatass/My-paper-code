1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=IDENTIFIABLE_BOUNDED_RANDOM_PROCESS_G34_DESIGN
source_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0
algorithm_change=none
training_change=none
g34_optimizer_steps=0
checkpoint_selection=exact_G32_zero_and_final_only

G34-P0 freezes a zero-shot evaluation source, not a new algorithm. It asks whether the exact three G32 final checkpoints retain usable control when the fixed three-event process at steps 12/24/36 is replaced by one bounded four-event random-process family.

The retained facts are:

horizon remains 48;

configured capacity is selected before a trajectory and is one of 6/8/12;

all checkpoints were trained only at capacity 8;

G34 performs no optimizer update;

actor, critic, recurrence, action support, reward, G31 credit identity, lifecycle ownership and checkpoint tensors are unchanged;

G33 and its derivatives remain excluded.

G32 remains exactly USABLE_RUNTIME_CAPACITY_G32. It already establishes strict-load transport across capacities 6, 8 and 12 and exact inactive-padding invariance, but not membership-process-law invariance.

The smallest new claim eligible for support is:

Within G34-P0 only, the frozen G31/G32 controller transports without retraining from G32’s fixed three-event schedule to episode-random event times and a held-out four-event lifecycle ordering family.

Success cannot establish arbitrary process laws, arbitrary horizon, capacities outside 6/8/12, UAV transport, recurrence necessity, G31-credit necessity, asynchronous skill lifetime, intrinsic-reward value or comparative superiority.

2. EXACT_RANDOM_PROCESS_CONTRACT
2.1 Unchanged physical/task process

G34 retains the G32 continuous-service task exactly:

horizon=48
action_dim=2
observation_dim=10
critic_state_dim=6
load_blocks=12
load_block_length=4
load_support=Uniform[0.30,0.70]
target_mix_support=Uniform[0.25,0.75]
capability_support=Uniform[0.75,1.25]^2
reward=unchanged_relative_service_matching_utility

The actor continues to receive capability, presentation priority, current load, current target mix, log1p(active_count), active lifecycle age, two previous actions and normalized absolute time. The critic continues to receive current load, target mix, active capability sums, log1p(active_count) and normalized absolute time.

The constructive action remains:

a
i
(0)
	​

=2load
t
	​

−1,a
i
(1)
	​

=2mix
t
	​

−1

for every active member, and zero for inactive rows. Under the unchanged reward equation this gives exact target service at every valid active roster.

2.2 Paired base ledger

Every G34 random-process episode begins from an exact G32 base ledger. The paired random and fixed-reference branches share byte-identical:

initial lifecycle keys;

temporarily absent cohort;

fresh-join cohort;

terminal-leave cohort;

member capabilities;

presentation priorities;

load trace;

target-mix trace;

stochastic action noise.

Only the membership-event schedule differs.

Configured-capacity profile support is:

Capacity	Base G32 profile support
6	small_4_2_6_3
8	train_4_3_6_5, train_5_3_7_6, train_6_4_8_6
12	large_6_3_10_7

For capacity 8, the three profiles occur in counts 43/43/42 within each replicate; the profile receiving 42 episodes rotates with replicate index. Across three replicates, each profile therefore occurs exactly 128 times.

2.3 Event-count and time support

Every random-process episode contains exactly four policy-relevant membership events:

event_count_support={4}

Define:

T
4
	​

=
⎩
⎨
⎧
	​

(t
1
	​

,t
2
	​

,t
3
	​

,t
4
	​

):
5≤t
1
	​

<t
2
	​

<t
3
	​

<t
4
	​

≤43,
t
j+1
	​

−t
j
	​

≥5,
t
j
	​

mod4

=0
	​

⎭
⎬
⎫
	​

.

Each event-time tuple is sampled uniformly without replacement from T
4
	​

 within each (replicate, capacity) cell.

Consequences:

no event occurs at G32’s trained event times 12/24/36;

no event coincides with a four-step load/target-mix block boundary;

the initial segment has at least five steps;

every pair of events is separated by at least five steps;

the final event leaves at least five active evaluation steps;

there are no event collisions.

Events are applied pre-action at their registered physical step. The resulting membership change is visible in the current active mask, count, lifecycle age and observations before the current action is sampled.

2.4 Edit-type ordering

Use the symbols:

L = temporary leave
R = rejoin the complete L cohort
J = fresh join
T = terminal leave

Every episode contains each symbol exactly once. The event-order support is:

Σ={(L,R,J,T),(L,J,R,T),(J,L,R,T)}.

Orders occur in counts 43/43/42 per replicate and capacity, with the 42-count order rotated by replicate. Across the three replicates, every order occurs exactly 128 times per capacity.

The temporary, fresh and terminal cohorts are the exact cohorts already sampled by the paired base G32 ledger. This order support guarantees that:

a rejoin never precedes its leave;

every terminally leaving lifecycle is active at T;

fresh lifecycles begin with zero age, zero previous action and zero recurrent state;

temporary absence freezes age, previous action and recurrent state;

rejoin restores that lifecycle;

terminal leave deletes recurrent ownership before the current action;

unaffected survivors remain continuous.

2.5 Exact active-count trajectories

The registered trajectory includes the initial count followed by the count after each of the four events.

Capacity/profile	L,R,J,T	L,J,R,T	J,L,R,T
6: small_4_2_6_3	4→2→4→6→3	4→2→4→6→3	4→6→4→6→3
8: train_4_3_6_5	4→3→4→6→5	4→3→5→6→5	4→6→5→6→5
8: train_5_3_7_6	5→3→5→7→6	5→3→5→7→6	5→7→5→7→6
8: train_6_4_8_6	6→4→6→8→6	6→4→6→8→6	6→8→6→8→6
12: large_6_3_10_7	6→3→6→10→7	6→3→7→10→7	6→10→7→10→7

No registered trajectory is empty or exceeds its configured capacity.

2.6 Exact fixed-schedule reference

For every random episode, the paired fixed reference uses its same base ledger but the exact G32 process:

t=12: L
t=24: atomic R+J
t=36: T

Thus the fixed and random branches share all source values and lifecycle cohorts. Their only scientific difference is:

fixed: 3 events, fixed times, fixed composite order
random: 4 events, held-out times, split R/J, one of three held-out orders
2.7 RNG ownership and episode addressing

Freeze the following fresh G34 seed block:

base_ledger_seed_base=10340000
process_seed_base=10341000
action_seed_base=10342000
bootstrap_seed=10343034

For replicate r∈{0,1,2}, add r exactly once to each non-bootstrap base.

For capacity C and local episode ID e∈{0,…,127}, use:

E(C,e)=10000C+e.

The exact G32 base ledger is generated from (base_ledger_seed_base+r, E(C,e)).

Process time-tuple permutation, type-order assignment and capacity-8 profile assignment use independent episode-addressed namespaces under:

SeedSequence(10341000+r,C,e,stream).

Action noise uses the existing member-owned action-stream construction with (10342000+r, E(C,e), member_key).

Fixed, random, zero, time-intervention and reactive-ablation branches retain the same episode and member-owned action streams.

Every (replicate, capacity) cell must contain 128 unique process signatures:

(time tuple,order,profile,L cohort,J cohort,T cohort).

No process signature may be excluded or replaced after evaluation.

3. HELD_OUT_AND_INFORMATION_BOUNDARY
3.1 Exact held-out distinction

G32 training used:

event_count=3
event_times=(12,24,36)
event_order=(L,atomic_R_plus_J,T)

G34-P0 uses:

event_count=4
event_times∈T4
event_times_mod_4!=0
event_order∈{LRJT,LJRT,JLRT}

Therefore every G34 random-process episode is outside checkpoint training in event count, event timing and event factorization. The checkpoint, task fields and learned interface remain unchanged. G32’s fixed event process and observation fields are repository facts, not G34 defaults.

This supports only a bounded held-out process claim. It does not sample arbitrary edit types, repeated leave/rejoin cycles, atomic replacement, arbitrary event count, horizon change or capacity change.

3.2 Future-event leakage prohibition

Neither actor nor critic receives:

event count;

future event times;

future edit order;

future cohort identities;

time to next event;

process-profile label;

random-process seed;

fixed-versus-random branch identity.

Absolute normalized physical time remains present because removing it would change the frozen checkpoint interface. Event times are independently sampled and never coincide with the trained event times or load-block boundaries.

3.3 Absolute-time diagnostic

At capacity 8 only, evaluate:

FINAL_RANDOM_TIME_ROTATED

Replace both normalized-time fields by:

τ
′
(t)=
47
(t+17)mod48
	​

.

All other observations, lifecycle state, hidden state, environment transitions and episode pairing remain unchanged.

Define:

D
time
	​

=U
time rotated
	​

−U
primary random
	​

.

This is an alternate-explanation diagnostic:

if the time-rotated arm accesses and is noninferior, fixed absolute time is not required;

if it confidently fails, absolute time remains load-bearing;

neither outcome relabels a valid primary transport result, because true absolute time is part of the frozen learned interface.

3.4 Reactive current-state diagnostic

At capacity 8 only, evaluate:

FINAL_RANDOM_REACTIVE_ABLATION

Before every forward step:

set all recurrent hidden rows to zero;

set lifecycle-age observation field to 0;

set both previous-action fields to 0.5, corresponding to neutral prior actions;

retain capability, presentation priority, current load, current target mix, log1p(active_count) and true normalized time.

Define:

D
reactive
	​

=U
reactive
	​

−U
primary random
	​

.

A passing reactive ablation supports the simpler explanation that current demand and current active-set information are sufficient. A failing ablation does not by itself prove recurrence necessary, because it is an intervention on a trained recurrent policy.

The existing G32 result already shows action means track current load and target mix with correlations above 0.9898 and MAEs below 0.0166; G34 must therefore preserve this simpler explanation rather than treating random-process access as recurrence evidence.

4. CONTROLS_AND_ALTERNATE_EXPLANATIONS
4.1 Registered cells

For each replicate and configured capacity:

Cell	Checkpoint/controller	Process	Action mode	Scientific role
CONSTRUCTIVE_RANDOM	exact constructive action	random	deterministic	Source feasibility
FINAL_RANDOM_DET	exact G32 final	random	deterministic	Primary process transport
FINAL_RANDOM_STOCH	exact G32 final	random	stochastic	Stability under registered policy noise
ZERO_RANDOM_DET	exact G32 zero	random	deterministic	Learned-gain reference
FINAL_FIXED_DET	exact G32 final	paired fixed	deterministic	Fixed-schedule checkpoint access and paired process reference
FINAL_FIXED_STOCH	exact G32 final	paired fixed	stochastic	Fixed-source stochastic control

At capacity 8 only, add:

FINAL_RANDOM_TIME_ROTATED
FINAL_RANDOM_REACTIVE_ABLATION

No learned comparison, retraining, new baseline or new credit estimator is introduced.

4.2 What each control can establish

Constructive random control

The constructive action must obtain:

every_step_reward>=1-2e-7
episode_utility>=1-2e-7
every_event_window>=1-2e-7
every_segment>=1-2e-7

for every source episode. This establishes source reachability, not checkpoint competence.

Fixed-schedule reference

This verifies that the exact checkpoint remains usable under its registered schedule with the new evaluation seed block. If this control confidently fails, random-process failure cannot be interpreted as process dependence.

Zero checkpoint

The random final-minus-zero contrast excludes a claim based only on favorable random initialization.

Time rotation

This estimates absolute-time reliance but does not change the primary claim.

Reactive ablation

This tests whether current-state mapping is a sufficient simpler explanation. Even a positive reactive result does not negate bounded process transport; it limits mechanism attribution.

4.3 Retained alternate explanations

Fixed-process dependence
The checkpoint may use the fixed 12/24/36 schedule or the trained composite edit order.

Reactive current-demand mapping
Current load and target mix directly define the constructive action, so process transport may require neither recurrence nor G31’s delayed-credit mechanism.

Lifecycle-state contribution
Frozen/restored hidden state may help at rejoin or after count shocks, but this is not inferred merely from primary access.

Absolute-time dependence
True time may remain behaviorally useful even though event times are random.

Only explanation 1 is conclusion-bearing for the main G34 branch. The other three are reported as mechanism annotations.

5. ESTIMANDS_GATES_AND_CONFIDENCE
5.1 Episode, segment and event-window quantities

For episode e, let r
e,t
	​

∈[0,1] be the unchanged service utility.

Episode utility:

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

Minimum step utility:

M
e
	​

=
t
min
	​

r
e,t
	​

.

For event times t
1
	​

,…,t
4
	​

, define four complete event windows:

W
j
	​

=[t
j
	​

,t
j
	​

+4),

and:

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

t∈W
j
	​

∑
	​

r
e,t
	​

.

Define five process segments:

S
0
	​

=[0,t
1
	​

),S
j
	​

=[t
j
	​

,t
j+1
	​

) (j=1,2,3),S
4
	​

=[t
4
	​

,48),

and:

P
e
	​

=
j=0,…,4
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

All event windows have denominator 4. All process segments have denominator at least 5.

Type-specific event-window utilities for L/R/J/T are also reported. Every episode contains every type exactly once, so those denominators are nonzero.

5.2 Paired contrasts

For capacity C:

Δ
C,e
process
	​

=U
C,e
final,random
	​

−U
C,e
final,fixed
	​

.

Combined learned gain:

Δ
e
learned
	​

=U
e
final,random
	​

−U
e
zero,random
	​

.

All differences are computed episode-paired within replicate and capacity.

5.3 Source and fixed-control gates

All structural lifecycle, schedule, pairing and checkpoint predicates must pass exactly.

The constructive source must satisfy every exact feasibility predicate in Section 4.2.

The fixed reference passes only if:

LCB
95
	​

(U
C
final,fixed,det
	​

)≥0.90∀C∈{6,8,12},
LCB
95
	​

(U
pooled
final,fixed,stoch
	​

)≥0.80,

and the minimum fixed-reference replicate mean is at least 0.85.

Equality passes.

5.4 Positive bounded-transport gates

SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34 requires all of:

LCB
95
	​

(U
C
final,random,det
	​

)≥0.90,
LCB
95
	​

(E
C
final,random,det
	​

)≥0.85,
LCB
95
	​

(P
C
final,random,det
	​

)≥0.85,
LCB
95
	​

(Δ
C
process
	​

)≥−0.05

for every C∈{6,8,12}, together with:

LCB
95
	​

(Δ
learned
)>0,
LCB
95
	​

(U
pooled
final,random,stoch
	​

)≥0.80,

and:

minimum_random_deterministic_replicate_mean>=0.85
all_lifecycle_gates=true
all_evaluation_optimizer_steps=0
all_checkpoint_state_before_equals_state_after=true

The −0.05 margin is a process-transport noninferiority boundary, not a superiority claim.

5.5 Alternate-explanation annotations

At capacity 8, the time-rotated or reactive control is classified as sufficient when:

LCB
95
	​

(U
control
	​

)≥0.90

and:

LCB
95
	​

(U
control
	​

−U
primary
	​

)≥−0.05.

It is classified as confidently load-bearing when either:

UCB
95
	​

(U
control
	​

)<0.90

or:

UCB
95
	​

(U
control
	​

−U
primary
	​

)<−0.05.

All remaining cases are annotation-underpowered.

These annotations never rescue or overturn the primary first-match branch.

5.6 Evidence unit and confidence

Freeze:

checkpoint_replicates=3
configured_capacities=6|8|12
episodes_per_capacity_per_replicate=128
bootstrap_resamples=10000
confidence_interval=95_percent_percentile
checkpoint_selection=exact_G32_zero_and_final
evaluation_optimizer_steps=0
episode_exclusions=none

One hierarchical paired bootstrap is generated with seed 10343034 and reused across registered estimands:

resample the three checkpoint replicates with replacement;

within each selected replicate and capacity, resample whole episode IDs;

retain every paired fixed/random/zero/stochastic/intervention branch for that episode;

never resample lifecycle rows, time steps, members, events or controls independently.

Every model-bearing cell must leave its checkpoint digest exactly unchanged.

5.7 Pass and fail witnesses

Positive source witness: constructive actions produce U=E=P=1.

Negative source witness: all active effort actions equal −1, giving zero served effort and utility 0 because load and both target components are strictly positive.

Positive process witness: random and fixed branches both implement constructive behavior, so Δ
process
=0.

Fixed-schedule dependence witness: a controller that acts correctly only around 12/24/36 passes the fixed reference and fails random event windows.

No-learned-gain witness: final and zero checkpoints produce identical utility, giving Δ
learned
=0.

Reactive-sufficiency witness: a direct load/mix mapping passes even when recurrent and history-bearing fields are neutralized.

Every scientific gate can therefore pass and fail for its intended reason.

6. FIRST_MATCH_TRUTH_TABLE

Define:

OPERATIONAL_VALID: exact artifact, checkpoint, strict-load, tensor-state, finite-value, zero-step, RNG, cell-inventory and evaluation-state invariants pass.

SOURCE_STRUCTURAL_VALID: process law, profile/order balance, time-tuple uniqueness, event boundaries, cohort ownership, count trajectories, denominators, lifecycle rules and constructive feasibility pass.

FIXED_CONTROL_PASS: all fixed-reference gates in Section 5.3 pass.

FIXED_CONTROL_CONFIDENT_FAIL: any fixed deterministic utility has UCB<0.90, fixed pooled stochastic utility has UCB<0.80, or a fixed-reference replicate mean is below 0.85.

RANDOM_PASS: every positive bounded-transport gate in Section 5.4 passes.

RANDOM_CONFIDENT_FAIL: any of the following holds:

for some capacity, UCB(U_random_det)<0.90;

for some capacity, UCB(E_random)<0.85;

for some capacity, UCB(P_random)<0.85;

for some capacity, UCB(Δ_process)<−0.05;

UCB(Δ_learned)<=0;

UCB(U_random_stoch_pooled)<0.80;

minimum deterministic replicate mean <0.85.

Priority	Terminal branch	Exact predicate	Scientific meaning
1	INVALID_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34	OPERATIONAL_VALID=false	No scientific update; repair only the exact operational defect.
2	SOURCE_OR_CONTROL_INVALID_RANDOM_PROCESS_G34	Operationally valid and either SOURCE_STRUCTURAL_VALID=false or FIXED_CONTROL_CONFIDENT_FAIL=true	The source or checkpoint-access control cannot support a process-transport inference. Close this exact G34 source; do not reinterpret G32.
3	FIXED_SCHEDULE_OR_PROCESS_DEPENDENCE_G34	Source valid, FIXED_CONTROL_PASS=true, and RANDOM_CONFIDENT_FAIL=true	The exact frozen checkpoint does not transport to the registered random-process family. G32 remains valid for its fixed family.
4	SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34	Source valid, FIXED_CONTROL_PASS=true, and RANDOM_PASS=true	Support zero-shot transport to G34-P0 only. Report time and reactive annotations separately.
5	UNDERPOWERED_RANDOM_PROCESS_G34	Every remaining valid numerical pattern	Close the frozen package unresolved; no seed, episode, threshold or profile expansion.

Branch evaluation stops at the first match. Time-rotation, reactive-ablation, correlation or MAE diagnostics cannot rescue an earlier branch.

7. DEGENERACY_AND_COMPLEXITY_AUDIT
7.1 Initial learning-signal audit

An initial gradient-path audit is inapplicable:

new_trainable_component=false
training=false
optimizer_steps=0

G34 evaluates immutable G32 zero and final checkpoints only.

7.2 Structural degeneracy checks

The source fails closed if any of the following occurs:

fewer or more than four events;

duplicate event time;

event time at a four-step load boundary;

separation below five steps;

empty roster or capacity overflow;

rejoin before temporary leave;

fresh lifecycle with nonzero hidden, age or previous action;

temporary hidden/age/action-state drift during absence;

survivor hidden discontinuity;

terminal hidden not deleted;

event or cohort information present in actor/critic inputs;

paired fixed/random source values or action streams differ;

duplicate process signature;

any zero denominator;

constructive reward below 1−2e−7;

evaluation optimizer step or checkpoint drift.

Because current load and target mix directly determine the constructive action, a positive G34 result cannot establish recurrence or delayed-credit necessity. The reactive ablation explicitly preserves that counterexample.

7.3 Search and wall-clock complexity
H=48
intrinsic_K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

The frozen formal inventory is:

20 cells per replicate
3 replicates
128 episodes per cell
48 real transitions per episode
total_cells=60
total_real_episode_transitions=368640

No result requires candidate search or simulated counterfactual trajectories. The design therefore lies strictly below the O(H*K_search), K_search<=16, 16H hypothetical-transition ceiling.

The contract is compatible in principle with the 20-minute nonformal and eight-hour formal ceilings, but PM must still perform the required prelaunch machine-specific measurement. Failure of that measurement is NON_EXECUTABLE_EVIDENCE_DESIGN, not a scientific result.

8. CODE_SCIENCE_MAPPING
Scientific field	Existing listed surface or minimal new G34 surface	Required correspondence
Frozen policy interface	ContinuousRosterPolicy.forward_step	No parameter, input-width, routing, recurrent, prefix, distribution or critic change. Active-set sum and log1p(active_count) remain unchanged.
Frozen G31 identity	compute_return_to_go_credit and G31 policy class	No optimizer call and no credit computation is required by G34; checkpoint identity must remain G31/G32.
Base source values	CapacityRosterLedger and make_ledger	G34 random and fixed branches must derive from the same exact base ledger. Member-owned streams and source values remain unchanged.
Random process	Minimal new G34 process ledger	Owns only the four event times and one of the three registered edit orders.
Lifecycle execution	Existing RuntimeCapacityRosterEnv ownership semantics plus minimal event-ledger dispatch	Event application becomes ledger-driven; observation, reward, age, previous action and lifecycle state semantics remain unchanged.
Constructive source control	Existing constructive_actions	Must retain exact current load/mix mapping and zero inactive rows.
Fixed reference	Existing G32 fixed-schedule environment	Uses the paired base ledger and exact 12/24/36 composite process.
Random final/zero evaluation	Existing checkpoint loader and evaluate_policy pattern	Strict-load at capacities 6, 8 and 12; no optimizer; exact before/after state identity.
Time diagnostic	Minimal evaluation-time observation transform	Alters only actor-time and critic-time coordinates according to the frozen permutation.
Reactive diagnostic	Minimal evaluation-time state transform	Zeros recurrent state and neutralizes only age/previous-action fields; model tensors remain unchanged.
Confidence and pairing	Existing hierarchical-CI and episode-cell analyzer surface	Three checkpoint replicates, whole-episode paired resampling, 10,000 draws and one first-match branch.
Operational validation	Existing G32 artifact/state/RNG/cell checks	Extend only to the G34 process inventory, paired cells and new branch predicates. G32 checks already fail closed on zero-step state drift, malformed cells and checkpoint mismatch.
Focused invariants	Existing two G32 test surfaces plus minimal G34 tests	Must cover process support, exact trajectories, lifecycle ownership, fixed/random pairing, controls, annotations and first-match witnesses.

File names, storage layout, vectorization, telemetry shape, batching and proof-sized test organization remain PM-owned implementation choices.

9. ONE_NEXT_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary occurs only after PM has accepted an implementation of the frozen G34-P0 contract and pushed one exact commit with the required code-science index.

The audit question is limited to:

Does the accepted implementation instantiate the exact four-event held-out process, paired fixed reference, immutable checkpoint evaluation, controls, estimands and first-match semantics frozen here, without creating another route to a positive branch?

It is a conformance diff only. It may return ALIGNED, MISMATCH or SCIENTIFIC_AMBIGUITY; it may not add a source, controller, threshold, evidence volume or algorithm.

This response grants no code, Git, nonformal or formal execution authority.

10. 中文简报

本轮冻结：

CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0

科研裁决是：

IDENTIFIABLE_BOUNDED_RANDOM_PROCESS_G34_DESIGN

它不训练新模型，只使用 G32 已经完成的三个 zero/final checkpoint，检查这些 checkpoint 是否能从固定事件表迁移到一个明确受限的随机 membership-process family。

随机过程

每个 episode 有 4 个事件：

L = temporary leave
R = rejoin
J = fresh join
T = terminal leave

允许三种顺序：

L,R,J,T
L,J,R,T
J,L,R,T

事件时间：

位于第 5–43 步；

相邻至少 5 步；

不允许落在 4 步 load/mix block 的边界；

因而不可能是训练时的 12/24/36。

Capacity 6、8、12 使用原 G32 的 cohort 大小和 source values，但事件被拆成四次并随机换时刻、换顺序。随机分支和固定分支共享 capability、load、target mix、成员 cohort 和 action noise。

主要对照

CONSTRUCTIVE_RANDOM：证明随机 source 本身可达；

FINAL_RANDOM：主要运输结果；

ZERO_RANDOM：证明不是随机初始化；

FINAL_FIXED：证明 checkpoint 在固定源上仍然可用；

TIME_ROTATED：检查是否依赖绝对时间；

REACTIVE_ABLATION：检查当前 load/mix 的直接映射是否已经足够。

后两个只是机制注释，不会救援或推翻主要分支。

成功门槛

每个 capacity 都必须满足：

deterministic utility 的 95% 下界至少 0.90；

最差 event-window 与 process-segment 的下界至少 0.85；

相对固定表的下降不超过 0.05；

final-minus-zero gain 下界严格大于 0；

pooled stochastic utility 下界至少 0.80；

最差 replicate mean 至少 0.85；

lifecycle、checkpoint 和 zero-optimizer 合同全部通过。

结果分支
INVALID_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34
SOURCE_OR_CONTROL_INVALID_RANDOM_PROCESS_G34
FIXED_SCHEDULE_OR_PROCESS_DEPENDENCE_G34
SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34
UNDERPOWERED_RANDOM_PROCESS_G34

如果固定表仍成功而随机过程明确失败，只能把 G32 收窄为固定过程族；不能改写已经成立的 capacity 6/8/12 结论。

复杂度为每 episode 一条普通 48-step trajectory：

intrinsic_K_search=0
hypothetical_transitions=0
nested_rollout=false

下一边界是代码完成后的：

CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_CODE_SCIENCE_ALIGNMENT_AUDIT

本回复只冻结科学合同，不授权实现或计算。
