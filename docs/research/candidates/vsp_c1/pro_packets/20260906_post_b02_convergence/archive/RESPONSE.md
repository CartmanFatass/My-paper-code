**决定：在当前边界结束“公开固定伙伴计划、六步、两个外生周期、全八 context”的价值参数化玩具族，不再为这个相同科学问题追加预算、种子、优化器变体或比较臂。保留 K4 的跨周期价值共享问题，但本次不同时选择新宿主 B，也不把停止这个家族改称为关闭 K4 或改变 Portfolio 状态。结束前不需要任何额外实验或观测。**

最强理由是下一项观测的决策价值已经改变：有限独立种子跟进揭示了原预算下的实例敏感性；随后那一对连续长训练回答了一个新的、具体的预算问题——这个新实例的早期领先在双方追加学习后归零，而且双方都达到现有宿主的合法策略参考值。继续原组合不会给这个已测终点创造更高的刻度；再换种子或比较器，主要是在细化这个小型公开计划控制问题的优化路径，而目前没有一个明确的 K4 后续选择必须依赖这种细化。**这是一项停止新增投入的方向判断，不是“所有剩余问题已经被证明没有价值”，更不是稳定优势、等价性或负迁移的实验证明。** [B02 结果 intake，§§3–5、8][b02-result]；[既有完整决定，§§三、五、八][previous]

对停止最强的反对意见同样成立：FACTOR 在新实例中并非毫无收益。它从较低的初始平均回报出发，在 128 处领先一个描述性 MEI，预设全曲线与后段 AUC 都为正，并在已记录的评价点上更早达到参考值。这些真实曲线事实不能被最终相等抹去。我的取舍是保留它们而不再研究这个宿主，不是把它们改判为零。[两臂原始 metrics 与 curve][factor][generic]

## 一、保留的科学结论：混合的短预算信号，以及一个实例内的追平

本文仓库科学证据统一读取自固定版本 `b7efcb9ce7e5c378f0442af79d5b99915eb11eca`。以下链接均保留完整来源路径；文档中引用的其他历史源版本没有替代本次固定证据。

### 原三种子的正负结果不改写

| B01 训练种子 | 初始 J：FACTOR / GENERIC | 128 更新 J：FACTOR / GENERIC | 终点差 | 原定 AUC(0:128)：FACTOR / GENERIC | AUC 差 |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.500000 / 0.500000 | 0.625000 / 0.666667 | −1/24 | 0.580729167 / 0.609375000 | −0.028645833 |
| 1 | 0.458333 / 0.500000 | 0.708333 / 0.625000 | +1/12 | 0.625000000 / 0.591145833 | +0.033854167 |
| 2 | 0.458333 / 0.500000 | 0.708333 / 0.625000 | +1/12 | 0.593750000 / 0.570312500 | +0.023437500 |

原三种子平均终点差仍为 `+0.041666667`，原三种子平均 AUC 差仍为 `+0.009548611`。它们是保留原始负 seed 的既有描述性汇总，不是稳定性估计或显著性结论。seed 0 在更新 16 的暂态领先和更新 64 的 −1/8 差距都保留；不把有利 checkpoint 换成终点。其终点损失位于 `(p=6, tau=2, c=1)`；两个新种子的比较损失转移到不同的短周期 context。这个位置变化支持实例敏感的读法，而不是唯一因果机制。两次新正结果也不能反向宣布原负结果异常或无效。[seed 0 完整结果，All primary observations][b01-zero]；[seed 1/2 完整结果，Rule and measurements][b01-two]

### B02 只是一对新实例的连续预算观察

| 预设量 | FACTOR | GENERIC | FACTOR − GENERIC |
| --- | ---: | ---: | ---: |
| J(0) | 0.458333333 | 0.500000000 | −0.041666667 |
| J(128) | 0.750000000 | 0.666666667 | +1/12 |
| J(512)，主终点 | 0.833333333 | 0.833333333 | 0 |
| J(512) − J(128) | +1/12 | +1/6 | D = −1/12 |
| J(512) − J(0) | +0.375000000 | +0.333333333 | — |
| AUC(0:128)，分母 8 | 0.643229167 | 0.640625000 | +0.002604167 |
| AUC(0:512)，分母 32 | 0.763671875 | 0.718750000 | +0.044921875 |
| AUC(128:512)，分母 24 | 0.803819444 | 0.744791667 | +0.059027778 |

