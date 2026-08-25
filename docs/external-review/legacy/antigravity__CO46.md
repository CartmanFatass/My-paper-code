# Antigravity CO46: Cross-Validation Analysis

Date: 2026-06-26
Context: HA-CTSE process-core standalone algorithm, post A1 run (`mi_only + high_only + smdp_bootstrap`, 240k steps, 6 agents, S7-S1).

## Source Evidence

- Code: `ha_ctse_process/standalone_agent.py` lines 1032–1048, 1115–1310
- Config: `ha_ctse_process/config.py`
- Run: `logs/ha_ctse_process_s7s1_6agent_a1_mi_highonly_smdp_1m2/metrics/train_updates.csv`
- Docs: `memory/ALGORITHM_PRINCIPLES.md`, `memory/IC_SPL_HAZARD_SMDP_ALTERNATIVE.md`

---

## Question 1: Does `mi_only + high_only` theoretically prevent low-level from learning process semantics?

### Verdict: Yes, structurally. The low-level policy is informationally isolated from process semantics.

**Evidence from code** (`standalone_agent.py` L1032-1048):

```python
if self.process_reward_injection in {"high_only", "high_and_low"}:
    high_process_rewards = process_reward_np
else:
    high_process_rewards = np.zeros_like(process_reward_np)
if self.process_reward_injection in {"low_only", "high_and_low"}:
    low_process_rewards = process_reward_np
else:
    low_process_rewards = np.zeros_like(process_reward_np)  # <-- high_only => this path
```

Under `high_only`, `low_process_rewards` is identically zero. The low-level rollout reward (`rollout.rewards`) receives **only** environment reward. The low-level policy `pi_l(a_i | o_i, z_i)` is updated by PPO on these env-only rewards.

**Theoretical consequence:**

- The low-level actor has no gradient path from process MI to its parameters.
- The skill embedding `z_i` enters the low-level actor as a one-hot vector, but nothing in the low-level reward encourages `z_i` to produce distinguishable **processes**. The only distinguishability pressure comes from the high-level reward, which adjusts *which* `z_i` is chosen, not *how* `z_i` is executed.
- The ALGORITHM_PRINCIPLES.md states: "The discoverer should receive task reward plus process/outcome exploration reward redistributed over the segment or assigned at termination." Under `high_only`, this contract is violated.

**However, the situation is not completely hopeless:**

The low-level critic is also conditioned on `(o_i, z_i)`. If different `z_i` values lead to different environmental reward landscapes (because the high-level is guided by process reward to assign skills situationally), then the low-level will *indirectly* learn different behaviors per skill. But this is a much weaker and slower channel than direct process reward injection.

**Implication for A2 ablation:** A2 (`high_and_low`) is the correct test. If A2 shows improvement in service metrics while A1 stagnates, it confirms that the low-level needs process signal to differentiate skill execution.

**Risk of `high_and_low`:** If the process MI reward is noisy or the posterior has shortcuts, injecting it into low-level will corrupt the environmental reward signal. This is why the reward magnitude matters — at `~1e-4` to `7e-4`, it may be harmless but also useless even when injected.

### Recommendation:

1. Run A2 as planned.
2. If process reward remains at `1e-4` scale, it will be negligible even when injected. Scale the problem first (see Q6).
3. Consider a hybrid: inject **per-step** redistributed process reward into low-level (as currently coded at L1041-1047), but also add a **terminal bonus** at segment end for the agent whose segment just closed. This creates a sharper credit signal.

---

## Question 2: Should SMDP bootstrap be clipped, coefficient-gated, or disabled?

### Verdict: SMDP bootstrap is likely amplifying high-level value error and should default to off or be heavily damped.

**Evidence from code** (`standalone_agent.py` L1129-1207):

The bootstrap computation:
```python
bootstrap_values = self.high.evaluate(...)[2]  # V(s_{t+T}) from critic
values[bootstrap_indices] = bootstrap_values
```

Then in `update_high_from_segments` (L1266-1275):
```python
returns_np = (
    env_returns_np
    + process_rewards
    - renewal_penalties
    + smdp_discounts_np * bootstrap_values_np  # <-- gamma^T * V(s_{t+T})
)
```

**Evidence from run data:**

From the CSV (update 60, step 240k):
- `high_env_return_mean ≈ 0.31`
- `high_bootstrap_value_mean ≈ 3.76`
- `high_smdp_discount_mean ≈ 0.40`
- So bootstrap contribution = 0.40 × 3.76 ≈ 1.50, which is **~5× the env return**.

