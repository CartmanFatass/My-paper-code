# 裁决

[
\boxed{\texttt{CONFIRM_NO_ACCESS_R52_ARFA_SPECIALISTS}}
]

同时作一个必要的解释收窄：

[
\boxed{
\text{R52 失败的是注册的 deterministic specialist-access gate，}
\quad
\text{不是 stochastic task-return access。}
}
]

精确的 R52 task/comparator contract 继续按预注册分支永久退休；不得通过更多 specialist updates、增加 PPO epochs、修改 entropy、改用 stochastic evaluation、降低阈值或选择 best checkpoint 重判。Shared policy 的完美结果仍然隔离，不能据此宣称 variable-(N) learning 已经成立。

唯一下一条路线是：

[
\boxed{
\textbf{R53-RCMA-G0：
Residual-Capacity Masked Autoregression}
}
]

它将在一个新的匿名多速率队列任务中，测试：

[
\boxed{
\begin{aligned}
&\text{显式剩余资源容量}\
&\rightarrow
\text{capacity-feasible autoregressive joint support}\
&\rightarrow
\text{stochastic policy 的高价值概率质量}\
&\rightarrow
\text{稳定的 deterministic joint mode}\
&\rightarrow
\text{有效的 shared variable-}N\text{ 比较}.
\end{aligned}
}
]

---

# 一、为什么 R52 不是实现无效

## 1. 最强 implementation-validity 证据

R52 的环境、概率和优化合同不仅通过了汇总检查，而且关键路径可以在代码中逐项对应：

* 终局效用严格为
  [
  U=\min(M,J);
  ]
* station health 可恢复，并按 post-transition health 累积；
* expired job 不能事后补完成；
* 所有中间 reward 都是零；
* sampled pointers、working prefix、recurrent hidden、focal-current relation 和 masked probability 都被存储并在 replay 中重新构造。

M0 还包含 constructive、no-job 和 partial schedules：

[
(M,J,U)=(1,1,1),
]

[
U_{\text{no-job}}=0,
]

[
0<U_{\text{partial}}<1,
]

并验证 health recovery、switching cost 和 job expiration。所有这些检查均通过。

正式运行精确达到：

```text
320,000 transitions/arm
1,280,000 agent-token decisions/arm
625 shared optimizer steps
125 optimizer steps/specialist
PPO epochs = 1
```

并且：

```text
sample/replay logp error       0
prefix replay error            0
hidden replay error            0
focal-relation error           0
masked probability mass        0
checkpoint reload error        0
```

所有 shared 和 specialist 模块均获得非零有限梯度并产生参数漂移。

没有发现可将结果改判为 `INVALID_R52_ARFA_WIRING` 的 line-level defect。

---

## 2. Deterministic evaluation 也没有接错

正式 evaluator 使用注册的 sequential greedy decode：

[
a_{\sigma(j)}
=============

\arg\max_a
\pi
\left(
a\mid s,a_{\sigma(<j)}
\right),
]

即每个 autoregressive token 执行当前条件分布的局部 argmax。代码中的 deterministic 分支确实调用 `torch.argmax`，并继续应用 working prefix。

Zero-step 和 exact-final 使用同一组 evaluation ledgers；final checkpoint保存后被重新加载再评估。

Shared policy 在完全相同的 evaluator 下，对所有 (N) 都达到：

[
M=J=U=1.
]

因此不能把 specialist 的零结果归因于 evaluator 无法执行正确策略。

---

# 二、最强反对意见：`NO_ACCESS` 这一名称在科学上过宽

R52 与 R51 有本质区别。

R51 的整个训练过程中没有出现一次正终局回报；R52 则为所有 specialist 提供了非常充分的 stochastic return carrier：

[
P_{\mathrm{train}}(U>0)
=======================

0.9575\text{--}0.9985.
]

CSV 也显示 specialist 的 stochastic rollout utility 并非只在随机初始化时非零。训练末期仍有：

* (N=2)：batch utility 约 (0.77)；
* (N=3)：约 (0.65)；
* (N=4)：约 (0.53)；
* (N=5)：约 (0.46)；
* (N=6)：约 (0.50)。

与此同时，shared 的 late stochastic utility 接近 (0.95)–(1.00)。

所以不能复用 R51 的结论：

[
\text{“PPO 没有得到 task-return carrier”。}
]

R52 实际观察到的是：

[
\boxed{
\begin{aligned}
&\text{specialist stochastic policy分布拥有正回报质量}\
&\not\Rightarrow
\text{其token-wise greedy projection是高回报joint policy}.
\end{aligned}
}
]

