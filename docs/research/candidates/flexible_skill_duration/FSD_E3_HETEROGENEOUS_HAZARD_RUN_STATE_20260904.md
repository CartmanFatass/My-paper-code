# FSD E3 heterogeneous-hazard detached run state

Snapshot: `2026-09-04T13:17:02Z`

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
  running `2`; valid complete `4`; quarantined `0`; not admitted/launched `12`. One of the
  twelve has only a refused admission receipt and no learner or scientific output.

## Detached processes at the snapshot

| invocation | PID | receipt assessed UTC | physical/effective available bytes | progress | stderr | terminal artifact |
| --- | ---: | --- | ---: | --- | ---: | --- |
| `small_d2_seed2` | `24664` | `2026-09-04T11:43:50.271300Z` | `9409052672 / 9409052672` | `19/20` rollouts, `3/4` evals | `0 B` | none; process alive |
| `small_d2_seed3` | `19048` | `2026-09-04T12:06:20.328822Z` | `7045365760 / 7045365760` | `15/20` rollouts, `3/4` evals | `0 B` | none; process alive |

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
| `small_d0_seed3` | same frozen counts and artifacts | `5315.1814547 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |

Missing peak RSS leaves these invocations valid under the repository telemetry rule. Their wall
times remain below the per-invocation 8 h cap. The first three launched while the code SHA was the
launch implementation SHA. `small_d0_seed3` records state-only code SHA
`5b84d8b072abda9650403b7fef7303a85205c48c`; the runner and focused-test byte surface at that SHA
is identical to launch implementation SHA `e6108e466eeea3df31db52c53e49eef828bde41a`.

## Refused admission and current compute route

At `2026-09-04T13:16:07.609566Z`, after `small_d0_seed3` terminated, a fresh local preflight for
prospective invocation `medium_d0_seed1` measured `4094947328` bytes physical and effective
availability. That was `200019968` bytes below the 4 GiB floor, so the preflight exited `6` and no
runner process, RNG master, model, optimizer, checkpoint, manifest, or scientific result was
created. The evidence-only receipt is preserved as
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed1/preflight_refused_20260904T131607Z.json`.
It is neither a launch nor an admission for any node.

Owner routing changed immediately afterward: do not retry this or any other new portable E3
invocation locally. The two already accepted/live local processes above remain local and must not
be migrated or duplicated. The twelve not-yet-launched invocations are held at `REMOTE_FIRST`
until the current main control-plane file `.codex/hmasd-compute.toml` changes from
`status = "provisioning"` to an active state. A future remote launch requires the exact pushed SHA,
a detached remote worktree, and one remote `agent-task` payload whose remote command performs its
own `admit-memory` immediately before the exact runner. The refused local receipt cannot admit a
remote invocation. Local fallback additionally requires definitive evidence of no remote process,
prospective portability, and a fresh local admission.

## Full 18-invocation matrix

`RUNNING` means independently admitted and detached. `NOT_CREATED` means no result root, RNG
master, model, optimizer, checkpoint, or scientific output has been created for that invocation.

| row | arm | seed | fixed science | runtime state at snapshot |
| --- | --- | ---: | --- | --- |
| small | D0 | 1 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE` |
| small | D0 | 2 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `RUNNING`, PID `24664` |
| small | D0 | 3 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `RUNNING`, PID `19048` |
| medium | D0 | 1 | `k=5`, `c=inf` | `ADMISSION_REFUSED`; receipt only; `REMOTE_FIRST_HOLD` |
| medium | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| medium | D0 | 2 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| medium | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| medium | D0 | 3 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| medium | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 1 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 2 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 3 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |

## Resume boundary

Observe the two named local PIDs and invocation directories to terminal without altering them.
Do not retry `medium_d0_seed1` locally or start another new portable invocation while the remote
control plane is provisioning. Once Root marks the compute configuration active, resume with
`medium_d0_seed1`, followed by its D2 pair and then the remaining medium and large row pairs. This
order is an operational plan, not a batch admission: each individual remote payload must combine
its own fresh 4 GiB remote preflight and exact runner invocation under the remote supervisor. A
refused admission creates no learner state and is not a scientific result.

Do not apply the frozen E3 result rule until all 18 required invocations are validly complete. Do
not revive E2b, retune `c`, or use any intermediate return to alter the remaining launch set.
