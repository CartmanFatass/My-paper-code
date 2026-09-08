Claim: one capped observation may recover the active Python call path at a fatal event in the unchanged B05 RAW learner; it tests no algorithm effect or historical root cause.
Binding structure: systems / information flow.

# CBSC-B05-FIRST-FAULT-P32 — A/RECON

This diagnostic concerns execution of a public-history learner inspired by
multi-agent partial observability; the fault-context question itself does not
arise from agent interaction or other-agent non-stationarity.

## Question, authority and retained-evidence check

[P32](../../portfolio/handoffs/2026-09-08-p32-cbsc-first-fault-context.md), main
`0c6bf8e175632098e46fcff1417d5d3c078962c9`, allocates at most one separate
first-fault observation after inspecting named retained evidence. Entry checkout
was clean at `eb76b46401064fb9a0380e5e65fdd00dabf8c597`; required P32/routing
inputs were synchronized in `e75a66e72f88424411bfc387544ff66e211beb82`.
Authoring remains `codex/cbsc` in
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`.

DM read P28's retained `logs.txt`, copied supervisor `task.log` and
`collection_facts.json` under
`temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907_collection/raw/`.
The two 812-byte logs contain admission, signal 11, exit 139 and 39.83 seconds,
but no location-bearing stack. The recorded inventory names no readable fatal
report or core path. No exhaustive dump census, target import or replay was done.
Retained evidence therefore cannot answer the missing call path.

Question: does startup-enabled fatal-stack reporting provide a location-bearing
Python call path during one unchanged RAW execution within 120 seconds? The
reference is P28's existing signal-only failure; this is an operation-context
observation, not a controlled estimate of the capture option's effect. Retain
[P28 intake](CBSC_OPPORTUNITY_CREDIT_B05_INTAKE_20260907.md) unchanged as
INCOMPLETE_RAW, with 24 durable update rows and zero complete pairs.

## Frozen source, input and observation channel

Scientific source: `d2753be86c12bfa63c404ac2cac513b914371115`; accepted source
checks and independent review remain those in the
[B05 handoff](CBSC_OPPORTUNITY_CREDIT_B05_ROOT_HANDOFF_20260907.md),
`87c1f2f01466e8ce0a558fc939b3f774b02af9f2`. Reuse them without smoke or imports.
Entry point: `scripts/run_cbsc_opportunity_credit_b04.py --b05 --arm RAW-GRU
--seed 21223`. Preflight ec8866b3968fcb1566976ce405d7c552d4d9a5de is already
present unchanged in that source. There is no code or package change.

Input is a fresh model/optimizer and original B1_RUN namespace at repeated seed
21223, with generated TRAIN/EVAL tapes; no retained checkpoint is resumed.
Preserve the [B05 card](CBSC_OPPORTUNITY_CREDIT_B05_SCIENCE_CARD_20260907.md)
sections Learner, host and comparison preserved / Fresh seed, runtime, outputs
and primary measurement: RAW public information, dynamic host, rewards, sampled
opportunity targets, normalization, optimizer/order, 48 rollouts, eight episodes
per rollout, four PPO epochs/four minibatches and update-0/48 evaluations.
The three RAW rule panels and ordinary publication/readback remain scheduled.
There is no STRUCT or pair computation. Original B05 metadata inside artifacts
identifies the reused learner; this outer card/handle identifies the diagnostic.

Node is pinned to wsl_4070, CPU FP32, one scientific process and Torch compute
thread, with original numeric-library thread limits. Interpreter:
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`
(P17/P28: CPython 3.12.3, NumPy 1.26.3, Torch 2.7.0+cu118).
Reuse the existing detached execution cwd
`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907` at the bound source.
New output parent relative to that cwd:
`temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908`;
runner output `raw/`, admission `raw-admission.json`.
New handle: `cbsc-b05-first-fault-p32-20260908`.

