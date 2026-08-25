# Atomic count-shock G15 prelaunch acceptance

Date: 2026-07-23

## Implementation acceptance

- `open_roster_atomic_count_shock_g15.py` deterministically generates six
  alternating low/high atomic transactions per episode. Both operation cohorts
  are positive and strictly unequal; terminal keys never reactivate and joined
  keys are always fresh.
- `run_open_roster_atomic_count_shock_g15.py` freezes the G15 identity, budget,
  seeds, gates and first-match branches while reusing the accepted G9--G14
  evidence core.
- The focused suite passes 6/6. The G15 plus foundational G5 suite passes
  11/11 on the registered CPU interpreter with one thread.
- The bounded nonformal pipeline at
  `logs/nonformal_atomic_count_shock_g15_20260723_pm1` completes with 12 unique
  source profiles, 72/72 positive unequal transactions, exact roster schedules,
  constructive utility one, lifecycle closure, six evaluation cells, zero
  optimizer steps, exact checkpoint copy and 6/6 immutable model states.
- A forged formal flag and a roster-schedule tamper both fail closed.

The previous G14 executable line and its focused tests are removed under the
active-line policy. Its design, formal artifacts, result note, Chinese report
and Git history remain the durable evidence.

No advisory review is selected: the only new behavior is a deterministic ledger
generator over the already accepted shared lifecycle/source-control path, and
the reproducer, tamper negative, focused suite and full-path exercise leave no
anomaly.

## Formal launch boundary

```text
algorithm=ATOMIC_COUNT_SHOCK_G15
authorization_token=AUTHORIZE_ATOMIC_COUNT_SHOCK_G15_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
eval_episodes=24
optimizer_steps=0
source_control_rows=72
evaluation_cells=18
utility_values=432
```

After integration, use a fresh run root and replace `<SOURCE_COMMIT>` exactly:

```powershell
$env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_atomic_count_shock_g15.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_ATOMIC_COUNT_SHOCK_G15_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 24
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_atomic_count_shock_g15.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_atomic_count_shock_g15.py analyze --run-root <RUN_ROOT>
```

The formal run consumes iteration 16 only if analyzer evidence is operationally
valid. One conclusion-bearing iteration remains after a valid result.
