# CBSC-OMRC-B01 r06 interpreter incident intake — 2026-09-04

- Direction: `capability_bound_semantic_currentness`
- Object/rung: `CBSC-OMRC-B01 / CBSC-OMRC-B1-THREE-SEED-SCOUT`
- Attempt root name: `b1_scout_r06`
- Exact launch commit: `a138b01534f41f88d1045179fadc464aefa79e9e`
- Remote task: `cbsc-b1-r06-a138b01534-01`
- Terminal status: exit `6` after one second
- Intake classification: **technical incomplete implementation; quarantined**
- Scientific object consumed: **false**
- Scientific polarity: **none**

## What I checked

I checked task status and the task's stored command, the outer admission receipt, exact Git state,
the create-only incident root, first worker request, bound per-slice admission, worker stderr,
supervisor incident, attempt ledger and whole-attempt incident. I then replayed the failing worker
entry step directly over the same exact source and recorded request before classifying it.

The outer command was correctly stored as fresh node-local `admit-memory && exact runner`. Admission
passed with physical and effective available memory both `12,904,972,288` bytes, above the 4 GiB
floor. The runner bound commit `a138b01534f41f88d1045179fadc464aefa79e9e`, the fixed B0 hashes,
the three Pro archives and source-conformance SHA
`2a8996dcc5b5786f32cb53852e2f495bc0f5daf1cbbb451a796d22fbf2608050`.

The first slot (`seed=21101`, `STRUCT-CURRENTNESS-GRU`, slice `0:12`) acquired its own valid memory
receipt and wrote its request. The child then exited before importing NumPy. Its stderr shows that
the parent had converted the configured virtual-environment executable
`/home/wu/.venvs/hmasd/bin/python` to the symlink target
`/home/wu/.local/share/uv/python/cpython-3.10.21-linux-x86_64-gnu/bin/python3.10`; that base
interpreter has no NumPy site package. The worker stopped at package import with
`ModuleNotFoundError: No module named 'numpy'`.

For direct reproduction I invoked the same base interpreter, module and preserved request from the
same detached worktree, changing only unused output locators to `/tmp`. It again exited `1` at the
same package import with the same missing-NumPy exception. This confirms an interpreter-path
portability defect rather than relying on the first error text alone.

The supervisor observed `0.0574833819991909` seconds, two samples, one process and no result. The
attempt ledger has no completed arm-seed; the whole-attempt incident records
`B1_ENGINEERING_ATTEMPT_INCOMPLETE`, `scientific_branch=null`, `scientific_claim=null`, and
`scientific_object_consumed=false`. Because import failed before model construction, no learner,
optimizer, checkpoint, evaluation or rule-read result was created.

## Bounded interpretation

This is a Linux virtual-environment identity defect in the B1 subprocess launcher. It does not test
STRUCT, RAW, PI, DERANGED, the host, the learner, currentness value, headroom, an MEI or any frozen
result branch. The passed memory receipt is valid only for this failed invocation and cannot admit a
fresh one.

The narrow repair must preserve the invoked virtual-environment executable path instead of
realpath-resolving through its symlink, while continuing to bind and hash the actual executable
bytes. It may touch only the B1 worker/policy-replay launch identity and focused tests. It must not
use `PYTHONPATH`, change dependencies, loosen admission or telemetry, alter scientific semantics,
or resume/reuse this incident. This fixes existing launch behavior and adds no engineering-scope
section-4 machinery (`scope: none`).

## Decisions this intake produces

### Quarantine and next attempt (Object tier, selection)

Options:

- **(a)** quarantine r06 as a reproduced technical incomplete attempt, repair only the
  virtual-environment subprocess binding, independently verify it on Linux, and if exact-SHA
  readiness remains green launch a fresh create-only `b1_scout_r07`;
- **(b)** reuse or resume the r06 incident, inject `PYTHONPATH`, or invoke the worker manually as a
  substitute for the frozen runner; or
- **(c)** treat the import failure as a scientific result, consume B01, or change the treatment,
  comparator, cap, exposure or result rule.

Recommendation: **(a)**. It follows the reproduced failure to the smallest reversible code surface
and preserves the scientific object. Option (b) creates unbound environment or attempt state;
option (c) invents polarity before any learner existed.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance label:
`OWNER_DELEGATED`. The failed r06 root remains immutable historical engineering evidence. A future
launch, if the repair passes, uses a new pushed SHA, new detached worktree, new task name, fresh
admission and new output root; it is not a retry or resume.
