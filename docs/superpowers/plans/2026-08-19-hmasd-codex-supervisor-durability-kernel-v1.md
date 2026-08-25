# HMASD Codex Supervisor Durability Kernel V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use an isolated Git worktree at execution time. Steps use checkbox (`- [ ]`) syntax for tracking. Only Operational Root may create Git commits; implementation, test, and review subagents return evidence without committing.

**Goal:** Replace the supervisor’s distributed, module-local state mutation rules with one durable transition and App Server effect kernel that enforces at-most-once submission attempts, evidence-based reconciliation, terminal incidents, atomic operator resolution, and restart-safe liveness for managed Root/Portfolio threads.

**Architecture:** Keep the existing Codex App Server, repository-owned authority, actor-scoped semantic overlay, external SQLite runtime, and native Codex subagents. Introduce a small `tools/codex_supervisor/durability/` package that owns aggregate state graphs, optimistic versions, transition journaling, mutating App Server effect journaling, a single process-lifetime session owner, reconciliation, and operator incident resolution. Existing business modules become orchestration adapters; they may request transitions but may not write state columns or send mutating App Server requests directly.

**Tech Stack:** Python 3.10/3.11 stdlib (`asyncio`, `sqlite3`, `dataclasses`, `enum`, `json`, `pathlib`, `typing`, `ast`, `threading`), existing Codex App Server JSONL client, existing external observer SQLite database, Windows PowerShell 5.1, pytest. No OpenAI Agents SDK, Codex SDK, Temporal, Dapr, Restate, DBOS, Redis, Kafka, or Rust core changes.

**Spec:** This plan plus the existing policies:
- `docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md`
- `docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md`
- `docs/research/workflow-runs/2026-08-18_codex-managed-actors/PROTOCOL_EVIDENCE.md`

Task 1 materializes the durable-kernel contract at:
`docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md`.

## Execution Baseline

Current design baseline:

```text
code_commit=3d6b87f20863c7a593e0dbbd8e6a59b307edb265
code_commit_message=fix: close null-lease claim, wake incident, and canary leftovers
prompt_pin_commit=04eb640f4090993b251b204096cff26b44350b90
prompt_pin_behavior_change=false
observer_schema_version=6
live_acceptance=absent
```

The implementation branch may advance before execution. At Task 0:

```text
1. record the exact new HEAD;
2. compare it with 3d6b87f2;
3. classify additional changes;
4. adapt file locations only;
5. preserve every invariant in this plan.
```

Do not silently drop requirements because a later corrective slice changed names.

## Why This Milestone Exists

The current supervisor has repeatedly repaired individual versions of the same classes of defect:

```text
INCIDENT overwritten by another module
persisted SUBMITTING treated as sendable
state and transport evidence diverge
wake delivery recorded without exact evidence
operator resolution partially commits
multiple wrappers arbitrate the same App Server process
recovery reopens or strands work
```

The durable-kernel milestone changes the unit of correctness from:

```text
“each caller remembers the rule”
```

to:

```text
“the transition/effect kernel makes the illegal path unavailable”
```

The target guarantee is not literal distributed exactly-once execution. SQLite
and App Server stdin do not share a transaction. The accepted contract is:

```text
at-most-one automatic submission attempt
+
durable possible-submission state
+
stable idempotency key
+
evidence-based reconciliation
+
idempotent downstream application
```

## Global Constraints

1. Do not add OpenAI Agents SDK.
2. Do not add Codex SDK.
3. Do not add another agent loop, handoff system, or conversation-memory layer.
4. Do not add a durable workflow product in this milestone.
5. Do not implement macro Stage 5 features:
   - task DAG;
   - capability-based write roles;
   - approval routing;
   - automatic work retry;
   - stalled-owner adjudication.
6. Do not patch Codex Rust core.
7. Do not require live App Server or restored quota for synthetic acceptance.
8. Live Phase 1 / Stage 3 / Stage 4 acceptance remains a separate later gate.
9. Do not treat missing live acceptance artifacts as code defects.
10. Preserve:
    ```text
    threadId → binding_id → actor_context_id
    ```
    as the only managed runtime identity.
11. Operational Root and Portfolio remain the only managed actor kinds.
12. EM, CM, and Leaf remain embedded Codex-native subagents.
13. Preserve `HMASD_SUBAGENT_RETURN_V1`.
14. Preserve `HMASD_MANAGED_ACTOR_COMMAND_V1`.
15. Preserve `HMASD_RUNTIME_WAKE_V1`.
16. Model text may not supply:
    ```text
    actor_context_id
    binding_id
    thread_id
    source_kind
    user_authority
    requester identity
    operator identity
    ```
17. Automatic Memory remains disabled or operator-confirmed disabled before managed binding activation.
18. App Server mechanical status never creates scientific, technical, workflow, direction, or Portfolio disposition.
19. Raw prose never becomes:
    - a state name;
    - a routing key;
    - an ACL input;
    - a retry decision;
    - an operator-resolution fact.
20. Forbidden supervisor/mailbox state names remain:
    ```text
    BLOCKED
    FAILED
    SUCCESS
    RETIRED
    PAUSED
    PARKED
    RELEASED
    ```
21. `turn.status="failed"` remains a mechanical turn-local value.
22. The supervisor does not edit canonical repository artifacts.
23. Typed packet registration may write control-plane packet/obligation rows only through the existing trusted semantic bridge.
24. SQLite remains noncanonical runtime/control state.
25. Runtime remains external:
    `%LOCALAPPDATA%\HMASD\codex-supervisor`.
26. Tests use `tmp_path` and explicit `--basetemp`.
27. No file-byte hash is a semantic gate.
28. No all-tools `PreToolUse` Hook.
29. No automatic approval or decline.
30. Unexpected server-initiated requests terminate the owned App Server process.
31. Every mutating App Server effect has one stable client key.
32. A mutating effect in `WRITE_STARTED` or later is never automatically submitted again.
33. Only an effect still in `PREPARED` may be proven unsent.
34. `INCIDENT` is terminal except through an explicit operator-resolution transaction.
35. Operator resolution is one-shot and evidence-bound.
36. Business modules may not directly update aggregate state columns after cutover.
37. Business modules may not call mutating `AppServerClient.request()` after cutover.
38. Read retry remains limited to:
    ```text
    thread/list
    thread/read
    ```
39. Mutating App Server methods are never automatically retried.
40. Keep the exact local generated schema as wire-compatibility authority.
41. Use `openaiDeveloperDocs` only as external official reference.
42. Do not send fields absent from the local schema.
43. Current-host project Python:
    `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
44. All scripts must run under Windows PowerShell 5.1.
45. Only Operational Root commits.
46. Every task ends in focused tests and a reviewable commit.
47. Stop at the first failed hard gate.
48. Do not physically delete existing observer or mutation-intent evidence.
49. Existing `mutation_intents` rows remain queryable after migration.
50. No new feature work begins until the kernel acceptance gate passes.

---

# Part I — Target Runtime Architecture

```text
Repository Authority Plane
────────────────────────────────────────────────────────
AGENTS / Roles / stage contracts / Portfolio contract
canonical owner artifacts / Plan Epoch / semantic packets
                        │
                        │ trusted semantic bridge
                        ▼
Supervisor Durability Kernel
────────────────────────────────────────────────────────
aggregate transition graphs
optimistic versions
transition journal
App Server effect journal
operator resolutions
reconciliation
                        │
                        │ one process-lifetime session owner
                        ▼
Codex App Server
────────────────────────────────────────────────────────
thread / turn / item / server requests / raw JSONL
```

## Single-Writer Rule

After Task 15, the following columns may be modified only through
`TransitionKernel`:

```text
managed_actor_bindings.binding_state
managed_turn_intents.submission_state
wake_batches.state
mailbox_messages.delivery_state
mailbox_messages.intake_state
managed_actor_commands.validation_state
app_server_effects.state
```

Existing `mutation_intents.state` becomes legacy read-only evidence after
cutover.

## Single Mutating-Transport Rule

After Task 13, mutating App Server requests may be sent only through:

```python
AppServerSessionOwner.submit_effect(effect_id: str) -> EffectSubmissionResult
```

The following modules may no longer call mutating `client.request()` directly:

```text
provisioning.py
managed_turns.py
wake_scheduler.py
wake_recovery.py
observer.py canary
managed_runtime.py
```

Read-only operations use:

```python
AppServerSessionOwner.request_read(method, params)
```

---

# Part II — Aggregate State Graphs

These state graphs are authoritative for the kernel. A transition not listed
here is illegal.

## Managed Binding

```text
PREPARED
  → THREAD_CREATED
  → REVOKED

THREAD_CREATED
  → VERIFICATION_REQUIRED
  → REVOKED

VERIFICATION_REQUIRED
  → ACTIVE
  → SUSPENDED
  → REVOKED

ACTIVE
  → SUSPENDED
  → REVOKED

SUSPENDED
  → VERIFICATION_REQUIRED
  → REVOKED

REVOKED
  → no transition
