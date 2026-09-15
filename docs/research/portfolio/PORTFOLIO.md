# 科研 Portfolio 报告

> OWNER_RESUMED 2026-09-14：所有者已明确恢复科研。2026-09-14 owner-pause handoff 仅作为恢复基线，不再表示当前运行状态。

当前工作集为 **4 个占用方向、0 个预留、0 个空缺**。ACVC、FOLR 与 TRDL 延续各自链；所有者于 2026-09-14 直接恢复 FSD 为第四条并行链，不挤占前三个方向，也不等待 Portfolio 重复准入。四个方向均由原生 Astra/max DM 管理完整生命周期。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| acvc | [ACTIVE/MEDIUM/recasts2](../candidates/acvc/DIRECTION.md)。fixed-rate B 已完成：primary lowC−refC −.1285335613 J（DOWN），两率F对照均UP；限于一个匹配训练block。 | 完整科学/计划 review 已固定并dispatch，尚未声称provider接受；范围是科学review/建议，不产生lifecycle finality。DM同时执行exact remote reclamation，随后完整intake；无第三fit/retry。 |
| vap_folr_core | [ACTIVE/MEDIUM](../candidates/vap_folr_core/DIRECTION.md)。fresh Z−G B 的G已完成：mean4.307734375、native2112.27s；普通1800s计划超出不是hard cap或科研违约。 | 卡内Z已在同source与fresh admission下接受，terminal-only Monitor仅观察Z；两原始均已接受、retry0。Z终态后由同一DM完成Z−G intake/review，不拼接旧比较。 |
| tail_return_distributional_learning | [ACTIVE/MEDIUM/recasts0](../candidates/tail_return_distributional_learning/DIRECTION.md)。零暴露A01和具体 prospective B01 card 已完成；scalar与Q32被明确为学习同一lower-tail目标W的两种方法。 | 唯一 Portfolio B01投资请求已固定并dispatch，尚未声称provider接受；只决定一pair及最小实现验证，不问vacancy/priority/lifecycle。393216 ticks/256 Adam仍是方案计数，旧3000秒offer未拨款。 |
| flexible_skill_duration | [ACTIVE/HIGH](../candidates/flexible_skill_duration/DIRECTION.md)。limited optional I1280与D0 default保留；2026-09-05 PARK只约束固定K2 corridor分支，旧no-current-addition不是整个方向的PARK。 | OWNER_DIRECT已恢复原方向DM；正在刷新事实并读取重启建议，准备中断×batch归因、同宿主基线与独立训练精度。当前是设计准备，尚无新fit、冻结卡或新增cap。 |

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
