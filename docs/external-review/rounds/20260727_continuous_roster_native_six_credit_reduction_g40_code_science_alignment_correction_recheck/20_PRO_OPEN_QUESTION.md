# External Pro open question: G40 alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
repair_implementation_code_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
superseded_implementation_code_commit=8fbc4964724b9eebdbecfb060a297d2ff55f60ed
original_alignment_stage_commit=79db3529ddc3a3e81ad818b007c6c8bf9bf1b130
frozen_contract=docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/21_PRO_OPEN_RAW.md
original_mismatch=docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_code_science_alignment_audit/21_PRO_OPEN_RAW.md
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md
fresh_runtime_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
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

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
only the exact target and listed evidence. Do not reopen the complete G40 audit.

The original raw records one mismatch: the common phase replaced the accepted
G39 shared two-output `credit_baselines` module with two private MLP trunks,
so the accepted baseline graph and common-phase optimization history were not
retained. The repair commit claims to keep the shared G39 module byte-for-byte
through the common phase and branch clones, while preserving ordinary-arm
shadow isolation.

Question: does repair commit
`97a8b237e0cec6c2713dd2a710d324040fa3dfc2` close only that exact mismatch,
without changing any other frozen G40-P0 contract or formal authority?

Verify only:

1. The common anchor and both branch clones retain the accepted G39 shared
   two-output `credit_baselines` graph, keys, shapes, parameter count,
   initialization bytes and optimizer state; no `IndependentCreditBaselines`
   replacement or private duplicate trunk remains. The two outputs are the
   immediate and successor baselines used by the frozen G40 credit paths.
2. The ordinary arm's two baseline losses remain shadow-only with respect to
   the actor and slow critic while the retained shared baseline module updates;
   focused tests prove omission of shadow losses leaves actor and slow-critic
   parameters bitwise unchanged while both shared-baseline output rows update.
   A branch-state tamper fails at the boundary before any optimizer step and
   cannot be hidden by a serialized-record flag.
3. The repair changes no credit equation, source backend, seeds, pairing,
   exposure, checkpoint, evaluation cell/order, optimizer constants,
   thresholds, confidence procedure, evidence volume, first-match branch order,
   complexity bound or exact formal-authority token. No runtime or formal
   compute has started, and no nonformal artifact authorizes a formal run.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this correction closes only the original
  mismatch and the target remains conformant to the frozen G40 contract.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run,
or reopen any other alignment point. Stop after the single scoped disposition.
