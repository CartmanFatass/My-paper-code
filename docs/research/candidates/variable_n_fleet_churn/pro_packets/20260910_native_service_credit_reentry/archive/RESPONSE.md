**选择（a）：仅开放 `VNFC-N7-NATIVE-SERVICE-CREDIT-B02` 的一次新训练对，以两个同构、同初始张量的 MAPR-4，比较原生服务区间信用 INTERVAL 与既有终点信用 TERMINAL。证据类为普通 B/EXPLORE；接受本提案的 900 秒完整机器工作边界，其中完整双臂原生调用最多 600 秒，全部支持机器工作最多 300 秒。** 这不恢复原样 MAPR–DIRECT 补种子，不重开部署方式比较、E01 或 R03，不增加第三次 recast，也不改变 Portfolio 的生命周期、优先级或争用排序。

重开的最强理由，是上一轮未定义的“服务差”现在已经成为一个可检查、可训练、可用原生回报反驳的具体估计器：在不改变完整 episode 目标的情况下，只改变六个训练标签的时间分配，并与同一个实际学习算法的终点版本直接比较。所需整数累计量已经由原生 reset/step 接口提供，不必购买反事实轨迹、候选搜索或新的控制器输入。它回答的是“这项时间信用处理在既定训练预算上是否值得继续”，而不是重新估计旧架构间的小差异。[本轮 intake §2—§3][S1]；[原暂停决定第四、六节][S3]；[原生累计与交互接口][S10]、[S11]

**这是一项有限的科学选择，不是新处理已实现、已接受或已运行的声明。** 当前没有新增效果证据，也没有得到新调用或支持工作的实测耗时。以下处理、对照、信息边界和完整预算可以构成这一个普通 B；无需先证明精确 headroom、唯一信用瓶颈或获得阳性 pilot。若后续实现发现实际奖励、信息、对照或预算与这些定义冲突，应准确返回该冲突，不能以本决定为由静默替换干预。[现行证据规范 §4、§5.2、§11.8—§11.10][S13]

## 一、什么发生了变化，什么反证没有消失

已经接受的 B01 观察仍是两种子下的共同学习，而不是稳定的 MAPR 特有优势。

| 原 B01 的总体 `R_fail_60` 对照 | 第一训练种子 | 第二训练种子 |
| --- | ---: | ---: |
| MAPR 最终减初始化 | +0.204127604 | +0.199453125 |
| DIRECT 最终减初始化 | +0.188658854 | +0.195520833 |
| MAPR 最终减 DIRECT 最终 | +0.015468750 | +0.003932292 |
| MAPR 最终减固定 BCRH | −0.041822917 | −0.060911458 |
| DIRECT 最终减固定 BCRH | −0.057291667 | −0.064843750 |

MAPR–DIRECT 的区 1 差异换号；两学习器的最终四项原生指标在两个区的均值都低于 BCRH。DIRECT 的参数和残差确实活动，不能把共同增益解释成只有 MAPR 学会了恢复。两个训练种子的评价面板也不同，既有跨运行差异混合了训练和评价变化，不足以识别稳定优势或等价性。[两种子完整 intake，“Per-seed results and native tradeoffs”][S5]

后续固定策略的 SAMPLE–GREEDY 四个恢复差为约 −0.006536、−0.003646、−0.005599、+0.016901，四个总体 `J_ext` 差都为负。该执行方式问题已经按原范围结束。本轮不把它改判为评价错误，不再加温度、采样次数、面板或检查点，也不将“这一条路径没有可用信号”扩展为排除了所有执行或学习原因。[原暂停决定第二节及应用记录 §2][S3]、[S4]

