---
name: hmasd-workflow-outsource
description: Use when an HMASD workflow, control-plane, role, skill, dispatch, session-routing, or AGENTS change must be outsourced or delegated to another Codex task.
---

# HMASD Workflow Outsource

## Mission

Make one bounded handoff to one named Codex task. The caller writes the contract and sends it
once; the destination task owns the implementation and returns evidence against the contract.
This skill is a routing boundary, not a second workflow designer.

Use the current destination requested by the user when they say "this session":

```text
DEFAULT_TARGET_THREAD_ID=01a04f5a-1c9f-7331-b1d9-249fb767362e
```

An explicit target ID in the current request overrides this value. Never infer a target from a
title, a model name, or a stale URL.

## Trigger and boundary

Trigger for workflow/control-plane changes or audits involving `AGENTS.md`, `.agents/skills`,
`.agents/roles`, `.codex/agents`, dispatch, session routing, transport, permissions, or task
lifecycle when the user wants the work handled by the designated session. Do not trigger for an
ordinary scientific question or implementation that does not change workflow behavior.

The caller must not edit workflow files, choose a second workflow owner, or fan out subagents
before dispatch. The destination may use a subagent only when the prompt explicitly lists that
subtask; the default is zero subagents and one serial task.

## Dispatch procedure

1. Freeze exactly one objective, the repository/worktree, baseline and Git destination, owned paths,
   allowed effects, deliverables, acceptance checks, verification commands, and stop conditions.
   Preserve user wording and facts;
   do not add research, portfolio, experiment, or transport work.
2. If any required slot is missing or the request contains multiple independent objectives, ask one
   blocking AMA question or return `BLOCKED_INPUT`; do not guess and do not send a vague prompt.
3. Read [references/prompt-template.md](references/prompt-template.md), fill every field, and keep
   the prompt self-contained. The prompt must tell the destination to return `OUTSOURCE_RESULT v1`
   and to stop on scope expansion.
4. If the source and target thread IDs are identical, return `BLOCKED_INPUT` rather than recurse.
   Otherwise call `send_message_to_thread` exactly once with the completed prompt and the target
   thread ID.
   If the target is already running, the message is queued; do not interrupt, duplicate, or create
   a replacement task. An uncertain send is `DISPATCH_UNCERTAIN`, not permission to retry.
5. Return a compact dispatch receipt. If execution was requested, use `wait_threads` for the same
   target; accept completion only after the destination supplies the result schema and every
   acceptance item is evidenced. The caller never repairs the destination's work in place.

## Quick reference

| State | Meaning | Caller action |
|---|---|---|
| `BLOCKED_INPUT` | Contract has a missing or ambiguous required slot | Ask one blocking AMA question; do not send |
| `DISPATCHED` | One prompt was accepted for delivery | Keep the same target; do not duplicate |
| `WAITING` | Target is still running or has not returned the schema | Wait or report the exact pending state |
| `COMPLETED` | Every acceptance item has evidence | Report the result; do not add work |
| `DISPATCH_UNCERTAIN` / `REJECTED_SCOPE` | Send or execution cannot be trusted | Preserve facts and escalate; do not retry or repair |

Minimal example: a request to update only `.codex/agents/hmasd-workflow-designer.toml` must name
that path, the baseline, one observable behavior, one test command, and `ALLOWED_EFFECTS=read/edit/test`.
It is not a request to audit all roles or add a new skill.

## Required result states

Use one of: `DISPATCHED`, `WAITING`, `COMPLETED`, `BLOCKED_INPUT`, `DISPATCH_UNCERTAIN`, or
`REJECTED_SCOPE`. A completed result must include changed paths, exact commands and outputs,
an acceptance matrix, assumptions, blockers, and Git facts. Missing evidence is incomplete, not
success.

AMA means bounded clarification only: at most one question for information that truly blocks the
contract. Do not turn AMA into an open-ended design interview.

## Red flags

- adding a second objective, new role/skill, experiment, or parallel branch;
- modifying an unlisted path or changing scientific meaning, permissions, or external effects;
- silently broadening "workflow" into a repository-wide audit;
- claiming tests, files, or commits that the destination did not evidence;
- retrying an uncertain send or creating another conversation.
- dispatching to the source thread itself (which would create a recursive handoff).

See the reference for the canonical prompt and return contract.
