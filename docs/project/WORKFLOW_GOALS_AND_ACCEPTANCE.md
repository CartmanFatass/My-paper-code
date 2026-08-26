# HMASD 工作流设计目标与验收标准

状态：用户确认的工作流重设计目标与验收基准  
Decision owner: User  
确认日期：2026-08-26

本文档定义工作流实现必须达到的目标和可观察验收结果。实现细节、历史协议、
skill、测试夹具或运行记录不得改变这些目标。若当前实现与本文档冲突，冲突表示
尚未完成的迁移工作，不得通过重解释本文档来消除。

## 已撤销的错误标准

此前提出的“删除 Work Packet、reconcile、native adapter、Clerk”验收项已经
作废。它会摧毁需要保留的自动化内核，不得作为简化、清理或重构的依据。

## 当前确认的设计目标

- Clerk 持有全局工作面：拓扑、任务创建/复用、路由、消息、等待、恢复和结果
  回收。
- Root 保持最高权限和用户入口，可直接介入任何角色，但不常驻普通自动流程。
- Portfolio、EM、CM、Operator 只接收自己的工作切面，完成局部工作并返回；
  不协调其他 session。
- 机械动作由 scripts 和统一协议完成，LLM 不自行解释状态机、不发明 gate。
- 研究→代码→实验→结果能够无人值守连续运行；故障按
  project/direction/feature/Effect 精确限定，有限修复后才请求用户。
- 多方向并行时路径和 Effect 正交；方向可在自有目录直接 Git，worktree 不是
  默认要求。
- 用户始终拥有全部权限；危险操作警告并记录，但不得形成权限死锁。
- 项目同时对人和 LLM 可读，使用分层文档、稳定目录和明确接口。
- 共享 C++ backend、神经网络基座等核心修改需要用户确认；方向实验代码自主
  修改。
- MARL 实验遵循真实科学与资源约束，不因 toy case 追求无意义精度或逐路径
  穷举。
- 从开源项目吸收简单、程序优先、单一事实源的设计哲学，不复制组件，也不
  叠加第二控制面。
- skill 只是可选组件；项目 spec、角色拓扑和机械协议不得拆散塞进多个 skill。

## 当前验收标准

1. 一条真实无人链完整通过：用户/Root → Clerk → EM → 必要时 CM → Operator
   → Clerk → 用户；Root 不做例行调度。
2. 四个方向可同时运行，任务列表可见，路径/Effect 无交叉，没有重复 task、
   重复发送或重复 Operator。
3. 中断、容量不足和局部失败能以同一工作身份恢复；修复次数有界，且不会传播
   裸 `BLOCKED`。
4. Participant 只看到目标、输入 refs、owned paths、允许 Effects、完成条件和
   返回接口；看不到全局协调复杂度。
5. 用户可随时直接覆盖或介入；危险行为有警告和完整记录，但不会被控制面阻挡。
6. Root 工作目录保持干净 `main`；方向内 Git 自主，worktree 可选且能够回收。
7. scripts 是唯一机械事实源；不存在并行 registry、重复状态机、重复恢复层或
   由 skill 重述的协议。
8. 删除或修改控制面前必须先做调用依赖和同一端到端基线核查。
9. 全部协议测试、命令运行测试和真实 native 测试通过；不能用“局部
   CM→Operator 成功”冒充完整无人链成功。
10. skill 只有在无 skill 基线确实失败、且内容是可重复单一能力时才创建；否则
    保持不存在。

## 已确认的执行与测试 seam

Decision owner: User  
确认日期：2026-08-26

以下接口集合是完整边界。实现 ticket 不得临时新增 public seam；若证据证明边界
不足，必须先修改本节并重新 review。

| 能力 | 冻结的 seam | 边界 |
| --- | --- | --- |
| Work Packet 原子协议 | `hmasd_work_packet.py build/publish/reconcile/return-publish/return-read/compare` | scripts 内部机械内核；participant 不负责组合调用，`validate` 保持内部 utility |
| 单工作 transport | `hmasd_codex_tasks.py execute-plan` | 一个闭合 plan 和一个明确 `work_id`；不得选择下一 hop |
| 完整无人链 | `hmasd_codex_tasks.py run-chain` | 唯一 workflow-level acceptance seam |
| 结果命令 | 一个 `hmasd-experiment-operator` leaf 与既有 `hmasd_run.py` | 不增加 `REQUEST_OPERATOR` 或 top-level Operator manager |
| 方向 Git | `hmasd_direction_git.py commit-push/observe-push` | 无 worktree 默认、无 branch manager、无 Git ledger |
| 可视化/控制 | 现有 Codex task UI 与 `hmasd_codex_tasks.py list/read` | 无 dashboard controller |
| 共享核心 | 现有 `hmasd-shared-core-action-v1` fence 与 `shared-core-record` | 新 Git CLI 不解释或授予批准 |

