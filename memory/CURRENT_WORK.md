# HA-CTSE Current Work

Updated: 2026-07-09

Purpose: compact first-read state for the current work only. Full historical
context is archived under `memory/LTM/`.

## Current Objective

- Reach HMASD-level S7-S1 behavior at roughly 1e6 steps before returning to
  S7-S3.
- Treat 160k/320k runs as mechanism gates, not final HMASD-comparison verdicts.
- Current main line: R24 Assignment-to-Behavior Bridge. R23-next validates the
  q_A residual path as high-level `Z -> xi` actionability, not full behavioral
  closure.
- Current state update: completion of R24 frozen q_d null-probe core Tasks 1-4 after
  full review chain:
  - Added `ha_ctse_process/r24_qd_dataset.py` with detached `q_d` window export
    to `<log_dir>/r24_qd_windows` (npz shards) for `r24_qd_export_windows`.
  - Added `scripts/analyze_r24_qd_frozen_nulls.py` with frozen null variants:
    `real`, `shuffled`, `fake_marginal`, `duration_matched`, `agent_matched`,
    `behavior_only`, `pre_only`, `action_only`, `effect_only`.
  - Implemented grouped null semantics without cross-group fallbacks; verified in
    `tests/r24_qd_frozen_nulls_test.py`.
  - Verification: `pytest tests\r24_qd_frozen_nulls_test.py -q` (5 passed),
    `pytest tests\r24_team_conditioned_qd_test.py tests\r24_qd_frozen_nulls_test.py -q`
    (18 passed), and implementation re-review approved.
  - No `q_d`/`q_D`/`team_disc` reward path was enabled or altered.
- Runner path is complete with frozen-null support:
  `scripts/run_r24_qd_null_control_cloud_64env.sh` supports optional
  `EXPORT_QD_WINDOWS=1` and `RUN_FROZEN_NULL_ANALYSIS=1`.
  Launch command:
  `EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh`
  and `EXP-20260709-r24-frozen-qd-null-probes` is marked launch-ready in
  `memory/ExpRecord.md`.
- Reward remains blocked (no q_d/q_D reward yet) until matched-null/round-3 gates pass.

## Active Principle Pointers

- `memory/ALGORITHM_PRINCIPLES.md`: current HA-CTSE research contract.
- `memory/R23_ACTIONABLE_TEAM_INTENT.md`: R23 actionability design and forward
  plan, especially the q_A residual and q_D target audit notes.
- `memory/R22_TWO_CLOCK_ELBO.md`: two-clock objective framing.
- `memory/R22_TARGET_ENTROPY_DESIGN.md`: entropy design constraints.
- `docs/superpowers/plans/2026-07-08-r24-frozen-qd-null-probes.md`: frozen
  same-capacity q_d null-probe diagnostics for cloud-gate continuation.

## Active Plan Pointers

