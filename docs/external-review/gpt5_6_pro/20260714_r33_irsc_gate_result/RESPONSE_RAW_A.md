# 1. 明确裁决

## **R33-IRSC：VALID SCIENTIFIC FAIL，永久退休**

没有发现会改变注册 estimand、随机化分布、完整 roster 概率、梯度范围或结果解释的具体 M0 缺陷。应执行预注册分支：

```text
FAIL_M1_RETIRE_R33_IRSC
```

永久退休：

* direct intervention-scored roster-complementarity selection；
  -同一 residualized role-swap score 的 reward、critic target 或 longer-run 版本；
* temperature、更多更新、score clipping、另一种 pair permutation、扩种子或改阈值；
  -通过更新 KEEP head、shared trunk、low actor、引入新 team latent、(q_D) 或 team reward 来“补救 R33”。

## **唯一下一路线：R34-BHMD**

# **Balanced Hindsight Mode Distillation**

# **平衡式事后行为模式蒸馏**

下一条因果边是：

[
\boxed{
\text{自然、无标签的交互轨迹模式}
\rightarrow
\text{平衡事后技能标签}
\rightarrow
\text{技能条件序列蒸馏}
\rightarrow
\text{可干预复现的技能模式}
\rightarrow
\text{未修改 R30 下的自然使用与探索}
}
]

决定性转向是：

> 不再假定当前 (z) 标签已经对应有意义的 primitive，然后继续为这些标签拟合 action、effect 或 roster score；改为先从行为轨迹中发现可重复模式，再把这些模式蒸馏进 (z)。

这不是另一种 R31 classifier，不是 R32 effect gradient，也不是 R33 high-head roster fitting。

---

# 2. R33 有效性审计

## 2.1 修正后的 estimand 数学上成立

实现先对每个 agent 和 replica 的完整 (K\times K) roster-effect table 做两向中心化：

[
\widetilde E_i^q(a,b)
=====================

E_i^q(a,b)
-\overline E_i^q(a,\cdot)
-\overline E_i^q(\cdot,b)
+\overline E_i^q(\cdot,\cdot).
]

代码的 row mean、column mean 和 grand mean 保留 replica、agent 和 effect 维度，因此确实是分别对每个 agent/replica 清除两个 roster 轴的 additive main effects。

在独立执行模型

[
E_1(a,b)=f_1(a)+u_1(b),\qquad
E_2(a,b)=u_2(a)+f_2(b)
]

下，两向残差严格为零。因此原始角色、agent identity、单个技能的自身效应以及 teammate skill 的纯加性效应不能产生 R33 分数。这正是上一轮 disposition 要求的估计器修正。

实现随后计算：

[
\widetilde g_{ab}^q
===================

\widetilde E_1^q(a,b)-\widetilde E_2^q(a,b),
]

[
h_{ab}^q
========

\frac12(\widetilde g_{ab}^q-\widetilde g_{ba}^q),
\qquad
k_{ab}^q
========

\frac12(\widetilde g_{ab}^q+\widetilde g_{ba}^q),
]

以及

[
\widetilde C_{ab}
=================

\frac14
\left[
\langle h_{ab}^{1},h_{ab}^{2}\rangle
------------------------------------

\langle k_{ab}^{1},k_{ab}^{2}\rangle
\right].
]

代码与该定义完全一致。

由两个独立 replica 可得：

[
\mathbb E[\widetilde C_{ab}]
============================

\frac14
\left(
|\mathbb E[h_{ab}]|^2
---------------------

|\mathbb E[k_{ab}]|^2
\right).
]

因此：

* 稳定的角色交换 sign reversal：(h\neq0,k\approx0)，得正分；
* 两个 orientation 同方向变化：(h\approx0,k\neq0)，得负分；
* 只有一个 orientation 有效：(h=k)，两项抵消；
  -纯 additive execution：两向 residual 均为零。

它是一个窄而合理的 **stable non-additive role-swap estimand**，不是普通的“两个技能移动方向不同”。

## 2.2 共享随机化有效

每个自然 R30 context 上枚举全部 16 个 final rosters。每个 branch 都恢复：

* 完整 simulator snapshot；
* low recurrent states；
* active runtime；
  -相同起始 observation/state；
  -指定 complete roster。

同一个 context/replica 下，16 个 roster 使用相同 branch seed；两个 replica 使用不同 seed，且所有 context-replica 流唯一。

这种设计使 roster 间比较使用 common random numbers，同时让 cross-replica inner product 具有独立随机重复。

