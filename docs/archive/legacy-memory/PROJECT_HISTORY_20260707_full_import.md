# HA-CTSE Attention Pointer

Updated: 2026-07-06

Purpose: first-read navigation for long-running HA-CTSE work. Keep this file short and point to the active sections in the real memory files; do not duplicate the full argument here.

## Current Focus

- Active research objective: make HA-CTSE reach HMASD-level behavior on S7-S1 at roughly 1e6 steps before returning to S7-S3; clarified parity means at least half of evaluation primitive steps reach `coverage == 1.0`, not reward_mean spikes. User reminder 2026-07-03: HMASD's stable high-coverage behavior is normally a ~1e6-step convergence read, so 160k/320k HA-CTSE runs are mechanism gates, not final HMASD-comparison verdicts.
- Active algorithmic focus: Round 22 adopts the GPT-5.5 correction that the
  current mainline is **R21/v6 three-timescale HA-CTSE**, not R12
  recognition-first alone.  OPT supplies continuous recognition substrate
  (`omega_t`, compact `c_t`, optional `kappa_t`); sampled team intent `Z`
  supplies slow synchronized commitment and non-vacuous team discriminator
  pressure; asynchronous individual `z_i` supplies response skills and
  decoupled lifetimes.  The next theory task is the two-clock ELBO/objective
  unification plan:
  `docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md`.
- Active R22 execution status (2026-07-06): R22-1 and R22-4 are complete and
  reviewed.  Read `memory/R22_TWO_CLOCK_ELBO.md` for the objective sketch and
  `memory/R22_TARGET_ENTROPY_DESIGN.md` for entropy design.  R22-3 diagnostic
  implementation is now complete after external review: `z_decisions_per_update`
  aliases Z-boundary decisions, `z_advantage_mean/std/var` tracks unnormalized
  high-level advantages only on charged Z-boundary samples, and
  `combined_intrinsic_env_ratio` plus cumulative guard counters monitors stacked
  prototype-disc + team-disc intrinsic load.  HMASD eval now exposes a fallback
  marker when light metrics cannot provide per-step parity samples.  Do not
  rewrite the R22 docs unless new R21/HMASD data changes the premise.
- Active R23 read (2026-07-06, COMPLETED — MIXED, 320k seed1): logs
  `dist\logs_cloud_r23_actionable_team_intent_64env` (3 arms r23_arch_only /
  r23_1_action / r23_3_reward, all clean exit 0). **R23-0 architecture PASS
  in-training** — the `z_assignment_residual_gain=0.5` fix restored Z→ξ capacity
  (forced-Z skill KL 0.04–0.08, z_assignment_itv 0.03–0.10 ≈ 20–50× the R21
  ~0.002 band, sustained). **R23-1 objective FAIL/null** — g-info active but loss
  ~-2e-4 (negligible), MI flat, objective-ON MI (0.012) < objective-OFF (0.024):
  coef 0.02 too weak; the KL elevation is the static architecture, not the learned
  objective. **R23-2 disc FAIL** — team_disc_acc ≈ chance (0.14–0.25 vs 1/6),
  prior entropy pinned ln6: ξ moves with Z but produces no recoverable joint-effect
  signature. **R23-3** — gate mechanics correct (gated_off at KL 0 → applied at
  KL≥floor), reward magnitude ~0, guard armed no-kill, no task effect. **Task**:
  cov_eq1_step_frac=0.0 all arms (parity untouched, like R21), cov 0.11–0.21. Net:
  R23 separated architecture-capacity (fixed) from actionability-learning + joint-
  effect-signature (both still failing); q_D remains an amplifier with nothing to
  amplify. Full readout: `ExpRecord.md` → `EXP-20260706-r23-actionable-team-intent`.
  Blocker moved from "Z can't move ξ" → "ξ doesn't map to a recoverable joint
  effect." Next (none launched): stronger/annealed actionability objective or
  Option-B residual q_A; interrogate the q_D effect target/timescale; no 960k / no
  seed2 on this coef until a rising MI trend shows at 320k.
- Active R23-next status (2026-07-06→07, IMPLEMENTED default-off, CC implementer — user
  authorized "do all the jobs"): the GPT post-read forward plan is now BUILT + tested.
  Plan `docs/superpowers/plans/2026-07-06-r23-next-actionability.md`; execution + metadata
  in `cross_validation.md` ("2026-07-06 GPT R23-result advice" → EXECUTION block);
  `R23_ACTIONABLE_TEAM_INTENT.md` §11. Done: (T1) decision curves confirm A/B/C;
  (T2) **g-info gradient audit = SCALE/FORM** (`scripts/r23_ginfo_grad_audit.py`): g-info
  grad into the Z path is <2% of PPO and self-stalling — NOT a wiring bug → main line
  switches to q_A; (T3) **q_A residual actionability** `ha_ctse_process/assignment_actionability.py`
  (q_A_full/q_A_prior, residual reward gated on residual_gain>0, high-level only, default-off,
  7 tests); (T4) **reward-off q_D target/timescale audit** `ha_ctse_process/team_effect_targets.py`
  ({s_next,joint_action,joint_effect,delta_omega}×H{10,20,50}, double-count-safe, 5 tests);
  (T5) **runners** `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh` (+ .ps1), 4 arms,
  dry-run validated. Regression: 245 pass, 4 pre-existing failures (stash-confirmed unrelated).
  Env for running: conda `SB3` (gymnasium 1.0.0 / pettingzoo 1.24.3). Nothing committed
  (project norm: user decides). NEXT (user): launch `EXP-20260707-r23-next-mechanism-matrix`
  on GPU; read arm1 q_a_residual_gain, arm2 forced-Z-KL trend + task health, arm3 q_d_acc per
  target/H. q_D reward stays OFF until arm3 finds a non-chance target. Stop list intact
  (no g-info coef sweep, no q_D reward-on, no 960k, no new kappa*/hazard/DADS, no comm-as-intrinsic).
- Superseded/deferred context: R12 remains valuable as recognition substrate,
  substrate-gate evidence, and recognition-only control, but it is no longer
  the cooperation engine.  R19 remains a mechanism-negative transition-residual
  control unless a later complete reward-on read contradicts the current
  negative `team_t_mi` evidence.  The previous Round 10/11 `g`-revival line
  remains deprecated unless explicitly re-opened by a later plan.
- Active implementation stage: Round 15 implemented AR-first response selection plus coordinator-residual reward `log q_d(z_i | o'_i, kappa) - stored log pi_h(z_i | kappa, z_{1:i-1})`. Round 16 Stage-1.5 roster-docking is now implemented behind `--ar_prefix_mode same_check|roster`: roster mode conditions a renewing agent on teammates' renewal-time active skills and ages, stores that snapshot in `Segment`, reconstructs PPO logp from the snapshot, and logs `roster_ar_kl_zeroed`, `roster_ar_kl_shuffled`, and `selection_independence_deficit`.
- Active experiment stage: `EXP-20260703-r15-stage1-steering` local A0/A1 first read has completed structurally. A0 is a weak control baseline; A1 reward-off probe reached update 40 with clean reward guards and no entropy collapse, but weak classifier signal (`proto_acc=0.270`) and rollout `proto_ar_kl=0.0`.
- Completed R16.5 entfloor base read: local CUDA run completed normally at 960k:
  `logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_233759\seed1\a2r_roster_reward_coef01_entfloor`.
  Gate classification is PASS-SCAFFOLDED, not PASS-CLEAN. The 960k eval recovered strongly
  (reward=67.263427, coverage=0.493333, qos=0.341250, throughput=27.252762,
  zero_throughput_ep_frac=0.200000, coverage_eq1_step_frac=0.075700) and beats
  the reference 960k collapse, holding >80% of the reference 480k peak. However,
  duration entropy did not self-sustain: update_120 duration_usage_entropy=0.543469,
  duration_usage_max_frac=0.770270, floor_active=1, and last10 floor_active=1.0.
  Mechanism claim must be qualified as floor-supported lifetime diversity. The warn
  guard recorded reward-ratio pathology (`kill_triggered=2`, `over05_count=25`) but
  did not stop the run. The four P2 eval-mode cells remain an optional diagnostic
  if train/eval action-mode divergence becomes important, but they no longer
  block the main algorithmic path. Do not mix this R16.5 read with R19/R21
  team-intent or team-transition results.
