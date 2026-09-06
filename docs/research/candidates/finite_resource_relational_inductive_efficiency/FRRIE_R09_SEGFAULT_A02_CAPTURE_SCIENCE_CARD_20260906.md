Claim: one bounded recorded-chain R09 reconstruction with corrected postmortem capture can record, if the serialization failure recurs, the actual evaluation address and the field-iteration state at the failing frame, and, if the fatal signal recurs instead, its faulthandler stack, at A/RECON ceiling.
Binding structure: `systems / information flow` — this diagnoses execution of the paired MARL input/learner path before any learner work; it supplies no partial-observation or non-stationarity mechanism claim.

# FRRIE R09 failure-capture reconstruction A02 — 2026-09-06

Status: `FROZEN / A_RECON / SINGLE_DIAGNOSTIC_REQUIRED`.
Object: `FRRIE-R09-SEGFAULT-A02-CAPTURE-20260906`.
Predecessor: `FRRIE-R09-SEGFAULT-A01-20260905` (valid, branch `A01_DIFFERENT_ORIGINAL_FAILURE`).
This is not a repair, not a fresh scientific R09 attempt, and not a second A01.

## Evidence, question and ceiling

- Original task `frrie_b01_contact_r09_43eec21e` ended after 16 s with exit 139 (SIGSEGV), no
  Python traceback, no output directory ([R09 incomplete intake](FRRIE_R09_INCOMPLETE_INTAKE_20260905.md)).
- A01 re-ran the same chain under `-X faulthandler` and module-mode pdb and, after 19 s, observed a
  different original failure: `AttributeError: 'tuple_iterator' object has no attribute 'name'`
  raised in CPython's `dataclasses._asdict_inner` (line 1245) called from
  `tapes.py:96 canonical_bytes` during the uplink-uniform assignment at `tapes.py:216`, before
  the output directory was created. The fixed pdb command file assumed the B01 training-tape
  address shape, so the address and the failing field object were not captured
  ([A01 intake](FRRIE_R09_SEGFAULT_A01_INTAKE_20260905.md), [terminal log](FRRIE_R09_SEGFAULT_A01_TERMINAL_LOG_20260905.txt)).
- The read-only engineering map of the failure chain
  ([FRRIE_R09_FAILURE_CHAIN_MAP_20260906.md](FRRIE_R09_FAILURE_CHAIN_MAP_20260906.md), Grok Build
  on the detached worktree at 43eec21e) finds: a single `asdict` call site (`tapes.py:96`) on a
  validated frozen slotted dataclass; no shadowing or monkeypatch of `dataclasses.fields`; the
  class field dict was 12 proper `Field` objects in A01; the event-time loop of the same tape
  had already serialized the same class successfully before the failing uplink call; no native32
  build, `ctypes.CDLL` or torch op runs before the production tapes (256 episodes × rosters 9
  and 15) are built, only the import-time libtorch and numpy loads; the R09 source bytes on the
  failing path are identical between 43eec21e and current `main`; and the pdb expressions that
  would capture the missing state. No static explanation for a `tuple_iterator` field object
  exists in the source bytes.

Question: under the same recorded command chain, node, interpreter and source, does an original
failure recur within 60 s, and when it is the serialization failure, what are (a) the actual
`R02EvaluationAddress` being serialized, (b) the local field-iteration state in `_asdict_inner`
(`f`, the `fields` name, `fields(obj)` re-evaluated, the unfiltered class field values, the
instance-versus-class identity of `__dataclass_fields__`, `__slots__`, the partial `result`), and
(c) the `evaluation_tape` loop indices; when it is a fatal signal, what faulthandler stack is
emitted. This is fault observation. A captured address or object does not by itself prove a root
cause, sameness with the original SIGSEGV, or code-versus-host responsibility.

## Exact protected reconstruction and the one deliberate difference

