**最终选择（a）：继续，并在方向科学层面开启一个窄的“固定多 UAV、运动介导观测、原生服务机会成本”B/EXPLORE 家族。第一问题是：在同一有限预算下，学习一个可选的短移动承诺前缀、随后利用实际新观测控制，是否比始终可以逐步反馈的同信息 recurrent PPO 控制器获得更高的完整团队原生回报。**

选择这条路径，是因为现有 `MultiUAVEnv` 已经给出速度改变位置、位置改变信道和局部观测、同一过程产生团队服务回报的实际链条；不需要把免费的局部信息遮掉再出售，也不需要假定存在新的传感器或购买 API。这里的“付费”仅指运动和延迟改变服务机会所产生的实际后果，不是固定正收费、飞行动力学能耗或已有的信息费用账。它可能没有机会损失，也可能直接改善服务，必须让结果区分这些情况。[UAV 源码：`step`、局部观测及 `_compute_reward`][E09]

**这不是已经发现 UAV 付费信息收益，也不是把 B05 的 count learner 移植成功。** 本次开启的最小范围仅为下述固定五机、单任务、一次短前缀的学习比较；不打开一般 COUNT/RAW 优越性、可选遥感收费、成员变化、时长迁移或通用 UAV 家族。旧 retained-policy/root-residual numerical-locus 家族的窄暂停保持不变。Portfolio 的 ACTIVE/HIGH、优先级、容量和 UAV 入场计数不变。本答复形成方向科学选择，但不分配实现、初始化、训练或评价。[方向家族边界][E06] [当前 Portfolio 与 P14 命令][E16] [P14-UCOPE 段][E18]

## 一、现有证据支持什么，不支持什么

B05 的原两数据集比较完整，原 joint RM-A 保留，不重算或改写其规则。两组 FULL 的 native/information 增益分别为 **0.002808186848958338、0.0024321289062500004**，联合均值 **0.002620157877604169**，超过原 0.001 MEI。FULL 在两组中都只于 `LINKED-p17_20-c9_100` 购买，该 context 的付费后净增益为 **0.022465494791666703、0.019457031250000003**；其余十四个 seed-context 对比为零。BLIND 与 IMMEDIATE-4 全部重合，因此两个相同对比列不是两次额外重复。[B05 intake §§2–3][E01] [原卡 §§2–3][E02]

独立单位仍是两份新训练数据集，n=2。endpoint sample SD **0.0002659131214081277** 描述这两个已估计 endpoint 的离散程度；给定拟合策略的联合条件评价 SE **0.0003805940070739763** 描述评价噪声，不能替代训练总体不确定性。四项预测命中；joint RM-B 与“至少一次额外购买”两项未命中。没有全种子正值或显著性的新门槛，也没有由小 SD 推出稳定重复性。[B05 intake §§2–3][E01]

以下反证与此前正值继续分别保留，不进入 B05 的主要量或不确定性：

| 已接受观察 | 本次保留的意义 |
| --- | --- |
| B04 seed6601 在 `LINKED-p13_20-c9_100` 额外购买，context 损失 **0.021816406250000003**；整体增益 **-0.0008735351562499955** | 是实际原生损失，不是 proxy 下降；原规则为 MEI 内的 RM-B，不改称 RM-C。 |
| B04 另一组增益 **0.002949300130208334**，联合均值 **0.0010378824869791692** | 原 joint RM-A 保留，但仅比门槛高 **0.00003788248697916916**，不能被后来两次正值改写为稳健结果。 |
| B01 两个最终策略均为全 context IMMEDIATE-4，增益均为零 | 当时确实有非零训练、probe 和参数更新；不能把零收益归因为没有 learner 暴露。 |
| B02 单数据集正值、B03 两数据集正值 | 是独立保留的有限宿主先例，不是 B05 的新增样本或配对 1024-batch 对照。 |
| 历史 PA-B、TW-B | 付费和尾部覆盖的支持仍在；完整 competence 的 3/6 对 3/6 和两次各损失 0.028562899 的 false probe 也仍在。 |

上述各项见 [B04 intake §§2–5][E04]、[B01 intake §§2–4][E05]、[DIRECTION 的 B02/B03 与 retained-policy 段][E06]。B02 同时改变 learner、探索和精度；不同数据集上的 B03/B04/B05 不构成训练预算的因果对照。拟合最大值偏差、数据变异、评价噪声和优化差异仍是替代解释，没有哪一个已被定位为唯一原因。

