**最终选择：继续当前公开固定伙伴、全八 context 的小型参数化家族，但只再选择一项真实 B——在一个新的配对训练实例 seed 3 中，将同一 FACTOR／GENERIC 比较推进到 512 次更新，并保留同实例的 128 次更新读数。** 这不是再做一批原预算种子，也不是为机制解释增设前置审计。所选新对象名为 **VSPC1-K4-FACTOR-VALUE-B02-BUDGET512**；两臂完整执行及其 intake 结束本次投入，不自动追加 seed、1024 更新、第三臂或 C 评价。

最强理由不是运行便宜，而是现有观察同时存在两种会影响下一步选择的事实：原 128 更新下的差异随训练实例变号；与此同时，短周期合法续约仍未被两模型普遍学好。一个保持原前缀、继续真实采样和更新的配对轨迹，能够直接观察当前差异在更多学习后保留、收缩还是反转。它比第四次仅在 128 更新停止多回答一个具体预算问题，又不必现在改变宿主、信息或比较器。**这个选择只购买一次局部预算响应观察，不承诺得到稳定优势或定位唯一原因。** 原始负 seed 和两个正 seed 都保留。[三种子完整结果][result12]、[原负结果][result0]、[本轮提案][proposal]。

## 一、当前最小科学结论

本答复的仓库证据统一读取于固定版本 `4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7`；文中的历史运行提交只是被读记录的溯源，不是另外跟随读取的证据版本。

**已经观察到的是：在既定两角色、两个已见外生周期、两个公开固定伙伴计划、镜像上下文、六步原生回报和 128 更新预算上，FACTOR 相对具名同信息 GENERIC 出现小幅、依赖训练实例的参数化性能信号。** 三种子描述均值为正，不能替代逐种子相反结果。源码、真实计数和技术记录支持两臂确实学习并完成原评价，不存在“旧 A01 没有 learner，所以本轮也没有 learner”的推论。[原卡§1–7][card]、[科学核心 Value／rollout／run][experiment]、[技术记录的六调用完成段][technical]。

| 训练 seed | FACTOR J(0) | GENERIC J(0) | FACTOR J(128) | GENERIC J(128) | 终点差 FACTOR−GENERIC | 原 0–128 AUC 差 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.500000 | 0.500000 | 0.625000 | 0.666667 | −0.0416666667 | −0.0286458333 |
| 1 | 0.458333 | 0.500000 | 0.708333 | 0.625000 | +0.0833333333 | +0.0338541667 |
| 2 | 0.458333 | 0.500000 | 0.708333 | 0.625000 | +0.0833333333 | +0.0234375000 |

三种子平均终点差为 `+0.0416666667`，平均 AUC 差为 `+0.0095486111`；已提供的配对终点样本标准差为 `0.0721687836`。它们是三个训练实例的描述，不是总体区间、显著性判断或“三取二通过”。两个新 seed 相同的终点差也不等于总体方差为零。此表与两份一训练实例一行的 [endpoint CSV][endpoint]、[AUC CSV][auc] 及 [computed_observations 的 records／paired_differences][computed] 一致；本节点未执行统计脚本或重算模型。

新 seed 中 FACTOR 从较低初始平均回报提高 0.25，GENERIC 提高 0.125，故“FACTOR 初始平均回报领先”不能解释这两个新结果。**这没有排除初始策略、参数尺度、优化轨迹或一般参数化的影响。** seed 0 初始均值相等，初始逐 context 策略仍不同；其 update 16 的短暂正差不能取代不利终点和全程 AUC。[两份结果的初始化与曲线段][result12]、[seed 0 全九点曲线][result0]。

原生损失位置也在变化。seed 0 的终点差来自 FACTOR 在 `(p=6,tau=2,c=1)` 返回 1/3，而 GENERIC 为 2/3。两个新 seed 的四个长周期 context 均在双方返回 2/3；FACTOR 分别在短周期 `(tau=4,c=1)`、`(tau=4,c=0)` 返回 1，而 GENERIC 分别在 `(tau=2,c=1)`、`(tau=2,c=0)` 返回 1/3。其余短周期格为 2/3。这是实际行为差异和镜像／训练实例敏感性，不是已经识别了跨周期负迁移。[computed_observations 的全部六个 final_contexts][computed]。

### 必须同时保留的反证和解释边界

