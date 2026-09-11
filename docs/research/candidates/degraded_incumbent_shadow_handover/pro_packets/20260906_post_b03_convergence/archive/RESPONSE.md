**方向层决定：继续现有首次合法应用时的 RETAIN/COPY/SHADOW 探索议程，但结束当前联合预测包支线的扩展投入；本轮只选择一个有界的 A/RECON 初末控制器见证，不选择新的学习器训练，不停车整个 DISH，也不作 RECAST。** 被结束的是当前宿主、接口和小预算下的「四维 Gaussian NLL、系数 0.025，加 sigmoid 服务接口」包的继续试验：不再为这个包自动追加种子、延长训练或围绕系数试变体。它不是对所有概率预测方法或状态来源机制的否定。

理由有两部分。第一，B03 已在两臂同样采用修正边界的条件下，给出完整且明显不利的原生包性能结果，足以结束这条具体支线的当前投入。第二，DM 用来支持转向“共同学习器退化”的核心前提尚未被测量：**128-tick 训练窗口的高服务，不能替代共同初始化在 1,200-tick 评估上的服务。** 这一分歧现在会改变下一步究竟是保护已有控制能力，还是研究有限预算学习能力，值得用一项直接的、无新训练的测量回答。[B03 结果 intake §§2–5][intake]；[两个原始 summary 的 curves、evaluation_rows][control][package]。

所选见证比 DM 的“三个策略各重跑四行”更窄，也修正其比较含义：**只新评估同一零更新初始化的 CONTROL、FORECAST_PACKAGE 两个接口视图，各四个完整条件；复用已经接受的两个 update-16 检查点的八行结果，不再执行它们。** 相同初始权重不等于相同完整控制器，因为 raw-logit 与 sigmoid 接口仍不同。下面明确输入、读法和 120 秒整项新支出上限。选择不是源码接受、实际启动或 Portfolio 动作。

## 一、B03 的不利读法保持，不用代理量或未测解释覆盖它

### 完整原生比较

| 开发条件，均为 speed 4 / slot 0 / block 0 | CONTROL 服务 tick | 包服务 tick | 包减 CONTROL | 包侧评估硬事件 |
| --- | ---: | ---: | ---: | --- |
| TARGET_VISUAL_MASK / K8 | 452 | 92 | −360 | 0 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 458 | 222 | −236 | 0 |
| TERRAIN_RELAY_MASK / K8 | 449 | 129 | −320 | 0 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 483 | 311 | −172 | invalid_commit 17；separation_breach 1 |

均值为 460.5 与 188.5，原配对主差分 **−272.0**，有用效果尺度仍为 **+24 平均服务 tick**。八行全部完成 1,200 tick。包的最后一行在范围末端同时记录 `fixed_horizon` 和 `separation_below_15`，最终间距为 14.71157529146157；不能因发生在范围末端就删除越界，也不能改写成较早终止造成的短曝光。CONTROL 四行没有硬事件。包每行能量较低约 4–7%，但在原主问题下不能抵消服务损失。原卡第 5 节的不利读法正确，保留全部行，不增加显著性或每行同号的必要条件。[原卡 §§4–5][card]；[CONTROL summary：evaluation_rows][control]；[包 summary：evaluation_rows、paired_primary][package]。

这里的“没有合法换主”**限于八个评估 episode**。原始训练汇总另记 CONTROL 有 **1 次 `training_legal_transfers`**、包为 0；训练 invalid_commit 分别为 **2,184、1,275**。不把这一次普通训练换主抹掉，也不把它升级为已完成来源干预、稳定接力能力或最终检查点的评估机会。八行评估的服务仍是 incumbent-only，COPY–RETAIN 与 SHADOW–COPY 仍未估计。[两个 summary：training_legal_transfers、training_hard_events、evaluation_rows][control][package]。

### 真实学习和有限的极端优化值