一个细节是 forced roster 后没有把发生技能变化的 `skill_age` 设为零。但 low actor 不读取 age，branch 内也不再次调用 high policy；age 只随 runtime snapshot 被携带。因此它不改变本轮物理轨迹 estimand，不构成 M0 缺陷。

## 2.3 完整 roster 概率是精确的

对于每个 final roster，代码把它唯一映射为：

[
e_i(r_i)=
\begin{cases}
\texttt{KEEP},&r_i=z_i^{-}\text{ 且 agent active},\
\texttt{SET}(r_i),&\text{其他情况}.
\end{cases}
]

然后使用现有 R30 `evaluate_sequence`，逐 token 重建 working roster，并把两个 token log-probability 相加。

注册结果中的最大概率和误差是：

[
2.384\times10^{-7},
]

低于 (10^{-6})。自然执行 token 的 replay error 为零。原始 JSON 也记录所有 probability/replay M0 检查通过。

所以本轮不是 approximate candidate pruning 或遗漏 roster 导致的负结果。

## 2.4 exact-expectation gradient 正确落在 skill head

目标是：

[
L_{\mathrm{IRSC}}
=================

-\frac1B
\sum_c
\sum_r
\pi_\theta(r\mid c)
\operatorname{stopgrad}[A_c(r)].
]

实现没有采样 roster，也没有使用 PPO ratio，而是直接枚举完整联合分布后计算期望。score 被 detach。

运行前，所有模块参数都被关闭梯度，只重新打开：

```text
high.skill_head.weight
high.skill_head.bias
```

训练时检查任意 non-head gradient；八次更新后再次检查参数漂移及 stored-prefix KEEP probability。

结果显示：

* real selected-head relative drift `0.027634`；
* sham selected-head relative drift `0.026423`；
* non-head gradient 和 drift 为零；
* KEEP probability drift 为零；
* low、critic、posterior、normal high PPO、task-reward objective 更新全部为零。

这不是 zero wiring、梯度没有到达参数或 sham 获得额外更新的问题。

## 2.5 pair-sham 是合格的注册 comparator

unordered pair 的顺序为：

```text
01, 02, 03, 12, 13, 23
```

source permutation：

```text
[5, 4, 3, 2, 1, 0]
```

对应：

```text
01 <-> 23
02 <-> 13
03 <-> 12
```

每个映射都不共享任何技能 identity。

`standardized_roster_scores` 将 pair score 同时放入两个 orientation，diagonal 为零，再做完整 16-roster 标准化。real 与 sham 因此拥有相同的 signed score multiset。

pair-sham **不保证参数梯度范数逐步相等**。这不构成无效性：

* comparator 的问题是“正确 pair attribution 是否比无技能重叠的 attribution 更能泛化到 heldout true score”；
  -它不声称是相同梯度方向或相同 Fisher geometry 的 null；
  -两臂具有相同 score 数值集合、上下文、参数初始化、更新次数及可训练参数；
  -实际 head drift 也非常接近。

因此，gradient-norm 不严格匹配是 comparator 的已声明限制，不是可推翻 M0 的错误。

## 2.6 M0 规则修正合理

R33 没有要求 selected head 必须漂移超过某个阈值。若真实 complementarity score 恰好为零，则 exact zero gradient 本身应该进入 M1 失败，而不是被错误归类为实现无效。上一轮 disposition 已明确修正这一点。

本次实际上八次更新均有有限、非零 head gradient，因此连这一边界情况也没有触发。

---

# 3. R33 的有效科学失败

M1 的两个 registered quantities 都是正值：

[
\Delta V_{\rm true}
===================

0.00195497,
\qquad
CI_{95%}
========

[0.00074433,0.00310530],
]

[
\Delta P_{\rm top2}
===================

0.00125035,
\qquad
CI_{95%}
========

[0.00051950,0.00190764].
]

但 material gates 分别为 `0.20` 和 `0.10`。换言之：

* expected true-score alignment 只有 gate 的约 `0.98%`；
* top-pair probability mass gain 只有 gate 的约 `1.25%`。

同时 head 已移动约 2.6%–2.8%，所以不能把结果解释为“再多做几次更新就好”。

原始 heldout residual pair scores多数只有约 (10^{-8})–(10^{-7}) 量级，并有正有负。标准化已经消除了绝对尺度，最终仍只有极小的 heldout mapping gain，说明真正缺失的是**跨 context 稳定 pair ordering**，而不只是 raw score 太小。

