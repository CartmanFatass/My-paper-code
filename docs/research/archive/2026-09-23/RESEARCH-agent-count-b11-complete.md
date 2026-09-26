退役日期：2026-09-23。DM1 固定 B11 两臂已完成并独立读取，下列仅保存被替代的 DM1 计划与最后运行快照。
来源：已发布 main `16d9063f5be7f0a34cac0d7878ced1542a36fe7e` 的 RESEARCH.md。
其他 DM 的现行计划与全部 owner 控制没有由本次退役改变；当前状态见 ../../RESEARCH.md。
完整冻结合同、原生输出、反例和后续问题仍在人数方向 NOTES。此摘录不再维护。

## 原方向运行快照

| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B10已完整验收：0 fits/48k eval/.984229 command min；普通三面板逐世界复现B07，48/48世界标签和执行动作改变。复用真实开局技能使N4/6/8平均J增加+.004172/+.003888/+.009197，未见N每步多服务.3155人；42/48世界J提高，但1545811少服务5.302人/步，N4质量均值下降。按事前混合后果分支保留具体部署取舍，不全面替换普通重选，不选按N/世界开关。固定诊断结束，无待收操作。B11 已固定前瞻比较：两个全新普通 SET 分别 N6/c10、N8/c10 训练，各360k team steps；共同实际初始张量，最终在共同新世界测 N8 主用途和 N6 专门化代价，2 fits/720k train/64k eval。T6/T8 为2.16M/2.88M agent rows，分别101250/135000次 actor及critic优化器更新，不声称等曝光或纯N因果。实现8项检查与独立复审通过；两臂均已在4070原生准入，源dc1bc1f27，实际初始张量/normalizer/RNG一致。T6已完成并收回15文件70,177,262bytes，独立轨迹重算及固定360k训练/32k评估计数通过；原生轨迹和逐世界终点已保存，T8仍沿原句柄运行，配对科学判断待齐。剩余观察已重挂；[T6完整收取与边界](../../candidates/agent_count_generalization/NOTES.md#b11-t6-collected-and-checked-t8-pending)；[运行与共同初始化](../../candidates/agent_count_generalization/NOTES.md#b11-native-acceptance-both-fixed-fits-running)；[前瞻、适用建议与L0](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b11-prospective-ordinary-set-training-conditions-for-n8-use)。方向与lead保留。B07包、B08有用学习和熵反证不改；n=1，不识别技能必要性、一般机制或计算节约。[完整结果、轨迹、反例与成本](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b10-complete-opening-assignment-replay-improves-means-with-consequential-local-losses)。 |

## 原 B11 计划

| **DM1：泛化与训练条件** | H6 的有界包优势保留，普通 SET 在训练 N6 也落后，故“只是没见过 N8”不成立。负载结果把动机指向策略产生的资格与服务，未证明学习一定能恢复差距。 | **已选择：两个全新普通 SET 分别在 N6/c10、N8/c10 训练，各360k team steps**；共同新世界最终测 N8（主用途）与 N6（专门化代价），**2 fits / 720k train / 64k eval**。看完整 J、资格、服务、损失世界与代价；不复用旧 SET 作新对照，不声称纯 N 因果或已补齐 H6。B11 前瞻、实现与独立检查已完成；T6 已完整收取且独立验算通过，T8 原句柄继续，齐备后按固定终点作配对读取。 |

**DM1 的关键实现与读法。** 指定旧 runner 的 Python `train_n` 已参与环境和批量，CLI 却没有该入口，
且 reward_units 写死 N6、seed 限定旧六-fit 合同；新比较须有自己的 prospective 与入口，保留旧实验绑定。
共同初始化核对实际张量；计量真实 N、样本行数、更新/优化量，并验证最终评价零更新。
T6/T8 分别暴露 **2.16M/2.88M agent rows**，reward/N 和联合物理条件也不同；等团队步不是等曝光。
Δ8=J(T8,N8)−J(T6,N8) 是主要用途，Δ6 是专门化后果，不能看结果后重加权；
每个 N 保存32世界配对幅度、正负数、不利尾部，世界级区间不替代独立训练重复。
混合 N4/6/8 是宽条件用途的最强替代；需要时另定调度和曝光，三种 N 的完整评价为96k而非64k。
