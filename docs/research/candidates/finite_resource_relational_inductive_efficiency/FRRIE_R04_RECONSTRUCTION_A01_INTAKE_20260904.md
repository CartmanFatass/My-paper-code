# FRRIE A01 diagnostic result intake — 2026-09-04

Status: `VALID_A_RECON / A01_NO_FAULT_WITHIN_BOUND / R04_CAUSE_UNRESOLVED`.

## What DM checked

DM read CM's E0 Markdown and compact JSON, the terminal CM record at committed/pushed
`6c7e44adbdf3aa8d468e74a5f53756eec21d1abd`, and the frozen A01 card/selection record. The exact
source/command, conditional capture requirement, node, literal root, execution order, admission,
completed counters, original exit path, publication, actual wall, scope and retained artifact
inventory were compared against that card. Native return/gap fields and the embedded B branch were
not presented to or used by this intake. CM supplied direct runtime observations; DM interprets
the recorded evidence. No new model, RNG, learner, test or experiment was run for intake.

The original runner's `SystemExit(0)` is directly recorded, independently of pdb/supervisor exit 0.
No original exception traceback occurred. The later fixed pdb commands ran at the normal debugger
stop before the script's first statement, as already verified, and their absent-local errors are
not learner failures. A matching-signature exception did not exist, so that conditional address/
field capture was not required. There was no second script-body or learner execution.

## Rule applied verbatim

> `A01_NO_FAULT_WITHIN_BOUND`: the original path reaches normal completion or the declared deadline
> without the recorded fault. State the actual reached boundary; r04 is not exonerated or repaired.

This is the first matching branch. `A01_INCOMPLETE_OBSERVATION` is false: the fixed source/node/
execution boundary, admission and required observations are present. Neither a matching original
exception nor another original failure occurred. The actual reached boundary was **natural full
128-update completion**, not a timeout. Accept only `A/RECON`, with no post-hoc B upgrade.

## Counts, receipts and cost

| quantity | directly retained observation |
| --- | --- |
| task / launch source | `frrie_r04_reconstruction_a01_b41a6ba7` / `b41a6ba779e514937e35c9b0c1dbc69a50ec68d5` |
| node | `wsl_4070`, configured Python 3.10, CPU FP32, one Torch thread |
| start / end | `2026-09-05T00:05:30Z` / `2026-09-05T00:20:57Z` |
| admission | physical and effective each 12,857,679,872 bytes; fresh on the actual node |
| original and supervisor termination | original SystemExit 0; separately pdb/supervisor exit 0 |
| paired updates | 128 |
| per-arm backward / Adam | 128 / 128 |
| per-arm factual episodes / learner transitions | 8,192 / 98,304 |
| per-arm training slots | 630,784 |
| per-arm learned evaluation episodes / slots | 2,048 / 24,576 |
| all evaluation episodes / slots | 4,608 / 55,296 |
| completed checks | 22 of 22 true |
| original summary | 118,881 bytes |
| actual supervisor / runner wall | 927 / 902.2496755629982 seconds |
| attributed PHY / EDGE wall | 160.52530051894428 / 160.3020884220823 seconds; shared work is additional |
| peak RSS | 615,354,368 bytes; scratch not measured |

The 1,800-second deadline plus five-second grace was not reached. No resource or engineering-scope
budget breach is observed. The source diff against r04's FRRIE surface is zero. Added files were
six stdlib fixture lines and nine fixed debugger commands, not a research wrapper. Required
exception-state telemetry was named on the card. The one lifecycle check was not repeated.

The original receipt, summary and six supervisor files remain remotely at the paths in the CM
record and as copies in the CM worktree's
`temp/directions/finite_resource_relational_inductive_efficiency/technical/a01-collection/`.
The supervisor log is 1,958 bytes; runner script 1,929; status 9; exit code 2; PID 7; start time 11;
admission 504. Later status uptime is not execution wall. A short observation loss was resolved
by one read-only status connection; it changed neither the process nor its deadline.

Exposure is the unchanged machine-generated line:
`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05;
nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04;
initial_projection_changed_coordinates=5`. Here the full update count is also directly retained.

The 927 seconds are a valid diagnostic's cost, recorded separately from the prior four accepted
B results and their Windows wall window. No new accepted B result or lifetime cost ratio is
manufactured. Headroom remains absent on RIDGEGATE-2Z; other hosts' baseline sets do not match.

## Bounded interpretation and predictions

