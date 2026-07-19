1. Evidence validity and delta
注册结果有效

接受本轮终局：

PASS_CLEAN_CARRIER_DIRECT_ACCESS

实现、carrier calibration 和 direct access 三项均通过。正式运行完成了 320,000 个环境 transition、1,280,000 个 active-agent rows、1,000 个 PPO optimizer steps 和 4,000 个训练 ledger；skill/high/intrinsic 路径计数均为零。token log-probability、joint log-probability、value、hidden 和 autoregressive prefix 的最大 replay 误差全部为零，schema-3 model/optimizer checkpoint 也精确恢复。

Carrier controls 通过：

constructive 最低 P/S/U=1/1/1；

uniform random 的正 utility 比例为 1.0，平均 U=0.32421875。

Direct learner 最终：

deterministic P/S/U=1.000000/0.998210/0.999105；

stochastic P/S/U=1.000000/0.973307/0.986654；

deterministic final-minus-zero utility CI95 为
[0.498535,0.499105,0.499593]。

这些结果均远离注册阈值，而不是边缘通过。

Process channel 的“零污染”成立

新增状态只有：

actuator_position
actuator_velocity

它们由环境按当前 active lifecycle 的 primitive action 更新；temporary absence 期间不推进，rejoin 恢复原状态，genuine join 清零，并进入环境 snapshot。actor observation、critic state、task reward、task transition、GAE 和 PPO 都不读取它。

Runner 并未创建新的 learner。它通过 ledger_factory 和 environment_factory 把 clean carrier 接入未经修改的 Stage-B direct runner，并明确检查 skill、高层和 intrinsic 计数为零。

因此，本轮 direct 数值与旧 Generic-SHORT Stage B 完全相同并不构成一个独立新 seed replication；它是相同 learner、task、ledger/action seeds 和 evaluation contract 在一个行为上 inert 的环境包装下得到的结构性等价结果。这种精确一致支持“process side-state 没有污染 access path”，但不增加独立统计重复性。旧 Stage B 的 deterministic/stochastic 结果和 CI 与本轮逐项相同。

相对 Iteration 5 的精确增量

本轮只改变以下判断：

A／carrier-access 解释已被解析。
Iteration 5 的 RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS 应解释为其精确 spatial carrier 的 substrate-specific 失败，而不是动态 roster、ordinary recurrent control 或 process-channel carrier 的普遍失败。

当前 clean carrier 现在是 access-valid evidence substrate。
它可以承载后续比较的上游 access prerequisite。

D／direct recurrence 作为 mandatory null 得到加强，但未成为最终 verdict。
它证明当前 Generic-SHORT 任务可由强 active-set recurrent instrument 学习；没有证明显式 skill、transfer 或 heterogeneous lifetime 永远无价值。

B/C 没有获得正证据，只是从“不可识别”变为“可在合格 substrate 上提出后续证据源”。

Iteration 5 的精确 C1 objective 仍然退休。
换 carrier 后 direct access 通过，不能反向修改其 action-TV、forced-effect、overlap 和 shuffle-null 失败，也不能重新解释 C1-on utility 差异。先前处置明确规定 clean-carrier positive branch只解析 A，并保留 D/B/C，而不自动实现任何层级候选。

新增的关键限制：clean process 是 action tape 的确定性编码

虽然 channel 不含任务字段，但“task-neutral”并不等于“可直接作为 intrinsic semantics”。

实现满足：

v
t+1
	​

=0.75v
t
	​

+0.25F(a
t
	​

),F(a
t
	​

)∈{−1,0,1}.

因此：

F(a
t
	​

)=4v
t+1
	​

−3v
t
	​

.

三个 force 值与三个 primitive actions 一一对应。只要保留起始 velocity 和连续 velocity 序列，完整 action tape 可以被精确恢复。

这产生一个严格的 claim ceiling：

channel 可以证明 lifecycle-owned、可 snapshot、与任务奖励隔离的物理 side-state 可以存在；

channel 可以用于 mask、leave/rejoin 和行为后果审计；

