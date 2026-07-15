# Verdict

`MODIFY_R41B_TEMPORAL_GATE`

R41B source anchor 接受，但两个先前 temporal gate 都不能直接执行。

需要修改为第三个、最小的 HMASD-native temporal intervention：

```text
keep original k0=50
+ preserve native HMASD team assignment
+ introduce per-agent renewal semantics only at existing checks
```

原因：

R41B 已经建立当前唯一有效 positive anchor：

```text
original HMASD source can solve Alice–Bob
```

但 temporal intervention 必须避免同时改变：

- check frequency；
- team credit；
- high policy factorization；
- discriminator semantics；
- action support。

# 1. R41B validity audit

`PASS_R41B_SOURCE_ACCESS` 成立。

R41B 使用：

- fresh original HMASD source；
- seed 1；
- 32 rollout environments；
- 937 outer updates；
- 2,998,400 environment transitions；
- k=50；
- n_Z=2；
- n_z=4。

实现：

- high replay error = 0；
- low replay error = 0；
- global replay error = 0；
- 五条 optimizer path 均完成 14,055 finite nonzero updates。

最终：

```text
win_zero=0
win_final=0.89
key0=0.97
key1=0.92
```

paired bootstrap：

```text
Delta=0.89
95% CI=[0.82975,0.95]
```

因此：

```text
R41B=VALID_POSITIVE_ANCHOR
```

# 2. 为什么不能接受旧 temporal gate

当前有两个冲突设计。

## Gate A

来源：R39 compatibility。

特点：

- k0=10；
- team Z 每次 check renewal；
- 320K continuation。

问题：当前 positive source k0=50，改成 10 会同时改变：

- high decision frequency；
- high buffer row density；
- optimizer exposure；
- team latent renewal。

因此不是单一 temporal intervention。

## Gate B

来源：R40/R41。

保持 k0=50，但：

```text
incumbent draw = KEEP
other draw = SET
```

问题：这不是原 HMASD categorical assignment 的自然扩展。它重新解释 K
个 skill sample，会改变 q_d(z_i | o_i, Z) 语义。

# 3. 唯一路线：R42 Native Per-Agent Renewal Gate

核心 intervention 保持 k0=50。

原因：这是唯一不改变 source temporal credit scale 的选择。

改变不是增加 KEEP head，不是增加 duration，不是改变 Z，而是：在已有
full refresh decision point，允许 `z_i_new=z_i_old` 表示 KEEP。

# 4. Team Z semantics

选择：

```text
Z held until next full team refresh
```

不每个 partial check 更新。

原因：原 HMASD

```text
pi(Z|x) prod_i pi(z_i | Z,z_<i,x)
```

中 Z 是团队条件变量。如果 partial KEEP 时刷新 Z，会导致
`q_d(z_i | o_i,Z)` 条件语义漂移。

因此 R42：full refresh event 重新采样 Z；partial checks 保持
`Z_t=Z_last_full`。这保留 team discriminator、team value、individual
discriminator。

# 5. Exact categorical probability

Original HMASD：

```text
pi_H(Z|x)
pi_i(z_i | x,Z,z_<i)
```

R42 partial check 对 agent i 的 candidate support：

```text
A_i={KEEP} union {1,...,K}
```

不新增 distribution，直接使用原 `pi_i(z_i | x,Z,z_<i)` 映射：incumbent
skill `z_i_old` 对应 KEEP；其他 `z != z_i_old` 对应 SET(z)。

# 6. Replay contract

行为概率：

```text
logp=log pi_H(Z|x)+sum_i log pi_i(tilde_z_i | x,Z,tilde_z_<i)
```

采样固定 agent order `sigma=(0,1,...,N-1)`。

Replay teacher forcing 存储 Z、z1,...,zN、action order、old log probs；重新
计算必须使用 same stored sequence，禁止重新 sample。

# 7. Warm start / compatibility

Fixed control arm C 调用原 HMASD full refresh path，即每 50 steps 执行：

```text
pi_H(Z|x) pi_i(z_i | x,Z,z_<i)
```

Treatment arm T 初始完全复制 SkillCoordinator、low actor、low critic、q_D、
q_d、normalizers、optimizer states。

新增逻辑只在 action selection wrapper 加入 incumbent mask。

禁止新 KEEP Bernoulli、新 duration、新 critic、新 latent。

# 8. Credit and clocks

Check clock 固定 k0=50。

Age：

```text
KEEP: age_i <- age_i+50
SET:  age_i <- 0
```

High return 保持 external reward only。Block：

```text
R_t^H=sum_{r=0}^{49} gamma^r r_{t+r}^env
```

Advantage 保持 native HMASD team value、agent value、GAE。

Low recurrent state：KEEP 时 hidden state continuity；SET 时 skill embedding
更新，RNN hidden 不清零。原因是 skill switch 不是 episode reset。

Episode reset 完全继承 HMASD：hidden reset、age reset、Z reset。

Rollout boundary 保持 native buffer，不跨 rollout 人工拼接。

# 9. Smallest abandonment gate

## R42-AliceBob-local

目的：只判断 renewal semantics 是否破坏 source ability。

Arms：

- Arm A — Fixed HMASD control：k0=50 full refresh。
- Arm B — R42 per-agent renewal：k0=50 KEEP/SET。

Initialization：同一个 R41B positive checkpoint。

Training per arm：

```text
Seed=1
Environments=16
Steps=320000
Outer updates=100
```

Optimizer 完全一致：high、low、q_D、q_d。

Evaluation：deterministic 100 reset streams。

## M0 Compatibility

必须：fixed mode reproduces original assignment；low actor unchanged；q_D/q_d
unchanged；reward unchanged；replay error `<1e-6`。

失败：`INVALID_R42_IMPLEMENTATION`。动作：修 compatibility。

## M1 Service preservation

要求 R42 final win rate `>=0.80*fixed`，且 paired difference CI lower `>-0.10`。

## M2 Lifetime decoupling

R42 treatment 必须：skill renewal correlation `corr(T_i,T_j)<0.9`，并至少两个
agent 满足 `P(T_i != T_j)>0.2`。

## 分支

`PASS_R42_TEMPORAL_DECOUPLING`：M0-M2 全通过。下一动作：进入 multi-seed
AliceBob，然后才 S7 temporal transfer。

`VALID_FAIL_R42_SERVICE`：M0通过、M1失败。结论：当前 renewal semantics
损害 HMASD service。动作：退休 KEEP/SET temporal formulation。

`VALID_FAIL_R42_NO_DECOUPLING`：M0/M1通过、M2失败。结论：保持性能但没有
产生真实 lifetime decoupling。动作：保留 fixed HMASD，不宣称 temporal
contribution。

# Final answer

Verdict token：`MODIFY_R41B_TEMPORAL_GATE`

Reusable causal conclusion：

```text
R41B proves the HMASD source substrate is valid. The remaining question is not
access, but whether individual renewal semantics can be introduced without
changing HMASD credit.
```

Single next experiment：

```text
R42: k0=50 native HMASD fixed refresh vs per-agent KEEP/SET
```

Minimal abandonment gate：

```text
If service preservation fails or lifetime does not decouple, retire the
temporal formulation.
```

Prohibited：

- k0=10；
- independent KEEP Bernoulli；
- duration head；
- variable N；
- open roster；
- intrinsic reward；
- reward shaping；
- q_D/q_d modification；
- new latent；
- R29-R40 route resurrection。

来源
