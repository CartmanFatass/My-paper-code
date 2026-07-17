---
name: hmasd-experiment
description: Prepare, launch, create or change persistent monitoring for, repair, or formally close an authorized HMASD smoke test, formal experiment, scale run, or analysis-only rerun. Use for real experiment lifecycle operations, not for a one-time status/result read, result interpretation, simple monitor diagnosis, or ordinary failure-location check. Do not infer training authority from completed code.
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
CUDA and the cloud; local GPU is for small diagnostics. Do not fall back to CPU
or serial execution. Make one stable pre-launch Git boundary and put all output
under one timestamped `logs/<run-id>/` root on the data disk.

Implementation completion alone never launches a run.

## Monitor One Run

Reuse one persistent project-local monitor conversation and one heartbeat
schedule targeting it. Each wake performs one bounded read of the authoritative
status. The monitor remains read-only and never edits, tests, restarts, or
interprets science. Routine dashboards remain in that conversation.

Never use cross-thread messaging for terminal relay: the desktop runtime has
been observed applying each sender's model settings to the receiver. Instead,
on completion, explicit failure, or monitor error, the monitor retargets the
same heartbeat to the active controller with a one-minute terminal-handoff
prompt and verifies the new target. It does not read the result or alter either
conversation's model. On the next wake the controller first pauses the same
schedule and verifies `PAUSED`, then reads the result or direct error once and
applies the registered branch. Text describing either automation mutation is
never success evidence.

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
