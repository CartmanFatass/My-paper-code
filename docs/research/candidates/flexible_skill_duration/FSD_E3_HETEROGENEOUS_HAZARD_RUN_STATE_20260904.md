# FSD E3 heterogeneous-hazard detached run state

Snapshot: `2026-09-04T14:34:50Z`

This is an operational recoverability snapshot for the frozen B/EXPLORE object
`FSD-E3-HET-R01`. It records runtime facts only. It is not a result, an intake, a scientific
polarity, a queue implementation, or authority to bypass a fresh resource admission.

## Frozen and accepted boundary

- Science card:
  `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`
- Card blob: `2939b751f3cf5ed22b1c9b59d3620d9107955036`
- Launch implementation SHA: `e6108e466eeea3df31db52c53e49eef828bde41a`
- Accepted portability-repair SHA:
  `69b24de052f19d3fbdf457358edd1a9c222585f4`. It changes only the E3 runner's
  unavailable-peak-RSS handling and the focused publication-path test. The replacement runner is
  560 lines, the full focused E3 file passes `13/13`, and no frozen scientific, numerical, RNG,
  checkpoint, evaluation, or result-rule byte was changed.
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
- Current counts at this snapshot: card-accepted invocation cells `18`; result-bearing attempts
  independently admitted/launched `7`; running `0`; valid complete cells `6`; quarantined attempts
  `1`; unfulfilled cells `12`, of which `11` have never launched. The earlier local refusal is
  preserved as evidence but was not itself an admission or launch.

## Terminal remote attempt at the snapshot

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | progress | terminal artifact |
| --- | --- | --- | ---: | --- | --- |
| `medium_d0_seed1` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_medium_d0_seed1_20260904_01`; wrapper PID `11443` | `2026-09-04T13:45:42.145553Z` | `15438573568 / 15438573568` | learner reached `20/20` rollouts and `4/4` evals; E3 postprocess incomplete | task `failed`, exit `1`, tmux inactive; attempt quarantined |

The task ran in detached remote worktree
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed1_20260904_01` at exact pushed SHA
`e6108e466eeea3df31db52c53e49eef828bde41a`. Its one supervised command performed the remote
`admit-memory` immediately before the exact runner. No receipt was reused as batch admission and
no request-specific evidence input needed staging outside Git. The learner/evaluation stage
finished, but the Linux publication step reproduced a `ctypes.windll` `AttributeError`; required
E3 fields were not written. The attempt is engineering-incomplete, is not interpreted, and is
recorded in
`FSD_E3_MEDIUM_D0_SEED1_ATTEMPT01_QUARANTINE_INTAKE_20260904.md`.

## Valid complete invocations

These are engineering-complete invocation facts only. No row comparison or frozen result branch is
applied before all 18 invocations complete.

| invocation | counts and artifacts | wall | resource telemetry | disposition |
| --- | --- | ---: | --- | --- |
| `small_d0_seed1` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 path rows, checkpoint, rollout-1/final five-network exposure | `4956.5854953 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d0_seed2` | same frozen counts and artifacts | `5044.9601495 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d2_seed1` | same frozen counts and artifacts | `6330.0531559 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d0_seed3` | same frozen counts and artifacts | `5315.1814547 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d2_seed2` | same frozen counts and artifacts | `6590.2443548 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |
| `small_d2_seed3` | same frozen counts and artifacts | `6468.8387185 s` | `resources_unmeasured` | valid complete; no stderr/quarantine |

Missing peak RSS leaves these invocations valid under the repository telemetry rule. Their wall
times remain below the per-invocation 8 h cap. The first three launched while the code SHA was the
launch implementation SHA. The other three record state-only code SHA
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
invocation locally. The two then-live local processes were observed without migration or
duplication and have now terminated validly. Current main `.codex/hmasd-compute.toml` changed to
`status = "active"`; `medium_d0_seed1` attempt 01 was therefore launched once on `wsl_4070` using the exact
pushed SHA, a detached remote worktree, and one `agent-task` payload whose remote command performed
its own `admit-memory` immediately before the exact runner. The local refused receipt did not admit
the remote attempt. It is now terminal and quarantined after reproduced publication failure. The
same invocation cell remains unfulfilled and is held for an outcome-blind portability repair at a
new SHA; the other eleven never-launched invocations stay `REMOTE_FIRST_HOLD`. Local fallback
additionally requires definitive evidence of no remote process, prospective portability, and a
fresh local admission.

## Full 18-invocation matrix

`QUARANTINED_ATTEMPT` means the named evidence attempt is terminal and contributes nothing to the
frozen result rule; the invocation cell remains unfulfilled.
`REMOTE_FIRST_HOLD` means no result root, RNG master, model, optimizer, checkpoint, or scientific
output has been created for that invocation.

| row | arm | seed | fixed science | runtime state at snapshot |
| --- | --- | ---: | --- | --- |
| small | D0 | 1 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE` |
| small | D0 | 2 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE` |
| small | D0 | 3 | `k=20`, `c=inf` | `VALID_COMPLETE` |
| small | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE` |
| medium | D0 | 1 | `k=5`, `c=inf` | `QUARANTINED_ATTEMPT_01 / REPAIR_HOLD`; task `fsd_e3_medium_d0_seed1_20260904_01`; local refusal retained separately |
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

Attempt 01 is terminal and must not be resent, resumed, migrated, postprocessed into acceptance, or
used to alter the frozen sequence. The next action is the smallest outcome-blind portability fix
and an end-to-end publication-path test. Only after those bytes are accepted, explicitly
committed, and pushed may a new detached remote task make one fresh `medium_d0_seed1` attempt at the
new exact SHA. Its one payload must combine its own fresh 4 GiB remote preflight and exact runner
under the remote supervisor. After a valid complete replacement, continue with its D2 pair and
then the remaining medium and large row pairs as actual resource and dependency state allow. This
is an operational order, not a batch admission. A refused admission creates no learner state; the
quarantined attempt creates no scientific result.

Do not apply the frozen E3 result rule until all 18 required invocations are validly complete. Do
not revive E2b, retune `c`, or use any intermediate return to alter the remaining launch set.
