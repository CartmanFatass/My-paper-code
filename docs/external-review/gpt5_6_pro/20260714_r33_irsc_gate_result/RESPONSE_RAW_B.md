# 1. 明确裁决

## **R33-IRSC：VALID SCIENTIFIC FAIL，永久退休**

没有发现能改变注册 estimand、随机化、完整 roster 概率、梯度归属或结果解释的具体 M0 缺陷。应执行已经注册的分支：

```text
FAIL_M1_RETIRE_R33_IRSC
```

不得重跑、扩种子或通过 temperature、更多更新、另一种 pair permutation、score clipping、KEEP/shared-trunk 更新、新 team latent、(q_D)、team reward 或 normal-trainer 集成挽救 R33。问题文件和实验记录均明确将这些后续动作列为禁止项。

## **唯一下一路线：R34-BHMD**

# **Balanced Hindsight Mode Distillation**

# **平衡式事后行为模式蒸馏**

选择的因果边是：

[
\boxed{
\text{自然、无标签的持续交互模式}
\rightarrow
\text{平衡 hindsight 技能标签}
\rightarrow
\text{技能条件 recurrent sequence distillation}
\rightarrow
\text{可干预复现的技能模式}
\rightarrow
\text{冻结 R30 下的自然调用与状态探索}
}
]

决定性转向是：

> 不再假设当前四个 (z) 已经是有意义的 primitive，然后为这些既定标签设计第五种 effect、pair 或 selection score；先从自然行为数据中构造可重复的模式，再将模式写入技能 codebook。

这不是 scheduler、queue、hazard、service rule 或 IMOD 迁移。IMOD 在本轮只提供执行约束：这些机制是基础设施，不是已验证的学习信号；`J`、value-of-revision、request-value、value-ranked pruning 和 ROSTER controller 仍保持退休。

---

# 2. R33 有效性审计

## 2.1 修正后的 R33 estimand 确实隔离了非加性 interaction

实现首先对每个 agent、replica 的完整 (K\times K) roster-effect 表分别做两向中心化：

[
\widetilde E_i^q(a,b)
=====================

E_i^q(a,b)
-\overline E_i^q(a,\cdot)
-\overline E_i^q(\cdot,b)
+\overline E_i^q(\cdot,\cdot).
]

代码中的 row mean、column mean 和 grand mean 只消去两个 roster 轴，保留 replica、agent 与 effect 维度。

因此在独立加性模型

[
E_1(a,b)=f_1(a)+u_1(b),\qquad
E_2(a,b)=u_2(a)+f_2(b)
]

下，(\widetilde E_i^q(a,b)) 精确为零。单个技能自身效应、teammate 技能的纯加性效应和固定 agent identity 不能独立产生 R33 分数。

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

代码与该定义一致。

两个 replica 独立时：

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

所以：

* 稳定的 sign-reversing role swap 得到正分；
* 两个 orientation 同方向的 interaction 得到负分；
* 只有一个 orientation 有效时，反对称与对称项相等，期望分数为零；
* 纯加性执行得到零。

这是一个边界窄但数学合理的 **stable non-additive role-swap** estimand。它不是把“两个技能动作不同”误称为 team complementarity。

## 2.2 完整 roster 随机化有效

每个自然 R30 context 枚举全部 16 个 final rosters。每个 branch 恢复：

* 同一个 simulator snapshot；
* 同一个 low recurrent runtime；
* 同一个起始 observation/state；
* 同一个 team-code context；
* 指定的 complete roster。

同一 context 和 replica 下，16 个 rosters 使用相同随机种子；两个 replica 使用不同且全局唯一的随机流。

branch 设置了强制 `active_skills`，但没有把 skill age 置零。这不是本轮 defect：低层 actor 接口仍是

[
\pi_l(a_i\mid o_i,z_i),
]

不读取 age；十步 branch 中也不再调用高层 `KEEP/SET`。因此 age 不影响被估计的低层物理轨迹。

## 2.3 16-roster 联合概率是精确的

对每个 final roster，代码根据 pre-check roster 唯一生成：

