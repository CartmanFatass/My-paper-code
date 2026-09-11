REQUEST_ID=2026-09-05-fsd-e3-complete-convergence-01
PINNED_REFERENCE=c64b2619978ca91b34917ea201a11e333553590a

# FINAL_DECISION：CONTINUE

**唯一下一方向动作：继续到一个无训练的、基于现有 E4 renewal/reference 的同信息原生动作机会 census，证据类别为 A/RECON。不开启 E4 学习矩阵，不重跑 E3，不转向 D3。**

最小适用对象族是：`flexible_skill_duration` 中，**固定成员、K=2 relay corridor 上，以公共事件信息支持原生续约的策略差距中断对象族**。本次继续仅覆盖现有三种 renewal law 的有限参考模型，用于界定随机时长问题还剩什么结构机会，以及这种机会是否已被简单的同信息规则解释；不预先承认 D2 能学到该机会，也不承认 D8 已具备训练链。

与此同时，执行并保留已经成立的对象级关闭：

> **E3 的 `c=c_Z=0.25`，在大差异行 `(λ₁,λ₂)=(0.02,0.20)、Δ=1`，以及每臂 20 rollouts／128,000 transitions 的预算下，得到 `E3-H0-NO-ADVANTAGE`。该关闭不扩展到其他阈值、其他时长 law 或整个方向。**

选择 CONTINUE 的依据不是“有 headroom 就值得训练”，而是：**一个已存在、无需 learner 的有限参考问题能够改变下一次学习比较的科学含义；当前证据却不足以把失败定位到必须更换信号的原因。** 本裁决不涉及 Portfolio 排序、容量、融合或生命周期变更，也不是新实验调用或源码修改授权。

以下仓库路径均指向上述完整固定 reference；末节列出实际读取的全部 13 个路径。

## E3_RULE_READING：执行原规则，不改写分支

依据 science card 的 **“Frozen result branches”**、完整结果的 **“Frozen rule applied verbatim, in order”**，以及 CM 的 **“Paired arithmetic”**：

| 大差异行 seed |      D0／J_k |       G = D2−D0 |  配对 episode SE |
| --------- | ----------: | --------------: | -------------: |
| 1         | 0.885432842 | −0.071387329102 | 0.000880042921 |
| 2         | 0.912487998 | −0.108895874023 | 0.000737006906 |
| 3         | 0.884880388 | −0.086455281576 | 0.000721098273 |

三组均超过原定 D0 competence 线 `0.85`。因此，按原顺序：`COMPETENCE-BLOCKED` 不成立；没有正收益合格种子，`H1-ACTIONABLE` 和 `RETURN-WITHOUT-PATH` 均不成立；三组 `G≤0` 使第四分支 **`E3-H0-NO-ADVANTAGE` 成立**；不进入 `UNSTABLE`。这里没有引入新的 MEI、显著性条件或跨种子置信区间。

原始实现以 **cumulative training path** 判断 `event_path`：大差异行依次为 **false／true／false**；final-rollout 窗口另列为 **false／false／true**。保留这两个窗口的区别，不把后者替换成原发布语义。卡片未明确窗口是局限，但在本结果中，两种窗口各自一致应用都给出 H0，因为三个合格 G 全负。

其余有效观察也不被分支裁决抹去：small seed 2 的合格正收益 **+0.033291585** 保留；small seed 3 的 **+0.062728760** 也保留，但其 D0 ratio **0.814254153** 低于原线，不能支持 superiority。small seed 1 为负，medium 三组全负；small／medium／large 的描述性平均 G 分别为 **+0.018094727／−0.036266602／−0.088912828**。episode SE 是给定已训练 seed 的评估不确定性，不是训练种子总体的不确定性。

**证据类别与 claim ceiling：**18 个原定单元均为有效完成的 adaptive B/EXPLORE。它支持上述有限反例及初步 H0，不支持稳定优势、迁移、C-BENCH、C consumption 或整个方向无价值。缺少 C-time 义务不能撤销这个有效 B 结果；方法规范 §11.1、§11.4、§11.7 明确区分了这些负担。

## STRONGEST_SUPPORT / STRONGEST_CONTRADICTION

### 最强支持：保留有限下一问，而不是宣称 D2 已有优势

