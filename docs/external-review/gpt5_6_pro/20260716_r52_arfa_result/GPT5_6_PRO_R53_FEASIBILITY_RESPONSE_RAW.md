CORRECT_R53_RCMA_G0_ACTION_CONTRACT

R53 不需要退休。最小且充分的修正是：

增加一个显式、匿名、可被多人选择的 IDLE/ABSTAIN 实体，容量为 N
	​


所有 productive queues 继续保持单位容量：

c
q
	​

=1,

只有 idle 的容量为：

c
∅
	​

=N.

这使 autoregressive support 成为：

productive queues 上的 injective matching+共享 slack/idle sink
	​


而不是强迫所有 agent 在每个 primitive step 都服务某个 productive queue。

当前提交确认尚未启动任何 R53 smoke 或训练，临时实现也已删除，因此不存在可审阅的 R53 结果 JSON；本轮审阅对象是 action contract 与已验证的 R52 pointer substrate，而不是结果重判。

一、可复用因果结论

当前矛盾是有效的：

capacity-feasible support

=task-neutral support.
	​


如果动作集合只包含 productive queues，那么单位容量 mask 不只是排除重复动作，还隐式规定：

所有 agent 每步必须被派往某个 productive resource.

这会把最低任务服务量硬编码进环境可行域，使策略无法表达“暂不分配资源”。入口文件给出的下界：

F
B
	​

≥
B
B−1
	​


以及在 P≥2 时：

F
P
	​

≥
P
P−1
	​


均成立，因此此前两个单类负控不可执行。

加入 idle 后，RCMA 的科学对象仍然不变：

已知 productive-resource capacity→动态 AR support→无重复 productive assignment 的 joint mode.
	​


Idle 只是让“未使用的 agent capacity”可表示；它不告诉策略应该服务哪一类 queue，不读取 reward，也不构成 shaping。

二、修正后的统一 launch-exact 合同
项目	唯一定义
Productive queue 数量	P
N
	​

=⌊N/2⌋，B
N
	​

=N+1−P
N
	​

，productive queue 数记为 Q
N
	​

=P
N
	​

+B
N
	​

=N+1。
Pointer action cardinality	新增一个 idle action entity：
K
N
	​

=Q
N
	​

+1=N+2。此前的 K
N
	​

=N+1 必须收窄解释为 productive queue 数，而不再是完整 pointer support 大小。
Action set	A
N
	​

={q
1
	​

,…,q
Q
N
	​

	​

,∅}，其中 ∅ 为匿名 idle/abstain。每个 active agent 每步仍必须输出一个 pointer。
Raw capacities	每个 productive queue：c
q
(0)
	​

=1。Idle：c
∅
(0)
	​

=N。选择任一 action 后，相应 raw capacity 减一；capacity 为零时才被 mask。
RCMA key field	Key 中的 residual-capacity 标量使用归一化值。Productive queue 为 c
q
	​

/1∈{0,1}；idle 为 c
∅
	​

