**方向层决定：继续现有首次合法应用时的 RETAIN/COPY/SHADOW 探索议程，当前联合预测包支线继续保持结束；本轮只选择一个新的、有限的 CONTROL 学习率对照 B/EXPLORE：继承 CONTROL 的 AdamW 学习率 3e-4 对 3e-5，使用一个新的配对训练种子 89，两臂各十六次更新。** 两臂都保留修正后的普通续约边界、raw-logit 服务接口、原 mean-MSE/PPO/其余辅助目标和正常 Welford 更新。不是重新开启 NLL 加 sigmoid 包，不冻结归一化，不同时减少 epoch，也不停车或 RECAST 整个 DISH。

理由是：见证已经把先前未测的前提变成一个有界事实——seed 73 的最终 CONTROL 在同条件完整评估上，比其零更新完整控制器少 245.75 平均服务 tick。现在值得直接问“较小的优化器步长能否在同样交互和更新次数下改善原生服务”，而不是继续解释一个未测的初始化基线。**这个事实提供改动的动机，但没有诊断学习率过大；选择的是一个性能假设，不是已定位原因的修复。** 当前证据不支持把归一化、参数移动或 PPO 中任何一项说成损失的唯一来源。[见证 intake §§2–3][w-intake]；[原始 summary：witness、initialization][w-summary]；[证据规范 §§5.2、11.8–11.9][method]。

本次新 B 内另包含同一新种子的一个 raw-interface 零更新参考，每个条件仅评估一次，共四个 episode，用来区分“胜过已退化 CONTROL”与“保留或提高自身初始化服务”。它不是另一个先行 A，也不决定是否准许训练。以下给出可写卡的完整比较、读法和支出边界。本决定不接受源码、不启动实验、不改 Portfolio。

## 一、见证确立什么，以及不能顺带推出什么

### 同条件初末差值已经测到，但只是完整控制器的条件性变化

| 开发条件，均为 speed 4 / slot 0 / block 0 | 零更新 CONTROL 视图 | CONTROL update 16 | 初末差值 | 零更新 PACKAGE 视图 | PACKAGE update 16 | 初末差值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 467 | 452 | −15 | 467 | 92 | −375 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 478 | 458 | −20 | 478 | 222 | −256 |
| TERRAIN_RELAY_MASK / K8 | 942 | 449 | −493 | 942 | 129 | −813 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 938 | 483 | −455 | 938 | 311 | −627 |
| **均值** | **706.25** | **460.5** | **−245.75** | **706.25** | **188.5** | **−517.75** |

零更新八行是新测量；最终八行是从已接受 B03 摘要按坐标复用，不是再次运行最终检查点。新测量全部完成 1,200 tick，没有七类硬事件或合法换主，参数范数在每个 episode 前后均为 38.24996300787587。原卡第一种模式 `D_C ≤ −24` 适用，包也下降；这是一个训练种子上的共同条件性初末损失，不是两次独立训练重复。[见证 summary：evaluation_rows、reused_rows、witness][w-summary]；[见证卡 §§1、4][w-card]。

零更新状态是从 B03 已记录 master 经现有初始化器生成一次，明确标为 `reconstructed_from_master`；没有保存的原始零更新快照。初始化 helper 构造了 model 和未步进的 optimizer，实际有八次 policy construction / checkpoint load。Welford 三种状态起始 count 均为零；其空状态变换使用 variance 1、不作均值中心化并保留 ±10 截断。最终控制器则携带训练后的参数与归一化状态。因此对比不是“仅参数更新的净效应”，更不是 isolated PPO effect。范数吻合是核对量，不独立证明整个状态身份。[见证卡 §2][w-card]；[CM record“Initializer facts”“Fresh recurrent state”][w-cm]；[见证 summary：initialization、zero_training][w-summary]。

CONTROL 的大幅损失集中在两个 TERRAIN 条件；两个 TARGET 条件只有 −15 和 −20。这个异质性应原样展示，不能把均值写成每行都大幅下降，也不能只选 TERRAIN 作为下一项“已证明最有希望”的评价总体。四行不足以分离条件效应、几何/相位差异与训练随机性。[见证 intake §2][w-intake]。

