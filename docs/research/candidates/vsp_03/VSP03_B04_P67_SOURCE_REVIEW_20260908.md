# VSP03 B04 / P67 independent command and dependency review

**No material finding found** in committed candidate
`828da00343e5036a4de93ccf1ec636e3b8c777b7`. Reviewed the new8-line
`experiments/candidates/vsp_03/vsp03_b04/launch_p67.sh` under
[P67 card sections4–5](VSP03_B04_P67_SCIENCE_CARD_20260908.md) and the
[CM assignment](VSP03_B04_P67_CM_ASSIGNMENT_20260908.md). Owned only this review;
no index operations, source edits, runtime checks or scientific execution.

The launcher passes the caller's quoted exact-SHA cwd both to the accepted launch.sh
path and its working-directory argument. Its unit and supervisor name are both
`vsp03-b04-p67-20260908`. Scientific output is the fresh
`b04_seed6_p67_20260908` root; admission and terminal filenames use that same P67
prefix. Derived payload/tmux paths and supervisor metadata therefore belong to the
new handle. The prior P64/P65 paths and spent allowance are not reused. Output object
VSP03_B04 remains permitted by the P67 assignment.

The literal single-quoted `bash -c` payload preserves `$VSP03_B04_STARTED` until
execution by the contained child shell. The accepted controller still exports the
exact command metadata as VSP03_B04_COMMAND; deadline.py supplies the original
manager monotonic start. The explicit seed6, wsl_4070, cap120 and reserve10 arguments
reach the unchanged runner/adapter. `admit-memory --out <P67 receipt> && exec ...`
keeps admission adjacent and prevents runner execution after admission refusal.
The canonical preflight's main returns0 only for passed admission and nonzero on
refusal or measurement/publication error. Required physical/effective4GiB semantics
remain unchanged.

The committed tree contains the previously missing admission source and its local
dependency, with canonical tracked blobs:

- `scripts/hmasd_resource_preflight.py`: `4127cd22d2e0c4cc1ad6df85aafeb7131c3d07b2`.
- `scripts/hmasd_platform.py`: `eb54e7c31170ad14c903ba87e55b1a479416b51b`.

Inspected the helper imports and required publication call. The preflight imports
hmasd_platform through its existing package/sibling fallback; both files otherwise
use the standard library. The sibling path remains available for the declared
`python scripts/hmasd_resource_preflight.py` invocation. No helper was rewritten.
The scientific runner still inserts its repository root before importing the shared
B03 implementation and calls it with seed6 and object_name VSP03_B04.

A scoped diff against reviewed `b5d605bf4` is empty for launch.sh, control.py,
deadline.py, the scientific runner and shared B03 driver. Their accepted science,
thread/RNG/count/primary behavior and P65 lifecycle checks are reused from
[B04 source review](VSP03_B04_SOURCE_REVIEW_20260908.md). No lifecycle fixtures or
seed tests were repeated. CM separately owns full committed/staged dependency,
LF and syntax verification; this review does not claim a staged invocation was run.

Applied the current runtime/scope provisions and relevant AGENTS changes. Prohibited
section4 additions without a card line: **none**. The existing task-local containment
is expressly reused by P67 card section5. Eight added command-binding lines introduce
no retry, guard, registry or new execution framework and create no source/runner
budget breach. The orchestration-only binding has a direct assigned purpose.

Residual risk is actual exact-SHA staging, fresh destination admission and the sole
submission's complete outputs/exit/termination evidence; these remain CM's complete
technical batch. A source review supplies neither a fresh admission nor a scientific
result. Any accepted failure spends P67's new allowance without retry. No repair is
requested from this inspection. This is independent technical evidence, not approval
or a terminal disposition.
