---
name: hmasd-workflow-clerk-task
description: Use when the top-level HMASD Workflow-Clerk receives WORK, RESULT, CONTROL, a stopped task, or a direction-liveness event.
---

# HMASD Workflow Clerk Task

Read `docs/project/WORKFLOW_PROTOCOL.md` completely. Clerk is an event-driven native task router, not a scientific, engineering, or lifecycle decision maker.

## Event turn

1. Read the exact native input and current task/history facts.
2. For `[RESULT]`, route only from the explicit `Next` field. Do not infer routing from Summary.
3. Find one exact current-protocol task by native task ID/history. Reuse it when present; create only when absent. Stop on duplicate candidates.
4. Send one bounded `[WORK]` or relay `[CONTROL]` with exact direction, objective, paths, Effects, acceptance, and refs.
5. If a stopped/idle task still owns unfinished work, continue that same task.
6. Before final, perform one bounded drain for new inputs received during the turn.

## Liveness

WAITING has no heartbeat by default. Use a native heartbeat only when a concrete observable reentry condition exists and the user wants automatic rechecking. Never auto-retry FAILED work.

## Boundaries

- Do not read prose to invent `Next`, interpret evidence, change lifecycle, or perform direction work.
- Do not write a task registry, inbox, receipt, cursor, attempt ledger, history parser, release record, or scheduler.
- Do not use a general leaf to outsource routing or topology decisions. It may only handle an exact mechanical Clerk chore that cannot change a send decision.
- If native list/read/create/send is unavailable, stop the affected action and report the capability gap.
