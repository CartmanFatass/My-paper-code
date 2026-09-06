**我的选择是继续，但只选择一次“公开计划下的跨周期价值：新种子 128→512 更新预算对照”B：FACTOR 与原先的同信息 GENERIC 各用全新 seed 3 连续训练到 512 次更新，在同一训练实例内保留第 128 次更新的测量。** 不再单独追加一个原预算种子，不增加第三臂，不先做精确参考、政策搜索或机制审计，也不选择新的多主体宿主。本次投入在这两个完整调用的结果归档与解读处结束；512 之后的更新、其他种子、调参和任何新宿主均不随之获得额度。

最强理由不是已经证明 FACTOR 更好，也不是六次运行很短，而是：**有限的独立种子跟进已经回答了“符号是否对训练实例敏感”；尚未回答的是，同一个新实例中，当前参数化差异在双方获得更多真实学习后会缩小、保留还是反转。** 这个观察能改变是否继续投入原有参数化与优化组合的判断，同时不改变环境、信息、对照和信用口径。最强反对理由也必须正面保留：原始 seed 0 在终点和全曲线均不利于 FACTOR，三种子平均效果很小；一个新的长训练实例仍不能估计训练总体的预算响应。因此，这是一项有明确退出点的局部预算探索，不是稳定性认证，也不是后续 MARL 实验必须通过的关卡。

## 一、现有证据只支持一个随训练实例变号的小幅性能信号

本轮仓库证据统一读取自固定版本 `4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7`。下文链接保留完整路径；文件内部引用的其他历史版本仅用于理解溯源，没有沿其外链改读其他源版本。

六个调用均已完成，现有技术接受记录没有报告主测量依赖缺陷。它们不是旧 A01 的零学习审计：每臂、每种子确有 4,096 条训练 episode、24,576 个训练联合原生步、8,192 条续约样本及 128 次 Adam 更新，随后有完整固定评价。相应证据来自原始科学卡、两批完整结果及 CM 技术记录，而不是 Issue 的摘要或较早的 Portfolio 执行栏。[原卡，§§4–7][card]；[seed 0 完整结果][e0]；[seed 1/2 完整结果][e12]；[CM 完成记录][cm]

| 独立训练种子 | FACTOR / GENERIC 初始 J | FACTOR / GENERIC 第 128 次更新 J | 配对终点差 | FACTOR / GENERIC 固定全曲线 AUC | 配对 AUC 差 |
| --- | --- | --- | --- | --- | --- |
| 0，原始结果 | 0.500000 / 0.500000 | 0.625000 / 0.666667 | −0.041666667，即 −1/24 | 0.580729167 / 0.609375000 | −0.028645833 |
| 1，前瞻选定的跟进 | 0.458333 / 0.500000 | 0.708333 / 0.625000 | +0.083333333，即 +1/12 | 0.625000000 / 0.591145833 | +0.033854167 |
| 2，前瞻选定的跟进 | 0.458333 / 0.500000 | 0.708333 / 0.625000 | +0.083333333，即 +1/12 | 0.593750000 / 0.570312500 | +0.023437500 |

表中终点与 AUC 分别可由两个六行数据表直接核对，初值和配对变化见完整 E0 与计算记录。新两种子的平均终点差为 +0.083333333，平均 AUC 差为 +0.028645833；**明确包含历史 seed 0** 的三种子平均终点差为 +0.041666667，平均 AUC 差为 +0.009548611。已有计算给出的配对终点样本标准差为 0.072168784；这里不把它或三种子均值变成总体显著性、稳定优势或等价性结论。[终点 CSV][endcsv]；[AUC CSV][auccsv]；[完整新结果的 Rule and measurements][e12]；[计算记录的 records、paired_differences][obs]

两次相同的正终点不是两条相同的训练轨迹。seed 0 的 FACTOR 在更新 16 曾领先 1/24，在更新 64 落后 1/8，最终和原定全曲线均落后；那个暂态正点不能代替主终点。其终点损失位于长周期 `(p=6, tau=2, c=1)`。两个新种子的长周期四个上下文两臂均为 2/3；在短周期，FACTOR 分别在 `(tau=4,c=1)`、`(tau=4,c=0)` 达到 1，而 GENERIC 分别在 `(tau=2,c=1)`、`(tau=2,c=0)` 只有 1/3，其余短周期上下文为 2/3。损失的位置随种子和模型移动，不能据此认定已经找到跨周期负迁移的唯一原因。原来的九点曲线、全部上下文及零动作计数均留在既有记录中，不截取有利窗口、不删除不利上下文。[seed 0 的 All primary observations][e0]；[seed 1/2 的 Rule and measurements][e12]；[CM 上下文与动作记录][cm]

