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

Register the smallest authoritative progress sources exposed by the runner and
the exact fields that matter for this experiment. Prefer one per-arm status
JSON with completed/total steps and updates, plus already-terminal arm metrics.
If no online metric exists, record `unavailable`; never infer it by scanning
logs, TensorBoard events, checkpoints, stdout, or stderr.

Create the final run root and authoritative `runner_status.txt` at launch.
Stage raw and result payloads inside that root. Publish a file or result
directory with an atomic replace/rename inside the root, then atomically publish
the terminal status that references it. Never rename an external staging root
into place after completion.

Use the registered cloud scheduler for cloud work. Treat the server as
available until an actual connection failure. Put large output on the data disk
and long commands in the registered background runner.

## Persistent Luna Monitor Task

After the live status file exists, bind the run to the one task and one
heartbeat automation registered in `references/monitor-task.json`. The task is
created once with:

```text
model: gpt-5.6-luna
thinking: medium
workspace: C:\project\HMASD
```

Do not create a new monitor task or automation per run. Only one run may be
bound at a time. Immediately before binding, use `$hmasd-task-router` to resolve
both the registered monitor and the active controller. Their live routes must
match their registry mirrors. Update the existing automation by its registered
ID, target it at the exact monitor thread, set it `ACTIVE`, and verify both the
status and target. This automation update is the assignment; do not also send a
duplicate assignment message.

The automation prompt contains only its automation ID, the absolute run root
and status path, the registered progress paths and fields, registered terminal
spelling (`complete` or `completed`, plus `failed`), payload keys, monitor
deadline, terminal schema, the controller registry mirror, and the
read-only/no-science boundary. It requires the monitor to read
`$hmasd-task-router` before any terminal relay.

Each heartbeat starts one bounded monitor turn. That turn reads
`runner_status.txt` exactly once and each explicitly registered progress source
at most once. It does not start a watcher, sleep, poll, scan other artifacts,
change experiment files, restart the run, or interpret science. Every running
tick writes one concise `MONITOR_PROGRESS` entry in the dedicated monitor task
with observation time, phase, per-arm completed/total steps and updates,
percent complete, elapsed time, a clearly labelled straight-line ETA when the
available counters support it, and the registered key metrics or `unavailable`.
It sends no running update to the controller and ends with `MONITOR_RUNNING`;
the next heartbeat is the only continuation mechanism. A Codex final answer is
never treated as a live background waiter.

Every existing status must parse completely. `running` is the only nonterminal
state; terminal states are the registered `complete`/`completed` and `failed`.
Every state contains `updated` and `phase`. Validate `run_root`, `run_id`, and
terminal payload containment when present. Malformed, missing, unknown, or
escaping data is an immediate actionable monitor error.

At terminal state, malformed status, or deadline, the monitor first updates its
registered automation to `PAUSED` and verifies that state. Only after the pause
is confirmed does it resolve the controller's live route again and send exactly
one final payload through `$hmasd-task-router`:

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

The terminal send must include the freshly resolved controller `model` and
`thinking`; omission is forbidden. Do not send an additional message or create
a second heartbeat, automation, dashboard, replacement monitor, or monitor
state file. If pausing cannot be confirmed, do not relay a terminal payload;
leave the automation active so the next bounded tick can retry the pause.

On `complete`, the monitor may read the contained result once to display only
the terminal status and the exact registered key fields in its own task. The
controller relay still carries the result path as authority; the monitor does
not choose a branch or add scientific interpretation.

The controller does not poll or sleep while the monitor owns the run. The
heartbeat tick itself applies the deadline and relays `TIMEOUT` after first
pausing. If no relay exists after the deadline plus one heartbeat interval, the
controller performs one direct automation/status inspection. A user-requested
progress read is a separate one-time controller inspection and does not replace
the monitor.

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
