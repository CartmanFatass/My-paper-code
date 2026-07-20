---
name: hmasd-review-exchange
description: Use only inside one registered persistent HMASD reviewer-exchange session when the active controller assigns exactly one Gemini divergent, Open-Pro divergent, or Convergent-Pro stage. It owns that reviewer's transport, exact raw capture, semantic quality note, heartbeat, and one direct callback to the controller; it never manages the round or another reviewer.
---

# HMASD Reviewer Exchange

## Entry Contract

Accept only:

```text
$hmasd-task-router
$hmasd-review-exchange

REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=<GEMINI_DIVERGENT|OPEN_DIVERGENT|CONVERGENT>
round=<id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
question=<round-relative question path>
raw=<round-relative raw path>
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
recovery_context=<optional prior error evidence or none>
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

The first two invocation lines are mandatory. A `role_skill=` field or Skill
path does not activate the current Skill in a long-lived Exchange session.

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

The assignment interface is narrow; transport and page inspection are wide.
Within the registered conversation, evidence boundary and read-only authority,
choose the inspection strategy that best fits the live surface. Diagnose
mismatches semantically, revise failed locators or page assumptions, and try
reasonable safe alternatives before reporting a blocker. No selector, DOM
hierarchy, click sequence or fixed page algorithm is part of this contract.

Verify `stage_commit` and the assigned question are remotely visible before any
Pro submission. Submit the neutral handoff exactly once. The handoff is a
current-stage freshness fence, not a scientific prompt assembled by the
Exchange:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=<round>
stage_commit=<stage_commit>
question=<question>
instruction=Ignore every earlier round, SHA and question path in this conversation. Use only this assignment. Read the assigned question; it contains the complete role and scientific instructions. If the GitHub connector resolves any other ref, repeat the lookup with stage_commit before answering.
```

Do not append generic full-round requests, candidate weighting, route selection,
result-JSON requirements or rescue prohibitions to this handoff. Those belong
only to the assigned question. This is especially important for a focused
Convergent follow-up, which must not inherit the preceding full-round request or
an earlier commit from the persistent external conversation. After submission,
require the visible user turn to contain the exact current `round`,
`stage_commit` and `question`. If the matching question is already accepted,
never resubmit it.

For Pro, control only this Exchange session's registered reviewer conversation
and verify its exact URL and visible `Pro` before submission or capture. Reuse
the live page when available and keep it available while the stage is pending;
avoid needless duplicate tabs or reloads. How the page is found, claimed,
inspected, released between wakes and recovered is model judgment. Never use an
unrelated ambient page or operate another reviewer's conversation.

For Gemini, use only the registered Antigravity conversation and allowlisted
manifest. The tracked launch path retains `--dangerously-skip-permissions` under
the user's standing approval. Diagnose and recover transport problems inside
that registered state and evidence boundary; do not request duplicate consent,
substitute a conversation, expand evidence access or disguise the launch behind
an untracked wrapper.

Treat transport as complete when the current assigned external response has
naturally stopped generating and its text is stable. Write every naturally
completed response to the assigned raw, reread it, and require exact text
equality with the capture. Never discard completed evidence because a heading,
field or recommendation is missing.

If a completed Pro response states that it inspected a different commit or
question path than the current freshness fence, archive it exactly and report
`COMPLETE_WITH_GAPS` with the mismatched ref. It is completed transport but has
no adoptable scientific authority. The controller may assign one corrected
stage; the Exchange must not silently reinterpret the response or reuse the
stale ref.

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

On a Pro page, keep identity strict and inspection flexible. Associate the
answer with the current `round`, `stage_commit` and question using whatever
read-only evidence is reliable on the live surface. Revise failed assumptions
and inspect alternative representations before blocking. A stale locator, DOM
ambiguity or layout change is not evidence that Pro failed to answer. Do not use
response controls or resubmit the question as a discovery method.

Use model judgment to distinguish active generation, incomplete output and a
stable completed answer. `WAIT_PRO_THINKING` is appropriate only when current
page evidence supports continued generation or changing output. A stable answer
associated with the current assignment must be archived and returned as
`REVIEW_STAGE_COMPLETE`, using `COMPLETE_WITH_GAPS` for content limitations.
DOM ambiguity alone is not a transport failure.

Create or retain this stage's heartbeat while the response is pending and leave
the registered page available for the next wake. Send `REVIEW_STAGE_BLOCKED`
only for a diagnosed operational or transport boundary, not ordinary deferred
thinking, content quality or one failed inspection method.

When an error occurs, describe the observed evidence, likely semantic cause and
remaining boundary instead of requesting mechanical instructions. On a retry,
reread both explicitly invoked Skills and use `recovery_context` only as
evidence. Choose the recovery method here; do not require the controller to
supply selectors, browser commands or Antigravity steps. If the failure exposes
a reusable role-contract weakness, include the smallest Skill improvement
recommendation in `reason`; the controller owns that protected edit.

## Heartbeat

After the external question is visibly accepted, create one 5-minute heartbeat
targeted to this Exchange session. Its minimal prompt explicitly invokes both
current Skills and includes only the role directory, reviewer registry,
assignment and heartbeat ID. Each wake performs one bounded inspection and ends.
Do not sleep, poll continuously, resubmit, create a second heartbeat or send
waiting messages to the controller. Preserve the same external page across
wakes when possible; page-control mechanics are not part of the contract.

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

After all three terminal facts exist, release or close the owned external page.
If final page cleanup fails, do not repeat the review, raw write, callback or
heartbeat deletion.

## Reply to Controller

Take the destination only from
`session-roles.json.roles.controller.thread_id`. Resolve it live immediately
before the send and copy its current `hostId`, `threadId`, `model`, and
`thinking` unchanged into the delivery call.

On success send exactly:

```text
$hmasd-task-router

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
$hmasd-task-router

REVIEW_STAGE_BLOCKED
role=<reviewer_role>
handoff_id=<round>:<reviewer_role>:blocked:<stable-code>
round=<id>
reason=<direct blocker>
```

Delivery succeeds only when the send tool returns the registered controller
`threadId`. A local final response is not delivery. Never send either payload
to another persistent session.