新 FACTOR 从较低的平均初始回报出发，各自提高 0.25，GENERIC 各提高 0.125。这排除了“两个新正结果只是 FACTOR 初始平均回报更高”这一具体解释，**没有排除初始策略、初始化尺度、参数几何、优化路径和较低起点留下更多改善空间的影响**。也不能把初始回报相减后，就把更大增益命名为纯粹的共享因果效应。此前 DM 对 GENERIC 平均至少不弱的预期未在这组三种子均值上实现；这项预测误差同样保留。[新结果][e12]；[新结果 intake 的 Bounded update, predictions and contrary evidence][i12]

所以最小科学结论是：**在公开固定伙伴、两个已见外生周期、六步完整原生回报、八个全支持上下文，以及指定模型与 128 次更新预算上，已观察到小幅、随训练实例变号的参数化性能差异；两个有限正结果与一个完整负结果同时成立。** 它既不是“没有真实 learner”，也不是“FACTOR 已可靠获胜”。

## 二、实现确实把周期接到了行动和学习上，但没有隔离唯一共享机制

实际作用链是：伙伴按公开计划在 `tau` 切换频道；焦点控制者只在自己的周期边界选择服务模式，并在其间保持；两者实际行动是否匹配决定每步服务；真实段回报与下一续约边界的价值进入更新；更新后的价值改变后续合法选择，最终改变同一个六步原生回报。周期并非无后果标签。在 `tau=2` 的初始上下文，短周期和长周期的最优首动作相反；在 `tau=4` 则一致。这里保留的是时间抽象及续约信用问题。[原卡，§§1–4][card]；[实现的 state_at、rollout、run][experiment]；[完整前次 Innovator 设计，§§二–四][innovator]

与此同时，伙伴既固定又公开，全部未来计划可得，因此现有世界可还原为完全可观测的单控制器问题；不存在伙伴学习、战略反应、协同适应或未见伙伴迁移。FACTOR 的状态—动作编码器共享 16 个隐藏单元，再与四维周期嵌入相乘；GENERIC 也共享隐藏特征，并通过周期输入改变其非线性计算。两个周期列配四个因子坐标没有形成有约束力的严格低秩瓶颈。188 与 191 个参数的接近也不等于函数类严格包含、同初始化策略或同优化条件。[原卡，§3][card]；[Value 实现][experiment]

仍未排除的解释至少包括一般参数化偏置、双线性优化、初始策略差异、状态编码，以及短周期的多次 bootstrap。原损失把每条 episode 的续约误差先取平均，使两个周期各占一半损失权重，但短周期每批仍有 48 条续约行，长周期只有 16 条；后者不能凭“权重相等”消失。现有上下文定位只能提出这些解释，不能完成其因果分解。[原卡，§4][card]；[run 中的权重与 detached target][experiment]

我不把缺少低秩瓶颈、伙伴适应、精确参考实跑或唯一解释当作否定上述 B 结果的理由。本次继续也不补齐这些更强证据类：放弃的是唯一共享效应、严格低秩收益及普遍 MARL 效果等主张，而不是已经实测的有限预算性能。当前 §11.8 和 §11.9 要求先问下一观察改变什么决定，不允许为了“完整”先安排最大值、headroom 或政策搜索。[证据规范，§§11.8–11.9][evidence]

## 三、为什么选这一对预算探索，而不是另四种投入

复杂度先按真实工作比较。现有每个学习循环是 32 条六步 episode，加一次 64 行的 Adam 更新；每个评价点是八条六步 episode。FACTOR 和 GENERIC 都只在合法边界评分两个动作。这里没有候选控制器、联合行动树、轨迹树、子集或反复求解器搜索。以下两个具名预算选项的数量来自已提供的前瞻算术，不是本轮新实验。[PROPOSAL 的 Work and implementation][proposal]；[PROSPECTIVE_WORK][work]

