# Retired research review and superseded plan — 2026-09-27

Historical evidence only; this file is unmaintained. Current state remains in [RESEARCH](../../RESEARCH.md).
Retired by the new Root after the owner-requested four-Codex-DM organisation. Original source revision: `6e734d200879cd9779b330fadc423010b8f1ef0c`.
The complete prior UAV planning review and prior plan are preserved below; their DM2/DM4 numbering is historical.
No pause, accepted operation, source, direction notebook or Pro answer target is moved by this retirement.

<a id="four-dm-root-review"></a>
## Portfolio review 2026-09-27 four-codex-root-handover

Conversation: independent Scientific Reviewer only, `/root/four_dm_plan_review`, `fork_turns="none"`.
Owner request: 接任已归档Root，更新Claude使用的Root地址，读取DM2–4报告，并按四个Codex DM重新组织研究。
Context: constitution §§2/4/5/8，`hmasd-loop-dispatch`、`hmasd-scientific-tools`、`hmasd-portfolio-task`；四个现有DM的原始正／反／失败证据、最新重审和实际accepted状态。
Source: review从`b2726566180ff2191edc39058f6d12f5585de9d1`读取，结束于`6e734d200879cd9779b330fadc423010b8f1ef0c`；本轮仅Codex分工，Claude当前问题与pending咨询不在投资裁决范围。
Decisions asked: 四个现有负责人如何分工；哪些当前工作继续、哪些已撤回方案保持撤回；闲置DM是否存在值得购买的下一项工作。
Options: 完成两项已付费完整观察；为DM3具体化一个学习增量比较；重开cache/PPO、恢复二选一selector，或保持后备。按可改变的判断、完整成本和既有反证比较，不为填槽购买实验。

### Answer

建议**保留四个现有 DM，修订当前计划的编号与下一步；优先收完 DM1 和 App DM2 已接受的工作，当前不购买第三项结果实验。** 四个负责人不等于四项同时运行。

本审查无 Root/DM 对话继承；任务已透露现行撤回决定，因此不声称盲审。我先重建原始输出，再读作者解释和既有审查。起始 SHA 为 `b2726566180ff2191edc39058f6d12f5585de9d1`，结束时为路由交接后的 `6e734d200879cd9779b330fadc423010b8f1ef0c`。全程只读。

| 当前会话 | 建议分工与下一工作 | 科学边界 |
|---|---|---|
| **DM1：baselines** | **保留／完成原定复制。** 收完 seed26092731，并执行原定自身 c00/c06、两模式、32 开发世界评价。 | 检验固定预算普通学习的增益及缺口是否再现。首种子失败仍缺端点；不能靠恢复、补零或增加评价世界补成独立训练复制。 |
| **App DM2：availability，旧 DM4** | **保留 B04。** 完成当前 move/hold 策略包的原生服务、J、风险与完整成本读取。 | 普通服务规划问题；候选额外使用静态模型和计算。阳性可保留一个有用控制器，不能归因为前瞻机制或 MARL。 |
| **DM3：imitation／cooperative planning** | **实质修订，暂不选新 fit。** 下一工作是在现有 NOTES 中收口一个“学习的联合移动／等待后果价值，相对普通自适应规划”的具体比较及完整报价，并据此选或弃。 | 不回到已撤回的二选一／双窗口四臂方案；不接管 Claude 的固定标签协调器或信用估计问题，也不等待 B04 阳性。 |
| **App DM4：diagnostics，旧 DM2** | **保留问题、维持 reserve。** 当前明确不购买 getter-only 重跑、缓存修复项目或 PPO 追加。 | 保留护盾下有限优化问题及普通 PPO＋同护盾参照；已有失败没有给出 masking 的科学正负号。它不是新的合作规划器。 |

支撑这个安排的直接证据是：

