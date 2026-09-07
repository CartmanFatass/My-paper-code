# State, packet, lease, and evidence schema

The registry is JSON at a caller-supplied path (default project-local path:
`temp/sessions/hmasd-chatgpt-pro-transport/registry.json`). Keep one record per
`conversation_binding_key`; do not overwrite a binding with a different
`conversation_id`. The exact keys are `em:<direction>:innovator`,
`em:<direction>:convergence`, and `portfolio:cross_direction`. Thus one direction
has two independent EM conversations and Portfolio has one conversation reused
across changing multi-direction scopes. Only one request may be active per key;
archive it before sending the next turn in that same conversation. Browser tab
handles, heartbeat wakeups, and executor turns remain ephemeral observations. The
registry is shared across all requests handled by the project Transport singleton;
its operator UUID never selects a provider conversation.

```json
{
  "schema_version": 4,
  "conversation_binding_key": "em:finite_resource_relational_inductive_efficiency:innovator",
  "workflow_node": "em_innovator",
  "direction_id": "finite_resource_relational_inductive_efficiency",
  "direction_ids": ["finite_resource_relational_inductive_efficiency"],
  "decision_authority": "pro_final",
  "request_id": "portfolio-frrie-r02-exact-law-20260831-01",
  "packet_id": "portfolio-frrie-r02-exact-law-20260831-01--finite_resource_relational_inductive_efficiency",
  "source_thread_id": "01a...",
  "creator_thread_id": "01a...",
  "parent_thread_id": "01p...",
  "operator_thread_id": "01b...",
  "operator_mode": "PROJECT_SINGLETON",
  "operator_model": "gpt-5.6-luna",
  "operator_thinking": "xhigh",
  "return_route": "PARENT_SESSION",
  "conversation_id": "6a...",
  "provider_url": "https://chatgpt.com/c/6a...",
  "state": "WAITING_GENERATION",
  "packet": {
    "canonical_form": "logical_packet_manifest",
    "manifest_path": ".../PACKET_MANIFEST.json",
    "body_path": ".../00_PROMPT.md",
    "reference_paths": [".../01_REF_001_DIRECTION.md"]
  },
  "tab_id": "7",
  "tab_lifecycle": "OPEN",
  "tab_lease": {
    "handle": "7",
    "lifecycle": "OPEN",
    "origin": "agent",
    "reusable": true,
    "last_observed_at": "...Z",
    "lease_expires_at": null
  },
  "monitor": {
    "identity_key": "request|binding|conversation|provider_url",
    "provider_url": "https://chatgpt.com/c/6a...",
    "last_observed_url": "https://chatgpt.com/c/6a...",
    "last_observed_state": "Pro thinking",
    "last_observed_at": "...Z",
    "cursor": null
  },
  "visible_model": "6 Pro",
  "underlying_model": "Latest",
  "thinking_effort": "Pro, 5 of 5.",
  "provider_requirement": {"model": "GPT-6 Astra", "mode": "Pro", "label": "6 Pro", "selector_hint": "Latest"},
  "source_mode": "upload",
  "prompt_sha256": "...",
  "reference_files": [
    {
      "path": ".../DIRECTION.md",
      "filename": "DIRECTION.md",
      "canonical_filename": "...__01_REF_001_DIRECTION.md",
      "bytes": 1234,
      "sha256": "...",
      "uploaded": true,
      "provider_filename": "DIRECTION(2).md"
    }
  ],
  "response_sha256": null,
  "send_evidence": {
    "send_click_count": 1,
    "url_observed": true,
    "user_node_observed": true,
    "user_node_exact": true,
    "user_message_id": "<observed DOM message ID>",
    "attachment_observed": true
  },
  "timestamps": {
    "received_at": "...Z",
    "sent_at": "...Z",
    "generation_started_at": "...Z",
    "completed_at": null,
    "captured_at": null,
    "archived_at": null
  },
  "archive": {
    "manifest_file": null,
    "prompt_file": null,
    "reference_files": [],
    "response_file": null,
    "transport_fact_file": null,
    "provider_context_reset_facts": {
      "request_id": "portfolio-frrie-r02-exact-law-20260831-01",
      "decision_outcome": "DECISION_NOT_FORMED|BLOCKED|<actual formed outcome>",
      "repository_paths_read": 0,
      "provider_context_contamination_acknowledged": false,
      "acknowledged_prompt_defect": null
    }
  },
  "return_receipt": {
    "required": true,
    "source_thread_id": "01a...",
    "parent_thread_id": "01p...",
    "destination_thread_id": "01p...",
    "status": "PENDING",
    "message_key": null,
    "attempt_count": 0,
    "retry_allowed": false,
    "delivery_mode": "bounded_single_attempt",
    "return_control_after_attempt": true,
    "routing_mode": "PARENT_SESSION",
    "fallback_enabled": false,
    "delivery_status": null,
    "error": null
  },
  "heartbeat": {
    "automation_id": "hmasd-experiment-monitor",
    "status": "ACTIVE",
    "next_wake_at": "...Z",
    "retired_at": null,
    "retirement_verified": false
  }
}
```

