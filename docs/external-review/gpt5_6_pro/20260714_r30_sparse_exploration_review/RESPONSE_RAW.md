## 1. **Verdict**

# **ACCEPT R31**

接受 R31，但必须把它落实为唯一一条明确路线：

> **自然窗口训练、随机干预审计的固定窗口因果效应信息目标**
> Natural-window Causal Fixed-window Effect Information，简称 **R31-CFEI**。

决定性理由是：R31 把优化对象从“一步动作/转移能否识别技能”推进到了“技能是否在相同自然上下文中产生超过随机执行噪声的后半窗状态效应”。这正对应当前缺失的因果边：

[
z_i
\longrightarrow
\text{persistent task-agnostic state effect}
\longrightarrow
\text{broader joint-state visitation}.
]

同时必须采用一项绑定解释：

* **自然 R30 窗口训练 reward scorer；**
* **forced/counterfactual 窗口只做 reward-off 因果审计，不训练在线 reward scorer；**
* “相同 teammate execution”是指相同 teammate skill、策略参数、初始 recurrent state 和共同随机数流，而不是在已经分叉的状态上硬回放同一条 teammate action tape。

这样不会重复 R28 的 forced-domain-to-natural-domain transport 错误。R28 已经证明 forced-deterministic scorer 即使内部表现良好，也可能无法运输到自然随机策略轨迹；当前研究状态则是 forced skill capacity 已存在，但 natural use 仍缺失。

R30 本身无需改动：当前实现已有固定 per-environment clock、完整 all-agent `KEEP/SET` 序列、独立 high-check buffer、combined token likelihood 和 prefix-independent high critic。

---

## 2. **Causal diagnosis of the 64K result**

### 2.1 64K 结果只验证了 R30 temporal mechanism

历史 Alice–Bob pair 使用的是：

[
r_{\rm env}
===========

r_{\rm collection}
+
0.20[\Phi(s_{t+1})-\Phi(s_t)],
]

因此它是：

```text
R30 controller-reward-pure
but Alice–Bob environment-shaped
```

两臂还使用了相同的 transition intrinsic reward，所以 adaptive-versus-shared 差异不能估计 intrinsic reward 的因果作用。

该 pair 支持的只有：

* PPO replay log-probability error 小于 (5\times10^{-7})；
* adaptive full-sync `SET` rate 为 `0.168956`，没有退化成强制同步；
* adaptive 出现 `125` 个超过 (4k_0) 的 skill spells；
* switch-time skill entropy 为 `0.997598`，最小技能份额为 `0.216007`。

因此 R30 已经证明：

[
\text{fixed check}
\neq
\text{realized lifetime},
]

但没有证明：

[
\text{variable lifetime}
\rightarrow
\text{sparse exploration}.
]

当前提交已经正确删除环境 potential shaping；唯一 external reward 是不同智能体同时占据 active button 与 active target 时的一次 collection event。`alice_bob_progress_reward` 仅作为恒等于零的兼容日志字段。

### 2.2 HMASD 内部循环实际提供了四种不同功能

HMASD 的有效内部循环不能简化成“加一个分类器”：

1. **Skill execution capacity**：低层 actor 保持
   [
   \pi_l(a_i\mid o_i,z_i),
   ]
   使 latent 是真正的 executable bottleneck。

2. **State-distribution differentiation**：individual/team discriminators 给低层策略密集压力，使不同 latent 占据可区分的状态/观测分布，而不是只输出不同 action logits。

3. **Cooperative composition**：team skill 与 autoregressive individual assignment 允许后序智能体根据前序技能形成互补组合。

4. **Delayed usefulness credit**：外部任务回报仍由高层/低层 value 和 advantage 传播；discriminator reward 不等于任务有用性。

原 HMASD 代码确实从 next state 和 next observations 计算 team/individual discriminator log-probability，再与环境奖励、entropy 等项组合成低层训练信号；individual discriminator还条件于 team skill。

在 R30 下可以保留的是：

* skill-conditioned recurrent low actor；
* all-agent autoregressive high assignment；
* switch-skill entropy 和 primitive-action entropy；
* task-only high-check return；
* centralized training。

