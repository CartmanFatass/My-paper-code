# **审阅结论：VALID FAIL — 退休 R31-CFEI；下一步只进入 R32-IFEPG**

我按完整提交 `b17404e7f1bab8866fc86d2bbc606fb22f22012a` 审阅了问题文件列出的 gate 脚本、R31 实现、环境、训练集成、原始结果 JSON 和失败复盘，而不是只采用摘要。该提交记录的是 “Record R31 causal gate failure”。

结论分成两部分：

1. **R31 的 matched-shuffle 近零判据在数学上不成立，`-2.068` 不能作为失败理由。**
2. **但 R31 仍是有效的科学 FAIL**：不依赖 posterior 或 shuffle 的直接 forced-skill M2 显示，技能间效应没有超过同技能随机执行变异。应按预注册约束退休 R31，不启动在线 reward，也不通过窗口、prior、posterior、epoch、bin 或阈值修改挽救它。

唯一下一路线是：

> **R32-IFEPG：Interventional Fixed-window Effect Policy Gradient**
> 直接用随机技能干预产生的、去随机噪声后的固定窗效应分离，更新低层 actor 的 skill-FiLM；不训练新 scorer，不生成 intrinsic reward，不修改 R30 high return。

---

## 1. R31 是否存在实现或比较器缺陷

### 1.1 干预和数据边界是有效的

原始结果确实满足注册的主要执行合同：

* 1,024 个自然窗口；
* 768 个 posterior 训练窗口，256 个 held-out 窗口；
* 128 个干预 context；
* 四个技能、每技能两个随机 replica，共 1,024 个 forced stochastic 窗口；
* 0 次 policy update；
* forced 窗口进入 posterior 训练的数量为 0；
* 未写出 gate-passed checkpoint。

自然数据按 reset group 划分训练和 held-out。在每个真正的 R30 check 后，先完成所有 `KEEP/SET`，再保存 post-edit skill roster、环境 snapshot 和低层 recurrent runtime，随后执行恰好 (W=10) 个 stochastic primitive steps。

forced branch 对每个技能都执行以下步骤：

1. 恢复完整 simulator snapshot；
2. 恢复 active skills、age、clock 以及 actor/critic recurrent states；
3. 只替换 focal agent 的技能；
4. 对同一个 replica，各技能使用相同随机种子；
5. 用当前 stochastic low actor 执行十步；
6. 不调用 policy update，也不把 forced 窗口用于 posterior 拟合。

环境 snapshot 包括位置、任务状态、窗口计数和 RNG state，恢复路径完整；R31 effect view 本身只暴露归一化智能体位置。

Alice–Bob 的 step dynamics 对给定 action 是确定性的，external reward 只有 simultaneous button/target collection event，没有 progress reward。

因此，没有发现会使 M2 无效的具体错误，例如：

* forced row 参与 scorer 训练；
* deterministic action 与 stochastic action混用；
* recurrent state未恢复；
* focal skill泄漏进 context；
* teammate skill发生变化；
* 不同 branch 从不同环境状态开始；
* 在线更新污染 frozen-policy gate。

### 1.2 R31 自然 posterior 也按设计实现

`FixedWindowEffectPosterior` 的两个 head 分别估计：

[
q_\phi(z_i\mid E_i,C_i),
\qquad
q_\psi(z_i\mid C_i).
]

输入在模块内再次 detach，而且没有 action、reward、agent ID、age、duration、phase 或 OPT feature。

其训练损失确实是两个独立 cross-entropy：

[
\mathcal L
==========

-\log q_\phi(z_i\mid E_i,C_i)
-\log q_\psi(z_i\mid C_i),
]

而报告的 residual 是：

[
\delta_{\rm CFEI}
=================

## \log q_\phi(z_i\mid E_i,C_i)

\log q_\psi(z_i\mid C_i).
]

窗口 effect 也与注册公式一致：

[
E_i=
\left[
\Delta x_i^{\rm end},
\Delta \bar x_{-i}^{\rm end},
\Delta x_i^{\rm late},
\Delta \bar x_{-i}^{\rm late}
\right],
]

