# HMASD Codex Semantic Protocol + Hook + Long-Wait MCP MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不使用 Codex SDK/App Server、不修改 Codex Rust core、且默认不改变未托管会话行为的前提下，为 HMASD Codex Root–Subagent 工作流加入一个最小可用的语义防火墙、义务账本、Hook 生命周期守门和当前 active turn 内的 MCP 长等待，从而减少 `blocked/error/released` 等局部词汇被提升为全局命令、避免 Root 带着未 intake 的 child return 静默结束，并替代反复 `wait_agent` 轮询。

**Architecture:** 保留现有 `Root → optional L1 manager → L2 leaf` 原生 Agent tree、custom subagents、`fork_turns` 和现有权限路由；新增一个仅对显式 `workflow_open` 的托管工作流生效的 Python overlay。自然语言仍负责开放研究、代码解释和科学判断；只有控制面交接使用小型 JSON envelope。`SubagentStart` 注入通用返回契约，`SubagentStop` 持久化原文并校验 envelope，`Stop` 只检查未关闭义务；MCP server 使用 SQLite 事件游标提供最长 25 分钟的 `workflow_await_event`，等待发生在 Python runtime，而不是模型轮询。

**Tech Stack:** Windows、固定 Python `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`、Python 标准库 `sqlite3`/`asyncio`/`dataclasses`/`enum`/`json`、`mcp==2.0.0`、pytest、PowerShell、Codex repository hooks、Codex stdio MCP server。

## Plan Metadata

```text
plan_id=HMASD-CODEX-SEMANTIC-LONGWAIT-MVP-20260815-01
target_repository=CartmanFatass/My-paper-code
target_branch=aggressive
repository_root=.
primary_platform=Windows
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
runtime_state=runtime/codex-semantic-mvp
sdk_or_app_server=forbidden_in_mvp
rust_core_fork=forbidden_in_mvp
plugin_packaging=deferred
cross_turn_auto_wake=not_supported_in_mvp
cross_session_transport=manual_or_existing_native_channel_only
```

---

## 1. MVP Design Boundary

### 1.1 This MVP implements

1. An opt-in **managed workflow** opened by Root.
2. A thin **obligation protocol**, not a global scientific state machine.
3. A strict `SUBAGENT_RETURN` JSON envelope appended to otherwise free-form child output.
4. Immutable storage of raw child text separately from typed fields.
5. Automatic `ROOT_INTAKE_REQUIRED` obligations when a child returns.
6. Optional explicit obligations such as:
   - `OWNER_ROUTING_REQUIRED`
   - `FOLLOWUP_DECISION_REQUIRED`
   - `PORTFOLIO_REVIEW_REQUIRED`
   - `USER_DECISION_REQUIRED`
7. `SubagentStart`, `SubagentStop`, `Stop`, `SessionStart`, and selected `PreToolUse` hooks.
8. A long-running MCP tool:
   - `workflow_await_event`
   - maximum requested wait: `1500` seconds
   - Codex MCP `tool_timeout_sec`: `1800`
9. OFF → SHADOW → ACTIVE rollout and byte-exact rollback of the live hooks file.
10. A manual typed path for recording a Portfolio review obligation, without attempting automatic cross-session wake.

### 1.2 This MVP explicitly does not implement

- Codex SDK or App Server.
- Automatic restart of an idle/completed Root turn.
- Automatic wake of the dedicated Portfolio session.
- A free-form peer-to-peer actor mesh.
- A global research FSM such as `ACTIVE → FAILED → RETIRED`.
- Scientific truth classification.
- Automatic portfolio investment, pause, retire, or backfill.
- A persistent background daemon independent of Codex.
- Redis, Temporal, Kafka, HTTP services, or a web UI.
- Codex Rust modifications.
- Transcript-format parsing as an authoritative interface.
- Automatic interception or replacement of native `spawn_agent`, `send_message`, `followup_task`, or `wait_agent`.

### 1.3 Accepted MVP trade-off

The MVP guarantees liveness only while a Root/Portfolio turn remains active and calls `workflow_await_event`. If the turn has already completed, events remain durable in SQLite but do not wake the session. That limitation is intentional and is the boundary that a later App Server/SDK phase may address.

---

## 2. Core Model: Thin State, Strong Protocol

### 2.1 Control-plane states only

The runtime may classify only mechanical workflow facts:

```text
Task lifecycle:
DECLARED
RUNNING
RETURNED_TYPED
RETURNED_UNTYPED
INTAKEN
CANCELLED

Obligation lifecycle:
OPEN
RESOLVED
CANCELLED

Workflow lifecycle:
ACTIVE
QUIESCENT
CLOSED
CANCELLED
```

It must not classify:

```text
MECHANISM_TRUE
DIRECTION_BAD
SCIENTIFIC_FAILURE
TECHNICALLY_ACCEPTED
PORTFOLIO_RETIRED
IDEA_EXHAUSTED
```

Those remain explicit decisions by the corresponding semantic owner.

### 2.2 Non-negotiable invariants

#### I1 — No lexical control

Changing only raw wording cannot change workflow state:

```text
"BLOCKED"
"fatal error"
"I cannot continue"
"local observation unavailable"
```

All four remain raw evidence unless a typed, authority-valid control packet says something more precise.

#### I2 — A child return means only `RETURNED`

A child final message never automatically means `SUCCESS`, `FAILURE`, `BLOCKED`, `ACCEPTED`, `PAUSED`, or `RETIRED`.

#### I3 — Reports create obligations, not commands

```text
SUBAGENT_RETURN
    -> ROOT_INTAKE_REQUIRED
```

The report cannot directly cause Root closure, portfolio disposition, scientific interpretation, or technical acceptance.

#### I4 — Runtime incidents cannot cross semantic layers

```text
provider/host/tool/resource incident
    -/-> scientific stop
    -/-> technical rejection
    -/-> portfolio pause or retirement
```

#### I5 — Open obligations prevent silent closure

A managed Root turn may not close while any required report is un-intaken or any explicitly opened decision/routing obligation remains unresolved.

#### I6 — One automatic continuation maximum

For each unique guard key:

```text
SubagentStop:
(session_id, turn_id, agent_id, report_hash)

Stop:
(session_id, turn_id, workflow_state_version)
```

Codex may receive at most one automatic continuation. A second hook pass must fail open and record an audit event.

#### I7 — Natural language remains available

The child may provide rich prose before the JSON envelope. The envelope is a control summary, not a replacement for scientific or technical reasoning.

#### I8 — No automatic global direction disposition

`PORTFOLIO_REVIEW_REQUIRED` means only that Portfolio owes a decision. It does not imply exploration, no-investment, pause, backfill, or retirement.

---

## 3. Minimal Typed Protocol

### 3.1 Root task registration

Root calls `task_register` before spawning a managed child. The tool returns a footer that must be copied verbatim into the spawn assignment. After `spawn_agent` returns its `agent_id`, Root calls `task_bind`; if a very short child returns before that call, `SubagentStop` may perform a one-time fallback bind only when task id, workflow id, session, and expected agent type all match.

Example returned footer:

