# UCOPE numerical-locus direct-reuse engineering disposition

Date: 2026-09-04. Parent: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`.
Frozen assignment: `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_NUMERICAL_LOCUS_PLAN_20260904.md`.
Scientific polarity: none.

## Engineering conclusion

The direct-reuse implementation is rejected for exceeding Engineering Scope Specification §5's
orchestration budget. No conformant implementation SHA, ready launch command, numerical observation,
or locus result exists. No tests, cost CLI, resource preflight, diagnostic invocation, parent retry,
learner, optimizer, model, or scientific computation ran. The request's one bounded feasibility
attempt is finished; no further redesign or launch is selected here.

The smaller draft directly reused `audit.py`'s retained-summary byte binding, admission reader,
launch-SHA reader, peak-RSS reader, finite/max-absolute helpers, and already loaded `CR` imports.
It reused the unchanged accepted generator, canonical ordering, stage designs, FP32 scorer target
path, and `exact_solve` (`numpy.linalg.lstsq(..., rcond=None)`). None of those existing source files
was edited. This reduced the earlier rejected draft's 295 source lines to 219, but did not bring
the required orchestration below 30 percent. Merely moving required orchestration into another
new helper would not remove it from the diff.

## Preserved assignment and source facts

The requested observation is the first differing design, target, solver, or retained-reference
boundary for seed `ucope-scout-r01-b1-fresh-00`, fold 0, eight contexts,
40,960 episodes per context, offset 2,000,000. Canonical C-order array values, FP32 arithmetic,
float64 `lstsq(rcond=None)`, retained vectors/scalars, `1e-12` absolute tolerance, and all six
ordered technical labels remain frozen. No algorithm, acquisition, COUNT/RAW, competence,
headroom, direction, or Portfolio claim follows.

Direct source inspection established that `CR.root_targets_fp32` computes FP32 values then returns
`.astype(numpy.float64)`. The draft preserved that existing float64 storage and solver input;
"FP32 targets" names the computation path. DM confirmed this interpretation before execution and
recorded it in `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_RESUME_INTAKE_20260904.md`.

Requested per-node work remains 327,680 replayed episodes, 1,638,400 transitions, one reconstructed
root block, one prerequisite MSE tail solve, and three target arrays. The remote invocation would
solve three roots; Windows would solve three local roots and three staged-remote roots. All new
seed/draw/independent-sample identities, learner rows, constructions, updates, and fresh sampled
evaluation episodes are zero. These are frozen workload counts, not executed counts.

Per-node cost projection: the plan fixes 61.827 seconds per invocation and the same per-node cap,
using the accepted runner's historical cost. This is a fixed two-node diagnostic, not a sweep.
The draft's cost/exposure CLI was not executed; no new measured cost or resource conformance is
claimed. The intended nodes are pinned `wsl_4070` emit-solve then Windows compare-solve at one exact
pushed SHA. There is no fallback, third invocation, driver/tolerance sweep, or retry.

Post-learner path coverage: OPEN. Independent tests were drafted for one toy paired publication,
the six first-match rules, signed-zero byte inequality, invalid shape/dtype/nonfinite stops, and
offline parent publication with the real 24-predicate constants. The offline fixture was copied
from quarantined attempt 02 and its digest verified. The tests were not executed because the
source diff already failed scope; this work does not establish publication-path coverage.

## Scope items considered before writing

No new §4 machinery was accepted. The existing single retained-input predicate was reused under
parent card §2 and numerical plan §1/§5. Plan lines 37–46 and 68–80 request four ordinary arrays,
root vectors, and direct byte/numerical comparisons as the measured quantities; these are not a
tamper-evidence system. Plan lines 53–60 prescribe source-external node execution, which was not
built or launched. No distributed execution implementation, resume/retry/lease/heartbeat layer,
manifest/currentness guard, incident framework, schema validator, registry/abstraction layer,
additional telemetry, compatibility shim, impossible-condition defense, or repeated smoke test
was added. Scope line: `scope: none`.

## Rejected bytes retained for inspection

Ordinary copies of only the rejected source/tests and existing fixture are retained under the
ignored local directory:

`C:/Projects/HMASD-worktrees/cm-ucope-locus-resume-20260904/temp/directions/ucope/exp/numerical_locus_rejected_direct_reuse_20260904/`

This directory is an unexecuted draft archive, not an experiment result. No numerical payload or
new scientific evidence is present. Exact file facts:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `numerical_locus.py` | 11281 | `192c9627ef543e64983bfae2f7dfed14ac1af70e36e73cc0214e565d97ab8e58` |
| `run_ucope_root_numerical_locus_r01.py` | 1033 | `f61159683836074deebe1f530f4cf19777643ab317866ab63a3c88fe29c445c0` |
| `test_numerical_locus.py` | 5177 | `ed23d5ecfe7a89d2f72f5dcadc3c94735606fac329193d41bf3a7a2fce3841f2` |
| `attempt02_summary.json` | 8366 | `d966848ec6e7ff1361bca1b2a99910879d65af95467098ded9bdb4666f657ccd` |

The fixture's original attempt is unchanged and remains quarantined. Its copy is not used as a
new result or as evidence of any diagnostic branch.

## Source-line classification

Classification counts physical nonblank source lines, excluding the one module docstring in each
file; tests and documents are excluded from the denominator. Module: 214 physical / 198 source
lines. Runner: 27 physical / 21 source lines. Total: 219 source lines. Blank lines inside listed
ranges are ignored.

The implementer's complete partition was 97 orchestration and 122 computation/evaluation lines,
or 44.2922 percent, already disqualifying. Module orchestration ranges (76 lines):

`3–12, 15, 42, 45–48, 75, 89, 95, 105–106, 109, 120–121, 129–130, 140–143, 151–173, 176, 178–185, 199–214`.

Module computation/evaluation ranges (122 lines):

`16–39, 43–44, 49–72, 76–86, 90–94, 96–104, 110–119, 122–128, 131–139, 144–148, 174–175, 177, 186–198`.

Runner orchestration ranges (21 lines): `2–5, 7–8, 11–23, 26–27`; no runner computation.

The independent reviewer read the full frozen files and independently recalculated this partition.
The final conservative census moves the 24 static cost/exposure declaration lines `16–39` and six
retained-payload copying lines `123–128` to orchestration. These lines do not compute, sample,
learn, or evaluate. CM inspected the full source and adopts that disposition.

| File/category | Orchestration | Computation/evaluation | Total |
| --- | ---: | ---: | ---: |
| Diagnostic module | 106 | 92 | 198 |
| CLI runner | 21 | 0 | 21 |
| Complete source diff | 127 | 92 | 219 |

Final module orchestration ranges:

`3–12, 15–39, 42, 45–48, 75, 89, 95, 105–106, 109, 120–121, 123–130, 140–143, 151–173, 176, 178–185, 199–214`.

Final module computation/evaluation ranges:

`43–44, 49–72, 76–86, 90–94, 96–104, 110–119, 122, 131–139, 144–148, 174–175, 177, 186–198`.

Runner classification is unchanged. Every source line is classified. Final share is
**127 / 219 = 57.9909 percent**. Even the implementer's more generous classification fails.
With computational lines unchanged, at least 88 orchestration lines would have to disappear to
reach strictly below 30 percent; under the generous partition, at least 45 must disappear.
The independent reviewer found no small plan-preserving shrink. The 241 total physical source
lines and 27-line runner satisfy the other code-size budgets. Scope rejection is solely the
orchestration share, not a source-size, numerical, resource, or scientific finding.

Review was read-only: no tests, diagnostic, or source edits. It found no newly prohibited §4
subsystem beyond requirements already explicitly named by the frozen plan. Semantic/runtime
acceptance was not performed once the scope breach was established.

## Remaining boundary

The required orchestration groups are CLI/dispatch/imports, retained binding/admission and launch
facts, Python/NumPy/BLAS configuration, ordinary staged array/JSON I/O, completion/failure
publication, and wall/RSS reporting. Deleting these groups would omit frozen observables or stop
semantics. Adding numerical padding or reclassifying serialization as computation is not a remedy.
This review establishes that this smaller draft fails; it does not prove no implementation could
ever fit the budget.

One additional untested draft issue was identified by inspection: its final summary rewrite falls
after its last measured wall check. This was not repaired or exercised after scope rejection.
Numerical and runtime correctness were not accepted.

After archiving, only the two assigned uncommitted source files and the two assigned test/fixture
drafts were removed by explicit path. The implementer worktree is clean at the original baseline;
the CM worktree contains only this engineering note for commit. Worktrees, branches, existing
evidence, and unrelated files remain intact.

The exact dependency returned to the DM is a concrete plan-preserving implementation genuinely
below the 30 percent orchestration threshold. This note asks for no waiver or permission and
changes no scientific meaning. No launch assignment follows this draft.
