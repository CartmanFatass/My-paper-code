# FSD E3 heterogeneous-hazard detached run state

Snapshot: `2026-09-04T12:06:57Z`

This is an operational recoverability snapshot for the frozen B/EXPLORE object
`FSD-E3-HET-R01`. It records runtime facts only. It is not a result, an intake, a scientific
polarity, a queue implementation, or authority to bypass a fresh resource admission.

## Frozen and accepted boundary

- Science card:
  `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`
- Card blob: `2939b751f3cf5ed22b1c9b59d3620d9107955036`
- Launch implementation SHA: `e6108e466eeea3df31db52c53e49eef828bde41a`
- Later state-only commit `5b84d8b072abda9650403b7fef7303a85205c48c` changes neither the
  runner nor its focused test bytes relative to the launch implementation SHA.
- Runner: `scripts/run_flexible_skill_duration_e3.py`
- Pre-launch focused suite on the launch SHA: `12 passed in 10.83s`
- Study root:
  `temp/directions/flexible_skill_duration/exp/E3_20260904`
- All 18 row/arm/seed invocations are card-accepted. Each still requires its own immediately
  preceding `admit-memory` receipt with at least 4 GiB physical and effective availability.
- Frozen projections per invocation: D0 small `1.16 h`; D0 medium/large `1.68 h`; D2 conservative
  mechanical maximum `4.63 h`; all are below the `8 h` per-arm cap.
- Current counts at this snapshot: card-accepted `18`; independently admitted/launched `6`;
  running `3`; valid complete `3`; quarantined `0`; not created/admitted `12`.

## Detached processes at the snapshot

| invocation | PID | receipt assessed UTC | physical/effective available bytes | progress | stderr | terminal artifact |
| --- | ---: | --- | ---: | --- | ---: | --- |
| `small_d2_seed2` | `24664` | `2026-09-04T11:43:50.271300Z` | `9409052672 / 9409052672` | `4/20` rollouts, `0/4` evals | `0 B` | none; process alive |
| `small_d0_seed3` | `6744` | `2026-09-04T11:45:29.417212Z` | `9487990784 / 9487990784` | `5/20` rollouts, `1/4` evals | `0 B` | none; process alive |
| `small_d2_seed3` | `19048` | `2026-09-04T12:06:20.328822Z` | `7045365760 / 7045365760` | first rollout in flight | `0 B` | none; process alive |

Each process was started separately with `Start-Process -WindowStyle Hidden`; its standard output
and error are redirected inside its own invocation directory. Each `preflight.json` passed before
that process was created. No receipt was reused as batch admission.

## Valid complete invocations

These are engineering-complete invocation facts only. No row comparison or frozen result branch is
applied before all 18 invocations complete.

| invocation | counts and artifacts | wall | resource telemetry | disposition |
| --- | --- | ---: | --- | --- |
| `small_d0_seed1` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 path rows, checkpoint, rollout-1/final five-network exposure | `4956.5854953 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d0_seed2` | same frozen counts and artifacts | `5044.9601495 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d2_seed1` | same frozen counts and artifacts | `6330.0531559 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |

Missing peak RSS leaves these invocations valid under the repository telemetry rule. Their wall
times remain below the per-invocation 8 h cap. All three launched while the code SHA was the launch
implementation SHA.

## Full 18-invocation matrix

`RUNNING` means independently admitted and detached. `NOT_CREATED` means no result root, RNG
master, model, optimizer, checkpoint, or scientific output has been created for that invocation.

| row | arm | seed | fixed science | runtime state at snapshot |
| --- | --- | ---: | --- | --- |
| small | D0 | 1 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE` |
| small | D0 | 2 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `RUNNING`, PID `24664` |
| small | D0 | 3 | `k=20`, `c=inf` | `RUNNING`, PID `6744` |
| small | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `RUNNING`, PID `19048` |
| medium | D0 | 1 | `k=5`, `c=inf` | `NOT_CREATED` |
| medium | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
| medium | D0 | 2 | `k=5`, `c=inf` | `NOT_CREATED` |
| medium | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
| medium | D0 | 3 | `k=5`, `c=inf` | `NOT_CREATED` |
| medium | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
| large | D0 | 1 | `k=5`, `c=inf` | `NOT_CREATED` |
| large | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
| large | D0 | 2 | `k=5`, `c=inf` | `NOT_CREATED` |
| large | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
| large | D0 | 3 | `k=5`, `c=inf` | `NOT_CREATED` |
| large | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |

## Resume boundary

Observe the three named PIDs and invocation directories to terminal without altering them. When a
slot clears, the next intended invocation is `medium_d0_seed1`, followed by its D2 pair and then
the remaining medium and large row pairs. This order is an operational plan, not a batch
admission: immediately before every individual detached launch, create only that invocation's
directory, run a fresh 4 GiB memory preflight into its `preflight.json`, and launch only when it
passes. A refused admission creates no learner state and is not a scientific result.

Do not apply the frozen E3 result rule until all 18 required invocations are validly complete. Do
not revive E2b, retune `c`, or use any intermediate return to alter the remaining launch set.