```text
[HMASD_MANAGED_TASK_V1]
workflow_id=wf_01J...
task_id=review_runtime_contract
return_schema=HMASD_SUBAGENT_RETURN_V1
global_disposition_authority=none
[/HMASD_MANAGED_TASK_V1]
```

### 3.2 Child final envelope

The child may write normal prose first. Its final output must end with exactly one envelope:

```text
<HMASD_SUBAGENT_RETURN_V1>
{
  "schema_version": "1.0",
  "packet_kind": "SUBAGENT_RETURN",
  "workflow_id": "wf_01J...",
  "task_id": "review_runtime_contract",
  "return_kind": "COMPLETED_ASSIGNMENT",
  "observed_facts": [
    {
      "object": "tools/example.py",
      "predicate": "function_present",
      "value": true,
      "evidence_ref": "tools/example.py:42"
    }
  ],
  "interpretive_claims": [
    "The implementation appears consistent with the bounded assignment."
  ],
  "remaining_unknowns": [
    "No production-scale runtime was authorized."
  ],
  "suggested_next_actions": [
    {
      "owner": "/root",
      "action": "Perform Root intake and decide whether a verifier is needed."
    }
  ],
  "research_frontier": null,
  "global_disposition": "NOT_ASSERTED"
}
</HMASD_SUBAGENT_RETURN_V1>
```

Allowed `return_kind` values:

```text
COMPLETED_ASSIGNMENT
PARTIAL_EVIDENCE
LOCAL_AUTHORITY_BOUNDARY
MECHANICAL_INCIDENT
```

`LOCAL_AUTHORITY_BOUNDARY` means only that the reporting actor has no authorized next action. It does not mean the parent, workflow, direction, or project is blocked.

Optional `research_frontier` shape:

```json
{
  "current_question": "What remains unresolved?",
  "strongest_live_alternative": "The best remaining alternative.",
  "claim_ceiling": "Maximum currently supported claim.",
  "next_discriminator": "Highest-information prospective discriminator, if known.",
  "exploration_debt": [
    "Known route not yet examined."
  ]
}
```

### 3.3 Root intake packet

Root closes a report obligation by calling `root_record_intake`:

```json
{
  "report_id": "rep_01J...",
  "intake_kind": "ROUTE_OWNER",
  "translation": {
    "exact_observed_fact": "The child did not observe the named URL in its assigned tab.",
    "exact_object": "the assigned Agentify tab",
    "remaining_unknown": "whether another native tab contains the conversation",
    "global_effect": "NONE"
  },
  "next_action": {
    "owner": "/root/project-scout",
    "action": "Reconcile the exact native tabs."
  },
  "note": "Child wording is evidence only; no global blockage is inferred."
}
```

Allowed `intake_kind` values:

```text
INTEGRATE
FOLLOWUP
ROUTE_OWNER
CANCEL_AUTHORIZED
ESCALATE_USER
```

### 3.4 Explicit liveness obligation

Root may open a non-child obligation:

```json
{
  "kind": "PORTFOLIO_REVIEW_REQUIRED",
  "subject": "direction:onlgr",
  "reason": "Stage completed and pair context was released without next-stage authorization or an explicit portfolio disposition.",
  "owner": "dedicated_portfolio_session",
  "source_ref": "stage:onlgr-b2"
}
```

This keeps the direction visible without deciding what Portfolio must conclude.

---

## 4. File Structure

```text
tools/
└── codex_semantic_mvp/
    ├── __init__.py
    ├── constants.py
    ├── models.py
    ├── protocol.py
    ├── db.py
    ├── store.py
    ├── hook_entry.py
    ├── mcp_server.py
    ├── cli.py
    └── doctor.py

tests/
└── codex_semantic_mvp/
    ├── __init__.py
    ├── conftest.py
    ├── test_protocol.py
    ├── test_store.py
    ├── test_hooks_shadow.py
    ├── test_hooks_active.py
    ├── test_mcp_tools.py
    ├── test_long_wait.py
    ├── test_semantic_canaries.py
    └── test_activation_assets.py

.codex/
├── hooks.json                                  # preserved until activation gate
├── hooks.semantic-mvp.shadow.json
└── hooks.semantic-mvp.active.json

scripts/
├── codex-semantic-mvp-doctor.ps1
├── codex-semantic-mvp-enable.ps1
├── codex-semantic-mvp-disable.ps1
└── codex-semantic-mvp-test.ps1

docs/
└── superpowers/
    └── plans/
        └── 2026-08-15-hmasd-codex-semantic-longwait-mvp-plan.md

runtime/
└── codex-semantic-mvp/                        # gitignored
    ├── state.sqlite3
    ├── audit.jsonl
    ├── baseline.json
    └── backups/
```

Each Python file has one responsibility:

| File | Responsibility |
|---|---|
| `constants.py` | enum string values, markers, limits |
| `models.py` | frozen dataclasses and validation errors |
| `protocol.py` | envelope extraction, JSON validation, hazard annotation |
| `db.py` | connection configuration and migrations |
| `store.py` | transactional repository and query methods |
| `hook_entry.py` | stdin hook dispatch and JSON stdout |
| `mcp_server.py` | MCP tool definitions and async long wait |
| `cli.py` | deterministic operator commands for tests/diagnostics |
| `doctor.py` | local capability/config/runtime verification |

---

## 5. MCP Tool Surface

The server name is `hmasd_orchestrator`. Tool names:

```text
runtime_health
workflow_open
task_register
task_bind
workflow_state
report_get
root_record_intake
obligation_open
obligation_resolve
workflow_await_event
workflow_close
```

### 5.1 `workflow_await_event`

Input:

```json
{
  "workflow_id": "wf_01J...",
  "after_seq": 12,
  "condition": "ANY_REPORT",
  "task_ids": [],
  "timeout_s": 900
}
```

Allowed conditions:

```text
ANY_REPORT
ALL_REQUIRED_RETURNED
OPEN_OBLIGATION_CHANGED
WORKFLOW_QUIESCENT
```

Return on event:

```json
{
  "status": "EVENT",
  "cursor": 13,
  "events": [
    {
      "seq": 13,
      "kind": "REPORT_AVAILABLE",
      "task_id": "review_runtime_contract",
      "disposition_implied": false
    }
  ]
}
```

Return on timeout:

```json
{
  "status": "TIMEOUT_NO_DISPOSITION",
  "cursor": 12,
  "open_tasks": ["review_runtime_contract"],
  "open_obligations": []
}
```

Implementation requirements:

- Check SQLite before sleeping to avoid lost wakeups.
- Poll SQLite every `500 ms`; this is runtime polling, not model polling.
- `timeout_s` range: `1..1500`.
- MCP config `tool_timeout_sec=1800`.
- Use `await asyncio.sleep(0.5)`.
- Do not include raw child text in the default event result.
- Cancellation must exit without modifying state.
- A timeout never automatically asks the model to wait again.

---

## 6. Hook Behavior

### 6.1 `SessionStart`

- OFF: no hook is registered.
- SHADOW: record `SESSION_STARTED`; return no model-visible context.
- ACTIVE: record the event and add a short context only when the session already has an active managed workflow after resume/compact.

