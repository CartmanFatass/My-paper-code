# HMASD Claude Code Entry

**This file is a signpost, and nothing else.** Every role loads it — the
orchestrator and every subagent alike — so it carries only what all of them need
and routes everything else.

It holds **no role-specific policy** beyond the marked block below. If a rule
binds one role, it lives in that role's file. This was not true before
2026-07-27: the orchestrator's loop mechanism, tool-batching rules and subagent
roster sat here **unmarked**, so every child loaded instructions it had no
authority to execute, while the orchestrator's own procedure was split across
three files. That is what "unclear authority" looked like in practice.

## Find your instructions

**Read your own row and stop.** Another role's file does not bind you.

| You are | Your instructions |
|---|---|
| **Project Manager** (main conversation, orchestrator) | `AGENTS.md` — its complete instructions. Then `docs/project/CURRENT_WORK.md` for what is live right now. |
| **Any subagent** | your own `.claude/agents/<name>.md`, then `docs/project/AGENT_CONTEXT.md`. Its **Unattended operation** and **Reporting honestly** sections bind you. |
| **External Pro** | only the question you were sent. Nothing in this repository binds you, and you are not asked to know the workflow. |

There is no separate constitution to load. Instructions belong to the actor that
executes them: a rule an actor cannot load is not a rule, and a rule an actor
cannot act on is noise in its context.

## Project Manager only — subagents skip this section

**Everything else you need is in `AGENTS.md`, which is not injected — you have to
open it.** These five are here because this file is the only one guaranteed to
load, and because each of them cost something real on 2026-07-27 while the rule
existed somewhere you had not read yet. They are the minimum that must hold even
if you read nothing else.

1. **All compute runs locally.** The cloud vehicle and every cross-device
   comparison design were retired by user ruling 2026-08-01. Before any run
   longer than a few minutes, check the shared workstation for the other line's
   processes (`scripts/check_compute_free.ps1`) and never touch them.
2. **Measure a rate before claiming a cause.** Two samples cannot separate a
   cause from a coin. Ten isolated runs cost ninety seconds.
3. **Verify a child's claim before it becomes a record.** Children are bound to
   report honestly; that protects the report, not the archive. Spot-check the
   load-bearing ones yourself and cite what you checked — **mechanically**:
   files present, schema intact, the number reproduced. Whether a run is
   *scientifically* valid is Pro's, never yours (`AGENTS.md`, **Scientific
   restraint**, user ruling 2026-07-30).
4. **A guard test needs a paired negative.** A test that cannot go red reads as
   coverage forever after. Watch it fail before you call it done.
5. **Waiting is in-band.** Ending a turn to wait is a stall, not a pause. Poll
   inside the turn, or hand back with a result or a named blocker.

A sixth, for anything you write here or elsewhere: **a duty must be executable by
the tool grant that carries it.** A duty without an affordance does not produce a
refusal — it produces an invention.

## Then read only what your task names

| Doing this | Read |
|---|---|
| Implementing against a frozen spec | your definition's **How work is done here** |
| Sizing a task before dispatching it | `$hmasd-task-design` |
| Running an external review round | `$hmasd-review-round` |
| Judging whether work is on path | `docs/project/RESEARCH_GOAL.md` |
| Designing evidence, freezing a contract | `docs/project/ALGORITHM_PRINCIPLES.md`, then `docs/project/EVIDENCE_COMPLEXITY_POLICY.md` |

Nothing else. Read the charter, definition or document your task actually names.

## What counts as true

```text
implementation_source = git-tracked code
runtime_evidence      = logs/<run-id>/
active_instructions   = this file, your role file, AGENTS.md, and what your task names
```

Historical modules, retired commands, past rounds and archived artifacts are
**not** active instructions. A document under `docs/archive/` or a superseded
round directory describes what was once true.

## Retiring a direction

Research code iterates fast and most directions die. A direction verified as
hopeless gets **the scientific record of its failure and nothing else** — what was
tried, what it returned, why it is dead. That is enough to stop the mistake
recurring years later, and it is the only part worth carrying.

Replace the body with a pointer. Do not maintain long documents for abandoned
work, and do not narrate a retirement in a document, a commit message or a reply.
Retired material competes for attention with live material on every read.

## Ownership

`docs/project/CURRENT_WORK.md` carries `active_pm_session`. If it names a session
other than yours, remain read-only unless an explicit handoff changes ownership.

Claiming it is one line in your first commit. A stale claim is not a lock: if the
named session's boundary is behind `HEAD` and you can advance it, take ownership
by naming yourself — a lock nobody can release is how a dead session blocks a
live one.
