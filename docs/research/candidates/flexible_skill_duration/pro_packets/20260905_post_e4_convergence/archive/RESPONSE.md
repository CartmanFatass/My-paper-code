REQUEST_ID=2026-09-05-fsd-post-e4-convergence-01
PINNED_REFERENCE=d990575470126c896ffb36db64cd1aab0dff08a2

# FINAL_DECISION=PARK

**暂停当前固定成员 K2 corridor 的 policy-gap interruption 学习收益探索分支；本节点不选择下一实验对象。**

最小适用对象族是：**现行 N6／K2／Z4／两区域／H400 corridor 中，公共 change flag 与 lagged cue 可恢复当前 latent、成员及区域归属固定、无 probe／churn／E5 coupling，并通过既有 HMASD coordinator—抽象技能—低层 actor 路径实施 D2 的这一探索分支**。本裁决针对以已完成 E3 三行和 E4 三种 law 为依据，继续追求 policy-gap 特有续约学习收益的研究推进；不否定直接公共续约规则的价值，不覆盖其他信息条件、其他 host 或整个 `flexible_skill_duration` 方向。相关对象边界见 `DIRECTION.md` 的 “Scientific question” 与 “Accepted mechanism-level science”。

**PARK 是可逆的科学对象族选择，不是新增经验阴性，也不是 Portfolio 生命周期登记。** E3 的阴性仍只关闭原定 `c=c_Z=.25`、大差异行、每臂 20 rollouts／128,000 transitions 下的声明；其他阈值没有因此被判为无效。E4 仍是完整 A/RECON，不升级为学习收益或方向关闭证据。

本次选择 PARK，而不是 CONTINUE 或 CLOSE，理由如下：

**新增 E4 已经回答了上次唯一选择的结构问题，却没有留下未被 public greedy 解释的同信息参考机会。现有 E3 学习失败仍未被因果定位；清单中的日志和执行接口，也尚未支持一个可直接复用、具有明确原生后果、足以区分这些原因的低成本干预。** 再做参考枚举是重复；直接增加训练则尚无比“也许这次能学好”更具体的判别依据。但 small seed 2 的合格正例和未分离的学习解释，又不足以支持整个家族永久 CLOSE。这里既不要求一般定理，也不把缺少 tuned headroom 当作停止投资的普遍门槛。

以下全部仓库引用均位于本次固定 reference；读取路径与范围列于末节。

## E4_RULE_READING

### 原规则得到 COMPLETE，不附加第二对象

依据 `FSD_E4_CENSUS_SCIENCE_CARD_20260905.md` 的 “Observations, numerical reading and predictions”，原规则依次检查完整性、按 `tau=1e-10` 标记数值差距、在三种 law 完成后停止。完整结果与三份原始 summary 均保留 `status=COMPLETE`；已发布的 reference discrepancy 字段均为零。接受 **3/3 laws、288/288 unique open-loop candidates** 的原完成判定，不加入学习门槛或新的结果分支。

| Law               | `J_switch=J_greedy` | 最佳 k |   `J_best_fixed_k` |             `m_dur` |        最佳 fixed−k20 |
| ----------------- | ------------------: | ---: | -----------------: | ------------------: | ------------------: |
| deterministic     |               0.381 |   20 |              0.381 |                   0 |                   0 |
| geometric         |             0.38005 |    5 | 0.2829504999999999 | 0.09709950000000012 | 0.04534486896341891 |
| rounded-lognormal |  0.3796748613706948 |    5 | 0.2814497251383473 | 0.09822513623234747 | 0.04561465590085298 |

确定性 law 的 `m_dur` 与最佳 fixed−k20 按原规则属于 **unresolved at the declared numerical resolution**；两个随机 law 的这两项均为正。`m=J_switch−J_open_best` 在全部 law 上为正，没有出现反向排序。不能把原规则中的 “unresolved” 改写为一个新近证明的、无数值限定的普遍等式定理。

