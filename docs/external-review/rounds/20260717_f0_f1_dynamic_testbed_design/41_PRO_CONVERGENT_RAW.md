## 1. Final verdict

# `MODIFY_TESTBED_CONTRACT`

保留一个匿名动态 roster、长短双职责和单次终局外部效用的 testbed，但必须改为 **单一通用 `SHORT` 动作、primitive-action autoregressive direct access、320K/PPO4 串行证据合同**，并删除不能改变因果分支的硬门槛堆叠。

---

## 2. Blind-review adjudication

### 2.1 证据事实

当前 event runtime 已经实现并审计了：

* 单一 policy-runtime lifecycle store；
* JOIN、temporary LEAVE、REJOIN、terminal LEAVE；
* pre-removal/post-membership 双快照；
* active-only packing；
* F0/F1 相同参数图；
* per-owner (\gamma^\Delta) return 与 GAE；
* ragged low replay；
* strict schema-3 resume；
* common-support constructive prefix path。

但是它仍然是 **environment-free deterministic transaction boundary**。生产入口在 collector 构造前调用 `assert_deterministic_trace_boundary` 并硬停止，因此现有证据不能支持环境 access、skill learning、variable-(N) utility 或 F1 优势。

F0/F1 在代码中的唯一 mode 差异确实是：

[
g(C^{(0)})
\quad\text{vs}\quad
g(C^{(j-1)}),
]

其余 commitment model、critic、low actor、low critic 和 event ledger 共用。

此前结果给出五个必须保留的约束：

1. **R41B** 证明原始 HMASD 在固定 (N) Alice–Bob 上存在正向能力锚点：final win `0.89`，而 zero-step 为 `0`；但它没有测试动态 roster 或 F0/F1。
2. **R51** 的实现、终局 reward、replay 和优化都有效，但所有 fixed-(N) specialist final success 都为零；因此不能再让 shared arm 绕过 ordinary-access prerequisite。
3. **R52** 中 stochastic training carrier 明显非零，但所有 deterministic specialist 最终 (U=0)；这证明正的训练期 expected return 不等于稳定可执行 mode。
4. **R53** 中 final deterministic competence 很高，但多个 final-minus-zero 下界没有达到注册增益，因此“终局能力”不能替代“学习增益”。
5. **R54** 中 full-active-set reference 随 (N) 明显退化，说明完整信息可见并不自动带来可优化性；同时也不能据此预装 graph、slot 或 critical-residual 栈。

当前没有本轮科学结果 JSON；入口明确说明本轮只审阅 testbed 设计，不授权实现或训练。

### 2.2 竞争性因果假设

| 假设                                   | 因果主张                                                                                            | 当前地位                             | 最小区分证据                                                                                           |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------ |
| **H0 / F0 sufficiency**              | active-set recurrence、异步机会、KEEP/SET 和 duration-correct credit 已足够；prefix coupling 没有额外任务价值      | 最强零假设，尚未被击败                      | F0 在 direct-access 已成立的环境中学习双职责，且 F1 没有正的外部效用增益                                                  |
| **H1 / F1 applied-prefix value**     | earlier applied commitment 会有方向地改变 later token 的共同支持分布，并改善团队职责组合                                | 只有结构路径，无 learnability/utility 证据 | 自然 post-initial common-support 变化、重复职责减少、F1-minus-F0 terminal utility 三者同时成立                     |
| **H2 / skill execution failure**     | 任务可由 primitive policy 学会，但 skill-conditioned low actor 无法形成或自然使用 persistent/reactive primitives | 上游活跃解释                           | direct arm 成功，而 F0/F1 均无 between-skill persistent process separation 且任务失败                       |
| **H3 / exogenous timing limitation** | skill 与 prefix 都有用，但固定外生 opportunity 无法及时响应短 wave 或 owner loss                                  | 仅条件性诊断                           | direct access、skill execution、prefix direction 均成立后，失败显著集中在 registered timing-infeasible windows |

Learned hazard/point process 不进入当前组合。H3 成立也只支持“时点可能是限制”，不授权学习 event time。

### 2.3 共同主张

接受两份盲审和 Codex 的共同骨架：