| 选择 | 新训练实例与主要工作 | 它新增的决策信息 | 本次取舍 |
| --- | --- | --- | --- |
| 原预算 seed 3 | 两臂各 128 更新；合计 50,016 联合步、256 更新 | 再观察一次原估计量的种子变化 | 不选。已有一次有限的两新种子跟进，已发现符号与错误位置变化；第四个同预算种子更可能细化这个已知事实，而不能直接观察预算响应。 |
| 同一新实例内 128→512 | 两臂各 512 更新；合计 199,776 联合步、1,024 更新 | 在不换环境与对照的情况下，观察追加学习时相对差异和两臂绝对回报如何变化 | 选择。它保留新的 128 点，又给双方同样的后续学习机会，避免把 FACTOR 的长训练与 GENERIC 的短训练比较。 |
| 改一个比较器 | 例如同信息表格 Q 与 FACTOR 的新配对 B | 挑战“优势只相对于当前神经 GENERIC 的表示或优化困难” | 有科学价值，但本次不选；它同时改变表示与初始化，不能回答原比较的预算依赖。无需先完成全面调参。 |
| 现在结束当前 toy 家族 | 零新增学习调用 | 接受小而混合的现有结论，放弃了解其预算依赖 | 合理的次选。其理由应是边际决策价值，而不是结果不全正或没有上界。当前仍有一个不改变主比较的有限问题，足以支持这一对 B，而不足以支持无边界延长。 |
| 转为真正的双学习角色问题 | 新环境信息流、两个可适应策略及其信用和评价实现 | 检验伙伴行动不再公开预定时，参数化是否仍有实际价值 | 暂不选。它提出不同问题并增加实现及学习难度，不能由旧 toy 秒数证明廉价，也不是本次 B 合法性的补考。 |

这里的“最低充分”指**两臂、一对新训练种子、一个固定延长预算，没有第三臂和嵌套搜索**。512 是本次选择的有限观察终点，不是已证明最少需要 512 次，也不保证足够收敛。相较仅到 128，它提供三个额外的 128 更新块来挑战当前有限预算读法；不在看到 256 或 384 的符号后再决定是否加长。一个 256 更新设计同样可以成为另一个有界 B，但没有证据允许称其足够或不足，更没有必要先做一个寻找“正确训练长度”的扫描。本次采用已有完整工作量说明的 512 选项，并将问题严格限定在这个预算变化本身。

**未选择的表格对照可以具体化，而不变成默认前置。** 同信息表格的键可取合法边界的 `(p,tau,c,t)`；其余公开状态特征由这些量确定。按当前宿主定义，短周期有 `4×3` 个状态，长周期有 `4×1` 个状态，两个动作合计 32 个可学习 Q 条目。这是从宿主定义得到的表示数量，不是枚举政策或计算最优动作。一个独立的新两臂 B 可以保留相同段目标、episode 权重、128 次更新和全部原生评价，表格只从真实 reward 学习，不写入解析答案；以独立的、预先声明尺度的非零随机初始化和实际参数位移记录来说明曝光。它与 FACTOR 两臂的交互计数仍可为 50,016 联合步、256 更新，但表格计算、开发和整次运行秒数尚未测量。参数量更少、表示不共享、初始化和优化几何变化都须披露，不能将胜负称为唯一机制证明。本次没有实施或选定这项替换。[原卡的可选比较器与完整支持][card]；[前次 Innovator，§六][innovator]

**未选择的 recast 也必须是一条真实的新后果链。** 一个具体候选是两个服务角色都学习：在六步任务中，各自只观察自己的频道需求、时钟、所持动作和上一拍服务回执；在一个外生事件时刻，一个角色的私有需求翻转，不向另一角色公开未来行动计划。每个角色只在自己的外生周期边界选频道，其他时刻保持；同频道碰撞使服务失败，只有匹配本地需求且未碰撞的角色获得服务，团队 reward 可定义为当拍成功角色数除以二，再对六步取平均。这样，局部事件→角色私有信息→持有或改频道→另一角色的服务与共同段信用→两套真实策略更新的链条不再是公开固定伙伴的换名。FACTOR 与 GENERIC 两个算法臂必须拥有相同的局部历史访问、角色信息、合法动作和联合交互预算，不能让一个看到伙伴未来意图。

