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
| 连续动态 roster 的跨容量、随机过程与 current-state 化简 | `SUPPORTED_RETAINED` | G31/G32/G34/G35 在已登记 48-step toy family 中形成可用测试版：capacity-8 训练模型可在配置容量 6/8/12 与固定/有界随机 roster process 上保持 access；G35 进一步表明，在保留 true time、age、previous action、active-set、prefix 与 G31 credit 时，不携带 learned cross-step hidden 的 CS arm 已充分，REC 的 >0.05 material advantage 在 P0 内被关闭。 | 不能推出 history-proxy-free、time-free、任意容量/过程/horizon、UAV transport、技能生命周期、内在奖励增益、G31 credit 冗余或全局 recurrence 无用。 | [G34 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_FORMAL_RESULT.md)；[G35 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_RESULT.md)；[第 26 轮报告](../../report/ITERATION_26.md) |
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

## 源或基准不可识别：不能评价算法

| 场景 | 状态 | 已知事实 | 尚不能回答 | 主要证据 |
|---|---|---|---|---|
| UAV temporary service loss G1 | `SOURCE_NOT_IDENTIFIABLE` | 构造控制器未达到绝对可行性且劣于 no-reallocation；正式流程在 learned training 前关闭。 | G31 或其他学习算法能否处理可行的临时脱队/失灵场景。 | [UAV G1 正式结果](EVIDENCE_NOTES/20260724_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_RESULT.md) |
| UAV charge rotation G2 | `SOURCE_NOT_IDENTIFIABLE` | proactive rotation 相对 no-rotation 是 load-bearing，但构造控制器仍远低于绝对可行 floor，support 失败，未产生 learned training。 | 算法在可识别的充电轮换与突增通信需求源上是否有效。 | [UAV G2 正式结果](EVIDENCE_NOTES/20260725_UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_RESULT.md) |

## 尚未验证的方向

| 方向 | 状态 | 当前最小问题 | 为什么仍未验证 |
|---|---|---|---|
| G35 current-state continuous-roster controller 向非 G33、可识别 UAV source 的 transport | `OPEN_UNTESTED` | 在物理可行、目标行为 load-bearing 且 source-identifiable 的非 G33 UAV source 上，fully informed current-state representation、bounded-process transport 与 G31 credit 是否保持可用。 | UAV G1/G2 在 learned training 前因 source 不可识别关闭；G33 被用户放弃；尚无可判别的 UAV transport 结果。 |
| G35 CS checkpoint 的 history-proxy-free 执行 | `OPEN_UNTESTED` | 在不改变 checkpoint、current load/mix、capability、active set、prefix、critic、source 或 action stream 时，neutralize actor 的 true time、lifecycle age 与 previous-action fields 后，CS 是否仍保持 access 与注册 noninferiority。 | G35 只删除 learned hidden carry；三个 history-proxy fields 均被保留，尚不能把 current-state sufficiency 写成纯即时 demand mapping。 |
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
5. G32 支持 capacity-6/8/12 strict-load，G34 支持固定过程到有界随机
   roster process 的零训练 transport。G35 通过 fresh paired REC/CS 比较支持
   fully informed current-state reduction，并在 P0 内关闭 learned actor hidden
   carry 的必要性或 >0.05 advantage。该结果仍保留 true time、age、previous
   action 与 G31 credit；下一边界检查 accepted CS checkpoint 是否依赖这些
   history-proxy inputs。

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
