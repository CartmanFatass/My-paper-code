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

Each manifest item names `provider` and `expected_model`. The operator derives
the unique provider-matching `protectedTab=true` entry at runtime and passes its
tool-returned key to `agentify_query`; the query then owns its internal selector and keeps or selects that exact
visible model before typing (`Pro` for ChatGPT Pro). The operator never creates
a second page or supplies `contextPaths`, attachments,
bundles or a prefix.

Every batch begins with the Skill-owned `ensure_agentify_runtime.ps1` service/browser receipt,
one tab inventory and one scoped Agentify status. Missing runtime is repaired by the operator or
routed to WDM while the batch remains pending; it is never returned to Explorer
or CPM as an item/batch failure. A runtime-ready claim without all three results
is invalid.
Run the preflight through the shell's elevated permission path so the registered
Agentify profile at `C:\Users\fires\.agentify-desktop\chrome-user-data` remains
usable; never replace it with a temporary profile.

One post-error `agentify_status` check distinguishes an idle key from a key
still occupied by an active query. The latter receives one no-send
`agentify_wait_response`; an unresolved runtime defect stays internal to
Operator/WDM instead of being returned to the requester. Genuine terminal item
errors still make the batch result `ERROR`. A closed page/tab/controller reruns
preflight once; the exact query is retried only after the same provider's unique
pinned protected page reappears. No new page, monitor, alternate page or additional retry is added.