`DIRECTION.md` 的 **“Accepted mechanism-level science”** 与 E2 结果的 **“Frozen rule, applied verbatim”／“Bounded scientific reading”** 共同支持一个很窄的事实：D2 阈值确实控制 persistence；E2 两个种子的段长随 c 单调增加。加上 E3 small seed 2 对合格 D0 的正收益，不能把现有结果写成“策略差距中断从无决策价值”。但是，E2 的正式结果仍是 **NEITHER**，不是事件驱动机制成立。

对本次 **CONTINUE** 更具决定性的支持来自历史 advancement plan 的 **§1、§6**，以及现有 `config.py`、`renewal.py`、`references.py`：随机时长是原本就存在的独立问题；其有限参考接口已经存在，能够在不增加学习证据的情况下检查原生动作机会。历史计划只提供问题来源，不提供自动开跑的当前权力，也不证明其关于 D2／D8 的预测。

### 最强反证：不能直接把同一学习机制推进成“随机时长优势”

完整 E3 结果的 **“Paired final returns and row shape”／“Regional event path”** 是最强反证：**medium、large 共六个合格配对全部亏损；结构 margin 增大时，观察到的学习增益没有随之变正。** 尤其 large seed 2 满足原 cumulative event path，却有最大的负 G，说明“出现所定义的事件路径”本身不足以保证收益。

更强的比较约束来自 `references.py` 的 **`enumerate_references`／`GreedyOnPublicState`**：K=2 时，公共 change flag 与 lagged cue 已足以确定新 latent，现有 public greedy 与 switching reference 相等。因而，未来参考 census 中即便发现 reactive renewal 超过固定时钟，**也可能完全由一个不学习 policy gap 的简单公共规则解释**。这不能成为 D2 特有机制或学习价值的证据。

因此，不选择现在就 RECAST 到 D3：当前并未因果识别“policy proxy 噪声是决定性失败原因”。也不选择 PARK／CLOSE 该最小家族：仍有一个具体、已具有限模型接口、能够改变下一比较含义的 A 问题。**这只支持先回答该问题，不支持承诺其后的训练。**

## SURVIVING_EXPLANATIONS：学习失败原因尚未分离

| 仍活着的解释                                         | 当前证据能说什么                                                                | 当前不能说什么                               |
| ---------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------- |
| Policy gap 对收益相关事件不够准确，或存在 chatter             | E2 对齐弱；E3 的区域响应不稳定，路径阳性也可能亏损                                            | 不能把 H0 分支等同于“已证明 gap noise 是原因”       |
| 优化暴露与学习质量不同                                    | 环境交互匹配，但 medium／large 的 D0 每单元 actor、critic 各 72,000 updates，D2 各 9,000 | 不能将差异视为新增有效性缺陷，也不能假定补足 updates 就会恢复优势 |
| Team-renewal interference                      | team-gap 会使两区域一起重决策；存在大量 team decisions                                 | 不能从累计计数估计独立干预 team path 的因果收益         |
| Seed-dependent learning／representation quality | small 有合格正收益和负收益；competence 线只检查 D0 的有限表现                               | 不能把 seed 2 推成可重复优势，也不能由参数移动断定学习已经充分   |

上述解释由原卡 **“Live explanations”**、完整结果的 **“Validity, provenance and work”／“Regional event path”** 与 intake 的 **“Supported meaning and limits”** 保留。它们不是已经被实验区分的诊断。

机器生成的 rollout-20 相对初始化位移范围为：

| 网络          |    18 单元的 final displacement 范围 |
| ----------- | ------------------------------: |
| coordinator |  0.0553152482813–0.166795515435 |
| actor       |   0.405381783309–0.869975205255 |
| critic      |   0.388725326960–0.933702345740 |
| team        | 0.0333875393170–0.0679988057420 |
| individual  |  0.0538310083276–0.104735919177 |

这些数值排除了“所有网络都没动”的叙述，却不证明收敛、充分训练、正确 credit assignment 或可比较的优化质量。CM 的核算是**对同一批证据的技术复核**，不是第二批独立学习证据。

### 结构 headroom 与学习短缺必须分开

在当前 K=2 参考模型中，记 `U=J_greedy=J_switch`，则

$$
U-\overline{R}_{D0}
=
\underbrace{U-J_{k^*}}_{\text{结构 margin }m_{\mathrm{dur}}}
+
\underbrace{J_{k^*}-\overline{R}_{D0}}_{\text{观察到的 D0 学习短缺}}.
$$

