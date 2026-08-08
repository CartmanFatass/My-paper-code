# Agentify Transport Operator workspace

CPM or Explorer dispatches one production `hmasd-agentify-transport` child;
WDM may dispatch its own workflow-acceptance smoke child. Each exact minimal
assignment names `batch_path` and assignment-specific `results_path`, while the
batch names one local natural-language `context_path` plus ordered question
files. The child does not reconstruct a queue, scan this workspace or
poll the parent. It follows `.agents/skills/hmasd-agentify-transport/SKILL.md`:
understand the live Agentify pages, create/read/select/switch ChatGPT
conversations, process the ordered questions, wait silently for natural
completion, write the exact results file and return one native terminal result.
Independent reviews normally receive clean conversations; true follow-ups reuse
the matching conversation. Requesters retain scientific selection,
interpretation and durable intake; a retry reuses the unchanged batch file.

The ordered results file records `question_path`, `status`, the actual raw
`response`, `conversation_url`, `model_evidence` and any direct error for every attempted item.
Completed rows survive a later item error. The process preflight receipt is not
page readiness; the child confirms scoped Agentify status before sending. The
parent receives no commentary, heartbeat or intermediate notification and
reads only the exact returned file after `COMPLETE` or `ERROR`.
