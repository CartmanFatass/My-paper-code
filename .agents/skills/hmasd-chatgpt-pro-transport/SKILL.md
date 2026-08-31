---
name: hmasd-chatgpt-pro-transport
description: "Use when another session supplies a research direction ID, an exact prompt, and optional reference attachments for ChatGPT Pro web transport, especially when model selection, delayed loading, ambiguous sends, long generation, scheduled wake-ups, or exact response archiving must be controlled."
---

# HMASD ChatGPT Pro Transport

Use this skill only as a transport operator. The calling session owns the evidence
scope and exact prompt wording; a complete Pro response owns the final decision for
its declared node. This skill validates the supplied scope, binds it to the exact
persistent ChatGPT conversation, and preserves transport/response evidence without
interpreting or overriding the decision. The transport task is the execution owner:
after it accepts a handoff it performs the complete transport, wait, archive, and
return-receipt lifecycle in this task. It is not an advice-only monitor and it does
not delegate the same handoff recursively.

**REQUIRED SUB-SKILL:** use `browser:control-in-app-browser` for the in-app browser.

## Input contract and authority

Accept a request object containing `request_id`, `direction_id`, `direction_ids`,
`workflow_node`, `conversation_binding_key`, `decision_authority=pro_final`, and
exactly one body source:

- `prompt` for exact clipboard-paste mode; or
- absolute `prompt_path` for file-upload mode, plus an exact `companion_prompt` only
  when the page requires text before its Send control becomes enabled.

The handoff must also provide the exact originating Codex `source_thread_id` for
the completion receipt. Treat it as routing metadata, never as scientific content;
do not infer it from the provider conversation URL or from prose.

