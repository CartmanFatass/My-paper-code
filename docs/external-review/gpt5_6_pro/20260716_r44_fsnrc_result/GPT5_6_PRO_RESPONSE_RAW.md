# 裁决

[
\boxed{\texttt{CONFIRM VALID_FAIL_R44_FSNRC}}
]

[
\boxed{\texttt{ANALYZER CORRECTION VALID}}
]

[
\boxed{
\texttt{RETIRE EXACT R44 NEXT-CHECK CREDIT}
;\text{，但不推广为所有异步 renewal 失败}
}
]
唯一下一条路线为：

[
\boxed{
\textbf{R45-SDRA：
Sequential Doubly-Robust Renewal Advantage}
}
]

其首先执行一个 **reward-off、natural-support renewal-credit identifiability gate**。在该 gate 通过以前，不允许再次更新 renewal actor。

---

# 1. Validity verdict

## 1.1 `VALID_FAIL_R44_FSNRC` 成立

R44 的正式结果满足：

[
M0=\text{PASS},\quad
M1=\text{PASS},\quad
M2=\text{PASS},\quad
M3=\text{FAIL}.
]

具体为：

* 两臂都从 R41B seed-1 exact-final checkpoint 开始；
* 每臂完成 320,000 environment steps、200 outer updates、6,400 environment-check rows；
* 每臂 factor optimizer 恰好执行 3,000 步；
* 五个 source optimizer 路径全部为 0 步；
* control 和 treatment 的确定性 win/key0/key1 都为 `0.93/1.00/0.93`；
* treatment-minus-control win CI 为 `[0,0]`；
* treatment renewal actor 相对漂移为 `0.353245`，且 3,000/3,000 次 actor gradient exposure 非零；
* 但 treatment 的确定性 discordance 为 0、full-sync RENEW 为 1、最小 KEEP/RENEW marginal 为 0。

因此 registered branch 必须是：

```text
VALID_FAIL_R44_FSNRC
```

而不是 `PASS`、`INVALID` 或 `UNDERPOWERED`。

---

## 1.2 Analyzer correction 忠于预注册 M0

第一次 analyzer 错误地要求 renewal critic 在全部 3,000 次 optimizer step 上都必须产生非零梯度。预注册合同实际要求的是：

* 3,000 次 gradient checks 全部有限；
* critic 至少存在一次非零 gradient exposure；
* critic 参数确实发生变化。

修正后的 analyzer 保留了：

```python
critic_gradient_checks == 3000
critic_all_gradients_finite is True
critic_nonzero_steps > 0
```

而没有要求：

```python
critic_nonzero_steps == 3000
```

这与正式 R44 M0 合同一致。control critic 为 3,000/3,000 次非零，treatment critic 为 2,992/3,000 次非零，但所有 3,000 次检查均有限；只有 analyzer 被重跑，训练产物、阈值和科学指标均未修改。

所以该修正是：

[
\boxed{\text{修复 analyzer 对既有合同的误实现}}
]

而不是结果后的阈值放宽。

---

## 1.3 没有改变 branch 的实现缺陷

实现审计支持以下事实：

* source MAT、low actor、low critic、(q_D)、(q_d) 全部 `requires_grad=False`；
* treatment 唯一可训练的行为参数是 renewal actor；
* 两臂均训练相同 renewal critic；
* factor optimizer 只包含 renewal actor/critic；
* source 参数、五个 source optimizer state 以及 source normalizer 状态均保持零漂移；
* conditional-skill ratio 最大偏差为 0；
* high/factor/low replay error 均为 0；
* working-prefix mismatch 为 0；
* auto-reset 没有产生额外 high action，也没有改变 roster、team skill 或 age；
* control 的 zero-step 与 final outcomes、high traces、low traces逐项完全一致。

我没有发现会把结果改判为 `INVALID` 的：

* factorization defect；
* likelihood/replay defect；
* freeze defect；
* reset/clock defect；
* checkpoint defect；
* evaluator defect；
* source-gradient leakage；
* analyzer branch defect。

---

# 2. 可复用的机制结论

必须把五个不同对象分开。

| 对象                              | R44 结论                |
| ------------------------------- | --------------------- |
| actor connectivity              | **已建立**               |
| renewal-credit estimator 的异质信息量 | **未建立，且有负面迹象**        |
| stochastic policy movement      | **存在，但朝更同步 RENEW 移动** |
| deterministic transport         | **不存在**               |
| task service                    | **被完整保留，但无增益**        |

