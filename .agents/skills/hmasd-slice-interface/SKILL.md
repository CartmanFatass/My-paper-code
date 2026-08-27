---
name: hmasd-slice-interface
description: Use when a top-level HMASD Root, Portfolio, EM/, or CM/ task receives an exact v2 message or completes a bounded session slice.
---

# HMASD Slice Interface

Read the current task's role prompt before using this transport edge.

For intake, run
`scripts/hmasd_session_envelope.py read-message --help`, then pass the exact
native one-line input. Use the validated envelope addressed to the current
task. For a validated `REANCHOR`, run
`scripts/hmasd_control_release.py verify --help` and verify its expected
release before role work resumes.

For outbound, run the applicable `scripts/hmasd_session_envelope.py` v2
subcommand's `--help`. Prepare only the body JSON, run the CLI, then call
`send_message_to_thread` once with `output.recipient_thread_id` and exactly the
one line in `output.message`.
