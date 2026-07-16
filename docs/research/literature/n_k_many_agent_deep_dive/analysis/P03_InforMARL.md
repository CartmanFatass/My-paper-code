# P03 — InforMARL

论文：*Scalable Multi-Agent Reinforcement Learning through Intelligent Information Aggregation*，ICML 2023
原文：[本地 PDF](../papers/P03_InforMARL_ICML2023.pdf) · [PMLR PDF](https://proceedings.mlr.press/v202/nayak23a/nayak23a.pdf)
代码：[官方仓库](https://github.com/nsidn98/InforMARL) · 本地 `../code/P03_InforMARL`

## 一句话结论

InforMARL 是短名单中对解绑 `N` 的表示层最直接的实现参考：局部图消息传递和全局固定维聚合可以跨不同团队规模复用权重。其证据是跨 episode、跨环境配置的 zero-shot `N` 泛化，不是 episode 内动态 roster；它最适合作为 Field-Slot 的 full-set reference 和局部场骨架。

## 机制拆解

InforMARL 把智能体、目标和障碍物表示为图节点，以感知/距离阈值构造局部边。`onpolicy/algorithms/utils/gnn.py` 使用 PyTorch Geometric `TransformerConv` 做局部消息传递：每个焦点智能体的 actor 读取自身节点聚合，critic 则对全部节点或智能体表示做 mean/max/add 等固定维 pooling。

关键属性是参数作用于节点和边特征，而不是绑定到第几个智能体。`graph_actor_critic.py` 和 `graph_buffer.py` 仍按一次运行的配置组织数据，但 GNN 本身可以用同一权重处理不同节点数。

## 对 `N` 的证据与边界

论文分别在 3、7、10 个智能体上训练和测试，也展示了在 3 个智能体训练后到 7 个智能体测试的泛化；目标和障碍物数量也可变化。这证明的是：

- 权重和输出维度不必随 `N` 变化；
- 局部稀疏图可限制每个焦点的有效信息范围；
- permutation-safe aggregation 能让模型接受新的固定规模配置。

但 runner 在每次启动时仍由配置确定 `num_agents` 和节点数。论文没有测试 episode 中途成员离开、归队或新增，也没有定义 survivor recurrent state、成员事件 mask 或离开时的 bootstrap。因此它只解决了 open-size representation 的一部分。

纯 mean pooling 还有一个对 HMASD 很重要的盲点：相同经验分布但不同绝对人数会得到相同向量。Field-Slot 中的 slot mass 和 `log(1+N)` 正好补足这一点；稀有中继或低电量成员还需要 bounded exact residual，不能期待平均池化保留。

## 对 `k / T_i` 的实际支持

InforMARL 采用常规同步 MARL rollout，没有事件时长字段、`gamma^T_i` 或异步 GAE。GNN 可接收 elapsed-control-time token，但论文不提供相应 credit 证据。因此它是变 `N` 的表示部件，不是变 `k` 的训练方案。

## 与 Field-Slot 的映射

```text
InforMARL local graph  -> F_local_i 的稀疏候选与消息传递
global graph pooling   -> full_set_reference / 固定维全局参考
Field-Slot additions   -> slot mass + log(1+N) + critical exact residual
```

必须保留的复杂度条件是：邻域来自物理图、通信图、空间索引或有界采样；若先计算所有有序 pair 再 Top-L，仍是 `O(N^2)`。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| ABSORB | 共享参数的局部稀疏图编码 | 不绑定成员槽位，适合无人机邻域交互 |
| ABSORB | 固定维、permutation-safe 的 active-set reference | 可作为 Field-Slot 表示门的强基线 |
| CONDITIONAL | mean pooling | 必须加入绝对人数/质量信息和稀有成员残差 |
| CONDITIONAL | 跨配置 `N` 泛化 | 不能替代 episode 内 join/leave 测试 |
| DO_NOT_ABSORB | 固定形状 runner 作为 open-roster collector | 缺少成员事件和 hidden-state continuity contract |

## 最小后续因果门

沿 Field-Slot README 的既定顺序，先做监督式表示充分性门：`full_set_reference` 可采用 InforMARL 式 active-set GNN；`hybrid_field_slot` 与其比较 held-out `N`、稀有关键成员、反协调、置换/填充等价及运行时斜率。首门不同时测试变 `k`。本报告不授权实现或实验。
