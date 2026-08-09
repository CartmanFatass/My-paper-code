# Research Scheduler workspace

This durable directory documents the user-owned Desktop Research Scheduler
workspace. Live assignment state is ignored and temporary.

```text
workflow_surface_owner=true
workspace_owner=research_scheduler
durable_workspace=docs/session-workspaces/research_scheduler/
live_roster_locator=temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md
binding_locator=temp/sessions/research_scheduler/bindings/<assignment_id>.json
binding_keys=assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active
tracked_live_state=false
```

The roster is a human-readable locator for active ephemeral owner tasks. The
binding is a minimal mutation-boundary identity record, not task context,
queue state or a result ledger. Do not create a tracked live roster or a
Scheduler `.codex` profile.

After the Scheduler reads the direct exact-task result and mechanically confirms
the canonical result locator, it changes the existing binding's `active` value
to `false` (`active=false`) before requesting archive/close. This revokes owner
mutation authority before archival. A successful archive removes that task's
entry from the active roster; canonical assignment/result locators remain
restart/archive evidence in their declared owner surfaces, not a Scheduler
result ledger. If archive/close is ambiguous, the binding remains inactive and
exactly one unresolved observation stays in the roster until direct exact-ID or
user resolution. Inactive bindings are ignored for active discovery, while an
exact stale identity remains fail-closed under the separate mechanical identity
contract. The six-key binding is unchanged: no new lifecycle fields, queue
state, or state machine is added.
