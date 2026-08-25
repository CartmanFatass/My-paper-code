# 裁决

[
\boxed{\texttt{CONFIRM_SOURCE_CLOCK_CONTRADICTION}}
]

[
\boxed{
\texttt{MODIFY R43-NRC}
;-;
\texttt{PRESERVE SOURCE-GLOBAL CLOCK}
}
]

唯一保留的实现路线是：

[
\boxed{
\textbf{R43-NRC with reset-censored controller time}
}
]

即：

> 保留原始 HMASD 的全局 (k_0=50) 高层时钟；环境在两个高层检查之间自动 reset 时，不产生新策略动作，而是把 reset 记为当前高层承诺中的外生 censoring boundary。

不采用“每次环境 reset 都强制 initial RENEW”，也不退休 R43 Alice–Bob gate。

---

# 一、矛盾裁决：source reading 正确

原始环境在两个目标都完成时立即返回 `done=True`，而不必等到第 100 步。

`ShareSubprocVecEnv` worker 收到该 `done` 后，会立刻调用 `env.reset()`，但向 runner 返回的仍是终止 transition 的 reward、done 和 info；只有 observation、shared observation 和 available actions 已经替换成新环境 episode 的初始值。

与此同时，Alice–Bob runner 只在一个 100-step outer rollout 的全局 primitive indices `0` 和 `50` 采样高层动作。局部变量 `team_skill` 和 `indi_skill` 会在其间持续复用，不会因为某个 vector worker 自动 reset 而重新采样。

高层 reward 也不是按真实环境 episode 关闭，而是继续累积到全局 step 49 或 99，再写入对应高层 row。 高层 buffer 的长度明确是：

[
100/50=2
]

行，而不是每发生一次环境终止就增加一行。

因此代码中的：

```python
for episode in range(episodes):
```

实际遍历的是 **outer rollout/update index**，不是 vector worker 内部真实环境 episode。一个 outer rollout 内可以完成并自动 reset 多个环境 episode。

R42 fixed arm 的结果与该读取一致：最终评估平均 episode 长度只有 `58.56`，win rate 为 `0.98`；也就是 100 个 episode 中有 98 个在 100 步以前完成。

所以此前同时要求：

1. source-global 两行高层时钟；
2. 每个环境 reset 强制 initial RENEW；
3. reset 关闭旧 skill event；
4. 仍保持固定两行 buffer 和 3,000 source optimizer steps；

在数学和实现上确实互不兼容。

---

# 二、可复用的因果结论

[
\boxed{
\text{环境 episode 终止}
\not\Rightarrow
\text{高层策略动作终止}
}
]

更一般地：

> 在自动 reset 的 vectorized MARL collector 中，一个 `done` 只有在它同时触发新的策略采样时，才是该策略因子的 action boundary。若策略动作在 reset 后继续控制行为，则 reset 对该高层动作是 censoring，而不是新的决策或新的 likelihood owner。

因此不能根据环境 episode 边界虚构一个没有被采样的 initial skill action。否则：

* post-reset 行为没有真实 stored log-probability；
* segment credit 被分配给不存在的动作；
* action count、optimizer exposure 和 comparator 都会改变；
* “variable lifetime”可能只是 collector reset 的副产品。

R43 的正确时间对象必须是：

[
\boxed{
\text{controller-time skill commitment}
\neq
\text{environment episode}
}
]

---

# 三、唯一 reset 语义：保留 source-global high clock

定义连续的 controller checks：

[
c_n=50n.
]

检查时钟不因环境 `done`、成功、自动 reset 或 outer-update index 变化。

## 3.1 三类边界

### A. 整个训练 collector 第一次初始化

此时没有 incumbent：

[
z_i^-=\varnothing.
]

所有 agent 执行 structural initial RENEW：

* 不采样 renewal factor；
* 不产生 renewal log-probability；
* 从原始 (K=4) 个 skill labels 中采样；
* age 初始化为 0。

这在每个 training environment 的整个 R43 run 中只发生一次，而不是每个 outer rollout 一次。

### B. 正常全局检查

包括：

* outer rollout 内的 step 50；
* 除首次启动外，每个后续 outer rollout 的 step 0；
* 恰好与某个环境 reset 对齐的全局检查。

这些都是正常：

[
b_i\in{\texttt{KEEP},\texttt{RENEW}}
]

决策。

