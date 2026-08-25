1. Independent thesis

变量 N 与变量技能寿命 T_i 不应被视为两个需要分别安装模块的问题。它们是同一个状态对象的两类变化：一个匿名、动态的“活动成员—技能承诺集合”在事件时刻发生增、删、延续或替换。

我认为最强的统一架构是：

交换等变、事件溯源的半马尔可夫承诺编辑器
（exchangeable event-sourced semi-Markov commitment editor）

在基础时刻 t，高层状态不是固定长度 roster，也不是单独的 team code，而是

C
t
	​

={(x
i
	​

,h
i
	​

,z
i
	​

,τ
i
	​

,κ
i
	​

):i∈A
t
	​

},

其中：

A
t
	​

 是当前活动成员集合；

x
i
	​

 是可泛化的成员、局部关系和执行状态；

h
i
	​

 是幸存成员需要连续保留的 recurrent/process state；

z
i
	​

 是当前执行的个体技能；

τ
i
	​

 是该技能已经持续的真实时间；

κ
i
	​

 只是 collector 用来路由状态的不透明生命周期键，不能作为 policy 的身份或槽位输入。匿名性不等于 collector 无法知道哪段 hidden state 属于谁。

这个集合上的四种基本事件是：

JOIN,LEAVE,KEEP,SET(z).

JOIN 增加一个成员承诺，LEAVE 关闭一个成员承诺，KEEP 延长现有技能承诺，SET 关闭旧技能并打开新技能。没有发生真实决策事件时，不应伪造高层动作、log-prob 或 PPO 样本。这样，episode 内 roster 变化和每成员技能寿命变化都进入同一个事件 ledger，而不是分别维护“roster 模块”和“termination 模块”。

高层每次只处理事件前沿 F
t
	​

，即本次确实加入、离开或到达续期机会的成员。先用交换等变的 active-set 编码器读取 C
t
	​

；若此次编辑存在互斥、容量或互补约束，再只对 F
t
	​

 做自回归联合因子化：

π(E
t
	​

∣C
t
	​

)=
j=1
∏
∣F
t
	​

∣
	​

π(e
σ
j
	​

	​

∣C
t
	​

,e
σ
<j
	​

	​

).

这里的顺序 σ 必须是与语义身份无关、可精确重放的外生顺序；它可以被记录，但不能退化为永久槽位。若事件之间近似条件独立，则该分布自然退化为并行、分解式普通 MARL。

这一路线保留 HMASD 的个体技能瓶颈：低层仍主要执行 π
low
	​

(a
i
	​

∣o
i
	​

,z
i
	​

)。但它不把额外 team code 视为架构必需品。团队意图的功能由“当前活动技能集合 + 已应用的编辑前缀”承担：它直接控制后续技能分配，因而天然可行动。现有 R30 已经证明 working roster 而不是简单 token 计数可以作为后续自回归条件，并定义了精确的 KEEP/SET 联合概率；这部分应保留为功能，而不是保留固定全员检查外壳。

行为概率与信用必须由同一事件 ledger 拥有：

外生 JOIN/LEAVE 没有 actor log-prob；

只有真实的 policy-owned KEEP/SET/termination 事件进入 PPO ratio；

每个事件存储 old log-prob、应用前缀、动态 mask、开始与结束 roster、value snapshot 和真实持续时间 Δ
e
	​

；

回报按基础物理时间折扣：

R
e
	​

=
r=0
∑
Δ
e
	​

−1
	​

γ
r
r
t+r
	​

,bootstrap=γ
Δ
e
	​

V(s
t+Δ
e
	​

	​

);

lambda 按宏事件深度递推，而不是按没有决策的空白微步递推。

这正是 ACAC 最有价值的语义：真实微时间控制 γ，宏事件次数控制 λ，每成员只保留其有效事件历史。

计算上，首选实现不需要固定最大 roster，也不应先形成全 N
2
 pair score。若当前关系图有 ∣E
