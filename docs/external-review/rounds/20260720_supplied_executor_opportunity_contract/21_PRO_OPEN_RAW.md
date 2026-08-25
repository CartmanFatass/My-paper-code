1. Evidence and branch validity

裁决：保留注册状态

INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT

不得改写为 PASS、VALID_FAIL 或 MIXED。

仓库事实：实现层 M0 有效。 正式运行完成 320,000 个 primitive transitions、1,000 个 high optimizer steps、零 low optimizer steps；supplied executor 是 0=IDLE, 1=PERSIST, 2=SHORT 的零参数恒等映射。learned/frozen update-zero tensors byte-equal，learned-only high drift 非零，high log-probability/value replay、active masks、owner credit、RNG、JOIN/LEAVE/REJOIN、mid-segment checkpoint 和 fail-closed restore 全部通过。

仓库事实：科学比较器前提失败。

routing oracle：P/S/U=0.978699/0.660807/0.819753

frozen high：1.000000/0/0.500000

learned high：0.942383/0.938639/0.940511

learned-minus-frozen utility CI95：[0.435689,0.440511,0.445251]。

预注册顺序规定 oracle 的 P/S/U 必须全部至少为 0.95；代码在读取 frozen 或 learned 分支前先触发 oracle INVALID。因此 learned 的数值不能越过该优先分支。

有效实现与无效科学比较器必须分开：

实现不是断梯度、错误 replay、低层泄漏或 checkpoint 损坏。

无效的是“当前 routing oracle 足以证明相同 opportunity contract 可达”的科学前提。

learned-versus-frozen 差异仍是可信的次级观察：训练 high/event graph 确实改变了策略，并在这个固定任务、固定原语、固定机会过程上显著提高外部 utility。

但它不能建立：F1 applied-prefix 的独立价值、一般 high-credit 成功、learned skills、hierarchy efficacy、合作贡献、异质 lifetime、迁移或最终目标能力。

Supplied executor 本身没有 learned skill 含义：它只是将数值标签直接解释为任务原语，且不存在 low likelihood、low replay 或 low gradient。

2. Oracle opportunity diagnosis
诊断 A：逐步 constructive rule 被错误投影到稀疏机会过程

完整的 constructive_actions 假定每个 active member 每个 primitive step 都可重新选择动作：一个成员 PERSIST；wave 活跃时其他未贡献成员 SHORT；其余时间 IDLE。

当前 routing oracle 实际执行的是：

先由 private opportunity clock 生成当前 frontier；

对整个当前状态计算 constructive actions；

只把 frontier 内成员的建议 teacher-force 给 high runtime；

不在 frontier 的成员继续保持旧 primitive skill。

所以它不是 full-step constructive controller 的 event-time 等价实现，也不是机会受限问题的上界。它是一个无前瞻、无保持规划的当前状态投影。

诊断 B：SHORT 任务时间尺度短于机会间隔

每个 short wave 仅持续四个 primitive steps，成员必须连续两步执行 SHORT 才贡献一个单位；而每次 high action 后的新 opportunity gap 在 1..19 中采样。

这意味着：

wave 到达时不在 frontier 的成员可能完全无法在 deadline 前切换；

即使在 wave 后半段到期，也可能没有剩余两步形成 streak；

oracle 在非 wave 时把到期的非 owner 设为 IDLE，可能恰好在下一 wave 前锁住 IDLE；

full-step constructive 的 S=1 不能证明该 opportunity-filtered oracle 应有 S≥0.95。

这直接使当前 oracle 失去“机会合同可达性证明”的资格，但不使 event runtime、owner credit 或 learned signal失效。

诊断 C：learned high 很可能学到了预配置与保持策略

Generic-SHORT observation 显式含 physical time、wave active、remaining steps/work、active count、当前 skill age 和 previous primitive action。

因此 learned high 可以：

在可能的 wave window 前提前把多数成员配置为 SHORT；

wave 之间继续 KEEP SHORT，而不是遵循 oracle 的 IDLE；

长期保留一个 PERSIST member；

在 membership churn 后重新建立该组成。

其结果正表现为相对 oracle 略少的 P、显著更多的 S：

oracle   P=0.9787  S=0.6608
learned  P=0.9424  S=0.9386

这是与“预配置换取 reactive coverage”一致的推断，但尚未由 trace decomposition 证明。