| 行      |   结构 margin | Upper−平均 trained D0 | 其中 J_k−平均 trained D0 |
| ------ | ----------: | ------------------: | -------------------: |
| small  | 0.057037446 |         0.098784120 |          0.041746674 |
| medium | 0.144357787 |         0.175543309 |          0.031185521 |
| large  | 0.271218984 |         0.336673587 |          0.065454603 |

因此，不能把右侧第二项算作 D2 的额外机制机会。A1 当时缺少的 medium／large 完整 D0 行，已由完整 E3 结果补齐；不再是当前缺口。仍然缺少的是**充分调优的通用同信息 baseline 集合**，而不是这三个已完成 D0 行。这里没有新 baseline tuning，也没有任何通用投资百分比阈值。

## NEXT_SINGLE_OBJECT_OR_NONE

**NEXT_SINGLE_OBJECT：既有 E4 renewal/reference 的同信息原生续约机会 census。**
**类别：A/RECON；learner runs=0。**

### 对象范围

选择一个 census，覆盖现有三种 law，而不是选择三项后续学习研究：

`N=6，K=2，Z=4，H=400，Δ=0.4；event_process=renewal；renewal_mean=20；rounded-lognormal shape=1；k∈{1,2,5,20,40}`。

这是采用现有配置默认值及既有有限网格的下一对象范围选择。两区域使用同一个 law；成员、agent–zone–region 归属固定，`rho=0`，无 probe、无 E5 物理 coupling。所有 law 从 age 0 的完整初始 dwell 开始，不改成 stationary residual-life 相位。确定性、几何、rounded-lognormal 只匹配名义均值，不能把它们之间的差异命名为“仅方差变化”的因果效应。

rounded-lognormal 采用现有有限截断校准语义，报告校准后的数值均值、方差、截断上限和残余质量；不把其数值校准改写成无穷支持上的精确均值定理。

### Native event → ownership → information → action/credit → learner exposure → consequence

**Native event：**区域 renewal event 改变 latent；lease renewal 本身不重置区域 dwell age。

**Ownership：**事件使该区域固定实体所持 lease 失效，而不是改变成员或把 agent ownership 转给另一实体；原有 agent–zone–region 归属保持不变。

**Information：**使用 change flag、lagged cue 与公共身份。K=2 时，发生事件只能切到另一个 latent，故当前 latent 可由公共输入重建。

**Action／credit：**参考策略选择原生 role 与 `RENEW/KEEP` mask；RENEW 付出一个零服务 step，随后持有新 lease。census 计算同一个原生服务回报，不新增 shaping reward，也不训练 segment advantage 或 credit head。

**Learner exposure：**零训练 episodes、零 learner transitions、零 optimizer updates、无 checkpoint selection；DP 状态传播次数不是学习暴露。

**Consequence：**输出有限 horizon 下的期望 native return 和参考差距。它回答“时机自由度在这个模型中值多少”，不回答“D2 能否通过当前学习链获得这些值”。上述链由 `config.py` 的固定归属、`renewal.py` 的 age law 与 `references.py::dp_service_profile` 的失效／续约／服务转移支撑。

### 最强合法同信息 null

选 **`GreedyOnPublicState`**，不是一个人为削弱的盲策略。

在 K=2，事件发生时由 lagged cue 推得唯一的新 latent，更新该区域计划并立即续约；无事件时保持计划。它不需要 policy gap、额外 Q head、学习 duration menu 或提前知道未来 dwell。现有参考实现给出 `J_greedy=J_switch`。因此，最强 null 是：

> **有限模型中的 reactive-over-fixed-clock 差距，可完全由公共事件触发的脚本规则解释；该差距本身不要求 D2 的学习机制。**

同时枚举全部固定 k 参考，而不只比较历史 E4 提到的 `k=20`。这不是训练或调优 baseline，而是报告现有参考函数定义的完整五点时钟曲线。`FixedKOracle` 的现有实现仍是 latent-aware reference，不冒称 trained D0；固定时钟和 open-loop 参考更不能冒称 D8 的 `(z,k)` 学习菜单。D8 在原计划 §3 的定义与这些参考策略不同。

### 关键可观察量、MEI 与结果含义

每个 law 报告：数值均值、方差及 hazard／age 表示；`J_switch`、`J_greedy`；全部五个 `J_k` 与 `k*`；全部 96 个 open-loop 候选及最优值；`m=J_switch−J_open_best`、`m_dur=J_switch−max_k J_k`；以及 `max_k J_k−J_20`，以显示历史 `k=20` 比较是否弱于网格内最佳时钟。这些均由现有 law／reference 接口支持。

