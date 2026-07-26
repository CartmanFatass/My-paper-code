# G34 code-science alignment correction recheck brief

```text
review_type=CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK
audit_mode=correction_diff_only
compute_budget=zero
original_audit_target_commit=599e3b2c9209f969baceb1e1a452953fa4375900
original_disposition=MISMATCH
repair_implementation_code_commit=973589414a865cf79ef9f80a33a8feb2d4aabf40
recheck_target_commit=15f95889f4a318905ba45a1977b5e9079d114545
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

The original code-science audit identified exactly two result-changing paths:
model-bearing cells were not independently bound to their declared G32
checkpoint digests, and conclusion-bearing summaries were trusted instead of
being recomputed from serialized 48-step reward and roster-size traces. PM made
only that in-contract repair, reran the smallest affected evidence, accepted the
repaired code and pushed the exact recheck target.

This is the one permitted correction-only recheck. It asks only whether those
two exact mismatch paths are closed. It cannot reopen the frozen design, search
for unrelated defects, review style or engineering quality, request compute, or
introduce another algorithm, source, threshold, sample, estimand or experiment.

The false assertion this recheck can prevent is the same one named by the
original mismatch: a G34 positive branch based on a wrongly routed checkpoint
or on conclusion metrics not supported by the episode traces. The recheck is
read-only and zero-compute; formal execution remains blocked until `ALIGNED`.
