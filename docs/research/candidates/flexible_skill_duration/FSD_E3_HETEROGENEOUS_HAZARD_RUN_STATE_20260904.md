# FSD E3 heterogeneous-hazard detached run state

Snapshot: `2026-09-05T00:53:00Z`

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
- The twelve accepted local cell roots are in
  `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904`.
  The completed medium D0 seed-3 cell also remains in its original remote worktree and a distinct
  verified local staging root named in its CM receipt. Older evidence roots were preserved.
- All 18 row/arm/seed invocations are card-accepted. Each still requires its own immediately
  preceding `admit-memory` receipt with at least 4 GiB physical and effective availability.
- Frozen projections per invocation: D0 small `1.16 h`; D0 medium/large `1.68 h`; D2 conservative
  mechanical maximum `4.63 h`; all are below the `8 h` per-arm cap.
- Current counts at this snapshot: card-accepted invocation cells `18`; result-bearing attempts
  independently admitted/launched `14`; running `1`; valid complete cells `12`; quarantined
  attempts `1`; unfulfilled cells `6`, comprising one running and five never launched. The earlier local refusal
  is preserved as evidence but was not itself an admission or launch.

## Accepted running large D0 seed-1 cell

The medium-D2-seed-3 intake accepted cell 12 and selected the next unchanged matrix entry,
`large_d0_seed1`, with CLI owner items `20260904-fsd-006/007/008`. Result, intake, brief and
the complete prospective assignment were committed/pushed at
`f42dcb7a76f6341d3552a27134ca674674b29718` before launch. Binding record:
`FSD_E3_MEDIUM_D2_SEED3_INTAKE_20260904.md`. No source, card, comparator or budget changed.

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | observed state |
| --- | --- | --- | ---: | --- | --- |
| `large_d0_seed1` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_large_d0_seed1_20260904_01`; wrapper PID `802417`, learner PID `802469` | `2026-09-05T00:52:33.793656Z` | `15042007040 / 15042007040` | pushed SHA `f42dcb7a76f6341d3552a27134ca674674b29718` | `running` at uptime 20 s, exit null, tmux active; exact learner argv observed |

Detached cwd: `/home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01`.
Root under it: `temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1`;
fresh receipt `<root>/preflight.json`. Supervisor log:
`/home/wu/.agent-tasks/fsd_e3_large_d0_seed1_20260904_01/task.log`; same-task
`agent-task status` is the terminal/exit witness. CM inspected task/root absence and accepted
one send. The exact runner followed destination-node admission in one `&&`-joined payload;
both 4 GiB floors and all pass fields were satisfied. Admission is not runtime peak-RSS evidence.

Frozen invocation remains large hazards `(0.02,0.20)`, `Delta=1.0`, seed 1, D0 `k=5`, infinite
costs/both caps 5, age off, four-thread CPU; 20/16/400 rollouts/lanes/steps and unchanged
512/512/512/2048 evaluations, RNG/tapes, precision, checkpoint and normalizer semantics.
Projection is 1.68 h per cell, cap 8 h; the original nonfinite/20-rollout/first-completed-rollout
after-cap stop remains. No success or scientific branch follows from initial running acceptance.

Responsible DM `/root/dm_amx_fsd_continue` directly handed the exact handle/SHA/paths/bound to
`/root/tracker_tl_experiments`, then received a separate direct adoption ACK. CM
`/root/dm_amx_fsd_continue/cm_am_fsd_continue` ended routine polling after the initial facts and
ACK. Tracker owns the sole observer and directly wakes DM on terminal/failure/loss/cap concern;
DM acknowledges and resumes this same CM for collection. No Root relay or launch gate is added.

## Accepted terminal D2 seed-3 cell and dedicated tracker

The owner's current explicit resume from the final tracker-restart handoff supersedes every
historical drain/PAUSED instruction below. Root persisted that instruction and ACTIVE heartbeat
at `af99c1ce5`. The object-tier continuation intake and CLI owner item `20260904-fsd-005` were
committed/pushed before launch at `31bfecd79fc0f708546786ee26dfd8faa9e85dfb`:
`FSD_E3_MEDIUM_D2_SEED3_CONTINUATION_INTAKE_20260904.md`. No scientific card or source changed.

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | observed state |
| --- | --- | --- | ---: | --- | --- |
| `medium_d2_seed3` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_medium_d2_seed3_20260904_01`; wrapper PID `106154`, learner PID `106170` | `2026-09-04T23:46:29.300533Z` | `15432294400 / 15432294400` | pushed SHA `31bfecd79fc0f708546786ee26dfd8faa9e85dfb` | `finished`, exit 0 at `2026-09-05T00:29:52Z`, tmux inactive; CM accepted and DM intake complete |

