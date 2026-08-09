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
| Workflow Design Manager | its exact assignment and `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`; expand only on a lazy trigger below | runtime, science and implementation state |
| Agentify Transport child | its exact requester assignment, `.codex/agents/hmasd-agentify-transport.toml`, `.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md`, agentify Skill and its workspace | science, code, `CURRENT_WORK.md` and workflow history |
| Independent Research Explorer | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, independent-research Skill, required principles and named sources | `CURRENT_WORK.md`, code, runtime and workflow state |
| registered native child | its exact assignment, `.codex/agents/<profile>.toml`, named Role, then assignment-named files | `CURRENT_WORK.md`, persistent history and other roles |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` | repository state outside the question |

A child never reconstructs task history. Missing identity, authority, path or
completion condition fails closed. Persistent sessions route workflow defects
and requirements to WDM; only WDM modifies or accepts workflow-control-plane
surfaces.

## Lazy workflow context triggers

The WDM default load is the exact assignment and WDM Role only. Expand context
only when the current task crosses one of these boundaries:

| Trigger | Load the owner surface |
|---|---|
| User change or reported workflow defect requires a plan | `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md` |
| Designing or dispatching a child or cross-session interface | `hmasd-writing-agent-assignments` and `docs/project/SESSION_WORKSPACE_CONTRACT.md` |
| Confirmed plan is being implemented or verified | `.agents/skills/hmasd-workflow-change-audit/SKILL.md` |
| Stable owner, interface, dependency or context edge is material | `docs/project/WORKFLOW_MAP.md` |
| Status, continuity or successor rotation is being updated | WDM `CURRENT_WORK` index and linked session/common records |

Specialized Agentify, CPM-mechanical and Explorer-mechanical interfaces remain
with their owner contracts; this router keeps only the registered pointers and
cross-role boundaries.

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
agentify_transport_test_parent=workflow_design_manager

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
code_project_manager_runtime_capacity_admission=exclusive
code_project_manager_runtime_capacity_pool_units=3
code_project_manager_routine_implementation_agent=hmasd-implementer-terra
code_project_manager_protected_implementation_agent=hmasd-implementer
cpm_mechanical_child=hmasd-cpm-mechanical
cpm_mechanical_parent=code_project_manager
project_map_owner=code_project_manager
project_map_update=same_commit_when_stable_architecture_fact_changes

independent_research_canonical_scientific_authority=none
independent_research_explorer_write_scope=local_research_including_explorer_owned_pro_reviews|temp/handoffs/explorer_to_code_manager/
independent_research_explorer_public_handoff_git_authority=none
independent_research_continuity_entry=local_research/RESEARCH_CONTINUITY.md
independent_research_continuity_owner=independent_research_explorer
independent_research_explorer_external_review_request_and_intake_authority=exclusive_for_independent_research_reviews
independent_research_experiment_roster_owner=scientific_direction_dependency_design_and_intake_only
independent_research_runtime_capacity_owner=code_project_manager
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
formal_compute_authority=user_only
explorer_mechanical_child=hmasd-explorer-mechanical
explorer_mechanical_parent=independent_research_explorer
workflow_change_request_route=workflow_design_manager
workflow_child_parent=workflow_design_manager|workflow_child_acceptance_authority=none|workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace|session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md
workflow_child_git_authority=none
native_child_authority=exact_assignment_only
workflow_assignment_writing_skill=hmasd-writing-agent-assignments
one_artifact_one_acceptance_owner=true
workflow_design_charter=WORKFLOW_DESIGN_MANAGER.md
cross_task_transport=codex_native_send_message_to_thread
```

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

The Independent Research Explorer may use the four already registered
read-only research children for one exact adaptive scientific question per dispatch;
campaign barriers and research authority remain unchanged. Detailed selection
and question-roster guidance lives in the independent-research Skill and its
parallel-workflow reference.

The Explorer's registered `hmasd-explorer-mechanical` child is a separate
read-only literal-fact organization capability, not a scientific consultant or
campaign member; it has no write, Git, runtime, science, technical-acceptance,
spawn or cross-task authority. Its profile and role are
`.codex/agents/hmasd-explorer-mechanical.toml` and
`.agents/roles/EXPLORER_MECHANICAL_OPERATOR.md`.

WDM is the semantic integrator and acceptance owner. Registered child roles and
the stable delegation boundary are owned by their Role, Skill and
`docs/project/WORKFLOW_MAP.md`; the router keeps only the child pointers above.

## Routed owner documents

- Workflow authority and roles: `.agents/roles/WORKFLOW_DESIGN_MANAGER.md` and `.agents/roles/WORKFLOW_*.md`.
- Stable workflow orientation: `docs/project/WORKFLOW_MAP.md`.
- Shared session/workspace contract: `docs/project/SESSION_WORKSPACE_CONTRACT.md`.
- WDM public state: `docs/project/CURRENT_WORK.md`, `docs/project/current-work/sessions/workflow_design_manager.md`, `docs/project/current-work/common/workflow_control_plane.md`.
- WDM durable/temporary workspace: `docs/session-workspaces/workflow_design_manager/`, `temp/sessions/workflow_design_manager/`.
- Collaborative design and workflow-change mechanics: `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`, `.agents/skills/hmasd-workflow-change-audit/SKILL.md`.
- Explorer research, validation and methodology pointers: `.agents/skills/hmasd-independent-research-exploration/SKILL.md`, `.agents/skills/hmasd-explorer-project-validation/SKILL.md`, `.agents/skills/hmasd-explorer-mechanical/SKILL.md`, `.agents/skills/hmasd-independent-research-pro-review/SKILL.md`.
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
