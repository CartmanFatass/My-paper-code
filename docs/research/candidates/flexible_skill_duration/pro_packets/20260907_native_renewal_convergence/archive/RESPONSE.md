**选择（a）：允许一次严格限于已选检查点的原生续约控制重入；不恢复整个固定 K2 policy-gap 学习收益分支，也不在本轮选择新的训练。** 理由不是 E4 还有结构差距，而是 P13 已把一个实际可操纵的环境动作、它的反馈路径以及一份具体保留权重对应起来。现在能够提出一个不同于 E3 的问题：在不改变权重的情况下，只替换真正送进环境的续约动作，这个既有控制器在自己随后产生的轨迹上能否提供更好的原生服务？这一读数可以改变是否继续投资“保留现有角色生成路径、改进续约执行”的判断；再做参考普查不能回答它，重新训练也不是这个固定权重问题的替代测量。

这是一项有明确终点的有限继续，不是已经得到正结果，不是把 H 命名为同步 D2 中断，也不是重新判定 E3。原暂停只在下面这个控制观测子范围内解除，其他未选训练、阈值、种子、host 和机制改写仍不由本决定开放。方向的 ACTIVE/HIGH、Portfolio 生命周期、优先级、容量和 UAV 投入不变。当前任务只交付研究答复；实际代码任务、科学卡、资源准入和调用仍由后续已有路线给出，本答复不声称已经分配或执行它们。（[P13 准备记录，§2–6][p13]；[post-E4 intake，Final decision / Re-entry][post]；[P14 的 FSD 专项][handoff]。）

## 一、为什么选这个控制问题，而不是直接训练或继续无后继暂停

此次选择的最小范围是：**已接受的 E3 large_d2_seed2 最终检查点，在原大差异 Bernoulli corridor 上的一次 C/H/G fresh-episode 比较**。仍为 N=6、每个 region 三个固定实体、K=2、四个 host zone、两个 region、H=400、hazards=(.02,.20)、Delta=1、rho=0、无 probe 和 E5 coupling。模型中的 team token 数是 n_Z=6，individual skill 数 n_z=2，原生 action_dim=2；四个 zone 不能代替六个 team token。C/H 内部均保留 c=c_Z=.25、individual/team caps=40/400、age feature off。P13 明确记录了这些不同数量和既有状态路径。（[P13，§2–4][p13]；[所选单元的 Terminal technical acceptance][cell]。）

三种方向选项的比较如下。

| 选项 | 真正新增的信息 | 此次处置 |
| --- | --- | --- |
| （a）固定检查点 C/H/G 控制观测 | 既有权重在改变实际续约后的闭环原生回报，以及这些新轨迹上的角色实现损失；不靠旧轨迹反事实拼接 | 选择一次，范围和终点见下文 |
| （b）直接真实 B | 新训练方法或新独立训练种子的学习表现、更新与评估结果 | 合法且不必先通过（a），但本轮不同时选择；它回答的是另一个问题 |
| （c）维持无后继暂停 | 不产生上述执行差异的观察 | 暂不选择：P13 已提供此前没有落实的具体动作语义和保留策略依据，足以选择这一有限观测，而不是先要求未来运行成功 |

必须承认（a）的反对意见：H 是人为解耦的执行控制器，正结果可能来自改变后的 observation、技能选择和 recurrent state，而不是原 policy gap 终于成为正确的学习信号；其实现、加载和测量也有成本。因此，我不把它辩护成“零 learner 所以一定最便宜”，也不把它当作所有后续 B 必经的资格考试。它值得测的独立理由是：**在这一已训练但失利的实例上，原生续约替换是否已经足以释放可实现的服务，还是保留的角色生成路径仍留下显著服务损失。** 这会分别支持或削弱针对该实例的续约执行投资，而不是要求先解释所有历史失败。