At the registry root, active records live under `bindings`, keyed by the exact
`conversation_binding_key`. A legacy `directions` object may remain as historical
transport evidence and is not normally consulted for the three decision-node
bindings. The one repair exception is an atomically locked serial admission: when
the binding is stale but its direction mirror is `ARCHIVED`, has a non-empty
`timestamps.archived_at` plus an archive object, and exactly agrees on binding key,
direction, request, conversation ID, and provider URL, the archived mirror repairs
the binding before admission. Any missing or disagreeing fact remains
`BINDING_BUSY`; this reconciliation never contacts the provider or creates a send.
When a new `request_id` arrives for an existing binding, the previous request must
already be `ARCHIVED`. Move its request/packet/archive/receipt facts into
`request_history`, reset only request-local state, and continue with the same
`conversation_id` and `provider_url`. A second request while the first is pending
is `BINDING_BUSY`, not permission to create another conversation.

Each `request_history` entry preserves that round's `source_thread_id`,
`creator_thread_id`, `parent_thread_id`, `operator_thread_id`, and `return_route` alongside its archive
and receipt. A singleton-era round reuses the configured operator but may use a
different creator while retaining the binding's exact provider conversation;
historical entries may preserve old per-handoff operator IDs. Completed old fixed-route receipts remain
historical evidence and are not rewritten or resent. An old `PENDING` or `BLOCKED`
receipt may migrate to `PARENT_SESSION` only when `attempt_count=0`, no send is
recorded on either its primary or fallback route, and that same round has a valid
`parent_thread_id`; its deterministic message key is preserved. Any primary/fallback
attempt count, delivery status, sent timestamp, or terminal delivery state freezes
the old receipt as historical evidence. A record without a parent task is marked
ineligible for an automatic receipt and is never sent to an old destination.

## Explicit provider-conversation replacement

An owner-directed new conversation uses `reset_invalid_provider_context=true`
with `provider_context_reset_evidence={previous_request_id, reset_authority:
"OWNER_DIRECT", owner_instruction: "<exact owner instruction>"}`. It requires a
distinct replacement request ID, preserves the complete prior record (including
unfinished/accepted-send state), and records `reason=owner_requested_new_conversation`.
It does not require or fabricate a blocked answer, zero retrieved paths, or
contamination. Stop the superseded operator's future actions and wake before takeover.
The legacy `quarantined_conversations` map stores the retired provider ID without
assigning scientific polarity. Repeating the same pending replacement preparation
is idempotent; a different pending replacement is refused.

Serial reuse is the default. Without an owner instruction, replacement still requires an explicit
`reset_invalid_provider_context=true` handoff supplies complete routing evidence and
the active record is the immediately previous `ARCHIVED` round: its outcome is
`DECISION_NOT_FORMED` or `BLOCKED`, `repository_paths_read` is exactly `0`, and an
acknowledged provider-context contamination names the prompt defect. The caller
never supplies a replacement conversation ID. Archive the actual outcome, exact
repository-path-read count, contamination acknowledgement, and named prompt defect
in `archive.provider_context_reset_facts` before accepting any reset. Admission
compares every caller field to those persisted facts; missing facts or a mismatch are
zero-mutation refusals. On admission, move the prior round to
`request_history`, append a quarantine entry containing its provider ID, binding,
reason, and evidence, and persist that ID in the registry-root
`quarantined_conversations` map. Set the binding to `CONTEXT_RESET_PENDING` with
`conversation_id=null` and `provider_url=null`; it has no active provider
conversation during this interval.

