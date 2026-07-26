# External Pro open question: G38 alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=read_only_smallest_operational_correction_diff
compute_budget=zero
audit_target_commit=ea93b15eabf68c35ba8e459ca8527e56d2988db8
repair_implementation_code_commit=ea93b15eabf68c35ba8e459ca8527e56d2988db8
superseded_implementation_code_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
original_audit_target_commit=3b13ce0c6936fc5209e9ff7928aaaae61ec7200b
formal_attempt_1=operational_invalid_zero_iteration
fresh_formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed target and allow-list. Recheck only the smallest operational
correction to the frozen fold-equivalence mismatch archived in the failed-run
evidence.

Question: does repair commit
`ea93b15eabf68c35ba8e459ca8527e56d2988db8` ensure that the actual pre-fold
FOLD6 path and true folded six-coordinate path execute an identical effective-
bias affine kernel under the frozen tolerances, while preserving the exact
FULL10/FOLD6 mathematical graph, trainable parameters and all other frozen G38
scientific and formal-authority fields?

Verify only:

1. `_G38RawInputAffine` implements the same mathematical affine `A[o]+b` for
   both pre-fold arms by evaluating columns 0:6 and then a fixed-order 6:10
   contribution combined with bias. FULL10 supplies its actual last four
   inputs, while FOLD6 receives only six source coordinates and supplies the
   registered constants inside the actor. This is the actual execution path,
   not an audit-only override.
2. Before folding, both arms retain the same two serialized
   `Linear(10,32)`/`Linear(10,2)` parameter sets, shapes, trainable masks,
   counts and initial bytes. All removable columns remain live under the actual
   inherited objectives. The forced clamped initialization check exercises the
   actual arm paths and retains its unchanged `1e-7` gate.
3. `fold_g38_constant_actor_checkpoint` computes both stored effective biases
   with the same fixed-order four-coordinate operation, retains columns 0:6,
   deletes exactly 136 actor weights and copies every unrelated tensor exactly.
   The folded actor consumes six coordinates and its retained affine call is
   numerically identical to the pre-fold FOLD6 retained/effective-bias call.
4. The stress test makes a legacy ten-wide reduction diverge above `1e-6`,
   while the corrected pre-fold/folded paths and a formal-like capacity-12,
   H48 audit produce an all-zero error vector. It also preserves the real
   removable-column gradient, FULL10/G32 collector and exact-fold guards.
5. The correction changes no constant, tolerance, raw-input inventory,
   source, critic, reward, lifecycle, seed, paired exposure, PPO/RNG,
   checkpoint, cell/inventory, estimand, threshold, bootstrap, evidence volume,
   first-match branch, complexity or formal token/preflight binding. The
   previous formal run remains operational invalid, read-only and zero-cost;
   no fresh formal compute has started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the exact formal-scale defect is corrected and
  no frozen scientific or authority field changed.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one previously unstated
  result-changing scientific choice that prevents conformance judgment.

Do not request or introduce another algorithm, source, fold, kernel tolerance,
experiment, threshold, evidence volume or formal run. Stop after the single
scoped disposition.
