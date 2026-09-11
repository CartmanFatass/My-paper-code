**继续现有首次合法应用时的 RETAIN/COPY/SHADOW 探索家族，但下一笔投入只选择一个修正接口上的 B03 双臂真实学习比较：CONTROL 对 FORECAST_PACKAGE，一个新的配对训练种子，每臂十六次更新。不是 RECAST，不先购买旧检查点的零训练见证，也不把 B02 当作已修复后重跑。** 理由不是“来源价值尚未被检验”本身，而是一个具体、已观测的动作交付障碍已经在限定范围内被排除：新的普通边界使当拍许可与 native 准入一致，并使有区别的新命令实际进入 held 状态。现在值得直接观察，重新在这个边界上训练的联合预测包，是否比同边界上的原学习器产生有用的原生服务增量。[A02 intake §§2–5][a02-intake]；[前次完整裁决 §§3–6][previous]。

本次选择的最窄单位是**修正普通接口下、固定小预算的预测包性能比较**，不是来源机制确认。两臂都采用已经接受的修正；差分处理仍只有 B02 的联合预测监督与服务概率接口。新结果最多支持一个训练样本、四个开发条件上的探索性包性能信号。它不证明接口修正有服务价值，不解释 B02 的零差异，也不证明校准、稳定优越性、通用接力或 SHADOW 的独立价值。选择不是源码接受、实际启动或 Portfolio 动作。

## 一、已知事实、最强反证与必须保留的边界

这里的 A02 指普通续约边界修正，不是早先同后缀的地面源点诊断。完整机器摘要给出：同一个 seed-61 FORECAST_PACKAGE update-16 检查点、两个新鲜循环状态、两个初始 32-tick 窗口，参数范数前后均为 39.149200792042365；没有训练转移或优化器更新。主一致性检查是该步实际 native 输出的 `renew_completed` 与步前策略消费的许可相比较，而不是两个从同一 countdown 复制出的布尔量相互证明。[A02 summary：configuration、primary_agreement、windows、exposure][a02-summary]；[A02 CM record：Finding 1][a02-cm]。

| 已观测量 | K8 初始窗口 | K4_TO_K12 的初始 K4 窗口 | 总计 |
| --- | ---: | ---: | ---: |
| 活跃完成 tick | 32 | 32 | 64 |
| 策略许可与该步 native 输出一致 | 32 | 32 | 64 |
| 两类许可不一致 | 0 / 0 | 0 / 0 | 0 / 0 |
| 准入且新命令按独立投影进入 held | 4 | 8 | 12 |
| 匹配非续约 | 28 | 24 | 52 |
| 准入外 held 改变 | 0 | 0 | 0 |
| 原生服务 tick | 30 | 30 | 60 |
| 合法 CAS | 0 | 0 | 0 |

这些总体数取自完整摘要和已接受 intake；本次直接核读了两窗口的原始边界例子，并未重新执行一个逐行重算程序。例如 K8 的 t=4 发出 `[-1.1995564699, 1.5664017200, 1.0252064466, -0.4977449477]`，实际 held 为 `[-0.9120000299, 1.1909055149, 1.0252064466, -0.4977449477]`，与独立投影一致；初始 K4 的 t=2 也有相应的非零、非 value-equal 准入，下一非准入 tick 的 held 不变。投影口径取卡片明确的**每机二维向量**限幅：原始模长 3、变化模长 1.5、结果模长 3；不把 intake 中“per component”的例句当作新的按分量投影定义。[A02 rows：window 1 t=4–5、window 2 t=2–3][a02-rows]；[A02 card §§2–4][a02-card]。

**最强的反向事实仍是：动作被交付后，短窗服务没有增加，而能量增加。** 服务依然是 60/64；能量增量总和为 9220.97，旧 A01 对应记录为 8563.59。无提前终止、硬事件或 CAS。DM 的“服务会不同于 60”子预测错误，不能因接口验收成功而删去。它提示实际执行旧策略的动作可能只增加支出，但不是对重新训练的 B03 学习器的判决。[A02 intake §§2–4][a02-intake]。

