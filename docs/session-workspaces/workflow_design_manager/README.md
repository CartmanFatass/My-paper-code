# Workflow Design Manager workspace

```text
session_owner_role=workflow_design_manager
session_owner_id=019fb73d-5635-7b63-b165-6c5129bc0217
durable_workspace=docs/session-workspaces/workflow_design_manager/
temporary_workspace=temp/sessions/workflow_design_manager/
workflow_surface_owner=true
```

This tracked directory holds compact WDM workflow plans and reload receipts.
WDM alone designs, accepts and integrates workflow-control-plane changes. It
does not contain project science, code, runtime evidence or review results.

`WORKFLOW_DEFECT_QUEUE.md` is the chronological incident log for typed reports.
Reports remain advisory; the log preserves history but is not a scheduler,
approval state or global blocker.

Authority and path ownership come from
`docs/project/SESSION_WORKSPACE_CONTRACT.md` and the WDM role charter.
