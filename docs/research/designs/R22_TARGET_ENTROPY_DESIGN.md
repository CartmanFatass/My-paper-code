# R22 Target Entropy Design

## 1. Purpose / Status

This document specifies the R22 design direction for replacing entropy patches
with per-head target-entropy constraints in the current R21/v6 two-clock
HA-CTSE mainline.

Status:

- Design document only in R22.
- No automatic temperature implementation is authorized by this document.
- Existing duration and Z entropy floors remain stabilizer flags for current
  experiments, not final mechanism claims.
- Implementation should wait until the R21 team-intent run and the HMASD
  current-env baseline read identify which head actually collapses under useful
  learning.

The goal is not to force heterogeneity as a reward target.  The goal is to make
entropy control a derived constraint attached to the relevant policy head, so
collapse prevention is explicit, measurable, and separable from the cooperation
mechanism claim.

## 2. Why Floors Are Stabilizers, Not Final Mechanism Claims

R16.5 showed that a duration entropy floor can preserve late training
performance, but the resulting classification is PASS-SCAFFOLDED rather than
PASS-CLEAN.  The floor is useful engineering: it can prevent a head from
collapsing while the rest of the objective is being tested.  It does not prove
that lifetime diversity is emergent or that the duration head is learning the
right SMDP structure.

The same rule applies to Z entropy.  A Z entropy floor can keep the slow
team-intent head sampled enough for the team discriminator to receive data, but
it does not prove that Z is a useful team commitment.  That claim must come from
R21 diagnostics: team discriminator health, task metrics, reward-ratio guards,
Z decision counts, advantage variance, and leakage audits.

Therefore:

- Floors are stabilizers for runnable experiments.
- Floors are not heterogeneity rewards.
- Floors are not evidence that the corresponding head has self-sustaining
  semantics.
- R22 should convert successful stabilizers into target-entropy constraints
  only after the useful-learning head failure is localized.

## 3. Per-Head Targets

Use one target per stochastic head.  Each target should be defined in the same
units as the observed entropy for that head, with a normalized diagnostic
reported against the head maximum when the action set is finite.

```text
H_target_Z        for slow team intent pi_Z
H_target_z        for individual skill pi_z
H_target_duration for duration/edit head
H_target_action   for low-level action policy
```

Recommended interpretation:

| Head | Policy | Clock | Target role | Initial target policy |
| --- | --- | --- | --- | --- |
| Team intent | `pi_Z(Z | c, omega)` | slow team commitment | Keep enough sampled team commitments for non-vacuous R21 team-disc learning. | Fraction of `log(num_team_intents)`, lower than uniform once `team_disc_acc` becomes informative. |
| Individual skill | `pi_z(z_i | Z, c, omega, o_i, roster)` | async individual response | Prevent premature collapse of response skills while allowing specialization by Z/context. | Fraction of `log(num_skills)`, monitored per Z/context bucket when sample counts permit. |
| Duration/edit | duration or edit decision head | async lifetime / renewal | Prevent the R16.5-style long-duration or single-edit collapse without claiming lifetime diversity as the objective. | Fraction of `log(num_duration_candidates)` or edit-head maximum; compare to per-duration truncation. |
| Low-level action | `pi_l(a_i | o_i, z_i)` | primitive action | Preserve exploration only where PPO action entropy collapses before task behavior stabilizes. | Standard action-space target; avoid using it to mask high-level collapse. |

Targets should be head-local.  A healthy low-level action entropy does not
rescue a collapsed Z head, and a healthy duration entropy does not prove useful
individual skill semantics.

Notation / metric warning:

```text
Mathematical notation:
  Z   = slow team intent.
  z_i = individual response skill.

Current R21 code metrics:
  `z_usage_entropy`, `z_usage_max_frac`, and `z_boundary_*` refer to the
  sampled team intent Z, not to individual response skills z_i.  This naming is
  historical and must not be copied into new theory notation.  If individual
  response-skill entropy is added later, use an unambiguous prefix such as
  `skill_usage_entropy`, `proto_skill_entropy`, or `ind_skill_entropy`.
```

## 4. Target-Entropy Lagrangian Form

For each head:

```text
minimize over log_alpha_head:
  L_alpha_head =
    -log_alpha_head * stopgrad(H_target_head - H_observed_head)
```

With a nonnegative temperature `alpha_head`, the practical update is the
SAC-style dual adjustment:

```text
alpha_head increases when H_observed_head < H_target_head
alpha_head decreases when H_observed_head > H_target_head
```

