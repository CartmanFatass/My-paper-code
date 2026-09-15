**独立科学审查结论：B13 是一个有实际参数学习、完整原生评价和明确比较含义的有限 B/EXPLORE 观察。在已列源码、完整结果、条件归约和技术记录中，未发现已证实、足以使现有主比较失效的实质缺陷。** 必须同时保留：sampled 策略改善了自己的初始化并超过 nearest，但在全部八格 U 与直接 full-Y 均值上仍落后于 fixed greedy；新的 combined-law mode 在全部512个场景的已测后果上与 greedy 相等；恢复均值与失败数量存在不能被服务排序覆盖的局部取舍。一个正学习结果、一个负参照差和一个 modal 零差，不是可以互相替代的结论。[B13 E0，Work / Primary native outcomes / Full eight-cell vector][e0]；[INTAKE_ANALYSIS，checkpoint / comparison][analysis]；[VECTOR_DETAILS][vector]。

**先前提出的可学习先验强度已经得到真实检验，但这次没有取得其所寻求的 greedy 增量服务。** eta 确实进入学习并增加，不能再把这个候选称为“尚未试过”；也不能因 eta 移动或 G_U 为正，就宣布先验瓶颈被修复或标量产生了独立因果收益。我的前向意见是：目前没有足以使另一项经验投入明显优先的已具体化新方法，不应默认续做消融、decoder 或种子序列；最有明确辨别力的继续反选项是一条同法则的新训练及评价实例，但它是可选择的开发观察，不是 B13 有效性的补票。是否把这一机会成本判断转成方向处置，应由 DM 连同完整结果与反方理由报告 Portfolio，而不是由本审查宣布。[前次 E01 review，第五节可学习先验反方案][prior-review]；[实际 Portfolio CONTINUE，第三至五节][portfolio]；[B13 intake，Prediction check and alternatives][intake]；[当前方向协议][protocol]。

## 一、发现、后果与相称处理

**已证实的科学失效发现：没有。** “未发现”限于本次访问的材料，并不认证所有原生依赖无错。下表区分已完成比较、解释边界和前向判断；没有把正确披露的局限虚构为 DM 已经犯下的错误。

| 审查项 | 精确依据与判断 | 后果及相称处理 |
|---|---|---|
| 实际新法则与训练 | `policy.py` 注册 FP64 eta，将 exp(eta) 放在实际组合 log prior 内；`study.py` 的 B13 入口固定新域、seed33、1024更新与五面板。九个 Adam 状态和实际 eta 变化有记录。[policy][policy] [study][study] [analysis][analysis] | 保留真实学习和新法则观察。没有据此更换 seed、补训或撤销结果的理由。 |
| eta 变化的科学含义 | eta=0→0.1922643915495339，强度=1→1.2119909147637744；不存在本轮新训练的固定 eta 匹配控制。[analysis，checkpoint][analysis] [card，Interpretation][card] | 可以说自由度实际参与学习；不能说它造成了全部 G_U、优于 B12，或证明旧先验是瓶颈。缺少因果控制不是当前完整程序比较的缺陷。 |
| 评价期参数冻结 | runner 在最终评价前后比较参数向量，报告位移0；保存的 final checkpoint 位于评价之前。[study，before_evaluation / summary.update][study] [analysis，evaluation_displacement][analysis] | 保留“运行内测得零位移”，不称独立前后 checkpoint 认证。现有声明已经作此区分，不要求为加强措辞重跑。 |
| modal 相等与样本性质 | 512/512逐行 U/F/tau/40U/Y 相等，八格失败数量相等；新面板预先指定，但没有动作 trace。[vector][vector] [e0，Primary native outcomes][e0] | 保留有限结局相等；不能称动作、策略、轨迹或总体等价。零经验 SE 不是零总体不确定性。 |
| 恢复向量 | sampled 对 greedy 的 tau 均值格符号为2好/6坏，失败数为3好/1坏/4平；primary12→8两者方向不同。[vector][vector] [e0，Full vector之后说明][e0] | 向量必须保持。不能将 modal 的服务改善称全指标无害，也不能因 sampled 服务负差删除恢复收益。 |
| 方向权责文本 | 当前协议明确 Portfolio 最终方向解释；同版 empirical §8.1 仍保留较早 DM-final/Clerk 文字。[protocol][protocol] [spec，§8.1][spec] | 这是具体的版本适用冲突，按当前 TASK 与专门 owner protocol 处理；不豁免科学规范，也不由 Reviewer/DM 单方 PARK 或释放槽位。 |

本次没有要求修改冻结数据、原卡阈值、主路径权重或评价终点的发现。需要持续限制的是因果、总体、等价、恢复和成本措辞。若后续简报实际越过这些边界，应收回其对应的扩展主张，而不是宣布整个 B13 失效。[intake，What the result supports][intake]；[spec，§§11.8.1、11.8.4–11.8.7][spec]。

## 二、设计、合法信息与实际学习链

### 同一初始法则，真正不同的训练自由度

B13 卡明确继承 B12 的科学映射及 B11 的指定方法段落，同时明确新增 eta 和第五个 final-modal 面板。故应采用“原宿主、信息、回报、训练块和配对规则，加本轮显式变化”，而不是用 B11 的旧四面板或无可学习先验文字否定 B13 的已声明设计。新对象为 seed33/run_block0 和自己的对象域；没有消费 B10/B12 的参数、优化器、baseline 或随机 tape。[B13 card，Scientific object / Measurements][card]；[B12 card，Exact scientific mapping][card12]；[B11 card，Fixed scientific object][card11]。

