---
name: hmasd-review-round
description: Run the full tracked HMASD external algorithm-review round with blind Gemini 3.1 Pro High and GPT-5.6 Pro divergent reviews, controller synthesis, and a convergent GPT-5.6 Pro review. Use only for a cross-round architecture contradiction, a coherent new route tied to the final variable-team plus variable-lifetime capability, or a critical promotion or retirement boundary that the registered contract cannot settle. Do not use for prompt generation, manual handoff, reading one returned review, routine result interpretation, literature discussion, open brainstorming, a single-reviewer consultation, or a disposition already determined by the registered contract. Archive raw replies before interpretation; reviewer advice never authorizes edits or experiments.
---

# HMASD Review Round

Read `docs/external-review/README.md`, the round's `00_REVIEW_BRIEF.md` and
`01_SHARED_SOURCE_MANIFEST.md`, then read `references/review-protocol.md`.
Gemini additionally reads `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Read the neutral
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` only before a Pro
submission. Do not reload every workflow document at every stage.

## Run the Round

1. Freeze one shared evidence boundary and exact source allowlists.
2. Run Gemini and the open GPT-5.6 Pro as blind, independent divergent
   reviewers with equal standing.
3. Archive both raw responses before the controller compares their claims with
   repository evidence and writes a synthesis.
4. Give the synthesis and both raw reviews to the convergent GPT-5.6 Pro.
5. Archive its raw response, then let the controller accept, reject, modify, or
   defer each proposal and update the owning project document.

The convergent reviewer may recommend stopping or at most one active evidence
source; only the controller may adopt that recommendation. A valid scientific
FAIL does not require a successor.

## Verify Pro Evidence Boundary

Before either Pro submission, resolve a full 40-character commit and verify
that it is reachable from the remote `aggressive` branch. Verify that the
question path and every path under its `Repository files to inspect` exist in
that same commit. If any check fails, return `BLOCKED` before browser transport;
do not ask the reviewer to discover missing evidence.

## Preserve Transport and Authority

Reuse the registered persistent conversation for each reviewer role. Never
create a duplicate because a reviewer is busy, never run parallel submissions,
and never change an existing conversation's model.

Automatic permission covers reviewer communication and raw archival only. It
does not authorize code, experiments, promotion, or scientific disposition. If
authentication, model identity, page state, source completeness, or response
completeness is ambiguous, return `BLOCKED` with the exact manual prompt.
