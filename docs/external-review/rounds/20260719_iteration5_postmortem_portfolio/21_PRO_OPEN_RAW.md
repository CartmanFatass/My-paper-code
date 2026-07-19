1. Evidence validity

本轮注册结果应接受为一个实现有效、科学分支有效，但算法比较受上游访问条件阻断的终局结果：

RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS
实现有效性

三臂都完成了注册暴露；C1-on、C1-off 的策略初始状态逐字节一致，除 beta 外语义状态一致；行为概率、价值、隐状态和前缀 replay 均满足合同；C3 的模型与优化器 checkpoint round-trip 误差均为零。C3 完成 320,000 个环境步和 1,000 个优化步，参数确实发生了非零变化，因此不是断梯度、未训练或加载失败。

语义实现也与登记设计一致：

process 输入先从策略图中 detach；

posterior 本身没有行为似然，不能向高、低策略反向传播；

每个低层 transition 恰好属于一个 lifecycle、membership epoch、policy version 下的 process window；

intrinsic score 只写入对应的低层 reward；

高层事件回报、KEEP/SET 概率和 lifetime 信用不读取该 intrinsic；

online/frozen posterior、优化器、采样 RNG、窗口账本和 intrinsic 计数都进入严格 checkpoint。

runner 也正确执行了注册的优先分支：只有在实现、carrier 和 direct-access 都通过后，才读取 semantic 与 task-value 分支；direct access 失败时，后面的连续读数仍报告，但不能覆盖上游失败。

最强支持结论

第一，精确的 Iteration 5 spatial carrier 已经退休。
C3 最终 deterministic P/S/U=1.0000/0.526855/0.763428，stochastic U=0.724528。它满足 persistent、deterministic utility 和 stochastic utility 的绝对门，但 short 未达到 0.65，而 deterministic final-minus-zero utility CI95 仅为 [0.048381, 0.070475, 0.093140]，其下界远低于要求的 0.15。因此 direct_access_pass=false 不是边缘性判定。

其零步 deterministic utility 已经是 0.692952，主要由 P=0.888184 支撑。这意味着 C3 的最终高 utility 不能单独证明强学习访问；注册的增量门正是在防止这种高初始值被误作训练成功。

第二，carrier 可达不等于 direct learner 已获得访问。
构造式 routing controller 能完成任务，random control 也非完全退化；这验证了环境状态机和奖励可达性，却不能替代注册的普通 recurrent learner access。Stage B 在旧 Generic-SHORT carrier 上的正结果也不能代替同一 spatial carrier 上的 C3。F0/F1 合同明确规定 direct access 是后续层级归因的前置条件。

第三，精确的 Iteration 5 C1 objective 没有形成 material executable semantics。
参考折选出的 skill pair 1–2 在 inference fold 上：

action-TV CI95：[0.010141, 0.011219, 0.012263]；

forced process-effect distance CI95：[0.002604, 0.014579, 0.033543]。

两个上界都低于登记 materiality floor 1/12≈0.083333。虽然两种 skill 的自然占比分别约为 0.3974 和 0.3123，但频繁使用不能替代可执行差异。

自然到 forced centroid 的 overlap-margin CI95 为 [-0.017526, 0.006318, 0.031485]，context/mask-matched shuffled-label residual CI95 为 [-0.002999, 0.008867, 0.021149]，两者下界均未超过零。因此弱自然关联不能排除 context、mask 或起点混杂。

第四，C1-on 确实改变了学习轨迹，但不能据此声称语义成功。
C1-on minus C1-off deterministic utility CI95 为 [0.037862, 0.044495, 0.051137]，C1-on final-minus-zero CI95 为 [0.116801, 0.129700, 0.143148]。这是有效的注册内数值处理效应；但 semantic_pass=false、task_access_pass=false、direct_access_pass=false。最保守解释是 intrinsic 改变了低层优化和状态分布，而不是它创建了可复用过程语义。

不能推断的事项

由于同 carrier 的 direct-access 前提失败，本轮不能推断：

C1 相对于强普通 recurrent MARL 是否有任务价值；

hierarchy 在最终目标上必要或不必要；

原始 q_d/q_D、team latent 或 fixed-N HMASD 的哪个组件造成 R41B 成功；

当前失败是高层 assignment、SMDP credit、event context、离散 skill 接口还是低层 executor 干扰所致；

C1-on/off utility 差异能否迁移到未见 roster、未见 lifetime 或最终 UAV 能力；

