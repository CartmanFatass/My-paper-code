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

| ID | Status | Stage | Location | Owner Role | Next Read | Key Logs / Package | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-20260705-r21-team-intent | packaged / launch-ready | R21 | cloud CUDA direct | Experiment Manager | 160k shape read, 320k mechanism gate, 960k task gate | `dist\ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip` | User chose direct cloud launch; K=48, team_disc_coef=0.05, coef005 matched base, duration floor off. |
| EXP-20260705-hmasd-currentenv-baseline | packaged / launch-ready | HMASD baseline | cloud CUDA | Experiment Manager | 1e6 eval x seeds 1,2 | `dist\ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip` | Current S7-S1 6-agent HMASD parity anchor; logs HA-CTSE eval parity metrics. |
| EXP-20260705-r16-5-continuation | completed | R16.5 | remote/cloud CUDA | Experiment Manager | completed 960k read | `dist\logs_cloud_r16_5_continuation_64env` | coef=0.05 seed2 is mechanism-clean but not parity; coef=0.1 retry underperforms; stop R16.5 floor tuning. |
| EXP-20260704-r19-team-transition-64env | partial read / mechanism-negative | R19 | remote/cloud CUDA | Experiment Manager | reward arm completion if available, otherwise stop/review | `dist\r_19log\logs_cloud_r19_team_transition_64env` | Probe ran to 960k with negative `team_t_mi`; reward arm snapshot to 224k is weak. Treat R19 team-transition residual as not yet validated. |
| EXP-20260704-r16-5-coef01-entfloor | completed | R16.5 | local CUDA | Experiment Manager | completed 960k read | `logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_233759\seed1\a2r_roster_reward_coef01_entfloor` | PASS-SCAFFOLDED: performance stabilized, lifetime heterogeneity floor-supported. |
| R16.5 P2 eval-mode cells | launch-ready | R16.5 diagnostic | local CUDA | Experiment Manager | update_60/update_120 x deterministic/stochastic | `scripts\run_r16_5_p2_eval_modes.ps1` | Diagnose train/eval action-mode divergence before final R16.5 interpretation. |
| EXP-20260704-r16-a2r-remote-parallel | partially read / weak-negative | R16 | remote/cloud | Reviewer / Experiment Manager | no broad rerun planned | `dist\a1r_roster_probe`, `dist\a2_samecheck_reward`, `dist\a2r_roster_coef005` | Roster AR remains decorative; only narrow checks if explicitly needed. |

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

Result status: launch-ready (cloud direct)

Result summary: no formal experiment yet. Implementation smoke only:
post-review implementation checks passed (`tests\r21_team_intent_test.py` 7/7,
AST parse of changed Python files, and `ha_ctse_process.train --help` import).
The 2026-07-06 Claude review response added R22-3 diagnostics/guards:
`z_decisions_per_update`, `z_advantage_mean/std/var`, and
`combined_intrinsic_env_ratio` with cumulative guard counters. These validate
wiring, not performance.

Next decision: launch cloud CUDA R21 probe/reward; read 160k `team_disc_acc`
shape first, 320k mechanism gate second, and 960k task gate only if mechanism
signals are non-degenerate.

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

Experiment name: `r16_5_a2r_roster_coef01_entfloor`

Created at: 2026-07-04

Planned location: local CUDA first; cloud optional only after local guard passes.

Command/script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r16_a2r_overnight_local_cuda.ps1 `
  -Experiments a2r_roster_coef01_entfloor `
  -Seeds "1" `
  -TotalTimesteps 960000 `
  -NumEnvs 16 `
  -Device cuda `
  -ContinueOnError
```

Optional remote backup command / not the active path (2026-07-04):

```bash
EXPERIMENTS=a2r_roster_coef01_entfloor \
SEEDS=1 \
TOTAL_TIMESTEPS=960000 \
NUM_ENVS=64 \
DEVICE=cuda \
LOG_ROOT=logs_cloud_r16_5_entfloor_64env \
bash scripts/run_r16_a2r_remote_32env.sh
```

Note: `run_r16_a2r_remote_32env.sh` is parameterized despite the historical
filename.  This 64-env CUDA command is now only a backup if local execution is
unavailable.  The active plan is a single local CUDA entfloor run, because this
is only one experiment and remote packaging would add operational overhead.
The entfloor arm still hardcodes `--reward_ratio_guard_mode warn`.

P2 eval-mode diagnostic commands:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r16_5_p2_eval_modes.ps1
```

Equivalent explicit commands:

```powershell
$py = "C:\Users\wu\.conda\envs\SB3\python.exe"
$src = "logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01"
$out = "logs\ha_ctse_r16_5_p2_eval_modes\run_20260704_142053"

& $py -m ha_ctse_process.train --config ha_ctse_process.config --mode eval --scenario energy --preset S7-S1 --seed 1 --n_agents 6 --skill_interval 10 --eval_episodes 20 --eval_action_mode deterministic --device cuda --resume_from "$src\standalone_process_core_update_60.pt" --log_dir "$out\update_60\deterministic"
& $py -m ha_ctse_process.train --config ha_ctse_process.config --mode eval --scenario energy --preset S7-S1 --seed 1 --n_agents 6 --skill_interval 10 --eval_episodes 20 --eval_action_mode stochastic --device cuda --resume_from "$src\standalone_process_core_update_60.pt" --log_dir "$out\update_60\stochastic"
& $py -m ha_ctse_process.train --config ha_ctse_process.config --mode eval --scenario energy --preset S7-S1 --seed 1 --n_agents 6 --skill_interval 10 --eval_episodes 20 --eval_action_mode deterministic --device cuda --resume_from "$src\standalone_process_core_update_120.pt" --log_dir "$out\update_120\deterministic"
& $py -m ha_ctse_process.train --config ha_ctse_process.config --mode eval --scenario energy --preset S7-S1 --seed 1 --n_agents 6 --skill_interval 10 --eval_episodes 20 --eval_action_mode stochastic --device cuda --resume_from "$src\standalone_process_core_update_120.pt" --log_dir "$out\update_120\stochastic"
```

Code snapshot / changed files:

```text
ha_ctse_process/config.py
ha_ctse_process/standalone_agent.py
ha_ctse_process/train.py
ha_ctse_process/plotting.py
scripts/run_r16_a2r_overnight_local_cuda.ps1
scripts/run_r16_a2r_remote_32env.sh
scripts/run_r16_5_p2_eval_modes.ps1
```

Purpose:

```text
R16.5 closing plan: stabilize the best known R16/S7-S1 peak from
`run_20260704_142053` without changing the roster objective, bootstrap
coefficient, duration candidates, low-level policy, or environment reward.
This tests CC's forensic diagnosis that the 480k peak decayed because of
slow high-level duration entropy collapse, not because the R16 arm never had
useful behavior.
```

Hypothesis:

```text
If the 480k->960k decay was driven by duration-head collapse, then the
default-off duration entropy floor should preserve heterogeneous lifetimes and
prevent the late eval collapse while keeping reward scale within guard.
```

Controls / comparison:

```text
Reference:
  logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01

Best known checkpoint:
  standalone_process_core_update_60.pt  (480k)

Late collapsed checkpoint:
  standalone_process_core_update_120.pt (960k)

Only intended variable:
  --enable_duration_entropy_floor
  --duration_entropy_floor_threshold 0.8
  --duration_entropy_floor_coef 0.05
  --duration_entropy_floor_warmup_steps 0
  --reward_ratio_guard_mode warn  # (Condition 1: warn-only mode for comparison)
```

Metrics to read:

```text
Peak/stability:
  eval coverage, reward_mean, zero_throughput_ep_frac, backhaul_connected_frac
  at 480k and 960k.

Entropy / lifetime:
  duration_usage_entropy
  duration_usage_max_frac
  duration_policy_entropy_norm
  duration_entropy_floor_active
  duration_entropy_floor_gap
  duration_entropy_floor_loss
  lifetime_heterogeneity
  renewal_agents_mean

Reward guard:
  proto_disc_reward_env_ratio
  proto_disc_reward_env_ratio_over05_count
  proto_disc_reward_env_ratio_guard_active
  proto_disc_reward_env_ratio_kill_triggered
```

Meaning of possible outcomes:

```text
PASS-CLEAN:
  960k eval holds >=80% of the reference 480k peak, duration_usage_entropy
  >= 0.8, AND duration_entropy_floor_active is transient (activates, then
  entropy self-sustains). The collapse was a fixable optimization artifact;
  heterogeneity-helps corollary stands. Use as stabilized A2r base.

PASS-SCAFFOLDED (CC Q2 taxonomy correction 2026-07-04 — this is NOT a fail):
  960k eval holds >=80% of peak BUT duration_entropy_floor_active stays
  active for most of late training. Performance/parity claims remain VALID
  (the floor is a legitimate stabilizer); mechanism claims about EMERGENT
  lifetime heterogeneity must be qualified as floor-supported — an honest
  partial falsification per R10.2-F, recorded as such. STILL use as the
  stabilized A2r base for a2_plus_t.

PARTIAL:
  Entropy stays healthy but task still decays.
  Then duration collapse was not sufficient; next one-variable knobs are
  intrinsic reward anneal, then smdp_bootstrap_coef.

FAIL:
  duration_usage_entropy still collapses WITH the floor on (after the one
  bounded retry below), or the eval peak is not held for reasons the
  entropy metrics do not explain.
  Bounded-retry rule (Condition 2): if usage entropy collapses with the
  floor on, allow ONE coefficient adjustment (0.05 -> 0.1). If it still
  collapses, pivot immediately to R19/team-transition. No silent sweeps.

WARN-MODE GUARD NOTE: in this run the ratio guard cannot kill; if the
  would-have-killed condition triggers (logged via
  proto_disc_reward_env_ratio_kill_triggered), it does not stop the run —
  it FLAGS the read: reward-scale pathology co-occurred, and the
  stabilization conclusion must note it.
```

Stop / continue rule:

```text
Run to 960k unless a non-guard runtime failure occurs.
In `kill` mode:
  instant stop if proto_disc_reward_env_ratio > 1.0 post-warmup;
  sustained stop if proto_disc_reward_env_ratio > 0.5 for 5 consecutive
  post-warmup updates.
For this comparison run, use `warn` mode (log, don't raise) to prevent confounding the read.
In `warn` mode, the same conditions increment the would-have-killed counter
but must not stop the run.
```

Result status: completed / PASS-SCAFFOLDED

Result summary:

```text
P3 bookkeeping completed before launch:
  update_60 checkpoint exists and is recorded as the current best-known
  R16/S7-S1 checkpoint:
    logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01\standalone_process_core_update_60.pt
  update_120 checkpoint also exists for late-collapse comparison:
    logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01\standalone_process_core_update_120.pt

Implementation validation 2026-07-04:
  in-memory compile of config.py / standalone_agent.py / train.py / plotting.py
    -> ok
  tiny CPU train smoke with --enable_duration_entropy_floor
    -> completed; floor activated when duration_usage_entropy < threshold
  tiny stochastic eval smoke with --eval_action_mode stochastic
    -> completed; eval log reports action_mode=stochastic

Guard-mode final spec validation 2026-07-04:
  default config:
    Config.reward_ratio_guard_mode == kill
  local entfloor runner dry-run precondition:
    ===== R16 A2r overnight: a2r_roster_reward_coef01_entfloor seed=1 =====
    guard_mode: warn
    ... --prototype_disc_warmup_steps 20000 --reward_ratio_guard_mode warn
        --enable_duration_entropy_floor --duration_entropy_floor_threshold 0.8
        --duration_entropy_floor_coef 0.05 --duration_entropy_floor_warmup_steps 0 ...
  warn-mode forced-trigger smoke:
    logs\smoke_r16_5_guard_warn
    triggered twice and continued to update=2 / total_steps=40.
    CSV last row:
      proto_disc_reward_env_ratio_over05_count=2.0
      proto_disc_reward_env_ratio_kill_triggered=2.0
  kill-mode forced-trigger smoke:
    logs\smoke_r16_5_guard_kill
    raised RuntimeError after writing update=1 / total_steps=20.
    CSV row exists with:
      proto_disc_reward_env_ratio_over05_count=1.0
      proto_disc_reward_env_ratio_kill_triggered=1.0

Completed run 2026-07-05:
  run:
    logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_233759\seed1\a2r_roster_reward_coef01_entfloor
  runner_status:
    state=finished
    exit_code=0
    finished=2026-07-05T06:05:14+08:00
  failure scan:
    runner_output.log contains no Traceback/RuntimeError/NaN/OOM/BrokenPipe.

Reference 480k peak (run_20260704_142053, update_60):
  reward_mean=78.140158
  coverage=0.345000
  qos=0.271246
  throughput=22.015988
  backhaul_connected_frac=0.387600
  zero_throughput_ep_frac=0.550000
  coverage_eq1_step_frac=0.000000

Reference 960k late-collapse point:
  reward_mean=20.078933
  coverage=0.080000
  qos=0.061291
  throughput=6.547736
  backhaul_connected_frac=0.210400
  zero_throughput_ep_frac=0.750000
  coverage_eq1_step_frac=0.000000

Entfloor eval trajectory:
  160k: reward=32.538359, coverage=0.156667, zero_throughput_ep_frac=0.600000
  320k: reward=48.602678, coverage=0.263333, zero_throughput_ep_frac=0.500000
  480k: reward=49.766409, coverage=0.200000, zero_throughput_ep_frac=0.500000
  640k: reward=46.498928, coverage=0.170000, zero_throughput_ep_frac=0.550000
  800k: reward=37.860116, coverage=0.135000, zero_throughput_ep_frac=0.600000
  960k: reward=67.263427, coverage=0.493333, qos=0.341250,
        throughput=27.252762, backhaul_connected_frac=0.446900,
        zero_throughput_ep_frac=0.200000,
        coverage_eq1_step_frac=0.075700,
        coverage_eq1_ep_frac=0.300000.

Gate read:
  The 960k entfloor eval holds >80% of the reference 480k peak on reward,
  coverage, qos, throughput, and backhaul_connected_frac, and it is far better
  than the reference 960k collapse point.  This satisfies the performance side
  of the R16.5 gate.

  However, duration entropy did not self-sustain:
    update_960k duration_usage_entropy=0.543469
    update_960k duration_usage_max_frac=0.770270
    update_960k duration_policy_entropy_norm=0.534978
    update_960k duration_entropy_floor_active=1
    update_960k duration_entropy_floor_gap=0.256531
    last10 duration_entropy_floor_active=1.0
    last10 duration_usage_entropy=0.588232

  Classification: PASS-SCAFFOLDED, not PASS-CLEAN.
  The floor is a useful stabilizer / parity baseline, but the mechanism claim
  must be qualified: lifetime heterogeneity is floor-supported late in training,
  not yet an emergent self-maintaining property.

Reward-scale guard note:
  warn mode allowed the comparison to complete.
  proto_disc_reward_env_ratio_kill_triggered reached 2 by update_100 and stayed
  2 at update_120; proto_disc_reward_env_ratio_over05_count reached 25.
  This flags reward-ratio pathology as co-occurring, not a crash cause.

Roster / AR note:
  proto_ar_parallel_kl and roster_ar_kl_shuffled remain approximately 5e-06,
  far below the 0.02 nats target.  R16 roster-docking still does not show a
  strong AR coordination signal.
```

Next decision:

```text
Run / read the four P2 eval-mode cells if not already completed, then send the
PASS-SCAFFOLDED read to cross-validation before deciding whether to:
  1. use entfloor as the stabilized R16 base for a2_plus_t / R19 comparison;
  2. run the bounded retry coef=0.1 only if the team wants to test whether
     entropy can be held nearer 0.8;
  3. avoid further roster-only sweeps because AR roster KL remains decorative.
Do not claim emergent lifetime heterogeneity from this seed-1 result.
```

### EXP-20260705-r16-5-continuation

Experiment name: `r16_5_entfloor_continuation`

Created at: 2026-07-05

Planned location: remote/cloud CUDA, separate from the currently running R19
overnight experiments.

Purpose:

```text
Continue the R16.5 result after the seed-1 PASS-SCAFFOLDED read:
  1. confirm whether floor_coef=0.05 scaffolded stabilization repeats on seed 2;
  2. run the one allowed bounded retry floor_coef=0.1 on seed 1 to test whether
     duration entropy can be held nearer 0.8 without hurting task performance or
     worsening reward-scale pathology.

This is not a broad R16 roster-only sweep and not an R19 team-transition read.
```

Command/script:

```bash
bash scripts/run_r16_a2r_remote_32env.sh --dry-run

EXPERIMENTS=a2r_roster_coef01_entfloor \
SEEDS=2 \
TOTAL_TIMESTEPS=960000 \
NUM_ENVS=64 \
DEVICE=cuda \
LOG_ROOT=logs_cloud_r16_5_continuation_64env \
bash scripts/run_r16_a2r_remote_32env.sh

EXPERIMENTS=a2r_roster_coef01_entfloor_coef010 \
SEEDS=1 \
TOTAL_TIMESTEPS=960000 \
NUM_ENVS=64 \
DEVICE=cuda \
LOG_ROOT=logs_cloud_r16_5_continuation_64env \
bash scripts/run_r16_a2r_remote_32env.sh
```

Fixed controls:

```text
scenario=S7-S1 energy
n_agents=6
num_envs=64
total_timesteps=960000
device=cuda
skill_lifetime_candidates=3,7,13,24
low_clip_epsilon=0.1
smdp_bootstrap_coef=0.25
prototype_disc_reward_coef=0.1
prototype_disc_clip=2.0
prototype_disc_warmup_steps=20000
ar_prefix_mode=roster
reward_ratio_guard_mode=warn
```

Variables:

```text
a2r_roster_coef01_entfloor:
  seed=2
  duration_entropy_floor_coef=0.05

a2r_roster_coef01_entfloor_coef010:
  seed=1
  duration_entropy_floor_coef=0.1
```

Metrics to read:

```text
duration_usage_entropy
duration_usage_max_frac
duration_policy_entropy_norm
duration_entropy_floor_active
duration_entropy_floor_gap
proto_disc_reward_env_ratio
proto_disc_reward_env_ratio_over05_count
proto_disc_reward_env_ratio_kill_triggered
coverage_eq1_step_frac
zero_throughput_ep_frac
coverage / qos / throughput
roster_ar_kl_shuffled
selection_independence_deficit
```

Meaning of possible outcomes:

```text
coef=0.05 seed2 repeats the scaffolded pass:
  Treat entfloor as a useful R16 scaffolded baseline, still with the caveat that
  lifetime heterogeneity is floor-supported unless floor_active fades late.

coef=0.1 keeps duration_usage_entropy much closer to 0.8 without task or guard
regression:
  Consider it a stronger scaffold candidate; do not call this emergent
  heterogeneity unless floor_active becomes transient.

coef=0.1 worsens task metrics or reward-ratio pathology:
  Stop R16.5 floor tuning; keep coef=0.05 as the scaffolded result and compare
  against R19/a2_plus_t when those runs finish.

roster_ar_kl_shuffled remains near zero:
  Do not revive broad roster-only sweeps; roster AR remains decorative.
```

Result status: completed

Result summary:

