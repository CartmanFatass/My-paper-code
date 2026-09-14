# 科研 Portfolio 报告

当前目标为三个占用与预留席位。Portfolio 按 [当前决策协议](../../project/PORTFOLIO_DECISION_PROTOCOL.md)
作方向层面的最终综合判断；DM 负责创新、实验、实现、证据报告和执行，普通实验不逐项申请批准。
中央 Clerk 已退休，DM 平等协调，Root 是用户入口。以下是已发布证据和当前登记的摘要，
实时席位、实际 producer 与同会话请求顺序以 [共享登记表](../../../.codex/hmasd-dm-sessions.toml) 为准。

## 当前三席

| 方向 | 已知科学位置 | 当前工作与席位 |
| --- | --- | --- |
| [RCLE](../candidates/roster_consistent_latent_exploration/DIRECTION.md) | B10/B12 有真实自身学习与 nearest 收益，但 sampled 服务仍落后 greedy；E01 两套保留 mode 的所有已测结局与 greedy 相等，零新拟合。完整审查已回应，恢复代价和 B11 缺失/未知 SIG11 保留。 | 占用1席，pending_portfolio_decision。[完整报告](../candidates/roster_consistent_latent_exploration/pro_packets/20260914_e01_portfolio_direction/REPORT.md)建议一个可学习先验强度 B，尚未应用或启动；等待 FOLR 同会话前序完成/归档后提交。 |
| [MGTAP](../candidates/metric_ground_transport_allocation/DIRECTION.md) | 历史混合符号保留，DENSE 仍为通用默认；新问题比较对称学习率选择后的完整学习程序。 | 占用1席。LR-SELECTION-B01 的8拟合/589,824 team ticks/4,096 Adam 是计划工作；runner 与独立审查推进，尚无本报告可引用的新原生结果。DM 负责实际接受、准入、执行和结果解释。 |
| [FOLR](../candidates/vap_folr_core/DIRECTION.md) | B02 一个 fresh/fresh 对比 BANK−Generic=−4.830859375。DM 已修正把局部负结果推成停止理由的不足，推荐一个新的同预算 B03 来观察复现性。 | 预留1席，pending_portfolio_decision。完整报告已交独立 Transport，当前 Portfolio 同会话作者为 FOLR；B03 实现/独立工程审查推进，零已报告的新原生曝光。 |

上述席位为2占用+1预留，总计3。RCLE/FOLR 的建议不是已应用的 PARK、CLOSE、CONTINUE 或新运行。
停止第四个方向限制扩容，不停止三席中的研究和接续。旧报告的 UCOPE/LCAC/ACVC 工作集和
RCLE/MGTAP/FOLR 归档表已经过期，不能用来判断现在是否“开始后直接结束”。

RCLE 当前完整审查/回应固定于93bb8ffcd4de430a722bbb6b84e9733f40d26782与
6f13c2b2fa713414e777190b7bcfbec11243b61a；新报告及一次未定位原因的保留权重分析见
094d1ff2a3e5f984d62e00dae782cda31a11be52。MGTAP 当前科学卡/重入依据见
3594eafe28ed91b2558fcc064e46ea714edd2e1c；FOLR 的完整修正与推荐卡见
fb38cbfadd69f578672f6918ebc2824338919040。这里引用已有 DM 结论，不新增跨方向的数值排序。

## 已归档方向的知识入口

| 方向 | 保留知识与当前限制 |
| --- | --- |
| [DISH](../candidates/degraded_incumbent_shadow_handover/PARK.md) | 保留 B09 −35.25、REPLACE 与 BYPASS 边界；旧 Portfolio 补位建议未应用，不能抢占 FOLR 的预留席位。 |
| [UCOPE](../candidates/ucope/PARK.md) | 保留 reactive renewal 的结果、反证和重新研究条件；当前未占用席位。 |
| [LCAC](../candidates/learned_counterfactual_agent_credit/PARK.md) | 保留 B03 负结果及基线/学习证据；当前未占用席位。 |
| [ACVC](../candidates/acvc/PARK.md) | 保留实际部署/重复性证据和完整 Portfolio 交流；当前未占用席位。 |

其他方向见 [Research map](../RESEARCH_MAP.md)。历史决定保留原始出处；当前 owner 挑战和
Portfolio 的新决定前瞻应用，不擅自重写结果或批量重启旧方向。

## 当前交接与成本口径

FOLR 请求2026-09-14-folr-portfolio-direction-reconciliation-01先处理，RCLE 请求
2026-09-14-rcle-e01-direction-decision-01随后；同一会话只保留一个在途请求，完整答复归档后交接。
旧6aa7836e会话答复已由552f0dce7904e35206b8e32f9180ab85aee822ad保全，其 DISH 建议未应用。
新的 Portfolio 决定须基于实际读取的固定权限、全局上下文、完整结果/反证/审查和 DM 回应。

support600s 与普通 wall 规划是允许误差的参考，不是自动停止、Send 或升级条件。
实际 owner/平台资源边界和冻结科学端点仍适用；未知费用保留 UNKNOWN，不变成0或 PARK 理由。
Heartbeat 登记仍为 MISSING，不能声称定时恢复已运行。当前依赖真实 producer 和直接消息交接。