增加 timing、更多 seed、更多预算、更大模型或改变窗口能否“救活”本路线。

R41B 只建立了固定 N、单 seed、原始完整源的正向 anchor：约 2,998,400 步、每条优化路径 14,055 次更新，最终 win/key0/key1 为 0.89/0.97/0.92。它不是对 q_d、q_D 或 hierarchy 必要性的消融。

Iteration 5 的 seed、预算、reward、task、模型、三 skill、12-active-step window、审计和阈值均保持关闭；下面的候选是新因果解释或替换架构，不是 Iteration 5 的重跑分支。

2. Two-to-four-candidate causal portfolio

以下 A–D 是并列的可证伪解释，编号不表示排序，也不预选唯一继任者。

Candidate A — 访问条件与证据 substrate 不匹配

机制

Iteration 5 spatial carrier 的 zero-step persistent 表现很高，而 direct learner 的主要缺口集中在 short duty 和 final-minus-zero 增量。该 substrate 因此可以验证状态机可达性，却没有为架构比较提供足够的普通学习访问余量。层级、语义和 direct 的差异被一个上游 access bottleneck 截断。

替换对象不是 policy module，而是证据架构：任何下一次层级比较必须先在同一新 carrier 上让 active-set direct recurrent control 独立清除预注册 access gate。

因果 estimand

Δ
access
	​

=U
final
direct
	​

−U
zero
direct
	​


连同 persistent、short 的绝对 access floors；所有指标均在同一预注册 carrier、同一 observation/reward、exact-final checkpoint 上读取。

预测观察

构造式和 random controls 首先确认环境非退化；

direct recurrent learner 在相同 carrier 上以严格正 margin 清除 persistent、short、utility 和 learning-gain 门；

此后 B、C、D 才变得可识别。

最强反证

若一个独立预注册、direct-access 已通过的 carrier 上仍重复出现：skill token 有占比、但 same-snapshot action/process effect 很小、自然 overlap 对 nuisance null 不稳，则 carrier mismatch 只能解释 Iteration 5 的归因失败，不能解释 skill bottleneck 本身。

置信度

对“Iteration 5 的算法比较未识别”为高；对“换成另一个合格 substrate 后 hierarchical semantics 会出现”为低至中。

Candidate B — 共享低层执行器的 skill interference；用离散过程基元替换 FiLM 弱条件化

机制

当前低层主要依赖共享 recurrent actor 加 skill conditioning。不同 z 共享绝大多数动态和 action head，可能在 task credit、mixed-age segment 和 membership churn 下收敛到近同一闭环行为。一个 posterior scalar 即使非零，也只能推动一个缺乏结构分隔的执行器。

替换架构是一个互斥的离散过程基元执行器：

保留三个 skill；

保留共享 observation trunk；

由 z 选择三个低秩、参数受限的 recurrent transition/action adapter 之一；

每次只执行一个 adapter，不再把其堆在现有 FiLM 与 posterior 之上；

高层仍只通过 external task return 学习 assignment；

第一证据门不要求新的 intrinsic reward。

这把“skill 是什么”写入低层闭环状态转移的参数化，而不是期望一个分类 reward 在完全共享的执行器中自行产生模式。

因果 estimand

在同一 access-valid carrier、同一高层/信用/数据合同下：

Δ
B
	​

=stable-process-separation
factorized
	​

−stable-process-separation
shared
	​


其中 separation 必须同时包含：

same-snapshot action distribution；

fixed-active-time process consequence；

held-out lifecycle、membership stratum、active-age stratum 的稳定性；

自然执行 overlap。

预测观察

两个以上自然占比充分的 skill 在 same-snapshot 条件下产生 material action 和 process separation；

分离在 ordinary、join、rejoin 和 survivor strata 中不反向；

自然 segment 落入对应 forced process 区域；

不需要角色、任务阶段或 reward 字段。

最强反证

在平衡 exposure、明确非零 adapter gradient 和严格 checkpoint 后，三个 adapter 仍产生近同分布行为；或者分离只存在于 adapter 参数而不出现在环境过程。这将否定“共享执行器 interference 是主要原因”。

置信度

中。现有证据证明 shared executor 的 z 影响过小，但没有直接证明参数分隔可以创建有用过程基元。

Candidate C — 硬 categorical skill 是错误接口；改为同三基底的 simplex process command

机制