- Completed R16.5 continuation read (2026-07-05):
  `dist\logs_cloud_r16_5_continuation_64env` contains the downloaded 64env
  continuation logs. Both branches finished cleanly. Seed2 coef=0.05 is
  mechanism-clean on duration (`duration_usage_entropy=0.937736`,
  `floor_active=0` at 960k) and reaches reward=71.713382 / coverage=0.416667,
  but remains far from parity (`coverage_eq1_step_frac=0.016400`,
  `zero_throughput_ep_frac=0.500000`). The coef=0.1 bounded retry underperforms
  (reward=31.248840, coverage=0.121667, coverage_eq1_step_frac=0). R16.5 floor
  tuning is closed; keep coef=0.05 only as a stabilized baseline/control.
  Roster remains decorative (`roster_ar_kl_shuffled` ~4e-6 to 5e-6), so do not
  run another broad roster-only sweep.
- Active cross-validation entry: `memory/cross_validation.md` is now the canonical cross-model validation ledger. `memory/advice_cc.md` is legacy-only and should remain a redirect/fallback. New reviewers should read `2026-07-04 Codex R16 four-arm experiment readout for external review` plus `Round 16 / R16.4 Experiment readout` before judging roster-docking; this is a weak/negative R16 result. R19 remains next batch and should be reviewed separately through the R19 implementation receipt and experiment record.
- Active R19 status (2026-07-04): the team-transition engine (situation-transition residual heads, `a2_plus_t` arm) is now IMPLEMENTED and locally verified from `docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md` (single source of truth; supersedes the Gemini v2 ledger entry). Everything is default-off; the reward arm launches only via the pre-registered OUT-OF-GAS branch of the A2 outcome matrix or explicit user decision after the A2 320k read. Pre-registered as `EXP-20260704-a2-plus-t` (trigger-blocked). Principle context: R17-R19 corrections now in `ALGORITHM_PRINCIPLES.md` (exogenous/atomic variation, kappa* canonical form, 2x2 task matrix, dual-engine principle, kappa dual-use churn caution, prior-mixed-null mitigation).
- Active R19 read (2026-07-05): downloaded logs are under `dist\r_19log\logs_cloud_r19_team_transition_64env`. Baseline and `a2_plus_t_probe_reward_off` finished 960k cleanly; `a2_plus_t_reward_coef005` is only a running snapshot to 224k in the downloaded files. The reward-off probe is mechanism-negative: at 960k `team_t_mi=-0.042034` and last-5 mean is `-0.064172`, with `team_t_self~0.93`; matched baseline 960k is much better on task readout (coverage 0.333 vs probe 0.115). Do not treat R19 team-transition residual as validated; only revisit if a later complete reward-on log shows sustained positive `team_t_mi` and task gains. Keep R19 separate from R16/R16.5 and compare against R21 team-intent restoration.
- Active Round 21 directive (2026-07-04, USER OVERRIDE — HIGHEST PRIORITY): restore the HMASD autoregressive team skill under async low-level lifetimes via the two-clock hierarchy (sampled Z held K_team checks, atomic AR reassignment at Z boundaries, async docking between; team discriminator reward ships in the same build — non-vacuous because Z is sampled). Spec: `docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md`. Codex builds NOW default-off; launch on the stabilized entfloor base after its 480k read. R20's team_bridge_none ablation is DROPPED and the kappa* deferral DISSOLVED (bridge machinery refactors into pi_Z); a2_plus_t demoted to complementary. Byproduct: R21 vs the recognition-only base answers commitment-vs-recognition (R14.0) on the mainline.
- Active R21 read (2026-07-06, COMPLETED — NEGATIVE): seed-1 cloud logs are in
  `dist\logs_cloud_r21_team_intent_64env`. Both arms (`r21_z_probe`,
  `r21_z_reward_coef005`) finished cleanly (960k, no kill/NaN). R21 FAILS both
  gates. Structural: `z_assignment_itv`≈0.002-0.005 (decorative, ~0) and
  `team_disc_acc`≈random (0.17 vs 1/6, prior entropy pinned at ln6) — Z carries
  no recoverable team signature; z_usage is non-collapsed only because it is
  near-uniform/unused; dur13/dur24 boundary truncation ~0.85-1.0 invalidates
  duration reads. Task: regresses vs the S-base ref (cov 0.10-0.15 vs ~0.42,
  cov_eq1_step_frac pinned at 0.0). Sampled+held Z with atomic AR reassignment
  is decorative AND harmful here (churn without coordination content). Stop rule
  triggered: NO seed 2, NO K/coef sweep on this design; fix the pi_Z/AR
  assignment path before any further team-intent run. Full readout:
  `ExpRecord.md` -> `EXP-20260705-r21-team-intent` Result block. This is the
  commitment-vs-recognition (R14.0) answer on the mainline so far: restoring a
  sampled team code did NOT make the team channel non-vacuous. Feeds directly
  into the R22 two-clock ELBO question (can sampled Z be made non-vacuous at
  all). The launch-ready command details are preserved in the ExpRecord entry.
- Active HMASD baseline status (2026-07-05): current-env baseline is pre-registered as `EXP-20260705-hmasd-currentenv-baseline` with cloud runner `scripts\run_hmasd_currentenv_baseline_cloud_64env.sh`. It uses `hmasd_original`, S7-S1, `--n_agents 6`, 64 env, ~1e6 steps, seeds 1 and 2, and now logs HA-CTSE parity eval metrics (`coverage_eq1_step_fraction`, `coverage_eq1_episode_fraction`, `zero_throughput_episode_fraction`, `throughput_gt5_step_fraction`). This is a logging-only change to the HMASD path.
- Active cloud package (2026-07-06): R21/R22 overnight runtime package is ready
  at `dist\ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip`; upload
  this timestamped zip directly, then run server-side `--dry-run` before
  launching.  This runtime zip intentionally excludes `memory/`; memory remains
  local collaboration state.  README:
  `dist\HA_CTSE_R21_R22_OVERNIGHT_UPLOAD_README.md`.
- Pending canonical-description candidate (2026-07-05): Claude/Research
  Copilot wrote `memory/ALGORITHM_DESCRIPTION_v6.md`. Codex reviewed it in
  `memory/cross_validation.md` as modified-acceptance, pending user
  confirmation. Treat v6 as a strong conceptual synthesis of the current
  three-timescale HA-CTSE direction, not yet as the sole canonical reference
  that `ALGORITHM_PRINCIPLES.md` points to. Before promotion, add an
  implementation/validation status box distinguishing implemented code,
  locally validated wiring, experiment-supported behavior, and theoretical /
  intended claims.