因此，E4 的最小科学更新是：**在这三个有限参考模型中，确定性完整初始 dwell 与 k20 对齐；两个随机 law 存在 reactive-over-best-clock 差距，但使用 k20 单独比较还会额外混入约 .0453／.0456 的弱时钟短缺。** 这不是 D2 或 D8 的效果。原卡第三条已执行完毕，不存在待补的原 census 启动条件。

### 零学习暴露已逐文件核对

三份原始 JSON 的 `learner_exposure` 都明确记录：

`episodes=0, transitions=0, optimizer_updates=0, checkpoint_selection=0`。

三者均有 `seed=0, seed_active=false`。`scripts/run_flexible_skill_duration_e4_census.py::main` 明确构造这组零字段，执行路径只构造配置、law 和参考计算，不构造模型、优化器或 checkpoint。因而参数相对初始化位移 **不适用**，不是“位移很小”或“未报告的学习”。正式 108 次加校准 18 次 DP 调用是数值工作，不是 126 个 learner runs。

## E3_BOUNDED_RESULT_PRESERVED

完整 E3 的全部九个配对继续保留：

| 行      | Seed |             G＝D2−D0 |          D0／J_k |
| ------ | ---: | ------------------: | --------------: |
| small  |    1 |     −0.041736165365 |     0.942572765 |
| small  |    2 | **+0.033291585286** | **0.872613126** |
| small  |    3 |     +0.062728759766 | **0.814254153** |
| medium |    1 |     −0.016412597656 |     0.884807482 |
| medium |    2 |     −0.039020019531 |     0.935604294 |
| medium |    3 |     −0.053367187500 |     0.959050880 |
| large  |    1 |     −0.071387329102 |     0.885432842 |
| large  |    2 |     −0.108895874023 |     0.912487998 |
| large  |    3 |     −0.086455281576 |     0.884880388 |

这是 `FSD_E3_FULL_MATRIX_READING_CHECK_20260905.md` 的 “Paired arithmetic” 所记录的同一批观察，不是本节点重新运行得到的结果。small seed 3 保留为有效观察，但不能支持 superiority；small seed 2 是合格正例，不能被平均或家族裁决抹去。

按原 science card 的顺序，大行有三个合格 D0，因此不是 competence-blocked；没有合格正 G，因此不进入两个正向分支；三个非正 G 使第四分支 **`E3-H0-NO-ADVANTAGE`** 成立。此阴性仍仅限原阈值、原大行和原预算。

原 cumulative `event_path=false/true/false` 与另报的 final-window `false/false/true` 都保留，不换窗口。原路径阳性的 large seed 2 仍损失约 .1089；任一窗口一致应用都不改变这里的 H0。大行配对 episode SE 分别为 `.000880042921/.000737006906/.000721098273`，不是跨训练种子的置信度。没有新增 MEI、显著性门槛或 C consumption。

## PUBLIC_NULL_CONTAINMENT

### 被包含的是哪一个主张

`envs/relay_corridor/references.py::GreedyOnPublicState` 在 K2 使用公共 flag、lagged cue 和固定 zone 身份：事件发生时推得唯一的新 latent，选择相应原生 role 并续约；无事件时保持计划。`enumerate_references` 在 K2 直接复用 switching 的区域值作为 greedy 值。故：

$$
J_{\text{greedy}}-J_{\text{best fixed}}
=
J_{\text{switch}}-J_{\text{best fixed}}
=
m_{\text{dur}}
$$

是这项 census 的源语义与数值读取，而不是独立学习证据。

**因此不能再用这两个正结构 gap 支持“必须学习 policy gap 才能利用该机会”，或“该 gap 本身识别了 policy-gap 特有贡献”。** 一个合法同信息、无需训练的直接公共规则已经解释了整个已报告 switching-reference 机会。

但这不是说 public greedy 作为软件类形式上包含所有 D2 网络策略，也不是从 `J_greedy=J_switch` 推出任意学习器、预算和未来 host 上的全称无价值结论。它包含的是**当前被当作继续依据的原生参考行为及其收益解释**。