动态团队中的有用执行可能不是三个互斥角色，而是 persistent/reactive/relocation 等过程成分的不同混合。硬 z∈{0,1,2} 迫使 mixed-age、不同位置和不同 roster context 共用一个离散标签，容易出现 aliasing。

替换接口：

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


仍只有三个共享 process basis，不通过增加 skill 数量救路线；

event action 为 KEEP 或 SET(w)；

w 在连续 active execution 中保持；

low actor 接收 composed command c_i，而不是 categorical embedding；

没有 duration head、learned hazard 或第二 controller。

这是 B 的替代方案，而不是 B 上再加一层 composition。

因果 estimand

在相同三个 basis、容量和 exposure 下：

Δ
C
	​

=heldout process controllability/generalization
simplex
	​

−same
one-hot
	​


重点是未见 roster、未见起点和 membership-event stratum，而不是训练内 utility。

预测观察

学到的 w 不全部坍缩到 simplex 顶点；

中间混合在过程空间中产生可预测插值；

对 persistent 与 short 需要的行为可在同一 basis 上连续调节；

rejoin 后恢复 command 时，不需要把成员硬归为固定角色。

最强反证

若 w 几乎总在顶点、连续混合不产生新的过程区域，或 one-hot B 在所有 held-out 条件下等价，则连续接口只是装饰性重参数化。

置信度

中低。相对/组成表示有理论动机，但当前仓库没有证明离散度本身是瓶颈。

Candidate D — hierarchy-null：active-set direct recurrent MARL 已足够

机制

共享 recurrent policy 可以通过 ordinary observation、active-set context 和自身 hidden state直接实现持续与响应行为。所谓“skill lifetime”可能只是 recurrent control 的内部状态，而不需要一个可干预、可命名的 bottleneck。Iteration 5 的层级失败与旧 Stage B direct success 均与此解释相容，但本轮同-carrier direct gate 失败，所以尚不能将其提升为最终结论。

因果 estimand

在一个 direct-access 已通过、负载能力明确的 carrier 上：

Δ
D
	​

=U
verified hierarchy
	​

−U
matched direct recurrent
	​


并在未见 membership schedule、未见 active lifetime 和相同参数/信息预算下读取 transfer 与 sample efficiency。

预测观察

direct recurrent policy 匹配或超过层级 policy；

去掉 high、skill 和 intrinsic 后性能、transfer 不下降；

层级中任何 skill decodability 都不带来负载能力增益。

最强反证

一个具有 nuisance-resistant、自然执行语义的 hierarchy，在同信息、同训练预算和同 carrier 上，对未见 roster/lifetime 给出 material external-utility 或样本效率优势。

置信度

中高，但不是 verdict；同-carrier access 失败正是阻止其成为唯一结论的原因。

3. Replacement and simplification ledger

四个候选是互斥或串行检验的替换，不应组装成 “factorized adapter + simplex + graph + posterior + learned scheduler” 的模块菜单。

Candidate	Retained	Deleted	Replaced	Added
A — access-valid evidence substrate	typed membership spine、active-only execution、survivor/rejoin continuity、terminal external objective、strict direct baseline	精确 Iteration 5 spatial carrier 作为算法比较 substrate；其 C1-on/off promotion claim	carrier/evidence contract，而非 learner	仅一个先于 hierarchy 的同-carrier direct-access gate；无算法模块
B — discrete process-basis executor	K=3、KEEP/SET、event credit、shared observation trunk、decentralized low execution	Iteration 5 posterior reward作为语义生成器；shared FiLM 是唯一 skill 分隔的设计	低层 recurrent transition/action conditioning	三个互斥低秩 process adapters；不是在旧 actor 上叠第二 controller
C — simplex process command	三个 process bases、active lifecycle、event opportunity、low recurrence、external reward	hard categorical skill embedding、categorical SET head	z 替换为 simplex command w；low actor消费组合 process command	exact continuous action density、存储的 command 状态及其 checkpoint 字段；不增加 duration/timing head
D — direct recurrent MARL	dynamic membership state machine、active-set encoder、centralized critic、survivor hidden continuity	high commitment policy、skill bottleneck、semantic learner、event opportunity作为策略决策	hierarchical policy 替换为 active-member primitive AR policy	无新增学习模块

B 与 C 的第一实现不能同时存在。若把 B 的离散 adapters、C 的 mixture、Iteration 5 posterior 和一个 learned hazard 一并启用，就无法再确定哪条因果边产生结果，违反“replace before accumulate”原则。

