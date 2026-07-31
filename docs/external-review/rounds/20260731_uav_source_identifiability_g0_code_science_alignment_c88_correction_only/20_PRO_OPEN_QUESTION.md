# External Pro open question: UAV G0 correction-only alignment

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_target_bound_correction_only
compute_budget=zero
audit_target_commit=c88f43de6451c40defefd7c679ba8d353c45735c
implementation_code_commit=c88f43de6451c40defefd7c679ba8d353c45735c
source_blob_sha256=b0baab9c47c2537217b689699d0520f158355e3d
prior_aligned_implementation_commit=c4d54e54978d98430c22c2cf21b789dd73c72d52
prior_aligned_source_blob_sha256=95b46e29ee44cc16ba5c5e91757b704be33e094e
prior_alignment_stage_commit=7a9190274f3dcde4eb168b2ec65fbcaf8b99a1c3
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded audit. Use the connected GitHub repository connector for
`https://github.com/CartmanFatass/My-paper-code.git`, branch `aggressive`, and
read only the allow-list in `01_SHARED_SOURCE_MANIFEST.md` at exact target
commit `c88f43de6451c40defefd7c679ba8d353c45735c`. Do not use a local working
tree, runtime logs, unlisted files, or compute. Do not activate Answer now.

Return exactly one token and no Chinese summary:

`AUDIT_DISPOSITION=ALIGNED`
`AUDIT_DISPOSITION=MISMATCH`
`AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY`

Use `ALIGNED` only if the exact c88 bytes remain a conformance
implementation of the frozen G0 source-identifiability, tracker/permutation,
and formal-interface reconstruction contracts. Use `MISMATCH` only with a
concrete target-bound conflicting path/symbol/behavior and the smallest
in-contract correction. Use `SCIENTIFIC_AMBIGUITY` only for an unstated
result-changing scientific choice. Do not redesign, add evidence or
thresholds, start compute, or select a scientific result.

Check these exact assertions:

1. The only claim-bearing source change from the prior aligned c4 target is
   `run_g0_episode` step-zero evidence ordering: `position_trace[0]` is
   serialized as `np.asarray(env.uav_positions, dtype=float64)[env._storage_to_internal]`,
   i.e. frozen storage/physical-slot order, while subsequent traces and the
   environment state remain unchanged.
2. The correction makes the serialized initial positions use the same order
   consumed by the accepted tracker/permutation validators. It does not alter
   target selection, actions, ownership, permutation semantics, R=273 for
   registered EVENT episode 0, NO_EVENT R=NONE, lifecycle/qualification
   counters, metrics, estimators, RNG, thresholds, or any result branch.
3. The indexed production tests at c88 exercise the corrected evidence path
   and preserve all frozen G0 certificates and artifact gates. Any mismatch
   must identify the exact target-bound symbol/behavior and a minimal repair;
   do not infer a defect from old c4 evidence or from runtime results.
4. The formal runner remains identity-only and fail-closed: the c88 source blob
   must not inherit the old c4 ALIGNED identity without this correction-only
   disposition and a new stage identity. No readiness or formal compute is
   authorized by this question.

Stop after this single scoped disposition.
