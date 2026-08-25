# 裁决

[
\boxed{\texttt{VALID_FAIL_R42_IRR_SERVICE}\ \text{成立}}
]

[
\boxed{\texttt{MODIFY R43-NRC}}
]

唯一保留的下一条因果路线是：

[
\boxed{
\begin{aligned}
&\textbf{真实、显式存储的个体 renewal 因子}\
&\rightarrow
\textbf{仅对 RENEW 智能体采样条件技能}\
&\rightarrow
\textbf{renewal 与 skill-assignment 分离的时间信用}\
&\rightarrow
\textbf{服务不退化的非同步技能寿命}
\end{aligned}
}
]

修改点不是回到 R42 的 skill-logit residual，而是把 R43 变成一个**源码等价 warm start、但在动作、概率和信用层面真实可分离**的层次化高层策略。

---

# 一、R42 validity verdict

没有发现会改变科学分支的实现、估计器、replay、comparator、evaluation 或 analyzer 缺陷。

R42 的 M0 通过；固定臂仍保持 `0.98/1.00/0.98` 的 win/key0/key1 正锚点。处理臂相对固定臂的 win-rate 差值为 (-0.10)，配对 95% 区间为 ([-0.17,-0.03])，没有通过严格的 (-0.10) noninferiority margin。处理臂的最终确定性策略还表现为 `0.90` 的 full-sync SET、`0.10` 的 discordance、一个智能体始终 SET，以及仅 `0.6514` 的实际 SET-target 归一化熵。

实现证据也排除了“残差没有真正学到”的解释：

* zero-output 时 action、log-probability、value、entropy、replay 和原有参数梯度误差全为零；
* residual 有直接策略梯度 `0.2221746`；
* treatment residual 的相对 (L_2) 漂移为 `0.5401`，最大参数变化为 `0.3486`；
* fixed residual 漂移严格为零；
* 高层、低层 actor、低层 critic、(q_D)、(q_d) 五条优化路径各执行 3,000 次，梯度有限且非零；
* high/low replay error 均为零。

PowerShell 父进程曾因重定向 `Start-Process` 返回空 `ExitCode` 而错误标记运行状态；两个 worker 当时已分别持久化完整 `completed` 结果，analyzer 使用的也是这些未修改工件。真实非零退出码仍拥有最高优先级，因此这是 orchestration defect，不是 estimand defect。

因此：

[
\boxed{
\text{不能以更多 seed、更多 step、增大 residual、改学习率或改阈值重新解释 R42。}
}
]

---

# 二、R42 的可复用因果结论

## 已建立

### 1. Incumbent-conditioned residual 具有真实 actionability

R42 的 residual：

* 能接收非零 policy gradient；
* 能显著改变参数；
* 能改变训练中的 roster 更新分布；
* 没有破坏 source likelihood replay。

所以“新增路径只是装饰模块”这一解释被排除。

### 2. 现有 HMASD high credit 足以让 residual 学习，但不足以形成有用 renewal

R42 使用原始 individual-skill token 的高层 advantage，同时更新原有 skill logits 和 residual。处理臂的训练期 effective discordance 从固定臂的约 `0.086` 提高到约 `0.150`，说明 credit 确实推动了策略变化；但最终确定性策略重新集中为近乎同步 replacement，并损害服务。

因此可以说：

[
\boxed{
\text{现有 credit 能移动策略}
\not\Rightarrow
\text{它能把“保留还是更新”学成有用的时间控制。}
}
]

### 3. R42 没有形成稳定的自然异步更新

最终策略的一个 agent 永远 SET，另一个仅 10% KEEP；90% 的检查仍全员同步变化。这不是非平凡异步 lifetime，只是完整 replacement 分布中的少量 incumbent 命中。

### 4. 最终可执行 skill supply 变窄

训练期 stochastic SET-target entropy 仍约为 `0.990`，但最终 deterministic evaluation 的实际 SET-target entropy 降为 `0.6514`。因此问题不是收集期完全没有技能支持，而是学习出的执行模式没有保留广泛、可用的更新选择。

### 5. 该 residual 的服务效果为负

