# G35 code-science alignment correction recheck brief

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=correction_diff_only
compute_budget=zero
original_audit_target_commit=49b3ba9399b056bd601863d6b0f2305c222f1f66
original_disposition=MISMATCH
repair_implementation_code_commit=f626dfd8a345ef670e08e601344b67e28ffb3563
recheck_target_commit=472178e3cc7675a8ba1044558b47dd094c34138f
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The original code-science audit identified one exact result-changing route:
formal admission trusted six favorable fields from `analysis_result.json`
without loading, validating and binding the bounded nonformal training and
evaluation manifests. PM made only the named in-contract repair, reran the
complete affected regression surface, accepted the corrected code and held one
fresh bounded nonformal exercise at the repair commit.

This is the one permitted correction-only recheck. It asks only whether that
exact mismatch route is closed. It cannot reopen the frozen design, repeat the
full audit, search for unrelated defects, review style or engineering quality,
request compute, or introduce another arm, source, seed, credit rule, threshold,
evidence volume, estimand, experiment or first-match branch.

The false assertion this recheck can prevent is the one named by the original
mismatch: a conclusion-bearing G35 formal branch authorized by a favorable but
fabricated, wrong-inventory, stale or later-tampered nonformal preflight. The
recheck is read-only and zero-compute; formal execution remains blocked until
`ALIGNED`.
