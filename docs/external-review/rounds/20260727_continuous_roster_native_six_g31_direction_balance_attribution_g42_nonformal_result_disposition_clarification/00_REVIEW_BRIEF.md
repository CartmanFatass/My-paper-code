# G42 correction-recheck disposition-only clarification

```text
semantic_author=research_operations_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
review_mode=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK_DISPOSITION_CLARIFICATION
round=20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_nonformal_result_disposition_clarification
stage_commit=5c8337a6bbf62fa266d8776e1200783c9aedaa4b
audit_target_commit=6b8ea82d8fdbc76c14a414ff2b042a126f945dfb
formal_compute_started=false
nonformal_compute_started=false
valid_iteration_cost=0_disposition_clarification
```

This is a single bounded clarification because the prior correction/recheck
response did not contain one of the required disposition tokens. External Pro
must return only the disposition token requested by the question, with one
target-bound counterexample only when the token is `MISMATCH`.

This clarification does not reopen G42 design, change code, run compute,
reinterpret the estimand, authorize formal execution, or select a successor.
