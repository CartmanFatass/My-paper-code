**方向层决定：继续现有首次合法应用时的 RETAIN/COPY/SHADOW 探索议程，联合预测包支线保持结束；本轮只选择选项 2——同一 CONTROL／LOW_LR 比较的第二个独立配对训练种子 101，仍为 B/EXPLORE。** 两臂各十六次更新，只评估 update 16，并在同一对象内保留这个新种子的四行零更新 raw-interface 参考。不重训 seed 89 来寻找损失发生时刻，不增加中间检查点评估，不同时冻结 Welford、修改 epoch、改变学习率或购买来源触发试验；不作 PARK、CLOSE 或 RECAST 整个 DISH。

理由不是“第二个种子是固定手续”，而是 B04 已经给出一个真实、完整、处理确实生效的原生平均差分 **+182.75 tick**，同时揭示它高度集中于一个条件、LOW_LR 仍低于自身初始化 **57 tick**、伴随事件和能量也并非全无代价。现在最能改变是否继续这项学习率比较的观察，是相同比较在一个新随机实例上的完整结果，而不是同一实例多次检查点的时间位置。后者可以描述何时发生损失，却不能仅凭“早发”就定位 Welford，也不能回答现有学习率差分是否在另一训练实例上仍有决策价值。[B04 配对原始量][paired]；[原卡 §§1、4–5][card]；[证据规范 §§11.8.2–11.8.3、11.9][method]。

这是在阅读 B04 全部结果后作出的**单项有限跟进选择**，不是宣告 B04 全条件获胜、恢复了初始化能力、已经稳定，或按旧卡自动获得更多额度。以下保留原读法记录，指出其叙述中的具体冲突，并给出这项跟进可直接写卡的边界。选择不等于源码接受、实验启动或 Portfolio 动作。

## 一、B04 的原始比较、终止和初末损失必须同时保留

### 完整四行而不是一个均值

| 开发条件，均为 speed 4 / slot 0 / block 0 | 零更新 raw 参考 | CONTROL | LOW_LR | LOW_LR−CONTROL | CONTROL−参考 | LOW_LR−参考 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 617 | 92 | 760 | +668 | −525 | +143 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 312 | 151 | 150 | −1 | −161 | −162 |
| TERRAIN_RELAY_MASK / K8 | 279 | 148 | 275 | +127 | −131 | −4 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 367 | 225 | 162 | −63 | −142 | −205 |
| **均值** | **393.75** | **154.0** | **336.75** | **+182.75** | **−239.75** | **−57.0** |

这些数来自完整的 `paired.json`，并与三个原始 summary 的逐行服务一致。LOW_LR 的平均相对改善和平均绝对损失可以同时成立；不能把前者说成已恢复初始化，也不能用后者抹去前者。它们是一个配对训练根的结果，不是四个独立训练种子。[paired：rows、三个均值与差分][paired]；[CONTROL evaluation_rows][control]；[LOW_LR evaluation_rows][low]；[shared reference_rows][shared]。

CONTROL 的 TARGET/K8 行在 native tick **684** 因 `separation_below_15` 终止，间距 **13.982364428191739**，已发生服务 92 tick；剩余 **516 tick** 依原来的固定 1,200-tick 定义计零。该行是**有效的原生终止结果**，不是缺失回报、测量异常或应删除的离群点。不能让 LOW_LR 也截到 684、把 CONTROL 除以存活 tick、换一个 reset，或去掉这一行再替代原主量。这里需要说“提前终止”，而不是声称旧对象从未出现过 native terminal：固定范围末端本来就记录 terminal，B03 包臂还曾在末端记录分离越界。[CONTROL evaluation_rows[0].terminal、unstepped_zero_service_ticks][control]；[B04 原卡 §4][card]；[B03 结果 intake §2][b03]。

平均值的集中性确实很强。直接由已发表四行作算术分解：第一行对四行均值贡献 `668/4 = 167`，其余三行合计贡献 `63/4 = 15.75`。这只是描述主量由哪些行构成，**不是选择删行后的新主量**。该事实既反对把这一次增量推广为普遍优势，也使独立配对观察更有价值。没有共同前缀的服务／动作分解，不能进一步把 +668 全部归因于终止，或把终止与此前运动、控制器状态造成的差异分离。

### 伴随结果不等于“LOW_LR 无害”

