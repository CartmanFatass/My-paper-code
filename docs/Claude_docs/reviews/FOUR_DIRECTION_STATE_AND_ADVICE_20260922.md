# 四方向研究现状与建议 — 2026-09-22

**Abstract (English).** Owner-requested read-only advice on the state of the research after the
2026-09-21 four-direction assignment. Read from published `main` `be38b4842` and the
`codex/agent-count-generalization` branch on 2026-09-22; nothing was launched, no direction
record was edited, `flexible_skill_duration` stays rested, 0 fits. The four Codex DMs cannot talk
to each other by design, so the cross-direction view is the one thing nobody inside the round is
producing; that is what this note supplies. Four judgments: (1) this round is one training seed
per arm on three of four directions, and its contrasts (+.02 to +.06 J so far) sit inside the
spread the programme has already measured for the fixed-clock learner (three fresh fixed-clock
instances on S1 landed at .458, .497 and .543; five historical blocks SD .055; panel-to-panel
.06–.09), so "inside noise" is the expected outcome and the policy for that case should be
written now; (2) on Scenario 7 the learner is not yet competent (training return does not rise
over 30 rollouts, evaluation J ends below initialization, energy mechanisms never fire), so the
auxiliary-head comparison is being measured on an incompetent base and a reference floor/ceiling
is missing; (3) the agent-count direction's SET arm is, unintentionally, the first competent
matched-information flat learner on a UAV host, which is the comparison the programme has lacked
since the 2026-09-14 review; (4) three directions built three non-poolable fixed-clock baselines
with three different evaluation panels, which is the cheapest power to recover. One
recommendation on the order of work after the round, and five decisions only the owner can take.

**性质与范围。** Owner 要求"check the research.md and then give me your advice"。本文是只读建议：
没有启动任何实验，没有编辑任何方向记录，FSD 继续 reserve，本会话 0 fits。所有数字来自已发布的
notebook、runner 摘要与归档，来源见附录 B。标签沿用上次：`[READ]` 我亲读的一手记录或代码；
`[HYP]` 我的推断。上次建议（`TEMPORAL_ABSTRACTION_PARADIGMS_AND_HMASD_DIRECTIONS_20260921.md`）
已由 Root 在 2026-09-21 归档中核对，采用三项、纠正五项；本文第 7 节据此更新我的立场，不重复上次内容。

---

## 0. 结论先行

1. **这一轮是"每臂一个训练实例"的探索轮，结果多半落在噪声内。** 三个 S1 方向各只买了一个种子
   （ACG 例外，计划每臂三个）。项目自己测过的固定时钟学习器分辨率是：跨种子 SD ≈ .055–.08，
   同一 fit 内面板间 SD ≈ .06–.09；本轮三个新的固定时钟 S1 实例分别落在 .458、.497、.543。
   目前出现的臂间差 +.021/+.051/+.062（ACG 首轮）都在这个范围内。这不是任何 DM 的失误，
   是设计的既定含义；需要现在写清楚"落在噪声内之后买什么"，否则四条线会各自以"无有用增量、停止配方"收尾。
2. **S7 上学习器尚未胜任。** detach 臂 30 个 rollout 的训练回报没有上升趋势（前 5 个均值 −755，
   后 5 个 −915），评估 J 终点 −645 低于初始化 −522，QoS 比例 .11→.23→.15→.15，返航约束代价 .23→.29 上升；
   充电/断电/耗尽事件全程为零。8 个评估世界的 J 标准差 ≈ 500，均值标准误 ≈ 170–200。
   在这个基座上比较辅助头，读不出任何东西；S7 需要先买"胜任 + 参照"，再买头。
3. **ACG 的 SET 臂是项目第一次拥有"能学会的同信息 flat 参照"。** 2026-09-14 评审指出层次结构从未
   在稠密奖励 UAV 宿主上对 flat MAPPO 检验过；FSD 的 CF 始终没学会（.14/.28）。SET 学到了 N6=.49、N4=.54。
   若这在三个种子上保持，H6−SET 就是项目缺了三个月的那个数字，其战略价值高于 ACG 本身的 N 泛化问题。
