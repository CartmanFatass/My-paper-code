# External Pro: G44 channel-scale normalization attribution code-science alignment audit v2

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=CODE_SCIENCE_ALIGNMENT_AUDIT
round=20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_code_science_alignment_audit_v2
stage_commit=9cb582b74450abc8f610a989c6e53328877b7a4e
audit_target_commit=9cb582b74450abc8f610a989c6e53328877b7a4e
design_source_commit=be903852fa7d4faf56cba39b5776b693e3192b47
compute_budget=zero
nonformal_compute_started=false
formal_compute_started=false
answer_now=forbidden
```

You are External GPT-5.6 Pro and the exclusive scientific authority for this
bounded read-only conformance diff. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from `stage_commit`. Do not edit or accept code,
run tests or compute, reopen G44 design, reactivate G33, or authorize a formal
run or successor. This is a new target commit; do not inherit any disposition
from an earlier G44 commit.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_design_assertion_audit/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_design_assertion_audit/01_SHARED_SOURCE_MANIFEST.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py`
- `scripts/run_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_test.py`
- `tests/run_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_test.py`

Do not read runtime logs, unlisted tests, earlier implementation versions, or
paths outside this allow-list.

## Alignment question

Does the implementation at `audit_target_commit` instantiate the frozen G44
design in the completed design-audit evidence, without a result-changing path?
Judge only the exact target source, runner, tests, code-science index and frozen
design evidence in the allow-list.

Check mechanically:

1. The two arms are exactly `NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE` and
   `NATIVE6_G31_EQUAL_MEAN_POOLED_SCALE`, both retaining literal
   `0.5*(g_I+g_S)` and all accepted G40/G41/G42/G43 source, target, baseline,
   optimizer, checkpoint, RNG and lifecycle semantics.
2. Per-channel centering and pooled scale use exactly 384 one-team rows from
   H=48 and the 8-environment `[48,8]` contract, with no active-count weighting
   or episode exclusion. All required means, centered sums, scales, row count
   and normalization-mask digest are serialized and reconstructed. The pooled
   unscaled raw gradient may differ from `m_cf`; for `m_cf>0`, only the pooled
   raw direction rescaled to `m_cf` is assigned. For `m_cf=0`, assigned credit is
   exact zero; positive raw cancellation/nonfinite behavior fails closed before
   the optimizer.
3. Activation evidence reconstructs `q_direction` from serialized inner
   product and both norms, not from a trusted scalar. q-scale, norm, actor-group
   and both baseline-output liveness gates are exact and precede Adam. Entropy,
   baseline and Adam exposure remain identical and stale reuse is forbidden.
4. Native-six actor/log_std, realized-successor and immediate decomposition,
   PPO semantics, parameter/Adam inventory, mandatory C++ toy backend,
   deterministic merge, source ledgers, paired RNG and final-only checkpoints
   are preserved. No DB vector/norm/shadow, alternate reward/target/observation,
   search or hypothetical transition is introduced.
5. Exact seed block and nonformal offset, H=48, K_search=0, zero hypothetical
   transitions, evaluation cells/episodes, confidence unit, access floors,
   margin 0.05 and frozen first-match branch order are preserved and fail
   closed. Formal admission remains blocked until this independent alignment.
6. Tests and proof-only execution-readiness evidence do not broaden the claim;
   two-process bitwise checks and readiness are operational conformance only,
   not a nonformal or formal result.

Return exactly one terminal disposition token:

```text
AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY
```

`ALIGNED` requires every point to conform. `MISMATCH` requires the exact frozen
assertion, conflicting target path/behavior, and smallest in-contract
correction. `SCIENTIFIC_AMBIGUITY` is reserved for a previously unstated
result-changing scientific choice that prevents judgment. Do not propose a new
algorithm, threshold, evidence volume, experiment, formal run, or successor.
