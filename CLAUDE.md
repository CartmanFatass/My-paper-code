# HMASD Claude Code Entry

**This file is a signpost.** It is loaded into every context, so it stores only
what every reader needs and routes everything else. Content that one role needs
lives in that role's file, not here.

Project authority — science, acceptance, Git, protected semantics — lives in
`AGENTS.md` and `.agents/roles/`. Runtime facts live here. Neither duplicates the
other.

## Who reads what

| You are | Read, in order |
|---|---|
| **Main-conversation orchestrator** (Project Manager) | `AGENTS.md`, then `docs/project/CURRENT_WORK.md` |
| **Any subagent** | your own `.claude/agents/<name>.md`, then `docs/project/AGENT_CONTEXT.md` — its **Unattended operation** and **Reporting honestly** sections bind you |
| **Implementing** | `$hmasd-agile-research-development` |
| **Running an external review round** | `$hmasd-review-round` |
| **Judging whether work is on path** | `docs/project/RESEARCH_GOAL.md` |
| **Designing evidence or freezing a contract** | `docs/project/ALGORITHM_PRINCIPLES.md`, then `docs/project/EVIDENCE_COMPLEXITY_POLICY.md` |

Then read only the charter, definition or document your task actually names.
Git-tracked code is the implementation source; `logs/<run-id>/` is runtime
evidence. Historical modules, commands, rounds and archived artifacts are not
active instructions.

If `CURRENT_WORK.md` names another active Project Manager, remain read-only
unless an explicit handoff changes ownership.

## The loop does not stop

Orchestrator-facing, except rule 4. Authorization semantics — what is granted,
where a mode pauses, what must still be escalated — are in `AGENTS.md`,
**Standing authorization** and **Execution modes**.

Mechanism is here because intent alone already failed: `AGENTS.md` said the loop
continues automatically and it still stalled, because a turn ends when the
orchestrator stops emitting tool calls and **no sentence in any document
re-invokes it**.

```text
loop_driver=/goal          # preferred -- blocks the stop until the condition holds
loop_driver_alt=/loop      # dynamic pacing, ScheduleWakeup
primary_wake=task notifications from background children
fallback_wake=the attached driver, for the gap notifications cannot cover
```

**Prefer `/goal`** (user ruling 2026-07-27). The two drivers fail in opposite
directions, and only one of them fails safe. `/loop` *schedules* a return: if the
wakeup is never armed, or is armed for the wrong horizon, the loop is simply
gone and nothing reports that it went. `/goal` *withholds* the stop until its
condition holds, so the failure mode is a turn that will not end rather than a
loop that quietly died — and a stall that announces itself is recoverable in a
way that a silent one is not. It also states the terminating condition, which
`/loop` never did; "keep going" has no completion test, and neither did we.

Either way the driver is session-bound. Overnight autonomy is a scheduled
`claude -p` and nothing else.

1. **The loop is a backstop, not a scheduler.** It exists to cover an *empty
   gap* — no work in hand, nothing in flight, nothing to answer. If there is a
   next step and it is yours, **take it now**; deferring ready work to a wakeup
   is the failure this mechanism was built to prevent, not an instance of it.
   Arm the wakeup only when the turn would otherwise end with the loop dead and
   nothing left to do.

   A turn ending is still not the loop ending: check before the last tool call
   that either work is in flight or a driver is attached.
2. **Compaction never pauses it.** Handoff, compact, resume into the next
   iteration. Nothing waits for an answer at that seam.
3. **Compute is a script, not a question.** `scripts/check_compute_free.ps1`.
   `COMPUTE_BUSY` schedules a one-hour recheck; it never returns to the user.
4. **Waiting is done in-band.** No blocking sleep exists, so ending a turn to
   wait is a stall. Poll inside the turn, or hand back. A prohibition without an
   affordance is unfollowable.

The driver is session-bound and dies with the session. `CURRENT_WORK.md` does
not, and records whether one is attached — the boundary is the continuity
record, not the driver.

## Retiring a direction

Research code iterates fast and most directions die. A direction verified as
hopeless gets **the scientific record of its failure and nothing else** — what
was tried, what it returned, why it is dead. That is enough to stop the mistake
recurring years later, and it is the only part worth carrying.

Do not maintain long documents for abandoned work, and do not narrate a
retirement in a document, a commit message or a reply. Retired material competes
for attention with live material on every read. Replace the body with a pointer;
keep the failure, drop the apparatus.

## Tool batching

Issue already-known, independent tool calls together in one message so they run
concurrently — read-only inspections especially. Inspect every result; one failed
call does not invalidate the others returned alongside it.

Keep sequential: dependencies, waits or resumes, approval-sensitive calls,
conflicting or interdependent mutations, and adaptive investigations whose next
step depends on the previous result. Do not batch merely to expand scope, and do
not split otherwise batchable read-only inspections across separate messages.

This governs tool orchestration only. It does not relax file ownership, compute
authority, or protected scientific semantics.

## Subagent runtime

```text
subagent_runtime=claude_code
subagent_definitions=.claude/agents/*.md
implementer_tier=sonnet_high
reviewer_tier=opus_high
mechanical_tier=haiku_low
general_purpose_tier=opus_high
```

An unregistered `general-purpose` spawn never inherits the orchestrator's own
model: pass `opus` explicitly, at high effort (user ruling 2026-07-26).

Those are defaults for a **new** role by class. Each definition carries its own
model, effort and tool grant and is the authority for that agent; several
deliberately sit above their class. No roster table is kept here — the Agent tool
already lists every registered agent and what it owns, and a second copy only
drifts.

Tier follows the work: judgment about protected semantics to opus, bounded
construction and design mapping to sonnet, mechanical lookup, transcription and
execution to haiku. Effort is set separately from model, and a role that decides
whether an observation matches a declared contract is tiered for that judgment
however mechanical its title sounds — which is why `hmasd-verifier` sits above its
class. The converse holds: when judgment is removed from a role rather than
simplified, the tier drops with it. Each definition states its own reason.

A haiku child that meets a real judgment call hands back rather than deciding.
No child commits, spawns a successor, or accepts its own work. An unknown
`agent_type` is a blocker — never substitute a default or ad hoc worker. One
authorized `train -> evaluate -> analyze` run belongs to `hmasd-experiment-operator`.

Claude Code has no per-agent approval policy. A definition can withhold a tool
and a `PreToolUse` hook can block a command, but "never ask for approval" is a
session-level setting the roster cannot express.
