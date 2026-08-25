REVIEW_DISPOSITION=MINIMAL_UAV_PACKAGE_CAN_SUPPORT_ORIGINAL_NARRATIVE

EXECUTIVE_JUDGMENT

当前证据尚不能支持 UAV robustness paper，也不足以单独构成一篇有竞争力的机制论文；但一个严格收窄、结论导向的 UAV 验证包可以支持原始叙事。

理由如下：

G31–G49 已经把候选方法从复杂训练链压缩为一个值得运输验证的、较小的 roster-native controller。G46/G48 提供了特定 toy boundary 内的统计性非必要证据，G47/G49 提供了精确功能等价证据。这些是可靠的内部机制筛选结果，但不是 UAV 结果，也不是普适 credit-assignment 理论。

两个既有 UAV source 均未通过绝对可行性门槛，且没有进入 learned-policy comparison。因此目前不存在任何正面的 UAV transport、mission access、failure recovery 或 charging-rotation 学习证据。

“variable agent number”“open team”“graph/set aggregation”“zero-shot transfer to new team compositions”均已有强文献先例。文章不能把共享参数、mask、attention 或变人数本身作为主要 novelty。

仍可能形成新贡献的组合是：
within-episode lifecycle semantics + explicit state ownership + unified planned/unplanned roster interface + absolute service feasibility + held-out roster-process evaluation + tail-aware inference。

所谓“minimal UAV package”不能是一段成功轨迹或一个平均 return 表。它至少需要一个通过 source-identifiability gate 的任务、计划与突发两类事件、重返或替换、未见 team sizes/roster laws、强 variable-agent baseline，以及预声明的绝对服务和尾部风险判据。

因此，当前应把 G49 看作通过 toy-domain 筛选的候选机制，而不是已经获得 UAV robustness 证据的最终算法。



PUBLISHABLE_THESIS_AND_CLAIM_CEILING

建议的一句话论文 thesis

在一个预注册、通过物理可行性和因果可识别性门槛的固定高度 UAV 服务基准中，单一共享的 roster-native decentralized policy 使用 permutation-invariant active-set context 与显式 lifecycle/state ownership，在一个训练队伍规模上学习后，无需按规模重新训练，即可在 held-out team sizes 和 held-out within-episode planned-rotation、dropout/rejoin roster processes 下维持预声明的服务水平并限制恢复损失。

该 thesis 比原候选 claim 更窄，因为它明确限定了：

一个注册任务类别，而不是“UAV systems”；

服务水平和恢复损失，而不是不加限定的“robustness”；

测试过的 team-size 和 roster-process support，而不是任意规模或任意过程；

simulated decentralized policy execution，而不是真实系统安全保证。

当前可辩护的 claim ceiling

目前只能声称：

在冻结的 H=48 toy-domain boundaries 内，若干 baseline-derived、realized-successor 和 duplicated-immediate actor-credit components 对注册 access result 并非 load-bearing；其中两个删除或折叠结果在指定投影上具有精确功能等价性。

不能声称：

UAV transport；

system robustness；

fault tolerance in general；

任意 team-size generalization；

arbitrary process-law robustness；

memoryless control generally；

safety、certification 或 operational reliability。

随证据等级变化的上限

证据等级	最大合理表述
当前 toy evidence	“exact registered toy mechanisms”
完成 mandatory simulation matrix	“registered simulated roster-perturbation service robustness”
完成 hardware-in-the-loop	“real-time executable under the tested autopilot, latency and dynamics envelope”
完成真实小型机队试验	“demonstrated on the specified platform and operating envelope”
任何上述等级	均不能推出 safety certification、任意故障容忍或通用 UAV resilience

“System robustness”现在过宽。建议使用：

roster-perturbation service robustness over a registered process class

其操作定义必须同时包含 absolute access、event-window loss、recovery 和 tail risk。



CURRENT_EVIDENCE_AUDIT

证据	科学状态	允许推论	禁止推论
离散 dynamic-roster chain	Demonstrated result，toy only	实现语义可承受高频 churn、replacement 和 count shock	UAV applicability
Continuous-service toy controller	Demonstrated result，toy only	lifecycle state、active-set aggregation 与直接 demand path 可形成可用控制	物理 UAV transport
G31–G39、训练 capacity 8，评估 6/8/12	Demonstrated result，限 H=48 注册 family	在该固定 source family 中存在跨容量 transfer；actor 不需要若干历史附加量	arbitrary N、其他 horizon、其他 roster laws
G46	Registered statistical noninferiority	baseline-derived scalar credit-norm schedule 在该 post-anchor path 中不 load-bearing	baseline 全局无用、credit 普遍等价
G47	Technically validated exact mechanism	matched shadow baseline module 可从指定 route 结构删除	新的统计性能结果或 UAV 结论
G48	Registered channel attribution	realized-successor package 对 frozen comparator 无注册 material advantage	successor information 在其他任务无用
G49	Technically validated exact collapse	duplicated equal-mean package 可精确折叠为 single normalized immediate channel	single-immediate route 对所有任务都充分
G50	Unresolved	无	不能假设 anchor 必要或不必要
UAV G1/G2	Negative source-development evidence	已有 source/controller 未达到可行性；proactive rotation 在 G2 中行为上有作用	算法被 UAV 数据否定，或已获得正面 transport 证据

