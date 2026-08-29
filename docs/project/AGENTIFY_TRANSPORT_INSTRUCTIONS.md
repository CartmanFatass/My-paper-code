# HMASD strict Agentify transport

This is the sole current mechanics reference for HMASD external consultations. It assumes the
trusted local Codex Desktop project. It creates no HMASD authentication, receipt, retry ledger,
registry, router, or UI checklist. `AGENTS.md` is the only human-readable glossary for shared
transport states.

## Objects and ownership

A tab is not a conversation. A tab is a replaceable browser view; the provider conversation is the
persistent ChatGPT/Gemini object named by its URL and conversation ID. A strict operation is one
attempt to inject one frozen prompt into one provider conversation. None of these is a top-level
WORK or an EM material cycle.

The parent supplies one exact frozen prompt file, its `promptPath`, the purpose, provider, required
visible model, conversation binding or new-conversation request, owner-selected `responsePath`,
observation bound, and stop condition. For research, EM writes cohesive natural language and may
tell GPT-5.6 Pro to use its GitHub connector against an origin-reachable commit and exact
repository-relative references. Repository code is a scientific reference, not a request for
general code review.

The transport must not compose, summarize, append, truncate, translate, wrap, or rewrite the
prompt. It must not paste a `[WORK]`, `[RESULT]`, state table, JSON packet, command receipt, or shell
output around it. It owns only navigation, readiness, provider/model selection, the single Send,
provider-visible fidelity, natural completion, response availability, and exact archive facts.

## Open and verify the provider view

1. Read the exact frozen prompt file once and reject an empty or unreadable file before any
   send-capable call. Derive `stableKey` and `idempotencyKey` only as tool-local Agentify inputs;
   they are not task identity or durable HMASD state. The caller normally omits `promptSha256`:
   Agentify computes its internal content hash. Supply a hash only for tool-local diagnosis.
2. For an existing conversation, open its exact URL/ID in any usable tab. Replacing or closing a
   tab does not replace or close the conversation. For a new ChatGPT conversation, use the provider
   root with `conversationId=__new__` and `firstBinding=true`; Agentify records the concrete
   conversation URL/ID after the provider creates it.
3. Resolve login, CAPTCHA, blank/loading page, and stale-tab readiness without touching the
   composer. Do not block on the first stale view: reopen the same conversation in a usable tab or
   perform one other evidence-changing no-send recovery. Conversely, do not loop or follow a fixed
   UI checklist when the next action cannot distinguish a new fact.
4. Verify the actual reasoning control, not arbitrary page text. On the current ChatGPT surface the
   required reasoning control has exact visible label `Pro`; use `model="Pro"`. “GPT-5.6 Pro” names
   the requested review capability in prose but is not an invented UI-label alias. A plan/account
   badge or unrelated `Pro` menu cannot satisfy preflight. Agentify persists the exact selected
   label and semantic control route at Send; a replacement tab's current High/Pro selection is only
   the next-send state and cannot rewrite the model evidence for an already sent turn.

## One strict Send

When readiness and the exact model are established and no user waiver applies, call
`agentify_review_query` exactly once with `promptPath`, `responsePath`, exact provider/model,
conversation binding, keys, first-binding flag when applicable, and a natural-completion timeout
of up to 45 minutes. Forty-five minutes is an ordinary Pro generation window, not an error budget.
A valid unwaived assignment is not silently left unsent.

Never make a second send-capable call for that operation. Do not use ordinary `agentify_query` as
the Send path, and do not activate Retry, Continue, Answer-now, Stop-and-resend, Regenerate, or any
other response-producing control. The provider-visible user turn must equal the exact frozen prompt
file; otherwise report the input-mismatch state and isolate that operation.

## Observe and archive

After Send, further work on that operation is non-sending:

- `agentify_review_observe` reads only the durable operation fact and never touches the page.
- `agentify_review_query` with `verifyExisting=true` reopens/observes the same provider conversation
  and exact operation; it never gains Send capability.

Each page-observation call may wait up to 45 minutes. If Pro is still generating when that window
ends, retain `SENT_WAITING` and continue the same operation in a later native wait/observation; the
timeout is not a global generation deadline. A clipped tool display, response prefix, mode label,
loading view, or currently unreadable page is not completion.

`COMPLETE` is available only after the naturally completed full assistant turn is written
atomically to the exact `responsePath` and reread successfully. The MCP result returns compact
metadata and the archive path, not a potentially truncated copy of the full response. Preserve the
complete owner prompt, provider/model/conversation facts, and complete provider response without
adding scientific or engineering conclusions.

## Release the browser view

`tabId` is an ephemeral local browser resource, never the durable locator for a provider turn. At
the end of every send or observation call, close its non-default tab once either the operation is
terminal or a concrete provider conversation URL/ID is known. In particular, a `COMPLETE` operation
closes the tab only after the response archive has been written and reread. Closing the page does
not delete or stop the provider conversation; a later observation opens the same conversation ID
in a replacement tab.

`COMMITMENT_UNKNOWN`, `SENT_WAITING`, and `SENT_UNREADABLE` therefore also release the tab when the
concrete conversation ID is known. If a first-binding failure has not yielded a concrete ID, retain
that tab because it may be the only recovery handle. Zero-send and terminal mismatch/loss states
release any non-default tab. A local close failure is returned as a tab-cleanup fact; it never
changes the transport state and never supplies scientific, engineering, Portfolio, or lifecycle
meaning. Callers retain the conversation URL/ID for reentry and must not treat an old `tabId` as a
stable binding.

## Tab recovery, conversation loss, and replacement

Unknown or sent-but-recoverable operations remain bound to the same provider conversation. Open
that conversation in a replacement tab and use `verifyExisting`; a tab timeout, closed tab, root
redirect, blank DOM, login/CAPTCHA, missing list entry, or clipped response does not prove that the
conversation is lost and never authorizes another Send.

Classify the conversation as permanently lost only when all of these mechanical facts are present:

- a possible or confirmed Send exists and the exact concrete conversation URL/ID is known;
- readiness/account problems have been resolved without sending;
- the exact URL/ID was directly reopened in a replacement tab; and
- the provider then gives a stable explicit not-found, deleted, or permanently-unavailable result.

Conversation-list absence may corroborate that result but cannot prove loss by itself. If first
binding crashed with `COMMITMENT_UNKNOWN` before a concrete conversation ID was recovered, the
transport cannot infer loss and cannot resend.

An input mismatch, model mismatch, or positively lost conversation isolates the old operation and
conversation. It supplies no scientific or lifecycle judgment. Under the `AGENTS.md` owner rule,
the same frozen prompt may then receive at most one replacement strict operation in a new provider
conversation while retaining the same top-level WORK and, for EM, the same material cycle. This is
not reinjection into the old conversation. Any late content from the isolated conversation remains
quarantined and cannot complete or influence the replacement.

Renaming the WORK, assignment, operation, key, leaf, tab, or task never authorizes a duplicate.
Changing to a new provider conversation is valid only for the explicit isolated-conversation
replacement above or for a materially different owner-authored question. No local cross-task
ledger is created; native history and Agentify's strict operation record provide the facts.

## Return

Return only the transport leaf's own state field, direct mechanical fact, concrete conversation
locator, archive path or `NONE`, and limitations. An error without strict zero-send proof cannot be
called zero-send; an incomplete archive cannot be called complete. Do not map transport to
scientific status, technical acceptance, Portfolio action, lifecycle, top-level failure, or
cancellation.
