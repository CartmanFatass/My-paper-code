# GPT-5.6 Pro R39 Compatibility Follow-up — Formal Response

## 1. Verdict

```text
MODIFY R39-S7 HMASD-compatible temporal decoupling
```

R39 的研究方向仍然成立，但不能按先前的“直接从历史 checkpoint 分叉”方案执行。决定性原因有两个：

1. 历史 `best_model.pt` 只保存到 1.760M steps，属于旧六智能体、三维动作、旧 load-balance S7 接口；当前 S7-S1 是八智能体、四维动作、Scenario-7 interface v3。旧 checkpoint 缺少当前 `policy_interface` / `training_interface` 元数据，不能作为当前 fixed-`k` 或 async arm 的权重来源。
2. `ha_ctse_process.FixedClockAREditPolicy` 不是原 HMASD `SkillCoordinator` 的兼容包装。它改变了高层网络、价值函数、buffer、optimizer、trainer 和语义回路，不能充当“只改变 lifetime”的 treatment。

因此唯一可执行路线必须是严格串行的两阶段：

```text
Stage A:
current-interface fixed-k HMASD from scratch
-> positive S7-S1 anchor

Stage B:
the same native HMASD checkpoint/code
-> fixed full-refresh control
   versus
   native per-agent KEEP/SET treatment
-> service preservation + genuine desynchronization
```

Stage A 未通过前，Stage B 不得实现或运行。

---

## 2. Repository facts and scientific inference

### 2.1 Repository facts

- 历史 HMASD 训练后来停止于 2.112M steps，但有效 `best_model.pt` 保存于 1.760M steps；旧 final-episode coverage 是 `0.9250`，`0.9639` 是最后三个 evaluation points 的均值，不是 checkpoint 指标。
- 旧 checkpoint 的接口是 6 agents、state 236、observation 252、action dimension 3；当前 `config_1.py` 的 S7-S1 是 8 agents、action dimension 4、Scenario-7 interface v3。
- 当前 `HMASDAgent.load_model` 会因缺少或不匹配的 interface metadata 拒绝旧 S7 checkpoint。不得用 `strict=False` 绕过这一边界。
- 原 HMASD 高层策略是 Transformer `SkillCoordinator`：

\[
\pi_H(Z,\mathbf z\mid x)
=
\pi_Z(Z\mid x)
\prod_{i=1}^{N}
\pi_i(z_i\mid Z,z_{<i},x).
\]

它带有 team/agent value heads，并由原 `hmasd.agent.HMASDAgent`、原 buffer、原 optimizer 和原更新顺序训练。
- standalone R30 的 `FixedClockAREditPolicy` 是另一套 MLP controller；其 `force_refresh_every_check` 不调用原 HMASD joint assignment path，也不保留完整原始 `q_D/q_d` 训练闭环。
- commit `aaba845` 已修复一个真实前置缺陷：`SkillCoordinator.evaluate_training_batch` 现在使用存储的 `Z,z_{<i}` teacher forcing 重算执行过的 joint action likelihood，而不重新采样 conditioning chain。
- 当前 S7-S1 的原生配置支持无 graph-potential 的 `qos_fixed_safety` reward variant。R39 不需要、也不得增加 environment shaping。

### 2.2 Scientific inference

历史运行只能证明“旧 HMASD policy class 曾经能访问旧 S7”，不能证明当前 S7 substrate 已有正向 anchor，也不能作为当前因果 comparator。

可识别的 temporal effect 必须来自：

\[
\text{同一当前 HMASD checkpoint}
+
\text{同一 coordinator/discoverer/discriminators/trainer}
+
\text{仅改变 individual renewal semantics}.
\]

如果 current-interface fixed-`k` HMASD 本身不能建立正向 service anchor，则这只说明当前 substrate / fixed HMASD reproduction 未关闭，不能解释为 asynchronous lifetime 失败。

---

# 3. Reusable causal conclusion

\[
\boxed{
\text{Historical algorithm success is not a warm start when the policy interface changed.}
}
\]

并且：

\[
\boxed{
\text{A temporal-abstraction comparison is valid only when the full-refresh
control and the partial-renewal treatment are two modes of the same native
high policy, buffer, optimizer, intrinsic loop, and environment contract.}
}
\]

