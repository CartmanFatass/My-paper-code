# R21 Autopsy Report — sampled team-intent Z mechanism-negative

Author: CC (Claude), Executor role (user-authorized diagnostic scripts).
Date: 2026-07-06. Read-only: no training launched, no algorithm code modified,
no fix applied. The implementation-era plan remains available in Git history.

Artifacts under audit (seed 1): `dist/logs_cloud_r21_team_intent_64env/.../seed1/{r21_z_probe,r21_z_reward_coef005}/`
+ `standalone_process_core_final.pt` / `..._update_20.pt`.
Diagnostic scripts (scratch): `<job>/tmp/audit_b_teamdisc.py`, `audit_b_control2.py`, `audit_a_forced_z.py`.

## TL;DR classification

**Primary: `true-objective-failure`** — the training objective contains no term that
forces the joint assignment to depend on `Z`, so `Z`'s influence on the
skill/duration policy stays at its ~noise *initialization* level (forced-Z skill
KL ≈ 0.002 at BOTH random-init and final). A `Z` that does not change behavior
leaves no signature in `s_next`, so the team discriminator correctly reads chance.

**Secondary contributors:**
- `effectively-unwired` assignment head: the team-vector pathway has near-zero
  effective gain even at random-init (not "trained out" — GPT's sub-hypothesis is
  refuted: random-init ≈ final).
- `truncation-contaminated` duration metrics + a **K≈episode confound**: with
  `team_intent_k=48 ≈ episode=50` high-level intervals there is ~one Z commitment
  per episode, so the two-clock degenerated to ~one team decision per episode.

**Ruled out:** `label-misaligned` (Audit B: strict lockstep). Not primarily
`Z-boundary churn` (Audit C: churn is once-per-episode near terminal).

---

## Audit B — team-discriminator data-contract sanity → `aligned-real`

**Alignment (static trace).** Rollout records are appended in lockstep per env-step
in `train.py:3016-3028`: `rollout.team_codes.append(int(low_context["team_code"]))`
(the *pre-step held Z*, captured in `pre_low_context`) and
`rollout.next_states.append(info["next_state"])` (the *post-step* global state).
`_team_intent_rollout_update` (`standalone_agent.py:3388`) consumes them at matching
indices: `labels = team_codes`, `states = next_states` → exactly `q_D(Z | s_next)`
with label = the Z in force during the transition. **Aligned. No off-by-one.**

**Leakage.** `next_states` is the env global UAV state; it does not carry `Z`.
Leakage would push acc *above* chance; observed acc ≈ chance is consistent with
*no* leakage and no behavioral imprint. Not a leakage bug.

**Prior + reward timing.** Prior = running `team_intent_prior_counts` normalized,
updated *after* the loss (no look-ahead). Reward preview computed under `no_grad`
*before* `opt.step()` (`standalone_agent.py:3414-3426`) → pre-update `q_D`. Both correct.
Checkpoint priors are near-uniform (probe entropy 1.7835 nats vs ln6=1.7918, norm
0.9954; reward arm 1.7831) — matches logged `team_disc_prior_entropy`, confirms Z
was sampled ~uniformly.

**Metric-path positive/negative control** (`audit_b_control2.py`, proper train/held-out split):

| dataset | train_acc | HELD-OUT_acc | chance |
|---|---|---|---|
| separable (signal exists) | 1.000 | **1.000** | 0.167 |
| independent (no signal) | 1.000 | **0.174** | 0.167 |

The logged `team_disc_acc` is the pre-update read on each *fresh* on-policy rollout,
i.e. an online/held-out read. The control reproduces R21's ≈0.17 exactly for the
*independent* case: the loss/acc path is sound; a model that *memorizes* train
labels still reads ~chance on held-out when the state carries no signal about Z.

**Verdict:** `team_disc_acc ≈ chance` is a **genuine mechanism read**, not a
label/leakage/prior/timing bug.

---

## Audit A — forced-Z assignment actionability → Z behaviorally near-inert

Method (`audit_a_forced_z.py`): rebuilt each checkpoint via
`eval_checkpoints.build_agent_for_checkpoint`; generated an in-distribution batch
from 48 real env resets (S7-S1, 6 agents; B = 48×6 = 288 rows); for each `z∈0..5`
computed `team_vector = bridge(compact, forced_team_code=z)` then
`high.logits(obs, prev_skills, ages, compact, team_vector, omega, agent_relevance, ar_prefix=None)`;
measured skill/duration divergence vs `z=0`. This mirrors the live
`_z_assignment_intervention_metric` (`standalone_agent.py:3304`), generalized to all
6 codes and both heads.

| build | SKILL KL_mean | KL_max | TV_mean | argmax_disagree | DUR KL_mean |
|---|---|---|---|---|---|
| random-init | 0.00165 | 0.00253 | 0.0247 | 0.346 | 0.00137 |
| update_20   | 0.00185 | 0.00505 | 0.0241 | 0.489 | 0.00094 |
| final       | 0.00223 | 0.00689 | 0.0260 | 0.526 | 0.00139 |