这是本轮最重要的解释修正。

不过，这个反对意见不改变注册分支。M1 明确要求 exact-final deterministic specialists 通过绝对任务门槛；它们全部得到：

[
M=1,\qquad J=0,\qquad U=0.
]

因此：

[
\boxed{\texttt{NO_ACCESS_R52_ARFA_SPECIALISTS}}
]

作为**注册状态**仍然有效。

---

# 三、carrier / final-policy divergence 的因果含义

## 1. PPO 优化的是 stochastic expected return，不是 greedy joint decode

R52 actor 更新使用 sampled trajectories：

[
\nabla_\theta
\mathbb E_{\mathbf a\sim\pi_\theta}
[U(\mathbf a)].
]

最终 evaluator执行的则是：

[
\hat a_{\sigma(j)}
==================

\arg\max_a
\pi_\theta(a\mid \hat a_{\sigma(<j)},s).
]

一般而言：

[
\left(
\arg\max_{a_1}\pi(a_1),
\arg\max_{a_2}\pi(a_2\mid a_1),
\ldots
\right)
]

既不一定是：

[
\arg\max_{\mathbf a}\pi(\mathbf a),
]

也不一定最大化：

[
U(\mathbf a).
]

因此一个stochastic policy可以通过在job actions上保留相当概率质量而获得正期望回报，但每个token的最大logit仍然偏向station action。组合成greedy roster后，所有job均被忽略：

[
M=1,\qquad J=0.
]

R52正是这一情形。

---

## 2. Shared perfect 是重要 diagnostic，但不是已完成的变量团队结论

Shared policy：

* 使用同一model class；
* 使用同一环境；
* 使用同一reward；
* 使用同一deterministic evaluator；
* 对所有 (N) 都得到 (U=1)。

所以它证明：

[
\boxed{
\text{R52 dynamics、observation、model class和greedy decoder}
\text{联合起来能够表达并执行正确策略。}
}
]

它还提供了一个强烈但未识别的机制线索：

[
\text{cross-}N\text{ gradient pooling}
]

可能帮助形成了一个一致的joint mode。

但是shared model完成了625个optimizer steps，而每个specialist只有125步；shared还接触到五种team-size数据分布。因此无法在R52中分离：

* 跨 (N) 的结构迁移；
* 更丰富的状态分布；
* 五倍的单模型optimizer exposure；
* 多任务式正则化。

这些差异是预注册treatment的一部分，不是wiring defect；但它们意味着不能从quarantined结果中直接得出：

[
\text{“parameter sharing导致成功”。}
]

---

## 3. 可复用结论

[
\boxed{
\begin{aligned}
&\text{自然stochastic return carrier}\
&+\text{正确on-policy PPO}\
&+\text{充分的模型容量}\
&\not\Rightarrow
\text{greedy-executable coordinated mode}.
\end{aligned}
}
]

对于可变团队、大动作集合的autoregressive MARL，应当把以下对象分开测量：

1. stochastic expected task value；
2. deterministic executable task value；
3. stochastic-to-deterministic gap；
4. joint action feasibility；
5. duplicate/capacity violation；
6. cross-(N) transfer。

R52 失败的上游对象不再是“有没有reward”，而是：

[
\boxed{
\text{概率质量是否形成一个可执行的联合模式。}
}
]

---

# 四、R52 中可以保留与必须退休的部分

## 可以作为实现基础保留

这些组件已经获得强实现证据：

* N-independent member/entity set encoder；
* focal-current-entity relation；
* active-only autoregressive pointer ledger；
* entity permutation与mask；
* exact prefix teacher forcing；
* recurrent hidden replay；
* token-dimension normalization；
* exact-final checkpoint与paired evaluation infrastructure；
* terminal graded task objective作为环境目标的原则。

它们可以复用为代码基础，但不能继承R52的科学PASS。

## 精确退休

以下组合永久退休：

```text
R52 station/job dynamics
terminal U=min(M,J)
unconstrained duplicate-allowed pointer support
R52 deterministic specialist prerequisite
R52 320K/625-vs-125 comparator result
```

不能通过只改变其中一个结果后敏感项而继续称为R52。

---

# 五、唯一下一路线：R53-RCMA-G0

## 1. 名称与核心对象

[
\boxed{
\textbf{Residual-Capacity Masked Autoregression}
}
]

在每个autoregressive位置，policy不仅看到前序planned counts，而且将**剩余资源容量直接写入有效action support**。

