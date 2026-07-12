# R27-G2 Pre-Implementation Design Review (Independent MARL Reviewer)

- Reviewer: Claude (independent MARL reviewer role; cross-family relative to the GPT peer-review line)
- Date: 2026-07-12
- Scope: design/review only, per the R27-G1 result-boundary sync. Nothing here authorizes implementation, launch, reward injection, or architecture change.
- Inputs read: `memory/CURRENT_WORK.md`, `memory/ALGORITHM_PRINCIPLES.md`, `memory/ExpRecord.md` (EXP-20260711-r27-g1 intake), `memory/IMPLEMENTATION_PLAN.md` (R26-G1a/R27-G1 boundary sections), `scripts/audit_r27_low_actor_capacity.py`, `scripts/r24_forced_behavior_audit.py` (flaw list confirmed as described), `envs/pettingzoo/scenario7_energy_aware.py` (RNG structure).

---

## 1. Verdict

**APPROVE_WITH_CHANGES.**

Option A (replay-matched causal branches) is the right instrument, the focal-agent-only intervention unit is correct, and the null/parity discipline is mostly right. But the proposed Gate B/C logic — "late-window separation nonzero with bootstrap lower bound > 0, exceeding inactive/shuffled nulls" — is **not able to answer the question the experiment is asking**. As written, the experiment would classify a pure transient nudge as PERSISTENT_BEHAVIOR_AND_EFFECT with high probability. The required changes (Section 10) fix this without changing the causal edge under test, the reward-off status, or the general-MARL boundary.

## 2. Strongest scientific objection

**Divergence under deterministic closed-loop dynamics is trivially nonzero, so "separation > 0 at H=50" cannot distinguish a persistent skill from a chaotically amplified one-step nudge.**

R27-G1 has already established that changing `z_i` changes the immediate action distribution (standardized action-mean distance ≈ 0.29–0.30 under rollout hidden state). In a deterministic policy + deterministic-given-seed multi-agent mobile environment, any nonzero action difference at the branch point compounds mechanically: positions diverge, observations diverge, hidden states diverge, and every downstream distance metric grows — even if the FiLM modulation carries zero information after step 1. Under the proposed design:

- The **inactive FiLM null is exactly zero by construction** (identical branches under determinism), so it is a wiring/leakage check, not a statistical reference for "how much divergence does a non-skill perturbation produce."
- The **shuffled-label null cannot help either**: in both the skill hypothesis and the chaos hypothesis, the divergence is genuinely caused by the label change, so shuffling destroys the association in both cases. It discriminates nothing.
- The **reset-cluster bootstrap LB > 0** will therefore pass almost automatically at every horizon, for every agent, for every skill pair, in both hypotheses.

Consequently interpretation branches 1 (PERSISTENT_BEHAVIOR_AND_EFFECT) and 2 (TRANSIENT_ACTION_NUDGE) are **observationally indistinguishable under the proposed gates**, and Gate C inherits the same defect (state divergence grows mechanically from action divergence). The experiment must add controls whose predictions differ between the two hypotheses. Three such controls exist and are cheap (Section 10, changes 1–3): the pulse-versus-hold control, the on-branch instantaneous z-swap controllability sequence, and cross-context label-consistency (held-out decoding promoted from supplementary to co-primary). This is the same class of mistake the program already caught once at R27-G1 ("do not interpret immediate sensitivity as persistence") — here it would reappear as "do not interpret accumulated divergence as persistence."

A second, smaller objection: **a fully deterministic natural prefix collapses context diversity to a single trajectory per reset seed and is off the training distribution** (R27-G1 collected snapshots with `deterministic=False` for both skill assignment and low actions). Prefixes should be stochastic-natural and *recorded*, then replayed exactly; determinism is only needed post-branch.

## 3. Answers to the twelve reviewer questions

