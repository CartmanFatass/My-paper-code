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
  路径的例行转递。
- Workflow-Clerk 是唯一 Luna xhigh、可见、长期协调 task。它使用 Codex 原生项目
  task 工具维护拓扑、发送 envelope、等待 RETURN、联系下一责任角色并汇总用户。
- Portfolio 是 gpt-5.6-sol max top-level task，负责方向选择、优先级、投资判断和
  下一责任角色。科学定义缺失时路由 EM；科学目标已接受但实现/test/CLI 缺失时
  必须路由 CM，不能仅因实现不存在而 PARK。
- EM/<direction-id>/g<generation> 是一个方向的 gpt-5.6-sol max 科研 task。
- CM/<direction-id>/g<generation> 是一个方向的 gpt-5.6-sol high 工程 task。
- Experiment Operator 是 CM 的单层执行 child，只持有一个冻结的结果命令。
- Watcher Advisor 是可选只读观察者，没有执行或批准权。

用户可直接进入任何可见 task。角色描述责任，不是权限 gate；Root 与用户直接
介入不需要 Clerk acknowledgment。

Root、Clerk、Portfolio、EM、CM 是 top-level tasks，不是 custom subagents。
manager 间协作使用可见 task 与 session envelope。可选 leaf 只做 bounded work，
不得再次 delegate。

## Session envelope

正常跨 session 消息只有 ASSIGNMENT 与 RETURN。固定 header 与 runtime 文件由
scripts/hmasd_session_envelope.py 生成；LLM 只填写 body。

- Clerk 使用 assignment 命令生成局部任务，再原生 send 固定 locator 消息。
- participant 使用 return 命令自动复制 direction、翻转 endpoints、绑定 reply_to
  并检查 changed_paths，然后在 final 前原生 send 给 Clerk。
- receiver 使用 read 命令获得校验后的 envelope 与固定 recipient thread ID。
- task 已停止但缺少 RETURN 时，Clerk 继续同一个 task 并重用原 assignment。

scripts 不创建或等待 task，不选择下一 hop，不维护 task lifecycle 或恢复 FSM。

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
10. Dashboard 只能是只读投影；不得增加 daemon、数据库或第二工作流引擎。
11. 删除旧控制面前先做调用依赖与真实路径核查，并保留用户及其他 session 的
    在途修改。

## Durable authorities and writers

- docs/research/portfolio/PORTFOLIO.md 与 lifecycle：Portfolio。
- docs/research/portfolio/workflow/registry.json：Portfolio，通过
  scripts/hmasd_state.py CAS 更新。
- docs/research/candidates/<id>/DIRECTION.md、research state、external index 和
  科研结果：对应 EM 或 exact Artifact Writer。
- direction engineering state：对应 CM。
- temp/directions/<id>/exp/<run-id>/：对应 Operator，通过 hmasd_run.py。
- 外部 commitment：Agentify。最终跨方向 Git integration：Root。

writer 表示领域责任，不是运行时权限 gate。需要跨 task 长期依赖的 material
decision 写入所属 Markdown/JSON authority；conversation 只提供 provenance。

## Direction workspace and Git

方向运行产物只位于：

    temp/directions/<direction-id>/exp/
    temp/directions/<direction-id>/test/

source 位于 experiments/candidates/，tests 位于 tests/experiments/candidates/，
durable scientific artifacts 位于对应 docs/research/candidates/<direction-id>/。

路径归属由 assignment body 的 owned_paths 声明。方向 actor 可在自己的路径内
自主修改、测试、commit 和 push。共享 main 在多方向工作期间可以暂时 dirty；
quiescent 时由各 owner 清理为 clean main。worktree 可选，不是默认要求。

共享 C++ backend、神经网络基座和跨方向核心修改必须先向用户说明 exact paths、
目标、非目标及语义影响并取得确认。方向自主权不能扩张到共享核心。

使用 native Windows Git/Python，项目 Python 优先使用
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe。tracked path 使用
repository-relative POSIX syntax，durable text 遵循 .gitattributes 的 LF。

## Working style

- 保留用户和其他 session 的修改，只处理 assignment 声明的方向与路径。
- Clerk 持有全局拓扑；participant 不协调其他 manager session。
- EM/CM 只加载 assignment/return 格式，不加载全局控制面。
- Codex task list/history 是 session 事实源；不得建立平行 registry 证明同一事实。
- reviews 与 tests 是风险相称的 evidence，不是授权层。
- 机械检查失败只返回 exact 字段或越界路径；LLM 不据此发明新 gate。
- 实验执行继续使用 hmasd_run.py；不要把 session 协调塞进实验或 Git 工具。