The actor-side entropy term for the same head should remain a regular
entropy-weighted policy term:

```text
J_entropy_head = alpha_head * H_observed_head
```

The stop-gradient constraint update prevents the target from becoming a direct
reward for arbitrary heterogeneity.  The head is asked to maintain enough
uncertainty for learning, not to maximize diversity for its own sake.

Sign convention:

```text
The formula above assumes ordinary gradient descent on log_alpha_head.  If an
implementation instead performs gradient ascent or optimizes alpha directly,
the sign must be re-derived and unit-tested.  A sign mistake would silently
increase collapse pressure when entropy is already too low.
```

## 5. Diagnostics For Auto-Temperature Decisions

Do not enable auto-temperature globally.  Decide per head from observed failure
mode.

| Head | Collapse signal | Useful-learning signal | Auto-temperature trigger | Do not trigger when |
| --- | --- | --- | --- | --- |
| `pi_Z` | Low team-intent entropy (`z_usage_entropy` in current R21 logs), too few Z samples, flat `team_disc_acc`. | Gradual `team_disc_acc` rise, stable reward ratios, nonzero Z advantage variance. | Z collapses before `team_disc_acc` can learn or before the 320k R21 mechanism gate. | `team_disc_acc` is instant-near-1.0; run leak audit first. |
| `pi_z` | Individual skill entropy collapses within Z/context buckets; skill decisions become single-mode. | Individual residual or action/effect diagnostics remain informative without shortcut dominance. | Skill collapse coincides with degraded R21 task metrics or dead individual residual signal. | High entropy only reflects inert interchangeable skills; then the missing issue is usefulness, not temperature. |
| Duration/edit | `duration_usage_entropy` falls, `duration_usage_max_frac` rises, floor stays active, or per-duration Z-boundary truncation concentrates. | Stable task metrics without persistent floor activation; per-duration truncation is not dominating. | R16.5-style lifetime collapse recurs in a useful R21 branch. | The head is healthy at coef=0.05 or the failure is caused by K-team truncation. |
| Low-level action | PPO action entropy collapses before coverage/throughput stabilize. | Task behavior improves while high-level heads remain non-collapsed. | Action collapse blocks exploration after high-level heads look healthy. | High-level heads are collapsed; fix the causal head first. |

Reward-ratio guards remain mandatory context.  If combined intrinsic-to-env
ratio or team-disc-to-env ratio is pathological, fix objective scale before
using auto-temperature as a mask.

## 6. Staged Implementation Path And Non-Goals

Staged path:

1. Keep R22 as design only while R21 and HMASD baseline reads are pending.
2. Use R21 diagnostics to identify the first collapsing head under useful
   learning.
3. Add head-local target, observed entropy, normalized entropy, and alpha
   diagnostics before changing actor loss behavior.
4. Implement auto-temperature for one head at a time, default-off, with the
   current floor retained only as a safety comparison.
5. Promote a floor to a target-entropy constraint only when the target version
   matches or improves the stabilizer without creating reward-ratio pathology.

Explicit non-goals:

- Do not add a new heterogeneity reward.
- Do not implement automatic temperature in R22 before R21/HMASD reads.
- Do not use entropy health as a substitute for task metrics or discriminator
  usefulness.
- Do not hide R16.5 PASS-SCAFFOLDED behind target-entropy language; the old
  result remains floor-supported evidence.
- Do not tune all heads at once.

## 7. Interaction With R16.5 PASS-SCAFFOLDED And R21

R16.5 remains the key cautionary example.  The duration floor helped prevent
late collapse and recovered useful task performance, but floor activation stayed
persistent.  That makes the floor a stabilizer and baseline scaffold, not a
claim that HA-CTSE discovered self-maintaining lifetime diversity.

R21 is the mainline test for sampled slow team intent Z.  The entropy design
must support that test without changing its scientific read:

- If R21 succeeds while Z and duration entropy stay healthy, auto-temperature
  can remain unnecessary.
- If R21 shows useful team-disc learning but Z collapses too early, consider
  `H_target_Z` first.
- If R21 shows useful team-disc learning but duration collapses again, consider
  `H_target_duration` first.
- If R21 has healthy entropy but poor task metrics, the issue is likely
  usefulness, scale, double-counting, or cross-layer coupling, not entropy.
- If R21 `team_disc_acc` is instantly high, run leakage audits before adding
  entropy machinery.

The desired endpoint is a per-head constraint system that explains why entropy
is present in the objective, while preserving the R22 rule that entropy is a
derived stabilizing constraint and not the mechanism that earns the cooperation
claim.
