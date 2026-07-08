# HA-CTSE Experiment Dashboard

Updated: 2026-07-07

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
`invalid`, `superseded`, `blocked`.

## Current Dashboard

| ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-20260708-r24-qd-null-control-cloud-handoff | launch-ready | R24 | cloud CUDA / 64env package | ExpManager + controller | run 320k reward-off q_d null-control seeds 1 and 2; read new null-control fields before any q_d/q_D reward decision | `dist/ha_ctse_r24_qd_null_control_cloud_runtime_20260708_190315.zip`; `scripts/run_r24_qd_null_control_cloud_64env.sh`; default log root `logs_cloud_r24_qd_null_control_64env` | Completes the unfinished post-update q_d diagnostic. Local seed1 stopped at 152k via unrelated ratio guard; seed2 stopped at 256k. Cloud runner uses `GUARD_MODE=warn`, CUDA, 64 env, `total_timesteps=320000`, q_A actionability reward on, q_d/q_D reward off. |
| EXP-20260707-r24-assignment-to-behavior-bridge | completed / blocked | R24 | local CUDA diagnostics | ExpManager | run matched-null forced-audit controls A-D, then reward-off behavior-window q_d probe; set `q_D/q_d` reward decision only after gate pass | `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/r24_forced_behavior_audit.py`; `logs_r24_qd_probe_local_cuda/seed1`; `logs_r24_behavior_audit_local/r24_behavior_audit.csv`; `logs_r24_behavior_audit_smoke/r24_behavior_audit.csv` | forced-audit signal is positive but insufficient for reward gating. q_d probe is near-null (`residual_gain=0.01105`, `positive_frac=0.52855`) and cannot justify reward-on. `q_D` and `q_d` rewards remain blocked pending matched-null controls + behavior-window `q_d` gate pass (`effect_ratio_h50>=1.3` + `h50-h10` growth + `between_within_ratio_h50>1.2`). |
| EXP-20260707-r24-assignment-to-behavior-bridge-overnight | completed | R24 | local CUDA / `logs_r24_overnight_existing_local_cuda/run_20260708_000836` | ExpManager | checked arm-level `runner_status.txt`, `runner_output.log`, audit/train tails, and `_watch/watch_state.json` | `scripts/run_r24_overnight_existing_local_cuda.ps1`; `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/run_r24_qd_probe_local_cuda.ps1`; `scripts/watch_r24_overnight_existing.ps1`; `scripts/codex_r24_alert_handler.ps1`; `logs_r24_overnight_existing_local_cuda/run_20260708_000836/arm*` | one-click local overnight runner completed with `NResets=64`, `NumEnvs=16`; all five arms finished with `exit_code=0`. |
| EXP-20260707-r23-next-mechanism-matrix | completed / mixed (local 16env, single seed) | R23-next | local CUDA; cloud candidate | ExpManager | optional cloud 64env rerun for a matched-env task read + q_D-probe upgrade | `logs_r23_next_mechanism_matrix_local`, `scripts/run_r23_next_mechanism_matrix_local_cuda.ps1`, `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh` | q_A actionability VALIDATED (Z->xi learnable: arm2 residual_gain +0.222, forced-Z KL 0.059->0.070). q_D target audit NULL across all targets/H (underpowered caveat) -> xi->recoverable-joint-effect still unestablished. Task encouraging @160k (cov 0.303 ~3x control) but confounded. Next lever = individual-skill/discoverer half + stronger q_D probe, NOT more q_D targets. Local 32env OOMs (31.6GB box); use 16env locally or 64env cloud. |
| EXP-20260706-r23-actionable-team-intent | completed / mixed | R23 | cloud CUDA seed1 | ExpManager | none unless comparing to R23-next | `dist/logs_cloud_r23_actionable_team_intent_64env` | Architecture capacity passed; g-info objective and q_D target failed/null. This motivates q_A residual and q_D target audit. |
| EXP-20260705-r21-team-intent | completed / negative | R21 | cloud CUDA seed1 | ExpManager | none | `dist/logs_cloud_r21_team_intent_64env`, `memory/R21_AUTOPSY_REPORT.md` | Z was near-inert; sampled team code did not create recoverable team effect. No seed2 or sweep on this design. |

## Active Experiment Detail

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

## Archive Pointers

- Full pre-compaction experiment record:
  `memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`
- LongTimeMemoryManager-owned detailed experiment archive:
  `memory/LTM/EXPERIMENT_ARCHIVE.md`