八个最终评估 episode 中，CONTROL 提前终止一行，其余七行完成 1,200 tick；另有四个完整零更新参考，因此本对象共 **12** 个 episode，不是“其余十一条学习行加四条参考”。实际最终评估 tick 为 **9,084**，参考为 **4,800**；共 **13,884** 个实际 tick，固定服务范围合计 14,400。原始记录同时支持完整结果和少于最大值的实际曝光。[两个 summary：actual_exposure、evaluation_rows][control][low]；[shared：evaluation_ticks、reference_rows][shared]。

CONTROL 四行 `invalid_commit` 为 **26／64／89／50**，LOW_LR 为 **23／4／0／11**；LOW_LR 最终评估没有分离越界，但仍有无效提交。零更新参考也不是无事件基准：其 `invalid_commit` 为 **0／42／38／0**。训练期两臂则各有 **2 次 separation_breach**，无效提交分别为 **3,251、2,234**，不能把“LOW_LR 评估没有分离越界”扩大成训练和评估全程安全。[三个 summary 的 hard_events 与 training_hard_events][control][low][shared]。

能量也须按真实暴露解释。CONTROL 提前终止行的能量约 **165,050**，不能与 LOW_LR 完整行的约 **289,152** 当成等时长效率比较；在另外三个双臂都完整的条件上，LOW_LR 的能量也都略高于 CONTROL，且四行均高于各自零更新参考。尤其两个 K4_TO_K12 行，在没有服务增益或已有服务损失时还保留较高能量。因而“没有使平均信号失去继续考察价值的伴随权衡”不等于“伴随代价不存在”。本轮既不以能量抹去原生服务主量，也不引入新能量权重掩盖这些代价。[三个 summary：energy][control][low][shared]。

### 真实处理和真实学习，而非仅修改配置标签

两臂都完成 **65,536 普通训练转移、16 更新、512 optimizer steps**。每次更新后从 trainer checkpoint 读出的两个参数组学习率，均分别为 `[3e-4,3e-4]` 和 `[3e-5,3e-5]`。原卡／CM 所记录的实现机制是：初始化 payload 改写 optimizer 参数组，随后 engine 每次构造 optimizer 再恢复 checkpoint 状态。这与运行时读回一致；它比仅在 `configuration` 写一个学习率更强，但不是本次咨询重新执行了 engine。[原卡 §§2、7][card]；[CM record“Learning-rate mechanism”][cm]；[两个 summary：curves[].learning_rates][control][low]。

初始范数为 **38.26126788822669**；参数 L2 位移为 **8.621537324105303** 与 **1.9122897033986779**，相对位移约 **0.22533、0.04998**。没有十倍位移关系的承诺，也没有“仅 actor 步长”的解释：AdamW 学习率同时作用于其原有参数衰减规则。训练服务和为 **30,846、26,412**，与最终评估优势排序不同。所有记录的损失／梯度均有限，不能用训练代理量重判原生结果。[parameter_movement、training_service、curves][control][low]；[原卡 §1][card]。

DM 的“LOW_LR 前十次更新梯度都更大”不是逐条成立：update 2 的记录是 CONTROL **516.1601155400276**、LOW_LR **148.24947547912598**。可以说多数这些更新的记录值较大，不能写成全部；这些还是按更新汇总的梯度统计，不是实际参数步长或损失原因。[两个 summary：curves，update 2][control][low]。

## 二、混合行读法的边界，以及为什么不是先买诊断

### 保留旧记录，区分平均信号与普遍优势

B04 卡片 §5 确实把“主量带内，**或行符号混合**”写进了第 4 行，DM 已同时应用第 2、4、6 行；这个历史适用记录保留。本轮不把它改写为 B04 已按旧规则自动晋级。另一方面，前次完整答复 §四原句是“主差分带内，或行间混合**而没有清楚的有用平均增量**”；这个后半限定在卡片和 intake 的转述中丢失了。原卡自己的表前段又明确“不要求每行或每个种子同号”。这是一个具体叙述冲突，不能不说明就把它当成新的科学必要条件。[前次完整答复 §四][prior]；[原卡 §5][card]；[post-witness intake §2][prior-intake]。

