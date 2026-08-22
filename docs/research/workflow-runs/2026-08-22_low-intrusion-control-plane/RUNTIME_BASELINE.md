# Runtime Baseline Record

## Scope and authority

Task 10 replaced the calibration placeholder with measured, non-formal
engineering evidence under lease `shared:context-foundation`, activity
`task10-runtime-calibration`. The lease was CPU-only, authorized up to four
workers, and carried an additional working-set fence of `<=8 GiB`. CM selected
two workers with one thread per worker for the bounded parallel sample. This
selection is neither a global/project worker default nor scientific or
portfolio evidence.

No formal training was launched. The learner sample is explicitly
non-result-bearing. These measurements characterize only the named Task 10
routes and host observation window.

## Host readings and resource preflight

CM recorded three system-total readings within 13 seconds before the wrapper
preflight:

| Captured at (UTC) | System CPU load | Available memory |
|---|---:|---:|
| `2026-08-22T18:56:10.9177747Z` | 22% | 6.4917 GiB |
| `2026-08-22T18:56:17.2630348Z` | 10% | 6.4929 GiB |
| `2026-08-22T18:56:23.5633911Z` | 8% | 6.8858 GiB |

The host reported 8 physical cores, 16 logical processors, and 29.7861 GiB
total visible memory. The wrapper snapshot is
`runtime/RESOURCE_PREFLIGHT.json`, preflight ID
`resource_1a595382366b4023b181e9ddfb84f38c`, captured at
`2026-08-22T18:59:58.6688874Z`. It observed 9% system CPU load and 6.7934 GiB
available memory and recorded route `continuous_roster_native`, backend `cpp`,
two workers, one thread per worker, and `parallel=true`.

The actual wrapper parameter is `-OutFile`; the plan's illustrative
`-OutPath` spelling is not accepted by this wrapper. The command used was:

```powershell
powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-resource-preflight.ps1 `
  -AssignmentId asg_context_runtime_calibration `
  -RouteId continuous_roster_native `
  -Backend cpp `
  -SelectedWorkerCount 2 `
  -SelectionRationale "Host preflight: 8 physical/16 logical CPUs, three system-total CPU readings 22/10/8 percent and 6.49-6.89 GiB available; two-worker bounded Task 10 calibration only within <=8 GiB lease; not a project default." `
  -CmOwner "CM:shared:context-foundation" `
  -ThreadsPerWorker 1 `
  -Parallel `
  -OutFile docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/RESOURCE_PREFLIGHT.json
```

## Measurement commands

Each command produced one exclusive JSON output. The commands below are the
commands recorded in the final samples:

```powershell
C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe .tmp_task10_calibration/task10_measure.py toy-env --out .tmp_task10_calibration/TOY_ENV_SAMPLE.json

C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe .tmp_task10_calibration/task10_measure.py learner-update --source-commit 3b2bc2a694693b084e0a126367a1894fa3ca3013 --out .tmp_task10_calibration/LEARNER_UPDATE_SAMPLE.json

C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe .tmp_task10_calibration/task10_measure.py cpp-parallel --out .tmp_task10_calibration/CPP_PARALLEL_SAMPLE.json