- `AGENTS.md`: project-level Codex entrypoint; read before relying on deeper
  docs or historical memory. It defines the main-controller protocol,
  controller communication contract (situation, meaning, next plan,
  recommendation, core MARL impact, and open gates/blockers must be stated
  proactively for experiment/result/plan transitions),
  official `.codex/config.toml` / `.codex/agents/*.toml` custom-agent runtime,
  official-only subagent dispatch with no fallback, core/non-core implementer
  routing (serial core code stays controller-local by default; ask about
  `PlanImplementer` only after a concrete work package is specified;
  `PlanImplementer` uses `gpt-5.5` high for accepted-plan execution, while
  `PlanImplementerFrontier` / `AlgorithmImplementerXHigh` uses `gpt-5.5` xhigh
  only for rare bounded core tasks that need architecture or algorithm judgment
  during implementation; `SparkImplementer` may handle non-core mechanical code
  directly inside an authorized workflow), plan-bound implementation dispatch,
  parallel-wave
  execution (dispatch full clean independent waves in the same response,
  Superpowers-style, up to the available runtime concurrency limit), task
  brief/report file handoff,
  progress-ledger resume control, workflow-level authorization for explicit
  subagent workflows, automation throttling, model-tiered reviewer gates
  (per-task implementation review plus final whole-branch review; cost is
  controlled by `ImplementationReviewerFast` / `ImplementationReviewer` /
  `ImplementationReviewerFrontier`, not by skipping reviews), fixed workflow
  hooks, ExpManager/ResultAnalyst joint experiment
  evidence workflow, ExpManager file/checkpoint context-budget contract,
  LTM-as-memory-service boundary, and subagent lifetime management. As of
  2026-07-08, `codex-subagent-workflow` has been retired as an active skill and
  backed up as ordinary documentation at
  `memory/LTM/codex-subagent-workflow-skill-backup-20260708.md`; do not invoke
  it automatically while the subagent workflow remains exploratory.
  `docs/subagents/hmasd-subagent-workflow-reference.md` is the exploratory
  living reference for Superpowers-style subagent techniques such as status
  control, file ownership, file handoffs, review packages, and parallel waves;
  it is not an active skill or a requirement to run Superpowers, and it is lower
  priority than the latest conversation, `AGENTS.md`, and official `.codex/`
  runtime config.
  Superpowers skill bodies provide process shape when active, while HMASD
  project rules supply Codex custom-agent mapping, runtime settings, memory
  hooks, and role boundaries.
  ExpManager currently uses `gpt-5.4-mini` with medium reasoning because
  experiment management is context-heavy factual coordination, not algorithm
  design; the strict file/checkpoint context-budget contract still applies.
  ExpManager `wait_agent` timeouts are soft: if checkpoint/status/evidence
  files show progress, leave the subagent open instead of fallback-closing it.
  ResultAnalyst uses `gpt-5.4` with medium reasoning for bounded metric/gate
  extraction from existing experiment artifacts because the mini tier produced
  reliability issues; it does not launch runs or update `ExpRecord.md` by
  default. When both are needed, ExpManager
  handles launch/progress/run-state/ExpRecord facts first, ResultAnalyst reads
  already-written artifacts for gate tables or extracts, and the main
  controller interprets the result. They can run in the same evidence wave only
  when their write scopes do not overlap. WorkflowAuditor uses
  `gpt-5.3-codex-spark` with high reasoning and read-only sandboxing for
  subagent/workflow consistency audits after broad or risky protocol changes.
- Superpowers migration note: subagent `wait_agent` timeouts are soft. If a
  subagent has written a status/report/checkpoint or output files are fresh,
  keep it open and do not fallback-close. Superpowers task briefs, report files,
  and durable progress ledgers are the authority for task execution shape.
- Subagent lifetime policy is low-churn: do not close every completed agent by
  reflex. Record status and leave agents open through integration when useful;
  rely on Codex runtime cleanup at concurrency pressure, and close manually only
  for cancellation, superseded/stale/faulty agents, scarce-concurrency cleanup,
  or deliberate workflow-boundary reset.
- Project subagents use a Superpowers-style protocol: status enum
  (`DONE`/`DONE_WITH_CONCERNS`/`NEEDS_CONTEXT`/`BLOCKED`), pre-flight wave
  review, file-based review packages, batch review fixes, dispatch templates,
  and no unchanged retry after blocked/needs-context results.
- Main-controller dispatch gate is mandatory: before spawning any project
  subagent, the controller must have an explicit brief/package/dispatch block
  with task id, assigned agent/profile/model tier, requirements source, owned
  scope, forbidden scope/actions, output path, checks, dependencies/conflict
  scan, terminal status contract, next owner, and lifetime policy. If these
  fields cannot be stated, do not spawn; write the brief, split the task, do the
  work locally, inspect missing files, or ask the user.
- Runtime output ownership is now part of the dispatch gate. Any subagent task
  that may run commands or produce experiment artifacts must name a run/log
  root. New runs should prefer `logs/<experiment-id-or-run-id>/...`; existing
  `logs_*` roots are allowed only when explicitly named for script/ExpRecord
  compatibility. Loose root-level runtime files are forbidden unless the user
  explicitly requests the exact root path.
