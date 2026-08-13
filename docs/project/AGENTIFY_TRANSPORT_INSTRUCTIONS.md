# HMASD Agentify transport instructions

```text
document_kind=canonical_transport_operations_manual
scope=ChatGPT_External_Pro|External_Gemini
transport_core=Agentify_strict_review_query
provider_mapping=chatgpt|gemini
version_basis=@agentify/desktop_0.2.4+e12caf8_2026-08-13
```

This is the canonical operating manual for every HMASD Agentify transport
leaf. The transport is one provider-neutral exact-one mechanism with two small
provider adapters. Gemini is not a second workflow. It differs from ChatGPT in
provider root, conversation-identity path, visible model/mode evidence, and DOM
message/send selectors only.

Labels in this document have precise meanings:

- **Verified** means directly established from the local Agentify source named
  in the evidence appendix.
- **HMASD rule** is the fail-closed operating contract chosen for this project.
- **Historical source defect** names a pre-fix violation retained below with
  its implemented repair and regression invariant. Operators never patch or
  simulate evidence during a provider assignment.

## 1. Root-cause summary

Most recent failures were operator/contract failures, not provider failures:

1. A tab was created under one key and strict review tried to adopt it under a
   different `stableKey`, producing `tab_key_mismatch`.
2. The live provider page had navigated to a conversation while Agentify's tab
   registry still held the provider root, producing `tab_url_mismatch` or
   `key_url_mismatch`.
3. Gemini was routed through ordinary `agentify_query` with one composite model
   label even though its UI exposes model and thinking mode as separate selected
   options, producing `expected_model_unavailable`.
4. An ordinary-query failure was followed by another send mechanism instead of
   one strict idempotent operation and observation-only recovery.
5. A click, composer mutation, or send-action counter was treated as a provider
   turn. None is commitment by itself.
6. Registry/status text, account-plan text, helper-injected DOM, or an old
   archive was treated as live selected-model or send evidence.

The confirmed Agentify defects are repaired in source commit `a9471f7`; source
commit `e12caf8` adds the provenance-preserving v1-to-v2 ledger migration needed
to load older valid COMPLETE receipts without weakening new-operation
enforcement. Section 15 retains the defects as regression contracts. An older
running desktop still has the pre-fix behavior, so the repaired tree must be
loaded before relying on those guarantees.

## 2. The operating model

Think in five layers. Never collapse them.

| Layer | What it owns | What it does not prove |
|---|---|---|
| Requester files | Frozen prompt, context, provider, desired conversation relationship, result path | Browser or send state |
| MCP/API | Selects a tab, invokes ordinary or strict transport, reports scoped status | Selected model unless returned from strict live evidence |
| Tab registry | `tabId`, `key`, `name`, provider, last recorded URL | Current live URL after provider-side navigation |
| Live provider DOM | Composer, visible selected model/mode, turns, controls, active generation, current URL | Durable exact-one history |
| Strict-operation ledger | Binding and operation fingerprint, prompt SHA, send-action count, provider user-message ID, completion receipt | A response when status is not `COMPLETE` |

**Verified:** `agentify_tabs` returns the in-memory registry. Scoped
`agentify_status` obtains the top-level URL and challenge state from the live
controller but includes `tabs.listTabs()` as a separate registry snapshot. The
two URLs can differ (`http-api.mjs:740-759`, `main.mjs:639-652`).

**Verified:** strict state is atomically stored in
`%USERPROFILE%/.agentify-desktop/review-transport.json`; bindings are keyed by
`stableKey` and operations by `idempotencyKey` (`state.mjs:34-40,257-272`).

**Verified compatibility boundary:** schema-v1 COMPLETE operations that predate
the durable `sendActionCount` field are migrated to schema v2 only when every
other completion invariant proves an exact natural completion. The migration
records each inferred field and operation in `migrationHistory`. Invalid legacy
rows are not migrated, and schema-v2/new COMPLETE rows still require an
explicit `sendActionCount===1`.

### Default and disposable tabs

The default tab is a protected ChatGPT tab created with key/name `default`; the
API refuses to close it (`main.mjs:254-266`, `http-api.mjs:826-832`). It is for
legacy callers, not production review transport.

Every provider conversation uses a disposable non-default tab. Remote
conversation memory lives at the provider URL, not in the local tab. Archive
the concrete URL, close the tab after terminal archival and inactive
generation, and reopen that URL in a new disposable tab for continuation.

## 3. Provider adapter table

| Field | ChatGPT External Pro | External Gemini |
|---|---|---|
| `provider` | `chatgpt` | `gemini` |
| New root URL | `https://chatgpt.com/` | `https://gemini.google.com/app` |
| First-binding ID | `__new__` | `__new__` |
| Concrete URL | `https://chatgpt.com/c/<id>` | `https://gemini.google.com/app/<id>` |
| Concrete ID | segment after `/c/` | segment after `/app/` |
| Expected model string | the frozen visible Pro label, normally `Pro` | `Gemini 3.1 Pro extended` |
| Required visible evidence | selected composer model is Pro | visible selected `3.1 Pro` and visible enabled `Extended thinking` |

