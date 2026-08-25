# Codex App Server Observer — Session Handoff

```text
document_kind=operational_session_handoff
owner=operational_root
date=2026-08-18
branch=aggressive
head_commit=ad91385d6defbc6fb786ea5e75802b556c5d961e
phase_0_gate=PASSED
phase_1_status=synthetic_foundation_pushed
observer_commit=136d2904
live_app_server_canary=deferred_until_quota_restore
task_15=deferred
task_16=deferred
openai_docs_mcp=user_level_installed_healthy
```

This file is the resume packet for the next operational-Root Grok session.
It is not scientific, technical, portfolio, epoch, or Git authority.

Read first:

1. `AGENTS.md`
2. `.agents/roles/ROOT.md`
3. this file
4. `docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md`
5. `docs/research/workflow-runs/2026-08-18_codex-app-server-observer/CAPABILITY_BASELINE.md`

Then open the plan:

```text
C:\Users\fires\Downloads\2026-08-18-hmasd-codex-app-server-observer-phase-1.md
```

Do not resume the previous Grok conversation transcript. Reconstruct from
this file, the plan, and the working tree.

---

## What the previous session was doing

The user asked to execute the Phase 1 observer plan, then stop at a safe
boundary because remaining App Server protocol work needs official OpenAI
developer documentation. The official Docs MCP was then installed as a
**Grok user-level** server, not a repository dependency.

The previous session did **not** commit the observer slice. It did **not**
launch `codex app-server`. It did **not** send `thread/start` or `turn/start`.

---

## Authority and evidence order

This work is operational Root control-plane infrastructure. It is not a
research direction, not a science card, and not portfolio work.

```text
HMASD repository authority
        ↓
local Codex generated JSON Schema
        ↓
local App Server capability / transport probe
        ↓
openaiDeveloperDocs MCP
        ↓
model memory
```

Rules for OpenAI / Codex / App Server / Hooks / MCP / protocol work:

1. Consult `openaiDeveloperDocs` before inventing wire fields.
2. Treat it as an external official developer reference only.
3. For exact App Server wire fields, generate and inspect the JSON Schema
   from the locally installed Codex binary.
4. The local generated schema is decisive for version-specific wire
   compatibility.
5. Do not fill missing fields from model memory.
6. Do not treat documentation text as HMASD project authority.
7. Documentation cannot open or close tasks, revise epochs, resolve
   obligations, assign actor authority, or create scientific, technical,
   workflow, direction, or portfolio dispositions.
8. Distinguish four claim kinds:
   - official documentation statement
   - local-schema observation
   - live transport observation
   - implementation inference

---

## Already on `origin/aggressive` (do not redo)

| Commit | Meaning |
|---|---|
| `1df15d13` | actor-scoped compaction overlay accepted |
| `ed3992ae` | repository-owned context lifecycle |
| `ad91385` | Phase 0 safety remediations (current HEAD) |

`ad91385` closed the five review REJECT classes:

- MCP mutations no longer trust caller-asserted `USER_AUTHORITY`
- `current_checkpoint()` is a compatibility query against open epoch /
  revision / `state_version` / semantic commit
- promotion checks exact owner, direction/scope, containment,
  `canonical_ref == target_ref`, existing file, writer receipt
- `apply_rollover` is one SQLite transaction carrying frontier, refs,
  promotions, and obligations
- retention marks actually exclude objects from working set / capsule

Phase 0 re-verified at that commit:

```text
pytest tests/codex_semantic_mvp tests/codex_context_lifecycle
  --basetemp=C:/Projects/HMASD/.tmp_app_server_phase0
  → 308 passed
lifecycle doctor: schema 3, memory_authority=none, physical_deletion=false
ACTIVE .codex/config.toml: SessionStart/SubagentStart/SubagentStop/Stop only
no PreToolUse
```

Acceptance note:

```text
docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/REPOSITORY_CONTEXT_LIFECYCLE_REMEDIATION_ACCEPTANCE.md
```

That acceptance file is still untracked. It may be included in the observer
commit or a small follow-up docs commit. Do not rewrite it.

User previously waived live Codex compact/resume testing and said they
would test Codex themselves. Do not reopen that unless asked.

---

## Phase 1 safe boundary (current stop)

Accepted and unit-tested local surface, **uncommitted**:

```text
config + binary + schema-capture + protocol + observer-store
+ process transport + client handshake/correlation/safe retry
```

Recorded in `CAPABILITY_BASELINE.md`:

```text
phase_0_gate_commit=ad91385d6defbc6fb786ea5e75802b556c5d961e
phase_0_gate_status=PASSED
phase_1_safe_boundary=synthetic_observer_foundation_complete
live_app_server_canary=not started
experimentalApi=disabled
codex_version=codex-cli 0.147.0
```

