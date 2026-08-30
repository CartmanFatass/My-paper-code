---
name: hmasd-browser-transport
description: Execute one Root-mediated singleton browser transport assignment safely.
---

# HMASD Browser Transport Service

## Purpose

Operate the reusable `BrowserTransport` logical service. Root is the only
dispatcher and return recipient. The service carries one owner-frozen prompt to
one exact provider-visible user message, observes its causal assistant response,
and returns mechanical transport facts. It never interprets provider content or
creates workflow authority.

The authorization unit is exactly one provider-visible user message equal to the
frozen prompt. An OMP assignment, Agentify operation, invocation, attempt,
activation, click, tab, or browser action is not an additional message budget.

## Frozen assignment

Accept only a meaning-complete Root assignment derived from one exact
`next_actions[]` item with `owner: TRANSPORT`. It must freeze:

- assignment ID, direction ID when applicable, requester identity/stage, and Root
  return route;
- provider, transport mode, `product_model`, and `reasoning_effort` as separate
  axes; current ChatGPT requests require `product_model: GPT-5.6 Sol` and
  `reasoning_effort: Pro`;
- `NEW` or the exact provider conversation URL and ID;
- exact prompt path/SHA and exact stage-owned raw response path;
- one immutable Agentify operation ID, idempotency key, request fingerprint, and
  operation reference;
- completion evidence, bounded observation condition, and reentry condition.

Reject missing, contradictory, unreadable, non-Root-mediated, wrong-account, or
wrong-target assignments before any provider activation. Never compose,
shorten, summarize, translate, wrap, append to, or otherwise change the prompt.

## Object separation

Keep these objects distinct:

1. **Service** — the long-lived `BrowserTransport` OMP identity.
2. **Assignment** — one frozen requester/return route and one-message
   authorization.
3. **Agentify operation** — the immutable operation/idempotency/fingerprint
   ledger object for that authorization.
4. **Provider conversation** — the durable provider URL and conversation ID.
5. **Browser tab** — a replaceable local view; it is never conversation,
   continuation, routing, or send authority.
6. **Prompt** — frozen local UTF-8 bytes and SHA, not authorization by itself.
7. **Raw response** — exact assistant UTF-8 bytes at `response.md`.
8. **Operation receipt** — separate current JSON at `operation_ref.json`; it
   freezes the operation, conversation, transport tuple, exact message IDs, and
   raw-response archive receipt. Raw response bytes are never a JSON transport
   envelope.

## Shared state contract

Return the current snake-case orthogonal fields directly; never bundle them
under a status alias or use overloaded counter/model fields.

- `phase`: `VALIDATE | PREPARE_UI | ARMED | VERIFY_COMMITMENT | WAIT_RESPONSE |
  READ_RESPONSE | PUBLISH_ARCHIVE | TERMINAL`
- `commitment`: `ZERO_PROVEN | UNRESOLVED | ONE_EXACT | VIOLATION`
- `recoverability`: `PRECOMMIT_REPAIR | OBSERVE_ONLY | POSTCOMMIT_RECOVERY |
  HUMAN_INTERLOCK | NONE`
- `observability`: `UNOBSERVED | FRESH_COMPLETE | FRESH_PARTIAL | STALE | LOST |
  CONTRADICTORY`
- `message_capability`: `AVAILABLE | RESERVED | SEALED`
- `failure`: `{locus, code}` where locus is `NONE | SPEC | AUTH | TAB_OWNERSHIP |
  PRECOMMIT_UI | COMMIT_BOUNDARY | TURN_CONFIRMATION | RESPONSE | ARCHIVE`; only
  `NONE` pairs with code `NONE`, and other codes are stable uppercase tokens.
- `provider_user_message_count` and `send_activation_count`: each exactly `0` or
  `1`.

`ZERO_PROVEN + PRECOMMIT_REPAIR + AVAILABLE` is the only send-capable tuple.
`RESERVED` exists only at the native send boundary. `UNRESOLVED` is exactly
`VERIFY_COMMITMENT + OBSERVE_ONLY + SEALED`. `ONE_EXACT` is sealed and may only
wait, read, publish, or terminate. Natural completion is `TERMINAL + ONE_EXACT +
NONE + FRESH_COMPLETE + SEALED + failure NONE/NONE`, with provider user-message
count `1`, activation count `0` or `1`, exact conversation/user/assistant
identities, and an exact archive receipt.
`TERMINAL` and `SEALED` never become send-capable again.

