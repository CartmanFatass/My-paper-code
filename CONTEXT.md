# HMASD Research Workflow

## Language

**Top-level Task**:
可被用户直接进入并独立恢复的长期工作身份；其创建关系不构成上下级或权限关系。
_Avoid_: manager subagent

**Root**:
永久持有最高项目操作能力的编排身份，可在用户已授权的范围内形成 Portfolio、科学或工程决定，并把决定写入正确的既有权威。
_Avoid_: sole entry point, permission gate

**Portfolio**:
负责跨方向选择、排序、生命周期和工程投入判断的责任域；它按需存在且可独立恢复。
_Avoid_: audit, read-only reviewer

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
实际发送、接收或执行一次有界工作的会话身份；它与 Domain Writer 分离，并为运行时可追溯性服务。
_Avoid_: domain writer, decision owner

**Work Packet**:
一次有界跨会话工作传递的不可变运行时载体，引用已有权威的精确版本且可至少一次投递；同一标识的重复接收不改变其语义。
_Avoid_: decision authority, workflow state machine

**Effect**:
会改变外部或持久状态的精确操作；它以独立身份和回执核对，未知提交只观察而不重放。
_Avoid_: ordinary reasoning step

**Reconciliation**:
基于当前权威和 Effect 事实推进一个有界可运行动作的过程；它不推断全局流程状态。
_Avoid_: daemon, global recovery engine

**Direction-owned Code**:
某一研究方向可以自主修改、测试和提交的代码范围。
_Avoid_: shared-core

**Shared-core**:
未归入任何方向的共享代码范围；精确修改须先得到用户一次明确确认。
_Avoid_: default direction-owned code
