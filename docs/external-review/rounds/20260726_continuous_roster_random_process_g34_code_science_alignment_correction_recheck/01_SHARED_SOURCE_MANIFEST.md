# Shared source manifest

```text
repository=https://github.com/CartmanFatass/My-paper-code.git
branch=aggressive
original_audit_target_commit=599e3b2c9209f969baceb1e1a452953fa4375900
repair_implementation_code_commit=973589414a865cf79ef9f80a33a8feb2d4aabf40
recheck_target_commit=15f95889f4a318905ba45a1977b5e9079d114545
comparison=599e3b2c9209f969baceb1e1a452953fa4375900..15f95889f4a318905ba45a1977b5e9079d114545
formal_compute=not_started
```

External Pro may inspect only these paths at the exact recheck target and, only
where needed to identify the repaired diff, their versions at the original
audit target:

- `.agents/roles/EXTERNAL_PRO.md` — authority and output interface.
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md` — correction-only recheck boundary.
- `docs/external-review/rounds/20260726_continuous_roster_random_process_g34_design_assertion_audit/21_PRO_OPEN_RAW.md` — frozen scientific contract.
- `docs/external-review/rounds/20260726_continuous_roster_random_process_g34_code_science_alignment_audit/20_PRO_OPEN_QUESTION.md` — original audit scope.
- `docs/external-review/rounds/20260726_continuous_roster_random_process_g34_code_science_alignment_audit/21_PRO_OPEN_RAW.md` — exact mismatch and required smallest correction.
- `docs/external-review/rounds/20260726_continuous_roster_random_process_g34_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md` — original response transport identity.
- `docs/research/designs/CONTINUOUS_ROSTER_RANDOM_PROCESS_G34.md` — PM realization record.
- `docs/research/designs/CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_CODE_SCIENCE_INDEX.md` — corrected critical-point navigation index.
- `docs/research/cdc/EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_ALIGNMENT_CORRECTION_PRELAUNCH.md` — PM repair evidence and formal block.
- `ha_ctse_process/continuous_roster_random_process_g34.py` — serialized episode trace production.
- `scripts/run_continuous_roster_random_process_g34.py` — exact-checkpoint binding, trace recomputation, validation and analysis.
- `tests/ha_ctse_process_continuous_roster_random_process_g34_test.py` — trace-shape regression.
- `tests/run_continuous_roster_random_process_g34_test.py` — wrong-checkpoint and summary/trace tamper regressions.
- `scripts/run_runtime_capacity_continuous_roster_g32.py` — inherited strict checkpoint loader and state-digest reference.

The question, this manifest and `00_REVIEW_BRIEF.md` are the complete recheck
package. No runtime log is in scope. The prelaunch note reports PM's mechanical
evidence only; this review remains a source-level conformance diff.
