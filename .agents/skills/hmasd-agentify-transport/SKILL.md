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

## Runtime preflight

Before interpreting any tab/key state or attempting an item, run the following
through the shell with `sandbox_permissions=require_escalated` because Agentify
Desktop writes its registered isolated profile and launches Chrome:

```powershell
& .agents/skills/hmasd-agentify-transport/scripts/ensure_agentify_runtime.ps1
```

The required profile is `C:\Users\fires\.agentify-desktop\chrome-user-data`
with profile directory `Default`. Do not move it to `C:\tmp`, create another profile or substitute
a bare Chrome launch. If escalation is denied, report that exact internal
runtime error to WDM and keep the batch pending.

Require its `AGENTIFY_RUNTIME_READY` receipt, then call one scoped
`agentify_status`. A missing Agentify service or browser process is an Operator runtime defect, not an item result.
Repair the runtime and repeat only this preflight. If it still
fails, report the exact script/tool error to WDM and keep the batch pending; do not send a batch `ERROR` to the requester.
Residual `tabId`, `activeQuery` or
`waiting_for_ready` data never proves that Chrome is running. Never claim
runtime readiness without both actual tool results.

## Mechanical lifecycle

Use only this lifecycle; do not improvise another procedure:

```text
BOOT -> PAGE -> SEND -> WAIT -> ARCHIVE -> COMPLETE
              \-> page/tab/controller closed or controls not ready -> same key -> retry once
SEND or WAIT error with activeQuery -> WAIT the same query without another send
recovery exhausted -> ERROR
```

`COMPLETE` and `ERROR` are the only terminal states. A closed page is a
recoverable event, not a terminal state. This lifecycle replaces scattered
fallback decisions and adds no ledger, monitor, hash, registry or approval gate.

## Normal path

1. Complete the runtime preflight, then read and validate the manifest. If the
   manifest cannot be read or processing cannot
   begin, send one `AGENTIFY_REVIEW_BATCH_RESULT` with `status=ERROR`; do not
   attempt any item.
2. For every item in manifest order, read the question once and call
   `agentify_query` once with exactly `key=stable_key`, `model=provider`,
   `expectedModel=expected_model`, the question as `prompt`, and
   `timeoutMs=2700000`. A ChatGPT Pro item uses the exact visible label `Pro`. On the existing
   idle page, Agentify keeps a matching model or selects the exact target and
   confirms it before typing. If that target is unavailable, record item
   `ERROR` before send. Omit every optional content field, including
   `contextPaths`, `attachments`, `bundleName` and `promptPrefix`. The tool owns
   whole-payload insertion, one send and the natural-completion wait.
3. On success, write the actual returned assistant text to
   `temp/sessions/agentify_transport_operator/<batch_id>/<request_id>/response.md`
   and record item `status=COMPLETE`. On error, perform the single read-only
   key check and the matching fallback below before assigning a terminal item
   status. Record `ERROR` only after the one applicable recovery is exhausted;
   items on other keys may continue.
4. After every item is terminal, write the ordered item results to
   `temp/sessions/agentify_transport_operator/<batch_id>/results.json` and send
   one `AGENTIFY_REVIEW_BATCH_RESULT` to `return_task_id` with
   `status=COMPLETE` only when every item completed, otherwise `status=ERROR`,
   the results path and the real batch error, using
   Codex-native `send_message_to_thread` without model or thinking overrides.

Batch `COMPLETE` means every registered item succeeded. Process one batch at a time. Native task
messages supply the inter-batch queue; do not add a registry or scheduler.

## One simple fallback

After an error, call `agentify_status` once for the same key. If it returns
`tab_not_found`, the query returned `model_switcher_unavailable`, or status
proves the page/tab/controller was closed, call
`agentify_query` one more time with the exact same key, provider, expected
model, question and timeout. Agentify reopens the same-key page; this is the only retry,
and it is never delegated back to the requester. If the same page
still has an active query, call `agentify_wait_response` once with the same key,
provider and timeout and never resend.
That blocking call sends nothing and returns only after natural completion. Write
and return its response exactly like the normal path. If the wait also errors
while the query remains active, report the exact runtime defect to WDM and keep
the affected item pending; do not relabel it as a scientific/reviewer failure or
return it to the requester. If the one page-recovery query also fails, record the
real item error and continue normally.
Do not navigate,
switch keys, use `agentify_review_query`, recover an old response, create a
monitor or invent another recovery path.

Item `COMPLETE` requires the actual query response and file-write results. Batch
`COMPLETE` requires the results-file and message-delivery results.
Never claim an action that no tool result proves.
