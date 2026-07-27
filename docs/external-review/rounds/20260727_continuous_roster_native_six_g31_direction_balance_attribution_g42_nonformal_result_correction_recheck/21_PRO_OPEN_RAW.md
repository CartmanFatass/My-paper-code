1. REGISTERED_RESULT_CONFORMANCE
registered_nonformal_branch=
G42_NONFORMAL_DIRECTION_BALANCE_ATTRIBUTION_EXERCISE_COMPLETE

source_commit=6b8ea82d8fdbc76c14a414ff2b042a126f945dfb
aligned_implementation_commit=e21a1464e186260878649ad170bc3f32b8b9496d
formal_compute=false
valid_iteration_cost=0
operational_valid=true
operational_errors=[]

本轮同源 bounded preflight 与冻结 G42-P0 机械边界一致：

项目	已登记结果
运行环境	CPU、PyTorch 2.7.0+cpu、单线程
环境后端	必须使用 ContinuousRosterToyBatch C++ 后端；无 Python fallback
Train / evaluate / analyze	全部 COMPLETE，退出码均为 0
训练 transitions	7,680
评价 transitions	6,912
总 real transitions	14,592
Optimizer steps	40
Evaluation cells	24
Episodes per cell	6
Bootstrap resamples	250
实测总 wall time	67.6726204s
Nonformal 上限	1,200s
Formal 投影	2,498.876157s
Formal 上限	28,800s

该 evidence note 明确将自身限定为 runtime/artifact 事实，而非科学裁决、formal 授权或 successor selection。

代码科学状态也已闭合：G42 修复后的实现记录了受信任 G40 anchors、G41 no-slow projection、精确零梯度语义、按 actor group 与 baseline output 的梯度有效性、以及逐 replicate 的非共线 treatment gate；correction recheck 的正式原文为 AUDIT_DISPOSITION=ALIGNED。

因此，本轮最强机械结论是：

精确的 G42 runner 能够从受信任的只读 anchors 出发，完成 paired branch training、gradient/treatment-separation validation、固定/随机过程评价、artifact validation 和 hierarchical analysis，并在用户规定的时间与证据复杂度边界内结束。

这不等于任何一个 G42 科学分支已经被支持。

归档元数据差异

本轮用户指定并实际读取的 ref 是 8d6555ed0af8549c6517f06a81a750344a4af816，但 manifest 内嵌的 stage_commit 仍为 f6cdfab…；allow-list 与问题完全一致，因此这是归档字段差异，而不是第二证据源。

此外，当前问题明确给出 8 个剩余结论性轮次，而 allow-listed CURRENT_WORK.md 与冻结 G42 design raw 仍记录 6 个。本裁决按当前问题提供的 8 作为 question-scoped balance；该 6↔8 差异只需机械对账。无论采用哪一个值，当前均有可执行候选，因此 disposition 不变。

2. SCIENTIFIC_DISPOSITION
scientific_disposition=
EXECUTABLE_SAME_SOURCE_G42_PREFLIGHT_NO_SCIENTIFIC_CLOSURE
最强受支持命题

在 G42-P0 的精确 aligned implementation、同源 runner、冻结 seed/inventory 和 CPU-C++ backend 下，scale-matched direction-only attribution 证据路径是可执行的；现有实测时间足以支持冻结 formal inventory 在八小时内完成。

该结论消除了以下当前操作性解释：

G42 runner 无法加载和投影受信任 G40 anchors；

G41 no-slow route 无法进入 G42 paired branch；

按 group 的双 channel 梯度门或 baseline-output 门必然阻断执行；

DB/raw treatment 在 nonformal anchor 上必然共线或不可 scale-match；

评价和 bootstrap artifact 路径无法闭合；

formal inventory 预计超出八小时。

这里最后两项是由 operational_valid=true、exercise-complete branch 以及 aligned index 对 conclusion-bearing gate 的强制绑定共同支持的操作性推断；不是性能推断。

尚未得到的科学结论

本轮不能支持或否定：

SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42

也不能支持或否定：

DIRECTION_BALANCE_FINITE_BUDGET_ADVANTAGE_G42

非正式 package 仅含一个 anchor replicate、每臂 10 次 branch update、每 cell 6 个 episode 与 250 次 bootstrap。冻结设计要求正式结论使用三个独立 accepted-anchor replicate、每臂每 replicate 100 次 branch update、每 cell 48 个 episode 与 10,000 次 bootstrap。

