# State, packet, lease, and evidence schema

The shared registry is JSON at the absolute registry_path in live
`C:/Projects/HMASD/.codex/hmasd-transport.toml`, currently
`C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/registry.json`.
All direction worktrees use this same path and file lock; no worktree-local default. Keep one record per
`conversation_binding_key`; do not overwrite a binding with a different
`conversation_id`. The exact keys are `em:<direction>:innovator`,
`em:<direction>:convergence`, and `portfolio:cross_direction`. Thus one direction
has two independent EM conversations and Portfolio has one conversation reused
across changing multi-direction scopes. Only one request may be active per key;
archive it before sending the next turn in that same conversation. Browser tab
handles, native observation passes, and executor turns remain ephemeral observations. The
registry is shared across all requests handled by author-owned transports;
its operator UUID never selects a provider conversation.

## Native execution overlay

Current native Transport uses `native_state`: READY_UNSENT, SEND_ATTEMPTED, OBSERVE, ARCHIVE,
RECEIPT. These are the operator's four steps (observation and archival share one step), not
another required transition through every legacy `state` value below. Preserve legacy evidence.
`scripts/native_transport.py` reads immutable HANDOFF/TASK bytes and claims the existing binding
under its brief registry lock. It handles existing-conversation GitHub requests; first-binding
continues through the existing firstBinding route in agentify.md. `frozen_handoff`, `frozen_routing` and `manifest` identify those
inputs. `execution_route={parent_thread_id,operator_thread_id,assignment}` identifies the actual
current native parent/child; it never overwrites frozen or historical receipt IDs. A conflicting
live executor requires factual same-request transfer, not an automatic route rewrite.

Keep the exact Agentify `operation` (including operationId, responsePath and productModel) and
effect receipts. `next_step` classifies explicit false plus no acceptance as VERIFIED_NONACCEPTANCE;
unknown/possible acceptance as UNCERTAIN_EFFECT; paired current user/archive as ACCEPTED. Only
the first permits repaired same-request Send. False-valued legacy send placeholders are not a
Send. The native state overlay alone is bookkeeping: a failed pre-Send strict operation can
return to READY_UNSENT. Accepted history, actual attempt/turn evidence and legacy sent/waiting
facts cannot be erased by that transition. Screenshot annotations cover page facts; they cannot
establish operation history. Preserve the same agentify_stable_key for each conversation generation
across successor requests, and never bind the same conversation to two scientific nodes.

After the full answer is source-bound and hash/size verified, `state=ARCHIVED` releases that
request for a successor. The independent `native_receipt` preserves current-parent delivery:
PENDING -> SENT, UNCERTAIN or REJECTED_BEFORE_DELIVERY. COMPLETE requires the full archive and
paired provider IDs, or a verified `github_response_pairing` supplying the fixed TASK/immutable
response commit/path/Git blob and exact delivery comment when strict provider IDs are unavailable.
CONFLICT and NO_CURRENT_WORK require assignment/status/evidence/next action without claiming a
completed archive. UNCHANGED_WAIT stages nothing. `native_receipt_history`
preserves returns from earlier changed boundaries; identical boundaries reuse the same receipt.
`finish_native_receipt(receipt, status)` records the tool outcome on the exact staged receipt
object returned by `stage_native_receipt`, including a historical return. Completion conflicts
are checked across all receipt history. A new
request moves this record into request_history; timeout, pre-Send failure or missing receipt
does not release the conversation. The legacy schema below is evidence compatibility, not a
mandatory checklist, scheduler or current return route.

```json
{
  "schema_version": 4,
  "conversation_binding_key": "em:example_direction:innovator",
  "workflow_node": "em_innovator",
  "agentify_stable_key": "em:example_direction:innovator",
  "direction_id": "example_direction",
  "direction_ids": ["example_direction"],
  "decision_authority": "pro_final",
  "request_id": "example-review-01",
  "packet_id": "example-review-01--example_direction",
  "source_thread_id": "/root/dm_example",
  "creator_thread_id": "/root/dm_example",
  "parent_thread_id": "/root/dm_example",
  "operator_thread_id": "/root/dm_example/transport",
  "operator_mode": "DM_NATIVE",
  "operator_model": "gpt-5.6-luna",
  "operator_thinking": "high",
  "return_route": "PARENT_SESSION",
  "conversation_id": "6a...",
  "provider_url": "https://chatgpt.com/c/6a...",
  "state": "WAITING_GENERATION",
  "packet": {
    "canonical_form": "logical_packet_manifest",
    "manifest_path": ".../PACKET_MANIFEST.json",
    "body_path": ".../00_PROMPT.md",
    "reference_paths": []
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
  "source_mode": "paste",
  "prompt_sha256": "...",
  "reference_files": [],
  "response_sha256": null,
  "send_evidence": {
    "send_click_count": 1,
    "url_observed": true,
    "user_node_observed": true,
    "user_node_exact": true,
    "user_message_id": "<observed DOM message ID>",
    "attachment_observed": false
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
      "request_id": "example-review-01",
      "decision_outcome": "DECISION_NOT_FORMED|BLOCKED|<actual formed outcome>",
      "repository_paths_read": 0,
      "provider_context_contamination_acknowledged": false,
      "acknowledged_prompt_defect": null
    }
  },
  "return_receipt": {
    "required": true,
    "source_thread_id": "/root/dm_example",
    "parent_thread_id": "/root/dm_example",
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
  }
}
```

