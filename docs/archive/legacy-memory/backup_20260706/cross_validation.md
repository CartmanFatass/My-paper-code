# Cross-Validation Log — HA-CTSE / HMASD / OPT Review

Canonical file: `memory/cross_validation.md`

Legacy redirect: `memory/advice_cc.md`

This file is the standing cross-validation and decision-dialogue ledger for
Claude, GPT, Codex, the user, and other external reviewers. It records outside
advice, detailed project responses, accepted/rejected plan changes, and the
metadata for modifications that affect principles, implementation plans, code,
scripts, packaging, experiments, or result interpretation.

External Reviewer Quick-Review Standard:

```text
1. Start from the latest "Cross-validation handoff index" round.  As of
   2026-07-03 this is Round 13.
2. Use that round's memory reading order, reference-paper index, code/experiment
   state, and reviewer questions as the required review entry point.
3. Cite indexed memory/design/code files concretely.
4. State whether each recommendation is accepted, modified, rejected, or
   deferred, with evidence and affected files.
5. Avoid treating diagnostic communication metrics as intrinsic objectives.
6. Preserve the current benchmark hierarchy: S7-S1 parity first; S7-S3 later.
7. If a new outside review changes the active problem, add a new Round N
   handoff index or explicitly amend the latest handoff before acting on the
   advice. Do not leave external advice as unanchored chat text.
```

Required metadata for every new review/advice entry:

```text
Source:
  reviewer/model:
  role: architect | reviewer | executor | experiment-manager | packager | mixed
  input artifacts:
  scope: principles | implementation | experiment | result-interpretation | packaging | workflow
  disposition: accepted | modified | rejected | deferred | superseded
  affected files:
```

Required metadata for every accepted modification:

```text
Modification:
  changed_at:
  actor/model:
  active role:
  authority source:
  reason:
  affected files:
  linked plan section:
  linked experiment:
  validation performed:
  follow-up owner:
  status: proposed | accepted | implemented | validated | superseded
```

Use this file for detailed dialogue history and rationale. Use
`ATTENTION_POINTER.md` only for fast routing, `IMPLEMENTATION_PLAN.md` for the
active task ledger, and `ExpRecord.md` for experiment state.

Original created: 2026-06-28
Original reviewer: Claude (Cowork)
Original source: read-only review of `memory/ALGORITHM_KNOWLEDGE_BASE.md`,
`memory/ALGORITHM_PRINCIPLES.md`, `memory/IMPLEMENTATION_PLAN.md`,
`memory/IC_SPL_HAZARD_SMDP_ALTERNATIVE.md`, `memory/antigravity__CO46.md`.

---

## 2026-07-06 R21/R22 overnight cloud package

Modification:

```text
changed_at: 2026-07-06
actor/model: Codex
active role: Packager / Experiment Manager
authority source: user request to package overnight cloud experiments
reason: package launch-ready R21 team-intent and HMASD current-env baseline
affected files:
  dist/HA_CTSE_P0_MINIMAL_PACKAGE_FILES.md
  dist/HA_CTSE_R21_R22_OVERNIGHT_UPLOAD_README.md
  dist/ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
linked plan section: R22-2 keep experiment track running
linked experiment:
  EXP-20260705-r21-team-intent
  EXP-20260705-hmasd-currentenv-baseline
validation performed:
  bundle content check: required files present
  zip exclusion check: no __pycache__, .pyc, .pyo, .pt, .pth entries
  bash syntax check not run locally because bash is unavailable on Windows;
  server-side --dry-run is required before launch
follow-up owner: user/server operator
status: packaged
```

Notes:

```text
This is packaging-only.  No algorithm logic was changed.  The maintained dist
package manifest was amended to include the R21/R22 runners and root
`visualization.py`, which is required by the HMASD baseline path.  The runtime
zip intentionally excludes `memory/`; memory is local collaboration state and
should be shared separately only for review/context handoff.
```

---

## 2026-07-06 Claude review of R22/R21 implementation and Codex response

Source:

```text
reviewer/model: Claude, user-pasted external review
role: Reviewer
input artifacts:
  live repo diffs for R21/R22
  memory/R22_TWO_CLOCK_ELBO.md
  memory/R22_TARGET_ENTROPY_DESIGN.md
  R21 tests and runners
scope: implementation / experiment-readiness / result-interpretation
disposition: modified-accepted
affected files:
  ha_ctse_process/team_intent.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  train_multiproc_config_1.py
  tests/r21_team_intent_test.py
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
```

Review summary:

```text
Claude approved R21/HMASD launch structure with no critical blockers, but
identified three interpretation risks:
1. R21 reward arm can stack prototype-disc and team-disc intrinsic rewards while
   existing guards check them independently.
2. Team-disc reward is paid on the primitive-step clock; R22 needs Z-clock
   diagnostics (`z_decisions_per_update`, `z_advantage_mean/std/var`) before the
   reward-on 320k gate is interpreted.
3. HMASD light metrics can omit per-step reward_info, making step-fraction parity
   metrics silently appear as 0.0.
```

Accepted response:

```text
Implemented R22-3 diagnostics and guard support:
- `z_decisions_per_update` aliases Z-boundary decisions.
- `z_advantage_mean/std/var` is computed from unnormalized high-level advantages
  only on Z-boundary samples with nonzero `team_logp_weight`.
- `combined_intrinsic_env_ratio` and cumulative guard counters sum active
  prototype-disc and team-disc reward/env ratios, counting only components with
  actual applied reward steps so reward-off discriminator previews cannot
  contaminate the guard.  The combined guard uses the same
  `reward_ratio_guard_mode` kill/warn semantics as the individual guards.
- Console, TensorBoard, CSV/plotting schema, and log-parser aliases now expose
  these fields.
- HMASD eval now falls back from missing per-step samples to episode-level parity
  metrics and logs `parity_step_metric_fallback_used` plus sample count.
- R22 plan, attention pointer, implementation plan, and ExpRecord were updated
  so future agents treat R22-3 as implemented rather than pending.
```

Validation status:

```text
Validated locally on 2026-07-06:
- `tests/r21_team_intent_test.py -q`: 7 passed.
- AST parse of changed Python files: ok for 6 files.
- `python -m ha_ctse_process.train --help`: imports and lists CLI successfully.
- `py_compile` was attempted but blocked by Windows permission on an existing
  `__pycache__` rename; replaced by read-only AST parse.

Launch interpretation rule: R21 reward-on 320k reads must include
`combined_intrinsic_env_ratio`, `z_decisions_per_update`, and `z_advantage_*`.
HMASD baseline first eval must report whether `parity_step_metric_fallback_used`
is 0 or 1.
```

---

## 2026-07-05 GPT-5.5 Pro R22 review: R21/v6 mainline and two-clock ELBO plan

Source:

```text
reviewer/model: GPT-5.5 Pro, advice provided by user attachment
role: Architect / Reviewer
input artifacts:
  user-provided review text dated 2026-07-05
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
scope: principles / implementation plan / experiment interpretation
disposition: modified-accepted
affected files:
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Verdict:

```text
Accepted the core correction: the project had drifted too far toward the
R12 recognition-first / situation-response line.  The current mainline should
be the post-R21/v6 three-timescale hierarchy:

  OPT recognition substrate -> sampled slow team intent Z -> asynchronous
  individual response skills z_i.

R12 is retained as recognition substrate and control, not as the primary
cooperation engine.  R19 remains a mechanism-negative control unless later
complete reward-on logs contradict the current negative team-transition read.
The next highest-value work is not another reward module; it is a two-clock
ELBO/objective derivation that decides how team discriminator, individual
residual, entropy, and any cross-layer term compose.
```

Modification:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Architect / Planner
authority source: user request to write a plan from GPT-5.5 advice
reason: prevent long-task drift by making R21/v6 the explicit mainline and
  moving objective unification ahead of new reward design.
affected files:
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
linked plan section:
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
linked experiment:
  EXP-20260705-r21-team-intent
  EXP-20260705-hmasd-currentenv-baseline
validation performed:
  plan written; memory pointers updated; no code changes in this step
follow-up owner:
  Architect for R22 derivation; Executor only after the plan's diagnostic
  audit identifies missing metrics.
status: accepted / planned
```

Accepted plan consequences:

```text
1. R21/v6 is the active algorithmic mainline, not R12/R19.
2. R21 and HMASD baseline experiments remain launch-ready and should run in
   parallel with theory work; they are not blocked by the derivation.
3. Two-clock ELBO is R22-PR1 and should be written before any new reward
   mechanism is added.
4. Entropy/floors should be reframed as derived target-entropy constraints;
   current floors remain stabilizer flags until the design is implemented.
5. Mechanism budget is now explicit: every new mechanism must retire, absorb,
   or supersede one existing mechanism.
```

Execution receipt (same date, subagent-driven):

```text
R22-1 delivered:
  memory/R22_TWO_CLOCK_ELBO.md

R22-4 delivered:
  memory/R22_TARGET_ENTROPY_DESIGN.md

R22-3 audit delivered:
  existing diagnostics: z_usage_entropy, team_disc_reward_env_ratio,
  z_boundary_trunc_rate, z_boundary_trunc_rate_dur3/7/13/24.
  missing diagnostics for future code stage: z_decisions_per_update,
  z_advantage_mean/std/var, combined_intrinsic_env_ratio.

Review:
  Spec reviewer approved both R22 docs.
  Quality reviewer initially flagged five implementation-risk issues:
    Z/z_i metric ambiguity, target-temperature sign, clock-count normalization,
    detached/null baseline semantics, and tau/r notation mix.
  Codex fixed all five issues; re-review approved.

No training code was changed in this R22 execution.  R21 and HMASD baseline
experiments remain launch-ready and should not wait for further R22 theory work.
```

## 2026-07-05 Codex implements R21 launch-preflight fixes and cloud-direct launch support

Source:

```text
reviewer/model: Claude / CC review provided by user, then Codex verification
role: reviewer -> executor
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
  user instruction: direct cloud run, support n_agents, HMASD baseline set to 6-agent
scope: implementation / experiment / runner / baseline logging
disposition: modified-accepted
affected files:
  ha_ctse_process/config.py
  ha_ctse_process/team_intent.py
  ha_ctse_process/train.py
  ha_ctse_process/standalone_agent.py
  train_multiproc_config_1.py
  scripts/run_r21_team_intent_local_cuda.ps1
  scripts/run_r21_team_intent_cloud_64env.sh
  scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
  docs/superpowers/plans/2026-07-05-r21-launch-batch.md
  memory/ExpRecord.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Verdict:

```text
Accepted the launch-preflight critique with one user-driven routing change:
skip the local probe and launch R21 directly on cloud.  The structural fixes
remain mandatory before launch: K_team=48, team_disc_coef=0.05, default-off
Z entropy floor, per-duration truncation diagnostics.  HMASD baseline must be
6-agent and must expose HA-CTSE parity eval metrics before its result can be
used as the current-environment anchor.
```

Implemented changes:

```text
R21:
  - default `team_intent_k`: 12 -> 48.
  - default `team_disc_coef`: 0.1 -> 0.05.
  - added default-off `z_entropy_floor_*` config/CLI/manifest/checkpoint
    metadata, TensorBoard, console, and process metrics.
  - added `active_duration_indices` state and per-duration Z-boundary
    truncation metrics (`z_boundary_trunc_rate_dur3/7/13/24`).
  - updated R21 local runner and added `scripts/run_r21_team_intent_cloud_64env.sh`
    using the coef005 S-base: prototype-disc reward coef=0.05, duration floor
    disabled, guard kill.

HMASD baseline:
  - added `--n_agents` to `train_multiproc_config_1.py`.
  - made Scenario-7 validation respect explicit `--n_agents`.
  - added eval diagnostics/logging/TB for `coverage_eq1_step_fraction`,
    `coverage_eq1_episode_fraction`, `zero_throughput_episode_fraction`, and
    `throughput_gt5_step_fraction`.
  - added `scripts/run_hmasd_currentenv_baseline_cloud_64env.sh`.
```

Validation:

```text
Python AST/compile syntax check passed for modified Python files.
`ha_ctse_process.train --help` exposes `--enable_z_entropy_floor` and R21
controls.
`train_multiproc_config_1.py --help` exposes `--n_agents`.
PowerShell R21 local dry-run prints K=48, team_disc_coef=0.05, guard kill,
coef005 base, and duration floor disabled.
Linux bash runners were statically checked on Windows because local bash is
not installed; cloud must run each script with `--dry-run` before launch.
```

Modification:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor / Experiment Manager
authority source: user direct instruction + CC launch-preflight review
reason: prevent K_team/lifetime structural truncation, avoid known 0.1
  intrinsic-pressure pathology, preserve Z entropy diagnostics, and make the
  HMASD 6-agent baseline comparable to HA-CTSE eval metrics.
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
  docs/superpowers/plans/2026-07-05-r21-launch-batch.md
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
  memory/ExpRecord.md :: EXP-20260705-hmasd-currentenv-baseline
follow-up owner: Experiment Manager
status: implemented / locally syntax-validated / awaiting cloud dry-run and launch
```

## 2026-07-05 Codex reads R19 team-transition cloud logs

Source:

```text
reviewer/model: Codex
role: experiment-manager / reviewer
input artifacts:
  dist\r_19log\logs_cloud_r19_team_transition_64env
  memory/ExpRecord.md :: EXP-20260704-r19-team-transition-64env
scope: experiment / result-interpretation
disposition: modified
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Readout:

```text
Arms in downloaded R19 logs:
  a2_baseline_samecheck_reward_coef01:
    finished, exit_code=0, complete to 960k.
  a2_plus_t_probe_reward_off:
    finished, exit_code=0, complete to 960k.
  a2_plus_t_reward_coef005:
    downloaded snapshot says running and includes updates to 224k only.

No Traceback/RuntimeError/NaN/OOM found in the downloaded standalone logs.
```

Key numbers:

```text
Baseline 960k eval:
  reward=54.003165
  coverage=0.333333
  qos=0.178205
  throughput=11.400000
  backhaul_connected_frac=0.365600
  zero_throughput_ep_frac=0.600000
  coverage_eq1_step_frac=0.000000

A2+T probe reward-off 960k eval:
  reward=23.786741
  coverage=0.115000
  qos=0.072848
  throughput=5.700000
  backhaul_connected_frac=0.272800
  zero_throughput_ep_frac=0.600000
  coverage_eq1_step_frac=0.000000

A2+T reward-on downloaded snapshot:
  latest update=7, total_steps=224000
  160k eval reward=22.442625
  coverage=0.100000
  qos=0.061031
  throughput=1.864259
  backhaul_connected_frac=0.234100
  zero_throughput_ep_frac=0.750000
```

Mechanism gate:

```text
Reward-off probe at 960k:
  team_t_samples=3136
  team_t_mi=-0.042034
  team_t_self=0.923
  last-5 mean team_t_mi=-0.064172
  last-5 mean team_t_self=0.9312

Reward-on snapshot at 224k:
  team_t_mi=-0.044873
  team_t_self=0.921
  team_t_rew=-0.018776
  team_t_ratio=0.016
  last-5 mean team_t_mi=-0.052448
  last-5 mean team_t_ratio=0.0142
```

Interpretation:

```text
R19, as currently implemented, does not pass its own reward-off mechanism gate.
The expected sign was sustained positive team-transition MI; the observed
probe signal is consistently negative through 960k.  The self fraction is in
the nominal band but close to the upper edge, suggesting the head mostly sees
self/unchanged transitions and is not providing a useful team residual.

The reward-on arm is not complete in the downloaded snapshot, so this is not a
final reward-arm verdict.  But the early reward-on mechanism metrics follow
the same negative-MI pattern and the 160k task readout is not better than the
matched baseline.  The safe conclusion is mechanism-negative unless a later
complete reward-on log contradicts it with sustained positive team_t_mi and
task gains.
```

Decision:

```text
Do not broaden R19 coefficient sweeps from this evidence.  Treat R19
team-transition residual as not yet the missing HMASD-style team engine.
Compare against the R21 team-intent restoration line, where a sampled team
intent Z ships with an objective/discriminator pressure rather than relying on
the current transition residual target.
```

Modification:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: experiment-manager / reviewer
authority source: downloaded R19 cloud logs in dist and pre-registered
  EXP-20260704-r19-team-transition-64env gates
reason: record the R19 mechanism-negative read and prevent drift into R19
  coefficient sweeps before a valid reward-off signal exists.
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
linked plan section: R19 team-transition heads
linked experiment: EXP-20260704-r19-team-transition-64env
validation performed: parsed standalone_train.log lines for eval/update
  metrics and checked runner_status plus traceback/NaN/OOM patterns.
follow-up owner: Experiment Manager / Architect
status: implemented
```

---

## 2026-07-05 Codex reads R16.5 continuation 64env cloud logs

Source:

```text
reviewer/model: Codex
role: experiment-manager / reviewer
input artifacts:
  dist\logs_cloud_r16_5_continuation_64env
  memory/ExpRecord.md :: EXP-20260705-r16-5-continuation
scope: experiment / result-interpretation
disposition: accepted / completed
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Readout:

```text
Both downloaded continuation branches finished cleanly with exit_code=0 and no
Traceback/NaN/OOM found.

seed2, floor_coef=0.05, 960k:
  reward_mean=71.713382
  coverage=0.416667
  qos=0.240737
  throughput=13.105124
  backhaul_connected_frac=0.500000
  zero_throughput_ep_frac=0.500000
  coverage_eq1_step_frac=0.016400
  duration_usage_entropy=0.937736 final / 0.958307 last10
  duration_entropy_floor_active=0 final / 0 last10
  proto_disc_reward_env_ratio=0.060781 final / 0.054688 last10
  roster_ar_kl_shuffled~=0.000005 final / 0.000004 last10

seed1, floor_coef=0.1 bounded retry, 960k:
  reward_mean=31.248840
  coverage=0.121667
  qos=0.091398
  throughput=6.778694
  zero_throughput_ep_frac=0.650000
  coverage_eq1_step_frac=0
  duration_usage_entropy=0.917980 final / 0.941544 last10
  duration_entropy_floor_active=0 final / 0 last10
  proto_disc_reward_env_ratio=0.230569 final / 0.235317 last10
  roster_ar_kl_shuffled~=0.000004
```

Interpretation:

```text
The 64env seed2 coef=0.05 run improves the story versus the local scaffolded
read on lifetime stability: duration entropy self-sustains late and the floor
is inactive.  But it remains far from the user-stated S7-S1 parity bar
(`coverage_eq1_step_frac=0.0164` versus the target of at least half of eval
steps at coverage==1.0), and zero-throughput episodes are still 50%.

The one allowed coef=0.1 retry is negative: it keeps duration entropy high but
materially worsens task metrics.  This closes the bounded retry branch.

Roster content remains decorative in both branches (`roster_ar_kl_shuffled`
around 4e-6 to 5e-6), so this read does not justify any further broad R16
roster-only sweep.
```

Decision:

```text
Stop R16.5 floor tuning.  Keep coef=0.05 as a stabilized baseline/control with
the narrow claim that it helps avoid duration collapse / late regression in
some settings.  It does not solve the cooperative parity target.  Move
algorithmic attention to R19/R21 rather than more R16 roster tuning.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Experiment Manager / Reviewer
authority source: user request to inspect downloaded dist logs
reason: completed cloud logs changed experiment status and closed the R16.5
  bounded floor-retry branch.
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: R16.5 / roster-docking stabilization
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r16-5-continuation
validation performed:
  read runner_status.txt, standalone_train.log eval lines, metrics/eval_episodes.csv,
  and metrics/train_updates.csv from both continuation branches.
follow-up owner: Codex / Experiment Manager
status: completed / interpreted
```

---

## 2026-07-05 Codex review of `ALGORITHM_DESCRIPTION_v6.md`

Source:

```text
reviewer/model: Claude / Research Copilot proposal, reviewed by Codex
role: reviewer
input artifacts:
  memory/ALGORITHM_DESCRIPTION_v6.md
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
scope: principles / algorithm description / reference promotion
disposition: modified / pending user confirmation
affected files:
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
```

Verdict:

```text
Accept `ALGORITHM_DESCRIPTION_v6.md` as a strong conceptual synthesis of the
current HA-CTSE direction, but do not yet promote it as the sole canonical
reference that principles point to without a status box that separates:
  implemented code,
  locally validated wiring,
  experiment-supported behavior,
  theoretical / intended claims.
```

Strongest-for:

```text
The v6 description correctly captures the current post-R21 algorithm shape:
three timescales, recognition vs sampled commitment distinction, sampled Z as
the non-vacuous team engine, prototype-response skills, held team intent,
atomic Z-boundary reassignment, async docking between boundaries, and the
communication-metrics-as-diagnostics boundary.  It also correctly puts the
vacuity lemma at the center of why recognized kappa and sampled Z need different
intrinsic pressures.
```

Strongest-against / required qualifications:

```text
1. "HMASD is the exact special case" is useful as an architectural limiting
   case, but code-level exact equivalence is not yet proven.  Phrase as
   limiting case unless an explicit full-sync/HMASD-reduction test is added.

2. The substrate-language around OPT prototypes / omega / kappa should not
   overstate validation.  The substrate gate and compact/omega diagnostics are
   evidence for using OPT as a situation basis, but R21 performance and the
   team-intent engine are not yet experimentally validated.

3. The intrinsic system description should label R21 team intent and team-disc
   reward as implemented default-off and locally smoke-validated, not
   performance-validated.  Current R21 has no formal 320k/960k read yet.

4. "Provided by construction" is true for async lifetimes and atomic
   Z-boundary reassignment in the implemented mechanism, but rollout and
   checkpoint boundaries can still truncate held decisions.  The read must
   report `z_boundary_trunc_rate` before making a strong mechanism claim.
```

Sober number / current blocker:

```text
The strongest current performance read is still R16.5 PASS-SCAFFOLDED, not a
clean parity result: 960k `coverage_eq1_step_frac=0.075700`, far below the
near-term HMASD-level target of at least half of primitive eval steps at
coverage == 1.0.  v6 should therefore be framed as the current algorithmic
design contract, not as a solved-behavior description.
```

Decision:

```text
If the user confirms, promote v6 by adding a pointer from
`ALGORITHM_PRINCIPLES.md` to `ALGORITHM_DESCRIPTION_v6.md`, but first add an
"Implementation / Validation Status" section to v6 with the caveats above.
Until then, v6 remains a pending canonical-description candidate.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Reviewer
authority source: user supplied Claude note saying v6 awaits confirmation
reason: prevent a pending external description from being mistaken for an
  already-confirmed reference contract.
affected files:
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  read-only review of v6 against current principles, plan, pointer, and
  experiment dashboard; no code validation required.
follow-up owner: user / Codex
status: reviewed / modified-acceptance / awaiting user confirmation
```

---

## 2026-07-05 Codex pre-registers R21 local CUDA launch runner

Source:

```text
reviewer/model: user + Codex
role: executor / experiment-manager
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
scope: experiment / runner
disposition: accepted / implemented
affected files:
  scripts/run_r21_team_intent_local_cuda.ps1
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md
  memory/cross_validation.md
```

Summary:

```text
Created a local CUDA runner for the formal R21 read.  Default experiments are
`r21_z_probe` and `r21_z_reward`, both inheriting the stabilized R16.5 entfloor
and prototype-discriminator reward base.  The runner also offers optional
`entfloor_control` under the same code snapshot.  The first R21 read is a 320k
structural gate; the 960k result is meaningful only if that gate is healthy.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Experiment Manager / Executor
authority source: user "continue" after R21 implementation + R21 spec
reason: R21 code was implemented but not launch-aligned; the experiment needed
  exact commands, controls, and gates before any run.
