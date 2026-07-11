# HA-CTSE Experiment Dashboard

Updated: 2026-07-11

Purpose: factual current experiment state. ExpManager records experiment
content, running state, commands, package paths, and result facts here.
LongTimeMemoryManager decides how these facts affect current memory and LTM
archives.

## Protocol

Before launching or recommending an experiment, keep one dashboard row here and
record enough factual detail for LongTimeMemoryManager to decide any archive or
project-memory update.

Required dashboard columns:

```text
ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision
```

Status vocabulary:
`planned`, `launch-ready`, `running`, `completed`, `stopped`, `failed`,
`invalid`, `superseded`, `blocked`, `standing-reference`.

**Standing-reference rule (user directive, 2026-07-10):** rows marked
`standing-reference` are fixed comparison data — the HMASD baseline curve
(REF-20260617) and the completed HA-CTSE baseline/control arms (R25 arm0/arm2
archives). Future experiment designs MUST reuse these archived curves and
checkpoints instead of re-running them; do not include an HMASD arm or a
repeat baseline arm in new runner scripts. A new control arm is justified only
when a config change makes the archived control incomparable (e.g., env-count
or scenario change), and that exception needs explicit user approval in the
experiment brief.

## Current Dashboard

| ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-20260711-r26-g1a-individual-skill-screening | launch-ready | R26-G1a reward-off screening | local CUDA (RTX 4070 Laptop 8 GB), six frozen R25 checkpoints | ExpManager | per-checkpoint gate plus arm0 2-of-3 family gate | `scripts/run_r26_g1_screening_local_cuda.ps1`; proposed run root `logs/r26_g1a_screening/` | No reward; a pass authorizes only separate G1b design. Launch is not authorized or executed. |
| EXP-20260710-r25-qa-verification-1m | completed / read + dispositioned 2026-07-10; arm0/arm2 archives now standing-reference (DO NOT RE-RUN — user directive 2026-07-10) | R25 verification tier | cloud CUDA / 64env / 1M steps / two arms (arm0 control, arm2 q_A) | ExpManager + ResultAnalyst + marl-peer-reviewer | all variants read; cross-seed single-seed gate analysis complete | `dist/logs_cloud_r25_qa_verification_1m/` (cloud archive); `gate_read_r25_seed1.md` (result analyst read); peer review Round 6 archived in `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` | arm0 arch-only beats arm2 q_A at 640k-960k (coverage 0.235→0.417 vs 0.052→0.113; throughput 13.76 vs 2.81 Mbps @960k); neither reaches HMASD milestones (0.7@480k, 0.9@800k); q_A reward demoted to default-off by Round 6 peer review (NOT VERIFIED at 1M verification gate under n=1 single-seed setup); parity OPEN (update-count confound: 32 updates vs HMASD ~2×/step). |
| EXP-20260709-r24-frozen-qd-null-probes | completed — 4/4 analyzed (3 CPU, qAoff/seed2 on GPU per user directive); external peer review Round 5 completed; disposition ACCEPTED 2026-07-09 | R24 frozen q_d null probes | cloud archive `dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/` + local analysis complete | ExpManager + ResultAnalyst + marl-peer-reviewer | all variants read; cross-seed synthesis complete | Archive complete; peer review Round 5 text archived in `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` | R24-1 FAIL accepted 2026-07-09 (Round 5, SUPPORTS_WITH_CONDITIONS). Wording condition: "fail under tested policies and current diagnostic setup" (3 of 4 collapsed). D2 sensitivity re-run approved-deferred with conditions. D3 pivot direction accepted pending deconfound. q_d/q_D rewards remain BLOCKED. |
| REF-20260617-hmasd-baseline-s7s1-seed1 | standing-reference (completed; stopped at 66% budget, clean; DO NOT RE-RUN — user directive 2026-07-10) | HMASD baseline reference curve | local, 32env, rollout 500, metrics-light; `C:\project\tf-logs\hmasd\energy-S7-S1\...\20260617_133148` | ResultAnalyst (read 2026-07-09) | none — reference | `logs/hmasd_baseline_read_20260709/metric_extract.md` | HMASD S7-S1 pace/ceiling reference (seed1): eval coverage >=0.5 and >=0.7 first at 480k, >=0.9 at 800k; plateau ~0.95-0.99 from ~800-960k; final-window (1.76M-2.08M) coverage mean 0.9639, reward mean 380.29; zero-coverage eval episodes gone from 640k. Run stopped externally at 2,112,000/3,200,000 steps, no crash. Caveats: 32env (vs 64env HA-CTSE cloud runs), predates parity metrics (no coverage_eq1 fields), single seed. |
| EXP-20260708-r24-qd-null-control-cloud-handoff | completed | R24 | cloud CUDA / 64env package | ExpManager + controller | ResultAnalyst to read metrics from the completed cloud archive before any q_d/q_D reward decision | `dist/ha_ctse_r24_qd_null_control_cloud_runtime_20260708_190315.zip`; `dist/r24_qd_null_control_log_extract_expmanager_20260708_230322`; `scripts/run_r24_qd_null_control_cloud_64env.sh`; default log root `logs_cloud_r24_qd_null_control_64env` | Cloud archive inspected. Both seeds finished with `exit_code=0` and `total_steps=320000`. Seed1 final eval row: `reward=52.852671269315316`, `coverage_ratio=0.8`, `system_throughput_mbps=8.611111111111114`, `backhaul_connected_step_fraction=0.51`, `zero_throughput_step_fraction=0.49`. Seed2 final eval row: `reward=-4.881497951854478`, `coverage_ratio=0.0`, `system_throughput_mbps=0.0`, `backhaul_connected_step_fraction=0.0`, `zero_throughput_step_fraction=1.0`. No `Traceback`, `RuntimeError`, `NaN`, `OOM`, or `BrokenPipe` matches were found in the runner logs. |
| EXP-20260707-r24-assignment-to-behavior-bridge | completed / blocked | R24 | local CUDA diagnostics | ExpManager | run matched-null forced-audit controls A-D, then reward-off behavior-window q_d probe; set `q_D/q_d` reward decision only after gate pass | `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/r24_forced_behavior_audit.py`; `logs_r24_qd_probe_local_cuda/seed1`; `logs_r24_behavior_audit_local/r24_behavior_audit.csv`; `logs_r24_behavior_audit_smoke/r24_behavior_audit.csv` | forced-audit signal is positive but insufficient for reward gating. q_d probe is near-null (`residual_gain=0.01105`, `positive_frac=0.52855`) and cannot justify reward-on. `q_D` and `q_d` rewards remain blocked pending matched-null controls + behavior-window `q_d` gate pass (`effect_ratio_h50>=1.3` + `h50-h10` growth + `between_within_ratio_h50>1.2`). |
| EXP-20260707-r24-assignment-to-behavior-bridge-overnight | completed | R24 | local CUDA / `logs_r24_overnight_existing_local_cuda/run_20260708_000836` | ExpManager | checked arm-level `runner_status.txt`, `runner_output.log`, audit/train tails, and `_watch/watch_state.json` | `scripts/run_r24_overnight_existing_local_cuda.ps1`; `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/run_r24_qd_probe_local_cuda.ps1`; `scripts/watch_r24_overnight_existing.ps1`; `scripts/codex_r24_alert_handler.ps1`; `logs_r24_overnight_existing_local_cuda/run_20260708_000836/arm*` | one-click local overnight runner completed with `NResets=64`, `NumEnvs=16`; all five arms finished with `exit_code=0`. |
| EXP-20260707-r23-next-mechanism-matrix | completed / mixed (local 16env, single seed) | R23-next | local CUDA; cloud candidate | ExpManager | optional cloud 64env rerun for a matched-env task read + q_D-probe upgrade | `logs_r23_next_mechanism_matrix_local`, `scripts/run_r23_next_mechanism_matrix_local_cuda.ps1`, `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh` | q_A actionability VALIDATED (Z->xi learnable: arm2 residual_gain +0.222, forced-Z KL 0.059->0.070). q_D target audit NULL across all targets/H (underpowered caveat) -> xi->recoverable-joint-effect still unestablished. Task encouraging @160k (cov 0.303 ~3x control) but confounded. Next lever = individual-skill/discoverer half + stronger q_D probe, NOT more q_D targets. Local 32env OOMs (31.6GB box); use 16env locally or 64env cloud. |
| EXP-20260706-r23-actionable-team-intent | completed / mixed | R23 | cloud CUDA seed1 | ExpManager | none unless comparing to R23-next | `dist/logs_cloud_r23_actionable_team_intent_64env` | Architecture capacity passed; g-info objective and q_D target failed/null. This motivates q_A residual and q_D target audit. |
| EXP-20260705-r21-team-intent | completed / negative | R21 | cloud CUDA seed1 | ExpManager | none | `dist/logs_cloud_r21_team_intent_64env`, `memory/R21_AUTOPSY_REPORT.md` | Z was near-inert; sampled team code did not create recoverable team effect. No seed2 or sweep on this design. |