**最强支持**是完整的新学习数据再次产生付费后的原生收益；这足以激发一个具体的新 B。**最强反证**是有害购买和两次零收益，说明“学到了探测行为”不保证值得购买。现有 finite coordinator 仍属于 systems / information flow，不是多智能体部分可观测或非平稳性的实证。没有新的 tuned-generic headroom 记录。[B05 intake §§5–7][E01]

## 二、直接源事实与由此作出的推断

### 1. 两个宿主不是同一个接口

`shared_data_return_model_b02/model.py::collect` 实际调用 `conditioning_discriminator_r01/host.py::execute_episode`。后者抽取 SHORT/LONG 和六个 marks，支付后把 displayed count 交给 duration selector，再形成 sampled tail service 和 `external_return`。`ReturnModel.observe` 更新实际完成动作的增量均值，FULL/BLIND 共享真实标签；这些均值更新不是 optimizer.step，也没有 UAV 环境调用。[`ReturnModel.observe/final_policies/collect`][E07] [`execute_episode`][E08]

`MultiUAVEnv` 的实际动作则是每架 UAV 的三维归一化速度。`step` 先将各分量乘 `max_speed`、按 `time_step` 更新并裁剪位置，再更新信道/连接、计算原生 reward、递增 primitive step，最后返回新观测。这里不把分量边界误说成额外的欧氏速度范数约束，也不添加源中没有的加速度或能耗模型。[`uav_env.py` 177–179、265–349 行][E09]

### 2. 当前免费的信息必须留下

两个观测实现都自动返回自身位置、局部用户相对位置与 SINR、局部其他 UAV 相对位置与 SINR、归一化时间。局部条目依 SINR 门槛排序并受数量上限约束。实际条目是 SINR，不按旧注释误读成距离；排序槽位也不是持久用户身份。[`_get_observation_vectorized/_reference`、`_local_user_entries/_local_uav_entries`][E09]

`step` 的 `infos` 另含连接、完整 SINR 行/矩阵及 entity positions。adapter 的实际 reset/step 又保留 `state/next_state`、`state_info`、`infos_dict` 和 `reward_components`。**这些返回值证明环境暴露了接口，不证明任何尚未选定的 actor 一定读取或一定读不到它们。** 不能依文件名断言某个现成 checkpoint、normalizer 或 learner 已经绑定成功。[`uav_env.py::step/_get_state`][E09] [`ParallelToArrayAdapter.__init__/reset/step`][E10]

### 3. 两种 reward 都不是独立信息账单

默认模式为

\[
R_t=0.7\frac{\text{connected users}_t}{n_{\rm users}}
 +0.3\frac{\sum_{\text{connected links}}\operatorname{clip}((\mathrm{SINR}-\mathrm{min\_sinr})/30,0,1)}{\max(\text{connected users}_t,1)}.
\]

`paper_reward=True` 则按已连接链路累加吞吐量减每连接的功率项。后者的功率项不能直接解释成飞行或购买观测的费用；前者也没有每移动一次必扣的正费用。[`_compute_reward`][E09]

还有一项关系到主要量的直接源事实：base environment 将 `global_reward/n_uavs` 返回给每个 agent，adapter 的 scalar 又取这些 reward 的均值。因此本任务下 adapter scalar 是 `R_t/5`，不是未缩放团队 `R_t`。未来比较应取 `sum(info['rewards_dict'].values())` 恢复团队原生量；不能再除一次 agent 数，或让两臂使用不同尺度。[`uav_env.py::step`][E09] [`env_adapter.py::step`][E10]

### 4. 有限推断

由以上链条可以提出一个真实但未验证的预测：某架 UAV 移动后，原本低于门槛或被数量截断的用户/邻机条目可能进入其局部视野，新的位置/SINR 信息可能改变随后速度控制；与此同时，该移动会改变实际连接和服务回报。信息与服务后果来自同一个物理状态推进，而非另造六个 marks。

这只是源支持的**可能路径**。源代码没有证明该配置必有重要隐藏信息，没有证明短承诺能获得优于逐步控制的观测，更没有证明它会提高回报。直接改善位置、减少控制抖动、改变优化暴露或 generic learner 自己完成同样探索，都是仍存解释。正因为这些解释尚未排除，第一对象应是下面的公平学习比较，而不是先搜索一个“保证正值”的轨迹。

## 三、本节点实际选择的新科学语义

下面的参数、actor/critic 边界和 learner 是**前瞻设计选择**，不是关于已有 learner 或已实现 adapter 的事实。环境计算路径保留上述源定义；仅在未来控制器内选择动作持续方式，不新增环境 pay/sense API。

### 固定任务与计量

