# 总体建议

结合 `aggressive@ffa18c3` 的仓库状态，我建议把这个新方向正式定义为：

[
\boxed{
\textbf{OR-HA-CTSE：Open-Roster Horizon-Aware Skill Editing}
}
]

但**当前唯一应该立即实现的因果边**不是“完整动态加入/退出 + 可变技能寿命 + intrinsic reward”，而是：

[
\boxed{
\text{固定身份 roster 表示}
\rightarrow
\text{集合等变 roster 表示}
\rightarrow
\text{在固定 }N\text{ 下保持 R30 语义与训练安全}
}
]

原因是当前仓库在 R38 后没有活跃的 core implementation stage，R30 的时间机制虽然已经实现，但其 320K reward-pure pair 被中止，并不存在一个完成的性能正结论；同时项目仍要求一次只推进一个上游因果边。

因此应将“可变 team number”作为一个**架构泛化轴**，与当前尚未解决的 skill-semantic intrinsic 轴分开：

[
\begin{aligned}
\text{轴 A：}&\quad
z_i\rightarrow\text{自然持续技能语义},\
\text{轴 B：}&\quad
A_t\rightarrow\text{可变 roster 下的联合控制与泛化}.
\end{aligned}
]

轴 B 不会解决 R26–R34 暴露的自然技能形成缺口，也不应被 intrinsic reward 定义或奖励。

---

# 一、首先区分三种“可变 team number”

不能把它们作为同一个问题处理。

## 1. 有效成员数变化

物理 UAV 数量固定，但一部分 UAV 暂时不可执行动作：

[
N_{\mathrm{physical}}=\text{常数},
\qquad
N_{\mathrm{available}}(t)=\text{变量}.
]

例如：

* 临时故障；
* 电量耗尽；
* 通信或执行能力暂时失效；
* 维修或充电期间退出服务。

这是当前仓库最容易首先测试的情形。S7 已经拥有 `uav_failed`、failure timer、minimum-active constraint 和失败期间 motion-disabled 语义；S4 还原生启用了失败概率和 20–60 步故障时间。

## 2. 跨 episode 的物理团队规模变化

每个 episode 内团队固定，但：

[
N_e\in{4,5,6,7,8}
]

随环境实例或 episode 改变。

这主要测试：

* 参数是否与 (N) 解耦；
* 是否能由一个共享 policy 处理多个规模；
* 是否能零样本迁移到未训练规模。

## 3. episode 内真实加入和退出

[
A_t\neq A_{t+1},
]

并且 agent 可能：

* 首次加入；
* 永久离开；
* 离开后重新加入；
* 以新能力或新成员实例重新进入。

这是完整的 open-roster MARL，也是最难的情形。它不仅改变输入长度，还改变：

* recurrent hidden 的生命周期；
* skill segment 的完成语义；
* low GAE 的 terminal mask；
* high row 的 token 集合；
* skill lifetime 的右删失；
* checkpoint 和 rollout buffer 的成员索引。

## 推荐顺序

[
\boxed{
\text{固定 }N\text{ 的 set 架构}
\rightarrow
\text{跨 episode 可变 }N
\rightarrow
\text{动态 available roster}
\rightarrow
\text{真实 join/leave}
}
]

不要一开始就把 PettingZoo 的 `possible_agents` 改成 episode 内完全 ragged。当前 S7 的失败机制已经提供了一个低成本的“有效 roster 变化”显微镜。

---

# 二、当前仓库真正绑定固定 (N) 的位置

## 1. R30 high actor 的 roster representation

当前：

[
\texttt{ar_prefix_dim}
======================

K(1+2N).
]

其中包含：

* 全局 skill count；
* 每个 agent identity 对应的 skill block；
* 每个 agent identity 对应的 age block。

并且 `encode_working_roster` 显式遍历：

```python
for agent_id in range(self.n_agents):
```

所以参数输入维度和 roster identity 都与 (N) 绑定。

## 2. high critic

当前 high critic 使用：

