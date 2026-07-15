According to a document from 2026-07-01，我的总体判断是：

> **当前 HA-CTSE 的正确主线已经从“解耦 K 的工程实现”转向“在 variable lifetime 下重建 HMASD 的 dense skill-discovery / differentiation / usefulness 动力闭环”。**
> 这一步是对的；但 P3/P4 现在最危险的地方，是把“forcing 让 skill 可解码”误认为“forcing 让 skill 有用”。你需要把 P3 明确写成 **low-level skill-effect forcing + shortcut residualization + task-generic usefulness selection + fixed-duration same-forcing control**，否则实验即使变好，也无法证明 variable lifetime 的算法贡献。

下面按你的 7 个问题逐条审查。

------

# 1. HMASD 机制拆解

## 1.1 HMASD 真正的闭环

HMASD 的机制不是单个 discriminator，而是四个东西连在一起：

```text
high-level skill coordinator
→ team skill Z + individual skills z_i
→ low-level discoverer π_l(a_i | o_i, z_i)
→ discriminator intrinsic rewards
→ low-level skills become diverse / distinguishable
→ high-level learns to compose them under sparse team reward
```

论文里 HMASD 的高层每隔固定 `k` 步分配 team skill `Z` 和 individual skills `z_1:n`，低层 discoverer 用 `π_l(a_i | o_i, z_i)` 执行动作，team/individual discriminators 给 discoverer 生成 intrinsic reward。这个结构在论文图 3 和算法描述里是核心：高层 skill coordinator 分配技能，低层 discoverer 执行，两个 discriminators 产生 `r_in`。

HMASD 的理论下界里有四类压力：

```text
team reward
+ diversity term
+ skill entropy term
+ action entropy term
```

其中 diversity term 让不同 skill 访问不同 state/observation 区域，skill entropy 和 action entropy 维持技能与动作探索。

最关键的是低层 reward。HMASD 的低层不是只吃环境 reward，而是：

```text
r_i_t =
    λ_e r_t
  + λ_D log q_D(Z | s_{t+1})
  + λ_d log q_d(z_i | o^i_{t+1}, Z)
```

论文明确解释：team reward 保证技能对团队表现有用，intrinsic rewards 用来优化 diversity term。

所以 HMASD 的“精神”不是：

```text
有一个 classifier
```

而是：

```text
低层 discoverer 每一步都收到 dense semantic pressure，
同时环境 reward 在正样本出现时把一部分技能拉向任务有用区域。
```

这正是 HA-CTSE 现在缺的东西。

## 1.2 它如何缓解 sparse reward 和 cooperative credit

HMASD 缓解 sparse reward 的方式有三层。

第一，discriminator intrinsic reward 把“等到 sparse team reward 出现”改成“每一步都能因为访问可区分状态/观测而收到训练信号”。这使 discoverer 不必完全依赖稀疏终局奖励。

第二，高层 team skill + autoregressive individual skill assignment 让 agents 的 skill 不是独立乱采样，而是被组合成互补结构。论文强调 individual skill 依赖 team skill 和之前 agents 的 skill，有助于 complementary skill selection。

第三，低层 reward 仍保留 `λ_e r_t`。论文附录特别强调，在复杂大空间任务中 `λ_e` 很大，是为了当 agents 遇到正 team reward 时，让 team reward 主导低层学习，推动 skills 更快变成任务有用技能。

这点对你很重要：**HMASD 不是纯 unsupervised diversity；它是 diversity + task return coupling。**

## 1.3 哪些依赖 fixed `k`，哪些可以迁移

依赖 fixed `k` 的部分：

```text
skills 同步刷新
high-level reward = k 步环境 reward sum
low-level rollout/chunk 与 k 对齐
discriminator 数据分布来自 fixed-k skill execution
skill interval k 是显式超参
```

论文附录也显示 HMASD 对 `k` 很敏感：skill interval 太短或太长都表现差，说明 fixed `k` 不只是实现细节，而是影响技能学习有效性的结构超参。

可以迁移到 variable lifetime 的精神：

```text
1. low-level actor 保持 skill bottleneck: π_l(a_i | o_i, z_i)
2. dense low-level intrinsic pressure
3. team-level coordination latent / global check clock
4. high-level composition of individual skills
5. skill/action entropy as exploration pressure
6. task return remains external usefulness signal
```

不能机械迁移的是：

```text
q_d(z_i | o_{t+1}, Z)
```

因为 variable lifetime 下，skill 的语义是一个 process，而不是单步 next observation。

------

# 2. HA-CTSE gap analysis

