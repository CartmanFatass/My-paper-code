# FSD 恢复研究与继续建议

日期：2026-09-14。方向：`flexible_skill_duration`。本文供研究 Root 和原 FSD DM 继续工作时使用。

**所有者已明确要求把 FSD 加入工作集并恢复推进。** [决定记录](../../portfolio/decisions/2026-09-14-owner-fsd-restart.md)记载原话、应用边界与实际回执。本文是依据现有证据提出的详细建议；DM 将其落实为具体研究选择、卡片和必要的有限投资问题。

## 1. 恢复从哪个边界开始

建议恢复原 FSD DM 对方向的连续所有权，围绕 **“已有 I1280 收益中，中断机制与批量设置各自贡献多少？”**准备下一项研究。这个问题直接服务 K 轴，也与已经回答的“是否保留可选配方”不同。

| 已核实的记录 | 应怎样理解 |
| --- | --- |
| [DIRECTION 的 post-E4 边界](DIRECTION.md#post-e4-convergence-boundary-2026-09-05)：`PARK_CURRENT_FIXED_K2_POLICY_GAP_LEARNING_BRANCH` | 2026-09-05 停的是固定 N6/K2/Z4 public flag/cue corridor 分支，记录明确没有关闭整个方向。该分支的历史边界继续保留。 |
| [完整 U intake](pro_packets/20260912_post_five_pair_use_convergence/INTAKE.md)：limited optional I1280，authentic D0 default | I1280 在所测宿主、配方与五个 rollout 条件下有有限可选用途。U 已完整解决这个用途问题。 |
| [2026-09-12 Portfolio 应用](FSD_POST_U_PORTFOLIO_APPLICATION_20260912.md)：ACTIVE/HIGH，no current addition | 当时没有新 LONG、重复 U 或第六对的投入；方向仍 ACTIVE。结束拨款与工作集未接续不能自动解释为科学否定。 |
| 本次所有者要求“FSD应该加入”“让root重启此方向” | 这是新的恢复与工作集加入决定，足以启动 DM 恢复、事实刷新和新问题准备；不必重新请求是否允许恢复。 |

**关于工作流迁移的原因判断：**所有者提出了迁移不稳定导致自行 PARK 的可能性。目前所读正式记录只能确认分支 PARK、有限拨款结束和方向仍 ACTIVE；尚不能确认整个方向曾因迁移被正式 PARK，或把迁移确定为停下的原因。Root 应核对原 DM 的实际交接/可用性，并修正当前登记中的误读；历史记录保持原样。

## 2. 为什么值得继续，以及证据到哪里为止

五个已接受 I1280/authentic-D0 配对差值为：

| 原对象 | 原始 I−D0（J） | 原读数 |
| --- | ---: | --- |
| 770703 | +0.0569774672 | above_mei |
| 771003 | +0.2062859041 | above_mei |
| 771103 | −0.0124304306 | opposite_sign |
| 771203 | +0.0125548057 | above_mei，接近原 .01 阈值 |
| 771303 | +0.0737976492 | above_mei |

数字与原判定均来自[完整 U intake](pro_packets/20260912_post_five_pair_use_convergence/INTAKE.md)，没有在本文重新选择或重判样本。已有四次正向观察，足以支持继续提出有区分力的问题；负向训练实例、各对的不利评价世界、训练阶段表现不足和额外开销同时存在。最近一对 I 的原生运行 wall 约为 D0 的 2.15 倍，不能据终点收益声称计算效率更高。

已有比较把 `gap=.25 / coordinator_batch_size=1280` 与 `gap=+infinity / batch=128` 放在一起。两者同时改变中断、有效 segment/joint rows、advantage 分组与优化安排。支持的是完整学习配方，尚不能单独归功于灵活持续时间。

[外部更正版 Correction 2–3](../../../Claude_docs/plans/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md#correction-2-acvc-c01-is-a-replicated-result-the-body-misdescribed-it)也承认 ACVC C01 有六个独立训练单元支持限定范围的正结果，并撤回 FSD 是“唯一重复正信号”的说法。恢复 FSD 的理由是它对 K 轴有具体、可回答的研究问题；没有必要否定 ACVC 或用跨宿主 J 数值给方向排名。

## 3. 优先建议：同宿主的中断 × 批量归因

### 3.1 首先准备完整的 2×2 设计

| 臂 | 个体中断阈值 | `coordinator_batch_size` | 所回答的问题 |
| --- | --- | ---: | --- |
| D0-128 | +infinity | 128 | 已有 authentic D0 参照 |
| D0-1280 | +infinity | 1280 | 仅把 D0 的 coordinator 分组改大，有什么后果？ |
| I-128 | .25 | 128 | 在原小 batch 下，中断路径有什么后果？ |
| I-1280 | .25 | 1280 | 已有正向配方；在相同 batch 下是否还有中断收益？ |

这里 D0 的“不中断”是保留 D2 路径、把个体 gap 设为正无穷，并保留共同的时钟/cap；**不等于把 `policy_interruption_mode` 切到另一条 `off` 实现路径**。原始 D0 的 recurrent primitive actor 仍每个环境步响应观测，不能把它换成保持动作或速度的弱比较器。

以既有 scenario1、六 UAV/五十用户、H500、五个 16-lane training rollout、sole-final 32-world 评价作为首个设计候选。沿用已接受的合法信息、reward、k10/caps10、team threshold infinity、age off、primitive-time discount、segment credit、独立 evaluator/RNG。新卡必须明确实际采用的版本、训练终点和评价分布。若改预算或宿主，结果回答新的条件，不再假装是原比较的直接补臂。

**保持名义训练配方一致，同时报告干预真正改变了什么。** batch 指 joint-row minibatch，不是训练 seed、lane 或 episode 数。批量大小会改变每个 epoch 的 optimizer steps 和 advantage normalization；中断会改变轨迹、segment 与有效行。强行把所有这些中介量配平，会引入另一个干预。四臂可估计这两项配置选择及其交互的后果，仍不是固定训练策略上的“纯执行时终止效应”。

### 3.2 在卡片中写清所估计的量

若第 b 个独立训练 block 内有四个臂的终点评分，记为 `J(D128,b)`、`J(D1280,b)`、`J(I128,b)`、`J(I1280,b)`。建议至少保留以下 contrasts：

```text
低 batch 的中断效应：SI128,b  = J(I128,b)  - J(D128,b)
高 batch 的中断效应：SI1280,b = J(I1280,b) - J(D1280,b)
等权边际中断效应：  MI,b = (SI128,b + SI1280,b) / 2
等权边际批量效应：  MB,b = [(J(D1280,b)-J(D128,b))
                         + (J(I1280,b)-J(I128,b))] / 2
交互效应：          INT,b = SI1280,b - SI128,b
原完整配方效应：    PKG,b = J(I1280,b) - J(D128,b)
```

主要 contrast 由 DM 在运行前选定并解释；其余注明为辅助解释，避免从多个指标中事后挑一个获胜。外部 addendum 的中断“主效应”公式少了等权平均的 `/2`，已由[正式双轴方案](../../portfolio/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md)校正。MEI 必须对应所选 contrast 的尺度。

同时报告两个 simple effects。若交互明显，平均效应可能掩盖只在 batch 1280 才有效的情况；若区间很宽，就保留该不确定性。即使两个中断 contrast 为正，也只支持此干预、宿主和训练预算，不自动推广到所有技能持续时间方法。

### 3.3 预算较小时的可执行缩小方案

若完整四臂设计当前投入过大，可先提出一个 **fresh I-1280 vs fresh D0-1280** 的有限 B 比较，直接问“相同大 batch 下，中断是否还带来差异”。它比再买原样 I1280/D0-128 更直接地区分当前替代解释。

这个两臂方案只能估计高 batch 下的 simple effect，不能给出完整的 batch 主效应、交互或低 batch 效应。它也是正式研究选择，DM 应说明为什么先回答这个窄问题。若日后扩为四臂，须在下一张卡中说明分阶段选择暴露与 block 结构；不能把不同日期/配方的旧结果拼成预先计划好的四臂训练重复。

完整四臂与两臂方案是供 DM 比较的候选；本文没有替 DM 冻结 arm set 或指定新调用数。建议优先提交一个能直接落实的有限对象，而非泛泛要求“进一步研究”。

## 4. 独立训练、精度与停止边界

1. **训练实例是基本单位。** 若设计采用 n 个四臂 block，就是 4n 次独立初始化的 arm fits；block 间独立，block 内配对须由随机化/共同随机数设计支持。相同 seed 标签本身不证明配对成立。32 个评价世界不能算作 32 个训练重复。
2. **历史结果用于设计。** 五个旧配对和更早 I-128 的两次损失必须保留；它们是此次 outcome-informed 设计的已见信息，不自动作为新四臂估计的同期控制或确认样本。
3. **MEI 说明实用价值。** 对所选主要量给出任务效用或成本理由；原卡 .01 J 继续保留其历史含义。既不统一改为 .05 J，也不要求效应大于 2 SD。若举覆盖率换算例子，只在其他 reward 项不变时成立：.05 J / .7 ≈ 7.14 个百分点。
4. **规模服务结论。** DM 根据可用预算、主要量、预计变异与期望精度选择 n；可用已知变异做规划敏感性分析。旧 package 差值 SD 不能直接当作新 simple effect 或 interaction 的已知方差。没有“必须先做 pilot”、五/十 seed 门槛或强制 t/IQM 切换。
5. **冻结追加与失败处理。** 固定终点、允许的 fits、评价暴露、缺失数据处理与任何分阶段追加边界，在见到新结果前记录。坏结果保留；无有效 primary 的失败不能被静默替换。更小 B 仍可提供局部开发证据，其结论按实际精度限缩。
6. **区间与单位一致。** 对训练 block 的 contrast 报告效应、跨 block 变异及适合该设计的估计不确定性，说明方法假设。单个 block 只能给局部训练实例观察与条件评价不确定性；bootstrap 不会补出训练信息。实际等效需要相对于预先定义区域足够精确，点估计接近零不等于已经证明无效。

## 5. 同宿主基线能力与归因一起准备

[正式双轴方案](../../portfolio/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md#4-准备顺序与可交付结果)把目标宿主的基线能力放在新投入准备的优先位置。FSD DM 应明确：当前 authentic D0 是真实比较器，但尚无调优后的同信息能力/完整 headroom 证据。

建议复用 Scenario1 基线准备，列出 flat MAPPO、固定 k HMASD 与 FSD D2-D0 的接口关系，明确谁拥有共享基线实现。固定 k 的选择、调参预算、环境步数、训练终点、合法信息及评价世界要可比较。直接 HMASD 路径与 FSD 的 D2-D0 不能仅因都叫“固定 k”就视为相同方法；必须核对代码与学习语义。

基线回答“相对有能力的参照，完整方法还有什么价值”，归因回答“当前包内哪个干预带来差异”。两项设计准备可以并行；实际投入顺序按有限提案处理，不以等待跨方向统一基线结果来停住已授权工作。Scenario1 的历史覆盖率和 ACVC cluster 的 J 不能相互替代。

## 6. 最小工程范围与已有入口

DM 从[原 B01 design §§2–5](FSD_UAV_RENEWAL_BATCH_B01_DESIGN_CARD_20260910.md)及[实现 intake](FSD_UAV_RENEWAL_BATCH_B01_IMPLEMENTATION_INTAKE_20260910.md)进入，再核对当前代码：

- `scripts/run_fsd_uav_renewal_batch_b01.py` 及其共享 UAV runner：现有 I/D0 绑定、learner/evaluator 构造、最终 primary 发布。
- `hmasd/agent.py`：D2 renewal、`coordinator_batch_size`、coordinator 更新和 primitive actor 调用。
- `hmasd/utils.py`：joint-row sampler、valid-head credit、duration discount 与分组。
- `envs/pettingzoo/scenario1.py`、`configs/config_1.py`：宿主、reward/信息与配置含义。
- `tests/experiments/candidates/flexible_skill_duration/uav_renewal_batch_b01/test_binding.py`：已有绑定验证入口。

只在选定对象所需处增加显式臂绑定与必要记录，避免复制整套 runner。DM 的具体 L0 列出交付、路径、保留语义、验收和允许暴露；涉及科学语义/RNG/共享核心的修改按现行 ENGINEERING_SCOPE_SPEC §7 做独立 review。检查聚焦四臂设置不串线、D0 真实保留、分组参数生效、状态/RNG隔离和结果身份；不因本文增加全库测试、profiling 或额外科研探针。

沿用 remote-first 和新鲜资源准入。原对象的 CPU FP32/四线程条件不能仅为方便换成 GPU/mixed precision；若新设计改 host/device，DM 事先定义新比较与可移植性边界。历史 worktree 路径只作恢复证据，当前路径和原生任务从活跃 Root/运行时取得。

## 7. 暴露与成本：给投资问题具体数字

若新设计沿用五个 rollout、16 lanes、H500 与单次 32-world endpoint，可由配置直接得到以下**候选计数**。n 是设计选定的独立 block 数，尚未拨款或选定：

| 范围 | fits | 训练 team-environment steps | 评价 team-environment steps |
| --- | ---: | ---: | ---: |
| 四臂 × n blocks | 4n | 4 × n × 5 × 16 × 500 = 160,000n | 4 × n × 32 × 500 = 64,000n |
| 两臂 × n blocks | 2n | 80,000n | 32,000n |

四臂每个 block 共 224,000 team steps、320 个训练 team episodes、128 个评价 episodes；这些不是独立训练单位数。本文用 Python 按上述配置计算，和[旧第五对 counts](uav_renewal_batch_b02_771303_20260912/PROSPECTIVE_COUNTS.json)的两臂口径一致。optimizer steps 取决于有效 rows/分组，不能由 rollout 数替代。

新 D0-1280 的实际 wall、支持工作和完整任务成本目前未知。使用既有 I1280/D0 timings 时标明旧宿主/配方、测量范围与不确定性，不把其和直接当新四臂总账，不把并行等待重叠相加。有限提案须给实际选定的 n、逐臂调用、预计资源/实际硬边界、失败/重试政策和支持范围。旧 LONG 的 3900 秒 offer 与过去未花完的时间不自动转成新额度。

## 8. 根据结果继续，避免再次停在工作流中

| 新证据 | 合理解释与后续建议 |
| --- | --- |
| 相同 batch 下 I 的收益仍有支持 | 保留中断路径有用的限定结论；进一步研究持续时间分布、事件响应以及训练/执行贡献的区分。 |
| I1280−D0-1280 的不确定性范围已足够窄，并落入预先定义的实用等效区域 | 若只做两臂，结论限于高 batch 下的中断 simple effect，批量解释仍待对应 batch contrast。四臂证据还支持批量 contrast 时，才有依据将收益归于批量相关设置，并考虑把好配方用于基线。一个宿主的结果不否定所有灵活时长问题。 |
| 交互明显或两个 simple effects 方向不同 | 把问题收窄为中断与优化分组的依赖关系，避免仅报平均效应。 |
| 区间宽、正负训练实例并存 | 结论为仍不确定；在投入与可改变判断之间选择是否增加事先界定的重复，不能写成机制已无效。 |
| 能力较强的同宿主基线显著缩小 package 差异 | 重新评估 FSD 的实用价值与比较器，完整保留早期正信号及其预算条件。 |

后续 hazard/移动用户条件、持续时间记录、执行时中断消融都可以成为候选，但应由下一项问题解释其信息价值。更早的 corridor 分支有自己的停下理由；不要把旧扫参表直接恢复成自动梯级。本文也没有新设“只有显著正效应才准探索”的通用门槛。

## 9. Root 与 DM 现在要做什么

**Root：**应用所有者恢复决定，将 FSD 加回当前工作集并唤醒原 DM；若旧原生任务无法恢复，保存该事实后按同角色同方向重建接续。记录实际 DM 路由、当前准备/实验/等待状态，保证原三个方向连续推进。此次加入是明确的 FSD 特例，不自动扩为一般五方向补位政策。

**FSD DM：**阅读本文、当前 DIRECTION/最新 U 与 Portfolio 应用、证据规范 §11.11 和正式双轴方案；在现有方向记录中写一段实际应用说明，并给 Root 一次原生回执。随后直接完成：

1. 确认旧对象、请求、产物与未决任务，恢复当前 DIRECTION 入口；避免重复已经完成的 U。
2. 比较四臂归因与同 batch 两臂方案，明确本次会改变的判断、保留的反证和最小实际投入；将基线能力准备接到同宿主问题。
3. 若已有授权覆盖下一步，按对象卡和站立委托推进。若所需新投资/调用超出现有授权，DM 直接准备、发布并通过自己的 Transport 提交有限 Portfolio 投资问题；新的方向级科学选择走原 Convergence/Innovator 节点。不要把所有对象选择都升级成两轮 Pro。
4. 把本次 OWNER_DIRECT 加入决定作为已知约束，不再问是否允许恢复 FSD。新请求应问设计/投入中真实未决的选择，说明相对旧 U/no-addition 的新问题；串行使用共享 Portfolio 绑定，保留已接受请求。
5. 获得适用的明确对象/投入后，同一 DM 连续完成实现、检查/review、发布、准入、实验、Monitor、结果与科学 intake，不逐步等待 Root ACK。对象结束时主动返回实际下一步；只有正式方向处置才能释放席位。

**恢复完成的可查证标志：**Root 已实际派发/恢复原方向 DM；DM 已读建议并留下应用记录；已有具体设计准备或具名请求在推进。训练是否已开始单独以接受的 invocation/Monitor 事实为准，不能由一条消息或一份计划推断。

## 10. 阅读依据与本文边界

科学判断复用 [Foundations §§5–6](../../../rl-marl-foundations-20260907/FOUNDATIONS.md)、[层次与异步专题](../../../rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md)和[实证专题](../../../rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)：技能保持期间 primitive 行为仍可响应；学习包比较和组件解释不同；独立训练与嵌套评价有不同不确定性。这些概念支持本次归因与重复设计，不提供额外审批规则。

[证据规范 §11.11](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#1111-owner-calibration-after-external-methodology-review-2026-09-14)及[已采纳双轴方案](../../portfolio/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md)控制采用范围。外部稿的统一 2 SD、固定 estimator/seed 门槛和逐 rung 所有者审批未获采用。本文新增科研训练/评价为零；原结果、原卡阈值、原请求和反证全部保留。