[
N\times obs_dim
+
N\times K
+
2N
]

的展平输入，因此不同 (N) 会直接改变第一层权重形状。

## 3. low centralized critic

低层 actor 本身比较容易保留：

[
\mathrm{MLPBase}(o_i)
\rightarrow
\text{skill FiLM}
\rightarrow
\mathrm{RNN}
\rightarrow
\text{action head}.
]

它不直接依赖 `n_agents`。但 low critic 的 `MLPBase` 接收固定 `state_dim`，所以当 centralized state 随团队规模变化时，critic 同样无法复用。

## 4. 运行态和 buffer

当前：

```text
active_skills       [num_envs, n_agents]
skill_age           [num_envs, n_agents]
has_active_skill    [num_envs, n_agents]
low_actor_hxs       [num_envs, n_agents, hidden]
low_critic_hxs      [num_envs, n_agents, hidden]
```

均固定分配。

## 5. 环境适配器

`ParallelToArrayAdapter` 把 `possible_agents` 固定为 `self.agents`，构建固定形状 observation/action space；缺失 agent 通过零填充保留固定 slot，并且当前使用“任何 agent terminal 即整个环境 terminal”的语义。

因此需要修改的核心不是 MAT 的顺序分解本身，而是：

[
\boxed{
\text{identity-indexed flattening}
+
\text{固定 state/obs shape}
+
\text{agent terminal 与 env terminal 混合}
}
]

---

# 三、建议的最终数学模型

定义三个不同集合：

[
P=\text{物理可能成员集合},
]

[
B_t\subseteq P=\text{primitive step }t\text{ 可实际执行动作的成员},
]

[
A_\tau\subseteq P=\text{高层 check }\tau\text{ 正式纳入 controller 的成员}.
]

高层仍只在固定时钟：

[
t=\tau k_0
]

执行。

成员变化：

[
J_\tau=A_\tau\setminus A_{\tau-1}
]

是新加入者，

[
L_\tau=A_{\tau-1}\setminus A_\tau
]

是离开者，

[
S_\tau=A_\tau\cap A_{\tau-1}
]

是持续成员。

高层 token 集合改为：

[
e_{i,\tau}\in
\begin{cases}
{\texttt{SET}(z):z\in[1,K]}, & i\in J_\tau,[2mm]
{\texttt{KEEP}}\cup
{\texttt{SET}(z):z\ne z_i^{-}}, & i\in S_\tau,[2mm]
\varnothing, & i\in L_\tau.
\end{cases}
]

这保留了 R30 的主要不变量：

* 新成员 initial assignment 不允许 KEEP；
* 持续成员仍为 KEEP/SET；
* 离开者不会获得一个伪造的 SET；
* surviving agents 不因别人加入或退出而自动重置；
* actual lifetime 仍由连续 KEEP 得到；
* membership leave 只造成 skill segment 右删失。

---

# 四、推荐的唯一主架构

我建议使用：

[
\boxed{
\textbf{静态 ISAB entity encoder}
+
\textbf{增量 Deep-Set roster accumulator}
+
\textbf{变长 AR KEEP/SET scan}
}
]

而不是每个 AR token 都重新运行完整 Transformer。

Set Transformer 的 inducing-point attention 能把普通 set self-attention 的二次复杂度降低到相对集合大小近似线性；Deep Sets 则提供 permutation-invariant/equivariant 集合表示的标准结构。([arXiv][1])

## 1. 静态 agent entity encoder

每个当前成员构造：

[
x_i=
\phi_{\mathrm{ent}}
\left(
o_i^{H},
c_i,
m_i^{join},
m_i^{active}
\right),
]

其中 (c_i) 是可选 capability descriptor，例如：

* 最大速度；
* 电池容量；
* 感知范围；
* UAV 类型；
* action-space type。

**不输入 persistent agent ID 或固定 slot ID。**

通过固定 (M=8) 个 inducing slots：

