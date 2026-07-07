# HA-CTSE Current Work

Updated: 2026-07-07

Purpose: compact first-read state for the current work only. Full historical
context is archived under `memory/LTM/`.

## Current Objective

- Reach HMASD-level S7-S1 behavior at roughly 1e6 steps before returning to
  S7-S3.
- Treat 160k/320k runs as mechanism gates, not final HMASD-comparison verdicts.
- Current main line: R23-next actionability. The q_A residual path is replacing
  the weak g-info path; q_D remains reward-off until a non-chance effect target
  is found.

## Active Principle Pointers

- `memory/ALGORITHM_PRINCIPLES.md`: current HA-CTSE research contract.
- `memory/R23_ACTIONABLE_TEAM_INTENT.md`: R23 actionability design and forward
  plan, especially the q_A residual and q_D target audit notes.
- `memory/R22_TWO_CLOCK_ELBO.md`: two-clock objective framing.
- `memory/R22_TARGET_ENTROPY_DESIGN.md`: entropy design constraints.

## Active Plan Pointers

- `docs/superpowers/plans/2026-07-06-r23-next-actionability.md`: accepted
  R23-next implementation and experiment matrix plan.
- `memory/IMPLEMENTATION_PLAN.md`: staged plan ledger and current gates.
- `memory/ExpRecord.md`: compact current experiment dashboard.

## Current Experiment Focus

- `EXP-20260707-r23-next-mechanism-matrix` — COMPLETE (local 16env, single seed), mixed verdict.
  - **q_A actionability pivot VALIDATED.** arm1 probe residual_gain 0->+0.097; arm2 q_A
    REWARD residual_gain ->+0.222 with forced-Z KL RISING 0.059->0.070 and Z-usage healthy.
    This decisively fixes the g-info failure (T2 gradient audit: g-info grad <2% of PPO,
    self-stalling). Z->xi is now an established, learnable mechanism.
  - **arm3 q_D target audit = NULL.** All of {s_next, joint_action, joint_effect,
    delta_omega} x H{10,20,50} collapse to the marginal baseline by u38 (residual_gain ~0).
    No effect space recovers Z; consistent with team_disc-at-chance. CAVEAT: underpowered
    probe (~1 grad step/update over high-dim targets; context-free baseline) => "no signal
    found", not "proven absent".
  - Task: NOISE-DOMINATED at this depth/seed — coverage@160k across arms spans 0.063
    (arm1) / 0.10 (arm0) / 0.192 (arm3) / 0.303 (arm2), and arm3 even declined 0.192->0.082
    by 320k, despite reward-off/probe arms having ~identical policies (RNG-desync variance).
    So arm2's "3x coverage" is most likely favorable variance, NOT a q_A-reward task gain.
    No reliable task signal without matched-env multi-seed runs. The q_A MECHANISM result
    (per-arm-internal residual_gain trend) is unaffected and stands.
  - CHAIN STATUS: Z->xi established+learnable; xi->recoverable-joint-effect still open.
  - INFRA: local 32env OOMs on the 31.6GB box (both earlier kills were OS OOM, not code);
    use 16env local or 64env cloud. Full detail in `memory/ExpRecord.md`.

## Next Actions

1. Frontier has moved to `xi -> behavior -> recoverable effect`. Next lever is the
   individual-skill/discoverer half (does z_i actually differentiate low-level behavior --
   GPT "Reason B") and/or a STRONGER q_D probe (more head epochs/update + a context-
   conditioned prior baseline, not context-free), NOT more q_D target engineering.
2. Optional: cloud 64env matched rerun of the matrix (both seeds) for a non-confounded
   task read and a clean arm2 320k eval.
3. Only after a q_D target beats a context-conditioned baseline, decide on a q_D reward arm.

## Do Not Do Yet

- Do not enable q_D reward before arm3 finds a non-chance target.
- Do not launch 960k or seed2 depth for the weak g-info coefficient line.
- Do not add new kappa/hazard/DADS/communication-intrinsic mechanisms before
  the q_A/q_D actionability question is resolved.

## LTM Archive Pointers

- `memory/LTM/PROJECT_HISTORY_20260707_full_import.md`: full
  historical project state imported from the former long pointer.
- `memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`: full previous
  experiment record imported before compaction.
- `memory/LTM/CROSS_VALIDATION_20260707_full_import.md`: full previous
  cross-validation ledger imported before compaction.
- `memory/LTM/EXPERIMENT_ARCHIVE.md`: future append-only experiment conclusion
  archive maintained by ExpManager.
- `memory/LTM/external_reviews/INBOX.md`: template-preserving paste area for
  Claude, GPT-5.5 Pro, and Gemini review dialogue.
- `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md`: newest-first detailed
  external review dialogue archive.
- `memory/LTM/external_reviews/INDEX.md`: newest-first lightweight review-round
  index.
