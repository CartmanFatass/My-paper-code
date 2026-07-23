---
name: hmasd-experiment-monitor
description: Observe one already-authorized HMASD experiment with bounded read-only polling, ETA reporting, heartbeat control, recovery, and exact terminal return.
---

# HMASD Experiment Monitor Procedure

## Contract boundary

Role contracts are normative. Read the root `AGENTS.md` and these relevant role
documents before operating:

- `.agents/roles/EXPERIMENT_MONITOR.md`
- `.agents/roles/CONTROLLER.md`

This Skill grants no authority. It contains only the mechanics for observing
and reporting one assigned run.

## Assignment intake

Accept only an assignment beginning with `$hmasd-experiment-monitor`. Before
accepting `MONITOR_ASSIGNMENT`, require:

- `run_id` and `run_root`;
- exact authoritative status, progress, and result or failure paths;
- mechanically defined terminal criteria and the authorized budget boundary;
- the reporting cadence or initial wake time; and
- the Project Manager return requirement, if any; Controller remains the local
  operator of this procedure.

Reject an incomplete or identity-ambiguous assignment without inspecting a
different run. Do not modify repository files.

## Bounded observation and ETA

On each assignment or scheduled wake-up:

1. Read only the assigned process state and exact assigned paths.
2. Capture observed time, state, phase, liveness, and the main progress quantity
   named by the assignment, such as update/step, shard generation, or evaluation
   cell count.
3. Compare with the preceding snapshot. Estimate ETA only from observed deltas
   and the assigned contract; otherwise report ETA as unavailable with the
   direct reason.
4. Send a status update only for meaningful progress, phase change, terminal
   state, failure signal, or a requested scheduled report.

Make one bounded status read per wake-up. Do not poll with blocking sleeps,
inspect unrelated runs, or open and close unrelated tasks.

## Heartbeat mechanics

Create one Controller-owned monitoring heartbeat after accepting the assignment. Never use a
cadence shorter than 10 minutes. Retarget it only when the ETA or phase changes
materially, and keep at most one heartbeat for the run.

Each heartbeat wakes the same assignment for one bounded observation; it does
not launch, restart, repair, extend, configure, or terminate a process. At a
terminal state or terminal monitor error, delete the heartbeat and confirm it
is absent before terminal return.

## Recovery before monitor error

No progress delta, unavailable ETA, a transient read failure, missing path, or
local return failure is immediately `MONITOR_ERROR`.
Keep the same assignment and perform bounded read-only recovery:

1. Inspect the direct error and latest observable run state.
2. Revalidate the exact assigned paths and run identity.
3. Retry only after an observable state change or scheduled wake, or use a
   materially distinct read-only check.
4. Revalidate the active Controller task and the exact assigned run identity.

Never switch runs, invent a cross-task route, or repeat an identical failed
action without changed state. Report every attempt:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed observation or delivery>
action=<read-only diagnostic or recovery action>
outcome=<observed result>
```

Emit terminal `MONITOR_ERROR` only when no safe read-only recovery remains. Its
payload includes the direct cause, `recovery_attempts=<count>`, a concise attempt
summary, and `recovery_exhausted=true`.

## Terminal return

Return the terminal payload locally to the active Controller task. This
procedure performs no cross-task send. If the assignment requires Project
Manager delivery, Controller uses `$hmasd-dispatch-task` afterward and copies
the payload unchanged; that dispatcher resolves the live target profile.

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

If local return fails, apply the recovery procedure. If recovery is exhausted,
return that payload with `terminal=MONITOR_ERROR`, the direct error, attempt
summary, and `recovery_exhausted=true`. Do not route through another task from
inside this procedure.