[
e_i(r_i)=
\begin{cases}
\texttt{KEEP},&r_i=z_i^{-}\ \text{且 agent 已 active},\
\texttt{SET}(r_i),&\text{其他情况}.
\end{cases}
]

然后调用 R30 的 `evaluate_sequence`，按照 agent order 重建 working roster，并将所有 token log-probability 相加。

结果中的最大概率和误差为：

[
2.384\times 10^{-7},
]

低于注册阈值 (10^{-6})；自然 high-token replay error 为零。原始结果 JSON 中所有 probability、replay 和 branch-count M0 项均为真。

所以不存在遗漏 roster、近似 candidate set 或错误 prefix 导致的负结果。IMOD 中另一个 legacy stored-prefix 问题也不能解释本轮结果；问题文件明确禁止重开该解释，因为 active R30/R33 replay 已精确通过。

## 2.4 exact-expectation objective 和梯度范围正确

R33 直接计算：

[
L_{\mathrm{IRSC}}
=================

-\frac1B
\sum_c
\sum_r
\pi_\theta(r\mid c)
\operatorname{stopgrad}[A_c(r)].
]

它不采样高层 roster，不使用高层 critic、GAE 或 importance ratio。实现对 score detach，并对完整 roster 概率求精确期望。

运行前关闭所有参数梯度，只重新打开：

```text
high.skill_head.weight
high.skill_head.bias
```

八次更新后检查：

* 任意 non-head gradient；
  -所有参数漂移；
  -存储 prefix 上的 KEEP probability；
  -完整 roster 概率归一化。

原始 JSON 显示：

* 两臂均完成八次 finite optimizer call；
* 八次 gradient 均非零；
* real head relative drift 约 `0.027634`；
* sham head relative drift 约 `0.026423`；
  -其他参数 drift 与 gradient 为零；
* KEEP probability drift 为零；
* low、critic、posterior、normal-high-PPO 和 task-reward objective 更新均为零。

因此不是 zero wiring，也不是优化器没有真正改变高层 skill distribution。

## 2.5 pair-sham 是合格的机制匹配 comparator

pair 顺序是：

```text
01, 02, 03, 12, 13, 23
```

sham 使用：

```text
[5, 4, 3, 2, 1, 0]
```

即：

```text
01 <-> 23
02 <-> 13
03 <-> 12
```

每一个映射都不共享技能 identity。两臂使用完全相同的六个 signed pair scores，只改变它们归属于哪个技能对；展开到 16 个 ordered rosters 后，score multiset、均值和方差保持一致。

该 comparator 没有承诺逐更新 gradient norm 相等。这不是无效性：

* 它测试的是“正确 pair attribution 是否优于无技能重叠的错误 attribution”；
  -两臂的容量、score 数值集合、context、更新次数和可训练参数相同；
  -实际 head drift 也接近；
  -最终 M1 在 heldout true score 上评估，而不是比较训练 loss。

## 2.6 修正后的 M0 规则合理

M0 没有要求 head 必须移动超过某个阈值。若真实因果 score 导致精确零梯度，那应当进入 M1 失败，而不是被误判为实现错误并授权重跑。上一轮 disposition 已明确做出这一修正。

本轮实际存在有限非零梯度，因此即使不考虑该边界修正，结果也不会变成 `INVALID`。

---

# 3. 为什么这是物质性的算法失败

M1 的两个量虽然统计上为正：

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

[0.00051950,0.00190764],
]

但 material gates 分别为 `0.20` 和 `0.10`。前者约为门槛的 (0.98%)，后者约为 (1.25%)。与此同时，两个 head 已经移动约 (2.6%)–(2.8%)。

所以不能把结果解释成“更新没发生”或“再多训练一些即可”。正确解释是：

> 高层 head 能沿正确 attribution 方向产生一个可检测但极小的变化；当前 codebook 中没有足够稳定、可跨 context 泛化的非加性 pair semantics，供 selector 放大。

自然 transport 也没有出现：

[
Coverage_{\rm real}=427,\qquad
Coverage_{\rm sham}=429,
]

