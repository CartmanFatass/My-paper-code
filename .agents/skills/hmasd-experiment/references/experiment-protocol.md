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

Resolve the monitor conversation from the local conversation registry. Reuse a
usable conversation; wait or recover a busy one; create one only when none is
usable. Never change its model.

Each scheduled wake reads the authoritative status once:

```text
running   -> update the monitor dashboard
failed    -> relay a terminal envelope to the controller
completed -> relay a terminal envelope to the controller
missing   -> relay a monitor-error envelope to the controller
```

The terminal envelope contains a stable
`event_id=<run_id>:<state>:<status_updated_at>`, the automation id, controller
thread id, run id, state, phase, status path, and registered result or
direct-error path. Resolve the controller from the conversation registry and
send exactly once with the real cross-thread messaging tool. Bind `hostId` only
when the registry and send tool expose the same usable host; otherwise omit it
and rely on `event_id` deduplication. Always omit model or reasoning overrides.
A normal assistant message or a textual
`<heartbeat decision=NOTIFY>` block is a user-facing fallback, not proof that
the controller received anything. Report `relay_confirmed=true` only after the
tool returns success. If the tool is unavailable or fails, emit one native
`NOTIFY` as `monitor_relay_error`; do not claim delivery, schedule pause, or
experiment failure, and do not reread terminal artifacts on a retry.

Terminal schedule ownership belongs to the active controller. On receipt of a
terminal envelope, its first action is to pause the named automation and verify
the stored status is `PAUSED`. Only then does it read the registered result or
direct error once, interpret the outcome, and optionally post the final
dashboard back to the monitor conversation. Delivery may be mirrored by the
desktop runtime, so the controller deduplicates by `event_id` and treats later
copies as no-ops. The monitor may change the same schedule only for a
running-state ETA cadence update; it must not attempt terminal self-pause. This
ordering prevents a second terminal wake and keeps scientific interpretation
with the controller.

Show registered parameters, progress, primary live metric, observed ETA and
next check in the monitor. Adapt the same schedule to observed ETA:

- above 120 minutes: 30 minutes;
- 30 to 120 minutes: 15 minutes;
- 10 to 30 minutes: 5 minutes;
- 2 to 10 minutes: 2 minutes;
- at most 2 minutes or finalization: 1 minute;
- unknown ETA: 15 minutes.

Do not create heartbeat files or duplicate monitoring tasks. Tool invocation
and its returned confirmation are the authority for notification and schedule
state; prose describing an intended invocation is not authority.

## Failure Classification

Read only the status source and direct error needed to locate the first failed
boundary. Distinguish operational failure, invalid implementation, analyzer or
monitor failure, and valid scientific FAIL. Compare with the nearest known-good
path, make one falsifiable root-cause hypothesis, and run one bounded diagnostic.

Do not change budget, seed, reward, model, threshold or estimand as an
operational repair. Do not rescue a retired line.