这些读数来自两份原始 summary 的 `metrics`，与 intake 的预设测量表相符。描述性 MEI 为绝对 `1/12`：128 的差恰等于它，512 的差为零，预算差的变化为 `−1/12`。MEI 没有因此变成等价界、显著性线或继续研究的门槛。[FACTOR 原始 metrics][factor]；[GENERIC 原始 metrics][generic]；[B02 卡，§2][b02-card]

128 和 512 属于同一对训练路径，二者的相关性正是这个对象的含义；它们不是独立训练样本。seed 3 的 128 前缀可以和上表逐个对照，但本次不形成四种子合并均值，不把一个 512 点并入旧三种子终点，不合并不同窗口的 AUC。33 个 checkpoint、八个 context 和追加的 episode 也不是新增训练 seed。[B02 卡，§§1–2][b02-card]

两臂在 512 的全部四个短周期 context 均为 `1`，全部四个长周期 context 均为 `2/3`。在原宿主中，短周期可以在伙伴切换边界换动作；长周期从头到尾必须持有一个动作，只能匹配六步中的四步。因此原卡给出的等权合法自由策略参考值为 `5/6`。这里的剩余 `1/6` 不是这个新实例尚未学掉的合法策略误差，更不能靠放宽持有规则后再说原模型提高了。参考是原卡的解析事实，不是实跑的第三臂、调优 headroom 或旧 A01 的补值。[B01 卡，§2][b01-card]；[两臂原始 curve 的 update=512][factor][generic]

FACTOR 在所记录的评价网格上首次触及 `5/6` 的点为 208，随后仍有回落；从 400 到 512 的已记录点都保持该值。GENERIC 首次触及的记录点为 432，448 回落到 `0.791666667`，从 464 到 512 的已记录点都保持参考值。这个“更早”是按每隔 16 更新的一次贪婪评价观察到的，不是逐更新的精确首达时间、墙钟速度优势或 512 以后不会退步的证明。FACTOR 的 208 后回落以及 GENERIC 在更新 16 的较高回报也说明，两条曲线并非全程同序。[B02 intake，§3][b02-result]；[FACTOR curve 的 update=16、208、224][factor]；[GENERIC curve 的 update=16、432、448、464][generic]

最小事实结论因此是：**指定全支持公开计划任务上的原预算参数化信号随训练实例变号；一个新实例中，原预算的 FACTOR 领先在四倍训练方案下被追平，同时仍留下有利于 FACTOR 的预设评价曲线面积及更早的网格首达记录。** 不把其中任何一项删掉，才是完整读法。

## 二、先执行已经写好的结果读法，再作本次家族判断

B02 原始 summary 的状态均为 complete，主依赖缺陷列表为空；训练、评价和检查计数与卡一致。既有源码及记录支持实际持有动作、伙伴切换、原生 reward、bootstrap、loss 权重与更新的比较含义。没有发现必须先另做实验才能解释主结果的具体依赖缺口。[原始 summary 的 status、checks、training_counts、evaluation_counts][factor][generic]；[实际核心实现][experiment]；[512 循环实现][budget]

据此，B02 卡第 3 节中依赖受损的第一行不适用；正差保持或扩大不成立；128 不利而 512 有利也不成立。**首先适用的是第 4 行**：128 有利，512 缩为零，而且 GENERIC 后段增量更大。其已执行后果保持原样：不再延长未改变的模型/优化器组合去寻找更大的终点优势，不做 1,024/2,048 更新，不追加第四个 B01 seed，不重复 B02 实例。它不证明等价或普遍负迁移。[B02 卡，§3][b02-card]；[B02 intake，§§4、8][b02-result]

