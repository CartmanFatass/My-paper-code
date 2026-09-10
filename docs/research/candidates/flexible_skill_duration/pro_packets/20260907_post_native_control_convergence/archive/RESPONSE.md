**开放一个有界真实学习问题：在原大差异 K2 corridor 上，从头训练一对 C_train／H_train，比较原生续约执行规则在真实学习过程中带来的总回报差异。选择一个新的配对训练种子、每臂五个 rollout、每 rollout 十六个环境与四百步；只在第五次更新后各评价三十二个配对回合，并在同一评价 keys 上运行三十二回合的公开信息 G。** 不增加第三个 trained arm，不重复旧检查点面板，不重跑 E3/E4，也不开放阈值、host 或架构搜索。

理由是：A01 已经给出了实际原生控制改变后的可信回报事实，而不再只是结构 headroom 或事件相关性。这个事实足以支持一次规模有限的真实学习比较，但它尚未回答新初始化的 learner 持续经历自身实际续约后果时，这种控制包的优势会保持、消失还是反转。H 的明显剩余角色损失使这个问题更有必要被如实限定，而不是使所有 B 都必须先完成因果诊断。**此次开放的是“固定公开续约规则＋既有内部 D2/actor 的混合控制器”与完整 D2 的早期学习比较，不是恢复整个普通 policy-gap 学习收益家族，更不是宣布同步 D2 termination 或 credit 已被修复。**（[A01 intake，§3–4、§7][intake]；[证据规范，§11.8.1–3、§11.9][spec]。）

普通 fixed-K2 家族的暂停只为这一具体比较作有限解除；其他未选对象继续保持原边界。这是方向内有限继续，不是更换 K、信息结构、Q-head、team-credit 或 host 的 recast。整体 ACTIVE/HIGH、Portfolio 生命周期、优先级、容量与 UAV 状态不变。后续科学卡、完整实现任务和实际执行分配仍经现有 Root／Portfolio 路线形成；本回复没有运行或分配新的科学调用。（[当前 DIRECTION 的两个 Convergence boundary][direction]；[P25 handoff 的 Question/bounds、Budget/return][handoff]。）

## 一、先保留 A01 真正回答的内容

A01 是条件于一份看到 E3 结果后选择的 large_d2_seed2 最终权重的 A/RECON。它不是新训练样本。C 为完整确定性 D2；H 仅改变 t>0 实际送入 host 的续约 mask，继续接收自身轨迹产生的 observation/state；G 使用公开信息和自己的 plan，绕过 learned actor。三者配对的是外生 episode keys，不是内生轨迹。（[A01 result，Population, policies and uncertainty unit][result]；[原卡，§1、§3][card]。）

| 已完成策略 | 完整回报均值，t=0…399 | post-reset 均值，t=1…399 |
| --- | ---: | ---: |
| C，完整 D2 | 0.4540234375000001 | 0.45516134085213045 |
| H，公开 applied renewal | 0.7233723958333336 | 0.7251853592314120 |
| G，公开信息 greedy | 0.8894921874999999 | 0.8892152255639098 |

完整 H−C 为 **+0.2693489583333334**，配对 episode SE 为 **0.007149877611049748**；post-reset H−C 为 **+0.2700240183792816**。与此同时，post-reset G−H 仍为 **0.16402986633249772**，配对 SE 为 **0.0030754574488204237**。全部三十二个 H−C 及 G−H 配对差都为正，只描述这组外生回合，不是三十二个独立训练种子。（[A01 result，Direct native-return observations][result]。）

反面量不能退到脚注。H 在 post-reset 的 68,121 个 KEEP/fresh 机会中有 12,566 次 wrong role，池化错误率 **18.4466%**，回报单位损失约 **0.16403**。C 在自身不同的 41,462 个机会中有 6,593 次错误，池化错误率 **15.9013%**，post-reset 错误角色损失约 **0.08606**。H 改善总回报，同时留下更多错误角色服务损失和更高的条件错误率；不能将不同机会集上的率差直接解释成同一分布上的 actor 能力退化，也不能用总收益隐去这些短缺。（[A01 result，Service accounting, applied action and reset][result]。）