4. **三个 S1 方向造了三个不能合并的固定时钟基线，用了三套评估面板。** 这是本轮最便宜的可回收统计功效：
   一份共同的 S1 固定时钟参照配方 + 共同评估面板，让每条线的基线臂互为种子。
5. **建议的下一步次序：** 读完四个 B01 之后，把确认种子集中到 ACG（唯一有胜任 flat 参照、且带泛化轴的比较），
   LOE/JDSL 首轮只作探索读数；USA 先转入胜任/参照阶段。这是 Portfolio 层面的建议，需要 owner 触发。

---

## 1. 我读了什么 `[READ]`

| 来源 | 内容 |
| --- | --- |
| `docs/research/RESEARCH.md` @ `be38b4842` | 背景 1–7、四个 active 行、reserve/archived、现行计划 |
| `docs/research/archive/2026-09-21/RESEARCH.md` | temporal-learning、marl-concept-formation（含 Claude advisory reconciliation）、潜在方向 20 问、whole-project 计划 Decision |
| 四个方向 NOTES（main；ACG 读其分支 `codex/agent-count-generalization` 779 行） | 问题、Pro 问答、L0、B01 声明、已完成 fit 的读数 |
| `runs/uav_service_auxiliary/b01_detach_910021_a01/summary.json` | 4 个评估面板逐世界 J/QoS/约束代价，30 个 rollout 的训练回报，事件计数 |
| `docs/research/candidates/flexible_skill_duration/NOTES.md` | B01 五块 D1280/CF/D128 表、B03 熵机制、B12/B13/B14 与 03:52 收尾 |
| `baselines/scenario7_arm_a_2400000_metrics.json`；`envs/pettingzoo/relay/energy_aware.py`；`configs/config_1.py` S7 预设 | 历史 arm-A 数量级；启发式布局可行性检查；S7-S2 参数 |
| `docs/project/OPERATING_CONSTITUTION.md` | §2–5、§8 |

未读：四个方向的代码 diff、S7 环境实现细节、G33 冻结的具体范围。涉及处标明。

---

## 2. 四个方向现在在哪里 `[READ]`

| 方向 | 宿主 / 比较 | 已完成 | 进行中 / 待做 | 已读到的数字 |
| --- | --- | --- | --- | --- |
| `joint_duration_skill_learning`（JDSL） | S1，固定 k=10 / 充分知情分解时长 / 普通 AR 时长，团队 cap=10，时长菜单 1..10，360k/臂，CUDA | fixed（1 次技术失败 + 1 次修正后完成） | factored 运行中，AR 待启动；计划 4 次 | fixed J：0→.212，120k .483，240k .506，**360k .497**；wall 72 min |
| `local_observation_encoding`（LOE） | S1，原 encoder 对稠密槽位/关系 encoder，seed 92101，360k/臂，CPU FP32 | ORIGINAL | DENSE 运行中；计划 2 次 | ORIGINAL J15 .484，J30 .406，**J45 .458**；wall 95.5 min |
| `agent_count_generalization`（ACG） | S1，H6（完整 HMASD + 状态集合编码）对 SET（共享循环 PPO + 同节奏中央快照），训练 N=6，测 N=4/6/8，360k/fit | H6 914201，SET 915201 | H6 914307 运行中；计划 6 次 | H6 N4/N6/N8 = .558/.543/.466；SET = .537/.492/.403；**H6−SET = +.021/+.051/+.062**；rollout 30 时三个差全为负 |
| `uav_service_auxiliary`（USA） | S7-S2（8 UAV、30 用户、1 地面站、电池/充电、移动用户、无 S4 故障），k=10，1500 步回合，detach 对 joint，180k/臂 | detach | joint 运行中；计划 2 次 | detach 终点 **J=−645**，QoS .152，公共事实 MSE .0108；wall 139 min |