[
Coverage_{\rm real}/Coverage_{\rm sham}=0.995338,
]

[
D_{\rm real}/D_{\rm sham}=0.984925.
]

paired-reset 区间均没有正下界。

R30 safety 则独立通过：

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

因此失败不是：

-异步 controller 坍缩；
-技能供给坍缩；
-强制同步刷新；
-长短 lifetime 消失；
-实现、随机化或 gradient wiring 错误。

---

# 4. 可复用的因果结论

R29–R33 联合建立了下面的约束：

[
\boxed{
\text{分类、放大或重新选择既定 }z
\text{，不能替代技能模式本身的形成。}
}
]

具体而言：

1. action density 可区分，不保证稳定 environmental effect；
   2.自然 effect 可预测标签，不保证 intervention-level persistence；
   3.直接 individual-effect gradient 可产生小 shift，但不产生 codebook-wide differentiation；
   4.完整 roster 的精确 causal score 与精确 selector 只能得到极小正确 attribution，不能创造不存在的 pair primitive。

仓库 failure matrix 的结论也是：现有 codebook 没有被证明含有 material selectable team interaction，高层 fitting 不是缺失的 transport mechanism。

最重要的新因果原则是：

> **Selection is downstream of semantics.**
> selector 可以选择已经存在的 primitive，但不能从 context-specific noise 中制造 primitive。

这也解释了为什么 IMOD 调度器、queue、hazard、teacher-KL 或 atomic commit 不能成为 R34：它们可以保证执行一致性，但没有提供使技能形成持续语义的学习目标。

---

# 5. R34-BHMD 算法

## 5.1 自然模式 descriptor

从 frozen adaptive-R30 policy 收集自然 stochastic episodes。每个完整 (W=k_0=10) block、每个 focal agent (i) 构造：