验收范围也不能扩大。第二个窗口只观察到初始 K4，摘要中的切换 tick 是 360，而窗口只有 32 tick；两个窗口都没有覆盖退化起点 420。prepare/commit 的策略采样已落在许可 tick，但这不等于原生准备锁存、intent、证书和 CAS 的完整门链已经获得经验验证。当前不存在修正路径上的完整学习表现或所有时钟情形的正确性结果。[A02 summary：windows.reset][a02-summary]；[前次裁决 §2“Prepare/commit”及 §4][previous]。

B02 的反证同样保留：两臂各 65,536 条普通训练转移、512 次优化器更新，参数都有非零且不同的移动；最终四行仍是每臂 572 / 447 / 433 / 428，均值 470，差分全为零。包臂曾出现很大的有限每更新平均损失峰值 7,423,381.7265625 和裁剪前梯度范数均值峰值 22,054,892.236206055。修正调度许可没有证明这些优化困难消失。MSE 与 NLL 数值不可直接比较为预测准确率；各自训练数据上的 BCE 也不是匹配校准观察。[B02 intake：Reading rule、Real learning][b02-intake]。

**限定重释继续按前次裁决，而不扩大其证据范围。** B02 的原始数值、真实学习计数和 inside-MEI 读法保持为已执行接口下的结果；不得隔离整项结果，也不得说“时序解释了零增益”。重释文中“新运动从未被采纳”用于完整历史 B02/B01 时，必须连同来源说明：两窗口上的未采纳是测量，历史训练及其他未经观测路径上的推广仍是源码支持的推断，不是新测出的全历史事实。B01 的不同 prepared 决策路径尤其不能由两个 B02 窗口替代。前次裁决明确作了这项限制；本轮不重跑、不重算或改写旧结果。[限定重释 §§1–3][reinterpretation]；[前次裁决 §4][previous]。

## 二、B03 的单一问题、处理和最强现有对照

**类别：B / EXPLORE。问题：在已修正的普通动作边界上，从匹配初始化开始，以相同小训练暴露学习，联合预测包能否相对原学习器提高完整普通 episode 的 native 服务？** 它保留来源研究的后续可能性，但当前不是来源干预实验。

两臂均用 `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`，按 B02 卡片第 2 节的既定地面终端宿主：地形参考的两米地面发射器/视觉目标、地面关联射线的线性净空、实际端点距离、不变的 UAV/base 高度及其余物理和协议。普通训练、私有标签生成与评估必须绑定同一宿主。没有新的高度、阈值、奖励、信息或动作空间改动。[B02 card §2][b02-card]。

| 部分 | FORECAST_PACKAGE | CONTROL |
| --- | --- | --- |
| 服务预测到 native 的接口 | 对 FP32 原始 logits 做 sigmoid 后转入 native 概率输入；训练仍对原始 logits 做 BCE-with-logits | 原始 logits 接口及原训练 BCE |
| 四维预测监督 | 同时训练既有 mean/Cholesky 输出，使用普通四维 Gaussian NLL | 既有按坐标平均的 mean MSE |
| 预测项权重与支持 | 有效系数 0.025；同四个循环副本、同 `next_mask` 法则 | 同系数与支持法则 |
| 普通时钟边界 | 当前 countdown 的许可；完成转移标志另存 | 完全相同的修正边界 |
| 其余算法 | 保留 PPO、AdamW、学习率 3e-4、裁剪、其他辅助项、服务标签法则、循环重放、归一化 | 同样保留 |

NLL 仍为 `0.5*((y-mu)^T Sigma^-1 (y-mu)+logdet(Sigma)+4*log(2*pi))`，协方差沿用既有下三角顺序、对角 `softplus(raw)+1e-3` 和 `Sigma=L*L^T+1e-4*I`。它与坐标 MSE 的尺度本就不同；本轮不同时调系数、截掉极端梯度记录、另换目标、删减标签或增加课程。那些是别的科学处理，不能伪装成这次接口修正后的自然延续。[B02 card §2][b02-card]。

CONTROL 是当前有根据的、同信息同训练暴露的完整对照，而非已调优的最优基线。不能故意让 CONTROL 继续使用滞后许可来制造差分。未得到调优 headroom 限制的是“优于强泛用算法”“接近上界”等措辞，不是这一次命名比较。[B02 card §§1–3][b02-card]；[证据规范 §§11.7–11.9][method]。