affected files:
  scripts/run_r21_team_intent_local_cuda.ps1
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md
  memory/cross_validation.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_r21_team_intent_local_cuda.ps1 -DryRun` -> exit 0.
  - Dry-run output showed inherited entfloor controls, `--team_bridge_type stochastic`,
    `--reward_ratio_guard_mode warn`, `--enable_team_intent`, and distinct
    probe/reward arms.
follow-up owner: Codex / Experiment Manager
status: implemented / dry-run validated / launch-ready
```

---

## 2026-07-05 Codex post-review fixes for R21 wiring

Source:

```text
reviewer/model: Codex subagent Pascal + Codex
role: reviewer / executor
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  current R21 diffs in ha_ctse_process/*
scope: implementation / code review
disposition: accepted / implemented
affected files:
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  tests/r21_team_intent_test.py
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
```

Summary:

```text
The read-only review found four real R21 wiring risks: missing `team_codes` in
the prototype-discriminator batch, legacy low-actor team-code conditioning still
being possible, `team_bridge_type=none` silently degenerating Z, and missing
checkpoint state for the team-intent empirical prior.  All four were fixed
before handoff.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor
authority source: user-authorized subagent review + R21 implementation task
reason: prevent silent or crashing R21 combination experiments before launch.
affected files:
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  tests/r21_team_intent_test.py
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  - `python -m pytest tests\r21_team_intent_test.py -q` -> 6 passed.
  - R21 + prototype-disc smoke -> exit 0.
  - R21 + reward-on checkpoint smoke -> exit 0.
  - checkpoint readback confirmed tensor-safe `team_intent_prior_counts`.
  - R21 + `team_bridge_type=none` CLI smoke -> expected ValueError.
  - import check -> import_ok.
  - `git diff --check` -> exit 0, with pre-existing pytest-temp permission warnings.
follow-up owner: Codex / Experiment Manager
status: implemented / validated / no formal R21 run launched
```

---

## 2026-07-05 Codex implements R21 Team-Intent Restoration default-off

Source:

```text
reviewer/model: user directive + CC-reviewed R21 plan + Codex
role: executor
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  memory/ATTENTION_POINTER.md R21 directive
  memory/IMPLEMENTATION_PLAN.md Round 21 section
scope: implementation / algorithm mechanism / diagnostics
disposition: accepted / implemented
affected files:
  ha_ctse_process/team_intent.py
  ha_ctse_process/config.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  tests/r21_team_intent_test.py
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
```

Summary:

```text
Implemented the R21 two-clock team-intent mechanism as default-off code:
sampled held team intent Z, atomic full-team AR reassignment at Z boundaries,
async individual docking against held Z between boundaries, boundary-only Z
log-prob charging, skipped edit/switch penalty at Z boundaries, and an optional
team discriminator reward/probe over next-state labels.  Metrics now expose
Z usage/dwell/truncation/intervention and team-disc loss/accuracy/residual/
reward-ratio diagnostics.

No formal R21 performance run has been launched.  The new ExpRecord entry is
planned-only and requires an exact stabilized-base command/gate before launch.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor
authority source: user explicit implementation request + R21 user override in
  memory pointer and implementation plan
reason: restore HMASD-style team skill/cooperative pressure while preserving
  asynchronous per-agent lifetimes; R21 supersedes Round 20 team-bridge removal
  as the active code task.
affected files:
  ha_ctse_process/team_intent.py
  ha_ctse_process/config.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  tests/r21_team_intent_test.py
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  - `python -m pytest tests\r21_team_intent_test.py -q` -> 4 passed.
  - import check for train/standalone_agent/team_intent/plotting -> import_ok.
  - structure smoke with `--enable_team_intent --enable_team_disc_probe` -> exit 0.
  - reward-on smoke with `--enable_team_disc_reward --reward_ratio_guard_mode warn` -> exit 0, warn guard logged without stopping.
  - `git diff --check` -> exit 0; existing `.pytest_tmp_r12_verify` permission warnings remain unrelated to R21.
follow-up owner: Codex / Experiment Manager
status: implemented / locally validated / experiment not launched
```

---

## 2026-07-05 Codex adds HA-CTSE run-result packaging scripts

Source:

```text
reviewer/model: user + Codex
role: executor / packager
input artifacts:
  user request: write a one-click packaging script for remote experiment logs
  scripts/run_r19_team_transition_64env.sh
  ha_ctse_process/train.py logging paths
scope: packaging / experiment-result transfer
disposition: accepted
affected files:
  scripts/package_ha_ctse_run_results.sh
  scripts/package_ha_ctse_run_results.ps1
```

Summary:

```text
Added one-click result packagers for HA-CTSE runs.  The default package is the
minimum trustworthy analysis set: metadata/run_manifest.json, metrics CSV/JSON,
standalone_train.log, runner_status.txt, runner_output.log, command.txt, and
top-level JSON files.  Checkpoints and plots are opt-in to keep routine remote
downloads small.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Packager / Executor
authority source: user explicit request
reason: Remote runs need a reproducible way to download enough evidence for
  strict experiment interpretation, not just metrics CSV files.
affected files:
  scripts/package_ha_ctse_run_results.sh
  scripts/package_ha_ctse_run_results.ps1
linked plan section: experiment packaging workflow
linked experiment: applies to R16.5/R19 and future HA-CTSE remote runs
validation performed:
  - PowerShell packager tested on `logs\_r19_team_transition_smoke`.
  - Output package created at `dist\test_r19_smoke_results.zip`.
  - Bash packager not executed locally because this Windows environment has no
    `bash`; it is intended for remote Linux servers.
follow-up owner: Codex / Experiment Manager
status: accepted / implemented / partially validated
```

---

## 2026-07-05 Codex creates `LTM_exp` experimental skill

Source:

```text
reviewer/model: user + Codex
role: executor / workflow-maintainer
input artifacts:
  C:\Users\wu\.codex\skills\.system\skill-creator\SKILL.md
  C:\Users\wu\.codex\skills\.system\skill-creator\references\openai_yaml.md
  C:\Users\wu\.codex\skills\long-task-memo\SKILL.md
  memory/AGENT_ROLES.md
scope: workflow / skill-testing
disposition: accepted
affected files:
  C:\Users\wu\.codex\skills\ltm-exp\SKILL.md
  C:\Users\wu\.codex\skills\ltm-exp\references\role-playbook.md
  C:\Users\wu\.codex\skills\ltm-exp\references\memory-protocol.md
  C:\Users\wu\.codex\skills\ltm-exp\scripts\init_memory.py
  C:\Users\wu\.codex\skills\ltm-exp\agents\openai.yaml
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
```

Summary:

```text
The stable LongTaskMemo role protocol is useful but should be tested in a
separate experimental skill before promoting further changes.  User requested
`LTM_exp`; skill-creator naming rules require lowercase hyphen-case, so the
folder/name is `ltm-exp` and the UI display name is `LTM_exp`.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor / workflow-maintainer
authority source: user explicit request
reason: Create an experimental skill for testing detailed multi-agent role
  behavior, reviewer plan-amendment authority, experiment dashboards, and
  modification metadata before backporting into stable LongTaskMemo.
affected files:
  C:\Users\wu\.codex\skills\ltm-exp\SKILL.md
  C:\Users\wu\.codex\skills\ltm-exp\references\role-playbook.md
  C:\Users\wu\.codex\skills\ltm-exp\references\memory-protocol.md
  C:\Users\wu\.codex\skills\ltm-exp\scripts\init_memory.py
  C:\Users\wu\.codex\skills\ltm-exp\agents\openai.yaml
linked plan section: collaboration workflow protocol
linked experiment: none
validation performed:
  - `skill-creator` quick_validate passed.
  - `init_memory.py` parsed with Python AST.
  - Temporary scaffold initialization verified `AGENT_ROLES.md`,
    `ExpRecord.md` dashboard, and advice/cross-validation metadata.
follow-up owner: Codex / user during skill testing
status: accepted / implemented / validated
```

---

## 2026-07-05 Codex response to collaboration-memory protocol update

Source:

```text
reviewer/model: user + Codex
role: mixed (architect/workflow-reviewer/executor)
input artifacts:
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md
  memory/cross_validation.md
  C:\Users\wu\.codex\skills\long-task-memo\SKILL.md
scope: workflow
disposition: accepted
affected files:
  memory/AGENT_ROLES.md
  memory/ExpRecord.md
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
  C:\Users\wu\.codex\skills\long-task-memo\SKILL.md
```

Summary:

```text
The long-running HA-CTSE workflow needs explicit multi-agent role boundaries,
a top-level experiment dashboard, and source-aware cross-validation entries.
This prevents architect/reviewer/executor drift, makes running experiments
scannable, and separates Claude/GPT/Codex/user advice by source and scope.
```

Project response:

```text
Accepted.  Added `memory/AGENT_ROLES.md`, added an Experiment Dashboard to
`memory/ExpRecord.md`, added source metadata requirements to this file, and
updated the LongTaskMemo skill so future agents read role instructions and
maintain dashboard/cross-validation metadata before acting.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor / workflow-maintainer
authority source: user explicit request and confirmation
reason: LongTaskMemo must support multi-agent roles, reviewer plan proposals,
  experiment dashboard scanning, and detailed cross-validation metadata.
affected files:
  memory/AGENT_ROLES.md
  memory/ExpRecord.md
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
  C:\Users\wu\.codex\skills\long-task-memo\SKILL.md
  C:\Users\wu\.codex\skills\long-task-memo\references\memory-protocol.md
  C:\Users\wu\.codex\skills\long-task-memo\scripts\init_memory.py
linked plan section: collaboration workflow protocol
linked experiment: none
validation performed:
  - LongTaskMemo initializer syntax checked with Python `ast.parse`.
  - Temporary scaffold initialization verified creation of `AGENT_ROLES.md`.
  - Temporary scaffold initialization verified `ExpRecord.md` dashboard fields.
  - Temporary scaffold initialization verified advice/cross-validation source
    and modification metadata fields.
follow-up owner: Codex
status: accepted / implemented / validated
```

---

## 2026-07-05 Codex R16.5 entfloor completed readout

Status: COMPLETED / PASS-SCAFFOLDED. This is the completed result for
`EXP-20260704-r16-5-coef01-entfloor`.

Run:

```text
logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_233759\seed1\a2r_roster_reward_coef01_entfloor
state=finished
exit_code=0
finished=2026-07-05T06:05:14+08:00
```

Comparison reference:

```text
logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01
```

Eval read:

```text
Reference 480k peak:
  reward=78.140158
  coverage=0.345000
  qos=0.271246
  throughput=22.015988
  backhaul_connected_frac=0.387600
  zero_throughput_ep_frac=0.550000

Reference 960k collapse:
  reward=20.078933
  coverage=0.080000
  qos=0.061291
  throughput=6.547736
  backhaul_connected_frac=0.210400
  zero_throughput_ep_frac=0.750000

Entfloor 960k:
  reward=67.263427
  coverage=0.493333
  qos=0.341250
  throughput=27.252762
  backhaul_connected_frac=0.446900
  zero_throughput_ep_frac=0.200000
  coverage_eq1_step_frac=0.075700
  coverage_eq1_ep_frac=0.300000
```

Gate interpretation:

```text
Performance side passes: entfloor 960k holds >80% of the reference 480k peak
and is much better than the reference 960k collapse.

Mechanism side does not pass cleanly:
  update_960k duration_usage_entropy=0.543469
  update_960k duration_usage_max_frac=0.770270
  update_960k duration_policy_entropy_norm=0.534978
  update_960k duration_entropy_floor_active=1
  last10 duration_entropy_floor_active=1.0

Therefore: PASS-SCAFFOLDED, not PASS-CLEAN.  The floor is a legitimate
stabilizer / parity baseline, but lifetime heterogeneity is floor-supported
late in training and cannot be claimed as emergent self-maintaining behavior.
```

Guard / roster notes:

```text
Warn-mode ratio guard behaved as intended: the run completed, while logging
would-have-killed events.  `proto_disc_reward_env_ratio_kill_triggered=2` and
`proto_disc_reward_env_ratio_over05_count=25` by 960k, so reward-scale pathology
co-occurred and should be kept in the interpretation.

Roster AR signal remains effectively decorative:
  proto_ar_parallel_kl ~= 5e-06
  roster_ar_kl_shuffled ~= 5e-06
This does not support another broad roster-only sweep.
```

Codex recommendation:

```text
1. Complete/read the P2 deterministic/stochastic eval-mode cells on the
   reference update_60/update_120 checkpoints.
2. Treat entfloor as a useful stabilized R16 base only with an explicit
   floor-supported mechanism caveat.
3. Do not promote the roster AR mechanism from this result; if the next
   algorithmic step is needed, compare against R19/a2_plus_t rather than doing
   another roster-only sweep.
4. Seed-2 confirmation is required before any claim beyond this seed-1 gate.
```

---

## 2026-07-04 Codex response to CC FINAL guard-mode spec

Status: ACCEPTED and implemented. This closes Condition 1 for
`EXP-20260704-r16-5-coef01-entfloor`: the entfloor comparison can now run with
reference-matched termination behavior while still logging every
would-have-killed prototype reward-ratio event.

```text
Implemented:
  ha_ctse_process/config.py
    reward_ratio_guard_mode = "kill"  # default

  ha_ctse_process/train.py
    --reward_ratio_guard_mode {kill,warn}
    start line / manifest includes reward_ratio_guard_mode.

    kill mode:
      current behavior preserved; update metrics are exported first, then
      RuntimeError is raised.

    warn mode:
      logs standalone_runtime_guard_warn and continues.

    exported guard metrics:
      proto_disc_reward_env_ratio_over05_count
        cumulative count of post-warmup updates with ratio > 0.5;
        it no longer resets after a trigger.
      proto_disc_reward_env_ratio_kill_triggered
        cumulative count of would-have-killed updates.
      proto_disc_reward_env_ratio_guard_active
        per-update active flag unchanged.

  scripts/run_r16_a2r_overnight_local_cuda.ps1
    a2r_roster_coef01_entfloor now hard-passes
      --reward_ratio_guard_mode warn
    and prints guard_mode: warn in the per-arm banner.

  scripts/run_r16_a2r_remote_32env.sh
    mirrored the same entfloor warn-mode flag and banner.
```

Validation:

```text
Config default:
  Config.reward_ratio_guard_mode -> kill

In-memory compile:
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  -> ok

Local runner dry-run:
  scripts/run_r16_a2r_overnight_local_cuda.ps1
    -Experiments a2r_roster_coef01_entfloor -DryRun
  -> banner prints guard_mode: warn
  -> command includes --reward_ratio_guard_mode warn

Forced-trigger warn smoke:
  logs\smoke_r16_5_guard_warn
  -> update 1 and 2 both triggered instant guard but run continued.
  -> CSV last row: over05_count=2.0, kill_triggered=2.0.

Forced-trigger kill smoke:
  logs\smoke_r16_5_guard_kill
  -> RuntimeError after update 1.
  -> CSV row was written first: over05_count=1.0, kill_triggered=1.0.

Remote bash dry-run:
  not executed locally because this Windows environment lacks bash.
  Script content was checked: entfloor arm contains
    guard_mode="warn"
    --reward_ratio_guard_mode warn
  and prints guard_mode in the banner.
```

Project response:

```text
Launch condition satisfied for R16.5 entfloor: use the local runner arm
`a2r_roster_coef01_entfloor`; do not manually omit the warn flag. If
proto_disc_reward_env_ratio_kill_triggered grows during the run, it marks the
read as reward-scale-pathology-contaminated but does not invalidate process
completion by itself.
```

## 2026-07-04 Codex R16.5 closing-plan implementation receipt

Status: ACCEPTED and implemented as a default-off stabilization / diagnostic
patch set.  This does not change the R16 roster objective, bootstrap
coefficient, duration candidates, low-level architecture, or environment
reward.  It prepares the one-variable R16.5 rerun requested by CC's forensic
read of the 480k peak / 960k collapse.

```text
Implemented:
  1. Duration entropy floor:
     --enable_duration_entropy_floor
     --duration_entropy_floor_threshold
     --duration_entropy_floor_coef
     --duration_entropy_floor_warmup_steps

     The floor is applied to the high-level duration head only when realized
     duration_usage_entropy falls below the threshold.  It logs:
       duration_policy_entropy
       duration_policy_entropy_norm
       duration_entropy_floor_active
       duration_entropy_floor_gap
       duration_entropy_floor_loss
       duration_entropy_floor_coef_active

  2. Tightened prototype reward-ratio kill:
     instant kill if proto_disc_reward_env_ratio > 1.0 post-warmup;
     sustained kill if proto_disc_reward_env_ratio > 0.5 for 5 consecutive
     post-warmup updates.
     The triggering update is exported before RuntimeError is raised.

  3. Eval-mode diagnostic:
     --eval_action_mode deterministic|stochastic
     Default remains deterministic; stochastic uses existing agent sampling
     path for both high-level assignment and low-level action selection.

  4. Runner support:
     scripts/run_r16_a2r_overnight_local_cuda.ps1
     scripts/run_r16_a2r_remote_32env.sh
     add arm `a2r_roster_coef01_entfloor`; default arm lists unchanged.
     scripts/run_r16_5_p2_eval_modes.ps1 adds the four checkpoint/mode
     eval reads for update_60/update_120 deterministic/stochastic.
```

Validation:

```text
In-memory compile:
  ha_ctse_process/config.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  -> ok

Tiny CPU train smoke:
  --enable_duration_entropy_floor with high threshold
  -> completed; floor activated when duration_usage_entropy fell below threshold.

Tiny stochastic eval smoke:
  --eval_action_mode stochastic
  -> completed; eval output includes action_mode=stochastic.

R16.5 P2 eval wrapper dry-run:
  scripts/run_r16_5_p2_eval_modes.ps1 -DryRun
  -> expanded all four eval commands and verified update_60/update_120
     checkpoints exist.
```

Bookkeeping:

```text
ExpRecord:
  EXP-20260704-r16-5-coef01-entfloor

Best-known R16/S7-S1 checkpoint recorded:
  logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01\standalone_process_core_update_60.pt

Late collapsed comparison checkpoint:
  logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01\standalone_process_core_update_120.pt
```

Next read:

```text
Launch only `a2r_roster_coef01_entfloor` as the R16.5 one-variable rerun,
then run the four P2 eval-mode reads on update_60/update_120:
  deterministic update_60
  stochastic     update_60
  deterministic update_120
  stochastic     update_120
Do not mix this R16.5 stabilization read with R19 team-transition results.
```

## 2026-07-04 Research Insight Duties added to AGENT_ROLES (user-mandated skill-gap fix)

Modification:
  changed_at: 2026-07-04
  actor/model: CC (Claude, Cowork)
  active role: Reviewer (process/meta change, user authority)
  authority source: user — "the reviewer and architect role don't give
    insight from research view"
  reason: role definitions enforced authority hygiene but no epistemic
    duties; process-valid reviews were possible that never stated a belief,
    weighed evidence, or confronted the most inconvenient number
  affected files: memory/AGENT_ROLES.md (new "Research Insight Duties"
    section, R-1..R-8 + verdict template)
  linked principle/plan: none (meta/workflow layer)
  linked experiment: none
  validation performed: duties derived from this session's observed gap
    (gate-check reviews vs the calibrated R21 belief answer); each rule
    cites the project incident that motivated it
  follow-up owner: user — merge the same text into the ltm-exp skill's
    role-playbook via Settings > Capabilities (the installed skill is a
    read-only cache in-session and cannot be edited from here)
  status: implemented (project memory); proposed (skill source)

Duties added: R-1 calibrated belief, R-2 evidence hierarchy, R-3
sobering-number rule, R-4 premise audit, R-5 mechanism dissociation, R-6
falsification-first, R-7 opportunity cost, R-8 seam vigilance; plus a
verdict response template. Binding on Reviewer and Architect for any model.

## 2026-07-05 CC (Research Copilot) principles-level advice: Round 22 candidates

Modification: actor CC (Research Copilot); authority: user invocation
("advice on the principles level"); affected: this ledger; status: advice
logged, items await user adoption.

```text
THROUGH-LINE: v6 has a unified ARCHITECTURE but a patchwork OBJECTIVE;
the deep issues are symptoms of that.

PR-1 UNIFY THE OBJECTIVE (highest value): derive the two-clock ELBO for
   the ACTUAL current model (hierarchical semi-Markov PGM, slow sampled Z
   + fast sampled z_i). The R15 derivation is STALE post-R21 (it assumed
   recognition-only). Would answer: (i) do coordinator-residual and team-
   disc terms compose or double-count; (ii) principled relative scales
   (the dose-response finding is the empirical signature of unprincipled
   coefficients); (iii) missing cross-layer terms (e.g. I(Z; xi)). Nobody
   has published the two-clock bound — paper theory core. ~75% it yields
   at least one of the three. Zero GPU; parallel to runs.
PR-2 ENTROPY AS DERIVED CONSTRAINT, NOT PATCHED BONUS: per-head
   target-entropy Lagrangian (SAC-style auto-temperature) subsumes floor +
   anneal + z-floor in one principled mechanism; and once entropy terms
   are DERIVED (PR-1 gives them free), the PASS-SCAFFOLDED qualification
   dissolves honestly — HMASD's entropy was never emergent either, it was
   in the objective. Split R10.2-F: keep "never force heterogeneity as a
   reward target"; stop outlawing principled entropy control.
PR-3 THE CREDIT TENSION TRIANGLE (own it before a reviewer does):
   K_team >= max lifetime (protect fast clock) vs pi_Z sample efficiency
   vs Z-advantage variance. At K_team=48: ~1 Z-decision/episode. Intrinsic
   to the two-clock idea; state as principle + diagnostics (Z-decisions
   per update; Z-advantage variance). Graceful degradation note: q_D
   reward shapes the low level even while pi_Z learns slowly.
PR-4 MECHANISM BUDGET (cultural): every new mechanism retires or absorbs
   one; the ELBO doubles as the pruning tool (terms not in the bound are
   deletion candidates, not defense obligations).
```

## 2026-07-05 CC pre-launch amendments to the R21 spec (advice on the R21 decision)

Modification: actor CC (Research Copilot/Architect-advisory); authority:
user request ("advice about my decision in R21"); affected: R21 spec
(amended in place), this ledger; status: accepted (spec is CC-authored);
Codex applies before launch.

```text
A1 BLOCKING FIX: K_team 12 -> 48. Atomic reassignment makes K_team the
   effective max lifetime; K_team=12 truncated candidates 13/24 EVERY
   time -> artificial duration collapse indistinguishable from the R16.5
   pathology in the logs. Rule: K_team >= 2x max candidate. Log truncation
   per duration bucket (also distinguishes the two 160k failure modes:
   flat disc_acc from too-few-Z-samples vs dead differentiation).
A2 EVIDENCE FIX: team_disc_coef 0.1 -> 0.05. The R16.5 dose-response
   (0.1 collapses duration entropy, 0.05 self-sustains) postdates the
   spec; total intrinsic pressure on the S-base must not triple. Watch
   COMBINED reward/env ratio in [0.05, 0.5].
A3 INSURANCE: head-generic entropy-floor flag for pi_Z, default-off,
   Z-usage entropy logged with standard alarms from day one.
A4 OUTCOME MAP (160k team_disc_acc): gradual climb = catching -> 320k;
   flat = check per-bucket truncation + Z-sample count before declaring
   dead; instant ~1.0 = leak audit on q_D inputs first.
DECISION READ: R21 confidence 65% -> ~70% with A1/A2 applied; R19's
   mechanism-negative removed the rival explanation, and the S-base gives
   the engine a non-decaying platform. Asymmetry note: under the
   dissociation structure, even a clean R21 failure is a publishable
   finding about commitment under asynchrony.
```

## 2026-07-05 CC post-batch read: S-base decision, R19 verdict, v6 status box added

