# External Pro: G41 code-science alignment correction recheck

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=0ce9c5ddbf77d4189f1994631a982b55ebae8282
repair_implementation_code_commit=0ce9c5ddbf77d4189f1994631a982b55ebae8282
superseded_implementation_code_commit=dedc8bfa9d4054e55a06bdd8ed8f637142e55ea7
original_alignment_stage_commit=f1019274851616b9c215bf2252e5e3a628258e61
original_mismatch=docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_audit/21_PRO_OPEN_RAW.md
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md
fresh_runtime_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_slow_critic_reduction_g41_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40.md`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
only the exact target and listed evidence. Do not reopen the complete G41 audit.

The original raw records one mismatch: `project_post_anchor_paths` accepted any
fast-phase G40-shaped model, derived its digest locally, and passed that digest
to the projection and static certificate. A fresh untrained model could thus
self-certify. The repair requires an independently trusted accepted-G40 anchor
digest before any projection, optimizer or checkpoint construction.

## Correction-only question

Does repair commit `0ce9c5ddbf77d4189f1994631a982b55ebae8282` close only that
exact self-certifying-anchor mismatch, without changing any other frozen G41
contract or formal authority?

Verify only:

1. Projection requires an independently trusted accepted-G40 complete-state
   digest or validated checkpoint payload, compares the supplied anchor before
   constructing either path, optimizer or projected checkpoint, and the static
   certificate validates against that same external digest rather than
   recomputing authority from the tested anchor.
2. Fresh, tampered, malformed-digest and self-consistent-checkpoint-rewrite
   cases fail closed before any optimizer step; the accepted anchor digest is
   deterministic under the registered CPU single-thread configuration and
   cannot be changed by test order or a serialized flag.
3. The repair changes no retained graph, G31 credit equation, optimizer
   constants, source backend, seeds, pairing, exposure, checkpoints,
   evaluation, tolerances, evidence bound, branch order, complexity bound or
   formal/nonformal authority. No runtime or formal compute has started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this correction closes only the original
  mismatch and the target remains conformant to the frozen G41 contract.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run,
or reopen any other alignment point. Stop after the single scoped disposition.
