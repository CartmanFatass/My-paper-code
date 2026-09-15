# 科研 Portfolio 报告

> OWNER_RESUMED 2026-09-14：所有者已明确恢复科研。2026-09-14 owner-pause handoff 仅作为恢复基线，不再表示当前运行状态。

当前工作集为 **3 个占用方向、0 个预留、0 个空缺**。ACVC、FOLR 与 TRDL 均由原生 Astra/max DM 管理完整生命周期；MGTAP 释放的席位已由完整 Portfolio 决定交给 TRDL。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| acvc | [ACTIVE/MEDIUM/recasts2](../candidates/acvc/DIRECTION.md)。fixed-rate B 已完成：primary lowC−refC −.1285335613 J（DOWN），两率F对照均UP；各4096train/8192Adam/192eval、exit0，限于一个匹配训练block。 | DM 继续完整 Convergence 科学/计划 review 与 exact remote reclamation；无第三fit/retry，保留3e-4 reference与optionalF。先前未获支持的Monitor adoption/time字段已更正，不声称live coverage。 |
| vap_folr_core | [ACTIVE/MEDIUM](../candidates/vap_folr_core/DIRECTION.md)。fresh Z−G B 已按 object-tier standing delegation 选定；卡、实现、独立review、检查和exact命令已接受，两原始各5000/4969/128。 | G handle 在 source8ad304d61 与 fresh admission 下运行；terminal-only Monitor 已接任务但未伪称adoption。G终态后由同一DM收集并fresh admission启动卡内Z；retry0，不把A−Z与旧A−G拼成排名。 |
| tail_return_distributional_learning | [ACTIVE/MEDIUM/recasts0](../candidates/tail_return_distributional_learning/DIRECTION.md)。零暴露A01和具体 prospective B01 card 已完成；scalar与Q32被明确为学习同一lower-tail目标W的两种方法。 | 唯一 Portfolio B01投资请求已固定并dispatch，尚未声称provider接受；只决定一pair及最小实现验证，不问vacancy/priority/lifecycle。393216 ticks/256 Adam仍是方案计数，旧3000秒offer未拨款。 |

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