R39 不重新设计 intrinsic reward。它保留当前 HMASD 的通用 `q_D/q_d` 路径，并禁止加入任何 S7-specific intrinsic、distance/contact/coverage bonus、potential shaping 或 external-reward-derived auxiliary target。R39 的结论只涉及 temporal compatibility 和 renewal semantics，不验证 `q_D/q_d` 的跨环境一般性。

---

# 4. Stage A — Current-interface fixed-`k` HMASD positive-anchor gate

## 4.1 Single causal edge

\[
\boxed{
\text{current-interface native fixed-}k\text{ HMASD}
\rightarrow
\text{stable positive S7-S1 service access}
}
\]

这是 source-anchor gate，不是 asynchronous algorithm test。

## 4.2 Algorithm and environment contract

使用原 `hmasd` trainer/collector，从零初始化训练：

```text
algorithm                     = native HMASD
preset                        = S7-S1
scenario7 interface           = v3
n_agents                      = 8
action_dim                    = 4
action distribution           = tanh Gaussian
n_Z                           = 6
n_z                           = 6
k                             = 10 primitive steps
episode_length                = 500
rollout_length                = 500
strict_hmasd_alignment        = true
use_horizon_window            = false
use_process_exploration       = false
use_opt                       = false
use_team_bridge               = false
disable_high_level_training   = false
disable_discriminator_training= false
disable_discriminator_rewards = false
```

外部 reward 固定为：

```text
scenario7_experiment_arm = C
scenario7_reward_variant = qos_fixed_safety
use_graph_pbrs           = false
```

启动顺序必须在应用 S7-S1 preset 和 arm C 后再次冻结 `qos_fixed_safety`，并在 manifest 中 fail-closed 验证最终 `use_graph_pbrs == false`。

保留原 HMASD 系数和更新顺序：

```text
lambda_e = 1.0
lambda_D = 0.05
lambda_d = 0.02
lambda_h = 0.07
lambda_l = 0.005
gamma = 0.99
GAE lambda = 0.95
PPO clip = 0.20
PPO epochs = 15
num_mini_batch = 4
actor/critic/coordinator/discriminator lr = current config values
ValueNorm and recurrent discoverer = current native implementation
```

不加入新 reward、classifier、latent、scheduler、process scorer 或 HA-CTSE module。

## 4.3 Exact exposure

```text
train seed          = 39039
num_envs            = 32
rollout_length      = 500
outer updates       = 100
total env steps     = 32 * 500 * 100 = 1,600,000
final checkpoint    = exactly the 1,600,000-step checkpoint
```

不得用 best-of-evaluation checkpoint、自动 early stopping、额外 seed 或追加预算替代该 final checkpoint。

Stage A 的 final evaluation：

```text
episodes            = 100 stochastic episodes
episode horizon     = 500
reset seeds         = 139039 ... 139138
bootstrap draws     = 10,000
bootstrap seed      = 40039039
resampling unit     = whole episode
```

## 4.4 Exact service estimands

每个 evaluation primitive step 读取原生：

\[
c_{e,t}
=
\texttt{reward\_info["coverage\_ratio"]}\in[0,1].
\]

定义：

\[
C_{\mathrm{mean}}
=
\frac{1}{EH}
\sum_{e=1}^{E}\sum_{t=1}^{H}c_{e,t},
\]

\[
C_{\mathrm{full}}
=
\frac{1}{EH}
\sum_{e,t}\mathbf 1[c_{e,t}\ge 1-10^{-6}],
\]

\[
F_{\mathrm{zero}}
=
\frac1E
\sum_e
\mathbf 1\!\left[\max_t c_{e,t}\le10^{-6}\right].
\]

QoS、throughput、安全和 reward 分量只作 diagnostics，不替换上述 positive-anchor estimand。

## 4.5 Stage A validity and decision

### M0-A — implementation validity

必须全部满足：

- current S7 interface manifest 精确为 8 agents / 4 actions / v3；
- final reward variant 是 `qos_fixed_safety`，graph PBRS 和其它 shaping 为零；
- exactly 1,600,000 environment steps 和 100 outer updates；
- no HA-CTSE/R30/partial-KEEP path；
- coordinator、discoverer、discriminator 均按原顺序更新；
- stored joint high action 的 team/agent maximum replay log-probability error：