## 2.1 Actor connectivity 已建立

Treatment renewal actor：

* 3,000/3,000 次 gradient exposure 非零；
* gradient 全部有限；
* relative parameter drift 为 `0.353245`；
* max parameter change 为 `0.210313`；
* source gradient tensor 数量为 0。

因此失败不能解释为：

[
\text{renewal actor 没有梯度}
]

或：

[
\text{optimizer 没有真正更新它}.
]

---

## 2.2 Stochastic policy 确实移动，但方向不是 temporal decoupling

训练期 stochastic occupancy 显示：

### Control

[
\text{KEEP count}=298+312=610,
]

[
\text{discordant}=160/6384\approx 0.025,
]

[
\text{full-sync RENEW}=5999/6384\approx0.940.
]

### Treatment

[
\text{KEEP count}=110+125=235,
]

[
\text{discordant}=89/6384\approx0.014,
]

[
\text{full-sync RENEW}=6222/6384\approx0.975.
]

也就是说，actor drift 并非完全行为无效；描述性地看，它把随机策略推向了：

[
\boxed{
\text{更少 KEEP、更少 discordance、更多全同步 RENEW}
}
]

而不是推向异步 lifetime。由于两臂在 actor 学习后经历不同 stochastic trajectories，这些训练计数不能被当作严格 paired causal effect，但它们足以否定“参数虽然漂移、分布完全没动”的解释。

---

## 2.3 Deterministic transport 不存在

最终确定性 evaluation 中，两臂：

* win、key0、key1 完全相同；
* episode lengths 完全相同；
* high action traces 完全相同；
* low primitive-action traces 完全相同；
* 每个 eligible check 都是双 agent RENEW；
* discordance 为 0；
* full-sync RENEW 为 1；
* 每个 agent 的 KEEP mass 为 0。

因此：

[
\boxed{
\text{参数变化}
\not\Rightarrow
\text{可执行策略变化}
}
]

更不能推出 temporal abstraction、skill semantics 或 cooperation。

---

## 2.4 Service 被保留，但不能算算法收益

两臂都得到：

[
0.93/1.00/0.93,
]

且 treatment-minus-control win CI 为：

[
[0,0].
]

这证明 frozen-source comparator 修复了 R43 中的 continuation instability，也证明 renewal actor 的训练没有破坏既有服务。但 treatment 没有改变执行轨迹，所以这一 service equality 不是“异步策略在保持服务的同时工作”，而是：

[
\boxed{
\text{异步机制没有进入最终执行策略}
}
]

---

## 2.5 R44 estimator 的异质 renewal 信息量没有建立

R44 对每个 agent 使用同一 team block return：

[
G_\tau
======

\sum_{r=0}^{49}
\gamma^r r^{env}*{t*\tau+r},
]

实现中通过：

```python
repeated_rewards = np.repeat(
    block_returns[:, :, None],
    runner.num_agents,
    axis=2,
)
```

复制给所有 agent。renewal critic 输出的是 action 前的 state/context value，而不是：

[
Q_i(c_i,\texttt{KEEP})
\quad\text{与}\quad
Q_i(c_i,\texttt{RENEW}).
]

renewal actor 随后用 sampled return 减 state-value baseline 的 PPO advantage 更新。

这在理论上仍是合法的 on-policy policy-gradient estimator，所以不能说它“恒零”或“数学上错误”。但 R44 没有证明该 estimator 能辨认：

[
\text{同一自然 context 下 KEEP 与 RENEW 的差分任务价值}.
]

现有结果同时兼容两种解释：

1. next-check shared return 主要提供 common-mode/synchronizing credit；
2. Alice–Bob 在 (t=50) 确实几乎总是偏好全员同步 renewal。

R44 本身不能区分这两者。

---

# 3. Retirement boundary

## 3.1 确认永久退休的精确对象

永久退休：

[
\boxed{
\begin{aligned}
&\text{冻结 R41B skill system}\
&+\text{source-exact binary KEEP/RENEW residual}\
&+\text{action-independent renewal value baseline}\
&+\text{共享 next-50 external-return PPO credit}\
&+\text{Alice--Bob }K=50
\end{aligned}
}
]

以及同一对象的：

