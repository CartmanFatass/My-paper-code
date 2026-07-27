# HA-CTSE Current Work

Last updated: 2026-07-26 (workflow overhaul; joint audit closed by user)

This file records active state only. Durable authority is in `AGENTS.md` and
`.agents/roles/*.md`; scientific method rules are in
`docs/project/ALGORITHM_PRINCIPLES.md`; cost ceilings in
`docs/project/EVIDENCE_COMPLEXITY_POLICY.md`. History lives in Git, closed
rounds under `docs/external-review/rounds/`, closed results under
`docs/research/cdc/`.

## Active execution surface

- The active Claude Code conversation is the Project Manager. It owns workflow,
  code design, implementation acceptance, Git, experiment orchestration, result
  intake and successor selection. Scientific decisions belong to External Pro.
  Review transport is `project_manager_direct`.
- Formal and bounded runs use only the registered nonpersistent
  `hmasd-experiment-operator` subagent, fixed to `haiku` with `low` effort. It
  remains silent and returns exactly one `COMPLETE` or `ERROR` terminal
  payload. PM-direct background shards are permitted for evaluation-only
  audits and recorded here.
- No Controller, persistent Monitor, dispatcher, callback route, global write
  lease, workflow hash handoff or compatibility line is active.

## Active boundary

```text
execution_mode=authorized
active_assignment_id=D7_S_SHARED_PREFIX_REALIZATION_AND_COST_GATE
autonomous_research_grant=ACTIVE_TWENTY_ITERATION_OVERNIGHT_GRANT_20260726
grant_20260726=user_20_authorized_iterations_maintain_overnight_workflow
iterations_remaining=17
conclusion_bearing_iterations_consumed=20
intermediate_authorization_prompts=forbidden
git_integration_status=project_manager_direct_authorized
experiment_operator_fallback=forbidden
iteration_report_requirement=required_before_successor
workflow_hash_validation=disabled
uav_user_scope=transient_demand_coverage_plus_charging_roster_change_plus_temporary_detach_failure_robustness
uav_physical_fleet_boundary=fixed_slots_distinct_from_dynamic_service_roster
grant_note=workflow_overhaul_and_audit_closure_are_support_work_no_iteration_consumed
iterations_since_last_compaction=4
loop_driver_status=NOT_ATTACHED_session_restarted_20260726_reattach_at_next_empty_gap
compute_gate=scripts/check_compute_free.ps1_COMPUTE_FREE_run_COMPUTE_BUSY_wait_one_hour_and_recheck
compute_gate_note=read_heavy_pids_first_own_run_means_wait_on_notification_not_sleep
working_branch=untied-k
aggressive_branch_ownership=independent_line_not_claude_owned_never_push
research_goal=docs/project/RESEARCH_GOAL.md
research_goal_standing_check=what_does_this_let_us_say_about_variable_k_that_we_could_not_say_before
project_goal=publish_a_paper_user_stated_20260725
science_status=UNFROZEN_20260725

workflow_overhaul_20260726=eight_step_loop_installed_by_user_ruling_see_AGENTS.md
workflow_overhaul_source=HMASD-new_reference_project_read_only_ported_by_user_direction
workflow_overhaul_changes=two_stage_triggered_audit|review_stack_false|griller_reviewer_verifier_opt_in_only|evidence_complexity_policy_installed|algorithm_principles_wired_into_reading_paths|time_distribution_table_mandatory_in_iteration_reports
pro_round_scope=decisions_only_any_number_never_verification_labor

next_boundary=D7_S_SHARED_PREFIX_REALIZATION_THEN_STAGE_B_THEN_COST_BOUND
next_boundary_class=steps_5_to_7_of_the_eight_step_loop_implement_review_then_gated_experiment
next_boundary_question=does_the_shared_prefix_clone_realization_pass_six_stage_b_conditions_and_does_the_2_2_prelaunch_upper_bound_fit_8h
next_boundary_inputs=refrozen_contract_R2|scripts/audit_d7_s_event_aligned.py|measured_0.10_0.30_s_per_step|EVIDENCE_COMPLEXITY_POLICY
pro_round_20260726_replicate_volume=CLOSED_archived_and_pushed_733868e_raw_hash_verified
pro_ruling_headline=freeze_nsel2_neval2|accept_shared_prefix_forking|launch_only_if_prelaunch_bound_le_8h|no_downscope|refreeze_in_same_round
pro_ruling_cost_allowance=one_microbenchmark_at_most_20_minutes_permitted_to_establish_shared_prefix_continuation_rate
stage_b_status=MANDATORY_named_by_pro_ruling_six_blocking_conditions_on_the_realization_diff
stage_b_disclosure_1=argmax_tie_break_is_deterministic_toward_first_enumerated_candidate_in_both_the_primary_bootstrap_and_the_diagnostic
stage_b_disclosure_1_why=exact_ties_are_rare_at_nsel4_and_common_at_nsel2_two_identical_candidates_tie_on_37.5pct_of_resamples_so_the_volume_reduction_raises_how_often_an_unspecified_rule_decides_the_selected_z_which_feeds_U_star
stage_b_disclosure_1_class=candidate_SCIENTIFIC_AMBIGUITY_previously_unstated_result_changing_choice_not_a_new_round

d7_s_contract_status=FROZEN_R2_20260726_docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md
d7_s_contract_executability=NON_EXECUTABLE_until_prelaunch_upper_bound_le_8h_is_produced
d7_s_contract_superseded=docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md_never_edited_after_freeze
d7_s_contract_key_values=leave_anchor|H_stable_139|H_flex_550|heldout_low_scoped|one_joint_event_per_episode|X50_Y10_Z139|nsel2_neval2|shared_prefix_clone_realization|selection_diagnostic_required|seeds_20260726_to_33_expansion_to_41_once|bootstrap_2026072601_10000_one_sided|delta_0.05_equivalence|ten_branch_precedence
d7_s_instrument=scripts/audit_d7_s_event_aligned.py_accepted_152_plus_tests_progress_telemetry_stderr
d7_s_instrument_commits=fc0c8e6_logic|cf1a7af_orchestration|f75fca5_part_a_wiring|a106335_telemetry|beb7690_shard_pooling
d7_s_pooling=scripts/pool_d7_s_event_aligned_shards.py_by_topology_identity_asserted
d7_s_conformance_derivation=docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_EVENT_ALIGNED_CONFORMANCE_DERIVATION.md
d7_s_joint_audit_20260726=CLOSED_BY_USER_before_completion_8_shards_killed_partial_outputs_deleted
d7_s_joint_audit_closure_reason=projected_2_to_4_days_wall_clock_user_ruled_cost_unacceptable_new_policy_would_have_caught_at_freeze
d7_s_smoke_2_20260726=CLOSED_BY_USER_as_valueless_4h_plus_oversized_rehearsal_outputs_deleted_lesson_in_memory
d7_s_ep64_diagnostic=logs/nonformal_d7_s_persistence_margin_20260726_ci_h1500_ep64_single_topology_20260725_branch_SOURCE_NECESSITY_UNRESOLVED
d7_s_ep64_headline=B_H_+65.965_CI_excludes_zero|U_stable_-40.602_CI_excludes_zero|norm_stable_-0.6155|flex_arm_degenerate_not_estimand
d8_status=BLOCKED_every_branch_until_the_paper_level_source_is_qualified

d7_2b_toy=RETIRED_as_positive_control_swap_degeneracy_see_20260725_D7_2B_TOY_SWAP_DEGENERACY_DERIVATION
d7_s_part_a=COMPLETE_zero_cost_role_exchange_structurally_absent_in_scenario7
u_src_margins=U_stable_src_over_B_H_le_minus_0.10_and_U_flex_src_over_B_H_ge_plus_0.10
r30_all_set_basin_bias=retained_hypothesis_parked_needs_multi_seed_preregistration
estimand_level=stays_agent_level_do_not_reframe_to_duty_level

iteration_report_status=iterations_1_to_24_complete_25_pending_this_boundary
iteration_report_numbering_note=ITERATION_24_exists_and_is_support_work_no_iteration_consumed_next_conclusion_bearing_report_is_25
latest_iteration_report=docs/report/ITERATION_24.md
```

