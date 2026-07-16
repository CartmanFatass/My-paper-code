# 裁决

[
\boxed{\texttt{CONFIRM VALID_FAIL_R48_SBRS}}
]

[
\boxed{
\texttt{CONFIRM NO-RESCUE RETIREMENT OF THE RECURRENT-BOUNDARY LINE}
}
]

[
\boxed{
\texttt{CONFIRM BINDING STOP OF FIXED-}N
\texttt{ SKILL/LIFETIME ALGORITHM EXPLORATION}
}
]

同时保留且仅保留一个独立的新研究问题：

[
\boxed{
\texttt{R49-ORSE-G0:
Open-Roster Set-Equivariant Interface Gate}
}
]

R49 是纯架构门，不继承“技能语义有效”“可变 lifetime 有效”或“R30 已形成可用技能”的任何前提。它只检验：

[
\boxed{
\text{可变 active set}
\rightarrow
\text{集合等变 roster 表示}
\rightarrow
\text{变长 AR sampling/replay 的严格一致性}
}
]

---

# 一、R48 validity audit

没有发现能够改变结果分支的 M0 缺陷。

## 1. Source checkpoint 与 context schedule 正确

R48 使用注册的 frozen adaptive-R30 checkpoint：

```text
logs/r30_alice_bob_paired_64k_20260714_163908/
runs/adaptive_keep_set/seed30031/
standalone_process_core_final.pt
```

结果 JSON 验证了：

* `checkpoint_total_steps=64000`；
* `checkpoint_update=50`；
* `N=2`、`K=4`、`k0=10`；
* continuous 2D action；
* recurrent low actor；
* actor 不读取 team code；
* R31 与 transition reward 均关闭。

自然 context 的生成日程也符合预注册合同：

[
\text{focal}(g)=g\bmod2,
]

[
\text{check}(g)
===============

1+\left\lfloor\frac g2\right\rfloor\bmod4,
]

所以 snapshot 位于 primitive time (10,20,30,40)，每个 focal hidden 已经经历至少一个完整自然 block。代码在自然 high check完成 roster commit后、该 block 第一个 low action之前保存 context。

正式结果取得：

* 64 个 context；
* 5,120 个自然 source steps；
* 0 次 early source reset；
* 每个 target skill 分别出现在 `47/48/50/47` 个 context中。

---

## 2. 三个 nonincumbent targets 与两个 arm 正确

每个 context 都从四个 opaque skill labels 中排除 natural incumbent，得到恰好三个 nonincumbent targets。

两个 arm 的实现是：

```text
carry_hidden:
    forced target skill
    focal actor hidden = snapshot hidden

reset_on_set:
    same forced target skill
    focal actor hidden = 0
```

`run_branch` 先恢复同一个环境 snapshot，然后复制相同：

* observation；
* centralized state；
* forced roster；
* team code；
* teammate actor hidden；
  -全部 critic hidden。

之后只有 `reset_on_set` 的 focal actor hidden 被清零。

Analyzer 又独立重建 expected hidden tensor，并验证：

* carry hidden 与 snapshot误差为 0；
* reset focal hidden误差为 0；
* teammate actor hidden没有变化；
* critic hidden arm间误差为 0；
* focal snapshot hidden最小 (L_2=1.4011)，所以并非在零 hidden上做一个装饰性 reset。

---

## 3. Gaussian CRN 与源 stochastic policy 正确

R48 没有退化为 deterministic action comparison。它从源 tanh-Gaussian head读取：

[
\mu_t,\sigma_t,
]

然后用显式 innovation：

[
\tilde a_t
==========

\mu_t+\sigma_t\odot\eta_t,
\qquad
a_t=\tanh(\tilde a_t).
]

如果 action head不是源 `TanhDiagGaussian`，代码会直接报错。

Innovation tensor由固定 seed `68041` 预生成，shape覆盖：

```text
context × replica × time × agent × action-dimension
```

同一 context/replica 的两个 arms和三个 targets使用同一个 tape；两个 replicas使用不同 tape。Analyzer验证 `common_innovation_max_error=0`。

因此：

[
\text{arm差异}
============

\text{focal hidden boundary差异},
]

而不是 action-noise差异。

---

## 4. 40-step hold 与 task-blind trajectory 正确

