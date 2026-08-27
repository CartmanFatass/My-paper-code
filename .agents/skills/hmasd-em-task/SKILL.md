---
name: hmasd-em-task
description: Use when a top-level HMASD EM direction task receives a bounded scientific question, evidence interpretation, mechanism, comparator, claim, or discriminator slice.
---

# HMASD EM Task

Read `.codex/prompts/hmasd-em.md` completely before acting. Use
`hmasd-slice-interface` for the exact v2 intake.

EM scientific review must never invoke `code-review`; use Research Critic and
Agentify instead.

After writing the accepted scientific state, run
`scripts/hmasd_session_envelope.py return --help`. Prepare only the body JSON,
run the CLI, then call `send_message_to_thread` once with
`output.recipient_thread_id` and exactly the one line in `output.message`.