## 2.1 解耦 lifetime 后，HMASD 闭环在哪里断了

HA-CTSE 已经保留了很多结构外壳：

```text
c_tau / g_tau / z_i / a_i 分离
low actor 默认保持 π_l(a_i | o_i, z_i)
per-agent skill lifetime / duration
process segment buffer
strict HMASD/MAPPO-style recurrent low-level executor
```

你的 principles 也明确写了：HA-CTSE 不是简单移除 fixed synchronized skill interval，而是要重建 HMASD 的四个功能：低层执行能力、skill/role semantic pressure、entropy/exploration pressure、sparse-reward credit densification。

真正断掉的是这三处：

```text
A. discriminator reward 不再自然 dense
B. skill segment 被 duration / context / reward shortcut 污染
C. high-level variable duration 增大了 credit assignment 方差
```

HMASD 的 discriminator 每步给低层 reward；HA-CTSE 的 segment/posterior 类信号通常要等 segment 或 micro-window 才能训练，而且 duration 本身可能泄露 skill label。principles 已经要求 variable duration 必须用 sequence/mask，并跟踪 duration-only shortcut baseline。

## 2.2 当前 P3 forcing 是否对应 HMASD 精神

**P3 forcing 是目前最接近 HMASD 精神的方向。**

原因是当前 principles 已经把 P3 定义成 variable-lifetime 版本的 HMASD closed intrinsic loop：

```text
skill sampled
→ low-level discoverer executes sustained process
→ intrinsic pressure makes skills distinguishable
→ credit/usefulness pulls part of them toward task value
→ high level composes processes across agents and lifetimes
```

并且明确说，HMASD 的旧 `q(z|s)` 形式有价值不是因为 classifier 神奇，而是因为它把 dense low-level intrinsic reward 直接喂给 discoverer。

这点非常正确。**P3 最大的进步，是从 reward-off passive probe 转向 controlled forcing loop。** principles 也已经写明：reward-off effect gain 只是诊断，不是永久 gate；如果没有 reward path 鼓励 `z_i` 诱导 stable process，`p_full(y|x,z)` 失败并不能说明 `z_i` 没有 actuator capacity。

但 P3 还差两个关键闭环：

```text
1. forcing 是否真的进入 low-level discoverer 并改变行为？
2. 改变后的行为是否被 high-level 选择和组合，而不只是 decodable？
```

所以 P3 目前是“对的方向”，不是“已经完整”。

## 2.3 最可能失败在哪里

我按风险排序：

### 第一风险：duration shortcut

离散 duration 天然很容易成为 skill identity shortcut。principles 已经明确说 discrete lifetime 有训练优势，但也有 duration shortcut 风险，必须跟踪 `duration_only_accuracy`、`skill_usage_by_duration`、`return_by_duration` 等。

如果：

```text
q_disc(z | effect_window) ≈ q_duration(z | duration)
```

那么 P3 只是学到：

```text
skill label = duration schedule
```

不是 skill effect。

### 第二风险：forcing 只提高 decodability，不提高 usefulness

HMASD 自己也有这个问题。论文说在大 state-observation space 中，HMASD 可以发现 diverse skills，但只有一部分对 team reward 有用；SMAC 上 50 个 individual skills 中只有 12 个有用，即约 24%。

所以 HA-CTSE 如果只让 skills 更可解码，可能会复现 HMASD 的缺点，甚至更严重：

```text
skills become distinguishable
but not selected for task-useful coordination
```

### 第三风险：high-level skill selection 仍然 uniform

principles 已经指出，高 skill entropy 不是 skill discovery 成功的证据，它可能只说明 skills 可互换；成功的 P3 应该先产生 behavioral differentiation，再允许 context-dependent specialization。

所以如果：

```text
skill_entropy ≈ max
skill_action_KL ↑
disc_acc ↑
coverage / return / variance 不动
```

这不是成功，而是“低层被迫分化，但高层没有使用这些分化”。

### 第四风险：credit assignment 不足

P1/P2 经验已经说明，仅改变 duration、env 数、low-level access to `g` 都没有动 recovery；P1 可改善部分 service/backhaul，但没有过 recovery hard gate。

不过你现在明确要求不要把通信指标写进 intrinsic reward，这意味着 P3 的 usefulness 必须来自 task-generic signal，而不是 topology metric。这会更难，但更符合 general MARL claim。

### 第五风险：低层能力不足