选择 base `MultiUAVEnv`，固定 **5 架 UAV、50 个用户、1000 m 区域、50–150 m 高度、max_speed=30、time_step=1 s、uniform 用户布局、free_space 信道、use_shadowing=False、use_fdma=False、vectorized channel backend、默认 reward**。保留局部观察上限 20 个用户/10 架 UAV、原连接规则和原数值路径。每次 reset 按该任务原有生成方式取新初始布局；不加地图挑选、最难布局搜索或 transfer 分布。[已有参数入口][E09]

本次另选有限 episode 长度 **H=256 primitive steps**，替代构造器默认的 5000；这是同一固定比较中两臂共同的新有限时域，不宣称覆盖原 5000-step 任务。固定成员与身份，不加入 join/leave、replacement、lifetime 或 teammate-policy 切换。

选默认 reward 是为了直接研究服务覆盖/SINR 后果并保持清楚的归一化尺度。**不选 paper_reward，不添加 probe bonus、信息预测奖励、位移罚款或飞行功率费用。** 主要量为

\[
J(\pi)=\mathbb E\left[\frac1{256}\sum_{t=0}^{255}R_t\right],
\]

其中每一步都是实际 base 团队 reward。短移动可能损失当期服务，也可能获得当期服务；两者都进入同一个完整 episode。

### 所有权与信息边界

每个 actor 只控制自己的三维速度，接收自己的**完整现有局部 obs**、自己的上一实际速度和控制器自己知道的剩余承诺时间；recurrent state 每个真实 primitive step 更新并在 episode reset 清零。参数可以共享，但不能把别的 UAV 的 obs 拼接到该 actor，也不引入免费跨机消息。两臂享有完全相同的局部信息规则和自身行动历史。

训练 critic 可以使用当前 `_get_state` 对应的全局位置/时间，以及各控制器已经选定的速度承诺和剩余时间。`infos/state_info/entity_positions` 作为训练/诊断数据保留，但不经归一化器、共享 hidden state、action feature 或输入拼接泄漏到执行 actor。两臂 critic 权限相同；环境返回值并不删除。[源字段依据][E09] [adapter 返回边界][E10]

这是为**新比较显式选定的 decentralized execution / centralized training 边界**，不是对某个现有全状态 actor 的追溯剥夺。若未来要复用的 baseline 原本合法读取更多 actor 信息，该结果仍须保留，不能把它降权后冒称“原 baseline 原样复用”；本答复选择的是在上述共同信息规则下从零训练的新 generic comparator，不宣称胜过未检验的全状态 controller。尚未读到的 checkpoint/normalizer 不进入本对象。

新的 MARL 结构是固定移动队伍下的部分可观测控制与共享服务后果；B05 本身不因此获得 MARL 证据身份。

### 两条实际控制路径

**处理臂：可选短移动承诺前缀。** 在 episode 的 t=0，每架 UAV 从自己的初始 obs 同时抽样一个归一化速度向量和 `d∈{1,4}`。d=4 时将该速度保持四次真正的环境 step；d=1 时只执行一次。即使处于承诺中，免费 obs、native reward、recurrent state 和系统其他 UAV 都照常推进。只是不在未到期时重新选择速度。该机到期即恢复逐 primitive step 的反馈控制；从 t=4 开始全队均为普通逐步控制。本对象只包含这一次开局前缀，不循环开启新的 options 或搜索时长菜单。

d=4 的命令在无边界裁剪时最多改变每个坐标分量 120 m，是所选现有动作/时间尺度上的短移动；实际距离由学习动作和边界决定，可以为零。**选择 d=4 不自动计为付费、探测或获得新信息。** 不强制移向未知区，不伪造“新增用户”，不把 d=1 当作源中不存在的即时无时间控制。

**最强合法 containing null：逐步反馈的 recurrent PPO。** 它在每个 primitive step 都可选择相同范围的三维速度，保留相同完整免费 obs、历史记忆和 critic 信息。它可以合法移动、悬停、连续四步重复同一个速度，也可以利用运动后出现的新条目。不能将其固定在初始位置，不能屏蔽免费观测，也不能用 IMMEDIATE-4 代替它。

这里的 containing 指合法动作和信息机会不被削弱，不是声称两个有限神经网络具有已经证明的函数类包含关系。两臂实际轨迹与因此得到的观测历史可以不同；相同信息规则不意味着人为把它们强制放在同一状态。

**可检验差别**是：显式学习一次“是否承担短运动承诺、随后反馈”的结构，是否在有限训练预算下改善相对于更自由 generic 控制器的完整原生回报。它不检验 generic 无法表示该行为。一个 generic 控制器自然实现同样的探索与收益，正是应当留下的最强简单解释。

