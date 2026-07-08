# Superpowers Subagent Lifecycle Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate HMASD Codex subagent handling to the Superpowers pattern: file handoffs, durable progress, explicit statuses, soft wait timeouts, and no duplicate dispatch after controller compaction or chat silence.

**Architecture:** Superpowers remains the process authority for task execution shape. HMASD Codex files only adapt that process to project roles (`ExpManager`, `ResultAnalyst`, `SparkImplementer`, `PlanImplementer`, reviewers, and memory managers). The migration adds a durable status/report contract for non-code experiment work and implementation work, then updates controller rules so `wait_agent` timeouts never imply task failure.

**Tech Stack:** Markdown protocol files, TOML custom-agent profiles, PowerShell verification commands, existing `scripts/` experiment runners, existing `memory/ExpRecord.md`, existing `.superpowers/sdd/progress.md` ledger convention.

## Global Constraints

- Superpowers process is authoritative when a Superpowers skill is active; `codex-subagent-workflow` is only the Codex adapter.
- The main Codex session remains controller; no MainAgent subagent.
- Do not use built-in `worker`, `explorer`, or `default` as fallback for project roles.
- A `wait_agent` timeout is a soft timeout: it means chat has not returned, not that the task failed.
- Do not close or supersede a subagent if its status/checkpoint/evidence files show progress.
- Do not duplicate a query or relaunch a task just because the subagent chat is silent.
- ExpManager owns experiment run-state facts and `ExpRecord.md` factual updates; ResultAnalyst owns metric/gate extraction from already-written artifacts.
- Large evidence must move through files, not chat.
- This plan changes workflow/configuration and helper artifacts only; it must not touch core algorithm code under `ha_ctse_process/`.

---

## File Structure

- Modify `AGENTS.md`: controller-level lifecycle rules, Superpowers authority, soft-timeout protocol, task/status vocabulary, and no duplicate-dispatch rule.
- Modify `.codex/agents/README.md`: detailed version of the same lifecycle and file handoff contract.
- Modify `.codex/agents/exp-manager.toml`: require checkpoint-before-deep-read, phase status, bounded output, and explicit final status vocabulary.
- Modify `.codex/agents/result-analyst.toml` if present: require metric extracts and no experiment launch/state mutation.
- Create `.codex/agents/templates/subagent-task-brief.md`: generic task brief template for project subagents, aligned with Superpowers task-brief style.
- Create `.codex/agents/templates/subagent-report.md`: report/status template with `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`, and file evidence fields.
- Create `.codex/agents/templates/expmanager-checkpoint.md`: checkpoint template for long experiment tasks.
- Create `scripts/check_subagent_handoff_contract.ps1`: lightweight verifier that required protocol strings and template files exist.
- Modify `memory/CURRENT_WORK.md`: compact pointer that this migration is active and that soft timeouts are mandatory.
- Do not modify `memory/ExpRecord.md` unless implementation testing creates or updates a real experiment fact.

---

### Task 1: Codify Superpowers Authority And Soft Timeout Rules

**Files:**
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `memory/CURRENT_WORK.md`

**Interfaces:**
- Consumes: Superpowers rules from `superpowers:subagent-driven-development` and `superpowers:dispatching-parallel-agents`.
- Produces: Controller-readable protocol text that future sessions must follow before using ExpManager/ResultAnalyst or implementation subagents.

- [ ] **Step 1: Update controller rule in `AGENTS.md`**

Add or replace the current ExpManager wait paragraph with this exact rule:

```markdown
- Controller waits on long-running or evidence-heavy subagent tasks with
  bounded soft timeouts. A `wait_agent` timeout means only that chat has not
  returned yet; it is not evidence of failure, completion, or abandonment.
  Before fallback, duplicate dispatch, or close, inspect the subagent's
  status/report files, expected outputs, process/file freshness, and any
  run-local checkpoint. If these show progress or a plausible in-flight phase,
  leave the subagent open and report that it is still working. Close or
  supersede only after capturing `DONE`, `DONE_WITH_CONCERNS`,
  `NEEDS_CONTEXT`, `BLOCKED`, an explicit user cancellation, or a checked
  workflow fault such as no status/evidence plus no process/file activity after
  a grace check. If an urgent user answer is needed, the controller may do a
  read-only status peek, but must not terminate the original subagent merely
  because the peek finished first.
```

