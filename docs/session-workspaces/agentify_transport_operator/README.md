# Agentify Transport Operator workspace

Requesters send one exact minimal JSON `batch_path` plus `return_task_id`; the
Operator does not reconstruct a queue from this workspace. The
Operator follows `.agents/skills/hmasd-agentify-transport/SKILL.md`: process the
ordered questions on the protected page, hold long generation with
`agentify_wait_response`, and return one results file. Requesters retain
selection, archival and interpretation; retry reuses the unchanged batch file.