即便该推断成立，它支持的也只是：

一个 recurrent event-time primitive allocator 可以利用固定任务时钟和机会历史形成高效持久配置。

它不等于 learned skill formation，也不证明这种策略在未知 wave schedule 或最终任务上可迁移。

诊断 D：F1 applied-prefix 贡献尚未被识别

当前 learned arm 只有 F1，没有 architecture-matched F0。F1 的 applied working roster 可能帮助同一 frontier 中的后续 owner 避免重复 PERSIST 或形成 SHORT 配置；但相同结果也可能由：

F0 initial-summary policy；

每 owner 独立 recurrent mark policy；

简单的时间感知有限状态控制器；

“一名 PERSIST、其余长期 SHORT”的任务特定规则

实现。

架构合同本身规定，只有 F1 相对 common-support-matched F0 改变相对 action scores并提高 utility，applied-prefix 才有不可约算法内容。

3. Two-to-four-candidate causal portfolio

以下四项不按 successor 顺序排列。

Candidate O — Opportunity-feasible comparator misspecification

机制

当前 oracle 是 myopic full-step rule 的 frontier-filtered版本，不是相同信息和控制权下的 causal opportunity-aware oracle。

因果 estimand

Δ
O
	​

=U
causal opportunity-aware oracle
	​

−U
current routing oracle
	​


并逐 wave 计算：

到达前已配置为 SHORT 的成员数；

到 t_w+2 前拥有机会的成员数；

opportunity-constrained maximum feasible work；

current-oracle regret。

预测

一个允许保持规划、但仍只在注册 frontier 上行动的 causal oracle 会显著提高 SHORT，可能清除原 0.95 floor。

最强反证

即使具有相同 actor-visible history并进行最优 causal规划，oracle仍远低于 0.95；或者连使用完整未来 ledger 的 hindsight ceiling 都无法清除该 floor。

置信度

高。

分离观察

当前 oracle失败是否主要集中于“wave 到达前成员刚被设为 IDLE且之后无及时 opportunity”的 rows。

Candidate R — Simpler scheduled recurrent mark policy suffices

机制

learned F1 的收益可能只需要：

current active-set summary；

physical time和task state；

per-member recurrent state；

persistent primitive commitment；

不需要 later-on-earlier applied-prefix coupling。

最小 reduction 是相同 lifecycle、opportunity、credit、fixed executor和参数图下的 F0／independent mark policy。

因果 estimand

Δ
R
	​

=U
F1
	​

−U
F0
	​


在 byte-equal initialization、相同 ledgers、相同 optimizer exposure 和相同 supplied executor下读取。

预测

F0 与 F1 都明显优于 frozen，但两者 utility、sample efficiency和自然 composition接近。

最强反证

F1 在 common legal support 上产生明确的 directional composition shift，并以正的 paired utility margin 超过 F0，且优势集中于多 owner frontiers。

置信度

中高。

分离观察

按 frontier size 分层的 F1-F0 增益：若 singleton frontier也有同等增益，applied-prefix不是解释。

Candidate P — F1 applied-prefix 确有 cooperative assignment value

机制

同一 frontier中，后处理的 owner读取已应用的早期 commitments，避免重复 persistent assignment，并补足 SHORT composition。

因果 estimand

Δ
P
	​

=U
F1
	​

−U
capacity/credit/data matched F0
	​


附加要求：

initial/working common-support TV；

directional shift；

utility transport；

多 owner frontier中的集中效应。

预测

F1 相对 F0 的优势在：

simultaneous structural arrivals；

rejoin/new join frontiers；

persistent owner丢失后的恢复；

frontier size大于一

时最明显。

最强反证

F0匹配F1；或F1概率变化只来自 hard mask/common-logit shift，没有外部 utility增益。

置信度

低至中。当前没有F0 arm，不能从learned-versus-frozen直接支持P。

分离观察

在同一 stored token上，将 working summary替换为initial summary后，是否改变 common-support relative scores，并预测真实任务增益。

Candidate B — Shared learned executor remains the bottleneck

机制

历史 Stage C／Iterations 4–5 中，shared skill-conditioned low actor没有形成 material natural skills；本轮在固定、完美可执行原语下，high actor至少能学习一种高 utility任务策略。可能的缺口因此位于 learned executor，而非 high graph完全不可训练。