准确的并存叙述是：**B04 在预先定义、四行全部保留的等权平均上测得 +182.75；它同时具有明显行间异质性、LOW_LR 平均仍低于初始化和伴随代价，未建立稳定或逐条件普遍优势。** “没有证明跨条件普遍优势”不等于“这个有限面板的平均差分不存在”。当前规范 §§11.8.2–11.8.3 也明确不以全部单元格／种子为正作为有限跟进的前提。因此本轮独立选择第二个配对种子，不用删掉旧卡或重判旧实验来获得授权，也不延续一个与现行规范冲突的同号门槛。[paired][paired]；[证据规范 §§11.7–11.9][method]。

DM 对“带内或混合”的预测有混合符号这一部分命中，但 **+182.75 并非带内**；不能把宽的“或”式命中称为预测到了平均效应大小。LOW_LR 初末变化带内的竞争预测则没有命中。预测记录不决定新观察是否有效。[B04 结果 intake][intake]；[原卡 §5][card]。

### 最强支持、最强矛盾和仍存的解释

**最强支持**是一个真实学习器、真实处理、完整原生终局下的正平均比较，且不是来自调换 checkpoint 或过滤失败行。**最强矛盾**是其集中性、另两行非正、LOW_LR 仍有 −57 的初末损失，以及所有评估仍无合法换主；这不足以推荐通用低学习率，更不足以称为来源机制进步。现有差分可能是种子／条件特定的运动与终止差异；归一化、参数、循环动力学、辅助目标及训练数据变化仍共同参与，均未被定位。

CONTROL 在 seed 73、89 上分别有 **−245.75、−239.75** 的完整控制器初末损失，确实是两个不同随机实例的相似描述；它们不是同一检查点的重复测量。不过种子同时改变初始化、训练随机和评估 reset 的派生值，706.25 与 393.75 的初始水平差异不能独归于权重。两例也没有证明损失何时发生、一定由 Welford 导致，或一般学习有害。[seed-73 见证 intake §§2–3][witness]；[B04 shared 与 paired][shared][paired]。

原始记录没有早期完整评估：训练窗口的服务、loss 和 parameter displacement 不能补出 update 1／2／4／8 的完整 episode 回报。即便新测时间曲线显示损失早发，参数与统计状态在早期也同时变化；“早发→Welford/raw 接口原因、晚发→参数累积原因”仍不是被识别的二择一因果结论。此限制不阻止性能 B，只限制诊断叙事。[DM options“Unknowns”“option 1”][options]；[两个 summary 的 curves 与 evaluation_selection][control][low]。

## 三、唯一下一对象：同一学习率比较的第二个独立配对种子

### 类别、问题与保护边界

**B/EXPLORE，B04 学习率比较的 seed-101 独立配对跟进**，单独写跟进卡、记录新输出，不覆盖 seed 89。问题是：同一十六更新预算下，3e-5 对 3e-4 的完整原生服务增量在一个新的随机实例上是什么；它与各自共同零更新参考的关系是什么；先前集中于一个终止条件的结果是否仍有继续开发价值？这不是稳定优势、罕见事故率、校准或来源效果的最终结论。

| 项目 | CONTROL | LOW_LR |
| --- | --- | --- |
| 方法 | 继承 STRUCTURED CONTROL | 同一方法 |
| AdamW 学习率 | 所有原参数组恒定 3e-4 | 所有原参数组恒定 3e-5 |
| 目标／服务接口 | 原 mean-MSE、BCE-with-logits、PPO、link／missingness 辅助目标；raw logits | 相同，forecast_package=False |
| 归一化、采样与约束 | 原 Welford 更新、recurrent replay、clipping、mask、采样、终止和合法性规则 | 相同法则，状态独立演化 |
| 训练 | 16 更新，32 lane ×128 tick，4 epoch ×8 minibatch | 相同 |
| 检查点选择 | 仅 update 16 | 仅 update 16 |

其余 optimizer 参数、weight-decay 系数、奖励、信息、动作空间和标签预算不变；不补偿学习率改变的 decay 效应。不重新启用 Gaussian NLL／sigmoid 包，不冻结 Welford，也不加入新 clipping 或学习率衰减表。CONTROL 是已有执行证据、同信息同曝光的直接学习对照；零更新参考提供绝对比较。它们不是 tuned oracle 或最佳同信息基线，也不需要先搜索一个上界才能做这一对。[原卡 §§1–4][card]；[规范 §§5.2、11.7–11.9][method]。