直接 B 的可信最小对照可以从既有大行 D2 c=.25 与 D0 k=5 的真实 learner 路径、一对新的配对训练种子起步。P13 给出的两臂、一个训练种子、一个 rollout、16 lanes、H=400 示例，在评价之前就只有 12,800 个训练 transitions，另有真实 updates 和评价；新小预算下的 D0 competence 仍要观察，不能继承旧种子的合格标签。这说明直接 B 完全可能比诊断更值得做，也说明一个 rollout 的参数运动不等于充分学习。若目标改为新学习性能，应直接选相称训练，而不是扩大本诊断。**此次目标保留为旧权重下的原生执行问题，因而不另列一个待自动启动的 B 矩阵。**（[P13，§5][p13]；[证据规范，§5.2、§11.8.2–3、§11.9][spec]。）

证据类别也要分清：本轮据以作决定的 P13 是 **A/RECON 源码和保留 artifact 事实**；所选后继是**固定检查点的控制干预探索，解释上限为 B/EXPLORE 层级的条件初步观察，而不是新的普通 B 学习实验**。它不产生新的训练种子、学习曲线或 optimizer 暴露，不能登记为“D2 学习效果已验证”。后续任何声称算法学习表现的普通 B，仍必须实际运行其 learner、trainer、环境和 evaluator，并报告真实非零训练及评价工作；不能用本控制测量顶替，也不为取得 B 名称添加无意义的 optimizer 调用。这里放弃的是新学习效果和学习机制归因的更强主张，不是放弃原生回报、信息权限或比较完整性。（[证据规范，§3–5.2、§11.8.1、§11.8.6][spec]。）

## 二、旧结果继续成立，新源码事实不替它们翻案

E3 的 18/18 有效 adaptive B 保留原解释。大行三个 D0/reference 比值约 .885433/.912488/.884880，三个配对 D2−D0 为 −.071387329/−.108895874/−.086455282；原规则仍得到 E3-H0-NO-ADVANTAGE，关闭的仍只是 c=c_Z=.25、该大行和每臂 20 rollouts/128,000 transitions 的声明。medium/large 六个合格配对全部失利；不能因为重新选择 large seed2 而把其旧负结果改称技术无效。原累计事件路径 false/true/false 与另报的最终窗口 false/false/true 都保留，不换窗口。

最强学习支持仍是 small seed2 对合格 D0 的 +.033291585，以及 E2 中阈值对 duration 的单调控制。small seed3 的 +.062728760 也保留，但其 D0 比值 .814254153 未达原 competence 线，不支持 superiority。最强反证是上述六个合格负配对，尤其累计路径阳性的 large seed2 仍损失约 .108895874。（[E3 完整结果，Paired final returns / Regional event path / Frozen rule][e3]；[DIRECTION，Accepted mechanism-level science][direction]。）

E4 则继续是三种 law、288 个候选、零 learner 的完整 A。随机 law 的 switching-over-best-clock 差距约 .0970995/.0982251362 全部被合法公开信息 greedy 解释。它否定“这个结构差距本身证明需要学 policy gap”的用法，不是证明所有 learned policies 在所有问题上都无价值。确定性 law 的零差距仍按原数值约定读取；只匹配名义均值不构成 variance-only 因果变化，rounded-lognormal 的 residual mass=0 仍是浮点 1−mass，不是无穷尾为零的证明。（[E4 完整结果，Population / Law facts / Frozen rule][e4]。）

噪声 gap、actor/representation 质量、seed 差异、不同 optimizer exposure 和 team-renewal interference 仍未被分离。medium/large 的 D0 actor/critic 每单元各 72k updates、D2 各 9k，是保留的旧执行路径，不是新增有效性缺陷，也不证明匹配 updates 会治好问题。所选检查点过去的 128,000 transitions 和 coordinator/actor/critic/team/individual updates=4350/9000/9000/300/1200 只属于历史训练；其非零位移不等于角色已经学会。P13 选这个检查点，是看到失利和累计路径后的选择，不是随机选出的代表性种子。（[E3 完整结果，Validity / Exposure][e3]；[所选单元技术接受][cell]；[P13，§3、§5][p13]。）