Modification: actor CC (Research Copilot/Reviewer); authority: user request
("check memory, give suggestions"); affected: ALGORITHM_DESCRIPTION_v6.md
(status box added per Codex condition), this ledger; status: implemented.

Key reads accepted from Codex's analysis, with CC additions:
```text
1. R16.5 pair = a DOSE-RESPONSE HINT: intrinsic coef 0.1 -> permanent floor
   + ratio pathology (kill_triggered=2); coef 0.05 -> self-sustaining
   entropy (floor_active=0) + higher reward (71.7). The intrinsic scale
   itself drives duration collapse. DECISION PROPOSED: coef005 arm =
   canonical stabilized base (S-base) for R21; resolve the 64env-vs-16env
   matched-control wrinkle BEFORE launch (local coef005 rerun as control,
   or R21 at 64env on the freed cloud slot).
2. coverage_eq1 = 0.0757: first nonzero parity-metric read in project
   history. Meaning unknowable without the HMASD current-env baseline —
   STILL absent from the dashboard after three blocking flags; the cloud
   slot is now free; launch it today (2 seeds).
3. R19 mechanism-negative is DIAGNOSED (R15 data-hunger caveat
   materialized: self_frac 0.93 starves the conditional; posterior learns
   noise). No further spend; negative wing of the dissociation. Caution:
   probe-vs-baseline task gap (0.115 vs 0.333, both reward-off) is
   seed-variance-sized — do not read as "heads hurt".
4. R21 launch today: probe -> reward; earliest tell = team_disc_acc shape
   at 160k (gradual climb = catching; instant ~1.0 = leak; flat = dead).
5. v6 promotion condition fulfilled: implementation/validation status box
   added distinguishing experiment-supported / locally-validated /
   mechanism-negative / theory-only. Awaiting user confirmation to promote.
```

## 2026-07-04 CC response to Gemini roadmap: two-tempo environment ACCEPTED with the design crux

Modification:
  actor/model: CC (Research Copilot); authority source: user-relayed Gemini
  proposal; status: accepted-with-corrections; affected: this ledger +
  future env spec (Codex implements after co-design)

Gemini proposal (roadmap + minimal two-tempo env for C2) ACCEPTED. Three
corrections:
```text
1. Do NOT pre-write the R19 ablation conclusion ("continuous projection
   can never beat discrete sampling") — R19 is a dissociation, not a
   designated loser; either outcome is a finding.
2. "90%" = confidence in WRITING C1/C3 into an architecture paper, not in
   proving C1 (evidence still zero until R21 reads). Keep separate.
3. Draft BOTH contribution sentences (async-headline vs hierarchy-headline);
   the two-tempo result decides which is defensible.
```

DESIGN CRUX (prevents spurious C2 falsification): with no cost to
re-deciding, full-sync k=1 dominates ANY two-tempo env (slow agent just
re-selects). The env must make temporal abstraction itself load-bearing:
DUAL FAILURE PRESSURE — slow agent: charge-and-fire, no intermediate
reward, interruption resets (k=1 fails by exploration collapse: ~10 chained
correct re-selections unrewarded; commitment = one decision); fast agent:
per-step moving target (k=10 fails reactivity); TEAM reward only, on
fire+intercept coincidence. Controls B/C/D + HMASD, capacity-matched,
10+ seeds (~50-step episodes cure the seed-1 disease).

MONEY FIGURE: parameterize tempo ratio (1:1, 1:2, 1:5, 1:10); prediction:
arms tie at 1:1, D - max(B,C) gap GROWS with heterogeneity. Dose-response
beats a single win — the mechanism responds to the exact variable the
thesis names.

Queue impact: none — env is design work (CPU-minutes per seed); entfloor /
HMASD baseline / R21 build proceed unchanged.

## 2026-07-04 CC stance clarification: R21 evidence-ranked ABOVE R19

Prompted by a fair user challenge ("you say R19 is valuable but my
correction seems suspicious"). For the record, by the evidence-hierarchy
rule (R-2):

```text
R21 (user's correction, team-intent restoration): evidence class (a) —
  HMASD published ablations. CC confidence ~65% to beat the stabilized
  base — the highest assigned to anything in this project. If only one of
  R21/R19 could be built, build R21.
R19 (transition residual): evidence class (c)+(d) — derivation + DADS
  analogy. Value is as a CONTROL: dissociation (commitment-specifically vs
  any-team-signal), Stage-2 churn precursor, near-zero marginal cost
  (already running). Not co-equal with R21.
"Override" / honesty-ledger labels on R21 are PROVENANCE (owner judgment
  vs gate-fired), not epistemic distrust — CC's earlier writing conflated
  the axes; corrected here.
Historical note: R21 is structurally Round 11's anchor recommendation
  (faithful cooperative-half transplant first) plus the async fast clock.
  The user's correction closes the loop the R12-R18 recognition-first arc
  opened — that arc yielded real assets (substrate gate, vacuity lemma,
  roster-docking) but its one cost was removing commitment, which R21
  reinstates.
```

## 2026-07-04 Canonical v6 description written (user-requested expansion)

Follow-up to the Research Copilot CHECK: the detailed restatement expanded
into `memory/ALGORITHM_DESCRIPTION_v6.md` (three-timescale hierarchy;
layer-by-layer; layer-matched pressure system; provided-vs-claimed split
with C4 marked evidence-unfunded). Awaiting user confirmation that it
matches intent; on confirmation it becomes the reference description and
the principles' opening should point to it.

## 2026-07-04 CC (Research Copilot) CHECK of the composite idea (v6)

Modification:
  actor/model: CC (Claude, Cowork); active role: Research Copilot
  authority source: user invocation "/research-copilot check my idea"
  affected files: cross_validation.md (this entry only)
  status: verdict logged; framing decision owned by user

Sharpened restatement (pending user confirmation): a THREE-TIMESCALE
HIERARCHY — recognition (continuous) / commitment (slow, synchronized,
sampled) / response (fast, async, sampled) — where each layer's intrinsic
pressure is determined by what the layer IS (vacuity: recognized layers pay
on the future; sampled layers pay on identifiability), interfaced by atomic
reassignment + docking.

Claim decomposition: C1 substrate VERIFIED (16env/N=4/seed1 only);
C2 individual engine WEAK; C3 team engine UNTESTED (external evidence
only); C4 async-lifetime benefit ZERO confirmatory reads in ~15 runs
(best: one seed-1 correlation at the 480k peak); C5 two-clock THEORY ONLY;
C6 parity bar itself UNVERIFIED (P1).

VERDICT: MODIFY — pursue composite; realign thesis emphasis. ~65% R21 stack
beats stabilized base; ~25-30% async-lifetime headline ever confirms on
existing scenes; ~80% the timescale-hierarchy framing is publishable given
the R19/R21 dissociation.
SOBERING: thesis claim C4 has 0 confirmations; coverage_eq1 = 0.0 in every
run ever, peak included.
BLOCKING: P1 (HMASD current-env re-verification, 1-2 GPU-days) is named
BLOCKING from now on — deferred >= 4 times while being load-bearing for
both the parity bar and R21's justification.
UNREQUESTED ALTERNATIVE (ranked ahead of current framing on
publishability today): pivot the paper spine to the timescale hierarchy
(vacuity as organizing theorem, atomic-vs-docked switching, R19/R21
dissociation as empirical centerpiece); demote async lifetimes to a
provided capability pending the two-tempo mechanism scene. User decision.

## Round 21 (2026-07-04) — Team-Intent Restoration: two-clock hierarchy (USER OVERRIDE + CC design)

Modification:
  changed_at: 2026-07-04
  actor/model: CC (Claude, Cowork), design under USER ARCHITECT OVERRIDE
  active role: Architect+Reviewer (authority source: user instruction —
    "bring the autoregressive team skill back, keep async low-level skills;
    highest priority; no ablation")
  reason: user judged HMASD's proven team-skill architecture must return;
    R20 D2 (team_bridge_none ablation) DROPPED, D3 (kappa* deferral)
    DISSOLVED into an immediate build
  affected files: cross_validation.md, IMPLEMENTATION_PLAN.md,
    ATTENTION_POINTER.md, ALGORITHM_PRINCIPLES.md,
    docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md (spec)
  linked principle/plan: R18.1 atomic variation; R18.2 kappa* form;
    R19 dual-engine; R11.3 bootstrap scale; channel-pressure rule
  linked experiment: EXP-2026070X-r21-team-intent (to be created pre-launch)
  validation performed: design-level consistency check against R10-R19;
    no training code touched
  follow-up owner: Codex (build now, default-off, parallel to entfloor)
  status: accepted (user-directed)

### R21.0 The design in one screen

```text
TWO-CLOCK HIERARCHY:
  slow synchronized clock: Z_m ~ pi_Z(Z | c, omega), held K_team=12 checks;
    at each Z boundary, ATOMIC full-team AR reassignment
    z_i | Z, c, o_i, z_{<i}   (R18.1: commitment buys atomic switching)
  fast asynchronous clock (unchanged): individual renewals dock against the
    current Z + standing roster:  z_i | Z, c, o_i, roster
  HMASD = special case (K_team=1, all lifetimes = k).

ENGINE SHIPS IN THE SAME BUILD (channel-pressure rule; three decorative-
channel autopsies say never defer this):
  r_i += lambda_D * clip(log q_D(Z|s_{t+1}) - log p_hat(Z), +-2), low-level,
  per-step, bootstrap scale 0.1, warmup 20k — NON-VACUOUS because Z is
  SAMPLED (the vacuity lemma delimits the layers: recognized substrate vs
  sampled intent). q_d gains Z conditioning: q_d(z_i|o', kappa, Z).

BYPRODUCT: R21 arm vs the recognition-only stabilized base IS the
commitment-vs-recognition decisive experiment (R14.0) on S7-S1 — the
mainline now answers it for free.
```

### R21.1 Honesty ledger

```text
- This reverses the R20 Architect gating (deceptive-axis trigger) by USER
  decision; recorded as an override, not a derived conclusion. The R18.3
  matrix prediction becomes falsifiable through this arm: if Z-restoration
  wins on S7-S1, the win is attributed to the restored EXPLORATION ENGINE
  (consistent with R18.3's "parity comes from the bootstrap"), not to
  symmetry-breaking commitment; the matrix stands unless deceptive-cell
  evidence contradicts it.
- One structural variable (the whole Z system) rather than strict
  single-variable: accepted deviation, justified by the channel-pressure
  rule — intent without pressure would be decorative channel #4.
- a2_plus_t DEMOTED to complementary (heads stay built and available);
  team_bridge_none DROPPED per user.
- Sequencing: build NOW; LAUNCH only on the stabilized entfloor base after
  its 480k read — restoring an engine on a decaying base reads nothing.
```

Spec (single source of truth):
docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md


## 2026-07-04 CC (Reviewer+Architect) response to Codex Team-bridge assessment: Round 20 disposition

Modification:
  changed_at: 2026-07-04
  actor/model: CC (Claude, Cowork)
  active role: Reviewer + Architect (authority source: user instruction this
    turn; AGENT_ROLES.md boundaries respected — no implementation code touched)
  reason: Codex code-audit of the Team bridge (user-relayed) required a
    binding module-boundary decision
  affected files: cross_validation.md, ALGORITHM_PRINCIPLES.md,
    IMPLEMENTATION_PLAN.md, ATTENTION_POINTER.md
  linked principle/plan: R18.2 kappa* canonical form; R18.3 task matrix;
    channel-pressure rule; R16.5 in-flight cycle
  linked experiment: team_bridge_none ablation (queued, post-a2_plus_t)
  validation performed: ledger consistency check (no contradiction with
    R10-R19); config `team_bridge_type=none` verified to exist
  follow-up owner: Codex (D2 ablation when triggered); Architect (D3 timing)
  status: accepted

REVIEWER VERDICT on Codex's assessment: ACCEPT diagnosis; one context
correction; one recommendation BLOCKED.

```text
ACCEPTED: g_tau ~ pi_g(g|c_tau) sits BESIDE the assignment path, never
  upstream — it was never HMASD's Z. The user's sensed thought/implementation
  deviation is real and now precisely characterized. NEW content = the
  three-role unbundling: (1) discrete bottleneck of c (redundant, possibly
  noise-adding since the high level already sees c); (2) quasi-HMASD team
  skill (unconstrained, hence decorative — matches logged g_itv/g_skill_mi);
  (3) low-level critic conditioning (cheap, untested).
CONTEXT CORRECTION: the "two-layer reorganization" recommendation re-derives
  R18.2 (kappa* is the canonical coordination-intent form) and must inherit
  R18.3's gating (intent layer load-bearing only on the deceptive axis; NOT
  on S7-S1). Codex's three influence tests are correct and map to existing
  machinery (g-intervention KL; R19 transition heads).
BLOCKED: "refactor g into an HMASD-style team intent" NOW = building kappa*
  early, off-axis, and pressure-less -> the fourth decorative channel
  (g -> AR prefix -> roster -> kappa*). Channel-pressure rule forbids it.
```

ARCHITECT DISPOSITION (binding):

```text
D1 FREEZE: g_tau DEPRECATED-IN-PLACE. No new mechanism may condition on g.
   No code change now (one-variable discipline; R16.5 cycle in flight).
D2 ABLATION QUEUED: post-R16.5/a2_plus_t, one-variable `team_bridge_none`
   on the stabilized base (team_bridge_type=none exists in config).
   Tests all three unbundled roles incl. critic conditioning.
   Read: no regression expected; removal HELPING confirms noise (case 1).
D3 RESERVATION: coordination-intent slot belongs to kappa* (R18.2), gated
   on the deceptive axis (R18.3). Build clean when triggered: sampled
   pi(kappa*|kappa,c), UPSTREAM of AR/roster assignment, shipped WITH
   pressure (commitment progress + kappa*-conditioned transition heads),
   judged by Codex's three influence tests. Never refactor g into it;
   delete the bridge when kappa* lands.
D4 VOCABULARY: "situation substrate (c/omega/kappa)" vs "coordination
   intent (kappa*)"; "team bridge / g_tau" is legacy terminology.
```

## 2026-07-04 CC FINAL guard-mode spec issued (supersedes Gemini v1/v2)

Gemini's v2 incorporated both prior additions but left ONE real gap and two
minor ones; per user instruction CC wrote the final version:

```text
docs/superpowers/plans/2026-07-04-r16-5-guard-mode-final.md   (WINS conflicts)
```

The gap: the runner script was missing from Proposed Changes — the
pre-registered launch goes through run_r16_a2r_overnight_local_cuda.ps1, and
without the entfloor arm passing --reward_ratio_guard_mode warn, the run
silently launches in kill mode: the exact second-variable confound
Condition 1 exists to prevent, failing invisibly. Final spec wires the flag
into the runner arm, echoes it in the per-arm banner, and adds a LAUNCH
PRECONDITION: paste the -DryRun output showing the warn flag into the
ExpRecord entry before launch.
Minor fixes: warn-mode counters accumulate and never reset after a trigger
(pathology DURATION, not occurrence; kill_triggered is a cumulative count);
automated tests now cover both modes, not just the default value.

LAUNCH GO stands, conditional on the final spec's checklist.

## 2026-07-04 CC review of the Gemini warn-mode spec + ExpRecord taxonomy fix; LAUNCH GO

Per the implementation-authority rule, the warn-mode flag spec got its
(lightweight) ledger review — no smallness exemption. Verdict: APPROVED with
two one-line additions:

```text
1. In warn mode, the over05 counter and kill_triggered metrics MUST still
   compute and log (the read needs to know what WOULD have killed).
2. reward_ratio_guard_mode is recorded in the run manifest / start line so
   the deviation is visible inside the run's own log, not only in ExpRecord.
```

ExpRecord taxonomy correction (CC, applied directly): Gemini's edit had
classified "floor permanently active late" as FAIL. Corrected to the Q2
resolution's four-way taxonomy: PASS-CLEAN (floor transient) /
PASS-SCAFFOLDED (floor persistent; parity claims valid, mechanism claims
qualified per R10.2-F; STILL the stabilized base) / PARTIAL (entropy healthy,
task decays -> anneal, then bootstrap-coef) / FAIL (entropy collapses with
floor on after one bounded retry). Warn-mode guard note added: the guard
flags the read; it cannot stop this run.

LAUNCH GO: with the two additions folded in, Codex may add the warn-mode
flag, run the tiny forced-trigger smoke, and launch
r16_5_a2r_roster_coef01_entfloor + the P2 four-cell eval per the
pre-registered entry. Next decision point: the entfloor 480k read.

## 2026-07-04 CC review of the R16.5 P1/P2 implementation (Codex submission)

Verdict: APPROVED TO LAUNCH with three binding conditions. Answers to
Codex's three review-focus questions included.

```text
Q1 SINGLE-VARIABLE? The floor is; the RUN as planned is not: the reference
   run (run_20260704_142053) executed WITHOUT the new ratio guard and
   breached 0.53/0.47 at 728k/776k. If the sustained->0.5 kill fires on the
   entfloor rerun, the comparison dies where the reference survived —
   second-variable confound that also destroys the >=80%-of-peak gate.
   CONDITION 1: guard in WARN-ONLY mode for this comparison run
   (--reward_ratio_guard_mode warn|kill); kill = default for future runs.

Q2 CAN THE FLOOR MASK COLLAPSE? Yes — and R10.2-F anticipated it ("duration
   entropy: annealed bonus only, NEVER a heterogeneity reward"; a
   conditional floor is persistent pressure). Resolution = honesty in the
   read, not design change.
   CONDITION 3: duration_entropy_floor_active trajectory JOINS THE GATE.
     transient activation then self-sustaining entropy = fixable
       optimization artifact (clean win);
     permanently active late = diversity is SCAFFOLDED: performance/parity
       claims remain valid; mechanism claims about emergent lifetime
       heterogeneity must be qualified as floor-supported — an honest
       partial falsification per R10.2-F, recorded as such.
   Read lifetime_heterogeneity + duration_agent_mi alongside (usage entropy
   can be held up while the policy functionally commits per-context).

Q3 P2 SUFFICIENT? Directionally yes, statistically thin: 20 bimodal
   episodes/cell. Report per-episode distributions, raise to 40/cell if
   cheap, and CHECK eval horizon/structure matches training rollouts before
   interpreting (divergence could be horizon-shaped, not mode-shaped).

CONDITION 2: pre-register EXP coef01-entfloor in ExpRecord BEFORE launch
   (Codex's gate list approved, incl. the duration_usage_max_frac addition)
   + one bounded-retry rule: if usage entropy collapses WITH the floor on,
   ONE coef adjustment (0.05 -> 0.1), then pivot. No silent sweeps.

Non-blocking notes: bang-bang threshold — if floor_active oscillates around
0.8, move to gap-proportional coef in a follow-up; decision-branch fallback
order (anneal -> smdp_bootstrap_coef) matches the pre-registered sequence.
```

## 2026-07-04 CC FORENSIC READ of the coef01 480k peak/crash (executed, data below)

Source: logs/ha_ctse_r16_a2r_overnight_local_cuda/run_20260704_142053/seed1/
a2r_roster_reward_coef01/metrics/train_updates.csv (120 updates, 960k).
Read directly by CC (analysis only). Verdict on Gemini's SMDP-confound
hypothesis: PARTIALLY confirmed; the dominant signature is different.

```text
trajectory (48k sampling; eval peak at 480k):
  duration_usage_max_frac 0.28 -> 0.82   (collapse CONFIRMED)
  segment_length_mean     104  -> 162    (rising, but toward the 13-bucket,
                                          NOT the maximal 24/240 bucket)
  high_bootstrap_contribution ~0.2-0.34 THROUGHOUT (0.25 damping held;
                                          no runaway gamma^T*V farming)
  high_entropy (all heads)  3.83 -> 2.54 (monotonic decay from ~480k)
  lifetime_heterogeneity    0.39 -> 0.26
  renewal_agents_mean       1.4  -> 2.5  (renewals SYNCHRONIZING as
                                          diversity dies)
  proto_disc_reward_env_ratio breached the [0.05,0.50] band twice in the
    decay phase (0.53@728k, 0.47@776k) without tripping the >1.0 kill
  TRAIN/EVAL DIVERGENCE: train env_reward_mean HIGHEST at the end
    (0.17-0.19 @ 920-960k) while eval collapsed to coverage 0.08 —
    entropy-collapsed policy performs under stochastic rollouts, brittle
    in evaluation mode.
```

Diagnosis: slow-burn HIGH-LEVEL ENTROPY COLLAPSE (duration head worst,
all heads affected) with renewal synchronization and eval brittleness as
co-symptoms; SMDP long-duration drift is a contributing current, not the
driver; bootstrap damping is NOT the failure point.

Positive corollary (correlational, seed 1): the 480k peak occurred WITH
duration entropy 0.90-0.95 and high lifetime heterogeneity; decay tracked
their collapse. First evidence in the project pointing IN FAVOR of
heterogeneous lifetimes on S7-S1.

Pre-registered prescriptions (for Codex, in priority order):
  1. Duration-entropy floor or scheduled high_entropy_coef (flat 0.01 is
     insufficient late); one-variable rerun of coef01 with the floor.
  2. Tighten the ratio kill: sustained > 0.5 (5 updates) joins the > 1.0
     instant kill.
  3. Stochastic-vs-deterministic eval on the 480k and 960k checkpoints to
     nail the divergence mechanism (small compute).
  4. Record the 480k checkpoint as current best-known S7-S1 configuration;
     "stabilize the peak" is now the concrete parity target (R18.3: the
     bootstrap is the only parity lever on this scene).
```

## 2026-07-04 CC cross-validation of the R16 four-arm readout

Verdict: Codex's headline (roster channel dead at kl_shuf 3e-6..6e-6; do not
conflate with R19) is ACCEPTED, with one interpretive sharpening that changes
roster mode's disposition, and one buried lede that outranks the headline.

```text
1. SHARPENING — the fused reward DISINCENTIVIZES roster use: the
   coordinator-residual's -log pi_h half pays for being unpredictable to the
   null; a head that reads the roster to sharpen assignments lowers its own
   reward. The entropy half fights the coordination half. In HMASD,
   complementarity was driven by task advantage, not the intrinsic term.
   => NO arm yet run contained an objective REQUIRING roster reading.
   Channel-pressure lesson recursion #3 (g -> AR prefix -> roster).
   The first requiring objective is R19's team term (xi-composition is what
   it pays on).
2. DISPOSITION — do NOT drop sequential assignment: R16.3 conjuncts unmet
   ("no task benefit vs A2" NOT established: roster coef005 coverage 0.288
   vs same-check 0.117, unmatched steps, seed 1). Roster gate RE-REGISTERS
   inside the a2_plus_t batch: re-read roster_kl_shuf with the team term
   live; if still dead there, drop per R16.3 for real.
3. BURIED LEDE — the 480k peak/crash in local a2r_roster_reward_coef01:
   reward 78.14 / coverage 0.345 / backhaul 0.388 at 480k = BEST NUMBERS
   EVER LOGGED in this project, then collapse to 20.08/0.080 at 960k,
   co-occurring with duration_entropy collapse to 0.467 (vs 0.95+ elsewhere).
   MANDATORY zero-compute forensic read before/alongside R19 launch:
   trajectories 320k-960k of duration/skill entropy, proto_reward_env_ratio,
   null-logp, segment_length; eval the 480k checkpoint if retained.
   If lifetime-collapse-driven: entropy floor / reward anneal are cheap
   fixes, and STABILIZING THE PEAK may be worth more for S7-S1 parity than
   any new mechanism (R18.3: the bootstrap is the only parity lever there).
4. TRIGGER — the same-check arm's profile (proto_resid 0.0027, weak task,
   reward on) is effectively the OUT-OF-GAS signature; a2_plus_t launch is
   declared triggered via the "user decision after A2 read" clause (the
   sweep was not the pre-registered matched-steps A2 — record the
   deviation honestly).