综合判断：

Demonstrated result： 仅覆盖冻结 toy families。

Technically validated mechanism： G47、G49 的精确删除/折叠。

Plausible hypothesis： representation、active-set semantics 与 state ownership 可能比复杂 credit path 更关键。

Proposed experiment： UAV source-identifiability 与 transport matrix。

Unsupported claim： UAV robustness、system robustness、通用 memorylessness、任意队伍规模泛化。

G46–G49 是选择最终候选方法的充分依据，但不是把“简化方法”本身包装为普适算法突破的充分依据。



HYPOTHESIS_AUDIT

假设	当前分类	审查意见	最小 falsifying experiment
H1 roster-native transport	Plausible but untested；toy 层面 partial support	跨 6/8/12 toy capacity 不能替代 UAV within-episode transport	在已通过 source gate 的 UAV task 上仅用 N=8 训练；若在预声明的 moderate、feasible N=6 或 N=12 held-out failure/rotation cell 中，absolute-access lower CI 未达门槛，H1 在注册范围内被否证
H2 unified planned/unplanned handling	Plausible but untested	统一 lifecycle interface 合理，但 planned event 含 anticipation，unexpected failure 含 detection delay；二者信息结构不同	matched-budget unified policy 与两个 event-specific policies 比较；若 unified policy 在任一事件族不能达到预声明 noninferiority，而 specialized policy 能达到，则统一架构主张被否证
H3 representation dominates credit complexity	Partially supported，toy-bound	G46–G49 只说明特定 credit components 未负载 toy access，不说明 representation 是因果主导因素	进行 roster representation × credit route 的小型 factorial；若恢复复杂 credit 明显改善 UAV primary endpoints，而破坏 lifecycle/active-set representation 不造成 material degradation，则 H3 被否证
H4 current-state sufficiency	Partially supported within the registered observability contract	只能在 current observation 足以 Markovize 决策时成立	在相同 observation contract、capacity 和 training budget 下，RNN 若在 primary cells 超过预声明 superiority margin，则 current-state sufficiency 被否证；这不能外推到人为制造的 partial observability
H5 anchor necessity is an optimization-path question	Plausible but untested	问题本身合理，G50 尚无 scientific result	fresh-G49、anchor-G49、以及额外 optimizer-exposure control 三臂比较；若 anchor advantage 被纯训练步数 control 吸收，则“curriculum/anchor mechanism”解释被否证
H6 robustness requires a matrix	Poorly posed as an empirical hypothesis	这是评价设计原则，不是可直接证伪的算法假设	改写为：“方法在预声明 event families、severity、size 和 process-law matrix 上同时满足 access、recovery 与 tail margins”；任一 primary gate 失败即否证
H7 source feasibility precedes comparison	Currently supported as a logical requirement	这是因果可识别性的先决条件，而非算法性能假设	若 no-reallocation 已能满足 SLA，则 roster adaptation 不是必要因果因素；若 oracle/constructive controller 也不能满足 SLA，则 source 无效，而不是算法被否证



NOVELTY_AND_PRIMARY_LITERATURE

已知内容及其对 novelty 的限制

Dynamic/open team composition 已有直接先例。 COPA 在 ICML 2021 研究成员加入/离开和未见 team compositions；GPL 在 ICML 2021/JMLR 2023 研究可随时间进入和离开的 open teams；CIAO 与 NAHT 又分别扩展了 open ad hoc teamwork 和多个受控代理的动态队伍。因而“within-episode count changes”本身不能作为首创。

Graph、attention、mean-field 和 permutation-invariant aggregation 已是成熟 scalable-MARL 路径。 InforMARL 使用图聚合实现不同 agent counts 的 transfer；mean-field MARL 用总体或邻域平均效应近似大规模交互。仅使用 pooling、attention 或 local-neighbor graph 不构成足够 novelty。

UAV 长期覆盖、energy-aware navigation 与 charging-aware routing 已有同行评审文献。 因而 energy、charging station 或 coverage objective 也不能独立承担 novelty。

Fault-tolerant UAV MARL 亦非空白。 已有工作处理 UAV/UGV coverage fault tolerance，另有 attention-based fault-tolerant MARL preprint；2026 年 TAG-MAPPO preprint 更直接研究 UAV node failure、dynamic graph 和 coverage recovery。

最相关 primary papers

