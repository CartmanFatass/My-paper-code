---
name: hmasd-task-router
description: Mandatory communication contract for every HMASD Codex session. Read at task entry and use before every message to an existing Codex task or expected reply. Immediately before sending, read the recipient's live delivery metadata and echo its current model and thinking values unchanged into the send so communication cannot alter them. This Skill does not manage models or own research, implementation, review, monitoring, or task creation.
---

# HMASD Communication

Every HMASD session reads this Skill at entry. It governs communication only;
the session's role-specific Skill governs its work.

## Read Recipient Delivery Metadata

Immediately before a cross-task send, run
`scripts/resolve_task_route.ps1 -ThreadId <recipient-id>` for the recipient only.
Require one unarchived task with nonempty `hostId`, `threadId`, `model`, and
`thinking`.

Registries may store stable task IDs and roles, but must not prescribe or mirror
models or reasoning effort. Live metadata is authoritative. Never infer the
recipient route from the sender, a registry, an earlier message, or a project
document. Never change a task's model or thinking to satisfy delivery.

`model` and `thinking` are read-only delivery arguments here. This Skill does
not store expected values, compare models, enforce a preferred model, select a
model, synchronize two tasks, or modify either task. It only copies the
recipient's values observed immediately before this send.

## Send Exactly Once

Call `send_message_to_thread` with the recipient's resolved fields:

```text
hostId=<live recipient hostId>
threadId=<live recipient threadId>
model=<live recipient model>
thinking=<live recipient thinking>
prompt=<task-local payload>
```

Omitting `model` or `thinking` is forbidden because sender defaults may alter
the recipient. Supplying the recipient's exact live values preserves its
current settings; it does not manage or select them.

Before replying, the recipient treats the reply destination as the new
recipient, reads its live delivery metadata, and uses those exact values. A task
must not reuse route metadata received in the prompt as current truth.

Send one task message and one terminal reply unless the owning role contract
explicitly defines another message. Do not send polling, waiting, heartbeat, or
unchanged-state messages across tasks. A definite pre-delivery `notLoaded`
error permits one identical retry after loading the same target. An accepted or
ambiguous delivery is never repeated.

## Require Delivery Proof

Delivery succeeds only when `send_message_to_thread` was actually called and
its tool result identifies the resolved recipient `threadId`. Compare that
returned target with the live recipient resolved immediately before the call.

Writing the payload in the sender's commentary or final response, emitting a
heartbeat directive, or placing text in delegation metadata is not cross-task
delivery. For a required callback, finish only after observing the matching
tool result. If the call fails before acceptance, keep the callback pending and
report the delivery failure locally; never claim that the recipient was
notified.

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