### 相同接口视图的结果，不是协议未行动或接口等价的证明

两种零更新视图在已发布的服务、能量、终止事实等行级结果上相同，DM 关于视图会实质不同的预测确实错误。但是本次 summary 没有逐 tick 的 prepare/commit 提案计数；**零 invalid_commit 和零合法换主，并不推出从未提出 prepare/commit，亦不推出两个视图的内部动作历史完全相同。** intake 关于“没有事件，所以接口无处作用”的解释只能留作推断，不能作为已测原因。本轮不为这个解释另买一次复现，也不据此认为后续学习时 raw 与 sigmoid 可互换。[见证 intake §§2、4][w-intake]；[见证 summary：evaluation_rows 中实际字段][w-summary]。

### 原不利结果和真实训练事实仍然可见

B03 的包减 CONTROL 主差分仍为 **−272.0**；包的 TERRAIN/K4_TO_K12 行仍保留 invalid_commit 17、separation_breach 1，以及在范围末端记录的 separation 14.71157529146157。低 4–7% 的能量不抵消服务损失。CONTROL 的一次普通合法换主在**训练**汇总中，不能被“八个评估 episode 无合法换主”抹掉。它也没有完成 RETAIN/COPY/SHADOW 的配对来源干预。[B03 两个 summary：training_legal_transfers、training_hard_events、evaluation_rows、paired_primary][control][package]。

两臂均进行了真实训练。CONTROL/包的 L2 参数位移分别为 8.605231896111574 / 7.5142387939077615；包的每更新平均 loss 和平均裁剪前 gradient norm 峰值分别为 6,541,776.3828125 和 1,755,882.8818359375，CONTROL 的后者峰值为 875.392335653305。有限大梯度不是“未裁剪”的证据，也不能当作非有限故障隔离。训练窗口曲线有 reset/episode 阶段变化，CONTROL update 11 的服务 4,093 还高于 update 1 的 4,016；旧的单调退化或“首个更新完全相同”表述仍按前次裁决收窄。本次完整初始化评估补足的是初末回报事实，没有倒过来证明那些旧表述的全部原因。[B03 curves、parameter_movement][control][package]；[前次完整裁决 §§一、二][previous]。

**继续的最强支持**是：CONTROL 自身也出现完整评估能力损失，已经不必围绕结束的预测包寻找后继；一个保留交互量、损失和归一化规则的标量步长对照能直接改变下一笔性能投入。**最强反证和不确定性**是：损失可能主要来自正常更新的 Welford、共享表示/循环动力学、训练与评估分布差异或该种子的偶然性；把学习率降十倍不保证改善这些因素，还可能妨碍必要学习。没有任何观察把 3e-5 认证为正确值或最优值。

## 二、为什么选低学习率 B，而不是 DM 首选的冻结 Welford

选择 DM 选项 1 中的 **3e-5 对 3e-4**，但用新的配对种子，并在同一个 B 中加入该新种子的四行零更新参考。选择理由不是“传统做法必然有效”，而是它在保留十六次更新、全部 minibatch、原目标及正常归一化规则时，只改变优化器的指定学习率，直接检验较弱更新是否具有原生性能价值。CONTROL 已有的整体初末损失足以支持这一项探索，不要求先定位 overshoot。[选项说明 option 1][options]；[证据规范 §§11.8.2、11.9][method]。

冻结 Welford 可以是另一个合法 B，但 DM 所说“分离一个成分”必须区分**干预了哪个部件**与**识别历史损失的哪个原因**。从训练开始冻结，会改变后续有效输入、饱和/截断情况、策略动作、采样数据、损失梯度和循环共适应；即使 optimizer 规则不变，也不是在其他实现状态不变下抽走一个历史通道。它不是必做的更科学前置诊断。本轮既不选择从零开始冻结，也不选择把最终权重与初始 Welford 交叉拼接的检查点手术；后者还是另一个未购买的对象。[见证卡 §2 的初末状态差异][w-card]；[选项说明“Unknowns”“Options”][options]。