处理臂 win rate 从 fixed continuation 的 `0.98` 降至 `0.88`，且差值区间完全位于零以下。这不仅是 M3 temporal gate 失败，也是 M2 task-safety gate 的明确失败。

## 尚未建立

R42 **没有**证明：

* 原始 HMASD 外部 high return 一般无效；
* 所有 per-agent renewal 都会损害服务；
* asynchronous lifetime 假设错误；
* 原始 (q_D/q_d) 技能语义失败；
* 更大的 residual 会成功；
* true renewal factor 也会失败。

最重要的未识别点是：

[
\boxed{
\text{R42 同时保留了“完整技能 replacement action”和它原有的信用粒度。}
}
]

它只是在 (K)-类 skill logits 上加入 roster-dependent 偏置，然后从“新标签是否等于旧标签”事后解释 KEEP。R42 因而没有直接测试：

[
\text{单独的 renewal action}
\rightarrow
\text{单独的 renewal likelihood}
\rightarrow
\text{单独的 renewal credit}.
]

---

# 三、为什么是 `MODIFY R43-NRC`

候选 R43 的因果对象正确，但原始描述还不足以排除两种伪解：

1. 将 categorical incumbent 命中重新命名为 KEEP；
2. 给 renewal 与 skill assignment 继续复制同一 replacement-token advantage。

修正后的 R43 必须满足：

[
\boxed{
\text{renewal 是真实随机变量，而不是 skill label 的派生统计量。}
}
]

同时，R41B 已证明官方 fixed-(k) HMASD 正锚点真实存在：source checkpoint 包含完整 policy、critic、两个 discriminator、五个 optimizer 和两个 ValueNorm；seed 1 的 final win/key0/key1 为 `0.89/0.97/0.92`，zero-step win 为 0，全部 optimizer 各完成 14,055 次更新且 replay error 为零。

所以新的机制必须从该 checkpoint **分布等价地开始**，不能通过 arbitrary KEEP prior 破坏 source anchor。

---

# 四、R43-NRC 的精确策略合同

## 4.1 联合概率分解

在全局检查 (\tau)，令：

* (x_\tau=(s_\tau,o_{1:N,\tau})) 为原始 centralized high information；
* (\mathbf z_\tau^{-}) 为检查前 incumbent roster；
* (\sigma=(1,\ldots,N)) 为原始 canonical MAT 顺序；
* (\tilde{\mathbf z}^{(0)}=\mathbf z^{-}) 为 tentative working roster。

联合策略为：

[
\boxed{
\begin{aligned}
&\pi_H
\left(
Z_\tau,\mathbf b_\tau,
\mathbf z_\tau^{+}
\mid
x_\tau,\mathbf z_\tau^{-}
\right)\
&=
\pi_Z^{src}(Z_\tau\mid x_\tau)
\prod_{j=1}^{N}
\pi_B
\left(
b_{\sigma(j)}
\mid c_{\tau,j}
\right)
\left[
\pi_S
\left(
z_{\sigma(j)}^{+}
\mid c_{\tau,j},b_{\sigma(j)}=\mathrm{RENEW}
\right)
\right]^{\mathbb 1[b_{\sigma(j)}=\mathrm{RENEW}]},
\end{aligned}
}
]

其中：

[
c_{\tau,j}
==========

\left[
\hat s_\tau,
\hat o_{\sigma(j),\tau},
Z_\tau,
\tilde{\mathbf z}^{(j-1)},
\mathbf{age}*\tau,
\mathbf m*\tau
\right].
]

这里只使用原始 high encoder 表示、当前 roster、通用 age 和 active mask；不增加 button、diamond、goal、contact、phase、success 或 reward 字段。官方 HMASD 本来就是先选 (Z)，再按 MAT 顺序条件分配 (z_i)，而 (q_D/q_d) 是另外的低层 discriminator，不是高层 skill policy。([NIPS 论文会议][1])

---

## 4.2 Source-exact renewal 初始化

令原始 MAT 在当前 prefix 下生成 individual-skill logits：

[
\ell_i(z),\qquad z\in{1,\ldots,K}.
]