- [ ] **Step 2: Update Superpowers authority wording in `AGENTS.md`**

Ensure `AGENTS.md` contains this exact rule near the Superpowers/Codex adapter section:

```markdown
When a Superpowers skill is active, Superpowers defines the process shape:
task briefs, report files, progress ledger, review packages, status handling,
and review loops. `codex-subagent-workflow` only maps those steps onto HMASD
custom agents and project memory boundaries. Do not invent a parallel Codex
workflow that contradicts an active Superpowers skill.
```

- [ ] **Step 3: Mirror both rules in `.codex/agents/README.md`**

Add the same two paragraphs from Steps 1 and 2 to `.codex/agents/README.md`.

- [ ] **Step 4: Update `memory/CURRENT_WORK.md`**

Add this compact pointer under the active plan pointers:

```markdown
- Superpowers migration note: subagent `wait_agent` timeouts are soft. If a
  subagent has written a status/report/checkpoint or output files are fresh,
  keep it open and do not fallback-close. Superpowers task briefs, report files,
  and durable progress ledgers are the authority for task execution shape.
```

- [ ] **Step 5: Verify text landed**

Run:

```powershell
Select-String -Path AGENTS.md,.codex\agents\README.md,memory\CURRENT_WORK.md -Pattern 'bounded soft timeouts|Superpowers defines the process shape|wait_agent.*soft' -Context 1,2
```

Expected: matches in all three files.

---

### Task 2: Add Project Subagent File-Handoff Templates

**Files:**
- Create: `.codex/agents/templates/subagent-task-brief.md`
- Create: `.codex/agents/templates/subagent-report.md`
- Create: `.codex/agents/templates/expmanager-checkpoint.md`
- Modify: `.codex/agents/README.md`

**Interfaces:**
- Consumes: Superpowers file handoff pattern.
- Produces: HMASD-specific templates future controller prompts can reference without pasting long context.

- [ ] **Step 1: Create task brief template**

Create `.codex/agents/templates/subagent-task-brief.md` with:

```markdown
# Subagent Task Brief

## Task ID

`<TASK-ID>`

## Role

`<ExpManager | ResultAnalyst | SparkImplementer | PlanImplementer | ImplementationReviewer | ExternalReviewManager | LongTimeMemoryManager>`

## Goal

<One sentence.>

## Requirements Source

- Plan/spec: `<path>`
- Relevant memory pointer: `<path>`
- Required first-read files: `<paths>`

## Owned Files / Directories

- `<path>`

## Forbidden Files / Directories

- `<path>`

## Exact Steps

1. <Step.>
2. <Step.>

## Required Evidence Files

- Report file: `<path>`
- Status/checkpoint file: `<path or n/a>`
- Extract files: `<path or n/a>`

## Required Checks

```powershell
<exact command>
```

Expected: `<expected result>`

## Return Contract

Return only:

- Status: `DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED`
- Report path
- Files changed
- Checks run
- Concerns/blockers
```

- [ ] **Step 2: Create report template**

Create `.codex/agents/templates/subagent-report.md` with:

```markdown
# Subagent Report

## Status

`DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED`

## Task ID

`<TASK-ID>`

## Agent Role

`<role>`

## Files Changed

- `<path>` — `<change summary>`

## Files Inspected

- `<path>` — `<bounded read or reason>`

## Commands / Checks

```powershell
<command>
```

Result: `<pass/fail/blocked>`

## Evidence Files

- `<path>`

## Summary

<Concise factual result.>

## Concerns / Blockers

- `<none or details>`

## Next Owner

`controller | ExpManager | ResultAnalyst | SparkImplementer | PlanImplementer | user`
```

- [ ] **Step 3: Create ExpManager checkpoint template**

Create `.codex/agents/templates/expmanager-checkpoint.md` with:

```markdown
# ExpManager Checkpoint

## Status

`IN_PROGRESS | DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED`

## Experiment ID

`<EXP-ID>`

## Phase

`prepare | launch | progress-check | metric-extract | exp-record-update`

## Started At

`<ISO timestamp>`

## Current Evidence Files

- Status file: `<runner_status.txt or n/a>`
- Transcript: `<runner_output.log or n/a>`
- Metric extract: `<metric_extract.md or n/a>`
- Error extract: `<error_extract.md or n/a>`

## Active Process / Command

```text
<command or no active command>
```

## Last Completed Step

<Short factual note.>

## Safe Resume Instruction

<Exactly what the controller or next ExpManager should inspect next.>
```

- [ ] **Step 4: Reference templates in `.codex/agents/README.md`**

Add:

```markdown
For any non-trivial subagent handoff, prefer file templates under
`.codex/agents/templates/`. The controller gives workers a task brief path and
requires a report path. ExpManager additionally writes an
`expmanager_checkpoint.md` before long progress/result checks so controller
soft timeouts can distinguish in-flight work from workflow faults.
```

- [ ] **Step 5: Verify templates exist**

Run:

```powershell
Test-Path .codex\agents\templates\subagent-task-brief.md
Test-Path .codex\agents\templates\subagent-report.md
Test-Path .codex\agents\templates\expmanager-checkpoint.md
```

Expected: three `True` lines.

---

### Task 3: Make ExpManager And ResultAnalyst Follow Explicit Status Contracts

**Files:**
- Modify: `.codex/agents/exp-manager.toml`
- Modify: `.codex/agents/result-analyst.toml` if present
- Modify: `.codex/agents/README.md`

**Interfaces:**
- Consumes: templates from Task 2.
- Produces: agent instructions that return explicit statuses and write checkpoint/extract files before large work.

- [ ] **Step 1: Update ExpManager final reply contract**

In `.codex/agents/exp-manager.toml`, ensure `developer_instructions` includes:

```text
For any task that writes or inspects more than a tiny bounded read, write a
report or checkpoint file first. Final chat replies must use the status
vocabulary `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
Return only the status, report/extract paths, changed files, checks run,
concerns/blockers, and next owner. Do not paste full logs, full CSV rows beyond
the requested bounded fields, or long transcripts.
```

- [ ] **Step 2: Update ExpManager timeout cooperation**

In `.codex/agents/exp-manager.toml`, ensure long work instructions include:

```text
If a controller wait may time out, that is expected. Keep working if the task is
in scope, but keep `expmanager_checkpoint.md` current enough that the
controller can see progress without interrupting you. Do not assume a
controller fallback peek cancels your task unless explicitly told so.
```

- [ ] **Step 3: Update ResultAnalyst if present**

If `.codex/agents/result-analyst.toml` exists, add:

```text
Write metric-heavy evidence to `metric_extract.md` or `gate_read.md`, then
return only `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED` plus
paths and concise metric highlights. Do not update `memory/ExpRecord.md` unless
the controller explicitly asks; ExpManager owns factual experiment records.
```

If the file does not exist, record in the task report:

```text
ResultAnalyst TOML not present; skipped by design.
```

- [ ] **Step 4: Verify model and status contract**

Run:

```powershell
Select-String -Path .codex\agents\exp-manager.toml,.codex\agents\result-analyst.toml -Pattern 'DONE_WITH_CONCERNS|expmanager_checkpoint|metric_extract|gpt-5.4-mini' -ErrorAction SilentlyContinue
```

Expected: ExpManager has status/checkpoint/model matches; ResultAnalyst has status/extract/model matches if present.

---

### Task 4: Add A Lightweight Contract Verifier

**Files:**
- Create: `scripts/check_subagent_handoff_contract.ps1`

**Interfaces:**
- Consumes: required strings and template paths from Tasks 1-3.
- Produces: a quick local check command for future workflow edits.

- [ ] **Step 1: Create verifier script**

Create `scripts/check_subagent_handoff_contract.ps1` with:

```powershell
param(
    [string]$Root = "."
)

$ErrorActionPreference = "Stop"
$rootPath = Resolve-Path -LiteralPath $Root

$requiredFiles = @(
    "AGENTS.md",
    ".codex/agents/README.md",
    ".codex/agents/exp-manager.toml",
    ".codex/agents/templates/subagent-task-brief.md",
    ".codex/agents/templates/subagent-report.md",
    ".codex/agents/templates/expmanager-checkpoint.md"
)

