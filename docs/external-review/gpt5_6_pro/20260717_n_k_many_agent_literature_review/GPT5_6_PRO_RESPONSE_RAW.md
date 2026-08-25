明确裁决
ACCEPT_WITH_MODIFICATION: ARES-SMDP
	​


即接受文献综述的基本方向，但不原样接受“四层结构里同时放入稀疏 GNN、population slots、关键成员 residual、动态成员与异步时间”的默认组合。唯一选择的后续架构是：

ARES-SMDP： Active-Roster Event-Set Semi-Markov Policy
	​


其唯一研究路线为：

	​

先验证 variable-N 表示压缩是否保留决策充分信息
→再验证该表示能否承载普通任务学习
→再加入 episode 内外生 join/leave/rejoin
→再在固定 roster 下加入外生异质 T
i
	​

 与真实 SMDP credit
→最后才联合 N
t
	​

+T
i
	​

.
	​

	​


当前不激活 learned timing、skill intrinsic、动态 membership 学习、mean field、field-slot team action 或 UAV 规模训练。

一、证据与结果 JSON 边界

指定提交中的 R53 仍处于正式运行阶段；仓库 dashboard 只登记了实现与 focused M0 已通过，明确要求 terminal branch 之后单独审阅，不能使用中间指标决定本轮文献路线。

我已检查 R53 的完整实现与结果合同：

r53_rcma.py 已实现 N+2 action entities、productive queue 单位容量、idle 容量 N、动态 support、prefix、previous-action relation 和 recurrent pointer policy；

runner 规定 terminal JSON 写入 <run-root>/result/r53_rcma.json；

JSON 会包含 M0/M1/M2、zero/final stochastic/deterministic evaluation、概率 replay、optimizer exposure 和互斥 status；

terminal status 只可能按注册顺序进入 INVALID_R53_RCMA_WIRING、NO_ACCESS_R53_RCMA_SPECIALISTS、VALID_FAIL_R53_SHARED_VARIABLE_N 或 PASS_R53_RCMA_VARIABLE_N。

但该提交中没有 terminal R53 result JSON 可供科学解释。因此本裁决没有使用任何 R53 中间训练值，也不假定它会 PASS 或 FAIL。

二、八篇论文与代码解读审计
总体结论
没有发现会推翻总体综合方向的事实性错误。
	​


但有四项必须收窄，否则实现阶段容易把论文启发误写成已经验证的能力：

ACE 的 robot-loss 实验不是完整 dynamic-roster 实现。
它仍以固定最大 agent tensor、固定 num_agents 模块和 mask 表达失效；可以借鉴 readiness/loss stress，不可宣称其已解决 join/rejoin、member epoch 或 survivor history。其异步 return 也没有明确保存 action duration。

InforMARL 没有提供 episode 内动态 roster 的 full-set actor。
它证明的是图节点、batch 与 pooling 可支持大小可变的表示运算；runner 仍从固定配置构造 agent/node 数。“full active-set reference”是本项目应建立的实验参考，不是该论文已交付的 controller。

Sable 并没有提出 fixed-M population-slot coordinator。
它的 retention/chunkwise 结构是 many-agent 容量启发，但实现仍把时间和固定 agent 轴组合为固定序列。将 retention 运行在 population slots 上是本项目的新设计，不能归因于 Sable。

CT-MARL 的 reward × dt 不能直接搬入当前离散环境。
当前项目应吸收的是 γ
Δt
 和 elapsed-time conditioning，而不是把已有 primitive-step reward 再乘一次 duration。当前 event return 必须仍然是 primitive rewards 的折扣和。

这些修正不会改变总体路线，但会改变哪些代码可以直接吸收、哪些只能作为诊断。

三、机制吸收矩阵

这里的 ABSORB NOW 指“立即写入统一架构与数据合同”，不代表本轮立即实现或训练。

文献	裁决	精确吸收对象	明确不吸收
ACE	ABSORB NOW	每个成员独立 readiness；active-only event collection；robot-loss/straggler stress；成员事件不应迫使 survivors 同步动作	固定 num_agents buffer、固定 identity mix、当前 return 计算、mask 覆写路径
ACAC	ABSORB NOW	agent-owned event history；显式 duration；事件级 R
i
	​

