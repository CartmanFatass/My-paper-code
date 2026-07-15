# 核心判断

这是一个真实且有潜力的创新方向，但需要先区分两类问题：

[
\boxed{
\text{跨 episode 的可变 }N
\neq
\text{episode 内成员动态加入/离开}
}
]

前者主要是**变长张量与泛化问题**；后者是更难的 **open-roster MARL**，还会改变 recurrent state、skill lifetime、buffer、GAE 和 high-level credit 的语义。

严格来说，**MAT 的序列建模思想并不天然排斥可变 team number**。原始 MAT 就把 team 表示成变长 agent sequence，并报告了跨 agent number 的迁移；其 advantage decomposition 对任意一个给定 agent 集合的排列成立。真正没有被自动解决的是：**同一 episode 内 active agent set 改变以后，谁参与当前联合策略、历史 hidden 如何保存、离队是否等于终止、加入是否产生额外高层决策机会。** ([arXiv][1])

你当前 R30 实现则确实是固定 (N) 的：

* `ar_prefix_dim = K(1+2N)`；
* roster 里含有每个 agent 的 identity-specific skill/age block；
* 每个 token 都遍历 `range(n_agents)`；
* high critic 直接展平 (N\times obs)，输入维度含 (NK+2N)。

所以改变 (N) 会直接改变网络参数形状，而不仅是更换 mask。

---

# 一、现有方法有哪些

| 方法                            |                          复杂度 | 能否处理动态 (N)          | 主要问题                                   |
| ----------------------------- | ---------------------------: | ------------------- | -------------------------------------- |
| `N_max` padding + active mask |  dense MAT 为 (O(N_{\max}^2)) | 可以，但不能超过 (N_{\max}) | 浪费算力、slot identity 泄漏、模型尺寸仍绑定最大团队      |
| Deep Sets / mean pooling      |                       (O(N)) | 可以                  | 对精细 pairwise complementarity 表达较弱      |
| Dense Set Transformer         |                     (O(N^2)) | 可以                  | 大团队时显存和计算较重                            |
| Induced Set Transformer       | (O(NM))，(M) 为固定 latent slots | 可以                  | 需要证明固定 slots 没有成为新的容量瓶颈                |
| 稀疏图 GNN / 局部 attention        |           (O(E))，通常约 (O(Nk)) | 可以                  | 可能丢失全局协调，需要额外 global token             |
| Mean-field / skill histogram  |                       (O(N)) | 可以，且非常可扩展           | 很难表达“某两个特定功能必须互补”的离散角色结构               |
| 动态分组/层级 squad                 |               约 (O(N\log N)) | 可以                  | 分组本身成为新的 latent assignment 与 credit 问题 |

Deep Sets 给出了集合上的 permutation-invariant/equivariant 建模框架；Set Transformer 在此基础上建模成员间交互，并通过 inducing points 将 attention 从二次复杂度降到相对 agent 数线性的复杂度。([arXiv][2])

对当前 UAV 场景，最合理的不是单独选其中一个，而是：

[
\boxed{
\text{entity/set encoder}
+
\text{固定数量 inducing slots 或稀疏图}
+
\text{变长 autoregressive KEEP/SET scan}
}
]

---

# 二、推荐的主结构：Open-Roster Set-AR R30

可以将新的控制结构写成：

[
\boxed{
k_0
+
A_\tau\text{ 动态 active set}
+
\text{set-equivariant AR KEEP/SET}
+
\text{per-agent variable lifetime}
}
]

其中：

[
A_\tau={i:m_{i,\tau}=1},
\qquad
n_\tau=|A_\tau|.
]

这里 (m_{i,\tau}) 表示 agent 是否是当前 team member。

## 1. 把 agent 表示成实体 token，而不是固定 slot

对每个当前 active agent：

[
x_{i,\tau}
==========

\phi\left(
o_{i,\tau},
\operatorname{onehot}(z_{i,\tau}),
\log(1+age_{i,\tau}),
c_{i,\tau}
\right),
]

其中 (c_i) 是可选的、通用的 capability descriptor，例如：

* 最大速度；
* 电池容量；
* 通信/感知范围；
* UAV 类型；
* action availability。

**不要输入 agent index 或固定位置 ID。**

随后使用 permutation-equivariant set encoder：

[
{h_{i,\tau}}*{i\in A*\tau},
g_\tau
======

E_{\mathrm{set}}
\left(
{x_{i,\tau}}*{i\in A*\tau}
\right).
]

这里：

