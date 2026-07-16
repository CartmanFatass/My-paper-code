# 裁决

[
\boxed{\texttt{ACCEPT_VARIABLE_TEAM_TOY_REQUIREMENTS}}
]

唯一下一条路线为：

[
\boxed{
\textbf{R51-AMDT-G0：
Anonymous Maintenance–Dispatch Task}
}
]

其唯一因果边是：

[
\boxed{
\begin{aligned}
&\text{真正随 }N\text{ 扩展的共享任务与资源约束}\
&+\text{一个跨 episode 共享的匿名策略}\
&+\text{稀疏原生完成奖励}\
&\rightarrow
\text{在多个稳定 team sizes 上形成可访问的合作策略}.
\end{aligned}
}
]

这是一个**不同于 Alice-and-Bob 的匿名维护—派遣 Markov game**，不是现有 Alice-and-Bob 的多副本扩展，也不是 R50 的环境化重命名。

---

# 一、审阅结论与可复用因果结论

R49 已经证明 N-independent Deep-Sets 接口能够保持 permutation、padding、incremental roster、sampling/replay 和 membership 语义，但其环境步、奖励读取和优化步均为零，因此它只是一项接口结果。

R50 则是一步 roster bandit：目标标签由成员特征相对 active-set mean 的象限定义，没有环境、低层动作或时间动力学。正式结果中固定-(N) specialists 唯独未通过 (N=16) exact-roster access 门槛，因此 shared arm 的全部数值 M2 结果按照注册合同被隔离。

与此同时，R48 已经绑定停止 fixed-(N) skill/lifetime 算法探索；open-roster 只能作为独立架构与任务问题继续，不能继承“技能语义已解决”或“异步 lifetime 有效”的前提。

因此，当前可复用结论是：

[
\boxed{
\begin{aligned}
&\text{variable-}N\text{ 接口正确}\
&+\text{synthetic set rule 可被某些模型拟合}\
&\not\Rightarrow
\text{共享策略能够学习真正随 }N\text{ 改变的合作任务}.
\end{aligned}
}
]

R39 还说明，表达能力、方向正确的回报和精确 replay 也不能替代 ordinary-policy task access；R35–R40 则反复表明，不能在无访问锚点时解释算法差异。

所以 R51 必须在**同一次正式运行中**同时包含：

1. 固定-(N) ordinary-policy specialists 的环境访问锚点；
2. 一个跨 (N) 共享策略；
3. 只在 specialists 建立访问以后才解释 shared arm。

---

# 二、唯一环境：Anonymous Maintenance–Dispatch Task

## 2.1 任务类型

R51-AMDT 是一个**匿名多智能体资源调度任务**，不是 Alice-and-Bob generalization。

现有连续 Alice-and-Bob 与 asymmetric-cycle 环境都把 agent 数固定为 2，并使用固定二维 agent arrays 和固定观察维度；它们不能通过增加 padding 变成真正的 variable-team task。

选择直接调度图而不是新网格的原因是：R35–R40 已经暴露了导航、稀疏到达和任务访问混淆。AMDT 删除长距离导航，却保留三个核心困难：

[
\text{资源不足}
+
\text{全队分配}
+
\text{不同任务时间尺度}.
]

它不是给 HA-CTSE 定制的 reward：环境从不奖励 KEEP、长 lifetime、角色分化或异步性。

---

# 三、完整 Markov game

## 3.1 Team size 与任务规模

每个 episode 开始时：

[
N\sim\operatorname{Uniform}{2,3,4,5,6},
]

本 episode 内 membership 固定。

定义：

[
P_N=\left\lfloor\frac N2\right\rfloor
]

个 persistent stations，以及：

[
D_N=N-P_N
]

个 concurrent dispatch jobs。

| (N) | persistent stations (P_N) | concurrent jobs (D_N) |
| --: | ------------------------: | --------------------: |
|   2 |                         1 |                     1 |
|   3 |                         1 |                     2 |
|   4 |                         2 |                     2 |
|   5 |                         2 |                     3 |
|   6 |                         3 |                     3 |

每个 wave 的同时职责数为：

[
P_N+D_N=N.
]

