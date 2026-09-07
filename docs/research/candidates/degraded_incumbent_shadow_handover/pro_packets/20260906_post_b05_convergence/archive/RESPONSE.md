**方向层决定：继续现有首次普通合法应用时的 RETAIN/COPY/SHADOW 探索议程；本轮只选择一个新的 DISH-SAMPLED-EXECUTION-B06（B/EXPLORE）。** 用新种子 113 训练一次既有 LOW_LR（AdamW 3e-5）学习器，完成十六次更新后，以同一个最终检查点比较普通模态执行与普通随机抽样执行。每个开发条件保留一个模态 episode 和两个事前编号的抽样 episode；同一对象内另有四行零更新 raw 接口的模态参考。整项新支出上限为 **1,800 秒**，不是每个执行模式各 1,800 秒。不先购买路径 A，不购买第三个学习率配对，不重开联合预测包，也不作整个 DISH 的 PARK、CLOSE 或 RECAST。

理由是：B04/B05 已提供两个有限的正平均学习率比较，足以把 LOW_LR 留作开发候选，但没有回答它应如何执行。现有源码明确区分训练时的高斯运动／Bernoulli 意图抽样与最终评估的均值／阈值动作；同一最终检查点的两个执行法则可以直接比较完整原生服务，且不需要重复训练一个相同的模态对照。**这是有代码依据的性能问题，不是已经查明“模态执行阻止换主”的修复。** 选择新训练实例让本次执行法则比较不只依附于已经看过结果的 seed101；它仍是 outcome-informed 探索，不是独立确认、部署安全背书或来源效果试验。[B05 intake §§2–4][intake]；[evaluate_episode][eval]；[step_rows、collect_update][policy]。

## 一、接受 B05 的有限信号，同时保留全部矛盾

### 原始十二行与既有读法

| 开发条件，均为 speed4／slot0／block0 | 零更新参考 | CONTROL | LOW_LR | LOW_LR−CONTROL | CONTROL−参考 | LOW_LR−参考 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK／K8 | 96 | 178 | 591 | +413 | +82 | +495 |
| TARGET_VISUAL_MASK／K4_TO_K12 | 330 | 491 | 214 | −277 | +161 | −116 |
| TERRAIN_RELAY_MASK／K8 | 323 | 153 | 695 | +542 | −170 | +372 |
| TERRAIN_RELAY_MASK／K4_TO_K12 | 440 | 301 | 568 | +267 | −139 | +128 |
| **均值** | **297.25** | **280.75** | **517.0** | **+236.25** | **−16.5** | **+219.75** |

这些是 E0 的 primary、paired_rows 与十二个 evaluation_rows 共同支持的读数，不是本次新运行。全部十二行实际完成 1,200 tick，未执行余段均为零。B05 的正增量不依赖本轮出现提前终止；但它不分解、也不解释 B04 那条 CONTROL 在 tick684 终止的历史差异。[TECHNICAL_ACCEPTANCE.json：primary、paired_rows、evaluation_rows、counts][e0]。

保留卡片和 intake 的适用读法：第 1 行的有限开发信号、第 3 行的 LOW_LR 正初末变化、第 5 行中**提前分离终止没有重复这一部分**、第 6 行的 incumbent-only。CONTROL 仍比自己的参考低 16.5，因此第 5 行“已不低于初始化”的另一部分并不成立；只是较早的大幅平均损失没有在本例超过 24 的描述尺度。不能把带内叫等价，或把两个条件的 CONTROL 初末损失隐藏在均值里。[B05 card §5][card]；[intake §3][intake]。

原生代价不能省略。按上表行序，LOW_LR 的 invalid_commit 是 **108／0／101／0，共 209**，CONTROL 四行均为零；参考为 **0／26／31／0**。其余六类评估硬事件均为零，不构成安全或零事件率结论。LOW_LR 能量分别约 288,085.76／275,908.33／287,672.07／225,337.75，CONTROL 为 289,103.31／285,512.97／288,205.51／287,053.58：四个等时长比较均较低，但 LOW_LR 两个 K8 条件的能量仍高于各自初始化。TARGET／K4_TO_K12 的 −277 服务差分及 −116 初末变化，是实质反例，不因平均正向或能量较低而消失。这里保留“仍值得有限开发”的判断，不把它扩大成无害、支配或通用推荐。[E0：全部 evaluation_rows][e0]；[intake §§2–3][intake]。

### 两个学习率实例，不是稳定性结论

