# HMASD 工作流设计目标与验收标准

状态：用户确认的工作流权威目标
Decision owner: User
确认日期：2026-08-27

本文档定义工作流必须达到的结果。冲突的历史协议、skill、测试夹具与实现属于
迁移对象，不能改变本目标。

## 核心边界

Codex 的独立 top-level task/session 是可信任务平面。项目直接使用 Codex 已提供的
可见 task 身份、会话历史、上下文隔离，以及原生 create、send、read、wait 和同
task 继续能力。

HMASD 不重新验证、缓存或模拟这些产品能力。项目只补充 Codex 不知道的领域语义：
方向、角色、局部目标、允许路径、结果类型和必要证据。

> 信任 Codex task plane；只机械验证项目语义边界。

## 角色

- **Root**：最高能力的用户入口，可介入任何角色，但不做普通流程的例行转递。
- **Workflow-Clerk**：唯一可见的长期协调 session。它持有全局拓扑，使用 Codex
  原生 task 工具创建或复用 task、发送消息、接收返回、路由下一切面并向用户汇总。
- **Portfolio**：只负责低频的跨方向选择、优先级、资源投入和 lifecycle 判断；它
  把决定 RETURN 给 Clerk，不创建或派发 Root、EM、CM task。
- **EM/<direction-id>/g<generation>**：只负责一个方向的科研语义。
- **CM/<direction-id>/g<generation>**：只负责一个方向的工程语义。
- **Experiment Operator**：CM 的单层执行 child，只运行一个冻结的结果命令。

角色是责任边界，不是用户权限 gate。EM/CM 不需要了解全局拓扑，只需要知道自己
可接收和必须返回的 envelope 格式。

## 唯一正常流程

1. Clerk 使用 Codex 原生项目 task 接口创建或复用一个可见 session。
2. Clerk 向该 session 发送一个标准 ASSIGNMENT envelope。
3. 接收 session 只在 envelope 的方向、目标和路径内工作。
4. 接收 session 在结束当前 turn 前，使用 Codex 原生消息能力向 assignment 指定的
   Clerk thread 发送一个标准 RETURN envelope。
5. Clerk 收到并核对 RETURN 后，在结束处理前向下一责任 session 发送新的
   ASSIGNMENT，或向用户发送 terminal summary。
6. task 已停止但没有匹配 RETURN 时，Clerk 继续同一个 task 并重投同一关联
   assignment；不创建重复 session。

科研或工程工作完成但没有完成第 4 步，只表示局部工作停止，**不表示自动交接
完成**。下一责任角色已经收到消息，才算本 hop 完成。

对仍为 ACTIVE 的方向，当前切面完成也不等于方向完成。participant 应用
`REQUEST_EM` 或 `REQUEST_CM` 明确普通下一责任；只有跨方向选择、优先级、资源投入
或 lifecycle 判断才使用 `REQUEST_PORTFOLIO`。Portfolio 把决定 RETURN 给 Clerk，
由 Clerk 路由 EM/CM。缺少现成实现本身不是 PARK 理由。

## Codex、LLM 与 script 的分工

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| Codex task plane | task 身份、历史、create/send/read/wait、同 task 继续、用户控制 | HMASD 方向语义 |
| Clerk LLM | 全局拓扑、读取 RETURN、选择并联系下一责任角色 | 方向内科研或工程判断 |
| EM/CM LLM | assignment 内的局部判断、填写并发送 RETURN | 其他方向、全局调度、恢复状态机 |
| scripts | envelope schema、关联 ID、方向/路径 containment、简单日志、实验命令事实 | 创建/等待 task、解释 prose、选择下一 hop、模拟 Codex 会话 |

script 校验失败只报告机械输入问题，不授予或否定用户权限，也不生成新 gate。

Clerk 使用 `.codex/prompts/hmasd-workflow-clerk.md` 中唯一的方向无关语义表。每个
事件 turn 先从 Codex task list/read 建立临时拓扑快照；快照不落盘为第二 registry。
同一批正交方向必须完成全部 ready assignment 的原生 send 后结束事件 turn；普通
事件 turn 不调用 wait，RETURN 由新原生消息再次唤醒。一个方向的科学名词、证据、
失败或等待不得出现在另一方向的 envelope 中。

