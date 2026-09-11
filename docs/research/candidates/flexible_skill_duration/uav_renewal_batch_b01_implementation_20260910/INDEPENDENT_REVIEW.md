# Independent FSD I1280/D0 review

Reviewer: `rev_ah_fsd_i1280`, independent Astra/high, read-only under
Engineering Scope §7.3. DM retained the following native final returns.
The Reviewer executed no imports, tests, numerical analysis or scientific calls.

## Initial source review, before any accepted fixture

No material finding found in the static review against the accepted execution mapping and card §§2–7. No edits, imports, tests or numerical commands were executed.

- **Binding:** shared runner lines 87–95, 149–156 and 249–253 set 1280/128 before learner/evaluator construction. Both snapshots retain the field.
- **Comparison:** lines 359–374 require the exact arm-specific batch values, then exclude only that field and the existing cost distinction. Other recorded configuration differences still fail.
- **Primary:** lines 344–379 preserve 32 ordered scores, `J=6U/500`, I−D0 differences, sample SD, conditional SE and one independent training pair. Missing primary data prevents paired polarity.
- **Compatibility:** default-false arguments preserve B01/B02 seeds, caps and behavior. Protected `hmasd/`, configuration and environment source has no diff.
- **Fixture:** static inspection supports four configurations, one buffer with 1,281 valid rows, two sampler traversals and four paired readouts. Reachable repository imports instantiate no model, environment, optimizer or logging worker.
- **Scope:** no new prohibited §4 machinery identified. Runners are 437 and 29 lines, within the 600-line limit.

The caller must create and isolate scratch, retain the report, clean scratch, and measure the complete command through exit. Import cache writes need inclusion in that isolation. The sampler retains its existing internal timing/cache bookkeeping; no additional profiling invocation is introduced.

Residual limits: fixture execution/publication remains unverified at this review point. Full learner numerics and gradients, activation memory, actual native thread use, complete runtime and native return remain unmeasured. Conditional episode uncertainty cannot establish training-population uncertainty or benefit from batching alone.

## Foreground wrapper correction, still before any accepted fixture

No material finding in the wrapper correction.

- Numerical fixture and invocation counts are unchanged.
- Scientific imports follow scratch-local `MPLCONFIGDIR` setup; invoke with the planned `-B`.
- Primary evidence is copied before cleanup. Context cleanup covers import/fixture exceptions, and the previous environment setting is restored.
- No model, environment, optimizer or additional numerical case is introduced.

One evidence limit remains: internal timing stops before receipt publication, stdout and process exit. Retain the foreground tool’s complete command wall separately to establish the 60-second boundary. No execution or imports performed by this reviewer.

## Final artifact readback

No material finding after artifact readback.

- Published source `0207d0b3cf307f656b5f46b298b74efa438608b8` remains unchanged.
- Foreground receipt records exit 0 and **4.8851396 seconds through publication, cleanup, stdout and process exit**, covering the complete 60-second requirement.
- Internal receipt records successful cleanup; independent filesystem readback confirms the named scratch directory is absent.
- Evidence matches the allowance: **one fixture, four configurations, one buffer, 1,281 valid rows, two traversals and four synthetic readouts**. Both traversals preserve all valid rows and their final one-row chunk.
- Published readouts retain ordered differences, means ±0.0175, sample SD and conditional SE; undeclared gamma and missing-U cases reject as intended.
- Models, environments, training, optimizer calls and scientific invocations remain zero.

This supports technical acceptance of binding, traversal and synthetic primary publication only. Full learner numerics/gradients, activation memory, actual native threading, complete training cost and native benefit remain unmeasured. No rerun or numerical analysis was performed during review.