The sole changed observation option is `-X faulthandler`, before the script
argument on the selected interpreter. Capture its existing stderr in the
supervisor's `task.log`; do not add a debug wrapper, signal injection or timer
thread. The [Python 3.12 documentation](https://docs.python.org/3.12/library/faulthandler.html)
supports startup activation and fatal Python traceback reporting to stderr.
It does not promise a native C backtrace, an offending writer or cause attribution.
The CM's exact command/collection literals and syntax acceptance will be committed
in `CBSC_B05_FIRST_FAULT_P32_ROOT_HANDOFF_20260908.md` before Root dispatch.

## Work, cost and exposure

One logical invocation, at most **120 seconds complete**, TERM at 115 seconds
plus five seconds KILL grace. The envelope includes admission, imports, all
learning/evaluation, fault reporting, normal publication/readback and termination.
Actual outer wall and terminal facts decide cap conformance; configured timeout
alone is not proof. Root performs fresh adjacent physical/effective memory
admission >=4 GiB on the actual node, joined by `&&` to the exact runner.
Missing/failed admission refuses the runner. No local fallback is selected.

Dominant work ceilings are 1 arm x 48 rollouts x 8 episodes, and 48 x 4 x 4
Adam steps; two 32-episode evaluations plus three 32-tape rule panels. This is
real learner exposure, not zero-learner diagnostics. The
[machine calculation](CBSC_B05_FIRST_FAULT_P32_EXPOSURE_AND_COST_20260908.json)
records 384 training episodes, 58368 transitions, 9216 decisions, 768 Adam
steps, 64 evaluations and 96 rule passes as schedule ceilings, not completed work.
Validation adds only static command/shell syntax checks; no runtime/import probe.
Fault-reporting overhead is unknown and included in the same 120-second cap.

P28 failed at 39.83 seconds. B05's older full-RAW planning scenario is 159.38
seconds; it is not a promise that a normal 48-update completion fits P32.
The diagnostic endpoint is the first terminal/cap observation with available
context, not forced completion of the original learner endpoint. An unchanged
600/1200-second pair could fail without a stack; shortening the learning schedule
would change the context. This selected observation seeks an actionable boundary,
not a complete causal diagnosis or a universal prerequisite for later B work.

Machine-generated exposure line: P32 allocates at most one fresh RAW execution
at repeated seed 21223; unchanged schedule ceiling 48 rollouts / 768 Adam steps /
384 training episodes / 64 evaluations plus 96 fixed-rule tape passes, under one
complete 120 s cap. P28 durably recorded 24 rollouts / 384 Adam steps at this seed
and source before signal 11; B04 same-learner displacement L2=3.647372245788574
from initial L2=29.883094787597656 establishes prior movement capacity. This is
diagnostic exposure, not a new independent seed or an algorithm-effect comparison.
Actual P32 invocation count at freeze=0.

## Reading, prediction and stop

Primary observable: the first reported fatal event's location-bearing Python
frames, if any, with terminal status and last durable work. Technical MEI is
absolute **one operation-locating frame beyond the signal-only record**: that
can identify a concrete boundary for the next technical task. There is no native
return MEI for this diagnostic; B05's 0.25 remains on its missing pair. Matched
tuned current-host headroom remains absent. No baseline is trained or tuned.

DM prediction: a fatal event will recur before the cap and expose at least one
Python operation boundary; confidence low because P28 has only one observed
fault and startup capture can alter timing. Owner prediction: not taken
(unattended). The independent observation unit is one process execution, with
zero new independent training seeds; frames/episodes are not independent trials.

Reading rule:

> A location-bearing fatal stack supports only the active reported call path in
> this execution; it does not identify the corrupting writer or historical cause.
> A fatal event without a usable stack, a timeout or nonreproduction leaves the
> missing context unresolved and never clears P28 or authorizes a retry.
> A complete normal RAW output receives a separate validity review as diagnostic
> execution evidence; it does not replace P28 RAW or form its absent pair.
> Every outcome ends this allocation. Retain terminal facts and durable work;
> no repair, extra probe, STRUCT, new seed, repeat or extension follows.

At or above the technical MEI, recommend only a bounded task at the located
operation if the stack and source support one. Below it, return the precise
missing evidence without inventing a fix. Normal completion is a separate
nonreproduction outcome, not an opposite-sign algorithm effect or runtime cure.
Cap or admission failure limits its dependent facts, with trustworthy narrower
evidence retained under evidence-spec sections 4, 5.1 and 11.8.7.
No performance superiority, mechanism value, historical cause, UAV entry or
direction/Portfolio disposition is within this card. CBSC and FRRIE evidence,
causes, costs and diagnostic outcomes remain separate.

## Scope and decision

Engineering-scope section 4 need: **diagnostic reporting beyond wall/RSS**, for
one invocation's fatal Python/thread stack via the existing interpreter option.
No source, profiler, recovery loop, custom telemetry or framework is added.
Reuse existing supervisor and ordinary retained artifacts. This is pure
collection/execution preparation, not a new coding assignment or comparison arm.
The three CM comparison batches are already exhausted; no fourth is requested.

Options: (a) freeze this single P32 observation because the named retained logs
lack a call path; (b) stop with the same unresolved signal-only evidence; (c)
launch a full pair or speculative repair. Recommend/select **(a)** within P32.
Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Entry owner reviews returned []; 65 CBSC audit rows had no non-empty owner field.
Record the new-card P2 item and audit row without waiting for an owner reply.
CM prepares and accepts the exact literal; Root dispatches/adopts/observes once;
CM collects and technically accepts; DM writes E0 intake, prediction check,
Chinese brief and audit. Root integrates the named commits and routes the next
concrete need. State at card freeze: command preparation pending, no run.
New-card item: [20260908-cbsc-001](../../portfolio/owner/inbox/2026-09-08/20260908-cbsc-001.json);
selection audit: [2026-09-08 row 5](../../portfolio/audit/2026-09-08.md#L5).

## DM command acceptance — 2026-09-08

**READY for Root's one P32 dispatch.** Same CM committed/pushed the exact
[handoff](CBSC_B05_FIRST_FAULT_P32_ROOT_HANDOFF_20260908.md) at
`67222c4434e796cdedde44b277d7097959087186` and returned a clean checkout.
DM read the complete handoff and `syntax_acceptance.json` against this card.
All four Python literals AST-parse; shlex exposes the exact selected runtime,
startup option, RAW seed21223 and fresh output/handle. Three local Bash `-n`
inputs accepted the full supervisor command, time/timeout payload and inner
admission/runner chain, exit0/empty stderr (CM reports 1.014s check wall).
These checks were not repeated. Source remains d2753be86, preflight is adjacent,
and the whole 115+5 envelope/collection/stop matches the frozen card. The only
added reporting is the named fatal stack; no implementation-budget breach or
unrequested machinery was observed. Actual target/learner calls remain zero.

Options: (a) accept the exact command and return READY to Root under P32;
(b) return a specific mismatch; (c) add a runtime/import smoke. Recommend/select
**(a)**; no concrete mismatch remains and (c) is unallocated.
Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Owner reviews again returned []; no relevant owner override was found.
Acceptance establishes source/card/command conformance, not runtime success,
cap conformance or fault capture. Root owns actual admission/dispatch/observation;
this same CM collects terminal artifacts and DM applies the diagnostic reading.

## P32 observed result boundary — 2026-09-08

**DIAGNOSTIC_CONTEXT_OBSERVED; allocation ended.** The
[E0](CBSC_B05_FIRST_FAULT_P32_RESULT_EVIDENCE_20260908.md) at
`6042c6a44f4e25e4ac8d16ba8dd56c23fdb5ccaa` (Root integration
`8ff9b0f1be67e6a79e737b06c60f0d8228ee9cca`) records one signal11/exit139
after 15.25 seconds, 799632 KiB RSS and passed fresh admission. Eight fatal
Python frames locate RAW adapter processing in the second initial-EVAL
projection. The raw output directory is empty. Zero training/Adam/policy
evaluation/rule execution is inferred from that source phase; projection
progress is unknown. No result or missing pair is reconstructed.

The [intake](CBSC_B05_FIRST_FAULT_P32_INTAKE_20260908.md) applies the frozen
reading: technical MEI and the stated signal/context prediction are met, with
no native writer or historical-cause attribution. P28 remains INCOMPLETE_RAW.
No retry, source repair, STRUCT or probe was added; CBSC/FRRIE remain separate.
The [owner brief](../../portfolio/owner/briefs/capability_bound_semantic_currentness/2026-09-08_P32.md)
and audit record this boundary. Any native-operation investigation in the
intake is a separate, unallocated next-task recommendation.