1. **Intervention unit.** Yes — focal-agent-only `z_i` forcing with team code and non-focal skills preserved is the correct unit for the edge `z_i -> persistent executable behavior`. Forcing all agents to one label (the r24 audit) confounds individual skill with team composition; the proposal correctly avoids it.
2. **Non-focal skills.** Two-stage, as you suspect. **Stage 1 (gated, primary): freeze non-focal skills and suppress all renewal for the horizon.** This is the cleanest isolation and is matched across branches by construction. **Stage 2 (reported, not gated): natural asynchronous renewal for non-focal agents**, where post-branch renewal divergence is a legitimate causal consequence of the intervention. Do not mix the stages in one gate. Note the external-validity bound honestly: with duration candidates {3,7,13,24} intervals = {30,70,130,240} primitive steps, some non-focal renewals would naturally occur inside H=50, so Stage 1 contexts become mildly unnatural late in the horizon — internally valid, externally bounded.
3. **Prefix replay sufficiency.** Yes, with the parity battery in Section 8 — and with one amendment: generate the prefix with **natural stochastic sampling, record executed actions and skill decisions, and replay the recorded actions** for every branch. Required parity checks: branch-point observation/global-state exact equality; **environment `np_random` bit-generator state equality at the branch point** (stronger than observation equality — it catches consumed-draw mismatches before they surface); restored actor hidden-state equality; live-vs-diagnostic action parity (R27-G1 style); same-z branch re-run bitwise identity; no torch global RNG consumption post-branch; CUDA with deterministic algorithms and no CPU fallback; checkpoint hash before/after.
4. **Branch points.** Fixed prefix times, provided they are multiples of `skill_interval=10` (50/150/250 all are), so every branch point is a high-level check boundary. At the branch, uniformly set the focal agent's `age_i = 0` and a fixed nominal duration for **all** branches including the same-z and inactive controls. Do **not** make natural focal renewal boundaries the primary branch set: conditioning on the policy's own choice to renew induces selection bias (context correlated with skill choice) and uneven support across agents. Record "focal agent was naturally at expiry vs mid-commitment" as a covariate and analyze the natural-expiry subset as a secondary robustness slice.
5. **Horizons.** 10/25/50 is acceptable and, critically, **nested**: run one 50-step branch and read H=10/25/50 as windows of it (early window steps 1–10, mid 16–25, late 41–50). Do not run separate branches per horizon — that would triple cost for nothing. Interpretive bound: H=50 = 5 check intervals, longer than the shortest lifetime (30) but shorter than d=7/13/24 lifetimes; the claim is "persists ≥5 intervals under forced hold," which suffices to falsify "one-step nudge" but not to certify lifetime-scale persistence for long durations. If the pilot shows budget headroom, add H=100 (≥ one d=7 lifetime) at decision grade; do not block on it.
6. **Effect representation.** Primary behavioral: focal deterministic action-mean sequence, per-dimension standardized with statistics frozen from natural-prefix data (endorsed). Co-primary (new): the on-branch instantaneous z-swap SKL sequence (Section 10, change 2). Secondary effect: focal local-observation delta trajectory and normalized global-state delta at H=25/50 endpoints; non-focal joint-action response diagnostic-only. Caveat to record: observation/state vectors *contain* communication-derived fields by construction; using the full standardized vector is domain-agnostic methodology and acceptable, but never gate on, select, or headline comm subfields — per-dimension breakdowns are descriptive only.
7. **Statistics/thresholds.** Section 6. Reuse R27-G1 anchors wherever a comparable quantity exists (0.02 nats SKL, 0.20 standardized distance); freeze all new thresholds **before the pilot runs**, and quarantine pilot outcome metrics (pilot is wiring/parity/timing only).
8. **Aggregation.** Unit of independence = reset group (64 clusters). Everything (contexts, agents, pairs) aggregates to cluster level before a 10k-resample cluster bootstrap with a fixed seed. Checkpoints are temporal-stability observations, never pooled as seeds: classify per checkpoint, require ≥2/3 agreement (the R27-G1 convention). Breadth rules prevent one-exceptional-pair passes: ≥4/6 focal agents individually positive on the primary statistic, ≥3/6 skill pairs with positive cluster-bootstrap LB.
9. **Nulls.** Necessary: inactive FiLM identity (expect *exactly* zero under determinism; nonzero → INVALID), same-z replay (expect bitwise identity; drift → INVALID), **pulse control (new, load-bearing)**, the full parity battery, finite/support checks, reset-cluster bootstrap. Redundant or demoted: shuffled/fake-label trajectory null (cannot discriminate the two live hypotheses — keep only as a cheap pipeline sanity check inside the decoding analysis); duration-matching is a design invariant under forced hold, not a separate null; agent-matched analysis is an aggregation rule, not a null.
10. **Option A hidden confounds.** (a) Env RNG: Scenario-7 uses the Gymnasium `np_random` stream with per-step, action-independent draws (e.g., UAV failure sampling), so common random numbers hold up to divergence — standard and fine — but assert bit-generator state equality at the branch and document that post-branch streams are common-up-to-divergence, not identical. (b) Deterministic prefixes collapse context diversity (one trajectory per seed) and are off-distribution — use recorded stochastic prefixes. (c) Restore *all* recurrent state that feeds behavior (per-agent low-actor hxs; any recurrent high-level selector state), not just low-actor hxs. (d) Exogenous failure events fire identically across branches (CRN) — good, but a failure of the focal agent inside the horizon should invalidate that context. (e) Episode boundary: prefix 250 + H 50 = 300 must sit strictly inside the episode; a branch crossing episode end is INVALID for that context. (f) Torch RNG: assert zero consumption post-branch in deterministic mode. (g) Frozen non-focal skills: internally valid, externally bounded (Q2). (h) Forcing must run through the **live stateful rollout path** with a forced-label hook and per-step assertion of the executed label — precisely the r24 static-method flaw to avoid.
11. **Nudge vs skill.** A transient nudge predicts: immediate SKL passes; instantaneous z-swap SKL decays toward zero across the horizon; hold-z and pulse-z trajectories are equally separated from reference at H=50; late-window behavior does not decode the forced label on held-out reset groups; effect directions are inconsistent (near-zero mean alignment) across contexts. A temporally extended skill predicts the converse on all four. Raw trajectory or state divergence distinguishes **nothing** — this is why changes 1–3 are required, not optional.
12. **Abandonment criterion.** Pre-commit now: capacity is already verified (R27-G1), and R27-G2 is maximally favorable to the skill hypothesis (forced hold, frozen team, matched context and RNG, deterministic execution). If, with valid instrumentation (all parity checks pass), adequate support (no UNDERPOWERED), and at most **one** INVALID-fix rerun, all three checkpoints show sustained-controllability decay AND hold≈pulse AND chance-level held-out decoding for both behavior and effect — then the conclusion is that the trained policy's `z_i` channel does not carry temporally extended behavior under the current architecture+objective, and the correct response is to stop re-instrumenting this diagnostic. The next move is then a *training-pressure/architecture* question (branch 2/5 actions), and if a subsequent redesigned training run still fails the same pre-registered G2 protocol, the skill representation itself should be abandoned. No threshold changes, no new diagnostic family for this edge.

