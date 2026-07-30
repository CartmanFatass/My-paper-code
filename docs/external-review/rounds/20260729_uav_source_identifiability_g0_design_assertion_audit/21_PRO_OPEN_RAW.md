Edit
G0_DESIGN_CONFORMANCE

审查结论：SOURCE_IDENTIFIABILITY_G0 是当前正确且最小的下一科学边界。

这不是对项目经理摘要的照单接受，而是由现有证据强制得到的顺序：

当前 Scenario-7 仍以 8 个固定 possible_agents 和固定尺寸 tensor 表示物理机队；现有 failure、charging 和 availability 字段尚未自然形成经过注册的 service-active lifecycle set。研究简报也明确要求区分“physical fleet”与“service-active roster”。

已关闭的 UAV_TEMPORARY_SERVICE_LOSS_G1 同时未通过绝对 feasibility 与 reallocation load-bearing gate：constructive J_event 的 CI95 低于 0.90，且 constructive-minus-no-reallocation CI95 完全为负。该结果只关闭该 source definition，不否定候选算法。

项目原则要求先区分 benchmark access、mechanism identifiability、intervention consequence 和 natural transport；benchmark non-identification 只能更新 benchmark-comparator pair，不能被更多 toy ablation 或 learned training“救回”。

独立 paper-readiness review 已把 UAV_SOURCE_IDENTIFIABILITY_G0 定为最高信息增益边界，并要求 no-failure oracle、same-information constructive、no-reallocation、event controls 和 ownership certificate 先行。

旧 G1 失败至少兼容三种结构性解释，G0 必须将其区分：

Fleet slack explanation： 现有用户、地面基站和无线容量使单机离线后仍有足够冗余，因此重分配并非必要。

Metric dilution explanation： 全局平均 QoS 掩盖局部服务区的严重缺口。

Information-path explanation： clairvoyant constructive 可以利用完整 ledger，但 current-only controller 未必能及时识别并恢复服务。

因此，G0 应重新定义一个新的、局部服务可识别的 source family，而不是修改 G1 的 onset、duration 或 margin 后重新命名。

G0_SCIENTIFIC_BOUNDARY

G0 的唯一科学问题是：

在固定 8 资产、固定高度的 UAV communication-service task 中，是否存在一个物理可行、在线可处理、且若不进行 roster-triggered spatial reallocation 就不能满足服务门槛的单次 temporary service-LEAVE/rejoin source？

G0 只识别 source，不比较 learned policies，不评估 G49，不评估 roster-native representation 相对 fixed masking 的优势。

两个不同的集合

固定物理机队：

[
\mathcal F={0,\ldots,7}.
]

物理 slot 在整个 episode 中存在，负责承载位置、速度、碰撞状态和环境随机性。

服务活跃 roster：

\left{
\ell=(i,e):
i\in\mathcal F,;
E_i^{\mathrm{phys}}(t)=1,;
L_{i,e}^{\mathrm{temporary}}(t)=0,;
L_{i,e}^{\mathrm{terminal}}(t)=0
\right}.
]

其中 (e) 是 service lifecycle epoch，而不是 actor-visible identity。

Temporary LEAVE 在该步动作采集前发生。离线资产：

仍占有物理 slot；

位置保持、速度置零；

不产生通信服务；

不产生 service-policy action；

不进入 service-active set；

不产生 action probability 或 policy loss。

Rejoin 时保留当前物理状态，但创建新的 lifecycle epoch：

[
(i,e)\longrightarrow(i,e+1).
]

新 epoch 不继承旧 actor state 或旧 action-noise stream；所有 survivor lifecycles 的状态与随机性所有权必须保持不变。该选择与当前无 actor carry 的候选边界相容，但 G0 不把它解释为算法优势。

这满足项目对 anonymous membership、join/leave/rejoin、state ownership、active masks 与 survivor continuity 的最低语义要求。

G0_MINIMUM_EXECUTABLE_CONTRACT
1. Physical source

复用 Scenario-7 的以下物理和服务语义：

physical_uavs=8
users=30
ground_base_stations=1
episode_steps=500
per_user_target_rate_mbps=1.0
fixed_altitude=true
battery_enabled=false
charging_enabled=false
terminal_loss_enabled=false

连续运动 action、速度/加速度限制、collision/safety mechanism、无线 propagation、association 和 rate computation 使用同一 source 内完全相同的现有实现。现有 S7-S1 基线确实具有 8 UAV、30 users、500 steps、1 Mbps target、0.90 QoS target，且关闭 battery、charging 和 failure。

2. Service-identifiable geometry

定义地图中心或 ground-BS 位置为 (b)，令

