---
name: hmasd-review-round
description: Run the full tracked HMASD external algorithm-review round with blind Gemini 3.1 Pro High and GPT-5.6 Pro divergent reviews, controller synthesis, and a convergent GPT-5.6 Pro review. Use only for a cross-round architecture contradiction, a coherent new route tied to the final variable-team plus variable-lifetime capability, or a critical promotion or retirement boundary that the registered contract cannot settle. Do not use for prompt generation, manual handoff, reading one returned review, routine result interpretation, literature discussion, open brainstorming, a single-reviewer consultation, or a disposition already determined by the registered contract. Archive raw replies before interpretation; reviewer advice never authorizes edits or experiments.
---

# HMASD Review Round

Read `docs/external-review/README.md`, the round's `00_REVIEW_BRIEF.md` and
`01_SHARED_SOURCE_MANIFEST.md`, then read `references/review-protocol.md`.
Gemini additionally reads `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Read the neutral
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` only before a Pro
submission. Read `docs/external-review/REVIEWER_CONVERSATIONS.json` before any
Pro browser transport. Do not reload every workflow document at every stage.

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

The active controller must not operate the browser for a Pro submission, send
the review prompt directly to another Codex thread, or pass a `model` or
`thinking` field during review transport. The only valid Pro route is:

1. Read `REVIEWER_CONVERSATIONS.json` and select exactly one role.
2. Confirm that role's raw artifact is absent and run the remote evidence
   preflight on the immutable commit.
3. Update only that role's registered heartbeat prompt with a route token,
   round path, commit, question path and raw destination; set it `ACTIVE`.
4. The one-to-one exchange conversation first verifies and reports its local
   thread ID, external conversation ID, role heartbeat and visible `Pro` label.
5. Only after that ACK may the exchange conversation use the browser and submit
   the neutral handoff to its registered external conversation.
6. It archives the exact completed response before interpretation. A plugin,
   authentication, identity or completeness failure is recorded as a transport
   blocker, not as the role's scientific raw response.
7. It pauses its own heartbeat after either raw archival or a blocker. The
   controller verifies `PAUSED`, reads the exchange thread and then resumes the
   review round from the first missing artifact.

The route token is `<round>:<role>:<commit>:<raw-path>`. Reusing a closed token
is a no-op. The Open exchange never opens the Convergent external thread, and
the Convergent exchange never opens the Open external thread.

## Preserve Transport and Authority

Use the exact registered conversation for each Pro role. `OPEN_DIVERGENT` and
`CONVERGENT` are separate persistent conversations and are never substitutes
for one another. Before every submission, open the registered URL directly and
pass the thread heartbeat check: the current URL contains the registered
conversation ID, the page shows the registered model label without opening or
changing the model selector, and the history contains the exact registered
role ACK. A mismatch is `BLOCKED_REVIEW_THREAD_IDENTITY`; do not submit, create
a fallback conversation, or alter any model.

Each Pro role has its own one-to-one local Codex exchange conversation recorded
under `codex_exchange` in the registry. The controller does not submit Pro
prompts in its own browser and does not use one exchange conversation for both
roles. Create each exchange conversation as `Luna High`, then freeze its model;
an existing manually configured exchange is never changed. Activate only the
matching exchange conversation's heartbeat; do not
send the review prompt with a cross-thread message and do not pass `model` or
`thinking` overrides. The heartbeat carries only the reviewer role, registry
path, round path, immutable commit and first missing artifact. The target must
return its own Codex thread ID, the external reviewer conversation ID and role
ACK before any browser side effect. Missing or mismatched ACK stops transport.
After a complete raw archive or a transport blocker, pause that role's
heartbeat. This prevents a cross-thread message from rebinding either
conversation's model or role.

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
