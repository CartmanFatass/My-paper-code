# Codex Subagent Workflow Superpowers Skill Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `codex-subagent-workflow` so it acts as a Codex adapter for Superpowers-style subagent work, not as a competing workflow authority.

**Architecture:** The updated skill should defer to active Superpowers skills for process shape, especially `superpowers:dispatching-parallel-agents`, `superpowers:subagent-driven-development`, `superpowers:executing-plans`, `superpowers:requesting-code-review`, and `superpowers:writing-skills`. It should keep only the Codex/project-specific adapter responsibilities: official custom-agent TOML setup, model/runtime fields, no built-in fallback, lifecycle closing, HMASD role boundaries, memory hooks, ExpManager/ResultAnalyst evidence split, and project validation. The plan `docs/superpowers/plans/2026-07-08-subagent-workflow-superpowers-update.md` is superseded wherever it treats `codex-subagent-workflow` as an equal or higher authority than Superpowers.

**Tech Stack:** Markdown skill document at `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`, Markdown pressure-scenario notes under `docs/superpowers/skill-tests/`, and optional Python standard-library validator for the skill text.

## Global Constraints

- Superpowers workflow skills are the style and process source of truth when they are active.
- `codex-subagent-workflow` must not duplicate or override Superpowers execution loops, review cadence, task-brief/report mechanics, review-package mechanics, or blocked-status handling.
- `codex-subagent-workflow` may add Codex-specific adapter rules: official custom-agent TOML discovery, explicit model/runtime settings, no built-in fallback, `close_agent` lifecycle cleanup, HMASD role mapping, project memory hooks, and experiment evidence routing.
- Do not edit `.claude/` or Claude-specific files.
- Do not reintroduce project `manifest.yaml` fallback.
- Do not spawn or recommend built-in `worker`, `explorer`, or `default` as a fallback for project roles.
- Do not reintroduce old low-concurrency wording such as `2-3 agents`, `old2`, `conservative`, `not a hard cap`, or `not a cap`.
- Keep the main controller responsible for user intent, algorithm discussion, execution decisions, subagent coordination, interpretation, git boundaries, and final explanation.
- Keep LongTimeMemoryManager memory-only.
- Keep ExpManager factual/operational and ResultAnalyst artifact-metric focused.
- This plan updates the global skill and its tests only; project `AGENTS.md`, `.codex/agents/README.md`, TOML roles, and compact memory can be aligned in a later execution wave after the skill change is accepted.

---

## File Structure

- Modify `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`: target skill to rewrite.
- Create `docs/superpowers/skill-tests/codex-subagent-workflow-pressure-scenarios.md`: pressure scenarios and baseline observations for the skill edit.
- Create `scripts/validate_codex_subagent_workflow_skill.py`: validator that checks the updated skill is an adapter, not a competing workflow.

---

### Task 1: Write Skill Pressure Scenarios Before Editing

**Files:**
- Create: `docs/superpowers/skill-tests/codex-subagent-workflow-pressure-scenarios.md`

**Interfaces:**
- Consumes: `superpowers:writing-skills` requirement that skill edits start with pressure scenarios.
- Produces: concrete failure cases used to judge the skill rewrite.

- [ ] **Step 1: Create pressure scenario file**

Create `docs/superpowers/skill-tests/codex-subagent-workflow-pressure-scenarios.md` with this content:

```markdown
# codex-subagent-workflow Pressure Scenarios

Purpose: verify that codex-subagent-workflow behaves as a Codex adapter for
Superpowers workflows instead of a competing workflow authority.

## Scenario 1: Active Superpowers SDD Review Cadence

User asks to execute a Superpowers implementation plan with
superpowers:subagent-driven-development. The current codex-subagent-workflow
contains HMASD batch-review language.

Expected updated behavior:
- Follow the active Superpowers SDD process for task review cadence.
- Use codex-subagent-workflow only to map task roles to official Codex custom
  agents, explicit model/runtime settings, and lifecycle cleanup.
- Do not replace the active Superpowers review loop with a different Codex-only
  cadence.

## Scenario 2: Parallel Independent Investigations

User asks to investigate four independent failures in separate files. The active
skill is superpowers:dispatching-parallel-agents.

Expected updated behavior:
- Group failures by independent domain.
- Dispatch one agent per independent domain in the same response when scopes do
  not share state.
- Use Codex adapter rules only for custom-agent names, no fallback, and close
  behavior.

## Scenario 3: Built-In Fallback Temptation

A required custom agent is not surfaced by the current spawn schema.

Expected updated behavior:
- Stop delegation and report that project custom-agent config is not loaded.
- Do not spawn built-in worker, explorer, default, or any role prompt fallback.

## Scenario 4: Memory Service Overreach

After experiment result interpretation, a memory update is needed.

Expected updated behavior:
- Main controller decides the accepted interpretation.
- LongTimeMemoryManager updates memory from the controller decision and raw
  evidence pointers.
- LongTimeMemoryManager does not own algorithm, execution, subagent routing, or
  user-facing interpretation.

## Scenario 5: ExpManager And ResultAnalyst Evidence Split

An experiment run is active and existing CSV artifacts also need gate tables.

Expected updated behavior:
- ExpManager handles process/run-state facts, status files, transcripts, and
  factual ExpRecord update.
- ResultAnalyst reads already-written artifacts for metric/gate extracts.
- Main controller integrates both and decides pass/fail/defer.
```

