**选择 A：结束 scenario1 上个体 gap cost=.25、团队时钟与两级 cap 均为10、每臂五次更新这一已测试配置的原样延续；本次没有选择下一对象，也不选择所提二十轮训练比较。** 两个独立配对学习实例均给出超过 .01 MEI 的原生回报损失，最初的性能观察及随后选定的同配置再次观察都已完成。二十轮 B 是合法且不同的预算问题，并非因为前两次为负就不能研究；但现有支持尚不足以使我愿意为这个特定的四倍训练扩展继续投入。停止依据是已观察的收益／成本与下一条信息的价值判断，不是稳定 D0 优势、全部预算无效或整个 FSD 无价值的证明。（[当前问题，§2–4][question]；[P70 结果，§1–4][r70]；[P72 结果，§1–5][r72]。）

反对停止的最强材料也必须保留：P72 的 I 在第2–5轮随机采集回报上高于 D0，并有质量、海拔成本的小幅改善；五次更新没有被证明足以收敛。这使更长训练可能改变最终排序成为一个真实未解问题。不过，这些采集曲线不是同一确定性评价方式下的学习曲线，P70 也没有呈现相同的相对改善；它们目前不能提供二十轮时 I 相对 D0 会改善的直接读数。**我接受暂时不知道这个更长预算答案的代价，而不把“仍可能有收益”自动变成下一次运行。** 这不是要求 B 先有正号、完整因果解释或更强证据类别。（[P70 intake，§3、§5][i70]；[P72 intake，§3][i72]；[证据规范，§11.8.1–3、§11.9][spec]。）

## 一、最小生效范围与旧边界

本决定只结束以下原样早期预算扩展：既有 `UAVBaseStationEnv` scenario1，六架固定 UAV、五十名用户，uniform reset、free-space channel，H500、latent team/individual 数量6/6；I 使用真实 D2 个体成本 .25、团队成本 numeric +infinity、个体／团队 cap=10、k=10、age off；authentic D0 在同一 D2 路径上使用两个 numeric +infinity 成本及相同 caps。两臂均保持逐步接收当前允许的局部观察、每步产生连续动作的 recurrent actor，以及相同权限的中央协调信息。已测试预算为每臂五个16×500 rollout、第五次更新后唯一32回合确定性终点。（[原 UAV B01 卡，§2–5][c70]；[UAV B02 卡，§2–3][c72]。）

不再为这项不变的 .25/k10/五次更新比较选择第三个训练对、更多终点回合或原运行的继续。所提二十轮对象也没有在本次被选中；这不把它变成已完成的阴性实验。其他阈值、训练预算、团队策略、任务人口和更广 FSD 问题仍未由这两个实例决定。这里的“没有现成后继”是**本节点没有选择继续执行的科学对象**，不是声称源码不可用、比较器不合法或所有后继都不可能。

P67 开放的内部个体续约问题，与 P52 已结束的 corridor supplied-public-mask 扩展不同。本次保留 P52 的完整决定和更早普通 N6/K2 public-cue corridor 家族的暂停，不重新开放两者，不增加 recast，不进行 Portfolio PARK、生命周期、优先级或容量变更。P70/P72 已经发生的真实 native UAV 学习与评价事实也保留；不能把 P67 当时的“尚无 UAV 结果”当作今天的事实。当前决定不产生新的 UAV 调用或迁移结论。（[DIRECTION，Post-B03、Native individual-renewal UAV boundary、Accepted P70/P72][direction]；[P67 完整答复，开头及§七][previous]。）

P74 已明确恢复当前问题准备，P72 的 soft stop 不再是本次不继续的理由。但研究恢复没有补发已花费的 P70/P72 运行额度，也没有预选第三对或长预算。当前答案形成方向选择；由 Root 返回原 DM 做既有完整 intake，任何后来真正需要的任务仍由现有权限下的新明确命令给出，不增设逐阶段批准。（[P74 restart，FSD 行及返回边界][restart]；[AGENTS，§1–2、§4–7][agents]。）

## 二、两次原生损失按原卡成立，不扩大独立单位

