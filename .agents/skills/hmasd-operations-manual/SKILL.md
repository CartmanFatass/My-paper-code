---
name: hmasd-operations-manual
description: Use when the HMASD Workflow-Clerk handles an incoming task message, participant completion, stopped task, resource wait, Portfolio action, or direction liveness event.
---

# HMASD Operations Manual

Read `docs/project/WORKFLOW_PROTOCOL.md` sections 1.1, 2, 3.1-3.3, 4.2-4.5,
5-7, and 12, plus `.codex/prompts/hmasd-workflow-clerk.md`. Run
`scripts/hmasd_session_envelope.py --help` and the applicable subcommand
`--help`; for a failed RETURN, include `failure-history --help`. Finish at the
Clerk prompt's section 6 final-drain boundary.