当前 R42 overlay 在每个 outer rollout 的 `step==0` 都把 incumbent 重设为 `-1`。R43 不能继承这一做法；incumbent、age 和 active skill 必须跨 outer updates 保存。

### C. 两个检查之间的环境 auto-reset

该 reset：

* 不产生 (Z)；
* 不产生 (b_i)；
* 不产生 conditional skill；
* 不产生 log-probability；
* 不消费高层 action RNG；
* 不增加 high/event row；
* 不改变 incumbent roster；
* 不改变 commitment age；
* 不关闭高层 skill commitment。

但它保持原始 source 的低层语义：

* low actor hidden 清零；
* low critic hidden 清零；
* low GAE mask 断开；
* 新环境初始 observation 从下一 primitive step 开始使用。

## 3.2 Final evaluation 的例外不是训练语义变化

最终 evaluator 显式开始一个新的独立 episode，并在该 episode 的 step 0 调用 high policy。因此 evaluation reset 本身与一个真实高层 action opportunity 对齐，可以使用 structural initial RENEW。R42 evaluator正是每个独立 episode 将 roster 初始化为空，并在 step 0 和 50 调用高层策略。

因此：

```text
training worker internal auto-reset:
    no high action

explicit evaluator episode start:
    structural initial assignment
```

两者不能混用。

---

# 四、修正后的概率合同

联合策略仍为：

[
\pi_H
\left(
Z_\tau,\mathbf b_\tau,\mathbf z_\tau^+
\mid
x_\tau,\mathbf z_\tau^-,\mathbf a_\tau
\right)
=======

\pi_Z^{src}(Z_\tau\mid x_\tau)
\prod_{j=1}^{N}
\pi_B(b_{\sigma(j)}\mid c_{\tau,j})
\left[
\pi_S(z_{\sigma(j)}^+\mid c_{\tau,j},b_{\sigma(j)}=\mathrm{RENEW})
\right]^{\mathbb 1[b_{\sigma(j)}=\mathrm{RENEW}]} .
]

其中 canonical MAT order 保持：

[
\sigma=(1,\ldots,N).
]

## 4.1 正常检查支持集

[
b_i\in{\texttt{KEEP},\texttt{RENEW}}.
]

若：

[
b_i=\texttt{KEEP},
]

则：

* (z_i^+=z_i^-)；
* 不打开 conditional skill factor；
* `skill_valid=0`；
* skill log-probability、entropy 和 actor gradient 全部为零。

若：

[
b_i=\texttt{RENEW},
]

则：

[
z_i^+\in{0,\ldots,K-1}\setminus{z_i^-}.
]

same-label RENEW 始终被 mask。

## 4.2 Working roster

在 canonical sequence 内，前序 agent 的 tentative KEEP/RENEW 结果立即写入 working roster，供后序 agent 条件化。

但只有完整序列结束后，才原子提交：

[
\mathbf z_\tau^{post}.
]

## 4.3 Auto-reset 上没有概率因子

设环境在 primitive step (d) 自动 reset，且：

[
c_n<d<c_{n+1}.
]

则：

[
\log \pi_{\mathrm{reset}}=0
]

不是因为 reset 是 deterministic policy action，而是因为它根本不是 policy action。

post-reset primitive actions 的责任动作仍是最近一次全局检查中已提交的：

[
(Z_{c_n},\mathbf z_{c_n}^{post}).
]

如果当前 skill 最早由更早的 RENEW 建立，则：

* 最近一次 KEEP factor 负责“继续使用它”的决定；
* 最早的 conditional skill factor仍是该 skill identity 的创建动作。

---

# 五、segment 与 age 合同

需要区分两层记录。

## 5.1 Assignment spell

一个 semantic assignment spell 从：

[
\texttt{RENEW}(z_i)
]

开始，到下一次该 agent 的 RENEW 结束。

它可以跨越：

* 一个或多个环境 auto-reset；
* 一个或多个 team-(Z) resampling；
* outer rollout/update boundary。

`KEEP` 不关闭 spell。

commitment age：

[
age_i(t)
========

\text{自最近一次 RENEW 后执行的 primitive steps}
]

在 auto-reset 后继续增加。

## 5.2 Execution fragment

由于 source 在环境 done 时清零 low recurrent hidden，行为过程本身出现真实断点。因此每个 auto-reset：

* 关闭当前 execution fragment；
* completion reason 标记为：

```text
env_reset_censored
```

