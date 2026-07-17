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
conversation registry. Reuse one monitor conversation and one heartbeat
schedule targeting it. Never change either conversation's model.

Do not use `send_message_to_thread` or any equivalent cross-thread steering for
monitor relay. In the observed desktop runtime, steering a Luna monitor from a
Sol controller applied Sol settings to the monitor, and the return relay then
applied Luna settings to the controller. Omitting model and reasoning fields did
not preserve the target. Host binding reduced duplicate delivery but did not
make model inheritance safe.

Each scheduled wake reads the authoritative status once:

```text
running   -> update the dedicated monitor dashboard
failed    -> retarget the same heartbeat to the controller
completed -> retarget the same heartbeat to the controller
missing   -> retarget the same heartbeat with monitor_error
```

At a terminal boundary the monitor reads no result or stderr. It updates the
existing automation in place, preserving id, kind and name while setting:

```text
targetThreadId = active controller
status         = ACTIVE
next cadence   = 1 minute
prompt         = terminal handoff containing automation id, run id, state,
                 phase, status path, and result or direct-error path
```

The monitor then verifies that the stored automation has the controller target
and remains active. It may report `handoff_confirmed=true` only after that
confirmation. If retargeting fails, return native `NOTIFY` with
`monitor_handoff_error`; do not claim delivery, pause, or experiment failure.

The controller's terminal-handoff wake first updates that same automation to
`PAUSED` and verifies the stored state. Only then does it read the registered
result or direct error once, interpret the outcome, and return native `NOTIFY`.
If pause fails or cannot be confirmed, report `monitor_pause_error` without
classifying the experiment as failed. A future run retargets the paused
automation back to the unchanged monitor conversation. This preserves a
dedicated dashboard, provides automatic controller handoff, and never steers a
conversation or supplies a model override.

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
