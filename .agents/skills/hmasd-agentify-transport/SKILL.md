---
name: hmasd-agentify-transport
description: Use in the registered Agentify transport child to complete one ordered file-backed external-review batch through Agentify pages and return the raw responses.
---

# HMASD Agentify Transport

```text
agentify_transport_child=parent-specific registered leaf
production_requester_parents=root|code_project_manager|independent_research_explorer
production_requester_partitions=temp/sessions/agentify_transport_operator/root/<assignment>/|temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/|temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/
```

The shared Skill supplies parent-neutral page and result mechanics. Production
CPM requests use `hmasd-cpm-agentify-transport`; Explorer direction requests
and Root research-support requests use `hmasd-explorer-agentify-transport` with
their distinct requester partitions. Each call has one requester, one exact
assignment partition and one return route to that invoker. Root relays any
cross-owner conclusion; configuration tasks are not production Agentify parents.

## Assignment

The requester assignment is exactly:

```text
AGENTIFY_REVIEW_BATCH_ASSIGNMENT
batch_path=<absolute UTF-8 JSON file in the caller's requester partition containing provider, context_path and question_paths>
results_path=<exact assignment-specific output path in that same requester partition>
```

Read that exact `batch_path` once, then read its exact local UTF-8
`context_path` before opening a page. The requester-owned context brief is the
semantic input: it explains in natural language why the batch exists, what a
useful complete outcome means, which page/result conflicts require judgment,
and for each question whether to start clean, continue an exact prior
conversation URL, run concurrently with named questions or remain independent.
Follow those requested relationships; do not infer scientific direction, review
independence, contamination risk, future reuse or grouping from question
similarity or titles. It is understanding input, not a schema or an outbound
prompt. Before relying on any path or schema anchor, the context brief must
state the owning requester and permitted action, frozen/protected meaning and
exclusions, bounded non-duplicating recovery, and completion evidence. The
terminal result remains conclusion-first and must identify the observable
completed response/postcondition and any residual uncertainty. Write
only the exact `results_path` under the caller's closed requester partition:
`temp/sessions/agentify_transport_operator/root/<assignment>/`,
`temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/`,
or `temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/`.
Reject a batch/result path that crosses those partitions or uses the shared
root-level generic locator. Do not write to the legacy root directly.
`question_paths` order is the batch order. Do not scan temporary directories,
infer a result path or reconstruct question paths from item names. The sent
payload is only the exact UTF-8 question file; the local context brief,
metadata, paths, logs, attachments and requester history stay local.
The local `question_path` is an internal transport locator and is never copied
into the Pro-visible payload. Before opening a page, fail closed if the exact
question text contains a local absolute path such as a drive-letter path,
`file://` URI, requester temp path or workspace absolute path. Outbound
evidence locators must instead be minimal: GitHub repository, branch
`aggressive`, and the relevant repository-relative path or paths supplied after
Root publication. A Pro-visible locator block must not contain GitHub raw/blob
URLs, full commit hashes, SHA-256 values, byte counts, receipt fields, or other
artifact-verification metadata. Keep those only in the local batch, strict send
receipt and archive. The question asks for scientific judgment only; never turn
Pro into a file-integrity, code, test, debugging, style, dependency or runtime
reviewer.

## Understand the live page

At task start run `scripts/ensure_agentify_runtime.ps1`. Its receipt proves only
that the desktop/browser processes are present; establish runtime readiness
with scoped Agentify status before sending. Then use Agentify's page tools
directly. Inspect `agentify_tabs`, `agentify_status`, `agentify_read_page`
and `agentify_list_conversations` as needed. The provider home page is a valid
starting point. Use `agentify_tab_create`, `agentify_show`,
`agentify_new_conversation`, `agentify_open_conversation`, `agentify_navigate`
and `agentify_tab_close` to establish useful pages and conversations.

Follow the conversation relationship already stated in the context brief. Use
the page controls to create or open the requested conversation, and verify the
actual conversation URL/ID shown by the page before binding a send or answer to
it. ChatGPT creates the native conversation identity; the child only observes
and returns it as transport evidence. For a requested exact continuation that
cannot be opened, use one safe page/session recovery that cannot duplicate or
interrupt a send; never guess or silently substitute another conversation, and
report the actual error if it remains unavailable. The operator may switch
conversations or tabs during the batch and keep multiple requester-authorized
sessions available.

## Prompt transport invariant

There are two distinct send routes. For a genuinely new conversation, use the
currently supported safe `agentify_query(promptPath=<exact question path>, ...)`
route, record the caller-computed lowercase SHA-256 of the question file, then
record the URL and ID created by ChatGPT; never invent an identity or a strict
review receipt that this route does not return.
For an exact existing conversation URL/ID, use `agentify_review_query`, not
`agentify_query`, with the exact `promptPath`, caller-computed lowercase
SHA-256 of that question file, assigned stable key/idempotency key, visible
`Pro`, and `timeoutMs=2700000`. The strict endpoint itself enforces exact-one
`prompt`/`promptPath` selection and validates the pre-send SHA.

Never source outbound prompt text from shell output, and never place stdout, a
tool result, JSON wrapper, or page wrapper in `prompt`. The question file is
the sole outbound payload. Before treating an exact-continuation send as
complete, require receipt `promptSha256` to equal the published/intended
question-file SHA. For a new-conversation `agentify_query`, retain the locally
computed question-file SHA and do not claim receipt-level SHA evidence. These
rules apply identically in Root and Explorer requester partitions and do not
add identity, authentication, or state-machine work.