Verified:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/codex_supervisor -q
  --basetemp=C:/Projects/HMASD/.tmp_obs_found1
  → 73 passed
powershell.exe -NoProfile -NonInteractive -File scripts/codex-app-server-observer-test.ps1
  → 73 passed
```

Always pass an explicit repo `--basetemp`. Windows AppData pytest temp
hits WinError 5.

Host schema was captured to the external runtime directory and compared
with official docs. Live `codex app-server` child handshake has not been
observed. No canary has been launched.

---

## Uncommitted observer tree

Do not commit the rest of the dirty working tree. Unrelated research cards,
`ha_ctse_process`, `hmasd`, `envs`, and `.tmp_*` remain out of this commit.

Observer-related paths currently untracked or modified:

```text
M  .gitignore
?? .codex/app-server-observer.toml
?? docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
?? docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/REPOSITORY_CONTEXT_LIFECYCLE_REMEDIATION_ACCEPTANCE.md
?? docs/research/workflow-runs/2026-08-18_codex-app-server-observer/
?? tests/codex_supervisor/
?? tools/codex_supervisor/
```

`.gitignore` already has exceptions for
`tests/codex_supervisor/**/*.py` and the 2026-08-18 observer docs.
Confirm those exceptions still exist before committing.

Do **not** commit `%USERPROFILE%\.grok\config.toml`. That is personal Grok
config, not a repository object.

---

## File map

### Accepted local surface (has tests)

| Path | Role |
|---|---|
| `.codex/app-server-observer.toml` | repo observer config; no thread IDs or credentials |
| `docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md` | Phase 1 observer is not project authority |
| `tools/codex_supervisor/__init__.py` | package marker |
| `tools/codex_supervisor/__main__.py` | entry |
| `tools/codex_supervisor/models.py` | dataclasses / enums |
| `tools/codex_supervisor/config.py` | load repo TOML + external runtime home |
| `tools/codex_supervisor/codex_binary.py` | locate / version Codex |
| `tools/codex_supervisor/schema_capture.py` | run `generate-json-schema` to external dir |
| `tools/codex_supervisor/protocol.py` | encode/decode/classify/ID extract; strips outbound `jsonrpc` |
| `tools/codex_supervisor/transport.py` | JSONL stdio child process; Windows `.cmd` + process-tree stop |
| `tools/codex_supervisor/client.py` | initialize/initialized, correlation, `-32001` read-only retry |
| `tools/codex_supervisor/normalizer.py` | mechanical notification/response mapping |
| `tools/codex_supervisor/observer.py` | serve/snapshot/canary orchestration |
| `tools/codex_supervisor/timeline.py` | prose-neutral thread timeline |
| `tools/codex_supervisor/doctor.py` | read-only doctor; no App Server launch |
| `tools/codex_supervisor/cli.py` | doctor/schema/snapshot/serve/canary/timeline |
| `tools/codex_supervisor/db.py` | observer SQLite schema v1 |
| `tools/codex_supervisor/store.py` | raw-log + snapshot store; no deletion API |
| `scripts/codex-app-server-observer-*.ps1` | PowerShell 5.1 operators |
| `tests/codex_supervisor/` | 73 passing tests for the surface above |

### External runtime (never commit)

```text
%LOCALAPPDATA%\HMASD\codex-supervisor
```

Tests must use `tmp_path` and never write that directory.

---

## Plan task status

| Task | Title | Status |
|---|---|---|
| 0 | Phase 0 safety gate | DONE at `ad91385` |
| 1 | Package, policy, external runtime config | DONE locally, uncommitted |
| 2 | Codex binary + schema capture helpers | DONE locally; **live schema not captured** |
| 3 | JSONL classify / redact | DONE locally, uncommitted |
| 4 | Process transport | DONE locally against docs+schema; uncommitted |
| 5 | Handshake, correlation, safe retry | DONE locally against docs+schema; uncommitted |
| 6 | Observer SQLite + raw logs | Store v1 DONE locally; keep extending with later tasks |
| 7 | Mechanical normalizer + snapshots | DONE locally, uncommitted |
| 8 | Observer service | DONE locally against fake server |
| 9 | Read-only thread catalog | DONE locally, uncommitted |
| 10 | Timeline export | DONE locally, uncommitted |
| 11 | Explicit ephemeral canary | DONE against **fake server only** |
| 12 | Restart / EOF recovery | DONE locally, uncommitted |
| 13 | CLI / doctor / PS 5.1 operators | DONE locally; PS 5.1 test script passed |
| 14 | Reliability / negative tests | DONE locally, uncommitted |
| 15 | Live capability + canary | deferred until Codex quota is restored |
| 16 | Independent review + final gate | deferred; do together with Task 15 |

Synthetic foundation (Tasks 1–14) is pushed as `136d2904`. Tasks 15 and 16
wait for quota. Stage 3/4 live canaries wait with them.

---

## OpenAI Developer Docs MCP

Installed as **Grok user-level** MCP. Not a project dependency.

```powershell
grok mcp add --scope user --transport http openaiDeveloperDocs https://developers.openai.com/mcp
```

Verified on 2026-08-18:

```text
grok mcp list
  openaiDeveloperDocs: https://developers.openai.com/mcp

