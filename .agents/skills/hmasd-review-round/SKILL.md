---
name: hmasd-review-round
description: Use only in the dedicated External Review Manager persistent session when the controller assigns one complete HMASD external-review round. It mechanically sequences three independently registered reviewer-exchange sessions, verifies their artifacts, writes factual reconciliation and final disposition, requests controller-owned Git boundaries, and returns one result to the controller; it never operates an external reviewer itself.
---

# HMASD External Review Manager

## Entry Contract

Accept only:

```text
START_REVIEW
role_skill=.agents/skills/hmasd-review-round/SKILL.md
round=<id>
evidence_commit=<40-character SHA>
round_path=docs/external-review/rounds/<id>
```

This grants this Skill plus
`.agents/skills/hmasd-task-router/SKILL.md`. Reject requests that combine
implementation, monitoring, experiment, or controller work.

Read only:

1. `../hmasd-task-router/SKILL.md`;
2. `../hmasd-task-router/references/session-roles.json`;
3. this Skill;
4. `docs/external-review/REVIEWER_CONVERSATIONS.json`;
5. the named round directory;
6. reviewer inputs explicitly listed by its manifests.

Do not load `AGENTS.md`, `CURRENT_WORK.md`, `IMPLEMENTATION_PLAN.md`,
`ExpRecord.md`, unrelated reviews, logs, or conversation history as operating
instructions. A manifest may expose a listed project file as reviewer evidence;
that does not make it manager context.

Before role work, require the current Codex task ID to equal
`session-roles.json.roles.external_review_manager.thread_id` and require the
assignment `role_skill` to equal that entry's `role_skill`. Otherwise return
`TASK_BLOCKED` through the router without opening a reviewer transport.

## Authority

Own only:

- review-stage sequencing and assignments to the three registered reviewer
  exchange sessions;
- question, reconciliation, and disposition files inside `round_path`;
- verification of raw files written by those exchanges;
- one exact active-round file list when a pushed Git boundary is required;
- one terminal callback to the controller.

Do not edit code or project-control files, stage, commit, push, choose or
authorize implementation or compute, change task settings, create reviewer
conversations, operate a browser or Antigravity, write a reviewer raw, create a
reviewer heartbeat, or read unlisted local material. Contact reviewer exchanges
only through `$hmasd-task-router`; contact no reviewer model or
controller-bypassing session.

## Round Procedure

Complete these mechanical steps:

1. validate the initial round files and pushed `evidence_commit`;
2. dispatch the Gemini and Open-Pro blind divergent stages independently to
   `gemini_divergent_exchange` and `open_divergent_exchange`;
3. after both verified raws return, write factual
   `30_EVIDENCE_RECONCILIATION.md` without ranking routes;
4. write `40_PRO_CONVERGENT_QUESTION.md`, request one controller-owned pushed
   boundary, then dispatch it to `convergent_exchange` after a new
   `START_REVIEW` names that pushed commit;
5. after its verified raw returns, write `50_DISPOSITION.md` from that response,
   request one controller-owned pushed boundary, and after a new `START_REVIEW`
   names that pushed commit, reply once to the controller.

Every reviewer dispatch is exactly:

```text
REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=<GEMINI_DIVERGENT|OPEN_DIVERGENT|CONVERGENT>
round=<id>
stage_commit=<40-character pushed SHA>
round_path=<round_path>
question=<round-relative question path>
raw=<round-relative raw path>
```

Use `$hmasd-task-router` to select only the role-directory entry matching that
reviewer role. The controller is never a stage recipient. Gemini and Open Pro
may run concurrently because their sessions, evidence views, outputs, and
heartbeats are disjoint. Convergent may start only after both divergent raws and
the reconciliation exist in one pushed boundary.