自然 transport 也反向：

[
Coverage_{\rm real}=427,\qquad
Coverage_{\rm sham}=429,
]

[
\frac{Coverage_{\rm real}}{Coverage_{\rm sham}}
===============================================

0.995338,
]

[
\frac{D_{\rm real}}{D_{\rm sham}}
=================================

0.984925.
]

两个 paired-reset interval 都没有正下界。

但 R30 safety 全部通过：

[
full\text{-}sync\ SET=0.185268,
]

[
H(Z\mid SET)/\log4=0.997333,
]

[
\min_zP(Z=z\mid SET)=0.216,
]

[
lifetime\ breadth=0.081841.
]

因此失败位置清晰：

```text
不是实现
不是随机化
不是概率归一化
不是梯度 wiring
不是 skill supply
不是同步刷新坍缩
不是 lifetime 坍缩

而是：
当前 codebook 不包含可跨 context 泛化的、物质性非加性互动 primitive
```

---

# 4. 可复用的因果结论

R29–R33 的联合结论是：

[
\boxed{
\text{选择、分类或放大一个既定技能标签}
\text{，不能替代技能模式本身的形成}
}
]

具体地：

1. action density 可以区分，但不产生稳定 effect；
   2.自然 effect 可以预测标签，但不具有 causal persistence；
   3.直接推动 individual effect 只产生很小 shift；
   4.精确重加权 complete roster 只能学到极小的正确 pair attribution，不能制造不存在的 pair semantics。

仓库的 cross-round failure matrix 已将 R33 概括为：

> existing complete roster → stable non-additive role swap → high selection → natural coverage 这一链路失败；现有 codebook 没有已证明的 material selectable team interaction。

最重要的新约束是：

> **Selection is downstream of semantics.**
> 即使联合概率计算完全精确，若 (z) 本身不是可重复行为模式，调整 high skill logits 只是在重新排列 context-specific noise。

这不否定：

* R30 固定检查、异步 lifetime；
  -离散 skill bottleneck 本身；
  -原始 HMASD 可能形成的有效技能；
  -其他代码本或其他训练来源。

它否定的是：

> 继续把当前 Alice–Bob checkpoint 的四个 (z) 当作已有 primitive，并为它们寻找另一个 score、reward、pair mapping 或 selector。

---

# 5. 唯一下一路线：R34-BHMD

## 5.1 为什么选择 mode distillation

当前路线一直采用：

```text
先有标签 z
-> 再问标签是否对应 action/effect/complementarity
```

R34 反转方向：

```text
先从无标签轨迹中找到重复行为模式
-> 再让 z 复现这些模式
```

它解决的是 codebook construction，而不是 codebook scoring。

这也符合研究原则中的因果顺序：必须先有 persistent executable behavior，之后才有 team assignment、joint effect 和 reward usefulness。

## 5.2 自然数据语义

从 frozen R30 policy 的自然 stochastic rollout 中，对每个真实 (W=k_0) block 和每个 focal agent (i) 构造：

[
y_{c,i}
=======

\operatorname{vec}
\left[
\left{
x_{i,t+r}-x_{i,t}
\right}*{r=1}^{W},
\left{
\bar x*{-i,t+r}-\bar x_{-i,t}
\right}_{r=1}^{W}
\right].
]

Alice–Bob 中：

[
x_i=\frac{\text{agent position}_i}{\text{world size}}.
]

因此 (y_{c,i}\in\mathbb R^{4W})。

descriptor：

* 包含 focal 与 teammate 的完整相对位移过程；
  -不含起始绝对位置；
  -不含旧 skill label；
  -不含 action；
  -不含 reward；
  -不含 button、target、contact、phase；
  -不含 agent ID、age、duration 或 OPT compact。

同一 descriptor 函数对两个 agent 共用，因此 prototype 表示的是 **focal-relative interaction role**，不是 Alice/Bob identity。

所有维度只用 train split 的均值和标准差标准化，随后冻结。

## 5.3 平衡模式发现

在 train descriptors 上解：

[
\min_{{c_z},P}
\sum_{n=1}^{N}
\sum_{z=1}^{K}
P_{nz}
|\widehat y_n-c_z|_2^2,
]

约束：

[
P\mathbf1_K=\mathbf1_N,
]

[
P^\top\mathbf1_N
================

\frac{N}{K}\mathbf1_K.
]

第一版固定：

[
K=4.
]

使用确定性 balanced assignment；最终 hard label：

[
z_n^\star=\arg\max_zP_{nz}.
]

