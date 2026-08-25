# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=6d8b18066d312d8733d08a9e9356f12760ec2f79
implementation_code_commit=6d8b18066d312d8733d08a9e9356f12760ec2f79
code_delta_from_implementation_to_audit_target=none
nonformal_compute=not_started
formal_compute=not_started
```

External Pro may inspect only these paths at the exact audit target commit:

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_coordinate_training_g39.py`
- `scripts/run_continuous_roster_native_six_coordinate_training_g39.py`
- `tests/ha_ctse_process_continuous_roster_native_six_coordinate_training_g39_test.py`
- `tests/run_continuous_roster_native_six_coordinate_training_g39_test.py`

The question, this manifest and `00_REVIEW_BRIEF.md` are the complete package.
No runtime log exists or needs to be fetched. `CURRENT_WORK.md`, workflow files,
G33 material, unrelated review rounds and all unlisted paths are excluded.