因此：

G42_scientific_status=OPEN_UNTESTED
formal_G42_decision_required=true

不得引用或解释非正式 arm utility、差值、训练曲线、channel cosine、scale ratio 或其他 reduced-run 数值来提前选择 formal branch。

3. COUNTEREXAMPLES_AND_EXCLUSIONS
3.1 Nonformal 只关闭 replicate-0 类操作路径

预检能够证明其实际使用的一个 anchor 上存在有效 gradient channels 与非共线 treatment，但 formal 要求 accepted replicates 0|1|2 各自至少出现一次严格大于 1e-6 的 DB/raw unit-direction distance。其余两个 replicate 仍可能：

treatment 始终共线；

某个 actor group 在两个 channel 中同时死亡；

immediate 或 successor baseline output 梯度死亡；

出现正 DB norm、零 raw sum 的不可 scale-match 情形。

任何一种都会使 formal package 进入最高优先级 INVALID...，而不能被 replicate 0 的 preflight 所覆盖。

3.2 五个 formal 分支仍全部可能

预检未排除：

INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42
SOURCE_OR_REFERENCE_ACCESS_FAILURE_G42
SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42
DIRECTION_BALANCE_FINITE_BUDGET_ADVANTAGE_G42
MIXED_UNDERPOWERED_DIRECTION_BALANCE_ATTRIBUTION_G42

尤其是：

已登记 DB reference arm 仍可能在正式三个 replicate 上 confident access failure；

NO_DB 可能通过全部 access 与 noninferiority；

DB 可能具有 material advantage；

两臂都可用但区间跨过 0.05 决策边界，形成 mixed。

冻结 first-match 顺序与等号/严格比较不可由 preflight 结果改写。

3.3 G42 只归因 angular composition

G42 的 NO_DB null 不是普通 raw sum。它保留每次 PPO pass 中注册 DB 输出的全局标量 norm schedule，只将向量方向替换为：

∥g
I
	​

+g
S
	​

∥
2
	​

g
I
	​

+g
S
	​

	​

.

因此 G42 能回答的只是：

在全局 pre-Adam actor-gradient norm 被匹配时，registered angular reorientation 是否有有限预算价值？

它不能回答：

DB 的 scalar step-norm schedule 是否可删除；

完全未缩放的 g
I
	​

+g
S
	​

 是否足够；

post-Adam parameter-delta norm 是否应匹配；

其他梯度组合规则是否有效。

由于 Adam 是逐坐标更新，方向变化引起的 moment trajectory 差异是 treatment 的一部分，而不是可另行“校正”的残余 confound。

3.4 其余 G31 组件未被归因

两臂都保留：

realized-successor target
immediate/successor decomposition
shared true-current-state two-output baseline
per-channel normalization
common fast anchor
native-six no-carry actor

即使 formal 选择 DB advantage，也只能支持方向平衡在该完整 package 中具有局部贡献；不能声明 realized-tail、分解、baseline conditioning 或 normalization 单独必要。

即使 formal 选择 NO_DB sufficiency，也只删除 angular balancing，不能删除上述其他组件。G40 支持的是完整 credit package，G41 只删除了 post-anchor standalone slow critic。

3.5 Native-six 结论没有被重新检验

G42 读取受信任 G40 common anchors，并应用 G41 no-slow projection；它不重新比较 native-six 与 constant-overparameterized training，也不从随机初始化训练 common anchor。

所以 G42 preflight：

不增加 G39 native-six sufficiency 的证据；

不改变 function-matched initialization 的 claim ceiling；

不说明独立随机初始化的 native-six graph 是否等价；

不检验 common fast-anchor curriculum 是否可删除。

3.6 任何未来差值仍是有限预算、optimizer-conditional 结论

正式两臂使用冻结 Adam、100 次 branch update、8 个环境、2 次 PPO pass。一个 DB 优势只能表示：

在这一源、这一 anchor、这一 Adam 状态演化和这一预算下，direction-balanced angular composition 相对 scale-matched raw sum 有优势。

它不能推出 optimizer-independent 或 asymptotic necessity。

3.7 Source、process、capacity 与 horizon 边界

G42 保持：

H=48
training/evidence source=G32/G34-P0 family
configured capacities=6|8|12
one each of L/R/J/T
three registered event orders

它不支持：

H≠48；

capacity 6/8/12 之外的 configured capacity；

trajectory 中途改变 maximum capacity；

