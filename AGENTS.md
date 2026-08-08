# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
project_history_in_router=forbidden
role_specific_procedure_in_router=forbidden
```

This file is the minimum identity, authority and routing contract. History,
results, budgets, procedures and implementation detail belong to the named
Role, Skill, Profile, contract or workflow record.

## Precedence and role resolution

Precedence is: direct user instruction, this router, the applicable role
charter, an authorized current-state read, the named design/science contract,
then procedural Skills. Use exactly one route:

| Active identity | Read after this file | Do not load by default |
|---|---|---|
| Code Project Manager | `docs/project/CURRENT_WORK.md`, `.agents/roles/CODE_PROJECT_MANAGER.md`, then the active workstream's named paths | unrelated workstreams, research corpus and workflow history |
| Workflow Design Manager | its assignment, `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`, `CURRENT_WORK.md`, linked WDM records, `WORKFLOW_MAP.md`, collaborative-workflow Skill, writing-agent Skill at child/cross-session design or dispatch, then workflow-change-audit after plan confirmation | runtime, science and implementation state |
| Agentify Transport child | its exact requester assignment, `.codex/agents/hmasd-agentify-transport.toml`, `.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md`, agentify Skill and its workspace | science, code, `CURRENT_WORK.md` and workflow history |
| Independent Research Explorer | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, independent-research Skill, required principles and named sources | `CURRENT_WORK.md`, code, runtime and workflow state |
| registered native child | its exact assignment, `.codex/agents/<profile>.toml`, named Role, then assignment-named files | `CURRENT_WORK.md`, persistent history and other roles |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` | repository state outside the question |

A child never reconstructs task history. Missing identity, authority, path or
completion condition fails closed. Persistent sessions route workflow defects
and requirements to WDM; only WDM modifies or accepts workflow-control-plane
surfaces.

Before designing, dispatching or materially revising any subagent or
cross-session assignment/interface, use
`hmasd-writing-agent-assignments`. Read
`docs/project/SESSION_WORKSPACE_CONTRACT.md` as the stable boundary. The Skill
keeps the brief self-contained and natural-language; paths, schemas, statuses
and forked context are anchors, not meaning, so the child can use local
judgment without reconstructing the parent session.

## Authority and ownership

```text
workflow_design_manager_workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces
workflow_design_manager_workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces
workflow_design_manager_workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces
workflow_design_manager_workflow_runtime_authority=none
workflow_design_manager_scientific_authority=none
workflow_design_manager_code_acceptance_authority=none
workflow_design_manager_current_work_authority=public_index_and_own_workflow_control_plane_records_only
workflow_design_manager_git_authority=exclusive_for_workflow_control_plane_surfaces
workflow_design_manager_remote_repository_authority=permanent_user_grant
workflow_design_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
workflow_design_manager_agentify_source_authority=permanent_user_grant_for_hmasd_transport_only
workflow_design_manager_agentify_workspace=C:/Projects/agentify-desktop
workflow_design_manager_agentify_git_authority=direct_modify_commit_and_push
workflow_design_manager_external_review_runtime_authority=none
workflow_design_manager_experiment_runtime_authority=none
workflow_design_owner=workflow_design_manager
persistent_session_workflow_design_authority=none
persistent_session_workflow_acceptance_authority=none
persistent_session_workflow_git_authority=none

agentify_transport_child=hmasd-agentify-transport
agentify_transport_child_parent=code_project_manager|independent_research_explorer
agentify_transport_skill=hmasd-agentify-transport
agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT
agentify_transport_assignment_fields=batch_path|results_path
agentify_transport_batch_file_fields=provider|question_paths
agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT
agentify_transport_result_fields=status|results_path|error
agentify_transport_terminal_status=COMPLETE|ERROR
agentify_transport_wait_visibility=silent_until_terminal_native_final

code_project_manager_code_authority=exclusive
code_project_manager_technical_acceptance_authority=exclusive
code_project_manager_runtime_authority=exclusive
code_project_manager_current_work_authority=exclusive
code_project_manager_scientific_authority=none
code_project_manager_git_authority=direct_for_code_runtime_review_evidence_report_ledger_and_state
code_project_manager_remote_repository_authority=permanent_user_grant
code_project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
code_project_manager_formal_external_review_request_and_intake_authority=exclusive
code_project_manager_experiment_dispatch_and_result_routing=exclusive
code_project_manager_mechanical_result_acceptance=exclusive
code_project_manager_routine_implementation_agent=hmasd-implementer-terra
code_project_manager_protected_implementation_agent=hmasd-implementer
cpm_mechanical_child=hmasd-cpm-mechanical
cpm_mechanical_parent=code_project_manager
cpm_mechanical_assignment=CPM_MECHANICAL_TASK_ASSIGNMENT
cpm_mechanical_assignment_fields=spec_path|result_path
cpm_mechanical_result=CPM_MECHANICAL_TASK_RESULT
cpm_mechanical_result_fields=status|result_path|error
cpm_mechanical_terminal_status=COMPLETE|ERROR
cpm_mechanical_wait_visibility=silent_until_terminal_native_final
cpm_mechanical_write_scope=assignment_named_temporary_outputs_only
cpm_mechanical_acceptance_authority=none
cpm_mechanical_git_authority=none
cpm_mechanical_scientific_authority=none
cpm_mechanical_runtime_authority=no_experiment_no_readiness_no_agentify
cpm_mechanical_finalize_owner=code_project_manager
cpm_mechanical_activation=after_fresh_profile_reload
cpm_mechanical_active_research_state_effect=none
project_map_owner=code_project_manager
project_map_update=same_commit_when_stable_architecture_fact_changes

independent_research_canonical_scientific_authority=none
independent_research_explorer_write_scope=local_research_including_explorer_owned_pro_reviews|temp/handoffs/explorer_to_code_manager/
independent_research_explorer_public_handoff_git_authority=none
independent_research_continuity_entry=local_research/RESEARCH_CONTINUITY.md
independent_research_continuity_owner=independent_research_explorer
independent_research_explorer_external_review_request_and_intake_authority=exclusive_for_independent_research_reviews
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
formal_compute_authority=user_only

workflow_change_request_route=workflow_design_manager
workflow_child_parent=workflow_design_manager|workflow_child_acceptance_authority=none|workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace|session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
workflow_child_git_authority=none
native_child_authority=exact_assignment_only
workflow_assignment_writing_skill=hmasd-writing-agent-assignments
workflow_implementer_parallelism=min(disjoint_owned_path_families,available_native_slots_minus_integrator)
integrated_review=one_per_integrated_batch_by_default|parallel_only_for_independent_review_questions|no_automatic_rereview
one_artifact_one_acceptance_owner=true
workflow_router_consistency_check=required_for_every_workflow_change
workflow_design_charter=WORKFLOW_DESIGN_MANAGER.md
cross_task_transport=codex_native_send_message_to_thread
cross_task_model_and_thinking_overrides=omit
```

