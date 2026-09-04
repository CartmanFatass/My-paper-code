# FSD E3 heterogeneous-hazard detached run state

Snapshot: `2026-09-04T19:13:05Z`

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
  independently admitted/launched `11`; running `0`; valid complete cells `10`; quarantined
  attempts `1`; unfulfilled cells `8`, all of which have never launched. The earlier local refusal
  is preserved as evidence but was not itself an admission or launch.

## Accepted terminal D2 seed-2 cell

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | terminal state |
| --- | --- | --- | ---: | --- | --- |
| `medium_d2_seed2` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_medium_d2_seed2_20260904_01`; wrapper PID `48821` | `2026-09-04T18:29:08.457312Z` | `15443664896 / 15443664896` | pushed SHA `4b61ddfffac042e2247c77668bc881cca68b9a78`; runner SHA-256 `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1` | `finished`, exit `0` at `2026-09-04T19:10:12Z`; tmux inactive; CM accepted |

This invocation ran in detached worktree
`/home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed2_20260904_01`. Its one supervised payload ran its
own fresh remote `admit-memory` immediately before the exact full runner and passed both 4 GiB
floors. No earlier receipt was reused, and no other invocation was admitted by this receipt. All
ten top-level artifact files matched the remote SHA-256 list after fetch and again after copy to
canonical local root
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed2`. The measured wall was
`2405.3374142149987 s`, below the conservative `4.63 h` projection and the `8 h` cap. Missing peak
RSS is recorded as `resources_unmeasured` under the repository telemetry rule. CM accepted the
contract counts, configuration, RNG and tape semantics, two-region path, exposures, checkpoint and
publication fields without inspecting or comparing scientific returns.

## Accepted terminal D0 seed-2 cell

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | terminal state |
| --- | --- | --- | ---: | --- | --- |
| `medium_d0_seed2` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_medium_d0_seed2_20260904_01`; wrapper PID `36170` | `2026-09-04T16:41:56.473341Z` | `15441227776 / 15441227776` | pushed SHA `e72e1cf08c9510b52ef67b135e93eee89dc4ddce`; runner SHA-256 `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1` | `finished`, exit `0` at `2026-09-04T17:26:32Z`; tmux inactive; CM accepted |

This invocation ran in detached worktree
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed2_20260904_01`. Its one supervised payload ran its
own fresh remote `admit-memory` immediately before the exact full runner and passed both 4 GiB
floors. No earlier receipt was reused, and no other invocation was admitted by this receipt. All
ten top-level artifact files matched the remote SHA-256 list after fetch and again after copy to
canonical local root
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed2`. The measured wall was
`2620.9682462340006 s`, below both the recorded `1.68 h` projection and the `8 h` cap. Missing peak
RSS is recorded as `resources_unmeasured` under the repository telemetry rule. CM accepted the
contract counts, configuration, RNG and tape semantics, exposures, checkpoint and publication
fields without inspecting or comparing scientific returns.

## Accepted terminal D2 pair

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | terminal state |
| --- | --- | --- | ---: | --- | --- |
| `medium_d2_seed1` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_medium_d2_seed1_20260904_01`; wrapper PID `28945` | `2026-09-04T15:35:02.258441Z` | `15447285760 / 15447285760` | pushed SHA `4c60f281febd9c5c6503b12aa8053f05642aac32`; runner SHA-256 `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1` | `finished`, exit `0` at `2026-09-04T16:20:20Z`; tmux inactive; CM accepted |

