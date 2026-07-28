# G47 code-science alignment correction recheck brief

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
compute_budget=zero
audit_target_commit=fab68ae1a87578b59c1a004ac5415edf55ee7452
repair_implementation_code_commit=fab68ae1a87578b59c1a004ac5415edf55ee7452
superseded_implementation_code_commit=744ebe8495c18a6e36e851da384ccd21351615e1
original_alignment_stage_commit=97cd2518f63d3273548c22033b028c408b46af93
original_audit_target_commit=744ebe8495c18a6e36e851da384ccd21351615e1
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The original G47 code-science alignment audit returned one bounded mismatch: the reduced actor/replay/trace path still consumed the baseline-only true-current-state view through `trajectory.critic_states`, despite the frozen structural deletion requiring no such reduced-arm input consumer.

This correction-only recheck is restricted to that exact input-dependency deletion, its static dependency certificate and the focused read-trapping guard. It cannot reopen the complete G47 audit or change source, target, optimizer inventory, seed law, thresholds, evidence volume, confidence procedure, branch order, environment, backend or formal authority. No runtime or formal compute is authorized.

