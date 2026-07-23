# HA-CTSE Current Work

Last updated: 2026-07-23

This file records active state only. Durable authority is in `AGENTS.md` and
`.agents/roles/*.md`.

## Active execution surface

- Project Manager task `019f8a2e-ed73-7a02-9bb9-4a57b2054cf3` is the sole
  persistent project task and owns workflow, scientific reconciliation,
  implementation acceptance, Git, review transport, experiment orchestration,
  result intake and successor selection.
- Formal and bounded runs use only the registered nonpersistent
  `hmasd-experiment-operator`, fixed to `gpt-5.6-luna` with `low` reasoning. It
  remains silent and returns exactly one `COMPLETE` or `ERROR` terminal payload.
- No Controller, persistent Monitor, dispatcher, callback route, global write
  lease, workflow hash handoff or compatibility line is active.

## Active boundary

```text
last_completed_assignment_id=OPEN_ROSTER_DIRECT_MVP_G5_FORMAL_ITERATION_6
active_assignment_id=OPEN_ROSTER_ZERO_SHOT_SCALE_G6_DERIVATION
next_boundary=OPEN_ROSTER_ZERO_SHOT_SCALE_G6_EXECUTABLE_DEFINITION
autonomous_research_grant=ACTIVE_EIGHT_ITERATION_DYNAMIC_ROSTER_CHAIN
grant_scope=dynamic_agent_count_usable_algorithm_design_implementation_cpu_formal_evidence_and_successors
intermediate_authorization_prompts=forbidden
iterations_remaining=7
conclusion_bearing_iterations_consumed=6
implementation_status=G5_CLOSED_SUCCESS_G6_DERIVATION_ACTIVE
nonformal_compute_status=complete_operational_valid
formal_compute_authority=standing_user_grant_cpu_only
formal_compute_status=authorized_after_next_evidence_contract_freeze
git_integration_status=project_manager_direct_authorized
external_review_transport_status=project_manager_direct_authorized_when_selected
experiment_operator_status=registered_available_idle
experiment_operator_last_terminal=COMPLETE
experiment_operator_fallback=forbidden
iteration_report_requirement=required_before_successor
iteration_report_status=iterations_1_to_6_complete
latest_iteration_report=docs/report/ITERATION_6.md
g2_source_commit=9a72dc6a0f776aa3e6dfa96d86f5265f12717ace
g2_formal_run=logs/formal_cross_lifecycle_handoff_g2_cpu_20260723_9a72dc6_r1
g2_formal_result=TEAM_REC_SUFFICIENT_HANDOFF_G2
g2_operational_valid=true
g2_source_identifiable=true
g2_team_rec_utility_ci95=[1.0,1.0]
g2_ehc_utility_ci95=[1.0,1.0]
g2_dum_utility_ci95=[0.5,0.5]
g2_g_team_ci95=[0.0,0.0]
g2_g_link_ci95=[0.5,0.5]
g2_scientific_disposition=closed_no_rerun_tuning_rename_or_rescue
g3_gate_contract=docs/research/designs/ASYNC_COMMITMENT_ROSTER_G3.md
g3_gate_source_commit=b5b67853a2012dd6957e30ad1a6d05d16dff02fe
g3_gate_artifact=logs/nonformal_async_commitment_roster_g3_20260723_pm1/result.json
g3_gate_result=PASS_ASYNC_ROSTER_INFORMATION_GATE_G3
g3_gate_cases=18400
g3_gate_tests=5_passed
g3_gate_iteration_cost=0
next_action_class=zero_compute_algorithmic_derivation
g3_formal_contract=docs/research/designs/USEFUL_EFFECT_ROSTER_G3.md
g3_primary_arm=ROSTER_ATTN
g3_primary_comparator=TEAM_REC
g3_primary_estimand=U_ROSTER_ATTN_minus_U_TEAM_REC
g3_access_floor=0.90
g3_gain_margin=0.10
g3_formal_authorization_token=AUTHORIZE_USEFUL_EFFECT_ROSTER_G3_FORMAL_CPU_V1
g3_implementation_tests=11_passed
g3_nonformal_exercise=logs/nonformal_useful_effect_roster_g3_20260723_pm1
g3_nonformal_result=SOURCE_NON_IDENTIFIABLE_USEFUL_ROSTER_G3
g3_nonformal_operational_valid=true
g3_nonformal_formal_validator_rejection=true
g3_formal_source_commit=3f636aa7ad43b406734f2f34472ba12ee4e0cd77
g3_formal_run=logs/formal_useful_effect_roster_g3_cpu_20260723_3f636aa_r1
g3_formal_result=UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3
g3_formal_operational_valid=true
g3_formal_source_identifiable=true
g3_roster_utility_ci95=[0.86337890625,0.91630859375]
g3_g_team_ci95=[0.02265625,0.069921875]
g3_g_null_ci95=[0.00966796875,0.06513671875]
g3_scientific_disposition=closed_no_rerun_tuning_threshold_or_budget_rescue
g4_derivation=docs/research/cdc/EVIDENCE_NOTES/20260723_COUNT_PRESERVING_ROSTER_G4_DERIVATION.md
g4_formal_contract=docs/research/designs/COUNT_PRESERVING_ROSTER_G4.md
g4_primary_arm=ROSTER_SUM
g4_primary_comparator=ROSTER_ATTN
g4_mission_comparator=TEAM_REC
g4_primary_estimand=U_ROSTER_SUM_minus_U_ROSTER_ATTN
g4_access_floor=0.90
g4_gain_margin=0.10
g4_formal_authorization_token=AUTHORIZE_COUNT_PRESERVING_ROSTER_G4_FORMAL_CPU_V1
g4_implementation_tests=12_passed
g4_nonformal_exercise=logs/nonformal_count_preserving_roster_g4_20260723_pm1
g4_nonformal_result=SOURCE_NON_IDENTIFIABLE_COUNT_ROSTER_G4
g4_nonformal_operational_valid=true
g4_nonformal_formal_validator_rejection=true
g4_formal_source_commit=64a04fafd5abd4e2955382063a97bff290548513
g4_formal_run=logs/formal_count_preserving_roster_g4_cpu_20260723_64a04fa_r1
g4_formal_result=NO_ACCESS_COUNT_ROSTER_G4
g4_formal_operational_valid=true
g4_formal_source_identifiable=true
g4_roster_sum_utility_ci95=[0.8580078125,0.8875]
g4_g_attn_ci95=[-0.02431640625,0.0119140625]
g4_g_team_ci95=[0.00302734375,0.04111328125]
g4_scientific_disposition=closed_no_rerun_tuning_threshold_or_budget_rescue
previous_chain_terminal_disposition=FIVE_ITERATION_CHAIN_COMPLETE
new_chain_authorized_by_user=true
new_chain_iterations=8
new_chain_report_range=ITERATION_6_to_ITERATION_13
primary_research_axis=dynamic_agent_count
asynchronous_skill_lifetime_status=frozen_out_of_active_scope
skill_controller_status=removed_from_mvp
initial_objective=absolute_usability_not_comparative_advantage
active_algorithm=OPEN_ROSTER_DIRECT_MVP_G5
active_design=docs/research/designs/OPEN_ROSTER_DIRECT_MVP_G5.md
g5_authorization_token=AUTHORIZE_OPEN_ROSTER_DIRECT_MVP_G5_FORMAL_CPU_V1
g5_focused_tests=6_passed
g5_nonformal_exercise=logs/nonformal_open_roster_direct_g5_20260723_pm1
g5_nonformal_probe=logs/nonformal_open_roster_direct_g5_probe20_20260723_pm1
g5_nonformal_probe_iid_utility=0.682373046875
g5_nonformal_probe_heldout_utility=0.6054909446022727
g5_formal_replicates=3
g5_formal_updates_per_replicate=250
g5_formal_num_envs=8
g5_formal_eval_episodes=128
g5_formal_source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
g5_formal_run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
g5_formal_result=USABLE_OPEN_ROSTER_DIRECT_G5
g5_operational_valid=true
g5_iid_deterministic_utility_ci95=[0.99853515625,0.9994303385416666,1.0]
g5_heldout_deterministic_utility_ci95=[0.9828879616477272,0.9939926609848483,1.0]
g5_heldout_min_replicate_mean=0.9828879616477272
g5_heldout_stochastic_mean=0.9737067945075756
g5_heldout_final_minus_zero_ci95=[0.48288796164772724,0.5434274384469696,0.6483043323863636]
g5_scientific_disposition=closed_success_no_rerun_tuning_or_threshold_change
g6_candidate_question=zero_shot_count_scale_and_membership_event_time_transport
workflow_hash_validation=disabled
backward_compatibility=not_required
```

