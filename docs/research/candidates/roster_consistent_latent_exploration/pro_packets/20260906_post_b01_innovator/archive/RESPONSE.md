# 直接做一个改步长的配对 B，不把单臂“先学会”设为门槛

**方向层决定：选择选项 2 的一个明确版本，开启新的、结果知情的 B/EXPLORE：`RCLE-TBCFV-B02-NORM-0p02`。** 在不改变 TBCFV 物理宿主、公共信息、两个包、初始化和回报的前提下，两臂均将每次非零联合更新的全参数欧氏步长从 0.0005 改为 **0.02**；使用 **一个新的配对训练种子 18**，每臂 **200 次完整更新、每次 64 个 episode**，最终模型在八个 held-out 格各评估 **256 个 episode**。本新对象以两条 ACTIVE_CONTINUATION 成员变化路径的 **U 差为主**，保留 τ、删失比例、40U 和 Y 曲线。另做一次共享初始化评估和一次同情景 INDEPENDENT-NEAREST 参考，不增加训练臂或候选步长。

这是一次同时观察原生服务学习和包差异的最小投入，不是对 0.02 的充分性保证，不是“已找到合适学习率”，也不是补做或修复 B01。理由是：B01 的真实、完整、但几乎未改善的学习观察已经足以支持一次具名学习器改动；用近似原有交互规模改变一个明确的更新量，比先增加到单臂 4,000 次、再把“出现完美恢复”当作两臂比较的资格，更直接且投入更小。B01 保留原来的 τ 主测量及混合／未决读法。本轮不停车，不冻结 C，不更改定义卡或规范，不作 Portfolio 生命周期、优先级、容量、融合、注册动作，不授权五臂二十 block 方案，也不接受源码或启动调用。[B01 卡 §§1–6][b01card]；[经验规范 §§5.2、11.8–11.9][spec]

## 一、B01 已经支持的观察，与尚未支持的解释

**直接记录。** B01 是一个配对训练重复，不是零学习器探查：seed 17 的每个臂完成 200 次更新、12,800 个训练 episode、2,048 个 held-out episode，实际非零更新数为 200。两臂八个 held-out 格的 τ 均值都是 40、τ=40 比例都是 1；两条主路径的配对 τ 差和 U 差均为零。逐情景结果和训练回报曲线相同是结果 intake 和包中报告的观察；本咨询核对了机器汇总、配对主量及部分曲线和情景行，没有重新执行全量逐位比对。[结果 intake][intake]；[C1P1 summary：configuration、counts、cells][c1]；[FLEX summary：counts、paired_primary][flex]

| B01 的活动变化路径 | C1P1／FLEX 的 τ | C1P1／FLEX 的 U | 最近信标参考 U | 最近信标参考 τ=40 比例 |
| --- | ---: | ---: | ---: | ---: |
| 8→12 | 40／40 | 0.692928／0.692928 | 0.243791 | 254/256 |
| 12→8 | 40／40 | 0.718079／0.718079 | 0.302246 | 247/256 |

上表是已记录的格均值，显示位数作了舍入。最近信标参考在两条路径上留下的需求明显更少，却仍很少完成连续四个 tick 全服务。因此，**“τ 离开 40”不能充当是否发生有用学习的通用资格线**。U 的改善可以先于首次完美恢复；反过来，一次偶然 τ<40 也不能证明策略已具备充分能力。这个判断来自两个真实服务量的关系，不需要先寻找最优控制器。[reference summary：cells、eight_cell_mean][reference]；[宿主定义：Treatment-blind physical endpoints][host]

B01 的含义仍是原卡第 3、4 行的极端情形：本次未观察到值得主张的包差，恢复指标完全饱和，学习性能未决。配对标准误为零只描述该组情景上的差值，不是训练种子总体的不确定性为零，也不是等价证据。两个学习器均差于这条脚本参考的有限面板事实保留；它不等于稳定劣势，更没有把最近信标参考变成调优的同信息通用学习器或数值上参考。H_A1 仍未识别。[B01 卡 §5][b01card]；[结果 intake][intake]；[经验规范 §§11.7、11.8.3][spec]

### 需要收窄的三个因果说法

**第一，1.4×10⁻⁸ 不是两条参数轨迹的距离。** 两个 summary 报告的是各自从同一初始化出发的最终位移范数：0.005124953442186519 与 0.005124967677931276。二者相减约为 1.4236×10⁻⁸；这是两个标量范数之差，不是 `‖θ_FLEX−θ_C1P1‖`，更不是 FLEX 更新头的梯度范数。在共同初始化、数值读数成立的前提下，反三角不等式只把其绝对值给成两臂最终参数距离的下界，不能给出所声称的微小上界或定位差异来源。所读 `event_plan` 确有 FLEX 专属图，CM 记录也有路径检查；这些与已接受执行记录共同支持继续使用当前实现，但不能仅由这个标量差证明“通路必然正确”。[C1P1、FLEX summary：initial_parameter_norm、final_displacement][c1] [flex]；[models.py：event_plan、make_pointer_inputs][models]；[CM 记录 §§2、7][cm]

