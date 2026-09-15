# DRAFT — FOLR B03后方向选择；尚未绑定或发送

Request: 2026-09-14-folr-post-b03-direction-decision-01

You are Portfolio, the global scientific synthesizer and final direction-level interpreter under the attached owner authority. The DM is the innovator/experiment owner and report author. Read the repository documents at the fixed URLs and sections in SOURCE_MANIFEST before deciding; do not assume any local conversation, filesystem access or unlisted skill context. Use the global direction snapshot, complete affected-direction evidence, contrary results, review and applicable specifications/foundations to decide the stated direction question. Identify the material sources actually accessed and any unavailable decision-critical material. A URL or document title is not evidence of access. If access fails, request the missing exact contents or use author-provided complete scoped excerpts; do not invent them or PARK for a transport gap. Explain what changed about the scientific hypothesis, why the strongest feasible next option should be pursued or declined relative to current alternatives, and the resulting CONTINUE, RECAST, PARK, CLOSE or reopening decision. State scope, claim limits, rationale, next DM objective and any actual resource condition. Do not turn local negative evidence into a universal failure, require positive-first results or approve routine experiments one by one. Address the prior rationale and reviewer challenges substantively. Return the complete decision, not a receipt.

本稿全局快照仍在RCLE补位请求处理中；需在该作者实际释放会话后补齐最新决定/应用，再绑定原始全文。此稿不是Send指令。

请最终用中文返回完整科学方向判断。你只作本次方向综合与回复，不写其他方向、实验或控制文件；不要求GitHub写入。

## 完整DM报告

# FOLR：B03 后的方向选择与受控实体历史方案

## 要 Portfolio 判断的问题

DM 建议继续 FOLR 当前实体历史问题，优先发展一次“共同保留 Generic64 循环路径，比较持续实体状态与逐步清空实体状态”的有限学习比较，维持现有一个席位和 MEDIUM。这是待 Portfolio 综合判断的建议；停止是最接近的备选。请判断这项有限问题是否值得相对于现有机会继续，以及应归为当前 family 内的重设计还是 recast。普通实验卡、实现、工程验收与运行仍由 DM 负责，不逐项申请实验批准。

成稿时 B03 及其完整独立审查都已结束，DM 已回应全部实质意见。没有后继卡、种子、实现或新 fit；没有自行 PARK、RECAST 或释放 FOLR 席位。当前已执行的方向决定仍是此前 Portfolio 的 CONTINUE / MEDIUM。本报告不请求新付费容量、扩大三席目标、改变其他方向或恢复被停止的 scalar LEARNED_EVENT 套件。

## 原来的继续理由实际得到了什么回答

此前质疑针对的是把“首个比较已做完”当作停止依据，以及没有回答完整独立 review 所保留的第二个学习实例的价值。DM 已纠正这一点。Portfolio 后来选择 B03，理由是新完整学习与评估实例中的反转、接近或再次劣势会改变开发取舍。B03 已真实执行，回答的是其中“再次劣势”的分支；不是以等待文书代替实验，也不是为了追逐正结果。

| 完整学习与评估实例 | Generic | BANK | BANK−Generic | 原规则 |
| --- | ---: | ---: | ---: | --- |
| B02 | -0.65296875 | -5.483828125 | -4.830859375 | GENERIC_ABOVE_MEI |
| B03 | 4.9259375 | -1.71078125 | -6.63671875 | GENERIC_ABOVE_MEI |

B03 每臂5000训练回合、100000ticks、4969次RMSprop更新、128最终greedy回合及2560评估ticks；两臂均exit0。共2次新拟合、205120ticks、9938更新、256最终回合，全部完成。主量按严格小于−1的原冻结规则解释；差值偏向Generic的幅度6.63671875，超过MEI1的部分5.63671875。