它不能直接支持新的 q_d/posterior intrinsic reward，因为从 z 预测该 channel 可以退化为从 z 预测 action sequence；

若 null 已条件化完整 action tape和起始 process state，则剩余 process residual 在当前确定性实现中应为零。

这不使本轮 access result 无效；它使“把 Iteration 5 posterior 接到 clean channel 上”成为尤其明显的 R29 重命名风险。

Checkpoint claim ceiling

当前 direct training 的每个 rollout 是完整的 80-step episode；learner checkpoint 位于 update boundary，保存 model、optimizer、ledger counter 和 Torch RNG。process state 则由环境 snapshot 单独做 round-trip。因此本轮的两个 checkpoint 声明在其注册边界内成立。

但这不证明未来 B/C 的 mid-segment live resume。显式 hierarchy 仍必须把 policy lifecycle、open event trace、skill/command、age、event RNG、pending membership transaction、worker snapshot 和 policy version 放入一个联合 fail-closed checkpoint；不能从本轮两个彼此分离的检查自动继承该结论。

2. Two-to-four-candidate causal portfolio

A 已成为验证过的 infrastructure，不再占用 live algorithm portfolio。以下四个候选并列，不构成唯一 successor 排名。

D — Information-matched direct active-set recurrence

机制

显式 skill bottleneck可能不是该任务或最终能力的必要表示。一个 recurrent policy可把持续、响应和 leave/rejoin 恢复编码在每个 lifecycle 的 hidden state中，直接输出 primitive action。

因果 estimand

在相同 carrier、actor-visible information、训练 exposure、critic能力和 checkpoint规则下：

Δ
D
	​

=U
hierarchy,heldout
	​

−U
direct,heldout
	​

.

Held-out 必须包含未见 membership schedule 和未见 active-duration distribution，而不只是训练 ledger。

预测

matched direct policy 对 hierarchy noninferior；

删除 high、skill 和 intrinsic 后，utility、transfer 与 sample efficiency 不下降；

hierarchy 中可能出现的 label/action separation不产生额外负载能力。

最强反证

一个具有 material、persistent、nuisance-resistant 且自然使用的 skill hierarchy，在信息和 exposure匹配时，对未见 roster/lifetime 给出 material external-utility或 sample-efficiency优势。

置信度

对当前 clean carrier 的 ordinary access：高；

对最终 decentralized variable-lifetime目标的充分性：中等。

原因是当前 direct actor不是纯 local executor，见第 4 节。

B — Factorized discrete process executor

机制

当前共享 recurrent low actor只通过 categorical skill conditioning区分行为。共享动力学和 action head可能让不同 z 在联合训练中互相干扰并收敛到几乎相同的闭环策略。

B 用三个互斥、容量受限的 recurrent/action adapters 替换“共享 actor + 单一 skill conditioning”：

shared observation trunk
        |
select exactly one adapter by z
        |
recurrent transition + action distribution

它保留 K=3、KEEP/SET、外生机会和 event-time credit；第一证据源不增加 intrinsic reward。

因果 estimand

Δ
B
U
	​

=U
factorized
	​

−U
capacity-matched shared
	​

,

并辅以：

same-snapshot z → action dependence；

自然 skill usage；

join/rejoin、active-age 和 active-set strata中的方向稳定性；

held-out membership条件上的 utility。

当前 actuator channel separation只能作为 action-behavior read，不能独立充当语义 estimand。

预测

factorized arm形成两个以上自然占比充分、跨 event strata稳定的行为；

相对 shared arm具有外部任务增益；

增益不是单纯来自更多参数。

最强反证

adapters获得非零 gradient 和 drift，但只出现参数/logit差异，没有自然 utility或稳定执行差异；

capacity-matched shared arm表现相同；

direct recurrent policy在 held-out条件下仍 noninferior。

置信度

中低。既有证据支持“共享 low executor的 z 作用太弱”，但尚未证明参数分隔是原因。

E — Executable-skill assignment／credit bottleneck

机制

