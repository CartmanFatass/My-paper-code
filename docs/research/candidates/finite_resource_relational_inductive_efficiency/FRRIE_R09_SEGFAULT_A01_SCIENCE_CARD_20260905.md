Claim: one bounded recorded-source R09 reconstruction can observe whether the fatal signal recurs and, if available, localize its Python stack, at A/RECON ceiling.
Binding structure: `systems / information flow` — this diagnoses execution of the paired MARL input/learner path; the signal itself supplies no partial-observation or non-stationarity mechanism claim.

# FRRIE R09 fatal-signal reconstruction A01 — 2026-09-05

Status: `FROZEN / A_RECON / SINGLE_DIAGNOSTIC_REQUIRED`.
Object: `FRRIE-R09-SEGFAULT-A01-20260905`.
This is distinct from the historical R04 reconstruction A01 and from a fresh scientific R09 attempt.

## Evidence, question and ceiling

Original task `frrie_b01_contact_r09_43eec21e` ended14:32:49Z after16 seconds with
exit139 and a Python+pdb fatal-signal/core notification. There is no Python traceback,
summary or specified experiment directory. Work reached and exact frame are unknown.
CM E0 `5dd4ae8ed9b8a7c6d3f399ce4d8757df325eeb74` preserves log, receipt and bounded
kernel excerpt. No checked core artifact is available to read offline.

Question: does that fatal signal recur within60 seconds of the same recorded command chain,
and does CPython's existing faulthandler expose a usable stack? This is fault observation,
not a repair, a native-return comparison or a shortened B run. A signal-location observation
does not prove a root cause, establish sameness to r04/attempt02 or prove code versus host
responsibility. Those historical causes remain separate.

No scientific root3 outcome has been inspected. The ordinal root3 selection and all frozen
R09 scientific meanings remain. The original incomplete invocation is not rehabilitated.
Any summary unexpectedly produced here remains diagnostic evidence and is never upgraded
into B or used to score the R09 native-return prediction.

## Exact protected reconstruction and deliberate differences

Pin source **43eec21e9584c83e5e8d940402d7e4570b454e59** and original configured node
**wsl_4070 / LAPTOP-U9TDKC8A**, interpreter /home/wu/.venvs/hmasd/bin/python resolving to
CPython3.10.21. CPU FP32/Torch1/native32 remains assigned. Host/interpreter are part of this
diagnostic boundary; no local/device fallback or runtime replacement.

Use the same module `scripts.run_frrie_b01_contact_r09`, numeric seed3,
root `0000000000000000000000000000000000000000000000000000000000000003`,
label `FRRIE-B09-CONTACT-BLOCK-003`, paired LR0.003, raw initialization, models, tapes,
128-update target, boxes, contact, checkpoint, evaluator, RNG/numerical and publication
code. Do not stub a learner, monkey-patch a function, change tracing semantics beyond the
declared flag, alter inputs or inspect/choose another root.

Only deliberate differences: enable existing CPython **-X faulthandler**, shorten the outer
diagnostic horizon to60 seconds with at most5 seconds TERM grace, and use unique diagnostic
cwd/output/receipt/task. Retain module-mode pdb, the unchanged fixed
`FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt` input, and q/EOF handling.
Invocation after fresh admission is:

`timeout --signal=TERM --kill-after=5s 60s /home/wu/.venvs/hmasd/bin/python -X faulthandler -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 --output-root <diagnostic-output> --admission-receipt <fresh-receipt> --seed 3 < <same-fixed-pdb-input>`

No source change, new wrapper, GDB framework, extra suite or second diagnostic is selected.
Fresh detached exact-SHA worktree prevents reuse of old native/model/tape/output state.
The original task and evidence remain untouched. This is one original-chain reconstruction,
not an isolated-step test whose failing input has already been captured.

## Observations, branches and predictions

Preserve exact source/argv/node/interpreter, actual admission, start/end/supervisor status,
raw stdout/stderr, original signal/exception/normal exit separately from debugger exit,
faulthandler stack if emitted, directory/artifact existence and actual reached counts only
when directly retained. Use existing supervisor/log and simple artifact inventory.
Do not invent zero draws, zero learner work or a failing frame from absent output.
A stack location is observed context, not sufficient causal classification.