[
y_{e,b,i}
=========

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

Alice–Bob 中 (x_i) 是 normalized position；因此：

[
y_{e,b,i}\in\mathbb R^{40}.
]

descriptor：

* 使用完整十步过程，而不只是 endpoint；
  -包含 focal 和 teammate 的相对起点位移；
  -不含绝对起始位置；
  -不含原 skill label；
  -不含 action；
  -不含 reward；
  -不含 button、target、contact 或 phase；
  -不含 agent ID、age、duration、OPT compact 或通信字段。

所有维度只使用 train split 的均值和标准差进行标准化，随后冻结。

## 5.2 精确平衡模式发现

训练 split 有 (N=384) 个 block-agent descriptors。固定：

[
K=4.
]

求解：

[
\min_{{c_z},q}
\sum_{n=1}^{N}
|\widehat y_n-c_{q_n}|_2^2
]

约束：

[
|{n:q_n=z}|=N/K=96,\qquad z=0,1,2,3.
]

实现使用确定性的 balanced k-means：

1. 固定 seed `34031` 的 k-means++ 初始化；
2. 对四个 center 各创建 96 个 assignment slots；
3. 使用 min-cost linear assignment 得到精确平衡 hard labels；
4. 更新 center；
5. assignment 不变或达到 50 次迭代时结束。

不扫描 (K)、初始化或距离函数。若 assignment 有限且精确平衡但四个 center 实质相同，这不是 M0 defect；它将进入 M1 失败。

## 5.3 仅作数字兼容的 Hungarian 对齐

模式发现完全不读取旧 (z)。聚类完成后，只为让 frozen R30 high policy 继续使用已有数值标签，求一次 permutation：

[
\sigma^\star
============

\arg\max_{\sigma\in S_4}
\sum_n
\mathbf 1[
\sigma(q_n)=z_n^{old}
].
]

(\sigma^\star) 只重新命名四个 prototype，不改变 cluster membership，也不把旧技能定义成模式。

## 5.4 机制匹配 comparator

两臂共享：

-完全相同的 source trajectories；
-相同 prototypes；
-相同 Hungarian permutation；
-相同网络、参数范围、minibatch 和 optimizer；
-相同模式 label counts；
-相同 episode/block 结构。

### `real_modes`

使用每个 block 的真实 hindsight mode label。

### `episode_sequence_sham`

对每个 agent channel 单独操作。将一个完整八-block label sequence 循环分配给下一 train episode：

[
\tilde{\mathbf z}_{e,i}^{sham}
==============================

\tilde{\mathbf z}_{(e+1)\bmod24,i}^{real}.
]

因此 sham 精确保留：

-每个 agent 的 label counts；
-全局每技能 96 个 block；
-八-block label sequence multiset；
-所有 run-length multiset；

* block-index/phase 的 label 分布；
  -标签 entropy。

它只破坏：

[
\text{该 episode 的 trajectory/action}
\leftrightarrow
\text{该 episode 的 hindsight mode sequence}.
]

这不是 IMOD teacher/student mixture，也不依赖 teacher KL。

## 5.5 完整 episode recurrent sequence distillation

每个训练单位是一个完整 focal-agent episode：

* 24 个 train episodes；
* 2 个 agents；
  -共 48 条长度 80 的 recurrent sequences。

对 sequence (e,i)，从零 actor hidden state 开始，用对应的八-block mode sequence重复展开十步标签。目标为：

[
L_{\rm BHMD}
============

-\frac1{48\cdot80}
\sum_{e,i,t}
\log
\pi_{\theta_l}
\left(
a_{e,i,t}
\mid
o_{e,i,t},
\tilde z_{e,i,b(t)},
h_{e,i,t}
\right).
]

关键语义：

* replay 跨越完整 80 步，避免修改 RNN 后使用不兼容的旧 block-start hidden state；
* source stochastic action 是 detached target；
* hindsight labels 与 prototypes 全部 detached；
  -没有 skill posterior；
  -没有 intrinsic reward；
  -没有 environment reward；
  -没有 value、critic 或 GAE；
  -没有 counterfactual effect U-statistic；
  -没有 R33 roster score。

### 梯度接收者

只更新：

```text
low.actor_film
low.actor_rnn
low.actor_act.action_out.fc_mean
```

冻结：

```text
low.actor_base
low action log-std
low critic 全部
R30 high actor 全部
R30 KEEP head / skill head / shared trunk
HighCheckValue
OPT / bridge
R29 / R31 / R32 / R33 modules
所有 posterior / classifier
environment
```

这不是“扩大 R32 参数范围”。R32 的 objective 是 intervention-effect score-function gradient；R34 是 natural-data hindsight sequence distillation，训练信号和数据生成机制均不同。

## 5.6 与 R30 KEEP/SET 的关系

第一个 gate 完全冻结 R30：

[
P(\texttt{KEEP}),
\qquad
P(\texttt{SET}(z)\mid\texttt{SWITCH})
]

均不被训练。

因此：

-没有新 scheduler；
-没有 queue、hazard、service rule 或 atomic partial commit；
-没有额外 check；
-没有强制 SET；
-没有 duration reward；
-没有长期技能 bonus；
-原 R30 exact probability/replay spine 保持 comparator 和 fallback。

自然 transport 中，两臂使用相同 R30 结构和参数。只有 low codebook 的 mode-label correspondence不同，因而已经是 scheduling-matched control，满足 IMOD 约束所要求的“学习与调度分离”。

---

# 6. 最小 Alice–Bob abandonment gate

## 6.1 固定预算

```text
source checkpoint:
  与 R32/R33 相同的 frozen adaptive-R30 checkpoint

seed:
  34031

source natural episodes:
  32 × 80 = 2,560 environment steps

split:
  24 train episodes
  8 heldout episodes

descriptors:
  train = 24 × 8 blocks × 2 agents = 384
  heldout = 8 × 8 × 2 = 128

modes:
  K = 4
  exactly 96 train descriptors per mode

arms:
  real_modes
  episode_sequence_sham

offline recurrent distillation:
  48 train agent-episode sequences
  sequence length 80
  batch size 8 sequences
  6 batches/epoch
  10 epochs
  exactly 60 Adam calls/arm
  lr = 3e-4
  gradient clip = 0.5

heldout forced evaluation:
  64 joint heldout block contexts
  2 focal agents/context
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
  source episode / paired natural-reset clusters
  seed = 40,034,031
```

无 `UNDERPOWERED`、自动扩种子或 post-result threshold revision 分支。

## 6.2 Heldout forced execution

对每个 heldout source episode：

1. 保存每个 block 的 simulator snapshot；
2. 对每个 arm，从 episode reset 的零 hidden state开始，在 source observation prefix 和 source active-skill sequence上重放到 block start，得到与当前 actor 参数兼容的 focal recurrent state；
3. teammate 使用冻结的 source low policy和其 source-compatible recurrent state；
4. focal 分别强制四个 skill，保持十步；
   5.同一 replica 内四个技能使用 common random numbers；
   6.两个 replica 独立；
5. external reward 不读取、不计分。

---

# 7. Gate 指标

## **M0 — 实现有效性**

全部必须满足：

1. `32/24/8` episode split 精确；

2. `384/128` descriptor 数精确；

3. prototypes 只用 train descriptors；
   4.每个 mode 精确 96 行；

4. Hungarian mapping 是四技能 bijection；

5. sham 无 self donor；

6. real/sham 的：
   -全局 label counts；
   -每-agent label counts；
   -八-block sequence multiset；

   * run-length multiset
     全部精确相同；

7. 两臂初始参数最大差异：

   [
   \le10^{-8};
   ]

8. source full-episode actor replay：

   [
   \max|\log p_{\rm replay}-\log p_{\rm stored}|
   \le10^{-5};
   ]

9. 两臂各精确 60 次 finite optimizer call；

10. gradient 仅进入：

    ```text
    actor_film
    actor_rnn
    action_out.fc_mean
    ```

11. 所有其他参数 max drift：

    [
    \le10^{-8};
    ]

12. log-std、low critic、完整 high controller、KEEP probability、OPT/bridge 均静止；
    14.无 reward、GAE、value、posterior、normal PPO 或 environment-objective read；

13. descriptor schema 中不存在 task、reward、action、old-(z)、age 或 agent-ID 字段；

14. forced branch/context/skill/replica 数与随机流合同精确。

M0 不要求允许参数必须移动。数学零梯度是有效 M1 失败。

M0 miss：

```text
INVALID_R34_IMPLEMENTATION
```

只允许修复具体 defect。

---

## **M1 — 因果技能模式复现**

用 frozen train prototypes 对 heldout forced trajectory descriptor 做 nearest-prototype assignment。

### Prototype fidelity

[
F
=

P[
\operatorname{NN}(y^{do(z)})=z
].
]

要求同时满足：

[
F_{\rm real}\ge0.60,
]

[
F_{\rm real}-F_{\rm sham}\ge0.20,
]

且 source-episode cluster 95% CI lower bound (>0)。

每个技能还必须满足：

[
F_{{\rm real},z}\ge0.45.
]

四分类 chance 为 (0.25)。

### Persistent mode SNR

定义：

[
\bar y_z=\frac12(y_z^1+y_z^2),
]

[
B_c
===

\frac1{\binom42}
\sum_{z<z'}
|\bar y_z-\bar y_{z'}|^2,
]

[
W_c
===

\frac14
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

[
\operatorname{median}
(R_{\rm real}-R_{\rm sham})
\ge0.30,
]

且 paired-context CI lower bound (>0)。

M1 直接判断 hindsight cluster 是否已经成为可由技能 intervention 复现的模式，而不只是离线分组。

---

## **M2 — 冻结 R30 下的自然调用与 transport**

运行 64 个 paired stochastic episodes。对每个完整自然 block 和 agent，计算 descriptor 的 nearest prototype。

### 自然 skill/mode consistency

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
A_{\rm nat}^{real}-A_{\rm nat}^{sham}\ge0.15,
]

paired-reset 95% CI lower bound (>0)。

### Task-agnostic joint coverage

继续使用固定的 625 个 joint-position cells：

[
\frac{Coverage_{\rm real}}
{Coverage_{\rm sham}}
\ge1.10,
]

且 paired-reset mean coverage difference 的 95% CI lower bound (>0)。

collection、button/target contact、joint coordination 和 sparse task reward只记录为 diagnostic，不进入 PASS。

---

## **M3 — R30 safety**

real arm必须满足：

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

该 gate 不增加 IMOD scheduler comparator，因为算法没有改变调度。两个 arms 的 high controller、检查时钟和 KEEP/SET 参数完全相同；若未来另加 queue/hazard/service mechanism，则必须另做 realized-rate-matched random control，不能继承 R34 的结论。

---

# 8. 精确结果分支

## `PASS_R34_BHMD`

仅当 M0 有效且 M1–M3 全部通过。

只支持：

> 从 task-generic、action-free natural trajectory descriptors 得到的平衡 hindsight labels，可以通过 recurrent sequence distillation 形成可干预复现的技能模式；冻结的 R30 KEEP/SET controller 能在自然执行中调用这些模式，并扩大联合状态访问。

PASS 后唯一授权动作：

```text
normal-training real_modes
versus
episode_sequence_sham
```

的 sparse-source mechanism-matched comparison。

仍不支持：

* task efficacy；
* cooperation；
* HMASD parity；
* async lifetime superiority；
* S7 transfer；
  -人类可解释角色语义。

## `FAIL_M1_RETIRE_R34_BHMD`

若任一 forced fidelity 或 persistent-SNR 条件失败：

> 当前自然轨迹中的 hindsight clusters 不能被蒸馏为稳定、可干预的技能。

永久退休 balanced hindsight mode-distillation line。不得改变 (K)、descriptor、clustering、epoch、参数范围、学习率、source 数量、window、seed 或阈值来重开。

## `FAIL_M2_FORCED_ONLY_MODE_CLONING`

若 M1 通过但 natural consistency 或 coverage失败：

> 技能模式只在 forced evaluator 中存在，冻结 R30 不能自然调用或运输它们。

永久退休为 forced-only mode cloning。不得立即加入 high imitation、team latent、reward 或 scheduler来补救。

## `FAIL_M3_R30_COLLAPSE`

若 M1/M2 通过但 safety失败：

> mode distillation 通过 skill-supply、同步刷新或 lifetime collapse 获得结果。

永久退休该路线。

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
fit_exact_balanced_prototypes
hungarian_align_to_existing_skills
build_episode_sequence_sham
full_episode_distillation_loss
replay_actor_prefix_hidden
nearest_prototype
causal_mode_fidelity
between_within_mode_ratio
parameter_drift_metrics
```

第二个文件包含：

```text
source natural episode bank
train/heldout episode split
real/sham label construction
paired recurrent actor distillation
heldout forced-mode evaluator
natural frozen-R30 consistency/coverage evaluator
M0-M3 decision
single result JSON
```

gate 前不修改：

```text
ha_ctse_process/standalone_agent.py
ha_ctse_process/r30_fixed_clock.py
ha_ctse_process/train.py
envs/pettingzoo/alice_bob_asymmetric_cycles.py
```

也不迁移 IMOD scheduler、event queue、hazard、teacher mixture、`J` 或 ROSTER controller。

---

# 10. 最终结论

[
\boxed{
\text{R33 VALID FAIL}
\Rightarrow
\text{永久退休 direct roster-complementarity fitting}
}
]

可复用的因果结论是：

[
\boxed{
\text{精确 selector 不能从不稳定标签中制造 primitive；
执行基础设施也不能替代技能形成信号。}
}
]

唯一下一条可证伪路线是：

[
\boxed{
\text{R34-BHMD：无标签自然模式发现}
\rightarrow
\text{平衡 hindsight label}
\rightarrow
\text{recurrent sequence distillation}
\rightarrow
\text{causal skill-mode gate}
}
]

它第一次直接检验当前失败链条上真正缺失的上游对象：

> **能否先构造一个可执行、可重复、并能被现有 R30 自然调用的离散技能 codebook。**