减少到一个 epoch 同样可以提出独立性能问题，但会同时减少 replay/backward/优化器曝光。计数须准确：四 epoch ×八 minibatch 是每次更新 32 步、十六更新共 512 步；一个 epoch ×八是每次更新八步、总计 128 步。只改处理臂时，对照仍为 512，不能把两臂都写成 128。本次为保留更新次数而不选择它。沿用已有 clipping 也不是新处理，不另加一项裁剪改动。[B03 configuration、curves][control]；[选项与成本记录中的候选计数][options][cost]。

不先购买“再一个 CONTROL 种子是否也下降”的独立对象：所选 B 的新 CONTROL 和自身零更新参考已经能报告这个事实，同时产生具名干预的配对比较；只有后一项不感兴趣时，单臂复现才更合适。单一 raw CONTROL 的零更新参考只需要四行，不需要两个接口的八行。B02 历史 witness、held-only、全支持 census、上界搜索和再一次相同视图解释均不解决当前低学习率的性能选择，故不加入。当前有一项具名有限对象，不据缺少唯一原因或 tuned headroom 把整个方向停车。[证据规范 §§11.8–11.9][method]。

## 三、唯一新对象的科学合同

### 类别、边界与比较臂

新对象可记为 **DISH-CONTROL-LOW-LR-B04，B/EXPLORE**。问题是：在修正普通续约接口和既定 A03 宿主上，同样十六更新曝光的继承 CONTROL 学习器，采用 3e-5 而不是 3e-4，是否提高最终完整 episode 的原生服务；改善是仅减轻相对对照的损失，还是也保留/提高本次初始化服务？

| 项目 | CONTROL | LOW_LR |
| --- | --- | --- |
| 优化器 | 继承 AdamW，恒定学习率 3e-4 | 同一 AdamW，其所有原参数组恒定学习率 3e-5 |
| 目标及接口 | 原 mean-MSE、raw-logit 服务接口、PPO 与原其余辅助目标 | 与 CONTROL 相同，不启用联合 NLL/sigmoid 包 |
| 归一化与循环状态 | 按原学习路径正常更新/传递 | 同一规则；不冻结、不借用另臂统计、不在评估拟合 |
| 训练曝光 | 16 更新；32 lane ×128 tick/更新；4 epoch ×8 minibatch | 相同 |
| 最终选择 | 只使用 update 16 的完整检查点 | 相同 |

其余 optimizer 系数、weight decay 系数、已有 gradient clipping、损失权重、动作采样法、PPO/replay、label/mask 法则与终止规则保持。AdamW 的学习率也影响该优化器规则中的参数衰减量；不补偿或再调别的系数。因此这是**学习率超参数的总效果**，不能承诺实际参数位移恰好变成十分之一，也不称纯 actor 步长效应。

实际 CONTROL 是最直接、已有执行证据的同信息学习对照；零更新参考防止只挑一个低服务最终控制器作比较而隐去绝对损失。两者都不是经过调优的最优基线或 oracle。当前没有同宿主 tuned upper-versus-generic headroom；706.25 不是上界，也不是可以跨种子搬用的基线。[B03 CONTROL configuration][control]；[见证读法][w-card]；[证据规范 §11.7][method]。

### 新种子、初始化和信息配对

选择**一个新配对训练种子 89**，不重用 seed 73，也不调用 seed 61。为这项新对象明确记录 master 的生成法：SHA256 对 ASCII 字符串 `DISH-CONTROL-LOW-LR-B04/seed/89` 的输出；这是事前指定的新对象随机流，不在本次咨询中生成或试跑。两臂使用同一 master-addressed STRUCTURED 初始参数、同一初始空 Welford 和相同的语义坐标外生随机法则；各自后续 optimizer、循环状态和 Welford 状态独立演化，不在两臂间拷贝学习结果。

选择新种子的目的，是避免仅为已经看见大幅下降的 seed 73 调参数，并增加一个新的训练随机实例；**改动的动机仍然由旧结果启发，不是独立确认**。两臂共享一个新配对根仍只形成一个训练重复，四行条件不是四个种子，不能用逐行 bootstrap 伪造训练种子总体区间。复用 seed 73 在 B 中并非禁止，但本轮不选择它。[证据规范 §§5.2、11.8.3][method]。