Detached remote worktree:
`/home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01`.
Run root: that worktree's
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3`.
Admission: `<run-root>/preflight.json`, with every pass field true and both 4 GiB floors passed.
Supervisor log: `/home/wu/.agent-tasks/fsd_e3_medium_d2_seed3_20260904_01/task.log`;
the same directory retains `runner.sh`, `status`, `pid` and `start_time` witnesses.
The exact task's `agent-task status` is the terminal/exit witness. The initial running receipt
and terminal technical appendix are in
`docs/Claude_docs/experiments/FSD_E3_MEDIUM_D2_SEED3_REMOTE_RUN_20260904.md`.

CM directly checked next-task/remote-root/canonical-root absence, accepted one supervisor send,
then observed the fresh receipt, wrapper and learner. The payload joined destination-node
admission immediately to the exact runner with `&&`. CPU/four-thread, medium row, seed 3,
`c=c_Z=0.25`, caps 40/400, 20 rollouts and all frozen evaluation/RNG semantics remain unchanged.
Conservative per-cell cost is 4.63 h with an 8 h cap; the original stop rule remains in force.
Initial running acceptance, admission and a live learner were operational facts. The later
complete-artifact acceptance, not process exit alone, establishes this cell's validity.

Responsible DM: `/root/dm_amx_fsd_continue`; CM:
`/root/dm_amx_fsd_continue/cm_am_fsd_continue`. The DM handed this accepted handle directly to
shared default tracker `/root/tracker_tl_experiments`, which returned a separate direct adoption
ACK for the task and exact SHA under token `tracker-resume-fsd-20260904-01`. CM was told to end
routine polling after the initial checks. Tracker owns the sole routine observer and directly
notifies this DM on terminal/failure, observation loss or the stated bound; it never relaunches.
DM then resumes this same CM for terminal collection and acknowledges the reminder. Root relays
neither handles nor terminal notices. ACK was a capability observation, not a launch gate.

Tracker later directly notified terminal completion; DM ACKed and resumed the same CM for
collection. CM terminal receipt `6b0669394eec563e286b61833879e52847be3f41` verifies complete
20-rollout/128,000-transition/320-episode/3,584-evaluation evidence, 22,575 actual optimizer
steps, both regional paths, first/final exposures, checkpoint and E3 publication. All ten
remote/staged/canonical hashes agree. Runner wall is `2525.5407063739985 s`, retained supervisor
duration 2603 s; both are under the cap. Missing resource peaks remain `resources_unmeasured`.
Canonical and distinct staging roots are fully located in that receipt and
`FSD_E3_MEDIUM_D2_SEED3_RESULT_EVIDENCE_20260904.md`. DM intake
`FSD_E3_MEDIUM_D2_SEED3_INTAKE_20260904.md` accepts cell 12 and prospectively selects exactly
`large_d0_seed1`. Tracker no longer polls this completed handle; no successor is admitted at
this snapshot. No paired return or aggregate E3 branch is computed before all 18 are valid.

### Read-only observation interruption, 2026-09-05T00:10:58Z

Tracker directly reported an SSH timeout from configured `hmasd-wsl-node` before it could read
`agent-task status`. Its last successful poll at `2026-09-05T00:09:05Z` reported the same task
running, wrapper PID `106154`, tmux active. The latest runtime state is therefore **unknown**;
this does not establish learner failure, termination, cause, quarantine or scientific polarity.

DM acknowledged this specific event directly, preserving the sole accepted supervisor and all
original evidence. Tracker was asked to retain one bounded, read-only observer with backoff and
notify DM on recovery or terminal status; CM receives an observation handoff only if tracker
explicitly cannot retain coverage. No second polling chain, admission, stop or relaunch was
created. This is an operational update under the existing unchanged-cell decision, not a new
scientific selection. At this boundary both DM and integrated owner-review CLI reads returned
`[]`; the FSD audit owner columns were empty.

This interruption is now historical: the same supervisor finished normally and CM collected
complete evidence after transport recovered. The timeout did not classify a learner failure,
create a quarantine, or justify a new launch.

## Accepted terminal D0 seed-3 cell

The owner's instruction “我们开始推进自动研究流程” supersedes the old drained pause. The
object-tier resume intake is
`FSD_E3_MEDIUM_D0_SEED3_RESUME_INTAKE_20260904.md`; owner item `20260904-fsd-002` records the
unchanged next-cell selection. No new card, VSP-03 control, family or result branch was added.
The owner's then-later safe-drain instruction stopped scheduling before the next cell after the
current result was taken in. That historical boundary is superseded by the current resume above;
neither instruction changes the direction's lifecycle or priority.

| invocation | execution node and handle | receipt assessed UTC | physical/effective available bytes | launch boundary | observed state |
| --- | --- | --- | ---: | --- | --- |
| `medium_d0_seed3` attempt 01 | `wsl_4070`; `agent-task` `fsd_e3_medium_d0_seed3_20260904_01`; original wrapper PID `74470`, learner PID `74473` | `2026-09-04T21:39:47.176686Z` | `15429533696 / 15429533696` | pushed SHA `9c0a990537a8ffef58306429a1ff402550fc4b82`; runner SHA-256 `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1` | `finished`, exit `0` at `2026-09-04T22:26:00Z`, tmux inactive; CM technically accepted and DM intake complete |

Detached remote worktree:
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01`.
Run root: that worktree's
`temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`.
Admission receipt: `<run-root>/preflight.json`.
Supervisor log:
`/home/wu/.agent-tasks/fsd_e3_medium_d0_seed3_20260904_01/task.log`.

