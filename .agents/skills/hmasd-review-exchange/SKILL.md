---
name: hmasd-review-exchange
description: Use only inside one registered persistent HMASD reviewer-exchange session when the active controller assigns exactly one Gemini divergent, Open-Pro divergent, or Convergent-Pro stage. It owns that reviewer's transport, exact raw capture, semantic quality note, heartbeat, and one direct callback to the controller; it never manages the round or another reviewer.
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
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
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

Require the literal `completion_policy` value above. It is the only
content-lifecycle rule carried across the persistent-session boundary: archive
every naturally completed response and report quality separately. It does not
prescribe headings, fields, reasoning or scientific judgment.

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

Before the initial Pro transport, call `codex_app__navigate_to_codex_page` once
with this Exchange session's registered task ID, then verify the exact
registered reviewer URL and visible `Pro`. Keep that owned page open for the
whole assigned stage. At the start of every later inspection, first reuse a
matching controlled tab from `browser.tabs.list()`. Otherwise inspect
`browser.user.openTabs()` and pass the exact matching registered-URL object to
`browser.user.claimTab(...)`. Do not create a duplicate tab when that user tab
exists, and do not call `goto` when the claimed tab is already on the registered
URL. Only if neither surface contains the registered page may the Exchange open
it once as recovery. Never use an unrelated ambient tab or operate another
reviewer page; ambient browser state is not assignment authority.

For Gemini, use only the registered Antigravity conversation and allowlisted
manifest. The two tracked Gemini launch scripts permanently include
`--dangerously-skip-permissions` under the user's explicit standing approval;
retain plan mode, sandbox mode, the registered conversation, and the manifest
evidence boundary. If the direct registered command fails only because the
Antigravity state root is not writable and standing consent is `APPROVED`, retry
that exact command once with escalation restricted to that state root. Do not
request duplicate consent, use a wrapper, or choose an alternate state path. A
second transport failure is terminal.

Treat transport as complete when the current assigned external response has
naturally stopped generating and its text is stable. Write every naturally
completed response to the assigned raw, reread it, and require exact text
equality with the capture. Never discard completed evidence because a heading,
field or recommendation is missing.

After archival, read the assigned question and response semantically. Report a
short `quality` and `quality_notes` to the controller. Use model judgment rather
than heading-string equality, regular expressions or a checklist implemented in
page code. `COMPLETE_WITH_GAPS` means transport succeeded but the response may
need a controller-authorized follow-up; it is not a transport failure and this
Exchange does not decide scientific adoption.

For an existing raw, inspect this session's registered external conversation
once and repeat only the natural-completion and exact-equality checks before
reporting success.

Never use a prior turn, another round, a compacted-context summary, local final
text, or a heartbeat message as evidence that the current stage completed. If
context compaction occurs during a bounded inspection, discard every
unconfirmed terminal assumption and restart the next wake from the current
assignment fields and filesystem. In particular, a missing assigned raw means
the current stage is not archived, regardless of what earlier text claims.

For Gemini recovery, compare an existing raw with the completed registered
conversation response before considering another external submission. If it is
equal, send the completion callback without resubmitting or overwriting it.
Resubmit only when the controller explicitly assigns materially changed review
content.

On a Pro page, determine state from the current assigned turn only. Locate the
user turn containing this stage's exact round and commit, then inspect only its
following assistant response container and current-generation indicator.
Controls inside historical turns, page navigation, a prior response, or another
conversation section are irrelevant. Never scan all page buttons and treat any
matching label as current-stage state.

Use message-role containers, not positional page sections: locate the matching
`[data-message-author-role="user"]` (or its enclosing conversation-turn
article), then select the first later
`[data-message-author-role="assistant"]`. Do not use
`document.querySelectorAll('section')` plus `idx+1`; ChatGPT page sections are
not a stable one-message-per-section contract. Scope text and controls to that
assistant element's enclosing conversation-turn article.

A current-turn `停止回答` or deferred `立即回答` means the request was accepted
and Pro is still working. It is a waiting state, never a transport failure and
never permission to click the control. `重新生成` on a stable completed current
response is a completion affordance, not a thinking signal; it must not block
archival. A `继续` control associated with the current response means the answer
is incomplete and must not be clicked or archived. Do not decide from controls
alone: natural completion requires stable current-response text and no
current-turn active or deferred generation indicator.

`WAIT_PRO_THINKING` is legal only when the current assigned turn has an active
or deferred generation indicator, or when two bounded reads in the same wake
show that its assistant text is still changing. If the current response is
naturally complete and stable, archive it and return `REVIEW_STAGE_COMPLETE`,
using `COMPLETE_WITH_GAPS` when semantic review finds a material omission. A
completed response must never remain in `WAIT` or become
`REVIEW_STAGE_BLOCKED` because of content quality.

Create or retain this stage's heartbeat while the current turn is pending. As
the final browser action of that waiting turn, call
`browser.tabs.finalize({ keep: [{ tab: <owned-tab>, status: "handoff" }] })`.
This releases automation control while preserving the live page for the next
heartbeat; it is not a close. Do not call another browser operation after
finalize. Send `REVIEW_STAGE_BLOCKED` only for a direct operational or transport
error, not for ordinary deferred Pro thinking or content quality.

## Heartbeat

Immediately after the external question is visibly accepted, create one
5-minute heartbeat targeted to this Exchange session. Capture its ID and update
that same heartbeat with a minimal prompt containing only the router Skill,
role directory, this Skill, reviewer registry, assignment fields, and heartbeat
ID. Each wake performs one bounded inspection and ends. Do not sleep, poll,
resubmit, create a second heartbeat, send waiting messages, or close and reopen
the owned Pro page. A pending wake must finalize the owned page with
`status: "handoff"` before ending, and the next wake must claim that page rather
than create a replacement.

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

After all three terminal facts exist, close the owned Pro page or finalize it
without a keep entry exactly once. This is the only normal close point for the
stage. Do not reopen it after terminal cleanup. If final page cleanup fails, do
not repeat the review, raw write, callback, or heartbeat deletion.

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
verification=natural_complete;exact_text_equal
quality=<COMPLETE|COMPLETE_WITH_GAPS>
quality_notes=<concise semantic observation or none>
```

On terminal operational or transport failure send exactly:

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