**最强反证是原 seed 0 的双指标反向，以及三种子平均曲线差很小。** 两个新正结果不能消除它。原本“GENERIC 在新 seed 平均至少同样有竞争力”的 DM 预期，在实际均值上没有成立；本轮不能把该预期继续写成观察事实。[扩展 intake 的预测核对][intake12]。

该任务的伙伴执行公开固定程序，不学习、不反应；它确实可还原成全观察单控制器问题。两个模型都共享隐藏特征，两个周期列上的四维嵌入没有形成严格低秩瓶颈。因此比较支持的是这两套参数化的有限预算表现，不是“共享对不共享”、严格低秩必要性、战略 MARL 或伙伴适应效果。缺少这些更强含义不使现有 B 失效，但限制继续投资的可获得结论。[完整上轮 Innovator 第2、4、7节][innovator]、[Value.forward][experiment]。

同信息、当前持有段最优选择给出的解析参考仍为 5/6；它不是已运行的第三臂，也不是调优后 GENERIC。旧 A01 的宿主／上参考／通用基线缺失仍属于旧资产快照，不能用新 toy 的解析值追溯填入。当前没有匹配的调优 headroom 记录；本次不要求先补它。[原卡§2、6][card]、[历史 A01 intake][a01]。

## 二、为什么选择预算响应，而不是其余候选

| 候选 | 真正增加的信息及主要工作 | 本轮取舍 |
| --- | --- | --- |
| 原预算 seed 3：两臂各 128 更新 | 第四个训练实例的同估计量观察；合计 50,016 联合步、256 更新。只需允许新 seed，不必改 AUC 终点 | 是最直接的随机性复现替代，但此前已明确做完两个新 seed 的有限跟进。它仍有价值，却不回答差异是否局限在较短学习预算 |
| **seed 3：同两臂各 512 更新** | 新实例的完整 0–512 学习轨迹，内含 128 点；合计 199,776 联合步、1024 更新，没有外层政策搜索 | **选择。** 当前未普遍学好的短周期动作与相反实例结果，使较长但一次封顶的预算响应有明确决策价值 |
| 增加同信息完全条件化表格 Q，或改变因子维数／网络参数化 | 前者能检验神经表示学习困难这一竞争解释；后者改变所比较的归纳／优化偏置。均需新参数、初始化、更新及工作量定义 | 不选。不是坏对照，也无需全面调参才准用；但此时改变对照同时改变解释轴，不能作为既有比较的预算响应。其实际新成本未测，不把“表格小”当成测量 |
| 停止当前公开计划 toy 家族 | 零新增科学调用；保留三种子局部信号，不再追问预算敏感性 | 是最强的节约投资替代。该 toy 能支持的结论确实很窄；但眼下尚有一项不用新宿主即可改变判断的真实学习问题，所以暂不选择停止 |
| 明确科学 recast | 新伙伴信息、反应、信用或未见周期条件可回答不同问题，但须给出真实行动后果、学习链及新增实现 | 本轮不选。没有把“换成更真实 MARL”当作完整设计，也不从本 toy 秒数推断其他宿主便宜；不重开旧 D6 source/countdown 搜索 |

两项现成候选的计数及条件成本均来自 [PROSPECTIVE_WORK][work]，不是本节点新实验。选择 512 是一个预算敏感的 B 判断，不是把 512 视为正确训练长度、收敛保证或将来研究的必经台阶。**一对新轨迹仍不能估计预算效应在训练 seed 总体上的分布；此限制是选择时就接受的主张上限。**

## 三、唯一新 B 的完整科学定义

### 1. 问题、绑定结构与保留人口

问题是：在同一新的配对训练实例中，FACTOR 与 GENERIC 从 128 推进到 512 次同规则更新后，其完整六步原生回报差是保留、扩大、收缩还是反转；变化来自各臂实际回报怎样改变，而不是仅由一个差值说明。

绑定结构仍是时间抽象／续约：**公开伙伴切换计划 → 伙伴实际频道行动 → 焦点服务模式在外生合法边界间保持 → 六步联合服务奖励 → 逐持有段 reward／bootstrap → 真实 Adam 更新 → 后续合法动作和原生回报。** 不加入学习伙伴、成员变化、隐藏计划、额外通信、人工正确动作标签或新奖励。