| 学习率配对实例 | 参考均值 | CONTROL 均值 | LOW_LR 均值 | 配对差分 | LOW_LR 初末差 |
| --- | ---: | ---: | ---: | ---: | ---: |
| seed89／B04 | 393.75 | 154.0 | 336.75 | +182.75 | −57.0 |
| seed101／B05 | 297.25 | 280.75 | 517.0 | +236.25 | +219.75 |

两实例等权差分 **+209.5** 只作描述。seed89 的提前 CONTROL 分离终止、LOW_LR 的初末损失及行间混合保持原义；seed101 的正初末变化不能替它补出恢复。四个条件不等于四个训练种子，B03 的预测包配对也不能算第三个 LR 配对。种子同时改变初始化、训练随机及评估 reset 的派生值，参考水平的不同不能只归于权重。[intake §4][intake]；[前次完整答复 §§一、四、七][prior]。

B05 两臂各完成 **65,536 普通训练转移、16 更新、512 optimizer steps**。E0 与 intake 记录实际学习率／有限性核对通过；本次没有重新执行这些核对，也没有把不在本清单中的原始 curves 文件说成已读取。CONTROL／LOW_LR 参数 L2 位移分别为 **8.425011334270215／1.956012517033048**，相对初始范数为 **0.22019392599878085／0.05112183928777729**。训练服务为 29,580／29,166，训练 invalid_commit 为 1,915／2,074；普通训练合法换主为 **3／0**。有限大梯度与参数位移并不定位损失来源，学习率的总效果仍包含 AdamW 原有衰减的缩放。[E0：training、acceptance][e0]；[intake §5][intake]。

DM 对“CONTROL 再次低于初始化至少 24”的预测没有命中；对 Delta 带内／近带的量级预测也没有命中。正号或混合行这一较宽部分命中，不能重记为预测到了 +236.25。旧结果、旧预测和本次新预测分别保存。[intake §4][intake]。

## 二、下一问题的依据、最强异议与替代选择

**最强支持**不是“来源量还没测到”，而是存在一个尚未比较、语义清楚的执行法则差异：被训练的普通随机策略与被评估的模态策略不是同一动作选择规则。它们共享最终网络时，可以在相同信息和相同原生约束下，直接观察服务及事件的变化。[eval：evaluate_episode][eval]；[policy：BatchedRecurrentPolicy.step_rows][policy]。

**最强异议**是：LOW_LR 已有可观的 incumbent 服务，给运动加入噪声可能损害它；随机意图可能增加无效提交或其他原生代价，最终预测／消息／证书链也可能仍不能支持合法应用。尤其 seed101 的三次训练换主属于 CONTROL，不属于本次拟沿用的 LOW_LR；训练还使用不同 reset、持续变化的权重与 Welford、更多交互。因此那三次事件不能证明“只要对最终 LOW_LR 抽样就会换主”，更不能证明抽样有益。[intake §§2、4–5][intake]；[E0：training][e0]。

本次只干预**高斯运动与 Bernoulli prepare／commit 的联合执行法则**。若出现增量，不能归因于其中某一成分，也不能据此解释历史 LR、归一化或循环共适应的原因。反过来，若抽样没有改善，它也不排除其他合法学习方法或来源机制。文献方面，intake §4 记录的是已有工具覆盖与未核实相关原文的边界；本答复不把目录匹配、合成库 fixture 或该覆盖检查当作机制证据、通用低学习率定理或新颖性判断。[intake §4][intake]。

### 为什么不先选 A

拟议 A 使用两份 seed101 最终检查点、四个原 reset、每格两个样本，需 **16 个新抽样 episode／最多 19,200 tick**，并只读复用八个历史模态行。它可以回答这些固定输入是否出现普通合法换主、出现时付出什么代价；它不能被写成算法效果或所选新训练实例的执行性能结论。本轮没有一个必须先知道该存在性事实才能作出的性能选择：无论事件为零还是非零，完整服务比较仍然有意义，且非零事件本身仍不确定来源原点可用。[PROPOSAL：Option A][proposal]；[证据规范 §§3、5.1–5.2、11.9][method]。

选择 B 是为了获得**一个事前指定的新学习实例及其执行法则比较**，不是声称任何既有检查点研究都必须重新训练。它新增一次真实学习，却只需八个抽样 episode，另有四个最终模态与四个初始化参考；两方案的 sampled width1 成本均未测，不能仅凭 A 无 learner 就断言它完成更快，亦不声称 B 已证明信息／时间比更优。这里按当前性能决定选择 B，放弃固定历史检查点的路径专门结论，不把 A 移成隐形前置条件。[PROPOSAL：Options A/B、Work][proposal]；[EXPOSURE_AND_COST.json][cost]。