实际因果与学习链为：**路线/退化事件 → 两物理 agent 的角色相关因果观测与真实消息 → active/shadow 循环状态 → 当前许可下的运动及 prepare/commit/预测输出 → 不变 native 投影、协议门与服务 → 普通收集的奖励、行为概率和辅助标签 → 循环 PPO/backward/AdamW → update-16 检查点的普通原生后果。** 改动协方差还会影响快照反馈；改善服务可以完全来自 incumbent 行为或共享表示，而不经过合法换主。[B02 card §§2–4][b02-card]；[A02 card §2][a02-card]。

privileged next-state 标签和私有服务标签 clone 继续只是训练监督；其内部显式 promotion 不是实际合法接力，不能填补 CAS 支持。原生准备、intent 和 CAS 门不得强制通过。[B02 card §2][b02-card]。

DM 选项文档把固定伙伴协议进一步表述成“没有 partner co-adaptation”，这一排除不由当前材料支持。固定协议不等于固定所有伙伴策略输出、共享表示或角色状态来源之间的学习关系。本轮不引入额外伙伴交叉实验，但保留检查点/共享状态共适应这一解释，不将其宣布消失。[选项说明首段][options]；[B02 card §2][b02-card]；[DIRECTION 的 B02 解释][direction]。

## 三、种子、参照行和有限暴露

**选择新的配对种子 73，不复用 seed 61。** 在 B03 自己的命名空间中，一次写定 ASCII `DISH-FORECAST-PACKAGE-B03/seed/73` 的 SHA256 为新 master，沿用既有 master-addressed 生成方法；本次只指定法则，没有生成训练根或加载模型。数字不是通过结果挑选的，也不要求寻找更有利的 seed。B02 的 seed-61 master、检查点和结果均不作为 B03 输入。

两臂从这一新根获得匹配初始参数，底层均为 STRUCTURED；输出臂名不能选取不同 RNG 子流。保持语义坐标上的公共外生随机性，各自持有演化中的 native、optimizer、recurrent 和 normalization 状态。匹配的是初始条件、抽样法则与工作预算，不是强迫后来轨迹、标签支持、提前终止或耗时相同。既有 seed-61 可以用于另一个明确的同随机根接口敏感性问题，但不是本轮购买的独立训练样本。新种子也不会使适应性设计变成独立确认；它只提供不复用旧根的训练观察。[B02 card §3][b02-card]；[证据规范 §11.8.3][method]。

**不加入不学习的 held-only 参考行，也不先评估旧双臂检查点。** held-only 对照回答“学习的控制是否优于不更新 held”，不是当前包相对原学习器的增量。省略它意味着不能声称优于 held-only、不能量出绝对学习价值或把旧 B02 当成这样的参考。旧检查点在修正路径上的好坏，又不能替代从修正交付下重新训练后的比较。当前没有一个必须依赖这项旁测才能改变的 B03 选择；因而不将它写成可随手追加的免费观察或先行门槛。DM 提出的“秒级”也只是外推，不是该完整旁测的实际成本。[选项说明 1–4][options]；[成本记录 prospective_option_2][cost]；[证据规范 §11.9][method]。

| 工作 | 每臂 | 完整双臂 |
| --- | ---: | ---: |
| 新独立训练样本 | 同一个配对 seed 的一个臂 | 一个配对训练样本，不是两个独立 seed |
| 完整更新 | 16 | 32 |
| 普通训练转移：32 lane ×128 tick ×16 | 65,536 | 131,072 |
| 优化器步：4 epoch ×8 minibatch ×16 | 512 | 1,024 |
| 评估检查点 | 仅 update 16 | 每臂一个 |
| 普通评估 episode | 4 | 8 |
| 最大普通评估 tick | 4,800 | 9,600 |

