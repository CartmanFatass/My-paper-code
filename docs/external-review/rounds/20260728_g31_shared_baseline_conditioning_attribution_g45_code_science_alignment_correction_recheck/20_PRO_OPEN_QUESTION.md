# External Pro: G45 code-science alignment correction recheck

review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=correction_recheck
compute_budget=zero
audit_target_commit=a42da997712d9c941ac9a6ca08992f4c5de033a2
repair_implementation_code_commit=a42da997712d9c941ac9a6ca08992f4c5de033a2
original_audit_target_commit=1c38e387fa7fe90dc6446177eb69146a12a29a20
original_stage_commit=8dec3a94aff7aaa28f6533eecc987acbd6e0c35c
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_INDEX.md
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY

You are External GPT-5.6 Pro, the exclusive scientific authority for this
bounded correction-only contract recheck. Read exactly the paths in
01_SHARED_SOURCE_MANIFEST.md from the exact pushed audit target commit. Do not
implement, compute, redesign, edit CDC, authorize a run, reopen G44, select a
successor, or reactivate G33.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/report/ITERATION_34.md`
- `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45.py`
- `scripts/run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45_test.py`
- `tests/run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py`
- `scripts/run_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py`
- `ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `ha_ctse_process/continuous_roster_native_six_g31_db_norm_schedule_attribution_g43.py`

## Exact correction target

The prior G45 code-science audit at
`1c38e387fa7fe90dc6446177eb69146a12a29a20` archived
`AUDIT_DISPOSITION=MISMATCH` because the baseline liveness gate reduced each
baseline loss to one whole-module norm and did not separately bind the shared
first-layer trunk or the two output rows. The exact prior raw response and
intake are allow-listed above; do not infer any additional mismatch.

The repaired target is `a42da997712d9c941ac9a6ca08992f4c5de033a2`. Verify only
whether it resolves that exact assertion while preserving the frozen G45
comparison: READ subtracts the detached immediate/successor baseline outputs
from actor credit, NO_READ uses raw immediate/successor credit, both retain the
same baseline module, targets, losses, optimizer exposure, G44 independent
channel centering/RMS scaling, literal `0.5*(g_I+g_S)`, paired source/RNG/order,
and artifact/checkpoint provenance.

The correction claims the following code-facing evidence predicates:

- `immediate_output_row_gradient_norm > 1e-12`
- `successor_output_row_gradient_norm > 1e-12`
- `shared_trunk_union_gradient_norm > 1e-12`
- `all_group_gradients_finite=true`
- shared-trunk union reconstructed from immediate- and successor-loss
  gradients of `credit_baselines.0.{weight,bias}`
- output evidence reconstructed from the corresponding rows of
  `credit_baselines.2.{weight,bias}`
- these groups serialized and revalidated through update, conclusion,
  checkpoint and artifact-reload evidence
- focused guards cover dead-trunk/live-output and live-trunk/dead-required-
  output cases

Return exactly one line:

`AUDIT_DISPOSITION=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY`

If and only if the disposition is `MISMATCH`, append one concrete counterexample
bound to the exact target commit. This is not a redesign or a request for
scientific computation.