The legacy `heartbeat` field is historical metadata, not a scheduling instruction. Preserve
existing evidence fields; do not create an automation from them. The Transport task drives
observation, and new records require no scheduler identity.

At the registry root, active records live under `bindings`, keyed by the exact
`conversation_binding_key`. Use the existing binding helpers for persisted-state
reconciliation; do not turn archived records into current assignments or edit routing
by hand. Reconciliation never contacts the provider or creates a Send.
When a new `request_id` arrives for an existing binding, the previous request must
already be `ARCHIVED`. Move its request/packet/archive/receipt facts into
`request_history`, reset only request-local state, and continue with the same
`conversation_id` and `provider_url`. A second request while the first is pending
is `BINDING_BUSY`, not permission to create another conversation.

Each `request_history` entry preserves that round's `source_thread_id`,
`creator_thread_id`, `parent_thread_id`, `operator_thread_id`, and `return_route` alongside its archive
and receipt. The actual `execution_thread_id` identifies the executor; preserved
request metadata never independently dispatches work. Completion is local when executor
and parent coincide. Otherwise it uses the validated parent and existing outbox state.
Preserve delivered or uncertain receipts; never infer permission to resend from recovery.

## Explicit provider-conversation replacement

An owner-authorized unrecoverable initial homepage operation may have no binding at all.
`prepare_unaccepted_first_binding_rebind(registry_path, request=<validated transport_request>,
prior=<fresh operation audit>)` supports that case only. The audit preserves explicit false Send,
explicit null pairing/observed-conversation/archive fields, the original operation and tab,
prompt hash, and receipt paths. It refuses missing or possible acceptance, changed prompt/model/
effort, or an existing binding/direction record. Admission reserves `CONTEXT_RESET_PENDING`
with the distinct deterministic Agentify key, the complete audit in `request_history`, and no
fabricated quarantined UUID. Repeating the same preparation is idempotent. Normal observed
post-Send binding retains this history and additionally checks the frozen prompt/model/effort.
The Transport establishes the fresh external facts; this local helper performs no provider call.

An owner-directed new conversation uses `reset_invalid_provider_context=true`
with `provider_context_reset_evidence={previous_request_id, reset_authority:
"OWNER_DIRECT", owner_instruction: "<exact owner instruction>"}`. It requires a
distinct replacement request ID, preserves the complete prior record (including
unfinished/accepted-send state), and records `reason=owner_requested_new_conversation`.
It does not require or fabricate a blocked answer, zero retrieved paths, or
contamination. Close or transfer the affected request's observation under the owner
instruction; preserve other pending records under their native assignments.
The `quarantined_conversations` map stores the excluded provider ID without
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
conversation during this interval. The reset helper records a distinct deterministic
agentify_stable_key for that admitted generation and preserves the old key in request_history;
ordinary next-round binding carries the current key forward. See agentify.md.

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
`<archive_id>__03_TRANSPORT_FACTS.json`. For GitHub delivery, a short provider chat
receipt that is distinct from the complete response is retained as
`<archive_id>__04_CHAT_RECEIPT.md`; it never occupies `__02_RESPONSE.md`.
When the accepted prompt returns a downloadable Markdown fallback, its complete bytes
occupy `__02_RESPONSE.md` and are also retained in the repository as
`archive/CHAT_FALLBACK_RESPONSE.md`. The scoped GitHub `archive/RESPONSE.md` remains
reserved for actual connector delivery. If both exist, preserve both and compare hashes;
do not overwrite either. Existing files are idempotent only when
their bytes match; a different response or manifest is `ARCHIVE_CONFLICT` and never
overwrites an existing artifact. Provider-visible filename normalization is stored
as `provider_filename`; it never changes the canonical filename or reference order.

