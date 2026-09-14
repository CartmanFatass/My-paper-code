# 科研 Portfolio 报告

当前目标为三个占用与预留席位。Portfolio 按 [当前决策协议](../../project/PORTFOLIO_DECISION_PROTOCOL.md)
作方向层面的最终综合判断；DM 负责创新、实验、实现、证据报告和执行，普通实验不逐项申请批准。
中央 Clerk 已退休，DM 平等协调，Root 是用户入口。以下是已发布证据和当前登记的摘要，
实时席位、实际 producer 与同会话请求顺序以 [共享登记表](../../../.codex/hmasd-dm-sessions.toml) 为准。

## 当前三席

| 方向 | 已知科学位置 | 当前工作与席位 |
| --- | --- | --- |
| [RCLE](../candidates/roster_consistent_latent_exploration/DIRECTION.md) | B13 实际学习 G_U=+0.072437，nearest 收益+0.154964，greedy 对比-0.019784；先验强度学到1.211991，modal 与 greedy 全512行测量相同，恢复取舍和 B11 缺失保留。 | 占用1席，完整 Portfolio CONTINUE 已读取、回应并应用。选定 B13 已完成1,024更新/4,358,144ticks，完整命令163.92s、exit0；完整原始证据已校验。[结果与 intake](../candidates/roster_consistent_latent_exploration/RCLE_B13_LEARNED_PRIOR_INTAKE_20260914.md)。独立 B13 实际结果审阅已派发，等待完整答复；未默认追加 seed 或 PARK/CLOSE。 |
| [MGTAP](../candidates/metric_ground_transport_allocation/DIRECTION.md) | 对称有限选率双方均选1e-4；全新8252主量+0.023704897713093642 J，COND_ABOVE_MEI。一次选择/一对最终训练，历史混合符号和DENSE通用默认保持；不声称稳定排序或调参收益。 | 占用1席。8拟合/589824ticks/4096Adam完整完成，658.02s、exit0，原始证据保全。166行独立结果审查已读并实质回应；[完整方向报告](../candidates/metric_ground_transport_allocation/pro_packets/20260914_lr_selection_portfolio_direction/REPORT.md)及固定请求已交既有Transport，等待Portfolio完整方向答复；provider接受尚未核实。建议固定率新配对而非已启动后继实验；无槽位变更。 |
| [FOLR](../candidates/vap_folr_core/DIRECTION.md) | B02 完整学习比较 BANK−Generic=−4.830859375，有限负面证据保持。Portfolio 已撤回原停止理由，选择 B03 观察新完整学习程序的结果变化；训练与评估变异不能单独分离。 | 占用1席，CONTINUE / MEDIUM。B03 Generic 已于08:24 UTC在固定源码远端分离运行，相邻内存准入通过，专属 native Monitor 已接管；BANK 待 Generic 收集后运行，尚无完整 B03 主比较。[执行记录](../candidates/vap_folr_core/entity_history_b03_781501/EXECUTION.json)。 |

上述席位为3占用+0预留，总计3。FOLR 与 RCLE 的完整 CONTINUE 均已应用；RCLE 的 B13 已实际运行完成。方向裁决和实际执行分别记录。
停止第四个方向限制扩容，不停止三席中的研究和接续。旧报告的 UCOPE/LCAC/ACVC 工作集和
RCLE/MGTAP/FOLR 归档表已经过期，不能用来判断现在是否“开始后直接结束”。

RCLE 当前完整审查/回应固定于93bb8ffcd4de430a722bbb6b84e9733f40d26782与
6f13c2b2fa713414e777190b7bcfbec11243b61a；新报告及一次未定位原因的保留权重分析见
094d1ff2a3e5f984d62e00dae782cda31a11be52。MGTAP 当前科学卡/重入依据见
3594eafe28ed91b2558fcc064e46ea714edd2e1c；FOLR 的完整裁决、修正及实际应用见
4776103de4f55beaee610c52506112651bfaed04。这里引用已有 DM 结论，不新增跨方向的数值排序。

## 已归档方向的知识入口

| 方向 | 保留知识与当前限制 |
| --- | --- |
| [DISH](../candidates/degraded_incumbent_shadow_handover/PARK.md) | 保留 B09 −35.25、REPLACE 与 BYPASS 边界；旧 Portfolio 补位建议未应用；新裁决已选择继续 FOLR，当前没有空槽。 |
| [UCOPE](../candidates/ucope/PARK.md) | 保留 reactive renewal 的结果、反证和重新研究条件；当前未占用席位。 |
| [LCAC](../candidates/learned_counterfactual_agent_credit/PARK.md) | 保留 B03 负结果及基线/学习证据；当前未占用席位。 |
| [ACVC](../candidates/acvc/PARK.md) | 保留实际部署/重复性证据和完整 Portfolio 交流；当前未占用席位。 |

其他方向见 [Research map](../RESEARCH_MAP.md)。历史决定保留原始出处；当前 owner 挑战和
Portfolio 的新决定前瞻应用，不擅自重写结果或批量重启旧方向。

## 当前交接与成本口径

FOLR 请求2026-09-14-folr-portfolio-direction-reconciliation-01已完成并应用 CONTINUE；
完整答复保全于4776103de4f55beaee610c52506112651bfaed04。RCLE 请求
2026-09-14-rcle-e01-direction-decision-01完整答复已按一次 Send 归档，20,895字节/SHA256 7c7476fca152aec673c7ff0974ae182c0ef30c091e230a4ba7039ac71f06a416；CONTINUE 于5f4abd6f应用，B13随后实际完成，完整证据见c58ec2fb4。该对话现已释放，没有新空缺。
旧6aa7836e会话答复已由552f0dce7904e35206b8e32f9180ab85aee822ad保全，其 DISH 建议未应用。
新的 Portfolio 决定须基于实际读取的固定权限、全局上下文、完整结果/反证/审查和 DM 回应。

support600s 与普通 wall 规划是允许误差的参考，不是自动停止、Send 或升级条件。
实际 owner/平台资源边界和冻结科学端点仍适用；未知费用保留 UNKNOWN，不变成0或 PARK 理由。
Heartbeat 登记仍为 MISSING，不能声称定时恢复已运行。当前依赖真实 producer 和直接消息交接。