令 a=exp(eta)，实际法则为

\[
q(s\mid x)=.9\,\mathbf1\{s=g(x)\}+.1/N,
\qquad
\pi_{\theta,\eta}(s\mid x)
=\frac{q(s\mid x)^a e^{z_\theta(s,x)}}{\sum_j q(j\mid x)^a e^{z_\theta(j,x)}}.
\]

`PhasePolicy` 只在 learned-prior 且 greedy-anchored 模式注册 `log_prior_strength`；其初值是无随机抽样的 FP64 零标量。`initialize` 沿原具名线性层填充 fan-in 值，保留最终 scalar score 层为零，不重写 eta。因此 a=1、z=0 时初始分布仍是 q。这里“同初始法则”不等于跨 B10/B12/B13 同随机权重、同物理世界或同评价均值；新根使这些实现实例不同。[policy，PhasePolicy.__init__ / initialize][policy]；[study，_run / parameter_uniforms][study]。

`phase_log_probabilities` 用整数距离获得当前 greedy 相位，将 `exp(eta)*log(q)` 加入网络分数后统一 log_softmax。`sampled_phase` 从这个组合分布抽样，并返回同一分布的所选 log probability。它不是先从 q 抽样、再用未锚定 scorer 的似然训练；也不是对全部 logits 统一调温度。[policy，phase_log_probabilities / sampled_phase][policy]。

给定当前公共状态，代码法则的解析得分为

\[
\partial_\eta\log\pi(s\mid x)
=a\left[\log q(s\mid x)-\sum_j\pi(j\mid x)\log q(j\mid x)\right]
=a\log(9N+1)\left[\mathbf1\{s=g(x)\}-\pi(g(x)\mid x)\right].
\]

这是对已有源码的推导，不是本次新梯度实验。它说明归一化项也参与 eta 导数；正、负方向都由实际动作、策略概率及回报相关性决定，不是“梯度天然要求弱化先验”。代码没有 detach eta、强制单调 schedule、clamp、模仿标签或新奖励。已有 synthetic 导数检查与独立工程审查支持这个路径；本审查未重跑那些检查。[policy，相应函数][policy]；[ENGINEERING，self-check / technical acceptance][engineering]；[CODE_REVIEW，Direct facts][code-review]。

### 一次共同决定的似然与完整原生回报

每次 claim opportunity 只选择一个共同相位，它映射成当时整队的 quota targets；不是给每个 agent 重复计一次共同随机事件的似然。`rollout` 将每个 episode 的16个机会 log probability 求和，再以该 episode 的直接 native Y 作 full-return score loss：

\[
S_e=\sum_{t\in\{0,4,\ldots,60\}}\log\pi_{\theta,\eta}(s_{e,t}\mid x_{e,t}),
\qquad
L=-\operatorname{mean}_{64}\{\operatorname{stop}(Y_e-\beta_{c(e)})S_e\}.
\]

每次更新覆盖八个6/10训练格各八条完整 H64 episode，两个 native32 batch 组成64条训练块。单一 Adam 获得 `model.parameters()`，包括 eta；参数步完成后才以 `.95*old+(1-.95)*cell_mean_Y` 更新八个 baseline。lr=.0003、betas=(.9,.999)、eps=1e-8、weight_decay=0、foreach=False 不变。loss/gradient 非有限检查在该参数步骤前；没有额外 critic、teacher、reward shaping 或单独的 eta 优化器。[study，rollout / _run][study]；[policy，adam_update][policy]；[card，Scientific object][card]。

full-Y 与事件后 U、tau 并非同一目标量。全回报梯度可能存在方差或信用困难，但现有记录没有定位它们为病因；不能仅因有限结果不足就宣告梯度错误，也不能把参数移动当成服务能力。直接 held-out U/Y 才支持本次学习后果。[FOUNDATIONS，§§3–4、6][foundations]；[empirical，完整方法比较 / return和开销][empirical]。

### 原生轨迹、五角色与配对完整性

宿主仍为120-sector、六 beacon、H64；四 tick claim，t24成员/epoch事件在行动前应用。`rollout` 先按当前 batch 状态生成并应用事件，再读 public observation，按实际 roster N 分组；survivor、departure、newcomer 和 rank 使用当前物理语义。phase 通过 `b[(rank_i+s) mod N]` 给出整队目标。greedy 在同一相位支持上最小化当前整数环形总距离，平局取最小索引；nearest 通过原生 scripted kernel 在自己的状态行动。[card11，Fixed scientific object][card11]；[study，rollout][study]；[policy，quota_arrays / greedy_phase][policy]。

公共联合调度器是被允许的设施，不是已验证的分散执行、无通信或信用分配机制。greedy 是强的同相位支持、同公共设施参照；nearest 保留已有服务参照含义，但不是等通信、等计算、同归纳偏置的组件因果控制。没有必要削弱 greedy 才让学习比较成立。[card11][card11]；[policy，phase_features][policy]；[foundations，§3][foundations]。

`run_b13_learned_prior1024` 固定33、新对象、1024和 learned-prior=True。`_run` 先评价自己的 sampled 初始化，完成1024个更新后保存 final1024，再依序评价 sampled final、greedy、nearest、modal。五个面板各512条，未在中途评测择优 checkpoint，亦未在最终两个执行法则之间事后选一个替代原主结果。[study，run_b13_learned_prior1024 / _run][study]；[card，Measurements][card]。