**继续保留暂停的最强论点**是，当前不是一个已证严重延迟信用问题：只有六次决策，原终点信号在最早决策处的 lambda 权重为 `0.95^5 = 0.7737809375`，并未衰减到接近零；两个旧学习器已经显著改变了各自行为。旅行、角色获取、固定占用者和伙伴配合造成的后果仍跨越多个区间，按服务发生时间放置 reward 并不等于识别哪个早期联合动作或哪个 agent 贡献了它。近似 critic 可能已经吸收部分时间结构，也可能在新标签下学得更差。旧曲线不能证明已经收敛，更不能证明仅改时间信用就会缩小参照差距。[本轮 intake §2—§4][S1]；[两种子曲线解读][S5]；[实际 GAE][S9]

我仍选择这一次比较，而不是继续暂停，因为现在变化的是**问题的可判别性**，不是对改善概率的夸大。相同 MAPR、相同曝光的 TERMINAL 是直接回答该问题的真实训练对照；INTERVAL 只使用每条既有原生轨迹的计数增量。原生代码还给出一个具体时间错位：失败区主指标在 60 秒停止累计，而原终点标签在第六次决策之后才交给 GAE；INTERVAL 的失败区 reward 分量在后三个区间为零。这个区别可能影响有限信用估计，值得在实际回报上检查，但它不是对旧算法“有 bug”或旧差距原因的判决。[`gtick`、`ginteractive_step`][S10]；[`learning.update`][S8]；[`gae_terminal`][S9]

旧结论因此不被推翻：原 B01 架构比较族继续暂停；此次只开放已具体定义的时间信用子问题。缺少调优同信息上参照、已有两次 recast 和最低争用排序，都不是选择或拒绝该科学比较的依据。[原决定第三、六节][S3]；[当前方向与规范][S7]、[S13]

## 二、处理在完整目标上自洽，但不具有有限梯度等价保证

### 原生累计量和标签

沿每个臂**自己的完整轨迹**，令 `F_j`、`T_j` 为 reset 后及第 j 个 20 秒区间结束时的失败区、全任务已交付量，`j=0,…,6`。`D_F`、`D_T` 是该 episode 对应的正终点需求分母。采用 intake §3 的原定义：

\[
J=\frac12\frac{F_6}{D_F}+\frac12\frac{T_6}{D_T},
\qquad
r^{T}_j=\mathbf 1\{j=5\}J,
\]

\[
r^{I}_j=\frac12\frac{F_{j+1}-F_j}{D_F}
       +\frac12\frac{T_{j+1}-T_j}{D_T},\qquad j=0,\ldots,5.
\]

这不是假设一个尚不存在的环境测量接口。`GS` 的相应计数从零开始；`ginteractive_reset` 的 prehistory 调用 `gtick(..., accumulate=false)`，之后才处理成员损失并开始 post-loss 计数。`ginteractive_snapshot` 输出累计交付和需求；Python 的 `_interactive_dict` 已在 `fail_endpoint`、`total_endpoint` 中保留其整数分子、分母，reset 及每次 step 都可取得。每次交互 step 执行 20 个原生 tick，第六次后终止。以上是本轮直接读取的源码事实，不是对新收集实现的运行验证。[原生 `GS`、`gtick`、`ginteractive_snapshot/reset/step`][S10]；[Python `_interactive_dict`、`NativeInteractiveBatch`][S11]

由于 `F_0=T_0=0`，对同一条已完成轨迹直接得到

\[
\sum_{j=0}^{5}r^I_j
=\frac12\frac{F_6-F_0}{D_F}
 +\frac12\frac{T_6-T_0}{D_T}
=J
=\sum_{j=0}^{5}r^T_j.
\]

这是所给记账定义的代数推论。在当前 `gamma=1`、完整终止和相同原生评价规则下，保持的是同一轨迹的完整外部目标，不是两个训练后策略必定产生相同轨迹或相同回报。`gtick` 只在 `post_time<60` 时增加失败区主指标计数；因此 `F_3=F_4=F_5=F_6`，但 total 继续累计至 120 秒。处理不能改为各区间交付／各区间需求的平均，不能省掉后半程 total 服务、改变两个 0.5 权重或添加 bonus。[intake §3][S1]；[原生计分窗口][S10]；[原 B01 目标与完整终局][S6]

### 保留原 GAE/PPO 的哪些具体运算