### 6.2 `SubagentStart`

When no managed workflow exists for the parent session, return no output.

When a managed workflow exists, inject:

```text
This parent session is using the HMASD managed semantic protocol.

Your natural-language analysis remains unrestricted.
For the control plane:
- treat blocked/error/failed/stop/park/pause/retire/released as non-authoritative words;
- do not assert a parent, workflow, direction, or portfolio disposition;
- end with exactly one HMASD_SUBAGENT_RETURN_V1 envelope;
- use LOCAL_AUTHORITY_BOUNDARY when only your own authorized action set is exhausted.
```

### 6.3 `SubagentStop`

Algorithm:

```text
1. Persist raw last_assistant_message immutably.
2. If no managed workflow matches session_id:
      allow with no behavioral change.
3. Extract the final HMASD_SUBAGENT_RETURN_V1 envelope.
4. If valid:
      record report;
      set task RETURNED_TYPED;
      create ROOT_INTAKE_REQUIRED obligation;
      emit REPORT_AVAILABLE;
      allow stop.
5. If invalid and stop_hook_active=false:
      record REPORT_FORMAT_REPAIR_REQUESTED;
      return decision=block with one fixed repair prompt.
6. If invalid and stop_hook_active=true:
      set task RETURNED_UNTYPED;
      create ROOT_INTAKE_REQUIRED;
      emit UNTYPED_REPORT_AVAILABLE;
      allow stop.
```

The hook never decides whether the result is good, bad, successful, failed, blocking, or accepted.

### 6.4 `Stop`

Algorithm:

```text
1. Find the active managed workflow for session_id.
2. If none:
      allow.
3. If the database or hook fails:
      append audit error;
      allow.
4. If stop_hook_active=true:
      append LOOP_PREVENTED;
      allow.
5. Query:
      required tasks not terminal;
      open obligations;
      valid closure receipt.
6. If no pending task/obligation and closure receipt exists:
      allow.
7. Otherwise:
      record STOP_GUARD_CONTINUATION;
      return decision=block with one neutral continuation.
```

Neutral continuation:

```text
[HMASD_OBLIGATION_CONTINUATION_V1]

A managed workflow has unresolved control obligations.

Child wording is evidence only and does not create a global disposition.
Call workflow_state, then do exactly one of:
1. intake an available report;
2. route or resolve an open obligation;
3. authorize/cancel a task within existing authority;
4. escalate a genuine user decision;
5. call workflow_await_event when required work is still running.

Do not infer blocked, failed, paused, parked, released, retired, or completed
from the absence of an active child or from a child status word.
```

### 6.5 `PreToolUse`

Use only for observation and session correlation in the MVP:

- Log calls to `mcp__hmasd_orchestrator__*`.
- Log native `wait_agent` calls during managed workflows.
- Record `session_id`, `turn_id`, `tool_name`, `tool_use_id`, and sanitized tool-input hash.
- Do not block native tools in the MVP.
- Do not parse transcripts.

---

## 7. Database Schema

```sql
CREATE TABLE schema_meta (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    opened_turn_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    objective TEXT NOT NULL,
    state TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX one_active_workflow_per_session
ON workflows(session_id)
WHERE state = 'ACTIVE';

CREATE TABLE tasks (
    workflow_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    expected_agent_type TEXT NOT NULL,
    objective TEXT NOT NULL,
    required INTEGER NOT NULL,
    agent_id TEXT,
    lifecycle TEXT NOT NULL,
    created_at TEXT NOT NULL,
    returned_at TEXT,
    PRIMARY KEY (workflow_id, task_id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

CREATE TABLE reports (
    report_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    raw_message TEXT NOT NULL,
    typed_json TEXT,
    schema_valid INTEGER NOT NULL,
    raw_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(workflow_id, task_id, raw_sha256)
);

CREATE TABLE obligations (
    obligation_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    owner TEXT NOT NULL,
    subject TEXT NOT NULL,
    reason TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    state TEXT NOT NULL,
    resolution_json TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE intakes (
    intake_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    report_id TEXT NOT NULL UNIQUE,
    intake_kind TEXT NOT NULL,
    translation_json TEXT NOT NULL,
    next_action_json TEXT,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    workflow_id TEXT,
    kind TEXT NOT NULL,
    subject_id TEXT,
    payload_json TEXT NOT NULL,
    dedupe_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE hook_guards (
    guard_key TEXT PRIMARY KEY,
    event_name TEXT NOT NULL,
    count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE closure_receipts (
    receipt_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL UNIQUE,
    closure_kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

SQLite settings:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
```

---

## 8. Global Constraints

1. Use an isolated worktree during implementation.
2. Read `AGENTS.md`, `.agents/roles/ROOT.md`, `.codex/config.toml`, and `.codex/hooks.json` before editing.
3. Preserve `multi_agent_v2=true`, `max_threads=40`, and `max_depth=2`.
4. Preserve the existing `.codex/hooks.json` bytes until the explicit live activation gate.
5. Every project Python command uses:

   ```text
   C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
   ```

6. Pin `mcp==2.0.0`; do not use an alpha/beta build and do not copy v1 `FastMCP` examples.
7. Runtime state stays outside Git under `runtime/codex-semantic-mvp/`.
8. Tests use temporary SQLite directories and never touch live runtime state.
9. No hook may take longer than `2 seconds` in normal operation.
10. Hook/database errors fail open with audit evidence.
11. Semantic/authority violations fail closed only inside MCP validation; they must not lock the Codex turn.
12. The overlay is an accidental-drift correctness boundary, not a hostile-local-process security boundary.
13. MCP caller identity is session-correlated but not yet cryptographically actor-authenticated; child profiles remain prohibited by Role from calling Root-only write tools.
14. No live hook activation until all unit tests and the SHADOW canary pass.
15. No App Server/SDK code or dependency may appear in this MVP diff.
16. No task changes scientific cards, treatments, seeds, thresholds, provider conversations, experiments, or portfolio allocations.

---

# Implementation Tasks

## Task 1: Freeze the Baseline and Create the Package Skeleton

**Files:**
- Create: `tools/codex_semantic_mvp/__init__.py`
- Create: `tools/codex_semantic_mvp/constants.py`
- Create: `tests/codex_semantic_mvp/__init__.py`
- Create: `tests/codex_semantic_mvp/conftest.py`
- Create: `tools/codex_semantic_mvp/doctor.py`
- Test: `tests/codex_semantic_mvp/test_activation_assets.py`
- Modify only if absent: `.gitignore`

**Interfaces:**
- Produces: mode string constants, `STATE_DIR_ENV`, `KILL_SWITCH_ENV`, marker constants, and `doctor.collect_baseline()`.
- Consumes: existing `.codex/config.toml`, `.codex/hooks.json`.

- [ ] **Step 1: Capture the current files and hashes before editing**

Run in PowerShell:

```powershell
Set-Location .
$python = 'C:\Users\wu\.conda\envs\SB3\python.exe'
Get-FileHash .codex\config.toml -Algorithm SHA256
Get-FileHash .codex\hooks.json -Algorithm SHA256
codex --version
& $python --version
```

