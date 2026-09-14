# Independent RCLE B07 high-risk review — 2026-09-12

Reviewer: native /root/dm_a_mx_rcle_intake/review_a_h_rcle_b07, independent
Astra/high. Read-only diff against e93845028; no edits, tests, RCLE model, native
invocation, scientific RNG or launch. DM retains technical acceptance.

## Findings and acceptance evidence

No material finding in the numerical/caller/runner diff. Both derivatives use
the same complete ordered parameter tuple before any mutation; unused coordinates
become zero. The first traversal retains the graph for the second. Scale-safe
unit normalization implements the exact selected formula. Zero/cancellation
does not move parameters; a nonzero combined direction takes one .02 step.
Nonfinite losses/vectors reject before mutation.

The caller preserves two native 32-episode batches, existing episode means,
stopped full-return advantages and the original FP64 baseline arithmetic/order.
Only detached baselines and scalar records leave the block. Shared B04 omitted
callback retains weight100 and old output metadata; custom counts distinguish
completed and interrupted exposure. Existing action-law serialization, native
ownership, reference/evaluation and primary consumers remain compatible.
No prohibited engineering-scope §4 machinery or source/runner line-budget breach.

The later inspected MemoryPath/StringIO fixture performs no filesystem writes.
DM test evidence is 15 passed in1.74 s, enclosing2.5407404 s, with scratch absent.
Reviewer did not rerun these checks.

## Exact outer-boundary addendum

The supplied single payload uses timeout900 around the whole .sh. Its
learned880/reference15 timeouts sum895, leaving a nominal five-second margin
inside the same900 ceiling. Each includes adjacent admission and runner; set-e
ends the chain on failure. This is not another allowance. The published source
SHA must replace the prospective placeholder before the actual command is bound.

## Limits and costs

Tests are DM evidence. No runtime/memory or complete publication cost was
pre-measured. Passing these checks is not evidence of useful learning or an
unbiased update. Assumption: unchanged stopped baselines and episode reductions
preserve the selected surrogate inputs.

Available reviewer command-wall samples total2.4825817 s: ten earlier samples
2.2720917 s plus addendum .21049 s. One parallel read's timing was truncated and
is unreported. This subtotal is not complete review/support cost.
