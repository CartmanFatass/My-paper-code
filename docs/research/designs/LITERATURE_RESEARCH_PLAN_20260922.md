# 文献启发研究计划：1 / 3 / 6 / 9 详细设计与 17 项备用构想

日期：2026-09-22。性质：owner 请求的研究设计稿。编号沿用本任务的 21 项文献机会图，
不会因以后改变优先级而重排。Owner 本次选择 **1、3、6、9 做详细计划，其余 17 项保留简要备用计划**。
本文件是一次性设计交付，不成为新的常规科研记录、方向注册表或实验调度清单。
实际方向状态、负责人、已接受批次和暂停仍以 [RESEARCH](../RESEARCH.md) 及对应 NOTES 为准。

## 阅读导航与使用方式

| 优先计划 | 主要科学问题 | 与现有工作的关系 |
| --- | --- | --- |
| [1：面向控制用途的预测小模块](#plan-1) | 服务监督的语义与辅助优化分别贡献了什么？怎样组织梯度才能保留控制用途？ | USA 的后续设计，由现任方向 DM 采用时接续其 NOTES，不新增竞争 lead。 |
| [3：目标条件化的信息聚合](#plan-3) | 当前合法技能/目标在聚合前参与取用信息，是否比聚合后条件化更有用？ | 是新的位置/条件化问题；继承 LOE dense 配方不利证据，不自动重开旧配方。 |
| [6：负载与关键成员泛化](#plan-6) | N 本身、需求/容量、空间竞争和关键依赖，哪些造成迁移困难？ | 接续现任人数 DM 的动作法判别；不得替换或重复已选 B02/B03。 |
| [9：实际互补的技能](#plan-9) | 能否学到组合后真正增加服务的技能，而不只增加可辨认性？ | 固定 k/N 研究共同学习与实际组合；不重开 cap=10 可变周期配方。 |
| [其余 17 项简要备用计划](#backup-plans) | 保留具体假说、普通强比较、首个可用比较和展开条件。 | “备用”表示本设计中的后续构想，不自动增加 RESEARCH 的 reserve 行或分配 DM。 |

本轮以已发布 `d7056f6249fe593b3969d22306af6e70cb841104` 为取证基点。
[当时的研究背景、方向状态和已选比较](https://github.com/CartmanFatass/My-paper-code/blob/d7056f6249fe593b3969d22306af6e70cb841104/docs/research/RESEARCH.md)
是下文设计的约束；此后结果由实际负责人在采用计划前吸收。尤其人数方向已选 B02 冻结 raw/clip
部署比较（0 fits、288k eval steps）和 B03 单区组训练动作法判别（4 fits、1.44M train + 384k eval steps）。
这些是原方向已经选定的工作，**不计作本提案的新成本，也不由本任务启动**。

文献依据来自 MyLib 已处理的 237 篇默认顶会研究记录；另一个 JAAMAS Track 摘要仅为参考，未纳入设计证据。
各记录含原 PDF 路径、页码与 evidence ID；缺外置附录的记录继续保留 partial，不据缺失内容推断保证。
入口：[第一批模块与边缘方法](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/syntheses/decision_modules_20260922.json>)、
[第二批 MARL 桥接](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/syntheses/marl_followup_20260922.json>)、
[剩余论文综合](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/syntheses/marl_remaining_20260922.json>)。
下文“预测”“拟议方法”是我们的推演；文献类比不代表已完成新颖性检索或已在 HMASD 得到收益。

## 共用的设计边界

- **先回答一个问题。** 四项详细设计互不要求另一项阳性；首个比较不同时叠加新人数、时长、奖励和网络。
  可用已有数据或小模型帮助辨别，但不设必须先通过的 toy、预测精度或基线分数门槛。
- **成本是设计选择。** 各节列出的臂、horizon、拟合次数是建议成本，不是已接受批次、额度或必须用完的预算。
  阶段之间按新证据选择；不合计所有可选分支成为默认执行清单，不在看到分数后扩展原批次。
  零新增 fit 的冻结评估仍计真实世界数、团队步、加载与计算成本。
- **保留实际任务。** actor 输入、critic 特权、技能采样、环境动作映射、周期、循环 reset、reward/normalizer
  均沿真实执行路径核对；后果标签只来自已执行事实。新增信息、任务分布或执行权另作明确干预。
- **区分设计与确认。** 一两个训练实例只作探索。确认另写 CLAIM，冻结主要对照、终点、实际 seed 整数、
  未用于选择的最终世界与判读规则，通常每臂 3–5 个新独立训练 seed。多世界和多 checkpoint 不增加训练 n。
  实际 seed 与现有 runs 核对后在 NOTES 绑定；本文件不冒充可直接执行的 seed/launch manifest。
- **采用时进入现有流程。** 当前任务完成设计与文献核对，未实施、训练或发送新的 Pro 问题。
  负责人将所选比较写入自己的 NOTES，并按 constitution §5 复用适用建议或就新的关键判断咨询 Pro；
  各节给出咨询焦点。此后才固定实现与实际批次。文档发布不更改 lead、归档状态、Claude 暂停或 G33。

## 首轮建议的范围与成本

下表只概括每项第一个有结果意义的比较，技术检查另计；不是联合启动清单。
M 为百万、k 为千，均指团队环境步/转移，不乘 agent 数。历史耗时只作尺度参照，新配置耗时未知。

| 计划 | 首轮主比较 | 建议新增训练 | 建议评价/事实采集 |
| --- | --- | ---: | ---: |
| 1 | 服务 joint / 普通自预测 joint / 双头 detach；2 个训练区组 | 6 fits ×180k = 1.08M | 576k native + 42k 共同事实 |
| 3 | 前置 query / 后置 query / 普通条件 pooling / 原 MLP；1 个训练区组 | 4 fits ×360k = 1.44M | 192k 常规 + 16k 支路干预 |
| 6 | 两个 B03 clip-train 冻结策略 × 五个 (N,容量) 条件 | 0 新 fits；依赖既有 B03 制品 | 80k 冻结评价 |
| 9 | 普通 AR / 匹配曝光 AR / 匹配曝光+事实组合辅助；每臂2实例 | 6 fits ×360k = 2.16M | 384k 常规 + 96k 统一选择器 + 96k 四格诊断 |

计划 6 若随后选择均衡负载训练，另为 2 fits、720k train + 400k eval；它不识别训练分布改变的因果作用。
计划 1 的受限梯度比较、各项确认以及备用构想均为单独的后续选择，费用不隐藏在上述首轮里。
这些规模提供可审阅的起点；采用时若当前证据要求实质修改，负责人在前瞻记录中重写比较和成本，不能看到结果后延长原批。

<a id="plan-1"></a>

## 1. 面向控制用途的预测小模块

**首问是现有服务辅助包相对一个强普通辅助参照还有没有完整控制收益；暂不把预测接入 actor，也不同时加入规划、通信、时长选择或固定读出。** 本节是候选方案，不接管 USA 的既有 DM，不改变其状态或接受新批次。依据版本为 `d7056f6249fe593b3969d22306af6e70cb841104`。

**起点与文献边界。** [USA 两对结果](../candidates/uav_service_auxiliary/NOTES.md#b02-complete-comparison-and-bounded-keep-decision--2026-09-22)来自 S7-S2、接口 v3/reward v2/arm C、N8/k10：四个 180k fits 中，joint 相对 detach 的终点 J 差为 +159.54/+403.51，QoS 和返航约束代价也改善；第二对共同事实 MSE 却高 2.248 倍。预测头没有成为行动输入，干预是辅助梯度进入 actor 的 base/GRU。两对都有晚期回落，复用八个评价世界，且评价没有充电、cutoff/depletion 事件。因此保留的是探索性训练包，尚不能称为预测机制、充电竞争、安全改善或总体优势。共享背景[主题 2/4/6](../RESEARCH.md#研究背景与共享认识)直接决定本方案：未来事实只作标签，原生收益与代理误差分读，训练实例才是重复单位。

文献提供可行性与强对照，不给 UAV 阳性保证：[Self-Predictive RL](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-C517F96832.json>) **E4/E7**支持普通单步自预测参照，且 OP/ZP 的优劣依任务；[SPR](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-F328FA237A.json>) **E1/E4/E6**提示停止目标梯度、归一化及完整计算成本的重要性，不能照搬其 Atari 数字。[MA²CL](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0502.json>) **E2/E3/E7**已有辅助梯度塑造 actor encoder 的机制；[MADiff](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0582.json>) **E9**的同结构队友预测损失消融有任务收益，但不证明本任务需要扩散或预测输入。[MOSDT](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0642.json>) **E1/E2/E7/E9**区分教师监督回传与输出 detach，并保留负迁移。三份本地综述由 DMX-C02 收窄到 MFX-C03；其[最新重评](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/syntheses/marl_remaining_20260922.json>)不支持预设“自由头吸收监督，所以必须固定坐标”。这里借用单智能体自预测的表示学习思路；它遗漏了共同学习队友、共享团队标签及内生轨迹变化，正是必须在完整 HMASD 上测的部分。

**主假说及区分。** 固定资源下，W10 服务辅助包相对指定普通单步自预测，在新训练实例、新世界上仍有完整 J/交付 QoS 增量及兼容风险。竞争解释是普通表征优化/稳定化：G 也能保留收益，S 没有清楚增量；另一解释是开发实例/世界偶合：旧面板差值仍好，新世界或新训练实例翻转。S/G 同时改变服务语义、W10/单步跨度、标量/潜变量目标及损失形状，所以这里检验的是两个具体训练包，**不识别服务语义的单独因果作用**。主要中间读数固定为共同终点事实面板上、按 episode 等权的 W10 QoS MSE；不在结果后改选排序。它描述读出分布变化，既不是 native 获益的必要条件，也不成为 keep 门槛；即使 MSE 反向，仍按真实控制结果读包级价值。

| 臂 | 辅助训练如何进入表示 | 用途 |
| --- | --- | --- |
| D：detach | 服务头与通用头都训练，输入表示均 detach；原生 RL 不变 | 当前 native 学习参照 |
| S：service-joint | 仅 W10 QoS 损失更新 base/GRU | 保留已有服务包 |
| G：generic-joint | 仅普通单步自预测损失更新 base/GRU | 强普通辅助参照，不能只比随机标签 |

三臂保留同一网络、两套相同影子头与数据权限，防止只给候选额外容量。服务头沿用 hidden→64→1；G 用 `(h_t, 已执行 a_t)`→64→hidden，预测停止梯度的下一潜表示，采用单位范数平方距离；目标在每次辅助 pass 开始时由当前网络回放计算并固定，不用未来量作执行输入。两头都更新，但各臂仅允许上述一条辅助表示梯度路径。沿用每轮 native 更新后一次辅助 pass、chunk50、头/表示 Adam 3e−4/3e−5、各自 clip .5。报告梯度与实际参数步长，不能把相同学习率叫作相同优化作用；不根据评价分数调权重。固定记录 G 的目标/表示逐维方差、有效秩、输出范数和每轮实际梯度/参数移动；若目标或预测坍塌、辅助梯度失活，则该普通参照未被有效检验，S 的优势不能计作语义证据。本批不调整目标、权重或补 fit；任何修订另提理由与完整比较。影子头必须通过 RNG/优化器隔离核验，使 D/S 的策略行为保持原配方。

**合法信息与时间合同。** actor 仍只接既有 observation、循环历史和原高层给定的 held skill，critic 权限与原学习不变；不加全局真值、未来队友行动或事后有效性位。`y_t=mean(q_t,…,q_{t+9})`，其中 q_t 是从 observation t 执行动作后的真实端到端 QoS。终止可以恰在窗口最后一步，提前终止、时间截断或采集边界不足十步均删失，不填零、不跨 reset、不补造未执行后果；G 使用同一有效起点。RL 保留终止/有限时限零 continuation、未完采集边界 bootstrap 的原合同。首行使用该序列真实入口的 hidden 与 mask，后续逐步 mask 为 `1−done[t−1]`；训练归一化统计不从评价或未来标签更新。单步预测的实际动作只进入训练头，各臂都具有该数据权限。

**分阶段投入。** 第 0 阶段为 **0 fits**：复核现有数组与代码的标签偏移、终止/删失、normalizer、广播团队标签、真实梯度路径和更新量；检查通用目标与初始/终点事实的变异范围。这里只做证据复算和必要正确性检查，不用 toy 阳性作为学习前置门槛，也不另拟合探针来冒充零成本。

| 阶段 | 拟议训练与固定终点 | 新 fits / 训练步 |
| --- | --- | ---: |
| 首批判别 | D/S/G ×两个新训练区组；每 fit 四 lanes×1500×30，rollout30 为终点 | **6 / 1.08M** |
| 有条件梯度路线 | 仅在同参数点诊断显示 base 辅助/RL 梯度冲突、而 GRU 路径可用时，S 对“辅助只更新 GRU”；两个另行独立的新训练区组，同 180k | **4 / .72M**，不自动启动 |
| 独立确认 | 最终选定候选与一个主要基线，各四个新训练种子；同 180k | **8 / 1.44M**，另写 CLAIM、另作决定 |

首批在 rollout0/10/20/30 用旧八世界读开发曲线；只在终点打开一组新的 32 世界，各臂相同。训练、开发事实及最终评价的具体种子在采用时核验占用、去重并绑定，三类面板隔离。名义 native 评价共 **576k steps**（提前终止按实际数记）。每训练区组另采共享初始策略的两个新事实世界；终点再将 D/S/G 在另外四个开发事实世界的轨迹合成共同面板，所有头回放同一字节、各自从 reset 重建状态。合计名义 **42k factual steps**，不由各臂私有轨迹误差直接排名，也不把同号世界误称跨区组相同轨迹；这些数据都不回流训练。每个完整 episode 等权，重叠窗口和八名 agent 不扩大 n。

主读数是每个训练区组的终点完整、未改动原生 reward 总和之世界均值差；并列 QoS、交付吞吐、返航约束代价、最低电池量和实际充电/切断/耗尽事件。主要中间读数仍是公共事实 QoS MSE；表示方差、同参数点 RL/aux 梯度余弦及更新前后策略 KL 为预写诊断，不扩充成可任选的胜出指标，也不单独证明机制。训练区组共享初始化与外生种子设计，并核验初始策略与首轮一致性；独立区组之间才做训练重复，不能因 seed 数字相同就声称配对。

首批拟保留 S 的条件是两区组在新面板的 S−D J 均为正，服务改善且风险没有明显恶化；若 S−G 也方向一致，保留对这个指定普通辅助包的增量，不能称为服务语义已识别。探索阅读效应大小、服务/风险权衡与绝对水平，不设没有任务依据的幅度门槛；确认的实用差值须由服务价值和成本另作论证。S/G 都有效而无清楚差别时保留较简单/便宜的包，不把未检出差异说成等价；预测变好但 J 无益，或只在旧面板有利，则削弱当前包的投入理由，不自动加训；MSE 反向但 J 有益则保留包级观察。不能靠另换代理量挽救没有 native 增量的包。若以后需要识别服务语义，应单列时间匹配的 W10 普通观测/任务监督比较，固定容量与更新条件；它不是本批自动追加项。持续低绝对服务、晚期下降或缺少风险事件，均限制实际采用，不能用早期最佳 checkpoint 替代终点。

可选梯度批次只回答一个新问题：限制辅助梯度位置能否减小对策略的破坏并改善终点服务。它预测同参数点冲突/辅助更新后 KL 降低，以及 J/QoS 改善；两者缺一不支持该修补故事。它不同时加入残差、注意力、固定读出或新预测目标。按相同开发/最终评价模板为 **384k native eval steps**，公共事实采集名义 **30k steps**；应使用另一个新终点世界面板并在新 prospective entry 中绑定。

确认只在有值得主张的包时考虑，四种子是 3–5 个 fresh seeds/arm 范围内的具体建议，并非已获执行授权。B01/B02 及本次首批都留作开发曝光；确认再用未查看的 32 世界、冻结 rollout30 与单一主要比较。建议主命题限定为该新固定面板上的跨训练平均收益，CLAIM 事先固定实用差值、配对区组估计及小样本区间假设；不声称四种子保证检验力或覆盖全部世界总体。首批加四种子确认合计 **14 fits/2.52M train steps**；若另选梯度批次则 **18 fits/3.24M**，不是必须花完的额度。已有四 fit 合计 509.11 runner min，仅给出原配方约127 min/fit的历史尺度；新 G、扩大的评价和共同事实回放的时间未知，不能用它保证未来时长。记录实际准备、训练、评价、回放、收集与节点占用。

**代码落点与采用前的问题。** 参考代码固定在 `30401722b14c208bf5330ab66e967c94b3df8a36`：[`auxiliary.py`](https://github.com/CartmanFatass/My-paper-code/blob/30401722b14c208bf5330ab66e967c94b3df8a36/experiments/candidates/uav_service_auxiliary/b01/auxiliary.py) 的 `future_window_targets`、`_representations`、`update` 控制标签和梯度；[`native.py`](https://github.com/CartmanFatass/My-paper-code/blob/30401722b14c208bf5330ab66e967c94b3df8a36/experiments/candidates/uav_service_auxiliary/b01/native.py) 的 `NativeSpec`、`write_facts`、`prediction_replay`、`run_native` 负责新种子、实际动作记录及独立面板。入口为同 revision 的 `scripts/run_uav_service_auxiliary_b01.py`，回归测试在 `tests/experiments/candidates/uav_service_auxiliary/b01/`；新研究另建后继入口，不改写冻结 B01/B02。共享 learner/runner 改动按工程方法独立审查。

采用本次实质改题前，由原 USA DM 对 Pro 提一个集中问题：**现有“J 改善而 MSE 反向”证据下，D/S/普通 ZP 的比较是否足以改变服务监督与普通稳定化的投资判断？哪些损失尺度、目标退化和公共事实分布混淆需要在这六 fits 中固定；什么结果应结束解释而不是增加模块？** 现有 Pro 答复没有评价这个新对照；本轮只形成问题，不发送、不启动训练。

<a id="plan-3"></a>

## 3. 目标条件化的信息聚合

**研究判断。** 值得准备的是一个关于条件化位置的新比较：在有限训练量下，让当前已选技能参与实体聚合，是否比聚合完成后才调制摘要更容易学到有用行为。它尚不是已诊断瓶颈的修复，也不意味着复开 LOE。当前 published main `d7056f624` 的[共享认识 §4、§6](../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)要求分别判断表示能力、有限学习和完整使用价值。[LOE 已关闭的 B01](../candidates/local_observation_encoding/NOTES.md#2026-09-22--dm-decision-archive-the-tested-dense-recipe)在每臂一个训练实例下，ORIGINAL/DENSE 的 J45 为 .458426/.202254，连接人数为 31.939/13.416，DENSE fit wall 约 1.95 倍；这些结果没有识别出 attention 或 pooling 的独立因果作用。新理由必须是“合法 query 在压缩前后有不同预测”，不能只是再换一个 dense 配方。

**文献支持到哪里。** [Tiny-Attention，E1](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-2A009C7766.json>)支持跨位置读取是一种不同于逐位置变换的已知操作；[Set Transformer，E2/E4/E7](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-F08EC1A407.json>)提供 query pooling，也保留普通 pooling 更好的任务；[Deep Sets，E2](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-CCA390C5FE.json>)提供条件化共享映射与集合读出。[RPG，E2/E4/E11](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0533.json>)的 ego query、GRU 与任务条件 head 说明构件已有 MARL 先例，但不能把其 task embedding 当作本项目部署可见目标；[PORTAL，E2/E4](</mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0048.json>)的关系加权在从头训练时也未全面胜过求和。这些已核对本地原文的事实不直接预测 HMASD 收益；两篇 MARL 材料的外置附录缺口仍保留。

**合法接口与主假说。** 实际顺序由 [hmasd/agent.py](../../../hmasd/agent.py) 的 `HMASDAgent.step` 确定：先选技能再选动作；[hmasd/networks.py](../../../hmasd/networks.py) 的 `R_Actor.forward/evaluate_actions` 执行 `base(obs) → FiLM(z_i) → GRU`，`update_discoverer_from_rollout` 重用保存的 `agent_skills_seq`。因此 query 只取已选/持有的个体技能 one-hot：边界步先完成高层选择，随后低层使用新技能；段内用原持有技能。不把尚待选择的技能反送高层编码，也不新增团队技能 Z、服务真值或未来目标。技能编号本身没有已验证的服务语义。

主假说是：有限宽度和更新量下，技能无关摘要使技能相关实体选择更难学；提前条件化应产生被策略实际使用的 query 依赖，并改善固定终点 J/服务。不是声称后置 FiLM 在理论上无法表达同一策略。相反预测分别是：技能没有此类有效差异，前置与后置无收益；普通条件化 pooling 已足够；额外结构只增加学习和计算负担。

所有臂使用 [MultiUAVEnv._get_observation_vectorized](../../../envs/pettingzoo/uav_env.py) 给出的同一 104 维局部观测、同一合法 z、GRU 历史和刷新时钟。20 个用户槽、10 个邻居槽的当前 SINR rank 可用，但不是持久身份；零槽照常参与，不增加隐藏有效位或计数。高层、中心 critic、通信、reward、归一化、reset、PPO/discovery 与完整共同学习均相同；动作执行采用下面的新共同合同。


**动作执行合同。** 已核对 LOE 所复用的 [run_fsd_baseline_interruption_b01.py](../../../scripts/run_fsd_baseline_interruption_b01.py) 中 `collect_training/evaluate_panel`：动作未经裁剪进入 `env.step`；[ParallelToArrayAdapter.step](../../../envs/pettingzoo/env_adapter.py) 只转换数组/字典；[MultiUAVEnv.step](../../../envs/pettingzoo/uav_env.py) 将输入乘 `max_speed`，随后裁剪位置。对应 [DiagGaussian.forward/evaluate_actions](../../../hmasd/r_mappo_utils.py) 抽样/评分原始 Normal，Box 声明不实现限幅。这些路径在 LOE 输入 `efe7d61e82b2c0aed7a634bbb2e22d7cc47430a3` 与本次 main 间未变，符合 [N 方向已发表的动作语义修订](../candidates/agent_count_generalization/NOTES.md#2026-09-22--full-pro-reading-b02-execution-probe-and-b03-investment-decision)。

本新比较明确选 **四臂全部 bounded train/bounded deploy**：训练抽样 `u~Normal(μ,σ)`，仅向环境传 `a_exec=clip(u.copy(),−1,1)`；buffer 保存原始 `u`、原始 old log-prob，PPO ratio 在同一个 `u` 上重评估，reward/next state/done 来自实际 clip 轨迹。不得原地裁剪后用 Gaussian 给执行副本评分。确定性评价及 query-off 评价均执行 `clip(μ,−1,1)`。保留原 Gaussian 初始化和原始熵系数 .05，不同时换 tanh、限制 logstd 或调熵；raw entropy 不代表执行动作熵，方差仍可能增长。新实验 collector/evaluator 在唯一执行边界加映射，旧冻结入口保持原义；记录 raw 超界率、幅度与执行饱和，所有臂同权。这里界定的是各坐标的动作盒，不额外宣称欧氏速度上限。

clip 会改变训练轨迹、状态访问及学习曝光；旧 LOE 分数和耗时只能作有范围的历史参照，不能与新四臂相减宣称编码收益。该共同合同不是对裁剪收益的实验，不复制或启动 N 方向 B02/B03，也不新增 raw 对照格。建议一次四臂探索：

| 臂 | 明确实现与比较作用 |
| --- | --- |
| O：MLP+FiLM | 现有网络配新共同 clip 执行；同批新训练基线，旧 ORIGINAL 不作直接对照。 |
| L：后置 query | 相同 typed token 编码；以自体/时间生成 ego query 做两类实体 attention pooling，技能投影 `U z` 在池化后加入，再走原 FiLM。 |
| E：前置 query | 与 L 共用结构规格，把同一个 `U z` 移到 ego query 中，先按技能读取实体，再走原 FiLM；E−L 是主位置比较。 |
| P：条件化 pooling | 共享非线性实体 MLP 同时接收实体、ego 和 z，再做各类型 mean+max、投影与原 FiLM；检验普通 query+pool 是否已经足够。 |

L/E 初始规格均为 token 宽度 64、四 heads、输出 256，token/rank 处理相同，`U` 都有实际作用，不用闲置参数凑数；采用小型单 query 读取，不沿用旧 dense 全槽两两交互。P 给足相近的有效容量，O 保留原结构；记录实际参数、激活与算时，不强求四臂精确同参数。统一 PPO epochs、批量与训练步数，第一批不搜索宽度、学习率或 pooling 组合；若后续调参，双方获得明确相同的选择曝光。

**分阶段投入与读法。** 第一步是 0 fits 的接口、梯度和短工程检查，不设阳性 toy 门槛。若将来决定采用，首批固定 S1、N=6、k=10、50 个静态均匀用户、free-space，六种 team/individual skills；复用 D1280 的步数和优化器预算：每 fit 为 45×16×500＝360,000 team transitions，PPO 15 epochs，高层 batch 1280。四臂×一个新训练区组＝**4 fits、1.44M 训练 transitions**，不复用旧 92101 作为新证据。各 fit 在 15/30/45 rollout 后各评估 32 个同分布、独立于训练的固定 reset worlds，合计 **192,000 evaluation transitions**。预写终点为 `J45=N×scalar episode return/500`；同步报告 coverage、连接人数、quality 和高度惩罚，后者不是实测电池耗能。所有曲线保留，不能挑 J15 峰值。

为检验“确实使用前置 query”，预先增加一次 E 终点的冻结策略评价：只将聚合支路 `U z` 置零，后置 FiLM 仍接收真实 z；同 32 worlds，**0 fits、16,000 额外 evaluation transitions**。中间预测是移除该支路会改变实际执行动作，并削弱 E 的原生收益；只改变 raw 动作而被 clip 吸收须另列。attention 热图或梯度非零不替代此读数。这仍只识别该训练实例对支路的依赖，干预可能离开训练分布，不能单独证明语义正确。首批总评价量为 **208,000 transitions**。

E 若不胜 L，前置位置假说没有兑现；E 胜 L 但不胜 P，保留普通条件化解释；E/P 都不优于 O，缺少完整包的投入理由。只有代理量改善、只有早期峰值、或收益不能支持实测额外成本，都不自动追加结构或种子。混合结果保留未决范围；技术失败单列并计入尝试。一个训练区组不能建立稳定排名；32 个 worlds 和三个 checkpoint 都不是训练重复。以上 worlds 检验同分布新布局，不宣称未见 N 或服务机制泛化。

**实现与成本边界。** 需要在 `R_Actor.forward/evaluate_actions` 两条路径显式传入 `(obs,z)` 给候选 encoder；仅替换当前 `base(obs)` 不会获得技能。可用实验内 actor 子类保持核心默认行为，安装后重建 optimizer，并让独立 evaluator 同构同步；核查 rollout→buffer→重评估的技能时间对齐、五组实际更新及参数位移；对执行映射检查过界样本原值入库、旧参数回放 log-prob 一致、裁剪副本不改 raw 数组，以及训练/评价仅有一个执行边界。保留[recurrent entry-mask 回归](../../../tests/hmasd/test_discoverer_entry_masks.py)。现 main 未包含 LOE 的实验 encoder/runner，复用时须从其科学输入 `efe7d61e82b2c0aed7a634bbb2e22d7cc47430a3` 恢复相关片段并核对当前依赖，不能直接假定旧入口可运行。核心 actor、训练接口、执行映射或 evaluator 的行为变化需要独立 Reviewer；本规划本身不改代码。

按同一节点、CPU FP32、四线程报告完整 fit wall、训练/评价 actor 调用、RSS 和占用；旧 ORIGINAL/DENSE 为 95.51/185.94 分钟/fit，仅是成本参照，新四臂耗时仍未知。首批不增加 distractor 维度：增添真实用户或邻居通常会改变干扰、可服务机会和目标；只有证明某个输入干预保持任务与信息机会，才可称无关实体鲁棒性测试，否则另立问题。更长 horizon、其他 N、服务 query 和任务压力都属于后续独立设计，不叠入本批。

将来实际采用或复开前，向 Pro 聚焦询问：“在 LOE 不利且尚无聚合瓶颈证据时，这个合法条件化位置比较是否提供足够不同的投资预测，L/P/O 是否覆盖主要简单解释？”本轮不发送。若开发结果支持明确用途，再冻结一个候选、一个最强合格主对照及实际主张，用 **3–5 个全新独立训练种子/臂＝6–10 fits、2.16–3.60M 训练 transitions** 做一次条件性的最终确认，评价预算沿固定协议为 288k–480k，使用未参与选择的世界；此前选择曝光全部披露，按独立训练实例报告不确定性，允许未决且不追加种子。确认比较决定可说的是包级收益还是位置效应，不把一种结论扩写成另一种；当前仅交付规划，不激活方向或接受任何 fit。

<a id="plan-6"></a>

## 6. 从人数泛化转向负载与关键成员泛化

**主问题。** 在共同的有界动作合同下，H6 相对普通 SET 的服务差异，是否主要随需求／连接容量压力变化，而不能单凭测试人数解释？先刻画任务，再考虑表示或学习修订。本提案依据 main `d7056f6249fe593b3969d22306af6e70cb841104` 的[背景与现行状态](../RESEARCH.md)，供现有 `agent_count_generalization` DM 后续选择，不接管方向、不排队执行。

**已有证据与前置边界。** B01 的六个训练实例给出 N4/6/8 的 H6−SET 原生 J 为 +.021721/+.044000/+.045222，但实际执行的是未裁剪高斯动作；这不是已验证的有界动作结论。其 N4 增益反而较小，也不支持直接讲“技能更善于应付容量紧张”。现有 DM 已采纳 B02 冻结 raw/clip 部署比较（0 fits、288k eval steps），以及 B03 的 H6/SET×raw/clip 训练、共同 clip 部署（4 fits、1.44M train＋384k eval steps）；本计划不替代或重复它们。只有 B03 完成、读结果并固定后续动作合同后，才借用其两个 **clip-train** 终点策略。若决定更换高斯、熵或执行约束，下面设计须重新绑定，不能沿用“已纠正”称谓。[原始比较、纠正及采纳记录](../candidates/agent_count_generalization/NOTES.md#2026-09-22--full-pro-reading-b02-execution-probe-and-b03-investment-decision)。

**文献怎样改变设计。** [M3FC／MARL-0438，E1/E6/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0438.json)提示把总体分布与不可忽略成员分开，但它依赖共同 major 状态／分布；少量局部观测 UAV 不能套用其平均场保证。[MIPI／0561，E1/E4/E7/E8](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0561.json)提供减少团队信息依赖的数量迁移先例，也保留过强压缩损害服务和复现／调参敏感性，故不预设“抹掉人数信息”是改进。[Deep Sets，E2/E3](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-CCA390C5FE.json)支持现有共享集合参照；[Set Transformer，E4/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-F08EC1A407.json)中简单池化亦能获胜，暂无新增 attention 的理由。[均值场采样／0637，E1/E8/E9](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0637.json)的独立转移假设及已记录证明疑点，阻止把本项目的近邻截断说成有保证的采样。[HAGG／0184，E8/E9](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0184.json)是不同人数分别训练，且缺外部附录，不能作为固定策略数量外推或关键成员接口的直接证据。本次核对了相关本地原文段落；完整覆盖与局限以各 reading 的证据编号为准。

**可操作变量与信息权限。** [S1](../../../envs/pettingzoo/scenario1.py)提供真实 N、用户数 U、面积、用户分布和同质整数连接上限 c；没有业务到达率、队列或逐成员能力向量。定义名义负载 λ=U/(Nc)，不是实际吞吐或可达需求；实际压力还受 SINR 和贪婪分配限制。

| 轴 | 当前能做什么；本轮处理 |
| --- | --- |
| 人数 N | 真实 N4/6/8；固定回合 roster，无加入／退出。变化同时改变干扰和 UAV 密度。 |
| 需求／容量 | 保持 U=50，改变现有 c。修改 U 虽是原环境参数，却违反当前 CountAdapter 的固定 50 用户状态合同，本轮不做。 |
| 密度／空间 | 固定 1000m×1000m、均匀静止用户；不同时改变面积、热点、发射功率。这样固定用户密度，不能固定 N 改变后的 UAV 密度。 |
| 关键成员 | 当前只有同质 c、速度及功率；持久身份和异质能力不是现成 actor 信息，留作独立后继。 |

[实际观测](../../../envs/pettingzoo/uav_env.py)为 **104 维**：自身、20 个 SINR 排序用户槽、10 个 peer 槽和时间；没有真实局部有效位或持久 ID。N≤8 不触发 peer 数量上限，但阈值不可见与用户截断仍存在。中央 state 的八槽有效位用于真实 roster，与局部可见 mask 不同。保留 H6 与 SET 的既定信息／十步刷新：SET 用共享 mean/max/count 集合编码和 GRU，是主参照；不能因其简单而判弱，也不把包比较归因于技能。

**首轮：五格、零新训练。** 固定动作执行、用户世界、奖励和策略，只交叉两个未见 N 与两个总连接容量 K=Nc，并保留 N6/c10 锚点：

| 测试 N | K=40，λ=1.25 | K=80，λ=.625 | 原训练锚点 |
| --- | --- | --- | --- |
| 4 | c=10 | c=20 | — |
| 8 | c=5 | c=10 | — |
| 6 | — | — | c=10，K=60 |

这些整数上限可由现有 S1 参数实现；连接资源已改变，不能称作“人数不同但完全同任务”。容量匹配也不消除干扰／空间差异，因此不能识别抽象的纯 N 效应。每格固定 16 个开发世界、500 步；两个 B03 冻结策略共 **0 fits、80k eval team steps、160 回合**。这是每臂一个既有训练实例，不能算新增学习证据或把世界数当 seed 数。

世界生成器使用分离的用户／UAV 随机流：同一世界共用 50 个用户与八个 UAV 初始位置，按 N 取预定前缀，各臂完全一致。原 reset 先抽 N 个 UAV 再抽用户，单纯同 seed 并不跨 N 匹配用户。初始化后按原生顺序刷新信道、观测和 state，完整重置记忆／技能／timer；冻结参数、normalizer、checkpoint，不挑优点。

关键可辨识性是：c 不进入 actor/state，连接分配也不反馈到移动或 SINR。因此同 N 的两种 c 下，确定性固定策略应有相同动作／轨迹；差异是同一几何轨迹的服务转换，**不是在线负载适应**。若轨迹不同，先查隐藏输入或实现问题。不给 actor 注入分析得到的“关键成员”、连接真值或局部 mask。

**预写预测和判读。** 令 G(N,K)=J_H6−J_SET，主要读同 N 的容量交互 G(N,80)−G(N,40)，再读同 K 的人数差异。容量机会解释预测：增加 K 减少“达到 SINR 阈值却未获连接”的用户，H6 相对 SET 的额外覆盖与 J 增益在两种 N 都增大。相反，若主要是联合几何／人数条件，匹配 K 后 G 仍明显随 N 改变，而同 N 容量变化未产生上述一致服务交互。两者可以并存；不按哪一项 p 值显著机械二分。

| 观察 | 改变的判断／下一步 |
| --- | --- |
| 容量诊断及覆盖、J 同向改变 | 加强“物理机会影响包收益”的解释；仍未证明学会负载表示。 |
| 容量诊断改变，J 增益不变或反向 | 削弱预写容量机会解释；质量／高度代价可能抵消，不能继续称作预测命中。 |
| 同容量仍有人数相关差异 | 保留干扰、密度、控制／学习差异；不是集合编码失败证据。 |
| 两臂在这些格均无可辨收益 | 结束这套后继投入，或保留不确定；不自动加架构、世界、种子。 |

原生终点 **J=N·Σr/500**，同时保存原始 scalar return、覆盖比例及人数、连接质量、高度项、每 UAV 占用／满载、SINR 可接入但未服务人数和可见槽截断率；训练继续用 R/6。主比较均在同 N、同世界、同容量进行，不把跨 N 的裸 J 差当迁移收益，也不把容量上限或某个启发式当可达最优值。

**若新学习确能改变判断。** 首轮之后只考虑一个有实质区别的训练问题：仍只在 N6 训练，让两臂共同经历 c∈{5,10,20} 的均衡回合分布，检验该训练分布下的未见 N 包价值。720 回合中每种 c 各 240 回合，预先打乱；不加入容量观测，明确这是未知容量下的稳健策略，不宣称条件化适应。H6 与上述 SET 各一个新实例、各 360k steps，**2 fits、720k train steps**；采纳时核验并绑定实际新训练 seed，不靠相同编号配对。这两 fit 不能识别均衡训练相对固定 c 的因果增益，也不能把与旧 B03 的跨 seed 差异归因于训练分布。若要回答训练分布的作用，须另立 H6/SET×固定/均衡训练的匹配四格前瞻比较，不能事后借历史结果补对照；该四格不自动选中，也不加入本计划默认成本。

开发只用固定 16 世界／格，在 0/120k/240k 读曲线；360k 终点用预先封存的 32 个全新世界／格。五格合计 **400k eval steps、800 回合**，最终只读末次 checkpoint，保留锚点损失与全部不利结果；开发／最终随机流独立于 B01–B03。新学习若未兑现服务预测，不用改变故事续跑。探索有清晰价值才另写 claim，选择每臂 3–5 个全新训练种子的一次固定确认：6–10 fits、2.16–3.60M train；若只作同样五格×32 世界的最终评估，则另需 480k–800k eval steps。训练实例是推断单位；报告逐实例效应与区间，窄世界误差不能补足训练 n。无百分比过关线，无自动确认；节点 wall、加载、评估与额外优化计算均实测。

**关键成员只作条件后继。** 若负载刻画留下真正有信息价值的问题，才考虑固定 N6、总容量 60 的同质 `[10×6]` 与异质 `[20,8,8,8,8,8]`；这只是候选关键成员，不保证它实际关键。当前原生接口不支持容量向量，需要同时实现两条连接分配路径，并声明每步自身能力、合法可见 peer 能力及十步中央快照的权限，两臂相同；每回合随机放置高能力成员，不能用固定槽位代替能力。首个参照应是直接拼接合法能力特征的普通 SET／FiLM。新增能力、通信或输入属于新任务合同，不可给旧 checkpoint 换标签就称泛化；本提案未选择该批次或 fits。

**工程落点与未来 Pro 问题。** 方向包目前在其已发布分支，主索引保留证据链接；实际已读 `experiments/candidates/agent_count_generalization/{adapter,configuration,models,runner}.py`。后续仅新建该目录下 `load_probe/` 的场景工厂／评估入口，复用 B02 已接受的 checkpoint、动作映射和冻结检查，不改冻结 B02/B03。`adapter.py:make_envs` 现锁定 U=50/c10，需显式传 c；`runner.py:evaluate_panel/native_components` 可复用奖励检查，但面板须扩展为 (N,c)。`models.py:StateSetEncoder/SetActorBase` 首轮不改。S1 构造器在父类 reset 后才写 c，场景工厂必须设置最终参数后再 reset；共用初态的重建须正确刷新缓存。若未来实现逐成员能力，才触及 `envs/pettingzoo/scenario1.py` 和 `uav_env.py:_greedy_connection_assignment`，不能只改 vectorized 路径。检查包括真实容量、共同初态、同 N 轨迹恒等、零更新、J 分量恒等、失败保留；环境／评估变更由独立 Reviewer 检查，执行前再按现行方法准入。

采纳前交给 Pro 的集中问题是：“在 B02/B03 的实际结果及动作合同下，这个五格容量匹配是否足以区分服务机会与人数相关差异？隐藏 c 下的零训练读数和后续均衡负载训练各能改变什么判断，普通 SET 是否已是充分强的参照，是否值得购买这两个新 fits？”现在只留下问题，不发送咨询、不实施、不启动。

<a id="plan-9"></a>

## 9. 发现实际互补的技能

**首问：事实组合回报辅助能否改善共同学习出的有用技能？** 先比较一个可实施的辅助训练包；“产生了因果互补奖励”不在首轮结论内。本项只作提案，不恢复已归档的 cap=10 时长路线。依据 [RESEARCH 主题3–5](../RESEARCH.md#3-marl-增加的是联合行为和信息结构)，固定 **S1、N=6、k=10、团队/个体标签各6个**，保持高低层及判别器共同学习，不要求冻结旧技能先通过阳性门槛。

**证据怎样改变设计。** [HMASD，MARL-0553:E1–E3,E8–E9](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0553.json) 已有团队潜变量、AR 分配和局部技能；其少量有用技能统计只构成动机，不能移作 UAV 瓶颈测量。[R3DM，0480:E2,E5–E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0480.json) 支持未来条件监督的可行性，但角色可分辨仍不保证团队用途。[AVGM，0209:E3–E4,E9](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0209.json) 与 [DAVE，0551:E1,E4,E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0551.json) 提醒我们联合支持和乐观搜索会改变结果，故不用“查询最大Q”制造训练真值。旧 [FSD B13/B14](../candidates/flexible_skill_duration/NOTES.md#2026-09-21-0343-pdt--b14-read-no-reversal-the-ten-step-credit-carries-a-real-but-small-gain-in-its-own-regime-and-points-the-wrong-way-on-one-block) 的加性标签信用没有稳定增益，削弱只改高层计数信用的投入理由；它没有测试形成技能时的伙伴条件辅助，也没有排除身份、状态条件交互。

**最小学习改动。** 技能边界 t 保存真实标签、状态/观测、低层循环状态和行为概率。令 $e_i=f_\theta(o_i,h_i,z_i)$ 为现有低层 actor 的技能条件特征，$x_t=(s_t,o_{1:6,t},h_{1:6,t},t)$；h 是分配新标签前的循环状态，x 中存储值均截断梯度。增加训练用回归头

\[
Y_t^{50}=\sum_{\ell=0}^{49}\gamma^\ell R_{t+\ell},\qquad
\hat Q=b(x_t,Z)+\tfrac16\sum_i u(x_t,Z,e_i)
 +\tfrac1{15}\sum_{i<j}g(x_t,Z,e_i,e_j).
\]

R 为原生团队奖励，γ=.99；g 暂用秩32双线性项。标签只来自当前 rollout 的真实50步：前10步执行本次技能，后40步按当时实际行为策略继续重选；不重标旧轨迹、不拼接另一组合的后果。只用 t≤450 的完整窗口，50步处无虚构 bootstrap；原有 PPO 仍承担完整回合信用，辅助不改奖励、判别器或高层优势。目标按训练数据标准化，以均方误差训练，损失系数暂定 .05，每 rollout 单遍。辅助梯度进入低层 encoder、FiLM 和当前 GRU 步，存储的进入隐状态截断梯度；不进入高层 coordinator。另拟合一个独立加性头，仅作诊断。两头的数值分解没有唯一因果信用含义。这个改动可能改善表示，也可能只提高可预测性，因此收益必须实测。

**信息与执行。** [现有高层](../../../hmasd/networks.py) 每10步读取全局状态及所有观测；低层每步只读自己的观测、技能和循环记忆。联合输入、未来事实标签只供训练头，部署删除辅助头，不向低层泄漏伙伴隐状态或未来。沿 [实际低层更新](../../../hmasd/agent.py) 保留原生 PPO、熵系数、归一化和判别奖励。所有臂统一在环境入口执行 `clip(raw_action,-1,1)`，PPO 保存并评分原始高斯样本，不能把裁剪值代入高斯密度；这是针对 [当前动作接口](../../../envs/pettingzoo/uav_env.py) 的共同修正，旧未裁剪成绩不能作新对照。

| 探索臂 | 技能曝光 | 辅助梯度 |
| --- | --- | --- |
| N：普通 AR-HMASD | 原有 AR | 两预测头仅在 detached 特征上训练 |
| E：匹配曝光 AR-HMASD，主参照 | 每个个体因子10%均匀混合 | 同 N |
| P：事实组合辅助 | 同 E | pair 头梯度进入低层；加性头仍 detached |

主对比固定为 **P−E**，E−N 只判断额外组合曝光是否足以解释收益。对合法支持 $A_i$，令高层原有输入 $c_t=(s_t,o_{1:6,t})$；不新增伙伴隐状态输入。实际采样与 PPO 重放均使用

\[
\mu_i(z_i\mid c,Z,z_{<i})=(1-\epsilon)\pi_i^{A_i}(z_i\mid c,Z,z_{<i})+\epsilon/|A_i|,
\]

其中 N 的 ε=0，E/P 为 .1；团队因子仍为原 AR。保存实际前缀、mask 与 `log μ_old`，更新重建同一条件律并评分 `μ_new/μ_old`，不在原策略采样后偷偷替换技能。P/E 的环境步数、混合率、PPO epochs、选择机会和调参权相同；实际访问频率仍会随学习改变，须报告联合/边际占用，不能声称轨迹完全相同。

**真正的留出与非加性检验。** 训练前按固定随机键选4个二人矩形：成员对为(0,1)、(2,3)、(4,5)、(1,4)，各固定一个不同团队标签和其余成员标签，两名成员各取两个标签，合计16个完整联合组合。三臂均在最后一个 AR 因子处屏蔽这些完整组合并重归一化；选表保证合法支持非空。单标签和二人搭配在其他完整组合中的学习保留；因此只测未见完整组合，不宣称陌生伙伴泛化。留出组合不得进入 PPO、辅助或调参数据。每个训练实例预先独立随机置换标签编号；跨种子只比较回报、预测误差和选择增益，不把“技能2”当同一技能，也不额外宣称 cross-play。

own-team评估、最终统一选择器面板及诊断的前缀/后40步续接都保留训练时的完整组合 mask；统一选择器在合法支持上逐因子均匀采样。只有四格诊断的首个10步允许强制执行16个留出组合，其数据永不回流训练。最终冻结模型，在16个新世界用该统一选择器走到第200步，复制完整环境、RNN及随机流。每个前缀执行4个矩形的全部四格：仅干预本次10步技能，随后40步恢复该冻结模型的实际随机行为律 μ，低层同样按训练时的高斯采样并裁剪。得到真实四格回报与

\[
\Delta_{ij}^{50}=E[Y_{ab}-Y_{a'b}-Y_{ab'}+Y_{a'b'}].
\]

这是指定前缀分布、一次技能干预及后续策略下的有限窗交互，不是永久保持技能或成员固有贡献；对应 [因果分解，0454:E1,E8,E10](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0454.json) 的识别与成本警示。测试前由训练好的 pair/加性头各选一格，比较其**真实**执行回报，不根据四格测试分数挑“最佳”。大 |Δ| 也可能来自坏搭配，须同时看到有用的选格增益；模型预测只供预选和误差检验。全部支路零更新，不做每个训练状态的分支搜索。

**终点、归因与失败分支。** 主终点为360k后的确定性 own-team 原生 J=6×平均回合 learner return/500，并读覆盖、SINR、高度罚；S1 高度罚不能解释成电池耗能。保留0/120k/240k曲线，不选最好 checkpoint。最终另以相同均匀技能选择规则评估低层库：P−E在此仍正、留出真实选格收益及交互预测改善，才加强“发现出了更有用的组合”解释；若只 own-team 正，低层与高层共同适应仍未分离。若 E−N 有益而 P−E 无益，普通曝光解释优先；若只有 MI、预测误差或 |Δ| 改善而原生收益不增，停止该辅助配方。若原生收益正但组合诊断不支持，只保留通用辅助包结论。P−E尚未排除普通加性辅助也足够；若要声明pair结构必要，须另立梯度同样进入低层的加性辅助对照，匹配更新与容量，不能自动加臂。[CPA，0069:E1–E3,E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0069.json) 的协调模式一致性属于备选#10；[RPG，0661:E7–E8](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0661.json) 也说明低搭配分数不等于有用多样性，本项不以制造不兼容为目标。

**暂定成本。** 三臂各2个独立新训练实例，采用时核验并一次绑定6个未使用种子，不按旧开发块配对；**6 fits ×360,000 =216万训练 team steps**。沿已测16 lanes×500 steps×45 rollouts、15 PPO epochs：每 fit 36,000次团队技能决策、33,120个完整辅助窗口；batch128单遍、每轮保留末个不满批次，共270个辅助 minibatch，每个预测头各更新270次，P相应增加270次低层辅助更新，须另报其梯度与墙钟成本。四个常规评估面板每次32×500，共38.4万步；最终统一选择器面板9.6万步；四格诊断每 fit 为16×200前缀步+16×4×4×50分支步，六 fits 共9.6万步；**总评估57.6万步**。评估世界及留出随机键在执行前登记；episode、窗口、格子都不增加训练 n。历史 [固定臂](../../../runs/joint_duration_skill_learning/b01_fixed_r1_s2026092201/summary.json) 在 `wsl_4070` 为4340.447秒/fit，六倍约7.23 fit-hours，仅作旧配置参照；新辅助、裁剪及额外评估的墙钟未知。优先该节点，实际准入才决定并发。

**实施边界与后续。** 未来局部 adapter 承担混合采样/重放、成组边界样本、辅助梯度和四格 evaluator；复用 `SkillCoordinator`、`HMASDAgent`、`RolloutBuffer`，不另造技能系统。独立 Reviewer 核对真实概率、留出零泄漏、原始/执行动作、50步续接、RNN进入掩码、训练头权限和 evaluator 零更新；测试须穿过收集→存储→更新，不只测网络函数。本轮两个训练实例/臂只作探索，负结果不自动加种子或延长尾部；若值得确认，再固定实际主张、P/E两臂及3–5个全新种子/臂，另计6–10 fits。

未来 Pro 聚焦问题（**此处不发送**）：在上述事实标签和固定 AR 主参照下，低层 pair 辅助是否提供区别于普通预测正则化的可检验价值？P−E、统一选择器和有限四格结果各能排除什么；若仍不足，最小的下一辨别比较是什么，或应否就此停止？既有固定技能阴性证据应怎样限制预期，而不变成新技能共同学习的准入门槛？

<a id="backup-plans"></a>

## 其余 17 项：简要备用计划

这些条目保留研究问题及展开入口，不承诺遍历，也不预分配训练。已有模块只是实现材料；展开时先查最近先例，
再选一项能区分普通解释的比较。所需数据、模型或设备可以成为后续建设内容，不因暂缺而删除构想。

<a id="plan-2"></a>

### 2. 任务对称性与预测表示

- **假说：** 对用途相同的队友施加身份区分的负样本监督，可能浪费有限表示；但删除承担协作约定的身份会有害。
- **首个比较：** 固定 actor 的身份/角色输入，比较原对比辅助、同类型负样本过滤、无负样本预测及普通服务辅助。
  在可交换成员与互补角色两种明确条件中读换编号/换搭档和正常搭配 J，不能只比较 contrastive loss。
- **展开条件与收束：** 先定义合法任务对称性，不能从“同类型”直接认定“同用途”。若简单过滤已吸收收益，
  保留它；若只是抹掉角色导致合作下降，结束该不变性假说。可接用计划 1 的辅助接口，但不依赖其阳性。
- **依据：** [MA²CL，MARL-0502，E2/E3/E11](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0502.json)。
  BYOL 替代较弱的反证须保留，不能预言无负样本方法普遍更好。

<a id="plan-4"></a>

### 4. 专业化模块的时间尺度

- **假说：** 慢上下文组织专业化子空间、快观测直接驱动动作，可以减少路由追逐噪声；真实责任突变时过慢刷新反而损失服务。
- **首个比较：** 同合法历史下比较身份条件 HyperMARL、逐步观测路由、普通 GRU+FiLM、EMA 上下文和少量固定刷新频率。
  分别操纵责任变化速度与无关观测噪声，预期出现交叉优势；读取切换后的累计服务损失、恢复时间和路由成本。
- **展开条件与收束：** 需要真实可识别的能力/责任变化，不能把隐藏角色标签送入候选；静态同质任务可能没有该机会。
  若简单 EMA/GRU 足够，就不增加复杂路由。与实际队友漂移 reserve 相邻，但不等同于自身 RNN refresh。
- **依据：** [HyperMARL，MARL-0622，E1/E2/E4/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0622.json)、
  [ADMN，MARL-0514，E1–E4](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0514.json)。

<a id="plan-5"></a>

### 5. 可组合的小模块迁移

- **假说：** 共享主干中的物理/服务规律与搭档相关修正可以部分分离；独立学到的小模块在未见“物理条件×搭档策略”组合中仍有用途。
- **首个比较：** 对同源训练数据，比较可组合残差、普通联合上下文 FiLM、只调头、全量微调和从头学习。
  预留真正未见的组合，读取目标 J、源条件遗忘及获得主干、各模块和目标适配的全部成本。
- **展开条件与收束：** 需要多源任务和明确的目标更新权；没有可迁移先验时冻结主干可能限制学习。
  若只有原搭配有效、普通上下文模型已解决或预训练成本抵消复用收益，则收缩可组合解释。
- **依据：** [LoRA，DMOD-5C109D4521，E1/E4/E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-5C109D4521.json)、
  [BiKT，MARL-0609，E5–E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0609.json)。
  不把权重幅值/方向先验解释为物理/合作语义。

<a id="plan-7"></a>

### 7. 动作—时长的后果压缩与组合

- **假说：** 短期后果相同的技能可能在长时域分裂；按期限学习后果类别及可组合转移，可能改善未充分覆盖时长的决策。
- **首个比较：** 相同真实片段上比较普通 duration-conditioned GRU、一步循环模型、多期限直接头与后果类别模型。
  先读持出期限的任务相关错排；进入控制比较后读取完整 J，核算模型与候选查询。
- **展开条件与收束：** 固定真实续接规则、闭环技能记忆和合法队友承诺。误差应能区分步数与队友重选边界；
  不把均值递推当分布组合，也不用未执行的提前切换后缀作事实。普通循环模型足够则不增加类别结构。
  更长承诺需要实际时钟/支持和相应固定参照，不重启旧 cap=10 或 SCDMP 配方。
- **依据：** [TempoRL，DMOD-19F190C762，E1–E3/E8](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-19F190C762.json)、
  [AVGM，MARL-0209，E4/E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0209.json)。

<a id="plan-8"></a>

### 8. 由真实反馈校准的训练想象

- **假说：** 会改变行动排序/更新方向的模型误差，比归一化 ensemble 分歧更适合决定合成数据的用途。
- **首个比较：** 对同一实际模型和反馈预算，比较 model-free、固定短想象、普通真实/合成混合、相对分歧与事实校准。
  区分行动相关的共同偏差和行动无关加性偏差，预期仅前者使对应校准具有明显价值。
- **展开条件与收束：** 当前 USA 尚非训练想象系统，需要明确新增模型、合成更新和真实纠错接口；验证行动后果须付真实交互成本。
  读取真实数据需求、J 和总计算。若收益只是减少更新的正则化，或普通短想象达到同效，停止复杂机制。
- **依据：** [CLWPO，MARL-0060，E4–E6/E10](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0060.json)、
  [PAR，MARL-0180，E2/E6/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0180.json)。

<a id="plan-10"></a>

### 10. 技能重组中的协作模式一致性

- **假说：** 联合支持充分仍可能因成员选择不同成功模式而失败；这与计划 9 的“是否存在有用互补技能”是不同解释。
- **首个比较：** 在具有多个成功分工的真实重组条件下，匹配曝光，比较原 HMASD、普通 population mixing、
  合法共同信息下的固定约定/共享 latent；检查组合冲突、重复/遗漏服务以及 own-team 和重组 J。
- **展开条件与收束：** 明确私有历史、公共 key、消息/同步权；原系统已有 team latent/AR，不能先削弱再补回。
  若收益仅来自更多组合曝光或固定约定足够，保留该简单解释。采用前核对 CPCP 与旧 RCLE 的具体停止边界。
- **依据：** [CPA，MARL-0069，E1/E3/E4](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0069.json)。

<a id="plan-11"></a>

### 11. 时间抽象用于联合探索

- **假说：** 训练期间有适当持续性的相关探索，更容易形成需要连续配合的成功序列；最终部署策略类可以保持不变。
- **首个比较：** 同最终 actor 比较普通共享 latent、持久动作噪声、UTE/formation 探索与关系条件持久探索。
  读取首次有效配合、去掉探索奖励后的最终 J 和实际更新数，保留解耦及需快速响应的反面条件。
- **展开条件与收束：** 当前 S1 稠密反馈可能限制收益；若新增稀疏/延迟任务，明确其新范围。
  相同环境步不保证相同高层优化量；只提高熵或序列新颖度不成立，普通持久噪声足够则不追加模块。
- **依据：** [UTE，VS-0005，E6/E11/E14](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/VS-0005.json)、
  [FoX，MARL-0036，E2–E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0036.json)。

<a id="plan-12"></a>

### 12. 面向目标迁移的可学进展课程

- **假说：** 可降低、且对固定目标分布有帮助的误差，比最高 TD 残差更适合分配训练世界。
- **首个比较：** 优先固定 N/k、原任务分布和总交互量，只改变初始世界抽样分配；比较均匀、残差优先、
  普通 EMA 验证进展与目标相关进展。课程验证世界和最终新世界分开，验证 rollout 全计成本。
- **展开条件与收束：** 先核实可复现 reset 与候选世界池，保持原分布覆盖。高误差未必可学，团队共同进步也未必迁移。
  若只降验证 loss 不改善目标 J、普通 EMA 已达同效或验证耗时抵消收益，则不采用复杂 teacher。
- **依据：** [SPMARL，MARL-0471，E1/E8/E9](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0471.json)、
  [PORTAL，MARL-0048，E1/E3/E5](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0048.json)。

<a id="plan-13"></a>

### 13. 跨团队离线经验复用

- **假说：** 整体表现差但部分成员有用的数据，可在保留原合作上下文时帮助学习；盲目合并边际行为可能恶化联合支持。
- **首个比较：** 固定真实数据量/质量，改变来源团队多样性和成员质量不均，比较全量/筛选/加权 BC、普通行为正则与联合支持方法。
  保留真实同场轨迹，不拼接不存在的转移；读持出团队 J、支持条件及目标更新成本。
- **展开条件与收束：** 先核实是否实际保存完整连续离线数据；若需新采集，策略生产与数据取得全部计入。
  若加权 BC 已解决，或关键联合行为缺失使选择性复用失效，就不声称能从个体优势恢复团队策略。
- **依据：** [SIT，MARL-0015，E3/E5/E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0015.json)、
  [AlberDICE，MARL-0544，E1/E2](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0544.json)。

<a id="plan-14"></a>

### 14. 部署前的团队编组

- **假说：** 同等能力与出动成本下，任务相关互补性可使有限校准选出的团队优于单体 top-N 或最佳原团队。
- **首个比较：** 固定权重和回合内 roster，按相同探测预算比较最佳完整原队、top-N、普通匹配/成对收益模型和学习选择器。
  在持出任务读取实际服务、探测成本及选队时间，不能事后从最终测试团队中选最好。
- **展开条件与收束：** 需要真实成员选择权和接口兼容的策略池；不同 seed 的技能标签不是天然对齐的成员库。
  若普通成对匹配吸收收益或优势仅来自更多试队次数，停止复杂选择器。与固定队伍 cross-play、运行中 churn 分开。
- **依据：** [MA-TLQL，MARL-0224，E1/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0224.json)
  只提供“选择价值须匹配后续执行”的桥梁，没有直接验证本部署编组任务。

<a id="plan-15"></a>

### 15. 相关失败与团队尾部风险

- **假说：** 相同个体边际故障率下，相关故障或集中返航造成不同团队下尾；利用依赖结构可改善均值—尾部前沿。
- **首个比较：** 固定边际扰动率而改变相关性，对同一风险目标比较调优 scalar 失败/成本模型、Lagrangian、普通 CVaR 和分布 critic。
  读完整 J、服务下尾、成本上尾与真实风险事件，不以局部分位误差替代服务。
- **展开条件与收束：** 继承 TRDL 的证据和强 scalar 参照；当前 USA 评估没有充电/切断/耗尽事件，须有真实风险曝光。
  单独计稀有事件评估量。若 scalar 达同一前沿或均值损失不可接受，停止复杂分布结构；仿真结果不称物理安全保证。
- **依据：** [RiskQ，MARL-0563，E1/E6/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0563.json)、
  [分布安全 critic，MARL-0189，E1/E3/E4](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0189.json)。

<a id="plan-16"></a>

### 16. 服务连续性与分配偏好

- **假说：** 相同总服务量下，连续断供、最差用户处境或资源牺牲分布仍产生稳定偏好，现有标量目标遗漏了这部分效用。
- **首个比较：** 先用真实轨迹对检查持出偏好；比较已知服务统计的可调目标、轻量 Bradley–Terry、普通 LSTM 和合作时序模型。
  后续策略比较同时读持出偏好、持续断供、最差用户及事先声明的平均服务底线。
- **展开条件与收束：** 需要个体服务历史、明确价值取舍和真实标签；脚本/LLM 标签只能测试流程，不能冒充人的偏好。
  标签制作成本计入。若已知统计模型已解释偏好，或标签准确但政策无用途，就不增加合作奖励模型。
- **依据：** [MAPT，MARL-0031，E2/E4/E5](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0031.json)、
  [O-MAPL，MARL-0477，E1/E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0477.json)。

<a id="plan-17"></a>

### 17. 端侧更新能力与模型容量分配

- **假说：** 局部映射变化和伙伴行为变化需要不同更新自由度；成员之间更新收益也可能互补，不能只按单层贡献相加。
- **首个比较：** 在同一可行设备约束下，比较冻结但更新 GRU 状态、head/bias-only、LoRA、末层和可行全量训练；
  再按同更新量比较固定/随机成员集合与联合配置。读适应期服务损失、恢复及旧任务性能。
- **展开条件与收束：** 需要真实端侧反馈和训练后端，实测每设备峰值激活/优化器/权重内存、更新时间和能耗。
  参数少不等于内存少，共享参数不等于设备免费共享存储。普通末层/GRU 足够时不增加联合配置。
- **依据：** [256KB 训练，DMOD-EE01216DA8，E2–E4/E12](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-EE01216DA8.json)、
  [TinyTL，DMOD-1AFADC3495，E1/E4/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-1AFADC3495.json)。

<a id="plan-18"></a>

### 18. 保持协作关系的量化

- **假说：** 相近个体输出误差可能带来不同联合控制损失；按团队决策敏感度保留少量精度可优于逐 agent 重构目标。
- **首个比较：** 冻结同一浮点策略，比较单成员、指定成员对和全队量化；同后端下比较统一 INT8/INT4、普通 PTQ/QAT、
  个体敏感度配置与团队配置。连续动作同时检查均值、方差、循环状态和实际执行位移。
- **展开条件与收束：** 先固定真实动作法；成本包含反量化、补偿、混合精度内核和激活。读 J、联合错配及实际存储/延迟。
  若个体敏感度已解释损失、普通 QAT 达同效或硬件没有实际节省，不增加团队量化结构。
- **依据：** [QA-LoRA，DMOD-1BB8E291C0，E1/E2/E9](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-1BB8E291C0.json)、
  [MiLo，DMOD-D109F00D57，E1/E4/E6/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-D109F00D57.json)。

<a id="plan-19"></a>

### 19. 保留关键团队决策的蒸馏

- **假说：** 保留少见但高后果的联合修正，比降低平均特征/动作模仿误差更能保住教师的服务用途。
- **首个比较：** 同有用教师和学生容量，比较小模型直接 RL、普通 feature/logit KD、无权重增量压缩与任务后果加权。
  若涉及多种协调模式，给普通 team-latent/CPA 同样公共信息。必须在学生自己诱导的轨迹上读 J 和关键错配。
- **展开条件与收束：** 当前没有已核实的强教师，可先建设并检验教师；教师数据、训练、蒸馏与目标微调全部计成本。
  教师额外全局信息另作比较，公共随机数不能补全不可见状态。普通 KD 或固定分工足够时收缩复杂压缩。
- **依据：** [PTDE，MARL-0524，E1–E5](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0524.json)、
  [CPA，MARL-0069，E1/E3/E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0069.json)。

<a id="plan-20"></a>

### 20. 联合策略的草稿与并行验证

- **假说：** 对较长且可合法批量评分的联合前缀，廉价草稿与验证有机会改善完整决策延迟；收益依赖前缀长度、接受率和负载。
- **首个比较：** 冻结目标策略，比较优化缓存/分块/批量评分与普通草稿、学习草稿。严格校正版本验证联合分布保持；
  近似接受版本单独读 J—延迟前沿，不能借用精确保证。蒸馏成并行学生归入 19。
- **展开条件与收束：** 先有真实串行瓶颈和验证接口；未来环境观测不是已知 token，也不能执行后撤销动作。
  测团队尾延迟、吞吐、cache、能耗；没有实时期限时，加速不自动提高模拟器 J。缓存已吸收优势或验证更慢则停止。
- **依据：** [Speculative Decoding，DMOD-6626D5050C，E1–E5/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-6626D5050C.json)、
  [负载/性能反证，DMOD-25AD9265EE，E2/E3/E6](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-25AD9265EE.json)。

<a id="plan-21"></a>

### 21. 昂贵计算的联合调用

- **假说：** 贵模型/更多搜索的收益依赖伙伴同时采取哪条计算路径，独立门可能错过互补调用或重复付费。
- **首个比较：** 固定便宜/昂贵选项与共同决策时刻，先读有界的成对调用干预，再比较同调用预算的固定成对、随机、
  独立收益阈值、透明 VoI 和小型联合门。逐决策价值必须固定续接规则；四个全程固定配置的 J 不能直接成为逐步 gate 标签。
- **展开条件与收束：** 需要确有用途差异的计算选项；门只能使用付费调用前合法可得的信息。
  平均预算和峰值预算分开，计门、通信、驻留/切换、等待和全部前向。互补不可预测、普通配对足够或协调成本抵消收益则停止。
- **依据：** [RouteLLM，DMOD-227EA09099，E1/E3/E6/E7](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/DMOD-227EA09099.json)、
  [VIL2C，MARL-0203，E2/E3/E8](/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/MARL-0203.json)。

## 后续采用的顺序

1. 四项详细计划可以并行做实现前推理；实际学习仍由各自负责人选定一个有信息价值的比较。
   计划 1 接续 USA，计划 6 衔接现任人数 DM 的已选 B02/B03，计划 3/9 需采用新的具体问题，不能冒用旧 archived 配方授权。
2. 计划 3 与 9 若都改变低层表示/技能学习，首批分别保持另一部分原样；待独立证据形成后才考虑组合，防止来源不可分。
   计划 1 的新监督也不默认加入 3/6/9；不同宿主的 J 不合并排名。
3. 备用项按出现的真实科学问题展开，不自动填满并发。17/18/20 需要设备证据，5/13/14/19 需要可复用模型或数据对象，
   16 需要真实偏好，15 需要风险曝光；建设这些条件可以是研究内容，但必须连同成本和目标写清。
4. 选中后只在现有 NOTES / CLAIM / runs 与 RESEARCH 中维护执行和结果。本设计保留本次 owner 要求及证据基点，
   不追加为另一套常驻进度表。本次实际新增训练、冻结策略评估与 Pro 发送均为零。