,γ
T
i
	​

 bootstrap 与 duration-aware GAE；joint event critic 的语义	固定 roster runner、直接复制 attention critic、其特定 macro-action 环境
InforMARL	ABSORB NOW	permutation-safe active-set encoder；图/set batching；active-set pooling；首个 gate 的 full-set reference	将其 runner 当成 dynamic membership 实现；将全局 critic pooling当作动态 roster 证明
Sable	DIAGNOSTIC ONLY	many-agent retention 的容量、吞吐量和 chunking 参考	固定 T×N sequence、固定 agent mask、直接充当 dynamic-slot coordinator
ExpoComm	CONDITIONAL	若 full-set reference 成功但大 N 成本不合格，才吸收 bounded candidate graph / one-peer sparse communication 思路	cyclic agent ID、固定同步 t、静态邻接、把通信拓扑当 intrinsic reward
Safe-M3-UCRL	DO NOT ABSORB	无	无限/交换性 mean field、model-based optimistic safety stack、纯平均场对稀有关键成员的替代
CT-MARL	DIAGNOSTIC ONLY	用于交叉验证 γ
Δt
、elapsed-time input 与连续时间极限	reward × dt 直接移植、全队共享 Δt、固定 N 联合 dynamics/value
IARO	DIAGNOSTIC ONLY	relative/spreadness 等不依赖绝对身份的表征诊断	全队同步 option、全局 option clock、将同步 option discovery 当成 per-agent T
i
	​


ACE 的代码确实提供了 per-agent readiness 和异步 buffer，但仍固定形状；ACAC 则显式抽取 agent 事件、duration 和宏事件 GAE，是当前最接近正确时间信用的参考。

InforMARL 是首个 active-set reference 的主要启发；Sable 只提供容量参照。

ExpoComm 的固定 circular ID 与同步时间需要全部替换；Safe-M3-UCRL 的纯 mean-field 假设与有限 UAV 团队中的割点、唯一 relay 和稀有能力成员不兼容。

CT-MARL 和 IARO 都不能提供 per-agent dynamic-roster SMDP，但适合做时间折扣与相对表示的诊断参照。

四、对四层分解的裁决

原四层分解在概念上基本合理，但存在两个因果耦合问题：

membership shell 与 event-time runtime 不能真正独立，因为 join、leave、rejoin 决定了：

哪个 policy action 存在；

哪条 history 拥有 reward；

是否 bootstrap；

哪个 old log-probability可以进入 PPO。

“sparse GNN + field slots + exact residual”不能在首个 gate 中同时作为既定答案。
这会把三个 representation interventions 混为一体，使失败无法归因。

因此我将其修改为一个三层架构，而不是四条同时激活的机制。

五、唯一替代架构：ARES-SMDP
1. Member-event control plane

每个活动实例以：

(member_key, membership_epoch)

标识。

member_key 和 membership_epoch 只进入 collector、buffer 与 checkpoint，不进入神经网络。

规则：

joiner：新建 epoch、隐藏状态归零、没有 incumbent，因此首次高层动作只能 SET(z)；

leaver：不产生额外 policy token；当前 event row 以 membership_censored 关闭；

survivor：不因其他成员 join/leave 而重置 skill、age、low hidden 或 event history；

rejoiner：即使物理 key 相同，也获得新的 membership epoch，不能复用旧 policy history。

ACE 的 readiness shell只吸收到这一 control plane；它不拥有 policy credit。ACAC 的 agent-owned history则在该 ledger 中实现。

2. Deterministic active-set representation

活动成员集合：

A
t
	​

={i:member i active at t}.

原始表示参考为：

H
t
set
	​

=SetEnc({x
i,t
	​

:i∈A
t
	​

}).

只有在下一节的 R54 gate 通过后，才允许替换为：

H
t
hyb
	​

=[{(F
m,t
	​

,ν
m,t
	​

)}
m=1
M
	​

,C
t
L
	​

,log(1+∣A
t
	​

∣)],

其中：

α
im
	​

=softmax
m
	​

g
θ
	​