这个风险已经比之前小，因为 implementation plan 记录了 strict HMASD/MAPPO low-level replica：actor 是 `MLPBase(o_i) -> skill FiLM(z_i) -> RNNLayer -> ACTLayer`，critic 是 `MLPBase(global_state) -> team-code FiLM(g) -> RNNLayer -> value`，并使用 per-env GAE(lambda)、recurrent sequence PPO、ValueNorm、value clipping 等。

所以接下来不应该优先怀疑 low-level capacity，而应该优先验证：

```text
low-level 是否被 P3 forcing 真正驱动出 skill-effect modes
```

------

# 3. P3/P4 intrinsic reward 设计

我建议把 P3/P4 正式命名成：

```text
VLSF: Variable-Lifetime Skill Forcing
```

或者：

```text
P3: Residual Skill-Effect Forcing
P4: Task-Generic Usefulness Selection
```

核心设计如下。

## 3.1 不使用通信指标的 general intrinsic reward

默认 P3 intrinsic reward 不应使用：

```text
coverage
backhaul
recovery
QoS
throughput
relay margin
connected components
```

这些只能作为 diagnostics / explicit ablation。

默认 effect window 应该使用 general behavior/effect fields：

```text
action statistics:
  mean action, action delta, action variance, action direction

local observation dynamics:
  normalized Δo_i
  end o_i summary
  within-window occupancy summary

generic physical state if exposed:
  Δposition in agent-centric frame
  Δvelocity
  Δenergy / charging progress
  local collision / safety / boundary progress

policy-internal controllability:
  low-level hidden-state change
  predicted next-local-observation embedding
  inverse-dynamics / forward-dynamics embedding
```

如果你担心 observation 太 task-specific，可以先训练一个 generic effect encoder：

```text
e_i(t,h) = f_effect(o_t, a_{t:t+h}, Δo_{t:t+h}, o_{t+h})
```

然后 discriminator 不直接看 raw communication fields，而看 `e_i`。

## 3.2 residual discriminator：应该使用，但要改成 forcing，不是 diagnostic

我建议保留 `force_disc_only`，并把它作为 P3 第一主线。

形式：

```text
R_disc_resid_i =
    log q_full(z_i | e_i, x_i^ctrl)
  - max(
        log q_context(z_i | x_i),
        log q_duration(z_i | d_i),
        log q_length(z_i | length_i),
        log q_reward(z_i | reward_sum_i),
        log q_agent_phase(z_i | agent_id, phase),
        log p_prior(z_i | g_tau)
    )
```

这里 `e_i` 是 effect window embedding，不是完整 segment label。

几个硬规则：

```text
1. label 必须是 active executed skill z_i，不是 candidate skill。
2. reward 用 pre-update discriminator logits 计算，再训练 heads。
3. shortcut heads 必须同时训练，不能只作为 eval。
4. reward 必须 low_only、micro-window distributed、warmup、center/clip。
5. 若 shortcut max 长期 >= full - margin，则 reward=0，不能继续加 coef。
```

这正好对应 principles 中 P3 的 Round 8 设计：`R_disc_residual` 是 load-bearing term，live reward 不能被 duration/reward shortcut predictors 解释，而且 forcing terms 必须 low-level、micro-window、warmup、clipped/centered，shortcut heads dominate 时关闭。

## 3.3 conditional effect predictor：应该使用，但只能做辅助

`R_effect_residual` 不应该替代 discriminator。它的作用是防止 discriminator 学到“可解码但无 effect”的表面模式。

推荐形式：

```text
R_effect_resid_i =
    log p_full(y_i | x_i, z_i)
  - max(
        log p_base(y_i | x_i),
        log p_duration(y_i | x_i, d_i),
        log p_reward(y_i | x_i, reward_sum_i),
        log p_context(y_i | context, agent_id, phase)
    )
```

如果用 Gaussian MSE，可以写成：

```text
R_effect_resid_i =
    -MSE_full(y_i)
    - max(-MSE_base, -MSE_duration, -MSE_reward, -MSE_context)
```

等价于：

```text
min_baseline_MSE - MSE_full
```

Round 8 已经指出，当前 live reward path 若仍用 raw `logp_full - logp_base` 不够干净；必须改成对 context/duration/reward baselines 的 residual。

我建议默认第一阶段：

```text
force_disc_only: w_disc=1, w_effect=0
force_disc_effect_resid: w_disc=1, w_effect=0.25
effect_only_resid: w_disc=0, w_effect=1  # diagnostic ablation only
```

不要一开始让 effect residual 单独承重。

## 3.4 是否需要 usefulness coupling

需要，但不应该第一步就开。

原因是 HMASD 已经证明：diverse skill discovery 不保证大空间中所有 skill 有用。