训练保留 B02 的 32-lane reset/population、片段与循环重放结构。评估仍为两退化包 `TARGET_VISUAL_MASK` / `TERRAIN_RELAY_MASK` 与 `K8` / `K4_TO_K12` 的四个组合，speed 4、slot 0、block 0，配对外生随机性，普通确定性策略动作。每行固定 1,200-tick 回报范围；native 终止即停止实际 stepping，其未执行余段在固定范围的服务和中为零，同时保留实际完成 tick 和终止原因。若合法换主发生，普通评估继续；不调用首次触发 fork evaluator 或标签 clone 充当评估。[B02 card §§3–4][b02-card]。

实际训练计数、每更新曲线、初末参数范数/位移、优化器步数和评估暴露都必须来自新运行，不能用上表的名义乘法替代。保留每臂实际 `next_mask` 与服务标签 eligible 数；它们记录当前支持与成本，不设“支持率必须过线”这一额外门槛。四个评估条件不是四个独立训练样本；单 seed 不能估计训练总体方差，也不能通过对四行 bootstrap 补出来。[B02 card §§3–5][b02-card]；[证据规范 §§5.2、11.8.3][method]。

## 四、主测量、读法继承与改变

令 `J[a,r]` 为上述固定范围内实际 native 服务指标之和，主测量为：

`Delta_B03 = (1/4) * sum_r (J[FORECAST_PACKAGE,r] - J[CONTROL,r])`。

**MEI 保持 +24 平均服务 tick，即 1,200-tick 范围的 0.02、2.4 秒服务。** 不是相对观测 CONTROL 回报的 2%，也不是 A02 时钟一致性分辨率或 B01 来源 MEI。所有四行、两臂均值、能量与七类 hard events、终止情况、合法换主数和换主前后服务都保留；不按是否触发或符号筛选。[B02 card §§4–5][b02-card]。

B02 的下列读法结构照搬，但其对象、数据和解释范围改为 B03：

| B03 观察 | 读法及下一选择 |
| --- | --- |
| 主差分至少 +24，且没有压倒服务价值的能量/事件代价 | 修正接口下的有用包性能投资信号；可考虑另行预算的一至两个新独立配对种子，不要求每行或每个未来 seed 都为正。不是稳定优越性或来源归因。 |
| 差分在有用效果尺度内，或四行明显异质、结论混合 | 本预算/条件下未建立清晰实用增益；保留完整模式，不宣称等价，不自动延长训练或补到全正。下一改动必须有具体依据。 |
| 原生服务下降、hard event 或不利能量/服务交换 | 无论 NLL、BCE、q95 或证书通过率如何改善，都保留 adverse 结论；不能用代理量给包续费。 |
| 没有普通合法换主 | 不否定完整 episode 的包性能读数；正信号只能称 incumbent-only，来源差分仍未估计。 |
| 出现普通合法换主 | 是新机会/行为观察，不是 SHADOW 优势；COPY–RETAIN 和 SHADOW–COPY 仍需以后另选匹配来源干预。 |
| 任一臂缺失主测量、关键训练暴露或完整既定工作 | 不能称完整十六更新双臂结果；明确受损依赖，保留可信的较窄事实和真实失败，不替换 seed 或补出缺行。 |

这里没有新的普遍非劣界或 hard-event 加权分数；不利交换按真实类别和数量报告，不藏入总分。时间上发生于换主之后的服务不自动等于由新 owner 发出的 packet 服务；没有直接包来源记录时，停止在时间描述层，不增加 ABI 或全轨迹归因要求。[B02 card §§4–5][b02-card]。

需要改变的不是 MEI 或结果极性，而是以下语义：**两臂现在共同采用修正许可、新 seed 与新训练；比较结果只属于这个新组合。** 不要求重现 572/447/433/428，不将 B02 与 B03 合并为同一算法的两个独立重复，不把两轮均值相减当作时序修正的因果效应。这样相减会混入种子、学习轨迹和执行接口等变化。原 B02 的 inside-MEI 观察继续存在；B03 无论正负都不能翻转它。[限定重释][reinterpretation]；[前次裁决 §4][previous]。

本次前瞻判断是：**出现非零命令交付有根据，出现至少 +24 的包优势没有可靠先验保证；inside-MEI、混合或 adverse 仍是认真对待的结果。** 这不是自动沿用 DM 旧预测，也不是要求未来观察服从该判断。记录新对象预测，owner 未作预测时保持“未取得”，不能替其填写。

