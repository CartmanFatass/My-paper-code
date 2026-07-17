---
name: hmasd-experiment
description: Prepare, launch, create or change persistent monitoring for, repair, or formally close an authorized HMASD smoke test, formal experiment, scale run, or analysis-only rerun. Use for real experiment lifecycle operations, including terminal closure that pauses monitoring, applies the registered branch, and records the result boundary. Do not use for a one-time status read, reading or interpreting an already closed result, simple monitor diagnosis, or ordinary failure-location check. Do not infer training authority from completed code.
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
freeze that model for its lifetime. Reuse that one monitor conversation and one
heartbeat schedule targeting it; never change the model of an existing monitor
and never attach model/thinking overrides to heartbeat updates. At activation,
freeze the exact controller thread,
monitor thread, automation id and run id in the prompt. Each wake performs one
bounded read of the authoritative status. The monitor is read-only with respect
to the repository and run: it never edits, tests, restarts, or interprets
science. Its only allowed mutation is the registered heartbeat's cadence,
prompt and status. Routine dashboards remain in that conversation.

Never use unguarded cross-thread messaging for terminal relay: the desktop
runtime has been observed applying sender settings when target settings are
omitted. On completion, explicit failure, or monitor error, use the guarded
direct format in
`references/experiment-protocol.md`: resolve the controller's live model and
effort, supply them explicitly with host and thread ID, then verify they remain
unchanged. After confirmed delivery, pause the monitor heartbeat and verify
`PAUSED`. A stable `handoff_id` makes duplicate delivery a no-op. Never use a
message to repair a settings mismatch, and never read or interpret the result in
the monitor.

The required call shape is
`send_message_to_thread({hostId, threadId, model: target_model, thinking:
target_effort, prompt})`; none of the four routing/settings fields may be
omitted.

## Diagnose and Close

Classify a terminal problem before changing anything. Fix and rerun only the
failed launcher, collector, training, analyzer, packaging, or monitor stage.
Never retrain when analysis-only repair suffices.

Experiments primarily judge algorithm capability and stability. If observed
wall time becomes grossly inconsistent with the expected range, the controller
may stop the run and repair the engineering path directly. This is runtime
judgment, not a performance gate, new threshold, extra smoke, or authorization
to change the registered algorithm or experiment contract.

On a valid terminal result, read the registered result once, apply the existing
outcome branch without rescue, update the owning experiment record, and create
one result/disposition Git boundary. A negative scientific result remains
binding.
