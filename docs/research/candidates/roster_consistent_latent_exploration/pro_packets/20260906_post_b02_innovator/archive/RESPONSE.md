# 做一次冻结状态的梯度分配测量，不再凭参数运动量追加训练

**方向层决定：选择选项 1 的收窄版本，作为唯一下一对象：RCLE-TBCFV-A02-FROZEN-SCORE-ALLOCATION，类别 A/RECON。** 在 B02 的共同初始化与两个 update-200 状态上，测量 manager-score 与 actor-score 对实际联合梯度的贡献、参数组位移，以及固定输入下的抓取分布变化；不更新参数，不改 baseline，不追加训练，不比较新的学习器效果。选用两个预先指定的训练域探查 block，共 512 个新 episode、最多 32 次反向求导；完整对象支出上限为 **300 s**。下文给出可直接写卡的状态、采样、读法与停止规则。

我改变上一轮“直接买一次更新量干预”的优先次序，是因为它已经得到有效反例：0.02/200 的实际运动量明显增加，却没有接近预定的服务改善。现在一个有明确分支解释的冻结状态测量，能够决定下一次改动应优先针对梯度分配、baseline 的有限样本作用，还是另一个仍未定位的学习问题。**它不是证明唯一机制、使 C1P1 先学会、补齐上参考或允许普通 B 的资格门槛。** 测量即使未决，也不禁止提出一个独立有价值的 B；本轮只选择这一个 A，不连带授权后续 B、源码变更或启动，不冻结 C，不改变 Portfolio 状态，也不授权完整五臂二十 block 方案。[B02 结果 intake §§1–4][result]；[经验规范 §§3、5.1、11.8–11.9][spec]

## 一、两个反例现在支持什么

**观察与保留读法。** B01 是 seed 17、0.0005 非零步长的完整配对；B02 是 seed 18、0.02 非零步长的完整配对。二者每臂均为 200 次真实更新、12,800 个训练 episode，并非零学习器替代。B02 还保留了一个共同初始化面板。B01 原有的带内／恢复指标饱和读法不改；B02 按其卡第 4 行结束本次运动量支出：没有得到约 0.05 的有用学习改善，不自动续到 4,000 次、扫步长或热启动头。[B01 intake][b01]；[B02 卡 §§2–5][card]；[B02 intake §§1–4][result]

B02 的主要结果可概括为下表。数字来自所列结果 intake 和机器派生的曝光／成本记录；参考行另与直接读取的 reference summary 核对。显示值做了舍入，不是本咨询重新运行得到的结果。[结果 intake §2][result]；[EXPOSURE_AND_COST.json][cost]；[reference summary：cells][reference]

| ACTIVE_CONTINUATION 路径 | 初始化 U | C1P1 最终 U | FLEX 最终 U | 最近信标参考 U |
| --- | ---: | ---: | ---: | ---: |
| 8→12 | 0.696696 | 0.695286 | 0.695319 | 0.245646 |
| 12→8 | 0.721233 | 0.718720 | 0.718683 | 0.318652 |

两路径等权的 ΔU（FLEX 减 C1P1）约为 −0.00000191，配对情景标准误约为 0.00002460；两臂相对初始化的 G_U 都约为 +0.00196。初始化及两个最终学习面板上的 τ 全为 40。参考在 8→12 的 τ=40 比例为 1，在 12→8 为 0.97265625：**大量降低 U 仍可以几乎不触发连续四 tick 完全恢复。** 因而 τ 脱离 40 不能作为“学习发生了”的通用门槛。本 A 不重新定义 τ，也不用一个偶然恢复 episode 判定能力。[cost]；[reference]；[宿主卡：Treatment-blind physical endpoints][host]