两臂均在完整收集后使用本臂的旧价值预测构造目标：

\[
\delta_j=r_j+V^{old}_{j+1}-V^{old}_j,\quad
A_j=\delta_j+0.95A_{j+1},\quad
V^{old}_6=A_6=0,
\qquad Y_j=A_j+V^{old}_j.
\]

`Y_j` 是未经 advantage 归一化的 critic 目标；actor 才使用原函数归一化后的 advantage。保持旧值和目标的 detach、原零方差处理、采样动作的 forced-command PPO 重放、四 epoch／八 minibatch、AdamW 配置和梯度裁剪。原损失的 ratio clip 为 `[0.8,1.2]`，value 系数 0.5、entropy 系数 0.01；不能因新标签重新缩放、裁剪或换掉这些设置。TERMINAL 必须保留当前真实终点递推，不成为一个人为削弱的对照。[`training.py::gae_terminal/normalize_advantages/ppo_loss/adamw_decay_groups`][S9]；[`learning.py::update`][S8]

同一个原生 `J` 并不使有限 GAE 等价。为解释这一点，**只在同一假设轨迹、同一固定旧价值数组、归一化之前**作代数比较：

\[
A^I_j-A^T_j
=\sum_{k=j}^{5}0.95^{k-j}(r^I_k-r^T_k).
\]

完整 reward 和相同，并不让这些各决策处的加权和相同。实际训练中，两臂的 critic、状态分布、归一化及 PPO 裁剪随后还会分化，所以本式不预测最终差异的符号，更不是纯方差降低或有限训练等价证明。不额外给 critic 加一个抵消处理差异的势函数，也不为解释此式增加 lambda=1 的第三臂。[提案的明确限制][S1]；[递推源码][S9]；[基础资料关于目标、critic 与有限训练的区分][S14]、[S15]

### 信息边界不能被“同信息”三个字掩盖

终点分母只在 episode 完成后用于两个臂的训练目标，不能进入行为时的 actor/critic 输入、动作选择或中途更新。两臂都记录相同种类的累计快照以匹配收集工作；TERMINAL 的更新仍只用末步 `J`，INTERVAL 使用时间展开的标签。共同 world 是配对的外生输入，不意味着两臂后续物理状态相同，更不能互用对方轨迹的累计量。

因此，准确表述是**执行时的公开信息、网络和原始轨迹记录种类匹配，训练标签的时间信息有意不同**。不能声明全部训练信息相同，不能把未来正常化后的标签当成已经证明 Markov 的逐步 reward。观察值 critic 的闭合性、有限 bootstrapping 与共享 actor/value 表征均是解释限制；它们不妨碍用完整原生终点评价该明确算法配方。[intake §3—§4][S1]；[实际收集的 pre-action 输入与旧价值][S8]；[FOUNDATIONS §2、§4 与 RL 专题][S14]、[S15]

intake §4 所记 GAE/RUDDER 文献用于解释“完整 return”与“时间分配”不是同一个对象。本轮直接读取的是该阅读记录和列明基础段落，未另行打开原论文；不借其中定理宣称本宿主的梯度无偏、最优重分配或新颖性。B02 使用测得的原生增量，不移植 RUDDER 的预测网络或贡献分析，也没有完成多 agent 个体信用归因。

## 三、只开放这一对真实学习器及其固定读数

绑定结构仍是单次成员损失后的团队恢复：**执行实体丢失 → 幸存实体及角色责任变化 → 原有公开状态、合法 mask 和固定占用者约束 → 四 token 联合物理分配 → 本臂六个区间的原生服务记录 → 时间标签进入 GAE/PPO → 参数更新后的策略在新 episode 上产生完整原生后果。** 处理改变的是这一链条中的时间信用标签，不是成员事件、动作语法或时间抽象本身。[intake §3][S1]；[原生角色与 step 路径][S10]

