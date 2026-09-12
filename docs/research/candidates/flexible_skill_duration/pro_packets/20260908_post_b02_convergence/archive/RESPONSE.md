**选择 B：只开放一次全新、同训练预算的 H／fair D0 k=5 比较，并保留公开信息 G。** 两个 learner 各训练五个 rollout、每个 rollout 十六个环境与四百步，各作一次三十二回合终点评价；G 使用同一组三十二个评价外生 keys。完整调用上限保持 D0／H／G 分别为 1200／900／60 秒，合计 2160 秒。不加入 C、第三个相同 C/H pair、调参网格、因果面板或新 host。

理由不是“两次为正，所以应继续”，而是：**B01/B02 已回答混合控制包相对内部 D2 控制的早期学习与再次出现问题，却仍未回答它相对实际固定时钟学习构造的同期性能问题。** C 的比较地位较弱，正是这两个大收益不能直接支持下一层性能判断的原因。这里愿意购买的是一个改变比较器、能够改变继续评价该混合控制包理由的有限读数，而不是再增加同一 C/H 问题的种子覆盖，也不是借一个玩具排名证明 UAV 迁移。（[B02 intake，§2–3、§6][b02intake]；[P44，§2–3][p44]。）

这一选择只延续**原 N6/K2 大 Bernoulli corridor 上，固定公开 applied-renewal 规则与现有内部 D2/actor/credit 组合的有限学习扩展**。普通 fixed-K2 policy-gap 学习家族的暂停不整体解除；其他阈值、同步 termination/credit 改造、其他 host、UAV 和 C 类对象均未开放。整体 ACTIVE/HIGH、Portfolio 生命周期、优先级与容量不变。新的 card、数值 keys、实现 source 与实际运行分配仍由后续明确任务给出；本次没有分配或执行科学调用。（[DIRECTION，Post-native-control learning boundary、Accepted independent-pair recurrence][direction]；[本次 handoff，Question/bounds、Return/stop][handoff]。）

## 一、为什么这次不采用结束扩展的建议

DM 对停止重复 C/H 的判断成立：两个已完成对象各自有清楚的比较意义，一个第三相同 pair 主要增加种子频率与变异信息，不能把给定规则变成 learned renewal。本节点不选择这种重复。B02 的原停止边界也保持，新的 H/D0 比较不是它的自动续跑。（[P44，§2–3][p44]；[B02 intake，§6][b02intake]。）

但 H/D0 不是 C/H 的另一次相同排名。它能区分两个目前都与已知结果相容的判断：混合控制包的优势只相对较弱的内部 D2 构造成立；或者，在相同早期训练预算下，它对历史上已有能力依据的固定时钟构造也有局部性能价值。前一种结果会削弱把 C/H 大差距当作继续这一扩展的依据；后一种结果则为一个明确的固定时钟比较留下新的、仍然有限的支持。**这个区别本身有方向内决策价值，不需要先解决全部原因或证明 UAV 可迁移。**

结束扩展的最强理由仍然是：公开规则已经解释主要原生机会，G 又在两组领先，即使 H 胜 D0，也未必值得把它发展为新的时长学习方法。我接受这个限制，不把本次比较包装为创新性、learned termination 或迁移论证。仍选择 B，是因为现在直接结束会把“弱 component control 之外的实际学习比较”留成未回答的、可由所给单一有限设计区分的问题。这里不要求先赢 G，也不因缺少 tuned headroom 而停；反过来，正值也不会自动兑换更多实验。（[P44，§3][p44]；[证据规范，§11.8.1–4、§11.9][spec]。）

因此，我与 DM 的分歧是**是否值得购买这一次具体性能比较**，不是否认其 UAV 接口分析。这个比较只能支持它实际观察的训练对。不能把一个正 H/D0 结果设为未来任何 B 或 UAV 问题的普遍前置条件；同样不能因为它不回答 UAV 问题，就把其本来的 B 性能目的替换成未请求的迁移负担。

上轮完整答复的第二节已明确：当问题从 component 比较转为固定时钟性能比较时，需要另行选择同预算 D0，不能借用旧分数。本次正是作出这个新选择，不是补写上轮未形成的决定。该完整答复及对应交付评论与历史短 blocker 并存，不能因短 blocker 而否认已经接受的上轮决定。（[上轮完整答复，§二、§五、§八][previous]；[本轮固定 Issue 快照][snapshot]。）

