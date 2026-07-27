# G41 code-science alignment correction recheck brief

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=0ce9c5ddbf77d4189f1994631a982b55ebae8282
repair_implementation_code_commit=0ce9c5ddbf77d4189f1994631a982b55ebae8282
superseded_implementation_code_commit=dedc8bfa9d4054e55a06bdd8ed8f637142e55ea7
original_alignment_stage_commit=f1019274851616b9c215bf2252e5e3a628258e61
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The original G41 code-science alignment audit returned one concrete mismatch:
the accepted projection self-certified an arbitrary fast-phase G40-shaped
model by deriving its own anchor digest. Code Project Manager accepted one
correction that requires an independently trusted accepted-G40 anchor digest
before projection, optimizer or checkpoint construction and adds fresh,
tampered and malformed-digest fail-closed guards.

This recheck is restricted to that one counterexample and its smallest
in-contract correction. It cannot reopen the complete G41 audit or change the
retained graph, credit rule, update kernel, initialization, source, seeds,
exposure, tolerances, evidence bound or formal authority. No runtime or formal
compute is authorized.