[
\text{ordinary access}
\rightarrow
\text{executable skills}
\rightarrow
\text{F0 vs F1}
\rightarrow
\text{conditional timing diagnosis}.
]

同时接受：

* 匿名 `4→2→6→4` active roster；
* persistent duty 与 short reactive duty 同时必要；
* 单次终局 graded external utility；
* task、membership、opportunity 和 order RNG 独立；
* direct arm 只是 access instrument；
* F0/F1 只有 summary selector 不同；
* H3 不得越过 access、skill 和 prefix 证据；
* 不恢复 R51–R55 或任何 intrinsic/shaping 路线。

### 2.4 四个分歧

#### A. 一个 generic `SHORT`，不使用 `SHORT_A/SHORT_B`

选择：

[
\boxed{
\mathcal A={\texttt{IDLE},\texttt{PERSIST},\texttt{SHORT}}
}
]

不是 A/B 两类 short action。

原因是当前需要区分的组合本质为：

[
\text{exactly one persistent commitment}
+
(N_t-1)\text{ reactive commitments}.
]

只要每个 short wave 要求：

[
R_w=N_w-1
]

个不同 lifecycle 完成工作，单一 `SHORT` 已经产生：

* 随 (N_t) 变化的 workload；
* persistent 与 reactive 的并行竞争；
* duplicate persistent assignment 的真实代价；
* later token 对 earlier commitment 的潜在依赖。

A/B 不增加新的 F1 因果需求，却增加了：

* 额外 task-type 匹配；
* 额外 low-policy semantic axis；
* 将 H2 skill failure 与 H1 prefix failure混合的风险。

因此 A/B 更像为了展示 F1 而增加的任务结构。Codex 已承认 A/B 只有在单一 short 无法产生 (N_t)-dependent competing commitments 时才必要；下面的精确 generic-short state machine 已关闭这一缺口。

#### B. direct access 使用 primitive-action autoregression

选择 Open-Pro/Codex 的较强 direct instrument：

[
p(\mathbf a_t\mid C_t)
======================

\prod_{j=1}^{N_t}
p(a_{\sigma_j,t}\mid
o_{\sigma_j,t},h_{\sigma_j,t},
g(A_t),a_{\sigma_{<j},t}).
]

它：

* 每个 primitive step 对全体 active members 决策；
* 使用共享 recurrent policy；
* 使用匿名 uniform recorded order；
* later token 看到 earlier primitive-action count prefix；
* 没有 skill、KEEP/SET 或 high event process。

这不是 F1 的 comparator；它只回答 task substrate 是否可由一个强 ordinary policy 访问。使用独立 primitive MAPPO 会人为削弱 ordinary objection。

#### C. 使用 320K / PPO4 / 单一 ledger generator，不使用三训练种子

拒绝 Gemini 的 `500K × PPO10 × 3 seeds`，因为其 per-arm/per-seed exposure 不闭合，也在 access 未知前扩大计算。

冻结：

[
16\times80\times250=320{,}000
]

primitive environment transitions per trained arm，PPO 4 passes。

“single ledger”不表示所有 episode 重复同一轨迹，而是：

> 一个冻结的 ledger generator、一个训练 master seed、4,000 个独立 episode ledgers，以及一套不重叠的 256 个 evaluation ledgers。

F0/F1 共享对应 ledger IDs 和外部 RNG 合同；不强迫 treatment-induced on-policy trajectory 相同。Codex 对 Pro exposure 和串行执行的选择成立。

#### D. 保留最小 branch-bearing thresholds

不采用 Gemini 的过弱三指标，也不采用 Open-Pro 将所有 diagnostic 都变成 hard gate 的方案。

只保留：

1. M0 correctness；
2. no-learning substrate carrier；
3. direct learned access；
4. skill execution；
5. H1 所必需的 distribution、direction、utility 三项。

Lifetime histograms、frontier sizes、timing feasibility、role occupancy 和各 block 数据全部记录，但除非进入对应因果分支，不成为独立 PASS。

---

## 3. Launch-exact environment contract

### 3.1 Episode and substep order

固定：

[
H=80,\qquad t\in{0,\ldots,79}.
]

每个 primitive step 的顺序为：