保持 `N=2`，`t=0,...,5`，`p∈{2,6}`、`tau∈{2,4}`、`c∈{0,1}`，八个外生 context 等权 1/8，全部训练、全部评价。伙伴在 `t<tau` 执行 `c`，之后执行 `1-c`；焦点只在 `t=0,p,2p,...<6` 选择合法动作 0 或 1，其他时刻保持。主回报为 `R=(1/6)Σ_t 1[a_t=b_t]`。这是实际自由策略回报，不是均匀强制首动作的条件均值。

两个周期共有的合法决策时刻只有 t=0；t=2、4只属于短周期。对 `tau=2`，最优首动作随周期不同；这使周期有实际行动含义，但不让该有限任务自动具有未见时长迁移或伙伴协同适应的含义。[原卡§1–3][card]、[完整 Innovator 的宿主和自由策略测量][innovator]。

### 2. 两个 learner 与共同更新

FACTOR 保持 `[s,onehot(i)]` 六维输入、16 tanh 单元、四维 `u(s,i)`、两行四维周期 embedding、`Q=u·v(p)`，188 个参数。GENERIC 保持 `[s,onehot(i),onehot(p)]` 八维输入、19 tanh 单元、标量 Q，191 个参数。共同状态仍为 `(2c−1,tau−3,t/6,ell_t)`，ell 为上一伙伴动作编码，t=0使用原哨兵。两臂有相同公开信息、动作支持和人口；不按架构名称假定对照已经充分调优。

GENERIC 是本轮最合理的既有同信息学习对照：已真实更新并改善回报，且与上一比较连续。解析控制器更强但不支付学习成本，不能替代它来回答这两套有限预算 learner 的差异；本轮不添加第三臂。[Value 与原训练设计][experiment]、[原卡§3–4][card]。

每轮仍有32条完整 episode，每个 context 四条，产生48个短周期和16个长周期 renewal，共64行。每段 `g=Σ_segment r/6`，目标为更新前参数计算并 detach 的 `g+(1−done)max Q(s_next,i_next,p)`，终局续接为0，gamma=1。每轮一次全批量 Adam，lr=0.01、betas=(0.9,0.999)、epsilon=1e−8、weight decay=0，global grad norm clip=5。

损失继续为 `L=(1/32)Σ_episode [(1/m_episode)Σ_segment(Q−y)^2]`、`m_episode=6/p`。两个周期各占总损失权重一半；短周期的行数和bootstrap深度仍较大。不得改成所有renewal等权、增加replay／额外epoch、改变target、加入监督或把更多训练称为对原128结果的修复。

### 3. 新 seed、探索 schedule 和停止时点

只用一个新配对训练实例 **seed 3**，两臂各自初始化模型和 Adam，从零训练；不恢复 seed 0–2 的任何权重或优化器状态。保留现有随机流定义：NumPy context／exploration分别为 SeedSequence `[3,101]`、`[3,102]`；FACTOR dense／embedding 为3201／3202，GENERIC dense 为3301。这些数值是从已读 `seed*1000+tag` 规则推得的未来配置，不是已经创建的随机流。[STREAM_TAGS、Value.__init__、run][experiment]。

两臂在同一 seed 共享外生context顺序及固定 `(32,6,2)` 探索draw槽位，各自执行自己的策略，不让一个臂的结果选择另一臂数据。评价为确定性greedy，不消耗训练随机流。不同形状模型不要求参数数组相同。

以第 j 个训练轮／Adam步编号：

\[
\epsilon_j=\begin{cases}
1-0.9(j-1)/127,&1\le j\le128,\\
0.1,&129\le j\le512.
\end{cases}
\]

探索动作保持均匀，贪婪平局仍选0。**不能把下降 schedule 拉伸到512，也不能将原线性式外推到负 epsilon。** 前128轮的科学设置保持原128预算定义；其后固定0.1是本次事前选定的新增学习条件。

两臂分别一次完整调用，顺序 FACTOR seed3、GENERIC seed3。无论128点或其他中间点是否有利、是否达到解析参考，都不作结果导向的提前成功停止；完成512或按下文资源／实际故障边界停止。512后的额外轮数、seed和模型均未选择。

### 4. 评价与 AUC：完整范围事前明确

在更新 `0,16,...,512` 的33个固定状态，每臂用真实宿主对全部八个 context 各执行一次无学习greedy episode。保存各点八格回报、原有周期／伙伴分层、完整动作计数和零计数。**主性能终点是512，不是看到哪个点好就换成哪个点。**

