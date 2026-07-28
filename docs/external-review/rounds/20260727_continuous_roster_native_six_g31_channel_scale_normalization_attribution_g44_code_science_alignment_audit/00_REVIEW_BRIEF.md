# G44 channel-scale normalization attribution code-science alignment audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
round=20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_code_science_alignment_audit
stage_commit=39a3cee897e9ac5615d21f25c21f6ccb925d407c
audit_target_commit=39a3cee897e9ac5615d21f25c21f6ccb925d407c
design_source_commit=be903852fa7d4faf56cba39b5776b693e3192b47
compute_budget=zero
nonformal_compute_started=false
formal_compute_started=false
submission_limit=exactly_one
recovery_submission_limit=zero
answer_now=forbidden
completion=natural_only
```

This is a read-only conformance diff of the accepted G44 implementation against
the completed G44 design audit. External Pro is the sole scientific authority.
The review authorizes no code edit, compute, formal admission, checkpoint use,
CDC edit, or successor action.

The only intended code change is the channel-scale attribution treatment. Keep
all accepted G40--G43 semantics fixed. In particular, the unscaled pooled raw
gradient may have a norm different from the independent-scale counterfactual
norm; the pooled assigned gradient is the pooled raw direction rescaled to that
counterfactual norm. The raw zero/nonfinite gates remain separate.

G33 is abandoned and outside this round. Report only the required disposition
token and bounded target-bound evidence.

The exact question and complete evidence allow-list are in
`20_PRO_OPEN_QUESTION.md` and `01_SHARED_SOURCE_MANIFEST.md`.
