# HMASD Research Workflow

## Language

**Top-level Task**:
可被用户直接进入并独立恢复的长期工作身份；其创建关系不构成上下级或权限关系。
_Avoid_: manager subagent

**Root**:
永久持有最高项目操作能力的编排身份，可在用户已授权的范围内形成 Portfolio、科学或工程决定，并把决定写入正确的既有权威。
_Avoid_: sole entry point, permission gate

**Workflow Clerk**:
默认停驻的异常文书与旧格式兼容身份；它只整理程序精确报告的协议缺陷并交给程序指定的责任方，不参与正常流。
_Avoid_: coordinator, scheduler, router, permission manager, fifth domain owner

**Protocol Kernel**:
以已验证类型化消息和显式观察到的任务快照驱动单一 work_id、并把每次推进限制为程序定义原子动作的确定性机制；它不从自然语言或隐式缓存补事实。
其 Agent Result 与 Next-packet Draft 绑定已经实现；Stage D 术语还包括
canonical typed return witness（ignored runtime 表示）、typed Effect/ref observer、
resource comparator 和 Codex App Server native adapter。
_Avoid_: LLM coordinator, workflow prose, Clerk

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

**Common Agent Result**:
参与任务对一个 Work Packet 产出的机器校验结果；其 assignment_id 等于输入 work_id，结构化 path+SHA256 引用可验证新鲜度，而不透明字符串引用的新鲜度属于专用领域契约。
_Avoid_: free-text handoff, completion authority

**Return Witness**:
对一个 exact `work_id` 的 canonical typed `agent_result` 与可选 draft 的不可变
ignored runtime 表示；用于恢复和去重，不是 completion ledger。
_Avoid_: ack, queue state, terminal-by-language

**Next-packet Draft**:
由 canonical build 生成的完整候选 Work Packet；请求后续责任时，Common Agent Result 只以该 draft 的唯一 work_id 绑定它。
_Avoid_: routing hint, prose proposal, partial packet

**Protocol Defect**:
程序对缺失字段或引用、旧格式不可路由或精确 schema/identity 缺陷的有界报告；
其 envelope 具有 field_path、ref、actual、expected、failure_scope、
producing_command 和 responsible_owner，v1 recovery owner 固定为 Root。
_Avoid_: bare blocked, model uncertainty, permission request

**Effect**:
会改变外部或持久状态的精确操作；其 typed 形式包含 kind、resource_id 和可选
operation，并以独立身份和回执核对，未知提交只观察而不重放。
_Avoid_: ordinary reasoning step

**Resource Comparator**:
对显式 Work Packet 的 write/effect resource 做有界相交判断的 reconcile/adapter
内部确定性机制。
_Avoid_: scheduler, lease, claim, control primitive

**Native Adapter**:
把协议动作映射到 Codex App Server 的 task/thread/turn 观察与发送接口的运行时适配层。
_Avoid_: second workflow authority

**Reconciliation**:
基于当前权威和 Effect 事实推进一个有界可运行动作的过程；它不推断全局流程状态。
_Avoid_: daemon, global recovery engine

**Direction-owned Code**:
某一研究方向可以自主修改、测试和提交的代码范围。
_Avoid_: shared-core

**Shared-core**:
未归入任何方向的共享代码范围；精确修改须先得到用户一次明确确认。v1
authority allowlist 仅包括 AGENTS.md、WORKFLOW_PROTOCOL.md、PORTFOLIO.md 和
对应方向 DIRECTION.md；其他 Markdown 不是 authority。
_Avoid_: default direction-owned code