```

A suspended binding cannot return directly to `ACTIVE`; it must reverify.

## Managed Turn Intent

```text
PREPARED
  → SUBMITTING
  → CANCELLED
  → INCIDENT

SUBMITTING
  → SUBMITTED
  → SUBMISSION_UNCERTAIN
  → INCIDENT

SUBMITTED
  → OBSERVED
  → SUBMISSION_UNCERTAIN
  → INCIDENT

SUBMISSION_UNCERTAIN
  → OBSERVED
  → INCIDENT

OBSERVED
  → COMPLETED
  → INCIDENT

COMPLETED
  → no transition

CANCELLED
  → no transition

INCIDENT
  → no automatic transition
```

`SUBMITTING` now has one exact meaning:

```text
the linked App Server effect reached WRITE_STARTED
```

A newly prepared turn is `PREPARED`, never `SUBMITTING`.

## Wake Batch

```text
PREPARED
  → SUBMITTING
  → CANCELLED
  → INCIDENT

SUBMITTING
  → SUBMITTED
  → SUBMISSION_UNCERTAIN
  → INCIDENT

SUBMITTED
  → ACTIVE
  → SUBMISSION_UNCERTAIN
  → INCIDENT

SUBMISSION_UNCERTAIN
  → ACTIVE
  → INCIDENT

ACTIVE
  → COMPLETED
  → INCIDENT

INCIDENT
  → CANCELLED       only with one operator resolution
  → ACTIVE          only with exact observed-turn evidence
  → COMPLETED       only with exact completed-turn evidence
  → ABANDONED       only with one operator resolution

COMPLETED / CANCELLED / ABANDONED
  → no transition
```

## Mailbox Delivery

```text
ENQUEUED
  → ELIGIBLE
  → CANCELLED_SOURCE_RESOLVED
  → DEAD_LETTER

ELIGIBLE
  → BATCHED
  → ENQUEUED
  → CANCELLED_SOURCE_RESOLVED
  → DEAD_LETTER

BATCHED
  → DELIVERED_TO_TURN
  → SUBMISSION_UNCERTAIN
  → ELIGIBLE
  → CANCELLED_SOURCE_RESOLVED
  → DEAD_LETTER

SUBMISSION_UNCERTAIN
  → DELIVERED_TO_TURN
  → DEAD_LETTER

DELIVERED_TO_TURN
  → DEAD_LETTER

CANCELLED_SOURCE_RESOLVED / DEAD_LETTER
  → no transition
```

`BATCHED → ELIGIBLE` requires one of:

```text
PRE_WRITE_CANCEL
OPERATOR_NO_SUBMISSION
SOURCE_INVALID_PREPARED_BATCH
```

## Mailbox Intake

```text
NOT_ACKNOWLEDGED
  → ACKNOWLEDGED

ACKNOWLEDGED
  → INTAKEN

INTAKEN
  → APPLIED

APPLIED
  → no transition
```

## Managed Command

```text
RECEIVED
  → VALIDATED
  → REJECTED
  → INCIDENT

VALIDATED
  → APPLIED
  → REJECTED
  → INCIDENT

APPLIED / REJECTED / INCIDENT
  → no automatic transition
```

A command in `INCIDENT` may be reconciled only through a one-shot operator
resolution with exact effect receipt evidence.

## App Server Effect

```text
PREPARED
  → WRITE_STARTED
  → CANCELLED_BEFORE_WRITE
  → INCIDENT

WRITE_STARTED
  → RESPONSE_OBSERVED
  → SUBMISSION_UNCERTAIN
  → INCIDENT

RESPONSE_OBSERVED
  → EFFECT_CONFIRMED
  → INCIDENT

SUBMISSION_UNCERTAIN
  → EFFECT_CONFIRMED
  → INCIDENT

EFFECT_CONFIRMED
  → no transition

CANCELLED_BEFORE_WRITE
  → no transition

INCIDENT
  → OPERATOR_RESOLVED
```

Evidence rule:

```text
PREPARED
= no write claim exists; automatic cancellation is safe.

WRITE_STARTED or later
= submission may have occurred; automatic resend is forbidden.
```

---

# Part III — Target Database Schema

Final target schema version: `7`.

## Version columns

Add:

```sql
ALTER TABLE managed_actor_bindings
ADD COLUMN version INTEGER NOT NULL DEFAULT 0;

ALTER TABLE managed_turn_intents
ADD COLUMN version INTEGER NOT NULL DEFAULT 0;

ALTER TABLE wake_batches
ADD COLUMN version INTEGER NOT NULL DEFAULT 0;

ALTER TABLE mailbox_messages
ADD COLUMN delivery_version INTEGER NOT NULL DEFAULT 0;

ALTER TABLE mailbox_messages
ADD COLUMN intake_version INTEGER NOT NULL DEFAULT 0;

ALTER TABLE managed_actor_commands
ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
```

## Effect references

Add:

```sql
ALTER TABLE managed_turn_intents
ADD COLUMN effect_id TEXT;

ALTER TABLE wake_batches
ADD COLUMN effect_id TEXT;

ALTER TABLE raw_messages
ADD COLUMN effect_id TEXT;

ALTER TABLE rpc_requests
ADD COLUMN effect_id TEXT;

ALTER TABLE mutation_intents
ADD COLUMN superseded_by_effect_id TEXT;
```

`managed_actor_bindings` does not need a single effect column. Thread creation
and resume effects refer to the binding through `app_server_effects.owner_id`.

## `app_server_effects`

```sql
CREATE TABLE app_server_effects (
    effect_id TEXT PRIMARY KEY,
    owner_kind TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    binding_id TEXT,
    method TEXT NOT NULL,
    client_key TEXT NOT NULL,
    request_json TEXT NOT NULL,
    state TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 0,
    run_id TEXT,
    client_request_id TEXT,
    request_row_id TEXT,
    raw_request_seq INTEGER,
    thread_id TEXT,
    turn_id TEXT,
    response_json TEXT,
    incident_json TEXT,
    legacy_intent_id TEXT,
    prepared_at TEXT NOT NULL,
    write_started_at TEXT,
    response_observed_at TEXT,
    confirmed_at TEXT,
    reconciled_at TEXT,
    resolved_at TEXT,
    UNIQUE(method, client_key)
);
```

Allowed `owner_kind`:

```text
THREAD_PROVISION
THREAD_RESUME
MANAGED_TURN
WAKE_BATCH
EPHEMERAL_CANARY
```

## `control_transitions`

```sql
CREATE TABLE control_transitions (
    transition_id TEXT PRIMARY KEY,
    aggregate_kind TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    state_column TEXT NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    from_version INTEGER NOT NULL,
    to_version INTEGER NOT NULL,
    cause_kind TEXT NOT NULL,
    cause_ref TEXT NOT NULL,
    evidence_ref TEXT,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(aggregate_kind, aggregate_id, state_column, to_version)
);
```

## `operator_resolutions`

```sql
CREATE TABLE operator_resolutions (
    resolution_id TEXT PRIMARY KEY,
    aggregate_kind TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    effect_id TEXT,
    operator TEXT NOT NULL,
    disposition TEXT NOT NULL,
    evidence_kind TEXT NOT NULL,
    evidence_ref TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(aggregate_kind, aggregate_id)
);
```

The unique key makes operator resolution one-shot.

## New indexes

```sql
CREATE INDEX app_server_effect_owner
ON app_server_effects(owner_kind, owner_id);

CREATE INDEX app_server_effect_binding
ON app_server_effects(binding_id, state);

CREATE INDEX app_server_effect_request
ON app_server_effects(run_id, client_request_id);

CREATE INDEX control_transition_aggregate
ON control_transitions(aggregate_kind, aggregate_id, to_version);
```

## Legacy evidence

Do not delete `mutation_intents`.

After cutover:

```text
new inserts into mutation_intents = 0
new state updates to mutation_intents = 0
legacy rows remain queryable
superseded_by_effect_id links migrated evidence
```

---

# Part IV — New File Map

## New implementation package

```text
tools/codex_supervisor/durability/
├── __init__.py
├── models.py
├── graphs.py
├── transaction.py
├── transitions.py
├── effects.py
├── session_owner.py
├── reconciliation.py
├── operator_resolution.py
└── static_guards.py
```

Responsibilities:

```text
models.py
  enums and immutable request/result dataclasses

graphs.py
  authoritative state graphs and cause restrictions

transaction.py
  BEGIN IMMEDIATE transaction owner

transitions.py
  CAS state updates, version increments, transition journal

effects.py
  App Server effect preparation, write claim, response, uncertainty,
  confirmation, incident, and evidence queries

session_owner.py
  one App Server client/process owner; reads, mutation submission,
  server-request handling, raw/effect correlation

reconciliation.py
  method-specific effect reconciliation and restart recovery

operator_resolution.py
  one-shot evidence-bound incident resolution

static_guards.py
  source scan for direct state writes and direct mutating client calls
