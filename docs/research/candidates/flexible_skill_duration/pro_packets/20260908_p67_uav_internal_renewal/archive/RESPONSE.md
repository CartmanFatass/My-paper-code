**选择 A：只开放 scenario1 上“固定团队时钟内的个体内部技能续约”这一有界 B/EXPLORE 对象族，并只选择一对新的 I／authentic D0 真实学习比较。** 接受提议的科学配置：六架固定 UAV、五十名用户、H500；两臂团队时钟均为 k10，个体上限均为10，I 的个体 gap cost=.25、团队 cost=+infinity，D0 两个 cost 均为+infinity。各训练五个16×500 rollout，之后各作一次32回合终点评价。完整调用上限保持 D0 3600秒、I 18000秒，合计21600秒；这些是所选问题的前瞻边界，不是已分配的运行或实测保证。（[本轮问题 intake，§2–4][question]；[机器工作量与成本记录][counts]。）

理由是：这一次可以直接问清楚一个不同且有实际用途的问题——**当固定时钟对照的 recurrent actor 已经逐步响应最新局部观察时，允许中央协调器在共同团队边界之间重新选择个体技能，是否仍对这个真实运动／服务任务的早期原生回报有增量价值。** D0 的反应能力使这个问题更严格，也使正、小、反向读数有不同意义；不能把 D0 想象成十步不看新观察、不改变速度的弱对照。源码证明了可干预的路径，不证明它有益。我愿意在明确可达六小时的完整调用总上限内购买这一次直接性能观察，不购买原因普查、更多旧 corridor 种子或一个没有边界的 UAV 研究计划。

**P52 的完整 A 决定和更早的 corridor 暂停都保留。** 旧 N6/K2 public-cue 家族不重开，已结束的 supplied-public-mask extension 不重开；这里没有 H 的继续训练或迁移。此次按现有 D2 内部门限机制的一个明确新对象族开放处理，**不作为对旧 H 机制的 RECAST**：不新建 termination head、价值信号或 credit 算法，而是把所问人口、实际干预位置和比较器限定到下述不同问题。它不是旧家族里的常规续跑，也不撤销旧停止或其他 recast 记录。Portfolio 生命周期、优先级、容量不变；本答案不登记正式 UAV 进入，不分配源码实现或科学调用。（[P52 完整答复，§一、§四、§六–七][previous]；[DIRECTION，Post-E4、Post-B03 boundaries][direction]；[P67 resume 的 FSD 行][resume]。）

## 一、为什么这次有一个值得问的边际问题

P52 停止的是已获得 component 和 fixed-clock 读数的公开规则控制包，并明确没有预约另一个内部技能／UAV 对象。当前提议不是增加该包的种子覆盖：它去掉 corridor 的 public regional-change flag 和 physical lease-renewal actuator，改为真实改变个体技能的内部重决策。普通 latent 数量为 team/individual 6/6，而非 corridor 的 n_z=2；native action 是连续运动，不是离散 role 加 lease mask。这个区别改变了研究问题，不能靠给旧 H 换一个 host 名字实现。（[P52，§六][previous]；[问题 intake，§2–3][question]；[config，L130–180][config]。）

直接读取的 `HMASDAgent._batched_assign_skills_d2` 显示：非 reset 步先以 held skills 计算 logit gap；团队 gap 或 cap 会触发全体重决策，否则个体 gap/cap 决定 sampled subset。`step` 先分配技能，再调用 primitive actor。普通 actor 每步输入当前 observation、当前个体 skill 和自己的 GRU hidden state；读取的路径仅在环境完成时清空相应 hidden state，并非每次技能续约都清空。（[agent，L2330–2540、L2897–2980、L3042–3133][agent]。）

由此得到的**可检验推断**是：在团队 token 保持的十步区间内，个体技能可能需要重新结合当前多机服务几何；仅靠固定 skill 下的局部 actor 反应也可能已经足够。前者若在真实训练后带来回报差异，会给这条内部控制路径提供此前没有的本机型模拟任务证据；后者若产生小或反向读数，会削弱继续采用这个 .25 个体门限配置的理由。无需首先定位每项因果贡献，也无需把“有源码”升级为“有收益”。

