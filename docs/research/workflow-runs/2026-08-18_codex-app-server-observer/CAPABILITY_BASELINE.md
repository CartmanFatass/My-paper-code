# Codex App Server Observer Capability Baseline

```text
phase_0_gate_commit=ad91385d6defbc6fb786ea5e75802b556c5d961e
phase_0_gate_status=PASSED
phase_1_safe_boundary=synthetic_observer_foundation_complete
phase_1_docs_schema_alignment=initialize+initialized+thread/list+thread/read+turn/start+turn/completed
live_app_server_canary=not started
experimentalApi=disabled
codex_binary=C:\Users\fires\AppData\Roaming\npm\codex.cmd
codex_version=codex-cli 0.147.0
schema_root=%LOCALAPPDATA%\HMASD\codex-supervisor\schema\codex-cli_0.147.0
```

## Phase 0

HEAD `ad91385` supersedes `ed3992ae`. Remediation acceptance is
`docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/REPOSITORY_CONTEXT_LIFECYCLE_REMEDIATION_ACCEPTANCE.md`.

Verified:

```text
pytest tests/codex_semantic_mvp tests/codex_context_lifecycle
  --basetemp=C:/Projects/HMASD/.tmp_app_server_phase0
  → 308 passed
lifecycle doctor: schema 3, memory_authority=none, physical_deletion=false
ACTIVE .codex/config.toml: no PreToolUse
```

## Phase 1 stop point

Synthetic observer and protocol foundation is complete. Covered by
`tests/codex_supervisor` (73 passed) and
`scripts/codex-app-server-observer-test.ps1` under Windows PowerShell 5.1.

Accepted locally, still uncommitted:

- config, binary, schema capture, JSONL protocol, observer store
- process transport and client handshake / read retry
- mechanical normalizer and thread/turn/item snapshots
- observer service over a fake App Server
- read-only `thread/list` + `thread/read` reconciliation
- mechanical timeline export
- explicit ephemeral canary **against the fake server only**
- restart / EOF recovery without auto-resume
- doctor / CLI / PowerShell 5.1 operators
- reliability and lexical-neutrality matrices

The observer lists stored threads. It receives live turn/item notifications
only for threads started or resumed through its own App Server connection.
Phase 1 does not auto-resume existing threads.

Live `codex app-server` child handshake, live snapshot, and live canary
have **not** been started. That remains Task 15.

## Official documentation pages used

Fetched through user-level `openaiDeveloperDocs` on 2026-08-18. These are
external official developer statements, not HMASD project authority.

- https://learn.chatgpt.com/docs/app-server
- https://learn.chatgpt.com/docs/app-server#protocol
- https://learn.chatgpt.com/docs/app-server#message-schema
- https://learn.chatgpt.com/docs/app-server#getting-started
- https://learn.chatgpt.com/docs/app-server#lifecycle-overview
- https://learn.chatgpt.com/docs/app-server#initialization
- https://learn.chatgpt.com/docs/app-server#experimental-api-opt-in
- https://learn.chatgpt.com/docs/app-server#threads
- https://learn.chatgpt.com/docs/app-server#turns

## Local schema capture

Claim kind: local-schema observation.

Command observed to succeed:

```text
C:\Users\fires\AppData\Roaming\npm\codex.cmd app-server generate-json-schema --out <external schema dir>
codex --version → codex-cli 0.147.0
```

The official docs name the same generate command. Capture wrote outside the
repository. Required method strings are present in the generated blob:

```text
initialize
thread/start
thread/list
thread/read
turn/start
turn/completed
item/started
item/completed
```

## Docs vs local schema, handshake and Task 4/5 methods

Claim kinds are separated below. Transport and client may use only the
overlapping facts.

Official documentation statement:

- Wire messages omit `"jsonrpc":"2.0"`.
- Default transport is stdio JSONL: `codex app-server`.
- Clients send one `initialize` request, then an `initialized` notification,
  before any other request. The server rejects earlier requests.
- `initialize.params.clientInfo` identifies the client (`name`, `title`, `version`).
- `initialize.params.capabilities.experimentalApi` defaults to stable when
  omitted or `false`.
- `thread/list` and `thread/read` are documented read APIs.
- `thread/start`, `thread/resume`, `thread/fork`, `turn/start`, `turn/steer`,
  `turn/interrupt`, `thread/compact/start`, and `review/start` are documented
  mutating APIs.
- `turn/completed` is a server notification.
- Error `-32001` is documented as `"Server overloaded; retry later."` with
  exponential delay and jitter. The documented occurrence is WebSocket
  ingress-full.

Local-schema observation (`codex-cli 0.147.0`):

- `JSONRPCRequest` / `JSONRPCNotification` have no `jsonrpc` property.
- `ClientRequest.json` includes `initialize`, `thread/start`, `thread/resume`,
  `thread/fork`, `thread/list`, `thread/read`, `turn/start`, `turn/steer`,
  `turn/interrupt`, `thread/compact/start`, `review/start`.
- `ClientNotification.json` includes only `initialized`.
- `ServerNotification.json` includes `turn/completed`, `thread/started`,
  `item/started`, `item/completed`.
- `ServerRequest.json` includes unexpected-in-Phase-1 methods such as
  `item/commandExecution/requestApproval`.
- `InitializeParams.clientInfo` requires `name` and `version`; `title` is
  optional. `capabilities.experimentalApi` exists and defaults to `false`.
- `InitializeResponse` requires `userAgent`, `platformFamily`, `platformOs`,
  and `codexHome`.
- Request `id` may be string or int64.
- `ThreadListParams` has no required fields. Observed optional keys:
  `archived`, `cursor`, `cwd`, `limit`, `modelProviders`, `searchTerm`,
  `sectionId`, `sortDirection`, `sortKey`, `sourceKinds`, `useStateDbOnly`.
- `ThreadReadParams` requires `threadId` and allows `includeTurns`.

Agreement used by Task 4/5:

- No outbound `jsonrpc` field.
- Handshake methods `initialize` and `initialized`.
- Read methods `thread/list` and `thread/read`.
- Mutating methods listed above exist in both sources.
- `experimentalApi=false` is the stable surface.

Not claimed / not sent:

- Official `thread/list` filters `isPinned`, `parentThreadId`, and
  `ancestorThreadId` are not in this host `ThreadListParams` property list.
- Host `ThreadListParams.sectionId` is not treated as documented for Phase 1.
- Live `codex app-server` child handshake has not been observed.
- No live `thread/start` or `turn/start` has been sent.

## Observer runtime

Default home: `%LOCALAPPDATA%\HMASD\codex-supervisor`. Tests use `tmp_path`
and must not write that directory.

## Next session prerequisite

Use the official OpenAI Docs MCP before implementing live handshake,
request shapes, or canary parameters.

Installed as **user-level** Grok MCP, not a repository dependency:

```text
~/.grok/config.toml
[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
enabled = true
```

Verified 2026-08-18: `grok mcp doctor openaiDeveloperDocs` → handshake OK,
5 tools, healthy. Repo `.grok/config.toml` must stay absent.

A new Grok session is required for those tools to appear. Resume from
`SESSION_HANDOFF.md` in this directory.
