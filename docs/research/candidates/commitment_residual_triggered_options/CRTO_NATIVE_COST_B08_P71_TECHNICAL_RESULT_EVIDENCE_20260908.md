# CRTO B08 P71 technical execution evidence

Status: **TERMINAL / COLLECTED / TECHNICALLY ACCEPTED**. Root allocated one real invocation at
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

One supervisor submission was accepted at `2026-09-09T05:28:32Z`, with return code 0 and no stderr.
`agent-task` reported tmux `agent_crto-b08-p70-seed0-20260909`; log path
`/home/wu/.agent-tasks/crto-b08-p70-seed0-20260909/task.log`.
First status: running, PID 3024150, uptime 18s, tmux active. Admission passed as recorded above.
The exact command and raw local receipts are preserved in the named stage/collection root:
`launch_command.txt`, `launch_receipt.json`, `staging_verification.json`.
CM retained sole observation through terminal facts and collection. Root/DM were notified once
of acceptance; no handover or second launch followed. The next section closes that running
milestone with actual terminal and collection evidence.


## Terminal result and collection acceptance

The same handle finished with exit 0, tmux inactive, at `2026-09-09T05:31:21Z`. Its terminal
log records **Duration 169s**, from 05:28:32Z. The later status uptimes 218s/320s include post-exit
waiting and are not used as runtime. There was exactly one accepted submission, one passed
actual-node admission and one real seed0/three-arm invocation. No retry, resumed process,
extra seed/arm/endpoint or scientific smoke occurred.

Published evidence:

- [Original complete summary](CRTO_NATIVE_COST_B08_P71_RESULT_20260908.json), all 411368 bytes,
  SHA256 `5fa2fcb91a643f1d377393994e38d390ae64ee3b39b270616ea788985e08fb61`.
- [Runtime receipts and technical checks](CRTO_NATIVE_COST_B08_P71_RUNTIME_RECEIPTS_20260908.json):
  staging/launch/admission, original supervisor log, terminal status, account command/response,
  complete accounting, copy verification and independently recalculated native facts.

CM copied `summary.json`, `admission.json`, `complete_accounting.json` and `task.log` from the
bound remote output/supervisor paths and verified their collected bytes against remote
size/SHA256. The original summary remains unchanged. The accepted source's account command
ran once after terminal collection with `--complete-wall-seconds 169`, exited0, and produced
`complete_accounting.json`; it performs no scientific work. Its exact argv is retained in the
runtime receipts. The summary's pre-publication/pending-accounting fields are preserved as
original output and are supplemented by this terminal collection record, not overwritten.

| Complete resource fact | Actual |
| --- | ---: |
| Whole quoted command, through publication/shutdown | 169s, supervisor whole-second resolution |
| Inner pre-publication wall | 164.3972584879957s |
| Shared overhead charged to every arm | 123.0375338079175s |
| RAW training/evaluation/scoring / final charged wall | 16.06360326905269s /139.1011370769702s |
| TRUE training/evaluation/scoring / final charged wall | 14.697494718013331s /137.73502852593083s |
| DERANGED training/evaluation/scoring / final charged wall | 15.201368205016479s /138.23890201293398s |
| Peak RSS reported by scientific process | 1543303168 bytes |

No charged-arm 1200s or complete shared 1500s cap breach is observed; the large margins are not
affected by the supervisor's one-second quantization. Study critical path and summed logical
invocation wall are both 169s; conservative arm charges are not summed as machine time.
Aggregate CPU is unmeasured. Admission was measured at the actual node and passed both 4 GiB
floors. Thread output reports all four native environment limits 1 and Torch intra/inter-op 1.
The source preserved CPU FP32. No cost/resource-efficiency claim is inferred.