| 已完成 native UAV 对象 | 训练／评价 base | D0 的 J | I 的 J | 配对 I−D0 | 条件终点 SE | 正／负终点差 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| B01 / P70 | 770503 / 780503 | .26946095234781076 | .21979038918069888 | −.049670563167111874 | .023762591435853447 | 12 / 20 |
| B02 / P72 | 770603 / 780603 | .4854120288125866 | .45009930351470057 | −.035312725297886094 | .012523489942436556 | 9 / 23 |

两项都在原 .01 absolute native MEI 下进入 `<−.01` 的 `opposite_sign` 分支。P70 的原读法是削弱这个 .25 个体门限与预算的配置；P72 的原读法是同一配置在两个已观察学习实例中都出现超过 MEI 的损失，仍不构成稳定 D0 优势或广泛关闭。本次保留这两个读法，不加入显著性要求、继承的 competence cutoff、所有回合必须同号或 endpoint gap 必须活动的条件。（[P70 结果，§1][r70]；[P72 结果，§1][r72]；[原卡，§5][c70]；[B02 卡，§3][c72]。）

独立学习单位是两个 matched training instances；每个实例各有新的有限32回合配对终点。P70/P72 的回合差 sample SD 分别为 .13442151634285882 和 .07084355729934733。已有分析报告两个 pair means 的描述性平均 **−.04249164423249899**、sample SD **.01015252452050656**；这些 pair means 仍带终点评价噪声，不是分离出的纯训练种子方差，不是64次独立训练，也不支持稳定总体排序。本节点引用既有分析结果，没有另算总体置信度或把回合池化为训练重复。（[P72 结果，§1、§3][r72]；[机器记录，existing_completed_records][counts]。）

这里的主量始终为 `J=6*adapter_episode_return/500`。它只把原 adapter 回合和换成每个 primitive step 的团队原生奖励单位，不改变训练 reward、value target、normalizer 或学习损失。目标是 `.7*coverage + .3*quality - altitude_penalty`；现有输出字段 `energy_penalty` 指这个海拔惩罚，不是另一个能耗指标。**.01 是包含该成本的加权原生尺度上的一个点，不是覆盖率恰好提高一个百分点。**（[原卡，§4–5][c70]；[P72 结果，§2][r72]。）

### 分量符号相反，不能编成共同的海拔伤害解释

| I−D0 的已记录分量 | P70 原分量差 | P70 对 J 的贡献 | P72 原分量差 | P72 对 J 的贡献 |
| --- | ---: | ---: | ---: | ---: |
| Coverage | +.024183750000 | +.016928625000 | −.052598750000 | −.036819125000 |
| Quality | −.028570901271 | −.008571270381 | +.001746146113 | +.000523843834 |
| Altitude penalty | +.058027917786 | −.058027917786 | −.000982555868 | +.000982555868 |

P70 的覆盖收益被质量和海拔奖励损失抵消；P72 则由覆盖损失超过小幅质量和海拔收益。第二次并没有重复第一次的海拔伤害。分量核算说明奖励差由哪些已记录项构成，不说明内部技能、某个 optimizer、运动策略或事件检测器为什么造成这些项。保留 P70 的覆盖正值、P72 的另外两个正贡献，以及12个／9个正终点差；它们都不能事后替换原最终 J 主量，也不能抵消对两次平均损失的报告。（[P70 结果，§2][r70]；[P72 结果，§2–3][r72]。）

## 三、训练中活动与终点不活动，是两种不同事实

两项都是实际训练而非固定权重或非学习占位比较。每项均有80000 collected/stored training transitions、160训练回合、10个 update stages、32000 scoring steps／64终点回合、4次模型构造、2次训练开始和零旧 checkpoint load；每个 learner 自己完成五轮与一次独立终点。五个 active parameter groups 的首轮及第五轮位移有限且非零；这支持真实更新发生，不认证 competence 或收敛。（[P70 结果，§3][r70]；[P72 结果，§4][r72]。）