两臂最终 U 在 14/2,048 个配对情景上不同；初始化与 C1P1 最终在 1,874/2,048 个情景上不同。最终参数距共同初始化的位移范数都约为 0.473，路径长度上界为 4。这里不存在“参数、动作或函数完全没变化”的证据；相反，已有结果反对最强的完全不动解释，但没有显示实质服务收益。两个位移范数接近也不是两臂参数向量之间的距离。[cost：scenario identity、parameter displacement]；[result §§1–2]

上一轮我提出“至少一包的 U 相对起点下降约 0.05”的工作预测没有发生；“两臂几乎不改善”的竞争预测得到支持。该反例必须与最初支持 0.02 的理由一起保留，不因本次改选诊断而消失。B01 与 B02 同时改变了种子和法则，因此不是同一法则的两个独立重复，也不能把它们之间的差直接解释为步长的配对因果效应。[上一轮决定：预测与结果分支][previous]；[post-B01 intake][previous-intake]；[result §4]

## 二、对 DM 解释的实质修正

**梯度范数下降，不等于归一化后的更新幅度下降。** 所读 `models.py` 的注册函数仍是 0.0005 法则；B02 卡和 CM 记录明确说明，B02 入口另有参数化步长函数，不调用该注册函数。B02 报告 400 次非零更新均使用并记录了 0.02 的应用位移范数。原始梯度由约 0.6–0.8 降到约 0.03–0.06，不能单独说明更新被 baseline 压到零；归一化已经去除了整体正比例尺度。它仍可能改变梯度方向、噪声与通路分配，这才是值得测的量。[models.py：registered_plain_sgd_step][models]；[config.py][config]；[CM 记录：参数化步长与实测 delta][cm]；[cost：training-curve samples]

**baseline 接近格均值，不等于有用 advantage 信息被消灭。** 对给定状态／格、动作无关并停止梯度的 baseline，score 的条件期望为零时，减去 baseline 不改变对应未归一化 score 估计量的期望；它主要改变有限样本方差和相消。该判断依赖卡片的固定时钟、成员程序和合法 score 计算，不是对任意依赖动作的 baseline 的保证。平均 advantage 接近零也不等于 advantage 的 RMS、回报差异或梯度方向没有信息。

还必须保留另一个区别：B02 用的是非线性的 `g/‖g‖`。即使两种 baseline 的原始梯度期望相同，归一化后更新方向的期望也未必相同。因此零 baseline 是可研究的改动，但不能先验说它“让信息保持更久”或一定修复训练。本次在同一冻结图上作零 baseline 的反事实梯度比较，只测这种有限样本敏感性，不把它当零 baseline 训练结果。[models.py：averaged_episode_score、exact_advantage_loss、apply_registered_block_update][models]；[宿主卡：Training, matching, and checkpoint law][host]

**manager 通路和 actor 通路不能按参数名字直接切成互斥两堆。** 实现的 episode score 是所用 Normal log-density 的均值加所用 claim log-probability 的均值。两个 score 的梯度可以落在共享 encoder 上；FLEX 的确定性事件头图保留在 actor 输入中。应先按 loss 项分解，再按实际张量组投影，而不是把 encoder 全部记给 manager，或从“head 末层起点为零”推断它一定没有梯度。共同初始化在两包中的前向策略对应，也不保证两包的反向图相同。[models.py：TBCFVModel、event_plan、stopped_actor_plan、make_pointer_inputs、averaged_episode_score][models]

这些是收窄解释，不是新的接线故障结论。B01、B02 继续作为有效结果保留；没有具体缺陷及依赖证据，不隔离它们，也不要求复现两轮训练。[经验规范 §4、§11.8][spec]

## 三、冻结状态 A 的精确合同

### 状态与采样

宿主、观测、reward、decoder、两包和 FP64 计算保持原定义。只使用 seed 18 的三组参数值：共同 θ0、C1P1 的 θ200、FLEX 的 θ200。形成 **四个逻辑配置**：C1P1-init、FLEX-init、C1P1-final、FLEX-final。增加 FLEX-init 的目的，是不把相同前向策略错误当作相同反向图；这不是增加训练臂。[host]；[models]；[card]

