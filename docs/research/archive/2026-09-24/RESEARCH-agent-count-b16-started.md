# Agent-count plan before B16 execution — retired 2026-09-24

Historical DM1 sections from `RESEARCH.md` at published main `06d8adbe513c2492baa5ec49b0deabe62da0fcb8`.
The adopted B16 plan has now passed implementation/review and its first fixed cell is running.
This extraction preserves superseded standing, plan and routing; it does not change B15
results, archive the direction or retire the active B16 operation. Current work remains in
[RESEARCH](../../RESEARCH.md) and the direction notebook.

## Direction standing

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | **B15六fit已完成，联合确认未建立；B16普通局部对照已采纳。** B15固定N8条件下J均值+.071049，95%区间[−.0000079125,.142106493]；服务+4.327729人/步，区间[−.876090,9.531549]，不扩样、不改判读。完整Pro答复已读并保存；B16固定三份新local1、N6各360k，复用全部已曝光B15区组/初末面板作为开发参照，主读L−SET，H6−L仅为剩余包差。正在实现和独立审阅，尚未启动fit；L败不认证SET充分或技能必要。[完整答复与B16前瞻/L0](../../candidates/agent_count_generalization/NOTES.md#2026-09-24--pro-advice-adopted-and-b16-local-ordinary-comparison-fixed)。[B15完整结果](../../candidates/agent_count_generalization/NOTES.md#2026-09-24--b15-complete-positive-block-means-do-not-establish-the-joint-claim)、[固定claim及结果](../../candidates/agent_count_generalization/CLAIM_bounded_count_transfer_20260923.md)。[任务路由](../../RESEARCH.md#session-routing)。 |

## Direction plan

| Direction | Fixed work and exposure | Scientific reading |
| --- | --- | --- |
| DM1：泛化与训练条件 | B15全部完成：6fits，2.16M train+384k eval，累计6.521557科学命令小时；[固定claim与结果](../../candidates/agent_count_generalization/CLAIM_bounded_count_transfer_20260923.md)。拟议下一项为局部观察普通循环对照，先完成比较器科学论证，未选新fit。 | J/服务均值正，但预写df2区间下界未越过0/1，联合确认未建立。自身学习、N6反号及局部服务损失分别保留；不扩样、不把已读世界重新称为确认，也不以差异不显著证明机制等价。 |

## Session routing

| Role | Task | Checkout | Continuation |
| --- | --- | --- | --- |
| DM1：智能体数量泛化 DM | `01a0c6ef-cdd4-7113-b2d9-20487e35171b` / `local` | `/home/fires/.codex/worktrees/7fef/hmasd-wsl` · `codex/agent-count-generalization` | B15六fit及固定判读已完整发表；同key恢复的Pro全文已保存并读毕，后继[B16普通局部对照前瞻与L0](../../candidates/agent_count_generalization/NOTES.md#2026-09-24--pro-advice-adopted-and-b16-local-ordinary-comparison-fixed)已采纳，沿notebook接续实现/审阅/原生执行。 |