任意 event count/type/order；

无界或重复 leave/rejoin process；

任意 roster-process law。

这些方向仍应独立改变一个轴，不得由 G42 toy preflight 静默吸收。

3.8 UAV、recurrence 与冻结方向

G42 没有 UAV evidence。非 G33 UAV transport 仍必须等待：

constructive absolute feasibility
target behavior load-bearing separation
policy-support validity
physical and roster semantics

UAV G1/G2 仍为 SOURCE_NOT_IDENTIFIABLE；G33 及其 full-ledger/static-preposition lineage 继续永久冻结。异步 skill lifetime 和 environment-agnostic intrinsic reward 仍在当前 scope 外。

4. CDC_PORTFOLIO_LEDGER_EDITS
CONJECTURES.md
EDIT=NONE

G42 preflight 没有改变任何 supported、failed、source-invalid 或 out-of-scope 状态。C-CREDIT 继续保持 package-level support；direction balancing 仍是未归因组件。

RESEARCH_DIRECTION_LEDGER.md
STATUS_EDIT=NONE

保留：

G31 internal component attribution=OPEN_UNTESTED

不得将其改为 SUPPORTED_RETAINED、FAILED_CLOSED 或 PENDING_PRO_DISPOSITION。该账本明确规定，非正式筛选与机械分析分支不能自行改变科研状态。

可做的唯一机械文字更新是记录：

G42_same_source_preflight=
COMPLETE_OPERATIONALLY_VALID_FORMAL_EXECUTABLE_NO_SCIENTIFIC_CLOSURE
IDEA_PORTFOLIO.md
SCIENTIFIC_ROW_EDIT=NONE

仅将 scheduling metadata 前移为：

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_NONFORMAL_PREFLIGHT

preflight_disposition=
EXECUTABLE_SAME_SOURCE_G42_PREFLIGHT_NO_SCIENTIFIC_CLOSURE

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_EXECUTION

formal_source_commit=
6b8ea82d8fdbc76c14a414ff2b042a126f945dfb

formal_compute_status=
NOT_STARTED_SCHEDULED_ONLY
CURRENT_WORK.md

机械 pointer 可更新为：

last_completed_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_NONFORMAL_PREFLIGHT

active_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_EXECUTION

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_EXECUTION

g42_nonformal_scientific_disposition=
EXECUTABLE_SAME_SOURCE_G42_PREFLIGHT_NO_SCIENTIFIC_CLOSURE

g42_formal_source_commit=
6b8ea82d8fdbc76c14a414ff2b042a126f945dfb

g42_formal_compute_status=
NOT_STARTED

当前文件已经机械记录了 preflight 的完整有效性、inventory 和 formal projection，因此无需改变任何科学状态字段。

Balance 字段

当前问题提供 remaining=8，而 CURRENT_WORK/design raw 保存 remaining=6。归档本裁决时应机械统一这两个字段；本回复按问题提供的 8 返回 disposition。该不一致不构成 G42 科学 invalidity，也不改变 formal design。

5. PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
VALID_RESULT_DISPOSITION=CONTINUE
question_scoped_remaining_conclusion_bearing_iterations=8
Portfolio delta
G42_before_preflight:
    aligned_but_unexercised

G42_after_preflight:
    same_source_formal_executable

G42_scientific_status:
    unchanged_OPEN_UNTESTED

存在已经冻结、aligned、同源预检通过且预计远低于八小时上限的 conclusion-bearing candidate，因此：

CLOSE_NO_EXECUTABLE_CANDIDATE

不成立；balance 也未耗尽，因此：

COMPLETE_BALANCE_EXHAUSTED

不成立。External Pro 在 grant 继续时必须指定一个当前 resource-consuming action，同时保留其他 legal directions。

保留的 live / parked portfolio
方向	当前状态
G42 direction-balance attribution	Live；正式执行已调度
Realized-tail target attribution	Live，未调度
Immediate/successor decomposition	Live，未调度
Shared-baseline conditioning	Live，未调度
Per-channel normalization	Live，未调度
Common fast-anchor simplification	Live，未调度
Broader process / horizon / capacity	Live，未调度；一次只改一个轴
可识别的非 G33 UAV transport	Parked，等待 source-identifiability
Recurrence / EHC	Parked，等待当前 observation 缺失关键信息的 source
C-BASE / C-COORD	当前 reduction 外保持 live
G37 donor-coherence	Parked historical question
异步 skill lifetime / intrinsic reward	OUT_OF_SCOPE_FROZEN
G33 lineage	永久冻结