评价每格使用 `EpisodeCoordinate(0,cell,0,i)`、i=0…63；训练坐标使用其更新编号及训练格。各角色共享本对象声明的外生语义地址，sampled init/final共享所声明的 phase uniforms；greedy/modal不消费 phase uniforms。共同随机地址不强制共同轨迹，newcomer的实际事件结果仍依各自物理历史产生。`contrasts` 按 cell/scenario 逐键配对，未以旧参照均值配新世界。与 E01 不同，本次 greedy/nearest 也是新对象中实际运行的面板，不是复用旧输出。[study，phase_uniforms / rollout / evaluate / contrasts][study]。

modal 分支确实对含 exp(eta) 的组合 log probabilities 求最低索引 argmax，再使用对应整队 targets；不是裸 z 的最大值，也不是直接调用 greedy。它没有训练 likelihood，`modal` 与 `training=True` 被拒绝。`eval`/`no_grad`不是这里 mode 的来源，显式分支才是。初始化 mode 由 eta=0、零 scorer 和 q 的唯一最大项解析为 greedy，故无独立初始 mode 面板并不删除本问题所需的不同参照角色。[policy，modal_phase][policy]；[study，rollout][study]；[card，Measurements][card]。

## 三、实际学习、服务与恢复向量

以下数值采用固定 summary、INTAKE_ANALYSIS 与完整 E0 的已有归约，仅缩短展示精度；本次没有重新计算置信区间、拟合、重抽样或运行模型。

### 完成事实与标量变化

记录有1个 fit、1024个完整更新，全部参数步骤非零；2,562个 FP64 参数在保存的最终状态相对初始化有变化。初始向量范数5.837959225394895、位移7.862306218627657；九个有限 Adam 参数状态的 step 均为1024。eta=0→0.1922643915495339，a=1→1.2119909147637744。曲线中已记录 eta 的最小/最大值为0.0002999999927698917和0.1922643915495339，不能由范围端点推成逐步单调。[summary，initial_norm / displacement / prior_strength][summary]；[analysis，checkpoint / observed_curve][analysis]。

first32/last32训练 Y 均值为.8158925374348959/.8814198811848959，是训练过程描述，不是独立确认、最佳 checkpoint 或收敛证明。代码与记录共同支持标量真实参与优化；它们不证明每个参数变化都具有可识别的行为贡献。[e0，Work and learning inventory][e0]；[intake，What the result supports][intake]。

评价期位移为0是实际 runner 在最终四面板前后计算的结果。保存的 final checkpoint 在这些评价之前；记录分析核对的是这一运行内测量及保存状态，不是独立保存了一个评价后 checkpoint。源码的 no_grad 评价与无 optimizer 步支持其合理性，但不能将测量来源夸大。现有 E0、analysis 和独立 analyzer review 已明确该限定。[study，before_evaluation / evaluation_parameter_displacement][study]；[analysis，evaluation_displacement][analysis]；[intake-code-review][intake-code-review]。

### 主路径绝对结果与分开的差值

primary 为 ACTIVE_CONTINUATION 8→12、12→8，各权重1/2；tau40以下为两条路径合计128场景中的失败编码数量，不是过去某些表采用的平均路径计数。

| 执行角色 | U | 直接full-Y | 失败编码tau均值 | tau40/128 | 40U |
|---|---:|---:|---:|---:|---:|
| sampled initialization | .198982747396 | .794031778971 | 21.8125000 | 54/128 | 7.959309895833 |
| sampled final1024 | .126546223958 | .861755371094 | 22.1953125 | 61/128 | 5.061848958333 |
| fixed greedy | .106762695312 | .879826863607 | 22.0000000 | 62/128 | 4.270507812500 |
| attained nearest | .281510416667 | .713602701823 | 39.9375000 | 127/128 | 11.260416666667 |
| final modal | .106762695312 | .879826863607 | 22.0000000 | 62/128 | 4.270507812500 |

四个 quota 角色 primary F=0，nearest F=.280143229167。F反映申领数量结构，不足以证明实际恢复、实体到位或安全。Y是完整原生直接回报，不由表中的post-event U或40U合成。[e0，Primary native outcomes][e0]；[analysis，primary_means][analysis]。

| sampled比较 | 均值 | 条件场景SE | 已发表normal近似95%区间 |
|---|---:|---:|---|
| G_U=U_init−U_final | +.072436523438 | .007893353037 | [.056965551485,.087907495390] |
| D_n=U_nearest−U_final | +.154964192708 | .009098165868 | [.137131787607,.172796597810] |
| D_g=U_greedy−U_final | −.019783528646 | .003637062965 | [−.026912172057,−.012654885234] |

G_U为正是这个 fit 对自身初始化的实际服务学习，不因 greedy 胜出消失；D_n是完整程序对 nearest 的优势，初始化本身已经优于 nearest，因此不能把全部 D_n 记为新训练创造。D_g为负说明 sampled endpoint 没有取得替代 greedy 的 U 依据。三个量共同使用 final 面板，不能当成三个独立训练证据。[analysis，comparison.final1024][analysis]；[intake，What the result supports][intake]。

| 主路径 | G_U（有利/不利/平局） | D_n（有利/不利/平局） | D_g（有利/不利/平局） |
|---|---|---|---|
| active8→12 | +.080273437500（35/4/25） | +.174967447917（61/3/0） | −.027018229167（0/18/46） |
| active12→8 | +.064599609375（43/3/18） | +.134960937500（58/6/0） | −.012548828125（3/12/49） |