两臂都是新的 MAPR-4：同一份新初始张量分别复制到 INTERVAL 和 TERMINAL，参数各 89,090，优化器状态独立；共同训练和评价 world，动作及 minibatch 用独立臂级随机流。只有一个新的配对训练抽取，不是两个独立训练种子。新 seed/master/namespace 的具体值按提案留给 DM 在新卡中确定，必须在问题相关运行前明确，不能加载旧 checkpoint 或按已见回报选身份。[intake §3][S1]；[机器计划计数][S2]

同构的 TERMINAL 是针对“这项信用改动是否有价值”最直接的合理对照：它真正训练，沿用已产生过学习的原更新法，不混入架构容量差异。原有 DIRECT 的正面学习与反证完整保留，但本轮不加第三个 DIRECT 臂；即使 INTERVAL 赢过 TERMINAL，也不能据此声称赢过新训练的 DIRECT。固定 BCRH 在同一个新评价面板上只执行一次，保持原生参考身份；它不是已证同信息上界，也不是训练标签或动作教师。[既有学习和对照边界][S5]；[本轮比较定义][S1]

| 选定工作 | 每个学习臂 | 整个新比较 |
| --- | ---: | ---: |
| 新 MAPR 模型 | 1 | 2，构成一个训练对 |
| 完整训练 episode | 64 轮 × 32 = 2,048 | 4,096 |
| 训练 joint transitions | 2,048 × 6 = 12,288 | 24,576 |
| optimizer step／backward | 64 × 4 × 8 = 2,048 | 4,096 |
| 固定 0／32／64 轮评价 | 3 × 64 = 192 episode | 384 episode |
| 固定 BCRH 参考 | 无训练 | 64 episode／384 完整调用 |
| 所有完整 episode | 2,240，不含参考 | 4,544，含参考 |
| native ticks，含 prehistory | 537,600 | 1,090,560，含参考 |

这些是本轮采纳的计划，**不是已执行曝光**。每轮训练两区各 16 episode，评价面板两区各 32；训练与评价分别来自新的随机域。共享外生 fixture 的数量是 2,112，而不是把 4,544 次各臂／各 checkpoint 的完整执行都称为独立 world。机器记录中的 collection batch forwards 为 768、optimizer forwards 为 4,096、evaluation batch forwards 为 36；重复 PPO 使用不是新增环境数据，四 token 或七个幸存者也不是独立训练样本。[计数 JSON 的 proposed_B02_unselected 字段][S2]；[真实收集与更新循环][S8]、[S12]

两个学习臂的三个 checkpoint 都使用现有逐 token 贪心评价，round 64 是唯一 primary。主要量为该面板上的

\[
\widehat\Delta_R=\frac1{64}\sum_{i=1}^{64}
\left(R^{I,64}_i-R^{T,64}_i\right).
\]

同时报告每臂的 final-minus-initial、相对同面板 BCRH 的差，以及 `J_ext`、`U_total`、`U_intact`、两个失败区、原生违规和已有恢复语境。不能用 midpoint 替换 final、只报较好区域，或把 20 秒语境写成精确恢复延迟。64 world 的配对 SE 条件于这一个训练对；它不估计训练种子总体的不确定性，旧两个架构比较的 seed 也不并入这次样本数。[新读数定义][S1]；[原生 readout 和评价程序][S12]；[证据规范 §11.8.3][S13]

采纳新问题的 **0.02 绝对 `R_fail_60` 描述尺度**。它是对已知约 0.04—0.06 MAPR–BCRH 差距的一部分是否具有可用价值的探索性取舍，动机使用了历史观察，必须如实保留这一结果知情设计背景。它不改变旧 B01 的 0.10，不把旧 MAPR–DIRECT 差异改判，也不是显著性、全正号或等价界线。[intake §3][S1]；[原 B01 卡][S6]；[规范 §11.7][S13]

## 四、什么观察会改变决定，为什么保留强反方

我的事前判断较保守：两臂仍出现真实学习，比 INTERVAL 必然取得超过 0.02、同时无其他原生代价的优势更可信；对主差符号没有高把握。原生服务归属区间可以使标签更贴近计分窗口，但不保证消除跨区间协调困难。这个判断不是新的结果或有效性条件。