Expected:
- both files exist;
- `.codex/hooks.json` still contains an empty `hooks` object;
- command output is copied into the task evidence packet.

- [ ] **Step 2: Write the failing constants and baseline tests**

Create tests asserting:

```python
from pathlib import Path

from tools.codex_semantic_mvp.constants import (
    ACTIVE_MODE,
    OFF_MODE,
    SHADOW_MODE,
    STATE_DIR_ENV,
)
from tools.codex_semantic_mvp.doctor import collect_baseline


def test_mode_constants_are_exact():
    assert (OFF_MODE, SHADOW_MODE, ACTIVE_MODE) == ("off", "shadow", "active")
    assert STATE_DIR_ENV == "HMASD_CODEX_MVP_STATE_DIR"


def test_collect_baseline_hashes_both_codex_files(repo_root: Path):
    result = collect_baseline(repo_root)
    assert result["config_toml"]["sha256"]
    assert result["hooks_json"]["sha256"]
    assert result["hooks_json"]["path"].endswith(".codex/hooks.json")
```

- [ ] **Step 3: Run tests and observe failure**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_activation_assets.py -q
```

Expected: import failure because the package functions do not exist.

- [ ] **Step 4: Implement constants and baseline collection**

`constants.py` must define:

```python
OFF_MODE = "off"
SHADOW_MODE = "shadow"
ACTIVE_MODE = "active"
STATE_DIR_ENV = "HMASD_CODEX_MVP_STATE_DIR"
KILL_SWITCH_ENV = "HMASD_CODEX_MVP_DISABLE"

RETURN_START = "<HMASD_SUBAGENT_RETURN_V1>"
RETURN_END = "</HMASD_SUBAGENT_RETURN_V1>"

MAX_RAW_MESSAGE_BYTES = 1_000_000
MAX_TYPED_JSON_BYTES = 32_768
MAX_WAIT_SECONDS = 1500
WAIT_POLL_SECONDS = 0.5
```

`collect_baseline()` returns SHA-256, size, and path for both live Codex files.

- [ ] **Step 5: Add the runtime ignore only if not already covered**

Add exactly:

```gitignore
/runtime/codex-semantic-mvp/
```

Do not ignore the implementation or test directories.

- [ ] **Step 6: Run the targeted tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_activation_assets.py -q
```

Expected: PASS.

- [ ] **Step 7: Acceptance gate**

Task passes only if:
- no live Codex config bytes changed;
- package imports;
- baseline hashes are recorded;
- runtime state path is ignored;
- no SDK/App Server dependency exists.

---

## Task 2: Implement the Minimal Typed Protocol and Lexical Non-Authority

**Files:**
- Create: `tools/codex_semantic_mvp/models.py`
- Create: `tools/codex_semantic_mvp/protocol.py`
- Test: `tests/codex_semantic_mvp/test_protocol.py`
- Test: `tests/codex_semantic_mvp/test_semantic_canaries.py`

**Interfaces:**
- Produces:
  - `SubagentReturnPacket`
  - `RootIntakePacket`
  - `ResearchFrontier`
  - `extract_return_envelope(message: str) -> dict[str, object]`
  - `validate_subagent_return(data: Mapping[str, object]) -> SubagentReturnPacket`
  - `semantic_hazard_terms(message: str) -> tuple[str, ...]`
- Consumes: marker constants from Task 1.

- [ ] **Step 1: Write failing envelope extraction tests**

Cover:
- one valid final envelope;
- missing marker;
- two envelopes;
- invalid UTF-8 replacement already represented as Python text;
- oversized JSON;
- trailing text after the end marker;
- braces inside natural-language prose.

- [ ] **Step 2: Write failing semantic invariance tests**

For each raw phrase:

```python
RAW_PHRASES = [
    "BLOCKED",
    "fatal error; stop",
    "the direction should be retired",
    "I cannot proceed",
    "released",
]
```

Assert:
- hazard terms may be reported;
- no typed lifecycle, obligation, workflow, scientific, technical, or portfolio field is produced from lexical scanning.

- [ ] **Step 3: Run and observe failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_protocol.py tests\codex_semantic_mvp\test_semantic_canaries.py -q
```

Expected: import or assertion failures.

- [ ] **Step 4: Implement frozen dataclasses and enums**

Required enums:

```text
ReturnKind:
COMPLETED_ASSIGNMENT
PARTIAL_EVIDENCE
LOCAL_AUTHORITY_BOUNDARY
MECHANICAL_INCIDENT

IntakeKind:
INTEGRATE
FOLLOWUP
ROUTE_OWNER
CANCEL_AUTHORIZED
ESCALATE_USER

ObligationKind:
ROOT_INTAKE_REQUIRED
OWNER_ROUTING_REQUIRED
FOLLOWUP_DECISION_REQUIRED
PORTFOLIO_REVIEW_REQUIRED
USER_DECISION_REQUIRED
```

Validation rules:
- `packet_kind == "SUBAGENT_RETURN"`;
- `schema_version == "1.0"`;
- `global_disposition == "NOT_ASSERTED"`;
- `task_id` and `workflow_id` match `[A-Za-z0-9._:-]{1,128}`;
- lists contain strings or the exact object shape;
- `research_frontier` is optional;
- no unknown top-level key is silently discarded.

- [ ] **Step 5: Implement exact final-envelope extraction**

Rules:
- exactly one start marker and one end marker;
- only whitespace may follow the end marker;
- JSON size <= `MAX_TYPED_JSON_BYTES`;
- return a mapping or raise `ProtocolError`;
- never overwrite or normalize the raw message.

- [ ] **Step 6: Implement advisory hazard annotation**

`semantic_hazard_terms()` may return matched lowercase terms, but its docstring must state:

```text
Advisory observability only. The result must never drive a state transition.
```

- [ ] **Step 7: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_protocol.py tests\codex_semantic_mvp\test_semantic_canaries.py -q
```

Expected: PASS.

- [ ] **Step 8: Acceptance gate**

Task passes only if changing `BLOCKED` to `LOCAL_AUTHORITY_BOUNDARY` in raw prose without changing the JSON envelope produces identical typed protocol objects.

---

## Task 3: Implement the SQLite Event and Obligation Store

**Files:**
- Create: `tools/codex_semantic_mvp/db.py`
- Create: `tools/codex_semantic_mvp/store.py`
- Test: `tests/codex_semantic_mvp/test_store.py`

**Interfaces:**
- Produces `SemanticStore` with:
  - `initialize()`
  - `open_workflow()`
  - `register_task()`
  - `record_agent_started()`
  - `record_report()`
  - `record_untyped_return()`
  - `record_intake()`
  - `open_obligation()`
  - `resolve_obligation()`
  - `events_after()`
  - `workflow_state()`
  - `create_closure_receipt()`
  - `acquire_guard_once()`
- Consumes typed models from Task 2.

- [ ] **Step 1: Write failing migration tests**

Assert:
- first initialization creates all tables;
- second initialization is idempotent;
- foreign keys are enabled;
- WAL mode is active;
- one active workflow per session is enforced.