**Verified:** strict input accepts only `chatgpt` or `gemini`, validates the two
roots for first binding, and extracts exact IDs from `/c/` or `/app/`
(`review-transport.mjs:109-157`). Query strings and fragments are invalid.

**HMASD rule:** account/subscription text such as ChatGPT Pro, Google AI Pro, or
Gemini plan marketing is never selected-model evidence. Availability in a menu
is not selection. Gemini requires selected-state evidence for both the model
and thinking mode. Synthetic, hidden, or helper-injected DOM is forbidden.

## 4. Stable keys, tab keys, names, and operation keys

One remote conversation has one immutable `stableKey`. Every local tab used for
that conversation is created with:

```text
tab.key == tab.name == strict.stableKey
```

Each submitted question/turn has a new immutable `idempotencyKey`. A continuation
keeps the conversation `stableKey` but changes the `idempotencyKey`. Never reuse
a `stableKey` for a new conversation, and never reuse an `idempotencyKey` for a
different prompt, model, URL, timeout, provider, or first-binding flag.

**Verified:** an existing keyed tab may be adopted only if its key is the same,
`default`, or empty; otherwise Agentify raises `tab_key_mismatch`. Adoption also
requires the registry URL to equal the requested URL exactly
(`tab-manager.mjs:130-150`). Strict review later calls `ensureTab` with
`exactUrl=true` (`review-transport.mjs:376-385`).

### Create versus adopt

- Create a tab with the final `stableKey` from the start.
- Pass `existingTabId` only for that exact already-inspected tab.
- For a continuation, call `agentify_navigate(tabId=<id>, url=<saved exact
  URL>)` before strict review. This updates both the live page and registry
  (`http-api.mjs:854-865`).
- Do not create a temporary keyed tab and ask strict review to rename it.
- Do not use the default tab as the disposable transport tab.
- If the requested key already exists unexpectedly, inspect that tab and the
  ledger. Reuse it only when it is the current call's known inactive tab. Never
  close an active or possibly unarchived operation merely to free a key.

## 5. Ordinary query versus strict review

`agentify_query` is a convenience path. It has no persistent idempotency key or
strict binding. Its generic send routine may try a button click, form submit,
and several Enter variants before declaring `send_not_triggered`
(`chatgpt-controller.mjs:861-1086`). Its completion check is generic DOM
stability (`chatgpt-controller.mjs:1919-2013`).

`agentify_review_query` is the production path. It records durable send intent,
binds a stable key to provider/model/conversation, permits one strict send
action, records the provider user-message identity, and requires two identical
assistant snapshots at least three seconds apart with no active response
controls (`review-transport.mjs:308-368,395-468,527-578`). It supports first
binding for both providers.

**HMASD rule:** every frozen ChatGPT Pro or Gemini consultation uses strict
review, including a new conversation. Do not fall back from strict review to
ordinary query. Ordinary query is outside this production transport contract.

## 6. Inputs and exact prompt

The assignment is:

```text
AGENTIFY_REVIEW_BATCH_ASSIGNMENT
batch_path=<absolute UTF-8 JSON>
results_path=<exact assignment-scoped output path>
```

Read the exact batch once, then its exact context and ordered question files.
The context is local understanding input and is never sent. Each strict call
uses exactly one of `prompt` or `promptPath`; HMASD always uses
`promptPath=<exact question file>`. Compute the lowercase SHA-256 over the file's
exact UTF-8 bytes and pass it as `promptSha256`.

**Verified:** the MCP layer reads the UTF-8 file once and the strict core rejects
anything but exact-one prompt source or a mismatched lowercase SHA
(`mcp-server.mjs:135-190`, `review-transport.mjs:37-63`).

Never send shell output, a tool result, a JSON wrapper, local paths, local
context, hashes, receipts, or logs as prompt content. Recent HMASD history
contains a prompt polluted with a shell-result wrapper; `promptPath` exists to
remove that operator error.

## 7. Provider-neutral lifecycle

The transport child executes this state progression once per question:

```text
LOCAL_VALIDATED
  -> CAPACITY_ADMITTED
  -> DISPOSABLE_TAB_BOUND
  -> LIVE_PREFLIGHT_CONFIRMED
  -> STRICT_SEND_INTENT_RECORDED
  -> PREPARED
  -> SEND_ACTION_ONCE
  -> PROVIDER_TURN_COMMITTED
  -> NATURAL_GENERATION_OBSERVED
  -> NATURAL_COMPLETION_VERIFIED
  -> ARCHIVED
  -> TAB_CLOSED
```

Any conflict leaves this main line for observe-only reconciliation or a terminal
error. No recovery path loops back to `SEND_ACTION_ONCE` inside the same call.

### 7.1 Local validation

1. Validate requester partition, exact result path, context ownership, question
   order, provider, conversation relationship, model, stable key, and operation
   key.
2. Reject provider-visible absolute/local paths and non-scientific transport
   metadata.
3. Compute question SHA locally. Do not obtain prompt bytes through shell output.
4. For a continuation, require the exact authoritative saved URL and ID. Never
   guess from a title or conversation list.

### 7.2 Capacity admission

