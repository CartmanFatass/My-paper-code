---
name: hmasd-workflow-outsource
description: Use when an HMASD workflow, control-plane, role, skill, dispatch, session-routing, or AGENTS change must be outsourced or delegated to another Codex task.
---

# HMASD Workflow Outsource

## Mission

Make one bounded handoff to one explicitly identified Codex task. The caller writes the contract
and sends it once; the designated target task is the execution owner, performs the complete
implementation and verification in that task, and returns evidence against the contract. This
skill is a routing boundary, not a second workflow designer or an advice-only review route.

The designated outsource target is fixed:

```text
OUTSOURCE_TARGET_THREAD=codex://threads/01a058a7-a26c-77d3-b220-d621a615df79
```

Always send to that exact task, using UUID `01a058a7-a26c-77d3-b220-d621a615df79` in
`send_message_to_thread`. Do not infer, override, rediscover, or replace the target from a title,
model name, summary, role, or URL.

The target is responsible for the full lifecycle after acceptance: it edits only the contracted
paths, runs the contracted checks, and returns `OUTSOURCE_RESULT v1`. The caller must not duplicate
the implementation in another task, repair the target in place, or treat a queued handoff as a
completed result. If the current task is already the fixed target, execute the contract directly;
do not dispatch the task to itself or create a recursive replacement.

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
2. If any required contract slot is missing or the request contains multiple independent
   objectives, ask one blocking AMA question or return `BLOCKED_INPUT`; do not guess and do not
   send a vague prompt.
3. Read [references/prompt-template.md](references/prompt-template.md), fill every field, and keep
   the prompt self-contained. The prompt must tell the destination to return `OUTSOURCE_RESULT v1`
   and to stop on scope expansion.
4. Call `send_message_to_thread` exactly once with the completed prompt and the fixed target UUID
   `01a058a7-a26c-77d3-b220-d621a615df79`.
   If the target is already running, the message is queued; do not interrupt, duplicate, or create
   a replacement task. An uncertain send is `DISPATCH_UNCERTAIN`, not permission to retry.
5. Return a compact dispatch receipt. If execution was requested, use `wait_threads` for the same
   target; accept completion only after the destination supplies the result schema and every
   acceptance item is evidenced. The caller never repairs the destination's work in place; the
   destination remains the sole execution owner for the contracted task.

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

See the reference for the canonical prompt and return contract.
