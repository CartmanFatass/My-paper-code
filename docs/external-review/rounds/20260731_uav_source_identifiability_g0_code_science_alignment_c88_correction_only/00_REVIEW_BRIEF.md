# UAV G0 correction-only code-science alignment brief

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_target_bound_correction_only
compute_budget=zero
scientific_iteration_cost=zero
audit_target_commit=c88f43de6451c40defefd7c679ba8d353c45735c
implementation_code_commit=c88f43de6451c40defefd7c679ba8d353c45735c
source_blob_sha256=b0baab9c47c2537217b689699d0520f158355e3d
prior_aligned_implementation_commit=c4d54e54978d98430c22c2cf21b789dd73c72d52
prior_aligned_source_blob_sha256=95b46e29ee44cc16ba5c5e91757b704be33e094e
prior_alignment_stage_commit=7a9190274f3dcde4eb168b2ec65fbcaf8b99a1c3
formal_compute_started=false
```

This is a single zero-compute correction-only audit. The only changed
claim-bearing behavior is the initial `position_trace[0]` serialization in
`run_g0_episode`: it is now converted from target-owned internal order to the
frozen storage/physical-slot order before evidence is recorded. Environment
state, actions, tracker, ownership/permutation certificates, R=273, NO_EVENT
R=NONE, metrics, estimators, seeds, thresholds, artifact schemas and formal
closure are otherwise unchanged.

Do not redesign G0, select a result, start readiness or scientific compute, or
merge G51. Decide only whether this evidence-order correction remains aligned
with the frozen G0 source-identifiability and reconstruction contracts.