Stage C 与 Iteration 5 都缺少已确认的 executable skill object，因此 high assignment和 owner-event credit一直未被独立识别。即使 low executor能够提供 persistent/reactive primitives，terminal team reward可能仍不足以让 high policy在异步 owner events上选择正确组合。

E 是因果解释，不是立即增加一个新 critic。第一步应使用冻结、供给的 executable primitives来隔离现有 high/event path；只有现有 high path在这种正控制下失败，新的 credit replacement才成为可讨论对象。

因果 estimand

Δ
E
	​

=U
learned high+supplied executor
	​

−U
frozen/uniform high+same executor
	​

,

同时读取其相对同-carrier direct policy的 gap。

预测

routing-only oracle可以用 supplied primitives解决任务；

learned high却不能显著超过 frozen/uniform high；

high replay、event return、gradients和 optimizer exposure均有效。

这会把失败定位到 assignment、credit或固定 opportunity interface，而不是 skill formation。

最强反证

learned high在 supplied executor上可靠取得任务 access并超过 frozen high。那将削弱 E，并把主要不确定性推回 B／自然 skill creation。

置信度

中低。旧 fixed-primitive toy 曾暴露 high access问题，但不是同 carrier因果控制；当前 clean result本身没有运行 high policy。

C — Three-basis simplex process command

机制

硬 categorical z 可能把需要连续调节的 persistent/reactive倾向强制压入三个互斥标签。C 保留三个共享 basis，但用：

w
i
	​

∈Δ
2
,c
i
	​

=
k=1
∑
3
	​

w
ik
	​

b
k
	​


替换 one-hot skill。KEEP 保持当前 command，SET 更新 w_i；lifetime仍由连续 active KEEP run length产生，不增加 duration head或 learned hazard。

因果 estimand

Δ
C
	​

=G
simplex
	​

−G
one-hot
	​

,

其中 G 必须是 held-out membership/lifetime条件下的 controllability和 external utility，而不是当前 action-derived actuator trace上的 classifier accuracy。

预测

learned commands不全部坍缩到 simplex vertices；

non-vertex command产生可重复、负载相关的中间行为；

相对 one-hot B产生额外 held-out utility或 transfer。

最强反证

command几乎总在 vertices；

non-vertex只混合 action probabilities，不形成额外任务能力；

B或direct可完全复现其行为。

置信度

低。当前结果没有证据表明“离散性”是 bottleneck；clean actuator channel又不足以单独验证连续过程语义。

3. Replacement and simplification ledger

A 已完成其功能：保留 clean carrier与 direct-access result作为证据 substrate；删除把 A 当作 algorithm candidate的做法。

Candidate	Retained	Deleted	Replaced	Added
D	clean carrier、typed membership、active masks、survivor hidden、terminal external reward、centralized training critic	high policy、skill latent、KEEP/SET、semantic objective、event opportunity actor	hierarchy替换为 primitive-time recurrent direct policy	无新学习模块
B	K=3、KEEP/SET、event runtime、外生 opportunities、owner-event return、shared observation trunk	Iteration-5 posterior reward；shared FiLM/conditioning作为唯一 skill separation	low recurrent/action conditioning	三个互斥、低秩、总容量匹配的 adapters
E	F0 high/event policy、当前 event critic/return、固定机会、external reward	在诊断中删除 learned low与所有 intrinsic	low executor暂时替换为冻结 supplied primitives	只增加 positive-control executor及 routing-only oracle；不加入新 credit模块
C	三个 process bases、event lifecycle、KEEP语义、low recurrence	categorical embedding和 categorical SET head	one-hot z 替换为 simplex command	exact continuous sample、transformed density和 command checkpoint state

明确拒绝：

B adapters
+ C simplex
+ posterior
+ graph
+ team latent
+ learned hazard
+ new critic

在同一个首轮实现中共同启用。那会同时改变 executor、interface、representation、reward、timing和credit，无法归因。

E 的 supplied executor只能是诊断正控制。它不能被包装为最终“scheduler + 手写角色”算法。

4. Ordinary-MARL and intrinsic boundary
当前 direct policy 是强 access instrument，而非天然公平的最终 decentralized baseline

