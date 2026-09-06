---
name: hmasd-workflow-outsource
description: Use only when the user explicitly requests outsourcing or delegation of an HMASD workflow or control-plane change to one native Terra/high subagent with a bounded implementation contract, reusing that agent for same-task follow-ups.
---

# HMASD Workflow Outsource

## Mission

Delegate one bounded workflow/control-plane change to one native subagent. An
initial contract creates exactly one `gpt-5.6-terra` subagent with `high` reasoning
effort in the current workspace; it is not a fixed Codex session and is not a
user-visible `create_thread` task. That agent owns the complete edit and verification
lifecycle, then returns `OUTSOURCE_RESULT v1` to its caller.

A follow-up that carries the same `REQUEST_ID` or `TASK_IDENTITY` is the same task:
recover its original returned agent handle from the dispatch receipt and reuse that
agent. Create a replacement Terra/high agent only when the original handle cannot be
recovered or is unavailable. Record the concrete replacement reason in the new
receipt; never silently fan out, duplicate, or replace an agent merely because it is
busy.

## Trigger and boundary

Trigger only when the user explicitly names `$hmasd-workflow-outsource` or explicitly
requests outsourcing or delegation of a workflow/control-plane change or audit involving
`AGENTS.md`, `.agents/skills`, `.agents/roles`, `.codex/agents`, dispatch, session
routing, transport, permissions, or task lifecycle. Otherwise, the current agent
handles ordinary workflow/control-plane work directly.

When explicitly invoked, the caller must not edit workflow files or fan out work
before delegation. One contract means one agent and one objective. A same-task
follow-up may refine that bounded contract but must retain its task identity and
ownership. The default is zero nested agents; the assigned agent may create one only
when the contract explicitly authorizes that subtask.

## Dispatch procedure

1. Freeze exactly one objective, repository/worktree, baseline, Git destination,
   owned paths, allowed effects, deliverables, acceptance checks, verification
   commands, and stop conditions. Preserve user wording and do not add scientific,
   portfolio, experiment, or external transport work.
2. Fill contract facts from the request, existing authorization and repository state.
   Resolve routine implementation choices locally and state material assumptions. If
   an essential scope, scientific meaning, destination or external-effect authorization
   remains unknown, ask one focused question and pause only the dependent work.
   Multiple requested changes may form one bounded objective; do not add unrelated work.
3. Read [references/prompt-template.md](references/prompt-template.md), fill every
   field, and classify the dispatch as `INITIAL`, `FOLLOW_UP_REUSE`, or
   `REPLACEMENT`.
4. For `INITIAL`, create exactly one agent with `spawn_agent`, using
   `agent_type=default`, `model=gpt-5.6-terra`, `reasoning_effort=high`, and
   `fork_turns=none`. Give it a unique lowercase task name such as
   `workflow_th_<request_id_slug>`, send the self-contained contract as its initial
   message, and record the returned agent handle in the dispatch receipt. Do not use
   `create_thread`, a fixed target UUID, or `send_message_to_thread` for dispatch.
   If creation is uncertain, return `DISPATCH_UNCERTAIN`; do not create another
   agent.
5. For `FOLLOW_UP_REUSE`, resolve the original handle from that task's dispatch
   receipt and use `followup_task` with the same `REQUEST_ID` or `TASK_IDENTITY`.
   Do not call `spawn_agent`; a busy original agent receives the follow-up when it
   reaches a message boundary. If the handle cannot be resolved or the original agent
   is unavailable, classify the dispatch as `REPLACEMENT` rather than guessing.
6. For `REPLACEMENT`, record the original handle (if known) and a concrete
   `replacement_reason` showing why recovery failed or the agent is unavailable.
   Create exactly one replacement using the same Terra/high `spawn_agent` settings.
   Give it the original bounded contract, its stable task identity, and the follow-up
   context. Do not create a replacement for a busy agent or retry an uncertain
   creation.
7. Wait for the assigned agent's final result. Accept completion only after it
   supplies `OUTSOURCE_RESULT v1` and evidence for every acceptance item. The caller
   never duplicates the implementation or repairs the agent's work in place.

## Required result states

Use one of: `DISPATCHED`, `WAITING`, `COMPLETED`, `BLOCKED_INPUT`,
`DISPATCH_UNCERTAIN`, or `REJECTED_SCOPE`. A completed result includes changed paths,
exact commands and outputs, an acceptance matrix, assumptions, blockers, and Git
facts. Missing evidence is incomplete, not success.

AMA is one bounded question for an essential fact that cannot be recovered from context.
Ordinary in-scope verification failures are repaired by the assigned agent until the
contract is met or a concrete blocker remains. They do not automatically end the task.
Existing experiment budgets and uncertain external-effect boundaries still apply.

## Red flags

- creating a second agent for a recoverable same-task follow-up;
- creating a user-visible task instead of one native Terra/high subagent;
- adding another objective, role/skill, experiment, or parallel branch;
- modifying an unlisted path or changing scientific meaning, permissions, or external effects;
- retrying an uncertain agent creation, omitting a replacement reason, or claiming
  unverified agent output.

See the reference for the canonical contract and return receipt.
