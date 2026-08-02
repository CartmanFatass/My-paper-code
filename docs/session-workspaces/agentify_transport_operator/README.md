# Agentify Transport Operator workspace

Requesters send one `AGENTIFY_REVIEW_REQUEST` containing `provider`, the frozen
`question_path` and `return_task_id`. The task sends it, waits, writes the raw
response under `temp/sessions/agentify_transport_operator/`, and returns one
`AGENTIFY_REVIEW_RESULT`. Requesters own selection, archival and interpretation
and may continue unrelated work. A retry reuses the same question path; no
requester-side file is rewritten.

Each request names only `provider`. The operator derives
the unique provider-matching `protectedTab=true` entry at runtime and passes its
tool-returned key to `agentify_query`; the query then owns its internal selector and keeps or selects that exact
visible model before typing (`Pro` for ChatGPT). The operator never creates
a second page or supplies `contextPaths`, attachments,
bundles or a prefix.

Every task begins with the Skill-owned `ensure_agentify_runtime.ps1` service/browser receipt,
one tab inventory and one scoped Agentify status. Missing runtime is repaired by the operator or
routed to WDM while the request remains pending. A runtime-ready claim without all three results
is invalid.
Run the preflight through the shell's elevated permission path so the registered
Agentify profile at `C:\Users\fires\.agentify-desktop\chrome-user-data` remains
usable; never replace it with a temporary profile.

One post-error `agentify_status` check distinguishes an idle key from a key
still occupied by an active query. The latter receives one no-send
`agentify_wait_response`; an unresolved runtime defect stays internal to
Operator/WDM instead of being returned to the requester. Genuine terminal item
errors return the request result `ERROR`. A closed page/tab/controller reruns
preflight once; the exact query is retried only after the same provider's unique
pinned protected page reappears. No new page, monitor, alternate page or additional retry is added.