Pin source **43eec21e9584c83e5e8d940402d7e4570b454e59** (the launch sha of R09 and A01; `main`
carries changed `b01/` training files on the import graph, so `main` is not the same chain), the
original node **wsl_4070 / LAPTOP-U9TDKC8A**, interpreter `/home/wu/.venvs/hmasd/bin/python`
(CPython 3.10.21), CPU FP32, one compute thread. Same module `scripts.run_frrie_b01_contact_r09`,
seed 3, root `…0003`, label `FRRIE-B09-CONTACT-BLOCK-003`, paired LR 0.003, unchanged models,
tapes, evaluator, RNG and publication code. `-X faulthandler`, module-mode `pdb -c continue`,
60 s outer horizon with at most 5 s TERM grace, fresh detached exact-sha worktree, unique
cwd/output/receipt/task names, fresh ≥ 4 GiB admission joined by `&&`.

The only deliberate difference from A01 is the postmortem command input:
`FRRIE_R09_SEGFAULT_A02_PDB_COMMANDS_20260906.txt` (beside this card; sha256 recorded in the
launch record) replaces the R04-era file. It is a frozen request input, not source; it is staged
on the node at its declared digest (AGENTS.md §5). Its commands, in order:

```
where
p ("PY", __import__("sys").version, __import__("sys").flags)
p ("FIELD_TYPES", type(obj).__name__, type(f).__name__, getattr(f, "name", None))
p ("F_LOCAL", repr(f), type(f).__module__, id(f), getattr(f, "name", None), getattr(f, "_field_type", None))
p ("FIELDS_FN", fields, getattr(fields, "__module__", None), id(fields), fields is __import__("dataclasses").fields)
p ("RESULT_SO_FAR", len(result), [r[0] for r in result])
p ("FIELDS_RESULT", [(type(x).__name__, getattr(x, "name", None), id(x)) for x in fields(obj)])
p ("VALUES_NOFILTER", [(type(x).__name__, getattr(x, "name", None), id(x), getattr(x, "_field_type", None)) for x in obj.__dataclass_fields__.values()])
p ("INSTANCE_VS_CLASS", obj.__dataclass_fields__ is type(obj).__dataclass_fields__, id(obj.__dataclass_fields__), id(type(obj).__dataclass_fields__))
p ("SLOTS", type(obj).__slots__)
p ("ADDRESS", obj.seed_label, obj.roster, obj.episode, obj.kind, obj.basin, obj.event_ordinal, obj.slot, obj.public_role, obj.role_local_index, obj.sender, obj.receiver, obj.draw)
up 5
p ("TAPE_LOOP", seed_label, roster, episode, slot, sender, receiver, role, local)
where
q
```

Every `p` is a read; none mutates state. If the postmortem frame is not `_asdict_inner`, the
name-bound expressions fail with their own pdb errors, which are recorded separately from the
original exception (A01 rule). `up 5` from `_asdict_inner` lands on `evaluation_tape`
(`asdict` → `canonical_bytes` → `block` → `uniform_float32` → `evaluation_tape`); the historical
`up 6` is not used.

Frozen invocation after fresh admission (`WT` = the detached worktree, `IN` = the staged command
file):

```
timeout --signal=TERM --kill-after=5s 60s /home/wu/.venvs/hmasd/bin/python -X faulthandler -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 --output-root WT/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_segfault_a02 --admission-receipt WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_segfault_a02_admission.json --seed 3 < IN
```

No source change, wrapper, GDB, malloc debugging, extra suite or second invocation is selected.
The A01 worktree, task and evidence remain untouched.

## Observations, branches and predictions

Retain exact source/argv/node/interpreter, admission, supervisor start/end/exit, raw stdout and
stderr, the original exception or signal separately from pdb's own command errors and exit, the
faulthandler stack if any, the directory/artifact inventory, and the wall from the supervisor.
Do not invent counts from absent output.

