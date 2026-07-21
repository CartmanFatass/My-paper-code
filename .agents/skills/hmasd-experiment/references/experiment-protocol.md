# HMASD Persistent Monitor Protocol

## Assignment

Accept only one active run. A `MONITOR_ASSIGNMENT` must provide:

- run ID and absolute run root;
- absolute authoritative `runner_status.txt` path;
- exact progress files and fields, or `unavailable`;
- terminal spellings and terminal payload key;
- deadline.

Use `monitor-task.json` for monitor and cadence policy only. Take monitor and
controller session IDs from the dispatcher-owned `session-roles.json`. Resolve all
live route fields through `$hmasd-dispatch-task`; registry files never supply
`hostId`, model, or reasoning effort.

On acceptance, use `automation_update` to create one heartbeat named from the
run ID and targeted to this monitor session. Start at the registry's fallback
cadence, capture the returned heartbeat ID, then update that same heartbeat with
its final prompt. The prompt contains only the dispatcher Skill path,
`session-roles.json`, this Skill path, `monitor-task.json`, the assignment
fields, and the heartbeat ID. Its first lines explicitly invoke
`$hmasd-dispatch-task` and `$hmasd-experiment`. Verify
the target, prompt, cadence, and `ACTIVE` state. Do not put project-control,
algorithm, review, conversation history, model, or thinking context in the
prompt. Reuse the exact heartbeat if the same assignment is delivered again;
never create a duplicate.

## One bounded heartbeat

Inspect the authoritative status and the smallest useful registered progress
evidence once per wake. Choose the read-only method and fields that best explain
the current run; do not sleep, poll continuously, scan unrelated artifacts,
restart work, or interpret scientific results.

For a running state, write one concise `MONITOR_PROGRESS` entry in this task:

```text
observed_at=<time>
phase=<phase>
progress=<registered counters and percent>
elapsed=<duration>
eta=<straight-line estimate or unavailable>
metrics=<registered fields or unavailable>
```

Then use judgment to retarget only this session's heartbeat when the expected
information gain changes, verify it remains targeted here and `ACTIVE`, and end
locally. The interval is never shorter than 10 minutes. Prefer the slowest
active arm and recent progress over nominal duration; increase frequency near
expected completion and reduce it when little can change. If ETA is unavailable,
retain the configured fallback. Do not send running or unchanged-state messages
to the controller. Completed training counters with a nonterminal runner state
mean finalization is pending, not failure.

## Terminal relay

Use the assignment's registered terminal meanings and the authoritative status
semantics. Missing, malformed, path-escaping or stale-beyond-deadline evidence
is actionable only after reasonable read-only diagnosis inside the registered
run boundary.

At terminal, error, or deadline:

1. keep this session's heartbeat `ACTIVE`;
2. resolve the controller's live route immediately;
3. send exactly one payload through `$hmasd-dispatch-task`:

```text
$hmasd-dispatch-task

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
