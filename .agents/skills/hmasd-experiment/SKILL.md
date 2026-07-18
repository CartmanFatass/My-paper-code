---
name: hmasd-experiment
description: Use only when an authorized HMASD action creates or mutates an experiment contract, package, launch, persistent monitor, failed runtime stage, analysis-only repair, or terminal closure. Do not use for a one-time status read, interpretation of an already closed result, or read-only failure location. Completed code never implies training authority.
---

# HMASD Experiment

Read `memory/CURRENT_WORK.md`, `memory/ALGORITHM_PRINCIPLES.md`, and the single
owning row in `memory/ExpRecord.md`. Read `references/experiment-protocol.md`
before packaging, launching, monitoring, or repairing a run.

## Establish Authority

Name the requested class precisely: code test, engineering smoke test, formal
experiment, or scale training. Refuse silent expansion from one class to the
next.

Before a conclusion-bearing launch, require a contract naming the causal edge,
comparator, metrics and thresholds, nulls, seeds, environment steps, optimizer
updates, outcome branches, prohibited changes, expected wall clock, and
authoritative status source.

## Package and Launch

Use the existing parallel topology when compatible. Formal or long work uses
CUDA and defaults to the cloud; an explicit user authorization and the owning
experiment contract may place a bounded run on local CUDA. Never migrate the
placement silently or fall back to CPU or serial execution. Make one stable
pre-launch Git boundary and put all output under one timestamped
`logs/<run-id>/` root on the registered storage root.

Implementation completion alone never launches a run.

## Monitor One Run

Create the persistent project-local monitor conversation as `Luna High`, then
freeze that model for its lifetime. At activation, initialize
`logs/<run-id>/monitor_state.json` only through
`scripts/monitor_state.ps1`; it is the durable handoff authority. Reuse that one monitor conversation and one
heartbeat schedule targeting it; never change the model of an existing monitor
and never attach model/thinking overrides to heartbeat updates. At activation,
freeze the exact controller thread,
monitor thread, automation id and run id in the prompt. Each wake performs one
bounded read of the authoritative status. The monitor is read-only with respect
to code, scientific artifacts and process state: it never edits code/results,
tests, restarts, or interprets science. Its only allowed writes are the exact
run's `monitor_state.json` through the state script and the registered
heartbeat's cadence, prompt and status. Routine dashboards remain in that
conversation.

Never use unguarded cross-thread messaging for terminal relay. The frozen
controller host/thread/model/effort recorded in `monitor_state.json` is the
routing authority; do not infer settings from the sender or conversation prose.
Use `codex_app__list_threads` to require that exact target and an idle status,
then send the guarded direct format in `references/experiment-protocol.md`. If
the target is running or absent, leave the heartbeat active. Record the returned
controller turn ID confirmed by `codex_app__read_thread`, then pause the exact
automation and confirm `PAUSED` through an update plus view call and its exact
`automation.toml`. Advance monitor state only from those durable observations.
A closed `handoff_id` makes duplicate delivery a no-op. Never use a message to
repair a registry mismatch, and never read or interpret the result in the monitor.

The required call shape is
`send_message_to_thread({hostId, threadId, model: target_model, thinking:
target_effort, prompt})`; none of the four routing/settings fields may be
omitted.

Initialize monitor state only after the heartbeat is active; the script freezes
its config path, status and `updated_at` as the activation baseline. Relay with
`-ReadThreadReceipt
"host=<controller-host>;thread=<controller-thread>;turn=<turn-uuid>;handoff=<handoff-id>"`.
The pause transition must observe a newer `automation.toml` update occurring
after that relay. A closed state validates its stored receipt and is unaffected
when the same heartbeat is later reactivated for another run.

## Diagnose and Close

Classify a terminal problem before changing anything. Fix and rerun only the
failed launcher, collector, training, analyzer, packaging, or monitor stage.
Never retrain when analysis-only repair suffices.

Experiments primarily judge algorithm capability and stability. If observed
wall time becomes grossly inconsistent with the expected range, the controller
may stop the run and repair the engineering path directly. This is runtime
judgment, not a performance gate, new threshold, extra smoke, or authorization
to change the registered algorithm or experiment contract.

On a valid terminal result, require monitor state `CLOSED`, read the registered result once, apply the existing
outcome branch without rescue, update the owning experiment record, and create
one result/disposition Git boundary. A negative scientific result remains
binding.