## Active Experiment Detail

### EXP-20260711-r26-g1a-individual-skill-screening

Launch-ready factual record for the reward-off R26-G1a six-checkpoint
individual-skill behavior screening. The experiment has not been launched, and
no scientific `PASS`/`FAIL` decision has been made.

- Status: `launch-ready`
- Stage: `R26-G1a reward-off screening`
- Location/compute: local CUDA only, NVIDIA GeForce RTX 4070 Laptop GPU,
  8188 MiB (8 GB); no CPU fallback
- Proposed run root: `logs/r26_g1a_screening/`
- Runner: `scripts/run_r26_g1_screening_local_cuda.ps1`
- Estimated wall time: approximately 30-45 minutes for all six sequential
  checkpoints. This is a controller estimate, not a launch fact, based on the
  five-reset smoke shard cadence (approximately 16 seconds observed) extrapolated
  to 64 resets plus analyzer/runtime overhead.
- Implementation state: 52 focused tests passed; Python compilation, runner
  dry-run, PowerShell parser, and diff-hygiene checks passed; task reviews are
  clean. Launch is not authorized or executed.
- Status source: TestRunner final verification, controller pace estimate, and
  the accepted R26-G1a design/implementation plan.

**Pre-launch contract correction (2026-07-11):** the prior launch-ready record
erroneously expanded the numeric gate from the accepted three grouped matched
nulls to five label nulls. Before any R26-G1a scientific data were collected,
the record was aligned with the accepted executable contract: the
gate-mandatory grouped matched nulls are exactly `agent_matched`,
`duration_matched`, and `agent_duration_matched`. `shuffled` and
`fake_marginal` remain required reported diagnostic/global label nulls, but are
excluded from the numeric gate, strongest-matched-null bootstrap, and
gate-overfit invalidation. No executable semantics or observed result changed;
the experiment remains launch-ready, not launched, and reward-off.

**Exact proposed command (not executed)**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/run_r26_g1_screening_local_cuda.ps1 -RunRoot logs/r26_g1a_screening -Device cuda -NResets 64
```

**Frozen checkpoint inventory** (`NumSkills=4` for every checkpoint):

- `arm0_update25`: `dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt`
- `arm0_update30`: `dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt`
- `arm0_final`: `dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt`
- `arm2_update25`: `dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_update_25.pt`
- `arm2_update30`: `dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_update_30.pt`
- `arm2_final`: `dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_final.pt`

The runner must verify each collector manifest reports
`checkpoint_metadata.n_skills=4` before analysis; it must reject a mismatch
rather than infer or change analyzer cardinality.

**Expected artifacts**:

- Batch: `logs/r26_g1a_screening/batch_status.txt`.
- Per arm under `logs/r26_g1a_screening/<arm-name>/`: `command.txt`,
  `runner_status.txt`, `collector_output.log`, `analyzer_output.log`,
  `windows/` (reset shards and `collector_manifest.json`), and `analysis/`
  (`r26_g1_behavior.json` and `r26_g1_behavior.md`).

**Pre-registered read**:

- Per checkpoint, report label count, normalized label entropy, maximum label
  fraction, grouped train/validation/test row and reset counts, test accuracy,
  macro-F1, cross-entropy, majority accuracy, `acc_full - acc_prior`,
  `acc_behavior - acc_prior`, `acc_behavior(post) - acc_behavior(pre)`, the
  per-row `log q_full(z_i) - log q_prior(z_i)` mean and positive fraction,
  real-minus-null differences, reset-cluster bootstrap 95% confidence
  intervals, early-stop steps, and train/test gaps.
- A checkpoint clears the numeric gate only if all five conditions hold:
  normalized label entropy is at least `0.8`; `acc_full - acc_prior >= 0.05`;
  `acc_behavior(post) - acc_behavior(pre) >= 0.05`; real beats every
  gate-mandatory grouped matched null (`agent_matched`, `duration_matched`, and
  `agent_duration_matched`) and the reset-cluster bootstrap 95% lower
  confidence bound for real versus the strongest of those three matched nulls
  is above zero; and no train/test overfit warning invalidates the read.
- The overfit warning is a strict train-minus-test accuracy gap greater than
  `0.20` for any fitted probe participating in the gate or required matched-null
  comparison; a gap equal to `0.20` does not trigger it.
- The arm0 family gate requires at least two of update 25, update 30, and final
  to pass in the same direction. Arm2 is context/contrast only and cannot rescue
  an arm0 family failure. With one R25 seed, any family pass remains screening
  evidence rather than a publication-level causal claim.

**Prohibited while this gate is open**:

- No `q_d`, `q_D`, or intrinsic-reward injection.
- No G1b implementation, training/resume, scale-up, or scientific claim before
  the reward-off screening is run and read.
- A pass authorizes only separate design and pre-registration of G1b forced-`z_i`
  intervention; it does not authorize reward.

**Next factual read point**: after an explicitly authorized run, inspect
`batch_status.txt`, every per-arm status/log/manifest, every analyzer JSON and
Markdown report, the per-checkpoint gate fields, and the arm0 2-of-3 family
gate. Record facts only; the controller owns scientific interpretation.

### EXP-20260710-r25-qa-verification-1m

Completed cloud execution record for the q_A verification tier.

- Status: `completed / read + dispositioned 2026-07-10`
- Stage/Round: `R25 verification tier` (scaling R23-validated q_A to 1M steps, 64 env)
- Location/compute: cloud CUDA, 64 envs, 1M steps (1000000), two arms, default seed `1`
- Runner script: `scripts/run_r25_qa_verification_cloud_64env_1m.sh`
- Build validation: `logs/r25_runner_build/dryrun.log` (captured --dry-run output)
- Bash syntax check: PASS (bash -n validation 2026-07-09 expmanager build)

**Arm configuration (exact R23 flags preserved)**:
- `arm0_arch_only`: Team-intent baseline (control). Flags:
  - `--enable_team_intent --enable_team_disc_probe --team_intent_k 8 --z_assignment_residual_gain 0.5`
  - No q_A reward, no q_d/q_D rewards
- `arm2_qA_reward`: Team-intent + q_A actionability residual (treatment). Flags:
  - All arm0 flags, plus:
  - `--enable_assignment_actionability_reward --assignment_actionability_coef 0.02 --assignment_actionability_clip 1.0 --assignment_actionability_warmup_steps 20000`
  - q_d/q_D rewards OFF

**Hyperparameters**:
- Scenario: S7-S1, 6 agents
- Collector: subproc, spawn start method
- Rollout length: 500, skill interval: 10
- Skill durations: 1,2,3,4 (R23 Choice-0, not R24's 3,7,13,24)
- Total timesteps: 1,000,000
- Eval interval: 160,000 (eval at 160k, 320k, 480k, 640k, 800k, 960k)
- Save interval: 5 updates (1M / 64*500 = 31 updates; save every ~160k steps to match eval cadence)
- Checkpoint keep: 4 (maintains mature checkpoints for G1 diagnostics)
- Eval episodes: 20 per eval window
- Guard mode: kill (standard)

**Per-run directory structure** (relative to repo root):
```
logs_cloud_r25_qa_verification_1m/
  arm0_arch_only/
    seed1/
      command.txt
      runner_status.txt (started/finished state)
      runner_output.log (full trainer output)
      standalone_train.log (readable log)
      metrics/
        train_updates.csv
        eval_episodes.csv
      standalone_process_core_update_5.pt (160k checkpoint)
      standalone_process_core_update_10.pt (320k checkpoint)
      standalone_process_core_update_15.pt (480k checkpoint)
      ... (continue every 5 updates)
      standalone_process_core_final.pt (1M checkpoint)
      events.* (TensorBoard)
  arm2_qA_reward/
    seed1/
      (same structure)
```

**Default launch commands** (for controller copy-paste to cloud server):
```bash
# Dry-run (no execution; prints all commands):
bash scripts/run_r25_qa_verification_cloud_64env_1m.sh --dry-run

# Full execution (both arms, seed 1):
bash scripts/run_r25_qa_verification_cloud_64env_1m.sh

