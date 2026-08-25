# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
implementation_code_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
original_audit_target_commit=ae1e01c64643b816fd15534fbfd46d16d3bf2f17
design_contract_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
readiness_contract=UAV_G0_READINESS_PERFORMANCE_CONTRACT_V2
formal_compute_started=false
```

External Pro may inspect only these repository-relative paths at the exact
audit target commit:

- `docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md`
- `docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260730_uav_source_identifiability_g0_executable_contract_addendum_v2/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260730_uav_source_identifiability_g0_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `ha_ctse_process/uav_source_identifiability_g0.py`
- `scripts/run_uav_source_identifiability_g0.py`
- `tests/ha_ctse_process_uav_source_identifiability_g0_test.py`
- `tests/run_uav_source_identifiability_g0_test.py`

Do not read CURRENT_WORK, runtime logs, workflow files, G50/G51 material, or
any path outside this allow-list. The question and this manifest are the
complete evidence boundary.