**第二，共享抽样不强制两个不同策略永远相同。** 在同一状态和同一均匀数下，概率变化只有跨过某个累积概率边界才改变离散选择，这是有力的相容解释。但目前没有逐状态累积概率间隙、函数敏感性或所有新种子的界；小参数位移也不直接等于小函数位移。结果量相同本身还不能重建所有中间动作。于是，“本次相同结果与小更新、零头起点及共同随机数相容”可以保留；“换一个独立种子仍必定相同”“已经唯一排除了所有接线问题”不能由现有读数推出。这里不要求新增轨迹普查或复现实验，也不推翻 B01 的有效状态，只把解释限制到已有证据。[DM 提案：What B01 observed、Unknowns][options]；[宿主定义：Frozen learned arms、Training, matching, and checkpoint law][host]；[经验规范 §§11.8.5–11.8.7][spec]

**第三，固定范数读数要区分算法量和独立测量。** `registered_plain_sgd_step` 计算原始梯度范数并应用规定的归一化更新，但返回的 `parameter_delta_norm` 是 `NONZERO_UPDATE_NORM` 常数，不是再次逐张量测出的实际差范数。它能与所读更新式一起说明预定步长；最终位移另有报告。200×0.0005=0.1 是路径长度上界，不是实际净位移或学习能力下界。B01 让这个法则成为值得改动的探索因素，没有证明归一化 SGD 本身错误，也没有使旧定义中该法则失效。[models.py：registered_plain_sgd_step][models]；[config.py：GRADIENT_DIRECTION_SCALE、LEARNING_RATE、NONZERO_UPDATE_NORM][config]

本轮不执行新的故障定位；没有直接缺陷证据就不把有效 B01 隔离。若下一实现中发现威胁真实训练、回报或比较的具体缺陷，才按其依赖处理，不能把“相同结果”本身当故障或有效性失败。[经验规范 §§4、11.8.7][spec]

## 二、为什么不接受 DM 的前置阶梯，以及最强反对意见

DM 的选项 1 有两个独立问题。真实环境、策略、反向传播和原生评估组成的“能否学会”观察属于 **B/EXPLORE**，不因只训练一个臂、不主张处理效果就变成 A/RECON。更重要的是，“先使 C1P1 达到某种能力，之后才允许比较 FLEX”把一个不必要的资格条件放进了前置对象；换成 A 名称也不能绕过 §11.9。单臂学习量 B 可以在回答自身值得投入的问题时成立，但本例已经有廉价、可比较的两臂路径，没有必要把它作为必经关口。[经验规范 §§3、5.1–5.2、11.4、11.9][spec]；[DM 提案：Options 1–3][options]

复杂度先按实际观察计数，而不是按“A”或“native”标签判断：单臂到 4,000 次需要最多 256,000 个训练 episode，并有多个检查点评估；两臂都到 4,000 次是 512,000 个训练 episode。本次选择仍只有两臂共 25,600 个训练 episode，没有候选策略、联合动作或未来轨迹搜索。单臂到 4,000 次的训练 episode 是本次整个两臂对象的十倍。800 次是原完整方案每个独立 block 的训练长度；4,000 次是新提出的曝光，不是现有结果已经支持的“卡片下一级”，二十个独立 block 也不能接成一个已验证的长训练曲线。一个有限阶梯无论结果如何，都不能决定“任何预算下”是否值得比较。[曝光与成本记录：prospective_option_1_learning_amount_ladder、prospective_option_3_larger_budget_pair][cost]；[宿主定义：Training, matching, and checkpoint law][host]

**对本选择的最强反对意见**是 0.02 可能主要放大梯度噪声、使策略更差，甚至仍未带来有意义的函数变化。它是旧步长的四十倍，但没有量级扫描或功效证据证明恰好合适。选择它只是把“200 次下运动太弱”的活解释变成一个明显不同、交互量不变、成本风险有限的尝试；不是证明参数范数的某个比例就能学会。零初始化头的有效梯度分配、manager 的高方差 score 项、actor 对 latent 的敏感性、任务协调难度等仍是活解释。把这些全部查清后才开始下一次训练，反而超出了当前决策需要。[models.py：averaged_episode_score、exact_advantage_loss、registered_plain_sgd_step][models]；[宿主定义：Training, matching, and checkpoint law][host]