## 四、真实 learner、primitive 信用与暴露

选择一个新卡内的 **FP32 recurrent PPO**，而不是复用 B05 的 264-value 表或宣称现有 MAPPO 接口可用。两臂使用同样的 64-unit tanh 编码层、GRU-64、三维 tanh-Gaussian velocity head；处理臂仅增加 t=0 的二元 duration head，初始概率 1/2。critic 为共同的两层 128-unit 网络，使用上述全局训练输入。保持环境自身的数值语义；FP32 仅声明 learner，不将环境内部数组偷偷改精度。

共同前瞻训练设置为 Adam learning rate 3e-4、PPO clip 0.2、value coefficient 0.5、entropy coefficient 0.01、gradient-norm clip 0.5。每 512 个实际团队 primitive steps 收集一个 rollout，每个 rollout 做四个 full-rollout optimization epochs，每个 epoch 一次联合 actor/critic optimizer.step；recurrent 反传按 32-step 段处理并正确携带段首历史状态。两臂所有公共参数的初始化方法相同，同一训练对的公共参数从相同随机流初始化；新增 duration head 不挤占公共参数的 RNG 流。使用源中已有 obs 的几何归一化；critic 的位置量按同一已知区域/高度尺度归一化。不加载旧统计量、checkpoint 或未知训练器默认值。

这些设置是可供 DM 写同一份完整卡/spec 的选定方案，不是已经运行、调优或验收的事实。选择普通 policy-gradient learner，是为了让取得观测、连续控制和回报之间的信用通过真实 episode 建立，不要求离散化联合速度或另建计数 oracle。

**时间与信用以 primitive step 为准。** 采用有限 episode 的 γ=1、完整实际剩余回报作为 value target；512-step rollout 包含两个完整 256-step episodes，episode 末 value 为零，不以无限时域 truncation 补上不存在的奖励。每个真实决策的 advantage 来自该时点至 episode 结束的实际团队奖励减 critic estimate。承诺开始处因此包含四步中的所有服务得失及其后果，而不是只读取观测出现那一步的 reward，也不额外除以 duration。

联合动作的 log probability 只包含当步真正抽样的速度，以及 t=0 真正抽样的 duration。保持中的速度是已选命令的执行，不能把它重复当作三份新 actor 样本；critic 和 recurrent observation processing 仍按全部真实步骤进行。普通 joint-policy likelihood 用当步实际决策项之和计算 log probability，不枚举五架 UAV 的 2^5 个 duration 组合。训练比较报告相同环境步数与 optimizer 次数，同时如实报告处理臂较少的实际 velocity 决策数、duration 选择数和参数位移，不能把“同 rollout 数”写成“每个 head 的样本数相同”。

完整链条因此为：**某 UAV 与其他 UAV 的实际速度推进 → 各自位置/连接改变 → 该 UAV 收到新的合法局部条目 → 所有权明确的 recurrent state 更新 → 到期后的自身 velocity 决策 → 整段实际 reward 进入 PPO → 所有用户服务与 SINR 构成团队后果。** 不产生未执行动作的反事实标签，不从模拟器全状态给 actor 补答案。

## 五、第一 B 的主要比较、能力记录与结果阅读

选择 **两个独立训练随机种子对**，每对训练处理臂 T 和 generic 臂 G。每个 arm-seed 从零开始，分别取得自己的 on-policy 数据；一对内可共用初始布局种子和公共初始化以降低无关变异，但不能称为共享同一份训练轨迹。两个训练对才是两个独立学习单位，五架 UAV、更多 steps 和重复评价不是新训练样本。具体新种子标识由后续卡在数据产生前写明；本答复不假造其未被用过的检查结果。

每个拟合策略只取训练结束 checkpoint，做 **32 个完整 sampled episodes**。同一对 T/G 使用共同的评价 reset 种子；actor 抽样流与环境流分开。配对以实际实现的共同外生输入为限，不要求在分歧轨迹上伪造全程 bit-identical 噪声或精确回放。每个 episode 的团队时间平均回报先形成配对差，再在该训练对内求均值；两个训练对的均值才形成主要 aggregate。

主要估计量为

\[
\widehat\Delta_s=\frac1{32}\sum_{e=1}^{32}\bigl(J_{T,s,e}-J_{G,s,e}\bigr),
\qquad
\widehat\Delta=\frac{\widehat\Delta_1+\widehat\Delta_2}{2}.
\]