## 二、两项新的支持与所有反面量都保留

B01 和 B02 分别是有效完成的 B/EXPLORE。它们保留各自原卡的 above-MEI 读法与停止边界，不合并成一个新的结果规则。

| 已完成训练对 | 训练／评价 masters | full H−C | 条件回合 SE | post-reset H−C | full／post G−H |
| --- | --- | ---: | ---: | ---: | --- |
| B01 | 770203／770204 | +0.49738281249999894 | 0.00864640484198601 | +0.49862938596491124 | +0.021184895833334313／+0.0187317251461998 |
| B02 | 770303／770304 | +0.5203906250000002 | 0.007576080882164499 | +0.5216948621553887 | +0.01084635416666652／+0.008367272347535353 |

这是两行分别报告的观察，不是把 64 个评价回合当作独立训练种子，也不是加权合并的效应估计。每行的 SE 条件于该训练对；两组各自所有三十二个 H−C 回合为正只是观察，不是接受要求。B02 的数值较大、G gap 较小，也不是一个受控的前后学习改进估计。（[B01 result，Direct native-return observations][b01]；[B02 result，Direct native observations、B01 and B02 remain separate training-pair rows][b02]。）

**最强支持：**大幅原生收益经历了真实从头初始化、各自轨迹采集、存储、更新及 fresh endpoint evaluation，并在另一个独立训练对再次出现；移除 reset 步后仍存在。这已超过旧 selected-checkpoint A01 能回答的内容，却不单独证明差异由学习更新造成，更不证明公开规则被学会。

**最强当前反证：**C 不是新预算下已经合格的固定时钟性能 baseline，G 在两组仍然领先。B02 post G−H 小于 .01 也不是与 G 等价：.01 原来用于 H−C 的解释，不能移作 G/H 等价阈值。H 仍有真实 wrong-role 服务损失，必须和收益并列。

| 对象／策略 | KEEP 且 lease-fresh 机会数 | 其中 wrong-role 数 | 自身机会上的错误率 | post-reset 回报单位角色损失 |
| --- | ---: | ---: | ---: | ---: |
| B01 C | 32555 | 3738 | 0.114821072032 | 0.048793859649 |
| B01 H | 68451 | 1435 | 0.020963901185 | 0.018731725146 |
| B02 C | 34598 | 6904 | 0.199549106885 | 0.090121136174 |
| B02 H | 68301 | 641 | 0.009384928478 | 0.008367272348 |

这些分母是不同策略自己的机会集，不能把条件率差当作固定共同人群上的 actor 因果效应。B02 的回报核算同时出现更多 eligible KEEP 机会和更少错误原生输出；它说明奖励从哪些已实现计数构成，不分配公开规则、数据分布、recurrence、优化暴露或 actor 能力的因果份额。G 绕过 learned actor，其正确角色不证明 H 的完整能力。（[B01 result，Own-opportunity role loss][b01]；[B02 result，Own opportunities, wrong-role loss and physical renewal][b02]。）

每项 B 都有 64000 training transitions、160 training episodes、10 update stages、96 endpoint episodes 和 38400 scoring steps。B01 的实际 optimizer calls 合计 10860，B02 为 10740；coordinator 的 C/H 计数分别为 615/495 与 510/480。两个对象各臂 actor/critic 各 2250、team 75、individual discriminator 300。首轮和最终相对初始化位移均有记录，表明真实更新发生，不认证学习充分或收敛。相同 schedule 并不等于相同实际优化工作。（[B01 result，Actual learning][b01]；[B02 result，Actual learning][b02]。）

历史反证不被 hybrid 的结果翻案。E3 仍是 18/18 有效 B；medium 三个 competent G 分别为 −.016412598、−.039020020、−.053367188，large 三个为 −.071387329、−.108895874、−.086455282。尤其 large seed2 原累计 event path 为真，仍亏损。原 H0 只关闭 c=c_Z=.25 在声明大行、20 rollouts／128000 transitions 每臂下的声明；累计与 final 路径窗口保留原区别。small seed1 的 −.041736165、small seed2 对 competent D0 的 +.033291585，以及 small seed3 的 +.062728760 都保留；最后一项对应 D0 ratio .814254153，不能支持 superiority。E2 保留单调 duration control 与原 NEITHER，不变成已确认的事件驱动机制。（[E3 result，Paired final returns、Regional event path、Frozen rule][e3]；[DIRECTION，Accepted mechanism-level science][direction]。）