| 训练阶段的实际计数 | P70 D0 | P70 I | P72 D0 | P72 I |
| --- | ---: | ---: | ---: | ---: |
| Individual gap causes | 0 | 54390 | 0 | 65761 |
| Sampled individual positions | 24000 | 78390 | 24000 | 89761 |
| Joint decision rows | 4000 | 28351 | 4000 | 31821 |
| Team decisions | 4000 | 4000 | 4000 | 4000 |
| Coordinator optimizer.step | 525 | 3345 | 525 | 3765 |

四个 learner 的 actor、critic 各11250次，team discriminator 各75次，individual discriminator 各300次；每个 evaluator 的全部 optimizer calls 为零。P70 两臂合计49620次 optimizer.step，P72 合计50040次。相同 actor/critic 调用数与环境步数不意味着相同梯度、数据、normalizer 或计算暴露；I 的高层工作明确更多。Joint row、个体采样位置、token switch 与 optimizer.step 不是可互换的单位。（[P70 结果，§3][r70]；[P72 结果，§4][r72]。）

在两项确定性终点中，**两臂均为零 individual gap causes**，每臂1600次团队决策、9600个体采样位置。Token switches 却不同：P70 为 D0 612／I 1421，P72 为 D0 760／I 1272。故相同终点时间计数不等于相同学得策略或相同动作。已发生的额外路径主要体现在训练阶段；这些结果不能被写成“终点评价中的额外在线中断造成收益／伤害”。它们仍是有明确处理历史的学习／数据／credit／control package 比较，不因终点 gap 为零失效。（[P70 结果，§3][r70]；[P72 结果，§4][r72]。）

空 evaluator storage/update buffers 没有提供 segment-duration 统计，因而该项是**未测量**，不是零时长技能。原生回报和决策计数独立可信，这个限定不需要用额外 replay、duration census 或活动门槛来修补完整 B 的极性。（[两次 intake 的 instrumentation limits][i70][i72]；[证据规范，§11.8.7][spec]。）

### 更长训练的最强支持保留为采集事实

| Rollout | P70 D0 sampled J | P70 I sampled J | P72 D0 sampled J | P72 I sampled J |
| --- | ---: | ---: | ---: | ---: |
| 1 | .244162003 | .222030451 | .239326522 | .233039917 |
| 2 | .237304032 | .121714614 | .158766954 | .222618770 |
| 3 | .273789234 | .140950264 | .183964045 | .249967688 |
| 4 | .314770682 | .171681191 | .231470434 | .247263146 |
| 5 | .325517987 | .220731432 | .134453430 | .283221612 |

这些是本臂当轮 update 之前、各自新轨迹上的随机采集均值。P70 I 全程低于 D0；P72 I 在第2–5轮较高，最终确定性 J 却较低。后一个事实是支持进一步探索的实质反面材料，不能因为决定停止就删掉；但它没有直接测量二十轮确定性终点，也不是“训练越久相对排序必然改善”的证据。原 runner 的 `collect_training` 与 `final_evaluation` 正好区分随机采集和最终唯一确定性评价；本次不改评价方式来选择有利结果。（[P70 结果，§3][r70]；[P72 结果，§2][r72]；[shared runner，collect_training、final_evaluation][runner]。）

## 四、同信息反应型 D0 为什么仍是正确的边际对照

所问路径保持为：自身／同伴运动改变服务几何 → 固定 UAV 拥有 held skill 与运动输出 → 当前允许的协调信息可触发内部个体 gap renewal → 当前观察驱动的 recurrent actor 产生连续运动 → 原生服务奖励与后续本臂数据 → 原有 segment/discount/credit 及 optimizer 更新。没有新增成员、身份复用、稀疏观察到达、primitive clock 或奖励语义；同伴在训练中共同适应，两臂的后续 RNG 消耗和内生轨迹保持各自所有。（[原卡，§2–3][c70]；[P72 intake，§3][i72]。）

D0 固定的是技能重决策时刻，不是把速度保持十步，也不是十步才看一次新观察。它的 recurrent actor 同样逐步响应并保留记忆；协调器信息权限也未被削弱。因此它能够回答“增加该内部个体重决策配置，在真实学习后是否有边际原生表现价值”。这不要求 D0 是调优后的最佳 UAV 算法。两个 D0 都是真实有效 learner，但目前不能称为 tuned competence reference；其强反应能力是比较器的能力边界，不是已达到最优表现的实测认证。（[原卡，§2][c70]；[当前问题，§3][question]。）

