# G41 trusted-anchor authority correction recheck v2

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=single_remaining_correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9
repair_implementation_code_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9
superseded_implementation_code_commit=0ce9c5ddbf77d4189f1994631a982b55ebae8282
original_alignment_stage_commit=f1019274851616b9c215bf2252e5e3a628258e61
prior_recheck_stage_commit=819fc2f0024f85a18d0fef39227a058d8a0f65e7
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The prior correction recheck found that a caller could still self-select a
fresh model's digest and pass it as `trusted_anchor_digest`. Code Project
Manager accepted a second correction that removes the caller-selected digest
interface, freezes the three manifest-backed accepted-G40 authority entries,
validates the Git-addressable replicate-0 payload and G40 digest encoding
before any model/projection construction, and rejects fresh, tampered,
wrong-replicate, malformed and self-consistent rewritten payloads.

This v2 recheck is restricted to that one remaining trust-boundary mismatch.
It cannot reopen the G41 audit, alter the retained graph/credit/update kernel,
or authorize any runtime or formal compute.
