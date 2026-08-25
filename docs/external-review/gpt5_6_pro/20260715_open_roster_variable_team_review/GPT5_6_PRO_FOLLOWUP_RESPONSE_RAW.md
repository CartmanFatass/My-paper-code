# 裁决

[
\boxed{\texttt{ACCEPT DISPOSITION}}
]

但需要精确限定：

> fixed-(N) native-HMASD toy anchor 不是编写 set encoder 的软件前置条件，却是当前证据链中不可跳过的**因果前置条件**。

现在直接实现 Set-R30 或 open-roster，会把尚未闭合的 joint-credit 问题与 roster representation、padding mask、active-agent decoding 和 membership semantics 混在一起。无论结果成功或失败，都无法归因。

当前唯一下一条路线应当是：

[
\boxed{
\text{固定 }N=2\text{、固定 primitive、native-HMASD 概率/credit 路径}
\rightarrow
\text{从采样外部回报学会正确 joint roster}
}
]

不是 Set-R30，不是 S7，不是 intrinsic reward，也不是另一条 standalone scorer 路线。

---

# 1. 为什么 fixed-(N) native anchor 是必要的

## 1.1 当前已经关闭的解释

R39 toy 的连续诊断已经关闭了以下解释：

* learned low-level primitive 不够强；
* compressed context 丢失关键信息；
* high actor 没有梯度；
* GAE 与 immediate block-return 梯度方向冲突；
* 单个 high PPO epoch 暴露不足；
* SMDP-GAE actor weight 本身选错；
* tiny autoregressive policy 无法表达正确 joint roster；
* reward 被放错时钟或错误地存入 high row。

其中最强的两条证据是：

1. 相同 high-32 policy 在八个注册 context 上，经过 exact joint-roster likelihood 优化后，最差正确 unordered-roster probability mass 达到 `0.999487`；
2. 自然采样中，正确 roster 的 raw block return 为 `4.900994`，错误 roster 为 `1.816988`；标准化 actor weight 分别为 `+2.120720` 和 `-0.192793`。

所以已有证据支持：

[
\boxed{
\text{joint policy 可表达正确解}
\quad\land\quad
\text{正确 joint action 获得方向正确的外部 credit}
}
]

但仍然没有支持：

[
\boxed{
\text{当前 on-policy factor-level learner 能稳定利用该 credit}
}
]

这正是 `CURRENT_WORK.md` 当前将剩余边界定位为 “standalone shared joint credit”的原因。

---

## 1.2 exact factorization PASS 不能替代 on-policy credit anchor

exact diagnostic 优化的是：

[
L_{\mathrm{sup}}
================

-\log
\sum_{\mathbf z\in C(x)}
\exp
\left[
\sum_i
\log\pi_\theta
\left(
z_i\mid x,z_{<i}
\right)
\right],
]

其中 (C(x)) 是由 oracle target signs 确定的两个正确 unordered orientations。

实现中确实先将所有 token log-probability 相加形成完整 roster log-probability，再最大化两个正确 roster 的总 probability mass。Oracle labels 被明确限制为 diagnostic-only，不进入环境训练。

这证明的是：

[
\text{representation/factorization capacity}.
]

它没有测试：

* sampled-action variance；
* critic baseline；
* PPO clipping；
* high GAE；
* 一个错误 joint roster 中哪些 token 应被惩罚；
* 共享 non-additive return 如何分解给 autoregressive factors。

因此不能因为 exact supervised objective 成功，就跳过 sampled-credit positive anchor。

---

## 1.3 当前 standalone learner 与 native learner 的实际差异

当前 standalone R30 对每个 high decision 使用同一个 scalar advantage：

[
A_{\tau,1}
==========

# A_{\tau,2}

A_\tau,
]

然后为每个 token 单独形成 PPO ratio：

[
\rho_{\tau,i}
=============

\exp
\left(
\log\pi_{\theta,i}
------------------

\log\pi_{\mathrm{old},i}
\right),
]

并优化：

