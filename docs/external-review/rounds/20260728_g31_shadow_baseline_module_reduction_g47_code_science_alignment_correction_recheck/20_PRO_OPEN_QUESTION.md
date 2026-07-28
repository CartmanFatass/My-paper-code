# External Pro: G47 code-science alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=fab68ae1a87578b59c1a004ac5415edf55ee7452
repair_implementation_code_commit=fab68ae1a87578b59c1a004ac5415edf55ee7452
superseded_implementation_code_commit=744ebe8495c18a6e36e851da384ccd21351615e1
original_alignment_stage_commit=97cd2518f63d3273548c22033b028c408b46af93
original_audit_target_commit=744ebe8495c18a6e36e851da384ccd21351615e1
original_mismatch=docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/21_PRO_OPEN_RAW.md
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_CODE_SCIENCE_INDEX.md
fresh_runtime_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/01_SHARED_SOURCE_MANIFEST.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47_test.py`
- `tests/run_continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47_test.py`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect only the exact target and listed evidence. Do not reopen the complete G47 audit.

The original raw records one bounded mismatch: the reduced actor/replay/trace path still indexed and forwarded the baseline-only true-current-state view `trajectory.critic_states[time]` into the retained actor step, while the frozen reduced contract requires no baseline-only true-state input consumer in that arm.

## Correction-only question

Does repair commit `fab68ae1a87578b59c1a004ac5415edf55ee7452` close only that exact G47 mismatch, without changing any other frozen G47 contract or formal authority?

Verify only:

1. The reduced actor/replay/trace path no longer accepts, indexes, forwards, validates or otherwise consumes `trajectory.critic_states` or an equivalent baseline-only true-state accessor. The reduced actor-only callable has no `critic_state` argument; the reference arm may retain its baseline-only path.
2. The static dependency certificate reconstructs zero baseline-only true-state reads into the reduced actor gradient, reduced action/log-probability and reduced evaluation paths; these counts are not literal constants. A focused read-trapping baseline-only true-state guard covers replay/trace/update/checkpoint construction/reload while preserving the reference path.
3. All protected G47 semantics remain unchanged: accepted G46 provenance and G40 anchor authority; genuine baseline-module/parameter/optimizer/checkpoint deletion; target-only `r_t` and `G_(t+1)` residuals; separate centering; independent per-channel RMS scaling; literal `0.5*(g_I+g_S)`; common entropy; two persistent PPO passes; per-parameter Adam projection/order; the same stored 8x48 trajectory; final-only checkpoint inventory; C++ backend requirement; and formal-admission closure.
4. No source, target, optimizer inventory, seed law, threshold, evidence volume, confidence procedure, branch order, environment, backend, formal/nonformal authority or scientific claim ceiling changed. No runtime or formal compute has started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this correction closes only the original mismatch and the target remains conformant to the frozen G47 contract.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated, result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run, or reopen any other alignment point. Stop after the single scoped disposition.
