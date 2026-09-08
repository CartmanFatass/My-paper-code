# CBSC P32 diagnostic intake

**DIAGNOSTIC_CONTEXT_OBSERVED; allocation ended.** The one P32 process failed
with signal 11 / exit 139 after 15.25 seconds and supplied the requested fatal
Python call path. Eight frames locate RAW adapter processing during the second
projection of the initial evaluation panel. This is a valid narrow A/RECON
operation-context observation, not a completed learner or a cause/writer finding.
P28 remains INCOMPLETE_RAW with zero complete pairs.

## Inputs, checks and rule applied

Authority: [P32](../../portfolio/handoffs/2026-09-08-p32-cbsc-first-fault-context.md),
`0c6bf8e175632098e46fcff1417d5d3c078962c9`. The
[card](CBSC_B05_FIRST_FAULT_P32_SCIENCE_CARD_20260908.md) was frozen at
`04254e7ffab87e8ea85024f6542d7b88fecb1cfd`, the
[command](CBSC_B05_FIRST_FAULT_P32_ROOT_HANDOFF_20260908.md) at
`67222c4434e796cdedde44b277d7097959087186`, and DM acceptance at
`31ae5138acaad3e745f14162c304ad988ab5efc2`. Root integrated these as
`3503cb0a5909fb2f86fb11c07d568e4fdd05dab3`,
`b2906c5ff974b316be5447fb63f2272014cae122` and
`86ebee3f8b66fbeb4509294703387a7fbbc32eb3`, respectively.
Same-CM [E0 evidence](CBSC_B05_FIRST_FAULT_P32_RESULT_EVIDENCE_20260908.md)
is `6042c6a44f4e25e4ac8d16ba8dd56c23fdb5ccaa`, integrated on main as
`8ff9b0f1be67e6a79e737b06c60f0d8228ee9cca`.

DM read the full E0 against the frozen reading, the actual fatal log,
collection facts and copied supervisor runner, and the relevant bound-source
ranges in `adapters.py`, `engine.py` and `opportunity_credit_b04/run.py`.
Root's execution/collection receipts agree with the E0. Root performed the
accepted launch and exact collection; CM inspected its copied bytes. Neither
CM collection nor source/syntax tests were repeated at intake. Local stdlib
arithmetic checked byte/GiB conversion, frame count and the recorded cap.
No target import, replay, native probe, evaluation or new pair calculation ran.

Card reading applied verbatim:

> A location-bearing fatal stack supports only the active reported call path in
> this execution; it does not identify the corrupting writer or historical cause.
> A fatal event without a usable stack, a timeout or nonreproduction leaves the
> missing context unresolved and never clears P28 or authorizes a retry.
> A complete normal RAW output receives a separate validity review as diagnostic
> execution evidence; it does not replace P28 RAW or form its absent pair.
> Every outcome ends this allocation. Retain terminal facts and durable work;
> no repair, extra probe, STRUCT, new seed, repeat or extension follows.

The first and last clauses apply. A failed scientific process supplied this
diagnostic's primary observable; exit failure does not erase the independent
stack. Evidence-spec sections 4, 5.1 and 11.8.7 limit its conclusion to that
observed context. No B05 performance branch is evaluated.

## Direct observations and source-flow inferences

The actual handle was `cbsc-b05-first-fault-p32-20260908`, PID 2766935,
wsl_4070. Supervisor start/end were 2026-09-08T07:28:36Z / 07:28:52Z;
terminal was failed, exit 139, tmux inactive. Outer GNU time reports **15.25 s**
and **799632 KiB** peak RSS (**818823168 bytes**). The rounded supervisor
duration is 16 s; collection uptime 117 s is an observation age. The fatal
event preceded the 115-second TERM boundary and met the 120-second complete cap.

Adjacent admission passed at 07:28:36.833284Z. Physical and effective available
memory were each 15646052352 bytes (**14.571521759033203125 GiB**), above 4 GiB.
This is admission evidence, not a memory-cause test. The copied command retains
source d2753be86c12bfa63c404ac2cac513b914371115, RAW seed 21223, the selected
system312 interpreter, CPU FP32/Torch1 and original numeric-library limits.
Startup `-X faulthandler` and the full time/115+5/admission/runner chain match
the accepted literal. P17/P28 version observations are reused; P32 published
no version summary, checkpoint identity or new package metadata.

One fatal report contains eight Python frames. The most recent reports
`RawHistoryAdapter.process`, `omrc_b01/adapters.py:128`, followed by `replay`
at line 93, `engine.build_observations:89`, `engine._project_panel:108`,
`opportunity_credit_b04/run.py:132` and the runner entry frames. The E0 preserves
all eight. At the bound source, line 128 is `for value in appended:`;
engine line 108 is the second `build_observations` call for replay comparison;
run line 132 projects the initial EVAL tapes. The exact tape/token index is
unknown. The 24 listed extension modules are not 24 suspects or evidence
identifying a responsible module. This is no native C backtrace or attribution
of the first invalid memory access.

Direct artifact observations: `raw/` exists and is empty; durable update rows,
checkpoints and summary files are all absent. The only output-parent file is
the admission receipt. Distinct source-order inferences are:

- The fatal path was reached after constructing 384 TRAIN and 32 EVAL tapes,
  action-uniform bookkeeping, model/trainer initialization and initial norm
  computation. No value or parameter displacement was published.