[
L=\min(\text{map width},\text{map height}).
]

每个 episode 采样一次全局旋转：

[
\phi\sim\operatorname{Uniform}[0,2\pi).
]

三个 hotspot 中心为

[
c_z=b+0.30L
\begin{bmatrix}
\cos(\phi+2\pi z/3)\
\sin(\phi+2\pi z/3)
\end{bmatrix},
\qquad z\in{0,1,2}.
]

每个 hotspot 有 10 个用户；用户位置独立采样于以 (c_z) 为中心、半径 (0.04L) 的圆盘内，并在该 episode 中保持静止。G0 不引入 user-motion prediction。

六架 UAV 以每个 hotspot 两架的方式初始化于 (c_z) 附近；另两架 UAV 初始化于 ground-BS 附近的两个 reserve staging points。每个 episode 将八个物理 slot 对六个 primary positions 和两个 reserve positions 做独立随机 permutation。任何控制器不得读取“primary slot”“reserve slot”或 hotspot-owner ID；这些仅是环境 target ledger。

该几何旨在制造“正常状态有备用容量，但单个局部 contributor 离线后必须移动备用资产”的可识别任务。它不是对既有 G1 数值参数的调整。

3. Disturbance law

唯一 G0 event cell 为：

cell=UNANNOUNCED_PRIMARY_TEMPORARY_LEAVE
owner=uniform_over_the_six_current_hotspot_serving_lifecycles
onset=discrete_uniform_180_to_220
duration=discrete_uniform_80_to_100
detection_delay=0
leave_timing=before_action_collection
physical_state_during_leave=position_hold_zero_velocity
communication_during_leave=disabled
rejoin=new_lifecycle_epoch_same_physical_slot

同时生成 paired NO_EVENT counterpart：物理初始状态、用户位置、channel randomness 和所有非 event disturbance 完全相同，只取消 service LEAVE。

G0 不包含 planned charging、maintenance transit、terminal failure、replacement 或 double shock。

4. Information-fair controls
Clairvoyant feasibility oracle

允许读取：

完整 owner/onset/duration/rejoin ledger；

当前和未来 event identity；

当前完整物理状态。

限制：

必须遵守相同动力学、action bounds、collision rules、通信模型和 service mask；

不得 teleport；

不得改变用户、channel 或 event；

不训练，不进入任何 learned comparison。

它只回答“物理上是否存在满足服务目标的轨迹”。

Same-information constructive controller

只能读取未来 policy 可获得的当前信息：

当前 active roster；

当前 UAV positions、velocities 和 service availability；

当前各 hotspot 的 demand 与 delivered-rate deficit；

当前 channel/association state；

当前 ground-BS 和 reserve-relative geometry。

不得读取：

event owner、onset 或 duration 的未来值；

rejoin time；
-未来 channel 或用户状态；

physical slot identity；

lifecycle epoch 数值。

其冻结行为规则是：

无 deficit 时维持两-UAV-per-hotspot service layout，剩余两架停留于 staging targets。

发现某 hotspot 的 active contributor 数或服务率下降后，选择当前物理距离最短的 service-active reserve 前往该 hotspot。

所有 tie 均由当前匿名物理内容确定，不由 slot index 决定。

rejoin 后，在不降低当前 service floor 的条件下将替补 UAV 送回 staging point。

该控制器回答“在与未来 learned controller 相同的在线信息下，source 是否可达”。

Ledger-blind no-reallocation control

它获得与 same-information constructive 相同的当前 physical observation 和 active mask，但：

event 前冻结每个 survivor 的 target ownership；

event 后不得把任何 reserve 或 survivor 重新分配到缺口 hotspot；

继续追踪各自 event 前 target；

只允许相同的低层 safety/collision correction。

它不得因 active-count change、hotspot deficit 或 rejoin 改变 target assignment。

因此，该 control 不是“看不见故障”的弱控制器，而是看见当前物理状态但禁用 roster-triggered reallocation的因果对照。旧 source contract 同样把 constructive 与 no-reallocation 定义为 evaluation-only feasibility controls，而非 learned comparators。

5. Paired randomness

以下变量使用互相独立的 RNG namespaces：

hotspot global rotation；

user positions；

physical-slot permutation；

initial UAV perturbations；

channel randomness；

event owner；

event onset；

event duration；

controller stochasticity，如存在。

同一 episode ID 下，oracle、same-information constructive、no-reallocation 和 NO_EVENT counterpart 共用完全相同的物理、用户、channel 和 event realization。

不得以 controller 名称重新播种环境。

6. Service and utility

对 hotspot (z)，定义：