因此增加 agent 的同时也增加任务量；不存在“任务仍是两人任务，其余 agent 闲置”的情况。

---

## 3.2 Task graph 与 entities

环境是一个 one-hop assignment graph，而非空间网格。每个 agent 的位置是其当前 assignment：

[
\ell_{i,t}\in
{\texttt{DEPOT}}
\cup\mathcal P_N
\cup\mathcal J_{N,w}.
]

其中：

* `DEPOT`：无服务产出的空闲节点；
* (\mathcal P_N)：整个 episode 都存在的 persistent stations；
* (\mathcal J_{N,w})：当前 wave 的 (D_N) 个短期 jobs。

最多同时存在：

[
E_N=1+P_N+D_N=N+1
]

个 action entities。

不存在 agent-specific station、job 或角色。

---

## 3.3 时间结构

固定：

```text
episode horizon T = 32 primitive steps
job waves          = 3
wave starts        = t ∈ {4, 12, 20}
job lifetime       = 6 primitive steps
station health max = 4
```

每个 wave 生成 (D_N) 个新 jobs。旧 wave 的 job keys 在下一 wave 到来时失效；位于旧 job 上的 agent 被送回 depot。

Station 从 (t=0) 到 (t=31) 一直存在。Job 只在一个六步窗口内需要处理。

---

## 3.4 Agent action 与 switching cost

每个 agent 选择一个当前有效 entity：

[
a_{i,t}\in
{\texttt{DEPOT}}
\cup\mathcal P_N
\cup\mathcal J_{N,w}.
]

服务只在 agent 选择继续停留时发生：

[
m_{i,e,t}
=========

\mathbb 1[
\ell_{i,t}=e
\land
a_{i,t}=e
].
]

若：

[
a_{i,t}\ne\ell_{i,t},
]

本 step 只发生转移，不提供服务；step 结束后：

[
\ell_{i,t+1}=a_{i,t}.
]

因此从一个任务切换到另一个任务至少损失一个 service step。环境不额外施加 switch penalty；机会成本来自原生动力学。

多个 agent 可以选择同一个 entity，但只有“是否至少有一人服务”有效，重复分配会浪费容量。

---

## 3.5 Persistent station transition

Station (p) 的 health：

[
h_{p,t}\in{0,1,2,3,4}.
]

若至少一个 agent 在该 station 连续停留：

[
h_{p,t+1}=4.
]

否则：

[
h_{p,t+1}
=========

\max(0,h_{p,t}-1).
]

任一 station 达到零时：

[
failed\leftarrow1.
]

环境不会提前终止；失败状态保持到 episode 结束，保证每个 episode 固定为 32 steps。

---

## 3.6 Short job transition

一个 active job 的 work 为一单位。若至少一个 agent 对该 job 提供服务：

[
work_{j,t+1}=0.
]

否则 deadline 每步减少一。若 deadline 到零且 work 仍未完成：

[
failed\leftarrow1.
]

一个完成的 job 不再需要服务，但在当前 wave 结束前仍作为可观察 entity 保留，其 `work_remaining=0`。

---

## 3.7 原生外部奖励

所有中间步骤：

[
r_t^{ext}=0.
]

只在 (t=31)：

[
\boxed{
r_{31}^{ext}
============

\mathbb 1
\left[
failed=0
\land
\text{三个 waves 的全部 }3D_N\text{ jobs 均完成}
\right].
}
]

所有 agent 获得同一个共享奖励。

明确不存在：

* station occupancy reward；
* job completion reward；
* deadline reward；
* progress reward；
* distance reward；
* role reward；
* team-size reward；
* join、survival、KEEP 或 membership reward；
* intrinsic reward。

Station failure、job completion 和 deadline miss 只写入 diagnostics。

---

## 3.8 Termination

Episode 始终在：

[
T=32
]

结束。不存在 early success termination 或 early failure termination。

这样每个 (N) 的 transition exposure、GAE 长度和 optimizer exposure可以精确匹配。

---

## 3.9 Reset distribution

每次 reset：

