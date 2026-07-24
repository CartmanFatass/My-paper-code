# Ultra-scale open-roster G12 prelaunch acceptance

Date: 2026-07-23

## Accepted implementation

- `ha_ctse_process/open_roster_ultra_scale_g12.py` defines the exact N=48, 64
  and 80 eight-edit profiles.
- `scripts/run_open_roster_ultra_scale_g12.py` binds those profiles to the
  frozen-G8 import/evaluate/analyze core.
- `tests/ha_ctse_process_open_roster_ultra_scale_g12_test.py` covers transition
  and constructive controls, lifecycle state, frozen representation, formal
  authorization/counts, first-match boundaries, nonformal rejection and source
  tampering.
- Closed G10/G11 executable paths are removed from the active line; their Git
  commits and evidence artifacts remain the archive.

The focused suite passes 5/5 and the G12 plus shared G5 suite passes 10/10 on
the registered CPU interpreter with one thread.

## Bounded nonformal full path

`logs/nonformal_ultra_scale_g12_20260723_pm1` completed train-import, evaluate
and analyze:

```text
formal=false
branch=NONFORMAL_ULTRA_SCALE_G12_EXERCISE_COMPLETE
operational_valid=true
replicates=1
evaluation_cells=6
utility_values=24
optimizer_steps=0
source_model_copy_maximum_difference=0.0
all_model_state_unchanged_exact=true
all_constructive_utility_one=true
all_roster_schedules_exact=true
all_actual_wave_requirements_exact=true
all_event_counts_exact=true
all_lifecycle_states_exact=true
```

Nonformal utility values are execution diagnostics only and do not support a
scientific branch. No anomaly triggered advisory review.

## Exact formal launch

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_ultra_scale_g12.py train --run-root <RUN_ROOT> --source-commit <SOURCE_COMMIT> --formal --authorization-token AUTHORIZE_ULTRA_SCALE_OPEN_ROSTER_G12_FORMAL_CPU_V1 --g8-run-root logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1 --replicates 3 --eval-episodes 64
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_ultra_scale_g12.py evaluate --run-root <RUN_ROOT>
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts/run_open_roster_ultra_scale_g12.py analyze --run-root <RUN_ROOT>
```

The run must use a fresh root and the fixed registered experiment operator. No
restart, resume, backend change or parameter substitution is authorized. A
valid analysis consumes iteration 13 and leaves four iterations.
