# Codex Managed Actor and Mailbox Policy

The supervisor binds App Server `threadId` values to existing semantic
`actor_context_id` values and may deliver typed mailbox references to
ACTIVE Operational Root and Portfolio threads.

## Authority

- Identity is only `threadId → binding_id → actor_context_id`.
- Thread names, previews, model prose, and `agentRole` are not identity.
- A model response may not supply or override actor, binding, thread,
  source-kind, or authority fields.
- Mailbox payloads are typed references, not free-form child prose.
- The supervisor does not edit canonical repository artifacts.

## Stage 3

Operator provisioning, Memory-off confirmation, manual turns, and
thread-derived `NO_CONTROL_ACTION` / `CONTEXT_REANCHOR_ACK` only.

## Stage 4

Durable mailbox, semantic-ledger scan, Root↔Portfolio ACL, and at most
one automatic `turn/start` per prepared wake batch targeting an idle
ACTIVE binding. `turn/steer` is never automatic. Mutating App Server
requests are never retried. Uncertain submissions stay
`SUBMISSION_UNCERTAIN` until reconciled by `clientUserMessageId`.

## Forbidden event kinds

```text
BLOCKED FAILED SUCCESS RETIRED PAUSED PARKED RELEASED
```

## Live work

Live App Server canaries remain deferred until Codex quota is restored.
Do not invent acceptance or live-canary reports.