新增的支持不是新增收益，而是一个更具体的源码结论：**内部 skill token、host 的 held_role、本步实际发出的 role，是三个不能混同的量。** 内部 D2 先决定 sampled mask、partial assignment 和年龄等状态；recurrent actor 再在每个 primitive step 生成连续二元 action；adapter 对 action 做 argmax，再独立传递 renew。host 在 KEEP 时评分的是本步 role，不是强制使用 held_role。只改 native renew 因此确有环境后果，但不是同步修改内部技能与 duration credit。（[agent.py 的分配、动作和 step 路径][agent]；[networks.py 的 partial decode / actor][networks]；[adapter.py L98–154][adapter]；[host.py L266–405][host]。）

## 三、唯一后继：闭环执行 C/H/G，不制造反事实 tape

设 i 所属固定 region 为 r(i)，当前公开 flag 为 f。对 C，实际送入 host 的 renew 就是它自己本步的内部 d2_sampled_mask。对 H：

- t=0 保留 H 正常 D2 reset 产生的 forced renew；它与 C 采用同一初始约定。
- t>0，仅将实际 host renew 设为 f[r(i),t]。取的是评分本步之前可见的当前 flag，不是下一次 transition 才产生的 flag。
- H 的内部技能选择仍正常执行，使用 H 自己的 observation、state、技能历史和隐藏状态。既不复制 C 的 sampled mask，也不修改 H 的内部 mask 来假装同步。

C/H 的权重、确定性动作选择约定、内部 c/c_Z 和 caps 相同；它们的内生状态与 action 可以不同，而且在有环境反馈时本来就应该允许不同。H 的连续 action 仍来自其 learned actor，不能把 G 的正确 role 填进去。两者都不做 transition storage、训练 update 或 optimizer.step，不伪造 replay metadata。（[P13，§2–3][p13]；[agent.py L2114–2177、L2330–2619、L3087–3160][agent]；[adapter.py][adapter]。）

原生链为：**外生区域事件改变 latent/epoch，使该区域固定实体的 lease 失效 → 公开 flag/cue 与自身 lease/age/held-role 进入 observation → 内部 D2 和 recurrent actor 产生本步技能与 role → H 只替换实际续约动作 → host 当步按 KEEP、freshness、role correctness 评分，再按 RENEW 写入 epoch/held_role/age → H 接收自己真实的下一 observation/state → 下一步继续自己的内部决策。** 人员、zone/region ownership 没变。host renewal 不重置外生区域 dwell age。这个比较估计的是执行规则替换的**总闭环效果，包括它引起的后续技能、隐藏状态与动作变化**，不是把所有中介固定后的“纯 timing 直接效应”。（[host.py L266–405][host]；[networks.py L1439–1465、L1687–1693][networks]。）

G 使用现成 GreedyOnPublicState，独立 reset 自己的 host 和 plan，仅从公开 cue、flag、zone 推出 K2 role 和续约时机。它是有能力的 operational null，回答同一公开信息下原生服务是否可实现；它绕开 learned actor，不能为 C/H 的 actor 领取 competence。这里不需要重新枚举最优策略，也不要求 H 超过 G 才有可报告的控制增益。（[references.py L436–468][greedy]。）

三个策略只共享同一组外生 episode keys 和 host 参数。32 个 keys 及顺序在看到任何本次回报前一次指定，不按结果筛选；使用旧 keys 时明确记录复用，不能称为新的独立训练或独立确认。每个策略有独立的 host、plan/controller state；禁止以 C 的 action/state/hidden trajectory 当作 H 的后续轨迹。旧 E3 保存了 per-episode returns，并未提供所需的全 action/logit/hidden 反事实 tape；这次不需要也不假定有这种 tape。（[P13，§4][p13]；[E3 evaluator L240–299][e3runner]。）

## 四、fresh-episode 状态处理：足够具体，但不要求重演整段训练

