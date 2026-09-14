# Agentify objects, interfaces and recovery

Use the currently exposed MCP schemas. This reference explains their boundaries; it does not
require every tool on every request. Implementation is in `C:/Projects/agentify-desktop/`,
principally `mcp-server.mjs`, `chatgpt-controller.mjs` and `review-transport.mjs`.
Read code only for a concrete adapter defect, not to reconfirm a successful operation.

## Which interface answers which question?

| Question | Interface / fields | Interpretation |
| --- | --- | --- |
| Which browser/tab is controlled? | `agentify_status({tabId})`; `agentify_tabs({})` if the handle is unknown | Key, URL, browser provenance and protection identify the target. A logical handle alone does not prove its browser target is still live. |
| Can the page accept ordinary input? | Status `blocked`, `promptVisible`, `indicators` | Input readiness, not model correctness, menu readiness or successful Send. `readyState=complete` describes document loading, not answer completion. |
| What can be interacted with now? | `agentify_operator_observe({tabId})`: `controls`, `composer`, `revision` | A point-in-time UI projection. Use current target IDs and the returned URL/revision for actions. `actionable=false` may be the operator's restriction, not a disabled webpage control. |
| Is the exact draft already present? | `composer.textLength` and `composer.textSha256` | Composer contents only. Matching text can remain after a pre-Send failure. It is not a sent user message. |
| Was Send attempted or accepted? | Exact persistent review operation: `sendAttempted`, `providerUserMessageId` and paired identity | The attempt flag is written before the external click. Acceptance needs the request's paired user turn or independently task-bound delivery; neither follows from an empty composer. |
| Has this request finished? | Strict observation/archive receipt; alternatively task-bound GitHub delivery | `wait_response COMPLETE` or page text alone is not an immutable, request-paired full archive. |

`generation.activeForbiddenControlLabels` is a list of controls the operator will not click,
not a generation boolean: it can contain `Send prompt` on an unsent draft. Likewise,
`activeQuery=null` means no local active query is reported, not that the provider has finished.
Inspect current response controls/paired observation for generation. Sidebar titles and earlier
answers are not evidence about the current request.

The operator's `reasoning.targets` maps rendered text to clickable ancestors; it is not strict
model/effort certification. A `Pro` account badge or a product selector's `Pro` text does not
prove Pro reasoning effort. Strict `productModelEvidence` and `reasoningEffortEvidence` answer
those separate questions. For ChatGPT the target is GPT-6 Astra (checked `Latest` / current
`6 Pro` identity) with Pro effort. Preserve an existing operation's canonical productModel.

## Handoff and binding

Run maintained helpers from `C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/`.
An older direction checkout may lack a current helper; that is a checkout dependency, not a
browser failure. The control checkout and live transport config determine current helper and
registry paths; frozen HANDOFF commits determine request bytes.

For existing-conversation GitHub handoffs, `scripts/native_transport.py` accepts full
`--handoff-sha`, repository-relative `--handoff-path`, actual `--parent` / `--operator` /
`--assignment` and immutable `--out`. Pass existing `--manifest` and `--prompt` together;
`--claim-registry` makes the brief locked claim. Reuse the result while inputs and executor
are unchanged. The helper validates frozen routing separately from current execution routing.
First-binding and explicit attachment-input contracts use their corresponding existing helpers
and keep their input mode; `native_transport.py` does not support first-binding.

HMASD `conversation_binding_key` identifies the scientific node. Agentify `stableKey`
identifies its concrete provider-conversation generation. The Agentify tab ID is the current
browser handle; a Computer Use window/tab ID belongs to a different interface. Never equate
these IDs or infer that two same-URL pages in different browser profiles are the same tab.
One active writer owns the binding across all such handles. Agentify's per-tab serialization
does not replace this shared conversation claim. Use only a dedicated non-protected Send tab.

## Strict query and continuation