[
{h_i}*{i\in A*\tau},g_\tau
==========================

E_{\mathrm{ISAB}}
\left(
{x_i:i\in A_\tau}
\right).
]

这里：

* (h_i) 是 contextualized agent feature；
* (g_\tau) 是 deterministic team representation；
* 它不是新的 sampled team latent；
* 它不会进入 low actor；
* 不会重开已经退休的 team reward 或 (q_D)。

## 2. 动态 working-roster accumulator

AR scan 内技能和 age 会变化，所以不能只在 scan 前做一次静态 attention。

定义：

[
u_i^{(j)}
=========

\psi
\left(
h_i,
\operatorname{onehot}(z_i^{(j)}),
\log(1+age_i^{(j)}),
p_i^{(j)}
\right),
]

其中 (p_i^{(j)}) 表示 agent 是否已在当前 AR sequence 中被处理。

聚合：

[
r^{(j)}
=======

\frac{1}{|A_\tau|}
\sum_{i\in A_\tau}u_i^{(j)}.
]

另外输入：

[
c_N=\log(1+|A_\tau|).
]

处理第 (j) 个 token 后，仅更新当前 agent 的贡献：

[
r^{(j)}
=======

r^{(j-1)}
+
\frac{
u_{\sigma(j)}^{new}
-------------------

u_{\sigma(j)}^{old}
}{
|A_\tau|
}.
]

这样不必在每个 token 上重新遍历或重新 attention 全队。

总体复杂度为：

[
O(NM)+O(N),
]

而不是：

[
O(N^2)
]

或每个 token 重算造成的更高复杂度。

## 3. 变长 autoregressive scan

[
\pi_H(\mathbf e_\tau\mid X_\tau,A_\tau,\sigma_\tau)
===================================================

\prod_{j=1}^{|A_\tau|}
\pi_H
\left(
e_{\sigma_\tau(j),\tau}
\mid
h_{\sigma_\tau(j)},
g_\tau,
r^{(j-1)},
j/|A_\tau|,
c_N
\right).
]

顺序 (\sigma_\tau) 应当：

* 从 active set 中外生随机采样；
* 不由 agent ID 排序；
* 不作为可学习动作；
* 原样存入 buffer；
* PPO 时 teacher-force 同一顺序。

在同时置换 agent tokens 和 `agent_order` 后，输出应相应置换。顺序条件策略本身可以依赖 prefix，但边际模型不应依赖固定 UAV 编号。

MAT 已经证明可以把联合决策表示为 agent action sequence，并报告了对 agent-number 变化的任务迁移；但这不自动解决 episode 内成员 churn、skill survival 或 membership censoring。你的贡献不能只写成“MAT 支持变长序列”。([arXiv][2])

---

# 五、high 与 low critic 的可变规模设计

## 1. High critic

不要再展平 joint observation 和 roster：

[
V_\psi^H
========

\rho_H
\left(
g_\tau^{crit},
\log(1+|A_\tau|),
steps_to_check/k_0
\right).
]

其中：

[
g_\tau^{crit}
=============

\operatorname{Pool}
\left(
{h_{i,\tau}^{crit}:i\in A_\tau},
\text{global fixed entities}
\right).
]

它仍然输出：

[
V_\tau^H\in\mathbb R,
]

每个 check 一个 scalar，与 token prefix 无关。

## 2. Low centralized critic

低 actor 继续保持：

[
a_{i,t}\sim\pi_l(a_i\mid o_{i,t},z_{i,t}).
]

但 centralized low critic 改为：

[
h_{i,t}^{C},g_t^C
=================

E_C
\left(
{s_{j,t}^{C}:j\in A_t}
\right),
]

[
V_{i,t}^{L}
===========

\rho_L
\left(
h_{i,t}^C,
g_t^C,
z_{i,t},
\log(1+|A_t|)
\right).
]

这会产生一个 permutation-equivariant 的 per-agent value vector，而不是依赖固定 `state_dim` 的 MLP。

## 3. Low actor 暂时不要同步重构