## 五、启动前检查：不再买一个 A，但不能夸大已有覆盖

**不需要先补训练侧历史滞后测量、重跑 A02 窗口、旧检查点完整评估、全部时钟 census 或新的校准实验。** 前次裁决已经明确：旧训练侧只作源码支持推断，修正的前瞻传播可由聚焦边界/片段检查确认。A02 CM 记录中的测试已经调用真实 `NativePersistentTrainingFlow._fragments` 来检查 `renew`、`prepare_mask`、`commit_mask` 的传播，而不是本地仿造同名张量；它是工程覆盖，不是历史训练测量。[前次裁决 §4][previous]；[A02 CM record：Finding 4][a02-cm]。

新 B03 只需现有规则要求的一次与本次改动和主输出相关的聚焦验证，复用 B02 与 A02 的可信覆盖：新 seed/对象绑定确实生效；两臂都走修正普通边界；forecast 标志、NLL/raw-BCE、host/passive-label 绑定在更新和最终加载后不丢失；策略侧许可、行为概率和新片段 masks 同拍；固定范围服务归约、终止和输出仍然正确。若这些组合在同一实际配置的已接受字节上已有可信验证记录，就复用，不因“现在要启动 B03”再执行一轮 smoke。[B02 card §7][b02-card]；[证据规范 §11.8.6][method]。

**但不能把“11 个 A02/A01 测试加 64 个 r06 测试通过”直接写成“B02 的聚焦 profile 已在修正组合上通过”。** 列出的 CM 记录还保留了 Windows 上 `test_package.py` 因 `resource` 模块缺失而未能收集的事实；它不是 Linux 科学路径已经失败，也不是该 profile 已通过。若没有现成的目标环境当前组合覆盖，在同一次必要聚焦检查中补上实际缺项即可，沿用配置中的 `wsl_4070`，不 stub 掉关键依赖来宣称覆盖。无需新 A、无额外审批层或整套历史重验。[A02 CM record：Focused tests][a02-cm]；[A02 intake §1][a02-intake]。

同理，CM 记录注明 `complete_b01_tick` 返回 `self.observe()` 的继承性覆盖，以及 TEST-only rollout fixture 的 mask 位移；因此本轮不声称所有 prepared 返回值或旧技术绑定都位级不变。它也明确 B01 实际 prepared 决策解码和 clone 解码未改。这些已限定的消费者差异不能被偷换为 B03 普通学习必须先完成全旧路径审计的理由。[A02 CM record：Finding 2、Consumer map、Exact lines][a02-cm]。

若新组合真的暴露奖励、信息、训练或主测量的具体错误，处理该依赖而不是继续宣称完整结果；若只是可选资源细项未观测，就保留其窄范围缺口。不存在“必须先证明训练无任何问题”或“必须有合法 CAS 才能开始 B”的新条件。[证据规范 §§4、11.4、11.8.7][method]。

## 六、完整工作、成本依据与停止边界

复杂度由**两臂 ×一个配对训练 seed ×十六更新 ×32×128 普通 tick，及每臂四个最终 episode**主导。没有策略搜索、候选轨迹树、来源 fork、上界求解或额外检查点搜索；但保留的标签算法确有嵌套 native 工作，不能只数普通转移。

对每臂，令 `N=65,536`，`E` 为真实服务标签 eligible 转移数，`H` 为对应实际后果 stepping 总数：

`W_native_train = N ordinary + N next-label + 2E delay + H consequence = 2N + 2E + H`，

`0 <= H <= 20E，E <= N，因此 W_native_train <= 24N = 1,572,864`。

再加最多 4,800 普通评估 tick；循环/critic 前向、四轮八 minibatch 的 PPO 重放与 backward、优化器、额外物理读出、初始化、编译、必要检查和发布仍另外计入完整工作。上界不是一个实测 wall 倍数，也不是每次实际执行的步数。[B02 card §6][b02-card]。