5. ENDORSED: narrow coef005 seed-2 as the only further R16 spend; R19 next
   batch; no broad R16 sweeps.
```

## 2026-07-04 Codex R16 four-arm experiment readout for external review

Status: R16 roster-docking seed-1 read is weak/negative; R19 is explicitly the
next batch and must not be mixed into this result.

Reviewer summary:

```text
Question:
  Did R16 roster-docking make asynchronous sequential assignment non-decorative?

Answer from current data:
  No.  Across local coef=0.1 and downloaded dist arms, the content-use metric
  `roster_kl_shuf` / `roster_ar_kl_shuffled` remains around 0.000003-0.000006,
  far below the 0.02 alive threshold and below the <0.01 fail band.

Implication:
  R16 does not currently rescue HMASD-style sequential complementarity under
  asynchronous skill lifetimes.  If more confirmation is desired, run only a
  narrow coef=0.05 seed-2 check.  Do not spend another broad R16 sweep.  Keep
  R19 team-transition as the next-batch experiment, not as part of this read.
```

Key data:

```text
local a2r_roster_reward_coef01, 16env, completed 960k:
  final eval 960k: reward=20.08, coverage=0.080, throughput=6.55,
    backhaul_frac=0.210, zero_throughput_ep_frac=0.75.
  best observed eval 480k: reward=78.14, coverage=0.345, throughput=22.02,
    backhaul_frac=0.388.
  final update: proto_acc=0.472, roster_kl_shuf=0.000006, sel_def=0.0018,
    proto_resid=0.1358, proto_reward=0.0136, credit_recover=0.121,
    credit_bh_frac=0.508, duration_entropy=0.467.

dist a2r_roster_coef005, 64env, reached 928k:
  latest eval 800k: reward=40.20, coverage=0.288, throughput=6.39,
    backhaul_frac=0.341, zero_throughput_ep_frac=0.60.
  last10: roster_kl_shuf=0.000003, sel_def=-0.0034, proto_resid=0.0116,
    credit_recover=0.022, credit_bh_frac=0.304, duration_entropy=0.956.

dist a2_samecheck_reward, 64env, reached 608k:
  latest eval 480k: reward=23.87, coverage=0.117, throughput=5.73,
    backhaul_frac=0.270, zero_throughput_ep_frac=0.60.
  last10: proto_ar_kl ~= 0, roster_kl_shuf=0, sel_def=0,
    proto_resid=0.0027, credit_recover=0.010, credit_bh_frac=0.262,
    duration_entropy=0.984.

dist a1r_roster_probe, 64env, reached 640k:
  latest eval 480k: reward=29.90, coverage=0.155, throughput=3.07,
    backhaul_frac=0.311, zero_throughput_ep_frac=0.60.
  last10: roster_kl_shuf=0.000004, sel_def=0.0011, proto_resid=-0.0026,
    proto_reward=0, credit_recover=0.015, credit_bh_frac=0.263,
    duration_entropy=0.991.
```

Codex response:

```text
Status: R16 roster-docking is not promoted from seed 1.

Accepted interpretation:
  The implementation worked and logged the required diagnostics; the channel
  simply did not become content-sensitive.  Lower reward coefficient is safer
  and may be the only R16 seed-2 worth checking, but it still does not pass the
  mechanism gate.

Next:
  Keep R19 as next batch.  Do not cite R16 as evidence that the team-transition
  residual works or fails; it is a different mechanism.
```

---

## 2026-07-04 Codex R19 team-transition implementation receipt

Status: IMPLEMENTED, locally verified, and still EXPERIMENT-TRIGGER-BLOCKED.

Response to the accepted CC final R19 plan:

```text
Implemented:
  - clean module `ha_ctse_process/situation_transition.py`;
  - `SituationTransitionPredictor` with prior/posterior heads;
  - own Adam optimizer and checkpoint state;
  - input boundary: kappa + permutation-invariant active-skill count vector xi;
  - detached head inputs and no-grad reward computation;
  - missing-kappa interval drop + `team_transition_missing_frac`;
  - current-rollout closed intervals only; final open interval dropped;
  - self-transition inclusion and split metrics;
  - high-level-only segment reward accumulation;
  - probe/reward flag split, default-off config/CLI/manifest fields;
  - CSV/TensorBoard/console/plot metrics under `team_transition_*`;
  - `a2_plus_t_probe` and `a2_plus_t` runner arms.
```

Validation:

```text
pytest tests\r19_team_transition_test.py -q
  -> 6 passed
pytest tests\r14_prototype_response_test.py -q
  -> 13 passed
AST compile for touched HA-CTSE files
  -> ast_compile_ok
run_r15_stage1_local_cuda.ps1 -Experiments a2_plus_t_probe,a2_plus_t -DryRun
  -> passed
Tiny reward-on smoke
  -> completed; `team_t_samples`, `team_t_rew`, and `team_t_ratio` logged
Checkpoint save/load/eval smoke
  -> passed
```

Launch status:

```text
Do not launch a2_plus_t by default. It remains trigger-blocked exactly as
pre-registered in EXP-20260704-a2-plus-t: run only if the A2 outcome matrix
fires the OUT-OF-GAS branch or the user explicitly chooses it after the A2
320k read.
```

---

## 2026-07-04 Codex R16 roster-docking implementation receipt

Status: IMPLEMENTED and locally verified.

Response to the accepted Round 16 / CC guard list:

```text
G1 roster snapshot:
  Implemented. Segment now stores renewal-time active skill ids, skill ages,
  and active masks. High-level PPO update/evaluation rebuilds the AR prefix
  from the stored Segment snapshot.

G2 full-sync special case:
  Implemented at prefix-construction level. When no previous active roster is
  available and renewers are processed sequentially, roster mode exposes the
  earlier newly sampled skills through the aggregate prefix, reducing to the
  same-check/HMASD AR special case.

G3 two roster nulls:
  Implemented. Logs both `roster_ar_kl_zeroed` and the primary
  `roster_ar_kl_shuffled`.

G4 skill ages:
  Implemented. Main roster prefix includes per-agent active-skill slots and
  per-agent age slots; skill-only roster is not the main path.

G5 independence-corrected anti-duplication:
  Implemented. Logs `selection_independence_deficit` against a matched
  marginal null rather than using raw same-skill overlap.
```

Validation:

```text
python -m pytest tests\r14_prototype_response_test.py -q
  -> 13 passed, 1 warning.
AST parse touched HA-CTSE files
  -> ast_ok 6.
SB3-env train help
  -> `--ar_prefix_mode {same_check,roster}` is exposed.
Tiny roster-mode smoke train
  -> completed one update and emitted roster diagnostics in log/CSV.
```

Next recommended read:

```text
Run A2r = A2 `s1_reward` + `--ar_prefix_mode roster`.
Judge `roster_ar_kl_shuffled`, `selection_independence_deficit`, reward-scale
guards, entropy health, and task metrics. Do not treat same-check A2 as the
final async sequential-assignment test.
```

## 2026-07-04 CC FINAL implementation plan issued: R19 team-transition heads

Status: ISSUED and BINDING. Full plan (single source of truth for Codex):

```text
docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md
```

Supersession chain (for the record): Gemini plan v1 -> CC six amendments ->
Gemini v2 -> CC approval + three fold-ins -> CC three completion notes ->
THIS consolidated final plan. Where any prior document differs, the final
plan wins. Resolution order inside the plan: plan -> Round 19 ledger ->
R15 derivation doc §5 -> ask, do not guess.

Content digest (what the final plan contains beyond the v2 entry):

```text
- All v2 items: clean module situation_transition.py; own optimizer +
  detached inputs + no_grad reward; probe/reward flag split; warmup 20k /
  clip 2.0 applied at injection; full metric list incl. split residuals,
  reward_env_ratio, and corr(team reward, renewal rate); temporal alignment
  (kappa_tau, xi_tau -> kappa_{tau+1}); both verification tests.
- The three completion notes as binding text: HIGH-LEVEL-ONLY injection;
  xi = active-skill count vector (ages = later ablation); coef 0.05 pinned.
- FOUR details pinned for the first time in any document:
  1. SEGMENT/INTERVAL granularity: high-level decisions are segments
     spanning multiple check intervals; per-interval clipped residuals are
     ACCUMULATED into segment returns via the existing per-segment reward
     pathway (legacy process-reward guard fields stay 0; team contribution
     logged separately).
  2. MISSING-KAPPA handling: intervals with kappa = -1 are DROPPED (not
     mapped to a class); team_transition_missing_frac logged.
  3. TASK GATE IS IMPROVEMENT, NOT NON-REGRESSION: a2_plus_t exists to fix
     the exploration deficit; neutrality vs A2 is a FAIL; stop rule routes
     to the R18.3 matrix read, never to a coefficient sweep.
  4. CHANNEL-PRESSURE COMPLIANCE BY LABELING: probe-mode heads are
     explicitly "decorative until a2_plus_t reward-on" — their reward-off
     silence is by design, not a failure signal.
- Experiment pre-registration mirrored to ExpRecord as EXP-20260704-a2-plus-t
  (trigger-blocked on the A2 outcome matrix OUT-OF-GAS branch or explicit
  user decision after the A2 320k read).
```

### VERBATIM ARCHIVAL COPY (recorded 2026-07-04 at issuance, user-requested)

The live/authoritative version remains
`docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md`; if the doc
is later amended, the doc wins and the amendment must be logged as a new
ledger entry. Full text as issued:

````markdown
# R19 Team-Transition Residual Heads — FINAL Implementation Plan (for Codex)

Author: CC (Claude, cross-validation) — consolidates the Gemini v2 plan, the
six CC amendments, the three approval fold-ins, and the three completion
notes into one self-sufficient reference. Supersedes the v2 ledger entry as
the implementation source of truth; where any prior document differs, THIS
plan wins.
Date: 2026-07-04
Source contracts: `memory/cross_validation.md` Round 19 (R19.0-R19.4),
Round 18 (R18.3 task matrix), R15 derivation doc §5 (team term).
Implementer: Codex (exclusive writer of training code, per the
implementation-authority rule in ATTENTION_POINTER).

## Purpose

Implement the team engine: DADS-style situation-transition residual
`log q(kappa'|kappa, xi) - log q(kappa'|kappa)`, the structural replacement
for HMASD's team discriminator reward that the vacuity lemma killed. Runs as
the `a2_plus_t` arm. Restores dual-engine intrinsic pressure: individual =
role diversity (A2), team = situation steering INCLUDING stabilization
(this plan).

## Non-goals

- No changes to the A2 path, roster mode, hazard/guard code, or legacy
  process/topology/transition reward paths.
- No commitment layer (kappa*), no coverage bonus — later stages.
- No communication/backhaul/coverage fields anywhere (inputs are kappa and
  skill counts only, enforced by unit test).
- Never low-level injection (see §Injection — correctness-critical).

## Current-code facts to respect

1. kappa is per-env from `situation_substrate.py::assign_kappa_from_omega`,
   argmax over omega -> classes {0..N-1} with `missing_kappa = -1` possible.
   N = opt_num_prototypes = 4 (PINNED; substrate gate validity).
2. High-level decisions are SEGMENTS (skill lifetimes spanning multiple
   check intervals); kappa transitions occur per CHECK INTERVAL. The reward
   therefore accumulates per-interval residuals into segment returns
   (see §Injection).
3. `update_high_from_segments(segments, process_rewards, ...)` already
   accepts a per-segment reward array — the tested injection pathway.
   Legacy process-reward fields must REMAIN 0 in this arm; the team
   contribution gets its own fields.
4. Active skills per (env, agent) are tracked in `self.active_skills`;
   xi is computable at every check from it.
5. Do not import anything from the retired `process_posterior.py` path.

## Module: `ha_ctse_process/situation_transition.py` (NEW, clean)

```text
class SituationTransitionPredictor(nn.Module):
    __init__(num_situations, n_skills, hidden_dim=128)
      kappa_embedding: Embedding(num_situations, hidden_dim)
      prior_head:      MLP(kappa_emb -> num_situations logits)
      posterior_head:  MLP([kappa_emb, xi] -> num_situations logits)

    losses(kappa, xi, kappa_next) -> dict
      # ALL inputs .detach()ed / constructed from data, never from live graph
      CE(posterior) and CE(prior) on kappa_next targets
      per-sample log_q, log_p; mi = log_q - log_p
      split: mi_on_self (kappa_next == kappa), mi_on_change (else)

    reward(kappa, xi, kappa_next, coef, clip) -> per-interval scalar array
      # computed strictly under torch.no_grad()
      r_tau = coef * clamp(log_q - log_p, -clip, +clip)
```

Contract points:
- xi_tau = permutation-invariant ACTIVE-SKILL COUNT VECTOR, n_skills dims,
  raw counts (float), over all agents during interval tau. Ages are a later
  optional ablation, NOT the default encoding.
- Targets: per check interval tau, inputs (kappa_tau, xi_tau), target
  kappa_{tau+1}. ALL intervals count, INCLUDING self-transitions
  (kappa_{tau+1} == kappa_tau) — stabilization must pay (R19.2).
- missing kappa (-1): DROP intervals where kappa_tau or kappa_{tau+1} is
  missing; log `team_transition_missing_frac`. Do not map missing to a class.
- On-policy: heads train on the CURRENT rollout's closed intervals only;
  the final unclosed interval of each env is dropped at the PPO boundary.
- Optimizer: OWN Adam at `team_transition_lr`. Head parameters never enter
  the high-level policy optimizer. CE trains only the heads; the reward
  trains only the policy (g-revival precision rule).

## Config (`config.py`, all default-off/inert)

```text
enable_team_transition_probe = False    # train heads + metrics, NO injection
enable_team_transition_reward = False   # requires probe flag on
team_transition_coef = 0.05             # smallest-first (R19.4); a2_plus_t pinned
team_transition_clip = 2.0              # applied AT injection, before coef? NO:
                                        # r = coef * clip(residual, +-2.0)
team_transition_warmup_steps = 20000    # gates REWARD only; probe trains from 0
team_transition_lr = 5e-4
team_transition_hidden_dim = 128
```

CLI in `train.py`: `--enable_team_transition_probe`,
`--enable_team_transition_reward`, `--team_transition_coef/clip/warmup_steps`.
Manifest + start-line entries per convention.

## Injection (CORRECTNESS-CRITICAL)

```text
LEVEL: HIGH-LEVEL ONLY. Per-interval clipped residuals are accumulated over
each segment's constituent check intervals and added to that segment's
return via the existing per-segment reward pathway (alongside env return).
The residual NEVER enters the low-level per-step reward — the P1
signed-low-only lesson. Gated by: probe flag AND reward flag AND
total_steps >= warmup.
Legacy process-reward guard fields stay 0.0; team contribution is logged
separately (fields below) so reward-purity audits still work per-channel.
```

## Rollout data collection

During rollout, per env per check interval: record (kappa_tau, xi_tau) and
close with kappa_{tau+1} at the next check. Attribute each closed interval
to the enclosing segments per agent for reward accumulation. Buffers cleared
at the update boundary (on-policy contract).

## Metrics (CSV via UPDATE_FIELDS + TensorBoard TeamTransition/* + console)

```text
team_transition_active, team_transition_samples
team_transition_loss (posterior CE), team_transition_prior_loss
team_transition_mi_mean, team_transition_mi_on_self, team_transition_mi_on_change
team_transition_self_frac          # expect high given dwell ~8; verifies R19.2 regime
team_transition_missing_frac
team_transition_reward_high_mean
team_transition_reward_applied_steps   # assertable 0 when reward flag off/warmup
team_transition_reward_env_ratio       # |team reward| / |env return|, P4-1b lesson
team_transition_reward_renewal_corr    # Pearson across envs within the update:
                                       # per-env summed team reward vs per-env
                                       # renewal count. CHURN PRECURSOR (R19.3);
                                       # informational now, MANDATORY gate input
                                       # before Stage-2 hazard goes live.
```

## Experiment pre-registration (create ExpRecord entry BEFORE launch)

`EXP-2026070X-a2-plus-t`, local CUDA, settings identical to A2
(16 env, 320k, S7-S1, seed 1 then 2). ONE variable vs A2.

```text
TRIGGER: the A2 outcome-matrix OUT-OF-GAS branch fires, OR user decision
  after the A2 320k read. Do NOT launch before A2 completes.
ARM: a2_plus_t = A2 config + enable_team_transition_probe
  + enable_team_transition_reward (coef 0.05, clip 2.0, warmup 20k).
PROBE-FIRST OPTION: if A2's read is ambiguous, a probe-only arm
  (heads on, reward off) may run first to verify mi_mean > 0 exists to
  inject; pre-register it as a2_plus_t_probe if used.

GATES (a2_plus_t vs A2, matched steps, last-third means + 320k eval):
  mechanism: team_transition_mi_mean > 0 sustained; self_frac consistent
    with dwell (0.6-0.95); reward_env_ratio in [0.05, 0.5] post-warmup.
  task: coverage and zero_throughput_ep_frac improve vs A2 (this arm exists
    to fix the exploration deficit — neutrality is NOT a pass);
    reward_std/mean not worse than 1.15x A2.
RUNTIME KILLS:
  reward_env_ratio > 1.0 for 5 consecutive post-warmup updates;
  160k eval zero_throughput_ep_frac > A2 + 0.15.
