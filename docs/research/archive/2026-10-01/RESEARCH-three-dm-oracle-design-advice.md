# Completed temporary Oracle design advice — 2026-10-01 PDT

This is the complete returned advice from the temporary Root adviser, not an independent
scientific review, an execution acceptance, or a replacement for the current research plan.
The native adviser completed this assignment; DMs retain the scientific questions and execution.

- Parent Root: `01a0f779-ace2-74e1-85ad-e0997b61d505`.
- Adviser: `/root/successor_allocation_review`, native UUID `01a0f77c-49e7-7292-91a3-2d8fa8fb1975`.
- Actual resumed turn: `01a0f9f6-a26a-7d90-9963-0a27dca186ef`, `gpt-6-astra`, `max`, verified by Root.
- Final-answer UTF-8 bytes: 13835; SHA256 `84df55fb2298b8ff2820f7518e7ac86bae1cca01b2b5bcf6400ff2127a7ad802`.
- Native source: `/mnt/c/Users/fires/.codex/sessions/2026/10/01/rollout-2026-10-01T05-41-52-01a0f77c-49e7-7292-91a3-2d8fa8fb1975.jsonl`; final assistant answer extracted without content editing.

## Assignment context (Root summary, not a verbatim prompt)

The owner asked to continue research with three substantive DMs, reserve a continuing DM for
generalized open/learned decision assistance beyond Laya, and use a temporary Astra Max Oracle
to relieve Root's research design and allocation work. The adviser was asked to construct concrete,
evidence-based comparisons from retained positive and adverse results, price the complete work,
consult primary literature, and return suggestions to Root. DMs supplied existing source and asset
facts. The adviser did not own execution, become a fourth DM, or approve individual fits.
The owner's subsequent status question emphasized that positive pre-handoff capabilities remain
available; it did not pause the resumed work.

## Root reading and disposition at publication

