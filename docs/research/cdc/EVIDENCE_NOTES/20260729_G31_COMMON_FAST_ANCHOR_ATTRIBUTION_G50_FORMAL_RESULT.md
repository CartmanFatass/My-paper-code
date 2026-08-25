# G50 formal result: mechanical runtime evidence

```text
round=20260729_g31_common_fast_anchor_attribution_g50_formal_result_review
source_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
execution_code_commit=23af6bf7c80a4b73c09cf0423f9f539972b1b55d
alignment_stage_commit=4df41063d077ace7e0c9212e0cbadbf56e1be4b7
formal_run_root=logs/formal_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_cpu_20260729_b829069_r5
preflight_root=logs/nonformal_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_cpu_20260729_b829069_r5
formal=true
execution_status=COMPLETE
train_exit=0
evaluate_exit=0
analyze_exit=0
operational_valid=true
result_branch=FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50
backend=ContinuousRosterToyBatch_CPU_CPP_required
python_fallback=false
cpu_budget=2
process_workers=2
worker_start_method=spawn
thread_controls=OMP_NUM_THREADS:1|MKL_NUM_THREADS:1|OPENBLAS_NUM_THREADS:1|NUMEXPR_NUM_THREADS:1|torch_intraop_threads:1
replicates=3
arms=2
phase_A_updates_per_arm=100
phase_B_updates_per_arm=100
environments_per_update=8
PPO_passes=2
evaluation_cells=72
episodes_per_cell=48
total_real_transitions=626688
optimizer_steps=2400
evaluation_optimizer_steps=0
bootstrap_resamples=10000
H=48
K_search=0
hypothetical_transitions=0
```

Terminal artifacts were mechanically checked by Research Operations Manager:

- `train_manifest.json`, `evaluation_manifest.json`, and `analysis_result.json`
  are present and report `status=COMPLETE`, `formal=true`, and the exact source
  commit above.
- The evaluation manifest digest matches the train manifest digest recorded in
  the analysis result; the analysis manifest digest matches the evaluation
  manifest digest.
- Six final-only checkpoints are present (replicates 0, 1, 2 × both G50 arms),
  and every checkpoint SHA-256 matches the train manifest.
- The analyzer reports `operational_valid=true`, `source_valid=true`,
  `treatment_activation_valid=true`, and the result branch above.

This note is a mechanical evidence record only. It does not state a scientific
disposition, CDC edit, portfolio decision, or successor action. External Pro is
the sole authority for those decisions in the associated review.