同一新初始化用继承的 raw CONTROL 接口评估四行，形成 `J_0,r`。它是带正常运动/协议输出的零更新策略，不是 held-only；学习率在无 optimizer.step 的推理中不构成第二种接口，所以无需重复一个 LOW_LR 初始视图。初始化 helper 可能构造未步进的 optimizer，按实际构造与加载次数记录。零更新参考带原始 count-0 Welford、每行新鲜循环状态，不能加载最终统计或评估时重拟合。可以保存本次初始状态，避免后来反推；不因此建 resume、registry 或身份 guard。

这四行属于同一 B 的附属测量，**不是训练前必须出现高回报的准入条件**。不能根据其表现跳过训练、更换 seed、选择新的条件或停止某一臂。seed 73 的 706.25 只列为历史参考，不参与新种子的 `J_16−J_0` 计算。

### 宿主、条件与事件到后果路径

两臂及零更新参考均采用不变的 `GROUND-TERMINAL-LINEAR-CLEARANCE-A03` 和修正普通续约边界。native float64、policy FP32、单 Torch 线程。保持 native ABI、奖励定义、服务标签法则、法定阈值、原始因果信息、动作空间、命令投影、实体/owner 身份和协议时序。采用继承 32-lane 训练分布；不把四个开发评价条件另改为训练分布。[见证卡 §§2–3][w-card]；[B03 configuration][control]。

最终评估仍为 TARGET_VISUAL_MASK / TERRAIN_RELAY_MASK × K8 / K4_TO_K12，speed 4、slot 0、block 0。为 seed 89 按继承坐标法则得到并记录四个完整 reset，在两臂与初始参考间共用各行 reset/外生随机。**不把 seed 73 的相位 4、2、1、1 或它的实测回报偷偷当成新种子的输入。** 每行从新鲜 native/循环状态开始，普通确定性评估；不得从另一行/另一臂借状态。

因果与学习路径为：既定路线及退化事件 → 两物理实体的角色相关因果观测和实际消息 → active/shadow 循环表示 → 当前许可下的运动、prepare/commit 与预测输出 → 原生投影、合法性处理和服务 → 真实 transition、原辅助 labels 与 recurrent PPO replay → AdamW 按所选学习率更新 → update-16 完整控制器的普通原生服务。

private passive-label 克隆中的强制 promotion 仍只是继承监督标签的生成工作，不能计为普通合法换主或来源价值；不向 actor 增加克隆未来信息。匹配的是标签/采样规则和曝光，不是强制两臂得到相同 realized labels、轨迹或 eligible 数。服务可以全来自 incumbent；没有 source fork 时，不产生 COPY–RETAIN 或 SHADOW–COPY 估计。把当前家族写成已经证明“学习运动在 handover 中提高服务”超过证据；本轮只是该议程内的一项普通控制性能探索。[前次完整裁决 §§一、三、六][previous]；[DIRECTION 的既有家族和后继边界][direction]。

## 四、主测量、绝对参考和前瞻读法

各行 `J_a,r` 是固定 1,200-tick 范围内原生二元 service 的和。native 提前终止则停止 stepping，未执行余段服务计零，并报告实际完成 tick、原因和事件；不用幸存 live tick 作分母。换主后继续普通评估，不能在 first-valid 处早停。所有四行进入主量，不按触发、符号或 regime 筛选。

主量为 `Delta_LR = (1/4) Σ_r (J_LOW_LR,16,r − J_CONTROL,16,r)`。附属绝对读法为 `D_CONTROL,new = (1/4) Σ_r (J_CONTROL,16,r − J_0,r)` 与 `D_LOW_LR,new = (1/4) Σ_r (J_LOW_LR,16,r − J_0,r)`。报告初始、两最终均值与所有逐行差值，明确当前新测数据与历史 seed-73 表的来源。以同一个初始参考相减不会产生更多独立样本。

**本对象的有用效果尺度为 +24 平均服务 tick**，即完整范围的 0.02、2.4 秒服务；对初末变化用同量纲 ±24 作描述。它适合区分几 tick 的边缘变化与值得追问的控制差异，不是 numerical tolerance，不要求每行超过它，不是仓库普遍阈值或 B 的启动门槛。[证据规范 §11.7][method]。

