退役日期：2026-09-23。科学项目管理复盘已收取完整答复、核验并由 Root 依 owner 委托采纳。
来源：已发布 main/项目管理分支 `74ec971656eb01bd4848db0020022a664855b6ad` 的退役前索引，加本次完整聊天答复与采纳决定；
[原索引版本](https://github.com/CartmanFatass/My-paper-code/blob/74ec971656eb01bd4848db0020022a664855b6ad/docs/research/RESEARCH.md)。
本快照不再维护；旧三 DM 计划与当时方向快照保留供追溯，当前计划以现行 RESEARCH 为准。
相对 Markdown 链接仅按归档位置调整；Pro 原文完整保留，Decision 明示数值纠正。

---

# HMASD research index

当前研究背景、共享认识、项目状态与研究计划，更新于 2026-09-23。治理依据为
[constitution](../../../project/OPERATING_CONSTITUTION.md)；本页维护现状，历史过程见[日期归档](..)。

阅读入口：[研究背景与共享认识](#研究背景与共享认识) · [方向状态](#active) · [现行计划](#current-research-plan)。

**Owner pause: lifted** 2026-09-18 about 17:55 PDT，owner 在 Claude WSL session 中解除项目暂停。
Owner 于 2026-09-23 进一步要求本任务作为科学项目管理者，给予 DM 更高自由度与韧性：失败后可以回顾整个项目，提出更广的建议并继续。当前科学选题与转向授权见 [constitution §2](../../../project/OPERATING_CONSTITUTION.md#2-who-does-what)，不再把结束一个配方等同于结束 DM 责任。
具体新比较仍在 NOTES 中前瞻声明；既有负证据、负责人及已接受实验保持可恢复。
**Claude 的 FSD session 仍暂时停止，仅由 owner 手动开启；G33 保持冻结。**

**当前科学项目管理：** Root task `01a0cd93-9107-7701-a7e5-84fb071ea8f7`，host `local`；
checkout `/home/fires/.codex/worktrees/project-management-sept23/hmasd-wsl`，branch `codex/project-management-sept23`。
Root 负责跨方向的科学判断、下一笔投入与实际停滞的处理；各 DM 继续自主实施、判读和发布。
Owner 随后明确按 **三个 DM 并行** 规划，另由本任务管理项目；具体责任域与下一步见[现行计划](#current-research-plan)。
原负载 B01 已完整核验，无遗留运行或 Pro；原 checkout `/home/fires/.codex/worktrees/load-capacity-sept23/hmasd-wsl`
保留实验代码及完整轨迹，旧配方停止记录不重写。人数与技能 DM 保持原责任和已固定比较。
聚合 E 的原生运行已完成，Root 本次从原节点收回了遗留证据，详见下方项目复盘；没有重启训练或替换原 lead。
共享源码发布并不证明其他活跃任务已加载新指示；没有发送跨 App 任务通知或建立汇报循环。

**计算优先级（owner，2026-09-21）：先使用配置中的 WSL 远端 `wsl_4070`，再考虑本地资源。**
远端不可用、实际资源不足或不适合所选计算时，DM 记录具体原因后使用本地；所有结果计算仍遵循实际节点准入，
不迁移已接受进程、不因观察丢失重复启动。三个 DM 的并行研究不绕过节点资源检查。

## 研究背景与共享认识

这里维护项目共同采用的概念、已有证据及其适用边界，作为选题和解释结果的研究背景。
按主题就地修订：新证据改变哪条认识，就修订该条并保留支持/相反证据入口；不逐次追加实验经过。
各 DM 在新问题或核心假说/比较/投入选择实质改变时，从已发布 main 读取相关主题，在现有 NOTES 中说明
它怎样影响对照、预测或下一步，或为什么不适用；读完结果后，在正常结果发布中直接回写可复用的认识变化。
不以引用次数衡量使用，也不要求每批产生共识更新；具体职责与边界见 [constitution §4](../../../project/OPERATING_CONSTITUTION.md#4-three-record-types-and-one-repository-table)。
尚未解决的假说保留其未决性质。背景提供科学依据，具体方向状态和执行安排见后面的索引与计划。
原共识的完整论证与引用保存在 [2026-09-21 迁移前快照](../2026-09-21/FOUNDATIONS.md)，
专题笔记和一手来源继续在[资料目录](../../../rl-marl-foundations-20260907/README.md)中按需查阅。

### 1. RL 研究的是交互后果，不是组件名称

任务规定转移、可用信息、动作、奖励与终止；策略根据可用信息行动，学习过程利用数据改变策略。
在 episodic discounted 设定下，目标是 \(J(\pi)=\mathbb E[\sum_t\gamma^t R_{t+1}]\)。训练产生策略实例，
实验提供有限观测；网络复杂度、平滑动作、技能稳定性或预测准确度都不能替代完整任务收益。

HMASD 在这里是一个 MARL 学习算法，UAV 服务是检验它的任务。S1 的连接覆盖、归一化 SINR 和高度项，
与 S7 接入—回传限制、能源/返航风险及势函数，是不同的原生后果。局部链路、连接数或势函数改善不等于
端到端服务改善；比较保留对应版本的目标并读服务/风险分量。traffic queue、独占预约、移动需求等机制，
只有实际接口具备时才属于研究条件。[任务定义、原生 reward 与来源](../2026-09-21/FOUNDATIONS.md#1-rl-研究的是交互后果不是组件名称)。

### 2. 部分可观测性要求处理信息，不要求每次都重新训练

observation 与环境状态不同；仅凭当前 observation 未必能作闭合的 Markov 递推。历史、信念和循环记忆
可以帮助，但 RNN 不保证恢复充分状态。固定参数也能根据新观测/记忆改变行为；动作适应、信念更新、
重算计划与参数训练需分别解释。用户移动或故障可以是固定转移规律下的状态变化，不能直接等同于
训练时队友更新策略造成的非平稳性。

已知 reward 公式不等于已知行动后的联合物理后果、队友响应和未来状态。若 reward 为 \(g(Y)\)，
一般不能以 \(g(\mathbb E[Y])\) 代替 \(\mathbb E[g(Y)]\)。已知模拟器中怎样有限学习仍可构成 MARL 问题，
不需要人为隐藏原本可查的策略或物理信息。模型已知、未知量可由合法反馈识别、有限数据足以支持决策，
是三个判断；过去无法识别当期独立隐变量，也不排除估计共享转移参数。[信息、反馈与 B/C 的证据边界](../2026-09-21/FOUNDATIONS.md#2-部分可观测性要求处理信息不要求每次都重新训练)。

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
共同学习的性能上界。信息不匹配或未学好的 flat 对照也不能单独测出 hierarchy 收益。[比较条件与已有反例](../2026-09-21/FOUNDATIONS.md#3-marl-增加的是联合行为和信息结构)。

固定数量训练后的零更新数量迁移，与回合内成员变化、cross-play 和能力异质性是不同问题。
S1 的学习器 scalar 为原生团队 reward 除以 N，跨 N 服务须用实际测试 N 恢复原生单位，
并在同一测试 N 内比较；改变 N 同时改变容量与联合物理条件。N=6 训练、N=4/6/8 测试的
每臂三个完整训练实例中，H6 相对普通共享 SET 在两个未见 N 的最终原生 J/覆盖均值更高，
N6 也无相对损失。但本次 B01 路径虽声明 `[-1,1]^3`，却把原始高斯动作直接乘速度执行，
只限制位置；单步检查已证实越界动作可产生超出声明分量范围的位移。保留实测包差异，
其范围须限定于这个实际动作法则，不能据此声称已在声明的有界动作任务上验证。
两臂最终高斯标准差不同，提出训练曝光的替代解释；确定性评估不采样该噪声，方差差异尚未
识别收益来源。固定策略的执行裁剪可检验直接部署路径，但不能排除既往训练曝光影响。
该探索结果也不建立一般数量不变性、训练总体排名，未分离技能、表示、内在奖励、带宽和
额外计算；保留不利中间比较与后期回落。[完整比较与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--b01-complete-comparison-and-bounded-retain-decision)；
[动作法则修正与下一实验](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--owner-continuation-and-action-law-premise-correction)。

后续 B02 复用六个旧最终策略，在同一新世界比较原始与逐坐标裁剪执行（0 新 fits、288k eval steps）。
全部 288 对位置轨迹第一步后分叉；裁剪后 N4/6/8 的 H6−SET 原生 J 差仍为
+.029915/+.041645/+.054739。两包逐 N 平均 J 均提高，但相对差距在 N4/6 缩小、N8 扩大，
且有 4/18 策略×N 均值、86/288 世界变差。它支持这些 raw 训练旧策略在当前面板的有界部署
收益，削弱优势必须靠越界确定性执行的解释；不更改历史训练，不识别训练曝光或技能机制。
确定性越界比例也不能由高斯 sigma 排序；动作限制与边界访问必须连同服务分量读取。训练动作
映射的作用须在共同有界部署下比较实际训练，不能用部署干预的符号代替。
[完整 B02 证据与边界](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--b02-complete-bounded-deployment-preserves-the-package-advantage)。

B03 的完整四格在每包同初始化、共同有界部署下比较 raw/clip 训练。最终未见 N 的
B_H6=+.031935、B_SET=−.037368，交互 I=B_SET−B_H6=−.069303；在 N4/6/8 均为
H6 改善、SET 变差，削弱「仅修正越界训练执行便选择性恢复 SET」的解释。SET 三个 N 均
损失覆盖，部分质量/高度改善未抵消；H6 的覆盖收益则超过质量和高度损失。共同 clip 训练后
H6−SET 未见 N 差为 +.112963，但该批只有一个训练区组，不确立总体排名、技能机制或普通
基线充分调优。第30轮未见 N 交互为正而 SET 自身仍略差，表明正交互本身不足以支持恢复；
不同阶段使用新世界，不能把曲线变化直接解释为训练退化。两包 clip 训练的最终 sigma 均高于
各自 raw 配对而服务效应相反；执行有界不约束 latent 熵，sigma 排序也不识别服务原因。
完整 B03 结束 clip-only 的自动追加；后续 B04 检验低层 raw 熵奖励对比较的影响。
[完整四格、反证与后续问题](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--b03-complete-training-clipping-fails-selective-set-recovery)。

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
[完整 B04、服务组成、反证和成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b04-complete-useful-set-endpoint-response-with-a-contrary-boundary-pathway)。

新 SET 配对 B05 在独立训练实例及新世界上，最终未见 N 效应反向为 **−.045630**；
N4/6/8 的 J 差为 −.050527/−.060413/−.040734，覆盖、质量均降，惩罚均增。原始尺度和
饱和率显著降低仍重现，物理边界截断仍增加；相同诊断方向可伴随相反服务结果，不能用其
替代实际用途。因而不把零熵系数提升为默认 SET 改进；旧开发块的正结果继续保留，不能
用两个块的合并均值掩盖反号。B05 当时同时更新训练实例与世界，单独不能分开两者；
这不新增 H6/Q、充分基线认证或总体精度。两块都是有范围的探索证据。
[完整 B05、反向分量与解释边界](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b05-complete-reduced-raw-noise-recurs-but-set-service-benefit-reverses)。

B06 随后把四个固定 final45 策略放到两套既有世界上完整交叉（0 fits、192k eval）。
12 个历史对角的逐世界 J/回报/服务分量完全复现。未见 N 等权 d=J(0)−J(.05) 在
旧训练对 A 的两面板为 **+.055541 / +.041046**，新训练对 B 为 **−.023586 / −.045630**；
N6/N8 同样随策略对保留符号，削弱「世界面板不同即可解释原反号」的说法。但面板 B 在
每个 N、两个策略对上都降低 d，且 A/N4 从微正转负；不能抹掉面板敏感性。训练 N6 也
明显分化，因此未识别为未见人数专属故障。R/C/T 只是这张有限表的对比，不是总体方差
或因果占比。旧有用端点得以保留，零熵系数仍不提升为默认配方；未识别新的可修复机制。
B06 本身没有增加 H6 训练复现，也不认证普通基线充分合格。已有控制可复用，
但已知结果之后选择的新比较仍属于探索。
[完整交叉、分量、反证与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b06-complete-finite-sign-reversal-follows-the-policy-pair-across-both-panels)。

B07 新 H6/.05/clip 训练实例在固定 B05 SET/.05 对照下，final45 的 N4/6/8 原生 J 差为
**+.078661 / +.140614 / +.152267**，未见 N 平均 **+.115464**，每步多服务
**2.814 / 7.733 / 8.805** 人。三个 N 的平均覆盖、质量和惩罚均有利，满足预写完整模式；
N8 的一个世界仍少服务 7.162 人。它加强保留有界完整包的探索理由，削弱“正端点仅限旧 H6
实例”的解释；两个探索实例的相近均值不建立稳定效果、技能机制或充分基线。新 fit 实测
61.825780 command min；控制原成本57.819554 min，调度不同，不构成受控效率比较。
[完整 B07 结果、反证与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b07-complete-bounded-package-benefit-recurs-with-an-initial-policy-rival)。

B08 将原初始策略放到同一最终世界（0 fits、48k eval、.780932 command min），直接区分
自身学习增益和最终包差。H6/SET 在 N4/6/8 的平均 J、覆盖、质量均提高、惩罚均降低；
各训练终点的平均 J 和覆盖都超过两份初始策略。未见 N 的 J 自身增量为
**+.215503 / +.244588**，覆盖每步增加 **12.160 / 11.296** 人；H6 的初始 J 领先
+.144549、最终领先+.115464。SET 的 J 增量更大，而 H6 在 N6/N8 的覆盖增量更大，
故最终领先、学习增量和服务分量不可互相替代。N8 世界1545810中两包均改善但排名反转，
世界1545802中 SET 少服务6.552人/步且J略降；正均值不是所有世界均改善。
按既定分支结束初始／最终诊断，不推出初始化修复或无训练替代。B04/B05熵反证、普通
基线充分性和训练总体不确定性仍保留；没有新增训练复现或识别技能机制。
[完整 B08 读数、反例与判断](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b08-complete-both-packages-learn-useful-service-and-the-initial-gap-is-not-a-causal-share)。

同世界的 `D45=D0+(I_H−I_S)` 是端点差分恒等式，不是初始化与学习的独立因果份额。
正差中之差可能伴随两包都退化，负值也可能伴随两包都改善；应先读取各包自身原生增量、
绝对用途和服务分量，不能按相对差的符号直接指定初始化或训练修复。冻结 H0 仍含完整技能
结构，不能因未经参数更新就称作无技能普通基线。[完整建议、实质纠正与固定比较](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--initial-policy-advice-adopted-with-material-revision-fixed-b08-zero-fit-study)。

固定训练值替换可以真实改变执行动作，却不产生统一服务改进。B09在原final45策略上
只把三个动作路径显式人数标量固定为.75，N6逐世界原生数组完全复现；SET在N4/N8的
J变化为−.004523/+.014978，服务人数变化为−.299/+.742人/步。N8有9/16个世界覆盖下降，
正均值由少数较大改善支持；此前不利的1545802明显改善但惩罚增加，1545810则各主要
分量恶化。未见N合并J增量+.005228和H6−SET差距缩小并不能满足“两种N均有用”的
预写判断。应保留全部世界的真实权衡，而不提升统一替换或结果选择的按N策略。
局部影子可证明当前动作/隐藏状态响应，不能替代完整原策略历史；H6对这个人数通道
有限敏感，也不能据此推出其在线技能分配不重要。该零新fit比较结束当前替换投资，
不识别训练时损害、单个位点贡献或技能机制。[完整激活、分量、反例与决定](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b09-complete-fixed-count-changes-behavior-without-a-uniform-service-gain)。

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
独立训练仍n=1，开发世界不构成确认。[完整服务、轨迹、反例与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b10-complete-opening-assignment-replay-improves-means-with-consequential-local-losses)。

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
或异质能力后继；有范围的正面用途与预测失败一并保留。[完整五格、分量及停止判断](../../candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)。

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
[三臂完整比较、成本与解释边界](../../candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)。

同样，固定策略的正比例 reward 缩放保留排序，有限优化过程仍可能改变；裁剪或一般 shaping 还可能改变目标。
FSD B05 的 CF_S 修复说明输入构造影响有限学习：三个开发块的晚窗臂间均值差约 +.059，最终 J45 仅约 +.004
且有负块；训练内上升约 +.10 不能改称处理效应。修复后的 CF_S 尚未因此成为已验证合格的最终 flat 对照。
[理论范围、输入构造与来源](../2026-09-21/FOUNDATIONS.md#4-学习理论表示能力和有限训练结果处在不同层面)；[B05 原始证据](https://github.com/CartmanFatass/My-paper-code/blob/00eac27c535ccffb66354f8bfac62acb504874ca/docs/research/candidates/flexible_skill_duration/NOTES.md#L1946-L2023)。

同信息重编码及加入普通结构也需作为完整学习包实测，不能默认改善。原生 S1 固定 k/N 的一次完整
共同学习中，typed-slot 稠密 actor 编码得到较低原生 J/覆盖和较高计算成本；这个历史观察保持独立。
[稠密配方比较与边界](../../candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)。
另一次固定 360k 训练的比较中，在逐实体非线性前加入当前技能条件的普通 Deep Sets 池化 P，最终 J 比
原始 MLP O 低 .349276，三个服务分量均不利，fit-body 耗时约为 1.22 倍；同批 attention E 尚待完整结果。
每臂只有一个训练实例，共同评价世界没有增加训练重复数。这些结果削弱对应配方在已测预算下的投入理由，
没有识别单一组件的因果作用或建立表示类总体排名；共享节点计时也不等于固有速度。
[P/O 结果、成本与未决 E 比较](../../candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-p-complete-and-read-e-remains-the-fixed-third-arm)。

### 5. 技能和异步性是组织决策的方式，其收益需要证据

技能的内部反馈、持续时间、终止与重选语义需要明确。合适条件下，持续 \(\tau\) 步的 option 用片段累计
reward 和 \(\gamma^\tau\) 接续价值。异步团队的共同事件链中，实际事件间隔可能短于某成员选定的驻留时间；
片段累计与折扣应按真实经过步数计算，队友先重选不表示早期时长选择的后果已结束。联合周期的跨事件回报
和采样前承诺条件价值已通过实现检查并用于完整共同学习；两种可变臂在预定终点均未高于固定周期，
每臂一个训练实例，检查通过不保证有限学习收益。[完整执行与解释边界](../../candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)。
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
[异步语义、推导、既有方法及全部适用边界](../2026-09-21/FOUNDATIONS.md#5-技能和异步性是组织决策的方式其收益需要证据)。

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
[两对完整比较、反面证据与成本](../../candidates/uav_service_auxiliary/NOTES.md#b02-complete-comparison-and-bounded-keep-decision--2026-09-22)。

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
[完整六格、两次回放与结束判断](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；
[G2 完整原生结果与分量](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-block-g-accepted-and-fixed-common-replay-bound)；
[首块三臂反面证据](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-22--b03-g-complete-acceptance-and-fixed-common-endpoint-replay)。

稀疏配对收益中的大量平局/小样本方差可能漏掉尾部，观察最大值不能替代预先有效的全局界。C07 LONG 的
有限上界约束该固定程序，不等于零效应、NEAR 全局最优或全部长时域方法等价。基础认识本身不推出固定 seed
数、阳性 toy、穷举或理论证明的普遍启动门槛；实际确认遵循当前 constitution。

成本包括数据取得、模型先验、训练、规划及执行；历史构造成本与复用已有制品的成本不同。VSP 的便宜参数
拟合不能忽略原采集训练，后续独立校准结果也只支持其具体模型族。较慢的离线面板没有直接测出在线服务损失，
但明确的期限、能耗或成本—回报目标可以形成有意义的新问题；无需虚构硬期限。[实证单位、固定统计读法与成本证据](../2026-09-21/FOUNDATIONS.md#6-实证研究是在具体条件下缩小解释空间)。

### 7. 当前研究选择放在这套认识的什么位置

A 的普通多步复用、C 的普通信息价值和 VSP 的后果模型是可复用资产；正面产出可以与结束该路线投入并存。
B/UCOPE 的局部预测、一步优势或真实后缀信用没有自动转成稳定完整收益；FOLR/MGTAP/ACVC 的不利结果限制
各自旧包，不能改名重试或外推为所有表示无用。FSD B13/B14 没有翻转旧停止判断；独立周期三臂已完成，
当前 S1/cap=10 配方结束投入，仍未建立相对固定周期的性能增益。相关支持和反面证据见后面的方向索引。

技术可达、已有价值证据、当前是否值得投入各需理由。技术失败与未执行不等于科学阴性；一个类别仍未决，
不要求维持没有选中比较的旧配方，也无需捏造“成功概率很低”。小模型可提供机制、反例或普通参照，其信息、
耦合与实施成本向 UAV 迁移仍需实测。当前没有证据判定 MARL 已饱和、技能一定无用或某个新模块必然有效。
[既有投入判断的范围](../2026-09-21/FOUNDATIONS.md#7-当前研究选择放在这套认识的什么位置)。

这些认识用于选择下一笔值得付费的观察。现行优先次序与比较见 [Current research plan](#current-research-plan)，
方向状态与 ownership 见下表；背景中的历史实例不产生方向激活或新的实验接受。

## Active

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `complementary_skill_learning` | 固定 N/k、完整高低层共同学习时，能否形成提高原生 UAV 服务的技能组合，并区别于普通曝光、通用辅助优化与共同适应？ | exploring | Codex DM (independent session) | Owner 于 2026-09-23 授权独立推进；直接 DM task `01a0cdb8-10c9-7743-a05a-6dcfc42621c5`，host `local`（原生 `Jacob`），`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/5916/hmasd-wsl`，branch `codex/complementary-skill-learning`。Pro完整建议及实现/独立审查已验收，4070节点16项检查通过。固定B01 D/G/P、同一初始化块、3 fits/1.08M train/161,280 eval。D已完整验收：360k train+53,760 eval，final own/uniform J=.487212/.485045；主G读出的十步T均值为−.000008640（scalar），7/16世界为正，尚不支持本D面板的平均配对用途。G已原生准入并训练，初始完整评价和首轮事实/校准与D相同；P未启动。保留全部世界与次读数，不由单臂或MSE判定互补；固定P−G等比较待全批完成，不自动加fit，不恢复Claude FSD/G33。[D完整结果、范围与成本](../../candidates/complementary_skill_learning/NOTES.md#2026-09-23--b01-d-complete-ordinary-learned-bank-baseline-accepted)；[G原生运行与起始一致性](../../candidates/complementary_skill_learning/NOTES.md#2026-09-23--b01-g-admitted-with-the-same-initialization-and-first-facts)。 |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B10已完整验收：0 fits/48k eval/.984229 command min；普通三面板逐世界复现B07，48/48世界标签和执行动作改变。复用真实开局技能使N4/6/8平均J增加+.004172/+.003888/+.009197，未见N每步多服务.3155人；42/48世界J提高，但1545811少服务5.302人/步，N4质量均值下降。按事前混合后果分支保留具体部署取舍，不全面替换普通重选，不选按N/世界开关。固定诊断结束，无待收操作或已选后继；方向与授权保留。B07包、B08有用学习和熵反证不改；n=1，不识别技能必要性、一般机制或计算节约。[完整结果、轨迹、反例与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b10-complete-opening-assignment-replay-improves-means-with-consequential-local-losses)。 |
| `uav_service_auxiliary` | 面向控制用途的预测小模块：事实预测监督与任务后果监督怎样影响 S7 完整服务收益？ | exploring | Codex DM (independent session) | 文献第 1 项；直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。固定 B03 D/S/G×两块六 fits、两次共同端点回放全部完整验收，source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`。两块最终 S−D J **+24.585407 / −16.825601**，G−D **+117.896434 / −24.945921**，S−G **−93.311027 / +8.120320**；收益均未复现，G服务增加但成本取舍转坏，保留负尾部。共同回放中G首块两类MSE最高、第二块最低，均不能代替原生用途。按已覆盖该分支的完整Pro建议关闭当前配方，0追加/确认，无运行中操作或已选下一批；方向与lead不变。6 fits累计769.038846 runner min，零更新共同回放另1.693106 min。[完整结果与判断](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；[G2验收](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-block-g-accepted-and-fixed-common-replay-bound)。 |
| `goal_conditioned_entity_aggregation` | 当前技能条件化的实体聚合，能否比原始 MLP 或普通条件化池化提供有用的完整共同学习收益？ | exploring | Codex DM (independent session) | 文献第 3 项，直接 DM task `01a0c7e4-e1aa-7460-a6bb-43db5c1b0898`，host `local`；checkout `/home/fires/.codex/worktrees/query-aggregation-sept22/hmasd-wsl`，branch `codex/goal-conditioned-aggregation-20260922`。固定 B01 O/P/E，每臂 360k、仅最终 32 世界评价，共 3 fits / 1.08M train / 48k eval；代码与 21 项检查及独立审查已验收。O/P 均已完整核验，各 45 次更新、五组参数均移动、评价零更新。J45 O=.509137、P=.159861，P−O=−.349276，32 个共同世界均为负；覆盖用户/步 33.58394→13.53369，另两服务分量也不利。fit-body O/P 为 89.9204/109.7429 min，P/O=1.220445，计时范围及共享节点限制保留。E 已在同一 source 下新准入并训练；首份快照 8k train、0 完成更新、0 eval、无失败。实际 3 fits 已开始，2 完成/1 运行，未添加第四臂或补救训练。P 结果削弱当前配方的投入理由；每臂一个训练实例，不识别机制或稳定排名，三臂判断等待 E 完整结果。[P 完整结果与判断](../../candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-p-complete-and-read-e-remains-the-fixed-third-arm)；[E 原生句柄](../../candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-e-accepted)；[固定比较](../../candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-prospective-comparison-and-l0)。 Root 本次已从原节点收回 E 完整输出并作项目级核对，J=.183015754；原 DM 的上述“运行中”为其最后发布快照，当前原生进程已终止。原 lead 与方向级最终记录责任保留，见[当前项目复盘](#portfolio-review-2026-09-23-scientific-management-and-next-learning-investment)。 |
| `skill_teammate_drift_learning` | When teammates change, what must be learned or reused to improve decisions beyond competent simple controls? | reserve | Codex DM (independent session) | DM task `01a0bdb4-cd2c-71a3-af95-a196aeed70cd`，host `local`；checkout `/home/fires/.codex/worktrees/b-unknown-joint-law/hmasd-wsl`，branch `codex/b-unknown-joint-law`。旧径向一步表路线结束；B09/B10 局部正用途保留，B11 完整轨迹增量不一致；自身网络 refresh/burn-in 未识别真实队友行为漂移，后继方案已否决。没有排队实验、诊断或 Pro；需具体行为变化、受影响的未来估计和有区别的比较，才能选择下一步。reserve 不是无价值判决或外部等待。[最新判断及 B 分支 entry-mask 修复](https://github.com/CartmanFatass/My-paper-code/blob/74fe267aa166299d93a03566e5f0ab149ff2b12d/docs/research/candidates/skill_teammate_drift_learning/NOTES.md)；修复没有追溯应用于历史/FSD 结果。 |

## Reserve

| Direction | State | Note |
| --- | --- | --- |
| `tail_return_distributional_learning` | reserve | B01 正结果保留，B02 在 MEI 内，B02 Pro 未开始。没有选中的新比较；相关新问题面对强 scalar 参照。[证据](../../candidates/tail_return_distributional_learning/DIRECTION.md)。 |
| `cross_play_compatible_population_learning` | reserve | 已选备用，尚无实现/实验；没有新 DM 或已接受 fits。候选是混合训练与曝光匹配的普通 self-play，评估独立 population 的预定混编及 own-team 得失。[原始范围](https://github.com/CartmanFatass/My-paper-code/blob/b793cf69b4935306708ad744b355acc4d5b33712/docs/research/portfolio/pro_packets/20260912_new_direction_discovery/archive/RESPONSE.md)。 |
| `variable_n_fleet_churn` | reserve | 保留旧 MAPR/DIRECT/BCRH 证据；后续 INTERVAL/TERMINAL 比较两次 SIG11 后没有最终 primary，仍未回答。可因新比较的信息价值再选，不自动修复或重跑。[B03 技术失败](https://github.com/CartmanFatass/My-paper-code/blob/51965a896a4e3b9288fccb6abe277c2547dc07b8/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_NATIVE_SERVICE_CREDIT_B03_RESULT_INTAKE_20260912.md)。 |
| `flexible_skill_duration` | reserve | Claude DM；session 由 owner 手动恢复。B01–B14 没有正面性能主张，B13/B14 未翻转旧高层标签信用路线的停止判断。可变周期问题保留；新共同学习比较是建议，未出现推翻停止的新阳性发现。没有活动 producer、后继批次或开放 Pro。[完整证据与收尾](https://github.com/CartmanFatass/My-paper-code/blob/00eac27c535ccffb66354f8bfac62acb504874ca/docs/research/candidates/flexible_skill_duration/NOTES.md)；[当前 notebook](../../candidates/flexible_skill_duration/NOTES.md)。 |

## Archived (investment only, not scientifically disproved)

以下是当前投资状态。归档不否定已获得的局部正结果，也不等于整个方法类别不可能。
没有具体新理由与可执行比较时，不维持常驻重开搜索；历史 lead/成本/接受操作见原始证据。

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `load_critical_member_generalization` | 如何区分团队人数、总容量/负载与关键成员对服务泛化的影响？ | archived | Codex DM (independent session) | 直接 DM task `01a0cd93-9107-7701-a7e5-84fb071ea8f7`，host `local`；checkout `/home/fires/.codex/worktrees/load-capacity-sept23/hmasd-wsl`，branch `codex/load-capacity-sept23`。B01 五格已全部验收，0 fits / 80k eval / 160 episodes，command 5.911021 min；全部 160 轨迹与 64 容量配对核验通过。原 H6/SET clip/final45 在 N4c10、N4c20、N8c5、N8c10、N6c10 的 J 差为 +.058101/+.037724/+.148026/+.171507/+.102055；保留 4 个 N4 不利 J 配对结果（3 个世界）。容量交互 D4=−.020377、D8=+.023481，否定本对策略的两-N统一边际预测，正面绝对用途保留。按既有 Pro 已覆盖分支结束当前冻结容量诊断投入；0 后继 fit、无待收结果或开放 Pro，不否定更广负载/关键成员问题，不自动选择 balanced-c 或异质接口。[完整结果与停止判断](../../candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)。 |
| `joint_duration_skill_learning` | 在完整高低层共同学习中，新增时长选择及普通联合时长参数化能否改善有限资源下的原生服务？ | archived | Codex DM (independent session) | 直接 DM task `01a0c348-428c-7f01-bd8b-121d69543032`，host `local`；checkout `/home/fires/.codex/worktrees/joint-duration-learning/hmasd-wsl`，branch `codex/joint-duration-learning-20260921`。B01 三臂均完成 360k 步，2026-09-22 结束 S1/cap=10 配方投入：固定／分解／AR 终点 J=.49670730/.46107574/.48021814，耗时 72.34/127.22/96.59 min。每臂一个训练实例；AR 胜分解但低于固定，按既有 Pro 建议和预写规则停止，非周期策略类总体否定。全部 4 次尝试结束（含原 24k 技术失败），0 后继 fit，无运行、未收集结果或开放 Pro。[完整结果与停止判断](../../candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)。 |
| `local_observation_encoding` | 同一合法局部观测下，普通稠密槽位/关系编码能否改善完整 HMASD 的有限学习？ | archived | Codex DM (independent session) | 直接 DM task `01a0c6ef-7c4b-7f02-b96d-ab115d467af8`，host `local`；checkout `/home/fires/.codex/worktrees/d683/hmasd-wsl`，branch `codex/local-observation-encoding`。B01 两个 fits 完整完成，2026-09-22 结束已测试 dense 配方投入：ORIGINAL/DENSE 固定 J45 为 0.458426/0.202254，连接人数 31.939/13.416，DENSE fit wall 约 1.95 倍。已读完并核验完整 Pro 答复；0 追加 fit，无后继排队。每臂一个训练实例，停止是有范围的投资判断，不是表示类总体否定。[最终决定](../../candidates/local_observation_encoding/NOTES.md#2026-09-22--dm-decision-archive-the-tested-dense-recipe)；[完整结果](../../candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)。 |
| `skill_information_refresh` | Can lawful estimates of multistep message value improve send-now versus retain-quota decisions through later receiver actions and communication opportunities? | archived | Codex DM (independent session) | C07 已完成。保留普通方法的 NEAR 正结果与 LONG 有限范围结论；当前宿主的继续投入结束，没有选中后继，不外推为神经方法或 UAV 增益。[停止判断](https://github.com/CartmanFatass/My-paper-code/blob/3ca4cb1f83ea869e1efca852a099db31c52b0e2c/docs/research/candidates/skill_information_refresh/NOTES.md)、[C07 claim/result](../../candidates/skill_information_refresh/CLAIM_near_commit_c07.md)。 |
| `vsp_03` | Can learned submission timing exploit shared service opportunities beyond a strong transparent same-information opportunity rule? | archived | Codex DM (independent session) | 普通后果/机会模型的有界正用途保留，B11 数据获取比较已完成；没有继续维护同一固定宿主的选中问题。[停止审计](../../candidates/vsp_03/NOTES.md)、[B09 claim/result](../../candidates/vsp_03/CLAIM_fitted_opportunity_b09.md)。 |
| `ucope` | Can feedback-conditioned KEEP/END of a UAV velocity commitment improve native return over ordinary feedback and fixed renewal? | archived | Codex session (direct DM; resumed original UCOPE task) | 当前 KEEP/END/copy 与 paired-suffix 配方停止；局部非零作用保留，未得到可保留的完整原生收益。原 task 的当前科学责任已转至 B，无 UCOPE 后继排队。[最终证据和判断](https://github.com/CartmanFatass/My-paper-code/blob/0d6f299c007840596405b8a359952a082a6ba567/docs/research/candidates/ucope/NOTES.md)。 |
| `vap_folr_core` | After membership changes, can organising the history a continuing agent may legitimately access beat a competent generic recurrent baseline? | archived | Codex DM | 三个 cache 对比的不利结果约束旧包；不能推出历史信息冗余或原生 UAV 的否定结论。当前配方停止。[notebook](https://github.com/CartmanFatass/My-paper-code/blob/cd3b97ab7982ac5efec86eace09d33328be841fa/docs/research/candidates/vap_folr_core/NOTES.md)。 |

更早的方向仍为 `archived`；[完整归属、停止边界与证据](../2026-09-21/RESEARCH.md#七全部既有方向的归属与停止边界)：
`active_post_churn_population_flow_identification`, `actuator_conditioned_partial_sharing`,
`acvc`, `capability_bound_semantic_currentness`, `commitment_residual_triggered_options`,
`contention_aware_decentralized_communication`, `degraded_incumbent_shadow_handover`, `ec4g_r1`,
`eociv_lite`, `expressibility_gated_renewal_credit_relay`, `finite_resource_relational_inductive_efficiency`,
`learned_counterfactual_agent_credit`, `metric_ground_transport_allocation`, `orbit_shadow_read`,
`recct_lite`, `roster_consistent_latent_exploration`, `scope_1s`,
`semigroup_consistent_duration_model_policy`, `termination_rule_experience_reuse`, `vsp_02`, `vsp_c1`。

## Current research plan

**Owner，2026-09-23：按三个 DM 并行规划，另由本任务持续担任科学项目管理者。**
三个名额按可持续的科学问题组织；一个 DM 每次推进一个明确比较，可以随证据修订或转向。
Root 管理科学优先次序、跨方向证据与真实停滞；本任务不再另占第四条持续研究线。
目标是有限学习资源下有用的技能、泛化和完整 UAV 服务，不以完成某个旧配方或获得正数为终点。

### 三条主线和近期动作

| DM 主线 | 科学问题与已有依据 | 近期工作、成本与有用的下一观察 |
| --- | --- | --- |
| **DM1：泛化与训练条件** | 不同人数和服务负载下，普通训练能做到什么，HMASD 的剩余优势何时成立？合并考虑人数 B01–B10 与负载 B01 的证据，不为同一 H6/SET 差距再拆出一个容量 DM。已有有界包优势，但去熵、固定人数通道、持续重选等解释各受反证约束。 | 首选候选为普通 SET 在 N6/c10 与 N8/c10 各训练 360k，最终共同测试 N8 与 N6，约 **2 新 fits / 720k train / 64k eval**。目标是观察实际 N8 资格、服务和 J 能否改善，以及 N6 专门化代价。N8 更多 agent rows、reward/N 尺度和联合物理条件需明示，不能称纯人数因果。混合人数训练是可替代设计，由完整项目建议和 prospective note 定稿。 |
| **DM2：有用技能与协作学习** | 如何在完整共同学习中得到真正对团队服务有用的技能组合？技能可辨认、组合预测准确与有用互补不同；人数 B10 不证明技能训练无用。 | 继续已固定的 **D/G/P 三臂比较**：每臂 360k，整批 3 fits；最新发布 D 已完成 360k 和评价，G 已原生准入并训练，P 未启动；尚待完成 **2 个既有计划 fits**。先读完整 J、服务、真实组合用途及成本，区分普通辅助效果和组合结构增量。结果不利时可改变真实重组曝光、学习目标或简化方法，保留原三臂结果，不自动停工或改终点。 |
| **DM3：服务收益与风险控制** | 怎样把学习到的信息变成稳定的端到端服务，同时处理返航与能源代价？S7 B03 中 G 的服务增益重现、成本改善却反号，说明只提高预测精度没有回答这个控制问题。 | 先把旧服务/成本证据和真实 reward、critic 路径连起来，选择一个直接学习比较。当前可批评的具体候选：同一任务、actor 信息、reward 系数和训练曝光下，普通总价值 critic 对按原系数组合的服务/成本分项价值估计；这是一种待测试的学习解释，不是已诊断的故障。初步规模 **2 fits、每臂 180k**，最终 horizon/评价/归一化在新 NOTES 中定稿。看完整 J、QoS、返航约束成本、真实电量低尾及各世界损失，不以 critic 或辅助 MSE 决定保留。 |

**责任路由与实际状态。** DM1 计划由现有“智能体数量泛化 DM”继续承担
（task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`）；B10 已完成，没有在途运行或选定后继。
DM2 保留“实际互补技能学习 DM”（task `01a0cdb8-10c9-7743-a05a-6dcfc42621c5`，host `local`）
及其原合同。DM3 计划复用“控制用途预测小模块 DM”（task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`）；
它已完成 B03、当前未加载，旧 checkout 缺失，新研究尚未接续。该路由是规划，不声称已投递任务或被会话采纳。
Root 负责恢复可工作的原责任路径，保留原证据；不因路径缺失创建第二名同方向 DM。

旧聚合 O/P/E 的运行已经结束，Root 已收回 E；原方向的最终 notebook 补录责任保持可恢复。
这项收尾不成为第四条持续新训练线。表示/聚合、可变周期、churn、cross-play、异质能力等是
这三名 DM 可按证据采用的后继问题，当前不另开常驻名额；Claude FSD 的手动恢复约束与 G33 冻结保持原义。
方向表保留各自历史合同、负责人和未结记录，不能把表中尚有收尾记录的行数当作并行训练数。

### 推进顺序和失败后的行动

1. **当前窗口：** DM2 完成已固定批次；DM1 定稿实际训练条件比较；DM3 定稿服务/成本学习假说。
   实现、文献/代码核对和已保存结果分析可以并行。正在生成的项目级 Pro 建议覆盖下一笔训练选择，
   回来后按三个 DM 的最新约束采纳，不重发同一个问题，也不等待 owner 再次选题。
2. **下一次结果边界：** 每名 DM 说明哪个判断被加强/削弱、最有价值的下一观察是什么，并自主推进。
   可以继续、复现、简化或换问题；不得只以“本配方失败、等待重新授权”结束。新解释要承担可区别的预测，
   但不要求穷尽所有诊断或每次提出新架构。记录失败后沿用的开发曝光，不能换名字清零。
3. **形成论文结论时：** 由最有信息价值且已有可重复用途的路线先进入固定确认；按实际 claim 定义总体、
   普通主对照和 3–5 个新独立训练种子。其余 DM 继续探索或检验关键替代解释，不让三条线同时铺开昂贵确认。
   探索中合理的零结果和无法区分也更新计划，不被包装成等效或总体无效。

**计算安排。** 三个 DM 的并行是研究责任并行，训练并发取决于当时节点负载和内存准入。
优先保存并完成已经接受的工作；新训练优先使用 `wsl_4070`，不打断、迁移或重复已接受进程。
当前概念性增量为 DM1 的 2 fits 与 DM3 的 2 fits，另有技能原批次尚待完成的约 2 fits；
它们的 horizon 不同，不能把 fit 个数当统一耗时，也不是额度、硬上限或六次都必须启动的承诺。
若 Pro/代码事实改变设计，由负责 DM 说明信息价值与成本后调整。全局没有每个实验再向 Root 申请的步骤。

**证据入口：** [人数 B10](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b10-complete-opening-assignment-replay-improves-means-with-consequential-local-losses)、
[负载 B01](../../candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)、
[技能学习](../../candidates/complementary_skill_learning/NOTES.md)、
[S7 B03](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)、
[聚合 E 原始输出](../../../../runs/goal_conditioned_entity_aggregation/b01_e_s922611/summary.json)。
服务/成本分项候选的接口依据为 `envs/pettingzoo/relay/energy_aware.py` 的
`_calculate_constrained_safety_reward` 及 `tests/scenario7_reward_safety_test.py`；已有分量接口不是改善学习的实证。
[前一版项目计划](RESEARCH-before-three-dm-plan.md)仅供追溯；
[当前待答项目问题](#portfolio-review-2026-09-23-scientific-management-and-next-learning-investment)的已发送原文与 Answer 位置保持不变。

## Portfolio review 2026-09-23 scientific-management-and-next-learning-investment

Conversation: new; private Jev conversation address remains only in local operation state.

### Question and delegated decision

Owner 的当前要求：“我希望你能做项目的管理者 从一个科学家的角度来看 我们如何推进研究 当前我们DM有频繁停滞的问题 我希望DM能够有更高的自由度和更强的韧性 不要在失败时局限于当前方向 可以来回顾整个研究project 来给出更广视角的建议 然后继续”。

Root 已据此落实 section 2 的选题与转向委托。这里请求科学建议，不请求 Pro 批准规则，
也不把 owner 再次确认当作研究下一步。核心决定是：**保留项目已得到的有界正证据与所有反证，下一笔真实学习投入最应该回答什么？**
请批评下面具体的普通 SET 训练条件比较，也可选择一个更有价值、当前能执行的替代；
不要仅在每个旧配方末尾重述停止条件，或把所有未决机制自动列为诊断队列。

### Current evidence and changed judgments

以下证据在本问题的 `source_sha`，除非明确指定另一 revision。完整结果和旧的停止判断保留。

- 人数研究：B03/B07 共同有界执行下未见 N 的 H6−SET 平均 J 差分别约 +.112963 / +.115464；
  B08 双方都实际学到服务。B04 的去熵收益未在 B05 重现，B06 交叉世界后符号仍随策略对保留，
  因而不把“去熵”当默认修复。B09 固定人数通道也无统一服务改善。
  **最新 B10 已完成**（发布 `1c247f3eccd859a06773dc9cee7b90f5cb9cfb40`）：保留开局联合标签而继续局部反馈/循环状态，
  N4/6/8 的 R−O J 为 +.004172080 / +.003888290 / +.009196934；42/48 世界 J 更高，
  但 N8 有 −5.302、−3.198 用户/步的损失。没有选中下一批；不能由此声称技能训练无用、普通 flat 已充分，
  或持续重分配普遍有害。初始标签多数成员相同也限制了“分工”解释。
  读 `candidates/agent_count_generalization/NOTES.md` 的 B07、B08、B10 complete entries；
  直接结果为 `runs/agent_count_generalization/s1_initial_policy_b08/summary.json` 与
  `runs/agent_count_generalization/s1_initial_assignment_b10/summary.json`（大文件可选取 judgment 所需 arrays/counters）。
- 负载 B01：0 fits / 80k eval，五格固定 H6/SET 策略包差均正，但容量交互 D4=−.020377、D8=+.023481，
  统一边际预测失败。N8/c10 的 SET 平均资格用户 20.00175、资格内未服务 .72350，H6 对应 29.654、.396875；
  在这些固定路径上主要不是剩余容量截断。此为学习问题的动机，不是“普通学习必能恢复”的证据、物理最优界或纯 N 归因。
  SET 在训练 N6 也落后，是纯粹未见 N 解释的反证。读
  `candidates/load_critical_member_generalization/NOTES.md` 的 B01 complete entry（资格表、working update），
  以及 `runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/summary.json`。
- S7 服务辅助 B03：S−D、G−D 都在两个训练块之间反号；G 的服务提升重现而返航/约束成本改善不重现。
  两块本来就使用相同最终世界 936001–936032，不能再用一个 B06 式跨世界诊断来假装解决反号。
  服务与风险的联合控制问题仍可有价值，重复 MSE 辅助不因此获得理由。
  读 `candidates/uav_service_auxiliary/NOTES.md` 的 B03 prospective comparison 及
  “B03 second common replay accepted and current recipe closed”；六个 `runs/uav_service_auxiliary/b03_[dsg]_<seed>_a*/summary.json`
  是原结果（912211 的 D 为 a02，其余 a01）。
- 实际互补技能 DM 正在执行固定 D/G/P 共同学习比较：3 fits、每臂 360k；本次读取时 D 已 240k，G/P 未开始。
  该比较已有完整 Pro 建议和独立工程检查；Root 不更改它，不另开一个重叠的辅助预测包。
  读 `candidates/complementary_skill_learning/NOTES.md` 的 complete advice/adoption、B01 learning comparison 与 implementation acceptance。
- 聚合 O/P/E 是另一个停止案例：**E 其实已在 2026-09-23 02:00:05 UTC 正常退出**，不是仍需等训练。
  原 observer 仍保留 running 和未消费 checkpoint，delivery_unknown/FileNotFoundError，cwd 指向已不存在的 checkout；
  具体缺失文件不能仅由该错误确定。Root 在此任务只读核对原句柄并收回 9 个原生文件，529857 bytes，逐文件 SHA-256 一致，
  未重启、未重发、未改变原 lead 或原任务 observer。E 的 checkpoint 66103713 bytes 留在原节点，
  SHA-256 `95a86790549721e66734ad5261407d8de728fb840f92d12e17d5c9ceddafacb7`；原根
  `/home/wu/hmasd-worktrees/gcea-b01-9316b175f/runs/goal_conditioned_entity_aggregation/b01_e_s922611`。
  本问题带入可复查的 runner 原始输出：`runs/goal_conditioned_entity_aggregation/b01_e_s922611/`，
  E summary SHA-256 `df3cad5ec44e331a08e92a60d002d3f61608a0e3b9b7ab30e2372bcd09a433df`。
  Root 对齐三臂 32 个同世界、500 步、原生 reward/return 恒等式，核对每臂 360k 训练、45 次更新、五参数组移动、评价零更新及完整 summary 有限性。
  O/P/E 的 J 为 .509136961/.159860890/.183015754；E−O=−.326121207（32/32 不利），E−P=+.023154864（20 正/12 负）。
  训练主体耗时 O/P/E 为 89.920405/109.742908/91.585929 min。三臂仍各只有一个训练实例；
  这约束已测聚合包，没有证明整个表示类别无效。原 DM 的方向级最终解释尚未发布，Root 的证据恢复不声称该 DM 已重新加载或完成工作。
  合同见 `candidates/goal_conditioned_entity_aggregation/NOTES.md` 的 B01 prospective、P complete、E accepted。

### Concrete next investment and alternatives

Root 当前优先候选是**普通学习对实际服务条件的适应**，从已完成的负载诊断切换到真实训练：
同一个普通 SET、同源有界动作、同信息与更新节律，两个新实例分别在 N6/c10 与 N8/c10 训练，
每臂 360k team steps；共同初始权重尽可能精确对齐，使用新世界，最终分别测试 N8（主要）与 N6（专门化代价）。
两个训练条件各一个实例，共 2 fits / 720k train / 64k final eval（2 策略 × 2 N × 32 世界 × 500 步）。
不复用旧 SET 训练结果充当新的对照，也不靠选择旧世界、早停点、常数人数值或去熵获得收益。

预期可证伪链：直接 N8 训练若有用，应改善实际 N8 资格/服务与完整 J；只有资格指标改善却无原生收益，
即未兑现用途。若 N8 改善而 N6 下降，应读为专门化得失；不是泛化已解决。N8 训练产生更多 agent rows，
原生 learner scalar 为 reward/N，且联合物理任务不同；这些要显式计量，本比较是实际训练条件的用途，
不把它冒充纯暴露机制或纯 N 因果效应。原 count 源码 `9fd88aa9f9e42d0855e367136751d37eb1648e07` 的 `experiments/candidates/agent_count_generalization/configuration.py`、`runner.py` 已有 train_n 参数和按实际 N 构造环境/学习批量；
但需要新的 prospective entry、明确 source 和窄的 CLI/统计实现，不能把“有参数”当已验收执行。
新训练的节点耗时未知，完整成本还包括实现、检查、独立审查与结果阅读；没有用旧每-fit 分钟数承诺 N8 成本。

请在以下真正能改变决定的选择之间比较，而非机械遍历：
1. 上述直接 N8 vs N6 的普通学习实验；
2. 改为 N4/6/8 的训练混合对固定 N6（更直接问宽条件用途，但新增混合调度/曝光问题）；
3. S7 中服务与返航风险的直接学习改进，要求明确实际可实现改变、普通对照及区别于旧辅助头的预测；
4. 当前不新增训练，把下一笔学习留给已有 D/G/P 的结果之后，但需说明现在等待的具体科学信息价值。
可以提出更好的有界替代。无需新架构、全问题 headroom census、穷尽诊断或正面 pilot 门槛。

### Context, source precedence and requested answer

读本问题 `source_sha` 的 `docs/project/OPERATING_CONSTITUTION.md` §§1–5、7–8（当前 owner 委托、成本、完整证据）；
`.agents/skills/hmasd-scientific-tools/SKILL.md` 的 working explanation、Comparators、Statistics、Cost and exposure；
`.agents/skills/hmasd-portfolio-task/SKILL.md` 的 Steps/Boundaries；当前 RESEARCH 的背景主题 1–4、相关方向和暂停。
上面的 `candidates/...` 均相对于 `docs/research/`，`runs/...` 相对于仓库根。
读取明确点名的原始支持/反对结果来判断，不要求重建全部历史或跟随每条旧链接。
旧实验继续按其绑定 source/endpoint/seed 有限解释；本次规则修订不追溯改变它们。

返回：项目现有最可信的进展是什么、哪种停止是在损失科学连续性、下一笔学习的首选和最强替代；
用观察/解释/新假说分开叙述，给出可执行比较、差异预测、主要读数、必要训练/非训练成本及改变选择的证据。
特别检验 N8 直接训练是否购买了足够有用的判断；若不值，请给出当前更值得执行的具体选择，而非只有“此配方关闭”。
指出你实际读取的来源及未读取但对决定关键的缺口；可有 MATERIAL_DISSENT。

Constraints: no experiments, no edits outside the empty `### Answer` below.
Read the pinned question. Fetch the latest `docs/research/RESEARCH.md` on branch
`codex/project-management-sept23` for writing and use its actual blob SHA. Preserve all other bytes,
including tables, this question and `### Decision`; stop on overlapping edits. Return the actual
commit on success, or the full answer in chat if GitHub writing fails, not just a receipt or link.

### Answer

Saved from chat（完整原文）。同一请求 key 为
`hmasd:1d02db50b970b1bf7ca4cbc7f445f83366400164d02b8b429c672206821b3ee4`，
source `c13350a7ce9ddbcf0c55acacae03fa93a9e140fd`；collector 报 COMPLETE，
`deliver` 核验为 NOT_DELIVERED、无写入提交，与答复声明一致。
正文 SHA-256 `3831d54162f944c23aacc2c437aca1ea558696661db008cc6b716dd84ebe82ff`，9550 字符；
保存文件只多一个终止换行，文件 SHA-256 `677c40c95d16ec6c3748c5f0b204db88065ad841226b8af3747ef2a7acd08871`。
下方保留完整抽取文本，包括原有引用占位和数学换行；数值核验及不同意之处见 Decision。

~~~text
GitHub 的固定版本读取可用，但当前连接没有可用于修改该文件的写入动作。因此，本次没有修改仓库，也没有生成提交 SHA；未运行实验。

以下是应写入 codex/project-management-sept23 分支、docs/research/RESEARCH.md 指定问题下的完整 ### Answer。判断依据是题目锁定的版本，不以移动分支或聊天记忆替代。

Answer
一、核心建议：下一笔投入优先购买“目标训练条件的实际用途”，而不是再次证明 SET 会学习

首选：按题目提出的方向，开展两个全新普通 SET 实例的 N8/c10 对 N6/c10 训练条件比较，每臂 360k team steps。最强替代是 N4/6/8 混合训练对固定 N6，但只有当宽条件用途比 N8 目标条件用途更重要时，才应现在替换首选。

我支持直接 N8 比较，不是因为现有材料已经证明“未见 N 是主要原因”，也不是因为它能判定普通 flat 是否已经充分。恰恰相反，SET 在训练 N6 也落后，已经反对“问题只是没有见过 N8”的简单解释。这个比较值得购买的判断更窄：

在相同普通策略类、信息、动作约束与更新节律下，投入相同团队步预算，把训练放到目标服务条件中，能否相对原训练条件改善 N8 的实际资格、服务与完整原生 J？这种改善是否以 N6 的用途下降为代价？

B08 已经提供了“双方确实学到服务”的证据，因此新比较不应把参数移动、学会服务或某个代理指标上升重新包装成主要发现。它必须回答改变训练条件是否值得采用。题目给出的负载结果、训练 N6 上的反证，以及明确限定的训练条件比较，共同支持这个决策问题，但不保证结果会是正的。

hmasd-pro-question-scientific-m… +1

现有 D/G/P 比较应按已接受合同继续，不因本建议更改，也不另开重叠的辅助预测包。Claude FSD 的具体暂停与 G33 的冻结保持不变。Root/DM 应依现有委托作研究取舍，不把本次答复变成新一轮 owner 或 Pro 审批。

hmasd-pro-question-scientific-m… +1

二、项目最可信的进展：有界正证据仍成立，解释范围则被反证收窄

观察一：人数研究保住了真实的终点优势，也排除了几个过于简单的修复故事。
B03/B07 在共同有界执行下，未见 N 的 H6−SET 平均 J 差约为 +.112963 / +.115464；B08 显示双方都实际学到服务。这里最可信的是所测策略包及终点的有界优势，不是“技能机制已经被识别”。B04 的去熵收益未在 B05 重现，B06 的符号仍随训练策略对保留，B09 固定人数通道也没有统一服务改善，因此去熵、常数人数通道都不应成为默认修复。

hmasd-pro-question-scientific-m…

B10 则增加了一个值得保留、但必须连同反例一起保存的结果：保留开局联合标签、继续局部反馈与循环状态时，N4/6/8 的 R−O J 分别为 +.004172080、+.003888290、+.009196934，42/48 个世界 J 更高；然而 N8 仍有每步少服务 5.302、3.198 个用户的世界。初始标签在多数成员间相同，也限制了“学到了分工”的解释。**平均 J 改善与服务尾部损失可以同时为真。**这既不是技能训练无用的证明，也不是持续重分配普遍有害的证明。

观察二：负载研究把问题推进到了“已有路径与控制所产生的服务资格”，但没有给出学习必能恢复的保证。
B01 的五格固定策略包差均为正，但容量交互 D4=−.020377、D8=+.023481，统一边际预测没有成立。N8/c10 中，SET 的平均资格用户为 20.00175、资格内未服务为 .72350；H6 对应 29.654、.396875。资格量相差约 9.65，而双方资格内未服务量均不到 1：在这些固定路径上，把主要差距归为剩余容量截断并不符合读数。这里的资格表是固定策略行为产生的结果，不是物理最优界，也不能证明某个训练改动一定能找回这部分服务。

hmasd-pro-question-scientific-m…

观察三：S7 保留下来的科学问题是服务与返航风险的联合控制，不是原辅助配方的可重复收益。
S−D 的 J 差从第一块约 +.010786083 变为第二块 −.088809686；G−D 从 +.028241173 变为 −.090692284。G 的服务分量改善重现，但返航／约束成本改善没有重现。两个训练块本来就在相同最终世界 936001–936032 上评价，因此再做一次“换到共同世界”的 B06 式解释，不能解决这次反号。读数支持关闭当前 MSE 辅助配方，不支持关闭服务—风险联合学习问题。

观察四：聚合方向已有可解释的完整负证据，不能继续被旧 observer 的状态遮蔽。
题目中的 Root 对齐报告给出 O/P/E 的 J 为 .509136961/.159860890/.183015754；E−O=−.326121207，32/32 世界不利；E−P=+.023154864，20 正、12 负。我读取的 E 原始 summary 包含完成的训练与最终评价记录，与“E 仍需等待训练完成”不一致。P 的完成记录同样不是一个未训练的空结果。当前判断应是：**这两个具体聚合包没有兑现相对 O 的用途，E 相对 P 的小幅恢复远不足以消除相对 O 的损失。**但每臂只有一个训练实例，不能据此宣布整个表示类别无效。跨臂配对数值在此采用 Root 的对齐报告，不冒充本轮独立重算全部 O/P/E 数组。

hmasd-pro-question-scientific-m…

工作解释。 这些材料共同支持的项目进展，不是一条已经证实的统一机制，而是更清楚的决策边界：某些策略包存在有界终点优势；普通包确实能学到服务；服务收益可能被原生风险代价抵消；若干看似直接的机制修复没有形成统一改善。下一步不应主要继续审问旧固定策略“为什么没有自动变好”，而应选择一个能改变用途判断的真实学习干预。

新假说。 对普通 SET 而言，直接在 N8/c10 训练可能比在 N6/c10 训练更好地形成目标条件下的资格与服务行为，并把它们转化为完整 J。该假说尚未得到现有材料验证；它允许三类有意义的反证：服务没有改善、服务改善但 J 不改善、或 N8 改善却付出 N6 专门化代价。它不是“只要训练过 N8 就会恢复 H6 差距”的假说。

三、哪一种停止正在损失科学连续性

应区分配方停止、执行故障和研究责任中断。

关闭一个已经被反证削弱的配方是合理的。例如，S7 当前辅助配方不应自动获得第三个 seed、重新调权重或另一轮相同解释的资格；B04 的去熵结果也不应在反例后仍被当作默认答案。但配方关闭之后，DM 仍需要保留工作解释、识别尚值得回答的问题，并选择下一种能改变判断的投入。把每个负结果都落成“此配方关闭，等待下一指令”，才是在损失科学连续性。当前治理已经把这项方向责任委托给 Root/DM，而不是要求 owner 反复重选。

聚合 E 是另一类更具体的断裂：**实际进程状态、结果交付状态、研究解释状态不是同一个状态。**按题目记录，E 已于 2026-09-23 02:00:05 UTC 正常退出，Root 已只读收回 9 个原生文件；旧 observer 仍显示 running，不能把它提升为“还需要训练”的证据。delivery_unknown/FileNotFoundError 和已不存在的 cwd 也不足以识别究竟缺了哪个文件。这里损失的首先是已完成工作的交付与解释，不是少了一次 fit；重启训练会掩盖这个区别。与此同时，Root 恢复证据不等于原 DM 已重新加载或完成方向级解释。

hmasd-pro-question-scientific-m…

因此，管理上的承接应是：保留原始结果与故障记录，让已有 O/P/E 进入方向级解释；让已接受的 D/G/P 继续完成；把新增学习集中到一个新的用途问题。既不把全部未决机制排成诊断队列，也不让每次失败都把选题责任退回 owner。

四、首选比较的可执行规格，以及它真正能够识别什么

比较对象与预算

项目	T6：新普通 SET	T8：新普通 SET
训练条件	N6/c10	N8/c10
训练终点	360k team steps	360k team steps
策略与执行	同一普通 SET、同源有界动作、同信息与更新节律	同左
最终评价	N8 为主要用途；N6 测专门化代价	同左
初始状态	与另一臂尽可能逐张量一致	与另一臂尽可能逐张量一致

总增量为 2 fits / 720k train team steps / 64k final eval team steps。最终评价为两策略 × 两个 N × 32 世界 × 500 步，不将旧 SET 的训练结果当作新对照。

hmasd-pro-question-scientific-m…

实现上有一项具体问题，必须在 prospective 中写实。
在明确指定的原 count 代码版本 9fd88aa9f9e42d0855e367136751d37eb1648e07 中，run 已有 train_n，环境和学习批量也按实际 N 构造；但我读取的 CLI 尚未暴露相应 --train-n，reward_units 的记录仍含硬编码的训练 N6 描述。因此，“有 Python 参数”不能直接当成新比较已验收。需要的是窄范围的 CLI 接线、实际 N 与 reward/N 元数据修正，以及行数、形状、更新计数和评价零更新检查；不是借此重写整个 runner。

新 prospective 应记录实际执行的 source commit、两臂配置、训练与最终世界清单、端点和统计定义。共同初始化应核对参数张量或哈希，而不只声称 seed 相同；任何因形状而不能对齐的部分都应事前说明。使用预先固定的新世界，隔离训练与最终评价；同一个评价 N 内，两策略共享世界条件。不同 N 的物理任务不相同，不能因为 seed 名称相同就宣称环境因素被纯粹隔离。

这类检查判断的是实现是否兑现比较合同，不是要求先获得一个正面 pilot，才允许进行正式学习。

主要读数

对每个评价人数分别计算：

Δ
8
	​

=
J(T8,N8)−J(T6,N8)
	​

,Δ
6
	​

=
J(T8,N6)−J(T6,N6)
	​

.

其中 Δ
8
	​

 是主问题，Δ
6
	​

 是专门化代价。不能看到结果后才把两者重新加权成一个有利的总分。

完整原生 J 与其原生 return 恒等式是用途判断的主轴；同时读取资格用户、真实服务、资格内未服务，以及该环境原生收益和约束代价分量。资格量上升而原生 J 不升，不能报成功；平均值上升也不能省略服务受损的世界，B10 已说明这种尾部反例会改变解释。

hmasd-pro-question-scientific-m… +1

统计上，应保存每个世界的配对差、均值、分布、正负计数及不利尾部；区间若采用配对世界重采样，其含义是对这两个固定已训练策略的世界变化不确定性。32 个世界不是 32 个训练重复，agent rows 也不是独立训练实例。每个训练条件只有一个实例，即使初始化精确对齐，也不能由世界级区间推出该训练方法跨 seed 的稳健平均效应。这个限制不使首轮比较失去用途，但必须限制结论强度。

同样，本轮若没有在共同新最终世界上评价 H6，就不能把 T8−T6 改善说成“已经补齐 H6 差距”。本轮不必为了回答训练条件用途而增加新的 H6 fit。

成本与暴露不等价必须显式报告

按每个团队步产生实际 N 条 agent row 计算，T6 的 360k 团队步对应 2.16M agent rows，T8 对应 2.88M，后者多 33⅓%；两臂合计 5.04M。相同更新节律不等于相同数据暴露或相同优化负担，应同时报告更新次数、实际批量、样本行数和实际优化工作量。原生 learner scalar 为 reward/N，N 变化也改变联合物理任务。因而这是一项固定团队步预算下的实际训练条件比较，不是纯 N、纯暴露或纯奖励缩放的因果试验。不能为了“消除混杂”临时改奖励归一化，再仍以原问题名义解释。

hmasd-pro-question-scientific-m…

非训练成本包括 prospective、窄实现、检查、独立工程审查、运行记录、结果取回与完整阅读。新 N8 的节点耗时未知；旧 O/P/E 的每-fit 分钟数不能用来承诺它的成本。这里可以确定的是拟议步数与暴露，不是尚未测得的时长。

hmasd-pro-question-scientific-m… +1

五、差异预测与改变选择的证据

下表不是预先承诺串行执行若干下一批，而是说明首轮结果怎样改变研究选择。

主要结果	应作的判断与下一种有价值选择
N8 的实际服务与 J 均有实质改善，N6 无明显用途损失	支持目标条件训练在本预算和这对实例中的实际用途。先保留这个简单有效选择；后续投入用于确实重要的稳健性或宽条件问题，而非宣称泛化已经解决。
N8 的服务与 J 改善，但 N6 明显下降	支持专门化得失。此时混合训练的价值明显上升，因为下一问题变成能否保住目标收益而减少条件间损失。
资格或服务改善，但完整 J 未改善，或不利尾部变差	未兑现用途。应根据已经观测到的原生代价解释失败；不能靠服务代理指标宣布成功。若决定转向服务—风险联合控制，应针对该问题提出直接学习改变，而不是自动复活旧 MSE 辅助头。
实现有效、实际完成学习，但 N8 无有用优势或更差	降低“仅改变目标训练条件，在这个预算下就值得采用”的优先级。它不证明普通学习已穷尽，也不自动支持混合训练；下一笔投入应与已完成的 D/G/P 等证据重新比较，而非默认重复 seed、加长训练或遍历机制。

实现未兑现合同，例如实际 N、奖励单位记录或学习批量错误，应判为执行有效性问题，不能把它计入训练假说的阴性证据。

“实质改善”不能被偷换成任意微小的正均值。应同时呈现 J 的幅度、服务量级、不利世界和成本。材料没有给出可以跨这些任务直接沿用的通用最小有效 J 阈值，因此不宜虚构一个数字门槛；但也不能事后只挑一个变好的指标。Root 可在既有委托下依据完整读数决定采用与否，无需新增 owner 确认。

六、真正可能替换首选的选择

最强替代：N4/6/8 混合训练对固定 N6。

它更直接购买“同一个普通策略在宽条件下是否更有用”的判断。如果项目的下一用途本来就是覆盖 N4、N6、N8，而不是先改善 N8，那么我会把它提到首位，而不是因为直接 N8 比较实现较窄就坚持后者。

但混合训练不是把一个参数换成三个值。它必须预先明确调度单位、条件分配、episode 边界与暴露统计。若在 360k 团队步中按三个 N 等额分配，则 N8 暴露约为 120k 团队步，而非直接 N8 臂的 360k；这正是用途差异的一部分，不应被隐藏。若要评价所声称的 N4/6/8 宽条件用途，两策略在三个 N 上各评价 32×500 步，则是 2 fits / 720k train / 96k final eval，不是沿用原方案的 64k。上述预算为本答复按拟议比较结构计算。题目也明确指出混合方案会新增调度与曝光问题。

hmasd-pro-question-scientific-m…

目前我仍把直接 N8 训练排在前面：它以更窄的实现改变回答目标条件适应是否值得，且不需要同时解释混合调度。真正改变排序的证据是宽条件用途成为首要目标，或直接训练显现明确专门化代价；不是单纯因为第一轮阴性就自动换成混合。

S7 的直接服务—风险学习：问题值得保留，但当前不是最成熟的新增比较。

一个区别于旧辅助头的具体候选，是在普通策略学习中，将训练时已有的原生返航／约束成本以预先固定的权重直接纳入 actor 更新的惩罚重加权；普通对照保持原有原生 RL 更新，其余信息、动作边界与预算一致。最终仍用原生完整 J 评价，而不是用重加权后的训练分数证明成功。

其差异预测应是：相对普通对照，在不过度牺牲服务的情况下减少返航／约束代价，从而改善完整 J；不是辅助预测误差下降。必须承认这是训练目标干预，而非纯粹增加一个诊断读数。S7 的两块结果为这个问题提供了动机，但没有验证这个新改动。

我没有读到该直接改动的已验收实现、已确定权重尺度或完整成本，也不能把结果日志中存在一个成本字段等同于训练时已具备正确接线。因此，它是一个明确的候选方向，不是本次已经具备完整执行合同的现成包。若后续证据把服务收益被原生风险抵消确认为最重要的用途障碍，它会比重复旧辅助头更值得投入；目前仍不如 N8/N6 比较聚焦。

等待 D/G/P：有具体信息价值，但不应成为默认停止。

D/G/P 分别能够提供普通辅助优化相对 D 的用途、成对结构相对普通辅助 G 的增量，以及 P 相对 D 的总用途。这个分解确实可能改变后续是否值得继续投入结构学习；已有完整建议与工程验收，应保护它完成，而不是再开一个类似的辅助包。

但它不直接回答 N8 对 N6 的训练条件问题，所以“它还没结束”本身不足以推出所有新增学习都必须等待。等待只有在两种情况下具有明确价值：共享节点或审查注意力确实构成瓶颈，会损害现有比较；或者其即将获得的结构增量证据足以改变新增投入的排序。目前资料没有证明这样的资源瓶颈已经存在，不能把假定的瓶颈写成事实。题目中的 D 已到 240k、G/P 未开始，是固定读取时点的状态，不是本答复对实时进度的确认。

hmasd-pro-question-scientific-m…

MATERIAL_DISSENT： 我赞同 Root 的 N8/N6 优先候选，但不同意把它解释为检验“差距主要源自未见 N”，也不同意阴性后转而宣称普通 flat 已充分。若项目的下一目标实际上是宽条件用途，而非 N8 的目标用途，我会直接改选混合训练，不要求先完成 N8 单条件比较才能获得资格。

七、实际读取范围与仍然存在的信息缺口

本次主体证据采用固定版本 c13350a7ce9ddbcf0c55acacae03fa93a9e140fd；原 count 执行代码采用题目另行指定的 9fd88aa9f9e42d0855e367136751d37eb1648e07。二者没有混用。

实际读取范围如下，路径分组也限定了本答复的证据边界：

治理、方法与项目背景。 已读 docs/project/OPERATING_CONSTITUTION.md 要求的 §§1–5、7–8，.agents/skills/hmasd-scientific-tools/SKILL.md 的工作解释、比较、统计、成本与暴露要求，.agents/skills/hmasd-portfolio-task/SKILL.md 的 Steps/Boundaries，以及固定版本 RESEARCH.md 的背景主题 1–4、相关方向与暂停。它们支持当前委托和方法边界，不追溯改写旧实验合同。

人数与负载。 已读 agent_count_generalization/NOTES.md 的 B07、B08、B10 完成条目，以及 runs/agent_count_generalization/s1_initial_policy_b08/summary.json、s1_initial_assignment_b10/summary.json 中用于判断的原始字段、数组和计数。已读 load_critical_member_generalization/NOTES.md 的 B01 完成条目、资格表与 working update，以及 runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/summary.json。B04–B06、B09 的历史判断采用本题固定记录及相关 NOTES，不声称独立重算了全部历史实验。

S7 与互补技能。 已读 S7 的 B03 prospective comparison 和 “B03 second common replay accepted and current recipe closed”，并读取六个原始 summary：b03_d_912211_a02、b03_s_912211_a01、b03_g_912211_a01、b03_d_912347_a01、b03_s_912347_a01、b03_g_912347_a01。核对用于判断的原生指标、训练／评价计数及最终世界信息；没有将大文件的局部读取描述为逐字节审计。互补技能方向已读 complete advice/adoption、B01 learning comparison 与 implementation acceptance，不把工程验收当成性能正证据。

聚合与执行代码。 已读聚合 B01 prospective、P complete、E accepted，以及恢复的 runs/goal_conditioned_entity_aggregation/b01_e_s922611/summary.json 中有关训练完成、最终评价、原生读数与计数的部分。O/P 和跨臂配对结论采用 NOTES 与本题 Root 对齐报告；没有独立读取并重算全部 O/P 原始逐世界数组。另已读指定旧 count revision 的 configuration.py 与 runner.py，因此上文 CLI 和元数据问题是基于实际代码读取，而非根据题目一句“有参数”作推断。

仍需明确的缺口有四类。第一，固定截面之后的 D/G/P 结果未知，不能提前使用其正负结论。第二，我没有访问原节点重新校验 E checkpoint，也没有独立复算 Root 所述九个文件的 SHA-256；这部分恢复与哈希事实归属于题目中的 Root 报告。第三，新 N8 比较的 CLI／统计改动尚未实施或验收，实际节点耗时未知。第四，每条件一个新训练实例只能提供受限的用途证据，不能填补训练随机性层面的重复证据；S7 新直接学习候选也尚无已验收实现。

这些缺口不妨碍现在选择一个有界的下一学习问题，但会限制将来能够声称的结论。最终建议是：把下一笔新增学习优先用于普通 SET 的 N8/N6 新训练比较；把混合训练保留为宽条件用途的最强替代；让现有 D/G/P 按原合同完成，并让已经恢复的 O/P/E 结果真正进入方向判断。关闭失败配方，不关闭科学问题；保留所有反证，也保留 Root/DM 继续选择和推进的责任。
~~~

### Decision

2026-09-23，Root 依 owner 的科学项目管理委托作出决定，按后续“三个 DM + 项目管理者”的约束执行。
已完整阅读本次 9550 字符答复，并核对会改变选择的原始数据与代码；Pro 是建议来源，以下为 Root 的采纳判断。

1. **采纳 DM1 的直接训练条件比较。** 首笔新增学习选两个全新普通 SET，分别 N6/c10、N8/c10，各 360k team steps；
   最终 N8 为主用途、N6 为专门化代价，2 fits / 720k train / 64k final eval。研究的是给定团队步预算下改变训练条件
   的实际用途，不是证明“差距主要来自未见 N”，也不重复购买 B08 已有的“SET 会学习”。单训练实例保持探索性质。
   不增加 H6 fit；没有共同新世界 H6 评价时，不声称缩小或补齐 H6 差距。混合训练仍是宽条件用途的最强替代，
   只有问题优先级或专门化证据使其更有信息价值时再选，不是阴性后的自动下一格。
2. **采纳实现与暴露方面的实质批评。** Root 复核指定 `9fd88aa9f9e42d0855e367136751d37eb1648e07`：
   `run_fit` 使用 `spec.train_n` 构造环境、动作形状与 bootstrap；CLI 没有 `--train-n`，reward_units 写死 train_N=6，
   CLI 还限定旧六-fit seed 集。新 prospective 的入口、实际 N 元数据、初始化张量一致性、样本行数、更新计数和零更新评价
   均须由 DM 兑现；不追溯修改旧六-fit 合同。T6/T8 分别有 2.16M/2.88M agent rows，原生 scalar 为 reward/N，
   两者不是等曝光或纯 N 因果试验。检查通过后无需一个正面 pilot 才能实施。
3. **保留 DM2 的已接受 D/G/P。** 题目发送后 D 已完整发布，G 已准入；采用当前索引的较新事实，
   不把 Pro 固定截面里的 D=240k 当作实时状态。不改三臂、终点或事前读法；P−G、G−D、P−D 分别回答结构增量、
   普通辅助和总用途。它的完整结果可以改变后续投资排序，但不是暂停 DM1 或 DM3 独立准备的理由。
4. **将 DM3 的准备聚焦于直接服务—风险学习。** 采纳 Pro 给出的可批评候选：普通原生更新，对比在 actor 训练目标中
   以预定系数加强真实返航/约束成本惩罚；最终仍以原生完整 J 及服务、电量低尾评价。这会改变训练目标，不能称为
   只改善同目标 critic，也不等于旧辅助头复活。前版分项 critic 留作有理由时可选的替代，不同时启动两包。
   当前尚无已定权重尺度或验收接线，DM 先依据真实 reward/learner 路径和已有开发证据定稿单一比较；
   初步规模为 2 新 fits、每臂 180k，最终配置与评价暴露在新 prospective 中固定，不能由此承诺性能或节点分钟数。
5. **纠正答复中的 S7 数值，不采纳错误幅度。** Root 从六个 `summary.json` 的
   `final_evaluation.aggregate.primary_native_J_mean` 重算：S−D 为 **+24.585406661 / −16.825601491**，
   G−D 为 **+117.896433768 / −24.945921167**。全部 final 世界为 936001–936032，每回合 1500 步；
   对应每步差分别为 **+.016390271 / −.011217068**、**+.078597623 / −.016630614**。
   答复的 +.010786083/−.088809686 和 +.028241173/−.090692284 不对应这些原始最终指标，也不是单一单位换算，
   因此不写入项目事实。G 的 QoS 每步差 **+.040290063 / +.054933804**，返航约束成本差
   **−.019338089 / +.035816853**；服务改善重现、成本改善未重现的定性判断仍被原数据支持。
   完整聊天原文保持不改，不能把建议与已核实证据混为一体。
6. **将聚合 O/P/E 完整证据纳入当前背景，结束这两个聚合配方的当前投入。** O/P/E 原生 J 为
   .509136961/.159860890/.183015754；E−O 在 32/32 世界为负，E−P 的小幅恢复未兑现相对 O 的用途。
   此方向保留为 reserve，不占第四条持续研究线；现有 lead 与原 DM 最终 notebook 补录责任保留，不声称其已重新加载。
   保留此前恢复的原生文件、哈希与句柄；没有重启 E 或替换原负责人。
7. **落实可接续的路径与诚实状态。** 原 DM3 task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e` 的地址仍有效，native 状态为 notLoaded。
   Root 核对其已发表分支 `fefc5ca8d6704845d3c18c7ed5039fe2af0a202d`、完整 B03 收尾及全部 terminal observation，
   在原路径 `/home/fires/.codex/worktrees/d319/hmasd-wsl` 恢复干净 checkout，保留原 branch/task；没有发消息、恢复工作进程
   或改动其他任务的观察器。发布计划并不等于 DM1/DM3 已开始新训练；接续时按当前 main 的授权与背景推进。

判断更新：已测 H6 包的有界优势保留；纯未见 N、统一容量边际、降低预测误差就提高控制收益等解释受到反证。
新的直接 N8 学习与服务—风险干预仍是假说。失败后根据实际改变的判断重新比较继续、简化、转向或停止的价值，
保持一个明确比较；不自动续 seed、不更换终点寻找正数，也不因旧配方结束就把选题退回 owner。
没有新训练由本次管理工作启动，方向级实施与科学验收仍由原 DM 负责。

## Retirement and history

按 [constitution §4](../../../project/OPERATING_CONSTITUTION.md#4-three-record-types-and-one-repository-table)
维护本页：更新现状时替换旧 standing；项目评审完成或计划被替代时，提炼仍有效的决定与证据入口，
在同次发布中将过时过程退役至 `archive/<YYYY-MM-DD>/RESEARCH.md`。同日再次归档用新后缀，历史文件不覆盖。
日期是退役定位，不是有效期；仍有效的决定、暂停、lead、冻结绑定与未完成操作留在当前页。
归档不改变方向状态或恢复研究；方向 NOTES 保持原职责，共享认识在本页按主题修订。

全项目历史快照：[2026-09-21 完整退役快照](../2026-09-21/RESEARCH.md)，包括六次已完成 Portfolio、旧计划、
第三方材料和历史路由，来源提交 `49029b96e02f6a8d08717849a366e4dca4a5477c`。更早快照按需从[日期目录](..)查找；
本页只保留仍需引用的入口，不追加每次维护的日志或完整归档目录。

以下兼容既有引用；链接中的旧排序和任务分配只代表当时判断，现行方案以上面的 Current research plan 为准。

<a id="portfolio-review-2026-09-21-closed-direction-research-value"></a>

[关闭方向的剩余研究价值](../2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-closed-direction-research-value)。

<a id="portfolio-review-2026-09-21-project-research-management"></a>

[全项目审阅及第三方报告核对](../2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)。

<a id="portfolio-review-2026-09-21-temporal-learning-and-uav-design"></a>

[可变周期与 UAV 设计](../2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-temporal-learning-and-uav-design)。

<a id="portfolio-review-2026-09-21-marl-concept-formation"></a>

[MARL 概念成型](../2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)。

<a id="claude-advisory-reconciliation-2026-09-21"></a>

[Claude 建议核对](../2026-09-21/RESEARCH.md#claude-advisory-reconciliation-2026-09-21)。

<a id="potential-research-directions-2026-09-21"></a>

[潜在问题全集与全部既有方向](../2026-09-21/RESEARCH.md#potential-research-directions-2026-09-21)。

<a id="portfolio-review-2026-09-21-information-first-three-dm-plan"></a>

[已被替代的三 DM 计划](../2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-information-first-three-dm-plan)。

<a id="fsd-planning-rationale-2026-09-21-new-advice-without-new-results"></a>

[FSD 建议与既有停止判断的核对](../2026-09-21/RESEARCH.md#fsd-planning-rationale-2026-09-21-new-advice-without-new-results)。

<a id="portfolio-review-2026-09-21-whole-project-evidence-led-research-plan"></a>

[全项目证据驱动计划的完整问答与决定](../2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-whole-project-evidence-led-research-plan)。

B08 选择前的咨询计划已退役至 [2026-09-23 选择前快照](RESEARCH-agent-count-b08-selected.md)；当前固定零拟合比较见上方人数方向。

B08 运行计划已退役至 [2026-09-23 完成前快照](RESEARCH-agent-count-b08-complete.md)；双方有用增益及当前人数通道问题见上方人数方向。
