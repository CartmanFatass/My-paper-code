# HA-CTSE Current Work

Updated: 2026-07-13

Purpose: the single mandatory first read. Current state only. History lives in
`memory/LTM/`; the staged plan lives in `memory/IMPLEMENTATION_PLAN.md`; run
facts live in `memory/ExpRecord.md`. Keep this file under ~150 lines.

## Controller Handoff

- **Active controller:** Codex, branch `aggressive`, traditional HMASD
  R24/R25/R26/R27/R28 line. One controller may modify the repo at a time.
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
- **Shared GPU scheduling (2026-07-13):** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9` and automation `hmasd-r27-g2` are the
  sole IMOD/HMASD GPU lease controller. This research task packages and
  interprets HMASD work, but does not reuse an old SSH snapshot to claim
  occupancy or launch compute. A future authorized job must be registered in
  the scheduler with its exact committed contract before it becomes `READY`.

## Current Objective

**Open causal edge: `distinct z_i -> naturally expressed, behaviorally
differentiated skills`.**

- **R27-G2 complete, accepted** as `PASS_BEHAVIOR_EFFECT` on 2026-07-13.
  Run `095408`/`6c06cde` completed at 16:04 +08:00 with 192/192 `OK`
  decision shards, 64 resets at each of update25/update30/final, successful
  aggregate validation, and A/B1/B2/B3/C PASS at all three checkpoints.
- The accepted claim is narrow: the frozen R25 arm0 low actor supports
  persistent label-conditioned action processes and a separate local effect
  under forced hold through native H40. Record this beside the R26 natural
  observational negative as `FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`.
- **R26-G1a remains negative** for its tested natural windows. R27 does not
  retroactively convert it into instrument failure or establish natural skill
  selection, reward usefulness, cooperation, credit, or task improvement.
- The stopped `085445` run's 11 partial shards and the quarantined pilot remain
  excluded from decision evidence.
- Longer-term: reach HMASD-level S7-S1 behavior at ~1e6 steps before returning to
  S7-S3. Treat 160k/320k runs as mechanism gates, not HMASD-comparison verdicts.

## Active Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — research contract (incl. the active R22
  two-clock contract, and the causal-discipline / baseline-hierarchy /
  promotion-ladder rules).
- `memory/IMPLEMENTATION_PLAN.md` — staged plan and current gates.
- `memory/ExpRecord.md` — experiment dashboard and artifact locations.
- `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md` — the
  frozen R27-G2 design and outcome branches.
- `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md` — the
  frozen R28-G0 target/null contract and accepted G1 implementation freeze.
  The code/test/runner package is complete. The current authorization is one
  bounded local engineering smoke; formal reward training and remote topology
  execution remain unauthorized.
- `docs/external-review/R27_G2_design_review_20260712_Claude.md` — raw external
  review. Exact Claude model/version was not supplied, so provenance is
  incomplete and recorded as such.
- `memory/R22_TWO_CLOCK_ELBO.md`, `memory/R22_TARGET_ENTROPY_DESIGN.md`,
  `memory/R23_ACTIONABLE_TEAM_INTENT.md` — derivations behind the contract.

## Current Experiment Focus

`EXP-20260713-r28-g1-causal-skill-forcing-reward` — **implementation complete;
local engineering smoke authorized; formal training not authorized**.

- Candidate target: fixed 10-step deterministic-action process residual over
  capacity-matched context, pre-window, and sham-label nulls. No communication
  field, environment reward, Gate-C observation effect, `q_A`, `q_d`, or `q_D`
  enters the intrinsic score.
- G0 remains accepted `PASS_TARGET_NULLS`; its scorer at
  `logs/r28_g0_action_process_target_20260713_175600/r28_g0_scorer_final.pt`
  is the sole frozen target/null input.
- G1 now has exact same-forward deterministic-action capture, frozen scorer and
  actor-base checkpoint continuity, natural episode/update clocks, common
  support and sham grouping, final-ten-step low-only reward attribution,
  fail-closed guards, unchanged R26 evidence plus sidecar, family analyzer, and
  a parallel data-disk Bash runner.
- No topology check or formal G1 training has run. The earlier remote job
  `HMASD-R28-G1-TOPOLOGY-20260713-195737` was superseded before scheduler
  registration or execution; it remains at zero steps and may not launch.
- The next action is one direct local `real_reward` engineering smoke: seed
  28030, one sync CUDA environment, 500 steps/one PPO update, no evaluation,
  expected 2-5 minutes. Existing trainer manifest/CSV/checkpoint are sufficient;
  its checkpoint is non-resumable and it creates no scientific/topology claim.

Other than the planned, execution-closed G1 row, the dashboard is `completed`
or `standing-reference`. R25 arm0/arm2 and the HMASD baseline (REF-20260617)
are **fixed comparison data**.

## Next Actions

1. Retrieve the accepted frozen G0 scorer when the server is reachable, then
   run the direct local one-update smoke and read its existing manifest, update
   CSV, and final checkpoint once.
2. Treat the smoke only as implementation evidence. A later formal launch still
   requires separate user authorization and a matching remote three-worker
   topology validation through the shared scheduler.
3. Preserve the R28-G0 scorer/result as the only target/null input; do not
   refit, retune, or sweep the classifier.
4. Preserve R27-G2 as forced causal capacity and R26 as a natural observational
   negative. Do not merge the claims.

## Do Not Do Yet

- Do not reinterpret R27-G2 as natural skill usage, team complementarity,
  reward usefulness, task improvement, or decoupled-lifetime evidence.
- Do not enable or tune the old `q_d/q_D` reward paths; R24-1 still blocks them.
  `q_A` remains default-off after the R25 task regression.
- Do not turn Gate C, raw communication/service/topology fields, or environment
  reward into the R28 intrinsic target.
- Do not execute the cloud runner's `topology`, `run`, `evidence`, `analyze`, or
  `all` modes. The local smoke does not authorize formal training.
- Do not re-run standing references (user directive 2026-07-10): the HMASD
  baseline (REF-20260617) and the R25 arm0/arm2 arms. Reuse the archived
  curves/checkpoints. Exceptions need explicit user approval.
- Do not add kappa/hazard/DADS, team reward, or communication-intrinsic
  mechanisms while the individual differentiation gate is open.
- Do not execute the superseded CSOG roadmap or Phase-A/G0 plan.

## LTM Archive Pointers

- `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md` — completed/superseded
  plan rounds (Decoupled-K, R12, R19, R20, R21, R22 receipts, June-2026 passes).
- `memory/LTM/EXPERIMENT_ARCHIVE.md` — long-form detail for completed experiments
  (R27-G2/G1, R26-G1a, R25, R24, R23).
- `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` — raw external-review text
  (the evidence; summaries are only indexes). `INDEX.md` is the round index.
- `memory/LTM/PROJECT_HISTORY_20260707_full_import.md`,
  `EXPERIMENT_RECORD_20260707_full_import.md`,
  `CROSS_VALIDATION_20260707_full_import.md`, `CROSS_VALIDATION_ARCHIVE.md` —
  pre-compaction full imports.