### 种子、实际输入和共享参考

**唯一新配对种子取 101**，不重用 89、73 或 61。保持同一比较族的随机生成法，master 为 SHA256 对 ASCII `DISH-CONTROL-LOW-LR-B04/seed/101` 的输出；这项种子绑定在本答复中先于结果指定，本次未生成 master 或执行初始化。跟进的卡／输出可以有独立名称，但不能悄悄把换名当成另一次未记载的 RNG 选择。两臂与零更新参考使用同一份新 master-addressed STRUCTURED 初始参数和空 Welford 状态；其后 native、optimizer、循环和 Welford 状态各自演化。[原卡 §3 的法则][card]。

为 seed 101 按继承 `_reset_row` 坐标法则派生并记录四个完整 reset，三种控制器使用各行相同 reset／外生随机。**不把 seed 89 的相位 6／0／6／0、原回报 393.75，或 seed 73 的 706.25 搬到新种子。** 最小实际输入是新种子及现有初始化／reset／学习／评估路径；旧最终检查点不需要加载，历史全轨迹不需要重建。若薄入口当前写死 89，只在所选跟进实现中显式绑定 101 并核对其传播，不能把 CLI 标签变化误当实际随机源变化。本清单没有该入口源码，本答复没有独立证明其已能无需修改接受新种子。[CM record 的 master、初始化与复用路径][cm]；[shared：reference_rows[].reset][shared]。

同一新初始化经原 raw 接口评估一次四行，形成 `J_0,101,r`。count-0 Welford 和每行新鲜循环状态保留，评估不拟合统计量；它是普通零更新控制器，不是 held-only。学习率不在无 optimizer.step 的推理中产生第二种接口，故只有一个四行初始参考。参考是**这项 B 内的伴随测量**，不是先行 A 或高回报启动门：不能据其好坏跳过训练、选另一个 seed 或改条件。保存本次初始状态只为明确输入，不建立新的 resume／registry 体系。

### 宿主、评估和 MARL 后果路径

保持 **GROUND-TERMINAL-LINEAR-CLEARANCE-A03**、修正普通续约边界、native float64、policy FP32、原单线程配置。仍是两个物理 UAV、当前 owner／standby 与 active／shadow 循环副本，不能把角色身份和实体身份混用。维持原训练分布，不把四个开发条件改造成训练分布。

路径是：路线／退化事件 → 各实体的因果局部观测与实际消息 → active／shadow 循环表示 → 当前许可下的运动、prepare／commit 与预测输出 → 原生投影、证书／所有权处理和服务 → 普通 transition 与原辅助标签 → recurrent PPO／AdamW 更新 → update-16 控制器的完整原生后果。双方匹配标签**法则**而不是强制匹配实际 eligible 数或轨迹。私有标签克隆的强制 promotion 只是监督标签生成，不能计为普通合法换主，未来标签信息不得进入 actor。[原卡 §§2–4、6][card]；[前次答复 §三][prior]。

最终四个条件不变：TARGET_VISUAL_MASK／TERRAIN_RELAY_MASK × K8／K4_TO_K12，speed 4、slot 0、block 0。每次由本种子对应 reset、新鲜 native／循环状态开始，普通确定性评估，固定范围 1,200 tick。**终止行的处理完全不变**：native 终止就停止 stepping，剩余范围计零，实际 tick／原因／事件并列；不除以存活时长，不删除坏行，不匹配到较短生存时间，也不遇到 first-valid 就停止。若出现合法换主继续普通评估，但不由此声称已经做过 RETAIN/COPY/SHADOW 来源 fork。

## 四、主量、伴随读法和一次跟进的结束条件

新配对主量为：

`Delta_101 = (1/4) Σ_r [J_LOW_LR,16,101,r − J_CONTROL,16,101,r]`。

同时给出 `D_CONTROL,101`、`D_LOW_LR,101`，分别用自己的新共同零更新行相减。所有十二个新行、三个均值、逐行配对差分与初末差分都保留。**MEI 仍取 +24 平均服务 tick**，初末描述用 ±24；这是同一 1,200-tick 量纲上的 0.02，用于保持可比的有用变化尺度，不是数值容差、逐行门槛、显著性结论或启动条件。