### 仍然不同的三个接口层次

| 层次                  | 已列源码支持的事实                                | 不能据此替代的事实                    |
| ------------------- | ---------------------------------------- | ---------------------------- |
| 直接公共规则              | 根据 flag／cue 直接输出原生 role 与 renew mask     | 不是学得的抽象技能选择器                 |
| D2 coordinator／技能路径 | 策略差距参与技能重决策，`d2_sampled_mask` 传给 adapter | 技能编号不因 `n_z=K` 就等于原生 role 编号 |
| 低层 actor            | 每步输出连续 K-vector，经 argmax 解码为 role        | 好的续约时机不自动保证 actor 给出正确 role  |

这一分层来自 `hmasd_driver.py` 的模块说明、`build_corridor_learner_config` 和 `run_rollout`，以及 `references.py` 的脚本接口。

完整的原生链仍是：

**区域事件 → 固定实体的 lease 失效，成员／区域归属不变 → 公共 flag／cue → coordinator 的抽象技能重决策与 sampled mask，同时 actor 产生原生 role → adapter 执行 RENEW／KEEP、支付一次零服务 step → service／shared reward → 连同原 step data 存入学习路径并更新网络。**

E4 的直接参考路径跳过学习环节，并没有证明上述 HMASD 链中哪个环节已经具备能力。`run_rollout(update=False)` 也只意味着该调用不做 optimizer update；driver 的构造仍会创建 agent，这个参数本身不是恢复旧训练策略的接口。

仍活着的问题是：**在一个明确学习目标与有限预算下，HMASD 的技能、actor 和续约路径能否学会并利用这些合法原生动作；D2 是否为这个学习过程提供了可识别的帮助。** E4 没有回答它，public greedy 的存在也不使它逻辑上不合法；但它需要自己的判别，而非重复结构机会论证。

## STRONGEST_SUPPORT / STRONGEST_CONTRADICTION / UNSEPARATED_EXPLANATIONS

**最强支持保留在学习观察中：**small seed 2 对合格 D0 的 `+0.033291585286`，加上 `DIRECTION.md` 保留的 E2 阈值控制段长事实。这足以阻止“D2 从来没有有限价值”的断言，却不识别收益来源或稳定性。E4 两个随机 law 的正 gap 支持的是时机问题仍有结构内容，不是 D2 的新增学习支持。

**最强反证是两个层面的合取：**E3 六个合格 medium／large 配对全部亏损，包括原路径阳性种子；E4 则表明新增随机时长参考机会完全可由 public greedy 解释。前者反对现行学习路径已有可靠收益，后者消除了“再换到随机 law，结构 gap 就是独立继续理由”的论据。它们不能被相加成一次更强类别的统一阴性试验。

尚未分离的解释如下：

| 解释                           | 当前支持的事实                                                | 未被识别的部分                            |
| ---------------------------- | ------------------------------------------------------ | ---------------------------------- |
| Policy-gap 噪声／不适当续约          | 事件响应不稳定，路径阳性也可亏损                                       | 未证明它是收益损失的主要原因                     |
| 优化暴露不足或不同                    | medium／large 每单元 D0 actor、critic 各 72k updates，D2 各 9k | 未证明匹配 updates 就会修复；差异不使原 B 结果失效    |
| Team-renewal interference    | team-gap 可使两区域共同重决策，已有 team 计数                         | 未估计独立改变 team 路径的因果收益               |
| Seed／representation／actor 质量 | 正负 seed 并存，原生 role 与抽象技能之间有学习映射                        | 未证明续约正确时 actor 已有足够控制能力，也未证明只是训练不够 |

这些均在完整 E3 的 “Validity, provenance and work” 与 “Regional event path” 中仍然开放。

机器生成的 final relative displacement 范围也已读取：

| 网络          |                18 单元的最终相对位移范围 |
| ----------- | ----------------------------: |
| coordinator |  .0553152482813–.166795515435 |
| actor       |   .405381783309–.869975205255 |
| critic      |   .388725326960–.933702345740 |
| team        | .0333875393170–.0679988057420 |
| individual  |  .0538310083276–.104735919177 |

