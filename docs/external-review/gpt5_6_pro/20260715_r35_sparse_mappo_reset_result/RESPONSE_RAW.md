1. TMPF INVALIDITY ACCEPTED

接受纠偏。

R35-TMPF 不具备可执行的 skill-formation contract，因此不能进入实现或 gate。

决定性缺陷：

TMPF 的形成目标是：

L_wm(theta) = -log p_theta(o_{t+1:t+W} | o_{t:t+W-1}, a_{t:t+W-1}, u)

但同时规定：

world model 不更新 policy；

policy 只由 sparse environment PPO 更新。

对于 detached 数据：

(o, a, u, o')

有：

grad_{theta_actor} L_wm = 0

grad_{u_policy} L_wm = 0

因此该 loss 只能训练：

p_theta

不能形成：

actor FiLM(u)；

latent generator；

executable motor manifold。

如果允许 action gradient 穿过 world model，则已经变成另一个 model-based actor optimization，需要新的：

policy objective；

model bias 分析；

on-policy contract；

而 TMPF 没有定义这些。

此外：

SET(z)

的冻结 R30 controller 不能直接产生：

u in R^d

随机扰动 latent 也只是外部 scheduler，不是 learned temporal abstraction。

因此：

TMPF INVALIDITY ACCEPTED

2. TMPF 及当前 skill-formation program 处置

永久关闭当前 unsupervised skill-formation program

最终处置：

R35-OCSF: RETIRED

R35-CBF: RETIRED

R35-TMPF: INVALID

不再提出：

新 latent；

新 classifier；

新 effect objective；

新 clustering；

新 skill slot。

因为这已经不是“哪个 skill objective 更好”的问题，而是：

当前架构没有证明 discrete/continuous latent skill object 是必要且可形成的研究对象。

R29-R34 已关闭：

action separation；

observational effect；

direct individual effect；

roster composition；

post-hoc mode reconstruction。

失败矩阵总结：

R29：action separation 不等于稳定 skill effect；

R31：effect association 不等于 causal persistence；

R32：individual effect gradient 不形成 codebook；

R33：selector 不创造 interaction primitive；

R34：trajectory relabel + cloning 不增强 source skill。

R34 已进一步证明：

real > sham；

但 source anchor 失败；

imitation 只修复 attribution，而没有创造更强 skill。

3. 唯一非 skill replacement direction

选择：

Sparse MAPPO Reset Baseline

这是一个 baseline/reset 方向，不是新的论文贡献。

目标：

回答：

HA-CTSE 的收益是否来自 skill abstraction，还是来自普通 cooperative MARL 优化？

算法定义

移除：

z_i

恢复：

pi(a_i | o_i)

低层：

o_i -> MLP -> RNN -> pi(a_i)

保留：

recurrent actor；

centralized critic；

PPO/MAPPO；

GAE。

Policy objective

只使用：

r_t = r_t_env

PPO：

L_pi = -E[min(rho_t A_t, clip(rho_t, 1-epsilon, 1+epsilon) A_t)]

其中：

rho_t = pi_theta(a_t | o_t) / pi_old(a_t | o_t)

critic：

L_V = (V_theta(s_t) - R_t)^2

entropy：

普通 action entropy。

禁止：

intrinsic reward；

skill reward；

latent；

q_d/q_D；

trajectory scorer；

team latent；

roster scorer；

scheduler contribution。

4. R30 KEEP/SET 处置

RETIRE

R30 KEEP/SET 不进入新 baseline。

原因：

KEEP/SET 的前提：

z_i

已经是有效 temporal object。

当前证据不足。

因此：

fixed clock 作为实验环境信息保留；

skill lifetime hypothesis 暂停；

KEEP/SET 只作为历史 comparator；

不作为新算法组件。

5. Sparse MAPPO gate

目的

不是证明 MAPPO 更强。

只判断：

在当前 benchmark 中，skill abstraction 是否提供超过普通 recurrent MARL 的必要价值。

初始化

两个 arm 从同一 source：

checkpoint:

adaptive-R30 frozen source

seed:

36031

Arms

Arm A

Sparse MAPPO Reset：

无 skill；

无 KEEP/SET；

无 high controller。

Arm B

Frozen R30 reference：

保持：

low skill actor；

KEEP/SET；

fixed clock。

但：

不更新；

不加入 intrinsic reward。

训练预算

完全一致：

envs:

16

rollout length:

500

PPO updates:

40

PPO epochs:

15

minibatch:

32

optimizer:

Adam

learning rate:

3e-4

每 arm：

16 x 500 x 40

environment transitions。

Evaluation：

64 deterministic episodes

M0 Validity

必须满足：

Environment

相同环境版本；

相同 seed stream；

相同 episode budget。

Optimization

相同 PPO updates；

相同 epochs；

相同 minibatch exposure；

相同 network parameter count。

Input

MAPPO：

Actor:

o_i

Critic:

s

R30:

原 frozen input。

禁止：

skill；

latent；

OPT compact；

team context。

失败：

INVALID

只修实现。

Metrics

1. Sparse reward

要求：

R_MAPPO >= 0.9 R_R30

2. Task completion

cycle completion：

Completion_MAPPO >= 0.9 Completion_R30

3. Joint coverage

固定：

625 joint-position cells。

要求：

Coverage_MAPPO >= Coverage_R30 - 5%

4. Stability

zero-service fraction：

恶化：

<= 0.10

Bootstrap:

unit：episode；

10000 repetitions。

Result branches

PASS

如果：

Sparse MAPPO 达到或超过 R30。

结论：

当前 HA-CTSE skill abstraction 没有证明提供额外价值。

下一步研究：

credit assignment；

temporal coordination；

centralized/decentralized optimization。

不是继续 skill discovery。

FAIL

如果：

Sparse MAPPO 显著低于 R30。

结论：

skill abstraction 可能有价值。

但不能恢复：

R29；

R31；

R32；

R33；

R34。

需要重新定义 skill object。

CRASH

只修：

implementation；

environment；

training wiring。

不改变算法。

6. 支持与禁止结论

该 gate 可以支持

如果 PASS：

skill abstraction not necessary

即：

当前 benchmark 的收益主要来自普通 MARL 优化，而不是 skill mechanism。

如果 FAIL：

当前 benchmark 仍显示 temporal abstraction 的必要性，但已有 skill formation 路线未被证明。

不支持

即使 Sparse MAPPO 失败，也不能声称：

HMASD skill 已成功；

R30 KEEP/SET 已证明有效；

sparse exploration 已解决；

cooperation 已恢复；

S7 transfer 已成立。

最终裁决

R35 skill-object search CLOSED

唯一下一步：Sparse MAPPO Reset Baseline

研究问题从：

如何创造 skill

转变为：

HA-CTSE 的真正贡献是否来自 skill，还是来自普通 MARL 优化结构？