4. Intrinsic-reward and ordinary-MARL boundary
可保留的 q_d/q_D 语义边界

原始 individual q_d 的核心思想可以作为允许的语义定义继续存在：

skill semantic evidence≈I(z
i
	​

;X
i,1:L
local process
	​

∣C
i
start
	​

,M
i
	​

,L)

但这不授权复用 Iteration 5 的精确 posterior、窗口或 reward。任何未来语义信号必须满足：

只读取 focal member 在 active steps 上的 task-neutral physical/process consequences；

start observation、hidden、mask、window length 只能作为 nuisance/context null；

不读取 external reward、return、persistent owner、wave progress、success、contact、task phase、role label、future membership；

不读取 lifecycle key、membership epoch、roster slot 或永久 identity；

不按 duration 放大；duration-scaled MI 会把“活得久”混入“语义强”；

score 最多进入所属 segment 的 low credit，不进入 high/event return；

forced branches只可审计，不能成为 reward、advantage 或 policy gradient。

Iteration 4 已明确拒绝把 primitive action one-hot、raw observation delta、actor hidden 或现有 task bookkeeping 当作正 process view；这些路径会分别退化为 R29 action information、任务字段泄漏或标签可解码但不可执行。

默认 q_D/team-code reward 不应保留。运行时 variable membership 和 mixed-age segments 没有一个自然、单一的 team-code event owner；原 event architecture 也已经删除默认 global team latent、bridge 和 q_D。恢复它需要新的独立因果证据，不能由 R41B 正例倒推。

各候选的 intrinsic 边界

**A：**不使用 intrinsic。它只判断 substrate 是否允许普通 learner 获得访问。

**B：**首个区分性证据不需要 intrinsic；skill-specific process adapter 本身是替换架构。后续若读取 q_d，它只是 segment-local 审计或 low-only task-neutral objective，不能再次把精确 Iteration 5 score注入旧 shared executor。

**C：**可以完全 external-reward-only。若需要 semantic audit，审计对象是 command-to-process controllability，不是给 mixture 权重付 intrinsic 奖励。

**D：**intrinsic 恒为零。

最强 ordinary-MARL objection

**Against A：**一个更易访问的 carrier 只说明 direct learner 能学，不说明 skills 有价值；A 本身不是层级证据。

**Against B：**skill-specific adapters 可能只是把参数分成三份。容量匹配的 direct recurrent actor可能学到同样闭环过程，因此 B 必须证明 reuse、intervention 或 transfer，而非仅证明参数不同。

**Against C：**simplex command 可能只是给 recurrent policy 增加一个冗余 latent；direct hidden state可以内部模拟该连续量。只有可控、可复用且带负载能力增益的 composition 才能反驳。

**Against D：**D 是最强 ordinary-MARL reduction。它只能被同-carrier、同信息、同预算、语义已验证的 hierarchy 直接击败，而不能被 label entropy、posterior accuracy 或 forced effect 单独击败。

5. Variable membership and lifetime semantics

这些语义是候选 B/C 的硬约束，也是 A 所选择的新 substrate 必须继承的 spine。D 保留 membership spine，但没有 high event。

Membership masks 与状态所有权

只有 ACTIVE lifecycle 产生 primitive action。

policy opportunity frontier 只能包含 active member。

temporary/terminal leaver 在离开后不能产生 actor row。

routing key 和 membership epoch 只用于精确定位、拒绝 stale row；不得进入网络。

active-set aggregation只处理当前 active tokens，不得用 dummy slot 伪造成员。

JOIN

Genuine join：

h_low = 0
h_high = 0
skill/command = undefined
active age = 0
immediate opportunity
legal action = SET only

它不能选择 KEEP，也不能继承同物理标签的旧 lifecycle 状态。

Temporary LEAVE

在 post-primitive、pre-removal snapshot 上：

关闭 low recurrent chunk；

关闭 semantic segment；

关闭 owner event trace并做 critic-only truncation；

保存旧 policy-version value；

冻结 recurrent state、skill/command、active age和 opportunity gap；

absence 不累积 skill lifetime、不分配 inactive reward；

所有 survivors 的 hidden、skill、age和 trace连续。

REJOIN

同一 lifecycle key恢复，但 membership_epoch += 1：

恢复 h、skill/command和 active age；

获得新的 policy opportunity；

从恢复状态开启新的 low chunk、event trace和 semantic segment；

不能把 leave interval 与 rejoin 后 segment 拼成一个 posterior window。

Terminal LEAVE

