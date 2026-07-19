---
name: hmasd-review-round
description: Use only for a complete tracked HMASD external-review round or an unresolved algorithm, portfolio, or next-evidence decision. One persistent External Review Manager owns the full round after one controller start message. Do not use for prompt generation, one returned answer, routine result interpretation, literature discussion, brainstorming, or a disposition already fixed by evidence.
---

# HMASD External Review Round

External review is a mandatory scientific boundary, not an optional advisory
step. Transport complexity must remain isolated from the active controller.

Read `../hmasd-task-router/SKILL.md` before any cross-task communication. Read
only the active round and the review resources named below; do not load the
controller control plane.

## Ownership

The persistent Luna External Review Manager registered in
`docs/external-review/REVIEWER_CONVERSATIONS.json` owns the complete round:

1. Gemini blind divergent review;
2. Open-Pro blind divergent review;
3. factual evidence reconciliation from both immutable raws;
4. Convergent-Pro scientific synthesis;
5. final converged disposition and terminal relay.

The controller creates and pushes the immutable evidence boundary, then sends
exactly one `START_REVIEW` message through `../hmasd-task-router/SKILL.md`. If a
recorded operational blocker is later resolved, the controller sends one
`RESUME_REVIEW` instead of starting a new round. It does not operate Gemini,
browser pages, heartbeat, review state, reconciliation, or recovery. The
manager sends exactly one terminal `REVIEW_COMPLETE` or `REVIEW_BLOCKED`
message through the router. Intermediate progress remains in the manager task
and round state; it is never relayed to the controller.

The manager may stage, commit, and push only files inside its active round
directory when a Git-visible boundary is required for an external reviewer. It
must not stage unrelated dirty-worktree changes or modify project-control files.

## Required Inputs

The registered commit pins reviewer-visible scientific evidence only. It never
pins operational instructions. At every start, resume, heartbeat, and relay,
read this Skill, `../hmasd-task-router/SKILL.md`, the state script, and the
conversation registry from the current working tree. Ignore workflow copies,
static route expectations, model values, or thinking values embedded in an
evidence commit, an old prompt, or prior task history.

The manager reads:

- `00_REVIEW_BRIEF.md`;
- `01_SHARED_SOURCE_MANIFEST.md`;
- `02_GEMINI_LOCAL_SOURCE_MANIFEST.md` for Gemini;
- `docs/external-review/REVIEWER_CONVERSATIONS.json`;
- `docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md`.

Before either Pro submission, run
`scripts/verify_pro_review_boundary.ps1` against the registered 40-character
commit, question path, and repository inputs. An unavailable boundary is a
terminal blocker; it is not reviewer evidence.

## Scientific Contract

Gemini and Open Pro are independent blind divergent reviewers with equal
standing. The manager's reconciliation may map claims to evidence, identify
contradictions, and identify missing inputs, but it may not rank candidates or
select the next evidence source. Convergent Pro receives the evidence, both
raws, and the reconciliation, and must provide:

- an evidence-validity decision;
- a two-to-four-candidate portfolio when the portfolio remains open;
- one selected next evidence source or an explicit stop;
- the causal estimand, comparator, result branches, and prohibited rescues;
- the implementation boundary Codex may operationalize.

No external response authorizes code execution or an experiment. The final
converged disposition is nevertheless mandatory before the controller selects
or promotes a new scientific route.

## Manager Execution

Use `05_REVIEW_STATE.json` and `scripts/review_state.ps1` only inside the manager
task. External prompts are submitted once after visible acceptance. Completed
raws are archived byte-for-byte before they are used downstream. A stage with
an accepted prompt is never resubmitted; a failure before visible acceptance
does not consume the one external submission.

`RESUME_REVIEW` is legal only after the exact recorded operational blocker has
been resolved. Invoke the state script's `resume` mode with that exact blocker.
It may reopen only a `BLOCKED` stage whose `dispatch_count` is zero and which has
no route or dispatch timestamps. Completed stages and their artifacts remain
immutable. A blocked stage with an accepted external dispatch is never reopened
or resubmitted.

The manager directly resumes the registered Antigravity conversation and sends
one document pointer for Gemini:

```text
Read @<question-path> and follow it exactly.
```

Do not spawn a Gemini transport subagent. The user's standing authorization
covers the project files explicitly listed in the Gemini manifest and the
Antigravity CLI's own state root. It excludes credentials, personal files,
unlisted project material, training, and unrelated execution. Do not ask the
controller to repeat the registered authorization.

For Pro, the manager alone uses the Codex in-app browser. It switches the Codex
application to the manager task before browser work, opens the role's registered
URL, verifies the conversation ID and visible `Pro`, submits the neutral handoff
once, and waits only through the registered heartbeat. The browser surface is
application-shared; task isolation is therefore an ownership rule, not a claim
that the UI is physically private to the manager. The controller never invokes
browser tools for a tracked review.

One heartbeat automation targets the manager. The manager activates it only
while a Pro response is pending, performs one bounded read per wake, and pauses
it at every terminal boundary. It never uses shell sleep or sends repeated
waiting messages to the controller.

Heartbeat prompts contain stable task and round identifiers only. They must not
contain model, thinking, expected route, or frozen-route values. Every heartbeat
reads the current operational Skills and resolves the recipient live only when
an actual cross-task send is required.

## Terminal Relay

Complete a terminal boundary in this order:

1. write and validate the authoritative round state and terminal artifact;
2. pause the review heartbeat and confirm that it is paused;
3. resolve the controller's live recipient metadata through the task router;
4. call `send_message_to_thread` once with those exact live values;
5. require the tool result's target `threadId` to match the resolved controller.

Only step 5 proves delivery. A local final response, commentary, heartbeat text,
or delegation payload is not a relay. If delivery proof is unavailable, keep a
relay-only heartbeat pending and do not finish or report the callback as sent.
The relay-only heartbeat may retry only after a definite pre-acceptance failure;
an accepted or ambiguous send is never duplicated.

## Outputs

The manager owns these files:

```text
11_GEMINI_DIVERGENT_RAW.md
21_PRO_OPEN_RAW.md
30_EVIDENCE_RECONCILIATION.md
40_PRO_CONVERGENT_QUESTION.md
41_PRO_CONVERGENT_RAW.md
50_DISPOSITION.md
```

`50_DISPOSITION.md` is the controller's only scientific input from the round.
It preserves the convergent decision and points to the immutable raws; it does
not add a manager-selected successor. The final relay contains only the round,
terminal state, disposition path, and blocker when present.

At `REVIEW_COMPLETE` the controller reads `50_DISPOSITION.md`, checks it against
the immutable evidence and project constraints, records the accepted boundary,
and operationalizes it. At `REVIEW_BLOCKED` the controller reports the exact
transport or evidence blocker without substituting its own scientific decision.