context 只含 focal/teammate 起始位置和 teammate skill one-hot，不含 focal skill。

在线集成路径同样正确实现了“先用旧 posterior 评分，后做 low PPO，再更新 posterior”；`real_reward` 才会把 signed、detached、对称 clipping 的 endpoint reward 写入低层 rollout。

所以这不是一个 scorer 没训练好或 wiring 没接通的结果。

---

## 2. matched-shuffle 判据确实错误

当前 shuffle 将 donor effect 从相同 teammate roster、相邻起始位置 bin 的另一行取出，但仍用 receiver 的 context 和真实 skill label评分。

注册判据却要求：

[
\left|
\mathbb E[
\log q_\phi(Z\mid E^{\rm shuf},C)
---------------------------------

\log q_\psi(Z\mid C)
]
\right|
\approx0.
]

这是不正确的。

假设两个 posterior 都达到 Bayes 最优，而且理想 shuffle 满足：

[
E^{\rm shuf}\perp Z\mid C,
\qquad
E^{\rm shuf}\sim p(E\mid C).
]

那么：

[
\begin{aligned}
\mathbb E[\delta_{\rm shuf}\mid C]
&=
\mathbb E_{E^{\rm shuf}\mid C}
\sum_z p(z\mid C)
\log
\frac{p(z\mid E^{\rm shuf},C)}
{p(z\mid C)}
\
&=
--

\mathbb E_{E^{\rm shuf}\mid C}
D_{\rm KL}
\left(
p(Z\mid C)
\middle|
p(Z\mid E^{\rm shuf},C)
\right)
\
&\le0.
\end{aligned}
]

也就是说：

* shuffle 后的期望一般应当是**负数**；
* 它只有在 full posterior 完全忽略 (E)，即 (E) 不提供任何技能信息时才接近零；
* full posterior 越依赖真实 (E)，错误配对的 donor effect 越可能强烈反驳 receiver label，负值反而越大。

这里还不是精确 conditional randomization：代码只要求四个位置 bin 各相差不超过一，并非严格相同 (C)。因此 donor (E) 与 receiver (C) 可能形成训练分布外组合，更没有理由期待 residual 接近零。

所以：

> **`matched_shuffle = -2.068` 应重新解释为“错误配对 effect 会显著降低真实标签似然”的 disruption diagnostic，而不是 shortcut/null failure。**

当前 `_decide` 使用：

```python
abs(shuffle_mean) > 0.5 * natural_mean
```

触发 hard fail，这个逻辑应从科学判定中删除。

但**不需要重跑 R31**，因为直接 M2 已经独立失败。

---

## 3. 为什么 M2 仍构成有效 FAIL

M2 不读取 posterior，也不依赖上述 shuffle。

