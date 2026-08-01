# Agentify Pro transport

```text
document_kind=workflow_control_contract
status=sole_backend
formal_compute=false
scientific_iteration_cost=zero
agentify_source=https://github.com/CartmanFatass/desktop.git
agentify_branch=codex/hmasd-strict-review-transport
agentify_required_commit=read_AGENTIFY_REQUIRED_COMMIT_from_wrapper
browser_backend=chrome-cdp
browser_window_policy=one_agentify_process_one_chrome_window
stable_key_tab_policy=one_live_tab_per_stable_key
```

Browser transport is retired; Agentify is the sole External Pro transport.

## Stable-key ownership

| Stable key | Owner | Use |
|---|---|---|
| `hmasd-formal-pro` | Research Operations Manager | formal-review Pro conversation |
| `hmasd-explorer-validation-pro` | Research Operations Manager | Explorer validation Pro conversation |
| `hmasd-independent-research-pro` | Independent Research Pro Review Operator | independent-research Pro conversation |

Stable keys identify a runtime binding, not a repository conversation record.
Within one live Agentify process, every operation for the same stable key reuses
its existing tab. Different stable keys use separate tabs in the same Chrome
window; an operation never creates a new window merely because it is a new
review turn. One tab may be recreated after an Agentify or Chrome restart.
Conversation IDs, URLs, model evidence, credentials, authentication material
and live registrations are runtime-only and must never be committed or placed
in role/Skill text. The binding is loaded from the local Agentify state at the
time of the operation and must match the selected owner and requested Pro
model before sending.

## One-round protocol

1. The owning role verifies the user-authorized turn. For Agentify, the
   registered wrapper reads the UTF-8 prompt and writes one new role-owned
   `TRANSPORT_BACKEND.json` plus its matching request.
2. The immutable selection is reloaded before every send or recovery.
3. For Agentify, the owner resolves its stable key to one runtime conversation
   binding and uses the wrapper's `prepare` command to persist the immutable
   request identity before sending.
4. Agentify submits at most one exact prompt for that operation. It does not
   click `Answer now`, `Continue`, `Retry` or `ResponseRetry`.
5. The transport validator
   `.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py`
   checks the stable key, conversation, selected model, completion snapshots
   and archived response integrity.
6. Only a complete validated request/receipt pair permits the owning role's
   normal raw archival and mechanical intake. The receipt is evidence of transport only;
   it cannot interpret science or authorize code, compute or project state.

An unavailable conversation or incomplete response stops that operation. One
fresh recovery operation is allowed by the Minimal recovery rule. A transport
failure consumes zero scientific iterations.

## Minimal recovery

The defining rule is `.agents/skills/hmasd-agentify-pro-transport/SKILL.md#minimal-recovery`.

## Runtime and installation boundary

Its public `/health` supplies `sourceCommit` and `sourceDirty`; the wrapper must match both before any send. Its MCP
registration is
`node C:/Projects/agentify-desktop/bin/agentify-desktop.mjs mcp`.
Agentify installation and its local state are outside HMASD Git. Credentials and
conversation bindings remain in the approved runtime locations. Workflow files
record only stable keys, owners, validator paths and invariants. The Agentify
service writes only its local transport ledger. The HMASD wrapper may write the
role-owned immutable backend selection, runtime request/receipt and, after
validation, the exact raw archive;
it may not write `CURRENT_WORK`, science, code, mechanical interpretation or Git
state.

## Acceptance evidence

The owning role returns one validated request/receipt pair. The request contains
the selected backend and selection path; the receipt contains the stable key,
conversation identity, message identities, completion snapshots, control state,
timing and response integrity. A
duplicate idempotency key with the same request returns the existing operation;
a conflicting payload is rejected. Restart recovery observes the same operation
and conversation without sending again.
