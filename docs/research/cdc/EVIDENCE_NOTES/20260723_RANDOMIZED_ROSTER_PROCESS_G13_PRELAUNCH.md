# Randomized roster-process G13 prelaunch acceptance

Date: 2026-07-23

## Accepted implementation

- `open_roster_random_process_g13.py` owns deterministic episode-random profile
  generation and its three bounded distributions.
- the shared frozen-checkpoint core now validates every episode's event
  signature and constructive source controls, with no compatibility reader;
- `run_open_roster_random_process_g13.py` freezes the G13 formal identity,
  seeds, budgets, thresholds and first-match order;
- the focused test covers generator determinism/diversity, count bounds, four
  event types, constructive solvability, lifecycle state, frozen G8 semantics,
  formal rejection, tamper rejection and threshold boundaries.

The focused suite passes 6/6 and the G13 plus shared G5 suite passes 11/11 on
the registered CPU interpreter with one thread. The initial source probe failed
only because its unrestricted removal times could intersect an active wave.
The repaired safe-window source passes all checks; no result gate changed.

## Bounded nonformal full path

`logs/nonformal_random_roster_g13_20260723_pm1` completes with:

```text
formal=false
branch=NONFORMAL_RANDOMIZED_ROSTER_G13_EXERCISE_COMPLETE
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

Nonformal utilities are execution diagnostics only. No protected-semantics
anomaly or review trigger remains.

## Exact formal launch

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_random_process_g13.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_RANDOMIZED_ROSTER_PROCESS_G13_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 48
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_random_process_g13.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_random_process_g13.py analyze --run-root <RUN_ROOT>
```

Use a fresh run root and the fixed experiment operator. No restart, resume,
backend change or parameter substitution is authorized. A valid result consumes
iteration 14 and leaves three iterations.
