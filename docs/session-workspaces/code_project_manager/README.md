# Code Project Manager workspace

```text
session_owner_role=code_project_manager
session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
durable_workspace=docs/session-workspaces/code_project_manager/
temporary_workspace=temp/sessions/code_project_manager/
workflow_surface_owner=false
```

This tracked directory holds compact CPM project-operation plans, runtime
contracts and accepted receipts. It contains no workflow-design authority and
does not duplicate scientific state, runtime evidence or another session's
context. CPM returns agent-configuration issues to Root and retains code,
runtime and operational ownership.

CPM scope is exactly `direction:<id>|shared:<component>`, where each atom
matches `[a-z0-9][a-z0-9._-]{0,63}` and rejects empty values, path separators,
extra colons, whitespace and `..`. A scope CPM's technical acceptance is final
for its exact slice. Root may mechanically integrate accepted candidates in a
separate integration worktree and run union Tests/Static; a Root union PASS is
mechanical evidence only, not technical-semantic acceptance. Root does not
resolve or rewrite semantic conflicts; they return to the owning scope CPM,
with a temporary named `shared:<component>` CPM for a shared dependency.

CPM sends External Pro questions through the registered
`hmasd-cpm-agentify-transport` child using the file-only
`AGENTIFY_REVIEW_BATCH_ASSIGNMENT` contract (`batch_path|results_path`).
Requester-partitioned temporary files live under
`temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/`.
Before reading a terminal result, CPM applies
`.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py`
to the expected and returned result paths. External Pro remains outside the
agent tree; Root owns user communication, lifecycle, relay and physical Git,
while CPM retains review meaning and technical acceptance and the transport
child has no acceptance authority.

## Root-managed tracked-write worktrees

The Root provision predicate is `required` when an assignment may write a
tracked path, including mixed tracked-plus-ignored output. Read-only,
ignored-only and temporary-only assignments are exempt. The owner request
contains `owner`, `assignment`, `base_revision`, `owned_paths`,
`expected_candidate`, `terminal_intent`, `recovery_ref` and
`ignored_evidence_disposition`. `base_revision` is the Root-selected base;
`expected_candidate` binds the anticipated candidate; `terminal_intent` is the
owner's requested `integrate`, `release` or `retain` outcome. A recovery uses an
explicit prior reference or `none`, and mixed output must receive an explicit
ignored-evidence disposition.

The worktree is a physical resource only: it is not ticket or agent identity,
authority, or runtime authorization. Root alone creates candidate worktrees,
mechanically integrates accepted required paths, and releases or retains them. Its lifecycle
has one nonterminal state, `active`; L2 children cannot create, manage, release,
or commit in a worktree, and raw child worktree commands remain forbidden.
Release is allowed only after accepted-required mechanical integration, or when the
worktree is clean and disposable, has no unique unprotected commit, and has an
explicit ignored-evidence disposition. A mismatch, dirty state, nonignored
untracked file or in-use worktree stays local and fails closed; legacy
worktrees are untouched. Worktree use adds no runtime accounting and does not
authorize costly runtime; Root observes live resource facts and the owning CPM
makes scope-local runtime judgment.

Authority and path ownership come from `AGENTS.md` and the CPM role charter.