对每个 context、技能对 ((z,z'))，代码计算：

[
B_{zz'}
=======

\frac12
\left[
|E_z^{(1)}-E_{z'}^{(1)}|^2+
|E_z^{(2)}-E_{z'}^{(2)}|^2
\right],
]

[
W_{zz'}
=======

\frac12
\left[
|E_z^{(1)}-E_z^{(2)}|^2+
|E_{z'}^{(1)}-E_{z'}^{(2)}|^2
\right],
]

[
R_{zz'}=\frac{B_{zz'}}{W_{zz'}+\epsilon}.
]

结果是：

[
\operatorname{median}(R)=0.889613,
]

95% cluster interval：

[
[0.763227,;1.078315].
]

平均 between 与 within 几乎相同：

[
\bar B=0.112531,
\qquad
\bar W=0.103734.
]

skill-specific pooled ratio 为：

[
R_0=0.552,\quad
R_1=0.842,\quad
R_2=1.161,\quad
R_3=1.790.
]

因此，这个 frozen low actor 的技能差异主要不是一个 codebook-wide、稳定高于随机执行噪声的 persistent effect：

* 至少技能 0 和 1 的干预效果低于同技能 stochastic variability；
* 全局 median 低于 1；
* interval 下界明显低于 1；
* 预注册 PASS 要求是 median 至少 1.5、下界高于 1、每个技能 pooled ratio 高于 1。

skill 3 在自然 held-out 数据中只有 44 行，少于原定 64 行。这会使 M1 的 skill-wide 自然信息结论不完整，但不会改变 M2 的直接干预失败。M1 的 posterior full loss `0.488` 明显低于 context loss `1.083`，表明模型确实拟合了自然关联；问题不是 posterior capacity。

### M1 为什么高而 M2 失败

自然 held-out：

[
G_{\rm nat}=0.487866\ \text{nats},
]

并不证明技能有因果效应。

R31 context (C) 只含起始位置和 teammate skill。 但实际 R30 high policy 依据 centralized state、joint observations、OPT compact 和 working roster选择技能。 Alice–Bob observation 又包含 button/target offsets，centralized state包含 active task、clock phase、contacts和历史 occupancy。

因此存在未进入 (C) 的变量 (U)：

[
U\rightarrow Z_i,
\qquad
U\rightarrow E_i.
]

于是：

[
I_{\rm obs}(Z_i;E_i\mid C_i)>0
]

完全可能与：

[
E_i\not!\perp!!!\perp do(Z_i)\mid C_i
]

同时不成立。

这正是当前结果的机制签名：

> 自然未来移动能帮助识别 high policy 当时选择的技能，但把技能直接替换后，技能并没有 codebook-wide 地改变未来移动到超过 stochastic noise 的程度。

### 源 checkpoint 的范围限制

源 policy 是历史 64K shaped-run checkpoint，而 gate 在当前 collection-only 环境中运行。由于 gate 没有 policy update、effect 不读取 reward、环境 dynamics 未改变，这不会使 M2 的 frozen-policy干预比较无效；但它严格禁止把结果解释为“稀疏训练下 R31 失败”或“R30 无法探索”。历史 64K pair 本身只验证 temporal wiring，不是 sparse-exploration evidence。

---

## 4. R31 的退休范围与负约束

应将结果归档为：

```text
R31-CFEI: VALID_FAIL_M2
matched-shuffle hard gate: INVALID_NULL_DEFINITION
online reward: RETIRED
```

可复用的负约束是：

[
\boxed{
I_{\rm observational}(Z_i;E_i\mid C_i)>0
;\not\Rightarrow;
|\mathbb E[E_i\mid do(Z_i=z),C_i]
---------------------------------

\mathbb E[E_i\mid do(Z_i=z'),C_i]|^2

>

\text{stochastic execution variance}
}
]

因此永久退休：

* `log q_full - log q_context` 作为在线 reward；
* 只改变 coefficient、clip 或 normalization 的变体；
* 改变 (W) 的变体；
* 换 prior/context posterior 的变体；
* 增加 posterior depth、epochs、data bins 的变体；
* 修改 shuffle 阈值后重新尝试 reward；
* 用 forced rows训练相同 posterior。

该结论与仓库失败复盘的主要判断一致：自然 effect classification 是 association-dominated，不能在没有 intervention-level separation 时授权 reward。

保留为 **diagnostic-only**：

* 自然 (G_{\rm nat})；
* forced posterior residual；
* matched-shuffle disruption score；
* `FixedWindowEffectPosterior`；
* R29 action-information；
* legacy one-step `TransitionSkillDiscriminator`。

它们不得再写入 low reward。

---

# 5. 唯一下一路线：R32-IFEPG

## 5.1 下一条因果边

不再问：

> 自然 trajectory 能否被分类为某个技能？

而直接优化：

[
\boxed{
\text{randomized skill intervention}
\rightarrow
\text{noise-corrected persistent effect separation}
\rightarrow
\text{skill-FiLM policy change}
}
]

名称：

> **R32-IFEPG — Interventional Fixed-window Effect Policy Gradient**

它不是 R31 的 scorer 变体：

* 没有 posterior；
* 没有自然 observational log-ratio；
* 没有 intrinsic reward；
* 没有 null classifier；
* forced trajectories直接定义 actor auxiliary objective。

R30 的 fixed clock、`KEEP/SET`、high-check PPO 和 asynchronous lifetimes全部保留。

## 5.2 干预窗口

从一个自然 R30 decision snapshot (c) 开始，保存：

[
c=
(s_t,\mathbf o_t,\mathbf z_t,
\mathbf h^{actor}_t,
\mathbf h^{critic}_t,
\text{env snapshot}).
]

选择 focal agent (i)。对所有技能 (z\in{0,\ldots,K-1})，执行两个独立 stochastic replicas：

[
\tau_{c,z}^{(r)}
\sim
P_{\theta}^{i,z}
\otimes
P_{\bar\theta}^{-i,\mathbf z_{-i}},
\qquad
r\in{1,2}.
]

其中：

* focal 使用当前待训练 low actor，并强制 (z_i=z)；
* teammate skill 固定；
* teammate 使用本轮开始时冻结的 behavior actor；
* 环境和 recurrent state从同一 snapshot 恢复；
* 执行恰好 (W=k_0=10) 步；
* 训练 replica 在技能和 replica之间使用**独立随机流**；
* external reward不进入 score。

使用 R31 已实现的同一个八维、task-agnostic position effect：

[
E_{c,z}^{(r)}
=============

[\Delta x_i^{end},
\Delta \bar x_{-i}^{end},
\Delta x_i^{late},
\Delta \bar x_{-i}^{late}].
]

环境现有 `intrinsic_effect_view()` 和 snapshot/restore 可以直接复用。

## 5.3 无偏的 effect-separation estimator

对技能对 ((z,z'))，定义：

[
U_{c,zz'}
=========

\left\langle
E_{c,z}^{(1)}-E_{c,z'}^{(1)},
E_{c,z}^{(2)}-E_{c,z'}^{(2)}
\right\rangle.
]

因为两个 replica 独立：

[
\mathbb E[U_{c,zz'}]
====================

\left|
\mu_{c,z}-\mu_{c,z'}
\right|*2^2,
\qquad
\mu*{c,z}
=========

\mathbb E[E\mid c,do(z_i=z)].
]

随机执行方差不会作为正奖励项进入期望。

context score：

[
S_c
===

\frac{1}
{d_E {K\choose2}}
\sum_{z<z'}U_{c,zz'},
\qquad
d_E=8.
]

(S_c) 可以为负；不使用 `ReLU`。

## 5.4 策略梯度

设每个 branch 中 focal trajectory 的 old log-probability 为：

[
\ell^{old}_{c,z,r,t}.
]

对一批 (B) 个 context，用不包含本 context 的 leave-one-out baseline：

[
b_c
===

\frac1{B-1}
\sum_{c'\ne c}S_{c'},
]

[
A_c
===

\frac{S_c-b_c}
{\operatorname{std}*{c'\ne c}(S*{c'})+\epsilon}.
]

只对 focal actions构造 ratio：

[
\rho_{c,z,r,t}
==============

\exp
\left[
\log\pi_\theta
(a_{i,t}^{c,z,r}\mid o_{i,t}^{c,z,r},z,h_{i,t})
-----------------------------------------------

\ell^{old}_{c,z,r,t}
\right].
]

一次 PPO-clipped auxiliary update：

[
L_{\rm IFEPG}
=============

-\frac1{BKRW}
\sum_{c,z,r,t}
\min
\left[
\rho_{c,z,r,t}A_c,;
\operatorname{clip}(\rho_{c,z,r,t},0.9,1.1)A_c
\right].
]

* 一次 epoch；
* gradient norm clip `0.5`；
* 无 value loss；
* 无 GAE；
* 无 task reward；
* 无 entropy bonus；
* 无 high policy update。

## 5.5 只更新 skill-FiLM

当前 strict low actor 的结构是：

[
\operatorname{MLPBase}(o_i)
\rightarrow
\operatorname{skill\ FiLM}(z_i)
\rightarrow
\operatorname{RNN}
\rightarrow
\operatorname{ACTLayer}.
]

`actor_film` 从 skill one-hot 生成 ((\gamma_z,\beta_z))，而现有 actor optimizer同时包含 base、FiLM、RNN 和 action head。

R32 只允许梯度进入：

```python
low.actor_film.parameters()
```

以下全部冻结：

* actor base；
* actor RNN；
* action head；
* tanh-Gaussian log standard deviation；
* low critic；
* high editor/critic；
* OPT/bridge；
* R31/transition posterior。

这样：

* 不能通过增大 action variance 获利；
* 不能通过所有技能共同增加移动幅度获利；
* 更新必须经 skill-conditioned bottleneck；
* 与 R27 已验证的 FiLM conditional capacity直接对接。

如果 R32 后来通过机制 gate，其生产集成形式也应是：

> 每个普通 R30 update 前，从 shadow intervention branches 做一次 FiLM-only auxiliary update；它不是 rollout reward，永远不进入 high return。

---

## 6. 精确代码变更边界

### 新增 `ha_ctse_process/r32_interventional_effect_pg.py`

包含：

* `InterventionalContext`;
* `ForcedEffectBranch`;
* `effect_u_statistic`;
* leave-one-context advantage；
* focal PPO surrogate；
* parameter-drift metrics。

### 修改 `StrictHMASDMAPPOLowLevelPolicy`

在 `ha_ctse_process/standalone_agent.py` 增加：

```python
def film_update_parameters(self):
    return self.actor_film.parameters()
```

以及只重放 focal sequence、返回逐步 log-probability 的 helper。

不能改 low actor输入；仍是：

[
\pi_l(a_i\mid o_i,z_i).
]

### 新增 `scripts/r32_ifepg_gate.py`

负责：

* 自然 R30 context bank；
* env/policy snapshot；
* frozen teammate behavior copy；
  -独立 stochastic training branches；
* held-out common-random-number evaluator；
* probe/update 两臂；
* paired cluster bootstrap；
  -唯一结果 JSON。

### 修改 `ha_ctse_process/train.py`

`enforce_r31_contract` 应永久拒绝：

```text
r31_effect_mode=real_reward
```

R31 只保留 diagnostic/provenance 用途。

R32 gate 本身不进入正常 trainer。只有 gate PASS 后，才允许增加单个 `r32_ifepg_mode` active path。

### 保持不变

* `alice_bob_asymmetric_cycles.py` 的 sparse reward；
* R30 high controller；
* `HighCheckBuffer`；
* R30 lifetime机制；
* environment task字段；
* existing R31 result JSON。

---

# 7. 最小可证伪机制实验

## 7.1 Comparator

两臂从同一 frozen adaptive-R30 checkpoint 和同一 context bank开始：

```text
probe_only:
  收集完全相同的 forced branches
  计算完全相同的 S_c
  不更新参数

real_update:
  收集完全相同的 forced branches
  只更新 low.actor_film
```

不是 shared-(k) versus R30，也不是 intrinsic-on versus task baseline。

该实验只测试：

[
\text{IFEPG 是否能创造并运输 persistent skill effects}.
]

不测试任务收益。

## 7.2 暴露和计算

```text
source context bank:    256 natural R30 decision contexts
held-out contexts:      128
focal agents:           balanced
auxiliary updates:      20
contexts/update:        32
skills/context:         4
replicas/skill:         2
window:                 10
PPO epochs/update:      1
clip:                   0.10
grad clip:              0.5
paired seed:            32031
```

每臂训练 shadow steps：

[
20\times32\times4\times2\times10
================================

51{,}200.
]

held-out forced evaluation：

[
128\times4\times2\times10
=========================

10{,}240
]

steps/arm。

另外每臂运行 64 个 stochastic、80-step natural Alice–Bob episodes，共 5,120 steps，用于 transport，不做 task PPO。

总计约 66K shadow/natural steps/arm。

训练 branches使用独立随机流；最终 M1 evaluator才使用与 R31 M2 相同的 cross-skill common random numbers。

---

## 7.3 四项决策指标

### **M0 — 实现有效性**

必须全部满足：

[
\max|\log p_{\rm replay}-\log p_{\rm stored}|
\le10^{-5}.
]

* branch/context/skill/replica 数量精确；
* probe arm 的 FiLM parameter drift (\le10^{-8})；
* real arm 的 FiLM relative (L_2) drift (>10^{-6}) 且有限；
* real arm 除 `actor_film` 外所有参数 drift (\le10^{-8})；
* 无 low critic、high policy、posterior或environment reward update。

失败：**INVALID**，只允许修实现，不评价算法。

### **M1 — 直接因果效应 SNR**

在 128 个 held-out context上：

[
\operatorname{median}R_{\rm real}\ge1.5,
\qquad
CI^{95%}_{lower}>1.0.
]

同时：

[
\operatorname{median}
(R_{\rm real}-R_{\rm probe})
\ge0.40,
\qquad
CI^{95%}_{lower}>0,
]

并且每个技能的 pooled ratio：

[
R_z>1.0.
]

### **M2 — 不是 stochastic-noise pathology**

要求：

[
\frac{\bar B_{\rm real}}
{\bar B_{\rm probe}}
\ge1.50,
]

paired-context difference 的 95% lower bound (>0)，且：

[
\frac{\bar W_{\rm real}}
{\bar W_{\rm probe}}
\le1.25.
]

也就是说，ratio 必须通过增大 between-skill persistent effect，而不是改变或放大同技能随机噪声。

### **M3 — 自然执行 transport 与 R30 安全**

将两个智能体的 (x,y) 位置各分成五个固定 bins，形成：

[
5^4=625
]

个 task-agnostic joint-position cells。

要求：

[
\frac{
Coverage_{\rm real}
}{
Coverage_{\rm probe}
}
\ge1.10,
]

paired-reset cluster bootstrap 的 coverage difference 95% lower bound (>0)。

同时保持：

[
full_sync_SET_rate\le0.50,
]

[
H(Z\mid SET)/\log K\ge0.80,
]

[
\min
\left[
P(T>4k_0),
P(T\le4k_0)
\right]
\ge0.05.
]

collection、button contact、target contact 和 sparse task reward只记录为 diagnostic，不参与 PASS。

---

## 7.4 唯一分支解释

### PASS

只有 M0 有效且 M1–M3 全部通过，才支持：

> IFEPG 可以在自然 R30 contexts上创造超过随机执行噪声的 persistent skill effects，并运输为更广的自然 joint-state visitation，而不破坏 asynchronous lifetime机制。

此时唯一授权动作是：在**重新从无环境 shaping 的 sparse source开始**的 R30 training中加入 FiLM-only IFEPG auxiliary step。

### FAIL — M1

如果 causal ratio 不提高或任一技能仍低于 1：

> 永久退休 direct interventional FiLM-effect policy-gradient路线。

不得改 coefficient、window、replica 数、effect posterior或阈值。

### FAIL — M2

如果 ratio 主要通过 within-noise变化得到：

> 退休为 stochastic/noise exploitation。

### FAIL — M3

如果 forced effect通过但自然 coverage不提高：

> 退休为 forced-only capacity；这会复现 R27 的边界，而不是解决 natural use。

如果 R30 lifetime或switch-skill supply坍缩，同样退休。

该完整预算没有 UNDERPOWERED 分支；除 M0 实现无效外，任何未满足均为算法 FAIL。

---

# 8. 允许与禁止的结论

## 当前 R31 结果允许支持

* R31 posterior真实学会了自然 trajectory association；
* 该 association没有通过直接 forced-skill persistence gate；
* R31 observational effect-information reward不得上线；
* matched-shuffle 的绝对近零判据错误，但不改变 M2 失败；
* R30 temporal controller不因本结果被否定。

## 当前结果禁止支持

* “技能完全没有因果效应”；
* “R30 variable lifetime无效”；
* “稀疏探索已失败”；
* “合作无法形成”；
* “HMASD parity不可能”；
* “S7 不能迁移”。

## R32 gate 即使 PASS，也仍禁止支持

* cooperation；
* task improvement；
* HMASD reconstruction；
* asynchronous lifetime superiority；
* S7 transfer；
* human-interpretable button/target skill semantics。

R32 PASS 最多证明：

[
\boxed{
\text{直接随机干预目标}
\rightarrow
\text{persistent task-generic skill effect}
\rightarrow
\text{自然 state-coverage transport}
}
]

从个体 persistent effect 到 complementary team composition 和 sparse cooperative usefulness，仍是后续独立因果边。