* 在新 observation 上开启同一 assignment spell 的新 fragment；
* 不产生新的 skill action或 actor log-probability。

因此准确语义是：

[
\boxed{
\text{assignment spell 继续，execution fragment 被 censor。}
}
]

## 5.3 Policy update boundary

active skill、age 和 controller clock跨 update 保存，但旧策略生成的 actor sample不能跨版本再次训练。

因此在 update boundary：

* actor-valid skill-event row以旧 critic bootstrap 关闭；
* 标记 `policy_truncated=True`；
* GAE trace 断开；
* active assignment spell继续；
* 下一 rollout先创建 actor-invalid、critic-only continuation state；
* 旧 skill log-probability不得在新 policy version 中再次使用。

这与项目已有的 on-policy原则一致：模拟器和 active skill可以继续，但旧版本 action不能成为新版本的训练 sample。

---

# 六、修正后的 credit 合同

## 6.1 Source team-(Z) path 保持不变

固定臂及 treatment 的 source team-(Z) token继续使用原始 `H_SharedReplayBuffer`：

* 两个全局 high rows；
* 原始 source block reward；
* 原始 source endpoint mask；
* 原始 high ValueNorm、critic 和 PPO。

不修改这一部分，否则 fixed comparator 不再是 R41B continuation。

原始 source 的 high mask只读取写入 row 时那个 primitive step 的 `done`；它不会看见 block 中更早发生的 reset。

## 6.2 Renewal/check credit

对检查 (c_n) 的 renewal factor：

[
R^B_{n,i}
=========

\sum_{r=0}^{49}
\gamma^r r^{env}_{c_n+r}.
]

若 block 中在 (d\in[c_n,c_n+49]) 发生成功和 auto-reset：

* step (d) 的成功 reward进入 (R^B)；
* reset 后到 block 结束的 reward也进入同一个 (R^B)；
* reset 不关闭 renewal row；
* reset mask 对 renewal credit 等于 1。

renewal TD 为：

[
\delta^B_{n,i}
==============

R^B_{n,i}
+
\gamma^{50}
V^B_i(x_{c_{n+1}})
------------------

V^B_i(x_{c_n}).
]

若 (c_{n+1}) 是同一 policy version 内的正常检查，则正常连接 GAE。

若 (c_{n+1}) 是 outer update boundary，则：

* 使用 old renewal critic bootstrap；
* `policy_truncated=True`；
* 不把 GAE 连到更新后的策略。

## 6.3 Conditional skill-event credit

若 agent (i) 在 (s_{i,m}) 执行 RENEW，则该 actor-valid skill event 的结束点为：

[
u_{i,m}
=======

\min
\left(
\text{下一次该 agent RENEW},
\text{当前 on-policy update boundary}
\right).
]

回报为：

[
R^S_{i,m}
=========

\sum_{t=s_{i,m}}^{u_{i,m}-1}
\gamma^{t-s_{i,m}}r_t^{env}.
]

环境 auto-reset不属于该最小值，因而不终止 event。

若在同一 policy version 内发生下一次 RENEW：

[
\delta^S_{i,m}
==============

R^S_{i,m}
+
\gamma^{T_{i,m}}
V^S_i(c_{i,m+1})
----------------

V^S_i(c_{i,m}).
]

若先到 update boundary：

* 从 boundary 的 reset/continuation state bootstrap；
* `policy_truncated=True`；
* 关闭 actor-valid row；
* 后续只保留 critic continuation，直到下一 RENEW。

## 6.4 成功发生在 step 56–99 时

以 (t=50) 的检查为例。

若成功发生在 (d<99)：

1. reward 1 计入 (t=50) renewal block和相关 skill event；
2. worker立刻返回新 episode初始 observation；
3. low hidden清零；
4. (Z)、incumbent skill和age保持；
5. steps (d+1,\ldots,99) 继续由 (t=50) 的高层动作控制；
6. t=100 old critic bootstrap后进行 policy update。

若成功恰好发生在 step 99：

1. reward 1 仍属于 (t=50) block；
2. wrapper返回 reset observation；
3. 对 R43 renewal/skill credit，该 reset observation是 update-boundary bootstrap state；
4. actor trace随后因 `policy_truncated=True` 断开；
5. 下一 outer rollout的 step 0 执行正常 KEEP/RENEW，而不是无条件 initial RENEW。

---

# 七、buffer 与 optimizer counts