第三个原样 LR 配对回答的是另一训练随机实例上的 LR 差分；全时间曲线、Welford 手术、运动／意图因子分解也各是不同问题。本轮不把它们附加进来。窄停止仍是合理备选，但当前有上述有限、会改变执行规则选择的对象，故不因来源尚未估计而停整个方向，也不凭两次正均值自动扩大原 LR 比较。

## 三、唯一新对象的训练与比较合同

### 一次真实学习，两种最终执行法则

对象为 **DISH-SAMPLED-EXECUTION-B06，B/EXPLORE**。问题：在一个新训练的 LOW_LR 最终控制器上，普通随机动作执行相对于其模态执行，是否带来值得开发的完整原生服务变化？最大主张是该训练实例、四个开发条件及所选有限动作样本上的探索性比较，不是稳定优势、安全、最优、来源效果或真实部署结论。

学习器沿用已接受 LOW_LR：STRUCTURED、所有原参数组 AdamW 恒定 **3e-5**、原 mean-MSE／BCE-with-logits／PPO／link 和 missingness 辅助目标、原梯度裁剪、recurrent replay、mask／标签规则及 Welford 更新。forecast_package=False，**服务预测输入保持 raw logits**；不要把 prepare／commit 原本就有的 sigmoid 概率计算误作重新开启已结束的 service-Q sigmoid／Gaussian-NLL 包。其他 optimizer 系数与 decay 系数不改。[B05 card §§2–3][card]；[policy：step_rows][policy]。

训练固定为 **16 更新 ×32 lane ×128 tick =65,536 普通转移**，每更新四 epoch ×八 minibatch，合计 **512 optimizer steps**。只保存并用于本次比较的训练终点为 update16；不选最佳或中间 checkpoint。记录实际更新、转移、optimizer 步、逐更新服务／loss／gradient 的统计口径与有限性、两个参数组 LR、参数位移、E／next-mask 及训练事件。一个独立训练实例不等于只构造一次模型对象；内部恢复、加载和构造按实际记录，不把评估副本或 engine 重建数算成独立训练种子。[B05 card §3][card]；[B04 study：run_arm][learner]。

### 新种子和实际 RNG 绑定

选定 **seed113**，新训练／环境 master 为 `SHA256(ASCII('DISH-SAMPLED-EXECUTION-B06/seed/113'))`。本次咨询没有生成该 master 或初始化模型。用它一次建立 master-addressed STRUCTURED 初始状态，原 actor／snapshot／critic Welford 均为空；初始化、训练 reset、训练随机流、四个评估 reset 及结果元数据都实际使用这个新绑定。不得复用 seed101 的相位 2／3／0／1、旧初始状态、旧最终参数或 297.25 参考均值。

这里有一个具体实现依赖：当前 B04 study 的 `master(seed)` 仍以模块常量 `OBJECT='DISH-CONTROL-LOW-LR-B04'` 计算摘要；`object_name` 只进入部分元数据，不能靠给它传 B06 名称就产生所选新 RNG 家族。CM 在对象内显式传递所选 master／家族并核对其消费者，保留 B04/B05 默认行为；不修改导入模块的全局 OBJECT／SEED，也不把元数据改名当作科学输入已经改变。[learner：master、configuration、prepare_shared、run_arm][learner]。

在同一 B 中评估该新初始化的**四行 raw-interface 模态参考**，一行一次，空 Welford、每行新鲜 native／循环状态，评估不更新统计。它是普通带运动／协议输出的零更新控制器，不是 held-only，不是 oracle，也不是安全基准。其回报不能决定是否训练、换种子、改条件或跳过某种执行模式；没有另一个先行 A。保留初始状态供本次输入明确使用即可，不建立新 resume 或身份验证体系。

### 宿主、输入配对与状态所有权

保持 **GROUND-TERMINAL-LINEAR-CLEARANCE-A03**、已修正普通续约边界、native float64／policy FP32 的单 compute-thread CPU 路径。原训练分布不改成四个评估条件；ABI、原生奖励、预测／标签法则、证书阈值、信息权限、动作空间、命令投影、实体／owner 身份和协议时序均不变。[card §§2–4][card]。

