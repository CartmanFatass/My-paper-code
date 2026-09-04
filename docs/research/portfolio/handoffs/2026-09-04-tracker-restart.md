# Tracker 配置重载前的研究交接

Status: `DRAIN_CURRENT_ROUND / NOT_FINAL`
Updated: 2026-09-04T22:31:47Z

本文件仍在收尾中。执行边界见
[所有者收尾指令](../decisions/2026-09-04-drain-for-tracker-restart.md)。本轮全部结束前不重启，
不补位，不创建下一轮实验。方向生命周期与优先级不变。

Root task: `01a06df5-528a-7b32-8475-9b098c2b33c2`.
Integration checkout: `C:/Projects/HMASD-worktrees/root-integration-02-20260904`.
Branch: `codex/root-integration-02-20260904`, upstream `origin/main`.
Saved project `C:/Projects/HMASD` has unrelated owner edits; preserve them.

## 待完成的边界

| 方向 | 当前事实 | 待收尾 |
| --- | --- | --- |
| FSD | 当前 medium_d0_seed3 supervisor 退出 0 | CM 验证和 DM intake；下一格不创建 |
| FRRIE | r04 supervisor 退出 1 | 有界复现/技术 intake；attempt05 不创建 |
| CBSC | 当前资源处理修复/审查中 | focused/offline formal 验证、scope 违例与最终工程 return；r08 不创建 |
| N5 | B02 卡片已冻结，实现中 | 当前成本 pilot 与可被接纳的同卡固定 panel，或具名阻塞边界 |
| N3 | B04_WITHIN_MEI，DM 已完成 | Root 整合已推送的结果、曲线、brief |
| CRTO | A03 有效且无超过 MEI 的改善，已整合 | 保留下一判别建议，不启动 |
| UCOPE | 127/219 orchestration scope 阻塞，工作树清洁 | 保留交接，不重新实现 |

## 配置重载事项

已安装的 role：`.codex/agents/hmasd-experiment-tracker.toml`，固定 Luna/xhigh，含本地和
远端 instructions。当前临时实例 `/root/tracker_lxh_experiments` 以 default 启动，不能
写成已成功加载 custom role。其记录在 [EXPERIMENT_TRACKING.md](../EXPERIMENT_TRACKING.md)。

原生 sibling 的双向发送和 idle 唤醒均已通过两个 custom DM 实测；见
[SIBLING_COMMUNICATION.md](../../../project/SIBLING_COMMUNICATION.md)。新 runtime 的第一步
是检查角色发现和一次实际 DM ACK；不得因为旧实例没有工具而改用被拒绝的 app-server
消息接口，也不重复提交实验或 Pro 请求。

最终主线 commit、各方向证据/工作树/下一步、所有进程与 Transport 核对、heartbeat PAUSED
状态和 owner reviews 将在各方向本轮完成后补齐。