编号	文献与状态	与本项目的关系
[1] COPA: Coach-Player MARL for Dynamic Team Composition, ICML 2021，同行评审	直接覆盖 join/leave 与 unseen team composition；但依赖 global coach，和纯 roster-native decentralized execution 不同。
[2] Towards Open Ad Hoc Teamwork Using GPL, ICML 2021，同行评审	open teams 可在任意时间进入/离开；GNN 处理 variable input size，是直接 novelty collision。
[3] A General Learning Framework for Open Ad Hoc Teamwork, JMLR 2023，同行评审	完整 GPL framework，包含 partial observability、type inference、agent modelling 与 dynamic membership。
[4] InforMARL, ICML 2023，同行评审	graph information aggregation、local sensing、variable-agent transfer 和 decentralized execution；是最合适的 graph baseline 类。
[5] Open Ad Hoc Teamwork with Cooperative Game Theory, ICML 2024，同行评审	CIAO 对 GPL 的 joint-value representation 给出合作博弈解释；限制“新 credit framing”方面的 novelty。
[6] N-Agent Ad Hoc Teamwork, NeurIPS 2024，同行评审	动态数量与类型的受控/非受控 teammates；表明“shared policy 面向动态数量”已经进入主流 MARL formulation。
[7] K-nearest MARL for a Variable Number of Agents, 公开版本为 preprint；投稿时需另行核验正式 venue	可作为 published-variable-number-style implementation baseline；论文中不得在未核验前称其为同行评审基线。
[8] Mean Field Multi-Agent Reinforcement Learning, ICML 2018，同行评审	提供 scalable population aggregation 先例；但其弱交互/平均场假设可能不适合稀疏 roster shocks。
[9] Towards Fault Tolerance in MARL, 2024 preprint	通过 attention 和 fault-prioritized sampling 提高 fault tolerance；是“attention 或训练采样是否 load-bearing”的直接比较对象。
[10] SERT-DQN UAV–UGV Fault-Tolerant MARL, Drones 2024，同行评审	已使用“fault-tolerant MARL”措辞；项目必须在 lifecycle semantics、held-out roster laws 和 absolute service 方面形成明显区分。
[11] Resilient Topology-Aware Coordination for Dynamic 3D UAV Networks under Node Failure, 2026 preprint	最危险的 novelty collision：dynamic graph、random observation shuffling、node failure、coverage recovery、shared lightweight actors。其当前公开版本未覆盖 planned charging rotation、rejoin/replacement lifecycle ownership、held-out roster-process matrix 或 tail-aware service inference。
[12] Distributed Energy-Efficient Multi-UAV Navigation for Long-Term Communication Coverage, IEEE TMC 2020，同行评审	建立长期通信覆盖、energy-aware decentralized UAV control 的先例。
[13] Deep RL for UAV Routing with Multiple Charging Stations, IEEE TVT 2023，同行评审	charging-aware route construction、attention 和跨实例规模 generalization 已有先例。

仍可能成立的 novelty

最可信的 novelty 不是一种全新的 neural block，而是以下组合：

Roster-process formulation： 同一 episode 内 planned leave、unexpected loss、replacement、rejoin 与 count shock。

Lifecycle/state-ownership semantics： survivor continuity、fresh lifecycle epochs、stale-state exclusion、member-owned stochastic streams。

统一但信息非对称的 interface： planned rotation 有 announcement lead time；unexpected failure 只有 bounded detection delay。

Source-identifiable UAV protocol： 先证明 task 可行且 roster adaptation 因果必要，再比较学习方法。

Tail-aware held-out evaluation： 未见 timing、duration、severity、order、team size 与 compound processes。

负机制结论： 在这一注册 observability contract 中，复杂 credit machinery 或 recurrent carry 未显示为必要——前提是 UAV ablation 复现这一点。

最危险的 novelty collision

TAG-MAPPO 2026 preprint 最接近拟议 UAV 故事。若本项目只做“图或集合策略在一个 UAV 突发失效场景中恢复平均 coverage”，novelty 将非常弱。必须至少在以下三项上形成实质区分：

lifecycle-aware leave/rejoin/replacement，而非单次 vertex removal；

planned 与 unplanned events 共用同一 roster interface；

source-identifiability、absolute SLA、held-out process laws 和 tail-risk inference，而非仅平均恢复曲线。



MINIMUM_IDENTIFIABLE_UAV_BENCHMARK

最小任务选择

建议只做一个主任务：

固定高度 UAV communication-service continuity：多个 UAV 作为移动服务节点，为静态或缓慢变化的地面 demand hotspots 提供连续服务；UAV 因 battery rotation、temporary failure、permanent loss、replacement 或 rejoin 改变 active roster。

该任务比 full coverage-path planning 更适合识别 roster adaptation，因为：

service 是逐时刻可测的；

一架 UAV 离开会产生局部 deficit；

surviving agents 的空间 reallocation 可以直接恢复服务；

planned charging 与 unexpected failure 可共享相同 active-set transition；

不需要把结论混入复杂地图探索、目标发现或未知风场。

状态、观察、动作和服务

全局状态可写为：

[
s_t=\left{
x^i_t,v^i_t,e^i_t,\lambda^i_t,m^i_t
\right}_{i\in\mathcal{R}_t}
\cup D_t\cup C_t,
]

其中：

(x^i_t,v^i_t)：二维位置和速度；

(e^i_t)：state of charge；

(\lambda^i_t)：lifecycle token，仅用于环境 ownership 与审计，不作为 fixed identity embedding；

(m^i_t)：active、departing、inactive、returning 等 roster status；

(D_t)：地面 demand field；

(C_t)：charging/depot capacity 与可用性。

每个 active UAV 的 actor observation 应包含：

native current ego state，例如
((x_i,y_i,v^x_i,v^y_i,e_i,\tau_i^{announce}))；

local demand summary 或低维 demand encoder；

depot-relative features；

unordered active-neighbor set，包括相对位置、速度、SoC 和 announced status；

bounded failure-detection indicator。

不得提供：

fixed agent ID embedding；

lifecycle age 作为隐含身份；

previous action；

actor clock；

rejoin 前遗留 hidden state。