共同点：四条线都在两臂中采用了同一个共享正确性修复（低层循环 entry mask 由 `1−done[t]` 改为 `1−done[t−1]`），
历史 FSD 结果没有这一修复。四条线串行共用一台 RTX 4070 笔记本节点；剩余约 8 个 fit，每个 1.2–2.3 小时，
本轮大约在一天内读完。**种子的决定马上就到。**

---

## 3. 判断一：这一轮的分辨率，以及"落在噪声内"之后买什么

### 3.1 仪器 `[READ]`

项目对固定时钟学习器在 S1、360k 曝光下的分散度已有多次测量：

| 测量 | 数值 | 来源 |
| --- | ---: | --- |
| D1280 五个独立训练块的 J45 | .456 / .355 / .499 / .400 / .428，**SD .055** | FSD B01 |
| D128 五块 | SD .025；与 D1280 配对差 SD .074 | FSD B02 |
| 同一 fit 内面板间（fixed，rollouts 5…45） | SD .06–.09 | FSD B03/B04 读数 |
| 本轮三个新的固定时钟实例（不同代码路径、不同面板） | LOE ORIGINAL **.458**；JDSL fixed **.497**；ACG H6@N6 **.543** | 三个 notebook |
| 单个 fit 内的曲线摆动 | LOE：.484→.406→.458；JDSL fixed：240k→360k **−.009**；ACG SET N6：.531→.492 | 同上 |

2026-09-14 评审已算过：五个种子/臂只能可靠分辨 ≈ .125–.175 J 的效应。本轮 JDSL、LOE、USA 每臂一个种子，
ACG 每臂三个。所以，**除非效应 ≥ .15 J，本轮的预期结果就是"落在噪声内"。** 这与各 DM 的自我声明一致
（"one seed is exploratory"），我只把它放到全项目层面：四条线同时得到"无稳定增量"，不是四个科学阴性，
是一个仪器事实。

### 3.2 现在就该写下来的三件事

**(a) "落在噪声内"的分支。** 各 notebook 都写了"若无有用增量且无新区别则停止配方、不自动加种子"。
这条规则对单种子探索是危险的：它把"看不见"读成"没有"。建议 owner 在本轮读分之前定一条项目层面的规则：
单种子探索的结果只分三类——**效应大到单种子可见（≥ ~.15）／方向一致但幅度在噪声内／技术失败**；
第二类的默认后续不是"停止"，而是"进入种子分配决策"（第 8 节），由 owner 决定把种子给谁。

**(b) 一份共同的 S1 固定时钟参照。** 三条 S1 线各自造了一个"完整 HMASD 固定 k=10"基线臂：
LOE 用 D1280 原配方，JDSL 用新的 duration adapter 的 fixed 模式（critic 多了承诺上下文），
ACG 用 count adapter 的 H6（状态集合编码 + 共享 value head）；评估面板分别是 32 个世界（93101–93132）、
32 个世界（740000–740031）、每 N 16 个世界。三个基线互不可合并。若把"S1 固定时钟参照"冻结为一份配方 +
一份种子清单 + 一份评估面板，写进 RESEARCH 共享背景，此后每条 S1 线的基线臂按它原样运行，
基线种子就会跨方向累积。这是不花新钱的功效。它属于跨方向协调，DM 各自做不了；需要 owner 或 Root 定 `[DECIDE-1]`。

**(c) 把 SET 纳入这份参照。** 见第 5 节。

---

## 4. 判断二：S7 上学习器尚未胜任，辅助头比较建立在它之上

### 4.1 detach 臂的实际读数 `[READ]`

| rollout | 评估 J（8 世界均值） | 世界间 SD | 均值 SE | QoS 比例 | 返航约束代价/步 | 公共事实 MSE |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | −521.7 | 486 | 172 | .114 | .227 | .0028 |
| 10 | −283.5 | 502 | 177 | .228 | .204 | .0073 |
| 20 | −555.8 | 568 | 201 | .153 | .258 | .0015 |
| 30（终点） | **−645.0** | 484 | 171 | .152 | .287 | .0108 |

