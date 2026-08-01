---
name: hmasd-cross-task-routing
description: Use for every cross-task message between persistent HMASD Codex roles. Resolve the target's locked role, session, model and thinking, pass that exact tuple in one native send, and validate the declared source session.
---

# HMASD Cross-Task Routing

## Purpose and boundary

Use this Skill before every message between persistent HMASD Codex roles. The
locked route table below is the single complete source for target role,
session, model and thinking. The root `AGENTS.md` mirrors session identities so
role bootstrap and non-routing consumers keep their existing address contract.

This protocol does not route native children or replace Code Project Manager's
Agentify External Pro transport ownership. A session is an address, not authority.
Do not discover live settings, read `state_5.sqlite`, cache a route, copy the
sender's settings or infer a replacement row.

## Locked route table

| role_id | session_id | model | thinking |
|---|---|---|---|
| `workflow_design_manager` | `019fb73d-5635-7b63-b165-6c5129bc0217` | `gpt-5.6-sol` | `high` |
| `code_project_manager` | `019f9e4f-f4d0-7fe0-b214-c47fd034e84d` | `gpt-5.6-sol` | `max` |
| `independent_research_explorer` | `019fbd62-3440-7dd1-8d41-c72c15cb8d4e` | `gpt-5.6-sol` | `ultra` |
| `independent_research_review_operator` | `019fb311-6137-7781-9708-3df24da34a4b` | `gpt-5.6-luna` | `medium` |

Each role appears exactly once. Router session fields must mirror this table.
The persistent independent review operator may route only an exact terminal
methodology packet or blocker to Workflow Design Manager. Direction review is a
native-child final to Explorer and never enters this cross-task route. Neither
path changes the formal loop.

## Independent-research authority preservation

Cross-task delivery never grants scientific command authority. Only a direct
user instruction in the Independent Research Explorer task may change an
Explorer research goal, candidate status or order, campaign lifecycle,
convergence decision, scientific review scope or continuation.

Workflow Design Manager may send Explorer only a control-plane reload notice or
mechanical receipt, each explicitly marked `research_state_effect=none`.
Code Project Manager may return only an exact mechanical nonconformance or a
verbatim External Pro advisory gap from its registered toy-validation lane. The
shared Project Operations Operator's `INDEPENDENT_DIRECTION_REVIEW` child
returns only to its Explorer parent and does not use this Skill. None of these
routes grants its
sender authority to select, sequence, pause, resume, revise, re-audit or
terminate a direction, interpret campaign completion, formulate a Pro
scientific question, or relay such a command on the user's behalf. Explorer
rejects any such message as `ROUTE_AUTHORITY_MISMATCH` without changing research
state.

## Native send

Resolve exactly one target row by `role_id`. Call
`codex_app__send_message_to_thread` once with the row's `session_id` as
`threadId`, the row's `model`, the row's `thinking`, and the intended message as
`prompt`. Passing both `model` and `thinking` is mandatory. Omitting either,
using a caller-supplied override or substituting the sender's settings is
`ROUTE_CONFIGURATION_MISMATCH` and permits no send.

Do not add a live-settings probe, route cache, restoration step, automatic
retry or substitute relay. The locked row is user-owned configuration; a
callable tool is a runtime capability, not something this Skill can create.

If the cross-task tool is unavailable or returns an error, finish with
`ROUTE_UNAVAILABLE`. Do not retry automatically, discover another task, switch
transport or report delivery. A successful tool return permits `ROUTE_SENT`
and reports the exact locked tuple used; it does not prove any later host-side
setting change outside that call.

## Long-text file handoff

Do not embed a UTF-8 payload larger than 8 KiB in a cross-task message. Also use
this path for a smaller payload when exact bytes must survive message rendering,
attachment conversion, task summaries or output truncation. Short ordinary
messages remain direct and incur no file-handling step.

The sender writes the complete payload beneath `temp/handoffs/` with the
mechanical helper:

```powershell
& '<hmasd_python_interpreter>' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' write `
  --label <purpose> --source <source-file>
```

Omit `--source` only when piping the exact payload bytes on standard input. The
helper accepts valid UTF-8, creates a non-overwriting timestamped file, and
returns `handoff_path`, `handoff_bytes`, `handoff_sha256` and
`handoff_encoding=utf-8`. Actual payloads are local-only and Git-ignored.

The cross-task message contains no payload body. It carries exactly the returned
identity plus `handoff_purpose`. That relative path becomes an assignment-named
read within the receiver's existing authority; it grants no search of `temp/`
or any other project state. Before reading, the receiver verifies the identity:

```powershell
& '<hmasd_python_interpreter>' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' verify `
  --path <handoff_path> --bytes <handoff_bytes> --sha256 <handoff_sha256>
```

Only `LONG_TEXT_HANDOFF_VERIFIED` permits consumption. A missing, truncated,
non-UTF-8, out-of-root or digest-mismatched file fails closed as
`LONG_TEXT_HANDOFF_INVALID`; it does not authorize reconstructing the payload
from task history or resending an embedded copy. After use, the receiver returns
`HANDOFF_CONSUMED path=<handoff_path> sha256=<handoff_sha256>`. Neither role
deletes a payload automatically; cleanup is a separate explicit action after
acknowledgement.

## Session replacement

No role replaces or discovers a route automatically. When the user archives or
replaces a persistent task or changes its model or thinking, all sends to that
role stop. The user supplies the replacement `role_id`, `session_id`, `model`
and `thinking`; Workflow Design Manager updates this table, the router's mirrored
session and focused contracts in one explicit user-directed workflow-design
commit. Until that commit is loaded, the route is `ROUTE_UNAVAILABLE`.

## Source validation and send result

For an incoming message, `codex_delegation.source_thread_id` must equal the
locked `session_id` for its claimed `role_id`. A mismatch is
`ROUTE_IDENTITY_MISMATCH` and has no authority. A long-text handoff that fails
the mechanical payload verifier ends as `ROUTE_HANDOFF_INVALID`.

End with exactly one routing result:

- `ROUTE_SENT role=<role_id> session_id=<session_id> model=<model> thinking=<thinking>`
- `ROUTE_CONFIGURATION_MISMATCH role=<role_id>`
- `ROUTE_AUTHORITY_MISMATCH role=<role_id>`
- `ROUTE_IDENTITY_MISMATCH role=<role>`
- `ROUTE_HANDOFF_INVALID role=<role>`
- `ROUTE_UNAVAILABLE role=<role>`

This protocol performs no experiment, scientific evaluation, review-runtime
operation, or project computation.
