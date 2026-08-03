# Agentify Transport Operator workspace

Requesters send one exact minimal JSON `batch_path` plus `return_task_id`; the
Operator does not reconstruct a queue from this workspace. The
Operator follows `.agents/skills/hmasd-agentify-transport/SKILL.md`: understand
the live Agentify pages, create/read/select/switch ChatGPT conversations, process
the ordered questions, wait for natural completion, and return one results file.
Independent reviews normally receive clean conversations; true follow-ups reuse
the matching conversation. Requesters retain scientific selection,
interpretation and durable intake; a retry reuses the unchanged batch file.

The ordered results file records `question_path`, `status`, the actual raw
`response`, `conversation_url` and any direct error for every attempted item.
Completed rows survive a later item error. The process preflight receipt is not
page readiness; the Operator confirms scoped Agentify status before sending.