两臂均有 65,536 条普通训练转移、16 次完整更新、512 次优化器步和 4,800 评估 tick。共同初始参数范数是 38.24996300787587，最终 L2 位移分别为 8.605231896111574、7.5142387939077615；不是没有学习或没有参数移动。包的每更新平均损失最高为 **6,541,776.3828125**，每更新平均裁剪前梯度范数最高为 **1,755,882.8818359375**，均在 update 10；CONTROL 对应梯度均值最高为 **875.392335653305**。这些是记录中指定的均值极值，不是每个 minibatch 的最大值，更不是裁剪后实际更新范数。[两个 summary：actual_exposure、parameter_movement、curves][control][package]。

这些有限大值及包的低服务都保留为不利证据；没有材料证明它们是数值非有限或测量损坏，因而不能为挽救包的解释而隔离整臂。它们也没有独立定位 NLL 尺度、协方差条件数、共享表示、消息反馈或标签支持中的哪一项是原因。最终训练 BCE 或不同定义的 MSE/NLL 数字不能替代匹配预测误差或原生收益。[B03 intake §3][intake]；[B02 完整结果“Actual learning and exposure”][b02]。

**结束当前包投入的最强支持**是这次完整、同接口的原生损失和伴随硬事件；**反对扩大关闭范围的最强理由**则是一对训练样本不能证明稳定劣势，更没有隔离联合包的成分。B02 的滞后接口零差异与 B03 的修正接口负差异不是同一算法的两个重复，不能合成“两个独立负例”或估计时序修正效应。结束这条支线是限定的下一步选择，不是统计学上的家族无效定理。[原卡 §§1、3、5][card]；[前次完整裁决 §§四、七][previous]。

## 二、当前 intake 有几处需要在解释上收窄

**“十六次更新使两臂都比初始化更差”尚不是观察。** B03 intake 第 3 节这样表述，但任务和选项说明同时承认初始控制器从未做完整评估。训练窗口还随 episode 年龄、路线事件、reset、当前策略和数据分布改变；不能用 update 1 的 4,016/4,096 与最后四个 1,200-tick episode 的比例直接比较，进而识别更新的效应。[intake §3][intake]；[选项说明“Unknowns”][options]。

原曲线也不是单调退化证据。CONTROL 在 update 11 达到 **4,093**，超过 update 1 的 **4,016**；包在 update 11 为 **3,800**，随后又下降，末次回升到 **1,340**。update 10 的 `next_mask_count=4064` 及相关 reset 背景应保留。这种共同的阶段性模式与“episode 内后段更难、reset 后更容易”的解释相容；它并不证明该解释，也不排除真实学习损失。所选见证正是用相同完整评估条件区分这些说法中的一个关键前提。[两个 summary：curves，updates 1、10–16][control][package]。

“update 1 完全一致”也要限于确实相同的量：训练服务和若干支持计数相同，但 CONTROL 的平均 loss/gradient 是约 **794.974 / 66.639**，包为 **1671.513 / 33463.701**，不能称整个更新相同。服务标签 eligible 数 **18,775 对 7,972**是实际支持差异，却不能单独归因给 sigmoid；处理还共同改变了 NLL 学习及后续轨迹、预测和消息状态。[两个 summary：curves[0]、service_label_eligible][control][package]。

还有一处历史数值误引：B03 卡片第 5 节的 DM 预测理由把 B02 写成包均值 447、CONTROL 572。B02 原结果是**两臂均值均为 470**，572 和 447 是两臂各自前两个条件的行值。旧预测原文及其错误结果继续保留；本轮不以这个错误前提选择对象，也不改写旧卡片。[B03 card §5][card]；[B02 “Frozen measurement and observed readout”][b02]。

这些限定不改变 B03 的 −272 主结果或不利读法，也不把 B01/B02/A03–A05 追溯隔离。历史普通训练侧滞后仍按原重释保留为源码支持的推断，不由 B03 改造成全历史测量；B01 的 prepared 路径尤其不能由 B02 的两个普通窗口代替。[限定重释 §§1–3][reinterpretation]；[前次完整裁决 §一及 §四][previous]。

## 三、唯一下一对象：匹配接口的零更新控制器见证

### 类别、问题和当前决策价值

**A / RECON，固定控制器与已有记录的有界比较。** 问题是：在 B03 的同一四个完整开发条件上，两个已记录的 update-16 完整控制器，分别比其同接口的零更新初始化视图服务更低、近似或更高吗？