**学习效果 MEI：不适用。** 这是无 learner 的数值参考 census；原生回报单位中的结构差距及数值误差应原样报告，不新增 5%、25% 或其他 launch／投资阈值。数值误差范围内的差异只记作未分辨，不转成科学正负。方法规范 §11.7 的 headroom／MEI 描述字段不改变 E3 的分支。

一个可由源语义直接预期的检查是：完整初始 dwell 的确定性 `D=20` 与固定 `k=20` 边界重合，因此该 law 下这个时钟应能实现相同的事件续约时机。**这不是执行得到的新结果，也不是 D2 阴性；它是 census 应保留的相位语义。** 对另外两种 law 不预报优势幅度，更不预报 D2 或 D8 的学习排序。

### 预算、逐参考臂成本与停止规则

从现有枚举结构读取，每个 law 的 DP 工作为：

$$
2\ \text{switching}
+2\times5\ \text{fixed-k}
+2\times2\times6\ \text{open-loop 基础项}
=36\ \text{DP evaluations}.
$$

K=2 的 greedy 复用 switching 值，不增加 DP。open-loop 候选数为 `2⁴×(5+1)=96`。三 law 合计 **108 DP evaluations、288 个候选**，不是 108 次训练。

| Law               | DP age 状态数 | DP evaluations | Open-loop 候选 | 额外计算           |
| ----------------- | ---------: | -------------: | -----------: | -------------- |
| deterministic     |         20 |             36 |           96 | 无 lognormal 校准 |
| geometric         |          2 |             36 |           96 | 无 lognormal 校准 |
| rounded-lognormal |        400 |             36 |           96 | 现有有限截断校准及矩计算   |

每次 DP 为 `O(H×K×age)`，二元状态轴为固定因子；rounded-lognormal 还包含有限校准成本。**当前没有 census 实测秒数，也没有已获证据支持的逐 law wall-time 预测。** 后续调用卡必须在实际节点上列出三个 law 各自的成本投影和停止上限，并保留现行资源 admission；不能沿用 E3 的 learner 成本式充当其计时结果。这个尚待填写的调用成本记录不妨碍本节点选择下一科学对象，但本裁决不因此宣称其已经可直接开跑。  

**停止规则：**完成一次完整三-law census 即停止；出现非有限数值、无法解释的校准／参考不一致，或达到该 law 的调用上限时，停止相应计算并记录明确缺口，不把未完成部分当作科学负结果。不因某 law 无 gap 而改均值、shape、Δ、初始相位或 k 网格，不因某 law 有 gap 而直接启动 learner。

census 的任何正差距都只保留“该有限模型存在时机自由度的结构机会”；零差距则缩小相应 law／网格下的机会问题。**两者都不自动选择第二个对象。**

### 已有纯函数与未实现训练链

现有证据支持的是 renewal law、有限 DP、scripted references 和 reference 枚举接口。包内明确记录：当前 E2/E3 runner 没有 renewal CLI／D8 arm mapping。这里没有读取未列出的 runner，也没有独立声称检查过它的完整训练实现。因此本裁决不使用“E4 learner ready”“已有调优 E4 同信息 baseline”或“D8 已实现”作为前提。

## LIMITATIONS_AND_REVISIT_TRIGGERS

**现有成本与资源事实保持原义。** E3 的原每臂预测式为

$$
[20(64.6+0.769u)+3584\times0.46]\times1.15.
$$

small D0、medium／large D0、D2 mechanical maximum 分别为 **4177.651 s、6034.786 s、16646.986 s**，均低于原 8 小时每臂上限。18 个有效单元实际 runner wall 合计 **66087.00043219907 s＝18.357500120 h**；small D0 超过预测，但没有单元超过 cap。18 个单元均 `resources_unmeasured`，所以保留非资源科学结果，不宣称运行峰值资源合规，也不从 Windows／remote 两种窗口推导跨主机速度优势。

本次读取的是清单中的冻结汇总、科学卡、技术复核和源文件；没有重新读取 gitignored 原始 arrays／checkpoints，也没有独立复现训练或执行 census。记录中的 digest、launch SHA 与 CM 算术核验属于可追溯的既有技术证据，不增加独立经验样本。