| 新比较的观察 | 可形成的有限判断及下一选择 |
| --- | --- |
| INTERVAL 的恢复改善达到或超过描述尺度，完整 `J_ext` 保持或改善，且没有被隐去的 intact／分区代价 | 支持这一个 N7 训练对中该时间信用配方的可用信号，可建议另外选择一个独立训练对作同配方跟进；不自动分配，不等于稳定优势或证明旧瓶颈。 |
| 恢复改善，但 `J_ext`、`U_intact` 或某区出现不利差异 | 保留为有原生代价的 mixed 结果，不能称无代价恢复改善；它不自动支持扩大该配方。完整目标与各分量均不能改成另一主指标来救结果。 |
| 主差小、分区混合或不确定性大 | 按实际幅度、服务代价和该训练对的条件不确定性解释。落在 ±0.02 内本身不证明等价，也不自动关闭方向或要求加 seed 至显著；没有新的决策收益就不选后续。 |
| TERMINAL 更好，尤其 INTERVAL 的恢复与完整目标同时更差 | 反对这一明确区间信用配方在当前训练预算上的价值；停止这笔已选投入后保留不利结果，不将它泛化为所有时间信用或 N7 学习无效。 |

这些读法不要求每个 world、分区或未来 seed 同号。即使主差有利，也要保留两臂的初始增益及 BCRH 差距，避免只因某臂偶然学得更差就夸大“恢复能力改善”。反向或混合输出真正能够限制这个 recipe，正是它相对于“再训练一次旧架构比较”有新增决策价值的地方。[提案的预期解释][S1]；[证据规范 §5.2、§11.8.2—§11.8.4][S13]

一次运行当然可能无法确定很小的真实效应。这是选择一项 B 的代价，而不是以一个训练对认证总体因果作用。无论哪个结果，本次授权范围都在这一次比较及其收集、接受、intake 后结束；没有第二 accepted invocation、替换 seed、追加评价或自动后继。

## 五、完整成本：沿用已有实测作规划，不把未知计成零

该比较的主导乘法仍是两臂 × 一个训练对 × 64 轮 × 32 episode × 六次联合决策，以及每臂 64 × 四 PPO epoch × 八个 minibatch；再加两臂 × 三个 checkpoint × 64 评价 episode 和 384 次完整 BCRH 参考调用。**新增部分是沿已有 own-trajectory 快照保留计数、形成六个标签并发布所需结果，不增加任何候选、政策或未来轨迹搜索轴。** 四 token 选择、原生环境和 PPO 是算法工作；BCRH 的内部枚举／checker 是既有参考的真实成本，不能因不输出候选记录而从账中删除。[计划计数][S2]；[原生 Python 接口][S11]；[`experiment.bcrh` 与完整训练循环][S12]

两次旧完整双臂运行的实际 wall 为 306.68 和 388.75 秒。新 JSON 用已有 MAPR 单位时间的最大观测值，为两个同尺寸 MAPR 给出了以下**历史替换规划项**，不是新运行测量：

| 历史规划输入 | 秒数 |
| --- | ---: |
| MAPR 每个 collection episode | 0.0221246242 |
| MAPR 每个 update round，含完整四 epoch | 1.9021591770 |
| MAPR 每个 evaluation episode | 0.0172086126 |
| 每臂 2,048 collection + 64 update round + 192 evaluation | 170.3534712763 |
| 既有完整 64-episode BCRH 参考项 | 46.3770763420 |
| 两个 MAPR 替换、参考和已记录共享项合计 | 400.2884091133 |

共享项包含既有 setup、world 生成、记账和 publication。每臂应保留 `2048*c_collect + 64*c_update + 192*c_eval + δ_new` 的含义；新 counter 收集、目标构造、输出及当前机器变化仍未测，不能将 `δ_new` 填零、把 400.29 秒叫作上界，或据此声称一定能在 600 秒内完成。历史 JSON 的 summary 投影与最终 stdout 的替换写回口径也不相同，不能将小差异误当另一套实测；已有程序明确区分最终 summary 写入／读回费用。[费用 JSON 的 per_arm_cost_projection、shared_projection_terms_seconds 及历史记录][S2]；[`experiment.cost_projection` 与最终发布段][S12]

