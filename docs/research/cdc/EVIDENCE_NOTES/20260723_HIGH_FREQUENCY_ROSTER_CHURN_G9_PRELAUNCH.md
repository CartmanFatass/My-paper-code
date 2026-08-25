# High-frequency roster churn G9 prelaunch acceptance

Date: 2026-07-23

## Accepted implementation evidence

The active G9 line replaces the completed G8-specific stress files while
retaining the shared prefix-normalized policy. It imports the exact three G8
update-250 final checkpoints and performs zero optimizer steps.

```text
focused_tests=6_passed
combined_g9_g5_tests=11_passed
backend=cpu
torch=2.7.0+cpu
torch_threads=1
nonformal_run=logs/nonformal_high_frequency_churn_g9_20260723_pm2
nonformal_branch=NONFORMAL_HIGH_FREQUENCY_CHURN_G9_EXERCISE_COMPLETE
nonformal_operational_valid=true
nonformal_optimizer_steps=0
nonformal_checkpoint_copy_maximum_difference=0.0
nonformal_evaluation_cells=6
nonformal_model_state_unchanged_exact=true
```

All three constructive controllers reached utility one. The serialized roster
schedules, actual-wave requirements, eight-edit counts and lifecycle-state
checks were exact. The exercise covered deterministic and stochastic cells for
`repeated_rejoin`, `load_proximal` and `mixed_churn`; its metrics are diagnostic
only and are not a conclusion-bearing result.

An earlier fresh run root ending in `pm1` timed out in the operator tool after
about 1.3 seconds before creating any artifact. No process remained. The
accepted `pm2` exercise used the same committed source and exact scientific
arguments with an explicit foreground tool timeout. This was an orchestration
repair, not an experiment retry or semantic change.

## Protected semantics audit

G9 changes only the membership schedule used for evaluation. It does not alter
G8 checkpoints, policy parameters, active-sum/log-count/prefix-fraction
representation, reward, observations, primitive actions, waves, horizon,
lifecycle ownership, RNG tables, thresholds, bootstrap or result precedence.
The formal analyzer rejects nonformal artifacts and fails closed on source,
profile, schedule, lifecycle, model-state or cell-inventory tampering.

## Exact formal boundary

After integrating this acceptance note, resolve the resulting full Git commit
as `<SOURCE_COMMIT>` and choose one fresh `<RUN_ROOT>`. Assign the fixed
Luna-low operator these exact foreground commands:

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_high_churn_g9.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_HIGH_FREQUENCY_ROSTER_CHURN_G9_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 128
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_high_churn_g9.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_high_churn_g9.py analyze --run-root <RUN_ROOT>
```

Restart and resume are forbidden. A valid formal analysis consumes iteration
10; operationally invalid evidence consumes none.