CM checked the task and scientific roots before sending, then observed the supervisor and learner
argv after the one accepted launch. One supervised payload joined the cell's fresh remote
`admit-memory` to the exact runner with `&&`; both 4 GiB floors passed. CPU/four-thread,
seed-3, `k=5`, 20-rollout and evaluation semantics remain frozen. The entire source comparison
against the accepted repair has no executable difference; its E0 docstring example is the only
wider-surface change. CM's exact command and acceptance evidence are recorded at
`docs/Claude_docs/experiments/FSD_E3_MEDIUM_D0_SEED3_REMOTE_RUN_20260904.md`.

CM's terminal receipt, pushed at `570670403f48ba0f2a3d64e6f47799a8354128d2`, checks all
20 learner/path records, four evaluations with `512/512/512/2048` ordered episode returns,
positive updates and first/final exposure in all five network groups, complete E3 publication,
and a readable checkpoint. All ten original/staged/canonical artifact hashes match. Runner wall
was `2687.7446834669972 s`; supervisor interval was `2773 s`. Missing RSS is
`resources_unmeasured`. Both durations are below the per-cell projection and 8-hour cap.

The cell is now the eleventh valid result. Its E0 evidence and DM intake are
`FSD_E3_MEDIUM_D0_SEED3_RESULT_EVIDENCE_20260904.md` and
`FSD_E3_MEDIUM_D0_SEED3_INTAKE_20260904.md`. The latter preserves the owner-direct execution
drain and exact seven-cell recovery boundary. No E3 aggregate branch or new mechanism polarity
is assigned from this incomplete study.

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

These are valid complete invocation facts. The seed-3 intake additionally reports that one D0
seed's raw observations; no paired-arm comparison or frozen aggregate result branch is applied
before all 18 invocations complete.

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
| `medium_d0_seed3` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 two-region path rows, checkpoint, rollout-1/final five-network exposure | `2687.7446834669972 s` | `resources_unmeasured` | attempt 01 valid complete; ten remote/staging/canonical hashes match; CM accepted and DM intake complete |
| `medium_d2_seed3` | 20 rollouts, 128000 transitions, 320 train episodes, eval `512/512/512/2048`, 20 two-region path rows, checkpoint, rollout-1/final five-network exposure | `2525.5407063739985 s` | `resources_unmeasured` | attempt 01 valid complete; ten remote/staging/canonical hashes match; CM accepted and DM intake complete |