保留全部 next-label 与服务-label clone 工作，因为它们是本次选定学习目标的组成，不是可以删去的“诊断开销”。`H` 的现有接口不提供完整读数时仍为未测；记录实际 `N/E` 及 `H<=20E`，不为这个可选成本细项增加 native ABI，不把上界填成实测值。旧 B02 对应两臂的 native 训练调用界为 148,354–321,174 和 148,370–321,350；这不是对新 B03 的预测。[B02 intake：Whole work][b02-intake]。

### 现有计时可以怎么用

| 已完成工作 | 已测范围 | 本轮可用含义 |
| --- | --- | --- |
| A02 formal / check | runner 约 0.092 / 0.064 秒；formal RSS 363,364,352 bytes | 原接受窗口的计时，不是冷启动全学习或 4,800-tick 旁测的单位成本 |
| B02 shared focused check 及准入 | 6.83 秒外层 wall，6.71 CPU-s | 一次历史共享准备，不是未来编译/检查的保证上界 |
| B02 CONTROL | 完整臂调用 337.23 秒，分摊后 340.645 秒 | 该旧接口、旧 seed、实际 eligible 数下的整臂参考 |
| B02 FORECAST_PACKAGE | 完整臂调用 298.60 秒，分摊后 302.015 秒 | 同样仅为历史整臂参考 |
| B02 全对 | 642.66 秒外层 wall、669.61 aggregate CPU-s | 不是单臂数，不是新执行设计的速度证明 |

来源：[A02 summary][a02-summary]、[A02 intake §1][a02-intake]、[B02 intake：Whole work][b02-intake]。

**不能用“修正不增加计算工作”推出 B02 可直接充当每臂可靠投影。** 不变的是普通转移和优化器的名义规模及标签工作公式，不是实际 `E/H`、轨迹终止、消息/预测状态或每阶段耗时。修正已经改变动作和提案发生时刻；这可改变标签 eligibility 与 clone 后果数量，不只是一点 wrapper 开销。成本记录把未知变化缩成“marginal”也没有观测根据。[A02 card §2][a02-card]；[成本记录 prospective_option_1][cost]；[B02 card §6][b02-card]。

所以，B02 可作为**注明边界的规划参考项**，但不能把 642.66 简单除以二、按核心数相除、固定旧 `E`，或把 24N 上界与旧 wall 拼成完成保证。CM 在现有技术记录中用新对象完整工作公式、可复用的真实计时和明确未知项说明规划；没有新的匹配全调用测量这一事实继续可见。未知不填零，不要求另买校准实验，既不能自动拒绝普通 B，也不能无视直接证据已经建立的超限。[runtime General requirements §§2–3、7–8][runtime]；[证据规范 §11.9][method]。

### 新支出选择

**本次重新选择每臂完整计算 wall 上限 1,800 秒，两臂分摊后 wall 总额上限 3,600 秒。** 这不是 B02 或 A02 的余额，也不是保证实际花费或完成可行性的预测。确有一次共享准备成本 `C` 时，只收费一次，预先按每臂 `C/2` 分摊，每臂独有完整调用余量为 `1800-C/2`；拆脚本、训练/评估阶段或切片不重置上限。计时包含实际支付的 import、专属 build/load、初始化、学习、必需检查、评估和发布。Git/代理/SSH控制与外部排队等范围分开说明，未测不填零。[B02 card §6 的成本分摊法][b02-card]；[runtime §2][runtime]。

采用既有单线程 CPU、FP32 学习/float64 native、tensor/native batch 与远程优先执行，不选择新 worker team、设备扫描、并行速度实验或新遥测服务。只要求普通范围的完整 wall 与有清楚范围的 peak RSS；既有工具若在其适用范围提供 CPU 累计，可如实保留，缺失则不声称完整 CPU 成本或 CPU 上限合规，不因而抹掉可信服务事实。每个实际 invocation 前执行节点的 physical/effective memory 都须新鲜测得至少 4 GiB，精确已提交/推送源码、detached supervision 和既有路由保持。[scope §§3–5][scope]；[runtime §§4、6–8][runtime]；[AGENTS §§5、7–8][agents]。