E4 保留 3 laws／288 candidates／零 learner 的完整 A，公开 greedy 解释 switching-reference 结构机会；它不是 learned headroom，也不是整个 learned-policy class 的无价值定理。此次仍在原大 Bernoulli 行，不迁入 E4 的新 renewal-law 人口。Tuned same-information generic headroom 仍缺失，不能写成零、失败或必须先补齐的门槛。（[E4 result，Population, strongest null][e4]；[证据规范，§11.7–11.8][spec]。）

## 三、只选择这个 H／真正 fair D0／G 问题

### 人口、信息与真实 learner

保持 N=6、每 region 三个固定实体、K=2、四个 host zones／两个 regions、H=400、Bernoulli hazards=(.02,.20)、Delta=1、rho=0，无 probe/churn/coupling。模型仍是 n_Z=6、n_z=2、连续 action_dim=2；四个 zone 不等于四个 team token。两臂都是现有 HMASD 全学习栈的新初始化，保留 recurrent actor/critic、coordinator 和 discriminator、既有损失和 optimizer schedule、CPU 四线程、float32 learner 与 float64 host/reward 语义；observation/state normalization 仍 off，各自使用自己的 ValueNorm。不加 shaping reward、G 角色监督、私有 latent 或新网络。（[B02 result，Population, packages and independent unit][b02]；[现有 learning runner，build_learner、collect_training][learning]。）

| 策略 | 内部决策构造 | 实际送入环境的 renewal | 比较地位 |
| --- | --- | --- | --- |
| H | D2 c=c_Z=.25，individual/team caps=40/400，age off | t>0 为实体所属 region 的公开 change flag；t0 保留内部 forced reset | 含固定公开执行规则的 trained hybrid |
| fair D0 k5 | 同一 D2 实现路径，c=c_Z=infinity，individual/team caps 均为 5，age off | 真实应用本臂自己的 sampled mask | 新同期固定时钟 trained comparator |
| G | 不构造、不加载 learner，沿自己的 public plan/state 使用既有 GreedyOnPublicState | 保留既有公开 cue/flag/zone 所决定的 role 和续约，包括初始不续约约定 | 最强合法同信息 operational null，不是受相同训练预算训练的 baseline |

D0 的定义由现有 E3 `arm_parameters` 支持。**只把外部 applied mask 换成 k5、内部仍运行有限成本 D2 的控制器，不是本次 D0。** 历史 large D0 seed2 的二十轮能力是选择这个可信比较器构造的依据，不是新五轮下已获 competence 的证明；旧 128000-transition 分数绝不替代新 32000-transition D0 的实际结果。（[E3 runner，arm_parameters][e3runner]；[旧 D0 result，Question、Work][d0history]。）

配对只限初始化和外生随机性：两个 learner 分别经历自己的 action、host state、hidden state、normalizer、reward、buffer 和 updates。新的数值训练／评价 keys 在后续任务中明确，不在本次指定；不复用旧 outcome-selected checkpoint，也不以同样 keys 强制两个内生轨迹一致。

### 原生后果与内部 credit 不能混写

实际链是：**外生区域事件使固定实体的 lease 失效 → 公开信息与本臂 observation/state → 内部技能决策及 actor 的当前连续输出 → actor role 与本臂 applied renewal 进入 host → setup outage、lease freshness 和正确角色共同形成 native service reward → 真实下一状态与奖励存入本臂 learning records → 按本臂内部 segment/credit 更新 → 下一轮继续采集自己的轨迹。**

H 的公开物理续约不回写成“模型采样了这个 mask”，不重置内部技能或 hidden state，也不伪造 log probability、计时器与 decision metadata。D0 则真正改变内部时钟并应用相应 mask。因此 H/D0 比较有意同时包含内部节奏、实际数据与优化暴露的差异；它不是只改变一个 actuator 的净因果效应，更不是 synchronized D2 interruption。这里让步的是纯 timing、唯一 mediator 和学习规则正确性的更强归因，不是让步真实学习或公平的信息/环境预算。（[learning runner，applied_mask、collect_training][learning]；[E3 runner，arm_parameters][e3runner]。）

