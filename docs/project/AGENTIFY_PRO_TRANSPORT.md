# Optional Agentify Pro transport

```text
document_kind=workflow_control_contract
status=optional_backend
formal_compute=false
scientific_iteration_cost=zero
agentify_source=https://github.com/CartmanFatass/desktop.git
agentify_branch=codex/hmasd-strict-review-transport
agentify_required_commit=917c5328695b4546e8c7e548878b00a07f45af91
```

Agentify is an optional receipt-bearing transport for an already-authorized
External Pro turn. It does not replace the registered Pro conversations or
change role authority. The transport backend is selected exactly once before
submission; one round never uses Agentify and the in-app browser path in
parallel.

## Stable-key ownership

| Stable key | Owner | Use |
|---|---|---|
| `hmasd-formal-pro` | Research Operations Manager | formal-review Pro conversation |
| `hmasd-explorer-validation-pro` | Research Operations Manager | Explorer validation Pro conversation |
| `hmasd-independent-research-pro` | Independent Research Pro Review Operator | independent-research Pro conversation |

Stable keys identify a runtime binding, not a repository conversation record.
Conversation IDs, URLs, model evidence, credentials, authentication material
and live registrations are runtime-only and must never be committed or placed
in role/Skill text. The binding is loaded from the local Agentify state at the
time of the operation and must match the selected owner and requested Pro
model before sending.

## One-round protocol

1. The owning role verifies the user-authorized turn. For Agentify, the
   registered wrapper reads the exact prompt bytes, computes SHA-256 internally,
   and writes one new role-owned `TRANSPORT_BACKEND.json` plus its matching
   request. Operators do not calculate, transcribe or edit hashes.
2. The immutable selection is reloaded before every send or recovery. It cannot
   be changed after creation; the other backend must refuse the assignment.
3. For Agentify, the owner resolves its stable key to one runtime conversation
   binding and uses the wrapper's `prepare` command to persist the immutable
   request identity before sending.
4. Agentify submits at most one exact prompt for that operation. It does not
   click `Answer now`, `Continue`, `Retry` or `ResponseRetry`.
5. The transport validator
   `.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py`
   checks the receipt against the exact prompt hash, stable key, conversation
   identity, selected model, user/assistant message identities, completion
   snapshots and response hash.
6. Only a complete validated request/receipt pair permits the owning role's
   normal raw archival and mechanical intake. The receipt is evidence of transport only;
   it cannot interpret science or authorize code, compute or project state.

An unreadable, ambiguous, mismatched or incomplete receipt fails closed without
another submission. A transport failure consumes zero scientific iterations.
The existing in-app browser workflow remains available as a nonparallel
alternative and keeps its own exact-fence, sentinel, monitor and archival
rules.

The Independent Research Pro Review Operator remains a persistent ownership
task for ordered review work, exact raw archival, mechanical intake and return
to the Explorer; it is not replaced by Agentify. An Agentify-backed turn never
creates a sentinel or monitor child. The monitor profile remains available
only to a browser-backed turn during migration. Retiring the browser monitor
or its sentinel is a separate workflow change, allowed only after both the
formal Operations route and the independent-review route have completed
stable Agentify production turns and the user explicitly accepts removal.

## Runtime and installation boundary

Agentify must run with the Electron browser backend from the exact required
commit above with no tracked source
changes; a later fork revision requires a new bounded compatibility smoke
before use. Its public `/health` response supplies `sourceCommit` and
`sourceDirty`, and the HMASD wrapper must match both before any send. Its MCP
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
the selected backend and immutable selection path; the receipt contains the
stable key, conversation identity, model evidence, exact prompt hash, message
identities, completion snapshots, control state, timing and response hash. A
duplicate idempotency key with the same request returns the existing operation;
a conflicting payload is rejected. Restart recovery observes the same operation
and conversation without sending again.