伴随报告每行能量、七类 hard events、完成/未执行 tick、终止原因、普通合法换主和换主前/后服务；后者仅是时间分解，未核对 packet 来源时不称 promoted-owner packet service。学习曲线保留每次更新的服务、loss/gradient 的实际统计口径、有限性、eligible/next-mask、optimizer 步及参数位移；训练的事件和换主总数与评估分别列出。不得把更低 training loss 或更低能量当成原生服务收益。

| 观察模式 | 读法与会改变的下一项建议 |
| --- | --- |
| `Delta_LR ≥ +24`，且伴随结果没有使其成为不利权衡 | 在这个新训练实例和四个条件上，低学习率有原生增量信号；可据完整记录考虑一至两个后续独立种子的同一比较，不要求每行或每个后续种子都正。此次不预购那些种子。 |
| 有上述相对信号，但 `D_LOW_LR,new ≤ −24` | 只称相对 CONTROL 的损失减轻，不能称恢复或超过自身初始化。仍可能有后续决策价值，但零更新参考的优势必须同列；不能靠相对胜出隐藏绝对退化。 |
| 有相对信号，且 LOW_LR 的初末差处于带内或 ≥+24 | 分别称本例近于初始表现，或本例同时存在正的初末变化；前者不是等价，后者不是一般“稳定学习”或原因定位。 |
| 主差分带内，或行间混合而没有清楚的有用平均增量 | 未建立本曝光下有用的 LR 优势；保留条件差异，不自动再降 LR、延长训练、找更好 checkpoint 或补 seed 直到同号。不宣称等价。 |
| LOW_LR 有明显服务损失、增加硬事件或不利能量/服务权衡 | 不利事实优先于任何 proxy 改善，不扩展这一 LOW_LR 配置；结束的是这项具体试验的扩展，不由单 seed 关闭所有 CONTROL 学习法或来源机制。 |
| 无评估合法换主 | 原生包外的 CONTROL 性能比较仍成立，明确 incumbent-only；来源问题继续未估计，不能借训练中的一次换主替代最终来源干预。 |
| 一个输入、训练链或主测量未完成/受损 | 保留独立可信的实际行和计数，但不给完整配对结论；指出受损依赖，不伪造未运行 episode，不把历史 B03 一并隔离。 |

这些是带伴随成本的读法，不是“每个单元格必须改善”的筛选律。若新 CONTROL 不再低于其初始化，只说明旧共同初末损失没有在这个新实例按相同描述重复；处理的配对结果仍可读，旧 witness 也不被推翻。没有结果自动授权另一个 LR、冻结 Welford、重开预测包或改变 Portfolio。

## 五、完整工作量、有限支出与停止边界

本对象的规模由普通交互、recurrent PPO 与监督标签决定，不包含政策搜索、联合动作穷举或未来轨迹树。

| 工作 | 本次选择 |
| --- | --- |
| 新独立训练重复 | 一个配对 seed 89；两个 learner run，不是两个独立 seed |
| 普通训练 | 每臂 32×128×16 = 65,536 transitions；合计 131,072 |
| 优化器工作 | 每臂 16×4×8 = 512 步；合计 1,024；保留全部 recurrent replay/backward |
| 新初始参考 | 一个 raw-interface 视图 ×四行，至多 4,800 native tick，零 backward/optimizer/label 调用 |
| 最终评估 | 两臂 ×四行 ×至多 1,200 tick，至多 9,600；与初始合计十二 episode / 14,400 tick |
| 检查点/配置选择 | 每臂只有 update 16；没有最优 checkpoint、LR 网格、旧 seed 或旧最终控制器旁测 |

对每个训练臂，令 `N=65,536`、`E` 为实际 service-label eligible 数、`H` 为实际克隆后果 stepping 数，保留原工作律：

`W_native,train = N + N + 2E + H = 2N + 2E + H`，其中 `0 ≤ H ≤ 20E`，故每臂至多 `24N = 1,572,864` 次原生训练 step 调用。