The owning L1, not Root, owns shared transport scheduling. Immediately before
dispatch it reads scoped/global Agentify status and admits work only inside its
authorized `max_inflight` allowance. It retains that admission until archive and
tab close.

**Verified defense in depth:** Agentify now uses one global inflight counter for
ordinary `/query`, `/send`, and every fresh strict `/review-query` that can cross
the Send boundary. At capacity, a fresh strict request fails before ledger
creation with stable `rate_limited` data:
`reason=max_inflight`, `operationKind=strict-review`, and
`sendActionCount=0`. Admission first reads the strict ledger fingerprint. An
exact existing operation, `verifyExisting`, or diagnostic observer does not
reserve another send slot and therefore cannot deadlock behind its own original
operation. A conflicting fingerprint still fails idempotency validation.

This governor is only a last mechanical safety barrier. L1 still owns provider
lease ordering and retains its admission until archive and tab close; Root does
not become the scheduler, and observer bypass is not permission to create a new
turn (`http-api.mjs:477-512,881-950`; `review-transport.mjs:
inspectReviewAdmission`).

### 7.3 Tab and URL binding

1. List tabs. Identify and preserve `defaultTabId`.
2. Create one non-default tab with provider hint, exact `stableKey`, and the same
   name.
3. For new binding, keep the exact provider root.
4. For continuation, navigate the tab by `tabId` to the saved concrete URL.
5. Read scoped status. Require top-level live URL and the selected registry row
   URL to be identical to the intended URL. If they differ, navigate once
   through Agentify to the intended URL and re-read status. Do not send while
   they differ.

### 7.4 Live preflight

Require all of the following immediately before the strict call:

- correct non-default `tabId`, key, name, vendor, and exact URL;
- `activeQuery=null` for that tab and no active generation;
- composer visible and usable;
- zero turns for first binding, or the expected prior conversation for a
  continuation;
- visible selected model/mode evidence from the provider UI;
- no Stop, Continue, Retry, Response Retry, Answer now, or equivalent active
  response control;
- no login, CAPTCHA, actual access-denied shell, or unresolved status/DOM
  conflict.

Do not use page/account text as model evidence. Production remains on strict
review; ordinary query is not a fallback. The shared provider adapter now maps
Gemini's composite expectation to two independent actions: exact model selection
and Extended-thinking selection. Strict review invokes that same adapter before
baseline capture. Its canonical receipt is accepted only after two distinct,
visible, selected, composer/menu-scoped controls were observed; generic `Pro`,
hidden menu remnants, unscoped role-menu nodes, and plan text fail closed. That
run-local preflight receipt remains the model identity evidence while the menu
closes for composer typing and Send.

### 7.5 Strict invocation

New conversation:

```text
provider=<adapter provider>
model=<adapter expected model>
conversationUrl=<exact provider root>
conversationId=__new__
firstBinding=true
stableKey=<conversation key>
idempotencyKey=<new immutable operation key>
existingTabId=<inspected tab>
promptPath=<exact question>
promptSha256=<lowercase SHA-256>
timeoutMs=2700000
```

Continuation:

```text
provider=<same provider>
model=<same binding model string>
conversationUrl=<saved exact concrete URL>
conversationId=<ID parsed from that URL>
firstBinding=false
stableKey=<same conversation key>
idempotencyKey=<new immutable turn key>
existingTabId=<inspected tab>
promptPath=<exact question>
promptSha256=<lowercase SHA-256>
timeoutMs=2700000
```

The immutable fingerprint comprises stable key, provider, model, URL, ID,
idempotency key, prompt SHA, timeout, and first-binding flag
(`review-transport.mjs:187-200`). Never change one field to evade an error.

### 7.6 Send boundary and commitment

These are not provider commitment:

- prompt text visible in the composer;
- `PREPARED`;
- a Send click;
- `sendActionCount=1`;
- the composer becoming empty;
- an MCP timeout or client disconnect.

Provider commitment requires exactly one new visible user turn bound to the
intended conversation identity, with readable rendered text exactly equal to
the frozen prompt. ChatGPT additionally requires a concrete `/c/<id>` for first
binding; Gemini requires a concrete `/app/<id>`. The strict core records
`sendCount=1` only after it validates the exact turn content and identity. A
post-click unreadable/mismatched turn is `SUBMITTED_UNVERIFIED`, never a resend
license (`review-transport.mjs:onSubmitted`; `chatgpt-controller.mjs:
#waitForReviewUserMessage,reviewQuery`).

For Gemini, stable reconciliation of all four facts—zero provider turns, no
`/app/<id>`, the complete question still in the composer, and no generation—is
the explicit terminal `SEND_NOT_COMMITTED`, with `prompt_sent=false` and
`response_received=false`. Do not retry inside the transport call.

If a turn, concrete identity, `sendCount=1`, or ambiguous commitment exists,
never send again. A `sendActionCount=1` without a readable provider turn is
ambiguous even if the operator believes the click did nothing.

### 7.7 Natural completion

Observe only. Never activate Stop, Continue, Retry, Response Retry, Answer now,
regenerate, or acceleration controls. `IN_PROGRESS` means keep observing the
same operation; it never means submit again.

Strict completion requires:

