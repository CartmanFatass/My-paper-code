# External Pro: G41 trusted-anchor authority correction recheck v2

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=single_remaining_correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9
repair_implementation_code_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9
superseded_implementation_code_commit=0ce9c5ddbf77d4189f1994631a982b55ebae8282
prior_recheck_stage_commit=819fc2f0024f85a18d0fef39227a058d8a0f65e7
original_alignment_stage_commit=f1019274851616b9c215bf2252e5e3a628258e61
original_mismatch=docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_audit/21_PRO_OPEN_RAW.md
prior_recheck_mismatch=docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_correction_recheck/21_PRO_OPEN_RAW.md
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
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_correction_recheck/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_code_science_alignment_correction_recheck/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/EVIDENCE_NOTES/fixtures/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/README.md`
- `docs/research/cdc/EVIDENCE_NOTES/fixtures/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/replicate_0_common_native6_fast_anchor.pt`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_slow_critic_reduction_g41_test.py`

Inspect only the exact target and listed evidence. Do not reopen the complete
G41 audit or select a successor.

## Correction-only question

Does repair commit `a5f63c349228fc2bba7843647e0ae4c34361c1c9` close only the
remaining self-selectable-anchor mismatch from the prior recheck?

Verify only:

1. The caller-selected digest interface is gone. Projection authority is
   selected only from the frozen three accepted-G40 manifest entries and the
   immutable Git-addressable replicate-0 fixture. Before any model, path,
   optimizer or projected-checkpoint construction, the payload source commit,
   schema, algorithm, source id, formal flag, checkpoint kind, replicate,
   `completed_anchor_updates=100`, configuration identity, file identity and
   complete-state digest must be validated using the G40 digest encoding.
2. The exact guard rejects `fresh` with its own digest, tampered state,
   malformed digest, wrong replicate, `completed_anchor_updates=200`, a
   locally self-signed payload and a self-consistent projected-checkpoint
   authority rewrite. The positive path loads the archived replicate-0 fixture
   rather than synthesizing a model or update.
3. The repair changes no retained graph, G31 credit/update equations, optimizer
   constants, source backend, seeds, pairing, exposure, evaluation,
   tolerances, evidence bound, branch order, complexity bound or
   formal/nonformal authority. No runtime or formal compute has started.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this v2 correction closes only the remaining
  mismatch and the target remains conformant to the frozen G41 contract.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path
  or behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run,
or reopen any other alignment point. Stop after this single scoped disposition.