* (h_i) 是每个 UAV 的 contextualized representation；
* (g_\tau) 是 deterministic pooled team context；
* (g_\tau) 只是高层 representation，不是重新引入 sampled team latent；
* (g_\tau) 不进入 low actor，仍保持：

[
a_{i,t}\sim\pi_l(a_i\mid o_{i,t},z_{i,t}).
]

当前 strict low actor 本身已经是共享的 local-observation + skill-FiLM + recurrent executor，因此低层 actor 主体比当前 high actor 更接近 team-size agnostic；主要需要重构的是 high roster encoder 和 centralized critic。

---

## 2. 不再构造 identity-specific roster vector

当前 R30 roster 是固定长度、按 agent identity 分块。可以改成一个 working-roster set statistic：

[
u_i^{(j)}
=========

\psi\left(
h_i,
z_i^{(j)},
\log(1+age_i^{(j)}),
b_i^{(j)}
\right),
]

其中 (b_i^{(j)}) 表示这个 agent 在当前 AR sequence 中是否已经处理。

聚合：

[
r^{(j)}
=======

\frac{1}{n_\tau}
\sum_{i\in A_\tau}u_i^{(j)}.
]

另外显式输入：

[
c_N=\log(1+n_\tau),
]

因为 mean pooling 本身会丢失团队大小。

当第 (j) 个 agent 的 working state 被 KEEP/SET 更新时，不需要重新编码全队：

[
r^{(j)}
=======

r^{(j-1)}
+
\frac{
u_{\sigma(j)}^{new}-u_{\sigma(j)}^{old}
}{
n_\tau
}.
]

这一步非常重要。它把当前“每个 token 重新遍历整个固定 roster”的潜在 (O(N^2)) 扫描，降为：

[
O(N)
]

的初始化加增量更新。

---

## 3. 动态长度 autoregressive factorization

对 active set 采样一个外生顺序：

[
\sigma_\tau\sim\operatorname{UniformPerm}(A_\tau).
]

然后：

[
\pi_H(\mathbf e_\tau\mid X_\tau,\sigma_\tau)
============================================

\prod_{j=1}^{n_\tau}
\pi_H
\left(
e_{\sigma_\tau(j),\tau}
\mid
h_{\sigma_\tau(j),\tau},
g_\tau,
r_\tau^{(j-1)},
j/n_\tau,
\log(1+n_\tau)
\right).
]

有效动作仍完全保持：

[
e_i\in
{\texttt{KEEP}}
\cup
{\texttt{SET}(z):z\ne z_i}.
]

这样：

* sequence 长度自动等于当前 active member 数；
* 不需要给每种 (N) 建立不同 policy；
* 无须优化 (N!) 种 agent order；
* order 是外生随机变量，原样存入 buffer 并 teacher-force replay；
* 网络不看 agent ID，随机顺序的边际策略是 permutation-equivariant。

原始 MAT 的关键分解本来就允许任意 agent permutation；使用随机顺序而不是固定 UAV 编号，可以避免顺序本身变成身份 shortcut。([arXiv][1])

不建议此时增加“学习 agent order”的 priority head。它会引入另一个离散决策、另一个 credit path，并把本来清晰的“动态 roster”问题变成“动态 roster + learned ordering”联合问题。

---

# 三、如何降低 attention 和 AR 的计算量

推荐两种可组合实现。

## 方案 A：Induced Set Attention

使用固定 (M) 个 deterministic inducing slots：

[
L_\tau
======

\operatorname{Attn}
\left(
Q_{1:M},
K=X_\tau,
V=X_\tau
\right),
]

[
H_\tau
======

\operatorname{Attn}
\left(
Q=X_\tau,
K=L_\tau,
V=L_\tau
\right).
]

复杂度约为：

[
O(n_\tau M d),
]

其中 (M) 与 team size 无关，例如固定为 8 或 16。

它比直接把所有 UAV 两两 self-attention 更适合作为可变 fleet size 的默认方案。Set Transformer 的 inducing-point attention 正是为集合交互中的二次成本问题提出的。([arXiv][3])

## 方案 B：局部图 + 一个 global token

构造通用关系图：

[
G_t=(A_t,E_t),
]

边只由一般物理可观测关系决定，例如：

* 是否在感知范围内；
* 是否在通信范围内；
* 相对距离的 (k)-nearest；
* 已存在的物理链路。

运行若干层局部 message passing：

[
h_i'
====

F\left(
h_i,
\operatorname{Agg}*{j\in\mathcal N(i)}
M(h_i,h_j,e*{ij})
\right).
]