这个 recast 至少新增私有观察和回执时序、碰撞原生回报、两个可适应策略、局部历史处理、双方续约样本与评价实现。以每臂 U 个 batch32、H=6 的训练循环为例，环境主因子仍是 `2 个算法臂×S 个独立训练种子×U×32×6` 个联合步，但每个边界需要两个实际策略的计算；若每角色每循环一次独立优化，还要计 `2×S×U×2` 次角色更新及历史编码成本，不能仍只报原来的一个 learner。评价另计固定 checkpoint×episode×六步，不默认为全联合政策搜索。具体 U、历史模型和秒数未选定、未测量；它没有获得本轮执行额度。这一候选说明了未来问题可能更有 MARL 价值，并不使当前局部预算问题无效，也不预设必须先在本 toy 获得正结果才能研究它。

## 四、选定 B 的完整科学含义

### 环境、信息、处理与对照不变

保留两个固定角色、焦点 learner 与公开固定伙伴、H=6、`p∈{2,6}`、`tau∈{2,4}`、`c∈{0,1}`。八个上下文均以 1/8 权重参加训练和评价，不留出第四角，不增加新周期、伙伴或角色。伙伴执行 `b_t=c`（`t<tau`），否则执行 `1−c`；焦点只在 `t=0,p,2p,...<6` 选择 `a∈{0,1}`。主回报仍是 `R=(1/6)Σ_t 1[a_t=b_t]`，不是强制首动作均值、Q 拟合误差或某个有利分层的回报。[原卡，§§1–2][card]

FACTOR 仍为 `[s,onehot(a)]` 的 6→16 tanh→4 表征与两行四维周期嵌入点积，188 参数；GENERIC 仍为 `[s,onehot(a),onehot(p)]` 的 8→19 tanh→1 网络，191 参数。共同状态是 `(2c−1,tau−3,t/6,ell_t)`，其中初始 `ell=0`，以后编码上一个实际伙伴动作。两臂的信息和合法动作完全相同。保持 CPU FP32、Xavier gain 1、零偏置以及 FACTOR 嵌入标准差 0.5；不加载旧模型、标签或解析策略。[原卡，§3][card]；[Value 与 state_at][experiment]

原先选定的 GENERIC 是这一预算问题最合理的连续对照：周期和公开计划未被删去，容量没有故意削弱，现有三个实例都确实学习。本次给它与 FACTOR 相同的 512 次更新和探索机会。它不是已经穷尽调优的最强学习器，也不是经证明严格包含 FACTOR 的函数类；本次不作这两种保证。全面调参或表格控制仍不是这对 B 的启动条件。

### 一对全新 seed 3，连续学习，不续跑历史结果

仅运行 FACTOR seed 3、GENERIC seed 3，按此顺序串行，各自从新模型、新 Adam 状态开始。沿现有种子方案，两个臂的 NumPy 上下文与探索流分别为 `[3,101]`、`[3,102]`；FACTOR 稠密层与嵌入初始化流为 3201、3202，GENERIC 稠密层为 3301。这些是现有源码种子算式在新种子上的前瞻取值，不是已经运行的记录。两臂各执行自己的策略轨迹；固定 episode/原生 tick 随机槽位继续配对，不能让一臂的结果决定另一臂的数据。评价为确定性贪婪，不消耗训练随机流。[种子延伸卡的 stream 方案][seedcard]；[run 与 rollout][experiment]

每个循环仍有 32 条真实 episode，每个上下文四条，完成后只进行一次全批量更新。学习率固定 0.01，Adam betas `(0.9,0.999)`、epsilon `1e-8`、weight decay 0、全局梯度范数裁剪 5。每个实际持有段提供 `g=Σ_segment r_t/6`，目标为 `y=g+(1−done)max_a Q_old(s_next,a,p)`，更新前计算并停止梯度，终局续接为零，gamma=1。损失仍为每条 episode 内先平均续约误差，再对 32 条 episode 平均；不更改周期权重，不加 replay、辅助任务、额外 epoch 或隐藏更新。[原卡，§4][card]；[run 的目标、权重和优化器][experiment]

探索 schedule 明确为：第 j=1,…,128 次训练循环使用 `epsilon_j=1−0.9(j−1)/127`；第 j=129,…,512 次使用 `epsilon_j=0.1`。探索动作均匀，贪婪平局取 0。**不能把原分母 127 改成 511，也不能在第 128 次重置优化器、重启探索或挑一个更好的 checkpoint 继续。** 第 128 次只读出当前状态和原生回报，之后仍是同一个新实例的连续学习。

这项处理改变的是“原前 128 次 schedule 加上 384 次低探索学习”的完整训练方案，既增加数据又增加更新；它不能单独识别数据量、优化器步数、探索退火或墙钟预算的纯因果效应。若需要分别识别那些效应，将是不同的新问题，而不是本轮补做实验。

