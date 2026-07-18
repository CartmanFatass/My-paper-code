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
3. Controller synthesis from both immutable raws.
4. Convergent-Pro review of evidence, both raws, and synthesis.
5. Controller disposition.

The divergent reviewers have equal standing. Reviewers recommend; only the
controller changes algorithms, experiments, or the portfolio.

## State and Dispatch Invariants

Manage `05_REVIEW_STATE.json` only with `scripts/review_state.ps1`. Current
schema 4 records `dispatch_count`, immutable `route_token`, `dispatched_at`, and
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

Before dispatch, verify that the sandbox identity can update the registered
Antigravity conversation database, `agentapi.bat`, and
`cache/last_conversations.json`, including creation of only their required
SQLite or atomic-replace auxiliary files. This is a transport precondition, not
a reason to grant write access to the whole user profile or to run the CLI
unsandboxed. If any exact path is not writable, stop before dispatch with
`BLOCKED_GEMINI_STATE_NOT_WRITABLE`.

## Pro

Reuse the two registered role-specific Luna Exchange tasks. `OPEN_DIVERGENT`
and `CONVERGENT` each have one fixed Codex task and one fixed ChatGPT Pro URL;
never substitute, merge, or create a replacement role session.

The controller dispatches one route to the matching Exchange through
`$hmasd-task-router`. The prompt contains only the route token, commit, question
path, raw path, and deadline. The Exchange's terminal message also goes through
that Skill using a freshly resolved controller route. The registry contains the
role-specific expected route and a controller mirror; a live mismatch blocks
before delivery and is never repaired by changing either task's model.

The Exchange alone operates the Codex in-app browser. It opens the registered
role-specific URL, verifies the visible `Pro` setting, expands the neutral
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

Archive each raw before interpretation. Write controller synthesis only after
both divergent raws and disposition only after the convergent raw. Update
`docs/project/CURRENT_WORK.md`, `docs/project/ExpRecord.md`, and Git only once at
the accepted disposition boundary.
