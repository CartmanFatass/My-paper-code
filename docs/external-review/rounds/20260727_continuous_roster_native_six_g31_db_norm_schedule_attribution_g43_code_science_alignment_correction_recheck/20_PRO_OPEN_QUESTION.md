# External Pro: G43 DB-norm schedule attribution code-science correction recheck

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
recheck_mode=correction_only
round=20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_code_science_alignment_correction_recheck
audit_target_commit=45e16f71d171228135b6444bee1678b157d79abe
original_audit_stage_commit=b04b053626501af775fb12b2cd7fcf84ffef4fbc
original_audit_target_commit=8646cdfba9b82790be6dfa168461b5e025120c83
compute_budget=zero
nonformal_compute_started=false
formal_compute_started=false
answer_now=forbidden
```

You are External GPT-5.6 Pro and the exclusive scientific authority for this
single correction-only recheck. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from `audit_target_commit`. Compare the prior
G43 mismatch raw response with the implementation and tests at the new target
commit. Do not reopen design, run tests or compute, edit code, perform a full
audit, or authorize formal execution.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_db_norm_schedule_attribution_g43.py`
- `scripts/run_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_test.py`
- `tests/run_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_test.py`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_code_science_alignment_correction_recheck/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_code_science_alignment_correction_recheck/01_SHARED_SOURCE_MANIFEST.md`

## Exact correction assertion to recheck

The prior audit’s frozen assertion was: treatment activation must be
reconstructed entirely from the DBNORM reference arm’s pre-update state; every
reference-arm pass must serialize its own `db_norm`, `raw_sum_norm`, and
`equal_mean_norm`; the null arm may not supply this gate evidence. The prior
conflict was that `_prepare_passes` formed `dbnorm` from DBNORM-arm gradients
but formed `mean` from independently evolving MEAN-arm gradients, then
`treatment_schedule_record` mixed the DBNORM `registered_gradient_norm` with
the MEAN `applied_gradient_norm` for `q`.

Confirm mechanically, and only for this assertion, that the target commit:

1. Builds the evidence-only equal-mean counterfactual `0.5*(g_I+g_S)` from
   the DBNORM arm’s own pre-update channel gradients; the actual MEAN arm update
   remains unchanged.
2. Serializes and reconstructs `q` only from DBNORM-arm `db_norm`, reference
   raw-sum norm, and reference equal-mean norm, with
   `evidence_source_arm=NATIVE6_G31_DBNORM_NO_SLOW`,
   `reference_equal_mean_counterfactual=true`, and
   `null_arm_evidence_read_count=0`.
3. Has a focused guard that changes only MEAN-arm gradients after branch
   divergence and proves reference-arm `q` and activation are unchanged; a
   reference-arm `q<=1e-6` cannot pass merely because the MEAN-arm norm differs.
4. Preserves the protected arm formulas, source/RNG/lifecycle pairing,
   optimizer and checkpoint semantics, thresholds, evidence volume and
   first-match order. The separately approved fixed process parallelism is
   launch-fixed and deterministic, but no parallel worker may alter the above
   scientific semantics.

Return exactly one terminal token:

```text
AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY
```

`ALIGNED` means the named prior mismatch is repaired at the exact target.
`MISMATCH` requires a target-bound counterexample and the smallest correction
only for the named assertion. `SCIENTIFIC_AMBIGUITY` is only for an unstated
result-changing choice that prevents this correction judgment. Do not propose a
new algorithm, threshold, evidence volume, experiment, or formal run.
