# G47 code-science alignment audit

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
round=20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit
audit_target_commit=744ebe8495c18a6e36e851da384ccd21351615e1
implementation_code_commit=744ebe8495c18a6e36e851da384ccd21351615e1
accepted_design_stage_commit=bcb494886e6fa9966a9a3c86e39fdd1af9851b81
accepted_design_source_commit=af7d6b1f1ad55f24e25202b39414203677a7813b
formal_compute_started=false
nonformal_compute_started=false
compute_budget=zero
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

This is a zero-compute, read-only conformance diff. Compare the exact G47
implementation at `audit_target_commit` with the accepted G47 design assertion
and its listed evidence. Do not implement code, run proof execution or formal
compute, edit CDC, authorize a run, select a successor, or reactivate G33.

The only question is whether the accepted candidate realizes the frozen
structural deletion of the shadow-baseline module while preserving the retained
actor and optimizer path bitwise. A MISMATCH must name the exact frozen
assertion, the conflicting target-bound path or behavior, and the smallest
in-contract correction. Do not infer a defect from style or from an unlisted
path.