主张只到这几个固定控制器、指定外生随机和该面板的条件性测量。它不是一次新的学习实验，不提供独立训练重复，不把初末差值归因于 PPO、学习率、NLL、归一化中的某个成分，不建立一般“学习损害”或稳定能力。初末对照包括训练后形成的全部控制器状态差异，而不只是参数矩阵差异。[证据规范 §§3、4、5.1、11.8][method]。

与上一轮不同，当时要决定的是联合包相对原学习器的增量，初始基线没有必要；前次裁决明确放弃了绝对学习价值主张。现在 DM 正以“共同退化”作为稳定化后继的理由，所以同条件初始基线能改变下一问题的选择。这是本节点的具体测量价值。**不同意把它说成“任何学习器侧下一对象都必须先有的事实”。** 一项独立说明理由、直接测原生性能的 B 不必先证明历史退化；本次只是没有选择那项 B。[前次完整裁决 §三][previous]；[证据规范 §11.9][method]。

### 策略视图、已有比较值及最小输入

| 视图 | 本对象如何取得 | 普通服务接口与状态 | 工作 |
| --- | --- | --- | --- |
| 零更新 CONTROL 视图 | B03 seed 73 的既定共同初始化 | raw service logits；原零更新归一化状态；每个 episode 新鲜循环状态 | 新评估四行 |
| 零更新 FORECAST_PACKAGE 视图 | 同一份初始参数，不再抽新权重 | sigmoid 服务接口；与前者相同的零更新归一化起点；每个 episode 新鲜循环状态 | 新评估四行 |
| CONTROL update 16 | 已接受的 CONTROL summary | 原完整最终控制器及其评估配置；结果 452 / 458 / 449 / 483 | 只读复用，不运行 |
| FORECAST_PACKAGE update 16 | 已接受的包 summary | 原完整最终控制器及其评估配置；结果 92 / 222 / 129 / 311 | 只读复用，不运行 |

这样共有四个比较视图，但**只新增两种初始接口视图的八个 episode**。不因初始权重相同、首个训练窗口服务相同，就假设两初始视图的 1,200-tick 行为相等。sigmoid 已是推理行为的一部分；NLL 在这个零训练对象中不执行。用一个未注明接口的“共同初始策略”同时对照两个最终策略，会把初末变化和接口差异混合。[原卡 §§2–3][card]；[两个 summary：configuration、evaluation_rows][control][package]。

种子与输入固定为 **B03 的既有 seed 73**，不是再购买一个训练种子。复用记录的 master `b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a`、block 0、STRUCTURED 初始化法则；不调用 B02 的 seed 61，不重建训练过程，不从最终参数反推初始化。原 B03 CM 记录列明复用 `build_master_addressed_initial_state`、`evaluate_episode` 等既有组件；它支持最小实施方向，但本次清单没有实现源码，因此不声称本答复已经独立验证那些函数的当前行为。[B03 card §3][card]；[CM record“Helpers reused”][cm]。

**原始零更新快照是否单独保存，当前材料未证明。** 所选可执行定义是：有该快照就读取；否则由上述已记录 master 和既有 B03 初始化器一次生成指定的零更新状态，并明确标成重建的初始化，不谎称读取了已留存原始快照。必须同时明确原零更新归一化状态，不能借用任一最终 Welford 状态或用评估数据重新拟合。初始范数 38.24996300787587 只是已记录核对量，**不构成参数相同的证明**。若现有保存状态或既有构造路径不足以给出这个确定的输入，就返回这一个输入缺口；不另训一个模型、搜索一个初始化或开展全历史重构。输入绑定是这项特定初末比较的完整性要求，不是一个通用 B 门槛。[两个 summary：initial_model_norm、configuration][control][package]；[证据规范 §§4、11.8.7][method]。

### 宿主、条件和因果路径

保持 `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`、修正普通续约边界、原生 dtype float64、策略 FP32、原单线程配置及不变的奖励、信息、动作空间、投影、准备/证书/换主规则。不拟合、不优化、不调阈值。角色仍是两个物理 UAV、当前 owner、standby 与各自 active/shadow 副本；初始化控制器不是 held-only 控制器，仍可提出运动和协议动作。[原卡 §§1–4][card]。