所有 open trace以零 bootstrap 关闭；

row finalization 后删除 recurrent、skill/command状态；

后续复用同物理标签必须建立新 opaque lifecycle。

Physical time 与 event time

对 high/event owner：

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

+r)

非终止边界 bootstrap 为：

γ
Δ
i,n
	​

V
i
	​

(C
t
i,n+1
	​

	​

)

gamma 按真实 primitive time 流逝；lambda 只跨同一 owner 的连续 policy events。其他成员的事件、silent primitive steps 和外部 membership 事件都不能制造该 owner 的 actor ratio。

对 low policy：

credit 沿 focal active primitive steps；

temporary absence 不推进；

semantic score只分配给所属 active rows；

update boundary不能让 actor或 semantic row跨 policy version。

Lifetime 是连续 KEEP 之间累计的 active execution time，不是 duration catalogue，也不是 wall-clock residence time。

Probability factors

B：

p=q(σ
t
	​

∣F
t
	​

)
j∈F
t
	​

∏
	​

π
H
	​

(e
i
j
	​

	​

∣C
t
(j−1)
	​

,m
j
	​

)
i∈A
t
	​

∏
	​

π
L
	​

(a
i
	​

∣o
i
	​

,h
i
	​

,z
i
	​

)

外部 order q、membership event和 opportunity schedule均无 policy gradient；只有实际 commitment token 与 primitive action有行为似然。

C：

SET(w) 必须保存实际连续 sample、pre-transform 参数、exact transformed density及 Jacobian。不得先采样后投影 simplex、不得用未记录的 conflict repair；KEEP 与 SET(w) 必须处于一个完整概率合同中。

D：

只有 active-member primitive autoregressive factors；没有 high、KEEP/SET、survival或 semantic likelihood。

Checkpoint

所有可行候选必须保存：

architecture mode与 schema；

policy、critic、optimizer、normalizer；

lifecycle table和 membership epochs；

survivor recurrent states；

active skill或 simplex command及 active age；

event opportunity RNG和 frontier-order RNG；

open event traces与 policy version；

collector active presentation、pending transaction和 command-response state；

worker environment snapshot和 environment RNG；

exact current observation/state boundary。

B 还需保存 adapter state及任何语义审计状态；C 需保存 continuous command state和密度参数。缺少任一 live-runtime 状态时必须 hard fail，不能 reset-and-continue。

Decentralized execution

low actor只能读取：

自身 ordinary observation；

自身 recurrent state；

自身 skill或 process command。

它不能读取 centralized critic、routing identity、future membership、team role、task oracle或其他成员的永久槽位。高层 active-set context不自动成为低层输入。

6. Literature-derived principles, not modules

文献提供的是约束和设计原则，不是可拼装的 successor stack。

Active-set、置换兼容不等于 episode 内 variable membership

跨固定 N 复用共享图权重说明参数不必绑定成员槽位；但固定 runner、固定 buffer和固定 agent list不定义 join、temporary leave、rejoin、survivor hidden continuity或 leave bootstrap。下一架构可以吸收 active-only shared-token 与 permutation-safe aggregation原则，不能直接移植固定-shape rollout。

Population summary 必须保留 mass 与 rare-critical information

纯 mean/field 会把相同归一化分布但不同绝对人数映射到相同表示，并抹去关键中继或低电量个体。可迁移原则是：任何固定维摘要至少保留 log(1+N) 或 mass；只有在实际信息缺失被证明后，才考虑 bounded exact residual。当前 B/C 都不需要先增加该结构。

Sparse interaction必须从稀疏候选开始

有界邻域和小直径通信是有用复杂度原则；但固定环形 ID、同步全局轮换时钟和旧邻居 message memory与 roster churn 不兼容。不能先形成所有 N² pair score再 Top-L，也不能把通信辅助目标顺带加入 skill gate。

每成员 readiness 可吸收，固定 buffer 与一步 return 不可吸收

独立 readiness和掉队压力测试支持 per-member event execution；但启动时固定 num_agents 的 control/buffer不支持真正 join/rejoin，而且一步 gamma 未按实际 duration 折扣。可迁移的是事件化执行概念，不是其 return或 collector。

gamma 属于物理时间，lambda 属于事件深度

agent-centric event history和 gamma^{\Delta t} 是当前最直接的时间原则。它与仓库 event contract一致，但固定 roster centralized shell不可迁移。连续时间工作进一步支持 duration 必须进入 value target，却不支持共享 Δt、PINN/HJB/VGI 整栈或固定 joint state。

