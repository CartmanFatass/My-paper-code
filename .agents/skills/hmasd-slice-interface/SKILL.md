---
name: hmasd-slice-interface
description: Use when a top-level HMASD Root, Portfolio, EM/, or CM/ task receives a session assignment, completes a slice, or prepares a cross-task handoff.
---

# HMASD Slice Interface

This is the transport edge for one top-level participant. It does not choose a
recipient or coordinate another task.

## Intake

Take the exact native delegation `input` value and run:

```text
python scripts/hmasd_session_envelope.py read-message --repo C:/Projects/HMASD --message <exact-input>
```

Act only when this returns a validated envelope addressed to the current task.
A non-envelope message from another task or a leaf is not work and does not
route anything. Direct conversation from the user remains ordinary user input.

## Outbound

Only the top-level task sends across sessions. A leaf returns only to its
spawning parent and is never given a recipient task ID.

The participant fills only the command's body JSON:

- Root uses `assignment` for one coordination objective to Workflow-Clerk.
- EM and CM use `return` with `DONE`, `REQUEST_EM`, `REQUEST_CM`,
  `REQUEST_PORTFOLIO`, `REQUEST_USER`, or scoped `FAILED`.
- Portfolio uses `portfolio-return`; each material direction gets one action
  with its own status and `next_objective`.

Run the applicable command, then call `send_message_to_thread` with exactly
`output.recipient_thread_id` and `output.message`. Do not send the body JSON,
summary, commentary, or a locator plus prose. `output.message` is the complete
cross-session message.

`next_objective` states the next bounded outcome, not the route. `DONE` means
the current assignment has no next responsibility. `FAILED` carries an exact
project/direction/feature/effect scope and preserves unaffected work.