反对开放的最强理由是：D0 已经保留逐步观察、连续动作和记忆，新增 gap 可能只是增加离散技能扰动、样本分布变化及更新成本；旧 E3 对 competent fixed clock 的亏损让这种担忧有实质依据。这个反对意见不能由已有 corridor 正结果消除。仍选择 A，是因为这里第一次把“额外个体内部重决策是否有用”放在不冻结 primitive actor 的同信息对照上直接观察，且团队更新时钟保持不变。它能改变是否继续把此具体内部-renewal 配置作为 native UAV 性能候选，而不只是证明一个给定公开规则可提高 lease service。（[问题 intake，§2、§5][question]；[P52，§二–三][previous]。）

我对正回报只有低信心，不给出未经测量的提升幅度。相比维持无后继，这一次有限的真实比较有足够的信息价值；相比重复旧面板，它回答不同的实际 action/learning 问题。这个选择不是由研究恢复指令或长期 UAV 目标自动推出的。

## 二、唯一所选 B 的人口、处理与最强合法对照

保持现有 `UAVBaseStationEnv` scenario1：固定六架 UAV、五十名用户，uniform reset、free-space channel，episode/rollout H500；其余 host 参数沿现有构造，包括原 coverage/quality/altitude reward，不改变连接分配规则。UAV 与用户在回合内的实体集合固定；没有 join/leave、replacement、身份重用或 survivor-state 问题。user reset 随机性与训练中的同伴共同适应分别保留，不把后者当作可强制相同的外生轨迹。（[E0 runner，_make_envs][e0runner]；[scenario1，constructor、_compute_reward][scenario]；[问题 intake，§2–3][question]。）

| 条目 | I：个体 gap 续约 | authentic D0：固定技能时钟 |
| --- | --- | --- |
| 实际 learner | 原 HMASD coordinator、recurrent actor/critic、discriminators | 同一学习栈 |
| 内部模式 | `d2` | `d2`，不是 `off` 的替代比较 |
| 个体／团队成本 | .25／numeric +infinity | numeric +infinity／+infinity |
| 个体／团队 caps | 10／10 | 10／10 |
| 团队决策 | 正常 reset 与每十步共同边界 | 相同时间边界 |
| 区间内个体决策 | 现有 gap/cap 选择真实 sampled subset | 不发生 finite-gap 决策，按真实内部固定时钟执行 |
| primitive actor | 每步当前局部观察、当前 skill 与本臂 GRU memory | 同样逐步反应并保留本臂 memory |
| 其他配置 | n_Z=6、n_z=6、k=10、interruption_delta=1、age off | 相同 |

保留普通配置的网络、原训练 reward、损失及 optimizer schedules；已查 literal 为 gamma=.99、GAE lambda=.95、PPO epochs=15。保持原 FP32 learner、既有环境数组／回报精度及 CPU 四线程，不顺带更改 normalizer 开关、intrinsic 项、precision、通信或观测结构。（[config，L130–180][config]；[E0 runner，_make_config][e0runner]；[counts，source_config_literals][counts]。）

“团队时钟相同”只意味着决策时刻相同，不意味着两臂选出的 team token 相同。I 的区间内重决策可以涉及零个、一个或多个 UAV，也可以重新选中原 skill；sampled decision 数与实际 token switch 数不能混用。团队边界仍会正常重决策全体。不得为制造处理强度强制 I 发生 gap、强制换 token，或把没有额外 gap 的有效读数作废。（[agent，L2330–2620][agent]。）

**D0 是这个边际问题最强的直接同学习栈、同信息固定时钟 null，不是已证明的最强 UAV 算法。** 它既有每步可更新的 primitive action，也有 GRU memory；两臂协调器都拥有相同权限的中央 state/observation 输入。I 没有额外私有信息，其变化在于何时把当前协调信息转成新的个体 skill。D0 因此足以检验这一配置变化的总边际后果；但一个新五轮 D0 的实际 competence 尚未观察，不能由旧 E0 代为认证。

不增加 flat MAPPO、第二种 k、`off` 或 corridor G。已有 G 是另一 host 的公开 role/lease 规则，不是当前 scenario1 的现成 null；环境共同使用的连接分配规则也不是给 I 的监督或 oracle。缺少 tuned scenario1 generic headroom、MAPPO 性能或 fixed-k sweep，限制的是广泛算法排名，不阻止这一次 I/D0 配置比较。（[scenario1 baseline，Result first、Bound host、Missing][baseline]；[证据规范，§11.7–11.9][spec]。）

