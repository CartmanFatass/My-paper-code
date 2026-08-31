# State and evidence schema

The registry is JSON at a caller-supplied path (default project-local path:
`temp/sessions/hmasd-chatgpt-pro-transport/registry.json`). Keep one record per
`direction_id`; do not overwrite a record with a different `conversation_id`.

```json
{
  "direction_id": "finite_resource_relational_inductive_efficiency",
  "source_thread_id": "01a...",
  "conversation_id": "6a...",
  "provider_url": "https://chatgpt.com/c/6a...",
  "tab_id": "7",
  "tab_lifecycle": "OPEN",
  "last_reopened_at": null,
  "request_id": "req-...",
  "visible_model": "Pro",
  "underlying_model": "GPT-5.6 Sol",
  "thinking_effort": "5/5",
  "source_mode": "paste",
  "prompt_path": null,
  "companion_prompt": null,
  "prompt_sha256": "...",
  "reference_files": [
    {
      "path": ".../REFERENCE_FILES.md",
      "filename": "REFERENCE_FILES.md",
      "bytes": 1234,
      "sha256": "...",
      "uploaded": true
    }
  ],
  "response_sha256": null,
  "state": "WAITING_GENERATION",
  "send_evidence": {
    "send_click_count": 1,
    "url_observed": true,
    "user_node_observed": true,
    "user_node_exact": true,
    "attachment_observed": false
  },
  "timestamps": {
    "received_at": "...Z",
    "pro_verified_at": "...Z",
    "sent_at": "...Z",
    "generation_started_at": "...Z",
    "completed_at": null,
    "captured_at": null,
    "archived_at": null
  },
  "archive": {
    "prompt_file": "...",
    "response_file": null,
    "transport_fact_file": null
  },
  "heartbeat": {
    "automation_id": "...",
    "status": "ACTIVE",
    "retired_at": null,
    "retirement_verified": false
  },
  "return_receipt": {
    "required": true,
    "destination_thread_id": "01a...",
    "status": "PENDING",
    "sent_at": null,
    "message_key": null,
    "error": null
  }
}
```

## State vocabulary

`RECEIVED` → `DIRECTION_VERIFIED` → `TAB_OPEN` → `PAGE_READY` →
`PRO_VERIFIED` → `PROMPT_READY` → `UPLOAD_PENDING`/`UPLOAD_CONFIRMED` →
`SEND_ATTEMPTED` → `SEND_CONFIRMED` → `WAITING_GENERATION` →
`WAITING_HEARTBEAT` → `NATURAL_COMPLETION` → `ARCHIVE_PENDING` → `ARCHIVED`.

Terminal or attention states are `SEND_UNCERTAIN`, `SENT_INPUT_MISMATCH`,
`WAITING_UNKNOWN`, `WAITING_TIMEOUT`, `UPLOAD_READY_SEND_DISABLED`, `MODEL_UNVERIFIED`,
`DIRECTION_UNVERIFIED`, `ARCHIVE_CONFLICT`, `RECOVERY_URL_MISMATCH`,
`RETURN_RECEIPT_UNCERTAIN`, `RETURN_RECEIPT_BLOCKED`, and `BLOCKED`.
A timeout or browser exception is never converted into a new conversation.

`tab_lifecycle` is ephemeral and may be `OPEN`, `HANDOFF`, or `CLOSED`; it is never
the conversation identity. Once a complete response is archived, set
`tab_lifecycle=CLOSED`, clear `tab_id`, and retain `conversation_id`, `provider_url`,
and archive paths. A later wake opens a new temporary tab from that exact URL and
closes it again after its bounded read.

## Send evidence

`SEND_CONFIRMED` requires all of:

1. a concrete provider URL containing one conversation UUID;
2. one visible user message node in that conversation;
3. the exact supplied prompt text in that node, byte-equivalent after the page's
   visible newline normalization; and
4. for upload mode, the file group plus the exact companion text, when one was
   supplied; and
5. for a non-empty `reference_files` list, every expected file group is associated
   with the bound conversation and matches its pre-upload size/hash. Provider-side
   filename normalization or placement is recorded as evidence but is not a failure
   by itself; no orthogonality or same-turn filename condition is required.

A URL alone, a cleared composer, a spinner, an attachment chip before Send, or a
`ChatGPT said` heading without a complete response is insufficient.

## Natural completion evidence

Capture only when the same conversation has a complete assistant node, the active
generation controls are absent, and the page reports completion (for example
`Response complete`). Keep the raw assistant node separate from status text and UI
labels. Hash the exact bytes written to the response file.

## Heartbeat contract

The 15-minute heartbeat reads pending records under a per-conversation lock. It may
reopen or reclaim the mapped tab from the persisted provider URL, but it may not
send, retry, switch direction, create a replacement conversation, or click `Answer
now`. On natural completion it captures/archives once, closes the temporary tab,
and clears its ephemeral handle; heartbeat retirement follows the single/shared
task-close rule below. On a 60-minute
timeout it keeps the record and same conversation in `WAITING_TIMEOUT`; when the
conversation ID is known it may close the temporary tab and recover it from the URL
on a later wake. A missing or mismatched URL is a blocker, not a replacement route.

For a heartbeat shared by multiple directions, retain it while any record still
requires a wake or recoverable timeout. After the final record is durably archived,
or reaches an explicit terminal/blocker state with no scheduled recovery, update the
existing automation to `PAUSED` (or otherwise disable it), verify the disabled status,
and persist `retired_at` plus `retirement_verified=true`. Do not retire a shared
heartbeat when only one direction has finished, and do not leave it active after the
transport task has no pending recovery work.

After durable archive verification, send one structured `ARCHIVED` receipt to the
record's exact `destination_thread_id` via `send_message_to_thread`; include the
request/direction IDs, provider conversation URL, response hash, archive paths, and
heartbeat status. Persist the receipt timestamp, a deterministic message key, and
delivery status. If the destination is missing or unresolved, retain the archive but
set `RETURN_RECEIPT_BLOCKED`; if delivery is uncertain, set
`RETURN_RECEIPT_UNCERTAIN` without sending a duplicate or rerouting to another
session. A terminal blocker without an archive receives the analogous blocker
receipt when possible.
