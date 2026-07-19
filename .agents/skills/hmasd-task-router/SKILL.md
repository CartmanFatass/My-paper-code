---
name: hmasd-task-router
description: Use whenever an HMASD workflow sends to an existing Codex task, expects a terminal message back from that task, or assigns work to the persistent Luna Medium experiment monitor. It resolves the live model and thinking settings for both endpoints, prevents model replacement, and forbids ambiguous or duplicate delivery. Do not use for ordinary work inside the active task.
---

# HMASD Task Router

This Skill owns Codex task routing only. It does not own algorithm decisions,
review state, experiment state, task creation, or model selection.

## Resolve Both Endpoints

Before any cross-task send, run `scripts/resolve_task_route.ps1` separately for
the target task and the active controller task. Live Codex task metadata is the
routing authority. A project registry may mirror those values but may not
select them.

Require an unarchived task and nonempty `model` and `thinking`. If a registry
value differs from live metadata, do not send and do not change either task's
model. Refresh the mirror from live metadata or return `BLOCKED_ROUTE_MISMATCH`.

The resolved route has exactly these fields:

```text
hostId
threadId
model
thinking
```

## Send to a Persistent Codex Task

Call `send_message_to_thread` with exactly the resolved target `hostId`,
`threadId`, `model`, and `thinking`, plus `prompt`. Omitting `model` or
`thinking` is forbidden. Supplying the target's exact current pair preserves
its routing; it does not change the model.

The receiving task returns its terminal payload with the controller's resolved
four route fields plus `prompt`. Resolve the controller route again immediately
before that return if the user may have changed its model or reasoning setting.

If a send returns a definite pre-delivery `notLoaded` failure, load only the
registered target task, retry the identical route once, then restore the
controller task. Do not retry an ambiguous delivery, create a replacement task,
substitute another role, or send the same route twice.

## Use the Persistent Experiment Monitor

`$hmasd-experiment` owns one registered Luna Medium monitor task and one
registered heartbeat automation. Before each assignment, resolve both that task
and the active controller. The controller binds the run by updating the
existing automation and targeting the resolved monitor thread; it does not
create another task or automation and does not send a duplicate assignment.

Each heartbeat only schedules one bounded monitor turn; it is not a transport
substitute and carries no terminal result. At terminal state the monitor first
pauses and verifies that automation, then resolves the controller again from
live metadata, verifies the registered mirror, and sends one terminal payload
with the controller's exact five-field route. Its Luna Medium setting is fixed
when the monitor task is created; the controller route never selects or changes
either model.

## Stop Conditions

Return `BLOCKED` before delivery when a task is missing, archived, lacks route
metadata, disagrees with its registered mirror, or the previous delivery is
ambiguous. A heartbeat may wake the registered monitor, but never replaces the
exact terminal route. Never use a shell wait, alternate task, duplicate
automation, or sender-default model inference.
