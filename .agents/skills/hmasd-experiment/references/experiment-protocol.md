# HMASD Experiment Protocol

## Launch Boundary

Confirm the exact commit, branch, runner, configuration, seeds, environment and
optimizer budgets, output root, expected wall clock, placement, and status
authority. Generate the timestamp once at launch; dry runs use `DRY_RUN`.

The monitor deadline is:

```text
launch time + registered expected wall clock + max(30 minutes, 25% of expected)
```

Record it in the monitor prompt. A contract without an expected wall clock is
not launch-ready.

Create the final run root and authoritative `runner_status.txt` at launch.
Stage raw and result payloads inside that root. Publish a file or result
directory with an atomic replace/rename inside the root, then atomically publish
the terminal status that references it. Never rename an external staging root
into place after completion.

Use the registered cloud scheduler for cloud work. Treat the server as
available until an actual connection failure. Put large output on the data disk
and long commands in the registered background runner.

## Terra Monitor Subagent

After the live status file exists, spawn exactly one depth-one child per run:

```text
task_name: monitor_<normalized-run-id>
fork_turns: none
model: gpt-5.6-terra
reasoning_effort: medium
```

Give the child only the absolute run root and status path, registered terminal
spelling (`complete` or `completed`, plus `failed`), payload keys, monitor
deadline, terminal schema, and read-only/no-science boundary.

The child runs `scripts/wait_runner_status.ps1`. The helper performs one initial
read and then waits on file events; it does not sleep or poll. The child may
resume a yielded helper with the process-wait tool. It reads no result, stderr,
or progress file, changes no file, and never restarts or interprets the run.

Every existing status must parse completely. `running` is the only nonterminal
state; terminal states are the registered `complete`/`completed` and `failed`.
Every state contains `updated` and `phase`. Validate `run_root`, `run_id`, and
terminal payload containment when present. Malformed, missing, unknown, or
escaping data is an immediate actionable monitor error.

The child returns exactly one final payload; the subagent runtime delivers it
to `/root` automatically:

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

Do not additionally send a collaboration message. Do not create a monitor
conversation, heartbeat, automation, dashboard, cross-thread relay, or monitor
state file.

The controller may keep at most one `wait_agent` call active for this child. If
it returns before the registered monitor deadline while the child remains
active, wait on the same child again without an intervening status read, child
read, sleep, poll, or replacement. At the deadline, perform one direct
authority/status inspection. If the run is not terminal, stop waiting and close
the lifecycle as `BLOCKED_MONITOR_TIMEOUT`; do not spawn or dispatch another
monitor. A user-requested progress read is a separate one-time controller
inspection and does not replace the child.

## Failure Classification and Retry Limit

Read only the status authority, the direct error needed to locate the first
failed boundary, and at most one comparator artifact. Distinguish launch,
collector, training, analyzer, packaging, monitor, invalid implementation, and
valid scientific failure.

State one falsifiable operational cause and run at most one diagnostic. The same
root cause receives at most one repair and one retry. If it recurs, return
`BLOCKED_REPEATED_OPERATIONAL_FAILURE` to the controller; do not continue a
repair loop. A materially different direct error may be classified separately.

Use the nearest known-good runner/configuration and change only the failed
stage. Do not retrain for analyzer-only repair. Do not change budget, seed,
reward, model, threshold, estimand, or placement as an operational repair, and
do not rescue a retired scientific line.