- `.codex/config.toml`: official project-scoped Codex agent config. Current
  HMASD subagent mode uses `multi_agent = true` and `multi_agent_v2 = false`.
  Custom roles live in standalone `.codex/agents/*.toml` files and are
  explicitly registered with `[agents."<name>"].config_file` entries for current
  runtime compatibility. The documented `[agents]` defaults are explicitly
  recorded: `max_threads = 6`, `max_depth = 1`, and
  `job_max_runtime_seconds = 1800`. Do not restore the retired YAML manifest.
- `docs/superpowers/plans/2026-07-06-r23-next-actionability.md`: accepted
  R23-next implementation and experiment matrix plan.
- `memory/IMPLEMENTATION_PLAN.md`: staged plan ledger and current gates.
- `memory/ExpRecord.md`: compact current experiment dashboard.

## Current Experiment Focus

- `EXP-20260707-r24-assignment-to-behavior-bridge` — diagnostics-complete / gated.
- 2026-07-08 completed status: `EXP-20260708-r24-qd-null-control-cloud-handoff`
    reward-off null-control at 320k in both seeds; gate FAIL on latest metrics
    across both seeds, so no reward path is permitted.
- 2026-07-09: R24 frozen q_d core diagnostic stack (Tasks 1-4) is implemented and
    review-approved, including runner wiring and frozen-null artifacts handoff to
    `memory/ExpRecord.md`.
  - First gate: forced-xi and forced-z behavior audits from a q_A reward
    checkpoint, with H={10,20,50}; action/effect distances rose with horizon
    (`xi_effect 0.17335 -> 0.25677 -> 0.41290`, `z_effect 0.18912 -> 0.27497 ->
    0.46262`) but this is insufficient for reward gating without matched-null.
  - Required matched-null forced-audit controls (before any q_D/q_d decision):
    A) matched architecture, no-q_A reward (`z_assignment_residual_gain = 0.5`,
    same architecture/checkpoint stage, q_A OFF);
    B) random-init or early-checkpoint;
    C) fake/shuffled label control (fake Z or permuted xi labels);
    D) within-label repeat baseline (same forced labels under different noise seeds,
    compute between/within).
  - Required stage-1 gates:
    `effect_ratio_h50 = effect_qA / effect_control >= 1.3`
    (strong if >=1.5),
    `growth_h50-h10` at least 1.3x control growth, and
    `between_within_ratio_h50 > 1.2`.
  - Second gate: reward-off q_d behavior-window probe on held-out windows:
    `log q_d_full(z_i | local_behavior_window_i, Z, xi_context_i, c,omega) -
    log q_d_prior(z_i | Z, xi_context_i, c,omega)`, where `xi_context_i`
    excludes focal `z_i`.
    q_d must use separate action and state/effect streams in `local_behavior_window`,
    strong prior/subtraction, and null controls (duration/reward/phase/agent
    shortcuts, matched no-q_A, random/early checkpoint, fake/shuffled labels,
    pre-assignment windows, between/within repeats).
    Gate thresholds before any reward: `residual_gain >= 0.05`, `positive_frac >=
    0.60`, full-prior accuracy gap >= `0.05`, shortcut/null residual ratio >= `1.3x`,
    shuffled/pre-assignment residual near zero, `between/within_h50 > 1.2`, and
    persistence/growth across horizons.
  - Only after matched-null + gate pass plus reward-off q_d probe pass:
    consider small clipped low-only q_d reward.
    q_D reward stays blocked; `q_D` re-probe remains reward-off and must not read
    `xi` directly (`q_D` can only go downstream of q_d behavior separation).
  - Implementation update (2026-07-07): `ha_ctse_process/team_conditioned_qd.py`
    and the `StandaloneProcessAgent` R24 q_d plumbing now use a two-stream
    behavior-window probe:
    `q_full(z_i | action_window_i, effect_window_i, Z, xi_context_i, c, omega)`
    versus `q_prior(z_i | Z, xi_context_i, c, omega)`.  `xi_context_i` is a
    teammate-skill histogram that excludes the focal `z_i`.  This remains
    reward-off only; held-out/null/shortcut gates still decide whether reward
    injection is allowed.
  - Implementation update (2026-07-08): plan
    `docs/superpowers/plans/2026-07-08-r24-qd-null-controls.md` added and
    implemented. The q_d probe now also logs behavior-only, pre-assignment
    window, shuffled-label, fake-label, and label-baseline diagnostics:
    `q_behavior(z_i | action/effect window)`, `q_pre(z_i | previous
    pre-assignment window, Z, xi_context_i, c, omega)`, and null residual reads.
    `SegmentManager.renew()` carries a bounded previous-window summary into the
    new segment for pre-assignment control. This remains reward-off only.
  - External review Round 4 (GPT web, 2026-07-08) accepted the reward-off
    continuation and clarified interpretation:
    `q_behavior` is not automatically a shortcut; if it beats prior/nulls it is
    positive evidence for individual skill behavior semantics. However, if
    `q_full - q_behavior` is small, team-conditioned/cooperative semantics are
    not proven. `q_pre` is not a pure leakage test or "must be zero" metric; it
    measures selection/history predictability before execution. If `q_pre` is
    strong, require post-window gain over pre-window (`q_full - q_pre`) and/or
    forced intervention evidence before interpreting q_d as executed-skill
    behavior. Reward remains blocked until seed-consistent q_d residual,
    null/shortcut controls, and forced-audit between/within gates pass.
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

