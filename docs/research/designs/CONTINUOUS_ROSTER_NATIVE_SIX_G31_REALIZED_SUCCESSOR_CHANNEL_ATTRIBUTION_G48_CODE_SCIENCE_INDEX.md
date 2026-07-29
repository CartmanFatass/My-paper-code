# G48 Code-Science Index

```text
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_P0
design_round=20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit
design_stage_commit=35a924424f842699dd275949626ef568aee08a22
design_source_commit=9d5416d69051365e9da35e496949fabd8e9a1493
design_disposition=IDENTIFIABLE_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48
accepted_g47_formal_source_commit=23939a16f9a6035fda91506f6e76ff742bf23b73
accepted_g47_aligned_implementation_commit=fab68ae1a87578b59c1a004ac5415edf55ee7452
accepted_g47_alignment_stage_commit=33432c16df22e5432710a5e5b05aa34a82c5a45f
accepted_g47_formal_branch=SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47
reference_arm=NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR
null_arm=NATIVE6_G31_DUPLICATED_IMMEDIATE
formal_runner=scripts/run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48.py
formal_authorization_token=CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_FORMAL_AUTHORIZATION_V1
artifact_schema_version=2
implementation_commit=the_Git_commit_containing_this_index_and_all_four_G48_code_test_paths
alignment_audit_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_CODE_SCIENCE_ALIGNMENT_AUDIT
alignment_audit_target_commit=5e2ace7199970634d79219f2858bb53aabf5a57e
alignment_audit_stage_commit=c6822acccbe681434ef723e06c398e87325ee58b
alignment_audit_disposition=MISMATCH
alignment_mismatch=replace_squared_q_credit_with_frozen_unsquared_complete_credit_vector_ratio
alignment_correction_recheck_round=20260729_g31_realized_successor_channel_attribution_g48_code_science_alignment_correction_recheck
alignment_correction_recheck_target_commit=d96f8f29367b55b5ea655b984631d6064877e237
alignment_correction_recheck_stage_commit=617414f9a175f044eecfbfec4e4b170c6990b47f
alignment_correction_recheck_disposition=ALIGNED
aligned_g48_implementation_commit=d96f8f29367b55b5ea655b984631d6064877e237
alignment_stage_commit=617414f9a175f044eecfbfec4e4b170c6990b47f
formal_admission=exact_bound_ALIGNED_target_and_stage_plus_same_source_nonformal_preflight_and_formal_authorization_token
acceptance_owner=code_project_manager
scientific_authority=external_pro
formal_compute_started=false
nonformal_compute_started=false
scientific_iteration_cost=zero
formal_inventory=replicates3|branch_updates_per_arm100|num_envs8|PPO_passes2|training_transitions230400|evaluation_transitions165888|total_real_transitions396288|optimizer_steps1200|evaluation_cells72|episodes_per_cell48|bootstrap10000
nonformal_inventory=replicates1|branch_updates_per_arm10|num_envs8|PPO_passes2|training_transitions7680|evaluation_transitions6912|total_real_transitions14592|optimizer_steps40|evaluation_cells24|episodes_per_cell6|bootstrap250
complexity=H48|K_search0|hypothetical_trajectory_count0|hypothetical_transitions0|nested_rollout=false|replanning=false|per_episode_O(H)
```