```text
Downloaded/read from:
  dist\logs_cloud_r16_5_continuation_64env

Both runs finished cleanly:
  seed1/a2r_roster_reward_coef01_entfloor_coef010:
    state=finished, exit_code=0, floor_coef=0.1
  seed2/a2r_roster_reward_coef01_entfloor:
    state=finished, exit_code=0, floor_coef=0.05

No Traceback/NaN/OOM was found in the downloaded logs.

seed2 coef=0.05, 960k eval:
  reward_mean=71.713382
  reward_std=78.257273
  coverage=0.416667
  qos=0.240737
  throughput=13.105124
  backhaul_connected_frac=0.500000
  zero_throughput_ep_frac=0.500000
  coverage_eq1_step_frac=0.016400
  coverage_eq1_ep_frac=0.050000

seed2 coef=0.05, final / last10 mechanism:
  duration_usage_entropy=0.937736 final, 0.958307 last10
  duration_usage_max_frac=0.403333 final, 0.382687 last10
  duration_entropy_floor_active=0 final, 0 last10
  proto_disc_reward_env_ratio=0.060781 final, 0.054688 last10
  proto_disc_reward_env_ratio_over05_count=0
  proto_disc_reward_env_ratio_kill_triggered=0
  roster_ar_kl_shuffled=0.000005 final, 0.000004 last10
  selection_independence_deficit=0.008343 final, -0.001080 last10

Interpretation:
  This seed-2 run is cleaner than the local seed-1 scaffolded read on duration:
  the floor is enabled but inactive late, and duration usage does not collapse.
  However, it is not S7-S1 parity: coverage_eq1_step_frac remains only 0.0164
  and zero_throughput_ep_frac remains 0.50.  It supports "entfloor helps avoid
  duration collapse / late regression" but not "R16 solves cooperation".

seed1 coef=0.1 bounded retry, 960k eval:
  reward_mean=31.248840
  coverage=0.121667
  qos=0.091398
  throughput=6.778694
  backhaul_connected_frac=0.286300
  zero_throughput_ep_frac=0.650000
  coverage_eq1_step_frac=0.000000

seed1 coef=0.1, final / last10 mechanism:
  duration_usage_entropy=0.917980 final, 0.941544 last10
  duration_entropy_floor_active=0 final, 0 last10
  proto_disc_reward_env_ratio=0.230569 final, 0.235317 last10
  ratio over05 / kill_triggered = 0 / 0
  roster_ar_kl_shuffled=0.000004 final and last10

Interpretation:
  coef=0.1 does not improve the useful read.  It keeps duration entropy high
  without needing the floor late, but task performance is poor and it remains
  far below the seed2 coef=0.05 run.  The bounded retry should be closed as a
  negative branch.
```

Next decision:

```text
Stop R16.5 floor tuning.  The useful retained base is coef=0.05, with the
caveat that it stabilizes duration/late regression but does not solve the
cooperation/parity target.  Do not do another broad roster-only sweep:
roster_ar_kl_shuffled remains ~4e-6 to 5e-6, so roster content use is still
decorative.  Move interpretation effort to R19/R21, keeping R16.5 only as a
stabilized baseline/control.
```

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

Experiment name: `r16_a2r_roster_remote_parallel_32env`

Created at: 2026-07-04

Planned location: cloud / remote servers, parallel split by arm and seed.

Command/script:

```bash
bash scripts/run_r16_a2r_remote_32env.sh
```

Package:

```text
dist/ha_ctse_r16_a2r_remote_bundle_20260704_163219.zip
dist/HA_CTSE_R16_REMOTE_UPLOAD_README.md
dist/HA_CTSE_P0_MINIMAL_PACKAGE_FILES.md
```

Recommended multi-server split:

```bash
EXPERIMENTS=a2r_roster_reward  SEEDS=1 TOTAL_TIMESTEPS=960000 NUM_ENVS=32 DEVICE=cuda bash scripts/run_r16_a2r_remote_32env.sh
EXPERIMENTS=a2r_roster_coef005 SEEDS=1 TOTAL_TIMESTEPS=960000 NUM_ENVS=32 DEVICE=cuda bash scripts/run_r16_a2r_remote_32env.sh
EXPERIMENTS=a2_samecheck_reward SEEDS=1 TOTAL_TIMESTEPS=960000 NUM_ENVS=32 DEVICE=cuda bash scripts/run_r16_a2r_remote_32env.sh
EXPERIMENTS=a1r_roster_probe   SEEDS=1 TOTAL_TIMESTEPS=960000 NUM_ENVS=32 DEVICE=cuda bash scripts/run_r16_a2r_remote_32env.sh
```

64-env resource override requested 2026-07-04:

```text
Use the same package and same script; set NUM_ENVS=64 and optionally set
LOG_ROOT=logs_cloud_r16_a2r_64env so 32-env and 64-env reads do not mix.
This is a throughput/resource configuration change, not a new algorithm arm.
```

Code snapshot / changed files:

```text
scripts/run_r16_a2r_remote_32env.sh
dist/HA_CTSE_R16_REMOTE_UPLOAD_README.md
dist/HA_CTSE_P0_MINIMAL_PACKAGE_FILES.md
dist/HA_CTSE_P0_MINIMAL_PACKAGE_FILES.txt
```

Purpose:

```text
Move the current R16/A2r roster-docking decision read to multiple remote
servers so arms and seeds can run in parallel.  This avoids waiting for the
local sequential overnight runner and avoids Windows PowerShell native-stderr
wrapper issues.
```

Hypothesis:

```text
If active-roster conditioning is the correct asynchronous analogue of HMASD's
autoregressive complementary assignment, then the roster reward arm should
make roster content non-decorative under reward pressure:
  roster_ar_kl_shuffled rises,
  selection_independence_deficit moves downward/negative,
  entropy/reward scale remain safe,
  and task metrics do not regress.
```

Controls / comparison:

```text
Primary: a2r_roster_reward coef=0.1.
Scale control: a2r_roster_coef005.
Same-check control: a2_samecheck_reward.
Reward-off roster control: a1r_roster_probe.

Seed 1 is the first remote read.  Seed 2 is required before any positive claim.
```

Metrics to read:

```text
R16 coordination:
  roster_ar_kl_shuffled
  roster_ar_kl_zeroed
  selection_independence_deficit
  selection_same_skill_rate
  selection_independence_null_rate

Prototype residual:
  proto_disc_acc
  proto_disc_residual_mean
  proto_disc_residual_positive_frac
  proto_disc_reward_mean
  proto_disc_reward_env_ratio

Safety:
  skill_entropy
  duration_entropy
  proto_skill_usage_entropy
  proto_skill_usage_entropy_by_kappa
  segment_length_mean
  renewal_agents_mean
  renewal_full_sync_rate

Task read:
  coverage_eq1_step_frac
  zero_throughput_ep_frac
  coverage
  qos
  throughput
  reward_mean/std
```

Meaning of possible outcomes:

```text
Roster reward raises roster_ar_kl_shuffled >= 0.02, selection deficit becomes
more negative, and task metrics are neutral/up:
  R16 roster-docking remains alive; run seed 2.

Coef=0.1 unstable but coef=0.05 moves the same roster diagnostics safely:
  use coef=0.05 as the next default.

Same-check reward works while roster does not:
  reward pressure may help individual identifiability, but roster docking
  content use is not proven.

All reward arms keep roster_ar_kl_shuffled < 0.01, selection deficit does not
move in the intended direction, and task metrics do not improve:
  treat R16 roster-docking as negative for this implementation and stop
  stacking sequential-assignment machinery.
```

Stop / continue rule:

```text
Run to the 320k gate unless there is a real Python traceback, NaN/OOM, or
catastrophic 160k eval.  Continue to 960k only for arms that are not already
mechanistically dead at 320k.  Do not interpret reward_mean alone.
```

Result status: packaged / partially read

Result summary:

```text
Remote bundle created and verified on 2026-07-04:
  dist/ha_ctse_r16_a2r_remote_bundle_20260704_163219.zip
  zip entry count=135
  required key files present
  pycache/pyc count=0

Local bash execution validation was not possible because Git Bash failed under
the local Windows sandbox with WinError 5.  Static checks passed; run
`DRY_RUN=1 bash scripts/run_r16_a2r_remote_32env.sh` on the server before
launching real training.

R16 four-arm read 2026-07-04 (user clarified this is R16; R19 is next batch):
  Local completed arm:
    logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01
    completed update 120 / 960000 steps, no errors.
    final eval: reward=20.08, coverage=0.080, throughput=6.55,
      backhaul_frac=0.210, zero_throughput_ep_frac=0.75.
    best observed eval was earlier at 480k: reward=78.14, coverage=0.345,
      throughput=22.02, backhaul_frac=0.388.
    final mechanism: proto_acc=0.472, roster_kl_shuf=0.000006,
      sel_def=0.0018, proto_resid=0.1358, proto_reward=0.0136,
      credit_recover=0.121, credit_bh_frac=0.508, duration_entropy=0.467.

  Dist downloaded arms:
    dist\a2r_roster_coef005\standalone_train.log
      reached update 29 / 928000 steps, no errors.
      latest eval at 800k: reward=40.20, coverage=0.288, throughput=6.39,
        backhaul_frac=0.341, zero_throughput_ep_frac=0.60.
      last10: roster_kl_shuf=0.000003, sel_def=-0.0034,
        proto_resid=0.0116, credit_recover=0.022, credit_bh_frac=0.304,
        duration_entropy=0.956.

    dist\a2_samecheck_reward\standalone_train.log
      reached update 19 / 608000 steps, no errors.
      latest eval at 480k: reward=23.87, coverage=0.117, throughput=5.73,
        backhaul_frac=0.270, zero_throughput_ep_frac=0.60.
      last10: proto_ar_kl ~= 0, roster_kl_shuf=0, sel_def=0,
        proto_resid=0.0027, credit_recover=0.010, credit_bh_frac=0.262,
        duration_entropy=0.984.

    dist\a1r_roster_probe\standalone_train.log
      reached update 20 / 640000 steps, no errors.
      latest eval at 480k: reward=29.90, coverage=0.155, throughput=3.07,
        backhaul_frac=0.311, zero_throughput_ep_frac=0.60.
      last10: roster_kl_shuf=0.000004, sel_def=0.0011,
        proto_resid=-0.0026, proto_reward=0, credit_recover=0.015,
        credit_bh_frac=0.263, duration_entropy=0.991.

Interpretation:
  The R16 roster channel remains mechanistically unused in every arm:
  roster_kl_shuf stays about 0.000003-0.000006, far below the 0.02 alive
  threshold and below the <0.01 fail band.  The coef=0.05 arm is safer and
  has the best late task read among the remote logs, while local coef=0.1
  temporarily peaks at 480k but regresses badly by 960k and collapses duration
  entropy.  This is not an R19 result; it is a negative/weak R16 read.
```

Next decision:

```text
Do not promote R16 roster-docking as the main mechanism from seed 1.  If more
R16 evidence is needed, only run a narrow coef=0.05 seed-2 confirmation; do not
spend another broad sweep on roster AR.  Keep R19 as the next-batch experiment,
separate from this R16 read.
```

### EXP-20260703-r15-stage1-steering

Experiment name: `r15_stage1_coordinator_residual`

Created at: 2026-07-03 (pre-registered by CC per Round 15; user-requested
settings and standards)

Planned location: local CUDA

Fixed settings (ALL arms; matches prior local-read conventions):

```text
scenario energy, preset S7-S1, n_agents 6
num_envs 16, rollout_length 500, skill_interval 10
skill_lifetime_candidates (3,7,13,24)
total_timesteps 320000 (40 updates), eval_interval 160000, eval_episodes 20
low_clip_epsilon 0.1, smdp_bootstrap_coef 0.25, device cuda
seed 1 first; seed 2 required before any PASS claim
opt_num_prototypes 4 — PINNED: the Stage-0 substrate gate was passed at N=4;
  changing N invalidates that gate read. An N=8 variant is a later ablation
  that requires re-running the substrate gate first.
prototype_skill_extra_codes 0  -> n_skills = 4 in prototype arms
reward-pure base everywhere: process/topology/transition/force rewards off;
  only the prototype disc reward may be nonzero, and only in A2.
```

Arms:

```text
A0 control_legacy4   master switch OFF, legacy skill labels with n_skills=4.
   RATIONALE: skill-count-matched control (legacy n_z=6 vs prototype n=4
   would confound skill cardinality with the mechanism). The historical
   diag_only n=6 run is a reference only, not the comparator.
A1 s1_probe          use_prototype_response_skills + high_condition_on_omega
   + use_agent_prototype_relevance + use_autoregressive_selection
   + enable_prototype_disc_probe. NO reward. use_compact_return_head OFF
   (Part C is a separate later variable).
A2 s1_reward         A1 + enable_prototype_disc_reward,
   coef 0.1, clip 2.0, warmup 20000.
   R15 NULL: reward = log q_d - stored log pi_h. The implemented
   prototype_disc_prior_coef path applies ONLY in the A3 fallback.
A3 r15_p1_ablation   (conditional, only per outcome matrix) A2 with
   --parallel_selection + kappa-prior head. Tests prediction R15-P1
   (usage-imbalance shortcut returns under a non-AR null).
```

Execution order (enforced): A0 and A1 first (sequential overnight is fine).
A2 launches ONLY after the A1 probe-health checklist passes. A3 only if the
outcome matrix calls for it.

Read protocol: read at update 20 (160k) and 40 (320k); DECIDE on last-third
means (updates 28-40) plus the 320k eval. Never decide on a single update or
reward_mean alone.

A1 probe-health checklist (gate for launching A2):

```text
reward guards: all reward-path fields 0.0 throughout.
proto_omega_nonzero_frac        in [0.30, 0.90]  (collapse=0.25, uniform=1.0)
proto_skill_usage_entropy       >= 0.69  (= 0.5 * ln 4)
proto_skill_usage_entropy_by_kappa >= 0.69
proto_skill_relevance_alignment >= 2x its shuffled-label null (log both)
proto_ar_parallel_kl            >= 0.02 nats by 320k; < 0.01 = AR chain
                                coordinates nothing -> fix A3 inputs before A2
proto_disc_acc                  >= 0.35 (chance 0.25) with rising trend
proto_bank_drift_cos            >= 0.90
J3 bundle (proto_rel_*)         logged with nonzero variance (feeds Stage 2)
```

A2 reward gate (vs A0 at matched steps; last-third means + 320k eval):

```text
PASS requires ALL of:
  forced-z trajectory spread ratio (h=50): A2 >= 1.3 x A0
  proto_disc_residual_mean > 0 sustained AND residual_positive_frac >= 0.55
  proto_skill_usage_entropy_by_kappa >= 0.69 (no situation->skill lookup)
  eval coverage_mean          >= A0 - 0.02 (absolute)
  zero_throughput_ep_frac     <= A0 + 0.05 (absolute)
  reward_std / reward_mean    <= 1.15 x A0
  throughput                  >= 0.90 x A0
  proto_disc_reward_env_ratio in [0.05, 0.50] post-warmup

RUNTIME KILL (stop the arm, do not wait for 320k):
  proto_disc_reward_env_ratio > 1.0 for 5 consecutive post-warmup updates
  eval at 160k shows zero_throughput_ep_frac > A0 + 0.15

SELF-EXTINCTION GUARD (R15 moving-null risk):
  at 320k, proto_disc_residual_mean >= 0.3 x its post-warmup peak,
  UNLESS the forced-z spread criterion already passed (pressure may
  legitimately anneal after separation is achieved).
```

Outcome matrix (Stage-1 exit; from the amended spec; R19 branch added
2026-07-04):

```text
OUT-OF-GAS (R19): proto_disc_acc >= 0.6 AND forced-z spread >= 1.3x A0 AND
                                    residual annealing, BUT coverage /
                                    zero-throughput flat vs A0/A1
                                    -> exploration-scale deficit, NOT a
                                    coordinator-residual failure: route to
                                    A2+T (team transition residual, xi =
                                    active-skill counts, self-transitions
                                    included, high-level injection, coef
                                    0.05). Do not tune the individual term.
separation UP  + task neutral/up -> PASS pending seed 2; proceed to the
                                    Stage-2 trigger check (J3 calibration).
separation UP  + task DOWN       -> halve coef once (0.05); still down ->
                                    keep probe-only, weight moves to P2/P4
                                    parallel reads.
separation FLAT + task neutral   -> conditioning/capacity problem: fix
                                    selection inputs / actor skill
                                    conditioning BEFORE any coef sweep;
                                    run A3 to separate null-model from
                                    capacity explanations.
separation FLAT + task DOWN      -> revert reward arm; re-read s1_probe and
                                    P1 per-agent dwell before touching
                                    anything else.
```

Round-15 stop rule (from cross_validation.md): both reward quadrants
separation-flat across 2 seeds -> fall back to the R14.1 kappa-prior form;
if that also fails separation, to the Round 11 commitment-first anchor.

Runner: sibling script `scripts/run_r15_stage1_local_cuda.ps1` with arms
`control_legacy4, s1_probe, s1_reward, r15_p1_ablation`; `-DryRun` must pass
before launch; per-invocation timestamped log dirs (the R12-1a contamination
lesson).

Status: RUNNING as of 2026-07-03. Codex implemented the R15 spec amendment
(AR-first prototype-response selection + stored assignment null-logp reward).
Validation already completed:

```text
pytest tests\r14_prototype_response_test.py -q -> 8 passed
AST parse for standalone_agent/prototype_response_discriminator/config/train/plotting/test -> ast_ok 6
scripts\run_r15_stage1_local_cuda.ps1 -DryRun -> default A0+A1 commands OK
scripts\run_r15_stage1_local_cuda.ps1 -Experiments s1_reward,r15_p1_ablation -DryRun -> explicit arms OK
tiny s1_probe smoke (2 env, 64 steps) -> passed; proto_null/proto_ar_kl logged
tiny s1_reward smoke with warmup=0 -> passed; proto reward path applied
tiny control_legacy4 smoke -> passed; prototype_response=False, n_skills=4,
  ar_selection=False
tiny r15_p1 fallback smoke -> passed; parallel_selection=True,
  prototype_disc_learned_prior=True
subagent spec review -> no blocking issues; Codex fixed its two P3 findings:
  added proto_assignment_logp_mean to prototype diagnostics plot and added a
  batch-level test proving Segment.skill_assignment_logp broadcasts into
  _prototype_discriminator_batch()["null_logp"].
```

Recommended next command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r15_stage1_local_cuda.ps1 `
  -Experiments control_legacy4,s1_probe `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Do not launch `s1_reward` until the A1 probe-health checklist passes.

Launch status 2026-07-03:

```text
User stopped the stale R14 restart.  Process check confirmed the old
run_r14_stage1_local_cuda process is gone.

R15 A0+A1 was launched locally:
  scripts\run_r15_stage1_local_cuda.ps1
    -Experiments control_legacy4,s1_probe
    -TotalTimesteps 320000
    -NumEnvs 16
    -Device cuda

Active process at inspection:
  powershell PID 43428
  python PID 23628

Active arm:
  logs\ha_ctse_r15_stage1_local_cuda\run_20260703_173650\
    control_legacy4_reward_pure

Current progress:
  standalone_train_start written
  no standalone_update yet at inspection

Start configuration sanity:
  prototype_response=False
  legacy_n_skills=4
  ar_selection=False
  high_omega=False
  agent_proto_rel=False
  proto_disc_probe=False
  proto_disc_reward=False
  device=cuda

Next read:
  after update 1 to confirm metric schema, then at 160k and 320k.  Do not
  launch or interpret s1_reward before A1 s1_probe passes the probe-health gate.
```

Interrupted-run read 2026-07-03:

