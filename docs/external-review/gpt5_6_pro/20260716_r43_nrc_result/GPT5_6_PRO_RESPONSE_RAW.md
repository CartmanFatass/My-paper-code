# 裁决

[
\boxed{\texttt{CONFIRM INVALID_R43_FIXED_ANCHOR_LOST}}
]

[
\boxed{\texttt{FIXED WRAPPER = SOURCE-EQUIVALENT}}
]

[
\boxed{\texttt{SELECT R44-FS-NRC}}
]

其中 **R44-FS-NRC** 表示：

[
\boxed{
\textbf{Frozen-Source Native Renewal Control}
}
]

唯一下一条因果边是：

[
\boxed{
\begin{aligned}
&\text{冻结已有 R41B 技能、执行器与 source coordinator}\
&+\text{真实 KEEP/RENEW 因子}\
&+\text{只训练 renewal adapter 及其 critic}\
&\rightarrow
\text{在不遗忘既有服务能力的前提下形成异步 lifetime}
\end{aligned}
}
]

当前 R43 结果不重跑、不换 seed、不调整门槛；其 treatment 既不判 PASS，也不判 FAIL。

---

# 一、Validity verdict

`INVALID_R43_FIXED_ANCHOR_LOST` 是正确分支。

正式结果中：

* M0 通过且 `invalid_reasons=[]`；
* fixed final win/key0/key1 为 `0.52/0.54/0.81`；
* 注册门槛为 `0.80/0.85/0.85`；
* 因此 M1 明确失败。

分析器的分支顺序也正确：

```text
M0 fail -> implementation invalid
M0 pass, M1 fail -> INVALID_R43_FIXED_ANCHOR_LOST
M0/M1 pass, M2 or M3 fail -> VALID_FAIL_R43_NRC
all pass -> PASS_R43_NRC_K50
```

M2 和 M3 虽然被计算并写入 JSON，但在 M1 失败时不能决定 scientific status；analyzer 最终确实先返回 fixed-anchor invalid。

没有发现会改变该分支的：

* checkpoint 恢复错误；
* optimizer/ValueNorm 漏载；
* replay 或 working-prefix 错误；
* controller clock 或 auto-reset 错误；
* evaluation reset-stream 错误；
* analyzer 条件错误；
* source archive 或环境合同错误。

这也与仓库的正式 disposition 一致：R43 implementation gate 有效，但 treatment 因 fixed anchor 丢失而没有可解释的科学结论。

不利的 seed-43041 continuation 结果不是 implementation defect。它是这个已注册 continuation 合同下的真实优化结果。

---

# 二、Fixed-path equivalence verdict

## 结论：现有代码加两更新零差异，已经足以认定 fixed wrapper 等价于原 source continuation

不需要再增加第三个 wrapper audit。

### 1. Fixed arm 原样恢复 source 状态

runner 恢复了 R41B checkpoint 中的：

* high policy；
* low actor；
* low critic；
* team discriminator；
* individual discriminator；
* 五个 optimizer；
* high/low ValueNorm；
* checkpoint RNG 状态。

### 2. Fixed arm 的 high collection 直接调用原函数

`_patch_fixed_runner` 中的 fixed `h_collect` 直接执行：

```python
result = original_h_collect(step)
```

之后只更新 telemetry ledger 和只读 roster 记录；它不替换 action、log-probability、value、reward、buffer 或 trainer。

### 3. 新模块在 fixed arm 中完全冻结

安装过程先恢复 module-construction RNG，再把新参数加入 optimizer；fixed 模式随后对三个新模块执行 `requires_grad_(False)`，并继续使用原 high collector 和原 trainer。

### 4. 额外 replay audit 不改变随机流

每次 audit 前保存 RNG，结束后恢复；随后才调用原 `runner.train()`。

### 5. 同 seed、同 checkpoint 的直接比较逐参数相等

两次完整 outer updates、3,200 环境步以后，untouched source continuation 与 fixed wrapper 在全部五个已训练模块上的最大参数差异均为：

[
0.
]

这包括 high policy、low actor、low critic 和两个 discriminator。

两次更新本身不是对 200 次更新的统计外推；这里还有代码级结构等价性。fixed wrapper 没有一个在后续更新才开始改变 loss 或 action 的时间分支，因此这个短 parity test足以验证安装、RNG、buffer 和 update wiring。

---

# 三、可复用的因果结论