全部场景均进入原定比较；不能把每格均值落后写成每个场景都落后，也不能删除少数有利场景。特别是两个primary路径的greedy差大小不同。总体负差绝对值小于.025不建立等价；active8→12点差和总量区间下端也提醒，不能仅凭总体点估计就宣称非劣。.025是原局部正收益兴趣尺度，不是对称等价界、G_U门槛、技术有效性或方向停止条件。[summary，comparison.paths][summary]；[card，Measurements][card]。

### 全八格与恢复相反证据

下表active为ACTIVE_CONTINUATION，new为NEW_EPOCH；greedy/modal列相同是本次逐行核对结果，不是预先假定。

| 格 | U_init | U_sampled-final | U_greedy/modal | U_nearest |
|---|---:|---:|---:|---:|
| 8→8 active | .239697266 | .180712891 | .171875000 | .322656250 |
| 8→8 new | .246289063 | .191210938 | .183251953 | .317578125 |
| 12→12 active | .094726563 | .008984375 | .000000000 | .209635417 |
| 12→12 new | .093945313 | .034960938 | .025781250 | .261490885 |
| 8→12 active | .135904948 | .055631510 | .028613281 | .230598958 |
| 8→12 new | .131510417 | .046777344 | .036425781 | .248860677 |
| 12→8 active | .262060547 | .197460938 | .184912109 | .332421875 |
| 12→8 new | .251562500 | .198144531 | .184082031 | .349658203 |

全部八格直接 full-Y 同样是 sampled final胜初始化/nearest、输greedy；全部五角色40格的U/F/tau/tau40/40U/Y已在完整E0和两个JSON中逐格读取。U与40U不是两个独立终点证据。下面保留恢复的绝对水平，每项为“tau均值；失败数/64”。[e0，Full eight-cell vector][e0]；[analysis，all_eight_cell_means][analysis]；[vector，sampled_cell_sign_counts_of8][vector]。

| 格 | Initialization | Sampled final | Greedy/modal | Nearest |
|---|---|---|---|---|
| 8→8 active | 37.8125；58/64 | 38.5；60/64 | 40；64/64 | 40；64/64 |
| 8→8 new | 22.390625；33/64 | 20.875；31/64 | 21.640625；33/64 | 40；64/64 |
| 12→12 active | .1875；0/64 | .015625；0/64 | 0；0/64 | 39.375；63/64 |
| 12→12 new | 1.578125；0/64 | 1.15625；0/64 | 1.03125；0/64 | 40；64/64 |
| 8→12 active | 7.03125；0/64 | 5.453125；0/64 | 5.25；0/64 | 40；64/64 |
| 8→12 new | 5.828125；0/64 | 4.3125；0/64 | 3.96875；0/64 | 39.40625；63/64 |
| 12→8 active | 36.59375；54/64 | 38.9375；61/64 | 38.75；62/64 | 39.875；63/64 |
| 12→8 new | 18.046875；25/64 | 18.65625；27/64 | 17.828125；26/64 | 39.375；62/64 |

sampled对初始化的tau格符号为5好/3坏/0平，但失败数量是1好/3坏/4平；对greedy分别为2/6/0和3/1/4；对nearest两项均8/0/0。它们是相关格的描述，不是多次独立试验，也不是显著性计数。[VECTOR_DETAILS][vector]。

最重要的反例是 primary12→8：sampled tau38.9375比greedy/modal38.75差，失败数61却少于62。换mode改善U与Y，不同时改善失败数。另在两条8→8格，sampled的38.5/60、20.875/31优于mode的40/64、21.640625/33；这些是真实的局部恢复利益，不能因mode服务更好而消失。[e0，Full vector后的tradeoff说明][e0]。

反过来，sampled相对初始化的active12→8从36.59375/54变成38.9375/61，是与正U学习并存的恢复损害。没有事前用途兑换率，就不能把全部向量写成整体优越、全面无害或毫无价值。失败编码tau不是仅在成功恢复者中测得的时长，tau40更不是“第40tick成功”；源码按每格 `sum(tau==40)`计数，primary合计128场景。[study，cell_means][study]；[intake-code-review，Analyzer facts][intake-code-review]。

### Modal 没有新增量，但比较必须命名正确

新modal与本次greedy在全部512行的U/F/tau/40U/Y相等，所有八格tau40计数也相等。两个primary路径分别0有利/0不利/64平局；modal D_g=0，经验SE=0、normal区间[0,0]。这不是正负效应抵销，也不是只保留显示精度后的平局。[vector，modal_greedy_equal_rows_of512][vector]；[summary，modal_comparison][summary]。

modal D_n=+.1747477213541667，条件SE=.007856179700582363；两条路径分别+.2019856770833334与+.147509765625。它是新的执行程序对nearest的比较，且本次结果与greedy对nearest相同；不能据此将规则已有服务记作modal新增学习。程序内部调用通用contrasts后只公开modal D_g/D_n，没有把modal相对sampled初始化的差标成G_U。[study，modal_comparison构造][study]；[analysis，comparison.modal][analysis]。

## 四、证据层级、缺失与未解决的完整性边界

### 新面板与独立训练不是同一个概念

E01是在看过B10/B12结果后选择两个完成checkpoint并复用旧面板；B13则事前写入新对象的五角色、final1024和新held-out坐标。因此B13的modal零差不是再次读取旧世界的同一结果，而是新学习程序的一次前瞻指定评价。方法选择仍受此前结果启发，不能写成整个研究过程盲于历史；新面板也不能把一个fit变成训练总体证据。[card，Measurements][card]；[portfolio，第五节][portfolio]；[e0，Primary native outcomes][e0]。

