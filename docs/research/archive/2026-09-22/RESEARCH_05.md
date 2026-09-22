# Retired agent-count post-B01 plan — 2026-09-22

Source: `3362e0c9b5d5d49472ad14a3747059e47fa66a31`, `docs/research/RESEARCH.md`.
Retired when the owner instructed this DM to continue and an action-law premise correction
changed the next scientific comparison. The B01 measurements remain evidence under their
actual execution law; this retirement does not alter other directions or reopen frozen work.

## Shared topic 3 passage before the action-law qualification

固定数量训练后的零更新数量迁移，与回合内成员变化、cross-play 和能力异质性是不同问题。
S1 的学习器 scalar 为原生团队 reward 除以 N，跨 N 服务须用实际测试 N 恢复原生单位，
并在同一测试 N 内比较；改变 N 同时改变容量与联合物理条件。N=6 训练、N=4/6/8 测试的
每臂三个完整训练实例中，H6 相对普通共享 SET 在两个未见 N 的最终原生 J/覆盖均值更高，
N6 也无相对损失，支持保留这个有界学习包。该探索结果不建立一般数量不变性、训练总体排名，
也未分离技能、表示、内在奖励、带宽和额外计算的作用；不同时刻仍有不利比较和后期回落。
[完整数量比较、反面曲线与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--b01-complete-comparison-and-bounded-retain-decision)。

## Direction standing before continuation

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。S1 N=6→4/6/8，H6 对普通共享 SET，输入 `5a250d97e`；六个预写 360k fits 全部完整核验（每臂 3、0 失败）。固定终点 H6−SET J 均值差为 +0.021721/+0.044000/+0.045222，unseen 等权差 +0.033472；各 H6 训练实例在每个 N 的最终均值均高于三个 SET，N6 未见相对代价。保留当前有界包与完整成本，仍为探索结果，无总体排名或组件归因。科学 command wall 合计 471.56 min（H6 263.12、SET 208.43），共享节点耗时不等于方法固有速度。本轮比较与保留判断完成；当前空闲，0 运行/0 排队，未进入确认。未来有用观察是相同固定配方在新训练种子和新最终世界上的复现，尚未选中或接受新批次。[完整比较与判断](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--b01-complete-comparison-and-bounded-retain-decision)。 |

## Superseded next-step plan

| Topic | Plan | Conditions and evidence |
| --- | --- | --- |
| **N 数量泛化** | 原生 S1 固定 k、N=6→4/6/8 的 B01 六 fits 已完成，保留有界 H6 包；当前 0 运行/0 排队。 | 两个未见 N 的固定终点原生 J/覆盖均改善，训练 N6 无相对损失；每臂 3 次训练仍是探索比较，成本和组件差异保留。下一有用区别是新训练种子／新最终世界能否复现该固定包优势，需另写实际前瞻计划；无自动确认、改架构或追加 fit。[完整结果](../../candidates/agent_count_generalization/NOTES.md#2026-09-22--b01-complete-comparison-and-bounded-retain-decision)；[退役的初始计划](RESEARCH_03.md)。 |