### `execute-plan` 与 `run-chain`

- `execute-plan` 是保留的原子内核 seam。一次调用只执行一个明确 `work_id` 的
  闭合 plan，负责确定性的 task create/reuse、投递、等待、fresh observation 和
  typed return 验证。它不得替 planner 补字段或决定后续工作。
- `run-chain` 是完整无人工作流的唯一外部验收 seam。生产 CLI 接收一个起始
  `--work-id`、`--cwd`、可选重复 `--peer-work-id`、可选精确
  `--root-override-reason` 和默认值为 16 的 `--max-transitions`。它不接受由调用者
  提供的静态 observed-task snapshot；每个 hop 都重新读取现有 runtime task
  projection 和 native list/read，并将该 fresh snapshot 显式交给 planner。
- `--root-override-reason` 只绑定起始 `--work-id` 的一次已知 overlap/active-unknown
  决定，并在第一个 work transition 后清除。后续 work identity 遇到 overlap 时链
  必须停止并返回该 exact `work_id`；新的 override 只能由 Root/用户对该 identity
  另行发起，不能继承前一 reason。
- `run-chain` 只依据 machine-validated return、canonical draft 和
  `next_action.input_refs`，有界组合现有 build、publish、`reconcile --once` 和
  `execute-plan`。它返回内存中的有序 event trace、transition count 和精确 stop
  fact，不写新的 durable workflow state。
- terminal completion、Root/用户 material decision、typed conflict、UNKNOWN
  commitment、capacity pause、native observation failure 或 transition 上限都会
  停止该链。每个 `work_id` 的自动 same-identity recovery 总预算为三次，计数来自
  native history，统一覆盖 terminal-without-return、`RESUME_SAME_SLICE` 和同范围
  repair；passive observation 不增加计数。capacity pause 之后仍只允许用同一
  identity 和剩余预算恢复。预算耗尽时返回 `RECOVERY_EXHAUSTED`，携带 exact
  project/direction/feature/Effect scope、failure ref 和 evidence，供 Clerk 向用户
  提出一个 material question；模型或 session 不得在每个 hop 之间另建 retry loop。
- `run-chain` 不得引入 durable queue、第二 registry、daemon、数据库、新 workflow
  schema 或第二状态机。所有 durable facts 仍来自既有 authority、Work Packet、
  return witness、Effect observer、run manifest、Git facts 和 native task history。

### Experiment Operator

- CM 在自己的 bounded assignment 内使用 `hmasd_run.py prepare` 冻结 exact command、
  cwd、assignment identity 和 output root，然后创建恰好一个
  `hmasd-experiment-operator` leaf。
- run manifest 中的 run-owner identity 由 frozen `run_id` 唯一派生为
  `Operator-<run_id>`；custom agent/common result 的 `logical_identity` 保持
  `hmasd-experiment-operator`。native child 的唯一 lookup key 是 exact parent CM
  thread、`agentRole=hmasd-experiment-operator` 与 child startup/name/history 中冻结的
  `run_id`，随后绑定 observed child thread ID。CM 创建前必须 fresh list/read 该
  child/history：存在 exact key 就恢复同一 child；只有已证明不存在才创建；UNKNOWN
  creation 只观察，不得重建第二 child。
- 该 leaf 使用既有 `execute` 并持有 command 至 `reconcile` 得到 terminal fact；
  `cancel` 仅取消已证明属于该 run 的 live process group，`promote` 仅处理成功且
  group-quiescent 的结果。
- run manifest、stdout/stderr refs 和 CM typed return 是 Clerk 的证据。Operator 不
  成为新的 top-level manager，协议不增加 `REQUEST_OPERATOR`。
- deterministic `run-chain` 验收必须注入“child 已创建、CM 在 return 前中断”的
  情形，并证明恢复后仍只有一个 child identity、一个 run claim 和一次 `execute`。

### Direction Git 与 shared core

- `hmasd_direction_git.py commit-push` 从 exact Work Packet/work identity 读取
  `owned_paths`，只 stage/commit 调用者显式列出的 `--path`；不得捕获其他方向或
  用户的 staged/dirty path。方向 actor 可在共享 `main` 上直接运行，Root 不执行
  例行 Git；最终 quiescence 时 Root checkout 必须处于 clean `main`。