# Single arm/seed variants:
ARMS=arm0_arch_only bash scripts/run_r25_qa_verification_cloud_64env_1m.sh
ARMS=arm2_qA_reward bash scripts/run_r25_qa_verification_cloud_64env_1m.sh
SEEDS=1 bash scripts/run_r25_qa_verification_cloud_64env_1m.sh
```

**Expected artifacts**:
- Per-run logs: `logs_cloud_r25_qa_verification_1m/arm{0_arch_only,2_qA_reward}/seed1/{command.txt,runner_status.txt,runner_output.log}`
- Training metrics: `logs_cloud_r25_qa_verification_1m/arm{0,2}/seed1/metrics/{train_updates.csv,eval_episodes.csv}`
- Checkpoints: `standalone_process_core_update_{5,10,15,20,25,30}.pt`, `standalone_process_core_final.pt`
- Build evidence: `logs/r25_runner_build/dryrun.log` (this session's validation)

**Time estimate** (wall-clock, per arm):
- Baseline from R24 archive: 320k steps on 64 env took ~1.9 hours (per archive timestamps)
- Scaling: 1M / 320k = 3.125x, so ~5.9 hours per arm
- Conservative estimate: ~6 hours per arm sequentially, ~12 hours total for both arms
- Parallel: if controller runs both seeds simultaneously on separate GPUs, ~6 hours wall time
- Cloud resource: 64 parallel environments, 1 GPU (CUDA, standard cloud instance)

**Read plan** (post-launch analysis):
1. Monitor checkpoint progression: verify updates 5, 10, 15, ... 30 exist (5-update saves) by ~30 min
2. Eval trajectory (coverage_ratio field):
   - Target: arm2 should trend higher than arm0 (mechanistic q_A effect)
   - Baseline: HMASD S7-S1 (REF-20260617) shows coverage >=0.7 by 480k, >=0.9 by 800k, plateau ~0.96
   - Interpretation: if arm2 reaches HMASD milestones earlier/higher than arm0, evidence for q_A scaling;
     if both track HMASD, no task-level q_A boost (but mechanism may still be present in residual_gain)
3. Mechanism fields (from train_updates.csv):
   - `assignment_actionability_gain`: should be >0 and rising in arm2 (measure of q_A learning)
   - `z_usage_entropy`: target >0.8 (skills actively used, not collapsed); baseline ~0.96 in R24
   - `z_assignment_itv` (forced-Z KL): should be stable or rising in arm2 (Z recoverable under q_A reward)
4. Checkpoint maturity (by update 20-25 ~ 640k-800k steps):
   - Verify coverage ~0.7-0.9 reached (ready for G1 skill-differentiation diagnostics)
   - No collapse signatures (zero_throughput_step_fraction >0.9, z_usage_entropy <0.5)
5. Final maturity (update 30 ~ 960k steps):
   - Checkpoints ready for offline G1 probes (don't delete until G1 work complete)
   - Expected: arm2 checkpoint carries both q_A learning + team-intent structure for G1 individual-skill probing

**Caveats**:
- Single seed (seed 1 only): results are point estimates; seed-consistency requires seed 2 re-run
- 64 env matches R23-next matrix cloud baseline; local 16env R23 showed noise-dominated task signal
- Mature checkpoint criteria (800k+): earlier checkpoints may show high noise; gate decisions deferred to 800k+

**Result read (2026-07-10)**:

- Both arms finished cleanly: 1,000,000 steps, 64 envs, 32 PPO updates, seed 1, ~6h10m each, back-to-back on one GPU. Manifests confirm arms differ only in the q_A reward block; q_d/q_D rewards off in both.
- Eval coverage trajectory (mean of 20 episodes) at 160k/320k/480k/640k/800k/960k: arm0_arch_only 0.067/0.033/0.055/0.235/0.230/0.417 (rising at end); arm2_qA_reward 0.060/0.147/0.085/0.052/0.113/0.113 (flat since 320k). Throughput at 960k: arm0 13.76 Mbps vs arm2 2.81. Episode reward at 960k: arm0 57.7 vs arm2 20.4.
- Pattern: arm2 led most metrics at 160k–480k; arm0 reversed and widened the gap over the last 3 eval points (all four core metrics aligned).
- Neither arm crossed HMASD reference milestones (0.7@480k, 0.9@800k, plateau 0.964±0.003). arm0 max 0.417@960k, still rising; arm2 0.113.
- q_A mechanism itself was live and learning in arm2: reward mean 0.000115→0.0046, acc_full 0.16→0.35 vs prior ~0.18, residual_gain 0.038→0.172 monotone rising. Entropies/switch_rate nearly identical across arms (z_usage ~0.98 both).
- Anomalies logged: eval `checkpoint` column NaN (use total_steps); arm2 `q_a_reward_applied_steps` drops 7700→2011 at final update (undiagnosed); no 1M eval row (expected, eval_interval boundary).
- Variance context: nominally identical R24 320k family spanned coverage 0.0–0.7, so single-seed point estimates are wide; the informative signal is the within-pair late reversal, not absolute levels.

**Disposition Accepted (2026-07-10, Round 6 peer review)**:

- External review Round 6 (GPT-5.6-sol max xhigh; raw reply archived in `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md`):
  - **D1 ACCEPTED**: q_A intrinsic reward = NOT VERIFIED at this gate; demoted from promoted/sanctioned (R23-validated) to default-off. Wording condition: this is a gate failure "under the tested setup, n=1 seed per arm", NOT a settled claim that q_A is causally harmful; arm0 is the stronger line but not "proven superior" from n=1. q_A discriminator remains available probe-only. Architecture flags (team_intent_k 8, z_assignment_residual_gain 0.5) stay mainline.
  - **D2 ACCEPTED**: HMASD parity OPEN, not failed — update-count confound (32 updates vs HMASD ~2×/step) plus arm0 still rising. Reviewer info-value ranking for follow-ups: 1M@32env update-matched > seed-2 R25 replication > 2M@64env. Next verification run = 1M@32env.
  - **D3 ACCEPTED**: R26 = G1 individual-skill differentiation / actor-conditioning capacity (per principles G1 gate), screening tier first. Use R25 mature checkpoints (updates 25/30/final, both arms) for diagnostics; treat arm2 as a CONTRAST condition (legibility-vs-task divergence), not a better checkpoint; caveat: 32-update snapshots may be underpowered for G1 probes.
  - Reviewer red flags recorded: serially-correlated late eval points ≠ independent replications; no CIs on 20-episode eval means; q_A reward magnitude relative to env advantage never quantified (required before any "interference" causal claim); HMASD reference single-run and not update-matched.
  - Approved-cheap follow-up diagnostics (existing logs/checkpoints only, no training): (i) correlate q_A reward share + residual gain vs task metrics across checkpoints; (ii) offline-score arm0 vs arm2 trajectories with the frozen q_A discriminator (legibility-vs-service dissociation test).

### EXP-20260707-r24-assignment-to-behavior-bridge

Current overnight run in scope: `logs_r24_overnight_existing_local_cuda/run_20260708_000836` (started by script `scripts/run_r24_overnight_existing_local_cuda.ps1`).

- Current arm status (snapshot):
  - `arm1_qA_checkpoint_forced_audit`: `finished`, `state=finished`, `exit_code=0`, `r24_audit_records=1920`, latest row `r24_xi_effect_distance_h50=0.391939268868`, `r24_z_effect_distance_h50=0.452627063296`.
  - `arm2_null_arch_no_qA_forced_audit`: `finished`, `state=finished`, `exit_code=0`, `r24_audit_records=1920`, latest row `r24_xi_effect_distance_h50=0.299989670404`, `r24_z_effect_distance_h50=0.192383847632`.
  - `arm3_null_qD_probe_no_qA_forced_audit`: `finished`, `state=finished`, `exit_code=0`, `r24_audit_records=1920`, latest row `r24_xi_effect_distance_h50=0.418377785946`, `r24_z_effect_distance_h50=0.325177116581`.
  - `arm4_behavior_window_qd_probe_seed1`: `finished`, `state=finished`, `exit_code=0`, latest `standalone_update=40`, `total_steps=320000`, `return_mean=2.618014`, `standalone_eval reward_mean=35.532402`, `coverage=0.240000`, `qos=0.157180`, `throughput=11.477799`.
- `arm5_behavior_window_qd_probe_seed2`: `finished`, `state=finished`, `exit_code=0`, latest `standalone_update=40`, `total_steps=320000`, `return_mean=1.248149`, `standalone_eval reward_mean=57.210692`, `coverage=0.305000`, `qos=0.150263`, `throughput=6.418232`.

- Snapshot check artifacts:
  - `runner_status.txt` present for all five arms.
  - `runner_output.log` tails and latest audit/train rows were checked for all five arms.
  - `_watch/watch_state.json` reports `done=true`, `process_count=0`, `issues=[]`.

### EXP-20260708-r24-qd-null-control-cloud-handoff

Cloud archive inspection facts:

- Archive path: `dist/logs_cloud_r24_qd_null_control_64env.zip`.
- Extracted path: `dist/r24_qd_null_control_log_extract_expmanager_20260708_230322/logs_cloud_r24_qd_null_control_64env`.
- Top-level run directories in the archive: `seed1`, `seed2`.
- Each seed contains one run directory:
  - `seed1/r24_qd_null_control_seed1`
  - `seed2/r24_qd_null_control_seed2`
- Key files present in each run directory:
  - `command.txt`
  - `runner_status.txt`
  - `runner_output.log`
  - `standalone_train.log`
  - `metrics/train_updates.csv`
  - `metrics/eval_episodes.csv`
  - `standalone_process_core_final.pt`
  - TensorBoard event file(s)
- `runner_status.txt` facts:
  - seed1: `state=finished`, `exit_code=0`, `finished=2026-07-08T21:09:34+08:00`
  - seed2: `state=finished`, `exit_code=0`, `finished=2026-07-08T22:59:13+08:00`
- Latest `train_updates.csv` row facts:
  - seed1: `update=10`, `total_steps=320000`, `return_mean=1.3028457164764404`, `process_reward_mean=0.0`
  - seed2: `update=10`, `total_steps=320000`, `return_mean=0.6852400898933411`, `process_reward_mean=0.0`
- Latest `eval_episodes.csv` row facts:
  - seed1: `episode=19`, `total_steps=320000`, `reward=52.852671269315316`, `coverage_ratio=0.8`, `qos_satisfaction_ratio=0.287037037037037`, `system_throughput_mbps=8.611111111111114`, `backhaul_connected_step_fraction=0.51`, `coverage_eq1_step_fraction=0.0`, `zero_throughput_step_fraction=0.49`, `throughput_gt5_step_fraction=0.51`
  - seed2: `episode=19`, `total_steps=320000`, `reward=-4.881497951854478`, `coverage_ratio=0.0`, `qos_satisfaction_ratio=0.0`, `system_throughput_mbps=0.0`, `backhaul_connected_step_fraction=0.0`, `coverage_eq1_step_fraction=0.0`, `zero_throughput_step_fraction=1.0`, `throughput_gt5_step_fraction=0.0`
- Bounded log scan on both `runner_output.log` files found no matches for `Traceback`, `RuntimeError`, `NaN`, `OOM`, `CUDA`, or `BrokenPipe`.

- Gate-read facts from the completed overnight run:
  - All five arms finished with `exit_code=0`.
  - Watch state remained `done=true` with `process_count=0` and `issues=[]`.
  - No `Traceback`, `RuntimeError`, `NaN`, `OOM`, or `BrokenPipe` matches were found in the arm logs.
  - Forced audit effect ratios: `arm1/arm2 z_effect_h50=2.352729` PASS; `arm1/arm3 z_effect_h50=1.391940` PASS.
  - Forced audit growth ratios: `arm1/arm2 z_growth_h50_h10=0.985999` FAIL; `arm1/arm3 z_growth_h50_h10=0.731172` FAIL.
  - Forced audit between/within H50: `z_bw_ratio_h50=0.308040`, which is below `1.2`.
  - q_d seed1: `r24_qd_residual_gain=0.017408` FAIL; `r24_qd_positive_frac=0.508704` FAIL; `r24_qd_acc_full - r24_qd_acc_prior=0.017407` FAIL.
  - q_d seed2: `r24_qd_residual_gain=0.063694` PASS; `r24_qd_positive_frac=0.598726` FAIL; `r24_qd_acc_full - r24_qd_acc_prior=0.063694` PASS.
  - Overall q_d gate status: FAIL because the criteria are not consistently met across seeds and `positive_frac` fails both seeds.

- Launch command template:
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\run_r24_overnight_existing_local_cuda.ps1 -RunRoot <RUN_ROOT> -Python <PYTHON_EXE> -Device cuda -NResets 64 -NumEnvs 16 -TotalTimesteps 160000 -IncludeBehaviorWindowQdProbe`
- `-IncludeBehaviorWindowQdProbe` is optional and adds two reward-off checks (`seed1` and `seed2`) using the current behavior-window two-stream q_d probe. `-IncludeLegacyQdProbe` remains a backward-compatible alias for old command habits, but it launches the same current behavior-window probe.
- Sequential arms in the script (all command+status+output under arm-specific folders):
  1. `arm1_qA_checkpoint_forced_audit`  
     checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm2_qA_reward_coef002/standalone_process_core_update_40.pt`
  2. `arm2_null_arch_no_qA_forced_audit`  
     checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm0_arch_only/standalone_process_core_final.pt`
  3. `arm3_null_qD_probe_no_qA_forced_audit`  
     checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm3_qD_audit/standalone_process_core_update_40.pt`
  4. optional `arm4_behavior_window_qd_probe_seed1` (`q_d` probe seed 1, `TotalTimesteps=160000`)
  5. optional `arm5_behavior_window_qd_probe_seed2` (`q_d` probe seed 2, `TotalTimesteps=160000`)
- Planned artifacts:
  - each arm writes `command.txt`, `runner_status.txt`, `runner_output.log` under `RunRoot\arm*`  
  - behavior-audit arms write `r24_behavior_audit.csv` inside each arm `-OutDir`
  - behavior-window q_d probe arms write `seed1/` and `seed2/` subfolders under their arm `LogRoot`
  - watcher writes `watch_status.log`, `watch_alert.txt`, and `watch_state.json` under `_watch`
  - Codex alert handler writes `codex_recovery_evidence_*.md`, `codex_recovery_prompt_*.md`,
    `codex_recovery_decision_*.json`, and `codex_recovery_transcript_*.log` under `_watch\codex_recovery`
- Metrics to monitor:
  - forced-audit `r24_xi_effect_h*`, `r24_z_effect_h*`, `r24_xi_action_distance_h*`, `r24_z_action_distance_h*`, `r24_xi_effect_between_within_ratio_h*`, `r24_z_effect_between_within_ratio_h*`
  - behavior-window q_d probes: `r24_qd_residual_gain`, `r24_qd_residual_mean`, `r24_qd_positive_frac`, `r24_qd_acc_full`, `r24_qd_acc_prior`, `r24_qd_loss_full`, `r24_qd_loss_prior`
- Caveat:
  - current code now uses a behavior-window action/effect dual stream and `xi_context_i` excluding focal `z_i`; the remaining caveat is that held-out shortcut/null controls and Round-3 reward gates are not yet fully implemented, so this remains reward-off diagnostic evidence only.

`logs_r24_qd_probe_local_cuda/seed1` and `logs_r24_qd_probe_local_cuda/seed2`
were launched by `scripts/run_r24_qd_probe_local_cuda.ps1`.

Updated q_d null-control facts from the post-2026-07-08 probe:

- `seed1` latest train row: `update=19`, `total_steps=152000`,
  `r24_qd_acc_full=0.42357274889945984`,
  `r24_qd_acc_prior=0.3775322437286377`,
  `r24_qd_acc_behavior=0.3922652006149292`,
  `r24_qd_acc_pre=0.37807607650756836`,
  `r24_qd_residual_gain=0.046040505170822144`,
  `r24_qd_positive_frac=0.6721915602684021`,
  `r24_qd_shuffle_acc_gap=-0.003683239221572876`,
  `r24_qd_fake_acc_gap=-0.04051566123962402`.
- `seed1` tail log ends with `standalone_runtime_guard mode=kill prototype
  discriminator reward/env ratio exceeded instant guard ratio=1.643980 update=19
  total_steps=152000`, so this run stopped early rather than reaching the full
  320k budget.
- `seed2` latest train row: `update=32`, `total_steps=256000`,
  `r24_qd_acc_full=0.4525691866874695`,
  `r24_qd_acc_prior=0.38932809233665466`,
  `r24_qd_acc_behavior=0.4229249060153961`,
  `r24_qd_acc_pre=0.3975609838962555`,
  `r24_qd_residual_gain=0.06324109435081482`,
  `r24_qd_positive_frac=0.658102810382843`,
  `r24_qd_behavior_gain_over_prior=0.033596813678741455`,
  `r24_qd_pre_gain_over_prior=0.009756118059158325`,
  `r24_qd_shuffle_acc_gap=-0.04743081331253052`,
  `r24_qd_fake_acc_gap=-0.03557312488555908`.
- `seed2` log tail currently ends at `update=32`, `total_steps=256000`; there is
  no CSV evidence in the inspected file that it reached the full 320k budget.

Cloud handoff facts for the unfinished R24 q_d null-control run:

- The controller prepared a cloud runtime package at
  `dist/ha_ctse_r24_qd_null_control_cloud_runtime_20260708_190315.zip` with
  matching directory
  `dist/ha_ctse_r24_qd_null_control_cloud_runtime_20260708_190315`.
- Package verification facts supplied by the controller: runner/train/q_d/env/
  routing present; `memory/` excluded; `pyc` count 0; `pt/pth` count 0; entry
  count 160; zip size 813431 bytes.
- New cloud runner script: `scripts/run_r24_qd_null_control_cloud_64env.sh`.
- Cloud settings to preserve: Linux bash, CUDA, 64 env, S7-S1, `n_agents=6`,
  seeds 1 and 2, `total_timesteps=320000`, `eval_interval=160000`,
  q_A actionability reward on, `q_d/q_D` reward off, `GUARD_MODE=warn`.
- Primary cloud log root: `logs_cloud_r24_qd_null_control_64env`.
- Commands recorded for launch: `bash scripts/run_r24_qd_null_control_cloud_64env.sh --dry-run`,
  `bash scripts/run_r24_qd_null_control_cloud_64env.sh`,
  `SEEDS=1 ...`, `SEEDS=2 ...`.

### EXP-20260709-r24-frozen-qd-null-probes

Launch-ready cloud execution record for the frozen q_d null-probe.

- Status: `launch-ready`
- Stage/Round: `R24 frozen q_d null probes`
- Location/compute: cloud CUDA, 64 envs, 320k steps, default seeds `1,2`
- Runner: `scripts/run_r24_qd_null_control_cloud_64env.sh`
- Default log root: `logs_cloud_r24_qd_null_control_64env`
- Commands recorded:
  - `EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh --dry-run`
  - `EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh`
  - `SEEDS=1 EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh`
  - `SEEDS=2 EXPORT_QD_WINDOWS=1 RUN_FROZEN_NULL_ANALYSIS=1 bash scripts/run_r24_qd_null_control_cloud_64env.sh`
- Artifact paths to read after cloud launch:
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/train_updates.csv`
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/runner_output.log`
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/r24_qd_windows/*.npz`
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/r24_qd_frozen_nulls/r24_qd_frozen_nulls.json`
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/r24_qd_frozen_nulls/r24_qd_frozen_nulls.md`
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/frozen_null_command.txt`
  - `logs_cloud_r24_qd_null_control_64env/seed*/r24_qd_null_control_seed*/frozen_null_output.log`
- Factual purpose: reward-off diagnostic to capture frozen null controls for q_d before any q_d/q_D reward decision.
- Read notes:
  - inspect `r24_qd_acc_full`, `r24_qd_acc_prior`, `r24_qd_residual_gain`, `r24_qd_positive_frac`, `r24_qd_acc_behavior`, `r24_qd_acc_pre`, `r24_qd_shuffle_acc_gap`, and `r24_qd_fake_acc_gap` from the train CSV;
  - inspect offline analyzer full/prior/residual, matched shuffled-label nulls, fake-label nulls, duration/agent-grouped nulls, and pre/behavior-only comparisons.

Current gate:
- Full forced behavior audit completed after the 2026-07-07 checkpoint
  compatibility fix. The audit is encouraging (`xi_effect`: 0.17335->0.25677->0.41290;
  `z_effect`: 0.18912->0.27497->0.46262) but not sufficient alone to unblock reward.
- Smoke command passed and wrote `logs_r24_behavior_audit_smoke/r24_behavior_audit.csv`
  with `r24_audit_records=4`, `r24_z_action_distance_h1=0.10420`,
  `r24_xi_action_distance_h1=0.21116`, `r24_z_effect_distance_h1=0.00445`,
  and `r24_xi_effect_distance_h1=0.00181`.
- Full command:
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_r24_behavior_audit_local_cuda.ps1 -NResets 16`
- Full command completed and wrote `logs_r24_behavior_audit_local/r24_behavior_audit.csv`
  with `r24_audit_records=480`, `r24_xi_action_distance_h10/h20/h50=0.30369`,
  `r24_z_action_distance_h10/h20/h50=0.20666`,
  `r24_xi_effect_distance_h10/h20/h50=0.17335/0.25677/0.41290`,
  `r24_z_effect_distance_h10/h20/h50=0.18912/0.27497/0.46262`,
  `r24_xi_label_entropy_h*=1.38629`, and `r24_z_label_entropy_h*=1.79176`.