当前 direct actor在每个 primitive step读取：

focal observation与其 lifecycle hidden；

全 active set的 member-embedding sum；

log(1+N)；

当前 autoregressive frontier中 earlier-action counts。

critic读取 active-set context和八个 common task fields。

因此它是一个强 team-context access upper bound，不能自动等同于最终 decentralized execution。未来 D 与 B/C 的 load-bearing比较必须满足至少一种：

direct与hierarchical low actor都只能使用相同 local information；

两者都获得相同、明确计费的 active-set communication；

证明 direct的set summary和prefix在部署时属于合法公共信息。

否则 direct胜出可能来自执行信息优势，而不是 hierarchy冗余。先前收敛审阅也明确记录了这个限制。

Intrinsic 边界

当前 portfolio中的 D、B、E、C 的第一证据源都不需要 intrinsic reward。

未来任何 environment-agnostic semantic signal至少必须：

只读取 focal active lifecycle 的局部物理后果；

不读取 task clock、persistent/short progress、owner、wave、role、contact、success、reward或return；

以 action-conditioned null排除 primitive action tape；

不按 segment duration放大；

score只进入所属 low segment的 credit；

不进入 high/event return、KEEP/SET advantage或lifetime选择；

forced intervention只用于审计，不能成为 reward或policy gradient。

当前 clean channel不能满足“超出 action tape的过程 residual”。完整 velocity序列精确编码 action；给定 action和start state后又没有剩余随机/环境动力学。因此：

q(z | clean-process trajectory)

不能被批准为新的 semantic reward，而：

q(z | process, action) - q(z | action)

在当前确定性 channel上理论上没有正 residual。

这也说明“字段名不含 task token”只是必要条件，不是充分的 intrinsic-validity证明。既有原则同样禁止把 action、raw task observation delta或 recurrent hidden当作可执行语义的替代。

5. Variable membership and lifetime semantics
Active masks 与 direct probability

Direct joint behavior probability只有当前 active成员的 primitive autoregressive factors：

p
θ
	​

(A
t
	​

∣O
t
	​

,H
t
	​

,σ
t
	​

)=
j=1
∏
∣A
t
	​

∣
	​

π
θ
	​

(a
σ
t
	​

(j)
	​

∣o
σ
t
	​

(j)
	​

,h
σ
t
	​

(j)
	​

,g(A
t
	​

),a
σ
t
	​

(<j)
	​

).

外部 membership ledger与 recorded order没有 policy gradient。Inactive lifecycle：

不在 order中；

不采样 action；

不贡献 token log-probability；

不更新 recurrent hidden。

实现对 order是否恰好是 active set的排列做 fail-closed检查，PPO loss也按真实 active count归一化。

内部张量仍按 MAX_LIFECYCLES=6 分配；这在本轮是 storage envelope，不是 dummy-agent决策。它不应被误称为一般 ragged/open-roster scaling证明。

Genuine JOIN

t=0 的四个 genuine members和 t=40 的两个新 members进入 active set；

direct hidden的未使用位置保持零，第一次 active action从零 hidden开始；

clean process state同样清零；

没有 join前 actor row。

代码与测试均验证新成员 process为零，direct hidden contract也检查 t=40 的新 lifecycle hidden为零。

Temporary LEAVE 与 REJOIN

Temporary leave时：

lifecycle从 active mask移除；

direct hidden冻结；

previous action与 active execution counter不推进；

process position/velocity冻结；

absence期间没有 primitive actor factor或inactive reward。

Rejoin时：

membership epoch增加；

frozen direct hidden恢复；

clean process state原样恢复；

rejoin后的第一个 active action才重新推进 hidden和process。

环境 membership state machine及process audit分别验证这些语义。

Terminal LEAVE

Terminal leaver不再产生 actor rows或process更新。当前 direct instrument的固定 tensor中可能仍保留不可达的旧 hidden数值，环境process字典也保留 tombstoned state；它们因 active mask而不可读、不可更新。

