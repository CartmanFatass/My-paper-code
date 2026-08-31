---
name: hmasd-chatgpt-pro-transport
description: "Use when another session supplies a research direction ID, an exact prompt, and optional separate reference attachments for ChatGPT Pro web transport, especially when model selection, delayed loading, ambiguous sends, long generation, scheduled wake-ups, or exact response archiving must be controlled."
---

# HMASD ChatGPT Pro Transport

Use this skill only as a transport operator. The calling session owns the research
direction, prompt wording, scientific interpretation, and lifecycle decision. This
skill validates the supplied direction, binds it to one ChatGPT conversation, and
preserves transport/response evidence.

**REQUIRED SUB-SKILL:** use `browser:control-in-app-browser` for the in-app browser.

## Input contract and authority

Accept a request object containing `request_id`, `direction_id`, and exactly one
body source:

- `prompt` for exact clipboard-paste mode; or
- absolute `prompt_path` for file-upload mode, plus an exact `companion_prompt` only
  when the page requires text before its Send control becomes enabled.

An optional `reference_paths` list contains one or more absolute reference files
(for example the authoring skill's `REFERENCE_FILES.md`). These are separate
attachments in the same conversation, not extra body text. Validate and hash every
reference before transport; preserve their order and names. The one-to-one
direction/conversation rule applies to the body and all references together.

Reject missing/ambiguous content, unknown direction IDs, relative upload paths, and
missing/duplicate reference files. Validate `direction_id` against both
`docs/research/portfolio/PORTFOLIO.md` and
`docs/research/candidates/<direction_id>/DIRECTION.md`; do not choose a direction or
rewrite the supplied prompt. Use `scripts/validate_request.py` before page actions.

Persist the registry described in [references/state-schema.md](references/state-schema.md).
It is a one-to-one map: one direction ID has at most one provider conversation ID.
If a mapping exists, continue that conversation; never create a replacement because
of a timeout, stale tab, model mismatch, or uncertain click. A new mapping is bound
only after a concrete `/c/<uuid>` URL is observed.
Use `scripts/bind_conversation.py` for the first binding and every idempotent retry;
it refuses a different conversation ID for an already-bound direction.

## Browser and model preflight

Use the existing in-app-browser binding. Claim an explicitly mentioned user tab by
exact title/URL/provider identity; otherwise create one tab and navigate once to
`https://chatgpt.com/`. Wait for the visible composer rather than guessing a fixed
load delay. After every navigation, reload, click, or upload, take a fresh DOM state
check before the next action.

Identify the model from the page, never from the account plan. Require visible
`Pro`, then open the selector and require the `Pro, 5 of 5.` indicator and the
checked underlying model shown by the page (currently `GPT-5.6 Sol`). The closed
control is labelled `Pro`; while open it may be labelled `Thinking effort`, so use
state-based fallback locators rather than one hard-coded accessible name. If the
required Pro state cannot be verified, stop before typing or sending. If a switch is
needed, select Pro, wait for the resulting page update, and re-check the composer
and exact input.

## Exact input and one-send rule

For paste mode, write the exact UTF-8 text to the tab clipboard, focus the composer,
and use the platform paste key. Verify the composer text before sending. Do not use
`locator.fill()` for transport: the live test produced a duplicated/malformed user
message node even though a response was returned.

For upload mode, start `waitForEvent("filechooser")` before opening the visible
upload control, set the absolute file path, and wait for the explicit file group and
filename state. Record file size/hash before upload. If `reference_paths` are
present, upload them before Send (in one chooser when `isMultiple()` is true, or in
separate chooser cycles otherwise) and verify every expected filename in the same
composer. If the upload is still pending, do not send. Do not invent companion text
when file-only Send is disabled; stop and request the exact companion text from the
calling session.

For the authoring packet, the preferred transport is exact clipboard paste of
`PROMPT_BODY.md` plus a separate upload of `REFERENCE_FILES.md`. Never merge the
manifest into the body, upload it in another conversation, or silently omit it.

Immediately before an outbound send, obtain the required action-time confirmation
for the exact content and `chatgpt.com` destination when it is not already present
for this invocation. Click Send once. Record `SEND_ATTEMPTED`, then re-observe:

- `/c/<uuid>` plus a visible exact user-message node is `SEND_CONFIRMED`;
- a URL change without the user node is `SEND_UNCERTAIN`;
- an unchanged URL, unchanged composer, enabled Send control, and no user node are
  the only positive evidence that a pre-send click failed and may permit one retry
  with the same request/idempotency key.

For a packet with references, `SEND_CONFIRMED` additionally requires every expected
reference filename/file group and its recorded hash to be associated with that same
user turn. Never retry an uncertain or mismatched send, never open a second
conversation, and never silently alter whitespace, file selection, reference order,
or prompt text.

## Long generation and 15-minute wake-up

Once `conversation_id` is bound, persist it before waiting and mark the tab for
handoff. The tab handle is ephemeral; the durable identity is the exact
`conversation_id` and `provider_url`. During Pro generation, `Pro thinking`, `Stop
answering`, a browser timeout, or `Answer now` are non-terminal observations. Never
click `Answer now`, Retry, Continue, or Stop. A timeout becomes `WAITING_UNKNOWN`,
not a send failure.

Use the heartbeat automation with `FREQ=MINUTELY;INTERVAL=15` as a wake-up, not a
busy-wait loop. Each wake performs one bounded status read under a per-conversation
lock and returns. A 20–60 minute generation may therefore span several wakes. At
60 minutes, persist the same conversation and mark `WAITING_TIMEOUT`; if the
conversation ID is known and the tab is agent-created, close the temporary tab
after recording that state and let the next wake recover from the exact provider
URL. Do not create a replacement or declare a scientific failure. If identity is
not known, keep the tab for human attention rather than closing an unrecoverable
submission. A user-owned or explicitly mentioned tab remains open unless the user
has separately authorized its closure.

Natural completion requires an explicit completed status, no active generation
control, and a complete assistant message in the same conversation. Capture the
assistant node exactly; partial streamed text is not an archive.

## Archive and tab lifecycle

Write separate exact UTF-8 prompt, reference-file, and response files plus a
transport-fact file
containing direction, conversation, tab, model, source mode/path, timestamps, hashes,
reference hashes, send evidence, wait status, and archive status. Deduplicate by
`(direction_id, conversation_id, response_sha256)`; an identical existing archive is
idempotent, while a different response for the same key is a conflict and must not
overwrite anything. Cancel/disable the heartbeat only after durable archive
verification. After a complete response is captured, hash-verified, and durably
archived, close the agent-created tab immediately and set its ephemeral `tab_id` to
null (or `tab_lifecycle=CLOSED`) while retaining the conversation URL/ID and archive
paths. Do not keep a completed page alive merely for convenience.

When a later wake needs a closed or stale page, create a fresh temporary tab in the
same in-app browser and navigate to the persisted exact `provider_url`. Verify the
loaded URL/conversation and direction before reading; never call `tabs.get()` on the
old handle and never create a new conversation. Close the recovered tab again after
the bounded status read or archive. A user-owned/explicitly mentioned tab is not
closed unless the user has authorized closing that tab. Mark deliverable only when
the user explicitly wants the page left visible.

## Stop conditions

Stop and report the exact state on unknown direction, missing prompt, failed Pro
verification, incomplete upload, uncertain/mismatched submission, stale/ambiguous
conversation identity, partial response, archive conflict, heartbeat overlap, or a
recovery URL that no longer resolves to the bound conversation.
Transport facts never imply scientific conclusions.
