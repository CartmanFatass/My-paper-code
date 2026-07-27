# G40 formal result update (mechanically recorded from External Pro)

g40_credit_row_supersedes=G39 native-six continuous-roster G31 credit package local necessity/open replacement row
g40_credit_row_status=SUPPORTED_RETAINED
g40_credit_row_evidence=docs/research/cdc/EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_FORMAL_RESULT.md|docs/report/ITERATION_31.md|docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_formal_result_review/21_PRO_OPEN_RAW.md
g40_credit_row_claim_ceiling=shared-accepted-native-six-fast-anchor and exact G40-P0 toy family; G31 realized-tail credit package has material finite-budget access/utility advantage over frozen ordinary shared-team GAE1/PPO branch
g40_credit_row_exclusions=not-universal-temporal-credit-necessity|not-future-information-alone|not-all-ordinary-estimators|not-UAV|not-recurrence|not-arbitrary-process-capacity-horizon
g40_credit_row_next_action=CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_DESIGN_ASSERTION_AUDIT
g40_ordinary_team_gae1_replacement_status=FAILED_CLOSED
g40_remaining_open=standalone_slow_critic_and_internal_G31_component_attribution

# HMASD 科研方向账本

## 用途与权威边界

本文件只回答四个科研问题：哪些方向已经得到支持、哪些精确方向已经
失败并关闭、哪些实验因源或基准不可识别而不能评价算法、哪些方向仍未
验证。它是面向后续科研的纵向索引，不是实现计划、运行日志、权限来源，
也不产生新的科研结论。

状态改变只来自用户的科研范围决定，或 External Pro 对正式结果的精确
科研裁决。Project Manager 只负责把已接受裁决机械地登记到这里；机械
分析分支、非正式筛选、代码覆盖缺口和 PM 推测都不能自行改变方向状态。
数值、种子、预算、命令和实现细节留在链接的原始证据中。

## 状态词

| 状态 | 含义 |
|---|---|
| `SUPPORTED_RETAINED` | 在明确边界内获得结论性支持，后续研究可复用，但不得越界外推。 |
| `FAILED_CLOSED` | 一个精确假设、机制或实现族被结论性证据否定；只关闭该最小单元。 |
| `SOURCE_NOT_IDENTIFIABLE` | 环境或对照不能形成有效算法检验；不计为算法成功或失败。 |
| `PENDING_PRO_DISPOSITION` | 正式机械结果完整，但科研含义尚未由 External Pro 裁决。 |
| `OPEN_UNTESTED` | 已知科研问题尚无结论性证据。 |
| `OUT_OF_SCOPE_FROZEN` | 当前授权有意不研究；不得被写成失败。 |

## 已支持并保留的方向