令queue (q) 的单步容量为：

[
c_q^{(0)}=1.
]

第 (j) 个agent选择后：

[
c_q^{(j)}
=========

## c_q^{(j-1)}

\mathbb 1[a_{\sigma(j)}=q].
]

后序token严格mask：

[
\pi(a_{\sigma(j)}=q)=0
\qquad
\text{if }c_q^{(j-1)}=0.
]

因此joint action天然是一组capacity-feasible partial matching，而不是依靠soft prefix feature自行学会避免重复。

其log-probability仍然精确可分解：

[
\log\pi(\mathbf a\mid s)
========================

\sum_{j=1}^{N}
\log
\pi
\left(
a_{\sigma(j)}
\mid
s,a_{\sigma(<j)},\mathbf c^{(j-1)}
\right).
]

Sampling、teacher-forced replay和deterministic decode使用完全相同的动态support。

---

# 六、新任务：Anonymous Multi-Rate Queue Allocation

这不是 R51/R52 maintenance–dispatch 的改名。

## 1. Team size

[
N\in{2,3,4,5,6},
]

episode内固定。

每个episode有：

[
P_N=\left\lfloor\frac N2\right\rfloor
]

个persistent queues，以及：

[
B_N=N+1-P_N
]

个burst queues。

总queue数：

[
K_N=P_N+B_N=N+1.
]

每步有 (N) 个agents和 (N+1) 个queues，所以至少一个queue必须等待，任务不是“一人一任务”的静态匹配。

---

## 2. 时间与到达过程

```text
horizon                 16
persistent arrivals     t = {0,2,4,6,8,10,12,14}
burst waves             t = {3,9}
burst deadline          3 steps
service/queue/step       at most 1 unit
```

每个persistent queue在每个persistent-arrival step增加1个work unit，共8个。

每个burst queue在两个wave各产生1个job，共2个；若未在3步内服务则过期。

Persistent backlog可以跨step累积；burst work过期后不能补做。

这产生两个自然时间尺度：

* 持续到达、允许短期积压的persistent streams；
* 具有短deadline的burst streams。

Actor不接收persistent/burst角色标签；只能从backlog、arrival与deadline过程识别。

---

## 3. Action

每个agent选择一个queue pointer。

在同一step内，一个queue被前序agent选择后，其residual capacity变为0，后序agent不能再选择。

被选queue若有backlog，则服务1个unit；空queue选择只浪费本agent的service opportunity。

不存在：

* agent ID；
* fixed role；
* learned order；
* task-specific intrinsic；
* duplicate penalty；
* switching reward；
* team-size reward。

---

## 4. 终局外部效用

Persistent fulfillment：

[
F_P
===

1-
\frac{
\sum_{p=1}^{P_N}q_{p,16}
}{
8P_N
}.
]

Burst fulfillment：

[
F_B
===

\frac{
#\text{在deadline前服务的burst jobs}
}{
2B_N
}.
]

唯一reward在最后一步：

[
\boxed{
U
=

\sqrt{F_PF_B}.
}
]

其余步骤：

[
r_t=0.
]

这是终局的balanced queue-service objective，不是中间shaping。只服务persistent或只服务burst都会得到：

[
U=0.
]

---

# 七、信息与模型边界

## Queue entity view：7维

```text
active
backlog / 8
new_arrival / 1
deadline_remaining / 3
cumulative_served / cumulative_arrived
expired_fraction
selected_previous_step_count / N
```

## Focal relation：1维

```text
is_previous_queue_for_focal
```

## Dynamic AR field：1维

```text
residual_capacity
```

Persistent/burst类别、queue key、agent ID和oracle priority均不输入actor。

## Model

```text
member encoder: 2 -> 32 -> 32
queue encoder:  7 -> 32 -> 32
GRU hidden:     32
query MLP:      128 -> 64 -> 32
queue key:      34 -> 32
critic:         pooled state -> 64 -> 1
```

Exact parameter count：

[
\boxed{24,737}
]

所有 (N) 使用同一state-dict shape。

复杂度：

[
O(NK_Nd),
\qquad K_N=N+1.
]

不存在：

* (K^N) joint enumeration；
* mandatory agent-agent (N^2) tensor；
* post-hoc beam search；
* task reward参与action mask。

---

# 八、比较和曝光合同

## Treatment

```text
shared_variable_N_RCMA
```

一套参数训练全部 (N)。

## Comparator

```text
fixed_N_RCMA_specialist_family
```

五个架构、初始化和动态capacity support完全相同的specialists。