t
	​

∣ 条边、事件前沿有 m
t
	​

 个成员，则目标量级应接近

O(N
t
	​

+∣E
t
	​

∣+m
t
	​

d),

而不是 O(N
max
2
	​

) 或每个检查时刻串行解码全部 N
t
	​

 个成员。全队同时变化时仍至少需要处理 O(N
t
	​

) 个输出，这是问题本身的下界，不是架构失败。

这套架构解决的是 roster、协调、概率和时间信用的共同接口。它不自动证明技能是行为上可辨识且合作上有用的；技能可执行性、差异性和合作效应仍是上游因果边，不能由一个正确的事件系统替代。

2. Evidence audit
Repository facts

固定 N、固定检查钟的 HMASD 是正参考，但不是变量 N/T_i 的证据。共同简报记录 R41B 复现通过、最终 win 为 0.89，并明确原始 HMASD 是参考而不是可静默改写的模板。

R42 的实现是有效的，但 treatment 相对 fixed 的 win 差异均值为 −0.10，95% 区间为 [−0.17,−0.03]；异步 discordance 只有 0.10，且 treatment 仍有 0.90 的 full-sync SET。它淘汰的是这一具体 incumbent-roster residual，不是所有异步寿命架构。

R45/R46 的共同模式是“动作相关结果信息存在，但同一检查时刻没有足够的异号续期价值”。R46 的 overlap 和 action-specific informativeness 通过，而 same-check 与 role-stratified sign discordance 都为零，因此失败落在异质决策结构，而不是 critic 完全学不到东西。

R47 和 R48 分别淘汰了具体的任务盲谱过程表示和 skill-boundary hidden reset；两者都没有测试 episode 内 roster，也没有证明普通 recurrent MARL 或其他事件语义无效。

R50–R53 没有提供已识别的 shared-versus-specialist 跨 N 结论：

R50 的 specialist 前提只因 N=16 exact-roster 门失败，而 shared arm 数值较好；文件明确写着 “do not judge variable-N sharing”。

R51 的 implementation、概率和 ledger 审计通过，但 specialist 和 shared 都没有任务访问，结果要求隔离 shared。

R52 的 specialist access 失败，即使 shared arm 的内部门为真，也被明确隔离。

R53 的多数最终策略能力检查通过，但注册的零基线/学习增益条件没有通过，因此 shared transport 仍未识别。

R54 的 full-active-set reference 在 N=8,16,32,64 上 exact-roster success 分别约为 0.633、0.137、0、0，token accuracy 也随 N 明显下降；固定 8 槽加 2 residual 的 hybrid 同样未解决关键成员召回和 held-out N。这是对该 toy、该网络和该压缩方案的负证据，不是“任何全局 attention”或“任何稀疏压缩”不可能。

Paper-supported claims

这里的“文献证据”指仓库内基于原论文 PDF 和官方代码快照形成的逐篇分析；我没有把控制器的跨文献综合当成绑定结论。

八篇中没有一篇同时实现 episode 内 join/leave/rejoin、幸存状态连续性和正确的异步 on-policy/SMDP 语义。

ACE 直接支持 per-agent readiness 和掉队压力，但其 buffer 仍固定 num_agents，return 没有按真实 T
i
	​

 使用 γ
T
i
	​

。

ACAC 直接支持 agent-centric event histories 和 duration-correct credit，但 roster 在启动时固定。

InforMARL 支持共享参数的局部图和跨固定 N 配置复用，不支持 episode 中途改变 roster。

Sable 是 1,000+ agent 的序列容量参考，但依赖固定 n_agents、固定顺序和同步时间。

ExpoComm 降低了通信边和图直径，但其循环索引和同步 one-peer 时钟在 roster churn 后会重映射语义。

Safe-M3-UCRL 的 pure mean field 会抹去有限团队中的稀有关键个体、绝对人数和异质技能。