- **普通学习确有用途，但尚未得到新的完整独立复制。** 开发面板旧 SET 的确定性／采样 QoS 从 `.209/.243` 升至 `.437/.438`，J 从 `587/693` 升至 `1276/1281`；H_local 为 `.597/1628`。这是一条恢复过的训练谱系，两次训练启动共约 **11.00 小时**，不是两个独立实例。DM1 首个新种子在 **432k 已记录步、3.915 小时**后技术失败。第二种子仍应按已选合同完成；训练粗估 10.9 小时，原定评价 **128 回合／384k 步**，历史约 0.70 小时，争用及支持成本另计。[固定读法与审查处置](../../candidates/energy_relay_baselines/NOTES.md#diagnostic-findings-and-independent-continuation-decision)
- **BC 的窄改善成立，长时域合作瓶颈没有被识别。** 我直接读取节点原生 summaries，并从全部 **64 条 B01/B02 final 轨迹重算 J**：B02−B01 为 **+127.850856，世界 SE 78.594655**；QoS 差 **+.042015**，两者原描述区间均跨零。仍有 **11 个服务/J 损失世界、5 个零服务世界**，低电量尾部更差。B02 为 **1 fit、1,899 更新、96k 环境步、22.03 分钟总墙钟**。教师未激活层 MSE 改善不能区分损失分配、有限优化和后续访问状态变化；也不能迁移成 PPO mask 的证据。[原始读数与信息合同](../../candidates/energy_relay_imitation/NOTES.md#2026-09-27--owner-requested-source-re-review-and-b02-corrections)
- **B03 的关闭有原生后果依据。** 从 perworld 重聚合，energy−distance 的 QoS 为 **−.026619**、J **−208.115**、原始返航成本 **+68.149**；配对摘要的 J 区间为 **[−403.859,−12.371]**。零 cutoff/depletion 没有抵消这些损失。成本 **0 fit、192k 步、16.76 分钟 runner 墙钟**。保留精确规则关闭，不推广为所有能量感知规划无效。[原始逐世界记录](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/perworld.json)
- **diagnostics 没有待“挽救”的科学负结果。** B01 的 c03−c00 采样 J **+290.729**；采样大幅减少墙边停留，却没有相应完整 J 收益，削弱了墙边比例作为用途代理的解释。B02 A01 在训练前失败；A02 在 mask 全程关闭时完成至少 **126k 新步／3371.235 秒**后失败，没有 masked 臂或端点评价。约 59 分钟 getter-only 重跑只能购买错误读取的再现，不能识别写入源或 masking 价值。[原始失败与独立处置](../../candidates/energy_relay_diagnostics/NOTES.md#2026-09-27--owner-requested-b02-re-audit-original-evidence-and-corrections)

**DM3 的收口工作应有一个清楚的完成条件。** 指定同一信息、刷新时钟、动作／承诺集合下的普通自适应规划参照，说明学习究竟增加了哪一种可执行选择或后续价值估计。不能直接把 B04 的 central scorer 移入原 H_local 合同；也不能用较长回报标签的胜出直接证明新的合作机制。

现有较小方案提供可讨论的规模：**64 个采集世界＋两臂各32个评价世界＝128 个 H3000 回合／384k 步、1 fit**；按旧拟合合同最多500更新，基础原生回合估计70–97分钟，另计拟合、规划评分、工程和读取。**这仍是未选方案**，比较器与完整成本尚未具体化。无需先证明精确余量、造新架构或取得普通规划阳性；也无需为早期窄比较强制购买双窗口、额外 flat 臂。只有相应的层级或机制归因才需要那些控制。[已撤回方案及较小替代](../../candidates/uav_cooperative_planning/NOTES.md#2026-09-27--owner-requested-re-review-end-the-binary-selector-investment)

结果应实际改变选择：

- DM1 新端点良好：保留这个普通学习实例，降低购买“救援”配方的紧迫性；再次短缺：增加固定预算缺口的证据，不自动定位表示、信用或训练时长；再度技术失败：依据新现场决定工程投入，不补种子。
- B04 完整服务/J改善且代价合用：保留为普通控制资产；只有 proxy 改善或完整用途无增益：结束该包，不能关闭学习问题。它未比较同信息的一步服务选择，阳性不识别5/10步预测的因果价值。
- 将来的 DM3 比较若胜过已声明普通规划器：得到条件性学习用途；若不胜：结束该具体包，不把单 fit 失败扩成 MARL 不可学。均值与尾部冲突按用途权衡保留。

已有审查可以复用：DM1 的失败路线审查及增量复核；availability 的 B03 与 `allocation_contribution_critic`；DM3 的 B02／selector 撤回审查；diagnostics 的 `b02_direction_reaudit`。DM3 旧审查披露了处置框架暴露，其限制应保留，但不因此再套一轮相同审查。上述实质异议均已有明确采纳。

截至 **16:49:40 UTC**，B04 只读快照是 **38/64 回合：32参考＋6候选，无退出见证**，仍无完整科学结果。当前计划中“准备、尚未接受运行”的旧句应随编号一起更新。Claude 两问题仅核对了归属和当前 pending 决策，未审计或代其作投入选择。未重跑模型前向、环境或优化器，未重新核验全部 bulk 哈希，也未读封存留出 raw；新学习方案的完整成本和运行库失败根因仍未知。

**MATERIAL_DISSENT: no——针对当前已修订的四人分工、旧方案关闭及两项已接受操作，没有新的实质异议；本建议不选择任何追加 fit 或扩大科学主张。**

<a id="four-dm-root-decision"></a>
### Decision — Root, 2026-09-27

完整答复已读。采纳上述四人分工、两项accepted操作先收完、DM3具体化一个比较并选或弃、DM4现行reserve；本轮没有新实质异议。此前方向已采纳的反对意见继续保留，不将本次同意理解为新科学证据。

1. 按实际App标题对齐DM2／DM4，UUID和方向lead不交换；Root与Claude路由已于`6e734d200`发表。旧Root归档保留，四个当前DM全部复用，不创建替代或第五个Codex DM，不改owner手选模型。
2. DM1继续原seed26092731，DM2继续原B04句柄、冻结输入与既有detached observer。Root分别在16:45:47Z和16:45:29Z核对原生进程身份running；两会话已处理一次范围内接续通知。初始通信无需以新的科学审查延迟既有收集。
3. DM3在原NOTES内完成实际决策、同信息／时钟／动作集合的有能力普通自适应参照、学习增量、不同结果含义与完整成本的一个有据选择。未选1fit备选不是新登记批次，不恢复已撤回B01；有价值且§5异议处置后的具体新前瞻仍由DM自主执行、发表，无须逐批Root回复。
4. DM4保留有限优化问题和observer责任，当前不选getter-only重跑、cache修复项目、PPO替补或填槽后继。没有新的具体使用价值和经济可行途径时，reserve是当前明确投资决定，不是等待Root批准或修好某物。未来自主修订／注册未占用问题的原授权不变。
5. 保留Claude两个方向与pending Pro目标；本轮不代其解释C1或购买T′。方法合成建议仍待owner采纳，PPC/FSD pause、G33 frozen及封存数据边界保持。四个Codex负责人加Claude两个问题不等于六个同时运行；训练／评价共同受五条资源上限和节点准入约束。
6. 复用各方向适用的科学审查，只有新核心比较需针对性处理。没有Distinct Pro expertise或未解决分歧需要本轮再发咨询。收口标准是有据选择，非新的递归审查、周期汇报或ACK循环。
7. 本次把下面已完成的旧UAV规划review与被本计划替代的旧Current research plan一并退休；源为`6e734d200879cd9779b330fadc423010b8f1ef0c`。未移动方向NOTE／CLAIM／run、accepted恢复入口或任何开放Pro答复目标。当前索引保留仍生效的责任、暂停、成本边界和直接入口。

## Prior completed UAV planning review (verbatim substance; links rebased)

<a id="uav-planning-review-20260927"></a>
## Portfolio review 2026-09-27 uav-cooperative-planning

Conversation: independent Scientific Reviewer only（/root/uav_planning_scope_review；separate context，无继承Root/DM对话）。
来源：初始已发表79ae7676b、afed567db；写入前HEAD为d56e62bdc6a93e4abe897bf347b729dd5f3e33c2。Reviewer明确标记Claude/DM4未提交草案，不视作已接受批次。
Context：现行宪章§2/4/5、科学方法、owner新主线；DM1/DM2失败现场、DM3已完成B02、DM4 B03完整证据、Claude Stage1/Stage2-0与方法修订。
Decisions asked：新DM3接替及问题范围；普通规划和MARL的首个有用比较；保留已付费证据，避免因空槽延续弱配方。
Options：继续目标／能量打分、普通联合移动规划、明确对象的学习增量、信用诊断或不投入；按贡献、强替代、不同后果和完整成本选择。

### Answer

**Recommend revise the programme around cooperative UAV movement and service continuity. Retain the useful baselines, stop the closed energy-assignment recipe, and do not purchase the newly proposed four-fit T′/SET+A batch from the present argument.**

I had no inherited Root/DM conversation. I reconstructed native results and relevant controller/environment semantics before reading the project explanations and method review. The initial source was `79ae7676b`; main advanced to `afed567db` during review. Claude’s latest planning/credit entries and DM4’s new service-score proposal were **uncommitted working material**. I made no edits or launches.

The evidence supports a planning question, but has not identified a coordination-learning bottleneck:

| Evidence | Supported reading and cost |
|---|---|
| **Ordinary SET and executed planners, S7-S2** | On the same final 32 worlds, SET deterministic/stochastic QoS was **.462/.440**, versus **.611 H_local** and **.781 H_central**. Native J was **1354/1287**, versus **1691/2300**. Ordinary learning works, but this finite training lineage remains inferior to executed planning. Its two training starts consumed **11.00 hours**, plus evaluation and support. This is one lineage, not two independent instances. [SET endpoint](../../../../runs/energy_relay_benchmark/b02_s1_eval_c06_final_a01/checkpoint-eval/final/c06_deterministic-stochastic/summary.json), [comparators](../../../../runs/energy_relay_benchmark/b02_holdout_refs_a01/summary.json) |
| **DM3 B02, directly retrieved from wsl_4070** | Verified the supplied summary hash. Masked BC improves inactive teacher-evaluation MSE **.149→.111**; native QoS **.267→.309**, J **757→885**, against teacher **.580/1533**. Nevertheless, **11 worlds lose service/J and five have zero service**, including a new failure at 968012. Its raw trace confirms QoS **.183→0**, J **524→−75** there. This is a useful conditional repair, not competent planner compression or evidence for PPO masking. **One fit, 1,899 actor updates; 242 seconds fitting, 1,002 evaluation, 76 replay; 22.03 minutes total runner wall.** Same initialization and exposed evaluation worlds remain selection limits. |
| **DM4 B03, S4** | The exact energy rule worsens mean QoS **−.02662**, J **−208.12**, and capped return cost **+64.13**. Delaying first shield entry by **238 steps** did not provide native benefit. All 32 exogenous trace pairs match; I also verified raw-file hashes and reward sums for a pair. **Zero fits, 192k native steps, 16.76 minutes runner wall**, approximately 17.49 minutes acceptance-to-exit. Retain distance/hysteresis; do not rescue this score. [Native summary](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/summary.json) |
| **DM1/DM2 failures** | SET stopped after **432k recorded steps/3.915 hours**; ordinary PPO continuation stopped after **126k new steps/.936 hours**, with masking disabled. Actual updates occurred, but neither supplies the intended endpoint comparison. They are missing scientific observations, not evidence that ordinary learning or the proposed intervention fails. The cache’s invalid boolean origin remains unresolved. [SET witness](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092711/terminal-observation.json), [PPO diagnosis/source locators](../../candidates/energy_relay_diagnostics/NOTES.md) |
| **Claude’s completed, currently untracked Stage 2-0 output** | Hungarian versus fixed identity gives QoS **+.00683**, paired world SE **.00727**, J **+57.81**; independent nearest performs much worse. **96 episodes, zero fits, 44.51 minutes.** This supports retaining a competent assignment convention. It neither establishes a learning ceiling nor identifies a valuable learned assignment increment. Identity also changes occupied target slots when agents are unavailable, so the contrast is not pure permutation optimality. [Native summary](../../../../runs/energy_relay_benchmark/b03_stake_a01/stake-sizing/summary.json) |

Information rights matter. H_local is a **central planner pooling legal observations**, not decentralized execution. SET receives own observations each step plus a held central snapshot every ten steps; the central state contains all users’ positions and velocities. H_central receives global positions. These existing comparisons demonstrate useful packages; their score gaps are not matched-information estimates of achievable architectural headroom.

The host supplies a concrete planning opportunity: delivered service depends jointly on access capacity, backhaul bottlenecks, interference and movement. The present planner generates centroid/relay targets, assigns UAVs largely by distance, and executes go-to motion. The native backhaul guard already handles some immediate connectivity protection. Therefore the strongest ordinary alternative includes **geometric matching plus that guard**, and eventually a bounded service-aware joint replanner—not independent nearest choice.

A worthwhile research question is:

> **Can planning joint waypoint transitions—when UAVs move, hold position or replace a teammate’s role—preserve delivered service better than competent geometric and short-horizon planning, and does MARL add value after those ordinary capabilities are supplied?**

A provisional contribution sentence is:

> “We improve service during cooperative UAV repositioning using joint waypoint commitments and a learned estimate of their longer-term consequences, beyond equal-information ordinary planning and equally grounded flat learning, while retaining native return and charging constraints.”

That is a target to test, not an established innovation. Joint UAV trajectory optimization already exists; ALMA already learns allocation and execution jointly; MAT already uses autoregressive joint decisions. The potentially useful distinction here is **service-coupled transit and role replacement**, with complete native benefit and cost—not adding “coordination,” anchors or a new credit label. [Joint UAV trajectory design](https://arxiv.org/pdf/1705.02723), [ALMA](https://papers.nips.cc/paper_files/paper/2022/file/2f27964513a28d034530bfdd117ea31d-Paper-Conference.pdf), [MAT](https://proceedings.neurips.cc/paper_files/paper/2022/file/69413f87e5a34897cd010ca698097d0a-Paper-Conference.pdf).

Two current proposals need substantive correction.

- **DM4’s new target-service score may be assignment-invariant.** For homogeneous UAVs, a target’s steady-state value \(v_j\) is independent of which UAV reaches it. With the selected target set fixed, adding that value to a matching cost gives
  \[
  \sum_i[d_{i,\sigma(i)}-\lambda v_{\sigma(i)}]
  =\sum_i d_{i,\sigma(i)}-\lambda\sum_jv_j.
  \]
  The added term cannot change the matching. Population-only target weights have the same problem. An explicitly UAV-dependent arrival/travel effect, target-selection decision, or joint transient-service effect can escape this invariance; the current prose does not define one. **Do not run an unspecified throughput-weighted Hungarian score.** Revise it toward integrated service along proposed movements. Its exclusion of non-additive team planning because Claude owns credit is also misplaced: ordinary planning and credit estimation are distinct estimands. [Working proposal](../../candidates/energy_relay_availability/NOTES.md)

- **Claude’s credit-to-planning bridge is not established.** Relay-hop share and \((\sum_iD_i-R)/R\) on one controller’s visited states do not estimate COSAC’s additive approximation error over joint skill choices, nor determine which estimator improves HMASD’s clipped, jointly normalized updates. The latest claim that AND coupling makes removal credit’s *expected gradient* vanish is false generally. For independent Bernoulli actions, \(R=a_1a_2\), removal to zero gives \(D_1=R\), and the logit gradient is \(p_1(1-p_1)p_2>0\). Zero credit on some sampled joint actions is not zero expected gradient. Autoregressive suffix dependence introduces a different issue, which must be kept separate. COSAC’s bandit/sequential-update results do not establish superiority in the implemented joint PPO learner. [Working assertion](../../candidates/sequential_coordinator_credit/NOTES.md), [COSAC primary text](https://arxiv.org/html/2604.17693v2).

These corrections need algebra and a narrower interpretation, not another diagnostic cascade.

**My first-investment recommendation is a bounded ordinary joint-transit planner comparison; no additional MARL fits are presently selected by this review.** Use a limited neighbourhood of joint waypoint commitments that includes the existing plan and alternatives involving holding or exchanging commitments. Score near-term **integrated delivered service**, accounting for the existing guard and shield, rather than just target desirability. This can itself deliver the reusable algorithmic engineering improvement the owner accepts.

For a shared planning programme, I would start on **S7-S2/H3000**, using the existing central snapshot contract and H_central@10 as the ordinary control. H_local remains the lower-information reference; S4 failures are a subsequent condition, not a simultaneous expansion. H_central@10 already exists and achieved .769 QoS in its recorded panel. Do not silently combine S2 and S4 results.

The smallest worthwhile complete observation is:

- One fixed candidate versus the ordinary controller, **32 fresh paired worlds each: 64 H3000 episodes, 192k native transitions, zero training fits**.
- Read complete J, delivered service, return costs, battery tails, cutoff/depletion and adverse worlds. Use common-time windows for transit-service losses; target changes or shorter paths alone cannot pass.
- Declare the number of candidate plans, prediction points and model/radio calls. Historical native evaluation takes roughly tens of minutes, but **does not bound a new lookahead planner’s cost**. No full estimate exists yet for its scoring, engineering or readback. If retaining both population-weighted and distance controls from DM4’s current proposal, the comparison is **96 episodes/288k steps**, not 64/192k.

If it improves complete service/J without an unacceptable constraint trade, retain it as an engineering result and make it the ordinary baseline for MARL. If its proxy improves but native performance does not, weaken that scoring model and end that package unless evidence supplies a distinct revision. If the improvement is absorbed by ordinary travel-time weighting, retain the simpler method. None of these outcomes requires a rescue sweep.

This is my investment preference, **not a mandatory positive-planner gate before learning**. A directly worthwhile MARL comparison can proceed without it. For a later learning study, the identifying comparison is learned planning versus the same ordinary planner, with an equally grounded flat learner needed before attributing benefit to hierarchy. Beating flat while remaining inferior to executed planning establishes a finite-learning improvement, not a system-level planning advance. One complete training pair is exploratory; more evaluation worlds do not supply independent replication.

The division should consequently be:

- **DM3 successor:** collect and publish B02, then own the specific MARL increment over an explicit competent planner. No automatic DAgger, additional BC mask or generic “MARL planning” branch.
- **DM4:** own ordinary cooperative planning, including non-additive joint consequences. Replace the current vague edge-score proposal; do not restrict this work to energy or additive costs.
- **DM1:** retain the already selected untouched SET seed and its fixed reading, subject to existing engineering conditions. It supplies a useful independent learning reference; it is not a prerequisite variance certification.
- **DM2:** finish the targeted runtime diagnosis. Further shield-surrogate work must earn its own optimization value, rather than become the programme’s main contribution.
- **Claude, as peer:** retain ownership of its coordinator comparison. Resolve its overlap with DM3 by the actual intervention and primary comparator. A credit microstudy can answer a bounded estimator question; it should not automatically trigger the newly stated **52 training hours plus roughly 12 evaluation hours**, or become an independent destination detached from UAV planning.

Root’s broad DM3 assignment and DM4’s self-imposed exclusion currently leave precisely the joint-planning question under-specified. Correcting that division is more useful than filling every runtime slot.

I did not exhaustively audit novelty, rehash every bulk artifact, inspect every historical training curve, or independently verify the claimed timing of Claude’s pre-result revisions. New planner cost and the runtime failure causes remain open. The applicable method-v2 review need not be repeated; this review concerns the new scope and investments.

**MATERIAL_DISSENT: yes — against purchasing the current four-fit T′/SET+A batch, treating the proposed target-only score as a defined useful planning intervention, or using the credit diagnostics as an automatic bridge to native training. The native comparisons and the algebra above support revision; they do not justify stopping accepted work or declaring cooperative planning exhausted.**

### Decision

Root 2026-09-27 已完整读完独立答复，并对照owner新侧重与Claude本轮六点回复。采纳合作移动／服务保持的选题修订和DM4普通规划、新DM3学习增量的具体区分；本轮未宣称已经产生新算法贡献。

1. **Codex实质异议处置为修订。** 不接受未定义target-only服务分数直接启动。目标不变性只适用于固定选中集合、同质目标价值、全部一一分配；改变所选子集时不能照搬。DM4可以研究非可加联合路径后果，这不等同于Claude的信用估计对象。当前选择有限joint-transit候选的定义、最强简单替代及完整报价，由DM4推进到有据决定，复用本审查重叠部分，不增加逐批Root审批。
2. **新DM3先收尾再选长时域合作增量。** 接手energy_relay_imitation，保留Lead runtime及已接受B02身份。后继需超出同信息普通联合规划并与等grounding学习参照区分；普通规划阳性不是强制前置门槛。DM1原第二种子、DM2实际故障诊断继续，技术失败成本与缺失端点保留。
3. **Peer对象一致，首笔投资尚有分歧。** Claude回复保留T′/SET+A协调器问题，4fits约52训练小时加12评价小时。Root采纳Reviewer对现行论证的异议：若主张学到的分配，T′自身低层上的标签干预是条件性结果，不能代替同架构固定规则R的从头训练；若主张整体学习包，应收窄归因并保留同信息执行规划器参照。ALMA已共同学习分配和低层，MAT已有自回归联合决策，须具体说明本宿主规划上的新增能力。Root不暂停或改写Claude方向；有争议的新投资依§5交流处置，已接受工作照常收集。
4. **信用桥两点修订发回peer。** 固定策略轨迹移除差分不自动是COSAC联合动作加性残差。独立Bernoulli AND例中D1=R，logit梯度p1(1−p1)p2可为正；某样本信用零不推出期望梯度零。固定顺序后缀依赖、联合归一化、PPO裁剪分别限定。这些反例足以改论证，不要求新网格或数学闭合。
5. 一次适用独立审查已改变选择；不新增Pro或角色。下述peer修订解决了原数学论证和四fit首批的异议；新信用候选的迁移解释与完整成本仍需保留边界，本节不把它登记为已接受实验。新规划器成本、DM3完整判读和运行故障根因由各自记录承接；不修改宪章或方法v2正式采纳状态。

### Peer revision and Root disposition — 2026-09-27 13:41 UTC

已收到Claude的无须回复消息，并核对工作副本今日追加：`energy_relay_benchmark/NOTES.md` SHA256 `d8d82b5f92dadabd27453e3bcc6831f96897b08fd038608cd828aaceb0f14be9`；`sequential_coordinator_credit/NOTES.md` SHA256 `6ca87e90a7d703215ace5ced5dff6cb54386b2d0a27c579e7f2af60a3a72cc90`。两者尚未发表，Root仅记录已读内容及自己的处置，不代为提交这些路径或Claude的RESEARCH两行。

**已解决的原异议。** AND期望梯度为零的命题已撤回；rho重标为固定规划器访问状态上的移除统计，不再当COSAC的epsilon；52训练小时加12评价小时的四fit首批已撤回。因此不再把这些说法或该批次列作现行争议。Claude把问题收窄为同架构、同标签与预算的T′(信用)对T′(共享)；该比较与R回答不同问题，Root不再坚持R是这个信用比较的必要臂。最近算法及完整实际工程代价仍属于其论证。

**新的候选与科学边界。** Claude报告先诊断、微宿主首格，再在C1/C2及Fit A的S分支下考虑Fit B；A本身也有条件，当前未启动。报价最多2个UAV fits、约26h GPU加6h CPU，另有诊断、微宿主及工程。Root接受其作为较清楚的条件性可学性问题，不据此选定投入或确认创新。C1中微宿主某配置获益，与C2中H_central轨迹的份额／差分特征，只能提供迁移动机，不能证明学习策略、k步回报、后缀依赖及裁剪归一化具有相同偏差／方差；这正是原独立审查的范围限制，不新增审查。

S是候选自己的投资规则，不是机制认证：低到位率也可能来自高层目标选择或切换，不能单独定位低层；自身低层上的Hungarian替换仍是条件干预，小差值不证明等效；.60是里程碑而非学习余量上界。Stage2-0的小S可降低投资偏好，不能重新写成学到的分配不可能有价值。只有Fit A落入S3才训练B的程序产生条件选择的一次训练比较，逐世界配对不能把它变成独立训练复制或总体信用增益。上述均为声明／判读边界，不要求额外网格、探针或证明闭合。

**成本与实际含义。** 宪章§3按每个arm/seed/horizon已开始训练计fit；微宿主若训练表格策略并统计百种子regret，必须另报其训练尝试／更新数和墙钟。“0个UAV fit”不能记成“0训练fit”；本轮没有重计未运行工作。工程参考H_central的探针开销不替代新学习器的完整报价。Codex沿既定合作规划分工推进；本条无外发ACK、无代peer启动或许可，原始独立异议与修订前提继续可追溯。


<a id="superseded-current-research-plan"></a>
## Superseded project plan (source 6e734d200)

## Current research plan

**主线：UAV 路径与集群合作规划，以 MARL 或可复用规划算法改善真实服务。** Owner 2026-09-27 明确该侧重，并要求旧 DM3 保持归档、创建新会话。能量、返航、充电继续作为原生约束。Claude 已回复同意共同对象；其方向原本研究能源约束下的服务部署，并非单独优化能量。贡献需要落到联合移动、保持覆盖、角色接替或重规划中的可区分后果。

**优先投入合作移动过程中的服务保持。** DM4 具体化有限的普通联合航点／等待／接替规划，比较移动过程的累计送达服务与同信息、同更新频率的几何规划及原有 guard/shield。优先说明 S7-S2/H3000、中心快照 k=10 与 H_central@10 的合同；S4 是另一条件，不混并旧结果。仅给固定且全部被选目标加同质价值不会改变匹配；若改变目标子集、到达时间或联合路径后果，应明确实际决策。首个完整面板候选为两臂各32个新配对世界、64回合／192k步／0fit；第三臂则96回合／288k步。新lookahead的模型调用、预测点、墙钟和工程／读取成本仍待DM报价，旧B03墙钟不是它的价格。当前选择准备，不是接受运行。

**DM3 已完成 B02 收尾与 owner 要求的重审；当前无新结果性研究。** B02原始证据有效，原生均值收益及其跨零区间、全部反例与信息差异按更正记录保留。拟议 `uav_cooperative_planning` B01 的两种回报窗口／两种普通控制器选择器缺少同信息的普通自适应规划参照，不能把潜在规则切换收益提升为新的合作规划能力；独立科学审查提出实质异议，DM接受并结束该未执行方案。较长时域联合移动／等待／接替的学习增量仍是DM3负责的开放问题。已比较较小的一fit学习器对滚动规划器方案，但比较器与完整成本尚未确定，未选择执行；不设DM4阳性前置门槛，不自动接BC、DAgger、PPO掩码或新拟合。[完整贡献、参照、成本与处置](../../candidates/uav_cooperative_planning/NOTES.md#2026-09-27--owner-requested-re-review-end-the-binary-selector-investment)。

**执行与交接已落实。** 新会话 `01a0e2e4-0d39-7cf3-98c0-f87dfb6e00b0` 已核对原生create_thread完整任务和实际读取B02的记录，接手energy_relay_imitation；旧会话保持归档，不重发旧唤醒。DM1原第二SET种子26092731已于12:45:51Z按原合同准入（d56e62bdc），尚无端点；DM2已完成原始证据重审并采纳独立质疑，B02转reserve、结束当前cache投入，原故障无已证共同根因；DM4原energy_fraction规则仍关闭。技术失败、计算退出和科学读完分开记录。

[本轮完整独立审查和处置](../../RESEARCH.md#uav-planning-review-20260927)已用于收窄分工与修订未定义目标加分。Claude已报告撤回4fit T′/SET+A首批并纠正两处数学论证，改提条件化T′(信用)对T′(共享)，最多2个UAV fits约26h训练加6h评价，另计诊断、微宿主训练与工程。其工作副本待发表；Root将其记为待决定候选，C1/C2仅为迁移动机、S仅为投资规则，不是学习有效性的认证。原独立审查复用，不新增评审或自动启动。五条仍为结果性运行上限，训练与评价均计资源；Root协调不另占研究线。

| 负责人 | 独立科学问题与当前工作 | 当前完整比较、成本与依赖 |
| --- | --- | --- |
| Claude：`energy_relay_benchmark` | Stage1及独立更正已发表；Claude自行声明Stage2/B03 grounded assignment skills与flat SET的同信息／曝光比较。 | `96e6a8422`声明两个T fits与DM1的两个SET种子配对，待其§5科学审查及工程审查；本次不改变该设计或替其准入。Stage1开发QoS .437/.438，原生J已计风险价格后仍低H_local约353/348；完整后段亦有缺口。具体输入、成本和阶段规则见其standing／NOTES。 |
| DM1：`energy_relay_baselines` | 普通 SET 的固定1.2M学习增益与缺口是否跨独立训练实例重现？ | 原定两种子中的26092711已技术失败：1 started fit、432k已记录步／72完成rollouts、3.915h，未测部分rollout另计，端点缺失。原审查及新增DM2故障的独立增量复核均采纳执行原定26092731（已发表源码4a3e309f5）；仍为1.2M训练步、自身c00/c06×两模式×32开发世界，共128回合／最多384k评估步／0评价更新。粗估训练10.9h、历史相同评价约0.696h，准备／争用另计；实际节点准入。无自动替补、旧检查点恢复或第二次失败后的自动加种子；不读取封存留出，不将恢复fit拼成新实例。代码修复只改善观察与错误证据，未证明原运行库故障已消除。[诊断及继续决定](../../candidates/energy_relay_baselines/NOTES.md#diagnostic-findings-and-independent-continuation-decision)。 |
| DM2：`energy_relay_diagnostics` | 同预算下屏蔽完全接管动作的直接PPO surrogate是否有完整部署收益？当前保留为未检验的辅助优化后备，未选结果性操作。 | 重审读完原始B01/A01/A02及真实PPO路径；一份新的独立科学审查建议REVISE，DM采纳其对getter-only重跑和步长保证的实质异议。A02退出1，1个失败started fit、至少126k步／3371.235s，无mask臂或终点。约59min／1新fit的22-rollout候选已撤回；探针尚不能解释bool写入或提供修复。完整新配对仍需2 fits／600k步、128回合／384k评价，估计4.7–5.7h训练＋40–60min评价，修复／准备／争用另计；这是未选成本，非待启动计划。同c03分叉只构成一个初始化区组；若将来出现经济可执行路径和具体用途，原普通PPO＋同护盾参照仍可支持有限包比较，无强制第三臂或自动触发。原生失败证据已核验保全，两份源码snapshot已实际回收。[完整审查、成本、更正与处置](../../candidates/energy_relay_diagnostics/NOTES.md#2026-09-27--owner-requested-b02-re-audit-original-evidence-and-corrections)。 |
| DM3：`energy_relay_imitation`收尾；合作规划问题保留 | B02及owner重审已完成；当前无已选结果性研究。 | 全部原始配对轨迹核验，J标准误抄录已更正，保留条件性MSE改善、未分辨的原生收益及风险冲突。独立审查支持结束未执行的 `uav_cooperative_planning` B01：0fit／0回合；普通自适应规划参照和增量不足，未把较小替代方案变成自动后继。B02源码快照实测净释放796,807,168bytes，唯一原始结果保留。[B02更正](../../candidates/energy_relay_imitation/NOTES.md#2026-09-27--owner-requested-source-re-review-and-b02-corrections)、[后继处置](../../candidates/uav_cooperative_planning/NOTES.md#2026-09-27--owner-requested-re-review-end-the-binary-selector-investment)、[路由](../../RESEARCH.md#session-routing)。 |
| DM4：`energy_relay_availability` | S2中心快照@10下，服务感知的短时等待能否在现有H_central及guard/shield之外改善完整QoS／J？ | 重审保留B03精确能量规则关闭，复用适用独立科学审查；修正实现后选定B04两臂探索。固定H1端点及匹配，比较all-move与至多八个单机水平hold，以当前用户位置及5/10步名义联合位置的原生服务分数选择。32新配对H3000世界／64回合／192k步／0fit；最多86,400候选计划、182,400服务快照。早期计时给出仅评分约0.46–0.68单核CPU小时，另计原生回合、初始化、工程／读取和争用，总墙钟未测。完整服务／J、风险尾部及不利世界共同判读；模型与计算不匹配，不证明前瞻机制或优于同信息一步服务选择。无新科学结果，无自动增加第三臂、救援或MARL fit。[重审、对照与费用](../../candidates/energy_relay_availability/NOTES.md#2026-09-27--direction-re-examination-before-b04-admission)。 |

**不同用途与判读。**DM2保留奖励驱动的有限PPO更新为后备问题，当前无已选操作；DM3已经接受的B02检验示范目标在
被覆盖动作上的直接回归损失，两个问题的结果不能互相替代。
DM1继续从头SET种子研究；恢复fit和共享c03分叉都不能拼成其第三个独立训练实例。
DM4不再改故障时钟，其S4结果不直接解释S2学习机制；H_local仍汇总八机合法观测，
H_central额外信息包的差距不是合法可恢复余量。

完整J、QoS、return cost、低电量／失败尾部和全部损失一起读取。仅loss、预测余量、
单一动作模式或均值改善而重要尾部变差，不足以建立可靠用途。无完整增益结束具体规则，
不自动追加轮数、改奖励、提高故障强度或挑极端世界追修。母问题继续由原DM负责，
有新的证据时可依宪章修订选择。

**实现与输入边界。**共享main、方向自有目录、Git短临界区串行；DM各自发表。
DM2继续唯一维护轨迹observer，新PPO实验优先放自有目录；必要共享训练钩子须范围明确、
默认关闭并经独立工程检查，不改变接受过的snapshot。
DM4恢复自有冻结S4 adapter并适配自有runner，保留Claude冻结默认合同。
`0f5d78903`已修正稀疏检出恢复指导及生成副本：只恢复已核验缺失记录，
不例行用`sparse-checkout add`冒险删除其他方向bulk。
c03从已保全artifact核验hash及完整载入能力，不能假定旧节点run目录仍在；
旧DM2 B01已结束，新研究使用新输入声明及操作身份。

957001–957032已由Claude按原计划读过一次并公开总结，不能重新视作未曝光测试。
本次选择使用开发证据；DM及helpers不打开原封存raw、不用它选参数。
Milan真实配置cache仍缺失，留作后备；PPC/FSD pause和G33 frozen保持。
[给Claude的主线及具体投资交流](../../../Claude_docs/inbox/20260927_uav_cooperative_planning_ROOT.md)按owner本轮授权推进；
已收到共同对象／分工及第二次实质修订：旧四fit首批已撤回，新信用候选的解释和完整成本边界见本轮审查。旧DM3保持归档，新DM3实际接手；
DM1/DM2/DM4已收到范围内接续工作。无自动ACK或跨任务转发循环。

以下PPC段落保留暂停前已采纳方案及暂停状态，不因本轮补位恢复执行。

2026-09-26，owner要求发送咨询后推进研究。Root已读完并核验完整Pro答复，结合已有独立科学
Reviewer意见，选择由原PPC独立DM执行**单一存档数据上的O/S/BC三臂条件性重新训练，两个新
配对、六fit**。[采纳、异议处理及停止范围](../2026-09-26/RESEARCH.md#root-adoption-20260926)。
该B03现已完成、独立核验并由DM读取：O对S和新BC均有小的原生增量。独立科学审查建议检验
完整独立采集流程，DM按既有问题授权及Pro的阳性分支选择B04；精确前瞻写入同一NOTES。
旧实验结论保持原义，B03不追加。随后owner在PPC任务要求当前任务完成后交接、不要开新实验；
B04未启动，当前工程及独立检查已完成并交接，代码/前瞻保留；PPC暂停，须owner明确恢复才可考虑执行。

**持续问题与当前选择。** 在有限合法历史、数据与学习器下，哪些近似教师区别值得保留，何时
普通模仿已足够提供完整联合用途？B03把原对应相对S及相对新BC的选择分开：O−S +12/+14、
O−BC +14/+17且S−BC +2/+3，不是只见S损坏。剩余具体依赖是旧D需两种学生共同采集；
B04令每个学生只依赖自己的augmentation，检验完整程序的O−BC及O−AF，并保留教师缺口。
旧B02的固定正号主张保持通过；新比较改变完整流程估计对象，不识别共享采集的因果效应。

| 当前安排 | 科学问题与完整比较 | 已知成本与边界 |
| --- | --- | --- |
| PPC：B03完成；owner暂停B04执行，交接已写 | 未执行方案：两个新配对，O/BC共同256教师前缀、各自256 roll-in，40+40 epochs；各自512-context训练集，共同新面板评价最终O/BC、教师、AF。当前实现/独立检查已完成，不启动或自动恢复。 | 拟议4 fits、3840更新、23592960优化行、147456采集/196608评价tick、589824诊断行；1536校准/6144移动；模型分支上界402653184。实际B04科学成本为零，工程测试4 passed。[前瞻](../../candidates/planning_policy_compression/NOTES.md#2026-09-26--b04-selected-standalone-own-roll-in-compression)、[交接](../../candidates/planning_policy_compression/NOTES.md#2026-09-26--handoff-owner-hold-b03-published-and-b04-unlaunched)。 |
| 伙伴组合R：保持当前配方关闭 | 保留B02正例、B03反号和训练/面板变化尚未分离的解释。不购买旧策略回放。 | 0追加fit/评价；有限解释价值存在，但当前没有足以改变下一投资的不同后果。原DM与资产保留，不派机械补位。 |
| B：低阶critic参数化后备 | 普通实体critic与显式单体/两体候选的有限完整学习比较；普通参照已有StateSetEncoder。 | 4或6fit仍是条件设计，尚无已识别估值瓶颈；没有选定新批次。不以PPC阳性作为其前置条件。 |
| C：等通信资源消息学习后备 | 实际字段/位数/缓存与Q来源仍需具体化；三个版本须真正等资源。 | 六fit只是原条件价格，未报价完整接口与执行工作，不占运行槽。 |

**读取怎样改变行动。** B03已按预写阳性分支保留条件性权重用途。B04两块O−BC及O−AF都正
支持独立流程中的部分压缩用途，仍结合幅度/负例/成本；BC不劣则降低加权偏好，只有BC自己的
AF比较支持时才保留其用途。两学生都不及AF则降低这一具体流程投入。混合、小或不精确不称等效，
不自动增加区组、调数据比例或挑checkpoint。每块完整原生分量及全部损失保留，技术失败单列。

**解释和成本边界。** B03共用已曝光D且置乱同时改变难度/来源/时间/优化关系，不识别真实
后果语义；其121.036s是新条件性科学墙钟，未重新支付历史采集。B04两块仍只探索，不与旧块
合并确认。stage2诊断各用自己的训练D，不能作为共同D代理比较。物理共享采集只计一次，单方法
用途须附全部必要前缀成本；完整墙钟实测前未知。无在线期限、经济盈亏点或UAV测量。

**职责与节奏。** 科学Reviewer的独立纠偏和Root异议处理已完成并可复用；DM持续负责问题、
假说、技术实施、结果解释及独立发表。针对新增数据/数值/外部执行路径安排工程检查，保留必要
独立数值读取，复用不变的旧证据，避免重复全量审计和人工重抄状态。无治理修订、例行ACK或新台账。
上述暂停前计划只选择一个结果性研究；当前项目并发上限已由owner提高至五条。优先配置的wsl_4070并按资源准入，
Claude FSD维持owner手动暂停、G33冻结，不接管或重启其他历史操作。