```

## New tests

```text
tests/codex_supervisor/durability/
├── __init__.py
├── test_graphs.py
├── test_schema_v7.py
├── test_transition_kernel.py
├── test_transition_triggers.py
├── test_effect_journal.py
├── test_session_owner.py
├── test_managed_turn_cutover.py
├── test_provisioning_cutover.py
├── test_wake_cutover.py
├── test_mailbox_cutover.py
├── test_command_cutover.py
├── test_operator_resolution.py
├── test_reconciliation.py
├── test_legacy_migration.py
├── test_static_guards.py
├── test_fault_matrix.py
└── test_concurrency_matrix.py
```

## New documentation

```text
docs/project/
└── CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md

docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/
├── BASELINE.md
├── MIGRATION_REPORT.md
├── SYNTHETIC_ACCEPTANCE.md
└── SYNTHETIC_REVIEW_PROMPT.md
```

## New scripts

```text
scripts/
├── codex-supervisor-durability-doctor.ps1
└── codex-supervisor-durability-test.ps1
```

---

# Task 0: Freeze the Baseline and Stop Feature Expansion

**Files:**
- Create: `docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/BASELINE.md`
- Read: existing supervisor policies, protocol evidence, latest synthetic prompt
- No behavioral source edits in this task

**Interfaces:**
- Produces:
  - exact `durability_kernel_baseline_commit`;
  - exact test command;
  - exact known open findings;
  - feature-freeze declaration.

- [ ] **Step 1: Create an isolated worktree**

Run from the main checkout:

```powershell
git fetch origin
git worktree add `
  C:\Projects\HMASD-durability-kernel-v1 `
  -b codex-supervisor-durability-kernel-v1 `
  origin/aggressive
```

- [ ] **Step 2: Record current state**

```powershell
Set-Location C:\Projects\HMASD-durability-kernel-v1
git status --short
git rev-parse HEAD
git log -8 --oneline
git diff --stat 3d6b87f20863c7a593e0dbbd8e6a59b307edb265..HEAD
```

- [ ] **Step 3: Classify post-3d6 changes**

Write a table:

```text
commit
files
behavioral / documentation
durability-kernel impact
```

Do not silently absorb unrelated Stage 5 work.

- [ ] **Step 4: Run current synthetic suites**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_semantic_mvp `
  tests/codex_context_lifecycle `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-durability-kernel-v1/.tmp_baseline
```

- [ ] **Step 5: Record current direct-write inventory**

Run:

```powershell
git grep -n -E `
  "UPDATE (managed_actor_bindings|managed_turn_intents|wake_batches|mailbox_messages|managed_actor_commands|mutation_intents)" `
  -- tools/codex_supervisor
```

Record every result in `BASELINE.md`.

- [ ] **Step 6: Record current direct mutation-call inventory**

```powershell
git grep -n -E `
  "client\.request\(\"(thread/start|thread/resume|thread/fork|turn/start|turn/steer|turn/interrupt|thread/compact/start|review/start)" `
  -- tools/codex_supervisor
```

- [ ] **Step 7: Write feature freeze**

`BASELINE.md` must state:

```text
No Stage 5 capability will be added before durability-kernel acceptance.
Live App Server remains deferred and is not a defect.
```

- [ ] **Step 8: Root-only commit**

```powershell
git add docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/BASELINE.md
git commit -m "docs: freeze supervisor durability kernel baseline"
```

**Acceptance criteria:**

- Baseline is exact.
- Existing test failures are recorded rather than hidden.
- No behavior changed.

---

# Task 1: Materialize the Kernel Contract and State Graphs

**Files:**
- Create: `docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md`
- Create: `tools/codex_supervisor/durability/__init__.py`
- Create: `tools/codex_supervisor/durability/models.py`
- Create: `tools/codex_supervisor/durability/graphs.py`
- Create: `tests/codex_supervisor/durability/__init__.py`
- Create: `tests/codex_supervisor/durability/test_graphs.py`

**Interfaces:**
- Produces:
  - `AggregateKind`
  - `TransitionCause`
  - `EffectState`
  - `TransitionRequest`
  - `TransitionResult`
  - `ALLOWED_TRANSITIONS`
  - `OPERATOR_ONLY_EDGES`

- [ ] **Step 1: Write failing graph tests**

Create tests that assert:

```python
def test_incident_has_no_automatic_exit() -> None:
    for aggregate, edges in ALLOWED_TRANSITIONS.items():
        for target in edges.get("INCIDENT", frozenset()):
            assert (aggregate, "INCIDENT", target) in OPERATOR_ONLY_EDGES


def test_managed_turn_starts_prepared() -> None:
    assert "PREPARED" in ALLOWED_TRANSITIONS[AggregateKind.MANAGED_TURN]


def test_effect_write_started_cannot_return_to_prepared() -> None:
    assert "PREPARED" not in ALLOWED_TRANSITIONS[
        AggregateKind.APP_SERVER_EFFECT
    ]["WRITE_STARTED"]
```

- [ ] **Step 2: Run and verify red**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_graphs.py -q
```

Expected:

```text
ModuleNotFoundError: tools.codex_supervisor.durability
```

- [ ] **Step 3: Implement enums**

`models.py` must define:

```python
class AggregateKind(str, Enum):
    MANAGED_BINDING = "MANAGED_BINDING"
    MANAGED_TURN = "MANAGED_TURN"
    WAKE_BATCH = "WAKE_BATCH"
    MAILBOX_DELIVERY = "MAILBOX_DELIVERY"
    MAILBOX_INTAKE = "MAILBOX_INTAKE"
    MANAGED_COMMAND = "MANAGED_COMMAND"
    APP_SERVER_EFFECT = "APP_SERVER_EFFECT"


class TransitionCause(str, Enum):
    OPERATOR_ACTION = "OPERATOR_ACTION"
    APP_SERVER_EFFECT = "APP_SERVER_EFFECT"
    APP_SERVER_RESPONSE = "APP_SERVER_RESPONSE"
    APP_SERVER_EVENT = "APP_SERVER_EVENT"
    SERVER_REQUEST_INCIDENT = "SERVER_REQUEST_INCIDENT"
    RECONCILIATION = "RECONCILIATION"
    SOURCE_RESOLUTION = "SOURCE_RESOLUTION"
    OPERATOR_RESOLUTION = "OPERATOR_RESOLUTION"
    CONTROL_COMMAND = "CONTROL_COMMAND"
    MIGRATION = "MIGRATION"
```

- [ ] **Step 4: Implement immutable transition types**

```python
@dataclass(frozen=True)
class TransitionRequest:
    aggregate_kind: AggregateKind
    aggregate_id: str
    expected_state: str
    expected_version: int
    target_state: str
    cause_kind: TransitionCause
    cause_ref: str
    evidence_ref: str | None = None
    field_updates: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TransitionResult:
    transition_id: str
    aggregate_kind: AggregateKind
    aggregate_id: str
    from_state: str
    to_state: str
    from_version: int
    to_version: int
    row: Mapping[str, object]
```

- [ ] **Step 5: Encode the exact state graphs from Part II**

No graph may be inferred in business modules.

- [ ] **Step 6: Encode operator-only edges**

At minimum:

```text
WAKE_BATCH INCIDENT → CANCELLED
WAKE_BATCH INCIDENT → ACTIVE
WAKE_BATCH INCIDENT → COMPLETED
WAKE_BATCH INCIDENT → ABANDONED
APP_SERVER_EFFECT INCIDENT → OPERATOR_RESOLVED
```

- [ ] **Step 7: Write the contract document**

The document must state:

```text
- at-most-once attempt, not distributed exactly-once;
- PREPARED is the only automatically cancelable effect state;
- WRITE_STARTED means possible submission;
- one session owner;
- one transition kernel;
- one-shot operator resolution;
- no Agents SDK.
```

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_graphs.py -q
```

- [ ] **Step 9: Root-only commit**

```powershell
git add `
  docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md `
  tools/codex_supervisor/durability `
  tests/codex_supervisor/durability
git commit -m "docs: define supervisor durability kernel contract"
```

---

# Task 2: Add Schema Version 7 Additively

**Files:**
- Modify: `tools/codex_supervisor/db.py`
- Create: `tests/codex_supervisor/durability/test_schema_v7.py`

**Interfaces:**
- Produces:
  - schema version 7;
  - new tables and columns from Part III;
  - additive v6→v7 migration.

- [ ] **Step 1: Write a real schema-6 fixture**

Create the current v6 tables with:

```text
one binding
one managed turn
one wake batch
one mailbox message
one managed command
one mutation intent
one raw request
```

- [ ] **Step 2: Write migration assertions**

After `initialize_database()`:

```text
all v6 rows remain
version columns exist with 0
app_server_effects exists
control_transitions exists
operator_resolutions exists
effect reference columns exist
schema_meta max(version) == 7
newer schema still fails closed
```

- [ ] **Step 3: Implement schema 7**

Set:

```python
SCHEMA_VERSION = 7
```

Add exact Part III tables and columns.

- [ ] **Step 4: Add uniqueness constraints**

Required:

```text
app_server_effects(method, client_key) UNIQUE
operator_resolutions(aggregate_kind, aggregate_id) UNIQUE
control_transitions aggregate version UNIQUE
```