第 6 行不能被简写成“双方到参考，所以自动满足整行”。该行还包含“没有有用曲线差异”，而本例确有预设 AUC 差和首达记录差；intake 正确保留了这个不满足的条件。参考值相等是解释零终点的事实，不是凭它改选第 6 行的理由。第 7 行的守则仍约束叙述：不能因 AUC 有利就改换获胜指标，宣布总体共享效率获胜。[B02 卡，§3][b02-card]；[B02 intake，§4][b02-result]

**本次更广的“停止这个玩具族”是对未来观测价值重新作出的方向选择，不是伪称旧卡已经自动决定了所有比较臂。** 这也保留了探索规范的区别：B 没有消费状态；选择不再投入，并不使过去的有效 B 被消费、撤销或改判。[证据规范，§§5.2、11.1、11.8–11.9][spec]

前次工作预测“128 的差距更可能缩小而不是扩大”在这个实例上吻合，所列反驳情形“FACTOR 的后段绝对回报与相对差距一起增加”没有发生。但这不是对概率预测的总体校准。DM 预期后段 AUC 差小于前缀差则明确被结果反驳：实际是约 `0.0590 > 0.0026`。双方后段继续改善、GENERIC 改善更多等预期吻合；不能只展示命中的部分。[既有完整决定，§五][previous]；[B02 卡，§5][b02-card]；[B02 intake，§5][b02-result]

## 三、实现在比较什么，以及仍不能归因的部分

真实作用链已经存在：公开的伙伴切换计划决定伙伴实际动作；外生周期决定焦点行动何时可以更新及其持有长度；实际联合动作的匹配产生每步服务 reward；每个实际持有段的 reward 与下一 renewal 的 detached bootstrap 进入 Q 学习；新的 Q 值改变之后的合法选择与完整六步回报。因此这不是仅改变标签而不发生学习后果的假比较。[B01 卡，§§2–4][b01-card]；[experiment.py 的 Value、state_at、rollout、run][experiment]

但伙伴程序固定、计划完全公开，且其未来行为不受焦点当前动作影响，所以这是一个可还原的单控制器问题。GENERIC 不是“不共享”的对照：它同样共享隐藏特征，只是通过周期输入形成一般非线性值函数；FACTOR 通过状态—动作表征与周期嵌入的乘法结构实现共享。188 与 191 参数相近不证明函数类包含或优化条件相同，四维因子与两个周期列也不产生有约束力的低秩瓶颈。[B01 卡，§§1、3][b01-card]；[Value 实现][experiment]

两臂同样采用每批 32 个真实 episode、一次 Adam 更新、学习率 0.01、全局裁剪 5。每个真实段的 reward 按完整 horizon 归一化，终局 continuation 为零；每个 episode 内先平均 renewal 误差，再平均 episode，使两周期各占一半 loss 权重。短周期却仍有每批 48 条 renewal，长周期只有 16 条，bootstrap 深度也不同。512 循环保留前 128 的探索分母 127，之后固定 epsilon=0.1，没有在 128 重置模型或优化器。这些定义能解释本次预算处理的实际含义，不能分别识别数据量、更新量、退火、参数几何和共享的纯因果效应。[B02 卡，§1][b02-card]；[experiment.py 的 run][experiment]；[budget512.py 的 epsilon_at、run][budget]

已有真实参数位移排除了“根本没有学习曝光”的说法。在 B02，FACTOR 的初始化范数约 4.020，0→128 位移 2.364，0→512 位移 3.557，128→512 位移 1.928；GENERIC 对应为 3.877、1.935、2.531、1.334。位移不是机制效益，更不是应再设一个比值门槛的理由。FACTOR 较低的初始平均回报排除的仅是“它只是从更高平均回报起步”这个解释，没有排除初始策略、双线性参数化和优化路径差异。[两臂原始参数字段][factor][generic]

因此仍未知：训练总体的预算交互；旧三个 seed 自己在 512 的表现；早期曲线差异在其他训练实例是否保留；不同表示、初始化与 credit 的相对因果贡献；未见周期、私有伙伴信息或伙伴适应下的价值。最终 context 回报相等也不意味着两个 Q 函数、参数或所有中间策略相同。没有稳定优势、等价性、负迁移、唯一共享因果效应、严格低秩收益、迁移、普遍 MARL 或 UAV 结论。