CT-MARL 支持“真实时长必须进入价值语义”，但所有成员共享同一 Δt，并非 per-agent T
i
	​

。

IARO 的全员投票、同步执行和共同终止恰好构成 shared renewal barrier 的反例。

My inference

N 变化和技能寿命变化可以统一为活动承诺集合的事件编辑。

关系图、set encoder、slot 或 mean field 都只是该策略状态的候选表示，不是独立的最终算法。

AR 是否必要不是由 HMASD 历史决定，而应由后续 token 对真实 prefix 的条件依赖是否承载了额外协调信息决定。

额外 team latent 不是必需不变量；若活动技能集合和已应用 prefix 已经是可行动的团队上下文，独立 team code 可能只是重复表示。

稀疏图是可扩展实现的优先项，但只有在任务相互作用本身可稀疏化时成立；全局强耦合任务可能仍需要全局 pooling 或低频全局事件。

False synthesis in the common brief

共同简报的事实表本身较谨慎；假综合主要存在于其候选框架的隐含前提中。

第一，原 H0 是一个偏弱的稻草人。 普通 MARL 不必等于固定 N_{\max}、dummy agents 和全员同步检查。一个共享参数、active-only/ragged、带 recurrent state、per-agent scheduler 和 duration-correct collector 的 MAPPO，仍然属于普通 MARL，却已经覆盖了大量所谓 H1/H2 的接口能力。原 H0 的写法会夸大新架构相对普通 MARL 的必要性。

第二，固定-N HMASD 的内部结构不应被误当成变量-N 后继的必要部件。 简报正确地写了“preserve or deliberately replace”，但候选叙述仍容易把 team code、AR 和 skill semantics 捆成一体。原则文档已经记录过 sampled team intent 几乎不影响 assignment，属于 behaviorally inert/decorative；因此应保留“可行动的联合分配功能”，而不是保护某个 team latent。

第三，文献综合中的 graph → slots → critical residual → fixed-length coordinator → event histories 是机制清单，不是已证明的组合架构。 该综合自己提出了这一长栈，但项目原则要求每个新机制必须吸收或淘汰一个旧机制；R54 又直接削弱了当前 fixed-slot/full-set 组合的经验前提。

3. Portfolio reconstruction
处置	架构族	Replaces	Retains	Adds
MODIFY H0 → H0′	Active-set scheduled MARL	原 H0 的固定最大 roster、dummy 语义和强制全员高层检查；不使用 learned joint event editor	共享 actor/critic、recurrent state、标准 CTDE；可选择保留 skill-conditioned low actor	active-only packing、幸存状态表、per-agent 外生或独立 scheduler、agent-centric SMDP ledger。策略在给定匿名 active-set summary 后按成员条件独立
MERGE H1 + H2 → H12	Exchangeable event-sourced relational editor，首选结构	固定 roster 的全员编辑、独立 team code、固定槽摘要、作为独立算法存在的 H2	HMASD 个体技能瓶颈、working-roster prefix、later-on-earlier 的联合分配、精确行为概率和 duration credit	动态活动承诺集合、显式 join/leave 生命周期、稀疏关系编码、只对事件前沿进行 AR 编辑、幸存 hidden continuity
MODIFY H3 → H3′	Decentralized skill-hazard MARL	中央 AR token 序列和全局续期 barrier	个体技能、per-agent lifetime、匿名活动技能上下文、真实事件 ledger	每成员独立继续/终止/换技 hazard；冲突必须由采样前的确定性可行性 mask 或被完整记录的联合 resolver 处理
ADD H4	Marked event-intensity / point-process skill controller	周期性的 KEEP/SET 检查钟；离散候选 duration	active-set 表示、skill-conditioned executor、SMDP return、外生 roster 事件	对技能终止时间和新技能 mark 建模的 hazard/intensity、survival probability、censoring 与 competing-risk likelihood

具体判断如下。

