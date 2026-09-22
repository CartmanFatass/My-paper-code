# Retired count action-law execution status — 2026-09-22

Retired when B02 was fully read and B03 became the remaining selected comparison. Other directions and plans are unchanged.

## Previous direction standing

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B01 六个 360k fits 完整核验，N4/6/8 的 H6−SET J 为 +.021721/+.044000/+.045222；保留实际 raw-action 实现下的探索收益，未验证声明动作边界。owner 继续研究；新 Pro 全文已核验、从聊天完整存档并采纳。B02 评估器已通过 DM/独立审查及远端 16 项检查，以源码 dd25f34a0 准入运行：六个冻结策略 raw/clip 部署比较，0 fits、288k eval steps；原生操作句柄已保存并自动观察。B03 固定四格及执行顺序，代码实现中：H6/SET × raw/clip 训练动作执行，统一 clip 部署，单个新训练区组共 4 fits、1.44M train+384k eval steps；无新训练已启动，无自动确认/十二 fits。平均零效应不排除轨迹分歧，差距缩小也不等于 SET 恢复。[完整建议、采纳与固定设计](candidates/agent_count_generalization/NOTES.md#2026-09-22--full-pro-reading-b02-execution-probe-and-b03-investment-decision)。 |

## Previous count plan

| Topic | Current selection | Next reading |
| --- | --- | --- |
| **N 数量泛化** | B02 冻结执行比较已准入运行并自动观察；B03 单区组训练动作法判别实现中，0 新 fits 已启动。 | B02 在相同新世界读旧策略 raw/clip 的完整服务与轨迹差异（0 fits、288k eval steps）；B03 保持原始高斯及熵/PPO 评分，仅改变向环境执行的动作，四格统一 clip 部署（4 fits）。选择性 SET 恢复需 SET 自身 J 改善且改善超过 H6；H6 单独受损不算。保留单区组与历史曝光边界，不据均值零效应声称等价，不自动确认或调参。[固定方案与判读](candidates/agent_count_generalization/NOTES.md#2026-09-22--full-pro-reading-b02-execution-probe-and-b03-investment-decision)；[验收与原生操作](candidates/agent_count_generalization/NOTES.md#2026-09-22--b02-engineering-acceptance-and-b03-implementation-scope)；[退役的咨询提案状态](archive/2026-09-22/RESEARCH_06.md)。 |