在这个fit内，路径SE为64条配对差的样本SD/8，两个等权路径再按独立语义场景域的声明合并。它反映本程序下场景/执行抽样的条件变化，不估计新训练根、其他宿主或开发选择的总体不确定性。多个参照共享final；sampled与modal共享训练产物及部分外生输入，不能把各自区间当联合独立保证。大量平局使normal近似尤其不宜被写成精确覆盖证书。[study，contrasts / evaluate][study]；[empirical，随机性有层级][empirical]。

modal的全零经验差使插入式SE机械地为零，未见世界或其他训练实例仍可能不同。相同记录也没有action traces；不同动作/轨迹可以得到相同终局向量。舍弃总体等价、动作等价和全状态机制结论即可保留现在的事实，不需要再做全支持枚举、行为等价证明或对全零样本bootstrap来“认证相等”。[e0，Primary native outcomes][e0]；[spec，§§11.8.1、11.8.3–11.8.5、11.9][spec]。

### B11 不能消失，历史程序不能混池

B11在164个完整更新后SIG11，缺少final1024端点；旧progress160只是较早观察。D1的synthetic非复现、B12/E01/B13成功都没有定位或修复其原因。B10/B12仍是原固定先验程序三次科学尝试中的两个完成端点；B13是另一个明确改变了法则的新fit。可在历史账上同时列出它们，但不能把三个完成的1024结果称为同一算法的三seed确认，也不能把B11补成零收益、负收益或tau40。[B12 intake，What remains open / Full review response][b12-intake]；[portfolio，第二节][portfolio]；[card，claim limits][card]。

不同训练/评价根使B13与B12的差同时混合程序、训练及评价变化；它既不是纯eta效应，也不是纯训练方差。未知SIG11与数据、轨迹或内存历史是否有关仍未知，不能假设缺失完全随机，更不能声称已证明某种特定选择机制。成功的B13没有追溯补齐B11端点。[intake，What the result supports][intake]；[foundations，§6][foundations]。

### 哪些完整性证据真正被检查，哪些没有

E0记录相邻实际节点准入15,627,395,072可用字节、4GiB门槛、精确source、CPU FP64/thread1、监督与直接监控；19个原始证据文件远端与本地摘要相符，含五原始面板、完整曲线、两checkpoint、准入/命令/计时/监督记录。独立代码审查覆盖scalar梯度、Adam/state、旧入口和五面板；独立扩展审查覆盖analyzer与完整supervisor参数边界。实际retained-byte analyzer完成后又核对了1024条曲线、九个Adam状态、逐键面板与条件归约。[e0，Exact execution][e0]；[code-review][code-review]；[intake-code-review][intake-code-review]。

这比单纯“exit0/JSON存在”更强，却仍不是独立的原生reward oracle，也不能排除一切silent corruption。本轮读取的是这些记录和两份实际科学源码，没有重新读取可选NATIVE_EVIDENCE.tgz二进制、解包checkpoint、检查全部native绑定/内核或执行analyzer。已读材料没有显示需要为一个具体未解主量矛盾再访问二进制的事实，故不制造额外审计义务，也不冒称独立确认了全部原始字节。[analysis，files / scope][analysis]；[TASK，optional archive及review范围][task]。

未来若取得实际影响state、reward、采样、训练或measurement的故障证据，应限制依赖它的结论，保留独立可信的较窄事实。现在不能把共享未知风险自动转成B13科学负面或无效，也不能因新法则/无崩溃就声称旧runtime已安全。[spec，§11.8.7][spec]。

## 五、对先前标量提案与 Portfolio CONTINUE 的实质回应

先前review提出的不是“eta必然有用”，而是让固定log-prior的相对强度参与实际full-Y学习，并明确可能只加强greedy、损害起点或仍无增量。完整Portfolio回答随后选择在现有家族内CONTINUE、以B13作具体研究目标，同时保留最强PARK理由和所有结果分支。本次应据真实结果更新那个问题，不能将其偷换成“只要发生参数变化就算提案成立”。[prior-review，第五节][prior-review]；[portfolio，第三至五节][portfolio]。

应区分三层。**实现/可更新性层面**已得到支持：新增标量不是死参数或事后decoder，它与scorer共同经历真实优化。**有限增量服务层面**本实例没有支持优于greedy的分支：sampled仍输，mode逐行相等。**唯一瓶颈/组件因果层面**始终没有被设计识别：无固定eta新匹配控制，旧模型的range检查也没证明分数范围不足。B13没有让这第三层突然成为已证事实。[analysis，checkpoint / comparison][analysis]；[engineering，self-check][engineering]；[portfolio，第三节range讨论][portfolio]。

对非greedy相位s，现行法则给出

\[
\log\frac{\pi_{\theta,\eta}(s\mid x)}{\pi_{\theta,\eta}(g\mid x)}
=z_\theta(s,x)-z_\theta(g,x)-a\log(9N+1).
\]

因此在**固定x和固定scorer**的反事实代数中，增大a增加非greedy赢过greedy所需的相对分数。B13实际a变大，这是测得的方向；但theta同时变化且轨迹也变化，不能由a alone推出实际非greedy概率处处下降、网络只复制greedy，或它导致服务缺口。一个全局标量还能对不同N产生不同的log-odds改变量；这属于声明的法则，不是额外信息泄漏。[policy，phase_log_probabilities][policy]；[analysis，checkpoint][analysis]。