## 三、event → ownership → information → action/credit → native consequence

这里的 event 是自身和同伴运动造成的当前服务几何、连接和干扰变化，不是一个新注入的外生告警 bit。每个固定 UAV 身份持有自己的个体 skill 和运动输出；团队 skill 属于该环境的共同高层计划。actor 观察包含自身位置、有限数量的局部用户／UAV 相对位置与 SINR、当前时间；所有 agent 在每个 primitive step 都收到观察。中央协调器以两臂相同的信息权限处理当前 state、observations 与 held skill prefix。（[uav_env，step L265–351、observations L382–435][uav]；[agent，L2330–2540][agent]。）

在非团队边界，I 按现有 `max(logits)−held_logit >= .25` 规则选择个体 sampled subset；D0 保持当前 skill。这个 gap 不是原生回报优势估计，也没有证据证明它能识别有用的物理事件。partial assignment 更新真实 skill、采样 log probabilities、ages 和 decision metadata，随后本臂 recurrent actor 输出当前连续 movement action。环境把归一化动作换成速度，更新位置，再计算 channel/connections 和共同 native reward；新观察、真实 reward 与 authentic step metadata 进入本臂既有学习路径。（[agent，L2330–2620、L3042–3133][agent]；[uav_env，step][uav]；[scenario1，step L171–197][scenario]。）

同伴运动会改变其他 UAV 的可见局部几何和共享服务结果，同伴策略又在训练中更新，因此这是多智能体部分观察及共同适应下的内部控制问题，而非六个独立单机重复。相同时间尺度的动作与状态会各自演化；配对初始化和外生 schedules 不使内生 trajectories、随机抽样消耗、normalizer、技能或梯度相同。

I 不使用外接 public mask，不制造 sampled metadata，不把一个物理 renewal 事后伪装为模型决策。它沿现有真实 D2 内部 segment/discount/terminal/credit 语义学习，不新写 credit 同步算法。技能变化不额外清空 actor memory。完整 terminal transition 先按原语义存储，再用该 lane 的 fresh reset observation/state 作为下一回合输入，并完成原环境结束的 RNN/skill reset。此处改变的 segment、数据和 optimizer exposure 是观察对象的一部分；不能为了“公平”事后匹配梯度次数而改写处理。（[问题 intake，§2–3][question]；[agent，ordinary action/step][agent]；[E0 runner，所述 batched route 与 Evaluator][e0runner]。）

采用相同团队边界减少了一个未请求的设计维度，但没有隔离唯一原因。即使 I 回报改善，也只支持此内部-renewal 学习控制包的观察效果，不能称为 timing causality、matched-compute superiority 或独立证明“学习造成了差值”。无零更新对照、训练/评价交叉干预或因果矩阵，因此明确放弃这些更强归因。

## 四、训练单位、终点和可改变的下一判断

选择一个新的 matched training pair。两臂分别初始化真实 learner，使用配对的新初始化和外生 reset schedules，各自采集五个16×500 rollout，即每臂40000 transitions、80个训练回合、五个 update stages。具体数值 training/evaluation keys 留给后续 prospective card；不选择旧 checkpoint，不复用旧成绩，不把已花费的 P47/P52 预算作为余额。

五轮是这个早期性能问题的有限训练预算，不是充分收敛承诺。相较单轮，它允许后续 rollout 经历先前真实更新的结果；不据此声称五轮一定足以显现任何机制，也不自动继承旧十轮或更大矩阵。保留所有五轮采集回报、各网络实际 optimizer 次数及首轮／最终 initialization-relative exposure。学习真实发生由 transitions、updates、evaluation 与可信输出共同支撑，参数位移本身不是 competence gate。（[counts，prospective_only][counts]；[证据规范，§5.2、§11.4、§11.8.2–3][spec]。）

只在第五次更新后各作一次32回合确定性评价，配对新的 evaluation exogenous schedules，并与训练 schedules 区分。每臂构造自己的 evaluator，同步自己的最终 active weights 和启用的 normalizers，`train(False)`、清理评价缓冲并重置评价 lane 的技能、timers、hidden state；构造、同步、reset、scoring 对训练 RNG 隔离。评价不做 optimizer.step，不更新 normalizer，也不继续训练。E0 的 separate-agent 设计支持这个隔离思路；新 I 的配置必须同时传到 learner 和 evaluator，不能只复制 weights 就声称评价了 I。（[E0 runner，Evaluator、_preserve_rng][e0runner]。）