- Note on UX: `scripts/run_r24_behavior_audit_local_cuda.ps1` delegates to
  `scripts/r24_forced_behavior_audit.py`, which prints metrics only after the
  audit finishes and writes the CSV at the end. A quiet console during execution
  is therefore expected for this script.

Run snapshot findings (prior completed diagnostic run, now superseded by the final 320k completion):
- Historical 160k snapshot for `run_20260708_000836`:
  - `watch_state.json` in `_watch` and `_watch_status_check` report `arm1` finished, `arm2` finished, `arm3` running.
  - Latest watcher snapshot includes GPU utilization `3%` with `1325 MiB / 8188 MiB` VRAM used on GPU 0.
  - `nvidia-smi` at read time confirms RTX 4070 Laptop GPU `1287 MiB / 8188 MiB` used, `3%` utilization.
  - `runner_output.log` file sizes: arm1 `2848`, arm2 `2836`, arm3 `0` bytes.
  - `runner_status.txt` sizes: arm1 `471`, arm2 `479`, arm3 `480`.

- Process-tree checks for this run are blocked by workspace permission (access denied for detailed listing/command lines). A Python process was observable via PID inventory at this read, but full command-line/process-tree inspection remains permission-restricted.
- `train_updates.csv`: 20 data rows; latest update=20 at `total_steps=160000`.
- `eval_episodes.csv`: 20 data rows (requested count reached), latest episode=19 at `total_steps=160000`.
- Checkpoints: `standalone_process_core_update_20.pt` and
  `standalone_process_core_final.pt` both exist.