正常 active agent 的 binary renewal logits 定义为：

[
u_i^{KEEP}
==========

\operatorname{sg}!\left[\ell_i(z_i^-)\right]
+
\Delta_\rho(c_i),
]

[
u_i^{RENEW}
===========

\operatorname{sg}
\left[
\operatorname{LSE}_{z\ne z_i^-}\ell_i(z)
\right],
]

[
\pi_B(b_i)=
\operatorname{softmax}
\left(
u_i^{KEEP},u_i^{RENEW}
\right).
]

(\Delta_\rho) 是共享的 renewal head，输出层严格零初始化。

若 (b_i=\mathrm{RENEW})：

[
\pi_S(z_i^+=z\mid b_i=\mathrm{RENEW})
=====================================

\frac{\exp\ell_i(z)}
{\sum_{z'\ne z_i^-}\exp\ell_i(z')},
\qquad z\ne z_i^-.
]

于是当 (\Delta_\rho=0) 时：

[
P(z_i^{post}=z_i^-)
===================

P_{src}(z_i^-),
]

[
P(z_i^{post}=z)
===============

P_{src}(z),\qquad z\ne z_i^-.
]

即 treatment 的**有效 post-skill 分布与 source categorical policy 完全一致**，但 renewal head 一旦学习，就能独立调节 incumbent retention 概率。

这里的 `stop-gradient` 边界意味着：

* renewal loss 只更新 renewal head；
* source skill logits只由真正执行的 conditional skill factor训练；
* 不允许 renewal loss借道修改整个 source skill distribution。

这与 R42 直接向所有 skill logits 添加 residual 是不同的因果对象。

---

## 4.3 支持集与 replay

初始 assignment：

[
b_i=\mathrm{RENEW}
]

由结构强制，不产生 renewal log-probability；(z_i) 可从全部 (K) 个技能中选择。

正常检查：

[
b_i\in{\mathrm{KEEP},\mathrm{RENEW}}.
]

若 `KEEP`：

* 保持 incumbent；
* 不采样 conditional skill；
* `skill_valid=False`；
* 不产生 skill log-probability、skill entropy 或 skill gradient。

若 `RENEW`：

[
z_i^+\in{1,\ldots,K}\setminus{z_i^-}.
]

**same-label RENEW 必须 mask。** 否则它会保持相同低层输入和相同 recurrent hidden，却只重置 age/segment，重新制造已经被 source audit 否决的装饰性动作。该 audit 已证明，原始系统中 SET(current) 与 KEEP 在低层执行上完全相同。

每个 high row 必须存储：

```text
pre_roster
pre_ages
active_mask
agent_order
team_Z
renew_token
renew_old_logp
skill_valid
new_skill
skill_old_logp
tentative-prefix reconstruction truth
renew_value
skill_event_value
```

replay 必须使用原始 action、incumbent、active mask 和顺序逐因子 teacher-force，不能从 final roster 反推中间 action。

---

## 4.4 Working roster 与 atomic commit

对每个 agent 采样后，先更新 tentative roster：

```text
if KEEP:
    tentative_skill[i] = incumbent[i]
if RENEW:
    tentative_skill[i] = sampled_new_skill
```

后序 agent 可以看到前序 agent 的 tentative 结果。

但环境和低层 actor只能在整个序列结束后一次性看到：

[
\mathbf z_\tau^{post}
=====================

\tilde{\mathbf z}^{(N)}.
]

因此“立即更新 working roster”是 autoregressive conditioning，不是 agent 间异步环境执行。

---

# 五、时钟和 segment 合同

## Team (Z)

第一道 gate 中：

[
Z_\tau\sim\pi_Z^{src}
]

仍在每个 (k_0=50) 检查重新采样，并在接下来的 50 primitive steps 固定。

不允许给 (Z) 增加 KEEP、duration 或独立 lifetime。否则同时修改 team strategy 和 individual renewal 两个时钟，无法归因。

官方 HMASD 的 source 合同本来就是每 (k) 步分配一次 (Z,z_{1:N})，高层奖励为该 (k)-step block 的环境回报，Alice–Bob 使用 (k=50,n_Z=2,n_z=4)。([NIPS 论文会议][1])

