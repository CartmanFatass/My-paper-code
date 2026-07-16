# P08 — IARO

论文：*Inter-Agent Relative Representations for Multi-Agent Option Discovery*，ICLR 2026
原文：[本地 PDF](../papers/P08_IARO_ICLR2026.pdf) · [作者终稿](https://homepages.inf.ed.ac.uk/msridhar/Papers/iclr26_multiagentOptionsDiscovery.pdf)
代码：[官方仓库（未下载）](https://github.com/raulsteleac/IARO)

## 一句话结论

IARO 的 Fermat state / feature-wise spreadness 对“用相对场描述群体协调模式”有启发，但其 joint option 要求全员投票、全员同步执行并共同终止，正面冲突于 HMASD 想要的不同 `T_i` 和动态 roster。它适合作为同步偏置与相对表示的诊断，不适合作为当前技能系统的代码底座。

## 机制拆解

IARO 先把联合状态因子化为各智能体状态，学习一个使到所有成员距离总和最小的虚拟 Fermat state，再计算每个状态特征相对该中心的 spreadness。随后在这种相对表示上估计图拉普拉斯特征向量，并以其为 intrinsic reward 训练 temporally extended joint options。

这种压缩把“绝对位置组合”转为“成员沿不同特征有多不对齐”，因此能发现聚拢、单轴对齐等协调模式。论文展示前三个智能体与四个智能体上出现相似对齐行为，并在附录用共享特征空间/padding 扩展到两类异质 toy agents。

## 对 `N` 的证据与边界

Fermat objective 对成员求和，形式上可接受不同集合大小；从 3 到 4 个成员的可视化也说明某些相对模式对团队规模具有一致性。然而下游 joint option 定义固定为
`pi_W = (pi_W^1, ..., pi_W^N)`，并要求启动阈值 `n_W = N`。主实验采用固定的 4-player LBF 和固定 Overcooked 队伍，没有 episode 内 join/leave。

成员变化不仅改变输入集合，还会改变 Fermat state、spreadness、全员投票阈值和 option policy 的联合语义。论文明确把“任意成员子集参与的 option”留作未来工作。因此它不构成 open-roster 方案。

异质扩展也有严格前提：不同类型必须共享可对齐的状态特征，类型需要可推断，缺失特征用 padding 并由距离函数忽略。它是 toy-level 表示证据，不是多技能无人机 roster 证据。

## 对 `k / T_i` 的实际支持

joint option 必须由全队达成一致后同步执行；终止要求所有参与者都选择终止动作，另有统一 50 步 hard stop。若任一智能体认为 option 不再有利，还可触发共同 interruption。这里的时间抽象是“全队共享一个 option 周期”，不是每个技能/成员独立 `T_i`。

这反而给 HMASD 一个重要反例：强同步可能在固定协作任务中产生漂亮协调模式，但充电、掉队和不同技能周期会让最慢成员支配所有人的重新决策时刻。

## 与 Field-Slot 的映射

可保留的只是表示层直觉：相对位置/运动/能力的 feature-wise dispersion 可作为通用场特征或 slot 诊断，用来检查场是否区分多个群体模式。不能把 Fermat 对齐本身变成任务奖励，也不能用单一中心替代多槽和 rare-critical residual；多模态团队很可能被一个中心别名化。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| CONDITIONAL | feature-wise 相对 spreadness 作为无奖励的表示/诊断特征 | 可帮助发现场压缩的多模态 aliasing，但需独立门验证 |
| DIAGNOSTIC | 全队同步 option 作为变 `T_i` 的反例 arm | 能量/掉队场景下应暴露 barrier synchronization 代价 |
| DO_NOT_ABSORB | 全员投票、全员共同终止和统一 hard stop | 与 per-agent `T_i` 直接冲突 |
| DO_NOT_ABSORB | 图拉普拉斯 eigenvector intrinsic rewards 和新 option 系统 | 引入新的奖励、技能发现和训练因果边 |
| DO_NOT_ABSORB | 单 Fermat center 取代 Field-Slot + exact residual | 易丢失多模态和稀有关键成员 |

## 代码下载决策

本轮未下载仓库。论文已经给出足够证据表明其核心执行 contract 与目标相反；当前真正需要的相对场思想可从公式和表示诊断中独立实现，无需引入整套 option-discovery/IQL 代码。保留官方链接供未来单独研究 option discovery。

## 最小后续因果门

若 Field-Slot 表示门出现多模态 aliasing，可增加 feature-wise dispersion 作为无奖励输入/诊断，与原 hybrid field 做单变量比较。不要在首个 N 门或首个 k 门中训练 IARO options。本报告不授权实现或实验。