每次实际 terminal 先存真实 terminal transition，再采用本臂 reset 后的 observation/state，并重置该臂相应 lane 的 RNN/skill 状态；不把上一回合 terminal state 当新回合输入。终点评价使用独立 fresh evaluator，同步自己的最终权重与启用的 normalizer，保留 RNG 隔离、train(False)、clear/reset 与 deterministic action；不作 optimizer update、旧 checkpoint 恢复或中途 checkpoint 选择。G 只 reset 自己的 host/plan。这些状态处理已有相应学习与评价路径；新 D0 分支的实际连接仍需后续明确实现与受影响边界检查，不由本次源码读取宣布已可运行。（[learning runner，collect_training、evaluate、final_evaluation][learning]。）

## 四、一次训练对、一个主量与原样的解释尺度

两臂各收集五次 16×400 的真实训练 rollout，共 64000 training transitions。只在第五次更新后的固定终点，各评价 32 个 fresh 外生回合；G 使用匹配的 32 个 keys。此处五轮是所选有限早期性能问题的预算，不是充分训练或收敛承诺；不降为单轮，也不默认加回旧二十轮。不得加入 C、另一个训练 seed、调参选择或额外中间评价。

对评价回合 e，主量定义为：

- `R[p,e] = sum(t=0..399) native_reward[p,e,t] / 400`；
- `d[e] = R[H,e] - R[D0,e]`；主报告为 32 个 d 的均值、各回合值与 spread，条件 SE 为 `sample_sd(d,ddof=1)/sqrt(32)`。

这一个新训练对不能估计训练种子总体不确定性。不得和 B01/B02 的 C/H 回合池化，后者比较器不同；不得把新 D0 的旧历史 seed 计作同期重复。

同时保留 `/399` 的 post-reset 回报与 H−D0、G−H、G−D0，两个 trained arms 各自的 roles、eligible KEEP/fresh、wrong-role 次数、条件率、reward-unit loss，以及 internal/applied renew 数。零 eligible 时率记 NA，不冒称零错误。H 与 D0 的 forced reset 约定一致；G 的初始不续约有已知 Delta/H=.0025 的 full 尺度差，不应记作 duration 收益。对 G−D0，可能同时存在错角色与过期 lease 等短缺，不能把它强行等同于 wrong-role loss。实际服务核算用于限定解释，不引入严格等式 gate。（[B01/B02 result 的 independent unit、own opportunities][b01][b02]；[learning runner，evaluate][learning]。）

采用指定的 **MEI=.01 absolute mean native reward**：在 Delta=1 的同服务尺度上是一个百分点，避免弱 baseline 下相对百分比的失真。它是这次新比较的解释尺度，不改写任何旧分支，不是显著性、等价、最优性或普遍投资硬门槛。

| 新训练对的完整、可信 full H−D0 | 这一观察能够改变的判断 | 不允许的外推 |
| --- | --- | --- |
| > +.01 | 对这个固定时钟构造出现局部 hybrid 优势；现有支持不再仅来自较弱的 C，有限性能价值值得作为单独事实保留 | 不是纯续约效应、D2 学会 renewal、稳定 superiority、最优 fixed-clock 或 UAV 证据 |
| inclusive [−.01,+.01] | 该预算下差距小或分辨率有限；不以旧 C/H 大收益宣称已跨过固定时钟比较 | 不是等价、无效定理，也不追加回合或 seed 追求更清楚的正号 |
| < −.01 | 该训练对和预算下出现相反性能观察；削弱用旧 C/H 优势延长这个 package 的理由 | 不翻案 B01/B02，不关闭其他 seed、阈值或整个方向 |

每一行都保留所有 outcomes、G gaps 和实际 learner exposure，完成一次 intake 后停止，**无自动后继**。不要求所有回合为正。新 D0 若表现差，必须如实保留其 G 短缺和训练记录，使“优势”只针对实际学得的这个 D0；不另建 `.85` 之类继承自 E3 的新排除线，不选择性删掉不合意的 pair，也不以未调优为由隐去比较。技术损坏与可信但弱的学习表现是不同情况。（[固定 TASK，Requested decision][task]；[证据规范，§5.2、§11.7–11.9][spec]。）

## 五、工作量、完整成本与停止边界

以下是已提供的机器计算设计数，不是本咨询的新科学暴露：

