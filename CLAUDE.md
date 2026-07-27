# HMASD Claude Code Entry

**This file is a signpost, and nothing else.** Every role loads it — the
orchestrator and every subagent alike — so it carries only what all of them need
and routes everything else.

It holds **no role-specific policy**. If a rule binds one role, it lives in that
role's file. This was not true before 2026-07-27: the orchestrator's loop
mechanism, tool-batching rules and subagent roster sat here, so every child
loaded instructions it had no authority to execute, while the orchestrator's own
procedure was split across three files. That is what "unclear authority" looked
like in practice.

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

## Then read only what your task names

| Doing this | Read |
|---|---|
| Implementing | `$hmasd-agile-research-development` |
| Running an external review round | `$hmasd-review-round` |
| Judging whether work is on path | `docs/project/RESEARCH_GOAL.md` |
| Designing evidence, freezing a contract | `docs/project/ALGORITHM_PRINCIPLES.md`, then `docs/project/EVIDENCE_COMPLEXITY_POLICY.md` |
| Deciding which machine runs something | `docs/project/COMPUTE_ROUTING.md` |

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

`docs/project/CURRENT_WORK.md` records who is driving. If it names another active
Project Manager, remain read-only unless an explicit handoff changes ownership.