| 方向 | 当前裁决 | 已支持的最小范围 | 明确不能推出 | 主要证据 |
|---|---|---|---|---|
| 动态成员直接循环策略 | `SUPPORTED_RETAINED` | G8 的 prefix-normalized direct recurrent policy 在已登记离散 toy family 中，经 G9--G16 覆盖高频 churn、N=12--40 组合、slot layout、N=80、随机 roster process、原子替换、count shock 与 fresh-seed mixture。 | 不能推出任意 N、任意过程律、异步技能生命周期、内在奖励优势或 UAV 可用性。 | [G16 最终链裁决](EVIDENCE_NOTES/20260723_DYNAMIC_ROSTER_CHAIN_FINAL_DISPOSITION.md)；[命题账本](CONJECTURES.md) |
| 连续动态 roster 的即时服务控制 | `SUPPORTED_RETAINED` | G17 支持在已登记 continuous-service toy family 中，成员生命周期状态、active-set 聚合与直接 demand path 可形成可用控制器。 | 不能推出长延迟信用、真实 UAV 物理运输或任意随机 horizon。 | [G17 正式结果](EVIDENCE_NOTES/20260724_CONTINUOUS_SERVICE_ROSTER_G17_FORMAL_RESULT.md) |
| realized-return-to-go 的延迟信用修正 | `SUPPORTED_RETAINED` | G31 在配对 G17/G18 toy family 与 fresh seeds 上同时保留即时任务并通过延迟 spike、rotation 和稳定性门槛。 | 不能单独推出 UAV transport、普适信用分配或对其他 source family 的优势。 | [G31 正式结果](EVIDENCE_NOTES/20260724_RETURN_TO_GO_DIRECTION_BALANCED_G31_FORMAL_RESULT.md) |
| 连续动态 roster 的原生六坐标 current-state 训练与部署 | `SUPPORTED_RETAINED` | G31/G32/G34/G35/G39 在已登记 H=48、capacity 6/8/12 toy family 中形成当前最小可用版本：capacity-8 训练可迁移到固定/有界随机 roster process；actor 不携带 learned hidden，也不读取 age、previous action 或 actor time；G39 的 NATIVE6_CS 从初始化起仅有 Linear(6,32)/Linear(6,2)，无 constant columns、donor 或 fold。CONST-minus-NATIVE pooled CI95 为 [-0.00286042, 0.00393514, 0.00975470]，两臂均通过 access，native route 通过全部 0.05 noninferiority 门槛。 | 不能推出任意独立 native initializer、其他 optimizer/budget、critic-time 冗余、普通 credit 等价、全局 memoryless、任意容量/过程/horizon、UAV transport、技能生命周期或 intrinsic-reward 结论。 | [G39 正式结果](EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_FORMAL_RESULT.md)；[第 30 轮报告](../../report/ITERATION_30.md) |
| 普通/团队循环状态作为强对照 | `SUPPORTED_RETAINED` | 普通 recurrence 解决精确 G1 cue source；TEAM_REC 解决精确 G2 global-bit handoff，是后续机制主张必须保留的较简单解释。 | 不能推出显式 event-held mechanism 永远无用，也不能替代 variable-cardinality 机制检验。 | [G2 正式结果](EVIDENCE_NOTES/20260723_CROSS_LIFECYCLE_HANDOFF_G2_FORMAL_RESULT.md)；[反例账本](LEMMA_COUNTEREXAMPLE_LEDGER.md) |

## 已失败并关闭的精确方向

