---
name: hmasd-agentify-transport
description: Use only when an HMASD transport leaf is explicitly assigned one owner-frozen external review operation.
---

# HMASD Agentify Transport

Transport and observe one owner-authored prompt. The parent retains every scientific or engineering
judgment. This skill is the complete transport-method authority. Consult
`../../../docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md` only when the current Agentify tool
argument surface is needed; that reference defines no workflow decision.

## Freeze the operation

Require one exact frozen prompt file and its `promptPath`, purpose, provider, required visible model,
existing conversation URL/ID or new-conversation request, owner-selected `responsePath`, observation
bound, and stop condition. Reject missing or unreadable inputs before a send-capable call.

The transport must not compose, shorten, summarize, append, truncate, translate, wrap, or interpret
the prompt. Do not add a WORK/RESULT packet, JSON, receipt, shell output, or commentary. Stable keys
and internal content hashes are tool-local inputs, never HMASD task identity, authorization, or
durable workflow state.

## Open and verify

A tab is not a conversation. A tab is a replaceable browser view; the provider conversation and its
conversation ID persist after that tab closes. Open the exact existing conversation in any usable
tab, or open the provider root for a new provider conversation and let Agentify record the concrete
conversation ID after first binding.

Resolve login, CAPTCHA, blank/loading view, or stale-tab readiness without touching the composer.
Use an evidence-changing no-send recovery when necessary; do not loop through a fixed UI ritual or
repeat the same failed action without a new observable premise.
Verify the actual visible reasoning control and required model, not arbitrary page text, account
badges, or an old tab's selection.

## Send exactly once

When the view and model are ready and no waiver applies, call `agentify_review_query` exactly once
with the exact `promptPath`, `responsePath`, provider/model, conversation binding, keys, and
first-binding flag when applicable. Use a natural completion window of up to 45 minutes; this is an
ordinary Pro reasoning window, not a global deadline or retry budget. Never call ordinary
`agentify_query` for Send and never activate Retry, Continue, Answer-now, Stop-and-resend,
Regenerate, or another response-producing control.

The provider-visible user turn must equal the exact frozen prompt file. If it differs, return the
input-mismatch state and isolate that operation. If the visible selected model differs, isolate the
model-mismatch operation. Never make a second send-capable call for the same operation.

## Observe and archive without sending

After Send, every action is non-sending:

- `agentify_review_observe` reads the durable operation fact without touching the page.
- `agentify_review_query` with `verifyExisting=true` reopens and observes the same provider
  conversation and operation; it has no Send authority.

If generation is still live after an observation window, retain the waiting transport fact and
continue the same operation later. A timeout, clipped display, prefix, loading view, or unreadable
page is not natural completion. Mark COMPLETE only after the naturally completed full assistant
turn is written atomically to the exact `responsePath` and reread successfully. Return the archive
path and compact metadata; never substitute a truncated tool preview for the archive.

## Release and recover browser views

Close a non-default tab after each call once the operation is terminal or a concrete provider
conversation URL/ID is known. For COMPLETE, close only after archive write and reread. Waiting,
commitment-unknown, and sent-unreadable facts also release the tab when the conversation ID is
known. If first binding failed without a concrete ID, retain the tab as the only recovery handle.
Closing a tab does not stop or delete provider work; later observation reopens the same conversation
ID. A tab-close failure is only a cleanup limitation and never changes transport or scientific
meaning.

Do not infer conversation loss from a closed tab, timeout, root redirect, blank DOM, CAPTCHA,
missing conversation-list entry, or clipped response. CONVERSATION_LOST requires the known exact
conversation URL/ID to be reopened on the same account after readiness recovery and the provider to
return a stable explicit not-found, deleted, or permanently unavailable result.

Unknown or recoverable sent states remain on the same operation and conversation. An input/model
mismatch or positively lost conversation isolates that operation and its conversation. Return the
exact transport state; this leaf cannot authorize a replacement or infer the parent's response. If
the parent later supplies a separately authorized strict operation, treat it only as the new frozen
assignment supplied. Late content from an isolated conversation stays quarantined and cannot be
used for another operation. Renaming a key, operation, leaf, task, or tab creates no send authority.

For `ZERO_SEND_FAILED`, return the exact no-send evidence and failure premise. A later assignment is
eligible only after its parent supplies a concrete evidence-changing non-sending repair; this leaf
does not impose an attempt count or invent that repair. The same unchanged failure returns
`ZERO_SEND_FAILED` again without a Send. This rule never applies to an unknown or possible Send.

## Return

Return only the transport leaf's own state field from `../../../AGENTS.md`, direct mechanical fact,
concrete conversation locator, archive path or NONE, and limitations. An error without strict
zero-send proof is not zero-send; an incomplete archive is not complete. Never infer any parent or
owner disposition from a transport fact.