- Superseded Round 20 disposition (2026-07-04): the Team bridge g_tau is DEPRECATED-IN-PLACE (Codex three-pass audit + CC review pass/design lead ruling, cross_validation "Round 20 disposition"). No new mechanism may condition on g; no code change while R16.5 is in flight; `team_bridge_none` ablation queued post-a2_plus_t; the coordination-intent slot is reserved for kappa* (deceptive-axis trigger, built with its own pressure, never refactored from g). Official vocabulary: situation substrate (c/omega/kappa) vs coordination intent (kappa*).
- Active workflow rule: use LongTimeMemory completion sync after every task; update affected memory files and this pointer before final response.
- Active memory-location rule (2026-07-05): memory should be project-local and
  git-tracked by default (`C:\project\HMASD\memory`).  If a shared external
  memory root is used, create a project-name subdirectory and record the
  mapping here.  Do not mix multiple projects in one flat memory directory.
- Active Codex subagent protocol (2026-07-07): use `.codex/agents/manifest.yaml`
  as the source of truth for Codex subagent routing. `LongTimeMemoryManager`
  owns memory synchronization, `ExpManager` owns experiment scripts/packages/log
  records, `simple-patcher` owns small scoped code edits, `test-runner` owns
  focused checks, and `codebase-scout` owns read-only mapping. `memory/ExpRecord.md`
  keeps the experiment dashboard; `cross_validation.md` keeps source-aware
  advice, handoff, disposition, and modification metadata.
- Active implementation-authority rule (AMENDED 2026-07-07): Codex subagent
  routing is defined by `.codex/agents/manifest.yaml`. CC (Claude) may act as a
  code editor when the user explicitly authorizes it, and CC has already
  implemented R23 architecture changes directly. To avoid the R12-1a "two
  processes on the same path" accident, only one implementer should touch a
  given code path at a time; CC records every code change with modification
  metadata in `cross_validation.md`, uses TDD, and does not launch training runs
  without user authorization.
- Active monitoring cadence: R16/A2r runs are long. Routine experiment-status polling should be at most once per hour. Do not poll every small update. Detailed reads should happen only at pre-registered eval/gate points (320k, then each 160k eval interval through 960k) or when `runner_status.txt` appears / a real traceback is reported. Per-update reads are too frequent and should be avoided unless debugging an active crash.
- Do not do yet: do not claim P3-4 works before ablations. Reward injection exists only behind `--enable_skill_forcing_reward`; keep process posterior/topology-role/transition semantic rewards disabled for the first P3-4 read.
- Hard constraint from grilling: P3/P4 intrinsic reward must not directly use raw communication indicators or relabel environment reward as intrinsic. Environment reward remains external task return, especially for high-level skill-period cumulative targets. Fixed/shared lifetime collapse is not an acceptable HA-CTSE mechanism outcome. Duration entropy may be an annealed exploration bonus only.

## Non-Drift Core Instruction

The 2026-07-02 Round 12 GPT-5.5 Pro response is now superseded as the mainline
by the 2026-07-05 R22 GPT-5.5 Pro review.  Keep the useful anti-drift warning
against isolated individual skill-discriminator work, duration-set tuning,
decorative g-revival, and communication-metric shaping, but route new design
through the R21/v6 two-clock hierarchy:

```text
OPT recognition substrate
  -> sampled slow team intent Z
  -> asynchronous individual response skills z_i
  -> team/individual discriminator-style pressure and derived entropy terms
  -> two-clock ELBO before any new reward module
```

Legacy Round 12 wording retained below for historical context only:

```text
Do not let HA-CTSE drift into isolated individual skill-discriminator work,
duration-set tuning, decorative g-revival, or environment-specific communication
shaping.

The core task is to test whether OPT can provide a continuously recognized
interaction situation, and whether skills can be learned as responses to that
situation:

  OPT prototypes / omega / compact context
  -> discrete slow situation kappa
  -> situation-conditioned response skill z_i
  -> situation-change hazard beta_i
  -> situation-effect discovery via SEF/DADS
  -> optional target situation kappa*
  -> optional co-edit complementarity

Stage 0 comes first: the substrate gate plus HMASD current-env gap
re-verification.  Do not inject SEF/DADS reward or build target-situation /
co-edit mechanisms until omega/c/kappa passes G-DWELL, G-OUTCOME, and G-ROLE,
or follows the pre-registered fallback decision tree.
```

## Pointer Map