| 精确关闭单元 | 状态 | 科研结论 | 不得误写为 | 主要证据 |
|---|---|---|---|---|
| 原始 prefix 表示向 N>16 的冻结外推（G7） | `FAILED_CLOSED` | persistent duty 保留，但 short allocation 随规模跨种子退化；原表示的 robust transport 被否定，随后由 G8 的 prefix normalization 另起修正。 | “动态 roster 方向失败”或“G8 救回并改写 G7”。 | [G7 正式结果](EVIDENCE_NOTES/20260723_BEYOND_DECLARED_COUNT_G7_FORMAL_RESULT.md) |
| 当前 EHC 五轮链 | `FAILED_CLOSED` | G1/G2 中普通或团队 recurrence 足够；G3/G4 虽有 roster 干预响应，却未建立稳健自然 access、mediation 或优势。当前证据不支持 event-held temporal commitment 作为已识别优势机制。 | “EHC 在所有任务上不可能有效”或“因后置诊断而重标旧结果”。 | [EHC 测量反例](EVIDENCE_NOTES/20260722_EHC_MEASUREMENT_COUNTEREXAMPLES.md)；[G3 正式结果](EVIDENCE_NOTES/20260723_USEFUL_EFFECT_ROSTER_G3_FORMAL_RESULT.md) |
| shared actor 的第一代 delayed-credit 组合（G18） | `FAILED_CLOSED` | 延迟 source 能学习，但跨 fresh seeds 不能同时稳定保留 G17；该精确双源实现不是可用共同算法。 | “representation 已被否定”或“所有 temporal credit 修正失败”。 | [G18 正式结果](EVIDENCE_NOTES/20260724_ACTOR_CRITIC_ISOLATED_G18_FORMAL_RESULT.md) |
| frozen-anchor additive residual 族（G19--G26） | `FAILED_CLOSED` | 受冻结 anchor 限制的加性 residual 族对已登记分离任务表达力不足。 | “所有 residual、所有双通道 actor 或所有信用分解都无效”。 | [G25 结果](EVIDENCE_NOTES/20260724_FROZEN_ANCHOR_RESIDUAL_EXPRESSIVITY_G25_RESULT.md)；[G26 结果](EVIDENCE_NOTES/20260724_PREFIX_CONTEXTUAL_RESIDUAL_G26_RESULT.md) |
| G27--G30 的精确 full-actor 约束变体 | `FAILED_CLOSED` | G27 保留 G17 但失去 delayed access；G28 接近但 spike utility 未过冻结门槛；G29 realized-step tangent 使 delayed access 崩溃；G30 broad utility 高但 spike allocation 跨种子不稳定。 | “调低门槛即可成功”或用 G31 结果追溯性改写这些失败。 | [G27](EVIDENCE_NOTES/20260724_IMMEDIATE_TANGENT_FULL_ACTOR_G27_RESULT.md)、[G28](EVIDENCE_NOTES/20260724_NET_IMMEDIATE_DESCENT_FULL_ACTOR_G28_RESULT.md)、[G29](EVIDENCE_NOTES/20260724_OPTIMIZER_REALIZED_TANGENT_FULL_ACTOR_G29_RESULT.md)、[G30](EVIDENCE_NOTES/20260724_DIRECTION_BALANCED_FULL_ACTOR_G30_FORMAL_RESULT.md) |
| G35-P0 中 learned actor hidden carry 的必要性或 >0.05 material advantage | `FAILED_CLOSED` | fully informed CS 与 REC 均达到 access；REC-minus-CS pooled CI95 为 [-0.0173505, -0.0081213, 0.0007130]，每个 capacity 的 UCB 均 <=0.0054082。该 source、预算与架构下，learned carry 不是 load-bearing。 | “所有任务都不需要 recurrence”“REC 在所有设置都更差”或“G31 credit 不需要”。 | [G35 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_RESULT.md)；[第 26 轮报告](../../report/ITERATION_26.md) |
| G36-P0 中目标真实/一致 history bundle 对 exact G35 CS checkpoint access 或 >0.05 material benefit 的必要性 | `FAILED_CLOSED` | 替换真实 time、lifecycle age 与两个 previous actions 后，fixed/random capacity-6/8/12 的全部 access 门槛通过；primary registered-minus-substitution CI95 为 [-0.0024790, 0.0001048, 0.0035749]，最大 component UCB 为 0.0075287。目标 episode 的真实 coherent bundle 在该精确边界内不是 load-bearing。 | “四个模型坐标可以删除”“任意 filler 都安全”“所有任务都无记忆”“critic 或 lifecycle state 不需要”。 | [G36 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_FORMAL_RESULT.md)；[第 27 轮报告](../../report/ITERATION_27.md) |
| G38-P0 中 actor 的 age/previous-action/time bundle、donor 接口或十坐标部署对 access 的必要性及 >0.05 advantage | `FAILED_CLOSED` | freshly trained FOLD6 从不读取四个真实字段，最终删除其 136 个 actor weights 和全部 donor/filler 路径；FULL10 与 FOLD6 均达到 access，FULL10-minus-FOLD6 pooled CI95 为 [-0.01008621, -0.00312729, 0.00841468]。 | “所有任务都不需要历史”“原生六输入训练必然等价”“critic true time 或 G31 credit 不需要”“四个字段可分别无条件删除”。 | [G38 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_RESULT.md)；[第 29 轮报告](../../report/ITERATION_29.md) |
| G39-P0 中 136 个 constant-column 参数、其 Adam moments 与 post-training fold 对 access 的必要性或 >0.05 advantage | `FAILED_CLOSED` | function-matched CONST10_FOLD6 与 NATIVE6_CS 均达到完整 access；CONST-minus-NATIVE pooled CI95 为 [-0.00286042, 0.00393514, 0.00975470]，capacity-6/8/12 UCB 均 <=0.012068。冗余 constant parameterization 在冻结 Adam/source/budget 下不是 load-bearing，且不提供 >0.05 material advantage。 | “所有初始化或 optimizer 下 native-six 都等价”“CONST 完全无任何微小效应”“critic 或 G31 credit 不需要”“所有任务都无记忆”。 | [G39 正式结果](EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_FORMAL_RESULT.md)；[第 30 轮报告](../../report/ITERATION_30.md) |

