1. Compact frozen-value table

The following contract preserves the already-frozen G2 source: unchanged S7-S3 physics, four-dimensional continuous actions, external QoS/safety reward, eight physical UAVs, 1,500 steps, 160 Wh batteries, two one-slot 1,000 W charging stations, no temporary failures, the three registered initial-energy profiles, charge-induced service LEAVE/REJOIN, current-only information, matched learned arms, common access formula, bootstrap construction, and comparative margins.

1.1 Source-identification controls
Protected field	Frozen G2 value
Constructive control name	CONSTRUCTIVE_CHARGE_ROTATION
No-reallocation control name	NO_PROACTIVE_ROTATION
Learned status	Both controls are deterministic, evaluation-only and receive zero optimizer exposure. They are never learned comparators.
Common initial service controller	On a copy of the current environment state, apply the existing deterministic Scenario-7 QoS-layout search to obtain service/relay target positions. During rollout, each service-active UAV legally tracks its assigned target through the unchanged velocity/action conversion. Both controls use the same target set and actions before the constructive controller’s first planned charging departure.
Constructive candidate set	At reset and after each completed REJOIN, forward-simulate the unchanged energy model under target tracking to the episode horizon. A UAV is a charging candidate iff its projected no-charge terminal return-energy margin is negative. If the set is empty, the source-pressure predicate fails; the controller must not force an unnecessary charging session.
Candidate order	Increasing projected no-charge terminal margin; ties by physical storage index.
Station assignment	Nearest charging station; ties by station index. If that station is occupied in the planned schedule, use the earliest legal station slot.
Departure and travel	Depart at the latest integer physical step that permits arrival inside the capture radius with battery strictly above the service-cutoff threshold. Outside the charging radius use the legal maximum-speed direction to the station; inside it use the unchanged docking-speed limits. Dock request remains active.
Service LEAVE	Exactly the frozen source rule: first pre-action boundary at which dock request is active and the UAV is within the capture radius, including queueing for a full station. Return transit remains service-active.
Inactive evolution	No service-policy action or likelihood. Physical position, battery, queue wait and charging continue under the same deterministic inactive physics in both learned representations.
Charge completion	Remain captured/queued and request docking until battery ratio first reaches 0.80; REJOIN occurs at the next pre-action boundary. The restored service recurrence is used before the next policy action.
Survivor reallocation	Constructive control recomputes the deterministic service targets immediately after every service LEAVE and REJOIN.
No-reallocation behavior	It follows the common service controller until the constructive controller’s first planned departure. At that boundary it freezes the current service targets and never voluntarily requests docking. Existing emergency limp-home, cutoff, depletion and physical dynamics remain active; they may not be disabled.
Constructive future information	No future user trajectory, future channel realization, future queue state or learned-policy randomness. It may use the known 1,500-step horizon, current physical state, current station geometry, exact deterministic energy equations and forward simulation of its own scripted actions.
No-reallocation information	Exactly the same information as the constructive control.
Control ledgers	The same 128 episode ledgers per energy profile and replicate used by learned-arm evaluation.

The source script intentionally uses the repository’s existing charging semantics: charging requires a dock request, capture and sufficiently low realized speed; finite station capacity selects among eligible candidates; battery continues to incur propulsion/hover consumption while charging. The existing static certificate already accounts for travel, station contention, propulsion energy, net charging power and temporary service loss, but G2’s formal control must evaluate the above legal rollout rather than treating that static certificate as a learned score.

1.2 Source-identifiability predicates

The parent’s mean(J_constructive) ≥ 0.90 and LCB95(J_constructive−J_no-reallocation)>0.10 do not apply unchanged to J_event in G2. Charge timing is endogenous: a no-reallocation controller can avoid voluntary service absence, obtain an empty or delayed event window, and appear favorable while accumulating return risk or terminal energy failure. G2 therefore uses an exact safety-adjusted control score while leaving learned-arm J_event, J_rejoin and Q_ordinary unchanged.

For control k in episode e, define:

c
e,t
	​

=min(
0.05
max
i
	​

max(0,−m
i,t
	​

)
	​

,1),

where m
i,t
	​

 is the unchanged raw return-energy margin. Let n
e,t
cut
	​

 and n
e,t
dep
	​

 be the numbers of newly triggered cutoff and depletion events at step t. Define:

ϕ
e,t
	​

=ρ
e,t
	​

−2c
e,t
	​

−5n
e,t
cut
	​

−10n
e,t
dep
	​

,
Φ
e
	​

=
1500
1
	​

t=0
∑
1499
	​

ϕ
e,t
	​

.

This is exactly the existing safety_reward_before_pbrs averaged over the episode; it excludes graph-PBRS so source identification is not driven by a potential boundary. The current environment computes return cost from the worst negative return margin, caps it at one, applies coefficient two, and separately applies one-time cutoff and depletion penalties.

