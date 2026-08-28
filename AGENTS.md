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

## Global field semantics

以下字段属于不同 namespace，不能互相推断。`Outcome:` 只表示当前 `[WORK]` 的存活/完成事实；
科学正负、实现成败、provider 状态和 Portfolio lifecycle 都由各自 owner 字段表达。

| Owner | Fixed fields and exhaustive values |
| --- | --- |
| Any top-level task | `Outcome: DONE | WAITING | FAILED | CANCELLED` |
| Root | `Root status: IN_PROGRESS | CHANGED | UNCHANGED | BLOCKED`; `Integration status: IN_PROGRESS | INTEGRATED | NOT_INTEGRATED | NOT_APPLICABLE` |
| Portfolio | `Portfolio action: NONE | ACTIVATE | CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF`; `Capacity action: KEEP | SET <n>` |
| EM | `Scientific status: IN_PROGRESS | SYNTHESIZED | NO_MATERIAL_INSIGHT | NOT_REACHED`; `Decision impact: <text or NONE>`; `Recommendation: NONE | CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF`; `Pro Innovator: <transport state>`; `Pro Convergence: <transport state>` |
| CM | `Engineering status: IN_PROGRESS | IMPLEMENTED | UNCHANGED | BLOCKED | NOT_REACHED`; `Observation status: IN_PROGRESS | OBSERVED | NOT_OBSERVED | NOT_REQUIRED`; `Verification status: IN_PROGRESS | SATISFIED | UNSATISFIED | NOT_RUN`; `Commit: <sha or NONE>` |

Leaf 只返回自己的 observation namespace，不返回 top-level `[RESULT]`：

| Leaf | Own final field |
| --- | --- |
| General leaf | `Chore status: COMPLETE | PARTIAL | UNAVAILABLE` |
| CM Scout | `Surface status: MAPPED | PARTIAL | UNAVAILABLE` |
| Reviewer | `Review status: FINDINGS | NO_FINDINGS | INCOMPLETE` |
| Verifier | `Verification observation: OBSERVED | NOT_OBSERVED | UNAVAILABLE` |
| Experiment Operator | `Run observation: TERMINAL | LAUNCH_FAILED | OBSERVATION_LOST` |
| Research Scout | `Evidence status: FOUND | CONFLICTED | NOT_FOUND | UNAVAILABLE` |
| Research Critic | `Critique status: OBJECTIONS | NO_MATERIAL_OBJECTION | INCOMPLETE` |
| Engineering transport | `Engineering transport state: ZERO_SEND_FAILED | COMMITMENT_UNKNOWN | SENT_WAITING | COMPLETE | SENT_UNREADABLE` |
| Pro transport | `Pro transport state: ZERO_SEND_FAILED | COMMITMENT_UNKNOWN | SENT_WAITING | COMPLETE | SENT_UNREADABLE` |

Pro transport state 只允许：`PENDING`（尚未调用）、`ZERO_SEND_FAILED`（明确 provider 未收到
请求、未创建 operation，且本地恢复已用尽）、`COMMITMENT_UNKNOWN`（无法证明是否发送）、
`SENT_WAITING`（已发送，等待自然完成）、
`COMPLETE`（完整回答已归档）、`SENT_UNREADABLE`（已发送但回答暂不可归档）、`WAIVED`
（用户豁免 exact operation）。transport failure 不得推导 Portfolio action、Scientific status、
Recommendation 或 lifecycle。CANCELLED 只能来自 `[CONTROL] Action: CANCEL`；负科学结果、
实现失败、zero-send 或 provider 不可读都不能自行产生 CANCELLED。

Top-level task 创建时使用以下用户确认的目标配置，必须显式传给 Codex native task API：

| Role | Model | Thinking |
| --- | --- | --- |
| Portfolio | `gpt-5.6-sol` | `max` |
| EM | `gpt-5.6-sol` | `max` |
| CM | `gpt-5.6-sol` | `high` |
| Root | 用户当前选择 | 用户当前选择 |

Direct leaf 的 `spawn_agent.task_name` 使用 `<alias>_<model>_<effort>_<task>`，它只是短显示名，
不作为身份或路由字段。alias 固定为 `cs/rv/vf/op/et/pt/rs/rc/gl`；model 为 `l/t/s`；effort 为
`l/m/h/xh/mx/u`；task 只允许 `[a-z0-9_]+`。model/effort code 必须来自实际 selected profile，
同一 parent 内不得重名。例如
`rv_s_xh_plan`、`gl_l_xh_pdf`、`pt_l_m_pro`。该规则只用于 `spawn_agent.task_name`，不用于
top-level task title、native task ID 或 recipient。