本次明确接受的是**一次 900 秒累计完整机器工作分配**，并保持提案的两项边界：

\[
T_{native}\le600\text{ s},\qquad
T_{support}\le300\text{ s},\qquad
T_{native}+T_{support}\le900\text{ s}.
\]

`T_native` 是完整双臂科学调用，不是单独的 C++ kernel：包括实际支付的 import、build、初始化、训练、三个固定评价点、完整参考、checkpoint／结果构造、publication 和读回。`T_support` 包括实际准备、必要 focused checks、source staging、Monitor 观察命令、收集／读回和 closeout 的机器工作。两项不是每臂额度，不相互补充，也不会因为拆脚本或未用完而重置。300 秒内已经包含所需测试，不再叠加一笔测试预算。[intake §5 与 proposed_caps_unselected][S1]、[S2]

既有工具的有限起止计时即可表达这些范围，不需要新的 telemetry 服务。行政思考与队列／网络空闲等待按提案另列，不能据此漏掉实际调用的支持工作；重叠的嵌套计时不重复收费。若支持计时缺失，完整 900 秒合规性保持未建立，而非补零；独立可信的原生主读数仍按其自身依赖判断。费用不完整与 reward／训练数据损坏是不同问题，不把前者自动变成方向科学负面。[提案费用口径][S1]；[完整性与失败依赖规则][S13]、[S17]

没有额外成本实验、校准、第二次正式尝试或自动 retry。若已有具体费用事实表明完整路径不适配分配，或执行达到所定边界，应保留已有事实并返回，不删一个臂、缩短 episode、去掉后半程服务或挪走 publication 来宣称完成。旧 B01 的 2,700 秒累计边界及 827.76／828.98 两种已说明口径继续保留；余额一分不转入本对象。E01 的资源、验证和并行例外也不迁移。[旧暂停的费用校正与应用][S3]、[S4]；[本轮费用记录][S2]

## 六、实现准备只处理这项变化，不追加科学前置

源码足以支持复用路径，却不等于当前 `experiment.run` 已经实现两臂 B02：旧 `initialize` 创建 MAPR 和 DIRECT，旧 `update` 只接受终点 `J`，旧 `rollout` 尚未将七个累计快照作为新信用数据返回。需要的是两个同构 MAPR 的初始化／命名接线、同轨迹计数保留、明确的六步目标和相应读数；并非直接重跑旧入口。不得为新对象修改旧证据或解释旧 checkpoint。[`learning.initialize/rollout/update`][S8]；[`experiment.run/readout`][S12]

按当前已采用规范，由现有 DM 完成新卡、精确新身份和 L0 中的目标、owned paths／入口、保留语义、接受范围、预算与停止条件；DM 默认直接实现，并对改变 reward／learner 语义的 diff 使用既有独立高风险审阅。不新建 CM 层、审批层或额外诊断任务。源代码提交／推送之后，未来执行仍限 `wsl_4070` 的 CPU float64／单计算线程、脱离代理的既有监督路径，并在同节点紧邻实际命令取得物理和有效可用内存均至少 4 GiB 的新鲜准入；本次没有测试该节点的当前容量。[工程规范 §7.1、§7.3][S16]；[当前 AGENTS §1、§5—§8][S17]

必要检查集中在这项实际变化：零起点和正确的累计字段；终点正分母与 60／120 秒边界；区间和与完整 `J` 一致；TERMINAL 保持原递推，INTERVAL 用所定义的不同目标；critic target 与 actor advantage 归一化次序不混淆；行为输入不接触未来分母；两臂自己的动作重放、真实非零更新及主要产物可读。以已有可信路径、最小非环境目标检查和正式链已有观测为依据，检查成本计入支持额度。不要求全历史重放、跨平台 bit 一致、完整 support、极严统一容差、阳性预跑或额外 calibration。完整原生计数的代码依据由上述接口提供，不能声称一个纯合成单元检查已经验证了所有物理轨迹。[实际训练与原生接口][S8]—[S11]；[工程规范 §4—§5、§7.3][S16]；[证据规范 §11.8.5—§11.8.7][S13]

