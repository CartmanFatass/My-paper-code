# Retired agent-count initial comparison and running standing — 2026-09-22

Source revision: `99f9757bc22b0f91f55c5046af316508ca9b56b3`.
This preserves the agent-count initial-comparison wording and last running standing that
were superseded by the completed six-fit B01 comparison and bounded retain decision.
The final accepted operation has been collected, verified and read; no live operation or Pro
answer target is moved. Other directions keep their own current owners and standing.
The full question, Pro Answer, prospective design and result interpretation remain in the
append-only direction NOTES. Relative evidence links below are pinned to the source revision.

[Complete source index](https://github.com/CartmanFatass/My-paper-code/blob/99f9757bc22b0f91f55c5046af316508ca9b56b3/docs/research/RESEARCH.md)

## Previous agent-count standing

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。S1 N=6→4/6/8；H6 对普通共享 SET，预写 6 个探索 fits、每 fit 360k 团队步，输入 `5a250d97e`。已有 5 项完整核验（H6×3、SET×2）：第三 H6 最终 N4/N6/N8 J=0.561704/0.517460/0.441317，command wall 69.68 min；各 N 均低于自身 rollout-30 面板。三个 H6 的最终各 N 均超过已完成两个 SET，正差仍是未完成比较的探索性观察，无总体排名。最后 SET（915413）已在 `wsl_4070` 准入运行，同句柄观察。全部 6 项已启动：5 完成、1 运行、0 未启动；待完整收读后作原定范围内的判断，无追加 fit 排队。[最新结果与解释](https://github.com/CartmanFatass/My-paper-code/blob/99f9757bc22b0f91f55c5046af316508ca9b56b3/docs/research/candidates/agent_count_generalization/NOTES.md#2026-09-22-fifth-completed-fit--h6-seed-914413)；[最后运行](https://github.com/CartmanFatass/My-paper-code/blob/99f9757bc22b0f91f55c5046af316508ca9b56b3/runs/agent_count_generalization/s1_count_b01_set_s915413/launch-manifest.json)。 |

## Initial agent-count comparison

| 研究问题 | 当前优先次序与第一个比较 | 证据如何约束投入 |
| --- | --- | --- |
| **N 数量泛化** | N 轴默认入口：固定 k、每回合固定 roster 的 train-N→test-N，普通共享/set generalist 对明确干预。 | 同一测试 N 内比较；specialist 成本另计。无需同时实现 churn、独立混编与异质能力，也不依赖 S1 编码或 duration 阳性。 |
