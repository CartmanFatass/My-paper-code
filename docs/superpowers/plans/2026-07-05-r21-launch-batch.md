# R21 Cloud Launch Batch Plan

Date: 2026-07-05

Scope: launch the R21 team-intent restoration experiments directly on cloud
compute, and launch the HMASD current-environment baseline with the same
S7-S1 / 6-agent evaluation target.

## Accepted Decisions

- No local R21 structural probe for this batch. The user will run R21 directly
  on cloud.
- R21 matched control is the completed 64-env coef005 continuation run
  (`dist/logs_cloud_r16_5_continuation_64env`): prototype response reward
  coefficient 0.05, duration entropy floor inactive.
- R21 launch defaults are amended by the 2026-07-05 pre-launch review:
  `team_intent_k=48`, `team_disc_coef=0.05`, Z entropy floor available but
  default-off, and Z-boundary truncation logged per duration bucket.
- HMASD baseline must be 6-agent. `train_multiproc_config_1.py` now accepts
  `--n_agents 6` for the baseline path and logs HA-CTSE parity eval metrics.

## Task 1: R21 Cloud Run

Runner:

```bash
bash scripts/run_r21_team_intent_cloud_64env.sh --dry-run
EXPERIMENTS=r21_z_probe,r21_z_reward SEEDS=1 TOTAL_TIMESTEPS=960000 NUM_ENVS=64 DEVICE=cuda bash scripts/run_r21_team_intent_cloud_64env.sh
```

Primary read points:

- 160k: `team_disc_acc` trajectory shape, `z_usage_entropy`,
  `z_boundary_trunc_rate_*`, reward-ratio guard.
- 320k: mechanism gate versus coef005 matched control.
- 960k: task gate versus coef005 matched control.

Stop / fault routing:

- `z_boundary_trunc_rate_dur13` or `dur24` high: K/lifetime interaction still
  present, do not interpret duration collapse as learned preference.
- `team_disc_acc` instant saturation near 1.0: audit discriminator input for
  Z leakage before reading reward.
- flat `team_disc_acc` near prior: Z does not induce distinguishable next-state
  distribution; inspect K_team/sample count before coefficient changes.

## Task 2: HMASD Current-Environment Baseline

Runner:

```bash
bash scripts/run_hmasd_currentenv_baseline_cloud_64env.sh --dry-run
SEEDS=1,2 TOTAL_TIMESTEPS=1000000 NUM_ENVS=64 DEVICE=cuda bash scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
```

Readout must include:

- `coverage_eq1_step_fraction`
- `coverage_eq1_episode_fraction`
- `zero_throughput_episode_fraction`
- `throughput_gt5_step_fraction`

This is a logging-only baseline support change. Do not edit HMASD learning
logic for this baseline.

## Bookkeeping

- Update `memory/ExpRecord.md` before launch with command and cloud location.
- Record first eval proof line in `memory/ExpRecord.md`.
- Record all external-review responses in `memory/cross_validation.md` with
  reviewer/source metadata.

