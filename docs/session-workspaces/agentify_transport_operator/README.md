# Agentify Transport Operator workspace

Requesters write one minimal JSON file containing `provider` and ordered
`question_paths`, then send one `AGENTIFY_REVIEW_BATCH_REQUEST` with its
`batch_path` and `return_task_id`. The Operator follows
`.agents/skills/hmasd-agentify-transport/SKILL.md`, processes the questions in
order on the existing protected provider page, waits for each response, writes
one results file here, and returns one `AGENTIFY_REVIEW_BATCH_RESULT`.

Selection, archival and interpretation remain with the requester. Runtime,
page, model and one-fallback mechanics remain with the Operator. Retry reuses
the unchanged batch file; no requester-side transport artifact is rewritten.
