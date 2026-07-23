# Scale-by-churn composition G10 prelaunch acceptance

Date: 2026-07-23

## Accepted evidence

```text
focused_tests=6_passed
combined_g10_g5_tests=11_passed
backend=cpu
torch=2.7.0+cpu
torch_threads=1
nonformal_run=logs/nonformal_scale_churn_g10_20260723_pm2
nonformal_branch=NONFORMAL_SCALE_CHURN_G10_EXERCISE_COMPLETE
nonformal_operational_valid=true
nonformal_optimizer_steps=0
nonformal_checkpoint_copy_maximum_difference=0.0
nonformal_evaluation_cells=6
nonformal_model_state_unchanged_exact=true
```

All three constructive controllers reached utility one. Exact count schedules,
post-event wave requirements, eight-event inventories and lifecycle-state
checks passed for capacities 32 and 48. The nonformal metrics are diagnostic
only and do not consume an iteration.

The first fresh run root ending in `pm1` failed before artifact creation because
the thin command-line runner had not inserted the project root before its first
package import. Commit `5d97128bd034575885c43274ac4d65ae7473754f`
adds only that execution-path repair; direct CLI invocation and all six focused
tests pass. The accepted `pm2` run is a fresh operational recovery with no
scientific field changed.

## Protected-semantics audit

G10 reuses the exact G8 checkpoints and G9 lifecycle/evaluation core. Only the
registered count/churn profiles, G10 identity, seeds and result labels are new.
Reward, observations, policy representation, action factorization, lifecycle
ownership, wave process, RNG construction, thresholds, bootstrap and
first-match precedence remain frozen.

## Formal boundary

After integrating this note, resolve the resulting full commit as
`<SOURCE_COMMIT>` and select one fresh `<RUN_ROOT>`. The fixed Luna-low operator
runs:

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_scale_churn_g10.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_SCALE_CHURN_COMPOSITION_G10_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 128
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_scale_churn_g10.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_scale_churn_g10.py analyze --run-root <RUN_ROOT>
```

Restart and resume are forbidden. A valid analysis consumes iteration 11;
operational invalidity consumes none.