原卡第二行继续成立：**报告局部收益与剩余服务短缺，撤回 timing-only complete competence 解释，不把残差归给唯一 mediator。** G 的初始不续约使其完整回报相对 C/H 多一个已知 .0025 项，但 C 与 H 的初始约定一致，不能用它解释 H−C。已记录的关系是 `(H−C)_full=(399/400)(H−C)_post`；`(G−H)_full=(399/400)(G−H)_post+.0025`。post G−H 与 H 的 wrong-role loss 对应，是该面板的原生奖励核算，不是唯一因果定位。（[原卡，§4][card]；[A01 result，Service accounting、Frozen rule][result]；[intake，§3][intake]。）

我的方向选择使用的是这个有残差的第二行，而不是把结果偷偷读成第一行的 near-G／完整 competence。原 A01 已结束，原停止规则没有被本次问题改写；新的真实学习比较是另一个明确、结果后选择的 B 对象。（[上轮完整答复，§六–七][previous]；[本次固定问题][task]。）

## 二、为什么选 C_train／H_train，而不是加入 D0 或继续暂停

此次要决定的不是“哪个方法已优于最强固定时钟”，而是：**在相同真实训练预算和既有学习规则下，把 applied native renewal 固定为公开事件规则的整套控制器，是否仍比让内部 D2 决定 applied renewal 的整套控制器获得更好的原生回报。** 这是实际训练后的控制包比较。它不单独估计“学习本身造成的收益”，也不将执行规则的直接作用与它改变的学习轨迹分开。

| 候选选择 | 能回答的问题 | 本次取舍 |
| --- | --- | --- |
| C_train／H_train，公开 G 为操作性参照 | 只在科学定义上改变 applied-renewal 规则，让两个 learner 各自训练，观察这个改变的总后果 | **选择**，两种新训练配置，共用一个新的配对训练 seed |
| H_train／同预算 D0 k=5 | 混合控制器与固定时钟方法的初步性能排序 | 不选择；这同时改变内部终止/技能节奏及原生续约规则，不再是此次最小 component 比较 |
| C_train／H_train／D0 全部训练 | 同时回答 component 与性能排序两问 | 不选择；不能通过把候选全加上来回避选择 |
| 维持无后继暂停 | 不再投资这个公开 host 上的混合控制器 | 反对意见成立但此次不采用，理由如下 |

**C_train 是可信的同实现 component control，不是本 host 上最强或已在新预算下合格的性能 baseline。** 这一限制必须写进后续结果。历史 D0 k=5 对六个 medium/large 配对的优势非常重要，但旧 128,000-transition D0 不能作为新 32,000-transition learner 的公平同期对照。本次不训练 D0 的代价是：即使 H_train 胜 C_train，也不能声称恢复了相对 competent fixed clock 的优势，或推翻 E3。若后来问题确实转为这种性能排序，应届时明确选择同预算的 D0，而不是事后借用旧分数。（[准备 intake，Recommendation and competing reading][preparation]；[E3 result，Paired final returns、Validity/exposure][e3]；[E3 runner，arm_parameters][e3runner]。）

G 是本问题最强合法的公开信息 operational null：不需要 learned actor 就能实现公开规则下的原生服务。它让报告不能把一个“超过较弱 C”的收益写成完整能力或最优表现。G 不是经过相同学习预算训练的 baseline，也不为 C/H 的 actor 提供 competence 证明。保留 G，不要求 H 先赢过 G 才允许 B。（[A01 原卡，§3–4][card]；[E4 result，Population, strongest null][e4]。）

维持暂停的最强理由是：A01 的收益可能主要来自一个已经存在的公开规则，剩余角色学习问题未必值得灵活时长方向继续投入。我认可这会限制未来论文或机制价值，却不认为它足以否定当前这个很小的探索。A01 已排除“在该已训练实例上，改变实际续约根本没有原生后果”的工作解释；它没有排除“从头训练后优势消失”。后者可由少量真实学习与直接回报比较回答，不能由更多旧权重回合、更多参考枚举或参数位移说明回答。**本次愿意购买的是这个早期学习比较的信息，不是对 public greedy 的新颖性主张，也不是对一个完整新架构的投资。**

这项选择与 §11.8 相称：一个可信、意义清楚的局部观察可以支持有限 B，既不要求事先唯一定位原因，也不要求已经跨种子显著。反过来，局部正结果也没有授权无限扩展。本次只选择下述一对运行，没有“直到所有种子为正”的后续规则。（[证据规范，§5.2、§11.8.2–4、§11.9][spec]。）

## 三、唯一新问题的科学定义

