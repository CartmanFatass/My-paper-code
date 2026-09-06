Claim: separately launched arms that build the same production tapes as the R09 chain, differing only in whether the torch extension is loaded and whether pdb tracing is active, can observe in which of those conditions the runtime object corruption seen in A01 and A02 appears, at A/RECON ceiling.
Binding structure: `systems / information flow` — a diagnosis of the execution substrate of the paired MARL input path; no mechanism claim.

# FRRIE R09 tape-isolation probe A03 — 2026-09-06

Status: `FROZEN / A_RECON / DIAGNOSTIC_ARMS_REQUIRED`.
Object: `FRRIE-R09-SEGFAULT-A03-TAPE-ISOLATION-20260906`.
Predecessors: A01 (`A01_DIFFERENT_ORIGINAL_FAILURE`), A02 (`A02_DIFFERENT_ORIGINAL_FAILURE`).
This is not a repair, not a fresh R09 attempt, and does not touch any R09 source path.

## Evidence, question and ceiling

Three invocations of the R09 chain at 43eec21e on wsl_4070 (all under module-mode pdb) failed
three different ways inside the address-hashing tape-construction loops: SIGSEGV at 16 s
(R09), `tuple_iterator` where a dataclass `Field` should be at 19 s in the evaluation tapes
(A01), a present `basin` that is not an `int` in `[0, 1]` at 33 s in the training tapes after the
evaluation tapes had succeeded (A02). The source cannot produce either Python-level value; the
same modules built training tapes for R06 to R08. The engineering map found the only loads
preceding the tapes to be import-time libtorch and numpy; the map also confirmed the parent
`tapes.py` and `rng.py` import no torch. All three failures happened under `sys.settrace`
(pdb); a plain run of this chain at seed 3 has never been made.

Question: when the same tape work is done in a process that (T0) never imports torch and runs no
tracer, (T1) imports torch first (as the runner's import graph does) and runs no tracer, and
(T2) is T1 under module-mode `pdb -c continue`, in which arms does an original exception or
fatal signal occur within the cap, and where? This is fault observation on the substrate. An arm
that fails does not prove which library or which line corrupts memory; an arm that passes does
not prove the substrate is sound for the full chain.

## Exact arms and protected boundaries

Source: the new probe module and runner (below) at the launch sha on `main`; the exercised
modules (`tapes.py`, `rng.py`, `contracts/core.py`, `b01_contact_r02/tapes.py`,
`b01_contact_r02/semantics.py`, `orchestration.py`, `policy.py`) must be byte-identical to
43eec21e, verified by the CM with `git diff 43eec21e <launch sha> -- <paths>` and recorded; if
any differs, the probe runs from a detached 43eec21e worktree with the new files committed on a
branch from 43eec21e instead. Node wsl_4070, interpreter `/home/wu/.venvs/hmasd/bin/python`,
`-X faulthandler` in every arm, one compute thread, fresh admission before each arm, each arm its
own `agent-task`, unique output roots.

Work per repetition (identical in every arm, same root `…0003` and label
`FRRIE-B09-CONTACT-BLOCK-003`): the production training inputs for updates 1 and 2 exactly as
`production_training_inputs` builds them (origin schedules for rosters 9 and 15; 64 episode
tapes per update through the parent `generate_episode_tape`); in T1 and T2 additionally the 512
production evaluation tapes (`evaluation_tape`, rosters 9 and 15 × 256 episodes) built before
the training inputs, matching the runner's order. T0 replicates the training-input body with
the parent-module functions so that no torch-importing module is loaded; the CM verifies with
`sys.modules` that `torch` is absent at the end of T0 and present at the start of T1's work.
Repetitions: 3 per arm, or until the cap. Per repetition and phase the probe records wall,
tape counts, a sha256 over the concatenated canonical bytes of the built tapes (so identical
work across arms and repetitions is checkable), and on failure the full traceback. Peak RSS at
exit. No learner, model, optimizer, native build or checkpoint.

Caps: 300 s per arm (external `timeout --signal=TERM --kill-after=5s 300s`); planning
observations 16 to 33 s to the first failure in the chain, and the evaluation-plus-training
work is of the same order as what A02 completed before failing. Three arms, at most 915 s
total. Not a sweep.

Deliberate differences from the R09 chain: no learner, no native adapter, no `execute()`; the
work is the chain's tape construction alone. T2's stdin is a file containing `q` lines so that a
postmortem prompt does not block.

## Observations, branches and predictions

Retain per arm: argv, node, interpreter, `sys.flags`, `sys.modules` membership for `torch` and
`numpy`, versions, the repetition/phase table, digests, tracebacks or faulthandler output,
supervisor exit code and wall, admission receipt.

| branch | first-match rule and bounded reading |
| --- | --- |
| `A03_INVALID_ARM` | An arm's declared source identity, interpreter, node, flag, admission or single-launch rule is not represented. That arm gives no observation; the others stand. |
| `A03_CORRUPTION_WITHOUT_TORCH` | T0 raises an original exception or fatal signal in its tape work. The corruption does not require the torch extension or a tracer; the interpreter build, numpy, or the host is implicated. |
| `A03_CORRUPTION_ONLY_WITH_TORCH` | T0 passes all repetitions; T1 fails. The import-time torch load is implicated (with or without pdb). |
| `A03_CORRUPTION_ONLY_UNDER_PDB` | T0 and T1 pass; T2 fails. The tracer is implicated; a plain run becomes the credible R09 path. |
| `A03_NO_CORRUPTION_OBSERVED` | All arms pass all repetitions with equal digests. Not reproduced under the probe; the failure may need the fuller chain or is intermittent below this exposure. |
| `A03_DIGEST_MISMATCH` | Arms or repetitions complete but their digests differ. Silent corruption of tape content; report the differing phase. Ranks above `NO_CORRUPTION` if both apply. |

What each changes next (object tier): `WITHOUT_TORCH` → a host/interpreter question for the
owner (the node's interpreter build and memory), and no R09 launch on this substrate until it
is answered; `ONLY_WITH_TORCH` → the torch load is the suspect; a bounded check of the installed
wheel against the interpreter before any launch; `ONLY_UNDER_PDB` → the outcome-blind full R09
attempt without pdb, faulthandler retained; `NO_CORRUPTION` → the same plain R09 attempt, with
the intermittency recorded; `DIGEST_MISMATCH` → treated as corruption of the failing arm.

DM prediction: **`A03_CORRUPTION_ONLY_WITH_TORCH` or `A03_CORRUPTION_ONLY_UNDER_PDB`** as the
two most likely branches, low confidence, with `NO_CORRUPTION` the main competitor (three
repetitions may be below the exposure needed). `WITHOUT_TORCH` is predicted least likely because
the node has run many minutes of other directions' pure-Python and numpy work without
incident. Owner slot: **not taken (unattended)**.

## Exposure, cost, stops, scope and handoff

Zero learner exposure; no parameter, checkpoint or native state. Three arms ≤ 300 s each.
Stop each arm at its first original failure, its third repetition, or the cap; no fourth
repetition, no extra arm because a preferred branch was absent.

Engineering §4: none. The probe is ordinary research code (one module, one runner, one focused
test) inside the direction's candidate tree; it adds no guard, registry, retry, resume or
telemetry beyond wall and peak RSS. R09 source bytes are untouched.

CM: Grok Build implements the module, runner and test in a fenced worktree; the hub reviews,
tests and commits by pathspec; no independent reviewer is required (no shared surface changes).
Operator launches the three arms on wsl_4070 at the pushed sha with fresh admissions.

scope: none