新模型的初始化范数、参数位移、实际梯度／更新量和完整费用均待真实运行报告。历史同构 MAPR 的初始 L2 范数约 33.3166655、相对位移 0.292124／0.304535，只说明旧预算下已有真实学习活动，不保证新标签的优化充分性。[机器历史曝光][S2]

HMAC 异常、SIGSEGV、不完整正式尝试、旧跨 N 负面、R09 无效包、有限特权 witness、R03 未完成和 E01 工程停止都不改判；已成功运行也不证明旧故障被治愈。此次选择不以唯一故障根因为前置，也不为诊断另外拨款。[历史结果限制][S5]；[旧决定与当前方向][S3]、[S7]

**由此，只对这个已定义的 native-service 时间信用比较解除暂停限制；旧架构比较与部署方式子问题继续遵守原停止边界。** 不选择第三次 recast，不改变 ACTIVE/HIGH 或两次 recast 的争用排序，不等待兄弟方向结果、清理或 Portfolio 批次。本轮零新增模型、环境步骤、优化、评价、测试和 profiling；科学选择本身不是源码接受或启动。[本轮 intake §1、§6][S1]；[现行滚动／权责要求][S17]；[生命周期快照][S18]

## 七、实际读取来源与结论上限

本次经连接的 GitHub 读取以下 19 条列明科学来源。除四条历史材料注明的版本外，来源均固定在 `b610a07986d839e4a44159d8c7c5a85ca300606c`；没有用共享分支的后续变化替换输入。表中 D 表示 `docs/research/candidates/variable_n_fleet_churn/`，E 表示 `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`，R 表示 `experiments/candidates/variable_n_fleet_churn_bpcr_r09/`。

| 实际来源 | 版本和实际范围 |
| --- | --- |
| [D/VNFC_NATIVE_SERVICE_CREDIT_REENTRY_INTAKE_20260910.md][S1] | 默认固定版本，全文 §§1—6；长响应结尾补读 |
| [D/pro_packets/20260910_native_service_credit_reentry/EXPOSURE_AND_COST.json][S2] | 默认固定版本，完整 JSON 内容，包括历史输入、计划计数、未知费用与 caps |
| [D/pro_packets/20260906_post_depmode_convergence/archive/RESPONSE.md][S3] | `6b466abedfb5d1dee88145e3d3990fce98fd2717`，全文分窗口读取 |
| [D/VNFC_POST_DEPMODE_CONVERGENCE_INTAKE_20260906.md][S4] | `1952f7b35bce656b778b00db2c466ec3574b46e8`，全文，重点 §§2—4 |
| [D/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md][S5] | `da2ba5a194ddb66acee253b5fb42619479e37fab`，全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md][S6] | `b6f8f0257bbf5dc93437662853990d6bc4c57812`，1—135 行，问题、处理、曝光、成本与停止范围 |
| [D/DIRECTION.md][S7] | 默认固定版本，1—138 行，当前暂停、部署方式、B01 与 E01 主要记录；未展开旧完整法则 |
| [E/learning.py][S8] | 默认固定版本，全文 |
| [R/training.py][S9] | 默认固定版本，全文；不将旧 96-entry minibatch 或 R09 总工作合同套入新 B |
| [R/native/bpcr_general.hpp][S10] | 默认固定版本，数据结构、`GS`、`gtick`、角色／观察相关片段及 `ginteractive_snapshot/reset/step`；长行选段，不声称完整控制器审计 |
| [R/native_backend.py][S11] | 默认固定版本，400—465 行，快照字段、reset/step/BCRH 接口 |
| [E/experiment.py][S12] | 默认固定版本，全文分窗口读取 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][S13] | 默认固定版本，§4、§5.2、§11 全文，重点 §11.4、§11.7—§11.10 |
| [docs/rl-marl-foundations-20260907/FOUNDATIONS.md][S14] | 默认固定版本，全文，实际判断使用 §§1—4、§6 |
| [docs/rl-marl-foundations-20260907/topic-notes/01_RL.md][S15] | 默认固定版本，全文，重点数据／更新、baseline／critic、reward 变换 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][S16] | 默认固定版本，§4—§5 及 §7 至文件末，重点 §7.1、§7.3；其他对象附款不转移 |
| [AGENTS.md][S17] | 默认固定版本，分窗口读取 §§1—8 与 Appendix A；仅采用本任务明确适用要求 |
| [docs/research/portfolio/PORTFOLIO.md][S18] | 默认固定版本，开头、方向表中 VNFC 行和队列／second-recast 相关段；其他方向不作为科学输入 |
| [D/pro_packets/20260910_native_service_credit_reentry/ISSUE_SNAPSHOT.json][S19] | 默认固定版本，完整 JSON；其观察时间为 2026-09-10T20:05:00.092104+00:00 |