新评估逐行直接复用两个 summary 已记录且配对一致的完整 `evaluation_rows[].reset`，不只凭行标题重建近似场景。条件为两退化包 × K8/K4_TO_K12，speed 4、slot 0、block 0；记录中的相位依次为 **4、2、1、1**，切换时刻和退化时刻沿用该行，不另抽相位、路线或噪声。每个初始视图都从该行相同外生输入、新鲜 native/循环状态出发，普通确定性评估；不让一个视图的状态或结果流入另一个。[两个 summary：evaluation_rows[].reset][control][package]。

路径是：**既定路线与退化事件 → 角色相关因果观测/真实消息 → 冻结权重下的循环状态 → 当前许可下的普通运动及 prepare/commit/预测输出 → 不变 native 行为与服务 → 固定范围归约，再与已有最终控制器行值相减。** 没有新的信用分配或学习步骤。私有 passive-label promotion、来源 fork、脚本强制换主都不进入此测量。

每行固定 1,200-tick 服务范围。native 提前终止就停止实际 stepping，未执行余段的服务计零，同时报告完成 tick、终止原因与事件。换主发生后继续普通评估，不按触发、服务符号或相位筛行；时间上换主后的服务不能自动称为新 owner packet 的服务。[原卡 §4][card]。

## 四、测量、读法与验收范围

令 `J_a,0,r` 为新测的零更新视图服务，`J_a,16,r` 为复用的原 B03 最终行值，a 分别表示 CONTROL 和 FORECAST_PACKAGE。主描述量是两个匹配接口的初末差值：

`D_a = (1/4) * Σ_r (J_a,16,r − J_a,0,r)`。

同时报告每个视图均值、全部逐行初末差值、原 B03 配对差分 −272 的既有来源。原值与新值应有清楚的数据来源列，不能把八个复用行写成新跑过。**描述性有用变化尺度取 24 平均服务 tick，正负对称使用**；这是同一 1,200-tick 服务量纲上的 0.02、2.4 秒服务，用于当前下一步选择，不是重新定义 B03 的 +24 规则。单 tick 是事件分辨率，24 不是数值匹配容差，不要求每行跨过它。[原卡 §§4–5][card]；[证据规范 §11.7][method]。

伴随测量为能量、七类 hard events、完成/未执行 tick、终止原因、普通合法换主及换主前后服务，沿用既有字段。没有来源包归因就只作时间描述。权重更新/训练转移/backward/optimizer.step 均为零，参数前后范数与位移据实记录；循环状态的正常演化不是参数学习。

| 观察模式 | 允许的读法，以及它改变的下一项建议 |
| --- | --- |
| CONTROL 的 D_C ≤ −24 | 这个最终 CONTROL 在四行上低于其同接口零更新视图，给“保护或恢复基线能力”的具名稳定性 B 提供具体动机；不证明学习率过大或 PPO 本身有错。若包也下降，报告共同的条件性前后损失，不把两臂当两个独立 seed。 |
| CONTROL 保持或提高，而包有明显初末损失 | 不采用“共同学习器都退化”的已知事实叙述；当前包停止不变。后继若提出，应针对仍有根据的具体学习/控制问题，而非以共同退化为依据普遍降低更新强度。 |
| 两者相对各自初始化提高 | 本面板不支持“十六次更新使两臂更差”；B03 的包相对 CONTROL 不利结论仍成立。绝对前后改善和包的增量劣势可以同时存在。 |
| 带内、行间异质或伴随不利代价 | 保留每一行，说明未建立清晰的大幅前后变化，不宣称等价；任何后继都须有具体理由，不靠补样本直到符号统一。 |
| 新输入/路径/测量不足或未完成 | 只保留可信的已测行，不能补出完整 D_a，不能要求旧 B03 被一并隔离；返回受影响的具体比较缺口。 |

上述模式按每臂的数值分别描述，再附上真实事件和能量；不是一个“必须两臂全下降才能准许 B”的新门。零更新视图自身出现原生坏行为也是有效观察，不能更换初始化或把这些行过滤掉。任何输出都**不自动购买学习器 B、恢复预测包投入或改变 Portfolio**。

