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

The direct External Pro transport contract is
`docs/session-workspaces/code_project_manager/PRO_REVIEW_TRANSPORT.md`.
CPM executes `prepare -> submit -> verify -> archive -> local_FIFO_intake` in
the persistent session; no transport or monitor child is registered. Code,
experiment and verifier children remain available only for their own exact
assignments.

Authority and path ownership come from
`docs/project/SESSION_WORKSPACE_CONTRACT.md`.