最终参数从 B02 留存状态加载，并记录实际来源与已有身份信息。θ0 优先加载留存初始张量；若只保留了初始化法则和 seed-18 键，则按同一固定法则重建，并核对已有初始化身份／范数，明确记为重建而非加载。不得为取得起点或 baseline 重跑训练，不换初始化种子，不使用 final 权重反推一个“更好”的起点。本咨询没有加载这些状态；其可用性仍需由执行节点实际读取确认。[result §1]；[card：seed law、初始化面板]；[models.py：apply_affine_fixture_uniforms][models]

在既有随机数派生方法中使用两个新的、固定的探查 block 标签 `19001`、`19002`，另设 `post-b02-frozen-probe` 用途域，来源仍为 seed-18 根键。它们不是新的训练种子。每个 block 严格为八个训练格各八个 episode，即 64 个 episode；训练 roster 仍为 {6,10}，包括静态与 6→10／10→6，交叉两种 epoch 条件。四配置共用相同外生场景及语义配对随机数；不让臂名选择随机子流，策略分歧后不强制相同访问状态。两个 block 均预先包含，不根据第一个结果决定是否购买第二个。

总量固定为 **4 配置 × 2 block × 64 = 512 个新 episode、32,768 个环境 tick**。这些都是测量曝光，不能因为零 optimizer step 就写成零曝光。不新增 held-out 面板，不用旧 held-out 情景挑阈值，不扫描参数、步长或 baseline。最多建立四个用于本测量的模型实例，顺序处理计算图；使用现有单模型构造与初始化函数，不调用五臂全量工厂来偷增配置。保留全部八格和两个 block，不只报告解释最顺的一格。

### 主测量：实际 loss 的通路梯度与张量位移

对每个固定 64-episode 图保留原来的 stopped 抽样与 stopped advantage。令 `s_M,e` 为 episode e 的所用 Normal score 均值，`s_A,e` 为所用 claim score 均值；不取消卡片中的分别取均值，不按 agent 数再重加权。计算：

`L_M = −mean_e[(Y_e−b_cell(e)) s_M,e]`，
`L_A = −mean_e[(Y_e−b_cell(e)) s_A,e]`，
`g_M = ∇L_M`，`g_A = ∇L_A`，`g = ∇(原联合 loss)`。

使用现有 PyTorch 的 `autograd.grad` 即可；不得执行 step。报告三者全向量范数、`g_M` 与 `g_A` 的夹角余弦、以及 `‖g‖/(‖g_M‖+‖g_A‖)` 的相消读数。计算同一图的 `g−g_M−g_A` 残差，按 FP64 的明确数值容差判定该测量实现能否解释原 loss；这只是当前测量的局部恒等式检查，不建立新的 guard 或通用验证框架。零向量的比值／夹角记为未定义或明确的零情况，不用任意 epsilon 制造正常比率。[models.py：exact_advantage_loss][models]

将每个梯度再投影到五个互斥的实际张量组：两个 set encoder；四个 `manager_*` 层；三个 `pointer_*` 层；`common_update_hidden/final`；`agent_update_hidden/final`。组内保留各个 named tensor 的范数，组间平方和覆盖全部注册参数；无图／无梯度与数值为零分别注明。对两个最终参数另外直接计算各张量及各组的 `‖θ200−θ0‖`，以及真实的 `‖θF,200−θC,200‖`。这些是加载权重后的新测量，不得用既有两个位移范数相减代替。这样同时回答“当前梯度落在哪里”和“已观察到的净位移落在哪里”，但不冒充 200 次训练的历史梯度分解。[models.py：TBCFVModel 参数清单][models]

