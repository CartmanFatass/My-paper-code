# External Pro open question: G39 alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=e322f817abab49b56dd7c53ad1c09cd2b081b0aa
repair_implementation_code_commit=e322f817abab49b56dd7c53ad1c09cd2b081b0aa
superseded_implementation_code_commit=6d8b18066d312d8733d08a9e9356f12760ec2f79
original_alignment_stage_commit=1b801240b304aee070d96d1b862d9c88aad5b704
frozen_contract=docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/21_PRO_OPEN_RAW.md
original_mismatch=docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_code_science_alignment_audit/21_PRO_OPEN_RAW.md
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_INDEX.md
fresh_runtime_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_coordinate_training_g39.py`
- `scripts/run_continuous_roster_native_six_coordinate_training_g39.py`
- `tests/ha_ctse_process_continuous_roster_native_six_coordinate_training_g39_test.py`
- `tests/run_continuous_roster_native_six_coordinate_training_g39_test.py`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
only the exact target and the listed evidence. Do not reopen the complete G39
audit.

The original raw records one mismatch: the initial first-batch audit proved
the two affected affines, 136 removable CONST scalars and 34 native effective
biases, but did not prove a finite live actual-objective gradient path for every
remaining registered actor, critic and credit-baseline group in each arm.

Question: does repair commit `e322f817abab49b56dd7c53ad1c09cd2b081b0aa` close
only that exact mismatch, on the same first paired 8-by-48 batch, by requiring
the exact registered group inventory in both arms to be finite and live above
`1e-12` for both fast and return-to-go objectives, while retaining the original
analytic relations and all 136 treated-scalar checks?

Verify only:

1. The actual initial gradient audit now includes every registered common
   actor, critic and credit-baseline group in both arms, in addition to the
   original affected affine, scalar and effective-bias checks. It binds
   serialized per-group results rather than relying on an incomplete top-level
   Boolean.
2. A focused guard makes one unaffected common actor, critic or baseline group
   dead while the 136 treated-scalar checks remain live, and that condition
   fails before the first optimizer step. Record tampering cannot substitute
   for the actual per-group result.
3. The repair preserves the exact frozen graph, intended 136-scalar/Adam/fold
   treatment, initialization map, optimizer, source, seed law, paired
   collection/update exposure, confidence plan, thresholds, evidence volume,
   first-match order and formal-authority binding. No runtime or formal compute
   has started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this correction closes the exact original
  mismatch without a frozen-contract or authority change.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run,
or reopen any other alignment point. Stop after the single scoped disposition.