Branch 内只设置一次 forced roster，随后连续执行 40 个 low-policy steps，不再调用 high controller。所有 768 个 branches均完整执行，没有 early reset或truncation。

过程读取只有四维：

[
y_{i,t}
=======

\begin{bmatrix}
\bar p_{i,t}-\bar p_{i,0}\
(\bar p_{-i,t}-\bar p_{i,t})
----------------------------

(\bar p_{-i,0}-\bar p_{i,0})
\end{bmatrix}
\in\mathbb R^4,
]

其中：

[
\bar p=p/8.
]

它不读取：

* action likelihood；
* skill label作为metric input；
* reward；
* task object；
* contact；
* phase；
* success；
* R47 spectral view或mode。

H10 的数组 indices `0..9`对应执行后的 primitive steps (1..10)，H40-late 的 indices `30..39`对应 (31..40)，与结果 JSON 登记一致。

---

## 5. (B/W/\rho) 与 target-conditional (\rho) 正确

对每个 arm/context，between statistic使用三个 targets的全部三对，并在相同 replica index下比较：

[
B_{a,c}^{H}
===========

\frac1{3}
\sum_{z<z'}
\frac12\sum_{r=0}^{1}
d_H(y_{a,c,z,r},y_{a,c,z',r}).
]

Within statistic为：

[
W_{a,c}^{H}
===========

\frac13\sum_z
d_H(y_{a,c,z,0},y_{a,c,z,1}).
]

实现逐项遵守该定义；target-conditional between则只比较该target与另外两个targets，within使用该target自己的两个replicas。

聚合是 ratio of means：

[
\rho_a^H
========

\frac{\mathbb E_c[B_{a,c}^H]}
{\mathbb E_c[W_{a,c}^H]+10^{-8}},
]

不是 context-wise ratio的平均。

Target-conditional (\rho)同样使用所有出现该target的contexts上的between mean除以within mean。

---

## 6. Paired bootstrap 与终端分支正确

Analyzer只生成一张：

[
10000\times64
]

的 context resampling table。两个arms、三个targets、两个replicas及全部轨迹coordinates共享同一context resample，因此所有arm ratio都是严格paired的。

M1代码逐字实现注册门槛：

对于H10和H40-late：

[
\operatorname{LCB}*{95}(\rho*{\mathrm{reset}})>1,
]

[
\operatorname{LCB}*{95}
\left(
\frac{\rho*{\mathrm{reset}}}
{\rho_{\mathrm{carry}}}
\right)>1.25,
]

[
\operatorname{UCB}*{95}
\left(
\frac{W*{\mathrm{reset}}}
{W_{\mathrm{carry}}}
\right)<0.80,
]

[
\operatorname{LCB}*{95}
\left(
\frac{B*{\mathrm{reset}}}
{B_{\mathrm{carry}}}
\right)>0.90,
]

并额外要求H40-late四个target-conditional (\rho>1)。

分支也严格为：

```text
M0 fail
    -> INVALID_R48_SBRS_WIRING

M0 and M1 pass
    -> PASS_R48_SBRS_G0

M0 pass and M1 fail
    -> VALID_FAIL_R48_SBRS
```

没有 `UNDERPOWERED`、追加数据或后验阈值修改分支。

结论：

[
\boxed{
\text{未发现 result-changing M0 defect。}
}
]

---

# 二、可复用的因果结论

R48最重要的结果是：

[
\boxed{
\text{between-target process difference被保留，}
\quad
\text{within-skill stochastic variability没有下降。}
}
]

## H10

Between mean：

[
B_{\mathrm{carry}}=0.05466,
\qquad
B_{\mathrm{reset}}=0.06255,
]

即reset后between difference约增加：

[
14.4%.
]

但within mean为：

[
W_{\mathrm{carry}}=0.05186,
\qquad
W_{\mathrm{reset}}=0.05227,
]

reset反而略增约：

[
0.79%.
]

所以：

[
\operatorname{UCB}*{95}
\left(
W*{\mathrm{reset}}/W_{\mathrm{carry}}
\right)
=======

1.01877,
]

远未达到注册的 `<0.80`。Absolute reset (\rho)均值虽然为 `1.1967`，其lower bound仍只有 `0.98468`；reset/carry (\rho) gain lower bound也只有 `1.11816`。

## H40-late

两个arms都已有很强的late process separation：

[
\rho_{\mathrm{carry}}=5.2814,
\qquad
\rho_{\mathrm{reset}}=5.3342.
]

Reset arm四个target-conditional (\rho)也全部大于1：

[
2.396,\ 4.370,\ 6.880,\ 9.138.
]

但是：

[
\operatorname{LCB}*{95}
\left(
\rho*{\mathrm{reset}}/\rho_{\mathrm{carry}}
\right)
=======

1.00223,
]

几乎没有实际增益；within ratio均值为：

[
1.00156,
]

其upper bound为：

[
1.00874.
]

也就是说，reset既没有降低late stochastic noise，也没有实质改变已有的target separation。

因此可复用的结论不是“low recurrent state没有作用”，而是：

[
\boxed{
\begin{aligned}
&\text{非incumbent skill targets能够在H40产生明显不同的raw trajectories；}\
&\text{但这些差异在carry和reset条件下几乎相同；}\
&\text{旧skill hidden记忆不是当前within-skill随机性的主要来源；}\
&\text{SET-time focal zero-reset不能解释或修复R31/R47类失败。}
\end{aligned}
}
]

这与“有forced conditional capacity、缺乏自然语义形成”的总证据一致。R48没有证明自然high policy会使用这些差异，也没有证明skill有合作或任务意义。

---

# 三、fixed-(N) 研究边界

`VALID_FAIL_R48_SBRS` 的预注册分支明确要求：

* 永久退休SET-time focal hidden zero-reset；
* 永久退休shared-parameter skill-boundary-reset路线；
* 永久退休该raw-trajectory (B/W/\rho) gate；
* 拒绝以recurrent contamination重新解释R31/R47；
* 停止fixed-(N) skill/lifetime算法探索。

此前选择R48时也明确规定：R48一旦有效失败，不得继续提出新的fixed-(N) intrinsic、classifier、effect scorer、mode estimator、renewal critic或actor-noise变体。

因此：

[
\boxed{
\text{当前项目中的fixed-}N
\text{ skill/lifetime算法主线到此终止。}
}
]

这是一项绑定的项目决策，不是关于所有MARL技能算法的不可能性定理。现有结果只说明，在已注册、逐层否决的本项目路线中，没有留下一个仍有上游因果授权的fixed-(N)机制。

特别是，以下工作不再授权：

* 新的fixed-(N) intrinsic reward；
* 新分类器或process scorer；
* 新spectral/kernel/neural mode target；
* 新renewal critic；
* 另一种hidden reset或skill-indexed hidden bank；
* 更换action noise；
* reward-on pair；
* fixed-(N) S7算法实验。

---

# 四、唯一可继续的问题：独立的 open-roster 架构轴

Open-roster仍有独立的工程和架构正当性。此前审阅已经接受：

* variable team membership是独立架构轴；
* membership transition与surviving agents的skill renewal必须分离；
* 第一版使用外生membership；
* padded storage和mask-aware set representation；
* active-only autoregressive decoding；
* 存储active set、membership epoch、external order和真实prefix；
* joiner initial SET；
* leaver membership-censored；
* survivors不重置hidden、skill或age。

但R48之后，该方向必须重新定位为：

[
\boxed{
\text{variable-}N\text{ interface correctness}
}
]

而不是：

[
\text{variable-}N+\text{已验证的异步技能算法}.
]

当前fixed R30实现确实与 (N) 绑定：

[
\texttt{ar_prefix_dim}=K(1+2N),
]

并为每个agent构造identity-specific skill/age slots。

High critic也直接展平：

[
N\times obs,
\qquad
N\times K,
\qquad
2N,
]

所以参数shape随 (N) 改变。

因此仍有一个合法而独立的架构问题：

> 能否把identity-indexed fixed-(N) roster替换为parameter-count-independent、permutation-equivariant、mask-aware的active-set接口，同时保持MAT式顺序sampling/replay的严格概率语义？

---

# 五、唯一下一条路线：R49-ORSE-G0

## Open-Roster Set-Equivariant Interface Gate

## 1. 唯一因果边

[
\boxed{
\begin{aligned}
&\text{identity-indexed fixed-}N\text{ roster}\
&\rightarrow
\text{mask-aware set representation}\
&\rightarrow
\text{active-only variable-length AR sampling/replay}\
&\rightarrow
\text{permutation、padding、prefix和membership语义严格成立}.
\end{aligned}
}
]

这是standalone architecture gate：

* 无environment；
* 无task reward；
* 无intrinsic reward；
* 无PPO；
* 无skill training；
* 无checkpoint迁移；
* 无S7；
* 无性能或合作claim。

其中四个categorical codes只是opaque protocol states，不被称为已形成语义的skills。

---

## 2. 固定架构

只实现一个最小 Deep-Sets版本，不引入graph、attention或inducing slots。

每个active member输入：

[
x_i=
[
o_i^{12},
\operatorname{onehot}(c_i)^4,
\log(1+age_i)/\log501,
joined_i,
processed_i
].
]

禁止输入：

* persistent agent ID；
* padded slot index；
* membership epoch；
* task或reward字段。

Membership epoch只进入storage key，不进入network。

共享member encoder：

```text
input -> Linear(64) -> GELU -> Linear(64) -> GELU
```

静态team summary：

[
g=
\left[
\frac1N\sum_i\phi(x_i),
\log(1+N)
\right].
]

动态working-roster accumulator：

[
r^{(j)}
=======

\frac1N\sum_i
\psi(
h_i,c_i^{(j)},age_i^{(j)},processed_i^{(j)}
).
]

处理一个token后只做：

[
r^{(j)}
=======

r^{(j-1)}
+
\frac{
u_i^{new}-u_i^{old}
}{N}.
]

共享decoder读取：

[
[h_{\sigma(j)},g,r^{(j-1)}]
]

并输出现有的：

```text
KEEP logit
conditional SET-skill logits
```

Scalar high value只读取pooled active set和 (\log(1+N))。

参数shape不得依赖 (N)。

---

## 3. 固定数据合同

```text
experiment                 R49-ORSE-G0
execution                  local CPU, deterministic, one thread
model seed                 49041
synthetic-data seed        59041
sampling seed              69041
opaque codes               4
member feature dimension   12
hidden dimension           64
active sizes               {1,2,3,4,6,8,12,16}
cases per size             128
base cases total           1024
permutations per case      8
permutation reads          8192
padding variants           1024
sample/replay sequences    1024
join/leave event pairs     256
optimizer steps            0
environment steps          0
reward reads               0
```

Padding使用随机非零junk values，确保结果不可能仅因dummy slot为零而偶然一致。

每个case存储：

```text
active member keys
membership epochs
active mask
opaque codes
ages
external AR order
sampled token sequence
actual applied working prefixes
old token log-probabilities
```

---

# 六、R49最小 abandonment gate

## M0：实现有效性

必须全部满足：

1. exact registered counts；
2. network state dict中没有agent-ID或slot embedding；
3. parameter count和tensor shape不依赖active (N)；
4. masked slots不产生token；
5. external order、active set、membership epoch和prefix完整存储；
6. stochastic sample与teacher-forced replay使用同一effective action support；
7. 所有logits、values、log-probabilities和gradients有限；
8. environment、reward、optimizer和checkpoint exposure均为0；
9. joiner/leaver/survivor event records完整；
10. incremental accumulator与full recomputation均被执行并记录。

失败：

```text
INVALID_R49_ORSE_WIRING
```

唯一动作是修复明确的mask、storage、order、prefix或replay defect，并原合同重跑。

---

## M1：架构性质

必须同时满足：

### Permutation equivariance

对member tokens和stored external order做一致置换后：

[
\max|\Delta\text{ token logits}|
\le10^{-6},
]

[
\max|\Delta V|
\le10^{-6}.
]

### Padding invariance

增加任意随机masked junk slots后：

[
\max|\Delta\text{ token logits}|
\le10^{-6},
]

[
|\Delta V|
\le10^{-6}.
]

### Incremental/full parity

每个AR位置：

[
\max
\left|
\ell^{incremental}
------------------

\ell^{full\ recompute}
\right|
\le10^{-6}.
]

### Replay parity

[
\max
\left|
\log p_{\mathrm{stored}}
------------------------

\log p_{\mathrm{replay}}
\right|
\le10^{-6}.
]

### Membership semantics

* joiner的KEEP不在action support中；
* leaver产生0个token；
* survivor的opaque code、age、low-hidden placeholder和membership epoch逐位不变；
* active token count严格等于active member count。

### Prefix actionability

对 (N\ge2) 的case：

[
P\left[
\left|
\frac{\partial \ell_{\sigma(j)}}
{\partial r^{(j-1)}}
\right|_F

> 10^{-8}
> \right]
> \ge0.99,
> ]

且：

[
\operatorname{median}
\left|
\frac{\partial \ell_{\sigma(j)}}
{\partial r^{(j-1)}}
\right|_F

> 10^{-4}.
> ]

这只证明前序applied roster能够影响后序token，不证明该影响有任务价值。

### Size independence与复杂度

对全部 (N)：

* state-dict keys/shapes完全相同；
  -每个check只有一次active-set full encode；
* incremental updates严格为 (N)；
* decoder calls严格为 (N)；
* pairwise (N\times N) tensor count为0。

---

# 七、R49互斥结果分支

## `PASS_R49_ORSE_ARCHITECTURE`

要求：

[
M0\land M1.
]

允许结论仅为：

> 一个parameter-count-independent、mask-aware、set-equivariant的active-roster接口能够在变长team上保持严格sampling/replay和membership语义。

唯一下一动作：

> 将该接口以default-off方式接入一个**外生、跨episode variable-(N)** compatibility gate。

仍不授权：

* skill semantic claim；
* variable-lifetime efficacy；
* intrinsic reward；
* within-episode join/leave training；
* S7算法比较；
* open-roster论文贡献claim。

## `VALID_FAIL_R49_ORSE_ARCHITECTURE`

条件：

[
M0\land\neg M1.
]

永久退休该精确组合：

```text
Deep-Sets mean roster
log-count feature
incremental working-roster accumulator
shared active-only AR decoder
pooled scalar value
```

不得自动换成graph、Transformer、ISAB、inducing slots或更大模型进行救援。

该分支触发后：

[
\boxed{
\text{当前项目的open-roster架构线也停止。}
}
]

## `INVALID_R49_ORSE_WIRING`

仅允许修复明确的实现缺陷并按相同合同重跑。

不存在：

* `UNDERPOWERED`；
  -参数扩容；
* seed追加；
  -测试case追加；
  -阈值修改；
  -模型替换；
  -任务环境救援。

---

# 八、永久关闭的分支

以下保持永久关闭：

1. old-(z) classifier与 (q_d/q_D) reward revival；
2. action-density/action-information reward；
3. observational effect posterior、CFEI；
4. direct IFEPG及effect-gradient改名；
5. roster complementarity scorer与high-head fitting；
6. hindsight clustering、prototype与mode distillation；
7. R35–R40 access/substrate路线；
8. R42 incumbent-logit residual；
9. R43 full-stack true-renewal continuation；
10. R44 frozen-source next-check renewal credit；
11. R45 Alice–Bob natural-support SDRA；
12. R46 HMRV dynamics/estimand/critic/read；
13. R47 spectral view/basis/score/reward pair；
14. R48 SET-time focal hidden reset与raw-trajectory gate；
15. duration head、duration-category action；
16. KEEP reward、lifetime reward、switch/edit penalty；
17. task-specific novelty、distance、contact、phase、progress、success或potential shaping；
18. 新fixed-(N) intrinsic、classifier、scorer、renewal critic、reset或actor-noise变体；
19. 任何通过seed、数据、预算、阈值、model size、reward、environment或best-checkpoint选择进行的救援。

R41B仍可作为原始HMASD fixed-(k)正参考，但不能被解释为当前HA-CTSE技能语义已经闭合。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\texttt{R48 = VALID_FAIL};\
&\text{没有result-changing M0 defect；}\
&\text{focal hidden reset保留between-target差异，}\
&\quad\text{但没有降低within-skill随机性；}\
&\text{recurrent contamination解释永久退休；}\
&\text{fixed-}N\text{ skill/lifetime算法探索正式停止；}\
&\text{唯一仍授权的问题是独立的R49-ORSE-G0架构门；}\
&\text{open-roster不得继承skill semantics、async efficacy或S7 claim；}\
&\text{R49有效失败后，当前项目线整体停止，不作任何救援。}
\end{aligned}
}
]
