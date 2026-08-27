# HMASD 原生 Session 控制面 v2：目标与验收

状态：用户确认的工作流权威目标
Decision owner: User
确认日期：2026-08-27

本文定义 v2 必须达到的结果。`docs/project/WORKFLOW_PROTOCOL.md` 是实现这些结果的
唯一正常跨 session 协议。冲突的历史协议、prompt、skill、fixture 与实现属于迁移
对象，不能反向修改本目标。

## 1. 产品边界

Codex 的可见 top-level task/session 是可信任务平面。HMASD 直接使用其 task 身份、
历史、上下文隔离、create/send/read/wait 和同 task 继续能力，只补充 Codex 不知道的
方向、角色、局部目标、路径、Effect、结果与证据语义。

长期同级工作必须是 top-level task；subagent 只做一个 manager 内部的 bounded leaf。
项目不得用本地 task cache、raw rollout、SQLite、receipt、隐藏 app-server 或另一个
scheduler 重新证明或模拟 Codex 产品事实。native task tools 不可用时，控制面停止并
报告能力缺口，不得降级到这些历史替代物。

> 信任 native task plane；只机械验证项目语义。

## 2. 五维状态必须分离

| 维度 | 唯一事实源 | 含义 |
| --- | --- | --- |
| `lifecycle` | Portfolio registry | `REGISTERED / ACTIVE / PARKED / CLOSED` 的 durable 投资决定 |
| `owner_stage` | Clerk 的短期只读投影 | 当前由谁持有 next event；不是 registry 或权限 gate |
| `native_task_status` | Codex task list/read | task 当前产品状态；不能推导方向完成或 ownership |
| `research_phase / engineering_phase` | 对应方向 state | 科研与工程领域进度；不能充当 transport receipt |
| `delivery_state` | native task history | envelope 是否真实投递及其 correlation；文件存在或 mtime 不算 delivery |

这些维度不得互相覆盖。research `COMPLETE` 不等于方向 `CLOSED`；task `idle` 不等于
无 owner；Dashboard 显示的新 phase 不等于 Clerk 已收到 RETURN。

生命周期结果必须满足：

- `REGISTERED` 是已知候选，不是终态；未被投资时可以没有 manager task。
- `ACTIVE` 必须有一个可解释的 next event：现有 top-level owner、同 owner 的
  `WAIT_RESOURCE`，或正在同一 Clerk turn 内完成的 validated handoff。不能因缺代码、
  当前 slice 完成、task idle 或 future Operator 尚未创建而静默失去 owner。
- `PARKED` 必须有 durable material reason、明确 reactivation condition 和已送达的
  用户/外部等待端点；普通资源重试或缺失实现不得伪装成 PARKED。
- `CLOSED` 必须有 durable terminal reason 与 evidence，且没有 next objective、
  assignment、heartbeat 或活跃实验。关闭不是局部 participant 的决定。

## 3. 角色与 standing authority

- **Root** 是永久用户入口与最高控制点，只保留用户材料决定、shared-core、identity
  conflict、不可机械解释的 protocol question 和最终跨方向 Git integration。
- **Workflow-Clerk** 是唯一长期协调 task，只负责 native topology、v2 transport、
  on-demand task creation/reuse、recovery 与 final drain。它不重做 Portfolio、科研或
  工程判断。
- **Portfolio** 是长期 global top-level task，负责完整 considered cohort、跨方向
  priority/lifecycle/capacity 与新方向选择。它不创建或直接派发其他 manager。
- **EM/<direction>/gN** 与 **CM/<direction>/gN** 是按需创建、之后复用的长期可见
  top-level task。EM 持有一个方向的科研语义；CM 持有该方向的工程与执行语义。
- EM 的 direct leaves 是 Research Scout、Research Innovator、Research Principles
  Analyst、Research Critic 与 Agentify external transport。CM 的 direct leaves 是
  Implementer、Reviewer、Verifier 与 Experiment Operator。
- **Experiment Operator** 始终是 CM 的单层 child，只运行一个冻结命令并把 terminal
  result 返回 CM；CM 解释结果后才向 Clerk RETURN。

Clerk 在某角色首次成为 next owner 时创建真实可见 task，而不是 custom subagent 或
本地记录；以后继续同一 identity/generation。非当前 owner 的长期 EM/CM idle 正常。
同一方向同一角色同一 epoch 不得出现两个 standing manager。资源 heartbeat 固定返回
持有 retry responsibility 的 task，不得漂移到 Root 或 Clerk。

角色与工具不是批准层。用户可以直接进入任何可见 task；该 task 必须把 PAUSE、
RESUME、OVERRIDE、CANCEL 或 REANCHOR 作为 v2 control fact 传播，使其他 session 不会
静默继续旧 mandate。

## 4. v2 正常流