## 7.1 行数保持固定

每个 environment、每个 100-step outer rollout：

[
2
]

个 global check rows。

16 个环境时：

[
2\times16=32
]

个 check rows/update。

200 updates 时：

[
32\times200=6400
]

个 environment-check rows/arm。

auto-reset不增加任何 row。

## 7.2 固定形状 factor storage

每个 global check row包含：

```text
team_Z
pre_roster
pre_age
active_mask
agent_order
renew_token[N]
renew_old_logp[N]
skill_valid[N]
new_skill[N]
skill_old_logp[N]
working-prefix truth
renew_value[N]
skill_event_value[N]
```

conditional skill slots固定存在，但通过 `skill_valid` mask决定是否参与 loss。

此外每个 env-agent只需一个固定 carry-in continuation state，用于跨 update保留 active assignment spell；它没有 actor log-probability。

因此无需 variable-length reset-event buffer。

## 7.3 Minibatch normalization

PPO仍按原始 32 个 check rows进行同一次 shuffle和一个 minibatch。

每行 actor surrogate：

[
L_{\tau}^{actor}
================

\frac{1}{N+1}
\left[
L_Z
+
\sum_{i=1}^{N}
\left(
L^B_i
+
\mathbb 1[b_i=\mathrm{RENEW}]L^S_i
\right)
\right].
]

规则：

* KEEP 的 skill loss严格为 0；
* skill loss不除以实际 RENEW 数量；
* denominator固定为 active (N+1)，避免小量 RENEW rows被重新放大；
* renewal entropy为 0；
* conditional skill entropy只在 `skill_valid=1` 时保留 source skill entropy。

## 7.4 Optimizer exposure不变

每个 outer update仍执行：

[
15
]

次 high optimizer step。因此：

[
200\times15=3000
]

次 high optimizer steps。

所有新 renewal actor、renewal critic和skill-event critic参数进入同一个 high optimizer的新增 param groups，不增加第二套 optimizer step。

每臂仍严格为：

| 路径                                 | steps |
| ---------------------------------- | ----: |
| source/new combined high optimizer | 3,000 |
| low actor                          | 3,000 |
| low critic                         | 3,000 |
| (q_D)                              | 3,000 |
| (q_d)                              | 3,000 |

R42 fixed artifact已经证明这一 source exposure可以精确达到，并且五条路径 replay和梯度均有效。

---

# 八、comparator validity

## Fixed arm

`fixed_refresh` 必须继续是未经改变的 R41B source continuation：

* 两个 global high rows；
* 每个检查重采样 (Z,z_1,z_2)；
* 原始 high buffer和mask；
* 原始 high、low和discriminator loss；
* 新 R43模块存在但 frozen；
* 不追踪或使用 reset-triggered high action。

## Treatment zero initialization

在每个**实际存在的全局检查**上，必须满足：

[
P_{\mathrm{R43},0}
(\mathbf z^{post}\mid x,\mathbf z^-)
====================================

P_{\mathrm{source}}
(\mathbf z^{new}\mid x),
]

以及：

[
\log\pi_B(b_i)
+
\mathbb 1[b_i=R]\log\pi_S(z_i\mid R)
====================================

\log\pi_{\mathrm{source}}(z_i^{post}).
]

误差均：

[
\le10^{-6}.
]

在 auto-reset 时，两臂都没有高层 action opportunity：

* fixed arm继续 held source roster；
* treatment继续相同 held roster；
* 两者均重置 low hidden；
* 两者均等到下一 global check才重新决策。

所以 distribution equivalence 也覆盖 auto-reset 后的 primitive execution，而不需要在 reset 上制造一个虚假的 action。

---

# 九、修订后的 M0

此前与 checkpoint、reward、replay、禁止字段和梯度有关的 M0 条款全部保留。仅替换 reset/clock相关条款如下。

## M0-clock

必须同时满足：

1. high buffer严格为每 env 每 outer rollout两行；
2. 整个训练 run 每 env恰好一次 structural initial assignment；
3. 后续每个 rollout step 0均是普通 KEEP/RENEW check；
4. auto-reset数量可以非零，但：
   [
   \text{high actions at auto-reset}=0;
   ]
5. auto-reset前后：

   * (Z) 不变；
   * incumbent roster不变；
   * commitment age不归零；
   * low actor/critic hidden归零；