当前材料使“给定训练预算下，额外重决策、数据分布与 credit/optimizer 暴露的改变没有转化为更好的最终 J”成为两个观察的准确描述。它没有分离 policy-gap 噪声、技能扰动、actor/representation、normalizer、某类梯度更新或共同适应的因果份额；也没有证明多训练无用。反应型 null 的存在与两次损失一起降低对当前配置的继续投入信心，却不构成整个策略类被包含或结构等价的定理。

Scenario1 tuned same-information generic headroom 仍**缺失**。不能拿原生奖励尺度的上端冒充已知可达上界，不能拿 E0 的旧分数排名或替代本次 comparator，也不能把缺失当作零或 B 的启动条件。本次既不选择 baseline tuning，也不把 flat MAPPO adapter、精确最大值或先做 headroom 的 A 塞到未选 B 前面。（[scenario1 baseline，Result first、Missing/inference][baseline]；[证据规范，§11.7–11.9][spec]。）

## 五、为什么在具体的二十轮 B 与停止之间选择停止

**B 确实改变了问题。** 它不是第三次原样五轮重复，而是在相同 I/D0 控制定义下，把每臂训练增加到二十轮后直接观察原生表现。这是一个充分明确的性能探索，不需先证明早期 undertraining、取得正结果或保证终点 gap 活动。不存在新五轮并行对照并不使这个 B 不合法，只意味着不能用它估计纯预算效应或预算响应曲线。（[当前问题，§4][question]；[本次 TASK，Requested decision][task]；[证据规范，§11.8.1–3][spec]。）

我不选择它的具体理由，是目前对这个**特定预算扩展的增量价值**评价低于其必要工作。最初开放时待查的是额外内部决策是否值得考虑；已有两次实际、活动充分但非收敛保证的训练观察，均未在预定原生终点兑现收益，且 I 付出更多工作。最有利于追加的 P72 采集曲线没有与最终比较同口径，第一次采集也没有同样的相对方向。它们留下“更长训练可能有不同结果”，但没有给这次从5到20的扩展提供一个已经观察到的终点追赶趋势或相对学习速度。**这里说的是支持力度，不是要求必须先取得这样的趋势才准运行 B。**

原生分量在两次间换了符号，也不能充当更长训练会纠正某一个共同缺陷的证据。反过来，不要求更长 B 去解决这个因果问题：其可能价值只计为一次新预算下的 I−D0 原生比较，不把“同时证明旧失败原因、收敛或在线 termination 价值”这些未设计的收益加进来。即使放弃全部强归因，单次新预算的性能信息仍有价值；本节点判断它当前尚不值得下面明确的320000训练 transitions与新完整调用额度。

| 未选择的二十轮 B 若得到完整读数 | 会新增的认识及可能改变的判断 | 不能预付给它的结论 |
| --- | --- | --- |
| I−D0 > +.01 | 在一个新长预算实例取得局部正支持；会改变“目前只有这个 native 配置的负面实例”这一证据状态，并使该长预算配置值得重新考虑 | 不是证明早期损失由 undertraining 导致，不是稳定正收益或在线 gap 价值 |
| inclusive ±.01 | 在这个新实例上表现小或分辨率有限，增加对预算相关表现的有限认识 | 不是等价，也不是已经找到最小充分训练量 |
| I−D0 < −.01 | 不利观察扩大到一个较长预算实例，进一步削弱继续采用该设置的理由 | 不关闭所有预算或阈值，不证明 D0 的总体优势 |

因此我没有声称 B 的任何结果都无关，也没有把它叫作重复劳动。选择 A 是接受目前仍可能错过一个长预算正例的风险，不继续为这个配置购买该观察。没有已测概率、信息价值分数或支配定理支持更精确的投资计算；这是基于所给证据与成本的有限方向判断。负结果可以支持有理由的新 B，正结果也不会自动授权无止境追加；本次两条原则同时保留。（[证据规范，§6.1、§11.8.2、§11.9][spec]。）

