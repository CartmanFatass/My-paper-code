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
| Code Project Manager task | its exact code assignment, `.agents/roles/CODE_PROJECT_MANAGER.md`, assignment-named design, code and tests, plus bounded read-only `CURRENT_WORK.md` when checking the current code boundary | runtime reviews/runs, portfolio and workflow-design history |
| Research Operations Manager task | `docs/project/CURRENT_WORK.md`, `.agents/roles/RESEARCH_OPERATIONS_MANAGER.md`, then only current-boundary review, runtime, evidence and state paths | implementation details outside an exact Code-PM return, workflow-design history |
| dedicated Workflow Design Manager task | its exact workflow-design assignment, `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`, `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`, then `.agents/skills/hmasd-workflow-change-audit/SKILL.md` only after plan confirmation and only named control-plane files | `CURRENT_WORK.md`, runtime reviews/runs, science and implementation |
| Independent Research Explorer task | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, `.agents/skills/hmasd-independent-research-exploration/SKILL.md`, algorithm-principles sections 1 and 3, then user-named read-only research sources | `CURRENT_WORK.md`, formal science/runtime, code and workflow state |
| Independent Research Pro Review Operator task | its exact user-authorized methodology or single-direction review assignment, `.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md`, `.agents/skills/hmasd-independent-research-pro-review/SKILL.md`, then the shared transport mechanics named by that Skill | `CURRENT_WORK.md`, formal review rounds, runtime/science/code state and the registered formal Pro conversation |
| registered native child | its exact assignment, its `.codex/agents/*.toml` profile, the named `.agents/roles/*.md` charter, then only assignment-named files | `CURRENT_WORK.md`, persistent-task history, other role charters |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` interface supplied by the question | repository history or files outside the question boundary |
A child never reconstructs task history. A missing identity, path, authority or completion condition fails closed instead of triggering a project-state search.

## Universal authority boundary

```text
workflow_design_manager_session=019f9d2f-e0ea-7411-9fd7-386f45f76909
code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
research_operations_manager_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b
workflow_design_manager_workflow_design_authority=exclusive
workflow_design_manager_workflow_runtime_authority=none
workflow_design_manager_current_work_authority=none
workflow_design_manager_scientific_authority=none
workflow_design_manager_code_acceptance_authority=none
workflow_design_manager_git_authority=direct_for_workflow_design_surfaces
workflow_design_manager_remote_repository_authority=permanent_user_grant
workflow_design_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
workflow_design_manager_external_review_runtime_authority=none
workflow_design_manager_experiment_runtime_authority=none
code_project_manager_code_authority=exclusive
code_project_manager_technical_acceptance_authority=exclusive
code_project_manager_runtime_authority=none
code_project_manager_current_work_read=bounded_read_only_on_demand
code_project_manager_current_work_write_authority=none
code_project_manager_scientific_authority=none
code_project_manager_git_authority=direct_for_code_tests_and_code_science_index
code_project_manager_remote_repository_authority=permanent_user_grant
code_project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
research_operations_manager_runtime_authority=exclusive
research_operations_manager_current_work_authority=exclusive
research_operations_manager_formal_external_review_transport_authority=exclusive
research_operations_manager_experiment_dispatch_and_result_routing=exclusive
research_operations_manager_mechanical_result_acceptance=exclusive
research_operations_manager_code_authority=none
research_operations_manager_code_acceptance_authority=none
research_operations_manager_scientific_authority=none
research_operations_manager_git_authority=direct_for_runtime_review_evidence_report_ledger_and_state
research_operations_manager_remote_repository_authority=permanent_user_grant
research_operations_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
independent_research_explorer_session=019fb398-0a76-7bd0-9400-c5ea4eefa5de
independent_research_review_operator_session=019fb311-6137-7781-9708-3df24da34a4b
independent_research_canonical_scientific_authority=none
independent_research_explorer_write_scope=local_research_except_pro_reviews
independent_research_review_operator_transport_authority=exclusive_for_user_authorized_independent_research_review
independent_research_review_operator_write_scope=local_research/pro_reviews_plus_registered_cross_task_handoff_helper
independent_research_review_operator_formal_workflow_authority=none
independent_research_review_operator_scientific_authority=none
formal_compute_authority=user_only
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
native_child_authority=exact_assignment_only
one_artifact_one_acceptance_owner=true
cross_task_routing=locked_role_session_model_thinking
cross_task_routing_skill=hmasd-cross-task-routing
```
The user permanently authorizes Workflow Design Manager, Code Project Manager and Research Operations Manager to fetch and push their accepted nonoverlapping path sets there; no other egress is covered. Independent research tasks have no Git or repository-egress authority.
There is no Controller, persistent Monitor, dispatcher, semantic relay, role registry or global lease. Workflow Design Manager owns workflow design, Code Project Manager owns code and technical acceptance, Research Operations Manager owns formal runtime and formal Pro transport, and External Pro owns science. The Independent Research Pro Review Operator owns only its separate registered conversation and local independent-review archive.
`hmasd-pro-response-monitor` sees only metadata and may observe one exact turn for either registered transport owner. Both persistent project managers may request workflow design directly; Workflow Design Manager returns to the exact requester.

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
concurrency_policy=file_ownership_only
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
isolated_worktree_identity=workspace_ticket_only
hmasd_worktree_root=C:/worktrees/HMASD
project_write_scope=current_checkout_plus_verified_ticket_worktree
external_workspace_access=read_only
raw_external_worktree_creation=forbidden
drive_or_path_alias_creation=forbidden
handoff_document_write_trigger=explicit_user_request_only
operational_recovery_owner=research_operations_manager
operational_recovery_scientific_iteration_cost=zero
```
Generic Superpowers Skills are not executed. Use project-native Skills, keep active code small, and use Git as archive. Tests create no approval owner.
The current HMASD checkout and one valid assignment-ticket worktree are the only agent-writable project directories; every other directory is read-only to project agents, while project-external reads remain allowed.
Agents do not create, edit, copy, move, delete or redirect files outside that scope and do not create drive mappings, junctions or path aliases. Isolated worktrees are provisioned only by `scripts/hmasd_workspace_ticket.py` beneath `C:/worktrees/HMASD`; raw external `git worktree` is not an authority path.
A future project-external write requires a new explicit user instruction for its exact target and does not broaden this standing boundary.

