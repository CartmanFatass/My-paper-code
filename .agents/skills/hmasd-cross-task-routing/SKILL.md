---
name: hmasd-cross-task-routing
description: Use for every cross-task message between persistent HMASD roles. Send once to the locked role/session/model/thinking tuple and use owner-scoped UTF-8 files for long payloads without hash validation.
---

# HMASD Cross-Task Routing

## Boundary and routes

This table is the sole persistent-task address source. An address grants no
authority. Do not discover settings, read task databases, cache a route, copy
the sender's model, infer a replacement, retry through another task or use this
protocol for native children or External Pro.
Public current-work records may link role state but never supply or override a
session address; stale pointer metadata is non-authoritative for routing.

| role_id | session_id | model | thinking |
|---|---|---|---|
| `workflow_design_manager` | `019fb73d-5635-7b63-b165-6c5129bc0217` | `gpt-5.6-sol` | `high` |
| `code_project_manager` | `019f9e4f-f4d0-7fe0-b214-c47fd034e84d` | `gpt-5.6-sol` | `max` |
| `independent_research_explorer` | `019fbded-24cb-7541-aa16-0111b626b945` | `gpt-5.6-sol` | `ultra` |
| `independent_research_review_operator` | `019fb311-6137-7781-9708-3df24da34a4b` | `gpt-5.6-luna` | `medium` |

Router session fields mirror this table exactly. Every workflow requirement,
defect or plan request targets WDM. CPM and Explorer have no workflow design,
modification, acceptance or workflow Git authority. WDM returns only an exact
workflow reload/mechanical receipt; it does not become a runtime or scientific
authority.

## Native send

Resolve exactly one row and call `codex_app__send_message_to_thread` once with
that `threadId`, `model`, `thinking` and the intended prompt. Passing model and
thinking is mandatory. Omission, override or sender-setting substitution is
`ROUTE_CONFIGURATION_MISMATCH` and permits no send.

If the native tool is unavailable or errors, return `ROUTE_UNAVAILABLE`. Do not
retry automatically, discover another task, use a relay or claim delivery. A
successful call returns `ROUTE_SENT`; it proves only that one call succeeded.

## Independent-research separation

Only direct user instruction in the Explorer task changes research goal,
candidate status/order, campaign lifecycle, review scope or continuation. WDM
may send Explorer only `WORKFLOW_RELOAD_RECEIPT` or a mechanical workflow fact,
each with `research_state_effect=none`. CPM may return only exact mechanical
project-validation facts. Explorer rejects a scientific command from either as
`ROUTE_AUTHORITY_MISMATCH` without changing state.

The Project Operations Operator direction-review child returns natively to its
Explorer parent and never uses this route. The persistent methodology operator
may return only its exact terminal methodology packet or blocker to WDM.

## Long-text file handoff

Use a direct message for ordinary text. For payloads larger than 8 KiB or whose
exact UTF-8 content must avoid message truncation, the sender writes one
non-overwriting file beneath its own
`temp/sessions/<role>/handoffs/` with the registered helper:

```powershell
& '<hmasd_python_interpreter>' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' write `
  --owner-role <source-role> --label <purpose> --source <source-file>
```

The helper returns only `handoff_path`, `handoff_owner_role` and
`handoff_encoding=utf-8`. The cross-task message carries those fields plus
`handoff_purpose`, not the payload body. Before reading, the receiver runs:

```powershell
& '<hmasd_python_interpreter>' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' verify `
  --owner-role <locked-source-role> --path <handoff_path>
```

Verification checks the locked owner, exact owner-root containment, regular
non-symlink file identity and valid UTF-8. It uses no hash, digest, fingerprint
or byte-count admission field. `LONG_TEXT_HANDOFF_VERIFIED` permits consumption;
failure returns `LONG_TEXT_HANDOFF_INVALID` without reconstruction or alternate
transport. The receiver returns `HANDOFF_CONSUMED path=<handoff_path>`. Only the
source owner may later perform an explicit cleanup.

## Route replacement and source validation

No role replaces a route automatically. When the user supplies a replacement
role/session/model/thinking tuple, WDM updates this table, router mirror and
focused contracts in one workflow commit. Until that commit is loaded, the
route is `ROUTE_UNAVAILABLE`.

For an incoming delegation, `source_thread_id` must equal the locked session of
its claimed role. A mismatch is `ROUTE_IDENTITY_MISMATCH`. A handoff that fails
owner/path/UTF-8 verification is `ROUTE_HANDOFF_INVALID`.

End with exactly one result:

- `ROUTE_SENT role=<role> session_id=<session> model=<model> thinking=<thinking>`
- `ROUTE_CONFIGURATION_MISMATCH role=<role>`
- `ROUTE_AUTHORITY_MISMATCH role=<role>`
- `ROUTE_IDENTITY_MISMATCH role=<role>`
- `ROUTE_HANDOFF_INVALID role=<role>`
- `ROUTE_UNAVAILABLE role=<role>`

This protocol performs no experiment, scientific evaluation, review transport
or project computation.