连续动作采用二维 desired velocity 或 acceleration：

[
a^i_t=(a^x_i,a^y_i),\qquad
|v_i|\le v_{\max},\quad
|a_i|\le a_{\max}.
]

低层 attitude control 可由固定 autopilot abstraction 完成。

服务函数

由固定、非学习的 association/scheduling layer 根据 UAV 位置和 link budget 分配服务。定义 hotspot (j) 的满足比例为

[
q_j(t)=\min!\left(1,\frac{y_j(t)}{d_j(t)}\right),
]

总体服务为

[
S_t=
\frac{\sum_j w_j q_j(t)}
{\sum_j w_j},
\qquad 0\le S_t\le1.
]

训练 reward 可为

[
r_t=
-\alpha(1-S_t)
-\beta\sum_i P_i(v_i)
-\gamma C_{\mathrm{collision}}
-\eta C_{\mathrm{reserve}},
]

但论文 primary endpoint 必须使用 (S_t) 和 SLA，不得用 reward 代替 mission service。

最低物理约束

必须包含：

固定高度但有界速度和加速度；

calibrated hover/transit energy model；

回程与安全 reserve energy；

charging/swap depot 的有限占用；

地理边界和最小 separation；

local communication/sensing radius；

planned departure announcement lead time；

unplanned failure 的 bounded heartbeat-detection delay；

inactive UAV 不产生服务或动作。

可保持抽象的内容：

六自由度飞行与 detailed attitude dynamics；

电池化学退化；

复杂 LoS/NLoS ray tracing；

风场和传感器漂移；

完整无线 MAC；

真实 charging hardware。

不能抽象掉：

depot travel time；

energy feasibility；

roster transition timing；

service capacity；

leave/rejoin ownership；

failure-detection delay；

absolute service floor。

Event generator

事件由预注册的 roster process (\mathcal P) 生成：

Planned rotation： 在 (t_e-L) 宣布，(t_e) 离开 active set，充电或维护后重返。

Temporary failure： 无提前通知，在 detection delay 后从 active set 移除，持续 (D) 后 rejoin。

Permanent loss/replacement： 原 source 不重返；replacement 从 depot 以新 source token 和新 lifecycle epoch 加入。

Count shock： 短窗口内 (m\ge2) 个 departure 或 arrival。

Repeated rejoin： 同一 physical member 可重返，但每次获得新 lifecycle epoch；survivors 的物理状态和 stochastic ownership 不变。

输入 set 的排列应在每步随机化。策略输出在相应 permutation 下必须保持 equivariance。

Source-identifiability gates

在任何 learned training 前，以下门槛必须全部通过。建议默认：

[
S_{\mathrm{SLA}}=0.90,\qquad S_{\mathrm{cat}}=0.60.
]

No-failure feasibility：
oracle 和 same-information constructive controller 在至少 95% episodes 中，至少 95% 时间满足 (S_t\ge0.90)。

Event feasibility：
在每个 mandatory moderate event 中，same-information constructive controller 的 access probability lower 95% CI 不低于 0.90。

Catastrophic avoidance：
(S_t<0.60) 持续超过预定 (K) steps 的概率，其 upper 95% CI 不高于 0.05。

Reallocation necessity：
oracle/constructive controller 相对 no-reallocation comparator 的 event-window minimum service 优势，其 lower 95% CI 大于 0.05，且建议点估计至少 0.10。

Event-free control：
关闭事件后，同一 demand/noise episodes 不出现由 event machinery 引入的性能下降。

Online identifiability：
不能只让 clairvoyant oracle 通过；对 unexpected events，至少一个只使用与 policy 相同 event information 的 constructive controller 必须通过。

Ownership certificate：
survivor state、noise stream 和 source ledger 在 replacement/rejoin 前后逐项连续；rejoining member 不能继承过期 actor state。

Permutation certificate：
active-set order permutation 只能导致对应的 output permutation，不得改变物理 joint action。

若第 1–4 项任一失败，应停止 learned-policy comparison并重新设计 source。



MANDATORY_EXPERIMENT_MATRIX

训练分布

只训练一个主要模型：

training team size：(N_{\text{train}}=8)；

一套 shared parameters；

不进行 size-specific fine-tuning；

training events：

no event；

announced single rotation；

unannounced single temporary dropout/rejoin；

每 episode 最多一个 moderate event；

event timing、duration 和被选成员来自窄的注册训练分布；

所有方法使用相同 environment steps、episode identities、optimizer-update budget 和模型选择规则。

这样可以使 replacement、count shock、compound churn 和极端 timing 成为真正 held-out tests。

Frozen conclusion-bearing evaluation

Block	Team sizes	Roster process	Distribution status	主要目的
A	6, 8, 12	no event	held-out sizes	检查基本跨规模 transport 和 no-event degradation
B	6, 8, 12	planned single rotation + return	ID timing；OOD earlier/later timing 与更长 absence	H1、H2、anticipation
C	6, 8, 12	abrupt temporary dropout + rejoin	ID severity；OOD duration/member selection	unexpected recovery 与 stale-state handling
D	6, 12	permanent loss + delayed replacement	完全 held-out	replacement semantics
E	6, 12	two-member count shock	完全 held-out，near-feasible severity	multiplicity robustness
F	6, 12	repeated leave/rejoin 或 mixed planned/unplanned sequence	完全 held-out compound law	lifecycle correctness 和 process-law generalization