## 4. Recommended intervention protocol (step by step)

Stage 1 (primary, gated), per checkpoint (final first as pilot, then update25/update30/final):

1. For each reset group r ∈ {0..63}: reset with `seed = 1 + r` (R27-G1 convention). Assign one prefix length per reset, balanced across {50, 150, 250} (≈21/21/22 split) — **one branch context per reset**, not three.
2. Run the natural policy stochastically (training-mode sampling, as in R27-G1 collection) to the prefix end. Record: executed primitive actions, executed skill decisions, and at the branch point: observations, global state, all per-agent actor hidden states, active skills, ages/durations, team code, masks, and the env `np_random` bit-generator state.
3. Reference branch: from the branch point, suppress all skill renewal, keep all agents' current skills, run deterministically for H=50. (This is the z_ref trajectory for every focal agent.)
4. For each focal agent i ∈ {1..6} and each skill label z ∈ {0..3}: re-reset with the same seed, replay the recorded prefix actions exactly, assert the parity battery, restore policy runtime state, set focal `z_i = z` with `age_i = 0` and fixed nominal duration, freeze all other agents' skills, suppress all renewal, run all policies deterministically and statefully for 50 steps. (The z = natural-z branch doubles as the same-z reproducibility null when compared to the reference branch.)
5. **Pulse branches**: for each focal agent and each z ≠ z_ref, force z for exactly the first check interval (10 steps), then revert to z_ref for the remaining 40. (If budget-constrained, pulse a pre-registered 2-of-3 subset of non-reference labels per agent.)
6. **Inactive branches**: per context, for each focal agent, two distinct labels with γ=1, β=0 — must be bitwise identical to each other and to the reference.
7. At every post-branch step of every forced branch, additionally compute (diagnostic forward, never executed) the action-distribution parameters the focal actor would emit for each *other* skill label given the branch's current `o_t, h_t` — the instantaneous z-swap sequence.
8. Log per-step: focal action mean/σ, focal observation, global state, executed skill labels for all agents (assert forcing), swap-SKLs, finiteness flags.
9. Stage 2 (secondary, ungated): repeat steps 4 with natural non-focal renewal allowed (non-focal high-level decisions run live post-branch); report but do not gate.