- [ ] **Step 2: Record baseline observations**

Read the current `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md` and append this section to the pressure scenario file:

```markdown
## Baseline Observations From Current Skill

- Potential conflict: the skill states its own review cadence and parallel-wave
  rules instead of explicitly deferring to active Superpowers skills.
- Potential conflict: the skill is long enough that future agents may treat it
  as a full workflow replacement rather than a Codex adapter.
- Useful content to preserve: official TOML custom-agent contract, no fallback,
  lifecycle close rule, HMASD role boundaries, ExpManager/ResultAnalyst split,
  ExternalReview raw-evidence rule, and memory-governance boundary.
```

- [ ] **Step 3: Verify pressure scenarios exist**

Run:

```powershell
rg -n "Scenario 1|Scenario 2|Scenario 3|Scenario 4|Scenario 5|Baseline Observations" docs\superpowers\skill-tests\codex-subagent-workflow-pressure-scenarios.md
```

Expected: all five scenario headings and the baseline section are found.

---

### Task 2: Reframe Skill Authority And Overview

**Files:**
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`

**Interfaces:**
- Consumes: Superpowers style-source requirement.
- Produces: skill intro that makes precedence unambiguous.

- [ ] **Step 1: Replace the overview**

Replace the current `## Overview` section with:

```markdown
## Overview

This skill is a Codex adapter for Superpowers-style subagent work. It does not
replace active Superpowers workflow skills. When a Superpowers skill is active,
follow that skill's process shape first and use this skill only for Codex
project-local custom-agent setup, role mapping, runtime settings, memory hooks,
and lifecycle cleanup.

Source-of-truth order:

1. The user's current explicit request.
2. The active Superpowers skill body, when one is being used.
3. Project `AGENTS.md` and `.codex/agents/README.md`.
4. This skill's Codex adapter rules.

Core principle: the active Codex session is the controller; subagents are
bounded workers. Delegating memory, experiments, review, or evidence extraction
does not delegate project governance.
```

- [ ] **Step 2: Add required Superpowers cross-reference**

After the new overview, add:

```markdown
## Required Superpowers Background

When doing implementation-plan execution or multi-agent investigation, use the
relevant Superpowers skill directly:

- `superpowers:dispatching-parallel-agents` for multiple independent problem
  domains.
- `superpowers:subagent-driven-development` for same-session execution of an
  implementation plan with task briefs, reports, review packages, progress
  ledger, and review loop.
- `superpowers:executing-plans` for inline execution when subagent-driven
  development is not being used.
- `superpowers:requesting-code-review` for broad code-review handoffs.
- `superpowers:writing-skills` before editing this or any other skill.

This skill must not restate those workflows as a competing procedure. It should
only explain how HMASD maps those workflows onto Codex custom agents and project
memory boundaries.
```

- [ ] **Step 3: Verify precedence wording**

Run:

```powershell
rg -n "Codex adapter|Source-of-truth order|active Superpowers skill|must not restate" C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: four matches.

---

### Task 3: Remove Or Downgrade Conflicting Workflow Sections

**Files:**
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`

**Interfaces:**
- Consumes: existing sections `Workflow-Level Authorization And Throttling`, `Role Boundaries`, and Superpowers execution-plan paragraphs.
- Produces: adapter language that does not override active Superpowers skills.

- [ ] **Step 1: Replace Superpowers execution-plan directive**

Replace the paragraph beginning `For superpowers subagent-driven development or execution-plan implementation` through the paragraph ending `Use ImplementationReviewer as a cost-controlled batch` with:

```markdown
## Superpowers Workflow Adapter

When a Superpowers workflow skill is active, do not invent a parallel Codex
workflow. Use the active Superpowers process and map its handoffs onto HMASD
Codex roles:

- Implementer handoffs map to `PlanImplementer` for accepted-plan core code,
  or `PlanImplementerFrontier` only when the task brief justifies bounded xhigh
  architecture/algorithm judgment during implementation.
- Implementer handoffs map to `SparkImplementer` for bounded non-core
  mechanical implementation from a complete task brief.
- Investigation handoffs map to `codebase-scout`, `ResultAnalyst`,
  `ExpManager`, `test-runner`, or `WorkflowAuditor` when their role boundary
  matches the Superpowers task.
- Reviewer handoffs map to `ImplementationReviewer` when the active
  Superpowers skill calls for a review or when the user/project workflow asks
  for a milestone, high-risk, or final review.

For `superpowers:dispatching-parallel-agents`, follow its independent-domain
rule: one focused agent per independent problem domain, dispatched in the same
response when there is no shared state.

For `superpowers:subagent-driven-development`, follow its task brief, report
file, review package, progress ledger, status handling, and review-loop
requirements. This skill supplies Codex custom-agent names and HMASD boundaries;
it does not replace the Superpowers loop.

For HMASD implementation workflows, do not reduce required task/final review
gates to control cost. Keep review gates and control cost through reviewer
model tiers.
```

- [ ] **Step 2: Keep Codex-only lifecycle section**

Ensure `## Lifecycle Protocol` still contains:

```markdown
Call `close_agent` unless the same subagent immediately needs a follow-up.
```

- [ ] **Step 3: Verify removed conflict phrases**

Run:

```powershell
rg -n "automatic per-task reviewer|not as an automatic per-task reviewer|Use ImplementationReviewer as a cost-controlled batch|routes core code work to" C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: no matches.

- [ ] **Step 4: Verify adapter phrases**

Run:

```powershell
rg -n "Superpowers Workflow Adapter|map its handoffs|does not replace the Superpowers loop|project preference" C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: four matches.

---

### Task 4: Preserve Codex-Specific Adapter Content

**Files:**
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`

**Interfaces:**
- Consumes: useful current Codex-specific sections.
- Produces: concise adapter sections that do not duplicate Superpowers.

- [ ] **Step 1: Keep official custom-agent contract**

Ensure the skill still states:

```markdown
Official custom agent files must define `name`, `description`, and
`developer_instructions`. Optional runtime fields such as `model`,
`model_reasoning_effort`, `sandbox_mode`, `approval_policy`,
`nickname_candidates`, `service_tier`, `mcp_servers`, and `skills.config` can be
set there so subagents do not silently inherit unsuitable defaults.
```

- [ ] **Step 2: Keep no-fallback policy**

Ensure the skill still states:

```markdown
Spawn project subagents only by official custom agent name. If a required custom
agent is not exposed by the current `spawn_agent` schema, stop delegation and
report a config-loading problem.
```

- [ ] **Step 3: Keep memory governance boundary**

Ensure the skill still states:

```markdown
LongTimeMemoryManager is a memory service. It may assess memory impact,
maintain compact memory, and archive records, but it does not own project
governance or execution decisions.
```

- [ ] **Step 4: Keep ExpManager/ResultAnalyst split**

Ensure the skill still states:

```markdown
ExpManager owns experiment operations and factual records. ResultAnalyst owns
metric/gate extraction from existing artifacts.
```

- [ ] **Step 5: Verify preserved adapter content**

Run:

```powershell
rg -n "Official custom agent files must define|Spawn project subagents only by official custom agent name|LongTimeMemoryManager is a memory service|ExpManager owns experiment operations" C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: four matches.

---

### Task 5: Add Skill-Specific Validator

**Files:**
- Create: `scripts/validate_codex_subagent_workflow_skill.py`

**Interfaces:**
- Consumes: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`.
- Produces: a local check that the skill is framed as a Superpowers adapter and does not contain known conflict phrasing.

- [ ] **Step 1: Create validator**

Create `scripts/validate_codex_subagent_workflow_skill.py` with:

```python
from __future__ import annotations

import re
import sys
from pathlib import Path


SKILL = Path.home() / ".codex" / "skills" / "codex-subagent-workflow" / "SKILL.md"