### 不变的人口、信息和模型结构

只用原 large Bernoulli corridor：N=6，每 region 三个固定实体，K=2，四个 host zone、两个 region，H=400，hazards=(.02,.20)，Delta=1，rho=0，无 probe、churn 或 E5 coupling，连续二元 action 经 argmax 得到该步原生 role。实体、zone、region 归属不变；无 join/leave/replacement 或 censoring 问题。

两臂均使用既有完整 HMASD learner、coordinator、recurrent actor/critic 和 discriminator 路线，从新初始化开始。模型仍为 n_Z=6 team tokens、n_z=2、action_dim=2；不能把四个 host zone 当作四个 team token。内部 D2 均为 c=c_Z=.25、individual/team caps=40/400、interruption_delta=1、age feature off。保留既有网络、损失、折扣、精度与 optimizer schedule；不新增 shaping reward、G 的角色监督、Q-head 或私有信息。（[A01 原卡，§3][card]；[E3 runner，arm_parameters][e3runner]；[E2 runner，_execute][e2runner]。）

### 被操纵的是 applied renewal，不是同步 termination

**C_train：**训练与评价都把内部 `d2_sampled_mask` 原样送给 host。

**H_train：**训练与评价都正常运行本臂内部 D2 和 actor；在每个 episode 的 t=0 保留正常 forced-reset renewal，t>0 仅把实际送给 host 的 renew 改为当前公开 regional change flag。连续 action 仍由本臂 actor 产生，不能填入 G 的正确 role。H 的规则是固定设计的一部分，不是 learner 学到的 renewal policy。现有 A01 的 `apply_renew_mask` 和 `evaluate` 给出了这个动作语义，但 A01 runner 没有真实训练路径，不能原样冠名为 B。（[A01 runner，apply_renew_mask、evaluate][a01runner]。）

原生与学习路径明确为：**外生区域事件使固定实体的 lease 失效 → 公开 flag/cue 及本臂实际 observation/state → 本臂内部技能决策、原生 actor action → 所选 applied renew 与本步 role 进入 host → 真实 shared reward、下一 observation/state → 本臂真实 transition storage、既有内部 segment/credit 和 optimizer updates → 更新后的策略再采集下一 rollout。** H 不能接收 C 的内生 action、hidden-state 或 state tape，也不能把 G 的角色正确性标签变成训练输入。

内部 skill segment 与物理 lease interval 是不同的区间。H 保留真实内部 sampled mask、采样 log probability、计时器和 decision metadata；其原生 H reward 与 H 的实际后续状态进入原来的学习记录。不能把公开 applied mask 回写成“模型采样过的 mask”或伪造 replay 来宣布同步。内部 segment 的数量和长度会因 H 自己的新轨迹而改变，这是允许的真实结果；保留相同 schedule 不意味着两臂 optimizer 次数相等。这里不声称该 heuristic credit 已经等价于按物理 lease 分段的优化，更不声称得到唯一正确的 termination gradient。（[A01 原卡，§1、§3][card]；[上轮答复，§三、§六][previous]；[E2 runner，_execute 的真实 rollout/update 与计数][e2runner]。）

这正是研究对象的有限含义：比较两套真实学习和执行规则的总原生后果。若实现改成用公开 flag 同步重新采样技能、重写计时器、segment 或 credit，那就是另一项尚未在这里选择的科学干预，不能作为 H_train 的无声修复。

### 从头训练与独立评价的状态边界

选择**一个独立于旧检查点的新的配对训练 seed**，在任何新结果之前一次写定其数值及外生 keys。两臂各自新建 learner、optimizer 和 normalization 状态，以配对初始化和共同外生训练随机性控制比较；不加载、续训或蒸馏旧 large seed2 权重。配对允许两臂初始权重相同，但后续 host、技能、hidden state、reward 和 updates 都属于各自轨迹。一个 seed 下的两臂不是两个独立训练重复；整个设计仍受旧结果启发，不能称为独立构思的确认性研究。

训练保留现有随机采样与真实更新。每个 episode 结束时保存其真实 terminal transition，再按本臂自己的 reset 同时取得新 observation 和 global state，清理该 lane 应重置的技能/recurrence/segment 状态；不能混用旧 terminal state 与新 observation。不得在 H 的每次公开 renewal 上额外 reset 内部网络状态。采用现有 episode key 推进，五个 rollout 不反复使用同一组训练 episode。