验收只需证明实际运行的是上述输入与普通路径、八行或合法终止均完整、没有训练更新、既有最终行正确按坐标连接、固定范围服务及事件可读。复用 B03 已接受的主归约与修正边界覆盖；只对新增的初始化/双接口绑定、冻结归一化、既有数据复用和主输出做一次针对性检查。无须重跑 A01/A02 窗口、全部 r06 套件、最终八行、训练历史、每个隐藏数组或跨平台位级一致性。若不能建立与原 B03 相同的宿主、信息、终止或评估语义，受损的是这次复用对比；不得用未经选择的最终重跑或新实现偷偷补齐。[CM record，执行附记中的 21 项通过][cm]；[scope §§3–5][scope]；[证据规范 §§11.8.5–11.8.7][method]。

## 五、工作量、完整成本和停止边界

### 本次新测量的规模

| 项目 | 新工作 |
| --- | --- |
| 已有训练样本 | 复用 seed 73；新增独立训练样本 0 |
| 初始化 | 一份指定零更新参数/归一化状态，两种接口视图；实际模型构造、加载次数记录 |
| 原生评估 | 2 视图 × 4 条件 ×至多 1,200 tick，即至多 **9,600** 实际完成 tick |
| 训练、PPO replay、backward、优化器步 | 0 |
| next-label / delay / consequence 标签工作 | 0；不调用 passive-label 接口 |
| 最终控制器比较数据 | 读取原八行，不加载或执行两个 update-16 检查点 |
| 搜索、来源分叉、held-only、B02 检查点 | 不包含 |

初始化不是零计算或零 RNG/模型曝光。既有初始化 helper 若构造了未步进的 optimizer 或额外模型对象，也必须如实记录并收费；“零训练”不能将这些调用藏起来。不得为了取一个初始化调用会 backward 或更新参数的全更新 wrapper。新测量的总工作还包括 import、实际支付的构建/加载、普通前向、状态与输出处理、聚焦检查及发布，不仅是 9,600 个 tick。[B03 CM record 的复用路径][cm]；[runtime General requirements §§2–3][runtime]。

**本对象新选择 120 秒整项计算 wall 支出上限。** 包含一次正式测量以及它实际需要的一次聚焦检查、初始化/构建/加载、比较与最终发布；共享准备只收费一次，不能写成“120 秒另加未定 native 构建”。一次逻辑对象拆成检查和正式调用也不重置上限。已有测试覆盖能复用就复用，不能把整套重复测试塞进这笔观察。

这 120 秒是有限支出选择，不是已测投影或完成保证。DM 的“远低于 60 秒加构建”和学习器 B 的“约 410 秒”都未由对应完整测量建立；不采用为承诺，也不因此另购校准实验。A02 的 64 tick 窗口时长不能直接外推为长 episode 冷启动单位成本；B03 的 196–211 秒整臂时长含学习和标签工作，曲线的每更新 wall 也不是独立的评估时长。[成本记录“prospective_option_a/b”][cost]；[runtime §§2–3、8][runtime]。

在既有 `wsl_4070`、单线程 CPU、原 FP32/float64 数值路径上，使用精确已提交和推送的源码及 detached supervision。每个实际调用在执行节点新鲜测得 physical/effective available memory 均至少 4 GiB。报告完整 wall 和注明范围的 peak RSS；无新的 profiler、registry、validator、worker pool、ABI 或资源阈值。普通 2,000 新源码行、600 runner 行、既有测试预算保留；编排比例仍只是审查信号，无 A05 例外继承。[AGENTS §§5、7–8][agents]；[scope §§3–5][scope]。

正式观察在八个 episode 及完整发布结束时停止，或在余下 wall 预算耗尽、输入不成立、出现威胁主测量的实际失败时停止。终止事件本身按科学终止规则保留，不是失败重跑的理由。没有早期较佳 checkpoint、替换 seed、扩相位/条件、自动 retry 或临时加最终策略重跑。超限或不完整时留下实际行与计数，不伪造未观测回报；本轮没有第二笔对象额度。

### 既有成本的准确用途

