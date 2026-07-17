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

Never omit target settings from a monitor relay. In the observed desktop
runtime, omitted settings inherit the sender turn and can make Luna/Sol threads
appear to exchange models. Use exactly:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<target host_id>",
  threadId: "<target thread_id>",
  model: "<target live model_id>",
  thinking: "<target live reasoning_effort>",
  prompt: "<stable handoff_id and terminal payload>"
})
```

Immediately before the call, require the frozen target thread to be idle and
resolve its current model/effort from the local thread state. Immediately
afterward, require the same values. If the target is active, keep the monitor
heartbeat active and retry at the next bounded wake. `hostId`, `threadId`,
`model`, and `thinking` are all mandatory.
Explicit values preserve an already matching target; they must never repair a
mismatch. Use the stable handoff ID for idempotence and never edit or restore
thread settings after delivery.

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

The terminal payload contains only the handoff ID, automation ID, run ID, state,
phase, status path, and result or direct-error path. The monitor reads no result
or stderr. After the guarded send returns and the controller settings remain
unchanged, pause the existing monitor heartbeat and verify `PAUSED`. Only then
report `handoff_confirmed=true`. If send or settings verification fails, leave
the heartbeat active for a bounded retry and report `monitor_handoff_error`. If
pause fails, report `monitor_pause_error`; neither error is an experiment FAIL.

The controller treats `handoff_id` idempotently, reads the registered result or
direct error once, applies the existing branch, and records closure. A duplicate
message for a closed handoff is a no-op. A future run reactivates the same
heartbeat on the unchanged monitor conversation with a new run namespace.

Show registered parameters, progress, primary live metric, observed ETA and
next check in the monitor. Adapt the same schedule to observed ETA:

- above 120 minutes: 30 minutes;
- 30 to 120 minutes: 15 minutes;
- 10 to 30 minutes: 5 minutes;
- 2 to 10 minutes: 2 minutes;
- at most 2 minutes or finalization: 1 minute;
- unknown ETA: 15 minutes.

Do not create heartbeat files or duplicate monitoring tasks. Tool invocation
and its returned confirmation are the authority for schedule target and state;
prose describing an intended invocation is not authority.

## Failure Classification

Read only the status source and direct error needed to locate the first failed
boundary. Distinguish operational failure, invalid implementation, analyzer or
monitor failure, and valid scientific FAIL. Compare with the nearest known-good
path, make one falsifiable root-cause hypothesis, and run one bounded diagnostic.

Do not change budget, seed, reward, model, threshold or estimand as an
operational repair. Do not rescue a retired line.