这足以满足本轮 access instrument，但最终 event-runtime integration应在row finalization后明确丢弃policy lifecycle状态，并禁止同物理标签复活旧生命周期。正式 event contract已经要求 terminal leave零 bootstrap和状态删除。

Clocks

本轮只有：

physical time：每个真实环境 step；

membership-event time：t=0/20/40/60 的外部结构边界；

active process time：clean process只在 focal lifecycle active时推进。

本轮不存在：

policy opportunity event；

KEEP/SET；

high owner event；

skill segment；

segment credit window；

learned termination；

heterogeneous realized skill lifetime。

Direct GAE逐 physical step使用 team reward和一步 γ,λ。Membership event没有actor likelihood。

因此本轮只证明了membership churn下的 ordinary physical-time control，没有证明 variable skill lifetime。

未来 B/C 必须恢复：

R
i,n
	​

=
r=0
∑
Δ
i,n
	​

−1
	​

γ
r
r
env
	​

(t
i,n
	​

+r),γ
Δ
i,n
	​

V(C
t
i,n+1
	​

	​

),

并让 λ 只沿同一 owner的真实 policy events推进。Silent steps、其他成员事件和membership事件都不能制造actor ratio。

Segment ownership

当前 clean process没有 semantic segment或 credit owner；它只是 environment-owned active trajectory。

未来 segment必须至少由：

(lifecycle_key, membership_epoch, policy_version, command/skill)

唯一所有，并满足：

temporary leave关闭当前 segment；

rejoin开启新 segment；

不跨 policy version；

每个 low transition最多属于一个 segment；

inactive interval不计入长度或reward；

external membership boundary无actor ratio。

Checkpoint

本轮：

direct update-boundary checkpoint保存 model、optimizer、RNG与下一 ledger；

environment snapshot保存 membership/task/process side-state；

两者各自精确 round-trip。

未来 mid-rollout hierarchy checkpoint必须联合保存 lifecycle store、skill/command、age、event traces、opportunity/order RNG、pending transaction、worker snapshot和policy version，缺失任一项必须 hard fail。

6. Literature principles, not imports
可兼容原则
Principle	可迁移内容	不可迁移部分
Agent-centric asynchronous credit	γ 按真实 physical elapsed time；λ 按 owner-event深度；只抽取真实事件历史	固定 n_agent rollout、固定 roster critic shell
Per-member readiness	每member独立到期、absence/dropout压力测试	一步 γ return、固定 num_agents buffer、把mask当JOIN/REJOIN
Active-set representation	shared node/token参数、permutation-safe pooling、局部稀疏候选	固定配置 runner，不能替代 episode-internal churn
Bounded topology	从一开始构造稀疏候选，避免先做完整 N² pair score	固定循环ID、同步 one-peer clock、默认通信辅助损失
Duration-aware value	elapsed time必须进入return/value语义	全员共享 Δt、PINN/HJB/VGI整栈
Population diagnostics	mass、coverage、dispersion作为无奖励诊断	无限同质 representative agent、丢失rare-critical member
Large-N capacity	未来的吞吐与显存 comparator	固定 T×N flatten不具备roster state ownership
Relative representation	feature-wise spread可检查场表示aliasing	全员投票、共同终止、eigenvector intrinsic option system

ACAC 提供最直接的 γ^{Δt} 与 event-depth λ 分离原则，但其 roster固定。ACE提供 readiness/dropout壳，却缺少 duration-correct return。

InforMARL 只支持跨固定配置的共享图权重和pooling；Sable解决固定大 N 的容量；ExpoComm提供有界拓扑思想，但三者均未定义 episode内 JOIN/LEAVE/REJOIN 的hidden和credit ownership。

Safe-M3-UCRL 的 pure mean field会抹去绝对人数和关键个体；CT-MARL只有共享 Δt；IARO的joint option依赖全员同步执行与共同终止。这些都不能作为当前 successor。

收敛的原则应保持为：

active lifecycle ownership
+ exact physical/event-time credit
+ task-neutral but action-null-resistant process evidence
+ mandatory information-matched direct null

而不是：