这不是原生工作只有 65,536 步，也不是 24 倍 wall 预测。额外 physics 读出、policy/critic forward、PPO replay/backward、optimizer、初始化/构建/检查和发布还需计入完整成本。E 会随新种子和学习率改变，不能沿用 B03 的 18,775 或 7,972 当成新值。保留现有 E 计数；若 H 仍无直接接口读数，照实记未测和 `H≤20E`，不为性能主张扩建 native ABI 或全轨迹。[B03 actual_exposure、planned_cost][control][package]；[runtime General requirements §§2–3][runtime]。

**新支出上限：每臂完整收费不超过 1,800 秒，两臂合计不超过 3,600 秒。** 它们是本轮新选择的上限，不继承 B02/B03 或 witness 的余额。共同初始化、四行零更新参考、必要聚焦检查、实际支付的 build/load、共同归约/最终发布都是同一项工作的一部分，不能另外获得 120 秒或“加构建”额度。

计账可沿用既有方式：真正共享的工作记一次为 S，事前各分配 S/2；两臂分别记录自己的完整 wall 和共享份额，均须在 1,800 秒内，合计含 S 不超过 3,600 秒。S 包含最后才完成的共享输出工作，不能只扣开头 smoke 而遗漏末尾；在执行计划中给发布留出余额，不能把它移出计时。不同分段不重置 cap；study elapsed、调用 wall 之和、可得 CPU 累计彼此分开，未测开销写未测。这里不新增资源性能评估或 CPU 上限，也不要求新增 profiler。[runtime §§2、6–8][runtime]。

B03 的 211.04 / 196.18 秒整臂、4.94 秒共享检查、412.16 秒成功链收费可以作已观察工作类型的参考；但新对象是两个 CONTROL 型臂加一个新初始参考，不是原来的 CONTROL/PACKAGE 对。witness 的 11.25 秒正式 wall 是既有八个零更新 episode 的那次完整运行，不是可直接除八的冷启动单位价格。因此不把 DM 的约 410 秒、211+16 秒当成已建立的新对象投影，更不把学习率降十倍写成时间降十倍；新 E、计算耗时、缓存和节点负载未知。**不为这个未知另买强制校准实验。** CM 用实际选定路径和已有计时如实列成本范围，若已知完整方案超出 cap，返回该具体范围问题，不静默删标签、少训练或扩大额度。[成本记录 measured / prospective options][cost]。

完整任务在两臂十六更新、规定十二行或合法终止及发布完成后结束；在预算耗尽、实际非有限训练状态或威胁主测量的失败时停止，并保留实际曝光。没有 efficacy 早停、临时早期 checkpoint、结果驱动 seed/行替换、自动续训或科学重试。启动前失败的记录、花费和零曝光仍保留，技术失败不创造新的研究预算或结果极性；相同已授权操作若接受状态不明，先检查状态再处理，不盲目重复。[AGENTS §§6–8][agents]。

沿用 remote-first 的 `wsl_4070`、已提交并推送的精确 source、现有 detached supervision，实际执行节点每次 invocation 前新鲜通过 physical/effective available memory 均至少 4 GiB。报告完整 wall 和有范围说明的 peak RSS。普通 2,000 新非测试行、600 runner 行及测试预算适用，无 A05 例外、scheduler、registry、validator、额外 guard 或跨平台位级合同；30% orchestration 仍只是审查信号。[scope §§3–5][scope]；[AGENTS §§5、7–8][agents]。

## 六、验收只保护本次真实比较，不延长诊断链

需要的针对性检查是：所选 LR 实际作用于各次 update 的全部原 optimizer 参数组，checkpoint/state 恢复或 trainer 重建没有把 LOW_LR 重新设成 3e-4；其余目标、mask、clipping、归一化和接口没有夹带变化。再检查同一新初始化/同一 raw 参考、reset 配对、固定范围主归约和初末差值的来源。这些是新比较的直接依赖，可合在一次针对改动与主输出的聚焦覆盖中；未改路径的 B03、续约修正与 witness 覆盖直接复用。[证据规范 §11.8.6][method]。