6. auto-reset不消费 high action RNG；
7. auto-reset不增加 renewal/skill log-probability或optimizer sample；
8. training、replay和checkpoint均保存跨 update incumbent与age。

## M0-segment

必须满足：

1. 每个 auto-reset恰好产生一个 `env_reset_censored` execution-fragment boundary；
2. 它不产生 semantic RENEW；
3. assignment spell在 reset 后仍指向同一创建 skill factor；
4. update boundary关闭 actor-valid event并 bootstrap；
5. continuation row actor-valid严格为 0；
6. 旧 policy skill log-probability不会进入下一 policy version。

## M0-credit

通过一个在 global block 内真实发生 early success 的 collected row验证：

1. success reward进入当前 renewal block；
2. reset后的 primitive rewards仍进入同一 block；
3. renewal和skill-event reset mask均为 1；
4. source team-(Z) path仍使用原始 high mask；
5. update boundary的 old-critic bootstrap有限；
6. replay误差：
   [
   \le10^{-6}.
   ]

## M0-count

每臂必须精确达到：

```text
320,000 env steps
200 outer updates
6,400 env-check rows
3,000 high optimizer steps
3,000 low-actor steps
3,000 low-critic steps
3,000 q_D steps
3,000 q_d steps
0 auto-reset high rows
```

任一失败：

```text
INVALID_R43_NRC_CLOCK_OR_IMPLEMENTATION
```

唯一动作是修复被定位的 clock、mask、buffer、bootstrap、replay或count defect，并原样重跑。

---

# 十、科学 gate 与最小 abandonment gate

预算不变：

```text
seed                    43041
arms                    fixed_refresh, r43_nrc
rollout envs            16 per arm, concurrent
environment steps       320,000 per arm
outer updates           200
source optimizer steps  3,000 per path
evaluation              100 deterministic paired episodes
bootstrap               10,000, seed 62043
```

## M1：固定正锚点

[
W_{\mathrm{fixed}}\ge0.80,
]

[
K0_{\mathrm{fixed}}\ge0.85,
\qquad
K1_{\mathrm{fixed}}\ge0.85.
]

失败：

```text
INVALID_R43_FIXED_ANCHOR_LOST
```

只允许恢复 source continuation。

## M2：服务安全

原门槛不变：

[
\operatorname{LCB}*{95}
\left[
W*{\mathrm{R43}}-W_{\mathrm{fixed}}
\right]

>

-0.10.
]

## M3：真实 temporal decoupling

只统计显式 (b_i)，排除 structural initial assignments：

[
\text{discordant-renewal rate}\ge0.20,
]

[
\operatorname{LCB}*{95}
[D*{\mathrm{R43}}-D_{\mathrm{fixed}}]>0,
]

[
\text{full-sync RENEW rate}<0.50,
]

[
\min_i
{
P_i(\mathrm{KEEP}),P_i(\mathrm{RENEW})
}
\ge0.05,
]

[
H(\text{actual RENEW targets})/\log4>0.80,
]

[
\text{same-label RENEW}=0.
]

## PASS

```text
PASS_R43_NRC_K50
```

仅当 M0、M1、M2、M3 全部通过。

唯一后续动作仍是：

> 原机制、原阈值的一次 paired multi-seed Alice–Bob verification。

不直接进入 S7 或 variable (N)。

## 唯一 abandonment branch

若 M0和M1有效，但 M2或M3任一失败：

```text
VALID_FAIL_R43_NRC
```

永久退休：

* source-exact renewal factor；
* controller-time renewal credit；
* reset-censored skill-event credit；
* Alice–Bob K50 R43 temporal route。

禁止通过：

* 每 reset 强制 refresh；
* 改 KEEP prior；
* 改 critic或mask；
* 取消 event credit；
* 增加 seed或steps；
* 改 service margin；
* 增加 age容量；
* 加 renewal entropy；
* 加 full-refresh escape；

进行救援。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\text{source clock contradiction：确认};\
&\text{reset semantics：保留 source-global }k_0=50;\
&\text{auto-reset：无策略动作，assignment继续，fragment被censor};\
&\text{age/roster：跨reset和update保存};\
&\text{credit：reset不终止新factor，update boundary才bootstrap截断};\
&\text{buffer：固定两行，无reset event rows};\
&\text{route：唯一继续 R43-NRC};\
&\text{有效M2/M3失败：永久 abandonment，无救援。}
\end{aligned}
}
]