[
L_{\mathrm{standalone}}
=======================

-\frac{1}{N}
\sum_i
\min
\left(
\rho_{\tau,i}A_\tau,
\operatorname{clip}(\rho_{\tau,i})A_\tau
\right).
]

代码中同一个 `actor_adv_np[local_idx]` 被复制到该 joint decision 的全部 token，随后逐 token 计算 ratio、clip 和平均 loss。

这个目标在 on-policy 点的一阶梯度未必方向错误；但在当前 non-additive roster reward 下，它缺少 factor-specific baseline。一个 joint roster 错误时，即便其中一个 token 本身选对，两个 token 仍获得同一个负权重。当前只有 `32` 条正确样本、`352` 条错误样本，因而 credit variance 和错误归责完全可能压倒正确的平均方向。

native HMASD 路径则已经实现：

[
\pi_H(Z,\mathbf z\mid x)
========================

\pi_Z(Z\mid x)
\prod_i
\pi_i(z_i\mid x,Z,z_{<i}),
]

PPO replay 时 teacher-force 存储的 (Z) 和全部 (z_{<i})，不会重新采样 conditioning chain。

它还分别使用：

[
A_Z,\qquad A_{z_1},\ldots,A_{z_N},
]

和对应的：

[
V_Z,\qquad V_{z_1},\ldots,V_{z_N},
]

形成独立的 team ratio loss 与 agent ratio loss，而不是把一个 scalar joint advantage 无差别复制给所有 token。

因此 native toy anchor 测试的是一个当前尚未验证、但仓库里已经存在的 credit package：

[
\boxed{
\text{teacher-forced native conditional likelihood}
+
\text{native team/agent advantages and value baselines}
}
]

这比现在增加 set representation 更直接地命中剩余因果边。

---

# 2. 可复用的因果结论

当前 R39 证据支持以下结论：

[
\boxed{
\begin{aligned}
&\text{joint policy 可表达正确 roster}\
&+\text{正确 roster 获得更高且符号正确的外部 credit}\
&\not\Rightarrow
\text{shared-token on-policy learner 能形成正确 joint policy}.
\end{aligned}
}
]

更一般地说：

> 对具有 non-additive team outcome 的 autoregressive MARL，模型容量、奖励方向和 replay 正确性只能关闭 representation/data defects；在改变 team representation 前，还必须建立一个能够把 team outcome 转化为 factor-level learning 的正 credit anchor。

因此：

[
\boxed{
\text{variable team representation}
\text{ 不是当前 joint-credit failure 的修复}
}
]

open-roster 是独立的架构泛化轴，而不是绕过当前 credit failure 的捷径。

---

# 3. 唯一立即因果边

[
\boxed{
\begin{aligned}
&\text{native SkillCoordinator 的存储前缀联合概率}\
&+\text{native team/agent high advantages}\
&\rightarrow
\text{从 sampled external reward 学会正确 unordered roster}\
&\rightarrow
\text{建立 fixed-}N\text{ positive credit anchor}.
\end{aligned}
}
]

允许的结论只有：

> 在固定两智能体、固定 primitive 的已闭合 toy 上，当前 native HMASD coordinator probability-and-credit path 能否通过正常 on-policy 训练获得可靠 dense access。

它不测试：

* skill discovery；
* intrinsic reward；
* variable lifetime；
* KEEP/SET 优势；
* dynamic team；
* membership censoring；
* S7；
* HMASD parity。

---

# 4. 最小实现边界

## 4.1 保留的对象

直接复用现有：

* `two_timescale_role_free_actions` toy；
* 两个 agent；
* constant identical local observations；
* centralized slow/fast target direction 与 clock；
* 四个 fixed axis primitives；
* swap-invariant dense external reward；
* 当前 native `SkillCoordinator`；
* native rollout buffer；
* native team/agent value heads、advantages 和 PPO update；
* current high replay likelihood audit。

现有 native coordinator 已经能够：