### 固定完整原生回报与两段预算的正确统计单位

在 `u=0,16,…,512` 的 33 个固定更新状态，各执行八条无学习、无探索的自由合法策略 episode。每个状态先算八上下文均值 `J_a(u)`，再定义下列量：

| 量 | 本次定义与用途 |
| --- | --- |
| 主终点 | `Delta J_512 = J_FACTOR(512) − J_GENERIC(512)`；两臂各自的 J512 同时报告。 |
| 主曲线支持量 | `AUC_a(0:512) = [0.5 J_a(0) + Σ_(k=1)^31 J_a(16k) + 0.5 J_a(512)]/32`，报告两臂及其差。 |
| 同实例原预算读数 | J128 与 `AUC_a(0:128)=[0.5J_a(0)+Σ_(k=1)^7J_a(16k)+0.5J_a(128)]/8`。这是同一 seed 3 的前缀，不是额外训练种子。 |
| 预算响应 | `D = Delta J_512 − Delta J_128`，并拆开报告 `L_F=J_F(512)−J_F(128)`、`L_G=J_G(512)−J_G(128)`，所以 `D=L_F−L_G`。 |
| 后段曲线描述 | 从相同已预算记录计算 `AUC_a(128:512)=[0.5J_a(128)+Σ_(k=9)^31J_a(16k)+0.5J_a(512)]/24`；用于描述后段，而不是替换全曲线。 |

后段 AUC 是本次事先说明的描述量，不增加评价，也不在结果出来后挑选起止点。三种 AUC 的窗口不同，不混为一个估计量。保留 J0、J512−J0、全部 33 点以及按 p、tau、c 的原始上下文结果；不选最佳点，不把某一分层改成总体主结果。[原评价定义][card]；[现有 reporting.py 的 curve_metrics][reporting]；[前瞻方案对新 AUC 的说明][proposal]

**第 128 和第 512 次更新属于同一训练路径，相关性正是这项配对预算观察的性质，而不是两个独立样本。** 不把 33 个 checkpoint、八个上下文或追加 episode 当成训练种子，不对一个训练实例做伪重复的总体区间。seed 3 的 0–128 前缀可与历史三种子逐个并列，明确注明它来自这项新 B；本次不把新 0–512 AUC 与旧 0–128 AUC 合并，也不把一个 512 点补进旧的三种子均值。seed 0–2 的旧读法、初值和所有不利观察不变。

描述性 MEI 保留绝对 1/12，表示平均每条六步任务半个服务步。它用于说明量级，不是继续的必需阈值、等价区间或显著性检验；D 与后段 AUC 不另设事后获胜线。[原卡，§5][card]；[证据规范，§§11.7、11.8.2–4][evidence]

## 五、预测、结果分支与实际改变的下一判断

我的工作预测是：更多同预算机会可能让 GENERIC 修正部分短周期错误，因而在 seed 3 的 128 点存在差距时，后续差距更可能缩小而不是可靠地放大。这只是由当前小规模全支持任务提出的可证伪预期；历史上 GENERIC 均值不弱的预期已失败，不能把它当作既定事实。若 FACTOR 的后段绝对回报和相对差距一起上升，这一预期就受到反驳。所有者在此没有给出新的预测，不能代写。

各分支先检查依赖是否可信，再联合读取主终点、完整 AUC、初值与两臂变化；不能在冲突时只保留更有利指标。