\[
\le 10^{-6};
\]

- checkpoint 含当前 `policy_interface`、`training_interface`、所有原生 module、normalizer 和 optimizer state；
- 所有参数、actions、values 和 losses finite。

M0-A miss：

```text
INVALID_R39A_IMPLEMENTATION
```

唯一下一动作：只修具体 current-HMASD wiring defect，按完全相同合同重跑 Stage A。

### M1-A — positive anchor

使用 episode bootstrap 的 percentile 95% interval，要求：

\[
LCB_{95}(C_{\mathrm{mean}})\ge0.90,
\]

\[
LCB_{95}(C_{\mathrm{full}})\ge0.50,
\]

\[
UCB_{95}(F_{\mathrm{zero}})\le0.10.
\]

PASS：

```text
PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR
```

唯一下一动作：冻结该 exact checkpoint 和 manifest，授权实现并注册 Stage B。

Valid fail：

```text
VALID_FAIL_R39A_NO_CURRENT_HMASD_ANCHOR
```

条件：M0-A 通过但任一 M1-A 条件失败。

唯一下一动作：停止 R39 temporal treatment；将结果归档为 current-interface fixed-HMASD/S7 substrate 未复现。不得实现 async arm，不得自动调参、扩 seed、追加预算、恢复旧 checkpoint 或加入 shaping/intrinsic rescue。

该失败不支持“asynchronous lifetime 无效”或“HA-CTSE 无效”。

---

# 5. Stage B — HMASD-native fixed-`k` versus per-agent KEEP/SET

Stage B 只在 `PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR` 后运行。

## 5.1 Single causal edge

\[
\boxed{
\text{native HMASD full-refresh assignment}
\rightarrow
\text{native partial-roster KEEP/SET semantics}
\rightarrow
\text{noninferior service plus genuine per-agent lifetime decoupling}
}
\]

## 5.2 Team `Z` lifetime: renew at every global check

唯一选择：

\[
Z_\tau\sim\pi_Z(Z\mid x_\tau)
\quad\text{at every }k_0=10\text{-step check}.
\]

`Z_\tau` 在接下来的一个 check block 内保持不变，下一个 check 重新采样。

理由：

- 这精确保留原 HMASD team-policy、team-value 和 `q_D(Z|s)` 的固定全局信息时钟；
- 不需要新增 team termination action 或新 team latent；
- `Z` 不进入低层 actor，因此更新 `Z` 不会重置或替换 agent 的可执行技能；
- 每个 active \(z_i\)、其 age 和 low recurrent state 可跨多个 `Z` blocks 连续存在；
- `q_d` 在每个 primitive transition 使用当前 pair \((Z_\tau,z_i)\)：

\[
q_d(z_i\mid o_i,Z_\tau).
\]

因此改变的是 cooperative conditioning context，不是 individual skill renewal。

持有 `Z` 直到所有 agent 同时 SET 会把 `Z` lifetime 绑定到最长个体 lifetime；新增 `Z` KEEP/REFRESH 又会引入第二个未经授权的 temporal action。两者均不采用。

## 5.3 Native effective action without action-space expansion

对每个 check，先由原 `SkillCoordinator` 采样 \(Z_\tau\)。随后按原固定 agent order 处理每个 agent。

令：

- \(r_{\tau}^{(i)}\)：处理 agent \(i\) 前的 working roster；
- \(a_{\tau}^{(i)}\)：对应 working ages；
- \(l^{\mathrm{orig}}_{i,\tau}(z)\)：原 `SkillDecoder` 在 stored \(Z_\tau\) 和已应用的前序 skill prefix 下产生的 \(K\) 个 skill logits；
- \(\rho_{\tau}^{(i)}\)：task-blind roster/age feature，只含：
  - 每个 agent 的 active flag；
  - 每个 agent 当前 skill one-hot；
  - `log1p(age_i / k0)`；
  - focal-agent one-hot。

新增一个共享 residual module：

\[
\Delta l_{i,\tau}
=
f_{\mathrm{roster}}(\rho_{\tau}^{(i)})\in\mathbb R^K.
\]

网络固定为：

