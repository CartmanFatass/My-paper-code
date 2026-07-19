---
name: hmasd-review-exchange
description: Use only inside one registered persistent HMASD reviewer-exchange session when the active controller assigns exactly one Gemini divergent, Open-Pro divergent, or Convergent-Pro stage. It owns that reviewer's transport, raw capture, completion validation, heartbeat, and one direct callback to the controller; it never manages the round or another reviewer.
---

# HMASD Reviewer Exchange

## Entry Contract

Accept only:

```text
REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=<GEMINI_DIVERGENT|OPEN_DIVERGENT|CONVERGENT>
round=<id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
question=<round-relative question path>
raw=<round-relative raw path>
```

Read, in order:

1. `../hmasd-task-router/SKILL.md`;
2. `../hmasd-task-router/references/session-roles.json`;
3. this Skill;
4. `docs/external-review/REVIEWER_CONVERSATIONS.json`;
5. the assigned question and only its stage-allowed manifest inputs.

Map `reviewer_role` to exactly one role-directory entry:

- `GEMINI_DIVERGENT` -> `gemini_divergent_exchange`;
- `OPEN_DIVERGENT` -> `open_divergent_exchange`;
- `CONVERGENT` -> `convergent_exchange`.

Require the current Codex task ID, assignment role, assignment `role_skill`,
registered external conversation, question filename, and raw filename all to
match that entry and `REVIEWER_CONVERSATIONS.json`. Otherwise return
`REVIEW_STAGE_BLOCKED` to the registered controller before opening a transport
or creating a heartbeat.

## Role Firewall

Own only the assigned external conversation, assigned question, assigned raw
file, and this session's stage heartbeat. Do not write questions,
reconciliation, disposition, Git, project control, code, experiments, or
another reviewer's files. Do not create or replace an external conversation,
change any task or reviewer model, rank routes, interpret the result, or
dispatch another role. Contact only the controller through
`$hmasd-task-router`; never contact another Exchange or the Code Manager.

Stage evidence is isolated:

- Gemini reads the shared and Gemini-local manifests named by its question;
- Open Pro reads only its Git-visible shared evidence and never sees Gemini raw
  or reconciliation;
- Convergent Pro reads only the two verified divergent raws, factual
  reconciliation, its question, and files explicitly listed there.

## Execute One Stage

Verify `stage_commit` and the assigned question are remotely visible before any
Pro submission. Submit the neutral handoff exactly once. If the matching
question is already accepted, never resubmit it.

Before every Pro browser operation, call
`codex_app__navigate_to_codex_page` with this Exchange session's registered task
ID, then verify the exact registered reviewer URL and visible `Pro`. Never use
ambient browser state or operate another reviewer page.

For Gemini, use only the registered Antigravity conversation and allowlisted
manifest. The two tracked Gemini launch scripts permanently include
`--dangerously-skip-permissions` under the user's explicit standing approval;
retain plan mode, sandbox mode, the registered conversation, and the manifest
evidence boundary. If the direct registered command fails only because the
Antigravity state root is not writable and standing consent is `APPROVED`, retry
that exact command once with escalation restricted to that state root. Do not
request duplicate consent, use a wrapper, or choose an alternate state path. A
second transport failure is terminal.

Treat a response as complete only when the external surface shows natural
completion and every section or decision field explicitly required by the
question at the assigned `stage_commit` is present. Derive requirements from
that committed question text only; never add a field from conversation memory,
an earlier working-tree version, or another round. Write the exact captured response to the assigned raw,
reread it, and require exact text equality with the capture. Nonempty is not
sufficient. For an existing raw, inspect this session's registered external
conversation once and repeat the same completion and equality checks before
reporting success.

For Gemini recovery, validate an existing raw against the current pinned
question before considering another external submission. If that raw satisfies
the current required fields and equals the completed registered-conversation
response, send the completion callback without resubmitting or overwriting it,
regardless of an earlier blocked callback or a later wording-only question
change. Resubmit only when the controller explicitly assigns materially changed
review content and the existing raw does not satisfy it.

On a Pro page, the visible deferred action `立即回答` means the request was
accepted and Pro is still working. It is a waiting state, never a transport
failure and never permission to click the control. Create or retain this
stage's heartbeat, close the bounded inspection, and let the next heartbeat
reopen the registered page. Send `REVIEW_STAGE_BLOCKED` only for a direct
terminal transport error, not for ordinary deferred Pro thinking.

## Heartbeat

Immediately after the external question is visibly accepted, create one
5-minute heartbeat targeted to this Exchange session. Capture its ID and update
that same heartbeat with a minimal prompt containing only the router Skill,
role directory, this Skill, reviewer registry, assignment fields, and heartbeat
ID. Each wake performs one bounded inspection and ends. Do not sleep, poll,
resubmit, create a second heartbeat, or send waiting messages.

Keep the heartbeat active through raw validation and controller callback.
Delete and verify deletion only after the callback tool confirms the registered
controller task. If callback delivery fails, the next wake retries only the
same `handoff_id`. If deletion alone fails, retry deletion without repeating
review work.

## Reply to Controller

Take the destination only from
`session-roles.json.roles.controller.thread_id`. Resolve it live immediately
before the send and copy its current `hostId`, `threadId`, `model`, and
`thinking` unchanged into the delivery call.

On success send exactly:

```text
REVIEW_STAGE_COMPLETE
role=<reviewer_role>
handoff_id=<round>:<reviewer_role>:complete:<question>
round=<id>
stage_commit=<pushed SHA>
raw=<round_path>/<raw>
verification=natural_complete;required_fields_present;exact_text_equal
```

On terminal transport failure send exactly:

```text
REVIEW_STAGE_BLOCKED
role=<reviewer_role>
handoff_id=<round>:<reviewer_role>:blocked:<stable-code>
round=<id>
reason=<direct blocker>
```

Delivery succeeds only when the send tool returns the registered controller
`threadId`. A local final response is not delivery. Never send either payload
to another persistent session.