## Routed project mechanisms

- Scientific principles and evidence complexity: `docs/project/ALGORITHM_PRINCIPLES.md`, `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`.
- Longitudinal scientific-decision ledger: `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`.
- Pro-assisted design and code-science audits: `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.
- Workflow-design changes: `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`.
- Code and technical acceptance: `.agents/roles/CODE_PROJECT_MANAGER.md`.
- Research operations and direct Pro transport: `.agents/roles/RESEARCH_OPERATIONS_MANAGER.md`.
- Mechanical experiment execution: `.agents/roles/EXPERIMENT_OPERATOR.md`.
- Silent long-Pro-turn observation: `.agents/roles/PRO_RESPONSE_MONITOR.md`.
- External Pro interface: `.agents/roles/EXTERNAL_PRO.md`.
- CPU/runtime facts, only when needed: `docs/project/AGENT_CONTEXT.md`.
- Implementation mechanics: `.agents/skills/hmasd-agile-research-development/SKILL.md`.
- Collaborative workflow design: `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`.
- Persistent-role cross-task routing: `.agents/skills/hmasd-cross-task-routing/SKILL.md`.
- Control-plane audit and execution: `.agents/skills/hmasd-workflow-change-audit/SKILL.md`.
- Browser review mechanics: `.agents/skills/hmasd-review-round/SKILL.md`.
- Independent advisory research: `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`, `.agents/skills/hmasd-independent-research-exploration/SKILL.md`.
- Independent methodology and single-direction Pro review: `.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md`, `.agents/skills/hmasd-independent-research-pro-review/SKILL.md`.
- Isolated-worktree identity harness: `scripts/hmasd_workspace_ticket.py`.
- Workspace write-boundary guard: `scripts/hmasd_workspace_boundary_guard.py`.
- Pro-response metadata broker: `scripts/hmasd_pro_response_sentinel.py`.

No role reads every routed document. The active assignment or role charter
names the smallest necessary subset.
## Repository surfaces

- Git-tracked code and tests are Code Project Manager implementation truth.
- `logs/<run-id>/` is Research Operations Manager runtime evidence.
- `docs/project/CURRENT_WORK.md` is Research Operations Manager operational state; Code Project Manager may read it on demand only to check the current code boundary and cannot edit, stage, commit or advance it.
- `docs/project/` holds stable project principles and executable plans.
- `docs/research/cdc/` holds Pro-adjudicated scientific state mechanically recorded by Research Operations Manager.
- `docs/external-review/` holds exact external evidence and transport facts.
- `docs/report/ITERATION_<n>.md` is the Chinese valid-iteration report.
- `.agents/roles/` holds authority; `.agents/skills/` mechanics; `.codex/agents/` fixed child profiles.
- `local_research/` is ignored advisory output. The Explorer owns it except for `local_research/pro_reviews/`, which is owned only by the registered Independent Research Pro Review Operator.