Portfolio引用的旧head理想包络约7.85439/7.76574高于原固定先验log73/log109门槛，最多说明那个包络没有证成不足；它并未证明极值可达、实际轨迹分数越过门槛或越过后能提高回报。这里仅采用完整Portfolio回答中明确限定的既有测量，我没有访问未列的SCORE_SCALE文件，也不将旧head数值套到B13的新权重上。[portfolio，第三节][portfolio]。

现在较准确的科学更新是：**在一个新根和有限1024训练下，允许全局先验强度学习仍没有取得超过现有greedy的已测服务；“只需开放这一自由度便得到有用增量”没有在这个实例实现，但参数学习和局部恢复价值仍存在。** 这削弱当前实现作为greedy替代者的开发理由，不等于证伪所有先验学习、同家族其他方法或整个RCLE。[intake，alternatives][intake]。

预测记录事前认为初始化/nearest收益可能保留、sampled仍难超过greedy、mode趋于greedy结果且先验增强较可能；这些定性方向被观察到，不是事后创造的成功判据。没有校准概率、owner预测或全部seed正值要求。准确预料一个仍无增量的结果，也不能将它重新归类成效力成功。[PREDICTIONS.md][predictions]；[intake，Prediction check][intake]。

完整Portfolio CONTINUE及DM应用已直接读取：最终归档20,895字节；此前20,896字节全回答快照已在实际launch前读入，最终修正仅一处Markdown表格分隔线连字符。它不是改变结论或数字的新批准。卡/工程中的“尚未运行”“只有synthetic零位移”是早期状态，不能覆盖09:01:24Z之后的实际结果；也不能用后来结果反称事前已证明可行或有效。[Portfolio INTAKE，Complete answer / Actual execution received][portfolio-intake]；[e0，Exact execution][e0]。

## 六、前向选择：最强继续理由、反方与最小问题

### 最强继续理由并非只剩“还有不确定性”

B13确有+.072436523438的自身服务学习，在全部八格U/Y胜自己的初始化，并保留两个8→8格相对greedy更好的恢复均值以及三个格较少失败。新法则只有一个训练实例；E01与B10/B12不能充当它的独立重复。另一个完整训练/评价程序可能得到有用的greedy增量，或不同的服务/恢复取舍。此前代码已能实际完成完整程序，163.92秒是真实历史而非未运行的设想。这些让继续成为科学上认真可辩护的选择，不需要先有全新机制、阳性pilot或headroom证明。[analysis][analysis]；[vector][vector]；[spec，§§11.8.2–11.8.3][spec]。

### 最小、清楚的经验反选项：同法则的一条新完整实例

若仍要回答“learned-prior程序未能提供greedy增量是否只发生在这一条训练及评价历史”，最直接的新观察是一个不筛选的新B13-style根，保持1024×64训练、五×512评价、同一sampled/modal法则和全部原生向量。它区分“这一实例没有增量”与“另一个实例能改变开发选择”，不试图隔离eta的因果作用。新结果有用、仍负、平局、混合或缺失都应保留，不能预设跑到正值。[card，Measurements][card]；[intake，alternatives][intake]。

它的完整规模是1个新fit、65,536训练+2,560评价=68,096 episodes、4,358,144 ticks、2,128个native32 batches和1024 backward/Adam；主体仍是当前N个phase各处理N个实体。不是再多512条旧checkpoint评价，也不是cheap decoder replay。历史163.92秒可作规划背景，未来实际native与support仍未知。本审查不选seed、不发卡、不分配这次调用，也不把一个或两个seed升级成总体保证。[TASK，next-work factors][task]；[card][card]。

这个反选项与此前B11/B12并非完全重复同一个问题：它重复的是已经改变的learned-prior程序。不能因为旧固定先验已有两条完成结果，就说B13已经重复充分；同样，不能因为只有一条新法则结果，就把第二条变成通用义务。其正当性应来自它可能改变“保留该程序还是使用fixed greedy”的具体选择，而不是凑样本数。[spec，§11.8.3][spec]；[empirical，随机层级及证据力度][empirical]。

### 为什么我不把这个反选项或另一个改法列为当前必然优先

反方有新增而具体的事实：此前最容易陈述的新自由度已经实际运行，eta增强且mode在新的前瞻面板中仍没有任何已测增量；sampled在八格U/Y均输greedy，新的学习收益没有转成该用途的替代理由。局部恢复优点是真实的，但本次没有声明一个愿意以较差U/Y换取这些恢复改善的实际用途规则。现有结果没有识别出某一具体修改会比一次重复更有希望改变决定；sunk engineering或“再加一个参数”不能代替这一论证。[intake，strongest contrary case][intake]；[portfolio，第四至五节][portfolio]。

**供DM后续完整Portfolio报告的科学建议是：不要默认延长这套程序的经验序列，也不要把eta消融或再改decoder作为现在的优先工作。** 在当前以greedy服务增量为目标的用途下，暂不追加该配方的经验投入是有根据的价值判断；一条同法则重复则是最清楚的反选项，应诚实保留其可能推翻当前模式的机会。这个建议是定性的边际价值判断，不是已计算的成功概率或期望信息价值，也不构成方向PARK。决定不测，须承认可能错过有利实例；决定测，也不需要先保证阳性。[spec，§§7–8、11.8.2–11.8.3、11.9][spec]；[protocol][protocol]。

