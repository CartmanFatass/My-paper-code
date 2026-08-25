# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
audit_target_commit=7a283c88e45ca9ce7c3cdad1e19bddd39b757921
implementation_code_commit=87f4dfbe56b36f31d34f134a3c350bd766fae8d7
code_delta_from_implementation_to_audit_target=none
formal_compute=not_started
```

External Pro may inspect only these paths at the exact audit target commit:

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260726_continuous_roster_history_proxy_coherence_g37_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260726_continuous_roster_history_proxy_coherence_g37_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37.md`
- `docs/research/designs/CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_PRELAUNCH.md`
- `ha_ctse_process/continuous_roster_history_proxy_coherence_g37.py`
- `scripts/run_continuous_roster_history_proxy_coherence_g37.py`
- `tests/ha_ctse_process_continuous_roster_history_proxy_coherence_g37_test.py`
- `tests/run_continuous_roster_history_proxy_coherence_g37_test.py`
- `ha_ctse_process/continuous_roster_history_proxy_free_cs_g36.py`
- `scripts/run_continuous_roster_history_proxy_free_cs_g36.py`
- `ha_ctse_process/continuous_roster_reactive_reduction_g35.py`
- `scripts/run_continuous_roster_reactive_reduction_g35.py`
- `ha_ctse_process/runtime_capacity_continuous_roster_g32.py`
- `ha_ctse_process/continuous_roster_random_process_g34.py`
- `scripts/run_continuous_roster_random_process_g34.py`

The question, this manifest and `00_REVIEW_BRIEF.md` are the complete package.
No runtime log needs to be fetched: the prelaunch note contains PM's mechanical
acceptance, while this audit concerns code-science correspondence. Every G33
path, `CURRENT_WORK.md`, workflow-design file and unrelated round is excluded.
