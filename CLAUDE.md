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
| `hmasd-review-exchanger` | sonnet / medium | byte-exact external review transport and archival |
| `hmasd-exp-recorder` | haiku / low | transcribes a classified run into `ExpRecord.md` |
| `hmasd-experiment-operator` | haiku / low | one authorized `train -> evaluate -> analyze` run |
| `hmasd-doc-auditor` | fable / high | adversarial audit of the governance surface itself |
| `hmasd-frontier-implementer` | opus / high | **test role** — the treatment arm measuring whether implementation here needs a frontier tier; instructions byte-identical to `hmasd-implementer`. Protocol and retirement condition: `docs/project/IMPLEMENTER_TIER_TEST.md`. Never the default implementer. |

Tier follows the work, not importance: judgment about protected semantics goes
to opus, bounded construction and design mapping to sonnet, and mechanical
lookup, transcription and execution to haiku. A haiku child that meets a real
judgment call hands back rather than deciding.

Effort is set separately from model. A role whose work includes deciding whether
an observation matches a declared contract carries that judgment even when its
title sounds mechanical, and is tiered for the judgment — `hmasd-verifier` and
`hmasd-review-exchanger` are both raised above their apparent class for exactly
that reason. When enumerating rules keeps failing to cover the cases, a role
needs a model that can infer them, not another rule. Each definition states its
own reason in a comment; the case history is in
`docs/project/REVIEW_TRANSPORT_AUDIT_20260724.md`.

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