For each of IID, LOW_ENERGY and SYNCHRONIZED_PRESSURE, all of the following must pass:

mean(Φ
constructive
	​

)≥0.90,
LCB
95
	​

(Φ
constructive
	​

−Φ
no-rotation
	​

)>0.10.

Additional exact source predicates are:

Predicate	Boundary
Constructive cutoff events	exactly 0 across all control episodes
Constructive depletion events	exactly 0 across all control episodes
Constructive return-risk cost	c
e,t
	​

=0 for every control row
Completed charge cycles, IID	at least 128 complete LEAVE→REJOIN cycles per replicate
Completed charge cycles, each held-out profile	at least 256 complete cycles per replicate
Recovery-window support	every counted rejoin occurs by physical step 1440, leaving the complete 60-step recovery window
Station-capacity use	at least one occupied station in every control episode
Synchronized-pressure concurrency	at least 64/128 episodes per replicate contain at least two simultaneously service-inactive charging lifecycles
No-charge pressure	at least 96/128 no-reallocation episodes per profile have either a positive return-risk step, a cutoff event or a depletion event
Physical consistency	every charging cycle obeys capture, queue-capacity, net-charge, cutoff and 0.80 rejoin semantics

Equality passes for count and fraction floors; the two performance inequalities retain their stated strictness.

1.3 Energy-safety admission for learned arms

For arm a, energy profile p, action mode m, and episode e, define:

Z
a,p,m,e
cat
	​

=1[N
a,p,m,e
cut
	​

+N
a,p,m,e
dep
	​

>0],
F
a,p,m
cat
	​

=E[Z
a,p,m,e
cat
	​

],

and

R
a,p,m
return
	​

=E[
1500
1
	​

t=0
∑
1499
	​

c
a,p,m,e,t
	​

].

An arm is energy-safety admitted iff, in every registered profile and action mode,

UCB
95
	​

(F
a,p,m
cat
	​

)≤0.05

and

UCB
95
	​

(R
a,p,m
return
	​

)≤0.05.

Equality passes.

These are absolute learned-arm access guardrails:

not source-validity predicates—the constructive controls carry that role;

not open-versus-mask noninferiority estimands;

not descriptive diagnostics;

not alterations to the S7-S3 reward.

Separate cutoff fraction, depletion fraction, maximum deficit, charging-session count and queue duration remain descriptive decompositions. The conclusion-bearing catastrophe statistic is their combined episode indicator above. The environment already records one-time cutoff/depletion events, return-risk steps, cumulative return cost and maximum return deficit.

1.4 Formal exposure and evaluation cells
Field	Frozen value
G1 prerequisite	G2 may start only after G1 produces a valid non-INVALID terminal disposition. No partial G1 runtime value is G2 evidence.
Learned arms	FIXED_MASK_REC, PREFIX_NORMALIZED_OPEN_ROSTER
Paired replicates	3
Parallel environments per arm/replicate	8
Trajectory and rollout length	1500 physical steps
Updates per arm/replicate	128
Environment transitions per arm/replicate	8×1500×128=1,536,000
PPO passes per update	4
Optimizer steps	one full collected recurrent batch per pass: 512 actor/critic steps per arm/replicate
Training profile	IID energy multiset only
Evaluation profiles	IID, LOW_ENERGY, SYNCHRONIZED_PRESSURE
Action modes	deterministic and stochastic
Access cells	six separate cells: profile × action mode
Evaluation episodes	128 per cell, arm and replicate
Evaluation batch size	16 complete episodes
Controls	128 paired ledgers per profile and replicate
Checkpoint rule	final update-128 checkpoint only
Best-checkpoint selection	prohibited
Bootstrap	hierarchical paired percentile bootstrap, 10,000 resamples; replicate first, then whole paired episode IDs
Comparative estimand domain	both held-out profiles and both action modes, paired and pooled through the registered hierarchy
Backend	registered CPU, one thread; no cross-backend resume or equivalence claim

Exact seed integers are implementation-only, as long as the following scientific coupling is preserved:

three disjoint replicate namespaces;

G2 namespaces fresh and disjoint from G1;

paired arms share task, initial-energy permutation, station geometry, user mobility, channel and evaluation ledgers;

paired stochastic evaluation uses common action uniforms;

base model initialization is paired;

training, evaluation, controls and bootstrap never reuse generator state;

checkpoint resume restores every owned RNG exactly.

The current question explicitly excludes in-flight G1 artifacts from evidence and requires that its eventual result not modify G2.

2. Exact mathematical predicates and branch order
2.1 Registered learned-arm metrics

