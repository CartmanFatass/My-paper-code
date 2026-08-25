# OMP → Codex 迁移文档

本目录记录从已实现的 OMP 工作流迁移到 Codex 的当前决策与实施计划。
OMP 原始设计与实现合同保留在：

- `docs/plans/2026-08-24-omp-autonomous-multidirection-research-concept.md`
- `docs/plans/2026-08-24-omp-autonomous-multidirection-research-implementation.md`

它们是行为基线和设计历史，不会被改写成 Codex 文档。

当前 Codex 迁移文档：

- `CODEX_MIGRATION_RECOMMENDATION.md`：新拓扑、权威边界和迁移决策。
- `2026-08-25-codex-single-layer-task-migration-implementation.md`：分阶段实施计划与验收标准。

目录中以 `2026-08-24-omp-` 开头的文件是 OMP 设计历史快照，不是 Codex
执行配置。它们保留原始 Linux/WSL 示例（例如 `/home`、`/mnt`、`python3` 和
Hub 命令）作为 provenance；Windows Codex 不得把这些示例路径或命令直接传给
执行器。当前执行面只使用仓库内相对 POSIX authority 路径、Windows 原生 Git/
Python，以及 `.codex/config.toml` 注册的角色。

当前决策的核心是：Root、Portfolio、EM、CM 使用项目中的同级顶层 Codex
task，每个 task 内部最多派生一层直接 subagent。Root 是有完整操作权限的低成本
orchestrator；Portfolio 使用 Sol max，按周期或用户互动形成跨方向决定并发送给
Root 编排，而不是直接持有 EM/CM。