| 实际观察 | 有限 B 读法 | 会改变什么下一判断 |
| --- | --- | --- |
| seed 3 的正差在 512 保留或扩大，且不是只有 GENERIC 退步；FACTOR 有可见的后段绝对改善 | 追加学习下仍存在该实例的有利参数化信号。全曲线相反时仍须写成“终点有利、全程代价未消失” | 保留这一模型/优化组合为值得研究的候选；后续应比较“独立 512 实例是否值得重复”或明确的新宿主问题，而不是继续本实例到满意。本次不自动授权那些调用。 |
| 128 点不利，512 点转为有利 | 原预算排序在这个实例内随训练方案反转，短预算不能代表此实例的长预算 | 放弃对这一参数化作预算无关的好坏判断；新的较长预算信号可以进入后续有限投入比较，但不会抹去历史负种子。 |
| 128 点有利，512 点缩小到零或转负，或 GENERIC 在后段改善更多 | 新结果限制“当前早期优势值得延长”的理由；不证明两个方法等价，也不证明普遍负迁移 | 不再以获取更大终点优势为理由延长原组合；保留原来的短预算性能证据，结束这条未改变模型的自动加时路径。 |
| 两臂在后段近乎不变，或仍有上下文错误而无新增区分 | 此次固定追加预算没有提供新的有用分辨力；不能据此宣布已收敛、已达上界或永远学不会 | 在 512 处停止这项预算路径，不自动改为 1,024/2,048。未来若选表格对照或新宿主，应说明它的新决策价值，而不是为旧结果寻找解释直到满意。 |
| 两臂达到相同的宿主解析参考，且曲线也没有有用差异 | 当前 toy 对这两种参数化缺少继续比较的空间 | 停止当前公开计划 toy 的重复投入，保留已有正负结果；不关闭 K4。无需另跑解析参考普查才可描述这项原生回报观察。 |
| 只有 GENERIC 下降使终点差变大，或终点、全 AUC、后段读法互相冲突 | 原生相对性能仍如实成立，但不能称 FACTOR 更快学会了任务；也不能挑一个指标宣告总体获胜 | 不据此提升“跨周期共享效率”叙事。若下一问题真是比较器表示困难，可考虑前述具体替换；本次不把补对照或全面调参设为修复有效 B 的必需工作。 |
| 实际 reward、信息、合法持有、更新或主评价出现受损依赖，或者调用未完整完成 | 只报告独立可信的较窄观察；不形成受损依赖上的胜负或机制极性 | 保留部分输出与实际曝光，返回具体缺口。没有替换 seed、换模型或自动续跑的权限。 |

这些是结果解读和投资分歧，不是要求某个正号出现才能结束任务。即使所有有效数值都很小，也保留其大小和方向。一个新实例不能检验训练总体的稳定预算交互，因此本次不能仅靠“种子数现在为四”晋级 C；真正需要总体判断时，再按问题的方差、效应和成本选择独立训练及不确定性，而非对当前轨迹重采样。[证据规范，§§5.2、11.8–11.9][evidence]

## 六、真实曝光、主导工作和硬停止边界

已有六次运行的位移是实际学习记录，不是用学习率推算的运动；技术记录没有声称独立参数重放或运行时线程采样。本轮只引用这些既有量，没有新建模型、环境交互、更新或评价。[PROSPECTIVE_WORK 的 observed_128_update_runs][work]；[CM 技术接受及限制][cm]

| 已有调用 | 初始化范数 | 实际参数位移范数 | 位移 / 初始化范数 |
| --- | ---: | ---: | ---: |
| FACTOR 0 | 4.011008263 | 2.032857895 | 0.506819673 |
| GENERIC 0 | 3.658432961 | 1.596985579 | 0.436521756 |
| FACTOR 1 | 4.019371033 | 1.841727972 | 0.458212978 |
| GENERIC 1 | 3.579924822 | 1.660745025 | 0.463905000 |
| FACTOR 2 | 3.883702517 | 2.191782236 | 0.564353790 |
| GENERIC 2 | 3.486590147 | 1.653138041 | 0.474141775 |

新 B 沿用相同初始化尺度、无冻结参数和 lr=0.01 的 512 次真实更新，名义学习率和为 5.12；其前 128 次为 1.28。这是可移动的学习方案，不是实际位移或 Adam 位移上界。新 seed 3 的位移仍未知，不能填零，也不能复制上表。实际调用中记录 theta0、theta128、theta512 的范数，以及相对初值和 128→512 的位移；第 128 次只需保存本次运行内的小型参数读数，不引入检查点恢复平台、额外模型或任何位移比启动门槛。

| 选定新 B 的完整计数 | 每臂 | 两臂合计 |
| --- | ---: | ---: |
| 训练 episode | 16,384 | 32,768 |
| 训练联合原生步 | 98,304 | 196,608 |
| 训练续约样本 | 32,768 | 65,536 |
| Adam 更新 | 512 | 1,024 |
| 固定评价 checkpoint | 33 | 每臂各 33，不作为独立种子 |
| 评价 episode | 264 | 528 |
| 评价联合原生步 | 1,584 | 3,168 |
| 完整训练＋评价联合原生步 | 99,888 | 199,776 |