Only a new concrete webpage `/c/<uuid>` URL observed after successful send may
replace that empty binding. Bind it with `observed_after_successful_send=true`; reject
all old quarantined IDs for every node, every unobserved replacement, and every
incomplete applicable reset record. The replacement record begins at `SEND_CONFIRMED` with
`send_click_count=1` and durable URL/user-node/attachment send evidence, so its next
reachable lifecycle step is generation waiting rather than another send. Reset
metadata is routing-only and never belongs in
`PROMPT_BODY.md`, `REFERENCE_FILES.md`, or companion UI text.

## Canonical packet and names

`packet_id` is derived from the opaque `request_id` and `direction_id` by
`scripts/transport_contract.py`. `scripts/materialize_packet.py` writes one
logical packet with deterministic names:

- `<packet_id>__00_PROMPT.md`
- `<packet_id>__01_REF_<ordinal>_<safe-source-stem>.<ext>` for each reference
- `<packet_id>__PACKET_MANIFEST.json`

Archive attempts use a separate directory suffix
`<packet_id>--attempt-XX` and contain `<archive_id>__02_RESPONSE.md` and
`<archive_id>__03_TRANSPORT_FACTS.json`. Existing files are idempotent only when
their bytes match; a different response or manifest is `ARCHIVE_CONFLICT` and never
overwrites an existing artifact. Provider-visible filename normalization is stored
as `provider_filename`; it never changes the canonical filename or reference order.

## State vocabulary and transitions

The normal sequence is:

`RECEIVED` → `DIRECTION_VERIFIED` → `TAB_OPEN` → `PAGE_READY` → `PRO_VERIFIED` →
`PROMPT_READY` → `UPLOAD_PENDING`/`UPLOAD_CONFIRMED` → `SEND_ATTEMPTED` →
`SEND_CONFIRMED` → `WAITING_GENERATION` → `WAITING_HEARTBEAT` →
`NATURAL_COMPLETION` → `ARCHIVE_PENDING` → `ARCHIVED`.

`WAITING_UNKNOWN` and `WAITING_TIMEOUT` are recoverable attention states, not send
failures. Terminal or attention states are `SEND_UNCERTAIN`, `SENT_INPUT_MISMATCH`,
`UPLOAD_READY_SEND_DISABLED`, `MODEL_UNVERIFIED`, `DIRECTION_UNVERIFIED`,
`ARCHIVE_CONFLICT`, `RESPONSE_IDENTITY_MISMATCH`, `RECOVERY_URL_MISMATCH`, `MONITOR_IDENTITY_MISMATCH`,
`RETURN_RECEIPT_UNCERTAIN`, and `BLOCKED`. `RETURN_RECEIPT_BLOCKED` is a receipt
substate for a missing parent route; it does not replace an `ARCHIVED` scientific
transport state.
`BOUND` is accepted only as a legacy result label; new records start at
`DIRECTION_VERIFIED`. A timeout or browser exception is never converted into a new
conversation.

## Tab lease and monitor identity

`tab_lifecycle` may be `OPEN`, `HANDOFF`, or `CLOSED`, but it is never the
conversation identity. The tab lease must remain `OPEN` throughout every
`WAITING_*` state. Ending an executor turn or returning from a heartbeat wake does
not close the tab. Only after natural completion, exact response capture, durable
archive verification, and either receipt staging or an explicit blocked-receipt
record may an agent-created tab be closed by the
normal completion policy; the close must then clear `tab_id` while retaining the
conversation URL/ID and archive paths. A user-owned/explicitly mentioned tab is not
closed without authorization.

The monitor identity is exactly:

`request_id|conversation_binding_key|conversation_id|provider_url`
(use `legacy:<direction_id>` only for legacy requests).

Every wake must verify the loaded URL against the persisted `provider_url` before
reading the page, then persist the observed URL, page state, completion controls,
and optional cursor. `tab_id` is only the current lease handle. A tab ID without an
exact URL/conversation observation is not monitor evidence and must produce
`MONITOR_IDENTITY_MISMATCH`.

## Send evidence

`SEND_CONFIRMED` requires all of:

1. a concrete provider URL containing one conversation UUID;
2. one visible user message node in that conversation;
3. the exact supplied prompt text in that node, byte-equivalent after the page's
   visible newline normalization; and
4. for upload mode, the file group plus the exact companion text, when one was
   supplied; and
5. for a non-empty reference list, every expected canonical file group is associated
   with the bound conversation and matches its pre-upload size/hash.

