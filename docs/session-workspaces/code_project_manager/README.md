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
context. CPM routes workflow defects to WDM and retains code, runtime and
operational ownership.

CPM sends External Pro questions directly with Agentify in the persistent
session and archives the returned raw response. No separate transport contract,
wrapper, monitor or transport child exists.

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
authority, or runtime admission. Root alone creates candidate worktrees,
integrates accepted required paths, and releases or retains them. Its lifecycle
has one nonterminal state, `active`; L2 children cannot create, manage, release,
or commit in a worktree, and raw child worktree commands remain forbidden.
Release is allowed only after accepted-required integration, or when the
worktree is clean and disposable, has no unique unprotected commit, and has an
explicit ignored-evidence disposition. A mismatch, dirty state, nonignored
untracked file or in-use worktree stays local and fails closed; legacy
worktrees are untouched. Worktree use consumes zero runtime units and does not
change CPM's independent three-unit pool or its admission judgment.

Authority and path ownership come from
`docs/project/SESSION_WORKSPACE_CONTRACT.md`.