固定eta匹配臂只有在“eta作为一个组件的作用会改变方法选择”这一更强问题本身值得研究时才有必要。它需要前瞻说明根/外生耦合、同初始化条件、学习及评价预算，不能把旧B12补叫匹配控制。当前没有提出eta因果主张，所以不为“解释为什么没赢”自动添一个控制fit。单在B13训练后把eta设回0只测换执行法则，不识别训练中可学习eta的总作用；它也不是本轮暗中授权的新E01式实验。[portfolio，第五节claim ceiling][portfolio]；[policy][policy]；[spec，§11.8.4][spec]。

对于改变训练目标、状态依赖先验或表示的选项，本次没有已给定的完整设计和实测成本。我没有发现一个足以压过上述反选项/暂缓理由的具体最小改法，故不把方法菜单写成计划。未来同家族改变可以合法且有价值，但应说明想区分什么、保持哪些比较、放弃哪些更强归因；不能由此次负面结果推成必须先做diagnostic grid、全支持搜索或动作等价证明。[intake，alternatives][intake]；[spec，§§11.8.1、11.9][spec]。

## 七、实际工作、成本与权责结论

| 项目 | 本次已记录事实 |
|---|---|
| 新学习 | 1 fit、2,562 FP64参数、1024更新/backward/Adam、九个Adam参数状态 |
| 完整训练 | 65,536个H64 episodes；1,048,576次共同phase draw |
| 评价 | 五个512面板，共2,560 episodes；sampled init/final共16,384次phase draw；modal8,192次确定性共同决定 |
| 全部native规模 | 68,096 episodes、4,358,144 ticks、2,128个native32 batches |
| 实际整链 | 163.92秒、peak RSS1,234,556KiB、exit0 |
| 嵌套study body | 156.05556364101358秒，不重复计入163.92秒 |
| 已具名支持分量 | synthetic checks外层12.5843584秒；Git/SSH准备6.891秒；collection约1.312秒；记录分析3.6449386秒 |

计数来自固定循环、运行出版与经审查的记录分析。新增eta是一个标量运算/梯度自由度，不改变N-phase×N-entity的主要计算维度；五面板不是五个fit，modal argmax不是策略或未来轨迹搜索。旧四面板67,584 episodes/4,325,376 ticks是前次反方案的条件规模，不能继续用它报本次已经增加第五面板的工作量。[card][card]；[code-review][code-review]；[analysis][analysis]；[prior-review，第五节条件规模][prior-review]。

GNU time整链覆盖实际准入、解释器/debugger、构造/训练、评价与发表；monitor的203秒观察uptime不是native运行时间。24项synthetic检查的11.24秒嵌套于12.5843584秒管理计时，不能再相加。工程/analysis的较短局部时间也不是完整provider、reviewer或作者工作成本。[e0，Exact execution / Actual costs][e0]；[engineering，self-check][engineering]。

已枚举B10+B11partial+D1synthetic+B12+E01+B13链和605.33秒，是这六条不同范围调用的已知wall和，不是support、研究elapsed、aggregate CPU或方向生命周期总价；尤其不能拿它与历史600秒support参考比较而宣布越界。历史B10 support下界627.289636秒及偏差保留，其他实现、审查、提供方、监控、整合及寿命尾项仍UNKNOWN。没有完整成本合规或加速比主张。[VECTOR_DETAILS，known_native_sum_scope][vector]；[e0，Actual costs][e0]；[portfolio，第六节][portfolio]。

native3–8分钟、support10–20分钟、1800秒watchdog及旧support600秒是有误差的普通计划或工程控制，不是科学失效、Send、升级或PARK规则。真正owner/platform限制、物理准入与已冻结的1024更新/五面板/一次started调用边界仍保留；本次成功或节省了规划时间不产生第二次fit、retry或新预算。[card，limits][card]；[spec，§11.8.1][spec]；[TASK，成本和边界][task]。

当前协议与TASK明确：本节点提供实质独立科学发现，DM回应、拥有普通研究执行并报告，Portfolio拥有最终方向解释。empirical §8.1及历史review中的DM-final/Clerk措辞按当前专门协议被覆盖，其余证据与比例原则不因此放松。B13有真实训练，不需要借用E01的零更新例外。[protocol，Portfolio final interpretation][protocol]；[spec，§§8、11.4][spec]。

现行完整CONTINUE已经应用，B13目标也已经实际完成；DM选择的是本次完整review与回应，而非新fit、promotion、PARK/CLOSE或释放槽位。本审查不投生命周期票，不再自动派一轮咨询；将任何实质方向/家族/recast或争议解释交给该协议要求的完整报告，不将它扩大成每个普通实验的批准门槛。两项历史窄HOLD及failed/cumulative evidence保持。[intake，actual selection][intake]；[portfolio-intake，Actual execution received][portfolio-intake]；[protocol][protocol]。

## 八、实际访问与未验证边界

本轮经GitHub访问固定TASK及清单中的22个必读文本路径；可选二进制NATIVE_EVIDENCE.tgz未访问。长返回分段补齐用于结论的完整结果、intake、Portfolio全文、summary逐路径差值及analysis向量；同一blob的历史review、B12 intake、规范/基础已读部分按本轮指定ref核对后复用。没有将交付HEAD的新文件当科学输入，也没有沿import、文件hash或历史链接递归扩展读取。

