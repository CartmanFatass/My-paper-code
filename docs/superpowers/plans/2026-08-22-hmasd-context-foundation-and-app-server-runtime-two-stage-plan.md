# HMASD Context Foundation Closure and App Server Runtime Control — Two-Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:using-git-worktrees` before each stage, `superpowers:systematic-debugging` for unexpected behavior, and `superpowers:verification-before-completion` before any acceptance or merge claim. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining ADR, `PROJECT_MAP`, context-source, current-work, recovery-intake, and read-only MCP gaps first; then turn the existing Codex App Server supervisor and durability kernel into an explicit, live, operator-controlled runtime for Operational Root and Portfolio without restoring behavioral Hooks or moving semantic authority into SQLite.

**Architecture:** Stage 1 completes the repository-owned semantic foundation. Canonical truth stays in owner-authored files; ADRs, the single `PROJECT_MAP`, `CURRENT_WORK`, the source registry, assignments/results, and promotion rules are validated and exposed through bounded read-only queries. Stage 2 adds a long-lived App Server host with an external runtime directory, truthful readiness, a typed local command channel, manual managed actors, manual mailbox delivery, and one explicitly armed single wake. The supervisor owns transport, delivery, effect durability, and recovery only; it never interprets science, technical acceptance, or Portfolio meaning.

**Tech Stack:** Python 3.10 project interpreter; stdlib `dataclasses`, `enum`, `json`, `pathlib`, `sqlite3`, `asyncio`, `os`, `tempfile`, `uuid`, `datetime`; `tomllib` with `tomli` fallback; existing `mcp.server`; Windows PowerShell 5.1; existing `tools/codex_context_lifecycle/`, `tools/codex_semantic_mvp/`, `tools/hmasd_control_plane/`, and `tools/codex_supervisor/`; pytest with explicit `--basetemp`.

**Spec:**
- `docs/project/CONTEXT_PRECEDENCE.md`
- `docs/project/CONTEXT_PROMOTION_POLICY.md`
- `docs/project/CONTEXT_RETENTION_POLICY.md`
- `docs/project/PROJECT_MAP.md`
- `docs/project/CURRENT_WORK.md`
- `docs/project/CONTEXT_SOURCE_REGISTRY.toml`
- `docs/project/LOW_INTRUSION_CONTROL_PLANE.md`
- `docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md`
- `docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md`
- `docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md`
- `docs/project/PROJECT_REQUIREMENTS.toml`
- `docs/superpowers/plans/2026-08-22-hmasd-low-intrusion-drift-containment-resource-grounded-execution-v2.md`

**Planning baseline:** `aggressive` was at `7cc1a56c188d39af61ee70979adc4e2dd1e9c0ae` when this plan was authored. Each stage records its actual fetched baseline before editing; do not assume the planning baseline is still HEAD.

## Global Constraints

1. Repository-owned owner artifacts remain canonical.
2. Runtime SQLite databases are noncanonical ledgers.
3. Automatic Memory, compacted context, raw conversation, tool output, child prose, App Server status, and runtime receipts cannot create authority or semantic disposition.
4. `docs/project/PROJECT_MAP.md` remains the only stable codemap. Do not add `CODEMAP.md`.
5. `docs/project/CURRENT_WORK.md` remains a pointer index, not a project-state monolith.
6. ADRs cover only durable shared architecture, harness, context, and control-plane choices.
7. ADRs do not restate scientific decisions, technical acceptance, or Portfolio allocation.
8. Canonical files are written only by their semantic owner or an explicitly authorized writer.
9. MCP tools may inspect repository context and record noncanonical ledger state; they do not edit ADRs, `PROJECT_MAP`, `CURRENT_WORK`, science cards, CM acceptance, or Portfolio artifacts.
10. Behavioral Hooks remain disabled.
11. Do not install `SessionStart`, `Stop`, `SubagentStart`, `SubagentStop`, `PreToolUse`, `PreCompact`, or `PostCompact` as active control-plane behavior.
12. Native auto-compaction remains unchanged.
13. Do not add per-turn drift prompts, workflow-wide self-audits, format-repair turns, or forced continuation turns.
14. Do not add a four-layer recovery-maturity state machine.
15. Do not add generic `PREFLIGHT_ONLY` / `SEND_ARMED` transaction states.
16. Do not require a fresh-operator receipt for every provider operation.
17. Do not bind every acceptance to a commit/runtime/document triple as a runtime admission gate.
18. Preserve the narrower rule: evidence may not be textually upgraded.
19. Every WRM assignment names one observable recovery outcome.
20. `RECOVERED` is valid only when that exact outcome was directly observed and evidence is named.
21. Parent intake may preserve or lower a child-proven recovery status; it may not raise it.
22. Scope-local incidents remain E0–E5 and route to the smallest capable owner.
23. Ordinary code, test, and documentation tasks do not inherit App Server ceremony.
24. The App Server supervisor never writes canonical repository artifacts.
25. The supervisor manages only `OPERATIONAL_ROOT` and `PORTFOLIO` in this plan.
26. EM, CM, and leaf actors remain native Codex/subagent workflows in this plan.
27. No automatic Provider send is introduced.
28. No automatic approval is introduced.
29. No automatic `turn/steer` is introduced.
30. Unknown App Server mutations are never retried.
31. `WRITE_STARTED` or later is never automatically submitted again.
32. `INCIDENT` exits only through one evidence-bound operator resolution.
33. Scheduler serve remains disabled.
34. Automatic wake is permitted only in the final Stage 2 one-shot profile and at most once per host run.
35. Ordinary sessions remain unmanaged.
36. Starting an observer does not bind an actor.
37. Starting a managed host does not create or modify a semantic workflow.
38. App Server thread identity is only `threadId → binding_id → actor_context_id`.
39. Thread title, preview, prose, and model role labels never establish identity.
40. Runtime data stays outside the repository under `%LOCALAPPDATA%\HMASD\codex-supervisor`.
41. Tests use `tmp_path` or an explicit repository `--basetemp`; they never write the live runtime directory.
42. Use `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
43. PowerShell wrappers must run under Windows PowerShell 5.1.
44. Only Operational Root stages, commits, pushes, merges, edits global requirements, or changes live runtime profile.
45. Every task ends with a focused test cycle and one reviewable commit.
46. Stop at the first hard-gate failure.

---

# Existing Assets — Extend, Do Not Rebuild

The implementation already contains:

```text
docs/project/decisions/ADR-0001..ADR-0004
docs/project/DECISIONS_INDEX.md
tools/codex_context_lifecycle/decisions.py
tools/codex_context_lifecycle/project_map.py
tools/codex_context_lifecycle/source_registry.py
tools/codex_context_lifecycle/doctor.py
tools/codex_context_lifecycle/cli.py

tools/codex_semantic_mvp/mcp_server.py
tools/hmasd_control_plane/mcp_server.py

tools/codex_supervisor/
tools/codex_supervisor/durability/
scripts/codex-app-server-observer-*.ps1
scripts/codex-managed-actor-*.ps1
scripts/codex-mailbox-*.ps1
scripts/hmasd-root-supervisor-*.ps1
```

Do not replace these with a new context database, a new codemap, a new orchestration framework, or an Agents SDK application.

---

# Stage 1 — Repository Context Foundation Closure

## Stage 1 Result

Stage 1 is independently mergeable. At completion:

```text
ADRs cover the current durable architecture.
ADR validation enforces owner/source/supersession rules.
PROJECT_MAP validation covers the actual current control-plane surfaces.
The source registry covers all current canonical context-policy surfaces.
CURRENT_WORK has validated, existing pointer targets.
WRM recovery status cannot be textually upgraded.
Constraint lint scans project policies, Roles, and Skills.
Read-only context queries are available through hmasd_observability.
A current-head context doctor report exists.
A real measured runtime calibration exists.
One real long-task assignment/intake pilot has been completed.
Behavioral Hooks remain disabled.
```

Stage 2 must not begin until Stage 1 has no open Critical/High review finding and has been merged or an exact accepted Stage 1 commit has been supplied as its baseline.

---

## Task 0: Create the Stage 1 Worktree and Freeze the Baseline

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_BASELINE.md`
- No behavioral modification

**Interfaces:**
- Consumes: current `origin/aggressive`
- Produces: exact Stage 1 baseline commit and clean isolated worktree

- [ ] **Step 1: Detect whether the current shell is already in a linked worktree**

```powershell
$gitDir = (git rev-parse --git-dir).Trim()
$gitCommon = (git rev-parse --git-common-dir).Trim()
$branch = (git branch --show-current).Trim()
Write-Output "git_dir=$gitDir"
Write-Output "git_common=$gitCommon"
Write-Output "branch=$branch"
```

Expected: record whether `git_dir` differs from `git_common`.

- [ ] **Step 2: If not already isolated, create the Stage 1 worktree**

```powershell
Set-Location C:\Projects\HMASD
git fetch origin
git worktree add `
  C:\Projects\HMASD-context-foundation-closure `
  -b codex-context-foundation-closure-v1 `
  origin/aggressive
Set-Location C:\Projects\HMASD-context-foundation-closure
```

- [ ] **Step 3: Confirm the worktree is clean and record the exact baseline**

```powershell
git status --short
git rev-parse HEAD
git log -8 --oneline
```

Expected: empty status. Save the exact `git rev-parse HEAD` output in `STAGE1_BASELINE.md`.

- [ ] **Step 4: Run the existing context/control baseline**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle `
  tests/hmasd_control_plane `
  tests/codex_semantic_mvp `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_stage1_baseline
```

Expected: current baseline result recorded exactly. A failure is a hard gate; diagnose before implementing.

- [ ] **Step 5: Record current foundation facts**

Run:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m tools.codex_context_lifecycle.cli `
  decisions-index `
  --repo-root C:/Projects/HMASD-context-foundation-closure

& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m tools.codex_context_lifecycle.cli `
  doctor `
  --repo-root C:/Projects/HMASD-context-foundation-closure
```

Record:

```text
decision index currentness
source registry validity
PROJECT_MAP contract validity
active actor count
open promotion count
prepared rollover count
hooks=false
```

- [ ] **Step 6: Commit the baseline record**

```powershell
git add docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_BASELINE.md
git commit -m "docs: freeze context foundation closure baseline"
```

---

## Task 1: Add the Missing Shared ADRs

**Files:**
- Create: `docs/project/decisions/ADR-0005-low-intrusion-artifact-first-control-plane.md`
- Create: `docs/project/decisions/ADR-0006-app-server-supervisor-is-noncanonical-runtime-plane.md`
- Create: `docs/project/decisions/ADR-0007-file-anchored-project-map-dispatch.md`
- Regenerate: `docs/project/DECISIONS_INDEX.md`
- Test: `tests/codex_context_lifecycle/test_decision_records.py`

