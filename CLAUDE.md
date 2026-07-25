# HMASD Claude Code Entry

Claude Code runtime facts live here: which subagents exist, what tier each runs
at, and how to orchestrate tools. Project authority — science, acceptance, Git,
protected semantics — lives in `AGENTS.md` and `.agents/roles/`. Neither file
duplicates the other.

Read `AGENTS.md` first, then only the role charter, agent definition, or
document your task actually names.

## Routing

Project Manager work uses the active files in `docs/project/`. Every bounded role is
a subagent below. Implementation procedure is
`$hmasd-agile-research-development`; external review transport is
`$hmasd-review-round`.

If `CURRENT_WORK.md` names another active Project Manager, remain read-only unless an
explicit handoff changes ownership. Git-tracked code is the implementation
source and `logs/<run-id>/` is runtime evidence. Historical modules, commands,
rounds and archived artifacts are not active instructions.

## The loop does not stop

Runtime mechanism only. Authorization semantics — what is granted, where a mode
pauses, what must still be escalated — live in `AGENTS.md`, **Standing
authorization** and **Execution modes**. Read them once per session; do not
restate them here.

The mechanism matters because intent alone has already failed. `AGENTS.md` said
the loop continues automatically, and it still stalled repeatedly, because a turn
ends when the orchestrator stops emitting tool calls and **no sentence in any
document re-invokes it**.

```text
loop_driver=/loop          # dynamic pacing, ScheduleWakeup
primary_wake=task notifications from background children
fallback_wake=/loop wakeup, for the gap notifications cannot cover
```

Four rules, all mechanical:

1. **A turn ending is not the loop ending.** Before the last tool call of a turn,
   confirm a driver is attached. If nothing is in flight and the next step is
   yours to start, that is the stall gap — arm the wakeup.
2. **Compaction never pauses it.** Write the handoff, compact, resume straight
   into the next iteration. Nothing waits for an answer at that seam.
3. **Compute is a script, not a question.** `scripts/check_compute_free.ps1`.
   `COMPUTE_BUSY` schedules a one-hour recheck; it never returns to the user.
4. **Waiting is done in-band.** No blocking sleep exists, so a child that ends its
   turn to wait has stalled. Poll with repeated checks inside the turn, or hand
   back. A prohibition without an affordance is unfollowable.

The driver is session-bound and does not survive session death.
`CURRENT_WORK.md` does, and records whether one is attached — the boundary is the
continuity record, not the driver.

## Retiring a direction

Research code iterates fast and most directions die. A direction verified as
hopeless gets **the scientific record of its failure and nothing else** — what
was tried, what it returned, why it is dead. That is enough to stop the mistake
recurring years later, and it is the only part worth carrying.

Do not maintain long documents for abandoned work, and do not narrate a
retirement in a document, a commit message or a reply. Retired material competes
for attention with live material on every read. Replace the body with a pointer;
keep the failure, drop the apparatus.

## Registered subagents

Default tiers for a **new** role, by class. The table below is authoritative per
agent and several deliberately sit above their class.

```text
subagent_runtime=claude_code
subagent_definitions=.claude/agents/*.md
implementer_tier=sonnet_high
reviewer_tier=opus_high
mechanical_tier=haiku_low
```

Each definition in `.claude/agents/<name>.md` carries its own model, effort and
tool grant, and supplies the standing boundary. The Project Manager spawns one
with an exact assignment.

| Subagent | Tier | Owns |
|---|---|---|
| `hmasd-implementer` | sonnet / high | one bounded frozen implementation task |
| `hmasd-reviewer` | opus / high | adversarial read-only audit of one diff |
| `hmasd-scout` | haiku / low | mechanical lookup — inventories, symbol sweeps, locations |
| `hmasd-code-scout` | sonnet / medium | design map — coupling, writer partitions, real vs accidental dependency |
| `hmasd-verifier` | haiku / high | executes assigned checks, returns bounded runtime evidence |
| `hmasd-patcher` | haiku / low | applies pre-decided exact file edits |
| `hmasd-monitor` | haiku / low | maintains `PROGRESS.md` under one run root |
| `hmasd-review-monitor` | haiku / low | reports when the external reviewer has finished generating; no send, capture or archive |
| `hmasd-exp-recorder` | haiku / low | transcribes a classified run into `ExpRecord.md` |
| `hmasd-experiment-operator` | haiku / low | one authorized `train -> evaluate -> analyze` run |
| `hmasd-doc-auditor` | fable / high | adversarial audit of the governance surface itself |

Tier follows the work, not importance: judgment about protected semantics goes
to opus, bounded construction and design mapping to sonnet, and mechanical
lookup, transcription and execution to haiku. A haiku child that meets a real
judgment call hands back rather than deciding.

Effort is set separately from model. A role whose work includes deciding whether
an observation matches a declared contract carries that judgment even when its
title sounds mechanical, and is tiered for the judgment — `hmasd-verifier` is
raised above its apparent class for exactly that reason. The converse also
applies: when the judgment is removed from a role rather than merely simplified,
the tier drops with it, which is why `hmasd-review-monitor` sits at haiku/low
after transport moved to the Project Manager. Each definition states its own
reason in a comment.

Every definition points at `docs/project/AGENT_CONTEXT.md`, whose **Unattended
operation** and **Reporting honestly** sections bind all children. Standing
constraints belong there rather than in each brief.

Claude Code has no per-agent approval policy. A definition can withhold a tool,
and a `PreToolUse` hook can block a command, but "never ask for approval" is a
session-level setting the roster cannot express.

No child commits, spawns a successor, or accepts its own work. An unknown
`agent_type` is a blocker — never substitute a default or ad hoc worker.

## Tool batching

Issue already-known, independent tool calls together in one message so they run
concurrently — read-only inspections especially. Inspect every result; one
failed call does not invalidate the others returned alongside it.

Keep sequential: dependencies, waits or resumes, approval-sensitive calls,
conflicting or interdependent mutations, and adaptive investigations whose next
step depends on the previous result. Do not batch merely to expand scope, and do
not split otherwise batchable read-only inspections across separate messages.

This governs tool orchestration only. It does not relax file ownership, compute
authority, or protected scientific semantics.