B03 成功链的整臂 wall 为 211.04 与 196.18 秒，共享检查 4.94 秒，原记录收费 **412.16 秒**。两次早期启动失败另有记录；其中 ModuleNotFoundError 的 **2.48 秒**及未完整测量的操作者开销不能从项目历史中消失，412.16 也不能冒称全部历史总成本。B02 成功链为 **642.66 秒、669.61 CPU-s**；两组不是同对象的速度试验，不能计算接口修正的因果加速比。[B03 CM 执行附记][cm]；[B03 intake §1][intake]；[B02 “Exact process, cost and resource evidence”][b02]。

B03 原学习的嵌套工作保持原读法：`2N+2E+H`，H 未测且 `0≤H≤20E`。CONTROL 原生训练调用界为 **168,622–544,122**，包为 **147,016–306,456**，不是确定实际调用数；本次 A 不重做这些标签或优化工作。B02+B03 的 **262,144** 普通训练转移是这两对包比较的累计，不是包括早先 B01 在内的整个 DISH 历史总曝光。[两个 summary：actual_exposure][control][package]；[成本记录 budget_state][cost]。

## 六、其他选项、旧结果与重新开启条件

**不增加 B02 的 update-16 检查点，也不增加 held-only 行。** 前者同时带入 seed 61、滞后训练历史和接口改变，不识别 B03 的同接口初末变化，也不识别时序的因果效应；后者回答学习运动相对持有的另一个问题。它们不是当前见证的必要输入，不作为可随手附加的免费旁测。[前次完整裁决 §§三、四][previous]。

**本轮不选择学习器稳定性 B。** 较低学习率或较少 epoch 可以成为独立、合理的 outcome-informed 性能问题，并不违法也不一定要先见到初始退化。但是当前没有事实把其中某个改动选成已定位的治疗；“采用现有 gradient clipping”尤其不是已经说明差异的新处理，B03 卡片本来就保留裁剪。有限大裁剪前梯度并不证明没有裁剪。用本次八行初始见证区分“最终 CONTROL 丢失已存在的服务”与“短训练窗口不是长期基线”，比现在同时改更新规则、预算和归因叙事更直接；其结果不预授权下一轮训练。[原卡 §2][card]；[选项说明 2–3][options]。

**不把整个 DISH 停车。** 此刻仍有上述具体、有限、会改变后继解释与选择的对象。与此同时，当前联合预测包支线确实结束，不以“机制还未知”索取无限修补。重新开启包探索，须在既有决策流程中提出有独立具体理由的新科学变化、清楚的同信息比较与原生主量、完整有限工作和支出；不以改名、微调一个系数或选择更有利 seed 规避当前停止。无须先证明唯一原因、精确上界或完整校准，正信号也不是所有后继的普遍前提。重开永不擦除这次包的原生损失与硬事件。[证据规范 §§5.2、11.8–11.9][method]。

B01 的触发不足、A03–A05 的原有有界事实、普通续约 A01/A02 的测量和推断边界、B02 的限定 inside-MEI、B03 的不利结果都保持。即使新初始见证显示两个最终控制器都低于各自初始视图，也不改变这些旧对象的原结果规则；更不推出 SHADOW/COPY/RETAIN 无价值。COPY、RETAIN、deadline replay 以及检查点/角色状态共适应等解释继续存在，闭合 R02 不重开。当前结论不改变 Portfolio 生命周期、优先级、容量、融合、注册或 recast 计数，不对其他 N3 来源传递极性。[DIRECTION 的历史关闭、B01 与当前家族章节][direction]；[限定重释][reinterpretation]；[AGENTS §2][agents]。

## 七、证据访问和未验证范围

所有科学材料均经连接的 GitHub 读取，固定在 **`3f71098dc008868d03444a136708106e63b96d41`**。下面 C/ 表示 `docs/research/candidates/degraded_incumbent_shadow_handover/`，P/ 表示 C/ 下 `pro_packets/20260906_post_b03_convergence/`。没有执行项目代码或重新计算实验，也没有以旧对话附件代替当前证据。

