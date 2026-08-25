# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=4c9a2bc4c491a338a78b0a52e741dc9de62c2924
repair_implementation_code_commit=8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04
superseded_implementation_code_commit=e96f0be154afcf778780bad6266458e211b4b047
original_audit_target_commit=3c1c7334e55b5f5c016bcbb9fa70c5073ee1fa28
formal_compute=not_started
```

External Pro may inspect only these paths and diffs at the exact target:

- `.agents/roles/EXTERNAL_PRO.md` — authority and output interface.
- `docs/external-review/rounds/20260726_continuous_roster_history_proxy_free_cs_g36_design_assertion_audit/21_PRO_OPEN_RAW.md` — frozen scientific contract.
- `docs/external-review/rounds/20260726_continuous_roster_history_proxy_free_cs_g36_code_science_alignment_audit/21_PRO_OPEN_RAW.md` — exact mismatch.
- `docs/research/designs/CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36.md` — corrected PM realization record.
- `docs/research/designs/CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_CODE_SCIENCE_INDEX.md` — corrected critical-point index.
- `docs/research/cdc/EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_PRELAUNCH.md` — replacement preflight evidence.
- `ha_ctse_process/continuous_roster_history_proxy_free_cs_g36.py` — corrected actor-input construction and unchanged G36 mechanism.
- `tests/ha_ctse_process_continuous_roster_history_proxy_free_cs_g36_test.py` — new end-to-end evaluator guard and existing focused checks.
- `scripts/run_continuous_roster_history_proxy_free_cs_g36.py` — unchanged validation, estimands, branches and authority.
- `tests/run_continuous_roster_history_proxy_free_cs_g36_test.py` — unchanged runner checks.

The implementation diff from `e96f0be154afcf778780bad6266458e211b4b047`
to `8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04` is the primary review surface.
The question, this manifest and `00_REVIEW_BRIEF.md` are the complete package.
