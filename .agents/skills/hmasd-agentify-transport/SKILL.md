---
name: hmasd-agentify-transport
description: Use only in the dedicated Agentify Transport Operator task to complete one ordered file-backed external-review batch through Agentify pages and return the raw responses.
---

# HMASD Agentify Transport

## Assignment

The request is exactly:

```text
AGENTIFY_REVIEW_BATCH_REQUEST
batch_path=<absolute UTF-8 JSON file containing provider and question_paths>
return_task_id=<requester task>
```

Read that exact file once. `question_paths` order is the batch order. Do not scan
temporary directories or reconstruct paths from item names. The sent payload is
only the exact UTF-8 question file; local metadata, paths, logs, context bundles,
attachments and requester history stay local.

## Understand the live page

At task start run `scripts/ensure_agentify_runtime.ps1`. Its receipt proves only
that the desktop/browser processes are present; establish runtime readiness
with scoped Agentify status before sending. Then use Agentify's page tools
directly. Inspect `agentify_tabs`, `agentify_status`, `agentify_read_page`
and `agentify_list_conversations` as needed. The provider home page is a valid
starting point. Use `agentify_tab_create`, `agentify_show`,
`agentify_new_conversation`, `agentify_open_conversation`, `agentify_navigate`
and `agentify_tab_close` to establish useful pages and conversations.

Choose rather than blindly reuse. Start a clean conversation for an independent
review; reuse the matching conversation for a true continuation. Read the page
and question to make that decision. The operator may switch conversations or
tabs during the batch and keep multiple useful sessions available.

## Complete the batch

For each question path:

1. Select or create the appropriate conversation and confirm that the requested
   provider/model and composer are usable.
2. Call `agentify_query` with `promptPath=<question path>`, the selected tab key
   or id, `timeoutMs=2700000`, and the exact visible `expectedModel=Pro` for
   ChatGPT. `Pro` is the current selectable intelligence label; do not replace
   it with the account heading or the separate `GPT-5.6 Sol` option. Agentify owns
   whole-file insertion, visible model selection and the single send.
3. If generation continues, call `agentify_wait_response` on that same page.
   `IN_PROGRESS` means the answer remains pending; continue observing without a
   new query. Only structured `COMPLETE` plus the actual response permits archive
   and advancement.
4. Save the response, question path, conversation URL and item status in one
   results file under `temp/sessions/agentify_transport_operator/`.

The results file has one ordered row per question with `question_path`,
`status`, `response`, `conversation_url` and an actual error when present.
Preserve completed rows if a later item fails. Batch `COMPLETE` requires every
row to contain the actual completed response; otherwise return `ERROR` with the
partial results path.

Then return:

```text
AGENTIFY_REVIEW_BATCH_RESULT
status=COMPLETE|ERROR
results_path=<path or empty>
error=<empty or actual error>
```

## Judgment and recovery

Do not follow an error-code decision table. Inspect the actual page, tabs,
conversation, active query and saved responses, then use the same page controls
to recover. A missing tab, provider home page, stale conversation, elapsed wait
interval or one failed tool call is not terminal. After one failed action,
inspect its postcondition and use at most one suitable page/session recovery
that cannot duplicate or interrupt a send. Preserve completed responses and
continue the remaining batch. Never ask the requester to rewrite an unchanged
batch solely to retry transport.

Never interrupt an active answer, duplicate a possibly submitted question, send
a placeholder, or activate Continue, Retry, Stop or Answer now. Perform no
scientific interpretation, project mutation, Git or workflow design.