另外，在本轮交付核查阶段（2026 年 9 月 11 日）直接读取了 [Issue 1 正文][I0]与当时四条评论：[原工具问题][I1]、[协作摘要][I2]、[两种子决定交付][I3]、[暂停决定交付][I4]。连接器未给出本次读取的精确时分秒，不把固定快照或评论创建时间当作本节点读回时间。正文中旧“尚无训练结果”等文字没有覆盖固定 intake；未跟随评论中的未列链接展开证据。

没有已列路径或有效固定版本的访问缺口。本次未重新解析旧完整 episode、装载 checkpoint、运行代码或直接验证新目标；原论文阅读范围限于 intake 所保存的来源说明，未声称本节点另行读过它们。剩余未知是新标签的有限训练效果、总体训练变异、未来正常化与观察 critic 的实际影响、完整新调用及支持费用，以及 BCRH 逐字段信息差异和旧故障根因。这些未知限制结论，不阻止上述一个定义明确的普通 B 科学选择。其结果仍不能支持稳定优越、等价性、纯时间信用因果归因、最优性／调优 headroom、跨 N／重复 churn／UAV 迁移或安全部署结论。

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/research/candidates/variable_n_fleet_churn/VNFC_NATIVE_SERVICE_CREDIT_REENTRY_INTAKE_20260910.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260910_native_service_credit_reentry/EXPOSURE_AND_COST.json
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/6b466abedfb5d1dee88145e3d3990fce98fd2717/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260906_post_depmode_convergence/archive/RESPONSE.md
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/1952f7b35bce656b778b00db2c466ec3574b46e8/docs/research/candidates/variable_n_fleet_churn/VNFC_POST_DEPMODE_CONVERGENCE_INTAKE_20260906.md
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/da2ba5a194ddb66acee253b5fb42619479e37fab/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/b6f8f0257bbf5dc93437662853990d6bc4c57812/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/research/candidates/variable_n_fleet_churn/DIRECTION.md
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/learning.py
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/experiments/candidates/variable_n_fleet_churn_bpcr_r09/training.py
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/experiments/candidates/variable_n_fleet_churn_bpcr_r09/native_backend.py
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/experiment.py
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/rl-marl-foundations-20260907/topic-notes/01_RL.md
[S16]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/project/ENGINEERING_SCOPE_SPEC.md
[S17]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/AGENTS.md
[S18]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/research/portfolio/PORTFOLIO.md
[S19]: https://github.com/CartmanFatass/My-paper-code/blob/b610a07986d839e4a44159d8c7c5a85ca300606c/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260910_native_service_credit_reentry/ISSUE_SNAPSHOT.json
[I0]: https://github.com/CartmanFatass/My-paper-code/issues/1
[I1]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5555371099
[I2]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5555521310
[I3]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5556114589
[I4]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5559622759
