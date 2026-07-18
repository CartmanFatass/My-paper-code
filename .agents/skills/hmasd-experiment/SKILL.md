---
name: hmasd-experiment
description: Use only when an authorized HMASD action creates or mutates an experiment contract, package, launch, Terra Medium monitor subagent, failed runtime stage, analysis-only repair, or terminal closure. Do not use for a one-time status read, interpretation of an already closed result, or read-only failure location. Completed code never implies training authority.
---

# HMASD Experiment

Read `memory/CURRENT_WORK.md`, `memory/ALGORITHM_PRINCIPLES.md`, the owning row
in `memory/ExpRecord.md`, and `references/experiment-protocol.md`.

## Authority and Launch

Name the requested class precisely: code test, engineering smoke test, formal
experiment, or scale training. Do not expand one class into another.

Before a conclusion-bearing launch, require a contract naming the causal edge,
comparator, metrics and thresholds, nulls, seeds, environment steps, optimizer
updates, outcome branches, prohibited changes, expected wall clock, placement,
and authoritative status source. Use the registered parallel CUDA topology and
one timestamped `logs/<run-id>/` final run root. Create that final run root and
its live `runner_status.txt` at launch. Keep raw and result payload staging
inside the final run root; never publish the run by renaming an external staging
root. Publish a completed payload with an atomic file or result-directory rename
inside that root, then atomically update the status to its terminal state. Do not
fall back to CPU or serial execution, change placement, or launch merely because
implementation completed.

## Monitor with One Subagent

After launch has created the final run root and live registered
`runner_status.txt`, create exactly one depth-one monitor with
`collaboration.spawn_agent`:

```text
task_name: monitor_<normalized-run-id>
fork_turns: none
model: gpt-5.6-terra
reasoning_effort: medium
```

The prompt freezes the run root, status path, and its contract's terminal state
spelling (`complete` or `completed`, plus `failed`). The
monitor is read-only. It runs
`scripts/wait_runner_status.ps1`, remains active until a terminal status or an
actionable monitoring error, and never reads result content or stderr, edits a
file, restarts work, interprets science, or changes the experiment.

Only an absent status file is ordinary silence. For every existing status, the
only nonterminal state is `running`; terminal state is the contract's registered
`complete` or `completed`, plus `failed`. Require `updated` and `phase` in every
state and continue validating `run_root`, `run_id`, and terminal payload
containment. A malformed line, missing state or required field, or unknown state
is an immediate actionable monitoring error.

The monitor returns exactly one terminal final answer, which the subagent
runtime delivers to `/root`, then exits:

```text
EXPERIMENT_MONITOR
terminal=<COMPLETE|COMPLETED|FAILED|ACTIONABLE_ERROR>
handoff_id=<run-id>:<state>:<status-updated-at>
run=<run-id>
state=<state>
phase=<phase>
status=<registered status path>
payload=<result path, direct-error path, or none>
reason=<single actionable line or none>
```

Do not create a monitor conversation, automation, heartbeat, dashboard, or
`monitor_state.json`. Do not use `create_thread`, `send_message_to_thread`,
`list_threads`, `read_thread`, `collaboration.send_message`, `Start-Sleep`, or
model/thinking fields in a message. An additional send would duplicate the
automatic final delivery. The model is fixed only at subagent creation. While it is active, the
controller may use a native mailbox wait for terminal delivery. Keep at most one
active `wait_agent` for the same child at a time. If a native wait times out while
the child remains active, call `wait_agent` again only for that same child. Do
not poll the status, read the status or child between waits, sleep, or spawn a
duplicate monitor. A mailbox wait is not status polling. A user-requested
progress read is a separate one-time controller inspection and does not replace
the monitor.

## Diagnose and Close

Classify a terminal problem before changing anything. Fix and rerun only the
failed launcher, collector, training, analyzer, packaging, or monitor stage.
Never retrain when analysis-only repair suffices.

If observed wall time becomes grossly inconsistent with the registered range,
the controller may stop the run and repair the engineering path directly. This
does not authorize a performance gate or algorithm change.

After the subagent relay, the controller verifies the registered status once,
reads the registered result or direct error once, applies the existing outcome
branch without rescue, updates the owning experiment record, and creates one
result/disposition Git boundary. A negative scientific result remains binding.