**Interpretation.** Forced-Z skill KL is ~0.002 at **both random-init and final**
(final is marginally *higher*, not lower). This matches the live logged
`z_assignment_itv` ≈ 0.0016-0.0051 (my probe 0.0017→0.0022; run 0.0033→0.0048),
validating the probe. Per the dissociation table this is the **`unwired` /
never-made-actionable** branch, not `wired-but-ignored (trained out)`: training
neither built nor removed Z's influence. The high argmax_disagreement (~0.5) with
tiny KL (~0.002) means the skill policy is **flat/under-confident**, so a
near-noise team-vector perturbation flips argmaxes without any structured,
confident, Z-conditioned assignment shift — i.e. Z nudges noise, not coordination.

Caveat: the probe uses episode-start contexts and `ar_prefix=None`; but (a) both
builds use the identical batch so the random-init≈final dissociation is robust,
and (b) the absolute magnitude agrees with the live real-segment metric, so the
simplification is not hiding a large effect. The roster/AR-docking channel
(teammates' active skills) is a *separate* mechanism from the Z code and is not the
subject of this actionability probe.

**Verdict:** the sampled `Z` code has ~noise (~0.002 KL) influence on the
assignment head, present already at initialization and never amplified by the
objective → Z is behaviorally near-inert; nothing made it actionable.

---

## Audit C — boundary-truncation cause → `truncation-contaminated` (+ K≈episode confound)

Trace (`standalone_agent.py:2534-2559`): `z_boundary_trunc_rate_durX` is recorded
**only inside `if team_boundary_due:`**, counting among agents whose *active* skill
is duration-X the fraction with `duration_remaining > 0` (i.e. not naturally
expired) at the Z boundary; then `expired[:]=True` reassigns all agents.

Arithmetic: `_open_team_intent_boundary` sets `team_intent_remaining = team_intent_k*k
= 48*10 = 480` primitive steps (`:2167`); `episode_length = 500` (`:1425`). So per
episode there is **one episode-start open** (records `trunc_frac=0`, per-duration
buckets skipped because no skills are active yet) **and one terminal Z boundary at
step 480**, ~2 intervals before episode end. This matches `z_decisions_per_update
= 128 ≈ 2 × 64 envs`.

Consequences:
- Per-duration buckets sample **only the terminal boundary**. A long skill (13/24
  intervals) that is "on" at step 480 is definitionally mid-flight → truncated →
  bucket rate ≈ **1.0 near-tautologically** (observed dur13≈0.99, dur24≈0.85).
- Overall `z_boundary_trunc_rate ≈ 0.45` is diluted by the episode-start zeros
  (~half the recorded boundaries).
- Therefore duration-collapse / lifetime reads under R21 are **invalid** — a
  measurement artifact of the `K≈episode` coincidence, exactly the gate's warning.
- Churn: atomic full-team reassignment fires ~**once per episode, near the end**,
  truncating long skills that were about to end anyway. So Z-boundary churn is
  **not** a large mid-episode disruptor and is **not** the primary cause of the
  task regression (the reward-off probe arm regressed too, cov 0.10 vs S-base 0.42).
  The regression is more plausibly the forced AR-roster + Z-conditioning
  assignment-path swap that turning on team-intent imposes vs the S-base.

**Bonus finding (design confound):** `team_intent_k=48 ≈ episode=50` means ~one
team-intent commitment per episode. The intended "slow Z with async individual
skills between Z boundaries" had almost no room to operate, and the discriminator
saw ~one Z label per episode trajectory — starving within-episode Z variation.
Any future two-clock test must set `team_intent_k ≪ episode horizon`.

---

## Implication for `memory/R22_TWO_CLOCK_ELBO.md`

1. **The missing ingredient is confirmed to be a cross-layer actionability term**
   `I(Z ; ξ | c, ω)` (ξ = joint assignment / roster / duration structure). Audit A
   shows Z was never actionable (init≈final ~0.002 KL); Audit B shows the team
   discriminator `I(Z ; s_next)` is downstream-useless until behavior depends on Z.
   The ELBO is a **rewrite around a never-actionable Z**, not an autopsy of a
   wired-but-idle one, and not merely "stop suppressing Z."
2. **Gate the team discriminator behind actionability.** `q_D(Z|s_next)` reward
   must not be applied until a `forced_Z_assignment_KL` floor is met, else it is
   provably decorative (this run). No double-count with the coordinator residual in
   R21 because the team channel is inert; the composition question only becomes real
   once actionability exists.
3. **Fix the K≈episode confound before any two-clock rerun** (`team_intent_k ≪`
   episode horizon) so multiple Z periods per episode exist, duration reads are
   clean, and the discriminator sees within-episode Z variation.
4. The task regression is a **policy-path** effect (forced AR-roster/Z-conditioning),
   not Z-boundary churn — separate any future team-intent from that confound by
   matching the S-base selection path when isolating Z.

## Reproduction

```bash
cd C:/project/HMASD
PYTHONPATH=C:/project/HMASD python <job>/tmp/audit_b_control2.py     # metric-path control
PYTHONPATH=C:/project/HMASD python <job>/tmp/audit_a_forced_z.py     # forced-Z sweep (CPU, ~1-2 min)
```
No bug requiring a code fix was found (data contract is correct); therefore no
minimal-fix patch is proposed. The findings are design/objective-level, not
implementation-bug-level.