- 训练回报（随机策略，4 lanes/rollout）：30 个 rollout 中没有上升趋势；前 5 个均值 −755，后 5 个 −915。
- 逐世界：终点 J 从 −1686 到 −206；世界 920007 在四个面板都是最差（−1344/−1346/−1780/−1686）。
  世界异质性远大于训练带来的变化。
- 充电 UAV 数、断电事件、耗尽事件：训练与评估全程为 0。电池机制在 1500 步回合、S2 预设下没有触发；
  返航约束代价在付，但约束从未真正绑定。
- 曝光：180k transitions。历史 arm-A 参照（S7-S3、k=50、reward v1、200 Wh，不同预设与奖励版本，只作数量级）
  在 2,400,000 步评估：中位回合奖励 +74，q10 −178，QoS utility 均值 .143。本轮曝光是它的 7.5%。

### 4.2 这意味着什么 `[HYP]`

- joint 臂即使读出 +100 J 的差，也在 8 世界 SE（≈ 170–200）之内；按世界配对能压一部分，
  但压不掉训练种子方差。**这个比较在设计上读不出辅助头的效果。**
- 更根本的是基座：训练回报不升、终点低于初始化，说明当前 180k 曝光下的 HMASD 在 S7-S2 上没有形成
  能被"改善"的控制器。B/UCOPE 的教训（局部预测改善不转成完整收益）在这里甚至还没到检验的地步。
- S7 被选作宿主，理由是它有真实的团队耦合：接入—回传、能源与充电竞争、返航接替。本轮实际激活的只有
  接入—回传（QoS .15 对目标 .9）；能源耦合在这个预设与回合长度下是惰性的。若要主张"能源约束下的协作"，
  要么换到能触发它的预设/回合长度（科学变更，需声明；G33 冻结范围我未核，须 DM 核对），
  要么把主张缩到接入—回传。

### 4.3 建议

1. **先补参照，零训练成本。** 代码里已有启发式布局可行性检查（`estimate_heuristic_qos_feasibility`，
   通过的布局须达到 .9 的 QoS 目标，S7-S3 测试中断言可行），adapter 已暴露，但 B01 runner 没有报告它。
   在 8 个评估世界上跑这个检查，得到 QoS 与 J 的"可达上界"；加上 arm-A 的数量级，J=−645 才有意义。
   COPA 之所以能说"学习器比手写基线差得多"，是因为它有一个手写基线；S7 现在没有。
2. **先买胜任，再买头。** 下一笔 S7 投入应是学习曲线：把一臂（detach 即可，它就是普通 HMASD）延长到
   训练回报出现趋势为止，或证明 3–5 倍曝光下仍不动。这一步决定 S7 是否是可用宿主；在它之前不再买第二个辅助变体。
3. **joint 臂读完就停在读数上。** 它已在跑，读完记录；不据此加种子、换窗口或换目标。

---

## 5. 判断三：ACG 无意中给出了项目缺失的"层次 vs 有能力 flat"比较

### 5.1 事实 `[READ]`

- 2026-09-14 评审的核心发现：层次结构前提从未在稠密奖励 UAV 宿主上对 flat MAPPO 检验。
  FSD B01–B04 的 CF（中央快照 flat）从未学会：J45 .14（B01）、.28–.29（B03 修熵之后），
  策略几乎不离开初始化。D1280 对 CF 的 +.29 因此是"对一个不学习的对照"的数字。
- ACG 的 SET：共享循环 PPO，每 10 步拿到与 H6 协调器相同的中央快照（全局状态 + 联合观测，集合编码），
  每步拿到局部观测，无协调器/判别器/发现目标。**它学会了**：N6 .492、N4 .537、N8 .403，
  都远高于初始化（.154/.246/.087）。