完成后把 **seed 89 的 182.75 与新 `Delta_101` 分开列出**。可附等权两种子平均 `(182.75 + Delta_101)/2` 作描述，但不能只给它而藏起冲突，也不能让一行大值、一个最佳 seed 或最佳 checkpoint 替代完整记录。两对是两个训练随机实例，四行是共享一个训练过程的条件；不以逐行 bootstrap 构造训练种子总体区间。这仍是两个随机实例上的有限探索，动机来自旧结果，不是独立的论文级确认；B03 的包对照不能充作第三个学习率配对。

| 新观察 | 当前允许的读法及改变的后续建议 |
| --- | --- |
| `Delta_101 ≥ +24`，且服务／事件／能量的整体权衡仍值得开发 | 又一个实例出现有用平均增量；结合两对完整行考虑是否继续把 LOW_LR 作为开发候选。混合行本身不取消平均信号；不据两次结果宣布稳定、逐条件普遍优势或安全。 |
| 上述相对信号同时伴随 `D_LOW_LR,101 ≤ −24` | 仍只是对 CONTROL 的损失减轻，不叫初始化能力恢复；未来投资须直面零更新参考仍更好这一事实。 |
| LOW_LR 初末差带内或 ≥+24 | 分别报告本例接近初始服务、或同时有正的初末变化；带内不是等价，正值也不是一般稳定学习。 |
| `Delta_101` 带内、明显负向，或收益伴随严重原生不利权衡 | 限定先前信号的可重复性／可用性，不自动买第三个 seed、再降学习率或延长训练。与 seed 89 并列，不否认旧 +182.75，也不为保住它删终止或坏行。继续、停止这项具体配置或提出另一具名问题，须依据这时的完整结果另作决定。 |
| 新 CONTROL 不再低于初始化，或分离终止未重现 | 旧初末损失／终止没有在这个新实例按同样方式重复；不推翻原记录，不据一次未发生估计事故率为零。学习率配对仍可独立读出。 |
| 仍无最终评估合法换主 | 完整服务比较保持 incumbent-only，来源差分仍未估计；不是来源无价值或整个宿主不可能换主的证明。 |
| 输入、训练或主测量未完成／受损 | 保留真实曝光和独立可信行，不填造完整配对或回报；按依赖报告具体缺口，不连带隔离 B04／B03。 |

这项跟进不要求复现 +668／−1／+127／−63 的每个符号，也不要求两种子都为正。伴随报告沿用现有字段：每行能量、七类 hard events、实际／未执行 tick、终止原因、普通合法换主及服务的换主前后时间分解；没有 packet 来源核对时不把时间上的“换主后”写成新 owner 所传服务。训练曲线、LR 参数组读回、有限性、参数位移、eligible／next-mask、训练事件与训练换主另列。参考行的坏行为也保留，不能把初始化默认称为安全或最优。

**本轮只购买这个新配对实例。** 两臂各十六更新、四个参考和八个最终 episode（或其合法提前终止）及完整发布结束即停止。预算耗尽、实际非有限训练状态或威胁主测量的失败时保留已发生结果并停止；有限大梯度本身不被改写成非有限故障。没有根据效果提前挑 checkpoint、更换 seed／reset、补跑坏行、自动续训或另一个学习率。原生分离终止是结果，不触发科学重试。技术失败不产生新预算或科学极性。

## 五、完整工作与支出：以实测作参照，不把参照当保证

| 项目 | 唯一所选跟进的工作 |
| --- | --- |
| 独立训练重复 | 一个新的配对 seed 101；两个 learner run，不是两个独立 seed |
| 普通训练 | 每臂 16×32×128 = 65,536 transitions；合计 131,072 |
| 学习工作 | 每臂 16×4×8 = 512 optimizer steps；合计 1,024，保留全部 recurrent replay／backward |
| 新零更新参考 | 一个 raw-interface 视图，四个 episode，至多 4,800 native tick；零学习／标签调用 |
| 最终评估 | 两臂各四行，至多 9,600 tick；加参考合计十二个 episode、至多 14,400 tick |
| 检查点、搜索与历史重做 | 只用 update 16；无中间 checkpoint、参数网格、策略搜索、旧种子重训或来源分叉 |

原标签算法的每臂工作仍是 `2N + 2E + H`，`N=65,536`，`0≤H≤20E`；在 `E≤N` 下，原生训练 step 调用上界为 **1,572,864／臂**，不是只有 N 次。普通 N 步、N 次 next-label、2E delay 和 H consequence 都保留。训练前向、critic、PPO replay、backward、optimizer、构建／加载、检查和发布另属于完整计算链，不能由这个 step 数省略。[原卡 §6][card]。

