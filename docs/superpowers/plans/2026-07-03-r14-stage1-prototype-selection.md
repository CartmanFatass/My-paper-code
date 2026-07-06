# R14 Stage 1 Implementation Spec — Prototype-Response Selection + Individual Per-Step Discriminator

Author: CC (Claude, cross-validation) — spec only, no code changed.
Date: 2026-07-03 (amended same day per Round 15: AR-first selection;
coordinator-residual reward replaces the prior head).
Source contracts: `memory/cross_validation.md` -> Round 14 (R14.1 J2 +
J5-individual, R14.2 stage 1) and Round 15; derivation:
`memory/R15_steering_objective_derivation.md`.
Implementer: Codex.

## Purpose

Implement R14.2 Stage 1: (A) skills become prototype-response codes selected by
a head conditioned on OPT's own outputs (Job 2), and (B) the paper-faithful
HMASD Eq. 4 individual discriminator returns as a per-step reward with the
team latent replaced by the recognized situation (Job 5, surviving half).
This is the first non-vacuous dense intrinsic pressure under the Round 12
recognition-first framing, and it finally tests the per-step active-skill-label
discriminator form that Rounds 11-13 note was never run.

## Non-goals (explicitly out of scope)

- No commitment / omega* target / validity hazard changes (J3 — Stage 2).
- No coverage complementarity or AR slot assignment (J4 — Stage 3).
- No team transition reward / SEF/DADS (Stage 4).
- No communication/backhaul/coverage fields anywhere in inputs or rewards.
- `learned_beta`, R12-1b guards, P3-4 forcing paths untouched.
- Everything default-OFF; reward additionally gated behind its own flag.

## Current-code facts the implementation must respect

1. `InteractionCompactEncoder` (`standalone_agent.py:98-160`) is a simplified
   OPT: pooled state+obs token -> `prototype_logits` -> sparsemax `weights`
   (batch, N) over N learned prototype VECTORS (`self.prototypes`), not
   entity-attention maps. There is NO per-agent omega today.
2. High-level selection is already per-agent via `self.high`
   (`logits(high_obs, prev_skills, ages, compact, team_vector)`), so J2 does
   not need a new policy class — it needs new INPUTS and a skill-space
   binding.
3. `weights` are currently discarded as `_weights` at the update sites
   (e.g. `update_high_from_segments` ~line 3301) and in rollout context
   computation. Exposing them is part of this stage.
4. Situation kappa is per-env (global) from `situation_substrate.py::
   assign_kappa_from_omega`. Stage 1 conditions the discriminator on this
   global kappa; per-agent kappa_i arrives with Stage 2 (J3) or the R13-Q6
   change, whichever lands first. The discriminator interface must accept a
   kappa tensor so the later per-agent swap is input-shape-only.
5. A legacy `transition_skill_discriminator` exists but is entangled with
   retired semantic-gate machinery. Do NOT extend it. Build the new module
   clean; leave the legacy path untouched and disabled.
6. Checkpoint compatibility: changing `self.high` input dims breaks resume.
   Follow the `low_actor_condition_on_team_code` precedent: record the new
   flags in checkpoint metadata and restore them on load.

## Part A — Prototype-response selection (Job 2)

### A1. Config (all default-off / inert)

```text
use_prototype_response_skills = False
    Master switch for Part A.
prototype_skill_extra_codes = 0
    n_skills := num_prototypes + extra codes when the master switch is on.
    Assert at startup that config.n_skills matches, or override with a loud
    log line (choose override + log; do not silently diverge).
high_condition_on_omega = False
    When True (required by the master switch), concat omega (num_prototypes)
    into the high-level policy input for both skill and duration heads.
use_agent_prototype_relevance = False
    When True, compute per-agent relevance and feed agent i's relevance row
    into agent i's selection input (see A2).
use_autoregressive_selection = True (when the master switch is on)
    R15 amendment: the sequential decision is KEPT HMASD STRUCTURE and the
    null model of the Part-B reward, so selection is AR from day one:
    pi_h(z_i | omega, c, o_i, z_prev_i, z_{1:i-1}), fixed agent-id order
    first (relevance-sorted order = later ablation). Store EACH agent's
    assignment log-prob log pi_h(z_i | ...) in the segment/buffer — Part B
    consumes it per step. `--parallel_selection` ablation flag preserves the
    old parallel path for comparison.
prototype_bank_ema_tau = 0.005
    EMA copy of `self.prototypes` updated after each encoder optimizer step.
    All SEMANTIC consumers (Part B discriminator conditioning, later Stage 2
    commitment targets) read the EMA bank; the live prototypes remain the
    trainable ones. Guards skill-semantics drift.
```