1. 所有 station health 设为 4；
2. 从 (N) 个 agent 中均匀随机选出 (P_N) 个，并随机一一放到 stations；
3. 剩余 (D_N) 个 agent 位于 depot；
4. agent keys、station keys、job keys 和 tensor presentation order 独立随机排列；
5. 网络不读取这些 keys；
6. recurrent hidden 全部归零；
7. jobs 在 (t=4) 前不激活。

初始 station holders 的身份每 episode 随机，所以它们不是固定角色。

---

# 四、为什么 (N) 真正改变任务

AMDT 不是独立 Alice-and-Bob pairs 的并集。

所有 station 和 jobs 共享：

* 同一个 team capacity；
* 同一个全局 failure flag；
* 同一个终局成功谓词；
* 同一个 agent assignment pool。

任一 station failure都会使全部 job 工作失去最终价值；一个 agent 被重复分配到已有足够服务的 entity，会减少全队完成其他 entities 的能力。

随着 (N) 增加：

[
P_N\uparrow,\qquad
D_N\uparrow,\qquad
E_N\uparrow,
]

所以同时需要：

* 维持更多长期资源；
* 分配更多短期 jobs；
* 生成更长的匿名 joint action sequence；
* 避免更多重复 assignment。

更大的团队不是简单地更容易，因为每新增一个 agent也新增一个同时责任。

---

# 五、两个自然时间尺度

## Persistent responsibility

Station 存活约束贯穿整个 32-step episode。持续留在 station 可避免切换损失和 health decay。

## Short-lived responsibility

每个 job 只存在六步，一个 agent通常需：

1. 一步切换到 job；
2. 下一步继续选择该 job以完成服务；
3. 随 wave 变化重新分配。

因此环境自然允许：

[
\text{long station commitment}
\quad\text{与}\quad
\text{short dispatch episodes}.
]

但环境从不指定哪个 agent 应承担哪一种职责；任何 agent 都可在任意时刻交换任务。

本轮只验证 ordinary policy access 和 cross-(N) sharing，不统计这些行为为“learned skills”。

---

# 六、Observation 与 centralized state

## 6.1 Actor information

每个 agent 获得：

### Self vector：6 维

```text
at_depot
current_entity_has_health
current_entity_has_work
current_entity_health / 4
current_entity_deadline / 6
served_on_previous_step
```

没有 agent ID 或 slot index。

### Unordered entity set：每 entity 7 维

```text
is_depot
active
health / 4
work_remaining
deadline_remaining / 6
ready_service_count / N
currently_assigned_count / N
```

不提供 `station`、`dispatcher`、`maintainer` 等角色标签；entity 的功能由当前 health、work 和 deadline 状态定义。

### Generic set counts

[
\log(1+N),\qquad
\log(1+E_N).
]

它们只进入 policy representation，不进入 reward 或 intrinsic。

Actor 不读取：

* future wave schedule；
* oracle assignment；
* role label；
* failure/success predicate；
* external reward history；
* membership epoch；
* persistent member ID。

---

## 6.2 Centralized critic state

Critic 读取完整 active-agent set、entity set，以及：

```text
t / 32
current wave index
failed flag
total completed jobs
```

这些 critic-only fields不进入 actor。

---

# 七、共享策略与固定-(N) comparator

## 7.1 Treatment

```text
shared_variable_N
```

一个参数集合同时训练：

[
N\in{2,3,4,5,6}.
]

## 7.2 唯一 comparator

```text
fixed_N_specialist_family
```

五个相互独立的模型，每个只训练一个 (N)。

每个 specialist 与 shared model：

* 架构完全相同；
* 初始化完全相同；
* 对相应 (N) 接收相同数量的 transitions；
* 对相应 (N) 接收相同数量的 optimizer substeps；
* 使用相同 reset schedule；
* 使用相同 agent/entity permutations；
* 使用相同 categorical sampling uniforms。

Specialist family 是一个访问上界 comparator。虽然聚合参数量为五倍，但每个 within-(N) 比较都是严格 capacity-matched。

---

# 八、模型与概率合同

## 8.1 N-independent model

```text
member encoder: 6 -> 32 -> 32, GELU
entity encoder: 7 -> 32 -> 32, GELU
temporal core:  GRU, hidden 32
query MLP:      128 -> 64 -> 32, GELU
entity key:     33 -> 32
critic:         pooled state -> 64 -> 1
```