但 usefulness coupling 不能用通信指标，也不能把 env reward 伪装成 intrinsic。你的 principles 已经明确：P3/P4 不要用 raw communication indicators 作为 forcing reward 或 usefulness multiplier；如果需要 usefulness coupling，应优先使用 task-generic quantities，比如 policy advantage、TD/value improvement 或 non-domain-specific controllability/progress estimates。

我建议 P4 用两种版本。

### P4a：advantage-gated forcing

```text
U_i = stopgrad(clip_pos(norm(A_low_i or A_segment_i)))
R_P4_i =
    λ_force * center_clip(R_disc_resid_i)
  + λ_use   * U_i * clip_pos(R_disc_resid_i)
```

这不是把 reward 直接塞进 intrinsic，而是让 task-generic advantage 选择哪些 differentiable skill effects 更值得保留。注意：

```text
U_i stopgrad
U_i normalize by batch / running stats
U_i use quantile gate, not raw magnitude
```

例如：

```text
U_i = 1[A_segment_i > percentile_70]
```

这比直接乘 raw reward 更安全。

### P4b：value-improvement / TD gating

```text
U_i = stopgrad(clip_pos(V_after - V_before))
```

或：

```text
U_i = stopgrad(clip_pos(-TD_error_after_policy_update?))
```

但要注意不要用 post-update value 破坏 on-policy 语义。更稳的是 rollout 内 pre-update critic 的 segment advantage。

## 3.5 duration entropy 如何退火

duration entropy 不能永久高，也不能早期坍缩。

我建议：

```text
L_duration_entropy =
    - β_T(t) * H(π_T(. | x))
```

或等价地作为 high-level entropy bonus，而不是低层 reward。

schedule：

```text
0 ~ 20% training:
    β_T = β0，防止早期 fixed-duration collapse

20% ~ 60%:
    β_T 线性或 cosine 下降

60% 以后:
    β_T = β_floor，仅防止数值塌缩，不强迫随机 duration
```

再加一个 adaptive stop：

```text
if duration_usage_max_frac > 0.85 before warmup_end:
    temporarily raise β_T
if duration_entropy stays near max and return/effect specialization not improving:
    lower β_T faster
```

principles 也已经写得很清楚：duration entropy 是探索 aid，不是永久目标；高熵永远不降可能表示 indecision，太早坍缩则说明 variable lifetime 没被探索。

------

# 4. variable lifetime 的理论定位

## 4.1 中心贡献不是“decoupled lifetime alone”

我建议论文定位不要写成：

```text
Decoupled K alone solves sparse MARL.
```

这太脆弱，也不符合你当前结果。

更好的定位是：

```text
Variable lifetime is the temporal abstraction substrate.
Residual skill-effect forcing is the discovery/differentiation motor.
Task-generic usefulness selection is the actually-work filter.
Together they form the variable-lifetime analogue of HMASD.
```

也就是中心贡献是：

```text
decoupled lifetime + HMASD-like forcing/discovery loop
```

principles 里已经有类似修正：decoupled-K experiment 只是 inclusion/optimization sanity gate，真正目标是在 asynchronous / variable lifetimes 下重建 HMASD-like internal drive，让 skills discovered, differentiated, useful。

## 4.2 fixed/shared lifetime control 怎样才公平

必须有这些 controls：

```text
A. HMASD original
B. HA-CTSE reward-pure variable duration
C. HA-CTSE reward-pure fixed duration
D. HA-CTSE fixed duration + same forcing
E. HA-CTSE variable duration + same forcing
F. HA-CTSE shared variable duration + same forcing
G. HA-CTSE oracle-best fixed duration + same forcing
```

关键不是只跑 `candidates=(7,)`，而是：

```text
fixed duration must use the same low-level network,
same high-level capacity except duration head disabled/frozen,
same z cardinality,
same g/c path,
same P3 forcing reward,
same coefficients,
same rollout length,
same total env steps,
same eval protocol.
```

`fixed-duration + same-forcing` 是 Round 8 必须项。principles 已经说：positive P3-4 forcing 结果只能证明 forcing 有帮助；要 claim HA-CTSE decoupling，必须至少跑 fixed-duration + same-forcing control，例如 `candidates=(7,) + disc_only`。

## 4.3 如果某些任务适合固定周期怎么办

这不是坏事。variable lifetime 是更大的 policy class，固定周期是特例。principles 也明确说 fixed-duration control outperform variable-duration 不应被解释为 variable lifetime 无用，而通常意味着当前 optimization / intrinsic reward / credit mechanism 没让 variable controller 找到有用特例。

论文里可以这样写：

