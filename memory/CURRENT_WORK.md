# HA-CTSE Current Work

Updated: 2026-07-11

Purpose: compact first-read state for the current work only. Full historical
context is archived under `memory/LTM/`.

## Controller Handoff

- 2026-07-11: Codex is the active controller for the traditional HMASD
  R24/R25/R26 line in isolated worktree `C:\project\HMASD\.worktrees\r26-g1a`.
  R26-G1a implementation and verification are complete, but the scientific
  six-checkpoint screen has not run. The current gate is explicit user approval
  for an estimated 30--45 minutes of local CUDA work. IMOD remains a separate
  migrated project/track and does not replace or redefine this line. The
  binding handover protocol below remains in force.
- 2026-07-10: controller direction is Claude Code -> Codex for an isolated
  theory/design revision on branch `aggressive`. The user approved IMOD-Direct
  as the replacement direction for graph-first CSOG, and Codex is writing the
  design spec only. No implementation or experiment was launched in this
  design turn; existing experiment state remains governed by
  `memory/ExpRecord.md` and run-local status files. No project subagents were
  spawned or left open. Pending gates are user review of the written IMOD spec
  and an independent Claude/Gemini MARL review; same-family GPT review does not
  satisfy the cross-validation gate. The worktree already contained unrelated
  user changes under `.codex/`, `AGENTS.md`, one agent-migration plan, and the
  workflow validator; the IMOD revision must not overwrite or stage them.
- 2026-07-09: R24 execution handed off from the Codex controller to Claude Code.
  The Claude-side subagent workflow (`.claude/agents/README.md`, cloned from
  `AGENTS.md`/`.codex/agents/`) now governs delegation; the MARL design
  cross-validation gate runs through `marl-peer-reviewer` (Codex plugin,
  gpt-5.5 xhigh). Experiment state below is unchanged by the handoff.
- Binding handover protocol for all future Claude<->Codex controller switches:
  `docs/subagents/claude-codex-handover-spec.md` (read at every switch; keep
  this block current per its section 2).

## Current Objective

- Current traditional-line gate: launch the reward-off R26-G1a frozen-policy
  screen only after explicit user approval. It asks whether naturally assigned
  individual `z_i` labels leave stable held-out local behavior signatures beyond
  assignment context/history and matched nulls. The implementation includes
  the behavior-window dataset, analyzer, frozen collector, and exact
  six-checkpoint CUDA runner; the final focused verification is clean with
  `52 passed`.
- IMOD-Direct is a separate migrated project/track. Its design state must not
  replace, redefine, or supply evidence for the traditional R24/R25/R26 line.
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

- `docs/superpowers/specs/2026-07-11-r26-g1a-individual-skill-behavior-screening-design.md`:
  accepted reward-off G1a design and pre-registered gates.
- `docs/superpowers/plans/2026-07-11-r26-g1a-individual-skill-behavior-screening.md`:
  implemented R26-G1a plan; scientific launch remains a separate user decision.
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

- R26-G1a individual-skill behavior-window screening is **launch-ready, not
  launched**. Exact runner:
  `scripts/run_r26_g1_screening_local_cuda.ps1`; experiment facts and the exact
  run command/root are in `memory/ExpRecord.md`. Expected local CUDA wall time
  is approximately 30--45 minutes, pending explicit user approval.
- Read each checkpoint against the full pre-registered gate. The primary arm0
  family passes only if at least 2 of update 25, update 30, and final pass in
  the same direction. Arm2 is contextual contrast only and cannot rescue an
  arm0 failure.
- A G1a pass authorizes only R26-G1b forced-`z_i` design with rewards still off.
  Fail/mixed/underpowered outcomes follow the accepted decision tree and do not
  authorize reward injection. `q_A`/`q_d`/`q_D` reward paths remain
  blocked/default-off while this gate is open.
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

1. Await explicit user approval before launching the exact R26-G1a
   six-checkpoint local-CUDA runner (estimated 30--45 minutes). Do not infer a
   scientific pass from implementation tests or smoke artifacts.
2. After a launch completes, read the per-checkpoint gate and the arm0 2-of-3
   family gate before choosing PASS/FAIL/MIXED/UNDERPOWERED. Arm2 remains
   contextual; a pass advances only to G1b design with rewards off.
3. Separately, user reviews
   `docs/superpowers/specs/2026-07-10-imod-direct-design.md`; revise the written
   spec if requested. Do not write a replacement implementation plan yet.
4. Prepare the unchanged IMOD design for independent Claude/Gemini MARL review
   and archive the raw review plus controller disposition before scientific
   acceptance.
5. After written-spec and cross-family review approval, invoke the
   Superpowers writing-plans stage for the minimal reward-off G-1/G1 instrument
   and direct-effect diagnostic only. Do not plan G2/G3 implementation as if G1
   has already passed.
6. Existing experiment operations remain separate from this design revision.
   Before acting, verify the run-local status for
   `EXP-20260709-local-overnight-audit-power-r23-deconfound`; if its matched
   arm0/arm2 pairs completed, read their coverage/throughput trajectories and
   preserve the result as a q_A task-effect deconfound, not IMOD evidence.
7. `EXP-20260710-r25-qa-verification-1m` remains launch-ready in
   `memory/ExpRecord.md`; this design turn neither launches nor cancels it.
8. D2 remains approved-deferred as an archival sensitivity analysis only, with
   separate validation, identical stopping rules, all outcomes, one all-GPU
   device class, and no reward unblocking from an unexpected pass.
9. Do NOT proceed to q_d/q_D reward arms, graph/world-model/async IMOD modules,
   or a new intrinsic reward. q_d/q_D remain BLOCKED by R24-1, and IMOD has not
   passed its direct-effect gate.

## Do Not Do Yet

- Do not launch R26-G1a without explicit user approval. Do not treat `52 passed`,
  dry-run checks, or implementation smokes as scientific checkpoint evidence.
  Do not enable `q_A`, `q_d`, or `q_D` reward paths; even a G1a family pass
  authorizes only G1b design.
- Do not execute the superseded CSOG roadmap or Phase-A/G0 plan. Do not create
  an IMOD implementation plan until the user has reviewed the written spec and
  the required independent cross-family review is archived.
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
