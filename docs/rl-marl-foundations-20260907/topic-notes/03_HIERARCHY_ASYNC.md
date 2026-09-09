# 层次 RL、技能与异步多智能体

## Option 的定义不要求所有部分都是学习模块

经典 option 写作 \(o=\langle\mathcal I_o,\pi_o,\beta_o\rangle\)：启动集合、执行期间的内部策略、终止机制。它们可以预先给定，也可以学习，不必分别实现成神经网络。固定动作保持可构成固定 option；按经过的步数终止时，可以使用内部计时或相应扩展状态。

Learned skill 强调行为由数据获得；latent skill variable 首先是策略的条件变量；角色是某种分工描述。这些概念可以组合，但不能仅凭名称相互等同。一个 \(\pi(a\mid o,z)\) 加上固定的选取与持续规则，也可能定义有效的 option，不要求另设 initiation/termination 网络。是否如此，应检查实际执行语义。[Sutton、Precup、Singh，1999](https://www.cs.utexas.edu/~shivaram/readings/b2hd-SuttonPS1999.html)；[Amato 等，2019，§2.3](https://lis.csail.mit.edu/pubs/amato-konidaris-jair19.pdf)

## 持续时间进入回报和后续价值

在合适的 Markov 状态及 option 条件下，option 边界上的过程可以用 Semi-MDP 描述。一段持续 \(\tau\) 个 primitive steps 的样本包含：

\[
R_t^o=\sum_{j=0}^{\tau-1}\gamma^j r_{t+j+1}.
\]

对给定高层策略，其 option value 可写成：

\[
Q(s,o)=
\mathbb E\left[
R_t^o+\gamma^\tau V(S_{t+\tau})
\mid S_t=s,O_t=o
\right].
\]

持续时间、累计 reward 和终止状态可能相关，期望必须保留这种联合关系。一步 primitive action 是相应特例。若使用部分观测、历史依赖或多个异步 option，不能因为“动作持续若干步”就认定原始 observation 是 Markov SMDP 状态。[Amato 等，2019，§§2.3–3](https://lis.csail.mit.edu/pubs/amato-konidaris-jair19.pdf)

## 时间抽象提供什么，也可能付出什么

高层较少决策、低层在片段内部控制，可以把探索和行为组织到更长时域。这些结构可能有助于发现或复用行为，也可能限制可表达动作、错过调整时机或产生额外学习困难。技能存在不等于技能有用，低频决策不等于更高 return。

Option-Critic 展示一种联合学习内部策略和终止的方式，证明“option 可以学”，不是规定“所有 option 都必须这样学”。[Bacon、Harb、Precup，2017](https://ojs.aaai.org/index.php/AAAI/article/view/10916)

## 异步的核心是不同 agent 的决策边界

当 option 持续时间不同时，一些 agent 重新选取 option，另一些继续内部执行。因此，轨迹要能够表示相关持续时间、正在执行的行为、可用历史与团队 reward。局部边界与联合环境演化之间的关系，是异步学习的实质内容。

MacDec-POMDP 和宏动作 MARL 给出相应建模及算法例子；ACAC 则提出具体的 agent-centric actor–critic 方法。不同方法可以采取不同的经验组织和价值估计。某一种 padding、replay、GAE 或历史编码并非 options 定义的一部分。[Xiao 等，2020](https://proceedings.mlr.press/v100/xiao20a.html)；[Jung 等，2025](https://proceedings.mlr.press/v267/jung25a.html)

## 几个时间尺度应各自命名

| 过程 | 发生了什么 |
|---|---|
| Primitive control | 产生或执行当前环境步的动作 |
| Option 内部执行 | 保持某个 option，由内部策略产生动作 |
| 高层选择与终止 | 决定继续、终止或选择新的技能/角色 |
| 记忆与状态估计 | 从新观测更新 RNN 状态、历史摘要或信念 |
| 参数学习 | 用数据更新策略、critic 或模型参数 |

同一个 option 持续时可以更新记忆，也可以改变 primitive action。终止 option 不意味着发生 optimizer step；参数固定也不意味着记忆冻结。

## 与本地研究资料的连接

*Hierarchical Multi-Agent Skill Discovery* 的 team/individual latent、skill coordinator 和条件策略是一个具体设计案例。是否把某个现有实现称为严格 option，须看其选取、执行和终止规则；本轮资料收集没有据名称替当前代码作这个判断。[Yang 等，2023](https://papers.neurips.cc/paper_files/paper/2023/hash/c276c3303c0723c83a43b95a44a1fcbf-Abstract-Conference.html)

保持时间、切换次数或结构可视化可以帮助描述行为，但评价应对应实际任务和所问的主张。原讨论的异步框架与合作机制选择另见 [会话选择记录](../SESSION_CHOICES.md)。

本地 MARL-0449、MARL-0553 的正文范围，以及上述基础论文的访问状态见 [来源索引](../sources/READING_MAP.md)。

