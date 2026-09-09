# CRTO B08 P71 technical execution evidence

Status: **ACCEPTED / RUNNING**. Root allocated one real invocation at
`9c2153b55b81fc6ab47f216014f62b14b581e476`. The assigned CM is the sole observer and collector;
DM owns scientific intake and Root receives milestones without parallel polling.

## Fixed binding and staged facts

The exact command, card and frozen historical input are the final P70
[technical binding](CRTO_NATIVE_COST_B08_P70_TECHNICAL_ACCEPTANCE_20260908.md#literal-prospective-execution-binding--not-staged-or-executed).
Source is `d9f643b761d57584de313b1f837d6c2c0becc931`; the P70 names remain unchanged.
CPU FP32/thread1, reused seed0, RAW/TRUE_RESIDUAL/CALIBRATED_DERANGEMENT, uninterrupted258 updates
and endpoints33/258 remain fixed. No source change, extra arm, retry, resume, smoke or successor
is allocated.

Remote node: `wsl_4070`, SSH `hmasd-wsl-node`, hostname `LAPTOP-U9TDKC8A`.
Interpreter: `/home/wu/.venvs/hmasd/bin/python`, actual `Python 3.10.21`.
Detached cwd: `/home/wu/hmasd-worktrees/crto-b08-p70-d9f643b761d57584de313b1f837d6c2c0becc931`.
Supervisor: `/usr/local/bin/agent-task`; fixed handle `crto-b08-p70-seed0-20260909`.
Result root: `/home/wu/projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/b08_seed0_p70_20260909`.
Frozen input: `/home/wu/hmasd-inputs/crto-b08-p70/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json`.
Local stage/collection root: `C:/Projects/HMASD-worktrees/codex-crto/temp/directions/commitment_residual_triggered_options/exp/b08_seed0_p70_20260909`.

Initial exact-handle status was `not_found`; bound input/cwd/result-root paths were absent.
CM extracted the frozen historical Git blob (193466 bytes) without Windows newline conversion,
verified SHA256 `1e5bd64d9f93ec75d5fe27921ac5c7877c4f027b5f01e239cf691c9e0ad4716a`,
copied it to the bound remote input path, and verified remote size/digest. The detached checkout
reports the exact source SHA, clean status and no diff from that SHA across runtime source paths.
The literal P70 supervisor command was read directly from its committed technical record into
local `launch_command.txt`; remote `bash -n` exited0 without executing the payload.

Source staging initially used a non-login SSH shell, which stalled the partial clone's network
fetch. Those staging-only processes were stopped, and their SSH clients closed. The configured
`zsh -lic` network route fetched the required source objects, but branch-ref update encountered
a pre-existing `origin/codex/crto/...` ref namespace conflict. Those refs were preserved. The exact
source commit was available and was used directly. Worktree population likewise needed the
configured network shell for missing promised blobs; Git removed the interrupted incomplete
checkout, and the exact bound checkout then completed under `zsh -lic`. These are pre-submission
source-staging facts, not accepted scientific invocations or result retries.

## Cost, coverage and enforcement recorded before submission

Per-arm cost projection: reused P68/B04 complete-stage law gives RAW413.97090837899304s,
TRUE411.96144017999904s, DERANGED413.06858835300955s, shared515.3820955440096s. They remain below
1200s charged per arm and1500s shared. Current load, changed-loss and setup/publication overhead
are unmeasured. Do not sum per-arm charges: study elapsed equals one invocation wall; aggregate
CPU work is unmeasured. Source preparation/copy/Git and observer collection are outside science wall.

Post-learner path coverage: P70's synthetic sixteen-row readout, JSON publication/readback,
terminal accounting reducer and mocked complete assembly passed focused tests; no new smoke was
run. Native panel agreement and actual work/resources remain unobserved until this invocation.

Existing deadline enforcement was inspected, not piloted: B08's `WallBudget` counts accrued
shared time plus each arm's training/evaluation/scoring, checks during preparation and learner
work and around publication, and raises when a charged arm exceeds1200s or shared exceeds1500s.
The existing `agent-task` preserves the detached command, exit, log and terminal duration; it has
no preemptive deadline itself. The accepted source binding explicitly describes callback-based
checks rather than an operating-system deadline. CM observes the same handle and reports/stops
an over-cap live command using the existing supervisor if necessary; no replacement launch follows.
The terminal log's `Duration` (whole-second resolution), not `status.uptime_seconds` after exit,
is the complete quoted-command elapsed used for `account`; it includes admission, runner startup,
all required scientific output publication and shutdown. Final accounting reduction is collection
metadata performed after termination, outside the scientific invocation.

The exact command places fresh actual-node `admit-memory` immediately before the runner with
`&&`; physical and effective available memory must both be >=4GiB. The accepted command's admission passed at `2026-09-09T05:28:32.086188Z`: physical and effective
available bytes both14403616768, measured via `/proc/meminfo`, against4294967296 bytes required.
One accepted submission maximum. An unexpected existing handle/input, admission/integrity/cap
conflict is returned without a replacement invocation. Partial output remains in place.

## Accepted handle milestone

One supervisor submission was accepted at `2026-09-09T05:28:32Z`, with returncode0 and no stderr.
`agent-task` reported tmux `agent_crto-b08-p70-seed0-20260909`; log path
`/home/wu/.agent-tasks/crto-b08-p70-seed0-20260909/task.log`.
First status: running, PID3024150, uptime18s, tmux active. Admission passed as recorded above.
The exact command and raw local receipts are preserved in the named stage/collection root:
`launch_command.txt`, `launch_receipt.json`, `staging_verification.json`.
CM retains observation through terminal facts and collection. Root/DM were notified once of
acceptance; no handover or second launch is authorized by that message. Primary result and
complete time remain unmeasured at this milestone.