### 原生主量：只换报告单位，不换训练奖励

scenario1 的每步团队目标为

`r_team = .7 * coverage + .3 * quality - altitude_penalty`。

原环境给每架 UAV `r_team/6`，adapter 又对 per-agent rewards 取均值，因此原 scalar 仍为 `r_team/6`。对完整500步评价回合 e，保留未经缩放的 adapter episode return `U[p,e]`，主报告采用

`J[p,e] = 6 * U[p,e] / 500`，`d[e] = J[I,e] - J[D0,e]`。

该常数只用于结果报告，不将训练 reward、value targets 或既有损失乘六。主量是包含 altitude cost 的 native mean team reward，不是覆盖率或无成本服务比例。（[scenario1，_compute_reward L80–125][scenario]；[uav_env，step][uav]；[env_adapter，L248–274][adapter]；[E0 runner，Evaluator.run][e0runner]。）

报告32个 paired d、均值、sample SD(ddof=1) 与 `sample_SD/sqrt(32)` 的条件 SE，同时保留每臂原始 episode return。它们只度量这一训练对的评价回合变化，不能估计 training-seed population uncertainty；训练 episodes、五轮 update stages、两次模型构造也不是额外独立训练。未来可直接复用已有逐回合数组和 NumPy 配对统计，不需要 bootstrap 服务、全轨迹 census 或更大评价面板。

采用 **MEI=.01 absolute native mean team reward**。它是在同一 weighted service/quality/altitude 尺度上的一个百分点，等于500步回合的5个 team-reward points，或5/6个 adapter-return points；不是相对弱 baseline 的百分比，也不等同于覆盖率恰好提高一个百分点。（[counts，native_reward_scale][counts]。）

| 新的完整可信 mean I−D0 | 这一观察能改变的研究判断 | 必须保留的限制 |
| --- | --- | --- |
| > +.01 | 首次取得该 native UAV 内部-renewal 配置在这一个训练对的局部增益；可以作为以后另行选择重复性或改进问题的候选依据 | 不声称最优固定时钟、learned termination、稳定优势、唯一因果或 H 迁移 |
| inclusive [−.01,+.01] | 在本次预算下没有较大边际差值或分辨率有限；不因旧 corridor 正值而延长这个配置 | 不是等价／无效定理，不追加回合或换 seed 求更清楚的符号 |
| < −.01 | 得到该配置在这次真实训练预算下的相反性能观察，削弱继续使用它的理由；保留 D0 的相对表现 | 不关闭所有门限、训练种子或整个 FSD，也不改写旧观察 |

三种情况均完整报告两臂回报、原有 reward components、实际 individual/team renewal 与 token-switch、segment/optimizer exposure和全部不利结果，完成一次 intake 后停止，无自动 successor。报告现成 coverage、quality、altitude components 是为了识别回报构成，不增加以其他分量选优的主量。若额外个体 gap 没有发生，那是配置在此观察中的活动事实，不是触发新门槛或强迫加大处理的理由。

这个 discriminator 改变的是“在这条已经明确的 native action path 上，是否有理由继续考虑此个体-renewal 配置”的证据，而不是要求一次 B 完成 publication-level 比较。一个正值有用但不无限兑换算力；一个小或负值也可以给出有用的有限结论。（[证据规范，§11.7–11.9][spec]。）

## 五、工作量与成本：接受可见的上限，不把 stress scenario 当保证

主导工作不是搜索，而是两套真实的 collection/update 与唯一 final evaluation，以及数据依赖的高层重决策和 segment 工作。

| 量 | 本次选择的前瞻范围 |
| --- | --- |
| 训练 | 2 arms ×1 pair ×5 rollouts ×16 lanes ×500 =80000 transitions；160 train episodes；10 update stages |
| 评价 | 2 arms ×32 episodes ×500 =32000 scoring steps；64 endpoints |
| 总体 | 112000 environment steps；672000 agent-step observations |
| 模型／控制调用 | 4 model constructions；2 training starts；0旧 checkpoint loads；6000 learned batch control calls |
| D0 每 rollout | 800 joint boundary rows；4800 individual decision rows |
| I 每 rollout | 团队 rows 仍800；joint rows 最多8000、individual rows 最多48000；实际值未知 |
| 额外工作 | 无 nested candidate/trajectory/solver search；无额外科学 validation panel |

