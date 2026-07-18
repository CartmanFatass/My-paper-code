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

Reuse the registered Gemini Exchange and Antigravity session. Send one route
using only `hostId`, `threadId`, and `prompt`; never pass model or thinking.
Gemini reads the approved manifest and writes only
`11_GEMINI_DIVERGENT_RAW.md`.

## Pro

**Required sub-skill:** use `chatgpt-delegate` from
`codex-chatgpt-control`.

The controller opens the registered role-specific URL, verifies the visible
`Pro` setting, expands the neutral handoff by replacing only commit and question
path, and submits once. After verified submission, record `DISPATCHED` with the
same route and deadline.

Use bounded reads on that URL until natural completion or the deadline. Never
use a Pro Codex Exchange, transport subagent, cross-task relay, heartbeat,
automation, shell sleep, alternate conversation, or response-control button.
Stop on a structured plugin blocker.

When the response is complete and inactive, write `responseText` exactly to the
registered raw and compare file content byte-for-byte before marking
`COMPLETE`. Missing, partial, or ambiguous raw is incomplete evidence.

## Finish

Archive each raw before interpretation. Write controller synthesis only after
both divergent raws and disposition only after the convergent raw. Update
`docs/project/CURRENT_WORK.md`, `docs/project/ExpRecord.md`, and Git only once at
the accepted disposition boundary.