```text
1. 若 t>0，完成上一 primitive transition
2. 应用 t 时刻的 external membership transaction
3. 生成 t 时刻到达的 short wave
4. 形成 actor observation / critic state
5. F0/F1 处理到期 event frontier；direct 处理全 active primitive frontier
6. 所有 active members 执行 primitive action
7. 更新 persistent duty 与 short duty
8. t=79 时支付唯一 terminal reward
```

无 early termination。完成 step 79 后 `terminated=True`；没有 time-limit truncation。

### 3.2 Membership ledger

Routing keys 不进入网络。

#### (t=0)

四个 genuine JOIN：

[
A_0={\kappa_0,\kappa_1,\kappa_2,\kappa_3}.
]

每个成员：

* recurrent states 为零；
* skill 未定义；
* event opportunity 立即到期；
* high action 只能 `SET(z)`。

#### (t=20)

从初始四成员中均匀无放回选两个：

[
L_{20}\subset A_{19},\quad |L_{20}|=2.
]

它们执行 temporary LEAVE：

[
|A_{20}|=2.
]

hidden、skill、age 和 remaining gap 冻结。

#### (t=40)

* (L_{20}) 以原 lifecycle REJOIN；
* 两个新 lifecycle genuine JOIN。

因此：

[
|A_{40}|=6.
]

四个 rejoin/join members 在该 boundary 立即获得 opportunity。

#### (t=60)

从当时六个 active lifecycles 中独立均匀无放回选两个执行 terminal LEAVE：

[
|A_{60}|=4.
]

若 persistent owner 被移除，owner 在 primitive action 前清空。

t=60 前已经完成的 team work 不回滚。终止成员不拥有 t=60 后的 actor rows；这一 credit difficulty 对 direct、F0 和 F1 完全一致，并由 direct-access 阶段先行校准，禁止在某个 arm 单独修复。

### 3.3 Primitive actions

对所有 active members：

```text
0 = IDLE
1 = PERSIST
2 = SHORT
```

无环境侧 action mask、hard role 或 agent-specific action support。

F0/F1 使用：

[
K=3
]

个 latent skills。Low actor 保持：

[
\pi_l(a_i\mid o_i,z_i).
]

### 3.4 Persistent duty

状态：

* `persistent_owner ∈ active lifecycle ∪ {NONE}`；
* `persistent_units ∈ {0,\ldots,64}`。

每一步：

1. 若 owner 仍 active 且执行 `PERSIST`：

   * `persistent_units += 1`，上限 64；
   * owner 保持。
2. 若 owner 不存在，或者 owner 未执行 `PERSIST`：

   * 若至少一个 active member 执行 `PERSIST`，由独立 owner-tiebreak ledger 均匀选择新 owner；
   * handoff step 不产生 persistent unit。
3. 非 owner 的多余 `PERSIST` 不产生任何工作。
4. owner temporary/terminal leave 时立即清空。

因此 persistent duty 要求一个成员长时间连续保持，而 duplicate persistent assignment 被自然浪费，但不通过额外 reward 惩罚。

定义：

[
P=\min\left(\frac{\text{persistent_units}}{64},1\right).
]

### 3.5 Short reactive duty

使用 8 个 wave。每个 wave 的到达时刻在 reset 时由 task RNG 独立选择：

[
{0},
{9,10},
{24,25},
{32,33},
{40},
{49,50},
{64,65},
{72,73}.
]

未来 wave 时刻不进入 observation。

Wave (w) 在 membership transaction 完成后生成。令：

[
N_w=|A_{t_w}|,\qquad R_w=N_w-1.
]

每个 wave 持续四个 primitive steps：

[
t_w,t_w+1,t_w+2,t_w+3.
]

对每个 lifecycle 保存：

* `short_streak ∈ {0,1,2}`；
* `contributed_current_wave ∈ {0,1}`。

规则：

* active 且未贡献的成员执行 `SHORT`：`streak += 1`；
* 执行 `IDLE` 或 `PERSIST`：`streak = 0`；
* `streak == 2` 时产生一个 work unit，并令 `contributed=1`；
* 每个 lifecycle 每个 wave 最多贡献一次；
* leave 或 wave 结束清空 streak；
* 四步结束时未完成的 work 永久失效。

