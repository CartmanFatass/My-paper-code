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

Official text does **not** document:

```text
thread/memoryMode/set
clientUserMessageId
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
