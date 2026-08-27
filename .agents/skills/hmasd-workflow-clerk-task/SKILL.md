---
name: hmasd-workflow-clerk-task
description: Use when the top-level HMASD Workflow-Clerk task receives a delegation, RETURN, Portfolio action, participant stop, retry event, or user routing request.
---

# HMASD Workflow-Clerk Task

Read `.codex/prompts/hmasd-workflow-clerk.md` and
`hmasd-operations-manual` completely before handling the event.

Use `scripts/hmasd_session_envelope.py` v2 `read-message` for each exact
one-line input. For every outbound `assignment` or `control-notice`, first run
that subcommand's `--help`. Prepare only the body JSON, run the CLI, then call
`send_message_to_thread` once with
`output.recipient_thread_id` and exactly the one line in `output.message`.

Before authoring a reanchor, run
`scripts/hmasd_control_release.py inspect --help` and bind the published
release selected by the role prompt.
