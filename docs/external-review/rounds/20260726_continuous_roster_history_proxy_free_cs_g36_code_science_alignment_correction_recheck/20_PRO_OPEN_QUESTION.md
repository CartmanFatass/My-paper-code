# External Pro open question: G36 alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=read_only_smallest_correction_diff
compute_budget=zero
audit_target_commit=4c9a2bc4c491a338a78b0a52e741dc9de62c2924
repair_implementation_code_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
superseded_implementation_code_commit=e96f0be154afcf778780bad6266458e211b4b047
original_audit_target_commit=3c1c7334e55b5f5c016bcbb9fa70c5073ee1fa28
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed target and allow-list. Recheck only the smallest correction to
the mismatch archived in the original alignment raw.

Question: does repair commit
`8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04` ensure that conclusion-bearing
G36 evaluation constructs the actor tensor without materializing, copying,
validating or otherwise reading active source observation coordinates 6:10
before substitution, while leaving every other frozen G36 scientific field and
formal-authority boundary unchanged?

Verify only:

1. `evaluate_g36_history_proxy` no longer stacks full source observations. Its
   exercised route allocates a fresh zero ten-coordinate actor buffer, copies
   only each source row's `:6` prefix, and writes donor bundles to active 6:10.
   Critic state is stacked separately and unchanged.
2. Protected active source coordinates cannot affect the transformed actor
   tensor or be inspected by finite/support validation before overwrite.
   Actual-age, previous-action and actor-time read counters truthfully derive
   from the no-read construction path and remain zero.
3. The new focused end-to-end evaluator guard exercises all 48 physical steps
   and fails if full-width source history reaches the pre-substitution actor
   buffer; the prior poisoned-transform test still excludes protected-value
   dependence inside the transform.
4. The correction changes no donor bank/tape law or seed, active-count
   conditioning, source ledger, lifecycle, critic, checkpoint, action stream,
   episode set, cell/inventory, trace metric, estimand, threshold, bootstrap,
   first-match branch, complexity or formal token/preflight binding.
5. The replacement nonformal preflight is bound to the exact repair commit and
   is used only as operational evidence. Formal compute has not started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the exact mismatch is corrected and no other
  frozen scientific or authority field changed.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one previously unstated
  result-changing scientific choice that prevents conformance judgment.

Do not request or introduce another algorithm, source, proxy distribution,
experiment, threshold, evidence volume or formal run. Stop after the single
scoped disposition.
