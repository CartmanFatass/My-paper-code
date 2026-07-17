---
name: hmasd-review-round
description: Run a tracked HMASD external algorithm-review round using the persistent Gemini 3.1 Pro High, divergent GPT-5.6 Pro, controller synthesis, and convergent GPT-5.6 Pro workflow. Use at qualifying architecture, coherent route-design, or critical result boundaries that need independent review. Archive raw replies before interpretation; reviewer advice never authorizes edits or experiments.
---

# HMASD Review Round

Read `docs/external-review/README.md`, the tracked round manifest, and
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md`. Then read
`references/review-protocol.md`.

## Run the Round

1. Freeze one shared evidence boundary and exact source allowlists.
2. Run Gemini and the open GPT-5.6 Pro as blind, independent divergent
   reviewers with equal standing.
3. Archive both raw responses before the controller compares their claims with
   repository evidence and writes a synthesis.
4. Give the synthesis and both raw reviews to the convergent GPT-5.6 Pro.
5. Archive its raw response, then let the controller accept, reject, modify, or
   defer each proposal and update the owning project document.

The convergent reviewer may stop or select at most one active evidence source.
A valid scientific FAIL does not require a successor.

## Preserve Transport and Authority

Reuse the registered persistent conversation for each reviewer role. Never
create a duplicate because a reviewer is busy, never run parallel submissions,
and never change an existing conversation's model.

Automatic permission covers reviewer communication and raw archival only. It
does not authorize code, experiments, promotion, or scientific disposition. If
authentication, model identity, page state, source completeness, or response
completeness is ambiguous, return `BLOCKED` with the exact manual prompt.
