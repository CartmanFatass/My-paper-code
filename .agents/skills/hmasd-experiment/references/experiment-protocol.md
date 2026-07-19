# HMASD Persistent Monitor Protocol

## Assignment

Accept only one active run. A `MONITOR_ASSIGNMENT` must provide:

- run ID and absolute run root;
- absolute authoritative `runner_status.txt` path;
- exact progress files and fields, or `unavailable`;
- terminal spellings and terminal payload key;
- deadline and initial cadence;
- the registered automation ID.

Use `monitor-task.json` for stable task and automation IDs only. Resolve all
task models and reasoning effort live through `$hmasd-task-router`; registry
files never supply them.

On acceptance, retarget the existing heartbeat automation to this monitor task,
install the assignment prompt, set it `ACTIVE`, and verify ID, target, prompt,
schedule, and state. Do not create another automation or send a duplicate
assignment.

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

Then update only the existing automation schedule when the ETA bucket changes,
verify it remains targeted here and `ACTIVE`, and end with `MONITOR_RUNNING`.
Do not send running or unchanged-state messages to the controller.

Use the slowest active arm. Estimate ETA only after at least 5% completion and
with fresh progress:

```text
ETA > 4 hours       -> 30 minutes
2 hours < ETA <= 4 -> 20 minutes
45 min < ETA <= 2h -> 10 minutes
ETA <= 45 minutes  -> 5 minutes
unavailable/stale  -> 15 minutes
```

Relax to a longer interval only after ETA crosses its boundary by 25%. Tighten
immediately. If training counters are complete while runner state is still
running, report `FINALIZATION_PENDING`, use 5 minutes, and wait for the
authoritative terminal status.

## Terminal relay

Valid nonterminal state is `running`; valid terminal states are the assignment's
registered complete spelling and `failed`. Missing, malformed, unknown, stale
beyond the deadline, or path-escaping status is an actionable monitor error.

At terminal, error, or deadline:

1. update the existing automation to `PAUSED`;
2. verify the same automation is paused;
3. resolve the controller's live route immediately;
4. send exactly one payload through `$hmasd-task-router`:

```text
EXPERIMENT_MONITOR
terminal=<COMPLETE|COMPLETED|FAILED|ACTIONABLE_ERROR|TIMEOUT>
handoff_id=<run-id>:<state>:<status-updated-at>
run=<run-id>
state=<state>
phase=<phase>
status=<absolute status path>
payload=<result path, direct-error path, or none>
reason=<one actionable line or none>
```

If pause verification fails, send nothing and leave the next heartbeat able to
retry. If live controller routing cannot be resolved, keep the heartbeat active
and retry only that resolution on the next tick. Never refresh a route mirror,
change a task model, create a replacement task, or send a second terminal
payload.