## 四、为什么仍选择停止，而不把正曲线转成下一轮自动投入

停止面临的最强反对意见，是**有限预算的学习效率本来就可能值得研究，即使最终水平相同**。一项事先固定的 AUC 仍然是原生回报评价曲线上的性能量，不会因为零终点而变成无效观测。这里的 AUC 是按更新索引对贪婪评价回报作积分摘要，不是实际探索训练期间累计获得的服务 reward；这一量的用途必须说清楚。[B01 卡，§5][b01-card]；[B02 卡，§2][b02-card]

我因此不接受 DM 文本中“唯一干净的本征读法是到达参考值的时间”的绝对表述。更准确的是：现有新实例没有最终可达水平的差异，但同时观察到了固定窗口评价表现差和网格首达差；它们都可以成为以后某个有明确用途的问题的证据。也不接受“换更强表格比较器只能缩小已为零的优势”作为排除该选项的完整科学理由。参考值确实限制这个终点的最高值，却没有抹去短预算、初始化敏感性或样本效率的可检验问题；而更直接的表示能力并不自动保证一个新表格学习器在相同有限预算下更强。[DM 选项，Options 1–3][options]；[B01 卡，§3][b01-card]

仍然停止的理由是：本次没有一个明确的后续方法选择、任务约束或样本稀缺用途，需要先把这个六步公开计划的首达分布估计得更准。原来的跨周期价值参数化能否影响学习已获得正反两面的真实观察；预算探索又表明一个短期优势可以在合法上限处消失。进一步在相同八个 context 上区分神经网络或表格优化，既不会引入新的伙伴信息后果，也不会回答更一般的跨周期信用与适应问题。这样的研究并非不合法，而是目前不足以优先成为这个家族的下一项具体工作。

| 备选 | 能新增的决策信息 | 主导工作与未知项 | 本次选择 |
| --- | --- | --- | --- |
| 结束当前玩具族 | 接受现有有限性能结论与残余不确定性，不再为原问题购买更多精度 | 零新增模型、交互、更新或评价；无需新工程实现 | 选择 |
| 相同模型继续加预算或追加原预算 seed | 更多优化轨迹或短预算变化；不能直接变成 K4 的总体结论 | 既有一对原预算运行的工作为 50,016 联合步、256 更新；更长运行增加 cycles 与评价项 | 已有停止边界不重开；不因便宜追加 |
| 同一玩具上的表格 Q 比较器 | 挑战特定神经 GENERIC 的表示/优化是否造成早期差异 | 新比较器实现及其真实训练、评价；总体工作随臂数、种子和 cycles 增长，实测 wall 与位移尚无 | 不选，不作为关闭前补考，也不声称没有科学价值 |
| 新宿主上的跨周期学习 | 在新的信息、持有行动或后续 credit 后果下比较方法 | 新宿主、策略/信息流、learner 与评价实现；角色数、horizon、renewal 数和训练预算尚未选定，成本未知 | 本次不选；保留下面的科学选题条件 |
| 改为这个玩具上的样本效率/表示研究 | 用明确预算约束重新解释 AUC 或首达分布为何影响一个实际决定 | 单独的前瞻估计量、比较器、种子与预算；不是沿旧数据挑指标即可完成 | 没有识别出独立的决策用途，不作正式 recast |

这个比较遵循 §11.9：不是先寻找精确最大值、完整 headroom 或唯一机制解释，再决定是否允许学习。现有信息足以作停止投入的判断；没有必要用一次“很小的”精确或 beam 搜索来为停止签发证书。放弃的更强主张是总体样本效率、预算交互及机制归因，而不是已经测得的有限曲线差。[证据规范，§§11.8.1–4、11.9][spec]

## 五、被结束的最小家族，与仍然开放的 K4 问题

