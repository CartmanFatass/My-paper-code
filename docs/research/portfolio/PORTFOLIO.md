# 科研 Portfolio 报告

> OWNER_RESUMED 2026-09-14：所有者已明确恢复科研。2026-09-14 owner-pause handoff 仅作为恢复基线，不再表示当前运行状态。

当前工作集为 **3 个占用方向、0 个预留、0 个空缺**。三个方向均由原生 Astra/max DM 管理完整生命周期；对象完成、实验结束、Transport 等待或临时工程恢复均不释放方向席位。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| [ACVC](../candidates/acvc/DIRECTION.md) | ACTIVE/MEDIUM/recasts2。extended-exposure B01 已完成并 intake：4096 F−C +0.1168642320 J、F−dwell +0.0923540717 J、G_dwell +0.0295386263 J，四端点 UP；保留 one-programme、非 tuned、训练波动与全部不利世界限制。 | 独立 Convergence 审查请求 `2026-09-14-acvc-cluster-extended-exposure-b01-scientific-review-01` 已固定并 dispatch，尚未把 dispatch 误记为 provider 接受。DM 的 Transport 负责 reconciliation 和完整响应归档；远端精确回收已完成，清理证据待与 intake 一并提交。 |
| [MGTAP](../candidates/metric_ground_transport_allocation/DIRECTION.md) | ACTIVE/MEDIUM，DENSE default 保留。fresh8254 late-exposure B01 已完成：512 COND−DENSE −0.0053750132 J（INSIDE_MEI），256 描述性差 +0.0083702794，gap change −0.0137452926；仅一个训练配对，不能解释为等价或稳定劣势。 | 原 Convergence 完整回答已结束当前 fixed1e-4/512 exposure exploration，明确无补跑、无整方向 PARK/CLOSE、无席位释放。DM 正完成该回答 intake，并准备向 `portfolio:cross_direction` 提交 optional COND 整方向维护/再投资问题。当前未发现另一个 accepted Portfolio writer。 |
| [FOLR](../candidates/vap_folr_core/DIRECTION.md) | ACTIVE/MEDIUM。entity-persistence B01 的 Z/current-only 已完成：mean 1.59265625、57/128 负值；原始/checkpoint 和真实 Monitor 恢复记录已保全。 | 原定 A/persistent 臂已在同一 source、fresh admission 和第二个既定 invocation 中运行；terminal-only child 在终态以 native final 直接返回，未伪称即时 adoption。DM 随后完成 A−Z intake、独立科学审查和回收；零 retry、原两 invocation 预算不变。 |

## 当前协作边界

- DM 自主完成方向科学、实现、检查、审查、Transport、Monitor、结果 intake 和已授权延续；Root 不对这些步骤逐项审批。
- Direction Convergence 处理方向内科学收敛；`portfolio:cross_direction` 处理投资、优先级、生命周期、容量、融合/分离和注册。只有完整 Portfolio 决定或所有者直接指令才能 PARK/CLOSE 整个方向。
- Root 处理 DM 原生事件、共享依赖、主分支集成和当前记录。Root 使用事件驱动的 `wait_agent`，不以短轮询或 ACK 作为推进门槛。
- 当前没有空缺，因此不创建替代方向。MGTAP 的 Portfolio 问题由其作者 DM 拥有，使用共享节点单 writer 约束；ACVC 的 Direction Convergence 请求不占用 Portfolio writer。

## 已 PARK / 未占用方向

| 方向 | 当前登记 |
| --- | --- |
| [RCLE](../candidates/roster_consistent_latent_exploration/PARK.md) | Portfolio 可逆 PARK；B10/B12 固定先验、B11 缺失、E01 面板、B13 结果和恢复条件均保全。 |
| [DISH](../candidates/degraded_incumbent_shadow_handover/PARK.md) | PARK；保留 B09、REPLACE/BYPASS 边界和历史证据。 |
| [UCOPE](../candidates/ucope/PARK.md) | PARK；保留 reactive renewal 结果、反证和重新研究条件。 |
| [LCAC](../candidates/learned_counterfactual_agent_credit/PARK.md) | PARK；保留 B03 负结果及基线/学习证据。 |

历史 pause 文件、旧分配和结束的对象仍是证据，但不作为当前 dispatch 路由或生命周期状态。新的判断从各 DM 的最新 `DIRECTION.md`、intake、固定 Pro packet 和本报告读取。运行时长参考值不自动触发停止、上报、PARK 或额外授权。