- H6−SET 首轮：+.021/+.051/+.062；rollout 30 时三个差全为负（−.005/−.006/−.034）；
  SET N6 从 .531 回落到 .492，其记录的动作熵升到 8.43。

### 5.2 含义与两点提醒 `[HYP]`

- 若 SET 的胜任在三个种子上保持，**H6−SET@N6 就是项目一直缺的那个数字**：完整 HMASD 对同信息节奏的
  有能力 flat，在稠密奖励 UAV 宿主上。它是包比较（技能 + 协调器 + 发现 + AR 对 集合 PPO），不是组件归因，
  但它是诚实的那种包比较。它的论文价值高于 ACG 自己提的 N 泛化问题。
- 提醒一：**SET 的后段回落与 B03 的机制同签名，而且设置相同。** B03 发现 CF 的评估回落来自 λ_l=.05 的熵项抬高
  动作噪声，降到 .005 后回落消失。SET 记录的 `lambda_l` 就是 .05 `[READ, runs summary]`（H6、LOE、JDSL 的固定臂
  也都是 .05，即 D1280 配方；原论文用 .01）。所以首轮 +.05 里可能有一部分是对照被自己的熵设置拖累，
  而 H6 因低层由技能条件化、且不是唯一在学的层，未必同样受影响。这不是事后换基线的理由，是读第二、三个种子前
  必须写进解释的一个已知混杂；若 ACG 之后要给 SET 补种子，值得同时买一个 λ_l=.005 的 SET 臂作对照。
- 提醒二：rollout 30 时 H6 全面落后、45 时全面领先，说明 ±.05 的差在这个仪器上会随终点选择翻转。
  ACG 已固定终点为 45，正确；但读者应知道这个翻转存在。

### 5.3 建议

- 把 SET 作为 S1 的 flat 参照写进共享背景（第 3.2(b) 的共同参照的第二臂），让 LOE、JDSL 以后也能对它读数。
  这两条线现在都没有 flat 参照，它们的"改善"只能相对 HMASD 自身。
- 若本轮之后只能给一条线买确认种子，给 ACG（第 8 节）。

---

## 6. 判断四：JDSL 与 LOE 各自能回答什么、不能回答什么 `[READ]` + `[HYP]`

**JDSL。** Pro 答复自己划定了范围："同一团队十步更新制度内，允许成员提前重选是否值得，以及 AR 是否比
充分知情分解多带来有限学习价值。它不是长于十步的时间抽象研究。" 这是对的，也意味着：
- 一个 cap=10 的阴性不回答"可变时长是否有用"，只回答"在十步窗口内提前重选是否有用"。
  FSD B07 已经看到 k=1 与 k=10 训练无差别；本轮很可能再看到一次同类结果。owner 应预先知道这一点，
  以免把它读成"可变时长问题已关闭"。
- 读分之前先看两个计数：`|S_j|≥2` 且至少两个成员各有多个合法时长的非退化联合事件数，
  以及实际执行时长分布。若非退化事件稀少，AR 对 factored 的差没有数据支撑，无论分数如何。fixed 臂这类事件为 0（按构造）。
- 正面的一面：这条线做了一次干净的工程——共同事件回报、采样前承诺条件价值、逐因子 PPO——它是可复用的资产，
  将来问"长于十步"的问题时不必重做。

**LOE。** 它问的是"同样的 104 个数，稠密槽位/关系编码能否改善有限学习"。读数要点：
- DENSE 多了一个注意力块，wall 会高于 ORIGINAL 的 95 分钟；"改善"要与成本一起读，notebook 已声明。
- 单种子；ORIGINAL 自己的曲线在 .41–.48 之间摆动。DENSE 落在 .40–.52 之间都不是信息。
- 若 DENSE 明显更高（≥ .55），值得两个补充种子；否则按第 8 节处理。

---

## 7. 范式层面：上次建议中我保留、撤回与更新的部分

Root 的核对（归档 "Claude advisory reconciliation 2026-09-21"）我逐条读了。