### A2. Encoder change

Extend `InteractionCompactEncoder.forward` to also return
`agent_relevance` (batch, n_agents, N):

```text
rel_i = sparsemax(prototype_logits(obs_tokens[:, i, :]))
```

Reuses the existing `obs_proj` and `prototype_logits` — zero new parameters.
This is the cheap standalone analogue of the OPT paper's per-agent
utility-network omega_a. Return signature change means all call sites must be
updated; keep the old 5-tuple unpacking working via a config-gated return or
update every site explicitly (prefer explicit update; there are ~4 sites).

### A3. High-level input wiring

When enabled, the high policy input for agent i gains:
`[omega (N)] + [rel_i (N) if use_agent_prototype_relevance]`.
Applies to `logits`, `evaluate`, and the act/assign path identically —
grep every `self.high.` call site including `_bootstrap_high_values` and the
GInfo objective's enumeration path (which must pass zeros or the true omega
consistently; choose true omega).

### A4. Part A metrics (CSV + TB + console, following G_INFO plumbing pattern)

```text
proto_skill_selection_entropy        overall H(pi_h)
proto_skill_usage_entropy_by_kappa   mean over kappa classes of H(z | kappa)
proto_skill_relevance_alignment      I(z_i ; argmax rel_i) per update
proto_omega_nonzero_frac             sparsemax sparsity health
proto_bank_drift_cos                 mean cosine(live prototypes, EMA bank)

J3-calibration bundle (logged from s1_probe; Stage 2 constants read off these):
proto_rel_row_entropy_mean           per-agent relevance sharpness
proto_rel_argmax_dwell_median        per-agent dwell of argmax rel_i (checks)
proto_rel_stability_cos              cos(rel_i[t], rel_i[t-1]) mean
proto_rel_drop_event_rate            rate of argmax-relevance falling below a
                                     provisional threshold (log at 0.5/0.3/0.1
                                     so Stage 2 can pick without rerunning)
```

Collapse alarms (log-only, no auto-action in Stage 1):
`proto_skill_usage_entropy_by_kappa` near 0 = situation->skill lookup
collapse; `proto_omega_nonzero_frac` near 1/N = prototype collapse.

## Part B — Per-step individual discriminator (Job 5, surviving half)

### B1. Module: `ha_ctse_process/prototype_response_discriminator.py`

```text
class PrototypeResponseDiscriminator(nn.Module):
    q_d(z_i | o_next_i, cond)     main head, MLP
    cond = one of {kappa one-hot, omega vector, none}   (config knob)
           optionally + rel_i when use_agent_prototype_relevance

    update(batch) -> metrics:
        CE(q_d) on executed ACTIVE skill labels per primitive step
        on-policy, current rollout only

    reward(batch) -> per-step per-agent (R15 coordinator-residual form):
        r_i = log q_d(z_i | o_next_i, cond) - logpi_h_stored(z_i)
        clip to [-prototype_disc_clip, +prototype_disc_clip]

    logpi_h_stored(z_i) = the assignment log-prob of the ACTIVE skill under
    the AR selection head, log pi_h(z_i | kappa, z_{1:i-1}, ...), captured at
    assignment time and BROADCAST constant over that skill's lifetime steps.
    There is NO learned prior head — the sequential coordinator is the null
    model (derivation: memory/R15_steering_objective_derivation.md §5; this
    is HMASD Eq. 3's diversity + skill-entropy pair fused pointwise).
```

Contract points:
- LABEL = the ACTIVE skill at that primitive step (well-defined under variable
  lifetimes; never a candidate skill from a no-edit check — same trap as the
  old candidate-label bug, assert against it in a unit test).
- NULL = the stored AR assignment log-prob, NOT a learned prior and NOT
  p(z). This is stronger than the R14.1 kappa-conditioned prior: the null IS
  the usage distribution (usage-imbalance immunity by construction) AND it
  prices in teammates' choices (a predictably duplicated response earns low
  reward -> anti-duplication for free). Requires
  use_autoregressive_selection; if --parallel_selection is set, fall back to
  the kappa-conditioned prior head and LABEL the run as the R15-P1 ablation.
- MOVING-NULL watch: as pi_h sharpens the reward shrinks (annealing
  feature / self-extinction risk). Log the reward trajectory; red flag in
  the readout table.
- Inputs strictly: o_next, kappa/omega/rel. No reward fields, no comm fields,
  no duration, no segment length. The structural duration-shortcut immunity
  comes from the per-step form; do not reintroduce segment features.
- CE trains only the heads; the REWARD is what trains the policy (HMASD
  separation, per the g-revival precision note in ALGORITHM_PRINCIPLES).