重新讨论是否值得进入学习对象，至少需要 census 明确哪些 law 下有何种固定时钟结构差距、公共 null 已解释多少，以及后续学习比较究竟要识别什么。重新讨论 D3 或其他机制改写，需要额外证据把 policy-gap 信号问题与 optimizer exposure、representation 和 team path 区分开；这些不是本次同时选择的实验。任何后续结果都不能回写 E3 的有效 H0。

## ACTUALLY_READ_PATHS

以下 **13/13 路径均通过 connected GitHub connector 在固定 reference `c64b2619978ca91b34917ea201a11e333553590a` 读取**；长文件已分段补读。

| 实际读取路径                                                                                                        | 本裁决使用的章节／接口                                                                                            |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `docs/research/candidates/flexible_skill_duration/DIRECTION.md`                                               | Scientific question；Accepted mechanism-level science；Evidence standard。                                |
| `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`       | Treatment；Live explanations；Frozen result branches；Budget；Exposure line。                               |
| `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md`    | Validity；Paired final returns；Regional event path；Frozen rule；Exposure, headroom, cost and deviations。 |
| `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_INTAKE_20260905.md`             | Checks and reading；Supported meaning and limits；Decisions 1–3。                                         |
| `docs/Claude_docs/experiments/FSD_E3_FULL_MATRIX_READING_CHECK_20260905.md`                                   | Paired arithmetic；两个路径窗口；全部 exposure 表；artifact digests 和 launch SHA 记录。                               |
| `docs/research/candidates/flexible_skill_duration/FSD_E2_INTERRUPTION_COST_SWEEP_RESULT_EVIDENCE_20260904.md` | Result first；原规则；Per-run observations；Bounded scientific reading。                                      |
| `docs/research/candidates/flexible_skill_duration/FSD_A1_SAME_INFORMATION_HEADROOM_CENSUS_INTAKE_20260904.md` | What is actually same-information；两类 headroom；当时缺失行的历史边界。                                              |
| `docs/Claude_docs/plans/RESEARCH_ADVANCEMENT_PLAN_20260902.md`                                                | §1 的 E4；§6 的 no-large-row-gain 分支；历史预算与工作流措辞。                                                          |
| `docs/Claude_docs/plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md`                                             | §3 D0–D8；§5 E4；§11 已接受选择及后续记录。                                                                         |
| `envs/relay_corridor/config.py`                                                                               | `RelayCorridorConfig`；固定归属；`region_laws`；默认参数与 k 网格。                                                   |
| `envs/relay_corridor/renewal.py`                                                                              | 三种 law；完整初始 dwell；hazard／age cap；有限 lognormal calibration。                                             |
| `envs/relay_corridor/references.py`                                                                           | `dp_service_profile`；`enumerate_references`；`FixedKOracle`；`GreedyOnPublicState`；open-loop 定义。         |
| `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`                                                         | §2–5 证据单位与类别；§6–8 有效性及权限区分；§11.1–11.7。                                                                 |

## DECISION_TEXT：供 durable intake 原样记录

> **REQUEST_ID：**2026-09-05-fsd-e3-complete-convergence-01
> **PINNED_REFERENCE：**c64b2619978ca91b34917ea201a11e333553590a
> **FINAL_DECISION：CONTINUE — PRO_FINAL。**
>
> 接受并保留全部 18 个有效 E3 单元及原冻结分支 `E3-H0-NO-ADVANTAGE`；只关闭 `c=c_Z=.25` 在声明的大差异行与 20 rollouts／128000 transitions 每臂预算下的声明。
>
> 对固定成员 K=2 relay-corridor 的策略差距中断对象族，唯一下一对象选择为：现有 deterministic／geometric／rounded-lognormal renewal/reference 的无训练 A/RECON，同一名义均值 20、现有五点 k 网格，界定公共事件信息下的原生动作机会。最强合法同信息 null 为 public greedy；结构 reference gap 不构成 D2 或 D8 学习收益。
>
> 不选择 E4 学习矩阵、E3 重跑、c 重调或 D3 recast。census 未运行、未计时；后续调用前须记录实际节点上的逐 law 成本投影及停止上限。参数位移不等于充分学习，optimizer exposure、seed quality、policy-gap noise 与 team-renewal interference 的因果贡献仍未识别。
>
> 本裁决形成；不存在阻止本节点裁决的 connector／manifest 缺口。无源码修改、新实验执行或 Portfolio 排序／容量／融合／生命周期变更由本响应执行。
