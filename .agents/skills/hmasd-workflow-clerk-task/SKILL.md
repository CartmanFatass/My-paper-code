---
name: hmasd-workflow-clerk-task
description: Use when the top-level HMASD Workflow-Clerk task receives a delegation, RETURN, Portfolio action, participant stop, retry event, or user routing request.
---

# HMASD Workflow-Clerk Task

Read `.codex/prompts/hmasd-workflow-clerk.md` and
`hmasd-operations-manual` completely, then finish at the prompt's Clerk return
boundary.

For every outbound ASSIGNMENT, run
`scripts/hmasd_session_envelope.py assignment-from-brief --help`, then supply
only its semantic CLI inputs and the validated ingress envelope locator as the
release source. The command generates the complete body, current context SHA
values, role defaults, and envelope. Do not author an assignment `*.body.json`
or control-release JSON file.