每个 event block 至少包含：

moderate feasible severity；

一个接近但仍由 constructive controller 证明可行的 severe severity；

deterministic event cell；

stochastic paired cell。

所有评估均使用：

final-only frozen checkpoints；

deterministic policy evaluation 为 primary；

paired stochastic evaluation 为 secondary；

identical demand、event、initial-state 和 environment-noise identities；

不在 N=6 或 N=12 上重新训练或调参。

一个还是两个任务

一项通过严格 source-identifiability gate 的任务足以支持最窄论文 thesis。

第二任务不是 mandatory。若第一任务的 physics 和 roster semantics 清楚，强基线与 held-out matrix 的科学价值高于添加另一个浅表环境。

Simulation 与 hardware-in-the-loop

Simulation-only： 足以支持“registered simulated UAV service benchmark”论文。

Hardware-in-the-loop： 不是最小必要条件，但会显著加强 latency、autopilot tracking 和 action-rate 可行性。

Real fleet： 只有在希望使用“operational UAV resilience”之类措辞时才接近必要；即便如此仍不能声称 safety certification。

G50 的位置

G50 不阻塞 source-identifiability，也不必先于初始 UAV transport gate 完成。它可概念上并行，但最终投稿前必须满足以下之一：

G50 表明 anchor 必要：把它作为 finite-budget curriculum/optimization-path ablation；

fresh G49 noninferior：最终方法移除 anchor，G50 放 appendix；

G50 仍 unresolved：不得把“minimal fresh training route”列为贡献，只能报告使用 historical anchor 的最终训练协议。



OPTIONAL_STRENGTHENING_EXPERIMENTS

第二 UAV task： 例如 persistent sensing 或 relay continuity。只有第一任务已通过全部 gates 后才值得开展。

Partial observability variant： 隐藏全局 demand，加入 communication delay；用于判断 recurrence 是否在新 contract 下必要，不能混入 current-state primary claim。

Larger-(N) scaling： (N=16,32,64)，用于拟合 latency 与 memory scaling，而非扩展主要 service claim。

Hardware-in-the-loop： PX4/ArduPilot dynamics、真实控制周期、network delay 和 packet loss。

Small-fleet demonstration： 3–5 架 UAV 的 planned swap 与单机 dropout。

Cross-simulator validation： 保持相同 roster/event protocol，在另一动力学或 radio model 中复验。

Unseen demand laws： 仅在 roster-law generalization 已成立后增加，避免同时改变两个分布轴而失去归因。

这些实验用于扩大 external validity，不应成为第一篇论文的无界 benchmark wishlist。



BASELINES_AND_ALTERNATE_EXPLANATIONS

Mandatory baselines

Baseline	最小公平实现	排除的 alternate explanation
No-reallocation	event 发生后 survivors 延续 no-event trajectory/assignment	证明服务恢复确实需要 roster-triggered reallocation
No-failure / oracle upper bound	相同 episode 关闭事件；另加 clairvoyant 或 MPC oracle	区分环境容量损失、不可行性和算法损失
Fixed-slot padded/masked MAPPO	capacity 12、固定 slots、active mask，训练时仅 8 active	检验 fixed identities 与 padding 是否已经充分
Roster-randomized padded MAPPO	与 proposed policy 完全相同 event curriculum	排除 robustness 仅来自 training randomization
Recurrent shared MARL	GRU/LSTM，parameter/compute matched，相同 roster interface	检验 actor memory 是否 load-bearing
Graph/attention/set variable-agent policy	例如 InforMARL-style GNN-MAPPO 或 Set/GAT-MAPPO	排除收益仅来自更强 permutation-equivariant function class
k-nearest variable-agent policy	固定 (k)，相同局部观测半径和训练数据	与稀疏 scalable aggregation 做直接比较
Capacity-matched MLP control	增宽普通网络以匹配参数量和 FLOPs	排除额外容量解释

GPL、CIAO 或 COPA 并非天然公平 baseline：它们分别面向 ad hoc teammate modelling、joint-value reasoning 或 global coach。只有在不改变问题定义且可适配 continuous decentralized control 时才应纳入。

最小 mechanism ablations

不应重跑全部 G31–G49 历史链。UAV paper 只需要四个结论导向 ablations：

Roster-native versus fixed slots
相同 actor size、training randomization、optimizer exposure。

Lifecycle/state ownership removed
在 rejoin 时故意沿用 slot-owned stale state；只用于检验 ownership 的因果作用。

Active-set context removed
保留 ego current state 与 demand path，移除 roster aggregate。

G49 single-immediate versus restored complex-credit route
只做一个 matched-budget formal comparison，判断 toy reduction 是否运输。

Representation、curriculum 与 exposure 的分离

至少使用一个 (2\times2) factorial：


	Fixed/no roster curriculum	Roster-randomized curriculum
Fixed-slot representation	A	B
Roster-native representation	C	D

解释：

(D-C)：training curriculum effect；

(D-B)：representation effect under matched randomization；

(B-A)：fixed-slot model 从 randomization 获得的收益；

若仅 D 优于其他三者，则可能存在 interaction，而不是单一 representation 主导。