**baseline 的处理必须固定。** 初始化用 b=0；最终状态用每臂实际的八格 b200，整个测量期间不更新。优先读取留存 buffer；若未保存，则可从该臂完整精度、逐更新的训练格 Y 均值，按原 dtype、顺序和 `b_(k+1)=0.95 b_k+0.05 mean(Y_k)`、b0=0 重建。注明加载／重建及精度限制，不能拿新探查 block 的回报均值代替 b200。若留存量与足够精度的曲线都无法支持重建，baseline-sensitive 部分明确未决；保留可独立成立的零 baseline 梯度、参数位移与条件分布测量，然后结束，不为恢复 buffer 重跑 B02。[models.py：apply_registered_block_update][models]

每个最终状态还在 **同一批轨迹和同一计算图** 上将 b 置零，计算 `g_M^0`、`g_A^0` 和它们的和；这只改变导数计算的权重，不产生新轨迹或修改模型。逐格报告 Y 的均值和标准差、原 baseline、advantage 的均值、RMS 与标准差，并报告原／零 baseline 的总梯度范数比及方向余弦。仅“梯度范数变大”不支持信号改善；要看方向、相消与 actor 投影是否也发生变化。

反向曝光上限为 **32 次导数求值**：四个初始化配置-block 图各三次（M、A、联合），共 12；四个最终图各五次（M、A、联合、零 baseline 的 M、A），共 20。这里调用 `autograd.grad` 仍算反向求导，不把 API 名称当作“零 backward”的理由。所有参数、baseline 和随机程序在测量过程中不接受任何学习更新。

### 伴随测量：小型固定输入库，而非重新跑性能面板

为区分“参数动了”与“pointer 在可见输入上动了”，从 C1P1-init 的两个探查 block 各取每格按情景序号最先的两个 episode，在 tick {0,24,28,60} 的抓取时刻各取公开排序的首、末两个活动成员，保留原始公共／个体／candidate 特征和当时使用的 z。共 **2×8×2×4×2=256 个固定输入点**，没有新增环境 episode。

在三个参数快照上，对同一输入点重算各自 encoder 和 pointer 的六路概率；不复用旧的已编码向量。z 固定为该点的 C1P1-init 值。初始化的两包在这个条件比较中只需一份概率，所以共 **768 个六路概率向量**。报告每格、每个探查 block 的 entropy 均值，以及 final 对 init、FLEX-final 对 C1P1-final 的总变差距离 `TV=0.5 Σ_a |p_a−q_a|` 的均值与最大值。不开 argmax 替代采样，不用概率库选择 checkpoint。

此伴随测量刻意固定 z 和外部输入，**只识别公共 encoder／pointer 的条件变化**；不识别 manager 或 FLEX 头改变 latent 后的全策略效应，不代表最终策略的访问分布，也不是服务价值的因果分解。这是省去额外在线面板所放弃的更强主张。头和 manager 的梯度／位移仍在主测量中报告；不为补齐端到端解释扩大本对象。

## 四、什么叫 actor 可忽略，什么不是

本 A 不登记算法效应 MEI。原 U=0.05 与 τ=4 的尺度只保留为 B01／B02 的服务解释背景，不移植为梯度“有效性”门槛。以下是本次选择的 **描述性读法尺度**，不是数学上的通路不重要或未来更新必然无效。

定义 `r_A=‖g_A‖/(‖g_M‖+‖g_A‖)`，以及 `r_P=‖P_pointer g‖/‖g‖`。对某个快照，只有其原 baseline 下 **两个探查 block 都同时满足 r_A≤0.01 且 r_P≤0.01**，才使用“这两个样本中的 actor-score 贡献与 pointer 更新分配很低”这一表述；不简写成“actor 无作用”。1% 是为避免把普通相对偏小夸成瓶颈而选的严格标记，不是从结果调出的阈值。对于一个非零、按 0.02 归一化的假想更新，r_P≤0.01 意味着 pointer 专属张量投影不超过 0.0002；这里不实际应用该更新，也不把投影幅度推成回报变化。