它们说明网络确实移动，不证明收敛、充分学习或优化质量匹配。CM 复核仍是对同一批证据的算术与来源检查，不增加独立经验样本。

## NEXT_SINGLE_OBJECT_OR_NONE=NONE

### 为什么当前不选择一个看似便宜的接续

**重复参考计算没有新的学习判别。** 三-law census、完整时钟网格和 public greedy 等式已经完成。再计算同一差距，或仅再次确认直接公共规则可以产生该原生行为，最多补充执行一致性，不区分 policy-gap、actor、优化暴露或 team 干扰。

**现有记录不足以直接给出新的反事实收益。** `E3Recorder` 在运行中接收 lease freshness、role correctness、service 等实现路径信息；`regional_path_record` 输出区域统计。`E3Evaluator.run` 保留有序 episode returns，`_postprocess` 发布累计和最终路径。这里没有已证明可用的“任意技能替换后继续执行”的反事实接口，也没有证据表明已归档逐步 logits、全部替代技能的 actor 输出或相应反事实状态。不能把 realized stale-correct-role opportunity 直接计作修改续约后可回收的收益。

**adapter 的插入位置不等于现成的“仅修复 gap”实验。** 在 adapter 前替换 renew mask 可以定义一个新的原生执行干预，但它未必同步改变 coordinator 的技能重决策、内部状态及 segment bookkeeping；同时替换 role 又绕过了待诊断的 actor。这样的干预并非原则上不可研究，但必须明确它是哪个混合策略、改变什么状态、估计什么原生后果。当前清单没有提供已被接受的该比较，也没有证明旧 checkpoint、normalizer 与恢复状态可直接支撑它。

因此，本裁决不把“存在插入位置”写成“低成本判别已经就绪”，也不把这些未验证事实当作必须启动一轮新训练的理由。**这不是证明未来不存在有价值的诊断，而是当前没有选择一个具有充分新增判别价值的对象。**

### 具体再进入条件

再进入应提交**一个有实际执行依据的、同 host 的原生动作／学习路径判别**，而不是另一个结构 gap。最低需要同时说明：

1. **干预对象确实可操作。** 明确是原生续约 mask、抽象技能重决策还是 actor 的 role 控制，并给出该变量如何进入实际后续状态与收益的源码依据。复用旧 checkpoint 时，须有其读取、normalizer 和策略状态处理的具体依据；不能仅引用 checkpoint 文件名。
2. **一个结果能改变当前判断，另一结果也有不同含义。** 例如，在原生 role 能力得到实际支持的条件下，隔离续约路径的改变若恢复服务，可支持“可定位的续约实现短缺”；若不恢复，则不能继续以同一短缺解释现有亏损。role 能力没有被支持时，结果必须停留在更窄的控制／表示能力问题，不能归罪 policy gap。
3. **比较有独立的学习目的与有限成本。** 写明相对已完成 E3／E4 新识别的量、合法同信息 null、实际暴露和逐臂成本／停止规则，并保留全部旧结果。仅增加 updates、发现更大位移、提高事件相关性，或换一个有正结构 gap 的 law，不足以满足这一点。

这是**重新打开对象选择的证据要求**，不是本节点选择的实验，也不要求先完成一个未经选择的正结果。无需先证明超过 public greedy、提供一般最优性定理，或完成通用调优 baseline 集合。若问题改为 K3、隐藏／延迟信息、新 Q head 或改变 team credit，必须作为明确的新问题提出 RECAST；本节点没有选择其中任何一项。A/B 的方法负担仍依原规范，不新增 C-time 启动关卡。

## LIMITATIONS

### 数值、信息与 headroom