- exact provider URL/ID and user-message anchor;
- one assistant message for that turn;
- nonempty full response;
- two identical assistant ID/text-hash snapshots separated by at least three
  seconds;
- no active forbidden controls;
- visible model evidence;
- ledger `status=COMPLETE`, `sendCount=1`, and
  `terminalState=NATURAL_COMPLETION_VERIFIED`.

### 7.8 Archive and close

Write one canonical top-level JSON object:

```json
{
  "schema_version": 1,
  "provider": "chatgpt|gemini",
  "status": "COMPLETE|ERROR",
  "rows": [
    {
      "question_path": "...",
      "question_sha256": "...",
      "status": "COMPLETE|ERROR|SEND_NOT_COMMITTED|SUBMITTED_UNVERIFIED",
      "response": "",
      "conversation_url": "",
      "conversation_id": "",
      "model_evidence": "",
      "promptSha256": "",
      "receipt": null,
      "prompt_sent": false,
      "response_received": false,
      "error": ""
    }
  ],
  "tab_cleanup": {
    "tab_id": "...",
    "generation_inactive": true,
    "closed": true,
    "error": ""
  }
}
```

Rows remain in `question_paths` order. A complete strict row copies the complete
receipt and requires `question_sha256 == promptSha256 ==
receipt.promptSha256`. `response` comes only from `receipt.responseText`. An
error row preserves any completed earlier rows.

After durable archive and confirmed inactive generation, close only the
disposable tab. Report close failure. Run the result-path guard using the
project interpreter:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  C:/Projects/HMASD/.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py `
  --repo C:/Projects/HMASD `
  --expected-results-path <assigned-results-path> `
  --returned-results-path <assigned-results-path>
```

## 8. Exact-one recovery rules

### Same fingerprint, existing operation

- `COMPLETE`: return the stored complete receipt; do not send.
- Provider user-message ID present but no complete response: call
  `agentify_review_query(verifyExisting=true, ...)` with the exact original
  fingerprint. This branch receives only the observer capability and uses a
  fresh bounded observation window (`review-transport.mjs:501-510`).
- No provider user-message ID: `verifyExisting` is unavailable. Inspect the
  ledger and stable live page without page action. Do not send in the same call.
- Conflicting fingerprint for the same idempotency key:
  `review_idempotency_conflict`; correct the caller's metadata, never the
  existing operation.

`verifyExisting=true` is observation, not retry. It must retain the same stable
key, provider, model, URL, conversation ID, idempotency key, prompt SHA,
timeout, and first-binding flag. Do not include a new `existingTabId` unless it
is the exact correctly keyed and URL-reconciled tab; the fingerprint itself
does not include `existingTabId`, but page identity still must match.

### Zero-turn recovery

After explicit `SEND_NOT_COMMITTED`, the owning L1 may authorize exactly one
fresh-tab attempt of the identical request only when its direction-stage
envelope already grants that recovery. It uses a new disposable tab and a new
idempotency key, while preserving question bytes, provider, model, intended
conversation relationship, and stable key. A second noncommit, any provider
turn/identity, or any ambiguity returns to the L1/Root boundary defined by the
direction envelope.

### Timeouts and client failures

A tool timeout is not a send fact. First inspect the strict ledger:

- `sendCount=1` or `userMessageId` present: verify existing only.
- `sendActionCount=1` without user identity: ambiguous; never resend.
- `sendActionCount=0`, no user identity, and pre-click/no-click proof: archive
  pre-send failure. Do not improvise another send route.

The MCP HTTP client itself uses a no-timeout Node HTTP request; provider
observation has the explicit strict deadline (`mcp-lib.mjs:71-112`). A caller
or tool transport can still disconnect, so the ledger remains authoritative.

## 9. Archive integrity and ledger-only restoration

The authoritative order for transport facts is:

```text
valid strict ledger operation > live DOM observation > Agentify registry/status
> HMASD result archive > commentary or memory
```

This order applies only to mechanical facts. It grants no scientific or
technical acceptance authority.

If an HMASD archive is missing or stale:

1. Perform no page action.
2. Read the exact operation under its original `idempotencyKey` from the local
   strict ledger.
3. Recompute the question SHA and request fingerprint inputs from the frozen
   assignment.
4. If and only if the ledger operation is `COMPLETE` and passes the state
   invariants in `state.mjs:117-151`, create the assignment's unused exact
   results path from `responseText` and the receipt fields.
5. If the ledger shows `SUBMITTED` or `BLOCKED`, restore only send-boundary
   facts; do not invent a response or completion.
6. Never overwrite an existing archive. Preserve it and have the owning L1
   dispatch a ledger-only recovery with a new assignment-specific results path.
7. Run the result-path guard. Record that no page, input, send, or response
   control was used.

## 10. Troubleshooting matrix