上表来自已提供的机器算术，不是本咨询运行。update stage、joint row、individual row 和 optimizer.step 是不同单位。两臂逐步 primitive actor 调用数量相同也不意味着梯度工作相同；I 的更早技能决策还可能改变数据、normalizer 曝露、内部 credit 和后续 minibatches。不得用最多十倍 rows 证明最多十倍 wall。（[counts，prospective_only][counts]；[agent，D2 assignment 与 decision metadata][agent]。）

历史 local Windows CPU4 E0 D0 的225.2秒／rollout、十轮加两次各8回合评价的2392.4秒，只提供旧配置的工作锚。记录中的推算为

`1.15 * [5*225.2 + 2*(2392.4 - 10*225.2)] = 1617.82 s`；

`10 * 1617.82 = 16178.2 s` 是 I 的刻意宽松 stress scenario。

其中140.4秒余量混合了旧非-rollout 工作，不能当作纯评价每回合成本；把全部工作乘十也不能精确表示初始化、环境循环、actor 与高层更新各自如何缩放。它没有测量新 remote node、batch32 evaluator 或 I 的实际更新负载。原 E0 的225.2秒事实和未来算术情景必须分别引用。（[E0 result，§2–4][e0result]；[counts，cost][counts]。）

| 臂 | 现有前瞻情景，非实测新成本 | 接受的完整 invocation cap |
| --- | ---: | ---: |
| authentic D0 k10 | 1617.82秒，旧工作尺度 | 3600秒 |
| I | 16178.2秒，十倍整项工作 stress scenario | 18000秒 |
| 两臂合计 | 不给出新运行预测 | 21600秒，即六小时 summed invocation cap |

**这并不廉价。** 我接受这些上限，是愿意为第一次区分“固定 skill 的反应 actor 已足够”与“额外个体内部决策仍有 native package 价值”承担最多这一有限投入，而不是因为 finite、零咨询 learner 或单 seed 就应便宜。它只有两个必要 learned arms、一个最终 endpoint，不扩维度；团队 cost 固定无穷，避免同时购买团队 gap 和个体 gap 两个问题。相比又一个旧 corridor pair，这里的信息改变了所评价的原生控制命题。若不愿承担这个上限，应明确不分配本对象，而不是先创建额外 A 或 profiling 任务。当前方向选择本身不占用或保证这六小时。

不以 stress 值小于 cap 作为已经通过的资源或时长证明，也不引入通用 overhead 倍数门槛。未知的新实际 wall、segment 与 optimizer 工作保持未知。五轮和32回合在两臂保留共同科学预算；较高 I wall cap 是允许算法工作不同的边界，不是 matched-compute 设计。

每臂完整 cap 从必要准入及 interpreter/import、config/model/optimizer 创建开始，包含全部学习、独立 evaluator 创建和同步、终点评价、primary paired readout 与 closed-file publication。不得先在别的任务初始化模型再开始计时，不把评价或 publication移到 cap 外，不拆片、重启、借另一臂未用时间或挪用旧 P52/P47 额度。后续若被明确分配，沿现有 remote-first CPU4、原数值语义、fresh on-node resource admission 和 detached exact committed source 执行；硬件不是效应的人口变量。（[本次 TASK，Requested decision][task]；[AGENTS，§5–6][agents]。）

完成五轮、唯一终点和必要发布即停止。触及完整 cap、真实动作／损失／参数／主回报非有限，或出现损害 reward、信息权限、实际更新或 primary comparison 的具体错误时，停止相应依赖工作并保留已完成事实。配置中有意采用的 numeric +infinity 成本不能误作损坏数据；也不能用字符串元数据代替真实运行配置。无自动 retry、降轮拼成完整对象、替换 seed 或 cap 增加。一个臂的可信读数可独立保留，但缺少任一完整可信臂就不能给完整 I−D0 极性；有效负面或弱学习不是 quarantine 理由。可选资源遥测与 primary 的依赖分别说明。（[证据规范，§4、§11.8.6–7][spec]。）

## 六、必须携带的反证、文献限制与实际实现缺口