我不选“去掉归一化、原始梯度乘 0.01”作为本次改动。记录中第 175 个零基更新索引处的原始梯度范数约为 0.04389；仅把该已记录梯度代入普通 0.01 步长，更新范数约为 0.000439，反而与原 0.0005 接近。早期范数较大，作用又会不同。这只是对已有读数的条件算术，不是普通 SGD 的实际轨迹预测；它说明去掉归一化未必是清晰的“增加运动量”干预。采用具名的 0.02 固定范数使所改变量更可读，同时保留归一化方法本身不变。[C1P1 summary：曲线／展示点 update=175、raw_gradient_norm][c1]；[FLEX summary：update=0、175][flex]

也不选非零 FLEX 头初始化。这里要更正选项 4 的措辞：若只是改变初始化、仍允许两头末层取零，**函数类含括并不消失**；消失的是两臂初始化时的策略对应，且初始服务水平可能已经不同。这是另一个合法的结果知情 B，但它会再加入一个不必要的起点因素，不是本次最小改动。[宿主定义：FLEX-REKEY — strict-containing comparator][host]；[models.py：apply_affine_fixture_uniforms][models]

同一 0.0005／200 条件下再取一个独立种子仍是合法、可能有信息的选项。我本次不优先买它，是因为先前观察的绝对服务水平和指标饱和使更新量改动更直接，不是因为能证明重复必然相同。新步长的 seed 18 **不是原 B01 条件的重复**；B01 的训练种子不确定性保持未解。停车和完整五臂方案分别过早与过大；本轮均不选。[经验规范 §§11.8.2–11.8.3][spec]；[DM 提案：Options][options]

## 三、新对象的可写卡合同

### 方法、宿主与唯一学习法则改动

本对象的主张是：在冻结 TBCFV 及以下有限学习量下，观察持久公共计划包相对于含括 FLEX 包的成员变化后平均未服务需求差，并用同一初始策略的读数判断绝对服务性能是否有改善，以决定下一小笔独立重复是否值得。绑定的 MARL 结构是 **agent 数量变化后的协调恢复**，不是私有线索聚合或动作合法性。[方向记录：2026-09-01 recast][direction]；[宿主定义：Question and decision value][host]

保持 120 扇区、六信标、H=64、t_c=24、六个始终合法的 claim、原 MOVE-TO-CLAIM decoder、需求／成员／epoch 过程和时序。每次更新仍为 `6→6、10→10、6→10、10→6` 与两种 epoch 条件交叉的八格，各八个 episode。held-out 仍为 `8→8、12→12、8→12、12→8` 与两种条件交叉的八格。一个参数向量跨 roster 使用；不训练 8／12，不新增 N 专用头，不改变低层控制、信息、通信、事件顺序、损失或奖励。[宿主定义：Frozen physical host、Shared maximum learned architecture][host]

学习臂只有 C1P1-COMMON-PERSISTENT 与 FLEX-REKEY。两臂保留 26,161 标量的最大结构，同一个初始化张量及原来的 Xavier／零偏置法则；FLEX 两个末层仍准确从零开始且可训练，C1P1 硬屏蔽它们。旧 epoch 样本保持 stop-gradient，FLEX 确定性更新头保持原 actor 梯度路径，八个每格 baseline 独立且在联合参数更新后按 0.95／0.05 更新。没有 Adam、momentum、entropy、辅助 reward、回报归一化、warm start 或参数组专用学习率。[B01 卡 §§2–3][b01card]；[models.py：exact_advantage_loss、apply_registered_block_update、event_plan][models]

**唯一学习法则改动为：对完整参数向量，若原始梯度 g 非零，θ ← θ − 0.02·g/‖g‖₂；若 g=0，不更新。** 每个完整 64-episode block 仍恰好一次 backward 和一次联合更新调用；不把一个 block 拆成四十次优化步骤。两臂使用同一新法则，全向量归一化，而非只放大 FLEX 头。原 0.0005 法则保留为 B01 和定义卡的历史含义；新卡明确覆盖的只是本 B 的更新量。这不是修改全局配置后宣称 B01 原样重复。[config.py][config]；[models.py：registered_plain_sgd_step][models]

本对象的工作预测是：这个改动可能使至少一个包在同一评价面板上相对自身初始化的平均 U 降低约 0.05，令原本几乎无运动的观察变得更有区分力；包差异的方向仍未知。最强竞争预测是两臂仍几乎不改善，或更大的随机更新降低原生服务。二者都以真实 U／Y 读数判断，而不是以“参数动过”“头不为零”或是否首次出现 τ<40 代替服务结果。

### 种子法则、配对和检查点