For a new authorized request, call `agentify_review_query` with `stableKey`, provider,
productModel, reasoningEffort, conversationUrl, conversationId, idempotencyKey, exact prompt,
responsePath and the known existingTabId; bound calls to 60000 ms. `promptPath` is an alternative
to `prompt`, never an additional input; `promptSha256` checks the exact bytes.

The strict tool prepares or retains the composer, checks the target model/effort, records the
attempt before its one Send, pairs the user turn and continues observation. A failure before
Send may therefore leave the full draft in place. The strict tool's internal checks are not
instructions for the operator to repeat them externally.

- Exact operation explicitly false, no other possible acceptance: after repairing the failed
  prerequisite, repeat the same arguments with `verifyExisting=true`. Only a repaired tab
  handle may change via `existingTabId`; keep the stable key and immutable operation inputs.
- Exact operation true: that same continuation observes/archives only, even if the first call
  timed out before a user message ID was returned. Never reset true to false.
- Missing history, contradictory evidence or a prior Send outside strict transport: use
  non-sending tools to reconcile. `verifyExisting` does not import a CUA Send, and false plus
  independent acceptance evidence is not permission to query again.

`agentify_review_preflight({tabId,productModel,reasoningEffort,timeoutMs:60000})` is an optional
non-sending diagnostic. It may open/close menus and set effort, so it is not read-only. Use it
when investigating a specific model-control problem; do not add it to the normal Send path.

`agentify_wait_response({tabId,timeoutMs:60000})` never sends. Use it, `operator_observe` or
`read_page` for non-sending reconciliation, retaining the expected request identity.
`IN_PROGRESS` continues the same wait; `COMPLETE` supplies an observation to pair/archive.
Pass the explicit known tabId to read tools; some key-only tools may create a missing tab.

## Scoped UI repair

Use `operator_observe -> operator_act -> returned after`. Act only on a currently observed
target using its tabId, URL, revision and targetId. Inspect relevant controls and composer
metadata, not a full inventory of unrelated chats. An action's returned `after` is already
the next observation. A stale-revision refusal calls for re-observation, not a blind retry.
`agentify_operator_wait` can wait for a specific loading/UI transition.

Repair a menu problem on the same tab with normal observed controls. A menu-open timeout
does not by itself imply a broken connection, wrong model, or missing authorization.
If ordinary UI interaction cannot resolve it, give the parent the concrete failing operation
and actual state. Do not turn each menu failure into runtime restart or source investigation.
A deployed-code discrepancy is different: a source patch alone does not prove the running
controller loaded it; verify the repaired behavior after the actual runtime change.

For visual ambiguity, use Computer Use on the identified real window/tab. Respect its returned
capabilities and policy stops. If it cannot identify the Windows browser URL, report that
specific inspection failure; do not invent a screenshot or relabel it as an Agentify failure.
Do not use another interface to bypass the refused action.

## Completion and exceptional binding

Strict completion already checks paired assistant identity/hash across samples at least three
seconds apart and absence of active Stop/Continue/Retry controls. An exact archive receipt has
path, sha256, sizeBytes and `projection=exact`. Preserve it verbatim; add no second stability
loop. GitHub's full answer is a separate artifact, paired to the fixed TASK through its scoped
path, immutable delivery commit and delivery comment; `verify_github_pairing` checks that route.
The chat receipt can be complete while GitHub delivery is absent, or GitHub delivery can be
complete while strict UI pairing failed. Preserve both facts and all conflicting artifacts.

A first binding uses provider root URL, `conversationId="__new__"`, `firstBinding=true` and a
dedicated clean tab. Retain these original arguments on continuation; store only the actually
observed post-Send conversation identity as the resulting binding.
Conversation replacement requires [state-schema.md](state-schema.md#explicit-provider-conversation-replacement).
After an admitted replacement, use the helper's deterministic `hmasd-gen:` key (SHA-256 of
JSON-encoded [node key, replacement request ID]); preserve the previous generation and receipts.
An ordinary retry, timeout, new DM or next round does not change that key.