第一阶段保留当前 strict HMASD low actor，避免同时改变：

* skill FiLM；
* actor recurrent state；
* action head；
* high representation；
* low observation encoder。

S7 配置已经把 `max_observed_uavs` 至少设为 8，所以 (N\le8) 提供了一个很自然的初始规模范围；但在实施前仍需确认 base observation 的全部子块在 (N=4\ldots8) 间形状完全一致。

超过这个范围，或者希望真正无固定上限时，才把 low actor 的 `MLPBase(flat_obs)` 换成 typed entity encoder：

[
o_i=
\left[
o_i^{self},
{o_{ij}^{uav}},
{o_{iu}^{user}},
{o_{ib}^{bs}}
\right],
]

[
\bar o_i
========

\left[
\phi_{\mathrm{self}}(o_i^{self}),
\operatorname{Pool}*j\phi*{\mathrm{uav}}(o_{ij}),
\operatorname{Pool}*u\phi*{\mathrm{user}}(o_{iu}),
\operatorname{Pool}*b\phi*{\mathrm{bs}}(o_{ib})
\right].
]

然后：

[
\bar o_i
\rightarrow
\text{skill FiLM}
\rightarrow
\text{RNN}
\rightarrow
\text{action head}.
]

这仍满足：

[
\pi_l(a_i\mid o_i,z_i),
]

但已经是新的 low-level architecture，后续 HMASD parity 必须重新做 capacity matching。仓库当前也明确要求网络规模变化不能直接当作算法比较。

---

# 六、“共享参数”不等于“所有 UAV 行为相同”

不需要为每个 UAV 身份保存一套网络。

合理的条件交换性是：

[
h_i=\phi(o_i,c_i),
]

[
\pi_i(a_i)=\pi(a_i\mid h_i,z_i,c_i).
]

同一个函数 (\pi) 可以因为：

* observation；
* capability；
* skill；
* recurrent hidden；
* team context；

不同而产生完全不同的行为。

若 UAV 只有少量类型，可使用：

[
\text{shared trunk}
+
\text{type embedding}
+
\text{small type-specific action head}.
]

若能力是连续变化的，可使用：

[
\theta_i^{head}=H(c_i)
]

的 hypernetwork。

DPN/HPN 已经展示了用 permutation-invariant input 和 permutation-equivariant output 处理 agent/entity 差异的方法；UPDeT 则针对不同 observation/action configuration 做了 policy decoupling。因此“共享网络但按能力产生差异”已有成熟基础。([arXiv][3])

只有当加入的成员是**未联合训练、未知 policy 的第三方 UAV**时，才需要显式 teammate-policy belief：

[
b_{j,t}
=======

q(\text{teammate policy/type}\mid h_{j,0:t}).
]

那属于 open ad hoc teamwork，比当前“共同训练但成员数量变化”的问题更强，不应在第一阶段一起承担。图式 open-team 方法已经研究了未知成员动态进入和退出，但其研究对象与当前共享 UAV controller 不完全相同。([arXiv][4])

---

# 七、成员加入、退出和技能寿命的精确语义

## 1. 新成员加入

当 (i\in J_\tau)：

* 初始化 low actor hidden；
* 初始化 low critic hidden；
* `has_active_skill=False`；
* skill age 为 0；
* KEEP 严格 mask；
* 必须采样 initial `SET(z)`；
* 不把 admission 计为 policy switch；
* 新建 `membership_epoch`。

## 2. 成员离开

当 (i\in L_\tau)：

* 不再产生 high token；
* low actor trace 终止；
* low GAE 对该 agent 断开；
* 当前 skill process 标记：

```text
membership_censored
```

而不是：

```text
SET
policy_switch
environment_terminal
```

* 其他 agent 的 hidden、skill、age、GAE 不重置；
* 全局 check clock 不重置。

## 3. 重新加入

默认：

[
\text{rejoin}=\text{new membership instance}.
]

即使环境复用了同一个 UAV ID：

