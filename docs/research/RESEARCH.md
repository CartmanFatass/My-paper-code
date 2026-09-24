# HMASD research index

当前研究背景、共享认识、项目状态与研究计划，更新于 2026-09-23。治理依据为
[constitution](../project/OPERATING_CONSTITUTION.md)；本页维护现状，历史过程见[日期归档](archive/)。

阅读入口：[研究背景与共享认识](#研究背景与共享认识) · [方向状态](#active) · [现行计划](#current-research-plan)。

**Owner pause: lifted** 2026-09-18 about 17:55 PDT，owner 在 Claude WSL session 中解除项目暂停。
Owner 于 2026-09-23 进一步要求本任务作为科学项目管理者，给予 DM 更高自由度与韧性：失败后可以回顾整个项目，提出更广的建议并继续。当前科学选题与转向授权见 [constitution §2](../project/OPERATING_CONSTITUTION.md#2-who-does-what)，不再把结束一个配方等同于结束 DM 责任。
具体新比较仍在 NOTES 中前瞻声明；既有负证据、负责人及已接受实验保持可恢复。
**Claude 的 FSD session 仍暂时停止，仅由 owner 手动开启；G33 保持冻结。**

**当前科学项目管理：** Root task `01a0cd93-9107-7701-a7e5-84fb071ea8f7`，host `local`；
checkout `/home/fires/.codex/worktrees/project-management-sept23/hmasd-wsl`，branch `codex/project-management-sept23`。
Root 负责跨方向的科学判断、下一笔投入与实际停滞的处理；各 DM 继续自主实施、判读和发布。
Owner 随后明确按 **三个 DM 并行** 规划，另由本任务管理项目；具体责任域与下一步见[现行计划](#current-research-plan)。
原负载 B01 已完整核验，无遗留运行或 Pro；原 checkout `/home/fires/.codex/worktrees/load-capacity-sept23/hmasd-wsl`
保留实验代码及完整轨迹，旧配方停止记录不重写。人数与技能 DM 保持原责任和已固定比较。
聚合 E 的原生运行与项目级完整读取均已完成，已收回证据并结束当前聚合配方投入；原 lead 的方向级最终记录仍待补录。
完整项目建议已核验并采纳，见[采纳记录](archive/2026-09-23/RESEARCH-scientific-management-adopted.md#decision)。
Owner 在该三 DM 方案后明确要求“请继续”；Root 已一次性向原 DM1、DM3 送达接续任务，两者 native task 均为 active。
DM2 的B01/B02/B03均已完整验收。B03新共同训练区组中D/G均有实际正服务学习，但主要uniform G−D J −.010459129（11正21负），反转旧+.019697695；原样G追加投入结束，P与删除奖励配方的负证据保留。B03无遗留运行或待收结果；新Pro已完整核验并保存，B04固定比较学习型高层M与均匀标签训练U，2fits/720k train/96k eval。M已完整收取并独立验收：12文件、45更新、四面板，uniform/own最终J .453674108/.409669218，各自J与服务均32/32初末改善；own−uniform J −.044004891、24/32不利，最差服务−11.65人。固定同源source483819eba的U已原生运行，实际初始权重/头/归一化/RNG及32世界uniform面板完全匹配；当前1验收/1运行，M/U主比较待完整U。[M完整证据](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-m-fully-accepted-fixed-u-follows-unchanged)；[U运行与实际初始配对](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-fixed-u-admitted-actual-initial-pairing-verified)。[完整B03](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b03-complete-generic-auxiliary-advantage-reverses-under-fixed-uniform-evaluation)。其他任务已接续不等于新训练已准入，也不证明已加载全部新指示；没有建立跨 App 回复或汇报循环。

**计算优先级（owner，2026-09-21）：先使用配置中的 WSL 远端 `wsl_4070`，再考虑本地资源。**
远端不可用、实际资源不足或不适合所选计算时，DM 记录具体原因后使用本地；所有结果计算仍遵循实际节点准入，
不迁移已接受进程、不因观察丢失重复启动。三个 DM 的并行研究不绕过节点资源检查。

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

原生S1完整共同学习区分了局部配对、实际学习和辅助方案的净用途。B01固定P辅助的主G读出
在预定十步四格中得到正平均T（+.000293732 scalar，10/16世界正），但own J比无辅助D低.023634，
uniform比D/G低.058564/.078262且32/32世界均不利。不同技能库的前缀与读出不同，局部正T
不识别P−G互补中介或P独有机制；P−G的own正差+.008217也不能代替P−D。
[完整三臂、真实分支与反例](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b01-complete-positive-local-pairing-does-not-recover-p-service)。

通用辅助的条件性正读数也未形成重复的额外用途。旧B01 G−D uniform J +.019698、own −.031851；
新共同训练区组B03在相同旧uniform世界和原标签流下变为uniform −.010459（11正21负），
质量28/32世界更低、高度罚26/32更高，最差配对少服务6.084人/步。两臂各自own/uniform的
J和服务却都在32/32世界较实际初始化改善；真实辅助更新和参数位移不能替代额外服务收益。
新own均值J −.002056而服务+.562125，保留其最差配对−7.566人；旧own世界不同，不冒充严格复现。
这些结果削弱原样G的追加投入理由，不否定原生学习或所有辅助方法，不以小均值宣称等效。
固定评价条件排除了换外生面板解释，但不分离训练随机性来源；两探索区组和嵌套世界不建立稳定排名。
同库own/uniform差仍只回答部署后果，不能推断学习型高层对训练库形成的贡献。
[完整训练反转、实际配对、全部损失世界与成本](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b03-complete-generic-auxiliary-advantage-reverses-under-fixed-uniform-evaluation)。

低层判别奖励的负均值也不能直接判断其有害。S1共同初始化的完整M/T比较只将原生系数.5改为0，
保留技能、高层、判别器训练和熵；真实存储奖励、低层GAE/critic目标改变，首轮原生事实与D2回报匹配。
删除后own/uniform原生J分别低.096874/.124783，31/32与32/32世界不利，所有世界质量更低、
高度罚更高；但task-only自身仍学习了正平均服务，own还有一个世界优于mixed。此有限实例支持
保留原生混合目标为工作参照，削弱当前删除配方；它包含目标尺度、价值拟合和后续共同适应变化，
不识别判别语义的独立作用、MI或技能的必要性，也不解释旧pair辅助的失败。世界数不增加训练n。
同世界own低于uniform的部署读数，也不能反推训练协调器没有贡献。
[完整目标比较、数值核验与反例](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b02-complete-removing-low-discriminator-rewards-loses-native-service)。

固定数量训练后的零更新数量迁移，与回合内成员变化、cross-play 和能力异质性是不同问题。
普通策略的目标人数训练并未形成可重复的默认升级。B11中新N8训练相对N6训练在N8平均
J提高.019681931、每步多服务3.0195人；新训练区组B12在相同实际初始世界上反转为
J低.042106854、每步少服务1.1256875人，28/32世界J下降。B12的N6也低.064500572 J、
少服务2.41025人，31/32世界J下降。更高高度代价在两区组均出现，服务收益没有重复；
B12的覆盖/质量加权小计也为负，不能把高度罚的账面贡献称为独立可恢复收益。
保留B11的有用实例和B12的有利个别世界，不以池化均值隐藏反号，也不据此否定所有目标或
混合训练方法。更强的N6训练普通策略在N8有用，须保留为后续完整包比较的真实对照。
等团队步同时改变agent rows、优化工作、reward/N和联合物理条件；固定评价世界排除了本次
换面板解释，却不分离初始化、采样和训练世界的贡献。两块仍是探索，不认证普通基线充分、
纯N机制或稳定排名。[两区组、完整配对、反例与成本](candidates/agent_count_generalization/NOTES.md#2026-09-23--b12-complete-target-condition-benefit-reverses-on-fixed-development-panels)。

面对更强普通实例后，已有完整包的有限用途仍须直接读取，不能由控制变强推断差距归零。
B13把两份保留H6与B11/B12两份T6放在相同N8/N6世界，四个SET面板的原生轨迹完全复现。
相对较强B12 T6，两份H6的N8平均J仍高.046008/.068402、每步多服务3.648/4.779人，
主要覆盖收益超过平均质量损失；N6平均J/服务也正。这削弱“剩余用途仅来自选弱普通实例”的
解释，但H1有7个N8不利J世界，H2在N6可少服务5.664人；平均用途不等于逐世界占优或尾部无损。
四份旧策略及开发世界经过结果选择，完整2×2差值代数依赖，不增加训练n或识别技能机制。
它提高新前瞻包学习比较的投入价值，不构成普通基线认证；新训练须保留其自身学习、N6后果和
损失世界，不能用旧最佳权重或跨N池化替代。
[完整共同回放、原生读数与反例](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-complete-remaining-package-gains-survive-stronger-ordinary-controls)。

新训练实例相对实际初始化的学习，须与跨方法终点优势分开。B14的新H6在固定开发世界中，
N8/N6的平均原生J分别增加.353294/.370646，每步服务增加18.868/19.566人；各32个世界的
J、服务和质量均改善，高度罚均下降。完整检查点、逐步原生事实和评价隔离已核验，支持
此实例学到了有用服务，包括未训练N8；不能把最终能力全归于初始化。与此同时，具资格
未服务U均值增加.203875/.512250，分别25/32及28/32世界上升，属于更多资格与服务之外的
残余漏服务后果。一个实例和已曝光世界不增加训练复现数，也不建立技能因果或优于普通学习；
固定新SET尚在运行，最终差、各自学习及差距变化仍须完整配对读取。
[完整H6学习、反向分量和成本](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-h6-complete-new-own-policy-learning-ordinary-comparison-pending)。

S1 的学习器 scalar 为原生团队 reward 除以 N，跨 N 服务须用实际测试 N 恢复原生单位，
并在同一测试 N 内比较；改变 N 同时改变容量与联合物理条件。N=6 训练、N=4/6/8 测试的
每臂三个完整训练实例中，H6 相对普通共享 SET 在两个未见 N 的最终原生 J/覆盖均值更高，
N6 也无相对损失。但本次 B01 路径虽声明 `[-1,1]^3`，却把原始高斯动作直接乘速度执行，
只限制位置；单步检查已证实越界动作可产生超出声明分量范围的位移。保留实测包差异，
其范围须限定于这个实际动作法则，不能据此声称已在声明的有界动作任务上验证。
两臂最终高斯标准差不同，提出训练曝光的替代解释；确定性评估不采样该噪声，方差差异尚未
识别收益来源。固定策略的执行裁剪可检验直接部署路径，但不能排除既往训练曝光影响。
该探索结果也不建立一般数量不变性、训练总体排名，未分离技能、表示、内在奖励、带宽和
额外计算；保留不利中间比较与后期回落。[完整比较与成本](candidates/agent_count_generalization/NOTES.md#2026-09-22--b01-complete-comparison-and-bounded-retain-decision)；
[动作法则修正与下一实验](candidates/agent_count_generalization/NOTES.md#2026-09-22--owner-continuation-and-action-law-premise-correction)。

后续 B02 复用六个旧最终策略，在同一新世界比较原始与逐坐标裁剪执行（0 新 fits、288k eval steps）。
全部 288 对位置轨迹第一步后分叉；裁剪后 N4/6/8 的 H6−SET 原生 J 差仍为
+.029915/+.041645/+.054739。两包逐 N 平均 J 均提高，但相对差距在 N4/6 缩小、N8 扩大，
且有 4/18 策略×N 均值、86/288 世界变差。它支持这些 raw 训练旧策略在当前面板的有界部署
收益，削弱优势必须靠越界确定性执行的解释；不更改历史训练，不识别训练曝光或技能机制。
确定性越界比例也不能由高斯 sigma 排序；动作限制与边界访问必须连同服务分量读取。训练动作
映射的作用须在共同有界部署下比较实际训练，不能用部署干预的符号代替。
[完整 B02 证据与边界](candidates/agent_count_generalization/NOTES.md#2026-09-22--b02-complete-bounded-deployment-preserves-the-package-advantage)。

B03 的完整四格在每包同初始化、共同有界部署下比较 raw/clip 训练。最终未见 N 的
B_H6=+.031935、B_SET=−.037368，交互 I=B_SET−B_H6=−.069303；在 N4/6/8 均为
H6 改善、SET 变差，削弱「仅修正越界训练执行便选择性恢复 SET」的解释。SET 三个 N 均
损失覆盖，部分质量/高度改善未抵消；H6 的覆盖收益则超过质量和高度损失。共同 clip 训练后
H6−SET 未见 N 差为 +.112963，但该批只有一个训练区组，不确立总体排名、技能机制或普通
基线充分调优。第30轮未见 N 交互为正而 SET 自身仍略差，表明正交互本身不足以支持恢复；
不同阶段使用新世界，不能把曲线变化直接解释为训练退化。两包 clip 训练的最终 sigma 均高于
各自 raw 配对而服务效应相反；执行有界不约束 latent 熵，sigma 排序也不识别服务原因。
完整 B03 结束 clip-only 的自动追加；后续 B04 检验低层 raw 熵奖励对比较的影响。
[完整四格、反证与后续问题](candidates/agent_count_generalization/NOTES.md#2026-09-22--b03-complete-training-clipping-fails-selective-set-recovery)。

B04 完整两包配对仅去掉低层 raw 熵奖励，保留方差学习及 clip 训练/部署。预定最终端点
SET 未见 N 平均 J 提高 .055541，交互 Q=E_SET−E_H6 为 +.065227；SET 自身收益存在，
不只是 H6 受损。收益集中于 N8（J +.110145，覆盖 +.105040），训练 N6 的 J/覆盖也提高；
N4 仅有很小的 J 增益，覆盖/质量反而下降。H6 未见 N 平均 J 降 .009687、三个 N 覆盖均降；
共同零系数下 H6−SET 未见 N 差仍为 +.047735。只支持该开发训练块的配方响应，既不确定
技能机制、普通基线充分调优或训练总体排名，也不能把差距缩小换算为已解释的因果比例。

两包去掉熵奖励后，全窗/晚窗 raw 动作饱和均下降，但物理边界截断均增加；SET 的最终服务
收益因此不要求边界截断减少。动作均值、梯度/优化器和状态访问等路径仍未分离。SET 第15/30轮
未见 N 的 J 差为 −.031708/−.049766，与最终正收益并存；阶段间世界不同，不能据此识别晚期
恢复轨迹。这个反证要求保留配方、N 和终点范围；潜在熵、执行饱和、边界截断与实际服务不能
互相代称。新训练实例的 SET 自身收益是否重现，与选择性交互或剩余包差距是否重现是不同问题。
[完整 B04、服务组成、反证和成本](candidates/agent_count_generalization/NOTES.md#2026-09-23--b04-complete-useful-set-endpoint-response-with-a-contrary-boundary-pathway)。

新 SET 配对 B05 在独立训练实例及新世界上，最终未见 N 效应反向为 **−.045630**；
N4/6/8 的 J 差为 −.050527/−.060413/−.040734，覆盖、质量均降，惩罚均增。原始尺度和
饱和率显著降低仍重现，物理边界截断仍增加；相同诊断方向可伴随相反服务结果，不能用其
替代实际用途。因而不把零熵系数提升为默认 SET 改进；旧开发块的正结果继续保留，不能
用两个块的合并均值掩盖反号。B05 当时同时更新训练实例与世界，单独不能分开两者；
这不新增 H6/Q、充分基线认证或总体精度。两块都是有范围的探索证据。
[完整 B05、反向分量与解释边界](candidates/agent_count_generalization/NOTES.md#2026-09-23--b05-complete-reduced-raw-noise-recurs-but-set-service-benefit-reverses)。

B06 随后把四个固定 final45 策略放到两套既有世界上完整交叉（0 fits、192k eval）。
12 个历史对角的逐世界 J/回报/服务分量完全复现。未见 N 等权 d=J(0)−J(.05) 在
旧训练对 A 的两面板为 **+.055541 / +.041046**，新训练对 B 为 **−.023586 / −.045630**；
N6/N8 同样随策略对保留符号，削弱「世界面板不同即可解释原反号」的说法。但面板 B 在
每个 N、两个策略对上都降低 d，且 A/N4 从微正转负；不能抹掉面板敏感性。训练 N6 也
明显分化，因此未识别为未见人数专属故障。R/C/T 只是这张有限表的对比，不是总体方差
或因果占比。旧有用端点得以保留，零熵系数仍不提升为默认配方；未识别新的可修复机制。
B06 本身没有增加 H6 训练复现，也不认证普通基线充分合格。已有控制可复用，
但已知结果之后选择的新比较仍属于探索。
[完整交叉、分量、反证与成本](candidates/agent_count_generalization/NOTES.md#2026-09-23--b06-complete-finite-sign-reversal-follows-the-policy-pair-across-both-panels)。

B07 新 H6/.05/clip 训练实例在固定 B05 SET/.05 对照下，final45 的 N4/6/8 原生 J 差为
**+.078661 / +.140614 / +.152267**，未见 N 平均 **+.115464**，每步多服务
**2.814 / 7.733 / 8.805** 人。三个 N 的平均覆盖、质量和惩罚均有利，满足预写完整模式；
N8 的一个世界仍少服务 7.162 人。它加强保留有界完整包的探索理由，削弱“正端点仅限旧 H6
实例”的解释；两个探索实例的相近均值不建立稳定效果、技能机制或充分基线。新 fit 实测
61.825780 command min；控制原成本57.819554 min，调度不同，不构成受控效率比较。
[完整 B07 结果、反证与成本](candidates/agent_count_generalization/NOTES.md#2026-09-23--b07-complete-bounded-package-benefit-recurs-with-an-initial-policy-rival)。

B08 将原初始策略放到同一最终世界（0 fits、48k eval、.780932 command min），直接区分
自身学习增益和最终包差。H6/SET 在 N4/6/8 的平均 J、覆盖、质量均提高、惩罚均降低；
各训练终点的平均 J 和覆盖都超过两份初始策略。未见 N 的 J 自身增量为
**+.215503 / +.244588**，覆盖每步增加 **12.160 / 11.296** 人；H6 的初始 J 领先
+.144549、最终领先+.115464。SET 的 J 增量更大，而 H6 在 N6/N8 的覆盖增量更大，
故最终领先、学习增量和服务分量不可互相替代。N8 世界1545810中两包均改善但排名反转，
世界1545802中 SET 少服务6.552人/步且J略降；正均值不是所有世界均改善。
按既定分支结束初始／最终诊断，不推出初始化修复或无训练替代。B04/B05熵反证、普通
基线充分性和训练总体不确定性仍保留；没有新增训练复现或识别技能机制。
[完整 B08 读数、反例与判断](candidates/agent_count_generalization/NOTES.md#2026-09-23--b08-complete-both-packages-learn-useful-service-and-the-initial-gap-is-not-a-causal-share)。

同世界的 `D45=D0+(I_H−I_S)` 是端点差分恒等式，不是初始化与学习的独立因果份额。
正差中之差可能伴随两包都退化，负值也可能伴随两包都改善；应先读取各包自身原生增量、
绝对用途和服务分量，不能按相对差的符号直接指定初始化或训练修复。冻结 H0 仍含完整技能
结构，不能因未经参数更新就称作无技能普通基线。[完整建议、实质纠正与固定比较](candidates/agent_count_generalization/NOTES.md#2026-09-23--initial-policy-advice-adopted-with-material-revision-fixed-b08-zero-fit-study)。

固定训练值替换可以真实改变执行动作，却不产生统一服务改进。B09在原final45策略上
只把三个动作路径显式人数标量固定为.75，N6逐世界原生数组完全复现；SET在N4/N8的
J变化为−.004523/+.014978，服务人数变化为−.299/+.742人/步。N8有9/16个世界覆盖下降，
正均值由少数较大改善支持；此前不利的1545802明显改善但惩罚增加，1545810则各主要
分量恶化。未见N合并J增量+.005228和H6−SET差距缩小并不能满足“两种N均有用”的
预写判断。应保留全部世界的真实权衡，而不提升统一替换或结果选择的按N策略。
局部影子可证明当前动作/隐藏状态响应，不能替代完整原策略历史；H6对这个人数通道
有限敏感，也不能据此推出其在线技能分配不重要。该零新fit比较结束当前替换投资，
不识别训练时损害、单个位点贡献或技能机制。[完整激活、分量、反例与决定](candidates/agent_count_generalization/NOTES.md#2026-09-23--b09-complete-fixed-count-changes-behavior-without-a-uniform-service-gain)。

对后续技能分配输出的实际依赖，需要在保留原权重、局部反馈和循环记忆时直接检验。
B10把原B07 final45 H6的真实开局标签复用整回合，保留k10建议计算；普通N4/6/8面板
逐世界精确复现旧数组，两模式前十步相同，全部48个世界随后出现个体标签和执行动作差异。
平均J在N4/6/8分别提高 **+.004172/+.003888/+.009197**，未见N平均每步多服务 **.3155** 人；
42/48个世界J提高，削弱持续采用新分配是这些权重在本面板平均用途必要条件的解释。
但N8世界1545811/1545801分别少服务 **5.302/3.198** 人/步，N4平均质量下降；1545810
几乎没有覆盖恢复，仍落后SET。故保留激活充分但后果混合的部署取舍，不全面替换或按结果选N。
开局标签在全部N4/N6世界对每个成员都是同一个个体标签，也不支持用多角色分化解释该观察。
它仍保留学得的技能条件与局部记忆，改变有效标签驻留；不识别训练必要性、开局协调价值、
一般技能机制或合格flat。协调器仍计算，惩罚是S1高度代理，不能声称省计算或实测节电。
独立训练仍n=1，开发世界不构成确认。[完整服务、轨迹、反例与成本](candidates/agent_count_generalization/NOTES.md#2026-09-23--b10-complete-opening-assignment-replay-improves-means-with-consequential-local-losses)。

当前 S1 的非 FDMA、0 dB 门槛、正噪声及全干扰公式，在精确算术下使每个用户至多对一个 UAV 有资格，
冻结几何的服务人数为 `Σ_i min(e_i,c)=E−T`。负载 B01 的 80k 原生步逐步验证了该恒等式；
64 组同策略/同 N 配对世界的动作、状态、几何及循环/技能时钟在改容量时完全相同，高度项严格抵消。
容量没有进入实际策略的信息历史；这些结果支持固定几何的服务转换，不能称为在线负载适应。

容量放宽对两包全部 64 个 arm×world 的 J 都有正作用，但相对收益取决于局部资格尾部和质量组成。
N4 c10→20 时 H6/SET 额外服务 4.11225/5.66125 人，D4=−.020377（13/16 世界负）；
N8 c5→10 时为 6.248375/4.550625 人，D8=+.023481（16/16 正）。N4 的中间预测已经失败，
质量反而缓和其负交互，不能靠高度或代理指标挽救“两种 N 都是 H6 多获益”的猜想。
原 B03 两份策略在五格的 H6 平均 J/覆盖优势仍保留，N4 有 4 个不利 J 世界比较。
高容量下剩余局部截断远少于 SINR 不合格用户，只约束这些既定轨迹的容量补救空间，不是学习上界。

匹配 K40/K80 后的 N8−N4 包差残差为 +.089925/+.133783，可拆成资格、截断、质量和高度贡献，
但每机容量分区、干扰与几何仍同时变化，不识别纯人数或技能机制。每包仅一份原训练实例，
新增世界不增加学习重复。当前容量诊断已按既有 Pro 的混合结果分支结束，无自动 balanced-c
或异质能力后继；有范围的正面用途与预测失败一并保留。[完整五格、分量及停止判断](candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)。

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

匹配环境步数和 PPO epochs 时，时长调度仍可能改变事件和小批更新数，实际计算量需单独报告。
S1/cap=10 完整共同学习的每臂单训练实例比较中，分解和 AR 的事件数均约为固定周期的 7.22 倍，
高层更新均为 5 倍；实测耗时分别为 1.76/1.34 倍，终点 J 分别低 .03563/.01649。
AR 后段改善并胜过分解，仍未兑现相对固定周期的预写收益条件。这个观察削弱当前配方的回报／成本理由，
没有识别探索压力或相关性的因果作用，也未建立策略类总体排名；共享节点耗时不是方法固有速度的对照实验。
[三臂完整比较、成本与解释边界](candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)。

同样，固定策略的正比例 reward 缩放保留排序，有限优化过程仍可能改变；裁剪或一般 shaping 还可能改变目标。
FSD B05 的 CF_S 修复说明输入构造影响有限学习：三个开发块的晚窗臂间均值差约 +.059，最终 J45 仅约 +.004
且有负块；训练内上升约 +.10 不能改称处理效应。修复后的 CF_S 尚未因此成为已验证合格的最终 flat 对照。
[理论范围、输入构造与来源](archive/2026-09-21/FOUNDATIONS.md#4-学习理论表示能力和有限训练结果处在不同层面)；[B05 原始证据](https://github.com/CartmanFatass/My-paper-code/blob/00eac27c535ccffb66354f8bfac62acb504874ca/docs/research/candidates/flexible_skill_duration/NOTES.md#L1946-L2023)。

同信息重编码及加入普通结构也需作为完整学习包实测，不能默认改善。原生 S1 固定 k/N 的一次完整
共同学习中，typed-slot 稠密 actor 编码得到较低原生 J/覆盖和较高计算成本；这个历史观察保持独立。
[稠密配方比较与边界](candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)。
另一次固定 360k 训练的完整 O/P/E 比较中，普通技能条件 Deep Sets 池化 P 与 attention E 的
终点 J 为 .159861/.183016，原始 MLP O 为 .509137；P−O=−.349276、E−O=−.326121，
两者在 32 个共同世界均低于 O。E 比 P 高 .023155（20 正/12 负），仍未兑现相对原始参照的用途。
训练主体耗时 O/P/E 为 89.9204/109.7429/91.5859 min。E 已正常完成并被 Root 取回核验，
旧 observer 的 running 不再是科学状态；方向 DM 的最终 notebook 补录与原生结果完成分开记录。
每臂只有一个训练实例，共同世界没有增加训练重复数。这削弱两个具体聚合配方在已测预算下的投入理由，
没有识别单组件因果或建立表示类总体排名；共享节点计时不等于固有速度。
[P/O 方向记录](candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-p-complete-and-read-e-remains-the-fixed-third-arm)、
[E 完整原生结果](../../runs/goal_conditioned_entity_aggregation/b01_e_s922611/summary.json)、
[项目级完整核验与投入决定](archive/2026-09-23/RESEARCH-scientific-management-adopted.md#decision)。

### 5. 技能和异步性是组织决策的方式，其收益需要证据

技能的内部反馈、持续时间、终止与重选语义需要明确。合适条件下，持续 \(\tau\) 步的 option 用片段累计
reward 和 \(\gamma^\tau\) 接续价值。异步团队的共同事件链中，实际事件间隔可能短于某成员选定的驻留时间；
片段累计与折扣应按真实经过步数计算，队友先重选不表示早期时长选择的后果已结束。联合周期的跨事件回报
和采样前承诺条件价值已通过实现检查并用于完整共同学习；两种可变臂在预定终点均未高于固定周期，
每臂一个训练实例，检查通过不保证有限学习收益。[完整执行与解释边界](candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)。
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
早期 B01/B02 中，原生 S7-S2 的 W10 事实 QoS 辅助在两个训练实例对上均改善固定终点 J、QoS 和返航约束代价，
但第二对在共同事实 MSE 更高时仍有原生收益；中间面板也有 MSE 更低而 J 更差的观察。这个有限实例
当时支持进一步检验辅助训练包，并削弱“该验证误差改善是控制收益必要条件”的解释；它未区分服务预测语义
与额外表征优化／稳定化，也未建立训练总体优势。两对均有晚期 J 回落，joint 的绝对服务仍低。
每对共同事实仅来自两个初始策略世界，跨对轨迹不同；重叠窗口、同一训练对的八个评估世界都不能扩充
训练样本数。评估没有充电、切断或耗尽事件，场景具有相应机制不等于比较实际检验了充电竞争或故障恢复。
[两对完整比较、反面证据与成本](candidates/uav_service_auxiliary/NOTES.md#b02-complete-comparison-and-bounded-keep-decision--2026-09-22)。

后续 B03 的两个固定训练块已完整读完。首块最终 J 对比 S−D **+24.585407**、
G−D **+117.896434**、S−G **−93.311027**；第二块依次为 **−16.825601 / −24.945921 /
+8.120320**。普通下一观测预测 G 的服务提升两块都出现，但首块的约束成本下降变为第二块
上升，真实最低电池两块都更低；S 的服务差与 J 差都转负。两种包均未复现正均值收益，
S−G 也反号。首块 G 的有用普通比较证据继续保留，但不提升为稳定方案或服务语义的因果结论。
第二块 D/S/G 绝对 J 为 +12.170880 / −4.654721 / −12.775041；低绝对收益和较大负尾部
仍是用途判断的一部分。第二块 S−D 有 19 胜 13 负及正中位数，却有负均值；G−S 同样有
19 胜及正中位数而负均值，不能只选均值或胜率有利的一面，也不能把小均值差称为等价。

同终点开发/最终面板的 S−G 首块反号，S−D 第二块反号；时间上的学习曲线变化另行保留。
两次零更新共同端点回放进一步限制预测误差解释：首块 G 原生 J 最高而两类混合 MSE 均最高；
第二块 G 原生 J 最低而两类混合 MSE 均最低。第二块 D/S/G 的 service MSE 为
.036340059 / .044194100 / .035131848，observation MSE 为 .020839702 / .021323893 /
.019598684。G 相比 D 的平均 service 优势只在 S 来源层出现，逐片段仅 4/12 更低；
第一块 S 的轻微平均 service 优势也只来自 1/12 片段。事实分布、readout 与表征共同影响误差；
跨块事实及训练校准不同，不能直接把误差幅度当共同难度或因果中介。当前样本特征不退化，
仍未识别一个值得继续投入的修复机制。更低 MSE、有效秩或零物理事件都不能替代完整用途。

按完整 Pro 已覆盖的反号/代理改善分支，关闭当前 B03 配方，不选第三块、重调、较早终点补救、
延长训练或确认。早期正结果保留；这削弱当前方案的继续投入理由，不证明预测辅助不可能、
总体伤害或普遍目标排名。只有两个训练块；32 共同世界和 12 事实片段不增加训练重复。
[完整六格、两次回放与结束判断](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；
[G2 完整原生结果与分量](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-block-g-accepted-and-fixed-common-replay-bound)；
[首块三臂反面证据](candidates/uav_service_auxiliary/NOTES.md#2026-09-22--b03-g-complete-acceptance-and-fixed-common-endpoint-replay)。

直接训练目标干预也需要按原目标读取完整用途。S7同初始化N/R的B04仅把真实返航成本的
训练系数2改为4，评价仍为2；首轮物理事实匹配、两层真实存储奖励/GAE与学习更新不同。
固定最终32世界的R−N原生J **+549.393528**，QoS **+.108482684**、成本 **−.129009370**，
支持这个有限实例中服务和风险可同时改善。22个J有利世界之外仍有10个损失，最差−899.031058；
R仍有12个负J和6个零服务世界。同一最终策略在开发8世界却J **−218.433452**、QoS更低、
成本更高；三个已训练开发时点都未出现平均优势。较高平均最低电池也不保证返航约束成本
更低，须保留位置/最差成员风险与低尾部。该面板反号不是额外训练变化，也未识别分布偏移
或优化机制；一个训练对不能支持稳定系数排序。原生评价无充电/切断/耗尽事件，R训练的一次
充电UAV-step不建立恢复能力。此结果保留直接风险学习的机会，不复活旧MSE辅助配方，
也不证明原系数普遍不足。[完整比较、全部世界与成本](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)。

稀疏配对收益中的大量平局/小样本方差可能漏掉尾部，观察最大值不能替代预先有效的全局界。C07 LONG 的
有限上界约束该固定程序，不等于零效应、NEAR 全局最优或全部长时域方法等价。基础认识本身不推出固定 seed
数、阳性 toy、穷举或理论证明的普遍启动门槛；实际确认遵循当前 constitution。

成本包括数据取得、模型先验、训练、规划及执行；历史构造成本与复用已有制品的成本不同。VSP 的便宜参数
拟合不能忽略原采集训练，后续独立校准结果也只支持其具体模型族。较慢的离线面板没有直接测出在线服务损失，
但明确的期限、能耗或成本—回报目标可以形成有意义的新问题；无需虚构硬期限。[实证单位、固定统计读法与成本证据](archive/2026-09-21/FOUNDATIONS.md#6-实证研究是在具体条件下缩小解释空间)。

### 7. 当前研究选择放在这套认识的什么位置

A 的普通多步复用、C 的普通信息价值和 VSP 的后果模型是可复用资产；正面产出可以与结束该路线投入并存。
B/UCOPE 的局部预测、一步优势或真实后缀信用没有自动转成稳定完整收益；FOLR/MGTAP/ACVC 的不利结果限制
各自旧包，不能改名重试或外推为所有表示无用。FSD B13/B14 没有翻转旧停止判断；独立周期三臂已完成，
当前 S1/cap=10 配方结束投入，仍未建立相对固定周期的性能增益。相关支持和反面证据见后面的方向索引。

技术可达、已有价值证据、当前是否值得投入各需理由。技术失败与未执行不等于科学阴性；一个类别仍未决，
不要求维持没有选中比较的旧配方，也无需捏造“成功概率很低”。小模型可提供机制、反例或普通参照，其信息、
耦合与实施成本向 UAV 迁移仍需实测。当前没有证据判定 MARL 已饱和、技能一定无用或某个新模块必然有效。
[既有投入判断的范围](archive/2026-09-21/FOUNDATIONS.md#7-当前研究选择放在这套认识的什么位置)。

这些认识用于选择下一笔值得付费的观察。现行优先次序与比较见 [Current research plan](#current-research-plan)，
方向状态与 ownership 见下表；背景中的历史实例不产生方向激活或新的实验接受。

## Active

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `complementary_skill_learning` | 固定 N/k、完整高低层共同学习时，能否形成提高原生 UAV 服务的技能组合，并区别于普通曝光、通用辅助优化与共同适应？ | exploring | Codex DM (independent session) | 直接 DM task `01a0cdb8-10c9-7743-a05a-6dcfc42621c5`，host `local`（原生 `Jacob`），`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/5916/hmasd-wsl`，branch `codex/complementary-skill-learning`。**B03两臂完整验收，原样G配方追加投入结束。** 新共同初始化、旧uniform世界及原标签流固定；主要G−D J −.010459129、服务−.1334375人/步，11正21负；质量28/32世界更低、高度罚26/32更高。own J −.002056386而服务+.562125，保留最差配对−7.566人。D/G各自初末J/服务在own和uniform均32/32改善；D/G学习不是G增量成功。旧B01 uniform +.019697695反转，不池化、不称稳定有害或等效；B01 P局部正T无净用途、B02删除奖励失败与task-only自身学习均保留。实际2fits/720k train/128k eval/108.606496 runner min，全部24文件、90更新、8面板与实际检查点通过。B03无待收实验或旧Pro，不追加第三G块/救援/确认。**B04 M完整验收，固定U原生运行，1验收/1运行。** M的12文件、45更新、实际检查点及四面板通过独立读回；最终uniform/own J .453674108/.409669218，服务31.336938/28.989750，两种部署各自初末J/服务均32/32提高。A_M=own−uniform J −.044004891（8正24负），保留最差服务−11.65人与1700203质量初末下降。M实耗1fit/360k train/64k eval/66.182845 runner min。同源483819eba、seed260923931的固定U已准入，199个实际初始张量及归一化/RNG、完整初始uniform面板配对通过；其360k train/32k eval保持原案，完整M/U增量尚待U。[M验收](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-m-fully-accepted-fixed-u-follows-unchanged)；[U原生操作与配对](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-fixed-u-admitted-actual-initial-pairing-verified)。 完整Pro同key核验、全文读取和原文保存；M学习高层，U独立均匀标签且0高层更新，两组低层/判别器/脱离主干的事实头照常学习。主比较共同uniform部署的M−U及各自初末学习，M own另读；六面板、2fits/720k train/96k eval，保留D2记录并隔离高采样/高更新/低动作随机流。仅支持整体训练制度差，不是纯梯度或必要性机制。[全部结果与判断](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b03-complete-generic-auxiliary-advantage-reverses-under-fixed-uniform-evaluation)；[完整答复、采纳和固定协议](candidates/complementary_skill_learning/NOTES.md#2026-09-23--training-law-advice-accepted-prospective-b04-mu)；[退役M运行计划](archive/2026-09-23/RESEARCH-complementary-skill-b04-m-accepted.md)。 |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B13完整验收：0fits/128k eval，8面板/24文件和原生重算通过，四SET轨迹字节复现。H1/H2对较强S2的N8 J +.046008/+.068402、服务+3.648/4.779人/步；保留H1的7个N8不利J世界与H2的N6 −5.664人配对损失，不能认证技能机制或训练总体优势。新完整Pro已读并原文保存，固定B14新H6/.05与普通SET/.05两臂，均N6/360k、seed974201、共同外生训练世界；对称initial0/final45 N8→N6评价，2fits/720k train/128k eval；source88b67e5e0经六项针对性检查和独立审阅；H6已完整收取20文件/556MB并独立重算验收，N8/N6自身J与服务各32/32世界改善，平均服务+18.868/+19.566人/步；具资格未服务U均值却增加+.204/+.512。固定SET于23:28:03Z在同源准入运行，观察器已接管；当前2已启动fits、1完整验收，尚无SET结果或两臂差距结论。分开读终点差、各自学习增量和差距变化，保留架构初始化及全部反例；不自动追加seed/世界/训练。旧输出与Pro已收齐。[完整H6及反向分量](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-h6-complete-new-own-policy-learning-ordinary-comparison-pending)；[当前SET操作](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-fixed-set-arm-admitted-after-complete-h6-acceptance)。[完整方案及L0](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-advice-adopted-fixed-b14-fresh-h6set-learning-block-and-l0)；[完整B13](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-complete-remaining-package-gains-survive-stronger-ordinary-controls)。 |
| `uav_service_auxiliary` | 在 S7 完整共同学习中，怎样把服务改善转成包含返航风险的净收益？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。B04最终R−N J +549.393528与开发−218.433452的反号、全部负尾部及B03失败继续保留。完整咨询后固定B05仅一对新N/R，source3de3e3f71、seed914173、训练成本系数2/4、评价均2；2fits/360k train/192k eval上限。**N已完整验收**：46文件与远端hash一致、全部原始轨迹/两层GAE/检查点独立核验，1fit/180k train/96k eval、124.628160 runner min。最终32世界J **−232.025030**、QoS .216057847、成本 .180828987，14负J、1零QoS，最差J−1796.058763；开发30−0 J +149.725207、服务提高但成本+.035404663，晚期J仍回落。训练3充电UAV步、评价无充电/切断/耗尽，不能声称风险干预已兑现。固定R已在同一源/seed上原生准入运行，观察器已接管；1已验收/1运行，配对增量待完整R。保持两区组×两端点分别读取，不池化反号或自动追加。[N完整验收](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-n-fully-accepted-fixed-r-follows-unchanged)；[R原生运行](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)；[B05前瞻与分支](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-advice-adopted-b05-fixed-independent-training-recurrence)；[B04完整证据](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)。 |
| `goal_conditioned_entity_aggregation` | 当前技能条件化的实体聚合，能否比原始 MLP 或普通条件化池化提供有用的完整共同学习收益？ | reserve | Codex DM (independent session) | 原直接 DM task `01a0c7e4-e1aa-7460-a6bb-43db5c1b0898`，host `local`；原 checkout `/home/fires/.codex/worktrees/query-aggregation-sept22/hmasd-wsl` 已缺失，branch `codex/goal-conditioned-aggregation-20260922` 与原 lead 保留。固定 B01 O/P/E 的 3 fits 全部完成：每臂360k，共1.08M train/48k eval。Root 已从原节点取回并完整核对 E，三臂 J=.509137/.159861/.183016；P−O=−.349276、E−O=−.326121，均32/32世界不利；E−P=+.023155（20正/12负）。fit-body O/P/E=89.9204/109.7429/91.5859 min。每臂一个训练实例，结束这两个具体配方当前投入，不否定整个表示类；不新增第四条持续研究线。无运行中训练，原 DM 最终 notebook 补录仍待其承接，不声称已重载或交接。[P完整记录](candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-p-complete-and-read-e-remains-the-fixed-third-arm)、[E原生输出](../../runs/goal_conditioned_entity_aggregation/b01_e_s922611/summary.json)、[恢复事实与项目判断](archive/2026-09-23/RESEARCH-scientific-management-adopted.md#decision)。 |
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
| `load_critical_member_generalization` | 如何区分团队人数、总容量/负载与关键成员对服务泛化的影响？ | archived | Codex DM (independent session) | 直接 DM task `01a0cd93-9107-7701-a7e5-84fb071ea8f7`，host `local`；checkout `/home/fires/.codex/worktrees/load-capacity-sept23/hmasd-wsl`，branch `codex/load-capacity-sept23`。B01 五格已全部验收，0 fits / 80k eval / 160 episodes，command 5.911021 min；全部 160 轨迹与 64 容量配对核验通过。原 H6/SET clip/final45 在 N4c10、N4c20、N8c5、N8c10、N6c10 的 J 差为 +.058101/+.037724/+.148026/+.171507/+.102055；保留 4 个 N4 不利 J 配对结果（3 个世界）。容量交互 D4=−.020377、D8=+.023481，否定本对策略的两-N统一边际预测，正面绝对用途保留。按既有 Pro 已覆盖分支结束当前冻结容量诊断投入；0 后继 fit、无待收结果或开放 Pro，不否定更广负载/关键成员问题，不自动选择 balanced-c 或异质接口。[完整结果与停止判断](candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)。 |
| `joint_duration_skill_learning` | 在完整高低层共同学习中，新增时长选择及普通联合时长参数化能否改善有限资源下的原生服务？ | archived | Codex DM (independent session) | 直接 DM task `01a0c348-428c-7f01-bd8b-121d69543032`，host `local`；checkout `/home/fires/.codex/worktrees/joint-duration-learning/hmasd-wsl`，branch `codex/joint-duration-learning-20260921`。B01 三臂均完成 360k 步，2026-09-22 结束 S1/cap=10 配方投入：固定／分解／AR 终点 J=.49670730/.46107574/.48021814，耗时 72.34/127.22/96.59 min。每臂一个训练实例；AR 胜分解但低于固定，按既有 Pro 建议和预写规则停止，非周期策略类总体否定。全部 4 次尝试结束（含原 24k 技术失败），0 后继 fit，无运行、未收集结果或开放 Pro。[完整结果与停止判断](candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)。 |
| `local_observation_encoding` | 同一合法局部观测下，普通稠密槽位/关系编码能否改善完整 HMASD 的有限学习？ | archived | Codex DM (independent session) | 直接 DM task `01a0c6ef-7c4b-7f02-b96d-ab115d467af8`，host `local`；checkout `/home/fires/.codex/worktrees/d683/hmasd-wsl`，branch `codex/local-observation-encoding`。B01 两个 fits 完整完成，2026-09-22 结束已测试 dense 配方投入：ORIGINAL/DENSE 固定 J45 为 0.458426/0.202254，连接人数 31.939/13.416，DENSE fit wall 约 1.95 倍。已读完并核验完整 Pro 答复；0 追加 fit，无后继排队。每臂一个训练实例，停止是有范围的投资判断，不是表示类总体否定。[最终决定](candidates/local_observation_encoding/NOTES.md#2026-09-22--dm-decision-archive-the-tested-dense-recipe)；[完整结果](candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)。 |
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

**Owner，2026-09-23：三个 DM 并行，另由本任务持续担任科学项目管理者。Root 已完整核验并采纳项目建议。**
三个名额按持续的科学问题组织；一个 DM 每次推进一个明确比较，可随证据继续、简化、复现或转向。
Root 负责优先次序、跨方向认识与实际停滞，不额外占第四条研究线。当前新增学习优先回答
“改变实际训练条件是否值得”，保留技能结构和服务—风险两条独立问题；失败不产生获得正数的义务。

### 三条主线和近期动作

| DM 主线 | 问题与选择理由 | 近期比较、成本与下一观察 |
| --- | --- | --- |
| **DM1：泛化与训练条件** | B13在更强普通T6对照下仍有剩余包用途，下一观察应挑战有利旧终点的选择。 | **B14 H6完整验收，固定SET正在运行。** H6自身N8/N6平均J增加+.353294/+.370646，服务增加18.868/19.566人/步，各32/32世界同向；保留U在25/32及28/32世界上升。完整检查点、逐步原生事实和训练/评价隔离通过。source88b67e5e0的SET于23:28:03Z准入、观察器接管，当前2启动/1验收；下一观察是完整SET及两臂初末比较。[H6结果](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-h6-complete-new-own-policy-learning-ordinary-comparison-pending)及[SET操作](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-fixed-set-arm-admitted-after-complete-h6-acceptance)。完整Pro支持新N6 H6/.05对普通SET/.05，2fits/720k train/128k初末评价；固定新seed974201、共同外生世界与各自原生初始化，在原开发世界读initial0/final45。初始评价必须隔离训练环境/学习器/RNG；SET真实单类别协调器推理也计数。最终优势、各自学习与N6/局部代价分开，两臂依预案完成而非按首臂分数选择。混合N普通学习为竞争投入，未加入本块。[完整建议、采纳和协议](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-advice-adopted-fixed-b14-fresh-h6set-learning-block-and-l0)；[B13反例与判断](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-complete-remaining-package-gains-survive-stronger-ordinary-controls)；[退役B13计划](archive/2026-09-23/RESEARCH-agent-count-b13-complete.md)。 |
| **DM2：有用技能与协作学习** | B03两臂真实学习但G增量反转；训练期分配怎样塑造可用技能库，仍不能由部署比较推断。 | **B04 M完整验收，固定U原生运行，1验收/1运行。** M在own/uniform均真实学习，最终uniform J .453674108、own .409669218；A_M −.044004891与最差服务−11.65人保留，不能替代训练制度的M/U主比较。实际初始网络、头、归一化/RNG和完整uniform面板匹配；下一观察是完整U的45更新、两面板、0高层更新及原始配对。source483819eba及固定成本不变。[M完整读数](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-m-fully-accepted-fixed-u-follows-unchanged)；[U操作与实际配对](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-fixed-u-admitted-actual-initial-pairing-verified)。 uniform G−D J −.010459129（11正21负），own −.002056386，保留服务/质量/高度权衡与全部损失世界。原样G不再追加；完整Pro后采纳新M/U完整学习比较，M学习高层、U固定均匀标签且0高层更新，低层/判别器保留学习。主要比较共同uniform部署下的最终库用途和各自初末学习，M own作为后果；固定2fits/720k train/96k eval，不伪造U的learned-own。补充代数Gamma=M(final,own)−U(final,uniform)，不能替换失败的uniform主比较；承认U训练与该部署规则更对齐。新seed931区组、独立随机流及完整协议已写入notebook；不重复DM1整包比较。[完整B03](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b03-complete-generic-auxiliary-advantage-reverses-under-fixed-uniform-evaluation)；[完整答复与固定B04](candidates/complementary_skill_learning/NOTES.md#2026-09-23--training-law-advice-accepted-prospective-b04-mu)。 |
| **DM3：服务收益与风险控制** | B04最终世界的服务/J/成本共同改善与开发世界损失并存；下一判断是该有限学习干预能否在新训练实例中复现。 | **B05固定：2fits/360k train/192k eval上限/552k总交互。** N已完整收取并独立核验，最终J−232.025030、14/32负J；开发自身学习J+149.725207但成本上升，不能由单臂判定风险加权用途。N实测1fit/276k总交互、124.628160 runner min；R已按同一source3de3e3f71/seed914173原生准入，保持原系数和已曝光面板，等待完整配对。分别读B04/B05×开发/最终四格的原生J、服务、真实成本及全部损失世界；净收益消失/反转默认结束此固定配方继续训练，持续面板反号只支持窄范围观察，不选择第三对、默认系数或确认。[N验收与固定R](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)；[前瞻分支](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-advice-adopted-b05-fixed-independent-training-recurrence)；[退役N运行计划](archive/2026-09-23/RESEARCH-uav-service-b05-n-accepted.md)。 |

**DM1 的关键读法。** B13的四个旧策略与世界均带开发选择暴露；共享四个绝对读数的2×2差值
不是四次训练复现或H6×SET交互。N8原生J与实际服务的正均值有完整反例，N6平均、配对损失和
最低绝对服务必须分开。B14的共同seed/世界不等于跨架构实际权重或随机消耗相同；
终点差D45、各臂自身增量I、差距变化Delta分别读，恒等式不识别因果份额。H6最终领先而
自身未改善、或SET退化，均不完整兑现两包学习预测。B11/B12的目标训练反号继续保留。
已完成B12/B13运行计划分别[退役保存](archive/2026-09-23/RESEARCH-agent-count-b12-complete.md)、
[退役保存](archive/2026-09-23/RESEARCH-agent-count-b13-complete.md)。

**责任路由与实际状态。** DM1 复用“智能体数量泛化 DM”（task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`），
原 checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`；B11 两臂已完整准入、收取和独立判读，
B11/B12/B13原生操作、完整收取及独立判读均结束。B12反号已保留，当前目标N配方不追加；B13新共同回放仍保留H6对较强普通实例的平均用途及重要损失世界。旧输出与Pro已完整收取。B14 H6已完整收取、独立核验和判读；保留自身J/服务改善及具资格未服务U上升。固定SET在同一source88b67e5e0准入，runner445237/监督445236原生身份匹配，本任务generation117观察器已接管；当前2已启动fits、H6完整验收、SET运行，未接受SET科学结果。下一观察是完整第二臂和实际训练世界/初末评价的成对核验。[H6完整验收](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-h6-complete-new-own-policy-learning-ordinary-comparison-pending)；[SET运行与恢复入口](candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-fixed-set-arm-admitted-after-complete-h6-acceptance)。[固定协议](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-advice-adopted-fixed-b14-fresh-h6set-learning-block-and-l0)。[完整B13](candidates/agent_count_generalization/NOTES.md#2026-09-23--b13-complete-remaining-package-gains-survive-stronger-ordinary-controls)。
DM2 保留“实际互补技能学习 DM”（task `01a0cdb8-10c9-7743-a05a-6dcfc42621c5`，host `local`）；B01–B03原生工作均完整收取验收。B03固定world/label-stream的新区组反转G的uniform增量，两臂自身学习保留；原样G停止追加。完整训练制度咨询已核验和读取；B04 M/U协议与source483819eba保持固定；M全部12文件、45更新、四面板和实际检查点已独立验收，同源同seed的U已原生准入。实际初始内容和完整uniform面板匹配；当前1验收/1运行，等待完整U后的主比较。[M验收](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-m-fully-accepted-fixed-u-follows-unchanged)；[当前U操作](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-fixed-u-admitted-actual-initial-pairing-verified)。[完整读数与下一选择](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b03-complete-generic-auxiliary-advantage-reverses-under-fixed-uniform-evaluation)。
DM3 复用“控制用途预测小模块 DM”（task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`）；
原路径 `/home/fires/.codex/worktrees/d319/hmasd-wsl` 已从其已发表分支 `fefc5ca8d` 恢复干净 checkout，
B03/B04完整证据保留；DM3的B05 N已完整收取、独立核验和判读。固定R在同一源/seed上原生运行，观察器已接管；1完成验收/1运行，尚无完整N/R配对结论。[N验收及R原生操作](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)。
首次投递因任务归档明确拒绝，解除归档后才成功接受；没有重复已接受消息或新建替代 DM。
两名 DM 的任务已接续，仍须区分任务运行、prospective/实现完成和新 fit 准入。接续请求要求读取当前 main 的治理、
完整项目建议及现行背景后自主实施、判读与发布，不要求回复 Root 或逐批取得 ACK。

聚合 O/P/E 三次训练全部结束，项目级解释已完成，原 DM 的最终 notebook 补录仍须保留；
方向暂列 reserve，当前聚合配方不再追加训练。表示、周期、churn、cross-play、异质能力是三名 DM
可按证据选择的后继问题，不为其另开常驻名额。Claude FSD 仍须 owner 手动恢复，G33 继续冻结。

### 推进与投入选择

- **并行准备，保护已接受的工作。** DM2 的B03新G/D区组已完整验收，原样G增量预测失败并结束追加；完整新Pro后固定B04 M/U训练制度比较，M已完整收取验收，U已按同源同seed原生运行，实际初始配对通过；DM1 的B14 H6完整验收，自身服务学习与未服务U上升均保留，固定同源SET已原生运行，等待完整两臂判读；DM3 的B05 N已完整验收并保留服务—风险取舍，原先固定的R已原生准入运行，等待完整配对。
  原项目 Pro 覆盖的DM1/B11已执行；B12的反号分支已按完整旧咨询处理；B13咨询与比较均完成，后续B14设计咨询亦完整读取并采纳，不重发旧问题或增加owner选题环节。
  D/G/P 未完成本身不阻止独立准备；只有真实资源冲突或会改变选择的待得证据才构成等待理由。
- **按结果改变判断。** DM1 的B12未兑现N8联合用途，已降低当前训练条件配方优先级，保留两块
  相反结果。B13已完成：两份H6对较强普通策略仍有N8平均J和服务优势，提高了新学习比较的
  投入价值；训练选择、尾部和实际工作差异仍在，不能称为确认。B14的H6自身新学习已验证，
  但这不回答相对普通SET的终点差或增量；固定SET运行中，未服务U的反向变化完整保留。
  不自动增加seed、延长训练或遍历混合调度，也不据此宣称普通学习已充分。
- **每名 DM 保持科学连续性。** 说明哪个判断加强、削弱或未受影响，再自主选择值得执行的下一观察；
  保留旧负结果和开发曝光。可以有理由停止，但“当前配方失败/完成”本身不再是退回 owner 的理由。
- **形成论文结论时再确认。** 优先让已有可重复用途、最有信息价值的一线进入固定确认，按实际 claim 定义
  总体、普通主对照和3–5个新独立训练种子。其他线继续必要探索，避免三线同时铺开昂贵确认；零结果和不确定也是结果。

**计算安排。** 三个 DM 是研究责任并行，训练并发以实际节点内存/负载准入为准。优先 `wsl_4070`，
保留已接受进程，不能重复启动。DM1的B11/B12/B13均完整验收；B12为2fits/720k train/64k eval（sum command181.734382min），B13为0fits/128k eval/3.072805command min；B14固定2fits/720k train/128k eval；H6完整验收实耗360k train/64k eval、70.229585 command min，固定SET已在4070同源运行，当前2已启动fits/1验收结果；DM3 的B04两fits已完整验收，360k train/192k eval、286.676430 runner min；B05固定2fits/360k train/192k eval，N已完整验收（180k train/96k eval、124.628160 runner min），R已在4070原生运行，当前1验收/1运行；
技能的B01三fits和B02/B03各两fits均完整验收；B03为720k train/128k eval、108.606496 summed runner min，D/G为53.417284/55.189212min；B01–B03累计7完整fits/2.52M train/417280 eval、363.745819 runner min。B04 M/U仍固定2fits/720k train/96k eval；M已验收1fit/360k train/64k eval，66.182845 runner min，峰值RSS1892300KiB、CUDA allocated/reserved1531556352/2111832064 bytes。同源483819eba的U已在4070原生准入，固定360k train/32k eval；当前1验收/1运行，完整配对尚待U，峰值scratch和共享节点占用未测。[M实际成本](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-m-fully-accepted-fixed-u-follows-unchanged)；[U原生操作](candidates/complementary_skill_learning/NOTES.md#2026-09-23--b04-fixed-u-admitted-actual-initial-pairing-verified)。不同 horizon 不等价，fit 数不是额度、硬上限或必须跑满的清单。
B11与B12完整批次已有上述实测成本；计入实现、检查、必要审查、取回与完整阅读成本。

**证据入口：** [人数 B12及区组反号](candidates/agent_count_generalization/NOTES.md#2026-09-23--b12-complete-target-condition-benefit-reverses-on-fixed-development-panels)、
[负载 B01](candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)、
[技能学习](candidates/complementary_skill_learning/NOTES.md)、
[S7 B04完整风险干预](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)、
[S7 B05 N完整验收与固定R运行](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)、
[聚合 E 原始输出](../../runs/goal_conditioned_entity_aggregation/b01_e_s922611/summary.json)。
[完整项目建议与 Root 采纳决定](archive/2026-09-23/RESEARCH-scientific-management-adopted.md#decision)
保存了 Pro 的实质不同意见、S7 数值纠正、CLI 核对和当前方案的证据边界。

<a id="portfolio-review-2026-09-23-scientific-management-and-next-learning-investment"></a>

[已完成项目复盘：完整答复、数值纠正与采纳决定](archive/2026-09-23/RESEARCH-scientific-management-adopted.md#portfolio-review-2026-09-23-scientific-management-and-next-learning-investment)。

## Retirement and history

按 [constitution §4](../project/OPERATING_CONSTITUTION.md#4-three-record-types-and-one-repository-table)
维护本页：更新现状时替换旧 standing；项目评审完成或计划被替代时，提炼仍有效的决定与证据入口，
在同次发布中将过时过程退役至 `archive/<YYYY-MM-DD>/RESEARCH.md`。同日再次归档用新后缀，历史文件不覆盖。
日期是退役定位，不是有效期；仍有效的决定、暂停、lead、冻结绑定与未完成操作留在当前页。
归档不改变方向状态或恢复研究；方向 NOTES 保持原职责，共享认识在本页按主题修订。

全项目历史快照：[2026-09-21 完整退役快照](archive/2026-09-21/RESEARCH.md)，包括六次已完成 Portfolio、旧计划、
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

B08 选择前的咨询计划已退役至 [2026-09-23 选择前快照](archive/2026-09-23/RESEARCH-agent-count-b08-selected.md)；当前固定零拟合比较见上方人数方向。

B08 运行计划已退役至 [2026-09-23 完成前快照](archive/2026-09-23/RESEARCH-agent-count-b08-complete.md)；双方有用增益及当前人数通道问题见上方人数方向。