```text
Our method does not assume asynchronous renewal is always beneficial.
It provides an inductive bias and a policy class for heterogeneous temporal coordination.
On tasks where a shared fixed period is optimal, the learned lifetime policy may converge toward it.
The mechanism claim is supported only when tasks exhibit heterogeneous role durations
and the learned policy uses nontrivial non-synchronized lifetimes while improving return/stability.
```

但在你的 S7-S1 gate 里，**如果它完全坍缩到 fixed/shared lifetime，就不能算 HA-CTSE 机制成功**。只能说 forcing 机制成功，decoupled lifetime 未证明。

------

# 5. 实验和 ablation 计划

下面是我建议的优先级矩阵。

## Stage 0：对齐基线与评估

| Arm                                          | 目的                             | 预期                      | falsification                                                | 指标                                                        | 失败后                               |
| -------------------------------------------- | -------------------------------- | ------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------- | ------------------------------------ |
| H0: HMASD original                           | 给 S7-S1 parity 上界             | 约 1e6 steps 接近稳定覆盖 | HMASD 自身不达标则环境/设置不一致                            | coverage==1 step fraction, failed episodes, reward variance | 先修 benchmark parity                |
| B0: HA-CTSE reward-pure variable             | 检查 variable lifetime substrate | 不一定赢，但不能全崩      | skill/duration 全坍缩或 eval 全零                            | reward, coverage gate, duration entropy, full_sync_rate     | 先修 high/low PPO/value scale        |
| B1: HA-CTSE reward-pure fixed d=7            | 固定周期强 control               | 可能更稳                  | 若明显优于 variable，说明 variable optimization 不稳         | 同上 + return_by_duration                                   | variable 不能 claim                  |
| B2: HA-CTSE reward-pure oracle fixed d sweep | 避免只拿 d=7 strawman            | 找到 best fixed           | 若 best fixed 远强于 variable，forcing 前先看 duration policy | fixed d ∈ {1,2,3,7,13}                                      | 用 best fixed 做后续 forcing control |

S7-S1 短期 gate 不只看 reward mean，而是至少一半 eval primitive steps 达到 `coverage == 1.0`，同时看 variance 和 failed/zero-service episodes；principles 明确说这是 evaluation milestone，不允许把 communication metric 变成 intrinsic reward target。

## Stage 1：P3 forcing 的最小验证

| Arm                                        | 目的                                                       | 预期结果                                                     | falsification                                                | 指标                                                      | 失败后                             |
| ------------------------------------------ | ---------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | --------------------------------------------------------- | ---------------------------------- |
| F1: variable + force_disc_only             | 测 residual discriminator 是否能创造 skill differentiation | `R_disc_resid ↑`, skill-action/effect divergence ↑, task 不退化 | shortcut max ≥ full，或 decodability ↑ 但 effect/action intervention 不变 | disc residual, shortcut gap, skill-action KL, skill usage | 修 effect_window 或换 hazard-SMDP  |
| F2: fixed best-d + force_disc_only         | same-forcing control                                       | 若 variable 真有用，F1 > F2 或 lifetime 机制更合理           | F2 ≥ F1 且 F1 lifetime 坍缩                                  | same + fixed vs variable delta                            | 不 claim decoupled-K               |
| F3: variable + force_disc_effect_resid     | 测 effect residual 是否让 forcing 更 process-grounded      | effect gain ↑，task/variance 不退                            | raw gain ↑ but residual gap ≤0                               | effect residual over max baselines                        | 修 residual path                   |
| F4: fixed best-d + force_disc_effect_resid | fixed same-forcing control                                 | 对照 F3                                                      | fixed 同样提升则 forcing 有效但 variable 未证                | same                                                      | 继续 variable-specific diagnostics |

这里的核心是：

```text
F1/F2 判断 forcing 是否有效；
F1 vs F2 判断 variable lifetime 是否贡献；
F3/F4 判断 effect residual 是否增强 process grounding。
```

## Stage 2：duration entropy annealing

| Arm                                                        | 目的                                    | 预期                                          | falsification                             | 指标                                                         | 失败后                           |
| ---------------------------------------------------------- | --------------------------------------- | --------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------ | -------------------------------- |
| DENT: variable + force_disc_only + duration entropy anneal | 防止早期 fixed collapse                 | early duration entropy ↑，late specialization | entropy 永远高但 task 不动；或仍早坍缩    | duration entropy, max frac, duration-agent MI, full_sync_rate | 调 β schedule 或换 stopping-time |
| DENT-fixed-control                                         | 确认提升不是普通 entropy regularization | fixed 不应获得同样 lifetime 机制收益          | fixed 同样提升，说明不是 decoupled effect | same                                                         | 降低 claim                       |

