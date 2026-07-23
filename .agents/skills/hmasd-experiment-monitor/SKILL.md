---
name: hmasd-experiment-monitor
description: Observe one already-authorized HMASD experiment run in the registered persistent Codex Spark monitor session. Use for assigning a run, bounded progress checks, ETA-based heartbeat adjustment, terminal evidence collection, or monitor-error reporting. Do not use to launch, repair, extend, interpret, or authorize experiments.
---

# HMASD Experiment Monitor

Operate only as the registered `experiment_monitor` session. The Controller
assigns a named, already-authorized run; this Skill grants no experiment,
scientific, Git, or file-write authority.

## Assignment

Accept assignments beginning with `$hmasd-experiment-monitor`. Before accepting
`MONITOR_ASSIGNMENT`, confirm that it names the `run_id`,
`run_root`, authoritative status/progress/result paths, and the Controller's
registered role. Inspect only that run. Do not modify repository files,
launch/restart a process, repair a failure, extend a budget, or interpret
scientific meaning.

## Observation and heartbeat

Make one bounded status read per wake-up. Report meaningful progress, phase,
and the main available quantity (update/step, shard generation, or evaluation
cell count). Estimate ETA from observed completed work and the assigned
contract. Own the heartbeat: create it after assignment, never use a cadence
shorter than 10 minutes, and retarget it only when ETA or phase changes
materially. Do not poll with sleeps or open/close unrelated tasks.

At a terminal state or monitor error, delete the heartbeat before delivery.

## Recovery before monitor error

No progress delta, unavailable ETA, a transient read failure, missing path,
route lookup failure or delivery failure is not immediately `MONITOR_ERROR`.
Keep the same run assignment active and perform bounded self-recovery within the
read-only authority: inspect the direct error, revalidate the exact assigned
paths and run state, retry after an observable state change or scheduled wake,
and re-resolve the Controller route before delivery. Never launch, restart,
repair or mutate the experiment, and never switch to another task or route.

Report each attempt in commentary:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed observation or delivery>
action=<read-only diagnostic or recovery action>
outcome=<observed result>
```

Only emit terminal `MONITOR_ERROR` when no safe read-only recovery remains. The
payload then includes `recovery_attempts=<count>`, a concise attempt summary and
`recovery_exhausted=true`.

## Terminal delivery

Resolve the active Controller with
`hmasd-dispatch-task/scripts/resolve_task_route.ps1 -Role controller`
immediately before delivery. Require nonempty `hostId`, `threadId`, `model`,
and `thinking`; send exactly one real cross-thread message with those values
copied unchanged. Never guess a target, reuse stale metadata, change model or
thinking, or start a successor.

```text
EXPERIMENT_MONITOR
role=experiment_monitor
terminal=<COMPLETE|FAILED|MONITOR_ERROR>
handoff_id=<run-id>:<terminal>:<timestamp>
run=<run-id>
state=<observed state>
phase=<observed phase>
status=<authoritative status path>
payload=<result or failure path>
reason=<direct reason or none>
recovery_attempts=<count or 0>
recovery_exhausted=<true only for MONITOR_ERROR; otherwise false>
```

If route resolution or delivery fails, apply the recovery contract and retry
only the same payload to the newly re-resolved registered Controller after
proving no accepted delivery exists. If recovery is exhausted, return the same
payload locally with `terminal=MONITOR_ERROR`, the direct error and the recovery
summary. Do not retry through another task.
