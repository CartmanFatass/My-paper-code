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

## Mandatory Pro Dispatch State Machine

The active controller never operates the Pro browser. The only valid Pro route
is its registered one-to-one local exchange using guarded direct delivery:

1. Read `REVIEWER_CONVERSATIONS.json` and select exactly one role.
2. Confirm that role's raw artifact is absent and run the remote evidence
   preflight on the immutable commit.
3. Require the target to be idle, then read its live model and effort. They must
   exactly match the registry; an active target waits, while an identity mismatch
   is `BLOCKED_REVIEW_THREAD_IDENTITY`, never an invitation to change it.
4. Send only the route token, round path, commit, question path and raw path by
   the exact guarded command below. All routing and target-setting fields are
   mandatory:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<registered host_id>",
  threadId: "<registered thread_id>",
  model: "<registered model_id>",
  thinking: "<registered reasoning_effort>",
  prompt: "<route token and tracked paths only>"
})
```

5. Re-read the target settings after delivery and require the same model and
   effort. The one-to-one exchange verifies its local thread ID, external
   conversation ID, role ACK and visible `Pro` label.
6. Only after that ACK may the exchange conversation use the browser and submit
   the neutral handoff to its registered external conversation.
7. It archives the exact completed response before interpretation. A plugin,
   authentication, identity or completeness failure is recorded as a transport
   blocker, not as the role's scientific raw response.
8. It returns only `COMPLETE` or `BLOCKED`, raw path, identity and anomaly by the
   same guarded command resolved against the controller's live settings. The
   controller resumes from the first missing artifact.

Never omit `model` or `thinking`: the affected desktop runtime otherwise
inherits the sender turn's settings. Never use a guarded send to repair a
mismatch, and never edit the thread database or restore a model after delivery.

The route token is `<round>:<role>:<commit>:<raw-path>`. Reusing a closed token
is a no-op. The Open exchange never opens the Convergent external thread, and
the Convergent exchange never opens the Open external thread.

## Preserve Transport and Authority

Use the exact registered conversation for each Pro role. `OPEN_DIVERGENT` and
`CONVERGENT` are separate persistent conversations and are never substitutes
for one another. Before every submission, open the registered URL directly and
pass the role identity check: the current URL contains the registered
conversation ID, the page shows the registered model label without opening or
changing the model selector, and the history contains the exact registered
role ACK. A mismatch is `BLOCKED_REVIEW_THREAD_IDENTITY`; do not submit, create
a fallback conversation, or alter any model.

Each Pro role has its own one-to-one local Codex exchange conversation recorded
under `codex_exchange` in the registry. The controller does not submit Pro
prompts in its own browser and does not use one exchange conversation for both
roles. Create each exchange conversation as `Luna High`, then freeze its model;
an existing manually configured exchange is never changed. A guarded direct
message always names the target's registered host, thread, model and effort and
is checked before and after delivery. The target must return its own Codex
thread ID, external conversation ID and role ACK before any browser side effect.
Missing or mismatched identity stops transport.

Never create a duplicate because a reviewer is busy, never run parallel
submissions, and never change an existing conversation's model.

Resume a round from its first missing artifact. A nonempty raw response is
immutable and proves that submission is already complete; archive or interpret
it, but never resubmit that reviewer prompt. An incomplete or ambiguous raw
response is `BLOCKED` for exact manual recovery, not authority to create another
reviewer conversation or silently submit again.

Automatic permission covers reviewer communication and raw archival only. It
does not authorize code, experiments, promotion, or scientific disposition. If
authentication, model identity, page state, source completeness, or response
completeness is ambiguous, return `BLOCKED` with the exact manual prompt.