两臂都保留 `use_obsnorm=false`、`use_statenorm=false`、`use_valuenorm=true` 的配置。ValueNorm 在本臂训练中按既有规则更新，不能把某一臂的训练统计拷给另一臂。最终评价使用各自训练结束时的活动网络与启用 normalizer，按既有独立 evaluator 路线同步，`train(False)`、deterministic action、清空 buffers、逐 lane reset；评价不更新训练统计或干扰 learner RNG。新评价 batch 为32，使用训练之外、也不复用已观察 A01 面板的三十二个配对 keys，三个策略各有自己的 host/plan/state。G 仅作这一次新学习比较的公共参照，不是重跑旧 A01 面板。（[E2 runner，CorridorEvaluator 的构造、_sync、_reset_lanes][e2runner]；[A01 原卡，§3][card]；[A01 runner，evaluate][a01runner]。）

以上是新比较所依赖的输入、reward 和状态语义，不是声称 H_train 已有可直接执行的训练实现。本次所读源码提供真实 learner/update 路线和完成过的 native-mask 测量路线，二者的训练衔接仍需后续实现。新方法不依赖旧 checkpoint 的完整 RNG/hidden 快照，也不继承重演旧历史或再次验证其 pickle 恢复的义务。

## 四、规模与读数：只问早期学习，不冒称已学充分

我选择五个 rollout，而不是先做一个再按结果决定是否加到五个。现有 `_execute` 每轮调用 `run_rollout(update=True)`：第一个 rollout 的数据是在首次更新之前采集的；只有一个 rollout，观察重心更接近随机初始化加一次更新后的表现。五个 rollout 让更新后的策略多次采集各自实际环境反馈，同时仍大幅小于旧二十轮矩阵。**五轮不是充分学习或收敛保证，而是为“经历反复真实学习后，早期控制包差异是否仍值得投入”选择的有限起点。** 不据其阴性关闭所有更长训练，也不因短预算自动把一个不利结果宣告无意义。（[E2 runner，_execute 的循环与 endpoint evaluation][e2runner]。）

使用准备文件已计算的 L=5 尺度；L=1 只是被比较后未选择的替代，不是另一个 rung：

| 工作 | 本次选择的有限设计 |
| --- | ---: |
| 新的配对训练 seed | 1 |
| 新 trained arms / 真实训练开始 | 2：C_train、H_train / 2 |
| 每臂 rollout × lanes × H | 5 × 16 × 400 |
| 每臂训练 transitions / episodes | 32,000 / 80 |
| 两臂训练总 transitions / episodes | 64,000 / 160 |
| 每个 trained arm 的最终评价 | 仅一次，32回合、12,800评分步 |
| G 的同期公开参照 | 32回合、12,800评分步，零训练 |
| 评价合计 | 96回合、38,400评分步 |
| 训练加评价的环境步口径合计 | 102,400 |
| 相应 agent-step observations | 614,400 |

这些是设计计数，不是本轮新执行量；训练 transitions 沿既有 runner 的 H×lanes 口径，参考 host 的外生区域转移每回合为 H−1，不能把二者当同一计数。每臂五个 update 阶段不是五次 `optimizer.step`；真实 optimizer 调用、coordinator/individual/team segment 数必须由运行记录给出，不能用环境步代替。（[EXPOSURE_AND_COST.json，illustrative_real_B_scales 中 L=5 项][counts]；[E2 runner，optimizer counters、rows_M、exposure_line][e2runner]。）

保留每轮训练回报、每个真实网络的更新次数和既有相对初始化 exposure line，至少清楚展示首轮与最终位移。参数运动表明更新发生，不认证学习充分。无中途 checkpoint 选优、无额外中间评估面板，只在第五次更新后的固定终点评价。五轮训练曲线不伪装成五个独立训练 seed。

主量仍是新训练后原生完整回报的配对差：对新 episode e，`R[p,e]=sum(t=0…399) r[p,e,t]/400`，`d[e]=R[H_train,e]−R[C_train,e]`，报告三十二个 d、均值及 `std(d,ddof=1)/sqrt(32)`。该 SE 条件于这一对新训练好的策略，不估计训练 seed 总体不确定性。不得与旧 A01 的 .26935 做跨检查点“保留率”推论；两次比较的权重、训练经历和样本都不同。