再用一次全局 set pooling 得到 (g_\tau)。

复杂度约为：

[
O(|E_t|)\approx O(n_\tau k).
]

图策略已经被用于可变团队和 open-team 建模；相关工作表明，图表示能够处理成员数量变化和不同实体类型，但这并不自动解决你这里的 variable-lifetime credit，需要另外定义 membership/skill semantics。([arXiv][4])

对于 UAV 网络，我更倾向：

[
\boxed{
\text{local sparse graph}
+
\text{small global inducing-slot pool}
}
]

因为通信和物理影响通常是局部稀疏的，但服务覆盖或 relay 可行性又可能依赖全局团队结构。

---

# 四、动态成员与技能寿命必须是三个不同的时钟

变量 team number 加入后，系统实际上有三个时间对象：

[
\boxed{
\begin{aligned}
k_0 &:\text{固定全局检查时钟}\
M_i &:\text{agent }i\text{ 的成员资格区间}\
T_i &:\text{agent }i\text{ 当前技能的实际寿命}
\end{aligned}
}
]

不能把它们混在一起。

## 1. 新成员加入

为保持固定 check clock，最干净的第一版合同是：

> 加入事件可以在任意 primitive step 被观测，但新成员只在下一个全局 check 正式进入 active controller。

在 admission check：

* 初始化其 low actor hidden state；
* `has_active_skill=False`；
* age 为 0；
* `KEEP` 被 mask；
* 必须执行 initial `SET(z)`；
* admission 不被算作一次“技能切换失败”；
* 之后才开始 normal KEEP/SET survival。

这样不会因为 team member 加入而给系统额外的异步高层决策机会。

如果真实系统要求 UAV 加入后立即行动，可以在工程层使用一个固定安全控制器直到下一次 check；不要在研究主线中临时增加 arrival-triggered high check，否则固定 (k_0) 的因果合同会被破坏。

## 2. 成员离开

若 agent 在 check 之间离开：

* 立即从 low action set 删除；
* 关闭其 recurrent rollout trace；
* 关闭当前 skill segment，但完成原因标记为：

```text
membership_censored
```

而不是：

```text
SET
environment_terminal
policy_switch
```

* 其他 agent 的 episode、hidden state、skill 和 age 不应重置；
* 离开前已经执行的 high token 仍属于当时 active set 的合法决策；
* 不给 departure、survival 或 member count 任何 intrinsic reward。

因此技能寿命统计应分别报告：

[
T_i^{SET\ completed}
]

和：

[
T_i^{membership\ censored}.
]

不能把离队造成的短 segment 解释成 high policy 偏好短技能。

## 3. 重新加入

最安全的默认语义是：

[
\text{rejoin}=\text{new membership instance}.
]

即：

* hidden 重新初始化；
* skill 重新 initial SET；
* lifetime 不跨 inactive gap 延续。

持久 UAV ID 可以用于环境状态恢复和 hidden-state dictionary 的索引，但**不能作为网络输入特征**。

---

# 五、buffer、GAE 与 PPO 如何改

## 1. Ragged high rows

每个 high row 存储：

```text
active_agent_keys
active_count
agent_order
prev_skills
prev_ages
token_kind
set_skill
token_valid
joined_mask
membership_censored_mask
```

训练时可以 pad 到当前 minibatch 的最大 (N_B)，但所有计算必须由：

[
m_{\tau,j}^{valid}
]

mask。

这和“模型绑定固定 (N_{\max})”不同：padding 只是一种 batch implementation，网络参数本身不依赖 (N_B)。

## 2. High loss 按 team-check 归一化

推荐延续当前 R30 的 shared block advantage，并把每个 check 的 token loss 平均：

[
L_H
===

\frac1B
\sum_{\tau=1}^{B}
\frac{
\sum_j
m_{\tau,j}
\ell_{\tau,j}^{PPO}
}{
\sum_jm_{\tau,j}
}.
]

这样 (N=20) 的一条 environment transition 不会仅因为 token 多，就比 (N=5) 获得四倍 optimizer 权重。

需要诚实标注：在可变 (N) 下，这是一种 **team-size-normalized PPO objective**，不是完整 joint likelihood ratio 的精确 PPO。直接把全部 token ratio 相乘会使 ratio variance 随 (N) 急剧增长，也不适合作为实际实现。当前项目本来就采用共享 check advantage 和 token-dimension averaging，并且不声称完整 MAT monotonic theorem，因此这一扩展在语义上是连续的。

## 3. Low GAE 必须区分两种 done

