# G51 formal result: mechanical runtime evidence

```text
round=20260729_g31_phase_a_shadow_baseline_module_reduction_g51_formal_result_review
source_commit=ce6ed8659c480ca2779155b2871dc82b89fa0e95
execution_code_commit=fa52274bdc6d90c79ef1658cd5c060046f113692
aligned_implementation_commit=188b210975a0f243ae34318d658fbf943d1d63ab
alignment_stage_commit=aa756dcd06a2ea622c155f2983a89bb5d76e9d80
alignment_disposition=ALIGNED
formal_authorization_token=CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_FORMAL_AUTHORIZATION_V1
formal_run_root=logs/formal_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51_cpu_20260729_ce6ed86_r1
preflight_root=logs/nonformal_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51_cpu_20260729_ce6ed86_r1
formal=true
formal_statistical_run=false
execution_status=COMPLETE
train_exit=0
evaluate_exit=0
analyze_exit=0
operational_valid=true
result_branch=PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51
passed=true
backend=ContinuousRosterToyBatch_CPU_CPP_required
python_fallback=false
cpu_budget=2
process_workers=1
worker_start_method=spawn
thread_controls=OMP_NUM_THREADS:1|MKL_NUM_THREADS:1|OPENBLAS_NUM_THREADS:1|NUMEXPR_NUM_THREADS:1|torch_intraop_threads:1
episodes=8
H=48
real_transitions=384
PPO_passes_per_arm=2
actor_optimizer_steps_per_arm=2
total_optimizer_steps=4
phase_B_optimizer_steps=0
bootstrap_resamples=0
K_search=0
hypothetical_transitions=0
D_G51=0
canonical_final_checkpoint_projection_equal=true
train_manifest_sha256=F9CFD769A8BE4CC9BB800D775662DFA2C54D410640452F91FF1E22251DAAC146
evaluation_manifest_sha256=CC5A86AF589C9B2712BF1F1F29AA2455824E28EC305E910B1B3C82F2D7DC7F9D
analysis_result_sha256=F817FFA8C372B7EE8706D345D0BAC99BDA8A5EACC5304BE75168BA760C5A943D
scientific_iteration_cost=one
```

Terminal artifacts were mechanically checked by Research Operations Manager:

- `train_manifest.json`, `evaluation_manifest.json`, and `analysis_result.json`
  are present and report `formal=true`, the exact source commit above, the
  exact result branch, and `passed=true`.
- `proof_inputs/shared_phase_A_trajectory.pt` and `proof/result_assessment.pt`
  are present; evaluation and analysis bind the upstream manifest/assessment
  digests.
- `checkpoints/reference_final.pt`, `checkpoints/reduced_final.pt`, and
  `parallel_proof/two_process_equivalence.json` are present for the exact
  outcome-conditioned inventory.
- The first analyze invocation was rejected before execution because an
  unsupported CLI flag was supplied; a same-root, same-source analyze retry
  without that flag exited 0. TRAIN and EVALUATE were not rerun.

This note is a mechanical evidence record only. It does not state a scientific
disposition, CDC edit, portfolio decision, or successor action. External Pro is
the sole authority for those decisions in the associated review.
