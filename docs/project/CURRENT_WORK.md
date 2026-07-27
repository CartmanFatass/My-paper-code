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
active_assignment_id=D7_S_REPLICATE_VOLUME_NECESSITY_PRO_ROUND
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
loop_driver_status=ATTACHED_session_bound_ScheduleWakeup_fallback_task_notifications_primary
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

next_boundary=D7_S_REPLICATE_VOLUME_NECESSITY_PRO_ROUND
next_boundary_class=step_1_of_the_eight_step_loop_scientific_decision
next_boundary_question=frozen_contract_volume_nsel4_neval8_projects_2_to_4_days_violating_the_8h_cap_pro_decides_necessity_reduction_or_redesign
next_boundary_inputs=frozen_contract|ep64_single_topology_diagnostic|measured_fork_cost_from_smoke_1|EVIDENCE_COMPLEXITY_POLICY

d7_s_contract_status=FROZEN_20260726_docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md
d7_s_contract_key_values=leave_anchor|H_stable_139|H_flex_550|heldout_low_scoped|one_joint_event_per_episode|X50_Y10_Z139|nsel4_neval8|seeds_20260726_to_33_expansion_to_41_once|bootstrap_2026072601_10000_one_sided|delta_0.05_equivalence|ten_branch_precedence
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

iteration_report_status=iterations_1_to_23_complete_24_pending_this_boundary
latest_iteration_report=docs/report/ITERATION_23.md
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
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md` — the frozen
  contract whose replicate volume is the open Pro question.
- `docs/report/ITERATION_23.md` — 最新的中文结论性迭代报告。
