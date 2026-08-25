# Shared source manifest: G45 code-science alignment audit

repository=CartmanFatass/My-paper-code
branch=aggressive
round=20260728_g31_shared_baseline_conditioning_attribution_g45_code_science_alignment_audit
review_mode=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
audit_target_commit=1c38e387fa7fe90dc6446177eb69146a12a29a20
implementation_code_commit=1c38e387fa7fe90dc6446177eb69146a12a29a20
accepted_design_source_commit=5f99e484f172a53e98307e20ed5ac0b6af40638d
formal_compute=not_started
nonformal_compute=not_started
compute_budget=zero

The submitted question and the following paths are the complete allow-list.
Read only these paths from the exact audit target commit:

- .agents/roles/EXTERNAL_PRO.md
- docs/project/ALGORITHM_PRINCIPLES.md
- docs/project/SCIENTIFIC_ASSERTION_AUDIT.md
- docs/project/EVIDENCE_COMPLEXITY_POLICY.md
- docs/external-review/OPEN_REVIEW_PRINCIPLES.md
- docs/project/CURRENT_WORK.md
- docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md
- docs/research/cdc/CONJECTURES.md
- docs/research/cdc/IDEA_PORTFOLIO.md
- docs/report/ITERATION_34.md
- docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/21_PRO_OPEN_RAW.md
- docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md
- docs/external-review/rounds/20260727_g31_shared_baseline_conditioning_attribution_g45_design_assertion_audit/20_PRO_OPEN_QUESTION.md
- docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_INDEX.md
- ha_ctse_process/continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45.py
- scripts/run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45.py
- tests/ha_ctse_process_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45_test.py
- tests/run_continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45_test.py
- docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_INDEX.md
- ha_ctse_process/continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py
- scripts/run_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44.py
- ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py
- ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py
- ha_ctse_process/continuous_roster_native_six_g31_db_norm_schedule_attribution_g43.py

The G45 source, runner and focused tests are the implementation under audit.
The accepted G44/G41/G43/G40 source paths are allow-listed only to verify the
frozen retained route and private orchestration boundary. No runtime log,
formal/nonformal artifact, unlisted round, G33 material or workflow file is
admitted. Do not infer any result from Git history or from the current
worktree outside this exact commit.
