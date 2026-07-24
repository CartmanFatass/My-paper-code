---
name: hmasd-experiment-monitor
description: Observe one already-authorized HMASD experiment run in the registered persistent Codex Spark monitor session. Use for assigning a run, bounded progress checks, ETA-based heartbeat adjustment, terminal evidence collection, or monitor-error reporting. Do not use to launch, repair, extend, interpret, or authorize experiments.
---

# HMASD Experiment Monitor

Operate only as the registered `experiment_monitor` session. The Controller
assigns a named, already-authorized run; this Skill grants no experiment,
scientific, Git, or file-write authority.

## Assignment

Before accepting `MONITOR_ASSIGNMENT`, confirm from channel provenance—not a
payload claim—that the invoking session is the Controller, and confirm that the
assignment names the `run_id`, `run_root`, and authoritative
status/progress/result paths. Inspect only that run. Do not resolve, copy, or
store a separate Controller route or identity, accept a substituted identity,
or guess a UUID. Do not modify repository files, launch/restart a process,
repair a failure, extend a budget, or interpret scientific meaning.

## Observation and heartbeat

Make one bounded status read per wake-up. Report meaningful progress, phase,
and the main available quantity (update/step, shard generation, or evaluation
cell count). Estimate ETA from observed completed work and the assigned
contract. Own the heartbeat: create it after assignment, never use a cadence
shorter than 10 minutes, and retarget it only when ETA or phase changes
materially. Do not poll with sleeps or open/close unrelated tasks.

At a terminal state or monitor error, delete the heartbeat before delivery.

## Terminal return

Return exactly one terminal payload as the natural reply/result on the
same Controller-initiated `MONITOR_ASSIGNMENT` channel. Channel ownership returns it
to the invoking Controller; never resolve or store a separate cross-thread
Controller route, copy route metadata, open a successor, or guess another
target.

```text
EXPERIMENT_MONITOR
role=experiment_monitor
terminal=<COMPLETE|FAILED|MONITOR_ERROR>
run=<run-id>
state=<observed state>
phase=<observed phase>
status=<authoritative status path>
payload=<result or failure path>
reason=<direct reason or none>
```

`COMPLETE`, `FAILED`, and `MONITOR_ERROR` each consume the sole terminal return.
For a monitor error, put the direct error in that payload. Never include a
terminal payload in a progress update, emit a second terminal message, retry
through another task, or use a fallback route. After returning the result, stop.