## Individual skill

* `KEEP`：继续当前 skill segment，age 继续增加；
* `RENEW`：关闭旧 segment、选择不同 skill、age 归零并打开新 segment；
* episode reset：所有 agent 强制 initial RENEW；
* episode terminal：关闭所有 open segments；
* low actor/critic recurrent hidden **不因 RENEW 重置**，只按原始 source 在 environment done 时重置。

Alice–Bob 的 episode 和 rollout 都为 100 步，所以本 gate 不存在跨 PPO update 的未完成 segment。若实现产生非 terminal update truncation，M0 直接 invalid，而不是临时设计跨更新 credit。

## Full-refresh escape

处理臂禁止：

* 定期强制所有 agent RENEW；
* 最大 age 强制更新；
* “连续 KEEP 太久”回退；
* hazard 或 scheduler override；
* 服务下降时自动 full refresh。

唯一结构性 full refresh 是 episode 初始 assignment。

策略自身选择所有 agent `RENEW` 是合法 joint action，但不能由 controller override。否则会悄然恢复 shared fixed lifetime。

---

# 六、credit 与 update 合同

## 6.1 原始 high credit 的裁决

结论不是“全部原始 high credit 失败”，而是：

[
\boxed{
\begin{aligned}
&\text{原始 external high return 与 team-}Z\text{ credit 可保留};\
&\text{R42 中一个 individual replacement advantage}\
&\text{同时训练 source logits 和 retention residual 的精确路径已失败。}
\end{aligned}
}
]

原始 source high buffer虽然给 team token和每个 agent token复制同一个 block reward，但为 (Z) 和每个 (z_i) 保存独立 value、return 和 advantage 槽位；MAT PPO按 token ratio 训练。它不是一个仅有单标量 critic 的 R30 buffer。

R43 不应继续把原 individual-token advantage无差别复制给 renewal 和 skill assignment。

---

## 6.2 Renewal credit

renewal 每个检查都产生，因此它的因果支持是下一个 fixed-check block：

[
R_{\tau}^{B}
============

\sum_{p=0}^{L_\tau-1}
\gamma^p r^{env}*{t*\tau+p},
\qquad L_\tau\le k_0.
]

为每个 agent 定义：

[
V_i^B(c_{\tau,i})
=================

\operatorname{sg}\left[V_i^{src}(x_\tau)\right]
+
\Delta_i^B(c_{\tau,i}),
]

其中 (\Delta_i^B) 为共享、零输出初始化的 centralized renewal critic residual。

按固定检查序列计算：

[
\delta_{\tau,i}^{B}
===================

R_\tau^B
+
\gamma^{L_\tau}(1-d_\tau)
V_i^B(c_{\tau+1,i})
-------------------

V_i^B(c_{\tau,i}),
]

[
A_{\tau,i}^{B}
==============

\operatorname{GAE}
\left(
\delta_{\tau,i}^{B}
\right).
]

它只训练：

[
\log\pi_B(b_i\mid c_{\tau,i}).
]

---

## 6.3 Conditional skill credit

skill factor只在 RENEW 时被采样，因此其回报支持必须从该 RENEW 开始，一直到：

* 下一次该 agent RENEW；
* 或 episode terminal。

令第 (m) 个 assignment event 的实际持续时间为 (T_{i,m})：

[
R_{i,m}^{S}
===========

\sum_{r=0}^{T_{i,m}-1}
\gamma^r
r^{env}*{s*{i,m}+r}.
]

定义：

[
V_i^S(c_{i,m}^{S})
==================

\operatorname{sg}\left[V_i^{src}\right]
+
\Delta_i^S(c_{i,m}^{S}),
]

并用 SMDP discount：

[
\Gamma_{i,m}=\gamma^{T_{i,m}}
]

计算 assignment-event GAE。

这不会形成 lifetime reward，因为只使用环境外部回报；较长 segment 不会额外获得任何 intrinsic 或 KEEP payment。

