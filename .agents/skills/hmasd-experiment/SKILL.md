---
name: hmasd-experiment
description: Use only inside the persistent HMASD experiment-monitor session when it receives a registered run assignment, creates and manages that session's heartbeat, performs bounded ETA-based progress checks, deletes the heartbeat after a tool-confirmed terminal callback, or relays one terminal result. Do not use for experiment design, launch, code repair, scientific interpretation, ordinary status reads, or controller work.
---

# HMASD Experiment Monitor

Read `../hmasd-task-router/SKILL.md`, `references/monitor-task.json`,
`references/experiment-protocol.md`, and only the run paths supplied in the
assignment. Do not read project-control, algorithm, implementation-plan,
experiment-history, external-review, or archive documents.

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
heartbeat active, resolve the controller through `$hmasd-task-router`, and send
the stable terminal payload. Delete and verify deletion of the heartbeat only
after the send tool confirms the controller task. Never use sleep, continuous
polling, broad artifact scans, duplicate automations, or waiting messages to
the controller.

If callback delivery fails, leave the heartbeat active. Its next wake retries
only the same `handoff_id`; it does not reread unrelated artifacts or repeat
experiment work. If delivery succeeded but deletion failed, the controller's
router treats the repeated `handoff_id` idempotently.
