---
name: hmasd-operations-manual
description: Use when the HMASD Workflow-Clerk handles an incoming task message, participant completion, stopped task, resource wait, Portfolio action, or direction liveness event.
---

# HMASD Operations Manual

Workflow-Clerk owns coordination. Load
`.codex/prompts/hmasd-workflow-clerk.md` and apply its direction-neutral
semantic table; no other session reconstructs this manual.

## Event entry

Refresh the temporary topology snapshot from Codex task list/read, Portfolio
registry authority, and native automation state. Do not persist the join.

For a native delegation, pass its exact `input` to
`hmasd_session_envelope.py read-message`. A validated `ASSIGNMENT`, `RETURN`,
or `PORTFOLIO_RETURN` is an event. A non-envelope message from a top-level task
or leaf is diagnostic chatter: it does not route, complete, pause, or create
work. If the participant owes a return, redeliver its existing assignment
locator to the same top-level task; never ask or accept a leaf to repair the
handoff. Direct user conversation and user override remain valid user input.

After ingress and once again before final, provide `hmasd_session_envelope.py
liveness` with fresh native task/history observations. Include only locators
visible in recipient history; envelope files are not delivery receipts. The program emits the
complete direction table and zero or more recovery actions and refreshes
`.codex/runtime/clerk-liveness.json` for the read-only Dashboard. Process every
emitted action in that pass. Never replace the machine result with a prose
classification; a second pass is the bounded drain for a locator injected
while another event was being handled.

## Direction-neutral routing

| Validated tag | Action |
| --- | --- |
| `REQUEST_EM` | Same direction's existing EM |
| `REQUEST_CM` | Same direction's existing CM |
| `REQUEST_PORTFOLIO` | Single Portfolio task |
| `REQUEST_USER` | Root/user with the exact material question |
| scoped `FAILED` | Same responsible owner for bounded repair |
| `PORTFOLIO_RETURN` | Validate all actions, then dispatch each independent action |
| `DONE` | No send only when the durable lifecycle permits it |

Every outgoing participant assignment is built by the envelope CLI. Send only
`output.message` to `output.recipient_thread_id`. The assignment objective is
the recipient's next bounded outcome; it does not copy unrelated direction
prose. End the event turn after all independent ready sends.