B03 的 H−D0 **+.3928645833333336**、条件 episode SE **.009650752471672294** 和 G−H **+.1152864583333331** 同时保留；H 的8662/68220 wrong/eligible，以及 D0/H actor、critic 各18000/2250次、coordinator750/870次更新，都不能被新提议抹去。D0 弱但有效。B01/B02 的 H−C +.4973828125/+.520390625 与 G−H +.0211848958/+.0108463542 是另外两个比较，不是更多 H/D0 pairs，更不是任何 I/D0 UAV 训练样本。（[P52 完整答复，§二–三][previous]；[DIRECTION，Accepted B03、Post-B03 boundary][direction]。）

E3 仍有六个 competent medium/large 负配对；small seed2 对 competent D0 的 +.033291585 和 E2 duration control 仍是有限支持。E4 的3-law/288-candidate、零 learner 公开 greedy 解释仍成立。这些材料降低了把 policy gap 视为有用事件检测器的信心，但不能单独决定新 UAV I/D0 的符号。反过来，给定公开 mask 的正回报也不能充当新内部续约的支持性实测；现阶段最强的正面理由是具体可区分的行动假设，而不是已有 native UAV 效果。（[previous，§三][previous]；[问题 intake，§5][question]。）

scenario1 E0 只证明 exposure/integrity 和旧成本。其回报排序被原 contract 明确禁止，本次不报告或利用这些分数选择强弱、不重新评价旧 checkpoints，也不把旧十轮 D0 当新五轮 D0。缺少 tuned scenario1 headroom 被如实保留。baseline 文件中旧 pilot、先 sweep 等建议不成为当前 §11.8 之外的条件；这里没有要求一个 flat MAPPO adapter 或新的 baseline assembly。（[baseline，Result first、Missing、Cost][baseline]；[E0 result，开头与§2–4][e0result]；[spec，§11.4、§11.7–11.9][spec]。）

本节点只使用问题 intake 所记录的 ACAC 选定 passage summary：PDF pp2–3、所列 JSON elements 对 intra-option reaction、termination 和决策时可用观察的区分。没有另取本地 PDF、外网论文或全库索引，不声称完成独立文献复核或新颖性检索。已读 UAV 源码每步更新所有 agent 的观察，**不是** ACAC 的稀疏异步 macro-observation／padding 问题；局部 user/UAV observation 槽位的固定大小也不能因此叫作同一个异步问题。不能导入 ACAC 的性能结论或架构来为本对象辩护。（[问题 intake，§5][question]；[uav_env，step、observations][uav]。）

尚缺的不是这个问题的科学定义，而是其后续明确实现和实测：E0 的 CLI 只接受 off/d0，`_make_config` 的非 off 分支构造 infinite-cost D0，`Evaluator` 再调用它。因而只新增一个 I 名称、或仅给训练 learner 改 cost，而沿用 D0 evaluator，都没有实现本题。需要让两套真实配置贯穿 learner、内部决策/存储、独立 evaluator 和主量发布；现有源码可复用，不等于新的有限成本 I runner 已交付或可直接运行。（[E0 runner，_make_config、Evaluator、main][e0runner]。）

后续验证只服务这个真正改变的配置→内部 sampled decisions→actor action／实际 learning records、终点 reward scale 与 primary 输出；不复刻 E0 全部 probes、bit equality、旧 checkpoint replay 或历史错误诊断。对未变路径复用已有可信证据。内部 gap/cap、团队边界和采样后仍同 token 的区分要能读懂，但不要求先有 useful gap、完整因果解释或所有 seeds 为正。当前没有额外 guard、registry、profile、resume 服务或科学 validation panel 的选择。（[spec，§11.8.1、§11.8.6–9][spec]。）

## 七、访问、最终范围与给主人的建议

本次科学读取均通过 connected GitHub connector 使用固定输入 `de9af8f93d311426f2af069b1a0039765cdeef93`，TASK 使用其指定的单独固定版本。以下十五个清单路径实际已读；长文件仅按相关范围读取，不是整个算法或依赖树的审核。没有用旧上传 packet 代替新 TASK，也没有运行代码来验证任何科学数字。