在当前 Alice–Bob gate 中，唯一正常 renewal 位于 (t=50)，所以新 assignment 的 event return恰好覆盖 (t=50) 到 terminal。初始 (t=0) assignment 若在 (t=50) KEEP，则其 event return自然覆盖整段 100 步；若 RENEW，则在 (t=50) 关闭。

---

## 6.4 PPO loss

[
L_B
===

\frac1N
\sum_i
L_{\mathrm{PPO}}
\left(
\rho_i^B,A_i^B
\right),
]

[
L_S
===

\frac1N
\sum_i
\mathbb 1[b_i=\mathrm{RENEW}]
L_{\mathrm{PPO}}
\left(
\rho_i^S,A_i^S
\right).
]

skill loss 除以 active-agent 数 (N)，而不是实际 RENEW 数量。这样频繁更新的策略不会仅因产生更多 assignment samples 获得更大优化权重。

* renewal factor没有 entropy bonus；
* conditional skill factor只在 RENEW row 保留 source high-skill entropy；
* team-(Z) entropy和 PPO保持 source；
* hard action、working-roster 更新、segment boundary均 detached；
* new critic residual只更新自己的参数，不反向修改 source encoder/value；
* renewal head使用 detached source representation，只由 (L_B) 更新；
* source MAT individual-skill path只由 (L_S) 更新。

---

## 6.5 (q_D/q_d) 边界

低层仍保持官方 Alice–Bob 合同：

[
r_{i,t}^{low}
=============

0.1\log q_D(Z_\tau\mid s_{t+1})
+
0.2\log q_d(z_{i,t}\mid o_{i,t+1},Z_\tau),
]

且：

[
\lambda_e=0.
]

(q_D/q_d)：

* 继续按原始 supervised discriminator loss训练；
* 继续只进入 low reward；
* 不读取 KEEP/RENEW、age 或 segment length；
* 不进入 renewal logits、renewal critic、assignment high return；
* 不作为 renewal selector。

这是对 R41B source mechanism 的冻结保留，不是重新开放旧 (q_D/q_d) 研究路线。论文明确区分了 high skill coordinator (\pi_h) 与两个 discriminator，并规定了这一低层 intrinsic reward。([NIPS 论文会议][1])

---

# 七、warm-start 边界

两臂必须从同一个：

```text
R41B seed-1 exact_final
schema: r41_official_hmasd_complete_checkpoint_v1
outer_updates: 937
```

恢复：

* source high policy和value；
* low actor和critic；
* (q_D)、(q_d)；
* 五个 optimizer；
* high/low ValueNorm；
* Python、NumPy、Torch、CUDA RNG；
* source checkpoint metadata。

不允许部分加载或 `strict=False`。R41B checkpoint已经包含全部这些组成。

两臂都实例化相同的新模块：

* renewal actor head；
* renewal critic residual；
* skill-event critic residual。

固定臂：

* 所有新模块 output scale 为 0；
* `requires_grad=False`；
* drift 必须为 0；
* 完整 source sampling、likelihood、value和训练路径保持不变。

处理臂：

* 三个新模块输出层严格为零；
* renewal actor的 base probability采用前述 source-exact分解；
* critic residual初始为零，因此 factor values等于 source values；
* 原有 optimizer state保持不变；
* 新参数作为新的 high optimizer param group加入，Adam moments为零。

形式化训练前必须证明：

[
\max_z
\left|
P_{\mathrm{R43},0}(z^{post}=z)
------------------------------

P_{\mathrm{source}}(z)
\right|
\le10^{-6},
]

[
\left|
\log\pi_B(b)
+
\mathbb 1[b=R]\log\pi_S(z\mid R)
--------------------------------

\log\pi_{\mathrm{source}}(z^{post})
\right|
\le10^{-6}.
]

同时：

* renewal actor direct gradient (>0)；
* 两个新 critic direct gradient (>0)；
* source fixed-path action/logp/value/base-gradient error (\le10^{-6})。

---

# 八、最小 Alice–Bob abandonment gate

## 实验