**Interfaces:**
- Consumes: existing ADR TOML-front-matter format
- Produces: three accepted shared ADRs and deterministic index entries

- [ ] **Step 1: Write failing tests for the three expected ADR IDs**

Add:

```python
def test_current_shared_architecture_adrs_are_present(repo_root):
    records = {item.decision_id: item for item in collect_decisions(repo_root)}
    assert records["ADR-0005"].status == "accepted"
    assert records["ADR-0006"].status == "accepted"
    assert records["ADR-0007"].status == "accepted"
```

- [ ] **Step 2: Run the focused test and confirm failure**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_decision_records.py::test_current_shared_architecture_adrs_are_present `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_adr_presence
```

Expected: failure because ADR-0005 through ADR-0007 do not exist.

- [ ] **Step 3: Create ADR-0005 with this controlling decision**

```toml
+++
decision_id = "ADR-0005"
title = "Normal workflow uses low-intrusion artifact-first control"
owner = "operational_root"
scope = "shared:codex-context-control-plane"
status = "accepted"
decision_date = "2026-08-22"
supersedes = []
canonical_sources = [
  "docs/project/LOW_INTRUSION_CONTROL_PLANE.md",
  "docs/project/PROJECT_REQUIREMENTS.toml",
  "docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md"
]
revisit_conditions = [
  "A measured live workflow demonstrates that artifact-first boundaries cannot provide required liveness without behavioral hooks."
]
+++
```

Body requirements:

```text
Behavioral lifecycle Hooks are not part of normal workflow.
Native auto-compaction is unchanged.
Assignments/results and owner intake contain drift.
This ADR does not forbid explicit App Server runtime control.
```

- [ ] **Step 4: Create ADR-0006 with this controlling decision**

```toml
+++
decision_id = "ADR-0006"
title = "App Server supervisor is a noncanonical runtime plane"
owner = "operational_root"
scope = "shared:codex-app-server-runtime"
status = "accepted"
decision_date = "2026-08-22"
supersedes = []
canonical_sources = [
  "docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md",
  "docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md",
  "docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md"
]
revisit_conditions = [
  "The supervisor is replaced by a different owner-authorized runtime implementation."
]
+++
```

Body requirements:

```text
The supervisor owns mechanical runtime, delivery, effect durability, wake, and incident recovery.
It does not own science, technical acceptance, Portfolio meaning, ADRs, PROJECT_MAP, or canonical project state.
```

- [ ] **Step 5: Create ADR-0007 with this controlling decision**

```toml
+++
decision_id = "ADR-0007"
title = "Nontrivial code dispatch is file-anchored and PROJECT_MAP-grounded"
owner = "operational_root"
scope = "shared:codex-assignment-control"
status = "accepted"
decision_date = "2026-08-22"
supersedes = []
canonical_sources = [
  "docs/project/PROJECT_MAP.md",
  "docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md"
]
revisit_conditions = [
  "A later sole repository architecture map replaces PROJECT_MAP.md by explicit owner decision."
]
+++
```

Body requirements:

```text
Abstract labels do not establish scope.
Implementation/review assignments name exact files or bounded discovery roots, PROJECT_MAP anchor, state owner, and direct consumer.
```

- [ ] **Step 6: Regenerate the decision index**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m tools.codex_context_lifecycle.cli `
  decisions-index `
  --repo-root C:/Projects/HMASD-context-foundation-closure
```

- [ ] **Step 7: Run the focused test**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_decision_records.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_adr_presence
```

Expected: pass.

- [ ] **Step 8: Commit**

```powershell
git add docs/project/decisions docs/project/DECISIONS_INDEX.md tests/codex_context_lifecycle/test_decision_records.py
git commit -m "docs: record current shared control-plane decisions"
```

---

## Task 2: Strengthen ADR Validation

**Files:**
- Modify: `tools/codex_context_lifecycle/decisions.py`
- Modify: `tests/codex_context_lifecycle/test_decision_records.py`

**Interfaces:**
- Consumes: `DecisionRecord`, ADR front matter
- Produces:
  - `validate_decision_set(root: Path, records: tuple[DecisionRecord, ...]) -> tuple[str, ...]`
  - stronger `collect_decisions(root)` failure behavior

- [ ] **Step 1: Add failing owner validation test**

```python
def test_shared_accepted_adr_rejects_non_root_owner(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0099",
        owner="cm",
        status="accepted",
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    with pytest.raises(DecisionError, match="shared accepted ADR owner"):
        collect_decisions(tmp_path)
```

- [ ] **Step 2: Add failing canonical-source existence test**

```python
def test_accepted_adr_requires_existing_canonical_source(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0098",
        owner="operational_root",
        status="accepted",
        canonical_sources=["docs/project/missing.md"],
    )
    with pytest.raises(DecisionError, match="missing canonical source"):
        collect_decisions(tmp_path)
```

- [ ] **Step 3: Add failing supersession consistency tests**

```python
def test_supersedes_requires_existing_adr(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0097",
        owner="operational_root",
        status="accepted",
        supersedes=["ADR-0042"],
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    with pytest.raises(DecisionError, match="unknown superseded ADR"):
        collect_decisions(tmp_path)

def test_accepted_replacement_requires_old_record_superseded(tmp_path):
    write_adr(
        tmp_path,
        decision_id="ADR-0096",
        owner="operational_root",
        status="accepted",
        supersedes=["ADR-0095"],
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    write_adr(
        tmp_path,
        decision_id="ADR-0095",
        owner="operational_root",
        status="accepted",
        canonical_sources=["docs/project/PROJECT_MAP.md"],
    )
    with pytest.raises(DecisionError, match="must be marked superseded"):
        collect_decisions(tmp_path)
```

- [ ] **Step 4: Run tests and confirm failure**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_decision_records.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_adr_validation
```

- [ ] **Step 5: Implement set-level validation**

Add:

```python
SHARED_ADR_OWNERS = frozenset({"operational_root", "user"})