(x
i
	​

),
F
m
	​

=
ϵ+∑
i
	​

α
im
	​

∑
i
	​

α
im
	​

ϕ
θ
	​

(x
i
	​

)
	​

,ν
m
	​

=
∣A
t
	​

∣
1
	​

i
∑
	​

α
im
	​

.

C
t
L
	​

 是固定上限 L 的 exact residual members。

这些 slots、mass、top-L indices 都是确定性表示。

它们：

没有 action log-probability；

不进入 PPO ratio；

不被称为 MAT tokens；

由 stored raw member set 在 replay 时重新计算；

可以通过 policy/value loss获得普通反向梯度，但不是 sampled actions。

候选文档自己已经识别了“stochastic slot assignment 会破坏 clean PPO ownership”的风险，因此这里明确选择 deterministic slots。

3. Event-owned high policy

在 primitive time t，只有真正到达高层决策边界的成员形成 ready set：

R
t
	​

⊆A
t
	​

.

联合高层策略为：

π
H
	​

(e
t
	​

∣X
t
	​

)=
j=1
∏
∣R
t
	​

∣
	​

π
H
	​

(e
σ
t
	​

(j)
	​

∣x
σ
t
	​

(j),t
	​

,H
t
	​

,
z
~
t
(j−1)
	​

)
	​


其中：

e
i
	​

∈{KEEP}∪{SET(z):z

=z
i
−
	​

}.

只有 R
t
	​

 中的 sampled actions 进入 autoregressive sequence。未 ready 的 surviving agents：

不产生 token；

保持 incumbent；

仍作为 deterministic team context的一部分。

当前 R30 正是把真实 sampled KEEP/SET、外生顺序、applied working roster 和 old token log-probability存储后 teacher-force；但它目前按固定 n_agents 构造 identity-specific prefix，并在每个 check 对全部 agents运行序列。

ARES-SMDP 保留其概率语义，删除固定 N 的 identity slots，并把序列长度从：

N
t
	​


改为：

∣R
t
	​

∣.

低层执行器继续保持：

a
i,s
	​

∼π
l
	​

(a
i
	​

∣o
i,s
	​

,z
i,s
	​

)
	​


不让 population field、slots、compact team context或 task identity绕过 skill bottleneck。当前 principles 与 strict low actor都将这一点作为不变量。

六、精确时间与 credit 合同

首轮时间实验只允许外生异质 event intervals；不学习何时终止。

对 member i 的第 m 个真实高层动作：

s
i,m
	​

=event start,
u
i,m
	​

=next real decision、leave 或 episode terminal,
T
i,m
	​

=u
i,m
	​

−s
i,m
	​

.

外部回报：

R
i,m
	​

=
r=0
∑
T
i,m
	​

−1
	​

γ
r
r
s
i,m
	​

+r
env
	​

.

TD error：

δ
i,m
	​

=R
i,m
	​

+γ
T
i,m
	​

(1−d
i,m
	​

)V
i
	​

(h
i,m+1
	​

)−V
i
	​

(h
i,m
	​

).

Event GAE：

A
i,m
	​

=δ
i,m
	​

+γ
T
i,m
	​

λ(1−d
i,m
	​

)A
i,m+1
	​

.

这里 λ 是 event-trace 参数，不写成固定 primitive-step GAE，也不从 ACE 当前 return实现中继承。ACAC 的 event extraction和 γ
duration
 bootstrap提供直接参考；CT-MARL只用来交叉检查 γ
Δt
。

Update boundary

若 PPO update 在某个 active event结束前发生：

使用旧 critic 在 boundary state bootstrap；

关闭 actor-valid row；

标记 policy_truncated=True；

GAE trace断开；

simulator、incumbent skill、age和low hidden继续；

旧 action的 log-probability不得进入下一 policy version。

当前 R30 已实现类似的 high-row截断与 continuation语义。

七、MAT tension 的最终解决
继续 autoregressive 的对象

只有以下 sampled policy actions继续 AR：

同一 primitive time 上多个 ready members 的 KEEP/SET(z)；

未来若另行批准的 sampled team coordination latent。

改为确定性表示的对象

以下不是动作：