定义 `J_a(u)=(1/8)Σ_x R_a(u;x)`，主要差值为 `D_512=J_F(512)−J_G(512)`。同时报告双方J(0)、J(128)、J(512)，从初始化到两预算点的增益，以及 `G_a=J_a(512)−J_a(128)` 和 `B_delta=D_512−D_128=G_F−G_G`。这些都是完整原生回报的比较，不以预测损失代替。

全程归一化 AUC 必须使用32个16-update区间：

\[
A_a^{0:512}=\frac{\frac12J_a(0)+\sum_{k=1}^{31}J_a(16k)+\frac12J_a(512)}{32}.
\]

保留同实例0–128前缀AUC，仍除以8。另从同一已选曲线计算128–512后缀AUC作为次要解释量：

\[
A_a^{128:512}=\frac{\frac12J_a(128)+\sum_{k=9}^{31}J_a(16k)+\frac12J_a(512)}{24}.
\]

不新增任何评价episode。按定义 `A_a^{0:512}=(1/4)A_a^{0:128}+(3/4)A_a^{128:512}`；这是区间分解的算术身份，不是新测量。全程和后缀的两臂差都保留，不能仅选符号有利的区间。[旧 AUC 的实际 `/8` 实现][reporting]。

**128与512共享初始化、前缀数据、参数和优化器历史，是同一训练实例内的相关观察，不是两个独立seed或两个独立预算实验。** 这条轨迹能观察所选继续学习路径的预算响应，不能独立识别增加数据、增加更新、探索持续时间或优化阶段中哪一个是唯一原因。seed3的0–128读数可以与旧三seed并列、注明来源；新0–512 AUC不得与旧0–128 AUC混为四次同估计量的样本。

保留描述性MEI `1/12`，用于说明平均原生服务差的大小，不作显著性、每层通过或全正号门槛。无须增设训练seed区间或p值。这里全八context评价是已选有限人口的完整读数，不是八个训练实例；确定性评价也不减少训练随机性的未知。

## 四、预测与什么结果会改变投资判断

本节点的定性预测是：GENERIC在短周期仍可能从新增学习中改善，局部差异收缩比将两次新正结果视为持续扩大的稳固优势更可信。供intake分别核对的具体方向预测为：GENERIC的p=2均值在512高于同实例128，以及 `|D_512|≤|D_128|`。这是两个可被实际观察否定的预测，不是准入、成功判据或对未来数值的声称；D_128为零时也照实保留该预测的严格含义。DM可记录自己的独立预测，所有者未提供预测时仍记未取得，不制造预测回复。[旧预测的实际得失][intake12]。

以下是新B的解释与下一投资读法，不是自动触发其他实验的状态机：

| 新的完整观察 | 能说什么，以及下一步倾向 |
| --- | --- |
| FACTOR在512仍有较高原生回报，自己的128后增益也为正，完整／后缀曲线相容 | 支持这一新实例中较长预算下仍存在局部参数化价值；若要扩大主张，可据实际大小提出另一项独立预算复现或明确新任务，但本次不自动执行 |
| GENERIC改善并追平／反超，或FACT0R原有差值显著收缩 | 原128点比较具有预算依赖；削弱把原短预算差当持续优势的理由，倾向结束原样预算阶梯。不能据此宣布两模型等价或唯一归因于优化 |
| 差值变大主要因为GENERIC下降，或FACTOR仅靠初始领先保持终点 | 报告对照损失／初值贡献，不叫更快学习。对新的不同对照或参数化问题另作判断，不为取得干净阳性自动调参 |
| 终点与AUC、前缀与后缀或各周期／镜像格相反 | 主终点仍为512，所有相反读数并列；仅支持阶段／人口敏感性，不挑最有利指标，不将平均抵消叫一致无效 |
| 双方到达同样高回报且无有用曲线差，或长期都基本不再改善 | 当前预算问题的边际分辨力低，倾向停止这个公开计划toy的原样继续，不自动增加1024更新或更多seed；未达到解析值并不是未训练或工程失败 |
| 实际学习、reward、信息或主结果出现具体缺陷 | 限制依赖该缺陷的比较，保留可信局部事实；不把故障当FACTOR输赢，不选择替换seed或用剩余时间自动重跑 |