定义：

[
S=
\frac{\sum_w\text{completed_work}_w}
{\sum_w R_w}.
]

在冻结 roster 过程中，分母为：

[
3+3+1+1+5+5+3+3=24.
]

任务的最优职责结构是：

[
1\text{ persistent owner}
+
(N_t-1)\text{ short workers}.
]

没有成员被 observation 或 reset 指定为某个角色。

### 3.6 External reward

唯一外部奖励：

[
r_t=
\begin{cases}
0,&t<79,[2mm]
U=\frac12(P+S),&t=79.
\end{cases}
]

为全体当前 active members 共享的 scalar team reward。

诊断字段 `P`、`S`、wave progress、owner handoff 和 completed work：

* 不在中间时刻支付；
* 不进入 intrinsic；
* 不形成 contact/progress bonus；
* 不形成 potential difference；
* 不进入 high/low reward 的额外通道。

这不是 shaping，因为 (U) 本身就是环境的最终任务目标和 evaluation estimand，而不是为另一个成功谓词构造的中间势函数。

### 3.7 Actor observation

每个 active member 的 primitive observation 为 **15 维**：

|    维度 | 字段                               | 归一化                                     |
| ----: | -------------------------------- | --------------------------------------- |
|     0 | primitive time                   | (t/80)                                  |
|     1 | active count                     | (\log(1+N_t)/\log 7)                    |
|     2 | persistent units                 | `units/64`                              |
|     3 | owner exists                     | (0/1)                                   |
|     4 | wave active                      | (0/1)                                   |
|     5 | wave steps remaining             | `remaining/4`                           |
|     6 | wave work remaining              | `remaining_work/max(R_w,1)`             |
|     7 | arrived-wave completion fraction | completed / required-arrived；无 wave 时 0 |
|     8 | self is persistent owner         | (0/1)                                   |
|     9 | self short streak                | `streak/2`                              |
|    10 | self contributed current wave    | (0/1)                                   |
|    11 | cumulative active execution time | `active_steps/80`，absence 不增加           |
| 12–14 | previous primitive action        | 3-way one-hot                           |

Temporary leave 冻结 previous action 和 active execution time；rejoin 恢复。Genuine join 的 previous action 固定为 `IDLE`。

公共字段 0–7 对同一 active set 中所有成员相同。禁止：

* lifecycle key、epoch、member index；
* future membership/wave schedule；
* sampled owner tie-break；
* assigned role；
* future opportunity；
* external reward、return 或 success label。

High event member token继续使用已接受的：

[
[o_i,\operatorname{emb}(z_i),\log(1+\tau_i),
\text{join},\text{rejoin}].
]

Low actor只获得 15 维 observation 和 (z_i)。

### 3.8 Centralized critic state

每个 active member critic token使用同一 15 维 observation；F0/F1 critic另外通过现有 runtime读取：

* current skill；
* skill age；
* join/rejoin flag；
* owner high hidden；
* boundary kind。

Global critic vector固定为 observation 的公共 8 维字段。

禁止 critic读取：

* future ledger；
* routing key/epoch；
* future wave；
* sampled action/order；
* external return。

### 3.9 Reset and independent RNG ledgers

固定 master seeds：

```text
direct model init         = 57056
paired F0/F1 model init   = 57057
training task ledger      = 67057
event opportunity/order   = 77057
policy action sampling    = 87057
evaluation ledger         = 97057
bootstrap                 = 107057
```

对 episode `e` 和 stream `s`：

[
RNG(e,s)
========

PCG64(\operatorname{SeedSequence}[
master,e,s]).
]

Task-ledger stream IDs：

```text
0 = t20 temporary-leave selection
1 = t60 terminal-leave selection
2 = wave arrival choices
3 = persistent-owner tie breaks
4 = active presentation permutations
5 = direct primitive frontier orders
```

Event master的 stream：

```text
0 = per-member opportunity gaps
1 = F0/F1 frontier permutations
```

训练 ledger IDs：

[
0,\ldots,3999.
]

Evaluation ledger IDs：

[
0,\ldots,255
]

但使用独立 evaluation master，因此与训练不重叠。