这些核心计数来自提供的前瞻算术。按同一批量律，每臂每个上下文有 2,048 条训练 episode，短/长周期续约分别为 24,576/8,192；评价合法选择为每个 checkpoint 16 次，共 528 次。这些后几项是对已给计数的展开，不是新的计数验证运行。相对一对原预算 seed 3，多出的工作是 149,760 个联合步和 768 次更新。**一对新长运行的总步数甚至大于已有六次调用的 150,048 步**，不能用“还是两次调用”隐藏投入。[PROSPECTIVE_WORK 的 alternatives][work]；[完整已执行计数][e12]

主导工作可写为每臂：初始化 + `512×[32 条 episode×6 步的 rollout + 一次 64 行更新]` + `33×8 条 episode×6 步评价` + 必需检查与发布。两臂串行，各有自己的模型和优化器。两动作评分是 learner 所需工作；新增加的验证仅针对循环终点、探索边界、AUC 窗口、实际计数及主要结果写读的改变，没有额外策略候选、轨迹展开、求解器、训练 smoke 或泛化验证集。

已有六次完整调用合计 17.00 秒 wall、14.47 CPU 秒，单次完整 wall 为 1.76–3.95 秒；这些是实际值。四倍训练工作得到的 7.04–15.8 秒/臂只是同形状条件线性情景，不是新调用测量、上界、速度提升或工程膨胀倍率。runner 的逐 rollout、更新和评价阶段计时可以支持条件外推，但新初始化、写读、启动退出、争用、节点状态和开发工作仍未测。不同宿主尤其不能沿用这些秒数。[已执行结果的 Actual exposure and technical evidence][e12]；[前瞻成本及 projection_limits][work]

每臂、每种子保留 **2,700 秒完整调用 cap**，包括启动/import、初始化、训练、全部评价、必要检查、发布读回及退出；两臂 cap 合计 5,400 秒不是预计耗时或 study elapsed 保证。共享准备只计一次；Git、SSH、代理与交接等另说明其范围，未测不填零。实际报告区分完整调用 wall 之和、CPU 工作与从首个调用到最后完成的 elapsed。[原卡，§8][card]；[运行规范，General requirements §§1–3、6–7][runtime]

继续采用 CPU FP32、一个科研进程、一个计算线程、进程内 batch32，按已有配置 remote-first。每次实际调用前，在实际执行节点重新测得物理及有效可用内存均不少于 4 GiB；旧记录或本回答不能替代准入。保持原先前瞻可移植的路由语义，不换 GPU、不迁移已接受进程、不转用 VNFC 的具名线程附款。到 cap 或发生实际技术失败即停该调用，保留已完成曝光和输出；不跳过评价或发布以装作完成，也不自动换种子或继续另一个预算。[计算节点声明][compute]；[原卡，§8][card]；[AGENTS 的资源与路由条款][agents]

## 七、只需普通研究改动，不把新设计误称为旧代码已可运行

当前 runner 仅允许 seed 0、1、2；experiment.py 固定 128 次更新和九个评价点，并有相应计数与 `theta128_norm` 等字段；reporting.py 的 AUC 分母固定为 8。因而现在不能直接把命令改成 seed 3 或写一个“512”参数就声称已执行新方案。[runner][runner]；[experiment.py 的 run][experiment]；[reporting.py][reporting]

未来实施限于这个已选择科学问题需要的普通改动：明确新 B 身份与 seed 3，保留旧前缀探索语义并加入 0.1 后段，扩展固定循环与评价点，分别计算 0–128、0–512、128–512 读数，更新实际预期计数、参数读数字段和计时说明。沿用既有真实 host、模型、更新与发布路径；对这些改变和主要写读做一次聚焦检查，并复用未变依赖的有效检查。不要重写旧卡或旧结果，也不要给旧 128 AUC 换分母。

不需要新工程 scope 设施、队列服务、恢复编排、注册表、hash 守卫、通用验证器、全数组发布、全面历史 replay、强制 profiling、CPU/GPU 扫描或新学习框架。保留普通研究的源码、runner、测试和资源预算；没有为此新增审批层或规范例外。源代码里的未实施变化由以后实际实施与读回确认，本轮只形成科学选择，没有运行代码或改变这些源码。[工程范围规范，§§3–5][engineering]；[证据规范，§§11.8.6–9][evidence]；[运行规范][runtime]

## 八、保留的边界、实际访问与未验证项

