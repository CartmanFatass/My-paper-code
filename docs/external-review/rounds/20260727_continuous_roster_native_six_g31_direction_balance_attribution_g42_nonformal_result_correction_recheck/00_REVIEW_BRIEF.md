# G42 nonformal result assertion-conflict correction recheck

```text
semantic_author=research_operations_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
review_mode=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
round=20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_nonformal_result_correction_recheck
stage_commit=c50cc06c1d4887f27977108eae9e9b0a4e3ec0c0
audit_target_commit=6b8ea82d8fdbc76c14a414ff2b042a126f945dfb
formal_compute_started=false
nonformal_compute_started=false
valid_iteration_cost=0_correction_recheck
```

This is one bounded correction-only recheck of the prior G42 nonformal result
review assertion conflict. External Pro must compare the prior `MISMATCH`
assertions against the exact audit-target source and tests at
`6b8ea82d8fdbc76c14a414ff2b042a126f945dfb` and return one of:
`ALIGNED`, `MISMATCH`, or `SCIENTIFIC_AMBIGUITY`.

The recheck does not reopen G42 design, alter the estimand, request a new
algorithm, run compute, or authorize a formal result. The accepted implementation
and all protected source, target, optimizer, seed, backend, inventory, threshold,
confidence and first-match semantics remain frozen. G33 remains abandoned.

The prior Pro response is evidence of the assertion conflict only; it is not
presumed correct or incorrect. The response must identify whether the prior
assertions are supported by the exact audit-target content and state any exact
mechanical disposition needed to restore source/review alignment.
