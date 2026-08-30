---
name: hmasd-browser-transport
description: Execute one exact browser transport request and return its receipt.
---

# HMASD Browser Transport Service

## Purpose

`BrowserTransport` carries one frozen prompt to one exact provider target, observes the causal assistant response, and returns mechanical transport facts. It never interprets provider content or creates scientific or workflow authority.

The authorization unit is one provider-visible user message equal to the frozen prompt. Tabs, invocations, local retries before Send, and observation calls are not additional messages.

## Frozen request

Accept one meaning-complete request that fixes:

- assignment, requester, direction/stage when applicable, and return route;
- provider, transport mode, `product_model`, and `reasoning_effort` as separate axes; current ChatGPT requests require `product_model: GPT-5.6 Sol` and `reasoning_effort: Pro`;
- `NEW` or the exact target conversation URL and ID;
- exact prompt path/SHA and exact raw response path;
- immutable Agentify operation ID, idempotency key, request fingerprint, stable key, operation reference, and timestamps.

Reject a missing, contradictory, unreadable, wrong-account, or wrong-target request before Send. Never compose, shorten, wrap, append to, or otherwise change the prompt.

The provider conversation is the durable external target; a browser tab is only its replaceable view.

## Receipt

Persist and return the minimal snake-case receipt facts directly:

- immutable provider and target axes, prompt and response identity, `operation_id`, `idempotency_key`, `request_fingerprint`, `stable_key`, `operation_ref`, and positive epoch-millisecond `created_at` and `updated_at`;
- `send_attempted` plus nullable positive epoch-millisecond `send_attempted_at`;
- nullable `observed_conversation_url`, `observed_conversation_id`, `provider_user_message_id`, and `provider_assistant_message_id`;
- nullable exact `archive` and nullable `error` containing one code.

Only these receipt invariants apply: `send_attempted: false` requires a null timestamp; `send_attempted: true` requires its timestamp; a provider user-message ID requires `send_attempted`; an assistant-message ID requires the user-message ID; an archive requires the assistant-message ID. Immutable identity never changes, `send_attempted` never returns to false, and observed IDs and archive are append-only.

The operation receipt is separate from raw `response.md`. Raw provider bytes are never a JSON envelope.

## Direct execution

Use one short linear path:

1. Validate the exact request and reread/fingerprint the prompt bytes.
2. Open the exact provider target, verify account, product model, reasoning effort, conversation, and visible composer, then insert the exact prompt.
3. Re-observe the current page and resolve one visible, hit-tested native Send control; persist `send_attempted: true` immediately before one hit-tested native pointer activation and write `send_attempted_at` in the same receipt update. Use zero DOM clicks and never submit with Enter or script execution.
4. Observe the provider user turn and record its exact message ID and observed conversation URL/ID.
5. Wait for the causal assistant turn, record its exact message ID, and read the stable response bytes.
6. Write the exact raw response, fingerprint and reread it, then persist the exact archive receipt.

A failure before `send_attempted` remains retryable automatically on the same immutable operation; after `send_attempted`, never activate Send again and only observe the existing provider turn and response. This direct fact guard is the complete unknown-never-resend rule.

For every page mutation use `observe -> interpret -> act -> verify`. Pre-Send sign-in, overlay, navigation, loading, stale-tab, selector, or residual-composer errors may be repaired in place while `send_attempted` remains false. A browser tab is only a replaceable view; it is not conversation identity or send authority.

## Exact archive

A complete receipt includes the exact provider, model and effort, operation identities, target and observed conversation identities, prompt identity, user and assistant message IDs, response path, and:

```json
{
  "archive": {
    "path": "docs/external-review/directions/<direction>/<round>/<stage>/<provider>/response.md",
    "sha256": "<raw-response-sha256>",
    "size_bytes": 123,
    "projection": "exact",
    "verified_at": 1788000000000
  }
}
```

The current external-review `operation_ref.json` uses schema version 4. Never rewrite historical receipts or raw responses, infer identity from response prose, normalize provider bytes, or publish an archive whose reread SHA/size differs.

## Returned result

Return the common v2 envelope with `role: hmasd-browser-transport`, `logical_identity: BrowserTransport`, the inbound assignment/generation, and `kind: transport`. Its payload contains the assignment envelope and the minimal receipt facts above. It contains no derived transport status.

The service writes no scientific, engineering, Portfolio, registry, external-index, or runtime-map authority. Agentify owns the mutable operation ledger; HMASD validates and projects its exact receipt.