所有 arm 必须匹配：

environment transitions；

gradient updates；

batch reuse；

parameter count，或报告严格的 capacity-matched control；

checkpoint-selection opportunities；

wall-clock 或 optimizer exposure。



ROBUSTNESS_METRICS_AND_STATISTICS

Robustness 的操作定义

令 (\mathcal P_{\text{test}}) 为预注册 roster processes。方法只有在下列所有 primary conditions 成立时，才可称为对该 process class 具有 roster-perturbation service robustness：

满足 absolute service SLA；

event-window degradation 有界；

recovery 在预声明时间内完成；

catastrophic-loss probability 低于上限；

held-out sizes 和 roster laws 的 transport gap 不超过 margin。

核心指标

Absolute mission access

[
A_e=
\mathbb 1!\left[
\frac1T\sum_t\mathbb 1(S_t\ge S_{\mathrm{SLA}})
\ge \rho_{\mathrm{SLA}}
\right].
]

报告 episode-level access probability，而非只报告 mean return。

Event-window minimum service

[
M_e=\min_{t\in[t_e-\Delta_-,,t_e+\Delta_+]}S_t.
]

Recovery time

[
T_{\mathrm{rec}}
=\inf{k:S_{t_e+k+k+K-1}\ge S_{\mathrm{SLA}}}.
]

若 episode 内未恢复，作为 right-censored failure 或赋予预声明最大 penalty。

Recovery deficit AUC

[
D_{\mathrm{AUC}}
=\sum_{t=t_e}^{t_e+H_r}
\left(S_{\mathrm{SLA}}-S_t\right)_+,\Delta t.
]

Catastrophic service loss

[
C_e=
\mathbb 1!\left[
S_t<S_{\mathrm{cat}}
\text{ for at least }K_{\mathrm{cat}}\text{ consecutive steps}
\right].
]

Tail risk

对 (M_e) 报告 lower-tail CVaR；或对 (D_{\mathrm{AUC}}) 报告 upper-tail CVaR：

[
\operatorname{CVaR}{0.10}(D{\mathrm{AUC}}).
]

Post-rejoin quality

rejoin 后固定窗口平均服务；

rejoin-induced transient deficit；

lifecycle contamination incidents；

rejoining member 与 survivors 的 action discontinuity。

Transport gaps

[
G_N=J(N_{\text{train}})-J(N_{\text{test}}),
\qquad
G_{\mathcal P}=J(\mathcal P_{\text{ID}})-J(\mathcal P_{\text{OOD}}).
]

Computational metrics

per-agent inference latency；

peak memory；

actor FLOPs；

communication bytes/step；

empirical scaling exponent；

(N) 增大时的 deadline-miss probability。

Primary estimands 与 margins

建议只有三个 multiplicity-controlled primary endpoints：

absolute access probability；

event-window minimum service；

recovery deficit AUC。

默认 operational gates：

access probability lower 95% CI (\ge0.90)；

catastrophe probability upper 95% CI (\le0.05)；

相对 no-event 的 service degradation 不超过
[
\delta_S=
\min\left(0.05,\frac{\Delta_{\text{oracle-NR}}}{3}\right);
]

相对主要 fixed-mask baseline 的 event minimum 优势 lower CI (>0)，并达到预声明最小 practical effect；

recovery-AUC margin 同样由 oracle–no-reallocation separation 的不超过三分之一确定。

这样 margin 来源于任务的 operational separation，而不是看完结果后选择。

Statistical protocol

Independent training seeds 是实验单位之一；episodes 不能替代独立训练。

对不同方法使用配对 initialization labels、training episode streams 和 evaluation episode identities，但承认不同优化轨迹不是严格相同随机变量。

evaluation pairing 固定：

demand；

event time/member/duration；

initial state；

environment noise；

source-owned stochastic streams。

使用 hierarchical whole-episode bootstrap：

第一层重采样 training seeds；

第二层在每个 seed pair 内重采样完整 paired episodes；

不跨 episode 拆分时间点。

access/catastrophe probability 同时报 one-sided Wilson 或 exact binomial bounds，并以 training seed 为 cluster 做敏感性分析。

final-only checkpoint；禁止为不同 evaluation cells 选择不同 checkpoint。

预声明 gatekeeping：

先检验 source access；

再检验 proposed versus primary fixed-mask baseline；

再检验 OOD transport；

其他 baseline 和 ablation 作为 secondary family。

除 CI 外报告 paired effect size、median、worst decile 和每个 training seed 的结果。

Seed 和 episode 数量的确定

不应使用“MARL 通常用 3 或 5 个 seeds”作为理由。

建议：

用小规模 blinded variance stage 估计 between-seed variance 和 within-seed paired variance；

不查看 method labels，仅根据 pooled variance 调整总 training-seed 数；

以 primary effect/margin 达到 90% power、one-sided (\alpha=0.025) 为目标；

通过 cluster-aware Monte Carlo power simulation 决定 seed 数；

rare catastrophe episode 数根据目标 CI 精度确定。例如若要求证明概率低于 0.05，48 episodes 通常不足以稳定刻画尾部；应选择使 one-sided upper bound 达到目标精度的 episode 数，并在多个独立 policies 上重复。



FALSIFIERS_AND_STOP_RULES

Source invalidation