四个开发条件仍为 TARGET_VISUAL_MASK／TERRAIN_RELAY_MASK × K8／K4_TO_K12，speed4、slot0、block0。按新 master 和继承坐标法则派生并记录完整 reset。每个条件的初始化模态、最终模态、最终 sample0 和 sample1 使用同一 reset／环境外生随机法则；sample 编号只分开评价策略随机流，**不更换环境 master 或偷偷购买另一组世界**。

最终两种执行模式共享同一 update16 参数、learned log_std、预测头与 checkpoint Welford。每个 episode 新建 native 与零起始循环状态，加载同一固定统计，评价期间不拟合 Welford、不学习或更新 optimizer；递归隐藏状态仍按实际观察与消息每 tick 演化。动作不同造成后续观察、隐藏状态和预测不同，是执行法则的正常后果，不能强行把两个模式的轨迹或后续隐藏状态绑成相同。[policy：构造器、prepare_recurrent、step_rows][policy]。

## 四、普通抽样的准确含义

`evaluate_episode` 当前每步调用 deterministic=True；`step_rows` 在续约许可为真时，以 `mu=3*tanh(motion)` 的四个分量作无噪声动作，并以 prepare／commit 概率 `>=0.5` 取 1。这里的“模态”是这条已有执行规则，不是最优动作或经过原生投影后分布的模式。[eval：evaluate_episode][eval]；[policy：step_rows][policy]。

本次两模式只按下表区分：

| 当前普通续约时的输出 | MODAL | SAMPLED |
| --- | --- | --- |
| 四个角色运动分量 | `mu_f` | `mu_f + exp(clamp(log_std_f,-5,1))*Z_f` |
| prepare 意图 | `1[p_prepare>=0.5]` | `1[U_prepare<p_prepare]` |
| commit 意图 | `1[p_commit>=0.5]` | `1[U_commit<p_commit]` |

高斯与 Bernoulli 采用现有 sampler 的均匀数映射与变换：从原生 word 得 `U=((word>>11)+0.5)/2^53`，每个 normal 独立取两次 uniform，以 `sqrt(-2*log(U0))*cos(2*pi*U1)` 生成；每个 Bernoulli 使用自己的一个 uniform。保留四个运动字段 `MOTION_OWNER_X/Y`、`MOTION_STANDBY_X/Y` 和两个意图字段 `PREPARE_BERNOULLI`、`COMMIT_BERNOULLI`。不加温度、不缩放噪声、不缓存余弦之外的第二个正态值改变抽样映射、不截断／重抽“坏动作”，由原 native 路径作原有投影和拒绝。[policy：MasterAddressedPolicySampler、step_rows][policy]。

非续约 tick 不抽动作噪声或意图，保持原持有命令与原零意图处理；policy 的普通循环更新仍执行。prepare／commit 是提案，不是承诺成功：不绕过消息到达、预测证书、origin/application 条件或 owner 原生应用。合法应用后沿用 `apply_native_promotion`，并继续整程评价；没有来源干预、替代隐藏状态或 first-success 早停。

评价采用两个事前编号样本 **j=0、1**。策略评价 master 选为 `SHA256(ASCII('DISH-SAMPLED-EXECUTION-B06/EVAL_POLICY/seed/113'))`，与训练／环境 master 分离。逻辑地址固定为完整条件 canonical key、样本 j、episode 的物理步前 tick t、上述语义字段 f、字段内 draw d；t 从 0 起，不能用“第几次续约”代替，换主时也不归零。字段的 owner／standby 含义跟随原角色映射，不当作永久物理 UAV 编号。

在新卡中把该逻辑坐标绑定为一条明确的对象内评价地址格式，并在首次使用前记录；例如固定前缀 `DISH-SAMPLED-EXECUTION-B06/EVAL_POLICY` 后接 canonical key、`sample/j/tick/t/field/f/draw/d`，整数用无补零十进制、无隐含随机盐。不同样本、字段和 draw 不共用地址。实际 adapter 沿用上述已列 word／uniform／normal／Bernoulli 规则，其接口适配由有限 CM 实现核对；本次没有调用该新地址。

**不能直接把 TRAIN32 sampler 当成 width1 evaluator。** 它检查 episode 数组形状为 (32,)，写 TRAIN 地址，并在 normal／Bernoulli 中忽略传入 tick、读取内部 lane_episode_tick。本对象只需要一个局部 adapter 实现现有采样协议并绑定评价坐标；不补 31 个假训练 lane，不改全局 sampler，不引入新的 RNG 框架或改变训练地址。[policy：MasterAddressedPolicySampler；NativePersistentTrainingFlow][policy]。