每个 prototype 必须获得完全相同的 train sample 数。这里不存在 (K) sweep。

然后仅为保持当前 R30 high-policy compatibility，使用一次 Hungarian matching，把 prototype index 与 source rollout 中原来的数值 skill label 做最大重叠匹配：

[
\sigma^\star
============

\arg\max_\sigma
\sum_n
\mathbf1[
\sigma(z_n^\star)=z_n^{old}
].
]

这一操作只重新命名 prototypes，不影响聚类，也不以旧 (z) 定义 mode。

## 5.4 行为蒸馏目标

对每个训练序列保存：

* observation sequence；
* executed action sequence；
* block-start actor recurrent state；
* mask；
* hindsight mode label (z^\star)。

用现有 recurrent low actor 计算：

[
L_{\rm BHMD}
============

-\frac{1}{N W}
\sum_{n,t}
\log
\pi_{\theta_l}
\left(
a_{n,t}
\mid
o_{n,t},
z_n^\star,
h_{n,t}
\right).
]

这是 sequence behavior distillation，不是 skill classifier：

-不训练 (q(z\mid\tau))；
-不把 score 变成 reward；
-不从 posterior 反推 intrinsic advantage；
-没有 counterfactual effect magnitude objective；
-没有 task reward、value 或 GAE。

训练标签和 prototypes 全部 detach。

### Gradient recipients

只允许：

```text
low.actor_film
low.actor_rnn
low.actor_act.action_out.fc_mean
```

冻结：

```text
low.actor_base
low actor log-std
low critic 全部
R30 high actor / keep_head / skill_head / shared trunk
HighCheckValue
OPT / bridge
R29 / R31 / R32 / R33 modules
所有 posterior / classifier
environment
```

允许 recurrent dynamics 和 action mean 改变，是因为本轮目标是**形成模式**；R32 只改 FiLM 且优化 individual effect magnitude，属于不同因果边。R34 不得被解释成扩大 R32 parameter scope。

## 5.5 机制匹配 sham

两臂使用相同：

* source trajectories；
* prototypes；
* prototype-to-old-(z) Hungarian mapping；
* optimizer；
* minibatches；
  -更新次数；
  -参数范围。

### `real_modes`

使用每条 trajectory 的真实 balanced mode label。

### `episode_sequence_sham`

对每个 focal-agent channel，把一个完整八-block label sequence 分配给另一个 train episode：

```text
episode e <- labels from episode (e+1) mod E
```

两个 focal-agent channel 分别执行，无 self donor。

这样 sham 精确保留：

* 每个技能的样本数；
  -每个 focal-agent 的技能数；
  -所有八-block label sequence 的 multiset；
* KEEP/SET run-length multiset；
  -标签 entropy；
  -每次更新的 loss 规模和模型容量。

它只破坏：

[
\text{trajectory/action/context}
\leftrightarrow
\text{mode label}
]

的对应关系。

## 5.6 与 R30 KEEP/SET 的关系

第一个 gate 不更新 high controller。

R30 继续使用现有：

[
P(\texttt{KEEP}),
\qquad
P(\texttt{SET}(z)).
]

Hungarian label alignment 的作用是让旧 high policy 尽可能继续选择与其原数值 label 对应的 mode。

因此：

-没有额外 check；
-没有强制 SET；
-没有改变 lifetime；
-没有为长技能付 intrinsic reward；
-没有 sampled team latent；

* low actor 仍严格是
  [
  \pi_l(a_i\mid o_i,z_i).
  ]

gate 测试的是：

> 在完全不修改 async scheduler 或 high selector 的情况下，修复 codebook 本身是否足以产生可复现模式和自然 transport。

若连这一点都失败，就不应把问题继续归因于 high-level credit。

---

# 6. 最小 Alice–Bob abandonment gate

## 6.1 固定 comparator 和预算

```text
source checkpoint:
  与 R32/R33 相同的 frozen adaptive-R30 checkpoint

seed:
  34031

source natural episodes:
  32 × 80 = 2,560 steps

split:
  24 train episodes
  8 heldout episodes

focal block rows:
  train = 24 × 8 × 2 = 384
  heldout = 8 × 8 × 2 = 128

balanced modes:
  K = 4
  exactly 96 train rows per mode

arms:
  real_modes
  episode_sequence_sham

offline distillation:
  10 epochs
  sequence batch size 64
  6 batches/epoch
  exactly 60 Adam calls/arm
  lr = 3e-4
  gradient clip = 0.5
  W = 10

heldout forced evaluation:
  64 joint contexts
  2 focal agents
  4 forced skills
  2 independent replicas
  10 steps
  = 10,240 environment steps/arm

natural transport:
  64 paired stochastic episodes/arm
  = 5,120 steps/arm

total environment exposure:
  2,560 + 2×10,240 + 2×5,120
  = 33,280 steps

bootstrap:
  10,000 repetitions
  source-episode / paired-reset clusters
  seed = 40,034,031
```