```text
LayerNorm[N*(K+2)+N]
-> Linear(..., embedding_dim)
-> GELU
-> Linear(embedding_dim, K)
```

最后一层 weight 和 bias 精确初始化为零，所以初始：

\[
\Delta l_{i,\tau}=0.
\]

effective logits：

\[
l_{i,\tau}(z)
=
l^{\mathrm{orig}}_{i,\tau}(z)
+
\Delta l_{i,\tau}(z).
\]

采样一个 categorical category：

\[
y_{i,\tau}\sim\operatorname{Cat}(\operatorname{softmax}(l_{i,\tau})).
\]

若 agent 尚未 active：

\[
e_{i,\tau}=\operatorname{SET}(y_{i,\tau}).
\]

若 agent 已 active，且 incumbent 为 \(r_{\tau,i}^{(i)}\)：

\[
e_{i,\tau}
=
\begin{cases}
\operatorname{KEEP},&
y_{i,\tau}=r_{\tau,i}^{(i)},\\
\operatorname{SET}(y_{i,\tau}),&
y_{i,\tau}\ne r_{\tau,i}^{(i)}.
\end{cases}
\]

因此每个 agent 始终只有 \(K\) 个有效 category：

```text
one incumbent category -> KEEP
K-1 other categories   -> SET(other skill)
```

不存在 `K*D` 扩张，也不存在 `KEEP` 与 `SET(current)` 的重复支持。

### Exact warm-start identity

当 residual 为零时：

\[
P_{\mathrm{partial}}(\operatorname{KEEP})
=
\operatorname{softmax}(l^{\mathrm{orig}})_{r_i},
\]

\[
P_{\mathrm{partial}}(\operatorname{SET}(z))
=
\operatorname{softmax}(l^{\mathrm{orig}})_z,
\quad z\ne r_i.
\]

所以 treatment 初始的 **final-skill distribution 与原 full-refresh categorical 完全相同**。唯一差异是：抽到 incumbent category 时，full-refresh control 将其记为一次 SET(current) 并重置 age；treatment 将其解释为 KEEP 并延续 lifetime。低层 actor、skill label 和 recurrent state 在该瞬间不变。

这比新增独立 keep head 更小，也避免任意 `p_keep_init`。

## 5.4 Incumbent roster and autoregressive prefix

每个 token 前：

1. working roster 从 pre-check incumbent roster 开始；
2. 已处理 agent 的 KEEP/SET 立即应用；
3. 原 `SkillDecoder` 使用 stored \(Z_\tau\) 和前序 **post-edit skill values** teacher forcing；
4. `f_roster` 同时读取完整当前 working roster 和 ages，因此 agent \(i\) 的 logits 显式条件于：
   - 所有 incumbent skills；
   - 已发生的前序 edits；
   - 仍未处理 agent 的 incumbent skills；
   - 当前 lifetime ages。

这是唯一新增 context；不得加入 S7 goal、coverage、distance、contact、QoS、reward 或 success fields。

## 5.5 Exact behavior and PPO replay probability

每个 check 存储：

```text
pre-check state and joint observations
pre-check active skills
pre-check ages and active masks
agent order
sampled team Z
sampled categorical y_i for every agent
derived KEEP/SET token
old team log-prob
old per-agent categorical log-prob
pre-action team value
pre-action agent values
block reward, block length, terminal flag
```

行为概率：

\[
\log\pi_\theta(A_\tau\mid x_\tau)
=
\log\pi_Z(Z_\tau\mid x_\tau)
+
\sum_{i=1}^{N}
\log
\operatorname{Cat}
\!\left(
y_{i,\tau};
l_{i,\tau}
\right).
\]

PPO recomputation 必须：

- teacher-force stored \(Z_\tau\)；
- 使用相同 stored agent order；
- 从 stored incumbent roster/ages 重建 working roster；
- teacher-force每个 stored \(y_{i,\tau}\)；
- 每一步应用相同 KEEP/SET mapping；
- 使用与采样完全相同的 effective support。

team ratio：

\[
r_\tau^Z
=
\exp(
\log\pi_Z^{new}
-
\log\pi_Z^{old}
).
\]

agent token ratio：

