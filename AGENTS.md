# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
project_history_in_router=forbidden
role_specific_procedure_in_router=forbidden
```

Every HMASD task receives this small router for identity, minimum documents and
shared boundaries. History, results, budgets and mechanics load only when assigned.

## Precedence and role resolution

Precedence is: direct user instruction, this router, the applicable role
charter, `docs/project/CURRENT_WORK.md` for Project Manager only, the named
scientific/design contract, then procedural Skills.

Use exactly one route:

| Active identity | Read after this file | Do not load by default |
|---|---|---|
| Project Manager task | `docs/project/CURRENT_WORK.md`, `.agents/roles/PROJECT_MANAGER.md`, then only current-boundary code, design/review and tests | completed rounds, workflow-design history, unrelated roles |
| dedicated Workflow Design Manager task | its exact workflow-design assignment, `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`, `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`, then `.agents/skills/hmasd-workflow-change-audit/SKILL.md` only after plan confirmation and only named control-plane files | `CURRENT_WORK.md`, runtime reviews/runs, science and implementation |
| dedicated External Review Operator task | its exact inter-task assignment, `.agents/roles/EXTERNAL_REVIEW_OPERATOR.md`, `.agents/skills/hmasd-review-round/SKILL.md`, then only assignment-named round files | `CURRENT_WORK.md`, project history, scientific interpretation, implementation files outside the review allow-list |
| registered native child | its exact assignment, its `.codex/agents/*.toml` profile, the named `.agents/roles/*.md` charter, then only assignment-named files | `CURRENT_WORK.md`, PM history, other role charters |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` interface supplied by the question | repository history or files outside the question boundary |

A child never reconstructs task history. A missing identity, path, authority or
completion condition fails closed instead of triggering a project-state search.

## Universal authority boundary

```text
workflow_design_manager_persistent_task=one
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
project_manager_persistent_task=one
project_manager_code_authority=exclusive
project_manager_runtime_authority=exclusive
project_manager_current_work_authority=exclusive
project_manager_scientific_authority=none
project_manager_technical_acceptance_authority=exclusive
project_manager_git_authority=direct_for_code_runtime_evidence_and_state
project_manager_remote_repository_authority=permanent_user_grant
project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
project_manager_external_review_dispatch_and_result_routing=exclusive
project_manager_experiment_dispatch_and_result_routing=exclusive
project_manager_round_metrics_skill=hmasd-pm-round-metrics
external_review_operator_transport_authority=exclusive
external_review_operator_scientific_authority=none
external_review_operator_code_acceptance_authority=none
external_review_operator_git_authority=none
formal_compute_authority=user_only
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
native_child_authority=exact_assignment_only
one_artifact_one_acceptance_owner=true
cross_task_routing=probe_confirmed_session_plus_conversation_local_cache
cross_task_routing_skill=hmasd-cross-task-routing
cross_task_model_thinking_override=omitted
```

The user permanently authorizes Workflow Design Manager and Project Manager to fetch and push accepted nonoverlapping path sets there. No other remote or egress is covered.

There is no Controller, persistent Monitor, dispatcher, semantic relay, role
registry or global lease. Workflow Design Manager owns workflow design only. External
Review Operator alone controls the browser and returns exact raw files to PM;
`hmasd-pro-response-monitor` sees only its metadata sentinel. External Pro owns
science; PM owns code and its mechanical runtime.

With an active grant, PM follows the exact Pro-selected sequence, dispatches
reviews and authorized runs, and maintains its code attention state. Workflow
Manager is invoked only to change workflow design. Only the user expands science
or compute authority.

## Universal project constraints

```text
development_mode=agile_algorithm_research
project_development_skill=hmasd-agile-research-development
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
handoff_document_write_trigger=explicit_user_request_only
```
Generic Superpowers Skills are not executed. Use project-native Skills, keep
active code small, and use Git as archive. Tests create no approval owner.

Each mutating assignment owns an exact path set. Disjoint writers may work in
parallel; overlapping writes are serialized. Native children never run Git.
For an isolated code worktree, PM creates one machine-readable workspace ticket;
the child resolves it before editing and never copies, guesses or substitutes
an absolute path. PM verifies the same ticket after the child returns.
Each role stages only its accepted owned paths, checks the staged path set
and `git diff --cached --check`, then commits and pushes `aggressive`. Git commit
plus exact path set is identity; hashes and handoff receipts are forbidden.

## Routed project mechanisms

- Scientific principles and evidence complexity: `docs/project/ALGORITHM_PRINCIPLES.md`, `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`.
- Longitudinal scientific-decision ledger: `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`.
- Pro-assisted design and code-science audits: `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.
- Workflow-design changes: `.agents/roles/WORKFLOW_DESIGN_MANAGER.md`.
- PM code authority and mechanical research runtime: `.agents/roles/PROJECT_MANAGER.md`.
- Mechanical Pro transport and callback: `.agents/roles/EXTERNAL_REVIEW_OPERATOR.md`.
- Mechanical experiment execution: `.agents/roles/EXPERIMENT_OPERATOR.md`.
- Silent long-Pro-turn observation: `.agents/roles/PRO_RESPONSE_MONITOR.md`.
- External Pro interface: `.agents/roles/EXTERNAL_PRO.md`.
- CPU/runtime facts, only when needed: `docs/project/AGENT_CONTEXT.md`.
- Implementation mechanics: `.agents/skills/hmasd-agile-research-development/SKILL.md`.
- PM complete-workflow metrics: `.agents/skills/hmasd-pm-round-metrics/SKILL.md`.
- Collaborative workflow design: `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md`.
- Persistent-role cross-task routing: `.agents/skills/hmasd-cross-task-routing/SKILL.md`.
- Control-plane audit and execution: `.agents/skills/hmasd-workflow-change-audit/SKILL.md`.
- Browser review mechanics: `.agents/skills/hmasd-review-round/SKILL.md`.
- Isolated-worktree identity harness: `scripts/hmasd_workspace_ticket.py`.
- Pro-response metadata broker: `scripts/hmasd_pro_response_sentinel.py`.

No role reads every routed document. The active assignment or role charter names the smallest necessary subset.
## Repository surfaces

- Git-tracked code is implementation truth.
- `logs/<run-id>/` is runtime evidence.
- `docs/project/CURRENT_WORK.md` is PM-only code attention and runtime state, not Workflow-Manager or child bootstrap.
- `docs/project/` holds stable project principles and executable plans.
- `docs/research/cdc/` holds durable scientific state.
- `docs/external-review/` holds exact external evidence.
- `docs/report/ITERATION_<n>.md` is the Chinese valid-iteration report.
- `.agents/roles/` holds authority; `.agents/skills/` mechanics; `.codex/agents/` fixed child profiles.

Persistent Codex roles probe-confirm live target sessions, cache them only in conversation, and omit model and thinking overrides; session IDs are addresses, not authority.
Ambiguity fails closed to the user. Native children keep fixed profiles and one final return rather than session sends.
