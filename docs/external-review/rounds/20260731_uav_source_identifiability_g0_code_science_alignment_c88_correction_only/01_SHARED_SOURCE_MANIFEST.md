# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=c88f43de6451c40defefd7c679ba8d353c45735c
implementation_code_commit=c88f43de6451c40defefd7c679ba8d353c45735c
source_blob_sha256=b0baab9c47c2537217b689699d0520f158355e3d
prior_aligned_implementation_commit=c4d54e54978d98430c22c2cf21b789dd73c72d52
prior_aligned_source_blob_sha256=95b46e29ee44cc16ba5c5e91757b704be33e094e
prior_alignment_stage_commit=7a9190274f3dcde4eb168b2ec65fbcaf8b99a1c3
formal_compute_started=false
```

External Pro may inspect only these repository-relative paths at exact target
commit `c88f43de6451c40defefd7c679ba8d353c45735c`:

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md`
- `docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md`
- `docs/external-review/rounds/20260730_uav_source_identifiability_g0_code_science_alignment_correction_recheck/21_PRO_OPEN_RAW.md`
- `ha_ctse_process/uav_source_identifiability_g0.py`
- `scripts/run_uav_source_identifiability_g0.py`
- `tests/ha_ctse_process_uav_source_identifiability_g0_test.py`
- `tests/run_uav_source_identifiability_g0_test.py`

Do not inspect runtime logs, `CURRENT_WORK.md`, workflow files, G50/G51
material, or any path outside this allow-list.
