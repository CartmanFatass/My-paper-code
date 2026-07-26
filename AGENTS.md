# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
project_history_in_router=forbidden
role_specific_procedure_in_router=forbidden
```

Every HMASD task receives this small router. It identifies the active role,
minimum required documents and shared boundaries. Scientific history, results,
budgets, browser mechanics and implementation details load only when assigned.

## Precedence and role resolution

Precedence is: direct user instruction, this router, the applicable role
charter, `docs/project/CURRENT_WORK.md` for Workflow Manager only, the named
scientific/design contract, then procedural Skills.

Use exactly one route:

| Active identity | Read after this file | Do not load by default |
|---|---|---|
| dedicated Workflow Manager task | `docs/project/CURRENT_WORK.md`, `.agents/roles/WORKFLOW_MANAGER.md`, then only the active boundary's named workflow/review/plan | implementation files, completed rounds, unrelated roles |
| Project Manager task | its exact Workflow-Manager assignment, `.agents/roles/PROJECT_MANAGER.md`, then only assignment-named scientific contract, code and tests | `CURRENT_WORK.md`, workflow history, transport mechanics, unrelated roles |
| dedicated External Review Operator task | its exact inter-task assignment, `.agents/roles/EXTERNAL_REVIEW_OPERATOR.md`, `.agents/skills/hmasd-review-round/SKILL.md`, then only assignment-named round files | `CURRENT_WORK.md`, project history, scientific interpretation, implementation files outside the review allow-list |
| registered native child | its exact assignment, its `.codex/agents/*.toml` profile, the named `.agents/roles/*.md` charter, then only assignment-named files | `CURRENT_WORK.md`, PM history, other role charters |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` interface supplied by the question | repository history or files outside the question boundary |

A child never reconstructs task history. A missing identity, path, authority or
completion condition fails closed instead of triggering a project-state search.

## Universal authority boundary

```text
workflow_manager_persistent_task=one
workflow_manager_project_coordination_authority=exclusive
workflow_manager_workflow_authority=exclusive
workflow_manager_scientific_authority=none
workflow_manager_code_acceptance_authority=none
workflow_manager_git_authority=direct_for_workflow_review_and_state
workflow_manager_remote_repository_authority=permanent_user_grant
workflow_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
workflow_manager_external_review_dispatch_and_result_routing=exclusive
workflow_manager_experiment_dispatch_and_result_routing=exclusive
project_manager_persistent_task=one
project_manager_code_authority=exclusive
project_manager_scientific_authority=none
project_manager_technical_acceptance_authority=exclusive
project_manager_git_authority=direct_for_code_and_engineering_evidence
project_manager_remote_repository_authority=permanent_user_grant
project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git
project_manager_external_review_authority=post_implementation_code_index_and_repair_only
external_review_operator_transport_authority=exclusive
external_review_operator_scientific_authority=none
external_review_operator_code_acceptance_authority=none
external_review_operator_git_authority=none
formal_compute_authority=user_only
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
native_child_authority=exact_assignment_only
one_artifact_one_acceptance_owner=true
```

The user permanently authorizes Workflow Manager and Project Manager to fetch and
push accepted nonoverlapping paths there. No other remote or egress is covered.

There is no Controller, persistent Monitor, dispatcher, semantic relay, role
registry or global lease. Workflow Manager owns the control plane. External
Review Operator alone controls the browser and returns raw to Workflow Manager;
`hmasd-pro-response-monitor` sees only its metadata sentinel. External Pro owns
science, PM owns code, and Workflow Manager never paraphrases either side.

With an active grant, Workflow Manager coordinates the Pro-selected sequence,
assigns bounded PM code, dispatches reviews and authorized runs, and records
state. PM accepts code only; only the user expands science or compute authority.

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
Each authority stages only its accepted owned paths, checks the staged path set
and `git diff --cached --check`, then commits and pushes `aggressive`. Git commit
plus exact path set is identity; hashes and handoff receipts are forbidden.

## Routed project mechanisms

- Scientific principles and evidence complexity: `docs/project/ALGORITHM_PRINCIPLES.md`, `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`.
- Longitudinal scientific-decision ledger: `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`.
- Pro-assisted design and code-science audits: `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.
- Workflow coordination and automatic research loop: `.agents/roles/WORKFLOW_MANAGER.md`.
- PM code authority and engineering loop: `.agents/roles/PROJECT_MANAGER.md`.
- Mechanical Pro transport and callback: `.agents/roles/EXTERNAL_REVIEW_OPERATOR.md`.
- Mechanical experiment execution: `.agents/roles/EXPERIMENT_OPERATOR.md`.
- Silent long-Pro-turn observation: `.agents/roles/PRO_RESPONSE_MONITOR.md`.
- External Pro interface: `.agents/roles/EXTERNAL_PRO.md`.
- CPU/runtime facts, only when needed: `docs/project/AGENT_CONTEXT.md`.
- Implementation mechanics: `.agents/skills/hmasd-agile-research-development/SKILL.md`.
- Control-plane audit: `.agents/skills/hmasd-workflow-change-audit/SKILL.md`.
- Browser review mechanics: `.agents/skills/hmasd-review-round/SKILL.md`.
- Isolated-worktree identity harness: `scripts/hmasd_workspace_ticket.py`.
- Pro-response metadata broker: `scripts/hmasd_pro_response_sentinel.py`.

No role reads every routed document. The active assignment or role charter
names the smallest necessary subset.

## Repository surfaces

- Git-tracked code is implementation truth.
- `logs/<run-id>/` is runtime evidence.
- `docs/project/CURRENT_WORK.md` is Workflow-Manager-only active state, not PM or child bootstrap.
- `docs/project/` holds stable project principles and executable plans.
- `docs/research/cdc/` holds durable scientific state.
- `docs/external-review/` holds exact external evidence.
- `docs/report/ITERATION_<n>.md` is the Chinese user report for a valid
  conclusion-bearing iteration.
- `.agents/roles/` holds role authority; `.agents/skills/` holds mechanics;
  `.codex/agents/` holds fixed native-child profiles.

Every cross-task send resolves the target task's live model and effort
immediately before sending and passes both explicitly in the send operation.
Never infer them from a fixed table. The sending assignment records the exact
return target, model and effort for its completion notification. Registered
benchmark and experiment profiles are the only fixed native-child exceptions;
the dedicated review task follows the user's current per-task choice.