REQUIRED = {
    "adapter": re.compile(r"Codex adapter"),
    "source_order": re.compile(r"Source-of-truth order"),
    "active_superpowers": re.compile(r"active Superpowers skill"),
    "workflow_adapter": re.compile(r"Superpowers Workflow Adapter"),
    "no_builtin_fallback": re.compile(r"Spawn project subagents only by official custom agent name"),
    "close_agent": re.compile(r"close_agent"),
    "ltm_boundary": re.compile(r"LongTimeMemoryManager is a memory service"),
    "exp_result_split": re.compile(r"ExpManager owns experiment operations and factual records"),
}

FORBIDDEN = {
    "old_agent_count": re.compile(r"\b2-3 agents\b", re.IGNORECASE),
    "old2": re.compile(r"old2", re.IGNORECASE),
    "low_concurrency_residue": re.compile(r"conservative|not a hard cap|not a cap", re.IGNORECASE),
    "competing_per_task_review": re.compile(r"automatic per-task reviewer|not as an automatic per-task reviewer", re.IGNORECASE),
    "built_in_fallback": re.compile(r"fallback to (worker|explorer|default)", re.IGNORECASE),
}


def main() -> int:
    if not SKILL.exists():
        print(f"missing skill: {SKILL}", file=sys.stderr)
        return 1
    text = SKILL.read_text(encoding="utf-8")
    missing = [name for name, pattern in REQUIRED.items() if not pattern.search(text)]
    if missing:
        print(f"missing required skill patterns: {', '.join(missing)}", file=sys.stderr)
        return 1
    for name, pattern in FORBIDDEN.items():
        match = pattern.search(text)
        if match:
            print(f"forbidden skill pattern {name}: {match.group(0)!r}", file=sys.stderr)
            return 1
    print("codex-subagent-workflow skill validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run validator**

Run:

```powershell
python scripts\validate_codex_subagent_workflow_skill.py
```

Expected:

```text
codex-subagent-workflow skill validation ok
```

---

### Task 6: Run Skill Edit Verification

**Files:**
- Read: `docs/superpowers/skill-tests/codex-subagent-workflow-pressure-scenarios.md`
- Read: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`

**Interfaces:**
- Consumes: pressure scenarios from Task 1.
- Produces: final verification notes appended to the pressure scenario file.

- [ ] **Step 1: Verify scenario coverage manually**

Append this section to `docs/superpowers/skill-tests/codex-subagent-workflow-pressure-scenarios.md`:

```markdown
## Post-Edit Verification Notes

- Scenario 1: The updated skill defers to active Superpowers SDD and only maps
  Codex roles/runtime/lifecycle.
- Scenario 2: The updated skill defers to dispatching-parallel-agents for
  independent-domain parallelism.
- Scenario 3: The updated skill preserves the official custom-agent-only
  no-fallback policy.
- Scenario 4: The updated skill preserves LongTimeMemoryManager as memory-only.
- Scenario 5: The updated skill preserves ExpManager/ResultAnalyst evidence
  boundaries.
```

- [ ] **Step 2: Run targeted searches**

Run:

```powershell
rg -n "defers to active Superpowers|official custom-agent-only|memory-only|ExpManager/ResultAnalyst" docs\superpowers\skill-tests\codex-subagent-workflow-pressure-scenarios.md
```

Expected: matches for all four phrases.

- [ ] **Step 3: Run final validator**

Run:

```powershell
python scripts\validate_codex_subagent_workflow_skill.py
```

Expected:

```text
codex-subagent-workflow skill validation ok
```

---

## Final Verification

- [ ] Run:

```powershell
python scripts\validate_codex_subagent_workflow_skill.py
```

Expected:

```text
codex-subagent-workflow skill validation ok
```

- [ ] Run:

```powershell
rg -n "2-3 agents|old2|conservative|not a hard cap|not a cap|automatic per-task reviewer" C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: no matches.

- [ ] Run:

```powershell
rg -n "Codex adapter|Source-of-truth order|Superpowers Workflow Adapter|does not replace the Superpowers loop" C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: matches for all four phrases.

---

## Self-Review

Spec coverage:
- The plan makes Superpowers the process source of truth.
- The plan updates only `codex-subagent-workflow` and skill-specific tests/validator.
- The plan preserves Codex-only value: official TOML roles, model/runtime fields, no fallback, lifecycle cleanup, memory boundaries, and experiment evidence split.
- The plan explicitly removes the parts most likely to conflict with Superpowers review cadence and execution loops.

Naming consistency:
- Target skill path is consistently `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`.
- Pressure scenario path is consistently `docs/superpowers/skill-tests/codex-subagent-workflow-pressure-scenarios.md`.
- Validator path is consistently `scripts/validate_codex_subagent_workflow_skill.py`.
