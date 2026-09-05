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

Use the available `mcp__cua_repl` browser API. Initialize it using the tool's documented
entry point, then read the returned documentation before acting. Use only available
browser methods; an unavailable export or locator API is not permission to resend.

## Input contract and authority

Accept a request object containing `request_id`, `direction_id`, `direction_ids`,
`workflow_node`, `conversation_binding_key`, `decision_authority=pro_final`, and
exactly one body source:

- `prompt` for exact clipboard-paste mode; or
- absolute `prompt_path` for file-upload mode, plus an exact `companion_prompt` only
  when the page requires text before its Send control becomes enabled.

Every canonical handoff must provide the exact creator Codex `source_thread_id`, its
exact `parent_thread_id`, and an explicit `operator_thread_id`. The default operator
is the project singleton declared in `.codex/hmasd-transport.toml`.
Treat all three as routing metadata, never as scientific content;
do not infer them from the provider conversation URL, a task title, or prose.
`parent_thread_id` is the sole completion or terminal-blocker receipt destination.
`source_thread_id` identifies the handoff author but is not a receipt destination.
`operator_thread_id` is the reusable Codex execution endpoint and never a
provider-conversation binding or receipt destination. Default canonical handoffs must
declare `dispatch_mode=REUSE_SINGLETON`, `operator_reuse_required=true`,
`operator_model=gpt-5.6-luna`, and `operator_thinking=xhigh`; validate all four and
reject a singleton ID that differs from the project config. Historical in-flight
`CREATE_ON_DEMAND` requests may finish, but they do not authorize another task creation.

When the owner explicitly asks Root/the caller to operate the browser personally,
accept `dispatch_mode=CALLER_DIRECT`, `operator_thread_id=source_thread_id`, and the
exact `owner_execution_instruction`. No singleton dispatch occurs. The caller follows
this same transport lifecycle. When caller and parent are the same task, archive and
intake locally without sending a message to itself; otherwise return the usual parent
receipt. This exception changes the executor, not the provider model or decision node.

An optional `reference_paths` list contains one or more absolute reference files
for bounded noncanonical/legacy transport. Validate and hash every
reference before transport. There is no strict filename or orthogonality requirement:
the provider may normalize/display attachment names, and references may be attached
or otherwise supplied in the page-supported form. Record the provider-visible names
and preserve the byte hashes and intended order where the page permits. The
one-to-one binding-key/conversation rule still applies to the body and all
references together.

For canonical Prompt Author handoffs, `PROMPT_BODY.md` is the sole scientific
attachment: its `GITHUB_EVIDENCE_MANIFEST` already contains the read-only reference
metadata. Such a handoff must not declare, upload, or synthesize `reference_paths`.
`scripts/validate_request.py` recognizes `source_mode=single_body_attachment`,
requires the sole `PROMPT_BODY.md` upload, and rejects any reference attachment
declaration in that mode.
Use the body bytes verbatim and retain any generic legacy reference support only for
non-Author transport requests.

Reject every canonical request that lacks a valid `source_thread_id` or
`parent_thread_id`. Reject legacy
fallback routing fields even when false or null. A legacy request may omit its source
or parent and still execute transport, but without a valid parent it is ineligible for an automatic receipt; mark
its receipt substate `RETURN_RECEIPT_BLOCKED`, do not guess a destination, and do not
send any receipt.

When loading legacy outbox state, normalize only a provably unsent `PENDING` or
`BLOCKED` receipt. Check both the primary and old fallback route: any attempt count,
delivery status, sent timestamp, or terminal delivery state preserves the complete
old receipt as historical evidence and forbids a new send. A valid parent permits
only the zero-attempt migration to `PARENT_SESSION`; no parent records
`required=false` and remains ineligible for return.

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
It is project-shared across every request handled by the singleton and is not keyed
by the singleton task ID.
The same direction therefore has two independent EM conversations, while Portfolio
has one conversation shared across direction scopes. Only one request may be active
per binding; a later round reuses the same conversation after the preceding request
is archived. If a mapping exists, continue that conversation; never create a replacement because
of a timeout, stale tab, model mismatch, or uncertain click alone. A new mapping is bound
only after a concrete `/c/<uuid>` URL is observed.
Use `scripts/bind_conversation.py` for the first binding and every idempotent retry;
it refuses a different conversation ID for an already-bound key.

Normal operation reuses the same bound conversation serially. A provider-context
replacement requires the handoff to explicitly set
`reset_invalid_provider_context=true` with complete
`provider_context_reset_evidence`. There are two supported reasons:

