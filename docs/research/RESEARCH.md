# HMASD research index

当前研究背景、共享认识、项目状态与研究计划，更新于 2026-09-21。治理依据为
[constitution](../project/OPERATING_CONSTITUTION.md)；本页维护现状，历史过程见[日期归档](archive/)。

阅读入口：[研究背景与共享认识](#研究背景与共享认识) · [方向状态](#active) · [现行计划](#current-research-plan)。

**Owner pause: lifted** 2026-09-18 about 17:55 PDT，owner 在 Claude WSL session 中解除项目暂停。
Owner 于 2026-09-21 明确选择四方向并行、由本任务选题并创建三个独立 DM；下表四个新问题进入 `exploring`。
方向授权覆盖各 DM 的独立研究；具体训练批次仍由其在 NOTES 中事先声明。
**Claude 的 FSD session 仍暂时停止，仅由 owner 手动开启；G33 保持冻结。**

**初始化已完成；本任务现直接担任周期方向 DM：** task `01a0c348-428c-7f01-bd8b-121d69543032`，host `local`。
Checkout `/home/fires/.codex/worktrees/joint-duration-learning/hmasd-wsl`，
branch `codex/joint-duration-learning-20260921`。当前四个 DM 均已核对实际轮次为 `gpt-6-astra` / `max`。
四个 DM 禁止互相通信，不设持续 Root 汇报、转发或进度监视；各自在本任务向 owner 报告并独立发布。
共享 Git 证据和研究背景继续按既有方法读写，Pro 咨询和本任务内有界 helpers 继续适用。
四方向并行是当前工作强度，不等于四份重训练同时占用节点，也不要求自动递补停止的方向。
**计算优先级（owner，2026-09-21）：先使用配置中的 WSL 远端 `wsl_4070`，再考虑本地资源。**
远端不可用、实际资源不足或不适合所选计算时，DM 记录具体原因后使用本地；所有结果计算仍遵循实际节点准入，
不迁移已接受进程、不因观察丢失重复启动。四个 DM 的并行研究不绕过节点资源检查。

## 研究背景与共享认识

这里维护项目共同采用的概念、已有证据及其适用边界，作为选题和解释结果的研究背景。
按主题就地修订：新证据改变哪条认识，就修订该条并保留支持/相反证据入口；不逐次追加实验经过。
各 DM 在新问题或核心假说/比较/投入选择实质改变时，从已发布 main 读取相关主题，在现有 NOTES 中说明
它怎样影响对照、预测或下一步，或为什么不适用；读完结果后，在正常结果发布中直接回写可复用的认识变化。
不以引用次数衡量使用，也不要求每批产生共识更新；具体职责与边界见 [constitution §4](../project/OPERATING_CONSTITUTION.md#4-three-record-types-and-one-repository-table)。
尚未解决的假说保留其未决性质。背景提供科学依据，具体方向状态和执行安排见后面的索引与计划。
原共识的完整论证与引用保存在 [2026-09-21 迁移前快照](archive/2026-09-21/FOUNDATIONS.md)，
专题笔记和一手来源继续在[资料目录](../rl-marl-foundations-20260907/README.md)中按需查阅。

### 1. RL 研究的是交互后果，不是组件名称

任务规定转移、可用信息、动作、奖励与终止；策略根据可用信息行动，学习过程利用数据改变策略。
在 episodic discounted 设定下，目标是 \(J(\pi)=\mathbb E[\sum_t\gamma^t R_{t+1}]\)。训练产生策略实例，
实验提供有限观测；网络复杂度、平滑动作、技能稳定性或预测准确度都不能替代完整任务收益。

HMASD 在这里是一个 MARL 学习算法，UAV 服务是检验它的任务。S1 的连接覆盖、归一化 SINR 和高度项，
与 S7 接入—回传限制、能源/返航风险及势函数，是不同的原生后果。局部链路、连接数或势函数改善不等于
端到端服务改善；比较保留对应版本的目标并读服务/风险分量。traffic queue、独占预约、移动需求等机制，
只有实际接口具备时才属于研究条件。[任务定义、原生 reward 与来源](archive/2026-09-21/FOUNDATIONS.md#1-rl-研究的是交互后果不是组件名称)。

### 2. 部分可观测性要求处理信息，不要求每次都重新训练

observation 与环境状态不同；仅凭当前 observation 未必能作闭合的 Markov 递推。历史、信念和循环记忆
可以帮助，但 RNN 不保证恢复充分状态。固定参数也能根据新观测/记忆改变行为；动作适应、信念更新、
重算计划与参数训练需分别解释。用户移动或故障可以是固定转移规律下的状态变化，不能直接等同于
训练时队友更新策略造成的非平稳性。

已知 reward 公式不等于已知行动后的联合物理后果、队友响应和未来状态。若 reward 为 \(g(Y)\)，
一般不能以 \(g(\mathbb E[Y])\) 代替 \(\mathbb E[g(Y)]\)。已知模拟器中怎样有限学习仍可构成 MARL 问题，
不需要人为隐藏原本可查的策略或物理信息。模型已知、未知量可由合法反馈识别、有限数据足以支持决策，
是三个判断；过去无法识别当期独立隐变量，也不排除估计共享转移参数。[信息、反馈与 B/C 的证据边界](archive/2026-09-21/FOUNDATIONS.md#2-部分可观测性要求处理信息不要求每次都重新训练)。

### 3. MARL 增加的是联合行为和信息结构

共享团队 reward 本身没有规定分散信息结构。CTDE 允许训练组件使用额外信息，执行 actor 使用部署时
合法可取的信息；合法团队摘要并不因“分散”名称而被禁止。信息权限沿真实 actor/critic 接口核对，
全局 coach、通信与伙伴模型的适用性也由此判断。共同参数、中心 critic 或身份编码不等于已学会合作。

原 HMASD 已有团队/个体技能、顺序高层分配和共同技能发现。“加入协调”“区分标签”本身不能承担新贡献。
需区分行为可辨认、组合对任务有用、有限训练学会选择。论文的少量有用技能统计依赖场景，不能移作当前
UAV 的测量；技能数量和子队结构是研究动机，尚非已证瓶颈。联合标签笛卡尔积的量级也不是样本复杂度倍率。
[原 HMASD 的机制与限制](https://proceedings.neurips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf)。

技能用途可能依赖搭档；实际组合预测准确不证明换搭档仍有效，需要真实执行与曝光匹配的比较，并保留
正常搭配收益。Other-Play/Fictitious Co-Play 等提供伙伴训练先例，未直接验证 HMASD 内部技能重组。
FSD B12 的特定标签计数回归不能排除身份、标签对或状态条件交互；冻结旧技能缺少阳性用途，不构成新技能
共同学习的性能上界。信息不匹配或未学好的 flat 对照也不能单独测出 hierarchy 收益。[比较条件与已有反例](archive/2026-09-21/FOUNDATIONS.md#3-marl-增加的是联合行为和信息结构)。

### 4. 学习理论、表示能力和有限训练结果处在不同层面

Bellman/策略梯度关系或表示能力不保证有限神经网络训练的效果。相同信息可有不同的有限学习难度；
固定程序在指定输入上的行为相同，也不等于两个表示类或学习过程等价。普通结构、后果模型和规划都是
有意义的参照，其收益及数据/计算代价应保留；一个固定问题被普通方法吸收，不关闭整个技能学习问题。

当任务、信息和执行语义相同，且可变周期策略类确实包含固定类时，最优值不会降低，却不保证严格提高。
令 \(J^*_{\mathcal P}\) 为策略类最优值，\(\bar J_{\mathcal P}(B)\) 为训练随机性平均的最终策略价值，
并定义学习缺口 \(\epsilon_{\mathcal P}(B)=J^*_{\mathcal P}-\bar J_{\mathcal P}(B)\)，则有限训练资源 \(B\) 下：

\[
\bar J_{\rm var}(B)-\bar J_{\rm fixed}(B)
=\bigl(J^*_{\rm var}-J^*_{\rm fixed}\bigr)
-\bigl(\epsilon_{\rm var}(B)-\epsilon_{\rm fixed}(B)\bigr).
\]

这是额外选择与学习缺口之间的定义分解，不是可估计的误差界或启动门槛。探索、估计、优化和共同学习
都可能改变缺口；更多时间选择也可能改善持续探索。实际权衡看声明资源下的学习曲线、终点和计算成本，
包括预训练及固定周期选择成本，不能从动作数量直接推出结论。

同样，固定策略的正比例 reward 缩放保留排序，有限优化过程仍可能改变；裁剪或一般 shaping 还可能改变目标。
FSD B05 的 CF_S 修复说明输入构造影响有限学习：三个开发块的晚窗臂间均值差约 +.059，最终 J45 仅约 +.004
且有负块；训练内上升约 +.10 不能改称处理效应。修复后的 CF_S 尚未因此成为已验证合格的最终 flat 对照。
[理论范围、输入构造与来源](archive/2026-09-21/FOUNDATIONS.md#4-学习理论表示能力和有限训练结果处在不同层面)；[B05 原始证据](https://github.com/CartmanFatass/My-paper-code/blob/00eac27c535ccffb66354f8bfac62acb504874ca/docs/research/candidates/flexible_skill_duration/NOTES.md#L1946-L2023)。

同信息的普通稠密重编码也需作为完整学习包实测，不能默认改善：原生 S1 固定 k/N 的一次完整共同学习
比较中，typed-slot 稠密 actor 编码同时得到较低原生 J/覆盖和较高计算成本。这个单训练种子观察只削弱
该配方在已测曝光下的投入理由，没有识别 attention、pooling 或容量的单独作用，也没有建立表示类的
总体排名或关闭其他局部表示问题。[比较、成本和单种子边界](candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)。

### 5. 技能和异步性是组织决策的方式，其收益需要证据

技能的内部反馈、持续时间、终止与重选语义需要明确。合适条件下，持续 \(\tau\) 步的 option 用片段累计
reward 和 \(\gamma^\tau\) 接续价值。异步团队的共同事件链中，实际事件间隔可能短于某成员选定的驻留时间；
片段累计与折扣应按真实经过步数计算，队友先重选不表示早期时长选择的后果已结束。联合周期的跨事件回报
和采样前承诺条件价值已通过实现检查，仍未建立原生性能增益；详见[设计与检查边界](candidates/joint_duration_skill_learning/NOTES.md#b01-implementation-accepted-for-execution--2026-09-21)。
当前 FSD/D2 的低层逐步反馈并保留循环记忆，高层重选相同标签仍可新开
credit segment；执行周期、标签变化、训练 chunk length、normalizer 更新和有效优化量不能混同。
held skills/age 未进入某些 value 输入提供了待检验问题，没有直接证明现有 critic 错误。

个体驻留、全队首次重选和有效配合持续时间不同。共同检查点、每成员独立以概率 \(p\) 重选时，全队首次
重选的平均检查数为 \(1/[1-(1-p)^n]\)；这不能直接当作任务合作的寿命。静态用户和固定 N 也不排除随轨迹
变化的有用时机，少切换或较长承诺本身不是收益。重新推理、切换目标、保持速度、保持目标并反馈导航的成本
也不同；运动惩罚不能直接记作重算费用。

充分共同输入下，确定性联合选择可以分解为各成员输出；现有 team latent 也能产生相关性。分解时长 head
不能被先验判为不会等待/接力；单成员重选事件没有额外跨成员采样关系可表达。普通自回归是强参照，有限训练
赢过分解式仍未单独识别“相关探索”的因果作用。COMA 类反事实 baseline 须服从实际采样结构；自回归后续动作
可能依赖前序动作，不能直接套用固定其他动作的边缘化。合法前缀 baseline 与成员固有因果信用也需区分。

持续时间会改变按决策与按时间采样的技能分布，判别分数可能包含占用率差异；分数提高不自动代表有用技能。
共同转移结构可以支持跨时长复用，TempoRL 等已有先例；但闭环技能、循环状态、策略版本和队友变化使固定
Markov 模型假设需要核对。已执行前缀没有提供提前换技能后的未执行轨迹。

信息价值沿发送、到达、接收者实际可行动时机和完整后果解释。C 的 NEAR 已覆盖第一个缓存敏感行动机会的
完整承诺，不能称为单步弱参照；其截断规则依赖特定宿主。资源承诺还可能改变队友下次合法行动的时刻，VSP
提供相应的有限实例。C/VSP 与理想化 CUSUM 原型均不直接建立原生 UAV 收益，oracle 名称也不自动证明最优。
[异步语义、推导、既有方法及全部适用边界](archive/2026-09-21/FOUNDATIONS.md#5-技能和异步性是组织决策的方式其收益需要证据)。

### 6. 实证研究是在具体条件下缩小解释空间

评价世界/episode 与独立训练实例回答不同不确定性；相同旧检查点上的新世界不构成新训练复现。学习曲线、
预定终点和已选最好 checkpoint 不能互换。同一历史上的不同更新能检验数据敏感性，不能生成各自行动后的
反事实轨迹。最小可检测效应取决于独立单位、方差、检验和 power，不是环境固定的“分辨率”。

完整方法比较回答实用效果，组件因果解释需要针对性控制；统计范围随实际选择曝光与抽样契约而定。
稀疏配对收益中的大量平局/小样本方差可能漏掉尾部，观察最大值不能替代预先有效的全局界。C07 LONG 的
有限上界约束该固定程序，不等于零效应、NEAR 全局最优或全部长时域方法等价。基础认识本身不推出固定 seed
数、阳性 toy、穷举或理论证明的普遍启动门槛；实际确认遵循当前 constitution。

成本包括数据取得、模型先验、训练、规划及执行；历史构造成本与复用已有制品的成本不同。VSP 的便宜参数
拟合不能忽略原采集训练，后续独立校准结果也只支持其具体模型族。较慢的离线面板没有直接测出在线服务损失，
但明确的期限、能耗或成本—回报目标可以形成有意义的新问题；无需虚构硬期限。[实证单位、固定统计读法与成本证据](archive/2026-09-21/FOUNDATIONS.md#6-实证研究是在具体条件下缩小解释空间)。

### 7. 当前研究选择放在这套认识的什么位置

A 的普通多步复用、C 的普通信息价值和 VSP 的后果模型是可复用资产；正面产出可以与结束该路线投入并存。
B/UCOPE 的局部预测、一步优势或真实后缀信用没有自动转成稳定完整收益；FOLR/MGTAP/ACVC 的不利结果限制
各自旧包，不能改名重试或外推为所有表示无用。FSD B13/B14 没有翻转旧停止判断；新 duration 比较是建议，
没有新的正实验推翻它。相关历史的支持和反面证据见后面的方向索引。

技术可达、已有价值证据、当前是否值得投入各需理由。技术失败与未执行不等于科学阴性；一个类别仍未决，
不要求维持没有选中比较的旧配方，也无需捏造“成功概率很低”。小模型可提供机制、反例或普通参照，其信息、
耦合与实施成本向 UAV 迁移仍需实测。当前没有证据判定 MARL 已饱和、技能一定无用或某个新模块必然有效。
[既有投入判断的范围](archive/2026-09-21/FOUNDATIONS.md#7-当前研究选择放在这套认识的什么位置)。

这些认识用于选择下一笔值得付费的观察。现行优先次序与比较见 [Current research plan](#current-research-plan)，
方向状态与 ownership 见下表；背景中的历史实例不产生方向激活或新的实验接受。

## Active

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `joint_duration_skill_learning` | 在完整高低层共同学习中，新增时长选择及普通联合时长参数化能否改善有限资源下的原生服务？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c348-428c-7f01-bd8b-121d69543032`，host `local`；checkout `/home/fires/.codex/worktrees/joint-duration-learning/hmasd-wsl`，branch `codex/joint-duration-learning-20260921`。B01 固定周期已完成 360k 步，预定 32 世界终点 J=.49670730，单训练实例；分解时长臂沿用同版代码、原种子和预算，已在 WSL 4070 原生运行，AR 待执行。已启动 3 次（含原 24k 步技术失败），计划总成本 4 次。尚无可变周期收益结论。[固定结果与后续比较](candidates/joint_duration_skill_learning/NOTES.md#b01-corrected-fixed-result-accepted-factored-continuation--2026-09-21)；[分解时长启动证据](../../runs/joint_duration_skill_learning/b01_factored_s2026092202/launch-manifest.json)。 |
| `local_observation_encoding` | 同一合法局部观测下，普通稠密槽位/关系编码能否改善完整 HMASD 的有限学习？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c6ef-7c4b-7f02-b96d-ab115d467af8`，host `local`；checkout `/home/fires/.codex/worktrees/d683/hmasd-wsl`，branch `codex/local-observation-encoding`。B01 两个 fits 均完整完成（输入 `efe7d61e8`，每臂 360k 团队步）：ORIGINAL/DENSE J45 为 0.458426/0.202254，平均连接 31.939/13.416；DENSE fit wall 约 1.95 倍。三个预写面板均不利；每臂仅一个训练 seed，不作总体排名。暂拟结束此配方投入，聚焦 Pro 咨询后定案；无新 fit 计划。[完整结果与判断](candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)；[已提交咨询](https://github.com/CartmanFatass/My-paper-code/blob/03eea08a6b3f3fa714b1cdc90d9339f86ed56e94/docs/research/candidates/local_observation_encoding/NOTES.md#pro-question-2026-09-22-dense-recipe-stop)。 |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。S1 N=6→4/6/8；H6 对普通共享 SET，预写 6 个探索 fits、每 fit 360k 团队步，输入 `5a250d97e`。已完整核验各臂首个 fit：最终 N4/N6/N8 的 H6−SET J=+0.021241/+0.050777/+0.062457，未见 N 均值差 +0.041849；command wall H6/SET 为 98.77/89.04 min。每臂仅一次完整训练，尚无稳定排名或训练种子总体结论；保留中途排序改变及 SET 后段回落。第二项 H6（914307）已在 `wsl_4070` 准入运行，同句柄观察。当前 3 项启动：2 完成、1 运行；其余 3 项未启动。[完整首轮比较与后续句柄](https://github.com/CartmanFatass/My-paper-code/blob/71ebc64157c7b50387b5c2e25cec80a765e361b4/docs/research/candidates/agent_count_generalization/NOTES.md)。 |
| `uav_service_auxiliary` | 未来事实端到端服务监督能否帮助 HMASD 学会接入、回传与能源约束下的协作？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c6f0-31e1-7510-bee7-4f0f8b62d821`，host `local`；checkout `/home/fires/.codex/worktrees/a335/hmasd-wsl`，branch `codex/uav-service-auxiliary`。S7-S2 v3/reward v2/arm C，固定 k=10/N=8；W10 事实 QoS 头 detach 对 joint，每臂 180k transitions。detach 已完整核验：终点 J=-644.966810、QoS=0.152040、公共事实 MSE=0.0108465，wall 138.64 min；joint 已在 `wsl_4070` 运行，源码、事实摘要和初始模型指纹相同。1 fit 完成、1 fit 运行，另有 15 秒训练前路径拒绝；无辅助包优势或训练种子总体结论，G33 冻结。[完整读数与范围](candidates/uav_service_auxiliary/NOTES.md#b01-detach-complete-and-read--2026-09-21-2220-pdt)；[joint 原生句柄](../../runs/uav_service_auxiliary/b01_joint_910021_a01/launch-manifest.json)。 |
| `skill_teammate_drift_learning` | When teammates change, what must be learned or reused to improve decisions beyond competent simple controls? | reserve | Codex DM (independent session) | DM task `01a0bdb4-cd2c-71a3-af95-a196aeed70cd`，host `local`；checkout `/home/fires/.codex/worktrees/b-unknown-joint-law/hmasd-wsl`，branch `codex/b-unknown-joint-law`。旧径向一步表路线结束；B09/B10 局部正用途保留，B11 完整轨迹增量不一致；自身网络 refresh/burn-in 未识别真实队友行为漂移，后继方案已否决。没有排队实验、诊断或 Pro；需具体行为变化、受影响的未来估计和有区别的比较，才能选择下一步。reserve 不是无价值判决或外部等待。[最新判断及 B 分支 entry-mask 修复](https://github.com/CartmanFatass/My-paper-code/blob/74fe267aa166299d93a03566e5f0ab149ff2b12d/docs/research/candidates/skill_teammate_drift_learning/NOTES.md)；修复没有追溯应用于历史/FSD 结果。 |

## Reserve

| Direction | State | Note |
| --- | --- | --- |
| `tail_return_distributional_learning` | reserve | B01 正结果保留，B02 在 MEI 内，B02 Pro 未开始。没有选中的新比较；相关新问题面对强 scalar 参照。[证据](candidates/tail_return_distributional_learning/DIRECTION.md)。 |
| `cross_play_compatible_population_learning` | reserve | 已选备用，尚无实现/实验；没有新 DM 或已接受 fits。候选是混合训练与曝光匹配的普通 self-play，评估独立 population 的预定混编及 own-team 得失。[原始范围](https://github.com/CartmanFatass/My-paper-code/blob/b793cf69b4935306708ad744b355acc4d5b33712/docs/research/portfolio/pro_packets/20260912_new_direction_discovery/archive/RESPONSE.md)。 |
| `variable_n_fleet_churn` | reserve | 保留旧 MAPR/DIRECT/BCRH 证据；后续 INTERVAL/TERMINAL 比较两次 SIG11 后没有最终 primary，仍未回答。可因新比较的信息价值再选，不自动修复或重跑。[B03 技术失败](https://github.com/CartmanFatass/My-paper-code/blob/51965a896a4e3b9288fccb6abe277c2547dc07b8/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_NATIVE_SERVICE_CREDIT_B03_RESULT_INTAKE_20260912.md)。 |
| `flexible_skill_duration` | reserve | Claude DM；session 由 owner 手动恢复。B01–B14 没有正面性能主张，B13/B14 未翻转旧高层标签信用路线的停止判断。可变周期问题保留；新共同学习比较是建议，未出现推翻停止的新阳性发现。没有活动 producer、后继批次或开放 Pro。[完整证据与收尾](https://github.com/CartmanFatass/My-paper-code/blob/00eac27c535ccffb66354f8bfac62acb504874ca/docs/research/candidates/flexible_skill_duration/NOTES.md)；[当前 notebook](candidates/flexible_skill_duration/NOTES.md)。 |

## Archived (investment only, not scientifically disproved)

以下是当前投资状态。归档不否定已获得的局部正结果，也不等于整个方法类别不可能。
没有具体新理由与可执行比较时，不维持常驻重开搜索；历史 lead/成本/接受操作见原始证据。

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `skill_information_refresh` | Can lawful estimates of multistep message value improve send-now versus retain-quota decisions through later receiver actions and communication opportunities? | archived | Codex DM (independent session) | C07 已完成。保留普通方法的 NEAR 正结果与 LONG 有限范围结论；当前宿主的继续投入结束，没有选中后继，不外推为神经方法或 UAV 增益。[停止判断](https://github.com/CartmanFatass/My-paper-code/blob/3ca4cb1f83ea869e1efca852a099db31c52b0e2c/docs/research/candidates/skill_information_refresh/NOTES.md)、[C07 claim/result](candidates/skill_information_refresh/CLAIM_near_commit_c07.md)。 |
| `vsp_03` | Can learned submission timing exploit shared service opportunities beyond a strong transparent same-information opportunity rule? | archived | Codex DM (independent session) | 普通后果/机会模型的有界正用途保留，B11 数据获取比较已完成；没有继续维护同一固定宿主的选中问题。[停止审计](candidates/vsp_03/NOTES.md)、[B09 claim/result](candidates/vsp_03/CLAIM_fitted_opportunity_b09.md)。 |
| `ucope` | Can feedback-conditioned KEEP/END of a UAV velocity commitment improve native return over ordinary feedback and fixed renewal? | archived | Codex session (direct DM; resumed original UCOPE task) | 当前 KEEP/END/copy 与 paired-suffix 配方停止；局部非零作用保留，未得到可保留的完整原生收益。原 task 的当前科学责任已转至 B，无 UCOPE 后继排队。[最终证据和判断](https://github.com/CartmanFatass/My-paper-code/blob/0d6f299c007840596405b8a359952a082a6ba567/docs/research/candidates/ucope/NOTES.md)。 |
| `vap_folr_core` | After membership changes, can organising the history a continuing agent may legitimately access beat a competent generic recurrent baseline? | archived | Codex DM | 三个 cache 对比的不利结果约束旧包；不能推出历史信息冗余或原生 UAV 的否定结论。当前配方停止。[notebook](https://github.com/CartmanFatass/My-paper-code/blob/cd3b97ab7982ac5efec86eace09d33328be841fa/docs/research/candidates/vap_folr_core/NOTES.md)。 |

更早的方向仍为 `archived`；[完整归属、停止边界与证据](archive/2026-09-21/RESEARCH.md#七全部既有方向的归属与停止边界)：
`active_post_churn_population_flow_identification`, `actuator_conditioned_partial_sharing`,
`acvc`, `capability_bound_semantic_currentness`, `commitment_residual_triggered_options`,
`contention_aware_decentralized_communication`, `degraded_incumbent_shadow_handover`, `ec4g_r1`,
`eociv_lite`, `expressibility_gated_renewal_credit_relay`, `finite_resource_relational_inductive_efficiency`,
`learned_counterfactual_agent_credit`, `metric_ground_transport_allocation`, `orbit_shadow_read`,
`recct_lite`, `roster_consistent_latent_exploration`, `scope_1s`,
`semigroup_consistent_duration_model_policy`, `termination_rule_experience_reuse`, `vsp_02`, `vsp_c1`。

## Current research plan

现行方案来自 [2026-09-21 全项目计划的 Decision](archive/2026-09-21/RESEARCH.md#本次计划的范围与纠正)。
目标是有限数据与计算下有用的联合技能和完整 UAV 服务收益。可变周期 k、可变成员 N 分别研究；
固定 k 的普通表示和学习改进也有独立价值。此处保留当前选择及依据，完整论证和其他候选按需查档。

**当前四项投入。** 已选择表中的普通局部信息组织、技能周期与有限学习、N 数量泛化、UAV 端到端服务预测。
它们分别改变表示、时间选择、训练/测试团队数量、服务监督，首问互不依赖新模块或阳性结果。
周期比较是现有计划中尚未执行的共同学习问题，此次由 owner 授权选题后单独分配；不重启旧 FSD 信用救援，
不接管 Claude notebook。技能规模、实际重组、churn、cross-play 等保留候选地位，不自动排队。

| 研究问题 | 当前优先次序与第一个比较 | 证据如何约束投入 |
| --- | --- | --- |
| **普通局部信息组织** | 首选：S1、固定 k，完整 HMASD 的现有 encoder 对普通稠密槽位/关系 encoder。 | 同一合法数值、类型/排序；保留 FiLM、GRU、高低层共同学习、discovery、PPO 和物理动作。无持久实体 ID/真值有效位，不从 simulator state 偷加 mask；不同时叠加稀疏选择、预测损失、技能规模或新 critic。B05 支持认真比较输入组织，未证明关系瓶颈。 |
| **技能周期与有限学习** | 下一项优先核心问题：固定 k 对充分知情的分解时长、普通自回归联合时长，高低层共同训练。 | 两种可变时长共享合法历史、现存承诺、team latent、当前联合技能、时长菜单/cap、critic 及更新原则；单成员重选事件没有额外跨成员采样差别。比较完整学习/服务与实际成本，不以编码阳性为前提，不延长旧 FSD 信用救援。 |
| 事实预测辅助 | 独立近邻：同一个实际训练的事实 readout，detach 对辅助梯度进入 actor/GRU。 | 两臂都有预测头；最终看完整回报，不能用更低 MSE 代替用途。先选一个后果/窗口，不叠加规划、通信、duration。 |
| 技能规模与实际重组 | 分别选择有依据的较小标签集合，或固定 k 下真实 partner-skill 重组曝光，对普通匹配训练。 | 标签组合数不是样本复杂度；保留正常搭配收益。技能可辨认不等于有任务互补性，冻结标签探针不是新共同学习的阳性门槛。 |
| **N 数量泛化** | N 轴默认入口：固定 k、每回合固定 roster 的 train-N→test-N，普通共享/set generalist 对明确干预。 | 同一测试 N 内比较；specialist 成本另计。无需同时实现 churn、独立混编与异质能力，也不依赖 S1 编码或 duration 阳性。 |
| 运行中成员变化、cross-play、异质能力 | 三个独立备选问题：服务连续性/区间信用，独立 population 混编，能力条件化共享。 | 分别继承 VNFC、CPCP、FOLR/ACPS 等证据；先明确真实任务和合法接口。技术失败、未执行和科学不利分别处理，不合成笼统“适应性”。 |
| **UAV 端到端服务预测** | S7 优先独立入口：固定 k/N，未来真实服务窗口的事实辅助，detach 对进入 actor/GRU 的梯度。 | interface v3 / reward v2 / arm C 的接入—回传、能源与接替后果；保持 G33 冻结。标签/窗口/evaluator 和端到端接入尚未绑定，需承担实际集成成本；无需先买 S1 阳性。 |
| 支持方法与条件候选 | 真实行为漂移下的经验复用/critic，任务相关 discovery，普通物理模型及学习修正，通信、尾部服务、实体/角色动作，事件终止/时钟课程。 | 只为具体待估未来量或真实服务后果选择。普通方法已解决就保留；行动接口、目标和信息权限改变单独解释，不列为前一个配方失败后的自动续集。[候选全集](archive/2026-09-21/RESEARCH.md#potential-research-directions-2026-09-21)。 |

**第一笔投入的产物与选择规则。** 普通编码比较应读完整原生 J、预定学习曲线位置、已有服务分量和实际训练/推理成本。
有用则保留普通改进；不明则按未决问题的价值选择独立重复或停止；只有代理改善且没有值得付费的新区别时结束该配方。
完整 HMASD 表示比较不能承担“层次结构胜过 flat MARL”的结论，后者另需能学好的同信息 flat 参照。
实际 horizon、种子和 fits 由选中后的 prospective note 声明，本页没有接受批次。

**周期比较的判读。** 策略类确实包含固定方案时，最优值不降低；有限训练仍受探索、估计和优化影响。
联合式只赢分解式但输固定 k，不支持增加实际复杂度；两种可变方式都有效而无可靠彼此增量，则保留简单方式。
只改变时长统计、熵或局部信用不构成服务增益。没有有用增量和具体新区别，就停止所测配方。
S1 只能检验自身覆盖/连接后果；S7 研究需要其真实服务机制，不能因 S1 阴性就自动换宿主制造机会。

研究依据在本页的[背景与共享认识](#研究背景与共享认识)中统一维护；必要正确性修复在相关新比较中共享。
完整答复、推导和原始结果留在方向 notebook / claim / runs 与日期归档。每次有新结果，重新选择下一笔有信息价值的投入，
不承诺遍历整个候选清单；并行强度不构成科学方向配额或自动补位规则。

## Retirement and history

按 [constitution §4](../project/OPERATING_CONSTITUTION.md#4-three-record-types-and-one-repository-table)
维护本页：更新现状时替换旧 standing；项目评审完成或计划被替代时，提炼仍有效的决定与证据入口，
在同次发布中将过时过程退役至 `archive/<YYYY-MM-DD>/RESEARCH.md`。同日再次归档用新后缀，历史文件不覆盖。
日期是退役定位，不是有效期；仍有效的决定、暂停、lead、冻结绑定与未完成操作留在当前页。
归档不改变方向状态或恢复研究；方向 NOTES 保持原职责，共享认识在本页按主题修订。

最近归档：[2026-09-21 完整退役快照](archive/2026-09-21/RESEARCH.md)，包括六次已完成 Portfolio、旧计划、
第三方材料和历史路由，来源提交 `49029b96e02f6a8d08717849a366e4dca4a5477c`。更早快照按需从[日期目录](archive/)查找；
本页只保留仍需引用的入口，不追加每次维护的日志或完整归档目录。

以下兼容既有引用；链接中的旧排序和任务分配只代表当时判断，现行方案以上面的 Current research plan 为准。

<a id="portfolio-review-2026-09-21-closed-direction-research-value"></a>

[关闭方向的剩余研究价值](archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-closed-direction-research-value)。

<a id="portfolio-review-2026-09-21-project-research-management"></a>

[全项目审阅及第三方报告核对](archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)。

<a id="portfolio-review-2026-09-21-temporal-learning-and-uav-design"></a>

[可变周期与 UAV 设计](archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-temporal-learning-and-uav-design)。

<a id="portfolio-review-2026-09-21-marl-concept-formation"></a>

[MARL 概念成型](archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)。

<a id="claude-advisory-reconciliation-2026-09-21"></a>

[Claude 建议核对](archive/2026-09-21/RESEARCH.md#claude-advisory-reconciliation-2026-09-21)。

<a id="potential-research-directions-2026-09-21"></a>

[潜在问题全集与全部既有方向](archive/2026-09-21/RESEARCH.md#potential-research-directions-2026-09-21)。

<a id="portfolio-review-2026-09-21-information-first-three-dm-plan"></a>

[已被替代的三 DM 计划](archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-information-first-three-dm-plan)。

<a id="fsd-planning-rationale-2026-09-21-new-advice-without-new-results"></a>

[FSD 建议与既有停止判断的核对](archive/2026-09-21/RESEARCH.md#fsd-planning-rationale-2026-09-21-new-advice-without-new-results)。

<a id="portfolio-review-2026-09-21-whole-project-evidence-led-research-plan"></a>

[全项目证据驱动计划的完整问答与决定](archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-whole-project-evidence-led-research-plan)。