1. 先采样原生 team skill (Z)；
2. 按顺序采样 (z_i)；
3. 保存 team 与 agent log-probability；
4. replay 时 teacher-force 原始 (Z,z_{<i})；
5. 输出独立 team value 和 agent values。

本轮只能复用这一已有 (Z) 因子；不得增加第二个 team latent。其 cardinality 必须在实验注册时一次固定，不能 sweep。`q_D`、`q_d`、discriminator reward 和所有其他 intrinsic 路径全部关闭。

## 4.2 最小代码变化

只需要一条 native toy entry：

1. 为 native HMASD trainer 接入现有两智能体 toy；
2. 增加 fixed-skill-to-axis-action execution hook；
3. 禁止 low policy 参数、low optimizer、low critic 或 recurrent discoverer更新；
4. 增加现有 match/slow/fast evaluator；
5. 在同一 runner 中记录 M0 replay、update 和 reward purity；
6. 输出一个结论 JSON。

不修改：

* `r30_fixed_clock.py`；
* set encoder；
* high/low critic architecture；
* environment reward；
* native team/agent advantage公式；
* agent order；
* open-roster buffer；
* membership semantics。

也不创建额外 capacity audit。现有 exact factorization 和 alignment gates已经完成了 capacity/data diagnosis；本次训练运行本身就是实现检查和证据运行。

---

# 5. 最小 evidence-bearing toy run

应复用已经冻结的 R39 toy 曝光，而不是重新选择预算：

```text
agents                 2
episode length         40
global check k0        5
parallel environments  16
rollout length         40
environment steps      12,800
outer updates          20
high PPO epochs        3
training seed          39041
final stochastic eval  32 episodes
high hidden            32
low trainable params   0
intrinsic reward       0
```

这些值与当前固定-primitive、高三 epoch R39 toy 证据保持一致；现有访问门槛也是：

[
\text{match}\ge0.70,
]

[
\text{slow match}\ge0.65,
]

[
\text{fast match}\ge0.65.
]

此前同一 toy 的 fixed-primitives 和 block-credit arms 都没有达到这些门槛，因此这一运行是 source-anchor gate，不是一个宣称 native 优于 standalone 的严格 paired efficacy comparison。

---

# 6. 必须冻结的六类合同

## 6.1 Probability contract

联合策略保持：

[
\pi_H(Z,z_1,z_2\mid x)
======================

\pi_Z(Z\mid x)
\pi_1(z_1\mid x,Z)
\pi_2(z_2\mid x,Z,z_1).
]

要求：

* sampling 与 replay 使用相同 canonical agent order；
* order 存入 rollout，不能重新排序；
* PPO replay 强制使用存储的 (Z,z_1,z_2)；
* coordinator dropout 为 0；
* 不消费 RNG 重新采样 prefix；
* team 与 agent replay max absolute error 均：

[
\le10^{-6};
]

* categorical action sampling 保持 stochastic；
* 不使用 learned agent order；
* 不增加新的 sampled team latent。

仓库已有 replay audit 会保存 RNG 状态、teacher-force 存储动作，并在 strict contract 下对大于 (10^{-6}) 的误差 fail closed。

## 6.2 Time contract

* 只在固定 (k_0=5) 边界采样一次完整 high action；
* 每次 check 都 full refresh；
* 当前没有 KEEP；
* 当前没有 variable lifetime；
* 一个 high action 只接收其后五个 primitive steps 的 discounted external block reward；
* episode 结束后不 bootstrap；
* rollout/update truncation按现有 native buffer语义处理；
* 不因 slow target 或 fast target变化额外触发 high action。

因此这一 gate 只测试 fixed-(k) credit，不含 temporal-treatment claim。

## 6.3 Information contract

低层执行器只读取：

[
z_i\rightarrow\text{fixed primitive action}.
]

它不读取：

* slow/fast target；
* clock；
* correct skill label；
* role；
* agent identity；
* reward；
* success predicate。

high coordinator可以读取现有 generic centralized state：

* slow action target direction；
* fast action target direction；
  -各自 clock。

