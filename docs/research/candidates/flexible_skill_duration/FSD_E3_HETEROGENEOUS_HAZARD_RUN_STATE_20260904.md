# FSD E3 heterogeneous-hazard detached run state

Snapshot: `2026-09-04T11:22:49Z`

This is an operational recoverability snapshot for the frozen B/EXPLORE object
`FSD-E3-HET-R01`. It records runtime facts only. It is not a result, an intake, a scientific
polarity, a queue implementation, or authority to bypass a fresh resource admission.

## Frozen and accepted boundary

- Science card:
  `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`
- Card blob: `2939b751f3cf5ed22b1c9b59d3620d9107955036`
- Launch implementation SHA: `e6108e466eeea3df31db52c53e49eef828bde41a`
- Runner: `scripts/run_flexible_skill_duration_e3.py`
- Pre-launch focused suite on the launch SHA: `12 passed in 10.83s`
- Study root:
  `temp/directions/flexible_skill_duration/exp/E3_20260904`
- All 18 row/arm/seed invocations are card-accepted. Each still requires its own immediately
  preceding `admit-memory` receipt with at least 4 GiB physical and effective availability.
- Frozen projections per invocation: D0 small `1.16 h`; D0 medium/large `1.68 h`; D2 conservative
  mechanical maximum `4.63 h`; all are below the `8 h` per-arm cap.
- Current counts at this snapshot: card-accepted `18`; independently admitted/launched `3`;
  running `3`; valid complete `0`; quarantined `0`; not created/admitted `15`.

## Detached processes at the snapshot

| invocation | PID | receipt assessed UTC | physical/effective available bytes | progress | stderr | terminal artifact |
| --- | ---: | --- | ---: | --- | ---: | --- |
| `small_d0_seed1` | `22204` | `2026-09-04T10:19:39.135209Z` | `11764240384 / 11764240384` | `19/20` rollouts, `3/4` evals | `0 B` | none; process alive |
| `small_d2_seed1` | `6336` | `2026-09-04T10:19:59.853295Z` | `9868259328 / 9868259328` | `14/20` rollouts, `2/4` evals | `0 B` | none; process alive |
| `small_d0_seed2` | `2280` | `2026-09-04T10:20:29.744139Z` | `7983693824 / 7983693824` | `19/20` rollouts, `3/4` evals | `0 B` | none; process alive |

Each process was started separately with `Start-Process -WindowStyle Hidden`; its standard output
and error are redirected inside its own invocation directory. Each `preflight.json` passed before
that process was created. No receipt was reused as batch admission.

## Full 18-invocation matrix

`RUNNING` means independently admitted and detached. `NOT_CREATED` means no result root, RNG
master, model, optimizer, checkpoint, or scientific output has been created for that invocation.

| row | arm | seed | fixed science | runtime state at snapshot |
| --- | --- | ---: | --- | --- |
| small | D0 | 1 | `k=20`, `c=inf` | `RUNNING`, PID `22204` |
| small | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `RUNNING`, PID `6336` |
| small | D0 | 2 | `k=20`, `c=inf` | `RUNNING`, PID `2280` |
| small | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
| small | D0 | 3 | `k=20`, `c=inf` | `NOT_CREATED` |
| small | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `NOT_CREATED` |
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
slot clears, the next intended invocation is `small_d2_seed2`, followed by the remaining small-row
seed-3 pair, then the medium and large row pairs. This order is an operational plan, not a batch
admission: immediately before every individual detached launch, create only that invocation's
directory, run a fresh 4 GiB memory preflight into its `preflight.json`, and launch only when it
passes. A refused admission creates no learner state and is not a scientific result.

Do not apply the frozen E3 result rule until all 18 required invocations are validly complete. Do
not revive E2b, retune `c`, or use any intermediate return to alter the remaining launch set.