B04 原实际 E 为 **22,044／15,616**，相应训练调用界为 **175,160–616,040／162,304–474,624**；H 的确切值未测。新种子不能沿用这些 E 作实际值。保留已有 E 记录与 H 的诚实未测上界，无须为当前性能主张增加 native ABI 或完整轨迹。[两个 summary：actual_exposure][control][low]。

**本对象重新选择每臂完整收费 1,800 秒、合计 3,600 秒的上限，不继承旧对象余额。** 一次真正共享的工作 S——必要聚焦检查、共同初始化、四行参考、实际构建／加载和共享归约／发布——只收费一次，事前各分配 S/2。每臂自己的完整调用加份额不超过 1,800 秒，合计包括 S 不超过 3,600 秒；给最终输出留在额度内，不另加 120 秒参考额度或“构建不计时”。分阶段、分脚本不重置 cap。[原卡 §6][card]；[runtime General requirements §§1–3][runtime]。

B04 已有相同比较类型与相同规模的完整链，**432.40 秒是有用的条件性规划参照**：S=15.84，CONTROL 外层 wall=210.07，LOW_LR=206.49；按原共享分摊算，两臂收费分别为 217.99、214.41 秒。它比早先 CONTROL／FORECAST_PACKAGE 对的计时更贴近本次所选工作，因此不拒绝利用它规划；但新种子会改变 eligible 标签、轨迹终止和计算量，缓存与节点负载也可能不同，不能把未来精确完成时间设为 432.40 或承诺固定倍率。当前可以据此按数百秒量级准备，而实际成本与完成情况仍待观察，不另购校准实验。[cost.measured][cost]。

prepublication wall（约 209.785／206.156）不是完整外层 wall。共享 summary 的 **6.5486 秒**包含该共享程序的初始化、参考和输出等，不是四个 episode 的独立单位价格；不能直接据其除四为额外 checkpoint 的确定成本。已有 CPU 与 RSS 都各有范围，单个 shared 程序 CPU 不含整套共享检查；不把可见局部 CPU 之和冒充完整链核算，也不把 self／child 峰值相加成同时内存。缺少非主张必需的资源量仍写未测，不否定独立可信原生结果。[shared 的 resource_scope][shared]；[两个 summary 的资源字段][control][low]；[runtime §§2、6–8][runtime]。

后续执行沿用 `wsl_4070`、精确提交且已推送的源码、现有 detached supervision、单线程 FP32／float64 路径；每个实际调用在执行节点新鲜测得 physical 与 effective available memory 均至少 4 GiB。普通 2,000 新非测试行、600 runner 行及现行测试预算保留，30% 编排比例仍只是审查信号。这里不新建 scheduler、registry、validator、额外 guard 或 profiler，不用 2,700 秒调查阈值扩大较严格 cap，也不把未测成本改成必做的额外校准试验。[AGENTS §§5、7–8][agents]；[scope §§3–5][scope]；[runtime §§1、8][runtime]。

### 每项保留负担服务的当前决定

普通交互、标签和 PPO 工作定义所比较的真实学习器；最终八行测第二个配对实例的性能；初始四行防止把较小损失叫恢复；LR 读回与实际位移证明处理和学习发生；事件、终止与能量限制收益解释。检查只保护新种子／master 的实际绑定、两臂共同初始与各行 reset、结果来源和既有主归约。若薄入口有相应变化，用一次针对改动和主输出的聚焦覆盖；LR 跨更新持久性、修正边界、reference 和 native 终止已有可信覆盖就复用，不因新一次启动重跑全部 smoke。[原卡 §7][card]；[CM record][cm]；[规范 §11.8.6][method]。

没有完整实现源码列在本清单，所以本次没有声称对当前入口完成独立代码审计或 seed-101 验收。真正威胁奖励、信息、训练或主量的依赖应在所选薄实现中解决或返回其具体缺口；不把它扩展为全历史重放。精确早期轨迹、上界／headroom 搜索、完整原因定位和逐中间数组发布都不属于本次比较；相应放弃何时退化、唯一机制、最优性、轨迹恒等和来源归因这些更强主张。[规范 §§11.8.1、11.8.7、11.9][method]。

