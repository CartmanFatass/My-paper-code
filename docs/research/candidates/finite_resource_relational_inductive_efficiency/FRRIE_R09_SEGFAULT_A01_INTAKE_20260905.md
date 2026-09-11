# FRRIE R09 fatal-signal A01 intake — 2026-09-05

Status: `VALID_A_RECON / A01_DIFFERENT_ORIGINAL_FAILURE / R09_SIGSEGV_CAUSE_UNRESOLVED`.
Object: `FRRIE-R09-SEGFAULT-A01-20260905`. This diagnostic is complete; no B result is added.

## What DM checked

DM read the frozen A01 card, the original R09 incomplete intake/E0, CM's pushed prospective
record `cbdd0552d` and complete terminal collection `04d634f3f`, including the actual supervisor
command, complete raw stdout/stderr, 504-byte receipt, source/runtime/status/artifact inventory.
These were checked against the original source, entry, seed, fixed pdb input, host/interpreter,
faulthandler flag, one-invocation limit, fresh admission and 60+5-second bound. No source,
test, learner or observation run was performed by DM during intake.

The owner-confirmed continuation actually reached ordinary remote acceptance and completion.
No fresh platform refusal occurred. Historical refusal evidence stays preserved in the handoff
and `FRRIE_R09_SEGFAULT_A01_RESUME_20260905.md`; no historical scientific record is removed.

The sole invocation ran original source **43eec21e9584c83e5e8d940402d7e4570b454e59**, not
the newer trainer on local main. It used the fresh exact-SHA worktree and configured original
node/interpreter. CM observed no prior accepted R09 fatal-signal A01 before launch, and no
replacement or duplicate computation was issued. Fixed q then EOF ended pdb after its re-entry
at module line 1; no cont/step was supplied to start a second scientific computation.

## Rule applied verbatim

> `A01_DIFFERENT_ORIGINAL_FAILURE`: No earlier match and a different original exception/signal
> occurs before natural completion or the cap. Preserve it separately, without calling it the
> original failure.

This is the first matching branch. The declared reconstruction is represented, so
`A01_INVALID_RECONSTRUCTION` does not apply. No original Python SIGSEGV recurred or fatal
faulthandler stack was retained, so neither fatal-signal branch applies. The ordinary original
exception occurred before the cap; this is not `A01_NO_FATAL_WITHIN_BOUND` or natural completion.

The observed exception is `AttributeError: 'tuple_iterator' object has no attribute 'name'`
at CPython `dataclasses.py:1245`, `_asdict_inner`, evaluating `getattr(obj, f.name)`. The stack
places it in `R02EvaluationAddress.canonical_bytes()` while constructing the uplink part of an
evaluation tape, before the source's output-directory creation and adapter/model/learner setup.
This is a directly observed execution failure on the recorded chain. It does not reproduce the
original SIGSEGV, prove that signal's cause or establish that both failures share a cause.

The fixed debugger captured `FIELD_TYPES = ('R02EvaluationAddress', 'tuple_iterator', None)`.
Its class inventory contained twelve actual `Field` entries with matching names. The local
loop variable and class inventory differ in that observed context. Why they differ is unknown;
the log does not prove malformed class metadata, a particular code defect, debugger causation,
native memory corruption or interpreter/host responsibility.

The later `seed_block` AttributeError and `number` NameError are failures of the historical
fixed observation commands, after the original exception. They do not replace the original
failure or invalidate this card, which requires the original failure and available context,
not successful capture of those inapplicable address/counter locals. The retained stack is an
ordinary exception/pdb stack, not a faulthandler fatal-signal stack.

## Actual counts, receipts and cost

| quantity | retained observation |
| --- | --- |
| accepted task | `frrie_r09_segfault_a01_43eec21e_20260905` |
| source / node | `43eec21e9584c83e5e8d940402d7e4570b454e59` / `wsl_4070`, observed `LAPTOP-U9TDKC8A` |
| interpreter | `/home/wu/.venvs/hmasd/bin/python`, CPython 3.10.21 |
| supervisor PID | 1683892 |
| start / end | `2026-09-05T16:21:23Z` / `2026-09-05T16:21:42Z` |
| supervisor execution wall | **19 seconds**; not later inventory uptime of 256 seconds |
| original termination | uncaught AttributeError before cap |
| debugger / supervisor termination | separately exit 0, finished, tmux inactive |
| fresh actual-node admission | assessed `16:21:23.090023Z`; physical and effective each **15,422,091,264 bytes**, both above 4 GiB |
| artifacts | only 504-byte admission under the direction temp tree; requested exp directory and summary absent |
| actual draws / learner / evaluator / contact / exposure counts | unmeasured, not zero |
| runtime peak RSS / per-arm timing / scratch peak | `resources_unmeasured` |

