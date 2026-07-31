# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
review_type=IMPLEMENTATION_ALIGNMENT_CLARIFICATION
clarification_type=ORACLE_GATE_FINITE_PRECISION_ARRIVAL_SEMANTICS
audit_target_source_commit=83bad9ebf489d24cb67ad30e10905cb0eb84f04a
execution_commit=9992701d814acc46d5a69d9b499b926f76a5d265
aligned_implementation_commit=c88f43de6451c40defefd7c679ba8d353c45735c
aligned_source_blob=b0baab9c47c2537217b689699d0520f158355e3d
alignment_stage_commit=499fcaac7acea4faf58268b71773459ef73bedec
failed_gate=gate_08
formal_root_status=TERMINAL_FAILED_PRESERVE_NO_RETRY
compute_budget=zero
scientific_iteration_cost=zero
```

External Pro may inspect only these repository-relative paths at the exact
commits named above:

- `ha_ctse_process/uav_source_identifiability_g0.py`
- `scripts/run_uav_source_identifiability_g0.py`
- `tests/ha_ctse_process_uav_source_identifiability_g0_test.py`
- `tests/run_uav_source_identifiability_g0_test.py`
- `docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md`
- `docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md`
- `docs/external-review/rounds/20260730_uav_source_identifiability_g0_formal_interface_contract_clarification_v2/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260731_uav_source_identifiability_g0_code_science_alignment_c88_correction_only/21_PRO_OPEN_RAW.md`

Do not inspect local runtime logs, `CURRENT_WORK.md`, workflow files, or any
unlisted path. Do not run code or compute.
