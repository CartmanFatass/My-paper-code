# HMASD — instructions live with the role that executes them

This file used to be a 594-line constitution said to bind every role. It did
not: **only `CLAUDE.md` is injected automatically**, so this file bound whoever
happened to open it, which in practice was the Project Manager alone. Its content
was always that role's instructions. It now lives there.

| You are | Read |
|---|---|
| **Project Manager** (orchestrator) | `.agents/roles/PROJECT_MANAGER.md` |
| **Any subagent** | your `.claude/agents/<name>.md`, then `docs/project/AGENT_CONTEXT.md` |
| **External Pro** | only the question you were sent — nothing in this repository binds you |

Routing is in `CLAUDE.md`, which every role does load. Live state is in
`docs/project/CURRENT_WORK.md`.

Instructions belong to the actor that executes them. A rule an actor cannot load
is not a rule, and a rule an actor cannot act on is noise in its context.
