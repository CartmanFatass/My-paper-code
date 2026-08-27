---
name: hmasd-operations-manual
description: Use when the HMASD Workflow-Clerk handles an incoming task message, participant completion, stopped task, resource wait, Portfolio action, or direction liveness event.
---

# HMASD Operations Manual

`docs/project/WORKFLOW_PROTOCOL.md` is the sole topology, routing, state, and
recovery authority. Read sections 1.1, 2, 3.1-3.3, 4.2-4.5, 5-7, and 12, plus
`.codex/prompts/hmasd-workflow-clerk.md`.

Run `scripts/hmasd_session_envelope.py --help` and the applicable subcommand
`--help`. Use `read-message` for each exact native line. For retry handling,
run `failure-history --help` and use ordered validated RETURN locators to check
cumulative same-fingerprint history and eligibility. Use the applicable
`scripts/hmasd_control_release.py inspect/verify --help` for release control.
Perform the protocol section 6 bounded final drain before yielding.
