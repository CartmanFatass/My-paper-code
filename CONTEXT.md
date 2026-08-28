# HMASD Research Workflow

## Language

**Top-level Task**:
可被用户直接进入并独立恢复的长期工作身份；其创建关系不构成上下级或权限关系。
_Avoid_: manager subagent

**Root**:
永久用户与 shared-core 入口；把 Portfolio、科学或工程工作直接投递给对应责任 task，
但不代替该角色形成领域决定。
_Avoid_: sole entry point, permission gate, domain substitute

**Portfolio**:
负责跨方向选择、排序、生命周期和工程投入判断的责任域；它按需存在且可独立恢复。
它直接向 EM 投递由自己冻结的完整 WORK，并把 RESULT 返回当前 requester。
_Avoid_: generic coordinator, engineering implementer, audit, read-only reviewer

**EM**:
负责一个方向科学判断、证据综合和下一步研究需求的责任域；它按需存在且可独立恢复。
_Avoid_: research worker

**CM**:
负责一个方向有界工程判断、实现协调和可整合结果的责任域；它按需存在且可独立恢复。
_Avoid_: generic project manager

**Durable Authority**:
会话之外可恢复和核对的既有项目事实；决定必须写入所属权威后才能成为跨任务依据。
_Avoid_: transcript, dashboard, runtime task ID

**Domain Writer**:
对某类 Durable Authority 内容负责的责任身份；它不等同于实际执行一次工作的身份。
_Avoid_: runtime actor, permission check

**Runtime Actor**:
实际发送、接收或执行一次有界工作的会话身份；它在概念上区别于 Domain Writer，并为运行时
可追溯性服务。
同一个 EM/CM task 可以同时是对应领域 writer；native task ID 只作可见运行定位，不成为
durable authority。
_Avoid_: hidden manager, local task identity record

**Requester**:
使用 Codex 原生 task ID 向相邻责任角色直接发送完整 bounded WORK 的 top-level task。
Requester 自己拥有 objective、paths、Effects、acceptance 与 refs；callee 把 RESULT 直接返回
WORK 中的 `Return task`。用户直接进入 participant 时不制造返回 ID。
_Avoid_: router, inferred work brief, durable reply ledger

**Effect**:
会改变外部或持久状态的精确操作；外部提交未知时只观察而不重放。
_Avoid_: ordinary reasoning step

**Handoff**:
作出下一步需求判断的 requester 自己冻结并直接发送完整 WORK；callee 完成后把 RESULT
直接返回该 requester。Portfolio 正常投递 EM，EM 正常投递 CM，CM 返回 EM，EM 返回 Portfolio。
_Avoid_: intermediary forwarding, prose-derived assignment, daemon, global recovery engine

**Direction-owned Code**:
某一研究方向可以自主修改、测试、提交和 push 的代码范围；有 Git-visible 改动时，
top-level 责任 session 在 RESULT 前自行收尾并报告 Git 信息。
_Avoid_: shared-core

**Shared-core**:
未归入任何方向的共享代码范围；精确修改须先得到用户一次明确确认。
_Avoid_: default direction-owned code
