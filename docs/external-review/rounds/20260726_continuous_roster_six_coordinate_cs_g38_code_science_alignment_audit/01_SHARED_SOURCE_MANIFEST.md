# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=3b13ce0c6936fc5209e9ff7928aaaae61ec7200b
implementation_code_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
code_delta_from_implementation_to_audit_target=none
nonformal_compute=not_started
formal_compute=not_started
```

External Pro may inspect only these paths at the exact audit target commit:

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260726_continuous_roster_six_coordinate_cs_g38_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260726_continuous_roster_six_coordinate_cs_g38_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38.md`
- `docs/research/designs/CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_PRELAUNCH.md`
- `ha_ctse_process/continuous_roster_six_coordinate_cs_g38.py`
- `scripts/run_continuous_roster_six_coordinate_cs_g38.py`
- `tests/ha_ctse_process_continuous_roster_six_coordinate_cs_g38_test.py`
- `tests/run_continuous_roster_six_coordinate_cs_g38_test.py`
- `ha_ctse_process/continuous_roster_reactive_reduction_g35.py`
- `scripts/run_continuous_roster_reactive_reduction_g35.py`
- `ha_ctse_process/continuous_roster_random_process_g34.py`
- `scripts/run_continuous_roster_random_process_g34.py`
- `ha_ctse_process/runtime_capacity_continuous_roster_g32.py`
- `ha_ctse_process/anchored_residual_g19.py`
- `ha_ctse_process/return_to_go_direction_balanced_full_actor_g31.py`

The question, this manifest and `00_REVIEW_BRIEF.md` are the complete package.
No runtime log exists or needs to be fetched. Every G33 path, `CURRENT_WORK.md`,
workflow-design file and unrelated review round is excluded.