立即判定 UAV source 无效并停止 learned comparison，若：

clairvoyant oracle 无法满足 SLA；

same-information constructive controller 无法在 moderate event 下通过；

no-reallocation comparator 也满足全部主要门槛；

event-free control 因 source mechanics 本身失败；

结果主要由 collision shield、battery reserve violation 或 unreachable depot 决定；

planned 或 unplanned event 没有造成可测且可恢复的 service deficit。

Roster-native transport 被否证

若在任一预声明 moderate、feasible primary OOD cell 中：

access lower CI 低于 0.90；

catastrophe upper CI 高于 0.05；

(G_N) 或 (G_{\mathcal P}) 超过 margin；

rejoin 出现系统性 stale-state contamination。

单个接近物理不可行边界的 stress cell 失败不应单独否证 H1，但必须限制 severity claim。

Fixed masking 已充分

若 roster-randomized padded/masked baseline 在所有 primary cells 中对 proposed method 达到预声明 noninferiority，且：

参数量；

training steps；

optimizer exposure；

input information；

均匹配，则不能把 roster-native representation 作为算法贡献。论文最多转为 benchmark/protocol paper。

Recurrence 或 attention 为 load-bearing

若 matched recurrent 或 graph-attention policy：

在 primary endpoints 上超过 practical superiority margin；

且这种优势跨 seeds 与 OOD laws 稳定；

则必须采用该架构，或删除“small current-state actor sufficient”的论文主张。

Robustness 仅来自 randomization

若在 (2\times2) factorial 中：

roster-randomized fixed-slot 与 roster-native 相同；

representation main effect 不存在；

不进行 randomization 时所有方法均失败；

则结论应改为 roster-event domain randomization，而不是 roster-native representation。

仅由额外容量或 exposure 驱动

若 capacity/compute/optimizer-matched control 消除优势，则算法 novelty 被否证。不能用未匹配的更大模型支撑 robustness claim。

Claim 被限制到单一规模或过程

若只有 N=8 或 training roster law 通过：

claim 必须限制为 in-distribution dynamic roster control；

删除 unseen-size 或 held-out-process generalization；

不得使用“without retraining for team size”作为主要贡献。

退回 mechanism-only paper

出现以下任一结果时，应放弃当前 UAV narrative：

连续两个合理设计的 UAV sources 均无法通过 source gate；

source 通过，但 G49 无法达到 absolute access；

fixed-mask 或标准 graph baseline 在全部结论 cells 中 noninferior；

UAV mechanism ablation 显示 G46–G49 simplification 不运输且没有替代的新机制发现。

此时 mechanism-only paper 还需增加至少一个独立非 UAV source family 或一般性理论，否则现有 toy reductions 仍可能过于 source-specific。



PAPER_TITLE_CONTRIBUTIONS_AND_OUTLINE

推荐标题

Roster-Native Decentralized Control for UAV Service Continuity under Within-Episode Team Changes

避免在标题中使用未经证明的 “System Robustness”“Fault-Tolerant UAV Swarms” 或 “Universal”。

一句话 thesis

A shared, lifecycle-aware and permutation-equivariant policy can maintain a registered UAV service SLA across planned rotations and unexpected within-episode membership changes at held-out team sizes and roster laws, without size-specific retraining.

预期贡献

只有在 mandatory matrix 成功后，才可列出以下贡献：

Roster-process formulation： formalize within-episode leave、failure、replacement、rejoin 与 state-ownership semantics。

Compact controller： shared current-state active-set policy with no fixed identity dependence and a single-immediate training route。

Identifiable UAV benchmark： absolute feasibility、no-reallocation necessity 和 same-information constructive gates。

Robustness protocol： held-out team sizes/process laws、event-window recovery、catastrophe probability 与 tail-risk inference。

Mechanism result： 在注册 observability contract 中，lifecycle/active-set representation 比恢复复杂 actor-credit machinery 更具因果负载——仅当 UAV ablation 支持时保留。

章节结构

Introduction and bounded claim

Related work and novelty boundary

Dynamic-roster Dec-POMDP and lifecycle ownership

Roster-native shared controller and training route

Identifiable UAV service benchmark

Registered experiment and statistical protocol

Results

source validity

absolute access

planned/unplanned transport

held-out sizes/process laws

tail risk

scalability

Mechanism ablations

Limitations and claim ceiling

Conclusion

G31–G49 的取舍

Main paper：

一张 compressed lineage 图；

G49 final route；

G47/G49 的精确简化结论各一段；

一个 UAV full-credit versus single-immediate comparison；

一个 roster representation/lifecycle ownership ablation。

Appendix：

G46 和 G48 的完整 registered CIs；

G47/G49 static/numerical certificate；

G31–G39 的冻结边界、formal gates 和完整统计协议；

source/seed ledger。

省略或仅放 provenance：

donor/filler columns 等已被后续 route 淘汰的历史细节；

每一次微小 branch token 的叙事；

与最终 thesis 无直接关系的 toy-only tuning chronology。

G50 的论文地位

anchor 必要且无法由 optimizer exposure 解释：curriculum ablation，通常不是核心贡献；

fresh G49 sufficient：appendix 或简短 negative result；

anchor 在多个 UAV cells 中产生稳定、显著和可解释的 finite-budget advantage：才可升级为次要贡献；