For profile-mode cell c, retain the parent definitions:

A
a,c
	​

=min(
0.80
J
event,a,c
	​

	​

,
0.90
Q
ordinary,a,c
	​

	​

),A
a
	​

=
c
min
	​

A
a,c
	​

.

Here c ranges over the six profile-mode cells. Dynamic-versus-mask estimands retain the frozen margins:

G
svc
	​

=E[J
event,open
	​

−J
event,mask
	​

],
G
rejoin
	​

=E[J
rejoin,open
	​

−J
rejoin,mask
	​

],
G
ordinary
	​

=E[Q
ordinary,open
	​

−Q
ordinary,mask
	​

].

The mechanism comparisons use the two held-out profiles and both action modes. The parent contract requires strict lower bounds of 0.03 and 0.02, plus ordinary-service noninferiority at −0.02; fixed-mask sufficiency uses the corresponding upper bounds.

2.2 Arm-level access classification

Define:

SafePass(a)⟺
p,m
⋀
	​

[UCB(F
a,p,m
cat
	​

)≤0.05∧UCB(R
a,p,m
return
	​

)≤0.05],
SafeFail(a)⟺
p,m
⋁
	​

[LCB(F
a,p,m
cat
	​

)>0.05∨LCB(R
a,p,m
return
	​

)>0.05].

Then:

AccessPass(a)⟺LCB(A
a
	​

)≥1∧SafePass(a),
AccessFail(a)⟺UCB(A
a
	​

)<1∨SafeFail(a).

Every other arm-level pattern is access-underpowered.

2.3 First-match branches
Priority	Terminal result	Exact condition	Smallest scientific update
1	INVALID_UAV_CHARGE_ROTATION_G2	Any reward, probability, continuous-action density, mask, service-lifecycle, inactive-row, physical-evolution, RNG, replay, checkpoint, parameter/exposure matching, count or provenance invariant fails	No scientific update. Repair only the operational defect under the identical contract.
2	SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2	Any energy-profile law, control behavior, source-support, no-future-leakage, constructive feasibility, load-bearing contrast or control-safety predicate fails	Close this exact charge source definition. Infer neither learner access nor mask/dynamic value.
3	NO_ACCESS_UAV_CHARGE_ROTATION_G2	Source valid and both learned arms satisfy AccessFail	Close only this G2 source–learner pair. Do not infer mask sufficiency or dynamic advantage.
4	UNDERPOWERED_ACCESS_UAV_CHARGE_ROTATION_G2	Source valid, no arm has AccessPass, and at least one arm is access-underpowered	Close under the frozen exposure. No seed, update or evaluation expansion.
5	USABLE_MASK_SUFFICIENT_UAV_CHARGE_ROTATION_G2	AccessPass(FIXED_MASK_REC) and UCB(G
svc
	​

)≤0.03 and UCB(G
rejoin
	​

)≤0.02	Support correctly masked fixed-slot recurrence as sufficient for the registered charging profiles. Do not generalize to burst, temporary loss, terminal loss or composition.
6	DYNAMIC_LIFECYCLE_SUPPORTED_UAV_CHARGE_ROTATION_G2	AccessPass(PREFIX_NORMALIZED_OPEN_ROSTER) and LCB(G
svc
	​

)>0.03 and LCB(G
rejoin
	​

)>0.02 and LCB(G
ordinary
	​

)≥−0.02	Support a local dynamic-service-lifecycle advantage for charge rotation with continuing inactive physical state.
7	MIXED_ANOMALOUS_UAV_CHARGE_ROTATION_G2	Every remaining valid access-positive pattern	Preserve both explanations and close G2 unresolved. No post-result stratum, threshold or budget rescue.

Branches stop at the first match. An arm whose QoS access passes but whose safety interval confidently fails does not count as accessed.

2.4 Promotion consequences
G2 result	Isolated burst source	Later composition
INVALID	blocked pending identical-contract operational repair	prohibited
SOURCE_NON_IDENTIFIABLE	remains an independent legal source	prohibited
NO_ACCESS	remains an independent legal source	prohibited
UNDERPOWERED_ACCESS	remains an independent legal source	prohibited
USABLE_MASK_SUFFICIENT	proceed independently	eligible only if G1 did not also resolve confidently in favor of mask sufficiency, and burst later becomes identifiable and accessible
DYNAMIC_LIFECYCLE_SUPPORTED	proceed independently	eligible after burst is identifiable and accessible
MIXED_ANOMALOUS	proceed independently	eligible after burst is identifiable and accessible, because G2 has not resolved confidently for mask sufficiency

Composition still requires all three isolated sources to be source-identifiable and access-positive, plus at least one genuine membership source not confidently resolved for fixed-mask sufficiency. A failed isolated source cannot be renamed or modified to satisfy that condition.

