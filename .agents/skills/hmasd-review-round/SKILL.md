---
name: hmasd-review-round
description: "Use when creating or resuming a tracked HMASD five-stage external-review round governed by 05_REVIEW_STATE.json. Do not use for prompt generation, manual handoff, one returned review, literature discussion, brainstorming, single-reviewer consultation, routine result interpretation, or a contract-determined disposition."
---

# HMASD Review Round

Read the round's `00_REVIEW_BRIEF.md`, `01_SHARED_SOURCE_MANIFEST.md`, and
`references/review-protocol.md`. Gemini additionally reads
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Read
`docs/external-review/REVIEWER_CONVERSATIONS.json` before transport and the
neutral `docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` before a Pro
submission.

## State Authority

Create and update `05_REVIEW_STATE.json` only through
`scripts/review_state.ps1`. Run `validate`, `show`, and `next` once on
activation and after an actual transition. Do not repeat them while an external
stage remains `DISPATCHED`.

- `NOT_STARTED`: no verified submission;
- `DISPATCHED`: one prompt was submitted to the registered external session;
- `COMPLETE`: the naturally completed raw is archived and verified;
- `BLOCKED`: an actionable authority, identity, source, authentication, or
  transport problem prevents progress.

`COMPLETE` is immutable. Never infer progress from artifact presence, move
`DISPATCHED` back to `NOT_STARTED`, or resubmit an identity-confirmed prompt.
Leaving `BLOCKED` requires the script's typed resolution receipt.

Receipts contain exactly:

```text
source;session;conversation;role;model;route;terminal;reference
```

## Round Order

1. Freeze one shared Git-visible evidence boundary and exact source allowlists.
2. Run Gemini and open Pro as blind independent divergent reviewers with equal
   standing; serialize external transport.
3. Archive both raws before controller synthesis.
4. Give both raws and synthesis to convergent Pro.
5. Archive its raw; only the controller writes disposition and updates project
   memory.

The convergent reviewer recommends; it never authorizes code, experiments,
promotion, retirement, or a unique legal research direction.

## Evidence Boundary

Before a Pro stage, resolve one full 40-character commit reachable from remote
`aggressive`. Require an explicit role, exact `Repository files to inspect`, and
every listed path at that commit. Run `scripts/verify_pro_review_boundary.ps1`.
A failure is `BLOCKED_REMOTE_EVIDENCE`; do not send the reviewer to discover
missing inputs.

## Gemini Transport

Gemini alone retains the registered one-to-one Codex Exchange and Antigravity
session. Follow `references/review-protocol.md`; the Exchange may write only
`11_GEMINI_DIVERGENT_RAW.md`. Its cross-task message uses only `hostId`,
`threadId`, and `prompt`; never supply model or thinking overrides.

## Direct Pro Transport

**REQUIRED SUB-SKILL:** Use `chatgpt-delegate` from the installed
`codex-chatgpt-control` plugin.

The active controller talks directly to the two registered visible ChatGPT
sessions. Do not create, dispatch, resume, or relay through a Pro Codex Exchange.
Use the role-specific URL in `REVIEWER_CONVERSATIONS.json`; open Pro and
convergent Pro never share a conversation.

Load the plugin-bundled runtime, create the redacted-reporting client, then:

1. call `experience.open({ experience: "chat" })`;
2. inspect Chat configuration and require `verified: true` with active
   intelligence `Pro`;
3. expand the neutral handoff by replacing only `<commit>` and
   `<question-path>`;
4. submit once to the registered URL:

```javascript
const submitted = await chatgpt.runner.run(reviewer, {
  input: handoff,
  thread: { type: "url", url: registered.url },
  experience: "chat",
  configuration: { intelligence: "Pro" },
  wait: false,
  read: false,
  report: { enabled: true, includeContent: false }
});
```

Require successful thread selection, `submissionState: "submitted"`, and a
verified configuration step before recording `DISPATCHED`. The receipt is:

```text
source=chatgpt_control;session=<registry pro_transport.session_id>;conversation=<registered conversation_id>;role=<registered role>;model=Pro;route=<exact route>;terminal=DISPATCHED;reference=plugin:submitted
```

The visible `Pro` setting is the verified fact; do not claim an unexposed
underlying model identifier.

## Completion and Recovery

After submission, use bounded reads on the same visible thread:

```javascript
const read = await chatgpt.messages.waitAndRead({
  timeoutMs: 25_000,
  stableMs: 1_500,
  pollMs: 750,
  role: "assistant",
  format: "markdown"
});
```

`partial`, `completionState: "generating"`, or `generationActive: true` means
the original request remains in progress. Keep the stage `DISPATCHED` and use
another bounded status/read call on the same thread; never submit, continue,
retry, regenerate, or shorten it. No Codex task notification, heartbeat,
automation, shell sleep, controller-to-controller message, or page response
control is part of Pro transport.

Only `complete: true` with generation inactive is admissible. Write
`responseText` exactly to the registered raw path and compare the in-memory text
with the file before interpretation. Then record:

```text
source=chatgpt_control;session=<registry pro_transport.session_id>;conversation=<registered conversation_id>;role=<registered role>;model=Pro;route=<exact route>;terminal=COMPLETE;reference=plugin:completed
```

Stop on the plugin's structured `browser_bridge_unavailable`, `login_required`,
`captcha`, `rate_limit`, `permission`, `needs_confirmation`, or
`selector_drift` blocker. A timeout after submission authorizes only same-thread
status/read recovery.

## Historical Compatibility

Existing `source=exchange`, `source=gemini`, and manual receipts remain valid
history and are never rewritten. New Pro dispatches use
`source=chatgpt_control`. Reviewers never edit `05_REVIEW_STATE.json`, root
memory, synthesis, disposition, code, or Git; the controller owns all state
transitions and scientific interpretation.