不能原样复制的是：

* 同步刷新下的 `q_D(Z|s)`；
* 一步 `q_d(z_i|o_i,Z)`；
* sampled team skill；
* 依赖 duration、segment length、age 或 task reward 的 semantic score。

R31 只重建 **individual persistent-effect half**。即使成功，它也不会自动恢复 HMASD 的 team-level composition 和 delayed cooperative credit。

### 2.3 当前 transition intrinsic 必须退出在线 reward

当前 `TransitionSkillDiscriminator` 的 full input 是：

[
(o_{i,t},a_{i,t},\Delta o_{i,t},r_t),
]

代码明确把 reward 标准化后与 observation、action 和 observation delta 拼接。

在线路径随后计算：

[
\delta_{i,t}
============

## \log q_\phi(z_i\mid o,a,\Delta o,r)

\max{
\log p_\phi(z_i),
\log q_{\rm ctx}(z_i)
},
]

再执行：

[
r_{i,t}
=======

\operatorname{clip}
\left(
0.02\operatorname{ReLU}(\delta_{i,t}),
0,0.05
\right).
]

`IntrinsicRewardComposer.transition_rewards` 的确使用了 `ReLU` 和非负 clipping。 在线更新将该 reward 直接写入对应 primitive rollout row。

它存在四个根本限制：

* **动作泄漏**：仅靠 skill-specific action pattern 即可提高 posterior；
* **任务奖励泄漏**：collection event 直接进入 discriminator input；
* **时间过短**：一步 (\Delta o) 无法区分 persistent mode 与瞬时 nudge；
* **正部截断**：只奖励容易识别的 transition，负证据不参与目标，鼓励少量高置信局部编码。

历史 late residual-MI 在两臂中仍为负，虽然 positive-residual fraction 和少量正 reward 存在。这说明当前信号“工作了”，但没有建立自然 process semantics。

结论是：

> `TransitionSkillDiscriminator` 可保留为 legacy one-step diagnostic，但在 R31 mode 中其 online reward 必须 fail closed。它不是 R31 的一个附加分量。

---

## 3. **Corrected intrinsic-exploration objective**

### 3.1 Task-agnostic interaction view

定义环境提供的、只包含 agent-controllable interaction state 的视图：

[
x_t
===

g_{\rm eff}(s_t,\mathbf o_t)
\in\mathbb R^{N\times d_x}.
]

Alice–Bob 第一版精确定义为两个智能体的归一化位置：

[
x_t
===

\frac{1}{\text{world_size}}
[p_{1,t}^{x},p_{1,t}^{y},p_{2,t}^{x},p_{2,t}^{y}].
]

当前 centralized state 的前四维正是 agent positions；其余维度包含 active plate/target、clock phases、collection flag、contacts 和前一窗口 occupancy。后面这些字段全部禁止进入 R31 target。

R31 不读取：

* button 或 target offset；
* active button/target identity；
* contact flag；
* task phase；
* task reward；
* collection event；
* environment potential；
* agent ID；
* skill age；
* segment length；
* primitive action。

### 3.2 窗口所有权

每个真实 R30 decision check 在已应用全部 `KEEP/SET` token 后开启一个窗口：

[
t,\ldots,t+W,\qquad W=k_0=10.
]

窗口要求：

* focal skill 在窗口内固定；
* 窗口恰好为 (W) 个 primitive transitions；
* episode terminal 或 PPO update 在 (W) 前截断时，该窗口不用于 posterior 训练，也不产生 reward；
* continuation row 不能开启窗口；
* 一个 check 对每个 agent 最多产生一个 R31 reward opportunity。

R30 已经保证每个真实检查点生成完整 token sequence，并将技能保持到下一次检查。

### 3.3 Persistent effect variable

令

[
\bar x_{-i,t}
=============

\operatorname{mean}*{j\ne i} x*{j,t}.
]

定义 focal-centered late-window effect：

