# HA-CTSE Current Work

Updated: 2026-07-13

Purpose: the single mandatory first read. Current state only. History lives in
`memory/LTM/`; the staged plan lives in `memory/IMPLEMENTATION_PLAN.md`; run
facts live in `memory/ExpRecord.md`. Keep this file under ~150 lines.

## Controller Handoff

- **Active controller:** Codex, branch `aggressive`, traditional HMASD
  R24/R25/R26/R27 line. One controller may modify the repo at a time.
- **Binding protocol:** `docs/subagents/claude-codex-handover-spec.md`. Read it
  at every switch and update this block when ownership changes.
- **Workflow status (2026-07-13):** the delegated-subagent workflow is retired.
  The controller works directly. Do not reconstruct the old dispatch-gate,
  model-tier-routing, review-package, or agent-lifetime rules from historical
  files; `AGENTS.md` is the authority. Archived detail:
  `memory/LTM/codex-subagent-workflow-skill-backup-20260708.md`.
- **Versioning (2026-07-12):** Git is the sole source-version manager. Active
  code and operations add no content-digest/checksum layer. Immutability checks
  compare typed values; derived reports are rebuilt from current inputs.
- **IMOD** is a separate project at `C:\project\IMOD` (own Git history). Its
  design state is **not** evidence for this line and does not block it.

## Current Objective

**Open causal edge: `individual skill z_i -> persistent executable behavior`.**

- **R27-G1 complete, accepted** as `STATIC_USED_OBSERVATIONAL_MISS`, qualified
  narrowly: the frozen low actor has *immediate* `z_i`-conditioned
  action-distribution separation (static PASS 3/3 checkpoints, synthetic PASS 3/3
  seeds). This does **not** establish persistent trajectory modes or downstream
  effects.
- **R26-G1a** remains a valid negative for its tested observational windows, but
  after R27 it can no longer be read as "the actor lacks immediate `z_i`
  capacity".
- **R27-G2** (forced-`z_i` trajectory/effect intervention) is design-frozen,
  implemented, and locally verified. The active remote workflow now uses a
  clean Git checkout rather than a deployed ZIP. **Pilot and decision-grade
  launch are not authorized** and each need a separate explicit decision.
- Longer-term: reach HMASD-level S7-S1 behavior at ~1e6 steps before returning to
  S7-S3. Treat 160k/320k runs as mechanism gates, not HMASD-comparison verdicts.

## Active Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — research contract (incl. the active R22
  two-clock contract, and the causal-discipline / baseline-hierarchy /
  promotion-ladder rules).
- `memory/IMPLEMENTATION_PLAN.md` — staged plan and current gates.
- `memory/ExpRecord.md` — experiment dashboard and artifact locations.
- `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md` — the
  controller-frozen R27-G2 design (design evidence only; authorizes nothing).
- `docs/external-review/R27_G2_design_review_20260712_Claude.md` — raw external
  review. Exact Claude model/version was not supplied, so provenance is
  incomplete and recorded as such.
- `memory/R22_TWO_CLOCK_ELBO.md`, `memory/R22_TARGET_ENTROPY_DESIGN.md`,
  `memory/R23_ACTIONABLE_TEAM_INTENT.md` — derivations behind the contract.

## Current Experiment Focus

`EXP-20260712-r27-g2-forced-z-trajectory-effect` — **planned / design-frozen**.

- 55 branches per reset, 64 reset groups, 3 frozen temporal checkpoints.
- Decision-grade Stage 1 is exactly **2,124,000 env steps** before diagnostic
  overhead: **12–20 h on cloud CUDA**. Planning facts only — nothing launched.
- The primary control is **hold vs a matched 10-step pulse**, not raw closed-loop
  divergence. Gated windows are steps 1-10, 11-20, 31-40 (native R25 durations
  are 10/20/30/40). H50 is descriptive stress, not native-duration evidence.
- Targeted local verification is complete; the remote-workflow subset passes
  10/10, including Windows PowerShell 5.1 native-argument transport into Bash.