### B2. Config / CLI

```text
enable_prototype_disc_probe = False    train heads, log metrics, NO reward
enable_prototype_disc_reward = False   requires probe flag on
prototype_disc_reward_coef = 0.1
    DELIBERATELY bootstrap-scale (R11.3 / R14 split: bootstrap pressure must
    be dense and non-negligible; this is not a 0.02 purity-scale term).
    Log the ratio r_disc_mean / env_reward_mean every update so scale is
    visible from update 1 — the P4-1b lesson.
prototype_disc_clip = 2.0
prototype_disc_warmup_steps = 20000
prototype_disc_condition = "kappa"     kappa | omega | none (ablation knob)
prototype_disc_lr = 5e-4
prototype_disc_null_mix_beta = 0.0
    R17 mitigation for moving-null self-extinction (DEFAULT OFF; activate
    ONLY if the self-extinction red flag fires): null becomes
    log[(1-beta)*pi_h(z_i|...) + beta/n_skills], beta ~ 0.1.
    Caveat: mixing breaks exact null=usage-distribution, so a small
    usage-imbalance sensitivity returns — keep beta small and log
    proto_disc_null_mix_active.
```

Injection: low_only, added to the per-step low-level reward exactly where
`transition_skill` reward used to inject (same tensor shape/path), guarded by
both flags + warmup. High-level returns remain pure env return.

### B3. Part B metrics

```text
proto_disc_acc
proto_disc_null_logp_mean              mean stored log pi_h of active skills
proto_disc_residual_mean               log q_d - log pi_h, pre-clip
proto_disc_residual_positive_frac
proto_disc_acc_by_skill_std            behavioral separation spread
proto_disc_reward_applied_steps        0 unless reward flag + warmup passed
proto_disc_reward_env_ratio            |r_disc mean| / |r_env mean|
proto_ar_parallel_kl                   KL(AR selection dist || parallel dist
                                       recomputed without z_{1:i-1}); ~0
                                       means the sequence coordinates nothing
```

## Part C — Compact grounding head (recommended, small)

One linear head on compact predicting the n-step (use rollout-available)
discounted return; MSE aux loss, coefficient `compact_return_coef = 0.1`,
metric `compact_return_loss`. This is the L_TD analogue from R14.0 — the
paper's grounding condition. Config `use_compact_return_head = False`.
If cut for scope, cut this, not A or B.

## Experiment pre-registration (create ExpRecord entry BEFORE running)

`EXP-2026070X-r14-stage1-prototype-selection`, local CUDA, 16 env, 320k,
seed 1 first then seed 2 if gate-relevant. Arms:

```text
control      reward-pure diag_only (existing arm, rerun or reuse matched-step)
s1_probe     Part A on + Part B probe on, NO reward
s1_reward    s1_probe + enable_prototype_disc_reward (coef 0.1)
```

Gates (pre-committed):

```text
PASS requires, s1_reward vs control at matched steps:
  forced-z trajectory spread UP (reuse P3-2e / effect_intervention machinery)
  proto_disc_residual_mean > 0 sustained (last-third mean)
  proto_skill_usage_entropy_by_kappa not collapsed (> 50% of uniform)
  task metrics not regressed (coverage, zero-throughput frac, reward_std/mean)

STOP rules:
  proto_disc_acc ~ proto_disc_prior_acc persistently
    -> skills not behaviorally separable; fix selection conditioning (A3
       inputs, actor skill-conditioning capacity) BEFORE raising the coef.
  s1_reward regresses task metrics vs control
    -> halve coef once; if still regressing, stop and read — do not sweep.
  Do not conclude from reward_mean alone (standing rule).
```

## Primary readout table (what to read, when, and red flags)

Read at 160k and 320k; decide on last-third update means; never on a single
update or reward_mean alone.

