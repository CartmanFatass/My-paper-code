# State and evidence schema

The registry is JSON at a caller-supplied path (default project-local path:
`temp/sessions/hmasd-chatgpt-pro-transport/registry.json`). Keep one record per
`direction_id`; do not overwrite a record with a different `conversation_id`.

```json
{
  "direction_id": "finite_resource_relational_inductive_efficiency",
  "conversation_id": "6a...",
  "provider_url": "https://chatgpt.com/c/6a...",
  "tab_id": "7",
  "request_id": "req-...",
  "visible_model": "Pro",
  "underlying_model": "GPT-5.6 Sol",
  "thinking_effort": "5/5",
  "source_mode": "paste",
  "prompt_path": null,
  "prompt_sha256": "...",
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
`DIRECTION_UNVERIFIED`, `ARCHIVE_CONFLICT`, and `BLOCKED`. A timeout or browser
exception is never converted into a new conversation.

## Send evidence

`SEND_CONFIRMED` requires all of:

1. a concrete provider URL containing one conversation UUID;
2. one visible user message node in that conversation;
3. the exact supplied prompt text in that node, byte-equivalent after the page's
   visible newline normalization; and
4. for upload mode, the expected filename/file group plus the exact companion text,
   when one was supplied.

A URL alone, a cleared composer, a spinner, an attachment chip before Send, or a
`ChatGPT said` heading without a complete response is insufficient.

## Natural completion evidence

Capture only when the same conversation has a complete assistant node, the active
generation controls are absent, and the page reports completion (for example
`Response complete`). Keep the raw assistant node separate from status text and UI
labels. Hash the exact bytes written to the response file.

## Heartbeat contract

The 15-minute heartbeat reads pending records under a per-conversation lock. It may
reopen or reclaim the mapped tab, but it may not send, retry, switch direction,
create a replacement conversation, or click `Answer now`. On natural completion it
captures/archives once and disables its own pending wake. On timeout it keeps the
record and same conversation in `WAITING_TIMEOUT` for human attention.