* 网络输入不读取这个 ID；
* storage 使用 `agent_key + membership_epoch`；
* hidden 重新初始化；
* skill 必须 initial SET；
* 旧 lifetime 不跨 inactive gap 延续。

## 4. 暂时不可用但未跨 check

需要区分：

[
B_t=\text{primitive-step availability}
]

和：

[
A_\tau=\text{controller membership at check}.
]

若 UAV 在两个 checks 之间短暂失效又恢复：

* 不查询其 low actor；
* action 使用环境 no-op；
* actor hidden 冻结；
* actor loss mask 为 0；
* 不因此伪造 SET；
* 到下一 check 再根据 availability 决定是否正式离队。

这保留固定 (k_0)，避免 failure event 变成额外 high decision opportunity。

---

# 八、GAE 和 PPO 的修改

## 1. High PPO

当前 R30 已经对每个 check 的 token dimension 做平均，使梯度尺度不随 agent 数增长。这个设计可以直接推广到 ragged roster。

[
L_H
===

\frac1B
\sum_{\tau=1}^{B}
\frac{
\sum_jm_{\tau,j}
L_{\tau,j}^{PPO}
}{
\sum_jm_{\tau,j}
}.
]

其中 (m_{\tau,j}) 是 token-valid mask。

高层回报完全不变：

[
R_\tau^H
========

\sum_{r=0}^{L_\tau-1}
\gamma^r r^{env}_{t+r}.
]

不得加入：

* team-size reward；
* join reward；
* survival reward；
* failure penalty；
* KEEP reward；
* membership intrinsic。

仓库当前也明确规定 high return 只能包含 external reward。

## 2. Low PPO 的 team-size exposure

若直接将所有 active agent rows 平铺，大团队会贡献更多 actor samples。

建议固定研究目标：

[
L_L
===

\frac1{|\mathcal T|}
\sum_{(e,t)\in\mathcal T}
\frac1{|A_{e,t}|}
\sum_{i\in A_{e,t}}
L^L_{e,t,i}.
]

这样每个 environment transition 的权重相同，而不是每个 agent row 权重相同。

同时训练时对 team size 做均匀采样：

[
N\sim\operatorname{Uniform}{4,6,8}.
]

否则 (N=8) 会仅因产生更多 agent rows 而主导优化。

## 3. Low trace mask

至少需要：

[
m_{i,t}^{trace}
===============

m_t^{env}
\cdot
m_{i,t}^{membership}
\cdot
m_{i,t}^{availability}.
]

成员永久离开或本轮 membership 结束时，该 agent 的 low trace terminal；其他 agent 不受影响。

---

# 九、不要立即实现真正 ragged Tensor

工程上建议：

[
\boxed{
\text{storage 使用 }N_{\max}\text{ padding}
+
\text{网络和 loss 完全 mask-aware}
}
]

这和“算法固定 (N)”不是一回事。

允许：

* buffer 为 `[B,T,Nmax,...]`；
* inactive slot 零填充；
* GPU batch 使用 mask；
* 按 active count bucketing。

禁止：

* slot embedding；
* agent ID；
* identity-specific skill block；
* dummy slot 改变 logits/value；
* inactive token 产生 PPO loss。

必须通过：

[
f(X\cup{\text{masked dummy}})=f(X).
]

当前 adapter 已经采用 possible-agent padding，但缺少明确 active mask 和正确的 per-agent terminal 语义，因此可保留 padding 策略，不能保留 identity-dependent policy representation。

---

# 十、建议的仓库实现边界

