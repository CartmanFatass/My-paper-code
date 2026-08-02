---
name: hmasd-agentify-transport
description: Use only in the dedicated Agentify Transport Operator task to send one standalone review question and return the raw response.
---

# HMASD Agentify Transport

## Boundary

This Skill grants only the runtime authority in
`.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md`. It performs no science,
archival intake, workflow design, code, Git or project-state work.

The exact request fields are:

```text
request_id|review_channel|provider|stable_key|question_path|return_task_id
```

`provider` is `chatgpt` or `gemini`. Read only the named standalone question;
do not prepend metadata or load requester history.

## Normal path

1. Read the question text exactly once.
2. Call `agentify_query` once with `key=stable_key`, `model=provider`, the exact
   question as `prompt`, `timeoutMs=2700000`, and no attachment, context bundle,
   prefix or alternate key. The tool owns readiness, whole-payload insertion,
   one send and the natural-completion wait.
3. On success, write the actual returned assistant text to
   `temp/sessions/agentify_transport_operator/<request_id>/response.md`.
4. Send one `AGENTIFY_REVIEW_RESULT` to `return_task_id` with
   `status=COMPLETE`, the response path and an empty error, using Codex-native
   `send_message_to_thread` without model or thinking overrides.

## One simple fallback

If the query call errors, inspect `agentify_status` once for the same key and
provider. Never interrupt or resend while generation is active. If it is idle,
retry the same `agentify_query` once; after another error return `status=ERROR`
with the real error. Do not navigate, switch keys, use `agentify_review_query`,
recover an old response, create a monitor or invent another recovery path.

`COMPLETE` requires the actual query response, file write and message-delivery
results. Never claim an action that no tool result proves.