\[
r_{\tau,i}
=
\exp(
\log\pi_i^{new}(y_{i,\tau})
-
\log\pi_i^{old}(y_{i,\tau})
).
\]

每个 agent token 只有一个 combined categorical ratio；不得将 KEEP 与 skill factor 分开 clip。

## 5.6 High-level credit

保持当前 native HMASD block semantics，不把 variable process segment 当作 high sample。

对于 check \(\tau\)，block 长度 \(L_\tau\le k_0\)：

\[
R_\tau^H
=
\sum_{r=0}^{L_\tau-1}
r^{env}_{t_\tau+r}.
\]

这是当前 HMASD collector 的 repository-native block sum。高层跨 block discount：

\[
\Gamma_\tau=\gamma^{L_\tau}.
\]

使用原 team value head 和 per-agent value heads计算：

\[
A_\tau^Z,\qquad A_{\tau,i}^{z}.
\]

- sampled \(Z_\tau\) 使用 \(A_\tau^Z\)；
- 每个 KEEP/SET categorical token使用对应 \(A_{\tau,i}^{z}\)；
- token dimension 取均值，避免 gradient scale 随 agent 数增长；
- high return 中不加入 lifetime reward、KEEP reward、switch penalty、coverage、QoS、`q_D/q_d` 或任何新 intrinsic。

低层 discoverer 保持原 HMASD reward 和更新顺序：

\[
r^{low}_{i,t}
=
\lambda_e r^{env}_t
+
\lambda_D r^{team\_disc}_t
+
\lambda_d r^{ind\_disc}_{i,t}.
\]

R39 不改变这些既有项，也不增加任何新项。

## 5.7 Clocks, ages, resets, and recurrent state

- 每个 environment 有独立 `steps_to_check`。
- environment reset 后 skills invalid、ages zero、`steps_to_check=0`；第一次 assignment 调用原 full joint path，所有 agent 执行 SET。
- 每个 primitive step 后 active age 增加 1。
- check 时：
  - KEEP：skill 不变，age 不重置；
  - SET：skill 替换，age 在下一 primitive action 前置零。
- \(Z\) 每个 check 更新，但不改变 individual age。
- actor 和 centralized critic recurrent hidden state只在 environment done/reset 时清零。
- individual SET、KEEP 或 \(Z\) renewal 均不清零任何 agent hidden state；未编辑 agent 的 low execution 完全连续。
- 注册配置满足：

```text
episode_length = rollout_length = 500
k0 = 10
```

两者均可被 10 整除。正常 rollout boundary 必须恰好位于 closed check block 后。terminal short block 以 bootstrap 0 闭合。任何 nonterminal open high block 出现在 rollout update boundary 都是 M0-B implementation failure；不得跨 policy version 重用该 row。

## 5.8 Mechanism-matched initialization and optimizer exposure

Stage B 两臂严格加载同一个 Stage A checkpoint：

```text
fixed_full_refresh
native_partial_keep_set
```

两臂都实例化相同 `f_roster`，使用 initialization seed `49040`，并具有相同 parameter count 和 coordinator optimizer parameter groups。

- shared HMASD parameter 和 optimizer states 从 Stage A checkpoint 按名字精确恢复；
- 新 residual parameters 的 optimizer moments 初始化为零；
- fixed arm 也执行相同数量的 optimizer calls，但通过 `mode_scale=0` 使 residual output 和 gradient 精确为零；
- fixed arm collector **直接调用原** `SkillCoordinator.assign_and_value_batch` 和 `evaluate_training_batch`，所有 category 都是 SET；不得通过 partial method 模拟 full refresh；
- treatment 调用 native partial method；
- discoverer、critics、discriminators、normalizers、update order、checkpoint schema 和 environment完全共享。

## 5.9 Stage B exposure and evaluation

```text
source checkpoint       = exact PASS_R39A final checkpoint
train seed              = 39040
residual init seed      = 49040
num_envs                = 32 per arm
rollout_length          = 500
outer updates           = 20
total env steps         = 32 * 500 * 20 = 320,000 per arm
PPO epochs              = 15
num_mini_batch          = 4
```

两臂使用相同 environment reset stream；policy/action RNG 为独立但固定流。

Final evaluation：

