---
name: hmasd-chatgpt-pro-transport
description: "Execute and monitor exact Pro requests in the independent Luna/high Transport task using Codex built-in browser; archive complete responses and notify the assigning author DM."
---

# Independent browser Transport

OWNER_DIRECT 2026-09-14 replaces Agentify MCP and native Transport children. Read the live
endpoint and registry path in C:/Projects/HMASD/.codex/hmasd-transport.toml. Use only the
supported Codex built-in browser (iab) API; initialize through the current tool documentation
and read its returned methods before acting. Screenshots are useful when page layout/state is
ambiguous. No Agentify operation, strict query, process or receipt is a readiness prerequisite.

## Assignment and concurrency

The author supplies request ID, exact prompt or immutable HANDOFF revision, input/delivery scope,
provider model/effort, conversation binding, archive destination and actual parent_thread_id.
Use send_message_to_thread to the registered Transport. The executor is an independent
Luna/high task serving related concurrent transport work; native-child batch rotation does not
apply to this service. It owns no science, experiment monitoring or main Git index. DM owns
scientific authorship, intake and difficult technical repair; the request-owning DM handles shared coordination.

Maintain a per-request queue and existing binding registry. One executor and one pending request
per provider conversation; different conversations can generate concurrently. Perform short
browser actions, move to other ready requests, then bounded observation/waits (up to 60 seconds
per wait). Do not block the entire queue until one answer finishes. A generating answer is real
pending work: retain observation until terminal or explicitly handed over. End when no requests
remain; a new App assignment starts a new turn. No ACK or Root-report loop.

### Durable outstanding assignments and turn completion

On each incoming assignment, persist its request ID and exact input reference, author/return
route, binding, observed acceptance state, archive destination and next action before switching
to another request. Keep this queue in `pending-requests.json` beside the configured binding
registry; reuse any existing per-request durable queue by recording its path there rather than
maintaining competing copies. This is execution state owned by Transport, not a new approval
or scientific ledger. A request waiting to be inspected is outstanding even without a provider
acceptance receipt. Deduplicate follow-ups by request ID; retain their new facts and input binding.

At resume/compaction and before finalizing a turn, reconcile the durable outstanding set against
incoming assignments and this turn's completed work. A conversation's old ARCHIVED binding is
not the status of a newer request. Match request identity and actual provider turn; an absent
GitHub response or missing local receipt alone does not prove that Send failed. Preserve the
exact accepted input through same-request recovery.

Completing or reporting one request removes only that request after its full archive and direct
author delivery are recorded. Continue other queued, inspecting, generating, archiving or
undelivered requests. A final response is appropriate only when the outstanding set is empty,
or each remaining request has an explicit handover with a named receiving owner and observable
acceptance of responsibility. A blocker notice alone is not a handover. If interrupted before
recording a newly arrived assignment, recover it from recent App messages on resume; do not
interpret the last successful archive as completion of the service's whole queue. Report concrete
unrecoverable coverage gaps to the affected author DM; no routine Root escalation or status loop.

## Execute from actual page state

1. Read the exact assigned bytes and current request history once. Reuse the bound conversation;
   keep task IDs distinct from provider IDs. For migration, the author releases the old executor
   and records the new execution route separately from immutable historical request fields.
2. Open/select the actual iab conversation, inspect login, requested model/effort and visible
   message/composer state. Fix ordinary navigation/model/composer issues locally. A screenshot
   can resolve an ambiguity; do not repeat an already successful readiness checklist.
3. Send the exact authorized prompt using supported browser controls. Preserve observed user
   turn/URL and effect facts. An ineffective click can be repaired and retried when the exact
   prompt is demonstrably unsent. Timeout or missing Agentify receipt is not a permanent ban.
   If acceptance is unclear, inspect the actual thread/latest matching turn before another Send;
   continue other requests meanwhile. Do not blindly duplicate an accepted request.
4. Observe the matching answer until completion. Do not click Stop/Regenerate as observation.
   Read full text with supported page/copy/download facilities. For GitHub delivery retrieve the
   exact scoped RESPONSE.md at its immutable commit; preserve chat receipt separately. An answer
   existing only on screen/clipboard is not yet a disk archive. Save its complete actual bytes,
   source, request binding, hash and size; never reconstruct missing text from a summary.
5. Send one completion or concrete blocker report directly to the supplied parent App task with
   event/request ID, acceptance facts, full archive paths, remaining issue and next owner/action.
   No routine messages to Root. Author reads full answer and owns scientific intake. Archive-only
   work never authorizes a new scientific request.

## Recovery and handover

DM takes over a difficult browser/tool fault locally, updates the workflow if needed, and returns
operation after avoiding overlapping executors. the request-owning DM coordinates shared access. No routine Root
approval. If an existing conversation cannot be recovered, DM may create and bind a replacement
with the same task/context, recording the reason and unresolved prior effects; first secure any
recoverable old answer and avoid two live submissions of the same request. A unavailable UI/tool
is not evidence that an old request was never accepted. Preserve contrary facts and exact scope.

Use existing archive/registry formats where useful; legacy Agentify fields may remain null or
historical. Old helper interfaces are optional compatibility tools, not launch gates. Do not load
legacy Agentify API instructions as the current procedure. Provider generation capacity remains
an observed account limit; independent sessions do not remove it. Keep protected/user tabs intact.