完整后果链是：退化／续约事件 → 两物理实体的因果局部观察与真实消息 → 当前角色拥有的 active／shadow 循环状态 → 模态或抽样的允许动作提案 → 原生投影、证书与 owner 应用 → 完整服务、能量和事件。此前仍有真实的普通采样训练、原私有辅助标签、recurrent PPO／AdamW 更新；私有标签克隆的 promotion 不计为普通合法换主，未来标签也不进入 actor。[card §2][card]；[policy：collect_update][policy]。

## 五、主测量、初始化参考和来源界限

令 `J_M,r` 为最终检查点在条件 r 的一个模态 episode 的服务和，`J_S,r,0/1` 为两个抽样 episode 的服务和。主量为：

`Delta_exec = (1/4) * sum_r[(J_S,r,0 + J_S,r,1)/2 - J_M,r]`。

各 J 都按固定 **1,200 tick** 范围求原生二元 service 之和。native 提前终止则停止 stepping，余段服务计零，实际完成 tick、未执行 tick 和原因分别保留；不除以生存时长，不删终止行，不把另一模式截到同一较短长度。模态每条件只跑一次，不复制一次模态 episode 来伪造两个独立对照；两个抽样结果都进入均值，没有 best-of-two。[eval：evaluate_episode、terminal_facts][eval]。

**MEI 选 +24 平均服务 tick**，即完整范围的 0.02；相反方向用 −24，带内为 −24 与 +24 之间。这是本对象的有用变化尺度，便于与既有服务读数同量纲阅读，不是逐样本／逐条件门槛、数值容差或显著性结论。两次策略样本只给每个固定条件很有限的蒙特卡洛观察；所有样本、条件均值与差分都应发布。一个新训练实例不能估计训练种子总体不确定性，八个抽样 episode 不能冒充八个训练重复，也不对共享 checkpoint 的行作训练种子 bootstrap。[method §§5.2、11.7–11.8][method]。

用四个初始化模态回报 `J_0,r` 另报告 `D_modal=mean_r(J_M,r-J_0,r)`。它是同一模态执行法则下完整控制器的初末变化，仍包含参数、归一化等共同改变，不是纯参数或纯 PPO 效应。可以同时报告 `G_sampled_vs_init=mean_r[(J_S,r,0+J_S,r,1)/2-J_0,r]`，但它**同时混合训练形成的控制器变化和执行法则变化**，不能称为“抽样策略自身相同接口下的学习增益”。算术上它等于 `D_modal+Delta_exec`，不是独立第三份证据；本轮不为获得更强归因再增加初始化抽样行。

伴随量保留每个 episode 的能量、七类原硬事件、实际／未执行 tick、终止原因、普通合法换主次数、首次换主时间以及前／后服务的时间分解。首次时间定义为首次观测 cas_applied 非零的**该次 native.step 完成后的 native tick**；没有则记未发生，不填成 horizon。原 evaluator 已有 cas_applied 累计与 promotion 路径，但没有首时刻字段，这个小的对象内报告增量需要检查。[eval：evaluate_episode][eval]。

事件／换主对照要注意分母：最终 MODAL 有四个 episode、SAMPLED 有八个。发布原始数与分母，并按“条件内两个样本均值、条件间等权”给可比伴随描述，不拿八行总事件数直接对四行总数宣称事件率上升。早终止导致暴露不同仍须明示；能量低可能只是更早停止，不能无条件称为能效改善。保留原回报，不另造事后事件权重抹去服务损失或 native 代价。

有三个不同层次：**普通合法换主**是本 evaluator 的原生 cas_applied／owner 应用事实；**可用来源原点**还需要在指定 first-application 切点具备来源比较的输入和资格；**COPY−RETAIN、SHADOW−COPY 价值**需要相应匹配来源干预与后果。本轮只观察第一层及普通服务。即使抽样出现换主，也不证明第二层已经可用，更不估计第三层；换主后时间上的服务不能未经 packet 来源核对便归于新 owner 传送，亦不是换主的因果收益。

## 六、前瞻预测与结果如何改变选择

**我的可评分主预测与 DM 同向：`Delta_exec <= -24`，但置信度低。** 理由是抽样会同时扰动已取得 incumbent 服务的运动及意图，完整 native 后果不保证随机策略比其模态执行更好；已有无效提交也提醒机会与代价可能同时增加。这是选定试验前的性能猜想，不是由训练／评估差异推出的噪声损害定理。新种子的模态基准还未测到，不能把 seed101 的 517 带入预测计算。

