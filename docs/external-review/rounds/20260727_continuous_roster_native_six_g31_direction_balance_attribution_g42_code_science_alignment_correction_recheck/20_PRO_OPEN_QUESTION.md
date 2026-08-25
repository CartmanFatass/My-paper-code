# External Pro: G42 code-science alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=e21a1464e186260878649ad170bc3f32b8b9496d
repair_implementation_code_commit=e21a1464e186260878649ad170bc3f32b8b9496d
superseded_implementation_code_commit=43df85e9ebf384f0baf6d44758ef62aeb5e7fe7b
original_alignment_stage_commit=e991af230f694f7fba8fa394eb662c8c8cc74f04
original_audit_target_commit=43df85e9ebf384f0baf6d44758ef62aeb5e7fe7b
original_mismatch=docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_code_science_alignment_audit/21_PRO_OPEN_RAW.md
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_INDEX.md
fresh_runtime_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_code_science_alignment_audit/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_code_science_alignment_audit/01_SHARED_SOURCE_MANIFEST.md`
- `ha_ctse_process/continuous_roster_native_six_g31_direction_balance_attribution_g42.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_direction_balance_attribution_g42_test.py`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
only the exact target and listed evidence. Do not reopen the complete G42 audit.

The original raw records one bounded mismatch: the accepted implementation
treated a zero registered DB actor-gradient norm as an invalid path instead of
submitting exact zero NO_DB actor gradients with baseline and Adam exposure;
validated only global immediate/successor norms rather than finite per-group
actor channels and separate live immediate/successor baseline outputs; and did
not require a DB/raw unit-direction distance above `1e-6` in the nonformal
package and in every formal replicate before a conclusion-bearing checkpoint
or branch.

## Correction-only question

Does repair commit `e21a1464e186260878649ad170bc3f32b8b9496d` close only those
exact G42 mismatches, without changing any other frozen G42 contract or formal
authority?

Verify only:

1. A zero registered direction-balanced global actor-gradient norm produces
   exact zero NO_DB actor gradients while preserving identical baseline updates
   and Adam-step exposure; a positive registered norm with zero or nonfinite raw
   sum still fails closed before any optimizer step.
2. Before any conclusion-bearing checkpoint or branch, both global actor
   channels are live, every registered actor group has finite channels and at
   least one live channel in both arms, and immediate and successor baseline
   output gradients are separately live. The diagnostics are serialized and
   scope-validated rather than inferred from only global norms.
3. DB-versus-raw unit-direction distance is serialized on every valid update;
   the nonformal package requires at least one strict distance `>1e-6`, and each
   formal replicate requires at least one such distance before its conclusion
   gate. An always-collinear treatment fails this gate.
4. The repair changes no source, target, optimizer inventory, seed law,
   threshold, evidence volume, confidence procedure, branch order, backend,
   environment, or formal/nonformal authority. No runtime or formal compute has
   started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this correction closes only the original
  mismatch and the target remains conformant to the frozen G42 contract.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run,
or reopen any other alignment point. Stop after the single scoped disposition.