总参数量必须低于 35K，并在 M0 中记录 exact count。所有 (N) 使用相同 state-dict shapes。

---

## 8.2 Autoregressive action probability

每个 primitive step 外生采样一个 active-agent order：

[
\sigma_t.
]

联合策略：

[
\pi_\theta(\mathbf a_t\mid o_t)
===============================

\prod_{j=1}^{N}
\pi_\theta
\left(
a_{\sigma_t(j),t}
\mid
o_{\sigma_t(j),t},
a_{\sigma_t(<j),t}
\right).
]

前序 actions 通过每个 entity 的 planned-assignment count进入 prefix。

Policy 只对有效 entities产生 pointer logits。不存在：

[
K^N
]

joint-action枚举，也不存在 agent-agent dense attention。

Sampling/replay 必须存储：

```text
active member keys
active mask
agent external order
entity presentation order and keys
entity action mask
sampled entity pointer
applied prefix counts
old token log-probability
recurrent hidden masks
```

Teacher-forced replay最大误差：

[
\le10^{-6}.
]

---

## 8.3 PPO credit

环境 step (t) 只有一个 centralized advantage (A_t)。

Token loss按 active member平均：

[
L_{\pi,t}
=========

-\frac1N
\sum_{i=1}^N
\min
\left[
\rho_{i,t}A_t,,
\operatorname{clip}(\rho_{i,t},0.8,1.2)A_t
\right].
]

这样大 (N) 不会仅因 token 更多获得更大梯度权重。

GAE：

[
\gamma=0.99,\qquad
\lambda=0.95.
]

每个 (N) 的 advantages独立标准化。Value loss每个 environment step计算一次。

其他固定优化参数：

```text
learning rate       3e-4
PPO epochs          1
entropy coefficient 0.01
value coefficient   0.5
gradient clip       0.5
```

唯一训练奖励是终局 external reward。

---

# 九、第一项 cross-episode variable-(N) gate

## 9.1 训练与评估 N

训练：

[
N_{\mathrm{train}}={2,3,4,5,6}.
]

评估：

[
N_{\mathrm{eval}}={2,3,4,5,6}.
]

本轮不测试 unseen-(N) extrapolation。它只测试一套参数是否能在 episode 间变化的 (N) 上学习。

---

## 9.2 固定 exposure

```text
experiment               R51-AMDT-G0
arms                     shared_variable_N, fixed_N_specialist_family
parallel environments    16 per arm
episode / rollout        32 / 32
outer updates            625
environment transitions  320,000 per arm
transitions per N        64,000 per arm
episodes per N           2,000 per arm
agent-token decisions    1,280,000 per arm
shared optimizer steps   3,125
specialist steps/model   625
specialist aggregate     3,125
PPO epochs               1
```

每五个 outer updates形成一个平衡 cycle。每个 cycle中，每个 (N) 恰好出现16个episodes。

Shared model在每个 outer update执行五个 N-specific substeps；substep顺序由固定随机种子生成并存储。Specialist family相应执行每模型一个step。

---

## 9.3 Seeds

```text
model/init seed          51051
training reset seed      61051
order/action RNG seed    71051
evaluation reset seed    81051
bootstrap seed           91051
```

---

## 9.4 Evaluation

在训练前和 exact-final checkpoint上，分别执行：

```text
128 deterministic episodes per N per arm
640 episodes per arm
```

Shared 与 specialist 使用同一批：

* reset seeds；
* agent order；
* entity presentation permutations。

不选择 best checkpoint。

预计本地单卡 CUDA wall clock约为 15–25 分钟；环境本身没有物理模拟或图搜索。

---

# 十、结果指标与 equal-(N) aggregation

定义 (S_N^A) 为 arm (A) 在 team size (N) 上的终局成功率。

所有 macro 指标使用：

[
\bar S^A
========

\frac15
\sum_{N=2}^{6}S_N^A,
]

而不是按 agent tokens、episode长度或 (N) 加权。

