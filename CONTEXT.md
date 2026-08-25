# HMASD Research Workflow

HMASD 的研究工作流把高价值决策、低成本编排和有界执行分开，使每类工作既可直接互动，又保有明确的科学与工程责任。

## Language

**Top-level Task**:
用户可直接进入、持续互动且保存独立会话记录的长期工作身份。它与其他 Top-level Task 同级，不因由谁创建而成为其下级代理。
_Avoid_: Main session, manager subagent

**Root**:
拥有完整操作能力的低成本编排者，负责可靠地传递已形成的决定、调度工作和整合结果，但不形成重要的 Portfolio、科学或工程决定。
_Avoid_: Decision maker, sole entry point, Portfolio owner

**Portfolio**:
负责跨研究方向判断、排序、生命周期和工程投入选择的最高能力决策者。它按需或周期性工作，并把已形成的决定交给 Root 编排。
_Avoid_: Audit, read-only reviewer, second Root

**EM**:
一个研究方向内的科学判断与综合责任者，负责形成该方向的科学结论和下一步研究需求。
_Avoid_: Research worker, Portfolio delegate

**CM**:
一个研究方向内有界工程范围的技术判断与协调责任者，负责把冻结的科学需求转化为工程结论和可整合结果。
_Avoid_: Implementer, generic project manager

**Decision Authority**:
对某类重要判断形成可执行结论的责任。它与执行该结论所需的操作权限相互独立。
_Avoid_: Permission, tool access

**Operational Authority**:
执行、协调、恢复和整合已授权工作的能力，不自动包含改变科学、Portfolio 或工程决定的权力。
_Avoid_: Decision authority

**Decision Packet**:
由用户、Portfolio、EM 或 CM 形成并记录的有界结论、约束和下一步请求，用于让 Root 在不重新判断其内容的情况下编排执行。
_Avoid_: Approval token, handoff gate

**Durable Authority**:
在会话之外仍可恢复和核对的项目事实。会话记录提供互动来源，重要决定需要进入其所属的 Durable Authority 才能驱动跨任务工作。
_Avoid_: Transcript, dashboard, runtime task ID