Actual work: predictor 128 tapes/32256 available examples/100 updates/12800 processed examples;
calibration 64 tapes/16128 examples (12160 horizon4,3968 horizon8); gate 774 updates/24768 examples;
96 network readout rows/scored decisions on 16 unique EVAL identities; 54848 environment transitions
and 3520 common-future branch steps. Each arm's SHORT33/LONG258 exposure is 1056/8256 examples,
22/172 canonical recipient and donor occurrences, lr .001 and nominal exposure .033/.258.
Initial L2/RMS/Linf is 18.87916908516977/.10402732933491829/.28862619400024414 for all arms.
All six endpoint movements and last-batch expected-cost losses are finite and visible in the
original summary; all three LONG displacement ratios are nonzero and differ across arms.

CM's stdlib-only arithmetic over the original collected JSON checked 96 row decisions: legal
first-printed logit argmax, oracle action, native regret, side counts/competence and every signed
paired gain. Maximum native-regret recalculation discrepancy is 0. The 16 EVAL identities/order,
48-row canonical training order, donor maps and 22/172 occurrence records match the fixed B04
package. All historical rows in the summary match the frozen input. Both endpoints' three
native comparisons are trustworthy under the frozen source; their maximum legal-label
discrepancy is 0. These are direct checks over output bytes, not an environment replay or new
scientific invocation. No primary measurement is missing or limited in this result.

## Primary facts returned for DM scientific intake

All six deterministic action vectors are identical. Each arm at each endpoint has equal-side
regret **.0021294544930598857**, KEEP 8/8 exact oracle actions with 0 mean regret, and REPLAN 5/8
exact oracle actions with .004258908986119771 mean regret. New RAW-LONG is therefore observed
**not competent** because REPLAN exact actions 5 is below 6; historical competence is not substituted.
The emitted frozen reading is `WEAK_NEW_RAW_LONG_DIAGNOSTICS_ONLY`, both endpoint alignment
flags false, no selected checkpoint, and no competent residual polarity.

| Endpoint | new RAW minus TRUE | new DERANGED minus TRUE | historical B04 RAW minus TRUE |
| --- | ---: | ---: | ---: |
| SHORT33 | 0 | 0 | +.0044524264964700775 |
| LONG258 | 0 | 0 | +.0016519755926440258 |

All signed rows are retained. Against historical RAW, SHORT has 7 gain rows and 3 loss rows,
net +.07123882394352124 and total negative gain -.03407127188895817; LONG has 3 gain rows and 2
loss rows, net +.026431609482304413 and total negative gain -.02270649938121741. The positive
historical aggregate never erases those losses. Historical TRUE regret improvement is
+.015984557591254618 at SHORT and +.008786079220940025 at LONG; those descriptive values do
not satisfy the new-RAW/new-DERANGED comparisons. New RAW minus new DERANGED regret is 0 at
both endpoints. These observations retain the reused-seed/exposed-panel ceiling and do not
establish equivalence, stable superiority or family exhaustion. DM owns the scientific intake,
forecast scoring and next-node recommendation; P71 allocates no successor.

The original log includes the inherited PyTorch warning about a non-writable NumPy history
view at `models.py:186`. Execution completed; native-label comparison checks above show no
observed discrepancy. No source repair or unique root-cause claim is made from that warning.

## Closure and remaining owner

Technical acceptance covers the exact committed source/input, one admitted detached invocation,
actual complete primary outputs/counts, corrected trustworthy-contrast reading, complete terminal
accounting and byte-preserving collection. No source was changed in P71 and no assigned process
remains live. The task's local stage/collection root and remote scientific outputs are evidence,
not test scratch; they are retained. No tests or disposable test scratch were created by P71.

DM receives all outcomes for scientific intake; Root receives the result and remaining action.
The detached execution checkout remains at the bound path only for this pending delivery/parent
acceptance. **Root owns its reclamation after accepting the archived result** under AGENTS 6;
source commit/input/evidence remain preserved, and the scientific output root is not deleted.
There is no ongoing observer handover. This return releases the direction checkout's index.