Many-agent 容量不是 runtime roster semantics

能处理上千固定顺序 agents 的 sequence model是将来的吞吐/显存对照，不是当前 join/leave答案；固定 T×N flatten 还会让成员删除改变 token phase和 hidden ownership。容量优化必须晚于 roster semantics与表示必要性证据。

相对过程表示可作诊断，同步 joint option 不可迁移

相对 displacement、spread或 dispersion 可以帮助检查过程压缩是否 alias；但全员投票、共同执行和共同终止会重新引入最慢成员 barrier，与 heterogeneous T_i 直接冲突。它们不能成为 B/C 的默认 option system或 intrinsic reward。

总原则是：

active lifecycle ownership
+ exact event-time credit
+ task-neutral local process semantics
+ direct recurrent null

而不是：

graph + retention + communication + mean field
+ option discovery + continuous-time model

后者是无法归因的模块堆栈。现有综述同样指出，没有一篇文献完整实现 episode 内 join/leave/rejoin、survivor continuity和正确 on-policy roster semantics。

7. Retired-line exclusion
R29 action-information family

没有候选用：

sampled primitive action likelihood ratio；

same-action counterfactual skill mixture；

terminal-window action density；

action one-hot 作为 semantic positive view。

B 的区分来自执行器状态转移参数化；C 来自 process-command composition；forced action/process读数仅是审计。R29 的在线 reward 已因 transfer 与 task safety 失败退休。

R31-CFEI

没有候选把 observational posterior 或 forced-effect statistic转成 intrinsic reward。R31 已表明自然关联可以很强，而 forced between/within ratio仍不超过执行噪声；因此 B/C 必须先建立可执行过程，而不是重新训练 effect classifier。

R32-IFEPG

没有候选用 intervention score直接对低层 FiLM、adapter或 action head做 policy gradient。Forced branches保持 audit-only；B 的 adapters若学习，只通过其单独注册的普通 low objective或 external task credit，不通过 R32 effect advantage。R32 已产生小但不足的 separation shift且无自然 transport。

R33-IRSC

没有 complete-roster enumeration、pair complementarity score、roster-pair sham或 head-only expected-score update。B/C 是个体过程接口；它们不学习“哪对 skills 应共同出现”的 intervention reward。R33 的 exact line已经因极小 heldout alignment和零 natural transport退休。

Task-shaped route

任何候选都禁止把：

persistent owner；

wave target或wave progress；

short completion；

success/contact；

task phase；

external reward/return

改名为 intrinsic。A/D 没有 intrinsic；B/C 的 process evidence只能来自 focal physical consequence。

Identity route

lifecycle key与epoch仅用于 routing、row ownership和 stale-row rejection。没有 agent ID、固定 slot、永久 order、role label或 identity embedding。

Scheduler-only route

A改变证据 substrate；B改变 low executor；C改变 skill command接口；D删除 hierarchy。它们都不是“保留原算法，只改变什么时候 SET”。机会仍是外生、exchangeable且 task-independent。没有 learned event hazard或termination policy。

Duration-catalogue route

B/C 的 lifetime均为连续 KEEP 所实现的 active-time run length。没有离散 (1,2,3,4,...) duration action、duration reward、age-conditioned semantic payment或 survival likelihood。只有未来真正学习 event time时才需要 hazard/survival/censoring概率；该路线当前不在 portfolio。

Iteration 5 rescue exclusion

Candidate A 不是修改 Iteration 5 carrier；它要求另建、另注册证据源，并永久保留本轮 terminal status。B/C 也不是在本轮上更换 window、skill count、seed、阈值或 posterior容量后重跑。精确 Iteration 5 三臂全部关闭。

8. Next-evidence candidates

以下顺序是逻辑依赖，不是对 B、C、D 的排名。每项都需要新的独立注册和授权；本审阅不授权实现或训练。

Evidence Source E1 — 同-carrier direct-access qualification

Comparator

routing-only constructive controller；

uniform random control；

architecture-matched active-set direct recurrent policy；

不含 high、skill或 intrinsic。

应使用一个与最终 membership/lifetime spine一致、但不是 Iteration 5 精确 spatial carrier的新合同。

Estimand

direct final-minus-zero external utility；

persistent、short和total utility 的绝对 floors；

deterministic与stochastic exact-final checkpoint；

paired episode uncertainty。

Outcome branches

