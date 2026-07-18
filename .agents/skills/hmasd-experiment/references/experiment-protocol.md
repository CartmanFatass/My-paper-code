# HMASD Experiment Protocol

## Launch Boundary

Confirm the exact commit, branch, runner, configuration, seeds, environment and
optimizer budgets, output root, expected wall clock, and status authority.
Generate the real run timestamp once, at launch. Dry runs use `DRY_RUN` and do
not reserve a run id.

Use the shared scheduler for cloud work. Treat the server as available; ask the
user to wake it only after a real connection failure. Write large data to the
data disk and use a background shell session for long commands.

## Persistent Monitor

Resolve the monitor conversation and active controller from the local
conversation registry once when the run is activated. Embed the exact monitor
thread id, controller thread id, automation id and run id in the schedule
prompt; do not rediscover or replace them on later wakes. Reuse one monitor
conversation created as `Luna High` and one heartbeat schedule targeting it.
The model selection is made only at conversation creation. Never change either
conversation's model afterward, and never include model or thinking settings in
heartbeat create/update/retarget operations.

Initialize `logs/<run-id>/monitor_state.json` with
`scripts/monitor_state.ps1 -Mode init`. Record the exact controller and monitor
host/thread/model/effort, automation id, run id and status authority. This state
file is the durable handoff authority; conversation prose and an unrecorded
tool call are not lifecycle state. Initialize only while the heartbeat is active;
the script records its config path, status and `updated_at` as this run's
activation baseline.

Never omit target settings from a monitor relay. In the observed desktop
runtime, omitted settings inherit the sender turn and can make Luna/Sol threads
appear to exchange models. Use exactly:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<target host_id>",
  threadId: "<target thread_id>",
  model: "<frozen target model_id from monitor_state.json>",
  thinking: "<frozen target reasoning_effort from monitor_state.json>",
  prompt: "<stable handoff_id and terminal payload>"
})
```

Immediately before the call, invoke `codex_app__list_threads` and require one
entry whose `id` and `hostId` equal the frozen controller fields. The target is
idle only when its returned status is `notLoaded`, `completed`, or `idle`; a
`running` or unknown status is not idle. The API does not expose authoritative
live model/effort fields, so use only the frozen model/effort recorded by the
controller at activation and never claim a live re-read. A user-reported or
registry mismatch is `BLOCKED_THREAD_IDENTITY`, not something a message may
repair. `hostId`, `threadId`, `model`, and `thinking` are mandatory. After the
call, invoke `codex_app__list_threads` again and require the same host/thread
identity, then invoke `codex_app__read_thread` on the controller and locate one
delivered turn containing the exact handoff ID. Transition to
`RELAY_CONFIRMED` only with
`-ReadThreadReceipt
"host=<host>;thread=<thread>;turn=<uuid>;handoff=<handoff-id>"` built from that
returned target-thread observation.

Each scheduled wake reads the authoritative status once:

```text
running   -> update the dedicated monitor dashboard
failed    -> guarded direct terminal relay
completed -> guarded direct terminal relay
missing   -> guarded direct monitor_error relay
```

At a terminal boundary the monitor reads no result or stderr. It derives one
stable identifier:

```text
handoff_id = <run-id>:<state>:<status-updated-at>
```

The transition script reads the frozen `status_authority` itself. For a terminal
file it requires the recorded `run_id`, normalized `state`, `updated` timestamp,
`phase`, and `result_path` or `error_path` to equal the proposed terminal fields. For a
`missing` report it requires the authority file to be absent. It also recomputes
the exact handoff ID; caller-supplied status summaries or path variants cannot
advance the state machine.

The terminal payload contains only the handoff ID, automation ID, run ID, state,
phase, status path, and result or direct-error path. The monitor reads no result
or stderr. Advance the state machine exactly:

```text
RUNNING
-> TERMINAL_DETECTED
-> RELAY_CONFIRMED
-> AUTOMATION_PAUSED
-> CLOSED
```

After the guarded send returns, record the delivered controller turn UUID and
transition to `RELAY_CONFIRMED`. Pause the existing heartbeat with
`automation_update`, view the same automation id, then require the exact
`$CODEX_HOME/automations/<automation-id>/automation.toml` to contain the frozen
id, monitor thread and `status = "PAUSED"`. The state script records its
`updated_at` only when it is newer than the activation baseline and occurs after
the relay confirmation. It transitions to `AUTOMATION_PAUSED`, then `CLOSED` with the same
explicit handoff ID. Only `CLOSED`
means `handoff_confirmed=true`. Any failure transitions to `BLOCKED` with the
exact failed operation; it is not an experiment FAIL. Leaving `BLOCKED`
requires a typed resolution receipt.

The controller validates the state file, treats a closed `handoff_id`
idempotently, reads the registered result or direct error once, applies the
existing branch, and records closure. A duplicate message for a closed handoff
is a no-op. A future run reactivates the same
heartbeat on the unchanged monitor conversation with a new run namespace.
Closed validation uses the stored pause receipt rather than the later live
heartbeat state, so reactivation cannot invalidate an older handoff.

Show registered parameters, progress, primary live metric, observed ETA and
next check in the monitor. Adapt the same schedule to observed ETA:

- above 120 minutes: 30 minutes;
- 30 to 120 minutes: 15 minutes;
- 10 to 30 minutes: 5 minutes;
- 2 to 10 minutes: 2 minutes;
- at most 2 minutes or finalization: 1 minute;
- unknown ETA: 15 minutes.

Do not create heartbeat files or duplicate monitoring tasks. The recorded tool
receipts plus valid `monitor_state.json` are the authority; prose describing an
intended invocation is not authority.

## Failure Classification

Read only the status source and direct error needed to locate the first failed
boundary. Distinguish operational failure, invalid implementation, analyzer or
monitor failure, and valid scientific FAIL. The nearest known-good path is the
same runner/configuration with only the failed stage differing. Inspect at most
the authoritative status, its direct error and one comparator artifact; state
one falsifiable root-cause hypothesis and run at most one diagnostic.

Do not change budget, seed, reward, model, threshold or estimand as an
operational repair. Do not rescue a retired line.
