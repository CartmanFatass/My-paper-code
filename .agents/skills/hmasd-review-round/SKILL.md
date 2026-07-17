---
name: hmasd-review-round
description: Run the full tracked HMASD external algorithm-review round with blind Gemini 3.1 Pro High and GPT-5.6 Pro divergent reviews, controller synthesis, and a convergent GPT-5.6 Pro review. Use only for a cross-round architecture contradiction, a coherent new route tied to the final variable-team plus variable-lifetime capability, or a critical promotion or retirement boundary that the registered contract cannot settle. Do not use for prompt generation, manual handoff, reading one returned review, routine result interpretation, literature discussion, open brainstorming, a single-reviewer consultation, or a disposition already determined by the registered contract. Archive raw replies before interpretation; reviewer advice never authorizes edits or experiments.
---

# HMASD Review Round

Read the round's `00_REVIEW_BRIEF.md`, `01_SHARED_SOURCE_MANIFEST.md`, and
`references/review-protocol.md`. Gemini additionally reads
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Read the neutral
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` only before a Pro
submission. Read `docs/external-review/REVIEWER_CONVERSATIONS.json` before any
Pro browser transport. `docs/external-review/README.md` is a human index, not a
mandatory runtime read. Do not reload workflow documents at every stage.

## Run the Round

1. Freeze one shared evidence boundary and exact source allowlists.
2. Run Gemini and the open GPT-5.6 Pro as blind, independent divergent
   reviewers with equal standing.
3. Archive both raw responses before the controller compares their claims with
   repository evidence and writes a synthesis.
4. Give the synthesis and both raw reviews to the convergent GPT-5.6 Pro.
5. Archive its raw response, then let the controller accept, reject, modify, or
   defer each proposal and update the owning project document.

The convergent reviewer must rank and stress-test a portfolio of two to four
live hypotheses or architectures when defensible. It may recommend stopping or
the next serialized evidence source, but must not turn compute serialization
into a unique permitted research direction. Only the controller may adopt its
recommendation. A valid scientific FAIL does not require a successor for its
failed branch, but it retires other branches only when the evidence reaches
them.

## Verify Pro Evidence Boundary

Before either Pro submission, resolve a full 40-character commit and verify
that it is reachable from the remote `aggressive` branch. Verify that the
question contains an explicit divergent or convergent role, an exact
`Repository files to inspect` section, and that every listed path exists in the
same commit. Run `scripts/verify_pro_review_boundary.ps1`; if it fails, return
`BLOCKED` before browser transport and do not ask the reviewer to discover
missing evidence.

## Mandatory Pro Transport

The controller never operates the Pro browser. For each missing raw artifact,
select its exact registered local/external pair, pass the remote evidence
preflight, and require the idle target's live model and effort to match the
registry. Send only the route token and tracked paths with this exact shape:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<registered host_id>",
  threadId: "<registered thread_id>",
  model: "<registered model_id>",
  thinking: "<registered reasoning_effort>",
  prompt: "<route token and tracked paths only>"
})
```

Re-read the target settings after delivery. The exchange must verify its local
thread, external conversation, role ACK and visible `Pro` label before browser
use, archive the exact response, then return `COMPLETE` or `BLOCKED` through the
same guarded format resolved against the controller. Never omit `model` or
`thinking`, repair a mismatch, change a model, edit thread state, mix roles,
create a duplicate, or submit roles in parallel. A mismatch is
`BLOCKED_REVIEW_THREAD_IDENTITY`.

The route token is `<round>:<role>:<commit>:<raw-path>`; a closed token is a
no-op. Browser, plugin, authentication, identity, or completeness failures are
transport blockers, never scientific raw responses.

Resume a round from its first missing artifact. A nonempty raw response is
immutable and proves that submission is already complete; archive or interpret
it, but never resubmit that reviewer prompt. An incomplete or ambiguous raw
response is `BLOCKED` for exact manual recovery, not authority to create another
reviewer conversation or silently submit again.

Automatic permission covers Git-visible Pro transport and raw archival only.
Sending private repository content, logs, or local papers to Gemini or another
external service requires explicit informed user approval naming the allowlist;
workflow automation never implies that consent. Reviewer advice does not
authorize code, experiments, promotion, or scientific disposition. If
authentication, model identity, page state, source completeness, or response
completeness is ambiguous, return `BLOCKED` with the exact manual prompt.