```text
User reported no process residue after an unexpected interruption.
Process query was not used after the denial; log state is authoritative here.

Run root:
  logs\ha_ctse_r15_stage1_local_cuda\run_20260703_173650

Observed arms:
  control_legacy4_reward_pure only
  no s1_probe directory exists

A0 control progress:
  update=40
  total_steps=320000 / 320000
  checkpoint saved:
    control_legacy4_reward_pure\standalone_process_core_update_40.pt
  160k eval exists
  320k eval is missing
  no Traceback/RuntimeError/ERROR found in standalone_train.log

A0 final train update:
  env_reward_mean=0.044321
  return_mean=2.372013
  skill_entropy=0.993
  duration_entropy=0.943
  credit_disc=0.643
  credit_recover=0.020
  credit_bh_frac=0.228

A0 160k eval:
  reward_mean=31.776934
  coverage=0.145000
  throughput=7.832558
  coverage_eq1_step_frac=0.000000
  zero_throughput_ep_frac=0.650000

Interpretation:
  A0 is mostly usable as a control training run because it reached update 40,
  but the missing 320k eval should be补跑 from the update_40 checkpoint before
  comparing against A1.  The sequence did not start A1, so R15's probe-health
  gate has not yet been tested.

Next decision:
  1. Run eval-only on A0 update_40 checkpoint to fill the missing 320k eval.
  2. Launch A1 `s1_probe` only.
  3. Do not launch A2 `s1_reward` until A1 passes the pre-registered
     probe-health checklist.
```

A0 eval-only补跑 result 2026-07-03:

```text
Command:
  python -m ha_ctse_process.train --mode eval
    --resume_from logs\ha_ctse_r15_stage1_local_cuda\run_20260703_173650\
      control_legacy4_reward_pure\standalone_process_core_update_40.pt

Result:
  standalone_eval_start total_steps=320000 update_idx=40
  reward_mean=26.347979
  reward_std=58.848179
  coverage=0.096667
  qos=0.074980
  throughput=6.106457
  backhaul_connected_frac=0.235100
  throughput_when_backhaul_connected=14.144247
  coverage_eq1_step_frac=0.000000
  coverage_eq1_ep_frac=0.000000
  zero_throughput_ep_frac=0.750000
  throughput_gt5_step_frac=0.235100

Interpretation:
  A0 control is a valid baseline but weak and high-variance.  The 320k eval is
  worse than its 160k eval on coverage and zero-throughput, but this does not
  decide R15.  It gives the comparator for A1/A2.  Next action remains A1
  `s1_probe` only; no reward arm until the probe-health checklist passes.
```

A1 progress read 2026-07-03:

```text
Run root:
  logs\ha_ctse_r15_stage1_local_cuda\run_20260703_214403\
    s1_probe_ar_null_reward_off

Progress:
  update=28
  total_steps=224000 / 320000
  160k eval exists
  no Traceback/RuntimeError/ERROR found

Latest update:
  env_reward_mean=0.045485
  proto_acc=0.358
  proto_prior_acc=0.000
  proto_null=-1.372613
  proto_ar_kl=0.000001
  proto_resid=0.004826
  proto_reward=0.000000
  proto_steps=0
  proto_skill_ent=0.985
  proto_kappa_ent=0.826
  proto_align=0.011
  proto_rel_dwell=2.0
  proto_rel_stab=0.971
  skill_entropy=0.985
  duration_entropy=0.972
  credit_disc=0.572
  credit_recover=0.015
  credit_bh_frac=0.192

160k eval:
  reward_mean=19.586445
  coverage=0.066667
  throughput=1.778312
  coverage_eq1_step_frac=0.000000
  zero_throughput_ep_frac=0.750000

Interpretation:
  Reward guards are clean: proto_reward=0 and proto_steps=0, so this is still
  a valid A1 probe.  The probe has some classifier signal (`proto_acc` above
  chance), but the critical AR coordination diagnostic is effectively zero
  (`proto_ar_kl` about 1e-6), far below the pre-registered 0.02 gate and below
  the 0.01 red-flag threshold.  This is an early but strong warning that the
  AR chain is not changing assignments relative to parallel selection.

Next decision:
  Let A1 finish to 320k if the process is still alive because the gate was
  defined at 320k.  Do not launch A2 `s1_reward`.  If 320k keeps
  `proto_ar_kl < 0.01`, treat A1 as failing the AR-coordination health gate
  and inspect/fix AR prefix conditioning / selection inputs before any reward
  arm.
```

A1 progress read 2026-07-04:

```text
Run root:
  logs\ha_ctse_r15_stage1_local_cuda\run_20260703_214403\
    s1_probe_ar_null_reward_off

Progress:
  update=34
  total_steps=272000 / 320000
  latest log write=2026-07-04 00:04:12
  no Traceback/RuntimeError/ERROR found
  latest eval remains the 160k eval

Latest update:
  env_reward_mean=0.051069
  proto_acc=0.281
  proto_prior_acc=0.000
  proto_null=-1.384069
  proto_ar_kl=0.000000
  proto_resid=0.006972
  proto_reward=0.000000
  proto_steps=0
  proto_skill_ent=0.997
  proto_kappa_ent=0.934
  proto_align=0.005
  proto_rel_dwell=2.0
  proto_rel_stab=0.978
  skill_entropy=0.997
  duration_entropy=0.970
  credit_disc=0.558
  credit_recover=0.000
  credit_bh_frac=0.248

Interpretation:
  Reward guards remain clean, so the probe is valid.  The negative signal is
  now stronger: `proto_ar_kl` is still exactly 0.0 at update 34, not just noisy
  early near-zero.  `proto_acc` is above chance only weakly and `proto_align`
  is near zero.  Unless the last six updates change materially, A1 will fail
  the AR-coordination health gate.

Next decision:
  Let the run finish to 320k if it is still alive; do not run A2.  If 320k
  confirms `proto_ar_kl < 0.01`, mark A1 failed and inspect AR prefix
  conditioning / selection inputs rather than tuning discriminator reward.
```

A1 final structural read 2026-07-04:

```text
Run root:
  logs\ha_ctse_r15_stage1_local_cuda\run_20260703_214403\
    s1_probe_ar_null_reward_off

Progress:
  update=40
  total_steps=320000 / 320000
  checkpoint saved:
    s1_probe_ar_null_reward_off\standalone_process_core_update_40.pt
  no Traceback/RuntimeError/ERROR found
  160k eval exists
  320k eval is missing and should be filled only for task-comparison
  bookkeeping, not for the AR-health decision.

Final update:
  env_reward_mean=0.038727
  proto_acc=0.270
  proto_prior_acc=0.000
  proto_null=-1.381176
  proto_ar_kl=0.000000
  proto_resid=0.007863
  proto_reward=0.000000
  proto_steps=0
  proto_skill_ent=0.998
  proto_kappa_ent=0.974
  proto_align=0.012
  proto_rel_dwell=2.0
  proto_rel_stab=0.969
  skill_entropy=0.998
  duration_entropy=0.974
  credit_disc=0.629
  credit_recover=0.030
  credit_bh_frac=0.172

160k eval:
  reward_mean=19.586445
  coverage=0.066667
  throughput=1.778312
  coverage_eq1_step_frac=0.000000
  zero_throughput_ep_frac=0.750000

Gate read:
  A1 FAILS the pre-registered AR-coordination health gate.  Reward guards are
  clean (`proto_reward=0`, `proto_steps=0`), and usage does not collapse, but
  `proto_ar_kl=0.0` at 320k is far below both the target 0.02 and red-flag
  threshold 0.01.  The AR coordinator is not changing assignments relative to
  parallel selection.  The weak positive residual/classifier signal is not
  enough to justify A2 reward injection.

Next decision at the time:
  Do NOT launch `s1_reward` until the AR prefix mechanical check is complete.
  Optionally fill the missing A1 320k eval from the checkpoint for record
  completeness.

Superseded by 2026-07-04 mechanical check below:
  the prefix channel is wired, so the next decision is no longer "fix wiring";
  it is whether to run A2 as an explicit reward-pressure test under the revised
  CC gate.
```