active-set GNN；

population slots；

slot masses；

log(1+N)；

exact residual member selection；

member/event masks；

sparse graph candidate construction。

它们没有 policy log-probability。

PPO 必须存储并 teacher-force 的内容

每条 event sequence必须存储：

member_key
membership_epoch
event_start_time
ready_member_set
active_member_set
raw member tokens
pre-action roster and ages
external AR order
sampled KEEP/SET kinds
sampled SET skills
applied working prefixes
old per-token log-probabilities
old event values
event duration T_i
primitive reward sequence or exact discounted event return
old next-event value
terminal / membership_censored / policy_truncated

Replay 时：

deterministic set/slot representation从 stored raw tokens重新计算；

stochastic actions、外生order和applied prefix严格 teacher-force；

只有 sampled actions形成 PPO ratios。

当前 R30 的 HighCheckRow已经存储pre-roster、顺序、token kind、SET skill、old token logp和value，但数组shape仍固定为 n_agents。

八、唯一有序研究路线
R53→R54→R55→R56→R57→R58
	​

阶段	唯一问题	明确禁止
R53 terminal review	conventional anonymous variable-N baseline 最终状态	使用中间指标
R54 representation gate	fixed-M slots + bounded exact residual 是否保留 full-set 决策信息	PPO、membership、timing、skills
R55 learning transport	R54 PASS 的表示能否在 stable cross-episode N 上承载 ordinary task learning	episode 内 join/leave、variable T
i
	​


R56 membership gate	外生 join/leave/rejoin、survivor continuity与概率 replay	learned timing
R57 time gate	固定 roster 下的外生 heterogeneous T
i
	​

 和 duration-correct SMDP	membership change、learned termination
R58 joint exogenous gate	外生 N
t
	​

+T
i
	​

 是否可同时运行	intrinsic、learned admission/timing
R58 PASS 后的新审阅	是否重新授权 learned timing 与新的 HMASD semantic mechanism	自动恢复任何 R29–R52 路线

候选文档提出的总体顺序是正确的，但 representation gate必须先把 full-set reference 和 compressed candidate分开；dynamic membership与variable time也必须保持串行。

九、R53 terminal branch table
R53 terminal branch	唯一下一动作
CRASH 或无 terminal JSON	只修复运行基础设施并完成同一 R53，不启动 R54
INVALID_R53_RCMA_WIRING	只修注册的具体 wiring defect，按原合同重跑 R53
NO_ACCESS_R53_RCMA_SPECIALISTS	接受并退休精确 R53 task contract；随后执行独立的 R54 representation gate，不使用 R53 reward或checkpoint
VALID_FAIL_R53_SHARED_VARIABLE_N	冻结 R53 specialists为表示/任务参考，执行 R54
PASS_R53_RCMA_VARIABLE_N	冻结 R53 为 conventional set-pointer baseline，执行 R54 作为更大 N 的压缩充分性门

所以 R54 只被 INVALID/CRASH 阻塞；任何有效 terminal branch都不会被拿来修改 R54 的模型、数据或阈值。

十、唯一最小 post-R53 abandonment gate
R54-HFSR-G0

Hybrid Field-Slot Representation Sufficiency

唯一因果边：

完整 active set 信息→固定 M slots + L exact residuals→保留多峰、稀有关键成员与 anti-coordination 决策信息
	​


这是 Level-0 supervised representation gate，不是环境性能实验，也不是 R50 的 reward-bandit 重跑。

1. Toy：Multimodal Capacitated Assignment

每个 one-step toy episode包含 N 个匿名 members和 N 个capacity-one tasks。

Member feature：12维
2-D position
2-D velocity
4 binary capabilities
energy
current load
availability
continuous observable tie-break value
Task feature：10维
2-D position
4 required capabilities
demand
deadline
priority
continuous observable tie-break value

每个case包含：

两个对称但多峰的member clusters；

一个critical task；

恰好一个member具有该critical task所需的稀有能力；

其余capability和位置保证存在perfect matching；

cost由位置、能量、load和capability feasibility决定；

oracle使用 deterministic Hungarian matching；

连续可观察字段保证唯一解；