## Closed generations — pointers only

- **G17** closed success (immediate service only):
  `docs/research/cdc/EVIDENCE_NOTES/20260724_CONTINUOUS_SERVICE_ROSTER_G17_FORMAL_RESULT.md`.
- **G18** closed `NO_G17_COMPATIBILITY` (all variants):
  `docs/research/cdc/EVIDENCE_NOTES/20260724_ACTOR_CRITIC_ISOLATED_G18_FORMAL_RESULT.md`.
- **G19** retired without formal cost:
  `docs/research/cdc/EVIDENCE_NOTES/20260724_FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19_SCREEN.md`.
- **G20/G20R/G20R2** retired/superseded chain (zero fixed point, floor round,
  nine-blocker rework ON_HOLD): rounds under
  `docs/external-review/rounds/20260724_g20*` and `20260725_g20r2_prefreeze_grill`;
  `g20r3_status=ON_HOLD` pending scope call.
- **Contract-grill mechanism** retired as a mechanism 2026-07-25 (casebook
  survives): `docs/external-review/rounds/20260725_contract_grill_design/30_PM_RECONCILIATION.md`.
  Its surviving function is the Stage A question in `AGENTS.md`.
- **UAV G1** deferred (operational timeout, no valid result), **UAV G2**
  contract frozen as deferred promotion candidate:
  `docs/research/designs/UAV_CHARGE_ROTATION_ROSTER_G2.md`.