每臂在十六次完整更新、四个最终评估和发布完成时结束，或在其完整 wall 余量耗尽、发生威胁学习/主测量的实际失败时停止。普通 episode 的坏行为或 native 提前终止按终止语义保留，不因回报不好更换该行，也不进行效果驱动的提前停止。未完成时不得拿早期较佳检查点代替 update 16；不补 seed、不恢复续费、不自动 retry、不扩 cap。一个臂受损时保留另一臂及所有可信部分，但不伪造配对差分。直接工程事实显示预算内不能实现本对象时，返回具体缺口，不静默缩短标签、删对照或减少既定暴露。

| 保留或省略的负担 | 它服务的当前决定 |
| --- | --- |
| 真实普通 native、policy、learner、trainer、evaluator | 判断新接口下这个联合包的有限预算性能，而非合成输出是否改变 |
| 原标签 clone 与 PPO 重放 | 本次学习目标与更新法则本身；完整计费，不叫历史重构 |
| 四行主结果、每更新曲线、参数/优化暴露、事件和终止 | 读出两臂差分、失败、异质性和实际学习；不需全 hidden/trace dump |
| 一次与改动相关的现有聚焦检查组合 | 防止许可/variant/主输出在新对象接线时丢失；不产生另一学习样本 |
| 历史训练回放、旧 checkpoint 零训练见证、held-only 行 | 本轮不购买；放弃历史全路径归因、旧策略反事实与绝对 motion-vs-hold 主张 |
| 来源 forks、deadline replay、校准、调优上界、全 schedule/support census | 延后到确实提出对应更强问题时；缺失不阻塞当前包性能 B |

## 七、为何不暂停或转向另一个家族

暂停是可合法考虑的投资判断，并非只有证明机制无效才能暂停；但此刻更合算的选择是上述一对有限比较：有一个已观察到具体动作交付的普通路径，也有已经跑过真实学习与主测量的成套对照设计，可以直接回答新的包性能问题。这个理由比“尚未检验就必须继续”更窄，也不构成无限后继额度。

改做 motion-vs-hold 会更换当前处理与比较目标；本轮没有必要为它放弃仍可清楚提问的联合包问题。即使以后这种对照有价值，也不因控制名称不同自动构成一个新家族，本轮不执行 RECAST。零训练旁测则回答旧策略的执行后果，不能代替修正路径的实际训练；它没有获选，不能作为额外工作随 B03 附带启动。[选项说明][options]；[证据规范 §§11.8–11.9][method]。

残余不确定性包括十六更新的实际能力、NLL 优化尺度、共同表示与快照反馈、准备/证书/意图门、真实换主机会以及训练样本差异。COPY、RETAIN 或 deadline replay 仍可能足够，即使包服务改善也如此。旧 R02 关闭不变；B01 触发不足、早期 A03–A05 和 B02 的限定结果不被替换；其他 N3 来源不合并。本次不改变 Portfolio 生命周期、优先级、容量、融合或注册。[DIRECTION 历史关闭、B01、A03–A05、B02 及 A02 章节][direction]。

## 八、证据访问与本次未验证项

仓库证据均经连接的 GitHub 读取动作取得，固定在 `a0be9f02aced95928519f61d5cd9143a68897843`。只读取任务列出的科学证据；没有跟随其中未列出的源码、旧附件或其他 ref 链接。下面 C/ 表示 `docs/research/candidates/degraded_incumbent_shadow_handover/`，P/ 表示 C/ 下 `pro_packets/20260906_post_a02_convergence/`。链接均指向该固定证据版本。

