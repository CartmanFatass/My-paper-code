---
name: hmasd-portfolio-task
description: Use when the top-level HMASD Portfolio task receives a bounded cross-direction priority, investment, lifecycle, fusion, separation, or new-direction decision.
---

# HMASD Portfolio Task

Read the validated assignment, then load
`.codex/prompts/hmasd-portfolio.md`. Work only on the cited cross-direction
decision and Portfolio-owned authority. Portfolio decides; it does not create,
contact, or wait for manager tasks.

Use `hmasd-slice-interface` for intake and return. After durable Portfolio and
registry writes, fill one `portfolio-return` body. Give every material
direction one action:

- `ACTIVE` + `REQUEST_EM`: next bounded scientific outcome.
- `ACTIVE` + `REQUEST_CM`: next bounded engineering outcome.
- `PARKED` + `REQUEST_USER`: exact user question and reactivation condition.
- `CLOSED` + `DONE`: durable terminal reason and no next work.
- `ACTIVE` + scoped `FAILED`: exact Portfolio/registry repair outcome.

Each action's `next_objective` describes that direction's next outcome and
uses only that direction's refs. It never names the recipient task or copies
another direction's semantics.

Run `scripts/hmasd_session_envelope.py portfolio-return`, then use
`send_message_to_thread` with exactly `output.recipient_thread_id` and
`output.message`. Leaves return only to Portfolio. No leaf sends a message to
Workflow-Clerk or another top-level task.