[
\begin{aligned}
E_{i,t}=
\Big[
&x_{i,t+W}-x_{i,t},\
&\bar x_{-i,t+W}-\bar x_{-i,t},\
&\frac{2}{W}\sum_{r=W/2+1}^{W}
(x_{i,t+r}-x_{i,t}),\
&\frac{2}{W}\sum_{r=W/2+1}^{W}
(\bar x_{-i,t+r}-\bar x_{-i,t})
\Big].
\end{aligned}
]

它同时读取：

* focal agent 的 endpoint 和 late-half displacement；
* teammate 的 endpoint 和 late-half response。

因此，它不是独立 wandering 的纯 focal displacement，也不是一步 nudge。技能必须在窗口后半段继续改变 joint interaction state 才会形成信号。

上下文定义为：

[
C_{i,t}
=======

\left[
x_{i,t},
\bar x_{-i,t},
\operatorname{onehot}(\mathbf z_{-i,t})
\right].
]

上下文不包含 focal (z_i)。

### 3.4 Natural-window variational target

训练两个 posterior：

[
q_\phi(z_i\mid E_{i,t},C_{i,t})
]

和 context-only null：

[
q_\psi(z_i\mid C_{i,t}).
]

训练损失为：

[
\mathcal L_{\rm effect}
=======================

\mathbb E_{\mathcal D_{\rm natural}}
\left[
-\log q_\phi(z_i\mid E_{i,t},C_{i,t})
-\log q_\psi(z_i\mid C_{i,t})
\right].
]

所有 ((E,C,z)) 均来自完整的、自然 stochastic R30 窗口。模型输入全部 `stopgrad`，posterior optimizer 不更新 policy、OPT、high editor 或 low actor。

样本 score 为：

[
\delta^{\rm CFEI}_{i,t}
=======================

## \log q_\phi(z_i\mid E_{i,t},C_{i,t})

\log q_\psi(z_i\mid C_{i,t}).
]

当两个 posterior 足够准确时：

[
\mathbb E[\delta^{\rm CFEI}]
\approx
I(Z_i;E_i\mid C_i)
]

是在自然 learned skill usage 下的 conditional effect information。这里不使用 uniform prior，因此不会把非均匀 skill usage 误解释成自然 MI。

### 3.5 Nulls

R31 使用三种不同功能的 null：

1. **Context null**
   (q_\psi(z_i\mid C_i)) 控制自然 skill usage、初始状态和 teammate roster。

2. **Matched shuffle null**
   在相同 teammate-skill roster 和相邻 start-state bin 内置换 (E)，计算：
   [
   \delta_{\rm shuf}
   =================

   ## \log q_\phi(z_i\mid E_i^{\rm shuf},C_i)

   \log q_\psi(z_i\mid C_i).
   ]
   shuffle 只用于 gate，不进入在线 reward 公式。

3. **Same-skill stochastic-repeat null**
   在因果 probe 中，同一 skill 的两个 stochastic replicas 估计执行噪声。它不由分类器产生。

### 3.6 Reward-off causal intervention

在自然 R30 decision context (c) 上复制：

* simulator state；
* environment RNG state；
* 所有 agent 的 low actor recurrent states；
* teammate skills；
* 当前 frozen policy parameters。

对 focal agent (i) 分别强制所有候选 (z)，持续 (W=k_0)；其他 agent 保持相同 skills 和 policy。每个 skill 做两次 stochastic replica。

在同一 replica index 内，各 skill branch 使用 common random numbers。不同 replica index 使用独立随机流。

重要的是，teammate 不回放固定 action tape。它们在各分支中按：

[
a_{j,r}
\sim
\pi_l(a_j\mid o_{j,r},z_j)
]

正常响应，但具有相同初始 hidden state 和匹配随机数。这是 focal-skill intervention 的 total environmental effect，而不是在 counterfactual state 上强制 off-policy teammate action。