**只取 seed 18，不续训或挑选 B01 的 seed 17。** 建议新卡固定 ASCII 标签 `RCLE-TBCFV-B02-NORM-0p02/seed/18` 的 SHA256 为主键，再按已有 `_derive_block_digest` 方案，以对象 identity `RCLE-TBCFV-B02-NORM-0p02`、block index 0 派生语义随机源。该式是拟采用的种子法则，本咨询没有计算 digest 或实例化 RNG。不得把新编号写成旧 B01 digest 的别名；B01 seed 17 仅作已见开发证据，不并入同配置重复统计。[CM 记录 §2：Authority seam and digest derivation][cm]；[B01 卡 §3][b01card]

两臂共享初始化、外生成员与物理随机量，以及原语义下可配对的 plan／actor draws；臂名不选择 RNG 子流。策略分歧后允许状态和动作自然分歧，不为制造差异而解耦随机数，也不为保持匹配而强迫相同动作。训练与评估沿原来的坐标域区分。新对象的最终面板与 B01 seed 17 面板不重用；在新面板内部，初始化、最终两臂及脚本参考按情景对齐。[B01 卡 §§2–4][b01card]；[CM 记录 §2][cm]

每臂固定从初始化训练到第 **200 次完成更新**。每次更新保留训练格的 Y、U、τ 等已有汇总，展示间隔为 25 次，但全部 200 个 block 保留。唯一用于包主比较的模型是第 200 次更新后的模型；不看中途评估选 25、100 或最佳 checkpoint，不早停寻找最好结果。

增加 **一次共享 update-0 评估**：在新面板八格各 256 个 episode，由 C1P1 初始化策略执行；FLEX 的初始化同分布由保留的零头对应给出，不冒称另行实测了第二份初始化面板。这个读数同时作为两臂的共同起点。随后两臂最终各八格×256，共 4,096 个最终评估 episode。共享起点不用于决定是否训练、不用于调步长或换 seed，也不是单独的“先过关”对象。它只解决“相对于本种子自己的起点是否改善”这一具体不确定性，避免把 seed 18 对 seed 17 的差误写成学习效果。[宿主定义：初始零头对应、Treatment-blind physical endpoints][host]；[经验规范 §§11.4、11.8.6][spec]

### 主测量、伴随量与 MEI

新主量为两条 ACTIVE_CONTINUATION 路径 `8→12`、`12→8` 的 **ΔU = 平均(U_FLEX − U_C1P1)**，两路径等权，每格内所有 256 个分配情景等权。正值有利于 C1P1，负值有利于 FLEX。分别报告两路径的两臂均值和差，不能只给一个总均值。U 仍严格是 t=24…63 的平均归一化未服务需求；没有改变 endpoint 的定义。[宿主定义：Treatment-blind physical endpoints][host]

主量的 MEI 为 **U 绝对 0.05**，即边界后 40 tick 中两个归一化未服务需求 tick；τ 的伴随 MEI 为 **4 个 physical tick**，一个 claim 周期、边界后窗口的 10%。沿用这两个服务尺度便于与 B01 阅读相接，而非从本轮结果挑出来；它们是 DM 可采用的投资兴趣尺度，不是功效保证、显著性线或启动门槛。[B01 卡 §5][b01card]；[经验规范 §11.7][spec]

τ 保持原定义：h=0…36 中第一个连续四 tick 未服务为零的偏移，不存在则记 40；同时报告 τ=40 的比例。40 编码下的均值不能解释成未删失的平均恢复时间。40U 是累计归一化未服务需求，不是原始 service-unit 总数。八格的 τ／U／Y 和现有 F 汇总完整保留，八格总均值为次要描述；NEW_EPOCH 不作为纯“抹掉计划身份”的因果对照。[宿主定义：Frozen physical host、Treatment-blind physical endpoints][host]

增加的伴随学习量是每臂 **G_U = 两活动路径平均(U_init − U_final)**，正值表示该评估面板上相对初始化减少了未服务需求；用同一 0.05 尺度解释，不另造合格阈值。Y 保留原生全 episode 回报及全部训练曲线，初始化和最终 learned 评估也保留 Y。即使 U 改善而 τ 仍几乎全 40，也只主张局部／累计服务改善，不声称更快完成完全恢复。

**把 U 列为本新 B 的主量，是观察 B01 后公开作出的测量选择。** 它不把 B01 的零差重新包装为 U 成功，不改 B01 卡，也不证明原方向中“更快恢复且无需求损害”的完整主张。未来若要就恢复时间作结论，还必须有对恢复时间本身有信息的观察。[经验规范 §§5.2、11.8.2、11.8.4][spec]