WDM's standing remote grant covers accepted workflow-control-plane paths and
the named Agentify transport source workspace only. The requester-owned
Agentify transport child receives one exact file assignment from CPM or
Explorer and returns one native terminal result; WDM never relays a live
review or result. There is no Controller, dispatcher, registry, semantic relay,
persistent Monitor, global lease or workflow queue.

## Hard project and workspace boundaries

```text
development_mode=agile_algorithm_research
project_development_skill=hmasd-agile-research-development
workflow_change_skill=hmasd-workflow-change-audit
hmasd_python_interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
test_scope=proof_sized
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
workflow_hash_admission=forbidden
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
workflow_parallel_implementation=file_family_adaptive
isolated_worktree_identity=workspace_ticket_only
hmasd_worktree_root=C:/worktrees/HMASD
project_write_scope=current_checkout_plus_verified_ticket_worktree
external_workspace_access=read_only
raw_external_worktree_creation=forbidden
drive_or_path_alias_creation=forbidden
```

Agents write only within the current checkout or a verified registered ticket
worktree. Project-external reads are allowed; project-external writes require a
new exact user instruction except for WDM's standing Agentify transport grant.
Children do not stage, commit, push, route or accept. Git-visible checks and
ticket retirement remain WDM-owned for workflow surfaces.

## Registered child pointers and normal delegation

The fixed registered workflow children are:

- Workflow Auditor/Scout: `.codex/agents/hmasd-workflow-auditor.toml` and `.agents/roles/WORKFLOW_AUDITOR.md`.
- Workflow Implementer: `.codex/agents/hmasd-workflow-implementer.toml` and `.agents/roles/WORKFLOW_IMPLEMENTER.md`.
- Workflow Reviewer: `.codex/agents/hmasd-workflow-reviewer.toml` and `.agents/roles/WORKFLOW_REVIEWER.md`.

WDM is the semantic integrator and acceptance owner. To reduce cost, routine
bounded work is normally delegated to these cheaper registered children: an
Implementer handles a frozen mechanical slice, an Auditor supplies local facts
when the surface is unclear, and one Reviewer examines a coherent integrated
batch. This is adaptive judgment, not a mandatory three-stage state machine;
the stable decision rules live in `docs/project/WORKFLOW_MAP.md`.

## Routed owner documents

- Workflow authority and roles: `.agents/roles/WORKFLOW_DESIGN_MANAGER.md` and `.agents/roles/WORKFLOW_*.md`.
- Stable workflow orientation: `docs/project/WORKFLOW_MAP.md`.
- Shared session/workspace contract: `docs/project/SESSION_WORKSPACE_CONTRACT.md`.
- WDM public state: `docs/project/CURRENT_WORK.md`, `docs/project/current-work/sessions/workflow_design_manager.md`, `docs/project/current-work/common/workflow_control_plane.md`.
- WDM durable/temporary workspace: `docs/session-workspaces/workflow_design_manager/`, `temp/sessions/workflow_design_manager/`.
- Collaborative design and workflow-change mechanics: `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`, `.agents/skills/hmasd-workflow-change-audit/SKILL.md`.
- Explorer research, validation and methodology pointers: `.agents/skills/hmasd-independent-research-exploration/SKILL.md`, `.agents/skills/hmasd-explorer-project-validation/SKILL.md`, `.agents/skills/hmasd-independent-research-pro-review/SKILL.md`.
- Code orientation (CPM-owned): `docs/project/PROJECT_MAP.md`.
- Boundary and ticket checks: `scripts/hmasd_workspace_boundary_guard.py`, `scripts/hmasd_workspace_ticket.py`.
- Other role contracts: `.agents/roles/CODE_PROJECT_MANAGER.md`, `.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md`, `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, `.agents/roles/EXTERNAL_PRO.md`.

Role charters own authority and capability; Skills own normal paths and one
fallback; Profiles own model, sandbox and pointers; focused tests verify their
contracts. No role reads every routed document.

## Repository ownership summary

Git-tracked code and tests, runtime evidence, scientific records and reports
remain with CPM; advisory research remains with Explorer; transport mechanics
remain with the requester-owned Agentify transport child. `docs/project/CURRENT_WORK.md` is only a WDM
link/schema index. Handoffs under `temp/handoffs/` are disposable and never
replace canonical owner records or enter Git.