- [ ] **Step 5: Preserve all old tables**

No `DROP TABLE`.

`mutation_intents_open_unique` remains during compatibility.

- [ ] **Step 6: Run migration tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_schema_v7.py -q
```

- [ ] **Step 7: Run prior schema tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_db.py `
  tests/codex_supervisor/test_managed_schema_v2.py `
  tests/codex_supervisor/test_mailbox_schema_v3.py `
  -q
```

- [ ] **Step 8: Root-only commit**

```powershell
git add tools/codex_supervisor/db.py tests/codex_supervisor/durability/test_schema_v7.py
git commit -m "feat: add supervisor durability schema"
```

---

# Task 3: Implement the Transaction and Transition Kernel

**Files:**
- Create: `tools/codex_supervisor/durability/transaction.py`
- Create: `tools/codex_supervisor/durability/transitions.py`
- Create: `tests/codex_supervisor/durability/test_transition_kernel.py`

**Interfaces:**
- Produces:
  - `DurabilityTransaction`
  - `TransitionKernel`
  - `TransitionError`
  - `AggregateLocator`

- [ ] **Step 1: Define aggregate table mapping**

```python
AGGREGATE_LOCATORS = {
    AggregateKind.MANAGED_BINDING: AggregateLocator(
        table="managed_actor_bindings",
        id_column="binding_id",
        state_column="binding_state",
        version_column="version",
    ),
    AggregateKind.MANAGED_TURN: AggregateLocator(
        table="managed_turn_intents",
        id_column="turn_intent_id",
        state_column="submission_state",
        version_column="version",
    ),
    AggregateKind.WAKE_BATCH: AggregateLocator(
        table="wake_batches",
        id_column="wake_batch_id",
        state_column="state",
        version_column="version",
    ),
    AggregateKind.MAILBOX_DELIVERY: AggregateLocator(
        table="mailbox_messages",
        id_column="message_id",
        state_column="delivery_state",
        version_column="delivery_version",
    ),
    AggregateKind.MAILBOX_INTAKE: AggregateLocator(
        table="mailbox_messages",
        id_column="message_id",
        state_column="intake_state",
        version_column="intake_version",
    ),
    AggregateKind.MANAGED_COMMAND: AggregateLocator(
        table="managed_actor_commands",
        id_column="command_id",
        state_column="validation_state",
        version_column="version",
    ),
    AggregateKind.APP_SERVER_EFFECT: AggregateLocator(
        table="app_server_effects",
        id_column="effect_id",
        state_column="state",
        version_column="version",
    ),
}
```

- [ ] **Step 2: Write failing CAS tests**

Required:

```text
correct state + version → transition
stale version → reject
wrong state → reject
illegal edge → reject
incident automatic exit → reject
operator-only edge without operator resolution → reject
transition audit inserted in same tx
```

- [ ] **Step 3: Implement `BEGIN IMMEDIATE` owner**

```python
class DurabilityTransaction:
    def __enter__(self):
        connection.execute("BEGIN IMMEDIATE")
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            connection.commit()
        else:
            connection.rollback()
```

Do not nest `with connection:` inside this transaction.

- [ ] **Step 4: Implement transition CAS**

The update shape must be:

```sql
UPDATE <table>
SET <state_column> = ?,
    <version_column> = <version_column> + 1,
    ...field updates...
WHERE <id_column> = ?
  AND <state_column> = ?
  AND <version_column> = ?;
```

Require `rowcount == 1`.

- [ ] **Step 5: Insert transition audit in the same transaction**

Audit uses the exact new version.

- [ ] **Step 6: Enforce operator-only edges**

A requested operator-only edge requires a matching unconsumed
`operator_resolutions` row in the same transaction.

- [ ] **Step 7: Add a multi-transition transaction test**

Atomically:

```text
wake batch INCIDENT → CANCELLED
message BATCHED → ELIGIBLE
operator resolution inserted
```

Injected exception after the first transition must roll back all rows.

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_transition_kernel.py -q
```

- [ ] **Step 9: Root-only commit**

```powershell
git add tools/codex_supervisor/durability/transaction.py tools/codex_supervisor/durability/transitions.py tests/codex_supervisor/durability/test_transition_kernel.py
git commit -m "feat: add supervisor transition kernel"
```

---

# Task 4: Add Database Transition Guards

**Files:**
- Modify: `tools/codex_supervisor/db.py`
- Create: `tests/codex_supervisor/durability/test_transition_triggers.py`

**Interfaces:**
- Produces SQLite guards for illegal state edges and version-less updates.

- [ ] **Step 1: Generate trigger SQL from `ALLOWED_TRANSITIONS`**

Do not maintain a second hand-written graph.

- [ ] **Step 2: Add version increment guards**

For every state column:

```text
if state changes, version must equal old version + 1
```

- [ ] **Step 3: Add illegal-edge guards**

Direct SQL:

```sql
UPDATE wake_batches SET state='COMPLETED' WHERE state='PREPARED';
```

must fail with:

```text
illegal WAKE_BATCH transition
```

- [ ] **Step 4: Guard incident exits**

An `INCIDENT → ACTIVE/COMPLETED/CANCELLED/ABANDONED` update requires a
matching `operator_resolutions` row.

- [ ] **Step 5: Test direct SQL bypasses**

Cover all aggregate kinds.

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_transition_triggers.py -q
```

- [ ] **Step 7: Root-only commit**

```powershell
git add tools/codex_supervisor/db.py tests/codex_supervisor/durability/test_transition_triggers.py
git commit -m "feat: guard supervisor state transitions in sqlite"
```

---

# Task 5: Implement the App Server Effect Journal

**Files:**
- Create: `tools/codex_supervisor/durability/effects.py`
- Create: `tests/codex_supervisor/durability/test_effect_journal.py`

**Interfaces:**
- Produces:
  - `EffectJournal`
  - `EffectRecord`
  - `EffectError`
  - `prepare_effect`
  - `claim_write`
  - `observe_response`
  - `mark_uncertain`
  - `confirm_effect`
  - `mark_incident`

- [ ] **Step 1: Write effect lifecycle tests**

Required:

```text
prepare is idempotent by method+client_key
only PREPARED can claim write
claim write is CAS
WRITE_STARTED cannot be prepared again
timeout after WRITE_STARTED becomes SUBMISSION_UNCERTAIN
response becomes RESPONSE_OBSERVED
confirmation requires evidence_ref
incident is terminal
```

- [ ] **Step 2: Implement effect preparation**

```python
def prepare_effect(
    *,
    owner_kind: str,
    owner_id: str,
    binding_id: str | None,
    method: str,
    client_key: str,
    request: Mapping[str, object],
) -> EffectRecord:
    ...
```

An existing key must match the complete immutable tuple or raise conflict.

- [ ] **Step 3: Implement write claim**

`claim_write()` takes:

```text
effect_id
run_id
client_request_id
request_row_id
raw_request_seq
```

and transitions:

```text
PREPARED → WRITE_STARTED
```

- [ ] **Step 4: Implement evidence queries**

```python
def has_possible_submission(effect_id: str) -> bool:
    return state != PREPARED or raw_request_seq is not None
```

Conservative rule:

```text
WRITE_STARTED always means possible submission,
even if the process may have exited before bytes reached App Server.
```

- [ ] **Step 5: Implement incident mapping**

Server request incident stores exact server-request row/evidence reference.

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_effect_journal.py -q
```

- [ ] **Step 7: Root-only commit**

```powershell
git add tools/codex_supervisor/durability/effects.py tests/codex_supervisor/durability/test_effect_journal.py
git commit -m "feat: journal mutating App Server effects"
```

---

# Task 6: Split Request Preparation from Transport Send

**Files:**
- Modify: `tools/codex_supervisor/client.py`
- Modify: `tools/codex_supervisor/store.py`
- Create: `tests/codex_supervisor/durability/test_prepared_requests.py`

**Interfaces:**
- Produces:
  - `PreparedRpcRequest`
  - `AppServerClient.prepare_request`
  - `AppServerClient.send_prepared`
  - `AppServerClient.await_prepared`
  - `ObserverStore.record_effect_write_start`

- [ ] **Step 1: Define prepared request**

```python
@dataclass(frozen=True)
class PreparedRpcRequest:
    request_id: str
    method: str
    params: Mapping[str, object]
    payload: Mapping[str, object]
    request_class: RequestClass
    future: asyncio.Future[dict[str, object]]
```

- [ ] **Step 2: Implement `prepare_request()`**

It allocates request ID and pending future but sends no bytes.

- [ ] **Step 3: Implement atomic outbound evidence recording**

`record_effect_write_start()` performs in one SQLite transaction:

```text
effect PREPARED → WRITE_STARTED
raw_messages insert
rpc_requests insert
effect request/raw linkage update
control transition insert
```

- [ ] **Step 4: Implement `send_prepared()`**

It sends the already recorded payload exactly once.

- [ ] **Step 5: Implement `await_prepared()`**

It waits for the registered future and does not resend.

- [ ] **Step 6: Restrict compatibility `request()`**

