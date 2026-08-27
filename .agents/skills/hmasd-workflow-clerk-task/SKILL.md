---
name: hmasd-workflow-clerk-task
description: Use when the top-level HMASD Workflow-Clerk task receives a delegation, RETURN, Portfolio action, participant stop, retry event, or user routing request.
---

# HMASD Workflow-Clerk Task

Load `hmasd-operations-manual` and
`.codex/prompts/hmasd-workflow-clerk.md`. Clerk alone owns the temporary
topology view and cross-session coordination; it does not perform Portfolio,
EM, CM, or Operator work.

At event ingress, treat every exact locator delegation in the current native
turn as an independent input. Run `hmasd_session_envelope.py read-message` on
each exact `input`; preceding leaf prose never changes how a later locator is
classified. A non-envelope message from another task or a leaf does not route
or change liveness. Direct user conversation remains user input.

Build fresh native observations containing only task `id`, `name`, native
`status`, exactly one outstanding current delivered locator per direction, and exact observed
pause/heartbeat/experiment facts. Envelope files are not delivery receipts.
Run `hmasd_session_envelope.py liveness` to write
`.codex/runtime/clerk-liveness.json`. Execute every machine-emitted action:
`HANDLE_RETURN` enters through `read-message`; `REDELIVER_ASSIGNMENT` resends
the exact existing message to its exact thread. Before final, refresh once and
run liveness again so a locator injected during the turn is not lost. Do not
hand-author a stage, reason, recovery action or Dashboard row.
An ASSIGNMENT clears when its correlated RETURN is visibly delivered; a RETURN
clears when its next ASSIGNMENT or terminal/user summary is visibly delivered.
Do not retain a cleared RETURN across heartbeats.

At bootstrap, verify the five-minute `hmasd-clerk-liveness` heartbeat targets
this Clerk task. Recreate that same heartbeat here if absent; never attach it
to Root.

For every validated event, select the recipient from the direction-neutral
semantic table, create the recipient's bounded body, run `assignment`, and
send exactly `output.message` to `output.recipient_thread_id`. Never forward a
leaf report, raw JSON, summary, or locator plus commentary. Preserve each
direction's own refs and `next_objective`; do not copy semantics between
directions.

Clerk never delegates to a leaf. If a top-level participant stops without its
correlated return, continue the same participant and redeliver the existing
locator. Do not create a duplicate manager or treat leaf prose as completion.