$requiredPatterns = @{
    "AGENTS.md" = @(
        "bounded soft timeouts",
        "Superpowers defines the process shape",
        "do not duplicate the query"
    )
    ".codex/agents/README.md" = @(
        "bounded soft timeouts",
        ".codex/agents/templates",
        "Superpowers defines the process shape"
    )
    ".codex/agents/exp-manager.toml" = @(
        "gpt-5.4-mini",
        "expmanager_checkpoint.md",
        "DONE_WITH_CONCERNS",
        "controller fallback peek"
    )
}

$failures = New-Object System.Collections.Generic.List[string]

foreach ($rel in $requiredFiles) {
    $path = Join-Path $rootPath $rel
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing file: $rel")
    }
}

foreach ($entry in $requiredPatterns.GetEnumerator()) {
    $path = Join-Path $rootPath $entry.Key
    if (-not (Test-Path -LiteralPath $path)) {
        continue
    }
    $text = Get-Content -Raw -LiteralPath $path
    foreach ($pattern in $entry.Value) {
        if ($text -notmatch [regex]::Escape($pattern)) {
            $failures.Add("Missing pattern '$pattern' in $($entry.Key)")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Subagent handoff contract check FAILED"
    foreach ($failure in $failures) {
        Write-Host " - $failure"
    }
    exit 1
}

Write-Host "Subagent handoff contract check passed"
```

- [ ] **Step 2: Run verifier before completing the migration**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check_subagent_handoff_contract.ps1
```

Expected:

```text
Subagent handoff contract check passed
```

---

### Task 5: Add A Migration Record And Execution Guidance

**Files:**
- Modify: `memory/IMPLEMENTATION_PLAN.md`
- Modify: `memory/CURRENT_WORK.md`
- Optionally modify: `memory/LTM/EXPERIMENT_ARCHIVE.md` only if a completed experiment conclusion is being archived in the same turn.

**Interfaces:**
- Consumes: completed docs/templates/verifier from Tasks 1-4.
- Produces: compact current memory so future sessions do not regress to chat-only waiting.

- [ ] **Step 1: Add an implementation-plan note**

Add this entry near the current workflow/infrastructure section of `memory/IMPLEMENTATION_PLAN.md`:

```markdown
### Workflow Migration: Superpowers-Style Subagent Lifecycle

Status: planned / in implementation.

Purpose: move HMASD Codex subagent handling to the Superpowers pattern:
task brief files, report files, durable progress, explicit statuses, and
soft `wait_agent` timeouts. A timeout is not a failure. If checkpoint/status
files show progress, the controller leaves the subagent open and does not
duplicate the task.
```

- [ ] **Step 2: Add concise current-work reminder**

Ensure `memory/CURRENT_WORK.md` contains:

```markdown
Superpowers migration note: subagent `wait_agent` timeouts are soft. If a
subagent has written a status/report/checkpoint or output files are fresh,
keep it open and do not fallback-close. Superpowers task briefs, report files,
and durable progress ledgers are the authority for task execution shape.
```

- [ ] **Step 3: Verify memory pointers**

Run:

```powershell
Select-String -Path memory\CURRENT_WORK.md,memory\IMPLEMENTATION_PLAN.md -Pattern 'Superpowers-Style Subagent Lifecycle|wait_agent.*soft|fallback-close'
```

Expected: matches in both files.

---

## Self-Review

**Spec coverage:** This plan covers the user's requested migration by anchoring to Superpowers authority, adding file handoffs, explicit statuses, soft timeout semantics, durable progress, and no duplicate dispatch/close behavior.

**Placeholder scan:** No `TBD`, `TODO`, or vague "handle edge cases" language is used in implementation steps.

**Type/name consistency:** Status vocabulary is consistently `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`; ExpManager checkpoint file is consistently `expmanager_checkpoint.md`; metric evidence is consistently `metric_extract.md`.

**Risk note:** This plan is workflow/configuration only. It intentionally does not modify core algorithm code or experiment runners beyond the optional verifier script.
