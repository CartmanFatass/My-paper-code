---
name: hmasd-cross-task-routing
description: Use for every cross-task message between persistent HMASD Codex roles. Route through fixed sessions, read the target's live model and effort immediately before sending, explicitly echo them in the visible tool call, and fail closed on settings or delivery errors.
---

# HMASD Cross-Task Routing

## Purpose and boundary

Use this Skill before every message between persistent HMASD Codex roles. The
root `AGENTS.md` supplies fixed session addresses only. The target task owns its
live model and reasoning effort; neither value is stored in Git, inferred from a
role default, copied from an assignment, or cached between sends.

This protocol does not route native children or replace Research Operations
Manager's External Pro browser binding. A session is an address, not authority. Dynamic
session discovery, liveness polling and conversation-local route caches remain
forbidden.

## Fixed session addresses

| Role | Session |
|---|---|
| Workflow Design Manager | `019f9d2f-e0ea-7411-9fd7-386f45f76909` |
| Code Project Manager | `019f9e4f-f4d0-7fe0-b214-c47fd034e84d` |
| Research Operations Manager | `019f9c6a-9401-7ae0-ace5-dd827dccba2b` |

The router is the source of truth and this table must mirror it exactly.

## Pre-send live-settings preservation

Immediately before every protocol or business send, use the registered HMASD
Python interpreter to run the bundled read-only probe:

```powershell
& '<hmasd_python_interpreter>' '.agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py' `
  --thread-id <fixed-target-session> --expect-cwd <project-root>
```

The script opens `~/.codex/state_5.sqlite` with SQLite `mode=ro`. Accept only a
zero exit with `status=LIVE_SETTINGS`. Its JSON visibly reports the exact
`model` and `thinking` currently stored for the unarchived target session.
Without caching or intervening work, invoke the visible
`send_message_to_thread` tool exactly once with the fixed session as `threadId`,
the returned `model` as `model`, and the returned `thinking` as `thinking`.
Omitting either explicit tool parameter, substituting a fixed/default value or
reusing an earlier probe result is forbidden.

Route settings are tool parameters only. Message payloads must not contain
`live_target_model`, `live_target_effort`, `live_target_thinking`, fixed target
model/effort copies, return model/effort copies, or another field reusable as a
reverse-route setting.

Any nonzero probe result is `ROUTE_SETTINGS_UNAVAILABLE` and forbids delivery.
A send tool error is `ROUTE_UNAVAILABLE`; never retry or resend automatically.
Only after a send error or a user-observed settings anomaly may the sender run
one diagnostic probe with `--expect-model` and `--expect-thinking`.
`SETTINGS_DRIFT` becomes `ROUTE_SETTINGS_DRIFT` and is reported without resend.

## Session replacement

No role replaces or discovers a session automatically. When the user archives
or replaces a persistent task, all sends to that role stop. The user supplies
the new session; Workflow Design Manager updates the router, this Skill and
focused contracts in one explicit user-directed workflow-design commit. Model
and effort never participate in session replacement. Until the session commit
is loaded, the route is `ROUTE_UNAVAILABLE`.

## Source validation and send result

For an incoming message, `codex_delegation.source_thread_id` must equal the
fixed session for its claimed source role. A mismatch is
`ROUTE_SOURCE_MISMATCH` and has no authority.

End with exactly one routing result:

- `ROUTE_SENT role=<role> session_id=<fixed-session>`
- `ROUTE_SOURCE_MISMATCH role=<role>`
- `ROUTE_SETTINGS_UNAVAILABLE role=<role>`
- `ROUTE_SETTINGS_DRIFT role=<role>`
- `ROUTE_UNAVAILABLE role=<role>`

This protocol performs no experiment, scientific evaluation, review-runtime
operation, or project computation.