An optional `reference_paths` list contains one or more absolute reference files
(for example the authoring skill's `REFERENCE_FILES.md`). Validate and hash every
reference before transport. There is no strict filename or orthogonality requirement:
the provider may normalize/display attachment names, and references may be attached
or otherwise supplied in the page-supported form. Record the provider-visible names
and preserve the byte hashes and intended order where the page permits. The
one-to-one binding-key/conversation rule still applies to the body and all
references together.

The allowed decision-node bindings are exact:

- `em_innovator` -> `em:<direction_id>:innovator` with exactly one direction;
- `em_convergence` -> `em:<direction_id>:convergence` with exactly one direction;
- `portfolio_decision` -> `portfolio:cross_direction` with
  `direction_id=portfolio` and a non-empty registered `direction_ids` scope.

An optional `requested_conversation_id` prebinds an existing provider conversation.
Otherwise the first concrete provider conversation observed for the binding key is
persisted. When one is supplied, navigate to its exact `/c/<uuid>` URL and refuse
any different observed conversation. One provider conversation ID may back only
one decision binding key; Innovator, Convergence, and Portfolio must never share a
conversation. The preferred input is a canonical packet produced by
`scripts/materialize_packet.py`. The packet is one logical object identified by
`packet_id` and a `PACKET_MANIFEST.json`; the body and references may be separate
physical files only because the page upload interface requires it. The manifest is
the authority for order, source path, byte count, and hash. Companion text is
transport UI text and is never a second scientific packet. Legacy `prompt_path` /
`reference_paths` input remains accepted, but the operator must materialize and
record the canonical manifest before page actions.

Reject missing/ambiguous content, unknown direction IDs, relative upload paths, and
missing/duplicate reference files. Validate the single `direction_id` against both
Portfolio and `DIRECTION.md` for EM nodes; for Portfolio validate every
`direction_ids` member. Do not choose a scope or rewrite the supplied prompt. Use
`scripts/validate_request.py` before page actions.

Persist the registry described in [references/state-schema.md](references/state-schema.md).
It is a one-to-one map from `conversation_binding_key` to provider conversation ID.
The same direction therefore has two independent EM conversations, while Portfolio
has one conversation shared across direction scopes. Only one request may be active
per binding; a later round reuses the same conversation after the preceding request
is archived. If a mapping exists, continue that conversation; never create a replacement because
of a timeout, stale tab, model mismatch, or uncertain click. A new mapping is bound
only after a concrete `/c/<uuid>` URL is observed.
Use `scripts/bind_conversation.py` for the first binding and every idempotent retry;
it refuses a different conversation ID for an already-bound key.

## Browser and model preflight

Use the existing in-app-browser binding. Claim an explicitly mentioned user tab by
exact title/URL/provider identity; otherwise create one agent tab and retain its
lease for the whole request. Navigate once to `https://chatgpt.com/` only when no
usable tab is available. Wait for the visible composer rather than guessing a fixed
load delay. After every navigation, reload, click, or upload, take a fresh DOM state
check before the next action. The tab handle is a lease, not the conversation
identity; persist `conversation_id` and `provider_url` before handing off to a wake.

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
upload completion state. Record file size/hash before upload. Before each upload
action, obtain the required action-time confirmation for the exact local file(s) and
the `chatgpt.com` destination when it is not already present for this invocation.
This is the only transport-level confirmation gate; do not add another confirmation
immediately before Send (subject to any higher-level browser safety confirmation).
If `reference_paths` are present, upload them before Send (in one chooser when
`isMultiple()` is true, or in separate chooser cycles otherwise) and verify every
expected file by its recorded size/hash and conversation association. A provider
filename suffix or other display normalization is informational, not a blocker. If
the upload is still pending, do not send. Do not invent companion text when
file-only Send is disabled; stop and request the exact companion text from the
calling session.

For a canonical packet, preserve the exact body bytes and every supplied reference
hash. Upload the manifest-selected physical files in the recorded order when the
page requires attachments. A provider filename suffix or normalization is an
observation to record, not a reason to rewrite the packet or fail the send.

After the verified packet is ready, click Send once. Record `SEND_ATTEMPTED`, then re-observe:

- `/c/<uuid>` plus a visible exact user-message node is `SEND_CONFIRMED`;
- a URL change without the user node is `SEND_UNCERTAIN`;
- an unchanged URL, unchanged composer, enabled Send control, and no user node are
  the only positive evidence that a pre-send click failed and may permit one retry
  with the same request/idempotency key.

For a packet with references, `SEND_CONFIRMED` additionally requires every expected
file group and its recorded hash to be associated with the bound conversation; the
provider-visible filename need not equal the local basename. Never retry an uncertain
or mismatched send, never open a second conversation, and never silently alter
whitespace, file selection, reference order, or prompt text.

## Long generation and asynchronous wake-up

Once `conversation_id` is bound, persist it before waiting and mark the tab for
handoff. The durable identity is the exact `conversation_id` and `provider_url`;
the tab lease remains active while generation is pending. During Pro generation,
`Pro thinking`, `Stop answering`, a browser timeout, or `Answer now` are non-terminal
observations. Never click `Answer now`, Retry, Continue, or Stop. A timeout becomes
`WAITING_UNKNOWN`, not a send failure.

Use one existing heartbeat automation as a bounded wake-up, normally
`FREQ=MINUTELY;INTERVAL=15`; never use `INTERVAL=1` busy polling. Each wake acquires
one per-conversation lock, reuses the active tab lease when it is valid, performs
one bounded DOM status read, persists the observation, and returns. A 20–60 minute
generation may span several wakes. At 60 minutes, persist the same conversation and
mark `WAITING_TIMEOUT`; keep the tab active for recovery and human visibility. Do
not create a replacement conversation, declare a scientific failure, or close the
tab merely because the executor turn or one wake ended. If the page handle is lost,
reclaim one tab by the exact persisted provider URL and update the lease; the old
tab ID is never used as identity. A user-owned or explicitly mentioned tab remains
open unless the user has separately authorized its closure.

Natural completion requires an explicit completed status, no active generation
control, and a complete assistant message in the same conversation. Capture the
assistant node exactly; partial streamed text is not an archive.

## Archive and tab lifecycle

Write one canonical packet manifest plus exact UTF-8 prompt, reference-file, and
response artifacts and a transport-fact file containing workflow node, binding
key, direction scope, conversation, tab, model, source mode/path, timestamps,
hashes, reference hashes, send evidence, wait status, and archive status.
Deduplicate by `(conversation_binding_key, request_id, conversation_id,
response_sha256)`; an identical existing archive is
idempotent, while a different response for the same key is a conflict and must not
overwrite anything. Cancel/disable the heartbeat only after durable archive
verification. After a complete response is captured, hash-verified, and durably
archived, close the agent-created tab and set its ephemeral `tab_id` to null (or
`tab_lifecycle=CLOSED`) while retaining the conversation URL/ID and archive paths.
The executor turn ending, a heartbeat wake returning, or a timeout is never
sufficient reason to close it; closure occurs only after natural completion and
archive verification.

### Completion receipt to the originating session

After a response is durably archived and hash-verified, call
`scripts/transport_contract.py:stage_receipt` to stage exactly one structured
completion receipt in the persisted outbox, then send it once to the supplied
`source_thread_id` using `mcp__codex_app__send_message_to_thread`. The receipt must contain at least
`request_id`, `workflow_node`, `conversation_binding_key`, `direction_id`,
`direction_ids`, `state=ARCHIVED`, `conversation_id`, `provider_url`, response
SHA-256, archive paths, and heartbeat retirement status; it must report
transport facts only and must not add scientific interpretation. Record the receipt
timestamp, destination thread ID, deterministic message key, attempt count, and
delivery status in the registry or transport-fact file. Treat the logical receipt as
idempotent; on uncertain delivery, do not create a duplicate or send to another
session—record `RETURN_RECEIPT_UNCERTAIN` and report it. If `source_thread_id` is
missing or no longer resolves, archive remains valid but mark
`RETURN_RECEIPT_BLOCKED` and report the exact routing gap. For an explicit
terminal/blocker state with no archive, call `stage_blocker_receipt` and send the
analogous structured blocker receipt when the source thread is available.

The only configured send-failure fallback is the exact source session
`codex://threads/01a04f5a-1c9f-7331-b1d9-249fb767362e`. It is routing metadata only.
Use it only when the request explicitly carries `fallback_enabled=true` and the
primary receipt send has a definite `FAILED`/`BLOCKED` result, or when the primary
`source_thread_id` is absent at staging time. An ordinary request without the flag
remains `RETURN_RECEIPT_BLOCKED` when its source is absent. Never use or reroute the
fallback for `UNCERTAIN`, `SEND_UNCERTAIN`, direction mismatch, or unknown
conversation identity. Persist fallback status and return control immediately after
a bounded attempt; a blocked subagent send must not hold the transport task open.

### Heartbeat retirement at task close

Persist the heartbeat automation ID and status with the transport facts. A shared
heartbeat remains active while any mapped conversation still needs a bounded wake
(`WAITING_GENERATION`, `WAITING_HEARTBEAT`, `ARCHIVE_PENDING`, or a recoverable
`WAITING_TIMEOUT`). When every conversation in this transport task is durably
`ARCHIVED`, or is an explicit terminal/blocker state with no scheduled recovery,
disable the existing heartbeat exactly once (for example by updating it to `PAUSED`)
and record the retirement timestamp and verification. If one heartbeat multiplexes
multiple directions, do not retire it when only one direction finishes; retire it
only after the last pending record is closed. Never leave a task-close heartbeat
active after the task has no pending recovery work, and never create a replacement
heartbeat merely to avoid retiring the existing one.

When a later wake needs a lost or stale page, create at most one recovery tab in the
same in-app browser and navigate to the persisted exact `provider_url`. Verify the
loaded URL/conversation and direction before reading; never call `tabs.get()` on the
old handle and never create a new conversation. Keep the recovered tab active while
the conversation is pending. After natural completion and archive, close it under
the rule above. A user-owned/explicitly mentioned tab is not closed unless the user
has authorized closing that tab.

### Monitor identity and observations

The monitor is keyed by `request_id|conversation_binding_key|conversation_id|provider_url`
(using `legacy:<direction_id>` only for legacy requests).
Every wake must record the observed URL, page state, completion controls, and an
optional monitor cursor. `tab_id`/`tab_handle` may be stored only as the current
lease handle. A tab ID without an exact URL/conversation observation is not monitor
evidence; it must produce `MONITOR_IDENTITY_MISMATCH` and stop recovery.

## Stop conditions

Stop and report the exact state on unknown direction, missing prompt, failed Pro
verification, incomplete upload, uncertain/mismatched submission, stale/ambiguous
conversation identity, partial response, archive conflict, heartbeat overlap, or a
recovery URL that no longer resolves to the bound conversation.
Transport facts never imply scientific conclusions.