- It preceded the rule panels and the policy-evaluation/training loop. Thus
  rollout updates, Adam steps, sampled training episodes/transitions/decisions,
  policy evaluations and fixed-rule scores reached are **zero by source flow**,
  not serialized terminal counters.
- Adapter projection had begun; its completed tape/token counts are unknown.
  Tape construction and projection are not policy interaction or optimizer steps.

The [exposure record](CBSC_B05_FIRST_FAULT_P32_EXPOSURE_AND_COST_20260908.json)
retains the prospective 48-rollout/768-Adam schedule ceilings and appends these
actual facts without relabelling them as completed exposure. The independent
unit is one process invocation, not eight frames or 416 independent learner
results. Repeated seed 21223 supplies zero new independent training seeds.
There is no endpoint score for `summarize_runs.py`, uncertainty estimation or
an algorithm comparison. STRUCT invocations and new pairs are zero.

## Interpretation, prediction and engineering limits

Technical MEI was one operation-locating frame beyond signal-only evidence.
It is met: one report supplies eight frames and a definite source phase. The
prediction of a fatal event before the cap plus a Python operation boundary
is **met on its stated signal/context terms**. It did not predict or establish
the same corrupting event as P28. Owner prediction: **not taken (unattended)**.

Strongest support is the directly retained stack and its correspondence to the
unchanged source. Strongest limitation is the gap between an active Python
location and a native faulting operation or writer. P28 reached 24 durable
rollouts before its signal-only failure; P32 fails before the learning loop.
Those different observed progress boundaries defeat any assumption that both
signals identify the same fixed optimizer failure. They neither identify the
source of that difference nor show that capture repaired or caused anything.
This execution's fatal event does not require an Adam update in this execution;
model initialization and other earlier native activity still precede it.

The report locates ordinary Python adapter iteration. It supports no specific
line-128 patch, module replacement, hardware diagnosis or runtime cure. A second
identical Python-stack invocation would add little decision value by itself.
No new mechanism/comparator question or causal interpretation required another
literature search. The accepted Python capture documentation supports the
channel, not the source of this observed signal.

Only the card-named diagnostic reporting beyond wall/RSS was used. No source,
framework, extra telemetry, repeated check or engineering-scope section-5 budget
breach was added. P32 invocation-wall sum is 15.25 s for one valid diagnostic
context observation; the earlier local static-check wall was 1.014 s, separately.
Aggregate CPU, scratch and full study critical path remain `resources_unmeasured`.
No per-valid-B-pair cost exists, and CBSC costs are not pooled with FRRIE.

B05's paired MEI 0.25, absent matched tuned headroom and unanswered comparison
remain. Old B04 RAW 12.0375 versus REQUEST_ONLY 12.375, missing STRUCT and two
earlier zero representation gaps remain separate scientific evidence. No new
algorithm support or contradiction is supplied here. DIRECTION mechanism science,
recasts, Portfolio lifecycle/priority and UAV entry remain unchanged.

## Decisions this intake produces

1. **Object / technical:** (a) accept the A/RECON call-path observation with
   explicit cause/writer and source-flow limits; (b) accept a learner result;
   (c) identify the displayed line or a loaded module as the cause.
   Recommend/select **(a)**. The primary diagnostic is readable; learning is not.
2. **Object / selection:** (a) end P32 and return the specific native-operation
   evidence need below for a separate Portfolio allocation; (b) repeat the same
   Python capture or spend the unused cap; (c) patch line 128 or invoke STRUCT.
   Recommend/select **(a)**. No further invocation or source work is selected.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a) for both.
Both actions are reversible; owner flags **none**. Entry/intake owner reviews
returned []; all 67 CBSC audit owner fields were empty. The existing new-card
P2 item `20260908-cbsc-001` remains linked to this card and its appended result.
Ordinary diagnostic facts produce no additional P1/P2 item or invented reply.
The [Chinese brief](../../portfolio/owner/briefs/capability_bound_semantic_currentness/2026-09-08_P32.md)
is this result's owner surface. A/B have no consumption state; only this named
execution allocation has ended.

## Concrete downstream need, not an allocation

No source repair is supported by the current Python frames. If Portfolio
continues technical investment on this runtime path, recommend **one separately
bounded native fatal-site observation at the existing initial RAW projection
boundary**, using an already available native debugger, unchanged source/seed/
runtime/schedule and at most one complete 120-second invocation. The requested
new quantity is the native failing instruction/call context, not proof of the
corrupting writer or a complete historical diagnosis. Availability of that
debugger is not established here; missing capability returns a no-run fact,
without automatic installation or package changes. This is a next-task proposal;
no debugger command, new card, admission or invocation is authorized by P32.

Decision value: direct inspection found no evidenced Python source defect;
another same-channel stack merely repeats the current location. An immediate
full B05 pair would retain up to 600/1200-second limits and could fail without
supporting a repair. The proposed one-call native observation instead targets
the missing operation needed to choose a change. Its known reference cost is
P32's 15.25 seconds; native-debugger overhead and completion time are unknown.
The unchanged learner ceiling remains one arm x 48 x 8 episodes, 768 Adam,
64 policy evaluations and 96 rule passes, not zero-learner diagnostic work.
The proposed 120 seconds is a complete cap, not a completion forecast.

This does not make native diagnosis a prerequisite for a separately justified
credible B path. The scientific next discriminator remains a complete fresh
RAW/STRUCT native-return pair. Root returns this direction-local technical
recommendation to Portfolio; selection of a new investment belongs there.