/N∈[0,1]。Feasibility 判定使用 raw capacity，而不是归一化数值。
允许重复的范围	Productive queue 每步最多被一个 agent 选择和服务。Idle 最多可被 N 个 agents 选择；这种重复不属于 productive duplicate assignment。
Idle 是否是 entity	是。Idle 作为一个显式 action entity参与 presentation permutation、pointer scoring、teacher-forced replay和 previous-action relation。它不是 productive queue，不产生 arrival、backlog、service、completion、expiration或 reward contribution。
七维 entity view 的最小语义修正	原 queue[0]=active 改为 queue[0]=is_productive_queue。Productive queues 为1，idle为0。所有 action entities在结构上始终 action-active，所以 action activity由独立support处理，不能再由该字段表示。其余六维保持原顺序。
Idle 的七维 view	[is_productive=0, backlog/8=0, new_arrival=0, deadline/3=0, served/arrived=0, expired_fraction=0, selected_previous_step_count/N]。
Productive queue view	[is_productive=1, backlog/8, new_arrival, deadline/3, cumulative_served/cumulative_arrived, expired_fraction, selected_previous_step_count/N]，所有原zero-denominator convention保持不变。
Static mask	全部 N+2 action entities在全部16个steps都静态有效。不得因queue为空、无arrival、无live burst、deadline、queue class或reward而mask。
唯一动态 mask	仅有 raw_residual_capacity > 0。这是唯一新增的feasibility mask。
Entity pooling	Idle进入同一个共享entity encoder和mean pool。Pool大小由 N+1 改为 N+2。
Cardinality injection	Entity-pool的cardinality项改为 log(1+
K
N
	​

)=log(N+3)。Member-pool仍加入 log(1+N)。
模型参数量	仍为 24,737。Idle复用现有7维entity encoder和34维queue key，不增加embedding、head或输入维度。R52基底本身使用共享entity encoder、mean pool和共享pointer key，因此增加一个set element不会改变state-dict shape。
Queue key	仍为 [entity_embedding(32), normalized_residual_capacity(1), is_previous_action_for_focal(1)] → 32。无额外idle head。
Previous action reset	Episode reset时 previous_action=-1、has_previous_queue=0、served_previous_step=0；首步所有relation为0。
选择idle后的状态	previous_action←idle，下一步idle entity的focal relation为1；served_previous_step=0。选择idle与选择空productive queue一样，都会覆盖前一步action history。
Idle selected count	selected_previous_step_count/N 对idle可以取 {0,1/N,…,1}；对productive queues因RCMA最多为 1/N。
Presentation order	每个episode对全部 N+2 entities生成一个anonymous permutation，其中包括idle。Idle没有固定presented slot；其canonical environment-local key只写入ledger，不进入网络。
Agent order	每primitive step继续使用外生agent permutation，不学习order。
Replay ledger	entity_keys/order/static_mask/dynamic_capacity/prefix/previous-relation 的最后一维由 N+1 改为 N+2。sampling_uniforms、agent-token数和old token log-prob shape不变。
Sampling/replay support	Sampling、teacher-forced replay和deterministic decoding都从同一raw-capacity vector开始，并按存储action逐token更新。
Deterministic tie-break	在当前capacity-feasible support中执行标准sequential argmax；精确tie选择presented order中的第一个位置。Idle没有特殊优先级或特殊惩罚。
Reward与transition	Persistent/burst arrivals、service-before-deadline-decrement、service windows、F
P
	​

,F
B
	​

,U=
F
P
	​

F
B
	​

	​

全部保持不变。Idle不改变环境状态，除previous-action bookkeeping外无副作用。
计算与曝光	每step仍有 N 个token；只把pointer candidates从 N+1 增加至 N+2。128K transitions、512K tokens、500/100 optimizer steps、PPO epoch 1完全不变。
统计合同	Zero/final、stochastic/deterministic、shared/specialist继续使用同一128-episode paired ledgers；bootstrap unit和10,000次bootstrap保持不变。

这一修改是对 proven R52 pointer substrate 的最小扩展：原实现已经将entity作为共享编码的set elements，依外生presentation order打分，并逐token更新prefix，因此增加一个无新参数的action entity不会改变模型形状。

三、三个 M0 调度现在对所有 N 都可执行

通用规则如下。

Constructive

在每个persistent-arrival step：

P
N
	​

 agents→P
N
	​

 distinct persistent queues,

其余：

N−P
N
	​

=B
N
	​

−1

个agents选择idle。

在burst arrival steps t=3,9：

B
N
	​

 agents→B
N
	​

 distinct burst queues,

其余：

N−B
N
	​

=P
N
	​

−1

个agents选择idle。

其他steps全部选择idle。

结果严格为：

(F
P
	​

,F
B
	​

,U)=(1,1,1).
Persistent-only

每个persistent-arrival step服务全部 P
N
	​

 persistent queues，其余agents选择idle。包括burst jobs仍live的 t=4,10，任何剩余agent都选择idle而不再被迫服务burst。所有其他steps全部idle。

结果严格为：

(F
P
	​

,F
B
	​

,U)=(1,0,0).
Burst-only