F0/F1 使用相同 external ledgers 和相同 action-uniform streams；策略分布不同后产生的 trajectory divergence 属于 treatment effect，不强制消除。

---

## 4. Evidence execution order

这是一份注册合同，按因果必要性串行执行，不是三条独立 toy 路线。

### Stage A — no-learning carrier checks

使用全部 256 evaluation ledgers，不训练。

#### Constructive controller

Routing-only controller：

* owner active时持续 `PERSIST`；
* owner缺失时按 tiebreak ledger选择一个 active member接管；
* wave active时所有非 owner 且未贡献成员执行 `SHORT`；
* 其余执行 `IDLE`。

要求：

[
\bar P_{\text{oracle}}\ge0.95,\qquad
\bar S_{\text{oracle}}\ge0.95,\qquad
\bar U_{\text{oracle}}\ge0.95.
]

#### Uniform random

每个 active member每步独立均匀选择三个 primitive actions。

要求：

[
\Pr(U>0)\ge0.20,
]

[
\bar U_{\text{random}}<0.55.
]

第一项证明 terminal reward carrier 非恒零；第二项排除 random ceiling。

若 Stage A 失败，退休该精确 testbed，不运行任何学习 arm。

### Stage B — direct primitive-AR access

仅在 Stage A 通过后执行。

#### Direct policy

* shared per-lifecycle recurrent actor；
* active-only sum/count encoder；
* 每个 primitive step 对 active set 采样 uniform recorded order；
* later token获得当前步 earlier action counts；
* centralized active-set critic；
* 无 skill、KEEP/SET 或 event opportunity。

#### Exposure

```text
num_envs                   = 16
episode_horizon            = 80
rollout_length             = 80
outer_updates              = 250
total_environment_steps    = 320,000
PPO passes/update          = 4
optimizer steps            = 1,000
```

每个 PPO pass使用该 update 的完整 valid recurrent batch，不额外拆分 minibatch，也不从旧 update 重放数据。

冻结：

```text
optimizer                  = Adam
learning_rate              = 3e-4
gamma                      = 0.99
GAE lambda                 = 0.95
PPO clip                   = 0.20
value clip                 = 0.20
value-loss coefficient     = 0.50
entropy coefficient        = 0.01
global grad clip           = 0.50
max recurrent chunk        = 20
advantage normalization    = per collected update
```

#### Evaluation

在 update 0 和 exact update 250：

* 256 deterministic episodes；
* 256 stochastic episodes；
* 相同 evaluation ledger IDs；
* 不选择 best checkpoint。

Direct access成立需要：

[
\bar U_{\mathrm{direct,det}}\ge0.70,
]

[
\bar P_{\mathrm{direct,det}},
\bar S_{\mathrm{direct,det}}\ge0.65,
]

[
\bar U_{\mathrm{direct,stoch}}\ge0.60,
]

以及 10,000 次 paired-episode percentile bootstrap：

[
LCB_{95}
\left(
U_{\mathrm{direct,final,det}}
-----------------------------

U_{\mathrm{direct,zero,det}}
\right)>0.15.
]

这同时防止 R52 的 stochastic-only carrier 和 R53 的高 zero-step competence重现。

若 direct 失败，退休该 testbed；不运行 F0/F1。

### Stage C — paired F0/F1

仅在 direct access 成立后执行。

每 arm：

```text
num_envs                   = 16
episode_horizon            = 80
rollout_length             = 80
outer_updates              = 250
environment_steps          = 320,000
PPO passes/update          = 4
high optimizer steps       = 1,000
low optimizer steps        = 1,000
latent skills K            = 3
```

High optimizer包含 commitment policy 与 event critic；low optimizer包含 low actor 与 low critic。其余 PPO 参数与 direct相同。

F0/F1：

* byte-equal initialization；
* 相同 state-dict keys；
* 相同 training/evaluation ledgers；
* 相同 opportunity/order streams；
* 相同 high/low batches与更新次数；
* 相同 zero/final evaluation；
* 唯一区别为 summary selector。

每臂在 zero/final各运行：

* 256 deterministic episodes；
* 256 stochastic episodes。

F0/F1 paired contrasts使用相同 256 ledgers和 bootstrap seed `107057`，10,000 次 episode-paired resampling。