## Stage 3：usefulness-coupled forcing

| Arm                                                          | 目的                                        | 预期                                  | falsification                         | 指标                                                   | 失败后                                    |
| ------------------------------------------------------------ | ------------------------------------------- | ------------------------------------- | ------------------------------------- | ------------------------------------------------------ | ----------------------------------------- |
| U1: variable + force_disc_only + advantage-gated positive forcing | 让 differentiated skills 向任务有用区域偏移 | skill effect 保持，task ↑，variance ↓ | task 不升或 discriminator collapse    | advantage-skill correlation, return_by_skill, variance | 改 U 定义或先不开 usefulness              |
| U2: fixed + same U1                                          | 判断 variable 是否仍有额外收益              | variable 应更好或 lifetime 非平凡     | fixed ≥ variable 且 variable collapse | same                                                   | variable mechanism 未证                   |
| U3: variable + force_disc_effect + usefulness                | 完整 P3/P4                                  | 接近 HMASD S7-S1 gate                 | coverage gate 不过，shortcut dominate | all metrics                                            | pivot to hazard-SMDP / option termination |

usefulness coupling 的 `U_i` 不要用 coverage/backhaul/recovery。用：

```text
U_i = stopgrad(positive normalized segment advantage)
or
U_i = stopgrad(positive TD/value improvement)
```

这符合 principles 对 P3/P4 的 reward boundary。

## Stage 4：hazard-SMDP trigger

如果出现：

```text
shortcut heads 长期追平 / 超过 full discriminator
duration_only_accuracy 高
skill_duration_mi 高
force_disc_only 和 force_disc_effect 都无法摆脱 duration shortcut
```

不要再加第 5 个、第 6 个 debiasing head。Round 8 已经写了：如果 shortcut heads across disc_only 和 revised residual path 仍匹配或超过 discriminator，应视为 discrete duration labels 结构性污染 skill semantics，转向 hazard-SMDP / stopping-time。

------

# 6. 成功 / 失败判据

## 6.1 S7-S1 任务 gate

短期最低 gate：

```text
eval 中至少 50% primitive steps coverage == 1.0
```

同时必须看：

```text
failed / zero-service episode fraction ↓
reward_std / reward_mean ↓
coverage long-window stability ↑
QoS / throughput 不退化
checkpoint sweep 中不是偶然 peak
```

但这些只作为 evaluation diagnostics，不进入 P3 intrinsic reward。

## 6.2 General MARL algorithm diagnostics

### Skill discovery / differentiation

```text
skill_usage_entropy
skill_usage_max_frac
skill_return_dispersion
skill_effect_embedding_pairwise_distance
skill_action_intervention_KL / TV
skill_effect_intervention_distance
force_disc_full_acc
force_disc_shortcut_acc
disc_residual_mean
disc_residual_positive_frac
```

关键判断：

```text
high skill entropy alone ≠ success
```

如果 entropy 高但 intervention KL 低，说明 skills 可互换。

### Shortcut gap

```text
disc_full_minus_context
disc_full_minus_duration
disc_full_minus_reward
disc_full_minus_agent_phase
effect_full_minus_best_baseline
duration_only_accuracy
reward_sum_only_accuracy
length_only_accuracy
skill_duration_mi
```

成功要求：

```text
full > max shortcut by margin
```

不是 full acc 高就行。

### Variable lifetime usage

```text
duration_usage_entropy
duration_usage_max_frac
duration_agent_mi
duration_skill_mi
lifetime_heterogeneity
renewal_full_sync_rate
renewal_pairwise_corr_mean
duration_return_range
return_by_duration
skill_effect_by_duration
early_expiry_or_forced_renewal_rate
```

成功要求：

```text
非坍缩、非全同步、duration 与 context/role/effect 有解释关系
```

principles 对 decoupled-K 也明确要求：D 必须赢过 fixed/shared control，且不能同步或 homogeneous lifetime collapse。

### High-level 使用 skill 的程度

```text
high_level_skill_entropy
conditional_skill_entropy H(z | context)
pi_z advantage correlation
team_code_skill_mi
g_intervention_KL / TV on pi_z
duration_policy_entropy
skill_selection_change_after_forcing
```

如果：

```text
low-level skills 分化了
but pi_z 仍 uniform / high-level 不利用
```

那 P3 只完成了 discoverer，不完成 high-level composition。

### Learning health