旧 A01 的 `R_upper`、`R_generic` 和 gap 仍然缺失而不是零；新 toy 的 5/6 是宿主定义下的解析参考，不是实跑的上参考、调优 headroom 或旧 A01 的补值。其缺失不能重新成为本轮 B 的门槛。旧 D6 的 source/countdown 与当前动作选择家族停止边界不变，本次没有借共享 K4 名称转移极性或重开它。方向局部的这一次 B 选择不修改 Portfolio 生命周期、优先级、容量、融合、注册或 C 冻结。[A01 历史 intake][a01]；[D6 完整停止边界][d6]；[K4 组织采纳记录][adoption]；[DIRECTION 的当前科学位置][direction]

实际通过 GitHub 连接器成功取回了所列的 28 个证据路径。完整阅读了两张科学卡、两批 E0 与 intake、前瞻提案/工作量/Issue 快照、原 Innovator 回答、三个实现文件、方向记录及两项历史边界。CM 记录按分段补齐了技术结论、结果、上下文和计数；两个 CSV 均读取全部六个观察。较大的 computed_observations.json 读取了六个实例记录、全部配对差及部分逐点记录，没有在本轮逐条重新计算 54 个 checkpoint 人口；其完整曲线保留为既有证据，不声称做过参数重放。较长 Portfolio、AGENTS 与规范按与本决定相关的条款阅读，特别读取完整 §11.8、§11.9；这不是全仓审查。工程规范、节点声明及 GitHub 协作文件的阅读也没有扩大本次写入权限。[计算记录][obs]；[Portfolio 固定执行快照][portfolio]；[证据规范][evidence]；[GitHub 协作范围][collaboration]

Issue 5 的正文和评论确实通过连接器读到。首次讨论读取阶段的时钟观测为 2026 年 9 月 5 日约 22:32（America/Los_Angeles，UTC−07；对应 9 月 6 日约 05:32 UTC），写入前又复核了评论。固定 ISSUE_SNAPSHOT 保留的是 9 月 6 日 00:40:03 UTC 时尚无评论的历史快照；本轮读到的既有评论是[这条交付通知](https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5555953327)，其原始 API 记录创建时间为 9 月 6 日 01:02:47 UTC。它指向的是先前另一目标的回答，不是本轮交付；没有跟随该回答链接，也没有把那份文本作为本决定的结论来源。Issue 的 DM 综合与完整原始科学证据分开使用，较早 Portfolio 执行栏不用于否定其后已完成的六次调用。[固定 Issue 快照][snapshot]；[Issue 5](https://github.com/CartmanFatass/My-paper-code/issues/5)

尚未验证的是新 seed 3 的实际回报、预算响应、参数位移、成本，以及未来改动是否完成实施；这些都不是零，也不在本回答中伪造为已发生。仍未解决的是训练总体稳定性、初始化/优化/共享的因果分解、调优比较器 headroom 和真正伙伴适应下的价值。**最终选择只有上述一对新 seed 3、固定到 512 更新的完整 B；它的价值是观察一个新的、有限的预算依赖，而不是把当前小信号升级为普遍结论。**

[card]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md
[seedcard]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SEED12_SCIENCE_CARD_20260905.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_RESULT_EVIDENCE_20260905.md
[e12]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SEED12_RESULT_EVIDENCE_20260905.md
[i0]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_INTAKE_20260905.md
[i12]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SEED12_INTAKE_20260905.md
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_CM_TECHNICAL_RECORD_20260905.md
[endcsv]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/results/k4_factor_value_b01_seed12_20260905/all_endpoint.csv
[auccsv]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/results/k4_factor_value_b01_seed12_20260905/all_auc.csv
[obs]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/results/k4_factor_value_b01_seed12_20260905/computed_observations.json
[proposal]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/PROPOSAL.md
[work]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/PROSPECTIVE_WORK.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/ISSUE_SNAPSHOT.json
[experiment]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/experiments/candidates/vsp_c1/k4_factor_value_b01/experiment.py
[reporting]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/experiments/candidates/vsp_c1/k4_factor_value_b01/reporting.py
[runner]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/scripts/run_vspc1_k4_factor_value_b01.py
[innovator]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_innovator_20260905/archive/RESPONSE.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/DIRECTION.md
[a01]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_IDENTITY_PERIOD_HEADROOM_A01_INTAKE_20260904.md
[d6]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md
[adoption]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md
[portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/portfolio/PORTFOLIO.md
[evidence]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[compute]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/.codex/hmasd-compute.toml
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/AGENTS.md
[collaboration]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/project/GITHUB_RESEARCH_COLLABORATION.md
