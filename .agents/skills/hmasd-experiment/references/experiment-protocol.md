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
failed    -> read the direct error once, notify controller, pause schedule
completed -> read the result once, notify controller, pause schedule
missing   -> report monitor error, pause schedule
```

Show registered parameters, progress, primary live metric, observed ETA and
next check in the monitor. Adapt the same schedule to observed ETA:

- above 120 minutes: 30 minutes;
- 30 to 120 minutes: 15 minutes;
- 10 to 30 minutes: 5 minutes;
- 2 to 10 minutes: 2 minutes;
- at most 2 minutes or finalization: 1 minute;
- unknown ETA: 15 minutes.

Do not create heartbeat files or duplicate monitoring tasks.

## Failure Classification

Read only the status source and direct error needed to locate the first failed
boundary. Distinguish operational failure, invalid implementation, analyzer or
monitor failure, and valid scientific FAIL. Compare with the nearest known-good
path, make one falsifiable root-cause hypothesis, and run one bounded diagnostic.

Do not change budget, seed, reward, model, threshold or estimand as an
operational repair. Do not rescue a retired line.