## 六、不选择其他对象的具体理由

**选项 1：同 seed 89 的跨更新评估。** 它是一项新真实训练 B，不是读取已有早期 checkpoint 的免费 A：原记录只保存最终检查点。它需要一个 65,536-transition／512-step learner 和五个检查点各四行，至多 24,000 评估 tick。它能描述这个再训练实例的损失时间位置，却不增加独立 LR 配对，也不凭时间曲线识别归一化原因。当前无需先有该事实才可重复既有性能比较；同种子 update-16 的精确复现也不是后者的准入门。本轮不买它，因而不回答早发还是累积。[选项说明 option 1][options]；[规范 §§11.8.3、11.8.5、11.9][method]。

**选项 3：新配对种子加两个学习器的五检查点评估。** 训练量与所选方案相同，但有 2×5×4=40 个最终／中间 checkpoint episode，加四行初始化共 **44** 个，而不是简单把十二行翻倍；最大评估量 **52,800 tick**，比本次选择多 32 个 episode／38,400 tick。更多数据可能有用，但“单位花费信息最多”没有由计时或一个会随检查点结果改变的当前决定建立。它还要求评估状态／随机流与继续训练隔离、避免最佳 checkpoint 选择。既然本轮要决定 LR 比较是否值得继续，而不是训练时刻选择，就不增加这一维。[options 1–3][options]；[规范 §11.9][method]。

**选项 4：立即以零更新控制器做来源研究。** 原始源问题仍需普通合法 first-application 机会和匹配的 RETAIN/COPY/SHADOW 干预；目前没有选定这样的新对象，不能靠强制触发或挑一个有利控制器补出它。也不能把“零更新在两个种子的平均服务最好”说成所有条件都最好：seed 89 TARGET/K8 的 LOW_LR 为 760，高于初始 617。更重要的是，“修正路径上从没有控制器合法换主”超出了记录；B03 CONTROL 训练中有一次。它不提供当前评估来源差分，但必须保留。[paired][paired]；[B03 intake §2][b03]。

**选项 5：停车整个 DISH。** 不选择。这里已有一个真实处理的有限性能信号，以及一个能直接检验它跨随机实例是否仍值得开发的具体比较，故继续有正面的决策理由；不是因为来源价值未回答就无限延长。预测包支线仍结束，本轮不买第三个 LR 种子，也不自动授权下一个稳定化变体。后续若不再有具体、有限且能改变选择的对象，应停在最小相关分支，而非由未估计来源效应推导整个机制失败。

## 七、历史结果和来源问题的边界

CONTROL 两个实例的初末损失不改变 B03 的包增量劣势、seed-73 见证的条件性测量，也不改变 B02 在已执行滞后接口下的限定 inside-MEI。B01 的触发不足、A03–A05 的原有有界事实、普通续约 A01/A02 的局部行为测量和未测训练侧历史推断均保持；不得改写为“时序已解释 B02 的零差异”或把 B02/B03 合并为同算法独立重复。[前次完整答复 §§一、七][prior]；[DIRECTION 当前与历史章节][direction]。

所谓二十个评估行，包括 B03 最终八行、B04 最终八行与 B04 初始参考四行，不是二十个训练重复；更早的零更新见证八行另有记录。它们的无合法换主使已观察服务明确保持 incumbent-only，**来源量此前未估计，现在仍未估计**，不是由未估计变成来源无价值。B03 的一次训练换主不等于已完成匹配来源比较；私有标签克隆更不等于普通换主。RETAIN／COPY 已足够、deadline replay 可包含增益、checkpoint／伙伴角色共适应等替代解释仍保留。

本轮不改 Portfolio 生命周期、优先级、容量、融合、注册或 recast 计数，不对其他 N3 成分传递极性，不重开历史 R02。`PORTFOLIO.md` 不在本轮允许清单中，未读取或推测其现状；这里没有 RECAST 决定需要依赖该未读记录。[AGENTS §2][agents]；[DIRECTION][direction]。

## 八、实际证据访问与未验证事实

全部科学材料经连接的 GitHub 在固定版本 **`f6ba67cd7cb2b249057e08278eaf78ee72c4463e`** 读取。下表 C/ 表示 `docs/research/candidates/degraded_incumbent_shadow_handover/`，P/ 表示 C/ 下 `pro_packets/20260906_post_b04_convergence/`。引用中的旧答复亦是在这个版本读取；没有跟随其引用跳到清单外文件或用历史附件替代本轮材料。

