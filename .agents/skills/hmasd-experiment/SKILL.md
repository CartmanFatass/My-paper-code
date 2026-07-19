---
name: hmasd-experiment
description: Use only inside the persistent HMASD experiment-monitor task when it receives a registered run assignment, performs heartbeat progress checks, changes its own ETA-based cadence, pauses at terminal state, or relays one terminal result. Do not use for experiment design, launch, code repair, scientific interpretation, ordinary status reads, or controller work.
---

# HMASD Experiment Monitor

Read `../hmasd-task-router/SKILL.md`, `references/monitor-task.json`,
`references/experiment-protocol.md`, and only the run paths supplied in the
assignment. Do not read project-control, algorithm, implementation-plan,
experiment-history, external-review, or archive documents.

The controller supplies one `MONITOR_ASSIGNMENT` containing the run ID, status
path, registered progress sources and fields, deadline, expected terminal
payload, and initial cadence. The monitor owns the registered heartbeat from
assignment until terminal relay. It must not launch, restart, repair, extend,
or interpret the experiment.

Each heartbeat performs one bounded check and ends. Running progress remains in
the monitor task. At terminal state, actionable monitor error, or deadline,
pause and verify the heartbeat, resolve the controller's live route through
`$hmasd-task-router`, and send exactly one terminal payload. Never use sleep,
continuous polling, broad artifact scans, duplicate automations, or waiting
messages to the controller.