| 文件                                      | 建议修改                                                                                      |
| --------------------------------------- | ----------------------------------------------------------------------------------------- |
| `ha_ctse_process/r30_fixed_clock.py`    | 保留现有类作为 exact fixed-roster control；不在原类中逐步堆条件分支                                           |
| `ha_ctse_process/open_roster_r30.py`    | 新增 `SetRosterAccumulator`、`SetFixedClockAREditPolicy`、`SetHighCheckValue`                 |
| `ha_ctse_process/standalone_agent.py`   | controller factory、membership epoch、join/leave/censor、active-mask low state               |
| `envs/pettingzoo/env_adapter.py`        | 返回 `active_mask`、`agent_terminated`、`env_terminated`；不再用任一 agent terminal 代表 env terminal |
| `ha_ctse_process/collectors.py`         | step payload 加入 active/join/leave mask；spec 加 `max_agents` 和 dynamic-roster capability    |
| `ha_ctse_process/train.py`              | ragged/padded collation、team-balanced low loss、size-bucket collector                      |
| `ha_ctse_process/config_open_roster.py` | 单独配置，不污染当前 R30 default                                                                    |
| `memory/ExpRecord.md`                   | 只注册当前一个 gate，不一次登记全部后续实验                                                                  |

建议添加新的 controller 名称：

```text
r39_set_fixed_clock_ar_edit
```

并保留：

```text
r30_fixed_clock_ar_edit
```

作为 exact compatibility control。

checkpoint 需要新版本：

```text
roster_encoder_version = 1
high_buffer_version = 2
```

迁移只复用兼容的：

* low actor；
* skill FiLM；
* low RNN；
* action head。

新的 set high actor、high critic，以及跨规模 low critic应重新初始化。不要模糊加载固定输入层。

---

# 十一、按当前项目纪律设计的实验晋级路径

## Gate 0：Set-R30 数学与 wiring

这是当前唯一建议立即实施的 gate。

### 数据

从真实 S7-S1 reset/check contexts 取 64 个上下文，不训练策略。

每个 context：

* 32 个随机 agent permutations；
* pad 到 (N_{\max}=8)；
* 随机合法 KEEP/SET teacher-forcing sequence；
* 每个 token 同时进行 full recomputation 和 incremental accumulator。

### PASS

必须全部满足：

[
\max |\Delta keep_logit|<10^{-5},
]

[
\max |\Delta skill_logit|<10^{-5},
]

[
\max |\Delta V|<10^{-5},
]

[
\max |\Delta logp_{\mathrm{replay}}|<10^{-5},
]

以及：

* dummy padding invariance；
* simultaneous permutation equivariance；
* incremental/full roster parity；
* joiner KEEP probability exactly zero；
* leaver token count exactly zero；
* nonzero high gradients；
* zero low-policy drift；
* manifest 中无 agent ID/slot embedding。

### 分支

```text
PASS_OR0
    -> 允许固定 N=6 的 reward-pure pair

INVALID_OR0
    -> 只修 mask/order/logp/shape 具体缺陷

FAIL_OR0_CAPACITY
    -> 若 wiring 正确但 set representation 无法表达已注册的
       synthetic pairwise roster target，退休当前 aggregator
```

禁止通过增加 inducing slots、heads、hidden size 或新特征来事后挽救 valid FAIL。

---

## Gate 1：固定 (N) 的 S7-S1 安全性

比较：

```text
current fixed-roster R30
versus
Set-R30
```

必须保持：

* N 相同；
* low actor 完全相同；
* external reward 相同；
* no intrinsic；
* 同样环境数、步骤、更新、seed、evaluation；
* high actor + critic 参数量相差不超过约 2%。

使用 320K mechanism gate，不作 HMASD parity claim。仓库原则本来就把 320K 视为发现 broken mechanism 的尺度，而不是最终 S7 parity。

### 主要读取

* replay validity；
* reward/coverage safety；
* KEEP fraction；
* all-skill supply；
* survival beyond one block；
* full-sync SET rate；
* token entropy；
* permutation/padding invariance是否在训练后仍保持。

Set-R30 不要求在固定 N 上显著胜出，只要求不造成明显退化和机制坍缩。

### 建议安全门槛

[
\frac{J_{\mathrm{set}}}{J_{\mathrm{fixed}}+\epsilon}\ge0.85,
]

coverage absolute difference 不低于 (-0.05)，zero-service fraction 不增加超过 (0.10)，并且 R30 lifetime safety 全部通过。

