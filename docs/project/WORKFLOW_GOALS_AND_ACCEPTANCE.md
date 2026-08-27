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
  原生 task 工具创建或复用 task、发送消息、等待返回、路由下一切面并向用户汇总。
- **Portfolio**：只负责方向选择、优先级和投资判断。
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

对仍为 ACTIVE 的方向，当前切面完成也不等于方向完成。科学定义缺失时 Portfolio
路由 EM；科学目标已接受但实现、test、CLI 或 instrumentation 缺失时路由 CM。
缺少现成实现本身不是 PARK 理由。

## Codex、LLM 与 script 的分工

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| Codex task plane | task 身份、历史、create/send/read/wait、同 task 继续、用户控制 | HMASD 方向语义 |
| Clerk LLM | 全局拓扑、读取 RETURN、选择并联系下一责任角色 | 方向内科研或工程判断 |
| EM/CM LLM | assignment 内的局部判断、填写并发送 RETURN | 其他方向、全局调度、恢复状态机 |
| scripts | envelope schema、关联 ID、方向/路径 containment、简单日志、实验命令事实 | 创建/等待 task、解释 prose、选择下一 hop、模拟 Codex 会话 |

script 校验失败只报告机械输入问题，不授予或否定用户权限，也不生成新 gate。

## Git、实验和共享核心

- 各方向在自己的 source、test、doc 与 temp/directions/<direction-id>/ 路径内
  自主工作、测试、commit 和 push；worktree 可选，不是默认。
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

真实验收使用 Codex 原生可见 task 与真实方向。synthetic transport、隐藏
app-server manager、raw rollout 重建或对 Codex 产品能力的重复证明不得代替。

## 退出正常路径的历史机制

hmasd_codex_tasks.py run-chain/execute-plan、本地 task cache、raw thread parser、
Work Packet planner、return witness 及其恢复状态机，不再是正常工作流或验收 seam。
完成调用依赖核查前代码可以暂留，但 Root、Clerk、Portfolio、EM、CM 不得自动
加载或调用。

删除旧实现前必须先检查是否仍被实验、Git 或领域工具调用，并保留用户与其他
session 的在途修改。
