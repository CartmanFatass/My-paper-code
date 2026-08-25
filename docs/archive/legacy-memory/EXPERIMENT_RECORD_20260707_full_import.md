# HA-CTSE Experiment Record

This file is the coordination ledger for HA-CTSE experiments.  Before launching
any local or cloud run, add an entry here so code changes, run location, expected
outputs, and interpretation stay aligned.

## Protocol

Each experiment must record:

```text
Experiment name:
Created at:
Planned location: local | cloud | both
Command/script:
Code snapshot / changed files:
Purpose:
Hypothesis:
Controls / comparison:
Metrics to read:
Meaning of possible outcomes:
Stop / continue rule:
Result status: planned | running | completed | stopped | invalid
Result summary:
Next decision:
```

Rules:

```text
1. Do not launch a new comparison run without an ExpRecord entry.
2. Do not interpret a run only from reward_mean; include the diagnostic fields
   named in the entry.
3. If code changed after a run was launched, mark the run's code snapshot as
   stale before comparing it with newer runs.
4. Local runs are for fast wiring / early structural signals. Cloud runs are for
   performance gates.
5. For P3, reward-off probe, low-only intrinsic, P3+P2-lite, and variable
   lifetime ablation are separate experiments.
6. The dashboard is for fast experiment-state review. Detailed dialogue,
   cross-model rationale, accepted/rejected advice, and modification metadata
   belong in `memory/cross_validation.md`; link to those entries rather than
   duplicating the full discussion here.
7. If an experiment result causes code, plan, principle, runner, package, or
   interpretation changes, record the experiment outcome here and the
   modification metadata in `memory/cross_validation.md`.
```

## Experiment Dashboard

| ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-20260705-r21-team-intent | completed — NEGATIVE + AUTOPSIED (true-objective-failure) | R21 | cloud CUDA (seed1, `dist\logs_cloud_r21_team_intent_64env`) | ExpManager → autopsy CC implementer | read+autopsy done 2026-07-06 | `dist\ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip` | Autopsy (`memory\R21_AUTOPSY_REPORT.md`): B=aligned-real (disc-chance genuine, not a bug); A=Z near-inert (forced-Z KL≈0.002 at random-init AND final → never made actionable); C=truncation-contaminated + K≈episode confound. Primary=true-objective-failure (no `I(Z;ξ)` actionability term). Regression is policy-path, NOT churn. Stop rule holds: no seed2 / no sweep. |
| EXP-20260705-hmasd-currentenv-baseline | DROPPED as blocking (user 2026-07-06: baseline is solid/well-tested) | HMASD baseline | — | — | — | — | Not a blocking premise. At most ONE appendix/sanity run for the paper; do NOT spend GPU re-verifying. |
| EXP-20260707-r23-next-mechanism-matrix | PARTIAL (local 32env, killed externally at arm1 18/20) — arm1 q_A gain RISING (POSITIVE); arm2/arm3 not run | R23-next | local CUDA 32env (`logs_r23_next_mechanism_matrix_local`) | ExpManager (CC) | interim read done 2026-07-07 | `scripts/run_r23_next_mechanism_matrix_local_cuda.ps1` | **INTERIM POSITIVE**: arm0 (arch-only control) completed 20 updates + eval (cov 0.10→0.23, qos 0.075→0.184, thr 3.7→11.8, cov_eq1=0 at 320k). **arm1 (q_A probe, reward off)** reached update 18/288k then the run was killed externally (status "killed", no traceback): q_A `residual_gain` RISES monotonically u12→u18 (+0.004→+0.018→+0.023→+0.064→+0.074→+0.090→+0.097; accF 0.333 vs accP 0.236 at u18) with forced-Z KL stable ~0.045 and z_usage_entropy healthy ~0.98 — the actionability-LEARNING signal g-info structurally could NOT produce (validates the T2 SCALE/FORM verdict + the q_A pivot). team_disc still ~chance (~0.22) — the q_D audit (arm3) that would explain this did NOT run. CAVEAT: single seed, probe-only (no policy feedback yet), 288k not 320k; arm0 vs arm1 task differs partly from RNG desync (extra q_A module draws) so arm0 is not a bit-matched control. NEXT: resume arm2 (q_A reward) + arm3 (q_D audit); optionally re-run arm1 to full 320k. Runner successor to the g-info line. **OPS NOTE (2026-07-07): both the first run (killed arm1 u18) and the arm2/arm3 resume (killed arm2 u9) died from OS OOM, not code — diagnosis: local box has 31.6 GB RAM, a single `--num_envs 32 --collector_backend subproc` arm holds ~14.5 GB (2.8 GB trainer + 32×~0.47 GB workers), OS+apps ~14.5 GB → only ~2–3 GB headroom, so eval/plot/checkpoint spikes trigger a clean SIGKILL (status "killed", no traceback; variable kill points 18 vs 9 rule out a fixed harness limit). FIX: rerun local arms at `-NumEnvs 16` (~7 GB → ~10 GB headroom) or `--collector_backend sync`. arm2+arm3 relaunched at NumEnvs 16.** **arm2 (q_A reward, 16env) COMPLETED 40 updates (2026-07-07) — STRONG POSITIVE mechanism: q_A `residual_gain` climbs to +0.222 (accF 0.412 vs accP 0.191 at u40; vs arm1 probe's +0.097), forced-Z KL RISES 0.059→0.070 over training, z_usage_entropy stays healthy ~0.98 → the actionability objective WORKS as a q_A reward (the exact thing g-info could not do). Task (CAVEATED — arm2 is 16env vs arm0 32env, single seed): arm2@160k cov 0.303 / qos 0.167 / thr 8.11 (N=20) vs arm0@160k cov 0.100 — ~3× coverage, encouraging but env-count-confounded; arm2@320k eval is UNRELIABLE (N=3, truncated by a Windows subproc-teardown access-violation `0xC0000005` at process exit — cosmetic spawn shutdown race in collectors.py, NOT training; all 40 updates + 160k eval are intact). cov_eq1_step_frac=0 still. team_disc_acc still ~chance → arm3 q_D audit is the needed next read (relaunched solo, 16env). The teardown segfault made the runner exit before arm3, hence the "failed" status; arm2 data is complete.** T2 g-info gradient audit (`scripts/r23_ginfo_grad_audit.py`) = SCALE/FORM: g-info grad into the Z path is <2% of PPO and self-stalling (not a wiring bug) → main line switches to **q_A residual** (cross-entropy, first-order). 4 arms 320k: arm0 arch-only / arm1 q_A probe (reward-off) / arm2 q_A reward (coef 0.02, gated on residual_gain>0) / arm3 reward-off q_D target audit over {s_next,joint_action,joint_effect,delta_omega}×H{10,20,50}. q_D reward OFF everywhere (amplifier-not-starter). All default-off; new modules `assignment_actionability.py`, `team_effect_targets.py`; tests 12 pass; full suite 245 pass (4 pre-existing failures, stash-confirmed). Nothing committed. Pending: user launches on GPU. |
| EXP-20260706-r23-actionable-team-intent | completed 320k seed1 — MIXED: R23-0 arch PASS, R23-1/R23-2 FAIL (null) | R23 | cloud CUDA seed1 (`dist\logs_cloud_r23_actionable_team_intent_64env`, 3 arms, 320k) | ExpManager (CC) | read done 2026-07-06 | `scripts/run_r23_actionable_team_intent_cloud_64env.sh` | 320k mechanism-depth read, single seed, all arms clean (exit 0, no kill). **R23-0 arch capacity PASS in-training**: forced-Z skill KL 0.04–0.08, z_assignment_itv 0.03–0.10 (~20–50× the R21 ~0.002 band), sustained → Z→ξ link restored. **R23-1 objective FAIL/null**: g-info active (loss ~-2e-4, negligible), MI flat, objective-ON arm MI (0.012) < objective-OFF arm (0.024) → coef 0.02 too weak; the KL elevation is the static architecture, not the learned objective. **R23-2 disc FAIL**: team_disc_acc ≈ chance (0.14–0.25 vs 1/6), prior entropy pinned ln6 → ξ moves but no recoverable joint-effect signature. **R23-3**: gate mechanics correct (gated_off at KL 0, applied at KL≥floor), reward magnitude ~0 (disc chance), guard armed no-kill, no task effect. **Task**: cov_eq1_step_frac=0.0 all arms/checkpoints, cov 0.11–0.21, zero_thr_step ~0.71–0.75. Blocker moved from "Z can't move ξ" (fixed) → "ξ doesn't map to a recoverable joint effect." Next: stronger/annealed actionability objective OR Option-B residual q_A; revisit the q_D effect target/timescale; extend depth + seed2 only if a stronger objective shows a rising MI trend. |
| EXP-20260705-r16-5-continuation | completed | R16.5 | remote/cloud CUDA | ExpManager | completed 960k read | `dist\logs_cloud_r16_5_continuation_64env` | coef=0.05 seed2 is mechanism-clean but not parity; coef=0.1 retry underperforms; stop R16.5 floor tuning. |
| EXP-20260704-r19-team-transition-64env | partial read / mechanism-negative | R19 | remote/cloud CUDA | ExpManager | reward arm completion if available, otherwise stop/review | `dist\r_19log\logs_cloud_r19_team_transition_64env` | Probe ran to 960k with negative `team_t_mi`; reward arm snapshot to 224k is weak. Treat R19 team-transition residual as not yet validated. |
| EXP-20260704-r16-5-coef01-entfloor | completed | R16.5 | local CUDA | ExpManager | completed 960k read | `logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_233759\seed1\a2r_roster_reward_coef01_entfloor` | PASS-SCAFFOLDED: performance stabilized, lifetime heterogeneity floor-supported. |
| R16.5 P2 eval-mode cells | launch-ready | R16.5 diagnostic | local CUDA | ExpManager | update_60/update_120 x deterministic/stochastic | `scripts\run_r16_5_p2_eval_modes.ps1` | Diagnose train/eval action-mode divergence before final R16.5 interpretation. |
| EXP-20260704-r16-a2r-remote-parallel | partially read / weak-negative | R16 | remote/cloud | review pass / ExpManager | no broad rerun planned | `dist\a1r_roster_probe`, `dist\a2_samecheck_reward`, `dist\a2r_roster_coef005` | Roster AR remains decorative; only narrow checks if explicitly needed. |

## Active / Planned Experiments

### EXP-20260705-r21-team-intent

Experiment name: `r21_team_intent`

Created at: 2026-07-05

Amended at: 2026-07-05 after CC pre-launch review and user instruction.

Planned location: cloud CUDA direct. The user explicitly removed the local
probe requirement for this batch. Run 64 env, 960k, seed 1 first; add seed 2
only after the 320k mechanism gate is healthy.

Command/script:

```bash
bash scripts/run_r21_team_intent_cloud_64env.sh --dry-run

EXPERIMENTS=r21_z_probe,r21_z_reward \
SEEDS=1 \
TOTAL_TIMESTEPS=960000 \
NUM_ENVS=64 \
DEVICE=cuda \
bash scripts/run_r21_team_intent_cloud_64env.sh
```

Cloud package:

```text
dist\ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip
dist\HA_CTSE_R21_R22_OVERNIGHT_UPLOAD_README.md
```

Package boundary note: this runtime zip intentionally excludes `memory/`.
Memory remains local collaboration state and should be shared separately only
for cross-validation/review, not for server execution.

Optional local debug runner only if cloud fails before producing usable logs:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r21_team_intent_local_cuda.ps1 `
  -Experiments r21_z_probe,r21_z_reward `
  -Seeds "1" `
  -TotalTimesteps 160000 `
  -NumEnvs 16 `
  -Device cuda `
  -TeamIntentK 48 `
  -TeamDiscCoef 0.05
```

Launch wiring proof recorded 2026-07-05: local dry-run emits K=48,
team_disc_coef=0.05, guard kill, coef005 base, duration floor disabled. The
Linux cloud runner was statically checked on Windows because local `bash` is
not installed; on the cloud, run `bash scripts/run_r21_team_intent_cloud_64env.sh
--dry-run` before launch and paste its output here.

```text
--enable_prototype_response_skills --enable_prototype_disc_reward
--prototype_disc_reward_coef 0.05
--team_bridge_type stochastic
--reward_ratio_guard_mode kill
--enable_team_intent --team_intent_k 48
probe arm:  --enable_team_disc_probe
reward arm: --enable_team_disc_reward --team_disc_coef 0.05 --team_disc_clip 2.0
```

Code snapshot / changed files:

```text
ha_ctse_process/team_intent.py
ha_ctse_process/config.py
ha_ctse_process/standalone_agent.py
ha_ctse_process/train.py
ha_ctse_process/plotting.py
tests/r21_team_intent_test.py
scripts/run_r21_team_intent_cloud_64env.sh
scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
train_multiproc_config_1.py
```

Purpose: test whether restoring a sampled, held team intent `Z` plus atomic
full-team AR reassignment can reconstruct the HMASD-style cooperative pressure
while preserving asynchronous individual lifetimes between `Z` boundaries.

Hypothesis: compared with the stabilized R16.5 base, R21 should make the team
coordination channel non-decorative: `z_assignment_itv` should rise, `z_usage`
should avoid collapse, team discriminator signal should be trainable in a
healthy band, and task metrics should not regress at the first structural gate.

Controls / comparison:

```text
Primary comparison: completed 64-env coef005 continuation run in
`dist\logs_cloud_r16_5_continuation_64env`. That branch is the S-base:
prototype discriminator reward coefficient 0.05, duration floor inactive,
duration usage entropy clean. R21 cloud runner matches scenario/preset/agents/
network/env count/rollout/k/timesteps/eval settings and changes only the Z
team-intent system.
```

Metrics to read:

```text
z_usage_entropy
z_usage_max_frac
z_dwell
z_decisions_per_update
z_advantage_mean
z_advantage_std
z_advantage_var
z_boundary_trunc_rate
z_boundary_trunc_rate_dur3
z_boundary_trunc_rate_dur7
z_boundary_trunc_rate_dur13
z_boundary_trunc_rate_dur24
z_assignment_itv
z_entropy_floor_active
team_disc_acc
team_disc_loss
team_disc_resid
team_disc_reward_env_ratio
team_disc_reward_applied_steps
combined_intrinsic_env_ratio
combined_intrinsic_env_ratio_over05_count
combined_intrinsic_env_ratio_guard_active
combined_intrinsic_env_ratio_kill_triggered
coverage_eq1_step_frac
zero_throughput_ep_frac
coverage / qos / throughput
```

Meaning of possible outcomes:

```text
Positive structural read:
  Z is used without collapse, boundary truncation is low, and team-disc signal
  is non-degenerate. Proceed to reward-on / longer comparison.

Negative structural read:
  Z remains decorative or collapses. Do not tune task-specific rewards; revisit
  pi_Z pressure, AR assignment path, or held-Z lifetime assumptions.

Task regression with healthy structure:
  mechanism exists but objective/scale may be wrong. Read reward ratios and
  compare reward-off vs reward-on before changing architecture.
```

Pre-registered gates:

```text
320k structural gate:
  - `z_assignment_itv` must be clearly nonzero and materially above decorative
    band seen in old g diagnostics; if it is ~0, stop R21 and inspect pi_Z/AR
    wiring before any longer run.
  - `z_usage_entropy` must stay above 50% of uniform entropy:
    entropy > 0.5 * ln(num_team_codes).
  - `z_usage_max_frac` should stay below 0.80; above that means Z collapse.
  - `z_boundary_trunc_rate` should be well below 1.0; per-duration bucket
    truncation must be especially low for 13 and 24. If long buckets truncate
    heavily, the K/lifetime interaction invalidates duration-collapse reads.
  - `team_disc_acc` should be above random but below saturation; random is
    about 1/num_team_codes. Early ~1.0 is leak suspect.
  - Reward arm ratio: `team_disc_reward_env_ratio` should usually sit in
    [0.05, 0.50]. Warn-mode guard logs pathology; do not hide it.
  - Stacked reward ratio: `combined_intrinsic_env_ratio` must be read alongside
    `proto_disc_reward_env_ratio` and `team_disc_reward_env_ratio`; it catches
    the case where each intrinsic is individually under guard but their sum is
    too large. It counts only actually applied reward components, not reward-off
    discriminator previews. Default R21 guard mode is kill.

Performance gate at 960k:
  - Must improve or at least not regress versus stabilized entfloor on
    coverage, zero_throughput_ep_frac, and coverage_eq1_step_frac.
  - A positive R21 claim requires both task improvement and healthy Z/team-disc
    mechanism metrics; reward_mean alone is insufficient.
```

Stop / continue rule:

```text
If the 320k structural gate fails, stop before burning to seed 2 or cloud.
If probe is structurally healthy but reward arm is unstable, inspect ratio and
team-disc overfit before coefficient changes. No coefficient sweep until the
first R21 read is recorded.
If reward arm fails the improvement gate on two seeds while mechanism metrics
are healthy, run one K_team sweep (24, 6) before escalating to the R18.3 matrix
read.
```

Result status: completed — NEGATIVE on both gates (seed 1, 2026-07-06)

Logs read: `dist\logs_cloud_r21_team_intent_64env\...\seed1\{r21_z_probe,
r21_z_reward_coef005}`. Both arms finished cleanly (exit_code=0, full 30
updates/960k, no guard/kill/NaN/traceback). num_team_codes=6 (random acc=0.167),
team_intent_k=48, S-base plumbing matched (proto_disc_reward_coef=0.05).

Structural (mechanism) gate — FAIL:
```text
- z_usage_entropy ~0.96-0.99 (normalized), z_usage_max_frac ~0.20-0.26 (<0.80)
  -> PASS: Z is NOT collapsed. But near-uniform usage = Z sampled ~uniformly,
     not selected discriminatively.
- z_assignment_itv ~0.0016-0.0051 across the whole run -> FAIL. Essentially
  zero; this is the pre-registered "decorative" failure ("if it is ~0, stop
  R21 and inspect pi_Z/AR wiring"). Same pathology as old g diagnostics.
- team_disc_acc oscillates 0.13-0.29 around random 0.167; prior entropy pinned
  at ln6=1.79; team_disc_residual ~0 (+/-0.01) -> FAIL. Team discriminator is
  at chance: Z carries no recoverable team-behavioral signature. Reward-on
  (coef005) does not lift it above chance.
- z_boundary_trunc_rate per-bucket: dur13 ~0.98-1.00, dur24 ~0.79-0.90 (also
  dur3/dur7 ~0.85-1.0) -> FAIL the "long buckets especially low" condition;
  duration-collapse reads are invalidated by heavy truncation.
- Reward ratios healthy/in-band: team_ratio ~0.02-0.08, proto_ratio ~0.03-0.07,
  combined ~0.06-0.13; no over05/kill triggered. Plumbing is safe but the
  signal it carries is meaningless.
```

Performance gate at 960k — FAIL (regresses vs S-base ref reward 71.7 /
coverage 0.417 / cov_eq1_step_frac 0.0164 / zero_thru_ep 0.50):
```text
probe  960k: reward 23.9, cov 0.098, qos 0.063, thr 6.19, cov_eq1_step_frac 0.0,
             zero_thru_ep 0.70  (peak was 800k: cov 0.163)
reward 960k: reward 33.3, cov 0.145, qos 0.090, thr 7.05, cov_eq1_step_frac 0.0,
             zero_thru_ep 0.60  (peak was 640k-800k: cov 0.22)
```
cov_eq1_step_frac is pinned at exactly 0.0 at every eval point; reward_std ~50-63
(huge, > mean). Caveat: the S-base reference was a warm continuation run, so the
absolute task gap is partly unfair; but cov_eq1=0.0, worsening zero_thru_ep, and
the comparison-independent mechanism failures make a positive R21 claim
impossible. Reward-on is marginally less bad than probe but within noise.

Interpretation: Z is simultaneously DECORATIVE (no recoverable team info; itv≈0;
team_disc at chance) and HARMFUL (task below S-base). Consistent with the
"kappa dual-use churn" / atomic-variation caution: atomic AR reassignment at Z
boundaries injects skill churn without coordination content. This is the
pre-registered "Negative structural read" branch.

AUTOPSY (2026-07-06, CC implementer; full: `memory/R21_AUTOPSY_REPORT.md`):
```text
Audit B (team-disc data contract): aligned-real. team_codes/next_states appended
  lockstep per env-step (train.py:3016-3028); label = pre-step held Z, state =
  post-step global state = correct q_D(Z|s_next); no leakage; prior updated after;
  reward pre-update (no_grad before opt.step). Positive/negative control
  (held-out split): separable->1.00, independent->0.174≈chance. So team_disc_acc
  ≈chance is a GENUINE no-signal read, NOT a bug.
Audit A (forced-Z actionability): Z near-inert. Forced-Z skill KL≈0.00165 at
  random-init and ≈0.00223 at final (matches live z_assignment_itv≈0.002-0.005);
  duration KL similarly ~0.001. random-init≈final => Z was never made actionable
  (NOT "trained out"). ~0.5 argmax churn at ~0.002 KL = flat under-confident
  policy nudged by noise, not coordination.
Audit C (truncation): truncation-contaminated. z_boundary_trunc_rate_durX recorded
  only at Z boundaries; team_intent_remaining=48*10=480 vs episode=500 => ONE
  terminal Z boundary/episode => long-duration buckets ≈1.0 near-tautologically;
  duration-collapse reads invalid. K=48≈episode=50 intervals => ~one Z commitment
  per episode (two-clock degenerated to one-clock). Churn is once-per-episode
  near-terminal => NOT the regression cause (probe arm regressed too).
CLASSIFICATION: primary true-objective-failure (no I(Z;ξ|c,ω) actionability term);
  secondary effectively-unwired assignment head + truncation-contaminated metrics;
  ruled out label-misaligned; regression is policy-path (forced AR-roster/Z-cond),
  not churn. No code bug found -> no fix proposed. No training run.
```

Next decision: STOP per stop rule — do NOT launch seed 2, do NOT run a K sweep
or coefficient sweep on this design. Before any further team-intent work, inspect
the pi_Z pressure / AR assignment path (why z_assignment_itv≈0 and team_disc
never beats chance) — the mechanism, not the coefficient, is broken. Feeds the
R22 two-clock ELBO question of whether sampled Z can be made non-vacuous at all.

### EXP-20260706-r23-actionable-team-intent

Experiment name: `r23_actionable_team_intent` (arms `r23_arch_only`,
`r23_1_action`, `r23_3_reward_coef005_floor005`).

Created at: 2026-07-06 (design `memory/R23_ACTIONABLE_TEAM_INTENT.md`).

Read at: 2026-07-06 (ExpManager / CC), logs
`dist\logs_cloud_r23_actionable_team_intent_64env` (unzipped from
`dist\logs_cloud_r23_actionable_team_intent_64env.zip`).

Location: cloud CUDA (autodl), 64 env, seed 1 only, 320k steps/arm, eval at
160k and 320k (20 episodes each). All three arms `state=finished exit_code=0`,
no NaN, no reward-ratio kill.

Shared config: S7-S1, 6 agents, `--z_assignment_residual_gain 0.5`,
`--enable_team_intent --enable_team_disc_probe`, `--team_intent_k 8`
(Choice-1), `--skill_lifetime_candidates 1,2,3,4`, prototype-disc reward on
(coef 0.05, warmup 20k), process/outcome/topology/transition rewards disabled.
Arm deltas: `r23_1_action` adds `--enable_g_info_objective --g_info_coef_skill
0.02 --g_info_warmup_steps 20000`; `r23_3_reward` adds that plus
`--enable_team_disc_reward --team_disc_coef 0.05 --team_disc_actionability_floor
0.05`.

Purpose/hypothesis: test the R23 correction — restore the Z→ξ link (residual
gain) so that (a) an actionability objective can raise I(Z;skill) and (b) the
team discriminator gets a real joint-effect signature to amplify, unlike R21
where Z was decorative (forced-Z KL ≈0.002).

Result (MIXED — one PASS, two FAIL; 320k mechanism-depth, single seed):

- R23-0 architecture capacity — **PASS in-training.** forced-Z skill KL
  (`g_itv_kl_skill`) ≈ 0.04–0.08, `z_assignment_itv` ≈ 0.03–0.10 across all
  arms/updates — ~20–50× the R21 decorative band (~0.002), sustained the whole
  run. The `z_assignment_residual_gain` fix genuinely restored Z→ξ capacity.
- R23-1 actionability objective — **FAIL / null.** g-info objective confirmed
  active (`g_info_objective_active=1`, `coef_scale=1`) but loss only ~-2e-4
  (negligible). `g_info_skill_mi` and forced-Z KL are FLAT across all 10
  updates — no rising trend. The objective-ON arm (`r23_1_action`, MI ≈0.012)
  is LOWER than the objective-OFF arm (`r23_arch_only`, MI ≈0.024): at coef
  0.02 the differentiable MI term is too weak to move MI; the entire KL
  elevation over R21 is the STATIC ARCHITECTURE, not the learned objective. The
  pre-registered "forced_Z_KL ↑" criterion is NOT met.
- R23-2 team-disc recovers Z — **FAIL.** `team_disc_acc` ≈ 0.14–0.25 around
  chance (1/6 = 0.167), prior entropy pinned at ln6 ≈ 1.79, in every arm
  including the reward arm. Predicted fail branch: ξ moves with Z (KL up) but
  produces no recoverable joint future-effect signature → discriminator stays
  an amplifier with nothing to amplify.
- R23-3 team-disc reward — **gate mechanics correct, effect ~zero.**
  `team_disc_reward_gated_off=1` at update 1 (forced-Z KL 0), then applied
  update 2+ (KL 0.077 ≥ floor 0.05). `team_disc_reward_mean` ≈ -0.0006…+0.0001
  (disc at chance → residual ~0). Env-ratio guard armed (`guard_active=1`) but
  never killed. No task effect distinguishable from noise.
- Task (320k, preliminary): `coverage_eq1_step_fraction = 0.0` for ALL arms at
  BOTH checkpoints (parity bar untouched, same as R21). coverage 0.11–0.21
  (arch 0.117 / action 0.122 / reward 0.207 at 320k), qos ~0.10–0.12,
  `zero_throughput_step_fraction` ~0.71–0.75, `env_reward_mean` flat/low
  (~0.04–0.09). No parity progress.

Interpretation: R23 cleanly SEPARATED two things the R21 autopsy conflated. The
architecture correction WORKS (Z→ξ capacity restored). But that is not
sufficient: the weak differentiable actionability objective adds nothing on top,
and the Z-moved ξ still yields no distinguishable joint effect, so q_D stays at
chance. Blocker moved from "Z can't move ξ" (fixed) → "ξ doesn't map to a
recoverable joint effect."

Next decision (none launched; needs user authorization): (1) the actionability
objective needs to actually bite — much larger `g_info_coef_skill` with anneal,
and/or switch to Option-B residual q_A (log q_A(Z|ξ) − log prior), before any
conclusion that "actionability can't be learned." (2) Independently interrogate
the q_D effect target/timescale — whether S7-S1 ξ (skill/duration assignment)
maps to ANY distinguishable future joint state at the current horizon; R23-2's
chance disc may be a target/timescale problem, not only an objective one.
(3) Do NOT extend depth (960k) or add seed 2 on THIS coef until a stronger
objective shows a rising MI trend at 320k. Keep separate from R21/R19/R16.5.

### EXP-20260705-hmasd-currentenv-baseline

Experiment name: `hmasd_currentenv_s7s1_6agent_baseline`

Created at: 2026-07-05

Planned location: cloud CUDA, preferably separate from the R21 cloud slot.

Command/script:

```bash
bash scripts/run_hmasd_currentenv_baseline_cloud_64env.sh --dry-run

SEEDS=1,2 \
TOTAL_TIMESTEPS=1000000 \
NUM_ENVS=64 \
DEVICE=cuda \
bash scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
```

Cloud package:

```text
dist\ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip
dist\HA_CTSE_R21_R22_OVERNIGHT_UPLOAD_README.md
```

Code snapshot / changed files:

```text
train_multiproc_config_1.py  # logging-only baseline support: --n_agents and parity eval diagnostics
scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
```

Purpose: verify the current S7-S1 6-agent environment parity bar for the
original HMASD algorithm. The user expects HMASD to reach stable high coverage
around 1e6 steps; HA-CTSE claims need this current-code anchor.

Hypothesis: HMASD original should show much higher `coverage_eq1_step_fraction`
than current HA-CTSE mechanisms by ~1e6 steps, validating that S7-S1 is a
solvable cooperative benchmark.

Controls / comparison:

```text
algorithm=hmasd_original
scenario=energy
preset=S7-S1
n_agents=6
num_envs=64
eval protocol: 20 episodes every 160k
```

Metrics to read:

```text
coverage_eq1_step_fraction
coverage_eq1_episode_fraction
zero_throughput_episode_fraction
throughput_gt5_step_fraction
parity_step_metric_fallback_used
parity_step_metric_sample_count
coverage / qos / throughput
reward_mean / reward_std
```

Meaning of possible outcomes:

```text
HMASD reaches the expected high coverage_eq1 fraction:
  S7-S1 remains a valid near-term parity benchmark; HA-CTSE must close the
  mechanism gap before S7-S3 claims.

HMASD does not reach high coverage by ~1e6 on this current 6-agent setting:
  Recalibrate the parity target in ALGORITHM_PRINCIPLES and compare HA-CTSE
  against the measured current-env HMASD curve, not historical expectation.
```

Stop / continue rule:

```text
Run seed 1 and seed 2 to ~1e6 unless a structural crash occurs. Do not tune
HMASD algorithm code. Only logging/eval-diagnostic support is allowed.
```

Result status: launch-ready

Result summary: no run yet.

Next decision: launch in parallel with R21 if cloud capacity permits. Paste one
eval line proving the parity diagnostics are present before treating baseline
results as comparable. If `parity_step_metric_fallback_used=1`, interpret
step-fraction parity metrics as episode-level fallback rather than true
per-step samples.

### EXP-20260704-r16-5-coef01-entfloor

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r16_5_a2r_roster_coef01_entfloor`

### EXP-20260705-r16-5-continuation

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r16_5_entfloor_continuation`

### EXP-20260704-r19-team-transition-64env

Experiment name: `r19_team_transition_remote_64env_960k`

Created at: 2026-07-04

Planned location: cloud / remote servers, preferably split by arm.

Command/script:

```bash
bash scripts/run_r19_team_transition_64env.sh
```

Package:

```text
dist/ha_ctse_r19_team_transition_64env_bundle_20260704_213707.zip
dist/HA_CTSE_R19_REMOTE_UPLOAD_README.md
```

Purpose:

```text
Run R19 team-transition validation without mixing in the already-running R16
roster-docking four-arm sweep.  R19 asks whether the DADS-style
situation-transition residual adds the missing team exploration/stabilization
engine on top of the A2 individual coordinator-residual path.
```

Hypothesis:

```text
If R19 is the right replacement for HMASD's killed team discriminator engine,
then `a2_plus_t` should show sustained positive `team_transition_mi_mean`,
healthy `team_transition_self_frac`, controlled reward scale, and better task
readout than matched A2, especially lower zero-throughput and higher coverage.
```

Controls / comparison:

```text
Primary R19 arms:
  a2_plus_t_probe  heads trained/logged, team-transition reward off.
  a2_plus_t        team-transition reward on, coef=0.05.

Matched A2 control:
  Use an already-running same-settings A2 same-check reward run if available.
  If not available, run the optional `a2_baseline` arm from the same R19
  script.  Do not use R16 roster arms as the A2 baseline.
```

Fixed settings:

```text
S7-S1 energy, n_agents=6, num_envs=64, total_timesteps=960000, cuda,
rollout_length=500, skill_interval=10, candidates=(3,7,13,24),
eval_interval=160000, eval_episodes=20, opt_num_prototypes=4.
```

Metrics to read:

```text
R19 mechanism:
  team_transition_samples
  team_transition_mi_mean
  team_transition_mi_on_self
  team_transition_mi_on_change
  team_transition_self_frac
  team_transition_missing_frac
  team_transition_reward_high_mean
  team_transition_reward_applied_steps
  team_transition_reward_env_ratio
  team_transition_reward_renewal_corr

A2 individual path:
  proto_acc
  proto_disc_residual_mean
  proto_disc_reward_env_ratio
  proto_skill_usage_entropy_by_kappa

Task / safety:
  coverage_eq1_step_frac
  zero_throughput_ep_frac
  coverage
  qos
  throughput
  reward_mean/std
  skill_entropy
  duration_entropy
```

Stop / continue rule:

```text
Run to 320k unless there is a real Python traceback, NaN/OOM, or reward scale
violation (`team_transition_reward_env_ratio > 1.0` for 5 consecutive
post-warmup updates). Continue to 960k only if mechanism metrics are alive and
task readout is not clearly worse than matched A2 at 320k.
```

Result status: partial read / mechanism-negative

Result summary:

```text
Package built 2026-07-04:
  dist\ha_ctse_r19_team_transition_64env_bundle_20260704_213707.zip
  entries=138
  size=999676 bytes

Static verification:
  required R19 files present:
    ha_ctse_process/situation_transition.py
    scripts/run_r19_team_transition_64env.sh
    tests/r19_team_transition_test.py
    docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md
    envs/, hmasd/, routing_protocols.py, config_1.py
  excluded:
    __pycache__, *.pyc, *.pyo, *.pt, *.pth,
    accidental mixed R16/R19 runner `run_r16_r19_overnight_64env.sh`
  bad entry count=0

Local dry-run:
  not executed because local Windows environment has no `bash` executable.
  Required first server command remains:
    bash scripts/run_r19_team_transition_64env.sh --dry-run

Downloaded cloud logs read 2026-07-05:
  root: dist\r_19log\logs_cloud_r19_team_transition_64env
  seed: 1

Arm completion:
  a2_baseline_samecheck_reward_coef01:
    finished, exit_code=0, 960k complete, no traceback/NaN/OOM found.
  a2_plus_t_probe_reward_off:
    finished, exit_code=0, 960k complete, no traceback/NaN/OOM found.
  a2_plus_t_reward_coef005:
    downloaded snapshot reports state=running and contains updates through
    224k plus the 160k eval only; no traceback/NaN/OOM in downloaded log.

Matched eval read:
  baseline 960k:
    reward=54.003165, coverage=0.333333, qos=0.178205,
    throughput=11.400000, backhaul_frac=0.365600,
    zero_throughput_ep_frac=0.600000, coverage_eq1_step_frac=0.000000.
  probe reward-off 960k:
    reward=23.786741, coverage=0.115000, qos=0.072848,
    throughput=5.700000, backhaul_frac=0.272800,
    zero_throughput_ep_frac=0.600000, coverage_eq1_step_frac=0.000000.
  reward-on 160k:
    reward=22.442625, coverage=0.100000, qos=0.061031,
    throughput=1.864259, backhaul_frac=0.234100,
    zero_throughput_ep_frac=0.750000, coverage_eq1_step_frac=0.000000.

Mechanism read:
  baseline has team_t_samples=0 as expected.
  probe at 960k: team_t_samples=3136, team_t_mi=-0.042034,
    team_t_self=0.923, team_t_rew=0.0, team_t_ratio=0.0.
    Last-5 mean team_t_mi=-0.064172, team_t_self=0.9312.
  reward-on snapshot at 224k: team_t_mi=-0.044873, team_t_self=0.921,
    team_t_rew=-0.018776, team_t_ratio=0.016.
    Last-5 mean team_t_mi=-0.052448, team_t_self=0.9226,
    team_t_ratio=0.0142.

Interpretation:
  The reward-off probe fails the pre-registered mechanism gate because
  `team_t_mi` is not positive or sustained; it is consistently negative.
  `team_t_self` is within the nominal [0.6, 0.95] band but near the upper
  end, meaning most samples are self/unchanged and the residual is not
  producing useful positive team-transition information.  The reward-on arm
  is not complete in the downloaded snapshot, but the early signal follows
  the same negative-MI pattern and its task readout is not better than the
  matched baseline.
```

Next decision:

```text
Do not treat the current R19 team-transition residual as validated.  Unless a
later complete reward-on log contradicts the snapshot with sustained positive
`team_t_mi` and task gains, stop coefficient sweeps on this mechanism.  Use
this as evidence that the current team-transition target/head is not yet the
missing HMASD-style team engine; compare with R21 team-intent restoration
instead of broadening R19 blindly.
```

### EXP-20260704-a2-plus-t

Experiment name: `a2_plus_t_team_transition`

Created at: 2026-07-04 (pre-registered by CC from the final R19 plan)

Planned location: local CUDA

Status: IMPLEMENTED / VALIDATED / TRIGGER-BLOCKED. Codex built the module
parallel to A2; this arm still launches ONLY via the OUT-OF-GAS branch of the
A2 outcome matrix in `EXP-20260703-r15-stage1-steering`, or explicit user
decision after the A2 320k read. Implementation reference (source of truth):
`docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md`.

Implementation receipt 2026-07-04:

```text
Code:
  ha_ctse_process/situation_transition.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  scripts/run_r15_stage1_local_cuda.ps1
  tests/r19_team_transition_test.py

Implemented contract:
  clean team-transition module;
  own Adam optimizer and checkpoint state;
  kappa + active-skill-count xi inputs only;
  missing kappa intervals dropped with missing_frac logging;
  current-rollout closed intervals only;
  self transitions included;
  high-level-only segment reward accumulation;
  probe/reward flags default off;
  team_transition_* metrics in CSV/TensorBoard/console/plots;
  a2_plus_t_probe and a2_plus_t runner arms added.

Validation:
  pytest tests\r19_team_transition_test.py -q -> 6 passed
  pytest tests\r14_prototype_response_test.py -q -> 13 passed
  AST compile for touched HA-CTSE files -> ast_compile_ok
  run_r15_stage1_local_cuda.ps1 -Experiments a2_plus_t_probe,a2_plus_t -DryRun -> passed
  tiny reward-on smoke -> completed; team_t_samples/reward/ratio logged
  checkpoint payload includes team_transition and team_transition_opt
  eval load of the smoke final checkpoint -> passed

Residual note:
  py_compile was not used as the decisive check because existing Windows
  __pycache__ permissions can fail independently of source syntax; AST compile
  was used instead.
```

Settings: identical to A2 (16 env, 320k, S7-S1 energy, seed 1 then 2),
plus `--enable_team_transition_probe --enable_team_transition_reward`
(coef 0.05, clip 2.0, warmup 20000). ONE variable vs A2.

Optional pre-arm: `a2_plus_t_probe` (heads on, reward off) if the A2 read
is ambiguous — verifies `team_transition_mi_mean > 0` exists to inject.

Gates (vs A2, matched steps, last-third means + 320k eval):

```text
MECHANISM: team_transition_mi_mean > 0 sustained;
  team_transition_self_frac in [0.6, 0.95] (R19.2 regime check);
  team_transition_reward_env_ratio in [0.05, 0.50] post-warmup.
TASK (IMPROVEMENT REQUIRED, not non-regression — this arm exists to fix the
  exploration deficit; neutrality vs A2 is a FAIL):
  coverage UP and zero_throughput_ep_frac DOWN vs A2;
  reward_std/mean <= 1.15 x A2.
RUNTIME KILLS: reward_env_ratio > 1.0 for 5 consecutive post-warmup
  updates; 160k eval zero_throughput_ep_frac > A2 + 0.15.
STOP RULE: task gate fails on 2 seeds while mechanism metrics are healthy
  -> the exploration deficit is not situation-steering-shaped; do NOT sweep
  coef; escalate to the R18.3 matrix read (kappa*-style atomic commitment
  may be needed even in the coverage-bound corner, or kappa classes are too
  coarse at N=4).
CHURN PRECURSOR: team_transition_reward_renewal_corr reported,
  informational here (no live hazard), MANDATORY input to the Stage-2 go
  decision.
```

### EXP-20260704-r16-a2r-remote-parallel

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r16_a2r_roster_remote_parallel_32env`

### EXP-20260703-r15-stage1-steering

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r15_stage1_coordinator_residual`

### EXP-20260704-r16-a2r-overnight-local

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r16_a2r_roster_overnight_local_cuda`

### EXP-20260703-r14-stage1-prototype-selection

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r14_stage1_prototype_selection`

### EXP-20260703-r12-1b-conservative-renewal

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r12_1b_conservative_renewal`

### EXP-20260702-r12-stage1-situation-hazard

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r12_stage1_situation_hazard`

### EXP-20260702-substrate-gate

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `r12_opt_substrate_gate`

### EXP-20260702-p4-1b-grad-probe

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `p4_1b_g_info_grad_probe`

### EXP-20260701-g-info-objective-probe

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `round10_g_info_objective_probe`

### EXP-20260630-local-kmatrix-quick

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `local_s7s1_overnight_kmatrix_4env`

### EXP-20260630-p3-stage-a-probe

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `p3_conditional_skill_effect_reward_off_probe`

### EXP-20260630-p3-2b-reward-off-probe

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `p3_2b_group_balanced_effect_probe`

### EXP-20260630-p3-2c-intervention-probe

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `p3_2c_skill_use_intervention_probe`

### EXP-20260630-p3-2d-observed-effect-probe

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `p3_2d_observed_effect_reward_off_probe`

### EXP-20260701-p3-2d-overnight-suite

_Condensed 2026-07-06 (completed/abandoned)._ One-line outcome: see `ATTENTION_POINTER.md` → Experiment Pointers. Full record: `memory/backup_20260706/ExpRecord.md`.
- Experiment name: `p3_2d_overnight_reward_off_suite`