不改为十轮、调 threshold、恢复 checkpoint、增加随机终点、搜索最优 skill 或另造诊断来回避这个选择。那些都是未选择的额外问题。**当前下一 discriminator 明确为没有；不是把下一科学机制留给 DM/Root 选择。** 以后一个真正改变继续理由的具体问题仍可按既有适当层级提出，但这里没有预约准备任务、复核服务或重入实验。

## 六、必要工作与已花费成本：B 可实施不等于本次值得购买

| 所提二十轮 B 的主导工作 | 前瞻数量，未选择／未分配 |
| --- | --- |
| 训练 | 2 arms ×1 fresh pair ×20 rollouts ×16 lanes ×500 =320000 transitions；640训练回合；40 update stages |
| 唯一终点 | 2 arms ×32 episodes ×500 =32000 scoring steps；64终点回合，仅在第20次更新后 |
| 总体 | 352000环境步；2112000 agent-step observations；21000 learned batch control calls |
| 模型 | 2 learners＋2 independent evaluators；2 starts；0 checkpoint loads |
| 每轮决策规模 | D0 800 joint rows／4800 individual positions；I 最多8000／48000；两臂团队 rows 均800 |
| 未知算法工作 | 实际 individual/team segments、coordinator minibatches及 optimizer calls，数据依赖，不能强行匹配 |
| 额外搜索／科学验证 | 无 nested candidate、trajectory 或 solver search；无额外 scientific validation panel |

以上是材料内的机器算术，不是本咨询执行量。相同 team rows 不意味着相同 team token，相同 primitive steps 不意味着相同计算量。四十个 update stages 不能替代 optimizer.step 计数。（[机器记录，proposal_B、known_count_expressions][counts]。）

| 臂 | P70 已测 complete wall | P72 已测 complete wall | B 的旧工作四倍情景 | B 所提新完整 cap |
| --- | ---: | ---: | ---: | ---: |
| D0 | 471.89秒 | 471.50秒 | 1887.56秒 | 3600秒 |
| I | 1221.49秒 | 1297.28秒 | 5189.12秒 | 18000秒 |
| 一对合计 | 1693.38秒 | 1768.78秒 | 7076.68秒 | 21600秒 |

情景式是逐臂 `4 × max(P70,P72 complete wall)`；它连不变的32回合终点评价也乘了四。它不是二十轮的新测时、统计上界或未来保证，I 后期续约频率和更新负荷仍可能改变。相对于此前 P67 的旧 E0 压力情景，现在有同一 native loop 的实际时长锚；这提高了工作量讨论的依据，但不能证明完成必在 cap 内。（[机器记录，proposal_B 的 wall_scenario_formula][counts]；[P70 结果，§4][r70]；[P72 结果，§5][r72]。）

两项已完成 native B 合计 **3462.16秒 summed complete wall、13739.12秒 aggregate CPU work**。P70/P72 各自 study critical path 为1817／1911秒，含调用之间的间隔，不能与上述两种工作量混用。两次 I 的 measured wall 均高于 D0，约2.5885／2.7514倍；这是这些执行的事实，不是一般算法复杂度或跨硬件效率结论。已有 admission、peak RSS 与 terminal receipts 完整；continuous free-memory 未测不撤销这些非资源主张。（[P70 结果，§4][r70]；[P72 结果，§5][r72]。）

**我没有以超预算为由拒绝 B。** 它的已给情景低于所提 cap，且没有组合搜索；但它仍要购买两套四倍训练和完整终点，最多使用新21600秒完整调用上限。该未知答案的当前价值不足，是停止的主因。不能因 cap 较宽或旧调用还有未用秒数就认为新工作免费；旧 allowance 已耗尽，情景未超 cap 也不是新增分配。（[当前问题，§4][question]；[P74 restart][restart]。）

若以后另行选择这个或其他对象，正常 remote-first CPU4/FP32、原数值语义、每次实际 invocation 的 fresh admission、exact committed source 与完整计时边界仍适用。这里没有新的 invocation 需要 admission。没有增加 pilot、profile、calibration、resume、重试或把评价／发布移出 cap 的选择；不以一个前置 A 代替这次没有选择的 B。