**先明确加载什么。** 目标是旧 launch 6d64a95a1189523e39abb184ef284a574050b748 的 large_d2_seed2 最终权重。原技术接受检查过 64,782,527-byte checkpoint 的有限 float32 tensors、configuration 和 normalizers；P13 后来直接核对其存在、大小和 SHA256 2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89，未反序列化。本节点读的是这些证据记录，没有访问或加载 checkpoint 本体。未来节点的实际加载仍未验证。（[P13，§4][p13]；[单元技术记录，Terminal technical acceptance][cell]。）

C/H 分别构造自己的 evaluator/policy 实例，从同一个已选 checkpoint 恢复实际需要的网络和启用的 normalizer；不能使用随机残留层、默认统计或错误维度却称为同一固定 policy。构造配置保持既有模型结构、n_Z/n_z/action_dim、recurrent 路径、dtype 与 D2 参数。32 lanes 是评价批量，不是把训练结构或 team token 改成 32。E2 的模块级 E2CorridorConfig 是实际 pickle class 路径，需按原保存语义处理，而不是只用一个同名临时默认类。（[agent.py L7143–7293、L7346–7664][agent]；[E2 runner L165–172][e2runner]。）

manifest 中 use_obsnorm=false、use_statenorm=false、use_valuenorm=true。不要为已关闭的 observation/state normalization 发明移植缺陷；仍应正确保留启用的 coordinator/discoverer ValueNorm mean/var/count，并在评价期间不更新它们。load_model 是 non-strict 加载，成功返回不能证明所需权重都载入，缺失启用统计还可能保留默认值。所需检查限于影响此次 policy、状态和 primary measurement 的实际字段，不把无更新的本测量扩张成完整 optimizer-resume 等价验证。（[P13，§4][p13]；[agent.py 的 save/load][agent]；[E2 evaluator L456–508][e2runner]。）

**每个策略从完整新 episode 开始。** C/H 都采用现有 evaluator 的 train(False)、deterministic=True、clear_buffers 和逐 lane reset_env_state。清除当前/前一 actor、critic 隐藏状态，技能无效化、timer/age/duration/reward/log-prob/pending 等状态按既有 reset 处理；host reset 返回的 observation 和 global state 必须一起作为 t=0 输入，env_steps 从零开始，不能把旧终端 state 搭配新 observation。此后每步接收本策略实际 host 输出，正常携带自己的 recurrence，不能在每次换 renew 时额外清空隐藏状态。G 独立执行其 plan reset。（[agent.py L1559–1621][agent]；[E2 evaluator reset][e2runner]；[E3 fresh-episode loop][e3runner]；[GreedyOnPublicState][greedy]。）

checkpoint 不包含完整 host、lane hidden states、当前 skills/ages、open segments 或全部 RNG 快照，故不宣称 mid-episode branching、轨迹续训、historical replay 或跨平台 bit equality。新评价使用显式外生 episode keys，C/H 用既有确定性 coordinator/actor 路径；构造时的随机初始化不能成为未加载权重的替代。P13 的十四个 method AST 相同，只支持所列源码片段的对应，不证明所有依赖或未来 evaluator 等价。（[P13，§4][p13]；[agent.py save/load][agent]。）

这些是该**依赖旧权重的测量**所需的状态语义，不是对所有普通 B 的全源码预审要求。本轮不加载、不测试。后续实现只需把改变的 state-to-action 路径和主输出做一次有针对性的核对，复用已有正确路径；不增加一轮 checkpoint 诊断普查，也不要求 C 在新 32 episodes 上精确重现旧 2,048-episode 均值。损害所需权重、信息权限或回报语义的实际错误会限制依赖它的读数，不能用缺少全历史快照一概拒绝 fresh-episode 测量。（[证据规范，§11.8.5–7][spec]。）

## 五、观测单位、主比较和角色损失

主单位是**固定检查点下的外生 episode**。对每个 episode e、策略 p，记录

\[
R_{p,e}=\frac{1}{400}\sum_{t=0}^{399}r_{p,e,t},\qquad
d_e=R_{H,e}-R_{C,e},\qquad
\widehat D=\frac{1}{32}\sum_{e=1}^{32}d_e.
\]