grok mcp doctor openaiDeveloperDocs
  server started
  handshake OK (protocol 2025-11-25)
  5 tools discovered
  1 healthy, 0 failing

grok inspect --json
  name: openaiDeveloperDocs
  transport: http
  target: https://developers.openai.com/mcp
  source.path: C:\Users\fires\.grok\config.toml
```

User config stanza:

```toml
[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
enabled = true
```

A previous project-level copy at `C:\Projects\HMASD\.grok\config.toml` was
**deleted**. Do not recreate it. Do not `grok mcp add --scope project`.

This MCP only searches and reads OpenAI developer documentation. It does
not call the OpenAI API and does not need an API key.

**A new Grok session is required** for the tools to appear as
`openaiDeveloperDocs__<tool-name>`. Confirm with `/mcps`; press `r` if the
list is stale.

First query after restart:

```text
使用 openaiDeveloperDocs 查询 Codex App Server 的官方文档。

查明：
1. initialize / initialized 握手顺序；
2. thread/start、thread/list、thread/read；
3. turn/start 与 turn/completed；
4. 本机 JSON Schema 生成命令。

只报告文档明确支持的内容。
列出使用的官方页面。
不要根据模型内部记忆补全未找到的字段。

然后从 Phase 1 安全边界继续 Task 4（transport）和 Task 5（client handshake）。
在文档和本机 schema 对齐之前，不要启动 live canary。
```

---

## Hard constraints (still active)

- Project Python: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`
- No Codex SDK, no OpenAI Agents SDK, no `openai/codex` fork
- No all-tools `PreToolUse`
- No `jsonrpc` field on outbound JSONL
- `initialize` then `initialized` before any other request
- Unexpected server-initiated requests terminate the owned App Server
- Error `-32001` is retryable only for classified idempotent reads
- Mutating requests are never auto-retried
- Phase 1 may start one ephemeral canary thread only via the explicit
  canary command (Task 11). No automatic `thread/start` / `turn/start` /
  `thread/resume` / `turn/steer` / `thread/compact/start` / `review/start`
- Observer events are mechanical evidence, never scientific or portfolio
  disposition. Do not invent normalized kinds named `BLOCKED`, `FAILED`,
  `SUCCESS`, `RETIRED`, `PAUSED`, `PARKED`, or `RELEASED`
- Do not change `AGENTS.md`, Roles, science cards, epochs, promotions,
  rollovers, working sets, obligations, or the semantic ledger
- Do not expose App Server mutations through `hmasd_orchestrator`
- Do not trust model-supplied `actor_context_id`, `source_kind`, role, or
  ownership
- SQLite observer DB is a ledger of mechanical facts, not semantic truth
- File hashes are never semantic gates
- Only operational Root stages, commits, or pushes
- Do not commit science cards or the unrelated dirty tree

---

## What the next session should do

1. Continue synthetic Stage 3/4 from
   `docs/research/workflow-runs/2026-08-18_codex-managed-actors/`.
2. Do not run Task 15, Task 16, or any live App Server canary until the
   user says Codex quota is restored.
3. Do not invent `LIVE_CANARY_REPORT.md` or `PHASE_1_ACCEPTANCE.md`.

---

## Explicitly not waiting / not blocked

- Research directions continue independently. This observer work is not a
  scientific stop.
- The dedicated portfolio session `019ffc20-5001-7453-a08a-dac783cf4d80`
  is unchanged and is not involved.
- Missing Docs MCP in the *previous* session was a session-load fact, not
  a direction pause. The MCP is now installed at user scope.
- Provider no-resend rules do not apply here; this is not Agentify.

---

## Suggested first user message for the new session

```text
Continue C:\Users\fires\Downloads\2026-08-18-hmasd-codex-app-server-observer-phase-1.md
from the safe boundary in
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/SESSION_HANDOFF.md

Use openaiDeveloperDocs. Do not invent protocol fields.
Do not launch a live canary until docs and local schema agree.
```
