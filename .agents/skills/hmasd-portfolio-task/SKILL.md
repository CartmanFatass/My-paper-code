---
name: hmasd-portfolio-task
description: Use when the top-level HMASD Portfolio task receives a bounded cross-direction priority, investment, lifecycle, fusion, separation, or new-direction decision.
---

# HMASD Portfolio Task

Read `.codex/prompts/hmasd-portfolio.md` completely before acting. Use
`hmasd-slice-interface` for the exact v2 intake.

After writing the accepted Portfolio state, run
`scripts/hmasd_session_envelope.py portfolio-return --help`. Prepare only the
body JSON, run the CLI, then call `send_message_to_thread` once with
`output.recipient_thread_id` and exactly the one line in `output.message`.