| 有效版本 | 实际访问和采用范围 |
|---|---|
| `cf4d9bd93ff9eb255800223d95de170b68315ba6` | [B13 card][card]全文；[B12 card][card12]Exact scientific mapping及有限执行；[B11 card][card11]Fixed scientific object、Observable与work-count段；[policy.py][policy]、[study.py][study]全文只读。 |
| `c58ec2fb49795035ff99f5ba9c60c44083f8d13b` | [B13 E0][e0]全文含40个格/角色行；[B13 intake][intake]全文；[summary][summary]输入/曝光/参数、全部endpoint means、sampled与modal主路径逐场景差、SE和零评价位移；[INTAKE_ANALYSIS][analysis]实际归约、全向量、Adam/eta、文件hash及测量来源；[VECTOR_DETAILS][vector]全文。 |
| 同上 | [PREDICTIONS][predictions]、[ENGINEERING][engineering]、[CODE_REVIEW][code-review]、[INTAKE_CODE_REVIEW][intake-code-review]全文；区分准备期检查与后来实际执行，不将synthetic当原生fit。 |
| 同上 | [完整Portfolio RESPONSE][portfolio]与[应用INTAKE][portfolio-intake]全文；[B12 intake][b12-intake]核对同blob后复用完整已读结果/缺失及DM回应；[前次E01 review][prior-review]核对同blob，重读标量反方案及全部限定，复用此前完整结论与背景。 |
| `bc4dec35273005676a9939a856b09ed0fcc9fb54` | [PORTFOLIO_DECISION_PROTOCOL][protocol]全文；[empirical spec][spec]§§7–8、11.4及同blob已读的11.7–11.10；[FOUNDATIONS][foundations]§§3–4、6，同blob已读内容与本轮窗口；[04_EMPIRICAL][empirical]全文相关比较/推断/成本段。 |

没有发现决策关键的必读正文不可用。未独立访问的是可选原始tgz/checkpoint/面板字节、清单外native绑定/内核、实际runner与analyzer全文、完整测试日志/支持账或实时远端状态。这些范围的核对使用已列材料明确记载的技术事实，不冒称本审查重新执行了它们；哈希相符也不被解释成测量或runtime普遍正确。[task，manifest][task]；[e0，retention / checks][e0]。

FOUNDATIONS与实证专题在本题的具体作用是区分公共协调设施和学习价值、表示范围和有限优化、实际参数学习和执行法则改变、条件场景精度和训练总体推断。它们没有替代新数据、增加固定seed门槛或要求唯一原因证明。本轮没有执行科学源码、模型、RNG、训练、评价、数值重分析、测试或profiler；等式仅为明确标出的已有法则解释。

**最终科学意见：保留B13的正自身学习、nearest收益、sampled greedy服务/full-Y缺口、modal有限结局相等与恢复矛盾；未发现使这些观察失效的实质缺陷。** 新标量确实学习了，但没有在此fit中产生新的已测greedy增量，既不支持eta因果成功，也不支持整族不可学习。当前无需为接受此结果强制加做匹配消融、重复seed或行为证明。后续最清楚的经验反选项是一条同法则独立训练/评价实例；现有证据未使它或某个新的改法成为必然优先工作。DM应完整回应这些限定和机会成本，最终方向解释保留给Portfolio；本文件不作方向处置或新增执行分配。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/e62ad353fc853293e24ae345e3416d96b0a42cbf/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260914_b13_learned_prior_review/delivery/TASK.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/cf4d9bd93ff9eb255800223d95de170b68315ba6/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B13_LEARNED_PRIOR_SCIENCE_CARD_20260914.md
[card12]: https://github.com/CartmanFatass/My-paper-code/blob/cf4d9bd93ff9eb255800223d95de170b68315ba6/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B12_FINAL1024_SCIENCE_CARD_20260914.md
[card11]: https://github.com/CartmanFatass/My-paper-code/blob/cf4d9bd93ff9eb255800223d95de170b68315ba6/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B11_FINAL1024_REPLICATION_SCIENCE_CARD_20260914.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B13_LEARNED_PRIOR_RESULT_EVIDENCE_20260914.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B13_LEARNED_PRIOR_INTAKE_20260914.md
[summary]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/summary.json
[analysis]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/INTAKE_ANALYSIS.json
[vector]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/VECTOR_DETAILS.json
[predictions]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/PREDICTIONS.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/ENGINEERING.md
[code-review]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/CODE_REVIEW.md
[intake-code-review]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/INTAKE_CODE_REVIEW.md
[policy]: https://github.com/CartmanFatass/My-paper-code/blob/cf4d9bd93ff9eb255800223d95de170b68315ba6/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/policy.py
[study]: https://github.com/CartmanFatass/My-paper-code/blob/cf4d9bd93ff9eb255800223d95de170b68315ba6/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/study.py
[b12-intake]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B12_FINAL1024_INTAKE_20260914.md
[prior-review]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260914_fixed_modal_e01_review/archive/RESPONSE.md
[portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260914_e01_portfolio_direction/archive/RESPONSE.md
[portfolio-intake]: https://github.com/CartmanFatass/My-paper-code/blob/c58ec2fb49795035ff99f5ba9c60c44083f8d13b/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260914_e01_portfolio_direction/INTAKE.md
[protocol]: https://github.com/CartmanFatass/My-paper-code/blob/bc4dec35273005676a9939a856b09ed0fcc9fb54/docs/project/PORTFOLIO_DECISION_PROTOCOL.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/bc4dec35273005676a9939a856b09ed0fcc9fb54/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/bc4dec35273005676a9939a856b09ed0fcc9fb54/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/bc4dec35273005676a9939a856b09ed0fcc9fb54/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