Conversation memory and browser-tab ownership are different. Closing a tab does
not delete its ChatGPT conversation, and a concrete saved conversation URL can
reopen that memory. Follow the context brief's clean, exact-URL continuation,
independence and concurrency relationships; do not make those semantic choices
from the question or page. Across batches, the requester decides any later
reuse; the child only returns the observed conversation URL/ID. Create only the
non-default tabs actually useful for the requester-authorized relationships and
live tool capacity, and remember only the IDs created during this native task.
An owned idle tab may be reused when the requested relationship and observed
conversation identity remain correct. Completion order may differ from question
order; write result rows in the original `question_paths` order.

After a tab's last intended response is fully saved and no generation is active,
the normal cleanup path closes that tab only if this task created it. Never close
the default tab, a pre-existing/unowned tab, or a tab with an active answer. If
an owned-tab close fails, inspect its postcondition once and make one safe retry;
if it remains open, report residual resource uncertainty while preserving any
complete saved answer and the otherwise complete batch status.

## Complete the batch

Complete every question path and preserve the original path order in the result.
Requester-authorized independent conversations may perform these steps
concurrently on separate owned tabs; preserve every stated dependency within a
conversation. For each question:

1. Select or create the context-requested conversation and confirm that the
   requested provider/model and composer are usable.
 2. Inspect the current composer model immediately before sending. If it shows
    High or any other non-Pro model, actively open the model picker, select Pro,
    and then read the composer again; continue only when the composer visibly
    shows Pro after that action. `expectedModel=Pro`, an available option or
    recognition metadata alone cannot prove that the switch occurred.
 3. For a clean, genuinely new conversation, call `agentify_query` with
    `promptPath=<question path>`, the selected tab key or id,
    `timeoutMs=2700000`, and exact visible `expectedModel=Pro` for ChatGPT. For
    an exact URL/ID continuation, call `agentify_review_query` with that exact
    `promptPath`, caller-computed lowercase question SHA-256, stable key,
    idempotency key, visible Pro and the same timeout. `Pro` is the current
    selectable intelligence label; do not replace it with the account heading
    or the separate `GPT-5.6 Sol` option. Agentify owns whole-file insertion,
    visible model selection and the single send.
 4. Accept the query result only when its structured content reports
    `status=COMPLETE`, contains a full nonempty natural-language response,
    reports visible `modelEvidence=Pro` (or a full label ending in `Pro`), and
    supplies a concrete `https://chatgpt.com/c/<id>` conversation URL. A tool
    `COMPLETE` token, provider-home URL or response fragment is not completion.
    If generation continues, call `agentify_wait_response` with
    `expectedModel=Pro` on that same page. `IN_PROGRESS` means the answer remains
    pending; continue observing silently without a new query. Do not emit
    commentary, progress, ETA, heartbeat, collaboration or intermediate parent
    notification while waiting. Only the actual complete answer plus its
    concrete conversation URL permits archive and advancement.
5. Save the response, question path, caller-computed question SHA-256,
   conversation URL and item status in the exact assigned `results_path`. For
   an exact-continuation review, also save receipt `promptSha256`; a `COMPLETE`
   continuation row requires it to equal the published/intended question SHA.

Before returning `COMPLETE`, run the read-only result-path guard at
`.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py`
with `--repo`, `--expected-results-path` and `--returned-results-path`. It
must validate the exact physical assignment file and the caller's requester
partition. On guard failure return
`ERROR` with an empty `results_path` and the actual error; do not move, copy,
rewrite or read result contents. The guard rejects the shared root-level
`temp/sessions/agentify_transport_operator/results.json` locator.

The results file has one ordered row per question with `question_path`,
`question_sha256`, `status`, `response`, `conversation_url`, `model_evidence`,
the strict continuation receipt `promptSha256` when that route was used, and
an actual error when present. Copy response and metadata only from the
structured terminal tool
result; never substitute page chrome, a provider-home URL or a partial preview.
Treat tool state as page evidence, not as the completeness decision. Read the
actual answer and reconcile it with the live conversation: an abruptly cut-off
sentence, an answer that has not addressed the question, or a page still
showing generation is `IN_PROGRESS` even if one tool call says `COMPLETE`.
Preserve completed rows if a later item fails. Batch `COMPLETE` requires every
row to contain the actual completed response; otherwise return `ERROR` with the
partial results path.

Then return exactly once through the native child final response. Begin with a
natural-language conclusion stating whether each question was actually
answered, the direct consequence checked and any residual uncertainty or
observable conflict; append the exact packet anchors below:

```text
AGENTIFY_REVIEW_BATCH_RESULT
status=COMPLETE|ERROR
results_path=<exact assigned path or empty>
error=<empty or actual error>
```

## Judgment and recovery

Do not follow an error-code decision table. Inspect the actual page, tabs,
conversation, active query and saved responses, then use the same page controls
to recover. A missing tab, provider home page, stale conversation, elapsed wait
interval or one failed tool call is not terminal. On a fetch/client failure
after an exact-continuation send, inspect the durable operation first, then use
`agentify_review_query(verifyExisting=true, ...)` only with the exact original
fingerprint (including stable key, idempotency key, conversation URL/ID, model,
question SHA and timeout). It is observation, never a resend. Do not alter one
field to bypass a conflict. After one failed action, inspect its postcondition
and use at most one suitable page/session recovery that cannot duplicate or
interrupt a send. Preserve completed responses and continue the remaining
batch. Never ask the requester to rewrite an unchanged batch solely to retry
transport.

Never interrupt an active answer, duplicate a possibly submitted question, send
a placeholder, or activate Continue, Retry, Stop or Answer now. Perform no
scientific interpretation, project mutation, Git or workflow design. The
native child returns exactly once, only at terminal `COMPLETE` or `ERROR`; never
use a task id, cross-task result relay or parent polling loop.
