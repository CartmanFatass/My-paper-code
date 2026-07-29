# External Pro: G50 common fast-anchor attribution code-science alignment correction recheck

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck
audit_mode=read_only_smallest_in_contract_correction_diff
round=20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_correction_recheck
stage_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
audit_target_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
repair_implementation_code_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
superseded_implementation_code_commit=5aeb3b7745847ca39edf556af29067506ead4c00
original_alignment_stage_commit=5aeb3b7745847ca39edf556af29067506ead4c00
original_audit_target_commit=5aeb3b7745847ca39edf556af29067506ead4c00
original_mismatch=docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_audit/21_PRO_OPEN_RAW.md
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_INDEX.md
fresh_runtime_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_audit/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_audit/01_SHARED_SOURCE_MANIFEST.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py`
- `scripts/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_test.py`
- `tests/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_test.py`
- `ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `ha_ctse_process/continuous_roster_native_six_g31_realized_successor_channel_attribution_g48.py`
- `scripts/run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48.py`
- `ha_ctse_process/continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49.py`
- `scripts/run_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49_test.py`
- `tests/run_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49_test.py`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_result_contract_clarification_g50/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260729_g31_common_fast_anchor_result_contract_clarification_g50/50_MECHANICAL_INTAKE_RECORD.md`

Read these exact paths from `stage_commit=b8290699f5c10c593bbc21a6666c17950fae84d3`; do not inspect or infer from any other path.

## Correction-only question

Does repair commit `b8290699f5c10c593bbc21a6666c17950fae84d3` close only the
original G50 code-science mismatch, without changing any other frozen G50
contract or formal authority?

The original bounded mismatch was this target behavior: `select_g50_result_branch`
used `not source_valid OR reference_access_confident_fail` for priority 2,
although the frozen result contract requires priority 2 whenever
`not source_valid OR not reference_access_pass`. A non-confident absolute
reference-access failure therefore could bypass the failure branch. The
smallest requested repair is to use `not reference_access_pass`, retain
`reference_access_confident_fail` as diagnostic-only evidence, keep the null
advantage predicate unchanged, and add a focused first-match witness for
`reference_access_pass=false` with `reference_access_confident_fail=false`.

Verify only:

1. The target selector now uses `not source_valid OR not reference_access_pass`
   for priority 2, and this failure branch retains precedence over favorable
   stored comparative booleans. `reference_access_confident_fail` is not used
   as a substitute for absolute reference access.
2. The focused proof exercises the non-confident absolute reference-access
   failure witness and requires `SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50`, while
   preserving the existing source-invalid witness and the unchanged null-side
   advantage predicate.
3. All protected G50 semantics remain unchanged: complete G40 Phase-A graph and
   disjoint fresh arms; G40 normalized reference credit; G49 centered/RMS raw
   reward null credit with zero null baseline reads; q_A activation and group
   liveness gates; physical Phase-A deletion and fresh actor-only Phase-B Adam;
   source, seeds, budgets, pairing, backend, confidence floors, margin and
   first-match branch order; final-only artifacts, reload checks and formal
   admission closure.
4. No source, target, optimizer inventory, seed law, threshold, evidence volume,
   confidence procedure, environment, backend, formal/nonformal authority or
   scientific claim ceiling changed. No runtime or formal compute has started.

Return exactly one terminal disposition:

- `AUDIT_DISPOSITION=ALIGNED` if this correction closes only the original
  mismatch and the target remains conformant to the frozen G50 contract.
- `AUDIT_DISPOSITION=MISMATCH` only with the remaining exact conflicting path or
  behavior and the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one unstated,
  result-changing scientific choice that prevents this limited judgment.

Do not accept or redesign code, request a new algorithm/source/threshold/run,
or reopen any other alignment point. Stop after the single scoped disposition.
