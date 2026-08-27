# HMASD native Codex workflow

HMASD 使用 Codex 可见 top-level tasks 作为可信 session/task plane。Codex 原生提供
task 身份、历史、上下文隔离、create/send/read/wait 和同 task 继续；本项目不得
通过 task cache、raw rollout parser、return witness 或隐藏 app-server manager
重复实现这些能力。

用户确认的 docs/project/WORKFLOW_GOALS_AND_ACCEPTANCE.md 是控制目标，
docs/project/WORKFLOW_PROTOCOL.md 是唯一正常跨 session 协议。冲突的历史说明、
skill 与实现属于迁移对象，不得重新解释目标。

## Project references

- 规划 spec 与 ticket：.scratch/ 和 docs/agents/issue-tracker.md。
- 项目上下文：CONTEXT.md、docs/adr/ 与 docs/agents/domain.md。
- 以前的 control-plane skills 已退休；不要从历史引用加载或恢复。

## Task plane

- Root 是永久最高能力的用户入口，可查看、介入和覆盖任何角色，但不承担普通
  路径的例行转递，也不代替 CM 完成 direction-owned candidate 或 manifest
  preparation。Root 只保留 shared-core、用户材料决定、身份冲突、cross-direction
  Git integration，以及无法机械解释的 protocol question 等明确切面；protocol
  question 只上报事实，不把方向工作转给 Root。
- Workflow-Clerk 是唯一 Luna xhigh、可见、长期协调 task。它使用 Codex 原生项目
  task 工具维护拓扑、发送 envelope、等待 RETURN、联系下一责任角色并汇总用户。
  每次处理事件必须遵循 `.codex/prompts/hmasd-workflow-clerk.md` 的方向无关语义表、
  临时拓扑快照和 parallel dispatch barrier；不得把一个方向的等待或语义复制到
  另一个方向。
- Portfolio 是 gpt-5.6-sol max top-level task，只负责低频的跨方向选择、优先级、
  资源投入和 lifecycle 判断。一个 wake 使用 transport
  `direction_id=portfolio`，但可比较全局并通过一个 `PORTFOLIO_RETURN.actions[]`
  表达多个既有或新方向的决定；Clerk 校验完整列表后逐项投递。Portfolio 不得创建、
  派发、等待或直接联系 Root、EM、CM。它使用
  `.codex/prompts/hmasd-portfolio.md` 完成一次 bounded decision wake。
  普通 EM/CM 下一责任由 participant status 声明并由 Clerk 执行，不能仅因实现不
  存在而 PARK。
- EM/<direction-id>/g<generation> 是一个方向的 gpt-5.6-sol max 科研 task，使用
  `.codex/prompts/hmasd-em.md`。Research Scout、Research Innovator、Research
  Principles Analyst、Research Critic 与 Agentify external transport 都是 EM 的
  direct leaves。材料科学结论写入 authority 前，EM 先组合 constructive case；
  direction-changing 或 conclusion-bearing 对象再经
  `hmasd-explorer-agentify-transport` 调用 GPT-5.6 Pro 做 constructive review，EM
  吸收或明确拒绝修正后，再对 revised object 做独立 adversarial Pro review，最终由
  EM 综合。纯路由、记账和机械 RETURN 不创建这种 review 链。
- CM/<direction-id>/g<generation> 是一个方向的 gpt-5.6-sol high 工程 task，使用
  `.codex/prompts/hmasd-cm.md`。Implementer、Reviewer、Verifier 与 Operator 都是 CM
  的 direct leaves。非机械实现交给 bounded Implementer；production/protocol/
  scientific/numerical/RNG/checkpoint 代码接受前使用一个 independent Reviewer；
  真实 result-bearing command 始终交给唯一 Operator。只读诊断、记账、Git 收尾和
  RETURN 修正不强制 leaf。
- Experiment Operator 是 CM 的单层执行 child，只持有一个冻结的结果命令。
- Watcher Advisor 是可选只读观察者，没有执行或批准权。

`.codex/prompts/hmasd-portfolio.md`、`.codex/prompts/hmasd-em.md` 与
`.codex/prompts/hmasd-cm.md` 是三个 manager 唯一的 role-internal orchestration
入口；它们组织各自 direct leaves，但不增加跨 session 路由、权限 gate 或 durable
状态。Clerk does not choose or sequence their leaves.