在 t=3,9 服务全部 B
N
	​

 burst queues，其余agents选择idle。所有persistent-arrival steps及其他steps全部idle。

每个persistent queue最终保留8个work units，因此：

(F
P
	​

,F
B
	​

,U)=(0,1,0).

逐 N 的精确assignment counts为：

N  P  B  productive Q  action entities N+2
2  1  2       3               4
   persistent event: 1 persistent + 1 idle
   burst event:      2 burst      + 0 idle

3  1  3       4               5
   persistent event: 1 persistent + 2 idle
   burst event:      3 burst      + 0 idle

4  2  3       5               6
   persistent event: 2 persistent + 2 idle
   burst event:      3 burst      + 1 idle

5  2  4       6               7
   persistent event: 2 persistent + 3 idle
   burst event:      4 burst      + 1 idle

6  3  4       7               8
   persistent event: 3 persistent + 3 idle
   burst event:      4 burst      + 2 idle

因此三个调度在每个注册team size上分别精确产生：

Schedule	F
P
	​

	F
B
	​

	U
Constructive	1	1	1
Persistent-only	1	0	0
Burst-only	0	1	0

没有删除负控，没有允许重复productive service，也没有增加reward-dependent mask。此前矛盾正是由于没有slack action而产生；idle恢复了“完全不服务某一类”的可表达性。

四、修正后的 launch-exact M0

M0 必须全部满足：

对每个 N：

P
N
	​

=⌊N/2⌋,B
N
	​

=N+1−P
N
	​

,Q
N
	​

=N+1,
K
N
	​

=N+2.

每episode恰有一个idle entity；它进入presentation、pool、sampling和replay，但不进入productive reward统计。

七维entity view的第一维严格为is_productive_queue；productive为1，idle为0。

Productive raw capacity严格为1；idle raw capacity严格为 N。

Productive entity每step选择数不超过1；idle选择数允许为0至 N。

全部entities静态action-active；唯一动态mask为raw residual capacity是否大于0。

Backlog、arrival、deadline、class和reward均不得产生额外action mask。

Reset首步所有previous-action relations为0；之后每个agent严格one-hot，包括previous action为idle的情况。

选择idle或空productive queue都更新previous action，但served_previous_step=0。

Sampling、replay和deterministic decode使用完全相同的heterogeneous-capacity support。

Constructive、persistent-only和burst-only schedules对所有 N 分别得到：

(1,1,1),(1,0,0),(0,1,0).

Persistent/burst arrival counts、deadline、service-before-decrement和burst service windows仍与原合同完全一致。

所有中间reward为0；终局reward逐episode严格等于：

U=
F
P
	​

F
B
	​

	​

.

Actor无agent ID、slot、productive queue class、oracle priority、skill、KEEP/SET、shaping或intrinsic输入。is_productive_queue只区分idle与真实resource，不区分persistent与burst。

Exact model parameter count仍为24,737；所有 N 的state-dict keys/shapes完全一致。

Shared和specialists从逐位相同参数开始，并使用相同arrival、entity-presentation、agent-order和sampling-uniform ledgers。

精确达到：

128,000 transitions/arm
25,600 transitions/N/arm
512,000 agent-token decisions/arm
500 shared optimizer steps
100 optimizer steps/specialist
500 aggregate specialist steps
PPO epochs = 1
collected-batch reuse = 0

Sample/replay log-probability、heterogeneous-capacity mask、prefix、previous relation和hidden replay误差均：

≤10
−6
.

Exhausted productive capacity上的probability mass为0；idle只在第 N 次idle选择后耗尽。

所有相关模块获得有限非零gradient exposure并产生参数漂移；全部参数有限。

Exact-final checkpoint reload误差为0。

Zero/final、stochastic/deterministic、shared/specialist evaluations均使用相同128 paired episodes/N。

M0失败：

INVALID_R53_RCMA_WIRING

唯一动作是只修复明确定位的action-entity、idle capacity、transition、mask、ledger、replay、count、statistics或checkpoint缺陷，并按本合同原样重跑。

五、M1：fixed-N specialist gate

M1 数学阈值全部保持不变。

每个 N 必须满足：