| 工作 | 指定范围 |
| --- | --- |
| 训练 | 2 learners×1 fresh pair×5 rollouts×16 lanes×400＝64000 transitions；160 training episodes；10 update stages |
| 终点评价 | 3 policies×32 episodes×400＝38400 scoring steps；96 endpoint episodes |
| 总计 | 102400 host steps；614400 agent observations |
| 模型与调用 | 2 learners＋2独立 evaluators＝4 model constructions；4800 learned batch calls；400 G calls；0 old checkpoint loads |
| D0时钟计数 | 每 rollout 1280 lane clock boundaries；不是 optimizer calls |
| 额外搜索／验证面板 | 无 nested policy、joint-action、未来 trajectory 或 solver search；无新增科学验证面板 |

内部六实体 decode、逐步 actor/coordinator 调用及实际 optimizer 工作属于算法；新验证只服务真正改变的 D0 内部参数→sampled mask→实际 action/reward/storage 与主要配对输出，复用未变的可信路径，不重放旧历史或追加 smoke 矩阵。十个 update stages 不能代替 optimizer.step 计数。新 D0/H 的 segment、coordinator 与各网络更新次数仍未知，必须报告实际值和既有 exposure line，不强行匹配它们来改变这个 package 比较。（[EXPOSURE_AND_COST.json，alternative_minimal_real_B_not_allocated][counts]；[证据规范，§11.8.6、§11.9][spec]。）

| 完整策略调用 | 本次设计 cap | 已有成本依据及限制 |
| --- | ---: | --- |
| fair D0 k5 | 1200秒 | 旧150 coordinator optimizer calls/rollout代入历史式得到1051.6405秒；不是新实测或保证 |
| H | 900秒 | B01/B02完整H墙钟333.89／323.99秒；不是下一 seed 或新比较调用的已测成本 |
| G | 60秒 | B01/B02完整G墙钟2.47／2.56秒；保留新调用全部setup与publication成本 |
| 合计 | 2160秒 | summed invocation cap，不是可挪用旧预算或已分配机器时间 |

D0 的历史尺度为 `1.15×[5×(64.6+.769×150)+32×.46]=1051.6405` 秒。这里 150 是旧 coordinator optimizer workload；每轮 1280 个 raw lane boundaries 不能代入它。旧 remote D0 的 20 rollouts＋3584评价回合实际 runner 为2603.2776923269994秒，supervisor为2784秒，二者也不能简单按新transition数比例缩放为实测新成本。（[旧D0 result，Work、Rule/cost][d0history]；[E3 runner，cost_law][e3runner]；[counts][counts]。）

B01/B02 的整套 G/C/H complete wall 分别为708.25／665.01秒，仍作为两项已消耗记录保留；它们不承诺更频繁内部时钟的 D0 也会如此快。新 D0 的优化、构造、evaluation、I/O 工作和所选新 pair 的具体时长未知。有限counts、native代码或batching都不证明必定在cap内完成；我选择的是在这些固定上限内值得提出的有限问题，不是已经通过实际admission的执行保证。无单独pilot、profile、cost probe或前置A。（[B01 result，Complete cost][b01]；[B02 result，Complete cost][b02]；[证据规范，§11.9][spec]。）

每臂 cap 覆盖从完整调用的启动、必要准入、interpreter/import、配置及模型/optimizer创建，到真实训练、独立evaluator同步、全部必要评价、主要输出计算和完成发布。不得把setup、最后的比较或publication移出上限，拆片重启，挪用另一臂节余，提高cap，或以并行化隐藏费用。沿现有remote-first CPU四线程路线，每个实际invocation前作既有physical/effective至少4 GiB fresh admission；本轮没有运行它。

完成五轮和唯一终点评价并发布后停止。达到任一完整cap、发生非有限学习/主回报，或实际错误损害信息、reward、更新、状态处理或primary comparison时，停止相应依赖工作，保留真实已完成量与准确缺口；不得自动重试、改seed、截短轮数后宣称完成或补拼数据。H或D0缺少可信完整主量时不作完整H−D0极性；若仅G缺失，已经独立可信的H/D0事实仍可保留，但三策略对象未完整、G依赖的说法不得成立。有效的不利结果不是quarantine理由，可选资源遥测的缺失也不抹去独立可信的原生事实。之后只做此次完整或不完整intake，不自动再选一个对象。（[证据规范，§4、§11.8.7][spec]。）