所有跨 session 工作只使用 v2 的 `ASSIGNMENT`、`RETURN`、`PORTFOLIO_RETURN` 和
`CONTROL_NOTICE`。native 消息是固定单行 header；canonical body 位于 header 绑定且
hash 校验的 gitignored locator。消息前后不得附加自然语言或第二行。

participant RETURN 没有局部 terminal status。exact status 只有
`REQUEST_EM / REQUEST_CM / REQUEST_PORTFOLIO / REQUEST_USER / WAIT_RESOURCE /
FAILED`。科研、工程或实验 interpretation 完成后必须明确下一责任；方向真正 PARKED
或 CLOSED 只能来自 Portfolio durable transition。

正常 hop 的结果是：

1. Clerk 从 native list/read 建立本 turn 的 topology snapshot，并创建或复用 next
   owner 的 standing task。
2. Clerk 原生发送一个 v2 ASSIGNMENT；接收者只在 direction/objective/owned paths/
   Effect 内工作。
3. participant 在结束当前 turn 前原生发送 correlated RETURN；文件生成但未 native
   send 不算交接。
4. Clerk 只按 typed status/transition 路由。多个正交方向 ready 时，在同一事件 turn
   发送全部 ready assignments；一个方向失败或等待不阻塞其他方向。
5. Clerk final 前执行 bounded drain，读取本 active turn 内新到达而尚未消费的 v2
   消息并完成 ready sends。随后到达的消息由责任 task/Clerk heartbeat 再次唤醒。
6. stopped task 缺 RETURN 时继续同一 task 并重用同一 assignment；不复制 manager，
   不重做已经有 durable evidence 的工作。

## 5. Portfolio 必须是全局研究与容量 hub

每次 Portfolio global wake 的 body 固定包含以下三个语义决策区块：

- `considered[]`：完整说明本次全局 cohort 中每个既有或 proposed direction 是否被
  选择、继续、延后、暂停或关闭，以及依据；
- `transitions[]`：每个 material lifecycle/next-owner 变化及其 reason、evidence、
  `next_role` 与 `next_objective`；
- `capacity`：本次决策前后预算、分配、保留量与 opportunity-cost 解释。

Clerk 校验完整 global result 后逐项执行 transport，不压缩、不重做比较，也不把
一个方向的 failure 删除其他 ready transitions。v1 的 direction-local action list
不再是正常路径。Portfolio/apply failure 仍用 PORTFOLIO_RETURN，并在完整三块之外携带
同一 typed `failure`；只有已 durable 持久化的 transition 才能出现在返回中。

新方向由 Portfolio 提出，并在任何 task creation/native send 前通过一个 CAS-bound
脚本原子 scaffold：direction ID、DIRECTION authority、research/engineering state、
external-review index 与 registry entry 要么全部形成并通过 postcondition，要么保持
原状且没有 partial direction。只有 scaffold 成功后才能发生 `REGISTERED -> ACTIVE`
并按需创建 EM。

## 6. Failure、resource wait 与控制版本

`FAILED` 必须携带 `scope, code, fingerprint, responsible_role, retryable, attempt,
max_attempts, summary`。同一 immutable fingerprint 从 attempt 1 开始，
`max_attempts` 不得超过 3；达到上限后不得靠改写 prose 或 fingerprint 继续重试。
外部 commitment 为 UNKNOWN 时仍只 observe，绝不因重试预算而 resend。

`WAIT_RESOURCE` 保持原 manager 为 owner，冻结 estimate、parameters、command、code
SHA 与 retry condition；同一 direction/run 只有一个 heartbeat，且 heartbeat 回到该
manager。资源恢复前不得创建 Operator。

每个 envelope 固定携带 `protocol_epoch` 与 `control_release`。同一 protocol epoch 内
的新 release 只能在 turn boundary 通过 `CONTROL_NOTICE REANCHOR` 更新 task 的 expected
release；这不改变 lifecycle。protocol epoch 改变时不得 re-anchor 或 fork 旧 manager，
必须创建新的 clean manager generation，并只迁移 durable authority/evidence。

## 7. Git、实验与 shared core

`C:/Projects/HMASD` 永久保持 shared `main`。manager 不得在这里 switch/checkout；只有
assignment 明确指定 separate worktree 时才使用方向 branch。方向 owner 只 stage/
commit/push exact owned paths，不能带入其他 session 的 dirty files；共享 index 的
mutation 必须串行，不能保证时使用明确 worktree。

有 Git-visible 修改的正常 top-level owner 在 RETURN 前完成自己的 Git 收尾并报告
branch、完整 SHA、remote/ref 与 push 结果；leaf 和 Root 不代做普通方向收尾。
shared C++ backend、神经网络基座或跨方向核心修改必须先向用户说明 exact paths、
目标、非目标与语义影响并取得确认。