- [ ] **Step 2: Write failing transactional tests**

Cover:
- duplicate `SubagentStop` event is deduplicated;
- valid report and `ROOT_INTAKE_REQUIRED` are created in one transaction;
- intake resolves exactly its report obligation;
- unrelated obligations remain open;
- event sequence increases monotonically;
- raw report text remains byte-for-byte identical.

- [ ] **Step 3: Run failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_store.py -q
```

Expected: failure before implementation.

- [ ] **Step 4: Implement connection and migrations**

Every connection applies:

```python
connection.execute("PRAGMA foreign_keys = ON")
connection.execute("PRAGMA busy_timeout = 5000")
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA synchronous = FULL")
```

Use explicit transactions:

```python
with connection:
    ...
```

- [ ] **Step 5: Implement neutral task/report transitions**

Rules:
- valid report -> `RETURNED_TYPED`;
- invalid second return -> `RETURNED_UNTYPED`;
- intake -> `INTAKEN`;
- no method accepts `SUCCESS`, `FAILURE`, `BLOCKED`, or `RETIRED`.

- [ ] **Step 6: Implement guard deduplication**

`acquire_guard_once(guard_key, event_name)` returns:
- `True` on first use;
- `False` on every later use.

- [ ] **Step 7: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_store.py -q
```

Expected: PASS.

- [ ] **Step 8: Concurrency canary**

Run a test with 20 threads writing distinct events and duplicate dedupe keys.

Expected:
- no database corruption;
- distinct events persist;
- duplicates remain one row.

- [ ] **Step 9: Acceptance gate**

Task passes only if a report, obligation, and event are either all committed or all absent after an injected exception.

---

## Task 4: Build SHADOW Hooks With Zero Behavioral Effect

**Files:**
- Create: `tools/codex_semantic_mvp/hook_entry.py`
- Create: `.codex/hooks.semantic-mvp.shadow.json`
- Test: `tests/codex_semantic_mvp/test_hooks_shadow.py`

**Interfaces:**
- Produces:
  - `handle_hook(payload: Mapping[str, object], mode: str, store: SemanticStore) -> dict[str, object] | None`
  - CLI entry: `python -m tools.codex_semantic_mvp.hook_entry`
- Consumes store and protocol modules.

- [ ] **Step 1: Write failing hook input tests**

Cover:
- `SessionStart`;
- `SubagentStart`;
- `SubagentStop`;
- `Stop`;
- `PreToolUse`;
- malformed JSON;
- unknown hook event;
- missing state directory.

- [ ] **Step 2: Write the shadow-mode noninterference assertion**

For every supported event in SHADOW mode:
- persist a diagnostic event when possible;
- return either no stdout or `{"continue": true}`;
- never return `decision: "block"`;
- never add `additionalContext`;
- exit code `0`.

- [ ] **Step 3: Run failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_hooks_shadow.py -q
```

- [ ] **Step 4: Implement the hook entrypoint**

Requirements:
- read exactly one JSON object from stdin;
- write JSON only when the event requires JSON;
- write diagnostics to `audit.jsonl`, never stdout;
- truncate audit previews, not raw report storage;
- complete under `2 seconds`.

- [ ] **Step 5: Create the SHADOW hook template**

Register:
- `SessionStart`
- `SubagentStart`
- `SubagentStop`
- `Stop`
- `PreToolUse`

Each command uses the fixed Python executable and:

```text
-m tools.codex_semantic_mvp.hook_entry
```

Set a bounded hook timeout of `5` seconds.

- [ ] **Step 6: Test the template as JSON**

```powershell
& $python -m json.tool .codex\hooks.semantic-mvp.shadow.json > $null
```

Expected: exit `0`.

- [ ] **Step 7: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_hooks_shadow.py -q
```

Expected: PASS.

- [ ] **Step 8: Acceptance gate**

The live `.codex/hooks.json` hash must remain identical to Task 1.

---

## Task 5: Implement the MCP Server and Basic Workflow Tools

**Files:**
- Create: `tools/codex_semantic_mvp/mcp_server.py`
- Create: `tools/codex_semantic_mvp/cli.py`
- Test: `tests/codex_semantic_mvp/test_mcp_tools.py`
- Modify later at gate: `.codex/config.toml`

**Interfaces:**
- Produces all tools listed in Section 5.
- Consumes `SemanticStore`.

- [ ] **Step 1: Install the exact stable MCP dependency**

```powershell
& $python -m pip install "mcp==2.0.0"
& $python -c "import mcp; print(mcp.__version__ if hasattr(mcp, '__version__') else 'mcp-import-ok')"
```

Record pip output and installed package metadata:

```powershell
& $python -m pip show mcp
```

- [ ] **Step 2: Write failing in-memory MCP tests**

Use the MCP v2 in-memory client/server path. Cover:
- `runtime_health`;
- `workflow_open`;
- duplicate active workflow rejection;
- `task_register` footer output;
- `task_bind` changes a declared task to `RUNNING`;
- `workflow_state`;
- `root_record_intake`;
- explicit `PORTFOLIO_REVIEW_REQUIRED`;
- invalid obligation kind;
- `workflow_close` with open obligations rejected.

- [ ] **Step 3: Run failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_mcp_tools.py -q
```

- [ ] **Step 4: Implement `MCPServer`**

Use the current v2 API:

```python
from mcp.server import MCPServer

mcp = MCPServer("hmasd_orchestrator")
```

Tool functions return JSON-serializable dictionaries. Do not return prose-only status.

The module entrypoint must end with:

```python
if __name__ == "__main__":
    mcp.run()
```

`run()` uses stdio by default and must not print to stdout before the MCP
transport starts.

- [ ] **Step 5: Implement `task_register` dispatch footer**

The footer includes:
- workflow id;
- task id;
- schema name;
- `global_disposition_authority=none`.

It must not include hidden secrets or user authority.

- [ ] **Step 6: Implement `workflow_close` validation**

Allow closure only when:
- all required tasks are `INTAKEN` or `CANCELLED`;
- all obligations are resolved/cancelled;
- closure kind is one of:

```text
COMPLETED
USER_CANCELLED
SCOPE_TRANSFERRED
DEFERRED_BY_USER
GOAL_BLOCKED_AFTER_AUDIT
```

`GOAL_BLOCKED_AFTER_AUDIT` is recorded but this MVP does not independently prove the scientific adequacy of the audit.

- [ ] **Step 7: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_mcp_tools.py -q
```

Expected: PASS.

- [ ] **Step 8: Add a disabled MCP config block**

Append one marker-delimited block to `.codex/config.toml`:

```toml
# BEGIN HMASD CODEX SEMANTIC MVP
[mcp_servers.hmasd_orchestrator]
command = "C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe"
args = [
  "-m",
  "tools.codex_semantic_mvp.mcp_server",
  "--state-dir",
  "C:\\Projects\\HMASD\\runtime\\codex-semantic-mvp"
]
startup_timeout_sec = 15
tool_timeout_sec = 1800
enabled = false
required = false
# END HMASD CODEX SEMANTIC MVP
```

Do not modify any existing agent or MCP entry.