同时报告 post-reset 的 `/399` 回报、H_train−C_train、G−H_train，并保留 C_train 到 G 的差距。对两个 trained arms 分别给出 KEEP/fresh 机会数、wrong-role 数、条件错误率及回报单位损失 `Delta×wrong/(399×N)`；没有 eligible 机会时率为不适用，不记作零错误。内部与实际 renew 数分开。G−H 与 wrong-role 损失的对应按实际结果核对，其含义仍限于奖励核算；不要求全 action/logit/hidden tape，也不把这个对应升级为唯一 actor 缺陷。（测量定义复用 [A01 原卡，§4][card] 与 [A01 runner，evaluate/summarize_panel][a01runner]。）

我为这个新问题选 **.01 absolute mean native reward** 作为描述性 MEI：在 Delta=1 时是一个百分点的平均服务，大于单步 reset 的 .0025 尺度。它不是自动继承的旧分支、显著性或等价线，也不是投资硬门槛；原 A01/E3 的规则完全不改。报告尺度内效果和不确定性，不要求事先显著、每个 episode 改善或超过 G。缺少 tuned generic headroom 如实保留，不补作强制 baseline tuning。（[证据规范，§11.7–11.8][spec]。）

## 五、下一条观察能改变什么

本比较观察的是**真实训练与部署两套控制规则后的总差异**。没有零更新随机策略臂或训练/评价交叉替换的因子面板，因此不单独证明差异由“学习获得”，也不识别公开规则的直接效应、不同数据分布和不同更新暴露各占多少。放弃这些更强归因，正是两臂小 B 而非大诊断矩阵的代价。

| 新的完整可信 B 读数 | 能支持的方向内判断 | 仍不能说的结论 |
| --- | --- | --- |
| H_train 的原生回报优于 C_train，同时如实报告 G 残差和角色损失 | 公开 applied-renewal hybrid 的局部收益不只出现在被挑选的旧 artifact；它在这次从头训练及早期预算下也有可实现差异，可作为另行评估重复性或性能比较的候选 | 不能称为学到公开 renewal 规则、D2 机制成功、超过 D0 或稳定优势 |
| H_train 改善 C_train，但两者仍远低于 G，H 角色损失仍大 | 保留局部控制包收益；不把增加 duration 复杂度当作恢复完整 competence 的依据，后续投资必须承认实际剩余服务短缺 | 不能把余差全归 actor、recurrence、team 或 credit，也不能因为局部正值自动加训练量 |
| H_train 不优于 C_train，或收益反转 | 旧固定权重收益没有在这次早期从头学习比较中形成同向优势；不以 A01 为理由自动延长这一 hybrid 路线 | 不是所有 seed/预算上的无效定理，也不推翻已完成 A01 的测量事实 |
| 结果很小、回合符号混合或分辨率有限 | 保留真实有限读数，结束此对象；是否再问问题须有新的决策价值 | 不把不显著写成等价，不加回合或换 seed 追求正号 |

这些是描述性结果解释与投资含义，不是新 C 式消费规则，也不要求一个不利 seed 被排除。一个 seed 不能回答稳定性，但可以给下一个有限决策提供比旧权重更多回合更相关的信息。没有任何一行自动批准第二个 seed、D0 arm、更长预算、同步 termination 或新 host；本次终点就是这对真实学习比较的完整 intake。（[证据规范，§11.8.2–4、§11.9][spec]。）

## 六、成本边界：完整调用，不把未知项移出账面

主导工作是两个 learner 各五次真实 collection/update、两个三十二回合的独立终点评价，以及一次三十二回合 G。内部每步 coordinator/actor 调用与原六实体 decode 属于算法工作；没有候选策略搜索、joint-action 枚举、未来 trajectory 分支或嵌套 solver。新增验证只覆盖改变的 applied-mask 到真实 storage/update、fresh state 和主回报输出，不另做科学验证矩阵。

现有成本证据只能作为尺度。旧 E3 的每臂经验式是 `1.15×[L×(64.6+.769×M)+.46×E]` 秒，其中这里 E=32；M 是旧式中的 coordinator 更新工作变量，不是 `k_max`，也不能直接把 `rows_M` 当成同一个量。新 C/H 的有效内部 duration、segment 和 optimizer 次数未测定。旧所选 E3 的 mean rollout 为 85.03268997474952秒，完整二十轮加3,584评价回合 runner 为2646.4799736300047秒；用旧均值和 `.46×32` 拼出的 L=5 历史锚是 **505.86596735480975秒/learned arm**，L=1 是114.71559347096193秒。它们不是新 H_train 的已测投影，也没有证明新初始化、独立 evaluator、发布和变化后的更新工作会在某个秒数内完成。（[EXPOSURE_AND_COST.json，existing_runner_cost_law、historical_same_node_cost_anchor][counts]；[E3 runner，cost_law][e3runner]。）

