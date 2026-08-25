你判断到的是**结构性矛盾**，不只是“时长候选设置不好”。更准确的重构应当是：

> **固定全局检查时钟 (k_0)，不再把技能长度作为高层离散动作；每个智能体的实际技能寿命 (T_i) 由连续的 `KEEP` 决策产生。**

也就是把“非固定 (k)”改写为：

[
\boxed{\text{fixed check clock } k_0 \quad+\quad \text{variable run length } T_i}
]

而不是同时学习 ((z_i,d_i))。

## 1. 当前设计为什么同时破坏三个性质

当前高层实际上是

[
\pi_H(z_i,d_i\mid x_i)
======================

\pi_z(z_i\mid x_i)\pi_d(d_i\mid x_i),
]

技能和时长由两个独立 categorical head 采样，log-prob 相加；只有 duration 到期的智能体才进入自回归选择循环。虽然网络只输出 (K+D) 个 logits，而不是显式输出 (KD) 个 logits，但有效行为组合仍是每个智能体 (K\times D)，多智能体联合组合则是 ((KD)^N)。更重要的是，每一个 ((z,d)) 组合都需要独立的访问和信用证据。当前实现可见于 [`SkillDurationPolicy` 和 expired-agent AR loop](sandbox:/mnt/data/hmasd_design_context/original/ha_ctse_process/standalone_agent.py)，尤其是约 920–1135 行和 3025–3199 行。

这带来三个问题。

第一，**它不是完整的 MAT 式联合顺序决策**。当前只有到期智能体产生新动作，未到期智能体只是 roster 条件，不是本检查点的策略动作，因此没有对应的 policy ratio 和 advantage。随着异步寿命展开，同一检查点通常只有一两个智能体更新，自回归前缀退化成稀疏子集。

第二，**短技能天然得到更多高层训练样本**。长度为 (d) 的技能在相同环境时间内大约产生 (1/d) 倍的高层 segment 数。因此即使 SMDP return 正确，短时长仍会在 minibatch 中被更高频地更新。这是对短技能的隐性优化偏置。

第三，**时长与技能共同选择，使时长成为技能语义的替代编码**。模型可能学习“技能 0 总是短、技能 1 总是长”，而不是让两个技能产生不同的闭环行为。项目背景里已经将这一点概括为“用于解耦的 duration，反而成为 entangling device”。参见 [研究背景](sandbox:/mnt/data/hmasd_design_context/prior_review/RESEARCH_BACKGROUND.md)。

MAT 的关键不是简单地“循环采样智能体”，而是把一个完整联合动作表示成按智能体分解的条件序列，使联合搜索从乘法规模变成各智能体动作空间之和，并用前序动作条件化后序动作。([arXiv][1]) 当前异步 expired-only 选择没有形成这样一个固定维度的联合高层动作。

---

## 2. 推荐结构：固定检查格上的自回归技能编辑

我建议把高层动作改成一个**技能编辑 token**：

[
e_{i,\tau}
\in
\mathcal E_i(z^-_{i,\tau})
==========================

{\texttt{KEEP}}
\cup
{\texttt{SET}(z):z\neq z^-_{i,\tau}}.
]

其中：

* `KEEP`：继续执行当前技能；
* `SET(z)`：切换为技能 (z)；
* `SET(current_skill)` 被 mask，因为它与 `KEEP` 重复，却会人为重置年龄。

因此在已有 (K) 个技能时，每个智能体仍然只有：

[
1+(K-1)=K
]

个高层选择，而不是 (KD) 个有效技能—时长组合。技能寿命可以一直延伸到 episode horizon，却不需要增加任何 duration category。

在每个固定检查点 (\tau)，所有智能体都参加一次顺序决策。令 (\sigma_\tau) 为本检查点存储下来的智能体顺序：

[
\pi_H(\mathbf e_\tau\mid x_\tau)
================================

\prod_{j=1}^{N}
\pi_H
\left(
e_{\sigma_\tau(j),\tau}
\mid
x_\tau,
e_{\sigma_\tau(1:j-1),\tau}
\right).
]

这里的 (x_\tau) 包含：

[
x_\tau=
\left(
s_\tau,\mathbf o_\tau,
\mathbf z^-*\tau,
\mathbf{age}*\tau,
c_\tau
\right),
]

但低层策略仍保持：

[
a_{i,t}\sim\pi_l(a_{i,t}\mid o_{i,t},z_{i,\tau}).
]

### 关键实现语义：前缀应是“编辑后的技能 roster”

不要只把 `KEEP/SET` token 计数放进前缀。每生成一个智能体的动作，就立即更新工作 roster：

