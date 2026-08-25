# P05 — ExpoComm

论文：*Exponential Topology-Enabled Scalable Communication in Multi-Agent Reinforcement Learning*，ICLR 2025
原文：[本地 PDF](../papers/P05_ExpoComm_ICLR2025.pdf) · [会议 PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/3514dbacaebf0f38b25adfe59ed81a8a-Paper-Conference.pdf)
代码：[官方仓库](https://github.com/LXXXXR/ExpoComm) · 本地 `../code/P05_ExpoComm`

## 一句话结论

ExpoComm 是有价值的 many-agent 通信拓扑研究：它用指数偏移边把通信边数和图直径同时压低，并展示从小团队到 20–100 个智能体的 zero-shot transfer。它依赖固定循环索引和同步全局时钟，不能直接支持 roster churn；对 HMASD 最有价值的是 Field-Slot 局部场/关键残差的有界候选拓扑，而不是完整算法。

## 机制拆解

对编号为 `i` 的智能体，静态指数图连接偏移约为 `1, 2, 4, ...` 的成员并对 `N` 取模。这样静态版本约有 `N floor(log2(N-1))` 条有向边，直径约为 `ceil(log2(N-1))`。one-peer 版本每个时刻只激活其中一个指数邻居，把瞬时边数降到 `N`，由消息记忆跨时间传播信息。

代码中的关键路径为：

- `src/controllers/ExpoComm_controller.py::get_exp_neighbors`：构造指数偏移邻居；
- `src/modules/agents/ExpoComm_agent.py`：消息 RNN/GRU、邻居聚合及辅助任务；
- controller 以固定 `self.n_agents` 组织 hidden state 和成员维度；one-peer 选择依赖同步的 `t % topk_neighbors`。

## 对 many-agent 的贡献

ExpoComm 直接解决完全通信的 `O(N^2)` 边开销，且小直径让远距离信息在少量轮次传播。论文在大规模 MAgent 和基础设施规划任务中测试，并报告从较小训练规模到更大测试规模的迁移。这说明拓扑规则可随一个新的固定 `N` 重新生成，而不要求学习每一条 pairwise link。

但这不是运行时变 `N`：成员索引构成稳定环。若中途删除一个成员并压缩索引，许多节点的邻居会瞬间改变；其消息 RNN 中保存的旧拓扑语义不再对应新邻居。新成员加入也没有 hidden-state 初始化和历史冷启动定义。

## 与 Field-Slot 的映射

ExpoComm 可作为以下两个模块的候选来源：

```text
live sparse communication graph -> F_local_i 的候选邻域
bounded exponential neighbors   -> C_i 的候选集合上限
```

但必须作三项改造：

1. 用当前活跃 roster 的稳定成员键或 active-rank 构图，不能依赖永久连续 ID；
2. roster event 后重建拓扑并明确消息记忆保留/清空规则；
3. 在掉队造成割点或低能量关键中继时做 live-graph connectivity repair，不能假定原指数图仍连通。

它也不能替代 `critical_neighbors` 的影响判据：指数偏移只提供低成本候选，稀有关键成员仍需一般性的连通性、能量、能力兼容等特征筛选。

## 对 `k / T_i` 的实际支持

one-peer 的轮换由所有成员共享的环境时刻 `t` 驱动，论文没有每智能体不同决策持续期、事件时长 return 或异步 GAE。消息记忆跨同步步传播，不等于技能级 `T_i`。

论文还用全局状态重构或对比目标来 grounding message。它们可能改善通信，但会引入新的辅助优化边；在 HMASD 不应与 N/k 主问题捆绑，更不能转成任务特定 intrinsic reward。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| CONDITIONAL | 指数稀疏拓扑作为局部/关键候选源 | 需改成 live roster 构图并验证掉队后的连通性 |
| DIAGNOSTIC | `O(N log N)` 静态图与 `O(N)` one-peer 图的效率基线 | 可检查 Field-Slot 是否隐藏了全 pair 打分 |
| DO_NOT_ABSORB | 固定循环成员索引与同步轮换时钟 | roster churn 会重映射邻居和消息状态 |
| DO_NOT_ABSORB | 默认加入状态重构、对比损失或通信奖励 | 会把表示/拓扑问题与新优化目标混杂 |

## 最小后续因果门

只有 Field-Slot 表示门通过后，才应在同一 active roster 上比较物理稀疏图与指数候选图的连通性、内存/时间斜率及关键成员召回；首轮不训练通信辅助目标，也不同时引入变 `k`。本报告不授权实现或实验。