The G2 formal pipeline completed from the exact integrated source. Project
Manager reclosed 15 checkpoints, 60 evaluation references, 15,360 evaluation
rows, 640 causal audits and all source controls, then independently reproduced
the first-match branch. TEAM_REC and EHC both reached utility 1.0 while DUM
reached 0.5. The link is load-bearing, but `G_team=0`, so TEAM_REC is sufficient
for this exact one-bit source. Iteration 3 is consumed and two remain.

The G2 mark labels also exposed a measurement symmetry: two replicates learned
the opposite internal sign with perfect behavior. Future natural mediation is
label-permutation invariant; raw `P(m=b)` is not reused as a gate.

## Accepted scientific state

- G0 is permanently closed as `NO_ACCESS_THIS_BENCHMARK`.
- G1 is permanently closed as `ORDINARY_EXPLANATION_G1`; per-member recurrence
  suffices for within-lifecycle cue memory.
- G2 is permanently closed as `TEAM_REC_SUFFICIENT_HANDOFF_G2`; persistent team
  recurrence suffices for one global cross-lifecycle bit.
- G2 nevertheless validates a learned, intervention-sensitive EHC link relative
  to DUM. That lower-precedence fact does not establish EHC advantage.
- C-EHC is narrowed from generic persistence to variable-cardinality,
  event-indexed roster factorization under asynchronous partial edits.