报告全部 32 个 C/H/G episode 回报、全部 d_e、均值以及配对 episode 标准误 s(d)/sqrt(32)。不要用 H 的新样本与 C 的历史 .455985311 均值做非配对替代；历史均值只是背景。32 个 episode 不等于 32 个训练种子，230,400 个 agent-step 也不是独立样本数。更多对这个检查点的评价不能估计训练种子总体的不确定性；32 也不保证足够的统计分辨率。（测量定义沿用 [E3 evaluator][e3runner]；独立性解释依据 [证据规范，§5.2、§11.8.3][spec]。）

同时报告 post-reset 回报

\[
R^{>0}_{p,e}=\frac{1}{399}\sum_{t=1}^{399}r_{p,e,t},
\]

及其 H−C、G−H 的逐 episode 配对差异。两个分母必须明确，不能把全回报与 post-reset 均值混在同一列。G 的默认 t=0 不续约与 C/H 的 forced reset renew 不同，初始一步在全回报上的已知尺度为 Delta/H=.0025；不能将这部分记成 duration 收益，也不增加第四个重置策略臂来重复解释它。（[P13，§3][p13]；[host.py][host]；[GreedyOnPublicState][greedy]。）

角色实现损失使用 host 在**本步评分时**给出的 applied renew、lease_fresh、role_correct，而不是更新后的 freshness。对 H 的 post-reset 部分，报告 reward 单位的

\[
L^{>0}_{H,e}=\frac{\Delta}{399N}\sum_{t=1}^{399}\sum_i
\mathbf 1\{\mathrm{KEEP}_{H,e,i,t}\land \mathrm{fresh}_{H,e,i,t}\land \neg\mathrm{correct}_{H,e,i,t}\}.
\]

一并给出 eligible KEEP/fresh 次数和 wrong-role 次数；没有 eligible 机会时条件错误率写为不适用，不能写成零错误或完整 competence。正确性标签只作为测量，不作为 C/H/G 新输入。G−H 与 H 的这些原生损失相对照，可以把“有实际增益”和“仍未实现可用服务”分开，但不把条件误差率外推成原 C 分布、全部状态或新训练策略的 actor competence。必要的内部与实际 renew 计数可随同记录，以表明被操纵的是哪个 mask；不要求保存全部 logits、hidden arrays 或另建反事实日志系统。（[host.py L318–377][host]；[adapter.py L98–154][adapter]。）

我接受 **.01 mean native reward 作为此次解释的描述尺度**：在 Delta=1 时它对应一个百分点的平均原生服务，且大于单步 reset 的全回报贡献。它不是显著性、等价、完整 competence 或硬投资阈值；不会改 E3 的任何分支。尺度内的真实增益也报告，正负和不确定性都保留，不用阈值把局部支持抹去。是否“接近 G”必须同时列出实际 post-reset 差距和 wrong-role 损失，不能仅凭一项不显著就声称等价。（[P13 的尺度提议][p13]；[证据规范，§11.7、§11.8.2][spec]。）

## 六、不同读数到底改变什么决定

| 完整、可信的本次观察 | 能改变的实际判断与后续投资含义 | 不允许的推论 |
| --- | --- | --- |
| H 相对 C 有原生改善，post-reset 接近 G，且 eligible wrong-role 损失小 | 不再以“保留这份 actor/skill 权重不可能产生高服务”作为该实例的工作假设；把原生续约执行保留为值得有限后续研究的具体杠杆 | 不等于同步技能/credit 改动有效，不等于 D2 学到事件规则或可在新 seed 重现 |
| H 改善 C，但仍有明显 G−H 与 wrong-role 损失 | 接受局部 native gain，同时撤回“只改续约就恢复完整控制能力”的强解释；任何后续方案须如实包含角色实现短缺，不能凭 gap 相关性继续加预算 | 不能把全部残差归于 actor 表示、recurrence、team 或训练暴露中的某一个 |
| H 不变或更差 | 不以本实例的 actuator substitution 为理由继续 timing-only 投入；完成这一观测后，未另选的学习分支继续暂停 | 不否定其他 checkpoint、threshold、独立 B 或整个方向 |
| 32 episodes 对关键差异仍分辨不足，或不同 episode 方向不一 | 如实记录有限信息，按既定终点结束；是否再问一个问题需新的决策价值，而非追求全正号 | 不把不显著称为等价，也不自动加 episodes、挑 seeds 或提高 cap |