def validate_decision_set(
    root: Path,
    records: tuple[DecisionRecord, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    by_id = {item.decision_id: item for item in records}
    for record in records:
        if record.status == "accepted" and record.scope.startswith("shared:"):
            if record.owner not in SHARED_ADR_OWNERS:
                errors.append(
                    f"{record.decision_id}: shared accepted ADR owner must be operational_root or user"
                )
        for source in record.canonical_sources:
            if record.status == "accepted" and not (Path(root) / source).is_file():
                errors.append(
                    f"{record.decision_id}: missing canonical source {source}"
                )
        for superseded_id in record.supersedes:
            peer = by_id.get(superseded_id)
            if peer is None:
                errors.append(
                    f"{record.decision_id}: unknown superseded ADR {superseded_id}"
                )
            elif record.status == "accepted" and peer.status != "superseded":
                errors.append(
                    f"{record.decision_id}: superseded ADR {superseded_id} must be marked superseded"
                )
    return tuple(errors)
```

Make `collect_decisions(root)` raise one `DecisionError` containing all errors.

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_decision_records.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_adr_validation
```

Expected: pass.

- [ ] **Step 7: Commit**

```powershell
git add tools/codex_context_lifecycle/decisions.py tests/codex_context_lifecycle/test_decision_records.py
git commit -m "fix: enforce ADR owner source and supersession rules"
```

---

## Task 3: Close PROJECT_MAP Coverage

**Files:**
- Modify: `docs/project/PROJECT_MAP.md`
- Modify: `tools/codex_context_lifecycle/project_map.py`
- Modify: `tests/codex_context_lifecycle/test_project_map_contract.py`

**Interfaces:**
- Consumes: existing sole-codemap invariant
- Produces:
  - a new `Codex App Server runtime plane` heading
  - current-surface coverage in `validate_project_map()`

- [ ] **Step 1: Add failing tests for current control-plane surfaces**

```python
def test_project_map_requires_current_control_plane_surfaces(tmp_path):
    map_path = write_minimal_valid_project_map(tmp_path)
    text = map_path.read_text(encoding="utf-8")
    text = text.replace("tools/hmasd_control_plane/", "")
    map_path.write_text(text, encoding="utf-8")
    errors = validate_project_map(map_path)
    assert "missing path: tools/hmasd_control_plane/" in errors
```

Add analogous checks for:

```text
tools/codex_supervisor/
docs/project/PROJECT_REQUIREMENTS.toml
docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
```

- [ ] **Step 2: Add failing heading test**

```python
def test_project_map_requires_app_server_runtime_heading(tmp_path):
    map_path = write_minimal_valid_project_map(tmp_path)
    text = map_path.read_text(encoding="utf-8").replace(
        "## Codex App Server runtime plane\n", ""
    )
    map_path.write_text(text, encoding="utf-8")
    assert "missing heading: Codex App Server runtime plane" in validate_project_map(map_path)
```

- [ ] **Step 3: Run focused tests and confirm failure**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_project_map_contract.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_map_contract
```

- [ ] **Step 4: Add the App Server runtime section to PROJECT_MAP**

The section must name:

```text
tools/codex_supervisor/
tools/codex_supervisor/durability/
tests/codex_supervisor/
scripts/codex-app-server-observer-*.ps1
scripts/codex-managed-actor-*.ps1
scripts/codex-mailbox-*.ps1
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
```

The section must state:

```text
runtime SQLite is external and noncanonical
supervisor owns mechanical transport/delivery/recovery
canonical repository artifacts remain owner-authored
managed actor identity is threadId → binding_id → actor_context_id
```

- [ ] **Step 5: Extend required headings and paths**

Add to `REQUIRED_HEADINGS`:

```python
"Low-intrusion control-plane route",
"Codex App Server runtime plane",
```

Add to `REQUIRED_PATHS`:

```python
"tools/hmasd_control_plane/",
"tools/codex_supervisor/",
"tests/codex_supervisor/",
"docs/project/PROJECT_REQUIREMENTS.toml",
"docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md",
"docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md",
"docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md",
"docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md",
```

Add required phrases:

```python
"supervisor runtime SQLite is noncanonical",
"supervisor does not write canonical repository artifacts",
```

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_project_map_contract.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_map_contract
```

- [ ] **Step 7: Commit**

```powershell
git add docs/project/PROJECT_MAP.md tools/codex_context_lifecycle/project_map.py tests/codex_context_lifecycle/test_project_map_contract.py
git commit -m "docs: close PROJECT_MAP control-plane coverage"
```

---

## Task 4: Close Context Source Registry Coverage

**Files:**
- Modify: `docs/project/CONTEXT_SOURCE_REGISTRY.toml`
- Modify: `tools/codex_context_lifecycle/source_registry.py`
- Test: `tests/codex_context_lifecycle/test_source_registry.py`

**Interfaces:**
- Consumes: `ContextSourceRegistry`
- Produces:
  - required-source coverage validation
  - actor-filtered read-only source selection with direction/scope filtering

- [ ] **Step 1: Add required source IDs**

Add canonical sources:

```toml
[[source]]
id = "decision-index"
path = "docs/project/DECISIONS_INDEX.md"
kind = "NAVIGATION"
owner = "operational_root"
actors = ["PORTFOLIO", "OPERATIONAL_ROOT", "CM"]
load_policy = "ON_DEMAND"
canonical = true

[[source]]
id = "app-server-observer-policy"
path = "docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md"
kind = "PROCEDURE"
owner = "operational_root"
actors = ["OPERATIONAL_ROOT", "CM"]
load_policy = "ASSIGNMENT_ONLY"
canonical = true

[[source]]
id = "managed-actor-mailbox-policy"
path = "docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md"
kind = "PROCEDURE"
owner = "operational_root"
actors = ["PORTFOLIO", "OPERATIONAL_ROOT"]
load_policy = "ASSIGNMENT_ONLY"
canonical = true

[[source]]
id = "durability-kernel-policy"
path = "docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md"
kind = "CANONICAL_OWNER_ARTIFACT"
owner = "operational_root"
actors = ["OPERATIONAL_ROOT", "CM"]
load_policy = "ASSIGNMENT_ONLY"
canonical = true
```

- [ ] **Step 2: Add failing required-ID test**

```python
def test_registry_contains_current_context_foundation_sources(repo_root):
    registry = load_registry(
        repo_root / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    )
    ids = {item.id for item in registry.sources}
    assert {
        "decision-index",
        "app-server-observer-policy",
        "managed-actor-mailbox-policy",
        "durability-kernel-policy",
    } <= ids
```

- [ ] **Step 3: Add optional `direction_id` and `scope_key` fields**

Extend `ContextSource` additively:

```python
direction_id: str | None = None
scope_key: str | None = None
```

Parse optional fields from TOML.

- [ ] **Step 4: Add filtering tests**

```python
def test_direction_scoped_source_is_not_selected_for_other_direction(tmp_path):
    registry = registry_with_source(
        actors=("EM",),
        direction_id="direction:alpha",
        load_policy="ASSIGNMENT_REFERENCED",
    )
    assert sources_for_actor(
        registry,
        "EM",
        direction_id="direction:beta",
        requested_source_ids=("source-x",),
    ) == ()
```

Add equivalent `scope_key` test.

- [ ] **Step 5: Implement filtering**

In `sources_for_actor()`:

```python
if source.direction_id is not None and source.direction_id != direction_id:
    continue
if source.scope_key is not None and source.scope_key != scope_key:
    continue
```

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_source_registry.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_source_registry
```

- [ ] **Step 7: Commit**

```powershell
git add docs/project/CONTEXT_SOURCE_REGISTRY.toml tools/codex_context_lifecycle/source_registry.py tools/codex_context_lifecycle/models.py tests/codex_context_lifecycle/test_source_registry.py
git commit -m "feat: close context source registry coverage"
```

---

## Task 5: Validate CURRENT_WORK as a Pointer Index

**Files:**
- Create: `tools/codex_context_lifecycle/current_work.py`
- Modify: `tools/codex_context_lifecycle/doctor.py`
- Modify: `tools/codex_context_lifecycle/cli.py`
- Modify: `docs/project/CURRENT_WORK.md`
- Create: `docs/project/current-work/common/control_plane_runtime.md`
- Test: `tests/codex_context_lifecycle/test_current_work_index.py`

**Interfaces:**
- Produces:
  - `CurrentWorkPointer`
  - `collect_current_work(root: Path) -> tuple[CurrentWorkPointer, ...]`
  - `validate_current_work(root: Path) -> tuple[str, ...]`

- [ ] **Step 1: Write failing missing-target test**

```python
def test_current_work_rejects_missing_pointer(tmp_path):
    path = tmp_path / "docs/project/CURRENT_WORK.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Current Work\n\n- [Missing](current-work/common/missing.md)\n",
        encoding="utf-8",
    )
    assert validate_current_work(tmp_path) == (
        "missing CURRENT_WORK target: docs/project/current-work/common/missing.md",
    )
```

- [ ] **Step 2: Write failing competing-state test**

The validator must reject a top-level section named:

```text
## Canonical project state
```

because `CURRENT_WORK` is a pointer index.

- [ ] **Step 3: Implement Markdown-link collection**

```python
@dataclass(frozen=True)
class CurrentWorkPointer:
    title: str
    path: str
    section: str

_LINK = re.compile(r"^- \[([^\]]+)\]\(([^)]+)\)\s*$")
```

Only repository-relative links under `docs/project/` are considered managed pointers.

- [ ] **Step 4: Add the control-plane runtime pointer record**

`control_plane_runtime.md` contains:

```text
owner=operational_root
current_milestone=STAGE1_CONTEXT_FOUNDATION_CLOSURE
assignment_refs=docs/superpowers/plans/2026-08-22-hmasd-context-foundation-and-app-server-runtime-two-stage-plan.md
owner_state_refs=docs/project/LOW_INTRUSION_CONTROL_PLANE.md|docs/project/DECISIONS_INDEX.md
next_decision_boundary=STAGE1_ACCEPTANCE
```

It is a pointer record, not an execution log.

- [ ] **Step 5: Add doctor and CLI output**

Doctor key:

```python
"current_work_valid": validate_current_work(root) == ()
```

CLI command:

```text
context-lifecycle current-work --repo-root ...
```

returns pointer objects as JSON.

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_current_work_index.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_current_work
```

- [ ] **Step 7: Commit**

```powershell
git add tools/codex_context_lifecycle/current_work.py tools/codex_context_lifecycle/doctor.py tools/codex_context_lifecycle/cli.py docs/project/CURRENT_WORK.md docs/project/current-work/common/control_plane_runtime.md tests/codex_context_lifecycle/test_current_work_index.py
git commit -m "feat: validate CURRENT_WORK pointer integrity"
```

---

## Task 6: Enforce Minimal Recovery Outcome Without a Maturity State Machine

**Files:**
- Modify: `docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md`
- Modify: `docs/project/templates/ASSIGNMENT_TEMPLATE.md`
- Modify: `docs/project/templates/RESULT_TEMPLATE.md`
- Modify: `tools/hmasd_control_plane/artifact_protocol.py`
- Modify: `tools/hmasd_control_plane/intake_router.py`
- Modify: `.agents/roles/WORKFLOW_RECOVERY_MANAGER.md`
- Modify: `.agents/roles/ROOT.md`
- Test: `tests/hmasd_control_plane/test_artifact_protocol.py`
- Test: `tests/hmasd_control_plane/test_intake_router.py`

**Interfaces:**
- Adds optional assignment field:
  - `acceptance_outcome: str`
- Adds result fields:
  - `acceptance_observed: Literal["TRUE", "FALSE", "UNKNOWN"]`
  - `acceptance_evidence: tuple[str, ...]`

- [ ] **Step 1: Add failing WRM assignment test**

```python
def test_wrm_assignment_requires_acceptance_outcome(valid_assignment):
    assignment = replace(
        valid_assignment,
        executor_role="hmasd-workflow-recovery-manager",
        acceptance_outcome="",
    )
    assert "WRM assignment requires acceptance_outcome" in validate_assignment(
        assignment, {}
    )
```

- [ ] **Step 2: Add failing recovered-without-observation test**

```python
def test_wrm_completed_result_requires_observed_acceptance(valid_wrm_assignment):
    result = valid_result(
        result_kind="COMPLETED",
        acceptance_observed="UNKNOWN",
        acceptance_evidence=(),
    )
    assert "WRM COMPLETED requires directly observed acceptance" in validate_result(
        result, valid_wrm_assignment
    )
```

- [ ] **Step 3: Add failing parent-upgrade test**

```python
def test_parent_cannot_upgrade_unobserved_recovery(valid_wrm_assignment):
    result = valid_result(
        result_kind="PARTIAL",
        acceptance_observed="FALSE",
        acceptance_evidence=("docs/session/runtime-boundary.md",),
    )
    decision = route_result(valid_wrm_assignment, result, {})
    assert decision.disposition_created is False
    assert decision.root_action == "ROUTE_SCOPE_LOCAL"
```

Add a second test that a result containing an intake claim `RECOVERED` in prose has no effect because only metadata is parsed.

- [ ] **Step 4: Parse the additive fields**

For old assignments/results, defaults are:

```python
acceptance_outcome = ""
acceptance_observed = "UNKNOWN"
acceptance_evidence = ()
```

No schema migration or new recovery state table is added.

- [ ] **Step 5: Add exact validation rules**

```python
if assignment.executor_role == "hmasd-workflow-recovery-manager":
    if not assignment.acceptance_outcome.strip():
        errors.append("WRM assignment requires acceptance_outcome")

if assignment.executor_role == "hmasd-workflow-recovery-manager":
    if result.result_kind == "COMPLETED":
        if result.acceptance_observed != "TRUE" or not result.acceptance_evidence:
            errors.append(
                "WRM COMPLETED requires directly observed acceptance and evidence"
            )
```

- [ ] **Step 6: Update Role text compactly**

WRM Role:

```text
RECOVERED means the assignment's exact acceptance_outcome was directly observed.
Source edits, tests, plans, process start, or a narrower substitute do not satisfy it.
```

Root Role:

```text
Parent intake may preserve or lower child-proven recovery status; it may not raise it.
```

Do not add maturity layers or receipts.

- [ ] **Step 7: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/hmasd_control_plane/test_artifact_protocol.py `
  tests/hmasd_control_plane/test_intake_router.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_recovery_outcome
```

- [ ] **Step 8: Commit**

```powershell
git add docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md docs/project/templates/ASSIGNMENT_TEMPLATE.md docs/project/templates/RESULT_TEMPLATE.md tools/hmasd_control_plane/artifact_protocol.py tools/hmasd_control_plane/intake_router.py .agents/roles/WORKFLOW_RECOVERY_MANAGER.md .agents/roles/ROOT.md tests/hmasd_control_plane/test_artifact_protocol.py tests/hmasd_control_plane/test_intake_router.py
git commit -m "fix: prevent textual recovery status upgrades"
```

---

## Task 7: Extend Constraint Lint to Roles and Skills

**Files:**
- Modify: `tools/hmasd_control_plane/constraint_lint.py`
- Modify: `tests/hmasd_control_plane/test_constraint_lint.py`
- Review and minimally reconcile: `.agents/roles/CODE_PROJECT_MANAGER.md`

**Interfaces:**
- Consumes: requirement IDs in `PROJECT_REQUIREMENTS.toml`
- Produces: repository-boundary findings across project policies, Roles, and Skills

- [ ] **Step 1: Add failing role-scan test**

```python
def test_constraint_lint_scans_roles(tmp_path):
    path = tmp_path / ".agents/roles/EXAMPLE.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "Every worker count must be exactly 16.\n",
        encoding="utf-8",
    )
    findings = lint_repository(tmp_path)
    assert any(item.path.endswith("EXAMPLE.md") for item in findings)
```

- [ ] **Step 2: Add failing skill-scan test**

```python
def test_constraint_lint_scans_skills(tmp_path):
    path = tmp_path / ".agents/skills/example/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "All internal handoffs require SHA-256.\n",
        encoding="utf-8",
    )
    findings = lint_repository(tmp_path)
    assert any(item.kind == "HASH_HANDOFF" for item in findings)
```

- [ ] **Step 3: Add requirement-scope test**

A paragraph containing `UR-EXEC-001` must not automatically legalize an unrelated fixed retry rule.

```python
def test_unrelated_requirement_id_does_not_authorize_constraint():
    findings = lint_text(
        "UR-EXEC-001 applies. Every recovery has exactly one attempt.",
        path=".agents/roles/EXAMPLE.md",
    )
    assert any(item.kind == "ONE_ATTEMPT" for item in findings)
```

- [ ] **Step 4: Implement scan roots**

Include:

```python
root / "AGENTS.md"
root / "docs/project"
root / ".agents/roles"
root / ".agents/skills"
```

Exclude generated requirement views and historical archives only by exact path list.

- [ ] **Step 5: Implement constraint-to-requirement compatibility**

Use a narrow mapping:

```python
COMPATIBLE_REQUIREMENTS = {
    "DIRECTION_CAP": {"NR-DIRECTION-CAP-001"},
    "WORKER_LIMIT": {"NR-WORKER-LIMIT-001", "UR-RESOURCE-001"},
    "HASH_HANDOFF": {"NR-HASH-HANDOFF-001"},
    "ONE_ATTEMPT": set(),
    "WALL_CLOCK_STOP": {"UR-PERF-001"},
    "FIXED_REVIEW_CHAIN": set(),
}
```

A requirement token suppresses a finding only when compatible with the finding kind and the paragraph is explicitly negating or constraining the prohibited rule.

- [ ] **Step 6: Reconcile the CM Role**

Replace any abstract component name not present in `PROJECT_MAP` or `EXECUTION_BACKEND_REGISTRY` with:

```text
the exact native boundary named by the assignment and EXECUTION_BACKEND_REGISTRY
```

Do not weaken:

```text
result-bearing registered equivalent route uses C++
parallel execution is required
no silent Python/serial fallback
```

Remove only unregistered global ceremony.

- [ ] **Step 7: Run tests and repository lint**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/hmasd_control_plane/test_constraint_lint.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_constraint_lint

powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-constraint-lint.ps1
```

- [ ] **Step 8: Commit**

```powershell
git add tools/hmasd_control_plane/constraint_lint.py tests/hmasd_control_plane/test_constraint_lint.py .agents/roles/CODE_PROJECT_MANAGER.md
git commit -m "fix: lint constraints across roles and skills"
```

---

## Task 8: Add Read-Only Context Foundation Queries to hmasd_observability

**Files:**
- Create: `tools/codex_context_lifecycle/context_query.py`
- Modify: `tools/hmasd_control_plane/mcp_server.py`
- Modify: `.codex/config.toml`
- Modify: `tests/hmasd_control_plane/test_mcp_server.py`
- Create: `tests/codex_context_lifecycle/test_context_query.py`

**Interfaces:**
- Produces:
  - `context_foundation_health(root: Path) -> dict[str, object]`
  - `decision_list(root: Path, status: str | None) -> list[dict[str, object]]`
  - `decision_get(root: Path, decision_id: str) -> dict[str, object]`
  - `project_map_validate(root: Path) -> dict[str, object]`
  - `project_map_resolve_anchor(root: Path, anchor: str) -> dict[str, object]`
  - `current_work_index(root: Path) -> list[dict[str, object]]`
  - `context_sources_for_actor(root: Path, actor: str, requested_ids: tuple[str, ...])`

- [ ] **Step 1: Add failing pure-query tests**

```python
def test_decision_get_returns_repository_path(repo_root):
    payload = decision_get(repo_root, "ADR-0001")
    assert payload["decision_id"] == "ADR-0001"
    assert payload["path"].startswith("docs/project/decisions/")

def test_project_map_resolve_anchor_is_exact(repo_root):
    payload = project_map_resolve_anchor(
        repo_root,
        "Codex App Server runtime plane",
    )
    assert payload["found"] is True
    assert payload["heading"] == "Codex App Server runtime plane"
```

- [ ] **Step 2: Implement bounded read-only queries**

No query writes a file, index, SQLite row, or runtime receipt.

`project_map_resolve_anchor()` returns:

```python
{
    "found": True,
    "heading": "Codex App Server runtime plane",
    "line": 123,
    "section_text": "...bounded to 8192 UTF-8 bytes...",
}
```

- [ ] **Step 3: Add MCP tools**

Add to `OBSERVABILITY_TOOL_ALLOWLIST`:

```text
context_foundation_health
context_sources_for_actor
decision_list
decision_get
project_map_validate
project_map_resolve_anchor
current_work_index
```

Each tool uses `_get_repo_root()` and returns bounded JSON.

- [ ] **Step 4: Add config allowlist entries**

Add the same seven tool names under:

```toml
[mcp_servers.hmasd_observability]
```

Do not add them to `hmasd_orchestrator`.

- [ ] **Step 5: Add mutation-negative test**

```python
def test_context_query_mcp_has_no_mutating_tool():
    server = build_server(repo_root)
    names = set(tool_names(server))
    assert "decision_write" not in names
    assert "project_map_write" not in names
    assert "current_work_write" not in names
```

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_context_query.py `
  tests/hmasd_control_plane/test_mcp_server.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_context_queries
```

- [ ] **Step 7: Commit**

```powershell
git add tools/codex_context_lifecycle/context_query.py tools/hmasd_control_plane/mcp_server.py .codex/config.toml tests/codex_context_lifecycle/test_context_query.py tests/hmasd_control_plane/test_mcp_server.py
git commit -m "feat: expose read-only context foundation queries"
```

---

## Task 9: Produce a Current-Head Context Foundation Doctor Report

**Files:**
- Modify: `tools/codex_context_lifecycle/doctor.py`
- Modify: `tests/codex_context_lifecycle/test_doctor.py`
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/CONTEXT_FOUNDATION_DOCTOR.json`
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/CONTEXT_FOUNDATION_REVIEW.md`

**Interfaces:**
- Doctor adds:
  - `current_work_valid`
  - `required_adr_ids_present`
  - `current_control_plane_sources_present`
  - `behavioral_hooks_disabled`

- [ ] **Step 1: Write failing doctor assertions**

```python
def test_doctor_reports_complete_context_foundation(repo_root):
    payload = collect_doctor(repo_root)
    assert payload["current_work_valid"] is True
    assert payload["required_adr_ids_present"] is True
    assert payload["current_control_plane_sources_present"] is True
    assert payload["behavioral_hooks_disabled"] is True
```

- [ ] **Step 2: Implement doctor keys**

`behavioral_hooks_disabled` is true only when:

```text
features.hooks=false
and no active hook tables are present in .codex/config.toml
```

- [ ] **Step 3: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle/test_doctor.py `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_context_doctor
```

- [ ] **Step 4: Generate the current-head report**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m tools.codex_context_lifecycle.cli `
  doctor `
  --repo-root C:/Projects/HMASD-context-foundation-closure |
  Set-Content `
  -Encoding UTF8 `
  docs/research/workflow-runs/2026-08-22_context-foundation-closure/CONTEXT_FOUNDATION_DOCTOR.json
```

- [ ] **Step 5: Write the review**

The review states:

```text
validated_commit
doctor result
ADR coverage
PROJECT_MAP coverage
registry coverage
CURRENT_WORK coverage
MCP read-only query inventory
open non-High limitations
```

It does not claim App Server live acceptance.

- [ ] **Step 6: Commit**

```powershell
git add tools/codex_context_lifecycle/doctor.py tests/codex_context_lifecycle/test_doctor.py docs/research/workflow-runs/2026-08-22_context-foundation-closure
git commit -m "docs: record current context foundation health"
```

---

## Task 10: Replace the Runtime Calibration Placeholder with Measured Evidence

**Files:**
- Modify: `docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/RUNTIME_BASELINE.md`
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/`
- Modify only if evidence requires: `docs/project/EXPERIMENT_EXECUTION_POLICY.md`

**Interfaces:**
- Consumes: existing resource preflight and runtime plausibility tools
- Produces: four measured, non-formal runtime samples

- [ ] **Step 1: Capture a current resource preflight**

Use the existing wrapper and a CM-selected width based on the actual host:

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-resource-preflight.ps1 `
  -AssignmentId asg_context_runtime_calibration `
  -RouteId continuous_roster_native `
  -Backend cpp `
  -SelectedWorkerCount 2 `
  -SelectionRationale "Two-worker bounded calibration only; not a project default." `
  -CmOwner "CM:shared:context-foundation" `
  -OutPath docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/RESOURCE_PREFLIGHT.json
```

If current CPU/memory evidence supports a different width, change only `SelectedWorkerCount` and record the actual rationale. Do not infer a global default.

- [ ] **Step 2: Measure a simple toy environment route**

Requirements:

```text
warmup 100 steps
sample at least 500 steps or 5 seconds
record environment steps, wall time, backend, workers, threads
```

Write:

```text
runtime/TOY_ENV_SAMPLE.json
```

- [ ] **Step 3: Measure one learner/update route**

Record separately:

```text
environment steps
optimizer updates
evaluations
wall time
```

Write:

```text
runtime/LEARNER_UPDATE_SAMPLE.json
```

- [ ] **Step 4: Measure one registered C++ parallel route**

Use:

```text
continuous_roster_native
```

Write:

```text
runtime/CPP_PARALLEL_SAMPLE.json
```

- [ ] **Step 5: Measure the Python reference route as non-result-bearing**

Write:

```text
runtime/PYTHON_REFERENCE_SAMPLE.json
```

Mark:

```text
result_bearing=false
runtime_profile=REFERENCE_ORACLE
```

- [ ] **Step 6: Run plausibility assessment**

```powershell
Get-ChildItem `
  docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime/*_SAMPLE.json |
ForEach-Object {
  powershell.exe -NoProfile -NonInteractive -File `
    scripts/hmasd-runtime-plausibility.ps1 `
    -Path $_.FullName
}
```

- [ ] **Step 7: Update the baseline document**

Replace the placeholder language with measured tables. Do not change thresholds unless the measured samples demonstrate a concrete false classification. A threshold change requires:

```text
old threshold
new threshold
sample reference
reason
```

- [ ] **Step 8: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/RUNTIME_BASELINE.md docs/research/workflow-runs/2026-08-22_context-foundation-closure/runtime docs/project/EXPERIMENT_EXECUTION_POLICY.md
git commit -m "docs: calibrate runtime policy with measured evidence"
```

---

## Task 11: Run a Real Long-Task Assignment and Intake Pilot

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/assignments/ASSIGNMENT_context_foundation_review.md`
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/results/RESULT_context_foundation_review.md`
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/LONG_TASK_PILOT.md`

**Interfaces:**
- Consumes: file-backed assignment/result protocol
- Produces: one actual child result and owner intake without Hook mediation

- [ ] **Step 1: Write the assignment with exact scope**

Use:

```toml
assignment_id = "asg_context_foundation_review"
assignment_mode = "REVIEW"
semantic_owner = "OPERATIONAL_ROOT"
executor_role = "hmasd-reviewer"
return_to = "OPERATIONAL_ROOT"
strictness_profile = "R4_CONTROL_PLANE_AND_AUTHORITY"
evidence_class = "B"
result_bearing = false
requirement_ids = ["UR-RECOVERY-001"]
nonrequirement_ids = [
  "NR-HIGH_FREQUENCY_HOOKS-001",
  "NR-COMPACTION-HOOKS-001",
  "NR-HASH-HANDOFF-001"
]
recovery_owner = "OPERATIONAL_ROOT"
result_path = "docs/research/workflow-runs/2026-08-22_context-foundation-closure/results/RESULT_context_foundation_review.md"
project_map_anchor = "Repository context lifecycle"
architecture_role = "CONTROL_PLANE"
affected_files = []
create_files = []
affected_symbols = []
search_roots = [
  "tools/codex_context_lifecycle",
  "tools/hmasd_control_plane",
  "docs/project"
]
direct_consumers = [
  ".agents/roles/ROOT.md",
  ".agents/roles/CODE_PROJECT_MANAGER.md"
]
upstream_inputs = [
  "AGENTS.md",
  "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
]
state_owner = "operational_root"
non_target_surfaces = [
  "scientific direction state",
  "technical acceptance",
  "Portfolio allocation",
  "App Server live runtime"
]
```

Outcome:

```text
Operational Root receives one evidence-backed review of whether Stage 1 artifacts form a coherent repository-owned context foundation, with no runtime or semantic disposition.
```

- [ ] **Step 2: Validate the assignment**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-validate-assignment.ps1 `
  -Path docs/research/workflow-runs/2026-08-22_context-foundation-closure/assignments/ASSIGNMENT_context_foundation_review.md
```

- [ ] **Step 3: Dispatch one real reviewer child**

The dispatch message contains only:

```text
Read and execute:
docs/research/workflow-runs/2026-08-22_context-foundation-closure/assignments/ASSIGNMENT_context_foundation_review.md

Write the declared result artifact.
Return the result path and conclusion to Operational Root.
```

Do not inject this full implementation plan.

- [ ] **Step 4: Collect the native child return**

Use native `wait_agent`. Do not use a Stop Hook or SubagentStop repair.

- [ ] **Step 5: Validate the result**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-validate-result.ps1 `
  -Path docs/research/workflow-runs/2026-08-22_context-foundation-closure/results/RESULT_context_foundation_review.md `
  -AssignmentPath docs/research/workflow-runs/2026-08-22_context-foundation-closure/assignments/ASSIGNMENT_context_foundation_review.md
```

- [ ] **Step 6: Record owner intake**

`LONG_TASK_PILOT.md` separates:

```text
observed facts
scope-local review conclusions
remaining authorized work
Operational Root decision
```

No child phrase is copied as a workflow or global status.

- [ ] **Step 7: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_context-foundation-closure/assignments docs/research/workflow-runs/2026-08-22_context-foundation-closure/results docs/research/workflow-runs/2026-08-22_context-foundation-closure/LONG_TASK_PILOT.md
git commit -m "docs: record long-task context foundation pilot"
```

---

## Task 12: Stage 1 Acceptance and Merge

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_ACCEPTANCE.md`
- Update: `docs/project/current-work/common/control_plane_runtime.md`

- [ ] **Step 1: Run the Stage 1 suite**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle `
  tests/hmasd_control_plane `
  tests/codex_semantic_mvp `
  -q `
  --basetemp=C:/Projects/HMASD-context-foundation-closure/.tmp_stage1_final
```

- [ ] **Step 2: Run boundary tools**

```powershell
powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-requirements.ps1 validate
powershell.exe -NoProfile -NonInteractive -File scripts/hmasd-constraint-lint.ps1
powershell.exe -NoProfile -NonInteractive -File scripts/codex-context-lifecycle-doctor.ps1 `
  -RepoRoot C:/Projects/HMASD-context-foundation-closure `
  -PythonExecutable C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
```

- [ ] **Step 3: Request focused independent review**

Review only:

```text
ADR validity and coverage
PROJECT_MAP and registry coverage
CURRENT_WORK pointer integrity
minimal recovery outcome semantics
Role/Skill constraint lint
read-only MCP surface
long-task pilot intake
```

Critical/High must be zero.

- [ ] **Step 4: Write acceptance**

Record:

```text
exact accepted commit
test commands/results
doctor result
constraint lint result
measured runtime evidence refs
long-task pilot refs
behavioral_hooks=false
native_auto_compaction=unchanged
app_server_live_acceptance=not_attempted
```

- [ ] **Step 5: Commit acceptance**

```powershell
git add docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_ACCEPTANCE.md docs/project/current-work/common/control_plane_runtime.md
git commit -m "docs: accept context foundation closure"
```

- [ ] **Step 6: Merge through Operational Root**

```powershell
Set-Location C:\Projects\HMASD
git checkout aggressive
git pull --ff-only origin aggressive
git merge --no-ff codex-context-foundation-closure-v1 `
  -m "merge: close HMASD context foundation"
```

Run the Stage 1 suite again on the merged tree. Push only after green.

---

# Stage 2 — Explicit App Server Runtime Control

## Stage 2 Result

Stage 2 is independently reviewable and starts from the accepted Stage 1 merge. At completion:

```text
Supervisor runtime is external.
PROCESS_STARTED and READY are different facts.
READY proves initialize, watcher start, and first reconciliation.
Process identity protects against PID reuse.
A typed local command channel controls the single long-lived host.
Observer profile is live-accepted.
One ephemeral canary is live-accepted.
Operational Root and Portfolio are manually managed.
Typed mailbox references can be manually delivered.
One explicitly armed single wake is accepted.
No scheduler serve, turn/steer, automatic approval, provider send, or managed EM/CM exists.
```

---

## Task 13: Create the Stage 2 Worktree and Freeze the Accepted Stage 1 Baseline

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/STAGE2_BASELINE.md`

- [ ] **Step 1: Fetch the accepted Stage 1 merge**

```powershell
Set-Location C:\Projects\HMASD
git fetch origin
git worktree add `
  C:\Projects\HMASD-app-server-live-runtime `
  -b codex-app-server-live-runtime-v1 `
  origin/aggressive
Set-Location C:\Projects\HMASD-app-server-live-runtime
```

- [ ] **Step 2: Record the exact baseline**

```powershell
git status --short
git rev-parse HEAD
git log -10 --oneline
```

- [ ] **Step 3: Verify Stage 1 acceptance exists and matches the baseline ancestry**

```powershell
Test-Path docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_ACCEPTANCE.md
git log --oneline --all -- docs/research/workflow-runs/2026-08-22_context-foundation-closure/STAGE1_ACCEPTANCE.md
```

- [ ] **Step 4: Run the existing supervisor baseline**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_stage2_baseline
```

- [ ] **Step 5: Commit the Stage 2 baseline record**

```powershell
git add docs/research/workflow-runs/2026-08-22_app-server-live-runtime/STAGE2_BASELINE.md
git commit -m "docs: freeze App Server live runtime baseline"
```

---

## Task 14: Define Explicit Runtime Profiles

**Files:**
- Create: `docs/project/CODEX_SUPERVISOR_LIVE_PROFILES.md`
- Create: `tools/codex_supervisor/runtime_profiles.py`
- Test: `tests/codex_supervisor/test_runtime_profiles.py`

**Interfaces:**
- Produces:
  - `RuntimeProfile`
  - `CommandKind`
  - `require_command_allowed(profile, command)`

Profiles:

```python
class RuntimeProfile(str, Enum):
    OBSERVER = "OBSERVER"
    MANAGED_MANUAL = "MANAGED_MANUAL"
    MAILBOX_MANUAL = "MAILBOX_MANUAL"
    SINGLE_WAKE = "SINGLE_WAKE"
```

Commands:

```python
class CommandKind(str, Enum):
    STATUS = "STATUS"
    STOP = "STOP"
    INSPECT = "INSPECT"
    MANAGED_CREATE = "MANAGED_CREATE"
    MANAGED_ADOPT = "MANAGED_ADOPT"
    MANAGED_VERIFY = "MANAGED_VERIFY"
    MANAGED_TURN = "MANAGED_TURN"
    MANAGED_SUSPEND = "MANAGED_SUSPEND"
    MANAGED_REVOKE = "MANAGED_REVOKE"
    MAILBOX_ENQUEUE = "MAILBOX_ENQUEUE"
    MAILBOX_LIST = "MAILBOX_LIST"
    MAILBOX_DELIVER_ONCE = "MAILBOX_DELIVER_ONCE"
    ARM_SINGLE_WAKE = "ARM_SINGLE_WAKE"
```

- [ ] **Step 1: Add profile matrix tests**

```python
def test_observer_profile_is_read_only():
    assert allowed(RuntimeProfile.OBSERVER, CommandKind.STATUS)
    assert allowed(RuntimeProfile.OBSERVER, CommandKind.INSPECT)
    assert not allowed(RuntimeProfile.OBSERVER, CommandKind.MANAGED_TURN)

def test_single_wake_profile_forbids_scheduler_serve():
    assert allowed(RuntimeProfile.SINGLE_WAKE, CommandKind.ARM_SINGLE_WAKE)
    assert "SCHEDULER_SERVE" not in {item.value for item in CommandKind}
```

- [ ] **Step 2: Implement exact matrix**

```python
ALLOWED_COMMANDS = {
    RuntimeProfile.OBSERVER: {
        CommandKind.STATUS,
        CommandKind.STOP,
        CommandKind.INSPECT,
    },
    RuntimeProfile.MANAGED_MANUAL: {
        CommandKind.STATUS,
        CommandKind.STOP,
        CommandKind.INSPECT,
        CommandKind.MANAGED_CREATE,
        CommandKind.MANAGED_ADOPT,
        CommandKind.MANAGED_VERIFY,
        CommandKind.MANAGED_TURN,
        CommandKind.MANAGED_SUSPEND,
        CommandKind.MANAGED_REVOKE,
    },
    RuntimeProfile.MAILBOX_MANUAL: {
        CommandKind.STATUS,
        CommandKind.STOP,
        CommandKind.INSPECT,
        CommandKind.MANAGED_SUSPEND,
        CommandKind.MANAGED_REVOKE,
        CommandKind.MAILBOX_ENQUEUE,
        CommandKind.MAILBOX_LIST,
        CommandKind.MAILBOX_DELIVER_ONCE,
    },
    RuntimeProfile.SINGLE_WAKE: {
        CommandKind.STATUS,
        CommandKind.STOP,
        CommandKind.INSPECT,
        CommandKind.MAILBOX_ENQUEUE,
        CommandKind.MAILBOX_LIST,
        CommandKind.ARM_SINGLE_WAKE,
    },
}
```

A host profile is immutable for one host process. Changing profile requires an explicit stop/start.

- [ ] **Step 3: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_runtime_profiles.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_profiles
```

- [ ] **Step 4: Commit**

```powershell
git add docs/project/CODEX_SUPERVISOR_LIVE_PROFILES.md tools/codex_supervisor/runtime_profiles.py tests/codex_supervisor/test_runtime_profiles.py
git commit -m "feat: define explicit supervisor runtime profiles"
```

---

## Task 15: Add External Host Identity and Truthful Readiness Records

**Files:**
- Create: `tools/codex_supervisor/host_state.py`
- Test: `tests/codex_supervisor/test_host_state.py`

**Interfaces:**
- Produces:
  - `SupervisorProcessRecord`
  - `SupervisorReadyRecord`
  - `atomic_write_json(path, payload)`
  - `load_process_record(path)`
  - `load_ready_record(path)`
  - `validate_ready_record(process, ready)`

```python
@dataclass(frozen=True)
class SupervisorProcessRecord:
    schema: str
    pid: int
    process_start_time_utc: str
    executable: str
    repo_root: str
    runtime_home: str
    profile: str
    started_at: str
    ready_file: str

@dataclass(frozen=True)
class SupervisorReadyRecord:
    schema: str
    run_id: str
    process_id: int
    initialized_at: str
    watcher_active: bool
    first_reconciliation_completed: bool
    thread_count: int
    runtime_home: str
    profile: str
```

- [ ] **Step 1: Add failing readiness tests**

```python
def test_alive_process_record_without_ready_record_is_not_ready(tmp_path):
    process = process_record(pid=123)
    assert validate_ready_record(process, None) == (
        "ready record is missing",
    )

def test_ready_record_requires_watcher_and_reconciliation():
    process = process_record(pid=123)
    ready = ready_record(
        process_id=123,
        watcher_active=False,
        first_reconciliation_completed=False,
    )
    errors = validate_ready_record(process, ready)
    assert "server-request watcher is not active" in errors
    assert "first reconciliation is incomplete" in errors
```

- [ ] **Step 2: Implement atomic JSON writes**

Use:

```python
with tempfile.NamedTemporaryFile(
    "w",
    encoding="utf-8",
    dir=path.parent,
    delete=False,
) as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
    handle.flush()
    os.fsync(handle.fileno())
Path(handle.name).replace(path)
```

- [ ] **Step 3: Validate identity fields**

`validate_ready_record()` checks:

```text
process ID match
runtime home match
profile match
watcher active
first reconciliation completed
run_id nonempty
```

It does not inspect semantic state.

- [ ] **Step 4: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_host_state.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_host_state
```

- [ ] **Step 5: Commit**

```powershell
git add tools/codex_supervisor/host_state.py tests/codex_supervisor/test_host_state.py
git commit -m "feat: add truthful supervisor host records"
```

---

## Task 16: Emit READY Only After Initialize, Watcher Start, and First Reconciliation

**Files:**
- Modify: `tools/codex_supervisor/observer.py`
- Modify: `tools/codex_supervisor/cli.py`
- Test: `tests/codex_supervisor/test_observer_ready.py`

**Interfaces:**
- `ObserverService.serve(duration_seconds=None, ready_hook=None)`
- CLI:
  - `serve --ready-file PATH --profile PROFILE`

- [ ] **Step 1: Add failing ready-order test**

```python
@pytest.mark.asyncio
async def test_ready_hook_runs_after_initialize_watcher_and_reconciliation(
    fake_service,
):
    observed = []

    async def ready_hook(payload):
        observed.append(payload)

    await fake_service.serve(
        duration_seconds=0.05,
        ready_hook=ready_hook,
    )

    assert len(observed) == 1
    assert observed[0]["watcher_active"] is True
    assert observed[0]["first_reconciliation_completed"] is True
    assert observed[0]["run_id"]
```

- [ ] **Step 2: Add no-ready-on-failure test**

If initialize or first reconciliation raises, the ready hook is never called.

- [ ] **Step 3: Add ready hook to serve**

Sequence must be:

```python
await self.start()
await self.initialize()
watcher = asyncio.create_task(self._watch_server_requests())
await asyncio.sleep(0)
reconciliation = await self.reconcile_threads()
await ready_hook({
    "run_id": self.run_id,
    "process_id": self.transport.process_id,
    "initialized_at": _now(),
    "watcher_active": not watcher.done(),
    "first_reconciliation_completed": True,
    "thread_count": reconciliation["thread_count"],
})
```

- [ ] **Step 4: Add CLI ready-file support**

The CLI creates an async ready hook that writes `SupervisorReadyRecord` atomically.

Reject a ready file under the repository.

- [ ] **Step 5: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_observer_ready.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_observer_ready
```

- [ ] **Step 6: Commit**

```powershell
git add tools/codex_supervisor/observer.py tools/codex_supervisor/cli.py tests/codex_supervisor/test_observer_ready.py
git commit -m "feat: make supervisor readiness evidence-based"
```

---

## Task 17: Rewrite Start, Status, and Stop Wrappers

**Files:**
- Modify: `scripts/hmasd-root-supervisor-start.ps1`
- Modify: `scripts/hmasd-root-supervisor-status.ps1`
- Modify: `scripts/hmasd-root-supervisor-stop.ps1`
- Create: `tests/codex_supervisor/test_root_supervisor_scripts.py`

**Interfaces:**
- External default:
  - `%LOCALAPPDATA%\HMASD\codex-supervisor`
- Start output:
  - `HMASD_SUPERVISOR_READY_V2`
  - or `HMASD_SUPERVISOR_INCIDENT_V2`
- Status schema:
  - `HMASD_SUPERVISOR_STATUS_V2`

- [ ] **Step 1: Add script-content tests**

```python
def test_start_script_uses_external_default(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "LOCALAPPDATA" in text
    assert "runtime/hmasd-root-supervisor" not in text

def test_start_script_does_not_treat_pid_as_ready(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "ready.json" in text
    assert "Start-Sleep -Milliseconds 300" not in text
```

- [ ] **Step 2: Use external default**

```powershell
if (-not $RuntimeHome) {
    if (-not $env:LOCALAPPDATA) {
        throw 'LOCALAPPDATA is required'
    }
    $RuntimeHome = Join-Path $env:LOCALAPPDATA 'HMASD\codex-supervisor'
}
```

Resolve paths and reject a runtime home under `$RepoRoot`.

- [ ] **Step 3: Record exact process identity**

Store:

```text
PID
Process.StartTime.ToUniversalTime()
Process.Path
repo root
runtime home
profile
ready file
full argument vector
```

- [ ] **Step 4: Wait for readiness**

The start wrapper:

```text
writes PROCESS_STARTED receipt internally
waits up to 20 seconds for ready.json
checks process identity every 200ms
returns READY only when ready.json validates
returns INCIDENT if process exits or deadline expires
```

- [ ] **Step 5: Make status truthful**

Status values:

```text
STOPPED
PROCESS_STARTING
READY
STALE_IDENTITY
INCIDENT
```

`READY` requires:

```text
exact process identity
valid ready.json
doctor binary/schema/static guards
active observer run with matching run_id
```

- [ ] **Step 6: Make stop identity-safe**

Stop refuses to terminate when current process start time or executable differs from the stored record. It writes an incident response and leaves the process untouched.

- [ ] **Step 7: Run tests under Python and PowerShell 5.1**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_root_supervisor_scripts.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_supervisor_scripts

powershell.exe -NoProfile -NonInteractive -Command `
  "[void][scriptblock]::Create((Get-Content -Raw scripts/hmasd-root-supervisor-start.ps1)); `
   [void][scriptblock]::Create((Get-Content -Raw scripts/hmasd-root-supervisor-status.ps1)); `
   [void][scriptblock]::Create((Get-Content -Raw scripts/hmasd-root-supervisor-stop.ps1))"
```

- [ ] **Step 8: Commit**

```powershell
git add scripts/hmasd-root-supervisor-start.ps1 scripts/hmasd-root-supervisor-status.ps1 scripts/hmasd-root-supervisor-stop.ps1 tests/codex_supervisor/test_root_supervisor_scripts.py
git commit -m "fix: make supervisor lifecycle truthful and external"
```

---

## Task 18: Add a Typed Local Command Channel to the Long-Lived Host

**Files:**
- Create: `tools/codex_supervisor/host_control.py`
- Modify: `tools/codex_supervisor/observer.py`
- Modify: `tools/codex_supervisor/cli.py`
- Test: `tests/codex_supervisor/test_host_control.py`

**Interfaces:**
- External runtime directories:

```text
control/inbox/
control/processing/
control/outbox/
control/rejected/
```

- Request schema:

```python
@dataclass(frozen=True)
class HostControlRequest:
    schema: str
    request_id: str
    created_at: str
    operator: str
    command: CommandKind
    arguments: dict[str, object]
```

- Response schema:

```python
@dataclass(frozen=True)
class HostControlResponse:
    schema: str
    request_id: str
    status: str
    payload: dict[str, object]
    error: str | None
    completed_at: str
```

- [ ] **Step 1: Add duplicate-request test**

```python
def test_duplicate_request_returns_existing_response(tmp_path):
    channel = HostControlChannel(tmp_path)
    request = request_status("req-1")
    channel.submit(request)
    channel.write_response(response_ok("req-1"))
    assert channel.submit(request).request_id == "req-1"
    assert channel.response("req-1").status == "OK"
```

- [ ] **Step 2: Add profile-rejection test**

```python
def test_observer_profile_rejects_managed_turn(tmp_path):
    request = HostControlRequest(
        schema="HMASD_SUPERVISOR_CONTROL_REQUEST_V1",
        request_id="req-managed",
        created_at=now(),
        operator="operator:test",
        command=CommandKind.MANAGED_TURN,
        arguments={"binding_id": "binding-x", "text": "test"},
    )
    with pytest.raises(ProfileError):
        require_command_allowed(RuntimeProfile.OBSERVER, request.command)
```

- [ ] **Step 3: Implement atomic claim**

Host claims:

```text
inbox/request.json
→ atomic rename to processing/request.json
```

Only one host can claim. A stale or malformed request moves to `rejected`.

- [ ] **Step 4: Implement allowlisted dispatch**

The host loop calls existing components only:

```text
BindingStore
ManagedProvisioner
ManagedTurns
MailboxStore
WakeScheduler
WakeRecovery
SemanticBridge
timeline functions
```

No arbitrary App Server method is accepted from the request.

- [ ] **Step 5: Add the command loop to ObserverService**

After readiness, run:

```python
command_task = asyncio.create_task(
    control.serve(
        profile=profile,
        service=self,
        stop_event=host_stop_event,
    )
)
```

The App Server client and `AppServerSessionOwner` remain process-lifetime objects owned by this host.

- [ ] **Step 6: Add CLI arguments**

```text
serve --profile PROFILE --ready-file PATH --control-home PATH
```

- [ ] **Step 7: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_host_control.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_host_control
```

- [ ] **Step 8: Commit**

```powershell
git add tools/codex_supervisor/host_control.py tools/codex_supervisor/observer.py tools/codex_supervisor/cli.py tests/codex_supervisor/test_host_control.py
git commit -m "feat: add typed control channel to supervisor host"
```

---

## Task 19: Route Existing Managed and Mailbox Scripts Through the Host

**Files:**
- Create: `scripts/hmasd-supervisor-request.ps1`
- Modify:
  - `scripts/codex-managed-actor-create.ps1`
  - `scripts/codex-managed-actor-adopt.ps1`
  - `scripts/codex-managed-actor-turn.ps1`
  - `scripts/codex-managed-actor-suspend.ps1`
  - `scripts/codex-mailbox-list.ps1`
  - `scripts/codex-mailbox-once.ps1`
  - `scripts/codex-mailbox-send-canary.ps1`
- Test: `tests/codex_supervisor/test_host_request_scripts.py`

**Interfaces:**
- Wrapper writes one request JSON and waits for one outbox response.
- Default timeout:
  - read-only: 30 seconds
  - managed turn: 1800 seconds
  - mailbox delivery: 1800 seconds

- [ ] **Step 1: Implement generic request wrapper**

Parameters:

```powershell
-Command
-ArgumentsJson
-Operator
-RuntimeHome
-TimeoutSeconds
```

It generates one UUID request ID, writes UTF-8 JSON atomically, waits for matching response, and never retries a mutating request under a new ID.

- [ ] **Step 2: Update managed scripts**

They no longer invoke a fresh `python -m tools.codex_supervisor managed ...` process for commands requiring a live session. They submit typed host commands.

- [ ] **Step 3: Update mailbox scripts**

`codex-mailbox-once.ps1` submits:

```text
MAILBOX_DELIVER_ONCE
```

It never starts scheduler serve.

- [ ] **Step 4: Add no-host test**

Without a valid ready host, wrappers return:

```text
HMASD_SUPERVISOR_HOST_REQUIRED_V1
```

and do not write a mutating request.

- [ ] **Step 5: Add no-retry test**

If a response is `SUBMISSION_UNCERTAIN`, the wrapper returns it unchanged and does not generate another request.

- [ ] **Step 6: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_host_request_scripts.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_request_scripts
```

- [ ] **Step 7: Commit**

```powershell
git add scripts/hmasd-supervisor-request.ps1 scripts/codex-managed-actor-*.ps1 scripts/codex-mailbox-*.ps1 tests/codex_supervisor/test_host_request_scripts.py
git commit -m "feat: route live supervisor commands through one host"
```

---

## Task 20: Live-Accept the Observer Profile

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/PHASE1_LIVE_OBSERVER_ACCEPTANCE.md`
- Create: `scripts/hmasd-supervisor-observer-live-test.ps1`

- [ ] **Step 1: Start OBSERVER**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-root-supervisor-start.ps1 `
  -RepoRoot C:/Projects/HMASD-app-server-live-runtime `
  -Profile OBSERVER
```

Expected: `HMASD_SUPERVISOR_READY_V2`.

- [ ] **Step 2: Query status twice**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-root-supervisor-status.ps1 `
  -RepoRoot C:/Projects/HMASD-app-server-live-runtime
Start-Sleep -Seconds 3
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-root-supervisor-status.ps1 `
  -RepoRoot C:/Projects/HMASD-app-server-live-runtime
```

Verify:

```text
same process identity
same run_id
READY
first reconciliation complete
watcher active
automatic wake false
active binding count zero
```

- [ ] **Step 3: Inspect timeline**

Use the read-only `INSPECT` host command. Confirm thread snapshots and reconciliations exist without a model turn.

- [ ] **Step 4: Stop**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-root-supervisor-stop.ps1 `
  -RepoRoot C:/Projects/HMASD-app-server-live-runtime
```

- [ ] **Step 5: Record acceptance**

The document includes:

```text
runtime home
Codex version
run_id
process identity
initialize evidence
watcher evidence
first reconciliation evidence
stop evidence
model turns started=0
canonical files written by supervisor=0
```

- [ ] **Step 6: Commit**

```powershell
git add scripts/hmasd-supervisor-observer-live-test.ps1 docs/research/workflow-runs/2026-08-22_app-server-live-runtime/PHASE1_LIVE_OBSERVER_ACCEPTANCE.md
git commit -m "docs: accept live App Server observer profile"
```

---

## Task 21: Run the Explicit Ephemeral App Server Canary

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/EPHEMERAL_CANARY_ACCEPTANCE.md`

- [ ] **Step 1: Ensure no live host owns the runtime**

Status must be `STOPPED`.

- [ ] **Step 2: Run the existing canary**

Use a separate external runtime subdirectory:

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/codex-app-server-observer-canary.ps1 `
  -RepoRoot C:/Projects/HMASD-app-server-live-runtime `
  -PythonExecutable C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  -NormalRuntimeHome "$env:LOCALAPPDATA\HMASD\codex-supervisor" `
  -RuntimeHome "$env:LOCALAPPDATA\HMASD\codex-supervisor-canary"
```

- [ ] **Step 3: Verify exact canary invariants**

```text
one thread/start
one turn/start
ephemeral thread
approvalPolicy=never
exact response HMASD_APP_SERVER_OBSERVER_OK
no tools
natural turn completion
no unexpected server request
no retry
scratch directory removed
```

- [ ] **Step 4: Record usage-bearing evidence separately**

This canary consumes one model turn. It is not repeated on every start and is not part of normal workflow.

- [ ] **Step 5: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_app-server-live-runtime/EPHEMERAL_CANARY_ACCEPTANCE.md
git commit -m "docs: accept explicit ephemeral App Server canary"
```

---

## Task 22: Live-Accept Manual Operational Root Management

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/MANAGED_ROOT_MANUAL_ACCEPTANCE.md`

- [ ] **Step 1: Start `MANAGED_MANUAL`**

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/hmasd-root-supervisor-start.ps1 `
  -RepoRoot C:/Projects/HMASD-app-server-live-runtime `
  -Profile MANAGED_MANUAL
```

- [ ] **Step 2: Obtain the exact Operational Root actor context**

Use `hmasd_orchestrator.actor_context_current` for the known Operational Root session. Do not infer from prose.

- [ ] **Step 3: Create a fresh managed binding**

Submit `MANAGED_CREATE` with:

```text
actor_context_id
semantic_state path
operator identity
confirm_global_memory_disabled=true
```

Verify:

```text
actor kind OPERATIONAL_ROOT
threadId → binding → actor exact
history trust FRESH
Memory-off evidence
binding verification
```

- [ ] **Step 4: Send one manual managed turn**

Text:

```text
Read the current Root Role and reply exactly:
HMASD_MANAGED_ROOT_MANUAL_OK
Do not use tools and do not modify files.
```

Verify one `turn/start` and natural completion.

- [ ] **Step 5: Restart and reconcile**

Stop the host after completion, restart `MANAGED_MANUAL`, inspect the binding and effect. Verify no resend and no duplicate thread.

- [ ] **Step 6: Suspend the binding and stop**

- [ ] **Step 7: Record acceptance**

The document includes:

```text
binding_id
thread_id
actor_context_id
effect_id
clientUserMessageId
turn_id
completion evidence
restart reconciliation
no canonical write
```

- [ ] **Step 8: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_app-server-live-runtime/MANAGED_ROOT_MANUAL_ACCEPTANCE.md
git commit -m "docs: accept manual managed Operational Root"
```

---

## Task 23: Live-Accept Manual Portfolio Management

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/MANAGED_PORTFOLIO_MANUAL_ACCEPTANCE.md`

- [ ] **Step 1: Repeat the manual managed procedure for the exact Portfolio actor**

The actor kind must be `PORTFOLIO`.

- [ ] **Step 2: Send one no-tool manual turn**

Text:

```text
Read the current Portfolio/Root contract and reply exactly:
HMASD_MANAGED_PORTFOLIO_MANUAL_OK
Do not use tools and do not modify files.
```

- [ ] **Step 3: Verify isolation**

```text
Portfolio binding cannot impersonate Operational Root
Root binding cannot impersonate Portfolio
thread names/previews do not establish identity
legacy history has no authority
```

- [ ] **Step 4: Suspend and record acceptance**

- [ ] **Step 5: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_app-server-live-runtime/MANAGED_PORTFOLIO_MANUAL_ACCEPTANCE.md
git commit -m "docs: accept manual managed Portfolio"
```

---

## Task 24: Live-Accept Manual Typed Mailbox Delivery

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/MAILBOX_MANUAL_ACCEPTANCE.md`

- [ ] **Step 1: Start `MAILBOX_MANUAL`**

Both Root and Portfolio bindings must already be ACTIVE and idle.

- [ ] **Step 2: Create one repository payload artifact**

```text
docs/research/workflow-runs/2026-08-22_app-server-live-runtime/mailbox/ROOT_TO_PORTFOLIO_CANARY.md
```

Content:

```text
document_kind=mailbox_canary
authority=none
instruction=acknowledge the exact artifact reference only
```

- [ ] **Step 3: Enqueue a typed reference**

The mailbox contains:

```text
source actor
target actor
message kind
subject_ref
payload_ref
priority
```

It does not contain the file body or a scientific conclusion.

- [ ] **Step 4: Execute one explicit `MAILBOX_DELIVER_ONCE`**

Verify:

```text
one batch
at most one turn/start
Root↔Portfolio ACL
message delivery evidence
intake ordering by event/raw sequence
no timestamp-only acceptance
no automatic retry
```

- [ ] **Step 5: Restart and inspect**

Delivered messages stay delivered. A completed active batch closes and does not occupy the open slot.

- [ ] **Step 6: Record acceptance**

- [ ] **Step 7: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_app-server-live-runtime/mailbox docs/research/workflow-runs/2026-08-22_app-server-live-runtime/MAILBOX_MANUAL_ACCEPTANCE.md
git commit -m "docs: accept manual Root Portfolio mailbox delivery"
```

---

## Task 25: Implement and Live-Accept One Explicitly Armed Single Wake

**Files:**
- Modify: `tools/codex_supervisor/host_control.py`
- Modify: `tools/codex_supervisor/wake_scheduler.py` only if required
- Create: `tests/codex_supervisor/test_single_wake_host.py`
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/SINGLE_WAKE_ACCEPTANCE.md`

**Interfaces:**
- `ARM_SINGLE_WAKE` is accepted only in `SINGLE_WAKE`.
- One host run has at most one accepted arm.
- After a wake is submitted or becomes uncertain/incident, the arm is consumed.

- [ ] **Step 1: Add one-arm test**

```python
def test_single_wake_profile_accepts_one_arm_only(host):
    first = host.arm_single_wake(operator="operator:test")
    assert first["armed"] is True
    with pytest.raises(SingleWakeAlreadyConsumed):
        host.arm_single_wake(operator="operator:test")
```

- [ ] **Step 2: Add no-event no-turn test**

Before an eligible mailbox message exists:

```text
turn/start count = 0
```

- [ ] **Step 3: Add one-event one-turn test**

After one eligible message:

```text
wake batch count = 1
turn/start count <= 1
arm consumed = true
```

- [ ] **Step 4: Add uncertain-consumes-arm test**

If submission is `SUBMISSION_UNCERTAIN`, no second submission occurs and the arm remains consumed.

- [ ] **Step 5: Implement bounded host loop**

The loop watches only the existing mailbox/effect ledger. It does not poll the model and does not use Hooks.

- [ ] **Step 6: Run focused tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_single_wake_host.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_single_wake
```

- [ ] **Step 7: Run one live single-wake canary**

Use one non-scientific typed mailbox artifact and one idle managed Root or Portfolio binding. Stop the host immediately after terminal evidence.

- [ ] **Step 8: Record acceptance**

The document states:

```text
scheduler_serve=false
arm_count=1
wake_batch_count=1
turn_start_count<=1
turn_steer_count=0
automatic_retry_count=0
provider_send_count=0
```

- [ ] **Step 9: Commit**

```powershell
git add tools/codex_supervisor/host_control.py tools/codex_supervisor/wake_scheduler.py tests/codex_supervisor/test_single_wake_host.py docs/research/workflow-runs/2026-08-22_app-server-live-runtime/SINGLE_WAKE_ACCEPTANCE.md
git commit -m "feat: add one-shot managed wake profile"
```

---

## Task 26: Add Deterministic Runtime Inspect and Explain

**Files:**
- Create: `tools/codex_supervisor/runtime_inspect.py`
- Modify: `tools/codex_supervisor/host_control.py`
- Modify: `tools/codex_supervisor/cli.py`
- Test: `tests/codex_supervisor/test_runtime_inspect.py`

**Interfaces:**
- `inspect_actor(actor_context_id)`
- `inspect_binding(binding_id)`
- `inspect_thread(thread_id)`
- `inspect_effect(effect_id)`
- `inspect_incident(incident_id)`
- `explain_why_not_wake(binding_id)`

- [ ] **Step 1: Add exact causal-chain test**

```python
def test_inspect_effect_returns_linked_owner_and_evidence(store):
    payload = inspect_effect(store, "effect-1")
    assert payload["effect_id"] == "effect-1"
    assert payload["owner_kind"]
    assert "raw_request_seq" in payload
    assert "operator_resolution" in payload
```

- [ ] **Step 2: Add no-model test**

The inspect module imports no model, transport-send, or MCP mutation component.

- [ ] **Step 3: Implement deterministic explanation**

`explain_why_not_wake()` returns reasons such as:

```text
binding_not_active
semantic_actor_not_eligible
thread_not_idle
open_batch_exists
mailbox_empty
lease_missing
single_wake_not_armed
single_wake_consumed
effect_unreconciled
incident_requires_operator
```

It does not infer from prose.

- [ ] **Step 4: Expose through `INSPECT` host request and read-only CLI**

- [ ] **Step 5: Run tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor/test_runtime_inspect.py `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_runtime_inspect
```

- [ ] **Step 6: Commit**

```powershell
git add tools/codex_supervisor/runtime_inspect.py tools/codex_supervisor/host_control.py tools/codex_supervisor/cli.py tests/codex_supervisor/test_runtime_inspect.py
git commit -m "feat: add deterministic supervisor inspection"
```

---

## Task 27: Stage 2 Acceptance, Rollback, and Merge

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/STAGE2_ACCEPTANCE.md`
- Create: `docs/research/workflow-runs/2026-08-22_app-server-live-runtime/ROLLBACK.md`
- Update: `docs/project/current-work/common/control_plane_runtime.md`

- [ ] **Step 1: Run all supervisor tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_stage2_supervisor
```

- [ ] **Step 2: Run integrated control-plane tests**

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m pytest `
  tests/codex_context_lifecycle `
  tests/hmasd_control_plane `
  tests/codex_semantic_mvp `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-app-server-live-runtime/.tmp_stage2_full
```

- [ ] **Step 3: Run static durability guard**

Require:

```text
scan_package() == []
```

Use:

```powershell
powershell.exe -NoProfile -NonInteractive -File `
  scripts/codex-supervisor-durability-doctor.ps1
```

- [ ] **Step 4: Request focused independent review**

Review only:

```text
external runtime and process identity
truthful readiness
host command channel and profile ACL
process-lifetime session owner
manual managed actor evidence
mailbox once
single wake
no canonical writes
no semantic interpretation
no mutation retry
```

Critical/High must be zero.

- [ ] **Step 5: Write Stage 2 acceptance**

Record exact evidence from:

```text
PHASE1_LIVE_OBSERVER_ACCEPTANCE
EPHEMERAL_CANARY_ACCEPTANCE
MANAGED_ROOT_MANUAL_ACCEPTANCE
MANAGED_PORTFOLIO_MANUAL_ACCEPTANCE
MAILBOX_MANUAL_ACCEPTANCE
SINGLE_WAKE_ACCEPTANCE
```

Also record:

```text
behavioral_hooks=false
native_auto_compaction=unchanged
managed_actor_kinds=OPERATIONAL_ROOT|PORTFOLIO
managed_em_cm=false
scheduler_serve=false
turn_steer=false
automatic_approval=false
automatic_provider_send=false
```

- [ ] **Step 6: Write rollback**

Rollback is:

```text
stop exact supervisor host
leave behavioral Hooks disabled
leave repository artifacts intact
suspend/revoke managed bindings
retain external runtime evidence
return Root/Portfolio to native sessions
continue ordinary native workflow
```

Do not delete incident/effect evidence.

- [ ] **Step 7: Commit**

```powershell
git add docs/research/workflow-runs/2026-08-22_app-server-live-runtime/STAGE2_ACCEPTANCE.md docs/research/workflow-runs/2026-08-22_app-server-live-runtime/ROLLBACK.md docs/project/current-work/common/control_plane_runtime.md
git commit -m "docs: accept explicit App Server runtime control"
```

- [ ] **Step 8: Merge through Operational Root**

```powershell
Set-Location C:\Projects\HMASD
git checkout aggressive
git pull --ff-only origin aggressive
git merge --no-ff codex-app-server-live-runtime-v1 `
  -m "merge: add explicit App Server runtime control"
```

Run the full integrated suite and durability guard again before push.

---

# Final Accepted Architecture

```text
Repository canonical plane
  AGENTS / Roles / ADR / PROJECT_MAP / CURRENT_WORK
  requirements / assignments / results / owner artifacts
                    │
                    │ explicit owner intent and artifact refs
                    ▼
Semantic ledger plane
  hmasd_orchestrator
  actor / workflow / epoch / obligation / packet / promotion refs
                    │
                    │ typed runtime identity and references
                    ▼
App Server runtime plane
  long-lived supervisor host
  durability kernel
  managed Root / Portfolio
  mailbox / one-shot wake / incidents / reconciliation
                    │
                    │ mechanical evidence only
                    ▼
Owner intake and canonical promotion
```

No layer may silently assume the authority of the layer above it.

---

# Explicitly Deferred After These Two Stages

```text
Managed CM host
Managed EM host
managed leaf actors
runtime task DAG
automatic reviewer routing
automatic technical acceptance
automatic scientific interpretation
automatic Portfolio disposition
automatic Provider send
scheduler serve
multiple automatic wakes
turn/steer
automatic approval
Agents SDK
Codex SDK
external workflow engine
high-frequency Hooks
custom compaction Hooks
```

These are separate future decisions, not missing acceptance items for this plan.

---

# Execution Handoff for Local Codex

Save this plan at:

```text
docs/superpowers/plans/2026-08-22-hmasd-context-foundation-and-app-server-runtime-two-stage-plan.md
```

Use this exact initial instruction:

```text
Read and execute:
docs/superpowers/plans/2026-08-22-hmasd-context-foundation-and-app-server-runtime-two-stage-plan.md

Read first:
AGENTS.md
.agents/roles/ROOT.md
docs/project/CONTEXT_PRECEDENCE.md
docs/project/CONTEXT_PROMOTION_POLICY.md
docs/project/PROJECT_MAP.md
docs/project/CURRENT_WORK.md
docs/project/CONTEXT_SOURCE_REGISTRY.toml
docs/project/LOW_INTRUSION_CONTROL_PLANE.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md

User intent is fixed:

- Stage 1 closes repository context foundations.
- Stage 2 adds explicit App Server runtime control.
- Do not restore behavioral Hooks.
- Do not alter native auto-compaction.
- Do not make SQLite canonical.
- Do not introduce recovery-maturity layers, generic send-arm states,
  per-operation fresh-operator receipts, or commit/runtime/doc admission binding.
- Preserve the narrow rule that evidence cannot be textually upgraded.
- Manage only Operational Root and Portfolio in Stage 2.
- Use explicit profiles and one process-lifetime App Server owner.
- Do not add scheduler serve, turn/steer, automatic approval, automatic Provider
  send, managed EM/CM, Agents SDK, or Codex SDK.

Execute Stage 1 in its own worktree and stop after Stage 1 acceptance/merge.
Begin Stage 2 only from the accepted Stage 1 baseline.
Use assignment-local context for children; do not send this whole plan to every
subagent.
Only Operational Root may commit or merge.
Stop on the first hard-gate failure and return exact evidence.
```
