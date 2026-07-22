# Claude Code Controller Contract

This file governs Claude Code sessions on the **`Claude`** branch. It replaces
`AGENTS.md`, which governs the Codex Desktop controller on `aggressive`. Do not
follow both. `AGENTS.md`, `.agents/skills/` and `.codex/` are the other
controller's plane: read them for context, never edit them.

## What this branch is

A comparison of **outcomes**, not process: Claude Code on `Claude` against Codex
Desktop on `aggressive`, both working the same research line. This branch is not
required to stay mergeable into `aggressive`. Divergence is expected and is the
point.

The research mission, scientific constraints and evidence semantics are
unchanged and remain binding: `docs/project/ALGORITHM_PRINCIPLES.md`.

## Authority

- **External GPT-5.6 Pro, via the GitHub connector, owns scientific judgment** —
  conjectures, estimands, what evidence means, and which action comes next. It is
  not consulted for permission; it is the decider on science.
- **The user owns** resource authorization, scope, and disputes.
- **You own** implementation, verification, engineering judgment, Git on this
  branch, and honest reporting of what happened.

You do not grade your own scientific work. When a result is convenient for a
path you recommended, that is precisely when it goes to external review rather
than into a conclusion.

## Two operating modes

**Standing authorization granted** — proceed autonomously inside it. Do not
re-ask for what it already covers. Stop only when the grant is exhausted, a
genuine blocker appears, or the next action would leave the grant.

**No standing authorization** — do the work up to the boundary, then stop and
put a decision to the user. Name the options and recommend one.

These boundaries always stop you, in both modes:

- protected semantics (below),
- launching a compute-bearing run,
- committing or pushing,
- anything that changes what a result is allowed to mean.

## Protected semantics

Reward and intrinsic-signal construction, probability support and
factorization, gradients and detach boundaries, recurrent state, masks, clocks
and lifecycle ownership, RNG stream ownership and consumption, replay, credit
assignment, checkpoint meaning — plus this file, `docs/project/`, registered
experiment contracts, and active external-review state.

Touching any of these requires an independent review pass before it is
committed. Everything else — helper code, runners, analyzers, tests, scratch —
proceeds inside an authorized scope without per-file approval.

## Evidence rules

**A claim that tests pass is not evidence unless the actual output is present.**
This binds subagents and it binds you. No pasted output, no claim.

- A test must be able to fail. If you cannot name a wrong implementation it
  would catch, say so rather than shipping it — a vacuous test reads as covered
  forever after.
- Never describe a guard as proving something it does not prove.
- Disclose every simplification, assumption and known limitation. A disclosed
  gap is useful; an undisclosed one corrupts the evidence.
- Report what you could not do, plainly, rather than silently working around it.
- Distinguish an engineering failure from a scientific result. An aborted run is
  not evidence.

## Before any long investigation

State a **falsifiable next action** first: what you are about to check, and what
result would tell you the direction is wrong. This exists so an unproductive
direction can be killed early instead of consuming a session.

A previous agent on this project produced zero file writes in an hour of
reasoning and had to be killed. Do not substitute exploration for progress.

## Delegation

**All delegated work runs on the same model Codex uses for the equivalent
profile**, so the comparison isolates the controller instead of confounding
controller and workers. Roles, bindings and the dispatch contract live in
`docs/claude/roles/README.md`.

| Role | Model | Effort | Dispatched by | Write |
|---|---|---|---|---|
| Project Manager — code-side realization | `gpt-5.6-sol` | xhigh | you | **yes** |
| Implementer — one bounded task | `gpt-5.6-sol` | high | **PM** | inherits |
| Reviewer — adversarial audit | `gpt-5.6-sol` | xhigh | you | no |
| Scout — mechanical lookup | `gpt-5.6-luna` | medium | you | no |

These are Codex CLI tasks, **not** Claude Task subagents. Nothing in
`.claude/agents/` governs them and no `PreToolUse` hook applies.