上述分支改变的是**这个特定原生控制候选是否得到支持，以及支持到哪个范围**，不是自动下发第二个对象。任何结果都不直接指定同步 D2、Q-head、team-credit、K3 或新 host。特别是 H 的正结果只支持进一步提出相称的学习或控制问题；把公开 mask 真正送入 skill sampling、partial decode、计时器与 credit，是新的待完整指定干预，不能说“adapter 改一行即可”。负结果也可以激发一个独立、具体的新 B；本诊断不是所有 B 的先决条件。（[networks.py partial decode][networks]；[agent.py assignment/storage][agent]；[证据规范，§11.8.2、§11.9][spec]。）

这也解释为何此次不继续无后继暂停：现在的未知是一个可以用真实环境动作改变来观察的条件返回差异，不是等待一般机制定理。反过来，如果把目标扩大为“先唯一定位全部失败原因才能允许学习”，（a）就失去比例性，应取消那个前置要求而直接设计真实 B。

## 七、有限工作量、未知成本与停止

采用 P13 所列的单检查点、三策略、每策略 32 episodes、H=400、一批 32 lanes 作为这项后继的设计范围，不增加 law、训练种子或 checkpoints。下列是准备记录中已有的工具计算，不是本轮运行结果。（[P13，§5][p13]。）

| 工作项 | 所选设计量 |
| --- | ---: |
| 完整 policy episodes | 3×32=96 |
| 环境评分 step 调用 | 38,400 |
| agent-step observations | 230,400 |
| C/H learned-controller environment steps | 25,600 |
| C/H batched agent.step | 800 |
| C/H gap/assignment coordinator batch calls | 最多 1,598 |
| 每次相关 coordinator pass | 原有固定六实体 decode，不是联合策略搜索 |
| G scripted act | 400 次 batch 调用 |
| 独立 learned-policy load | 2 次 |
| 新训练开始、optimizer.step | 0、0 |

这里 H=400 是每 episode 的评分长度，host 的外生事件 transition 为 H−1；不能混用这两个计数口径。模型构造、可能由原 agent 构造出的 optimizer 对象、两次 checkpoint load、normalizer 处理和 publication 都是真实工作；“无 optimizer.step”不是“无初始化成本”。没有 beam search、best-of-many、joint-action 枚举、未来 trajectory 搜索或嵌套候选重规划。

历史最终评价的 563.180000862 s/2,048 episodes/batch512，按 episode 线性缩放仅给每个 32-episode learned arm 约 8.7997 s；旧 runner .46 s/episode 则给 14.72 s。**两者都不是 batch32 的测量，也没有为新的 standalone load/setup/publication 和 G 的独立执行定价。** 现有 E4 的 DP 秒数更不能用于这里。未知费用保持未知，不增加单独 profiling/cost experiment，也不保证此次会比前述 12,800-transition 最小 B 示例更便宜。（[P13，§5][p13]。）

在选择这个有限问题时，我采用**每个完整策略最多 180 s、三策略合计最多 540 s 的 invocation wall 设计上限**，包含各自 load、评价、必要读数检查和 publication。它是下一实际卡应保留的边界，不是已获资源准入、P14 已分配的调用或对旧预算的扩展。额外的改变行为/主输出工程核对须在后续完整任务中单独列出其目的与预算，并单独报告真实消耗；不能通过把科学初始化或结果发布移到别的进程、切片或所谓验证步骤来规避完整 invocation cap。算法工作与新增验证分开计量，不新增验证矩阵。