- **Owner-directed new conversation:** `reset_authority=OWNER_DIRECT`, the exact
  `owner_instruction`, and `previous_request_id`. This covers an explicit request
  to use a new conversation for a new model. Preserve the entire prior record and
  all accepted-send facts, even if its generation is unfinished. Do not claim that
  its answer was contaminated, blocked, or scientifically negative. Stop the old
  operator's future actions and retire its superseded wake before taking over; an
  accepted provider generation need not be stopped. Use a distinct request ID.
- **Automated contaminated-context recovery:** the immediately previous round is `ARCHIVED`,
its final outcome is `DECISION_NOT_FORMED` or `BLOCKED`, it read exactly zero
repository paths, and acknowledged provider-context contamination is traced to a
named prompt defect. Before reset admission, archive those actual facts in
`archive.provider_context_reset_facts`; compare every caller field to that persisted
record and refuse missing or mismatched facts without mutation. A pending request
or an ordinary bad answer does not qualify for this automated route.

For either reason, the caller must not invent a replacement provider ID. Before page
actions, call `scripts/bind_conversation.py:prepare_context_reset` to retire the
old provider ID and leave the binding with no active provider conversation. The old
ID is permanently unavailable to every binding. Then create no provider conversation
by inference: only after a successful send produces a newly observed webpage
`/c/<uuid>` URL may Transport call `bind` with
`observed_after_successful_send=true` to bind that replacement. A reset flag and its
evidence are routing metadata; never put them in the body, reference manifest, or
provider-visible companion text. That replacement is persisted directly as
`SEND_CONFIRMED` with one send click and durable send evidence; it may proceed only
to generation waiting, never to another Send action. Repeating preparation with the
same request and evidence is idempotent. The legacy `quarantined_conversations`
storage name includes owner-retired conversations; it does not label their science.

## Browser and model preflight

Use the existing in-app-browser binding. Claim an explicitly mentioned user tab by
exact title/URL/provider identity; otherwise create one agent tab and retain its
lease for the whole request. Navigate once to `https://chatgpt.com/` only when no
usable tab is available. Wait for the visible composer rather than guessing a fixed
load delay. After every navigation, reload, click, or upload, take a fresh DOM state
check before the next action. The tab handle is a lease, not the conversation
identity; persist `conversation_id` and `provider_url` before handing off to a wake.

Identify the model from the page, never from the account plan or the closed `Pro`
label alone. Read the provider selection in `.codex/hmasd-transport.toml` separately
from the Codex executor model: the owner's 2026-09-04 requirement is **GPT-6 Astra
in Pro mode (6 Pro)**. Verify the configured tuple with
`scripts/transport_contract.py:verify_provider_selection`. The successfully observed
UI has the closed label **`6 Pro`**, checked model **`Latest`**, and effort
**`Pro, 5 of 5.`**. `Latest` is accepted only together with the configured `6 Pro`
label; it is not a model identity by itself. An explicit checked `GPT-6 Astra` is
also valid with Pro mode. Record the exact labels, not an inferred model name.
The UI may label the open control `Thinking
effort`, so use current state-based locators rather than a single hard-coded name.
If the required 6 Pro state cannot be verified, stop before typing or sending and
report the exact available state; do not substitute GPT-5.6 Sol or a non-Pro mode.
If a switch is needed on an idle conversation, select the required model and Pro
mode, wait for the page update, and re-check the composer and exact input.

An owner model change after a confirmed Send does not change the model of that
accepted request. Preserve its original model and one-send evidence; do not switch
an active generation or resend its request ID. A newly authorized review under the
new model uses a distinct caller-supplied handoff. Normally it reuses the binding
after the prior archive; an explicit owner request for a new conversation uses the
owner-directed replacement above. Never keep retrying an old conversation that
does not expose the requested model. Record the prior
answer as superseded for the owner's model requirement, not as a scientific negative.

## Exact input and one-send rule

For paste mode, write the exact UTF-8 text to the tab clipboard, focus the composer,
and use the platform paste key. Verify the composer text before sending. Do not use
`locator.fill()` for transport: the live test produced a duplicated/malformed user
message node even though a response was returned.

For upload mode, start `waitForEvent("filechooser")` before opening the visible
upload control, set the absolute file path, and wait for the explicit file group and
upload completion state. Record file size/hash before upload. Acceptance of a
validated handoff authorizes uploading exactly its validated `prompt_path` and any
validated `reference_paths` to `chatgpt.com` for that request. Do not request
action-time confirmation before upload or immediately before Send. This authorization
does not extend to any other local file, destination, replacement packet, or second
send. An exact retry remains covered only when authoritative state proves the prior
operation was rejected before acceptance and produced no external effect.
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