This D2 pair ran in detached worktree
`/home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed1_20260904_01`. Its one supervised payload ran its
own fresh remote `admit-memory` immediately before the exact full runner and passed both 4 GiB
floors. The D0 receipt was not reused, and no other invocation was admitted by this receipt. All
ten top-level artifact files matched the remote SHA-256 list after fetch and again after copy to
canonical local root
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed1`.

## Accepted terminal replacement attempt

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | terminal state |
| --- | --- | --- | ---: | --- | --- |
| `medium_d0_seed1` attempt 02 | `wsl_4070`; `agent-task` `fsd_e3_medium_d0_seed1_20260904_02`; wrapper PID `21170` | `2026-09-04T14:41:52.389634Z` | `15434072064 / 15434072064` | pushed SHA `ee7fdae278cede2200ab8c356c4f238cce980edb`; runner SHA-256 `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1` | `finished`, exit `0` at `2026-09-04T15:26:31Z`; tmux inactive; CM accepted |

Attempt 02 ran in detached worktree
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed1_20260904_02`. Its one supervised payload ran the
fresh remote `admit-memory` immediately before the exact full runner and passed both 4 GiB floors.
It is a new attempt at the repaired SHA, not a resume, salvage, migration, or duplicate of attempt
01. No other new invocation was admitted by this receipt. All ten top-level artifact files were
copied to a request-specific local staging root and matched the remote SHA-256 list exactly before
being copied into canonical local root
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed1`; the earlier refused local
receipt remains alongside, under its distinct filename.

## Quarantined remote attempt

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
| `medium_d0_seed1` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 path rows, checkpoint, rollout-1/final five-network exposure | `2677.041620939 s` | `resources_unmeasured` | attempt 02 valid complete; exact remote/local hashes; CM accepted; attempt 01 remains quarantined |
| `medium_d2_seed1` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 two-region path rows, checkpoint, rollout-1/final five-network exposure | `2678.061287428 s` | `resources_unmeasured` | attempt 01 valid complete; exact remote/local hashes; CM accepted |
| `medium_d0_seed2` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 two-region path rows, checkpoint, rollout-1/final five-network exposure | `2620.9682462340006 s` | `resources_unmeasured` | attempt 01 valid complete; exact remote/local hashes; CM accepted |
| `medium_d2_seed2` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 two-region path rows, checkpoint, rollout-1/final five-network exposure | `2405.3374142149987 s` | `resources_unmeasured` | attempt 01 valid complete; exact remote/local hashes; CM accepted |

Missing peak RSS leaves these invocations valid under the repository telemetry rule. Their wall
times remain below the per-invocation 8 h cap. The first three small cells launched while the code
SHA was the launch implementation SHA. The remaining three small cells record state-only code SHA
`5b84d8b072abda9650403b7fef7303a85205c48c`; its runner and focused-test byte surface is identical
to launch implementation SHA `e6108e466eeea3df31db52c53e49eef828bde41a`. The accepted medium
cells use the exact pushed SHAs named in their terminal tables and the same accepted repaired
runner SHA-256.

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
the remote attempt. Attempt 01 is terminal and quarantined after reproduced publication failure;
the repaired outcome-blind attempt 02 subsequently fulfilled that invocation cell. The eight
never-launched invocations stay `REMOTE_FIRST_HOLD`. Local fallback additionally requires
definitive evidence of no remote process, prospective portability, and a fresh local admission.

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
| medium | D0 | 1 | `k=5`, `c=inf` | `VALID_COMPLETE`; attempt 02 task `fsd_e3_medium_d0_seed1_20260904_02`; attempt 01 quarantined and local refusal retained separately |
| medium | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE`; attempt 01 task `fsd_e3_medium_d2_seed1_20260904_01` |
| medium | D0 | 2 | `k=5`, `c=inf` | `VALID_COMPLETE`; attempt 01 task `fsd_e3_medium_d0_seed2_20260904_01` |
| medium | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE`; attempt 01 task `fsd_e3_medium_d2_seed2_20260904_01` |
| medium | D0 | 3 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| medium | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 1 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 2 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 3 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |

## Resume boundary

The quarantined D0 seed-1 attempt 01 must not be resent, resumed, migrated, postprocessed into
acceptance, or used to alter the frozen sequence. Four medium-row cells are now valid; no return
comparison or E3 result branch is applied. Owner instruction received after `medium_d2_seed2`
terminated requires the direction to pause at this drained boundary. `medium_d0_seed3` is the next
frozen invocation but remains uncreated and unlaunched: no task, preflight, result root, model,
optimizer or RNG master exists for it. When the owner or Root resumes this direction, every later
invocation still requires the exact pushed SHA and its own fresh 4 GiB remote preflight immediately
before its exact runner. A refused admission creates no learner state; the quarantined attempt
creates no scientific result.

Do not apply the frozen E3 result rule until all 18 required invocations are validly complete. Do
not revive E2b, retune `c`, or use any intermediate return to alter the remaining launch set.