## 3.1 已建立：R41B checkpoint 本身具有可靠 access

R41B exact source reproduction 在 seed-1 上获得：

[
\text{win/key0/key1}=0.89/0.97/0.92,
]

zero-step win 为 0，所有五条 optimizer path 各执行 14,055 次更新，M0–M2 全部通过。

同一个未继续训练的 R41B checkpoint 在 R43 的 seed-43041 evaluation stream 上甚至达到：

[
0.93/1.00/0.93.
]

所以 R43 的 M1 失败不是新 evaluation reset stream 太困难。

## 3.2 已建立：继续优化已解 checkpoint 不是稳定的机制控制

继续训练 320K 后，R43 fixed final checkpoint：

* 在 seed-1 stream 上从原 checkpoint 的 `0.89` 降到 `0.61`；
* 在 seed-43041 stream 上从 `0.93` 降到 `0.52`。

因此当前可复用结论是：

[
\boxed{
\begin{aligned}
&\text{一个已具服务能力的 HMASD checkpoint}\
&\xrightarrow{\text{继续执行原 PPO/低层/discriminator 更新}}\
&\text{不保证在短 continuation 中保持该能力。}
\end{aligned}
}
]

更精确地：

> 在 R41B seed-1 checkpoint、16 rollout env、seed 43041、320K continuation 的冻结合同下，原 HMASD full-stack continued optimization 不是一个稳定的 service comparator。

这不是“HMASD 不能继续训练”的一般结论。R42 的 seed 42041 fixed continuation 最终达到 `0.98/1.00/0.98`，说明 continuation 稳定性存在明显 trajectory/seed 依赖；但不能因此事后挑选 R42 的有利 seed。

## 3.3 已建立：fixed wrapper 不是 anchor loss 的原因

代码级 source equivalence、两更新参数零差异和跨 evaluation-stream 结果共同排除了：

* wrapper action path；
* replay instrumentation；
* evaluator reset stream；

作为 observed anchor loss 的解释。

## 3.4 未建立：NRC treatment 的科学效果

不能从当前 R43 得出：

* NRC 导致 zero win；
* true renewal 必然 all-RENEW；
* renewal credit 无效；
* conditional skill-event credit 无效；
* asynchronous lifetime 损害服务；
* R43 应永久退休。

这些 estimand 都要求一个有效的 fixed M1 anchor。

当前 treatment 可复用的只有 implementation-level 证据：

* source-exact zero-init log-probability误差为 (9.54\times10^{-7})；
* working-prefix mismatch 为 0；
* high/factor/low replay error 均为 0；
* renewal actor、renewal critic、skill-event critic在 3,000 次更新中都有非零梯度；
* 三个新模块均有显著参数漂移。
* reset-censored clock也真实执行：3,771 次 auto-reset，没有 reset-triggered high action、roster/team/age violation，且有 6,400 个合法 check rows。

这些只证明：

[
\boxed{
\text{NRC factorization、replay、clock 和 gradient path 可以机械运行}
}
]

不证明其 policy effect 有用。

---

# 四、唯一下一条路线：R44-FS-NRC

当前问题不能通过再换一个 continuation seed解决。需要把“skill system 是否被继续训练破坏”与“renewal timing 是否可学”分开。

## 4.1 唯一因果边

[
\boxed{
\begin{aligned}
&\text{冻结的高服务 R41B skill system}\
&+\text{source-exact true renewal factor}\
&\xrightarrow{\text{只训练 renewal adapter}}\
&\text{服务安全的非同步 renewal}
\end{aligned}
}
]

它只测试：

> 在已有 HMASD skill semantics 和低层执行能力保持不变时，一个显式的 per-agent renewal policy 能否学习何时 KEEP/RENEW。

它不测试新的技能发现、低层适应、(q_D/q_d) 重训练或 source coordinator 再优化。

---

## 4.2 联合策略

在普通 global check：

[
\begin{aligned}
&\pi_H
\left(
Z_\tau,\mathbf b_\tau,\mathbf z_\tau^+
\mid
x_\tau,\mathbf z_\tau^-
\right)\
&=
\pi_Z^{R41B}(Z_\tau\mid x_\tau)
\prod_{j=1}^{N}
\pi_B^\rho
\left(
b_{\sigma(j),\tau}
\mid c_{\tau,j}
\right)
\left[
\pi_S^{R41B}
\left(
z_{\sigma(j),\tau}^+
\mid
Z_\tau,\tilde{\mathbf z}^{(j-1)},x_\tau
\right)
\right]^{\mathbb 1[b_{\sigma(j)}=\mathrm{RENEW}]} .
\end{aligned}
]