停止规则是：完整 C/H/G panel 与读数 intake 后结束；不因符号或 .01 尺度扩充样本。达到任一策略完整上限，或发现影响所需 policy loading、fresh state、信息权限、奖励或主配对输出的具体失败，就报告实际完成量及受限比较，不自动重启、换权重、减片后拼接、并行化或提高 cap。如果 H 的依赖损坏，不能解释 H−C；已经独立可信的 C 或 G 事实仍可保留，不能因为一个发布或资源字段缺失抹去所有独立读数。可选 RSS 缺失也不能自动冒充主回报失败。（[证据规范，§4、§11.8.6–7、§11.9][spec]。）

每个实际 invocation 仍需在真实执行节点上满足已有 physical/effective 4 GiB 准入；本轮没有做这一准入或赋予新命令。若实际路径在选定边界内无法完成，应回到“这项信息是否值得这个问题和工作量”的判断，而不是自动立项一轮更大的恢复或性能工程。后续研究实现只复用已有 evaluator/loader/reset/adapter/greedy 路径，保持研究 runner/source 预算，不引入 checkpoint-resume 服务、注册表、guard 链或新调度层。（[AGENTS，§5–8][agents]；[工程规范，§4–5][engineering]。）

## 八、现行方法约束、限制与本轮实际访问

有两项继承措辞不能变成新门槛。DIRECTION 的旧梯子仍写着三至五 seeds 后才能 C promotion，但本次固定输入的证据规范 §11.1、§11.8 已明确那不是普遍门槛；本观测更不提出 C 结论。工程规范也已将普通研究的 30% orchestration 比例改为审查提示，且不再要求另申请 100-line 例外。没有理由为本次选择恢复旧式全源码普查、极小数值容差、先验正结果或额外审批层；既有历史记录照原义保留。（[DIRECTION，Position][direction]；[证据规范，§11.1、§11.8–9][spec]；[工程规范，§5][engineering]。）

已执行的 post-E4 暂停不是全方向关闭，也不是让一次新方向节点必须先证明未来运行成功才有权选择问题。此次开放的是已明确定义的条件控制观测，不是回写旧暂停的理由或把未验证的加载说成已完成。当前最实在的技术未知仍是未来节点的 checkpoint→fresh evaluator 恢复及新路径的正确发布；它们限制未来依赖读数，不构成新的经验阴性。若无法建立这些必需事实，就报告该测量的准确缺口，而非加载别的模型或引用旧 full-run 作为替代。

缺少 tuned generic renewal-host headroom 仍是缺少，不能当成零或失败，也不是此项控制重入的独立准入门槛。旧大行 public reference .890275 和所选旧回报 .455985311 是不同历史数量，其差不是已测 H 增益，也不是新的已调优 headroom。G 的能力可以解释原生机会，不能证明 learned actor 的能力；H 的能力若被观察到，也只属于此选择和这些改变后的轨迹。（[P13，§5][p13]；[E3 / E4 完整结果][e3]；[E4 数值与 null 说明][e4]。）

本轮没有初始化模型、开始训练、执行环境 step、调用 optimizer.step、生成 evaluation episode 或进行 result-bearing invocation；这些新暴露均为零。P13 的零新暴露和旧 checkpoint 的历史暴露分开引用。本节点仅阅读规定证据并交付此答复，没有重新计算 AST、checkpoint hash、E3 配对数组或 E4 候选，也没有运行外部科学工具或安装依赖。

以下 18 个清单路径均通过 connected GitHub 在固定科学版本 **13b4677e44265a2aa62fe4c7ebecb6c9056d493e** 访问成功。表中给出实际采用的章节/源码窗口；导航读取时出现的邻接历史文字不构成本决定的新权限或科学依据。长源码只按本问题所需范围读取，不能把这份清单理解为整个仓库或所有运行依赖的独立复核。