```text
64 paired stochastic episodes per arm
reset seeds             = 139040 ... 139103
fixed policy RNG        = 239040
async policy RNG        = 339040
bootstrap draws         = 10,000
paired-bootstrap seed   = 40039040
resampling unit         = paired episode index
```

## 5.10 Stage B gates

### M0-B — exact compatibility

在任何 Stage B optimizer update 前，两臂均置于 `full_refresh_compat`，对 32 个 paired 500-step traces 使用相同 environment 和 policy RNG，要求：

- sampled \(Z\) 和所有 \(z_i\) exact equal；
- primitive actions、actor/critic hidden states、values、rewards、states、observations和 coverage traces：
  
\[
\max |\Delta|\le10^{-6};
\]

- stored/replayed team and agent log-probability errors：

\[
\le10^{-6};
\]

- shared checkpoint tensors exact equal；
- residual tensors exact equal且 output zero；
- no standalone R30/HA-CTSE module active；
- no graph PBRS、new reward、task-specific intrinsic 或 altered discriminator path；
- both arms exactly 320,000 steps and 20 outer updates after mode split。

M0-B miss：

```text
INVALID_R39B_COMPATIBILITY
```

唯一下一动作：只修 native full-refresh/partial replay 或 migration defect，按完全相同 Stage B 合同重跑。

### M1-B — fixed control remains a positive anchor

固定 arm final evaluation 必须再次满足：

\[
LCB_{95}(C_{\mathrm{mean}}^{fixed})\ge0.90,
\]

\[
LCB_{95}(C_{\mathrm{full}}^{fixed})\ge0.50,
\]

\[
UCB_{95}(F_{\mathrm{zero}}^{fixed})\le0.10.
\]

若失败：

```text
INVALID_R39B_FIXED_ANCHOR_LOST
```

这不是 treatment 科学失败。唯一下一动作：停止 treatment 解释并定位 Stage A continuation / checkpoint / optimizer reproduction defect；不得调 treatment。

### M2-B — async service noninferiority

定义 paired async-minus-fixed：

\[
\Delta C_{\mathrm{mean}}
=
C_{\mathrm{mean}}^{async}
-
C_{\mathrm{mean}}^{fixed},
\]

\[
\Delta C_{\mathrm{full}}
=
C_{\mathrm{full}}^{async}
-
C_{\mathrm{full}}^{fixed},
\]

\[
\Delta F_{\mathrm{zero}}
=
F_{\mathrm{zero}}^{async}
-
F_{\mathrm{zero}}^{fixed}.
\]

要求：

\[
LCB_{95}(\Delta C_{\mathrm{mean}})\ge-0.05,
\]

\[
LCB_{95}(\Delta C_{\mathrm{full}})\ge-0.05,
\]

\[
UCB_{95}(\Delta F_{\mathrm{zero}})\le+0.10.
\]

### M3-B — genuine individual lifetime decoupling

忽略 initial assignment，使用 treatment final evaluation 的所有真实 checks。

定义：

\[
u_{i,\tau}
=
\mathbf1[e_{i,\tau}=\operatorname{SET}].
\]

1. Full-sync SET rate：

\[
S_{\mathrm{full}}
=
\frac1M\sum_\tau
\mathbf1[\forall i,\ u_{i,\tau}=1].
\]

要求：

\[
UCB_{95}(S_{\mathrm{full}})\le0.50.
\]

2. Pairwise renewal correlation：

对每个 agent pair 计算 episode-clustered Pearson correlation of \(u_i,u_j\)。任一零方差 pair fail-closed 记为 1。定义 pair mean \(\bar\rho\)，要求：

\[
UCB_{95}(\bar\rho)<0.90.
\]

3. Lifetime breadth：

使用所有 completed individual lifetimes；right-censored terminal lifetimes不进入分子或分母。必须至少有 128 个 completed lifetimes，并要求：

\[
LCB_{95}\big(P(T_i>4k_0)\big)\ge0.05,
\]

\[
LCB_{95}\big(P(T_i\le4k_0)\big)\ge0.05.
\]

4. Switch-skill supply：

在 SET events 上：

\[
LCB_{95}
\left(
\frac{H(Z_{\mathrm{set}})}{\log K}
\right)
\ge0.80,
\]

且每个 skill 的 pooled SET share：