Shared与对应specialist逐batch共享：

* reset/arrival ledger；
* queue presentation order；
* external agent order；
* sampling uniforms；
* transition数；
  -每个 (N) 的optimizer exposure。

## 固定曝光

```text
experiment                    R53-RCMA-G0
balanced cycles               100
N-specific batches/cycle      5
parallel episodes/batch       16
episode / rollout             16 / 16
batches/N                     100
batches/arm                   500
episodes/N/arm                1,600
transitions/N/arm             25,600
transitions/arm               128,000
agent-token decisions/arm     512,000
PPO epochs                    1
shared optimizer steps        500
specialist steps/model        100
specialist aggregate          500
zero-step evaluation          128 episodes/N/arm
final stochastic evaluation   128 episodes/N/arm
final deterministic eval      128 episodes/N/arm
bootstrap repetitions         10,000
```

固定seeds：

```text
model/init          53053
training arrivals   63053
orders/actions      73053
evaluation          83053
bootstrap           93053
```

PPO继续使用：

```text
gamma               0.99
GAE lambda           0.95
learning rate        3e-4
PPO epochs           1
entropy coefficient  0.01
value coefficient    0.5
clip                  0.2
gradient clip         0.5
```

---

# 九、最小 abandonment gate

## M0：实现有效性

必须全部满足：

1. (P_N,B_N,K_N) 与公式一致；
2. persistent与burst arrival counts逐episode精确；
3. burst expiration后不能补服务；
4. 每个queue每step有效service最多1；
5. dynamic residual-capacity mask使一个queue每step最多被一个agent选择；
6. constructive schedule对所有 (N) 产生：
   [
   F_P=F_B=U=1;
   ]
7. persistent-only和burst-only schedules均产生 (U=0)；
8. 所有中间reward严格为0；
9. terminal reward逐episode严格等于 (\sqrt{F_PF_B})；
10. actor无ID、slot、queue-type role或oracle priority；
11. shared与specialists初始参数逐位相同；
12. exact 128K transitions/arm和500/100 optimizer steps；
13. PPO epoch 1，无batch reuse；
14. stochastic sample/replay、dynamic mask、prefix和hidden误差：
    [
    \le10^{-6};
    ]
15. masked probability mass为0；
16. relevant modules均有有限非零梯度和parameter drift；
17. exact-final checkpoint reload误差为0。

失败：

```text
INVALID_R53_RCMA_WIRING
```

唯一动作是修复明确的transition、capacity support、reward、replay、count或checkpoint defect，并原合同重跑。

---

## M1：specialist access与mode transport

每个 (N) 必须同时满足：

### 训练carrier

[
P_{\mathrm{train}}(U>0)\ge0.50.
]

### Final stochastic policy

[
\bar U^{spec,stoch}_N\ge0.70.
]

### Final deterministic policy

[
\bar U^{spec,det}_N\ge0.65,
]

[
\bar F^{spec,det}*{P,N}\ge0.70,
\qquad
\bar F^{spec,det}*{B,N}\ge0.70.
]

### Stochastic-to-deterministic transport

[
\operatorname{UCB}_{95}
\left[
U^{spec,stoch}_N-U^{spec,det}_N
\right]
<0.15.
]

### Learning与稳定性

[
\operatorname{LCB}*{95}
\left[
U^{spec,det}*{N,\mathrm{final}}
-------------------------------

U^{spec,det}_{N,\mathrm{zero}}
\right]

> 0.15.
> ]

四个连续32-episode deterministic blocks中，至少三个满足：

[
\bar U^{spec,det}_{N,\mathrm{block}}\ge0.60.
]

Equal-(N) deterministic macro：

[
\bar U^{spec,det}\ge0.70.
]

若M0通过但M1失败：

```text
NO_ACCESS_R53_RCMA_SPECIALISTS
```

唯一动作：

> 永久退休精确AMQA dynamics、terminal utility、residual-capacity action support和mode-transport gate；隔离shared结果。

不允许增加数据、entropy、epochs、model、beam search或改变capacity。

---

## M2：shared variable-(N)

Shared每个 (N) 要求：

[
\bar U_N^{shared,stoch}\ge0.70,
]

[
\bar U_N^{shared,det}\ge0.65,
]

[
\bar F_{P,N}^{shared,det},
\bar F_{B,N}^{shared,det}\ge0.70.
]

Mode-transport gap：

[
\operatorname{UCB}_{95}
[
U_N^{shared,stoch}-U_N^{shared,det}
]
<0.15.
]

Deterministic macro：

