---
name: hmasd-result-run
description: Use when one HMASD result-bearing train, evaluate, or analyze command must be owned through terminal observation.
---

# HMASD Result Run

One Experiment Operator leaf owns one exact command from launch through terminal
observation. Freeze direction/run/assignment IDs, argv, native cwd, code SHA,
parameters, output paths, activity predicate, resource estimate, and manifest
revision. Preflight memory; an unsafe plan is reduced, batched, or sharded.

For a command over 7200 seconds, make one performance-reasonableness attempt
and return the frozen user-decision request. Launch one foreground
`scripts/hmasd_run.py execute`; the same Operator retains its yielded session
until terminal. Check duplicate manifest/process identity first.

Return the typed Effect ref with `kind: run_manifest`, its exact `resource_id`,
and `operation`, plus terminal manifest/artifacts. An unproven identity is
`UNKNOWN`: observe/reconcile it; never signal or relaunch blindly. Do not
reinterpret metrics or start a successor.