需要两个 mask：

[
d^{env}_{i,t}
]

和：

[
d^{member}_{i,t}.
]

对 agent (i) 的 recurrent trace：

[
m^{trace}_{i,t}
===============

(1-d^{env}*t)(1-d^{member}*{i,t}).
]

成员离开会切断该 agent 的 low GAE 和 recurrent trace，但不会切断其他成员的 trace，也不会把整个 environment 视为 terminal。

## 4. Critic 不再 flatten roster

高层 critic 改为：

[
V_\psi^H
========

\rho_V
\left(
\operatorname{Pool}{h_i:i\in A_\tau},
\log(1+n_\tau),
s_\tau^{entity}
\right).
]

若 centralized state 中也包含 variable number of agents，应将它拆为 typed entity set，而不是把所有 agent state 拼接成固定向量。

critic 输出仍是每个 high check 一个 scalar，所以：

* critic loss 每个 environment row 计算一次；
* 不随 team number 重复；
* ValueNorm 不需要为每个 (N) 建立独立 head；
* critic 必须看到 (n_\tau)，否则同一个 pooled mean 无法区分 3 个 UAV 和 30 个 UAV。

---

# 六、不把所有 UAV 当“标准 agent”，是否会计算爆炸

关键是：

[
\boxed{
\text{共享参数}
\neq
\text{假设所有 agent 行为相同}
}
]

真正需要的是**条件交换性**：

> 两个 agent 若交换完整 token，输出也相应交换；但 token 中的能力、状态、历史不同，所以它们可以产生完全不同的策略。

可以按异质程度分三层。

## 同构 UAV、状态不同

直接共享：

[
\pi(a_i\mid o_i,z_i).
]

差异来自 observation、skill 和 recurrent hidden。

## 少数固定 UAV 类型

采用：

[
\text{shared trunk}
+
\text{type embedding}
+
\text{small type-specific action head}.
]

参数规模与 UAV 类型数量相关，不与实际 team member 数量相关。

## 连续能力差异或不同 action configuration

使用 capability-conditioned hypernetwork：

[
\theta_i^{head}=H(c_i),
]

[
\pi_i(a_i)=\pi(a_i\mid h_i,z_i;\theta_i^{head}).
]

Permutation-invariant input 和 permutation-equivariant output、以及基于 agent/entity descriptor 生成模块或权重，已有 DPN/HPN 一类方法作为先例；UPDeT 也通过 entity/action-group decoupling 处理不同观察与动作配置。([arXiv][5])

若加入的 UAV 甚至不由共享 policy 控制，而是未知第三方控制器，那么问题已经从 variable-team CTDE 变成 open ad hoc teamwork。此时需要每个 teammate node 的行为 belief/model，例如：

[
b_{i,t}
=======

q(\text{teammate type/policy}\mid\text{observed history}),
]

再把 belief embedding 输入图网络。Open ad hoc teamwork 的图方法正是针对“未知成员、成员组成随时间变化、部分可观测”这一更强问题。([arXiv][6])

你的联合训练 UAV fleet 在第一阶段没有必要承担这个更强假设。

---

# 七、真正可能形成论文创新的部分

下列单项本身都不够新：

* variable number of agents；
* padding/mask；
* GNN；
* Set Transformer；
* shared policy；
* MAT 的 variable-length decoder。

更有价值的贡献是：

[
\boxed{
\textbf{Open-Roster Asynchronous Skill Editing}
}
]

具体因果对象是：

[
\boxed{
\begin{aligned}
&\text{dynamic active-agent set}\
&+\text{fixed global information clock}\
&+\text{per-agent KEEP/SET skill survival}\
&+\text{membership-censored process semantics}\
&+\text{set-equivariant autoregressive composition}.
\end{aligned}
}
]

可以形成这样的论文级假设：

[
\boxed{
\begin{aligned}
&\text{在成员数量和成员资格动态变化的 cooperative MARL 中，}\
&\text{将 membership clock 与 individual skill lifetime 解耦，}\
&\text{比固定长度、同步刷新或固定 roster controller}\
&\text{产生更稳健的跨团队规模合作。}
\end{aligned}
}
]

这里最独特的不是“可变团队”，而是：

[
\boxed{
\text{team membership change 不等于 skill renewal}
}
]

例如：

* 一个 relay UAV 离队，不应迫使所有剩余 UAV 同步换 skill；
* 一个 UAV 加入，不应重置现有成员的技能寿命；
* 新成员只需 initial SET，旧成员可以 KEEP；
* 其他成员可以在后续 checks 中异步调整；
* skill lifetime 是 agent active membership interval 内的 survival process。