| 实际读取路径 | 范围 |
| --- | --- |
| [C/DISH_RENEWAL_BOUNDARY_A02_RESULT_INTAKE_20260906.md][a02-intake] | 完整 intake |
| [C/DISH_B01_B02_QUALIFIED_REINTERPRETATION_INTAKE_20260906.md][reinterpretation] | 完整限定重释，按前次裁决限制全历史推广 |
| [C/a02_renewal_boundary_20260906/formal/rows.json][a02-rows] | 原始窗口例子：请求行 1–350、351–1050、2170–2500；第二段返回被截断。直接包含 K8 t=4–5、初始 K4 t=2–3；未声称全部 64 行独立重算 |
| [C/a02_renewal_boundary_20260906/formal/summary.json][a02-summary] | 完整机器摘要；总体计数的直接来源 |
| [C/DISH_RENEWAL_BOUNDARY_A02_CORRECTION_SCIENCE_CARD_20260906.md][a02-card] | 完整卡片 |
| [C/DISH_RENEWAL_BOUNDARY_A02_CORRECTION_CM_RECORD_20260906.md][a02-cm] | 完整记录，经重叠读取补齐长命令尾部；只读、不执行 |
| [C/DISH_FORECAST_PACKAGE_B02_SCIENCE_CARD_20260905.md][b02-card] | 完整卡片，包括 H 可观测性说明 |
| [C/DISH_FORECAST_PACKAGE_B02_INTAKE_20260905.md][b02-intake] | 完整 intake，包括原四行、训练曲线极值及实际完整成本 |
| [P/EVIDENCE_AND_OPTIONS.md][options] | 完整建议，未作为已选实验接受 |
| [P/EXPOSURE_AND_COST.json][cost] | 完整文献性派生记录；未来成本措辞不视为测量 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 完整准备时快照与两条旧交付评论 |
| [C/pro_packets/20260906_post_a01_convergence/archive/RESPONSE.md][previous] | 完整前次裁决，重叠读取补齐重释段和引用尾部 |
| [C/DISH_POST_A01_CONVERGENCE_INTAKE_20260906.md][previous-intake] | 完整 intake |
| [C/DIRECTION.md][direction] | 行 217–305、350 至末尾：R02 关闭/重入、B01、A03–A05、B02、续约 A01/A02 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 行 45–125 的类别/完整性/B；315 至末尾的控制性 §11，含 §§11.8–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 普通 §§1–5；未借用后继不适用的对象附款 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][runtime] | General requirements §§1–8，经补读取得末尾；附带返回的 VNFC 专项未用于本决定 |
| [AGENTS.md][agents] | 正文及附录 A–C 完整读取；其中方法不扩大本任务写权限 |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md][delivery] | 完整交付说明 |

没有任何列出的证据路径不可访问。原始行记录是范围读取，不是全轨迹审计；本轮不额外取得未列出的 B02 机器文件或实现源码，关于其运行/实现的事实按上述卡片、机器摘要、CM/intake 和前次完整裁决的层级引用。新 seed 的实际训练、修正组合的完整学习表现和新完整耗时均尚未观察；这些未知不被本答复填成结果。

[Issue 4][issue] 正文与全评论接口实际可读；初次读取完成于 2026-09-06 16:08:54 UTC 之前，当时返回两条旧交付评论：[post-B02][comment-b02] 与 [post-A01][comment-a01]，不是本轮交付。固定快照记录的是 15:45:53 UTC 的准备时状态，两者区别保留；可变讨论未替代固定科学证据，也未跟随其未列出的材料。交付前另检查目标与评论，避免重复。

本次咨询未执行代码、模型构造、native 状态/转移、backward、优化器步、测试或实验。唯一外部改动限于所授权的完整答复文件和链接评论；没有执行 B03、重新验收源码或改写科学状态。

[a02-intake]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A02_RESULT_INTAKE_20260906.md
[reinterpretation]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_B01_B02_QUALIFIED_REINTERPRETATION_INTAKE_20260906.md
[a02-rows]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/a02_renewal_boundary_20260906/formal/rows.json
[a02-summary]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/a02_renewal_boundary_20260906/formal/summary.json
[a02-card]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A02_CORRECTION_SCIENCE_CARD_20260906.md
[a02-cm]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A02_CORRECTION_CM_RECORD_20260906.md
[b02-card]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B02_SCIENCE_CARD_20260905.md
[b02-intake]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B02_INTAKE_20260905.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a02_convergence/EVIDENCE_AND_OPTIONS.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a02_convergence/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a02_convergence/ISSUE_SNAPSHOT.json
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a01_convergence/archive/RESPONSE.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_A01_CONVERGENCE_INTAKE_20260906.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[method]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/AGENTS.md
[delivery]: https://github.com/CartmanFatass/My-paper-code/blob/a0be9f02aced95928519f61d5cd9143a68897843/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[comment-b02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
[comment-a01]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5558729980