对 skill pair ((z,z'))，定义：

[
d_{\rm between}
===============

\frac12
\left(
|E_z^{(1)}-E_{z'}^{(1)}|*2^2+
|E_z^{(2)}-E*{z'}^{(2)}|_2^2
\right),
]

[
d_{\rm within}
==============

\frac12
\left(
|E_z^{(1)}-E_z^{(2)}|*2^2+
|E*{z'}^{(1)}-E_{z'}^{(2)}|_2^2
\right),
]

[
R_{\rm causal}
==============

\frac{d_{\rm between}}{d_{\rm within}+\epsilon}.
]

该 probe 同时检查 frozen natural posterior 对 forced branch 的 residual score，但 **forced windows不进入 posterior loss**。

这解决了 R28 的 transport 问题：

* reward scorer 只在 natural windows 上训练和使用；
* forced windows只是 held-out causal audit；
* forced execution为当前 stochastic policy；
* 若 forced branches 对 natural posterior 是 OOD 或没有稳定效应，gate 直接失败，不开启 reward。

### 3.7 OPT 的边界

首个 R31 不使用 OPT compact 作为 effect、context 或 reward input。

原因是当前 `InteractionCompactEncoder` 同时读取 centralized state 和 joint observations，并随 high-policy训练更新；Alice–Bob state 又含 active task identity、phase、contact 等禁用字段。

允许记录：

[
\operatorname{stopgrad}(c_{t+W}-c_t)
]

作为非决策诊断，但它不能进入：

* (q_\phi)；
* (q_\psi)；
* causal ratio；
* intrinsic reward。

---

## 4. **Reward, gradient, window, and null contract**

### 4.1 Reward formula

只有 reward-off gate 通过后才启用：

[
r^{\rm R31}_{i,t+W-1}
=====================

\operatorname{clip}
\left(
0.02,
\operatorname{stopgrad}
[
\delta^{\rm CFEI}_{i,t}
],
-0.05,
0.05
\right).
]

低层 rollout reward 变为：

[
\widetilde r^{\rm low}_{i,\tau}
===============================

r^{\rm task}*\tau
+
\mathbf 1[\tau=t+W-1]
r^{\rm R31}*{i,t}.
]

不使用 `ReLU`。完整 signed log-ratio 才对应 conditional-information variational objective；只保留正部会重新鼓励少量容易分类的窗口。

系数 `0.02` 和 clip `0.05` 沿用当前 Alice–Bob transition signal 的量级，作为 no-sweep migration。

### 4.2 Scoring/update order

对 update (u)：

1. 使用 update (u-1) 结束时冻结的
   ((\bar\phi,\bar\psi)) 对本 rollout 的完整 natural windows 评分；
2. 将 endpoint reward 写入低层 rollout；
3. 计算 low GAE/PPO；
4. 使用本 rollout 的 detached natural windows 更新
   ((\phi,\psi))；
5. 将新 posterior 冻结，供下一 rollout 使用。

不能用同一 minibatch先拟合再评分，否则 posterior 能通过短期记忆制造虚假 intrinsic reward。

### 4.3 Gradient contract

| 项目                              | 梯度                                            |
| ------------------------------- | --------------------------------------------- |
| (q_\phi,q_\psi) supervised loss | 只更新 R31 posterior                             |
| (E,C)                           | 全部 detached                                   |
| R31 reward                      | detached                                      |
| low actor                       | 只通过 PPO log-probability × shaped advantage 更新 |
| low critic                      | 拟合 task + R31 low return                      |
| R30 high actor/critic           | 只接收 sparse external task return               |
| OPT/bridge                      | 不接收 R31 gradient                              |
| forced probe                    | 全部 reward-off，不更新任何 policy                    |

当前 high buffer在 primitive step时直接累积原始 scalar environment reward；R31 的 low reward在 rollout 后续处理阶段注入，因此无需也不得修改 high-check reward。

### 4.4 为什么不会直接奖励长 lifetime

* 每个 agent 每个 fixed check block 最多一个 endpoint reward；
* reward数量按环境时间而不是 segment 数计算；
* effect window长度固定为 (W=k_0)；
* score不读取 age 或 lifetime；
* R31 reward完全不进入 R30 high return；
* `KEEP` 不会因为延长 skill 而直接获得 intrinsic advantage。

持续 `KEEP` 的 skill会得到更多低层行为样本，因为它确实执行了更多 primitive steps；但 high-level survival decision只能通过 sparse task advantage受益。

### 4.5 Fail-closed conditions

R31 mode 中以下任一项应直接拒绝启动：

```text
alice_bob_progress_reward != 0
current transition-skill reward active
R28/R29 online reward active
effect window W != k0
effect input contains task reward/contact/target/button/phase
high return contains R31 reward
incomplete effect window receives reward
```

---

## 5. **Exact code change map**

### `envs/pettingzoo/alice_bob_asymmetric_cycles.py`

新增：

```python
def intrinsic_effect_view(self) -> np.ndarray:
    # shape [2, 2]
    return self.agent_pos / self.world_size
```

只返回 normalized agent positions。

另为 reward-off probe 新增完整 simulator snapshot/restore：

```python
get_probe_snapshot()
set_probe_snapshot(snapshot)
```

snapshot 应包含 positions、steps、active plate/target、window flags、counts 和 RNG bit-generator state。后面这些字段用于精确恢复 simulator，但不得进入 effect vector。

当前 environment reward 保持 collection-only，不做任何 shaping 修改。

### `ha_ctse_process/config_alice_bob_asymmetric.py`

将：

```python
alice_bob_semantic_reward_enabled = False
transition_skill_reward_coef = 0.0
```

新增唯一 R31 配置：

```python
r31_effect_mode = "off"       # off, probe_only, real_reward
r31_effect_window = 10        # 必须等于 skill_interval
r31_effect_coef = 0.02
r31_effect_clip = 0.05
r31_effect_hidden_dim = 64
r31_effect_schema_version = 1
```

禁止新增 coefficient 列表或 sweep 字段。

### `ha_ctse_process/config_alice_bob_shared_k.py`

保持 frozen R30 temporal comparator。

它不是 R31 reward comparator。R31 reward-on实验只能比较：

```text
R30 + probe_only
versus
R30 + real_reward
```

当前 shared-k config 只是将 `r30_force_refresh_every_check=True`。

### `ha_ctse_process/process_posterior.py`

保留 `TransitionSkillDiscriminator` 作为 legacy diagnostic。

新增：

```python
class FixedWindowEffectPosterior(nn.Module):
    full_logits(effect, context)
    context_logits(context)
    losses(...)
```

它不读取：

```text
actions
rewards
duration
age
agent_id
phase
OPT compact
```

`TransitionSkillDiscriminator` 当前明确是一步 `(obs, action, delta_obs, reward)` posterior，因此不得被简单扩展窗口后重用。

### `ha_ctse_process/intrinsic_rewards.py`

新增 signed reward：

```python
def effect_information_reward(delta, coef, clip, enabled):
    raw = coef * delta
    reward = torch.clamp(raw, -clip, clip) if enabled else zeros
```

不得调用现有 `transition_rewards()`，因为该函数强制执行 `ReLU` 和非负 clip。

### 新增 `ha_ctse_process/r31_effect_information.py`

拥有：

```text
EffectWindowRow
EffectWindowBuffer
build_effect_and_context
matched_context_shuffle
FixedWindowEffectScorer
causal_between_within_metrics
```

`EffectWindowRow` 至少保存：

```text
env_id, episode_id, policy_update
start_rollout_index, endpoint_rollout_index
start_effect_view
effect_view_sequence [W+1, N, d_x]
active_skills [N]
complete, terminal, policy_truncated
```

不保存 task reward为模型输入。

### `ha_ctse_process/r30_fixed_clock.py`

不改变 `KEEP/SET` policy、high critic 或 PPO。

只允许增加一个轻量 decision-event hook，使 R31 知道何时全体 token 已应用。现有 working roster replay和 high rows保持原样。当前 high buffer已经清楚区分 decision与continuation rows。

### `ha_ctse_process/standalone_agent.py`

在 `_r30_maybe_assign_skills` 中，完成：

```python
self.active_skills = sample.final_skills
```

之后开启 R31 window。此时保存的是 post-edit active roster，而不是 pre-check roster。当前技能应用发生在这里。

在 `record_environment_step` 中：

* append新的 effect view；
* 到 (W) 后关闭窗口；
* terminal/update truncation前不足 (W) 的窗口标为 invalid；
* 不通过 `SegmentManager` 构造 R31 窗口。

新增：

```python
_r31_score_complete_windows()
_r31_update_effect_posterior()
```

执行顺序必须为：

```text
score with previous frozen posterior
-> inject low endpoint rewards
-> low GAE/PPO
-> update posterior
```

`_r30_transition_skill_update` 在 R31 mode 中不调用。当前该函数负责训练一步 posterior并直接写入 rollout rewards，因此必须显式分流，而不是让两个奖励同时存在。

### `ha_ctse_process/train.py`

collector 每步获得：

```python
effect_view = env.intrinsic_effect_view()
```

并传给 R31 buffer。

在现有：

```text
process_update
-> update_low
-> update_high_from_checks
```

之前插入 R31 scoring/update边界，但不改变 high-row raw reward。当前训练循环已在 low update前完成 process/reward处理，并独立调用 `update_high_from_checks`。

新增：

```text
--r31_effect_mode off|probe_only|real_reward
```

并在 R31 contract 中检查旧 transition reward关闭。

### 新增 `scripts/r31_causal_effect_gate.py`

只做 reward-off shadow intervention：

* sync Alice–Bob environment；
* frozen checkpoint；
* snapshot/restore；
* common-random-number stochastic branches；
* reset-cluster bootstrap；
* 不写 policy checkpoint，不更新 policy。

### Checkpoint

保存：

```text
r31_effect_schema_version
effect_posterior
effect_context_posterior
effect_optimizer
effect_gate_status
effect_view_name
```

从普通 R30 checkpoint进入 R31 时：

* 复用 high、low、OPT、ValueNorm；
* 新建 effect posterior和optimizer；
* 不恢复 legacy transition posterior optimizer状态；
* `probe_only` 与 `real_reward` 必须从同一个 gate-passed R31 checkpoint开始。

`hmasd/networks.py` 和 `hmasd/agent.py` 不修改，只作为结构参考。

---

## 6. **Smallest reward-off gate and conditional reward-on comparison**

全流程只使用四个决策指标。

### 6.1 Reward-off causal gate

使用一个 frozen R30 checkpoint，关闭当前 transition reward。

自然数据：

```text
64 stochastic reset groups
8 complete k0 windows per episode
2 agents
up to 1,024 natural windows
48 reset groups for posterior training
16 held-out reset groups
```

因果数据：

```text
128 held-out natural decision contexts
focal agent alternates by context
4 forced skills per context
2 stochastic replicas per skill
W = 10
1,024 forced windows
10,240 shadow primitive steps
```

所有置信区间按 reset/context cluster bootstrap，10,000次。

#### M1 — Natural residual effect information

[
G_{\rm nat}
===========

\mathbb E_{\rm heldout}
[\delta^{\rm CFEI}].
]

PASS要求：

[
G_{\rm nat}\ge0.02\ {\rm nats},
\qquad
CI_{95%,lower}>0,
]

且每个 skill 的 held-out mean 至少 `0.005` nats。

#### M2 — Interventional persistence versus null

定义前述 (R_{\rm causal})。

PASS同时要求：

[
\operatorname{median}(R_{\rm causal})\ge1.5,
\qquad
CI_{95%,lower}>1.0,
]

没有任何 skill 的 pooled ratio 小于 `1.0`，并且：

[
|G_{\rm shuffle}|
\le
\min(0.005,;0.25G_{\rm nat}).
]

### Reward-off interpretation

* **PASS**：M1、M2全部通过；唯一授权动作是启动下述 matched reward-on pair。
* **FAIL**：M1 point estimate (\le0)、causal ratio (\le1)，或 shuffle超过真实信号一半；唯一动作是退休 R31-CFEI，不开启 reward。
* **UNDERPOWERED**：point estimate达到PASS方向，但CI跨过阈值，或任一skill少于64个held-out自然窗口；唯一动作是追加一批相同的64 reset reward-off数据，不修改目标或阈值。

### 6.2 Conditional reward-on comparison

只有 reward-off PASS 后运行：

```text
arms:       probe_only versus real_reward
controller: identical adaptive R30
source:     same gate-passed R31 checkpoint
seed:       31031, paired streams
envs:       16
updates:    20
exposure:   160,000 environment transitions per arm
low PPO:    5 epochs
evaluation: 40 deterministic 80-step episodes
external reward: sparse collection-only
```

`probe_only` 与 `real_reward`：

* 构造相同 natural windows；
* 更新相同 posterior；
* 计算相同 score；
* 唯一区别是 endpoint reward是否写入 low rollout。

#### M3 — Mechanism and exploration movement

要求：

[
(G_{\rm nat}^{real}-G_{\rm nat}^{probe})
\ge0.02\ {\rm nats},
\qquad CI_{lower}>0.
]

同时在 task-agnostic joint-position view上，将四个坐标各分成5个固定 bins，共625个 joint cells。要求：

[
\frac{
Coverage_{\rm real}-Coverage_{\rm probe}
}{
\max(Coverage_{\rm probe},\epsilon)
}
\ge0.10,
\qquad CI_{lower}>0.
]

这检查 reward是否扩大 joint interaction-state visitation，而不是只提高分类器分数。

#### M4 — Sparse task access and R30 safety

要求 deterministic evaluation 中：

[
\overline{targets_completed}_{real}
-----------------------------------

\overline{targets_completed}_{probe}
\ge0.25
]

每个80-step episode，且paired-reset 95% lower bound (>0)。

同时保持：

[
full_sync_SET_rate\le0.50,
]

[
H(Z\mid SET)/\log K\ge0.80,
]

[
\min[P(T>4k_0),P(T\le4k_0)]\ge0.05.
]

### Reward-on interpretation

* **PASS**：M3、M4全部通过。支持 R31进入预注册多种子 sparse experiment。
* **FAIL**：

  * M1上升但coverage或task不升：persistent skill identifiability不等于exploration/usefulness，退休该reward；
  * M1不升：reward没有改变目标机制，退休该reward；
  * lifetime/skill supply collapse：退休该reward，不加keep entropy或调系数。
* **UNDERPOWERED**：M1和coverage通过，但两臂合计少于5次evaluation collection event；唯一动作是添加一个相同 exposure 的 paired seed `31032`，不改变算法、系数或阈值。

---

## 7. **Claims allowed and prohibited**

### Reward-off PASS 后允许的结论

可以支持：

> 在自然 R30 检查上下文中，改变一个智能体的 persistent skill，同时保持 teammate policies、initial recurrent states和随机执行机制匹配，会在 (W=k_0) 后产生超过同技能 stochastic variability 的 task-agnostic joint-state effect；自然窗口 posterior 捕获了该因果效应，而非仅恢复上下文中的 skill usage。

不能支持：

* task improvement；
* sparse exploration成功；
* cooperative composition；
* HMASD parity；
* variable lifetime优于shared/fixed lifetime；
* online reward有用。

### Reward-on PASS 后允许的结论

可以支持狭窄结论：

> 在 collection-only sparse Alice–Bob 中，固定窗口因果效应信息作为 detached、endpoint、low-GAE-only reward，提高了自然 persistent-effect information 和 task-agnostic joint-state coverage，并增加了 sparse collection access，且没有使 R30 lifetime或skill usage坍缩。

### 始终禁止的结论

即使全部PASS，仍不得宣称：

* 已完整重建 HMASD；
* 已恢复 team discriminator或team skill；
* 已证明 skills 具有人类可解释的 button/target语义；
* 已证明异步 lifetime 是收益来源；
* 已证明 delayed cooperative credit已解决；
* 已证明跨环境或S7泛化；
* 已达到HMASD性能；
* effect posterior估计的是精确 mutual information；
* forced probe rollout可以直接作为在线reward；
* 原64K shaped pair是sparse-exploration证据；
* action entropy、switch-skill entropy或classifier accuracy本身证明语义。

R31-CFEI 解决的是一个边界明确的中间问题：

[
\boxed{
\text{natural skill}
\rightarrow
\text{persistent controllable joint-state effect}
\rightarrow
\text{task-agnostic exploration pressure}
}
]

它尚未解决的是：

[
\text{individual effects}
\rightarrow
\text{complementary team composition}
\rightarrow
\text{long-horizon cooperative usefulness}.
]

