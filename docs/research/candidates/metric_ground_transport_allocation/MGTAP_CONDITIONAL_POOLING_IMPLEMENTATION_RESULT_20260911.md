# Conditional pooling implementation result — 2026-09-11

**Technical fixture PASS; no native scientific result.** This is the evidence for
the [implementation card](MGTAP_CONDITIONAL_POOLING_IMPLEMENTATION_CARD_20260911.md),
under the MGTAP-only numerical allowance in Portfolio option A. No B/C object was run.

## E0 — rule, bytes, execution and counts

Allocation rule, applied verbatim:

> Success establishes only tested technical properties.

> Failure leaves numerical acceptance incomplete; review cannot replace it.

The one command completed at source`4be7f07a3f9dab19b21e5f70705e605fdbd1feec`.
The source surface stayed unchanged through command/review publication`21f750ff4`.
Execution was the literal [COMMAND.ps1](conditional_pooling_implementation_20260911/COMMAND.ps1)
in the existing local `codex/mgtap` checkout, using the existing CPU interpreter.
No prior fixture output/scratch existed. No retry, second fixture, additional
source-test execution or old full-policy suite was run. Source/command parsing was nonexecuting.

| Receipt quantity | Direct observation |
| --- | --- |
| Start UTC |2026-09-11T08:10:44.608560+00:00|
| Enclosing complete command, including outer startup/receipt/exit |**3.8409721s**, exit0, cap60s|
| Child chain through exit, including admission/imports/fixture/publication/cleanup |3.5940000000118744s; no timeout|
| Runner wall before final summary write |3.1560000000172295s; not used as complete wall|
| Adjacent destination admission |physical/effective available both15552196608bytes; floor4294967296; PASS via GlobalMemoryStatusEx|
| Device/dtype |CPU FP32; script configured one intra/inter-op thread|
| Standalone encoders |2, COND and DENSE|
| Forward calls |4 per arm;16 fixed108-component rows each|
| Supplied-loss backward calls |1 per arm; no optimizer|
| Synthetic readouts |4 paired panels,32 supplied scores per arm per panel|
| Full actors/critics/checkpoint loads |0/0/0|
| Environments/trajectories/native steps/training/real evaluation/optimizer/profiling/search |all0|
| Creator test scratch |removed inside child; independently observed absent after exit|

Machine-generated facts are preserved in [summary.json](conditional_pooling_implementation_20260911/summary.json),
[admission.json](conditional_pooling_implementation_20260911/admission.json),
[command receipt](conditional_pooling_implementation_20260911/COMMAND_RECEIPT.json),
and [enclosing execution receipt](conditional_pooling_implementation_20260911/ENCLOSING_EXEC_RECEIPT.json).
The enclosing measurement is the complete execution window; the shorter nested
measurements are not added to it or presented as separate study work.

## Measured contracts and primary publication

Within the16 supplied rows, the independent scalar context oracle agreed with the
implemented COND operation. The checks covered legal masks, visible zero-offset
rows, empty users/UAVs, query direction and denominator, user count scaling,
UAV fixed-slot scaling, all21 V outputs, row permutation, shaped output and the
intact raw path. Both actual standalone encoders have9744 parameters, of which2768
belong to the nonlinear branch. Zero initial projections, common supplied raw
weights and construction-time global Torch RNG restoration passed.

The69079 complete-learner count is **source-shape arithmetic only**. GRU/head/critic
copying and old REL/DENSE initialization behavior were independently reviewed in
source. They were not checked by constructing or running a complete policy.

At the explicitly nonzero fixture projection, every parameter block and input had
finite nonzero supplied-loss gradients. COND's user-map/UAV-map/projection norms
were0.0006170776905491948/0.0005167046329006553/0.0021677808836102486.
DENSE hidden-weight/hidden-bias/projection norms were
0.00948609784245491/0.010529136285185814/0.006206734571605921.
These are connectivity observations after supplied fixture weight changes, not
policy movement, optimizer exposure, learning or credit efficacy.

| Supplied panel | Published result |
| --- | --- |
| Above |32 ordered differences+.02, mean+.02, conditional SE0, COND_ABOVE_MEI|
| Inclusive boundary |32 differences−.01, mean−.01, conditional SE0, INSIDE_MEI|
| Adverse |32 differences−.02, mean−.02, conditional SE0, COND_ADVERSE|
| Damaged |duplicate/missing index, nonfinite score and incomplete episode detected;29 valid paired rows retained, paired mean/SE null, INCOMPLETE; all32 intact DENSE scores retained|

Both±.01 scalar boundaries were also checked. All four synthetic readouts and the
complete summary passed closed-file JSON publication/readback. Those scores were
supplied by the fixture; their labels and SE are not native performance evidence.

## Review, deviations, support and retention

[Independent review](conditional_pooling_implementation_20260911/INDEPENDENT_REVIEW.md)
found two P2 failure-preservation gaps; both were corrected and reviewed before the
one execution. Source/diff/reachable-import and command follow-ups ended with no
unresolved material finding. Reviewer numerical exposure was0. No source, runner,
test or numerical-command budget breach occurred. No Engineering Scope§4 machinery
was added. The old REL/DENSE/H/two-master runner and shared UCOPE/environment bytes
are unchanged.

Source reading, authoring, static parsing, review, Git, preservation and intake are
separate support work. Complete support wall/CPU was not instrumented and is not
claimed zero. No performance probe was run. Peak RSS, aggregate CPU and activation
memory are unmeasured (`resources_unmeasured`); this limits resource claims, not the
tested technical properties. No native COND runtime is inferred from3.84s.

The three runtime JSON files were copied and checked byte-identical at collection;
[preservation facts](conditional_pooling_implementation_20260911/PRESERVATION.json)
record original working-file lengths/digests before ordinary Git text normalization.
Creator scratch is absent. The small runtime output directory is retained for
Root's integration/retention acceptance; it contains only those three copied files.
No remote worktree or experiment handle was created. The active shared authoring
checkout and unrelated work remain intact. Cleanup ownership remains with this DM
after Root accepts preservation; no full checkout is kept merely as a backup.