## 六、实现与 UAV 的边界，以及仍未回答什么

源码支持 H 的真实 applied-mask→own reward/storage/update 路径，也支持 E3 的真正 fair-D0 参数构造；但当前 learning runner 的 `build_learner` 固定调用 `arm_parameters("large","d2")`。**新 H/D0/G 的命名、参数接入、comparison输出与完整cap仍是后续实现任务，不是把当前 C 字符串换成 D0 就已获得可执行比较。** 不在本轮修改源码、冻结keys/card/source或加载模型。未来只需针对这个实际改变的边界做比例相称的验证，不新增guards、registries、resume、profilers或工程比率普查；现行§11.8优先于旧30%硬门槛/100行申请措辞。（[learning runner，build_learner、final_evaluation][learning]；[工程规范，§4–5][engineering]；[证据规范，§11.8.6–8][spec]。）

我认可已检视的UAV接口差异：`scenario1.step` 把actions交给父类；`MultiUAVEnv.step` 以连续动作更新位置，随后更新channel/connections并计算reward；scenario1的reward组合coverage、SINR quality和altitude penalty。这个被检查的step接口没有corridor的applied lease-renewal参数。内部skill影响movement可能构成另一个问题，但本次不提出或选择它，也不声称全库没有别的接口。（[scenario1.py，step、_compute_reward][scenario]；[uav_env.py，step][uav]；[P44，§4][p44]。）

已有scenario1 baseline记录只允许使用off/fair-D0的exposure/integrity事实：各臂80000 transitions与旧37.7–39.9分钟成本不授权性能排序，也不为这个新比较或UAV新调用定价。其旧pilot/sweep建议不成为本B的前置门槛。P44所记录的局部文献只用于区别内部termination、intra-option action与实际actuator；本节点未另取论文原文，不由其综述诊断FSD或引入新架构。（[scenario1 baseline，Result first、Bound host、Cost][uavbaseline]；[P44，§5][p44]；[证据规范，§11.8–11.9][spec]。）

本次H/D0比较仍不能分离公开规则的直接作用、实际训练数据改变、recurrence、内部team决策、actor/representation质量和不同optimizer exposure。G的角色输出不能变成训练监督或actor能力证据；参数移动不是收敛证明。即使新H局部胜D0，也只能说它对这个同预算固定时钟构造有观察到的性能优势，不能说D2本身获胜、学会公开规则、最优固定时钟已被排除或UAV迁移成立。放弃这些更强结论，使本次只需要一次真实训练对和采样回报，而不是原因普查。

## 七、实际访问、历史交付与最终范围

本次科学证据按固定版本 `7b773b5a27336d3855fea83c4d6c5fc723ac74bc` 通过connected GitHub connector读取；任务定义按其单独固定版本读取。下表列出全部二十个已访问清单路径与使用范围。长文件是按相关章节/函数读取，不声称审阅全部依赖树、重新核算全部原始数组或独立复现训练。

