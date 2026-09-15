# 科研 Portfolio 报告

> OWNER_RESUMED 2026-09-14：所有者已明确恢复科研。2026-09-14 owner-pause handoff 仅作为恢复基线，不再表示当前运行状态。

当前工作集为 **2 个占用方向、0 个预留、1 个正式空缺**。ACVC 与 FOLR 由原生 Astra/max DM 管理完整生命周期；MGTAP 已由完整 Portfolio 决定可逆 PARK 并释放一席。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| acvc | [ACTIVE/MEDIUM/recasts2](../candidates/acvc/DIRECTION.md)。extended-exposure B01 与完整独立 review 均已 intake；review 未发现实质经验/推断缺陷，也未授予新 fit 或 lifecycle。原始证据、Transport 事实、远端回收和保全 inventory 已发布。 | DM 已刷新 MGTAP/FOLR 当前事实并正完成具体投资报告；MGTAP 仍是共享 Portfolio writer，因此 ACVC 暂不 Send。真实节点释放后由 ACVC 直接绑定最新 Portfolio 快照接续，无 Root 科学 ACK。 |
| vap_folr_core | [ACTIVE/MEDIUM](../candidates/vap_folr_core/DIRECTION.md)。entity-persistence B01 的 Z/current-only 已完成：mean 1.59265625、57/128 负值；原始/checkpoint 和真实 Monitor 恢复记录已保全。 | 原定 A/persistent 臂已在同一 source、fresh admission 和第二个既定 invocation 中运行；terminal-only child 在终态以 native final 直接返回，未伪称即时 adoption。DM 随后完成 A−Z intake、独立科学审查和回收；零 retry、原两 invocation 预算不变。 |

## 当前协作边界

- DM 自主完成方向科学、实现、检查、审查、Transport、Monitor、结果 intake 和已授权延续；Root 不对这些步骤逐项审批。
- Direction Convergence 处理方向内科学收敛；`portfolio:cross_direction` 处理投资、优先级、生命周期、容量、融合/分离和注册。只有完整 Portfolio 决定或所有者直接指令才能 PARK/CLOSE 整个方向。
- Root 处理 DM 原生事件、共享依赖、主分支集成和当前记录。Root 使用事件驱动的 `wait_agent`，不以短轮询或 ACK 作为推进门槛。
- MGTAP 的正式 PARK 已产生一个真实空缺。ACVC 当前按既定队列占用共享 Portfolio writer；Root 的 vacancy replacement 请求排在其完整归档/intake 之后，避免并发绑定同一节点。

## 已 PARK / 未占用方向

| 方向 | 当前登记 |
| --- | --- |
| metric_ground_transport_allocation | [Portfolio 可逆 PARKED/MEDIUM](../candidates/metric_ground_transport_allocation/PARK.md)；DENSE default、optional COND、8252/8214 正证据、8253 与8254反证全部保留；0新拟合、无RECAST/CLOSE，已释放1席。 |
| roster_consistent_latent_exploration | [Portfolio 可逆 PARK](../candidates/roster_consistent_latent_exploration/PARK.md)；B10/B12 固定先验、B11 缺失、E01 面板、B13 结果和恢复条件均保全。 |
| degraded_incumbent_shadow_handover | [PARK](../candidates/degraded_incumbent_shadow_handover/PARK.md)；保留 B09、REPLACE/BYPASS 边界和历史证据。 |
| ucope | [PARK](../candidates/ucope/PARK.md)；保留 reactive renewal 结果、反证和重新研究条件。 |
| learned_counterfactual_agent_credit | [PARK](../candidates/learned_counterfactual_agent_credit/PARK.md)；保留 B03 负结果及基线/学习证据。 |

历史 pause 文件、旧分配和结束的对象仍是证据，但不作为当前 dispatch 路由或生命周期状态。新的判断从各 DM 的最新 `DIRECTION.md`、intake、固定 Pro packet 和本报告读取。运行时长参考值不自动触发停止、上报、PARK 或额外授权。