* learning-rate 变化；
* entropy 或 temperature 变化；
* seed 替换；
  -更多 steps；
  -阈值放宽；
* best-checkpoint selection；
* source unfreeze 作为“R44 rescue”；
  -额外 KEEP/lifetime/switch reward。

正式 disposition 已经注册了这一 retirement。

## 3.2 必须收窄的泛化

R44 不支持退休：

* 所有 action-conditional renewal credit；
* 所有 option/termination value learning；
* 所有 joint co-adaptive skill-and-renewal learning；
* 所有 asynchronous lifetime；
* 所有 (K=50) 控制器；
* S7、open roster 或 variable-(N) 的科学假设。

因此更准确的结论是：

[
\boxed{
\text{退休 shared-return/state-value 的 R44 estimator，}
\quad
\text{而不是退休 renewal 问题本身。}
}
]

---

# 4. 唯一下一条因果边：R45-SDRA

## 4.1 要修复的失败边

R44 失败边为：

[
\boxed{
\text{shared next-check return}
\not\Rightarrow
\text{agent/context-specific renewal advantage}
}
]

R45 测试：

[
\boxed{
\begin{aligned}
&\text{自然 source-exact renewal 随机化}\
&\rightarrow
Q_i(c_i,\texttt{KEEP}),Q_i(c_i,\texttt{RENEW})\
&\rightarrow
\text{cross-fitted action-conditional renewal advantage}\
&\rightarrow
\text{可辨识的正负 renewal-value 异质性}
\end{aligned}
}
]

本轮首先只做 reward-off identifiability gate，不更新 renewal actor。

---

## 4.2 为什么这不是 R44 rescue

R45 不修改：

* R44 actor 学习率；
* entropy；
* temperature；
* seed；
* evaluation mode；
* service margin；
* decoupling threshold；
* duration/action space；
  -训练 budget 来重新判 R44。

它改变的是**信用 estimand**：

### R44

[
A_i^{R44}
=========

\operatorname{GAE}
\left(
G_\tau,,
V_i(c_i)
\right).
]

### R45

[
\Delta_i(c_i)
=============

## Q_i(c_i,\texttt{RENEW})

Q_i(c_i,\texttt{KEEP}).
]

所以它不是“让同一个 actor 更容易探索”，而是首先检查：

> natural on-policy support 中是否存在可识别、方向随 agent/context 变化的 renewal treatment value。

---

# 5. R45-SDRA 的精确算法合同

## 5.1 Policy factorization

数据由冻结的 source-exact renewal policy 产生：

[
\begin{aligned}
\mu(
Z,\mathbf b,\mathbf z^+
\mid x,\mathbf z^-
)
&=
\pi_Z^{R41B}(Z\mid x)\
&\quad
\prod_{j=1}^{N}
\mu_j(b_{\sigma(j)}\mid c_j)
\left[
\pi_S^{R41B}
(z_{\sigma(j)}^+\mid c_j,b_{\sigma(j)}=R)
\right]^{\mathbb 1[b_{\sigma(j)}=R]} .
\end{aligned}
]

其中：

* (\sigma=(1,2)) 保持 canonical autoregressive order；
* team (Z) policy 冻结；
* conditional non-incumbent skill policy 冻结；
* renewal actor residual 固定为零；
* 每个 binary action 的真实 propensity

[
e_i(c_i)=\mu_i(R\mid c_i)
]

被逐 row 存储。

对 agent 1，(Q_1) 包含后序 agent 2 按冻结策略响应的总效应；对 agent 2，其 context 已包含 agent 1 应用后的 working prefix。

---

## 5.2 时间与 reset

完全保持 R43/R44 已验证语义：

* global check 为 (k_0=50)；
* 每个 training environment 整个 run 只有一次 structural assignment；
* 后续 checks 都是正常 KEEP/RENEW；
* auto-reset 不产生 high action；
* roster、team skill、age 和 assignment spell 跨 auto-reset；
* low actor/critic hidden 在 reset 时清零；
* outcome 跨 reset 累积至同一个 50-step controller block；
* update boundary截断数据版本，但不制造额外 action。

---

## 5.3 Information boundary

Critic context 使用与 R44 相同的 148 维通用 controller context：

[
c_i=
[
\text{detached source global representation},
\text{detached focal representation},
Z,
\text{working roster},
\text{age},
\text{focal position},
\text{active mask}
].
]