反向机制同样合理：模态阈值可能把一段概率固定为重复动作，抽样可能打断无效提案或产生有用的运动／准备组合；训练本来也优化随机行为。因此 **`Delta_exec >= +24` 且原生权衡值得开发** 是重要竞争观察；带内、样本间或条件间异质性也都可能。不给换主次数设预测下限，不预测必然无事件或必然合法换主。主量的大小与符号按实际计分，不能再以“出现混合行”代替量级预测命中。[proposal：Prediction、Concrete grounding][proposal]；[policy：采样与模态法则][policy]。

| 新观察 | 本轮之后允许的读法与建议 |
| --- | --- |
| `Delta_exec>=+24`，原生事件／能量／终止权衡仍值得开发 | 本训练实例上抽样执行有有限平均增量，可把它留作执行规则候选，并据完整结果考虑一个有限独立训练跟进；不是默认全方向切换或稳定优势。混合行本身不取消主均值，但所有负行仍限制适用性。 |
| 相对模态改善，但 sampled-versus-init 仍明显负向 | 只称执行法则的相对改善，不能说恢复初始化服务；初始化参照及其接口差异必须同列。 |
| 主量带内，或两个样本／条件差异使开发价值不清楚 | 报告有限未决／异质性，不称等价，不追加样本直到同号，也不按最好一条选择模式。 |
| `Delta_exec<=-24`，或正均值伴随严重 native 代价 | 在本例倾向保留模态默认、不扩展该联合抽样规则；预测命中也不是原因定位。若仍有换主，则是带成本的路径事实，不能挽救服务负结果为“来源成功”。 |
| 抽样或模态出现普通合法换主 | 保留次数、首时刻、完整后果；只能说明所观察路径可发生该事件。是否有来源原点及来源增量留给另一个实际选择，不在本轮自动追加 fork。 |
| 全部最终评价无合法换主 | 原生执行法则比较仍可读，来源量仍未估计；不说宿主不可能换主、抽样无支持的普遍定理或 SHADOW 无价值。 |
| 学习、输入或主测量受损／未完成 | 报告实际缺口、计数及独立可信行，不填造完整 Delta，不连带重判 B05/B04。原生合法终止本身不是这种损坏。 |

表中分支可以并存。任何结果都不自动购买第二训练 seed、第三个样本、另一个噪声强度、意图阈值、长训练或中间 checkpoint；对一个新对象的需求和支出在完整结果后另行判断。无论我的预测还是 DM 预测错误，都保留结果，而不换 seed 或重写旧判据。

## 七、完整工作、支出与必要检查

| 工作因素 | 唯一所选 B06 |
| --- | --- |
| 独立学习单位 | 一个新 seed113 的 LOW_LR learner；不是两种执行模式各训一次 |
| 普通交互与更新 | 65,536 转移、16 更新、512 optimizer steps，全部原 recurrent replay／backward 保留 |
| 初始化参考 | 四个模态 episode，最多 4,800 实际 tick，零标签／backward／optimizer 调用 |
| 最终执行比较 | 四个模态、八个抽样 episode，最多 14,400 实际 tick |
| 全部评价 | 十六个 episode，最多 19,200 native step／width1 policy 调用；native 终止可使实际计数更少 |
| 选择／搜索 | 一个最终 checkpoint；两个固定样本全部保留，无候选搜索、轨迹树、来源 fork、参数网格或 best-of-many |

原学习标签工作不能被“普通转移数”藏起来。令 `N=65,536`、E 为本次实际 eligible 数、H 为私有克隆后果步数，原生训练调用是 **`2N+2E+H`**，`0<=E<=N`、`0<=H<=20E`，所以界为 **131,072 至 1,572,864**。这是训练 step 调用界，另有 policy／critic forward、PPO、backward、optimizer、构建／加载、检查和发布；不是 24 倍 wall 预测。保留现有 E 读数，H 无直接读数时记未测及上界，不为性能结论扩建 native ABI 或全轨迹记录。[cost：proposed_B][cost]；[card §6][card]。

八个最终抽样 episode 若共有 R 次实际续约，新增评价策略抽样为 **4R 次 normal、2R 次 Bernoulli、10R 次 uniform**；`R<=9,600`，故该评价部分至多 96,000 次 uniform。这个界不包括原训练 sampler 的抽样工作，也不是所有评价 tick 都有续约。不存在 a^N／b^H 候选扩展：两个 episode 是被估计执行法则的保留样本，不是挑选可用轨迹的搜索。未来 E、H、R 和 sampled width1 wall 均未测。[cost][cost]；[policy：sampler、step_rows、collect_update][policy]。