- [ ] **Step 9: Acceptance gate**

`codex mcp list` must show the server configuration as disabled, and all pre-existing MCP entries must remain unchanged.

---

## Task 6: Implement the Long-Wait Event Cursor

**Files:**
- Modify: `tools/codex_semantic_mvp/mcp_server.py`
- Modify: `tools/codex_semantic_mvp/store.py`
- Test: `tests/codex_semantic_mvp/test_long_wait.py`

**Interfaces:**
- Produces `await_events(...)` and MCP tool `workflow_await_event`.

- [ ] **Step 1: Write failing immediate-event test**

Insert an event before calling the tool.

Expected tool response:
- returns immediately;
- `status == "EVENT"`;
- cursor advances;
- no raw report body is returned.

- [ ] **Step 2: Write failing delayed-event test**

Start `workflow_await_event` with timeout `5` seconds, then insert an event after `1` second.

Expected:
- elapsed time between `0.8` and `2.5` seconds;
- exactly one result;
- no repeated model/tool call is involved.

- [ ] **Step 3: Write timeout and cancellation tests**

Expected timeout:

```json
{
  "status": "TIMEOUT_NO_DISPOSITION"
}
```

Expected cancellation:
- coroutine exits;
- no workflow/task/obligation state changes;
- no synthetic timeout event is inserted unless cancellation handling explicitly records `AWAIT_CANCELLED`.

- [ ] **Step 4: Run failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_long_wait.py -q
```

- [ ] **Step 5: Implement cursor-first waiting**

Pseudo-code:

```python
deadline = monotonic() + timeout_s
while True:
    events = store.events_after(workflow_id, after_seq)
    if condition_met(events, store.workflow_state(workflow_id)):
        return make_neutral_result(events)
    remaining = deadline - monotonic()
    if remaining <= 0:
        return make_timeout_result()
    await asyncio.sleep(min(WAIT_POLL_SECONDS, remaining))
```

- [ ] **Step 6: Enforce bounds**

Reject:
- `timeout_s < 1`;
- `timeout_s > 1500`;
- unknown conditions;
- task ids outside the workflow.

- [ ] **Step 7: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_long_wait.py -q
```

Expected: PASS.

- [ ] **Step 8: 120-second runtime canary**

Use the CLI to open a test workflow, start a wait, and insert an event from a second process after `120` seconds.

Expected:
- one MCP/runtime wait;
- one return;
- no 60-second timeout cycle;
- CPU usage remains negligible.

- [ ] **Step 9: Acceptance gate**

The tool must survive a wait longer than Codex's default MCP timeout only after the configured `tool_timeout_sec=1800` block is enabled in a controlled test profile.

---

## Task 7: Activate Typed Subagent Start/Stop Semantics

**Files:**
- Modify: `tools/codex_semantic_mvp/hook_entry.py`
- Create: `.codex/hooks.semantic-mvp.active.json`
- Test: `tests/codex_semantic_mvp/test_hooks_active.py`

**Interfaces:**
- Produces the exact SubagentStart context and one-shot SubagentStop repair continuation.

- [ ] **Step 1: Write failing managed/unmanaged tests**

Assert:
- unmanaged session: no additional context and no block;
- managed session: SubagentStart adds the generic contract;
- valid report: allowed and obligation created;
- missing report first pass: one `decision: block`;
- missing report second pass with `stop_hook_active=true`: allowed as `RETURNED_UNTYPED`.

- [ ] **Step 2: Write the exact repair continuation test**

Expected reason must contain:
- `Do not redo the investigation`;
- required envelope fields;
- prohibition on global `blocked/failed/paused/retired` assertions.

It must not contain the child's raw status phrase.

- [ ] **Step 3: Run failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_hooks_active.py -q
```

- [ ] **Step 4: Implement managed-session lookup**

A hook becomes active only if:
- `session_id` has one ACTIVE managed workflow;
- mode is `active`.

Otherwise it is a no-op.

- [ ] **Step 5: Implement valid report binding**

At `SubagentStop`:
- report `workflow_id` must match the session workflow;
- `task_id` must exist;
- `expected_agent_type` must equal hook `agent_type`;
- if task has no `agent_id`, bind the hook `agent_id`;
- if already bound to another id, reject as untyped and audit the mismatch.

- [ ] **Step 6: Implement one-shot format repair**

Use both:
- Codex `stop_hook_active`;
- durable `hook_guards`.

Either one indicating prior continuation prevents a second block.

- [ ] **Step 7: Create active hook template**

Same handlers as SHADOW. The ACTIVE template invokes the hook entrypoint with `--mode active`; the
SHADOW template uses `--mode shadow`. Do not depend on changing the parent
Codex process environment after startup. `HMASD_CODEX_MVP_DISABLE=1` is an
emergency no-op kill switch when it is present before the Codex process starts.

The template itself must not contain scientific or portfolio instructions.

- [ ] **Step 8: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_hooks_active.py -q
```

Expected: PASS.

- [ ] **Step 9: Acceptance gate**

A child may literally write `BLOCKED; stop everything` in prose, but if its envelope says `LOCAL_AUTHORITY_BOUNDARY` and `global_disposition=NOT_ASSERTED`, the stored lifecycle must be `RETURNED_TYPED` and the only automatic result must be `ROOT_INTAKE_REQUIRED`.

---

## Task 8: Implement the Root Stop Obligation Guard

**Files:**
- Modify: `tools/codex_semantic_mvp/hook_entry.py`
- Test: `tests/codex_semantic_mvp/test_hooks_active.py`
- Test: `tests/codex_semantic_mvp/test_semantic_canaries.py`

**Interfaces:**
- Produces one neutral Stop continuation per state version.

- [ ] **Step 1: Write failing guard tests**

Cover:
- running required task;
- typed report awaiting intake;
- untyped report awaiting intake;
- explicit `PORTFOLIO_REVIEW_REQUIRED`;
- no open obligations with closure receipt;
- second Stop pass with `stop_hook_active=true`;
- SQLite exception.

- [ ] **Step 2: Run failures**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_hooks_active.py tests\codex_semantic_mvp\test_semantic_canaries.py -q
```

- [ ] **Step 3: Implement the guard**

The Stop hook must query only typed store state. It must never search `last_assistant_message` for status words.

- [ ] **Step 4: Implement fail-open audit**

On store error:
- append `STOP_GUARD_FAIL_OPEN`;
- include exception class but no secret payload;
- return `{"continue": true}`.

- [ ] **Step 5: Test one-shot behavior**

First Stop:
- `decision=block`.

Second Stop with unchanged state:
- allow;
- event `LOOP_PREVENTED`.

After state version changes:
- one new continuation may occur.

- [ ] **Step 6: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_hooks_active.py tests\codex_semantic_mvp\test_semantic_canaries.py -q
```

Expected: PASS.

- [ ] **Step 7: Acceptance gate**

Root cannot silently close a managed workflow containing an un-intaken report or a manually opened Portfolio review obligation, but a broken hook/store cannot trap the user indefinitely.

---

## Task 9: Add Safe OFF/SHADOW/ACTIVE Activation and Byte-Exact Rollback