| 实际读取路径 | 范围 |
| --- | --- |
| [C/DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md][intake] | 完整 intake；区分主结果与其过强解释 |
| [C/b03_forecast_package_20260906/control/summary.json][control] | 完整机器摘要，含十六更新、完整 reset/终止、训练及资源字段 |
| [C/b03_forecast_package_20260906/forecast_package/summary.json][package] | 完整机器摘要，含 paired_primary 与全部原始行 |
| [C/DISH_FORECAST_PACKAGE_B03_SCIENCE_CARD_20260906.md][card] | 完整原卡，保留错误预测的历史原文 |
| [C/DISH_FORECAST_PACKAGE_B03_CM_RECORD_20260906.md][cm] | 完整记录，执行附记与较早未执行模板分开 |
| [C/DISH_FORECAST_PACKAGE_B02_RESULT_EVIDENCE_20260905.md][b02] | 完整技术结果；没有据此声称读过未列出的 B02 原始曲线文件 |
| [C/DISH_B01_B02_QUALIFIED_REINTERPRETATION_INTAKE_20260906.md][reinterpretation] | 完整限定重释 |
| [C/DISH_POST_A02_CONVERGENCE_INTAKE_20260906.md][previous-intake] | 完整 intake |
| [C/pro_packets/20260906_post_a02_convergence/archive/RESPONSE.md][previous] | 完整前次答复，重叠读取补齐被截断段及引用尾部 |
| [P/EVIDENCE_AND_OPTIONS.md][options] | 完整 DM 建议，未当作既定决定 |
| [P/EXPOSURE_AND_COST.json][cost] | 完整文献性派生记录；未来成本不是实测 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 完整固定快照，含三条此前交付评论 |
| [C/DIRECTION.md][direction] | 行 210–310、350 至末尾；所见末段是 B03 选择，B03 原结果用上述主源 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 行 40–122；300 至末尾，含 §§11.1、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 普通 §§1–5；不借用不适用的旧对象附款 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][runtime] | General requirements §§1–8，重叠补齐尾部；不使用 VNFC 附款 |
| [AGENTS.md][agents] | 正文与实际返回的附录 A/B；运行时名称不扩大本任务权限 |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md][delivery] | 完整说明 |

列出的路径均可访问。当前清单没有 B02 原始逐更新 summary 或实现源码，所以没有跟随目录名、旧答复引用或 Issue 中的其他 ref 去补取；B02/B03 是否在相同 episode 阶段都有相似曲线，不能凭 B02 的训练总和和损失范围作完整比较。`PORTFOLIO.md` 也不在允许列表中，未读取或推断其 recast 状态；本轮没有作 RECAST，因而不需要据未读记录分配后果。

固定 Issue 快照的读取时刻是 **2026-09-06 17:37:50 UTC**。本次实际读取 [Issue 4][issue] 正文与全部评论，在 **17:53:35 UTC 之前**已取得三条历史交付：[post-B02][comment-b02]、[post-A01][comment-a01]、[post-A02][comment-a02]；它们不是当前交付，也不替代固定科学证据。交付前再次检查目标、分支和评论，避免覆盖或重复。

本答复未加载模型、创建 native 状态、运行转移/backward/优化器、测试或实验。新的零更新视图、其完整原生回报及 120 秒内完成可行性尚未观察；仅给出上述明确输入和停止边界。唯一获准的外部改动是本答复文件及其 Issue 链接评论，既有科学文件和状态没有被修改。

[intake]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md
[control]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/b03_forecast_package_20260906/control/summary.json
[package]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/b03_forecast_package_20260906/forecast_package/summary.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_SCIENCE_CARD_20260906.md
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_CM_RECORD_20260906.md
[b02]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B02_RESULT_EVIDENCE_20260905.md
[reinterpretation]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_B01_B02_QUALIFIED_REINTERPRETATION_INTAKE_20260906.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_A02_CONVERGENCE_INTAKE_20260906.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a02_convergence/archive/RESPONSE.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b03_convergence/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b03_convergence/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b03_convergence/ISSUE_SNAPSHOT.json
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[method]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/AGENTS.md
[delivery]: https://github.com/CartmanFatass/My-paper-code/blob/3f71098dc008868d03444a136708106e63b96d41/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[comment-b02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
[comment-a01]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5558729980
[comment-a02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5560502547