[
\bar U^{shared,det}\ge0.70.
]

相对specialists：

[
\min_N
\frac{
\bar U_N^{shared,det}
}{
\bar U_N^{spec,det}+10^{-8}
}
\ge0.85,
]

[
\frac{
\bar U^{shared,det}
}{
\bar U^{spec,det}+10^{-8}
}
\ge0.90.
]

Paired macro noninferiority：

[
\operatorname{LCB}_{95}
\left[
\frac15\sum_N
\left(
U_N^{shared,det}
----------------

U_N^{spec,det}
\right)
\right]

> -0.08.
> ]

Shared final-minus-zero：

[
\operatorname{LCB}*{95}
[
\bar U*{\mathrm{final}}^{shared,det}
------------------------------------

\bar U_{\mathrm{zero}}^{shared,det}
]

> 0.20.
> ]

若M0、M1通过而M2失败：

```text
VALID_FAIL_R53_SHARED_VARIABLE_N
```

唯一动作：

> 永久退休精确shared RCMA contract，并停止当前variable-(N) learning line，进行一次架构失败审查。

---

## PASS

```text
PASS_R53_RCMA_VARIABLE_N
```

仅当：

[
M0\land M1\land M2.
]

唯一下一动作：

> 在同一个AMQA、相同RCMA policy和相同terminal utility下，注册一次within-episode **exogenous join/leave 与 membership-censoring gate**。

不授权：

* skill latent；
* KEEP/SET；
* variable lifetime；
* intrinsic reward；
* learned admission；
* S7/UAV transfer；
* field-slot/mean-field并行路线；
  -论文novelty。

---

# 十、最强反对意见

[
\boxed{
\text{Residual-capacity mask把“一队列最多一名server”}
\text{直接写进action support，可能被视为硬编码anti-coordination。}
}
]

这个反对意见成立，并限制未来claim。

R53即使PASS，也只能说明：

> 当资源具有已知、可观测的排他容量约束时，将该约束写入autoregressive support，可以形成随 (N) 扩展且greedy-compatible的联合策略。

它不能证明：

* 所有多智能体协调都能转化为capacity masking；
* 适用于需要多agent共同服务同一目标的任务；
* 已解决一般UAV协作；
* 已解决 (k) 或skill lifetime。

但这不改变推荐。Capacity mask属于已知action feasibility，而不是reward shaping；它不告诉policy“哪个queue更重要”，只排除物理上无增益的重复占用。R52的主要未闭合边恰好是：

[
\text{高价值stochastic质量}
\not\rightarrow
\text{coherent deterministic joint mode}.
]

RCMA是对此最小且直接的结构性修复。

---

# 十一、永久禁止的路线和救援

以下全部保持关闭：

* 重新运行R52；
* 给R52 specialists增加到625 steps/model；
* PPO epochs由1改为5；
  -降低R52 M1阈值；
  -用R52 stochastic training utility替代注册的deterministic gate；
  -对R52 final checkpoint做temperature、beam search、joint-MAP或best-checkpoint选择；
  -把R52 shared perfect结果升级为variable-(N) PASS；
  -修改R52 entropy或evaluation rule；
  -重开R51或R50；
  -任何R29–R48 skill、renewal、spectral、classifier或hidden-reset路线；
  -环境特定intrinsic reward或中间shaping；
  -agent ID、slot-specific head、learned agent order；
  -learned admission；
  -在R53同时加入mean-field、field slots、可变 (k) 或skill lifetime；
  -通过追加seed、预算、model width、阈值或reward挽救R53有效失败。

实验纪律要求有效失败只能通过新的因果对象继续，而不能事后修改门槛或优化曝光。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\texttt{R52 status = CONFIRMED NO ACCESS};\
&\text{没有branch-changing wiring defect；}\
&\text{注册的deterministic specialist gate失败，}\
&\quad\text{但stochastic task-return carrier真实存在；}\
&\text{可复用结论是stochastic-return learning}\
&\quad\not\Rightarrow\text{greedy joint-mode transport};\
&\text{shared perfect仅为diagnostic，继续quarantine；}\
&\text{精确R52 task/comparator永久退休；}\
&\text{唯一下一路线为R53-RCMA-G0，}\
&\quad\text{以residual-capacity action support}\
&\quad\text{形成greedy-compatible variable-}N\text{ joint policy};\
&\text{任一有效M1或M2失败均永久退休精确路线，}\
&\quad\text{不得通过调参、扩种子、改阈值或改reward救援。}
\end{aligned}
}
]