每个block每臂只有一个学习实例；训练与评估种子都改变，所以两个绝对分数的变化不等于纯训练方差或算法改进。条件episode SE不能当成训练总体不确定性；不合并面板、按种子标签推定配对，或宣称稳定排序。Generic仍有40/128负回报回合，BANK为97/128；Generic的较高均值不证明绝对能力、已调好上限或收敛。曲线来自变化中的训练策略，不能证明更长训练无用。

E仍缺原Generic最终策略/评估，不能补成原始对照。F是结果知情的旧BANK固定参考用途比较，和E共用那次BANK训练；不是新的BANK训练重复。所有更早typed/scalar结果、H、失败和recast成本继续保留。原始checkpoint、回报、日志及准备/监测失败已归档，终态远端副本已在字节核验与发布后清理。没有活动native进程。

## 完整独立审查与 DM 的实质回应

最新完整107行review没有发现使B03结果失效的缺陷，支持其有限比较结论。它认为受控的附加实体历史问题比第三个不变block更值得进一步考虑，但指出三项会影响科学含义的前瞻问题。它没有选择实验、recast或方向结局。DM已读全文及访问声明；reviewer报告访问全部21项固定资料，但没有运行代码、复核原始archive或重算实验。

1. **不可见时也要清空对照的实体状态。** 原提案只写每步把GRU输入隐状态置零，仍可能经旧代码的不可见carry分支保留历史。新法则为：持续组先按观察者与目标的同一存续期截断旧状态，可见时用GRU更新，不可见时保留截断后的状态；对照组可见时只计算GRU(当前合法输入,0)，不可见时实体隐状态就是0。两组均保留相同的合法seen/age等信息及readout masks。这是改正尚未实现的提案含糊处，不能追溯称为B03的代码bug。
2. **共同保留通用循环架构，不等于保留原来的策略成绩。** 两组均由当前合法attention与public/local metadata进入各自Generic64，再在Q读出端融合实体分支。实体特征不能只在一组反馈到Generic输入；peer变化也不能清空整个Generic自身存续期记忆。拟用64维通用流、64维实体读出拼接后共同的linear128-to5读出。两组角色对应模块初始化相同，但各自参数、优化器、replay和隐状态可因学习而不同；online/target分别重建两个状态流。共享模块、初始化次序与RNG消费者将在前瞻卡中固定，改变路径需相称的独立工程审查。
3. **同参数量不等于同时间容量或同优化。** 清空实体状态同时改变跨步依赖、梯度及有效计算；这是干预的一部分。两组仍有Generic历史和合法bookkeeping，不是有记忆对无记忆。拟比较的是两个完整训练程序中额外持久实体状态的有限作用，不是证明唯一记忆机制，也不是解释B02/B03输在哪里。

完整原文与逐项DM回应由清单分别提供，不能用上述摘要替代。实际Git答复有23158bytes及末尾LF；Transport曾把去尾LF的正文哈希称为原文件哈希。DM直接读取Git blob后更正事实，原回执保留，完整科学内容没有缺失，也未重发问题。新的方法清单使用已修正角色用语的规范版本；已接受B03问答不重写。

## 窄问题为何可以有价值，以及它不能决定什么

现有源码揭示的差别是真实结构：旧Generic在融合当前关系信息后运行GRU64，旧BANK先对观察者—目标更新GRU16，再做当前融合，替代了那条通用循环路径。物理特征旁路没有消除这种时间组织差别。这是形成新假设的源码依据，不是测得损失的原因诊断。

附加方案让两组共同保留通用循环能力，再比较额外实体状态是否持续。拟定主量为新训练的持续组减逐步清空组最终native均值，仍用前瞻绝对MEI1。高于MEI会支持继续考察该附加候选中的persistence；区间内只表示该实例缺少实际分离，非等效；负向超过MEI则更偏向该候选的逐步清空程序。缺少端点则没有依赖它的比较。没有一个分支自动选择下次实验或方向结局。

