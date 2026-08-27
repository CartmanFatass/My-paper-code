---
name: hmasd-em-task
description: Use when a top-level HMASD EM direction task receives a bounded scientific question, evidence interpretation, mechanism, comparator, claim, or discriminator slice.
---

# HMASD EM Task

Read the validated assignment, then load `.codex/prompts/hmasd-em.md`. Own only
the named direction's scientific outcome, authority, accepted interpretation,
and research-state writes. Internal scientific leaves return evidence to EM;
EM alone integrates and accepts it.

Use `hmasd-slice-interface` for intake and return. Choose one RETURN status:

- `REQUEST_CM` when the science card is complete and implementation,
  instrumentation, prepare, or execution is next.
- `REQUEST_EM` for another exact scientific question in the same direction.
- `REQUEST_PORTFOLIO` for a genuine cross-direction decision.
- `REQUEST_USER` for an exact material user choice.
- scoped `FAILED` for a scientific failure that preserves unaffected work.
- `DONE` only when this bounded assignment has no next responsibility.

`next_objective` states the next bounded outcome and evidence need; it does not
choose or contact the next task.

Run `scripts/hmasd_session_envelope.py return`, then use
`send_message_to_thread` with exactly `output.recipient_thread_id` and
`output.message`. Research leaves and provider transports return only to EM;
they never receive a Workflow-Clerk task ID or send across sessions.