```text
low_approx_kl
low_clip_frac
low_value_error_rmse
low_advantage_std
process_reward_low_mean / env_reward_scale
high_policy_loss
high_value_loss
high_bootstrap_value_mean vs high_env_return_mean
grad_norms
```

如果 process reward scale 远大于 env 或 value loss 爆炸，先修训练稳定，不要解释为算法失败。

------

# 7. 代码实现建议：按优先级

## Priority 1：修正 `force_disc_effect` 的 live reward

必须把当前 raw gain：

```text
logp_full - logp_base
```

改成：

```text
logp_full - max(logp_context,
                logp_duration,
                logp_reward,
                logp_agent_phase,
                logp_base)
```

连续 target 用 NLL/MSE 等价形式。

同时把日志拆成：

```text
effect_gain_raw
effect_gain_resid_context
effect_gain_resid_duration
effect_gain_resid_reward
effect_gain_resid_best
effect_best_shortcut_name
effect_reward_applied_after_gate
```

如果 `best_shortcut_name == duration` 长期占主导，要触发 duration shortcut hard-stop。

## Priority 2：增加 fixed-duration + same-forcing control

至少实现 CLI / preset：

```text
--skill_lifetime_candidates 7
--p3_force_mode disc_only
--p3_force_coef same_as_variable
```

以及：

```text
fixed_best_d_force_disc_only
fixed_best_d_force_disc_effect_resid
variable_force_disc_only
variable_force_disc_effect_resid
```

没有这个 control，任何 forcing 成功都只能说明：

```text
forcing helped
```

不能说明：

```text
variable lifetime helped
```

## Priority 3：把 P3 reward feature set 与 diagnostics feature set 硬隔离

增加配置：

```text
p3_effect_feature_set = generic | generic_plus_energy | scenario_probe | scenario_reward_ablation
```

默认：

```text
generic / generic_plus_energy
```

禁止默认 P3 reward 读取：

```text
coverage
backhaul
qos
throughput
recovery
relay
connected_components
```

这些只能在：

```text
scenario_probe diagnostics
explicit ablation
```

中出现。principles 已经要求 P3/P4 不要用 raw communication indicators 作为 forcing reward 或 usefulness multiplier。

## Priority 4：实现 micro-window forcing buffer

不要只用 completed segment。P3 应在 active skill 内部采样：

```text
h ∈ {5, 10, 20}
```

每个 sample：

```text
(env_id, agent_id, t0, h, active_z, duration_bucket, age, context, effect_window)
```

注意：

```text
label = active executed z
mask done / rollout boundary
reward 用 pre-update heads 计算
heads 用 rollout 后数据训练
不跨 PPO update 复用
```

P3 principles 已经明确：P3 用 micro-windows 恢复 HMASD-like dense discoverer pressure，一个长 lifetime 应产生多个 micro-window samples，而不是只在 completed lifetime 上训练一次。

## Priority 5：增加 skill-action / skill-effect intervention diagnostics

实现两个 cheap diagnostic：

### Skill-action intervention KL

同一个 batch 的 `o_i`，枚举不同 `z`：

```text
π_l(a | o_i, z=0), ..., π_l(a | o_i, z=n_z-1)
```

记录：

```text
skill_action_pairwise_KL
skill_action_pairwise_TV
skill_action_entropy_by_z
```

如果 P3 forcing 后 classifier acc ↑ 但 action KL 不变，说明 skill 没控制 actor。

### Skill-effect predicted intervention

用 effect predictor：

```text
p_full(y | x, z)
```

枚举 z，看 predicted effect 是否改变：

```text
skill_effect_pred_KL / MSE distance
```

这比只看 `q_disc` acc 更接近 “z controls effect”。

## Priority 6：duration entropy annealing

实现：

```text
duration_entropy_coef_schedule:
  constant_warmup
  linear_decay
  floor
```

并加 collapse reactive adjustment：

```text
if duration_usage_max_frac > threshold before warmup:
    increase beta_T temporarily
```

日志：

```text
duration_entropy_coef
duration_entropy_loss
duration_usage_entropy
duration_usage_max_frac
duration_agent_mi
duration_skill_mi
duration_return_range
```

## Priority 7：usefulness-coupled forcing，作为第二阶段

先实现但默认关闭：

```text
p4_usefulness_coupling = none | advantage_gate | td_gate
```

建议第一版：

```text
U_i = stopgrad(1[A_segment_i > percentile_70])
R_use_i = U_i * clip_pos(R_disc_resid_i)
```

日志：

```text
usefulness_gate_frac
force_reward_when_U_pos
force_reward_when_U_neg
skill_return_dispersion
advantage_by_skill
skill_selected_after_positive_advantage
```