No native-effect MEI applies. The diagnostic minimum of interest is one recurring fatal
signal and at least one usable Python frame when available; this categorical target has
no native-return threshold. The R09 scientific MEI0.005 is unchanged and not evaluated here.
Host headroom/tuned baseline references remain absent and irrelevant to this diagnostic.

| branch | first-match rule and bounded reading |
| --- | --- |
| `A01_INVALID_RECONSTRUCTION` | Declared source, original entry/seed/pdb/input, pinned node/interpreter, faulthandler option or fresh >=4GiB admission is not represented; an undeclared change or duplicate invocation occurs. Incomplete diagnostic, no diagnosis. |
| `A01_FATAL_SIGNAL_WITH_FRAME` | Original Python SIGSEGV recurs within the diagnostic horizon and usable faulthandler Python frame(s) are retained for that process. Report exact stack and ordering; the signal recurred, but sameness of original cause and component responsibility remain unproved. |
| `A01_FATAL_SIGNAL_UNLOCALIZED` | Original Python SIGSEGV recurs but no usable stack is retained. Record the recurring signal only; missing localization remains open. |
| `A01_DIFFERENT_ORIGINAL_FAILURE` | No earlier match and a different original exception/signal occurs before natural completion or the cap. Preserve it separately, without calling it the original failure. |
| `A01_NO_FATAL_WITHIN_BOUND` | No earlier match; original chain reaches its60-second limit without an earlier original failure, or completes normally. Report cap versus natural completion explicitly. Failure was not reproduced within this bound; this is not a fix or valid B result. |

A transport/observation loss with unknown terminal evidence leaves intake pending on the
same supervisor; it does not authorize a replacement or a branch from guessed status.
Missing optional resource measurements are resources_unmeasured. Original pdb exceptions
must be separated from its own postmortem command errors and terminal reentry.

DM predicts **A01_FATAL_SIGNAL_WITH_FRAME**, low confidence: the source/root and startup
chain are fixed and the original failure occurred well inside the bound; transient process/
tracing/runtime behavior remains a competing explanation. A different failure or no fatal
signal contradicts recurrence; recurrence without a frame is only a partial prediction
match. Owner slot: **not taken (unattended)**. No standalone prediction inbox.

## Exposure, cost, stops, scope and handoff

Exposure reference is the unchanged original target:128 updates, LR.003, nominal .384,
initial half-range.05, ratio7.68, tight half-box.04. Actual reached initialization/contact/
learner exposure is unknown unless directly retained. The nominal index is not a displacement
bound, and this diagnosis makes no completed-learner claim. It introduces zero additional
optimizer steps into the original target; its early termination can leave partial work.

Not a sweep. Original failure cost16 seconds is the planning observation. The whole
diagnostic cap is **60 seconds plus at most5 seconds grace**, allowing several times the
observed failing interval without requiring the roughly15-minute full scientific assignment.
Every arm still retains its original4-hour cap; total diagnostic wall is bounded by65 seconds.
Actual cost is recorded separately from valid B compute and from the original16 seconds.
Stop at first original fatal/exception, natural completion or cap; never automatically continue
or issue a second command because a preferred failure was absent.

Immediately before this sole invocation run actual-node admit-memory, requiring both
physical/effective >=4GiB, joined by && to the command before scientific state. Use configured
detached agent-task, unique paths, exact committed/pushed source. Current remote-first route
is already pinned to the original node. Do not relocate a live process.

Named engineering §4 need: **fatal-exception stack telemetry**, using the existing CPython
-X faulthandler option to observe the missing failure frame, alongside already-existing
fixed pdb observation. No project source facility/framework is built; no new source, test,
registry, guard, retry/resume, incident tree, retention service or compatibility shim.
The R09 A28/D15 source remains unchanged; this diagnostic does not exploit the reuse exception
to add machinery or silently expand the scientific object.

CM owns exact launch/collection/technical evidence with the current reusable child chain.
No implementer/reviewer rewrite or repeat of the passed focused suite is needed for this
source-unchanged flag-only diagnostic. If reproducing a fault later suggests a repair, return
the exact observed failing step before any new source or scientific attempt is selected.
CM hands accepted task/node/SHA/cwd/output/receipt/bound directly to
`/root/tracker_tl_experiments` and DM `/root/dm_amx_frrie_continue`; tracker observes the
same handle and wakes DM/CM at terminal/loss/bound. No ACK is a launch gate.