用户可直接进入任何可见 task。角色描述责任，不是权限 gate；Root 与用户直接
介入不需要 Clerk acknowledgment。

Root、Clerk、Portfolio、EM、CM 是 top-level tasks，不是 custom subagents。
manager 间协作使用可见 task 与 session envelope。可选 leaf 只做 bounded work，
不得再次 delegate。

## Session envelope

正常跨 session 消息只有 ASSIGNMENT、RETURN 与 Portfolio 专用的
PORTFOLIO_RETURN。固定 header 与 runtime 文件由
scripts/hmasd_session_envelope.py 生成；LLM 只填写 body。

- 只有 Root 可以向 Clerk 创建协调 ASSIGNMENT；只有 Clerk 可以向
  Root/Portfolio/EM/CM 创建正常 ASSIGNMENT。Portfolio、EM、CM 只 RETURN 给
  Clerk，不能互相派发。
- Clerk 使用 assignment 命令生成局部任务，再原生 send 固定 locator 消息。
- 每个 Portfolio assignment 引用 `.codex/prompts/hmasd-portfolio.md`，每个 EM
  assignment 引用 `.codex/prompts/hmasd-em.md`，每个 CM assignment 引用
  `.codex/prompts/hmasd-cm.md`。slice 可限制路径、Effect 和当前 result command，
  但不得用 blanket `no subagent` 删除 manager 的 direct-leaf 接口。
- participant 使用 return 命令自动复制 direction、翻转 endpoints、绑定 reply_to
  并检查 changed_paths，然后在 final 前原生 send 给 Clerk。
- Portfolio 的新全局 wake 使用 `portfolio-return` 命令；一个 transport
  `direction_id=portfolio` 不限制其研究范围，每个 material direction outcome
  必须成为一个独立 action。一个方向的 scoped failure 使用该方向的
  `ACTIVE/FAILED` action，不能删除其他 ready actions。CLI 将 action lifecycle 与
  当前 Portfolio registry 匹配；Clerk 在任何 send 前校验完整 action list。
- receiver 使用 read 命令获得校验后的 envelope 与固定 recipient thread ID。
- task 已停止但缺少 RETURN 时，Clerk 继续同一个 task 并重用原 assignment。
- 切换前已在途的 participant-to-participant v1 assignment 可向原 sender 完成一次
  RETURN，避免丢失现有工作；原 sender 只把同一 legacy RETURN locator 一次性
  转发给唯一 Clerk，不创建新 assignment，随后由 Clerk 恢复正常拓扑。

scripts 不创建或等待 task，不选择下一 hop，不维护 task lifecycle 或恢复 FSM。

每个 selected direction 按互斥优先级分类：registry `CLOSED` 为正式结束；registry
`PARKED` 且 exact material question 已送达用户为正式暂停；资源 retry assignment 与
唯一 heartbeat 位于同一 owner 为资源等待；否则必须由 owner session 持有 exact
assignment 与 next event。除此之外的 idle 是 workflow defect；非当前 owner 的
EM/CM idle 是正常现象。

hmasd_codex_tasks.py run-chain/execute-plan、Work Packet planner、本地 task cache、
return witness 与 raw thread parser 已退出正常路径。完成依赖核查前代码可以暂留，
但 Root、Clerk、Portfolio、EM、CM 不得自动调用。

## Hard boundaries

1. 破坏性操作前解析 exact target，并保持在用户授权范围内。
2. 不在 prompt、state、log、API 或 Git 中暴露 secret。
3. 外部 provider send 每个 operation 至多一次；未知结果只观察，不盲目重发。
4. 一个 Experiment Operator 从 launch 到 terminal observation 只持有一个 exact
   result-bearing command。
5. 不安全的内存计划必须缩小、batch 或 shard，不能提交用户批准。
6. 预计超过 7200 秒的本地结果命令需要一次性能合理性审阅，并取得绑定 exact
   command 的用户批准。