`request()` remains available for:

```text
initialize
thread/list
thread/read
thread/loaded/list
```

It rejects mutating methods with:

```text
mutating requests require AppServerSessionOwner.submit_effect
```

- [ ] **Step 7: Preserve read retry behavior**

Only `thread/list` and `thread/read` retry `-32001`.

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_prepared_requests.py -q
```

- [ ] **Step 9: Run client regressions**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_client_handshake.py `
  tests/codex_supervisor/test_request_retry.py `
  -q
```

- [ ] **Step 10: Root-only commit**

```powershell
git add tools/codex_supervisor/client.py tools/codex_supervisor/store.py tests/codex_supervisor/durability/test_prepared_requests.py
git commit -m "refactor: separate App Server request preparation and send"
```

---

# Task 7: Build the Single Process-Lifetime Session Owner

**Files:**
- Create: `tools/codex_supervisor/durability/session_owner.py`
- Modify: `tools/codex_supervisor/session_guard.py`
- Create: `tests/codex_supervisor/durability/test_session_owner.py`

**Interfaces:**
- Produces:
  - `AppServerSessionOwner`
  - `EffectSubmissionResult`
  - `request_read`
  - `submit_effect`
  - process-lifetime server-request watcher.

- [ ] **Step 1: Define the public API**

```python
class AppServerSessionOwner:
    async def start(self) -> None: ...
    async def request_read(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]: ...
    async def submit_effect(
        self,
        effect_id: str,
    ) -> EffectSubmissionResult: ...
    async def close(self) -> None: ...
```

- [ ] **Step 2: Make it singleton per client**

One client has exactly one owner and one server-request consumer.

- [ ] **Step 3: Submit an effect**

Sequence:

```text
load PREPARED effect
prepare RPC request
record WRITE_STARTED + raw/rpc evidence atomically
send prepared request once
await response
response → RESPONSE_OBSERVED
timeout/EOF → SUBMISSION_UNCERTAIN
server request → INCIDENT + terminate
```

- [ ] **Step 4: Keep watcher alive after response**

A server request that arrives before turn completion must still mark the linked
effect and domain aggregate incident.

- [ ] **Step 5: Make `SessionGuard` a compatibility shim**

It delegates to the single owner and does not create another queue consumer.

- [ ] **Step 6: Add race tests**

Required:

```text
server request before response
server request with response
server request after response
two simultaneous read RPC responses
one server-request consumer
effect incident persists after response
```

- [ ] **Step 7: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_session_owner.py -q
```

- [ ] **Step 8: Root-only commit**

```powershell
git add tools/codex_supervisor/durability/session_owner.py tools/codex_supervisor/session_guard.py tests/codex_supervisor/durability/test_session_owner.py
git commit -m "feat: add single App Server session owner"
```

---

# Task 8: Cut Managed Turns Over to the Kernel

**Files:**
- Modify: `tools/codex_supervisor/managed_turns.py`
- Modify: `tools/codex_supervisor/managed_runtime.py`
- Create: `tests/codex_supervisor/durability/test_managed_turn_cutover.py`

**Interfaces:**
- Consumes:
  - `TransitionKernel`
  - `EffectJournal`
  - `AppServerSessionOwner`
- Produces managed-turn operations with no direct state SQL.

- [ ] **Step 1: Change turn preparation**

New row state:

```text
PREPARED
```

Prepare one linked `turn/start` effect in `PREPARED`.

- [ ] **Step 2: Submit through session owner**

Domain transition sequence:

```text
managed turn PREPARED → SUBMITTING
effect PREPARED → WRITE_STARTED
```

These occur in the same database transaction that records outbound evidence.

- [ ] **Step 3: Handle response**

Known response:

```text
effect → RESPONSE_OBSERVED
managed turn SUBMITTING → SUBMITTED
```

Timeout/transport:

```text
effect → SUBMISSION_UNCERTAIN
managed turn SUBMITTING → SUBMISSION_UNCERTAIN
```

- [ ] **Step 4: Reconcile by client message ID**

Observed turn:

```text
effect → EFFECT_CONFIRMED
managed turn SUBMITTED/SUBMISSION_UNCERTAIN → OBSERVED
```

- [ ] **Step 5: Preserve terminal incident**

No completion, command, or reconciliation may leave `INCIDENT`.

- [ ] **Step 6: Remove new `MutationIntentStore` writes**

Managed turns no longer create or update `mutation_intents`.

- [ ] **Step 7: Add tests**

Required:

```text
test_new_managed_turn_is_prepared_not_submitting
test_managed_turn_write_started_is_never_resubmitted
test_managed_turn_timeout_reconciles_by_original_client_key
test_managed_turn_incident_is_terminal
test_managed_turn_effect_and_domain_state_never_diverge
```

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_managed_turn_cutover.py -q
```

- [ ] **Step 9: Run existing turn/activation tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_managed_turns.py `
  tests/codex_supervisor/test_stage3_end_to_end.py `
  tests/codex_supervisor/test_command_gateway.py `
  -q
```

- [ ] **Step 10: Root-only commit**

```powershell
git add tools/codex_supervisor/managed_turns.py tools/codex_supervisor/managed_runtime.py tests/codex_supervisor/durability/test_managed_turn_cutover.py
git commit -m "refactor: move managed turns onto durability kernel"
```

---

# Task 9: Cut Provisioning and Binding Transitions Over

**Files:**
- Modify: `tools/codex_supervisor/provisioning.py`
- Modify: `tools/codex_supervisor/binding_store.py`
- Create: `tests/codex_supervisor/durability/test_provisioning_cutover.py`

**Interfaces:**
- Produces thread start/resume through effect journal and binding transitions.

- [ ] **Step 1: Provisioning prepares effects**

Thread create:

```text
owner_kind=THREAD_PROVISION
owner_id=binding_id
method=thread/start
client_key=thread/start:<binding_id>
```

Thread resume:

```text
owner_kind=THREAD_RESUME
owner_id=binding_id
method=thread/resume
client_key=thread/resume:<thread_id>
```

- [ ] **Step 2: Send only through session owner**

No direct `client.request()`.

- [ ] **Step 3: Attach and confirm atomically**

In one `BEGIN IMMEDIATE` transaction:

```text
effect RESPONSE_OBSERVED/SUBMISSION_UNCERTAIN → EFFECT_CONFIRMED
binding PREPARED → THREAD_CREATED
thread_id written
transition audit written
```

- [ ] **Step 4: Preserve uncertain effect**

If response/attach certainty is absent:

```text
do not create another effect
do not call thread/start or thread/resume again
reconciliation only
```

- [ ] **Step 5: Remove production no-effect attach**

`attach_thread_for_tests` remains test-only and cannot exist in production
imports.

- [ ] **Step 6: Add tests**

Required:

```text
test_thread_start_effect_confirm_and_attach_are_one_tx
test_thread_resume_effect_confirm_and_attach_are_one_tx
test_crash_after_response_before_attach_reconciles_original_effect
test_unresolved_write_started_prevents_second_thread_start
test_binding_transition_uses_expected_version
```

- [ ] **Step 7: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_provisioning_cutover.py -q
```

- [ ] **Step 8: Root-only commit**

```powershell
git add tools/codex_supervisor/provisioning.py tools/codex_supervisor/binding_store.py tests/codex_supervisor/durability/test_provisioning_cutover.py
git commit -m "refactor: journal managed thread provisioning effects"
```

---

# Task 10: Cut Wake Submission and Recovery Over

**Files:**
- Modify: `tools/codex_supervisor/wake_batches.py`
- Modify: `tools/codex_supervisor/wake_scheduler.py`
- Modify: `tools/codex_supervisor/wake_recovery.py`
- Create: `tests/codex_supervisor/durability/test_wake_cutover.py`

**Interfaces:**
- Produces one effect-backed wake submission and evidence-based recovery.

- [ ] **Step 1: Prepare wake batch and effect together**

Batch:

```text
state=PREPARED
```

Effect:

```text
state=PREPARED
method=turn/start
client_key=hmasd-wake:<wake_batch_id>
owner_kind=WAKE_BATCH
owner_id=<wake_batch_id>
```

- [ ] **Step 2: Claim first send atomically**

One `BEGIN IMMEDIATE` transaction:

```text
validate exact live lease holder/generation
wake PREPARED → SUBMITTING
effect PREPARED remains linked
attempt 1 insert
```

The session owner’s write claim then transitions effect to `WRITE_STARTED`.

- [ ] **Step 3: Remove lease fallback**

Public signatures require:

```python
lease_holder: str
lease_generation: int
```

No reading credentials back from the batch for the caller.

- [ ] **Step 4: Submit through session owner**

No direct mutating client request.

- [ ] **Step 5: Derive possible submission only from effect**

Delete heuristic `_has_possible_submission()` checks based on optional
timestamps.

Use:

```python
effects.has_possible_submission(effect_id)
```

- [ ] **Step 6: Recover by original effect**

```text
PREPARED effect
  → safe batch cancellation

WRITE_STARTED / SUBMISSION_UNCERTAIN
  → clientUserMessageId reconciliation only

