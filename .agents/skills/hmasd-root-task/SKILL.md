---
name: hmasd-root-task
description: Use when the top-level HMASD Root task receives user control, a shared-core change, a task-identity conflict, a protocol question, or cross-direction Git integration.
---

# HMASD Root Task

Read `.codex/prompts/hmasd-root.md` completely before acting.

With `scripts/hmasd_session_envelope.py`, first run the outbound v2
`assignment` or `control-notice` subcommand's `--help`. Prepare only the body
JSON, run the CLI, then call
`send_message_to_thread` once with `output.recipient_thread_id` and exactly the
one line in `output.message`.

For a reanchor, first run `scripts/hmasd_control_release.py inspect --help` and
bind the published release selected by the role prompt.

Use `hmasd-slice-interface` for exact v2 intake.