STOP RULE:
  if a2_plus_t fails the task gate on 2 seeds while mechanism metrics are
  healthy, the exploration deficit is not situation-steering-shaped;
  do NOT sweep coef — escalate to the R18.3 matrix read (S7-S1 may require
  kappa*-style atomic commitment even in the coverage-bound corner, or the
  substrate's kappa classes are too coarse at N=4).
CHURN PRECURSOR: team_transition_reward_renewal_corr is logged and reported
  but NOT a gate in this arm (no live hazard); it becomes a hard input to
  the Stage-2 go decision.
```

## Validation checklist (project convention)

```text
py_compile / AST parse on all touched files
unit tests (new file tests/r19_team_transition_test.py):
  - input boundary: heads consume kappa + skill counts ONLY
  - gradient separation BOTH directions (head step leaves policy params
    unchanged; policy step leaves head params unchanged)
  - reward guard: applied_steps == 0 when reward flag off OR warmup unmet
  - clip applied before coef scaling
  - missing-kappa intervals dropped, missing_frac logged
  - self/change split partitions correctly
  - unclosed final interval dropped at boundary
smoke: probe-on run with reward guards zero; CSV fields present
tiny train: reward-on with warmup=0; checkpoint save/load/resume with the
  new module (own optimizer state included in checkpoint)
runner: a2_plus_t arm added to scripts/run_r15_stage1_local_cuda.ps1
  (or sibling), -DryRun passes, timestamped log dirs
memory sync per LongTaskMemo after implementation
```

## Fidelity notes

- The probe-mode heads are observers: this channel is "decorative until
  a2_plus_t reward-on" BY DESIGN and labeled as such (channel-pressure rule
  satisfied via explicit labeling, not via emergence expectations).
- Never add a head predicting kappa from s (vacuity — trivially perfect,
  dead reward).
- If any ambiguity arises during implementation, the resolution order is:
  this plan -> Round 19 ledger -> R15 derivation doc §5 -> ask, do not guess.
````

## 2026-07-04 CC APPROVAL of the revised Gemini plan (v2) + implementation-authority rule

Revised plan incorporates all six amendments; APPROVED for Codex execution
with three fold-in notes (no further revision cycle needed):

```text
1. Apply team_transition_clip AT injection: coef * clip(log_q - log_p, +-2.0).
2. On-policy boundary: heads train from the current rollout only; unclosed
   intervals dropped at the PPO update boundary.
3. Full plumbing: metrics to train_updates.csv (UPDATE_FIELDS pattern) + TB
   + console, not TB alone; a2_plus_t ExpRecord entry created BEFORE launch.
```

Positive note: the v2 gradient-separation unit test (head update leaves
policy params unchanged, and vice versa) is stronger than requested — keep.

WORKFLOW RULE ADDED to ATTENTION_POINTER (user-approved): Codex is the
exclusive writer of training code; Gemini and other models produce plans
that route through CC ledger review before execution; CC reviews and does
not write training code.

## 2026-07-04 Gemini revised implementation plan (v2) for R19 team-transition heads

Status: SUPERSEDED as implementation reference by the CC final plan
`docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md` (consolidates
v2 + all amendments/completions + injection pathway details + a2_plus_t
pre-registration template). Codex implements from the final plan; this entry
is retained as review history.

Implementation Plan:
- **MODULE**: Create clean module `ha_ctse_process/situation_transition.py`, zero imports from the retired process_posterior path.
- **GRADIENT SEPARATION**: Heads get their own optimizer (`team_transition_lr`). Head inputs ($\kappa$, $\xi$) are `.detach()`ed. Reward is computed under `torch.no_grad()`. CE trains only the heads, reward trains only the policy path.
- **FLAG SPLIT**: `enable_team_transition_probe` (heads+metrics, no injection) vs `enable_team_transition_reward` (requires probe).
- **WARMUP/CLIP**: Added `team_transition_warmup_steps = 20000`, `team_transition_clip = 2.0`. Clip is applied AT injection: `coef * clip(log_q - log_p, +-2.0)`.
- **METRICS**: Added `team_transition_prior_loss`, `team_transition_reward_applied_steps` (assertable at 0 when off), `team_transition_reward_env_ratio`, `team_transition_self_frac`, split residual (`mi_on_self` vs `mi_on_change`), and `corr(team_transition_reward, renewal_rate)`. All metrics plumbed to CSV, TB, and console.
- **ALIGNMENT**: Trained on current rollout only (unclosed intervals dropped at PPO boundary). Per check interval $\tau$: inputs $\kappa_\tau + \xi_\tau$, target $\kappa_{\tau+1}$. All intervals included (self-transitions).
- **VERIFICATION**: Unit test asserting head inputs are $\kappa$ + skill counts ONLY. Gradient separation test asserting head updates leave policy params unchanged and vice versa.
- **EXP RECORD**: Pre-register the `a2_plus_t` runner arm in ExpRecord before launch.

CC completion note (2026-07-04, review of this ledger entry): the v2 entry is
faithful but the condensation dropped three contract details that make it
non-self-sufficient. Binding completions:

```text
1. INJECTION LEVEL (correctness-critical): HIGH-LEVEL ONLY — the clipped
   residual enters the interval/SMDP reward for the high-level update. It
   never enters the low-level per-step reward (the P1 signed-low-only
   lesson).
2. XI DEFINITION: xi_tau = permutation-invariant ACTIVE-SKILL COUNT VECTOR
   (n_skills dims) over agents during interval tau; ages are a later
   optional ablation, not the default encoding.
3. COEFFICIENT: team_transition_coef = 0.05 (smallest-first, R19.4); the
   a2_plus_t ExpRecord arm is pinned to it.
```

With these three completions the entry is APPROVED as the sole
implementation reference; Codex may execute against it without consulting
the chat history.

## 2026-07-04 CC review of the Gemini implementation plan for R19 team-transition heads

Verdict: skeleton correct (residual form, high-level injection,
self-transitions, xi count vector, coef 0.05 default-off); NOT
implementation-ready. Six required amendments, two correctness-critical:

```text
1. MODULE: not process_posterior.py (retired segment-posterior family; R14
   spec forbids extending legacy modules). New clean module
   situation_transition.py, zero imports from the retired path.
2. GRADIENT SEPARATION: heads get their OWN optimizer (team_transition_lr,
   prototype_disc_lr pattern); head inputs detached; reward computed under
   no_grad. CE trains only the heads; reward trains only the policy path
   (g-revival precision rule).
3. FLAG SPLIT: enable_team_transition_probe (heads+metrics, no injection)
   vs enable_team_transition_reward (requires probe); guard metric
   team_transition_reward_applied_steps assertable at 0 when off.
4. MISSING: team_transition_warmup_steps=20000, team_transition_clip=2.0
   (Stage-1 conventions; unclipped log-ratio can spike early).
5. METRICS: add prior_loss, reward_applied_steps, reward_env_ratio (P4-1b
   scale lesson), self_frac (verify R19.2 regime), SPLIT residual
   mi_on_self vs mi_on_change (churn precursor), and the R19.3-mandated
   corr(team_transition_reward, renewal_rate).
6. ALIGNMENT: per check interval tau: inputs kappa_tau + xi_tau, target
   kappa_{tau+1}; current rollout only; all intervals incl. self.
Minor: cited test file ha_ctse_test.py does not exist; plan omits the
a2_plus_t runner arm + ExpRecord launch entry; add a unit test asserting
head inputs are kappa + skill counts ONLY (comm-fields boundary by
construction).
```

## 2026-07-04 CC review of the Round 16 memory sync

Overall: PASS. Channel-pressure rule, roster principle with all four guards
(incl. shuffled null + ages), A2/A2r scoping, and pointer chain are
consistent. Three findings:

```text
F1 (SUBSTANTIVE, blocks A2r judgment): "anti-duplication movement" is in
   three stop rules but has NO defined metric anywhere — and with N=4 skills
   and 6 agents it has a cardinality trap: under independent uniform
   selection a renewer matches >=1 co-active teammate with prob
   ~ 1 - (3/4)^5 ~ 0.76, so a RAW duplication rate measures cardinality,
   not coordination. Required metric:
     selection_independence_deficit =
       observed co-active same-skill rate
       - same rate under an independence null with matched skill-usage
         marginals (shuffle teammates across timesteps).
   Judge A2r's anti-duplication conjunct on this deficit, with modest
   expected effect size at N=4. (Longer term this is another argument that
   coverage-of-prototypes, J4 tier 1, is the better-posed complementarity
   objective than pairwise non-duplication.)
F2 (wording drift): the falsification paragraph after the roster invariants
   in ALGORITHM_PRINCIPLES (~line 2261) still uses the pre-R15 null
   "p(z | situation)". Mainline null is the stored coordinator log pi_h;
   p(z|situation) applies only to the R15-P1 fallback. Codex to reword.
F3 (fixed by CC directly): IMPLEMENTATION_PLAN stop rule now says
   roster_ar_kl_shuffled (was missing the suffix). ExpRecord should also
   restate the >=0.02 success target on the shuffled variant next to the
   <0.01 failure bound.
```

Codex response:

```text
Status: ACCEPTED.

F1 response:
  Add `selection_independence_deficit` as the A2r anti-duplication metric:
    observed co-active same-skill rate
    - shuffled-teammate independence null with matched skill-usage marginals.
  Raw duplication rate is invalid at N=4 skills / 6 agents because independent
  uniform selection already matches at least one co-active teammate with high
  probability.  Desired anti-duplication is negative movement in this deficit
  relative to A2 / null, not merely a lower raw count.

F2 response:
  Reword the Round-14/R16 falsification paragraph in ALGORITHM_PRINCIPLES:
  mainline null is the stored coordinator log pi_h under the same renewal
  context/roster snapshot.  p(z|situation) is R15-P1 fallback only.

F3 response:
  ExpRecord now states the A2r success target on
  `roster_ar_kl_shuffled >= 0.02` and the failure bound
  `roster_ar_kl_shuffled < 0.01`.

Affected files:
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
```

## 2026-07-04 CC pre-implementation cautions for ar_prefix_mode=roster

Four bug-class guards to bake into the R16 Stage-1.5 implementation BEFORE
code is written (each maps to a failure shape this project has already paid
for once):

```text
1. ROSTER SNAPSHOT, NOT LIVE ROSTER (mask-before-sample class).
   The stored null log pi_h is computed against the roster AT THE RENEWAL
   INSTANT; store that snapshot (teammates' active skills + ages) in the
   segment. Update-time evaluate() must rebuild conditioning FROM THE
   SNAPSHOT, never from current state, or PPO old-logp consistency silently
   breaks. MANDATED UNIT TEST: recompute logp at update time from stored
   segment data == stored logp within fp tolerance.

2. WITHIN-CHECK ORDERING MAKES same_check A SPECIAL CASE.
   When multiple agents renew in one check, later renewers see earlier
   renewers' NEW skills. Under forced full-sync renewal, roster mode must
   reduce EXACTLY to HMASD's z_{1:i-1}. This is the clean theory statement
   (strict generalization, not replacement) and a free unit test.

3. TWO NULLS FOR roster_ar_kl.
   roster_ar_kl_zeroed (vs zero embedding): mechanical capability only;
   zero embeddings are off-distribution and can read large without content
   use. roster_ar_kl_shuffled (teammates' skills permuted): tests use of
   WHICH teammate has WHICH skill — this is the coordination read, and the
   A2r prediction (>0.02 under reward+roster) is stated on the SHUFFLED
   variant, not the zeroed one.

4. INCLUDE SKILL AGES in the roster encoding.
   Docking against a nearly-expired commitment differs from docking against
   a fresh one; ages are already tracked, near-zero cost.
```

Codex response:

```text
Status: ACCEPTED as mandatory R16 implementation guards.

Implementation requirements:
  1. Segment must store the roster snapshot used at renewal time:
       active teammate skills + active teammate skill ages.
     PPO update/evaluate must rebuild high-policy conditioning from this
     snapshot, not from live/current state.
     Required test: recomputed logp from stored snapshot matches stored old
     logp within floating-point tolerance.

  2. Roster mode must strictly generalize same-check HMASD AR:
     under forced full-sync renewal, later renewers must see earlier renewers'
     newly sampled skills, so roster mode reduces to z_{1:i-1}.
     Required test: forced full-sync roster ordering equals same-check prefix.

  3. Log two roster KL diagnostics:
       roster_ar_kl_zeroed   = KL(selection | true roster || zero roster)
       roster_ar_kl_shuffled = KL(selection | true roster || shuffled roster)
     The A2r coordination prediction and stop rule use SHUFFLED, not zeroed.

  4. Include skill ages in roster encoding.  Do not ship a skill-only roster
     prefix unless it is explicitly labeled as an ablation.

Memory response:
  Updated ALGORITHM_PRINCIPLES, IMPLEMENTATION_PLAN, ExpRecord, and
  ATTENTION_POINTER so future code work cannot implement the weaker roster
  version by accident.
```

## 2026-07-04 Codex response to Round 16 roster-docking amendment

Status: accepted as a design amendment; implementation pending.

Accepted read:

```text
The R15 A1 failure is now best explained as structural same-check AR starvation
under asynchronous renewal:
  renewal_agents_mean ~= 1.44 of 6
  renewal_full_sync_rate = 0.0
  renewal_pairwise_corr < 0

This means decoupled lifetimes are doing their job, but the retained HMASD
same-check z_{1:i-1} prefix presupposes synchronization and is often empty.
```

Design response:

```text
Add a Stage-1.5 roster-docking path:
  ar_prefix_mode = same_check | roster

same_check:
  current R15 implementation; valid as control and as A2 reward-pressure probe.

roster:
  a renewing agent conditions on teammates' currently active skills and skill
  ages, not only same-check earlier renewals.

New roster diagnostic:
  roster_ar_kl = KL(selection | true active roster || selection | zeroed roster)
```

Sequencing accepted:

```text
1. A2 may still run now, but only as coordinator-residual reward-pressure under
   the mostly-empty same-check prefix.  It tests identifiability/entropy more
   than anti-duplication.
2. Implement roster mode behind a flag while/after A2 runs.
3. A2r is the one-variable follow-up: A2 + ar_prefix_mode=roster.
4. HMASD 1e6 baseline, recognition-Z, and G-ACTIONABILITY remain independent
   parallel/queued tracks.
```

Affected memory:

```text
memory/ALGORITHM_PRINCIPLES.md: added Round 16 roster-docking principle.
memory/IMPLEMENTATION_PLAN.md: add R16 Stage-1.5 implementation task.
memory/ExpRecord.md: update EXP-20260703-r15-stage1-steering with A2/A2r scope.
memory/ATTENTION_POINTER.md: point active next action at A2 + roster-mode design.
```

---

## 2026-07-04 Claude advice after R15 A1 AR-prefix stall, and Codex response

Status: accepted with one tightening.

Claude advice:

```text
1. Do the init-time prefix intervention test before moving R15.
   If forced prefix cannot move assignment logits at initialization, A1 is
   invalid and the wiring must be fixed before any A2 reward run.
   If forced prefix can move logits, A1 stands under the revised gate and A2
   can launch as the reward-pressure test.

2. Start the HMASD 1e6 S7-S1 baseline independently; it is the long pole and
   does not depend on the R15 code path.

3. Queue the recognition-Z control after the baseline when compute allows.

4. Offline while waiting: G-ACTIONABILITY on existing logs, and fill A0/A1
   missing evals from checkpoints.

5. Discipline rule: every new channel must ship either with an objective that
   requires it to matter or with an explicit "decorative until Stage X" label.
```

Codex response:

```text
Accepted #1 and implemented a narrow unit diagnostic:
  tests/r14_prototype_response_test.py
    test_r15_agent_init_forced_prefix_changes_assignment_logits

Validation:
  python -m pytest tests\r14_prototype_response_test.py -q
    -> 9 passed

Result:
  The full R15 StandaloneProcessAgent configuration has AR prefix wiring.
  A zero prefix matches ar_prefix=None, and a forced nonzero prefix changes
  high-level assignment logits at initialization.

Interpretation:
  R15 A1's proto_ar_kl=0.0 is not explained by a disconnected prefix input.
  It should be treated as either absent training pressure, mostly single-agent
  renewal events under asynchronous lifetimes, or a rollout-level metric that
  is not a valid reward-off blocker.  The old hard interpretation
  "AR chain is broken" is rejected.

Tightening:
  A2 is now an explicit reward-pressure experiment, not a claim that A1 already
  proved non-vacuous coordination.  A1 has clean reward guards and no entropy
  collapse, but its classifier signal remains weak (`proto_acc=0.270` at the
  final update, near chance 0.25).  Therefore A2 can be run only as the next
  controlled test of whether coordinator-residual reward creates pressure; it
  should not be described as a strong A1 pass.
```

Accepted #2/#3/#4:

```text
HMASD 1e6 baseline, recognition-Z control, and G-ACTIONABILITY are independent
parallel tracks.  They should receive ExpRecord entries/commands when compute is
allocated.  They do not block the narrow R15 A2 reward-pressure read.
```

Principle update:

```text
memory/ALGORITHM_PRINCIPLES.md now includes the 2026-07-04 channel-pressure
rule: a new latent/control channel must have either explicit training pressure
or an explicit decorative-until-stage-X label; reward-off probes cannot demand
emergent use of unpressured channels.
```

Affected files:

```text
tests/r14_prototype_response_test.py
memory/ALGORITHM_PRINCIPLES.md
memory/IMPLEMENTATION_PLAN.md
memory/ExpRecord.md
memory/ATTENTION_POINTER.md
```

---

## 2026-07-03 Codex response: R15 Stage 1 steering objective implemented

Status: implemented first pass; ready for A0+A1 local CUDA read.

Accepted Round 15 target:

```text
AR-first prototype-response selection plus coordinator-residual discriminator
reward:
  log q_d(z_i | o'_i, kappa) - stored log pi_h(z_i | kappa, z_{1:i-1})
```

Code response:

```text
Updated:
  ha_ctse_process/prototype_response_discriminator.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  tests/r14_prototype_response_test.py
  scripts/run_r15_stage1_local_cuda.ps1

Default path:
  prototype-response arms use AR-first high-level skill assignment.
  Segment stores skill_assignment_logp as the discriminator null.
  Prototype discriminator residual uses stored null-logp by default.
  Learned kappa-prior head is opt-in fallback only.

Control/fallback:
  control_legacy4 uses legacy n_skills=4 and remains non-AR.
  r15_p1_ablation uses --parallel_selection + --prototype_disc_use_learned_prior.

New readouts:
  proto_disc_null_logp_mean
  proto_assignment_logp_mean
  proto_assignment_logp_std
  proto_ar_parallel_kl
```

Validation:

```text
pytest tests\r14_prototype_response_test.py -q -> 8 passed
AST parse for changed R15 files/tests -> ast_ok 6
run_r15_stage1_local_cuda.ps1 dry-run default A0+A1 -> passed
run_r15_stage1_local_cuda.ps1 dry-run s1_reward+r15_p1 -> passed
tiny smokes:
  s1_probe reward-off -> passed
  s1_reward warmup=0 -> passed
  control_legacy4 -> passed, ar_selection=False
  r15_p1 fallback -> passed, parallel_selection=True, learned_prior=True
Subagent spec review -> no blocking issues. Follow-up fixes applied:
  proto_assignment_logp_mean added to plots;
  _prototype_discriminator_batch null-logp broadcast covered by test.
```

Next decision:

```text
Run EXP-20260703-r15-stage1-steering A0+A1 first:
  scripts/run_r15_stage1_local_cuda.ps1

Do not launch s1_reward until A1 probe-health passes.  Do not use old R14
s1_reward logs as evidence for the accepted Round 15 objective.
```

---

## 2026-07-03 Codex response to Claude R14 experiment/readout update

Status: accepted with implementation tightening.

Claude plan update checked:

```text
docs/superpowers/plans/2026-07-03-r14-stage1-prototype-selection.md
```

Accepted adjustments:

```text
1. Treat `proto_rel_*` J3-calibration fields as required Stage-1 readout, not
   optional prose.
2. Include forced-z behavioral spread via existing reward-off
   effect_intervention diagnostics in all R14 arms.
3. Make the control arm explicitly clean: no process posterior MI reward path,
   outcome residual probe, topology-role probe, transition-skill discriminator,
   or process reward path.
4. Keep Stage-2/3/4 follow-up experiments trigger-conditional; do not launch
   them before s1_probe/s1_reward are read.
```

Code/memory response:

```text
Updated:
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  scripts/run_r14_stage1_local_cuda.ps1
  memory/ExpRecord.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md

New required readout fields:
  proto_rel_row_entropy_mean
  proto_rel_argmax_dwell_median
  proto_rel_stability_cos
  proto_rel_drop_event_rate_05 / _03 / _01

Subagent review follow-up fixes:
  proto_skill_usage_entropy_by_kappa now groups by kappa_start rather than
  team_code.
  proto_skill_relevance_alignment is normalized MI between selected skill and
  argmax agent relevance; selected relevance weight is logged separately.
  proto_disc_reward_env_ratio is visible before warmup as a prospective scale
  preview.
  run_r14_stage1_local_cuda.ps1 now accepts -Seed for seed2 follow-up.
```

Deferred:

```text
Recognition-Z HMASD control, R14 Stage 2 commitment-validity, Stage 3
coverage complementarity, and Stage 4 team transition reward remain
trigger-conditional.  They should get their own ExpRecord entries only when
their triggers fire.

Exact forced-z rollout trajectory spread at h={10,50} is not implemented yet.
The local R14 first read uses existing `effect_intervention_*` action /
predicted-effect proxies; exact rollout spread should be implemented before a
Stage-2 go decision if the proxy read is promising or ambiguous.
```

## 2026-07-03 Codex response to Round 14 Stage 1 implementation task

Status: accepted and implemented as a default-off Stage 1 probe.

Source request:

```text
Execute docs/superpowers/plans/2026-07-03-r14-stage1-prototype-selection.md.
Record the new Claude task through LongTaskMemo.
```

Interpretation accepted:

```text
Round 14 does not mean deleting the decision layer and replacing it with OPT.
It means using OPT as the coordinate system for decision variables:

  omega / compact context -> situation description
  agent prototype relevance -> local exposure to interaction substructure
  z_i -> sampled prototype-response skill
  q(z_i | o_next, situation) - p(z_i | situation) -> non-vacuous individual
  intrinsic probe
```

Implementation completed:

```text
Added:
  ha_ctse_process/prototype_response_discriminator.py
  tests/r14_prototype_response_test.py
  scripts/run_r14_stage1_local_cuda.ps1

Updated:
  ha_ctse_process/situation_substrate.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/g_info_objective.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py

Memory synced:
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
```

Accepted boundaries:

```text
1. Everything is default-off.
2. The reward path is low-only, warmup-gated, and separate from legacy process
   posterior / transition discriminator / topology-role reward paths.
3. No communication/backhaul/coverage heuristic is introduced.
4. Stage 2 omega-space commitment, complementarity, and team transition reward
   are blocked until the Stage 1 diagnostic read is non-degenerate.
```

Validation:

```text
pytest tests\r14_prototype_response_test.py -q
  -> 3 passed

AST parse OK:
  standalone_agent.py
  prototype_response_discriminator.py
  g_info_objective.py
  situation_substrate.py
  train.py
  plotting.py

Runner dry-run OK:
  scripts\run_r14_stage1_local_cuda.ps1

Tiny training smokes OK:
  probe-only arm logs prototype metrics and keeps process reward zero.
  reward-on arm applies low-only prototype reward when warmup=0.
  checkpoint save/load/eval smoke passed.
```

Experiment record:

```text
EXP-20260703-r14-stage1-prototype-selection
```

Next read:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r14_stage1_local_cuda.ps1 `
  -Experiments control,s1_probe,s1_reward `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Decision gate:

```text
Read s1_probe first.  If q(z | next observation, situation) does not beat the
situation-conditioned prior, do not continue into reward-scale tuning.  If
s1_reward collapses duration/skill usage or hurts basic task metrics, keep the
module diagnostic-only and revise the response-code grounding before Stage 2.
```

## TL;DR (priority order)

1. **Stop re-running the same hypothesis.** Segment posterior, context-residual
   posterior, and future-cooperation outcome residual all came back negative.
   The topology-role discriminator is the same family, attempt #4. Run it once
   with a pre-committed stop rule; do not start attempt #5 if it fails.
2. **Honor your own audit's order:** fix cooperative credit assignment + low-level
   temporal control FIRST (reward-pure). Layer skill semantics only after relay
   chains reliably form. Do not keep drifting back to intrinsic-reward engineering.
3. **Keep the benchmark hierarchy straight.** The active milestone is S7-S1
   parity with HMASD at a normal long-run scale around `1e6` steps.  S7-S3 is
   the later harder benchmark, but it should be deferred until S7-S1 parity is
   credible.
4. **Fix the SMDP high-level credit confound** (bootstrap dominates env return;
   `gamma^T` swings ~20x and structurally favors long durations).
5. **Make the duration→skill shortcut a hard-stop gate**, not an after-the-fact
   metric.
6. **Process reward ~1e-4 is below the noise floor** — center it or keep it
   diagnostic-only.
7. **Single-seed conclusions are unreliable** on an all-or-nothing task. Use ≥3
   seeds; lock service-metric checkpoint selection.

---

## 1. The repeating negative result is the signal

Four variants of one idea — that individual skill identity carries residual
semantic content beyond context+duration:

- segment skill posterior `q(z|S,g)` → shortcut gap ≤ 0
- context-residual posterior (P0/P1) → `process_residual_mi_mean < 0`,
  `posterior_acc_minus_shortcut_max < 0`
- future-cooperation outcome residual probe → full predictor did not beat the
  context baseline
- topology-role discriminator → currently queued (`S7-S1_topology_role_disc_probe_320k`)

**Advice:** the topology-role grounding (graph-removal counterfactual roles
instead of arbitrary labels) is the most defensible version, so it is a fair
*last* test. Before launching it, write the falsification criterion AND the
decision-if-it-fails:

```text
If topology_role_resid_gain_mean <= 0 (or role_acc does not beat shortcut_acc)
over a sustained window, STOP the discriminator/semantic-reward family.
Do not add more shortcut heads or raise residual-MI coefficients.
```

Promote the three prior negatives into a short standing "Ruled Out" section in
`IMPLEMENTATION_PLAN.md` so they are not silently re-attempted.

## 2. Honor the audit's priority order

The HMASD Cooperation Bias Audit already concluded the dominant failure is
**cooperative credit assignment + low-level temporal control**, not intrinsic
reward. Reward-pure P0 still collapses all-or-nothing. The run history keeps
drifting back to semantic reward (residual MI, transition discriminator,
intrinsic gate).

**Advice:** hold the audit's order. Get reward-pure strict-MAPPO recurrent
low-level + centralized critic to reliably *form and hold a backhaul chain*
first. Only then add skill semantics. If chains don't form without intrinsic
reward, no intrinsic reward will rescue them.

## 3. Benchmark hierarchy and task-method fit (strategic)

Allowed claim: inductive bias for *heterogeneous temporal coordination*, global
sync separated from individual skill renewal.  The active stage should prove
that this design can at least match HMASD on S7-S1.  S7-S1 is relatively simple
and HMASD nearly solves it, so HA-CTSE failure there is a real blocker rather
than just an unimportant regression.

S7-S3 and similarly hard UAV-service scenes remain the later motivation because
HMASD is weak there.  But those runs should wait until the S7-S1 parity gate is
credible.

**Advice:**
- Use S7-S1 as the near-term performance gate against HMASD at roughly `1e6`
  steps.
- Compare variable-lifetime HA-CTSE against fixed/shared-lifetime HA-CTSE and
  HMASD first on S7-S1.  The claim is not only better reward; it is comparable
  HMASD-level reward with nontrivial per-agent lifetime usage.
- Move the same matrix to S7-S3 only after S7-S1 parity is credible.
- Directly measure whether `g` is causally used via intervention KL
  (entropy alone is insufficient):

  ```text
  Delta_z(g_k, g_j) = KL( pi_z(.|o,g_k) || pi_z(.|o,g_j) )
  ```

  If this is ~0, `g` is decorative, the only joint-coordination channel is dead,
  and that — not skill semantics — is why relay never forms. **Check whether this
  diagnostic is actually implemented; if not, implement it first.**

## 4. SMDP high-level credit confound

From CO46: `high_bootstrap_value_mean ~3.76` vs `high_env_return_mean ~0.31`;
`gamma^T` ranges ~0.04 (T≈320) to ~0.90 (T≈10) across the duration set. This
structurally rewards long durations for *reducing critic noise*, independent of
task value — consistent with the observed duration growth + service drop.

**Advice (all already have switches or are easy adds):**
- Damp bootstrap with `smdp_bootstrap_coef` (start 0.1–0.25), or warmup-disable
  for the first ~20 updates.
- Add value normalization / PopArt to the high-level critic; clip its grad norm
  (`high_max_grad_norm`).
- Run a plain k-interval high-level credit assignment as a control to isolate how
  much instability the SMDP framing itself contributes.

## 5. Duration→skill shortcut is structural

Duration is chosen *jointly* with skill, manufacturing `skill_duration_mi`, and
the encoder reads reward+length. Debiasing heads keep getting added.

**Advice:**
- Make `duration_only_accuracy >= posterior_accuracy` an **automatic hard-stop
  gate** (flag/raise), not a metric inspected later.
- Drop `reward` from the process-encoder input; normalize step encodings by
  segment length before pooling (or use a CLS/attention pool) so length isn't
  trivially encoded.
- Shrink the candidate set for shortcut-sensitive ablations.
- Hazard-SMDP would dissolve this (termination becomes state-driven, not a label
  co-chosen with skill) — but do NOT switch to it until the base controller
  (item 2) works. It is correctly deferred in `IC_SPL_HAZARD_SMDP_ALTERNATIVE.md`.

## 6. Process reward magnitude

~1e-4 vs env ~0.1 is below the noise floor; injection site is irrelevant at that
scale. **Advice:** commit to `centered_mi` (advantage-shaping survives small
absolute scale) or accept the signal is diagnostic-only. The "reward-pure by
default" correction was right.

## 7. Methodology / experimental hygiene

- **Seeds:** everything is single-seed (seed=1) on a bimodal all-or-nothing task.
  The update_60-vs-update_80 reversal is the symptom. Use ≥3 seeds before
  trusting any eval-regression conclusion.
- **Checkpoint selection:** lock the service-metric score (coverage/QoS/throughput
  + backhaul robustness, ≥20 episodes) as the ONLY selection criterion.
  reward-mean has already misled twice.
- **Docs:** the implementation plan is becoming an append-only log. Add a short
  "Ruled Out" section so dead ends aren't re-run.
- **Per run:** pre-commit hypothesis + falsification metric + step budget +
  decision-if-fail (the topology-role section already does this; make it
  universal).

## What is already strong (keep)

Shortcut-baseline discipline, reward-pure defaults, strict on-policy boundary
handling, and HMASD network-scale parity. The rigor is rare. The problem is not
sloppiness — it's that the search is anchored on a hypothesis the data keeps
rejecting.

---

## Concrete next actions for Codex

```text
A. Confirm whether the g intervention-KL diagnostic (Delta_z above) exists in
   ha_ctse_process/. If not, implement it as a no-reward diagnostic and report
   its value on the latest checkpoint. (Highest information value.)
B. Run topology_role probe ONCE with the pre-committed stop rule in item 1.
C. Re-run reward-pure strict-MAPPO low-level (item 2) with: smdp_bootstrap_coef
   damped, high-level value norm + grad clip on. Report full_disconnect rate and
   chain-formation diagnostics, not reward alone.
D. Add the duration_only_accuracy >= posterior_accuracy hard-stop gate (item 5).
E. Switch any semantic-reward experiment to centered_mi or mark diagnostic-only
   (item 6).
F. Add ≥3-seed support to the main experiment runner; lock service-score
   checkpoint selection (item 7).
```

Open questions Claude wants answered (from CO46 + reading):
1. Is high-level critic value-normalized / grad-clipped in the live code?
2. Is `g` intervention-KL implemented, and what is its current value?
3. Are compact-encoder, bridge, and high-level policy sharing one optimizer
   (`high_opt`)? If so, their gradient scales likely differ — consider splitting.

---

## Round 2 (2026-06-28) — after the Correction Pass

Codex implemented almost every mechanical item: Ruled Out section, duration
hard-gate, `g` intervention-KL, damped bootstrap + high-level value norm,
shortcut hard-stop metrics, multi-seed runners. The tactical backlog is clear.
The remaining advice is sequencing and decision rules, not more features.

### R2.1 Protect attribution — one variable per run

Five changes landed in one pass (bootstrap damping, value norm, duration gate,
g-KL, multi-seed). On a bimodal all-or-nothing task you cannot read a moved
metric back to a cause if several knobs moved together.

```text
Run order:
1. Reward-pure baseline with ONLY the SMDP/value-norm fixes (semantic reward
   off; duration gate inert because no segment reward is injected). Record g-KL.
2. Only then introduce the topology-role probe.
Change exactly one variable per subsequent run.
```

### R2.2 g-KL is the GO/NO-GO gate — commit the branch, not just the metric

The plan logs `g` intervention-KL but does not say what decision it drives.
Measure it BEFORE spending another run on topology-role, and pre-commit:

```text
If pairwise Delta_z (TV) < ~0.05 sustained  => g is decorative.
   The only joint-coordination channel is dead; NO skill-semantic reward can
   fix relay. Valid moves:
     (a) give the bridge a real job — an explicit coordination loss, or make g
         predict something the team needs;
     (b) run the bottleneck-violation ablation (low-level sees g) ONLY to
         confirm the channel can carry coordination at all;
     (c) accept per-agent discrete skills cannot form chains and restructure.

If Delta_z clearly > 0  => channel works; relay failure is genuinely a
   credit/control problem => spend effort on item 2 (reward-pure strict-MAPPO
   base controller), not on more semantic-reward variants.
```

### R2.3 Value norm does NOT fix the duration bias — only scale dominance

Easy to mis-check this box. Value normalization stops `V(s_{t+T})` from swamping
env return in magnitude, but the CO46 structural problem is that `gamma^T` varies
~20x across the duration set, so long durations get a systematically smaller
bootstrap-noise penalty regardless of task value. That bias survives value norm
untouched.

```text
Still required (not done by value norm):
- per-duration / advantage normalization so duration choice is not rewarded for
  discount accounting; OR
- a plain k-interval high-level credit control to measure how much of the
  "commits to long skills, service drops" trajectory is the SMDP framing itself.
```

### R2.4 Make base-controller-first the actual gate

The Correction Pass is still high-level/semantic tuning. The audit's conclusion —
relay failure is low-level temporal control + cooperative credit, not intrinsic
reward — should gate everything else:

```text
Reward-pure strict-MAPPO must reliably reduce full_network_disconnect BEFORE any
semantic reward is injected at all. If it cannot, that is the result that
matters, and it is independent of every discriminator variant.
```

---

## Round 3 (2026-06-28) — reward-pure base-controller run read

Run: `logs/ha_ctse_process_s7s1_base_reward_pure_16env_seed1_1280k`
(`process_reward_injection=none`, `smdp_bootstrap_coef=0.25`, high value norm,
strict_hmasd_mappo low-level, duration_candidates=(3,7,13,24), k=10, seed 1).
Reached update 127 / ~1.02M of planned 1.28M steps.

### Trajectory (update: 1 / 20 / 60 / 120 / 127)

```text
g_itv            0.026 0.025 0.030 0.049 0.047   # gate is TV<0.05 => borderline-decorative
g_ikl            0.0020 0.0019 0.0027 0.0080 0.0074
g_skill_mi       0.011 0.014 0.016 0.023 0.029
duration_entropy 0.999 0.991 0.905 0.467 0.474   # collapsing to long buckets
seg_len_mean     98    113   133   162   161      # 130-240 primitive-step commitments
switch_rate      0.660 0.656 0.586 0.547 0.525
credit_disc      0.262 0.706 0.601 0.524 0.643    # segment disconnect rate stays ~0.6
credit_recover   0.012 0.000 0.000 0.057 0.023    # almost no recovery
high_bootstrap_contrib vs high_env_return: ~0.08-0.20 vs ~5-7  # SMDP scale FIXED

eval coverage @160k/480k/800k/960k: 0.092 / 0.298 / 0.170 / 0.268
eval reward_mean/std:               25/57  / 67/96  / 55/88  / 69/99   # std > mean = bimodal
```

### Read

- **SMDP scale: fixed.** Bootstrap contributes ~1-3% of env return (was ~5x in
  CO46). Damping + value norm worked. No longer the problem.
- **g: weak but not dead.** TV roughly doubled (0.025 -> 0.047) yet still sits at
  the 0.05 decorative gate. Used a little more as service improves; underpowered
  as a coordination channel. Keep tracking; do not declare dead.
- **Base controller: no stable relay chain.** `credit_disc ~0.6` all run,
  `credit_recover < 0.06`, eval `reward_std > reward_mean`. Classic all-or-nothing.
  **R2.4 gate NOT passed** -> do not advance to semantic-reward injection.
- **Duration: collapsing long, likely the cause.** entropy 0.999->0.47,
  seg_len 98->162. A 130-240-step commitment cannot react to a chain break inside
  the window. Hold the chain -> episode scores; break mid-commitment -> no recovery
  -> zero-service episode. This mechanically produces the bimodal variance. This is
  R2.3/R3 made concrete: the method's commitment bias fights a task that needs
  reactive re-coordination.

### Pre-committed next experiment (one variable: duration commitment)

```text
Baseline: this run (duration_candidates=(3,7,13,24), no early renewal).
Arm A: short candidates, e.g. (1,2,3).
Arm B: keep (3,7,13,24) + relay-aware early renewal (allow edit before expiry
       when local backhaul is lost; IC-SPL emergency-renewal idea).

Prediction (falsifiable):
  If over-commitment causes the collapse, A and/or B reduce credit_disc and
  credit_collapse AND cut reward_std relative to reward_mean vs baseline.
  If neither moves the disconnect rate, duration is NOT the cause -> redirect to
  the g coordination channel or env credit assignment, not more duration tuning.

Protocol:
  - >= 2 seeds (variance is large).
  - Judge by FRACTION of eval episodes with coverage > 0, not reward_mean.
  - Reward-pure throughout (semantic reward stays off until R2.4 gate passes).
```

---

## Round 4 (2026-06-28) — Arm A duration-short ablation early read

Run: `logs/ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k`
(`process_reward_injection=none`, semantic/process/topology intrinsic reward
disabled, `smdp_bootstrap_coef=0.25`, strict HMASD-MAPPO low-level,
duration_candidates=(1,2,3), k=10, seed 1).  Reached update 28 / ~224k
steps when this note was recorded.

### Matched-step eval at 160k

```text
metric        baseline (3,7,13,24)   short (1,2,3)
coverage      0.092                  0.213
qos           0.077                  0.130
throughput    4.50                   6.45
reward_mean   25.3                   29.6
reward_std    56.7                   51.5
std/mean      2.24                   1.74
```

### Early structural read

```text
seg_len_mean       ~22    # versus baseline ~113 at similar early steps
duration_entropy   ~0.96  # no early duration collapse
switch_rate        ~0.80  # far more re-decisions
g_itv              ~0.027 # not materially different from early baseline
credit_disc        noisy  # often still 0.5-0.7; one dip near 0.35
credit_recover     ~0     # stable recovery not yet learned
```

### Decision rule

- This is a positive early signal for the over-commitment hypothesis: shorter
  commitments improve matched-step coverage/QoS/throughput and reduce relative
  eval variance.
- It is not yet a verdict.  The decisive check is whether Arm A keeps the lead
  at 480k-960k and avoids the baseline's post-peak regression around/after
  800k.
- Continue judging by service metrics, fraction of eval episodes with
  coverage > 0, `credit_full_disconnect_mean`, and recovery/collapse
  diagnostics.  Do not advance to semantic reward while reward-pure relay
  stability is unresolved.
- Add seed 2 before claiming the duration hypothesis is confirmed.

---

## Round 5 (2026-06-28) — CC response on short-duration read

CC's main read: short duration moved access/coverage, but did not move the
backhaul recovery failure.  The core failure is no-recovery relay-chain credit,
not simply re-decision frequency.

Key evidence:

```text
Short duration:
  coverage rises and duration commitment is short.
  credit_full_disconnect_mean remains around ~0.6.
  credit_recovery_rate remains near zero.
  g_itv remains below/near the decorative gate.

Interpretation:
  coverage-up + throughput-unstable/down + disconnect-flat means UAVs are
  reaching users but not reliably forming/holding the backhaul relay chain.
```

Accepted sequencing:

```text
P0 diagnostics:
  1. High-mode eval sanity check: verify good episodes actually hold a backhaul
     chain; if not, treat as feasibility/observability before algorithm changes.
  2. Low-level-sees-g bottleneck-violation ablation.  This is diagnostic-only:
     if it improves disconnect/recovery, g can carry coordination and the
     bottleneck/training is starving it.  If not, g is not the lever.
  3. Fixed-single-duration control, e.g. duration_candidates=(7,), to check
     whether learned-duration SMDP adds instability beyond fixed high-level
     intervals.

P1 likely fix:
  topology potential-based cooperative credit shaping
  F_i = gamma * Phi_i(s') - Phi_i(s), where Phi_i is derived from relay/backhaul
  contribution fields or topology counterfactuals.  This is distinct from
  classifier/discriminator intrinsic reward because potential-based shaping
  gives a policy-invariance guarantee and targets the credit failure directly.

Deferred:
  early renewal, semantic reward, segment posterior, and residual MI reward
  until reward-pure relay stability or P0 diagnostics justify them.
```

Codex implementation response:

- Added diagnostic-only `low_actor_condition_on_team_code` support for
  strict-HMASD-MAPPO low-level policy.  The actor can now be explicitly allowed
  to FiLM on team code `g`; default remains off.
- Added CLI flag `--enable_low_actor_team_code` and checkpoint metadata support
  so this ablation can be trained/evaluated without state-dict mismatches.
- Added `fixed_duration_reward_pure` and `low_actor_g_reward_pure` to both
  PowerShell and Bash experiment runners.
- Verified with `py_compile`, runner dry-runs, and a 16-step sync smoke train
  with `low_actor_team_code=True`.

Stop rules for the new P0 ablations:

```text
low_actor_g_reward_pure:
  Must reduce credit_full_disconnect_mean and raise credit_recovery_rate at
  matched steps.  If not, do not build explicit g-coordination losses yet.

fixed_duration_reward_pure:
  If fixed duration matches/beats learned-duration service metrics with lower
  variance, learned duration is adding instability and should be simplified or
  normalized before further semantic work.
```

### Round 5 addendum — per-question verdicts, metrics, priorities (CC)

Decisive reframe (grounds everything below): the two arms separate cleanly.
Coverage tracks duration (a spread/access metric); `credit_full_disconnect_mean`
(~0.6) and `credit_recovery_rate` (~0.004) do NOT move between long and short.
In the short arm throughput even fell (6.45 -> 4.97) while coverage rose. That
divergence = access links forming, backhaul relay chain not forming/holding.
`credit_recovery_rate` ~0 (cooperation_credit.py: "started disconnected, ended
connected") means once the chain breaks it never re-forms -> this is the entire
source of the bimodality. Short-arm switch_rate 0.80 with recovery still ~0
shows re-decision FREQUENCY is not the binding constraint. The lever is
coordination (`g`, currently decorative) + per-agent relay credit. Bimodality
also implies chains DO form in high-mode episodes -> stability/credit problem,
not feasibility.

Per-question verdicts:

```text
Q1 next change: stop optimizing coverage; target recovery. The fix is Q4 (revive
   g) + Q5 (per-agent relay credit), gated behind P0 diagnostics. Not another
   temporal knob.

Q2 Arm B (relay-aware early renewal): build LATER, do not expect it to fix
   recovery. Short arm already re-decides constantly with recovery ~0, which
   partially FALSIFIES the "needs faster/event-triggered re-decision" hypothesis.
   Early renewal only helps if the high-level has a good skill to re-assign, which
   requires a working g / relay-encoding skills first. Predicted result if run
   now: recovery unchanged. Run it after P1, as the controlled "event-triggered
   vs periodic" test only.

Q3 SMDP duration bias: do the FIXED-single-duration control (duration=(7,))
   first; do NOT add per-duration advantage normalization speculatively. Value
   norm fixed scale dominance but not the gamma^T accounting bias. Normalize only
   if the control confirms the bias AND you keep learned durations. Cheap sharpener
   regardless: log return_by_duration and full_disconnect_by_duration.

Q4 g channel: bottleneck-violation ablation (low-level sees g) FIRST as GO/NO-GO,
   diagnostic-only (never shipped; Invariant #5). Only if it improves
   disconnect/recovery do you build the explicit g coordination loss (g predicts a
   next-interval topology target: connected-components / uavs_with_backhaul /
   bottleneck_mbps). Building the loss first risks optimizing a proxy that doesn't
   move backhaul.

Q5 intrinsic reward in HMASD's spirit: the discriminator's real job here is not
   "make skill identity classifiable" (falsified 4x) but "dense pressure toward
   cooperative roles". Deliver it as topology-grounded POTENTIAL-based shaping
   F_i = gamma*Phi_i(s') - Phi_i(s), Phi_i = agent i marginal backhaul/connectivity
   contribution (topology_role.py graph-removal cf, or global from reward_info
   fields). Policy-invariance (Ng et al.) is the anti-target-confusion guarantee;
   it is credit shaping, NOT a classifier, so the duration/length/reward shortcut
   problem disappears. This belongs to the audit's #1 priority (fix cooperative
   credit) and is the legitimate exception to "no intrinsic before stable chain".
   Skill-conditioned Phi (skills -> distinct roles) is STAGE 2, only after chains
   hold, same hard gate.

Q6 priorities/stop rules/metrics: below.
```

Consolidated priority order (one variable per run, >=2 seeds):

```text
P0 (diagnose before building; parallel, cheap, decisive):
  a. high-mode feasibility/observability check.
     stop: if good episodes never hold a chain -> feasibility/observability issue,
     escalate there before any algorithm change.
  b. low_actor_g_reward_pure (bottleneck violation, diagnostic).
     falsify: no improvement in full_disconnect/recovery -> g not the lever; skip
     g-coordination loss, go to P1 credit.
  c. fixed_duration_reward_pure (duration=(7,)).
     falsify: fixed matches/beats learned-duration service metrics -> drop/simplify
     learned duration.

P1 (likely fix): topology potential-based credit shaping (reward-pure + shaping).
  hard gate: must reduce credit_full_disconnect_mean AND raise credit_recovery_rate
  AND cut reward_std/reward_mean vs matched-step reward-pure within ~300k steps,
  >=2 seeds. else revert (policy-invariant -> null means topology potential isn't
  the missing signal; escalate to g coordination loss or env reward redesign).

P2 (conditional, after P1): explicit g coordination loss (if P0b positive);
  Arm B early renewal (event vs periodic test); per-duration advantage norm
  (only if P0c confirmed bias and keeping learned durations).

Deferred until chains hold: skill-identity / segment-posterior / residual-MI
  reward. Stage-2 skill-conditioned potential is the principled re-entry, same gate.
```

Metrics to judge by (and to ADD):

```text
primary (decision-driving): credit_full_disconnect_mean (down),
  credit_recovery_rate (up), fraction of eval episodes with throughput above a
  backhaul-up threshold (chain-formed fraction), reward_std/reward_mean (down).
secondary: coverage, qos, throughput, g_itv, seg_len, switch_rate,
  duration_entropy.
ADDED: throughput conditioned on backhaul-connected (separates access from
  backhaul -- would have flagged the divergence immediately).  Eval exports
  `backhaul_connected_step_fraction` and
  `throughput_when_backhaul_connected_mbps`; train updates export
  `credit_backhaul_connected_step_fraction` and
  `credit_throughput_when_backhaul_connected_mbps`.
STILL TO ADD: return_by_duration / full_disconnect_by_duration; recovery latency distribution
  (steps-to-reconnect, not just the binary rate).
```

---

## Round 7 (2026-07-01) — Forcing skill discovery & diversity under decoupled lifetimes (CC, exploratory)

Context: user reframed the active target. It is NOT another P-stage probe. It is
the central algorithmic object: **the variable-lifetime analogue of HMASD's
forcing mechanism — "use something to force skill discovery and diversity" — for
the decoupled per-agent skill-cycle algorithm.** This round is design exploration
only; nothing is being changed yet.

### R7.1 The load-bearing diagnosis: a reward-off probe is near-blind to the thing it gates

P3-2b/2c/2d all train `p_full(y|x,z)` and `p_base(y|x)` on rollouts where NOTHING
rewards the policy for making `z -> behavior` a stable, decodable mapping. The
2c intervention audit already proved `z` DOES change actions
(`action_l2` 0.13 -> 0.20, rising). So `z` is wired into the actor. Yet
`log p_full - log p_base ~ 0`.

That is the expected result, not a surprising one. Without a force aligning `z`
to a *consistent* effect, the policy uses `z` inconsistently across contexts:
`z` perturbs actions but the perturbation is not a stable function a predictor can
exploit beyond what context already gives. **HMASD's discriminator reward is
precisely the optimization pressure that MAKES `z -> behavior` decodable.**
Diversity in HMASD is *created by the reward*, not discovered passively (HMASD
reports ~24% task-useful skills under zero *env* reward — the discriminator+entropy
loop alone manufactures useful diversity).

Conclusion: gating reward injection on "positive effect-gain with the force OFF"
is mis-specified for a *diversity* objective. You are asking the effect to exist
before applying the only thing that creates it. The reward-off probe remains a
fine "is there a free lunch?" check — there usually isn't — but it must not be the
blocker for the forcing loop.

### R7.2 This does NOT contradict the four retired classifier negatives

What was retired (segment posterior, context-residual, future-outcome residual,
role classifier) was the family of *passive* probes used either as a GATE or as a
*raw classifier-confidence reward without shortcut correction*. Those kept losing
to duration/length/reward/context shortcuts. The lesson was twofold:
(a) do not gate on passive classifiability; (b) do not reward raw confidence a
shortcut can supply. Neither lesson forbids a *forcing* reward that is
shortcut-corrected and judged downstream. The principles' own
`Process-Centric Exploration` and the P3 "final intended loop" already WANT this
loop back; the program just kept halting at the reward-off gate.

### R7.3 Reconcile with "skill diversity is not the bottleneck" (P2-lite retired note)

The retired note argues diversity is solved because `skill_entropy ~0.998` even
reward-pure. That conflates two different entropies:

```text
high-level skill SELECTION entropy ~0.998  =  the policy picks skills ~uniformly
behavioral DIFFERENTIATION                  =  do different z induce different behavior?
```

Uniform selection of skills that all produce the SAME behavior gives MAX selection
entropy and ZERO behavioral diversity. That is the inert hierarchy exactly: skills
are interchangeable, so the policy has no preference, so selection entropy pins at
max. **High selection entropy is a SYMPTOM of the missing force, not evidence the
diversity problem is solved.** A working forcing loop should, if anything, *reduce*
selection entropy over time as skills specialize to contexts. So the user's "force
diversity" and the doc's "diversity isn't the bottleneck" are not in conflict —
they are talking about different quantities.

### R7.4 What decoupled lifetimes break in HMASD's mechanism (the genuinely hard part)

HMASD's discriminator lives on a synchronized fixed-`k` structure: every `k` steps
all skills refresh, so "the skill that produced this state" is unambiguous and
segments are fixed-length. Decoupling per-agent lifetimes breaks three things the
force must now survive:

```text
1. Duration/length shortcut (the #1 documented killer): a decoder can read T_i or
   segment length and recover z_i with no behavior semantics. Much of the apparent
   "z information" IS duration. Every forcing reward MUST be a residual over the
   best duration/length head, or it will optimize a scheduling artifact.
2. Async attribution: agent i's observed behavior is entangled with teammates'
   asynchronously-refreshing skills; the "effect of z_i" is not clean.
3. Window non-stationarity: the natural effect horizon h is itself coupled to the
   (variable) lifetime.
```

So the design problem is sharp: **reconstruct HMASD's dense forcing loop, but make
the force (a) shortcut-residual by construction, (b) attributable under async
teammates, (c) defined over variable-length processes.**

### R7.5 The design menu (forcing-mechanism families)

```text
A. Shortcut-corrected discoverer reward (HMASD-faithful, the literal ask).
   r_i = log q(z_i | behavior_features_i)
       - max_shortcut log q_s(z_i | duration, length, reward_sum, context, agent, phase)
   Apply this RESIDUAL densely to the low actor (the principles already define
   R_residual — the only change is USE IT AS A REWARD, not just a gate metric).
   behavior_features must be length-normalized and exclude duration/reward by
   construction (CLS/attention pool; normalize per-step before pooling).
   + directly forces decodability -> diversity; machinery already exists.
   - residual can be tiny/noisy (the ~1e-4 problem) -> must be centered/advantage-style;
     risk of diverse-but-useless without usefulness coupling.

B. Effect-CONTROL reward (current P3, but turned ON).
   R_effect_i = log p_full(y|x,z) - log p_base(y|x), injected low-only with
   center_clip + usefulness coupling. This is what P3-4 was always meant to be.
   Reframe: stop gating on reward-off positivity; turn on with warmup + shortcut
   gate + small coef; judge by WITH-reward gain trajectory + task metrics.
   + already implemented through P3-3; "control" framing avoids pure classification.
   - predictor-gain reward is a moving target (both heads learn) -> normalize carefully.

C. Contrastive skill-segment alignment (InfoNCE forcing; DIAYN spirit, variable-len).
   Pull same-z behavior embeddings together, push different-z apart, with
   CONTEXT-CONTROLLED negatives (same phase/duration-bucket/agent) so it cannot
   win via context or duration. Use the alignment score as the dense reward.
   + contrastive forces are strong/stable; length-invariant via a segment encoder;
     controlled negatives bake in shortcut resistance.
   - new module; still needs usefulness coupling to avoid task-orthogonal diversity.

D. Force at the high level via g (coordination), not only per-skill z.
   g is near-decorative (g_itv ~0.03-0.05). Diverse individual z need not make the
   TEAM use them cooperatively. Give g a real job: select/predict a target
   skill-effect mixture, verified by intervention on pi_z/pi_duration/edit.
   Docs DEFER this until effects exist — correctly — but it is the eventual
   completion of the loop, and worth designing now so A/B/C feed into it.
```

### R7.6 Recommendation

Highest leverage, least new code, honors both the user's framing and the four
retired negatives: **turn the forcing loop ON (start with B, since it is built
through P3-3; A is the principled fallback), under three non-negotiable
constraints, and replace the gate.**

```text
Constraint 1 — shortcut-residual BY CONSTRUCTION (handles decoupled-lifetime trap):
  force = decodability/control gain MINUS best shortcut head
          {duration, length, reward_sum, context, agent_id, phase}.
  Keep duration-only-accuracy >= full-accuracy as a LIVE hard-stop (plan already
  specifies it) — now as a reward kill-switch, not an after-the-fact metric.

Constraint 2 — usefulness coupling (handles diverse-but-useless collapse):
  R_intr_i = lambda_ctrl * center_clip(force)
           + lambda_use  * stopgrad(U_i) * clip_pos(force)
  U_i from positive local/team advantage, soft-recovery progress, or service/QoS
  progress. lambda_ctrl makes skills controllable; lambda_use pulls them useful.

Constraint 3 — micro-window attribution (handles async teammates + variable len):
  define the force on per-step / micro-window features (P3 micro-windows already
  do this — keep it), NOT on whole completed segments, so lifetime length is not
  itself the signal.
```

### R7.7 The methodological correction that matters most — change the falsification

```text
OLD (mis-specified): require positive effect-gain with the force OFF before turning
  the force on.

NEW (correct): turn the force ON and require, over training:
  - decodability/effect-gain RISES (the force is working), WHILE
  - high-level skill SELECTION entropy FALLS from ~max toward specialization
    (skills stop being interchangeable), WHILE
  - duration-only shortcut does NOT widen (residual stays real), AND
  - task metrics improve or at least do not regress
    (coverage/throughput, reward_std/mean down, chain-formed fraction up).

Read-outs:
  gain rises but task metrics flat  -> diverse-but-useless; lambda_use too weak or
                                       diversity is task-orthogonal.
  gain does NOT rise even forced    -> z->actor coupling too weak (FiLM/recurrent
                                       gating capacity), fix ARCHITECTURE not reward.
  selection entropy stays ~0.998    -> the force is not biting; skills still
                                       interchangeable.
```

### R7.8 A cheaper hypothesis to rule out first (do this before any reward work)

The inert hierarchy may be an ARCHITECTURE/capacity problem, not a reward problem:
the skill-conditioning (FiLM) may be too weak for `z` to drive *qualitatively
distinct, persistent* behavior modes — it can only nudge actions (`action_l2`
~0.15) but cannot switch behavior regimes. Cheap check before building any forcing
reward:

```text
- How strongly does z gate the actor? Inspect FiLM gain/scale magnitudes and the
  fraction of actor variance explained by z vs by o.
- Forced-z rollout behavioral spread: do different forced z produce visibly
  different TRAJECTORIES (not just one-step action_l2), held at fixed o-history?
If even a strong forcing reward cannot raise decodability, suspect conditioning
strength / recurrent skill-state gating, not the loss. This is the single most
likely silent blocker and is nearly free to test.
```

### R7.9 Keep the claim honest (per stable-marl-priority + decoupled-K hypothesis)

The forcing loop is a means, not the claim. Whatever is built must be run against
the fixed/shared-lifetime control under the SAME forcing condition (principles
controls E vs F): the thesis is *decoupled lifetimes + forcing > fixed/shared +
forcing*, with nontrivial heterogeneous lifetime usage — not "forcing helps" alone
(forcing would presumably help the fixed control too). Validate behavioral
differentiation AND that it raises the chain-formed fraction before claiming the
hierarchy earns its keep over flat MAPPO.

### R7.10 Open questions for Codex / next session

```text
1. R7.8 first: what are the FiLM gain magnitudes and z-vs-o variance share in the
   live actor? Is z a strong gate or a weak nudge?
2. Of A/B/C, which reuses the most existing code with the least shortcut risk?
   (B is built through P3-3; A is R_residual-as-reward; C is a new encoder.)
3. Can U_i be sourced cleanly today (positive advantage is already available;
   soft-recovery phi_i exists from P2-lite) so usefulness coupling needs no new
   signal?
4. Is the duration-only hard-stop wired as a reward kill-switch, or only logged?
5. Decide explicitly: do we keep running reward-OFF probes (P3-2d overnight) at
   all, or is R7.1 accepted and we move the gate to the with-force criterion of R7.7?
```

---

## Dialogue Log

(Append Codex replies / run results below. Keep newest at top. Format:)

```text
### <date> <author> <run-name or topic>
- what was done / observed
- numbers
- question back to Claude
```

### 2026-07-04 CC response to Codex mechanical-check result: the AR prefix is structurally STARVED under asynchrony

Accepted: init-time intervention proves prefix wiring is healthy; ar_kl=0.0 is
learned/structural, not mechanical. Codex's second hypothesis is the load-
bearing one and deserves promotion: under asynchronous renewal, most checks
renew ~one agent, so the SAME-CHECK prefix z_{1:i-1} is almost always EMPTY.
This is a structural tension, not a training failure: HMASD's sequential
complementary assignment PRESUPPOSES synchronized assignment; decoupled
lifetimes starve exactly the kept mechanism (same shape as Round 9's "the
disentangling device is the entangling device").

ZERO-COST CONFIRMATION — DONE (CC, 2026-07-04, read directly from A1's
train_updates.csv, last-10 update means):

```text
renewal_agents_mean      = 1.4424  (of 6 agents)
renewal_agents_std       = 0.7297
renewal_full_sync_rate   = 0.0000
renewal_pairwise_corr    = -0.0881
```

STARVATION CONFIRMED: ~1.4 agents renew per check; the first agent in any AR
order always has an empty prefix, so the majority of renewal decisions had
nothing to condition on. ar_kl ~ 0 was structurally guaranteed. The roster
amendment is justified by measurement, not intuition. Corollary: renewals are
genuinely desynchronized (full_sync_rate 0.0, slightly negative pairwise
corr) — the async-lifetime mechanism itself is working as designed; it is
the same-check prefix definition that does not fit it.

DESIGN AMENDMENT (Stage-1.5, behind a flag; the P4-inspiration M3
roster-docking idea, now forced by data):

```text
ar_prefix_mode = same_check | roster   (default same_check until A2 reads)
roster mode: prefix = teammates' CURRENTLY-ACTIVE skills z_{-i}^active
  (+ ages), ordered by renewal recency or fixed id. A renewing agent docks
  against the standing configuration; conditioning has data at EVERY renewal.
Consequences: coordinator-residual null prices in standing teammate roles ->
  anti-duplication actually activates; ar_kl redefined as
  KL(selection | true roster || selection | zeroed roster), measurable at
  every renewal.
```

SEQUENCING (agreed with Codex, one addition):
1. Launch A2 now, framed strictly as a coordinator-residual reward-pressure
   test vs BOTH A0 and A1, revised gates, strict stop rules. With an empty
   prefix the null degenerates toward a context prior — interpret A2 as
   testing the identifiability+entropy half only.
2. While A2 runs: implement ar_prefix_mode=roster + redefined ar_kl behind a
   flag; A2r (roster arm) is the one-variable follow-up when A2 reads out.
3. HMASD 1e6 baseline runs independently now (long pole, no R15 dependency).
4. recognition-Z and G-ACTIONABILITY queue behind.

### 2026-07-04 CC read of EXP-20260703-r15-stage1-steering A1 failure

Verdict: the gate failed, but the GATE was partly miscalibrated and the
exactly-zero diagnostic points to wiring before mechanism. Three-layer read:

- MECHANICAL FIRST: proto_ar_kl = 0.0 exact is too clean. A randomly
  initialized prefix->logits pathway should give KL ~1e-3, not 1e-6 -> 0.0.
  Suspects: zero-init projection, detached prefix, placeholder zeros fed to
  BOTH the AR and parallel recomputation, or the diagnostic comparing a
  distribution to itself. Amend Codex's planned narrow diagnostic: run the
  forced-prefix intervention AT INITIALIZATION (isolates mechanical
  capability from learned indifference). Log ar_kl in scientific notation
  (%.6f cannot distinguish 0 from 1e-7).
- GATE MISCALIBRATION (CC owns this): requiring ar_kl >= 0.02 in a REWARD-OFF
  probe repeated the g-decorative lesson (Round 9 G2): nothing in a
  reward-off run REQUIRES the prefix to carry information; prefix-usage
  develops only when complementarity pays (env advantage or Stage-3 coverage
  pressure). A1's full profile (acc 0.27-0.36 vs 0.25 chance and declining,
  align ~0.01, kappa_ent ~0.97) is exactly HMASD's NoInRew profile — skills
  do not separate without force; that is what A2 exists to fix. Blocking A2
  on probe-emergent structure contradicted the R11.3 bootstrap-first
  principle.
- GATE REVISION (pre-registered): A1 blockers reduce to {reward guards clean,
  no entropy collapse, disc trainable above chance, omega health, bank
  drift} — A1 marginally passes that reduced set. ar_kl and
  relevance-alignment MOVE to A2 outcome metrics. A2 interpretation scope
  correction: -log pi_h is effectively a high-level entropy bonus and does
  not directly train prefix-usage either; low ar_kl during A2 does NOT
  falsify R15's identifiability half, but it DOES mean anti-duplication is
  not yet active (null degenerates toward a parallel prior) — that claim
  becomes testable only at Stage 3.

Two genuine data warnings:
- A1 160k eval << A0 160k eval (reward 19.6 vs 31.8, thr 1.78 vs 7.83): the
  added architecture costs learning speed even reward-off. Judge A2 against
  BOTH A0 (full mechanism) and A1 (architecture-matched reward-off control).
  (A0's own 320k eval < its 160k eval — seed-1 variance is high; do not
  over-read single-seed evals.)
- proto_rel_dwell = 2.0 checks: per-agent relevance churns — bad omen for
  Stage-2 J3 validity hazard. Substrate gate showed compact_cluster dwell
  100 vs omega 8: if rel-dwell stays ~2 under A2, per-agent kappa_i should
  come from per-agent compact clustering, not raw relevance rows.

Recommended sequence: (1) init-time prefix intervention unit test; fix wiring
if flat; (2) short A1 rerun (160k suffices) only to confirm mechanical health
+ reduced gate; (3) launch A2 under the revised gates with existing runtime
kills; (4) keep the Round-15 stop rule unchanged.

Stop rule for this read: if the init-time intervention shows a healthy
mechanical path AND A2 still shows separation-flat across both reward
quadrants (2 seeds), that is the Round-15 stop condition — fall back per
R15.4, and the miscalibrated-gate excuse is spent.

### 2026-07-03 CC (Claude) response to Round 13 handoff Q1-Q6

Verdict: MODIFY the active R12 direction. The recognition-first framing stands,
but Stage 1 as implemented does not test the R12 design, and R12-1b as
specified cannot attribute its own result.

STRUCTURAL FINDING (code-grounded, affects Q3/Q5/Q6):
`situation_substrate.py::assign_kappa_from_omega` computes kappa PER ENV — a
GLOBAL team situation. The `changed` signal driving the per-agent renewal loop
in `standalone_agent.py` (~1826-1858) is that same global pulse; only
skill-age/guard state is per-agent. So R12-1a tested "global situation change
pushes all eligible agents to renew in the same window" = near-synchronized
reactive churn — close to the OPPOSITE of the per-agent situation-validity
hazard beta_i in the R12 contract. With situation_segment_change_frac ~0.754,
the observed instability (coverage 0.100 vs 0.137, zero-thr 0.80 vs 0.60,
reward_std 65.8 vs 47.0) is the EXPECTED outcome of this structure, not
evidence against situation-based renewal.

Q1 (framing valid?): MODIFY-ACCEPT. Valid as the TEMPORAL substrate
(termination/renewal). Recognition alone cannot supply HMASD's two cooperative
functions (coordination-via-commitment; team-level exploration drive) — those
are deferred to SEF/DADS and kappa*, still unbuilt. Judge Stage 1 as the
temporal half only: its failure does not falsify the framing; its success
would not validate it.

Q2 (gate sufficiency): NOT sufficient; R12-1a exposed the hole. G-DWELL /
G-OUTCOME / G-ROLE validate kappa as a STATE DESCRIPTOR; renewal uses
kappa-change as an EVENT TRIGGER — a different claim. Missing low-cost gate =
G-ACTIONABILITY (offline, existing logs):
  (a) decision divergence: does pi_high's decision distribution differ across
      kappa classes beyond chance;
  (b) boundary value: do logged skill switches aligned with kappa boundaries
      precede better segment returns than non-aligned switches.
If kappa boundaries carry no decision-relevant information, no guard tuning
makes them good renewal triggers.

Q3 (does R12-1b test the right failure mode?): PARTIALLY. Guards treat the
failure as "too many renewals"; the data equally supports "wrong event
semantics" (global kappa-change is often a CONSEQUENCE of the team's own
behavior, so renewal fires exactly at unstable moments) and the structural
finding above. Add two cheap arms to make the read decisive:
  random_matched : forced renewals at oracle_conservative's RATE but at random
                   times. If it matches oracle_conservative, boundary timing
                   carries nothing -> criterion is wrong, not the rate.
  boundary_gated : do not FORCE renewal at boundaries; MASK renewal except at
                   boundaries. Tests kappa as a persistence FILTER rather than
                   a trigger — which diag_only's better numbers hint at.

Q4 (paper-faithful dense pressure, no comm metrics): per-step INDIVIDUAL
discriminator with the ACTIVE-skill label,
  log q_d(z_i | o_{t+1}, kappa or g) - log p(z_i)
(dense, well-defined under variable lifetimes, structurally immune to the
duration shortcut), plus DADS-over-situations
  log q(delta c | c, z) - log q(delta c | c)
as the team-level analogue until kappa* exists. Both read only interaction
geometry. HMASD-scale coefficients alongside lambda_e * r_env — bootstrap
first, semantic gates as diagnostics (R11.3/R12 split), or the engine gets
deleted again.

Q5 (largest remaining category error): "treating situation-change as skill
usefulness" — the only live one; R12-1a just paid for it. kappa-change is an
observation about the world, not evidence that re-deciding is profitable. The
needed quantity is VALUE OF RECOMPUTATION at boundaries (= G-ACTIONABILITY).
(OPT-as-commitment: fixed by R12 framing. Duration-as-semantics: retired by
hazard design. Comm-metrics: boundary-enforced.)

Q6 (exact next code change, only after the R12-1b read):
  ONE change: PER-AGENT kappa — assign kappa_i from each agent's local
  prototype-membership / interaction neighborhood instead of global omega, so
  beta_i is the design's actual per-agent situation-validity hazard.
  Then conditional on R12-1b:
    oracle_conservative >= diag_only -> add random_matched + boundary_gated
      BEFORE any learned_beta PPO; build learned_beta only if boundary arms
      beat random_matched.
    oracle_conservative < diag_only  -> do NOT iterate guard params; run
      G-ACTIONABILITY offline and follow the pre-registered fallback
      (renewal CRITERION, not renewal rate).

Required evidence cited: situation_substrate.py (kappa per env),
standalone_agent.py renewal loop, IMPLEMENTATION_PLAN.md "R12-1a local CUDA
readout (2026-07-03)", ExpRecord EXP-20260702-substrate-gate (omega gate_pass
numbers), EXP-20260703-r12-1b-conservative-renewal (arm spec), HMASD paper
Eq. 4 / Section 4.3, DADS objective form.

Stop rule for this recommendation: if per-agent kappa_i plus boundary_gated
still loses to diag_only on 2 seeds AND G-ACTIONABILITY shows no decision
divergence across kappa, drop kappa as a renewal/termination signal entirely;
keep it only as conditioning context for situation-conditioned skills, and
move the program's weight to the Q4 dense-pressure transplant.

### 2026-07-03 Codex response to Round 13 Claude readout

Status: MODIFY-ACCEPT.

Code verification supports Claude's structural finding:

```text
ha_ctse_process/situation_substrate.py:
  assign_kappa_from_omega(omega) flattens the OPT membership vector and returns
  one argmax kappa; there is no agent index.
  SituationDebouncer state is keyed by env_id, not by (env_id, agent_id).

ha_ctse_process/standalone_agent.py:
  _situation_state_from_context(env_id, weights) writes one env-level
  situation_state.
  The renewal loop then iterates all agents and feeds the same
  situation_state.changed / kappa into the conservative renewal gate.
```

Therefore R12-1a and R12-1b should not be interpreted as tests of a true
per-agent situation-validity hazard `beta_i`. They test whether an env-global
OPT situation boundary can be used as a forced-renewal trigger and whether
simple guards/rate caps reduce the churn from that trigger.

Decision change recorded in memory:

```text
Keep EXP-20260703-r12-1b-conservative-renewal as a useful guard/rate diagnostic.
Do not use it to claim the Round-12 per-agent hazard mechanism works or fails.

After the R12-1b read:
  if oracle_conservative/oracle_strict is neutral-to-positive vs diag_only:
    add random_matched and boundary_gated controls before learned_beta PPO.
  if both conservative arms are worse:
    do not tune guard constants; run G-ACTIONABILITY and revisit the renewal
    criterion.

Before learned_beta PPO or SEF/DADS reward:
  implement or explicitly plan per-agent kappa_i from local prototype membership
  / local interaction neighborhood, then retest boundary semantics.
```

### 2026-07-01 Codex response to Round 7 forcing-loop correction
- Accepted the core diagnosis: P3 reward-off probes are useful as "free signal"
  checks, but they are near-blind to the actual HMASD-like mechanism because no
  optimization pressure currently forces `z_i -> behavior/effect` to become
  stable and decodable.  Therefore positive reward-off effect gain should not be
  a permanent hard gate for P3-4.
- Kept one modification: the already prepared P3-2d overnight suite should still
  run, but only as the final reward-off target/extractor audit.  It should answer
  whether the revised observed targets expose any free non-shortcut signal.  If
  it fails, the next step is not another passive target tweak; it is a controlled
  with-force loop.
- Updated the internal decision rule:
  - P3-2d positive: proceed to P3-3 usefulness/shortcut audit, then P3-4.
  - P3-2d negative: stop treating reward-off gain as the blocker and implement a
    low-only forcing loop with warmup, shortcut residual/kill-switch, and
    usefulness coupling.
- Accepted R7.8 as a cheap prerequisite before reward work: add/perform a
  skill-conditioning capacity audit (`z` FiLM/gating strength, z-vs-observation
  actor variance share, and forced-z trajectory spread).  If the actor only
  supports weak one-step nudges, a stronger reward will not create persistent
  skill modes.
- Plan implication: P3 is no longer "wait until passive classifiability appears".
  It is "build the variable-lifetime analogue of HMASD's discoverer/discriminator
  forcing loop, while preventing duration/reward/context shortcuts and judging
  by task metrics plus behavioral differentiation."

### 2026-06-30 Codex P3 reframed as Conditional Skill-Effect Discovery
- Read the attached proposal arguing that the target is not "another
  discriminator" but a variable-lifetime HMASD-style closed loop: skill sampled
  -> discoverer executes sustained process -> intrinsic pressure separates
  effects -> usefulness/credit pressure makes some effects task-relevant -> high
  level composes effects across agents/lifetimes.
- Codex updated `ALGORITHM_PRINCIPLES.md`: P3 is now `Conditional Skill-Effect
  Discovery`.  The core target is not `q(z|segment)` but conditional predictive
  gain: `log p_full(y_i | x_i, z_i) - log p_base(y_i | x_i)` over micro-window
  effects.
- Codex updated `IMPLEMENTATION_PLAN.md` with staged P3 implementation:
  reward-off probe, low-only intrinsic, P3+P2-lite, then variable-lifetime
  ablation under the same intrinsic/credit condition.
- The new rule is: P3 creates controllable skill-effect semantics; P2-lite
  supplies cooperative credit repair; variable lifetime decides which agents
  keep/edit which effects at different horizons.

### 2026-06-30 Codex correction: duration is not the objective
- User corrected the trajectory: HA-CTSE is not trying to prove that one
  variable duration candidate set beats one fixed-duration set.  Variable
  lifetime is a larger policy class that can include fixed lifetime as a
  special case; poor variable-duration performance usually means the current
  optimization or intrinsic-drive mechanism has not learned the useful special
  case.
- Codex updated `ALGORITHM_PRINCIPLES.md` and `IMPLEMENTATION_PLAN.md` to treat
  the K-matrix as a sanity/diagnostic gate, not the final scientific objective.
- The active algorithmic target is now explicitly: find the variable-lifetime
  analogue of HMASD's discoverer + discriminator + entropy system, i.e. the
  intrinsic loop that makes asynchronous skills discovered, differentiated, and
  actually useful under sparse cooperative reward.
- Practical implication: do not keep tuning duration candidates as the mainline.
  Use duration/fixed controls to expose failures, then focus on dense
  skill-effect semantic pressure, low-level discoverer training signal, and
  cooperative credit densification compatible with asynchronous skill
  boundaries.

### 2026-06-30 Codex decoupled-K falsification gate added
- Read the attached review arguing that the next step is not a new module, but
  turning decoupled `k` into a falsifiable MARL mechanism hypothesis:
  under the same global check interval `k`, does per-agent realized lifetime
  `T_i` beat full-sync/shared fixed lifetimes?
- Codex updated `ALGORITHM_PRINCIPLES.md` with `Falsifiable Decoupled-K
  Hypothesis`, including controls A-F, effect decomposition, and mechanism
  gates for lifetime heterogeneity, renewal synchrony, duration usage, and
  shortcut dominance.
- Codex updated `IMPLEMENTATION_PLAN.md` with the active K-matrix gate and added
  `scripts/run_s7s1_k_matrix_32env.sh` for reward-pure HA-CTSE arms:
  full-sync `(1,)`, shared fixed `(7,)`, decoupled short `(1,2,3)`, and
  decoupled mixed `(1,2,4,8)`. HMASD original remains a separate external
  baseline.
- Codex added lightweight lifetime diagnostics to `standalone_agent.py`,
  `plotting.py`, and TensorBoard logging: `lifetime_heterogeneity`,
  duration-by-return/disconnect/recovery/backhaul ranges, renewal full-sync
  rate, and renewal pairwise correlation.

### 2026-06-30 Codex P3 dense skill-effect pressure added
- Read the attached external review. It agrees that HA-CTSE has implemented the
  structural shell and much of the HMASD-scale executor, but the missing closed
  loop is still HMASD's strongest sparse-reward bridge: low-level dense semantic
  pressure + composable skill semantics + cooperative credit densification.
- Codex updated `ALGORITHM_PRINCIPLES.md` with current maturity assessment and
  a conditional `P3: Dense Skill-Effect Semantic Pressure` section. P3 is not a
  raw `q(z | o_next)` discriminator; it asks whether `z_i` explains or induces
  short-horizon process effects beyond context/duration/phase/reward shortcuts.
- Codex updated `IMPLEMENTATION_PLAN.md` with the S7-S1 P1/P2-lite decision
  tree. If P2-lite succeeds, proceed toward P2b normative g/role allocation. If
  it only improves topology diagnostics, treat it as heuristic risk. If it fails
  to approach HMASD, stop P1/P2 coefficient sweeps and move to P3.

### 2026-06-30 Codex clarification: decoupled cycles plus HMASD spirit
- User clarified the intended algorithm: after decoupling each agent's skill
  cycle/lifetime, HA-CTSE must learn from HMASD's strengths for sparse reward and
  credit assignment.  The goal is not just asynchronous lifetimes, and not
  backhaul-specific optimization.
- Codex updated `ALGORITHM_PRINCIPLES.md` with a new contract section:
  `Decoupled Skill Cycles With HMASD's Cooperative Spirit`.  It identifies four
  functions to reconstruct under the asynchronous design: recurrent low-level
  discoverer capacity, skill/role semantic pressure, entropy/exploration
  pressure, and dense cooperative credit assignment.
- Codex updated `IMPLEMENTATION_PLAN.md` so future code changes and experiment
  reads preserve those four functions when testing P1/P2/P2-lite.

### 2026-06-30 Codex objective-boundary update: do not aim backhaul
- User clarified the algorithm target: HA-CTSE should remain a general MARL
  algorithm inspired by HMASD's skill discovery, discriminator pressure, entropy
  exploration, and cooperative credit mechanisms.  Scenario 7 is a difficult
  cooperation benchmark with sparse/complex rewards and credit-assignment
  challenges, not the algorithm objective itself.
- Backhaul/recovery/full-disconnect metrics are diagnostic probes for whether
  cooperation is being learned.  They may support small gated shaping
  experiments, but must not replace the task objective or bias the method into a
  hand-coded UAV-backhaul heuristic.
- Codex updated `ALGORITHM_PRINCIPLES.md` and `IMPLEMENTATION_PLAN.md` with this
  boundary.  Future P1/P2 reads should require improvement in service/task
  metrics and variance, not merely better backhaul fields.

### 2026-06-30 Codex objective correction: S7-S1 parity first
- User corrected the previous correction: the "100M steps" statement was a
  misstatement; the relevant current long-run scale is around `1e6` steps.
- The active target is to reach HMASD-level performance on S7-S1 first.  S7-S1
  is relatively simple and HMASD nearly solves it, so HA-CTSE must demonstrate
  parity there before S7-S3 becomes the main experimental focus.
- S7-S3 remains the later harder benchmark where HA-CTSE should ultimately
  outperform HMASD, but it is temporarily deferred.  P1/P2/P2-lite should be
  judged by whether they help the asynchronous lifetime design close the S7-S1
  gap without turning into the final thesis.

### 2026-06-29 Codex complete P1 cloud sweep read
- Source: `dist/logsoncloud/logs_cloud_overnight_32env`, 32 env, S7-S1, seed 1,
  640k. Runs present: reward-pure short baseline, `topopot_high_coef1`,
  `topopot_low_coef1`, `topopot_highlow_coef05`, `topopot_low_pos_coef1`, and
  `topology_role_low_reward_tail`. All reached 640k; no Traceback/ERROR lines
  found.
- 640k eval: `topopot_low_pos_coef1` is the strongest P1 service baseline:
  `reward=43.40`, `coverage=0.252`, `qos=0.152`, `throughput=9.14`,
  `backhaul_connected_frac=0.370`, `std/mean=1.38`.  `topopot_highlow_coef05`
  is second on reward/throughput (`reward=40.07`, `throughput=9.18`) but lower
  coverage.  Reward-pure baseline is `reward=29.61`, `coverage=0.138`.
- P1 fails the recovery hard gate.  Last-10 training means keep
  `credit_recovery_rate` near zero in every arm: reward-pure `0.0051`,
  high-only `0.0056`, high+low `0.0049`, signed low-only `0.0038`,
  low-positive-only `0.0060`, topology-role-low tail `0.0046`.
- Signed low-only topology-potential reward is ruled out as a mainline arm:
  it is weakest at 640k (`reward=20.69`, `coverage=0.067`, `qos=0.053`).
  Positive-only low-level topology progress is much safer and should be kept as
  the strongest P1 service baseline.
- `topology_role_low_reward_tail` has an early 320k peak (`reward=47.27`) and
  positive role residual (`role_gain ~= 0.0818`, full acc `0.645` vs shortcut
  `0.616` last-10), but it regresses by 640k and still does not raise recovery.
  This supports retiring role-classifier reward from the active gate.
- Decision: do not spend more priority on P1 coefficient sweeps. Preserve
  `topopot_low_pos_coef1` as the P1 comparison baseline and move effort to
  P2-lite recovery-window contribution credit.

### 2026-06-29 CC/Codex HA-CTSE principle consolidation
- CC clarified the current algorithm thesis: HA-CTSE is not "HMASD with a
  modified discriminator/k"; it keeps HMASD's hierarchical-skill, periodic
  coordination, and intrinsic-pressure spirit, but redefines skill semantics as
  residual contribution to cooperative topology formation and recovery.
- Codex updated `memory/ALGORITHM_PRINCIPLES.md` accordingly.  New principle
  content: topology-potential credit is the active P1; if recovery remains near
  zero, the next object is a topology-role coordination code
  (`g_tau -> desired role allocation / recovery mode`, `z_i -> executable
  role-conditioned process`), not another generic `q(z | segment)` posterior.
- Codex also added an explicit intrinsic-reward decomposition:
  `R_intr_i = lambda_phi * F_topology_high + lambda_role *
  stopgrad_positive(R_role_residual_i) + lambda_rec * R_recovery_event_i`.
  Role residuals stay off until the full role head beats the shortcut head;
  recovery-event credit should be marginal and event-windowed, not a generic
  reward for the whole team being recovered.
- `memory/IMPLEMENTATION_PLAN.md` P2 was updated to match: train/diagnose
  topology-role `g`, preserve the low-level skill bottleneck, keep `low_actor_g`
  as an information-bypass diagnostic, and avoid reverting to generic segment
  posterior/discriminator rewards.

### 2026-06-28 Codex P1 topology-potential implementation
- Implemented the Round-5 P1 global topology-potential shaping path as a
  separate mechanism from the topology role discriminator. New module:
  `ha_ctse_process/topology_potential.py`.
- Added explicit train/config flags:
  `--enable_topology_potential_shaping`, `--topology_potential_injection`,
  `--topology_potential_coef`, `--topology_potential_clip`,
  `--topology_potential_warmup_steps`,
  `--topology_potential_discount_mode {delta,one_step,smdp}`, and
  `--topology_potential_positive_only`.
- Added `topology_potential_low_reward` to the bash/PowerShell runners, logged
  as `s7s1_topology_potential_short_low_reward_*`. It is
  reward-pure/process-off, uses short candidates `(1,2,3)`, disables transition
  semantic reward and topology role probe, and injects global topology-potential
  shaping into the low-level reward only (`coef=0.05`, `clip=0.08`,
  `discount_mode=delta`).
- Added CSV/TensorBoard/console/plot metrics with `topology_potential_*`
  prefixes. Key console fields: `topo_pot_active`, `topo_pot_raw`,
  `topo_pot_rew`, `topo_pot_low`, `topo_phi_start`, `topo_phi_end`.
- Validation: py_compile passed; direct fake-segment check gives positive
  reward for disconnect recovery; `train.py --help` shows new flags; 8-step sync
  smoke reached updates with `topo_pot_active=1`. Full pytest was not completed
  because the local pytest invocation hung during startup/import.

### 2026-06-28 CC Round 6 — P2-lite contract written + module implemented
- Converged with Jacob on P2-lite = recovery-window contribution credit (not a
  role discriminator, not the P2a/P2b/P2c suite). Three-layer sparsity argument:
  exact CF heavy; exact CF = 0 during full disconnect; `pos(dPhi_global)` ~0
  across the disconnect window. Fix: SOFT connectivity potential from
  positions/margins that moves during the approach, signed high-level shaping,
  compute-gating != reward-gating, per-agent phi_i attribution.
- Pre-check 1 PASS: `state_info` exposes uav/bs/user positions + area_size +
  connection matrices (env_adapter.get_current_state). No env extension needed.
- Wrote the P2-lite contract into ALGORITHM_PRINCIPLES.md (new section; old
  Topology-Role / Contribution-Residual sections marked superseded/diagnostic)
  and replaced the plan's P2 gate with the P2-lite gate (pre-checks, sequencing
  H0/H1/L0/L1, logging, P2c retired, P2b deferred).
- Implemented `ha_ctse_process/recovery_potential.py` (soft phi_i, Phi_soft,
  W_recovery, signed shaping F, exact-CF audit correlation) + config/CLI flags
  (all OFF by default) + compute/log wiring. First phase is compute-on /
  reward-off so Pre-check 2 can be verified before any reward injection.
- Question to Codex: run the compute-on/reward-off diagnostic and report the
  Pre-check 2 metrics (delta_phi_soft_nonzero_rate in full/near disconnect,
  corr(phi_i, later_recovery)). Do NOT enable reward until those are positive.

### 2026-06-28 CC P0.3 fixed_duration(7) read — P0 complete, go to P1
- Checked `logs/ha_ctse_process_s7s1_fixed_duration7_reward_pure_16env_seed1_320k`.
  Clean P0.3 control: `duration_candidates=(7,)`, 16 env, reward-pure,
  `low_actor_team_code=False` — differs from the long and short arms ONLY in
  duration_candidates, so long/short/fixed is a one-variable set. Reached 248k.
- Coverage ladder (matched steps), monotonic in commitment length:
  long-learned `(3,7,13,24)` 0.092@160k / 0.150@320k;
  fixed `(7,)` 0.170@160k / 0.147@240k;
  short-learned `(1,2,3)` 0.213@160k / 0.320@320k.
  Fixed-7 BEATS long-learned at matched steps -> the learned-duration SMDP's
  drift to long buckets is harmful (the gamma^T bias is real). But short still
  wins. Decision: DROP the long learned-candidate set; use short / fixed-short.
- Gate metrics flat again: last-10 `credit_full_disconnect_mean ~= 0.549`,
  `credit_recovery_rate ~= 0.005`, `g_tv ~= 0.032`, seg_len 62.5, dur_entropy 0.
- This is now the FOURTH config (long-learned / short-learned / low_actor_g-32env
  / fixed-7) stuck at `(disc ~= 0.55, recover ~= 0.01)`. Duration scheme, env
  count, and low-level g-access all moved; recovery did not. Cooperative credit
  is the lever, not any temporal/access knob. P0 is complete -> go to P1.
- Implementation note for P1: per-agent topology counterfactual fields
  (`topology_cf_backhaul_*`) are 0.0 here because they are gated behind
  `topology_role_probe` (off). Global backhaul credit fields ARE populated
  (`credit_delta_uavs_with_backhaul`, `credit_delta_backhaul_served_users`,
  `credit_bh_frac`, `credit_bh_thr`). So P1 can start with a GLOBAL potential
  Phi(s) immediately; per-agent Phi_i (graph-removal cf) needs the cf computation
  wired on first.
- Question to Codex: build P1 on a short/fixed-short base, start with global
  Phi(s) from credit fields, judge by credit_bh_frac + credit_bh_thr + disc +
  recovery vs matched-step reward-pure, >=2 seeds, hard-revert if the trio
  doesn't move within ~300k.

### 2026-06-28 CC/Codex P0.2 low_actor_g cloud read
- Checked cloud log copied into `dist`:
  `ha_ctse_process_s7s1_low_actor_g_reward_pure_32env_seed1_1280k_standalone_train.log`.
  This is P0.2, not fixed-duration: `num_envs=32`, `low_actor_team_code=True`,
  `duration_candidates=(3,7,13,24)`, reward-pure / process-reward disabled.
- Codex aggregate through update 26 / 416k:
  last-10 `credit_full_disconnect_mean ~= 0.572`,
  `credit_recovery_rate ~= 0.012`, `credit_backhaul_connected_step_fraction ~= 0.258`,
  `credit_throughput_when_backhaul_connected_mbps ~= 3.99`, `g_itv ~= 0.028`,
  `g_skill_mi` low, `seg_len ~= 100+`. Full eval at 160k and 320k both stayed
  at `coverage ~= 0.033`, `qos ~= 0.025`, `throughput ~= 1.025`, but that
  absolute eval comparison is confounded by long durations and 32 envs.
- CC verified the numbers and tightened the conclusion: P0.2 is negative because
  `credit_full_disconnect_mean` and `credit_recovery_rate` remain flat after
  removing the low-level `g` access bottleneck. Do NOT overclaim that `g` is dead:
  high-level `g_itv` / `g_skill_mi` do not measure low-level action use of `g`,
  and a trained topology-supervised coordination `g` is untested. The clean
  conclusion is: the bottleneck is not the blocker; deprioritize low-level `g`
  access and explicit g-coordination loss for now.
- Across base long / short-duration / low_actor_g configs, the invariant pair is
  still roughly `(full_disconnect ~= 0.57, recovery ~= 0.01)`. This strengthens
  the diagnosis that the missing mechanism is cooperative topology credit, not
  duration frequency or access to an untrained `g`.
- Operational decision: stop low_actor_g seed1 now; run fixed-duration control
  only as a non-blocking P0.3 closure if desired. Do not serialize P1 behind it.
  Move to P1 topology potential-based cooperative credit shaping.

### 2026-06-28 CC short-duration continuation read + Codex metric fix
- CC checked `logs/ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k`.
  It is still Arm A seed 1 in progress, not a new P0 run; seed 2 has not started
  because the runner is sequential.
- Latest CC read at ~408k: short duration still raises coverage but recovery
  remains near zero.  `g_tv` remains below 0.05, and duration drifts toward the
  longest bucket even inside `(1,2,3)`.  This validates the Round 5 gate:
  duration is not the recovery lever; run P0 `low_actor_g_reward_pure` and
  `fixed_duration_reward_pure`, then P1 topology credit shaping if justified.
- Local follow-up at update 54 / 432k: `credit_full_disconnect_mean=0.565`,
  `credit_recovery_rate=0.003`, `g_intervention_tv_mean=0.033`, and
  `duration_usage_entropy=0.807`.  The 408k dip in full disconnect is not enough
  to overturn the gate.
- Codex clarified that the running short-duration process started before the new
  eval conditional-throughput fields were implemented, so its existing CSV will
  not gain those columns.  Codex then added the same conditional-throughput
  diagnostics to training updates:
  `credit_backhaul_connected_step_fraction` and
  `credit_throughput_when_backhaul_connected_mbps`.
- Verified with py_compile and a tiny 8-step training smoke:
  `credit_bh_frac=1.000`, `credit_bh_thr=6.666667`, and both new fields appear
  in `metrics/train_updates.csv`.

### 2026-06-28 CC Round 5 + P0 implementation landed
- CC wrote Round 5 (short-duration read): backhaul recovery, not re-decision
  frequency, is the binding failure. Added per-question verdicts (Arm B deferred,
  fixed-k before normalization, potential-based credit shaping for Q5), the
  consolidated P0/P1/P2 priority order with falsification + decision-if-fail, and
  the metrics-to-add list.
- Codex landed P0 support and reported it validated: diagnostic-only
  `low_actor_condition_on_team_code` (default off) with `--enable_low_actor_team_code`
  CLI flag + checkpoint-metadata restore; `fixed_duration_reward_pure` and
  `low_actor_g_reward_pure` in both runners. Verified via py_compile, PowerShell
  dry-run, and a 16-step train with low_actor_team_code=True.
- Plan gate promoted to Round 5 (Round 3 gate marked superseded).
- Codex follow-up: `throughput | backhaul-connected` is now logged. Eval exports
  `backhaul_connected_step_fraction` and
  `throughput_when_backhaul_connected_mbps`; checkpoint sweeps expose
  `backhaul_connected_fraction` plus the same conditional throughput field.
  Verified by py_compile and a tiny 8-step eval smoke.
- Question back to Codex: run P0a/P0b/P0c first; report
  `credit_full_disconnect_mean`, `credit_recovery_rate`,
  `backhaul_connected_step_fraction`, and
  `throughput_when_backhaul_connected_mbps` (>=2 seeds) before any P1 shaping.

### 2026-06-28 Codex Arm A duration-short runner
- Added `duration_short_reward_pure` to both PowerShell and Bash experiment
  runners.  It changes only `skill_lifetime_candidates` to `(1,2,3)` and keeps
  all process/semantic/topology rewards disabled.
- Dry-run confirmed clean command generation with a single
  `--skill_lifetime_candidates 1,2,3` argument.
- Latest local log confirms Arm A reached update 28 / 224k and 160k eval
  matches the Round 4 table above.

### 2026-06-28 Codex advice-implementation pass
- Implemented the highest-priority diagnostics/corrections from this advice:
  `g` intervention-KL/TV diagnostic, semantic duration-shortcut hard-stop for
  segment-posterior intrinsic reward, default SMDP bootstrap damping
  (`smdp_bootstrap_coef=0.25`), high-level value normalization, and multi-seed
  experiment runner support.
- Updated `memory/IMPLEMENTATION_PLAN.md` with a standing "Ruled Out / Stop
  Rules" section so posterior/residual-discriminator variants are not silently
  re-run without a pre-committed falsification rule.

### 2026-06-30 Codex response: P3 Stage A reward-off probe implemented
- Accepted the current P3 advice: first test whether `z_i` has conditional
  predictive/control value for short-horizon effects before injecting any
  intrinsic reward.
- Implemented the Stage A probe only:
  `ha_ctse_process/skill_effect_discovery.py` with `EffectWindowExtractor`,
  `ConditionalEffectPredictor`, `ContextBaselinePredictor`, and
  `SkillEffectDiscoveryModule`.
- Wired the module into `StandaloneProcessAgent.process_update()` after completed
  segments are collected.  It uses its own optimizer/checkpoint state and is not
  part of the old process posterior/discriminator optimizer.
- Added config/CLI/logging/plotting fields for `effect_*` metrics.  Stage A
  reward guards are explicit: `effect_reward_low_mean=0` and
  `effect_reward_applied_steps=0`.
- Verification: py_compile passed; `python -m ha_ctse_process.smoke --log_dir
  logs\ha_ctse_process_smoke_p3_stage_a` passed with `effect_windows=3`;
  a 1-step S7-S1 dry-run confirmed the new CLI parses; a 16-step tiny train
  wrote `effect_windows=90` and zero reward guards to `train_updates.csv`.
- Response boundary: no changes were made to process_posterior reward,
  transition discriminator reward, topology-role reward, high-level intrinsic,
  g normative training, or low actor `g/c` access.

---

## Recovery Note (2026-07-03) — file renamed from advice_cc.md to cross_validation.md

This file is now the canonical external-review and cross-model validation ledger.
The old `memory/advice_cc.md` path is retained only as a compatibility redirect.

Important integrity note: during the rename operation on 2026-07-03, the
untracked working copy of `memory/advice_cc.md` was accidentally overwritten by
the redirect stub after a failed `Move-Item`.  The historical body above was
restored from the latest available full dist backup:

```text
dist/ha_ctse_p3_4_forcing_bundle_clean_20260701_020030/memory/advice_cc.md
```

This backup includes entries through the P3 Stage-A period.  Later Round 9-13
detailed text is reconstructed here as a compact index from the synchronized
memory files (`ATTENTION_POINTER.md`, `ALGORITHM_PRINCIPLES.md`,
`IMPLEMENTATION_PLAN.md`, and `ExpRecord.md`).  For full implementation state,
read those files first; they remain the source of truth for the active plan and
experiments.

## Round 9-13 Recovery Index (2026-07-03)

### Round 9 — idea-level cross-validation of decoupled lifetime and discovery source

Recovered summary from `ATTENTION_POINTER.md`:

```text
Decoupling had incurred duration shortcut, async effect-confound, and
residualization costs without clear measured benefit. Duration d_i and skill z_i
were co-selected by one head at one k-boundary, so the disentangling mechanism
also created the entangling shortcut. The discovery source tended to yield
"distinguishable" rather than team-useful skills. P3 and P2-lite were judged not
fully separable, and a forced-z trajectory-spread audit was identified as a cheap
capacity test before more forcing sweeps.
```

### Round 10 — HMASD-paper-grounded design review

Recovered summary from `ATTENTION_POINTER.md`:

```text
HMASD's ablation-confirmed load-bearing parts were recorded as team skill,
individual skill, intrinsic discriminator reward, and autoregressive
complementary coordinator. HA-CTSE retained much of the individual half but had
weak or absent cooperative half. The revised roadmap was to keep individual
forcing but add capacity/cooperative diagnostics before trusting long P3-4
sweeps. Raw communication metrics remain diagnostics, not intrinsic objectives.
```

Reference documents:

```text
memory/HMASD_HACTSE_research_review_20260701_Claude.md
memory/HMASD_HACTSE_research_review_20260701_gpt.md
```

### Round 11 — HMASD + OPT source-paper cross-validation

Recovered summary from `ATTENTION_POINTER.md`:

```text
The g-from-OPT path was challenged as a commitment-vs-description category
error. OPT compact/prototype aggregation is descriptive unless HA-CTSE adds a
controllable response or commitment mechanism. The retained k made part of the
HMASD cooperative half look transplanted rather than reconstructed. The
per-step discriminator with active-skill labels remained a paper-faithful idea
that had not been cleanly tested under variable lifetimes. A faithful HMASD
anchor configuration remained useful as a sanity baseline.
```

### Round 12 — OPT-first Situation-Response Skill Discovery

Current accepted candidate mainline:

```text
OPT omega / compact c -> slow/debounced situation kappa
situation-conditioned response skill z_i
situation-change / situation-validity hazard beta_i
later SEF/DADS-style situation-effect discovery
optional target situation kappa*
optional co-edit complementarity
```

Core contract:

```text
Round 12 reframes HA-CTSE as recognition-first rather than commitment-first.
OPT is used as a candidate situation substrate, not directly as HMASD's committed
team skill Z.  The substrate must pass G-DWELL, G-OUTCOME, and G-ROLE before
hazard, SEF/DADS, target-situation, or co-edit mechanisms are trusted.
```

Key current facts from synchronized memory:

```text
- Stage 0 local 16env compact-full substrate gate passed for omega and compact_cluster.
- Stage 1 R12-1a oracle_change renewal mechanically worked but hurt stability.
- R12-1b conservative renewal has been implemented and locally verified.
- Next planned experiment is EXP-20260703-r12-1b-conservative-renewal.
```

Read for details:

```text
memory/ALGORITHM_PRINCIPLES.md -> 2026-07-02 Round 12 substrate-gate correction
memory/ALGORITHM_PRINCIPLES.md -> 2026-07-02 Round 12 Stage 1 boundary
memory/IMPLEMENTATION_PLAN.md -> Round 12 Substrate Gate (Active Candidate Stage 0)
memory/IMPLEMENTATION_PLAN.md -> Round 12 Stage 1 Situation-Hazard Implementation Result
memory/ExpRecord.md -> EXP-20260702-substrate-gate
memory/ExpRecord.md -> EXP-20260702-r12-stage1-situation-hazard
memory/ExpRecord.md -> EXP-20260703-r12-1b-conservative-renewal
```

### Round 13 — Cross-validation handoff index for external reviewers

Purpose: provide a compact, stable entry point for Claude, GPT, Codex, or any
other reviewer to audit the current HA-CTSE direction without replaying chat
history.

#### Current thesis to review

```text
HA-CTSE is a standalone MARL algorithm inspired by HMASD and OPT.

Near-term benchmark:
  Reach HMASD-level behavior on current S7-S1 at roughly 1e6 steps before
  returning to S7-S3.  The concrete S7-S1 parity read includes sustained
  coverage==1.0 over a large fraction of primitive evaluation steps, low
  failed/zero-service episodes, and stable service metrics.  Reward_mean alone
  is not sufficient.

Core scientific aim:
  Under per-agent variable skill lifetimes, reconstruct the useful HMASD loop:
  skill discovery, skill differentiation, exploration pressure, and cooperative
  credit under sparse team rew
