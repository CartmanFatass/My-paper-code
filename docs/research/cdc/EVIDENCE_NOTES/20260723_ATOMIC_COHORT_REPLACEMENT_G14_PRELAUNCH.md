# Atomic cohort-replacement G14 prelaunch acceptance

Date: 2026-07-23

## Accepted implementation

- `open_roster_atomic_replacement_g14.py` generates exact count-preserving
  atomic terminal/join processes for three scales;
- the active evaluator accepts a source-specific required event-operation set
  while retaining exact per-episode signature validation;
- `run_open_roster_atomic_replacement_g14.py` freezes the formal identity,
  source seeds, budget, thresholds and first-match order;
- the focused test proves deterministic diversity, atomic equal-size edits,
  constant N, constructive utility, lifecycle cold start/terminal behavior,
  G8 immutability, formal rejection, tamper rejection and threshold boundaries.

The focused suite passes 6/6 and the G14 plus shared G5 suite passes 11/11 on
the registered CPU interpreter with one thread.

## Bounded nonformal full path

`logs/nonformal_atomic_replacement_g14_20260723_pm1` completes with:

```text
formal=false
branch=NONFORMAL_ATOMIC_REPLACEMENT_G14_EXERCISE_COMPLETE
operational_valid=true
replicates=1
evaluation_cells=6
utility_values=24
source_control_rows=12
optimizer_steps=0
source_model_copy_maximum_difference=0.0
all_model_state_unchanged_exact=true
all_profile_names_unique=true
all_event_operation_types_present=true
all_constructive_utility_one=true
all_roster_schedules_exact=true
all_actual_wave_requirements_exact=true
all_event_counts_exact=true
all_lifecycle_states_exact=true
```

Nonformal utilities are execution diagnostics only. No review-triggering
anomaly remains.

## Exact formal launch

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_atomic_replacement_g14.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_ATOMIC_COHORT_REPLACEMENT_G14_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 32
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_atomic_replacement_g14.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_atomic_replacement_g14.py analyze --run-root <RUN_ROOT>
```

Use a fresh run root and the fixed experiment operator. No restart, resume,
backend change or parameter substitution is authorized. A valid result consumes
iteration 15 and leaves two iterations.