在 seed 内，以 cell 分层的配对情景差计算 Monte Carlo 标准误或描述性区间；现有 NumPy 均值、样本方差与配对差计算就够了。两路径均值之差的汇总按实际情景独立性处理；不把 tick、agent、checkpoint 或格子当作独立训练种子。单个配对训练种子不能估计训练种子总体方差；不以 episode bootstrap 或零 SE 声称稳定优越或等价。[CM 记录 §7：paired_difference_se][cm]；[经验规范 §11.8.3][spec]

### 参考与证据要求

INDEPENDENT-NEAREST 在 **新 seed 面板**上八格各 256 个 episode 评估一次，不训练、不搜索、不改规则。不能拿 B01 的不同情景参考冒充本轮配对参考。它提供可达到的简单服务水平，不是含括 FLEX 的充分调优证明、上参考或 headroom。脚本接口不返回 Y 时，沿用 null 和原因说明，不从 U 伪造全 episode Y。[reference summary：Y_note、configuration][reference]；[CM 记录 §2][cm]

完整比较至少要留下：两臂实际更新与 episode 计数；全训练曲线；初始化和最终参数身份及已有位移读数；最终每个分配情景的 τ／U／Y、格完成数及删失计数；初始化行、参考行的明确来源；所用更新量与选择历史；执行节点、源码 SHA、wall／RSS 的实际范围。没有好结果的情景不能删除。F 和资源量按自身依赖保留；不增加所有动作轨迹、全中间张量、参数组普查或逐位跨平台重放。[经验规范 §§4、9、11.8.6–11.8.8][spec]

## 四、完整工作、计费与最小工程范围

下表是**新设计的算术计数，不是已经发生的曝光**。训练量复用 B01 的有限规模；额外共享起点评估专门购买可解释的绝对学习变化，不增加候选模型选择。

| 新对象工作 | episode 数 | 环境 tick 数 |
| --- | ---: | ---: |
| 每臂 200×64 训练 | 12,800 | 819,200 |
| 每臂最终八格评估 | 2,048 | 131,072 |
| 两臂训练与最终评估合计 | 29,696 | 1,900,544 |
| 一次共享初始化面板 | 2,048 | 131,072 |
| 一次最近信标参考面板 | 2,048 | 131,072 |
| 本对象合计 | **33,792** | **2,162,688** |

共有两个真实训练实例、一个配对训练种子、至多 400 次 backward／联合更新调用；零梯度次数单列。初始化与最终评估不是新的训练重复。已有初始化 helper 会先分配五个包的模型再取两臂，这是 CM 记录的实际实现细节；实际分配与真正参与训练的实例应分别记录，不把三份临时模型记成三个训练种子，也不假称从未分配它们。本咨询则仍为零模型、零 native 状态、零交互、零 backward、零优化步骤、零测试和零实验。[CM 记录 §2][cm]；[B01 暴露与成本记录][cost]

主要算法工作是固定数目的真实 episode、每个 claim clock 对当前 agent 的六个 beacon 候选评分，以及每 64 个 episode 的图保留／反向传播和一次全向量更新。没有 `6^N` 联合动作枚举、轨迹树、beam search、控制器候选搜索或额外超参数网格。保持已有单进程／单 CPU 线程及现有批处理边界；native、批处理和节点名字中的 4070 本身不提供新的加速论证。验证新增工作仅是对新步长和相关输出的一次适度检查；它不扩大成前置科学阶梯。[宿主定义：Claim decisions、Shared maximum learned architecture][host]；[CM 记录 §§2、5][cm]；[运行规范 General requirements §§3–5][runtime]

已测成本要照原范围引用：B01 C1P1 约 62.0 s、FLEX 约 69.8 s，参考约 1.5 s，准备约 11 s，合计计费约 144.3 s；冷构建记录 5.09 s。**62／200 与 69.8／200 得到的约 0.31–0.35 s 不是单独分段测得的纯训练更新成本**，因为这些臂时长还包括最终评估等工作。DM 的“每检查点约 10 s 评估”没有单独计时支持，不能写成测量事实。更大更新数的线性外推是有假设的规划参考，不是已经跑过的成本律。[cost：measured、prospective options][cost]；[结果 intake：执行记录][intake]

本设计保留原来的训练规模、形状和 dtype，因此 B01 的两臂时长是最相关的成本参考；约 150 s 只能作为原相近规模的参考量级，不是新法则加起点评估后的已测整次 wall，也不是保证。新增起点评估、改动后的更新实际成本、检查与输出开销仍未独立测量，不能填零。本次不要求另做校准实验、CPU/GPU 对照、线程扫描或再跑一次“首次可执行性”。[运行规范 General requirements §§2–5、8][runtime]

