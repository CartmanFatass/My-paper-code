# Code Project Manager workspace

```text
owner_task_source=research_scheduler
owner_mode=treatment|integration
owner_assignment_fields=parent_owner_assignment|owner_mode|direction_or_treatment|ticket|worktree|base_commit|owned_paths|result_destination
durable_workspace=docs/session-workspaces/code_project_manager/
temporary_workspace=temp/sessions/code_project_manager/
workflow_surface_owner=false
```

This tracked directory holds compact CPM project-operation plans, runtime
contracts and accepted receipts. It contains no workflow-design authority and
does not duplicate scientific state, runtime evidence or another session's
context. CPM routes workflow defects to WDM and retains code, runtime and
operational ownership.

An assignment-scoped CPM owner task sends an authorized External Pro question
through the registered Agentify transport child and archives the returned raw
response. Treatment and integration scopes remain separate.

Authority and path ownership come from
`docs/project/SESSION_WORKSPACE_CONTRACT.md`.