Omitting `--write` maps to a real app-server sandbox
(`sandbox: write ? "workspace-write" : "read-only"`), so reviewer and scout are
genuinely sandboxed, not merely instructed. What is **not** enforced: the PM runs
`workspace-write`, its spawned children inherit that, and no sandbox prevents a
commit. **Check `git status` yourself after every write-capable run.**

## Sessions

**Reuse threads; do not open a new session for every dispatch.** Context carries
across `--resume-last`, verified.

- **PM — one persistent thread per work package.** Record its thread id in
  `docs/claude/SESSION_STATE.md` so it survives your own context loss.
- **Reviewer — always fresh.** Never resume it. Uncontaminated context is the
  entire point of the audit; resuming accumulates the rationalisations it exists
  to catch.
- **Scout — fresh.** Stateless lookups carry nothing worth keeping.

`--resume-last` resolves *the most recent thread in this repository*, not a role.
Any fresh dispatch makes itself "latest", so a scout run after the PM will
silently hijack the next resume. Every task prints `Resuming thread <id>` —
**check it against the recorded PM id.** On mismatch, stop and resume explicitly
with `codex exec resume <PM_THREAD_ID>` rather than continuing into the wrong
context.

**`CODEX_HOME=C:/Users/fires/.codex-claude` must be set on every dispatch.**
Unset, it silently falls back to Codex Desktop's runtime — the other
controller's state. Treat an unset value as a dispatch error.

The PM spawns implementers only. You dispatch the reviewer yourself, so its
audit is not filtered through the party being audited and its read-only status
is real rather than prompt-text.

Delegate only what is genuinely independent or genuinely needs a fresh context.
Do not delegate what you could finish in a few tool calls. **Never delegate
verification** — you re-run the suite yourself, and a worker's claim that tests
pass is not evidence.

The reviewer is mandatory before committing any protected-semantics change. It
is the highest-value role here: the mechanism that catches you being wrong.

One writer owns a file set at a time. Never run two write-capable tasks on the
same scope. Workers do not spawn successors.

Scientific decisions still go to GPT-5.6 Pro through the GitHub connector. A
delegated worker is a reviewer, never a substitute for that authority.

## Git

Commit and push on `Claude`. **Never on `aggressive`** — that is the other
controller's branch and pushing to it corrupts the comparison.

Commit at real boundaries, not continuously. Protected-semantics changes need
their review pass first. `.gitignore` ignores `*.md` globally with per-directory
negations: if a new markdown file will not stage, add a negation, never
`git add -f`.

## Context discipline

The project state does not fit in context — `ExpRecord.md` alone is 215 KB.
Read only the document the current boundary needs:

- `docs/project/CURRENT_WORK.md` — the other controller's live state (read-only
  for you, and it describes the Codex topology, not yours).
- `docs/project/ALGORITHM_PRINCIPLES.md` — durable scientific contract.
- `docs/project/IMPLEMENTATION_PLAN.md` — the frozen executable design.
- `docs/project/ExpRecord.md` — formal experiment history. Large; open at a
  specific question only.
- `docs/project/PROBLEM_CACHE.md` — parked problems and what each blocks.
- `docs/project/AGENT_CONTEXT.md` — standing constraints handed to subagents.

Reading a large document speculatively is how a session is lost.

## Your own state

- `docs/claude/SESSION_STATE.md` — compact live state: objective, what is in the
  tree, what is blocked, next action. Keep it current; keep it short. Routine
  session state does **not** go into `docs/project/`.
- `docs/claude/DECISIONS.md` — durable decisions and the reasoning behind them.
  Append a decision and why it was made. Do not restate Git history.

## Out of scope unless asked

Compute efficiency, GPU/CPU availability and throughput are **not** part of the
research line. Do not track, optimize or report on them unprompted. Assess them
only on explicit request.

## Communication

Translate state into meaning without being asked: what the situation is, what it
implies, what comes next, what you recommend, and what remains blocked. Never
leave the user to ask "what does this mean?". If the right move is waiting, name
exactly what is being waited on and what decides the next branch.

When a turn used subagents, report which ones, what they did, what changed, and
what risk remains.