Controls 与 direct 均通过：
A 被解析为 Iteration 5 特定 substrate 归因问题；B、C、D获得可识别测试入口。

Controls 通过、direct 失败：
仍是 access/observation/optimization问题；B/C暂停，D也未获支持。

Constructive 或 random calibration 失败：
新 carrier无效，不读取 learner结果。

实现 M0 失败：
只修具体 wiring defect。

Portfolio update

所有候选都更新：E1 不支持任何 hierarchy，但决定 B/C/D 是否可科学比较。

Prohibited rescues

结果后不得改变 observation、reward、horizon、budget、seed、threshold、optimizer、best checkpoint或引入 shaping/intrinsic。

Implementation boundary

只允许先冻结 environment、ledger、observation、direct learner、概率、checkpoint和分支合同；不能由本审阅直接启动。

Evidence Source E2 — executor/interface realizability gate

仅在 E1 direct-access 通过后开放。它不是任务 efficacy 实验，而是检查 B/C 是否能建立可执行 process command。

Comparator

在同一 access-valid carrier和同一 task-neutral local process channel上，使用预注册、平衡、外生的三基底 command ledger，比较：

shared-conditioning reference；

B 的 hard one-hot factorized process executor；

C 的 simplex-composed executor。

保持三个 basis、12-active-step read、相同起点/ledger和相近参数预算。高层 assignment关闭；external task fields不进入 command objective。

Estimand

held-out command-to-action TV；

paired process-effect distance；

same-command within-replica noise；

join、ordinary、rejoin、active-age strata中的方向稳定性；

temporary leave前后恢复同一 command的连续性；

nuisance-matched context/null残差。

这是executor positive control，不是 natural assignment或任务优势证明。

Outcome branches

B 通过、shared失败：
executor interference explanation上升；C仍可活，但不再是必要解释。

只有 C 通过：
hard categorical interface被反驳，C上升，B退休或降为 one-hot special case。

B 与 C 都通过：
executor可实现；下一问题是自然 assignment和负载价值，D仍保留。

三者都失败：
B/C的 process-command family大幅降权；A或更基础的 actuation/observation问题上升。

shared也通过：
Iteration 5 的主要失败更可能来自其学习压力或 carrier，而非 executor参数化；精确 posterior仍不重开。

Portfolio update

E2 同时区分 B 与 C，也更新 A 和 D：仅有 command controllability而无后续任务优势时，D不受削弱。

Prohibited rescues

不得在结果后改变三 basis、window、process view、command ledger、adapter rank、simplex temperature、训练 exposure、seed或materiality门；不得加入 task reward、role labels、R29/R31/R32/R33 score。

Implementation boundary

必须先把它登记为 diagnostic-only process gate；不进入正常 trainer、不更新高层、不声称 task improvement。

Evidence Source E3 — load-bearing hierarchy-versus-direct gate

仅当 E1 已建立 direct access，且 E2 至少有一个 executor/interface通过时开放。

Comparator

matched active-set direct recurrent MARL；

每个 E2 存活的 hierarchical candidate分别作为独立 arm；

相同 actor-visible information、external reward、environment ledgers、training exposure、checkpoint选择规则和 centralized critic能力；

已验证的 process executor/interface在比较前固定其合同，不能边比较边加入新语义模块。

Primary estimand

ΔU
heldout
	​

=U
hierarchy
	​

−U
direct
	​


在预注册的未见 membership schedule和未见 active-lifetime distribution上读取。训练内 label classification或forced effect不是 primary outcome。

Outcome branches

Hierarchy external utility/transfer materially优于 direct，且语义保持：
D下降；对应 B或C满足进入独立 integration review的必要条件。

Direct noninferior或更优：
D上升；B/C最多保留为可解释 process abstraction，不应集成到最终 learner。

Hierarchy utility提高但语义坍缩：
不得归因为 reusable skills；检查是否只是容量、优化或任务 shortcut。

两类方法都失去访问：
该 carrier不能承担负载比较，停止该证据源；不能通过更多 seed或 shaping救援。

稳定 executor存在，但自然 assignment失败：
才允许重新打开独立的 assignment/SMDP-credit问题；这不是 credit成功。

Portfolio update

这是第一个能实质削弱 D 或支持层级 integration 的证据。E2 的 process success单独不够。

Prohibited rescues

不得修改 reward、任务、预算、seed、模型容量、event schedule、threshold、best checkpoint；不得在失败后增加 learned timing、team latent、graph、communication或task-shaped intrinsic。