H0′ 必须保留为最强普通-MARL 归约。 它与 H12 的区别不是有没有正确 collector，而是策略联合分布是否在给定 active-set context 后条件分解。若 prefix 没有额外信息，H12 就应收缩成 H0′。

H12 是当前最强架构解释。 H1 负责“哪些时刻存在决策以及如何联合因子化”，H2 只负责“如何表示当前活动集合”。两者分开会造成假模块边界，因此合并。H2 作为独立架构族应退休，但局部图、set pooling 或稀疏邻域仍可作为 H12/H0′ 的可替换 encoder。

H3′ 是严肃的低带宽替代，而不是 H12 的简化实现。 它假设合作所需的耦合主要通过共享状态和 critic 学到，终止决定本身近似独立。若 later-on-earlier 的依赖不承载信息，H3′ 可能比中央事件编辑器更稳、更便宜。

H4 是唯一新增族。 它把技能寿命真正建模为随机事件时间，而不是每 k
0
	​

 步询问一次 KEEP。其优点是异质寿命原生；缺点是 PPO 概率必须包含生存项、积分 hazard 和外生 censoring，正确性风险明显高于 H12/H3′。因此它应留在组合空间中，但当前不应成为默认路线。

4. Capability matrix

✓ 表示架构原生覆盖；△ 表示可覆盖但依赖额外正确性条件；— 表示刻意不提供。设 m=∣F
t
	​

∣ 为一次事件中的实际编辑成员数。

架构族	Episode-internal N	Heterogeneous lifetime	HMASD skill semantics	Autoregressive coordination	Probability / credit correctness	Computational scaling
H0′ Active-set scheduled MARL	✓ active-only roster、生命周期键和 survivor state	✓ 外生或独立 per-agent scheduler	△ 可保留 z
i
	​

，但不保证互补联合分配或 skill discovery	— 条件分解	✓ 若只给真实事件建 row，并使用 γ
T
i
	​