停止对象按科学内容而不是文件名界定：伙伴为已公开的固定切换程序；焦点为唯一 learner；horizon 为六个计分步；`p∈{2,6}`、`tau∈{2,4}`、`c∈{0,1}` 的八个 context 等权且全在训练和评价内；合法持有服务动作与 `sum 1[a_t=b_t]/6` 不变；通过再换参数化、比较臂、初始化、学习预算或种子，继续追问这个宿主上的同一参数化性能排序。这一研究用途停止，不通过改名或另开目录延续投入。它不禁止以后因具体实现错误而使用保留材料检查受影响的依赖，也不是关于任何预算、任何 learner 都等价的定理。

保留材料包括三个 B01 seed 的全部曲线、初值和负结果，新 B02 的全部 33 点和三个分开的 AUC 窗口、128/512 同实例关系、全部 context 回报、真实更新与位移、技术完成和实际资源记录，以及双方达到原卡参考值这个事实。既有 B02 自动延长停止规则保持；旧 A01 的缺失仍是缺失而不是零，原玩具解析参考不回填它；旧 D6 的 source/countdown 停止边界不动。不同 K4 来源不因共享名称而合并极性。[完整既有决定，§八][previous]；[方向记录的来源与历史边界][direction]；[原三种子结果][b01-zero][b01-two]；[B02 intake][b02-result]

仍然开放的 K4 问题是：当一个共享价值结构必须面对不同持有周期下不同的可用信息、后续状态或联合行动后果时，它相对合理同信息学习器是否改善有限预算下的完整原生任务表现，在哪些条件下反而有代价。当前玩具没有回答这些问题，也没有提供关闭它们的证据。本次不为一个尚未选定的宿主预留实验额度，不作 Portfolio 的生命周期、优先级、容量或融合判断。[方向记录][direction]；[AGENTS，§2][agents]

未来重新提出研究，应有一个本次材料未回答、且结果会改变具体选择的问题，而不是“还可以再跑几秒”。例如，某个实际研究用途确实受训练样本上限约束，使曲线效率而非最终水平成为有决策后果的量；或者已找到一个威胁现有 reward、信息、更新或主测量的具体缺陷，需要先限定其影响。新问题不必先有正结果、稳定性证明或唯一因果解释；但仅想再找一个正 seed、换比较器保住优势、提高原结果精度而说不出其用途，不构成当前重新投入的理由。

### 未来宿主值得写卡时，卡上需要说明什么

本次没有选择一个新宿主，所以不把一个名字加上未定数字包装成可执行 B。下列是以后选题必须讲清的比较含义，不是增加证据规范 §11.4 之外的启动关卡。

首先，应说明一条具体的环境事件→角色→可用信息→合法行动或 credit→真实更新→完整原生后果链。事件应改变某个角色实际知道什么、能何时行动，或当前选择对下一阶段有什么后果；各角色到底固定、隐藏状态、反应式还是会学习，必须区分。只把公开伙伴的两个周期换成三个、把 horizon 延长，不能自动产生伙伴适应或多主体信息问题；隐藏一个固定程序也不等于伙伴在学习。若选这样的更简单宿主，它仍可以是合法的单控制器 B，但必须说明它增加了哪个值得回答的问题，而不是借复杂标签升级主张。

其次，新宿主无需在一个不同 reward 刻度上取得“大于 5/6”的数值。应有理由相信所选择的有限预算及任务后果能区分待选方法，并在真实同信息比较里报告实际回报与剩余误差；不要求在写卡前执行精确上限、参考普查或完整 headroom。旧宿主的 5/6 既不成为新宿主的阈值，也不成为它的 baseline。[B01 卡，§2][b01-card]；[证据规范，§§11.7–11.9][spec]

最后，一张真正选定的新 B 卡应一起固定：实际可实现的处理与最强合理同信息对照；完整 episode 原生回报主测量及评价分布；独立训练实例、初始化和更新方案；环境步、renewal、优化步与评价的完整数量；全调用预算、停止边界，以及有利、相反、无分辨力和主依赖受损时分别改变什么判断。不要故意删去比较器可得的周期或历史信息，也不要把全面调参、低秩证明或伙伴适应证明变成普通 B 的前置义务。若主问题是适应，两个学习角色的更新与相互作用必须真的进入曝光和费用；若主问题只是表示，就不要同时偷偷增加多个伙伴、周期、horizon 和参数化扫描维度。