- C-COORD is the active mission-aligned explanation: later value must depend on
  complementarity among retained and newly selected commitments.
- The zero-training G3 information gate passed and retains TEAM_REC as a complete
  simpler explanation. Its uniqueness utility is structural only and cannot be
  promoted as useful complementarity.
- The useful-effect implementation is Project-Manager accepted. It replaces
  label diversity with realized service effects and demand-served external
  utility and retains TEAM_REC as the primary comparator. Its exact formal run
  is validly underpowered on access and is now closed without rescue.
- ROSTER_ATTN has the highest mean and responds to roster intervention, but its
  access interval crosses 0.90. Between-seed training instability, not
  evaluation-row scarcity, motivates a count-preserving roster derivation.
- The count-preserving G4 correction is implemented and PM-accepted under the
  unchanged source, reward, budget and thresholds. `ROSTER_SUM` exposes current
  commitment multiplicity through a permutation-invariant count skip. Its exact
  formal result is NO_ACCESS and it does not improve ROSTER_ATTN.
- All five conclusion-bearing iterations are consumed. The chain establishes
  causal state sensitivity in G2-G4 but no robust EHC/roster advantage over
  ordinary recurrence under the tested sources and frozen PPO budgets.
- The user has now authorized a separate eight-iteration chain whose primary
  axis is dynamic agent count. Asynchronous skill lifetime is frozen, not
  rejected; no active skill controller or skill-advantage claim is carried into
  the MVP.
- The new chain begins from the access-valid direct recurrent active-set path
  and the R49 `N`-independent interface lemma. Its first goal is absolute task
  usability across within-episode membership changes and unseen counts, not
  superiority over a comparator.
- Formal G5 establishes that first goal: one parameter-shape-independent
  checkpoint reaches held-out deterministic utility CI95
  `[0.98288796, 0.99399266, 1.0]` on unseen counts through nine and a larger
  padding capacity. This is a usable dynamic-roster MVP, not evidence of
  arbitrary-count scaling, event-time robustness or skill/lifetime competence.

## Runtime and protected semantics

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch=2.7.0+cpu
torch_threads=1
backend=cpu
```

There is no CUDA fallback, backend mixing, cross-backend resume or CPU/CUDA
equivalence requirement. Preserve every closed G0/G1/G2 source, result and
first-match meaning. The G3 information gate may add only its independent
roster source; it cannot change reward, observations, thresholds, seeds or
semantics of any closed experiment.

## Concurrency

```text
concurrency_policy=file_ownership_only
global_write_lease=disabled
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
active_file_writers=project_manager_exact_active_path_set
```

Project Manager directly stages accepted paths, checks the staged path set and
`git diff --cached --check`, commits and pushes `aggressive`. Per-file hash and
callback receipts are forbidden.

## Pointers

- `AGENTS.md` and `.agents/roles/PROJECT_MANAGER.md` — authority.
- `.agents/roles/EXPERIMENT_OPERATOR.md` — silent single-run contract.
- `docs/project/IMPLEMENTATION_PLAN.md` — accepted useful-effect implementation
  and prelaunch evidence.
- `docs/research/cdc/EVIDENCE_NOTES/20260723_USEFUL_EFFECT_ROSTER_G3_PRELAUNCH.md`
  — bounded nonformal acceptance and formal launch boundary.
- `docs/research/cdc/EVIDENCE_NOTES/20260723_USEFUL_EFFECT_ROSTER_G3_FORMAL_RESULT.md`
  — iteration-4 formal closure and next correction.
- `docs/research/cdc/EVIDENCE_NOTES/20260723_COUNT_PRESERVING_ROSTER_G4_DERIVATION.md`
  — algorithmic counterexamples and count-preserving correction.
- `docs/research/designs/COUNT_PRESERVING_ROSTER_G4.md` — frozen final evidence
  contract.
- `docs/research/cdc/EVIDENCE_NOTES/20260723_COUNT_PRESERVING_ROSTER_G4_PRELAUNCH.md`
  — focused implementation acceptance and launch boundary.
- `docs/research/cdc/EVIDENCE_NOTES/20260723_COUNT_PRESERVING_ROSTER_G4_FORMAL_RESULT.md`
  — iteration-5 closure and five-iteration terminal disposition.
- `docs/research/designs/USEFUL_EFFECT_ROSTER_G3.md` — frozen learned/formal
  evidence contract.
- `docs/research/designs/ASYNC_COMMITMENT_ROSTER_G3.md` — frozen gate.
- `docs/research/cdc/EVIDENCE_NOTES/20260723_CROSS_LIFECYCLE_HANDOFF_G2_FORMAL_RESULT.md`
  — G2 closure and correction.
- `docs/report/ITERATION_1.md`, `ITERATION_2.md`, `ITERATION_3.md` — 用户可读的
  中文结论性迭代报告。
- `docs/research/cdc/EVIDENCE_NOTES/20260723_ASYNC_COMMITMENT_ROSTER_G3_INFORMATION_GATE.md`
  — nonformal gate evidence and successor correction.