在 heldout forced evaluator 中：

-同一 context/replica 下四个技能使用 common random numbers；
-两个 replica 独立；
-每个 branch 恢复相同 environment 和 recurrent snapshot；
-只替换 focal skill；
-teammate 使用 frozen behavior policy。

没有 `UNDERPOWERED` 分支。

---

# 7. Gate 指标

## M0 — 实现有效性

以下必须全部通过：

1. `32/24/8` episode split 和 `384/128` focal rows 精确；

2. prototype 只用 train rows；
   3.四个 mode 各精确 96 行；

3. prototype-to-skill Hungarian mapping 是 bijection；

4. sham 无 self donor；

5. real/sham 的 label counts、每-agent counts、八-block sequence multiset 和 run-length multiset完全相同；

6. 两臂初始参数最大差异：

   [
   \le10^{-8};
   ]

7. source actor replay：

   [
   \max|\log p_{\rm replay}-\log p_{\rm stored}|
   \le10^{-5};
   ]

8. 两臂各精确 60 次 finite optimizer call；

9. gradient 仅进入：

   ```text
   actor_film
   actor_rnn
   actor_act.action_out.fc_mean
   ```

10. 所有其他参数 max drift：

    [
    \le10^{-8};
    ]

11. log-std、high policy、KEEP probability、critic、OPT/bridge 全部静止；
    13.无 reward、GAE、value、posterior、normal PPO 或 environment objective read；

12. descriptor schema 确认不存在 task/reward/action/age/old-(z) 字段。

与 R33 修正原则一致，M0 **不要求允许参数必须产生非零 drift**。若数学梯度为零，它进入 M1 失败。

任何 M0 miss：

```text
INVALID_R34_IMPLEMENTATION
```

只允许修复该具体实现错误。

---

## M1 — 因果模式复现

对每个 heldout context、focal agent、forced skill 和 replica，构造同一 trajectory descriptor，并用 frozen prototypes 做 nearest-prototype assignment。

### Prototype fidelity

定义：

[
F
=

P[
\operatorname{NN}(y^{do(z)})=z
].
]

要求：

[
F_{\rm real}\ge0.60,
]

[
F_{\rm real}-F_{\rm sham}\ge0.20,
]

且 source-episode cluster 95% CI lower bound (>0)。

每个技能单独要求：

[
F_{{\rm real},z}\ge0.45.
]

随机基线是 (0.25)。

### Persistent mode SNR

在每个 context 中定义：