Bootstrap单位为同一 (N) 下的 paired evaluation episode。Macro bootstrap先在每个 (N) 内重采样，再对五个 (N) 等权平均。

额外记录但不进入reward：

```text
station-failure rate
completed-job fraction
deadline-miss rate
duplicate-assignment fraction
station assignment dwell lengths
job assignment dwell lengths
```

---

# 十一、最小结果分支

## M0：实现有效性

必须全部满足：

1. 每个 (N) 的 (P_N,D_N,E_N) 与注册公式一致；
2. reward只在最终step出现，且严格等于完整成功谓词；
3. 无中间reward、shaping或intrinsic；
4. 无agent ID、slot embedding或oracle role；
5. shared与specialists初始参数逐位相同；
6. exact 320K transitions/arm、64K/N和3,125 optimizer steps/arm；
7. shared与specialists的 N schedule、reset streams和随机顺序配对；
8. active token count严格等于 (N)；
9. entity action mask、agent order和prefix完整存储；
10. sample/replay log-probability误差 (\le10^{-6})；
11. absent members和masked entities不产生token或概率质量；
12. recurrent hidden只在episode reset清零；
13. relevant modules有有限非零gradient和parameter drift；
    14.所有checkpoint、metrics和trajectories有限；
14. exact-final checkpoint由final update直接产生，无best selection。

失败：

```text
INVALID_R51_AMDT_WIRING
```

唯一下一动作：只修复明确的transition、reward、mask、replay、count、checkpoint或pairing缺陷，并原合同重跑。

---

## M1：ordinary-policy specialist access

对每个 (N)：

[
S_N^{spec}\ge0.60.
]

Equal-(N) macro：

[
\bar S^{spec}\ge0.70.
]

每个 (N) 的 paired final-minus-zero bootstrap：

[
\operatorname{LCB}*{95}
\left[
S*{N,\mathrm{final}}^{spec}
---------------------------

S_{N,\mathrm{zero}}^{spec}
\right]

> 0.20.
> ]

将每个 (N) 的128个evaluation episodes分成四个连续32-episode blocks；至少三个blocks必须满足：

[
S_{N,\mathrm{block}}^{spec}\ge0.50.
]

若M0通过但M1失败：

```text
NO_ACCESS_R51_AMDT_SPECIALISTS
```

解释：该精确 sparse task/ordinary-policy contract没有形成访问锚点。Shared结果全部隔离。

唯一下一动作：永久退休 AMDT 的精确 dynamics、horizon和reset contract，完成一次环境设计失败审查。不得增加steps、seeds、model、threshold或reward；任何后继环境必须重新注册，而不能作为R51 rescue。

---

## M2：shared cross-N learning

要求：

[
S_N^{shared}\ge0.50
\qquad\forall N,
]

[
\bar S^{shared}\ge0.65,
]

[
\min_N
\frac{S_N^{shared}}
{S_N^{spec}+10^{-8}}
\ge0.75,
]

[
\frac{\bar S^{shared}}
{\bar S^{spec}+10^{-8}}
\ge0.85,
]

以及paired equal-(N) macro noninferiority：

[
\operatorname{LCB}_{95}
\left[
\frac15
\sum_N
\left(
S_N^{shared}-S_N^{spec}
\right)
\right]

> -0.10.
> ]

Shared final-minus-zero macro还必须满足：

[
\operatorname{LCB}*{95}
[
\bar S*{\mathrm{final}}^{shared}
--------------------------------

\bar S_{\mathrm{zero}}^{shared}
]

> 0.25.
> ]

若M0、M1通过但M2失败：

```text
VALID_FAIL_R51_SHARED_VARIABLE_N
```

允许结论：

> AMDT在每个固定 (N) 上可访问，但所注册的一套共享匿名策略没有在多个 (N) 上接近capacity-matched specialists。

唯一下一动作：永久退休该 exact shared set-pointer MAPPO contract，并停止当前 variable-(N) learning line，先完成架构/优化失败审查。不得修改环境、模型宽度、更新量、seed或阈值进行救援。

---

## PASS

```text
PASS_R51_AMDT_VARIABLE_N
```

要求：

[
M0\land M1\land M2.
]

唯一下一动作：