| Area | File | Section / anchor | Why read it |
| --- | --- | --- | --- |
| Codex subagent roster | `.codex/agents/manifest.yaml` | whole file | Routes work to current Codex subagent profiles. |
| Experiment scan | `memory/ExpRecord.md` | `Experiment Dashboard` | Fast scan for current running / launch-ready / completed experiments before reading detailed entries. |
| Research contract | `memory/ALGORITHM_PRINCIPLES.md` | `P3: Conditional Skill-Effect Discovery` | Defines the current replacement for HMASD-style discoverer/discriminator pressure. |
| Research correction | `memory/ALGORITHM_PRINCIPLES.md` | `2026-07-01 correction after Round 7 external review` | Reward-off gain is diagnostic, not a permanent forcing-loop gate. |
| Research boundary | `memory/ALGORITHM_PRINCIPLES.md` | S7-S1 objective and general MARL objective boundary near the top | Clarifies that backhaul/recovery are diagnostics, not the final objective. |
| Research boundary | `memory/ALGORITHM_PRINCIPLES.md` | `User clarification 2026-07-01` entries | Records coverage==1.0 half-step parity, fixed-lifetime collapse rejection, env-reward/intrinsic separation, and no raw communication metrics in P3/P4 reward. |
| Execution plan | `memory/IMPLEMENTATION_PLAN.md` | `P3 Candidate (conditional) - Conditional Skill-Effect Discovery` | Describes what P3 is supposed to implement. |
| Stage ledger | `memory/IMPLEMENTATION_PLAN.md` | `P3 staged task ledger`, `P3-2d observed effect target/extractor revision`, `P3-2e skill-conditioning capacity audit`, `P3-4a`, `P3-4b`, and `Round 7 forcing-loop correction` | P3-4 mainline is residual discriminator forcing plus effect residual auxiliary. |
| Stage ledger | `memory/IMPLEMENTATION_PLAN.md` | `Round 8 hardening response` | New immediate hardening: effect residual composition and fixed-duration forcing control. |
| Stage ledger | `memory/IMPLEMENTATION_PLAN.md` | `Round 10 / GPT review synthesis: cooperative half before more individual forcing` and `P4-1 / G2 Stage A implemented` | Records the live-g audit result and implemented default-off decision-level g-info objective. |
| Research correction | `memory/ALGORITHM_PRINCIPLES.md` | `2026-07-02 OPT-specific Round 10 correction` | Defines OPT as descriptive interaction basis and `g` as controllable prototype-response code over fixed `(c_tau, omega_tau)`. |
| Research contract | `memory/ALGORITHM_PRINCIPLES.md` | `2026-07-02 Round 12 substrate-gate correction` | Formal substrate gate contract and fallback decision tree before hazard/SEF/target-situation work. |
| Research contract | `memory/ALGORITHM_PRINCIPLES.md` | `2026-07-02 Round 12 Stage 1 boundary` | Defines reward-pure situation-change renewal as the first post-gate mechanism and keeps `learned_beta` inference-only until a real hazard PPO update exists. |
| Research contract | `memory/ALGORITHM_PRINCIPLES.md` | `2026-07-03 Round 14 Stage 1 prototype-response principle` | Current mainline: sampled prototype-response `z_i` over OPT situation coordinates and non-vacuous individual discriminator pressure. |
| Research contract | `memory/ALGORITHM_PRINCIPLES.md` | `2026-07-04 Round 16 roster-docking principle` | Defines the async analogue of HMASD AR: renewing agents dock against active teammate skill roster and ages. |
| Execution plan | `memory/IMPLEMENTATION_PLAN.md` | `Round 12 Substrate Gate (Active Candidate Stage 0)` | Current next implementation stage: CSV triage, eval-only omega dump, offline substrate analysis, HMASD gap re-verification. |
| Execution plan | `memory/IMPLEMENTATION_PLAN.md` | `R14 Stage 1 prototype-response implementation result` | Current implemented code stage and validation status; blocks Stage 2 until the local probe read is non-degenerate. |
| Execution plan | `memory/IMPLEMENTATION_PLAN.md` | `R16 roster-docking amendment` and `Pre-implementation guards from CC` | Next code direction: add `ar_prefix_mode=same_check|roster`; must store roster snapshots, test old-logp consistency/full-sync reduction, use `roster_ar_kl_shuffled`, and log `selection_independence_deficit`. |
| Execution plan | `docs/superpowers/plans/2026-07-02-r12-stage1-overnight-auto-task.md` | whole doc | Concrete overnight automation plan: wait for current training, then sequentially launch Stage 1 `diag_only` and `oracle_change` local CUDA runs. |
| External advice | `memory/cross_validation.md` | `R12.5 Substrate gate (2026-07-02 addendum, from user/Codex challenge)` | Upgrades offline dwell diagnostic into the precondition for all Round 12 downstream mechanisms: G-DWELL, G-OUTCOME, G-ROLE, zero-new-run checks, frozen-encoder protocol, and one-retrain-cycle fallback tree. |
| External advice | `memory/cross_validation.md` | `R12.6 GPT-5.5 Pro response after Round 12: OPT-first Situation-Response Skill Discovery` | Current strongest candidate mainline: OPT situation recognition -> response skill -> situation-change hazard -> SEF/DADS. Read before any new P4/P3 implementation. |
| External cross-validation | `memory/cross_validation.md` | `Round 13 (2026-07-03) - Cross-validation handoff index for external reviewers` | First-read packet for Claude/GPT/other reviewers: current thesis, memory reading order, reference paper index, code/experiment state, and questions to answer. |
| Workflow metadata | `memory/cross_validation.md` | `Required metadata for every accepted modification` | Detailed dialogue and modification metadata standard; use for all plan/code/script/package/experiment-gate changes. |
| External cross-validation | `memory/cross_validation.md` | `2026-07-03 Codex response to Round 14 Stage 1 implementation task` | Records accepted Round 14 task, implementation boundaries, validation, and next experiment gate. |
| External cross-validation | `memory/cross_validation.md` | `2026-07-03 CC (Claude) response to Round 13 handoff Q1-Q6` and `2026-07-03 Codex response to Round 13 Claude readout` | Corrects R12-1b interpretation: current kappa is env-global, so R12-1b tests global boundary guard/rate, not a real per-agent hazard. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260702-substrate-gate` | Active pre-run record for R12 Stage 0. Contains the checkpoint-grid requirement, G-ROLE label-variance trap, pre-registered thresholds, and four-branch decision tree. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260703-r12-1b-conservative-renewal` | Planned local CUDA first read for conservative situation-change renewal after R12-1a oracle_change churned. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260703-r14-stage1-prototype-selection` | Stale/superseded R14 local read. Latest `run_20260703_154805` reached 160k with weak probe signal; stop recommended before entering stale `s1_reward`. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260704-r16-a2r-remote-parallel` | Current remote package/run plan for multi-server R16/A2r arms; use this before uploading or reading cloud logs. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260704-r16-5-coef01-entfloor` | Active R16.5 stabilization gate: one-variable duration entropy floor rerun plus deterministic/stochastic eval-mode reads on update_60/update_120. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260702-r12-stage1-situation-hazard` | Active R12 Stage 1 local CUDA record for diag-only versus reward-pure oracle situation-change renewal. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260630-p3-stage-a-probe` | Completed negative reward-off probe and gate readout. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260630-p3-2b-reward-off-probe` | Completed 320k readout; gate failed, next decision is P3-2c. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260630-p3-2c-intervention-probe` | Completed local 320k read; records the P3-2c gate result. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260630-p3-2d-observed-effect-probe` | Planned local reward-off probe for the revised effect targets. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260701-p3-4-forcing-first-ablation` | Next active experiment: first controlled with-force P3-4 ablation. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260701-g-info-objective-probe` | Completed negative Round 10 G2 experiment: weak g-info objective did not revive g. |
| Experiment ledger | `memory/ExpRecord.md` | `EXP-20260701-p3-2d-overnight-suite` | Reward-off diagnostic suite; no longer blocks P3-4. |
| Local diagnostic run | `memory/ExpRecord.md` | `EXP-20260630-local-kmatrix-quick` | Tracks local fixed/shared/variable lifetime sanity run. |
| External advice | `memory/cross_validation.md` | `2026-06-30 Codex response: P3 Stage A reward-off probe implemented` | Records accepted Stage A scope and no-reward-path boundary. |
| External advice | `memory/cross_validation.md` | `Round 8 (2026-07-01)` and `2026-07-01 Codex response to Round 8 decoupling + P3-4 code audit` | CC audit found raw-effect contamination and missing fixed-duration forcing control; Codex accepted. |
| External advice | `memory/cross_validation.md` | `Round 9 (2026-07-01)` and `2026-07-01 Codex response to g-revival precision update` | CC/GPT cross-validation: decoupling has incurred costs without proven benefit; duration/skill co-selection is the shortcut source; discovery source yields distinguishable-not-useful skills; `g` must be revived by a real training path, not by AR editor form alone. Codex accepted: audit `g` reward/loss path before cooperative reward implementation. |
| Design inspiration | `memory/HACTSE_P4_highlevel_design_inspiration.md` | whole doc | P4 high-level co-design: persistent team-intention `g` + asynchronous docking + counterfactual composition credit. Concrete mechanisms M1-M6 (recurrent g, joint discriminator wired into g, roster-attention AR docking editor, effect-prototype set-coverage, counterfactual skill credit, hazard lifetimes), MVP order, falsifiable predictions. Contains HMASD as the all-edit-together special case. |
| External advice | `memory/cross_validation.md` | `Round 10 (2026-07-01)` + `memory/HMASD_HACTSE_research_review_20260701_Claude.md` | Full HMASD-paper-grounded review. Key finding: HMASD's 4 ablation-confirmed load-bearing parts are team skill, individual skill, intrinsic discriminator reward, and autoregressive complementary coordinator; HA-CTSE kept the individual half but the cooperative half is weak/absent. Codex accepted the modified roadmap: keep individual forcing, but add P3-2e and cooperative-half diagnostics/design before trusting more long P3-4 sweeps. |
| External advice | `memory/HMASD_HACTSE_research_review_20260701_gpt.md` | Full GPT review | Practical P3/P4 correction: P3 must be low-level skill-effect forcing, not posterior scoring; fix residual effect reward, fixed-duration same-forcing controls, task-generic advantage/value usefulness coupling, and duration entropy annealing. Accepted with the no-communication-reward boundary. |
| Workflow skill | `C:\Users\wu\.codex\skills\long-task-memo` | `Completion Sync` and `Attention Pointer Rules` | Defines how future Codex turns should keep memory and code aligned. |

## Code Pointers