[
B_c
===

\frac{1}{\binom K2}
\sum_{z<z'}
\left|
\frac{y_z^1+y_z^2}{2}
---------------------

\frac{y_{z'}^1+y_{z'}^2}{2}
\right|^2,
]

[
W_c
===

\frac1K
\sum_z
\frac12
|y_z^1-y_z^2|^2,
]

[
R_c=\frac{B_c}{W_c+\epsilon}.
]

要求：

[
\operatorname{median}(R_{\rm real})\ge1.50,
]

[
CI_{95%,lower}>1.0,
]

以及：

[
\operatorname{median}
(R_{\rm real}-R_{\rm sham})
\ge0.30,
]

其 95% CI lower bound (>0)。

M1 检查：

> hindsight label 是否已经变成真实可干预的 skill mode，而不只是离线 cluster。

---

## M2 — 未修改 R30 下的自然 transport

运行 64 个 paired stochastic episodes。对每个完整自然 block 和 agent，计算实际 descriptor 的 nearest prototype。

### Natural skill/mode consistency

定义：

[
A_{\rm nat}
===========

P[
\operatorname{NN}(y_{\rm natural})
==================================

z_{\rm active}
].
]

要求：

[
A_{\rm nat}^{real}\ge0.45,
]

[
A_{\rm nat}^{real}
------------------

A_{\rm nat}^{sham}
\ge0.15,
]

paired-reset 95% CI lower bound (>0)。

这证明不是只有 forced evaluator 能找到模式；原始 R30 high policy 在自然状态下也实际使用了新 codebook。

### Task-agnostic joint coverage

继续使用固定 625 个 joint-position cells：

[
\frac{
Coverage_{\rm real}
}{
Coverage_{\rm sham}
}
\ge1.10,
]

且 paired-reset mean coverage difference 的 95% CI lower bound (>0)。

external task reward、collection 和 button/target/contact 只记录，不进入 PASS。

---

## M3 — R30 安全

real arm 必须满足：

[
full_sync_SET_rate\le0.50,
]

[
H(Z\mid SET)/\log4\ge0.80,
]

[
\min_zP(Z=z\mid SET)\ge0.05,
]

[
\min
\left[
P(T>4k_0),
P(T\le4k_0)
\right]
\ge0.05.
]

因为 high policy被冻结，明显的安全失败意味着 low mode distillation通过状态分布间接破坏了 R30 temporal behavior，同样不能 promotion。

---

# 8. 精确 PASS/FAIL 分支

## `PASS_R34_BHMD`

要求 M0 有效且 M1–M3 全部通过。

仅支持：

> 从 task-agnostic、action-free natural trajectory modes 得到的平衡 hindsight labels，可以通过 sequence distillation 形成可干预复现的 skill modes；这些模式在未修改 R30 KEEP/SET controller 下得到自然使用并扩大联合状态访问。

PASS 后唯一授权动作是准备：

```text
normal-training real_modes
versus
episode_sequence_sham
```

的 sparse-source mechanism comparison。

仍不支持：

* task improvement；
* cooperation；
* HMASD parity；
* async lifetime superiority；
* S7 transfer；
  -人类可解释角色语义。

## `FAIL_M1_RETIRE_R34_BHMD`

若任一 fidelity 或 persistent-SNR 条件失败：

> 当前自然轨迹中的 hindsight clusters 不能被蒸馏为稳定、可干预的 skills。

永久退休 BHMD。不得更改：

* (K)；
* descriptor；
* clustering method；
* epoch；
* parameter scope；
* learning rate；
* source episode 数；
* forced window；
* fidelity/SNR threshold；
* seed。

## `FAIL_M2_FORCED_ONLY_MODE_CLONING`

若 M1 通过但 natural consistency 或 coverage 失败：

> skill modes 只在 forced evaluator 中成立，不能被原有 R30 high policy自然调用或运输。

永久退休为 forced-only mode cloning。不得立即增加 high imitation、team latent 或 reward 来补救。

## `FAIL_M3_R30_COLLAPSE`

若 M1/M2 通过但 R30 safety 失败：

> mode distillation 通过同步刷新、skill-supply collapse 或 lifetime collapse 获得结果。

永久退休本路线。

---

# 9. 代码边界

在 gate 通过之前只新增：

```text
ha_ctse_process/r34_balanced_hindsight_mode_distillation.py
scripts/r34_bhmd_gate.py
```

第一个文件包含：

```text
InteractionModeDescriptor
fit_balanced_prototypes
hungarian_align_to_existing_skills
build_episode_sequence_sham
sequence_distillation_loss
nearest_prototype
causal_mode_fidelity
between_within_mode_ratio
parameter_drift_metrics
```

第二个文件包含：

```text
source natural sequence bank
train/heldout episode split
real/sham label construction
paired low-actor distillation
heldout forced evaluator
natural R30 semantic-consistency evaluator
M0-M3 decision
single result JSON
```

gate 之前不修改：

```text
ha_ctse_process/standalone_agent.py
ha_ctse_process/r30_fixed_clock.py
ha_ctse_process/train.py
envs/pettingzoo/alice_bob_asymmetric_cycles.py
```

现有 recurrent focal sequence replay 和 R30 collector接口足够支持 gate。

---

# 10. 最终结论

[
\boxed{
\text{R33 VALID FAIL}
\Rightarrow
\text{RETIRE direct roster-complementarity fitting}
}
]

可复用因果结论是：

[
\boxed{
\text{精确选择器不能从不稳定的标签中制造 primitive；
先形成模式，再讨论选择与组合。}
}
]

唯一下一路线是：

[
\boxed{
\text{R34-BHMD：自然交互模式发现}
\rightarrow
\text{平衡 hindsight label}
\rightarrow
\text{低层序列蒸馏}
\rightarrow
\text{因果 skill-mode gate}
}
]

这条路线不再为当前 (z) 寻找第五种 score，而是第一次直接测试：

> **能否从现有自然行为数据中构造一个真正可执行、可自然调用的离散技能 codebook。**
