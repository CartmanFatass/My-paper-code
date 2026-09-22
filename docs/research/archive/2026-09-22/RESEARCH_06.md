# Retired agent-count consultation-stage plan — 2026-09-22

Source: `46a1f3097eb7cf33202bd6cfa9d80374047fa560`, `docs/research/RESEARCH.md`.
Retired after the complete Pro fallback was read and the DM selected B02/B03. The actual
Answer and scientific decisions remain append-only in the direction notebook; this is only
the superseded index standing/plan, not a new research record or direction closure.

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B01 六个 360k fits 全部核验，每臂 3、0 失败；N4/6/8 的 H6−SET J 为 +.021721/+.044000/+.045222，command wall 共 471.56 min。保留实际实现下的探索包收益。owner 已明确继续研究；新检查纠正旧动作契约描述：原始高斯动作未经声明范围限制而直接执行，且两臂训练方差不同；未证明它造成收益。已转入动作法则诊断，准备新的针对性 Pro 咨询，优先提案为六个冻结终点策略的 raw/clip 共同世界比较（0 fits、288k eval steps）；是否追加训练由此问题与咨询决定。0 新训练/0 已接受新批次，未进入确认，不再以旧 idle 决策停留。[事实、推理与提案](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--owner-continuation-and-action-law-premise-correction)。 |

| Topic | Plan | Conditions and evidence |
| --- | --- | --- |
| **N 数量泛化** | B01 六 fits 完整保留；owner 继续指示后转入动作执行契约与学习曝光诊断。 | 实际 raw-action 路径不执行声明的动作边界，原有 H6 优势暂限于该实现。新 Pro 问题评议六个冻结策略的 raw/clip 比较（0 fits、288k eval steps），明确部署干预不能清除训练曝光解释；不直接进入原配方确认或按结果调熵。后续训练若值得，另定固定契约、种子与成本。[新证据与问题](../../candidates/agent_count_generalization/NOTES.md#pro-question-2026-09-22-action-law-and-next-count-study)；[退役的已完成批次后计划](RESEARCH_05.md)。 |