禁止显式加入：

* key/diamond/goal identity；
* contact；
* task phase；
* success predicate；
* reward history；
  -到目标距离；
* oracle role；
* future outcome。

外部回报只作为 supervised return target，不作为 critic input，也不成为 intrinsic reward。

---

## 5.4 Credit estimand

Outcome 仍是外部任务回报：

[
G_\tau
======

\sum_{r=0}^{49}\gamma^r r^{env}*{t*\tau+r}.
]

定义：

[
Q_i^\mu(c,b)
============

\mathbb E_\mu
[
G_\tau
\mid
C_i=c,\ B_i=b
].
]

由于 (B_i) 是在已完整记录的 canonical context/prefix 下，由已知 propensity 随机采样，R45 可在有 overlap 的自然支持上估计该 sequential action value；不使用 simulator clone、forced branch 或 `do(z)` rollout。

Cross-fitted doubly robust score为：

[
\boxed{
\begin{aligned}
\psi_i
&=
\hat Q_i(c,R)-\hat Q_i(c,K)\
&\quad+
\frac{\mathbb 1[b=R]}{e_i(c)}
\left(
G-\hat Q_i(c,R)
\right)\
&\quad-
\frac{\mathbb 1[b=K]}{1-e_i(c)}
\left(
G-\hat Q_i(c,K)
\right).
\end{aligned}
}
]

该 score 用于 reward-off gate 的 held-out causal read。

若 gate 以后通过，唯一允许的 actor advantage 是：