```text
TRAIN CSV (train_updates.csv), all arms:
  proto_skill_selection_entropy, proto_skill_usage_entropy_by_kappa,
  proto_skill_relevance_alignment, proto_omega_nonzero_frac,
  proto_bank_drift_cos, proto_rel_* (J3 bundle),
  proto_disc_acc, proto_disc_prior_acc, proto_disc_residual_mean,
  proto_disc_residual_positive_frac, proto_disc_acc_by_skill_std,
  proto_disc_reward_applied_steps, proto_disc_reward_env_ratio,
  compact_return_loss (if Part C on),
  reward guards: process/force/effect/topology low rewards must stay 0.0 in
  control and s1_probe; only proto_disc reward may be nonzero in s1_reward.

EVAL (eval summaries), all arms:
  coverage_eq1_step_fraction, coverage, qos, throughput,
  zero_throughput_episode_fraction, throughput_gt5_step_fraction,
  reward_mean, reward_std/reward_mean.

BEHAVIORAL (existing machinery):
  forced-z trajectory spread (P3-2e / effect_intervention path) —
  between/within spread ratio at h in {10, 50}, s1 arms vs control.

RED FLAGS (any of these = stop and read, do not extend the run):
  proto_disc_reward_env_ratio > 1.0      disc reward dominating env return
  proto_disc_residual_mean -> 0 while forced-z spread stays flat
                                         moving-null self-extinction (R15
                                         risk): pressure died before skills
                                         separated
  proto_skill_usage_entropy_by_kappa < 50% uniform   situation->skill lookup
  proto_bank_drift_cos < 0.9             semantics drifting under EMA
  proto_omega_nonzero_frac ~ 1/N         prototype collapse
  eval bimodality worsening vs control (zero_throughput_ep_frac up)
```

## Follow-up experiment templates (pre-registered, trigger-conditional)

Create the ExpRecord entry when the trigger fires; do not launch early.

```text
EXP-r14-stage2-commitment-validity
  TRIGGER: s1_probe read complete AND proto_skill_relevance_alignment above
    a pre-set floor (commit the floor in the ExpRecord entry before reading;
    suggested: significantly above the shuffled-label null).
  ARMS: diag_only | commitment-validity hazard (J3, constants from the J3
    bundle) | random_matched forced renewal at the SAME rate (carried over
    from the R13 review — without it a neutral hazard result is
    uninterpretable).
  GATE: hazard arm beats BOTH diag_only and random_matched on task metrics
    with per-agent lifetime heterogeneity nontrivial.

EXP-r14-stage3-coverage
  TRIGGER: full Stage 1 gate pass (forced-z spread + no task regression).
  ARMS: stage-2 best | + coverage/repulsion bonus (J4 tier 1).
  GATE: redundant-docking rate down, high-omega prototype coverage up, task
    metrics not regressed.

EXP-r14-stage4-team-transition
  TRIGGER: stages 2-3 in place and read.
  ARMS: stage-3 best | + team transition reward (smallest coefficient).
  GATE: task metrics and stability, never classifier metrics.

s1_reward OUTCOME MATRIX (decides Stage-1 exit):
  separation UP + task neutral/up   -> proceed to Stage 2 trigger check.
  separation UP + task DOWN         -> halve coef once; if still down, keep
                                       probe-only and move weight to P2/P4
                                       parallel reads before any Stage 2.
  separation FLAT + task neutral    -> conditioning/capacity problem: fix A3
                                       inputs or actor skill-conditioning
                                       (P3-2e finding) BEFORE any coef sweep.
  separation FLAT + task DOWN       -> revert reward arm; substrate or
                                       selection design is wrong — re-read
                                       s1_probe and P1 dwell data before
                                       touching anything else.
```

## Validation checklist (project convention)

```text
py_compile / AST parse on all touched files
new unit tests: label-is-active-skill assertion, stored-null broadcast
  (log pi_h captured at assignment, constant over lifetime, refreshed on
  renewal), AR log-prob storage per agent, EMA bank update, encoder 6-tuple
  return shapes, reward path zero when flags off
smoke run with probe on: reward guards zero, new CSV fields present
tiny train: checkpoint save -> load -> resume with new input dims (metadata)
runner: new arms in scripts/run_r12_stage1_local_cuda.ps1 or a sibling
  runner; -DryRun passes
memory sync per LongTaskMemo after implementation
```

## Sequencing / dependency map for the remaining jobs

```text
J3 commitment + validity hazard:
  needs the s1_probe READ (not the reward gate): rel_i sparsity/stability
  distributions, per-agent prototype dwell, and proto_skill_relevance_alignment
  calibrate the validity threshold and stall window. If relevance_alignment
  ~ 0, J3's trigger loses its signal source -> redesign before building.
J4 coverage complementarity:
  needs the FULL Stage 1 gate (forced-z spread passed). Coverage of
  prototypes by skills that do not behaviorally differentiate is label
  bookkeeping, not coordination.
Stage 4 team transition reward:
  after J3 + J4 by construction (xi undefined until commitment and
  assignment semantics exist).
Discipline rule: implement-behind-flags != enable-and-judge. Hold J3/J4 CODE
until the probe read exists (one overnight run) — the P3-4 lesson: building
before reading premises cost weeks of rework.
```

## Parallel track — four items with NO Stage-1 dependency (start now)

These run alongside `s1_probe`; none of them consumes a Stage-1 result.