**本轮目的明确是候选内部的persistence开发选择，不是把Generic从可用方案中替换掉。** 持续组即使胜过逐步清空组，两者仍可能都差于未增强Generic。历史B03不能替代同期未增强Generic的比较。若下一步实际要主张或决定增强方案胜过Generic，必须有对应的新比较证据。本轮不默认购买第三臂，因为它并非这个较窄主量的必要条件；遗漏第三臂所损失的直接采用价值是真实局限，不能隐去。

DM倾向继续这个窄问题，是因为它保留通用循环路径、控制一个具体实体状态法则，并用两个完整学习程序的native后果来区分候选内部的开发路线。两个旧损失没有回答它。它比再次运行原替代架构多付出工程和计算，但可能提供更直接的设计信息。这里没有可量化成功率或确定的价值排序；若Portfolio判断这类条件性开发价值仍不值得成本，停止是可成立的决定。

## 最强反方案与成本

**停止是最接近的反方案。** H20短行程、再度可见的线索、public lifecycle信息及Generic已有的历史处理能力，可能使额外持久状态没有回报空间。原替代套件两次明显落后，新分支还会增加优化负担。窄消融即使阳性也不证明增强净收益，存在多走一个无效开发阶段的风险。这些理由支持PARK，强于“结果为负、票据完成或支持成本未知”。DM推荐继续并非已经排除这些解释，Portfolio应实质比较它们。

其他有效方案包括：第三个不变5000回合block，主要增加同一替代架构的实现实例证据；把旧比较延长到10000训练回合，检验曝光敏感性；或选择更需要历史的native环境/更长horizon，改变信息需求和信用条件。既有曲线不能否定这些选择。换环境也无需先有阳性pilot、上限证明或机会普查；但当前受控附加问题先保持host和信息接口不变，故DM目前优先它。任何更佳方案都应说明具体可区分的问题，而非默认继续或默认停掉。

拟议附加比较：2个新fit，每臂5000训练/4969更新/128最终评估，共205120ticks、9938更新及256最终回合。每fit包括33391680个Generic replay位置及上界166958400个BANK位置，宽度不同；另有acting、attention、fusion、backward、mixer及发布。没有嵌套轨迹/控制器搜索。共享算子与不同梯度路径使历史wall不可直接相加预测新wall。5400秒/增强fit、10800native合计加1800主动支持，仅是未选择的前瞻计划，实际耗时和峰值内存未知。原10000回合例子则为405120ticks/19938更新，两者都要按实际源码与准入运行。

B03实测native墙钟为2005.71和1774.14秒，合计3779.85；CPU合计3776.06；study经过4424秒，含644秒臂间隔。这三个口径分别保留。E/F/B02/B03已知native合计12538.44秒，不是整个方向累计总成本。已测收集/分析/保全/清理的13.187秒只是选择性支持成本下界；全部支持、模型服务、更早成本及新增工程成本仍UNKNOWN，没有清零或宣称完整原cap合规。尚无相同信息、完整调参的baseline与upper headroom记录；B03正回报不能代替它，缺口也不是停止或启动门槛。

实施继续决定时仍使用现有远端资源、新准入、明确源码提交、每次一个FOLR调用及固定科学端点。普通wall计划可按实际工作前瞻修订；真实owner/平台限制保持。不会以改名、重新建卡或辅助归档重置历史成本或已有family停止。

## 全局上下文与所需输出

报告准备时共享登记为FOLR和MGTAP各占一席、RCLE已PARK并负责唯一真实空缺的Portfolio补位请求，无预留。MGTAP已完成对称选率及全新holdout，双方选1e-4，新实例主量+0.023704897713093642 J；完整review和Portfolio后继续目标为固定率新配对。其收益单位、环境和学习问题与FOLR不同，不能直接比较原始return数字。RCLE的B13及完整review/Portfolio PARK依据、资产和补位事务由原DM保留。本报告不重复其补位请求或抢占其会话；发送时清单会补入当时最新实际全局状态和已完成的补位选择（若已有）。