这些信息为将来选择一个具体有限对象服务；它们不是本次已选实验的待填空格，也不要求额外 Pro 审批、profiling 任务或新基础设施。当前工作就结束在现有玩具族的决定上。

## 六、成本不是拒绝理由；已知工作与未知费用分开

现有完整 B01 六调用合计 150,048 个训练加评价联合步、768 次优化更新，完整调用 wall 之和 17.00 秒、CPU 之和 14.47 秒。B02 每臂有 16,384 训练 episode、98,304 训练联合步、32,768 个真实 renewal 和 512 次更新；33 次各八 episode 的评价另有 1,584 联合步。因此一对 B02 为 199,776 联合步、1,024 次更新，外层完整调用 wall 分别 2.66、2.17 秒，合计 4.83 秒，报告的外层峰值内存最大约 510 MB。[B01 新结果，Actual exposure and technical evidence][b01-two]；[B02 intake，§§1–2、6][b02-result]；[曝光与成本记录][cost]

简单相加所得整个已完成家族的联合步为 `150,048+199,776=349,824`，更新为 `768+1,024=1,792`，调用 wall 之和为 `17.00+4.83=21.83` 秒。这只是工作量记账，不是合并不同科学估计量；wall 之和不是从第一次启动到最后完成的 study elapsed，也不包含未测的全部人工、代理、准备和交接费用。两份 B02 summary 的 CPU 2.236408、2.099161 秒止于 primary readback，不能不加边界说明就和 B01 的完整外层 CPU 记为同一种完整累计量。[原始 resources 字段][factor][generic]；[运行规范，General requirements §§2、6][runtime]

每臂 B02 的主导工作为：初始化，加上 `512×[32 episode×6 步 rollout + 一次 64-row 更新]`，加上 `33×8 episode×6 步评价`，再加必要检查与完整发布。已有的两动作评分属于普通 learner 行动选择，没有额外候选政策树、轨迹分支或反复求解器搜索。原预算只是把 cycles 换成 128、评价点换成九个，并不因此成为必须再运行的便宜对照。[实际两个 run 循环][experiment][budget]；[B02 卡，§4][b02-card]

卡上的 2,700 秒是每臂完整调用 cap，不是预算必须花满的目标；运行规范的一般调查阈值也不自动产生新的计算额度。卡与 CM 保留的四倍完整 wall 情景为 7.04–15.8 秒/臂，是有条件推算而非上界。intake 中约 30 秒/臂的概括不应替换这个原始情景；更不能由实际更短就推导算法加速或节点加速原因。[B02 卡，§4][b02-card]；[CM 记录，Per-arm cost law][cm]；[B02 intake，§6][b02-result]；[运行规范，General requirements §§1–3][runtime]

因此我同意“旧玩具的实测机器成本不是当前限制因素”，但不把它扩大为“任何未实现选项的成本都已知”。成本文件把表格比较器写成秒级、没有实质未知，是作者的前瞻判断，不是这个新比较器的完整调用测量；少一个 Torch 模型不自动确定启动、实现、评价与检查成本。新宿主成本更是未知，不能从本玩具外推。[EXPOSURE_AND_COST 的 prospective_options][cost]

若以后选择普通双臂学习比较，主要乘法项仍应明写为“臂数×独立训练实例×训练循环、每循环 episode 与 horizon、实际 renewal/策略更新工作”，再加“臂数×实例×评价 checkpoint×评价 episode×horizon”。增加可适应角色还会增加真实策略、credit 和更新工作；不能将这些藏在“有限”或“批处理”中。没有选定的 host、角色和预算，就没有可信的具体秒数。通常先去掉不改变决定的扫描维度，而不是加速不必要的策略搜索；无需为了当前停止决定追加一次成本实验。[证据规范，§11.9][spec]；[工程范围规范，§§3–5][engineering]

本咨询新增模型、环境步、优化更新、评价和测试均为零。没有执行所读源码；既有技术测试和数值记录只作为既有证据引用。未来普通研究仍按已有源码、runner、资源准入与一次聚焦验证的含义实施，不继承 VNFC 的具名例外，也不新增工程 scope 设施。