当前清单没有训练实现源码；本答复依据实际配置、卡片和 CM 记录选择科学参数，**不宣称已经独立验证当前程序有无需修改的 LR 开关或完成了新 LR 的端到端验收**。需要的参数传递在本次有界研究实现中完成；若碰到使这项比较无法按既定含义运行的真实依赖，返回那个具体缺口，不以此启动完整历史重构。无需重测 seed-61 的训练滞后、复跑 A01/A02 窗口、整个 r06 套件、所有 schedule、历史 fragment、所有梯度连接或原八个最终 B03 行。[witness CM record 的实际复用与未验证边界][w-cm]；[证据规范 §§11.8.7、11.9][method]。

保留的每项负担都有当前用途：普通交互和原 labels 定义算法；PPO replay/backward/steps 实现所选学习；最终八行测 LR 增量；共享初始四行限定绝对学习读法；曲线、位移和事件防止把未学、未完成或带伤害的 proxy 当收益；一次聚焦检查保护真实处理和主量；wall/RSS 与 admission 支持完整支出和运行事实。**不保留**完整机制定位、历史 replay、精确上界/census、调优 oracle、完整逐 tick 数组和发布历史重放；相应放弃独特机制、最优、全路径恒等和来源归因等更强主张。缺少这些不是 B 门槛。[method §§11.4、11.8–11.9][method]。

## 七、旧结果、成本和方向边界

本次 witness 的 r2 成功链收费是 **16.231 秒**，包含 4.981 秒聚焦检查与 11.25 秒正式外层 wall；r1 的失败聚焦检查另有 **5.816 秒**。不能把 r2 数字称为所有尝试的总花费，也不能把 r1 没有科研曝光写成零成本。正式 summary 的 prepublication wall 10.953281042980962、CPU 10.948027、self RSS 473,096,192 bytes 和独立 child peak 各有自己的范围；self 与 child 峰值不相加当同时内存，scratch 未测不抹掉原生结果。[见证 intake §1][w-intake]；[cost.measured][cost]。

B03 的增量劣势与两臂相对初始化的绝对损失可以同时成立；见证没有重新读取 B03 的分支，也没有把来源机制判负。B02 的 lagged-interface inside-MEI、B01 的触发不足、A03–A05 的 bounded facts、普通续约 A01/A02 的观测范围与历史训练侧推断继续保留。不因本轮新 B 改变旧数字、把时序解释成已识别的 B02 成因、把两对包实验当独立同算法复现，或重新开启闭合 R02。[前次完整裁决 §§一、二、六][previous]；[post-B03 intake §§2–4][previous-intake]；[DIRECTION][direction]。

当前联合预测包支线保持结束，不通过只改名、包系数微调或挑一个好 seed 恢复。重新提出包研究仍需要有独立具体理由的新科学变化、同信息原生比较和有限完整工作，并保留原服务损失与硬事件；不是必须先证明唯一原因。所选 CONTROL 学习率 B 不自动生成第二个配置或第二项对象。

现有 source-selection 科学问题仍是：在普通合法 first-application 机会发生后，COPY–RETAIN 与 SHADOW–COPY 分别有什么恢复价值。一个普通服务增量即使全来自 incumbent 也可以有 B 层性能意义，但不能替代该干预；COPY/RETAIN 足够、deadline replay 包含和 checkpoint/partner 共适应仍是活的替代解释。未选择 Portfolio 生命周期、优先级、容量、融合、注册或 recast 操作；其他 N3 成分不继承本结果极性。`PORTFOLIO.md` 不在当前允许读取列表中，没有读取或推测其 recast 计数；本轮不作 RECAST。[AGENTS §2][agents]；[DIRECTION 的 family 与关闭边界][direction]。

## 八、实际证据访问与未验证范围

科学证据全部经连接的 GitHub 在 **`98d9defd8bbad23f20d6d949db0c40d35e343399`** 读取。下表 C/ 指 `docs/research/candidates/degraded_incumbent_shadow_handover/`，P/ 指 C/ 下 `pro_packets/20260906_post_witness_convergence/`。没有用旧对话附件或其他 ref 补全当前材料。