RESPONSE_OBSERVED
  → bind exact turn

EFFECT_CONFIRMED + active turn
  → ACTIVE

mechanical completion
  → COMPLETED

INCIDENT
  → operator resolution only
```

- [ ] **Step 7: Add tests**

Required:

```text
test_wake_batch_and_effect_share_client_key
test_wake_claim_requires_explicit_lease
test_write_started_wake_is_never_automatically_requeued
test_response_lost_after_send_reconciles_original_turn
test_recovery_never_submits_an_existing_effect
test_completed_effect_unblocks_next_batch
test_two_sqlite_connections_have_one_wake_claim_winner
```

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_wake_cutover.py -q
```

- [ ] **Step 9: Run existing wake tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_wake_batches.py `
  tests/codex_supervisor/test_wake_scheduler.py `
  tests/codex_supervisor/test_wake_recovery.py `
  tests/codex_supervisor/test_wake_uncertain.py `
  -q
```

- [ ] **Step 10: Root-only commit**

```powershell
git add tools/codex_supervisor/wake_batches.py tools/codex_supervisor/wake_scheduler.py tools/codex_supervisor/wake_recovery.py tests/codex_supervisor/durability/test_wake_cutover.py
git commit -m "refactor: move wake submission onto effect journal"
```

---

# Task 11: Cut Mailbox State Over to the Kernel

**Files:**
- Modify: `tools/codex_supervisor/mailbox_store.py`
- Modify: `tools/codex_supervisor/semantic_scanner.py`
- Create: `tests/codex_supervisor/durability/test_mailbox_cutover.py`

**Interfaces:**
- Produces delivery/intake transitions through the kernel.

- [ ] **Step 1: Replace `_set_delivery()` direct SQL**

It delegates to:

```text
AggregateKind.MAILBOX_DELIVERY
```

using exact `delivery_version`.

- [ ] **Step 2: Replace intake direct SQL**

It delegates to:

```text
AggregateKind.MAILBOX_INTAKE
```

using exact `intake_version`.

- [ ] **Step 3: Make prepared-batch cancellation atomic**

In one transaction:

```text
batch PREPARED → CANCELLED
invalid messages → CANCELLED_SOURCE_RESOLVED
valid siblings → ELIGIBLE
```

- [ ] **Step 4: Tie delivery to effect evidence**

Messages may enter `DELIVERED_TO_TURN` only when:

```text
linked wake effect is RESPONSE_OBSERVED or EFFECT_CONFIRMED
exact turn ID is known
```

- [ ] **Step 5: Preserve in-flight source resolution**

For possible-submission effects:

```text
do not cancel delivery attempt
set source_resolved_after_submission=1
```

- [ ] **Step 6: Add tests**

Required:

```text
test_mailbox_delivery_transition_requires_version
test_mailbox_intake_cannot_skip_ack
test_prepared_batch_cancel_is_atomic
test_delivery_requires_effect_turn_evidence
test_source_resolution_does_not_requeue_write_started_effect
```

- [ ] **Step 7: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_mailbox_cutover.py -q
```

- [ ] **Step 8: Root-only commit**

```powershell
git add tools/codex_supervisor/mailbox_store.py tools/codex_supervisor/semantic_scanner.py tests/codex_supervisor/durability/test_mailbox_cutover.py
git commit -m "refactor: enforce mailbox transitions through kernel"
```

---

# Task 12: Cut Managed Command State Over to the Kernel

**Files:**
- Modify: `tools/codex_supervisor/command_gateway.py`
- Modify: `tools/codex_supervisor/observer_evidence.py`
- Create: `tests/codex_supervisor/durability/test_command_cutover.py`

**Interfaces:**
- Produces command transition and effect reconciliation without direct state SQL.

- [ ] **Step 1: Keep exact command evidence**

Require:

```text
raw stdout
method=item/completed
item_id present
payload item id/type exact
snapshot exact
turn completed
binding thread exact
```

- [ ] **Step 2: Transition command states through kernel**

```text
RECEIVED → VALIDATED → APPLIED
or
RECEIVED/VALIDATED → REJECTED/INCIDENT
```

- [ ] **Step 3: Check source effect before control effect**

Reject if linked turn/wake effect is:

```text
INCIDENT
WRITE_STARTED without reconciliation
SUBMISSION_UNCERTAIN without exact observed turn
```

- [ ] **Step 4: Reconcile crash windows**

If a domain effect receipt exists but supervisor command receipt is missing:

```text
command → INCIDENT
operator reconciliation required
```

If matching receipt exists:

```text
validate exact tuple
command VALIDATED → APPLIED
```

- [ ] **Step 5: Add tests**

Required:

```text
test_command_state_is_versioned
test_command_from_incident_effect_has_no_control_effect
test_command_receipt_reconciliation_is_idempotent
test_missing_receipt_becomes_durable_incident
test_command_cannot_apply_from_unreconciled_possible_submission
```

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_command_cutover.py -q
```

- [ ] **Step 7: Root-only commit**

```powershell
git add tools/codex_supervisor/command_gateway.py tools/codex_supervisor/observer_evidence.py tests/codex_supervisor/durability/test_command_cutover.py
git commit -m "refactor: move managed commands onto transition kernel"
```

---

# Task 13: Implement Atomic One-Shot Operator Resolution

**Files:**
- Create: `tools/codex_supervisor/durability/operator_resolution.py`
- Modify: `tools/codex_supervisor/wake_recovery.py`
- Create: `tests/codex_supervisor/durability/test_operator_resolution.py`

**Interfaces:**
- Produces:
  - `OperatorResolutionService`
  - `ResolutionDisposition`
  - one-shot wake and command incident resolution.

- [ ] **Step 1: Define dispositions**

Wake:

```text
NO_SUBMISSION_EVIDENCE
TURN_OBSERVED_ACTIVE
TURN_OBSERVED_COMPLETED
ABANDON
```

Command:

```text
RECEIPT_CONFIRMED
ABANDON
```

- [ ] **Step 2: Define evidence rules**

`NO_SUBMISSION_EVIDENCE` requires:

```text
effect.state == PREPARED
effect.raw_request_seq is null
effect.client_request_id is null
effect.write_started_at is null
no delivered/uncertain message
```

A `WRITE_STARTED` effect can never use this disposition.

`TURN_OBSERVED_*` requires exact stored evidence:

```text
thread ID matches binding
turn ID exists
clientUserMessageId matches effect client key
mechanical status matches requested disposition
```

- [ ] **Step 3: Implement one transaction**

Within one `BEGIN IMMEDIATE`:

```text
verify aggregate INCIDENT and version
verify no existing resolution
insert operator resolution
transition batch/command
transition all messages
transition effect if applicable
insert transition audit
commit
```

- [ ] **Step 4: Enforce one-shot behavior**

Second resolution receives:

```text
incident already has an operator resolution
```

- [ ] **Step 5: Require explicit operator identity**

The operator value comes only from CLI/process input, never from a model
command.

- [ ] **Step 6: Add concurrency tests**

Two SQLite connections attempting resolution:

```text
exactly one winner
no partial message transitions
```

- [ ] **Step 7: Add regression tests**

Required:

```text
test_write_started_effect_cannot_use_no_submission_resolution
test_prepared_effect_can_return_messages_to_eligible
test_turn_observed_requires_exact_client_key
test_operator_resolution_is_atomic
test_operator_resolution_is_one_shot
test_abandoned_incident_cannot_be_reopened
```

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_operator_resolution.py -q
```

- [ ] **Step 9: Root-only commit**

```powershell
git add tools/codex_supervisor/durability/operator_resolution.py tools/codex_supervisor/wake_recovery.py tests/codex_supervisor/durability/test_operator_resolution.py
git commit -m "feat: add atomic operator incident resolution"
```

---

# Task 14: Implement Unified Effect Reconciliation

**Files:**
- Create: `tools/codex_supervisor/durability/reconciliation.py`
- Modify: `tools/codex_supervisor/wake_recovery.py`
- Modify: `tools/codex_supervisor/provisioning.py`
- Modify: `tools/codex_supervisor/managed_turns.py`
- Create: `tests/codex_supervisor/durability/test_reconciliation.py`

**Interfaces:**
- Produces:
  - `EffectReconciler`
  - method-specific reconciliation handlers.

- [ ] **Step 1: Define the reconciliation registry**

```python
RECONCILERS = {
    "thread/start": reconcile_thread_start,
    "thread/resume": reconcile_thread_resume,
    "turn/start": reconcile_turn_start,
}
```

- [ ] **Step 2: Reconcile without submission**

The reconciler never calls a mutating App Server method.

Allowed reads:

```text
thread/list
thread/read
thread/loaded/list
observer raw/snapshot tables
```

- [ ] **Step 3: Reconcile `turn/start`**

Match:

```text
thread_id
clientUserMessageId
turn_id
mechanical status
```

- [ ] **Step 4: Reconcile `thread/resume`**

`IDLE_LOADED` confirms effect.

`UNKNOWN` remains unresolved.

No second resume.