**Files:**
- Create: `scripts/codex-semantic-mvp-doctor.ps1`
- Create: `scripts/codex-semantic-mvp-enable.ps1`
- Create: `scripts/codex-semantic-mvp-disable.ps1`
- Create: `scripts/codex-semantic-mvp-test.ps1`
- Modify: `tools/codex_semantic_mvp/doctor.py`
- Test: `tests/codex_semantic_mvp/test_activation_assets.py`

**Interfaces:**
- Produces deterministic operator commands.
- Consumes hook templates and config marker block.

- [ ] **Step 1: Write failing activation-asset tests**

Assert:
- both templates are valid JSON;
- live file is not one of the templates before activation;
- config has exactly one marker block;
- configured Python path is exact;
- `tool_timeout_sec == 1800`;
- server starts disabled.

- [ ] **Step 2: Implement doctor checks**

Doctor must print machine-readable JSON including:

```json
{
  "live_hooks_hash": "...",
  "config_hash": "...",
  "mcp_version": "2.0.0",
  "server_config_present": true,
  "server_enabled": false,
  "runtime_writable": true,
  "mode": "off"
}
```

- [ ] **Step 3: Implement enable script**

Parameters:

```powershell
-Mode Shadow
-Mode Active
```

Behavior:
1. verify current live hook hash matches the recorded baseline or latest known backup;
2. copy live hooks file into runtime `backups/`;
3. atomically replace `.codex/hooks.json`;
4. copy the template whose command line declares the requested mode;
5. enable the MCP marker block only for ACTIVE;
6. print new hashes;
7. never edit any agent profile.

- [ ] **Step 4: Implement disable script**

Behavior:
1. restore the exact backup bytes;
2. set MCP block back to `enabled = false`;
3. retain SQLite and audit evidence;
4. verify restored SHA-256;
5. print `ROLLBACK_VERIFIED=true`.

- [ ] **Step 5: Implement test script**

Runs:

```powershell
& $python -m pytest tests\codex_semantic_mvp -q
& $python -m tools.codex_semantic_mvp.doctor --repo-root .
```

- [ ] **Step 6: Run tests**

```powershell
& $python -m pytest tests\codex_semantic_mvp\test_activation_assets.py -q
```

Expected: PASS.

- [ ] **Step 7: Dry-run SHADOW enable/disable in a temporary copy**

Do not touch live config. Validate backup, copy, and restore logic against temp files.

- [ ] **Step 8: Review hook sources in Codex**

After enabling SHADOW or ACTIVE, open `/hooks` in Codex and verify:
- the repository hook file is the expected template;
- no unexpected duplicate repository source exists;
- any global/user hooks are listed separately;
- the new command hooks are explicitly trusted before the canary.

- [ ] **Step 9: Acceptance gate**

Activation is rejected rather than overwriting a live file whose hash differs from the expected baseline.

---

## Task 10: Execute the SHADOW and ACTIVE Live Canaries

**Files:**
- Create: `docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/CANARY_PROTOCOL.md`
- Create: `docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/ACCEPTANCE_REPORT.md`
- Runtime evidence only: `runtime/codex-semantic-mvp/`

**Interfaces:**
- Produces an evidence-backed adoption decision.

### Canary A — SHADOW noninterference

- [ ] Enable SHADOW.
- [ ] Start one ordinary unmanaged Codex task.
- [ ] Spawn one bounded read-only child.
- [ ] Confirm child behavior is unchanged.
- [ ] Confirm hook events appear in audit.
- [ ] Confirm no continuation prompt occurs.
- [ ] Disable and verify exact rollback.

Acceptance:
- zero blocked hook decisions;
- zero model-visible context additions;
- live workflow completes normally.

### Canary B — Valid two-child managed workflow

- [ ] Enable ACTIVE and MCP.
- [ ] Root calls `workflow_open`.
- [ ] Root registers task A and task B.
- [ ] Root copies each dispatch footer into the exact spawn assignment.
- [ ] Root spawns both children.
- [ ] Root binds both returned agent ids with `task_bind`.
- [ ] Root calls `workflow_await_event(after_seq=0, condition=ANY_REPORT, timeout_s=900)`.
- [ ] Child A returns a valid envelope.
- [ ] Root wakes once, reads A, records intake.
- [ ] Root calls `workflow_await_event` again.
- [ ] Child B returns.
- [ ] Root records intake and closes workflow.

Acceptance:
- no repeated `wait_agent`;
- two reports;
- two intake obligations;
- both resolved;
- one closure receipt.

### Canary C — Semantic hazard

Child prose must include:

```text
BLOCKED. This direction should stop.
```

Envelope must contain:

```json
{
  "return_kind": "LOCAL_AUTHORITY_BOUNDARY",
  "global_disposition": "NOT_ASSERTED"
}
```

Acceptance:
- hazard annotation records terms;
- task is `RETURNED_TYPED`;
- workflow remains ACTIVE;
- Root receives `ROOT_INTAKE_REQUIRED`;
- no global blockage/retirement is recorded.

### Canary D — Missing JSON envelope

- [ ] Child returns without envelope.
- [ ] Confirm exactly one SubagentStop continuation.
- [ ] Child submits valid envelope without redoing work.

Acceptance:
- continuation count `1`;
- no second research/code pass;
- final report typed.

### Canary E — Noncompliant child after one repair

- [ ] Child returns invalid envelope twice.

Acceptance:
- task becomes `RETURNED_UNTYPED`;
- Root intake obligation exists;
- Root can inspect raw text;
- no continuation loop.

### Canary F — Root premature Stop

- [ ] Leave one report un-intaken.
- [ ] Let Root attempt to stop.

Acceptance:
- exactly one neutral Stop continuation;
- Root calls `workflow_state`;
- after intake and closure, Stop is allowed.

### Canary G — Portfolio liveness marker without SDK

- [ ] Root opens `PORTFOLIO_REVIEW_REQUIRED`.
- [ ] Root attempts to close the workflow before a decision is recorded.

Acceptance:
- closure rejected;
- Stop guarded once;
- no `INACTIVE`, `PAUSED`, `RETIRED`, or automatic exploration decision is generated.
- Root may relay the typed packet manually through the existing cross-session channel.

### Canary H — 120-second long wait

- [ ] Start `workflow_await_event(timeout_s=300)`.
- [ ] Let the child work for at least `120` seconds.
- [ ] Child returns valid envelope.

Acceptance:
- long-wait tool returns promptly after event;
- PreToolUse audit count for native `wait_agent` during the interval is `0`;
- no model continuation at 60 seconds;
- no context-polling chatter.

### Canary I — Fail-open recovery

- [ ] Temporarily point hook to an unavailable test database.
- [ ] Trigger Root Stop.

Acceptance:
- audit records `STOP_GUARD_FAIL_OPEN`;
- Root is not trapped;
- live database is untouched.

### Final MVP acceptance thresholds

```text
unit_test_failures=0
shadow_behavior_changes=0
lost_reports=0
duplicate_reports_after_dedupe=0
automatic_continuation_loops=0
managed_wait_agent_calls=0
semantic_hazard_to_global_transition=0
portfolio_review_to_automatic_disposition=0
rollback_hash_mismatches=0
```

