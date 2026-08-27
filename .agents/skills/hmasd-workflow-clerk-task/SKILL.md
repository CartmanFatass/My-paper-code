---
name: hmasd-workflow-clerk-task
description: Use when the top-level HMASD Workflow-Clerk task receives a delegation, RETURN, Portfolio action, participant stop, retry event, or user routing request.
---

# HMASD Workflow-Clerk Task

Load `hmasd-operations-manual` and
`.codex/prompts/hmasd-workflow-clerk.md`. Clerk alone owns the temporary
topology view and cross-session coordination; it does not perform Portfolio,
EM, CM, or Operator work.

At event ingress, run `hmasd_session_envelope.py read-message` on the exact
native delegation `input`. A non-envelope message from another task or a leaf
does not route or change liveness. Direct user conversation remains user input.

For every validated event, select the recipient from the direction-neutral
semantic table, create the recipient's bounded body, run `assignment`, and
send exactly `output.message` to `output.recipient_thread_id`. Never forward a
leaf report, raw JSON, summary, or locator plus commentary. Preserve each
direction's own refs and `next_objective`; do not copy semantics between
directions.

Clerk never delegates to a leaf. If a top-level participant stops without its
correlated return, continue the same participant and redeliver the existing
locator. Do not create a duplicate manager or treat leaf prose as completion.