我按任务允许范围读取了 shared native runner，以评估预算改变所依赖的实际路径：当前 `ROLLOUTS=5` 同时进入 config、collection、endpoint与 pair checks，`main` 在 collection结束后只调用一次 `final_evaluation`，主量用真实 U 计算 J。二十轮若被选中，需要后续明确的预算／身份接入及受影响边界检查，保留旧实例；不能直接把当前文件称为已交付的二十轮实验。这个实现事实**不是本次 A 的 blocker**，也不要求全文依赖审计或额外科学测试面板。（[shared runner，make_config、collect_training、final_evaluation、assemble_pair、main][runner]；[工程规范，§4–5][engineering]。）

## 七、历史、文献与本节点实际读取

旧 corridor 的 H−C +.4973828125／+.520390625、对应 G−H +.0211848958／+.0108463542，与 corridor B03 的 H−D0 +.3928645833333336、G−H +.1152864583333331 全部保持原意义。它们不是本次 I/D0 的额外训练实例。B03 的弱但有效 D0、H 的原生角色短缺以及不相等的旧 optimizer 工作，仍限制其因果和性能范围。E3 六个 competent medium/large 配对损失、small seed2 competent +.033291585、E2 的 duration-control 事实和 E4 的 public-greedy 解释也不被删除。当前 native 两次阴性不反向改写这些有界正观察，旧正观察也不抵销当前主量。（[P67 完整答复，§六][previous]；[DIRECTION，P52／P67／P70／P72边界][direction]。）

P67 当时源于一个有用途的可检验假设而开放有限对象；P70/P72 给出了真正的新数据。现在缩小继续范围不是声称当初研究不该进行，而是让当初选择的直接观察产生方向后果。P67 原选择不是 RECAST，本次也不引入新的机制改写或 recast 计数。（[P67 完整答复，开头及§四][previous]；[DIRECTION，Native individual-renewal UAV boundary][direction]。）

本节点只复用了 P67 intake §5 记录的 ACAC/MARL-0449 选定 passage summary，所述 PDF pp2–3、JSON elements388–389/410/412 区分 intra-option reaction、termination 与决策时观察可用性。没有另读原论文、索引或 PDF，不作新颖性或当前文献覆盖判断。该区分只约束这里每步有观察的反应路径表述，不能解释两次损失，不能把本题说成异步 macro-observation/padding 缺失问题，也不支持从更多训练导入某篇论文的收益。（[P67 问题 intake，§5][literature]；[P72 intake，§3][i72]。）

科学资料均通过 connected GitHub connector 使用固定证据版本 `1fd266b76de99e43cbda4c9bee1b2e96dba82e1f`；TASK 使用其指定的单独固定提交。实际读取了下列17个清单路径。长文件按相关章节／函数读取；表中链接对应完整仓库路径，不声称审阅整个依赖树或独立重算旧原始数组。