| Symptom | What it actually means | Required action |
|---|---|---|
| `tab_key_mismatch` | Existing tab has a different non-default key | No send occurred. Close only if safely inactive; create a new tab with `key=name=stableKey`. Never fall back to ordinary query. |
| `tab_url_mismatch` | Explicit adopted tab's registry URL differs from request | Compare live top-level status URL and registry row. Navigate by `tabId` to the exact intended URL, then re-read both. |
| `key_url_mismatch` | The keyed registry tab is not at the strict binding URL | Same reconciliation; do not change the strict URL to a stale registry value. |
| Registry/live URL mismatch | Registry is stale relative to DOM | One Agentify `navigate` to the intended exact URL while idle; verify equality before strict call. |
| `review_model_mismatch` | Strict live evidence does not match frozen model | Inspect genuine selected composer/model controls; fix preflight only. Never change the frozen model or use plan text. |
| `expected_model_unavailable` | Ordinary generic selector could not find one matching option | This is not proof the Gemini model is unavailable. Production used the wrong route or unsupported composite selector. Use strict + genuine visible preflight; otherwise fail closed. |
| `send_not_triggered` | Ordinary query did not establish its generic send signal | Reconcile turns, identity, composer, generation, and ledger. If zero-turn facts all hold, archive noncommit; otherwise ambiguous. Never call another send route. |
| `blocked=true`, login/CAPTCHA | Agentify detected a human/access gate | Do not send. Wait only within assignment timeout; archive pre-send terminal if unresolved. |
| `looks403=true` with usable conversation/composer | Possible false positive from bare `403` text | Treat as evidence conflict, not permission to send. Archive conflict; source fix required. |
| Actual access-denied/403 shell | Provider page is blocked | Pre-send terminal if no operation; verify existing only if ledger says already submitted. Restarting Agentify is not a repair. |
| `review_idempotency_conflict` | Same operation key, different fingerprint | Restore original exact fields or choose a genuinely new authorized operation. Never mutate existing identity. |
| `review_observation_unavailable` | No persisted provider user-message anchor | No `verifyExisting` possible. Inspect ledger/live page without input and fail closed. |
| `SUBMITTED_UNVERIFIED` | Send action or provider turn may exist but completion is absent | Never resend. Use exact `verifyExisting` only when user-message ID exists. |
| `IN_PROGRESS` | Same answer is still active | Continue observation only. Do not query again or close the tab. |
| Timeout | Deadline/client ended; send state unknown from timeout alone | Ledger first, then exact observe-only recovery. |
| Stale results archive | Local result disagrees with valid ledger | Preserve it; perform ledger-only recovery. Do not revisit provider to make the archive agree. |

## 11. Clean examples

The following are call shapes, not permission to send.

### New ChatGPT Pro conversation

```text
stableKey=VQFP-B1-PRO
idempotencyKey=VQFP-B1-PRO-MATH-CLOSURE-01
tab_create(model=chatgpt,key=VQFP-B1-PRO,name=VQFP-B1-PRO)
status(tabId) -> live URL and registry URL both https://chatgpt.com/
visible preflight -> selected Pro, zero turns, idle
review_query(
  provider=chatgpt, model=Pro,
  conversationUrl=https://chatgpt.com/, conversationId=__new__,
  firstBinding=true, existingTabId=<tab>,
  stableKey=VQFP-B1-PRO,
  idempotencyKey=VQFP-B1-PRO-MATH-CLOSURE-01,
  promptPath=<question>, promptSha256=<sha>, timeoutMs=2700000)
terminal -> archive concrete https://chatgpt.com/c/<id>, then close tab
```

### Saved ChatGPT continuation

```text
stableKey=VQFP-B1-PRO
idempotencyKey=VQFP-B1-PRO-MATH-CLOSURE-02
tab_create(model=chatgpt,key=VQFP-B1-PRO,name=VQFP-B1-PRO)
navigate(tabId=<tab>,url=https://chatgpt.com/c/<saved-id>)
status(tabId) -> live URL == registry URL == saved URL; selected Pro; idle
review_query(provider=chatgpt,model=Pro,
  conversationUrl=<saved URL>,conversationId=<saved-id>,firstBinding=false,
  stableKey=<same>,idempotencyKey=<new>,existingTabId=<tab>,
  promptPath=<question>,promptSha256=<sha>,timeoutMs=2700000)
```

### New Gemini conversation

```text
stableKey=VQFP-B1-GEMINI
idempotencyKey=VQFP-B1-GEMINI-INNOVATION-01
tab_create(model=gemini,key=VQFP-B1-GEMINI,name=VQFP-B1-GEMINI)
status(tabId) -> live URL and registry URL both https://gemini.google.com/app
genuine visible preflight -> 3.1 Pro selected + Extended thinking selected,
                           zero turns, idle
review_query(
  provider=gemini, model="Gemini 3.1 Pro extended",
  conversationUrl=https://gemini.google.com/app, conversationId=__new__,
  firstBinding=true, existingTabId=<tab>,
  stableKey=VQFP-B1-GEMINI,
  idempotencyKey=VQFP-B1-GEMINI-INNOVATION-01,
  promptPath=<question>,promptSha256=<sha>,timeoutMs=2700000)
commit -> visible user turn + https://gemini.google.com/app/<id>
```

### Saved Gemini continuation