候选替换是三个互斥、总容量匹配的 discrete process adapters，而不是再加 posterior。

因果 estimand

Δ
B
	​

=U
factorized learned executor
	​

−U
capacity matched shared executor
	​


且必须同时建立：

same-snapshot action control；

持续环境后果；

跨 JOIN/REJOIN/age strata稳定；

natural use；

相对 direct null的held-out价值。

预测

在 high/opportunity合同有效后，factorized executor相对shared executor形成自然可执行差异并提高外部utility。

最强反证

adapter有非零gradient和drift，却仅产生参数或logit差异；没有自然过程差异、任务增益，或仍不优于information-matched direct recurrence。

置信度

中低。本轮只表明fixed primitives使任务可学，不能证明factorization是正确修复。

分离观察

在valid high-path comparison下，shared与factorized low的自然行为和external utility是否分离。

4. Ordinary-MARL and replacement audit
最强 simpler reduction

现有 direct recurrent policy 每个 primitive step均可行动，并读取：

focal lifecycle observation和hidden；

active-member embedding sum与log(1+N)；

同一 primitive frontier中 earlier-action counts；

centralized team critic。

它在clean carrier上近乎完美访问任务，但拥有比event high/fixed executor更频繁的控制权与不同信息带宽。因此它是强access upper bound，不是现成的公平event-abstraction comparator。

对F1最强的机制匹配reduction不是full primitive direct，而是：

F0 scheduled recurrent mark policy
+ same membership spine
+ same opportunities
+ same fixed executor
+ same owner-event credit
- applied-working-prefix dependence
Replacement ledger
Candidate	Retain	Delete	Replace	Minimally add
O	已完成运行、event runtime、原threshold和INVALID状态	current oracle作为“可达上界”的解释	仅替换诊断比较器	causal oracle与hindsight feasibility ledger
R	membership、opportunity、fixed executor、event critic/credit	F1 working-prefix conditioning	F1改为F0／independent mark	无新学习模块
P	F1 graph、fixed executor、外部reward、event credit	无效routing-oracle efficacy claim	用valid opportunity comparator约束F1	architecture-matched F0 arm；无额外latent
B	high/event path、K=3、KEEP/SET、external reward	fixed executor用于最终算法；Iteration-5 C1 posterior reward	shared low conditioning改为互斥adapters	仅总容量匹配的adapter参数

首轮不得形成：

factorized low
+ simplex command
+ posterior
+ graph
+ learned hazard
+ new critic

这种组合同时改变executor、interface、representation、timing与credit，违反replacement-before-accumulation原则。

5. Variable membership, lifetime and intrinsic boundary
Membership 与 masks

本轮M0实际验证：

genuine JOIN：zero high state、无旧skill、立即进入structural frontier；

temporary LEAVE：关闭旧owner trace，冻结high state、skill、age与gap；

REJOIN：同一lifecycle、epoch递增、恢复state并立即获得opportunity；

terminal LEAVE：high state清空、skill删除、无后续actor row；

unaffected survivors保持high-state continuity；

只对active members形成frontier、mask和primitive action。

这些语义符合event architecture的state ownership合同。

必须区分的时间对象

Physical time：每个primitive step，决定环境推进与gamma指数。

Opportunity time：某owner被允许选择KEEP/SET的外生事件。

Event depth：同一owner的真实policy events，决定lambda递推。

Realized lifetime：同一skill在连续active KEEP中的执行时间。

Learning segment：由SET、leave/rejoin、terminal与policy-version边界切分的数据所有权窗口。

Owner-event return为：

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

+r),

非终止bootstrap为γ^Δ V；其他成员的events和silent steps不制造该owner的actor ratio。

本轮没有建立 variable-lifetime claim

虽然high actor可以KEEP同一primitive并产生不同skill age，但：

executor不是learned skill；

没有注册lifetime breadth、heterogeneity或held-out duration estimand；

任务可能由近静态“一名PERSIST、其余SHORT”配置解决；

没有与shared renewal、fixed lifetime或information-matched direct进行temporal causal comparison。

因此本轮只验证了event-runtime clocks和state ownership，不验证learned heterogeneous lifetime。

Intrinsic boundary

本轮intrinsic reward恒为零。未来signal仍不得读取task progress、owner、wave、success、contact、identity、role或external reward。

