---
name: hmasd-cm-task
description: Use when a top-level HMASD CM direction task receives a bounded implementation, test, integration, prepare, execution, or technical-repair slice.
---

# HMASD CM Task

Read `.codex/prompts/hmasd-cm.md` completely before acting. Use
`hmasd-slice-interface` for the exact v2 intake.

For one bounded diff, the top-level CM may invoke `code-review`: exactly two
direct `hmasd-reviewer` leaves perform the Standards axis and Spec axis.

After writing the accepted engineering state, run
`scripts/hmasd_session_envelope.py return --help`. Prepare only the body JSON,
run the CLI, then call `send_message_to_thread` once with
`output.recipient_thread_id` and exactly the one line in `output.message`.