### Forced-skill audit

在两个 final checkpoint各抽取 128 个自然、非 (t=0) snapshot，按 roster phase平衡。

对每个 snapshot、每个 (z\in{0,1,2})：

* 仅强制 focal member 的 (z)；
* 其他 policy与环境不变；
* 执行 (W=12) primitive steps；
* 两个独立 action RNG replicas；
* forced data只用于审计，不训练 scorer或 policy。

---

## 5. Attribution and outcome branches

### 5.1 Skill execution read

对每个 skill定义 12-step process signature：

[
\psi_z=
\left[
f_{\texttt{PERSIST}},
f_{\texttt{SHORT}},
\Delta P_{\text{units}}/12,
\Delta S_{\text{work}}/\max(R_w,1)
\right].
]

定义：

[
B=
\operatorname{median}*{z\neq z'}
|\mathbb E[\psi_z]-\mathbb E[\psi*{z'}]|_2,
]

[
W=
\operatorname{median}*{z,r\neq r'}
|\psi*{z,r}-\psi_{z,r'}|_2,
]

[
\rho=\frac{B}{W+10^{-8}}.
]

Arm 的 executable-skill read成立需要：

1. (LCB_{95}(\rho)>1)；
2. persistent-like skill (z_P) 与 reactive-like skill (z_S) 不同；
3. 两个技能对应动作占用率相对其它技能的 margin 均 (>0.15)；
4. (z_P,z_S) 在自然 rollout 中各覆盖至少 `10%` active primitive steps。

这些指标只确定 skill execution与natural use，不建立 task value。

### 5.2 F0 task sufficiency

F0 task access成立需要：

[
\bar U_{\mathrm{F0,det}}\ge0.60,
]

[
\bar P_{\mathrm{F0,det}},
\bar S_{\mathrm{F0,det}}\ge0.55,
]

[
LCB_{95}
(U_{\mathrm{F0,final,det}}
--------------------------

U_{\mathrm{F0,zero,det}})

> 0.10.
> ]

### 5.3 H1 natural applied-prefix evidence

只使用 F1 natural on-policy event rows，且必须满足：

* (t>0)；
* frontier size (m\ge2)；
* token position (j>0)；
* actual prefix 与 initial-prefix counterfactual具有完全相同 legal support；
* focal observation、incumbent、pre-hidden、critic source和参数完全相同；
* 不重新采样 action；
* 不使用 forced/synthetic row；
* 明确排除 episode-start all-join rows。

对 later token计算：

[
p^{work}_j
==========

\pi_\theta(\cdot\mid C^{j-1}),
\qquad
p^{init}_j
==========

\pi_\theta(\cdot\mid C^{0}).
]

#### Distributional read

[
D_{\mathrm{TV}}
===============

\frac12
\sum_{a\in S}
|p^{work}_j(a)-p^{init}_j(a)|.
]

至少需要 1,024 个 eligible natural rows，并要求：

[
LCB_{95}(\mathbb E[D_{\mathrm{TV}}])>0.02.
]

F0 对同一 read 的最大误差必须：

[
\max D_{\mathrm{TV}}^{F0}\le10^{-6};
]

否则属于实现无效，而不是 F0 scientific result。

#### Directional composition read

Forced-skill audit确定 (z_P)。令当前 applied working roster 中 persistent-like commitment数为 (n_P)。

定义：

[
d_j=
\begin{cases}
p^{work}_j(z_P)-p^{init}_j(z_P),&n_P=0,[1mm]
p^{init}_j(z_P)-p^{work}_j(z_P),&n_P\ge1.
\end{cases}
]

即：

* roster 尚无 persistent commitment时，应提高其概率；
* 已有 persistent commitment时，应降低 duplicate概率。

要求：

[
LCB_{95}(\mathbb E[d_j])>0.02.
]

#### External utility read

H1 还必须满足：

[
LCB_{95}
(U_{\mathrm{F1,det}}-U_{\mathrm{F0,det}})

> 0.03,
> ]

且：

[
\bar U_{\mathrm{F1,det}}\ge0.60,
\qquad
\bar P_{\mathrm{F1,det}},
\bar S_{\mathrm{F1,det}}\ge0.55.
]

同时 F1 executable-skill read必须成立。

仅有 prefix gradient、TV 或 synthetic constructive read不能支持 H1。

### 5.4 Conditional H3 timing read

Timing不独立 PASS。

对每个 short wave，在 arrival时定义：

[
\text{feasible}_w=1
]

当至少 (R_w) 个 active members满足以下之一：

* 已携带 reactive-like skill；
* 在 (t_w+2) 前具有已记录 opportunity，仍可完成两步 `SHORT` streak。

Persistent owner失效后另记录：

[
D_{\mathrm{recover}}
====================

\text{下一 active persistent-like commitment出现所需步数}.
]

只有在：

* direct access成立；
* F1 executable skills成立；
* F1 prefix TV和direction成立；
* 但 F1-minus-F0 task gain不成立；

时，才读取 H3。

若：

* 至少 `25%` 未完成 work 被分类为 timing-infeasible；
* feasible-wave completion minus infeasible-wave completion 的 95% CI 下界 (>0)；

则标为 **conditional H3 support**。这不授权 learned hazard。

### 5.5 互斥结果分支

按以下优先级解释：

| 分支                                | 条件                                                  | 假设更新                | 唯一处置                         |
| --------------------------------- | --------------------------------------------------- | ------------------- | ---------------------------- |
| `INVALID_IMPLEMENTATION`          | 环境、ledger、replay、resume、F0 reduction 任一 M0 错误       | H0–H3 均不更新          | 只修命名错误，合同不变                  |
| `RETIRE_TESTBED_CARRIER`          | constructive/random carrier失败                       | testbed substrate无效 | 永久退休该精确 testbed              |
| `RETIRE_TESTBED_NO_DIRECT_ACCESS` | direct access失败                                     | H0–H3 未识别           | 永久退休该精确 testbed              |
| `SUPPORT_H1_ON_TESTBED`           | skill、prefix TV、direction、F1 task gain全部成立          | H1上升，H0被该 testbed反驳 | 停止；另行进行 integration decision |
| `SUPPORT_H0_STOP_AT_F0`           | F0 task sufficiency成立，但H1完整条件不成立                    | H0上升，H1退休           | 停在F0                         |
| `SUPPORT_H2_SKILL_LIMIT`          | direct成功，F0/F1 task均失败且两臂skill execution均失败         | H2上升                | 停止skill/F1解释，不自动加模块          |
| `CONDITIONAL_H3_TIMING_LIMIT`     | skill与prefix direction成立、task gain失败、timing split成立 | H3条件性上升             | 停止并做一次跨轮架构解释                 |
| `VALID_MIXED_UNCATEGORIZED`       | 有效但不满足上述组合                                          | 不强行归因               | 停止；不生成 successor toy         |

只要 Stage C 已运行，所有连续指标及 CI 均保留，即使上游 scientific branch失败；但不得用下游描述性读数覆盖上游失败。

---

## 6. F0/F1 causal isolation

### 6.1 必须完全相同

F0/F1 必须共享：

* environment state machine；
* task/member ledgers；
* opportunity gaps；
* recorded frontier order；
* active presentation；
* lifecycle store；
* high/low model graph；
* parameter count和初始化；
* critic；
* low actor；
* action support；
* legal mask；
* high/low optimizer；
* value normalization；
* event return与GAE；
* checkpoint schema；
* rollout/evaluation exposure。

当前实现已经把 mode差异集中为：

```text
F0 -> initial_summary
F1 -> working_summary
```

并在每个 token 后立即更新 working commitment summary。

必须匹配的是：

[
\boxed{\text{same data-generation contract}}
]

而不是 identical realized trajectories。F1改变动作后，后续状态分布分叉属于待测因果效应。

### 6.2 Natural common-support boundary

H1证据不得来自：

* (t=0) all-join对称性；
* synthetic parameter control；
* forced skill trajectory；
* mask变化；
* additive common-logit shift；
* post-sampling repair；
* routing identity。

当前 deterministic test中的 constructive centered-logit control只证明参数路径存在，不证明自然使用；测试本身也将此明确限制为 wiring evidence。

### 6.3 最强 ordinary-MARL 反对意见

最强 matched baseline不是旧 fixed-(N) MAPPO，而是 F0：

* 动态 JOIN/LEAVE/REJOIN；
* survivor hidden continuity；
* per-agent exogenous opportunities；
* variable realized lifetime；
* skill-conditioned recurrent low actor；
* active-set critic；
* exact event probability；
* duration-aware credit；
* 与 F1 相同 exposure。

Direct primitive-AR再证明任务本身可访问。

因此 F1 不能把以下能力当作贡献：

* variable (N)；
* asynchronous lifetime；
* ragged replay；
* schema-3 resume；
* skill persistence；
* active-set representation。

F1 唯一可支持的新增能力是：

[
\boxed{
\text{natural earlier commitment}
\rightarrow
\text{later common-support relative distribution}
\rightarrow
\text{better composition}
\rightarrow
\text{higher external utility}
}
]

缺少最后两项时，ordinary-MARL objection保持成立。

---

## 7. Replacement ledger and stop

### 7.1 Final-capability map

| Family                       | Dynamic roster | Per-agent realized lifetime | Executable skill bottleneck |                    Joint mark coupling | 当前状态                       |
| ---------------------------- | -------------: | --------------------------: | --------------------------: | -------------------------------------: | -------------------------- |
| Direct primitive-AR          |              是 |          不测试 skill lifetime |                           否 |                    primitive-action AR | access instrument          |
| F0 active-set scheduled MARL |              是 |                           是 |                           是 |                否；initial-context marks | mandatory matched baseline |
| F1 event-frontier editor     |              是 |                           是 |                           是 | applied-prefix common-support coupling | conditional hypothesis     |
| Learned point process        |          理论可支持 |                          原生 |                         可保留 |                                     可选 | deferred                   |

“可表达”不等于“已学习”。当前 runtime只证明接口与概率正确性。

### 7.2 Retain

* schema-3 event runtime；
* typed membership transaction；
* survivor/rejoin continuity；
* active-only sum/count reference；
* uniform external event order；
* exact F0/F1 selector；
* per-owner (\gamma^\Delta) credit；
* (\pi_l(a_i\mid o_i,z_i))；
* task-blind intrinsic boundary；
* terminal external task objective。

### 7.3 Delete or keep retired

* R51–R54 exact tasks、comparators和threshold contracts；
* R55编号路线和未执行 substrate；
* `SHORT_A/SHORT_B` type-specific draft；
* fixed-(N) specialists作为 universal prerequisite；
* identity或hard roles；
* graph、attention、slot、critical residual；
* team latent、bridge和新 discriminator；
* learned ordering；
* learned event time；
* task-specific intrinsic或reward shaping。

R51–R54 的 retirement boundaries已经明确禁止通过改预算、阈值、模型或seed恢复。

### 7.4 Add，且仅在未来另行授权后

* 一个 generic-short dynamic-roster environment/adapter；
* 一个小型 direct primitive-AR access instrument；
* event-mode真实 training integration；
* 一个统一 analyzer，覆盖 access、skill execution、prefix direction和timing。

它们是 testbed evidence boundary，不进入 F1 模块图。

### 7.5 Stop rule

任一失败不得自动产生 successor：

* carrier/direct失败：退休该 testbed；
* H2：停止并记录 skill bottleneck；
* H0：停止在F0；
* H3：只做架构解释；
* H1：只支持本 testbed，等待独立 integration disposition；
* mixed：停止，不重新设计 toy。

---

## 8. Authorization

# 文档迁移：`AUTHORIZED_AFTER_CORRECTION`

允许将上述修正版冻结为：

```text
docs/research/designs/
F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md
```

文档必须包含：

* generic `SHORT`；
* exact roster/task/reward state machine；
* direct → F0/F1 串行顺序；
* 320K/PPO4 exposure；
* exact metrics、branches和RNG ledger；
* no-rescue replacement ledger。

# Environment implementation：`NOT_AUTHORIZED`

# Event training integration：`NOT_AUTHORIZED`

# Any experiment launch：`NOT_AUTHORIZED`

# F1 promotion or UAV integration：`NOT_AUTHORIZED`

本轮入口明确规定，无论 verdict为何，都不能授权实现、训练或promotion。