Everything reward-off; checkpoints loaded frozen with before/after hash equality; no training graph constructed.

## 5. Exact primary and secondary metrics

Let windows be W_early = steps 1–10, W_mid = 16–25, W_late = 41–50 post-branch. All action/state dimensions standardized with natural-prefix statistics frozen before any forced branch is analyzed.

Primary (behavior):

- **P1 Sustained controllability**: mean pairwise symmetric KL of the instantaneous z-swap distributions per step, averaged within window; report SKL_late and decay ratio ρ = SKL_late / SKL_early.
- **P2 Hold-vs-pulse late separation**: D_hold = standardized L2 distance between hold-z and reference focal action-mean sequences over W_late, averaged over labels; D_pulse likewise for pulse branches; statistic Δ = D_hold − D_pulse and ratio D_hold/D_pulse, computed per (context, agent) on matched labels.
- **P3 Label consistency**: held-out reset-group decoding accuracy of the forced label from a fixed low-dimensional W_late behavior summary (window action-mean, action-Δ, and swap-SKL features), using the frozen R27-G1 synthetic classifier protocol (same optimizer/early-stopping/split contract); chance = 0.25.

Primary (effect, Gate C):

- **P4**: standardized focal local-observation delta distance between skill pairs at H=25 and H=50 endpoints, with the same hold-vs-pulse difference Δ_effect and a held-out decoding variant from state-effect summaries.

Secondary/diagnostic (reported, never gated): branch-point immediate SKL and standardized action-mean distance (Gate A reproduction); global-state delta distances; per-dimension effect breakdowns; effect-vector cross-context alignment (mean cosine of (traj_z − mean_z) across reset groups); non-focal joint-action response; pulse-branch return-to-reference dynamics; Stage-2 (natural renewal) versions of P1–P4.

## 6. Pre-registered thresholds and aggregation rules

Freeze before the pilot; pilot outcomes are quarantined from threshold setting.

- **Gate A (immediate, sanity)**: branch-point mean pairwise SKL ≥ 0.02 nats and standardized action-mean distance ≥ 0.20, cluster-bootstrap LB > 0. Failure here contradicts R27-G1 → treat as INVALID-suspect and audit instrumentation before any interpretation.
- **Gate B (persistent executable behavior)** — all three required:
  - B1: SKL_late ≥ 0.02 nats with cluster-bootstrap LB > 0, and decay ratio ρ ≥ 0.5.
  - B2: cluster-bootstrap LB of Δ (hold − pulse, W_late) > 0 and median D_hold/D_pulse ≥ 1.5.
  - B3: held-out decoding accuracy ≥ 0.40 (chance 0.25) with cluster-bootstrap LB > 0.25.
  - Breadth: ≥4/6 focal agents individually satisfy B1; ≥3/6 skill pairs have positive pairwise-separation LB in W_late.
