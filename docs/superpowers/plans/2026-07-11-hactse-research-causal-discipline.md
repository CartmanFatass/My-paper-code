# HA-CTSE Research Causal Discipline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a binding project rule that organizes HA-CTSE experiments by causal edges, preserves failed evidence, and requires the correct comparison baseline before code or reward promotion.

**Architecture:** Add one self-contained policy section to `AGENTS.md` immediately after the experiment communication and cloud-handoff rules. The section defines the causal chain, failure-review gate, four-level baseline hierarchy, promotion ladder, and prohibited comparison/retry patterns without changing algorithm code or runtime behavior.

**Tech Stack:** Markdown project instructions; `rg` and `git diff --check` for verification.

## Global Constraints

- Preserve all pre-existing uncommitted `AGENTS.md` edits.
- Modify no algorithm, experiment runner, memory, or subagent configuration file.
- Do not encode volatile round-specific metric values as permanent workflow rules.
- Keep the main controller responsible for scientific interpretation and user-facing decisions.

---

### Task 1: Add the causal research and baseline discipline

**Files:**
- Modify: `AGENTS.md`, after the cloud-handoff rule and before `Subagent Runtime Rules`.

**Interfaces:**
- Consumes: the existing `Experiment Communication Hard Gate`, `memory/ExpRecord.md`, and accepted experiment plans.
- Produces: a binding controller rule for causal-edge registration, failure review, baseline selection, and experiment promotion.

- [ ] **Step 1: Insert the new policy section**

Add a section that requires:

```text
causal edge -> pre-registered gate -> matching baseline -> result classification
             -> retained conclusion -> next authorized edge
```

The section must define diagnostic-null, mechanism-matched HA-CTSE,
async-vs-fixed/shared, and HMASD-parity baselines; require the lowest sufficient
baseline; and prohibit downstream reward work while an upstream edge is open.

- [ ] **Step 2: Verify policy coverage**

Run:

```powershell
rg -n "Research Causal Discipline|Diagnostic null|Mechanism-matched|Async temporal|HMASD parity|promotion ladder|Failure review" AGENTS.md
```

Expected: every required policy concept appears in the new section.

- [ ] **Step 3: Check Markdown and diff hygiene**

Run:

```powershell
git diff --check -- AGENTS.md docs/superpowers/plans/2026-07-11-hactse-research-causal-discipline.md
git diff -- AGENTS.md
```

Expected: no whitespace errors; the `AGENTS.md` diff preserves pre-existing edits and adds only the new research-discipline section for this task.