但不得读取：

* “当前正确 roster”；
* unordered-pair label；
* match indicator；
  -未来 target；
* oracle role assignment。

correct-roster classification只允许出现在 evaluator/analyzer 中，不能影响 reward、advantage、gradient、采样或 checkpoint selection。

## 6.4 Credit contract

唯一训练 reward 是现有 dense external task reward：

[
r_t=r_t^{env}.
]

关闭：

[
q_D,\quad q_d,\quad
r^{int},\quad
\text{task shaping},\quad
\text{block-label bonus}.
]

high learner必须原样使用 native：

* team GAE/return；
* agent GAE/returns；
* team value；
* agent values；
* team ratio；
* agent ratios；
  -统一 advantage normalization。

不能恢复 standalone 的 shared scalar token credit，也不能将 diagnostic block return 变成新算法。

## 6.5 Recurrent-state contract

这个 positive-control toy 中：

* fixed primitive executor没有 trainable low recurrent state；
* low hidden 不参与 credit；
* low optimizer step 数严格为 0；
* high `SkillCoordinator` 本身是 Transformer，不跨 high decision 保存 recurrent hidden；
* episode reset 清除环境与 rollout 状态；
* 不存在 agent join、leave、rejoin 或 membership epoch。

这确保失败不能再归因于 low recurrent execution。

## 6.6 Checkpoint contract

* 从 fresh neutral initialization 开始；
* 禁止加载 exact-factorization supervised checkpoint；
* 禁止加载 standalone R39 toy checkpoint；
* 禁止加载历史 S7/HMASD checkpoint；
* 保存 exact final checkpoint，不选 best checkpoint；
* checkpoint包含 coordinator、optimizer、ValueNorm/normalizer、config、update/step metadata；
* final evaluation只能读取 exact final checkpoint；
* 不允许 post-result append。

---

# 7. Exogenous membership 与 policy-selected membership

本轮 fixed-(N) anchor 没有 membership action。

后续 open-roster gate 中，第一版 membership 必须是**外生的**：

[
A_\tau
======

f_{\mathrm{env}}(\text{registered reset/failure process}),
]

它是环境给定的 active mask：

* 不含 policy log-probability；
* 不获得 advantage；
* 不因加入、离开或存活获得 reward；
* 必须与 active set、external order、prefix 一起存储和 replay。

若未来由策略决定是否接纳、部署或移除一个成员，则它是新的 high-level action：

[
m_\tau\sim\pi_m(m\mid x_\tau),
]

必须另行定义：

* action support；
* log-probability；
* clock；
  -资源约束；
* SMDP return；
* critic；
* comparator。

不能把 policy-selected admission伪装成 environment mask。现有 disposition 对这一区分是正确的。

---

# 8. 对两份 raw responses 的处置

| 处置     | 内容                                                                                                                                                                                                                                                                                                             |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **接受** | 区分 cross-episode variable (N)、temporary availability 与真实 join/leave；membership transition 不应自动刷新 surviving agents 的技能；joiner initial SET；leaver `membership_censored`；survivors 保持 hidden/skill/age；active-only AR；存储 active set、membership epoch、external order 和实际 prefix；禁止 team-size/join/survival reward。 |
| **修改** | set representation 后续先采用 padded、mask-aware 的最小集合表示；permutation、padding 和 replay invariance应作为 evidence-bearing run 的 M0，而不是单独建立长期 Gate-0 audit工作流。                                                                                                                                                             |
| **推迟** | ISAB、sparse graph、固定 inducing count、`M=8`、low-critic rewrite、hypernetwork、跨 episode (N) 训练集、within-episode censoring、learned admission、S7 failure machinery，以及 “Membership-Aware Asynchronous Skill SMDP” 的 novelty claim。                                                                                     |
| **拒绝** | 立即用 `R39-OR0` 替代当前 credit anchor；立即进入 S7；把 variable (N) 当成当前 shared-credit failure 的修复；learned agent order；任何 membership intrinsic；以及 raw response 中未经注册的 2% parameter tolerance、0.85 reward ratio、({4,6,8})/({5,7}) team-size sets 和其他数值门槛。                                                                   |

