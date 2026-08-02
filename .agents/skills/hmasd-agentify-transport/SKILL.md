---
name: hmasd-agentify-transport
description: Use only in the dedicated Agentify Transport Operator task to process one ordered review batch and return its raw responses.
---

# HMASD Agentify Transport

## Boundary

This Skill grants only the runtime authority in
`.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md`. It performs no science,
archival intake, workflow design, code, Git or project-state work.

The batch request fields are:

```text
batch_id|manifest_path|return_task_id
```

The manifest is JSON with the same `batch_id` and one ordered `items` array.
Every item has exactly:

```text
request_id|review_channel|provider|expected_model|stable_key|question_path
```

`provider` is `chatgpt` or `gemini`. Preserve manifest order. Read only each
named standalone question; do not prepend metadata, select science or load
requester history. A manifest may contain only questions already frozen by the
requester; a future barrier-dependent follow-up belongs in a later batch.

## Normal path

1. Read and validate the manifest. If it cannot be read or processing cannot
   begin, send one `AGENTIFY_REVIEW_BATCH_RESULT` with `status=ERROR`; do not
   attempt any item.
2. For every item in manifest order, read the question once and call
   `agentify_query` once with exactly `key=stable_key`, `model=provider`,
   `expectedModel=expected_model`, the question as `prompt`, and
   `timeoutMs=2700000`. A ChatGPT Pro item uses `GPT-5.6 Pro`. On the existing
   idle page, Agentify keeps a matching model or selects the exact target and
   confirms it before typing. If that target is unavailable, record item
   `ERROR` before send. Omit every optional content field, including
   `contextPaths`, `attachments`, `bundleName` and `promptPrefix`. The tool owns
   whole-payload insertion, one send and the natural-completion wait.
3. On success, write the actual returned assistant text to
   `temp/sessions/agentify_transport_operator/<batch_id>/<request_id>/response.md`
   and record item `status=COMPLETE`. On error, record item `status=ERROR` and
   continue to the next item.
4. After every item is terminal, write the ordered item results to
   `temp/sessions/agentify_transport_operator/<batch_id>/results.json` and send
   one `AGENTIFY_REVIEW_BATCH_RESULT` to `return_task_id` with
   `status=COMPLETE`, the results path and an empty batch error, using
   Codex-native `send_message_to_thread` without model or thinking overrides.

Batch `COMPLETE` means every registered item was attempted and recorded; it
does not imply every item succeeded. Process one batch at a time. Native task
messages supply the inter-batch queue; do not add a registry or scheduler.

## One simple fallback

Never call `agentify_query` twice for one item. If it errors while the same
page is already generating, call `agentify_wait_response` once with the same key,
provider and timeout. That blocking call sends nothing and returns only after
natural completion. Write and return its response exactly like the normal path.
If it also errors, record item `status=ERROR` with the real error and continue.
Do not navigate,
switch keys, use `agentify_review_query`, recover an old response, create a
monitor or invent another recovery path.

Item `COMPLETE` requires the actual query response and file-write results. Batch
`COMPLETE` requires the results-file and message-delivery results.
Never claim an action that no tool result proves.