| claim_id | frozen assertion | code path::symbol | observable invariant | focused test::test name | rejected plausible defect |
|---|---|---|---|---|---|
| G48-PROVENANCE-01 | Both arms start only from the accepted G47 baseline-free route. | source `::project_g48_arms`; `::branch_boundary_audit`; runner `::source_controls` | Exact G47 formal source, aligned implementation, stage and branch are serialized. Actor/log-std bytes, empty Adam configuration and trainable order match before treatment; storage and projection RNG are disjoint/zero. | source `::test_projection_and_null_route_are_actor_only_and_successor_read_free` | A new anchor, baseline-bearing branch, shared storage or caller-selected provenance cannot enter. |
| G48-TARGET-02 | The sole treatment is the complete realized-successor channel package. | source `::reference_channel_package`; `::duplicated_immediate_channel_package`; `::_prepared_packages` | Reference materializes `r_t|G_(t+1)`; null accepts only a rewards tensor and separately clones `r_t|r_t`. The null builder has no successor-bearing argument or bytecode read. | source projection/null-route test | A duplicated pointer, latent `G_(t+1)` read, successor-derived scale or counterfactual call cannot masquerade as duplicated immediate credit. |
| G48-NORMALIZE-03 | Each complete 48x8 channel is separately centered and independently population-RMS normalized once before both passes. | source `::_normalize_package`; `::_normalization_record`; `::validate_normalization_record` | Per-arm route, channel IDs, means, centered sums, scales, normalized digests, row count 384 and mask digest round-trip exactly; null rows and digests are byte equal. | source `::test_update_serializes_reference_activation_and_rejects_route_tampering` | Epsilon, running statistics, row filtering, active-count weights, between-pass recomputation, swapped routes or forged null evidence fail closed. |
| G48-GRADIENT-04 | Credit is literal `0.5*(g_1+g_2)` and common entropy is added once after credit construction. | source `::_probe`; `::_gradient_evidence`; `::_apply_actor_pass` | Every registered actor group is finite in both reference channel rows and live in at least one; null duplicate channel gradients are bitwise equal; combined reference/null counterfactual rows are finite; one actor Adam step occurs per pass. | source completed-update test | Requiring both global rows live, stale gradient reuse, altered reduction, double entropy, clipping, minibatches or skipped zero exposure cannot pass. |
| G48-ACTIVATION-05 | Activation comes only from reference pre-update target and complete credit-vector evidence. | source `::_activation_scalars`; `::activation_record`; `::validate_activation_record` | `q_target=RMS(z_S-z_I)` and `q_credit=||v_REF-v_NULL,cf||/max(||v_REF||,||v_NULL,cf||)` are independently reconstructed from serialized squared sufficient statistics; both strict `>1e-6` are required. An intermediate relative difference between `1e-6` and `1e-3` is active, direction distance is descriptive only, and the actual null supplies zero activation evidence. | source `::test_strict_activation_and_zero_nonfinite_cases`; completed-update test | Squaring the registered ratio, caller-authored passed flags, norm-only evidence, a direction gate, equality activation, nonfinite rows or actual-null evidence reads cannot select treatment. |
| G48-PAIRING-06 | Both complete trajectories exist before either update and update order is fixed. | source `::order_swap_guard`; `::optimize_realized_successor_channel_update`; runner `::_train_replicate` | First-update zero-step reverse-order construction leaves mate model, optimizer and RNG bytes unchanged; production order is reference then null with paired source/ledger/action evidence. | source completed-update test | Completion-order merge, arm-owned recollection after mate update, diagnostic optimizer steps or adaptive RNG can no longer hide ordering effects. |
| G48-NULL-CERT-07 | Null successor reads are zero across actor credit, scaling, checkpoints, evaluation and results. | source `::_null_zero_read_certificate`; `::reconstruct_static_certificate`; runner `::_ActorOnlyEvaluationPolicy`; `::_load_checkpoint_payload` | Static bytecode evidence precedes training; update, final-only checkpoint, reload and evaluation independently require zero null successor reads and no baseline/critic schema. | source projection test; runner `::test_null_checkpoint_tamper_and_first_match_priority_fail_closed` | A label-only certificate with a live successor accessor, checkpoint field or evaluator dependency is rejected. |
| G48-CHECKPOINT-08 | Only final actor/log-std state and actor Adam exposure are result-bearing. | source `::build_final_checkpoint`; `::_target_route_certificate`; runner `::_save_checkpoint`; `::_load_checkpoint_payload` | Each final checkpoint binds source, arm, replicate, final update, conclusion activation, exact target route and final-only inventory; null has no baseline or successor-credit schema. | source completed-update test; runner readiness/tamper tests | Intermediate checkpoints, missing duplicate evidence, forged target labels, added baseline/critic keys or one-sided reference evidence cannot reload. |
| G48-RUNTIME-09 | CPU C++ backend and launch-fixed process isolation preserve serial semantics. | runner `::_configuration`; `::_collect_trajectory`; `::prove_two_process_update_equivalence` | Backend is `ContinuousRosterToyBatch_CPU_CPP`, Python fallback false, workers are limited to 1..6, child BLAS/OpenMP and torch intra-op threads are one, and preassigned-index two-process model/Adam/evidence digests equal. | runner `::test_configuration_seeds_workers_and_formal_admission_are_fail_closed`; `::test_readiness_proves_two_process_artifact_reload_and_evaluate_entry` | Nested parallelism, Python fallback, completion-order merging or merely numerically-close worker artifacts cannot enter. |
| G48-CONFIDENCE-10 | Access, paired bootstrap, margin and first-match rules are inherited exactly. | runner `::_comparison`; `::select_g48_result_branch`; `::analyze` | Paired whole-episode hierarchical bootstrap uses equal capacity weights and all registered component contrasts. Invalid precedes source/access failure, null sufficiency, reference advantage and mixed/underpowered; UCB=0.05 passes noninferiority and LCB=0.05 is not material. | runner first-match test | A malformed artifact, reordered branch, unregistered component rescue or relaxed strict inequality cannot decide G48. |
| G48-AUTHORITY-11 | Scientific runs are closed until independent alignment and same-source preflight. | runner `::ALIGNED_IMPLEMENTATION_COMMIT`; `::ALIGNMENT_STAGE_COMMIT`; `::train`; `::_validate_formal_preflight` | The runner and isolated orchestration backend bind exactly `d96f8f29367b55b5ea655b984631d6064877e237` and `617414f9a175f044eecfbfec4e4b170c6990b47f`; formal entry still rejects before model/optimizer construction unless the caller supplies those identities, the authorization token and a complete same-source nonformal preflight. | runner configuration/formal-admission test | The design-stage hash, original mismatched target/stage, G47 alignment, caller-supplied hashes or an absent/prior-source preflight cannot authorize formal compute. |
| G48-READINESS-12 | Runner/serialization/lifecycle changes receive all six proof-sized phases. | runner `::readiness_interface_smoke`; `::readiness_train`; `::readiness_training_errors`; `::reload_readiness_artifacts`; `::readiness_evaluate`; `::readiness_analyze` | A one-update-per-arm, one-evaluation-episode-per-arm, zero-bootstrap, non-conclusion-bearing root validates interface, exercise, artifact schema, reload, evaluate and analyze without scientific threshold selection. | runner readiness test; Git-private execution-readiness receipt | Unit tests alone, prior formal results or a scientific nonformal run cannot substitute for executable artifact-lifecycle proof. |

Next boundary after Code PM technical acceptance:
fresh same-source G48 nonformal preflight, followed only on success by the frozen formal train/evaluate/analyze interface.
