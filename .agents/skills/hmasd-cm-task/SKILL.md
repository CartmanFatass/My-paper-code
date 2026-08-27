---
name: hmasd-cm-task
description: Use when a top-level HMASD CM direction task receives a bounded implementation, test, integration, prepare, execution, or technical-repair slice.
---

# HMASD CM Task

Read the validated assignment, then load `.codex/prompts/hmasd-cm.md`. Own only
the named direction's engineering outcome, exact paths, technical evidence,
engineering-state writes, and eligible result command. Implementer, Reviewer,
Verifier, Scout, and Operator return to CM; CM alone integrates their evidence.

Use `hmasd-slice-interface` for intake and return. Choose one RETURN status:

- `REQUEST_EM` for a genuine scientific semantic question or interpretation.
- `REQUEST_CM` for the next exact engineering slice in the same direction.
- `REQUEST_PORTFOLIO` for a genuine cross-direction investment decision.
- `REQUEST_USER` for an exact material choice, shared-core semantic change, or
  user-owned Effect.
- scoped `FAILED` for a technical failure that preserves unaffected work.
- `DONE` only when this bounded assignment has no next responsibility.

`next_objective` states the next bounded outcome and evidence need; it does not
choose or contact the next task.

Run `scripts/hmasd_session_envelope.py return`, then use
`send_message_to_thread` with exactly `output.recipient_thread_id` and
`output.message`. Every leaf, including the unique Operator, returns only to
CM. No leaf receives a Workflow-Clerk task ID or sends across sessions.