- Last train update `r24`/probe metrics:
  `r24_qd_active=1.0`, `r24_qd_samples=543.0`,
  `r24_qd_acc_full=0.33149170875549316`, `r24_qd_acc_prior=0.32044199109077454`,
  `r24_qd_residual_gain=0.011049717664718628`,
  `r24_qd_residual_mean=0.00891975499689579`,
  `r24_qd_positive_frac=0.5285451412200928`,
  `z_usage_entropy=0.9316608242035893`,
  `duration_usage_entropy=0.9655920718201262`,
  `combined_intrinsic_env_ratio=0.14822086680486282`,
  `combined_intrinsic_env_ratio_kill_triggered=0.0`.
- Last eval row (`episode=19`) values include:
  `reward=32.000119264395046`, `coverage_ratio=0.5`, `length=500`,
  `backhaul_connected_step_fraction=0.334`, `throughput=3.691667`,
  `zero_throughput_step_fraction=0.666`, `throughput_gt5_step_fraction=0.334`.
- Run summary line in `standalone_train.log` reports
  `reward_mean=21.397332`, `coverage=0.120000`, `throughput=3.691667`
  at `total_steps=160000`, `episodes=20`.

Error scan:
- `standalone_train.log`, `train_updates.csv`, `eval_episodes.csv` contain 0 matches for
  Traceback, RuntimeError, NaN, OOM, or BrokenPipe.

Pending matched-null control/probe gates:
- A) matched-architecture, no-q_A control (`z_assignment_residual_gain=0.5`, same
  architecture/checkpoint stage, q_A OFF)
- B) random-init or early-checkpoint control
- C) fake/shuffled label control
- D) within-label repeat baseline
- Gate criteria before any reward-on path:
  - control-normalized `effect_ratio_h50 >= 1.3` (strong >=1.5)
  - `growth_h50_minus_h10` > control (`>=1.3x` suggested)
  - `between_within_ratio_h50 > 1.2` (strong >1.5)
- `q_D` and `q_d` remain reward-off until matched-null controls and reward-off
  behavior-window `q_d` probe both pass.