[
\mathbf z_\tau^{(j)}
====================

\operatorname{Apply}
\left(
\mathbf z_\tau^{(j-1)},
e_{\sigma_\tau(j),\tau}
\right).
]

后续智能体看到的是：

* 前面智能体刚刚保留或切换后的技能；
* 后面尚未处理智能体原有的活跃技能；
* 所有智能体的年龄或持续信息。

因此，后序智能体可以做出类似：

> “前两个智能体继续 relay-like 技能，因此我切换到 tracking-like 技能”

这样的互补选择。

这恢复了 HMASD/MAT 自回归协调最重要的归纳偏置，同时又不要求所有智能体同步更换技能。同步的是**检查和编辑决策**，异步的是**实际技能更新和寿命**。

伪代码是：

```text
every k0 primitive steps:
    working_roster = active_skills
    order = stored permutation of all agents

    for i in order:
        e_i ~ high_policy(global_context, working_roster, ages, previous edits)

        if e_i == KEEP:
            working_roster[i] remains unchanged
        else:
            working_roster[i] = selected new skill
            age[i] = 0

    active_skills = working_roster
    execute pi_l(a_i | o_i, active_skills[i]) for k0 steps
```

这也是完全事件驱动异步与 MAT 顺序联合更新之间的合理折中：

* 任意时刻异步 termination：没有固定维度的联合动作，MAT 分解很难直接成立；
* 固定 (k_0) 检查格、独立 `KEEP/SET`：每个检查点都有完整 (N)-agent 联合编辑动作。

---

## 3. 高层 PPO 应回到固定检查步，而不是变量 segment 步

每个检查块形成一个固定时长的高层 transition：

[
R_\tau^H
========

\sum_{r=0}^{k_0-1}
\gamma^r r_{\tau k_0+r}^{env},
\qquad
\Gamma=\gamma^{k_0}.
]

高层 TD residual 为：

[
\delta_\tau^H
=============

R_\tau^H
+
\Gamma V_H(x_{\tau+1})
----------------------

V_H(x_\tau).
]

然后在这个固定检查序列上计算高层 GAE。

对每一个自回归 token 使用：

[
\rho_{\tau,j}
=============

\frac{
\pi_\theta(e_{\sigma(j),\tau}\mid x_\tau,e_{\sigma(<j),\tau})
}{
\pi_{\mathrm{old}}(e_{\sigma(j),\tau}\mid x_\tau,e_{\sigma(<j),\tau})
},
]

以及共享的 joint high-level advantage：

[
L_H
===

-\mathbb E_{\tau,j}
\left[
\min
\left(
\rho_{\tau,j}A_\tau^H,
\operatorname{clip}(\rho_{\tau,j},1-\epsilon,1+\epsilon)A_\tau^H
\right)
\right].
]

训练时可以像 MAT 一样，用存储的完整 token 序列做 teacher forcing，并行计算所有 token 的概率；执行时再自回归生成。MAT 本身也正是利用已收集动作，在训练阶段并行计算自回归条件概率。([arXiv][1])

这恢复的是 MAT 的顺序联合决策结构和 additive factorization；由于这里仍然使用近似 PPO、共享网络、部分可观测状态以及高层 SMDP，不能直接宣称继承其完整单调改进定理。

---

## 4. 为什么它更容易让长任务学到长技能

实际寿命成为 `KEEP` 的游程长度。设第 (m) 个检查点继续当前技能的概率为 (p_{i,m}^{keep})，则：

[
P(T_i=m k_0)
============

\left[
\prod_{\ell=1}^{m-1}p_{i,\ell}^{keep}
\right]
\left(1-p_{i,m}^{keep}\right).
]

这有三个直接优势。

### 每一个延长决策都有局部信用

原来的 40-step duration 是在技能开始时一次性选择，之后要等待很长时间才能知道是否正确。新结构中，每个 (k_0) 块都会重新得到：

[
A_\tau^H(\texttt{KEEP})
\quad\text{和}\quad
A_\tau^H(\texttt{SET}(z)).
]

如果稳定执行当前技能持续提高未来任务价值，`KEEP` 会在每个检查点获得连续的正优势，逐渐使：

[
p^{keep}\rightarrow 1.
]

不再需要先访问足够多的 `(skill=2, duration=40)` 样本才能学到长时长。

### 消除短 duration 的样本频率优势

所有智能体每个检查块都有一个高层 token。长技能不再意味着“高层样本更少”，而是表现为一串 `KEEP` 样本。因此高层梯度按环境时间而不是按 segment 数计权。

### 不再需要 duration entropy floor

当前 duration entropy floor 与“收敛到长技能”目标实际上冲突。它要求广泛使用多个 duration category，即使任务已经明确偏好长期稳定技能。

新设计中应当：