CC gate revision 2026-07-04 (after the A1 failure read; full reasoning in
`cross_validation.md` -> "2026-07-04 CC read of EXP-20260703-r15-stage1-steering
A1 failure"):

```text
1. MECHANICAL CHECK FIRST: ar_kl=0.0 exact is a wiring suspect, not a
   mechanism verdict. Required before any rerun: init-time forced-prefix
   intervention proving the prefix changes assignment logits at
   initialization; log ar_kl in scientific notation.
2. A1 PROBE-HEALTH CHECKLIST REVISED: blockers reduce to {reward guards
   clean, no entropy collapse, disc acc above chance, omega health in
   [0.30,0.90], bank drift >= 0.90}. ar_kl and relevance-alignment are
   REMOVED as A1 blockers (reward-off emergence was the g-decorative mistake
   repeated) and become A2 outcome metrics.
3. A2 comparators: BOTH A0 (full mechanism) and A1 (architecture-matched
   reward-off control; A1's weaker 160k eval shows the added inputs cost
   learning speed).
4. A2 interpretation scope: low ar_kl under A2 does not falsify the
   identifiability half; it marks anti-duplication as not-yet-active
   (testable at Stage 3). Round-15 stop rule unchanged and now
   excuse-free once the mechanical check passes.
5. Stage-2 pre-registration from A1 data: proto_rel_dwell=2.0 is churny; if
   it persists under A2, per-agent kappa_i must come from per-agent compact
   clustering (substrate-gate dwell 100) rather than raw relevance rows.
```

Codex mechanical-check result 2026-07-04:

```text
Implemented:
  tests/r14_prototype_response_test.py::
    test_r15_agent_init_forced_prefix_changes_assignment_logits

Validation:
  python -m pytest tests\r14_prototype_response_test.py -q
    -> 9 passed

Result:
  In the full R15 StandaloneProcessAgent configuration, ar_prefix=None is
  equivalent to an explicit zero prefix, and a forced nonzero prefix changes
  high-level assignment logits at initialization.

Experiment interpretation:
  A1's `proto_ar_kl=0.0` is not a disconnected-prefix failure.  The likely
  explanations are missing training pressure in reward-off rollout, mostly
  single-agent renewal events, or an A1 metric that should not be a hard
  blocker.  A2 may be launched as a reward-pressure experiment if we accept the
  revised gate, but this is not a strong A1 pass because `proto_acc=0.270` is
  only weakly above chance.
```

Round 16 update 2026-07-04:

```text
CC measured A1 last-10 renewal statistics:
  renewal_agents_mean      = 1.4424
  renewal_agents_std       = 0.7297
  renewal_full_sync_rate   = 0.0000
  renewal_pairwise_corr    = -0.0881

Decision:
  The same-check AR prefix is structurally starved under asynchronous renewal.
  This explains why the rollout `proto_ar_kl` can be zero despite healthy
  forced-prefix wiring.

Experiment scoping:
  A2 `s1_reward` remains useful, but only as a coordinator-residual
  reward-pressure test under the current same-check prefix.  Its `proto_ar_kl`
  should be interpreted as anti-duplication not yet active, not as a wiring
  failure.

Planned follow-up:
  A2r = A2 + `ar_prefix_mode=roster` after roster mode is implemented.
  Roster mode conditions a renewing agent on teammates' currently active skills
  and skill ages.  Its main diagnostic is:
    roster_ar_kl_shuffled = KL(selection | true roster || shuffled roster)
  Success target:
    roster_ar_kl_shuffled >= 0.02 under reward + roster.

Implementation guards before launching A2r:
  1. Segment stores renewal-time roster snapshot, not live/current roster:
       teammate active skill ids, skill ages, order/mask.
     Test: recomputed logp from stored snapshot equals stored assignment logp.
  2. Forced full-sync renewal reduces roster mode exactly to same-check/HMASD
     AR: later renewers see earlier renewers' newly sampled skills.
  3. Log both:
       roster_ar_kl_zeroed   (mechanical capability)
       roster_ar_kl_shuffled (coordination/content use; primary A2r metric)
  4. Skill ages are mandatory in main roster encoding.
  5. Anti-duplication must be judged by:
       selection_independence_deficit =
         observed co-active same-skill rate
         - shuffled-teammate independence null with matched skill-usage marginals
     not by raw same-skill duplication.  Desired movement is downward/negative
     relative to A2 or the shuffled null.

Stop rule:
  If A2r across 2 seeds still has roster_ar_kl_shuffled < 0.01, no
  negative movement in `selection_independence_deficit`, and no task benefit vs
  A2, drop sequential assignment from the mainline and fall back to parallel
  selection with kappa-conditioned null / later Stage-3 complementarity
  pressure.
```

Round 16 implementation status 2026-07-04:

```text
Code status:
  READY_FOR_A2R.

Implemented:
  --ar_prefix_mode same_check|roster
  Segment renewal-time roster snapshot:
    roster_active_skills_start
    roster_active_ages_start
    roster_active_mask_start
  PPO/evaluate reconstruction from stored roster snapshot.
  Full-sync special case: roster prefix can reduce to same-check AR by exposing
  earlier same-check renewers' newly sampled skills.
  Diagnostics:
    roster_ar_kl_zeroed
    roster_ar_kl_shuffled
    selection_independence_available
    selection_same_skill_rate
    selection_independence_null_rate
    selection_independence_deficit

Validation:
  python -m pytest tests\r14_prototype_response_test.py -q
    -> 13 passed, 1 warning.
  AST parse touched HA-CTSE files
    -> ast_ok 6.
  SB3-env CLI help
    -> `--ar_prefix_mode {same_check,roster}` present.
  Tiny roster smoke train
    -> completed; `metrics/train_updates.csv` contained roster diagnostics.

Next local launch:
  A2r seed 1, S7-S1, 6 agents, 16 env, 320k, CUDA.
  Compare against A2 same-check if available; otherwise treat A2r as a
  mechanism gate, not a final performance claim.

Read after run:
  metrics/train_updates.csv
  standalone_train.log eval lines
  TensorBoard/plots if generated

Primary interpretation:
  PASS only if the reward arm produces non-decorative roster use:
    roster_ar_kl_shuffled >= 0.02
    selection_independence_deficit moves downward/negative
    skill/duration entropy do not collapse
    reward scale remains within the pre-registered guard
    task metrics do not show obvious harm.
```

### EXP-20260704-r16-a2r-overnight-local

Experiment name: `r16_a2r_roster_overnight_local_cuda`

Created at: 2026-07-04

Planned location: local CUDA overnight; cloud optional after local read.

Command/script:

```powershell
& .\scripts\run_r16_a2r_overnight_local_cuda.ps1
```

Dry run:

```powershell
& .\scripts\run_r16_a2r_overnight_local_cuda.ps1 -DryRun
```

Default arms:

```text
1. a2r_roster_reward
   A2 reward arm + --ar_prefix_mode roster, coef=0.1.
   Primary R16 mechanism test.

2. a2r_roster_coef005
   Same as A2r but coef=0.05.
   Safety/scale arm if coef=0.1 is noisy or harms task metrics.

3. a2_samecheck_reward
   A2 reward arm + --ar_prefix_mode same_check, coef=0.1.
   Control for "reward pressure exists but same-check prefix is starved".

4. a1r_roster_probe
   Roster mode, prototype discriminator probe on, reward off.
   Diagnostic for whether roster context alone is decorative without reward
   pressure.  This should not be used as a hard blocker.
```

Fixed settings:

```text
S7-S1 energy, 6 agents, seed 1 by default
num_envs=16, rollout_length=500, skill_interval=10
skill_lifetime_candidates=(3,7,13,24)
total_timesteps=640000 by default, eval_interval=160000, eval_episodes=20
low_clip_epsilon=0.1, smdp_bootstrap_coef=0.25
device=cuda
opt_num_prototypes=4, prototype_skill_extra_codes=0
process/posterior/outcome/topology/transition rewards disabled
```

Runtime length note:

```text
Default is intentionally longer than the 320k mechanism gate so the read has
160k/320k/480k/640k eval points.  For a shorter debug gate, run with
`-TotalTimesteps 320000`.  For a near-1e6 local read, run with
`-TotalTimesteps 960000`, but prefer fewer arms if wall-clock is limited.
```

Purpose:

```text
Use the new R16 roster-docking implementation overnight to decide whether
asynchronous sequential assignment becomes non-decorative once the coordinator
residual reward is applied against a non-empty active teammate roster.
```

Hypothesis:

```text
If same-check AR was starved only because few agents renew together, then
roster mode should raise `roster_ar_kl_shuffled` under reward pressure and
move `selection_independence_deficit` downward/negative relative to same-check
or reward-off roster probe, without collapsing skill/duration entropy.
```

Controls / comparison:

```text
Compare `a2r_roster_reward` vs:
  a2_samecheck_reward  -> reward pressure without active-roster context.
  a1r_roster_probe     -> roster context without reward pressure.
  a2r_roster_coef005   -> coefficient sensitivity.

Existing A0/A1 R15 runs remain reference baselines, not identical-script arms.
```

Metrics to read:

```text
Primary R16 coordination:
  roster_ar_kl_shuffled
  roster_ar_kl_zeroed
  selection_independence_deficit
  selection_same_skill_rate
  selection_independence_null_rate

Prototype residual:
  proto_disc_acc
  proto_disc_residual_mean
  proto_disc_residual_positive_frac
  proto_disc_reward_mean
  proto_disc_reward_env_ratio if available

Safety:
  skill_entropy
  duration_entropy
  proto_skill_usage_entropy
  proto_skill_usage_entropy_by_kappa
  segment_length_mean
  renewal_agents_mean / renewal_full_sync_rate

Task read:
  coverage_eq1_step_frac
  zero_throughput_ep_frac
  coverage, qos, throughput, reward_mean/std
```

Meaning of possible outcomes:

```text
roster reward raises roster_ar_kl_shuffled >= 0.02 and selection deficit moves
downward/negative while task metrics are neutral/up:
  R16 roster-docking remains alive.  Repeat seed 2 before any claim.

coef=0.1 unstable but coef=0.05 has healthier reward scale and similar roster
KL movement:
  use coef=0.05 as the next A2r default.

same-check reward improves task metrics but roster does not move the roster
diagnostics:
  reward pressure may be helping individual identifiability, but sequential
  roster complementarity remains unproven.

reward-off roster probe has high zeroed KL but low shuffled KL:
  mechanical roster channel exists, but content/identity use is absent without
  reward pressure.  This is not a blocker by itself.

all reward arms show roster_ar_kl_shuffled < 0.01, no negative movement in
selection_independence_deficit, and no task benefit:
  sequential assignment should be dropped from the mainline per the R16 stop
  rule; fall back to parallel selection / kappa-conditioned null and later
  complementarity pressure.
```

Stop / continue rule:

```text
Default script stops on first failure.  Use `-ContinueOnError` if the goal is
to salvage later arms after one crash.  If `proto_disc_reward_env_ratio` exceeds
1.0 for 5 consecutive post-warmup updates or the 160k eval is catastrophically
worse than A0/A1, stop that arm and prefer coef=0.05.
```

Result status: stopped (first overnight arm interrupted during 320k eval; runner hardened)

Result summary:

```text
Script created:
  scripts/run_r16_a2r_overnight_local_cuda.ps1

Dry-run validation 2026-07-04:
  powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File .\scripts\run_r16_a2r_overnight_local_cuda.ps1 -DryRun
  -> passed for the initial 320k default.
  After user requested a longer overnight read, the script default was changed
  to 640k and dry-run was rerun:
    total_timesteps=640000
    eval points expected at 160k/320k/480k/640k.
  The default suite expands four commands:
     a2r_roster_reward_coef01
     a2r_roster_reward_coef005
     a2_samecheck_reward_coef01
     a1r_roster_probe_reward_off

Interrupted run read 2026-07-04:
  Log root:
    logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_014614
  Arm:
    seed1\a2r_roster_reward_coef01
  User-launched length:
    total_timesteps=960000 (from command.txt)
  Observed state:
    training update 40 / total_steps 320000 completed;
    standalone_process_core_update_40.pt was saved;
    metrics\train_updates.csv contains 40 updates;
    metrics\eval_episodes.csv contains 20 episodes for 160k but only 14/20
    episodes for 320k, so the stop happened during the 320k eval.
  Error evidence:
    standalone_train.log has no main-process traceback, RuntimeError, ERROR,
    KeyboardInterrupt, or train/agent exception.  The pasted console trace
    contains worker-side BrokenPipe/EOF traces from collectors.py after the
    parent pipe closed.  Treat those worker traces as downstream symptoms,
    not root cause.
    User later reported the original script failure line:
      BrokenPipeError [WinError 232] pipe is being closed
      Experiment a2r_roster_reward_coef01 seed=1 failed with exit code
      -1073741819
    Decimal -1073741819 is Windows 0xC0000005, an access-violation/native
    crash code.  This explains why no Python main-process traceback appeared
    in standalone_train.log.  The script throw line only reported the nonzero
    Python process exit; it was not the source of the crash.
  Mechanism read up to the completed update:
    update 40 roster_ar_kl_shuffled ~= 0.00001;
    selection_independence_deficit ~= -0.031;
    proto_disc_acc ~= 0.247;
    proto_disc_residual_mean ~= 0.0;
    proto_disc_reward_mean ~= 0.0;
    env_reward_mean ~= 0.033;
    return_mean ~= 2.25.
  Interpretation:
    Current evidence is insufficient to call an algorithm-code crash.  It is
    more consistent with a Windows native crash / resource or eval-time
    subprocess failure.  The partial mechanism read is weak/negative, but not
    a complete A2r verdict because the arm did not finish its scheduled evals
    and later arms did not run.
  Runner hardening:
    scripts\run_r16_a2r_overnight_local_cuda.ps1 now writes per-arm
    runner_output.log and runner_status.txt so future main-process tracebacks
    are captured next to standalone_train.log.
  Follow-up 2026-07-04:
    The manual eval command omitted `--eval_episodes 20`, so it ran only 3
    episodes.  Combined with the interrupted eval, the 320k eval CSV now has
    17/20 rows, not a clean 20-episode read.
    Two attempted Codex-launched hidden/background runner starts
      run_20260704_074241
      run_20260704_074504
    did not produce a usable long run.  After adding explicit runner capture,
    run_20260704_074601 showed the concrete reason:
      PermissionError [WinError 5] in multiprocessing Pipe creation inside
      SubprocEnvCollector.
    Interpretation: do not treat this as an algorithm bug.  It is a Windows
    multiprocessing/subprocess permission issue caused by launching the
    training stack as a hidden detached background process from Codex.  Use an
    interactive PowerShell terminal for the overnight runner, or switch to a
    non-subproc collector for tiny smoke/debug only.  The runner script was
    restored to same-process Python invocation while retaining
    runner_output.log + runner_status.txt capture.
  Interactive rerun monitor 2026-07-04:
    User started the runner from an interactive PowerShell terminal:
      logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_074839
    Process check:
      runner powershell PID 61204
      training python PID 32680
      first arm a2r_roster_reward_coef01
    Health check:
      update 1 / 8000 steps written;
      update 2 / 16000 steps written;
      no Traceback / RuntimeError / BrokenPipe in standalone_train.log during
      the initial monitor window.
    Early mechanism read:
      update 1 roster_kl_shuf=0.000004, sel_def=-0.028535;
      update 2 roster_kl_shuf=0.000004, sel_def=0.032085.
      This is too early for a mechanism verdict.  The important immediate
      conclusion is that the interactive runner is healthy so far.
  Runner bug found 2026-07-04:
    The interactive runner's first arm later stopped at update 10 / 80000
    steps with exit_code=1, while `-ContinueOnError` advanced to the next arm.
    No Python traceback was present.  The captured output showed a matplotlib
    plotting warning (`UserWarning: Tight layout not applied`) followed by a
    PowerShell `NativeCommandError` at the native Python invocation line in
    scripts\run_r16_a2r_overnight_local_cuda.ps1.
    Root cause:
      runner-level bug.  `$ErrorActionPreference="Stop"` caused Windows
      PowerShell 5.1 to treat harmless native stderr warnings from Python as a
      terminating error, so the arm was marked failed even though the training
      code had only emitted a plotting warning.
    Fix:
      Around the Python invocation, the runner now temporarily sets
      `$ErrorActionPreference="Continue"` while still capturing all output and
      still using `$LASTEXITCODE` to detect real Python nonzero exits.  Dry-run
      validation passed after the patch.
    Operational note:
      The currently running PowerShell process was launched before this patch,
      so it will not pick up the fix.  Stop the current runner and restart from
      an interactive PowerShell terminal with the same command.
  Follow-up check 2026-07-04:
    The second arm in the same run,
    `seed1\a2r_roster_reward_coef005`, also ended with exit_code=1 and the
    same runner-level failure signature: no Python traceback, and captured
    native stderr converted into a PowerShell `NativeCommandError`.
    Interpretation:
      both `coef01` and `coef005` in run_20260704_074839 are runner-invalid
      and must not be read as algorithm failures.
    Current state at check time:
      `seed1\a2_samecheck_reward_coef01` had started and had no
      runner_status.txt yet, but it was launched by the pre-fix runner and is
      therefore expected to remain vulnerable to the same plot-warning failure.
      Preferred action remains: stop the old runner and restart the patched
      script from an interactive PowerShell terminal.
  Patched rerun check 2026-07-04:
    New log root:
      logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_085358
    Arm:
      seed1\a2r_roster_reward_coef01
    Command:
      same R16 A2r roster reward arm, total_timesteps=960000,
      ar_prefix_mode=roster, prototype_disc_reward_coef=0.1.
    Status at check:
      no runner_status.txt yet, runner_output.log length 0, and
      standalone_train.log reached update 8 / total_steps 64000 without
      Traceback / RuntimeError / BrokenPipe / PermissionError.
    Follow-up correction:
      this run was later found NOT to be a hardened-runner launch.  Its
      directory has no `run_command.cmd`, and `runner_output.log` contains the
      old PowerShell native invocation site:
        `& $command[0] @($command[1..]) *> $outputFile`
      plus a `NativeCommandError` wrapper around the matplotlib
      `plotting.py:900 fig.tight_layout()` warning.  Therefore
      `run_20260704_085358` is also vulnerable to the same false runner
      failure as `run_20260704_074839`.  If it later writes
      `runner_status.txt` with `exit_code=1` but `standalone_train.log` has no
      Python traceback, treat it as runner-invalid rather than an algorithm
      failure.
    Early read:
      update 8 roster_kl_shuf=0.000003, sel_def=0.000899,
      proto_acc=0.249, proto_resid=-0.003329, proto_reward=-0.000333,
      skill_entropy=0.999, duration_entropy=0.998.
    Follow-up status:
      update 9 / total_steps 72000 reached; no `Traceback`, `RuntimeError`,
      `BrokenPipe`, `PermissionError`, or `ERROR` in standalone_train.log.
      No eval line yet and no runner_status.txt yet.  Latest read:
        roster_ar_kl_shuffled=0.0000029
        selection_independence_deficit=0.0190
        env_reward_mean=0.0205
        return_mean=1.5925
      This remains below the first judgment point; do not interpret before the
      160k eval unless a real failure or kill rule appears.
    Interpretation:
      metrics are too early for an A2r mechanism verdict.  The active run may
      continue writing training updates, but it was launched with the old
      wrapper and can still false-fail on harmless stderr warnings.  For a
      reliable overnight run, restart from the current hardened script, which
      creates `run_command.cmd` and invokes `cmd.exe`.
  Runner hardening update 2026-07-04:
    The old run_20260704_074839 failure was re-checked from code and logs.
    `standalone_train.log` reached update 10 / 80000 steps with no Python
    traceback; `runner_status.txt` recorded exit_code=1 because PowerShell
    wrapped a matplotlib stderr warning as `NativeCommandError`.
    Code change:
      `scripts\run_r16_a2r_overnight_local_cuda.ps1` now writes a per-arm
      `run_command.cmd` and invokes it through `cmd.exe`; the batch file
      redirects Python stdout/stderr directly to `runner_output.log`.  This
      avoids Windows PowerShell 5.1 native-stderr wrapping entirely for future
      launches.  Dry-run validation passed.
    Current live old-wrapper run:
      `run_20260704_085358\seed1\a2r_roster_reward_coef01` reached update
      14 / 112000 steps; no `runner_status.txt`, no eval yet, and no
      Traceback / RuntimeError / BrokenPipe / PermissionError / ERROR in
      `standalone_train.log`.  However, this directory also has no
      `run_command.cmd`, and `runner_output.log` contains an old-wrapper
      `NativeCommandError` around the same matplotlib tight-layout warning.
      Latest read:
        roster_ar_kl_shuffled=0.0000030
        selection_independence_deficit=-0.0029
        proto_acc=0.2798
        proto_disc_reward_mean=-0.000922
        env_reward_mean=0.0127
        return_mean=0.2529
      This is still before the first 160k eval.  If uninterrupted, continue
      monitoring; if the runner exits with code 1 and no Python traceback,
      restart the hardened script rather than debugging HA-CTSE model code.
  160k monitor read 2026-07-04:
    The same old-wrapper run continued past the earlier warning:
      `run_20260704_085358\seed1\a2r_roster_reward_coef01`
      reached update 21 / total_steps 168000 and completed the 160k eval.
    Runner state:
      no `runner_status.txt`;
      no `run_command.cmd` because this is still an old-wrapper launch;
      no Traceback / RuntimeError / BrokenPipe / PermissionError / ERROR in
      `standalone_train.log`.
    160k eval:
      reward_mean=26.011100
      reward_std=43.370809
      coverage=0.131667
      qos=0.077489
      throughput=4.725000
      backhaul_connected_frac=0.284500
      zero_throughput_ep_frac=0.600000
      coverage_eq1_step_frac=0.000000
      coverage_eq1_ep_frac=0.000000
    Update-20 coordination/reward diagnostics:
      roster_ar_kl_shuffled=0.0000029
      roster_ar_kl_zeroed=0.0000037
      selection_independence_deficit=-0.0166
      proto_disc_acc=0.236
      proto_disc_residual_mean=-0.008851
      proto_disc_reward_mean=-0.000885
      proto_disc_reward_env_ratio=0.108
      high_entropy=3.794
      skill_entropy=0.999
      duration_entropy=0.996
    Interpretation:
      This is not a code-crash signature.  The previous exit-code-1 event was
      a runner-level PowerShell stderr wrapping bug.  Mechanistically, the
      first 160k read is weak/negative for R16 roster use because
      `roster_ar_kl_shuffled` remains far below the <0.01 fail band, though
      entropy and reward scale are still safe.  Continue to 320k only as a
      scheduled read; do not call PASS or FAIL from this single early point.
  200k quick snapshot 2026-07-04:
    The run is still alive after the user's interruption of Codex's long
    polling command.
    Runner/log state:
      no `runner_status.txt`;
      no `run_command.cmd` because this remains an old-wrapper launch;
      no Traceback / RuntimeError / BrokenPipe / PermissionError / ERROR in
      `standalone_train.log`;
      training process group still present under the SB3 Python environment.
    Latest train update:
      update=25
      total_steps=200000
      env_reward_mean=0.095420
      roster_ar_kl_shuffled=0.0000027
      roster_ar_kl_zeroed=0.0000037
      selection_independence_deficit=0.0085
      proto_disc_acc=0.280
      proto_disc_residual_mean=0.002802
      proto_disc_reward_mean=0.000280
      proto_disc_reward_env_ratio=0.059
      high_entropy=3.745
    Interpretation:
      No training-code failure is visible.  The A2r coordination signal remains
      essentially absent at 200k.  This still does not close the pre-registered
      320k read, but if 320k keeps the same pattern the R16 roster mechanism
      will be a clear negative for seed 1.
  224k retry snapshot 2026-07-04:
    The same run continues after the user's retry request.
    Runner/log state:
      no `runner_status.txt`;
      no `run_command.cmd` because this remains an old-wrapper launch;
      no Traceback / RuntimeError / BrokenPipe / PermissionError / ERROR /
      KeyboardInterrupt in `standalone_train.log`;
      the PowerShell runner and SB3 Python training process are still present.
    Latest train update:
      update=28
      total_steps=224000
      env_reward_mean=0.042657
      roster_ar_kl_shuffled=0.0000029
      roster_ar_kl_zeroed=0.0000041
      selection_independence_deficit=0.0120
      proto_disc_acc=0.271
      proto_disc_residual_mean=-0.002453
      proto_disc_reward_mean=-0.000245
      proto_disc_reward_env_ratio=0.095
      high_entropy=3.795
    Interpretation:
      Retry confirms no real training-code failure.  The mechanism signal is
      still effectively absent: `roster_ar_kl_shuffled` remains orders of
      magnitude below the <0.01 fail band.  Continue only to the 320k gate read
      or until a real traceback appears; do not restart while the process is
      alive solely because this old-wrapper launch is vulnerable to false
      runner failures.
  Hardened-run progress snapshot 2026-07-04:
    After suppressing harmless plotting `tight_layout` warnings and using the
    hardened cmd-wrapper runner, the current valid run is:
      `run_20260704_142053\seed1\a2r_roster_reward_coef01`
    Runner/log state:
      `runner_status.txt` exists and says `state=running`;
      `run_command.cmd` exists;
      `runner_output.log` is UTF-8 and no longer shows the old
      `NativeCommandError` wrapper;
      no Traceback / RuntimeError / NaN in `standalone_train.log`;
      SB3 Python process group is present and GPU memory is allocated.
    Latest train update:
      update=25
      total_steps=200000
      env_reward_mean=0.103115
      roster_ar_kl_shuffled=0.000003
      roster_ar_kl_zeroed=0.000004
      selection_independence_deficit=-0.003596
      proto_disc_acc=0.251
      proto_disc_residual_mean=0.001680
      proto_disc_reward_mean=0.000168
      high_entropy=3.764
      skill_entropy=0.997
      duration_entropy=0.960
    160k eval:
      reward_mean=34.534953
      reward_std=62.707836
      coverage=0.128333
      qos=0.107687
      throughput=7.118133
      backhaul_connected_frac=0.312000
      zero_throughput_ep_frac=0.600000
      coverage_eq1_step_frac=0.000000
      coverage_eq1_ep_frac=0.000000
    Interpretation:
      The runner fix appears effective: the current launch is the first clean
      hardened-run read.  Mechanistically, however, the R16 roster signal is
      still near zero at 200k, so this remains a weak/negative early read.
      Wait for the pre-registered 320k gate before closing seed 1.
  Hardened-run 256k progress snapshot 2026-07-04:
    Current valid run:
      `run_20260704_142053\seed1\a2r_roster_reward_coef01`
    Runner/log state:
      `runner_status.txt` still says `state=running`;
      no Traceback / RuntimeError / BrokenPipe / PermissionError / CUDA OOM /
      NaN / ERROR in `standalone_train.log`;
      SB3 Python process group remains present and GPU memory remains
      allocated.
    Latest train update:
      update=32
      total_steps=256000
      env_reward_mean=0.034335
      roster_ar_kl_shuffled=0.000004
      roster_ar_kl_zeroed=0.000004
      selection_independence_deficit=-0.004722
      proto_disc_acc=0.312
      proto_disc_residual_mean=0.015358
      proto_disc_reward_mean=0.001536
      high_entropy=3.724442
      skill_entropy=0.999
      duration_entropy=0.970
    Interpretation:
      The process is healthy and has not reached the 320k gate yet.  The R16
      roster-use signal remains effectively absent (`roster_ar_kl_shuffled`
      still far below the <0.01 fail band), but this remains a progress read,
      not the pre-registered gate decision.
```

Next decision:

```text
Read the current hardened run `run_20260704_142053` at the pre-registered
320k gate, or earlier only if `runner_status.txt` changes from `state=running`
or a real traceback appears.  Do not decide R16 from the 200k snapshot.
```

### EXP-20260703-r14-stage1-prototype-selection

Experiment name: `r14_stage1_prototype_selection`

Created at: 2026-07-03

Planned location: local CUDA first; cloud only after local diagnostic read is non-degenerate.

Command/script:

```powershell
# Preview commands only.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r14_stage1_local_cuda.ps1 `
  -Experiments control,s1_probe,s1_reward `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda `
  -DryRun

# Actual local CUDA run.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r14_stage1_local_cuda.ps1 `
  -Experiments control,s1_probe,s1_reward `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Code snapshot / changed files:

```text
R14 Stage 1 prototype-response implementation:
  ha_ctse_process/prototype_response_discriminator.py
  ha_ctse_process/situation_substrate.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/g_info_objective.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  scripts/run_r14_stage1_local_cuda.ps1
  tests/r14_prototype_response_test.py
  docs/superpowers/plans/2026-07-03-r14-stage1-prototype-selection.md
```

Purpose:

```text
Test Round 14 Stage 1: use OPT prototype structure as the coordinate system for
sampled prototype-response skills, then probe whether an individual per-step
situation-conditioned discriminator provides non-vacuous dense pressure without
communication-specific reward or HMASD legacy entanglement.
```

Hypothesis:

```text
If skill codes are responses to OPT prototypes rather than arbitrary labels,
then q(z_i | o_{i,t+1}, situation) should beat p(z_i | situation), residual
prototype-disc reward should be non-degenerate, and forced/selected response
skills should show behavioral spread without collapsing skill or duration usage.
```

Controls / comparison:

```text
control:
  reward-pure baseline, no R14 prototype-response flags.

s1_probe:
  prototype-response skills enabled, high policy conditioned on omega and
  per-agent prototype relevance, per-agent kappa diagnostics enabled, prototype
  discriminator trained as diagnostic only.

s1_reward:
  same as s1_probe plus low-only prototype-disc residual reward after warmup.
```

Metrics to read:

```text
proto_disc_acc
proto_disc_prior_acc
proto_disc_residual_mean
proto_disc_residual_positive_frac
proto_disc_acc_by_skill_std
proto_disc_reward_mean
proto_disc_reward_applied_steps
proto_disc_reward_env_ratio
proto_skill_selection_entropy
proto_skill_usage_entropy_by_kappa
proto_skill_relevance_alignment
proto_skill_selected_relevance_mean
proto_omega_nonzero_frac
proto_bank_drift_cos
proto_rel_row_entropy_mean
proto_rel_argmax_dwell_median
proto_rel_stability_cos
proto_rel_drop_event_rate_05 / _03 / _01
situation_agent_kappa_enabled
situation_agent_kappa_change_rate
situation_agent_kappa_disagreement_rate
situation_agent_kappa_median_dwell
situation_agent_kappa_global_mi
situation_agent_unique_kappa_mean
compact_return_loss / compact_return_active (only if compact return head is enabled)
effect_intervention_active
effect_intervention_action_l2_mean
effect_intervention_pred_effect_l2_mean
effect_intervention_best_skill_gap
skill_usage_entropy
duration_usage_entropy
segment_length_mean
coverage_eq1_step_fraction / coverage_eq1_episode_fraction
coverage / qos / throughput
zero_throughput_episode_fraction
throughput_gt5_step_fraction
reward_mean / reward_std
process_reward_high_mean / process_reward_low_mean
```

Current behavioral-spread caveat:

```text
The R14 runner enables the existing reward-off `effect_intervention_*` proxy
diagnostics across all arms.  These measure action-distribution and predicted
effect changes under forced z.  They are NOT yet exact forced-z rollout
trajectory spread at h={10,50}.  Treat them as the first local proxy read; if
the proxy is promising or ambiguous, implement exact rollout trajectory spread
before the Stage-2 go decision.
```

Meaning of possible outcomes:

```text
Probe residual positive, reward arm neutral-to-positive, no entropy collapse:
  continue to R14 Stage 2 omega-space commitment / validity hazard.

Probe residual positive but reward arm hurts task metrics or collapses usage:
  keep diagnostic/probe, retune reward scale or warmup, and do not proceed to
  long cloud runs until low-only injection is stable.

Probe residual near zero or prior matches q:
  prototype-response discriminator is not providing non-vacuous pressure; do
  not add team transition reward on top.  Revisit prototype grounding / compact
  return head or run recognition-Z HMASD control.

Reward guards or process/topology semantic rewards become nonzero:
  invalid run; R14 Stage 1 must stay independent of previous process posterior,
  transition discriminator, topology-role reward, and communication-specific
  shaping paths.
```

Stop / continue rule:

```text
Do not proceed to R14 Stage 2 or cloud performance sweeps unless s1_probe shows
non-degenerate residual signal and s1_reward does not regress basic task metrics
or collapse duration/skill entropy during the 320k local read.

Red flags from the Claude plan update:
  proto_disc_reward_env_ratio > 1.0
    -> discriminator reward dominates env return; stop reward arm and read.
  proto_disc_acc ~= proto_disc_prior_acc persistently
    -> no behavioral separation signal; fix conditioning/capacity before coef work.
  proto_skill_usage_entropy_by_kappa < 50% of uniform
    -> situation-to-skill lookup collapse.
  proto_bank_drift_cos < 0.9
    -> prototype-response semantics are drifting.
  proto_omega_nonzero_frac ~= 1 / opt_num_prototypes
    -> prototype collapse / uniformity risk.
  zero_throughput_episode_fraction or reward variance worsens vs control
    -> do not claim improvement from reward_mean.
```

Result status: interrupted by R14 s1_probe bug; fix applied, restart pending.

R15 supersession note 2026-07-03:

```text
Round 15 has superseded the normal R14.1 prototype-response residual design.
The accepted target is AR-first response selection and coordinator-residual
reward:

  log q_d(z_i | o'_i, kappa) - stored log pi_h(z_i | kappa, z_{1:i-1})

The current code still implements the pre-R15 learned situation-prior head and
residual q_logp - prior_logp.  Therefore the old unfinished s1_probe/s1_reward
restart is paused.  Run it only if it is explicitly relabeled as the R15-P1 /
R14.1 learned-prior fallback ablation.
```

Result summary:

```text
Implementation validation complete:
  - `pytest tests\r14_prototype_response_test.py -q`: 3 passed.
  - AST parse OK for standalone_agent.py, prototype_response_discriminator.py,
    g_info_objective.py, situation_substrate.py, train.py, plotting.py.
  - Runner dry-run OK for control, s1_probe, s1_reward.
  - Tiny probe-only train smoke OK; prototype discriminator metrics reached
    console/CSV and process reward stayed zero.
  - Tiny reward-on train smoke OK with warmup=0; low-only prototype reward was
    applied and process reward stayed zero.
  - Checkpoint save/load/eval smoke OK for the new structure metadata.
  - After the Claude plan update, runner/metrics were tightened:
      * control/probe/reward arms now explicitly disable legacy process MI,
        outcome residual, topology role, transition-skill discriminator, and
        process reward paths;
      * all arms enable reward-off skill-effect intervention diagnostics so
        forced-z trajectory/action spread can be compared against control;
      * J3-calibration prototype relevance metrics are logged:
        proto_rel_row_entropy_mean, proto_rel_argmax_dwell_median,
        proto_rel_stability_cos, proto_rel_drop_event_rate_05/_03/_01.
      * subagent review found and Codex fixed three metric semantics:
        `proto_skill_usage_entropy_by_kappa` now groups by `kappa_start`, not
        team code; `proto_skill_relevance_alignment` is normalized MI between
        skill and argmax relevance, with selected relevance weight kept as
        `proto_skill_selected_relevance_mean`; and `proto_disc_reward_env_ratio`
        is logged as a prospective scale preview from update 1, even before
        reward warmup applies.
      * runner accepts `-Seed` for seed2 follow-up.
  - Post-adjustment validation:
      * `pytest tests\r14_prototype_response_test.py -q`: 3 passed.
      * runner dry-run OK with `-Seed 2`.
      * AST parse OK for touched Python files.
      * tiny sync s1_probe smoke OK; CSV header contains the new proto_rel,
        selected relevance, per-agent kappa dwell, reward/env ratio, and
        effect_intervention fields.

Known validation caveat:
  py_compile attempted to write `.pyc` files and hit Windows permission-denied
  on existing __pycache__ paths.  No-write AST parsing was used instead.

Local run progress 2026-07-03:
  Actual process:
    scripts\run_r14_stage1_local_cuda.ps1
      -Experiments control,s1_probe,s1_reward
      -TotalTimesteps 320000
      -NumEnvs 32
      -Device cuda

  Current arm:
    logs\ha_ctse_r14_stage1_local_cuda\run_20260703_121810\control_reward_pure

  Progress at inspection:
    update=7
    total_steps=112000 / 320000
    first eval at 160000 not reached yet
    log was still updating, so training was alive

  Latest update metrics:
    env_reward_mean=0.037571
    return_mean=2.007720
    segment_length_mean=107.02
    skill_switch_rate=0.653
    duration_usage_entropy=0.995
    skill_usage_entropy=0.998
    situation_change_rate=0.013
    credit_disc=0.586
    credit_recover=0.000
    credit_bh_frac=0.203
    credit_bh_thr=3.479

  R14-specific read:
    This is the control arm, so prototype-response flags are off:
      prototype_response=False
      proto_disc_probe=False
      proto_disc_reward=False
    Therefore proto_disc/proto_reward fields staying 0 is expected and is not
    evidence against R14.

  Diagnostic caveat:
    metrics/train_updates.csv currently contains a duplicate header
    `situation_agent_unique_kappa_mean`, so PowerShell Import-Csv fails.
    Low-level CSV parsing still works.  This should be fixed after the run or
    before relying on PowerShell CSV tooling, but it does not invalidate the
    current training data.

Local run progress 2026-07-03 second read:
  control_reward_pure completed:
    train updates=20
    total_steps=320000
    final update env_reward_mean=0.056403
    final update return_mean=2.783649
    final update segment_length_mean=111.89
    final update skill_switch_rate=0.653
    final update duration_usage_entropy=0.990
    final update skill_usage_entropy=0.999

  control eval:
    160k, 20 episodes:
      reward_mean=19.855
      coverage_ratio_mean=0.093
      qos_mean=0.075
      throughput_mean=4.484
      backhaul_connected_step_fraction_mean=0.233
      coverage_eq1_step_fraction_mean=0.0
      zero_throughput_episode_flag_mean=0.65
      throughput_gt5_episode_flag_mean=0.35
    320k, 20 episodes:
      reward_mean=32.689
      coverage_ratio_mean=0.143
      qos_mean=0.097
      throughput_mean=8.667
      backhaul_connected_step_fraction_mean=0.312
      coverage_eq1_step_fraction_mean=0.0
      zero_throughput_episode_flag_mean=0.60
      throughput_gt5_episode_flag_mean=0.40

  current arm:
    logs\ha_ctse_r14_stage1_local_cuda\run_20260703_121810\s1_probe_no_reward

  s1_probe_no_reward status:
    process running
    run_manifest and standalone_train.log created
    no train_updates.csv yet at inspection, so it has not completed its first
    rollout/update
    flags confirm the intended probe arm:
      prototype_response=True
      high_omega=True
      agent_proto_rel=True
      per_agent_kappa=True
      proto_disc_probe=True
      proto_disc_reward=False

Crash and fix 2026-07-03:
  s1_probe_no_reward crashed during first high update:
    RuntimeError in `ha_ctse_process/g_info_objective.py`
    omega batch had 925 rows while g-info diagnostic had sub-sampled high_obs
    to max_segments=256.

  Root cause:
    `GInfoObjective.forward()` deterministically sub-sampled
    high_obs/prev_skills/ages/compact when batch_size > max_segments, but did
    not apply the same `chosen` index to optional `omega` and
    `agent_relevance`.  R14 s1_probe enables high_omega and agent_proto_rel, so
    the optional tensors were present and kept their full segment count.

  Fix:
    `ha_ctse_process/g_info_objective.py`
      - when sub-sampling g-info diagnostics, also index_select `omega` and
        `agent_relevance` with the same chosen rows.

    `tests/r14_prototype_response_test.py`
      - added `test_g_info_objective_subsamples_optional_omega_and_relevance`,
        which failed before the fix with the same shape-mismatch class and now
        passes.

  Validation:
    `python -m pytest tests\r14_prototype_response_test.py -q`
      -> 4 passed

    no-write AST parse for:
      ha_ctse_process/g_info_objective.py
      tests/r14_prototype_response_test.py
      -> AST_OK

  Process status after crash:
    no active `ha_ctse_process.train` / `run_r14_stage1_local_cuda.ps1` process
    remained at inspection.
```

Next decision:

```text
Control is already a complete baseline, but do not restart the unfinished arms
under the old normal-path interpretation.  First implement R15 Stage-1
alignment:

  - AR-first per-agent response assignment when prototype-response skills are on;
  - store each selected agent assignment log-prob over the skill lifetime;
  - use the stored coordinator log-prob as the discriminator null;
  - remove/disable the learned prior head from the normal path;
  - expose the old learned-prior / parallel-selection path only as the labeled
    R15-P1 fallback ablation;
  - log proto_disc_null_logp_mean and proto_ar_parallel_kl;
  - update tests for null broadcast and AR log-prob storage.

Historical pre-R15 restart command, only for the R15-P1/R14.1 fallback ablation:

  powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File .\scripts\run_r14_stage1_local_cuda.ps1 `
    -Experiments s1_probe,s1_reward `
    -TotalTimesteps 320000 `
    -NumEnvs 32 `
    -Device cuda

After R15 code alignment, rerun s1_probe_no_reward to at least 160k and
preferably 320k, then compare:
  proto_disc_acc vs proto_disc_prior_acc
  proto_disc_null_logp_mean and coordinator-residual mean
  proto_ar_parallel_kl
  proto_disc residual/reward preview
  proto_skill_usage_entropy_by_kappa
  proto_rel_* calibration metrics
  effect_intervention action/pred-effect spread
  basic task metrics versus the completed control baseline

Do not interpret s1_reward until s1_probe shows non-vacuous residual signal.

User clarification 2026-07-03:
  HMASD convergence on S7-S1 should be judged around the 1e6-step scale, where
  it can maintain high average coverage.  This R14 320k run is not a fair final
  performance comparison against HMASD.  It is a mechanism gate: use it to
  reject collapse / reward contamination / vacuous discriminator pressure, or
  to justify a longer ~1e6-step follow-up if s1_probe and s1_reward are viable.
```

Local restart read 2026-07-03 (run_20260703_154805):

```text
Actual process found at inspection:
  scripts\run_r14_stage1_local_cuda.ps1
    -Experiments s1_probe,s1_reward
    -TotalTimesteps 320000
    -NumEnvs 32
    -Device cuda

Current arm:
  logs\ha_ctse_r14_stage1_local_cuda\run_20260703_154805\s1_probe_no_reward

Progress:
  update=10
  total_steps=160000 / 320000
  160k eval completed
  no R15 run directory exists yet

160k structural read:
  proto_acc=0.251
  proto_prior_acc=0.263
  proto_resid=-0.002337
  proto_reward=0.000000
  proto_skill_ent=0.998
  proto_kappa_ent=0.986
  proto_align=0.005
  proto_rel_dwell=2.0
  credit_disc=0.766
  credit_recover=0.011
  credit_bh_frac=0.135
  g_itv=0.023917

160k eval:
  reward_mean=28.727952
  coverage=0.121667
  throughput=5.515777
  backhaul_connected_frac=0.252000
  coverage_eq1_step_frac=0.000000
  zero_throughput_ep_frac=0.700000

Decision:
  STOP-RECOMMENDED.  This is a pre-R15 R14 restart, while the active mainline
  is R15 AR-first coordinator-residual steering.  It does not log the R15
  required `proto_ar_parallel_kl` / stored-null-path readout and it tests the
  superseded learned-prior/probe framing.  The 160k probe signal is also weak:
  proto_acc is not above the prior, proto_resid is negative, proto_align is
  near zero, and coverage_eq1_step_frac remains zero.  Continuing to 320k or
  entering s1_reward would burn time on a stale gate.  Preserve this run only
  as a stale R14/R15-P1-style reference if needed.

Next command should be the R15 A0+A1 run:
  scripts\run_r15_stage1_local_cuda.ps1 -Experiments control_legacy4,s1_probe
```

### EXP-20260703-r12-1b-conservative-renewal

Experiment name: `r12_1b_conservative_renewal`

Created at: 2026-07-03

Planned location: local CUDA first.

Command/script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments diag_only,oracle_conservative,oracle_strict `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Code snapshot / changed files:

```text
R12-1b conservative renewal implementation:
  ha_ctse_process/situation_hazard.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/plotting.py
  scripts/run_r12_stage1_local_cuda.ps1
  tests/r12_conservative_renewal_test.py
  docs/superpowers/plans/2026-07-03-r12-1b-conservative-renewal.md
```

Purpose:

```text
Test whether conservative situation-change renewal removes the churn observed
in R12-1a oracle_change while keeping reward path pure.
```

Hypothesis:

```text
Stronger dwell/confirmation and a forced-renewal-rate cap should keep useful
situation boundaries while avoiding frequent reactive renewal.
```

Round 13 interpretation caveat (Claude/Codex cross-validation, 2026-07-03):

```text
Current R12-1b does NOT test a true per-agent situation-validity hazard.
`assign_kappa_from_omega` produces one env-global kappa, and the renewal loop
feeds the same `situation_state.changed` pulse to every eligible agent.  Only
skill age and conservative guard state are per-agent.

Therefore this experiment is a guarded env-global boundary trigger diagnostic:
it can say whether the current global-boundary renewal criterion is less harmful
when rate/confirmation/dwell guarded, but it cannot validate or falsify the
Round-12 design requirement of per-agent `kappa_i` / `beta_i`.
```

Controls / comparison:

```text
diag_only:
  situation diagnostics only.

oracle_conservative:
  min_age=30, min_dwell=3, confirm_changes=2, max_force_rate=0.03.

oracle_strict:
  min_age=50, min_dwell=5, confirm_changes=3, max_force_rate=0.015.
```

Metrics to read:

```text
situation_hazard_forced_renewal_rate
situation_hazard_guard_event_count
situation_hazard_guard_allow_rate
situation_hazard_guard_confirm_block_rate
situation_hazard_guard_dwell_block_rate
situation_hazard_guard_rate_cap_block_rate
situation_hazard_guard_recent_force_rate
segment_length_mean
skill_switch_rate
duration_usage_entropy
skill_usage_entropy
coverage_eq1_step_frac
zero_throughput_ep_frac
reward_mean / reward_std
process_reward_high_mean / process_reward_low_mean
force_reward_low_mean
effect_reward_low_mean
topology_potential_low_mean
```

Meaning of possible outcomes:

```text
conservative arm neutral-to-positive vs diag_only:
  do not jump directly to learned_beta PPO.  Add two controls first:
    random_matched   = forced renewals at matched oracle_conservative rate but
                       random times;
    boundary_gated   = do not force renewal at boundaries, only allow/mask
                       renewal at boundaries.

conservative arm still worse but guard allows many renewals:
  do not keep tuning guard constants.  Run G-ACTIONABILITY and revisit the
  renewal criterion / per-agent kappa_i design.

conservative arm blocks almost everything:
  treat as an inconclusive guard diagnostic only; it still does not validate
  per-agent hazard semantics.

reward guards nonzero:
  invalid run.
```

Stop / continue rule:

```text
Do not proceed to learned_beta PPO unless a conservative oracle arm is
neutral-to-positive on stability without entropy collapse and without reward
contamination, and the follow-up random_matched / boundary_gated controls show
that boundary timing has value beyond renewal rate.
```

Result status: running / partial read 2026-07-03.

Partial read 2026-07-03:

```text
Local run root:
  logs\ha_ctse_r12_stage1_local_cuda\run_20260703_102200

Current process:
  scripts\run_r12_stage1_local_cuda.ps1
  -Experiments diag_only,oracle_conservative,oracle_strict
  -TotalTimesteps 320000 -NumEnvs 16 -Device cuda

Important correction:
  The running job is NOT the active R14 prototype-response experiment.  It is
  the R12-1b side diagnostic, and it was still on the first
  `diag_only_reward_pure` arm at the time of inspection.

diag_only_reward_pure train updates:
  update=40 / total_steps=320000 completed.
  last10 env_reward_mean ~= 0.0647
  last10 return_mean ~= 3.4963
  last10 segment_length_mean ~= 123.07
  last10 skill_switch_rate ~= 0.638
  last10 duration_usage_entropy ~= 0.957
  last10 skill_usage_entropy ~= 0.995
  last10 situation_change_rate ~= 0.0062
  situation_hazard_forced_renewal_rate = 0.0 as expected for diag_only.

eval:
  160k completed, 20 episodes:
    reward_mean=25.244
    coverage_ratio_mean=0.098
    qos_mean=0.088
    throughput_mean=5.765
    backhaul_connected_step_fraction_mean=0.230
    coverage_eq1_step_fraction_mean=0.0
    zero_throughput_episode_flag_mean=0.75
    throughput_gt5_episode_flag_mean=0.25

  320k was still in progress during inspection, 8/20 episodes written:
    reward_mean=32.055
    coverage_ratio_mean=0.192
    qos_mean=0.115
    throughput_mean=7.726
    backhaul_connected_step_fraction_mean=0.242
    coverage_eq1_step_fraction_mean=0.0
    zero_throughput_episode_flag_mean=0.75
    throughput_gt5_episode_flag_mean=0.25

Interpretation:
  The first arm remains bimodal and far from the user-defined parity target
  (`coverage == 1.0` for at least half of primitive evaluation steps).
  Since this is only the diag baseline for a side diagnostic, it cannot answer
  the R14 prototype-response question.  If local compute is needed for the main
  line, stop/defer the remaining R12-1b conservative/strict arms after the
  current 320k eval finishes and launch EXP-20260703-r14-stage1-prototype-
  selection instead.
```

Result summary:

```text
Implementation validation complete:
  - SPEC_PASS from subagent review.
  - QUALITY_PASS from subagent review.
  - `python -m pytest tests\r12_conservative_renewal_test.py -q`: 7 passed.
  - AST parse OK for six touched Python files.
  - Stage 1 runner dry-run OK for diag_only, oracle_conservative, oracle_strict.
  - Tiny sync smoke OK; conservative guard metrics reached CSV and reward guards
    remained zero.

Known local artifact:
  `tests\test_r12_conservative_renewal.py` is an ignored migration copy that
  could not be deleted due Windows Access denied. Use the tracked
  `tests\r12_conservative_renewal_test.py` path.
```

Next decision:

```text
Run the local CUDA first read, but read it as a global-boundary guard/rate
diagnostic only.

If a conservative oracle arm is neutral-to-positive against diag_only:
  add random_matched + boundary_gated controls before learned_beta PPO.

If neither conservative oracle arm is neutral-to-positive:
  run G-ACTIONABILITY and revisit the renewal criterion; do not tune guard
  constants as if the per-agent hazard hypothesis had been tested.
```

### EXP-20260702-r12-stage1-situation-hazard

Experiment name: `r12_stage1_situation_hazard`

Created at: 2026-07-02

Planned location: local CUDA first.

Command/script:

```powershell
# Dry-run first; should print commands only.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments diag_only,oracle_change `
  -TotalTimesteps 32000 `
  -NumEnvs 4 `
  -DryRun

# First local read: diagnostic-only vs reward-pure oracle renewal.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments diag_only,oracle_change

# Optional exploratory arm only; learned_beta is inference-only in the current
# code and should not be interpreted as a trained hazard policy yet.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_local_cuda.ps1 `
  -Experiments learned_beta_small
```

Code snapshot / changed files:

```text
Round 12 Stage 1 situation substrate diagnostics and default-off hazard renewal
control are expected to be present in the working tree before launch.

Experiment runner / records:
  scripts/run_r12_stage1_local_cuda.ps1
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md

Before interpreting real runs, verify the exact git diff or commit hash used
for the launch and mark this entry stale if code changed afterward.
```

Purpose:

```text
Test whether the validated OPT situation substrate can drive reward-pure skill
renewal without adding intrinsic reward or communication-specific shaping.
```

Hypothesis:

```text
Debounced kappa changes identify meaningful situation boundaries.  The
oracle_change arm should improve coverage stability or reduce variance by
renewing eligible active skills at those boundaries, while preserving
duration/skill entropy and keeping all SEF/DADS or communication-shaped rewards
off.
```

Controls / comparison:

```text
diag_only:
  Log kappa/change metrics with no hazard control.

oracle_change:
  Enable reward-pure hazard control and renew eligible active skills when the
  debounced kappa changes after the minimum age.

learned_beta_small:
  Exploratory only.  The current code can sample learned_beta for renewal, but
  it does not yet train a hazard policy update path and must not be treated as
  evidence for a learned hazard mechanism.
```

Metrics to read:

```text
situation_change_rate
situation_unique_kappa
situation_segment_change_frac
situation_hazard_forced_renewal_rate
situation_hazard_control_enabled
duration_usage_entropy
skill_entropy
coverage_eq1_step_fraction
reward_mean and reward_std
force/process/topology intrinsic reward guards, which should remain zero unless
explicitly enabled
```

Meaning of possible outcomes:

```text
oracle_change improves coverage_eq1_step_fraction or reduces variance without
collapsing duration/skill entropy:
  Keep Stage 1 and design learned_beta PPO properly.

oracle_change hurts and diagnostics show high churn:
  Add stronger debounce/min-age before learned_beta.

diag_only shows kappa nearly static or one-step noisy:
  Return to substrate representation rather than adding rewards.

learned_beta_small differs from oracle_change:
  Treat as a wiring/exploration signal only until the learned hazard policy has
  a real update path.
```

Stop / continue rule:

```text
Stop local Stage 1 runs if reward guards become nonzero without explicit
enablement, if duration/skill entropy collapses, or if diagnostics show kappa is
too noisy/static to support renewal.  Continue to learned hazard training design
only if diag_only is well-behaved and oracle_change is neutral-to-positive on
coverage stability without reward-path contamination.
```

Result status: completed

Result summary:

```text
2026-07-03 00:04 local automation launch (superseded/invalid path):
  Windows scheduled task:
    HA-CTSE R12 Stage1 Overnight
  Automation wrapper:
    scripts/run_r12_stage1_after_current.ps1
  Scheduled runner:
    scripts/run_r12_stage1_local_cuda.ps1
  Requested arms:
    diag_only, oracle_change
  Requested setup:
    CUDA, 16 envs, 320k steps, poll_seconds=300, max_wait_hours=18
  Automation log:
    logs\ha_ctse_r12_stage1_overnight_auto\_automation\r12_stage1_after_current_20260703_000438.log

The wrapper found no active `ha_ctse_process.train` process at launch time and
therefore immediately started the Stage 1 runner.  A validation read detected
that the first runner reused the fixed log directory
`logs\ha_ctse_r12_stage1_local_cuda\diag_only_reward_pure`, which already
contained old updates/checkpoints.  The contaminated run and its child
processes were stopped; do not use that fixed directory for readout.

2026-07-03 00:15 clean automation relaunch:
  Runner fix:
    scripts/run_r12_stage1_local_cuda.ps1 now writes every invocation under
    `logs\ha_ctse_r12_stage1_local_cuda\run_<timestamp>\...`.
  Active clean run root:
    logs\ha_ctse_r12_stage1_local_cuda\run_20260703_001552
  Active first arm:
    logs\ha_ctse_r12_stage1_local_cuda\run_20260703_001552\diag_only_reward_pure
  Process check:
    active `ha_ctse_process.train` command uses the timestamped clean log_dir.

This run is still a local pre-run/readout, not final performance evidence.
Keep SEF/DADS reward and communication-specific shaping out of interpretation.

2026-07-03 clean run result:
  Run root:
    logs\ha_ctse_r12_stage1_local_cuda\run_20260703_001552
  Automation status:
    completed with exit code 0.
  Arms completed:
    diag_only_reward_pure: 40 updates / 320k steps.
    oracle_change_reward_pure: 40 updates / 320k steps.

Final eval at 320k:
  diag_only:
    reward_mean=31.517343, reward_std=47.021388
    coverage=0.136667, qos=0.087169, throughput=8.376547
    backhaul_connected_frac=0.324900
    coverage_eq1_step_frac=0.000000
    zero_throughput_ep_frac=0.600000
  oracle_change:
    reward_mean=27.361690, reward_std=65.803590
    coverage=0.100000, qos=0.084123, throughput=6.761627
    backhaul_connected_frac=0.200000
    coverage_eq1_step_frac=0.000000
    zero_throughput_ep_frac=0.800000

Last-10 update structural read:
  diag_only:
    situation_change_rate=0.025788
    situation_segment_change_frac=0.457012
    forced_renewal_rate=0.000000
    switch_rate=0.636560
    segment_length_mean=117.20
    skill_entropy=0.993899
    duration_entropy=0.976588
    credit_recovery_rate=0.018160
  oracle_change:
    situation_change_rate=0.040800
    situation_segment_change_frac=0.754170
    forced_renewal_rate=0.041318
    switch_rate=0.681005
    segment_length_mean=85.49
    skill_entropy=0.996251
    duration_entropy=0.976553
    credit_recovery_rate=0.008675

Reward purity:
  process/high/low, force/effect/topology low reward guards all stayed 0.0.
```

Next decision:

```text
Stage 1 wiring works, but the oracle_change gate failed.  Do not proceed to
learned_beta PPO yet.  Next stage should be R12-1b conservative situation-change
renewal: stronger debounce/min_age/hysteresis or a forced-renewal-rate cap, then
rerun against diag_only.  If conservative oracle renewal still hurts, return to
substrate representation / renewal criterion before SEF/DADS reward.
```

### EXP-20260702-substrate-gate

Experiment name: `r12_opt_substrate_gate`

Created at: 2026-07-02

Planned location: local first, cloud only after the eval-only dump and offline
gate scripts are verified.

Command/script:

```powershell
# 1. zero-new-run CSV triage over existing HA-CTSE logs.
& "C:\Users\wu\.conda\envs\SB3\python.exe" scripts\analyze_r12_csv_triage.py `
  --root logs `
  --output logs\r12_substrate_gate_local\csv_triage.json

# 2. print the exact checkpoint-grid export/analyze commands.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local `
  -Updates 20,40,60,final `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cpu `
  -DryRun

# 3. run the diagnostic-only checkpoint-grid export and offline gate analysis.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local `
  -Updates 20,40,60,final `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cpu
```

Code snapshot / changed files:

```text
Implemented diagnostic-only tooling; no reward-path or training-path change.

Files:
  ha_ctse_process/substrate_gate.py
  ha_ctse_process/export_substrate_gate.py
  scripts/analyze_r12_csv_triage.py
  scripts/analyze_r12_substrate_gate.py
  scripts/run_r12_substrate_gate_local.ps1
  tests/test_r12_substrate_gate.py
```

Purpose:

```text
Pre-register the Round 12 Stage-0 gate before reading new dump data.  The goal
is to decide whether OPT omega/c is a real situation substrate for
Situation-Response Skill Discovery, rather than a drifting embedding.
```

Hypothesis:

```text
omega_t / c_t should encode slow interaction situations that:
  1. persist longer than a single check interval,
  2. predict existing episode modes beyond simple shortcuts,
  3. align nontrivially with generic topology-role counterfactual labels.
```

Controls / comparison:

```text
- G-DWELL: block-shuffled null over the same trajectories.
- G-OUTCOME: simple-feature baseline using existing non-learned fields.
- G-ROLE: permuted topology-role labels.
- Checkpoint grid: frozen encoder x early/mid/late policy checkpoints, plus
  best-vs-worst episode contrast.  Latest-checkpoint-only export is invalid for
  this gate.
```

Metrics to read:

```text
Zero-new-run CSV triage:
  opt_aggregation_entropy
  opt_cd_loss
  opt_cmi_loss
  compact_norm_mean

Eval-only dump:
  omega_tau / OPT aggregation weights
  c_tau / compact norm
  per-entity argmax prototype or membership summary
  delta_omega
  existing episode-mode fields: zero-throughput / coverage-positive split
  topology-role counterfactual labels

Gate metrics:
  g_dwell_median_intervals
  g_dwell_transition_diag_minus_null
  g_outcome_auc
  g_outcome_auc_minus_simple_baseline
  g_role_label_variance
  g_role_max_label_fraction
  g_role_mi_minus_permutation
  g_role_stability_minus_permutation
```

Pre-registered thresholds:

```text
G-DWELL passes only if:
  median dwell >= 3 check intervals AND
  transition diagonal mass exceeds the block-shuffled null by >= 0.20.

G-OUTCOME passes only if:
  cross-validated AUC >= max(0.60, simple-feature-baseline AUC + 0.05),
  using the existing zero-throughput / coverage-positive episode-mode split.

G-ROLE is valid only if:
  role-label variance > 0 AND max role-label fraction < 0.95.

G-ROLE passes only if:
  MI >= permuted-label MI mean + 2 std AND
  within-phase membership stability exceeds the permuted baseline by >= 0.10.
```

Meaning of possible outcomes:

```text
All gates pass:
  Proceed to reward-pure situation-change hazard and compare against fixed-best
  / discrete-duration controls.

omega fails but compact c has structure:
  Cluster c instead of raw omega, then re-run the same substrate gate.

omega and c both fail:
  Allow exactly one offline situation-ness encoder retrain on pooled logs
  (slowness, next-omega predictability, discreteness), then re-gate.

retrain fails:
  Validate the Round 12 paradigm using hand-crafted topology situation classes
  before spending more effort on learned omega.
```

Stop / continue rule:

```text
Do not implement SEF/DADS reward, target-situation commitment, co-edit AR, or a
new g-response branch until this gate is read.  Do not report G-ROLE if the
counterfactual role-label variance assertion fails.  Do not accept a
latest-checkpoint-only export as satisfying the gate.
```

Result status: implementation complete; full local checkpoint-grid gate read
after compact-vector fallback instrumentation.

Result summary:

```text
2026-07-02 implementation smoke:
  - pytest tests\test_r12_substrate_gate.py: 38 passed.
  - py_compile passed for the new gate/export/analyzer modules.
  - PowerShell dry-run printed exporter and analyzer commands.
  - Tiny local checkpoint export/analyze smoke passed:
      logs\r12_substrate_gate_smoke_dump\substrate_steps.csv
      logs\r12_substrate_gate_smoke_dump\substrate_roles.csv
      logs\r12_substrate_gate_smoke_dump\substrate_gate_report.json
    The tiny run correctly failed the substrate gate because outcomes were
    single-class and role labels were all idle; this validates fail-closed
    behavior, not a real algorithm conclusion.

2026-07-02 partial real gate read:
  - User's requested checkpoint directory
    `logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k` did not
    exist locally / did not contain requested updates.
  - Ran the gate on the available local checkpoint grid:
    `logs\ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k`
    with updates 20, 40, 60.
  - Report:
      `logs\r12_substrate_gate_local_duration_short_16env\substrate_gate_report.json`
  - Rows: steps=418, roles=846, roles_available=846.
  - G-DWELL passed: median_dwell=9.0, transition_diag=0.9257,
    null_transition_diag=0.7074, margin=0.2182.
  - G-ROLE passed and label validity passed: role variance=0.9769,
    max_label_fraction=0.6040, n_unique_labels=3, MI=0.0281 vs threshold=0.0077.
  - G-OUTCOME failed: AUC=0.4841, compact_norm baseline AUC=0.5937,
    margin=-0.1096.  Target was valid but omega did not predict
    coverage-positive better than the simple baseline.
  - Overall gate_pass=false.

2026-07-02 compact-vector full real gate read:
  - Implemented and validated direct vector export/analyzer fallback before this
    read: `compact_dim`, `compact_json`, `omega_dim`, and `omega_json` are now
    exported; analyzer compares `omega` membership with deterministic
    `compact_cluster` membership side by side.
  - Ran a complete checkpoint grid on the available local run:
      `logs\ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k`
      with updates 20, 40, 60.
  - Report:
      `logs\r12_substrate_gate_local_duration_short_16env_compact_full\substrate_gate_report.json`
  - Row integrity: `substrate_steps.csv` has 600 rows:
      update 20 = 200, update 40 = 200, update 60 = 200.
  - Role-label guard passed: role rows=1224, available=1224,
    variance=0.9835, max_label_fraction=0.5899, n_unique_labels=4.
  - Omega branch passed all gates:
      G-DWELL median_dwell=8.0, transition_diag=0.9232,
        null_transition_diag=0.6795, margin=0.2437.
      G-OUTCOME AUC=0.6507 vs compact_norm baseline=0.5793,
        margin=0.0714; target coverage_positive_step valid
        with class counts 448/152.
      G-ROLE MI=0.0178 vs threshold=0.0077; stability=0.9232
        vs threshold=0.7795.
      gate_pass=true.
  - Compact-cluster branch also passed and is stronger on outcome:
      G-DWELL median_dwell=100.0, transition_diag=0.9933,
        null_transition_diag=0.7563, margin=0.2371.
      G-OUTCOME AUC=0.7085 vs compact_norm baseline=0.5793,
        margin=0.1293.
      G-ROLE MI=0.0140 vs threshold=0.0083; stability=0.9933
        vs threshold=0.8563.
  - Analyzer decision: `fallback_decision=omega_pass`.  The fallback path is
    implemented and informative, but not needed for this complete local read
    because omega itself passed.
```

Next decision:

```text
The local 16env duration-short checkpoint grid now satisfies the Stage-0
substrate gate, so the old "first export compact c and re-gate" blocker is
closed.  This is still not a final performance claim: before any long Round 12
paradigm run, keep the HMASD current-env gap re-verification requirement and
prefer repeating the same gate on a true 32env checkpoint grid if one becomes
available.  The next implementation discussion can move to reward-pure
situation-change hazard / situation-response Stage 1 design, with no SEF/DADS
reward injection until that stage is explicitly planned.
```

### EXP-20260702-p4-1b-grad-probe

Experiment name: `p4_1b_g_info_grad_probe`

Created at: 2026-07-02

Planned location: local (SB3 conda env, CUDA)

Command/script:

```powershell
# Dry-run first to print commands.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_p4_1b_grad_probe_local.ps1 `
  -DryRun

# Full probe: smoke + grad_diag + grad_obj_strong (default 32k / 16 env each).
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_p4_1b_grad_probe_local.ps1
```

Code snapshot / changed files:

```text
- ha_ctse_process/g_info_objective.py   (unit-weighted MI probe tensor,
  g_info_objective_raw, extended G_INFO_METRIC_FIELDS)
- ha_ctse_process/standalone_agent.py   (P4-1b gradient probe before backward:
  autograd.grad of unit-weighted MI on bridge/high/compact groups + PPO
  policy-loss reference norms; g_info_loss_ratio)
- ha_ctse_process/config.py             (use_g_info_grad_diagnostic=True)
- ha_ctse_process/train.py              (--disable_g_info_grad_diagnostic,
  manifest, GInfo/* TB scalars, console fields)
- ha_ctse_process/plotting.py           (CSV auto via G_INFO_METRIC_FIELDS,
  grad/loss ratio plot lines)
- scripts/run_p4_1b_grad_probe_local.ps1
```

Purpose:

```text
P4-1b / G2 hardening step 1: measure the g-info objective scale and gradient
path before any stronger/normalized coefficient sweep.  The Stage-A negative
(EXP-20260701-g-info-objective-probe) logged g_info_loss ~ -1e-5 vs PPO terms
O(0.1-1); this probe determines whether that failure is scale, path, or
objective form.
```

Hypothesis:

```text
The gradient path exists (compact -> bridge.code_embedding -> high.logits), so
g_info_grad_norm_bridge and _high should be nonzero, while
g_info_grad_ratio_* and g_info_loss_ratio should be far below 1e-2,
confirming a scale failure rather than a broken path.
```

Read fields:

```text
g_info_objective_raw, g_info_loss_ratio
g_info_grad_norm_bridge / _high / _compact
g_info_ppo_grad_norm_bridge / _high
g_info_grad_ratio_bridge / _high
```

OPT-specific caveat added 2026-07-02:

```text
This P4-1b probe answers scale/path/objective-form only.  It does NOT yet answer
whether g is a controllable prototype-response code over OPT interaction
prototypes, because the current update path discards omega_tau (`_weights`) and
GInfoObjective only receives compact c_tau.

After this short probe, the next code step should expose/log omega_tau and add
OPT shortcut baselines before any P4 team discriminator or team-conditioned P3
reward is trusted:
  q_opt(z | c, omega)
  q_opt_g_prior(z | c, omega, g)
  q_opt(g | c, omega)
```

Pre-committed decision rule:

```text
1. grad ratios << 1e-2 with nonzero grad norms
   -> scale failure confirmed: run one normalized/stronger sweep targeting
      g-info/PPO gradient ratio ~1e-2..1e-1 (with skill/duration-collapse
      watch), not a blind coefficient ladder.
2. g_info_grad_norm_bridge ~= 0
   -> path failure: the MI probe does not reach bridge parameters; fix wiring
      before any sweep.
3. grad_obj_strong shows ratio ~1e-1 at 32k AND a follow-up 320k strong run
   still shows no MI/TV movement above the diagnostic band
   -> objective-form failure: stop coefficient work, escalate to the
      team/joint discriminator intrinsic reward path (G2 option (a)).
4. regardless of the scale/path result, do not claim a real prototype-response
   g until omega_tau is exposed and OPT shortcut baselines are added.
```

Status: CODE REVERTED 2026-07-02 (user decision: the CC/Cowork agent's role is
cross-validation/advice only, not implementation).  All P4-1b diagnostic code
listed above was removed from `g_info_objective.py`, `standalone_agent.py`,
`config.py`, `train.py`, and `plotting.py`, and
`scripts/run_p4_1b_grad_probe_local.ps1` was deleted; the code files are back
to their pre-P4-1b state.  This entry is retained as the experiment DESIGN
(metrics, arms, and the pre-committed decision rule remain valid) plus the
OPT-specific caveat above, for Codex to reimplement if the P4-1b probe is still
wanted.  The scale-audit finding stands independently of the revert: with
coef=0.01 and MI ~5e-4, g_info_loss ~ 1e-5 vs PPO terms O(0.1-1).

### EXP-20260701-g-info-objective-probe

Experiment name: `round10_g_info_objective_probe`

Created at: 2026-07-01

Planned location: local first, cloud after wiring smoke

Command/script:

```powershell
# Preferred local CUDA script.  Use -DryRun to print commands without training.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_g_info_objective_local_cuda.ps1 `
  -DryRun

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_g_info_objective_local_cuda.ps1

# Optional progress monitor.  Registers a Windows scheduled task that checks
# this experiment every 8 hours and writes summaries under the log root.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\register_g_info_monitor_task.ps1 `
  -IntervalHours 8 `
  -RunNow

# Manual one-shot monitor check.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\check_g_info_progress.ps1

# Diagnostic-only first read.
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 16 `
  --rollout_length 500 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7,13,24 `
  --total_timesteps 320000 `
  --eval_interval 160000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --checkpoint_keep_last 4 `
  --plot_interval 10 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cpu `
  --log_dir logs\ha_ctse_process_s7s1_g_info_diag_16env_seed1_320k `
  --disable_process_posterior_mi `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe

# Small default-off objective activation after diagnostic smoke passes.
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 16 `
  --rollout_length 500 `
  --skill_interval 10 `
  --skill_lifetime_candidates 3,7,13,24 `
  --total_timesteps 320000 `
  --eval_interval 160000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --checkpoint_keep_last 4 `
  --plot_interval 10 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cpu `
  --log_dir logs\ha_ctse_process_s7s1_g_info_obj_16env_seed1_320k `
  --disable_process_posterior_mi `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe `
  --enable_g_info_objective `
  --g_info_coef_skill 0.01 `
  --g_info_coef_duration 0.01 `
  --g_info_warmup_steps 80000
```

Code snapshot / changed files:

```text
- ha_ctse_process/g_info_objective.py
- ha_ctse_process/standalone_agent.py
- ha_ctse_process/config.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- scripts/run_g_info_objective_local_cuda.ps1
- scripts/check_g_info_progress.ps1
- scripts/register_g_info_monitor_task.ps1
```

Purpose:

```text
Round 10 / G2 live-g probe.  Test whether g can be made non-decorative at the
high-level decision layer without communication-specific reward and without
feeding g/c into the low-level actor.
```

Hypothesis:

```text
Diagnostic-only run measures the historical decorative band.  With the small
decision-level objective, g_info_skill_mi, g_info_duration_mi, g_itv_tv_skill,
g_itv_tv_duration, and g_joint_assignment_distance should move above the
diagnostic-only band without immediate lifetime collapse or reward degradation.
```

Controls / comparison:

```text
Control: same reward-pure run with diagnostic-only g_info.
Treatment: same config plus `--enable_g_info_objective --g_info_coef_skill 0.01
--g_info_coef_duration 0.01`.
Do not compare against topology-potential or forcing-reward runs for this gate.
```

Metrics to read:

```text
g_info_active, g_info_objective_active, g_info_loss
g_info_skill_mi, g_info_duration_mi, g_info_total_mi
g_itv_tv_skill, g_itv_tv_duration, g_joint_assignment_distance
team_code_usage_entropy, team_code_usage_max_frac
team_code_skill_mi, team_code_duration_mi, team_code_edit_mi
duration_usage_entropy, duration_usage_max_frac, segment_length_mean
eval coverage_eq1_step_fraction, reward_mean, zero_throughput_step_fraction
```

Meaning of possible outcomes:

```text
Objective raises g decision MI/TV but task metrics do not move:
  g is no longer dead, but cooperation still needs P4 team/joint discriminator
  or co-edit complementarity.

Objective does not raise g decision MI/TV:
  high-level architecture is not using g even with explicit pressure; inspect
  bridge/code embeddings and high policy conditioning before building P4.

Objective raises g metrics by collapsing to one duration/skill:
  reject coefficient or add anti-collapse/annealing; do not count as g revival.
```

Stop / continue rule:

```text
Stop at 320k for first read.  Continue only if g decision metrics move above
diagnostic-only band and task/lifetime metrics do not visibly collapse.
```

Result status: completed

Result summary:

```text
Code smoke passed on 2026-07-01.

2026-07-01 8h monitor:
  Windows scheduled task created:
    TaskName = HA-CTSE GInfo Progress Check
    Repeat = every 8 hours
    LastTaskResult = 0
    NextRunTime = 2026/7/1 23:08:00 at creation-time query
  Monitor outputs:
    logs\ha_ctse_process_g_info_local_cuda\_monitor\g_info_progress_latest.txt
    logs\ha_ctse_process_g_info_local_cuda\_monitor\g_info_progress_*.txt

2026-07-01 manual monitor check:
  control run:
    run = ha_ctse_process_s7s1_g_info_diag_16env_seed1_320k
    status = complete to 320000 steps / update 40
    g_info_objective_active = 0
    last g_info_skill_mi = 0.0008
    last g_info_duration_mi = 0.0012
    last g_itv_tv_skill = 0.0326
    last g_itv_tv_duration = 0.0347
    latest_eval coverage_eq1_step_frac = 0.000000
    latest_eval zero_throughput_ep_frac = 0.750000
  objective run:
    run = ha_ctse_process_s7s1_g_info_obj_skill_duration_16env_seed1_320k
    status = running at 272000 steps / update 34
    g_info_objective_active = 1
    last g_info_skill_mi = 0.0004
    last g_info_duration_mi = 0.0004
    last g_itv_tv_skill = 0.0240
    last g_itv_tv_duration = 0.0212
    latest_eval at 160000 coverage_eq1_step_frac = 0.000000
    latest_eval zero_throughput_ep_frac = 0.750000

Initial read caution:
  The small objective has not yet improved g decision MI/TV relative to the
  diagnostic-only band.  Do not decide the gate until the objective arm reaches
  its 320k readout, but watch for a negative result.

2026-07-02 final read:
  Both arms completed normally and wrote `standalone_process_core_final.pt`.

  Diagnostic-only control:
    run = logs\ha_ctse_process_g_info_local_cuda\ha_ctse_process_s7s1_g_info_diag_16env_seed1_320k
    total_steps = 320000, update = 40
    last g_info_skill_mi = 0.000849
    tail5 g_info_skill_mi = 0.000838
    last g_info_duration_mi = 0.001216
    tail5 g_info_duration_mi = 0.001156
    last g_info_total_mi = 0.002065
    last g_itv_tv_skill = 0.032638
    tail5 g_itv_tv_skill = 0.032374
    last g_itv_tv_duration = 0.034676
    tail5 g_itv_tv_duration = 0.033630
    last g_joint_assignment_distance = 0.033657
    last skill_usage_entropy = 0.993064
    last duration_usage_entropy = 0.954454
    320k eval: reward_mean = 25.844740, coverage = 0.096667,
      throughput = 3.077298, coverage_eq1_step_frac = 0.000000,
      zero_throughput_ep_frac = 0.750000.

  Small objective treatment:
    run = logs\ha_ctse_process_g_info_local_cuda\ha_ctse_process_s7s1_g_info_obj_skill_duration_16env_seed1_320k
    total_steps = 320000, update = 40
    objective = --enable_g_info_objective --g_info_coef_skill 0.01
      --g_info_coef_duration 0.01 --g_info_warmup_steps 80000
    last g_info_loss = about -0.000010
    last g_info_skill_mi = 0.000458
    tail5 g_info_skill_mi = 0.000451
    last g_info_duration_mi = 0.000545
    tail5 g_info_duration_mi = 0.000508
    last g_info_total_mi = 0.001003
    last g_itv_tv_skill = 0.024752
    tail5 g_itv_tv_skill = 0.024552
    last g_itv_tv_duration = 0.023897
    tail5 g_itv_tv_duration = 0.023034
    last g_joint_assignment_distance = 0.024325
    last skill_usage_entropy = 0.997341
    last duration_usage_entropy = 0.990290
    320k eval: reward_mean = 22.682098, coverage = 0.095000,
      throughput = 6.338254, coverage_eq1_step_frac = 0.000000,
      zero_throughput_ep_frac = 0.700000.

  Gate decision:
    Failed for the current small-coefficient G2 objective.  The objective arm did
    not move g decision MI/TV above the diagnostic-only band; it reduced the core
    diagnostic values instead:
      skill MI 0.000458 vs 0.000849,
      duration MI 0.000545 vs 0.001216,
      skill TV 0.024752 vs 0.032638,
      duration TV 0.023897 vs 0.034676.

  Interpretation:
    This does not prove that g is impossible to revive.  Code inspection shows
    high_opt includes compact + bridge + high, so the gradient path is not
    obviously missing.  The observed objective scale is the immediate problem:
    with MI around 5e-4 and coefficients 0.01/0.01, g_info_loss is only about
    1e-5, far below the PPO high-level loss scale.  The experiment therefore
    falsifies the weak Stage-A objective as a live-g reviver, not the whole
    cooperative-g idea.
```

Next decision:

```text
Do not proceed directly to team/joint discriminator or co-edit complementarity
from this read.  Next step is P4-1b / G2 hardening:
  1. add g-info objective scale/gradient diagnostics
     (raw objective magnitude, loss/high-loss ratio, bridge/high gradient norms);
  2. verify the differentiable loss actually changes bridge/high parameters in a
     short controlled probe;
  3. then run a small coefficient/normalization sweep, or redesign the objective
     as a stronger team-code usage pressure.

Keep P3-4 forcing ablations separate; this G2 result says team-conditioned
forcing is still conditioning on a mostly-dead g variable.
```

### EXP-20260630-local-kmatrix-quick

Experiment name: `local_s7s1_overnight_kmatrix_4env`

Created at: 2026-06-30

Planned location: local

Command/script:

```powershell
& .\scripts\run_s7s1_local_overnight.ps1
```

Code snapshot / changed files:

```text
Uses current local workspace.  Important recent files:
- ha_ctse_process/standalone_agent.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- scripts/run_s7s1_local_overnight.ps1
- scripts/run_s7s1_local_quick.ps1
- scripts/summarize_ha_ctse_runs.py
```

Purpose:

```text
Fast local sanity check for fixed/shared vs variable lifetime behavior under
reward-pure settings.  This is not the final decoupled-lifetime claim.
```

Hypothesis:

```text
The run should expose whether obvious fixed/shared controls dominate and whether
variable-lifetime runs create desynchronization or nontrivial lifetime usage.
```

Controls / comparison:

```text
k_full_sync candidates=(1,)
k_fixed_d7 candidates=(7,)
k_decoupled_short candidates=(1,2,3)
k_decoupled_mixed candidates=(1,2,4,8)
p2_precheck reward-off diagnostics
p1_low_pos_probe weak shaping probe
```

Metrics to read:

```text
eval_reward, coverage, qos, throughput
credit_full_disconnect_mean, credit_recovery_rate
credit_backhaul_connected_step_fraction
credit_throughput_when_backhaul_connected_mbps
lifetime_heterogeneity, renewal_full_sync_rate
renewal_pairwise_corr_mean, duration_agent_mi
duration_return_range, duration_recovery_range
```

Meaning of possible outcomes:

```text
fixed/shared > variable:
  current variable-lifetime optimization/intrinsic loop is weak; do not claim
  variable lifetime is useless.

variable ~= fixed/shared:
  sanity pass, but no mechanism proof.

variable > fixed/shared with nontrivial lifetime metrics:
  useful signal that asynchronous lifetime may help; still needs cloud-scale
  confirmation.
```

Stop / continue rule:

```text
Let local suite finish unless it crashes.  Use it only for early diagnosis and
script/logging validation.
```

Result status: completed

Result summary:

```text
As of last check: k_full_sync and k_fixed_d7 completed locally; decoupled_short
started.  Full interpretation pending suite completion.
```

Next decision:

```text
After completion, compare with cloud 32env gates.  Do not use this local run as
final performance evidence.
```

### EXP-20260630-p3-stage-a-probe

Experiment name: `p3_conditional_skill_effect_reward_off_probe`

Created at: 2026-06-30

Planned location: local first, cloud after smoke

Command/script:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 16 `
  --rollout_length 500 `
  --skill_interval 10 `
  --skill_lifetime_candidates 1,2,3 `
  --total_timesteps 320000 `
  --eval_interval 160000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --checkpoint_keep_last 4 `
  --plot_interval 10 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cpu `
  --log_dir logs\ha_ctse_process_s7s1_p3_stage_a_reward_off_16env_seed1_320k `
  --disable_process_posterior_mi `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe `
  --enable_skill_effect_probe `
  --skill_effect_horizons 5,10,20 `
  --skill_effect_stride 5
```

Code snapshot / changed files:

```text
- ha_ctse_process/skill_effect_discovery.py
- ha_ctse_process/standalone_agent.py
- ha_ctse_process/config.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- ha_ctse_process/smoke.py
```

Purpose:

```text
Reward-off probe for Conditional Skill-Effect Discovery.  Test whether knowing
z_i improves prediction of short-horizon effects y_i(t,h) beyond context-only
baselines.
```

Hypothesis:

```text
If skill latents have real process-effect semantics, p_full(y|x,z) should beat
p_base(y|x) on micro-windows, and the gain should not be explained by duration,
reward, phase, or agent-id shortcuts.
```

Controls / comparison:

```text
Full predictor: p_full(y_i | x_i, z_i)
Baseline predictor: p_base(y_i | x_i)
Shortcut audits: duration/reward/phase/agent/context controls
No reward injection in this stage.
```

Metrics to read:

```text
effect_windows
effect_loss_full, effect_loss_base
effect_gain_mean, effect_gain_positive_frac
effect_gain_motion, effect_gain_service
effect_gain_energy, effect_gain_topology
effect_gain_minus_duration_baseline
effect_gain_minus_reward_baseline
effect_reward_low_mean = 0
effect_reward_applied_steps = 0
```

Meaning of possible outcomes:

```text
gain <= 0:
  no evidence that z controls short-horizon effects; fix effect target or model.

gain > 0 but shortcut-driven:
  do not inject reward; improve context/shortcut controls.

gain > 0 and not shortcut-driven:
  proceed to P3-4 low-only intrinsic.
```

Stop / continue rule:

```text
Do not enable P3 reward until reward-off probe passes.  Stage A must remain
diagnostic-only.
```

Result status: completed

Result summary:

```text
2026-06-30 code wiring smoke passed:
  py_compile: skill_effect_discovery/standalone_agent/train/config/plotting/smoke
  smoke path: logs/ha_ctse_process_smoke_p3_stage_a/smoke_result.json
  smoke effect_windows=3
  smoke effect_reward_low_mean=0
  smoke effect_reward_applied_steps=0
  dry-run CLI S7-S1: logs/ha_ctse_process_p3_stage_a_dryrun
  tiny train loop: logs/ha_ctse_process_p3_stage_a_tiny_train
  tiny train CSV last row: effect_windows=90, effect_reward_low_mean=0,
    effect_reward_applied_steps=0

2026-06-30 reward-off training probe completed:
  run path: logs/ha_ctse_process_s7s1_p3_stage_a_reward_off_16env_seed1_320k
  updates/steps: update=40, total_steps=320000
  reward guard: effect_reward_low_mean=0 and effect_reward_applied_steps=0 for
    all windows, so this was a clean reward-off probe.

P3 Stage A gate metrics:
  all updates:
    effect_gain_mean=-0.002188
    effect_gain_positive_frac=0.442
    effect_gain_motion=-0.007380
    effect_gain_service=-0.000045
    effect_gain_energy=-0.000236
    effect_gain_topology=-0.000137
    effect_gain_minus_duration_baseline=0.000229
    effect_gain_minus_reward_baseline=-0.001948
  last 10 updates:
    effect_gain_mean=-0.004261
    effect_gain_positive_frac=0.449
    effect_gain_motion=-0.014956
    effect_gain_service=0.000066
    effect_gain_energy=-0.000032
    effect_gain_topology=-0.000029
    effect_gain_minus_duration_baseline=0.001111
    effect_gain_minus_reward_baseline=-0.001657

Eval:
  160k: reward=35.07, coverage=0.213, qos=0.106, throughput=3.254,
    backhaul_connected_frac=0.339
  320k: reward=21.20, coverage=0.090, qos=0.063, throughput=2.169,
    backhaul_connected_frac=0.233

Interpretation:
  The current P3 Stage A probe fails the predeclared gate.  p_full(y|x,z)
  does not beat p_base(y|x); positive fraction stays below 0.55; the only
  positive shortcut gap is against duration, while the reward baseline still
  beats the full model.  Motion dominates the negative signal; service/topology
  gains are near zero.  This is not enough to justify intrinsic reward.
```

Next decision:

```text
Do not enable P3-4 low-only intrinsic reward.  Revise P3 Stage A before another
reward experiment: improve effect target/model/audit so the probe can test
skill-conditioned controllable effects without being dominated by generic
motion or reward shortcuts.
```

---

### EXP-20260630-p3-2b-reward-off-probe

Experiment name: `p3_2b_group_balanced_effect_probe`

Created at: 2026-06-30 17:55

Planned location: local first; cloud optional after local read

Command/script:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 16 `
  --rollout_length 500 `
  --skill_interval 10 `
  --skill_lifetime_candidates 1,2,3 `
  --total_timesteps 320000 `
  --eval_interval 160000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --checkpoint_keep_last 4 `
  --plot_interval 10 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cpu `
  --log_dir logs\ha_ctse_process_s7s1_p3_2b_reward_off_16env_seed1_320k `
  --disable_process_posterior_mi `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe `
  --enable_skill_effect_probe `
  --skill_effect_horizons 5,10,20 `
  --skill_effect_stride 5
```

Code snapshot / changed files:

```text
- ha_ctse_process/skill_effect_discovery.py
- ha_ctse_process/config.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- ha_ctse_process/smoke.py
```

Purpose:

```text
Reward-off P3-2b revision.  Re-test whether z_i gives conditional predictive
power for short-horizon effects after fixing the Stage-A probe's likely
measurement problems: motion-dominated loss, no per-horizon readout, and no
diagnostic for whether z changes actions/targets at all.
```

Changed variables:

```text
skill_effect_group_balanced_loss=True
new P3-2b metrics:
  effect_gain_group_balanced_mean
  effect_gain_nonmotion
  effect_gain_horizon_*
  effect_field_gain_*
  effect_action_skill_eta2
  effect_target_skill_eta2
  effect_skill_usage_entropy / max_frac
```

Fixed controls:

```text
No P3 reward injection.
Process posterior MI off.
Process reward off.
Transition discriminator off.
Topology-role probe off.
Same S7-S1, n_agents=6, duration candidates=(1,2,3), 16 envs, 320k budget.
```

Metrics to read:

```text
Primary gate:
  effect_gain_group_balanced_mean
  effect_gain_nonmotion
  effect_gain_positive_frac
  effect_gain_minus_duration_baseline
  effect_gain_minus_reward_baseline

Localization:
  effect_gain_horizon_0/1/2 and positive fractions
  effect_gain_motion/service/energy/topology
  effect_field_gain_*

Mechanism diagnostic:
  effect_action_skill_eta2
  effect_target_skill_eta2
  effect_gain_skill_std
  effect_skill_usage_entropy
  effect_skill_usage_max_frac

Safety:
  effect_reward_low_mean=0
  effect_reward_applied_steps=0
```

Stop / continue rule:

```text
Do not enable P3-4 unless the revised reward-off probe shows positive
non-shortcut gain: group-balanced/non-motion gain positive, positive fraction
around or above 0.55, and full model beating duration/reward baselines.  If
action~skill eta2 and target~skill eta2 are both near zero, diagnose z/low-level
usage before changing reward.
```

Result status: completed

Result summary:

```text
Code validation before launch:
  py_compile passed for skill_effect_discovery, standalone_agent, config, train,
    plotting, smoke.
  smoke passed at logs/ha_ctse_process_smoke_p3_2b.
  tiny train passed at logs/ha_ctse_process_p3_2b_tiny_train.
  Tiny train wrote new effect_* CSV fields and kept effect_reward_low_mean=0,
    effect_reward_applied_steps=0.

2026-06-30 partial read at 160k:
  run path: logs/ha_ctse_process_s7s1_p3_2b_reward_off_16env_seed1_320k
  status: running or not yet finalized; latest checkpoint update_20.pt, no
    final checkpoint observed.
  reward guard: effect_reward_low_mean=0 and effect_reward_applied_steps=0.

  P3-2b first 20 updates:
    effect_gain_mean=-0.000082
    effect_gain_group_balanced_mean=0.000092
    effect_gain_nonmotion=0.000390
    effect_gain_positive_frac=0.513
    effect_gain_minus_duration_baseline=-0.001292
    effect_gain_minus_reward_baseline=-0.001724
    effect_action_skill_eta2=0.012
    effect_target_skill_eta2=0.004

  P3-2b last 10 updates:
    effect_gain_mean=-0.000143
    effect_gain_group_balanced_mean=-0.000039
    effect_gain_nonmotion=0.000196
    effect_gain_positive_frac=0.488
    effect_gain_minus_duration_baseline=-0.001397
    effect_gain_minus_reward_baseline=-0.001994
    effect_action_skill_eta2=0.018
    effect_target_skill_eta2=0.006

  Matched 160k comparison to old Stage A:
    effect_gain_mean improved from roughly -0.00117 to -0.00008.
    positive fraction improved from roughly 0.437 to 0.513.
    motion penalty improved from roughly -0.00356 to -0.00080.
    non-motion fields now expose weak positive energy/topology signal.

  Interpretation:
    P3-2b made the diagnostic more informative and reduced motion domination,
    but it has not passed the gate.  The full model still loses to duration and
    reward baselines, positive fraction is below 0.55 in the last 10 updates,
    and action/target eta2 remain small.  Continue/read to 320k before final
    decision; do not enable P3-4.

2026-06-30 final read at 320k:
  run path: logs/ha_ctse_process_s7s1_p3_2b_reward_off_16env_seed1_320k
  status: completed; standalone_process_core_final.pt exists.
  reward guard: effect_reward_low_mean=0 and effect_reward_applied_steps=0
    throughout, so this remained a clean reward-off probe.

  P3-2b all 40 updates:
    effect_gain_mean=-0.000162
    effect_gain_group_balanced_mean=-0.000023
    effect_gain_nonmotion=0.000365
    effect_gain_positive_frac=0.478
    effect_gain_minus_duration_baseline=-0.000525
    effect_gain_minus_reward_baseline=-0.000496
    effect_action_skill_eta2=0.022
    effect_target_skill_eta2=0.0069
    credit_full_disconnect_mean=0.593
    credit_recovery_rate=0.0034

  P3-2b last 10 updates:
    effect_gain_mean=-0.000902
    effect_gain_group_balanced_mean=-0.000700
    effect_gain_nonmotion=0.000190
    effect_gain_positive_frac=0.429
    effect_gain_minus_duration_baseline=-0.000147
    effect_gain_minus_reward_baseline=-0.000033
    effect_action_skill_eta2=0.038
    effect_target_skill_eta2=0.011
    credit_full_disconnect_mean=0.610
    credit_recovery_rate=0.0014

  Eval:
    160k: reward_mean=18.82, reward_std=39.59, coverage=0.107,
      qos=0.071, throughput=4.43, backhaul_connected_frac=0.226
    320k: reward_mean=30.05, reward_std=51.64, coverage=0.115,
      qos=0.105, throughput=10.75, backhaul_connected_frac=0.278

  Matched 320k comparison to old Stage A:
    effect_gain_mean improved from -0.002188 to -0.000162.
    motion penalty improved from -0.007380 to -0.001186.
    energy/topology field gains became weakly positive.
    However, positive fraction only improved from 0.442 to 0.478 and remains
    below the 0.55 gate; duration/reward baseline gaps are still negative.

  Interpretation:
    P3-2b improved measurement but did not prove a usable skill-effect signal.
    The full model still fails the non-shortcut gate, and action/target eta2 are
    small.  There is weak non-motion structure, especially energy/topology, but
    it is not stable enough to become intrinsic reward.
```

Next decision:

```text
Do not enable P3-4.  The next step should be P3-2c: diagnose whether z_i is
actually being used by the low-level executor under controlled same-observation
skill interventions.  If z barely changes action distributions or expected
short-horizon effects under intervention, fix the z->low-level behavior coupling
before designing any reward.  If z does change actions but not effects, revise
effect targets/horizons and environment-effect extraction.
```

---

### EXP-20260630-p3-2c-intervention-probe

Experiment name: `p3_2c_skill_use_intervention_probe`

Created at: 2026-06-30 21:35

Planned location: local first; cloud optional after local read

Command/script:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 16 `
  --rollout_length 500 `
  --skill_interval 10 `
  --skill_lifetime_candidates 1,2,3 `
  --total_timesteps 320000 `
  --eval_interval 160000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --checkpoint_keep_last 4 `
  --plot_interval 10 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cpu `
  --log_dir logs\ha_ctse_process_s7s1_p3_2c_intervention_16env_seed1_320k `
  --disable_process_posterior_mi `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe `
  --enable_skill_effect_probe `
  --enable_skill_effect_intervention_probe `
  --skill_effect_horizons 5,10,20 `
  --skill_effect_stride 5 `
  --skill_effect_intervention_max_samples 512
```

Code snapshot / changed files:

```text
- ha_ctse_process/skill_effect_discovery.py
- ha_ctse_process/standalone_agent.py
- ha_ctse_process/config.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- ha_ctse_process/smoke.py
```

Purpose:

```text
Reward-off P3-2c audit.  Separate two failure modes left by P3-2b:
whether z_i is decorative for the low-level executor, or whether z_i changes
actions but the current effect target/model fails to capture consequences.
```

Hypothesis:

```text
If the current skill latents are being used by the low-level policy, then at
the same observation/team context forced z=0..n_z-1 should produce nontrivial
low-actor action-distribution distances.  If the effect model also contains
usable skill-conditioned signal, forced z should produce nontrivial predicted
effect-vector distances.
```

Controls / comparison:

```text
No P3 reward injection.
No process posterior MI.
No process reward.
No transition skill discriminator.
No topology-role probe.
Same S7-S1, n_agents=6, duration candidates=(1,2,3), 16 envs, 320k budget as
P3-2b.
```

Metrics to read:

```text
Primary P3-2c:
  effect_intervention_active
  effect_intervention_samples
  effect_intervention_action_l2_mean
  effect_intervention_action_l2_max
  effect_intervention_action_pairwise_std
  effect_intervention_pred_effect_l2_mean
  effect_intervention_pred_effect_l2_max
  effect_intervention_best_skill_gap
  effect_intervention_low_entropy_mean

Context:
  effect_gain_group_balanced_mean
  effect_gain_nonmotion
  effect_gain_positive_frac
  effect_gain_minus_duration_baseline
  effect_gain_minus_reward_baseline
  effect_action_skill_eta2
  effect_target_skill_eta2

Safety:
  effect_reward_low_mean=0
  effect_reward_applied_steps=0
```

Meaning of possible outcomes:

```text
action_l2 near zero and pred_effect_l2 near zero:
  z_i is effectively decorative; fix z->low-level coupling before reward.

action_l2 nonzero but pred_effect_l2 near zero:
  low actor uses z, but effect target/model/horizons are missing the relevant
  consequences; revise targets/extractor before reward.

action_l2 nonzero and pred_effect_l2 nonzero:
  return to P3-3 shortcut/usefulness audits; P3-4 reward remains blocked until
  non-shortcut gain also passes.
```

Stop / continue rule:

```text
Run to 320k unless the reward guard is violated or effect_intervention_active
stays 0 after the first few updates.  Do not enable P3-4 from this experiment
alone; it is a mechanism audit, not a reward gate.
```

Result status: completed

Result summary:

```text
Code validation before launch:
  py_compile passed for touched files.
  smoke passed at logs/ha_ctse_process_smoke_p3_2c.
  tiny train passed at logs/ha_ctse_process_p3_2c_tiny_train.

Partial read at 2026-06-30 22:25:
  update=26/40, total_steps=208000/320000.
  First eval at 160000:
    reward_mean=23.131215, reward_std=40.817744, coverage=0.116667,
    qos=0.069722, throughput=3.050000, backhaul_connected_frac=0.260500,
    throughput_when_backhaul_connected=7.891655.
  Probe health:
    effect_intervention_active=1, effect_intervention_samples=512 on recent
    updates, effect_reward_low_mean=0, effect_reward_applied_steps=0.
  Intervention signal:
    forced-z action_l2 is nonzero and rising
    (first-10 avg 0.054472, last-10 avg 0.146668, latest 0.175852).
    This means z_i is not completely ignored by the low actor.
  Effect-model signal:
    pred_effect_l2 is roughly flat/slightly down
    (first-10 avg 0.102230, last-10 avg 0.092234).
    group-balanced gain moved from 0.000324 to -0.000276, positive_frac is
    near 0.49, and duration/reward baseline gaps are negative in the last-10
    average.
  Cooperation context:
    last-10 credit_full_disconnect_mean=0.562039,
    credit_recovery_rate=0.002304.  This run is diagnostic and is not expected
    to solve cooperation by itself.

Progress read at 2026-06-30 23:12:
  Training updates reached update=40/40, total_steps=320000/320000.
  Final 320k eval is still in progress: eval_episodes.csv has 320k episodes
  10/20 written at the time of reading, so do not use the partial 320k eval as
  final performance evidence yet.
  Training-side all-update averages:
    effect_intervention_action_l2_mean=0.135512,
    effect_intervention_pred_effect_l2_mean=0.098471,
    effect_gain_group_balanced_mean=-0.000316,
    effect_gain_positive_frac=0.501907,
    effect_gain_minus_duration_baseline=-0.001415,
    effect_gain_minus_reward_baseline=-0.001425,
    effect_reward_low_mean=0,
    effect_reward_applied_steps=0,
    credit_full_disconnect_mean=0.595795,
    credit_recovery_rate=0.003587.
  Training-side last-10 averages:
    effect_intervention_action_l2_mean=0.199302,
    effect_intervention_pred_effect_l2_mean=0.106000,
    effect_gain_group_balanced_mean=-0.000907,
    effect_gain_positive_frac=0.525757,
    effect_gain_minus_duration_baseline=-0.002242,
    effect_gain_minus_reward_baseline=-0.002629,
    credit_full_disconnect_mean=0.589397,
    credit_recovery_rate=0.002972.
  Interpretation:
    P3-2c confirms z_i has a measurable low-actor action effect, and that
    effect strengthens through training.  However, the conditional effect
    predictor still fails the non-shortcut gate: group-balanced gain is negative
    by the end, duration/reward baseline gaps are negative, and cooperation
    recovery remains near zero.  This favors revising effect targets/extractor
    instead of repairing z->low-level coupling or injecting intrinsic reward.

Final read at 2026-06-30 23:18:
  Eval completed: 160k and 320k both have 20 episodes.
  160k eval:
    reward_mean=23.131215, reward_std=40.817744, coverage=0.116667,
    qos=0.069722, throughput=3.050000, backhaul_connected_frac=0.260500,
    throughput_when_backhaul_connected=7.891655.
  320k eval:
    reward_mean=29.122841, reward_std=44.965725, coverage=0.136667,
    qos=0.075913, throughput=5.550714, backhaul_connected_frac=0.315900,
    throughput_when_backhaul_connected=9.986215.
  Episode structure from eval_episodes.csv:
    coverage_gt0_frac=0.35 at both 160k and 320k;
    throughput_gt5_frac=0.35 at both 160k and 320k;
    zero_throughput_frac=0.65 at both 160k and 320k;
    full_disconnect_episode_frac=0.40 at both 160k and 320k.
  Artifacts:
    standalone_process_core_update_20.pt and update_40.pt saved.
    No SB3 python process remains running.
  Final interpretation:
    The intervention audit succeeded as a mechanism diagnostic and rules out
    the simplest "z is ignored by the low actor" failure mode.  It does not
    pass the P3 reward gate: effect gains are weak/negative relative to context,
    duration, and reward baselines, and task behavior remains bimodal with many
    zero-throughput episodes.  P3-4 remains blocked.
```

Next decision:

```text
Next code work should revise effect targets/extractor/horizons and observed
effect audits.  Do not spend the next step on z->low-level coupling repair, and
do not enable P3-4 low-only intrinsic until a reward-off probe shows stable
non-shortcut positive effect gain.
```

---

### EXP-20260630-p3-2d-observed-effect-probe

Experiment name: `p3_2d_observed_effect_reward_off_probe`

Created at: 2026-06-30 23:50

Planned location: local first; cloud optional only after local read

Command/script:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --collector_backend subproc `
  --collector_start_method spawn `
  --num_envs 16 `
  --rollout_length 500 `
  --skill_interval 10 `
  --skill_lifetime_candidates 1,2,3 `
  --total_timesteps 320000 `
  --eval_interval 160000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --checkpoint_keep_last 4 `
  --plot_interval 10 `
  --low_clip_epsilon 0.1 `
  --smdp_bootstrap_coef 0.25 `
  --device cpu `
  --log_dir logs\ha_ctse_process_s7s1_p3_2d_observed_effect_16env_seed1_320k `
  --disable_process_posterior_mi `
  --disable_process_reward `
  --disable_transition_skill_discriminator `
  --disable_topology_role_probe `
  --enable_skill_effect_probe `
  --enable_skill_effect_intervention_probe `
  --skill_effect_horizons 3,5,10,20 `
  --skill_effect_stride 3 `
  --skill_effect_max_windows 8192 `
  --skill_effect_intervention_max_samples 512
```

Code snapshot / changed files:

```text
- ha_ctse_process/skill_effect_discovery.py
- ha_ctse_process/config.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- ha_ctse_process/smoke.py
- memory/ALGORITHM_PRINCIPLES.md
- memory/IMPLEMENTATION_PLAN.md
```

Purpose:

```text
Reward-off probe for P3-2d.  Test whether adding end-state and window-mean
effect targets lets the conditional predictor capture useful observed effects
after P3-2c proved that z_i already changes low-level actions.
```

Hypothesis:

```text
The previous delta-only target was too narrow/noisy.  Revised observed targets
should increase target availability and expose skill-conditioned effect
structure not explained by duration/reward shortcuts.
```

Controls / comparison:

```text
Compare primarily against:
  EXP-20260630-p3-2c-intervention-probe
  EXP-20260630-p3-2b-reward-off-probe

Still reward-off:
  no P3 reward injection
  no process posterior MI
  no process reward
  no transition skill discriminator
  no topology-role probe
```

Metrics to read:

```text
Gate metrics:
  effect_gain_group_balanced_mean
  effect_gain_nonmotion
  effect_gain_positive_frac
  effect_gain_minus_duration_baseline
  effect_gain_minus_reward_baseline
  effect_observed_target_skill_l2_mean
  effect_observed_target_skill_l2_nonmotion
  effect_observed_action_skill_l2_mean
  effect_observed_action_target_corr
  effect_endstate_available_frac
  effect_window_mean_available_frac

Safety:
  effect_reward_low_mean=0
  effect_reward_applied_steps=0

Context:
  coverage, throughput, zero-throughput fraction, credit_full_disconnect_mean,
  credit_recovery_rate.  These are diagnostic only for this probe.
```

Meaning of possible outcomes:

```text
Observed target availability remains low:
  extractor is still missing environment fields; inspect state_info/reward_info
  schemas before another model change.

Observed target skill L2 rises but predictive gains remain <= 0 or shortcut gaps
stay negative:
  z produces distinguishable observed states, but the predictor/baseline design
  still cannot isolate causal skill effect; revise context controls or target
  normalization.

Predictive gains become positive and beat duration/reward baselines:
  proceed to P3-3 usefulness/shortcut audit, still reward-off.

Task metrics improve:
  useful but not the gate; do not confuse task performance with approval for
  P3-4.
```

Stop / continue rule:

```text
Run to 320k unless reward guards become nonzero, effect_windows stays zero, or
the process crashes.  Do not enable P3-4 from this run alone.
```

Result status: partially completed and read on 2026-07-01

Result summary:

```text
Code validation before launch:
  in-memory compile passed for touched files.
  smoke passed at logs/ha_ctse_process_smoke_p3_2d.
  tiny train passed at logs/ha_ctse_process_p3_2d_tiny_train.
```

Next decision:

```text
After the run, decide whether to move to P3-3 usefulness/shortcut audit or
revise extractor/context controls again.  P3-4 remains blocked.
```

---

### EXP-20260701-p3-2d-overnight-suite

Experiment name: `p3_2d_overnight_reward_off_suite`

Created at: 2026-07-01

Planned location: local overnight, PowerShell one-key runner

Command/script:

```powershell
& .\scripts\run_p3_2d_overnight.ps1
```

Dry run:

```powershell
& .\scripts\run_p3_2d_overnight.ps1 -DryRun
```

Code snapshot / changed files:

```text
- scripts/run_p3_2d_overnight.ps1
- ha_ctse_process/skill_effect_discovery.py
- ha_ctse_process/config.py
- ha_ctse_process/train.py
- ha_ctse_process/plotting.py
- ha_ctse_process/smoke.py
```

Purpose:

```text
Fill an 8-10 hour local overnight window with P3-2d reward-off diagnostics.
Do not test P3-4 reward yet.  The suite asks which target/horizon/lifetime
condition best exposes non-shortcut observed skill effects after P3-2c proved
z_i affects low-level actions.
```

Runs:

```text
1. p3_2d_main
   candidates=(1,2,3), horizons=(3,5,10,20), stride=3
   Primary P3-2d probe.

2. p3_2d_dense_short
   candidates=(1,2,3), horizons=(1,3,5,10), stride=1
   Tests whether useful effect signal is very short-horizon and diluted by
   coarser micro-windows.

3. p3_2d_mixed_lifetime
   candidates=(1,2,4,8), horizons=(3,5,10,20), stride=3
   Tests whether richer lifetime diversity creates more observable skill-effect
   separation.

4. p3_2d_no_group_balance
   candidates=(1,2,3), horizons=(3,5,10,20), stride=3,
   --disable_skill_effect_group_balanced_loss
   Tests whether group-balanced loss is suppressing raw predictive signal.
```

Fixed controls:

```text
S7-S1, n_agents=6, seed=1, num_envs=16, rollout_length=500,
total_timesteps=320000 per run, eval_interval=160000, eval_episodes=20,
low_clip_epsilon=0.1, smdp_bootstrap_coef=0.25, device=cpu.

Reward and semantic components remain OFF:
  no P3 reward injection
  no process posterior MI
  no process reward
  no transition skill discriminator
  no topology-role probe
```

Metrics to read:

```text
Primary P3-2d gate:
  effect_gain_group_balanced_mean
  effect_gain_nonmotion
  effect_gain_positive_frac
  effect_gain_minus_duration_baseline
  effect_gain_minus_reward_baseline
  effect_observed_target_skill_l2_mean
  effect_observed_target_skill_l2_nonmotion
  effect_observed_action_skill_l2_mean
  effect_observed_action_target_corr
  effect_endstate_available_frac
  effect_window_mean_available_frac

Safety:
  effect_reward_