请按所附固定协议、全局状态、完整方向证据、反证、独立review与DM回应，给出完整中文方向判断：继续上述有限开发问题、recast成更合适的明确问题，或PARK/CLOSE；说明为何其价值胜过最强备选，family归属/旧边界、结论上限、下个DM目标及任何真实资源条件。不要把科学review当成执行选择或把每个常规fit变成许可申请。无需认可DM建议才能继续讨论；如果有实质异议，请指出会改变判断的具体假设或证据。

请列出实际访问的关键固定资料和不可访问的决策关键内容；若缺关键内容，保持同一请求澄清，不凭标题推断内容，也不因传输缺口作科学PARK。最终答复应是完整方向决定及理由，由DM核对与应用；不需要Root再次批准。


## SOURCE_MANIFEST — fixed documents and required scopes

- **protocol**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/project/PORTFOLIO_DECISION_PROTOCOL.md
  Read: Complete final direction authority and web-source-access contract.
- **agents**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/AGENTS.md
  Read: Current owner overrides and sections1,2,4,5,6: roles, three slots, resources and fixed evidence; current protocol takes precedence over historical role wording.
- **peer**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/project/PEER_DM_COORDINATION.md
  Read: Current equal-peer ownership, serial Portfolio author and shared-main/vacancy rules.
- **spec**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
  Read: Sections7-8.1,11.4,11.7-11.10; corrected11.9, adverse-result follow-up, claim burden and finite-work reasoning.
- **foundations**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
  Read: Sections2,4,6: legal information versus sufficient state; representation versus finite learning; evidence units.
- **empirical**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
  Read: Comparison targets, randomness levels, trained-program versus component claim, and claim-dependent burden.
- **engineering**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/project/ENGINEERING_SCOPE_SPEC.md
  Read: Sections4 and7.1-7.3 for the proposed recurrence/fusion/RNG change; no implementation already selected.
- **runtime**: https://github.com/CartmanFatass/My-paper-code/blob/df2a5ea2311c88eb502e8b6d748cd725db6f815d/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
  Read: Sections1-3: plans versus real constraints, complete invocation/study/CPU accounting and dominant work.
- **global_report**: https://github.com/CartmanFatass/My-paper-code/blob/6ed70786a0b2aa8bb6a41a656e4a94d05d2d896c/docs/research/portfolio/PORTFOLIO.md
  Read: All current directions, actual work, vacancy and costs at this draft snapshot; refresh actual later changes before Send.
- **global_registry**: https://github.com/CartmanFatass/My-paper-code/blob/6ed70786a0b2aa8bb6a41a656e4a94d05d2d896c/.codex/hmasd-dm-sessions.toml
  Read: Portfolio and active/RCLE rows: two occupied, one RCLE-owned vacancy, accepted current RCLE request and named next FOLR author notice. Refresh before Send.
- **report**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/pro_packets/20260914_post_b03_portfolio_direction/REPORT.md
  Read: Complete current DM report, proposal, strongest alternatives, limits and costs.
- **direction**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/DIRECTION.md
  Read: Scientific question/current position, stopped scalar-family boundaries and relevant entity-history opening/results; retain all recast history.
- **b03_review**: https://github.com/CartmanFatass/My-paper-code/blob/18e03e45d69def09d29c0f2c299bb855891b0f27/docs/research/candidates/vap_folr_core/pro_packets/20260914_entity_history_b03_result_plan_review/archive/RESPONSE.md
  Read: Complete107-line independent review and its source-access limitations, including P1/P2/P3.
- **b03_response**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/pro_packets/20260914_entity_history_b03_result_plan_review/INTAKE.md
  Read: Complete substantive DM response, explicit persistent/current-only state law, common generic route/fusion and narrower decision value.