## 源或基准不可识别：不能评价算法

| 场景 | 状态 | 已知事实 | 尚不能回答 | 主要证据 |
|---|---|---|---|---|
| UAV temporary service loss G1 | `SOURCE_NOT_IDENTIFIABLE` | 构造控制器未达到绝对可行性且劣于 no-reallocation；正式流程在 learned training 前关闭。 | G31 或其他学习算法能否处理可行的临时脱队/失灵场景。 | [UAV G1 正式结果](EVIDENCE_NOTES/20260724_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_RESULT.md) |
| UAV charge rotation G2 | `SOURCE_NOT_IDENTIFIABLE` | proactive rotation 相对 no-rotation 是 load-bearing，但构造控制器仍远低于绝对可行 floor，support 失败，未产生 learned training。 | 算法在可识别的充电轮换与突增通信需求源上是否有效。 | [UAV G2 正式结果](EVIDENCE_NOTES/20260725_UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_RESULT.md) |

## 尚未验证的方向

| 方向 | 状态 | 当前最小问题 | 为什么仍未验证 |
|---|---|---|---|
| G39 NATIVE6 controller 向非 G33、可识别 UAV source 的 transport | `OPEN_UNTESTED` | 在物理可行、目标行为 load-bearing 且 source-identifiable 的非 G33 UAV source 上，六坐标 current-state representation、bounded-process transport 与 G31 credit 是否保持可用。 | UAV G1/G2 在 learned training 前因 source 不可识别关闭；G33 被用户放弃；该方向 parked 至一个独立可识别 source 被冻结。 |
| G36 donor 跨列 coherence 的 exact-checkpoint 问题 | `OPEN_UNTESTED` | G37 对 exact G35 checkpoints 得到 mixed directional cost，但 G38 已在 fresh training 后删除完整 donor/history-shaped actor interface。 | 当前不阻塞 accepted G38 actor，作为历史 checkpoint-sensitivity 问题 parked；仅在未来重新采用 donor-based deployment 或研究 multivariate checkpoint OOD 时复活，禁止扩 G37-P0 seed/episode 救援。 |
| G39 native-six continuous-roster 中 G31 credit package 的局部必要性/可替代性 | `OPEN_UNTESTED` | 在保持 NATIVE6 actor、true-current-state critic、G32/G34 source、reward、paired ledgers、action streams、environment interactions 与 optimizer exposure 不变时，普通 primitive-step team credit 是否达到完整 access 并对 G31 route 非劣。 | G39 两臂都固定使用 G31 realized-future-tail/direction-balanced credit；actor information、carry 与 constant-overparameterization 已分离，但 credit 尚无 matched comparator。当前 scheduled action 为 G40 design audit。 |
| 超出已登记边界的 active count、membership process 与 horizon | `OPEN_UNTESTED` | 已支持表示在 N>80、configured capacity 6/8/12 之外、重复 leave/rejoin、不同 event count/type、任意过程律与 horizon≠48 时的边界。 | G34 只覆盖一个 each-of-L/R/J/T、三种顺序、五步最小间隔和 H=48 的有界 process family。 |
| 异步技能生命周期 | `OUT_OF_SCOPE_FROZEN` | runtime-variable team membership 与 variable individual skill lifetime 的组合效应。 | 当前主链主动冻结 skill-cycle 维度，先建立动态 agent 数量下可用算法。 |
| 环境无关 intrinsic reward 的增益与比较优势 | `OUT_OF_SCOPE_FROZEN` | 在可识别 source 与强 recurrence comparator 下是否提供稳定额外价值。 | 当前主链目标是先得到可用算法，不以建立优势为准入条件。 |
| UAV localized-demand-burst G33 及其 full-ledger/static-preposition 衍生线 | `OUT_OF_SCOPE_FROZEN` | 用户直接放弃并禁止重命名或复活该 lineage。 | 这是范围决定，不是 source 或算法的科学失败；不得由后续 G34 结果改写。 |
| S7/S1 类突增通信、充电轮换、临时脱队/失灵的完整鲁棒性 | `OPEN_UNTESTED` | 在物理可行且可学习的 UAV source 中验证服务 roster 变化与算法 transport。 | 已有两项 UAV source 未通过 source-identifiability；heavy UAV 只用于 toy-supported candidate promotion。 |