\frac{1}{10}
\sum_{u\in z}
\mathbf 1
\left[
r_u(t)\ge1.0;\text{Mbps}
\right].
]

主要 service variable 为最弱 hotspot：

[
S_t=\min_{z\in{0,1,2}}\rho_z(t).
]

全局平均 QoS：

\frac{1}{30}
\sum_{u=1}^{30}
\mathbf 1[r_u(t)\ge1.0;\text{Mbps}]
]

仅作 secondary diagnostic，不能替代 (S_t)。

令 event/recovery window 为

[
W=[O,;O+D+60).
]

定义：

[
d_t=\frac{(0.90-S_t)_+}{0.90},
]

1-\frac{1}{|W|}
\sum_{t\in W}d_t,
]

\frac{1}{|\bar W|}
\sum_{t\notin W}S_t,
]

\min\left(
\frac{J_{\mathrm{event}}}{0.90},
\frac{Q_{\mathrm{ordinary}}}{0.90}
\right),
]

[
M_{\mathrm{event}}=\min_{t\in W}S_t.
]

Catastrophic service loss 为：

[
C=
\mathbf 1\left[
S_t<0.60
\text{ for at least 10 consecutive steps in }W
\right].
]

现有 external reward、total delivered throughput、distance 和 collision telemetry 必须报告，但均为 secondary utility diagnostics；它们不能救回失败的 source-identifiability gate。

7. Evidence volume and confidence

G0 不创建 learned model、optimizer、checkpoint 或 training seed。

每个 control 在 event cell 和 paired no-event cell 各使用 128 个完整 episode IDs。该数量不是算法 seed convention；它用于使 episode-level access 和 catastrophic probabilities 可获得有意义的单侧置信界。

连续 estimands 使用 10,000 次 paired whole-episode bootstrap。Access 和 catastrophe 同时报告 one-sided exact binomial interval。

所有 gate 使用预声明的 95% confidence bounds。

8. Exact certificates

在读取 behavioral result 前必须通过：

physical fleet 始终为 8；

active roster count 在 leave/rejoin 边界准确变化；

LEAVE 在 action collection 前生效；

inactive lifecycle 无 service action；

inactive lifecycle 无 actor row、likelihood 或 policy-loss authority；

rejoin 创建新 lifecycle epoch；

survivor physical state、controller state 和 RNG stream 不变；

physical-slot permutation 只置换内部记录，不改变 world-space trajectory、service 或 control target；

NO_EVENT 中 same-information 与 no-reallocation 的 target、actions 和 physical trajectories 完全一致；

oracle、same-information 和 no-reallocation 使用相同物理 action support 与 safety rules；

无 future-ledger leakage；

event 与 no-event counterparts 的非 event randomness 精确配对。

Permutation 和 ownership 证书只是 source semantics 的必要条件，不是 roster-native algorithm advantage 的证据。

G0_COUNTEREXAMPLES_AND_CLAIM_LIMITS
Counterexample 1：no-reallocation 仍可 access

若 no-reallocation 满足 absolute service access，则该 source 不证明 roster-triggered reallocation 的必要性，即使 constructive 有更高平均 reward。

允许结论仅为：

该物理服务任务具有足够 slack，单次 temporary leave 不识别 reallocation necessity。

不得缩窄 CI、改换 metric、延长 duration 或重新选择 owner 来救回同一次 source。

Counterexample 2：oracle 可行但 same-information constructive 不可行

这说明 task 在 clairvoyant planning 下物理可行，但在 current-only unexpected-failure information contract 下不可在线恢复。

允许选择只有：

把 source 限定为 announced/planned event；

或在新的科学边界中增加合法的 detection/announcement information。

不能在本 G0 内把 future onset 或 duration 暗中提供给 actor。

Counterexample 3：结果依赖 slot identity

若将 physical slots 做一致 permutation 后，target ownership、world-space action 或 service 改变，则所谓 anonymous roster source 无效。

固定 slot 可用于环境存储，但不能成为 cooperation 或 reserve selection 的信息捷径。项目原则明确要求 fixed identity slots 不得成为 variable-membership cooperation 的唯一载体。

Counterexample 4：局部 service 失败但全局平均通过

若 (\bar\rho_t) 通过而 (S_t) 失败，必须按 primary zonal service gate 判定失败。全局平均 utility 不能掩盖一个 hotspot 的持续失服。

本 G0 明确排除的 claims

即使 G0 source 被识别，也不支持：

任一 learned policy access；

G49 UAV transport；

roster-native 优于 fixed masking；

recurrent 或 current-state sufficiency；

planned charging rotation；

maintenance queueing；

terminal loss；

replacement；

repeated rejoin robustness；

count shock；

variable team size；