报告每对原始回报、配对差、两个 endpoint 的 sample SD 和按完整评价 episode 计算的条件 MC SE。n=2 不产生稳定训练总体结论；不把 primitive reward 当独立样本。运行内训练曲线直接使用已收集的 on-policy 记录，不能拿它挑选更好的评价 checkpoint。

### “competent null”不由名称保证

generic 具有相同记忆、更多反馈决策自由和相同真实训练预算，这给它公平的能力机会，但不是已观测 competence。为避免两臂都不会控制却宣称击败有能力的 controller，在同一评价集中增加一个**固定零速度悬停参考**，不训练、不搜索、不调参。记录 G 相对悬停的完整 native 表现和学习曲线、动作/服务是否实质改变；悬停只是低成本能力参照，不是 tuned baseline 或最优值。

若 G 未显示可解释的控制能力，T−G 的数值仍保留为这两个拟合策略的结果，但不能宣传“超越 competent generic”；将该强解释标为 comparator-limited。G 相对悬停的一次非正差也不证明整个策略类无能，悬停可能本来就不差。这个能力记录位于**同一个 B 内**，不是启动前的 baseline census、oracle search 或先取得正结果的关卡。

### 新 MEI 与信息路径的限缩

本任务选择 **0.01 的绝对时间平均团队 reward** 为 MEI。默认 reward 的覆盖/质量组合在 0–1 尺度上；0.01 对应完整 episode 平均一个百分点。作为尺度解释，持续多服务一个用户的覆盖项是 0.7/50=0.014，故 0.01 不是仅凭数值最后几位变化续投的阈值。这是本新任务的解释性选择，不是推导出的最优阈值、实际 headroom 或 UAV 工程 QoS 标准；不移植 toy 的 0.001，不更改旧 RM 分支。[reward 依据][E09] [MEI 的方法边界][E14]

除主要量外，保存前四步与余下步骤的实际 reward 小计、承诺频率/持续时间/运动量、局部条目变化与后续控制输入时序。局部观察中的排序槽位不作持久用户 ID；需要描述具体条目来源时，只读诊断可以记录原局部选择索引，不能把它或全局用户位置送给 actor。只记录实际执行中已有的观测，不进行影子轨迹、候选 rollout 或 all-subsets 信息搜索。

**前缀 T−G 的服务差额是配对描述，不是已经识别的纯信息价格。** 两臂的位置也变了，后续服务差既可能来自信息也可能来自直接几何优势。一次 d=4 激活、可预测的新条目或后续动作改变均不是效果；完整 native primary 才决定该方案是否值得。若信息路径读数缺失而 native primary 独立可信，保留性能事实，只限制依赖的信息解释。

| 观察 | 本节点规定的有限阅读 |
| --- | --- |
| 主要均值 >0.01，G 的能力解释可信，且实际使用了移动后观测/控制路径 | 支持这个短前缀 acquisition-control **package** 的初步原生价值，可作为后来明确问题的依据；保留反向训练对。不能仅凭两臂比较分离信息价值、时间结构和优化效应。 |
| 均值 >0.01，但没有实际承诺/新增观测路径，或 G 能力未建立 | 如实报告控制 package 的数值优势及 attribution/comparator limit；不宣布 UAV 付费信息机制已识别。 |
| -0.01≤均值≤0.01 | 本预算下未显示达到所选尺度的增益；不是稳定等价，也不删去局部正值或负值。 |
| 均值 <-0.01 | 限制这个任务、前缀结构与训练预算的价值；信息可预测、动作变化或更多条目不能抵消 native 损失。 |
| 两训练对符号相反 | 在上述总体阅读旁完整保留异质性，不追加运行直到全正，不把条件评价噪声当训练总体解释。 |
| 真实 reward、信息权限、训练或 primary 损坏 | 说明受损依赖；独立可信的较窄事实保留，不赋予技术故障机制负极性。 |

这是 B/EXPLORE 的事前阅读叙述，不是 C 的稳定效应检验。没有显著性、全 seed 正值、精确最优或固定数量复制的资格门槛。**本对象主动放弃单独 COUNT、纯 VoI、独特架构和唯一根因归因；这些更强结论没有相应对照。** 一个完整 native package 增益不会因原因尚未完全分离而消失，但也不能被改写为已经排除了“generic 用免费信息与合法移动就足够”的一般结论。[证据规范 §§5.2、11.8–11.9][E14]

## 六、主工作量、未知成本与停止边界

在选择上述设计前，最小可比工作是两条真实 learner 路径、一个固定任务、少量独立训练对和一次 final sampled evaluation。另做 toy pair 不能回答 UAV 接口问题；先做联合动作、轨迹或 controller search 会增加不必要维度。以下数量是**新设计的前瞻规模，不是测量值或当前运行配额**。