P
train
	​

(U>0)≥0.50,
U
ˉ
N
spec,stoch
	​

≥0.70,
U
ˉ
N
spec,det
	​

≥0.65,
F
ˉ
P,N
spec,det
	​

≥0.70,
F
ˉ
B,N
spec,det
	​

≥0.70,
UCB
95
	​

[U
N
spec,stoch
	​

−U
N
spec,det
	​

]<0.15,
LCB
95
	​

[U
N,final
spec,det
	​

−U
N,zero
spec,det
	​

]>0.15.

四个连续32-episode deterministic blocks中，至少三个满足：

U
ˉ
N,block
spec,det
	​

≥0.60.

Equal-N deterministic macro：

U
ˉ
spec,det
≥0.70.

M0通过但M1失败：

NO_ACCESS_R53_RCMA_SPECIALISTS

唯一动作是永久退休精确的：

AMQA dynamics
terminal sqrt(F_P * F_B) utility
corrected idle-entity action contract
seven-dimensional entity view
previous-action relation
heterogeneous residual-capacity support
stochastic-to-deterministic transport gate

Shared结果全部隔离。

六、M2：shared variable-N gate

每个 N 必须满足：

U
ˉ
N
shared,stoch
	​

≥0.70,
U
ˉ
N
shared,det
	​

≥0.65,
F
ˉ
P,N
shared,det
	​

≥0.70,
F
ˉ
B,N
shared,det
	​

≥0.70,
UCB
95
	​

[U
N
shared,stoch
	​

−U
N
shared,det
	​

]<0.15.

并要求：

U
ˉ
shared,det
≥0.70,
N
min
	​

U
ˉ
N
spec,det
	​

+10
−8
U
ˉ
N
shared,det
	​

	​

≥0.85,
U
ˉ
spec,det
+10
−8
U
ˉ
shared,det
	​

≥0.90,
LCB
95
	​

[
5
1
	​

N
∑
	​

(U
N
shared,det
	​

−U
N
spec,det
	​

)]>−0.08,
LCB
95
	​

[
U
ˉ
final
shared,det
	​

−
U
ˉ
zero
shared,det
	​

]>0.20.

M0、M1通过但M2失败：

VALID_FAIL_R53_SHARED_VARIABLE_N

唯一动作是永久退休精确shared RCMA contract，并停止当前variable-N learning line，进行一次只读架构失败审查。

全部通过：

PASS_R53_RCMA_VARIABLE_N

唯一下一动作仍然只是：

在同一AMQA、同一corrected RCMA action contract和同一terminal utility下，注册一次within-episode exogenous join/leave与membership-censoring gate。

不授权skills、KEEP/SET、variable lifetime、intrinsic reward、learned admission、S7/UAV、mean field或field slots。

七、永久 no-rescue 边界

以下全部禁止：

删除或弱化三个M0调度；

将idle改成productive queue；

允许一个productive queue每步接受多个agents；

把idle capacity从 N 改为可调参数；

根据backlog、arrival、deadline、queue class或reward增加mask；

改变terminal utility；

改变128K transitions、500/100 optimizer exposure、PPO epoch、seeds、模型宽度或24,737参数规模；

改变M1/M2阈值、bootstrap cluster、macro weighting或tie-break；

temperature、beam search、joint MAP、best checkpoint或post-hoc action repair；

增加seed、预算、epoch或batch reuse；

agent ID、slot-specific head、learned agent order或learned admission；

intrinsic reward或中间shaping；

并行加入mean field、field slots、skills、KEEP/SET、variable k 或variable lifetime；

通过修改idle观察、容量、统计或negative-control定义挽救有效M1/M2失败。

有效失败只能进入已注册的永久退休分支。仓库的因果纪律明确要求保留负结果，并禁止在结果后修改预算、阈值、指标或机制定义以获得有利结论。

	​

R53 唯一路线保持不变；
加入一个容量 N 的匿名idle entity；
productive queues继续保持单位容量RCMA；
三个M0调度现对所有 N 可执行；
参数量、训练曝光、reward、M1/M2和统计阈值不变。
	​

	​
