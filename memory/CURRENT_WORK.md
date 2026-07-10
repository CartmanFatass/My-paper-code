# HA-CTSE Current Work

Updated: 2026-07-09

Purpose: compact first-read state for the current work only. Full historical
context is archived under `memory/LTM/`.

## Controller Handoff

- 2026-07-09: R24 execution handed off from the Codex controller to Claude Code.
  The Claude-side subagent workflow (`.claude/agents/README.md`, cloned from
  `AGENTS.md`/`.codex/agents/`) now governs delegation; the MARL design
  cross-validation gate runs through `marl-peer-reviewer` (Codex plugin,
  gpt-5.5 xhigh). Experiment state below is unchanged by the handoff.
- Binding handover protocol for all future Claude<->Codex controller switches:
  `docs/subagents/claude-codex-handover-spec.md` (read at every switch; keep
  this block current per its section 2).

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

- `EXP-20260709-r24-frozen-qd-null-probes` — completed 4/4 cloud runs with external peer review (Round 5, GPT-5.5 xhigh); disposition ACCEPTED 2026-07-09.
- R24-1 verdict: **FAIL accepted** with wording condition: "fail under the tested policies and current diagnostic setup" (3 of 4 policies collapsed), NOT a categorical universal negative. q_d/q_D rewards remain BLOCKED on this evidence line.
- External review Round 5 disposition (raw text verified from DIALOGUE_ARCHIVE.md):
  - **D1 (R24-1 gate)**: Accepted as FAIL. No existing-data reanalysis would reverse it. q_d/q_D reward paths remain permanently blocked on this evidence line unless a new mechanism changes the setting.
  - **D2 (sensitivity re-run)**: APPROVED-DEFERRED as a post-hoc instrument-sensitivity check only, NOT as confirmatory. Conditions: (i) separate validation split for early stopping, (ii) identical stopping rules for all variants, (iii) all outcomes reported (including negatives), (iv) single device class all-GPU, (v) if unexpected pass, reopens instrument-validity only, does not itself justify reward-on.
  - **D3 (pivot direction)**: ACCEPTED. Pivot to individual-skill behavioral differentiation (minimal diagnostic: blinded behavior-only separability vs context/history nulls, then forced-z_i between/within test). Detailed design deferred until arm0-vs-arm2 deconfound pair (running tonight locally) is read.
  - **Unaffected positives**: q_A actionability (Z->xi) result stands; q_A task-pace observation (coverage 0.7-0.8 @320k vs HMASD 0.7 @480k baseline REF-20260617) pending deconfound.
- 2026-07-09 update: Frozen q_d null-probe core Tasks 1-4 completed and reviewed; cloud 4/4 runs analyzed (3 CPU, qAoff/seed2 GPU). Gate-read facts: healthy qAon/seed1 and all others FAIL all core gates (real residual_gain -0.0319 to +0.0153 < 0.05 gate; positive_frac < 0.60; real loses to behavior_only in 3 of 4 runs). Cross-seed consistent: team-conditioned evidence absent (real - behavior_only negative in both qAon seeds). Instrument caveat: overfitting bias (loss_full/loss_prior 2.4x-3.7x); frozen residuals ~0/negative while prior in-loop read small positive. Per-seed variability >> arm identity; no q_A-dependence pattern visible. Mechanism-fail likely; D2 re-run worth one pre-registered sensitivity check mainly for publication solidity, not to rescue gate.
- Local overnight arms 5-7 deconfound (R23 arm0-vs-arm2 seed-matched pairs) resuming; arms 1-4 audits complete. Expected completion ~09:02 UTC+8 2026-07-10. Monitor `train_updates.csv` growth in `logs/r24_overnight_20260709_audit_deconfound/arm*/`.
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

1. Monitor completion of `EXP-20260709-local-overnight-audit-power-r23-deconfound` arms 5-7 (R23 arm0-vs-arm2 matched-seed deconfound pair training) running locally overnight; expected ETA ~09:02 UTC+8 2026-07-10. Read `train_updates.csv` and `eval_episodes.csv` to extract coverage/throughput curves and task-read unconfoundedness vs single-seed R23 arm2 result.
2. Optional after arms 5-7 completion: D2 approval-deferred sensitivity re-run (early-stopping + all variants + pre-registered acceptance criterion) can be queued for cloud execution when local GPU frees (post-arm7 ~day 2026-07-10) or handed off to user as a standalone diagnostic task. Set conditions per Round 5 advice: separate validation split, identical rules, all outcomes reported, single all-GPU device class, unexpected pass reopens instrument only.
3. Pending D3 concretization: after arm0-vs-arm2 deconfound read, finalize minimal reward-off diagnostic design for individual-skill behavioral differentiation (blinded behavior-only separability + forced-z_i between/within gate) and get explicit design cross-validation round before implementation. Archive D3 diagnostic design plan to IMPLEMENTATION_PLAN.md once approved.
4. Do NOT proceed to q_d/q_D reward arms, q_D re-probe design changes, or scale-up until R24-1 disposition fully archived and D3 diagnostic design approved. q_d/q_D rewards remain BLOCKED by R24-1 FAIL + wording condition.

## Do Not Do Yet

- Do not enable `q_D` or `q_d` reward, q_D/q_d coefficient sweeps, or q_D target engineering as the primary branch. R24-1 FAIL accepted 2026-07-09; q_d/q_D rewards remain BLOCKED until D3 diagnostic design passes cross-validation and shows individual-skill behavioral differentiation is real.
- Do not launch 960k scale/task runs from R23/q_A before arm0-vs-arm2 deconfound is read (locally tonight/2026-07-10) and R24-1 disposition is fully archived.
- Do not launch seed2 depth for the weak g-info coefficient line until R24-1/D3 pivot resolves.
- Do not add new kappa/hazard/DADS/communication-intrinsic mechanisms before the R24 assignment-to-behavior bridge is resolved (R24-1 FAIL accepted, D3 pivot direction registered, diagnostic design pending).
- Do not run D2 sensitivity re-run on the frozen analyzer until all four conditions are confirmed (separate validation split, identical stopping rules, all outcomes reported, single all-GPU device class) and q_d/q_D reward paths remain blocked even if D2 passes (instrument-validity reopened only, per Round 5 advice).

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