CM 的 static dossier 不调用 run CLI；CM 的 runtime prepare 负责 manifest/preflight
和资源等待；唯一 Operator 才执行 payload/result command。memory-unsafe prepare 不
创建 reserved root。满足既有 authority/resource/Effect 边界且预计不超过 7200 秒的
本地 PREPARED command 不因“真实科学执行”再请求批准；超过 7200 秒的 exact command
需要性能审阅和用户批准。

## 8. Dashboard 与可观察性

Dashboard 只能是 `127.0.0.1` 的只读 projection。它必须逐字段显示 source/provenance、
protocol epoch、control release、native observation time 和 stale/unknown；重新加载页面
不能只改 `observed_at` 来伪造 freshness。它可以显示五维状态，但不能写 registry/state、
创建 task、发送消息、触发 recovery 或决定 owner。关闭 Dashboard 不改变工作流。

## 9. 可观察验收

1. 新 epoch 的 Clerk、Portfolio 与按需 EM/CM 都出现在 Codex 项目 task list；没有用
   fork 复制旧 conflicting mandate，也没有同 identity/generation 的重复 manager。
2. 每个 native handoff 是一行 exact v2 header，四类 kind 之外全部拒绝；body hash、
   correlation、identity、direction 和 owned-path containment 可机械验证。
3. 五维状态分别可追溯到自己的事实源；`native_task_status` 或 phase 的变化不会静默
   改写 lifecycle/delivery。
4. 每个 ACTIVE 方向在 final drain 后都有唯一 next event；缺实现进入 CM，研究缺口
   进入 EM，lifecycle/capacity 进入 Portfolio，用户材料问题进入 Root/user。
5. PARKED 与 CLOSED 均有 durable reason/evidence，并满足无错误 owner/heartbeat/
   experiment 的不变量；REGISTERED 不被误显示为 CLOSED。
6. participant 只产生六个 exact status；局部完成不会终止方向。Operator terminal
   result 回到 CM，CM 再提供下一责任。
7. 同一 failure fingerprint 的 attempt 不超过三次；到达上限后有显式 responsible
   role。外部 UNKNOWN 没有重复 send。
8. Portfolio 一次 global wake 同时提供完整 `considered[] / transitions[] / capacity`；
   多个 ready transition 在同一 Clerk turn 全部 native send。新方向 scaffold 的故障
   注入证明 all-or-nothing，且 partial direction 不可见；关闭释放的 capacity 要么选出
   replacement，要么留下非空且可审计的 unused-capacity reason。
9. Portfolio authority/registry 已写但 RETURN 尚未发送、participant final 缺 RETURN、
   Operator terminal、消息在另一个 active turn 中到达等静默点，都能在原 task 中恢复
   并完成 handoff，不重复 material work。
10. 用户直接 PAUSE/RESUME/OVERRIDE/CANCEL 可传播为 CONTROL_NOTICE；旧 assignment
    不会在控制变化后被静默重投。
11. 同 epoch release 更新经 REANCHOR 后才继续；epoch 改变会创建 clean generation，
    旧 session history 不被 fork 到新 session。
12. memory refusal 不留下 reserved root；heartbeat 位于 exact responsible manager；
    PREPARED 后取消 heartbeat，且此前没有 Operator。
13. 四个真实方向可并行完成 EM -> CM -> Operator -> CM -> Clerk/Portfolio 链；一个
    方向的 waiting/failure 不延迟其他方向，shared Git index 没有交叉污染。
14. Dashboard 关闭、陈旧或 projection 删除不改变任何 owner/recovery；每个显示值有
    provenance，无法证明时显示 UNKNOWN 而不是猜测 transport gap。
15. 真实验收使用 native visible tasks、真实方向与原生 task history。synthetic
    transport、`run-chain`、hidden app-server、raw rollout 或 task cache 不得代替。

## 10. v2 epoch 迁移与退休路径

v2 控制面形成一个新的 protocol epoch。先把 authority、scripts、prompts、skills 与
tests 集成为一个 committed `control_release`，停止创建新的 v1 工作；对既有外部
commitment/Operator 只观察到安全边界。随后创建 clean Clerk 与 Portfolio，不 fork
旧 task；EM/CM 在下一次成为 owner 时创建新 generation，只从 durable authority 和
evidence rehydrate。新 epoch 可见且无 outstanding old Effect 后，再归档旧 task。

v1 locator、participant-to-participant forwarding、`DONE`、Portfolio `actions[]`、
Work Packet planner、`hmasd_codex_tasks.py run-chain/execute-plan`、本地 task cache、
return witness、raw rollout parser 和隐藏 app-server manager 不再是正常协议或验收
seam。代码可在完成调用依赖核查前暂留，但任何 v2 top-level task 都不得加载或调用。