Implementation boundary

本轮不授权 E3。它必须等待 E1/E2 的已归档终局结果，并有单独的 comparator、概率、credit和checkpoint审阅。

9. Portfolio stop and integration conditions
Candidate A

解析或退休条件

一个预注册新 carrier上，constructive/random calibration和direct recurrent access都清晰通过：A作为“Iteration 5 特定 substrate问题”被解析，不再是后续算法候选。

若有限数量、预先声明的 carrier连续出现 controls通过但direct access失败，应停止 carrier搜索，回到 observability、objective和普通 learner合同；不得无限制造新 toy。

可合并条件

若 E1 通过后 direct继续在所有 load-bearing测试中占优，A与D合并为“access-first ordinary-MARL研究路径”。

Candidate B

退休条件

factorized adapters在 E2 中有非零梯度和参数变化，却没有 material、nuisance-resistant process separation；

separation只存在于参数或 action logits，不进入环境 consequence；

process realizability通过，但 E3 中相对于 direct无任何 transfer、utility或sample-efficiency价值。

合并条件

若 C 的 simplex command在训练和测试中始终坍缩为 one-hot顶点，并与 B 的三个 adapters等价，C应并入 B，而不是保留两个名字。

进入 integration 的必要条件

B 必须同时具备：

same-snapshot可执行差异；

跨 lifecycle/event strata稳定；

自然 assignment overlap；

未见 roster/lifetime上的负载能力优势；

无 task-shaped semantic signal。

Candidate C

退休条件

mixture权重长期位于 simplex顶点；

中间 command没有可预测的过程插值；

one-hot B 在所有 held-out条件下等价；

mixture只增加 policy entropy或容量，却没有 intervention/reuse/transfer价值。

合并条件

若 C 只在极少数 context使用非顶点组合，而其有效 process law可由 B 的有限 basis直接表示，则并入 B；不得为了保留 C 而增加 basis数量或温度调参。

进入 integration 的必要条件

除 B 的通用条件外，还必须证明 composition本身是 load-bearing，而非装饰性 latent。

Candidate D

退休条件

只有以下联合证据可以退休 D：

同-carrier direct access已通过；

hierarchical executor具有 shortcut-resistant、自然执行语义；

information、critic、预算和checkpoint选择匹配；

hierarchy在未见 membership/lifetime上提供 material external-utility或sample-efficiency优势。

仅有 posterior accuracy、label occupancy、forced effect或训练内 utility差异都不能退休 D。

集成条件

若 direct recurrent policy满足最终 membership/lifetime能力，而所有语义 hierarchy都没有负载优势，D应成为集成基线或最终实现；不保留无证据的 high/skill/intrinsic路径。

Whole-portfolio stop

整个 hierarchy/process-skill line应在以下任一条件下停止：

E1 无法建立普通 direct access。
问题仍在 substrate、信息或 ordinary optimization；继续研究 skill算法没有识别力。

E1 通过，但 B/C 均无法产生稳定可执行 process commands。
停止当前三基底、event-owned process-skill family，不通过新 posterior、更多窗口、更多 skill或新 reward复活。

B/C 形成语义，但 E3 中 direct noninferior。
语义存在但不是 load-bearing能力；停止层级集成。

任何唯一看似成功的路线需要 task field、identity、role、learned scheduler、duration catalogue或已退休 effect objective。
该成功不属于目标问题，直接停止。

候选只能通过模块堆叠才工作。
若必须同时增加 team latent、graph、communication、new critic、learned hazard和semantic reward，因果问题已失去可解释性，应停止而不是集成。

Whole-portfolio integration

只有一个候选满足全部条件时，才有资格进入另一次独立 integration decision：

同一 carrier上的强 direct access先通过；

exact probability、mask、credit、replay和checkpoint均有效；

JOIN、temporary leave、REJOIN、terminal leave和survivor continuity逐项成立；

physical-time discount与event-depth trace正确；

semantic segment ownership唯一且不跨 policy version；

process semantics在 same-snapshot、nuisance-matched、natural-overlap三层均成立；

未使用 reward、task progress、role或identity shortcut；

相对于 matched direct recurrent policy，在一个负载能力上有 material优势；

该优势来自一个可说明的替换，而非多个新模块同时激活。

当前结论仍是：Iteration 5 的精确 carrier与精确 C1 objective均已关闭；portfolio未穷尽，但没有任何候选获得实现、训练或集成授权。