- **Gate C (generic downstream effect)**: at H=25 or H=50, P4 pairwise separation LB > 0 **and** at least one of {Δ_effect LB > 0 (hold > pulse), state-effect held-out decoding ≥ 0.40 with LB > 0.25}. Magnitude-only passes are prohibited (they are chaos-compatible). No communication-specific target anywhere.
- **Gate D (family)**: classify per checkpoint; final classification requires ≥2/3 checkpoints agreeing. Checkpoints are temporal-stability observations, never pooled and never counted as seeds. Cluster = reset group everywhere; contexts/agents/pairs aggregate within cluster (mean over contexts, median over agents) before bootstrap (10k resamples, 95% CI, fixed registered seed).
- **Support floors (else UNDERPOWERED)**: ≥48/64 reset groups valid after parity/episode-boundary/focal-failure exclusions, per checkpoint; every (agent, label) cell ≥40 valid branches; every prefix-length stratum ≥14 valid clusters.
- **Validity (else INVALID)**: any parity failure, inactive nonzero separation, same-z nonzero drift, non-finite value, CPU fallback, checkpoint hash change, executed-label assertion failure, or episode-boundary crossing not excluded.

## 7. Required null controls and validity checks (final list)

Required: (1) inactive FiLM identity (exact-zero expectation); (2) same-z replay bitwise reproducibility; (3) **pulse control** (new); (4) branch-point obs/state/hidden/RNG-state parity battery incl. env `np_random` bit-generator state equality; (5) live-vs-diagnostic actor parity; (6) executed-label per-step assertion; (7) finite-value and support checks; (8) reset-cluster bootstrap; (9) episode-boundary and focal-failure exclusion rules; (10) checkpoint hash immutability; (11) torch-RNG non-consumption post-branch; (12) agent-matched, duration-matched, context-matched construction (design invariants, verified in manifests). Demoted: shuffled/fake-label trajectory null (pipeline sanity inside P3 only — it cannot discriminate the live hypotheses).

## 8. Pilot, then decision-grade configuration

- **Pilot (wiring only, final checkpoint)**: 8 reset groups, prefix 150 only, all 6 agents × 4 labels + pulses + inactive + same-z, H=50 nested windows, full parity battery. Purpose: parity exactness, timing, support accounting, manifest/schema validation. ≈8 × ~54 branches × 200 steps ≈ 90k env steps — minutes at R27-G1 cloud throughput. **Pilot outcome metrics are quarantined**: read only by an automated validity checker; no human reads effect sizes; thresholds do not move.
- **Decision-grade**: 3 checkpoints × 64 reset groups × 1 context each (prefix balanced 50/150/250) × [24 hold + 12–24 pulse + 2 inactive + 1 same-z + 1 reference ≈ 40–52 branches] × (prefix + 50) steps. ≈8–11k steps per env per checkpoint → roughly 2–3 h/checkpoint at the R27-G1 rate; ~6–9 h total, one overnight cloud batch. Stage 2 (natural renewal) adds ~40% if run for all contexts; acceptable to run Stage 2 on a pre-registered half of the resets.

## 9. Full decision tree

```text
Any validity check fails ............................ INVALID
  -> fix instrumentation only; rerun same thresholds; at most ONE such
     iteration before escalating to the user.
Support floors unmet ................................ UNDERPOWERED
  -> increase pre-registered support only; thresholds unchanged.
Gate A fails ........................................ INVALID-suspect
  -> contradicts R27-G1; instrumentation audit before interpretation.
Gate A passes:
  B1 ∧ B2 ∧ B3 ∧ breadth ∧ C ....................... PERSISTENT_BEHAVIOR_AND_EFFECT
     (≥2/3 checkpoints) -> authorizes DESIGN of a small clipped low-only
     intrinsic reward (separate review); not activation.
  B passes, C fails ................................. PERSISTENT_ACTION_NO_EFFECT
     -> investigate discovery/semantic training pressure, not actor capacity.
  B1 decays (ρ<0.5) ∧ hold≈pulse (B2 fail) ......... TRANSIENT_ACTION_NUDGE
     -> commitment/recurrent architecture question (separate authorization).
  B1 passes, B2 fails ............................... AMPLIFIED_NUDGE (record as MIXED)
     -> FiLM stays live but adds nothing beyond its first-interval push;
        treat as branch 2 for all reward decisions.
  B1/B2 pass, B3 fails .............................. INCONSISTENT_MODES (record as MIXED)
     -> control without stable skill identity; treat as branch 5 for reward.
  Nothing beyond A passes ........................... NO_PERSISTENT_SEPARATION
     -> apply the pre-committed abandonment criterion (Q12); do not enable
        reward; do not re-instrument.
  Checkpoints disagree (<2/3) ....................... MIXED / temporal instability
     -> no reward authorization; report per-checkpoint.
Any B/C pass + standing R26 negative ................ additionally record
     OBSERVATIONAL_INSTRUMENT_FAILURE for R26 (annotation, not an outcome).
```

