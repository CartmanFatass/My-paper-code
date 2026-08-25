AUDIT_DISPOSITION=MISMATCH

Frozen assertions:

When the registered direction-balanced norm is exactly zero, both arms must submit an exact zero actor gradient; that case is valid and must not be classified as operational invalidity.

Before the first optimizer step, both credit channels, every registered actor group, and both baseline-output groups must be finite and live. Each formal replicate must also contain at least one update whose DB and raw-sum unit directions differ by more than 1e-6; otherwise the treatment is vacuous and must fail closed.

Conflicting code behavior:

compose_scale_matched_raw_sum_gradients and validate_scale_match reject every registered_gradient_norm <= 1e-12, including the frozen valid m_DB=0 case. The focused test explicitly requires a zero registered norm to raise G42GradientGateError, thereby encoding the opposite semantics.

The implementation checks only the global immediate and successor norms. It never audits named actor-group liveness, immediate- and successor-baseline-group liveness, or the frozen DB-versus-raw unit-direction distance. optimize_matched_direction_attribution_update can therefore return passed=true and emit final checkpoints when part of the registered gradient path is dead or when direction balancing is never an active treatment.

Smallest in-contract correction:

Handle registered_gradient_norm == 0 by assigning exact zero actor gradients in the NO_DB arm while leaving the identical baseline update and Adam-step exposure intact. Continue to fail only when the registered norm is positive and the raw sum is zero or nonfinite.

On the first paired batch, serialize and validate finite per-group channel gradients for the exact registered actor-group inventory and separate live gradients for both baseline outputs.

Record the DB/raw unit-direction distance on every valid update; require one distance strictly greater than 1e-6 in the nonformal package and at least one per formal replicate before any conclusion-bearing checkpoint or branch can pass.

Add focused guards for a dead unaffected actor/baseline group, an always-collinear DB/raw treatment, and the valid zero-DB-norm case. No source, target, optimizer, seed, threshold, evidence volume, confidence procedure, or first-match branch needs to change.