E4 只匹配名义均值，不是 variance-only intervention；完整初始 dwell 的 age0 相位没有被替换。rounded-lognormal 保留数值均值 `19.999999999999996`、方差 `687.3086223944757`、log location `2.495691739886703`、moment support cap `98296`、second moment `1087.3086223944756`、computed mass `1.0` 和 residual mass `0.0`。最后一项是浮点 `1−mass`，不是零无穷尾质量证明；moment cap 也不是 H400 下的 age399 边界。`tau=1e-10` 与均值一致性 `1e-8` 均非认证误差包络。

renewal host 的 **tuned same-information generic headroom 仍然缺失**。E3 的 upper−trained-D0 均值 `.098784120/.175543309/.336673587`，分别包含结构 margin `.057037446/.144357787/.271218984` 加上 D0 的学习短缺；不能移植为 E4 tuned headroom。缺少这项记录不是本次 PARK 的独立理由，也不是自动训练它的理由。完成的 E4 没有 learning MEI；本节点未选择新学习对象，因而不新增 MEI。

### 成本事实，不外推为新对象秒数

E4 原投影采用每 law 六次 H400 DP 样本：

$$
P=2\left(T_{\rm cold}+36\max T_{\rm sample}\right).
$$

| Law               |             已测投影秒数 | 正式 process wall 秒数 |
| ----------------- | -----------------: | -----------------: |
| deterministic     | 1.5478515890717972 |                .41 |
| geometric         |  .8055051176052075 |                .47 |
| rounded-lognormal |  2.926211677637184 |               1.47 |

原 calibration cap 为 120 s／law，census cap 为 300 s／law；实际节点 admission 均超过 physical／effective 4 GiB。正式总计 2.35 s，加 calibration .74 s 为 3.09 s，再加两个 verification process windows .72 s 为 3.81 s。这些窗口排除单独 mkdir 复现、SSH／调度／agent 开销与旧历史；投影只是经验启发式，不是最坏情况界。

E3 历史每臂式 `[20*(64.6+.769*u)+3584*.46]*1.15` 给出 `4177.651/6034.786/16646.986 s`，均低于原 8 h cap；18 个有效单元的 wall 总计 `66087.00043219907 s`。保留 `resources_unmeasured`，不作跨 host 速度比较。这些也不是某个新反事实或学习干预的已测成本。

本节点选择的新调用数为零；**未来判别成本仍未知**。E4 的 91 行复用与 13 项测试接受不自动覆盖后续实现；工程规范的 100 行复用例外既不授权新科学对象，也不证明新干预正确。

## ACTUALLY_READ_PATHS

**21/21 清单路径均通过 connected GitHub connector 在本次固定 reference 读取；无 connector、repository、ref 或列出路径的访问缺口。**

读取范围如下。原始 JSON 核对了配置、关键 law 字段、零暴露、参考值及完成／差距字段；不声称本节点独立重算或逐条复核了全部 288 个候选。完整候选覆盖采用已读取的结果和 CM 接受记录。