held-out process-law generalization；

tail robustness of a learned controller；

real-time deployment；

UAV system robustness；

safety 或 certification。

G0 成功只表示：已经获得一个可用于后续 learned comparison 的 source-identifiable diagnostic task。

G0_EVIDENCE_AND_FIRST_MATCH_GATES

所有结果严格按下列顺序 first-match；匹配后不读取后续 branch。

1. INVALID_UAV_G0_REALIZATION

任一以下条件失败：

source law 或 episode count；

RNG independence 或 pairing；

physical/service roster separation；

leave/rejoin timing；

ownership或 survivor continuity；

permutation certificate；

information visibility；

controller action-support matching；

metric arithmetic；

provenance。

科学更新：无。仅修复实现与冻结 contract 的不一致。

2. INFEASIBLE_UAV_G0_SOURCE

实现有效，但满足任一条件：

[
\operatorname{LCB}{95}(A{\mathrm{oracle}})<1,
]

或 oracle 违反 physical/safety constraints，或 no-event oracle 无法维持 service floor。

科学更新：关闭该 clustered-reserve source。不能推断算法失败。

3. ORACLE_ONLY_UAV_G0_SOURCE

Oracle 可行，但满足任一条件：

[
\operatorname{LCB}{95}(A{\mathrm{sameinfo}})<1,
]

[
\operatorname{UCB}{95}
\left(
P(C{\mathrm{sameinfo}}=1)
\right)>0.05.
]

科学更新：unexpected current-only source 不在线可达；不得进入 learned training。

4. NON_CAUSAL_UAV_G0_SOURCE

Same-information constructive 可行，但满足任一条件：

[
\operatorname{UCB}{95}(A{\mathrm{no\text{-}reallocation}})\ge1,
]

J_{\mathrm{event}}^{\mathrm{no\text{-}reallocation}}
\right)
\le0,
]

或

M_{\mathrm{event}}^{\mathrm{no\text{-}reallocation}}
\right)
\le0.05.
]

科学更新：source 不识别 roster-triggered reallocation necessity。

5. UNDERPOWERED_UAV_G0_SOURCE

点估计方向满足识别要求，但任一 relevant CI 跨越对应 gate。

科学更新：不认定 source。任何增加 episode 数的决定需要新的、只针对 precision 的审查，不得修改 source、controller 或 margin。

6. IDENTIFIED_UAV_G0_SOURCE

仅当以下全部成立：

[
\operatorname{LCB}{95}(A{\mathrm{oracle}})\ge1,
]

[
\operatorname{LCB}{95}(A{\mathrm{sameinfo}})\ge1,
]

[
\operatorname{UCB}{95}(A{\mathrm{no\text{-}reallocation}})<1,
]

[
\operatorname{UCB}{95}
\left(
P(C{\mathrm{sameinfo}}=1)
\right)\le0.05,
]

J_{\mathrm{event}}^{\mathrm{no\text{-}reallocation}}
\right)>0,
]

M_{\mathrm{event}}^{\mathrm{no\text{-}reallocation}}
}
\ge0.10,
]

M_{\mathrm{event}}^{\mathrm{no\text{-}reallocation}}
\right)>0.05,
]

且所有 exact certificates 和 NO_EVENT identity checks 通过。

科学更新仅为：

该固定 8 资产、三 hotspot、单次 unexpected temporary service-LEAVE source 在注册物理和信息边界内既可行，又因果需要在线 roster-triggered reallocation。

旧 G1 已证明 source validity 必须优先于 learned access，并采用 first-match 关闭 non-identifiable source；本 G0 保留该证据顺序，但不复用旧 G1 的 source 或结论。

Evidence-search realization不得使用 nested rollout replanning；若 oracle 使用候选轨迹，其候选数必须固定且不超过 16，并遵守 (O(HK_{\text{search}})) ceiling。

G0_NEXT_BOUNDARY

若未来 first-match 得到 IDENTIFIED_UAV_G0_SOURCE，最小后继问题是：

UAV_G0_SOURCE_CONTRACT_REALIZATION_AUDIT：pushed implementation 是否逐项实现本轮冻结的三-hotspot source、physical-slot/service-roster separation、三类 controls、paired RNG ownership、service metrics、certificates 与 first-match analyzer，并且没有创建 learned model、optimizer 或 checkpoint？

该问题只是下一次 design/code-science audit 的对象，不授权 formal execution，不消费 scientific iteration，不选择 G33，也不授权 paper acceptance。

G0_DESIGN_DISPOSITION

G0_DESIGN_DISPOSITION=PROCEED_TO_UAV_G0_SOURCE_IDENTIFIABILITY