| File | Status | Why it matters |
| --- | --- | --- |
| `ha_ctse_process/substrate_gate.py` | Implemented R12 Stage-0 diagnostics | Pure gate math for G-DWELL, G-OUTCOME, and G-ROLE with fail-closed label validity checks. |
| `ha_ctse_process/prototype_response_discriminator.py` | R15-aligned | Default residual is `log q_d - stored null_logp`; learned situation-prior head exists only behind `prototype_disc_use_learned_prior` for R15-P1 fallback. |
| `ha_ctse_process/situation_substrate.py` | Updated R14 Stage 1 | Adds per-agent situation debouncer used for per-agent kappa diagnostics. |
| `ha_ctse_process/standalone_agent.py` | R19-aligned | Adds R15 skill/duration log-prob split, AR prefix conditioning, stored Segment null log-probs, plus R19 team-transition interval recording and high-level-only segment reward injection. |
| `ha_ctse_process/standalone_agent.py` | R16.5-aligned | Adds default-off duration entropy floor loss on the high-level duration head; logs floor active/gap/loss and duration policy entropy without changing reward inputs. |
| `ha_ctse_process/train.py` | R16.5-aligned | Adds `--enable_duration_entropy_floor`, `--reward_ratio_guard_mode kill|warn`, reward-ratio runtime guard metrics, and `--eval_action_mode deterministic|stochastic` for P2 eval divergence reads. |
| `ha_ctse_process/situation_transition.py` | Implemented R19 team engine | Clean DADS-style situation-transition residual heads: `log q(kappa'|kappa, xi)-log q(kappa'|kappa)`, own optimizer, detached inputs, no-grad reward. |
| `scripts/run_r15_stage1_local_cuda.ps1` | Updated R15/R19 runner | One-key local CUDA run for `control_legacy4`, `s1_probe`, explicit `s1_reward`, conditional `r15_p1_ablation`, plus R19 `a2_plus_t_probe` / `a2_plus_t`. |
| `scripts/run_r19_team_transition_64env.sh` | New R19 remote runner | Linux/cloud 64env/960k CUDA runner for R19-only `a2_plus_t_probe`, `a2_plus_t`, and optional `a2_baseline`. |
| `scripts/run_r16_5_p2_eval_modes.ps1` | New R16.5 eval wrapper | Runs deterministic/stochastic eval on update_60 and update_120 of `run_20260704_142053` for train/eval divergence diagnosis. |
| `tests/r14_prototype_response_test.py` | Updated R15 tests | Covers agent relevance/EMA drift, high policy omega/relevance/AR-prefix conditioning, stored-null discriminator residuals, and opt-in learned-prior fallback. |
| `tests/r19_team_transition_test.py` | New R19 tests | Covers input boundary, gradient separation, reward guard/clip, missing-kappa drops, self/change split, and interval-to-segment attribution. |
| `ha_ctse_process/export_substrate_gate.py` | Implemented R12 Stage-0 exporter | Eval-only checkpoint-grid dump for omega/compact/outcome/role artifacts; no reward or training-path change. |
| `scripts/analyze_r12_csv_triage.py` | Implemented R12 Stage-0 triage | Zero-new-run scan for existing OPT collapse/uniformity fields in `train_updates.csv`. |
| `scripts/analyze_r12_substrate_gate.py` | Implemented R12 Stage-0 analyzer | Offline substrate report over exported CSV artifacts; `--require_role_label_variance` guards against the G-ROLE all-zero trap. |
| `scripts/run_r12_substrate_gate_local.ps1` | Implemented R12 Stage-0 runner | One-key local dry-run/export/analyze wrapper for the real checkpoint-grid gate. |
| `scripts/run_r12_stage1_local_cuda.ps1` | Updated R12 Stage-1 runner | One-key local CUDA dry-run/run wrapper for `diag_only`, `oracle_change`, `oracle_conservative`, `oracle_strict`, and exploratory inference-only `learned_beta_small`. |
| `tests/r12_conservative_renewal_test.py` | New R12-1b tests | Covers conservative renewal guard, pending kappa-change pulse carry, min-age carry, and force-rate warm-up/cap behavior. |
| `ha_ctse_process/skill_effect_discovery.py` | Implemented first pass P3-2b | Adds group-balanced loss, per-horizon gains, field-specific gains, action~skill and target~skill diagnostics. |
| `ha_ctse_process/standalone_agent.py` | Implemented first pass | Wires reward-off `SkillEffectDiscoveryModule.update(valid, total_steps)`; does not consume returned rewards. |
| `ha_ctse_process/config.py` | Implemented first pass P3-2b | Adds `skill_effect_group_balanced_loss=True`; defaults still keep reward off. |
| `ha_ctse_process/train.py` | Implemented first pass P3-2b | CLI/manifest/TensorBoard/console integration for group-balanced probe fields. |
| `ha_ctse_process/plotting.py` | Implemented first pass P3-2b | Adds P3-2b CSV fields and `ha_ctse_skill_effect_p3_2b.png`. |
| `ha_ctse_process/smoke.py` | Implemented first pass P3-2b | Checks new P3-2b metrics and reward-off guards. |
| `ha_ctse_process/skill_effect_discovery.py` | Implemented P3-2c first pass | Adds forced-z intervention metrics over action-distribution and predicted-effect distances. |
| `ha_ctse_process/standalone_agent.py` | Implemented P3-2c first pass | Provides diagnostic low-actor forced-skill action-distribution callback; does not mutate rollout hidden state or rewards. |
| `scripts/run_s7s1_local_overnight.ps1` | Existing diagnostic runner | Local sanity runner; not final performance evidence. |
| `scripts/run_p3_2d_overnight.ps1` | New overnight runner | One-key 8-10h local P3-2d reward-off suite; supports `-DryRun` and experiment filtering. |
| `ha_ctse_process/skill_effect_discovery.py` | Implemented P3-4 first pass | Adds `ResidualSkillDiscriminator`, `ShortcutSkillHeads`, `SkillEffectIntrinsicComposer`, force metrics, and micro-window low reward outputs. |
| `ha_ctse_process/g_info_objective.py` | Implemented Round 10 G2 Stage A | Adds decision-level g liveness diagnostics and default-off usage loss over skill/duration decisions. |
| `ha_ctse_process/standalone_agent.py` | Implemented P3-4 first pass | Applies force micro-window rewards over rollout indices only when gate is active. |
| `ha_ctse_process/standalone_agent.py` | Implemented Round 10 G2 Stage A | Wires `GInfoObjective` into high-level PPO loss without feeding g/c to the low-level actor. |
| `ha_ctse_process/config.py` / `ha_ctse_process/train.py` | Implemented P3-4 and G2 first passes | Adds forcing and g-info CLI, manifest, console, and TensorBoard fields. |
| `ha_ctse_process/plotting.py` | Implemented P3-4 and G2 first passes | Adds `ha_ctse_skill_forcing_reward.png` and g-info metrics in process diagnostics. |
| `ha_ctse_process/train.py` / `ha_ctse_process/eval_checkpoints.py` | P3-4 readout support | Eval now logs `coverage_eq1_step_fraction`, `coverage_eq1_episode_fraction`, zero-throughput and throughput>5 step diagnostics. |
| `scripts/analyze_p3_4_forcing.py` | P3-4 readout support | Offline comparison script for downloaded cloud logs; reports force gate, shortcut, lifetime collapse, and coverage==1.0 success metrics. |
| `scripts/run_p3_4_forcing_cloud_32env.sh` | New cloud runner | One-key 32-env Linux P3-4 long sweep. |
| `scripts/run_g_info_objective_local_cuda.ps1` | New local CUDA runner | One-key Round 10 G2 local suite: diagnostic-only vs small g-info objective. |
| `scripts/check_g_info_progress.ps1` | New local monitor | Reads `logs\ha_ctse_process_g_info_local_cuda` and writes `_monitor\g_info_progress_latest.txt` summaries. |
| `scripts/register_g_info_monitor_task.ps1` | New local monitor registrar | Registers Windows task `HA-CTSE GInfo Progress Check` to run the g-info monitor every 8 hours. |
| `ha_ctse_process/g_info_objective.py` | P4-1b REVERTED 2026-07-02 | The unit-weighted MI probe / grad-scale diagnostics were removed; file is back to the G2 Stage-A state. Reference design in `ExpRecord.md` -> `EXP-20260702-p4-1b-grad-probe`. |
| `dist/ha_ctse_p3_4_forcing_bundle_clean_20260701_020030_v2.zip` | New upload bundle | Clean cloud package with P3-4 code, envs, hmasd compatibility, scripts, memory, and `routing_protocols.py`. |