其中：

* (\sigma=(1,\ldots,N)) 保持原 MAT canonical order；
* (\pi_Z^{R41B}) 完全冻结；
* conditional non-incumbent skill distribution完全冻结；
* 唯一可训练的行为参数是 renewal residual (\rho)。

若 source skill logits 为 (\ell_i(z))，则零 residual 时：

[
\pi_B^0(\mathrm{KEEP})
======================

\frac{\exp \ell_i(z_i^-)}
{\sum_z\exp\ell_i(z)},
]

[
\pi_B^0(\mathrm{RENEW})
=======================

\frac{\sum_{z\ne z_i^-}\exp\ell_i(z)}
{\sum_z\exp\ell_i(z)},
]

并且：

[
\pi_S^{R41B}(z\mid\mathrm{RENEW})
=================================

\frac{\exp\ell_i(z)}
{\sum_{z'\ne z_i^-}\exp\ell_i(z')}.
]

因此：

[
P_{\rho=0}(z_i^{post}=z)
========================

P_{R41B}(z_i=z).
]

control 与 treatment 都使用这个真实 factorization，而不是一个使用原 categorical、另一个使用 KEEP/RENEW。

---

## 4.3 Exact comparator

### Control：`frozen_source_nrc0`

* 加载 R41B seed-1 `exact_final`；
* source-exact renewal factorization；
* renewal residual输出严格为 0，且冻结；
* source conditional skill logits冻结；
* source high、low、(q_D/q_d) 全部冻结；
* renewal critic可以训练，但不能影响行为。

### Treatment：`frozen_source_nrc`

* 与 control 完全相同；
* 唯一差异是 renewal residual可由 renewal PPO更新。

两臂都实例化相同模块和相同张量路径。control 是 capacity-matched inactive pathway，而不是较小网络；这种 inactive/sham comparator 符合项目的 mechanism-matched hierarchy。

---

## 4.4 冻结与更新边界

两臂均严格冻结：

```text
source MAT encoder
source MAT decoder / team-Z and skill logits
source high value head
low actor
low critic
team discriminator q_D
individual discriminator q_d
high and low ValueNorm
all five R41B optimizer states
```

这些状态仍随 checkpoint 保存，但 optimizer step 数必须为 0。

两臂新增同一个独立 factor optimizer，采用原 high Adam 超参数，不做调参：

```text
renewal actor
renewal critic
```

每个 arm 都调用 factor optimizer 3,000 次：

* control：renewal critic有梯度；renewal actor actor-mask为 0、参数漂移为 0；
* treatment：renewal critic和renewal actor都有有限非零梯度。

conditional skill likelihood仍被存储和 replay-audit，但其 PPO ratio恒为 1，不产生 actor update。这样下一实验只有一个行为变化来源：

[
\boxed{\text{renewal timing}}
]

当前 R43 treatment 的 preflight 明确显示 source decoder也有非零直接梯度 `0.4507`，其训练 loss同时含 team、renewal 和 conditional-skill actor项。因此直接把原 treatment与冻结 control相比会变成“source全栈训练 + NRC”对“冻结 source”，并不能隔离 renewal。

---

## 4.5 Renewal credit

renewal factor继续使用已验证的 reset-censored controller-time return：

[
R_{\tau,i}^{B}
==============

\sum_{r=0}^{49}
\gamma^r r_{t_\tau+r}^{env}.
]

* auto-reset不终止该 return；
* reset后的 primitive steps仍归入同一个 50-step block；
* update boundary使用 old renewal critic bootstrap并断开 GAE；
* 不增加 lifetime reward、KEEP reward、switch penalty或 renewal entropy。

低层仍执行：

[
a_{i,t}\sim\pi_l^{R41B}(a_i\mid o_{i,t},z_{i,t}),
]

但参数冻结。

原 (q_D/q_d) 可以继续按原公式只读计算和记录；它们不更新，不成为 renewal selector，也不进入 renewal return。

---

## 4.6 为什么不是有利 seed 选择

新 gate 保持：

```text
training seed = 43041
evaluation reset stream = seed 43041
source checkpoint = R41B seed-1 exact_final
```