### P1. Per-agent situation kappa_i (R13-Q6 structural fix)

```text
Purpose: R12-1a tested global-kappa-triggered near-synchronized renewal, not
  the per-agent situation-validity hazard the R12 contract specifies.
Deliverable: extend situation_substrate.py to compute kappa_i per agent from
  the agent-local relevance row rel_i (Part A2 output):
    kappa_i = assign-kappa logic applied to rel_i instead of global omega,
    tracked per (env_id, agent_id) with the existing dwell/debounce tracker.
  Keep global kappa computed alongside (do not remove).
Config: use_per_agent_kappa = False (default off).
Metrics: per-agent kappa dwell distribution, cross-agent kappa disagreement
  rate, I(kappa_i ; kappa_global), per-agent situation_change frac.
Note: depends MECHANICALLY on Part A2 (agent_relevance exists) but on no
  experiment read; implement together with Part A.
Read: per-agent dwell heterogeneity across roles is the design's motivating
  signal — if kappa_i dwell is homogeneous across agents, record that
  honestly; it weakens the per-agent-lifetime premise.
```

### P2. Recognition-Z HMASD control (R14.0 decisive experiment)

```text
Purpose: settle commitment-vs-context — the load-bearing assumption of the
  entire recognition-first program.
Deliverable: an HMASD-original VARIANT (hmasd/ path, via
  train_multiproc_config_1.py algorithm registry; do not touch
  ha_ctse_process): replace the sampled team skill Z with a RECOGNITION:
    fit a frozen codebook (e.g. k-means, n_Z clusters) on global states from
    an early rollout buffer; at each k-boundary set Z := cluster(s_t).
  Disable the team discriminator reward (lambda_D = 0) — it is vacuous under
  recognition (H(Z|s)=0). KEEP the individual discriminator conditioned on
  the recognized Z. Everything else unchanged.
Arms: hmasd_original vs hmasd_recognition_Z, S7-S1, matched settings,
  2 seeds, matched budget.
Read (pre-committed):
  recognition-Z retains most of original's performance
    -> shared context is what matters; the substitution is sound in
       principle; kappa* commitment layer is optional.
  recognition-Z collapses
    -> commitment is load-bearing; OPT can only be the substrate BENEATH a
       commitment layer; kappa* (target situation) becomes MANDATORY and
       moves up the build order.
```

### P3. HMASD current-env gap re-verification (owed since Stage 0)

```text
Purpose: the program's motivating premise — "HMASD ~solves S7-S1, fails
  S7-S3" — was read months ago; env code (energy model, routing, packet sim,
  mobility) changed substantially since.
Deliverable: run hmasd_original on TODAY's S7-S1 and S7-S3, 2 seeds each,
  budget at or near the 1e6-step parity scale.
Read: S7-S1 against the coverage==1.0 half-step parity criterion (this
  re-anchors the target number every gate references); S7-S3 failure profile
  documented. If the gap moved, the framing and target metrics move with it —
  update ALGORITHM_PRINCIPLES benchmark section accordingly.
```

### P4. G-ACTIONABILITY offline gate (adjudicates the pending R12-1b line)

```text
Purpose: G-DWELL/G-OUTCOME/G-ROLE validated kappa as a STATE descriptor;
  renewal uses kappa-change as an EVENT trigger — the untested claim.
Deliverable: extend the substrate-gate analyzer (substrate_gate.py /
  export_substrate_gate.py) with two offline reads over existing logs and
  checkpoint dumps:
  (a) decision divergence: JS divergence of the high-level decision
      distribution across kappa classes, vs a shuffled-kappa null;
  (b) boundary value: segment returns following skill switches ALIGNED with
      kappa boundaries vs NON-aligned switches, matched on skill age.
  Append both to substrate_gate_report.json with pass thresholds.
Read: if neither (a) nor (b) clears its null, kappa boundaries carry no
  decision-relevant information -> no guard tuning (R12-1b) can rescue
  boundary-triggered renewal; keep kappa as conditioning context only and
  fall back per the pre-registered substrate decision tree.
```

## Fidelity notes for Codex

- The two design authorities are R14.1 in `memory/cross_validation.md` and
  this spec; where they differ, this spec wins (it is grounded in current
  code shape).
- The vacuity constraint means: never add a head predicting kappa from s —
  it is trivially perfect and any reward built on it is dead weight.
- Keep Part B's discriminator OUT of the encoder's gradient path
  (detach compact/omega/rel inputs to q_d and prior) so semantic pressure
  flows through behavior (the reward), not through representation shortcuts.
  This mirrors HMASD: the discriminator observes; the policy earns.
