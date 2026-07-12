# HA-CTSE Current Work

Updated: 2026-07-12

Purpose: compact first-read state for the current work only. Full historical
context is archived under `memory/LTM/`.

## Controller Handoff

- 2026-07-12: Codex is the active controller for the traditional HMASD
  R24/R25/R26/R27 line on branch `aggressive`. R26-G1a failed its primary arm0
  family gate: none of update 25, update 30, or final passed the pre-registered
  held-out behavior screen. The current gate is the reward-off R27-G1 frozen
  low-actor capacity autopsy. Implementation commits through `10f4615` are
  complete; the final Frontier review passed spec compliance, code quality,
  runner/artifact contract, and launch readiness, and the focused matrix passed
  `74 tests in 18.23s`. The scientific audit remains `ready_not_launched` and
  requires a separate explicit user instruction for approximately 2.5--3.5
  hours of local CUDA work with `NResets=64`. IMOD remains a separate migrated
  project/track and does not replace or redefine this line. The binding
  handover protocol below remains in force.
- 2026-07-11 subagent cache policy update: project runtime capacity is now
  `max_threads = 12`. The controller must reuse compatible child threads by
  `(profile, model/reasoning, sandbox, workstream, ownership)` for sequential
  follow-ups; `DONE` no longer implies close. Twelve is retention capacity, not
  a fan-out target. A Codex app/session restart is required before the runtime
  exposes the new ceiling.
- 2026-07-11 correction: HMASD and IMOD are independent active research
  workspaces. `C:\project\HMASD` continues the traditional HA-CTSE R24/R25
  line, including R26 individual-skill diagnostics and update-matched parity
  work. `C:\project\IMOD` carries the separate IMOD-Direct exploration; its
  design gates do not replace or block the traditional HA-CTSE continuation.
- 2026-07-10: standalone IMOD workspace migration completed from HMASD to
  `C:\project\IMOD`. The new repository has independent Git history on branch
  `main`, root commit `4b84b8b`, and preserves the current working-tree
  `AGENTS.md` plus complete `.codex/` configuration. Reproducible package:
  `dist/imod_workspace_bundle_20260710_final.zip`; manifest and per-file
  SHA256 records are inside the archive. The migrated workspace passed checksum
  verification, core import smoke, workflow-protocol validation, and focused
  R24 audit tests (20 passed). No logs, checkpoints, old `.git`, caches, or
  experiment outputs were migrated. Future IMOD design/implementation work
  should start in the new workspace. This HMASD repository remains active for
  the traditional HA-CTSE line and also preserves its source history and
  experiment archive. Existing q_d/q_D blocks and written-spec / cross-family
  review gates are unchanged.
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
  cross-validation gate runs through `marl-peer-reviewer` (Codex plugin).
  Peer-review model updated 2026-07-10: pinned to gpt-5.6-sol max (xhigh tier).
  Experiment state below is unchanged by the handoff.
- Binding handover protocol for all future Claude<->Codex controller switches:
  `docs/subagents/claude-codex-handover-spec.md` (read at every switch; keep
  this block current per its section 2).

## Current Objective

- Current traditional-line gate: launch the reward-off R27-G1 frozen low-actor
  capacity autopsy only after a separate explicit user instruction. It asks
  whether the existing strict-HMASD MAPPO low actor has unused
  `z_i`-conditioned action capacity, loses static sensitivity through recurrent
  carryover, has a weak static FiLM path, or was missed by the R26 observational
  instrument. The exact audit is implemented and fully reviewed, but no R27
  scientific classification exists yet.
- IMOD-Direct is a separate migrated project/track. Its design state must not
  replace, redefine, or supply evidence for the traditional R24/R25/R26/R27
  line.
- Reach HMASD-level S7-S1 behavior at roughly 1e6 steps before returning to
  S7-S3.
- Treat 160k/320k runs as mechanism gates, not final HMASD-comparison verdicts.
- Current main line: R27-G1 on the causal edge
  `individual skill z_i -> persistent executable behavior`. R23-next validated
  high-level `Z -> xi` actionability, R25 did not verify q_A reward at 1M, and
  R26-G1a found no arm0 checkpoint PASS; R27 now separates low-actor capacity,
  recurrent washout, missing specialization pressure, and observational miss.
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
- No `memory/ALGORITHM_PRINCIPLES.md` change is needed at the R27 implementation
  boundary; the audit applies the existing reward-off causal-gate contract.

## Active Plan Pointers

- `docs/superpowers/specs/2026-07-11-r27-g1-low-actor-capacity-autopsy-design.md`:
  accepted reward-off R27-G1 design and fixed classification gates.
- `docs/superpowers/plans/2026-07-11-r27-g1-low-actor-capacity-autopsy.md`:
  implemented and reviewed R27-G1 plan; scientific launch remains a separate
  explicit user decision.
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
  recorded: `max_threads = 12`, `max_depth = 1`, and
  `job_max_runtime_seconds = 1800`. Do not restore the retired YAML manifest.
- `docs/superpowers/plans/2026-07-06-r23-next-actionability.md`: accepted
  R23-next implementation and experiment matrix plan.
