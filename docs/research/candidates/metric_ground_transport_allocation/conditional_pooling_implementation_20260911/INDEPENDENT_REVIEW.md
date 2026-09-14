# Independent high-risk review — 2026-09-11

Reviewer: native Astra/high, read-only, independently grounded from the allocation,
card, source/design definition, applicable instructions/specification and actual diff.
Reviewed source was published unchanged at`4be7f07a3f9dab19b21e5f70705e605fdbd1feec`.
No test, scientific import, model or numerical check was executed by the reviewer.

**Final disposition: no unresolved material findings after the correction.**

Resolved P2: readouts and gradient evidence initially lived only in locals until
successful return, while runner cleanup removed scratch before final publication.
A late assertion could therefore lose trustworthy completed facts. The corrected
fixture attaches mutable gradient/readout dictionaries to the output summary before
population and records each readout before its publication/readback. Missing or
nonfinite gradient norms are JSON-safe on failure. Reviewer inspected the correction.

Source inspection confirms positive-SINR masks, first20 mean visible-UAV query,
division by sqrt20, masked user softmax, nU/20, empty-user zero, no-UAV uniform
weights, masked UAV sum/10 including all21 components, and the intact raw108 affine
path. REL/DENSE initialization draw order, private CPU RNG restoration, common raw/
GRU/head copies and independent critic copies are preserved. The old runner, H and
aggregate remain unchanged.

Reachable package imports contain definitions/static configuration and construct no
actors, critics, environments, optimizers or checkpoint-loaded objects. Calls remain
two standalone encoders, four forwards per arm on16×108 rows, one backward per arm,
four synthetic readouts with32 scores per arm. No unallocated Engineering Scope§4
machinery or source/runner budget breach was found. Complete ordered pairing,
conditional SE, inclusive MEI boundaries, damaged-primary suppression and retained
DENSE observations are implemented.

Residual limits: no numerical acceptance from review; numerical correctness,
publication execution, actual thread behavior and complete≤60-second wall remain
unmeasured before the fixture. Full actors/critics received source review only. The
outer timeout command was not in the first review; its bounded follow-up is recorded
below before the one execution. Review makes no scientific disposition.

Command follow-up found a second P2: killing the fixture on timeout bypasses the
child's `finally`, so the outer command must preserve partial readouts/stdout/stderr
and remove this creator's scratch. The correction saves and reads back available
partial files in the command receipt before removing the exact resolved directory
inside this checkout's temp root. There is no retry. The literal argv/source binding
and55-second single-child timeout otherwise passed source review. The internal wall
field covers child execution through exit; the enclosing tool invocation must supply
complete-command wall including outer startup/receipt publication/exit.

Final command correction check: **no unresolved material finding**. Available
timeout diagnostics/readouts are preserved and read back before bounded scratch
cleanup; exactly one child fixture is invoked with no retry. The minor timing-label
note was applied: `wall_through_child_exit_and_timeout_cleanup_seconds` includes
timeout preservation/cleanup when that branch is reached. Actual complete wall
remains for the one enclosing execution receipt; the reviewer ran nothing.