Earlier updates show even more extreme ratios:
- Update 50 (200k): env_return=9.30, bootstrap=2.88, discount=0.48 → bootstrap contribution≈1.38
- Update 55 (220k): env_return=6.54, bootstrap=3.46, discount=0.49 → bootstrap contribution≈1.70

**The problem:** The high-level critic `V(s_{t+T})` is trained jointly with policy updates. Early in training, this value estimate is highly inaccurate. When the bootstrap contribution is comparable to or larger than the env return, the high-level advantage becomes dominated by critic error, not by actual task performance. This explains:

1. `high_value_loss` being very large (18-168 range in later updates).
2. High-level policy oscillating rather than consistently improving.
3. The eval metric regression: the high-level may be choosing skills/durations that look good to a miscalibrated critic but produce poor real-world outcomes.

**Additional concern: compounding through SMDP discount.**

With `duration_candidates = [1,2,4,8,16,32]` and `skill_interval` (k), segment lengths range from k to 32k steps. For long segments:
- `gamma^T` with γ=0.99, T=320 steps (32 intervals × 10 steps) → 0.99^320 ≈ 0.04
- `gamma^T` with γ=0.99, T=10 steps → 0.99^10 ≈ 0.90

The discount factor itself varies by 20× across duration choices. Combined with inaccurate V, this creates a strong incentive to choose long durations (low discount = low bootstrap contribution = less critic noise), which aligns with the observed behavior of segment lengths growing over training.

### Recommendations:

1. **A1b ablation is the right immediate test.** If `no_bootstrap` stabilizes or at least prevents eval regression, that's strong evidence.
2. **If bootstrap must stay:** Add a `bootstrap_coef ∈ [0, 1]` that scales the `smdp_discounts_np * bootstrap_values_np` term. Start with 0.1 or 0.25.
3. **Value normalization:** Consider normalizing the high-level value target to have zero mean and unit variance within the batch (PopArt or simple running stats). This would prevent the critic from learning a scale that makes the bootstrap contribution dominate.
4. **Warmup:** Disable bootstrap for the first N updates (e.g., 20 updates / 80k steps) to let the critic learn a reasonable value scale before feeding its predictions back as training targets.
5. **Gradient clipping for high-level critic:** If `high_value_loss` is in the 100+ range, the critic gradients are very large. Add grad norm clipping (e.g., max_grad_norm=0.5) to the `high_opt`.

---

## Question 3: Does the process posterior have duration/length/reward-sum shortcuts?

### Verdict: Likely yes. The diagnostic evidence is consistent with moderate shortcut leakage.

**Evidence from run data (update 60, 240k):**

| Metric | Value |
|--------|-------|
| `posterior_acc` | 0.374 |
| `duration_only_accuracy` | 0.413 |
| `length_only_accuracy` | 0.385 |
| `reward_sum_only_accuracy` | 0.374 |

All three shortcut baselines track very close to the actual posterior accuracy. The posterior accuracy is **not significantly above** the duration-only or length-only baselines.

**Over the training trajectory:**

| Update | posterior_acc | duration_only | length_only | reward_sum_only |
|--------|--------------|---------------|-------------|-----------------|
| 1 (4k) | 0.218 | 0.299 | 0.280 | 0.257 |
| 20 (80k) | 0.249 | 0.257 | 0.261 | 0.249 |
| 40 (160k) | 0.295 | 0.306 | 0.285 | 0.276 |
| 50 (200k) | 0.353 | 0.371 | 0.362 | 0.357 |
| 60 (240k) | 0.374 | 0.413 | 0.385 | 0.374 |

Key observations:
1. `posterior_acc` and `duration_only_accuracy` rise together.
2. At update 60, `duration_only_accuracy` is **higher** than `posterior_acc`, which is a red flag — it means you could predict skill labels from duration alone better than the trained posterior can from full segment data.
3. `skill_duration_mi` rises from 0.03 to 0.04, meaning skill and duration choices are becoming correlated (the policy is learning to assign specific durations to specific skills).

**Why this happens:**

The `ProcessEncoder` (L310-335) pools over `(obs, action, reward)` sequences with mean pooling. The `reward` signal encodes segment return scale, which correlates with duration. The mask itself encodes length. The one-hot skill embedding is not involved in the encoder — the encoder only sees the segment and must infer the skill from the trajectory. If trajectories under different skills mainly differ by how long they run, duration/length becomes the dominant feature.

**Additionally,** with `duration_candidates = [1,2,4,8,16,32]`, the candidate set spans a 32× range. This creates very distinct segment profiles just from length and accumulated reward, making shortcut prediction easy.

### Debiasing Recommendations:

1. **Normalize segment length in the encoder.** Before mean-pooling, normalize the step encodings by segment length so the pooled representation doesn't trivially encode length. Alternatively, use a fixed-length attention mechanism or a CLS token approach.

