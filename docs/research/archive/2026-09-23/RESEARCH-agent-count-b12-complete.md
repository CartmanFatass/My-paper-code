退役日期：2026-09-23。DM1 的 B12 两臂已完整验收；此页保存被替代的运行快照与计划，不再维护。
来源：已发布 main `367fa62b8ff196e6aa5f8a934820b1b084c234ea` 的 RESEARCH.md。
仅退役 DM1 已完成计划，其他 DM 和 owner 控制不变；当前判断见 ../../RESEARCH.md。

## 原方向状态

| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B11 已完整验收：两个新普通 SET 分别 N6/N8 训练，共同实际初始张量，2 fits/720k train/64k eval；30文件逐字节核验、四面板原生轨迹独立重算通过。T8−T6 在 N8 的 J +.019681931、服务 +3.0195人/步，J 20正/12负、服务27正/5负；N6平均J +.002872282、服务+1.3943125，但J 14正/18负、median −.005296835。资格增加与未服务减少伴随更高高度惩罚；N8最差J −.078844612，最差服务 −3.334人/步。保留这一训练区组的有界用途，不提升为稳定默认，不识别纯N、技能机制或H6差距已补齐。T6/T8各2.16M/2.88M agent rows、101250/135000次actor与critic优化；sum command157.908843min，重叠批次admission→last exit93.377582min。无旧操作待收，0追加B11 fit。完整Pro答复已核对并采纳；B12固定两个新T6/T8 fits、共同seed963401，训练地址964401–16，在同已读N8/N6世界检验训练区组复现。720k train/64k eval，2 fits已原生准入并实际训练；五项检查和独立审阅通过。原生两臂初始张量、normalizer及RNG一致；张量和采样/RNG状态已确认不同于B11；T6已完整收取并独立验算：1fit/360k train/32k eval，81.932786 command min；N8/N6 J .405497333/.506411159、服务26.0768125/32.8373125人/步。T8原句柄仍运行，配对复现判断待齐。保留高度/尾部代价，不自动第三块或扩展为确认。B04–B06反号、B07/B08有用学习及B10部署取舍保留。[B11完整读数、损失世界与选择](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b11-complete-target-condition-service-gains-with-height-costs-and-adverse-worlds)；[下一科学问题](../../candidates/agent_count_generalization/NOTES.md#pro-question-2026-09-23-training-condition-recurrence-after-b11)；[B12 T6完整读取](../../candidates/agent_count_generalization/NOTES.md#b12-t6-collected-and-independently-read-fixed-t8-remains-running)。 |

## 原 B12 计划

| **DM1：泛化与训练条件** | B11 的目标训练在一个共同初始化区组提高N8原生J与实际服务；N6无均值损失但18/32世界J下降，高度代价上升。B04–B06曾跨训练对反号，稳定训练用途仍未识别。 | **B12已固定：2新fits，各360k train，共64k eval。** 完整Pro已读、同key交付核验后保存全文；采纳新训练区组、保留旧开发世界的比较。共同seed963401，训练964401–16，最终45在1645800–31、1645600–31读取N8主用途及N6后果。新入口、五项检查和独立审阅通过；2 fits均已原生准入，实际共同初始化已核对。T6完整验收，360k train/32k eval、81.932786 command min，N8/N6 J .405497333/.506411159；T8沿原句柄运行，配对复现判断待齐。逐块保留收益、损失世界和高度代价，不合并均值掩盖反号，不默认第三块。[决定、前瞻与L0](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--pro-recurrence-advice-adopted-fixed-b12-training-block-comparison)；[两臂原生运行](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b12-both-fixed-cells-admitted-and-training-same-handle-observation-active)。 |

**DM1 的关键实现与读法。** B11已实际核对共同初始张量、normalizer/RNG、真实N与reward/N、
真实样本行数和优化器次数、最终评价零更新以及共同物理世界。T6/T8各2.16M/2.88M agent rows，
等团队步并不构成等曝光或纯人数因果；Δ8是主用途，Δ6保持专门化后果，未按结果跨N重加权。
B12已选新初始化/采样器seed963401及训练轨迹，原生两臂实际初始张量、normalizer及RNG一致，张量与采样/RNG状态不同于B11；在同已读世界保持评价条件。两正训练区组仍不构成确认，
反号则保留两块而不靠合并均值隐藏。混合条件的宽用途仍为替代，B11的正N6均值不提供平均
专门化损害证据。原B11执行计划已[退役保存](RESEARCH-agent-count-b11-complete.md)。