```text
stableKey=VQFP-B1-GEMINI
idempotencyKey=VQFP-B1-GEMINI-INNOVATION-02
tab_create(model=gemini,key=VQFP-B1-GEMINI,name=VQFP-B1-GEMINI)
navigate(tabId=<tab>,url=https://gemini.google.com/app/<saved-id>)
status(tabId) -> live URL == registry URL == saved URL
genuine visible preflight -> 3.1 Pro selected + Extended thinking selected; idle
review_query(provider=gemini,model="Gemini 3.1 Pro extended",
  conversationUrl=<saved URL>,conversationId=<saved-id>,firstBinding=false,
  stableKey=<same>,idempotencyKey=<new>,existingTabId=<tab>,
  promptPath=<question>,promptSha256=<sha>,timeoutMs=2700000)
```

## 12. Preflight checklist

Before every strict call, record yes/no for each item:

- [ ] Exact batch, context, question order, and result path validated.
- [ ] Exact question SHA computed from UTF-8 file bytes.
- [ ] Provider payload contains no local path, wrapper, receipt, or hidden context.
- [ ] Owning L1 admitted shared `max_inflight` capacity.
- [ ] Default tab identified and excluded.
- [ ] Disposable tab key and name equal immutable `stableKey`.
- [ ] Provider/vendor matches the request.
- [ ] Live URL equals registry URL equals provider root or saved exact URL.
- [ ] New binding has zero turns; continuation has the expected conversation.
- [ ] Genuine visible selected model/mode evidence is present.
- [ ] Account-plan text and synthetic DOM were not used as evidence.
- [ ] Composer is usable and contains no old prompt.
- [ ] No active query/generation or forbidden response control exists.
- [ ] Stable key, new operation key, exact URL/ID, model, SHA, timeout, and
      first-binding flag are frozen.
- [ ] No previous turn/identity/operation makes this a possible resend.

## 13. Terminal checklist

- [ ] Commitment classified from visible turn + concrete identity, not click.
- [ ] No second send route was used.
- [ ] Any recovery was exact-fingerprint observation only.
- [ ] Completion has two stable snapshots and no forbidden controls.
- [ ] Row SHA equals strict receipt SHA.
- [ ] Full response copied from structured strict receipt only.
- [ ] Error row reports `prompt_sent` and `response_received` explicitly.
- [ ] Result written once in canonical schema and original order.
- [ ] Generation confirmed inactive before close.
- [ ] Only disposable tab closed; close outcome archived.
- [ ] Result-path guard passed.
- [ ] One conclusion-first native result returned to the invoker.

## 14. Recent anti-patterns and replacements

The sample below reads only transport metadata, not scientific response content.

| Evidence | Anti-pattern | Correct replacement |
|---|---|---|
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/vqfp_b1_gemini_3_1_pro_extended_innovator_20260812_04/results.json:6-17` | Strict first binding used a mismatched tab key, then ordinary query fallback produced a model error | Create the tab with the final stable key; reconcile URL; use one strict first-binding operation only |
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/crto_b1_gemini_innovator_v3/results.json:2-15` | Ordinary composite-model/send path ended `send_not_triggered` | Genuine two-part Gemini preflight followed by strict first binding; zero-turn means archive noncommit, not another send |
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/crto_b1_gemini_innovator_v4/results.json:2-23` | Generic `Gemini Pro`/availability text was mixed with required selected model/mode | Require visible selected 3.1 Pro and Extended thinking separately |
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/sgsp_b1_gemini_innovator_20260813_01/results.json:3-20` and recovery `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/sgsp_b1_gemini_innovator_20260813_01_fresh_tab_recovery_01/results.json:5-9` | Helper expected a fixed menu shape/count, then ordinary model selection failed | Adapter recognizes exact options by semantic labels/selected state; absence is pre-send terminal, not a fallback send |
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/vqfp_b1_chatgpt_pro_result_convergence_20260813_01/results.json:3-24` | `looks403` was accepted as sufficient blocked proof without archived page-context discrimination | Treat `looks403` plus usable composer as a conflict; do not send; apply source fix in section 15 |
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/scdmp_b1_chatgpt_pro_result_convergence_20260813_01/results.json:3,8-30` | Clean reference, not an anti-pattern: strict continuation captured Pro, matching SHA, one send/action, and natural completion | Reuse this receipt-bearing pattern |
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/independent_research_explorer/ccic_b1_chatgpt_pro_math_closure_20260813_06/results.json:3,15-33` | Clean reference: same strict core and terminal facts | Reuse this pattern for either provider through the adapter |

Other recurring anti-patterns are keeping idle tabs to preserve memory, changing
an idempotent field to bypass a conflict, treating `IN_PROGRESS` as failure,
closing while generation is active, asking Root to poll routine status, and
rewriting stale archives from memory. Their replacements are saved URLs,
exact-fingerprint observation, same-operation waiting, archive-before-close,
L1-owned scheduling, and ledger-only recovery.

## 15. Resolved Agentify defect packets and regression contract

These packets preserve the original diagnosis and the regression invariant.
They were implemented in the Agentify working tree on 2026-08-13 in
`chatgpt-controller.mjs`, `review-transport.mjs`, `state.mjs`, `tab-manager.mjs`,
`main.mjs`, and `http-api.mjs`, with offline fixture coverage in the corresponding
tests. Transport operators must not patch Agentify during a provider assignment
and must not assume the fixes exist in an older running build.

Current source behavior is:

| Packet | Enforced behavior |
|---|---|
| A | exact composer serialization before the only Send; exact one rendered user turn afterward; unreadable/mismatch is ambiguous |
| B | Gemini evidence is visible, scoped, selected, and derived from two distinct controls; plan/hidden/synthetic evidence is excluded |
| C | the shared adapter independently selects exact `3.1 Pro` and `Extended thinking`, returns canonical `Gemini 3.1 Pro extended`, and is used by strict and ordinary entry points |
| D | scoped status reconciles only a valid same-origin live URL into the selected tab's registry row |
| E | bare `403` is not an access error; structured access wording is not blocking when the genuine composer remains usable |
| F | a fresh strict request fails `review_tab_busy` on a prior active turn; only observer recovery uses a persisted `userMessageId`; completion requires `sendActionCount===1` |
| G | strict and ordinary send-capable entry points share one global inflight governor; exact existing observers do not reserve a second slot |

The “observed source defect” and “reproduction” bullets below describe the
pre-fix implementation retained for audit provenance. The invariant and fix
bullets are the current acceptance contract.

### A. Strict prompt DOM identity is enforced before Send

- **File/symbol:** `chatgpt-controller.mjs`, `reviewQuery`, around lines
  1732-1747; `#typePrompt` and `inspectReviewComposerIdentity`, lines 593-687.