stable member/task keys只进入ledger，不进入模型。

另外构造mean-alias twins：两个case具有相同raw coordinate-wise population mean，但稀有能力位于不同空间member上，oracle必须改变critical assignment。

2. 两个精确 arms
full_active_set_reference

每个focal member通过共享cross-attention读取全部 active member embeddings。

hybrid_m8_l2

固定：

M=8,L=2.

Slot：

α
im
	​

=softmax
m
	​

g
θ
	​

(ϕ
i
	​

),
F
m
	​

=
ϵ+∑
i
	​

α
im
	​

∑
i
	​

α
im
	​

ϕ
i
	​

	​

.

Exact residual score：

r
i
	​

=
	​

ϕ
i
	​

−
m
∑
	​

α
im
	​

F
m
	​

	​

2
2
	​

.

保留 r
i
	​

 最大的两个 members。Selection indices detached；member embeddings本身不detach。

Hybrid attention只读取：

8 slots+2 exact residuals.

两个arms使用完全相同的task pointer decoder、member/task encoders、slot auxiliary loss、oracle order和teacher-forced assignment sequence。

3. Exact model budget

每个arm恰好：

49,576 trainable parameters
	​


组成：

member encoder  12 -> 64 -> 64                 4,992
task encoder    10 -> 64 -> 64                 4,864
member-context Q/K/V/O, each 64 -> 64         16,640
slot assignment 64 -> 32 -> 8                  2,344
AR query        192 -> 64 -> 64               16,512
task key        65 -> 64                       4,224
                                                  ------
total                                            49,576

Full-set arm同样实例化并训练slot module，使参数量和auxiliary exposure一致；它只是用full members而不是compressed tokens形成decision context。

4. Data 与 exposure
training N                    {8,16,32}
unique training cases/N       1,024
total training cases          3,072

held-out N                    {8,16,32,64}
held-out cases/N              512
其中 mean-alias twin cases    256/N

model seed                    64054
data seed                     54054
minibatch/order seed          74054
bootstrap seed                84054

optimizer                     Adam
learning rate                 3e-4
updates                       600
batch size                    64
case exposures/arm            38,400
dropout                       0
checkpoint selection          exact final
bootstrap                     10,000 paired case clusters

Loss：

L=L
oracle pointer
	​

+0.1L
slot reconstruction
	​

+0.01L
slot mass KL
	​

.

没有 environment reward、PPO、critic、low actor、skill、membership event或duration。

十一、R54 的 M0 / M1 / M2
M0：实现有效性

必须全部满足：

exact member/task feature formulas与 unique feasible oracle；

critical task只有一个qualified member；

两arms初始化、参数量、minibatches、external member order和oracle prefixes逐项配对；

parameter count均为49,576；

slots、mass和top-L selection完全确定性，slot log-probability数量为0；

teacher-forced pointer replay误差：

≤10
−6
;

member/task simultaneous permutation后的canonical logits误差：

≤10
−6
;

random masked junk padding误差：

≤10
−6
;

capacity-one task mask使collision数量严格为0；

hybrid representation token数始终为：

M+L=10;

hybrid路径不创建member-member N×N tensor；

所有gradients、losses和parameters有限；

两arms恰好600 optimizer steps；

无reward、PPO、agent ID、slot ID、human role、task success predicate输入；

exact-final checkpoint reload误差为0。

失败：

INVALID_R54_HFSR_WIRING

唯一动作：只修明确的generator、oracle、equivariance、padding、replay、parameter-count或mask defect，原合同重跑。

M1：full-set reference access

对所有 held-out N：

token accuracy≥0.98,
critical-task assignment accuracy≥0.99,
normalized oracle-cost regret≤0.01.

其中：

regret=
1+∣C(a
⋆
)∣
C(
a
^
)−C(a
⋆
)
	​

.

另外：

macro exact-roster success≥0.60,
exact-roster success at N=64≥0.20.

失败：

NO_ACCESS_R54_FULL_SET_REFERENCE

唯一动作：永久退休精确toy/generator/model/gate，不解释field-slot candidate，不增加数据或网络。

M2：hybrid representation sufficiency

对所有 held-out N：