同时逐块报告 manager-dominant 的较弱读数 r_A<0.5，而不把它与上述 1% 标记混为一谈。方向相消、共享 encoder 及 FLEX-head 投影必须与比率一起读。单块低、另一块高，或一个状态低、另一个状态高，按异质／未决保留，不合并成一个方便的平均结论。

固定输入库中，每个探查 block 的平均 TV≤0.01 可称“该输入库上的平均条件概率变化小”，但仍展示所有格与最大 TV；不能据此声称所有动作分布不变。对零 baseline 只报告方向、范数、投影的连续变化；不存在一个新的“必须达到多少倍才允许下一 B”的门槛。

**工作预测与反驳方式。** 我的暂定预测是，至少一个最终快照在两个探查 block 上都表现为 manager-score 的原始范数较大（r_A<0.5），并伴随较小的条件 pointer 概率变化；我不预言它必然通过更强的 1% 标记。若没有任何最终快照同时满足这两个条件，或 actor 通路并不弱且条件 TV 明显不小，这个具体解释优先级应下降。更强的竞争解释是：actor 已收到可观梯度，参数与概率都改变，但方向噪声、平均 score 的信用分配或协调结构没有转化成服务。这次有限测量可以区分若干局部读数，不能裁定唯一病因。[models]；[DM 备选与未知][options]

## 五、结果分支改变什么

| 完成后观察 | 当前可改变的判断 | 明确保留的限制 |
| --- | --- | --- |
| 两块均出现低 actor／低 pointer 分配，且条件 TV 小 | 提高“联合梯度分配或 pointer 条件敏感性”作为下一具名改动动机的优先级；降低盲目再加整体步长的优先级 | 不是通路全训练期无梯度，也未证明重加权必然改善 U |
| 原 baseline 对零 baseline 改变方向、相消或 actor 投影，而不只是全局尺度 | baseline 的有限样本作用值得单独检验；可为未来一个明示 baseline B 提供理由 | 零 baseline 的冻结梯度不是零 baseline 的训练效果，不自动执行选项 2 |
| actor 分配不低，或条件概率已经明显移动而服务仍平坦 | 反对“抓取分布完全不响应”这一简单解释；保留信用分配、噪声与协调学习问题 | 不自动证明宿主不可学，不转向无界架构／步长搜索 |
| 块间冲突、未达任何强读数，或各量普通 | 原样发表未决结果并结束这次 A；不能把未决作为禁止普通 B 的规则 | 不补买样本直到出现一个方便解释，不承诺唯一诊断 |
| 文件身份、数值图或资源问题破坏某部分观察 | 只停止并标明依赖该问题的测量；保留独立可信的直接读数 | 没有具体依赖证据，不追溯隔离有效 B01／B02；无自动重试预算 |

各分支都以 **结束 A 并带测量回到下一对象选择** 为止，不是在本卡里藏一个条件触发的 B。若以后提出算法实验，仍需使用真实 learner、同信息比较与按主张需要的独立训练种子；两个探查 block 不能冒充训练重复。[经验规范 §§4、5.1–5.2、11.8.3][spec]

## 六、为何不是另外四个对象，以及这次工作是否值得

**最强反对意见**是，这仍然是一个不能直接证明服务提高的诊断：两个冻结状态和两个采样 block 可能不代表训练中段；梯度范数又依赖参数化；输入库还故意固定了 latent。因此，直接做新的配对 B 依旧是合法而可能有价值的选择。我选择 A 的理由不是“必须先解释失败”，而是眼前两个便宜改动的动机还分不清：固定零 baseline 的说法混淆了均值与信息，0.2 则再次混淆参数运动量与有用函数变化。少量具体测量能使下一次改动的理由更窄，且可以在没有有利读数时干净结束。