**主动选定的新支出界限：每臂每种子的完整逻辑调用最多 600 s；本对象累计执行 wall 最多 1,500 s。** 共享初始化面板在 C1P1 调用内支付一次；总账还包括本对象实际支付的必要构建、一次聚焦检查、参考和归并发布，不能在两臂额度外免费追加。各子项不能同时用满后再加尾部工作；600 s 是本对象的保守硬界限，不是旧 2,700 s 阈值自动给予的新余额。采用这个界限是限制一次未测改动的风险，不是声称实际需要这些时间或已证明资源充分。编辑、Git／传输和代理推理不冒充实验执行 wall；未测的外部成本另述。[运行规范 General requirements §§1–2、7][runtime]

每臂计时覆盖 import、实际支付的编译／初始化、该臂全部训练、评估、必要检查和完整发布；共享项目按实际归属记一次。报告 study 的 elapsed critical path 与逻辑调用 wall 之和，不把历史计费和为 144.3 s 的记录自动当成全部端到端时间。原有 CPU 数据可保留，不因本次单线程科学问题再建设遥测服务。资源量缺失是否影响结论按实际依赖处理，不能把非主张所需的 RSS 缺失升级成算法失败。[运行规范 General requirements §§2、6][runtime]；[AGENTS §8：Telemetry rule][agents]

CM 的任务是最小适配既有真实 B 路径：在新对象作用域实现 0.02 的更新和相应配置／输出，保留原 0.0005 路径的可解释性；输出新 ΔU 及起点对照，复用宿主、批处理、回报、配对与发布计算。不调用完整五臂二十 block 入口，不以改全局常数、伪造旧 identity 或重用旧 summary 来省掉真实比较。所列证据中没有 B01 `study.py` 或 runner 的源码，因此本咨询关于这些入口的实现细节以 CM 记录为依据，没有声称逐行审计了未列代码。[CM 记录 §§2、5、7][cm]

只保留一次针对改变行为和主输出的聚焦检查：新全向量更新对非零／零梯度的处理；FLEX 更新头仍可从合法事件 actor 路径学习而 C1P1 仍屏蔽；既有真实 reward／τ／U 语义不变；新 ΔU、共享起点来源、计数和最终输出可读。复用已有 oracle 和包检查，不能因新的 launch 边界再加一套首次构建／全 smoke／历史复现。原始 `parameter_delta_norm` 不能仍打印 0.0005 伪装成新量；也不要求为此新增全参数遥测框架。[models.py][models]；[工程范围 §§3–5][engineering]；[经验规范 §11.8.6][spec]

普通工程界限保持：新增非测试源码至多 2,000 行、runner 至多 600 行、研究目录测试总 wall 按原五分钟界限；30% 编排比例是审查提示，不是新门槛。无新 registry、validator、guard、worker pool、重试／恢复服务或额外 profiling 框架。已有 Linux native 路径的成功记录可复用；若本次实际不得不重建，只计真实支付的一次构建，不重新包装成科学对象。[工程范围 §§4–5][engineering]；[CM 记录][cm]；[结果 intake][intake]

## 五、停止、结果分支和下一步改变什么

启动只保留 §11.4 的四类条件：共同完整性、真实 learner 的非零交互／更新／评估要求、资源准入，以及机器生成的曝光说明。新曝光说明应写清：200 次×0.02 的路径上界为 **4**，初始化尺度参考 B01 的约 21.186、实际新初始化范数在被计费调用中记录；上界不是实际位移、更不是运动合格线。不能要求 U 先下降、τ 先离开 40、FLEX 头先达到某个范数或补齐 headroom 才启动。[经验规范 §11.4][spec]；[C1P1 summary：initial_parameter_norm][c1]

结果性执行在 wsl_4070 从确切已提交、已推送的源代码、既有 detached supervision 路径开始；每次调用在执行节点临近启动重新取得 physical 和 effective available memory 均至少 4 GiB 的准入，不能复用上一臂的 receipt。保留单 CPU 线程、既有 float64 和 RNG／批处理语义，不默许 GPU、低精度、并行或换节点。准入失败、现有依赖不能执行、所需实现超过普通预算时返回具体工程缺口；不创造重试预算。[AGENTS §§5、7–8][agents]；[运行规范 General requirements §§4–7][runtime]

学习一旦开始，不按结果早停或更换配置。C1P1 服务很差不阻止 FLEX 进行完整比较；初始面板的好坏也不改变 200 次更新。只有完整逻辑调用达到 600 s／整对象达到 1,500 s、具体的非有限数值、错误 reward／信息／事件语义、实际学习链或必需输出损坏等技术问题才终止相关尝试。中途停止如实报告完成数，不能把截断调用重命名为完成的 200 次对象，也不换 seed、步长或自动续跑。若第一臂已损坏到无法形成本次配对，不再自动花第二臂额度；若第二臂损坏，保留第一臂的独立可信事实。[经验规范 §§4、11.8.7][spec]

