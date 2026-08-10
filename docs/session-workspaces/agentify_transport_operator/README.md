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
The requester-owned context brief names each question's clean, exact-URL
continuation, named concurrency and independence relationship; the transport
child follows that meaning and does not infer scientific direction, review
independence, contamination risk, future reuse or grouping from similarity or
titles. Requesters retain scientific selection, interpretation and durable
intake; a retry reuses the unchanged batch file.

The ordered results file records `question_path`, `status`, the actual raw
`response`, `conversation_url`, `model_evidence` and any direct error for every attempted item.
Completed rows survive a later item error. The process preflight receipt is not
page readiness; the child confirms scoped Agentify status before sending. The
parent receives no commentary, heartbeat or intermediate notification and
reads only the exact returned file after `COMPLETE` or `ERROR`.

After writing and before terminal `COMPLETE`, the child runs
`.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py`
with the assignment path and returned terminal anchor. Explorer and CPM run
the same guard after terminal return and before reading/accepting the file.
The guard requires a strict physical assignment descendant, rejects redirects
and the shared root-level `results.json`, and reports `ERROR` with an empty
`results_path` on mismatch or missing/non-regular files. It never reads,
copies or rewrites response contents.

Tabs are browser containers, while conversations hold the memory: closing a tab
does not delete its conversation, and a saved conversation URL can reopen it.
The child uses page controls to create or open the context-requested
conversation and verifies the observed URL/ID; ChatGPT creates the native
conversation identity and the requester decides any later reuse. If a requested
exact continuation cannot be opened, one safe page recovery may be attempted,
but the child never guesses or silently substitutes another conversation and
reports the actual error if it remains unavailable. During one native task it
remembers only the IDs of tabs it created, may create as many non-default tabs
as the requester-authorized relationships and live tool capacity make useful,
and may reuse an owned idle tab only when that requested relationship and
observed identity remain correct. After each owned tab's last intended response
is saved and no generation is active, it closes only that owned tab;
the default and pre-existing/unowned tabs, and any tab with an active answer,
remain untouched. A failed close gets one postcondition inspection and one safe
retry; an owned tab that remains is residual resource uncertainty, not grounds
to discard a complete answer or turn an otherwise complete review into
`ERROR`. Result rows still follow the original question order even when
conversations finish out of order.