| 实际读取路径 | 范围 |
| --- | --- |
| [C/DISH_INIT_WITNESS_A01_RESULT_INTAKE_20260906.md][w-intake] | 完整 |
| [C/init_witness_a01_20260906/witness/summary.json][w-summary] | 完整，含八个新行、八个复用行、全部 reset、初始化和曝光 |
| [C/DISH_INIT_WITNESS_A01_SCIENCE_CARD_20260906.md][w-card] | 完整 |
| [C/DISH_INIT_WITNESS_A01_CM_RECORD_20260906.md][w-cm] | 完整；实施前未验证项与后来真实结果分开 |
| [C/DISH_POST_B03_CONVERGENCE_INTAKE_20260906.md][previous-intake] | 完整，重叠读取补齐尾部 |
| [C/pro_packets/20260906_post_b03_convergence/archive/RESPONSE.md][previous] | 完整，含读法、否定选项、成本和引用尾部 |
| [C/DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md][b03-intake] | 完整；旧过强解释按先前限定与当前新事实分别处理 |
| [C/b03_forecast_package_20260906/control/summary.json][control] | 完整，含十六更新、事件、全部评估行及成本 |
| [C/b03_forecast_package_20260906/forecast_package/summary.json][package] | 完整，含配对主量和全部行 |
| [P/EVIDENCE_AND_OPTIONS.md][options] | 完整，视作建议而非已选方案 |
| [P/EXPOSURE_AND_COST.json][cost] | 完整；未来估计与已测数分开 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 完整固定快照 |
| [C/DIRECTION.md][direction] | 行 210–310、350 至末尾；所见末段停在 witness 选择，实际 witness 结果以上述主源为准 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 行 35–126、300 至末尾，含完整 §§11.1、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 行 1–112，普通 §§1–5；不采用历史专用附款 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][runtime] | General requirements §§1–8，重叠补齐；不采用 VNFC 专用附款 |
| [AGENTS.md][agents] | 行 1–370，正文与 Appendix A 的已返回部分；未读其余运行时附录，不据运行时名字取得权限 |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md][delivery] | 完整 |

所有列出路径均可访问；表中限定范围的文件不宣称全文阅读。没有读取当前清单外的实现代码、B02 原始曲线、模型文件或 Portfolio。当前资料不能验证新 LOW_LR 实现、未来 seed-89 初始回报、其 E/H、完成时长或效果；这些是已选新对象的待观察量，不是一个已发生的实验。

固定 Issue 快照的时刻为 **2026-09-06 21:08:42 UTC**。本轮在 **21:22:35 UTC 前**已通过连接读取 [Issue 4][issue] 正文及四条既有交付评论：[post-B02][comment-b02]、[post-A01][comment-a01]、[post-A02][comment-a02]、[post-B03][comment-b03]；交付前再次检查目标、分支和评论。它们不是本轮结果，也不代替上述固定科学证据。

本次咨询没有模型加载、native 状态/transition、backward、optimizer.step、测试或实验；只读取证据并交付本答复及其链接评论。科学决定限于本轮这一项新 B，实施、运行与后续结果仍未发生。

[w-intake]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_INIT_WITNESS_A01_RESULT_INTAKE_20260906.md
[w-summary]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/init_witness_a01_20260906/witness/summary.json
[w-card]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_INIT_WITNESS_A01_SCIENCE_CARD_20260906.md
[w-cm]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_INIT_WITNESS_A01_CM_RECORD_20260906.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_B03_CONVERGENCE_INTAKE_20260906.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b03_convergence/archive/RESPONSE.md
[b03-intake]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md
[control]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/b03_forecast_package_20260906/control/summary.json
[package]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/b03_forecast_package_20260906/forecast_package/summary.json
[options]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_witness_convergence/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_witness_convergence/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_witness_convergence/ISSUE_SNAPSHOT.json
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[method]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/AGENTS.md
[delivery]: https://github.com/CartmanFatass/My-paper-code/blob/98d9defd8bbad23f20d6d949db0c40d35e343399/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[comment-b02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
[comment-a01]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5558729980
[comment-a02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5560502547
[comment-b03]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5561089362