For a canonical Prompt Author single-body packet, upload only `PROMPT_BODY.md`.
The in-body `GITHUB_EVIDENCE_MANIFEST` is not a second attachment and must not be
split back out for upload.

After the verified packet is ready, click Send once. Record `SEND_ATTEMPTED`, then re-observe:

- `/c/<uuid>` plus a visible exact user-message node is `SEND_CONFIRMED`;
- a transient `/c/WEB:<uuid>` is a client URL awaiting the concrete provider UUID;
  keep observing the same tab without another Send;
- a URL change without the user node is `SEND_UNCERTAIN`;
- an unchanged URL, unchanged composer, enabled Send control, and no user node are
  the only positive evidence that a pre-send click failed and may permit one retry
  with the same request/idempotency key.

For a packet with references, `SEND_CONFIRMED` additionally requires every expected
file group and its recorded hash to be associated with the bound conversation; the
provider-visible filename need not equal the local basename. Never retry an uncertain
or mismatched send, never open a second conversation, and never silently alter
whitespace, file selection, reference order, or prompt text.
Persist the exact user-message ID or another unique DOM identity when available,
alongside its text and attachment association. A file chip proves page association;
its byte identity comes from the pre-upload local hash, not from its display name.

### Locator hit-point mismatch recovery

A locator result is not, by itself, proof that its rendered hit point is clickable. The
observed failure mode is an exact Send prompt locator with `matchCount=1`,
`visibleCount=1`, and `disabled=false`, followed by a force-click error such as
`No element found at point … waiting on click for selector`. Treat that combination
as a locator coordinate offset, not as `SEND_FAILED_PRE_SEND` and not as evidence
that a submission occurred.

Before making any classification, take fresh DOM state using the current browser
API. Select the exact visible Send prompt node from that fresh DOM; do not guess
coordinates or reuse a stale node. A single DOM-node click is
permitted only when all of the following are true: the URL is unchanged from the
pre-send observation, no visible user-message node exists for the exact prompt, and
fresh locator diagnostics still prove that this exact Send control is enabled and
visible. This DOM-node click replaces the failed locator click; it is the one Send
attempt and is recorded as `SEND_ATTEMPTED`.

Immediately after the DOM-node click, re-verify the concrete `/c/<uuid>` URL (and the
bound conversation when one already exists), the exact visible user-message node and
its exact prompt text, and every expected attachment/file group and recorded hash. If
that evidence is complete, record `SEND_CONFIRMED`. If the URL or user-node evidence
is ambiguous at any point, record terminal `SEND_UNCERTAIN`; do not retry. If the
post-click snapshot is unambiguously unchanged with no user node, record
`SEND_FAILED_PRE_SEND` and stop. Never perform blind coordinate retries, a second
DOM-node click, or any retry after `SEND_UNCERTAIN`.

## Long generation and asynchronous wake-up

Once `conversation_id` is bound, persist it before waiting and mark the tab for
handoff. The durable identity is the exact `conversation_id` and `provider_url`;
the tab lease remains active while generation is pending. During Pro generation,
`Pro thinking`, `Stop answering`, a browser timeout, or `Answer now` are non-terminal
observations. Never click `Answer now`, Retry, Continue, or Stop. A timeout becomes
`WAITING_UNKNOWN`, not a send failure.

Use the active request's heartbeat automation as a bounded wake-up, normally
`FREQ=MINUTELY;INTERVAL=15`; never use `INTERVAL=1` busy polling. Each wake acquires
the conversation lock, reuses the active tab lease when it is valid, performs
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
assistant node paired with this request's recorded user message, not the first or
last unscoped assistant/copy control in a long conversation. `Worked for ...` with
response actions and no active generation is a completed status. Partial streamed
text is not an archive.

## Archive and tab lifecycle