**完整新 cap 为 1,800 秒，覆盖整项 B06。** 必要聚焦检查、原生构建／cache load、初始化与模型加载、训练／标签、全部十六个评价、归约与完整发布均计入，只收费一次；分脚本或分阶段不重置额度。没有另加 300 秒路径 A、120 秒参考、第二执行模式额度，亦不因运行较快而增加样本。给发布留在剩余额度内；支出耗尽、实际非有限学习状态或威胁主量的真实故障时停止并保留已发生曝光。有限大梯度不被改称非有限错误；原生提前终止保留为结果，不触发坏行重跑。

B05 的 **212.86 秒 LOW_LR 整臂**已包括其训练和四行最终模态评价，**7.11 秒共享项**包括初始化／四参考行。它们是本次有用的已测工作类型参照，不是 sampled episode 单价，也不能把新方案精确完成时间写成其简单相加。增加的八个抽样 episode、adapter／检查及新种子的 E/H、cache／节点负载尚有成本不确定性；不以未知为零，也不要求另买校准实验或按核心数线性折算。[E0：cost、training][e0]；[cost：cost_projection][cost]。

历史完整成本保持可读：B05 包括失败 focused 1.15 秒、成功 focused 1.07 秒、shared 7.11 秒、CONTROL 210.63 秒、LOW_LR 212.86 秒，总 invocation wall **432.82 秒**；两臂正式分摊约 **215.30／217.52 秒**。聚合 CPU **444.01 秒**与含控制面间隔的 study elapsed **2,663 秒**不是同一个量，失败前无学习不等于无成本。这些是旧支出，不是新额度。新对象报告完整 wall 和有范围说明的 peak RSS；不新增 CPU 合规主张、profiler 服务或其他非本主张必需的遥测门槛。[intake §5][intake]；[E0：cost][e0]。

后续实现与执行遵循既有 remote-first 路由、精确提交／推送源码、detached supervision、单线程 CPU／FP32／float64 和每次实际调用前同节点 physical／effective available memory 均至少 4 GiB。活的路由配置和 owner resume 由已有操作链处理，不在本答复新设审批或等待。若具体完整实现已知超出 cap，返回该明确工作／范围问题，不静默删标签、少训练、缩短回报范围或扩大 cap。[AGENTS §§4–8][agents]。

### 检查只保护本次比较的直接依赖

需要一次聚焦的改动／主输出覆盖：新 master 确实进入初始化、训练和 reset，而不是只改标签；评价采样器确实使用 width1 的评价坐标、物理 tick 和分离的字段／样本；Gaussian 与 Bernoulli 保留原变换，非续约不取新动作样本；modal 路径未夹带改变。核对两模式从同一最终参数和固定 Welford 起步、各 episode 的 native／循环状态独立重置、promotion 和 full-horizon terminal 规则保持；用少量合成行核对两样本先平均、四条件再等权的主归约及首次换主时间／缺失表示。已有 LR 持久性、修正接口与终止处理的可信覆盖直接复用，不重跑整个 B05、全部历史窗口或所有原始 fixture。[policy][policy]；[eval][eval]；[method §11.8.6][method]。

普通交互、PPO 和私有 labels 定义真实 learner；modal／sampled 行定义当前执行法则比较；初始化四行限定初末叙述；事件／能量／终止限制性能解释；必要 sampler 检查保护处理、信息与主量。其余完整原因定位、精确上界／headroom、支持 census、逐更新评价、历史重放、所有中间数组或来源框架均不购买，相应放弃唯一机制、最优性、轨迹恒等、稳定性和来源归因等更强主张。不是把这些变成下一个 A 等待队列。[method §§11.4、11.7–11.9][method]。

CM 保留普通 **2,000 新非测试行、600 runner 行及现行测试预算**，按语义风险完成已有独立 review，不新增 reviewer 层级、scheduler、registry、guard 或验证服务。对象内 sampler／输出改动不是当前已经接受的实现。本次既未执行源码，也未证明新地址适配已通过；源码接受和实际完成以后继的真实检查与记录为准。[scope §§4–5][scope]；[AGENTS 的 workflow／focused reading 校准][agents]。

## 八、历史与实际访问边界