graph + retention + communication + mean field
+ team latent + option discovery + continuous-time model

现有综述也明确指出，没有一篇列出的工作同时实现 episode内 JOIN/LEAVE/REJOIN、survivor continuity和正确 on-policy roster semantics。

7. Retired-line exclusion
R29

当前 clean velocity递推精确编码 primitive action。把：

log q(z | clean process)

加入 low reward，会把 action-information换成“actuator-information”名称，实质仍是 R29。

因此：

clean channel可作审计；

不能直接成为 intrinsic reward；

不能通过换posterior、窗口或系数声称是新路线。

R31-CFEI

Forced skill/action/process差异可以继续作为诊断统计，但不能：

训练 observational effect posterior；

把 forced effect score当reward；

用自然关联替代 intervention control。

R31已显示自然关联强并不意味着forced effect超过执行噪声。

R32-IFEPG

B 的 adapters若以后训练，不能接受由forced-effect advantage产生的policy gradient。Forced branches只能审计；不得重新使用 effect U-statistic、FiLM-only intervention gradient或其学习率/窗口变体。

R33-IRSC

没有 complete-roster effect enumeration、pair complementarity score、pair sham或head-only expected-score update。任何 high assignment证据必须来自正常 external return与机制匹配 comparator，而不是干预评分。

Iteration 5 C1

禁止把以下组件整体迁移到 clean carrier：

conditional process posterior
+ signed posterior-minus-context score
+ beta=0.05 low reward

Iteration 5 的精确 objective已经有效失败；而 clean process又是action-derived，迁移后更接近R29，不是“修复后的C1”。

Task shaping

禁止把 persistent owner、wave active、wave progress、short completion、terminal utility、role或success重新编码为process target或intrinsic。它们可以作为external task observation/reward，但不能证明environment-agnostic semantics。

Identity

Routing key和membership epoch只能定位状态与拒绝stale rows，不得进入embedding、pooling、adapter选择或command。

Scheduler-only

E 的 supplied-executor high test只是诊断正控制；它不能被推广为“手写skill + learned scheduler”的最终算法。B/C必须改变可学习executor/interface，而不仅改变检查时刻。

Duration catalogue

所有 live candidates保留：

lifetime = consecutive active KEEP run length

没有离散 duration action、SET(current)、duration reward或age-payment。若未来学习 event time，必须另行注册hazard、survival和censoring likelihood；当前 portfolio不包含该路线。

8. Two or three next-evidence candidates

以下是按逻辑依赖排列的三个小型证据候选。顺序不是唯一 successor排名，也不授权执行。

E1 — Clean-channel action-equivalence audit

Comparator

真实 actuator_position/velocity trajectory；

从相同 start process state和实际 primitive action tape确定性重建的trajectory；

action-only null。

Estimand

ϵ
a
	​

=
t
max
	​

∣F(a
t
	​

)−(4v
t+1
	​

−3v
t
	​

)∣,

以及：

ϵ
x
	​

=
t
max
	​

∥x
t
observed
	​

−x
t
predicted
	​

(x
0
	​

,a
0:t−1
	​

)∥.

两者是exact-equivalence reads，不设置可调统计阈值。

Mutually exclusive branches

EXACT_ACTION_EQUIVALENCE
两个误差为数值精度零。当前 channel永久保持audit-only；所有基于它的semantic intrinsic proposal关闭。D/B/E/C仍活，但B/C只能靠结构与external task evidence。

NONTRIVIAL_PROCESS_RESIDUAL
存在未由action/start解释的registered dynamics。只有此时才可为该residual设计单独、action-conditioned semantic null；仍不授权reward。

INVALID_CHANNEL_AUDIT
action、process或snapshot ledger不一致。只修审计实现，不改process dynamics。

Portfolio update

该证据主要决定是否还存在一个独立“clean semantic pressure”候选。预期 exact-equivalence 会关闭该候选并提升结构性B、high-path E和ordinary D的相对重要性。

Prohibited rescues

不得改变 damping、drive、step、force map、process fields、加入noise、改projection、换window或训练posterior。