本次选择结束于这一对调用的完整或受阻intake。进一步行动应针对新增事实；**短wall、正结果、负结果、接近MEI或机制仍未知，都不能单独成为无界续投规则。** 这不是宣布A/B被消费，也不是为以后普通B新增一个必须再过Pro的门槛。结束或重开家族仍按现有方向权限处理。[证据规范§11.8–11.9][evidence]。

## 五、工作量、真实成本和实施边界

### 计划曝光与主导乘法因子

| 数量 | 每臂 seed3 | 两臂总计 |
| --- | ---: | ---: |
| 新训练实例 | 1 | 2个模型、1对训练seed |
| 训练轮／Adam步 | 512 | 1024 |
| 训练episode | 16,384 | 32,768 |
| 训练联合原生步 | 98,304 | 196,608 |
| 训练renewal行 | 32,768 | 65,536 |
| 评价状态 | 33 | 66 |
| 评价episode | 264 | 528 |
| 评价联合原生步 | 1,584 | 3,168 |
| **完整训练加评价联合步** | **99,888** | **199,776** |

每臂每个训练context有2048个episode；由每轮48/16行直接得到短／长周期renewal为24,576／8,192。主工作是 `2臂×1新seed×512轮×32episode×6步`，加 `2×33×8×6` 评价步、每轮一个64行更新。普通合法动作选择比较两个Q值，**没有nested policy、trajectory、subset、controller或solver搜索**。这不是把旧精确诊断缩小后作为学习前置。[现有源码][experiment]、[已提供候选计数][work]。

初始化保持CPU FP32 Xavier gain1／零bias，FACTOR embedding正态std0.5，188／191参数；原定义中的预期初始范数尺度约4.138510931／3.627569332。512步名义 `sum(lr)=5.12`，不是Adam位移上界。未来实际初始范数、终端范数、实际位移和位移比应来自新模型，未知不填零，不设任意最小比率。[原卡曝光][card]。

六个已有真实位移比按FACTOR／GENERIC分别为：seed0 `0.506819673／0.436521756`，seed1 `0.458212978／0.463905000`，seed2 `0.564353790／0.474141775`。它们证明旧learner在旧预算内确实移动，不代替新run的曝光。咨询本身未创建模型、随机流、环境episode、更新或评价，也未运行分析代码。[PROSPECTIVE_WORK 的实际记录][work]。

### 已测窗口与前瞻估计分开

| 旧128更新完整调用 | FACTOR wall／CPU秒 | GENERIC wall／CPU秒 |
| --- | ---: | ---: |
| seed0 | 1.76／1.71 | 3.95／1.76 |
| seed1 | 2.77／2.68 | 2.76／2.71 |
| seed2 | 2.90／2.81 | 2.86／2.80 |

六调用合计17.00秒完整wall、14.47 CPU秒、150,048联合步、768更新，均为已完成观察。seed0 GENERIC的wall较长不能直接解释成架构计算更慢；其cause未测。串行交接和准备使study elapsed不同于调用wall之和；原seed0约60秒、seed1/2约109秒的study窗口不与计算wall混算。原测峰值RSS约510,000 KiB量级也不替代新节点准入。[技术记录][technical]。

新每臂成本律采用实际源码的分阶段形式：

`T = C_import/init + 512*(t_rollout_cycle + t_update_64rows) + 33*t_eval_8contexts + C_check/publication/exit`。

使用旧固定batch32／H6／同模型phase测量时，要区分rollout中已含的轨迹检查、update中已含的target／loss检查与另行JSON写读，避免漏算或重复计入。新33点逐次发布的I/O、启动、退出与争用仍未测，不能填零。

已给出的旧phase线性情景中，512轮训练部分约1.047–7.724秒／臂、33点评价约0.031–0.064秒／臂；将旧完整wall乘四得到7.04–15.8秒／臂，只是另一个总工作量线性情景。**两种情景不能相加，任何一个都不是实测新成本、upper bound、加速比或工程膨胀倍数。** 它们支持这一小规模提案的合理性，不保证实际完成。无需为形成科学选择先加profile或新的计时A。[work的phase及projection_limits][work]。

