# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
project_history_in_router=forbidden
role_specific_procedure_in_router=forbidden
```
Every HMASD task receives this small router for identity, minimum documents and shared boundaries. History, results, budgets and mechanics load only when assigned.

## Precedence and role resolution

Precedence is: direct user instruction, this router, the applicable role charter, any role-authorized current-state read, the named scientific/design contract, then procedural Skills.
Use exactly one route:

| Active identity | Read after this file | Do not load by default |
|---|---|---|
| Code Project Manager task | `docs/project/CURRENT_WORK.md`, `.agents/roles/CODE_PROJECT_MANAGER.md`, then only the active workstream's named science, code, tests, review, runtime and evidence paths | unrelated workstreams, independent-research corpus and workflow-design history |
| dedicated Workflow Design Manager task | its exact workflow-design assignment, `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`, the public `CURRENT_WORK.md` index plus only WDM's linked session/common records, `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`, then `.agents/skills/hmasd-workflow-change-audit/SKILL.md` only after plan confirmation | other current-work records, runtime reviews/runs, science and implementation |
| Independent Research Explorer task | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, `.agents/skills/hmasd-independent-research-exploration/SKILL.md`, algorithm-principles sections 1 and 3, then user-named read-only research sources | `CURRENT_WORK.md`, formal science/runtime, code and workflow state |
| registered native child | its exact assignment, its `.codex/agents/*.toml` profile, the named `.agents/roles/*.md` charter, then only assignment-named files | `CURRENT_WORK.md`, persistent-task history, other role charters |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` interface supplied by the question | repository history or files outside the question boundary |
A child never reconstructs task history. A missing identity, path, authority or completion condition fails closed instead of triggering a project-state search.

Every persistent session routes workflow requirements and defects to Workflow Design Manager; only WDM uses the shared Workflow Design Skills to modify or accept control-plane surfaces.

## Universal authority boundary

```text
workflow_design_manager_session=019fb73d-5635-7b63-b165-6c5129bc0217
code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
workflow_design_manager_workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces
workflow_design_manager_workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces
workflow_design_manager_workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces
workflow_design_manager_workflow_runtime_authority=none
workflow_design_manager_current_work_authority=public_index_and_own_workflow_control_plane_records_only
workflow_design_manager_scientific_authority=none
workflow_design_manager_code_acceptance_authority=none
workflow_design_manager_git_authority=exclusive_for_workflow_control_plane_surfaces
workflow_design_manager_remote_repository_authority=permanent_user_grant
workflow_design_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
workflow_design_manager_external_review_runtime_authority=none
workflow_design_manager_experiment_runtime_authority=none
workflow_design_owner=workflow_design_manager
persistent_session_workflow_design_authority=none
persistent_session_workflow_acceptance_authority=none
persistent_session_workflow_git_authority=none
workflow_change_request_route=workflow_design_manager
workflow_input_precedence=direct_user_instruction|wdm_charter_and_design_principles|accepted_stable_workflow_contract|other_session_report
workflow_user_change_lane=plan_confirmation_then_continuous_implementation_verification_git_reload
workflow_defect_lane=archive_then_fifo_autonomous_stable_contract_repair
workflow_defect_queue_states=QUEUED|ACTIVE|CLOSED
workflow_defect_report_authority=advisory_only
workflow_child_parent=workflow_design_manager|workflow_child_acceptance_authority=none|workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace|session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
workflow_implementer_parallelism=min(disjoint_owned_path_families,available_native_slots_minus_integrator)
workflow_router_consistency_check=required_for_every_workflow_change
code_project_manager_code_authority=exclusive
code_project_manager_technical_acceptance_authority=exclusive
code_project_manager_runtime_authority=exclusive
code_project_manager_current_work_authority=exclusive
code_project_manager_formal_external_review_transport_authority=exclusive
code_project_manager_formal_review_workstreams=formal_toy_research|uav_validation
code_project_manager_experiment_dispatch_and_result_routing=exclusive
code_project_manager_mechanical_result_acceptance=exclusive
code_project_manager_scientific_authority=none
code_project_manager_git_authority=direct_for_code_runtime_review_evidence_report_ledger_and_state
code_project_manager_remote_repository_authority=permanent_user_grant
code_project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
independent_research_explorer_session=019fbded-24cb-7541-aa16-0111b626b945
independent_research_canonical_scientific_authority=none
independent_research_explorer_write_scope=local_research_including_explorer_owned_pro_reviews
independent_research_explorer_external_review_transport_authority=exclusive_for_independent_research_reviews
independent_research_explorer_external_review_stable_key=hmasd-independent-research-explorer-pro
independent_research_review_transport_execution=persistent_explorer_session_direct
formal_compute_authority=user_only
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
native_child_authority=exact_assignment_only
experiment_operator_compute_authority=derived_from_valid_code_project_manager_assignment
experiment_operator_per_run_user_authorization=not_required_inside_active_grant
independent_research_per_review_authorization=not_required_inside_active_explorer_grant
independent_research_wdm_campaign_approval=none
one_artifact_one_acceptance_owner=true
cross_task_routing=locked_role_session_model_thinking
cross_task_routing_skill=hmasd-cross-task-routing
workflow_design_charter=WORKFLOW_DESIGN_MANAGER.md
```
The user permanently authorizes WDM to fetch and push accepted workflow-control-plane paths. Other persistent sessions may fetch and push only their non-workflow operational, scientific, code and workspace content defined in `SESSION_WORKSPACE_CONTRACT.md`; independent-research egress remains limited to its research and workspace boundary.
There is no Controller, Research Operations Manager, persistent Monitor, dispatcher, semantic relay, role registry or global lease. WDM owns the complete workflow control plane; CPM owns project execution; Explorer owns independent research; External Pro owns science within each review boundary.
## Universal project constraints

```text
development_mode=agile_algorithm_research
project_development_skill=hmasd-agile-research-development
hmasd_python_interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
workflow_change_skill=hmasd-workflow-change-audit
superpowers_plugin=reference_only
superpowers_execution=disabled
backward_compatibility=not_required
test_scope=proof_sized
evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md
codebase_policy=small_active_line_only
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
workflow_hash_admission=forbidden
wdm_core_control_plane_line_budget=1000
workflow_single_mechanism_line_budget=100
workflow_single_mechanism_terminal_state_budget=3
workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch
workflow_legacy_mechanism_policy=no_expansion_reduce_when_touched
workflow_permanent_rule_minimum_independent_recurrences=2
workflow_new_mechanism_requires_named_deletion=true
concurrency_policy=file_ownership_only
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
workflow_parallel_implementation=file_family_adaptive
isolated_worktree_identity=workspace_ticket_only
hmasd_worktree_root=C:/worktrees/HMASD
project_write_scope=current_checkout_plus_verified_ticket_worktree
external_workspace_access=read_only
raw_external_worktree_creation=forbidden
drive_or_path_alias_creation=forbidden
workflow_gate_form=budget_grant_or_scope_decision_only
per_action_confirmation_inside_active_grant=forbidden
reversible_internal_action_user_gate=forbidden
internal_role_handoff_within_active_grant=no_user_authority_required
operational_recovery_owner=code_project_manager
operational_recovery_scientific_iteration_cost=zero
```
Workflow hash rules prohibit payload/content digests, byte counts and
fingerprints as admission evidence. Git revision identifiers remain source
locators only and never replace direct contract checks.
Generic Superpowers Skills are not executed. Use project-native Skills, keep active code small, and use Git as archive. Tests create no approval owner.
The current HMASD checkout and one valid assignment-ticket worktree are the only agent-writable project directories; every other directory is read-only to project agents, while project-external reads remain allowed.
Agents do not create, edit, copy, move, delete or redirect files outside that scope and do not create drive mappings, junctions or path aliases. Isolated worktrees are provisioned only by `scripts/hmasd_workspace_ticket.py` beneath `C:/worktrees/HMASD`; raw external `git worktree` is not an authority path.
A future project-external write requires a new explicit user instruction for its exact target and does not broaden this standing boundary.

## Routed project mechanisms
- Scientific principles and evidence complexity: `docs/project/ALGORITHM_PRINCIPLES.md`, `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`.
- Longitudinal scientific-decision ledger: `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`.
- Pro-assisted design and code-science audits: `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.
- Workflow-design authority and automation: `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`.
- Project coordination, code, technical acceptance, runtime and direct Pro transport: `.agents/roles/CODE_PROJECT_MANAGER.md`.
- Exact mechanical Pro transport and result intake: each owning persistent session through `.agents/skills/hmasd-agentify-pro-transport/SKILL.md`.
- Mechanical experiment execution: `.agents/roles/EXPERIMENT_OPERATOR.md`.
- External Pro interface: `.agents/roles/EXTERNAL_PRO.md`.
- CPU/runtime facts, only when needed: `docs/project/AGENT_CONTEXT.md`.
- Implementation mechanics: `.agents/skills/hmasd-agile-research-development/SKILL.md`.
- Collaborative workflow design: `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`.
- Persistent-role cross-task routing: `.agents/skills/hmasd-cross-task-routing/SKILL.md`.
- Control-plane audit and execution: `.agents/skills/hmasd-workflow-change-audit/SKILL.md`.
- Mechanical workflow harness: `.agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py`.
- WDM public state: `docs/project/current-work/sessions/workflow_design_manager.md`, `docs/project/current-work/common/workflow_control_plane.md`.
- WDM durable and temporary workspaces: `docs/session-workspaces/workflow_design_manager/`, `temp/sessions/workflow_design_manager/`.
- WDM defect FIFO: `docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md`.
- Pro transport: `.agents/skills/hmasd-agentify-pro-transport/SKILL.md`, with stable-key mechanics in `docs/project/AGENTIFY_PRO_TRANSPORT.md`.
- Independent advisory research and its project toy-validation bridge: `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, `.agents/skills/hmasd-independent-research-exploration/SKILL.md`, `.agents/skills/hmasd-explorer-project-validation/SKILL.md`, `docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`.
- Independent methodology review: the persistent Explorer may invoke `.agents/skills/hmasd-independent-research-pro-review/SKILL.md`; direction and methodology reviews use its direct Agentify transport.
- Isolated-worktree identity harness: `scripts/hmasd_workspace_ticket.py`.
- Workspace write-boundary guard: `scripts/hmasd_workspace_boundary_guard.py`.

No role reads every routed document. The active assignment or role charter names the smallest necessary subset.
## Repository surfaces
- Git-tracked code and tests are Code Project Manager implementation truth.
- `logs/<run-id>/` is Code Project Manager-owned runtime evidence written only by an exact assigned native operator or CPM.
- `docs/project/CURRENT_WORK.md` is a WDM-owned public link/schema index. CPM owns project-operation records; WDM owns its workflow-control-plane session/common records.
- `docs/project/` holds stable project principles and executable plans.
- `docs/research/cdc/` holds Pro-adjudicated scientific state mechanically recorded by Code Project Manager without reinterpretation.
- `docs/external-review/` holds exact external evidence and transport facts.
- `docs/report/ITERATION_<n>.md` is the Chinese valid-iteration report.
- `.agents/roles/` holds authority; `.agents/skills/` mechanics; `.codex/agents/` fixed child profiles.
- `local_research/` is ignored advisory output. Explorer owns its direction and methodology review items under `local_research/pro_reviews/`, with one operation per assigned item root and stable binding.