C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe .tmp_task10_calibration/task10_measure.py python-reference --out .tmp_task10_calibration/PYTHON_REFERENCE_SAMPLE.json
```

The final samples were promoted byte-for-byte to
`docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/`.

## Measured samples

`target_steps` equals the measured `environment_steps` in every row. The
throughput values below are the plausibility tool's measured
environment-steps-per-second values; none is extrapolated.

| Artifact | Warmup env steps | Measured env steps | Optimizer updates | Evaluations | Measured wall seconds | Backend | Workers x threads | Parallel | Result-bearing | Runtime profile | Throughput (env steps/s) | Assessment |
|---|---:|---:|---:|---:|---:|---|---:|---|---|---|---:|---|
| `runtime/TOY_ENV_SAMPLE.json` | 384 | 768 | 0 | 0 | 0.018435200094245374 | `cpp` | 1 x 1 | false | false | `TOY_SMOKE` | 41659.433913 | `PLAUSIBLE` |
| `runtime/LEARNER_UPDATE_SAMPLE.json` | 192 | 576 | 9 | 0 | 3.6362880000378937 | `python_torch_cpu` | 1 x 1 | false | false | `TOY_EXPLORATORY` | 158.403295 | `PLAUSIBLE` |
| `runtime/CPP_PARALLEL_SAMPLE.json` | 768 | 1536 | 0 | 0 | 0.030842300038784742 | `cpp` | 2 x 1 | true | true | `TOY_EXPLORATORY` | 49801.733271 | `PLAUSIBLE` |
| `runtime/PYTHON_REFERENCE_SAMPLE.json` | 384 | 768 | 0 | 0 | 0.042542300070635974 | `python_reference` | 1 x 1 | false | false | `REFERENCE_ORACLE` | 18052.620538 | `PLAUSIBLE` |

The learner/update sample used integrated source commit
`3b2bc2a694693b084e0a126367a1894fa3ca3013`. Its three measured independent
non-formal train calls each accounted for 192 environment steps and three
optimizer steps: one fast optimizer step plus one direction actor and one
direction critic step. It ran no evaluations.

The actual two-process C++ parallel sample used worker PIDs `24244` and
`28956`. Their measured worker-local elapsed times were
`0.029708900023251772` and `0.025415599928237498` seconds, respectively. Both
workers completed, agreed on the exact outcome, and independently confirmed
native/Python oracle equivalence before the coordinated barrier release. The
measured route had no serial or Python environment fallback; Python performed
spawn, synchronization, and lifecycle orchestration only.

The toy native, two-worker native, and Python reference routes shared exact
outcome digest
`8dc6ee0695ea1b4d660b92064a41e3679b4b3bc2a6b1023e8386329e08b2290a`.
The native extension used flags `/O2`, `/std:c++17`, `/EHsc`, and
`/fp:precise`. Cold build/load and fixture or batch construction were excluded
from the steady measured native regions. The steady native wall values must
therefore not be read as complete process startup durations.

Where independently retained, outer command wall observations were 2.1177
seconds for the Python reference command, approximately 6.95 seconds for the
spawned C++ parallel command, and 10.7933543 seconds for the learner command.
These outer observations include lifecycle/startup work and are context, not
the `wall_seconds` inputs to plausibility assessment. No separate outer wall
observation was retained for the single-worker toy command.

## Plausibility assessment

The actual wrapper parameter is `-InputJson`; the plan's illustrative `-Path`
spelling is not accepted. The four commands were:

```powershell
powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-runtime-plausibility.ps1 -InputJson docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/TOY_ENV_SAMPLE.json

powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-runtime-plausibility.ps1 -InputJson docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/LEARNER_UPDATE_SAMPLE.json

powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-runtime-plausibility.ps1 -InputJson docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/CPP_PARALLEL_SAMPLE.json

powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-runtime-plausibility.ps1 -InputJson docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/PYTHON_REFERENCE_SAMPLE.json
```

All four commands exited 0 and returned `PLAUSIBLE`, incident level
`E0_OBSERVATION`, route `CURRENT_EXECUTOR`, and
`user_authority_required=false`. Because every sample has basis `MEASURED` and
`target_steps == environment_steps`, no extrapolation was used. The samples
show no concrete false classification, so no runtime threshold was modified.

## Artifact integrity

| Artifact | SHA-256 |
|---|---|
| `runtime/RESOURCE_PREFLIGHT.json` | `C571B54F481B2E70D254C1BC6FA3F22F33BC8354C3603E0F9E52CDD8C88383F3` |
| `runtime/TOY_ENV_SAMPLE.json` | `F8A948C0A494E79BDFB04F90F715B79EDD28496B4AF865C21B7A47580A832438` |
| `runtime/LEARNER_UPDATE_SAMPLE.json` | `FAF70A496AF0DAF68D166D8C6612386F14C2536AFE24FBB16B167C64837C0CB8` |
| `runtime/CPP_PARALLEL_SAMPLE.json` | `0F20F10E76044F5DA0CFC7533BE7396DBF3AE42121C3A4E382D3D63A2F708104` |
| `runtime/PYTHON_REFERENCE_SAMPLE.json` | `FA832E0DFF04ADCC90E3937941E664A230CD168D8ABCD710C011D37347248694` |

## Limitations and policy disposition

This is non-formal calibration only and supports no scientific or portfolio
inference. The learner route is not result-bearing. The two-worker observation
does not establish a global worker count, thread count, backend, or project
default.

Peak additional RSS was not independently sampled during the measurement
commands, so this record makes no measured peak-RSS claim. It records only the
system-total preflight observations and the lease/operator `<=8 GiB`
additional-working-set fence. The measured native steady regions exclude
startup, build/load, fixture construction, and oracle execution.

All assessments were plausible and exposed no threshold false classification.
Accordingly, `docs/project/EXPERIMENT_EXECUTION_POLICY.md` remains unchanged.