两份 raw responses 对长期架构方向的核心判断是有价值的，但它们基于较早的 `ffa18c3` 状态，尚未看到随后形成的 exact factorization 与 joint-credit alignment 证据。现有 disposition 正确地保留了它们的长期贡献，同时拒绝其 immediate route。

---

# 9. PASS / INVALID / abandonment 分支

## `INVALID_R39_NATIVE_TOY_CREDIT`

触发条件：任一 M0 失败，例如：

* replay error (>10^{-6})；
* prefix 未 teacher-force；
* dropout 非零；
* low parameters或optimizer被更新；
* intrinsic/discriminator path非零；
  -不是 exact 12.8K/20-update/three-epoch contract；
  -标签进入训练；
  -checkpoint/evaluation不一致。

唯一下一动作：

> 修复所定位的具体 wiring defect，并原样重复同一合同。

不能修改模型大小、seed、预算、阈值或 reward。

---

## `PASS_R39_NATIVE_TOY_CREDIT_ANCHOR`

要求 M0 全部通过，并同时满足：

[
\text{match}\ge0.70,\qquad
\text{slow}\ge0.65,\qquad
\text{fast}\ge0.65.
]

允许结论：

> native HMASD probability-and-credit path在固定 (N)、固定 primitive toy 上提供了正 joint-credit anchor。

唯一下一动作：

> 在同一 native toy 上注册一个 exogenous active-mask、padded mask-aware set-roster arm，并保持同一 external reward、native credit和 full-refresh时钟；该运行同时检查 permutation、padding和 replay invariance。

不能跳到跨-(N)、membership censoring、KEEP/SET efficacy或S7。

---

## 唯一 abandonment branch：`VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`

触发条件：

* M0 有效；
* 任一 access floor失败。

可复用结论：

> 即使使用原生 teacher-forced coordinator likelihood 和原生 team/agent credit，当前 toy仍没有提供可学习的 fixed-(N) joint-credit anchor。

此时永久停止：

* 在该 toy 上实现 set/open-roster；
* 继续修改 standalone shared credit；
  -增加 epoch、seed、budget或model size；
  -降低 access threshold；
  -进入 S7；
  -引入 intrinsic、(q_D)、counterfactual oracle或reward shaping。

唯一下一动作：

> 关闭 R39 toy-credit路线并完成一次固定-(N) joint-credit failure review；在新的正 credit substrate被正式选择前，不再进行 open-roster核心实现。

不存在 `MIXED`、`UNDERPOWERED` 或自动扩展分支。

---

# 10. 结果工件说明

我核对了实现与注册结果来源，但没有虚构不存在的 JSON：

* joint-factorization脚本明确生成带有 `status`、M0、M1、parameter count和correct-mass字段的 JSON；
* 该 runtime JSON 没有被跟踪在指定 Git commit 中；
* 最新 joint-credit-alignment gate在 `ExpRecord` 中明确把三行 `train_updates.csv` 定义为结果来源，而不是 result JSON；注册数值已逐项记录为 `32/352`、`4.900994/1.816988` 和 `+2.120720/-0.192793`。

这不改变本轮判断，但后续归档 native toy gate时，建议让唯一 decision source成为被保存的：

```text
result/r39_native_hmasd_toy_credit.json
```

---

# 最终决定

[
\boxed{
\begin{aligned}
&\texttt{ACCEPT DISPOSITION}\
&\text{fixed-}N\text{ native toy credit anchor 必须先完成}\
&\text{唯一当前边：native likelihood/credit }\rightarrow
\text{ sampled joint-roster learning}\
&\text{PASS 后才允许同 toy 的 exogenous active-mask/set-roster}\
&\text{有效 FAIL 即永久停止该 substrate 上的 open-roster 推进。}
\end{aligned}
}
]