## Experiment Pointers

| Experiment | Status | Read after | Decision meaning |
| --- | --- | --- | --- |
| `EXP-20260703-r15-stage1-steering` | A1 finished update 40 / 320k; prefix wiring passed; Round 16 starvation measured; roster-docking code implemented and smoke-tested | Run A2r (`s1_reward` + `--ar_prefix_mode roster`) and read `roster_ar_kl_shuffled`, `selection_independence_deficit`, reward scale, entropy, and task metrics | A1 renews only ~1.44 agents/check with full_sync_rate=0, so same-check AR is starved. Prefix input is wired; A2r tests whether active-roster context restores async sequential assignment. |
| `EXP-20260704-r16-a2r-overnight-local` | Planned; runner created | `logs\ha_ctse_r16_a2r_overnight_local_cuda\run_*` after default suite completes | Overnight suite compares roster reward, lower-coef roster reward, same-check reward, and roster reward-off probe. It is the immediate R16 decision read. |
| `EXP-20260703-r14-stage1-prototype-selection` | Stale restart stopped after 160k read | Do not continue as mainline; preserve only as R14/R15-P1-style reference | 160k `s1_probe_no_reward` has proto_acc below prior, negative proto_resid, near-zero proto_align, coverage_eq1_step_frac=0.0, and lacks R15 stored-null/AR diagnostics. |
| `EXP-20260703-r12-1b-conservative-renewal` | Planned local CUDA first read | After `diag_only`, `oracle_conservative`, and `oracle_strict` complete | Read only as a guarded env-global boundary diagnostic. Positive result triggers `random_matched` + `boundary_gated` controls; negative result triggers G-ACTIONABILITY / renewal-criterion rethink, not guard-constant tuning. |
| `EXP-20260702-r12-stage1-situation-hazard` | Completed; oracle_change gate failed | Already read clean run `logs\ha_ctse_r12_stage1_local_cuda\run_20260703_001552` | Stage 1 wiring works, but first-pass oracle renewal adds churn and hurts stability; next is conservative debounce/min-age/rate-cap renewal before learned_beta PPO. |
| `EXP-20260702-substrate-gate` | Completed local 16env compact-full gate read | Before long Round 12 runs, repeat on true 32env grid if available | Stage 0 local gate passed for omega and compact_cluster; still not final performance evidence. |
| `EXP-20260630-local-kmatrix-quick` | Running/partially complete at last record | Local suite completion | Diagnose fixed/shared/variable behavior only; do not claim final performance. |
| `EXP-20260630-p3-stage-a-probe` | Completed negative | Already read | Gate failed: no clean effect gain; revise P3-2b target/model/audit before any reward path. |
| `EXP-20260630-p3-2b-reward-off-probe` | Completed negative at 320k | Already read | Probe improved diagnostics but failed non-shortcut gate; do P3-2c before any reward path. |
| `EXP-20260630-p3-2c-intervention-probe` | Completed at 320k | Already read | z changes low-level actions, but effect target/model/horizon still fail the non-shortcut useful-effect gate. |
| `EXP-20260630-p3-2d-observed-effect-probe` | Planned | After 160k/320k or if reward guards trip | Decide whether revised end-state/window targets justify P3-3 usefulness audit or need another extractor/context revision. |
| `EXP-20260701-p3-2d-overnight-suite` | Partially completed/read | Already read 2/4 arms | `main` and `dense_short` completed to 320k; passive effect gain stayed near zero/negative after baselines, so do not expand passive P3-2 as mainline. |
| `EXP-20260701-p3-4-forcing-first-ablation` | Planned next | After 160k/320k per arm | Decide whether residual forcing opens the HMASD-like skill differentiation loop without fixed-duration collapse or communication-metric bias. |
| `EXP-20260701-g-info-objective-probe` | Completed negative | Already read at 320k | Weak coefficient decision-level usage pressure did not revive g; proceed to P4-1b objective scale/gradient hardening before P4 team/joint mechanisms. |
| `EXP-20260702-p4-1b-grad-probe` | Design only; code reverted 2026-07-02 | After Codex reimplementation + grad_diag/grad_obj_strong (32k each) | Decides scale vs path vs objective-form for the g-info failure; pre-committed rule in ExpRecord selects normalized sweep, wiring fix, or escalation to team/joint discriminator reward. |

## Completion Sync Checklist

Before ending a task:

1. If the algorithm meaning changed, update `ALGORITHM_PRINCIPLES.md`.
2. If stage status or next implementation step changed, update `IMPLEMENTATION_PLAN.md`.
3. If an experiment was proposed, launched, stopped, or interpreted, update `ExpRecord.md`.
4. If outside advice was used, update `cross_validation.md` or the active advice file with response status.
5. Always update this pointer when current focus, section anchors, code pointers, experiment pointers, or next action changed.

## Last Update Notes

- 2026-07-07 (R23-next matrix PARTIAL interim read, ExpManager / CC): Local
  32env run (`logs_r23_next_mechanism_matrix_local`) was killed externally at arm1
  update 18/20 (status "killed", no traceback). arm0 (arch-only) completed. **arm1
  (q_A probe) is a POSITIVE interim**: q_A `residual_gain` rises monotonically u12→u18
  to +0.097 (accF 0.333 > accP 0.236), forced-Z KL stable ~0.045, z_ent healthy — the
  actionability-LEARNING signal g-info could not produce (confirms the T2 SCALE/FORM
  verdict + the q_A pivot). team_disc still ~chance → the q_D audit (arm3) that would
  diagnose it did NOT run; arm2 (q_A reward) did NOT run. CAVEAT: 1 seed, probe-only,
  288k not 320k, arm0 not a bit-matched control (RNG desync). Full read: `ExpRecord.md`
  → `EXP-20260707-r23-next-mechanism-matrix`. Decision pending user: resume arm2+arm3
  (and optionally finish arm1 to 320k). Nothing committed.
- 2026-07-06→07 (R23-next IMPLEMENTED, CC implementer — user "do all the jobs now"): Built
  the full accepted forward plan (`docs/superpowers/plans/2026-07-06-r23-next-actionability.md`,
  T1–T5) TDD in the SB3 conda env. Decisive T2 result: g-info gradient audit = SCALE/FORM
  (grad <2% of PPO, self-stalling; not a wiring bug) → q_A confirmed as the actionability
  main line. New default-off modules `assignment_actionability.py` (q_A) + `team_effect_targets.py`
  (reward-off q_D target/timescale audit), wired into the high update / process_update with
  config+CLI+plotting fields; runner `run_r23_next_mechanism_matrix_cloud_64env.sh` (+.ps1),
  4 arms, dry-run validated. Tests: 12 new pass, 31/31 R23/R21/R19 regression, full suite 245
  pass (4 pre-existing failures stash-confirmed unrelated). Updated ExpRecord (launch-ready
  `EXP-20260707-r23-next-mechanism-matrix` row), cross_validation (EXECUTION block + modification
  metadata), R23 note §11, this pointer. No training run launched; nothing committed (user decides).