有效失败后退休当前 set architecture，不进入 variable-(N)。

---

## Gate 2：跨 episode 可变 (N)

S7 当前设置天然给出了第一组合理规模：

[
N_{\mathrm{train}}={4,6,8},
]

[
N_{\mathrm{heldout}}={5,7}.
]

选择这一范围的原因不是调参，而是仓库的 S7 profile 已经把 `max_observed_uavs` 设为至少 8；先在不修改 low actor 输入容量的范围内验证 high/critic 泛化。

采用 size-bucket collectors：

```text
collector_N4
collector_N6
collector_N8
```

共享同一套网络参数，每个 update 从每个 bucket 取相同数量的 environment transitions。

### Comparator

最干净的 comparator 是同容量的 slot-aware control：

* treatment：无 identity，set-equivariant；
* control：相同 encoder/hidden/optimizer，但加入 slot-specific embedding；
* 两者均能处理 padding；
* 唯一差异是是否依赖固定 slot identity。

### 评估原则

不能直接比较：

[
J(N=4)\quad\text{和}\quad J(N=8).
]

S7 内部部分通信带宽计算直接除以 `n_uavs`，因此不同 N 的原生任务难度和 reward scale 并不相同。必须在**同一个 N 内做 paired treatment-control comparison**。

对每个 N 单独报告：

* native return；
* coverage；
* QoS；
* throughput；
* zero-service episodes；
* lifetime metrics；
* compute/memory。

### PASS

在两个未训练规模 (N=5,7) 上：

* set treatment 的 paired primary metric 平均效应为正；
* 至少一个 held-out N 的置信区间下界大于 0；
* 另一个 held-out N 不发生预注册的 task-safety regression；
* permutation test 仍通过；
* skill/lifetime supply 不坍缩。

小规模 gate 通过后，才进入约 (10^6) steps 的长跑。

---

## Gate 3：episode 内有效 roster 变化

不要新造 toy。使用 S7 已有的 failure machinery。

S7-S4 当前已经有：

```text
uav_failure_enabled = True
uav_failure_probability = 0.001
uav_failure_duration_range = (20, 60)
```

并且环境会让失败 UAV 无法移动、从连接和容量计算中失效，同时继续维持其物理 slot。

比较：

```text
mask_only
versus
membership_censored
```

两臂均使用相同 Set-R30。

### `mask_only`

* inactive agent 不执行动作；
* skill、hidden、age 原样保留；
* 恢复后继续旧 skill。

### `membership_censored`

* 1→0：关闭当前 segment，标记 membership_censored；
* 0→1：新 membership epoch、hidden reset、initial SET；
* surviving agents 完全连续。

### 主指标

实现指标：

[
join_illegal_KEEP=0,
]

[
leave_token_rate=0,
]

[
censored_as_switch=0,
]

[
unaffected_agent_reset=0.
]

科学指标：

* failure 后 0–50 步 coverage/QoS recovery AUC；
* rejoin 后恢复时间；
* zero-service duration；
* surviving agents 的 lifetime continuity；
* team return；
* membership-censored 与 policy-SET lifetime 分布是否正确分离。

这一步只支持“membership semantics 有效”，不能宣称 variable lifetime 更好。

---

## Gate 4：可变成员数 × 可变技能寿命

这一层必须暂时阻塞。

仓库原则明确规定：

> async temporal control 只能在 skill mechanism 已经工作后进行。

因此只有一个 skill semantic mechanism 通过：

[
\text{reward-off natural gate}
\rightarrow
\text{causal }do(z)\text{ gate}
\rightarrow
\text{small reward pair}
]

后，才比较：

[
\begin{aligned}
B:&\quad\text{open-roster full refresh every }k_0,\
C:&\quad\text{open-roster shared fixed lifetime},\
D:&\quad\text{open-roster per-agent KEEP/SET}.
\end{aligned}
]

这时真正的论文因果问题才是：

