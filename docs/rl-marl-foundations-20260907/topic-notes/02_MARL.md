# MARL：合作、信息、协调和 MAPPO

## 模型分类首先说明目标和信息

Markov game 描述状态、联合动作、转移和各 agent 的 reward。所有 agent 共享团队 reward 时是完全合作情形。若所有参与者都获得充分的全局状态，可以讨论 fully observable cooperative game / MMDP；Dec-POMDP 还明确分散执行及各 agent 可用的观测历史。共享 reward 不是 Dec-POMDP 的充分定义。

分散执行的核心是每个动作根据该 agent 被允许取得的信息生成，而不是必须使用多个不同网络。信息可以包含本地观测、历史、共享摘要或通信，具体取决于任务假设。完整模型可能允许联合观测的相关性，不能把各 agent 的观测核无条件假设成独立。[Albrecht 等教材](https://www.marl-book.com/)；[Amato 等，2019，§2.1](https://lis.csail.mit.edu/pubs/amato-konidaris-jair19.pdf)

## CTDE 和参数共享各自改变什么

CTDE 是训练与执行的信息安排。训练 critic 可以使用执行 actor 没有的额外信息；actor 仍受执行信息边界约束。若团队摘要本来就能在部署时取得，它可以进入 actor。通信模型可以理想化，也可以显式描述延迟、带宽和丢失；采用哪种假设应由具体研究问题决定。

参数共享是一种模型组织方式和归纳偏置。它能共享数据与参数；配合身份、角色或不同输入，也可以形成不同 agent 的行为。其表达限制取决于输入和网络结构，不能简单说共享参数必然同质，也不能说不共享参数自然形成协调。

CTDE、参数共享、循环记忆和通信都不保证任务 return 提升。它们改变学习可用的上下文、策略表示或优化过程，效果需要结合任务判断。[MAPPO 论文，§§3–5](https://arxiv.org/abs/2103.01955)

## 信用分配与非平稳性

团队 reward 同时包含跨时间和跨 agent 的贡献。中心 critic 可以利用联合上下文，但它不自动给出各 agent 的真实因果贡献。反事实 baseline、差分 reward 和值分解采用不同假设处理这一问题，不能仅凭用了中心 critic 就声称信用分配已解决。

本地两篇工作提供的是具体方法案例：[Consensus Learning](https://doi.org/10.1609/aaai.v37i10.26385) 与 [Contrastive Identity-Aware Learning](https://doi.org/10.1609/aaai.v37i10.26370)。它们说明协调与行为差异可以成为方法设计对象；各自实验不构成所有合作任务上的普遍结论。本地正文位置见来源索引 L1、L2。

训练中队友不断更新策略，会使单个学习者面对的有效行为分布变化。部署时用户移动或 UAV 暂时失效，则可能只是固定转移核中的状态变化。参数在线更新、状态变化、任务规律漂移和记忆递推需要分别命名，以免用“非平稳”掩盖不同问题。

## MAPPO 为什么是一个具体而有用的起点

MAPPO 原论文使用 PPO 和集中价值估计进行合作多智能体学习。执行 actor 使用被允许的观测或历史；critic 用于训练。PPO epoch、mini-batch、归一化、clipping、death masking 等设置可以影响实际表现，但不是 CTDE 或 MAPPO 名称所保证的固定答案。

论文在 MPE、SMAC、GRF 和 Hanabi 上提供了强经验结果，并研究若干实现因素。它支持把成熟实现作为对照起点，不证明 MAPPO 在当前 UAV 任务最优。[Yu 等，2022](https://arxiv.org/abs/2103.01955)；[官方代码](https://github.com/marlbenchmark/on-policy)

采用循环 MAPPO，可以让基线也利用历史信息。新机制若增加合作表征、角色或异步技能，需说明这些结构如何进入策略或训练过程；基线有无对应能力以及具体差别，应来自实际接口和实现，而不是只根据名称判断。

## 阅读范围

本文提供一般概念。原讨论的信息接口与研究选择另见 [会话选择记录](../SESSION_CHOICES.md)，不能据此替换其他方向的实际任务条件。
