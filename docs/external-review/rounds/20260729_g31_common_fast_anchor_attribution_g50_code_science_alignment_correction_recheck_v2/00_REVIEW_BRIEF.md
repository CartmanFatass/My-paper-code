# G50 correction-recheck-v2 evidence brief

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck_v2
audit_mode=read_only_immutable_target_excerpt_check
round=20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_correction_recheck_v2
stage_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
audit_target_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
repair_implementation_code_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
superseded_implementation_code_commit=5aeb3b7745847ca39edf556af29067506ead4c00
original_alignment_stage_commit=5aeb3b7745847ca39edf556af29067506ead4c00
original_audit_target_commit=5aeb3b7745847ca39edf556af29067506ead4c00
prior_recheck_stage_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
compute_budget=zero
fresh_runtime_compute_started=false
formal_compute_started=false
submission_limit=exactly_one
recovery_submission_limit=zero
answer_now=forbidden
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The earlier correction-recheck response claimed that the repaired target still
contained the superseded selector. This v2 package inlines immutable excerpts
from `git-show` at the exact target and asks only whether those bytes resolve
that single mismatch. It does not reopen G50, change its contract, request code
changes, or authorize compute.
