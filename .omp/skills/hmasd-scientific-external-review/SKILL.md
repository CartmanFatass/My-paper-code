---
name: hmasd-scientific-external-review
description: Run one frozen, at-most-once scientific external-review round.
---

# HMASD Scientific External Review

## Purpose

Coordinate mutually blind Gemini and Pro divergent review, local EM synthesis,
and optional Pro convergence through the single Root-mediated
`BrowserTransport` service. Review is evidence, not permission. Provider
binding, at-most-once send, exact archive bytes, scientific interpretation, and
tracked handoff authority remain separate.

## Inputs

- Direction ID, deterministic round ID, frozen question SHA, and frozen evidence
  set SHA.
- Exact prompt paths/bytes, archive paths, and expected provider/model
  identities.
- Existing BrowserTransport/Agentify operation references, transport states,
  and external-index revision.
- EM synthesis references for any Convergence prompt.

Every transport request uses the OMP task/Hub carrier with meaning-complete
`Objective`, `Inputs`, `Acceptance`, `Non-goals`, and `Return` sections and is
returned as `next_action.owner=TRANSPORT` through Root. EM and CM never spawn or
contact BrowserTransport directly.

## Bounded cycle

1. Freeze the question/evidence SHAs and derive the deterministic round ID.
   Refuse any prompt or evidence mutation after freezing.
2. Prepare mutually blind Gemini and Pro divergent requests in parallel. Root
   dispatches both to the one reusable BrowserTransport service; the singleton
   serializes send-capable page mutations but a `SENT_WAITING` operation does
   not block initiation of the other eligible request. Both requests use only
   Agentify strict `agentify_review_query` as the send-capable surface. Pro must
   bind `provider: chatgpt` and its exact Pro model; Gemini must bind
   `provider: gemini` and its exact Gemini model. Cross-provider substitution is
   forbidden in either direction.
3. BrowserTransport returns common v1 transport envelopes to Root. Root routes
   the exact transport operation/conversation/archive references back to EM.
   `MONITOR` or any observation of a committed or uncertain request uses only
   the same strict operation through `agentify_review_observe` or
   `agentify_review_query` with `verifyExisting`; it never sends again.
4. Wait for natural completion without provider quorum, polling, or resend.
   BrowserTransport performs no scientific interpretation. EM interprets
   provider content only after the exact archive has passed transport
   fingerprint and reread checks.
5. Perform local EM synthesis before authoring a Pro `CONVERGENCE` prompt. That
   prompt is a new frozen Root-mediated BrowserTransport assignment bound to
   `provider: chatgpt`; it cannot reuse Gemini or bypass Agentify strict review.
   Return the exact rendered intake to Artifact Writer when a handoff is needed.
6. Root alone invokes `hmasd_external_review.py` to validate exact archive bytes
   and create the tracked archive reference. EM updates the external index once.

One cycle has one frozen round and one divergent wave. A later parent wake-up may
start the next deterministic round; no second sender, local transport ledger,
provider substitution, or automatic resend route is introduced.

## State writes

- BrowserTransport writes no tracked scientific state and never reconstructs
  Agentify ledger/send state. Agentify may write only the assignment's exact
  response path; BrowserTransport fingerprints and rereads it before returning
  a non-null archive reference.
- Root validates and records exact tracked archives through the external-review
  CLI.
- EM writes only external-index pointers and handoff references after the
  transport return; Artifact Writer writes the provider `HANDOFF.md`.
- Never add OMP schema fields to an immutable Agentify natural-completion
  archive, and never treat an operation, tab, key, or hash as provider or
  workflow authority.

## Returned result envelope

BrowserTransport returns the common v1 envelope to Root with
`role: "hmasd-browser-transport"`, logical identity `BrowserTransport`, and a
payload of this form:

```json
{
  "kind": "transport",
  "browser_identity": "BrowserTransport",
  "transport_assignment": "<transport-assignment>",
  "requester": "EM-example-direction",
  "provider": "gemini",
  "mode": "DIVERGENT",
  "effect_ref": null,
  "transport_state": "COMPLETE",
  "round_id": "0123456789abcdef0123",
  "provider_conversation_ref": "<provider-conversation-reference>",
  "operation_ref": "<Agentify-operation-reference>",
  "archive_ref": "<fingerprinted-and-reread-path>",
  "handoff_ref": null
}
```

A completed round also carries frozen question/evidence references in
`state_refs` and exact operation/archive paths in `artifact_refs`. Root forwards
those facts to EM without changing their provider binding. A nonterminal same-
operation observation retains `next_action.owner=TRANSPORT`; scientific
interpretation returns to EM only after transport completion.

## Failure handling

Unknown commitment is terminal for sending: observe and recover the same exact
Agentify operation, never resend. `SENT_WAITING`, `COMMITMENT_UNKNOWN`, and
`SENT_UNREADABLE` are observe-only. `ZERO_SEND_FAILED` proves no send for that
operation but does not authorize operation two. Reject changed prompt/evidence
SHAs, non-natural completion, wrong provider or model identity, duplicate round
IDs, invalid or unreadable archive bytes, stale index revisions, any ordinary
send surface, and every attempt to substitute Gemini for Pro or ChatGPT for
Gemini.

Missing transport or Advisor output is an evidence gap, not an approval failure.
Transport failure does not change a scientific conclusion, claim ceiling,
engineering status, Portfolio action, or lifecycle. Root mediates exact
recovery/redispatch; BrowserTransport handles bounded page-local non-sending
recovery; EM owns all scientific interpretation.

## Deletion condition

Delete this Skill when a reviewed external-review boundary preserves the
singleton Root-mediated transport service, Agentify strict-review-only
at-most-once ledger, exact provider bindings, blind divergent ordering, local
synthesis, exact archive bytes, and handoff authority without a second sender or
state writer.
