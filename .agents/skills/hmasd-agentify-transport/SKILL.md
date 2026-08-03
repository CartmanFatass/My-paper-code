---
name: hmasd-agentify-transport
description: Use only in the dedicated Agentify Transport Operator task to process one ordered file-backed review batch and return its raw responses.
---

# HMASD Agentify Transport

## Boundary

The request is exactly:

```text
AGENTIFY_REVIEW_BATCH_REQUEST
batch_path=<absolute UTF-8 JSON file containing provider and question_paths>
return_task_id=<requester task>
```

The batch JSON contains only `provider` and `question_paths`. Array order is
the send order. Read the exact assigned `batch_path`; never discover a batch by
scanning the Operator workspace and never derive paths from item names. The
Operator performs no science, intake, workflow design, code, Git or project
state work. It sends only the exact question files named by the batch. Shell output, metadata,
attachments, context bundles and requester history never enter the prompt.

## Normal path

1. Read the exact `batch_path` once and preserve `question_paths` order. At task start, run
   `scripts/ensure_agentify_runtime.ps1` once. Require its
   ready receipt and one provider-matching `protectedTab=true` page.
2. For each ordered question path, call `agentify_query` with the page's
   tool-returned key, `provider`, `promptPath=<question path>` and
   `timeoutMs=2700000`. For ChatGPT pass `expectedModel=Pro`; Agentify owns model
   selection, whole-file insertion and one send. If the same page is still
   generating when the call returns, immediately call `agentify_wait_response`
   on that page with `timeoutMs=2700000`. `IN_PROGRESS` repeats that same wait
   call; it never sends. Never end the turn, resend or start the next item before
   the completed response returns.
3. Write every returned assistant text plus its question path and item status
   into one results file under `temp/sessions/agentify_transport_operator/` and send:

```text
AGENTIFY_REVIEW_BATCH_RESULT
status=COMPLETE|ERROR
results_path=<path or empty>
error=<empty or actual error>
```

## One fallback

After an item error, read the same page status once. An active query uses the
standard `agentify_wait_response` path. If the page is idle and no response was
produced, repeat that item once with the unchanged question path; otherwise
record the actual error. Never ask the requester to rewrite the batch file.

Do not create another page, switch conversations, send a placeholder, use
Answer now, or claim completion without the actual returned assistant response.
