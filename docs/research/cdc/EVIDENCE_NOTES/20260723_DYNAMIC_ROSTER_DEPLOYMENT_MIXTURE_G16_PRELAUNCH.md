# Dynamic-roster deployment mixture G16 prelaunch acceptance

Date: 2026-07-23

## Implementation acceptance

- `open_roster_deployment_mixture_g16.py` builds a deterministic balanced
  episode mixture of fresh-seed serial-random, equal-atomic and shock-atomic
  profiles at three scales.
- The shared evidence core now accepts the exact active event-count set
  `{6,12}`; profile reconstruction still fails closed on every signature,
  schedule, source and lifecycle mismatch.
- `run_open_roster_deployment_mixture_g16.py` freezes the final identity,
  1:1:1 formal mode balance, new seeds, budget, gates and first-match branches.
- The focused suite passes 6/6. The G16 plus foundational G5 suite passes 11/11
  on the registered CPU interpreter with one thread.
- The bounded nonformal pipeline at
  `logs/nonformal_deployment_mixture_g16_20260723_pm1` completes with 12 unique
  source profiles, exactly four of each mode, event counts `{6,12}`, all four
  membership operation types, exact schedules and wave demand, constructive
  utility one, lifecycle closure, six cells, zero optimizer steps, exact
  checkpoint copy and 6/6 immutable model states.
- A forged formal flag and an event-count tamper both fail closed.

The G15 runner and focused test exit the active code line; its generator remains
because G16 directly composes the accepted atomic-shock implementation. G15
formal evidence, design, report and Git history remain unchanged.

No advisory review is selected because the mixture composes accepted process
generators, the sole shared-core change has a focused positive and tamper
negative, and no anomaly remains.

## Formal launch boundary

```text
algorithm=DYNAMIC_ROSTER_DEPLOYMENT_MIXTURE_G16
authorization_token=AUTHORIZE_DYNAMIC_ROSTER_DEPLOYMENT_MIXTURE_G16_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
eval_episodes=36
profiles_per_mode_per_domain=12
optimizer_steps=0
source_control_rows=108
evaluation_cells=18
utility_values=648
```

After integration, use a fresh run root and replace `<SOURCE_COMMIT>` exactly:

```powershell
$env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_deployment_mixture_g16.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_DYNAMIC_ROSTER_DEPLOYMENT_MIXTURE_G16_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 36
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_deployment_mixture_g16.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_deployment_mixture_g16.py analyze --run-root <RUN_ROOT>
```

The run consumes iteration 17 only when analyzer evidence is operationally
valid. It is the terminal conclusion-bearing iteration of the current grant.