The receipt is joined immediately by `&&` to the original-chain invocation. Source status is
clean and unchanged after collection. The card's 60-second TERM horizon and at most 5-second
grace were not reached. No scientific return or six-branch R09 publication exists.

Nominal exposure remains the source's target: 128 updates, LR 0.003, nominal 0.384 against
initial half-range 0.05, ratio 7.68. This is not a claim of achieved learner exposure. Missing
optional resource peaks do not annul this non-resource A observation. The 19 seconds are one
valid diagnostic's cost, separate from the original R09 16-second incomplete B invocation and
from the earlier valid B results. No new valid-B denominator or pooled performance is created.

No source/test change, suite, wrapper, runtime change or repair was added. The existing card
names stdlib fatal-exception telemetry; no new engineering facility was built. Formal-sized
end-to-end publication-test coverage remains an open engineering item, not exercised here.

## Bounded reading and predictions

The strongest support for the accepted A reading is the full original exception traceback,
actual debugger state and matching source/command/admission, observed before the cap. The
strongest limitation is that the targeted SIGSEGV did not recur and the exact address values
and completed draws were not captured. This is a different observed fault, not a repair,
exoneration, recurrence-with-frame result or diagnosis of historical R04/attempt02.

DM's low-confidence prediction `A01_FATAL_SIGNAL_WITH_FRAME` is **contradicted** by this
different original exception. It is not a partial match merely because an ordinary traceback
exists. Owner prediction: **not taken (unattended)**; current owner review CLI returned `[]`
again at the clean intake boundary `2026-09-05T16:27:07Z`. R09's native-return prediction
remains unscored. No owner answer is imputed.

The accepted mechanism-level evidence in DIRECTION remains unchanged. R06's selected root-1
N15 gap was +0.005548293532 against MEI 0.005; R07's second literal path was -0.001948094523,
within MEI, and neither supplied a material N9 benefit. R08's interaction was within MEI and
reused root-1 evidence. The diagnostic supplies no support or contradiction to projection's
native value. A tuned same-information/upper-reference host headroom pair remains absent.

## Decisions this intake produces

Options: (a) accept the complete A01 observation as a different original failure, retain the
old SIGSEGV cause as unresolved; (b) treat debugger exit 0 as a fix or B success; (c) call the
ordinary traceback the predicted fatal-signal frame; (d) merge historical causes from similar
error text.

Recommendation and selection: **(a)**, object tier, kind `technical`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
The card is unchanged; one complete A observation has been taken in and the assigned slice ends.

The next proposed engineering discriminator is **capture of the actual evaluation address and
the local field-iteration state at this observed serialization failure**, if Root selects
continued diagnosis. Existing fixed pdb commands assumed a different address shape and did not
retain these values. A separately bounded observation can target that precise missing fact
without changing learner/tapes/seed semantics; the present evidence does not yet identify a
specific source repair. This is direction-local advice returned to Root, not a selected second
invocation, a Portfolio action or a new permission requirement. No blind full R09 retry, R10,
new Pro round or lifecycle change is taken in this slice.

## Recoverability and Root-owned surfaces

CM branch `codex/cm-frrie-a01-resume-20260905` supplied `cbdd0552d` then `04d634f3f`; DM
fast-forward integrated both into `codex/dm-frrie-a01-resume-20260905` and immediately pushed.
The shared tracker adopted the sole handle, delivered terminal to CM/DM directly and received
DM's terminal ACK; no active diagnostic remains. Remote witnesses stay at
`/home/wu/.agent-tasks/frrie_r09_segfault_a01_43eec21e_20260905/` and the fresh cwd stated
in the CM evidence. Historical evidence and frozen card bytes are untouched.

Root owns Portfolio/audit/owner console and receives this intake, the Chinese brief text and
the existing P2 item `20260905-frrie-017` for actual execution tracing. P3/P4 are not recreated;
DM writes no shared owner JSON or replies. Append-ready technical row for Root:

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T16:27:07Z | finite_resource_relational_inductive_efficiency | object | technical | (a) retain different original failure and unresolved SIGSEGV; (b) infer fix/B success; (c) call ordinary stack fatal frame; (d) merge old causes | (a) VALID A/RECON A01_DIFFERENT_ORIGINAL_FAILURE, 19s, no new B result | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_SEGFAULT_A01_INTAKE_20260905.md` | none | |

Evidence: adjacent `FRRIE_R09_SEGFAULT_A01_RESULT_EVIDENCE_20260905.md`,
`FRRIE_R09_SEGFAULT_A01_CM_RECORD_20260905.md` and raw COMMAND, ADMISSION, TERMINAL_LOG and
INVENTORY files; original card, `FRRIE_R09_INCOMPLETE_INTAKE_20260905.md` and
`FRRIE_R09_RESULT_20260905.md` retain the separate historical meanings.