2. **Remove reward from encoder input.** The `step_input = cat([obs, action, reward])` at L330 lets the encoder read per-step reward, which accumulates into a length-correlated signal. Consider dropping reward from the encoder input (keep it only for the outcome head via a separate path).

3. **Add a duration-invariant contrastive loss.** Within each duration bucket, enforce that different skills produce different embeddings. This directly penalizes the posterior for relying on duration.

4. **Shrink the duration candidate set.** `[1,2,4,8,16,32]` is a very wide range. Consider `[1,2,4,8]` or even `[2,4,8]` for the initial ablation batch to reduce the information content of duration as a feature.

5. **Add explicit duration-debiasing.** Train an auxiliary head that predicts skill from duration alone, then subtract its logits from the posterior logits (adversarial debiasing). This forces the posterior to rely on segment content.

6. **Track `posterior_acc_minus_duration_only` as a primary diagnostic.** If this gap is consistently near zero or negative, the posterior is not learning anything beyond duration.

---

## Question 4: Should entropy coefficients be ablation switches rather than fixed values?

### Verdict: Yes, but with nuance. The current fixed coefficients are too small to matter and should be tuned or made adaptive.

**Evidence from code:**

- `high_entropy_coef = 0.01` (config.py L42)
- `low_entropy_coef = 0.01` (config.py L43)

**Evidence from run data (update 60):**

- `high_entropy = 3.99` (compared to max ≈ log(5) + log(6) ≈ 3.39 for skill + duration, so this is actually high because team code entropy is added)
- `low_entropy = 5.70`
- `team_code_entropy ≈ 1.59` (max ≈ log(5) ≈ 1.61)

The entropy values look healthy in isolation. But the real question is about the **loss contribution**:

- `high_entropy_loss ≈ -0.04` vs `high_policy_loss ≈ 0.0` to `8.0` vs `high_value_loss ≈ 9.9` to `168`
- The entropy loss is 2–3 orders of magnitude smaller than the value loss.

**This means entropy pressure is practically irrelevant in the high-level update.** The optimizer is dominated by value loss corrections, not by entropy exploration.

### Recommendations:

1. **For ablation design:** Make `duration_entropy_coef`, `skill_entropy_coef`, and `g_entropy_coef` separate switches with independent defaults. This lets you test whether, e.g., forcing duration diversity matters without changing skill diversity pressure.

2. **For practical tuning:** Increase `high_entropy_coef` to 0.05–0.1 or use adaptive entropy (e.g., target entropy = 0.5 × max_entropy, adjust coefficient by Lagrange). The current 0.01 is decorative.

3. **For the ablation batch:** Add an A1c variant with `high_entropy_coef=0.1` to see if increased exploration pressure at the high level prevents the duration collapse seen at update 60.

4. **Low-level entropy is less urgent** because the low-level is receiving env reward and the action space is continuous (4D). The 0.01 coefficient for continuous entropy is reasonable given that the log-std parameterization already provides exploration.

---

## Question 5: Should you push toward IC-SPL hazard SMDP now?

### Verdict: Not yet. The current discrete-lifetime core has not been sufficiently debugged.

**Rationale:**

1. **The current problems are not caused by discrete durations per se.** They are caused by:
   - Weak/negligible process reward magnitude (~1e-4).
   - Bootstrap-dominated high-level returns.
   - Possible posterior shortcut learning.
   - Low-level not receiving any process signal.

   All of these would also affect a hazard SMDP variant.

2. **Hazard SMDP adds complexity:**
   - Per-step termination probabilities require storing per-step termination log-probs in the rollout, which changes the PPO update structure.
   - The hazard rate itself can collapse (always terminate or never terminate).
   - On-policy correction for variable-length segments with stochastic termination is harder than for discrete-lifetime segments with deterministic countdown.

3. **The current discrete-lifetime baseline provides a cleaner ablation target.** Once the A1/A1b/A2 batch resolves the bootstrap and injection questions, you'll have a stable process-reward signal to compare hazard termination against.

### When to switch:

- After the current ablation batch (A1b, A2) is complete.
- After process reward magnitude is confirmed to be meaningful (>0.01 average, or demonstrably affecting policy choices).
- After the posterior shortcut issue is addressed.
- After high-level bootstrap is stabilized.
- Then Stage 3 of the IC-SPL migration plan (introduce `HazardSkillPolicy` as a named variant) is the right next step.

---

## Question 6: Is the eval regression caused by weak process reward, wrong injection site, or high-level credit assignment error?

### Verdict: It is primarily a **credit assignment** problem, compounded by weak reward magnitude.