每个 arm-seed 选择 **131,072 个团队 primitive training steps**，即 512 个 H=256 episodes、256 个 512-step rollouts、1,024 次所定义的 optimizer.step。五架 UAV 的行动记录分别计数，不把它们当五倍独立环境 steps。

| 工作 | 前瞻乘数与数量 |
| --- | --- |
| 主训练 | 2 arms × 2 independent seed pairs × 131,072 = **524,288 团队 primitive steps**；共 2,048 个 training episodes |
| 优化 | 4 fits × 256 rollouts × 4 epochs = **4,096 optimizer.step**；实际 actor 决策/critic 样本数另报 |
| 两个学习策略的主要评价 | 2 pairs × 2 policies × 32 episodes × 256 steps = **32,768 团队 steps** |
| 同场固定悬停能力参考 | 2 pairs × 1 reference × 32 episodes × 256 steps = **16,384 团队 steps**；这是额外参照工作，不藏入“零开销” |
| 全部 final evaluation | **192 episodes / 49,152 团队 steps** |
| 嵌套 candidate/trajectory/controller/solver 搜索 | **不选择**；只作正常 policy 抽样与优化，不遍历 2^5 duration 组合、联合连续动作或未来轨迹 |
| 额外 result-bearing 验证调用 | **不选择**；有界 changed-path 工程检查与原始科学预算分开，不能把测试当新 seed |

相应每个训练 fit 的主成本可写为

\[
T_{\rm init}+131072\,c_{\rm env+actor}+1024\,c_{\rm update}
 +32\times256\,c_{\rm final\ eval}+T_{\rm publish},
\]

再按四个 fits 计总量，并单列悬停参考及必要工程检查。该表达式只是工作因素分解，系数不是已测常数；channel/connection 计算、recurrent learner、初始化、评价和 publication 的实际时间均未建立。共享标签的 B05 成本不能用于给这些系数赋值。**UAV 完整 wall/CPU 预测与合适 cap 都保持未知，本答复不分配秒数，也不要求 cost pilot。** 未来实际命令必须给出其完整调用预算；若容纳不了该规模，应重新考虑足够回答问题的规模/对象，而不是加 cap、增加并行或把初始化移出计时窗口。[既有 exposure/cost 记录][E12] [规范 §11.9][E14]

前瞻使用已有 remote-first 路由，初始设计为单科学进程、CPU/单计算线程；具体兼容 learner/runtime 绑定尚未验收。处理器不是 estimand，不提出跨节点 bit equality。任何后续实际调用仍需要自己的相邻 actual-node 4 GiB physical/effective memory admission；历史 B05 receipt 不予继承。

该第一比较在各预定 fit 及完整 final evaluation 完成后结束；有效的负值不触发替换 seed、best checkpoint 或额外训练。实际 admission 失败、所分配完整 cap 到达、无法维持信息/reward 语义、nonfinite learner 或缺失 primary，均保留已完成事实和受损依赖后返回；不自动换节点或重复 invocation。未知成本本身不是 paid-information 负结果，也不要求先做一项 A 搜索才允许普通 B。

## 七、为什么选择（a），而不是（b）或另一轮 toy

**不选择（b）的关键不是“已经有现成付费 adapter”，而是本节点明确选择了一个无需该 adapter 的原生路径。** 新信息归每个正在运动的 UAV 所有，来自已有局部列表；可用时点在实际 step 之后；使用者是同一 UAV 的后续 actor；动作仍为合法速度；成本/收益由真实服务事件计入整段团队 reward。actor/critic 边界和前缀结构已经作为新科学语义写明，不把其决定留给 CM 暗中发明。

（b）的最强理由仍然成立一半：源没有证明这里存在独立正的“信息购买费用”，也没有证明改变观测是回报差的唯一因果来源。因此本答复**不打开独立收费传感器或纯信息价值识别问题**。若要作那种更强比较，真正缺的是具名的新信息通道、对 actor 的增量权限及同一次操作的原生成本接口；不能用本答复的移动 package 充当它。当前选择接受这个限制，直接检验有机会成本的实际控制方案，不将尚未识别的组件效果设为启动前提。

再做两组原样 finite-host 学习只会增加原问题的变异记录，不能验证这条新环境链。重新启动 numerical-locus、先求最优 paid path、先训练成功一个 oracle comparator，也不回答第一 UAV 性能问题。既有文献记录只支持“按下游 native benefit 与代价解释”的原则，不提供本任务接口、性能或新颖性；本轮不进行新文献检索。[B05 intake §7][E01] [此前 proposal §5][E11]