- `memory/IMPLEMENTATION_PLAN.md`: staged plan ledger and current gates.
- `memory/ExpRecord.md`: compact current experiment dashboard.

## Current Experiment Focus

- `EXP-20260711-r27-g1-low-actor-capacity-autopsy` is
  **`ready_not_launched`**. Exact runner:
  `scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1`; expected cost is
  2.5--3.5 hours on the local RTX 4070 Laptop GPU with `NResets=64` and no CPU
  fallback. A separate explicit user launch instruction is still required.
- Implementation commits `c6136e2`, `9df2e3e`, `bf55ad2`, `7cbc8de`,
  `72420ea`, `6ce55e3`, `47399aa`, `5395331`, `aafaa8d`, `d6978bf`, and
  `10f4615` are complete. Final Frontier verdicts are PASS for spec compliance,
  code quality, runner/artifact contract, and launch readiness. The focused
  verification result is `74 passed in 18.23s`; parser, AST, diff hygiene,
  forbidden-core-file, exact-checkpoint, and CUDA 3+1+1 no-write dry-run checks
  passed.
- R27 is a reward-off frozen diagnostic only. It changes no reward, actor,
  policy/critic architecture, optimizer/loss/advantage logic, collector
  semantics, environment dynamics, or source checkpoint, and it authorizes no
  actor redesign or q_A/q_d/q_D change before classification review.
- Known unrelated baseline debt remains: the legacy standalone evaluation
  fixture lacks `args.log_dir` (`3 passed, 1 failed` in that bounded baseline
  subset). R27 did not modify the fixture, `train.py`, or the evaluation path.
- `EXP-20260710-r25-qa-verification-1m` — completed 1M-step verification on 64env, 1 seed, 2 arms; external peer review Round 6 (GPT-5.6-sol max xhigh); disposition ACCEPTED 2026-07-10. q_A NOT VERIFIED at verification gate (demoted to default-off, D1); HMASD parity OPEN pending update-count deconfound (D2); R26 pivot to G1 individual-skill diagnostics approved (D3).
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

1. Await a separate explicit user instruction before launching the exact R27-G1
   local-CUDA runner (estimated 2.5--3.5 hours, `NResets=64`). Do not infer a
   root-cause classification from implementation tests or review verdicts.
2. After a launch completes, read the three arm0 static reports, three fixed-seed
   synthetic active/sham reports, and aggregate two-of-three classification
   before authorizing any next design. `INVALID`/`UNDERPOWERED` repeats the same
   instrument without changing thresholds.
3. Treat the completed R25 arm0/arm2 archives and HMASD baseline as standing
   references. Reuse their curves/checkpoints; do not rerun those controls.
4. Optional cheap q_A interference diagnostics may use existing R25 artifacts:
   correlate q_A reward share/residual gain with task metrics, or offline-score
   arm0 versus arm2 trajectories with the frozen q_A discriminator.
5. The separate update-matched parity question may later use a 1M/32env cloud
   run prepared through the cloud-handoff protocol. It requires its own explicit
   user approval and must not duplicate a standing-reference control.
6. D2 remains approved-deferred as an archival sensitivity analysis only, with
   separate validation, identical stopping rules, all outcomes, one all-GPU
   device class, and no reward unblocking from an unexpected pass.
7. IMOD design and implementation continue only in the separate
   `C:\project\IMOD` workspace; do not use IMOD state as evidence for this
   traditional R24/R25/R26/R27 line.
8. Do NOT proceed to q_d/q_D reward arms or a new intrinsic reward. q_d/q_D
   remain BLOCKED by R24-1 and the open R27 classification gate.

## Do Not Do Yet

- Do not launch R27-G1 without a separate explicit user instruction. Do not
  treat `74 passed in 18.23s`, dry-run checks, or four Frontier PASS verdicts as
  a scientific capacity result. Do not redesign the actor, reset recurrent
  hidden state, add post-GRU FiLM/action-head residuals, or enable `q_A`, `q_d`,
  `q_D`, or another reward path before the R27 classification is reviewed.
- Do not re-run the standing-reference runs (user directive 2026-07-10): the
  HMASD baseline (REF-20260617) and the completed R25 baseline/control arms
  (arm0_arch_only, arm2_qA_reward archives) are fixed comparison data. Future
  experiments reuse the archived curves/checkpoints; no HMASD arm and no
  repeat baseline arm in new runners (exception only for incomparable config
  changes, with explicit user approval). See the standing-reference rule in
  `memory/ExpRecord.md`.
- Do not execute the superseded CSOG roadmap or Phase-A/G0 plan. Do not create
  an IMOD implementation plan until the user has reviewed the written spec and
  the required independent cross-family review is archived.
- Do not enable `q_D` or `q_d` reward, q_D/q_d coefficient sweeps, or q_D target engineering as the primary branch. R24-1 FAIL accepted 2026-07-09; q_d/q_D rewards remain BLOCKED until D3 diagnostic design passes cross-validation and shows individual-skill behavioral differentiation is real.
- Do not launch 960k scale/task runs from R23/q_A before arm0-vs-arm2 deconfound is read (locally tonight/2026-07-10), R24-1 disposition is fully archived, and R25 non-verification (demotion to default-off, D1) is resolved by G1 diagnostics.
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
