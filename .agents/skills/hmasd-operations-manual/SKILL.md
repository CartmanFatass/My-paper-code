---
name: hmasd-operations-manual
description: Use when the HMASD Workflow-Clerk handles an incoming task message, participant completion, stopped task, resource wait, Portfolio action, or direction liveness event.
---

# HMASD Operations Manual

Read `.codex/prompts/hmasd-workflow-clerk.md` completely. That prompt is the
topology, routing, and recovery authority.

At ingress, run `scripts/hmasd_session_envelope.py read-message --help`, then
classify every exact native one-line input separately. For a validated
`REANCHOR`, run `scripts/hmasd_control_release.py verify --help` and verify the
expected release. Execute the prompt-selected operation. Before each outbound
subcommand, run its `--help`, prepare only the body JSON, and send exactly
`output.message` to `output.recipient_thread_id`.