| 实际访问路径 | 读取和使用范围 |
| --- | --- |
| [FSD_POST_B02_QUESTION_P44_ASSESSMENT_20260908.md][p44] | §1–5，重点选项、实际B价值、成本与UAV接口解释 |
| [pro_packets/20260908_post_b02_convergence/EXPOSURE_AND_COST.json][counts] | 零新暴露、两组旧成本、唯一备选工作/caps全文 |
| [FSD_NATIVE_RENEWAL_LEARNING_B02_INTAKE_20260908.md][b02intake] | §1–6，原branch、独立单位、角色短缺与停止 |
| [FSD_NATIVE_RENEWAL_LEARNING_B02_RESULT_EVIDENCE_20260908.md][b02] | 原生比较、全部阶段exposure、完整cost及边界 |
| [FSD_NATIVE_RENEWAL_LEARNING_B01_RESULT_EVIDENCE_20260908.md][b01] | 原生结果、服务核算、更新和完整成本 |
| [DIRECTION.md][direction] | 接受E3/E4、历次有限边界、B01/B02当前含义 |
| [pro_packets/20260907_post_native_control_convergence/archive/RESPONSE.md][previous] | §二、§五、§八及相关定义/停止；不是新任务替代品 |
| [FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md][e3] | 九配对、原规则、路径窗口、exposure/headroom |
| [FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md][e4] | 完成状态、人口、public null与reference表 |
| [FSD_E3_LARGE_D0_SEED2_RESULT_EVIDENCE_20260905.md][d0history] | 旧构造、Work、cost及历史状态边界 |
| [scripts/run_flexible_skill_duration_e3.py][e3runner] | arm_parameters与cost_law；另读取相邻manifest/CLI片段定位 |
| [scripts/run_fsd_native_renewal_learning_b01.py][learning] | applied_mask、build_learner、collect_training、evaluate/final_evaluation |
| [envs/pettingzoo/scenario1.py][scenario] | _compute_reward、step及定位时相邻片段 |
| [envs/pettingzoo/uav_env.py][uav] | step的action/position/reward接口；未作完整observation依赖审查 |
| [docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md][uavbaseline] | Result first、Bound host、历史cost与禁止排名边界 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §3–4、5.1–5.3、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][engineering] | §4–5和现行比例规则 |
| [AGENTS.md][agents] | focused reading、§2–4及相关共享工作权限 |
| [docs/research/portfolio/handoffs/2026-09-08-p45-fsd-post-b02-convergence.md][handoff] | 本次唯一问题、固定边界和零科学调用范围 |
| [pro_packets/20260908_post_b02_convergence/ISSUE_SNAPSHOT.json][snapshot] | 固定discussion快照、两轮旧交付与时间 |

本轮初读Issue10约在2026-09-08 12:33 UTC，实际读取了正文与两条既有评论。正文仍是历史P14描述，不能替代本次固定TASK。两条评论分别为[原生控制轮交付](https://github.com/CartmanFatass/My-paper-code/issues/10#issuecomment-5576589781)与[完成原生控制后学习选择的交付](https://github.com/CartmanFatass/My-paper-code/issues/10#issuecomment-5580329460)；后者对应完整提交 `eaff53a10b21383fb682f63bcf58782875599ff0`，其本轮固定版本内的正文已经读取。固定快照自身的观察时间为2026-09-08T12:05:49.096565+00:00，与本轮读取时间分开。旧短blocked receipt保留为历史矛盾记录，不撤销实际完整交付，也不重复它们。（[snapshot][snapshot]；[previous][previous]。）

没有妨碍这次方向选择的列出路径访问缺口。本咨询新增scientific invocations、model constructions、checkpoint loads、training starts/transitions、optimizer steps与evaluation episodes均为零；这里使用的是清单内已有机器记录与源码事实，没有运行代码或重新测量成本。

**最终范围仍是 B：在原固定N6/K2大Bernoulli corridor上，仅选择一对fresh H／真实fair-D0 k5 learner与匹配G的有限B性能比较；其余普通policy-gap家族保持原暂停。** 选择的不是“再试直到稳定”，而是从已回答的component问题转到尚未回答的同期固定时钟比较。任何结果都保留全部正反证、结束一次intake、无自动后继。完整答复的形成不修改现有证据、card、DIRECTION或Portfolio，也不授权本轮执行下一实验。

[p44]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_POST_B02_QUESTION_P44_ASSESSMENT_20260908.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_post_b02_convergence/EXPOSURE_AND_COST.json
[b02intake]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_LEARNING_B02_INTAKE_20260908.md
[b02]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_LEARNING_B02_RESULT_EVIDENCE_20260908.md
[b01]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_LEARNING_B01_RESULT_EVIDENCE_20260908.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/archive/RESPONSE.md
[e3]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md
[e4]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md
[d0history]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/FSD_E3_LARGE_D0_SEED2_RESULT_EVIDENCE_20260905.md
[e3runner]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/scripts/run_flexible_skill_duration_e3.py
[learning]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/scripts/run_fsd_native_renewal_learning_b01.py
[scenario]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/envs/pettingzoo/scenario1.py
[uav]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/envs/pettingzoo/uav_env.py
[uavbaseline]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/AGENTS.md
[handoff]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/portfolio/handoffs/2026-09-08-p45-fsd-post-b02-convergence.md
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/7b773b5a27336d3855fea83c4d6c5fc723ac74bc/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_post_b02_convergence/ISSUE_SNAPSHOT.json
[task]: https://github.com/CartmanFatass/My-paper-code/blob/e04604a460b2871ef4e9d6928599085dcd06268b/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_post_b02_convergence/TASK.md