unresolved：future work，且删除 minimal-optimization-path claim。

Venue 类别

AAMAS main track： 最匹配 dynamic teams、MARL formulation 和系统性 evaluation。

IEEE RA-L / ICRA / IROS： 需要更强物理建模、实时测量，最好含 HIL 或小型 fleet demonstration。

TMLR： 若重点是严谨 protocol、机制审计和全面 reproducibility。

顶级通用 ML venue： 单一 UAV simulation task 通常不足；需要更一般的理论、多个任务族或广泛 reusable benchmark。



PRIORITIZED_NEXT_ACTIONS

顺序与 boundary	结果改变的决策	所需证据	Success boundary	Failure boundary	是否 conclusion-bearing	失败后不再需要的工作
1. UAV_SOURCE_IDENTIFIABILITY_G0	UAV narrative 是否有科学对象	no-failure oracle、same-information constructive controller、no-reallocation、event controls、ownership certificate	全部 source gates 通过	oracle/constructive 不可行，或 no-reallocation 也通过	是，source-level	所有 learned training、G50-to-UAV transport、HIL
2. UAV_TRANSPORT_ACCESS_G1	G49 是否值得进入 formal matrix	N=8、moderate planned rotation 与 temporary dropout；对比 padded baseline	G49 达到 absolute access，且至少一个 roster event 显示 causal reallocation	G49 无法 access，或明显劣于简单 baseline	是	全 size/process matrix、第二任务、hardware
3. UAV_FORMAL_MATRIX_G2	原始论文 thesis 是否成立	N=6/8/12、ID/OOD planned/failure、replacement、count shock、rejoin；强 baselines	所有 primary moderate gates 与关键 OOD gates 通过	unseen size/process 或 absolute access 失败	是，核心	广义 robustness claim；必要时退回 in-distribution 或 mechanism-only
4. UAV_REPRESENTATION_FACTORIAL_G3	novelty 来自 representation、curriculum 还是 capacity	(2\times2) representation × randomization、capacity/exposure controls	roster representation 有独立 practical effect；ownership ablation 失败	randomization/fixed mask 已充分	是	roster-native algorithm contribution；可转 protocol paper
5. UAV_CREDIT_TRANSPORT_G4	G46–G49 是否属于 UAV mechanism story	G49 与 restored complex-credit route matched comparison	single-immediate noninferior，复杂 route 无 material advantage	complex credit 显著改善 primary metrics	是，但次级	“representation dominates credit complexity” claim
6. G50_OPTIMIZATION_PATH	最终训练方法是否需要 anchor	fresh、anchor、extra-exposure control	明确归因 anchor effect 或证明可删除	结果不稳定或只由额外 steps 解释	是，仅影响方法叙事	curriculum contribution
7. SCALING_AND_HIL_G5	能否扩大到 real-time/robotics claim	target-device latency、memory scaling、autopilot HIL	deadline、tracking 和 communication envelope 通过	inference 或 dynamics 不可部署	否，对最窄 simulation thesis 非必要	real-time/HIL/fleet wording
8. SECOND_TASK_OR_FLEET_G6	external validity 是否足以扩大 venue/claim	第二任务或 3–5 UAV demonstration	同一机制跨任务或平台成立	只在单一 simulator 成立	可选	broad UAV resilience claim

最大的当前不确定性不是 G50，而是是否存在一个既物理可行、又确实需要 roster-triggered reallocation 的 UAV source。因此第一项不得被算法训练或更多 toy ablation 替代。



UNRESOLVED_SCIENTIFIC_QUESTIONS

是否能构造一个 online-causally feasible、但 no-reallocation 明确失败的 UAV service source？

G49 在 UAV source 上能否达到 absolute SLA，而不仅是提高平均 utility？

fixed-slot mask 加充分 roster randomization 是否已经和 roster-native representation 等价？

lifecycle/state ownership 是否在 repeated rejoin 中产生可测的独立作用，还是只是一项实现卫生条件？

planned rotation 和 unexpected failure 是否真的可由一个 policy 处理，还是需要不同 anticipation modules？

current observation 是否充分 Markov；若有 heartbeat delay、demand aliasing 或 communication loss，recurrence 是否变为必要？

G46–G49 的 credit simplification 是否运输，还是 toy reward structure 的特例？

historical fast anchor 的收益是否来自 curriculum、initialization basin、额外 optimizer exposure 或 checkpoint opportunity？

local-neighbor (O(Nk)) policy 在 count shock 时是否遗漏关键远程 reallocation 信息？

service robustness 是否在 N=6/12 和 held-out process laws 上保持，还是只在训练 law 附近成立？

尾部 catastrophic events 是否由 policy、source infeasibility、failure-detection delay 或 safety shield 主导？

simulation 的 energy、communication 和 depot abstractions对最终结论有多敏感？

paper_now=NO
uav_validation_minimum=一个通过 oracle、same-information constructive controller 与 no-reallocation 因果门槛的固定高度 UAV 服务任务，加上 N=8 单次训练及 N=6/8/12 对计划轮换、突发失效重返和 held-out roster laws 的冻结强基线评估。
system_robustness_claim_now=TOO_BROAD
recommended_next_boundary=UAV_SOURCE_IDENTIFIABILITY_G0
review_complete=true