每个完整臂／seed调用保留 **2700秒**，两臂串行的cap和为5400秒；不是本对象总计2700秒，也不是保证的study elapsed。import／初始化、全部训练与33点评价、必需检查、发布读回及退出均在完整边界内。实际执行分别报告完整wall、CPU及可得RSS，不用phase时间冒充完整时间。无法满足所选真实工作时返回具体缺口，不能删context、删不利checkpoint、偷短训练或用别的主指标通过。

### 现有实现能复用什么，必须显式改变什么

已读现行runner只接受seed0/1/2；`experiment.run`固定range(129)、128终点和计数，`reporting.curve_metrics`固定除以8。**当前源码不能仅输入seed3或把循环上限改成512就被称为完成新B。** 新对象需由CM在普通研究范围内明确新身份／seed3入口、后128 epsilon floor、33点评价、AUC分母及前后缀读数、实际512计数和终端字段含义。不能把512范数继续标作theta128，或把新曲线套进旧AUC分母。[runner][runner]、[run][experiment]、[reporting][reporting]。

这是一项新、结果启发的B，不是修改历史B01。复用现有host、Value、rollout、renewal loss和紧凑发布路径；一个针对实际改动和主要输出的focused检查足够，不新增环境烟测、旧四克隆证书、全历史replay、全tensor转储、精确上参考或独立时长校准。保留reward、合法持有、伙伴时序、episode权重、真实更新及全人口主测量这些实际依赖。

CPU FP32、单科研进程／单compute thread、batch32及原remote-first路径保持。每次调用在实际执行节点取得新的physical/effective各4GiB内存准入；原声明的可移植／无已接受远端进程／fresh destination admission规则保持，不迁移活动run，不把GPU或VNFC四线程例外移入本题。普通2000新增源码行、600 runner行及既有测试预算保持，编排比例只作审查提示；不选新§4机械设施、不改规范。[工程范围§3–5][scope]、[runtime一般要求][runtime]、[节点声明][compute]、[AGENTS§5–8][agents]。

本节点只形成科学选择，不验收未来源代码、预发实际资源准入或启动训练；本次授权写入仅用于交付这份回答及对应评论。

## 六、读取范围、未知量和不变边界

**28条列明仓库路径均已实际访问，无仓库、固定ref或列明路径访问缺口。** 完整科学卡、提案、两轮结果与intake、原Innovator全文、CM技术记录全文、两CSV及三份当前科学代码均已读取；长返回的科学文件截断部分通过同路径同ref补齐。以下明确区分完整阅读与相关段读取，不声称复算全部原始运行数据。

下列文件位于 `docs/research/candidates/vsp_c1/`：