- [ ] **Write the acceptance report**

The report must state:
- exact Codex version;
- exact MCP version;
- exact hook/config hashes before and after;
- all canary outcomes;
- every limitation encountered;
- recommendation: `ADOPT_SHADOW`, `ADOPT_ACTIVE_MVP`, or `REJECT_AND_ROLL_BACK`.

- [ ] **Final rollback rehearsal**

Disable the overlay and verify:
- `.codex/hooks.json` exact original hash;
- MCP server disabled;
- existing Agentify server unchanged;
- Codex starts normally.

---

# 9. How Root Uses the MVP

A managed workflow should follow this sequence:

```text
1. workflow_open
2. task_register for each child
3. spawn child with returned footer
4. task_bind with the returned agent id
5. workflow_await_event
6. report_get
7. root_record_intake
8. repeat wait/intake as needed
9. resolve any explicit obligations
10. workflow_close
```

Root must not use the MVP for a trivial one-step direct task.

Root should prefer:

```text
workflow_await_event
```

over:

```text
wait_agent -> timeout -> wait_agent -> timeout
```

but may still use native `wait_agent` outside managed workflows or as an explicit recovery diagnostic.

---

# 10. Known MVP Limitations

1. A completed/idle Root session is not automatically woken.
2. The dedicated Portfolio session is not automatically scheduled.
3. Cross-session packets are durable only if explicitly written into this store.
4. Root/child MCP actor identity is not yet a cryptographic boundary.
5. SQLite polling has up to roughly `500 ms` notification latency.
6. The generic JSON envelope does not exhaustively type every scientific concept.
7. The Stop guard guarantees intake/decision obligations, not the scientific quality of those decisions.
8. A Root that never opens a managed workflow remains governed only by the existing natural-language Role protocol.
9. A Root that forgets to open `PORTFOLIO_REVIEW_REQUIRED` after pair context release is not automatically detected in this MVP.
10. The overlay does not replace the existing same-direction EM/CM authority rules.

These are acceptable for the MVP because its purpose is to validate three hypotheses:

```text
H1: typed bounded reports reduce semantic promotion;
H2: obligation guards reduce silent premature closure;
H3: MCP long wait removes repeated model polling.
```

---

# 11. Subsequent Expansion Order

Do not start the next item until the previous one has been used successfully in at least three real workflows.

## Expansion 1 — Root–Portfolio typed bridge, still without SDK

Add:

```text
portfolio_review_open
portfolio_decision_record
portfolio_decision_ack
portfolio_execution_receipt
```

Behavior:
- `PAIR_CONTEXT_RELEASED` remains a lifecycle fact;
- stage completion without authorization opens `PORTFOLIO_REVIEW_REQUIRED`;
- Root manually sends generated JSON through the existing native cross-session channel;
- Portfolio records an explicit decision;
- Root records execution receipt.

No automatic Portfolio wake yet.

## Expansion 2 — Cooperative cross-session listener mode

Allow an already-active Root or Portfolio turn to call:

```text
workflow_await_event(owner="dedicated_portfolio_session")
```

This gives event-driven delivery while the session remains inside one long MCP call. It still cannot revive a fully completed turn.

## Expansion 3 — Compaction resilience

Use:
- `PreCompact` to snapshot open obligations and cursors;
- `PostCompact` or `SessionStart(source=compact)` to inject a bounded state summary.

Do not inject raw transcripts. Inject only:
- open obligations;
- active tasks;
- latest event cursor;
- exact authority boundaries.

## Expansion 4 — ACL mailbox

Add addressed messages with:
- sender;
- recipient;
- message kind;
- scope;
- acknowledgment;
- routing ACL.

Allow only the existing Router-authorized channels. Do not create unrestricted sibling messaging.

## Expansion 5 — Actor identity hardening

Probe and then enforce:
- per-agent MCP visibility;
- stable association among `agent_id`, `turn_id`, and MCP `PreToolUse`;
- root-only write tools;
- child report writes bound to SubagentStop identity.

Until this passes, the overlay remains a correctness guard rather than a hostile security boundary.

## Expansion 6 — Notification broker optimization

Replace SQLite's `500 ms` polling with:
- loopback named pipe, local TCP, or Windows event notification;
- SQLite remains source of truth;
- broker is only a low-latency signal.

Proceed only if measured latency or database polling is material.

## Expansion 7 — Package as a Codex plugin

After the repository-local implementation stabilizes:
- bundle the MCP server;
- bundle the skill/protocol docs;
- bundle hook templates;
- retain project-specific authority policy in the repository rather than the generic plugin.

Do not publish before local compatibility tests cover at least two Codex releases.

## Expansion 8 — App Server/SDK true idle wake

Only when the user chooses to accept SDK/App Server:

```text
durable event
    -> thread state check
    -> turn/start on idle Root/Portfolio
```

This is where true sleeping-session wake belongs.

## Expansion 9 — Durable DAG/supervisor

After true wake is stable:
- dependency-aware obligations;
- retries;
- stalled-owner detection;
- scheduled portfolio review ticks;
- crash recovery;
- event coalescing.

Keep semantic decisions in LLM owners.

## Expansion 10 — Rust core fork disposition

Consider a core fork only if all prior layers still cannot provide one of:

```text
native followup_task(root)
native message -> idle root turn
native indefinite wait without MCP
native persistent agent-tree recovery
```

Require a written cost/benefit and upstream-rebase plan before editing Rust.

---

# 12. Execution Prompt for Codex

Use this exact initial prompt after copying this plan into the repository:

```text
Read AGENTS.md, .agents/roles/ROOT.md, .codex/config.toml,
.codex/hooks.json, and the complete plan at:

docs/superpowers/plans/2026-08-15-hmasd-codex-semantic-longwait-mvp-plan.md

Execute the plan task-by-task using
superpowers:subagent-driven-development.

This is the no-SDK MVP. Do not add Codex SDK, App Server, a background
supervisor, Redis, a web UI, a plugin package, or Rust changes.

Preserve the live hooks file until Task 9's explicit activation gate.
Use the exact project Python executable. Treat child status vocabulary as
non-authoritative evidence. Implement only the thin obligation protocol,
typed child return, Hook guards, SQLite event cursor, and MCP long wait.

At each task boundary:
1. run the exact targeted tests;
2. inspect the diff;
3. verify no unrelated authority or scientific files changed;
4. return the acceptance evidence;
5. stop immediately on a failed phase gate.
```

---

# 13. Final Decision Rule

Adopt ACTIVE MVP only if all of the following are true:

```text
semantic drift canaries pass
SubagentStop repair is exactly once
Stop continuation is exactly once
long wait exceeds 60 seconds without model polling
unmanaged workflows are unchanged
rollback restores exact bytes
no scientific/technical/portfolio state is inferred from raw wording
```

Otherwise:
- preserve SHADOW logging if it is nonintrusive;
- disable ACTIVE behavior;
- retain evidence;
- revise the smallest failed component rather than expanding scope.