- [ ] **Step 5: Reconcile `thread/start`**

If response/thread evidence identifies a created thread:

```text
confirm effect
attach original binding
```

If no safe unique evidence exists:

```text
remain SUBMISSION_UNCERTAIN
operator review
```

- [ ] **Step 6: Recover process restart**

Enumerate:

```text
WRITE_STARTED
RESPONSE_OBSERVED
SUBMISSION_UNCERTAIN
```

Never enumerate `PREPARED` for automatic send.

Never enumerate `INCIDENT` for automatic reopen.

- [ ] **Step 7: Add tests**

Required:

```text
test_reconciler_never_calls_mutating_method
test_turn_start_reconciles_by_original_client_key
test_resume_reconciles_loaded_without_resend
test_unknown_thread_start_requires_operator_review
test_restart_reconciliation_is_idempotent
```

- [ ] **Step 8: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_reconciliation.py -q
```

- [ ] **Step 9: Root-only commit**

```powershell
git add tools/codex_supervisor/durability/reconciliation.py tools/codex_supervisor/wake_recovery.py tools/codex_supervisor/provisioning.py tools/codex_supervisor/managed_turns.py tests/codex_supervisor/durability/test_reconciliation.py
git commit -m "feat: reconcile App Server effects without resubmission"
```

---

# Task 15: Cut Observer, Canary, and All Callers Over to the Session Owner

**Files:**
- Modify: `tools/codex_supervisor/observer.py`
- Modify: `tools/codex_supervisor/managed_runtime.py`
- Modify: `tools/codex_supervisor/wake_scheduler.py`
- Modify: `tools/codex_supervisor/provisioning.py`
- Modify: `tools/codex_supervisor/managed_turns.py`
- Modify: `tools/codex_supervisor/session_guard.py`
- Create: `tests/codex_supervisor/durability/test_full_session_cutover.py`

**Interfaces:**
- Produces one process owner for all observer and managed operations.

- [ ] **Step 1: Instantiate one owner in `ObserverService.start()`**

All components receive that owner.

- [ ] **Step 2: Route all reads through `request_read()`**

```text
thread/list
thread/read
thread/loaded/list
```

- [ ] **Step 3: Route all mutations through `submit_effect()`**

```text
thread/start
thread/resume
turn/start
canary thread/start
canary turn/start
```

- [ ] **Step 4: Remove direct per-RPC session wrappers**

`SessionGuard` becomes a deprecated compatibility alias or is removed after
all imports disappear.

- [ ] **Step 5: Keep one server-request consumer**

Static/runtime assertion:

```text
active watcher count == 1 per AppServerClient
```

- [ ] **Step 6: Add end-to-end synthetic tests**

Required:

```text
server request before response
server request plus response
server request after response
canary stops before second mutation
managed wake becomes incident
no duplicate queue consumer
```

- [ ] **Step 7: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_full_session_cutover.py -q
```

- [ ] **Step 8: Root-only commit**

```powershell
git add tools/codex_supervisor/observer.py tools/codex_supervisor/managed_runtime.py tools/codex_supervisor/wake_scheduler.py tools/codex_supervisor/provisioning.py tools/codex_supervisor/managed_turns.py tools/codex_supervisor/session_guard.py tests/codex_supervisor/durability/test_full_session_cutover.py
git commit -m "refactor: centralize App Server process ownership"
```

---

# Task 16: Migrate Legacy Mutation Evidence and Disable New Writes

**Files:**
- Modify: `tools/codex_supervisor/db.py`
- Modify: `tools/codex_supervisor/mutation_intents.py`
- Create: `tests/codex_supervisor/durability/test_legacy_migration.py`

**Interfaces:**
- Produces conservative v6 evidence migration and read-only legacy adapter.

- [ ] **Step 1: Define conservative mapping**

```text
legacy SUBMITTING
  → effect SUBMISSION_UNCERTAIN

legacy SUBMISSION_UNCERTAIN
  → effect SUBMISSION_UNCERTAIN

legacy SUBMITTED_UNRECONCILED
  → effect RESPONSE_OBSERVED only with response/turn evidence;
    otherwise SUBMISSION_UNCERTAIN

legacy SUBMITTED
  → effect RESPONSE_OBSERVED only with response evidence

legacy APPLIED
  → effect EFFECT_CONFIRMED

legacy INCIDENT
  → effect INCIDENT

legacy OPERATOR_RESOLVED
  → effect OPERATOR_RESOLVED
```

Never map legacy `SUBMITTING` to `PREPARED`.

- [ ] **Step 2: Link rows**

Set:

```text
mutation_intents.superseded_by_effect_id
app_server_effects.legacy_intent_id
```

- [ ] **Step 3: Make migration idempotent**

Second run creates no duplicate effect.

- [ ] **Step 4: Disable new writes**

`MutationIntentStore.begin()` raises:

```text
legacy mutation-intent writes are disabled; use EffectJournal
```

Read/query methods remain.

- [ ] **Step 5: Add tests**

Required:

```text
test_legacy_submitting_migrates_fail_closed
test_legacy_applied_migrates_confirmed
test_legacy_migration_is_idempotent
test_new_mutation_intent_writes_are_disabled
test_legacy_rows_are_not_deleted
```

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_legacy_migration.py -q
```

- [ ] **Step 7: Root-only commit**

```powershell
git add tools/codex_supervisor/db.py tools/codex_supervisor/mutation_intents.py tests/codex_supervisor/durability/test_legacy_migration.py
git commit -m "refactor: supersede legacy mutation intents with effects"
```

---

# Task 17: Enforce No Direct State Writes and No Direct Mutation Sends

**Files:**
- Create: `tools/codex_supervisor/durability/static_guards.py`
- Create: `tests/codex_supervisor/durability/test_static_guards.py`

**Interfaces:**
- Produces source-level enforcement used by CI/local tests.

- [ ] **Step 1: Implement direct state-write scanner**

Scan `tools/codex_supervisor/**/*.py`.

Reject SQL that updates protected state columns outside:

```text
durability/transitions.py
durability/operator_resolution.py
db.py migration code
```

- [ ] **Step 2: Implement direct mutating-call scanner**

Reject:

```python
client.request("thread/start", ...)
client.request("thread/resume", ...)
client.request("turn/start", ...)
client.request("turn/steer", ...)
```

outside `durability/session_owner.py`.

- [ ] **Step 3: Reject legacy mutation writes**

Reject:

```text
INSERT INTO mutation_intents
UPDATE mutation_intents SET state
```

outside schema migration/tests.

- [ ] **Step 4: Test the scanners against synthetic violating files**

- [ ] **Step 5: Run against the real package**

Expected:

```text
violations=[]
```

- [ ] **Step 6: Add static guard to the standard test script**

- [ ] **Step 7: Root-only commit**

```powershell
git add tools/codex_supervisor/durability/static_guards.py tests/codex_supervisor/durability/test_static_guards.py
git commit -m "test: prohibit supervisor durability bypasses"
```

---

# Task 18: Add Fault Injection and Concurrency Matrices

**Files:**
- Create: `tests/codex_supervisor/durability/test_fault_matrix.py`
- Create: `tests/codex_supervisor/durability/test_concurrency_matrix.py`
- Modify: new durability modules only if tests expose a defect

**Interfaces:**
- Synthetic crash and concurrency acceptance.

- [ ] **Step 1: Add deterministic failpoints**

Production default is a no-op callable:

```python
fault.hit("effect_after_prepare")
fault.hit("effect_after_write_claim")
fault.hit("effect_after_transport_send")
fault.hit("effect_after_response")
fault.hit("effect_before_domain_apply")
fault.hit("resolution_after_receipt")
```

- [ ] **Step 2: Test every effect crash boundary**

For each failpoint assert:

```text
no automatic second send
durable state explains uncertainty
reconciliation resumes safely
no partial operator resolution
```

- [ ] **Step 3: Test two SQLite connections**

Required races:

```text
two transition CAS callers
two wake claims
two operator resolutions
two effect write claims
lease generation turnover
```

- [ ] **Step 4: Exhaustively test state edges**

For every aggregate and every state pair:

```text
listed edge succeeds
unlisted edge fails
incident exit requires resolution
```

- [ ] **Step 5: Test lexical neutrality**

Inject:

```text
BLOCKED
FAILED
RELEASED
PAUSE
RETIRE
NO FURTHER ACTION
```

into raw agent text and references.

Assert no state graph changes.

- [ ] **Step 6: Run matrix**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/durability/test_fault_matrix.py `
  tests/codex_supervisor/durability/test_concurrency_matrix.py `
  -q
```

- [ ] **Step 7: Root-only commit**

```powershell
git add tests/codex_supervisor/durability/test_fault_matrix.py tests/codex_supervisor/durability/test_concurrency_matrix.py tools/codex_supervisor/durability
git commit -m "test: fault-inject supervisor durability kernel"
```

---

# Task 19: Add Doctor, Timeline, Operator CLI, and PowerShell Operators

