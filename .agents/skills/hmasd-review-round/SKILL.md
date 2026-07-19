---
name: hmasd-review-round
description: Use only in the dedicated External Review Manager persistent session when the controller assigns one complete HMASD external-review round. It mechanically sequences three independently registered reviewer-exchange sessions, verifies their artifacts, writes factual reconciliation and final disposition, maintains Git-visible round boundaries, and returns one result to the controller; it never operates an external reviewer itself.
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
- verification and Git integration of raw files written by those exchanges;
- Git add, commit, and `git push My-paper-code aggressive` for active-round
  files needed by a reviewer;
- one terminal callback to the controller.

Do not edit code or project-control files, choose or authorize implementation or
compute, change task settings, create reviewer conversations, operate a browser
or Antigravity, write a reviewer raw, create a reviewer heartbeat, or read
unlisted local material. Contact reviewer exchanges only through
`$hmasd-task-router`; contact no reviewer model or controller-bypassing session.

## Round Procedure

Complete these mechanical steps:

1. validate the initial round files and pushed `evidence_commit`;
2. dispatch the Gemini and Open-Pro blind divergent stages independently to
   `gemini_divergent_exchange` and `open_divergent_exchange`;
3. after both verified raws return, write factual
   `30_EVIDENCE_RECONCILIATION.md` without ranking routes;
4. write `40_PRO_CONVERGENT_QUESTION.md`, commit and push the active round, then
   dispatch it to `convergent_exchange`;
5. after its verified raw returns, write `50_DISPOSITION.md` from that response,
   commit and push the active round, and reply once to the controller.

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

Commit and push only active-round artifacts before every downstream dispatch.
A push failure is an operational blocker to report, not a request for the
controller to operate the review.

## Liveness

Each reviewer exchange creates, retargets, and deletes its own external-response
heartbeat. This manager never creates or manages a heartbeat. It performs one
bounded mechanical transition when it receives `START_REVIEW`,
`REVIEW_STAGE_COMPLETE`, or `REVIEW_STAGE_BLOCKED`, sends the next required
message, and ends. The recipient message wakes the next session.

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