token accuracy≥0.96,
critical-task assignment accuracy≥0.95,
normalized regret≤0.03.

并同时要求：

UCB
95
	​

[regret
hybrid
	​

−regret
full
	​

]<0.02∀N,
full macro exact-roster+10
−8
hybrid macro exact-roster
	​

≥0.80,
full N64 exact-roster+10
−8
hybrid N64 exact-roster
	​

≥0.75,
P[critical member∈C
L
]≥0.90,
mean-alias twin critical-decision accuracy≥0.90,
medianexp[−
m
∑
	​

ν
m
	​

log(ν
m
	​

+10
−8
)]≥4.

失败：

VALID_FAIL_R54_HYBRID_REPRESENTATION

绑定 abandonment：

永久退休精确 M=8,L=2；

永久退休 reconstruction-error residual selection；

不改 M,L、网络宽度、loss系数、数据量、seed或门槛；

不自动换成attention slots、ISAB、graphon、mean field或更大 residual；

不进入dynamic membership或variable-time实现。

全部通过：

PASS_R54_HYBRID_REPRESENTATION

唯一下一动作：

注册一次固定 membership、固定/common external clock 下的 full-set reference versus hybrid-field ordinary-learning transport gate。

仍不授权 join/leave、heterogeneous T
i
	​

、skills、intrinsic reward或 UAV 训练。

十二、现在处理与必须延后
现在写入架构合同

(member_key, membership_epoch) ledger；

deterministic active-set reference；

deterministic slot/mass/residual contract；

ready-set-only autoregression；

raw member snapshot、order、prefix与old-logp replay；

event duration、γ
T
i
	​

 return/bootstrap的数据字段；

low actor保持 π
l
	​

(a
i
	​

∣o
i
	​

,z
i
	​

)。

R54 PASS 后才实现

field slots；

exact residual；

ordinary-learning transport。

R55 PASS 后才实现

episode内 exogenous join/leave/rejoin；

survivor hidden continuity；

membership-censored event rows。

R56 PASS 后才实现

fixed roster下的外生 heterogeneous T
i
	​

；

ACAC-style event GAE；

elapsed-time-conditioned critic/policy。

R57/R58 PASS 后仍需新审阅

learned readiness；

learned termination；

stochastic slot directives；

HMASD-like process intrinsic；

team latent；

S7/UAV transfer。

十三、最强反对意见
一个固定 M=8,L=2 的压缩器可能仍会丢失真正的拓扑割点，
	​


因为：

稀有关键成员未必是feature-space reconstruction outlier；

关键性可能只在某个任务、邻接或未来状态下出现；

top-L residual selection本身也可能随着 N 增长失效；

full-set attention具有 O(N
2
) reference优势，而hybrid被要求近似它。

这个反对意见不改变推荐。相反，它正是 R54 必须包含：

unique critical member；

equal-mean multimodal twins；

unseen N=64；

critical residual coverage；

full-set prerequisite；

的原因。

若 R54 有效失败，就永久退休该精确 hybrid，而不是通过扩大 M/L 或更换 salience score挽救。这使反对意见成为可证伪条件，而不是事后解释。

最终单一决定
	​

八篇论文的核心解读无 route-changing factual error；
ACE/ACAC/InforMARL 的精确机制进入架构合同；
Sable、CT-MARL、IARO只作诊断；
ExpoComm条件吸收；Safe-M3-UCRL不吸收；
四层候选修改为 ARES-SMDP；
deterministic representation 与 stochastic MAT action严格分离；
MAT只对同一时刻真正ready的成员动作进行AR；
每个成员event使用真实 T
i
	​

、γ
T
i
	​

 和agent-owned history；
R53 terminal后唯一下一门为R54-HFSR-G0；
R54首先否决或接受 M=8,L=2 的表示充分性；
在representation、learning、membership、time依次PASS前，
不联合 N
t
	​

+T
i
	​

，不恢复skills/intrinsic，不进入UAV训练。
	​

	​


本裁决只完成架构选择和 gate 注册建议。在该回复被归档、形成仓库 disposition，并完成 R53 terminal review之前，不授权实现 R54 或修改当前 controller。
