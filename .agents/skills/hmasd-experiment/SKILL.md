---
name: hmasd-experiment
description: Prepare, launch, monitor, diagnose, or close an authorized HMASD smoke test, formal experiment, scale run, or analysis-only rerun. Use when an experiment contract and launch authority exist, or when a running job needs one persistent monitor, bounded failure diagnosis, or terminal result handling. Do not infer training authority from completed code.
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

Reuse one persistent project-local monitor conversation and one schedule
targeting it. Each wake performs one bounded read of the authoritative status.
The monitor remains read-only and never edits, tests, restarts, or interprets
science. Routine dashboards remain in the monitor conversation; notify the
controller only on completion, explicit failure, or monitor error.

## Diagnose and Close

Classify a terminal problem before changing anything. Fix and rerun only the
failed launcher, collector, training, analyzer, packaging, or monitor stage.
Never retrain when analysis-only repair suffices.

On a valid terminal result, read the registered result once, apply the existing
outcome branch without rescue, update the owning experiment record, and create
one result/disposition Git boundary. A negative scientific result remains
binding.
