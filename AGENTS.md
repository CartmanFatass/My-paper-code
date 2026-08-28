# HMASD native Codex workflow v3

HMASD 直接信任 Codex 可见的 top-level task/session plane：task 身份、历史、上下文
隔离、create/send/read/wait 与同 task 继续都由 Codex 原生提供。项目只机械约束方向、
角色、路径、Effect、结果与证据，不重建 task registry、inbox、receipt 或隐藏 manager。

## 权威索引

- 用户确认的控制目标与真实验收：
  `docs/project/WORKFLOW_GOALS_AND_ACCEPTANCE.md`。
- 唯一正常跨 session 协议、状态转换与恢复规则：
  `docs/project/WORKFLOW_PROTOCOL.md`。
- 规划与 ticket：`.scratch/`、`docs/agents/issue-tracker.md`；项目与领域背景：
  `CONTEXT.md`、`docs/adr/`、`docs/agents/domain.md`。
- `.codex/prompts/` 和 task skills 只是角色入口；不得复制 authority、topology、
  scheduler 或权限 gate。与上述两份权威文档冲突的 prompt、skill、fixture、历史说明
  和实现都是迁移对象。

v3 的 session skill 层仅为 `hmasd-root-task`、
`hmasd-workflow-clerk-task`、`hmasd-portfolio-task`、`hmasd-em-task`、
`hmasd-cm-task`、`hmasd-slice-interface` 与 `hmasd-operations-manual`。

## Task plane 与角色切面

长期同级协作必须使用真实可见的 top-level task；subagent 只用于一个 manager 内部的
bounded direct leaf。leaf 不再 delegate、不持有其他 top-level task ID，只 final
return 给 spawning parent。任何 heartbeat 都回到当前责任 task。

- **Root**：永久用户入口；处理用户材料决定、shared-core、task identity conflict、
  无法机械解释的协议矛盾和最终 cross-direction Git integration。它不做普通方向转递，
  不代 EM/CM 完成方向工作。
- **Workflow-Clerk**：唯一长期协调 task；只做 native topology、v3 transport、
  on-demand task creation/reuse、bounded final drain 和 recovery。它不做方向科研、
  工程或 Portfolio 判断，也不维护第二状态机。
- **Portfolio**：长期 global top-level task；负责跨方向 considered set、lifecycle、
  priority、capacity 与新方向决定。它把决定 RETURN 给 Clerk，不创建或直接联系
  Root/EM/CM。
- **EM/<direction-id>/g<generation>**：一个方向的长期科研 task。Research Scout、
  Research Innovator、Research Principles Analyst、Research Critic 与 Agentify
  external transport 是其 direct leaves。结论性或 direction-changing 对象保持
  constructive case、constructive Pro review、修订后独立 adversarial Pro review。
- **CM/<direction-id>/g<generation>**：一个方向的长期工程 task。Implementer、
  Reviewer、Verifier 与 Experiment Operator 是其 direct leaves。非机械实现交
  Implementer；高影响 production/protocol/scientific/numerical/RNG/checkpoint
  代码接受前交 independent Reviewer。
- **Experiment Operator**：CM 的单层 child，只持有一个冻结的 result-bearing
  command；terminal result 固定回 CM，绝不直达 Clerk。

角色是责任边界，不是用户权限 gate。用户可直接进入任何可见 task；被直接控制的
participant 必须按 v3 `CONTROL_NOTICE` 让 Clerk 看见 transport 变化。

## Durable writers

- Portfolio：`docs/research/portfolio/PORTFOLIO.md`、registry 与 lifecycle。
- 对应 EM：`docs/research/candidates/<id>/DIRECTION.md`、research state、external
  review index 与科研结果。
- 对应 CM：engineering state、direction-owned source/test、static dossier 与
  `hmasd_run.py prepare` 生成的 manifest/preflight。
- 唯一 Operator：payload/result、stdout/stderr、checkpoint 与 terminal observation。
- Root：明确授权的 shared-core 和最终 cross-direction integration。

对应 EM/CM 也是各自 `instrument evidence sidecar` 的 durable writer。leaf 只返回
typed observation；EM/CM 校验并写 sidecar，raw instrument output 只留在对应 direction
的 `temp/` 路径。工具成功不是 scientific acceptance、routing 或 lifecycle authority。

writer 表示领域责任，不是额外批准层。material decision 写入所属 durable authority；
conversation 和 Dashboard 只保留 provenance。

## Hard boundaries

1. 破坏性操作前解析 exact target；不得越过用户授权范围，不得暴露 secret。
2. 外部 provider 的一个 operation 至多 send 一次；结果未知时只 observe，不盲目重发。
3. 一个 Operator 从 launch 到 terminal observation 只运行一个 exact command。
4. 不安全内存计划必须缩小、batch 或 shard。prepare 的 memory refusal 在 manifest
   前发生时 reserved output root 必须不存在；旧 partial root 仅由 run CLI 对精确
   安全形状机械回收。
5. 预计超过 7200 秒的本地 result command 必须经过一次性能合理性审阅，并取得绑定
   exact command 的用户批准。authority 已覆盖、memory-safe、无新 external/shared-core
   语义且不超过 7200 秒的 PREPARED command 不增加批准 gate。
6. 科学、数值、RNG、checkpoint、bit identity 和 external Effect 语义不得静默改变。
7. failure 必须限定为 project、direction、feature 或 effect，并按 v3 fingerprint
   计数；同一 fingerprint 最多三次。该上限不放宽外部 at-most-once。
8. 用户始终拥有最高权限。危险行为应说明并记录；工具或校验不能变成新的批准层。
9. Dashboard 只允许 `127.0.0.1` 上的只读 provenance projection。它不得写 authority、
   创建 task、路由、恢复或刷新伪造的 freshness；失败或陈旧不改变 liveness。
10. `hmasd_codex_tasks.py run-chain/execute-plan`、Work Packet planner、本地 task
    cache、return witness、raw rollout parser 与隐藏 app-server manager 均已退出正常
    路径和验收。删除前先核查真实依赖并保留在途修改。

## Shared workspace 与 Git

`C:/Projects/HMASD` 是 shared checkout 且永久保持 `main`。Root、Clerk、Portfolio、
EM、CM 不得在这里运行 `git switch` 或 `git checkout`。只有 assignment 明确给出
separate worktree 时才允许方向分支；否则 owner 在 shared `main` 上只处理 exact
`owned_paths`，不得 stage 或回退其他 session 的修改。

方向 source 位于 `experiments/candidates/`，tests 位于
`tests/experiments/candidates/`，durable science 位于
`docs/research/candidates/<direction-id>/`，运行产物仅位于
`temp/directions/<direction-id>/{exp,test}/`。正常 top-level owner 在 RETURN 前完成
自身 exact paths 的 Git 收尾并报告 branch、完整 SHA、remote/ref 与 push 结果；leaf
和 Root 不代做普通方向收尾。共享 index 不允许并发 mutation；不能保证时使用显式
separate worktree。

共享 C++ backend、神经网络基座或跨方向核心修改前，必须向用户说明 exact paths、
目标、非目标与语义影响并取得确认。使用 native Windows Git/Python；项目 Python
优先 `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`；tracked paths 使用
repository-relative POSIX syntax，durable text 遵循 `.gitattributes` 的 LF。

保留用户与其他 session 的修改；reviews/tests 是风险相称的 evidence，不是 authority。
session 协调不得进入实验运行器或 Git 工具。
