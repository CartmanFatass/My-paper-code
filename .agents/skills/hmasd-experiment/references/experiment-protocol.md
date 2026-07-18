# HMASD Experiment Protocol

## Launch Boundary

Confirm the exact commit, branch, runner, configuration, seeds, environment and
optimizer budgets, output root, expected wall clock, and status authority.
Generate the run timestamp once at launch. Dry runs use `DRY_RUN`.

Use the shared scheduler for cloud work. Treat the server as available until a
real connection failure. Put large outputs on the data disk and long commands
in the registered background runner.

## Terra Monitor Subagent

Spawn the monitor only after the runner has created the exact registered status
file. Use one child per run, depth one, `gpt-5.6-terra`, medium reasoning, and
`fork_turns=none`. A task name derived from the run ID is the uniqueness key;
do not create a second child for the same run.

The child receives only:

- absolute run root and status path;
- the registered terminal spelling `complete` or `completed`, plus `failed`;
- the terminal payload keys `result_path` and `error_path`/`error`;
- the exact terminal message schema;
- the read-only and no-scientific-interpretation boundary.

The child starts `.agents/skills/hmasd-experiment/scripts/wait_runner_status.ps1`.
That helper performs an initial read and then waits on file create/change/rename
events; it does not sleep or poll. A yielded helper process is owned by the
child, which may resume that process with the process-wait tool. The controller
does not wait on it.

On terminal status, require:

- `state` is exactly `complete`, `completed`, or `failed`;
- `updated` and `phase` are present;
- `run_root`, when present, resolves to the frozen run root;
- the selected result/error path, when present, remains under the run root.

The child returns one `EXPERIMENT_MONITOR` final payload. The subagent runtime
delivers it to `/root` without model or reasoning fields, so it cannot select or
exchange task models. Do not also call `collaboration.send_message`; that would
duplicate delivery. The payload is a notification, not lifecycle authority;
`runner_status.txt` remains authoritative.

The child sends `ACTIONABLE_ERROR` only when the watcher fails, the status is
malformed, a frozen identity/path check fails, or a terminal state lacks its
registered payload. It does not report ordinary running silence. It does not
read progress CSVs unless the user separately requests one progress report.

There is no monitor conversation, heartbeat, automation, cross-thread send,
thread identity check, controller polling, or monitor state machine. Historical
monitor artifacts remain evidence for their runs but are not inputs to a new
monitor.

## Failure Classification

The controller reads only the status source and direct error needed to locate
the first failed boundary. Distinguish operational failure, invalid
implementation, analyzer or monitor failure, and valid scientific FAIL. Use
the nearest known-good runner/configuration with only the failed stage changed.
Inspect at most the authority, direct error, and one comparator artifact; state
one falsifiable cause and run at most one diagnostic.

Do not change budget, seed, reward, model, threshold, or estimand as an
operational repair. Do not rescue a retired line.