P21 的外层 G/C/H 墙钟为 .27/20.44/18.19秒、合计38.90秒，确实包含了那次面板的加载、评价与发布，却不为新学习 co-adaptation 定价。E4 的 DP 秒数更不能移来定价 learner。未知的新成本保持未知，不增加单独 cost probe、profile 或 checkpoint 面板。（[A01 result，Counts, receipts and actual cost][result]。）

**为本次选择的下一问题，采用每个完整 learned-arm invocation 最多900秒，G 的完整 reference invocation 最多60秒；三者 summed invocation wall 上限1860秒。** 这是本次对有限问题所选的设计边界，不是运行预测、已通过的资源准入或可挪用的旧预算。选择有限上限的依据是：只愿意为一次五轮早期判断投入这一有终点的工作，而不是恢复旧二十轮或八小时每臂矩阵。旧约506秒锚只能说明量级，不能保证900秒足够。它也不使这个 B 必然比已经完成的38.90秒面板便宜；后者已经回答另一问题，重复它不能新增训练证据。

每个 learned arm 从 interpreter/import、配置和模型/optimizer 创建开始计入完整墙钟，包含全部训练、必要终点评价、normalizer 同步、必要主比较读数和结果发布。采用独立 evaluator 所产生的额外模型创建也在本臂账内；本设计不需要旧 checkpoint load。不能先在“工程验证”里初始化实际 learner，再只给训练计时；不能把终点评价或 publication 移到 cap 外、切片重启或以并行化掩盖每臂费用。G 的 setup、reset、评价与发布同样计入其60秒。后续实际卡及分配保留这些完整调用语义，不能称为已经获得本轮执行额度。（[证据规范，§11.9][spec]；[P25 handoff，Budget/return][handoff]。）

完成五轮及一次终点评价并完整发布后停止；达到任一完整调用 cap、发生非有限学习/主回报，或有实际错误损害本臂 reward、信息权限、真实更新或主要配对输出时，停止相应依赖工作并返回具体事实。不得自动提高上限、减轮后冒称完成五轮、复用部分运行拼出完整对象、替换 seed 或追加测量。若某一臂未完成，不能给完整 H_train−C_train 极性；已经独立可信的另一臂或 G 读数、真实完成量仍保留。不利但有效的完整结果不是 quarantine 理由。可选 RSS 缺失亦不能抹去独立可信的原生回报。（[证据规范，§4、§11.8.7][spec]。）

实际执行仍须在所用节点每次 invocation 前满足既有 physical/effective ≥4 GiB 准入。采用原 CPU/四线程与既有 float32 learner、float64 host/reward 语义，不在本问题顺带选择 GPU、精度或并行方案。若真实新路径无法在上述范围完成，应回到该问题与充分证据的价值判断，不自动立项更大性能工程。

## 七、历史反证、仍存解释与实现边界

E3 仍为18/18有效 adaptive B。六个 competent medium/large 配对全负；large 的三项 D2−D0 为 −.071387329、−.108895874、−.086455282，D0/reference 均超过原 .85线，原第四分支 E3-H0-NO-ADVANTAGE 不变。它只关闭 c=c_Z=.25、原大行、二十轮/128,000 transitions每臂的声明。原累计路径 false/true/false 与另报最终窗口 false/false/true 都保留，尤其被选 large seed2 有累计路径却仍亏损。small seed2 对合格 D0 的 **+.033291585** 和 E2 的单调 duration control 是保留的学习支持；small seed3 的 +.062728760 与其不足 .85 的 .814254153 ratio 同样保留，但不支持 superiority。（[E3 result，Paired final returns、Regional event path、Frozen rule][e3]；[DIRECTION，Accepted mechanism-level science][direction]。）