；普通同步 buffer 不合格	通常 (O(N+
H12 Event-sourced relational editor	✓ JOIN/LEAVE 是同一 ledger 的结构事件	✓ KEEP/SET 延伸同一技能承诺	✓ 保留个体技能；活动 roster/prefix 替代独立 team code 的功能	✓ 只对事件前沿 AR	✓ 每 token old log-prob、prefix、mask、owner、duration 均被存储	(O(N+
H3′ Decentralized hazard	✓ 本地状态由 active roster 路由	✓ 最自然的独立寿命形式之一	△ 个体技能强，互补联合分配较弱	— 或仅确定性 resolver	△ resolver 若在采样后改动作而不入 log-prob，则立即无效	最好，约 (O(N+
H4 Marked event intensity	✓ 外生 birth/death 作为 context/censoring 事件	✓ 原生学习随机技能终止时间	△ mark 可为技能，但合作语义不自动出现	△ 可对同一事件的 marks 联合因子化	△ 必须精确计入 survival、integrated hazard、censoring 和 mark probability	每次 intensity 评估可 (O(N+

矩阵中最重要的结论是：概率与信用正确性不是 H1/H2 的独占能力，而是所有可接受架构必须具备的基础设施契约。 因此它不能被算作 H12 相对 H0′ 的算法优势。

5. Unifying insight versus module stack

可以吸收成一个原则的文献思想是：

策略只在活动承诺集合发生政策相关变化时产生决策；表示、行为概率与信用都围绕同一个真实事件组织。

在这个原则下：

ACE 的 readiness 只是事件触发语义；

ACAC 的 agent-centric history、γ
Δt
 和事件级 λ 只是事件 ledger 的学习语义；

InforMARL 的局部图和 ExpoComm 的有界邻域只是交换等变 active-set encoder 的候选后端；

HMASD 的 applied working roster 是联合事件分布的可行动上下文；

CT-MARL 贡献的是“时长必须进入 value target”这一不变量；

IARO 的共同终止不是模块，而是应避免的同步反例；

mean field、slots 和 global pooling 都只是有损摘要候选，只有在充分性成立时才可使用。

这样吸收后，架构只有三个真正不可混淆的层次：

活动承诺状态：谁活跃、执行什么技能、持续多久、hidden state 属于哪个生命周期；

事件策略：本次哪些承诺发生变化，以及这些变化是否需要联合因子化；

事件学习语义：谁拥有 log-prob、真实时间经过多少、怎样 bootstrap。

以下组合则会形成脆弱模块堆：

full-set attention 后再做 fixed slots，再补 critical residual，再加 sparse graph；

同时保留 global team code、field summary、slot summary 和 AR prefix；

对所有成员每个固定检查钟运行 event-token decoder，即使只有一个成员到期；

用 Sable 展平 T×N，再额外安装 open-roster state table；

用 ExpoComm 的固定循环 ID 作为匿名动态 roster 图；

把 CT-MARL 的 PINN/HJB/VGI 整栈引入 PPO；

在 H12 上再叠 H3 的独立 termination head，却不定义哪个分布拥有最终执行事件；

为了“技能语义”同时加入 IARO eigenvector reward、通信辅助损失和新的 process reward。

仓库中的跨文献综合明确列出了 active tokens、sparse graph、fixed slots、critical residual、fixed-length coordinator 和 agent-centric histories；但这是一份候选部件表，不是联合必要性的证据。

我的替代原则直接删除 fixed slots 和独立 team latent 作为默认项。只有当 active-set encoder 在现有观察上确实发生不可接受的信息别名时，才有理由增加摘要结构；不能预先安装后再寻找其用途。

6. Discriminating evidence

最小且真正改变组合权重的证据，不是新的 toy，也不需要环境 rollout、训练或优化器步骤。

Reanalysis

使用现有 R53 最终 checkpoint 与已存 evaluation/decision ledger，对其自回归 coordinator 做一次prefix 必要性审计。R53 已经证明 dynamic mask、previous-relation、prefix 和 sample log-prob 可以精确重放，因此这项分析不需要重新训练。

对每个 later token，固定：

环境与 active-set state；

focal member features；

recurrent hidden；

当前合法动作集合；

当前 token 位置。

然后比较两个均合法的 earlier-assignment prefix p,p
′
。分析分成两部分：

MaskDependence=1{support(p)

=support(p
′
)},

以及在共同合法支持上的 learned-logit 依赖：

PrefixGain=D
KL
common
	​

[π(⋅∣s,p)∥π(⋅∣s,p
′
)].

若现有动作空间允许枚举合法 prefix，可直接计算

I(A
j
	​

;A
<j
	​

∣S,active roster,mask),

否则使用共同支持上的 KL 与 action-rank reversal。结果按 N、是否存在容量竞争、是否为 burst/persistent 冲突状态分层。与 logged utility 的关系只能作观察性支持，不能称为因果收益。

这项审计只回答“自回归条件是否是负载承载结构”，不回答 variable lifetime、skill discovery 或 open-roster learning。

Outcome-dependent portfolio updates

结果 A：共同支持上的 PrefixGain 近似为零，且 earlier actions 也很少改变 mask。
H12 的 AR decoder 在已有任务上可约化。将 H12 的事件 ledger 和关系 encoder 吸收到 H0′；退休“later-on-earlier 是必要协调机制”的主张。H3′ 上升为首选异步寿命方案，H4 没有新增支持。

结果 B：依赖几乎全部来自动态 mask，共同支持上的 logits 不变。
说明序列主要在执行确定性可行性约束，而不是学习互补条件分布。优先 H0′ 加采样前 deterministic feasibility layer；H12 可保留为序列化实现，但不能作为算法贡献。H3′ 仍可用同一 mask/resolver。

结果 C：共同支持上存在稳定的 learned prefix dependence，集中在真实竞争状态，并能跨 N 保持相似结构。
这会真正支持 H12，削弱条件独立的 H0′ 和 H3′。AR 应只保留在事件前沿，而不是扩展成每个检查时刻的全 roster decoder。H4 对这一结果中性，因为它解决的是事件时间，不是联合 mark 的必要性。

结果 D：prefix dependence 很大，但只在某个 N、某种顺序或任意成员位置上出现。
这更像 order/slot memorization，而不是可交换协调。H12 降权；H0′ 和 H3′ 升权。任何后续事件编辑器都必须先消除顺序语义泄露。

结果 E：不同 prefix 没有足够共同支持，所有差异都被 hard mask 决定。
R53 无法区分 learned AR 与确定性约束；组合保持未识别。不得据此继续执行一个新的 fixed-membership toy。

这比重新启动 R55 更有信息量，因为至少 A、B、C、D 四类结果会导致实际的 merge、retain 或 stop 决策，而不是仅给某个 toy 一个 PASS/FAIL。

7. R55 disposition

REPURPOSE

R55 作为 fixed-membership、fixed-horizon direct-edge toy 不应按原样执行。共同简报已经说明它从未测试，并因不能区分最终目标假设而暂停。

应保留并重新使用的不是该 toy 环境，而是它隐含的问题：

“较晚成员的动作分布是否真正依赖较早成员已经做出的选择？”

这个问题应被迁移到第 6 节的现有 R53 prefix 必要性审计中。这样：

不增加新环境；

不生成新的编号实验；

不修改训练 contract；

不需要超参数；

能直接决定 AR 是整合、降级为可行性序列化，还是停止。

若该审计发现只有 mask dependence，R55 的 direct-edge 架构线可以停止；若存在稳定 learned dependence，R55 的核心问题已获得更强的现有策略证据，也没有必要再执行原 toy。

8. Strongest self-critique

我偏好的“事件溯源半马尔可夫承诺编辑器”可能并不是一个新的算法，而只是把正确的软件与数据契约重新命名。

一个普通的共享 recurrent MAPPO 可以同时具备：

active-only 或严格 masked roster；

每成员 hidden-state table；

action persistence 或 per-agent scheduler；

DeepSets/GNN centralized critic；

skill-conditioned actor；

agent-centric event buffer；

γ
T
i
	​

 return；

外生 join/leave mask。

若成员动作在给定 invariant active-set summary 后基本条件独立，那么 H12 的事件前沿 AR 只是把 H0′ 的联合采样串行化；所谓“活动承诺集合”也只是 ragged batch 加 option state。此时最诚实的结论应是：普通 masked/scheduled MARL 已经足够，真正需要的只是正确的 collector 和 SMDP accounting。

此外，我对稀疏关系编码的偏好部分来自 R54 的负结果，但 R54 只淘汰一个 toy、一个 full-set reference 和一个固定槽压缩。更好的全局 attention、不同训练分布或 moderate active N 完全可能使 O(N
2
) 不是实际瓶颈。稀疏图反而可能遗漏低频但全局关键的依赖。

还有三个具体风险：

匿名 AR 顺序可能重新引入身份。 即使 agent ID 不进入网络，只要某些生命周期键持续更早出现在 prefix，策略仍可能学习隐式槽位语义。

异步 team-reward credit 可能增加方差。 多个重叠技能承诺共享稀疏团队回报时，事件 ledger 能保证数学一致，却不能保证 credit 足够可学。

HMASD skill ontology 本身可能不是必要抽象。 R41B 证明固定-N HMASD 能工作，不证明 variable-N/lifetime 问题必须继续使用离散技能。一个普通 recurrent policy 或通信策略可能直接学到所需持续行为，且不承担 skill identifiability、termination 和联合 assignment 的全部额外因果边。

因此，我的首选是一个最简架构解释，不是已获经验支持的最终算法。现有证据支持 event ownership、active-set exchangeability 和 duration-aware credit 是正确性不变量；它尚未证明 learned event editor、AR prefix 或离散 HMASD skills是性能上不可归约的必要条件。
