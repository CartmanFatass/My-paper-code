# 科研 Portfolio 报告

当前目标是三个并行方向。DM 负责方向完整生命周期；方向 Pro Convergence 是独立科学
Reviewer；Clerk 负责协调、记录和真实缺位的 Portfolio 补位；Root 是用户入口。
停止第四个方向仅限制扩容，不暂停 Portfolio，也不停止三方向内的接续。

## 当前工作集

以下是已接受事件的快照，实时路由、占位和请求状态以
[当前登记表](../../../.codex/hmasd-dm-sessions.toml) 为准。占位不等同于正在训练。

| 方向 | 已接受进展 | 当前工作与下一责任人 |
| --- | --- | --- |
| [UCOPE](../candidates/ucope/DIRECTION.md) | reactive renewal B01 已进入远程执行链，ACTIVE/HIGH。 | 最新登记为远程 producer 已接管；DM 负责 terminal collection、intake 和后续决定。 |
| [LCAC](../candidates/learned_counterfactual_agent_credit/DIRECTION.md) | B01 差值 −0.00362643，within MEI；结果复核已派发。 | 独立结果 review 链在途，DM 负责实质回应和接续决定。 |
| [ACVC](../candidates/acvc/DIRECTION.md) | [Portfolio 已选择 ACVC 填补 DISH 空缺](decisions/2026-09-14-acvc-dish-vacancy-selection.md)，Astra/max DM 已落实。 | DM 已读取旧 PARK、DIRECTION、B02 intake/review，正在处理 repeatability 问题与选择证据；尚未选定新科学对象。 |

当前 UCOPE、LCAC、ACVC 三个实际 DM 占位，预留槽位为零。ACVC 正式任务为
`01a09dfa-0655-7831-aa3a-9fff2ddd2508`，复用原 codex/acvc authoring checkout；
重复创建的任务已归档且无写入或科研副作用。补位不代表自动选择实验、增加预算或接受有利结论；
DM 依据完整选择证据和既有 claim limits 自主决定下一研究对象或生命周期。

ACVC 的[历史 PARK 知识](../candidates/acvc/PARK.md)继续保留，供当前 DM intake；它不代表当前任务已归档。

## 已归档方向的知识入口

| 方向 | 最新处置与保留资产 |
| --- | --- |
| [DISH](../candidates/degraded_incumbent_shadow_handover/PARK.md) | B09 差值 −35.25；保留 REPLACE，结束 BYPASS 扩展；方向已可逆 PARK 并归档。 |
| [MGTAP](../candidates/metric_ground_transport_allocation/PARK.md) | 已科学 PARK 并归档；保留 COND/DENSE 结果、相反证据与解释边界。 |
| [RCLE](../candidates/roster_consistent_latent_exploration/PARK.md) | 已科学 PARK 并归档；不再计为活跃槽位，保留研究启示与重新进入条件。 |
| [FOLR](../candidates/vap_folr_core/PARK.md) | 已科学 PARK 并归档；保留 reference-use 知识、证据和局限。 |

其他方向的研究入口见 [Research map](../RESEARCH_MAP.md) 和各自 DIRECTION.md；它们不因
历史 ACTIVE 标签自动计入当前工作集。已有实验与历史决策保留原始出处，不从旧报告推断
新的运行、暂停或授权。重新纳入工作集由当前容量下的 Portfolio 选择或用户明确决定触发。

## 维护规则

Clerk 根据 DM 实际回报更新本报告、登记表和下一动作。一个事件同步更新当前结论、
生命周期、占位与在途工作，替换失效断言，不追加互相矛盾的状态表。
科学判断归 DM；历史证据不改写。真实 PARK/CLOSE 释放槽位后，Clerk 按三槽目标自动请求
Portfolio 补位，无需 Root 再授权。其他跨方向布局或新资源承诺仍需用户明确范围。

Heartbeat 登记为 MISSING，不能声称定时恢复已运行；当前协调依赖实际消息事件。