## State vocabulary and transitions

The normal GitHub-delivery sequence is:

`RECEIVED` → `DIRECTION_VERIFIED` → `TAB_OPEN` → `PAGE_READY` → `PRO_VERIFIED` →
`PROMPT_READY` → `SEND_ATTEMPTED` →
`SEND_CONFIRMED` → `WAITING_GENERATION` →
`NATURAL_COMPLETION` → `ARCHIVE_PENDING` → `ARCHIVED`.

`UPLOAD_PENDING`/`UPLOAD_CONFIRMED` apply only to explicit attachment-input contracts.
`WAITING_HEARTBEAT` is a retained legacy label, not a scheduler or required new transition.

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

Terminal labels prohibit normal submission transitions; they do not cancel
same-request reconciliation under the owner's Transport-stall repair. Use the
`scripts/transport_contract.py:reconcile_send_effect` with fresh effect evidence and original identity,
not an unrestricted state reset. Preserve prior attempts and blocker notifications.
The helper consumes operator-verified browser evidence; it performs no browser action.
`NOT_ACCEPTED` requires exact restored composer payload, absent current user/generation,
a named repaired interaction, and no conflicting preserved acceptance evidence.
`ACCEPTED` requires the concrete observed conversation and exact paired user identity;
it resumes observation only. An unbound recovery stays on its original recorded home tab.
Before binding an observed first submission, record every actual click in the same-request
prebinding record (canonical binding or exact direction mirror, `conversation_id=null`).
Use the existing binder with original request/payload/routing/tab, the observed UUID/URL and
`--observed-after-successful-send`; it carries the count, history and blocker receipt forward.
After actual recovery/completion, a separately keyed completion receipt may be
staged while the earlier blocker receipt remains in history, including uncertain
delivery facts. No prior notification is retried merely to report completion.

## Tab lease and monitor identity

`tab_lifecycle` may be `OPEN`, `HANDOFF`, or `CLOSED`, but it is never the
conversation identity. The tab lease must remain `OPEN` throughout every
`WAITING_*` state. Ending an executor turn or returning from an observation pass does
not close the tab. Only after natural completion, exact response capture, durable
archive verification, and either receipt staging or an explicit blocked-receipt
record may an agent-created tab be closed by the
normal completion policy; the close must then clear `tab_id` while retaining the
conversation URL/ID and archive paths. A user-owned/explicitly mentioned tab is not
closed without authorization.

The monitor identity is exactly:

`request_id|conversation_binding_key|conversation_id|provider_url`.

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

## Native asynchronous processing

Each author-owned Agentify Transport observes its assigned requests while its parent waits natively.
Each due conversation gets one bounded read in serial; avoid busy polling and do not create
scheduled automations. A pass observes the existing request, never resends it or changes provider identity. Natural
completion archives the paired response; timeout retains the same conversation for recovery.

If a page handle is lost, one recovery tab may be opened from the exact persisted
provider URL; the loaded URL and direction must be re-verified before observation.
Never call `tabs.get()` on an old handle and never treat the new tab ID as a new
identity. The recovered tab remains active while the conversation is pending.

Transport may own overlapping provider generations. Tab leases, outbox entries, archives and
idempotency keys remain request-scoped. Legacy scheduling metadata grants no authority to
recreate the removed automation. Request completion clears only that request's pending
observation; other pending work remains recoverable within the assigned native task. Preserve
each request's recorded observation facts without rewriting another request's state.

## Automatic return outbox

New records use REUSE_DM_TRANSPORT: author and receipt parent are the owning author (DM, or Root for Portfolio vacancy replacement), operator is
its actual native Transport child. execution_thread_id records actual recovery ownership without
rewriting immutable accepted historical metadata. No app-task self-dispatch or Root forwarding.
Existing attempted/uncertain delivery evidence is never restaged during recovery.
The following external-parent procedure applies only when executor differs from parent.

After `ARCHIVED`, call `stage_receipt` from `scripts/transport_contract.py` before
using native `collaboration.send_message` to the validated waiting author parent (DM or Root). The deterministic `message_key` remains
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
failure or timeout is insufficient; the same parent route is preserved.
Terminal blockers without an archive use
`stage_blocker_receipt` with the same parent-session rule. If no valid parent is
available, no outbox message is staged: the receipt records
`required=false`, `receipt_state=RETURN_RECEIPT_BLOCKED`,
`destination_thread_id=null`, and no message key. Preserve the evidence and report the
missing parent; do not invent a destination or another Send.
