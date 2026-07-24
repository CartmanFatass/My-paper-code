# Codex restart handoff

Date: 2026-07-23

Reason: user-requested Codex update

## Safe terminal state

The Project Manager stopped the formal experiment operator and the read-only G2
scout. It then explicitly terminated the exact formal process tree: one parent
and sixteen `hmasd-amd-cpu` Python workers started at 22:28 local time. A final
process check found no Python process.

Git-tracked G1 implementation and prelaunch evidence were already accepted,
committed and pushed before the pause:

```text
formal_source_commit=b125efd205e302666aea78b286d6857f8ecf9286
branch=aggressive
local_and_remote_matched=true
implementation_review=ACCEPT
focused_tests=38_passed_plus_1_final_delta_passed
nonformal_run=logs/nonformal_uav_temp_loss_g1_20260723_pm2
nonformal_result=NONFORMAL_UAV_TEMP_LOSS_G1_EXERCISE_COMPLETE
```

The later handoff commit changes only active project-control documentation. It
does not replace the frozen formal source identity above.

## Interrupted formal run

```text
iteration=18
run_root=logs/formal_uav_temp_loss_g1_cpu_20260723_b125efd_r1
formal=true
backend=cpu
torch_threads=1
authorization_token=AUTHORIZE_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_CPU_V1
conclusion_bearing_iteration_consumed=false
scientific_result=none
```

The run root contains only:

- `launch_identity.json`
- `source_screen_launch_identity.json`

There is no completed control-batch journal, train manifest, evaluation
manifest or analysis result. No conclusion was available or interpreted. The
existing identity files are valid and the same train command may safely resume;
because zero batches completed, it will begin the first exact control batch.

## Exact restart action

After the user returns from the Codex update and asks to continue, read
`AGENTS.md`, `docs/project/CURRENT_WORK.md`, this handoff and the G1 design.
Then spawn exactly one registered `hmasd-experiment-operator` with the same
source, root, CPU/thread contract, token and commands below. Do not create a
Controller or monitor session and do not delete the existing run root.

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts\run_uav_temp_loss_g1.py train --run-root 'logs\formal_uav_temp_loss_g1_cpu_20260723_b125efd_r1' --source-commit b125efd205e302666aea78b286d6857f8ecf9286 --formal --authorization-token AUTHORIZE_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_CPU_V1

& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts\run_uav_temp_loss_g1.py evaluate --run-root 'logs\formal_uav_temp_loss_g1_cpu_20260723_b125efd_r1'

& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' scripts\run_uav_temp_loss_g1.py analyze --run-root 'logs\formal_uav_temp_loss_g1_cpu_20260723_b125efd_r1'
```

The operator remains silent and returns once at `COMPLETE` or `ERROR`. The
train phase first runs exact source-identifiability controls. If they fail, it
performs zero learned training and returns the registered branch 2 after
evaluation/analyze; if they pass, it continues the frozen learned budget.

## Iteration and successor state

Ten conclusion-bearing UAV iterations remain (`ITERATION_18` through
`ITERATION_27`). `docs/report/ITERATION_18.md` does not exist and must be written
only after a valid formal result. The read-only G2 charging scout was stopped
before returning a report; restart it only if useful after the formal operator
is safely resumed. No G2 file or scientific choice was created.