## Priority 8：hazard-SMDP trigger

不要急着实现 hazard-SMDP，但要实现 trigger：

```text
if shortcut_dominance_updates > N:
    write hazard_smdp_recommended = 1
```

条件：

```text
disc_full_minus_best_shortcut < margin for N updates
best_shortcut == duration or length often
duration_only_accuracy high
skill_duration_mi high
```

触发后停止增加 debiasing head，转向 stopping-time policy：

```text
hazard λ_i(t | o_i, z_i, age_i, context)
```

而不是 discrete duration label。

------

# 当前 HA-CTSE：哪些继承了 HMASD，哪些只是表面模仿

## 真正继承了 HMASD 精神的部分

```text
1. low actor skill bottleneck: π_l(a_i | o_i, z_i)
2. strict recurrent MAPPO-style discoverer / centralized critic
3. team coordination latent g_tau 与 individual skill z_i 分离
4. high-level SMDP skill/duration policy
5. P3 low-level forcing 试图恢复 dense discriminator pressure
6. shortcut residualization 试图避免 fake skill semantics
```

这些是对的。

## 表面模仿或危险部分

```text
1. 只看 q(z | segment) / posterior acc
2. skill_entropy 高就认为 skill discovery 成功
3. g_entropy 高就认为 team code 有用
4. topology-role classifier reward 复活
5. P2/P1 通信 topology shaping 被当成主 intrinsic
6. variable duration 最终坍缩到固定周期还声称 decoupled-K 成功
```

其中 P2-lite 可以作为 support / diagnostic，但不能成为 P3/P4 的通用 intrinsic reward。principles 已经将 P2c role-classifier reward 从 active gate 退休，并推迟 P2b `g` 训练，直到 recovery credit 有明显 movement。

## variable lifetime 下必须重新发明的机制

```text
1. discriminator target:
   from q(z | o_next) to residual q(z | effect_window) / p(y | x,z)

2. entropy:
   from skill/action entropy to skill + duration + renewal + action entropy

3. high-level reward:
   from fixed-k sum to variable-length SMDP return

4. usefulness:
   from λ_e r_t inside fixed-k low-level reward
   to task-generic advantage/value-gated effect forcing

5. team code:
   from team skill Z directly conditioning discriminator/critic
   to g_tau selecting skill-effect mixtures after skills have semantics
```

------

# 最值得实现的下一步

我会把接下来 2 周的优先级压成 5 件事：

```text
1. 修正 force_disc_effect：
   live reward = full - max(context, duration, reward, phase/agent, base)
   不是 raw full - base。

2. 跑 force_disc_only 作为第一主线：
   variable-duration + force_disc_only
   fixed-best-duration + same force_disc_only

3. 加 skill-action intervention KL 和 effect intervention diagnostics：
   证明 z_i 真的控制 low-level behavior/effect，而不是只让 classifier 高兴。

4. 加 duration entropy annealing：
   early 防坍缩，late 允许 specialization；
   同时记录 duration_agent_mi / full_sync_rate / lifetime_heterogeneity。

5. 如果 disc_only 只提高 decodability、task 不动，
   再开 advantage-gated usefulness coupling；
   不要用 coverage/backhaul/recovery 作为 multiplier。
```

最短可执行实验包：

```text
E0: HMASD original S7-S1 matched eval
E1: HA-CTSE variable reward-pure
E2: HA-CTSE fixed-best reward-pure
E3: variable + force_disc_only
E4: fixed-best + force_disc_only
E5: variable + force_disc_effect_residual_corrected
E6: fixed-best + force_disc_effect_residual_corrected
E7: variable + force_disc_only + duration entropy annealing
E8: variable + force_disc_only + advantage-gated usefulness
```

如果 E3/E4 都提升，但 E3 不优于 E4：

```text
P3 forcing 有效；
decoupled lifetime 未证明。
```

如果 E3 优于 E4，且：

```text
lifetime_heterogeneity ↑
full_sync_rate 不高
duration_usage_entropy 不坍缩
coverage gate 接近或通过
shortcut gaps positive
high-level skill selection 不再 inert uniform
```

那才是 HA-CTSE 的核心证据。

最后一句最重要：

> **不要把 P3 做成“更复杂的 posterior”。P3 必须是一个真的 low-level forcing reward：让 `z_i` 在相同 context 下制造可区分、可持续、可被 high-level 选择的行为效果。然后用 task-generic advantage/value 信号筛出有用 effects。这个组合，才是 variable-lifetime 版本的 HMASD 精神。**