3. Minimal formal evidence schedule
Phase A — conclusion-bearing source screen

Before creating or optimizing either learned model:

Materialize 128 paired ledgers for each of IID, LOW_ENERGY and SYNCHRONIZED_PRESSURE, for each of three replicate namespaces.

Run CONSTRUCTIVE_CHARGE_ROTATION and NO_PROACTIVE_ROTATION.

Validate:

initial-energy permutations;

station and energy physics;

charge candidate ordering and station allocation;

service LEAVE, inactive deterministic evolution and 0.80 REJOIN;

control support counts;

exact safety conditions;

per-profile Φ reachability and strict contrast.

Apply branch 1 or branch 2 immediately if applicable.

If branch 2 fires, learned training is skipped. The control rows are the formal source evidence and are not regenerated after inspecting the result.

Phase B — paired learned exposure

Only after the source screen passes:

initialize both learned arms with paired common parameters and exact parameter count;

run three paired replicates;

collect eight complete 1,500-step trajectories per update;

run 128 updates and four full-batch recurrent PPO passes per update;

preserve identical episode ledgers, interactions and optimizer exposure;

save continuation state after complete updates, but designate only update 128 as conclusion-bearing.

Phase C — final paired evaluation

For each arm and replicate, evaluate update 128 in:

IID_DETERMINISTIC
IID_STOCHASTIC
LOW_ENERGY_DETERMINISTIC
LOW_ENERGY_STOCHASTIC
SYNCHRONIZED_PRESSURE_DETERMINISTIC
SYNCHRONIZED_PRESSURE_STOCHASTIC

Each cell contains 128 episodes, evaluated in batches of 16. Record:

J_event;

J_rejoin;

Q_ordinary;

catastrophe episode indicator;

mean capped return-cost burden;

cutoff and depletion decompositions;

complete charge LEAVE/REJOIN counts;

deterministic and stochastic action-path evidence;

all registered paired differences.

Phase D — one terminal analysis

Use the frozen 10,000-resample hierarchy and emit exactly one first-match result. A valid negative is terminal for this source: no threshold, reward, observation, seed, model, budget, profile or name rescue. This follows the durable rule that a benchmark no-access or non-identification result updates only its benchmark–comparator pair and cannot be rescued by post-result tuning.

This schedule is a scientific recommendation only. It does not authorize source realization or execution; those authorities remain outside this scoped review.

4. 中文说明

G2 测试的是：

在固定 8 架物理 UAV 的前提下，充电、排队和返航使部分 UAV 暂时退出通信服务时，显式的 service lifecycle 是否比“固定槽位 + 正确 availability mask + hidden 冻结/恢复”的普通 recurrent MARL 更有价值。

物理 UAV 在充电缺席期间并没有消失。它的位置、电量、排队和充电过程继续演化；消失的只是它的服务策略 lifecycle：

不产生通信动作；

不进入 actor active set；

不产生 action likelihood 或 PPO loss；

recurrent state 冻结；

电量达到 0.80 后恢复同一 lifecycle。

首要控制不是 learned baseline，而是两个 source-identification 控制：

CONSTRUCTIVE_CHARGE_ROTATION：按当前能量和充电站容量进行可行的轮换充电，并在成员离开或归队后重新分配服务位置；

NO_PROACTIVE_ROTATION：保持充电前的服务目标，不主动安排充电，只接受原环境的紧急返航、cutoff 和 depletion 后果。

临时失联源中使用的 J_event 对充电源不能直接承担 source-identification：不主动充电可能暂时保持较高 QoS，却在后期产生 return-risk、cutoff 或 depletion。因此 G2 的 source screen 使用现有未加 PBRS 的安全奖励：

ρ
t
	​

−2c
t
	​

−5n
t
cut
	​

−10n
t
dep
	​

,

要求 constructive 平均至少 0.90，并且相对 no-rotation 的 95% 下界严格大于 0.10。

learned arm 还必须通过独立安全 admission：

发生 cutoff 或 depletion 的 episode 比例 UCB 不超过 0.05；

平均 return-constraint burden 的 UCB 不超过 0.05。

第一轮 G2 可以得到的结论只有三类实质性结果：

两种方法都不能安全访问该充电源；

正确实现的固定-agent mask 已足够；

open-roster lifecycle 在充电缺席和归队恢复上有冻结 margin 以上的优势。

它不能证明局部需求 burst、临时失联、terminal loss、组合鲁棒性、任意规模或 learned skill lifetime。Burst 仍是独立的下一源；组合只有在三个独立源都可识别且可访问，并且至少一个真实 membership 源没有明确支持 mask sufficiency 时才允许进入。

本回复冻结科学证据合同，不授权实现或计算。