The unchanged computational source and prescribed input sequence can complete in this observed
execution. This is stronger launchability evidence than a representative-address or tape-only
probe because the native/learner prefix also ran. It does not reconstruct r04's unretained process
state. Debugger process context may itself differ from the original invocation even though its
line tracing was disabled and no scientific computation was replaced.

Strongest support is the original normal-exit witness together with full paired counters and
published output. Strongest limitation is nonrecurrence: there is still no captured r04 failure
state or demonstrated cause. Source/input, process-state, native and interpreter explanations are
not excluded; no repair, transience, harmlessness or common cause is identified. Attempt02 remains
separate and unresolved. This observation supplies neither support nor contradiction for the
activated projection's native-return value. DIRECTION therefore stays unchanged.

DM's recorded A01 prediction was `A01_NO_FAULT_WITHIN_BOUND`, low confidence: **matched**, by
normal completion rather than deadline. The owner prediction is `not taken (unattended)`; no
prediction reply exists. The original R02 scientific prediction is still unscored. Reviews in both
the DM and integration worktrees returned `[]`; today's review is already answered, yesterday's
file is absent, and no new direction-specific owner instruction is present.

## Decisions this intake produces

### Validity and reading

Options: (a) accept the complete A01 observation with its literal no-fault boundary; (b) treat
normal completion as repair or scientific R02 success; (c) invalidate it because exception locals
do not exist after normal completion.

Recommendation and selection: **(a)**. It applies the predeclared conditional observation rule
and preserves class. Object tier, kind `technical`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.

### Next invocation

Options: (a) one fresh unchanged-card R02 B attempt using the already verified exception-observation
route; (b) another full-chain A diagnostic without a new cause-discriminating intervention;
(c) retroactively promote A01 into the original B result.

Recommendation and selection: **(a)**. The full source path completed; no concrete repair is
identified. A fresh B invocation can answer the already accepted algorithm question while
preserving the same exception observation if it fails. Repeating A without a new discriminator
would spend comparable work without advancing that question, and option (c) violates A01's
prospective class boundary. This is a fresh invocation, not evidence reuse or a claim of repair.
The literal root, computation, comparison, update/evaluation work, MEI and first-match rule remain
fixed. No outcome-dependent seed or treatment is selected.

Object tier, kind `selection`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
The prospective R05 execution addendum names exception telemetry for this invocation and records
the observed same-node cost. No new family, direction decision, lifecycle or priority change occurs.

## Next discriminator and owner surfaces

The next scientific discriminator is the original R02 direct return contrast after a complete
fresh R05 invocation. Its claim ceiling remains one literal root, seen N={9,15}, CPU FP32 on the
actual node, B/EXPLORE; no relation-specificity, stable superiority, transfer or population claim.
R05 is selected only after this written intake and before any R05 question-relevant output.

CM owns the new exact committed/pushed launch, fresh admission, detached process and subsequent
collection. The tracker observes accepted handles and notifies DM/CM directly. Old r04, A01 and
all earlier attempts remain distinct and preserved. No old model, checkpoint, tape, native build
or result is reused. Previously passing debugger/source checks are reused without another smoke.

Real publication completed in A01; formal-sized end-to-end test coverage remains unrecorded,
an engineering limitation rather than a new B gate. The Chinese brief and owner-console items
are written at this intake; append-ready audit rows are supplied below for Root integration.

The brief is 316 characters, below 600. Owner items: `20260904-frrie-019` accepts the A reading;
`020` carries its brief; `021` records the delegated R05 selection; `022` presents the execution
addendum and Chinese decision packet. The original B prediction is not recreated per invocation.

### frrie-a01-intake-r05-selection

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T17:48:59-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) accept A01 complete no-fault boundary; (b) infer repair or B success; (c) reject absent exception locals after normal exit | (a) VALID A/RECON A01_NO_FAULT_WITHIN_BOUND, natural completion | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-019.json` | none | |
| 2026-09-04T17:48:59-07:00 | finite_resource_relational_inductive_efficiency | object | technical | reading-agreed; reading-disputed | publish A01 Chinese brief; no owner reading imputed | yes | VALID_RESULT_INTAKE | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-020.json` | none | |
| 2026-09-04T17:49:00-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) fresh unchanged R02 B attempt with existing exception observation; (b) another same A diagnostic; (c) upgrade A01 post hoc | (a) one fresh R05 at unchanged scientific meaning, no new production source | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-021.json` | none | |
| 2026-09-04T17:49:01-07:00 | finite_resource_relational_inductive_efficiency | object | technical | accept; reject; revise | frozen R05 execution addendum; accept recommended, no owner choice imputed | yes | CARD_RECORDED | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-022.json` | none | |
