---
name: hmasd-review-round
description: Use only when creating or resuming a complete tracked HMASD five-stage external-review round. Do not use for prompt generation, one returned review, literature discussion, brainstorming, single-reviewer consultation, routine result interpretation, or a disposition already determined by the registered contract.
---

# HMASD Review Round

This is a current-path workflow, not a compatibility layer. Ignore old states,
transports, receipts, and scripts.

Read only the round's `00_REVIEW_BRIEF.md` and
`01_SHARED_SOURCE_MANIFEST.md`; additionally read
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md` for Gemini. Read
`docs/external-review/REVIEWER_CONVERSATIONS.json` for current sessions and
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` for the neutral Pro
handoff.

Before any controller-to-Exchange or Exchange-to-controller task message, read
and follow `../hmasd-task-router/SKILL.md`. It is the sole task-routing contract
for this workflow.

## Five Serialized Stages

1. Gemini blind divergent review.
2. Open-Pro blind divergent review.
3. Codex factual evidence reconciliation from both immutable raws.
4. Convergent-Pro scientific synthesis and decision from evidence, both raws,
   and the reconciliation.
5. Codex operational disposition.

The divergent reviewers have equal standing. Codex stage 3 checks provenance,
claim support, contradictions, and missing inputs only; it does not rank the
portfolio or select a route. Convergent Pro owns scientific synthesis,
portfolio weighting, and the recommended next evidence source or stop. Codex
stage 5 adopts that decision unless it conflicts with the registered evidence,
an explicit user/project constraint, or operational feasibility. Such a
conflict is returned as `BLOCKED` rather than resolved through local research.
No external response authorizes code execution or an experiment.

Before convergent dispatch, `40_PRO_CONVERGENT_QUESTION.md` must explicitly ask
for: the evidence-validity decision; a two-to-four-candidate portfolio when the
portfolio remains open; one selected next evidence source or an explicit stop;
its causal estimand, comparator, outcome branches, and prohibited rescues; and
the implementation boundary Codex may operationalize. A missing item is a
pre-dispatch blocker. This is the required coverage that prevents scientific
choices from falling back to the Codex controller.

## State and Dispatch Invariants

Manage `05_REVIEW_STATE.json` only with `scripts/review_state.ps1`. Current
schema 5 records `dispatch_count`, immutable `route_token`, `dispatched_at`, and
`deadline_at` for each external stage.

- Run `show` once when resuming.
- An external stage may be dispatched exactly once.
- A pre-dispatch blocker may be repaired and then dispatched once.
- A blocker after dispatch is terminal for that stage; never submit again in the
  same round.
- `COMPLETE` and archived raw files are immutable.
- Only one external stage may be `DISPATCHED` at a time.

Set `deadline_at` from the explicit deadline in `00_REVIEW_BRIEF.md`; if absent,
use two hours after verified dispatch. When the deadline passes, make one final
bounded same-thread read. If incomplete, mark `BLOCKED_TIMEOUT` and stop; do not
resubmit, regenerate, continue, or move to another session.

The route token is
`<round>:<role>:<40-char-commit>:<raw-path>`. Before either Pro dispatch, run
`scripts/verify_pro_review_boundary.ps1` for that commit, question path, and all
listed repository inputs. Stop before dispatch if any path is unavailable.

## Gemini

Spawn one depth-one transport subagent with `fork_turns="none"`, model
`gpt-5.6-terra`, and reasoning effort `medium`. It resumes the registered
Antigravity conversation through an interactive `agy` PTY; never create a
persistent Codex Exchange or change the Gemini model.

The TUI handoff is exactly one single-line document pointer:
`Read @<question-path> and follow it exactly.` Do not paste the question body or
any multiline prompt into the TUI. Mark `DISPATCHED` only after that one message
is visibly accepted by the registered session.

The subagent may approve once only a displayed read-only command whose resolved
paths are all in `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Never use
`--dangerously-skip-permissions`; deny invisible commands, writes, credentials,
project-external paths, or broader execution. It may write only this round's
state and `11_GEMINI_DIVERGENT_RAW.md`, returns one terminal payload to the
controller, and is not reused for another round.

Before dispatch, verify that the transport identity can update only the
registered Antigravity conversation database, `bin/agentapi.bat`,
`cache/last_conversations.json`, and Antigravity's own `log/` and `crashes/`
runtime-output directories, including creation of only their required SQLite,
atomic-replace, log, or crash auxiliary files. These paths are transport state,
not review evidence, and their write allowance grants no additional read scope.
This is a transport precondition, not a reason to grant write access to the
whole user profile or to bypass Antigravity permissions. If any exact path is
not writable, stop before dispatch with
`BLOCKED_GEMINI_STATE_NOT_WRITABLE`.

## Pro

Reuse the one registered Luna Exchange task for both Pro stages. It owns two
distinct registered ChatGPT Pro conversation URLs, one for `OPEN_DIVERGENT` and
one for `CONVERGENT`, and switches the Codex in-app browser to the URL named by
the current route. Do not create a second Codex Exchange task, merge the two Pro
conversations, substitute another URL, or reuse one Pro page for both roles.

The controller dispatches one route to the shared Exchange through
`$hmasd-task-router`. The prompt contains only the route token, commit, question
path, raw path, and deadline. The Exchange's terminal message also goes through
that Skill using a freshly resolved controller route. The registry contains one
Exchange route, two role-specific browser URLs, and a controller mirror; a live
mismatch blocks before delivery and is never repaired by changing either task's
model.

The Exchange alone operates the Codex in-app browser. It opens the registered
URL for the current role even when another Pro page is already open, verifies
the conversation ID and visible `Pro` setting, expands the neutral
handoff by replacing only commit and question path, and submits once. It does
not use Chrome, Computer Use, an external browser, a plugin, MCP, shell sleep,
heartbeat, automation, an alternate conversation, or a response-control
button.

The Exchange performs bounded same-page reads until natural completion or the
deadline. It writes the completed response exactly to the registered raw,
compares file content byte-for-byte, transitions the stage, and sends one
terminal payload back with the registered controller route. The controller does
not poll the Exchange. Missing, partial, or ambiguous raw is incomplete
evidence.

## Finish

Archive each raw before interpretation. Write
`30_EVIDENCE_RECONCILIATION.md` only after both divergent raws; it may map
claims to evidence and list contradictions but may not choose an algorithm.
Write `50_DISPOSITION.md` only after the convergent raw and preserve its
scientific decision without adding a Codex-selected successor. Update
`docs/project/CURRENT_WORK.md`, `docs/project/ExpRecord.md`, and Git only once at
the accepted disposition boundary.
