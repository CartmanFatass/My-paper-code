# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=e322f817abab49b56dd7c53ad1c09cd2b081b0aa
repair_implementation_code_commit=e322f817abab49b56dd7c53ad1c09cd2b081b0aa
superseded_implementation_code_commit=6d8b18066d312d8733d08a9e9356f12760ec2f79
original_alignment_stage_commit=1b801240b304aee070d96d1b862d9c88aad5b704
fresh_runtime_compute=not_started
```

External Pro may inspect only these paths and their exact target/diff history:

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

The primary review surface is the implementation diff from the superseded
commit to the target. This package, its allow-list and the exact original raw
are the complete correction-only boundary. Runtime logs, `CURRENT_WORK.md`,
workflow files, G33 material and unrelated rounds are excluded.