| 实际读取路径 | 范围 |
| --- | --- |
| [C/DISH_CONTROL_LOW_LR_B04_RESULT_INTAKE_20260906.md][intake] | 完整结果与 intake |
| [C/control_low_lr_b04_20260906/low_lr/paired.json][paired] | 完整四行与主量 |
| [C/control_low_lr_b04_20260906/control/summary.json][control] | 完整，含 16 更新、LR 读回、reset、事件、资源 |
| [C/control_low_lr_b04_20260906/low_lr/summary.json][low] | 完整，重叠读取补齐末段 |
| [C/control_low_lr_b04_20260906/shared/summary.json][shared] | 完整初始化与四个参考，含参考无效提交 |
| [C/DISH_CONTROL_LOW_LR_B04_SCIENCE_CARD_20260906.md][card] | 完整，含原读法、验收、成本与停止边界 |
| [C/DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md][cm] | 完整；实施前未验证项与实际结果分开 |
| [C/DISH_INIT_WITNESS_A01_RESULT_INTAKE_20260906.md][witness] | 完整 |
| [C/DISH_POST_WITNESS_CONVERGENCE_INTAKE_20260906.md][prior-intake] | 完整，补齐尾部 |
| [C/pro_packets/20260906_post_witness_convergence/archive/RESPONSE.md][prior] | 完整，含原混合行限定和引用尾部 |
| [C/DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md][b03] | 完整；历史过强表述按已列限定理解 |
| [P/EVIDENCE_AND_OPTIONS.md][options] | 完整，建议与决定分开 |
| [P/EXPOSURE_AND_COST.json][cost] | 完整，既有派生计数与未来估计分开 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 完整固定快照与五条历史交付 |
| [C/DIRECTION.md][direction] | 行 210–310、350 至末尾；末段为 B04 选择，B04 结果以主源为准 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 行 35–112、308 至末尾，含 §§11.1、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 行 1–103，普通 §§1–5；不采用旧专用附款 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][runtime] | General requirements §§1–8，重叠补齐；不采用 VNFC 附款 |
| [AGENTS.md][agents] | 行 1–410，正文与实际返回的附录 A/B；未据其他运行时名称扩大权限 |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md][delivery] | 完整 |

二十条所列路径均可访问；范围读取不冒称全文。当前资料不能独立验证 seed-101 入口实现、未来回报、E/H 或完成耗时，亦没有给出早期完整评估轨迹；这些未测事实不被补造。现有验收与运行记录用于说明已完成 B04，不被说成本次又跑过测试。

固定 Issue 快照时刻是 **2026-09-06 22:44:22 UTC**。本次在 **2026-09-06 18:58:47 PDT（2026-09-07 01:58:47 UTC）之前**已实际读取 [Issue 4][issue] 正文及五条既有交付：[post-B02][comment-b02]、[post-A01][comment-a01]、[post-A02][comment-a02]、[post-B03][comment-b03]、[post-witness][comment-witness]；写入前再次检查分支、目标与评论。可变讨论不替代固定科学证据。

本次咨询没有执行项目代码、创建模型或 native 状态、运行 transition／backward／optimizer step、测试或实验。唯一外部改动范围是本完整答复及其 Issue 链接评论；新学习对象、实际源码接受和后续科学结果仍未发生。

[intake]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B04_RESULT_INTAKE_20260906.md
[paired]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04_20260906/low_lr/paired.json
[control]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04_20260906/control/summary.json
[low]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04_20260906/low_lr/summary.json
[shared]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04_20260906/shared/summary.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B04_SCIENCE_CARD_20260906.md
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md
[witness]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_INIT_WITNESS_A01_RESULT_INTAKE_20260906.md
[prior-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_WITNESS_CONVERGENCE_INTAKE_20260906.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_witness_convergence/archive/RESPONSE.md
[b03]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b04_convergence/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b04_convergence/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b04_convergence/ISSUE_SNAPSHOT.json
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[method]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/AGENTS.md
[delivery]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[comment-b02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
[comment-a01]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5558729980
[comment-a02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5560502547
[comment-b03]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5561089362
[comment-witness]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5562295763