此外，clean actuator dynamics由primitive action确定，因此其trajectory本质上是action tape的连续编码，不能直接恢复成C1或新q_d reward。既有处置已明确将该channel限制为audit-only。

Decentralized use

Supplied executor本身完全local：

primitive_action_i = active_skill_i

但high commitment policy使用active-set summary和frontier autoregression。未来与direct null比较时，必须匹配可部署通信信息，不能把direct的primitive-time全队信息优势误作hierarchy冗余。

6. Literature principles, not modules

**ACAC：**可迁移的是gamma按真实微时间、lambda按owner-event深度，以及agent-centric有效event history；固定n_agent rollout与critic shell不可迁移。

**ACE：**可迁移per-member readiness、异步执行和dropout压力测试；其固定num_agents buffer和一步return不具备JOIN/REJOIN与gamma^{T_i}语义。

**InforMARL：**共享参数、permutation-safe active-set aggregation和稀疏候选是表示原则；其runner仍固定agent/node count，不能替代episode内membership ownership。

跨论文综述的直接结论是：没有一项现有工作同时实现episode内JOIN/LEAVE/REJOIN、survivor continuity与正确on-policy roster semantics。

因此应保留：

active lifecycle ownership
+ exact physical/event credit
+ permutation-compatible active-set handling
+ information-matched ordinary null

而不是导入：

fixed-N async buffer
+ GNN/attention
+ communication
+ team latent
+ synchronized option

作为模块堆栈。

7. Two or three next-evidence candidates

以下三个证据源不排序，也不构成实施授权。

Evidence A — Opportunity-feasibility audit

Comparator

当前myopic routing oracle；

使用相同actor-visible history和相同frontiers的causal opportunity-aware oracle；

允许读取完整未来ledger、仅作可达上界的hindsight oracle。

Estimand

三者的P/S/U；

per-wave maximum feasible work；

current-oracle regret；

owner loss后的minimum feasible persistent recovery；

wave到达前/到t_w+2前的可用SHORT commitments。

Mutually exclusive branches

causal oracle ≥0.95，current oracle失败：
当前比较器定义错误；原结果仍INVALID，但opportunity合同本身可达。

hindsight ≥0.95，causal oracle失败：
actor information/opportunity合同不能支持注册的causal floor；本G0不识别high learning。

hindsight也失败：
exact gap/task/oracle floor结构性不可达；退休该opportunity qualification合同。

current接近causal optimum：
learned优势来自oracle未拥有的策略表示或信息；需重新审计信息匹配，不能降低threshold。

Portfolio update

区分O、R/P与“task/opportunity本身不识别”。

Prohibited rescue

不改gap、threshold、reward、wave deadline、seed、observation或learner；不训练policy。

Minimal boundary

evaluation-only或有限状态动态规划；零optimizer、零reward修改、原INVALID状态不变。

Evidence B — Existing-checkpoint opportunity-use decomposition

Comparator

相同256个evaluation ledgers上的：

learned high；

frozen high；

current oracle。

Estimand

逐wave读取：

arrival前已在SHORT的active share；

arrival后发生的SET-to-SHORT次数；

到t_w+2前的due-owner coverage；

completion conditioned on feasibility；

frontier size；

persistent handoff latency；

pre-wave versus within-wave contribution。

Mutually exclusive branches

learned收益主要来自pre-positioning/long KEEP：
R上升；P下降；当前任务主要检验time-aware persistent allocation。

收益集中于multi-owner frontier中的within-wave composition：
P上升，授权理由仍需F0比较。

收益主要由physical-time/calendar window解释：
归类为task-specific scheduling signal，不作为一般hierarchy证据。

现有trace不足以区分：
返回UNDERPOWERED；不合并strata、不扩episode。

Portfolio update

直接区分simple scheduled reduction、F1 coupling与opportunity mismatch。

Prohibited rescue

不重训、不选best checkpoint、不改wave/gap/threshold，不用routing identity训练policy。

Minimal boundary

冻结checkpoint的read-only replay；只增加诊断字段和分析，不改行为路径。

Evidence C — Architecture-matched F0 versus F1 supplied-executor comparison

Comparator

F0 initial-summary high policy；

F1 working-summary high policy；

byte-equal frozen high control；