> 在同一个 AMDT、同一个普通策略和同一外部奖励上，注册一次 within-episode **exogenous** join/leave 与 membership-censoring gate。

不得直接进入技能、KEEP/SET、variable lifetime或S7。

---

# 十二、当前与延后的合同

| 合同                                         | R51是否执行 |
| ------------------------------------------ | ------- |
| variable (N) across episodes               | 执行      |
| stable membership within episode           | 执行      |
| anonymous shared parameters                | 执行      |
| permutation/mask/replay                    | 执行      |
| active-only AR action                      | 执行      |
| recurrent hidden reset at episode boundary | 执行      |
| within-episode join/leave                  | 延后      |
| leaver membership censoring                | 延后      |
| survivor hidden/skill/age continuity       | 延后      |
| learned admission                          | 禁止      |
| learned agent order                        | 禁止      |
| skill latent或KEEP/SET                      | 不存在     |
| variable skill lifetime                    | 延后且尚无授权 |
| intrinsic reward                           | 不存在     |
| S7/UAV transfer                            | 延后      |

此前open-roster disposition同样要求先完成cross-episode variable (N)，之后才进入within-episode外生membership，并将learned admission另行视作带likelihood与credit的新动作。

---

# 十三、计算复杂度

令：

[
E_N=N+1
]

为有效task entities数，(d=32)为embedding宽度。

每个environment step：

[
\text{member encoding}=O(Nd^2),
]

[
\text{entity encoding}=O(E_Nd^2),
]

[
\text{AR pointer scoring}=O(NE_Nd).
]

即：

[
\boxed{O(NK)}
]

其中当前 action support (K=E_N)。

Replay和update具有同阶复杂度。Rollout storage只保存active members、entities、masks、orders、actions、prefix和old log-probabilities：

[
O(T(N+E_N)).
]

不存在：

* (K^N) roster枚举；
* mandatory agent-agent (N\times N) interaction tensor；
* fixed-agent parameter blocks；
* slot-specific policy head。

---

# 十四、PASS能够与不能够建立什么

## PASS能够建立

1. AMDT是一个在注册预算下可被普通策略访问的variable-team task；
2. (N) 改变了真实任务负载和可行分配，而不仅是tensor长度；
3. 一套匿名、N-independent策略能够在多个训练team sizes上接近相应fixed-(N) specialists；
4. R49式set/mask/replay接口可以承载真实task-level learning。

## PASS不能建立

1. unseen-(N) interpolation或extrapolation；
2. within-episode join/leave正确性；
3. membership censoring的任务价值；
4. variable skill lifetime有效；
   5.任何skill semantics；
5. intrinsic reward有效；
6. HMASD parity；
7. S7/UAV transfer；
   9.论文novelty。

---

# 十五、永久关闭与禁止救援

R51不会重新开放：

* R39 fixed-(N) toy credit；
* R42–R48全部skill、renewal、credit、spectral与hidden-reset路线；
* R50 synthetic bandit；
  -现有 asymmetric-cycle Alice-and-Bob原样复用；
* task shaping或environment-specific intrinsic；
* learned admission；
* learned agent order；
* agent identity或slot-specific blocks；
* S7-first；
* variable-lifetime first；
* 通过增加seed、数据、budget、model、阈值、reward或best-checkpoint选择挽救有效失败。

项目的promotion原则也明确要求先建立低层访问和机制证据，再进入异步时序比较；下游claim不能绕过失败的上游边。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\texttt{ACCEPT_VARIABLE_TEAM_TOY_REQUIREMENTS};\
&\text{唯一环境：Anonymous Maintenance--Dispatch Task};\
&\text{唯一正式比较：shared variable-}N\text{ policy}\
&\qquad\text{versus capacity-matched fixed-}N\text{ specialists};\
&\text{specialists先承担ordinary-policy access prerequisite};\
&\text{M1失败：退休精确环境并隔离shared结果};\
&\text{M1通过、M2失败：退休精确shared learning contract};\
&\text{PASS：只授权同任务的within-episode exogenous membership gate};\
&\text{不授权skill、variable lifetime、intrinsic、S7或novelty claim。}
\end{aligned}
}
]