## 科研路线的最小纵向摘要

1. EHC 探索首先证明了“自然使用、寿命多样性、logit 干预和值增益”不足以
   识别 event-held temporal commitment，并以 ordinary/team recurrence 的
   简单解释关闭了当前精确链。
2. 项目转向先建立可用的动态成员算法。G5--G16 从直接 recurrent MVP，
   经一次 G7 规模反例和 G8 修正，逐步闭合规模、churn、slot、随机过程与
   fresh-seed mixture，得到离散 toy 版可用算法。
3. G17 把主线扩展到连续控制；G18 暴露即时与延迟信用不能稳定共存，
   G19--G30 逐个关闭较弱或过强约束，G31 以 realized future tail 在配对
   toy 上形成当前保留的延迟信用方向。
4. UAV G1/G2 说明先验证 source 比直接重型训练更重要：两轮都没有形成
   算法证据，因此主线回到 toy，而不是把基准失败归因于算法。
5. G32 支持 capacity-6/8/12，G34 支持固定过程到有界随机 roster
   process，G35 关闭 learned actor carry，G36 关闭 exact-checkpoint 对目标真实
   history sensors 的依赖，G38 支持六坐标部署。G39 进一步证明 function-matched
   原生六输入图可直接训练：无 136 个 constant-column 参数、对应 Adam moments
   或 fold，仍通过全部 access 与 0.05 noninferiority 门槛。当前最小 route 已在
   actor information、recurrence 和参数化层面完成化简；下一边界隔离 G31 credit
   package，而 broader process/horizon/capacity 与可识别非 G33 UAV transport
   继续保留。

## 每轮更新协议

每个有效结论性迭代在 External Pro 完成
`FORMAL_RESULT_SCIENTIFIC_DISPOSITION` 后，由 Project Manager 在写入中文
迭代报告的同一 Git 边界内完成以下机械更新：

1. 更新或新增一条方向记录，使用且只使用上述六种状态词；
2. 写明被支持或关闭的最小范围，以及至少一条禁止外推；
3. 将失败区分为算法/假设失败和 `SOURCE_NOT_IDENTIFIABLE`；
4. 链接原始正式 evidence note 与迭代报告，不复制运行细节；
5. 若 Pro 未完成科研裁决，只能登记为 `PENDING_PRO_DISPOSITION`；
6. 同步维护 [CONJECTURES.md](CONJECTURES.md)、
   [IDEA_PORTFOLIO.md](IDEA_PORTFOLIO.md) 和
   [LEMMA_COUNTEREXAMPLE_LEDGER.md](LEMMA_COUNTEREXAMPLE_LEDGER.md) 中真正受
   该裁决影响的最小条目，不做全文件重述。