| 实际读取资料 | 本次使用范围 |
| --- | --- |
| [FSD_P74_POST_UAV_B02_QUESTION_INTAKE_20260909.md][question] | §§1–5，当前选择、全部相反材料、B的价值及工作量 |
| [FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md][r72] | §§1–5，原规则、回报／分量／训练／终点／资源 |
| [FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_INTAKE_20260909.md][i72] | §§1–5，接受、解释、instrumentation与历史 soft stop |
| [FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_RESULT_EVIDENCE_20260908.md][r70] | §§1–4，第一次的全符号观察、学习活动和完整成本 |
| [FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_INTAKE_20260908.md][i70] | §§1、3–5及相关核对，已由P72回答的再次观察问题 |
| [FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md][c72] | §§1–4及相邻完成记录，原比较、独立单位及阅读规则 |
| [FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md][c70] | §§2–6，原生路径、训练／评价、主量、MEI与caps |
| [pro_packets/20260909_p74_post_uav_b02_convergence/EXPOSURE_AND_COST.json][counts] | 当前零暴露、既有记录的提取字段、proposal_B完整工作／成本；不重算原始实验 |
| [DIRECTION.md][direction] | P52、P67、accepted P70/P72及定位时相邻摘要 |
| [pro_packets/20260908_p67_uav_internal_renewal/archive/RESPONSE.md][previous] | 完整既有方向答复、原家族范围与保留的历史反证 |
| [FSD_P67_UAV_INTERNAL_RENEWAL_QUESTION_INTAKE_20260908.md][literature] | §5 文献／信息边界及相邻原准备语境 |
| [scripts/run_fsd_uav_individual_renewal_b01.py][runner] | 预算常量、collection、唯一endpoint、J和pair assembly路径 |
| [docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md][baseline] | exposure-only、禁止排名与headroom缺失；旧pilot建议不作新义务 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §6–7与§11.4、11.7–11.9及相邻解释，区分方向处置和经验极性 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][engineering] | §§4–5，既有no-new-machinery和比例相称的source/check边界 |
| [AGENTS.md][agents] | §§1–2、4–7及定位时相邻文字，当前Root/Portfolio、tier、shared branch及admission |
| [docs/research/portfolio/handoffs/2026-09-09-research-resume-p74.md][restart] | 当前恢复指令、FSD准备与完整返回范围 |

两份独立 DM_ANALYSIS JSON、B02 thin runner、`hmasd/agent.py`、`scenario1.py` 和可选 ISSUE_SNAPSHOT 未另行读取：所需数值及计数已由上述结果／intake／机器提取记录相互说明，没有需要扩大读取的实质矛盾。核心动作路径采用原卡、P67已形成答复及当前接受记录；未声称重新审查这些未展开源码的全部依赖。指定 Issue10 的正文及五条历史交付评论已直接读取，用于识别本轮不是早先 corridor post-B02 或P67的重复交付，而非科学额度来源。

没有妨碍本次方向选择的已列必要路径访问缺口。当前 consultation 的 scientific invocations、model constructions、checkpoint loads、training starts/transitions、optimizer steps、evaluation episodes、simulation steps、profiling、checkpoint replays 与 scientific validation 均为零。没有运行科研代码、构造模型、另做分析实验、选择数值 keys、创建 card/CM spec 或修改科学状态。上述推荐与假设结果表是本节点的推断与取舍，历史数字是固定材料中的观察。（[机器记录，current_consultation_exposure][counts]。）

**给主人的建议：停在这个已测试的 .25/k10/五次更新扩展，不继续原样重复，也暂不购买二十轮扩展。** 最强反证是两次真实原生损失与更高 I 工作；最强保留支持是第二次较好的随机训练回报、各次不同的正分量及正终点。它们留下更长训练可能不同的真实不确定性，但没有让我选择新320000训练 transitions、7076.68秒旧工作情景及最多21600秒完整 cap 的那一个 B。保留实际native UAV结果、旧corridor停止与所有有效正反证，不作总体无效、稳定D0优势或Portfolio处置；本次下一对象明确为没有。

[question]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_P74_POST_UAV_B02_QUESTION_INTAKE_20260909.md
[r70]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_RESULT_EVIDENCE_20260908.md
[r72]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md
[i70]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_INTAKE_20260908.md
[i72]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_INTAKE_20260909.md
[c70]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md
[c72]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/pro_packets/20260909_p74_post_uav_b02_convergence/EXPOSURE_AND_COST.json
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/pro_packets/20260908_p67_uav_internal_renewal/archive/RESPONSE.md
[literature]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/candidates/flexible_skill_duration/FSD_P67_UAV_INTERNAL_RENEWAL_QUESTION_INTAKE_20260908.md
[runner]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/scripts/run_fsd_uav_individual_renewal_b01.py
[baseline]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/AGENTS.md
[restart]: https://github.com/CartmanFatass/My-paper-code/blob/1fd266b76de99e43cbda4c9bee1b2e96dba82e1f/docs/research/portfolio/handoffs/2026-09-09-research-resume-p74.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/b2342c20a2cbc01ec750a0442025a5615809eb13/docs/research/candidates/flexible_skill_duration/pro_packets/20260909_p74_post_uav_b02_convergence/TASK.md