单臂 1,000 次的曝光阶梯若回答其自身的有限学习问题，可以是合法 B，不因单臂就变成 A；也不能声称决定“任何曝光下”宿主是否可学。但它需要最多 64,000 个训练 episode 和多个面板，且继续沿用已经没有服务收益的方向法则。当前没有必要优先购买它。再加一个量级、热启动头或改 baseline 都是结果知情的新对象，不能从便宜、上限未花完或旧卡默认重复取得自动授权。停车整个 RCLE 则超出了这两个小预算、不同种子的反例；本轮也不作这个选择。[options]；[card §5]；[spec §§11.8–11.9]

**完整工作量**是：三组参数、四个包-状态图、两个 64-episode 探查 block、512 次环境 episode、32 次求导、768 个固定点的六路概率前向、张量差与描述统计，以及加载、必要准备和结果出版。没有候选策略搜索、联合动作枚举或未来轨迹搜索；六路 softmax 本身是原算法正常 action selection。512 个 episode 是一个新的 200-update 配对 B 的 25,600 个训练 episode 的 2%，但不能把这个比例当成运行时比例：同图重复求导、图保留、文件加载和统计出版都有额外成本。

只用已经测到的时间作为背景：B02 完整链约 152.6 s，B01 约 144.3 s；B02 的 C1P1 臂约 71.5 s（包含初始化面板），FLEX 约 71.2 s，脚本参考约 1.5 s。**现有记录没有把一个 2,048-episode 学习面板独立计时。** 两臂约 0.3 s 的总时差既混合臂差异又混合准备工作，不能识别“每面板约 10 s”，也不能据此将三快照诊断报价为约 30 s。每个训练更新约 0.3 s 的粗略尺度也不是本次多次反向图的已测成本。[cost]；[result §1]

本次新对象的 **300 s 是完整逻辑调用的支出上限，不是预测耗时**，也不是从 B02 剩余 1,500 s 或旧的 2,700 s 上限转来的余额。包括加载／重建、必要启动准备、全部测量、汇总和出版；不得拆成多个各享上限的 worker。一次调用，达到上限即停并保留部分记录，不延长、不替换探查 block、不自动重试或换节点。未知成本保持未知，不要求先做一个新的成本校准实验。[运行时规范：complete logical invocation、toy threshold][runtime]

CM 所需的是现有模型与 episode 路径上的窄测量入口，不是训练框架迁移：顺序处理图，使用现有 PyTorch 导数和张量运算，沿用已有 wall time／peak RSS 记录。按普通每尝试 2,000 新行、每 runner 600 行的工程边界，不新增 registry、guard、validator 或一般遥测框架；本卡要求的科学量就是输出表，不是新的平台设施。结果性调用仍要求 wsl_4070 remote-first、确切 committed-and-pushed 源码、detached supervision、执行节点新鲜的 physical/effective 至少 4 GiB 内存准入。源码接受和启动均不由本咨询代替。[工程范围规范][engineering]；[AGENTS §§2、5、8][agents]；[runtime]

## 七、训练法则、headroom 与家族上限

两次结果降低的是“在这两个种子及各自 200-update 固定范数设置下，已有学习包能得到可用服务学习及持久-重键差异”的可信度。它们没有证明所有固定范数 SGD 无效、归一化原则错误、TBCFV 不可学或持久公共状态无价值。定义卡中的原法则仍是原对象的冻结法则，B02 是独立具名改动；本 A 不改任何训练法则。函数类含括仍成立，但尚未得到一个具备有用绝对学习能力的稳定包比较。[host]；[card]；[direction：2026-09-01 recast]

**可以形成 Portfolio 用途的诊断性 headroom 记录，但不能声称 H_A1 已识别。** 同一 B02 面板上，脚本参考的两路径 U 均值约 0.28215，而两学习臂约 0.70700，差约 0.425；这是特定已实现行为相对于这些学习结果留下的具体改善空间，不是最佳可达性能减去已调优通用学习器的 headroom。参考不是数值上参考，两包也没有成为 competent tuned generic baseline。τ 本身同时接近失败码上限，说明恢复指标的分辨力也应写入记录。B01 没有 B02 那样的共享初始化评估，不能把两个对象都叙述成有独立初始化面板。[reference]；[cost]；[b01]；[经验规范 §11.7][spec]