- **Invariant:** strict review must prove the active composer serializes exactly
  to the frozen prompt before its sole Send action.
- **Pre-fix defect:** `reviewQuery` called
  `#typePrompt(prompt, { human: false })`; `verifyExact` defaults false. It then
  clicks Send. The post-send new-user-message path identifies a new turn but
  does not require that turn text to equal the prompt.
- **Minimal fix:** call `#typePrompt(prompt, { human:false, verifyExact:true })`;
  after the new user turn appears, require readable rendered text equal to the
  prompt (or exact UTF-8 SHA) before `onSubmitted`. On unreadable/mismatch,
  persist ambiguous submission and never resend.
- **Reproduction:** submit strict review with a composer implementation whose
  `insertText` normalizes or truncates content; pre-fix code could click without
  composer-exact proof despite README's claim at
  `C:/Projects/agentify-desktop/README.md:171-174`.

### B. Gemini strict model evidence excludes hidden or unscoped nodes

- **File/symbol:** `chatgpt-controller.mjs`, `#reviewSnapshot`, lines
  1326-1340.
- **Invariant:** Gemini model evidence must come from visible selected `3.1 Pro`
  and visible selected `Extended thinking` controls.
- **Pre-fix defect:** `geminiModeItems` was not filtered through the local
  `visible` predicate before selected-state matching. A hidden node with a
  selected class can produce `Gemini 3.1 Pro extended`.
- **Minimal fix:** filter every Gemini evidence item with `visible`, scope it to
  the actual model menu/composer control, and reject synthetic/hidden evidence.
  Keep the two selected-state checks independent.
- **Reproduction:** append `display:none` elements matching
  `data-test-id^="bard-mode-option-"`, class `selected`, and the two target
  labels; the pre-fix snapshot returned exact Gemini evidence.

### C. Gemini composite model selection is adapter-mapped

- **File/symbol:** `chatgpt-controller.mjs`, `#ensureExpectedModel`, lines
  1135-1214; `modelLabelMatches`, lines 39-50.
- **Invariant:** provider `gemini` plus expected
  `Gemini 3.1 Pro extended` must select/verify two UI controls, not look for one
  menu item with the composite label.
- **Pre-fix defect:** the generic selector looked for one option whose
  normalized label matches the complete expected string. Gemini exposes model
  and thinking as separate options, so ordinary query reports
  `expected_model_unavailable` even when the plan/model may be available.
- **Minimal fix:** introduce a provider adapter:
  `ensureExpectedModel({provider:'gemini', model:'3.1 Pro', mode:'Extended thinking'})`.
  Select and visibly verify both options; return one canonical evidence string.
  Reuse this adapter in strict preflight before baseline capture. Do not use
  ordinary query as a workaround.
- **Reproduction:** Gemini menu contains separate visible `3.1 Pro` and
  `Extended thinking` items but no single `Gemini 3.1 Pro extended` item; call
  ordinary query with that composite expected model.

### D. Scoped live status safely reconciles the tab registry

- **File/symbol:** `main.mjs` `getStatus`, lines 639-652;
  `tab-manager.mjs` registry/update/adopt, lines 92-109,130-160.
- **Invariant:** after provider-side navigation, the registry URL used by strict
  adoption/exact URL matching must reflect the live page URL.
- **Pre-fix defect:** status read the live URL but returned the registry
  without calling `tabs.updateTabUrl`. Provider-side redirects therefore leave
  the registry stale and strict adoption can raise `tab_url_mismatch` or
  `key_url_mismatch`.
- **Implemented fix:** scoped status calls
  `tabs.reconcileLiveTabUrl(tabId, liveUrl)` after a successful live read. The
  helper accepts only a valid HTTP(S), same-origin URL for that exact tab;
  cross-provider and malformed observations cannot rewrite the registry.