**Files:**
- Modify: `tools/codex_supervisor/doctor.py`
- Modify: `tools/codex_supervisor/timeline.py`
- Modify: `tools/codex_supervisor/cli.py`
- Create: `scripts/codex-supervisor-durability-doctor.ps1`
- Create: `scripts/codex-supervisor-durability-test.ps1`
- Create: `tests/codex_supervisor/durability/test_operators.py`

**Interfaces:**
- Produces operational visibility and explicit operator resolution.

- [ ] **Step 1: Extend doctor output**

Required:

```json
{
  "durability_kernel_version": 1,
  "observer_schema_version": 7,
  "direct_state_write_violations": 0,
  "direct_mutation_call_violations": 0,
  "new_legacy_mutation_writes": 0,
  "unreconciled_effect_count": 0,
  "incident_effect_count": 0,
  "automatic_resend_enabled": false,
  "operator_resolution_is_one_shot": true,
  "live_acceptance": false
}
```

- [ ] **Step 2: Add effect timeline**

Display:

```text
PREPARED
WRITE_STARTED
RESPONSE_OBSERVED
EFFECT_CONFIRMED
SUBMISSION_UNCERTAIN
INCIDENT
```

with transition/evidence refs.

- [ ] **Step 3: Add operator commands**

```text
effect show
effect reconcile
incident show
incident resolve-wake
incident resolve-command
```

Every mutation requires `--operator`.

- [ ] **Step 4: Do not expose generic state setting**

There is no:

```text
set-state
force-complete
force-active
```

command.

- [ ] **Step 5: Add PowerShell 5.1 wrappers**

Use arrays, not `ProcessStartInfo.ArgumentList`.

- [ ] **Step 6: Run operator tests**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  .\scripts\codex-supervisor-durability-test.ps1 `
  -RepoRoot C:\Projects\HMASD-durability-kernel-v1 `
  -PythonExecutable C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe
```

- [ ] **Step 7: Root-only commit**

```powershell
git add tools/codex_supervisor/doctor.py tools/codex_supervisor/timeline.py tools/codex_supervisor/cli.py scripts/codex-supervisor-durability-*.ps1 tests/codex_supervisor/durability/test_operators.py
git commit -m "feat: add durability kernel operators"
```

---

# Task 20: Full Migration Verification

**Files:**
- Create: `docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/MIGRATION_REPORT.md`
- Modify source only for defects found by verification

- [ ] **Step 1: Run full test suites**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_semantic_mvp `
  tests/codex_context_lifecycle `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-durability-kernel-v1/.tmp_full
```

- [ ] **Step 2: Run static guards explicitly**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest tests/codex_supervisor/durability/test_static_guards.py -q
```

- [ ] **Step 3: Verify no new legacy writes**

Query:

```sql
SELECT COUNT(*)
FROM mutation_intents
WHERE created_at > <cutover timestamp>;
```

Expected:

```text
0
```

- [ ] **Step 4: Verify all nonterminal domain objects have effect links**

Queries:

```text
managed turn SUBMITTING/SUBMITTED/SUBMISSION_UNCERTAIN/OBSERVED
wake SUBMITTING/SUBMITTED/SUBMISSION_UNCERTAIN/ACTIVE
```

Each must have one `effect_id`.

- [ ] **Step 5: Verify transition-log completeness**

For every aggregate version > 0, the corresponding transition count must
equal the version.

- [ ] **Step 6: Verify runtime remains external**

```powershell
git status --short
git check-ignore runtime/codex-semantic-mvp
```

No supervisor runtime is committed.

- [ ] **Step 7: Write migration report**

Record:

```text
baseline commit
final commit
schema migration
legacy row counts
effect counts by state
transition counts
direct-write inventory before/after
test count
known live-only limitations
```

- [ ] **Step 8: Root-only commit**

```powershell
git add docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/MIGRATION_REPORT.md
git commit -m "docs: verify supervisor durability migration"
```

---

# Task 21: Synthetic Acceptance and Independent Review

**Files:**
- Create: `docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/SYNTHETIC_ACCEPTANCE.md`
- Create: `docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/SYNTHETIC_REVIEW_PROMPT.md`

- [ ] **Step 1: Request independent architecture review**

The review must answer these kernel-level questions, not append dozens of
module-local questions:

```text
1. Can any business module mutate a protected state outside the kernel?
2. Can any business module send a mutation outside the session owner?
3. Can WRITE_STARTED or later ever be automatically submitted again?
4. Can INCIDENT exit without one operator resolution?
5. Can an operator resolution partially commit or execute twice?
6. Can aggregate state and effect state contradict after any failpoint?
7. Can recovery perform a mutating App Server request?
8. Can raw prose affect state, routing, ACL, retry, or resolution?
9. Can a released/non-ACTIVE actor receive a managed effect?
10. Can live acceptance be inferred from synthetic evidence?
```

- [ ] **Step 2: Request code review**

Focus:

```text
SQLite transaction ownership
version/CAS correctness
async cancellation
pending future cleanup
server-request watcher lifetime
effect/raw evidence correlation
operator evidence validation
migration conservatism
```

- [ ] **Step 3: Close all Critical/High findings**

Medium findings require either correction or explicit accepted limitation with
a bounded reason.

- [ ] **Step 4: Write synthetic acceptance**

Accepted capabilities:

```text
single transition kernel
single mutating session owner
effect journal
at-most-one automatic attempt
evidence-based reconciliation
terminal incidents
atomic one-shot operator resolution
fault-injection recovery
```

Absent capabilities:

```text
live App Server acceptance
Stage 5 DAG
automatic approvals
write-capability profiles
additional managed actor kinds
distributed workflow engine
Agents SDK
```

- [ ] **Step 5: Run final tests fresh**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_semantic_mvp `
  tests/codex_context_lifecycle `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-durability-kernel-v1/.tmp_acceptance
```

- [ ] **Step 6: Root-only acceptance commit**

```powershell
git add docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel
git commit -m "docs: accept supervisor durability kernel v1"
```

**Hard gate:**

Do not resume Stage 5 feature work until the independent synthetic disposition
is accepted.

---

# Part V — Acceptance Matrix

| Invariant | Required evidence | Pass condition |
|---|---|---|
| One transition writer | static guard + code review | zero bypasses |
| One mutation sender | static guard + session tests | zero direct mutating calls |
| At-most-one automatic attempt | effect journal + fault matrix | no resend after WRITE_STARTED |
| PREPARED unsent proof | effect/raw linkage | no write evidence exists |
| Incident terminality | graphs + triggers + tests | no automatic exit |
| Operator resolution | transaction + unique row | atomic and one-shot |
| State/effect consistency | failpoint matrix | no divergent terminal pair |
| Wake liveness | restart/recovery tests | no stranded valid message |
| Mailbox correctness | effect-bound delivery | no false delivery |
| Command correctness | exact item/effect evidence | no incident effect applied |
| Server requests | process-lifetime owner | persist, incident, terminate |
| Legacy evidence | migration tests | no deletion, fail-closed mapping |
| Memory boundary | policy/doctor | automatic Memory has no authority |
| Runtime location | config/test | external only |
| Live honesty | acceptance docs | live remains absent until run |

---

# Part VI — Explicit Non-Goals After Kernel V1

The following remain unavailable after this plan:

```text
automatic EM/CM managed threads
arbitrary peer mailbox
automatic turn/steer
automatic approval
automatic code-write wake turns
runtime task DAG
capability-based write roles
scientific retry policy
Portfolio decision automation
Windows background service
web debugger UI
Agents SDK
Codex SDK
Codex Rust fork
```

---

# Part VII — Follow-On Order

After synthetic kernel acceptance:

```text
1. Restore quota.
2. Run Phase 1 live App Server observer acceptance.
3. Run Stage 3 Root/Portfolio binding canaries.
4. Run Stage 4 mailbox/wake canaries.
5. Reconcile any live protocol differences.
6. Only then design macro Stage 5 runtime DAG/capability work.
```

Live work may expose protocol facts, but it must not weaken the durability
kernel.

---

# Execution Handoff for Grok Build

Save this plan at:

```text
docs/superpowers/plans/2026-08-19-hmasd-codex-supervisor-durability-kernel-v1.md
```

Use this exact execution instruction:

```text
Use the openaiDeveloperDocs MCP only for current OpenAI/Codex/App Server
reference. Verify every wire field against the schema generated by the exact
installed Codex binary.

Read:
- AGENTS.md
- docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
- docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
- docs/research/workflow-runs/2026-08-18_codex-managed-actors/PROTOCOL_EVIDENCE.md
- this complete plan

Execute task-by-task with test-first implementation and independent review
between tasks.

Do not add Agents SDK, Codex SDK, a durable workflow product, Stage 5
features, new managed actor kinds, automatic approval, or live App Server
requirements.

Do not preserve module-local state writes for convenience.
Do not send a mutating App Server request outside AppServerSessionOwner.
Do not automatically resubmit an effect after WRITE_STARTED.
Do not reopen INCIDENT except through one atomic operator resolution.
Do not delete legacy evidence.
Only Operational Root may commit.

Stop at the first failed hard gate and return the exact mechanical evidence.
```