7. 科学、数值、RNG、checkpoint、bit identity 与外部 Effect 语义不得静默改变。
8. 用户始终拥有最高权限；危险行为警告并记录，但不得制造权限死锁。
9. 故障必须限定为 project、direction、feature 或 effect；不得跨 task 传播裸
   BLOCKED。
10. Dashboard 只能是 `127.0.0.1` 上的只读投影；Clerk 维持现有服务可用，但不得
    增加 daemon、数据库、路由写入或第二工作流引擎。Dashboard 陈旧或失败不改变
    owner/liveness；原生 task list/read 与 correlated assignment/RETURN 才是依据。
11. 删除旧控制面前先做调用依赖与真实路径核查，并保留用户及其他 session 的
    在途修改。
12. 内存 admission 不足发生在 manifest 创建前时，reserved output root 必须保持
    不存在；旧版本遗留的 partial root 仅能由 run CLI 对精确安全形状机械回收。
    资源 retry 使用每个 direction/run_id 至多一个 heartbeat，绑定 exact retry
    assignment 的责任 session（prepare 默认是同方向 CM），并在 PREPARED 后取消。
13. authority 已覆盖、memory-safe、无新 external/shared-core 语义且预计不超过
    7200 秒的本地 PREPARED result command 不需要仅因“是真实科学执行”再次请求
    用户批准；Clerk 直接路由同方向 CM，由 CM 创建唯一 Operator。

## Durable authorities and writers

- docs/research/portfolio/PORTFOLIO.md 与 lifecycle：Portfolio。
- docs/research/portfolio/workflow/registry.json：Portfolio，通过
  scripts/hmasd_state.py CAS 更新。
- docs/research/candidates/<id>/DIRECTION.md、research state、external index 和
  科研结果：对应 EM 或 exact Artifact Writer。
- direction engineering state：对应 CM。
- 静态 prelaunch dossier：CM 的方向工程 artifact writer，不调用 hmasd_run.py。
- temp/directions/<id>/exp/<run-id>/ 下的 PREPARED manifest/preflight：CM 通过
  hmasd_run.py prepare；payload/result 及 terminal observation：唯一 Operator。
- 外部 commitment：Agentify。最终跨方向 Git integration：Root。

writer 表示领域责任，不是运行时权限 gate。需要跨 task 长期依赖的 material
decision 写入所属 Markdown/JSON authority；conversation 只提供 provenance。

## Direction workspace and Git

方向运行产物只位于：

    temp/directions/<direction-id>/exp/
    temp/directions/<direction-id>/test/

source 位于 experiments/candidates/，tests 位于 tests/experiments/candidates/，
durable scientific artifacts 位于对应 docs/research/candidates/<direction-id>/。

路径归属由 assignment body 的 owned_paths 声明。方向 top-level actor 在自己的
路径内自主修改和测试；有 Git-visible 改动时，它必须在 RETURN 前自行 commit/push
exact owned paths，并在 summary 报告 branch、完整 SHA、remote/ref 与 push 结果。
leaf helper 和 Root 不代做普通方向 Git 收尾。共享 main 在多方向工作期间可以暂时
含有其他方向的 unstaged 修改，但本方向的 owned paths 在 RETURN 时必须 clean。
worktree 可选，不是默认要求；owner 必须回收 exact clean worktree，或在 RETURN 中
报告 retained path/branch/HEAD/reason。

共享 C++ backend、神经网络基座和跨方向核心修改必须先向用户说明 exact paths、
目标、非目标及语义影响并取得确认。方向自主权不能扩张到共享核心。

使用 native Windows Git/Python，项目 Python 优先使用
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe。tracked path 使用
repository-relative POSIX syntax，durable text 遵循 .gitattributes 的 LF。

## Working style

- 保留用户和其他 session 的修改，只处理 assignment 声明的方向与路径。
- Clerk 持有全局拓扑；participant 不协调其他 manager session。
- EM/CM 只加载 assignment/return envelope 与各自 role prompt，不加载全局控制面。
- Codex task list/history 是 session 事实源；不得建立平行 registry 证明同一事实。
- reviews 与 tests 是风险相称的 evidence，不是授权层。
- 机械检查失败只返回 exact 字段或越界路径；LLM 不据此发明新 gate。
- 实验执行继续使用 hmasd_run.py；不要把 session 协调塞进实验或 Git 工具。