不使用 R42 的 seed 42041，不使用 R42 fixed final checkpoint，也不从多个 continuation 中选择最佳 checkpoint。

## 4.7 为什么不是“frozen versus trained”全算法比较

两臂的整个 source HMASD system都冻结。

唯一 active/inactive 差异是：

```text
renewal residual actor:
    control   frozen at zero
    treatment trainable
```

两臂的：

* source policy；
* skill executor；
* conditional skill distribution；
* team (Z) policy；
* critics/discriminators；
* collector；
* clock；
* renewal critic训练；
* environment exposure；

全部一致。

因此这是一个 renewal-adapter ablation，不是 frozen HMASD 与 fully trained NRC 的比较。

---

# 五、最小 abandonment gate

## 5.1 固定运行合同

```text
experiment                 R44-FS-NRC-K50
source checkpoint          R41B seed-1 exact_final
training seed              43041
arms                       frozen_source_nrc0, frozen_source_nrc
rollout environments       16 per arm, concurrent
episode / rollout          100 / 100
global check               k0 = 50
environment steps          320,000 per arm
outer updates              200 per arm
environment-check rows     6,400 per arm
factor PPO epochs          15
factor optimizer steps     3,000 per arm
source optimizer steps     0 on all five paths
final evaluation           100 paired deterministic episodes per arm
bootstrap repetitions      10,000
bootstrap seed             62043
```

继续使用 320K，而不是缩短或扩展，是因为它是 R42/R43 已注册的机制暴露；换成一个更短预算会重新引入 underexposure 解释，扩展预算则构成 invalid-result rescue。

---

## 5.2 M0：implementation 与 frozen-source contract

必须全部满足：

1. 两臂从同一个 R41B exact-final checkpoint恢复；

2. zero-step 两臂的有效 joint post-skill probability和分解 log-probability相对 source误差均：

   [
   \le10^{-6};
   ]

3. team、renewal、conditional skill和low replay最大误差：

   [
   \le10^{-6};
   ]

4. working-prefix mismatch 为 0；

5. source MAT、low actor/critic、(q_D/q_d)、两个 ValueNorm 在两臂中的最终最大参数/状态漂移：

   [
   \le10^{-12};
   ]

6. 五个 source optimizer step 数全部为 0；

7. factor optimizer两臂均恰好 3,000 steps；

8. control renewal actor drift：

   [
   \le10^{-12};
   ]

9. treatment renewal actor：

   * 3,000 次有限非零 gradient exposure；
   * relative parameter drift (>10^{-6})；

10. renewal critic在两臂都有有限非零梯度；

11. exactly 16 structural assignments、6,400 check rows、0 auto-reset high actions；

12. same-label RENEW 为 0；

13. no task fields、no reward shaping、no new intrinsic、no renewal entropy；

14. 在相同的 100 个 deterministic resets 上，control 的 zero-step和final：

```text
episode wins
key0 rows
key1 rows
episode lengths
high and low action traces
```

必须逐项完全相同。

任一失败：

```text
INVALID_R44_FSNRC_IMPLEMENTATION
```

唯一下一动作是修复明确的 freeze、replay、clock、checkpoint或evaluation defect，原样重跑。

---

## 5.3 M1：frozen service anchor

control final 必须满足原门槛：

[
W_C\ge0.80,
]

[
K0_C\ge0.85,
\qquad
K1_C\ge0.85.
]

由于 control 的行为参数不可变化，M1失败只能是 checkpoint、factorization或evaluation wiring错误：

```text
INVALID_R44_FROZEN_ANCHOR
```

不得解释 treatment。

---

## 5.4 M2：服务安全

保持 R42/R43 原门槛：

[
\operatorname{LCB}_{95}
\left[
W_T-W_C
\right]

>

-0.10.
]

不得改为只看均值，也不得扩大 margin。

---

## 5.5 M3：真实 temporal decoupling

排除 structural initial assignments，只读显式 renewal token：

[
\text{treatment discordant-renewal rate}\ge0.20,
]

[
\operatorname{LCB}_{95}
\left[
D_T-D_C
\right]>0,
]

[
\text{treatment full-sync RENEW}<0.50,
]

[
\min_i
{
P_i(\mathrm{KEEP}),
P_i(\mathrm{RENEW})
}
\ge0.05,
]

[
H(\text{actual RENEW targets})/\log4>0.80,
]

