---
name: hmasd-agentify-transport
description: Use only in the dedicated Agentify Transport Operator task to send one frozen review question and return its raw response.
---

# HMASD Agentify Transport

## Boundary

The request is exactly:

```text
AGENTIFY_REVIEW_REQUEST
provider=<chatgpt|gemini>
question_path=<absolute frozen UTF-8 question file>
return_task_id=<requester task>
```

The Operator performs no science, intake, workflow design, code, Git or project
state work. It sends only the exact question file. Shell output, metadata,
attachments, context bundles and requester history never enter the prompt.

## Normal path

1. At task start, run `scripts/ensure_agentify_runtime.ps1` once. Require its
   ready receipt and one provider-matching `protectedTab=true` page.
2. Call `agentify_query` with the page's tool-returned key, `provider`,
   `promptPath=question_path` and `timeoutMs=2700000`. For ChatGPT pass
   `expectedModel=Pro`; Agentify owns model selection, whole-file insertion, one
   send and the natural-completion wait.
3. Write the returned new assistant text under
   `temp/sessions/agentify_transport_operator/` and send:

```text
AGENTIFY_REVIEW_RESULT
status=COMPLETE|ERROR
response_path=<path or empty>
error=<empty or actual error>
```

## One fallback

After an error, read the same page status once. If a query is active, wait for
that query without sending. If the page is idle and no response was produced,
repeat the same `agentify_query` once with the unchanged `question_path`.
Otherwise return the actual error. Never ask the requester to rewrite a question,
manifest, batch, identifier or archive merely to retry transport.

Do not create another page, switch conversations, send a placeholder, use
Answer now, or claim completion without the actual returned assistant response.
