# RL/MARL 的基础认识：从任务、策略到证据

这份共享知识摘要用于查阅 RL/MARL 概念、假设与推断边界，不是科研规范或实验卡。四个 Luna 子代理分别收集资料，原对话负责核查和综合；来源及访问限制保留在索引中。原讨论的局部选择另存于 [SESSION_CHOICES.md](SESSION_CHOICES.md)，不随通用知识阅读自动适用于其他方向。

## 1. RL 研究的是交互后果，不是组件名称

一个任务先规定环境怎样变化、决策者能够获得什么信息、可以采取什么动作，以及如何用 reward 表达后果。策略由可用信息产生动作，动作影响后续状态和数据；学习算法再利用数据改变策略。任务、策略、学习过程和评价结果是相互连接但不同的对象。

在一个 episodic discounted 设定中，可以写成：

\[
G_t=\sum_{k=0}^{T-t-1}\gamma^k R_{t+k+1},\qquad
J(\pi)=\mathbb E_{\rho_0,P,\pi}[G_0].
\]

这里的 reward、折扣、初始状态分布和终止规则共同决定目标。算法训练得到的是一个策略实例，实验看到的是对其表现的有限观测。网络更复杂、动作更平滑、技能更稳定，都不能单独替代任务 return 的改善。上述公式是一个明确的任务设定；平均回报等其他目标也存在，不能混用其结论。[RL 教材与版本记录](sources/READING_MAP.md#b1)

UAV 场景中的服务代理也不能混同。当前 Scenario 1 以连接覆盖、连接链路的归一化 SINR 和高度项形成 reward；连接分配由环境执行。Scenario 7 的当前 QoS 版本还受接入与回传共同限制，并有返航风险、电池事件和势函数项。较好的局部 SINR、较多连接或较好的势函数，未必提高端到端服务及完整目标。比较应保留相同版本的 native reward，同时报告其服务与风险分量。用户 traffic queue、独占预约或可变需求等机制，不能仅因应用名叫 UAV 基站就视为已经存在。[Scenario 1 reward](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/envs/pettingzoo/scenario1.py#L77)；[Scenario 7 QoS 与风险](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/envs/pettingzoo/relay/energy_aware.py#L773)

## 2. 部分可观测性要求处理信息，不要求每次都重新训练

环境状态描述影响未来的相关变量，observation 是 agent 实际得到的信息。一个 observation 没有包含充分状态时，仍可以定义条件期望价值；困难在于能否仅靠该 observation 作闭合的 Markov 递推。历史、信念状态或循环记忆可以帮助决策，RNN 本身并不保证恢复充分状态。

固定参数也可以产生动态行为：

\[
z_{t+1}=f_\theta(z_t,o_{t+1},a_t),\qquad
a_t\sim\pi_\theta(\cdot\mid o_t,z_t).
\]

即使 \(\theta\) 不变，观测和记忆变化也会改变动作分布。根据新信息调整动作、更新信念、重算计划、选择技能，以及利用数据更新参数，是不同过程。“部署期适应”需要说明是哪一种，不能自动解释为重新训练。[RL 专题](topic-notes/01_RL.md)；[MARL 教材](https://www.marl-book.com/)

用户移动、故障和恢复也可以是固定转移规律下的状态变化。只有相关转移规律、任务分布或其他机制发生未被当前状态解释的漂移时，才需要另外讨论环境非平稳性。这与训练时队友持续更新策略造成的学习问题不同。

已知奖励公式不等于已知联合物理后果、队友响应或未来状态。如果奖励为已知的 g(Y)，需要预测的可能是合法历史与行动条件下的 E[g(Y)]；当 g 非线性时，g(E[Y]) 一般不能替代它。普通后果模型仍是有意义的参照，是否足够要由反馈、支持范围与具体决策判断，不能由“奖励已知”直接排除学习问题。[B 的原生问题与项目级解释](../research/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)

联合物理后果相互耦合，也不自动意味着给定完整策略输入后的动作采样相关。中心方法能够直接查询自身当前策略时，比较必须保留这些查询权。B09 因此将未知混合概率明确放在外部控制者的信息契约中，比较普通联合计数与相同边缘分布的乘积。随后完成的三块原生结果中，联合模型的预测及已访问状态上的一步选择更好，但实际闭环回报差两负一正，正的总均值受一个大收益 episode 主导，未建立稳定闭环优势。它没有测量当前 HMASD 的内生共同学习，也没有证明更长规划能修复问题；不能把这个受控外部未知量写成现有 HMASD 的缺陷。[B09 完整结果与范围](https://github.com/CartmanFatass/My-paper-code/blob/69a55e71d9f1bca4e8cdd204adce256cd05a7676/docs/research/candidates/skill_teammate_drift_learning/NOTES.md)

B10 随后在同三个已曝光的学习结果上，用 12 个新评价世界比较始终向内、始终向外两条规则。联合模型相对两者的三个 base 均值都为正，但逐世界仍有负值；边缘乘积模型则与向外规则的完整轨迹相同。这削弱了两条固定方向规则能吸收联合模型部署价值的解释，保留了该受控任务的条件使用价值。它不是新的训练复制，也没有确立所有状态反馈规则都不足、学习的必要性或 HMASD 内生共同学习的收益；B09 的反面世界仍需保留。[B10 完整结果与范围](https://github.com/CartmanFatass/My-paper-code/blob/8f7a8ba197f9a9cf9ba60068b55b10febbcf3dd0/docs/research/candidates/skill_teammate_drift_learning/NOTES.md)

可识别性取决于具体未知量及可用反馈。C05 中当前周期独立重抽且未被观测的风险量，不能由过去周期识别；这不排除从合法本地历史估计共享转移参数。C 的后续源码核查发现，符合条件的相邻自身距离记录能给出一次 0/1 前进观测，形成共享前进概率的估计路径。该路径尚未拟合，也未验证有限数据能否保留决策收益。模型已知、参数可识别与有限数据足以支持有效决策，是三个不同判断。[C 的模型知识与反馈边界](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/NOTES.md#L3181-L3204)

## 3. MARL 增加的是联合行为和信息结构

完全合作意味着 agent 共享团队目标。Dec-POMDP 还明确每个 agent 的观测历史与分散决策结构；仅有共享 reward 不足以完成这个模型判断。多架 UAV 的算法是否能使用团队摘要，应由实际可用的信息接口判断。

CTDE 允许训练时的 critic 等组件利用额外信息，而执行策略使用部署时能够取得的信息。执行时已允许的团队摘要可以进入 actor。CTDE 这个名称既不会禁止这种输入，也不会保证协调、正确的个体信用、通信可靠性或故障恢复。[MARL 专题](topic-notes/02_MARL.md)；[Amato 等，2019，§2](https://lis.csail.mit.edu/pubs/amato-konidaris-jair19.pdf)

团队 return 把联合后果压成学习信号，因此既有跨时间的信用问题，也有 agent 之间的信用问题。共享参数、中心 critic、身份编码、通信和角色机制各自改变表达能力或学习过程；它们不是“已经学会合作”的证明。一个机制的价值最终仍要回到它帮助形成了什么联合行为，以及该行为在什么任务中改善了 return。

HMASD 的算法对象还包括团队技能、个体技能以及它们的共同学习。原论文的高层顺序分配已经让个体技能依赖团队技能和前序分配，低层则用团队/个体判别器提供技能发现信号；因此，“加入协调”或“区分技能标签”不能自动成为新的贡献。应分别检验技能行为是否不同、是否能组成有用的团队行为，以及有限训练是否学会选择这些组合。UAV 物理模型可以提供任务、先验或参照，其改进不自动等于改进了这些 MARL 学习机制。[HMASD，§3](https://proceedings.neurips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf)

原论文也将技能用途、技能数敏感性和子队协作灵活性列为限制。附录 F 在三个 SMAC 场景、各五次运行的 50 个个体技能中报告 12 个对任务有用；同文还报告表现好的 Overcooked 运行中各技能均有用。因此 24% 不是 HMASD 的普遍常数，更不是当前 UAV 的测量。全队一个 team skill 缺少显式的子队层次，也不等于联合个体技能不能表达任何分组行为。上述限制提供研究动机，仍需检验当前任务的实际学习瓶颈。[HMASD，附录 D、F、G](https://proceedings.neurips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf)

原论文主要验证稀疏奖励下的技能发现与协调，不能直接将这套作用解释移到稠密奖励 UAV，也不能由奖励稠密推断探索问题消失。配置的量级差异是真实的：论文所用任务最大联合标签笛卡尔积为 3m 的 `3 * 3^3 = 81`，当前六成员 S1 配置为 `6 * 6^6 = 279936`，相差 3456 倍。正文的 `2s_vs_1sc` 有两名受控成员，不应把敌方单位计入；其组合数为 `2 * 5^2 = 50`。这些是配置计数，非学习样本量比例。较小技能集合可以作为普通实现候选；奖励尺度、熵项和共同更新不同，不能由原始系数或组合数直接诊断停滞原因。[HMASD，§4、附录 E 表 3](https://proceedings.neurips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf)；[配置与计数核对](../research/RESEARCH.md#claude-advisory-reconciliation-2026-09-21)

技能的任务用途也可能依赖搭档组合。预测已执行组合的结果准确，不能直接证明更换伙伴技能后的用途；后者需要实际执行证据，同时不能要求每个技能与所有搭档都同样有效。搭档多样化和减少共同适应已有成熟先例：Other-Play 利用已知任务对称性，Fictitious Co-Play 训练对一组固定伙伴及其历史检查点的响应。它们研究陌生伙伴协作，不能直接当作同一 HMASD 团队内部技能重组的已验证方法；通用的伙伴随机化本身也不是新的机制。[Other-Play，§§3–5](https://proceedings.mlr.press/v119/hu20a/hu20a.pdf)；[Fictitious Co-Play，§2.1](https://proceedings.neurips.cc/paper/2021/file/797134c3e42371bb4979a462eb2f042a-Paper.pdf)

FSD B12 的标签计数回归不是“任务没有协作需求”的测量：收集来自三个固定 checkpoint 的状态依赖策略，模型含位置效应，只用一个同质性项检查特定非加性。其后 Pro 和 DM 已限定为原分布中的标签回报关联，不能排除成员身份、标签对或状态条件的交互；负的重复标签效应还可能对应去重协调。常量标签地图也不能限定时变选择的收益。用途探针可以帮助选题，但旧固定技能下缺乏正证据，不是新技能共同学习的性能上界。[B12、解释咨询及随后采用](https://github.com/CartmanFatass/My-paper-code/blob/00eac27c535ccffb66354f8bfac62acb504874ca/docs/research/candidates/flexible_skill_duration/NOTES.md)；[本次建议对照](../research/RESEARCH.md#claude-advisory-reconciliation-2026-09-21)

比较的信息条件需要沿实际 actor 输入核对。普通 own-observation MAPPO 可以回答一个有用的实际基线问题；如果另一方法在执行时还能访问团队摘要，这个比较就同时改变了信息和方法，不能独自归因为分层的收益。FSD 的当前 B01 已明确将 D1280−CF 定义为完整方法包的差异，而非 hierarchy headroom；后来的 CF_S 缩放修复也不能被忽略。应分别说明实用比较、匹配信息的比较和组件归因各回答什么。[FSD 的固定 B01 问题](https://github.com/CartmanFatass/My-paper-code/blob/267d1bcaebafa5f8f9049098d645e2f548b7c678/docs/research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md)；[B05 修复及后续解释](https://github.com/CartmanFatass/My-paper-code/blob/267d1bcaebafa5f8f9049098d645e2f548b7c678/docs/research/candidates/flexible_skill_duration/NOTES.md)

全局 coach 是否被允许取决于任务的信息条件，不能仅凭组件名称纳入或排除比较。COPA 的 coach 为部分观测的成员提供策略，论文也包含回合内成员加入；它是相关的队伍变化参照，但原来的离散动作、AQMIX 结构与当前 UAV 连续动作接口仍需匹配。其通信阈值是在计算新策略后决定是否发送，因此减少策略广播不能直接记作减少 coach 推理。[COPA 原文，§§3.2–3.4、4.1](https://proceedings.mlr.press/v139/liu21m/liu21m.pdf)

把两个学习方法放在同一份已采集历史上，可以检验其学习映射对数据的敏感性，却不会产生它们在原环境中各自行动后的反事实轨迹。B08 的六个续学比较复用三个块；R 在两套相同历史上都落后于 F，削弱了“仅修复采集就能恢复当前 R 优势”的解释。早期有利结果、奖励噪声与估计误差相互抵消的替代解释仍然保留。六个相关比较不是六个独立复现，也没有证明所有条件响应复用无效。[B08 同历史比较与反例](https://github.com/CartmanFatass/My-paper-code/blob/fe0e5719836f16cc5a44f02d80f53c95592250bd/docs/research/candidates/skill_teammate_drift_learning/NOTES.md)

## 4. 学习理论、表示能力和有限训练结果处在不同层面

即使模拟器的规则全部已知，有限资源下怎样学到好的联合策略仍然可以是 MARL 问题；不必先人为加入未知物理量才允许研究学习算法。已知模型的控制器是有意义的参照，其优势需连同数据、规划和执行成本解释。普通规划在一个固定问题中吸收了当前方法的收益，只约束该比较，不能推出技能学习、联合探索或学习稳定性都已没有价值。[RL 任务与学习对象](#1-rl-研究的是交互后果不是组件名称)；[项目中模型与数据成本的具体例子](#6-实证研究是在具体条件下缩小解释空间)

Bellman 关系、策略梯度恒等式以及带条件的收敛定理，解释某些更新为什么有依据。它们不能直接保证任意神经网络、近似 critic 和有限训练预算下得到好策略。“网络能够表示某行为”和“当前数据及优化能学到该行为”也是两回事。

合适的结构可以让有关行为更容易被表示、探索或学习；也可能限制表达、增加优化困难或放大估计误差。因此，对于可复用合作结构，应提出可检验的理由，而不是把“结构化”“分层”“可解释”本身当成有效性结论。[策略梯度原始论文](https://proceedings.neurips.cc/paper_files/paper/1999/hash/464d828b85b0bed98e80ade0a5c43b0f-Abstract.html)；[实现因素的经验研究](https://arxiv.org/abs/2005.12729)

由此也不能反向推出“相同信息的重新表示必然获得严格为零的收益”。信息是否相同、固定程序的动作是否相同，以及有限数据和优化下是否学到相同行为，需要分别判断。具体程序在指定输入上的动作与回报完全相同，可以构成局部相等证据；它不能自动推广为表示类等价。透明规则赢过当前 learner 同样是有效结果，但不是“只有不存在简短规则时学习才有价值”的定理。[项目审阅中的适用范围核对](../research/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)

reward 的数学目标和训练时的数值处理也应分开。固定任务条件下，正比例缩放给出 \(J'=cJ\)，\(c>0\)，保持固定策略排序；但有限优化得到的策略可能改变。裁剪、一般 shaping 或策略相关的累计常数则可能改变目标。具体边界见 [RL 专题](topic-notes/01_RL.md)。

扩大可选的技能持续时间，首先扩大的是时间策略类。在任务、信息与执行语义相同，且可变类确实能复制固定类时，只能推出最优值不降低，不能保证严格提高。令 \(J^*_{\mathcal P}=\sup_{\pi\in\mathcal P}J(\pi)\)，令 \(\bar J_{\mathcal P}(B)\) 为预算 B 下对训练随机性取平均的最终策略价值，并定义学习缺口 \(\epsilon_{\mathcal P}(B)=J^*_{\mathcal P}-\bar J_{\mathcal P}(B)\)，则有：

\[
\bar J_{\rm var}(B)-\bar J_{\rm fixed}(B)
=\bigl(J^*_{\rm var}-J^*_{\rm fixed}\bigr)
-\bigl(\epsilon_{\rm var}(B)-\epsilon_{\rm fixed}(B)\bigr).
\]

这是按定义得到的分解，不是可直接估计的误差界；未知最优值也不是实验启动前必须测出的量。探索、统计估计、优化和共同学习都可能影响缺口，目前没有把它们独立识别出来。比较可以直接看声明资源下的学习曲线与终点表现，计入预训练和选择固定周期的成本。更多时间选择可能增加学习负担，也可能通过连续探索改善学习，方向不由动作数决定。动作保持的控制频率研究和持续探索研究提供了这种权衡的单智能体先例，尚未验证当前多智能体闭环技能的收益。[Metelli 等，2020](https://proceedings.mlr.press/v119/metelli20a/metelli20a.pdf)；[Dabney 等，2021](https://openreview.net/forum?id=ONBPHFZ7zG4)；[本次问题及推导范围](../research/RESEARCH.md#portfolio-review-2026-09-21-temporal-learning-and-uav-design)

## 5. 技能和异步性是组织决策的方式，其收益需要证据

Option 由启动条件、内部行为和终止机制定义，这些部分可以固定、隐含或通过学习得到。固定动作保持也可以构成固定 option；反过来，单有一个 latent 向量或角色标签，还不能判断其完整执行语义。要看该变量如何影响动作、持续时间和终止。

在适当的 Markov 条件下，option 边界可用 Semi-MDP 描述。持续 \(\tau\) 个 primitive steps 的片段累积 reward，并以 \(\gamma^\tau\) 折扣后续价值。异步多智能体中，不同 agent 的边界可以不同；学习方法需要表达谁正在继续、谁重新选择以及哪些 reward 属于哪些时间段。某篇论文采用的 padding、轨迹组织或 advantage 方法不是所有异步算法的必选项。[层次与异步专题](topic-notes/03_HIERARCHY_ASYNC.md)；[宏动作原始论文](https://proceedings.mlr.press/v100/xiao20a.html)

时间抽象可以组织较长时域的探索和行为，也可能使响应迟缓或承诺于不合适的技能。更少切换本身不是收益；它必须通过任务后果体现价值。

个体驻留、全队重选事件间隔和有效合作的持续时间需要区分。若各成员在共同离散检查点以独立概率 \(p\) 重选，首次有人重选的平均检查数为 \(1/[1-(1-p)^n]\)，而不是无条件等于个体均值除以成员数。\(p=.4,n=6\) 时个体均值 2.5、首次有人重选均值约 1.049。即使发生重选，也可能仍选同一标签或通过局部接替保持合作；连续时间合流的 \(k/n\) 事件率推理不自动描述这些任务后果。承诺上下文可帮助学习，但不自行延长合作或保证异步收益。[假设、计算与采用边界](../research/RESEARCH.md#claude-advisory-reconciliation-2026-09-21)

在多智能体中，个体持续时间还决定哪些成员能在此刻重新选择，哪些成员继续执行已有承诺；联合探索与信用学习需要面对这种不同步的行动机会。一个全队共享的可变时钟可以研究时间抽象，但不能单独证明解决了个体异步协调。联合动作组合数也不能直接当作学习样本复杂度定理。已有宏动作 MARL 和异步 actor-critic 方法是相关参照；新方法需要说明相对它们以及现有 HMASD 已有机制改进了什么。[宏动作 MARL](https://proceedings.mlr.press/v100/xiao20a.html)；[异步 actor-critic](https://arxiv.org/abs/2209.10113)；[ACAC](https://proceedings.mlr.press/v267/jung25a.html)

联合时序影响回报，不意味着必须增加跨成员的随机采样相关性。在共同且充分的输入下，一个确定性的联合技能—时长映射可以分解成各成员的确定性输出；共同状态和已有 team latent 也能产生边缘相关。因而“独立时长 head”不能被先验断言无法等待、接力或错峰。若一次仅一名成员有权更新，事件内自回归采样也没有额外的跨成员随机关系可表达；两类策略仍需处理其他成员正在执行的承诺。普通自回归策略是学习参照，其更好的有限训练结果仍不唯一识别相关探索的原因。[本次概念审查的推理与范围](../research/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)

队友 option 条件化与学习终止也并非空白：Dynamic Termination 已用队友最近广播的 option 估值，并学习带终止价格的终止动作；它的延迟通信和价格是该论文的设定，不能移植为当前 UAV 已有条件。顺序联合决策和优势分解亦已有 MAT 等方法。给高层增加时长、承诺输入、顺序解码或正确的异步结算，可以构成值得评价的实现改进，但组件组合本身没有建立新颖性或效果。[Dynamic Termination，§4](https://arxiv.org/pdf/1910.09508)；[MAT，§§2.2、4](https://arxiv.org/pdf/2205.14953)

反事实 baseline 还须服从实际采样结构。COMA 的分散动作乘积条件下，可以固定其他成员动作并边缘化自身动作；对自回归策略，后采样动作可能已受当前动作影响，直接照搬不保证 baseline 的 score 项期望为零。合法前缀 baseline 可依赖决策前上下文与已采样前缀；共享参数不破坏这一条件恒等式，但不自动带来独立参数更新或联合信赖域保证。前缀条件优势是依赖顺序的学习信号，不是成员固有的因果贡献。此处只说明方法边界，没有诊断当前实现存在该错误。[COMA，§4、附录 A](https://arxiv.org/pdf/1705.08926)；[本次解析反例与核对](../research/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)

技能执行、重新选择相同标签和学习片段边界也未必相同。当前 FSD/D2 的低层策略每个 primitive step 接收观测并更新循环隐藏状态；高层重新选择即使得到同一标签，也会关闭并新开 credit segment，重置 age 和片段统计，而低层记忆继续。协调器此时重新编码当前输入，未被采样的 agent/team token 保持；team renewal 会触发所有 agent renewal。因此，时长比较需要说明团队时钟、个体时钟、实际标签变化及片段结算的关系，不能用低层保持速度或隐藏态重置替代这些语义。这是当前实现事实，没有诊断出折扣或 credit 的错误，也不要求固定类模拟可变类的全部额外行为。[原生 segment 与选择实现](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/hmasd/agent.py#L2286)；[低层逐步反馈](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/hmasd/agent.py#L3045)

同一实现中，held skills 与采样 mask 进入部分技能解码，但高层 value heads 只使用当前 state/joint observations；age 的可选特征进入判别器，不进入这些 value heads。这给出了异步 continuation context 是否影响有限学习的具体问题，没有直接证明当前 baseline 错误、价值误差大或加入输入就有收益。固定 primitive 步数和相同更新安排下，每步仍写入低层与判别器 buffer，改变 k 不必然改变原始样本行数；它主要改变技能驻留、标签分布和高层片段数。高层 D2 片段累积环境 reward，低层另有技能发现的 intrinsic reward，二者不能混作同一个目标。[value 与 partial assignment](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/hmasd/networks.py#L756)；[逐步 buffer 写入](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/hmasd/agent.py#L3886)

上述相同更新安排是实质条件：当前低层循环序列采样将 `chunk_length` 设为 `config.k`。因此改变全局固定 k 还可能改变训练序列长度；相同 primitive 样本行数不等于相同优化过程。D2 的部分分配还会在决策子集上调用归一化：若启用且处于训练模式，该路径更新 running statistics，边界变化可能改变其采样权重；这不是统计量唯一的更新路径。应按实际生效的 sampler 和 normalizer 区分执行周期、训练序列、统计更新和优化量，而非把它们都称作探索成本。这里没有测得新增效应或诊断出现有失败。[低层序列采样](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/hmasd/agent.py#L6300)；[D2 决策子集](https://github.com/CartmanFatass/My-paper-code/blob/e9f77d1e03ee9d3bdb86187ecd90224a1822f74b/hmasd/agent.py#L2639)

技能的决策频率与 primitive-time 占用频率也不同。在固定策略下的平稳驻留过程、有限平均时长及无选择性删失等条件下，实际驻留时间 \(\tau\) 给出 \(p_t(z)=p_d(z)\mathbb E[\tau\mid z]/\mathbb E[\tau]\)。若判别器准确拟合时间采样的后验，则 \(\mathbb E_t[\log p_t(z\mid x)-\log p_d(z)]=I_t(Z;X)+D_{\rm KL}(p_t\Vert p_d)\)。在 X 不携带技能信息的例子中，两种相同行为若决策概率各半、平均时长为 1 和 9，便可出现非零 KL 而无状态互信息。因此较好的判别分数未必代表更有用的技能。该推导不是原生 HMASD 目标的错误诊断；其 reward 与 entropy 路径需要分别核对，异步联合事件分布也不能直接用独立更新公式代替。较长有效服务的真实收益可以保留，统一占用率不是通用前提。[推导条件及原生差异](../research/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)

不同持续时间也不必作为互不相关的选项从头学习。TempoRL 利用相同动作的已执行中间转移学习多个保持长度；Timing-as-an-Action 利用共同的一步转移模型联系不同延迟。后者假设中间状态与奖励不可见并有交互成本，与当前 FSD 的逐步观测不同。把共同模型迁移到闭环技能时，还要处理隐藏状态、策略版本和队友行为；持续学习的技能不能无条件视作固定 Markov 转移矩阵。合法的已执行前缀提供反馈，但没有提供提前换技能后的未执行后续轨迹。共享结构是候选学习办法，既不是本项目已实现的增益，也不是新颖性证明。[TempoRL，§3.2](https://proceedings.mlr.press/v139/biedenkapp21a/biedenkapp21a.pdf)；[Timing-as-an-Action，§§2、4](https://proceedings.mlr.press/v238/zhou24c/zhou24c.pdf)

重新计算策略、切换目标、保持速度、保持目标并继续反馈导航，是不同操作。只有在信息与资源相同、逐步策略类能够模拟保持行为时，才可由策略类包含关系说其最优回报不低于固定时钟；这不保证某个逐步 greedy 或有限训练策略更好。service-restoration 的当前四个 preset 均为 motion_weight=0；底层运动项衡量实际速度的平方，而非重新决策次数。脚本时机曲线可以筛查这套控制器的响应机制，不能凭平坦曲线否定全部技能时长，也不能把运动成本当成重算费用。[项目级源码核对及探针范围](../research/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)

汇总队友的结果证据可以改善共同隐状态的估计，但要说明证据能否合法取得、条件相关性及汇总成本。此次第三方 CUSUM 原型在已知奖励似然、共同隐状态及无通信损失的设定内保留强信号收益；弱信号下的收益接近零，部分汇总比较为负。刷新在原型中还会直接揭示真实状态并牺牲一步奖励，因此它提供的是一个有条件的检测例子，没有验证未知模型或原生 UAV 的终止算法。被称为 oracle 的指定策略也需要证明最优性，才能把它与基线的差距称作上界。[追加原型的源码、数据与限制](../research/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)

静态用户和固定机群数也不等于决策状态不变：UAV 的位置、当前承诺和可用行动机会仍可随轨迹变化。“事件频率 × 等待时长 × 响应收益”只能解释预设的事件响应机制，不能因没有外生事件就把所有自适应终止价值设为零。Relay corridor 的 exact references 已展示其设定内的机会；E3 实际使用固定 c=.25、无触发器梯度的 heuristic，且事件召回率已有报告。该实现失利限制的是它的校准和完整学习包，不构成 trained KEEP/END 的一般否定，也不建立 UAV 收益。[E3 已有结果及边界](https://github.com/CartmanFatass/My-paper-code/blob/267d1bcaebafa5f8f9049098d645e2f548b7c678/docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md)；[E3 实现](https://github.com/CartmanFatass/My-paper-code/blob/267d1bcaebafa5f8f9049098d645e2f548b7c678/scripts/run_flexible_skill_duration_e3.py)

通信的信息价值也需要沿发送、到达、接收者行动与任务后果来解释。包到达时，接收者可能尚无受缓存影响的行动机会；只估到到达时刻或当前技能结束，可能漏掉消息第一次有用的后果。C06–C07 的 NEAR_COMMIT 将估值覆盖到第一个缓存敏感行动机会所在的完整承诺结束，或更早的整局终点，包括等待下一次任务边界的情形。它本身已经是多步方法；延长日历时域是否增加价值，需要相对这个有能力的近端参照检验。这里的终点来自固定 CrossingHost 的行动和奖励结构，不能直接成为所有任务的统一截断规则。[C06 终点修正及其适用条件](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/NOTES.md#L1926-L1943)

当承诺持续、排他地占用共享资源时，它可能改变队友下一次**合法行动的时刻**。资源释放时刻与队友的决策时钟不一定重合；失败的服务也可能继续占用资源。因此，协调可能表现为提前承诺、为后续任务保留机会，而不只是等待让位。在 VSP-03 的公开双任务模型中，一条末次可行时刻的提交规则，恢复了三个开发块中联合规划器相对孤立规划器平均增益的约 56.5%；剩余差值有正有负。这说明一个可行性修正能恢复部分观测增益，未隔离唯一因果机制，也未证明简单规则与完整规划等价，也未建立一般 MARL 或 UAV 的机制结论。[VSP-03 B10 的完整读法](https://github.com/CartmanFatass/My-paper-code/blob/16762710035b007287a72dc9c0f6f4c498ff339a/docs/research/candidates/vsp_03/NOTES.md)

## 6. 实证研究是在具体条件下缩小解释空间

一个结果首先说明某个任务、训练过程、策略实例和评价方式下发生了什么。多个评价 episode 主要反映同一策略执行时的变动，不能自动替代多个独立训练实例。学习曲线、指定训练终点的表现和从多个 checkpoint 中选出的最好表现回答不同问题，不能不加说明地互换。[实证方法专题](topic-notes/04_EMPIRICAL.md)

最小可检测效应是实验设计下的量，取决于独立单位数、方差、检验和目标 power，不是一个环境固定不变的“分辨率”。当前 FSD 历史配对训练 SD .07428 与 .10316，在特定正态配对模型、双侧 .05、80% power 和五个独立单位下，对应约 .125 与 .174 J 的设计尺度；小样本 SD 本身仍有不确定性。增加同一检查点的评估世界，能减少世界层的噪声，不能消除训练实例间的差异。冻结检查点的配对干预可以更便宜地回答部署选择问题，但不能替代重新训练方法的效果估计。已见世界上选出的最佳标签或检查点，也需要和新的测试世界分开。[第三方重算、Root 算术核对及限制](../research/RESEARCH.md#portfolio-review-2026-09-21-project-research-management)

端到端比较可以回答哪套完整方法在所给条件下更好；解释某个组件为什么有效，需要有针对性的控制或消融。探索信号可以推动下一步研究；跨任务泛化、稳定优势或机制归因则需要匹配的证据。这里没有从基础知识推出固定 seed 数、显著性阈值、阳性 toy 或理论证明的通用启动门槛。[Henderson 等，2018](https://ojs.aaai.org/index.php/AAAI/article/view/11694)；[Agarwal 等，2021](https://arxiv.org/abs/2108.13264)

负结果也可以排除解释、暴露实现问题或改变机制判断；具体投入选择属于当前问题的决策范围，不能由基础定义代替。

共享原始观测不等于共享模型先验，也不意味着取得这些数据没有成本。VSP-03 中，学习策略相对 readiness 规则的正收益仍然成立，但使用正确模型族的拟合规划器在新的固定确认批次中更好；这改变了该条件下应保留的方法，没有否定原来的正收益。该批次规划器的参数拟合很便宜，其数据却来自完整的神经策略训练；只计拟合时间不能据此称整个方法低成本。模型族、采集策略、数据量与执行计算需要分别说明，历史构造成本也不同于复用已有制品的成本。[VSP-03 B09 的比较条件与结果](../research/candidates/vsp_03/CLAIM_fitted_opportunity_b09.md)

这项数据依赖随后得到了实际检验：B11 每个模型仅从固定 R0 采集 512 局，三个新校准模型在新世界里相对 R0 的收益都为正，平均 +0.02813 J；相对三个预选的大数据规划器，平均差为 −0.000271 J。这支持该正确模型族内的独立构造办法，未证明等价、最小样本量或一般未知系统的低数据学习能力。采集局数减少 128 倍，也不是端到端速度提高 128 倍。[VSP-03 B11 原始结果](https://github.com/CartmanFatass/My-paper-code/tree/4780940a613c595a49fd19d94ad6d3f7ffb0dd9d/runs/vsp_03/opportunity_calibration_b11_22001_22003)

C07 的固定双智能体 CrossingHost 确认中，已知模型规划 NEAR_COMMIT 相对透明规则 ACTIVE_FIRST，在 1,280 个配对世界中平均多完成 0.07969 个任务，近似正态 95% 区间为 [0.05606, 0.10331]，通过预先声明的保留规则。各程序的包数和字节数相同，这一比较衡量等通信量下完整发送时机程序的收益。已知模型、更细的合法自身历史处理及额外计算都是获胜程序的资源，尚未隔离各组件的贡献，也未建立神经学习或 UAV 泛化收益。普通规划取得的这种有边界的正面结果，可以作为研究产出保留。[C07 完整结果与解释](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/NOTES.md#L2748-L2840)

稀疏的配对收益中，大量平局和很小的样本方差仍可能遗漏罕见尾部。C07 的 LONG 相对 NEAR 总共多完成 3 个任务；在声明的独立、等均值抽样条件下，使用预先固定的全局差值上界 14，得到单侧至少 97.5% 覆盖的期望增益上界 0.04345 个任务/世界，低于预设尺度 0.05。这个有限样本结论约束固定 LONG 程序，不能外推成零效应、NEAR 全局最优或所有长时域方法等价。用观察到的最大差值替代全局上界，会把未观察的尾部排除在保证之外；上述近似正态主结果与此次有限样本保证也分别解释，不构成联合覆盖保证。[C07 预先固定的统计读法](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/CLAIM_near_commit_c07.md#L37-L66)；[对应读数](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/NOTES.md#L2759-L2773)

计算成本需要联系任务目标解释。C07 中 NEAR 的批量面板用时约为 ACTIVE_FIRST 的 26.1 倍，这没有测得在线决策超时或能耗导致的任务损失，也不能直接推出不可部署。实际期限、能耗后果或明确选择的成本—回报目标，都能使计算开销成为可检验的问题；研究成本—回报关系并不必须先有外部硬期限。相对用时本身尚未给出这种目标，也不自动产生下一轮优化实验。[C 的资源条件评估](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/NOTES.md#L3206-L3215)

## 7. 当前研究选择放在这套认识的什么位置

原讨论已表达的选择、可否定的机制假设和未冻结实现分别保存在 [会话选择记录](SESSION_CHOICES.md)。该记录仅在当前任务明确采用其范围时适用，不是全局基线、排序或方向要求。

2026-09-21 的 C07 后续评估建议结束当前 C 投入并保留 NEAR，依据是当前选定的问题已得到有边界的答案，且尚未选定值得续投的新比较；没有测得所有后续方案成功概率低。可复用的区别是：技术可达、已有价值证据与当前投入选择各需理由。一次投入可以带着正面成果结束；新的具体假设、有限模型数据问题或成本—回报目标也可能支持后续研究，无须事先证明会成功。笼统的重新进入条件本身不构成持续投入的证据。这是一次有来源的研究判断，不是共享知识文档替各方向作投入决定。[C 的可达性与结束投入建议](https://github.com/CartmanFatass/My-paper-code/blob/a76339b5f13244daed94cabb06809fa8923f7f27/docs/research/candidates/skill_information_refresh/NOTES.md#L3130-L3278)

项目级复核同样区分“有可执行的新问题”和“已证明值得成功”。低精度或相互混合的原生结果，可以使一个类别仍然未决，同时使当前方案不值得继续投入；无需把负的观测抹去，也无需把它升级为类别失败。小模型能提供规则、反例、估计量或机制理解；通向原生任务所缺的信息、耦合和实施成本仍需明确承担。方向的当前排序、归档和执行归属只在 [研究索引的项目决定](../research/RESEARCH.md#portfolio-review-2026-09-21-project-research-management) 中记录，这份共享认识不产生新方向或自动重新启动实验。

阅读入口：[四个专题与来源索引](README.md)。本次访问范围、书籍版本差异及初稿纠错分别保存在 [检索记录](working/RETRIEVAL_COVERAGE.md) 和 [核查记录](working/REVIEW_NOTES.md)。
