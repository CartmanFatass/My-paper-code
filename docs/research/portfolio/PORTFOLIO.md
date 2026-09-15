# 科研 Portfolio 报告

> OWNER_RESUMED 2026-09-14：所有者已明确恢复科研。2026-09-14 owner-pause handoff 仅作为恢复基线，不再表示当前运行状态。

当前工作集为 **4 个占用方向、0 个预留、0 个空缺**。ACVC、FOLR 与 TRDL 延续各自链；所有者于 2026-09-14 直接恢复 FSD 为第四条并行链，不挤占前三个方向，也不等待 Portfolio 重复准入。四个方向均由原生 Astra/max DM 管理完整生命周期。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| acvc | [ACTIVE/MEDIUM/recasts2](../candidates/acvc/DIRECTION.md)。fixed-rate B与review已完成；后续零暴露评估确认原HMASD的集中式global-state技能选择不能直接充当private-actor ACVC的同信息基线。 | DM正准备flat recurrent MAPPO-style对比的有限Portfolio投资包；当前0新fit/代码执行。shared writer由FSD占用，ACVC尚未绑定或发送。 |
| vap_folr_core | [ACTIVE/MEDIUM](../candidates/vap_folr_core/DIRECTION.md)。fresh Z−G完整：Z −.136015625、G 4.307734375、差−4.44375，支持本次Generic对照；两臂各一个fit，旧A−G正结果仍为强反例。 | 完整Convergence review已intake，支持准备两块fresh A−G并保留一块低成本备选；DM直接记卡、实现、审查与准入，尚无新调用。远端对象已回收。 |
| tail_return_distributional_learning | [ACTIVE/MEDIUM/recasts0](../candidates/tail_return_distributional_learning/DIRECTION.md)。B01两原始完成：Q32−SCALAR lower-tail差+.0345634681 J；每臂一个训练实例，支持完整配方B，不支持稳定优势或组件归因。 | 完整Convergence response已归档，DM正在intake并准备master9602 unchanged-recipe pair的有限投资材料；0追加grant/launch。shared writer由FSD占用，TRDL尚未绑定或发送。 |
| flexible_skill_duration | [ACTIVE/HIGH](../candidates/flexible_skill_duration/DIRECTION.md)。OWNER_DIRECT恢复后已实际读取重启建议；完整2×2归因为首选准备，两臂I1280/D0-1280为有限备选，旧证据与D0 default保持。 | 唯一Portfolio请求 `2026-09-14-fsd-interruption-batch-investment-01` 已原生dispatch并占用shared writer；等待provider/full response，当前0训练/handle。 |

## 当前协作边界

- DM 自主完成方向科学、实现、检查、审查、Transport、Monitor、结果 intake 和已授权延续；Root 不对这些步骤逐项审批。
- Direction Convergence 处理方向内科学收敛；`portfolio:cross_direction` 处理投资、优先级、生命周期、容量、融合/分离和注册。只有完整 Portfolio 决定或所有者直接指令才能 PARK/CLOSE 整个方向。
- Root 处理 DM 原生事件、共享依赖、主分支集成和当前记录。Root 使用事件驱动的 `wait_agent`，不以短轮询或 ACK 作为推进门槛。
- vacancy 请求 `2026-09-14-mgtap-park-vacancy-replacement-01` 已完整归档并应用：选择 TRDL，占用第三席；Root Transport 已结束。新的 vacancy 只有在未来正式 Portfolio/owner lifecycle 处置释放席位时才产生。

## 已 PARK / 未占用方向

| 方向 | 当前登记 |
| --- | --- |
| metric_ground_transport_allocation | [Portfolio 可逆 PARKED/MEDIUM](../candidates/metric_ground_transport_allocation/PARK.md)；DENSE default、optional COND、8252/8214 正证据、8253 与8254反证全部保留；0新拟合、无RECAST/CLOSE，已释放1席。 |
| roster_consistent_latent_exploration | [Portfolio 可逆 PARK](../candidates/roster_consistent_latent_exploration/PARK.md)；B10/B12 固定先验、B11 缺失、E01 面板、B13 结果和恢复条件均保全。 |
| degraded_incumbent_shadow_handover | [PARK](../candidates/degraded_incumbent_shadow_handover/PARK.md)；保留 B09、REPLACE/BYPASS 边界和历史证据。 |
| ucope | [PARK](../candidates/ucope/PARK.md)；保留 reactive renewal 结果、反证和重新研究条件。 |
| learned_counterfactual_agent_credit | [PARK](../candidates/learned_counterfactual_agent_credit/PARK.md)；保留 B03 负结果及基线/学习证据。 |

历史 pause 文件、旧分配和结束的对象仍是证据，但不作为当前 dispatch 路由或生命周期状态。新的判断从各 DM 的最新 `DIRECTION.md`、intake、固定 Pro packet 和本报告读取。运行时长参考值不自动触发停止、上报、PARK 或额外授权。