相比只有 generic learner 的单臂 UAV run，这个两臂设计增加了一个真正可反驳的结构选择；相比完整层级 options、多时长、更多队伍或全场传感器 redesign，它只增加一次二元前缀决策。其潜在失败同样有决策价值：若 generic 自己用免费观测和运动取得相同或更好回报，就没有理由仅凭 B05 的正值继续扩大这一前缀结构。这里没有预定正结果或自动后继。

## 八、当前暴露、实现缺口与权限

复用的 B05 机器生成暴露是：两数据集、262,144 train episodes、393,216 scalar value updates、131,072 histogram updates、196,608 evaluation episodes、458,752 total episodes、1,753,088 actual host events。各 fit 的 264 个数值从零开始，第一观察步长为 1，FULL 绝对 L2 位移 **9.9462296319907 / 9.903561290902969**；零 initial L2 的相对位移比无定义，不填零或有限比值。[B05 intake §4][E01] [EXPOSURE_AND_COST][E12]

B05 两完整调用 wall 是 **4.67 / 4.84 s，合计 9.51 s**。389 s 是首成功 start 到第二 exit 的控制/收集/集成窗口；aggregate CPU 和 scratch 未测。最初已接受 shell quoting 失败保留 supervisor 0 s、pre-admission/pre-learner 零暴露与 no-science；不把其未进入 learner 的事实扩展成新结果。原 600 s/dataset、1200 s/pair 只属于 B05，不是 UAV 配额。[B05 技术结果与 intake][E03] [E01]

**本次 consultation 的新训练数据集、环境 episodes、参数更新、评价 episodes 和 result-bearing invocations 全为零。** 本节点没有重新验收 B05 原始摘要、重算统计、导入 source、初始化 learner/environment 或运行 checkpoint probe。

科学路径已选定不等于源码 ready。确切的未来实现依赖是：将上述 recurrent PPO、开局持速时序、共同 actor/critic 输入边界、团队 reward 聚合和 final sampled comparison 绑定到指定 base/adapter；明确兼容 runtime、实际参数/更新计数与完整调用预算。这些没有现成验收证据，不从文件名或旧模型推断。它们是已界定设计的实现事实，不是另一个泛泛架构研究题。

需要的工程检查仅围绕实际改变的决策时序、信息越界、奖励尺度和主要输出：持速期间系统继续推进、actor 不读全局诊断、holding action 不伪造新决策、base 团队 reward 不被 adapter 多除一次。已有不变路径的可信检查复用。若接口未能满足上述科学语义，返回具体冲突；不默默改成收费 oracle、不删掉 null 的合法动作。

当前 §11.8 已把普通 research 的 30% orchestration 比例改为 review signal；不继承旧 general100 申请或逐行比例验收为本 B 的关卡。研究源码 2000 行、runner 600 行及适用检查/资源边界仍在。这里不请求例外、registry、validator、额外审批层或新调度设施。[现行 evidence spec §11.8.8][E14] [ENGINEERING_SCOPE_SPEC §§4–5][E15]

此次只出版完整方向答复及指定交付评论。后续卡与完整 spec 若获实际命令推进，Root 应按现有要求在任何 CM coding 前捕获同一份 committed source/spec/original checks，供既定五臂比较；本答复不建立或启动那项工程任务。原 DM 按当前 P14 接收完整答复并作 conformity/intake；不重复发送本轮、不代替 Portfolio 分配，也不改变历史记录。[AGENTS 的 focused reading/decision ladder][E17] [P14-UCOPE 段][E18]

## 九、实际读取范围

下表全部科学材料均通过连接的 GitHub 在固定证据版本 **`41ea97afb572971b7768b9ffe6402f708f00f104`** 读取。18 条允许路径均可访问；长文件采用以下相关范围，不声称阅读了未取回的全部历史。B05 原始 summaries、旧 rejected draft、未列出的 learner/checkpoint/normalizer、其他 UAV 子类和外部论文均未读取或运行。另读取了固定 TASK 及授权的交付分支/目标/Issue 11 元数据；这些不增加科学样本。