A URL alone, a cleared composer, a spinner, an attachment chip before Send, or a
`ChatGPT said` heading without a complete response is insufficient.
A transient `/c/WEB:<uuid>` after Send is awaiting a concrete provider URL, not
evidence of a failed click. Observe the same tab; do not send again.

## Natural completion and archive evidence

Capture only when the same conversation has the complete assistant node paired
with this request's recorded user message, the active
generation controls are absent, and the page reports completion (for example
`Response complete`). Keep the raw assistant node separate from status text and UI
labels. Hash the exact bytes written to the response file. Set `ARCHIVE_PENDING`,
write and verify the canonical artifacts, then set `ARCHIVED`; do not close a tab
before this sequence.
Record `user_message_id` and `assistant_message_id` when exposed by the DOM. New
Prompt Author replies are natural-language answers and need not echo request IDs,
pinned refs or status envelopes. Match the recorded conversation/user/assistant
binding against the captured node with `validate_response_identity`; missing DOM
IDs require documented manual pairing against the exact question. Preserve and
re-inspect a mismatched capture on the same page, never repair it with a new Send.

## Heartbeat and asynchronous processing

Integrated Root reuses one thirty-minute heartbeat for all current experiments and Pro
requests. A due Pro check occurs on the thirty-minute fallback wake;
each due conversation gets one bounded read in serial. `INTERVAL=1` busy polling is invalid.
A wake observes the existing request, never resends it or changes provider identity. Natural
completion archives the paired response; timeout retains the same conversation for recovery.

If a page handle is lost, one recovery tab may be opened from the exact persisted
provider URL; the loaded URL and direction must be re-verified before observation.
Never call `tabs.get()` on an old handle and never treat the new tab ID as a new
identity. The recovered tab remains active while the conversation is pending.

Root may own overlapping provider generations. Tab leases, outbox entries, archives and
idempotency keys remain request-scoped, but `heartbeat.automation_id` names the same Root
automation. Request completion clears only that request's pending observation. Pause the shared
automation only when no current experiment or Pro request needs observation, reconciliation,
archival or notification. Never retire it merely because one request completes. Preserve
historical per-request heartbeat records; superseded old-executor wakes are disabled at handover.

## Automatic return outbox

`REUSE_SINGLETON` identifies the configured Root endpoint. If the author is that endpoint,
the renderer selects `CALLER_DIRECT` with the owner instruction and no app self-dispatch.
New records name Root in `operator_thread_id`. An adopted legacy record retains that original
field and records the actual executor in `execution_thread_id` with handover evidence.
When actual executor equals parent, `stage_receipt` or `stage_blocker_receipt` creates
`required=false`, `status=LOCAL`, `routing_mode=LOCAL`, `destination_thread_id=null` and zero
message attempts. Root forwards the scientific work to the DM. No app self-receipt is sent.
Existing attempted/uncertain delivery evidence is never restaged during migration.
The following external-parent procedure applies only when executor differs from parent.

After `ARCHIVED`, call `stage_receipt` from `scripts/transport_contract.py` before
using `send_message_to_thread` exactly once on the validated parent task. The deterministic `message_key` remains
`request_id|direction_id|conversation_id|response_sha256`. The outbox transitions
from `PENDING` to `SENT`, `UNCERTAIN`, `FAILED`, or `BLOCKED` and records the exact
parent destination, timestamp, attempt count, delivery status, and error.
`destination_thread_id` must equal the validated `parent_thread_id`,
`routing_mode` is `PARENT_SESSION`, and `fallback_enabled` is false.

An uncertain delivery is not retried, rerouted, or duplicated. A confirmed rejection
before acceptance with no external effect may be retried after resolving its blocker:
call `retry_rejected_receipt(record, not_accepted_evidence=<direct tool evidence>)`.
It preserves the key, parent, payload metadata and attempt count, records the rejected
attempt in `rejected_attempts`, and restores `PENDING` for the same payload. A generic
failure or timeout is insufficient; never use this to migrate a legacy fallback route.
Terminal blockers without an archive use
`stage_blocker_receipt` with the same parent-session rule. If no valid parent is
available, no outbox message is staged: the receipt records
`required=false`, `receipt_state=RETURN_RECEIPT_BLOCKED`,
`destination_thread_id=null`, and no message key. Legacy transport may still
complete, but it cannot send a receipt.