[
\boxed{
\text{在相同 dynamic roster、相同技能机制和相同 reward 下，}
\quad
D-\max(B,C)>0?
}
]

在此之前，只能证明 open-roster architecture，不得声称 variable skill lifetime 带来了任务优势。

---

# 十二、未来 intrinsic 与可变 (N) 的兼容约束

任何未来 intrinsic 都必须增加以下 null，而不是增加 team-size reward：

1. active-count-matched null；
2. membership-event-matched null；
3. windows crossing join/leave 先判 invalid；
4. teammate statistics 使用 mean/covariance 等 normalized set statistics；
5. 不把 (N)、join、leave、failure duration 作为 skill identity；
6. 不奖励成员存活时间；
7. 不奖励技能跨成员变化继续 KEEP。

尤其要防止：

[
z_i \leftrightarrow N_t
]

成为新的 shortcut。

允许 high policy 根据 team size 选择不同技能，因为这属于合理控制；但 skill semantics 不能只由“这个技能常在 4 架机时出现”来定义。

---

# 十三、真正可能成立的论文创新

仅有以下内容不够新：

* padding + mask；
* variable-length MAT；
* Set Transformer；
* GNN；
* shared actor；
* agent-number curriculum。

MAT 已报告 agent-number 变化下的迁移，UPDeT、DPN/HPN 已处理变长实体和异质配置，open ad hoc teamwork 已研究动态成员组成。甚至 2026 年已有预印本把动态 agent population 与异步 action duration 放在同一框架下。因此“可变 N + 异步决策”本身不足以构成独特贡献。([arXiv][2])

更有希望的论文级对象是：

[
\boxed{
\textbf{Membership-Aware Asynchronous Skill SMDP}
}
]

其独特内容是：

[
\boxed{
\begin{aligned}
&\text{固定 global check clock},\
&\text{动态 active roster},\
&\text{surviving agents 的技能不被 team change 强制重置},\
&\text{离队造成 skill process 右删失而非 policy termination},\
&\text{新成员 initial SET},\
&\text{set-equivariant autoregressive joint editing},\
&\text{per-agent skill lifetime 与 membership lifetime 解耦}.
\end{aligned}
}
]

最有力的核心假设可以写成：

[
\boxed{
\begin{aligned}
&\text{在动态 UAV fleet 中，将 membership transition}\
&\text{与 surviving agents 的 skill renewal 解耦，}\
&\text{能够比 full-team refresh 或 shared lifetime}\
&\text{提供更稳定的成员变化恢复和跨规模合作。}
\end{aligned}
}
]

---

# 当前最优下一步

在 `ffa18c3` 后，建议只注册：

```text
R39-OR0: Set-Roster R30 Fixed-N Compatibility Gate
```

唯一因果边：

```text
identity-indexed fixed-N roster representation
-> set-equivariant roster representation
-> permutation/padding-safe R30 high decisions
-> no fixed-N mechanism or task-safety regression
```

本轮明确禁止：

* 动态 join/leave 训练；
* 新 intrinsic；
* S7-S4 长跑；
* variable lifetime task claim；
* agent-ID embedding；
* task-specific team-size reward；
* learned ordering；
* 新 sampled team latent；
* 修改 KEEP/SET reward；
* 根据结果扩大 inducing slots 或 hidden size。

只有该 gate 通过，才进入 (N={4,6,8}) 训练、(N={5,7}) held-out 的跨规模实验。这样既能利用当前 R30 的成熟时间结构，又不会把 fixed-(N) 架构问题、自然技能形成问题和 sparse-task access 问题重新混为一谈。

[1]: https://arxiv.org/abs/1703.06114 "https://arxiv.org/abs/1703.06114"
[2]: https://arxiv.org/abs/2205.14953 "https://arxiv.org/abs/2205.14953"
[3]: https://arxiv.org/abs/2101.08001 "https://arxiv.org/abs/2101.08001"
[4]: https://arxiv.org/abs/2006.10412 "https://arxiv.org/abs/2006.10412"