| 实际读取路径                                                                                                              | 本节点读取重点                                               |
| ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `docs/research/candidates/flexible_skill_duration/DIRECTION.md`                                                     | 当前 E3／E4 科学、家族与已完成边界                                  |
| `docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_SCIENCE_CARD_20260905.md`                           | 原 A 规则、公共 null、人口、成本与停止                               |
| `docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md`                        | 完整结果、候选覆盖、数值与暴露／成本                                    |
| `docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_INTAKE_20260905.md`                                 | 接受与原规则停止；未选择 successor                                |
| `docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_COST_PROJECTION_20260905.md`                        | 六样本投影、实际节点与计时窗口                                       |
| `docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_CM_TECHNICAL_RECORD_20260905.md`                    | 技术接受、原调用、测试及末节完成记录                                    |
| `docs/research/candidates/flexible_skill_duration/e4_census_20260905/census_deterministic.json`                     | 配置、law、`learner_exposure`、reference、候选片段、完成字段         |
| `docs/research/candidates/flexible_skill_duration/e4_census_20260905/census_geometric.json`                         | 配置、law、`learner_exposure`、reference、候选片段、完成字段         |
| `docs/research/candidates/flexible_skill_duration/e4_census_20260905/census_lognormal.json`                         | 配置、hazard 段、moments、`learner_exposure`、reference、完成字段 |
| `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`             | 原 B 分支、比较、预算与暴露                                       |
| `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md`          | 九个配对、路径、暴露、headroom 与成本                               |
| `docs/Claude_docs/experiments/FSD_E3_FULL_MATRIX_READING_CHECK_20260905.md`                                         | 配对算术、双窗口、18 单元 first／final 位移与计数                      |
| `docs/research/candidates/flexible_skill_duration/pro_packets/20260905_e3_complete_convergence/archive/RESPONSE.md` | 前 100 行：历史唯一 census 选择及“不承诺后续训练”边界                    |
| `envs/relay_corridor/config.py`                                                                                     | 固定归属、K2／renewal 配置与有限网格                               |
| `envs/relay_corridor/renewal.py`                                                                                    | 初始 dwell、hazard、有限校准与两个 cap                           |
| `envs/relay_corridor/references.py`                                                                                 | DP、枚举、public greedy、fixed／open 接口                     |
| `envs/relay_corridor/hmasd_driver.py`                                                                               | 模型构造、actor／role、sampled mask、存储及 update 路径            |
| `scripts/run_flexible_skill_duration_e3.py`                                                                         | recorder、evaluator、区域统计、发布字段与实际 CLI                   |
| `scripts/run_flexible_skill_duration_e4_census.py`                                                                  | 零暴露构造、校准、序列化与差距标记                                     |
| `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`                                                               | A/B、最小结论单位、§11 方法负担和描述字段                              |
| `docs/project/ENGINEERING_SCOPE_SPEC.md`                                                                            | §4 设施边界、§5 预算与复用例外                                    |

清单中没有新反事实比较的实现或结果，是**下一科学对象的尚未成立前提**，不是上述路径读取失败，也不妨碍本节点作出 PARK。

## DECISION_TEXT

> **REQUEST_ID=2026-09-05-fsd-post-e4-convergence-01**
> **PINNED_REFERENCE=d990575470126c896ffb36db64cd1aab0dff08a2**
> **FINAL_DECISION=PARK；DECISION_AUTHORITY=PRO_FINAL。**
>
> 暂停现行固定 N6/K2/Z4、公共 flag／lagged cue、原生 role／lease-renewal 条件下，经既有 HMASD 技能／actor 路径实施 policy-gap interruption 的学习收益探索分支。不选择下一对象，不执行 Portfolio 生命周期、优先级、容量或融合变更。
>
> E4 保留 COMPLETE A/RECON：三 law、288 候选、零 learner；确定性 m_dur 为零数值观察，两种随机 law 的 m_dur 约 .0971/.0982，全部 switching-reference 机会均由合法同信息 public greedy 解释。该结构结果不构成 D2/D8 学习收益，也不自动选择继续训练。
>
> E3 保留 18/18 有效 adaptive B 与原 `E3-H0-NO-ADVANTAGE`，阴性只适用于 c=c_Z=.25、声明的大差异行和原预算；全部六个合格 medium／large 亏损、small seed2 合格正例、small seed3 未达 competence 的正观察及两个路径窗口均保留。
>
> Policy-gap 噪声、优化暴露、team-renewal interference 与 seed／representation／actor 质量尚未被因果分离。现有原生接口提供新干预的可能位置，但现有记录不证明可直接利用旧 checkpoint 或日志进行该反事实比较。不以这个未知选择重复 census、额外训练或 D3/K3 等改写。
>
> 再进入需要一个源码与执行事实支持、明确隔离变量及原生收益后果、能够产生不同方向判断的同 host 学习实现判别，并诚实列出暴露和逐臂成本。仅有结构 gap、参数移动、预测相关性或增加预算不够；无需先取得正结果、超过 public greedy 或完成 C-time 义务。
>
> 21/21 清单路径访问成功。**本节点决定已形成，无访问 blocker；未执行代码或修改仓库。**