**The causal chain I infer from the evidence:**

```
1. Process reward is negligibly small (~1e-4 to 7e-4)
   ↓
2. High-level return is dominated by env_return + bootstrap
   ↓
3. Bootstrap value (V~3.8) >> env_return (V~0.3-6.5)
   ↓
4. High-level advantage is mostly bootstrap noise
   ↓
5. PPO ratio pushes high-level policy toward critic's biased preferences
   ↓
6. Critic learns from returns that are themselves bootstrap-contaminated
   ↓
7. Positive feedback loop: critic bias → policy shift → worse trajectories → worse value targets
   ↓
8. Eval metrics degrade even though training "return" appears to improve
```

**Specific evidence for each link:**

| Step | Evidence |
|------|----------|
| 1 | `process_reward_mean ≈ 0.0017` at 240k |
| 2 | `process_reward_high_mean ≈ 0.0017` vs `high_env_return_mean ≈ 0.31` |
| 3 | `high_bootstrap_value_mean ≈ 3.76` at 240k |
| 4 | `high_value_loss` varies 2–168 across updates |
| 5 | `high_policy_loss` oscillates wildly (0.0 to 8.0) |
| 7 | Eval coverage drops: 0.195 → 0.127 → 0.068 |
| 8 | Training `env_reward_mean` stays ~0.1, doesn't track eval degradation |

**It is NOT primarily an injection-site problem:**

Even if you inject process reward into low-level (A2), at magnitude ~1e-4, it adds ~0.0001 per step to a reward signal where env reward is ~0.1 per step. The ratio is 1:1000. The injection site matters only when the injected signal is large enough to influence behavior.

**Priority fix order:**

1. **Fix bootstrap** (A1b ablation, or add bootstrap coefficient 0.1).
2. **Increase process reward scale.** Options:
   - Increase `process_reward_coef` from 0.05 to 0.5 or 1.0.
   - Use `centered_mi` mode, which batch-centers the MI reward to create relative advantages even when absolute MI is small.
   - Use `positive_mi` mode to avoid negative process rewards that fight env reward.
3. **Address posterior shortcuts** so that MI reward reflects genuine process differentiation.
4. **Then** test injection site (A2) once the reward is large enough to matter.

---

## Summary Table

| Question | Answer | Priority |
|----------|--------|----------|
| Q1: Low-level process semantics | Structurally blocked under `high_only` | Medium — fix after Q6 |
| Q2: SMDP bootstrap | Likely causing eval regression via critic bias | **Critical — A1b is the right test** |
| Q3: Posterior shortcuts | Moderate evidence; duration_only_acc ≥ posterior_acc | High — debiasing needed |
| Q4: Entropy as ablation | Entropy coefficients too small to matter; make separate + larger | Medium |
| Q5: Push to hazard SMDP | Not yet; fix current issues first | Low priority now |
| Q6: Root cause of eval regression | Bootstrap credit assignment error + weak reward scale | **Critical** |

## Recommended Immediate Actions

1. **Wait for A1b** (`no_bootstrap`) results at 80k–160k eval. This is the single most informative ablation running.

2. **Prepare A1c**: `mi_only + high_only + smdp_bootstrap=False + process_reward_coef=0.5`
   - Tests whether increasing process reward magnitude helps when bootstrap is removed.

3. **Prepare A1d**: `mi_only + high_only + smdp_bootstrap=True + bootstrap_coef=0.1`
   - Tests whether damped bootstrap is viable.

4. **Defer A2** until bootstrap and reward magnitude are resolved. Running it now with ~1e-4 process reward will produce a null result.

5. **Add `posterior_acc - duration_only_acc` as a tracked metric.** If this is consistently ≤ 0, the posterior is not providing useful signal regardless of reward mode.

## Open Questions for User

1. What is the `skill_interval` (k) for the A1 run? The CSV doesn't directly show it, but segment lengths suggest k≈10 based on `segment_length_mean ≈ 134` at update 60 and `duration_target_mean ≈ 16.8`, giving k ≈ 134/16.8 ≈ 8–10.

2. Is the high-level critic using any form of value normalization or grad clipping? From the code, I see no explicit `nn.utils.clip_grad_norm_` in `update_high_from_segments`. Adding this could help independently of the bootstrap question.

3. Should we consider **not** sharing the optimizer between compact encoder, bridge, and high-level policy? Currently they're all in `high_opt`. The OPT compact encoder may have very different gradient scales than the skill-duration heads.

4. The `process_reward_mode = "centered_mi"` option batch-centers MI within each update's segments. Has this been tried? It would make the process reward zero-mean by construction, which is better for PPO advantages than a raw MI that is always near zero with a tiny positive bias.
