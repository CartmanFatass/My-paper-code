---
name: hmasd-task-design
description: Use before dispatching an implementer or any bounded child — how to size the task, what evidence is proportional, what to delete, and how to write a brief that will not be contradicted by the procedure governing the child.
---

# Sizing and briefing a bounded task

Project Manager only. Load this when you are about to delegate.

## Sizing the task — agile research development, from the scoping side

This is what you apply when you **design** a task. The implementer definition
carries the execution side of the same principle; neither restates the other,
because scoping and executing are different jobs.

**Maintainability is not the requirement here; reproducibility is.** These
packages are not extended — they are built, produce evidence, and are superseded
(G20 by G20R by G20R2). So extensibility, adapters and backward compatibility are
dead weight, and a brief that asks for them is asking for waste. But a package
*is* the evidence for a claim, so it must produce the same number from the same
commit in six months: frozen seeds, the registered interpreter and thread count,
declared RNG stream ownership, exact replay. **Trade maintainability away freely;
never trade reproducibility.** When those two conflict in a brief you are
writing, reproducibility wins and you say so explicitly.

**Scope one discriminator, not one feature.** The task is the smallest change
that can move the decision. Name the files it may touch and the files it may
not — the out-of-scope list is deliberate staging, and the implementer is told to
stop rather than widen it, so an omission there reads as permission.

**Size the evidence to the claim, in the brief, before dispatch.** Do not leave
it to the child to decide how much proof is enough:

| Change | Smallest sufficient evidence |
|---|---|
| helper or schema | one focused check |
| bug or invariant repair | reproduction, regression if durable, focused rerun |
| runner/analyzer integration | focused suite plus one bounded exercise |
| protected cross-file path | frozen contract, focused evidence, optional one review |

A broad suite is for a changed **shared surface** only. Asking for one otherwise
buys nothing and hides the signal you wanted.

**Say what to delete.** No backward compatibility: replaced interfaces, adapters,
migrations, fallbacks, state and tests go with the change. Git history is the
archive. If you do not say this, a careful implementer will preserve the old path
"just in case" and you will accept a worse artifact than you asked for.

**Do not add ceremony the brief does not need** — no brainstorm, plan, worktree,
ledger or approval step when the outcome, files, exclusions and completion are
already known. That ceremony is the generic-agile reflex, and it is exactly what
this project does not run.

## Authoring the brief

**A brief that contradicts the procedure governing the child is worse than no
brief: the child will follow the brief.** This has already cost one retired
review round. When a Skill or charter governs the work, read it before writing
and quote its constraints. Never paraphrase a procedure from memory. If brief and
procedure disagree, the procedure is right and the brief is the defect.

Children carry no workflow knowledge by design — `AGENT_CONTEXT.md` gives them
environment and behaviour only. **Everything task-specific must be in the brief.**
A worker that has to reconstruct the process from documents is a worker guessing.

Three traps already hit:

- **Never put an instruction inside a block the child will copy verbatim.** A
  transcription brief on 2026-07-27 ended a dictated Decision cell with *"carry
  that qualifier through into the cell rather than dropping it"* — and the child,
  correctly treating the block as content, copied the instruction into
  `ExpRecord.md` along with the facts. A transcriber cannot tell your directions
  from your dictation; that boundary is the author's job. Put the content in one
  block and the instructions about it outside that block.

- "Submit the question verbatim" reads as *paste the file body*. The review
  transport contract is the opposite — the question carries exact paths, not file
  contents, and the reviewer reads the repository itself.
- Declaring evidence paths in the brief or a side manifest does not put them in
  front of the reviewer. The freshness fence names only the question, so the
  allow-list has to live inside the question under a literal `## Evidence to read`
  heading.