Root read this complete final answer and the preceding complete proposals. The A/R study was
selected in `e2c99cdb7` after the separate ResearchCritic's complete review; its full review and
DM disposition belong in the direction notebook. The S7 assignment and learned-search-branch
proposals are undergoing their own one-time independent scientific readings and precise source
contracts. This archive records advice completion, not unobserved acceptance of those runs.
Current choices and original sources remain in [RESEARCH](../../RESEARCH.md#three-dm-decision-assistance-20261001).

Root directly checked the load-bearing primary passages: SATzilla §§1.1–1.2 and §2.1
(instance features and past performance used for pre-execution selection; ridge/quadratic features),
Multiagent Rollout §1.1 (actual base-policy cost-to-go is used by the improvement result), and
the earlier Deep Sets §§2.2–3 plus MARL-0571 pp.3–4. These motivate constructions, not promised
UAV improvements. No source-selection argument turns the proposed short-horizon model into an
exact rollout guarantee or static prediction into a native-service result.

The adviser's CPU/support figures are forecasts. DMs are closing their actual test and reader
counts; limits are declared stop/reassessment boundaries, not measured runtime guarantees or
permission to silently expand. In particular, S7's necessary per-tick hold-xy NaN adapter and
current-visible-only user set must preserve actual controller semantics. Retained frozen students,
ordinary control, prediction, uncertainty handling and continuity results remain valid with their
original adverse evidence and costs.

## Complete original adviser answer

建议保留三个互补问题：**经验怎样帮助规划器少做无效搜索；结构怎样帮助学习器泛化到新几何；已有预测怎样改善有能力的普通控制。** A/R 已由 Root 选定；其余两项建议各买一次完整比较，随后按结果决定具体机制去留。三个 DM 不等于三个新模型，也不要求三批同时运行。

本答是临时方案提出者给 Root 的建议。我继承了此前讨论并参与构造，**不属于独立上下文评议，不能代替另行进行的 ResearchCritic 审阅**。后续合同、实施、完整阅读由 DM 负责。

1. **长期决策辅助：用既有搜索经验选择尚未执行的下降分支。**

   长期问题是：可复用的学习经验能否与普通规划合作，改善新世界的决策质量、数据使用或质量与计算的取舍。首次研究不再训练网络近似那个已经很便宜的八菜单静态评分，而把学习放在真正尚未支付的搜索步骤之前。

   已有支持来自完整普通规划能力及其保存的搜索经验。旧 64 个 gate 世界保留了 192 个 relay top-3 start 的初始值和最终静态结果。初始排名第一最终获胜分别只有 16/32、9/32；三个已选 start 的最终 reward spread 均值为 .02496/.02961。这说明“当前分数最高”与“下降后最好”可以分离，**没有证明条件预测一定可学，也没有给出 native 收益上界**。旧两类搜索全部在预算前收敛，实际 flat 约 869、relay 约 1,135 次查询，不能把两次 3,000 上限当常态成本。

   建议固定四个程序：

   - **G**：完成原 flat 搜索及 relay 全部初始候选评分，执行原 top-3 中初始 static rank 0 的一个下降分支。
   - **B**：用旧 64 世界的最终静态结果，选择平均最好的一项固定 rank；新世界仍只执行这项。若 B 与 G 相同，明确列为别名。
   - **L**：用同一份旧数据学习 final gain；在原三个 starts 中，按 `initial_reward + predicted_gain` 选择一个分支。
   - **P**：原完整 flat→relay、三个下降分支的规划器。

   四者保留相同候选生成、初始静态评分、匹配和完整 H500 executor。G/B/L 只执行被选分支的**原三分之一剩余预算 share**，不重新分配未用预算。所有在线前置工作照付，不能把 P 已完成的搜索免费交给 L。

   L 首次采用一次确定性、低复杂度拟合即可：建议固定物理摘要及二阶项的 ridge，训练标准化、λ=1，无调参或架构搜索。输入限于选择时已经取得的初始 reward、coverage、potential、kind/k/rank，以及布局、用户距离、跨度、高度、匹配行程；不得使用最终结果、接受 moves、消耗查询数等未来量。具体摘要字段由 DM 在合同中一次固定。192 行来自 64 个世界，只有**一个拟合资产**，不能将新测试世界数解释成训练复制。

   主科学比较是 L−G、L−B 的完整 J/C 和成本，以及 L−P 的质量与冷启动完整延迟取舍。预测误差和 start 排序是中间结果，最终还要经过下降、目标匹配及完整飞行。
   
   - L 有条件选择价值且 native 质量有用：支持继续发展经验辅助搜索。
   - G/B 同样好：节省主要来自普通的少搜分支，不能归功学习。
   - static 排序改善而 native 变差：这个静态目标不足以支持当前用途，停止该组合。
   - L 无法泛化：结束这个资产/表示配方，长期决策辅助问题仍由同一 DM 持有。

   这与 SATzilla 的直接桥梁是“实例特征及既往表现→预测各算法结果→在付运行费用前选择算法”。这里实例是世界与 start，算法是固定下降分支，预测对象改为有限预算后的静态 reward；论文并不证明本任务存在收益。[SATzilla，§1.1–1.2](https://arxiv.org/pdf/1111.2249)

   **完整预测价格**：64 个 fresh 世界×至多 4 臂×H500＝128,000 native steps；加最多 16 个完整工程 audit，共 **136,000**。零新训练标签查询、一次 fit、零新权重/GPU依赖。按每程序两次搜索及路由查询、worker 与 reader 都计入，保守静态调用上限为 **3,264,544**。完整 CPU 预计 **1–3 小时，上限 6 小时**，支持工作 **8–14 小时**。旧数据的 128,288 次搜索查询是沉没生成成本，仍须列出。

   尚需正常落实的实质事项是源绑定和分支适配：旧 gate 为 `f589523191c670e215e3d719fc4f2cd01492c301`，旧/今 planner 哈希不同；DM 的局部 diff 显示默认候选及下降语义保留，但未核完全部传递依赖。`n_starts=1` 会改变排名选择及预算，不能直接冒充方案。上述 audit 已为正确实现这个差别计价，不需另买前置科学诊断。

2. **数值决策泛化：区分计算几何特征与利用关系结构。**

   这项是有限的能力研究。B01 的 N 确实拟合了训练集，训练 regret 约 .0005–.0008，而 fresh test 约 .10；L-F 训练拟合更弱。二者不能归为同一种失败原因。与此同时，普通 static 在 384 个世界中 341 次达到菜单最优，且静态评分本身增量约 4.3 ms；“网络将节省大量在线成本”没有成为可信前提。

   首次比较保留原八菜单、t0 信息权利、H500 后果及三块原训练数据：

   - 原三个 N final checkpoints 作为冻结参照，不重新训练 N。
   - **A**：完整 raw geometry 加确定性相对位移/距离关系，flatten 后评分。
   - **R**：取得与 A 逐元素相同的信息，用共享实体/关系计算及汇聚输出 candidate score。

   DM2 已将建议闭合为共享 **5,377 维** tensor，A **348,417** 参数、R **208,449** 参数，保留 row ID、UAV initial→assigned-target 配对和 BS 关系。这里报告的是 DM 的具体构造，不是我对其实现的正确性认证。

   A−N 判断增加几何计算后的表示组合；R−A 判断同一输入下关系共享的组合价值。参数数目和计算结构不同，因此即使 R 获胜，也不是纯“对称性因果效应”。用户原顺序带有五个 cluster-block 的弱线索；不随意删除，也不把 UAV 重标记、构造器 tie 或边界旋转假定为严格物理对称。

   每个新模型三块独立训练，仍用每块 256 世界、64 epochs、batch 32、原 Q/.02 soft targets及相同训练曝光。旧 B01 test 已曝光，只作 development；重新购买三块各 128 个 fresh 世界的完整八候选 H500 后果。logits 经固定 argmax 成为实际布局选择，最终比较 native coverage/regret、其他原生指标和完整决策成本。

   - R 在 fresh 世界优于 A，而不只是训练误差下降：支持关系共享的条件泛化能力。
   - A≈R，二者优于 N：证据主要支持任务几何特征组合。
   - 仅训练改善：这个固定学习构造停止，不自动增加数据或架构。
   - 超过 fixed、仍低于 static：可以保留能力进展，不能据此默认部署。

   Deep Sets 提供的是共享变换、汇聚及条件输入的架构桥梁；本题保留身份和生成顺序信息，不照搬其集合不变性定理。[Deep Sets，§2–3](https://arxiv.org/pdf/1703.06114)

   **完整价格**：6 fits、3,072 updates、98,304 training contexts；零新增训练标签。fresh 八菜单后果、full-planner 尺度参照及工程 audit 合计最多 **1,736,000 native steps、2,307,840 static calls、9,984 endpoint/reader contexts**。初估 **1–3 CPU 小时，CPU/GPU 上限分别 5/1 小时，支持 10–16 小时**。应计候选构造、匹配、特征和完整推理；缓存不能变成免费在线计算。Root 已根据另一个独立 critic 选定本研究，无需等待另外两项。

3. **S7 预测用途：保留 C 的当次布局，让预测选择服务 UAV 的移动分配。**

   这项直接发展已有正能力。B09 的 F−H 为 **+65.974 J**，但 F−C 为 **−454.277 J**；world 28 有 F 完整超过 C 的正例，world 31 有大幅 F−H 增量却仍低于 C。world 12 已有充分回程仍显著亏损，world 21 的零服务也不是 F 相对 H 造成。故旧“只在选中预测零服务时回退 C”的高价合同仍不是首选。

   同时，B08 已经试过把未来位置交给普通几何规划，V−M J 为负。新问题须落在不同的真实选择上：**既定目标之间，哪些服务 UAV 应沿哪些路径移动？**

   建议完整比较 **C / H_A / F_A**：

   - 每 30 tick，在本臂真实合法历史上按原 C/P_BS 生成当次 relay、service、ring 目标及普通分配。
   - 候选 0 是普通 C 分配。其余只交换两个实际被分配 service 目标的可动 UAV；relay UAV/targets、ring、NaN及目标多重集均保留。
   - 最多六名 service UAV，故最多 15 对交换加 baseline，共 **16 候选**；不足两名时保持 C。
   - H_A/F_A 使用同一候选菜单、30 tick nominal motion/charging 和原三个采样时刻的 QoS/return score。H 保持当前点位置；F 对**相同当前 canonical 用户集合**使用已有关联速度做 10/20/30 tick 外推。历史仅供速度，未观测旧 tracks 不进入评分。
   - 仅 literal float64 `score > baseline_score` 才替换；同分保留 baseline，非 baseline 同分固定 lex pair。不复用旧 travel tie-break。
   - 在当步动作生成前写回实际选择的 targets/last_plan，下一轮迟滞继承真实选择；时钟、tracker 不重置，真实 shield 每 tick 仍只执行一次。

   “保留 C 布局”仅指**该臂该次历史所生成的布局**。闭环历史分离后，各臂布局当然可以不同。

   普通参照是 C 的距离/Hungarian/300 m 迟滞分配，以及 H_A 的同模型、无未来移动重评分。主读 F_A−H_A 的预测增量及 F_A−C 的完整使用价值，另读 H_A−C。除了 J/QoS，必须保留个体服务/未服务、route、耗电与充电、reserve、末端风险，以及 proposal→submitted→physical 的实际曝光。

   - F_A>H_A 且完整收益优于 C：支持这种具体预测用途。
   - F_A>H_A、仍低于 C：保留有限预测能力，停止这个融合配方。
   - H_A≈F_A、二者都好：普通分配重评分有用，无需归功预测。
   - 少有实际不同动作：当前受限动作空间用途小；不能扩大为预测无用。
   - 主动产生负作用：停止当前组合，不自动增加搜索、触发器或预测模型。

   有限动作 lookahead 是方法桥梁。Bertsekas 的 rollout 改善性质依赖基策略的完整 cost-to-go；我们的 30 tick 近似缺少该条件，也省略部分 native guard、association 和奖励过程，因此**没有“不差于 C”的理论保证**。[Multiagent Rollout，§1.1](https://arxiv.org/pdf/1910.00120)

   **完整预测价格**：32 个 fresh 世界×3 臂×H3000＝288,000 native steps；加最多 8 个完整 audit，共 **312,000**。worker+reader及保守 audit 上限共 **230,400 candidate forecasts、6,912,000 nominal ticks、691,200 RF samples**，零 fit、零新权重、零阈值扫描。CPU 预计 **4–8 小时，上限 12 小时**，支持 **12–18 小时**；这是新构造的预测价格，不是沿用旧 8–24 CPU 小时合同。

   源接口确有两个必须处理的缺口。旧 `_assign_targets` 丢掉目标列索引，不能按最近坐标猜 service role；须保留实际 solver `(row,col)` provenance。C 的 NaN 目标表示逐 tick 保持当前 xy、向 z100 移动，不能用 decision-start xyz 填充，否则返航释放时改变语义。DM 已识别所需 direction-local adapter；这些属于本次完整工程工作，不另设诊断关口。

已有正面资产应继续参与判断。S_L1−G 的 **+.023431 J、服务 +1.868** 说明指定普通随机评分控制未吸收其全部价值；B06 又显示其收益依赖完整使用法，同时保留 outage 和质量代价。普通 full-consequence、静默移动、S7 预测以及 U32 的条件收益也仍有效。这些结果支持继续发展能力，**不意味着每个正例都应马上追加一批**。当前配置中，S7 直接发展预测正例，经验选择发展普通规划及已付搜索经验，A/R 才是针对学习泛化的有限构造，注意力没有全部压在最新 Laya/N 失败上。

三项总预测支持费用约 **30–48 小时**，预计完整 CPU **6–14 小时**；支持工作可能比拟合本身更贵。若需压缩投资，应按问题价值和具体报价缩减购买，而不是降低完整阅读、填满三个并发 producer，或把缺少胜出当成长期问题结束。

实际查阅包括当前治理与 scientific-tools、相关 RESEARCH/交接与 July/外审背景、三库的定向检索、B01 原 numeric/codec/数据绑定和紧凑结果及完整原 critic、D2 planner/menus/host 和实际保存的 start/candidate 记录、S7 C 的调用链及 B09 controller/model/nominal，以及上述原论文负重段落。远端完整资产存续与全部 manifest 复核使用 DM 已完成的事实核验，没有重复全量 raw 阅读。尚未验证新程序正确性、实际运行价、新世界收益或所有旧/今传递依赖等价。没有运行模型、环境、controller、RNG 查询、训练或实验，也没有编辑记录。Claude、FSD/PPC、G33 和 Milan 的既有约束保持。

**MATERIAL_DISSENT: no——对当前三个有界问题的分配无新增实质异议；这是方案提出者的投资建议，不是其独立审阅或实施认证。本次临时顾问任务至此完成。**

<oai-mem-citation>
<citation_entries>
MEMORY.md:44-45|note=[used only to locate current governance and evidence rather than rely on historical routing]
</citation_entries>
<rollout_ids>
01a0e3b9-53b6-7ab3-a128-f4dbfa1403e4
</rollout_ids>
</oai-mem-citation>