- **Reproduction:** create a keyed provider-root tab, navigate from the provider
  UI to `/c/<id>` or `/app/<id>` without the `/navigate` API, call status, then
  adopt/ensure the concrete URL. Top-level status URL is concrete while the
  registry row remains root.

### E. Bare `403` text no longer causes blocked-page classification

- **File/symbol:** `chatgpt-controller.mjs`,
  `BLOCKED_PAGE_TEXT_PATTERN`/`detectChallenge`, lines 9-12 and 353-459.
- **Invariant:** ordinary conversation text containing the number 403 must not
  by itself classify an otherwise usable provider conversation as blocked.
- **Pre-fix defect:** the first 5,000 body characters were matched
  against bare `\b403\b`, and `looks403` unconditionally makes `blocked=true`.
- **Minimal fix:** remove bare-number matching or require an access-error phrase
  and blocked-page structure; at minimum do not use `looks403` alone when a
  genuine provider composer is visible and usable. Archive a bounded diagnostic
  reason, not provider content.
- **Reproduction:** place `403` in a normal visible conversation while the
  composer is available; `detectChallenge` reports `looks403=true` and blocked.

The archived VQFP `looks403` event does not retain enough page context to prove
that particular instance was false. The pre-fix source-level false positive was
nonetheless directly reproducible.

### F. A fresh strict operation fails busy on an active prior turn

- **File/symbol:** `chatgpt-controller.mjs`, `reviewQuery`, lines 1724-1731;
  `state.mjs` complete-operation validation, lines 117-151.
- **Invariant:** a new strict operation must never complete from a provider turn
  that existed before its own baseline and send action.
- **Pre-fix defect:** when Stop/Continue/Retry was active at fresh strict
  entry, `reviewQuery` selects the latest existing user message and waits for
  its assistant instead of failing busy. The completion validator requires
  `sendCount=1` but does not require `sendActionCount=1`, so that prior turn can
  be recorded as the new operation's completion.
- **Minimal fix:** for a fresh operation, reject any active response before
  baseline capture with a pre-send `review_tab_busy`/`review_active_generation`
  error. Only the existing-operation observer may attach to a persisted
  `userMessageId`. Require `sendActionCount===1` for every newly completed
  strict operation.
- **Reproduction:** start a provider response outside the new operation, then
  invoke a fresh strict request on that conversation before it finishes. The
  pre-fix branch followed the prior latest user turn without executing
  `onPrepared`, `onSendAction`, or `onSubmitted`.

### G. Strict review shares the global inflight governor

- **File/symbol:** `http-api.mjs`, `assertInflightCapacity`, `/review-query`,
  `/query`, and `/send`; `review-transport.mjs`, `inspectReviewAdmission`.
- **Invariant:** every fresh send-capable operation consumes the same desktop
  inflight capacity. Exact idempotent replay and observer recovery consume no
  new send capacity and cannot be blocked by their own existing operation.
- **Pre-fix defect:** ordinary `/query` and `/send` incremented the governor
  counter, while `/review-query` only appeared in `activeReviewQueries`. Two L1
  owners could therefore exceed the configured last-line tool limit despite
  correct strict receipts.
- **Implemented fix:** strict admission validates and fingerprints the ledger
  request before capacity reservation. Only a genuinely fresh strict operation
  reserves one slot. Exact active joins, exact completed operations,
  `verifyExisting`, and diagnostic observation share the existing operation and
  do not reserve again. Capacity rejection occurs before strict state mutation
  with `rate_limited`, `reason=max_inflight`,
  `operationKind=strict-review`, and `sendActionCount=0`.
- **Regression:** hold an ordinary request with `maxInflightQueries=1`; a fresh
  strict request returns 429 and leaves the strict ledger empty. Conversely,
  hold a fresh strict request; an ordinary query returns 429. After the strict
  receipt exists, `verifyExisting=true` succeeds while an unrelated ordinary
  request occupies the single slot.

## 16. Source evidence index

- Package and supported providers: `C:/Projects/agentify-desktop/package.json:2-5`,
  `vendors.json:2-39`.
- MCP ordinary/strict schemas and forwarding:
  `C:/Projects/agentify-desktop/mcp-server.mjs:32-196`.
- Status, tabs, navigation, strict and ordinary HTTP routes:
  `C:/Projects/agentify-desktop/http-api.mjs:172-245,740-925,928-1039,1139-1173`.
- Key, URL, adoption and close invariants:
  `C:/Projects/agentify-desktop/tab-manager.mjs:56-150,153-210`.
- Strict request identity/fingerprint/state machine:
  `C:/Projects/agentify-desktop/review-transport.mjs:37-200,234-368,395-632`.
- Live challenge, model, Gemini adapter DOM, send, and completion mechanics:
  `C:/Projects/agentify-desktop/chatgpt-controller.mjs:9-83,299-520,593-1086,1106-1768,1919-2063`.
- Ledger schema and atomic persistence:
  `C:/Projects/agentify-desktop/state.mjs:6-15,34-155,257-272`.
- Default tab/status construction:
  `C:/Projects/agentify-desktop/main.mjs:254-266,639-652`.
