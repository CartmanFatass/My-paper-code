# HA-CTSE Implementation Plan

This plan is based on inspecting the live repo on 2026-06-23.

## Corrected Research Target

The active objective is S7-S1 parity with HMASD.  The previous "100M steps"
wording should be read as a mistake; for the current stage, `1e6` environment
steps is the more normal long-run budget scale.

S7-S1 is relatively simple and HMASD can nearly solve it.  Therefore HA-CTSE
should first reach HMASD-level behavior on S7-S1 before spending the main effort
on S7-S3.  S7-S1 remains a real performance gate, not only a smoke test.
The clarified parity target is sustained near-100% communication coverage over
a relatively long evaluation window, with low failed/zero-service episode
fraction and stable service metrics.  This is an evaluation gate, not a license
to make communication fields the algorithm's intrinsic reward.
Concrete readout: at least half of evaluation primitive steps should have
`coverage == 1.0`, alongside low zero-service/failure fraction and acceptable
variance.

S7-S3 is temporarily deferred.  It remains the later benchmark where HMASD
performs poorly and the HA-CTSE hypothesis should become more valuable:

```text
per-agent high-level skill lifetimes should be decoupled because different UAVs
and roles naturally need different temporal commitments in difficult topology
and service conditions.
```

Planning consequence:

- P1/P2/P2-lite are not the final scientific claim. They are credit-assignment
  repairs needed to make the asynchronous lifetime design competitive.
- The implementation goal is: decouple each agent's high-level skill
  cycle/lifetime, then reconstruct HMASD's useful sparse-reward machinery under
  that asynchronous structure.  Specifically track and preserve four HMASD
  functions: recurrent low-level discoverer capacity, skill/role semantic
  pressure, entropy/exploration pressure, and dense cooperative credit
  assignment.
- HA-CTSE is a general MARL algorithm.  Backhaul/recovery metrics are diagnostic
  probes for cooperation and sparse-reward credit assignment in Scenario 7, not
  the target to optimize directly.  Do not accept a change merely because it
  raises backhaul metrics if reward, QoS, throughput, coverage, variance, or
  skill-lifetime behavior do not improve.
- P3/P4 intrinsic reward must avoid raw communication-specific indicators and
  must not simply reuse environment reward as an "intrinsic" signal.  Use
  benchmark communication metrics to evaluate whether cooperation emerged.  The
  environment reward remains the external task return, especially in high-level
  skill-lifetime cumulative targets; discoverer/discriminator-style intrinsic
  pressure should be a separate skill-semantics signal.
- Do not skip S7-S1 parity.  A mechanism that cannot approach HMASD on this
  simpler scene is unlikely to be useful for the harder S7-S3 setting.
- Mainline near-term runs should compare HMASD and HA-CTSE on S7-S1 with matched
  scenario settings, matched network scale, and comparable `~1e6`-step budgets.
- Required ablations for the claim: variable per-agent lifetime HA-CTSE,
  fixed/shared lifetime HA-CTSE, and HMASD.  Mechanism diagnostics should report
  duration/lifetime distribution, switch rate, agent-wise lifetime usage,
  backhaul connectivity, recovery, and service metrics.  Run this first on
  S7-S1; transfer the same matrix to S7-S3 later.

Current correction: do not let the plan collapse into duration-set tuning.  A
variable-lifetime policy class can represent fixed lifetime as a special case,
so the important question is not whether a hand-picked variable set beats one
hand-picked fixed duration in a short run.  The important question is whether
HA-CTSE can reconstruct HMASD's skill-discovery, skill-differentiation, and
actually-work intrinsic drive under asynchronous skill lifetimes.

## Round 22 Two-Clock Objective Unification (planned)

Source plan:

```text
docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
```

Status: planned / theory-first / no new reward module yet.

Round 22 accepts the GPT-5.5 Pro correction that R21/v6 is the current
algorithmic mainline:

```text
OPT recognition substrate -> sampled slow team intent Z ->
asynchronous individual response skills z_i.
```

R12 is now a recognition substrate/control line, not the primary cooperation
engine.  R19 is a mechanism-negative transition-residual control unless later
complete reward-on evidence contradicts the current negative `team_t_mi` read.

Staged tasks:

```text
R22-0: memory alignment.
  Update cross_validation, principles, implementation plan, and attention
  pointer so R21/v6 is the mainline and R12/R19 are controls.

R22-1: write `memory/R22_TWO_CLOCK_ELBO.md`.
  Derive the objective for slow sampled Z plus fast async z_i; audit
  team-discriminator, individual/coordinator residual, entropy, and possible
  cross-layer terms for double-counting.

R22-2: keep experiment track running.
  Launch/read EXP-20260705-r21-team-intent and
  EXP-20260705-hmasd-currentenv-baseline when compute is available.  These are
  not blocked by the derivation.

R22-3: add only missing diagnostics required by the bound.
  Audit/add `z_decisions_per_update`, `z_advantage_mean/std/var`,
  `combined_intrinsic_env_ratio`, `team_disc_reward_env_ratio`, and
  per-duration Z-boundary truncation fields if not already present.

R22-4: write `memory/R22_TARGET_ENTROPY_DESIGN.md`.
  Recast duration/Z/skill/action entropy as per-head target-entropy
  constraints.  Do not replace the current floors until R21/HMASD reads show
  which head collapses under useful learning.

R22-5: mechanism budget pruning.
  Every new mechanism must retire, absorb, or supersede an existing mechanism.
  Terms absent from the two-clock objective default to deletion candidates.
```

Execution status update (2026-07-05, Codex subagent-driven execution):

```text
R22-0 COMPLETE:
  memory/cross_validation.md, ATTENTION_POINTER.md, ALGORITHM_PRINCIPLES.md,
  and this plan now name R21/v6 as the active mainline and R12/R19 as
  substrate/control lines.

R22-1 COMPLETE:
  memory/R22_TWO_CLOCK_ELBO.md written and reviewed.  Spec review approved.
  Quality review found and fixed five implementation-risk issues:
    - Z vs z_i notation/metric ambiguity,
    - target-temperature sign convention,
    - clock-count normalization across team/individual/primitive clocks,
    - detached/null baseline semantics for p_hat and stored log pi_z,
    - tau/r notation mix.

R22-3 IMPLEMENTED / VALIDATION PENDING:
  Existing diagnostics:
    z_usage_entropy
    team_disc_reward_env_ratio
    z_boundary_trunc_rate
    z_boundary_trunc_rate_dur3/7/13/24
  Added diagnostics:
    z_decisions_per_update
    z_advantage_mean
    z_advantage_std
    z_advantage_var
    combined_intrinsic_env_ratio
    combined_intrinsic_env_ratio_over05_count
    combined_intrinsic_env_ratio_guard_active
    combined_intrinsic_env_ratio_kill_triggered
  Modified locations:
    ha_ctse_process/standalone_agent.py
    ha_ctse_process/team_intent.py
    ha_ctse_process/train.py
    ha_ctse_process/plotting.py
    tests/r21_team_intent_test.py
    train_multiproc_config_1.py
  Notes:
    z_advantage_* is computed on unnormalized high-level advantages and only for
    Z-boundary samples with nonzero team_logp_weight.  combined_intrinsic_env_ratio
    sums the active prototype-disc and team-disc reward/env ratios and uses the
    same reward_ratio_guard_mode semantics as the individual guards.  HMASD eval
    falls back to episode-level parity metrics if light metrics omit per-step
    reward_info, with parity_step_metric_fallback_used logged.

R22-4 COMPLETE:
  memory/R22_TARGET_ENTROPY_DESIGN.md written and reviewed.  It keeps
  auto-temperature design-only until R21/HMASD reads identify which head
  collapses under useful learning.
```

Mechanism budget table:

| Mechanism | Current status | R22 disposition |
| --- | --- | --- |
| R21 sampled team intent `Z` | mainline | keep and test |
| OPT `omega/c/kappa` | substrate | keep as recognition input/control |
| R12 situation hazard | deferred | no expansion until after R21/HMASD read |
| R19 transition residual | control | no new sweep unless complete reward-on contradicts negative probe |
| `g` / team bridge | deprecated | no new mechanism conditions on it |
| target `kappa*` | deferred | revisit only if ELBO or R21 failure points to target commitment |
| topology/communication rewards | diagnostic only | never use as intrinsic objective |

Validation before implementation completion:

```powershell
rg -n "Round 22|two-clock|Mechanism budget" memory\IMPLEMENTATION_PLAN.md
Test-Path docs\superpowers\plans\2026-07-05-r22-two-clock-elbo-mainline.md
```

## Decoupled-K Sanity Gate

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- The current K-matrix is a sanity/diagnostic gate, not the final objective.  It
- Can the variable-lifetime implementation approach strong fixed/shared controls,

## Round 12 Substrate Gate (Active Candidate Stage 0)

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Round 12 reframes the mainline as OPT-first Situation-Response Skill Discovery.
- Before any new reward or hazard mechanism is implemented, the OPT situation

## Round 12 Stage 1 Situation-Hazard Implementation Result

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- R12-1a implemented on 2026-07-02: default-off situation substrate diagnostics
- and reward-pure oracle-change renewal control are in the working tree.  Default

## Round 21 Team-Intent Restoration (2026-07-04, USER OVERRIDE — build now, highest priority)

User Architect decision: bring the HMASD autoregressive team skill back
while keeping asynchronous low-level lifetimes. Supersedes Round 20 D2
(ablation DROPPED) and D3 (kappa* deferral DISSOLVED). Spec (source of
truth): `docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md`.

```text
Two-clock hierarchy: sampled Z ~ pi_Z(Z|c,omega) held K_team=12 checks;
ATOMIC full-team AR reassignment at Z boundaries; async individual docking
(z_i | Z, c, o_i, roster) between them. HMASD = K_team=1 special case.
Team discriminator engine ships IN THE SAME BUILD: per-step low-level
lambda_D * (log q_D(Z|s') - log p_hat(Z)), bootstrap scale 0.1 — non-vacuous
because Z is SAMPLED. q_d gains Z conditioning. pi_g/bridge machinery is
refactored into pi_Z; old decorative g wiring deleted in-scope.
Build NOW default-off; LAUNCH on the stabilized entfloor base after its
480k read; a2_plus_t demoted to complementary. Pre-register
EXP-2026070X-r21-team-intent before launch (gates in spec: improvement
required vs stabilized base; z entropy not collapsed; disc acc in healthy
band; z_boundary_trunc_rate << 1).
```

Implementation receipt (2026-07-05, Codex Executor):