Write one canonical packet manifest plus exact UTF-8 prompt, reference-file, and
response artifacts and a transport-fact file containing workflow node, binding
key, direction scope, conversation, tab, model, source mode/path, timestamps,
hashes, reference hashes, send evidence, wait status, and archive status.
Record the paired user and assistant message identities. Use that response's Copy
control and the browser clipboard API to preserve Markdown when available. For
all packets, use the recorded conversation and paired user/assistant messages to
identify the answer. `validate_response_identity` compares the recorded binding
with the binding of the actual captured node; obtain these independently from the
accepted-send record and the scoped conversation inspection, never fabricate them
from the answer's prose. If IDs are unavailable, inspect the exact question and its
paired reply manually and record that evidence. A mismatch means re-inspect the
same conversation and preserve the mismatched capture, never send a repair prompt.
The owner requires natural-language Pro answers: no request-ID echo, envelope,
JSON/status block or pinned-ref header is required. Keep identifiers and hashes in
internal handoff/transport facts. Preserve old accepted prompts and exact responses;
do not edit archives or resend accepted requests to change their presentation.
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

### Completion receipt to the parent session

For owner-directed `CALLER_DIRECT` execution with caller equal to parent, record
local completion/intake and zero message attempts; do not stage or send a self-receipt.
All other routes retain the following completion procedure.

After a response is durably archived and hash-verified, call
`scripts/transport_contract.py:stage_receipt` to stage exactly one structured
completion receipt in the persisted outbox, then send it once to the exact validated
`parent_thread_id` using
`mcp__codex_app__send_message_to_thread`. Omit `model` and `thinking` on every
parent receipt, including blocker receipts, so the receiving Root/DM retains its
own settings. `operator_model` and `operator_thinking` apply only to dispatch INTO
the Transport singleton; copying them onto a receipt changes the parent model.
Use `send_message_to_thread({threadId: parent_thread_id, prompt: receipt_text})`.
Do not send an extra receipt to repair a prior model override.
The receipt must contain at least
`request_id`, `workflow_node`, `conversation_binding_key`, `direction_id`,
`direction_ids`, `state=ARCHIVED`, `conversation_id`, `provider_url`, response
SHA-256, archive paths, and heartbeat retirement status; it must report
transport facts only and must not add scientific interpretation. Record the receipt
timestamp, destination thread ID, deterministic message key, attempt count, and
delivery status in the registry or transport-fact file. Treat the logical receipt as
idempotent; the deterministic message key is unchanged by this routing choice. Its
route record is `routing_mode=PARENT_SESSION`,
`destination_thread_id=<parent_thread_id>`, and `fallback_enabled=false`. On
uncertain delivery, do not create a duplicate or send again—record
`RETURN_RECEIPT_UNCERTAIN` and report it. Persist the one bounded attempt's result
and return control immediately; a rejection must not cause a second send. For an
explicit terminal/blocker state with no archive, `stage_blocker_receipt` applies the
same parent-route, one-send rule. If the parent is missing or invalid, staging
records the receipt substate `RETURN_RECEIPT_BLOCKED` without a message key or
destination and performs no send. Never use the source/creator task, the operator task itself, an old receipt
task, or any repository UUID as a fallback.

### Request heartbeat retirement and singleton reuse

Persist each request's heartbeat automation ID and status with that request's transport facts. A
request heartbeat remains active while its conversation still needs a bounded wake
(`WAITING_GENERATION`, `WAITING_HEARTBEAT`, `ARCHIVE_PENDING`, or a recoverable
`WAITING_TIMEOUT`). When that request is durably `ARCHIVED`, or is an explicit
terminal/blocker state with no scheduled recovery, delete or disable only that
request's existing heartbeat exactly once and record the retirement timestamp and
verification. Never archive or close the singleton task after a request. Later
handoffs may be queued or active concurrently in other provider conversations, but
their tabs, heartbeat IDs, facts, archives, receipts, and idempotency keys remain
strictly request-scoped. Never reuse one request's heartbeat for another or leave a
retired request heartbeat active merely because the singleton remains alive.
Never multiplex a later owner-authored follow-up into the already archived request.
Record its exact user-message identity separately and watch its paired response
without sending anything. If the owner starts participating in an agent-created
conversation, keep its tab open for that continuing use; finish only the earlier
request's archive and wake cleanup. Apply the owner's new scope before intake.

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

An owner stop or takeover cancels the old operator's future actions for that
request. Persist whether a provider Send was accepted (including uncertainty),
retire only that operator's superseded wake, and return one factual handover. Do
not resume browser actions, correct the prompt, or dispatch another operator after
the stop. Root can adopt a proven accepted request without another Send.

Stop and report the exact state on unknown direction, missing prompt, failed Pro
verification, incomplete upload, uncertain/mismatched submission, stale/ambiguous
conversation identity, partial response, archive conflict, heartbeat overlap, or a
recovery URL that no longer resolves to the bound conversation.
Transport facts never imply scientific conclusions.
