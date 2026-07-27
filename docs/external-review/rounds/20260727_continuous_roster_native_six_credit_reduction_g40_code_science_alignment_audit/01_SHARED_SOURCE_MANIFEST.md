# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=8fbc4964724b9eebdbecfb060a297d2ff55f60ed
implementation_code_commit=8fbc4964724b9eebdbecfb060a297d2ff55f60ed
code_delta_from_implementation_to_audit_target=none
formal_compute=not_started
nonformal_compute=not_started
```

External Pro may inspect only these paths at the exact audit target commit:

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py`
- `scripts/run_continuous_roster_native_six_credit_reduction_g40.py`
- `tests/ha_ctse_process_continuous_roster_native_six_credit_reduction_g40_test.py`
- `tests/run_continuous_roster_native_six_credit_reduction_g40_test.py`
- `ha_ctse_process/continuous_roster_native_six_coordinate_training_g39.py`
- `scripts/run_continuous_roster_native_six_coordinate_training_g39.py`
- `ha_ctse_process/continuous_roster_toy_cpp_backend.py`
- `ha_ctse_process/native/continuous_roster_toy_backend.cpp`
- `ha_ctse_process/continuous_roster_random_process_g34.py`
- `ha_ctse_process/runtime_capacity_continuous_roster_g32.py`
- `ha_ctse_process/return_to_go_direction_balanced_full_actor_g31.py`

The question, this manifest and `00_REVIEW_BRIEF.md` are the complete
package. No runtime log needs to be fetched: this audit concerns only code
and frozen-science correspondence. `CURRENT_WORK.md`, workflow files, G33
material, unrelated rounds and all unlisted paths are excluded.
