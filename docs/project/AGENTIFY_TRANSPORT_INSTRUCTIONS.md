# Agentify tool argument reference

This file is a compact reference for the current Agentify call surface. It is not a transport
workflow, role method, status authority, or recovery policy. The complete HMASD transport method is
`.agents/skills/hmasd-agentify-transport/SKILL.md`; shared transport-state meanings are in
`AGENTS.md`. `AGENTS.md` is the only human-readable glossary for shared transport-state meanings.

## Provider objects

- `conversationId` or the concrete conversation URL identifies the persistent provider
  conversation.
- `tabId` identifies only an ephemeral browser view. Closing a tab does not delete or stop the
  provider conversation.
- On the current ChatGPT surface the required reasoning-control label is exactly `Pro`; pass
  `model="Pro"`. Account badges or unrelated page text do not establish this selection.

## `agentify_review_query`

The strict call accepts the exact file-backed request and archive destinations:

- `promptPath`: readable path containing the complete provider-visible user prompt;
- `responsePath`: owner-selected path for the complete assistant response archive;
- provider and exact visible `model` label;
- an existing conversation binding, or `conversationId="__new__"` with `firstBinding=true`;
- tool-local `stableKey` and `idempotencyKey` values;
- the bounded observation timeout, which may be as long as 45 minutes for a Pro turn; and
- `verifyExisting=true` when reopening and observing an already bound operation without Send
  authority.

The caller normally omits `promptSha256`; Agentify computes its own internal content hash. Supplying
that argument is reserved for tool-local diagnosis. Tool keys and hashes are not HMASD task
identity or durable control state.

For a new conversation, first binding records the concrete provider conversation ID after the
provider creates it. For an existing conversation, pass its concrete binding rather than relying on
an old tab.

## `agentify_review_observe`

`agentify_review_observe` reads the stored fact for the same strict operation without navigating or
sending. Use its operation identifier and idempotency binding exactly as returned by the original
strict call.

## Returned facts and archive

Agentify returns compact operation metadata, including the send/observation fact, provider/model
evidence, concrete conversation locator when available, archive status, archive path, and any
failure predicate. A compact or clipped tool display is not the full response.

When natural completion is observed, the complete assistant turn is written atomically to
`responsePath` and reread before archive success is reported. The transport method, not this
argument reference, determines how those facts map to an HMASD transport state or what action is
allowed next.
