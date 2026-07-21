---
name: hmasd-experiment
description: Use only inside the persistent HMASD experiment-monitor session when it receives a registered run assignment, creates and manages that session's heartbeat, performs bounded ETA-based progress checks, deletes the heartbeat after a tool-confirmed terminal callback, or relays one terminal result. Do not use for experiment design, launch, code repair, scientific interpretation, ordinary status reads, or controller work.
---

# HMASD Experiment Monitor

Accept only an assignment whose first lines explicitly invoke:

```text
$hmasd-dispatch-task
$hmasd-experiment
```

Read `../hmasd-dispatch-task/SKILL.md`, `references/monitor-task.json`,
`../hmasd-dispatch-task/references/session-roles.json`,
`references/experiment-protocol.md`, and only the run paths supplied in the
assignment. Do not read project-control, algorithm, implementation-plan,
experiment-history, external-review, or archive documents.

Before monitoring, require the current Codex task ID to equal
`session-roles.json.roles.experiment_monitor.thread_id` and require the
assignment `role_skill` to equal that entry's `role_skill`. Otherwise return
`TASK_BLOCKED` through the router without reading run artifacts or creating a
heartbeat.

The controller supplies one `MONITOR_ASSIGNMENT` containing
`role_skill=.agents/skills/hmasd-experiment/SKILL.md`, the run ID, status path,
registered progress sources and fields, deadline, and expected terminal
payload. The monitor session creates and owns its heartbeat after accepting the
assignment. The controller never creates, updates, pauses, or deletes that
heartbeat. The monitor must not launch, restart, repair, extend, or interpret
the experiment.

Each heartbeat performs one bounded check and ends. Running progress remains in
the monitor session. It estimates remaining time from registered counters and
retargets only its own heartbeat; the interval is never shorter than 10
minutes. At terminal state, actionable monitor error, or deadline, keep the
heartbeat active, resolve the controller through `$hmasd-dispatch-task`, and send
the stable terminal payload. Delete and verify deletion of the heartbeat only
after the send tool confirms the controller task. Never use sleep, continuous
polling, broad artifact scans, duplicate automations, or waiting messages to
the controller.

Within those boundaries, use model judgment rather than a fixed progress state
machine. Select the registered counters that best explain current progress,
estimate ETA from recent movement, adjust cadence to expected information gain,
and report a concise anomaly explanation when direct evidence supports one.
Do not require every run to expose identical progress fields, and do not turn a
missing optional metric into experiment failure. Strictness applies to the
assigned run identity, read-only authority, terminal evidence and callback—not
to one universal progress template.

Diagnose a monitoring anomaly from the registered evidence before reporting it.
Try reasonable read-only alternatives inside the run boundary; do not ask the
controller for a command sequence or file-by-file recipe. A retry reuses the
same assignment with semantic `recovery_context` and an observable outcome,
explicitly activates both Skills again, and leaves the monitor free to choose
the bounded recovery method.

If callback delivery fails, leave the heartbeat active. Its next wake retries
only the same `handoff_id`; it does not reread unrelated artifacts or repeat
experiment work. If delivery succeeded but deletion failed, the controller's
router treats the repeated `handoff_id` idempotently.

## Reply to Controller

Take the controller session ID only from
`session-roles.json.roles.controller.thread_id`. Immediately before a terminal
callback, resolve that ID with `$hmasd-dispatch-task`; copy the returned `hostId`,
`threadId`, `model`, and `thinking` unchanged into the send. Never take a return
ID or model setting from the assignment, monitor registry, conversation history,
or heartbeat prompt. Delivery succeeds only when the send tool returns the same
registered controller `threadId`; only then may this session delete its
heartbeat.

Every terminal callback prompt begins with `$hmasd-dispatch-task`, followed by a
blank line and the registered `EXPERIMENT_MONITOR` payload.