1. Launch/follow `EXP-20260709-r24-frozen-qd-null-probes` in cloud 64env at
   320k for both seeds with:
   `EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh`.
2. Read frozen-null diagnostics from:
   `r24_qd_windows/*.npz`, `r24_qd_frozen_nulls/*.json|.md`, and
   `train_updates.csv`; treat strong `q_pre`, behavior-only, or null residual as
   confounds unless post-assignment full-minus-null controls pass.
3. Re-run matched-null `q_d` diagnostics under the completed core stack:
   `q_d_full(z_i | local_behavior_window_i, Z, xi_context_i, c, omega) - q_d_prior(...)`,
   with separate action/state-evidence streams, matched-null controls, and the Round-3
   gates: residual gain/positive fraction, full-prior accuracy gap, shortcut/null
   dominance, horizon persistence/growth, shuffled/pre-assignment near-zero residual,
   and between/within_h50 ratio.
   Interpret `q_behavior` as individual skill behavior evidence when it beats
   nulls; interpret strong `q_pre` as selection/history confound unless the
   post-assignment window exceeds it.
4. Only after full Round-3 gate pass and seed-consistent evidence, run low-only
   q_d reward and then reward-off `q_D` re-probe with behavior-window targets.
5. Optional/lower priority: cloud 64env matched rerun of the R23 matrix (both seeds)
   for a non-confounded task read and a clean arm2 320k eval.

## Do Not Do Yet

- Do not enable `q_D` or `q_d` reward, `q_D` coefficient sweeps, or more
  q_D target engineering as the primary branch until the full Round-3 gate stack
  passes.
- Do not launch 960k scale/task runs from R23/q_A before the xi-to-behavior bridge
  is validated and the task read is unconfounded.
- Do not launch seed2 depth for the weak g-info coefficient line.
- Do not add new kappa/hazard/DADS/communication-intrinsic mechanisms before
  the R24 assignment-to-behavior bridge is resolved.

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
  external review dialogue archive. Raw pasted model text is the evidence;
  summaries and handoffs are only indexes.
- `memory/LTM/external_reviews/INDEX.md`: newest-first lightweight review-round
  index.
- `memory/LTM/CROSS_VALIDATION_ARCHIVE.md`: Round 1 external-review disposition
  for R24 sequencing and principle-deferral rationale.