仅共享起点评估缺失时，不能主张 G_U，但在最终两臂及其曝光仍完整可信的条件下，ΔU 的比较意义可以保留；仅脚本参考缺失时不补跑，也不抹去有效包比较。上述依赖降级不等于完整卡已经全部完成。实际发生 NaN 是需要修复的数值／执行问题；数值有限但服务恶化则是可解释的不利学习结果，不能以“优化失败”为名丢掉。

| 观察 | 这次改变的判断与建议 | 主张边界 |
| --- | --- | --- |
| ΔU 约 +0.05 或更大，且无达到 τ 的 4-tick 兴趣尺度的反向变化 | 得到此新学习器下持久包的初步累计服务信号；优先考虑一次同配置的新独立配对种子，保留逐路径交易 | 若 τ 仍全 40，只是累计服务信号；不称恢复时间优越、非劣证明、机制归因或稳定优势 |
| ΔU 约 −0.05 或更小，或存在实质的相反服务／恢复交易 | 降低对该预算下限制 FLEX 的支持；可信的反向结果也可值得独立重复 | 不关闭 RCLE，不把新步长下单种子结果外推至所有持久状态／预算 |
| 包差在 MEI 内，但至少一臂 G_U 有约 0.05 的改善 | 说明现在可观察原生服务学习，但尚无 material 包差；可据曲线与成本考虑同配置重复 | 不称两包等价，不把“学会了一些”升级为优于通用基线或完全恢复 |
| 包差在 MEI 内，两臂相对起点也几乎不改善，τ 仍饱和 | 此次 0.02／200 的运动量尝试未给出有用学习信号；结束本次支出，带完整反例返回下一对象选择 | 不自动做 4,000 次、扫描步长或热启动头；不证明归一化原则错误或宿主不可学 |
| 两路径方向不同、U 与 τ 冲突、评估误差跨越兴趣尺度 | 报混合／未决，保留平均与全部细目；不择优路径、指标或 checkpoint | 局部事实不消失，但不能给单一优越结论 |
| 主比较所依赖的执行或读数损坏 | 报直接异常、退出、缺量与计数，只保留独立可信的窄事实 | 无算法极性，无自动补臂、重试或种子替换 |

这些是新 B 的解释叙事和投资建议，不是 C 的冻结显著性规则。种子内区间先不显著、没有正结果或不能唯一定位机制，均不自动禁止一个有理由的后续 B；同样，任何有利点估计都不自动授予无限计算。以后若继续学习性能问题，优先一个或两个新的独立训练种子，全部结果保留；**这些后续种子不在本次一对的额度中**，本轮没有同时开启第二个对象。[经验规范 §§11.7、11.8.2–11.8.4][spec]

本选择的直接反证是：在新规定的有限预算中，FLEX 服务同样好或更好，或 C1P1 的某个恢复收益伴随实质 U 损害。对“更大更新可使本次观察脱离近起点性能”的工作预测，两臂相对共同初始化仍无 material 原生服务改善就是反证；它只限制这个量级和预算，不是全方法的否证。最终上限始终是**一个新种子、新步长、固定 toy 与所列情景上的探索信号或反例**；既不证明原步长是唯一原因，也不建立 commonality／persistence 的单因素贡献、headroom、稳定优越、任意 roster 泛化或部署结论。

## 六、实际访问与未做事项

本答复通过连接的 GitHub 工具读取任务固定版本 `8c0367eab44db96e23853b17ad6d57b0ee34d7af`；下列文件链接全部使用任务指定的证据版本 `ad9f8635d245a2fa31bf7c2868939dcfa27a22dd`。没有改用默认分支、web 镜像、本地 clone、其他文件或外部论文补充证据。以下是实际读到的范围，而不是整仓库或所有数组审计：[固定任务][task]