旧 medium/large D0 的 actor/critic 各72,000更新，D2各9,000，是实际暴露差异，不是原结果的新有效性缺陷，也不证明匹配次数就会修复它。本次 C/H 保留 schedule 而报告实际次数，仍不单独识别 optimizer exposure 的因果贡献。旧参数相对初始化的非零位移和所选检查点的128,000 transitions、4350/9000/9000/300/1200组更新，均不认证新 H_train 已具角色能力。（[E3 result，Validity、Exposure][e3]；[EXPOSURE_AND_COST.json，retained_checkpoint_training][counts]。）

E4 的三 law/288候选/零learner完整 A 也不变；公开 greedy 完全解释那两项约 .0971/.0982 的 reactive-over-best-clock 结构机会。这个事实继续阻止“结构 gap 本身证明需要学习 policy gap”的推论，但不是整个 learned-policy class 的无价值定理。只匹配名义均值不构成 variance-only intervention，rounded-lognormal 的浮点 residual mass=0 不证明无穷尾为零。本次不重复 census，也不选择该 renewal-law 人口；所选 B 仍在原 Bernoulli 大行。（[E4 result，Population、Law facts、Frozen rule][e4]。）

最强当前支持是 A01 的真实局部 native gain；最强当前反证是 **H 的 .16403 剩余 G 差距、H 更高的 wrong-role loss/rate，以及六个 competent E3 学习亏损**。噪声 gap、actor/representation、recurrence、不同训练轨迹、team-renewal interference 和 optimizer exposure 仍未分离。新两臂设计不会完整分离它们；它只将“旧失利权重上的控制测量”推进到“新真实学习后的有限控制包比较”。不为未解决的原因增加 actor census、旧轨迹重放或新 architecture。

Tuned same-information generic baseline headroom 仍缺失。E3 的 upper−trained-D0 .098784120/.175543309/.336673587 包含原结构 margin 和 learner 短缺，不能等同于 A01 的新 H−C，更不能替代新小预算的公平 baseline。缺失不是零，不是此次必须先训练补齐的门槛；本次也不声称产出完整 tuned baseline package。（[E3 result，Exposure, headroom, cost][e3]；[证据规范，§11.7、§11.8.1][spec]。）

现有 `_execute` 确有真实 collection/update、optimizer counters 与同步 evaluator；A01 runner 确有已完成的 applied-mask／own-state／reward 读数，但只有 evaluation。**新 H_train 的训练衔接、完整调用计时和输出实现尚未交付、未测，不由源码存在推定已可运行。** 后续只需针对实际改变的 action→reward/storage/update 和主输出做有目的的检查，复用未变路径，不默认复制 E2 的全部历史 census、digest、检查点恢复或诊断字段。不加 resume 服务、guard/registry、反复 smoke 或单独成本实验。源码、runner与测试仍受现行工程预算约束；30%编排比例是 review signal，不是自动退回门槛，也不重新要求100行例外申请。（[E2 runner，_execute、CorridorEvaluator][e2runner]；[A01 runner][a01runner]；[工程规范，§4–5][engineering]；[证据规范，§11.8.6–8][spec]。）

准备文件中的 ACAC/UTE 检索只用于区分 intra-option action、termination 和 applied actuator。本节点只读了该文件所记录的190-record检索范围和选文限制，没有独立复核其本地论文原文；不据此诊断 FSD、宣布新颖性或引入它们的架构。省去新的文献/支持集/原因普查，放弃的是这些更强结论，不是放弃真实训练和原生比较。（[PREPARATION_INTAKE，Question-driven source retrieval and its effect][preparation]。）

## 八、本轮访问与最终边界

科学读取均使用固定证据版本 `1db0df54cf19b0a9eb300468144fab7eb8abbd29`，任务定义使用其指定固定版本。下表是实际访问的全部十七个科学/准备路径与重点范围；长文件按相关章节或函数读取，并非声称审查完整依赖树。无列出路径的访问缺口。