这和你的原始异步寿命动机非常一致。

---

# 八、最安全的研究推进顺序

不要一开始就把“variable team number”和新的 intrinsic mechanism 同时加入。否则自然技能形成失败时，无法判断来自：

* set encoder；
* membership handling；
* critic；
* AR order；
* intrinsic；
* dynamic task difficulty。

建议按下面顺序推进。

## Gate 0：结构正确性

必须满足：

1. **Permutation equivariance**

   输入 agent tokens 任意置换，per-agent action/edit distribution 同样置换，team value 不变。

2. **Padding invariance**

   增加任意 masked dummy slots，全部有效输出严格不变。

3. **Membership locality**

   一个 agent 离开，不重置其他 agent 的 hidden、skill、age 或 global check clock。

4. **No-ID gate**

   网络输入中无 persistent agent ID 或固定 slot embedding。

5. **Ragged replay parity**

   stored variable-length order/token replay 的 old/new log-prob 在未更新参数时一致。

## Gate 1：固定 (N) 安全性

在原有固定六 UAV 合同下比较：

```text
current fixed-roster R30
versus
set-equivariant R30
```

两者均 reward-pure，不引入 team churn。这里只回答架构替换是否破坏现有学习与 lifetime supply。

## Gate 2：跨 episode 的 unseen-(N) 泛化

例如训练团队规模集合：

[
N_{\mathrm{train}}={4,6,8},
]

评估：

[
N_{\mathrm{test}}={5,7,10}.
]

必须使用同一组网络参数，不为新 (N) fine-tune。

## Gate 3：episode 内 open roster

加入成员 churn，但先保持外部 reward 和技能机制不变，验证：

* join/leave 后策略仍稳定；
* unaffected agents 的 recurrent continuity；
* censored lifetime 与 policy switch 正确区分；
* 性能退化小于 fixed-roster/padded control；
* 计算时间随 (N) 近似线性或 (O(NM))。

## Gate 4：variable lifetime contribution

最后才比较：

[
\text{open-roster per-agent KEEP/SET}
]

与：

[
\text{open-roster shared/fixed lifetime}.
]

这时才能提出：

[
\text{variable member count}
+
\text{variable skill length}
]

的联合贡献。

---

# 最终推荐

在当前代码和研究目标下，最合理的技术路线是：

[
\boxed{
\begin{aligned}
&\text{保留低层 }\pi_l(a_i\mid o_i,z_i),\
&\text{将 high roster 和 critic 改为 entity-set architecture},\
&\text{用小型 inducing set 或 sparse graph 控制复杂度},\
&\text{在当前 active set 上执行变长 AR KEEP/SET},\
&\text{用随机、已存储的 agent order 保持交换性},\
&\text{显式分离 membership termination 与 skill switch},\
&\text{把加入、离开和 skill survival 写成三时钟 SMDP}.
\end{aligned}
}
]

不建议直接放弃 MAT 式 autoregressive composition；应当放弃的是当前的：

[
\boxed{
\text{固定身份 roster flattening}
}
]

而不是：

[
\boxed{
\text{顺序联合编辑本身}.
}
]

从计算、泛化和科学可解释性看，最佳折中是：

[
\boxed{
\textbf{sparse entity graph}
+
\textbf{fixed inducing team slots}
+
\textbf{incremental set-roster AR scan}
}
]

其高层复杂度可以控制在：

[
O(NM+NK),
]

其中 (M) 是固定 team slots 数、(K) 是固定技能数；不会随着可能的 agent identity 数量扩张网络参数。

[1]: https://arxiv.org/abs/2205.14953 "Multi-Agent Reinforcement Learning is a Sequence Modeling Problem"
[2]: https://arxiv.org/abs/1703.06114?utm_source=chatgpt.com "Deep Sets"
[3]: https://arxiv.org/abs/1810.00825 "[1810.00825] Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks"
[4]: https://arxiv.org/abs/2006.04222?utm_source=chatgpt.com "Randomized Entity-wise Factorization for Multi-Agent Reinforcement Learning"
[5]: https://arxiv.org/abs/2203.05285 "[2203.05285] Breaking the Curse of Dimensionality in Multiagent State Space: A Unified Agent Permutation Framework"
[6]: https://arxiv.org/abs/2210.05448 "[2210.05448] A General Learning Framework for Open Ad Hoc Teamwork Using Graph-based Policy Learning"