Missing peak RSS leaves these invocations valid under the repository telemetry rule. Their wall
times remain below the per-invocation 8 h cap. The first three small cells launched while the code
SHA was the launch implementation SHA. The remaining three small cells record state-only code SHA
`5b84d8b072abda9650403b7fef7303a85205c48c`; its runner and focused-test byte surface is identical
to launch implementation SHA `e6108e466eeea3df31db52c53e49eef828bde41a`. The accepted medium
cells use the exact pushed SHAs named in their terminal tables and the same accepted repaired
runner SHA-256, including the now-complete medium D0 seed-3 cell.

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
the repaired outcome-blind attempt 02 subsequently fulfilled that invocation cell. Five
never-launched large-row invocations stay `REMOTE_FIRST_HOLD`; large D0 seed 1 is running and
medium D0/D2 seed 3 are valid complete under the owner's explicit resume. Local fallback additionally requires
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
| medium | D0 | 3 | `k=5`, `c=inf` | `VALID_COMPLETE`; attempt 01 task `fsd_e3_medium_d0_seed3_20260904_01`; intake complete |
| medium | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `VALID_COMPLETE`; attempt 01 task `fsd_e3_medium_d2_seed3_20260904_01`; CM acceptance and DM intake complete |
| large | D0 | 1 | `k=5`, `c=inf` | `RUNNING`; attempt 01 task `fsd_e3_large_d0_seed1_20260904_01`; fresh admission/learner observed and tracker directly adopted |
| large | D2 | 1 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 2 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 2 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |
| large | D0 | 3 | `k=5`, `c=inf` | `REMOTE_FIRST_HOLD` |
| large | D2 | 3 | `k_max=40`, `k_Z=400`, `c=0.25` | `REMOTE_FIRST_HOLD` |

## Resume boundary

The quarantined D0 seed-1 attempt 01 must not be resent, resumed, migrated, postprocessed into
acceptance, or used to alter the frozen sequence. Six medium-row cells are valid; no paired
return comparison or E3 aggregate branch is applied. The earlier pause after `medium_d2_seed2`
was superseded by the explicit resume that launched exactly `medium_d0_seed3`. That cell has now
finished and passed both CM technical acceptance and DM intake.

**Current owner-direct boundary:** automatic research resumed after the Root/config restart.
`medium_d2_seed3` has completed technical acceptance and DM intake, making all six medium cells
valid. `large_d0_seed1` is the sole FSD running task. The dedicated shared tracker holds its
accepted process identity directly and reminds the DM for CM collection and intake before
subsequent cells. Lifecycle, priority, card, claim
ceiling and accepted mechanism science stay unchanged. All prior terminal handles remain
historical evidence and are not polled or relaunched.

The current running task remains recoverable with
`ssh hmasd-wsl-node '/usr/local/bin/agent-task status fsd_e3_large_d0_seed1_20260904_01'`.
Do not duplicate this accepted task or resume completed checkpoints. The running table above
contains exact SHA, handle, receipt, process and output witnesses; terminal collection is pending.
The medium treatment result and all artifact-root locators remain in its receipt and E0 result.

After current-cell intake, the next never-launched cell is `large_d2_seed1`, followed by
`large_d0_seed2`, `large_d2_seed2`, `large_d0_seed3`, `large_d2_seed3`.
Each invocation still requires the exact pushed SHA and its own fresh 4 GiB remote preflight
immediately before its exact runner.
A refused admission creates no learner state; the historical quarantine creates no scientific
result. The completed tasks and all artifacts remain preserved across the Root/config restart.

Do not apply the frozen E3 result rule until all 18 required invocations are validly complete. Do
not revive E2b, retune `c`, or use any intermediate return to alter the remaining launch set.