```text
experiment             R43-NRC-K50
source checkpoint      R41B seed-1 exact_final
training seed           43041
arms                    fixed_refresh, r43_nrc
rollout envs            16 per arm, concurrent
episode / rollout       100 / 100
native check k0         50
environment steps       320,000 per arm
outer updates           200 per arm
source optimizer steps  3,000 on each of five paths per arm
high new-param steps    3,000 in treatment
final evaluation        100 deterministic paired resets per arm
bootstrap               10,000, seed 62043
```

这沿用 R42 的曝光量，不增加 seed、预算或门槛。

## Comparator

`fixed_refresh` 必须是完整 R41B source continuation：

* 每个检查重采样 (Z,z_1,z_2)；
* source high PPO、low PPO、(q_D/q_d) 全部不变；
* 新 renewal/critic模块存在但冻结；
* exact final checkpoint，不选择 best。

## M0：实现有效性

必须全部通过：

1. source/checkpoint/schema/RNG完整恢复；
2. fixed path action、logp、value、gradient与 source误差 (\le10^{-6})；
3. treatment zero-init effective-skill distribution与 source误差 (\le10^{-6})；
4. team、renewal、conditional skill和low replay误差均 (\le10^{-6})；
5. KEEP row的 skill-valid、skill logp、skill entropy和skill gradient严格为零；
6. initial assignment不产生 renewal logp；
7. same-label RENEW 数量严格为零；
8. tentative prefix与atomic final commit一致；
9. fixed新模块 drift为零；treatment renewal/critic模块有非零有限gradient和非零drift；
10. 五个source optimizer各恰好3,000步；没有数值修复；
11. high return只含环境回报；
12. low reward严格保持 `0*q_env + 0.1*q_D + 0.2*q_d`；
13. 没有 renewal entropy、lifetime reward、switch penalty、forced refresh或任务字段。

失败：

```text
INVALID_R43_NRC_IMPLEMENTATION
```

唯一下一动作是修复所定位的 sampling、replay、credit、checkpoint 或计数 defect，并原合同重跑。

## M1：固定正锚点

要求：

[
W_{\mathrm{fixed}}\ge0.80,
]

[
K0_{\mathrm{fixed}}\ge0.85,
\qquad
K1_{\mathrm{fixed}}\ge0.85.
]

未通过：

```text
INVALID_R43_FIXED_ANCHOR_LOST
```

唯一动作是恢复 R41B continuation wiring；不得解释 treatment。

## M2：服务安全

保持 R42 原门槛：

[
\operatorname{LCB}*{95}
\left[
W*{\mathrm{R43}}-W_{\mathrm{fixed}}
\right]

>

-0.10.
]

不能改为均值门槛，也不能把 `-0.10` 改成更宽 margin。

## M3：真实 temporal decoupling

所有指标必须直接读取 (b_i)，不能再通过 label 是否变化推断：

[
\text{discordant-renewal rate}\ge0.20,
]

[
\operatorname{LCB}*{95}
\left[
D*{\mathrm{R43}}-D_{\mathrm{fixed}}
\right]>0,
]

[
\text{full-sync RENEW rate}<0.50,
]

[
\min_i
{
P_i(\mathrm{KEEP}),
P_i(\mathrm{RENEW})
}
\ge0.05,
]

[
H(\text{actual RENEW targets})/\log 4>0.80.
]

并要求：

[
\text{same-label RENEW}=0.
]

## 结果分支

### `PASS_R43_NRC_K50`

仅当：

[
M0\land M1\land M2\land M3.
]

允许结论：

> true renewal factorization与factor-aligned credit在官方 fixed-(N) HMASD source上实现了服务安全、非退化的个体技能续期。

唯一下一动作是**原样冻结该机制并进行一次 paired multi-seed Alice–Bob verification**。不直接进入 S7 或 variable (N)。

### 唯一 abandonment branch：`VALID_FAIL_R43_NRC`

只要 M0/M1有效，但 M2或M3任一失败，即永久退休：

* 该 source-exact renewal factorization；
* 该 renewal/check credit；
* 该 conditional skill event credit；
* 该 Alice–Bob K50 temporal route。

不允许：