There is no review state machine. Derive progress from immutable round
artifacts and tool-confirmed `REVIEW_STAGE_COMPLETE` callbacks. Nonempty is not
sufficient: accept a raw only when the callback comes from the registered
exchange session, uses the expected stable `handoff_id`, names the assigned raw,
and reports
`verification=natural_complete;required_fields_present;exact_text_equal`.
Read the corresponding question and raw once to confirm every explicitly
required section or decision field is present before downstream use.

If a raw already exists, send the same assignment to its owning exchange for
verification; never inspect an external reviewer from this manager and never
resubmit from the manager. A `REVIEW_STAGE_BLOCKED` callback is a terminal round
blocker, not authority to substitute another exchange or reviewer.

Before a downstream dispatch, require every needed active-round artifact to be
present in `evidence_commit`. If newly written or verified files are not in that
pushed commit, send exactly one `REVIEW_GIT_PUSH_REQUIRED` callback and end the
turn. The controller inspects only the named paths, commits and pushes them, then
resends `START_REVIEW` with the new 40-character commit. Derive progress from
the files and commit; do not add a state file or a separate resume command.

Verify a controller-supplied pushed boundary only against the shared local
remote-tracking ref: require `git merge-base --is-ancestor <evidence_commit> My-paper-code/aggressive`
to succeed. Do not run `git push`, `git fetch`,
`git ls-remote`, or another network command from the manager. The controller's
successful push is what updates that ref in this shared repository.

## Liveness

Each reviewer exchange creates, retargets, and deletes its own external-response
heartbeat. This manager never creates or manages a heartbeat. It performs one
bounded mechanical transition when it receives `START_REVIEW`,
`REVIEW_STAGE_COMPLETE`, or `REVIEW_STAGE_BLOCKED`, sends the next required
message, and ends. The recipient message wakes the next session. A Git-boundary
callback ends the turn; the controller's next `START_REVIEW` wakes it again.

Attempt the final controller callback once with the stable `handoff_id`. If the
send tool does not confirm the registered controller task, preserve the pushed
disposition and end locally with `REVIEW_DELIVERY_UNCONFIRMED`; do not create a
heartbeat, contact a reviewer, or repeat scientific work. Re-delivery of the
same handoff is idempotent when the controller explicitly resumes the manager.

## Reply to Controller

Take the controller session ID only from
`session-roles.json.roles.controller.thread_id`. Immediately before replying,
resolve that ID live with `$hmasd-task-router`; copy the returned `hostId`,
`threadId`, `model`, and `thinking` unchanged into the send. Never take a return
ID or model setting from the assignment, review registry, conversation history,
or heartbeat prompt.

When a pushed boundary is required, send exactly:

```text
REVIEW_GIT_PUSH_REQUIRED
role=external_review_manager
handoff_id=<round>:git:<divergent-acceptance|convergent-question|final-disposition>
round=<id>
paths=<comma-separated exact round-relative paths>
next=<CONVERGENT_DISPATCH|FINAL_CALLBACK>
```

This callback grants no Git authority to the manager. After the controller
pushes the named paths, it resends `START_REVIEW` with the new pushed commit.

On success send exactly:

```text
REVIEW_COMPLETE
role=external_review_manager
handoff_id=<round>:complete:<pushed-disposition-commit>
round=<id>
disposition=<round_path>/50_DISPOSITION.md
commit=<pushed commit>
```

On a terminal operational blocker send exactly:

```text
REVIEW_BLOCKED
role=external_review_manager
handoff_id=<round>:blocked:<stable-blocker-code>
round=<id>
reason=<direct blocker>
```

The callback is complete only when the send tool returns the same registered
controller `threadId`. A local final response is not delivery. If delivery is
unconfirmed, follow the `REVIEW_DELIVERY_UNCONFIRMED` rule above; do not contact
a reviewer or create a heartbeat. A later explicit re-delivery uses the same
`handoff_id` and is idempotent under the router receive contract.

External review recommends scientific action but never grants code or experiment
authority. The controller consumes only `50_DISPOSITION.md`.
