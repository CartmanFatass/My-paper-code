---
name: hmasd-task-router
description: Mandatory communication contract for every HMASD Codex session. Read at task entry and use before every message to an existing Codex task or expected reply. Resolve both endpoints from live metadata and send the target's exact current model and thinking values so communication never changes task routing. This Skill does not own research, implementation, review, monitoring, task creation, or model selection.
---

# HMASD Communication

Every HMASD session reads this Skill at entry. It governs communication only;
the session's role-specific Skill governs its work.

## Resolve Live Routes

Immediately before a cross-task send, run
`scripts/resolve_task_route.ps1 -ThreadId <id>` for the sender and recipient.
Require one unarchived task with nonempty `hostId`, `threadId`, `model`, and
`thinking`.

Registries may store stable task IDs and roles, but must not prescribe or mirror
models or reasoning effort. Live metadata is authoritative. Never infer the
recipient route from the sender, a registry, an earlier message, or a project
document. Never change a task's model or thinking to satisfy delivery.

## Send Exactly Once

Call `send_message_to_thread` with the recipient's resolved fields:

```text
hostId=<live recipient hostId>
threadId=<live recipient threadId>
model=<live recipient model>
thinking=<live recipient thinking>
prompt=<task-local payload>
```

Omitting `model` or `thinking` is forbidden. Supplying their exact live values
preserves the recipient's current route; it does not select a new route.

The recipient resolves the controller or other destination again immediately
before replying and uses that destination's exact live four-field route. A task
must not reuse route metadata received in the prompt as current truth.

Send one task message and one terminal reply unless the owning role contract
explicitly defines another message. Do not send polling, waiting, heartbeat, or
unchanged-state messages across tasks. A definite pre-delivery `notLoaded`
error permits one identical retry after loading the same target. An accepted or
ambiguous delivery is never repeated.

## Role Boundaries

- The controller sends a self-contained implementation task and receives one
  implementation terminal report.
- The controller sends one `START_REVIEW` and receives one `REVIEW_COMPLETE` or
  `REVIEW_BLOCKED` from the External Review Manager.
- The controller assigns one run and receives one terminal payload from the
  experiment monitor; heartbeat ticks remain inside the monitor task.

Communication does not create a task, switch a task, operate a browser, update
an automation, authorize an experiment, or choose a scientific route. Return
`BLOCKED_ROUTE` only when live routing cannot be resolved safely.
