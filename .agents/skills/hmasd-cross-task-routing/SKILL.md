---
name: hmasd-cross-task-routing
description: Use for every cross-task message between persistent HMASD Codex roles. Route only through the fixed session, model and effort triples in AGENTS.md, validate incoming sources, and fail closed on replacement or delivery errors.
---

# HMASD Cross-Task Routing

## Purpose and boundary

Use this Skill before every message between persistent HMASD Codex roles. It
uses only the fixed route triples in the root `AGENTS.md`; there is no dynamic
discovery, liveness probe, SQLite lookup, conversation cache or inferred route.

This protocol does not route native children or replace the External Pro
browser conversation binding. A fixed session is an address, not authority.

## Fixed routes

| Role | Session | Model | Thinking |
|---|---|---|---|
| Workflow Design Manager | `019f9d2f-e0ea-7411-9fd7-386f45f76909` | `gpt-5.6-sol` | `high` |
| Project Manager | `019f9e4f-f4d0-7fe0-b214-c47fd034e84d` | `gpt-5.6-sol` | `xhigh` |
| External Review Operator | `019f9c6a-9401-7ae0-ace5-dd827dccba2b` | `gpt-5.6-luna` | `medium` |

The router is the source of truth. This table is a readable contract mirror and
must match it exactly. For `send_message_to_thread`, pass the selected session
as `threadId`, model as `model`, and thinking as `thinking` in the same tool
call. Never use the sender's own settings, an assignment field, message history
or any runtime state as a target setting source.

Route settings are transport parameters only. Message payloads must not contain
`live_target_model`, `live_target_effort`, `live_target_thinking`, fixed target
model/effort copies, return model/effort copies, or any field that can be reused
as a reverse-route setting. Session IDs may appear only where assignment
identity requires an address; they do not carry model or effort authority.

## Route replacement

No role replaces or discovers a route automatically. When the user archives or
replaces a persistent task, all sends to that role stop. The user supplies the
new session, model and effort; Workflow Design Manager updates the router, this
Skill and focused contracts in one explicit user-directed workflow-design commit. Until that
commit is loaded, the route is `ROUTE_UNAVAILABLE`.

## Send business messages

Select the exact fixed target triple, send once with all three tool parameters,
and stop after successful delivery. A tool error or unavailable fixed task is
`ROUTE_UNAVAILABLE`; never retry automatically.

For an incoming message, `codex_delegation.source_thread_id` must equal the
fixed session for its claimed source role. A mismatch is
`ROUTE_SOURCE_MISMATCH` and has no authority. Do not reply until the user
directs a route replacement commit.

End with exactly one routing result:

- `ROUTE_SENT role=<role> session_id=<fixed-session>`
- `ROUTE_SOURCE_MISMATCH role=<role>`
- `ROUTE_UNAVAILABLE role=<role>`

This protocol performs no experiment, scientific evaluation, review-runtime
operation, or project computation.