| 已读文件／子路径 | 范围 |
| --- | --- |
| `pro_packets/20260905_three_seed_convergence/PROPOSAL.md` | 全文 |
| `pro_packets/20260905_three_seed_convergence/PROSPECTIVE_WORK.json` | 全文 |
| `pro_packets/20260905_three_seed_convergence/ISSUE_SNAPSHOT.json` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_SEED12_RESULT_EVIDENCE_20260905.md` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_SEED12_INTAKE_20260905.md` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_RESULT_EVIDENCE_20260905.md` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_INTAKE_20260905.md` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_SEED12_SCIENCE_CARD_20260905.md` | 全文 |
| `VSPC1_K4_FACTOR_VALUE_B01_CM_TECHNICAL_RECORD_20260905.md` | 全文，包括seed0和seed1/2完成段 |
| `results/k4_factor_value_b01_seed12_20260905/all_endpoint.csv` | 全六行 |
| `results/k4_factor_value_b01_seed12_20260905/all_auc.csv` | 全六行 |
| `results/k4_factor_value_b01_seed12_20260905/computed_observations.json` | 第1–760行：六个records、全部终点context、配对差及部分seed0曲线；未逐行复核其余全部54点人口 |
| `pro_innovator_20260905/archive/RESPONSE.md` | 全文；旧引用不跟随 |
| `DIRECTION.md` | 全文 |
| `VSPC1_IDENTITY_PERIOD_HEADROOM_A01_INTAKE_20260904.md` | 全文 |

其余12条已读路径为：

| 已读路径 | 范围 |
| --- | --- |
| `experiments/candidates/vsp_c1/k4_factor_value_b01/experiment.py` | 全文 |
| `experiments/candidates/vsp_c1/k4_factor_value_b01/reporting.py` | 全文 |
| `scripts/run_vspc1_k4_factor_value_b01.py` | 全文 |
| `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md` | 全文 |
| `docs/research/portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md` | 全文 |
| `docs/research/portfolio/PORTFOLIO.md` | 当前头部、来源表及相关执行说明；不读取全部历史快照 |
| `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` | 第11节，完整11.8／11.9及其相邻规则 |
| `docs/project/ENGINEERING_SCOPE_SPEC.md` | 第1–115行，普通research范围及第3–5节规则 |
| `docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md` | 开头及一般要求的成本、batch、数值、验证与角色相关段 |
| `.codex/hmasd-compute.toml` | 全文 |
| `AGENTS.md` | 第1–350行：权限、方法、资源、范围及交付相关段 |
| `docs/project/GITHUB_RESEARCH_COLLABORATION.md` | 全文 |

此外，直接读取了[固定任务][task]和[Issue 5][issue]正文及评论集合；撰写前及准备交付时均未见既有评论或本轮已交付文件。Issue正文是DM综合，不是Pro原文，也不替代固定证据。本轮连接器没有返回读取发生的精确时钟字段，故不声称一个未测的UTC读时刻；其`created_at/updated_at`为2026-09-06T00:36:31Z，是Issue字段而非本次观察时间。[固定ISSUE_SNAPSHOT][snapshot]记录的采集时刻为2026-09-06T00:40:03.474799Z，也不冒充本轮读时刻。证据中的UTC运行日期与America/Los_Angeles的2026年9月5日相容。

本节点没有读取未列出的raw summary、图片、测试或第三方网页，没有执行模型、环境、统计脚本或benchmark。数值表依据被读的完整E0／技术记录、CSV和派生JSON；未把CM／DM的独立检查计作额外训练样本，也没有独立复现这些运行。

尚未知：seed3的实际初始化范数、轨迹、128／512差值、未来wall和位移，预算响应在训练总体中的变异，以及初始化、优化、双线性参数化或段信用何者造成现有差异。本次B只减小局部预算响应的不确定性，不声称一次观察会解决其余问题。

**最小家族边界仍为这个公开固定伙伴、全支持两周期、两参数化的有限预算学习比较。** 本轮没有C冻结、严格低秩结论、未见周期／伙伴迁移、一般MARL或UAV主张。旧D6动作选择及source/countdown搜索停止不变，旧A01缺失不改写，VSP-C1的Portfolio ACTIVE/MEDIUM和K4其他来源不由此变更。[D6 intake][d6]、[方向当前科学记录][direction]、[组织决定][organization]。

**下一步只有这项seed3、512更新的具名真实B。** 保留全部原128证据，先取得所选完整新观察，再按实际大小、相反行为和成本决定是否还有值得购买的问题；不把更多种子或更多预算写成自动续约。

[proposal]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/PROPOSAL.md
[work]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/PROSPECTIVE_WORK.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/ISSUE_SNAPSHOT.json
[result12]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SEED12_RESULT_EVIDENCE_20260905.md
[intake12]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SEED12_INTAKE_20260905.md
[result0]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_RESULT_EVIDENCE_20260905.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md
[technical]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_K4_FACTOR_VALUE_B01_CM_TECHNICAL_RECORD_20260905.md
[endpoint]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/results/k4_factor_value_b01_seed12_20260905/all_endpoint.csv
[auc]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/results/k4_factor_value_b01_seed12_20260905/all_auc.csv
[computed]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/results/k4_factor_value_b01_seed12_20260905/computed_observations.json
[experiment]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/experiments/candidates/vsp_c1/k4_factor_value_b01/experiment.py
[reporting]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/experiments/candidates/vsp_c1/k4_factor_value_b01/reporting.py
[runner]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/scripts/run_vspc1_k4_factor_value_b01.py
[innovator]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/pro_innovator_20260905/archive/RESPONSE.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/DIRECTION.md
[a01]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/vsp_c1/VSPC1_IDENTITY_PERIOD_HEADROOM_A01_INTAKE_20260904.md
[d6]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md
[organization]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md
[evidence]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#118-exploration-and-publication-burden-calibration-2026-09-05
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[compute]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/.codex/hmasd-compute.toml
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7/AGENTS.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/5
[task]: https://github.com/CartmanFatass/My-paper-code/blob/d46f25bdef9e88e8a13def2d8a1a724a13bceca3/docs/research/candidates/vsp_c1/pro_packets/20260905_three_seed_convergence/TASK.md