- 2026-07-06 (GPT R23-result advice cross-validated, CC review pass): Routed the
  updated `memory/advice_gpt.md` (post-320k-read forward plan) into
  `cross_validation.md` ("2026-07-06 GPT R23-result advice"); disposition
  ACCEPTED-WITH-MODIFICATIONS. GPT's read matches the log analysis. Accepted
  sequence (none launched, all pending user authorization): g-info gradient audit
  FIRST → Option-B q_A residual (PR-1, with a double-count audit vs g-info) →
  q_D effect target/timescale audit reward-off → small 320k mechanism matrix
  Arm0..3. Modifications: Option-B q_A and new q_D targets are algorithm changes
  requiring implementer + authorization (not a review pass build); the q_A term must land
  in PR-1 with an I(Z;ξ|c,ω) double-count check. Confirmed GPT's A/B/C from the CSV
  (arch KL stable early / g-info flat / disc at chance throughout). Wrote §11 forward
  plan into `R23_ACTIONABLE_TEAM_INTENT.md` and updated this pointer's R23 bullets.
  No code changed, no run launched, nothing committed.
- 2026-07-06 (R23 verdict read, ExpManager / CC): Read seed1 cloud logs
  `dist\logs_cloud_r23_actionable_team_intent_64env` (3 arms, 320k, all clean).
  MIXED result: R23-0 architecture capacity PASS in-training (forced-Z KL
  0.04–0.08 ≈ 20–50× R21 band); R23-1 actionability objective FAIL/null (g-info
  loss ~-2e-4, MI flat, objective-ON < objective-OFF → coef 0.02 too weak);
  R23-2 team-disc still at chance (acc 0.14–0.25 vs 1/6); R23-3 gate mechanics
  correct but reward ~0; task cov_eq1_step_frac=0.0 all arms. Blocker moved from
  "Z can't move ξ" (fixed) to "ξ doesn't map to a recoverable joint effect."
  Updated `ExpRecord.md` (dashboard row + new detailed
  `EXP-20260706-r23-actionable-team-intent` Result block) and the R23 bullet in
  this pointer's Current Focus. No code/principle change; no run launched. Next
  actions (pending user): stronger/annealed actionability objective or Option-B
  residual q_A; interrogate q_D effect target/timescale; no 960k/seed2 on this
  coef until a rising MI trend appears at 320k.
- 2026-07-06 (R23 cloud bundle packaged, CC packaging pass): Self-contained runtime zip
  `dist\ha_ctse_r23_actionable_cloud_runtime_20260706_180016.zip` (1.23 MB) with
  ha_ctse_process (R23 code), envs, hmasd, config_1/config, requirements_server.txt,
  scripts (incl. the R23 cloud runner + capacity gate), tests, and
  `R23_UPLOAD_README.md`. Excludes memory/logs/models (matches the runtime-zip
  convention). Verified self-contained (isolated-PYTHONPATH import OK, R23 flags
  present, runner emits 3 arms). Server: unzip → `pip install -r
  requirements_server.txt` → `bash scripts/run_r23_actionable_team_intent_cloud_64env.sh
  --dry-run` → launch with EXPERIMENTS=r23_arch_only,r23_1_action,r23_3_reward.
- 2026-07-06 (R23-2/R23-3 IMPLEMENTED + runners written, CC implementer): R23-2 (q_D
  probe) needs no new code — the existing `--enable_team_disc_probe` runs on top of
  R23-1. R23-3 (q_D reward) got the hard actionability gate:
  `team_disc_actionability_floor` (default 0.0 = no gate). Gate:
  `_team_disc_actionability_gate_open()` allows the q_D reward only once the last
  measured forced-Z skill KL (`g_itv_kl_skill`, cached by the high update) ≥ floor;
  else `team_disc_reward=0` and logs `team_disc_reward_gated_off`/`team_disc_forced_z_kl`.
  TDD: gate test 6/6 R23 pass, 7/7 R21 pass (13 total). Smoke: reward gated OFF at
  update 1 (KL 0), applied at update 2 (KL 0.059 ≥ floor 0.05), then the pre-existing
  ratio guard killed the degenerate tiny-smoke ratio (expected, composes correctly).
  Runners written + dry-run validated: `scripts/run_r23_actionable_team_intent_cloud_64env.sh`
  (Linux/CUDA/64env, arms r23_arch_only/r23_1_action/r23_3_reward, Choice-1 K=8/dur
  1,2,3,4) and `scripts/run_r23_actionable_team_intent_local_cuda.ps1` (local mirror).
  READY for the user's server overnight run. All R23 mechanisms default-off; the
  overnight run is the first verdict read (does forced-Z KL/MI rise + task health hold,
  and does the gated q_D reward help once actionability passes?). Nothing committed.
- 2026-07-06 (R23-1 actionability objective IMPLEMENTED via DRY reuse, CC implementer):
  Found that R23-1 Option A already exists as `GInfoObjective` (the Round-10 g-info
  objective): enumerates Z, computes `I(Z; skill/duration | c,ω)`, coef/warmup/anneal,
  default-off, already wired into the high update. It FAILED in Round 10 only because
  Z was decorative — the exact defect R23-0 fixes. So R23-1 = no new module (DRY /
  mechanism-budget): `--z_assignment_residual_gain <0.3-0.5> --enable_g_info_objective
  --g_info_coef_skill <small>` + Choice-1 (`--team_intent_k 8 --skill_lifetime_candidates
  1,2,3,4`), q_D reward OFF. Recipe in R23 note §4. Verified: tests show actionability
  live with residual (`g_info_skill_mi>0.02`, loss<0) and decorative without (`<0.005`,
  reproduces Round-10 failure); 128-step smoke ran clean (skill MI≈0.023, forced-Z KL
  ≈0.099 ~50× the R21 band, no guard kills). CAVEAT: smoke = live-wiring proof, NOT the
  verdict; the real R23-1 read (MI/forced-Z-KL RISE + task health hold) needs a GPU run
  + authorization. NEXT: authorize the R23-1 run; then R23-2 q_D probe (reward still
  gated to R23-3 behind the forced-Z-KL floor).
- 2026-07-06 (R23 architecture correction IMPLEMENTED, CC implementer — user expanded
  role to code-editor/executor): The active line is now **R23: Actionable Team
  Intent** (design `memory/R23_ACTIONABLE_TEAM_INTENT.md`; v6 sampled-Z is negative
  evidence). R23-0 static capacity gate confirmed the current architecture routes Z
  with ~noise gain (forced-Z skill KL ~0.002 at random-init AND final → FAIL vs 0.02
  gate). Implemented the §3 fix default-off: `z_assignment_residual_gain` (config +
  `--z_assignment_residual_gain` CLI + `SkillDurationPolicy` residual logit path;
  low-level actor still blind to Z/c; S-base selection path untouched). Verified:
  flag-on random-init PASSES (skill KL 0.12, 60× band); flag-off keeps S-base
  bit-identical; `tests/r23_actionable_team_intent_test.py` 3/3 + `r21_team_intent_test`
  7/7; `scripts/r23_capacity_gate.py` is the reusable gate. (3 pre-existing unrelated
  test failures confirmed present at HEAD via stash — not caused by this change; a
  known `log_dir`/SimpleNamespace eval-harness issue + two prototype/process tests.)
  HMASD current-env baseline is DROPPED as a blocking premise (user: it is solid /
  well-tested; at most one appendix run). NEXT (needs authorization + GPU): R23-1
  actionability objective (small warmed/annealed gain + `I(Z;π_z)` usage loss or
  residual q_A, no q_D reward, Choice-1 K=8/durations{1,2,3,4}); do NOT enable q_D
  reward until the forced-Z-KL floor + q_A gain gate pass. Full staged matrix
  R23-0..R23-4 in the R23 design note. NOTE: gain=1.0 is strong (demonstrates
  capacity); training must use a small annealed gain.