- **D7 part B margin-instrument era** (defect history, repro sweeps, sharded
  ep64): superseded by the frozen event-aligned contract; evidence notes under
  `docs/research/cdc/EVIDENCE_NOTES/` and round
  `20260726_d7_s_part_b_flex_arm_and_instrument`. The ep64 run is preserved as
  a single-topology diagnostic only.
- Earlier closed generations: `docs/research/cdc/CLOSED_GENERATION_BOUNDARY_ARCHIVE_G2_G16.md`.

## Accepted scientific state

- Scenario-7 is a lossy-exchange source (part A structural fact); the margin
  quantification awaits the event-aligned audit under whatever replicate
  volume the next Pro round rules executable.
- The toy positive control is retired (swap degeneracy); its retained lemma is
  in `AGENTS.md`. R30 carrier, U_src estimand, forcing hook, ledger all intact.
- Scenario-7 topology provenance standing rule: reused results must prove
  shared topology or scope their claim (`AGENTS.md`, Result interpretation).

## Runtime and protected semantics

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch=2.7.0+cpu
torch_threads=1
backend=cpu
```

No CUDA fallback, backend mixing, or cross-backend resume. Preserve every
closed source, result and first-match meaning.

## Concurrency

```text
concurrency_policy=file_ownership_only
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
```

Project Manager directly stages accepted paths, checks the staged path set and
`git diff --cached --check`, commits and pushes `untied-k`. The `aggressive`
branch is another line's and is never touched.

## Pointers

- `AGENTS.md` — authority, the eight-step loop, Stage A/B audits, document
  ownership table.
- `docs/project/ALGORITHM_PRINCIPLES.md` — scientific method contract.
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md` — cost ceilings and violation
  semantics.
- `docs/project/RESEARCH_GOAL.md` — what the paper is about; the standing check.
- `docs/project/AGENT_CONTEXT.md` — standing context every subagent reads.
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md` — the refrozen
  contract: `2/2`, shared-prefix clone realization, non-executable until the
  eight-hour prelaunch bound exists.
- `docs/report/ITERATION_23.md` — 最新的中文结论性迭代报告。