[
A_i^{SDRA}(c,b)
===============

## \hat Q_i(c,b)

\sum_{b'}
\pi_B(b'\mid c)\hat Q_i(c,b'),
]

并且整个 (Q) 路径 detached。当前 gate 不执行这一步。

---

## 5.5 Updated 与 frozen 参数

当前 reward-off gate 中：

### 冻结

```text
source MAT encoder/decoder
source team-Z policy
source conditional skill policy
source high value
low actor
low critic
q_D
q_d
all source optimizers
high/low ValueNorm
renewal actor
```

### 更新

仅更新四个 cross-fit critic：

```text
fold-A true-action Q
fold-B true-action Q
fold-A action-blind sham
fold-B action-blind sham
```

每个 critic：

```text
148 -> 32 GELU -> 2 action values
```

---

## 5.6 Mechanism-matched comparator

### Real：`sdra_true_Q`

网络输出：

[
q_K(c),q_R(c),
]

训练 prediction 为：

[
q_{b}(c).
]

### Null：`sdra_action_blind`

使用完全相同的网络、初始化规则、optimizer、数据和 step 数，但 prediction 固定为 behavior mixture：

[
v(c)
====

(1-e(c))q_K(c)+e(c)q_R(c),
]

与实际 sampled action 无关。

因此 real 与 null 的唯一区别是：

[
\boxed{
\text{是否允许 outcome 依赖当前 renewal action}
}
]

而不是模型容量、context 或训练 exposure。

---

# 6. 最小 Alice–Bob abandonment gate

## 6.1 固定合同

```text
experiment                  R45-SDRA-G0
source checkpoint           R41B seed-1 exact-final
environment/action seed     43041
rollout environments        16
outer updates               100
environment steps           160,000
global checks               3,200 env-check rows
structural rows              16
normal rows                  3,184
normal agent-factor rows     6,368
source optimizer steps       0
renewal-actor steps          0
critic folds                 env ranks 0-7 / 8-15
critic arms                  true-Q / action-blind sham
critic architecture          148 -> 32 -> 2
epochs per critic            15
minibatch                    256, drop_last=False
optimizer steps/model        195
total critic steps           780
optimizer                    Adam, lr 5e-4, eps 1e-5
evaluation                   100 deterministic episodes
bootstrap repetitions        10,000
bootstrap seed               62045
```

160K 不是对 R44 的缩短重跑。R44 保持永久失败；该预算只收集 reward-off action-support data。若数据支持不足，没有扩展 budget 分支。

---

## 6.2 Cross-fitting

固定按 environment rank 划分：

```text
fold A: env 0..7
fold B: env 8..15
```

* A 训练的 critic 只评分 B；
* B 训练的 critic 只评分 A；
* input normalization 只用各自 training fold；
* held-out fold 不参与模型选择、early stopping 或 normalization；
* 不进行超参数选择。

---

## 6.3 M0：实现与数据合同

必须全部满足：

1. source checkpoint、环境、(k_0)、reward、observation 与 R44 一致；

2. source modules、source optimizers、ValueNorm 和 renewal actor最终零漂移；

3. source optimizer与 renewal-actor optimizer steps均为 0；

4. source-exact probability error、stored/replayed binary logp error：

   [
   \le10^{-6};
   ]

5. working-prefix mismatch 为 0；

6. propensity 与实际 sampled action一一对应；

7. 恰好 160K steps、3,200 check rows、16 structural rows；

8. auto-reset high action 为 0；

9. return严格等于 next-50 external reward；

10. true/null critic架构与 optimizer exposure完全相同；

11. 每个模型恰好195次 optimizer step；

12. train/held-out environment无交叉；

13. 所有 critic gradients、predictions、propensities、weights和 DR scores有限；

14. 无 task field、shaping、intrinsic、forced branch 或 actor update；

15. frozen source 100-episode deterministic evaluation满足 zero/final exact trace equality。

任一失败：

```text
INVALID_R45_SDRA_WIRING
```

只修复具体数据、split、likelihood、freeze或critic实现错误，并原合同重跑。

---

## 6.4 M1：source service 与 natural overlap

必须同时满足：

[
W_{\mathrm{source}}\ge0.80,
]

[
K0_{\mathrm{source}},K1_{\mathrm{source}}\ge0.85.
]

并对每个 agent、每个 action：

[
ESS_{i,b}
=========

\frac{(\sum_j w_j)^2}{\sum_j w_j^2}
\ge64,
]

其中：

[
w_j=\frac{1}{\mu_i(b_j\mid c_j)}.
]

此外任何单个 environment cluster 不得贡献超过对应 action 总 stabilized weight 的 10%。

没有 propensity clipping、补样本或 forced action；overlap 不足即 scientific FAIL。

---

## 6.5 M2：action-specific credit informativeness

在 cross-fitted held-out rows 上要求：

[
\operatorname{LCB}*{95}
\left[
WMSE*{\mathrm{sham}}
--------------------

WMSE_{\mathrm{trueQ}}
\right]

> 0.
> ]

再按 predicted：

[
\hat\Delta_i(c)
===============

\hat Q_i(c,R)-\hat Q_i(c,K)
]

分成 top/bottom quartiles，并要求：

[
\operatorname{LCB}*{95}
\left[
\bar\psi*{\mathrm{top}}
-----------------------

\bar\psi_{\mathrm{bottom}}
\right]

> 0.
> ]

这两个条件分别否决：

* action-conditioned critic只是在拟合 context；
* predicted renewal advantage不能排序真实 held-out effect。

---

## 6.6 M3：可用于异步 renewal 的 sign heterogeneity

对两个 agent分别要求：

[
\operatorname{LCB}*{95}
[
\bar\psi*{i,\mathrm{top25%}}
]

> 0,
> ]

[
\operatorname{UCB}*{95}
[
\bar\psi*{i,\mathrm{bottom25%}}
]
<0.
]

同时，在同一个自然 check 的两个 focal rows中：

[
P
\left[
\operatorname{sign}(\hat\Delta_1)
\ne
\operatorname{sign}(\hat\Delta_2)
\right]
\ge0.20,
]

且 cluster-bootstrap：

[
\operatorname{LCB}_{95}>0.10.
]

这才说明自然支持中存在“一个 agent 应 KEEP、另一个应 RENEW”的可辨识任务价值，而不是仅有全队共同的 phase-switch 信号。

---

## 6.7 互斥分支

### `PASS_R45_SDRA_IDENTIFIABILITY`

要求：

[
M0\land M1\land M2\land M3.
]

允许结论仅为：

> 在冻结 R41B 的自然 source-exact renewal 支持上，存在稳定、action-specific、方向随 agent/context 改变的 renewal value signal。

唯一下一动作：

> 使用 detached cross-fitted (A_i^{SDRA}) 做一个 mechanism-matched renewal-actor pair。

仍不能进入 S7、open roster 或 variable (N)。

### `VALID_FAIL_R45_SDRA_IDENTIFIABILITY`

M0 有效，但 M1、M2 或 M3 任一失败。

永久退休：

* Alice–Bob (K=50) 上的 natural-support SDRA renewal-credit route；
* 在该 substrate 上继续训练任何 renewal actor；
* 通过 critic容量、更多数据、propensity clipping、阈值或 seed变化挽救。

允许结论：

> Alice–Bob 的自然 source policy support 没有提供足以识别异质 KEEP/RENEW 价值的证据。

这将退休 Alice–Bob 作为异步 temporal-mechanism substrate，而不是退休一般异步技能学习。

不存在 `UNDERPOWERED` 或自动扩展分支。

---

# 7. R41B–R44 的联合 evidence boundary

## 已建立

### R41B

原始 HMASD source 在 Alice–Bob 上确实建立了 fixed-(k) cooperative access：

[
0.89/0.97/0.92,
]

zero-step win 为 0，且 paired gain CI 严格为正。

### R42

Incumbent-conditioned skill-logit residual 可以移动策略，但：

* service 明确退化；
* temporal decoupling不足；
* full-sync SET仍为0.9；
  -一个 agent没有KEEP mass。

因此 R42 已永久退休。

### R43

True renewal factorization、reset-censored clock、separate factor replay和梯度路径均机械可行；但 fixed full-stack continuation丢失 anchor，treatment不能作科学解释。

### R44

冻结 source 后：

* 服务 anchor稳定；
* renewal actor可训练且策略概率有所移动；
* source遗忘被排除；
* 但最终策略与完整轨迹完全不变；
* next-check renewal credit没有形成 temporal decoupling。

---

## 尚未建立

这些结果均不证明：

* asynchronous skills 不能共同适应；
  -自然 skill semantics 已经形成；
  -process-level intrinsic loop 不存在；
  -HMASD-like sparse exploration 已被重建；
  -S7 transfer 失败；
  -open roster 或 variable team number 失败；
  -动态成员与 variable lifetime 不兼容。

尤其是，R44 没有测试：

[
\boxed{
\text{skill semantics}
+
\text{low executor}
+
\text{renewal timing}
\quad
\text{联合适应}
}
]

而 R45 当前只检查更上游的 renewal-credit identifiability。

---

# 8. Prohibitions 与最强反对意见

## 继续禁止

不得通过以下方式重开 R42–R44：

-换 seed；
-增加 seed；
-增加 steps；
-改 service/discordance门槛；
-entropy或temperature；
-learning-rate sweep；
-best checkpoint；
-renewal/KEEP/lifetime reward；
-switch penalty；
-duration-category action；
-task shaping；
-task-specific intrinsic；
-goal/key/diamond/contact/phase/distance字段；
-R42 residual改名；
-R43/R44 checkpoint继续训练；
-S7 promotion；
-open-roster promotion；
-variable-(N) 实现。

R45 也不得使用 forced renewal branch、simulator clone 或已经退休的 direct-effect policy gradient。

---

## 最强反对意见

最强反对意见是：

[
\boxed{
\text{Alice--Bob 任务本身可能真实偏好在 }t=50
\text{ 同步切换全部 skills。}
}
]

如果如此，即使一个完美的 renewal-credit estimator也应得到：

[
\Delta_1(c)>0,
\qquad
\Delta_2(c)>0
]

并选择全同步 RENEW。此时 R44 的 deterministic collapse并不是 optimization error，而是任务的真实最优结构。

这个反对意见不改变 R44 verdict，也不授权调参。它正是选择 R45 reward-off identifiability gate 的理由：

* 若 R45发现稳定正负异质 renewal value，则 R44失败可定位到 credit estimator；
* 若 R45没有发现，则应停止把 Alice–Bob 当作异步 lifetime 正 substrate。

两种结果都可证伪，并且都不会篡改 R44 的既有负结果。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\texttt{R44 = VALID_FAIL};\
&\text{analyzer correction 合法，未发现 branch-changing defect};\
&\text{renewal actor 可训练，随机分布有所移动，}\
&\quad\text{但移动方向更同步，且无 deterministic transport};\
&\text{永久退休 R44 shared-next-check-return estimator};\
&\text{唯一下一边为 R45-SDRA reward-off identifiability};\
&\text{先证明自然支持中存在 action-specific、sign-changing}\
&\quad\text{renewal value，再允许任何 actor update};\
&\text{有效 FAIL 即退休 Alice--Bob K50 的该 credit/substrate，}\
&\quad\text{不调参、不扩数据、不进入 S7 或 variable team。}
\end{aligned}
}
]