```text
Status: IMPLEMENTED default-off; not yet formally launched.

Code delivered:
  - ha_ctse_process/team_intent.py
      TeamIntentDiscriminator, prior-corrected residual reward, metric fields.
  - ha_ctse_process/config.py / train.py
      R21 CLI/config/manifest/checkpoint plumbing; `--enable_team_intent`,
      `--enable_team_disc_probe`, `--enable_team_disc_reward`, `--team_intent_k`,
      team-disc coef/clip/warmup/lr/hidden controls.
  - ha_ctse_process/standalone_agent.py
      two-clock Z lifetime state; atomic full-team AR reassignment at Z
      boundaries; async individual docking against held Z; boundary-only Z
      log-prob weight; no edit/switch penalty at Z boundary; rollout next-state
      capture; team discriminator update/reward path; R21 diagnostics.
  - ha_ctse_process/plotting.py
      CSV/plot fields for `z_*` and `team_disc_*`.
  - tests/r21_team_intent_test.py
      targeted tests for AR override, R21 guardrails, boundary semantics,
      async docking, discriminator reward shapes, and R21+prototype-disc
      conditioning.

Post-review fixes:
  - Added `team_codes` to the prototype-discriminator batch when R21 is active
    so `q_d(z_i | o'_i, kappa, Z)` does not crash in combination runs.
  - R21 now disables low-actor team-code conditioning even if legacy
    `--enable_low_actor_team_code` is supplied.
  - R21 rejects `team_bridge_type=none` at both CLI/config override and agent
    construction layers.
  - Team-intent prior counts are saved/restored in checkpoints as torch tensors
    to keep PyTorch `weights_only=True` loading safe.

Validation performed:
  - `python -m pytest tests\r21_team_intent_test.py -q` -> 6 passed.
  - import check for train/standalone_agent/team_intent/plotting -> import_ok.
  - structure smoke with `--enable_team_intent --enable_team_disc_probe`
    confirmed `ar_selection=True`, `parallel_selection=False`,
    `ar_prefix_mode=roster`, and R21 metrics written.
  - combination smoke with `--enable_team_intent --enable_prototype_disc_probe`
    confirmed the individual/prototype discriminator receives Z conditioning.
  - reward-on smoke with `--enable_team_disc_reward --reward_ratio_guard_mode warn`
    confirmed reward application metrics and warn-mode guard logging without
    stopping the run.
  - tiny checkpoint smoke confirmed `team_intent_prior_counts` is present and
    loadable with default `torch.load`.
  - CLI guard smoke confirmed `--enable_team_intent --team_bridge_type none`
    exits with a ValueError before launch.

Known caveats / launch guard:
  - R21 is default-off; no performance claim exists yet.
  - The formal experiment still requires `EXP-20260705-r21-team-intent` launch
    entry with stabilized-base controls, exact command, and gate thresholds.
  - Current training architecture resets policy state at rollout boundaries, so
    the Team Intent slow clock is guaranteed within rollout; long-run read
    should inspect `z_dwell`, `z_boundary_trunc_rate`, and `z_assignment_itv`.
```

Launch-preflight amendment (2026-07-05, Codex Executor after CC review + user
direct-cloud instruction):

```text
Status: IMPLEMENTED / launch-ready.

Accepted fixes:
  - `team_intent_k` default changed from 12 to 48.  K_team is the effective
    maximum individual lifetime at Z boundaries; 12 structurally truncated
    duration candidates 13 and 24 and would fabricate duration collapse.
  - `team_disc_coef` default changed from 0.1 to 0.05, matching the R16.5
    dose-response result where 0.05 was the cleaner stabilized base.
  - Added default-off Z entropy floor configuration/CLI/manifest/metrics:
    `z_entropy_floor_*`.  It is an insurance/stabilizer flag only, not evidence
    of self-sustained team-intent heterogeneity.
  - Added per-duration Z-boundary truncation diagnostics:
    `z_boundary_trunc_rate_dur3`, `dur7`, `dur13`, `dur24`.
  - Updated R21 runners to use the 64-env cloud direct plan and the coef005
    matched base (prototype-disc coef=0.05, duration floor disabled, guard kill).
  - Added HMASD current-env baseline support: `train_multiproc_config_1.py`
    now accepts `--n_agents`; HMASD eval logs HA-CTSE parity diagnostics
    (`coverage_eq1_*`, `zero_throughput_episode_fraction`,
    `throughput_gt5_step_fraction`) without changing HMASD learning logic.

Validation:
  - AST/compile syntax check passed for modified Python files.
  - HA-CTSE train help exposes `--enable_z_entropy_floor` and R21 controls.
  - HMASD train help exposes `--n_agents`.
  - Local R21 PowerShell dry-run prints K=48, team_disc_coef=0.05, guard kill,
    coef005 base, and duration floor disabled.
  - Linux cloud runner static checks confirm NUM_ENVS=64, K=48, coef=0.05,
    `--n_agents 6`, and parity eval metric labels.  Local bash dry-run was not
    possible because bash is not installed on the Windows host.

Next:
  - Launch `scripts/run_r21_team_intent_cloud_64env.sh` directly on cloud.
  - Launch `scripts/run_hmasd_currentenv_baseline_cloud_64env.sh` if a second
    cloud slot is available.
```

## Round 20 Team-Bridge Disposition (2026-07-04, SUPERSEDED by Round 21 user override)

Fully superseded by Round 21: g_tau was DEPRECATED-IN-PLACE, then R21 DROPPED the
queued `team_bridge_none` ablation and DISSOLVED the kappa* deferral (bridge
machinery refactors into pi_Z). No action remains here. Full original disposition
text is preserved verbatim in `memory/backup_20260706/IMPLEMENTATION_PLAN.md`.

## Round 19 Team-Transition Engine (2026-07-04, implemented, trigger-blocked)

Status: IMPLEMENTED and locally validated by Codex after the final
multi-model review pipeline (Gemini plan v1 -> CC six amendments -> Gemini v2
-> CC approval with fold-ins -> CC completion notes -> CC final consolidated
plan).
Implementation reference (single source of truth, wins over all prior docs):

```text
docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md
```

What it is: the DADS-style situation-transition residual
`log q(kappa'|kappa, xi) - log q(kappa'|kappa)` — the structural replacement
for HMASD's team discriminator engine killed by the vacuity lemma. xi = the
active-skill count vector. Self-transitions INCLUDED so stabilization pays
(holding the relay chain is a xi-dependent predictable self-transition).
Injection: HIGH-LEVEL ONLY, per-interval clipped residuals accumulated into
segment returns; coef 0.05, clip 2.0, warmup 20k, probe/reward flag split,
own optimizer, detached inputs, clean module `situation_transition.py`.

Build/launch discipline:

```text
BUILT NOW (parallel to A2): module + config + wiring + tests + a2_plus_t
  runner arm. Everything default-off.
LAUNCH ONLY via the pre-registered OUT-OF-GAS branch of the A2 outcome
  matrix (disc separation healthy but task flat) or explicit user decision
  after the A2 320k read. One variable: a2_plus_t vs A2.
TASK GATE IS IMPROVEMENT, NOT NON-REGRESSION: this arm exists to fix the
  exploration deficit; neutrality vs A2 is a FAIL.
CHURN PRECURSOR: team_transition_reward_renewal_corr logged now,
  informational in a2_plus_t (no live hazard), MANDATORY input to the
  Stage-2 hazard go decision (kappa is dual-use: exploration reward target
  AND termination signal — R19.3).
```

Implementation receipt 2026-07-04:

```text
New module:
  ha_ctse_process/situation_transition.py

Main wiring:
  StandaloneProcessAgent records closed per-env situation intervals, trains
  SituationTransitionPredictor with its own optimizer, and accumulates
  no-grad residual rewards into per-segment high-level rewards only.

Config/CLI/checkpoint/logging:
  enable_team_transition_probe/reward, coef/clip/warmup/lr/hidden;
  checkpoint saves and loads team_transition + team_transition_opt;
  UPDATE_FIELDS/TensorBoard/console/plots include team_transition_* metrics.

Runner:
  scripts/run_r15_stage1_local_cuda.ps1 now exposes a2_plus_t_probe and
  a2_plus_t arms.

Validation:
  pytest tests\r19_team_transition_test.py -q -> 6 passed
  pytest tests\r14_prototype_response_test.py -q -> 13 passed
  AST compile for touched files -> ast_compile_ok
  a2_plus_t runner dry-run -> passed
  tiny reward-on smoke -> completed and logged team_t fields
  checkpoint save/load/eval smoke -> passed
```

## Current Repo Structure

- `hmasd/networks.py`: HMASD neural modules. It contains `OPT`,
  `sparsemax`, `SkillCoordinator`, `SkillDecoder`, `SkillDiscoverer`,
  `R_Actor`, `R_Critic`, `TeamDiscriminator`, and
  `IndividualDiscriminator`.
- `hmasd/agent.py`: training-facing `HMASDAgent`, skill assignment,
  action selection, intrinsic reward computation, discriminator updates,
  coordinator PPO update, low-level PPO update, and checkpoint IO.
- `hmasd/utils.py`: `RolloutBuffer`, `DiscriminatorBuffer`, GAE, PPO helper.
- `hmasd/baselines.py`: command-line algorithm registry and non-learning
  heuristic baselines.
- `config_1.py`: main configuration.
- `config_test.py`: small smoke configuration.
- `train_multiproc_config_1.py`: active training entry point. It exposes
  `--algorithm`, imports `ALGORITHM_CHOICES`, applies
  `apply_algorithm_config`, and creates agents through `create_agent`.
- `tests/`: pytest tests for buffer, intrinsic reward, hidden state arrays,
  sharded env, and scenario 7 checks.
- `new-test-alg/`: documentation and experiment notes for this reconstruction.

## Existing HMASD Modules

- High-level coordinator: `SkillCoordinator` in `hmasd/networks.py`.
- Team skill `Z`: sampled by `SkillCoordinator.assign_and_value_batch`.
- Individual skill `z_i`: sampled autoregressively in
  `SkillCoordinator.assign_and_value_batch`.
- Skill interval `k`: enforced in `HMASDAgent._batched_assign_skills` via
  `env_steps_batch % self.config.k == 0`.
- Low-level actor: `R_Actor.forward(obs, rnn_states, masks, agent_skill, ...)`.
- Low-level critic: `R_Critic.forward(cent_obs, rnn_states, masks, team_skill)`.
- Team discriminator: `TeamDiscriminator.forward(state)`.
- Individual discriminator: `IndividualDiscriminator.forward(observation,
  team_skill)`.
- PPO update path:
  - high level: `HMASDAgent.update_coordinator`;
  - low level: `HMASDAgent.update_discoverer_from_rollout`;
  - discriminator: `HMASDAgent.update_discriminators`.
- Rollout buffer: `RolloutBuffer` in `hmasd/utils.py`.
- Logging: `TensorBoardManager` and `RewardTracker` in
  `train_multiproc_config_1.py`, plus `training_info` in `HMASDAgent`.

## Existing OPT Modules

- `OPT` exists in `hmasd/networks.py`.
- `StateEncoder` can optionally use OPT, but current active
  `SkillCoordinator` bypasses `StateEncoder` and uses its own Transformer
  encoder.
- Existing `use_opt` fields in `config_1.py` do not yet implement the
  requested compact-team bridge separation.

## Legacy Compatibility Boundary

- This branch is for constructing the new HA-CTSE/process algorithm, not for
  conservative HMASD maintenance.
- Keep old `hmasd`/`hmasd_original` runnable only as comparison baselines when
  doing so does not block the new algorithm.
- Do not keep fixed-k HMASD data-flow assumptions inside the HA-CTSE core just
  to preserve old behavior.
- Preserve archived `_server_package_*` folders by not editing them.

## Ruled Out / Stop Rules

- Segment posterior `q(z | S, g)`, context-residual posterior, and
  future-cooperation outcome residual probes repeatedly failed to beat
  shortcut/context baselines as reliable positive intrinsic rewards. Keep them
  diagnostic-only unless a new run pre-commits a falsification metric.
- Topology-role discrimination is the final classifier-style semantic probe in
  this family. If its full classifier does not sustainably beat the
  OPT/context/duration shortcut, stop adding new residual-discriminator heads.
- Duration-only shortcut is now a hard gate for segment-posterior intrinsic
  reward: if duration-only accuracy is not worse than posterior accuracy by the
  configured margin, segment posterior reward is zeroed before it can affect
  either high or low policy updates.
- Process reward with magnitude far below environment reward remains
  diagnostic-only unless explicitly changed to a centered/advantage-style
  shaping mode.

## Current Correction Pass (2026-06-28)

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- force each team code at the same segment start and measure pairwise KL/TV of
- `pi_z(. | o, c, g)`. Near-zero values mean `g` is decorative.

## Superseded Experimental Gate (2026-06-28 Round 3)

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- largely fixed, but stable relay-chain formation is still not solved:
- `credit_full_disconnect` stays high, recovery remains rare, and eval reward is

## Active Experimental Gate (2026-06-28 Round 5)

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Reframe: short duration improved access/coverage but did NOT move backhaul
- recovery. `credit_full_disconnect_mean` (~0.6) and `credit_recovery_rate`

## P2-lite Gate (2026-06-28) — Recovery-Window Contribution Credit

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- STATUS 2026-06-29: IMPLEMENTED (default OFF), validated by py_compile + smoke
- tests, and shipped in `dist/ha_ctse_p2lite_bundle_20260629_064151.zip`.

## P3 Candidate (conditional) — Conditional Skill-Effect Discovery

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Trigger: run this only if the current S7-S1 P1/P2-lite sweep fails to approach
- HMASD-level behavior or only improves topology diagnostics without task-metric

## Files To Modify

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- high-level assignment/update through it when enabled, maintain per-agent
- skill ages, and preserve original path otherwise.

## New Modules To Add

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._

## Config Fields

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._

## Buffer Fields

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Add process segment storage outside the PPO tensor buffer:

## Logging Fields

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- First implementation returns these in `update_info` where available:

## Test Checklist

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- 1. `test_original_hmasd_runs`
- 2. `test_opt_compact_shape`

## Smoke Commands

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Use the small smoke config first:
- python train_multiproc_config_1.py --config config_test --algorithm hmasd_original --num_envs 1 --rollout_length 16 --total_timesteps 16 --disable_eval --console_log_level error

## Current Documentation Status

As of 2026-06-23:

| Document | Stage | Current role |
| --- | --- | --- |
| `ATTENTION_POINTER.md` | Active pointer | First-read navigation layer. Points to the current principle section, plan stage, advice entries, experiments, and code focus. Update it after every task when focus or next action changes. |
| `ALGORITHM_PRINCIPLES.md` | Stable contract | Defines the scientific and implementation invariants. Use it to decide whether a code change is allowed. |
| `ALGORITHM_KNOWLEDGE_BASE.md` | Stable compact memory | Short reference for what HA-CTSE is and what claims are allowed. Use it before writing experiment text or summaries. |
| `IMPLEMENTATION_PLAN.md` | Active tracker | Tracks code status, partial implementations, next changes, commands, and continuation prompts. Keep this file current after each coding pass. |
| `ExpRecord.md` | Experiment ledger | Record every planned local/cloud experiment before launch: name, time, location, purpose, metrics to read, outcome meanings, and next decision. |
| `C:\Users\wu\.codex\skills\long-task-memo` | Codex workflow skill | General LongTaskMemo workflow for reading/updating attention pointer, principles, plan, ExpRecord, advice, and then aligning code or experiment work with the active stage. |

LongTaskMemo completion rule: after every task, update the affected memory files
and `ATTENTION_POINTER.md` before final response.  If no memory update is needed,
explicitly confirm that the pointer remains accurate.

Update on 2026-06-24: implementation moved beyond the first pass. The core
HA-CTSE path, stochastic bridge, autoregressive editor, compact-conditioned
discriminators, TensorBoard metric routing, and low-level compact ablation path
now have executable code paths and focused tests/smoke checks.

## Standalone Process-Core Separation

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Update on 2026-06-24 evening: the active implementation direction has changed.
- The new algorithm is no longer to be trained as a mixed `hmasd.agent` variant.

## Research Operating Principle

User correction on 2026-06-24: this work is algorithm exploration, not a
conservative patch series. Do not default to minimal HMASD-preserving edits when
the stated goal is to reconstruct and test a new algorithm.

Working rules for future coding passes:

1. Treat HA-CTSE design changes as first-class research hypotheses.
2. Preserve old HMASD only as a control/baseline path, not as the default design
   pressure for the new algorithm.
3. When a change modifies HMASD exploration semantics, keep it if it is a
   coherent experimental hypothesis, then expose metrics/ablations to evaluate
   it.
4. Avoid silently "conservative-izing" the core variant. If a conservative
   variant is useful, give it an explicit ablation name or document it as a
   control.
5. For entropy, discoverer exploration, and discriminator intrinsic rewards,
   reason from the new algorithm's mechanism first, then compare against HMASD.
6. Do not keep every old structure as an ablation by default. If the process
   framework makes an old component conceptually obsolete, retire it or keep it
   only as a legacy diagnostic. Ablations should answer live questions about
   the current algorithm, not preserve all historical mechanisms.

Continuation prompt for Codex:

```text
This is algorithm exploration, not conservative maintenance. Before changing
HA-CTSE, state the research hypothesis being tested, the metrics that can
falsify it, and whether the change belongs in the core algorithm or in a named
ablation/control. Do not automatically minimize diffs toward old HMASD behavior.
```

## Principles Alignment Audit

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Update on 2026-06-24: the first audit found that the code implemented the
- HA-CTSE mechanics but left several exploration objectives inactive or weak.

## Ablation Budget And Retirement Rules

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Research update on 2026-06-24: the process-centric redesign is a framework
- change. Not every structure from HMASD or the first HA-CTSE pass deserves a

## Process-Centric Exploration Plan

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._
- Research update on 2026-06-24: do not assume the original HMASD discriminator
- is the right exploration mechanism for HA-CTSE. Once `k` is only the high-level

## Current Implementation Status

Status legend: Complete means usable in the current code path. Partial means
the switch or module exists but the research version is not fully implemented.
Pending means planned but not implemented.

| Stage | Status | Notes |
| --- | --- | --- |
| Repo inspection and docs | Complete | The live repo was inspected and the new docs were placed under `new-test-alg/`. |
| Standalone algorithm boundary | Initial complete | `ha_ctse_process/` now contains env construction, a standalone process-core agent, and a standalone training entrypoint. It reuses `envs`/config only and does not import `hmasd.agent`. |
| Standalone synchronous collection | Complete first pass | `ha_ctse_process.train` supports `--num_envs` with independent per-env active skill, duration countdown, and process segment state. Segment rewards use explicit rollout indices, so multi-env interleaving does not corrupt process reward redistribution. |
| Standalone high-level PPO | Initial complete | Closed skill-lifetime segments now carry the high-level skill/duration decision observation, old log-prob, value, and entropy. Segment return plus process reward trains the standalone high-level skill/duration policy. |
| Standalone logging/checkpointing | Complete first pass | TensorBoard scalars are written under `Train/`, `Process/`, `High/`, and `Low/`. Periodic and final checkpoints save high, low, process modules and optimizers. |
| Standalone Scenario 7 outcome extraction | Complete first pass | `ha_ctse_process.process_outcomes` extracts masked deltas for coverage, connected users, throughput, QoS, backhaul, energy, charging, return pressure, plus observation/reward fallbacks. The process outcome head now predicts this 12-field normalized vector with masked MSE. |
| Preserve original HMASD | Complete | `hmasd` and `hmasd_original` disable HA-CTSE switches. A smoke run passed. |
| OPT compact extractor | Complete first pass | `OPTCompactExtractor` exists in `hmasd/ha_ctse.py` and produces compact context plus auxiliary losses/metrics. It is representation context, not a team skill. |
| Compact-team bridge | Research core updated | Deterministic and stochastic bridge modes exist. `horizon_ctb_sse_core` now uses stochastic bridge; `deterministic_bridge` is the explicit ablation. |
| Horizon skill editor | Complete first pass | Parallel editing, per-agent active skills, skill ages, `H_min` masking, `H_max` force, candidate skills, executed edit masks, and autoregressive sequential editing are implemented. |
| Discrete skill lifetimes | Complete first pass | `horizon_ctb_sse_core` now samples duration buckets from `skill_lifetime_candidates`, stores duration log-probs/entropy/targets, and suppresses edit sampling until expiry. |
| Rollout buffer fields | Process-aware first pass | HA-CTSE fields plus duration fields are stored and sampled by `RolloutBuffer`. High-level replay entries also store elapsed primitive steps, terminal closure, and close reason. |
| Process segment data contract | Complete first pass | `SkillProcessSegmentBuffer` collects per-agent skill-lifetime segments, reward-info sequences, outcome vectors/masks, and TensorBoard segment stats. Closed on-policy segments feed the process encoder/update path. |
| High-level PPO data flow | Process-aware first pass | Pending high-level samples now stay open across no-decision k-boundaries and close on duration expiry/done/rollout-local closure. High-level GAE uses `gamma ** elapsed_steps` for variable-duration samples. The old warning for missing pending samples at no-decision boundaries should not appear. |
| `strict_hmasd_alignment` | Legacy-only | This flag means fixed-k high-level sample closure for original HMASD. HA-CTSE process/discrete-lifetime presets force it off because it conflicts with duration-aware replay. |
| Legacy high-level contribution monitors | Retired for process mode | Fixed-k checks that expected one high-level sample every `k` steps and set `force_high_level_collection` are disabled for HA-CTSE process/discrete-lifetime mode. They are replaced by diagnostics for closed samples, duration remaining, and process segment stats. |
| On-policy update boundary | Complete first pass | After each update, HA-CTSE process mode clears rollout/discriminator/process buffers, drops pending high-level samples, invalidates active high-level skills, and resets RNN hidden state so the next rollout starts from the current policy instead of continuing decisions sampled by the previous policy version. |
| Process outcome extraction | Complete first pass | Closed process segments now get stable masked outcome vectors with Scenario 7 reward-info deltas and fallback obs-delta/return fields, plus running normalization. Outcomes are used by masked process prediction loss and process reward. |
| Process encoder training | Complete first pass | `SkillProcessEncoder`, `SkillOutcomePredictor`, `SkillProcessContrastiveHead`, executed-skill label extraction, and duration-only shortcut baseline are optimized inside `HMASDAgent.update` before discoverer PPO. |
| Process reward integration | Complete first pass | Segment-level process reward is computed from contrastive executed-skill evidence and outcome-prediction error, then redistributed into low-level rollout rewards before discoverer GAE. `reward_process` is logged separately. |
| High-level PPO update | Complete first pass | The HA-CTSE path recomputes log-probs for executed high-level decisions and updates the editor/bridge through PPO. |
| Low-level actor path | Complete for core and ablation | The core path keeps `R_Actor(obs, skill)` unchanged. `opt_mappo_k` and `horizon_ctb_sse_compact_low_level_ablation` use an explicit compact-context branch outside the core path. |
| Discriminator path | Removed from process core | `horizon_ctb_sse_core` disables discriminator training and discriminator rewards. The old team/individual discriminators remain only for HMASD-compatible baselines or explicit legacy controls, not as part of the process/outcome target. |
| Baselines and ablations | Complete first pass | Registered HA-CTSE variants now have executable code paths and short smoke checks. Long-run scientific validation is still required. |
| Metrics/logging | Complete first pass | HA-CTSE edit/horizon/compact/bridge/duration/process-segment/replay-span/process-training/process-reward metrics are routed explicitly to TensorBoard under `HA_CTSE/...`. |
| Tests | Current pass complete | `py_compile` passed for touched HMASD and standalone modules. Standalone env dry run passed on `config_1`/`S7-S3`; standalone 16-step training smoke passed with continuous Scenario 7 actions. Focused HMASD regression tests should still run after migration cleanup. |
| Scenario 7 standalone command | Ready for smoke | Use `python -m ha_ctse_process.train --scenario energy --preset S7-S3`. The standalone path supports synchronous multi-env training; multiprocessing/sharded collection is pending migration. |

## Implemented Code Map

- `ha_ctse_process/env_factory.py`: standalone env factory using only
  `envs.pettingzoo` and `ParallelToArrayAdapter`.
- `ha_ctse_process/standalone_agent.py`: minimal standalone process-core agent
  with continuous/discrete low-level PPO, skill-lifetime segments, high-level
  skill/duration PPO, process encoder, outcome prediction, contrastive
  skill/process loss, and process reward redistribution.
- `ha_ctse_process/process_outcomes.py`: standalone process outcome extractor
  for Scenario 7 reward-info deltas and fallback process statistics.
- `ha_ctse_process/recovery_potential.py`: P2-lite recovery-window contribution
  credit — soft per-agent `phi_i` from positions (non-saturating `exp(-d/scale)`
  closeness), `W_recovery` smooth state weight, SIGNED segment shaping and
  per-agent `F_i`, plus Pre-check-2 / CF-audit diagnostics. Default OFF; wired
  into `standalone_agent.py` alongside the P1 topology_potential path. Smoke
  test: `ha_ctse_process/test_recovery_potential.py`.
- `ha_ctse_process/train.py`: standalone training entrypoint, independent from
  `train_multiproc_config_1.py` and `hmasd.agent`; supports synchronous
  multi-env collection, TensorBoard, and checkpoint save.
- `hmasd/ha_ctse.py`: new OPT compact extractor, compact-team bridge, and horizon-aware skill editor with optional discrete duration head.
- `hmasd/ha_ctse.py`: also contains compact-conditioned team/individual discriminators and the autoregressive editor path.
- `hmasd/process_exploration.py`: masked process outcome extraction,
  running normalization for closed skill-lifetime segments, process encoder,
  outcome predictor, contrastive head, executed-label helper, and duration-only
  shortcut diagnostic.
- `hmasd/agent.py`: optional HA-CTSE assignment path, per-env skill ages and duration countdowns, process-aware high-level pending sample closure, process segment collection, process encoder/outcome/contrastive training, process reward redistribution into discoverer rollout rewards, HA-CTSE high-level PPO update, compact-conditioned discriminator integration, low-level compact ablation integration, rollout storage integration, checkpointing, and metrics.
- `hmasd/utils.py`: rollout fields for compact context, team code, active/candidate skills, edit masks, ages, duration fields, high-level replay span fields, variable-span high-level GAE, high-level log-probs, OPT aggregation entropy, low-level joint observations for compact-conditioned PPO replay, `reward_process`, low-level process reward insertion, and `SkillProcessSegmentBuffer` with masked outcome records.
- `hmasd/baselines.py`: algorithm names and config switches.
- `config_1.py` and `config_test.py`: HA-CTSE config fields.
- `tests/ha_ctse_test.py`: focused tests for shapes, masks, skill persistence, PPO gradients, discriminator labels, and config loading.

## Legacy Variant Status

These names exist in code from the first implementation pass. Under the
process-centric framework, some are full baselines, some are temporary controls,
and some may be retired instead of expanded into formal ablations.

| Algorithm name | Current state | Process-era role |
| --- | --- | --- |
| `horizon_ctb_sse_core` | Research core updated | Stochastic bridge, horizon editor, discrete lifetime buckets, process segments, process encoder/outcome/contrastive training, process reward, adaptive entropy targets, OPT auxiliary pressure, and TensorBoard metrics are wired. Discriminator training/rewards are disabled in the core. Short smoke passed. |
| `hmasd_original` | Complete baseline | Stable external baseline. Keep. |
| `opt_mappo_k` | Complete baseline/control | External/direct compact-conditioning control. Keep, but do not use success here as proof of process skill learning. |
| `deterministic_bridge` | Complete first pass | Temporary live ablation only while stochastic team-code sampling remains a current hypothesis. |
| `stochastic_bridge` | Complete first pass | Alias-style preset close to the current core; may be removed or repurposed once `horizon_ctb_sse_core` is unambiguously stochastic. |
| `ctb_sse_no_horizon` | Complete first pass | Candidate for retirement if discrete/process lifetimes replace learned keep/edit as the temporal mechanism. |
| `opt_full_sync_skill` | Complete first pass | Collapse/control reference only. Not a serious process-framework alternative. |
| `horizon_ctb_sse_no_discriminator` | Redundant alias/control | Its main behavior is now the core default. Keep only temporarily for command compatibility; future process-era controls should be `process_no_reward`, `process_no_contrast`, or `process_no_outcome`. |
| `horizon_ctb_sse_compact_low_level_ablation` | Complete first pass | Explicit bottleneck-violation ablation only. |
| `autoregressive_editor` | Complete first pass | Keep only if sequential per-agent assignment remains relevant after discrete/process lifetimes are implemented. |

## Next Change Plan

Completed on 2026-06-24:

1. TensorBoard/log routing for HA-CTSE metrics is explicit.
2. Core low-level actor contract remains unchanged; compact context is isolated behind `use_compact_in_low_level_actor`.
3. Compact-conditioned discriminator interfaces were added without modifying old HMASD discriminator classes.
4. `opt_mappo_k` has a separate compact-to-low-level actor/critic branch.
5. `autoregressive_editor` has sequential per-agent sampling and focused tests.
6. All registered HA-CTSE variants passed short config-test smoke runs.
7. Work principle updated: HA-CTSE is an exploratory algorithm reconstruction.
   Future changes should be framed as research hypotheses and ablations, not as
   automatic conservative reductions to old HMASD behavior.
8. Ablation budget corrected: old HMASD structures are not automatically
   expanded into new ablations. Current implementation work follows the
   process-core stages first.
9. Discrete skill lifetime buckets are implemented for the research core.
10. Process outcome extraction, process encoder/contrastive training, and
    process reward redistribution are implemented as the current research core.
    The next work is empirical validation, P5 termination-aware learning, and
    process-era ablation cleanup.

Operational note from the 20260623_231851 long run:

- `Training/Skill_Switches_Total` was an old tracker metric and had no active
  call site in the training loop, so it could stay at 0 even while HA-CTSE high
  level decisions were being made. The training loop now updates it from
  `step_data`; for HA-CTSE it counts real per-agent active-skill changes using
  `active_skill_prev`, `active_skill`, and `initial_assignment_mask`.
- The more diagnostic HA-CTSE metrics are `HA_CTSE/Editing/SwitchedAgents_Mean`,
  `HA_CTSE/Editing/ExecutedEdits_Mean`, `HA_CTSE/Editing/FullSync_Rate`, and
  `HA_CTSE/Horizon/PersistenceCycles_Mean`.
- Evaluation and evaluation images are triggered by `eval_interval`, not by
  reward improvement. For the observed S7-S3 run, `eval_interval=480000`, so a
  run at `304000` steps has not reached its first evaluation.

Open research reminder from 2026-06-24:

- HMASD's exploration pressure comes from multiple places: high-level entropy
  in the target/loss, low-level discoverer action entropy, and discriminator
  intrinsic reward terms. HA-CTSE changes the high-level latent, edit horizon,
  compact-team bridge, and optionally discriminator conditioning, so these
  exploration terms must be reconsidered as part of the new algorithm rather
  than simply copied or removed.
- Compact-conditioned discriminators are currently part of the exploratory
  HA-CTSE implementation. They may help align skill identity with interaction
  structure, or they may weaken the old HMASD skill-discovery pressure by
  letting compact context explain labels. This should be tested, not resolved
  by conservative default.
- Training trajectory images are generated only with `--debug`; normal visual
  outputs are produced during evaluation.

Next:

1. Restart long training for `horizon_ctb_sse_core`; existing runs launched
   before the process training pass are still the old weakened implementation.
2. Inspect `HA_CTSE/ProcessTraining/*`,
   `HA_CTSE/Discoverer/ProcessReward_*`, `HA_CTSE/ProcessOutcome/*`,
   `HA_CTSE/Duration/*`, and the existing edit/horizon/bridge entropy metrics.
3. Verify that `process_segments_trained` is nonzero after updates,
   `process_reward_applied_steps` is nonzero when the gate is enabled, and the
   reward scale is not overwhelming env reward.
4. If process reward is unstable, adjust `process_reward_coef`,
   `process_outcome_coef`, `process_contrastive_coef`, or reward clipping
   before adding more architecture.
5. Do not use legacy discriminator MI in the core. If a later comparison is
   needed, introduce an explicitly named legacy-MI control rather than
   re-enabling it inside `horizon_ctb_sse_core`.
6. Compare `deterministic_bridge` against the stochastic research core only if
   team-code sampling remains a live question after process diagnostics.
7. Treat compact-low-level and OPT-MAPPO-K as baselines/controls, not core
   algorithm evidence.
8. Add segment-level discriminator only if process/outcome objectives are
   insufficient and the hypothesis is explicitly rewritten for the process
   framework.
9. Re-run focused tests after every code pass:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\rollout_buffer_test.py tests\ha_ctse_test.py tests\training_metrics_profiler_test.py -q
```

10. Run a short smoke command before any long experiment:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" train_multiproc_config_1.py `
  --config config_test `
  --algorithm horizon_ctb_sse_core `
  --collector_backend subproc `
  --num_envs 4 `
  --rollout_length 16 `
  --total_timesteps 64 `
  --disable_eval `
  --console_log_level error `
  --log_dir logs\smoke_ha_ctse_core
```

For the long-run collector path, also run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" train_multiproc_config_1.py `
  --config config_test `
  --algorithm horizon_ctb_sse_core `
  --collector_backend sharded `
  --num_workers 2 `
  --envs_per_worker 2 `
  --rollout_length 16 `
  --total_timesteps 64 `
  --disable_eval `
  --console_log_level error `
  --log_dir logs\smoke_ha_ctse_core_sharded
```

## Recommended Standalone Core Training Command

For a Scenario 7 run with an episode length around 1500, use an energy preset
other than `S7-S1`. The standalone path supports synchronous multi-env
collection; multiprocessing/sharded collection is still pending:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config config_1 `
  --scenario energy `
  --preset S7-S3 `
  --num_envs 8 `
  --rollout_length 500 `
  --skill_interval 10 `
  --total_timesteps 320000 `
  --save_interval 20 `
  --device cuda `
  --log_dir logs\ha_ctse_process_standalone_320k
```

## 2026-06-25 Standalone Eval Result

The most useful checkpoint from the first `S7-S1` 6-agent standalone run is
currently `update_60`, not the final `update_80` checkpoint.

Eval command target:

```text
logs\ha_ctse_process_s7s1_6agent_subproc_320k\standalone_process_core_update_60.pt
```

20-episode eval result:

```text
reward_mean      = 85.424256
reward_std       = 59.354647
length_mean      = 500.0
coverage         = 0.281667
qos              = 0.191187
throughput       = 19.133963
battery_min      = 1.000000
```

Distribution notes from `metrics/eval_episodes.csv`:

- 13 / 20 episodes had nonzero coverage, QoS, and throughput.
- 7 / 20 episodes still collapsed to zero service.
- Reward ranged from about `-3.75` to `219.51`, so the policy is promising but
  still high-variance.
- The 240k/update_60 checkpoint is empirically more credible than the final
  checkpoint from the same run because the final 320k two-episode eval showed
  zero coverage/QoS/throughput despite a positive reward mean.

Decision:

- Do not blindly continue the same long training recipe.
- Treat the current discrete-lifetime process core as a working but unstable
  baseline.
- Next code work should focus on diagnostics and stabilization:
  1. batch-evaluate multiple checkpoints and select by Scenario 7 service
     metrics, not reward alone;
  2. reduce checkpoint IO so training is not slowed by saving every update;
  3. split high/low policy loss, value loss, entropy, and return scales in
     logs;
  4. add duration/skill/g histograms and collapse diagnostics;
  5. add process posterior and coordination diagnostics before moving to a
     hazard-SMDP variant.

Alternative research track:

- `new-test-alg/IC_SPL_HAZARD_SMDP_ALTERNATIVE.md` records the more aggressive
  IC-SPL hazard-SMDP proposal. It is a future named variant, not the current
  implemented core.

Implementation update after this eval:

1. Checkpoint sweep eval is implemented as:

   ```powershell
   & "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.eval_checkpoints `
     --checkpoint_dir logs\ha_ctse_process_s7s1_6agent_subproc_320k `
     --log_dir logs\ha_ctse_process_s7s1_6agent_checkpoint_sweep `
     --config ha_ctse_process.config `
     --scenario energy `
     --preset S7-S1 `
     --n_agents 6 `
     --seed 1 `
     --device cuda `
     --updates 20,40,60,80,final `
     --eval_episodes 20 `
     --eval_max_steps 1500 `
     --overwrite
   ```

   It writes `metrics/checkpoint_eval_summary.csv`, sorted by a service score
   using coverage, QoS, throughput, and battery safety.

2. Standalone training logs now split total losses into:

   ```text
   process_outcome_loss
   process_contrastive_loss
   high_policy_loss
   high_value_loss
   high_entropy_loss
   high_aux_loss
   low_policy_loss
   low_value_loss
   low_entropy_loss
   ```

   This is intended to diagnose whether the large high-level loss is mostly
   value-scale, policy-ratio, entropy, or OPT auxiliary pressure.

3. Collapse diagnostics are now exported to CSV/TensorBoard:

   ```text
   skill_usage_entropy
   skill_usage_max_frac
   duration_usage_entropy
   duration_usage_max_frac
   skill_duration_mi
   team_code_usage_entropy
   team_code_usage_max_frac
   team_code_skill_mi
   ```

   These directly test skill collapse, duration shortcuts, and whether `g`
   affects skill distribution.

4. Checkpoint IO is reduced:

   - standalone `--save_interval` default is now `10`, not every update;
   - `--checkpoint_keep_last` defaults to `3` periodic checkpoints;
   - `standalone_process_core_final.pt` is still always saved.

5. Lightweight smoke checks passed:

   ```text
   python -m py_compile ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py ha_ctse_process\eval_checkpoints.py
   python -m ha_ctse_process.train ... --total_timesteps 8 --rollout_length 8
   python -m ha_ctse_process.eval_checkpoints ... --updates 60,final --eval_episodes 1 --eval_max_steps 1
   ```

Follow-up diagnosis on the original 320k `S7-S1` 6-agent run:

```text
updates 1-20:  return=3.60,  duration_acc=0.282, switch=0.665, seg_len=87.0,  high_entropy=4.43, high_loss=84.3
updates 21-40: return=5.20,  duration_acc=0.288, switch=0.657, seg_len=89.2,  high_entropy=4.41, high_loss=120.1
updates 41-60: return=7.31,  duration_acc=0.336, switch=0.619, seg_len=104.2, high_entropy=4.28, high_loss=244.0
updates 61-80: return=10.85, duration_acc=0.487, switch=0.474, seg_len=158.3, high_entropy=3.36, high_loss=620.6
```

Interpretation:

- Reward/return keeps improving, but Scenario 7 service metrics peak around
  update 40 / 160k.
- After update 40, segment length grows and switch rate falls sharply. This is
  not automatically bad, but in this run it coincides with worse coverage/QoS.
- `duration_only_accuracy` rises from about `0.28` to `0.49`, suggesting the
  policy/process encoder may be leaning on duration as a skill identity
  shortcut.
- `team_code_entropy` stays close to `log(5)`, so `g` is still sampled with
  high entropy. This does not prove `g` is useful; new `team_code_skill_mi` and
  intervention diagnostics are needed in the next run.
- `high_loss` grows strongly. Because the old run did not split high policy and
  value losses, the next run must use the new loss decomposition before adding
  architecture changes.

Experiment implication:

- `S7-S1` is still a complex environment; 1M+ steps is a more realistic training
  horizon than 320k.
- Do not interpret 320k instability as failure. Interpret it as evidence that
  longer training must log value-scale, duration shortcut, and `g` usage
  diagnostics.
- Before switching to hazard-SMDP, run a longer discrete-lifetime baseline with
  the new diagnostics and checkpoint sweep. If service metrics still peak early
  and then regress, first try value normalization/loss scaling and duration
  regularization.

## 2026-06-25 Process Posterior MI Upgrade

User hypothesis: a sequence classifier can provide the exploration pressure
that old team/skill discriminator rewards used to provide, but it must operate
on completed process segments rather than single states. This is compatible
with the process-core framework if it is treated as a variational process MI
estimator:

```text
q_phi(z | S, g)      = segment-to-skill posterior
p_phi(z | g)         = coordination-conditioned skill prior
R_process_mi         = log q_phi(z | S, g) - log p_phi(z | g)
```

Implemented standalone module:

- `ha_ctse_process/process_posterior.py`
  - `SegmentSkillPosterior`
  - separate class, not a legacy HMASD discriminator
  - consumes segment encoder embedding and team code `g`
  - outputs posterior logits `q(z | S,g)` and prior logits `p(z | g)`

Config switches:

```text
use_process_posterior_mi = True
process_posterior_condition_on_team = True
process_posterior_team_embed_dim = 0
process_prior_coef = 0.25
```

CLI switch:

```powershell
--disable_process_posterior_mi
```

Training changes:

- The old process reward term `log q(z|S) + log n_z` is replaced by
  `log q(z|S,g) - log p(z|g)` when `use_process_posterior_mi=True`.
- The segment encoder still predicts Scenario 7 process outcomes.
- The old `ProcessEncoder.skill_head` remains available as the legacy fallback
  path when the MI posterior is disabled.
- Checkpoints now save `process_posterior`; loading old checkpoints remains
  compatible because missing posterior weights are initialized from the current
  config.

New metrics:

```text
process_prior_loss
process_posterior_acc
process_mi_estimate_mean
process_log_q_mean
process_log_p_mean
```

Smoke checks passed:

```text
python -m py_compile ha_ctse_process\process_posterior.py ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py ha_ctse_process\eval_checkpoints.py
python -m ha_ctse_process.train ... --total_timesteps 8 --rollout_length 8
python -m ha_ctse_process.train --mode eval ... new checkpoint
python -m ha_ctse_process.train --mode eval ... old checkpoint
```

Next 1M baseline should keep this enabled by default, while a control run can
disable it with `--disable_process_posterior_mi`.

## Continuation Prompt

Use this prompt when resuming implementation work:

```text
Continue HA-CTSE implementation in C:\project\HMASD. First read
new-test-alg/ALGORITHM_PRINCIPLES.md, new-test-alg/IMPLEMENTATION_PLAN.md, and
new-test-alg/ALGORITHM_KNOWLEDGE_BASE.md. Check git status and do not revert
user changes. The process-core algorithm must live in `ha_ctse_process/`, not
inside `hmasd.agent`. Reuse environment/config infrastructure only when needed.
Do not reintroduce discriminator training/rewards into the process core. Respect
PPO/on-policy boundaries: no rollout, process-segment, active-skill, or hidden
state data should silently cross an update boundary as training data for a new
policy version. Next migration targets are proper evaluation,
resume-from-checkpoint, multiprocessing/sharded collection, and replacing
remaining minimal trainer shortcuts inside `ha_ctse_process/`.
```

## Pre-Change Self Check

Before editing code, answer these questions in the work notes:

1. Which stage or variant is this change advancing?
2. Does it risk changing `hmasd` or `hmasd_original` behavior?
3. Does it let `c_tau` or `g_tau` bypass the skill bottleneck outside an explicit ablation?
4. Are discriminator labels active executed skills, not candidate no-edit skills?
5. Are edit masks applied before sampling so old and new log-probs match executed actions?
6. Does any training sample or hidden state cross an update boundary in a way
   that would make PPO/discriminator/process updates off-policy?
7. Is the change covered by a focused test or smoke run?

## Open Risks And TODOs

- Long-run stability is not proven by short smoke tests.
- Process training is implemented, but its reward scale and stability are not
  proven. Watch for process reward overwhelming environment reward or producing
  high-variance discoverer advantages.
- The first posterior run showed that `q(z|S,g)` starts learning useful segment
  signal, but the old `MI - outcome_error` process reward often becomes
  negative because the outcome prediction error dominates. The next branch
  should treat outcome prediction as an auxiliary representation loss by
  default, not as a direct process reward penalty.
- `paper_data` export for process reward components is still pending; TensorBoard
  logging exists first.
- Segment-level discriminator is no longer the default next step. Reintroduce it
  only as a process-era hypothesis, not as an inherited HMASD obligation.
- Update-boundary closure is intentionally strict: pending process samples are
  discarded unless explicitly closed with valid bootstrap support. If sample
  efficiency becomes a problem, implement rollout-boundary partial closure
  rather than off-policy replay.
- Compact-low-level and OPT-MAPPO-K are ablations only; do not use them to
  redefine the HA-CTSE core.
- Stochastic bridge is now the research core and may add variance; compare it
  against `deterministic_bridge` explicitly instead of treating deterministic
  behavior as the default.
- The method still needs empirical evidence that it avoids full-sync collapse:
  monitor `full_sync_rate`, `avg_executed_edits`, `skill_persistence_cycles_mean`,
  and `lifetime_heterogeneity`.

## 3D Topology Evaluation View

Status: implemented as an optional standalone eval artifact.

Rationale: scalar curves cannot show whether the learned process is producing
meaningful UAV movement, service links, relay routes, charging behavior, and
skill lifetime choices. The most direct inspection tool for Scenario 7 is a
dynamic 3D topology trace.

Implementation:

- New module: `ha_ctse_process/topology_viz.py`.
- Eval switch: `--save_topology`.
- Sampling controls:
  - `--topology_interval`: environment steps between captured frames.
  - `--topology_episodes`: number of eval episodes to capture, default 1.
  - `--topology_max_frames`: cap per captured episode.
- Outputs under `log_dir/topology/`:
  - frame JSON with UAV/user/base-station/charging-station positions,
    connections, routing paths, active skills, remaining durations, batteries,
    reward, and eval metrics.
  - final static 3D PNG.
  - animated GIF when Pillow-backed matplotlib animation is available.

Validation smoke:

```text
python -m py_compile ha_ctse_process\topology_viz.py ha_ctse_process\train.py
python -m ha_ctse_process.train --mode eval ... --eval_max_steps 2 --save_topology
```

The smoke produced non-empty JSON, PNG, and GIF artifacts. Use this for
observation-only eval; do not enable it in high-frequency checkpoint sweeps
unless explicitly needed because GIF generation is extra CPU/IO work.

## Communication Metrics And Run Manifest

Status: implemented for standalone eval/log outputs.

Rationale: reward, coverage, QoS, and battery are not enough to explain Scenario
7 behavior. The communication topology itself is part of the task: a policy can
increase reward while losing backhaul robustness, overusing direct BS links,
breaking relay paths, or producing unstable service drops. Model parameters and
physical environment parameters are equally important for interpreting a run.

Added eval CSV fields:

- Service/user counts: `connected_users`, `access_connected_users`,
  `total_connected_users`, `served_users`.
- Topology: `connectivity_ratio`, `connected_uavs`, `uavs_with_backhaul`,
  `avg_hops`.
- Relay/backhaul robustness: `relay_route_loss_ratio`,
  `relay_route_loss_prev_served_ratio`, `relay_route_lost_uavs`,
  `relay_route_lost_users`, `backhaul_outage_ratio`, `service_drop_ratio`,
  `backhaul_drop_ratio`, `full_network_disconnect`, `coverage_drop_ratio`.
- Capacity and guard behavior: `min_serving_backhaul_bottleneck_mbps`,
  `avg_serving_backhaul_bottleneck_mbps`, `backhaul_margin_penalty_raw`,
  `backhaul_guard_checked_actions`, `backhaul_guard_blocked_actions`,
  `routing_overhead`.

Added plots:

- `eval_communication_topology.png`
- `eval_backhaul_robustness.png`
- `eval_backhaul_capacity_guard.png`

Added metadata:

- `metadata/run_manifest.json`
- Records command-line args, standalone algorithm parameters, training
  parameters, model dimensions, physical/communication/energy environment
  parameters, runtime env dimensions, and runtime agent dimensions.

Topology JSON now also includes `uav_connections`, `uav_bs_connections`, and
`routing_paths`, so the 3D topology view can distinguish physical/reachable
links from actually selected routing paths.

## Checkpoint/Eval Boundary Protection

Status: implemented after the 560k diagnostic interruption.

Observation: the 1M S7-S1 diagnostic run reached `update=140` /
`total_steps=560000`, then started eval. The log directory contains only
18/20 eval episode rows for 560k, no `standalone_eval total_steps=560000`
summary line, and no `standalone_process_core_update_140.pt`. The previous
training loop saved periodic checkpoints after eval, so an interruption during
eval could lose the latest trained weights.

Fix: periodic checkpoints are now saved and pruned before running scheduled
eval. Future eval-boundary interruptions should retain the just-finished update
checkpoint.

Operational note: for the interrupted run, the latest complete checkpoint is
`standalone_process_core_update_130.pt` at 520k steps. Resume or re-evaluate
from that checkpoint unless the original process is still alive and later writes
the update-140 checkpoint.

## Process Posterior Reward Branch

Status: implemented as the next experimental branch after tagging the prior
standalone version as stable.

Observation from the clean S7-S1 6-agent posterior run:

- Early posterior signal is weak before roughly 80k-160k steps.
- After roughly 280k steps, `posterior_acc` and `process_mi` sometimes rise
  meaningfully, so the segment posterior is learning process-level skill
  information.
- The mixed reward `process_reward = MI - outcome_error` often remains negative,
  and service metrics degraded after 160k in the first posterior run. This points
  to reward mixing, not necessarily to the posterior estimator itself, as the
  immediate failure mode.

Implemented change:

- Added `process_reward_mode` to `ha_ctse_process.config.Config` and CLI.
- Default mode is now `mi_only`.
- Supported modes:
  - `mi_outcome`: old mixed reward, `MI - outcome_error`.
  - `mi_only`: direct variational process MI reward.
  - `positive_mi`: only rewards positive process MI.
  - `centered_mi`: batch-centered process MI for advantage-like shaping.
  - `none`: trains process heads without injecting process reward.
- Outcome prediction remains trainable through `process_outcome_coef`, but is no
  longer part of the default reward.
- Added reward diagnostics:
  - `process_reward_mi_component_mean`
  - `process_reward_outcome_penalty_mean`
  - `process_reward_unclipped_mean`
  - `process_mi_positive_frac`

Next experiment priority:

1. Run `mi_only` as the main posterior branch.
2. If MI reward is still too sparse or negative early, run `positive_mi`.
3. Keep `process_outcome_coef` nonzero as auxiliary representation learning
   unless it becomes a speed bottleneck.
4. Compare at 160k, 320k, 480k, and 1M+ steps using reward, coverage, QoS,
   throughput, posterior accuracy, MI positive fraction, and topology traces.

## Correction + Ablation + Diagnostics Pass

Status: implemented as the next branch after the first `mi_only` reward split.

Intent: distinguish algorithm-correctness fixes from real ablation knobs and
from passive diagnostics.

Correctness fixes now enabled by default:

- High-level returns are now SMDP-style segment returns:
  - environment segment reward is discounted inside the variable-length segment.
  - non-terminal segments can bootstrap with `gamma^T V(s_{t+T})`.
  - diagnostics report `high_env_return_mean`,
    `high_bootstrap_value_mean`, and `high_smdp_discount_mean`.
- Process posterior reward is explicitly computed from pre-update posterior
  logits for the current rollout, then the posterior is trained. This keeps the
  reward assignment order clear for on-policy reasoning.
- Checkpoint selection now includes communication robustness in the score, not
  reward/coverage/QoS/throughput alone.

Ablation switches now available:

- `process_reward_mode`:
  - `mi_outcome`
  - `mi_only`
  - `positive_mi`
  - `centered_mi`
  - `none`
- `process_reward_injection`:
  - `high_only` (default)
  - `high_and_low`
  - `low_only`
  - `none`
- SMDP correction toggles:
  - `--disable_smdp_discounted_high_return`
  - `--disable_smdp_bootstrap`

Diagnostics added:

- `process_reward_high_mean`
- `process_reward_low_mean`
- `length_only_accuracy`
- `reward_sum_only_accuracy`

Interpretation:

- If `posterior_acc` rises together with `duration_only_accuracy`,
  `length_only_accuracy`, or `reward_sum_only_accuracy`, the posterior may be
  using shortcuts rather than process semantics.
- If `process_reward_high_mean` improves but service metrics degrade, the
  process reward is shaping high-level choices in the wrong direction.
- If `high_bootstrap_value_mean` dominates `high_env_return_mean`, high critic
  scale or bootstrap use should be audited before trusting long-run results.

First ablation batch:

```text
A0: process_reward_mode=none,        process_reward_injection=none
A1: process_reward_mode=mi_only,     process_reward_injection=high_only
A2: process_reward_mode=mi_only,     process_reward_injection=high_and_low
A3: process_reward_mode=positive_mi, process_reward_injection=high_only
```

Keep duration candidates fixed for this batch:

```text
1,2,4,8,16,32
```

Do not mix duration-set ablations into this first batch.

## Reward-Purity Correction After A1/A1b

Status: active correction pass.

Reason:

- A1 (`mi_only + high_only + bootstrap`) showed low-position eval oscillation
  and declining service metrics by 240k.
- A1b (`mi_only + high_only + no bootstrap`) improved some reward/coverage
  means at 80k, but episode outcomes became strongly all-or-nothing:
  successful episodes had high service, while many episodes had full network
  disconnect and zero coverage.
- This exposed a conceptual issue: high-level and low-level rewards share the
  same environment source, but the high-level target is a segment-level SMDP
  aggregation while the low-level target is per-step reward. Injecting process
  reward into high only creates a second high-level objective that the low-level
  policy does not directly receive.

Correction:

- The default standalone config now keeps the RL task reward pure:
  `process_reward_injection = "none"`.
- The process posterior is still trained and logged by default. Its MI estimate
  is treated first as a diagnostic/auxiliary signal, not as a reward target.
- Explicit reward-injection ablations remain available through
  `--process_reward_injection high_only|high_and_low|low_only|none`.
- Added `smdp_bootstrap_coef` so bootstrap can be damped instead of only on/off.
- Added `high_max_grad_norm` to prevent high-level critic/policy updates from
  being dominated by large value targets.
- Added direct shortcut-gap diagnostics:
  - `posterior_acc_minus_duration_only`
  - `posterior_acc_minus_length_only`
  - `posterior_acc_minus_reward_sum_only`

New near-term experiment order:

```text
P0: reward-pure baseline
    process_reward_mode=mi_only
    process_reward_injection=none
    smdp_bootstrap_coef=0

P1: damped bootstrap baseline
    process_reward_mode=mi_only
    process_reward_injection=none
    smdp_bootstrap_coef=0.1

P2: reward-pure + stronger posterior training diagnostics
    process_reward_mode=centered_mi or mi_only
    process_reward_injection=none
    process_reward_coef can be nonzero, but should not affect RL reward

Only after P0/P1 prove stable:

R1: low-level process shaping
    process_reward_injection=high_and_low
    process_reward_coef=0.5 or 1.0
```

Interpretation rule:

- If `posterior_acc_minus_duration_only <= 0`, do not trust process MI as a
  semantic reward. It is likely reading duration/length shortcuts.
- If reward-pure P0 is still all-or-nothing, the issue is not process reward
  injection; inspect environment reward/communication credit assignment and
  high-level action semantics.
- If P0 is stable but reward-injection runs collapse, the process reward is
  corrupting task credit and must remain auxiliary until debiased.

## Cooperative Relay Failure Interpretation

Status: user-confirmed task interpretation.

The high full-disconnect rate in S7-S1 should not be treated as a logging bug or
as merely an unlucky evaluation artifact.  This cooperative UAV setting has a
real relay-formation requirement: if the policy fails to learn cooperative relay
behavior, the network naturally breaks and service collapses.  Therefore the
P0 all-or-nothing pattern means the current algorithm is not yet reliably
forming and maintaining stable relay chains.

Updated implication:

- Full disconnect is a core task failure mode, not a nuisance metric.
- The next algorithmic work should address cooperative credit assignment: the
  policy must learn which local behaviors enable team connectivity even when an
  individual UAV's immediate reward/output is hard to isolate.
- Reward-pure P0 is still useful because it proves this failure happens without
  process reward contamination.
- The next diagnostics should inspect whether failed episodes correspond to
  agents never forming a backhaul chain, forming it too late, or breaking it
  after initial service.
- Relay/backhaul measurements are diagnostic proxies for cooperation credit,
  not first-class optimization targets.  Do not hard-code "relay-chain output"
  as the algorithm objective.

Candidate directions:

1. Add relay/topology state diagnostics to high-level segment records as
   cooperation-credit probes.
2. Diagnose whether skill/duration choices correlate with later team
   connectivity changes, without using relay-chain output as a direct target.
3. Add counterfactual or baseline-style contribution diagnostics where possible:
   which agent was plausibly bridge-critical, bottleneck-critical, or irrelevant
   during a segment.
4. Keep process posterior reward auxiliary until it proves it captures relay
   semantics beyond duration/length shortcuts and improves downstream task
   behavior.

## HMASD Cooperation Bias Audit

Status: code-audited migration plan.

Purpose: explain why HMASD can learn cooperative relay behavior while the
current standalone HA-CTSE process path still shows persistent all-or-nothing
relay failure.

Audited files:

- `hmasd/agent.py`
- `hmasd/networks.py`
- `hmasd/utils.py`
- `hmasd/process_exploration.py`
- `envs/pettingzoo/scenario_base.py`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/process_outcomes.py`

### 1. Environment already has relay robustness reward

The environment does provide direct relay/backhaul shaping in `load_balance`
mode:

- `backhaul_outage_ratio`
- `backhaul_drop_ratio`
- `coverage_drop_ratio`
- `backhaul_outage_ema`
- `full_network_disconnect`
- `relay_route_loss_ratio`
- `backhaul_margin_penalty_raw`
- lighthouse/navigation reward when the whole team has no base-station
  connection

The shared reward subtracts a robustness penalty:

```text
w_backhaul_outage * outage
+w_full_disconnect * full disconnect
+w_coverage_drop * coverage drop
+w_outage_memory * outage EMA
+w_relay_break * relay route loss
+w_backhaul_margin * backhaul margin deficit
```

Therefore P0 failure is not because relay failure is absent from the environment
reward.  The reward signal exists, but the current standalone algorithm does not
reliably convert it into stable cooperative relay behavior.

### 2. HMASD low-level discoverer is much stronger than current low-level

HMASD `SkillDiscoverer` uses recurrent MAPPO-style actor/critic modules:

- recurrent actor conditioned on local observation and individual skill;
- recurrent centralized critic conditioned on global state and team skill;
- sequence/chunk sampler with `chunk_length = k`;
- GAE over rollout buffer;
- ValueNorm for discoverer returns;
- actor/critic optimizers separated;
- grad clipping for both actor and critic;
- optional compact context injection.

Current `ha_ctse_process.LowLevelPolicy` is feedforward:

```text
pi_l(a_i | o_i, one_hot(z_i))
V_l(o_i, z_i)
```

It has no recurrent state, no centralized low-level critic, no ValueNorm, and no
sequence update.  In a relay task where each UAV must infer and maintain a
temporal role in a partially observed chain, this is a major capacity and credit
assignment gap.

Migration implication:

- Before adding more process reward, upgrade the standalone low-level path to a
  recurrent MAPPO-style discoverer or an equivalent recurrent low-level actor
  with centralized value.
- Keep it inside `ha_ctse_process`, not by importing HMASD directly.

### 3. HMASD discriminator is not just a classifier; it feeds low-level reward

HMASD computes per-step intrinsic rewards from discriminator log-probabilities:

```text
intrinsic =
    lambda_e * env_reward
  + legacy_mi_coef * lambda_D * team_discriminator_MI
  + legacy_mi_coef * lambda_d * individual_discriminator_MI
  + optional uncertainty
```

The individual discriminator is conditioned on team skill and predicts
individual skill from next observation.  This makes the low-level discoverer
receive a direct skill-semantic shaping signal, not merely a diagnostic.

Current standalone P0 intentionally has:

```text
process_reward_high = 0
process_reward_low  = 0
```

and the process posterior often fails shortcut-gap checks.  Thus it does not
replace HMASD's semantic pressure.

Migration implication:

- Do not reintroduce the old generic discriminator unchanged.
- If adding auxiliary learning, treat relay-related labels as representation and
  credit-assignment probes, not as the main reward target:
  - did team connectivity improve after this segment?
  - did the agent occupy a bridge-critical or bottleneck-critical role?
  - did a local action precede a team service drop or recovery?
  - did skill identity explain cooperation-relevant trajectory differences
    beyond duration/length shortcuts?
- Only use this as reward after the posterior/outcome model beats duration and
  length shortcut baselines.

### 3b. What to distill from HMASD, not copy

User correction: the goal is not to discard HMASD.  HMASD's
discoverer/discriminator system has proven value in this cooperative relay
setting.  The new standalone algorithm should learn from those mechanisms while
keeping its own algorithm directory and process/SMDP framing.

Distill these functions:

- Discoverer as temporal skill executor: recurrent low-level policy, sequence
  update, centralized value, ValueNorm, and separated actor/critic optimization.
- Discriminator as semantic pressure: make executed skills induce distinguishable
  behavior, but move from one-step state labels toward process-level or
  cooperation-credit semantics.
- Update order discipline: policy uses reward from the pre-update estimator;
  estimator updates after the rollout, so reward generation and policy update
  remain on-policy for the collected data.
- Reward decomposition visibility: keep environment reward, semantic/process
  pressure, entropy, and credit diagnostics separately logged.

Do not distill these parts blindly:

- single-step next-observation skill classification as the only semantic test;
- relay-chain output as a hard-coded supervised target;
- off-policy reuse of discriminator/process data across rollout updates;
- direct import of HMASD classes into `ha_ctse_process`.

Implementation implication:

- First migrate discoverer capacity/critic structure, because P0 indicates the
  standalone low-level controller is likely underpowered for cooperation.
- Then add a process-level semantic estimator that can be switched on/off and
  tested against duration/length/reward shortcuts.
- Use relay/backhaul signals to diagnose cooperation credit assignment, not to
  define the core reward target.

Progress after this correction:

- Added standalone cooperation-credit diagnostics in
  `ha_ctse_process/cooperation_credit.py`.
- Wired the diagnostics into `StandaloneProcessAgent.process_update`, update
  CSV export, TensorBoard, train log parsing, and `ha_ctse_cooperation_credit`
  plots.
- These metrics are off the reward path.  They only measure segment-level
  disconnect/recovery/collapse, backhaul served/outage changes, relay loss
  changes, bottleneck, and reward/connectivity correlations.
- Smoke test `ha_ctse_process.smoke` now verifies reward-pure behavior remains
  unchanged while a toy disconnected-to-connected segment reports recovery.

Next discoverer migration slice:

1. Add a standalone recurrent low-level policy option inside
   `ha_ctse_process`, not by importing `hmasd.SkillDiscoverer`.  Done.
2. Store low-level recurrent hidden states and masks in `Rollout`.  Done.
3. Replace flat low-level PPO batches with chunked sequence batches.  Done.
4. Add centralized low-level critic input from global state and team/coordination
   code.  Done.
5. Add low-level ValueNorm and separate actor/critic optimizers.  Done.
6. Keep feedforward low-level as an explicit ablation/control.  Done via
   `--disable_recurrent_low_level`.

Implementation notes:

- `ha_ctse_process.standalone_agent.RecurrentLowLevelPolicy` keeps the low-level
  actor skill-bottlenecked on `(o_i, z_i)`, but gives the critic centralized
  `(state, team_code, z_i, agent_id)` context.
- `Rollout` now stores `env_id`, global `state`, `team_code`, low actor hidden
  state, and low critic hidden state for each transition.
- `update_low` reconstructs per-env sequences, chunks them, masks done resets,
  and runs recurrent PPO without crossing rollout boundaries.
- `low_value_norm` normalizes critic targets while policy advantages use
  denormalized values collected on-policy.
- The recurrent path is now the default in `ha_ctse_process.config`; the old
  feedforward path remains the explicit ablation.
- Smoke and a 4-step S7-S1 tiny train passed.

Network-scale correction:

- User pointed out that comparing against HMASD is unfair if the standalone
  process algorithm uses a smaller low-level network.
- Standalone defaults are now aligned to the main Scenario-7 HMASD scale:
  `n_Z=6`, `n_z=6`, `hidden_size=256` inherited from `config_1`,
  `low_rnn_hidden_size=256`, `low_ppo_epochs=15`, `low_sequence_length=10`,
  `low_value_loss_coef=1.0`, `low_max_grad_norm=0.5`.
- `network_scale_profile="hmasd_s7_256"` is written into the manifest and train
  startup log.
- Train startup now logs parameter counts:
  `params_total`, `params_high_stack`, `params_low`, and
  `params_process_stack`.
- Tiny S7-S1 smoke with this profile reported:
  `params_total=1819422`, `params_high_stack=295879`,
  `params_low=1096201`, `params_process_stack=427342`.
- Future claims about algorithmic improvement should compare runs under the same
  network-scale profile or explicitly label the run as a capacity ablation.

Strict HMASD/MAPPO low-level replica status:

- `ha_ctse_process.standalone_agent.StrictHMASDMAPPOLowLevelPolicy` now reuses
  HMASD's `MLPBase`, `RNNLayer`, and `ACTLayer`.
- Low actor path is:
  `MLPBase(o_i) -> skill FiLM(z_i) -> RNNLayer -> ACTLayer`.
- Low critic path is:
  `MLPBase(global_state) -> team-code FiLM(g) -> RNNLayer -> value`.
- Rollout stores actor/critic hidden states before action selection, global
  state, team code, log-probabilities, denormalized values, and env id.
- Low-level update is now MAPPO-style on-policy sequence PPO:
  per-env GAE(lambda), rollout-end bootstrap, recurrent sequence chunks,
  separate actor/critic optimizers, low-level ValueNorm, normalized target
  clipping, and PPO value prediction clipping.
- The older `RecurrentLowLevelPolicy` remains only as `gru_ctde` ablation; the
  original MLP low-level remains only as `feedforward` ablation.
- Verification on 2026-06-26:
  `py_compile` passed, `ha_ctse_process.smoke` passed, and a 4-step S7-S1
  strict-MAPPO tiny train completed with controlled low value loss.
- Low-level diagnostics added on 2026-06-26:
  `low_value_error_abs_mean`, `low_value_error_rmse`,
  `low_advantage_std`, `low_ratio_mean`, `low_clip_frac`,
  `low_approx_kl`, actor/critic grad norms, actor/critic hidden-state norms,
  skill/team-code usage entropy, skill/team-code return dispersion, and
  skill/team-code value-error dispersion.
- These metrics are exported to `metrics/train_updates.csv`, TensorBoard, the
  `standalone_update` log line, and two plots:
  `ha_ctse_low_level_diagnostics.png` and
  `ha_ctse_low_level_skill_team_diagnostics.png`.

Next structural slice:

1. Add explicit GAE(lambda) for recurrent low-level returns instead of pure
   Monte Carlo returns.  Done for the strict MAPPO path.
2. Add recurrent low-level diagnostics by skill/team-code: action entropy,
   value error, return mean, and hidden-state norm.  Done.
3. Revisit semantic pressure after the stronger discoverer has a short sanity
   run: process posterior can become auxiliary reward only if shortcut gaps and
   cooperation-credit diagnostics improve.

### 4. HMASD uses adaptive/structured exploration pressure

HMASD has separate entropy channels:

- team-code entropy coefficient;
- termination entropy coefficient;
- skill entropy coefficient;
- low-level action entropy coefficient;
- optional target-entropy adaptation.

The current standalone path has simpler fixed entropy pressure.  P0 shows large
high-level grad norms and high value losses, so entropy may be numerically
dominated by value-scale instability.

Migration implication:

- Split skill, duration, team-code, and low-level action entropy coefficients in
  the standalone path.
- Track their loss contribution relative to value loss.
- Consider target-entropy adaptation only after the reward/critic scale is under
  control.

### 5. HMASD high-level editing has keep/edit semantics and horizon masks

HMASD HA-CTSE path tracks requested edits, executed edits, H-min/H-max masking,
skill ages, suppressed edits, termination rate, duration target histogram, and
close reasons.

The standalone path currently samples a skill and a discrete lifetime when a
countdown expires.  This is simpler, but may make recovery from relay failure
too slow: once a poor skill/duration is selected, the agent may remain in a bad
relay role for many primitive steps.

Migration implication:

- Add explicit relay-failure early-renewal diagnostics first.
- Consider a relay-aware emergency termination option:
  if full disconnect or local backhaul loss persists, allow early skill renewal
  even before duration expiry.
- Treat this as a separate ablation, not as the default until diagnostics prove
  it is needed.

### 6. Current process outcomes are too generic

`ha_ctse_process/process_outcomes.py` already extracts coverage, throughput,
QoS, backhaul margin, energy, charging, and fallback reward/observation deltas.
It does not yet provide enough cooperation-credit diagnostics to explain why a
team succeeds or fails at stable connectivity.  The goal is not to make relay
chain output a first-class algorithm target.  The goal is to expose whether
skills, durations, and local actions are being assigned credit for their effect
on later team connectivity.

Useful relay/backhaul diagnostic proxies:

- mean/full-disconnect rate inside segment;
- segment starts disconnected and ends connected;
- segment starts connected and ends disconnected;
- delta `uavs_with_backhaul`;
- delta `connectivity_ratio`;
- delta/current `current_backhaul_served_users`;
- delta `backhaul_outage_ratio`;
- delta `relay_route_loss_ratio`;
- min/mean `min_serving_backhaul_bottleneck_mbps`;
- full-disconnect streak change;
- whether the acting UAV is on a routing path or critical relay path.

These fields should answer credit-assignment questions:

- Is a segment associated with later team service recovery or collapse?
- Does a skill create a stable cooperative role, or only change local movement?
- Are failures caused by never forming a chain, late formation, or chain break?
- Does the posterior/latent model learn cooperation-relevant semantics beyond
  duration, length, and raw return shortcuts?

Migration implication:

- Extend diagnostics before trusting process MI reward.
- Add segment-level relay/backhaul credit probes to train CSV and eval plots.
- Optional auxiliary heads may predict cooperation-relevant outcomes for
  representation learning, but they should remain off the reward path until
  ablation proves they improve task behavior rather than overfitting to relay
  proxies.

### Priority order after P0

Do not tune process reward first.  The audit indicates a larger structural gap:
cooperative credit assignment and low-level temporal control.

Recommended order:

```text
1. Add relay/backhaul cooperation-credit diagnostics, not reward targets.
2. Upgrade low-level policy/training toward recurrent MAPPO-style discoverer.
3. Add centralized low-level value or value normalization.
4. Add contribution-style diagnostics/baselines for agent role credit.
5. Optionally add cooperation-relevant auxiliary prediction heads for
   representation learning only.
6. Re-test reward-pure P0 with the stronger low-level/critic path.
7. Only then test process/semantic reward injection as a controlled ablation.
```

Decision rule:

- If reward-pure recurrent low-level still fails relay formation, inspect
  high-level skill/duration semantics and relay-aware early renewal.
- If recurrent low-level improves full-disconnect rate, the main missing HMASD
  bias was temporal low-level control and centralized value, not discriminator.
- If cooperation-credit diagnostics improve shortcut gaps and correlate with
  better eval behavior, then process reward may be reconsidered as a controlled
  ablation.

## 2026-06-27 Residual Process Posterior Slice

Motivation:

- The strict MAPPO low-level run improved implementation fairness but still
  showed weak cooperation learning and low-level reward oscillation.
- HMASD's discriminator/discoverer pair has useful semantic-pressure value, but
  a one-step discriminator is incompatible with the standalone process-core
  target.
- The new test should pressure the discoverer to produce segment-level skill
  semantics while explicitly rejecting trivial duration/length/reward shortcuts.

Implemented status:

- `ha_ctse_process/process_posterior.py` now trains a full segment posterior
  plus duration, segment-length, and reward-sum shortcut heads.
- `ha_ctse_process/standalone_agent.py` supports residual process reward modes:
  `residual_mi`, `positive_residual_mi`, `centered_residual_mi`, and
  `residual_mi_outcome`.
- `process_reward_injection` can target `none`, `high_only`, `low_only`, or
  `high_and_low`.
- Current preferred experiment is `residual_mi + low_only`, because it mirrors
  HMASD's semantic pressure on the discoverer without making the high-level
  controller chase a noisy auxiliary target first.
- New diagnostics are exported to logs, CSV, TensorBoard, and plots:
  `process_residual_mi_mean`, `process_residual_mi_positive_frac`,
  `process_shortcut_loss`, `process_shortcut_duration_acc`,
  `process_shortcut_length_acc`, `process_shortcut_reward_sum_acc`,
  `process_shortcut_max_acc`, and `posterior_acc_minus_shortcut_max`.
- Checkpoint loading uses non-strict process-posterior loading so old
  checkpoints do not fail because shortcut heads were added.

Verification:

```text
py_compile passed for process_posterior.py, standalone_agent.py, train.py,
eval_checkpoints.py, plotting.py, and smoke.py.

ha_ctse_process.smoke passed.

Tiny S7-S1 residual low-only train passed and logged:
process_resid_mi, process_shortcut_acc, posterior_gap_short, and
process_reward_low.
```

Current full-run command:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --n_agents 6 `
  --collector_backend subproc `
  --num_envs 8 `
  --rollout_length 500 `
  --skill_interval 10 `
  --total_timesteps 1280000 `
  --eval_interval 80000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --plot_interval 20 `
  --process_reward_mode residual_mi `
  --process_reward_injection low_only `
  --process_reward_coef 0.05 `
  --process_shortcut_coef 0.5 `
  --log_dir logs\ha_ctse_process_s7s1_6agent_residual_low_1280k
```

Codex runtime note:

- In the current Codex execution environment on Windows, `subproc` collector
  fails at `multiprocessing.Pipe()` with `PermissionError: [WinError 5]`.
- The user can still run the `subproc` command in a normal local terminal if
  desired.
- The background run launched from Codex on 2026-06-27 therefore uses the same
  algorithm settings with `collector_backend=sync`, `num_envs=8`, and log dir:

```text
logs\ha_ctse_process_s7s1_6agent_residual_low_sync_1280k_full
```

Read this run by comparing:

- eval reward/coverage/qos/throughput trend;
- `posterior_acc_minus_shortcut_max`;
- `process_residual_mi_mean` and positive fraction;
- `credit_full_disconnect_mean`;
- low-level value error, KL, clip fraction, and grad norms.

Decision rule after the run:

- If `posterior_acc_minus_shortcut_max <= 0` for most of training, the segment
  posterior is learning shortcuts rather than useful behavior semantics.
- If shortcut gap improves but eval reward does not, keep it as a diagnostic or
  reduce the reward coefficient.
- If shortcut gap and cooperation-credit metrics improve together, test
  `high_and_low` and `centered_residual_mi` as the next ablations.

## 2026-06-27 Semantic-Pressure Correction

The 1.28M residual low-only run showed that process posterior training was
connected but not yet solving semantic skill separation:

- `process_residual_mi_mean` stayed negative late in training;
- `posterior_acc_minus_shortcut_max` was not stably positive;
- `skill_switch_rate` stayed around 0.75, too high for stable UAV service and
  relay roles;
- low-level PPO clip fraction was high, and high-level bootstrap/grad norms had
  large spikes.

Code changes made after this diagnosis:

- `skill_lifetime_candidates` default changed from short/regular candidates to
  `(3, 7, 13, 24)`, corresponding to 30/70/130/240 primitive steps when
  `skill_interval=10`.
- Low-level PPO now has an independent `low_clip_epsilon`; default is 0.1 while
  the high-level `clip_epsilon` remains 0.2.
- Added `process_reward_warmup_steps`: process posterior and shortcut heads are
  trained during warmup, but process reward is not injected into policy updates.
- Added `process_shortcut_margin` and `process_shortcut_margin_coef`: full
  segment posterior is explicitly penalized unless it beats the best
  prior/duration/length/reward shortcut by a margin.
- Startup logs now print `process_warmup_steps`, `process_shortcut_margin`,
  `process_shortcut_margin_coef`, `clip`, `low_clip`, and
  `duration_candidates`.
- Train CSV/TensorBoard now include `process_shortcut_margin_loss` and
  `process_reward_warmup_active`.

Verification:

```text
py_compile passed.
ha_ctse_process.smoke passed.
Tiny S7-S1 train confirmed:
duration_candidates=(3, 7, 13, 24), low_clip=0.1,
process_warmup_steps, process_shortcut_margin, and process_margin_loss.
```

## 2026-06-27 Dense Transition Semantic Discriminator

Motivation:

- Segment posterior receives one sample per completed skill-lifetime segment.
  In long-horizon UAV service tasks, this is too sparse compared with HMASD's
  discriminator/discoverer pressure.
- The new algorithm should not import the legacy discriminator objective, but
  it should recover the useful idea: dense semantic pressure that pushes skill
  labels to correspond to behavior, not only duration or reward shortcuts.

Implemented status:

- Added `TransitionSkillDiscriminator` in
  `ha_ctse_process/process_posterior.py`.
- It predicts skill identity from primitive transition features:
  `o_t, a_t, delta_o_t, r_t, g`.
- `StandaloneProcessAgent.process_update` now expands completed segments into
  dense transition samples with a configurable cap
  `transition_skill_max_samples`.
- Transition discriminator loss is optimized by `process_opt` together with
  the process encoder/posterior stack.
- Pre-update transition MI,
  `log q(z | o,a,delta_o,r,g) - log p(z | g)`, can inject a small positive
  low-level semantic reward after `transition_skill_reward_warmup_steps`.
- It does not inject high-level rewards and does not redefine relay-chain
  output as a first-class objective.

New config/CLI fields:

- `use_transition_skill_discriminator`
- `transition_skill_condition_on_team`
- `transition_skill_coef`
- `transition_skill_prior_coef`
- `transition_skill_reward_coef`
- `transition_skill_reward_warmup_steps`
- `transition_skill_reward_clip`
- `transition_skill_max_samples`
- `--disable_transition_skill_discriminator`
- `--disable_transition_skill_team_conditioning`

Diagnostics:

- `transition_skill_samples`
- `transition_skill_available_samples`
- `transition_skill_loss`
- `transition_skill_prior_loss`
- `transition_skill_acc`
- `transition_skill_mi_mean`
- `transition_skill_mi_positive_frac`
- `transition_skill_reward_mean`
- `transition_skill_reward_active`
- `transition_skill_log_q_mean`
- `transition_skill_log_p_mean`

Verification:

```text
py_compile passed.
ha_ctse_process.smoke passed.
Tiny S7-S1 train passed and logged:
trans_samples, trans_acc, trans_mi, trans_reward, trans_active.
```

Decision rule:

- If `transition_skill_acc`/`transition_skill_mi_mean` rise but eval reward and
  cooperation-credit metrics do not improve, reduce
  `transition_skill_reward_coef` or keep this component diagnostic-only.
- If transition semantics improve before segment posterior gap improves, keep
  the dense discriminator and delay segment-level reward injection longer.
- If both transition MI and segment residual MI remain weak, revisit skill
  generator/context architecture rather than increasing reward coefficients.

## 2026-06-27 Intrinsic Reward Reconstruction

_Condensed 2026-07-06 (completed/superseded). Full text: `memory/backup_20260706/IMPLEMENTATION_PLAN.md`._

