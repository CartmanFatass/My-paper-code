# Verdict

`ACCEPT_R42_NATIVE_CATEGORICAL_RENEWAL_K50`

R42 路线保留，但必须按照 native HMASD categorical renewal 修正。

核心结论：上一轮 R42 的方向正确：

```text
k0=50 + same HMASD source checkpoint + only renewal semantics change
```

但需要关闭两个实现歧义：

- team Z 生命周期不能同时“保持”和“每 check 重采样”；
- KEEP/SET 必须严格是原始 categorical z_i sample 的重新解释，而不是新增
  action head。

# 1. R41B 正向 anchor 保留

R41B 已建立唯一有效 source anchor。

结果：原始 HMASD source；Alice-Bob；k0=50；n_Z=2；n_z=4。

最终：

```text
win_final=0.89
key0=0.97
key1=0.92
paired improvement=0.89
95% CI=[0.82975,0.95]
```

因此 R42 可以从该 checkpoint 做 temporal intervention。

# 2. 单一 causal edge

R42 只测试：

```text
shared synchronous skill renewal -> per-agent renewal semantics
```

不测试 skill discovery、intrinsic、better reward、variable team、open roster。

Claim boundary：如果通过，只能证明在原 HMASD 的 k0=50 网格上，individual
renewal 不破坏性能并产生局部异步更新。不能宣称任意 skill duration、
continuous scheduling、UAV transfer、variable-N。

# 3. Team Z contract

选择：Z 每次原始 k0=50 check 都重新采样。不选择 held-Z。

原因：原 HMASD 的 `pi_H(Z|x)` 是 high action。如果 partial check 保留旧 Z，
却不产生 `log pi_H(Z|x)`，会改变 team credit、high buffer、value target。
因此保持 native source contract。

Alice-Bob episode example (`H=100`)：

- t=0：采样 Z0，并采样 z0_1,z0_2；
- t=50：重新采样 Z50，然后 z50_i 通过 renewal mapping。

Team clock unchanged，仍为 50-step。

# 4. Exact action support

原始 K=4 categorical skill sample `z_i in {0,1,2,3}`。

R42 event support：

```text
{KEEP} union {SET(z): z != z_i_old}
```

大小仍为 K，不是 K+1。

Mapping：incumbent `z_i_old` 对应 KEEP；其他 `z != z_i_old` 对应 SET(z)。

因此 R42 与被拒绝 Gate B 不同。区别：Gate B 人为把 KEEP 作为新独立
categorical class；R42 只是 same q_d 在 incumbent-relative semantics 下解释。

# 5. Probability and replay contract

Team probability：

```text
p(Z)=pi_H(Z|x)
```

Individual probability，agent order `sigma=(1,2,...,N)`：

```text
p(z_i)=q_d(z_i | o_i,Z,z_<i)
```

Joint event probability：

```text
logp=log pi_H(Z|x)+sum_i log q_d(z_i | o_i,Z,z_<i)
```

Buffer 保存 Z、z1,...,zN、pre-edit roster、post-edit roster、old log
probabilities、values、hidden states。

PPO replay teacher forcing 重新计算
`log pi_theta(Z,z1,...,zN|x)`，使用 stored sequence，禁止重新 sampling。

# 6. No new parameters

R42 新增 0 parameters。禁止 KEEP head、Bernoulli switch、duration head、new
critic、new latent。

# 7. Clock and credit contract

Check clock 固定 k0=50。

Age：

```text
KEEP: age_i <- age_i+50
SET:  age_i <- 0
```

Reward 保持 `r_t=r_t_env`，无 lifetime reward、switch reward、intrinsic。

High block return：

```text
R_t^H=sum_{r=0}^{49} gamma^r r_{t+r}^env
```

Advantage 保持 native team value、agent value、GAE。

Hidden state：KEEP 时 h_i 连续；SET 只改变 skill embedding，不 reset recurrent
hidden。

Episode reset：reset Z、skill、hidden state、buffers。

# 8. Checkpoint migration

两 arm 从同一个 R41B final checkpoint 恢复：SkillCoordinator、low actor、low
critic、q_D、q_d、optimizer states、value normalizer、observation normalizer。

Fixed arm 使用 exact original path：

```text
pi_H(Z|x) q_d(z_i | o_i,Z,z_<i)
```

R42 arm 唯一变化为 categorical sample interpretation。

# 9. Budget

选择：

```text
32 envs x 100 rollout x 100 updates
```

理由：保持 R41B source batch compatibility。总计 320,000 steps。

每 arm：32 environments，rollout 100，outer updates 100，PPO 保持 source
optimizer loops。预计每 arm `100/937*14055`，约 1,500 optimizer steps/path，
实际必须由 runner manifest 写出。

# 10. Evaluation

每 arm Alice-Bob deterministic 100 reset streams。

Bootstrap 10,000，unit=episode cluster，seed=60042。

# 11. Gates

## M0 Compatibility

必须：fixed arm full-refresh exact；replay error `<1e-6`；low actor unchanged；
q_D/q_d unchanged；reward unchanged。

失败：`INVALID_R42_IMPLEMENTATION`。下一动作：修 implementation。

## M1 Fixed-anchor retention

Fixed arm 必须 `win_fixed>=0.80`，并保持 `key0,key1>=0.85`。

否则 `INVALID_FIXED_ANCHOR_LOST`。下一动作：恢复 source continuation contract。

## M2 Service noninferiority

定义 `Delta=win_R42-win_fixed`，要求 `CI_95,lower(Delta)>-0.10`。

## M3 Renewal decoupling

只测 t=50 renewal event，因为 100 horizon 只有一次 check。

Metrics：SET rate、KEEP rate、discordant renewal、full-sync SET、skill supply
entropy。

两个 agent 的 discordant renewal：`1[e1 != e2]`，要求
`P(discordant)>0.20`。

Full-sync SET：`P(e1=SET,e2=SET)<0.50`。

Skill supply entropy：`H(Z_SET)/logK>0.8`。

# 12. Terminal lifetime handling

不使用 `corr(T_i,T_j)`，因为 Alice-Bob horizon=100 且 terminal censoring。
只记录 t=50 renewal event；terminal age 作为 censored diagnostic。

# 13. Decision branches

`PASS_R42_NATIVE_CATEGORICAL_RENEWAL_K50`：M0-M3 全通过。下一动作：进入
multi-seed R42 verification，随后才考虑 S7。

`VALID_FAIL_R42_SERVICE`：M0/M1 通过、M2失败。结论：per-agent renewal 在
保持 HMASD credit 下损害服务能力。动作：退休当前 renewal formulation。

`VALID_FAIL_R42_NO_DECOUPLING`：M0-M2通过、M3失败。结论：性能保持，但没有
证明 temporal decoupling。动作：保留 fixed HMASD，不宣称 lifetime
contribution。

`OPERATIONAL_FAILURE`：训练运行失败（CUDA、checkpoint、environment）。动作：
修运行问题，不改变算法。

# Final verdict

`ACCEPT_R42_NATIVE_CATEGORICAL_RENEWAL_K50`

最终唯一实验：

```text
R41B checkpoint -> k0=50 -> native HMASD categorical per-agent renewal
```

不引入新 KEEP、新 duration、intrinsic、variable-N、open roster。

R42 的科学问题被严格限定为：

```text
Can HMASD's existing categorical skill semantics support per-agent renewal
without breaking its original credit contract?
```

来源