**接受的纠正。**
- B12 不是"场景 1 没有协调需求"的测量：它在固定训练基座上、按原协调器的状态依赖采样律拟合，
  非加性检查只有一个 homogeneity 项，标签未被随机化。我上次把它写成"函数 (ii) 为零"是过度推论，撤回。
- η² 不是策略梯度信噪比；"无切换费 ⇒ 有限学习无收益"不是定理；联合驻留的 k/n 在离散共同检查点上不成立，
  正确的量是首次有人重选前的检查数 1/[1−(1−p)^n]（p=.4、n=6 时 ≈ 1.05 次）。
- 四篇文献的边界不等于交叉领域为空。

**保留的判断，措辞收窄。**
- 联合技能在任何 UAV 宿主上是否有用，仍然**未测**（不是"为零"）。本轮四条线里，三条在 S1 上比较 HMASD 的变体，
  一条在 S7 上比较辅助头；没有一条直接测联合技能的互补性。ACG 的 H6−SET 是最接近的包层面替代（第 5 节）。
- 干预式测量仍然便宜，而且现在有了现成的检查点：LOE ORIGINAL 的最终权重（66 MB，本地与节点各一份）、
  JDSL fixed 的四个检查点、ACG H6 的权重。Root 要求"说明具体的状态、成员、技能替换、续接规则和新增评估成本"；
  附录 A 给出规格。它是诊断，不是门槛；Root 已明确不把它设为前置，我同意。
- 第 3.3 节的 2×2（可及性 × 耦合）仍是我看这四条线的地图：S1 三条在"可及但耦合未测"格，
  S7 一条在"耦合但当前不可及"格（第 4 节）。两格都没有同时满足。

**更新。** 上次我建议"B：联合技能分两段，先固定 k 让技能有用，再解开时间"。本轮 owner 选的四条线中，
JDSL 直接进了第二段（cap=10 的窄版本），没有第一段。我不再主张改变本轮；但本轮读完后，若 JDSL 是 cap=10 阴性、
ACG 的 H6−SET 在噪声内，那么"技能在 S1 上是否有用"就是被两条线同时绕过的问题，而它决定 S1 是否值得再买种子。

---

## 8. 这一轮读完之后怎么办

**推荐次序（一个建议，供 owner 决定）。**

1. 读完四个 B01（约一天内）。每条线按自己的预写规则读；不追加。
2. 先做第 3.2(b)+(c) 的共同参照与共同面板（工程，零 fits），再谈种子。
3. 种子集中：把 3–5 个确认种子给 **ACG 的 H6 对 SET@N6**（它有胜任的 flat 参照，且 SET 熵设置核对通过）。
   若 LOE/JDSL 出现单种子可见的效应（≥ .15），它排在 ACG 之后，用共同参照配方补种子。
4. USA 转入"胜任 + 参照"阶段（第 4.3 节）；辅助头问题保留，等基座学会再问。
5. 若 JDSL 是 cap=10 阴性且 ACG 在噪声内，回到"技能在 S1 上是否有用"（附录 A 的零 fit 诊断，或 Root 保留的
   固定 k 伙伴重组后备），再决定 S1 是否继续。
6. FSD 继续休息；本会话不启动任何东西。

**只有 owner 能定的事。**

- `[DECIDE-1]` 是否冻结一份共同的 S1 固定时钟参照（配方 + 种子清单 + 评估面板）并把 SET 作为其 flat 臂，
  写入共享背景。这是跨方向协调，DM 各自无权。
- `[DECIDE-2]` 本轮读完后触发一次 Portfolio review，决定种子集中到哪条线；以及单种子探索"落在噪声内"时的
  默认后续（第 3.2(a)）。
- `[DECIDE-3]` S7：是否接受 S2 预设下能源机制惰性的事实并把主张缩到接入—回传；下一笔 S7 投入是否改为学习曲线/参照。
- `[DECIDE-4]` 是否让本会话做附录 A 的零 fit 耦合诊断（只用已有检查点和评估 rollout；不训练，不改任何方向记录）。
  不做也不影响以上任何一条。