- 2026-07-06 (GPT post-autopsy advice cross-validated, CC review pass): Routed the
  updated `memory/advice_gpt.md` into `cross_validation.md` ("2026-07-06 GPT
  post-autopsy advice"); disposition accepted-with-modifications. GPT accepts the
  autopsy and retracts its earlier "trained-out" and "churn-cause" framings.
  Applied: (1) autopsy-CONFIRMED principles amendment (v6 sampled-Z demoted to
  negative evidence; `I(Z;ξ)` REQUIRED; `q_D` forbidden without a forced-Z-KL
  actionability floor; K≈episode a forbidden two-clock setting; NEW static
  architecture-capacity gate before R23). (2) R22 ELBO addendum (capacity gate,
  Choice-1 short-duration/K≈8-12 lifetime resolution, entropy derived-vs-stabilizer,
  no SAC auto-temp yet). (3) Surgical `.gitignore` fix — canonical `memory/*.md` +
  `docs/superpowers/plans/*.md` are now git-trackable (backup_* stays ignored);
  makes the "git-tracked memory" claim accurate. NOT committed — user decides
  whether to `git add`/commit. Next actions (all pending user go-ahead; none are
  CC's to launch): design lead draws PR-1 two-clock ELBO + R23 static capacity-gate
  design; ExpManager runs the HMASD current-env baseline (top unverified
  premise, GPU). No R21 sweep, no R23 reward build before PR-1 + the capacity gate.
- 2026-07-06 (R21 autopsy COMPLETE, CC implementer): Read-only forensic autopsy done;
  full report `memory/R21_AUTOPSY_REPORT.md`. Classification: PRIMARY
  **true-objective-failure** (no cross-layer `I(Z;ξ|c,ω)` actionability term). Audit
  B = aligned-real (team-disc data contract correct; disc-at-chance is genuine, not
  a bug — verified via lockstep trace + held-out control). Audit A = Z near-inert:
  forced-Z assignment KL ≈0.002 at BOTH random-init and final → Z was never made
  actionable (refutes GPT's "trained out"). Audit C = truncation-contaminated +
  `team_intent_k=48 ≈ episode=50` confound → ~one Z commitment/episode (two-clock
  degenerated to one-clock); churn is once-per-episode near-terminal so it is NOT
  the regression cause (regression is the forced AR-roster/Z-conditioning
  policy-path swap). ELBO implications written into `R22_TWO_CLOCK_ELBO.md`: promote
  `I(Z;ξ)` to required, gate team-disc reward behind a forced-Z-KL floor, fix
  K≈episode before any rerun. No code modified, no training run, no fix needed
  (no bug). Diagnostic scripts in job tmp. cross_validation.md has the implementer entry.
- 2026-07-06 (GPT R21 review cross-validated, CC review pass): Routed
  `memory/advice_gpt.md` into `cross_validation.md` ("2026-07-06 GPT review of
  R21 negative read"). Disposition: accepted-with-modifications. Accepted: stop
  R21 (no seed2/sweeps), R21 is mechanism-negative (conditional on a disc-sanity
  audit), read-only autopsy A/B/C, PR-1 two-clock ELDO derivation with
  `I(Z;xi|c,omega)` promoted optional->candidate-necessary, demote the v6
  sampled-Z "commitment layer" claim (labeled amendment added to
  `ALGORITHM_PRINCIPLES.md` Active R22 Contract), and HMASD current-env baseline
  ELEVATED to the top unverified blocking premise. Deferred/modified: the
  "atomic reassignment = harmful churn" causal claim (hypothesis pending Audit C)
  and the forward "R23/actionability-first" objective form (proposal pending the
  ELBO). CC did not write code or launch runs; autopsy + PR-1 are Codex tasks
  pending user authorization. Next actions queued: {PR-1 ELBO, autopsy A/B/C,
  HMASD current-env baseline} — no R21 sweep, no new mechanism build first.
- 2026-07-06 (R21 team-intent negative read, ExpManager / CC): Read
  seed-1 cloud logs `dist\logs_cloud_r21_team_intent_64env`. Both arms finished
  clean at 960k. Result: NEGATIVE on both the 320k structural gate and the 960k
  performance gate — `z_assignment_itv`≈0 (decorative), `team_disc_acc`≈random,
  heavy long-duration boundary truncation, and task regression vs the S-base
  (cov 0.10-0.15, cov_eq1_step_frac=0.0). Updated `ExpRecord.md` dashboard row +
  detailed Result block and this pointer's R21 bullet. No code/principle change;
  stop rule invoked (no seed 2, no coef/K sweep). No new experiment launched.
- 2026-07-04 (R19 team-transition implementation, Codex): Implemented `docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md`. Added `ha_ctse_process/situation_transition.py`, default-off team-transition config/CLI/checkpoint/logging/plotting support, high-level-only segment reward accumulation, and `a2_plus_t_probe/a2_plus_t` runner arms. Validation: `pytest tests\r19_team_transition_test.py -q` -> 6 passed; `pytest tests\r14_prototype_response_test.py -q` -> 13 passed; AST compile OK; R19 runner dry-run passed; tiny reward-on smoke and checkpoint save/load/eval smoke passed. `EXP-20260704-a2-plus-t` remains trigger-blocked until A2 OUT-OF-GAS or explicit user decision.
- 2026-07-04 (R19 remote package, Codex): Created R19-only cloud bundle `dist\ha_ctse_r19_team_transition_64env_bundle_20260704_213707.zip` and runner `scripts/run_r19_team_transition_64env.sh`. Corrected an intermediate mixed R16/R19 packaging direction: R16 four-arm roster sweep is separate and already running; this R19 package defaults only to `a2_plus_t_probe,a2_plus_t`, with optional `a2_baseline` only if no matched A2 same-check control exists. Static zip verification passed; local bash dry-run unavailable on Windows, so server-side `bash scripts/run_r19_team_transition_64env.sh --dry-run` is required before launch.
- 2026-07-04 (R17-R19 memory sync, CC/Cowork): Synced the cross-model review cycle into memory. `ALGORITHM_PRINCIPLES.md` gains the Rounds 17-19 principle-corrections block (exogenous variation not persistence; two-layer symmetry theory + atomic-variation deficit; kappa* as canonical commitment form with noise-on-recognition rejected; 2x2 task matrix with S7-S1 in the neither-mechanism corner; dual-engine principle; kappa dual-use churn caution; prior-mixed-null mitigation). `IMPLEMENTATION_PLAN.md` gains the Round 19 Team-Transition Engine section and a supersession note pulling the team term out of the old Stage-2 blanket hold. `ExpRecord.md` gains the trigger-blocked `EXP-20260704-a2-plus-t` pre-registration (improvement-required task gate, kills, stop rule, churn precursor). Final implementation reference for Codex: `docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md`. No training code changed by CC (implementation-authority rule).
- Change-log entries before 2026-07-04 (R12/R14/R15/P3 era) were condensed on 2026-07-06; see the Experiment Pointers table above and `memory/backup_20260706/ATTENTION_POINTER.md`.
