# CM objective: FRRIE-R09-SEGFAULT-A03-TAPE-ISOLATION — 2026-09-06

Card: `FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_SCIENCE_CARD_20260906.md` (binds). Implementer:
Grok Build in a fenced worktree from `main`; hub review and pathspec commit; no independent
reviewer (no shared surface). Operator launches on wsl_4070.

## Deliverables

1. `experiments/candidates/finite_resource_relational_inductive_efficiency/tape_isolation_a03.py`
   (new). Functions:
   - `training_inputs_no_torch(root, seed_label, update)`: replicates the body of
     `b01_contact_r02.tapes.production_training_inputs` using only the parent-package modules
     (`..tapes.generate_training_origin_schedule`, `..tapes.generate_episode_tape`,
     `..rng.AddressedRNG`, `ROSTERS` from a torch-free source: hard-code `(9, 15)` with a comment
     citing `b01_contact_r02/semantics.py`), returning the 64 tapes. It must not import
     `orchestration`, `policy`, `semantics`, `b01_contact_r02` or `torch`.
   - `evaluation_tapes(root, seed_label, episodes=256)`: imports `b01_contact_r02.tapes`
     lazily inside the function and builds `evaluation_tape` for rosters 9 and 15 × `episodes`.
   - `tape_digest(tapes)`: sha256 over the concatenation of each tape's canonical bytes (use the
     tapes' own arrays: `np.ascontiguousarray(x).tobytes()` for every array field in a fixed
     field order, plus the scalar fields as canonical JSON); one digest per phase.
   - `run_arm(arm, repeat, out_dir)`: for `repeat` repetitions, T0 runs training inputs for
     updates 1 and 2; T1 additionally runs `evaluation_tapes` first (T2 is T1 launched under
     pdb by the operator; the module does not implement tracing). Records per repetition and
     phase: wall seconds, tape count, digest; on any exception the full traceback text; then
     `sys.modules` membership of `torch` and `numpy` with versions, `sys.flags`, `sys.version`,
     `sys.gettrace() is not None`, peak RSS (`resource.getrusage` on Linux; `None` elsewhere),
     and writes `summary.json` under `out_dir`. Exceptions are recorded and re-raised after the
     summary is written so the supervisor exit code reflects them.
2. `scripts/run_frrie_r09_tape_isolation_a03.py` (new): `argparse` with `--arm {T0,T1}`,
   `--repeat` (default 3), `--updates` (default 2), `--eval-episodes` (default 256), `--out`
   (absolute), `--launch-sha`, `--admission-receipt` (path, existence checked, copied into the
   summary). Root and label are fixed: root hex `…0003` (64 hex chars, value 3), label
   `FRRIE-B09-CONTACT-BLOCK-003`. Under 150 lines.
3. `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/test_tape_isolation_a03.py`
   (new): one focused test that (a) runs `training_inputs_no_torch` for update 1 with a small
   root in a subprocess whose `sys.modules` is checked to contain no `torch` at exit, (b) checks
   that `training_inputs_no_torch(root, label, 1)` produces tapes whose per-tape canonical bytes
   equal those from `b01_contact_r02.tapes.production_training_inputs(root, label, 1)` for
   the same root and label (equality of the 64 tapes, field by field), and (c) `tape_digest` is
   deterministic. Keep the test under 60 s (use `episodes` small where the API allows; the
   training inputs are fixed at 64 tapes per update and should take a few seconds).
4. CM record `FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_CM_RECORD_20260906.md` with: the byte
   identity check `git diff 43eec21e <HEAD> --stat -- experiments/candidates/finite_resource_relational_inductive_efficiency/{tapes.py,rng.py,contracts/core.py,orchestration.py,policy.py,b01_contact_r02/tapes.py,b01_contact_r02/semantics.py}`
   (expected empty; report verbatim), local test result, a local T0 timing for one repetition
   with `--updates 1` (record wall), and the three frozen `wsl_4070` commands with `WT` and
   `LAUNCH_SHA` placeholders: T0 and T1 as plain invocations, T2 as
   `python -X faulthandler -m pdb -c continue -m scripts.run_frrie_r09_tape_isolation_a03 --arm T1 ... < <file of q lines>`; each preceded by the admission and wrapped in
   `timeout --signal=TERM --kill-after=5s 300s`.

## Protected

Every existing file under `experiments/candidates/finite_resource_relational_inductive_efficiency/`
and `scripts/run_frrie_*.py`; the R09 card and evidence; `tests/` other than the new file.

## Checks and stop rule

Focused test passes locally; runner `--help` works; `python -c` import of the new module does not
import torch (assert `'torch' not in sys.modules`). Stop when the four deliverables exist and the
CM record carries the identity check and frozen commands. Budget: under 500 new lines in total.
