# HMASD Custom Subagents — Design

2026-07-21

## Purpose

Encode the durable constraints of this project into agent definitions instead of
retyping them into every dispatch brief. Two failures motivated this: an
implementer stalled for an hour with zero file writes because nothing instructed
it to prefer motion over completeness, and the implementer model had to be
corrected by hand after the fact because nothing pinned it.

An agent definition holds what is true every time. A brief holds what is true
this time.

## Roster

```
.claude/
  agents/
    hmasd-context.md        shared constraints, read by implementer and reviewer
    hmasd-implementer.md
    hmasd-reviewer.md
    hmasd-scout.md
    hmasd-monitor.md
```

| Agent | model | effort | tools | reads at start |
|---|---|---|---|---|
| implementer | `opus` | `high` | inherit all, plus a PreToolUse git hook | context + implementer engineering principles |
| reviewer | `opus` | `xhigh` | `Read, Grep, Glob, Bash`; `disallowedTools: Write, Edit, NotebookEdit` | context + reviewer review principles |
| scout | `haiku` | `low` | `Read, Grep, Glob` | inline environment block |
| monitor | `haiku` | `low` | `Read, Grep, Glob, Write` | inline environment block |

Tiered by design: the two heavyweight roles already pay for a principles read, so
a shared context file costs them little and removes drift between them. The two
lightweight roles need three lines of environment and never touch algorithm
semantics, so they carry those inline rather than reading two documents to run a
grep sweep.

Reviewer runs at `xhigh` rather than `high` because the frozen plan already
specified a read-only `xhigh` reviewer for this work, and review is where depth
has paid best: that pass caught a vacuous detachment test and a latent
`env_index` indexing bug that the full acceptance suite never reached.

## Source of truth

Agent definitions reference the existing engineering and review principles by
path rather than copying them:

- `.agents/skills/hmasd-implementer/references/engineering-principles.md`
- `.agents/skills/hmasd-reviewer/references/review-principles.md`

Those files are durable technical constraints rather than Codex workflow, they
bind this work regardless of which agent executes, and the Codex tree stays
unmodified. Copying would create two live versions that drift.

## What lives where

`hmasd-context.md` carries: the SB3 interpreter path and the rule never to use
`conda run`; CUDA required with tests failing closed and no CPU fallback; the
16-environment width; the git prohibition; active-line development with no
compatibility shims or deprecated aliases; the `.gitignore` bare `*.md` trap and
its negation remedy; working discipline; and honest reporting.

Working discipline is stated as a hard requirement, not advice: make the first
code edit within the first few tool calls; on an unanswered design question take
the smallest reasonable choice, record it and keep moving; a working
implementation with a noted simplification beats an unwritten perfect one.

Honest reporting is likewise mandatory: paste real command output, never claim
tests pass without it, and state plainly what could not be done.

Per-agent definitions add only their role: the implementer's mandatory
pre-return inspection and its duty to flag rather than proceed when a task
appears to touch protected semantics; the reviewer's verdict format and its
standing instruction that passing tests are not the question; the scout's hard
boundary away from algorithm mechanisms, training, reward, optimizer, collector,
credit and numerical code; the monitor's `PROGRESS.md` contract with no chat
updates mid-run and no interpretation of scientific results.

Briefs continue to carry the spec pointer, file scope, what to build, required
tests, the explicit out-of-scope list, and facts already verified that the agent
must not re-derive.

No definition pins a test count. That number changes every task and would rot
into a false statement; it belongs in the brief.

## Git guard

Permission deny rules in `.claude/settings.json` are session-wide and cannot be
scoped to a subagent, so they would block the orchestrator's own commits. The
per-agent mechanism is a `PreToolUse` hook in the implementer definition that
rejects `git add`, `commit`, `push`, `stash` and `reset`. `disallowedTools: Bash`
is not an option because the implementer needs Bash to run the suite.

The instruction stays in the definition as well; the hook makes it enforced
rather than trusted.

## Repository requirement

The repository `.gitignore` ignores `*.md` globally with per-directory
negations. Both `.claude/agents/**/*.md` and `docs/superpowers/specs/*.md` need
negations or the files silently refuse to stage. Add the negation rather than
using `git add -f`, so the next file in those directories is not refused either.

## Deferred

Reasoning effort for the orchestrator is unchanged. No repo-wide permission
rules are added. Agent definitions for research review are not created, because
external scientific review is dispatched by the user to GPT-5.6 Pro rather than
run as a subagent.
