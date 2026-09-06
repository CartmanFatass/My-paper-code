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

Archive completeness is a transport fact, not specification-conformance acceptance.
The receiving Root/DM checks the formed decision against current owner/spec constraints
at its existing intake. Transport preserves the full answer and reports it without
adjudicating or rewriting scientific requirements; a conflict never permits a duplicate Send.

Use the available `mcp__cua_repl` browser API. Initialize it using the tool's documented
entry point, then read the returned documentation before acting. Use only available
browser methods; an unavailable export or locator API is not permission to resend.

## Scoped GitHub delivery — OWNER_DIRECT 2026-09-05

All newly authored requests now use GitHub delivery (owner overall cutover).
No additional VNFC trial or Pro design review is required. Keep accepted in-flight
requests on their original route, without another Send.
An Author handoff with `delivery_mode=github_delivery` uses the already supported
paste transport request. Send its short fixed task link verbatim, no attachment,
read-only preamble or copied evidence. Dispatch only a bound READY_TO_DISPATCH task;
TASK_NOT_PUBLISHED has no provider payload. This mode authorizes Pro's named file
and comment; Transport does not write them. Archive the complete short chat reply
and actual URLs unchanged. Root/DM retrieves the full file for scientific intake;
a delivery receipt alone is not a formed Pro decision. Repeated/uncertain receipt
handling observes existing state, never repeats Send. Keep request-scoped existing
waiting and cleanup, singleton/provider binding and parent model unchanged.

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

For explicit attachment fallback, noncanonical uploads or legacy request/outbox recovery,
read [attachment-compatibility.md](references/attachment-compatibility.md) before acting.
Normal GitHub delivery uses the exact short prompt and canonical routing above. A missing
canonical source/parent ID or forbidden legacy fallback routing field is rejected; never
infer a receipt destination.

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
conversation. For attachment materialization follow the compatibility reference above.

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

Normal operation reuses the same bound conversation serially. Only an explicitly
authorized owner replacement or the existing narrowly defined contaminated-context
recovery may reset a binding. Read [provider-context-replacement.md](references/provider-context-replacement.md)
before either path; preserve accepted-send facts and never invent a provider ID.
An ordinary bad answer, model mismatch, timeout or uncertain Send does not authorize reset.

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

For upload mode, read [attachment-send.md](references/attachment-send.md) before
uploading. Preserve exact body/reference bytes, verify every expected upload before
Send, and retain canonical manifest order. A pending upload cannot be sent.

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

If a locator reports a hit-point/coordinate failure, read
[send-hit-point-recovery.md](references/send-hit-point-recovery.md) before any replacement
click. The error alone proves neither submission nor a safe retry; uncertain Send stops.

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
