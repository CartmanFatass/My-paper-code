---
name: hmasd-cross-task-routing
description: Use for every cross-task message between persistent HMASD Codex roles. Route one message through the role's fixed session and validate the declared source session.
---

# HMASD Cross-Task Routing

## Purpose and boundary

Use this Skill before every message between persistent HMASD Codex roles. The
root `AGENTS.md` supplies the fixed session addresses. This Skill routes session
identity only. It does not inspect, select, transmit, preserve, compare or
restore a task's model or reasoning effort. Those settings and their host-side
effects are outside the project routing contract.

This protocol does not route native children or replace Research Operations
Manager's External Pro browser binding. A session is an address, not authority.
The role table is the only target selection performed here.

## Fixed session addresses

| Role | Session |
|---|---|
| Workflow Design Manager | `019f9d2f-e0ea-7411-9fd7-386f45f76909` |
| Code Project Manager | `019f9e4f-f4d0-7fe0-b214-c47fd034e84d` |
| Research Operations Manager | `019f9c6a-9401-7ae0-ace5-dd827dccba2b` |
| Independent Research Pro Review Operator | `019fb311-6137-7781-9708-3df24da34a4b` |

The router is the source of truth and this table must mirror it exactly.
The independent review operator may route only its exact terminal methodology
packet or blocker to Workflow Design Manager. It never routes through Research
Operations Manager or changes the formal operations loop.

## Native send

Use the currently callable Codex cross-task send tool once with the fixed target
session and the intended message. Do not add a project-side settings probe,
route guard, settings cache, restoration step or substitute relay. A callable
tool is a runtime capability, not something this Skill can create or infer.

If the cross-task tool is unavailable or returns an error, finish with
`ROUTE_UNAVAILABLE`. Do not retry automatically, discover another task, switch
transport or report delivery. A successful tool return permits `ROUTE_SENT`;
it makes no claim about the target task's model or reasoning effort.

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

No role replaces or discovers a session automatically. When the user archives
or replaces a persistent task, all sends to that role stop. The user supplies
the new session; Workflow Design Manager updates the router, this Skill and
focused contracts in one explicit user-directed workflow-design commit. Until
the session commit is loaded, the route is `ROUTE_UNAVAILABLE`.

## Source validation and send result

For an incoming message, `codex_delegation.source_thread_id` must equal the
fixed session for its claimed source role. A mismatch is
`ROUTE_IDENTITY_MISMATCH` and has no authority. A long-text handoff that fails
the mechanical payload verifier ends as `ROUTE_HANDOFF_INVALID`.

End with exactly one routing result:

- `ROUTE_SENT role=<role> session_id=<fixed-session>`
- `ROUTE_IDENTITY_MISMATCH role=<role>`
- `ROUTE_HANDOFF_INVALID role=<role>`
- `ROUTE_UNAVAILABLE role=<role>`

This protocol performs no experiment, scientific evaluation, review-runtime
operation, or project computation.