## 七、实际访问与不能声称已经验证的事项

所列 21 个证据路径均通过 GitHub 连接器在上述固定版本成功取回。读取了 B02 卡、结果 intake、两份原始 summary 中的主测量、最终 context、计数、参数和成本字段及相关曲线片段，实际核心与 512 循环；也读取了 B01 卡与两批结果、原完整决定的相关科学章节、接收记录、方向记录、提案、曝光成本与 Issue 快照。较长规范和 AGENTS 按相关条款阅读，尤其完整读取证据规范 §11.8、§11.9。原始 summary 没有在此逐项重新计算全部 33 个 checkpoint 和所有 action cell，也没有参数重放、独立复跑或 cross-host 检验；这些更强验证没有被伪造为已完成。[原接收记录][previous-intake]；[科学核心][experiment][budget]；[证据规范][spec]；[AGENTS][agents]

Issue 5 正文及其两条既有评论确实通过连接器读取，评论复核阶段的时钟观测为 2026 年 9 月 6 日约 07:55（America/Los_Angeles，UTC−07；约 14:55 UTC）。读到的分别是[早先另一轮的交付通知](https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5555953327)和[前次独立完整决定的交付通知](https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5557268673)。前者没有作为本决定的结论来源，也没有沿其链接读取不在清单中的回答。后者的科学原文只使用本次清单内、固定版本的 archive；没有用评论摘要替代它。固定快照记录的读取时间为 2026-09-06 14:34:29 UTC，与这次实际访问分开。[固定 Issue 快照][snapshot]；[既有完整决定][previous]

CM 记录中“尚未执行”的段落属于实施阶段；固定 DIRECTION 尚未追加 B02 结果章节也属于更新时序。不能用它们否定随后已有的两份 complete 运行输出和结果 intake。源字节、测试与执行的不同时间和证明范围分开保留。本次没有独立读取清单之外的运行日志、timing 文件、旧 A01 或旧 D6 原文件；其历史边界依据已读卡、方向与完整前次决定保留，不冒称重新审计。[CM 记录][cm]；[DIRECTION][direction]；[B02 原始输出与 intake][factor][generic][b02-result]

没有形成新学习实验、源码变更、C 冻结或 Portfolio 状态动作。GitHub 协作记录只说明完整回答和单一链接通知的交付方式，不扩大科学或仓库修改范围。[GitHub 协作范围][collaboration]

**最终决定不变：停止这个六步公开固定伙伴玩具族的新增研究投入，零追加观测；完整保留小幅正负性能、正曲线与参考值相等的事实。K4 仍是未被这组结果否定的研究问题，但下一宿主或 recast 没有在本次被选定，也没有自动获得实验预算。**

[b01-card]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md
[b01-zero]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_RESULT_EVIDENCE_20260905.md
[b01-two]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SEED12_RESULT_EVIDENCE_20260905.md
[b02-card]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_SCIENCE_CARD_20260906.md
[b02-result]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_RESULT_INTAKE_20260906.md
[factor]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/results/k4_b02_budget512_seed3_20260906/factor/summary.json
[generic]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/results/k4_b02_budget512_seed3_20260906/generic/summary.json
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_CM_RECORD_20260906.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/pro_packets/20260906_post_b02_convergence/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/pro_packets/20260906_post_b02_convergence/EXPOSURE_AND_COST.json
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence_r02/archive/RESPONSE.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/VSPC1_K4_THREE_SEED_CONVERGENCE_R02_INTAKE_20260906.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/DIRECTION.md
[experiment]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/experiments/candidates/vsp_c1/k4_factor_value_b01/experiment.py
[budget]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/experiments/candidates/vsp_c1/k4_factor_value_b01/budget512.py
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/candidates/vsp_c1/pro_packets/20260906_post_b02_convergence/ISSUE_SNAPSHOT.json
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/AGENTS.md
[collaboration]: https://github.com/CartmanFatass/My-paper-code/blob/b7efcb9ce7e5c378f0442af79d5b99915eb11eca/docs/project/GITHUB_RESEARCH_COLLABORATION.md