| Alias | Custom subagent |
| --- | --- |
| `cs` | `hmasd-cm-scout` |
| `rv` | `hmasd-reviewer` |
| `vf` | `hmasd-verifier` |
| `op` | `hmasd-experiment-operator` |
| `et` | `hmasd-cpm-agentify-transport` |
| `pt` | `hmasd-explorer-agentify-transport` |
| `rs` | `hmasd-research-scout` |
| `rc` | `hmasd-research-critic` |
| `gl` | `hmasd-general-leaf` |

## Hard boundaries

1. Root 是用户与 shared-core 入口；Portfolio 只作跨方向 lifecycle/priority/capacity 判断；
   EM 直接负责科研；CM 直接负责工程。正常链路由 requester 使用 Codex 原生 task ID 直接
   投递，callee 把结果返回同一个 requester。
2. Long-lived participant 使用 top-level task。Subagent 只是一个 manager 内的 bounded direct
   leaf，只 final return 给 spawning parent，不再 delegate，也不联系其他 top-level task。
3. Manager 应把与主判断弱耦合的下载、整理、机械检查和杂务交给通用 Luna-xhigh leaf；
   专门工作仍分别使用 CM Scout、Research Scout、Reviewer、Verifier、Operator 或 external
   transport。Leaf 数由独立信息缺口决定，不设固定配额；多份同模型回答不是独立证据。
4. EM/CM 只在 material milestone 跨越时覆盖各自 current state；`snapshot_state` 只描述
   checkpoint，不是 assignment `Outcome:`，state 也不是日志数据库。
5. 外部 provider 的一个授权 operation 至多 send 一次；commitment 未知时只观察，不重发。
6. Experiment Operator 从 launch 到 terminal observation 只运行一个 exact command。
7. 不安全内存计划必须缩小、batch 或 shard。预计超过 7200 秒的本地 result command 需要
   一次性能合理性审阅和绑定 exact command 的用户批准。
8. 科学、数值、RNG、checkpoint、bit identity 和 external Effect 语义不得静默改变。
9. 用户始终拥有最高权限。工具与验证是 evidence，不是新的批准层。
10. Native task 能力不可用时显式停止；不得启用中转协调 task、本地 task plane、inbox、
    history parser、registry、receipt 或 scheduler 替代品。

## Workspace and Git

`C:/Projects/HMASD` 是 Root 的 primary checkout 且保持 `main`，不得在其中运行 `git switch`
或 `git checkout`。Portfolio、EM、CM 从已保存的 HMASD project 使用 Codex 原生
`environment: worktree` 创建 top-level task；需要特定基线时指定 exact existing branch。
Codex 持有 task worktree、branch 与 ready thread ID，不要求把方向目录另存为 Desktop project，
也不建立本地 project/worktree registry。REGISTERED、PARKED、CLOSED 不预建 task worktree。

同一 direction 同时只有一个 Git-visible writer phase，即使 EM 与 CM 位于不同 native task
worktree：EM 向 CM 交付前提交自身 owned refs并转为只读；CM branch 必须 fast-forward 到 exact
EM commit 后再工作。CM 只提交 exact owned paths并返回 known commit/diff，随后 EM branch 必须
fast-forward 到 exact CM commit，writer phase 才回到 EM。任一方向非 fast-forward 时，当前
participant 停止并向当前 `Return task` 返回 terminal blocker，不得越过 requester 直接联系
Root，也不得 cherry-pick、rebase 或重写历史。Root 只在既有链路关闭后收到独立 bounded repair
WORK 时处理。Leaf 不 commit/push、不创建 worktree。Owner 保留其他 task 与用户的修改；shared
Git mutation 串行进行。

方向 source 在 `experiments/candidates/`，tests 在 `tests/experiments/candidates/`，durable
science 在 `docs/research/candidates/<direction>/`，运行产物只在
`temp/directions/<direction>/{exp,test}/`。跨 top-level role handoff 且 refs 包含 Git-visible
内容时必须 commit；同一 saved HMASD repository 内的 native-worktree 交接不需要 push。Push
只在用户要求远端同步、跨主机交付或正式交付时强制。

新建 Portfolio/EM/CM task 时，initial prompt 本身就是完整 `[WORK]`；不得创建空 task 后重复
发送。旧 archived task 不复用。只有 ready thread ID 可作为 recipient；setup client ID 只等待。

共享 C++ backend、神经网络基座或跨方向核心修改前，必须向用户说明 exact paths、目标、
非目标与语义影响并取得确认。使用 native Windows Git/Python；项目 Python 优先
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`；tracked paths 使用 repository-relative
POSIX syntax，durable text 遵循 `.gitattributes` 的 LF。
