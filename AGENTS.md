# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
project_history_in_router=forbidden
role_specific_procedure_in_router=forbidden
```

Every HMASD task in this workspace automatically receives this file. Keep it
small: it identifies the active role, points to the minimum required documents,
and states only boundaries shared by every role. Scientific history, current
results, experiment budgets, browser mechanics and implementation details live
elsewhere and are loaded only when an assignment names them.

## Precedence and role resolution

Precedence is: direct user instruction, this router, the applicable role
charter, `docs/project/CURRENT_WORK.md` for Project Manager only, the named
scientific/design contract, then procedural Skills.

Use exactly one route:

| Active identity | Read after this file | Do not load by default |
|---|---|---|
| root Project Manager | `docs/project/CURRENT_WORK.md`, `.agents/roles/PROJECT_MANAGER.md`, then only the current boundary's named design/review/plan | completed rounds, historical reports, unrelated roles |
| dedicated External Review Operator task | its exact inter-task assignment, `.agents/roles/EXTERNAL_REVIEW_OPERATOR.md`, `.agents/skills/hmasd-review-round/SKILL.md`, then only assignment-named round files | `CURRENT_WORK.md`, project history, scientific interpretation, implementation files outside the review allow-list |
| registered native child | its exact assignment, its `.codex/agents/*.toml` profile, the named `.agents/roles/*.md` charter, then only assignment-named files | `CURRENT_WORK.md`, PM history, other role charters |
| external GPT-5.6 Pro | the submitted question, its allow-list and `.agents/roles/EXTERNAL_PRO.md` interface supplied by the question | repository history or files outside the question boundary |

A child never reconstructs task history. If its assignment omits a required
identity, path, authority or completion condition, it fails closed instead of
searching project state for one.

## Universal authority boundary

```text
project_manager_persistent_task=one
project_manager_project_authority=exclusive
project_manager_scientific_authority=none
project_manager_technical_acceptance_authority=exclusive
project_manager_git_authority=direct
project_manager_external_review_transport=question_dispatch_and_result_intake_only
external_review_operator_transport_authority=exclusive
external_review_operator_scientific_authority=none
external_review_operator_code_acceptance_authority=none
external_review_operator_git_authority=none
formal_compute_authority=user_only
external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary
native_child_authority=exact_assignment_only
one_artifact_one_acceptance_owner=true
```

There is no Controller, persistent project Monitor, dispatcher, relay chain,
role-session registry or global write lease. One dedicated persistent External
Review Operator is the mechanical browser boundary: PM sends it an exact pushed
question assignment and receives its exact-raw completion notification. One registered nonpersistent
`hmasd-pro-response-monitor` is the explicit exception for silently observing
the metadata-only External-Review-Operator broker for a single already-submitted long Pro turn; it
owns no browser, transport or science.
External Pro owns scientific
designs, result interpretation, CDC changes and scientific successor choice
inside the user-authorized review boundary. Project Manager owns code,
engineering acceptance and mechanical realization; it does not adopt, reject
or reinterpret science. A child reports evidence but accepts nothing.

When `CURRENT_WORK.md` records an active autonomous grant, Project Manager
continues every in-scope code/experiment action, dispatches exact review
packages to the registered External Review Operator, and realizes every exact
External-Pro-selected successor without asking again. If science is not yet
decided, PM opens the smallest Pro review rather than choosing locally. Only
the user may expand protected scientific scope or formal-compute authority.

## Universal project constraints

```text
development_mode=agile_algorithm_research
project_development_skill=hmasd-agile-research-development
workflow_change_skill=hmasd-workflow-change-audit
superpowers_plugin=reference_only
superpowers_execution=disabled
backward_compatibility=not_required
test_scope=proof_sized
codebase_policy=small_active_line_only
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
concurrency_policy=file_ownership_only
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
isolated_worktree_identity=workspace_ticket_only
handoff_document_write_trigger=explicit_user_request_only
```

Generic Superpowers Skills are not executed in HMASD. Use the project-native
Skills only when their mechanics apply. Keep active code small; Git history is
the archive. Tests protect the exact claim or operational invariant and do not
create another approval owner.

Each mutating assignment owns an exact path set. Disjoint writers may work in
parallel; overlapping writes are serialized. Native children never run Git.
For an isolated worktree, PM creates one machine-readable workspace ticket;
the child resolves it before editing and never copies, guesses or substitutes
an absolute path. PM verifies the same ticket after the child returns.
Project Manager stages accepted paths, checks the staged path set and
`git diff --cached --check`, then commits and pushes `aggressive`. Git commit
plus exact path set is code identity; per-file hashes and handoff receipts are
forbidden.

## Routed project mechanisms

- Scientific principles: `docs/project/ALGORITHM_PRINCIPLES.md`.
- Longitudinal scientific-decision ledger: `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`.
- Pro-assisted design and code-science audits: `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.
- PM authority and automatic research loop: `.agents/roles/PROJECT_MANAGER.md`.
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
- `docs/project/CURRENT_WORK.md` is PM-only active state, not child bootstrap.
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
