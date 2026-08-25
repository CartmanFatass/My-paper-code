# Stage 3 Protocol Evidence

```text
document_kind=protocol_evidence
owner=operational_root
date=2026-08-18
codex_version=codex-cli 0.147.0
schema_root=%LOCALAPPDATA%\HMASD\codex-supervisor\schema\codex-cli_0.147.0
```

Claim kinds are separated. Documentation and schema do not create HMASD
authority.

## Official documentation statements

Pages used through `openaiDeveloperDocs` on 2026-08-18:

- https://learn.chatgpt.com/docs/app-server
- https://learn.chatgpt.com/docs/app-server#lifecycle-overview
- https://learn.chatgpt.com/docs/app-server#api-overview
- https://learn.chatgpt.com/docs/app-server#threads
- https://learn.chatgpt.com/docs/app-server#turns

Documented methods:

```text
thread/start     create a thread; emits thread/started
thread/resume    reopen a stored thread for later turn/start
thread/read      read without resume; includeTurns optional
turn/start       start generation; streams turn/item notifications
turn/completed   server notification with final mechanical status
```

Official text also documents:

```text
thread/loaded/list   list thread ids currently loaded in memory
thread/read          returned thread objects include runtime status
```

Official text also documents approval policy on thread/start and turn/start.
It does **not** document:

```text
thread/memoryMode/set
clientUserMessageId
thread/name/set
sandbox
sandboxPolicy
```

## Local-schema observations (`codex-cli 0.147.0`)

Present in `ClientRequest.json`:

```text
thread/start
thread/resume
thread/read
turn/start
```

`TurnStartParams` includes `clientUserMessageId` as `string | null`.

`thread/loaded/list` is present. Params are optional `cursor` / `limit`.
Response is `{ data: string[], nextCursor?: string|null }`.

Local `ThreadStatus` is a tagged union:

```text
notLoaded
idle
systemError
active   (requires activeFlags)
```

`ThreadMemoryMode` exists as an enum `{enabled, disabled}` but is not
referenced by any client method and is not a `ThreadStartParams` field.
No client method named `thread/memoryMode/set` exists.

## Live-transport observations

None in this session. Live App Server is deferred with Tasks 15/16.

## Implementation inferences (not wire facts)

- Wake-batch reconciliation may send `clientUserMessageId` because the
  local schema has the field.
- Memory-off cannot be proven through a thread API on this host. Stage 3
  activation must use `OPERATOR_CONFIRMED_GLOBAL_DISABLED` until a later
  schema shows a memory-mode method.
- Idle/loaded decision table used by synthetic Stage 4:

```text
binding REVOKED or missing          -> REVOKED
thread/read status.type=active      -> ACTIVE_TURN   (queue; no turn/steer)
thread/read status.type=idle
  and id in thread/loaded/list      -> IDLE_LOADED
thread/read status.type=notLoaded
  or idle but absent from loaded    -> IDLE_NOT_LOADED (resume once, no retry)
status missing or systemError
  or thread/read fails              -> UNKNOWN       (operator review)
```

`thread/loaded/list` is sent with `{}` when no cursor is needed. It is
not added to the `-32001` retry allow-list; only `thread/list` and
`thread/read` retry.

## Wire fields actually sent by this supervisor

Each row names how it is known. Implementation inferences are not local
schema proofs.

```text
method/field                         claim kind
thread/start                         official-doc + local-schema
thread/start.cwd                     official-doc + local-schema
thread/start.ephemeral               official-doc + local-schema
thread/start.approvalPolicy          official-doc observation
thread/resume                        official-doc + local-schema
thread/read                          official-doc + local-schema
thread/read.includeTurns             official-doc + local-schema
thread/loaded/list                   official-doc + local-schema
turn/start                           official-doc + local-schema
turn/start.input                     official-doc + local-schema
turn/start.clientUserMessageId       local-schema observation
turn/start.approvalPolicy            official-doc observation
```

`thread/name/set` is **not** in the 0.147.0 `ClientRequest.json` methods
recorded above. The supervisor does not send it.

`thread/start.sandbox` and `turn/start.sandboxPolicy` remain
implementation inferences, not local-schema observations. The supervisor
does **not** send them until a local-schema definition or live capability
evidence exists.

If `thread/loaded/list` fails or times out, readiness is `UNKNOWN`. A
failed loaded-list query is never treated as "already loaded".