Operational candidate scan (2026-07-07):
- Current q_A audit checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm2_qA_reward_coef002/standalone_process_core_update_40.pt`
  (q_A reward ON, coef=0.02, 16 env training, 320k total steps).
- Best immediate Null A candidate without new training:
  `logs_r23_next_mechanism_matrix_local/seed1/arm0_arch_only/standalone_process_core_final.pt`
  (same team-intent architecture, `z_assignment_residual_gain=0.5`, q_A reward/probe OFF,
  32 env training, 320k total steps). This is usable as a first matched architecture
  no-q_A control, but the env-count difference means it is a mechanism screen, not a
  final paper-grade matched control.
- Secondary no-q_A candidate:
  `logs_r23_next_mechanism_matrix_local/seed1/arm3_qD_audit/standalone_process_core_update_40.pt`
  (q_A reward OFF, q_D audit probe ON, 16 env, 320k). Useful as a same-env-count
  reward-off probe-policy control, but less clean than arm0 because audit heads were active.
- Existing `scripts/r24_forced_behavior_audit.py` can run checkpoint-to-checkpoint
  forced audits now, but does not yet implement fake/shuffled-label controls or emit
  between/within ratios despite helper support in `ha_ctse_process/r24_behavior_audit.py`.

Matched-null forced-audit read (2026-07-07, v1):
- `logs_r24_behavior_audit_null_arch_no_qA/r24_behavior_audit.csv` completed
  (`r24_audit_records=480`). This is matched architecture/no-q_A but trained with
  32 env, so it is a first mechanism screen rather than a final matched-env control.
- `logs_r24_behavior_audit_null_qD_probe_no_qA/r24_behavior_audit.csv` completed
  (`r24_audit_records=480`). This is 16env/no-q_A but qD-audit probe active, so it is
  a same-env-count reward-off probe-policy control.
- q_A reward checkpoint vs `arch_no_qA`:
  `xi_effect_ratio_h50=1.19`, `xi_growth_ratio=0.99` (FAIL);
  `z_effect_ratio_h50=2.33`, `z_growth_ratio=2.13` (STRONG PASS).
- q_A reward checkpoint vs `qD_probe_no_qA`:
  `xi_effect_ratio_h50=0.95`, `xi_growth_ratio=0.90` (FAIL);
  `z_effect_ratio_h50=1.32`, `z_growth_ratio=1.15` (BORDERLINE PASS on h50 ratio,
  weak on growth).
- Interpretation: the matched-null screen supports a real team-level `Z` behavior
  bridge from q_A reward, especially against the clean arch-only null. It does not
  support an individual `xi` semantic bridge yet, and therefore does not justify
  q_d reward-on. The next code/experiment need is non-core audit tooling for
  fake/shuffled labels and within-label repeat ratios before any reward path changes.

Matched-null forced-audit read (2026-07-07, v2 with between/within + shuffled
baseline fields):
- `logs_r24_behavior_audit_local_v2/r24_behavior_audit.csv`, `logs_r24_behavior_audit_null_arch_no_qA_v2/r24_behavior_audit.csv`,
  and `logs_r24_behavior_audit_null_qD_probe_no_qA_v2/r24_behavior_audit.csv`
  completed (`r24_audit_records=480` each). Runs were executed sequentially by
  ExpManager; no code or memory changes were made by the subagent.
- q_A v2:
  `xi_effect_h50=0.41290`, `z_effect_h50=0.46262`;
  `xi_growth_h50_h10=0.23956`, `z_growth_h50_h10=0.27350`;
  `xi_effect_between_within_ratio_h50=0.30368`, `z_effect_between_within_ratio_h50=0.55443`;
  `xi_effect_between_within_lift_h50=5.82319`, `z_effect_between_within_lift_h50=11.18140`.
- Null arch/no-q_A v2:
  `xi_effect_h50=0.34756`, `z_effect_h50=0.19854`;
  `xi_growth_h50_h10=0.24157`, `z_growth_h50_h10=0.12847`;
  `xi_effect_between_within_ratio_h50=0.03903`, `z_effect_between_within_ratio_h50=0.07329`;
  `xi_effect_between_within_lift_h50=0.80077`, `z_effect_between_within_lift_h50=1.34554`.
- Null qD-probe/no-q_A v2:
  `xi_effect_h50=0.43581`, `z_effect_h50=0.34917`;
  `xi_growth_h50_h10=0.26638`, `z_growth_h50_h10=0.23850`;
  `xi_effect_between_within_ratio_h50=0.04827`, `z_effect_between_within_ratio_h50=0.05799`;
  `xi_effect_between_within_lift_h50=1.00966`, `z_effect_between_within_lift_h50=1.10618`.
- Ratios vs arch/no-q_A:
  `xi_effect_h50=1.188`, `xi_growth=0.992`; `z_effect_h50=2.330`, `z_growth=2.129`.
- Ratios vs qD-probe/no-q_A:
  `xi_effect_h50=0.947`, `xi_growth=0.899`; `z_effect_h50=1.325`, `z_growth=1.147`.
- Mechanism read: team-level `Z` behavior bridge remains positive and clearly
  label-structured relative to shuffled/null baselines, especially against the
  clean arch-only null. The qD-probe/no-q_A control is a harder/null-contaminated
  comparison but still gives a borderline `z_effect_h50` pass. Individual `xi`
  does not pass either null. Absolute between/within ratios remain below the
  pre-registered strong threshold (`>1.2`), so this is not enough to enable
  q_d/q_D reward. Keep rewards blocked; next valid step is a behavior-window
  reward-off q_d/q_D probe design, not reward injection.

### EXP-20260709-r24-frozen-qd-null-probes (smoke verification)

Local pipeline smoke verification (2026-07-09):

- **Smoke objective**: Verify window-export -> frozen-null-analyzer end-to-end pipeline.
- **Command run**:
  `python -m ha_ctse_process.train --preset S7-S1 --scenario energy --n_agents 6 --num_envs 4 --collector_backend sync --total_timesteps 2000 --rollout_length 100 --skill_interval 4 --device cuda --enable_team_conditioned_qd_probe --r24_qd_export_windows --log_dir logs\r24_smoke_frozen_null_pipeline`
- **Training completion**: total_steps=2000 (5 updates at 400-step boundaries), final row at standalone_update 5.
- **QD window export facts**:
  - Shards directory: `logs/r24_smoke_frozen_null_pipeline/r24_qd_windows/`
  - Shard count: 5 npz files (update 1-5 at steps 400, 800, 1200, 1600, 2000)
  - Array names per shard: `['action', 'effect', 'condition', 'labels', 'pre_action', 'pre_effect', 'pre_valid', 'env_id', 'agent_id', 'duration_idx', 'segment_length', 'total_steps', 'update_idx']`
  - Total probe samples across shards: 350 labeled windows (train/eval split 267/83 per variant)
- **Analyzer execution**:
  - Command: `python scripts/analyze_r24_qd_frozen_nulls.py --input_dir logs/r24_smoke_frozen_null_pipeline/r24_qd_windows --output_dir logs/r24_smoke_frozen_null_pipeline/r24_qd_frozen_nulls --num_skills 6 --steps 300 --seed 17`
  - Exit status: 0 (success)
  - Output files created: `r24_qd_frozen_nulls.json` (7125 bytes), `r24_qd_frozen_nulls.md` (987 bytes)
- **Null variant coverage**: All 9 variants present in json: `real`, `shuffled`, `fake_marginal`, `duration_matched`, `agent_matched`, `behavior_only`, `pre_only`, `action_only`, `effect_only` ✓

Pre-registered gate-read checklist (to apply to cloud data after full-scale 320k-step run):

- **Per-seed residual gain and positive fraction criteria**:
  - residual_gain >= 0.05 (smoke real=0.0843, strong pass; smoke shuffled=-0.0361, baseline null)
  - positive_frac >= 0.60 (smoke real=0.5422, borderline/FAIL; smoke shuffled=0.4699, below threshold)
  - acc_full - acc_prior gap >= 0.05 (smoke real=0.0844, PASS; smoke shuffled=-0.0361, negative)
- **Real vs. null variant signal separation**:
  - real residual_gain (0.0843) vs. nulls: shuffled (-0.0361, inverted), fake_marginal (0.0120, ~7x gap), behavior_only (0.0361, ~2.3x), pre_only (0.0602, ~1.4x), effect_only (0.0723, ~1.2x)
  - shuffled/fake_marginal near-zero or inverted as expected; signal isolation baseline check PASS
- **Team-conditioned evidence signal (full - behavior_only acc)**:
  - smoke: full_minus_behavior_acc = -0.0602 (negative; behavior outperforms full model, weak team-context evidence)
  - GPT Round 4 context: cloud gate criterion is full - behavior > 0 demonstrating team-condition context gain
- **Per-seed policy health context columns** (to read from cloud eval/train CSV):
  - final `coverage_ratio`, `zero_throughput_step_fraction`, `z_usage_entropy`
  - Gate fail trigger: high zero_throughput (>0.9) + low z_usage_entropy (<0.5) indicates collapsed policy, weakening any discriminator evidence
- **Seed consistency requirement**:
  - Smoke demonstrates single-seed pipeline (positive)
  - Cloud gate criterion: both seeds must independently satisfy residual_gain>=0.05 AND positive_frac>=0.60 for reward unblock decision; inconsistency between seeds is automatic gate-fail

**Smoke result**: Pipeline health **PASS**. All 9 frozen-null variants exported and analyzed. Metric values are **throwaway** (2k-step smoke insufficient for convergence).

### EXP-20260709-r24-frozen-qd-null-probes (Cloud Archive & Local Analysis)

**Controller wording amendment (2026-07-09, user calibration):** where the
notes below say "collapsed policy / policy health", read
"early-training/underconverged at 320k" — HMASD itself was below 0.5 coverage
with zero-coverage eval episodes at 320k and converges only ~800k-1M. The R24-1
fail is therefore "fail at early-training checkpoints under the current
diagnostic setup"; mature-checkpoint (~1M) re-probes are the fair future test,
and mechanism diagnostics should preferentially run on mature checkpoints.

**Controller decision/interpretation (2026-07-09, seed1 early gate read):**
- qAon/seed1 (the HEALTHY policy: coverage 0.700, z_usage_entropy 0.958) frozen
  gate read = FAIL on all core gates: real residual_gain -0.0319 (negative),
  positive_frac 0.395, real ranked below 7 of 8 null variants,
  real - behavior_only = -0.023 (no team-conditioned evidence). Full table:
  `qAon/seed1/r24_qd_null_control_seed1/r24_qd_frozen_nulls/gate_read_seed1.md`.
- Verdict per pre-registered tree: q_d gate FAIL on a healthy policy. q_d/q_D
  rewards remain BLOCKED; no reading of this data supports reward-on.
- INSTRUMENT CAVEAT (direction-neutral, flagged before verdict): all frozen
  probes show held-out overfitting (loss_full 2.5-4.7x loss_prior across
  variants; action_only beats real; in-loop online probe on same run reads
  +0.010, opposite sign). All residual_gains cluster in a noise band; "no
  signal" vs "instrument cannot see" is not yet separated.
- Seed2 update (2026-07-09, collapsed-policy qAon seed): all core gates FAIL
  again (real residual_gain -0.0073, positive_frac 0.433). Cross-seed
  CONSISTENT facts: real residual ~0/negative in both seeds; real NEVER beats
  behavior_only (real - behavior_only = -0.023 in BOTH seeds) -> no
  team-conditioned evidence on healthy or collapsed policies; in-loop online
  probe reads small positive (+0.010/+0.011) while frozen reads ~0/negative in
  both. Pattern differences: seed2 is better-behaved (real 4/9, tight spread
  0.06, label-nulls below real) vs seed1's wild ordering (real 8/9, spread
  0.16); consistent instrument artifact in both: reduced-input probes
  (action_only etc.) generalize better than full-input real at fixed 300 steps
  (overfitting bias AGAINST real). New seed2 anomalies: two exact-identity
  degenerate variants (shuffled acc_full==acc_behavior; agent_matched
  acc_behavior==acc_prior). Table: `qAon/seed2/.../gate_read_seed2.md`.
- qAoff/seed1 update (2026-07-09, matched NO-q_A control, collapsed policy):
  all core gates FAIL. KEY: no q_A-dependence is visible — qAoff/seed1's
  pattern (real rank 8/9, spread 0.146) mirrors qAon/seed1 (8/9, 0.161), not
  qAon/seed2 (4/9, 0.060); per-seed variability dominates arm identity. real -
  behavior_only = -0.074 (most negative yet; behavior_only itself +0.061).
  In-loop/frozen sign AGREEMENT here (both negative), unlike both qAon seeds.
  No exact-identity degeneracies. Table: `qAoff_coef0/seed1/.../gate_read_qAoff_seed1.md`.
- Cross-run synthesis (3 of 4 read): (a) team-conditioning (real vs
  behavior_only) never helps in ANY run — the central R24-1 claim fails
  uniformly; (b) arm identity (q_A on/off) does not separate the frozen-null
  patterns — the probe sees the same near-nothing either way; (c) the only
  variant ever crossing gate-level residual is behavior_only (+0.061) on a
  collapsed no-q_A run — individual-behavior signal crumbs at best, orthogonal
  to the team-conditioned hypothesis.
- Controller posterior after two seeds: mechanism-fail is the likely final
  read; an instrument fix (early stopping) would need to swing real by ~+0.08
  to reach gates - implausible. Instrument fix remains worth ONE pre-registered
  re-run mainly to make the negative result solid, not to rescue the gate.
- Disposition: (1) fail stands, reward blocked; (2) do NOT modify the analyzer
  or reinterpret without the design cross-validation gate — any probe-training
  recipe change (early stopping / regularization) is a diagnostic-instrument
  change requiring marl-peer-reviewer review with pre-registered acceptance
  criteria; (3) qAoff/collapsed-seed analyses (retry in flight) will
  discriminate instrument-noise vs mechanism-fail: same noise-band pattern in
  qAoff strengthens the instrument-problem hypothesis; (4) pivot discussion
  (skill-differentiation half, per Do-Not-Do-Yet) folds in Phase-A b/w=0.308
  and tonight's seed-1 deconfound pair.

**Disposition Accepted (2026-07-09, Round 5 peer review):**
- External review Round 5 (GPT-5.5 xhigh, SUPPORTS_WITH_CONDITIONS) archived in `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md`.
- Verdict: R24-1 gate = FAIL accepted with wording condition: "fail under the tested policies and current diagnostic setup" (3 of 4 policies collapsed), NOT a categorical universal negative. q_d/q_D reward paths remain permanently BLOCKED on this evidence line.
- D2 (sensitivity re-run with early stopping): APPROVED-DEFERRED only for archival solidity (NOT confirmatory); conditions: separate validation split, identical stopping rules, report all outcomes, single device class all-GPU, unexpected pass reopens instrument-validity only.
- D3 (pivot to individual-skill differentiation): ACCEPTED pending deconfound; diagnostic design deferred until arm0-vs-arm2 matched-seed deconfound pair results available.
- Date archived: 2026-07-09.

Cloud overnight run completed 2026-07-09 08:34:42 UTC+8. Archive transferred to `dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/`.

**Cloud run structure**:
- Two arms: `qAon` and `qAoff_coef0` (unexpected matched no-q_A control variant)
- Each arm: seed1, seed2
- Total runs: 4
- Each run contains:
  - `r24_qd_null_control_seed{N}/` dir (server-side log root)
  - `r24_qd_windows/` subdir with 10 shards (`.npz` files, one per update at steps 32k, 64k, ..., 320k)
  - `metrics/train_updates.csv` (10 data rows, final: total_steps=320000)
  - `metrics/eval_episodes.csv` (20 data rows, final: episode=19, total_steps=320000)
  - `runner_status.txt`, `runner_output.log`, `standalone_train.log`, event files
  - `frozen_null_command.txt` and `frozen_null_output.log` (server attempted analyzer; failed with ModuleNotFoundError ha_ctse_process)
  - NO `r24_qd_frozen_nulls/` output yet (server-side analyzer failed; local rerun in progress)

**Inventory facts (all 4 runs)**:
- qAon/seed1: shards=10, total_steps=320000, z_usage_entropy=0.9581796625966484, r24_qd_acc_full=0.37506040930747986, coverage_ratio=0.7, zero_throughput_step_fraction=0.494
- qAon/seed2: shards=10, total_steps=320000, z_usage_entropy=0.9740648515987139, r24_qd_acc_full=0.35477069, coverage_ratio=0.0, zero_throughput_step_fraction=1.0
- qAoff_coef0/seed1: shards=10, total_steps=320000, z_usage_entropy=0.9631162846960536, r24_qd_acc_full=0.34242424, coverage_ratio=0.0, zero_throughput_step_fraction=1.0
- qAoff_coef0/seed2: shards=10, total_steps=320000, z_usage_entropy=0.9563014133400384, r24_qd_acc_full=0.31430015, coverage_ratio=0.0, zero_throughput_step_fraction=1.0

**Policy health context**:
- qAon/seed1: reasonable policy (coverage=0.7, 49.4% zero-throughput steps = 50.6% serving)
- qAon/seed2, qAoff_coef0/*: collapsed policies (coverage=0.0, 100% zero-throughput, no service) — likely reward converged to no-action strategy

**Local analyzer execution** (started 2026-07-09 10:56:25 UTC+8):
- Script: `_local_analysis/run_final_batch.py` (direct Python invocation with sys.path setup)
- Configuration: num_skills=6, steps=300, seed=17, hidden_dim=128, lr=3e-3, max_rows=0 (all data)
- Status: Running in background (PID tracked in `runner_status.txt`)
- Expected output per run: `r24_qd_frozen_nulls.json` + `r24_qd_frozen_nulls.md` with all 9 variants
- Log files: `_local_analysis/frozen_null_<arm>_<seed>.log`, `master_progress.log`
- Estimated time: 30-90 minutes total (depends on GPU speed and batch size with 21k+ rows per run)
- Monitor: `tail -f _local_analysis/master_progress.log`

**Next factual read point**:
- When analyzer completes: verify `r24_qd_frozen_nulls.json` + `.md` in each run's output dir
- Extract per-run variant metrics and compare against pre-registered gate criteria
- Verify 9-variant count and accuracy fields (full, prior, behavior, pre, majority) per variant
- Consolidate findings in ExpRecord gate-read section before any reward decision

### EXP-20260707-r23-next-mechanism-matrix

Current read:

- Arm1 q_A probe: positive residual-gain trend, but stopped before full 320k.
- Arm2 q_A reward: completed 40 updates at 16 env; q_A residual gain reached a
  strong mechanism-positive signal. Task read is encouraging but caveated by
  env-count mismatch and single seed.
- Arm3 q_D target/timescale audit: COMPLETED-effectively (38/40 converged, 16env).
  NULL result — every target x horizon collapses to the marginal baseline by u38
  (acc ~0.243, residual_gain ~0.000 for s_next / joint_action / joint_effect /
  delta_omega at H{10,20,50}). No effect space recovers Z above marginal; consistent
  with team_disc-at-chance. CAVEAT: underpowered probe (~1 grad step/update over
  high-dim targets; q_A succeeded on the same budget only because xi is low-dim/direct;
  baseline is context-free marginal, not context-conditioned) -> read as "no signal
  found", NOT "proven absent". Earlier u20 gains (+0.06..0.13) were a transient
  baseline-lag artifact, now gone. Keep q_D reward disabled.

Verdict (R23-next matrix): the g-info -> q_A pivot is VALIDATED. Z->xi actionability
is now learnable (arm1 probe gain 0->+0.097; arm2 reward gain ->+0.222 with forced-Z
KL rising 0.059->0.070, Z-usage healthy) -- decisively fixing the g-info failure
(T2 audit: g-info grad <2% of PPO, self-stalling). The remaining blocker is xi ->
recoverable joint effect: arm3 finds no q_D target/timescale above marginal (underpowered
caveat). Next lever is the individual-skill/discoverer half (does z_i differentiate
low-level behavior -- "Reason B") and/or a stronger q_D probe (more head epochs/update +
context-conditioned baseline), NOT more q_D target engineering. Task: NOISE-DOMINATED at
this depth/seed. cov@160k across arms = arm1 0.063 / arm0 0.10 / arm3 0.192 / arm2 0.303,
and arm3 declined 0.192->0.082 by 320k despite reward-off/probe arms sharing ~identical
policies -> RNG-desync variance. arm2's "3x coverage" is most likely favorable variance,
NOT a real q_A-reward task gain; downgrade it. No reliable task signal without a
matched-env, multi-seed run. The q_A mechanism result (per-arm-internal residual_gain
trend) is independent of this and stands. Firm-up: cloud 64env matched rerun (both seeds).

Operational note:

- Local 32env subproc runs can exceed available RAM. Prefer 16 env locally or a
  cloud 64env package/run.

### EXP-20260709-local-overnight-audit-power-r23-deconfound

Launch-ready overnight sequential runner combining two independent experimental objectives:

**Phase A: R24 Forced-Behavior Audit Power Upgrade (3 audit arms)**
- Upgrade to NResets=64 (4x the prior 16-reset standard)
- Horizon list expanded to {10,20,50,100} (added H=100 for finer timescale resolution)
- Three audit arms, each loading an existing R23 checkpoint and running forced-behavior diagnostics:
  1. `arm1_qA_checkpoint_forced_audit`: checkpoint=`logs_r23_next_mechanism_matrix_local/seed1/arm2_qA_reward_coef002/standalone_process_core_update_40.pt`
  2. `arm2_null_arch_no_qA_forced_audit`: checkpoint=`logs_r23_next_mechanism_matrix_local/seed1/arm0_arch_only/standalone_process_core_final.pt`
  3. `arm3_null_qD_probe_no_qA_forced_audit`: checkpoint=`logs_r23_next_mechanism_matrix_local/seed1/arm3_qD_audit/standalone_process_core_update_40.pt`
- Each arm writes `r24_behavior_audit.csv` to its arm directory under the run root

**Phase B: R23 Arm0 vs Arm2 Matched-Environment Deconfound (4 training arms)**
- Budget: 320000 timesteps (per controller specification, matching cloud eval checkpoint interval)
- Environment configuration: 16 parallel environments (local CUDA capacity limit)
- Seeds 1 and 2, matched per pair (both arm0 and arm2 get the same seed value for each pair)
- Arm order: pair-complete-first `[arm0_seed1, arm2_seed1, arm0_seed2, arm2_seed2]` for overnight survivability
- Four training arms:
  1. `arm4_training_arm0_seed1`: arm0_arch_only, seed=1
  2. `arm5_training_arm2_seed1`: arm2_qA_reward (with q_A residual flags), seed=1
  3. `arm6_training_arm0_seed2`: arm0_arch_only, seed=2
  4. `arm7_training_arm2_seed2`: arm2_qA_reward (with q_A residual flags), seed=2
- Arm0 uses base R23 training flags (no assignment_actionability_reward)
- Arm2 uses base R23 flags + `--enable_assignment_actionability_reward --assignment_actionability_coef 0.02 --assignment_actionability_clip 1.0 --assignment_actionability_warmup_steps 20000`
- No q_D or q_d reward paths enabled; q_A remains reward-off per R23 precedent

**Runner Script & Status Files**
- Script: `scripts/run_r24_overnight_20260709_audit_deconfound_local_cuda.ps1`
- Log root: `logs/r24_overnight_20260709_audit_deconfound/`
- All output under run root: per-arm `command.txt`, `runner_status.txt`, `runner_output.log`
- Dry-run validated: `logs/r24_overnight_20260709_audit_deconfound/dryrun_final.log`
- Checkpoint: `logs/r24_overnight_20260709_audit_deconfound/expmanager_checkpoint.md`

**Controller decision/interpretation (2026-07-09, Phase A read):**
- Phase A result: `gate_read_phaseA.md` found all three audit arms byte-identical
  to the 2026-07-08 overnight audit arms. Root cause is a controller design
  error, not a wiring bug: the 2026-07-08 overnight ALREADY ran `-NResets 64`
  (1920 records), and the audit script is deterministic
  (`reset_seed = seed + reset_idx`, default seed 1), so same checkpoints + same
  NResets + same seed reproduced identical output. The "4x power upgrade"
  premise was wrong; the prior 16-reset run (480 records) was a different,
  earlier standalone audit.
- Additionally, H=100 was never actually passed to the audit script (no h100
  columns exist despite the packaging claim above; the script supports
  `--horizons` but the runner did not use it). The Phase A description above
  overstates what ran.
- Disposition: between_within_ratio_h50 = 0.308 (z) / 0.228 (xi) FAIL stands as
  an already-64-reset estimate; tonight's Phase A adds no information. A true
  power upgrade would need an audit seed sweep (different `--seed` values)
  and/or `--horizons 10,20,50,100`; DEFERRED — not worth GPU time before the
  cloud frozen-null verdict. Phase B (deconfound arms) is unaffected and remains
  the payload of this run.
- New incidental fact: xi_effect_ratio_h50 vs the qD-probe control FAILS (0.937)
  while passing vs arch-only (1.307) — forced-audit evidence remains mixed.

**Estimated Runtime & Constraints**
- Phase A: ~10-15 minutes (audit is lightweight: 3 arms × 64 resets × max 100 steps)
  [ACTUAL: ~2.5h per audit arm; the estimate above was wrong]
- Phase B: ~12-16 hours (4 arms × 320k steps / 16 envs ≈ 3-4 hours per arm on local RTX 4070)
- Total wall time: ~12-16+ hours (suitable for overnight, may exceed one night if stalled)
- GPU constraint: RTX 4070 Laptop (8 GB VRAM) at ~16 envs = ~1.3 GB per arm during training
- Storage: ~500 MB expected per training arm (checkpoints + metrics)

**Checkpoints Verified**
All three source checkpoints exist and are sized 25 MB each:
- qA checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm2_qA_reward_coef002/standalone_process_core_update_40.pt` (created 2026-07-07 12:01)
- null-arch checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm0_arch_only/standalone_process_core_final.pt` (created 2026-07-07 03:28)
- null-qD checkpoint: `logs_r23_next_mechanism_matrix_local/seed1/arm3_qD_audit/standalone_process_core_update_40.pt` (created 2026-07-07 14:32)

**Launch Command**
```powershell
powershell -NoProfile -File scripts/run_r24_overnight_20260709_audit_deconfound_local_cuda.ps1
```

Optional arguments:
- `-DryRun`: Print all 7 arm commands without executing
- `-Python "C:\Users\wu\.conda\envs\SB3\python.exe"`: Specify Python executable (default: C:\Users\wu\.conda\envs\SB3\python.exe)
- `-RunRoot "logs/r24_overnight_20260709_audit_deconfound"`: Specify run root (default: logs/r24_overnight_20260709_audit_deconfound)
- `-ContinueOnError`: Continue to next arm if one fails (default: stop on first error)

## Archive Pointers

- Full pre-compaction experiment record:
  `memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`
- LongTimeMemoryManager-owned detailed experiment archive:
  `memory/LTM/EXPERIMENT_ARCHIVE.md`