* 删除 duration head；
* 删除 duration entropy floor；
* 不给 `KEEP/SWITCH` 二元变量长期 entropy bonus；
* 只对“发生切换时的新技能分布”保留技能 entropy 或 balance pressure。

不要加入显式的 (+\beta T_i) 长度奖励。那会把“有用的长期技能”错误地替换成“无条件地不切换”。正确做法是去掉短时长偏置，让环境任务优势决定是否继续。

### 一个无需 sweep 的初始化

若原 duration 候选为均匀的 ({1,2,3,4}) 个检查块，则平均寿命是 (2.5) 个块。可以用无界 geometric continuation 初始化：

[
p_{\mathrm{keep}}^{(0)}
=======================

# 1-\frac{1}{2.5}

0.6.
]

这保持相同的初始平均寿命，同时允许自然产生超过 4 个块的长技能。之后 (p_{\mathrm{keep}}) 完全由学习改变，不需要增加新的 duration 超参数或候选集合。

---

## 5. 如何保留 HMASD 的技能区分动力

必须把“是否继续”和“选择哪个技能”严格分开：

[
P(e_i)
======

\begin{cases}
p_i^{keep},
&
e_i=\texttt{KEEP},
[4pt]
(1-p_i^{keep})
\pi_i^z(z\mid\texttt{SWITCH},\text{prefix}),
&
e_i=\texttt{SET}(z).
\end{cases}
]

对应 log-prob 为：

[
\log P(e_i)
===========

\mathbf 1_{\mathrm{keep}}\log p_i^{keep}
+
\mathbf 1_{\mathrm{switch}}
\left[
\log(1-p_i^{keep})
+
\log\pi_i^z(z)
\right].
]

技能熵只作用于：

[
H_z^{cond}
==========

(1-p_i^{keep})
H!\left(\pi_i^z(\cdot\mid\texttt{SWITCH})\right).
]

这样可以同时出现：

* 很高的 `KEEP` 概率，即很长的技能寿命；
* 切换发生时，仍有充分的技能覆盖和技能间竞争。

但需要明确：

> **conditional skill entropy 只能防止标签使用坍缩，不能单独逼出行为语义。**

真正的 HMASD-like 语义压力仍必须是一个**skill-only、duration-blind、固定窗口**的低层目标。其接口应被限定为：

[
r_{\tau,i}^{sem}
================

F\left(
\xi_{\tau:\tau+W,i},
z_{\tau,i}
\right),
\qquad W=k_0,
]

并满足：

* 所有样本窗口长度严格相同；
* (F) 不访问 duration、age、agent ID 或环境任务奖励；
* 同一个 (z) 在不同寿命下使用同一个语义目标；
* 只进入低层 reward/GAE；
* 不进入高层 `KEEP/SET` return，防止长技能通过重复收集 intrinsic reward 获益；
* 目标必须反映固定窗口内的闭环行为效果，而不是同状态动作均值分离。

R29-T10 的结果已经表明：即使分离完全来自 action mean，而不是 variance，仍可能降低自然过程区分和任务表现。因此不能再用 actor-density separation 充当这个语义项。参见 [R29-T10 pair result](sandbox:/mnt/data/hmasd_design_context/results/r29_t10_pair.json)。

同样，当前证据也不支持直接恢复原始 (q_d/q_D)。这里“保留 HMASD 的区分动力”应理解为保留以下结构：

[
\text{balanced skill supply}
\rightarrow
\text{skill-conditioned low-level bottleneck}
\rightarrow
\text{fixed-window behavior/effect differentiation}
]

而不是重新启用已经出现 shortcut/collapse 的特定分类器。

## 结论

最关键的一刀不是缩小 duration 候选集，而是：

[
\boxed{
(z_i,d_i)
\quad\longrightarrow\quad
\texttt{KEEP}\ \text{or}\ \texttt{SET}(z_i)
}
]

这一个变化同时实现：

1. 固定 (k_0) 上的完整 MAT 式顺序联合决策；
2. 将每智能体有效高层分支从 (KD) 降到 (K)；
3. 消除短技能的 segment-frequency 优势；
4. 让长技能通过连续正 `KEEP` advantage 自然形成；
5. 将 duration 从技能语义中彻底剥离；
6. 保留 (\pi_l(a_i\mid o_i,z_i))；
7. 使以后合格的 HMASD-like 语义目标能够在固定窗口上训练，而不再被长度 shortcut 污染。

这应当是下一版高层控制结构，而不是继续扩大 duration 集、调整 duration entropy，或给 R29 再换一个时间聚合方式。

[1]: https://arxiv.org/abs/2205.14953 "Multi-Agent Reinforcement Learning is a Sequence Modeling Problem"
