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

Each manifest item names `expected_model`; `agentify_query` keeps or selects that
exact model before typing (`GPT-5.6 Pro` for ChatGPT Pro). The operator never
supplies `contextPaths`, attachments, bundles or a prefix.

Every batch begins with the Skill-owned `ensure_agentify_runtime.ps1` service/browser receipt
and one scoped Agentify status. Missing runtime is repaired by the operator or
routed to WDM while the batch remains pending; it is never returned to Explorer
or CPM as an item/batch failure. A runtime-ready claim without both tool results
is invalid.

One post-error `agentify_status` check distinguishes an idle key from a key
still occupied by an active query. The latter receives one no-send
`agentify_wait_response`; an unresolved runtime defect stays internal to
Operator/WDM instead of being returned to the requester. Genuine terminal item
errors still make the batch result `ERROR`; no retry or monitor is added.