这份记录用于保留机会、失败和未知，不是新增投资阈值，不据此改变方向生命周期、容量、优先级、融合或注册。前身宿主的 B1/B2/CPC 极性及已关闭的信息必要性分支不迁移，也不重开。**最终选择仍只有上述一次冻结状态 A；完成或损坏后都停止本次支出，不自动启动其他对象。**

## 实际访问与未验证范围

任务读取自 `4eebef120498d85d5d32fa73eaf33b45cc441bb9` 的指定 TASK.md；科学证据均使用该任务声明的 `f6ba67cd7cb2b249057e08278eaf78ee72c4463e`。已读取所列结果／科学卡／CM／intake、上一轮答复的相关合同与读法、models/config、宿主与方向记录、研究映射、相关规范及协作文件；本轮三个 packet 文件均可读取，没有沿用先前错误 pin 的 404 作为当前缺口。[task]；[options]；[cost]；[snapshot]；[map]；[collaboration]

两个大型学习臂 summary 的 Contents 接口返回 `encoding=none` 和 blob 身份；通过 blob 接口成功取得了编码内容，但本咨询没有独立解码重算全部 200 条曲线和所有逐情景行。上述聚合数字及差异计数使用任务中列明的机器派生 EXPOSURE_AND_COST.json 与接受结果 intake，并直接读取较小的 reference summary。不能把这写成独立逐位复现、参数文件读取或梯度分解已经执行；现有分解缺失正是本 A 的测量目标。[C1P1 summary][c1]；[FLEX summary][flex]；[cost]；[result]

Issue #8 正文和全部已返回评论已通过 connector 读取；评论复核观察时间为 2026-09-06 19:13 左右（America/Los_Angeles，UTC−07:00）。读取时只有 [first-B r02 评论](https://github.com/CartmanFatass/My-paper-code/issues/8#issuecomment-5560789984) 和 [post-B01 评论](https://github.com/CartmanFatass/My-paper-code/issues/8#issuecomment-5562367990)；它们是可变讨论的链接，不是新科学证据。Issue 正文中的“尚未执行”是旧状态描述，不能覆盖固定提交中的 B01／B02 结果。没有跟随未列出的讨论或文件链接。

本咨询新增的模型、环境状态、transition、forward、backward、optimizer step、测试和实验均为零；只交付这份方向决定。未来 A 的非零模型／环境／反向测量曝光已在上文单列，不能与本咨询的零曝光混写。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/4eebef120498d85d5d32fa73eaf33b45cc441bb9/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b02_innovator/TASK.md
[result]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B02_NORM_0P02_RESULT_INTAKE_20260906.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B02_NORM_0P02_SCIENCE_CARD_20260906.md
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md
[b01]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B01_RESULT_INTAKE_20260906.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_POST_B01_INNOVATOR_INTAKE_20260906.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b01_innovator/archive/RESPONSE.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b02_innovator/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b02_innovator/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b02_innovator/ISSUE_SNAPSHOT.json
[c1]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/b02_tbcfv_norm0p02_20260906/c1p1/summary.json
[flex]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/b02_tbcfv_norm0p02_20260906/flex/summary.json
[reference]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/b02_tbcfv_norm0p02_20260906/reference/summary.json
[models]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/experiments/candidates/roster_consistent_latent_exploration_tbcfv/models.py
[config]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/experiments/candidates/roster_consistent_latent_exploration_tbcfv/config.py
[host]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/candidates/roster_consistent_latent_exploration/DIRECTION.md
[map]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/RESEARCH_MAP.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/AGENTS.md
[collaboration]: https://github.com/CartmanFatass/My-paper-code/blob/f6ba67cd7cb2b249057e08278eaf78ee72c4463e/docs/project/GITHUB_RESEARCH_COLLABORATION.md
