# FRRIE R09 failure-capture A02 intake — 2026-09-06

Object `FRRIE-R09-SEGFAULT-A02-CAPTURE-20260906`
([card](FRRIE_R09_SEGFAULT_A02_CAPTURE_SCIENCE_CARD_20260906.md),
[selection](FRRIE_R09_SEGFAULT_A02_SELECTION_INTAKE_20260906.md)). Direction Manager: the Claude
research hub. Prediction on record before the launch: `A02_SERIALIZATION_FAILURE_CAPTURED`.

## Provenance (observation)

| Fact | Value |
| --- | --- |
| Node / task | `wsl_4070` (LAPTOP-U9TDKC8A) / `frrie_r09_segfault_a02_43eec21e_20260906`, PID 1947752 |
| Worktree / HEAD | `/home/wu/hmasd-worktrees/frrie-r09-segfault-a02-43eec21e-20260906`, detached at `43eec21e9584c83e5e8d940402d7e4570b454e59`, clean |
| Interpreter | CPython 3.10.21 (uv-managed build, `Clang 22.1.3`), `hash_randomization=1`, `-X faulthandler`, module-mode `pdb -c continue` |
| Staged input | `FRRIE_R09_SEGFAULT_A02_PDB_COMMANDS_20260906.txt`, sha256 `f644c1e5…` verified on the node, LF, 15 lines |
| Admission | passed; physical = effective available 15,673,655,296 B (14.6 GiB) at 2026-09-06T14:39:24Z |
| Command | exactly the card's frozen invocation, launched once |
| Supervisor | started 22:39:24 +08:00, exited 22:39:57 +08:00, duration 33 s, exit code 0 (pdb's own exit after `q`; the original chain did not complete) |
| Output root | created, empty (`inventory`) |
| Evidence | `FRRIE_R09_SEGFAULT_A02_TERMINAL_LOG_20260906.txt` (sha256 `46a8d8f4…`), `FRRIE_R09_SEGFAULT_A02_ADMISSION_20260906.json`, `FRRIE_R09_SEGFAULT_A02_INVENTORY_20260906.txt` |

## What happened (observation)

The chain raised, before natural completion and inside the 60 s horizon, a third original failure
distinct from both R09's SIGSEGV and A01's `AttributeError`:

```
experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core.ContractError:
semantic RNG basin must be absent or in [0,1]
```

at `rng.py:171 validate()` ← `rng.py:204 canonical_bytes()` ← `rng.py:251 block()` ←
`rng.py:273 uniform_float32()` ← `tapes.py:373 generate_episode_tape()` (the parent training-tape
generator, uplink-uniform assignment) ← `b01_contact_r02/tapes.py:247 production_training_inputs()`
← `experiment.py:242 execute()`.

Where this sits on the chain: past the point where A01 died. The 512 production evaluation tapes
(`execute()` line 166, A01's failure site) were built without error; the output root was created
(line 175, which neither R09 nor A01 reached); the native adapter build and load at line 178 and
the torch import at line 199 were passed; the failure came in the *training* tape construction
for update 0, in a different address class (`rng.py`'s semantic RNG address) than A01's
`R02EvaluationAddress`.

What the check means: `validate()` raises when a coordinate is present and is not exactly of type
`int` in `[0, upper)`. `basin` is set from `for basin in range(EVENT_BASINS)` with `EVENT_BASINS = 2`
(`tapes.py:24, 329`) or left absent; on the uplink path at line 373 it should be absent. A present
`basin` that is not an `int` in `[0, 1]` at that site cannot be produced by the source as written;
the same code built training tapes for R06, R07 and R08 at roots 1 and 2. This is a second
observed instance of a Python object slot holding the wrong value during the address-hashing
loops, after A01's `tuple_iterator` in a field iterator.

Postmortem capture: pdb entered postmortem at `rng.py:171`, not `_asdict_inner`, so every
name-bound capture expression failed with its own `NameError` (recorded separately from the
original exception, as the card requires); `PY` printed the interpreter facts; `up 5` landed on
the `production_training_inputs` generator frame, where `episode` is undefined; both `where`
listings are retained. Nothing was captured about the offending `basin` value.

## Reading rule applied (card, first match)

1. `A02_INVALID_RECONSTRUCTION`: no. Source sha, entry, seed, node, interpreter, faulthandler,
   input digest and fresh admission are all represented; one invocation.
2. `A02_SERIALIZATION_FAILURE_CAPTURED`: no. The postmortem frame is not `_asdict_inner` and the
   capture expressions errored.
3. `A02_SERIALIZATION_FAILURE_UNCAPTURED`: no. The exception class (`ContractError` from
   `validate`) is not A01's class.
4. `A02_FATAL_SIGNAL_WITH_FRAME` / `UNLOCALIZED`: no fatal signal.
5. **`A02_DIFFERENT_ORIGINAL_FAILURE`: yes.** Preserved separately; not called the original
   failure; not a fix, not a B result.

Bounded reading: three invocations of this chain (R09, A01, A02) produced three different
original failures at three different points, all inside the address-hashing tape-construction
loops (R09 at 16 s with no traceback; A01 at 19 s in evaluation tapes; A02 at 33 s in training
tapes, after the evaluation tapes had succeeded). The failures are not reproducible in form, and
each of the two Python-level ones shows an object slot holding a value the source cannot produce.
This is consistent with runtime corruption of Python objects on this node/interpreter under this
chain, and inconsistent with a deterministic source defect in either address class. It does not
identify the corrupting agent (interpreter build, an imported C extension, pdb tracing, or the
host) and does not prove the three failures share a cause.

DM prediction `A02_SERIALIZATION_FAILURE_CAPTURED`: **contradicted** (different failure, nothing
captured). Owner prediction: not taken (unattended). R09's native-return prediction remains
unscored. The frozen third-root B card is unchanged and still unexecuted.

## Cost and exposure

33 s supervisor wall, one process, zero learner work claimed; the R09 target's exposure is
unchanged. Card cap 60 s + 5 s respected. Total diagnostic spend on this failure so far: 19 s
(A01) + 33 s (A02) + two read-only maps.

## Decisions this intake produces (object tier, owner absent)

Options: (a) accept the A02 observation as a valid A/RECON with branch
`A02_DIFFERENT_ORIGINAL_FAILURE`, retain both earlier failures as unresolved; (b) call the exit
code 0 a completion; (c) merge the three failures into one cause from their common location.
Selection: **(a)**, kind `technical`, `OWNER_DELEGATED (unattended, 2026-09-03 instruction)`.

Next object (selection, per the card's branch consequence "return to this node with the new facts;
no automatic third capture"): the DM's options are (1) a bounded runtime-isolation probe that
builds the same production tapes at 43eec21e in separately launched arms varying only the
suspected agents (no torch import and no pdb; torch imported first; the same under pdb), each
repeated within a short cap, zero learner; (2) an outcome-blind full R09 attempt without pdb
(the original R09 and both diagnostics ran under module-mode pdb; a plain run of this chain at
seed 3 has never been made); (3) park the third-root family. Recommendation: **(1)** first,
because it separates interpreter, extension and tracing hypotheses in minutes and its result
decides whether (2) is credible or the node itself is suspect; (2) is the runner-up and follows
directly if (1) shows no corruption in any arm. Selection: **(1)**,
`OWNER_DELEGATED (unattended, 2026-09-03 instruction)`, kind `selection`, owner flag `none`;
the card is `FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_SCIENCE_CARD_20260906.md` (frozen next), with
a CM objective for Grok Build (new diagnostic source only; no change to any R09 path) and hub
review; no reviewer is required because no shared surface changes.

Owner brief (Chinese): `docs/research/portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-06_R09-A02-capture.md`.

scope: none