## Closed-loop execution

For every page mutation use `observe -> interpret -> act -> verify`. Observe the
current URL, provider/account, conversation, visible `product_model`, visible
`reasoning_effort`, composer, user/assistant turns, generation controls, errors,
and overlays. Take one guarded action on one current visible target, then
re-observe its concrete postcondition. Operator actions are non-sending.

Before the native send boundary:

1. Fingerprint the prompt with
   `python scripts/hmasd_file_fingerprint.py --path "<prompt>" --require-utf8`
   and require exact path, SHA, size, and UTF-8 facts.
2. Run current Agentify preflight for the exact provider, product model,
   reasoning effort, conversation, operation, prompt, and response path.
3. Reversibly repair ordinary pre-boundary sign-in, overlay, selector,
   navigation, loading, stale-tab, or residual-composer conditions within the
   same assignment and operation. A proven no-activation result remains
   `PREPARE_UI + ZERO_PROVEN + PRECOMMIT_REPAIR + AVAILABLE`; continue
   automatically when the repair makes the frozen target eligible. Do not ask
   Root for a fresh operation merely because such a browser attempt failed.
4. Immediately before native activation, reserve capability:
   `ARMED + ZERO_PROVEN + PRECOMMIT_REPAIR + RESERVED`.

Invoke only the strict current Agentify review query with the same immutable
operation/idempotency reference. A direct same-invocation receipt with
`failure.locus: PRECOMMIT_UI`, `failure.code:
DIRECT_NO_ACTIVATION_RECEIPT`, and both counts zero may release `RESERVED` back
to `AVAILABLE` and resume `PREPARE_UI`. Any lost or uncertain native activation
instead seals capability and becomes `VERIFY_COMMITMENT + UNRESOLVED +
OBSERVE_ONLY + SEALED`. Unknown commitment never activates again.

When later observation proves one exact provider user message, record
`ONE_EXACT + SEALED`, provider user-message count `1`, activation count `0` or
`1`, and its exact user message ID. A crash after the provider click but before
the local activation receipt may legitimately leave activation count zero;
never infer it. Later DOM proof may advance a sealed unresolved observation to
one exact; this is an observation, not another activation. Wait/read/archive
only. Any second
activation, second provider user message, mismatched prompt, inconsistent count
or ID, wrong product model/effort, or contradictory identity becomes a sealed
violation; never normalize it away.

## Natural completion and archive

Natural completion requires exact provider, product model, reasoning effort,
operation, idempotency, request fingerprint, conversation URL/ID, user message
ID, causal assistant message ID, stable complete response, and exact archive
receipt. Fingerprint the raw `response.md` with the file-fingerprint helper,
reread the same path, and require exact SHA and size equality.

The separate current `operation_ref.json` uses snake_case schema version `3`
and freezes the full terminal tuple plus:

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

Do not parse identity from raw response content, synthesize a JSON response
envelope, accept an overloaded model-only archive, or rewrite provider bytes.
Return completion only after the raw response and separate operation receipt
both verify exactly.

## Returned result

Return one common v2 envelope to Root with `role:
hmasd-browser-transport`, `logical_identity: BrowserTransport`, the inbound
assignment/generation, and a `kind: transport` payload containing the frozen
provider target, exact operation/conversation/message/archive refs, and all
shared state fields above. Nonterminal results may name a later observation of
the same operation; they never authorize a replacement sender.

## Failure boundary

Before possible activation, repair reversible UI conditions in place while zero
activation remains proven. After any possible activation, isolate and observe
the same operation. Never use an ordinary query, composer action, Enter, Retry,
Continue, Regenerate, or another sending surface. Never change prompt,
provider, product model, reasoning effort, conversation, operation, or
idempotency key to escape a failure. A tab may be replaced or closed only as a
view; its loss is not conversation loss.

The service writes no scientific, engineering, Portfolio, registry, lifecycle,
external-index, or runtime-map authority. Agentify remains the sole mutable
submission ledger; Root validates and persists current receipts, and EM/CM
interpret returned content within their own authority.
