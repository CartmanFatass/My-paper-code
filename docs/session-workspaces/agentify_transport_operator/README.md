# Agentify Transport Operator workspace

Requesters send `AGENTIFY_REVIEW_BATCH_REQUEST`; the task processes the ordered
manifest sequentially and returns one `AGENTIFY_REVIEW_BATCH_RESULT`. Raw
responses use
`temp/sessions/agentify_transport_operator/<batch_id>/<request_id>/response.md`
and the ordered mechanical result uses
`temp/sessions/agentify_transport_operator/<batch_id>/results.json`. Requesters
own item selection, archival and interpretation and continue unrelated work
while the batch runs. The task loads `hmasd-agentify-transport`; no science or
project state is stored here.

Each manifest item names `expected_model`; the operator checks the visible model
before sending and never supplies `contextPaths`, attachments, bundles or a
prefix to `agentify_query`.