| 实际访问的来源 | 本决定采用的范围 |
| --- | --- |
| [docs/research/candidates/flexible_skill_duration/FSD_P13_REENTRY_SOURCE_PREPARATION_20260907.md][p13] | §1–6；分两段读取，动作、artifact、状态限制、全部拟议计数/成本 |
| [docs/research/candidates/flexible_skill_duration/FSD_POST_E4_CONVERGENCE_INTAKE_20260905.md][post] | Final decision、Re-entry、P13 boundary；完整 intake |
| [docs/research/candidates/flexible_skill_duration/DIRECTION.md][direction] | L1–140；Accepted mechanism-level science、Post-E4 boundary、Position |
| [docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md][e3] | L1–195；配对、路径、原规则、暴露和成本 |
| [docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md][e4] | L1–111；完成状态、public null、数值边界和原规则；未重做候选普查 |
| [docs/Claude_docs/experiments/FSD_E3_LARGE_D2_SEED2_REMOTE_RUN_20260905.md][cell] | Terminal technical acceptance、checkpoint 表及其前置执行记录 |
| [hmasd/agent.py][agent] | L1559–1621、2114–2177、2330–2619、2857–3032、3087–3160、7143–7293、7346–7664 |
| [hmasd/networks.py][networks] | L1030–1110、1439–1465、1583–1595、1687–1693 |
| [envs/relay_corridor/host.py][host] | L266–405；score/renew/transition 与 observation feedback |
| [envs/relay_corridor/adapter.py][adapter] | L98–154；role decode 和独立 renew 输入 |
| [envs/relay_corridor/references.py][greedy] | L436–468；GreedyOnPublicState，不重新枚举 references |
| [scripts/run_flexible_skill_duration_e2.py][e2runner] | L165–172、456–508；pickle class、sync、eval mode、lane reset |
| [scripts/run_flexible_skill_duration_e3.py][e3runner] | L240–299；fresh-episode deterministic evaluator 与 episode 输出 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | L25–140、300 至文末的相关 §11；尤其 §11.8–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][engineering] | §4–5 和其普通研究更新；不采用邻接对象专用例外 |
| [AGENTS.md][agents] | decision ladder、standing delegation、focused reading、shared branch 和准入语义 |
| [docs/research/portfolio/handoffs/2026-09-07-p14-vsp02-code-and-direction-continuations.md][handoff] | 采用 P14-FSD-NATIVE-RENEWAL-CONVERGENCE-01；其他方向命令不用于本决定 |
| [docs/research/portfolio/PORTFOLIO.md][portfolio] | 当前 direction table 中 flexible_skill_duration 行：ACTIVE/HIGH 与既有最小暂停 |

**最终处置保持单一：有限继续这一个固定检查点的原生控制问题。** 它比旧“再有一个结构 gap 就继续”多了真实可操纵量和可改变决策的条件回报，也比“先穷尽所有原因才能学习”少了不必要负担。未选的普通学习分支不自动解冻；不新增同步技能干预、训练矩阵或 Portfolio 变更。访问层面没有阻止本节点作决定的缺口，未来 load/runtime/cost 未验证则作为未来测量的实际限制保留。

[p13]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/candidates/flexible_skill_duration/FSD_P13_REENTRY_SOURCE_PREPARATION_20260907.md
[post]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/candidates/flexible_skill_duration/FSD_POST_E4_CONVERGENCE_INTAKE_20260905.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[e3]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md
[e4]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md
[cell]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/Claude_docs/experiments/FSD_E3_LARGE_D2_SEED2_REMOTE_RUN_20260905.md
[agent]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/hmasd/agent.py
[networks]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/hmasd/networks.py
[host]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/envs/relay_corridor/host.py#L266-L405
[adapter]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/envs/relay_corridor/adapter.py#L98-L154
[greedy]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/envs/relay_corridor/references.py#L436-L468
[e2runner]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/scripts/run_flexible_skill_duration_e2.py
[e3runner]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/scripts/run_flexible_skill_duration_e3.py#L240-L299
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/AGENTS.md
[handoff]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/portfolio/handoffs/2026-09-07-p14-vsp02-code-and-direction-continuations.md#p14-fsd-native-renewal-convergence-01
[portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/13b4677e44265a2aa62fe4c7ebecb6c9056d493e/docs/research/portfolio/PORTFOLIO.md