| 实际读取路径 | 使用范围 |
| --- | --- |
| [docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_CONTROL_A01_INTAKE_20260907.md][intake] | §1–7，重点原分支、限定解释与待决学习问题 |
| [docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_CONTROL_A01_RESULT_EVIDENCE_20260907.md][result] | 原生回报、服务核算、原规则、counts/cost及记录限制 |
| [docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_CONTROL_A01_SCIENCE_CARD_20260907.md][card] | §1、3–7及相关配置，旧 P21 定义不改写 |
| [docs/research/candidates/flexible_skill_duration/pro_packets/20260907_native_renewal_convergence/archive/RESPONSE.md][previous] | 前轮有限选择、§三–七的状态/比较/停止语义 |
| [docs/research/candidates/flexible_skill_duration/DIRECTION.md][direction] | 接受的 E3/E4、暂停与有限重入、A01测量边界 |
| [docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md][e3] | 配对表、路径窗口、原分支及 exposure/headroom/cost |
| [docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md][e4] | 完成状态、公开 null、有限数值语义与原规则 |
| [docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/PREPARATION_INTAKE.md][preparation] | 建议与反方、局部文献记录、工作/费用与准备边界 |
| [docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/EXPOSURE_AND_COST.json][counts] | 全部零新增暴露、保留暴露、两个未选规模及旧成本锚 |
| [scripts/run_fsd_native_renewal_control_a01.py][a01runner] | apply_renew_mask、load_controller、evaluate、summarize_panel及无训练路径 |
| [scripts/run_flexible_skill_duration_e2.py][e2runner] | CorridorEvaluator、_execute 的真实 learner/update、计数与终点评价 |
| [scripts/run_flexible_skill_duration_e3.py][e3runner] | arm_parameters 和记录的旧 cost_law |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §3–4、5.1–5.2、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][engineering] | §4–5的现行工程范围和比例/预算规则 |
| [AGENTS.md][agents] | focused reading、§2–4 decision ladder与既有 delegation |
| [docs/research/portfolio/handoffs/2026-09-07-p25-fsd-native-control-convergence.md][handoff] | 本轮唯一方向问题、交付与零科学执行边界 |
| [docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/ISSUE_SNAPSHOT.json][issue_snapshot] | 区分历史 P14 discussion/旧交付与本轮问题 |

A01全部三十二回合及候选结果的保留、算术和运行接受来自已读取的冻结结果/intake；本节点没有越过清单另读原始模型、原始回合数组或本地论文，也没有独立重算、重演训练或再跑环境。Issue的历史 P14 body与旧交付不能代替本轮 P25 结果后任务。

准备记录的机器生成新增暴露为 **scientific invocations、model constructions、checkpoint loads、training starts/transitions、optimizer steps、evaluation episodes 全部0**；本咨询维持这一事实。P21已有96回合、38,400评分步、230,400 agent observations、两次load与零训练，以及旧检查点训练暴露，都仍属于各自历史记录。上面选择的新 B 工作量和完整 cap 是下一问题的设计，不冒称本轮已消费或获准调用。（[EXPOSURE_AND_COST.json][counts]。）

**最终选择因此是一次有限真实学习继续：C_train 对 H_train，一个新的配对训练 seed，五轮/每轮十六环境/四百步，终点各三十二回合与同 keys 的 G，完整 learned-arm 900秒、G 60秒、合计1860秒上限。** 它只开放这个公开 applied-renewal hybrid 的早期 B/EXPLORE 比较，不开放普通家族其他实验；不新增同步技能/credit、D0 trained arm、host 或 UAV 动作。后续真实读数同时保留局部收益、G短缺、wrong-role损失、所有训练结果和实际 optimizer exposure。E3 bounded H0、E4完整 A 和 A01原第二分支一并保留；没有把一个条件 A 变成学习优势或以其正号预先保证新 B 成功。

[intake]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_CONTROL_A01_INTAKE_20260907.md
[result]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_CONTROL_A01_RESULT_EVIDENCE_20260907.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_CONTROL_A01_SCIENCE_CARD_20260907.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/pro_packets/20260907_native_renewal_convergence/archive/RESPONSE.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[e3]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md
[e4]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md
[preparation]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/PREPARATION_INTAKE.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/EXPOSURE_AND_COST.json
[a01runner]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/scripts/run_fsd_native_renewal_control_a01.py
[e2runner]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/scripts/run_flexible_skill_duration_e2.py
[e3runner]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/scripts/run_flexible_skill_duration_e3.py
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/AGENTS.md
[handoff]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/portfolio/handoffs/2026-09-07-p25-fsd-native-control-convergence.md
[issue_snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/1db0df54cf19b0a9eb300468144fab7eb8abbd29/docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/ISSUE_SNAPSHOT.json
[task]: https://github.com/CartmanFatass/My-paper-code/blob/c3fb335a3af51ae156354209df1c9e3d8718c1c0/docs/research/candidates/flexible_skill_duration/pro_packets/20260907_post_native_control_convergence/TASK.md