| 已访问的列定文件 | 实际用途与读取范围 |
| --- | --- |
| [RCLE_TBCFV_B01_RESULT_INTAKE_20260906.md][intake] | 已读结果 intake 的执行、读数、解释与后继选择内容 |
| [b01_tbcfv_20260906/c1p1/summary.json][c1]、[flex/summary.json][flex] | 配置、格均值、计数、部分曲线／展示点、参数位移和 native 字段；FLEX 配对主量；部分情景行；未独立遍历比较全部 200 曲线及 2,048 行 |
| [b01_tbcfv_20260906/reference/summary.json][reference]、[executability/summary.json][executability] | 参考各格及总汇总、脚本 Y 缺失说明；八批准备、episode 数与 native 身份；未重放其情景 |
| [RCLE_TBCFV_B01_PERSIST_VS_FLEX_SCIENCE_CARD_20260906.md][b01card] | 问题、算法、种子、主量、分支、预算及工程边界；一次连接中断后同版本重读成功 |
| [RCLE_TBCFV_B01_CM_RECORD_20260906.md][cm] | authority seam、既有 API 行为、POSIX、局部测试、命令和 review 修订；未执行命令、未取未列实现文件 |
| [RCLE_TBCFV_FIRST_B_INNOVATOR_INTAKE_20260906.md][firstintake]、[前一完整答复][previous] | 前一决定、匹配／测量／停止的相关段落；保持其旧结果规则，不重新形成旧决定 |
| [EVIDENCE_AND_OPTIONS.md][options]、[EXPOSURE_AND_COST.json][cost] | 五个候选、已测结果／成本及投影内容；机械派生和 proposal 不冒充新实验 |
| [ISSUE_SNAPSHOT.json][snapshot] | 包制作时的 Issue 正文和旧交付评论快照，read_at=2026-09-06T21:18:12Z |
| [models.py][models]、[config.py][config] | 初始化、FLEX 图、loss、全向量归一化更新、baseline 顺序和常数的静态源码 |
| [RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md][host] | 物理宿主、端点、架构、两包及含括、训练律相关段落；未审计完整 C 的所有推断尾部 |
| [DIRECTION.md][direction]、[RESEARCH_MAP.md][map] | 方向 recast、首 B 选定记录和 RCLE 当前代码映射；没有访问未列 Portfolio 文件 |
| [MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | 分类、完整性、B 及 §§11.1、11.4、11.7–11.9 |
| [ENGINEERING_SCOPE_SPEC.md][engineering]、[MARL_RUNTIME_ENGINEERING_SPEC.md][runtime]、[AGENTS.md][agents] | 普通工程／测试预算、完整调用核算、决定层级、远程与资源／诚信相关章节；未把其他对象附款当本次额度 |
| [GITHUB_RESEARCH_COLLABORATION.md][delivery] | 原有响应文件和评论交付边界；不扩展本轮写入范围 |

Issue 8 的正文及评论也经 connector 实际访问；写作前的评论复核时间约为 **2026-09-06 14:33 PDT（21:33 UTC）**。当时只返回首个 B 的旧评论 [5560789984][oldcomment]，不是本 post-B01 轮的交付。Issue 正文仍是首 B 前的状态，不能用其中“从未运行”覆盖固定 B01 结果；定义卡的 definition_only 也只是该卡的属性，不否定另有 B01 卡授权的已记录执行。[Issue 8][issue]；[快照][snapshot]；[结果 intake][intake]

本轮对所列证据不存在未解决的访问缺口；大文件的选择性阅读已如实限定。没有读取未列的 A1 原始普查、训练参数文件、原始节点日志或 B01 study／runner 源码；这些事项仅在列定材料已经转述的程度使用。没有 native 构建、模型载入、代码执行、测试、计时、梯度检查或实验复现。科研零新增曝光与本次只交付研究答复的范围保持不变。

[intake]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_RESULT_INTAKE_20260906.md
[c1]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/b01_tbcfv_20260906/c1p1/summary.json
[flex]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/b01_tbcfv_20260906/flex/summary.json
[reference]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/b01_tbcfv_20260906/reference/summary.json
[executability]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/b01_tbcfv_20260906/executability/summary.json
[b01card]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_PERSIST_VS_FLEX_SCIENCE_CARD_20260906.md
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_CM_RECORD_20260906.md
[firstintake]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_FIRST_B_INNOVATOR_INTAKE_20260906.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_tbcfv_first_b_innovator_r02/archive/RESPONSE.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b01_innovator/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b01_innovator/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b01_innovator/ISSUE_SNAPSHOT.json
[models]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/experiments/candidates/roster_consistent_latent_exploration_tbcfv/models.py
[config]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/experiments/candidates/roster_consistent_latent_exploration_tbcfv/config.py
[host]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/candidates/roster_consistent_latent_exploration/DIRECTION.md
[map]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/RESEARCH_MAP.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/AGENTS.md
[delivery]: https://github.com/CartmanFatass/My-paper-code/blob/ad9f8635d245a2fa31bf7c2868939dcfa27a22dd/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/8c0367eab44db96e23853b17ad6d57b0ee34d7af/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b01_innovator/TASK.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/8
[oldcomment]: https://github.com/CartmanFatass/My-paper-code/issues/8#issuecomment-5560789984
