---
name: hmasd-review-round
description: "Use when creating or resuming a tracked HMASD five-stage external-review round. Do not use for prompt generation, one returned review, literature discussion, brainstorming, single-reviewer consultation, routine result interpretation, or a contract-determined disposition."
---

# HMASD Review Round

This is a current-path workflow, not a compatibility layer. Ignore old review
states, transports, tasks, receipts and scripts. Start each new round with the
current files and schema.

Read only:

- the round's `00_REVIEW_BRIEF.md` and `01_SHARED_SOURCE_MANIFEST.md`;
- `02_GEMINI_LOCAL_SOURCE_MANIFEST.md` for Gemini;
- `docs/external-review/REVIEWER_CONVERSATIONS.json` for current sessions;
- `docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` for Pro.

## Five Stages

1. Gemini divergent review.
2. Blind open-Pro divergent review.
3. Controller synthesis from both archived raws.
4. Convergent-Pro review of the evidence, both raws and synthesis.
5. Controller disposition.

The two divergent reviewers have equal standing. Reviewers recommend; only the
controller changes algorithms, experiments or the research portfolio.

## Lightweight State

`05_REVIEW_STATE.json` prevents duplicate submissions. Manage it only with
`scripts/review_state.ps1`.

- `init` creates the current schema;
- `show` reports all stages and the next action;
- `transition` records a real dispatch, completed artifact or blocker;
- `validate` is diagnostic only.

Run `show` once when resuming. Do not run separate inventories or historical
state checks. A completed raw is immutable. External stages move
`NOT_STARTED -> DISPATCHED -> COMPLETE`; a blocker records one actionable
reason. `route_token` is `<round>:<role>:<commit>:<raw-path>`.

## Evidence Boundary

Before either Pro submission, run
`scripts/verify_pro_review_boundary.ps1` for one remote-reachable 40-character
commit, the exact question path and every `Repository files to inspect` entry.
Stop if that current evidence boundary is unavailable.

## Gemini

Reuse the registered Gemini Exchange and Antigravity session. Send one route
using only `hostId`, `threadId` and `prompt`; never pass model or thinking
fields. The Exchange reads the approved manifest and writes only
`11_GEMINI_DIVERGENT_RAW.md`.

## Pro

**REQUIRED SUB-SKILL:** Use `chatgpt-delegate` from
`codex-chatgpt-control`.

The controller directly uses the registered role-specific URL. Open Chat,
require the visible intelligence setting `Pro`, expand the neutral handoff by
replacing only commit and question path, then submit once:

```javascript
const submitted = await chatgpt.runner.run(reviewer, {
  input: handoff,
  thread: { type: "url", url: registered.url },
  experience: "chat",
  configuration: { intelligence: "Pro" },
  wait: false,
  read: false
});
```

After a verified submission, transition the stage to `DISPATCHED`. Use bounded
same-thread reads; never resubmit or use response-control buttons:

```javascript
const read = await chatgpt.messages.waitAndRead({
  timeoutMs: 25_000,
  stableMs: 1_500,
  pollMs: 750,
  role: "assistant",
  format: "markdown"
});
```

If generation remains active, keep the same stage and thread. When
`complete: true` and generation is inactive, write `responseText` exactly to
the registered raw file, compare the file with the in-memory text, then mark
`COMPLETE`.

Use no Pro Codex Exchange, transport subagent, cross-task relay, heartbeat,
automation, shell sleep or alternate conversation. Stop on the plugin's
structured blocker rather than adding a fallback path.

## Finish

Archive each raw before interpretation. The controller writes synthesis only
after both divergent raws and disposition only after the convergent raw. Update
project memory and Git once at the accepted disposition boundary.