| 实际读取路径 | 本次使用范围 |
| --- | --- |
| [docs/research/portfolio/handoffs/2026-09-08-research-resume.md][resume] | P67 当前恢复边界、FSD 行和新分配规则 |
| [FSD_P67_UAV_INTERNAL_RENEWAL_QUESTION_INTAKE_20260908.md][question] | §1–7，特别是新路径、null、成本、文献界限 |
| [pro_packets/20260908_p67_uav_internal_renewal/EXPOSURE_AND_COST.json][counts] | 全文零暴露、counts、历史算术情景 |
| [pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md][previous] | 完整 P52 A、有效正反证与无后继边界 |
| [DIRECTION.md][direction] | Post-E4、Accepted B03、Post-B03；定位读取的相邻旧边界只作历史 |
| [hmasd/agent.py][agent] | L2330–2540、2897–2980、3042–3133；为核对真实 token/age/metadata 更新扩至2541–2622 |
| [scripts/run_flexible_skill_duration_e0.py][e0runner] | _make_config、_make_envs、Evaluator、main；定位范围的 RNG/exposure helpers |
| [configs/config_1.py][config] | L120–190，普通6/6、PPO及 interruption fields |
| [envs/pettingzoo/uav_env.py][uav] | L265–351、382–435，motion、reward、每步局部观察 |
| [envs/pettingzoo/scenario1.py][scenario] | L14–125、171–197；另一个越过文件末尾的定位读取返回空，并非源不可访问 |
| [envs/pettingzoo/env_adapter.py][adapter] | L248–274，原 reward scalar |
| [docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md][baseline] | exposure-only、bound host、missing/headroom及旧建议边界 |
| [docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_RESULT_20260902.md][e0result] | §2–4 和定位时相邻开头，旧时长／配置与禁止排名 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §4、§5.2、§11.4、§11.7–11.9及相关解释 |
| [AGENTS.md][agents] | §1–2、§4–6，当前 Root/Portfolio 职责、层级与共享 branch |

另读取了指定 Issue10 正文和四条既有交付评论，包含 [P52 的完整交付评论](https://github.com/CartmanFatass/My-paper-code/issues/10#issuecomment-5590454095)。它们是历史交付而非当前 scientific allowance。可选 `ISSUE_SNAPSHOT.json` 未再读取，因为当前讨论已直接读取且 P52 完整文件已核对；不声称读取该快照。所有本题需要的已列科学路径访问成功。

当前 consultation 的 scientific invocations、model constructions、checkpoint loads、training starts/transitions、optimizer steps、evaluation episodes、simulation steps、profiling、checkpoint replay 和 scientific validation invocations 都为零。上文训练与成本是前瞻定义，旧观测来自材料，未产生新 UAV 结果。scope 仅此研究回复与交付评论，不修改 card、CM spec、source、DIRECTION、audit 或 Portfolio。（[counts，current_consultation][counts]。）

当前 Root 同时承担 Portfolio 职责，完整答复交给原 DM 做既有 intake，再由 Root 在现有权限下提供后续明确分配；不恢复旧独立 Portfolio 会话依赖，也不新增逐阶段批准。本决定只明确选择这一个新对象族和一个有界 B，不声称已完成实现、正式 UAV 进入或开始执行。（[AGENTS，§1–2、§4–6][agents]；[P67 resume][resume]。）

**给主人的建议：接受这一次 native I/D0 边际比较，而不是恢复旧 corridor。** 值得了解的是，已有反应 actor 之外的个体内部技能重选是否还有回报价值；目前对此没有 UAV 性能证据，旧 competent negatives 和 reactive D0 使正值信心偏低。保留五轮、一个训练对、唯一32回合终点及 D0/I 3600/18000秒完整上限，接受最多六小时的有限信息成本，任何正、小、负或不完整结果都如实结束 intake，无自动扩展。P52 的结束、普通 corridor 暂停和全部历史证据继续有效。

[question]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/candidates/flexible_skill_duration/FSD_P67_UAV_INTERNAL_RENEWAL_QUESTION_INTAKE_20260908.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_p67_uav_internal_renewal/EXPOSURE_AND_COST.json
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[resume]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/portfolio/handoffs/2026-09-08-research-resume.md
[agent]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/hmasd/agent.py
[config]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/configs/config_1.py
[e0runner]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/scripts/run_flexible_skill_duration_e0.py
[uav]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/envs/pettingzoo/uav_env.py
[scenario]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/envs/pettingzoo/scenario1.py
[adapter]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/envs/pettingzoo/env_adapter.py
[baseline]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md
[e0result]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_RESULT_20260902.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/de9af8f93d311426f2af069b1a0039765cdeef93/AGENTS.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/1c9440abdf136250fa614d9e006ae66732755f0f/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_p67_uav_internal_renewal/TASK.md
