# HMASD Persistent Monitor Protocol

## Assignment

Accept only one active run. A `MONITOR_ASSIGNMENT` must provide:

- run ID and absolute run root;
- absolute authoritative `runner_status.txt` path;
- exact progress files and fields, or `unavailable`;
- terminal spellings and terminal payload key;
- deadline.

Use `monitor-task.json` for monitor and cadence policy only. Take monitor and
controller session IDs from the router-owned `session-roles.json`. Resolve all
live route fields through `$hmasd-task-router`; registry files never supply
`hostId`, model, or reasoning effort.

On acceptance, use `automation_update` to create one heartbeat named from the
run ID and targeted to this monitor session. Start at the registry's fallback
cadence, capture the returned heartbeat ID, then update that same heartbeat with
its final prompt. The prompt contains only the router Skill path,
`session-roles.json`, this Skill path, `monitor-task.json`, the assignment
fields, and the heartbeat ID. Verify
the target, prompt, cadence, and `ACTIVE` state. Do not put project-control,
algorithm, review, conversation history, model, or thinking context in the
prompt. Reuse the exact heartbeat if the same assignment is delivered again;
never create a duplicate.

## One bounded heartbeat

Read the status file exactly once and each registered progress source at most
once. Do not sleep, poll, watch, scan the run directory, parse unregistered
logs, restart work, or interpret scientific results.

For a running state, write one concise `MONITOR_PROGRESS` entry in this task:

```text
observed_at=<time>
phase=<phase>
progress=<registered counters and percent>
elapsed=<duration>
eta=<straight-line estimate or unavailable>
metrics=<registered fields or unavailable>
```

Then update only this session's heartbeat schedule when the ETA bucket changes,
verify it remains targeted here and `ACTIVE`, and end with `MONITOR_RUNNING`.
Do not send running or unchanged-state messages to the controller.

Use the slowest active arm. Estimate ETA only after at least 5% completion and
with fresh progress:

```text
ETA > 4 hours       -> 30 minutes
2 hours < ETA <= 4 -> 20 minutes
ETA <= 2 hours      -> 10 minutes
unavailable/stale  -> 15 minutes
```

Relax to a longer interval only after ETA crosses its boundary by 25%. Tighten
immediately. If training counters are complete while runner state is still
running, report `FINALIZATION_PENDING`, use 10 minutes, and wait for the
authoritative terminal status.

## Terminal relay

Valid nonterminal state is `running`; valid terminal states are the assignment's
registered complete spelling and `failed`. Missing, malformed, unknown, stale
beyond the deadline, or path-escaping status is an actionable monitor error.

At terminal, error, or deadline:

1. keep this session's heartbeat `ACTIVE`;
2. resolve the controller's live route immediately;
3. send exactly one payload through `$hmasd-task-router`:

```text
EXPERIMENT_MONITOR
role=experiment_monitor
terminal=<COMPLETE|COMPLETED|FAILED|ACTIONABLE_ERROR|TIMEOUT>
handoff_id=<run-id>:<state>:<status-updated-at>
run=<run-id>
state=<state>
phase=<phase>
status=<absolute status path>
payload=<result path, direct-error path, or none>
reason=<one actionable line or none>
```

4. require the send tool to return the registered controller `threadId`;
5. delete this heartbeat with `automation_update` and verify deletion.

If routing or delivery cannot be confirmed, leave the heartbeat active and
retry only the same terminal payload on the next wake. If delivery succeeds but
deletion fails, retry deletion; a repeated payload uses the same `handoff_id`
and is idempotent at the controller. Never pause before delivery, create a
replacement session, change a task model, or interpret the result.