内存 admission 失败是 result launch 前的可恢复资源等待：run CLI 不创建 reserved
output root；仅对旧版本留下的、无 manifest/日志/结果且目录为空的精确 partial
root 执行机械回收。Clerk 为 exact direction/run_id 保持至多一个 heartbeat，并把
它绑定到 retry assignment 的 exact recipient session；prepare 的责任 session 默认
是同方向 CM，而不是 Root/Clerk。责任 session 收到 assignment 后重试冻结 prepare，
PREPARED 后发送 RETURN 并取消自身，不得创建 Operator 或改变
estimate/command/code SHA。

## Git、实验和共享核心

- 各方向在自己的 source、test、doc 与 temp/directions/<direction-id>/ 路径内
  自主工作、测试、commit 和 push；有 Git-visible 改动的 top-level 责任 session
  在 RETURN 前自行提交并 push exact owned paths，报告 branch、commit SHA、
  remote/ref 与 push 结果。leaf helper 和 Root 不代为做普通方向 Git 收尾；
  worktree 可选，不是默认。
- 路径归属来自 assignment 的 owned_paths。机械检查只检测越界，不判断科研
  意义。
- 共享 C++ backend、神经网络基座和跨方向核心修改需要用户确认 exact paths 与
  语义影响。危险操作警告并记录，但确认后不得形成权限死锁。
- 实验命令 owner、进程终态和 stdout/stderr 继续由 hmasd_run.py 记录；session
  协调不重复实现实验运行器。
- MARL 实验遵循真实科学与资源价值，不因 toy case 追求无意义 float64 精度或
  逐路径穷举。

## 可观察验收

1. Portfolio、EM、CM 与 Clerk 均为 Codex 项目任务列表中的可见 top-level task；
   同方向同角色没有重复 task。
2. 每次跨 session 投递都是标准 envelope；EM/CM 的 identity、direction_id 和
   路径属于同一方向。
3. participant 在 final 前原生发送 RETURN；Clerk 收到后原生发送下一
   ASSIGNMENT 或 terminal summary。
4. 缺失或 malformed RETURN 在同一个 task 中补发，不重做已完成工作、不复制
   manager。
5. 一个方向的失败、等待或用户问题不停止其他方向；故障明确限定为 project、
   direction、feature 或 effect。
6. ACTIVE 方向的切面完成会收到下一责任角色 assignment；实现缺失会进入 CM，
   不会无理由停在 idle/PARKED。
7. 四个真实方向可同时经历上述转递，用户可以观察并随时介入。
8. 机械测试只覆盖 envelope 格式、关联、方向 identity 和路径 containment；不重复
   测试 Codex 是否能 create、send、wait、保存历史或恢复 session。
9. 四方向事件同时到达时，Clerk 在结束事件 turn 前已发送所有独立 ready
   assignment，且普通事件 turn 不调用 wait；task list/read 中的方向拓扑与 exact
   task ID 足以解释每一次 send。
10. 内存不足的 prepare 不留下 reserved root；同一 direction/run_id 只有一个可见
    heartbeat，且它位于 retry assignment 的责任 session；PREPARED 后该 heartbeat
    被取消，且未提前创建 Operator。
11. Portfolio 只通过 correlated RETURN 给 Clerk 提供低频材料决定；任何新建的
    `Portfolio -> Root/EM/CM ASSIGNMENT` 都被 envelope CLI 拒绝。切换前已在途的
    legacy assignment 只允许完成一次 RETURN；原 sender 只把同一 locator 一次性
    转发给 Clerk，不得派生新的直连边。
12. 有 Git-visible 改动的责任 session 在 RETURN 前已 commit/push exact owned
    paths 并报告 Git 信息；其他方向的 dirty files 未被带入 commit。worktree 要么
    已由 owner 精确回收，要么带 exact branch/HEAD/reason 明确保留。

真实验收使用 Codex 原生可见 task 与真实方向。synthetic transport、隐藏
app-server manager、raw rollout 重建或对 Codex 产品能力的重复证明不得代替。

## 退出正常路径的历史机制

hmasd_codex_tasks.py run-chain/execute-plan、本地 task cache、raw thread parser、
Work Packet planner、return witness 及其恢复状态机，不再是正常工作流或验收 seam。
完成调用依赖核查前代码可以暂留，但 Root、Clerk、Portfolio、EM、CM 不得自动
加载或调用。

删除旧实现前必须先检查是否仍被实验、Git 或领域工具调用，并保留用户与其他
session 的在途修改。
