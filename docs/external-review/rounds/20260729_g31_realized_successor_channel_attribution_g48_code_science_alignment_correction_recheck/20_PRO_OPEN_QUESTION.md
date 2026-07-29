# External Pro: G48 code-science alignment correction recheck

```text
semantic_author=research_operations_manager
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
review_mode=read_only_contract_diff
round=20260729_g31_realized_successor_channel_attribution_g48_code_science_alignment_correction_recheck
audit_target_commit=d96f8f29367b55b5ea655b984631d6064877e237
original_audit_target_commit=5e2ace7199970634d79219f2858bb53aabf5a57e
repair_implementation_code_commit=d96f8f29367b55b5ea655b984631d6064877e237
prior_alignment_stage_commit=c6822acccbe681434ef723e06c398e87325ee58b
compute_budget=zero
submission_limit=exactly_one
recovery_submission_limit=zero
answer_now=forbidden
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro, the exclusive scientific authority for this
bounded correction-only contract recheck. Read only the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the exact `stage_commit`. Do not run
tests or compute, edit code/CDC, reopen the G48 design, select a successor or
reactivate G33. Compare only the repaired target against the prior mismatch.

## Exact evidence allow-list

- .agents/roles/EXTERNAL_PRO.md
- docs/project/ALGORITHM_PRINCIPLES.md
- docs/project/SCIENTIFIC_ASSERTION_AUDIT.md
- docs/project/EVIDENCE_COMPLEXITY_POLICY.md
- docs/external-review/OPEN_REVIEW_PRINCIPLES.md
- docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md
- docs/research/cdc/CONJECTURES.md
- docs/research/cdc/IDEA_PORTFOLIO.md
- docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_CODE_SCIENCE_INDEX.md
- docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_CODE_SCIENCE_INDEX.md
- docs/external-review/rounds/20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit/20_PRO_OPEN_QUESTION.md
- docs/external-review/rounds/20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit/21_PRO_OPEN_RAW.md
- docs/external-review/rounds/20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md
- docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/21_PRO_OPEN_RAW.md
- docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md
- docs/external-review/rounds/20260729_g31_realized_successor_channel_attribution_g48_design_assertion_audit/20_PRO_OPEN_QUESTION.md
- docs/external-review/rounds/20260729_g31_realized_successor_channel_attribution_g48_design_assertion_audit/21_PRO_OPEN_RAW.md
- docs/external-review/rounds/20260729_g31_realized_successor_channel_attribution_g48_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md
- ha_ctse_process/continuous_roster_native_six_g31_realized_successor_channel_attribution_g48.py
- tests/ha_ctse_process_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48_test.py

## Correction question

Does the repaired target at `audit_target_commit` correct the prior G48
activation mismatch by implementing the frozen unsquared complete-credit-vector
ratio

`||v_REF-v_NULL,cf||_2 / max(||v_REF||_2,||v_NULL,cf||_2)`

with the unchanged strict `q_target > 1e-6` and `q_credit > 1e-6`
thresholds, while preserving every other protected G48 source, target law,
null zero-read, normalization, gradient, pairing, optimizer, seed, evidence,
access, confidence, first-match and formal-authority field?

Check only:

1. `_activation_scalars` computes the unsquared ratio from the serialized
   squared sufficient statistics, with zero denominator yielding zero.
2. `validate_activation_record` independently reconstructs the same unsquared
   ratio and rejects the old squared statistic, stale treatment flags and
   nonfinite/invalid evidence.
3. The focused intermediate-ratio witness lies between `1e-6` and
   `1e-3`, and the repaired code/index no longer states the squared gate.
4. All other protected semantics remain unchanged; no new treatment arm, target
   law, optimizer exposure, seed, confidence, artifact or runtime path was
   introduced.
5. Formal entry remains closed pending this independent disposition and a fresh
   same-source preflight.

## Required response

Return these sections in order:

1. `CODE_SCIENCE_ALIGNMENT`
2. `FROZEN_CONTRACT_CONFORMANCE`
3. `CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE`
4. `MINIMAL_IN_CONTRACT_CORRECTION`
5. `PROTECTED_SEMANTICS`
6. `EVIDENCE_AND_COMPLEXITY`
7. `EXECUTABLE_BOUNDARY`
8. `中文简报`

Then return exactly one separate line:

`AUDIT_DISPOSITION=ALIGNED`
or `AUDIT_DISPOSITION=MISMATCH`
or `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY`.

The response must contain all eight sections and exactly one disposition line.
If and only if the disposition is `MISMATCH`, include one concrete target-bound
counterexample and the smallest correction. Do not propose redesign or compute.