- 一个短时、带上限的 Git transaction lock 只覆盖 path validation、一次 commit 和
  一次 push，不覆盖实现、测试、科学工作或 task wait。固定目标为 `origin/main`；
  不创建 branch/worktree，不自动 merge、rebase 或解决 conflict。
- 每个方向 commit 必须包含 canonical `HMASD-Work-ID: <64hex work_id>` trailer；
  script 同时记录其本次锁内观察到的 base SHA。任何 commit 前先在当前可达历史中
  查找该 exact trailer：零个才允许创建；一个时必须验证其 base、exact changed
  paths 和 assignment 后复用 candidate SHA；多个或不匹配时返回 scoped conflict。
  因此进程即使在 commit 后、输出 candidate SHA 前崩溃，也不得把后续方向的 HEAD
  当作本 work 的 candidate，且不得生成 duplicate commit。
- push 前后都观察 remote ancestry。remote 等于 candidate 或为包含 candidate 的
  descendant 均为成功；remote divergence 在发送前停止。一次 push 结果未知时只
  允许 `observe-push` 做 fetch/ancestry comparison，绝不再次 push。
- Git UNKNOWN 使用既有 envelope 的 `failure_scope="feature"` 与
  `failure_ref="git_push"`。CM return 在既有 `cm` payload 中携带 base/candidate SHA，
  `integrated_sha` 在 unknown 时为 `null`；精确 remote observation 写入既有 summary
  与 evidence refs。不得增加顶层 `feature` 字段或使用 Root-owned `git` payload。
  v1 不增加 Git Effect kind、receipt、ledger 或 registry；`run-chain` 对该 UNKNOWN
  只停止/观察。
- shared-core path 在任何 Git mutation 前返回 exact shared-core action request；仍由
  现有 authority fence、Root 和用户决定。可选 worktree 只使用现有
  `hmasd_worktree.py`，新 Git CLI 不管理 worktree。

### Recovery、并发与 real-native 验收

- 不增加 recovery public CLI。恢复只组合 `run-chain`、`execute-plan`、
  `hmasd_run.py reconcile`、`hmasd_direction_git.py observe-push` 和现有 Effect
  observers。容量或失败只暂停 project/direction/feature/Effect 的精确范围；没有
  裸 `BLOCKED`。
- 四方向并发使用四个独立起始 Work Packet 和四次独立 `run-chain` 调用。Clerk
  根据一次明确 Portfolio 决定进行 bounded caller-side fan-out；不增加
  `run-many`、scheduler 或 test-only orchestrator。每条链独立停止，一条冲突不得
  停止其他链。
- task identity、lifecycle、`threadSource`、turn 和重复检测通过现有 Codex task UI
  与 `list/read` 观察；`run-chain` trace 是本次调用输出，不是 durable authority。
- 最终必须通过一条完整 real-native `run-chain` 和四条并发 real-native
  `run-chain`。证据必须包括 persisted `threadSource`、unique task IDs、恰好一个
  Operator/command、typed returns、scoped conflict、无 duplicate send 和 final clean
  `main`。每条链还必须标明实际调用它的 canonical Workflow-Clerk task/thread/turn，
  证明普通路径中没有 Root create/send/dispatch/Git action，并展示 Clerk 的 terminal
  report 已返回用户。由 Root、pytest 或独立 shell 直接调用得到的相同 transport
  facts 只能作为底层证据，不能冒充 Clerk-coordinated acceptance。fake transport 或
  局部 CM→Operator 证据不得替代。
- 工作流完成后四方向的 exact initial packets 来自 Portfolio authority。当前只有
  三个 `ACTIVE` 方向；第四个及 priority order 必须由 Portfolio 明确决定，不能从
  历史标签或 registry 顺序猜测。

### 非 seam 的 subagent 命名约定

- 自定义 subagent：`<最小别名>_<模型首字母><thinking缩写>_<task>`。
- native child：`native_<模型首字母><thinking缩写>_<task>`。
- thinking 缩写为 `l`、`m`、`h`、`x`、`mx`、`u`。

原子 transport/identity 测试使用 `execute-plan`；无人 multi-hop、bounded recovery、
四方向并发和 real-native 验收使用 `run-chain`。单独通过前者不得宣称工作流完成。

## 当前完成状态

真实全链验收仍未通过，因此不得声称工作流已经完成。局部协议测试、fake
transport、单个 native adapter probe 或 scoped CM→Operator 成功都不能替代
上述完整验收。