| 证据 | 路径与实际相关读取 |
| --- | --- |
| E01 | [`docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B05_INTAKE_20260907.md`][E01]：§§1–9，重点 §§2–7；长输出续读补齐。 |
| E02 | [`docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B05_SCIENCE_CARD_20260907.md`][E02]：§§2–5，以及历史准备状态/原比较的上下文。 |
| E03 | [`docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B05_RESULT_EVIDENCE_20260907.md`][E03]：两次 terminal collection 与 final pair acceptance。 |
| E04 | [`docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B04_INTAKE_20260907.md`][E04]：§§1–5，重点 harmful acquisition、规则与不确定性。 |
| E05 | [`docs/research/candidates/ucope/UCOPE_NATIVE_RETURN_ACQUISITION_B01_INTAKE_20260907.md`][E05]：完整 intake，重点 §§2–4。 |
| E06 | [`docs/research/candidates/ucope/DIRECTION.md`][E06]：Authority、Current scientific position、B04/B03/B02/B01、retained-policy disposition 与 exploration burden clarification；相关长输出续读。 |
| E07 | [`experiments/candidates/ucope/shared_data_return_model_b02/model.py`][E07]：`ReturnModel`、`collect` 等全文。 |
| E08 | [`experiments/candidates/ucope/conditioning_discriminator_r01/host.py`][E08]：`Execution`、`execute_episode` 及其上下文。 |
| E09 | [`envs/pettingzoo/uav_env.py`][E09]：1–240、265–590、1400–1630 行，判断限于 constructor、step、state/局部 obs、局部 entry 与 reward 路径；未审查所有信道实现/子类。 |
| E10 | [`envs/pettingzoo/env_adapter.py`][E10]：1–340 行，重点 `__init__/reset/step` 的实际参数和返回边界。 |
| E11 | [`docs/research/candidates/ucope/UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md`][E11]：100–220 行，文献结论只复用 §5。 |
| E12 | [`docs/research/candidates/ucope/pro_packets/20260907_uav_interface_convergence/EXPOSURE_AND_COST.json`][E12]：全文；其中原始 summary 路径只作 provenance，不向外展开。 |
| E13 | [`docs/research/candidates/ucope/pro_packets/20260907_uav_interface_convergence/ISSUE_SNAPSHOT.json`][E13]：全文；初始 discussion 快照不是当前交付状态。 |
| E14 | [`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`][E14]：55–218、280–末尾；§4、§5.2、§6.1、§11.4、§11.7–11.9。 |
| E15 | [`docs/project/ENGINEERING_SCOPE_SPEC.md`][E15]：40–150 行，使用 §§4–5 的当前普通规则。 |
| E16 | [`docs/research/portfolio/PORTFOLIO.md`][E16]：当前 P14 入口及 ucope 行；旧 B03 摘要不覆盖 B05。 |
| E17 | [`AGENTS.md`][E17]：1–200 行，focused reading、scientific tool use、当前执行分工和 decision ladder。 |
| E18 | [`docs/research/portfolio/handoffs/2026-09-07-p14-vsp02-code-and-direction-continuations.md`][E18]：读取 handoff，结论只使用 P14-UCOPE-UAV-INTERFACE-CONVERGENCE-01。 |

**因此，最终决定是开启上述一个有限的运动介导信息获取/控制 B 家族，第一对象就是处理臂与有完整合法运动和免费信息的 recurrent generic null 的 sampled native-return 比较。** 保留 B05 的有限正面证据、所有负面与零值、未知成本和未知实现事实。若获得的只是更多信息、不同动作或更高 proxy，而没有成本后原生收益，就不称为付费信息成功；即使出现原生收益，也只先支持所比较的 package，不越过本文明确放弃的因果、稳定性、转移和部署边界。

[E01]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B05_INTAKE_20260907.md
[E02]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B05_SCIENCE_CARD_20260907.md
[E03]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B05_RESULT_EVIDENCE_20260907.md
[E04]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B04_INTAKE_20260907.md
[E05]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/UCOPE_NATIVE_RETURN_ACQUISITION_B01_INTAKE_20260907.md
[E06]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/DIRECTION.md
[E07]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/experiments/candidates/ucope/shared_data_return_model_b02/model.py
[E08]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/experiments/candidates/ucope/conditioning_discriminator_r01/host.py
[E09]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/envs/pettingzoo/uav_env.py
[E10]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/envs/pettingzoo/env_adapter.py
[E11]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md
[E12]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/pro_packets/20260907_uav_interface_convergence/EXPOSURE_AND_COST.json
[E13]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/candidates/ucope/pro_packets/20260907_uav_interface_convergence/ISSUE_SNAPSHOT.json
[E14]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[E15]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/project/ENGINEERING_SCOPE_SPEC.md
[E16]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/portfolio/PORTFOLIO.md
[E17]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/AGENTS.md
[E18]: https://github.com/CartmanFatass/My-paper-code/blob/41ea97afb572971b7768b9ffe6402f708f00f104/docs/research/portfolio/handoffs/2026-09-07-p14-vsp02-code-and-direction-continuations.md