* 改 KEEP prior；
* 改 critic；
* 删除 event return；
* 增加 age feature容量；
* 加 entropy；
* 扩 seed/step；
* 改 margin；
* 增加 full-refresh escape。

唯一下一动作是完成一次 R41–R43 temporal failure review；在选定全新因果对象前不继续修改 renewal。

不存在 `UNDERPOWERED`、`MIXED` 或自动 rescue 分支。

---

# 九、对未来 variable-team 的结构兼容约束

R43 不授权 variable (N)，但必须避免制造不可迁移的时间语义：

1. renewal/skill head参数在 agent间共享；
2. 概率分解未来只遍历 active set；
3. storage必须保留 active mask、外生 order、prefix和membership epoch；
4. joiner没有 incumbent，必须走 initial RENEW；
5. leaver不产生 KEEP/RENEW token，当前 segment标记 `membership_censored`；
6. surviving agents不因其他成员加入/离开而重置 skill、age或low hidden；
7. loss按 active-agent数归一化，不按 padded slot数；
8. membership是外生 mask，不是未记 likelihood 的policy action；
9. 不将 member count、join、leave或survival作为 intrinsic reward；
10. 后续 set-equivariant实现不能重新定义 R43 的 renewal概率和credit语义。

这些约束与已接受的 open-roster disposition一致，但只有 fixed-(N) gate通过后才可实现。

---

# 十、保持关闭的路线

继续永久关闭：

* R42 skill-logit residual 的任何容量、深度、学习率、输入、seed或budget变体；
* 把 age加入 R42 residual后重新运行；
* 将 residual仅限制为 incumbent logit后改名；
* R29 action-density/action-information reward；
* R31 observational effect posterior；
* R32 direct IFEPG；
* R33 roster scorer；
* R34 hindsight clustering/distillation；
* R35–R40 substrate与access路线；
* task-specific novelty、distance、contact、goal、phase、coverage、success或potential shaping；
* (q_D/q_d) 作为 renewal selector或high reward；
* sampled team latent revival；
* duration-category action；
* KEEP/lifetime reward；
* switch/edit penalty；
* learned agent order；
* full-refresh hazard/escape；
* variable (N)、membership censoring和S7 promotion，直到固定-(N) gate及其multi-seed verification通过。

---

# 十一、最强反对意见

最强反对意见是：

[
\boxed{
\text{Alice–Bob 可能在结构上真正偏好一次同步全队角色切换。}
}
]

该任务只有一个正常检查 (t=50)。官方论文展示的典型解正是在 (t=0) 选择一组蓝色 button/diamond skills，并在 (t=k) 同步转为一组红色 button/diamond skills；fixed continuation 的 `0.98` win rate也说明同步 full refresh已接近最优。([NIPS 论文会议][1])

因此，R43 即使实现正确，也可能面对：

[
\text{非同步 renewal}
\rightarrow
\text{真实服务损失}.
]

这意味着一个 `VALID_FAIL_R43_NRC` 不能被推广为：

* 异步 lifetime普遍无效；
* UAV任务不需要不同寿命；
* open-roster不成立。

它只能说明：

> 在当前唯一正 source anchor上，所注册的 true-renewal policy/credit没有同时满足服务安全和非同步机制门槛。

这个反对意见**不改变裁决**。R43仍是当前最小、最可归因的下一步，因为它第一次直接测试真实 renewal action及其信用，而不是继续调整 replacement logits。但也正因为 Alice–Bob可能天然同步，M2/M3必须同时通过；不能用“任务不适合”在结果后豁免其中任何一项。

---

# 最终单一路线

[
\boxed{
\begin{aligned}
&\texttt{R42 = VALID FAIL};\
&\texttt{Route = MODIFY R43-NRC};\
&\text{下一边：source-exact true renewal}\
&\quad+\text{conditional non-incumbent skill assignment}\
&\quad+\text{renewal/check credit}\
&\quad+\text{skill/event credit};\
&\text{PASS：仅进入同机制 multi-seed verification};\
&\text{VALID FAIL：永久退休该 R43 路线，不救援。}
\end{aligned}
}
]

[1]: https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf "https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf"