调度 formal G42 只是 attribution boundary，不代表其他方向被排序为无效或被退休。项目原则要求一次只调度一个消耗资源的动作，同时保留其他方向及其 reactivation conditions。

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_EXECUTION
为什么直接进入 formal G42

科学问题、实现和操作路径均已闭合到 formal 前最后边界：

exact estimand、null、gates、confidence unit 和 first-match order 已冻结；

correction-only alignment 为 ALIGNED；

exact same-source runner 已完成 bounded preflight；

treatment 在 nonformal anchor 上不是 vacuous；

gradient/group/baseline gates 可执行；

formal projection 约为 2,498.88s，只占八小时上限约 8.7%；

当前没有 source-identifiability、scientific ambiguity 或 evidence-complexity blocker。

此时切换到另一个 G31 component、扩大 process/horizon/capacity，或设计 UAV source，都会在一个已就绪的 attribution 问题获得正式证据之前放弃它。按照 information gain、成本与可逆性，formal G42 是最小下一动作。

该 scheduling disposition 本身不生成 runner token、不调用 runner，也不构成 compute authorization。

7. EXECUTABLE_SCIENTIFIC_BOUNDARY
formal_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_FORMAL_EXECUTION

formal_source_commit=
6b8ea82d8fdbc76c14a414ff2b042a126f945dfb

aligned_implementation_commit=
e21a1464e186260878649ad170bc3f32b8b9496d
7.1 科学对象
DB arm:
NATIVE6_G31_DB_NO_SLOW

NO_DB arm:
NATIVE6_G31_RAW_SUM_SCALE_MATCHED_NO_SLOW

两臂都从三个 immutable accepted G40 common fast anchors 出发，应用 aligned G41 no-slow projection，并保持：

native-six actor
log_std
shared true-state immediate/successor baseline
realized-successor target
immediate/successor decomposition
per-channel normalization
source and action streams
PPO and Adam exposure
final-only checkpoint selection

唯一 treatment 是两个既成 actor-gradient channel 的 angular composition。

7.2 Scale-matched null

对于每次 PPO pass：

r=g
I
	​

+g
S
	​

,
d
NO_DB
	​

=∥d
DB
	​

∥
2
	​

∥r∥
2
	​

r
	​

.

冻结语义：

DB norm = 0:
    NO_DB actor gradient = exact zero
    baseline update and Adam exposure continue

DB norm > 0 and raw sum = 0/nonfinite:
    INVALID before optimizer step

DB coordinates:
    never enter NO_DB vector

每个 formal replicate 必须至少有一次：

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

否则 treatment vacuous，不能进入 conclusion-bearing branch。

7.3 Primary estimand
Δ
DB
	​

=U
DB
	​

−U
NO_DB
	​

,

以 paired final random deterministic episodes 计算，并对 capacities 6|8|12 等权。

materiality_and_noninferiority_margin=0.05

Positive values favor direction balancing.

7.4 Absolute-access gates

每个 arm 必须独立满足：

fixed deterministic utility LCB per capacity >=0.90
fixed stochastic pooled LCB >=0.80
minimum fixed deterministic replicate mean >=0.85

random deterministic utility LCB per capacity >=0.90
event-window LCB per capacity >=0.85
process-segment LCB per capacity >=0.85
random-minus-fixed LCB per capacity >=-0.05
random stochastic pooled LCB >=0.80
minimum random deterministic replicate mean >=0.85

G42 无 zero/anchor evaluation cell，因此没有独立的 final-minus-zero learned-gain predicate；branch liveness、actor departure、baseline departure 和 treatment activation 是对应的 operational gates。

7.5 Comparison gates

NO_DB_NONINFERIOR：

UCB
95
	​

(Δ
DB
	​

)≤0.05

并且每一个 fixed/random、deterministic/stochastic、event-window、segment 和 transport component UCB 都不超过 0.05。

MATERIAL_DB_ADVANTAGE：

LCB
95
	​

(Δ
DB
	​

)>0.05

且：

LCB
95
	​

(Δ
DB,C
	​

)>0∀C∈{6,8,12}.
7.6 Frozen first-match branches
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G42

3. SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42

4. DIRECTION_BALANCE_FINITE_BUDGET_ADVANTAGE_G42

5. MIXED_UNDERPOWERED_DIRECTION_BALANCE_ATTRIBUTION_G42