MIXED is a first-class recorded outcome (the proposal's 7-branch set has no home for partial passes; the two named MIXED sub-cases above close that gap). All MIXED outcomes are treated as branch 5 for reward/authorization purposes.

## 10. Required changes before implementation (blocking)

1. **Add the pulse control** (force one interval, revert; duration-matched horizon) and gate B2 on hold-vs-pulse. Without it, branches 1 and 2 are indistinguishable.
2. **Add the instantaneous z-swap controllability sequence** (diagnostic forwards along each branch) and gate B1 on late-window sustained controllability, not trajectory distance.
3. **Promote held-out reset-group decoding from supplementary to co-primary (B3)** using the frozen R27-G1 classifier protocol. Trajectory divergence without cross-context label consistency is chaos-compatible.
4. **Replace the deterministic natural prefix with a recorded stochastic-natural prefix** (replayed exactly); keep determinism post-branch only. Optionally add a CRN-stochastic post-branch robustness tier (shared Gaussian noise across branches) as ungated secondary.
5. **Make horizons nested windows of one 50-step branch** (no separate runs per horizon).
6. **Add env RNG bit-generator state equality to the branch parity battery**, plus episode-boundary and focal-failure-event exclusion rules.
7. **One branch context per reset** with prefix length balanced across resets; branch at check-interval boundaries with uniform `age=0`/nominal-duration handling across all branches including controls.
8. **Rewrite Gates B and C** per Section 6 (conjunctive B1∧B2∧B3 + breadth; C requires hold>pulse or decoding, never magnitude alone), add the MIXED sub-outcomes, freeze all thresholds before the pilot, and quarantine pilot outcomes.
9. **Force through the live stateful rollout path** with per-step executed-label assertions (the r24 static-path flaw is otherwise easy to reintroduce via a "convenient" diagnostic method).
10. **Pre-register the abandonment criterion** (Section 3, Q12) and the one-INVALID-fix-iteration limit in the design doc itself.

## 11. Claims the experiment may and may not support

May support (if gates pass): the frozen R25 arm0 policy's individual `z_i` causally controls the focal agent's action pattern in a sustained, label-consistent way for ≥5 check intervals under forced hold in matched contexts; forced `z_i` produces distinguishable generic local/global state effects at H≤50; R26's observational instrument missed a real causal mechanism (annotation). May support (if gates fail): the trained `z_i` channel is a transient control nudge, or controls behavior without consequential effect, under conditions maximally favorable to persistence.

May NOT support, regardless of outcome: natural (unforced) skill persistence or the policy's own duration usage; skill *semantics*, differentiation quality, or usefulness; team complementarity; credit assignment; sparse-reward benefit; task improvement; any intrinsic-reward choice or activation; anything about arm2 or other checkpoints/architectures; generalization beyond this environment family (the method is domain-agnostic; this evidence is not). Synthetic-control accuracy and decoding accuracy remain instrument checks, never skill-semantics evidence.

## 12. Reviewer-role and memory notes

This document is a proposal under the project's reviewer role boundary: it amends nothing in `ALGORITHM_PRINCIPLES.md`, `IMPLEMENTATION_PLAN.md`, or `ExpRecord.md` by itself. Disposition (accept/modify/reject per change) belongs to the active controller and should be recorded in the external-review dialogue ledger per the Round protocol, with this file as the raw-text evidence. The `CURRENT_WORK.md` attention state ("R27-G2 design/review is the only authorized next step") remains accurate after this review; the next action it points to is the controller's disposition of Section 10.