| branch | first-match rule and bounded reading |
| --- | --- |
| `A02_INVALID_RECONSTRUCTION` | Declared source, entry, seed, node, interpreter, faulthandler, command-file digest or fresh ≥ 4 GiB admission not represented; undeclared change or duplicate invocation. No diagnosis. |
| `A02_SERIALIZATION_FAILURE_CAPTURED` | An exception is raised inside `dataclasses._asdict_inner` / `canonical_bytes` within the horizon and `ADDRESS`, `F_LOCAL` and at least one of `FIELDS_RESULT` / `VALUES_NOFILTER` print without a pdb error. Record the address, the anomalous object, the partial `result`, and whether the class field dict itself holds a non-`Field` value (object-level corruption visible at Python level) or only the re-iterated `fields(obj)` does. Classification of cause remains open. |
| `A02_SERIALIZATION_FAILURE_UNCAPTURED` | The same class of exception recurs but the capture commands themselves error. Record the recurrence and the exact pdb errors; the missing state stays open. |
| `A02_FATAL_SIGNAL_WITH_FRAME` | A fatal signal (SIGSEGV or other) terminates the interpreter within the horizon and faulthandler emits at least one usable Python frame. Record the stack; the original R09 signal recurred, cause unproved. |
| `A02_FATAL_SIGNAL_UNLOCALIZED` | Fatal signal without a usable stack. Record the signal only. |
| `A02_DIFFERENT_ORIGINAL_FAILURE` | No earlier match and another original exception or signal occurs before completion or the cap. Preserve separately. |
| `A02_NO_FATAL_WITHIN_BOUND` | The chain reaches the 60 s limit or completes without an original failure. State cap versus completion. Two of three runs of this chain then differ from the third; the failure is not reproducible on demand under this chain. Not a fix, not a B result. |

What each branch changes next (object tier, DM): `CAPTURED` → the hub reads the captured state
before selecting either a targeted repair proposal (only if the state names a source-level cause)
or a bounded runtime-isolation probe (production tape construction with and without the
import-time torch load); no blind full R09 retry. `FATAL_SIGNAL_*` → the runtime-isolation probe
becomes the next discriminator. `NO_FATAL_WITHIN_BOUND` → an outcome-blind full R09 attempt at a
new sha, with `-X faulthandler` retained and no pdb, becomes the credible path (§8 post-learner
and credible-alternative clauses), with the intermittency recorded. `UNCAPTURED` / `DIFFERENT` →
return to this node with the new facts; no automatic third capture.

DM prediction: **`A02_SERIALIZATION_FAILURE_CAPTURED`**, low-to-moderate confidence, with these
sub-predictions: the failure is again at the uplink assignment for roster 9 within the first few
episodes; `FIELDS_FN` is the stdlib function; `VALUES_NOFILTER` shows 12 proper `Field` objects
(the class dict is clean); `FIELDS_RESULT` or `F_LOCAL` shows the non-`Field` object, pointing at
a corrupted iteration or heap rather than Python-level shadowing. A recurrence of the original
SIGSEGV, or no failure within the bound, contradicts the primary prediction. Owner slot: **not
taken (unattended)**. R09's native-return prediction remains unscored.

## Exposure, cost, stops, scope and handoff

Exposure reference is the unchanged R09 target (128 updates, LR 0.003); actual reached learner
exposure is unknown unless directly retained; no learner claim is made. Not a sweep. Whole
diagnostic cap **60 s plus at most 5 s grace**; planning observations are A01's 19 s and R09's
16 s. Stop at the first original failure, natural completion or cap; never issue a second
command because a preferred failure was absent. Fresh admit-memory (physical and effective ≥ 4
GiB) on the executing node immediately before the invocation, joined by `&&`.

Named engineering §4 need: **fatal-exception stack telemetry** through the existing CPython
`-X faulthandler` option plus fixed read-only pdb postmortem commands (the same need A01 named).
No project source, test, guard, registry, retry or telemetry facility is built or changed; the
R09 source bytes at 43eec21e are unchanged.

Execution: the hub's `hmasd-experiment-operator` creates the detached worktree at 43eec21e on
wsl_4070, stages the command file at its sha256, runs the admission and the frozen invocation
as one `agent-task` command, and returns the handle; the hub reads the terminal log and takes
the result in. The engineering map and this card are the whole preparation; no CM code task.

scope: none