Equality semantics：

absolute floor equality           = pass
random-minus-fixed LCB = -0.05    = pass
UCB(DB-NO_DB) = 0.05              = noninferior pass
LCB(DB-NO_DB) > 0.05              = strict advantage
direction distance = 1e-6         = active

不得使用 preflight metric、training curve、cosine、channel norm 或 event stratum 改写 first-match 结果。

7.7 Confidence unit
accepted_anchor_replicates=3
episodes_per_cell=48
bootstrap_resamples=10000
bootstrap_seed=10427042
confidence_interval=95_percentile
episode_exclusions=none

一个 paired hierarchical plan 重采样：

三个 accepted-anchor replicate blocks；

每个 replicate/capacity 下的完整 episode IDs；

同时保留 arm、fixed/random 与 deterministic/stochastic mates；

capacities 6|8|12 等权。

不得独立重采样 member、time step、event、gradient channel 或 action factor。

7.8 Formal inventory
accepted_anchor_replicates=3
branch_updates_per_arm_per_replicate=100
environments_per_update=8
PPO_passes=2

evaluation_cells=72
episodes_per_cell=48
bootstrap_resamples=10000

training_transitions=230400
evaluation_transitions=165888
total_real_transitions=396288
optimizer_steps=1200

三个 event orders 在每个 replicate/capacity 下为精确 16/16/16；capacity 8 的三个 profile 同样为 16/16/16。

7.9 Complexity and compute ceiling
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

formal_wall_clock<=28800_seconds
measured_projection=2498.876156999777_seconds

该 evidence design 明显低于用户 hard boundary。若运行前重新验证发现投影超界，应返回 NON_EXECUTABLE_EVIDENCE_DESIGN，其 scientific iteration cost 为零；不能把超时当作 DB 或 NO_DB 结果。

Formal admission 仍必须由 runner 侧绑定：

exact same-source preflight artifacts
ALIGNED implementation/source identity
registered formal token
CPU-only required C++ backend

本回复不复制、创造或授权该 token。

8. 中文简报
本轮机械分支=
G42_NONFORMAL_DIRECTION_BALANCE_ATTRIBUTION_EXERCISE_COMPLETE

科学裁决=
EXECUTABLE_SAME_SOURCE_G42_PREFLIGHT_NO_SCIENTIFIC_CLOSURE

有效结果 disposition=
CONTINUE

当前调度动作=
G42 FORMAL EXECUTION
本轮证明了什么

同源 G42 runner 已经完整跑通：

train
evaluate
analyze

结果为：

operational_valid=true
14,592 real transitions
40 optimizer steps
24 cells
6 episodes/cell
250 bootstrap draws
67.67 seconds

正式投影为：

2,498.88 seconds

远低于八小时上限。

这证明 formal G42 的证据路径可执行，不证明 DB 或 scale-matched raw sum 谁更好。

本轮没有证明什么

不能提前写成：

direction balancing removable

也不能提前写成：

direction balancing load-bearing

正式三个 anchor replicate 仍可能产生：

invalid gradient/treatment gate；

DB reference access failure；

NO_DB sufficiency；

DB material advantage；

mixed/underpowered。

CDC 状态
CONJECTURES.md scientific status       不变
RESEARCH_DIRECTION_LEDGER status       不变
IDEA_PORTFOLIO scientific rows         不变
G31 direction-balance attribution      OPEN_UNTESTED

只将调度指针前移到正式 G42。

当前研究位置
阶段	状态
G40	完整 G31 package 优于 TEAM_GAE1
G41	post-anchor standalone slow critic 可精确删除
G42 design	已冻结 scale-matched direction-only comparator
G42 code-science	修复后 ALIGNED
G42 nonformal	同源完成、operationally valid、formal 可执行
当前位置	正式 G42 execution
问题给出的剩余结论性轮次	8

正式 G42 保持：

Delta_DB = U_DB - U_NO_DB
margin = 0.05
H = 48
K_search = 0
hypothetical transitions = 0
396,288 formal real transitions
1,200 optimizer steps
72 cells
48 episodes/cell
10,000 bootstrap draws
formal cap = 28,800 seconds

其余 G31 components、common fast anchor、broader process/horizon/capacity、可识别非 G33 UAV、recurrence/EHC 等方向继续保持 live 或 parked。G33 永久冻结。本裁决不自行执行或授权 implementation、Git 或 compute。