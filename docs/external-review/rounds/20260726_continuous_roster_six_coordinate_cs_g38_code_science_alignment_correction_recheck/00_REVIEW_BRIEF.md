# G38 code-science alignment correction recheck brief

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=read_only_smallest_operational_correction_diff
compute_budget=zero
audit_target_commit=ea93b15eabf68c35ba8e459ca8527e56d2988db8
repair_implementation_code_commit=ea93b15eabf68c35ba8e459ca8527e56d2988db8
superseded_implementation_code_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
original_audit_target_commit=3b13ce0c6936fc5209e9ff7928aaaae61ec7200b
source_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_P0
pm_code_acceptance=complete
formal_attempt_1=operational_invalid_zero_iteration
fresh_formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The first formal attempt exposed one exact implementation defect that the
proof-sized and bounded checks had not reached: the pre-fold FOLD6 ten-wide
float32 reduction and folded six-wide reduction were algebraically equal but
accumulated different rounding error. Thirty-four FOLD6 cells exceeded only
the frozen prefix-action tolerance. PM archived the run as operational invalid
with zero iteration cost and no retry, resume or restart.

PM applied only the unchanged-contract deterministic-kernel correction. Both
pre-fold arms now use the actual same factorized affine path; FULL10 supplies
its real last four coordinates, FOLD6 supplies the registered constants, and
the folded actor uses the identically computed effective bias. PM accepted the
three-path correction after 51 focused/regression tests and a read-only formal
checkpoint audit whose complete fold-error vector was exactly zero.

This recheck asks only whether that smallest correction preserves the frozen
G38 science and closes the observed formal-scale fold-equivalence defect. It
requests no compute, redesign, refactoring, new evidence or successor work.
