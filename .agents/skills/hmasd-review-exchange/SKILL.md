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

- Gemini reads the shared and Gemini-local manifests named by its question plus
  `ALGORITHM_PRINCIPLES.md` and `OPEN_REVIEW_PRINCIPLES.md`;
- Open Pro reads only its Git-visible shared evidence plus those same two
  principle files and never sees Gemini raw or reconciliation;
- Convergent Pro reads only the two verified divergent raws, factual
  reconciliation, its question, explicitly listed evidence,
  `ALGORITHM_PRINCIPLES.md`, and `CONVERGENT_REVIEW_PRINCIPLES.md`.

Before transport, require the assigned question to list the matching principle
file exactly. Reject an open question that lists the convergent principle, a
convergent question that lists the open principle, or any stage that omits the
base algorithm principles. Return `REVIEW_STAGE_BLOCKED` without opening the
external transport when this binding is invalid.

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

Never use a prior turn, another round, a compacted-context summary, local final
text, or a heartbeat message as evidence that the current stage completed. If
context compaction occurs during a bounded inspection, discard every
unconfirmed terminal assumption and restart the next wake from the current
assignment fields and filesystem. In particular, a missing assigned raw means
the current stage is not archived, regardless of what earlier text claims.

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

### Terminal evidence rule

A terminal success requires three separate tool-level facts for the current
round and current `handoff_id`:

1. the assigned raw exists and the current wake has verified exact equality
   with the naturally completed external response;
2. `codex_app__send_message_to_thread` returned the registered controller task
   ID for the exact `REVIEW_STAGE_COMPLETE` payload;
3. `codex_app__automation_update` deleted this assignment's exact
   `heartbeat_id`, and a follow-up view confirms that it is no longer active.

Text saying that a callback or deletion happened is never evidence. Do not
emit `DONT_NOTIFY`, `heartbeat_deleted`, `controller confirmed`, or any local
terminal-success wording unless all three facts were produced for this stage.
If any fact is missing, keep the heartbeat active and end the bounded wake
without a terminal claim. After the callback succeeds but deletion fails, the
next wake performs deletion only and must not send the callback again.

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
