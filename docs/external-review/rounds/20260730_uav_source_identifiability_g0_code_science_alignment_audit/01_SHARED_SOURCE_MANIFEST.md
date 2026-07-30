# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=d5aab62dde3ddd33f3a9864f77931174d4371f82
implementation_code_commit=d5aab62dde3ddd33f3a9864f77931174d4371f82
design_contract_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
readiness_workflow_commit=dc3d3af1be4c1d97725f9f7db50ef62456c090e1
formal_compute_started=false
```

External Pro may inspect only these repository-relative paths at the exact
audit target commit:

- `docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md`
- `docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260730_uav_g0_executable_contract_addendum_v2/21_PRO_OPEN_RAW.md`
- `ha_ctse_process/uav_source_identifiability_g0.py`
- `scripts/run_uav_source_identifiability_g0.py`
- `tests/ha_ctse_process_uav_source_identifiability_g0_test.py`
- `tests/run_uav_source_identifiability_g0_test.py`

Do not read CURRENT_WORK, runtime logs, G51/G50 material, workflow files, or
any path outside this allow-list. The question and this manifest are the
complete evidence boundary.
