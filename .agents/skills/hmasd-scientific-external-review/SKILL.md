---
name: hmasd-scientific-external-review
description: Run one frozen, at-most-once scientific external-review round.
---

# HMASD Scientific External Review

## Purpose

Coordinate mutually blind Gemini and Pro divergent review, local EM synthesis,
and optional convergence while preserving Agentify as the sole submission
ledger. Review is evidence, not permission; exact archives and scientific
handoffs have distinct authorities.

## Inputs

- Direction ID, deterministic round ID, frozen question SHA, and frozen evidence
  set SHA.
- Exact prompt paths/bytes and expected provider/model identities.
- Agentify operation references, commitment states, and the existing external
  index revision.
- EM synthesis references for any convergence prompt.

## Bounded cycle

1. Freeze question/evidence SHAs and derive the deterministic round ID. Refuse
   any prompt or evidence mutation after freezing.
2. Dispatch mutually blind Gemini and Pro divergent prompts in parallel through
   their transport leaves. Both use the Windows Agentify strict
   `agentify_review_query` ledger surface, but Pro must bind `provider: chatgpt`
   and Gemini must bind `provider: gemini`; cross-provider use is forbidden.
   Each transport may send at most once and uses only `agentify_review_observe`
   in MONITOR mode. Exact-operation recovery remains Root-owned.
3. Wait for natural completion and immutable transport operation/archive
   references. Do not interpret provider responses in the transport role.
4. Perform local EM synthesis before authoring or dispatching a Pro convergence
   prompt. Return the exact rendered intake to Artifact Writer when a handoff is
   needed.
5. Root alone invokes `hmasd_external_review.py` to validate exact archive bytes
   and create the tracked archive reference. EM updates the external index once.

One cycle has one frozen round and one divergent wave. A later parent wake-up may
start the next deterministic round; no polling, provider quorum, or resend route
is introduced.

## State writes

- Transports write no tracked scientific state and never reconstruct Agentify
  ledger/send state.
- Root writes validated exact archives through the external-review CLI.
- EM writes only external index pointers and handoff references after transport
  return; Artifact Writer writes the provider `HANDOFF.md`.
- Never add OMP schema fields to an immutable Agentify natural-completion archive.

## Returned result envelope

Return the common v1 envelope with `role` set to the transport or EM caller and
payload:

```json
{
  "kind": "transport",
  "provider": "gemini",
  "mode": "DIVERGENT",
  "round_id": "<round-id>",
  "operation_ref": "<Agentify-operation-reference>",
  "archive_ref": null,
  "handoff_ref": null
}
```

A completed round also carries frozen question/evidence references in
`state_refs` and the exact operation/archive paths in `artifact_refs`.

## Failure handling

Unknown commitment is terminal for that operation: observe and recover, never
resend. Reject changed prompt/evidence SHAs, non-natural completion, wrong
provider identity, duplicate round IDs, invalid archive bytes, and stale index
revisions. Missing transport or Advisor output is an evidence gap; it does not
become an approval failure.

## Deletion condition

Delete this Skill when a reviewed external-review boundary preserves Agentify's
at-most-once ledger, exact archive bytes, blind divergent ordering, local
synthesis, and handoff authority without a second sender or state writer.
