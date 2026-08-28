# HMASD native Codex workflow

HMASD 直接信任 Codex Desktop 可见的 task/session plane。项目只约束角色、路径、Effect、
milestone、科学证据和实验结果，不重建身份认证、消息账本、task registry、receipt、retry
状态机或隐藏 scheduler。

## Authority

- 唯一控制 authority：`docs/project/WORKFLOW_PROTOCOL.md`。
- 方向科学 authority：`docs/research/candidates/<direction>/DIRECTION.md` 及其引用材料。
- 当前组合 authority：`docs/research/portfolio/PORTFOLIO.md`。
- 规划与 ticket：`.scratch/`、`docs/agents/issue-tracker.md`；背景：`CONTEXT.md`、
  `docs/adr/`、`docs/agents/domain.md`。
- Session skills 仅为 `hmasd-root-task`、`hmasd-portfolio-task`、
  `hmasd-em-task`、`hmasd-cm-task`。

与唯一协议冲突的历史文档、fixture、prompt、旧 task 消息或脚本均不是当前输入。旧 task
已经退役；需要方向工作时创建当前协议的新 EM/CM task。

## Hard boundaries

1. Root 是用户与 shared-core 入口；Portfolio 只作跨方向 lifecycle/priority/capacity 判断；
   EM 直接负责科研；CM 直接负责工程。正常链路由 requester 使用 Codex 原生 task ID 直接
   投递，callee 把结果返回同一个 requester。
2. Long-lived participant 使用 top-level task。Subagent 只是一个 manager 内的 bounded direct
   leaf，只 final return 给 spawning parent，不再 delegate，也不联系其他 top-level task。
3. Manager 应把与主判断弱耦合的下载、整理、机械检查和杂务交给通用 Luna-xhigh leaf；
   专门工作仍分别使用 CM Scout、Research Scout、Reviewer、Verifier、Operator 或 external
   transport。
4. EM/CM 只在 material milestone 跨越时覆盖各自 current state；state 不是日志数据库。
5. 外部 provider 的一个授权 operation 至多 send 一次；commitment 未知时只观察，不重发。
6. Experiment Operator 从 launch 到 terminal observation 只运行一个 exact command。
7. 不安全内存计划必须缩小、batch 或 shard。预计超过 7200 秒的本地 result command 需要
   一次性能合理性审阅和绑定 exact command 的用户批准。
8. 科学、数值、RNG、checkpoint、bit identity 和 external Effect 语义不得静默改变。
9. 用户始终拥有最高权限。工具与验证是 evidence，不是新的批准层。
10. Native task 能力不可用时显式停止；不得启用中转协调 task、本地 task plane、inbox、
    history parser、registry、receipt 或 scheduler 替代品。

## Workspace and Git

`C:/Projects/HMASD` 是 shared checkout 且保持 `main`。除非 assignment 明确给出 separate
worktree，不运行 `git switch` 或 `git checkout`。Owner 只改 exact owned paths，保留其他
task 与用户的修改；shared index mutation 串行进行。

方向 source 在 `experiments/candidates/`，tests 在 `tests/experiments/candidates/`，durable
science 在 `docs/research/candidates/<direction>/`，运行产物只在
`temp/directions/<direction>/{exp,test}/`。跨 top-level role handoff 且 refs 包含 Git-visible
内容时必须 commit；push 只在用户要求远端同步、跨 worktree 集成或正式交付时强制。

共享 C++ backend、神经网络基座或跨方向核心修改前，必须向用户说明 exact paths、目标、
非目标与语义影响并取得确认。使用 native Windows Git/Python；项目 Python 优先
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`；tracked paths 使用 repository-relative
POSIX syntax，durable text 遵循 `.gitattributes` 的 LF。
