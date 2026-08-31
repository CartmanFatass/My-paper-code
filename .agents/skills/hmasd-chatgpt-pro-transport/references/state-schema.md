# State, packet, lease, and evidence schema

The registry is JSON at a caller-supplied path (default project-local path:
`temp/sessions/hmasd-chatgpt-pro-transport/registry.json`). Keep one record per
`conversation_binding_key`; do not overwrite a binding with a different
`conversation_id`. The exact keys are `em:<direction>:innovator`,
`em:<direction>:convergence`, and `portfolio:cross_direction`. Thus one direction
has two independent EM conversations and Portfolio has one conversation reused
across changing multi-direction scopes. Only one request may be active per key;
archive it before sending the next turn in that same conversation. Browser tab
handles, heartbeat wakeups, and executor turns remain ephemeral observations.

```json
{
  "schema_version": 2,
  "conversation_binding_key": "em:finite_resource_relational_inductive_efficiency:innovator",
  "workflow_node": "em_innovator",
  "direction_id": "finite_resource_relational_inductive_efficiency",
  "direction_ids": ["finite_resource_relational_inductive_efficiency"],
  "decision_authority": "pro_final",
  "request_id": "portfolio-frrie-r02-exact-law-20260831-01",
  "packet_id": "portfolio-frrie-r02-exact-law-20260831-01--finite_resource_relational_inductive_efficiency",
  "source_thread_id": "01a...",
  "fallback_enabled": false,
  "fallback_thread_id": null,
  "fallback_thread_url": null,
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
  "visible_model": "Pro",
  "underlying_model": "GPT-5.6 Sol",
  "thinking_effort": "5/5",
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
    "transport_fact_file": null
  },
  "return_receipt": {
    "required": true,
    "primary_destination_thread_id": "01a...",
    "destination_thread_id": "01a...",
    "status": "PENDING",
    "message_key": null,
    "attempt_count": 0,
    "retry_allowed": false,
    "delivery_mode": "bounded_single_attempt",
    "return_control_after_attempt": true,
    "fallback_enabled": false,
    "fallback_thread_id": null,
    "fallback_destination_thread_id": null,
    "fallback_status": "NOT_NEEDED",
    "fallback_used": false,
    "fallback_message_key": null,
    "fallback_delivery_mode": null,
    "delivery_status": null,
    "error": null
  },
  "heartbeat": {
    "automation_id": "hmasd-transport-wake",
    "status": "ACTIVE",
    "next_wake_at": "...Z",
    "retired_at": null,
    "retirement_verified": false
  }
}
```

At the registry root, active records live under `bindings`, keyed by the exact
`conversation_binding_key`. A legacy `directions` object may remain as historical
transport evidence but is not consulted for the three decision-node bindings.
When a new `request_id` arrives for an existing binding, the previous request must
already be `ARCHIVED`. Move its request/packet/archive/receipt facts into
`request_history`, reset only request-local state, and continue with the same
`conversation_id` and `provider_url`. A second request while the first is pending
is `BINDING_BUSY`, not permission to create another conversation.

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
`ARCHIVE_CONFLICT`, `RECOVERY_URL_MISMATCH`, `MONITOR_IDENTITY_MISMATCH`,
`RETURN_RECEIPT_UNCERTAIN`, `RETURN_RECEIPT_BLOCKED`, and `BLOCKED`.
`BOUND` is accepted only as a legacy result label; new records start at
`DIRECTION_VERIFIED`. A timeout or browser exception is never converted into a new
conversation.

## Tab lease and monitor identity

`tab_lifecycle` may be `OPEN`, `HANDOFF`, or `CLOSED`, but it is never the
conversation identity. The tab lease must remain `OPEN` throughout every
`WAITING_*` state. Ending an executor turn or returning from a heartbeat wake does
not close the tab. Only after natural completion, exact response capture, durable
archive verification, and receipt staging may an agent-created tab be closed by the
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

## Natural completion and archive evidence

Capture only when the same conversation has a complete assistant node, the active
generation controls are absent, and the page reports completion (for example
`Response complete`). Keep the raw assistant node separate from status text and UI
labels. Hash the exact bytes written to the response file. Set `ARCHIVE_PENDING`,
write and verify the canonical artifacts, then set `ARCHIVED`; do not close a tab
before this sequence.

## Heartbeat and asynchronous processing

The heartbeat performs one bounded read per wake under a per-conversation lock. The
normal cadence is `FREQ=MINUTELY;INTERVAL=15`; `INTERVAL=1` busy polling is invalid.
The wake may reuse the active tab lease. It may not send, retry, switch direction,
create a replacement conversation, or click `Answer now`. On natural completion it
captures/archives once and then applies the completion close policy. On timeout it
keeps the same conversation and active tab in `WAITING_TIMEOUT` for a later wake.

If a page handle is lost, one recovery tab may be opened from the exact persisted
provider URL; the loaded URL and direction must be re-verified before observation.
Never call `tabs.get()` on an old handle and never treat the new tab ID as a new
identity. The recovered tab remains active while the conversation is pending.

For a heartbeat shared by multiple directions, retain it while any record requires
a wake or recoverable timeout. After the final record is durably archived, or is an
explicit terminal/blocker state with no scheduled recovery, update the existing
automation to `PAUSED` exactly once, verify the disabled status, and persist
`retired_at` plus `retirement_verified=true`. Heartbeat retirement and tab closure
are separate facts.

## Automatic return outbox

After `ARCHIVED`, call `stage_receipt` from `scripts/transport_contract.py` before
using `send_message_to_thread`. The deterministic `message_key` is
`request_id|direction_id|conversation_id|response_sha256`. The outbox transitions
from `PENDING` to `SENT`, `UNCERTAIN`, `FAILED`, or `BLOCKED` and records the
destination, timestamp, attempt count, delivery status, and error. An uncertain
send is never retried or rerouted; a missing/unresolved source thread leaves the
archive valid and sets `RETURN_RECEIPT_BLOCKED` unless the request explicitly sets
`fallback_enabled=true`.

The only configured fallback is the exact Codex session
`codex://threads/01a04f5a-1c9f-7331-b1d9-249fb767362e`. With explicit
`fallback_enabled=true`, a missing source thread or a definite primary send failure
stages one fallback outbox entry with `fallback_used=true`, the fallback destination,
timestamp, and `message_key=<primary-key>|fallback|<fallback-thread-id>`. A normal
request without that flag never uses the fallback. `UNCERTAIN` and
`SEND_UNCERTAIN` never use it because the primary may already have been accepted.
Terminal blockers without an archive use `stage_blocker_receipt` with the same
explicit fallback rule. Fallback delivery is a separate bounded action; its failure is recorded and does not
block archive completion.