\[
\min_z P(Z_{\mathrm{set}}=z)\ge0.05.
\]

这些量只评估 lifetime 使用，不进入 reward 或 policy input。

## 5.11 Mutually exclusive Stage B outcome

PASS：

```text
PASS_R39B_NATIVE_TEMPORAL_DECOUPLING
```

条件：M0-B、M1-B、M2-B、M3-B 全部通过。

唯一下一动作：注册约 1M additional steps、paired seeds 的完整 native HMASD fixed/shared-`k` versus per-agent-lifetime验证。该下一实验仍不得加入新 intrinsic 或 task shaping。

Scientific abandonment：

```text
VALID_FAIL_R39B_NATIVE_KEEP_SET
```

条件：M0-B/M1-B 通过，但 M2-B 或 M3-B 任一失败。结果中记录：

```text
failure_axis = service | no_decoupling | both
```

唯一下一动作：永久退休这一 native categorical KEEP/SET temporal formulation。不得通过 keep bias、residual width、age normalization、coefficient、learning rate、budget、seed、threshold、Z lifetime 或 entropy 调整来救援，也不得回到 standalone R30 或已退休 R29–R38 路线。

Operational failure：

```text
OPERATIONAL_FAILURE_R39
```

只允许修复 crash、I/O、CUDA、process-spawn 或 artifact-write 的具体故障，并从相同 committed contract 重试同一未完成路径；不得改变科学参数。

---

# 6. Exact claim boundary

Stage A PASS 只支持：

> 当前接口下，原生 fixed-`k` HMASD 能在注册的 unshaped S7-S1 contract 上建立正向 service anchor。

Stage B PASS 只支持：

> 在同一 positive HMASD substrate 上，将每个 individual categorical incumbent event解释为 KEEP，并允许 task-blind roster/age residual学习 partial renewal，可以在 320K mechanism exposure 内保持 service noninferiority并产生真实非同步 lifetime。

Stage B PASS 仍不支持：

- full HMASD parity；
- final paper efficacy；
- S7-S3 improvement；
- asynchronous lifetime superiority at long-run scale；
- `q_D/q_d` 已满足新的跨环境 intrinsic-input contract；
- 新 intrinsic reward 已被发现。

---

# 7. Minimal repository boundary

Stage A 不新增 core algorithm。只允许：

```text
config_1.py
train_multiproc_config_1.py
scripts/run_r39a_fixed_hmasd_anchor.*
scripts/analyze_r39a_fixed_hmasd_anchor.py
```

其中对 `config_1.py` / trainer 的修改仅限 manifest、fail-closed reward variant 和正式 runner 参数，不改变算法。

Stage B 最小修改：

```text
hmasd/networks.py
    - native roster/age residual
    - native partial assign/evaluate methods
    - original full-refresh methods unchanged

hmasd/utils.py
    - stored incumbent roster/age/category fields
    - exact partial-sequence replay sampler

hmasd/agent.py
    - per-env active skills, ages, check clock
    - native partial collector path
    - original q_D/q_d and low update order unchanged
    - strict checkpoint/optimizer migration

config_1.py
    - default-off native partial flags and frozen manifest

train_multiproc_config_1.py
    - mode selection, metrics, fail-closed contract

scripts/run_r39b_native_temporal_gate.*
scripts/analyze_r39b_native_temporal_gate.py
```

明确禁止修改或调用：

```text
ha_ctse_process/standalone_agent.py
ha_ctse_process/r30_fixed_clock.py
ha_ctse_process/train.py
old historical checkpoint weights
R29-R38 retired reward/effect/benchmark modules
Scenario-7 observation/action/dynamics
```

---

# Final decision

\[
\boxed{
\text{MODIFY R39-S7}
}
\]

唯一顺序是：

\[
\boxed{
\text{current fixed-}k\text{ HMASD positive anchor}
\rightarrow
\text{native categorical KEEP/SET temporal gate}.
}
\]

没有 positive current-interface anchor，就没有可解释的 R39 treatment。存在 anchor 后，唯一允许测试的 intervention 是原 `SkillCoordinator` 内部、exact full-refresh bypass 可验证、与原 discoverer/discriminator/trainer 同源的 per-agent renewal semantics。
