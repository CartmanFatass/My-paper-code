# 科研 Portfolio 报告

> OWNER_RESUMED 2026-09-14：所有者已明确恢复科研。2026-09-14 owner-pause handoff 仅作为恢复基线，不再表示当前运行状态。

当前工作集为 **2 个占用方向、1 个预留、0 个未处理空缺**。ACVC 与 FOLR 由原生 Astra/max DM 管理完整生命周期；MGTAP 释放的席位已由 Root 唯一 replacement 请求预留。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| acvc | [ACTIVE/MEDIUM/recasts2](../candidates/acvc/DIRECTION.md)。Portfolio 已选择唯一 final-only 1e-4/3e-4 配对 B：两次 fresh4096 C-only fit、6 个 final 私有面板，合计2195456 ticks /16384 Adam；无新 recast、PARK、default、retry 或自动追加。 | DM 直接完成新卡、窄实现、独立 review、准入、两 originals、intake 和 cleanup，不等待 Root ACK。共享 Portfolio writer 已释放给 Root replacement。 |
| vap_folr_core | [ACTIVE/MEDIUM](../candidates/vap_folr_core/DIRECTION.md)。A−Z 完整结果与独立 review 已 intake；review 接受 d−3.069453125 / CURRENT_ONLY_ABOVE_MEI 的单fit/臂结论，CONTINUE/MEDIUM、family OPEN 不变。 | DM 正把 fresh Z−G 具体化为有界对象；当前无运行进程只是时间点事实。若符合当前 OPEN family 的 object-tier standing delegation，可直接记卡、实现/review、准入和执行，无 Root ACK。 |

## 当前协作边界

- DM 自主完成方向科学、实现、检查、审查、Transport、Monitor、结果 intake 和已授权延续；Root 不对这些步骤逐项审批。
- Direction Convergence 处理方向内科学收敛；`portfolio:cross_direction` 处理投资、优先级、生命周期、容量、融合/分离和注册。只有完整 Portfolio 决定或所有者直接指令才能 PARK/CLOSE 整个方向。
- Root 处理 DM 原生事件、共享依赖、主分支集成和当前记录。Root 使用事件驱动的 `wait_agent`，不以短轮询或 ACK 作为推进门槛。
- MGTAP 的正式 PARK 产生的空缺已由 Root 请求 `2026-09-14-mgtap-park-vacancy-replacement-01` 预留。固定 TASK/HANDOFF 已发布并交给 Root Luna/high Transport；Portfolio 将选择恰好一个方向和首个有界 Astra/max DM 任务。

## 已 PARK / 未占用方向

| 方向 | 当前登记 |
| --- | --- |
| metric_ground_transport_allocation | [Portfolio 可逆 PARKED/MEDIUM](../candidates/metric_ground_transport_allocation/PARK.md)；DENSE default、optional COND、8252/8214 正证据、8253 与8254反证全部保留；0新拟合、无RECAST/CLOSE，已释放1席。 |
| roster_consistent_latent_exploration | [Portfolio 可逆 PARK](../candidates/roster_consistent_latent_exploration/PARK.md)；B10/B12 固定先验、B11 缺失、E01 面板、B13 结果和恢复条件均保全。 |
| degraded_incumbent_shadow_handover | [PARK](../candidates/degraded_incumbent_shadow_handover/PARK.md)；保留 B09、REPLACE/BYPASS 边界和历史证据。 |
| ucope | [PARK](../candidates/ucope/PARK.md)；保留 reactive renewal 结果、反证和重新研究条件。 |
| learned_counterfactual_agent_credit | [PARK](../candidates/learned_counterfactual_agent_credit/PARK.md)；保留 B03 负结果及基线/学习证据。 |

历史 pause 文件、旧分配和结束的对象仍是证据，但不作为当前 dispatch 路由或生命周期状态。新的判断从各 DM 的最新 `DIRECTION.md`、intake、固定 Pro packet 和本报告读取。运行时长参考值不自动触发停止、上报、PARK 或额外授权。