- **b03_card**: https://github.com/CartmanFatass/My-paper-code/blob/4776103de4f55beaee610c52506112651bfaed04/docs/research/candidates/vap_folr_core/FOLR_ENTITY_HISTORY_B03_SCIENCE_CARD_20260914.md
  Read: Complete prospective B03 comparison, seeds, exposure, primary/MEI, prediction, budgets and interpretations.
- **b03_result**: https://github.com/CartmanFatass/My-paper-code/blob/6642b5e63d7e9d8dd95f52511c53e7b15f92eb86/docs/research/candidates/vap_folr_core/FOLR_ENTITY_HISTORY_B03_RESULT_EVIDENCE_20260914.md
  Read: Complete accepted result/counts/cost/uncertainty/deviations; no outcome regrading.
- **b03_intake**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/FOLR_ENTITY_HISTORY_B03_INTAKE_20260914.md
  Read: Complete result reasoning and original prospective proposal, explicitly updated by latest full review intake.
- **b03_cost**: https://github.com/CartmanFatass/My-paper-code/blob/51842d2bbfb3a2ea44e677bdb8bd61bf92d98232/docs/research/candidates/vap_folr_core/entity_history_b03_781501/COST_SUMMARY.json
  Read: Known native/study/CPU costs and updated selected support lower bound13.187s; all remaining totals UNKNOWN.
- **actor**: https://github.com/CartmanFatass/My-paper-code/blob/b257dcb1d7578a057afa9b4bdd7c7ff74ad8e24f/experiments/candidates/vap_folr_core/entity_history_b01/model.py
  Read: Complete Actor and ObserverAttention source; original replacement architecture and prospective control carry risk, not a diagnosed old defect.
- **b02_result**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/FOLR_ENTITY_HISTORY_B02_RESULT_EVIDENCE_20260914.md
  Read: Complete separate B02 outcome and E/F dependency limits.
- **b02_review**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/pro_packets/20260914_entity_history_b02_review/archive/RESPONSE.md
  Read: Complete earlier independent review that challenged completion-based stopping; preserved original response sourceb4a67c7b.
- **b02_response**: https://github.com/CartmanFatass/My-paper-code/blob/7557dc5c44d684ea44d5603e5300c3cfd97098c0/docs/research/candidates/vap_folr_core/FOLR_ENTITY_HISTORY_B02_INTAKE_20260914.md
  Read: Owner-requested scientific reconciliation and exact prior PARK/reading-claim correction; original results preserved.
- **prior_portfolio**: https://github.com/CartmanFatass/My-paper-code/blob/4776103de4f55beaee610c52506112651bfaed04/docs/research/candidates/vap_folr_core/pro_packets/20260914_portfolio_direction_reconciliation/archive/RESPONSE.md
  Read: Complete prior Portfolio CONTINUE rationale, B03 outcome consequences and rejected unchanged stopping/DISH option.
- **prior_application**: https://github.com/CartmanFatass/My-paper-code/blob/4776103de4f55beaee610c52506112651bfaed04/docs/research/candidates/vap_folr_core/pro_packets/20260914_portfolio_direction_reconciliation/INTAKE.md
  Read: Complete DM scientific response and actual prior direction application.
- **mgtap**: https://github.com/CartmanFatass/My-paper-code/blob/6ed70786a0b2aa8bb6a41a656e4a94d05d2d896c/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_lr_selection_portfolio_direction/INTAKE.md
  Read: Current applied CONTINUE, actual finite-selection result, contrary evidence, cost and pending fixed-rate pair; later peer-state passages are historical, current global snapshot governs.
- **rcle**: https://github.com/CartmanFatass/My-paper-code/blob/6ed70786a0b2aa8bb6a41a656e4a94d05d2d896c/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260914_post_b13_portfolio_direction/INTAKE.md
  Read: Applied post-B13 PARK and strongest fresh-instance alternative, costs, evidence and single-vacancy ownership; new replacement selection remains separately pending at this snapshot.