Exact implementation boundary

零policy update、零optimizer、零reward read；只读取现有代码方程和已归档/确定性生成的active process rows。不得修改normal trainer。

E2 — Supplied-executor high-path localization

Comparator

同一 clean carrier、同一 event runtime和external reward内：

learned_high + supplied_executor；

frozen/uniform_high + identical supplied_executor；

routing-only oracle assignment，用于证明executor与固定opportunity合同可解；

matched direct recurrent access arm。

Supplied executor只作为positive control，例如三个透明primitive modes：

always IDLE
always PERSIST
always SHORT

它是task-specific diagnostic instrument，不是候选最终技能库。

Estimand

learned-high minus frozen-high paired utility；

final-minus-zero high-policy gain；

相对direct utility gap；

exact high likelihood、event value、gradient、owner-event return和checkpoint；

oracle在相同opportunity ledger下的可达性。

Mutually exclusive branches

HIGH_ACCESSES_WITH_SUPPLIED_EXECUTOR
learned high显著超过frozen high，并达到预注册access。E下降；B上升，因为现有high path能利用已存在的executor。D仍是mandatory null。

HIGH_NO_ACCESS_ORACLE_VALID
oracle可解、direct通过，但learned high不学习。E显著上升；不应先实现B/C或新semantic reward。

OPPORTUNITY_CONTRACT_NO_ACCESS
oracle本身失败。当前固定opportunity interface不能承担该诊断；不得由此授权learned scheduler。

INVALID_HIGH_PATH
replay、event credit、mask、count、checkpoint或direct access失效。只修具体实现。

Portfolio update

所有候选均更新：

high pass：B更可识别，E弱化；

high fail：E上升，B/C暂缓；

oracle fail：当前event substrate不适合assignment判断；

supplied hierarchy达到任务 access仍不自动削弱D，因为primitives是手工供给。

Prohibited rescues

不得修改opportunity schedule、event return、budget、seed、threshold、high width、reward、primitive table或加入intrinsic/new critic/learned timing。

Exact implementation boundary

独立diagnostic runner；supplied low无trainable parameters、零low optimizer；只训练现有high/event path。Oracle字段不得进入learned policy、reward或advantage。该证据不能进入integration。

E3 — Factorized-versus-shared executor comparison

仅当 E2 表明现有 high path可利用supplied executable skills时，该source才有充分识别力。

Comparator

一个结果中同时包含：

capacity-matched shared-conditioning hierarchy；

B 的factorized discrete adapters；

matched direct recurrent null。

三臂共享：

clean task与membership ledgers；

high/event architecture与opportunity schedule；

external terminal reward；
-总参数预算、environment transitions和optimizer exposure；

zero/final evaluation、checkpoint选择和RNG合同。

不启用posterior、intrinsic、graph、team latent或simplex。

Estimand

主要 estimand：

Δ
B
U
	​

=U
factorized
	​

−U
shared
	​

,

以及相对direct的held-out utility。机制读数包括自然 skill usage、same-snapshot action control和join/rejoin strata stability，但clean actuator separation不能单独构成semantic pass。

Mutually exclusive branches

FACTORITZED_TASK_AND_EXECUTION_GAIN
factorized相对shared具有material task增益和稳定自然使用。B上升；C保持替代解释；D被局部削弱但不退休。

DIVERSITY_WITHOUT_VALUE
factorized只增加action/process separation，没有external utility。记录arbitrary diversity并退休B。

NO_FACTORITZATION_EFFECT
shared与factorized等价。退休“共享executor interference”解释。

BOTH_HIERARCHIES_FAIL_DIRECT_PASSES
E或D上升；不得添加posterior或simplex救援。

DIRECT_ACCESS_OR_M0_FAILS
evidence source invalid；只修具体wiring。

Portfolio update

B通过但仍弱于direct：semantic/executor存在但不load-bearing，D继续上升；

B失败且E2 high已通过：C可获得一次独立interface评估资格，但不能自动实施；

B与shared都通过：当前问题转为natural assignment/utility，而不是executor capacity。