- `[DECIDE-5]` 是否让 Pro 对第 3、5 节做一次关键批评。第 3 节的仪器数字全部来自项目记录，第 5 节的"SET 熵机制"
  是待核对的假设。

---

## 附录 A. 零 fit 耦合诊断的规格（回应 Root："需说明具体…") `[HYP]`

目的：在一个已训练的 S1 检查点上，测标签组合的回报是否可加，即协调器是否有可协调的对象。诊断，不是门槛。

| 项 | 规格 |
| --- | --- |
| 检查点 | LOE ORIGINAL `final_checkpoint.pt`（sha256 `b11589ac…`，本地 `runs/local_observation_encoding/b01_original_s92101/`）；或 JDSL fixed 360k |
| 状态 | 该方向自己的 32 个评估世界，500 步，确定性执行，与其 J45 面板相同 |
| 成员与替换 | 一对成员 (i, j)，个体标签强制为 (a, b)，a,b ∈ {0..5}；其余四个成员照常由协调器分配；团队标签照常 |
| 续接规则 | 两种，分别报告：整回合常量（与 B12/B13 的 E 面板同规矩）；每十步在团队边界重新强制同一对标签（与训练时的十步制度一致） |
| 读数 | 36 格 J 表 → 双因素分解：主效应 SS_i、SS_j 与交互 SS_ij；报告交互占比 SS_ij/(SS_i+SS_j+SS_ij) 及其对世界的 bootstrap 区间 |
| 成本 | 每对：36 面板 × 32 世界 × 500 步 = 576k 评估 transitions；按 LOE 的评估速度（48k transitions ≈ 124 s）约 25 分钟 CPU；三对成员约 75 分钟。0 fits |
| 解释边界 | 只说明这个检查点上这些技能的可加性；不说明任务没有角色，不给新共同学习设上界（Root 的限定，我接受） |

判读：交互占比 < .1 → 在这个检查点上协调器没有可协调的对象，S1 上的联合技能主张需要换宿主或换技能；
≥ .3 → S1 上值得直接问"协调器是否学到了它"（B13 的问题，但这次有了非零的靶子）。中间值：报告，不推论。

## 附录 B. 数字来源

- FSD 五块与 D128：`docs/research/candidates/flexible_skill_duration/NOTES.md` B01（行 440–460）、B02（行 731–745）；
  B03 熵机制：同文件 B03/B04 综述（行 1362）；03:52 收尾（行 4252 起）。
- JDSL：`docs/research/candidates/joint_duration_skill_learning/NOTES.md` "B01 corrected fixed result accepted"。
- LOE：`docs/research/candidates/local_observation_encoding/NOTES.md` "ORIGINAL complete and read"。
- ACG：分支 `codex/agent-count-generalization` 的 NOTES "first completed fit — H6 seed 914201"、"second completed fit — SET seed 915201"。
- USA：`docs/research/candidates/uav_service_auxiliary/NOTES.md` "B01 detach complete and read"；逐世界与训练回报由
  `runs/uav_service_auxiliary/b01_detach_910021_a01/summary.json` 直接计算（`evaluations.*.native.worlds`、`training_rollouts`）。
- arm-A 参照：`baselines/scenario7_arm_a_2400000_metrics.json`。可行性检查：`envs/pettingzoo/relay/energy_aware.py`
  `estimate_heuristic_qos_feasibility`，`envs/pettingzoo/env_adapter.py` 转发，`tests/scenario7_events_certificates_test.py` 断言。
- S7-S2 参数：`configs/config_1.py` `_apply_scenario7_energy_preset`。
- 2026-09-14 评审的分辨率：`docs/Claude_docs/reviews/FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md`。
- Root 对上次建议的核对：`docs/research/archive/2026-09-21/RESEARCH.md` "Claude advisory reconciliation 2026-09-21"。