相同fixed executor、membership、opportunity、critic、credit、seeds、environment exposure和optimizer exposure。

Direct recurrent结果只作信息范围明确的外部reference，不替代F0。

Estimand

Δ
F1−F0
	​

=U
F1
	​

−U
F0
	​


以及：

common-support relative-score shift；

directional composition shift；

frontier-size-stratifiedutility；
-sample efficiency。

Mutually exclusive branches

F1显著超过F0，且valid oracle可达：
P上升；applied-prefix在本任务具有task-level assignment价值。

F0≈F1且均超过frozen：
合并到R；F1 prefix不是load-bearing。

两者均失败但valid oracle通过：
high credit/optimization解释重新上升。

两者均成功但不优于信息匹配direct：
event abstraction可执行，但无负载优势。

oracle或M0再次失败：
不读取F1-F0；仅处理具体invalid boundary。

Portfolio update

分离R与P，并决定B是否获得后续可识别性。

Prohibited rescue

不改fixed executor、opportunity、budget、seed、threshold、critic、reward；不加入learned low、intrinsic、graph或hazard。

Minimal boundary

唯一处理差异为architecture_mode=f0/f1；其余图、数据与执行合同完全相同。

8. Valuable unselected ideas

**Factorized learned executor B：**保留，但应等待valid high-path和F0/F1定位；否则同时改变high与low无法归因。

**Simplex command C：**继续park。只有one-hot learned executor已有效、且non-vertex composition产生不可由B复现的held-out价值时才有独立意义。

**Learned opportunity hazard／point process：**当前不开放。它需要完整survival、intensity、censoring与leave边界概率；不能作为oracle失败的scheduler-only救援。

**Schedule-shift frozen evaluation：**可用于检查learned high是否记忆固定wave windows，但应在existing-trace decomposition后进行，避免无必要地改变环境分布。

**Local-information direct comparator：**对最终integration很重要，可消除现有primitive direct actor的active-set/prefix信息优势；当前不是修复INVALID oracle所需的最小证据。

**新的action-null-resistant physical process：**仅在未来真实环境具有不能由start state和action tape确定的local consequence时再讨论；当前clean actuator不满足。

9. Stop and integration conditions
Candidate-level retirement／merge

O — comparator misspecification

causal oracle清除floor：退休当前myopic oracle作为upper bound，但保留event runtime。

hindsight仍无法清除floor：退休exact opportunity qualification contract。

R — simpler scheduled reduction

F0匹配F1：将F1合并为F0／ordinary scheduled recurrent controller。

F1在matched条件下稳定胜出：R下降但仍保留direct null。

P — applied-prefix value

F1不优于F0，或优势不集中于multi-owner common-support rows：退休P。

F1只改变distribution而不提高utility：作为decorative dependence关闭。

B — factorized executor

adapter有gradient/drift但无material natural semantics或external value：退休B。

B产生semantics但information-matched direct noninferior：不进入integration。

不得通过增加adapter rank、skill count、posterior或intrinsic保留B。

Toy／supplied-executor line stop

满足任一条件即停止本toy线：

opportunity-feasible hindsight ceiling无法达到注册任务floor；

learned gain完全归约为固定wave calendar或“一名PERSIST、其余SHORT”的task-specific规则；

F0与F1等价，且matched direct仍占优；

fixed supplied primitives是唯一成功executor，而learned executor无法形成自然语义；

继续前进必须同时增加hazard、graph、team latent、new critic、posterior与reward；

任一方案需要task field、identity、role、duration catalogue或退休effect objective。

Integration prerequisites

任何hierarchical candidate进入独立integration review前，必须同时满足：

comparator与scientific branch有效；

learned而非supplied的executor；

intervention-sensitive、persistent、nuisance-resistant且自然使用的skills；

anonymousJOIN/temporary LEAVE/REJOIN/terminal LEAVE和survivor continuity；

physical/opportunity/event/segment clocks及gamma^Δ credit正确；

exact probability、mask、RNG、replay和mid-segment checkpoint；

actor-visible information与direct baseline匹配；

在未见membership schedule和lifetime distribution上，对direct提供material external-utility或sample-efficiency优势；

不使用task-shaped intrinsic、identity、role或模块堆栈。

当前结果不满足integration条件，也不授权修改oracle、实现新候选或启动后续实验。