[
\text{same-label RENEW}=0.
]

label entropy或高 renewal频率不能代替这些联合门槛。

---

## 5.6 互斥分支

### `PASS_R44_FSNRC_K50`

仅当：

[
M0\land M1\land M2\land M3.
]

允许结论：

> 在冻结的、已有服务能力的 HMASD skill system 上，显式 renewal adapter能够在不显著损害服务的情况下产生非退化的个体 lifetime。

唯一后续动作：

> 原公式、原冻结边界、原门槛的一次 paired multi-seed Alice–Bob verification。

不进入 S7 或 variable (N)。

### `VALID_FAIL_R44_FSNRC`

条件：

[
M0\land M1\land\neg(M2\land M3).
]

永久退休：

* frozen-source renewal adapter；
* 该 next-check renewal credit；
* 该 Alice–Bob K50 timing-only route。

不能通过解冻 source、改 seed、加预算、加 entropy或改门槛救援。

允许的结论仅为：

> 已有 R41B skills 固定时，所注册的 renewal adapter没有同时实现服务安全和 temporal decoupling。

它不否定一般的共同适应式 asynchronous skills。

---

# 六、当前 R43 treatment 的处置

[
\boxed{\texttt{DIAGNOSTIC-ONLY；不退休 NRC}}
]

可保留：

* source-exact probability decomposition；
* replay/teacher-forcing正确性；
* reset-censored clock；
* auto-reset continuity；
* renewal/critic gradient actionability；
* 观察到的 optimizer collapse pattern，作为未来 failure-mode catalog。

禁止据此声称：

* zero win 是 NRC 的 causal effect；
* all-RENEW 是 NRC 必然坍缩；
* target entropy低证明 skill supply失败；
* R43相对 fixed HMASD退化；
* renewal route应被退休。

仓库 disposition 已经明确规定，在 M1 失败时这些 treatment outcome必须 quarantine。

---

# 七、继续关闭的路线

以下均不得用于“救援”当前结果或新 gate：

* 换用 seed 42041；
* 增加训练 seed；
* 增加或减少 environment steps；
* 降低 `0.80/0.85/0.85` anchor；
* 放宽 (-0.10) service margin；
* best-checkpoint selection；
* 从 R43 invalid final继续训练；
* R42 residual的任何改名或容量变体；
* lifetime/KEEP reward；
* switch penalty；
* renewal entropy；
* full-refresh escape；
* duration-category action；
* task goal、button、diamond、contact、distance或phase字段；
* task-specific intrinsic reward；
* S7；
* open roster或 variable (N)。

这些边界也符合当前工作记录：R43不得重跑，variable-team在 fixed-(N) gate以前继续阻塞。

---

# 八、最强反对意见

最强反对意见是：

[
\boxed{
\text{冻结 source skill system 可能阻止 renewal timing 与 skill semantics 共同适应。}
}
]

原 HMASD 的技能是在固定 50-step refresh下学习的。延长某个技能后，其低层 executor、(q_d) semantics和 team-(Z) composition可能需要同步改变。R44-FS-NRC 若失败，可能只是说明：

[
\text{固定的 }50\text{-step skills}
\not\Rightarrow
\text{可直接重组为 variable-lifetime skills}.
]

它不能证明 joint co-adaptive NRC 不存在。

这个反对意见不改变裁决。当前首要未识别因素是 source full-stack continued optimization本身会摧毁服务。先冻结 source，才能第一次干净回答：

[
\boxed{
\text{renewal timing 本身是否具有安全、可学习的增量价值？}
}
]

在该边闭合以前，再允许 source skill、低层 policy和 discriminator共同变化，只会重新混合 temporal mechanism与 catastrophic continuation drift。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\texttt{R43 status = INVALID_R43_FIXED_ANCHOR_LOST};\
&\text{fixed wrapper已充分证明 source-equivalent；不再审计 wrapper};\
&\text{R43 treatment只保留 implementation diagnostics；无科学结论};\
&\text{唯一下一边 = R44-FS-NRC frozen-source renewal adapter};\
&\text{source五条 policy/discriminator路径全部冻结};\
&\text{只训练 renewal actor及其 critic};\
&\text{使用同 seed 43041、同 320K、同 service/temporal thresholds};\
&\text{有效失败即永久退休该 frozen-source timing route，不救援。}
\end{aligned}
}
]