- Non-launching Git-based cloud `prepare` passed on 2026-07-13. The clean
  data-disk checkout is at commit `60ac83e`, its two-line source pointer is
  Bash-readable, all three checkpoints are cached, and the 192-reset dry-run
  wrote no run directory. No R27 `screen` or scientific run exists.
- User execution policy (2026-07-13): compute-bearing experiments default to
  parallel cloud CUDA. R27-G2 defaults to 64 reset workers; serial launch and
  serial fallback are disabled. The exact parallel topology still requires a
  bounded validation before launch.
- `launch`/`all` remain fail-closed behind explicit experiment authorization.

Everything else on the dashboard is `completed` or `standing-reference`. R25
arm0/arm2 and the HMASD baseline (REF-20260617) are **fixed comparison data**.

## Next Actions

1. Hold. R27-G2 implementation and non-launching cloud preparation are
   complete. Before compute, separately validate a safe concurrent process/GPU
   topology and obtain an explicit pilot or decision-grade launch decision. A
   pilot is <90k steps and cannot contribute to the gate; decision grade is
   2.124M steps and 12–20 h cloud CUDA only with the validated flattened queue.
   Do not invoke guarded `launch`/`all` under the present authorization.
2. Preserve the R27-G1 qualification: immediate action sensitivity verified;
   persistence and downstream effect open. Preserve the R26 FAIL narrowly.
3. Optional cheap diagnostics may reuse existing R25 artifacts (correlate q_A
   reward share / residual gain with task metrics; offline-score arm0 vs arm2
   with the frozen q_A discriminator). No new run needed.
4. The update-matched parity question may later use a 1M/32env cloud run via the
   cloud-handoff protocol. Needs its own approval; must not duplicate a
   standing-reference control.
5. D2 stays approved-deferred: archival sensitivity analysis only, separate
   validation split, identical stopping rules, all outcomes reported, one all-GPU
   device class, and **no reward unblocking even on an unexpected pass**.

## Do Not Do Yet

- Do not treat R27-G1 static separation or synthetic `1.0` accuracy as evidence of
  persistent trajectory modes, downstream effects, cooperation, credit, or task
  improvement.
- Do not launch or pilot R27-G2 without separate explicit authorization.
- Do not enable `q_A`, `q_d`, `q_D`, or any other intrinsic reward while the
  persistent-behavior edge is open. `q_d`/`q_D` are **BLOCKED** by R24-1
  (FAIL accepted 2026-07-09); no q_D/q_d coefficient sweeps or target engineering.
- Do not redesign the actor, reset recurrent hidden state, or add post-GRU
  FiLM / action-head residuals.
- Do not re-run standing references (user directive 2026-07-10): the HMASD
  baseline (REF-20260617) and the R25 arm0/arm2 arms. Reuse the archived
  curves/checkpoints. Exceptions need explicit user approval.
- Do not launch a long task-scale or update-matched parity run as a response to
  R27-G1 — it does not resolve whether immediate sensitivity becomes persistent
  behavior.
- Do not add new kappa/hazard/DADS/communication-intrinsic mechanisms while this
  edge is open.
- Do not execute the superseded CSOG roadmap or Phase-A/G0 plan.

## LTM Archive Pointers

- `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md` — completed/superseded
  plan rounds (Decoupled-K, R12, R19, R20, R21, R22 receipts, June-2026 passes).
- `memory/LTM/EXPERIMENT_ARCHIVE.md` — long-form detail for completed experiments
  (R27-G1, R26-G1a, R25, R24, R23).
- `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` — raw external-review text
  (the evidence; summaries are only indexes). `INDEX.md` is the round index.
- `memory/LTM/PROJECT_HISTORY_20260707_full_import.md`,
  `EXPERIMENT_RECORD_20260707_full_import.md`,
  `CROSS_VALIDATION_20260707_full_import.md`, `CROSS_VALIDATION_ARCHIVE.md` —
  pre-compaction full imports.