B04 的所有行、初末损失和提前终止，B05 的 −277、209 invalid commits、三次 CONTROL 训练换主、零最终换主及正平均差分全部保留。新的执行法则结果不会倒过来解释旧 LR 差分，更不改变 B03 的预测包不利结果、B02 已执行接口下的限定读法或更早 A/B 事实。联合预测包扩展仍结束，历史 R02 不重开。COPY／RETAIN 足够、deadline replay 包含及 checkpoint／角色共适应仍是未被排除的来源解释。[前次完整答复][prior]；[intake §§3–6][intake]。

本轮不修改规范，不冻结 C，不选择新算法家族或 Portfolio 生命周期、容量、优先级、融合、注册、recast 操作。来源议程的下一完整干预仍未选择；“来源量未估计”不是负来源结果，也不是无限续投理由。这里只购买上述一个具名执行法则 B。[当前 task][task]。

科学证据均经连接的 GitHub 在 **8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002** 读取。下表 C/ 为 `docs/research/candidates/degraded_incumbent_shadow_handover/`，P/ 为其 `pro_packets/20260906_post_b05_convergence/`，E/ 为 `experiments/candidates/`；链接均绑定本次科学版本。范围读取不冒称全文。

| 实际读取的允许路径 | 范围 |
| --- | --- |
| [P/PROPOSAL.md][proposal] | 完整，作为尚未选定的 DM 建议评估 |
| [P/EXPOSURE_AND_COST.json][cost] | 完整，区分已测值、派生界及拟议工作 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 完整正文与六条先前评论；updatedAt 是讨论更新时间，不冒称本次读取时刻 |
| [C/DISH_CONTROL_LOW_LR_B05_RESULT_INTAKE_20260906.md][intake] | 完整 §§1–6，补齐成本及结尾 |
| [C/control_low_lr_b05_20260906/TECHNICAL_ACCEPTANCE.json][e0] | 完整 primary、十二行及 reset、counts、cost、training、acceptance |
| [C/DISH_CONTROL_LOW_LR_B05_SCIENCE_CARD_20260906.md][card] | 完整，含 §§1–6、工程 handoff 与结尾 |
| [C/pro_packets/20260906_post_b04_convergence/archive/RESPONSE.md][prior] | 完整，重叠读取补齐被截断部分与引用尾部；未递归读取其其他引用 |
| [E/degraded_incumbent_shadow_handover/forecast_package_b02/study.py][eval] | 行90至文件尾；判断依据为 terminal_facts、evaluate_episode，未展开依赖树 |
| [E/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py][policy] | 行1–465，覆盖 sampler、初始化／状态、step_rows／promotion 及 collector |
| [E/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py][learner] | 完整共享初始化、master／LR、run_arm 与原 reducer |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 行35–130、308至末尾，含 §§3–5 与相关完整 §11 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 行1–112；采用普通 §§4–5，不采用旧对象专用附款 |
| [AGENTS.md][agents] | 行1–415，相关正文／owner 校准；不读取活路由配置或扩大当前写权限 |

十三条所列路径均可访问。Issue4 正文及全部六条既有交付评论已在 **2026-09-06 22:33:53 PDT（2026-09-07 05:33:53 UTC）之前**实际读取，包括明确列出的 [post-B04 评论][comment-b04]；其余为 [post-B02][comment-b02]、[post-A01][comment-a01]、[post-A02][comment-a02]、[post-B03][comment-b03]、[post-witness][comment-witness]。交付前再次检查分支、目标和后续评论；可变讨论不替代固定文件。未读取清单外 DIRECTION／Portfolio／原始曲线／文献目录或 native 依赖，不用自动出现的旧附件替代本次 task。

本次咨询新增模型、native 状态、episode、transition、backward、optimizer step、测试和实验均为零。未来 seed113 的回报、转移机会、位移、E/H/R、采样器验收及完成成本仍未观察。唯一外部变更是当前完整答复文件及其链接评论；科学选择不等于实现、启动或已经取得新结果。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/3433eb9bfb80dd61a1fa23d3a56533715623ef92/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b05_convergence/TASK.md
[proposal]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b05_convergence/PROPOSAL.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b05_convergence/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b05_convergence/ISSUE_SNAPSHOT.json
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B05_RESULT_INTAKE_20260906.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05_20260906/TECHNICAL_ACCEPTANCE.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B05_SCIENCE_CARD_20260906.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b04_convergence/archive/RESPONSE.md
[eval]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/study.py
[policy]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py
[learner]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py
[method]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/8d7be753b8f609d555e8cc1dd24d5d1c9a2e3002/AGENTS.md
[comment-b02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
[comment-a01]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5558729980
[comment-a02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5560502547
[comment-b03]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5561089362
[comment-witness]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5562295763
[comment-b04]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5563973543