Prohibited rescues

不得改变adapter rank、总参数、skill count、budget、seed、threshold、event schedule、reward或增加C/simplex arm。不得在失败后迁移Iteration-5 posterior。

Exact implementation boundary

只允许替换low conditioning；shared与factorized总容量、数据和optimizer exposure必须匹配。任何后续C comparison必须是新的、单变量证据源。

9. Stop and integration conditions
A／access substrate

A 已被本轮 positive result解析：

clean carrier保留为access-valid evidence substrate；

不再作为algorithm candidate；

Iteration-5 spatial carrier继续退休；

不再创建第三个carrier来“进一步确认”access。

若后续修改 task、observation、direct learner或membership schedule，则必须重新建立同-carrier access，但不能把这种需求称作A复活。

D／direct recurrence

D 只能被以下联合证据显著削弱：

同-carrier direct access通过；

actor-visible information与communication匹配；

hierarchy具有material、persistent、natural且nuisance-resistant的learned semantics；

hierarchy在未见membership/lifetime上具有material external advantage；

优势满足decentralized execution，不依赖task shortcut。

Posterior accuracy、label entropy、forced effect、supplied primitives或训练内utility差异都不足以退休D。

B／factorized executor

退休条件：

adapters有梯度和drift但无稳定自然执行；

只有logit/action差异，没有external task价值；

shared arm在容量匹配后等价；

factorized semantics存在，但matched direct在held-out条件下noninferior。

合并条件：

若C的simplex长期坍缩为vertices且与B等价，C并入B；

不得为保留B而增加adapter rank、skill数或semantic reward。

E／high assignment/credit

退休条件：

supplied executable primitives下，现有high/event path可靠学习并超过frozen high；

high replay、credit和optimizer均有效。

上升条件：

oracle与direct均通过，但learned high失败。

即使E上升，也只能先设计一个单独的credit/assignment replacement；不能同时改critic、timing、executor和reward。

C／simplex command

退休或并入B：

commands坍缩到vertices；

non-vertex只混合primitive action probabilities；

没有held-out utility或transfer；

direct/B能复现全部行为。

C只有在one-hot executor已可执行、high path已可用，而non-vertex composition仍显示负载相关增益时，才有独立存在理由。不得通过增加bases、temperature sweep或新posterior维持它。

Toy/process line的整体停止条件

以下任一成立时，应停止当前显式process-skill/hierarchy toy线：

clean carrier已通过，但supplied executor下high path仍无法学习，且没有单一、可审计的assignment/credit replacement；

high path通过，但shared与factorized executor都不能产生自然、稳定、load-bearing行为；

B/C形成差异，但information-matched direct在未见membership/lifetime上noninferior；

当前clean process被确认只是action tape，而唯一“成功”的semantic route仍依赖它；

唯一可行方案需要task fields、identity、role、learned scheduler、duration catalogue或已退休effect objectives；

只有同时叠加graph、communication、team latent、new critic、hazard和semantic reward才出现效果。

停止后不应继续制造新toy、添加seed或修改阈值；应回到最终benchmark requirement或接受ordinary recurrent reduction。

Integration 条件

任何hierarchical candidate进入独立integration review前，必须同时满足：

access-valid同一carrier；

genuine JOIN、temporary LEAVE、REJOIN、terminal LEAVE和survivor continuity逐项通过；

exact probability、mask、RNG、credit、replay和联合live checkpoint有效；

learned，而非supplied或task-labeled的skill semantics；

segment所有权唯一且不跨membership epoch/policy version；

same-snapshot action control、持续环境后果、nuisance stability和natural overlap均达预注册material门；

semantic signal不是action tape、task progress、role、reward或identity shortcut；

与information、communication、参数、environment exposure和optimizer exposure匹配的direct policy相比，在未见membership/lifetime上有material外部优势；

贡献来自一个明确替换，而不是模块堆叠。

本轮只接受 clean access substrate，并完成上述 portfolio 更新；不授权 E1–E3 的代码、训练、计算或任何 B/C/E 集成。