# Retired local observation encoding standing and initial plan — 2026-09-22

Source revision: `9029b4847bc42dacfd9671742f454b14f3014a90`.
This preserves the wording of the superseded LOE standing and initial comparison passages
from RESEARCH before the completed B01 study was archived; relative links are pinned to
the source revision so they remain usable from this archive. Only this direction's
pending decision and prospective comparison are retired here. Other directions and their
accepted operations remain in the current index. The complete question, Pro Answer and DM
decision remain in the direction's append-only NOTES; no in-flight answer target is moved.

[Complete source index](https://github.com/CartmanFatass/My-paper-code/blob/9029b4847bc42dacfd9671742f454b14f3014a90/docs/research/RESEARCH.md)

## Previous LOE standing

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `local_observation_encoding` | 同一合法局部观测下，普通稠密槽位/关系编码能否改善完整 HMASD 的有限学习？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c6ef-7c4b-7f02-b96d-ab115d467af8`，host `local`；checkout `/home/fires/.codex/worktrees/d683/hmasd-wsl`，branch `codex/local-observation-encoding`。B01 两个 fits 均完整完成（输入 `efe7d61e8`，每臂 360k 团队步）：ORIGINAL/DENSE J45 为 0.458426/0.202254，平均连接 31.939/13.416；DENSE fit wall 约 1.95 倍。三个预写面板均不利；每臂仅一个训练 seed，不作总体排名。暂拟结束此配方投入，聚焦 Pro 咨询后定案；无新 fit 计划。[完整结果与判断](https://github.com/CartmanFatass/My-paper-code/blob/9029b4847bc42dacfd9671742f454b14f3014a90/docs/research/candidates/local_observation_encoding/NOTES.md#2026-09-22--b01-complete-adverse-package-observation)；[已提交咨询](https://github.com/CartmanFatass/My-paper-code/blob/03eea08a6b3f3fa714b1cdc90d9339f86ed56e94/docs/research/candidates/local_observation_encoding/NOTES.md#pro-question-2026-09-22-dense-recipe-stop)。 |

## Initial comparison context and rule

**当前四项投入。** 已选择表中的普通局部信息组织、技能周期与有限学习、N 数量泛化、UAV 端到端服务预测。
它们分别改变表示、时间选择、训练/测试团队数量、服务监督，首问互不依赖新模块或阳性结果。
周期比较是现有计划中尚未执行的共同学习问题，此次由 owner 授权选题后单独分配；不重启旧 FSD 信用救援，
不接管 Claude notebook。技能规模、实际重组、churn、cross-play 等保留候选地位，不自动排队。

| 研究问题 | 当前优先次序与第一个比较 | 证据如何约束投入 |
| --- | --- | --- |
| **普通局部信息组织** | 首选：S1、固定 k，完整 HMASD 的现有 encoder 对普通稠密槽位/关系 encoder。 | 同一合法数值、类型/排序；保留 FiLM、GRU、高低层共同学习、discovery、PPO 和物理动作。无持久实体 ID/真值有效位，不从 simulator state 偷加 mask；不同时叠加稀疏选择、预测损失、技能规模或新 critic。B05 支持认真比较输入组织，未证明关系瓶颈。 |

**第一笔投入的产物与选择规则。** 普通编码比较应读完整原生 J、预定学习曲线位置、已有服务分量和实际训练/推理成本。
有用则保留普通改进；不明则按未决问题的价值选择独立重复或停止；只有代理改善且没有值得付费的新区别时结束该配方。
完整 HMASD 表示比较不能承担“层次结构胜过 flat MARL”的结论，后者另需能学好的同信息 flat 参照。
实际 horizon、种子和 fits 由选中后的 prospective note 声明，本页没有接受批次。
