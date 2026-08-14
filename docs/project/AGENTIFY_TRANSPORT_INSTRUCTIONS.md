# HMASD Agentify transport instructions

```text
document_kind=canonical_transport_operations_manual
scope=ChatGPT_External_Pro|External_Gemini
transport_core=Agentify_strict_review_query
provider_mapping=chatgpt|gemini
version_basis=@agentify/desktop_0.2.4+b6d9bbf_2026-08-13
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
7. Blink rewrote collapsible ASCII spaces in a `contenteditable` composer to
   NBSP while preserving UTF-16 length. Raw DOM equality therefore rejected an
   intact prompt, and a separate raw rendered-turn hash could reject the same
   reversible representation during content rebind.
8. A persisted failed-attempt draft survived in the composer. The old typing
   primitive relied on click, Select All, and Backspace without observing that
   the composer became empty; when focus/selection did not cover the editable
   root, the next frozen prompt was appended and the serializer exposed an
   approximately doubled DOM/text structure.
9. After one exact click-time Send, the controller observed exactly one new
   visible user-turn ID but threw before persisting it because the rendered
   content serializer was unreadable. The transport catch then overwrote the
   true count of one with an unset ledger field's zero, obscuring commitment
   evidence and collapsing `turn_unreadable` into a generic content mismatch.
10. The rendered-user serializer selected the deepest matching content node and
    rejected the exact `PRE > CODE > text` wrapper used for a Markdown-bearing
    user turn. A nested code-block candidate could therefore shadow its outer
    content node, while an exact raw-text PRE/CODE wrapper failed before any
    code point was compared.
11. Even after PRE/CODE became readable, a real Markdown-rendered turn was 124
    characters while its frozen source was 132. The ten source fence characters
    were removed by Markdown rendering and two structural block newlines were
    added, for a net loss of eight. Rendered HTML is therefore a lossy display,
    not a provider-neutral raw submission payload or source-identity oracle.

The confirmed Agentify defects are repaired in source commit `a9471f7`; source
commit `e12caf8` adds the provenance-preserving v1-to-v2 ledger migration needed
to load older valid COMPLETE receipts without weakening new-operation
enforcement. Current source and active runtime commit `b6d9bbf` includes the
collision-resistant review plain-text identity model, the verified-selection
`agentify_review_composer_replace_v2` contract, atomic click-time verification,
defect-J durable post-click observed-turn evidence, defect-K exact PRE/CODE
rendered-turn extraction, and defect-L causal-submission/display-fidelity
separation, plus defect-M semantic Gemini picker evidence. Section 15 retains
the defects as regression contracts. A running desktop must load `b6d9bbf`
before operators rely on the complete A-M guarantee.

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

### 2.1 Incident observation and reporting hierarchy

An Agentify incident is mechanical evidence, not a declaration that the user,
thread, task goal, or unrelated production work is blocked. Inspect the native
Agentify surface in this order: (1) `agentify_tabs` to identify the exact tab
and URL candidate, then (2) exact-tab `agentify_read_page`/DOM/read-page
evidence. Scoped status and `loginLike` are diagnostic hints only; they cannot
prove logout or access loss. A Computer Use/Chrome safety refusal because it
cannot determine a URL is `UNOBSERVED`, not authentication evidence. A user's
direct observation is evidence to reconcile with the native record, not an
automatic replacement for it.

A transport/operator leaf archives the mechanical terminal according to the
exact-one rules and returns `INCIDENT_REPORTED` with observed facts, observation
method, actions taken, actions not taken, remaining unknown, causal hypotheses,
and the smallest next authority/action. It never returns generic `BLOCKED`,
calls `update_goal`, claims a production pause beyond its assignment, or
requests user action unless the directly observed interface proves it. A
persisted ledger `BLOCKED` value remains an internal mechanical fact and does
not transfer goal or Root authority. Only operational Root may make the
separate thread-level blocked decision after its independently verified audit.

An exact-one terminal, non-resend result, exhausted fresh-tab allowance,
resource limit, or absent response is transport evidence only. It does not
command CM, Root, EM, or the portfolio session to consume, pause, retire, or
declare a scientific direction non-resumable, nor does it impose a binary next
choice. Root translates the return into observed fact, exact object, remaining
unknown, scientific implication, and smallest semantic owner/action. Without
complete question-relevant data, unchanged-science repair/completion belongs to
CM. A finite compute budget can be scientifically causal only when the
same-direction EM establishes that prospectively. Preserve ledger status facts
and exact-one/no-resend invariants; where frozen transport semantics permit,
retain a resumable blinded atomic frontier rather than treating a lease/resource
pause as a scientific termination.

Pending user adjudication, legacy one-attempt/no-retry, CM-recommend-park,
fixed wall-cap, terminal/`ERROR`, archive/commit/push-before-intake, and stale
Pro/Gemini retry schemas are suspended as scientific or portfolio routing
commands. They remain mechanical transport facts and do not pause, retire, or
stop a scientific direction. This does not authorize a resend: after a visible
provider turn or concrete conversation identity, the exact no-resend rule
remains absolute. A transport failure cannot pause the direction. Resource
slices pause their lease only; CM owns semantics-preserving same-coordinate
blinded atomic resume until complete question-relevant data exist.

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
visible, selected, menu-scoped items were observed. On the verified 2026-08-13
Gemini UI, the visible menu item's semantic `.label` child is authoritative:
`3.1 Pro` and either `Extended thinking` or the localized `扩展思考`. The parent
menu item's full text also contains localized descriptions and badges and must
not be compared as the model label. `data-active=true` and class `active` are
keyboard/focus state, not selection. Selection requires class `selected`,
`aria-checked=true`, `aria-selected=true`, or a visible descendant selected
marker. The closed header trigger may abbreviate the same state as `Gemini Pro`
or `Pro 扩展`; it is useful only to open the menu and is not exact two-part
evidence. Generic `Pro`, hidden menu remnants, unscoped role-menu nodes, and
plan text fail closed. That run-local preflight receipt remains the model
identity evidence after the menu closes for composer typing and Send.

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

### 7.6 Composer and rendered-turn text identity

Strict text comparison uses the named model
`agentify_review_plain_text_v1`. It first canonicalizes only line endings:
CRLF and a lone CR become LF. It performs no trimming, paragraph folding,
Unicode normalization, generic whitespace normalization, or hash-only bypass.

Blink may preserve a run's visible ASCII spacing in a `contenteditable` DOM by
rebalancing one or more collapsible U+0020 spaces to U+00A0 NBSP. Agentify may
reverse only that deterministic, length-preserving representation, and only
when every condition below holds:

- the frozen source contains no NBSP and contains at least one non-whitespace
  code point;
- each mismatch is expected U+0020 ASCII space versus observed U+00A0 NBSP;
- each mismatch belongs to an ASCII-space run at line start, at line end, or
  containing at least two consecutive ASCII spaces;
- replacing only those observed NBSP code points with the expected ASCII
  spaces recovers the complete canonical expected text exactly; and
- the SHA-256 of that recovered canonical observed text equals the canonical
  prompt SHA-256.

This exception never equates NFC with NFD, an ordinary interior single ASCII
space with NBSP, a source-native NBSP with ASCII space, a zero-width code point
with its absence, one astral code point with another, or any other differing
code point. Pure-whitespace prompts cannot use the recovery. These distinctions
fail closed even when UTF-16 lengths happen to match.

The pre-send composer and atomic click-time check validate this same safe text
receipt. An accepted receipt requires both recovered-text exactness and
canonical SHA equality; a second raw/canonical equality test must not contradict
it. Separately, `sourceSha256`/`promptSha256` remains the SHA-256 of the exact
frozen UTF-8 source bytes and binds the request fingerprint. The browser text
model is not permission to change those frozen bytes
(`review-text-identity.mjs:REVIEW_PLAIN_TEXT_MODEL,compareReviewPlainText,
reviewPlainTextIdentity`; `chatgpt-controller.mjs:#replacePrompt,
#clickReviewSendOnce`; `review-transport.mjs:onComposerVerified,onSendAction`).

Do not apply that source-text claim to rendered provider HTML. Markdown
rendering is intentionally many-to-one: headings, list markers and indentation,
fence delimiters/info strings, and other source syntax may disappear or become
structural nodes. Agentify therefore keeps three non-interchangeable evidence
layers:

1. **Frozen source and Send-boundary text.** Raw source SHA binds the file;
   canonical prompt SHA plus the atomic composer receipt proves the exact
   browser text at the unique click boundary under the narrow text model.
2. **Accepted provider turn.** The persisted baseline, exactly one new visible
   user-turn ID outside it, and a concrete conversation URL/ID prove the unique
   click caused one accepted turn in that conversation.
3. **Rendered display fidelity.** Structural serialization is recorded as
   `exact`, `lossy_mismatch`, or `unreadable`. It is diagnostic display evidence,
   never raw-source identity and never a reconstruction license.

The provider-neutral core exposes no authoritative raw request-body anchor:
the Chrome CDP backend does not capture Network request bodies, the Electron
backend does not intercept web requests, and the shared DOM snapshot contains
turn IDs plus rendered nodes only. Provider-private network JSON, React state,
edit mode, semantic Markdown equivalence, trimming, contains tests, and
length/hash bypasses are forbidden substitutes.

Rendered user-turn discovery prefers the outermost non-control content candidate;
a nested selector hit cannot replace an ancestor that contains the complete
message. One additional wrapper is readable: an exact `PRE` with exactly one
`CODE` element child. Agentify serializes that CODE subtree by preserving its
text code points and line breaks exactly. It performs no trimming, `innerText`
fallback, Markdown parsing, heading/list reconstruction, fence insertion, or
semantic equivalence. If the PRE/CODE node is merely one rendered fenced-code
fragment, its extracted text is only lossy display evidence. Malformed PRE
structure, controls, multiple CODE children, unsupported nodes, and multiple
distinct outer content candidates remain unreadable or ambiguous. The raw frozen
source SHA, atomic click-time receipt, persisted causal receipt, unique new turn,
and concrete identity remain mandatory independently
(`chatgpt-controller.mjs:serializeReviewComposer,serializeReviewUserMessage,
#reviewSnapshot,#waitForReviewUserMessage,#resolveReviewUserAnchor,
inspectReviewSubmissionIdentity,recoverReviewSubmission`).

Before the one strict insertion, Agentify uses the provider-neutral
`agentify_review_composer_replace_v2` contract:

1. Resolve the visible primary composer and classify it as `contenteditable`,
   `textarea`, or plain-text `input`.
2. If nonempty, focus the composer and construct a selection proven to cover
   its complete editable value/root. Dispatch exactly one real Backspace key so
   the browser and provider editor framework receive the native keyboard,
   `beforeinput`, and `input` transaction. Never directly mutate
   contenteditable children or a form-control value. An already-empty composer
   sends no delete key.
3. Independently serialize and prove empty in two snapshots separated by a
   bounded delay. This detects immediate and queued draft rehydration. A
   nonempty/unreadable snapshot fails before any prompt insertion.
4. Re-resolve the same primary composer, prove it remains empty, and establish
   a verified collapsed caret (contenteditable range or native selection range).
   Focus or selection uncertainty fails before insertion.
5. Insert the frozen prompt in one `insertText` operation, never by appending a
   second recovery copy, then require the section 7.6 identity receipt.
6. Immediately before Send, one synchronous page-evaluation task reserializes
   and revalidates the same exact text model and, only on success, clicks the
   unique Send control. No awaited callback or ledger write separates this
   final identity test from the click. The click-time receipt is required by
   `onSendAction` and the ledger.

An empty snapshot alone is not the final send guarantee: persisted application
state may rehydrate later. The atomic click-time check closes that interval. A
selection, delete, empty, caret, final identity, or Send-control failure reports safe
structural metadata, `noClickProven=true`, `promptInsertCount=0` when insertion
never occurred, and leaves `sendActionCount=0`. It must never be repaired by
typing again in that operation (`review-composer-replacement.mjs`;
`chatgpt-controller.mjs:#clearReviewComposerOnce,#verifyReviewComposerEmpty,
#prepareReviewComposerInsertion,#replacePrompt,#clickReviewSendOnce`;
`review-transport.mjs:onComposerVerified,onSendAction`).

### 7.7 Send boundary and commitment

These are not provider commitment:

- prompt text visible in the composer;
- `PREPARED`;
- a Send click;
- `sendActionCount=1`;
- the composer becoming empty;
- an MCP timeout or client disconnect.

Provider commitment requires the conjunction of:

- a durable `agentify_review_causal_submission_v1` receipt bound to the operation
  ID, raw source SHA, canonical prompt SHA, exact persisted baseline digest,
  `clickCount=1`, and `sendActionCount=1`;
- exactly one new visible user-turn ID outside that baseline; and
- the exact intended conversation identity. ChatGPT additionally requires a
  concrete `/c/<id>` for first binding; Gemini requires a concrete `/app/<id>`.

This proves the exact click-bound composer text causally produced one provider
turn. It does not claim that rendered HTML reproduces source Markdown or that
Agentify captured the provider's private HTTP request bytes. The strict core may
record `sendCount=1` and `userMessageId` with rendered fidelity `exact`,
`lossy_mismatch`, or `unreadable` only when every causal predicate above is
persisted and validated. Without that causal receipt, an unreadable/mismatched
turn remains `SUBMITTED_UNVERIFIED` and permanently non-resendable
(`review-text-identity.mjs:REVIEW_CAUSAL_SUBMISSION_MODEL,
validateReviewCausalSubmissionReceipt`; `review-transport.mjs:onSendAction,
onUserTurnObserved,onSubmitted`; `chatgpt-controller.mjs:
#waitForReviewUserMessage,reviewQuery`).

The first exactly-one new visible user-turn ID is durable commitment evidence
even when its content is unreadable or mismatched. Before any such failure,
Agentify persists `observedUserMessageId`, observation time, exact observed
conversation URL/ID, and a non-content `observedTurnEvidence` receipt. The
terminal classes are distinct:

- `click_no_turn`: the observation window ended without a new visible user turn;
- `turn_unreadable`: exactly one new turn exists, but its structural serializer
  cannot produce text;
- `turn_content_mismatch`: exactly one readable new turn exists, but the narrow
  plain-text identity receipt does not match and no valid causal receipt is
  available;
- `turn_causal_exact_rendered_unreadable`: the exact causal receipt is valid but
  rendered display structure is unreadable; and
- `turn_causal_exact_rendered_mismatch`: the exact causal receipt is valid but
  rendered display is a lossy/non-source representation.

`turn_exact` and the two `turn_causal_exact_rendered_*` classes may promote the
durable anchor only under the complete causal receipt. Every observed-turn class
cuts off resend. An unreadable turn has no trustworthy rendered length, hash, or
mismatch class unless those safe fields were actually returned; never infer them
from composer evidence. A lossy-display operation may continue observing by its
persisted user-turn ID. If that ID disappears after reload, content-based rebind
is unavailable because lossy display cannot collision-resistently identify the
raw source; fail closed instead of reconstructing Markdown.

For Gemini, stable reconciliation of all four facts—zero provider turns, no
`/app/<id>`, the complete question still in the composer, and no generation—is
the explicit terminal `SEND_NOT_COMMITTED`, with `prompt_sent=false` and
`response_received=false`. Do not retry inside the transport call.

If a turn, concrete identity, `sendCount=1`, or ambiguous commitment exists,
never send again. `sendActionCount=1` without one new provider-turn anchor is
ambiguous even if the operator believes the click did nothing.

### 7.8 Natural completion

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

### 7.9 Archive and close

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
- `observedUserMessageId` present but no validated `userMessageId`: a visible
  turn is durably anchored but its content was unreadable or mismatched.
  `verifyExisting` remains unavailable because that turn is not a validated copy
  of the frozen prompt. Preserve `SUBMITTED_UNVERIFIED` and never resend.
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
   facts; do not invent a response or completion. Report the latter only as an
   internal ledger fact under `INCIDENT_REPORTED`, never as a goal conclusion.
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
| `expected_model_unavailable` | The adapter could not find an exact visible semantic option; on `f0f48ef`, it incorrectly compared the parent menu item's model label plus localized description to `3.1 Pro` | This is not proof the account lacks the model. Inspect only the genuine open picker: semantic `.label`, selected state, and separate thinking item. Never use the header abbreviation, full item text, menu count, account text, ordinary query, or another send. A zero-turn/root-URL/empty-composer failure is `SEND_NOT_COMMITTED`; one later fresh-tab recovery needs owner authority and active runtime `b6d9bbf` or later. |
| `send_not_triggered` | Ordinary query did not establish its generic send signal | Reconcile turns, identity, composer, generation, and ledger. If zero-turn facts all hold, archive noncommit; otherwise ambiguous. Never call another send route. |
| Composer serialized length/DOM structure is approximately doubled | A persisted draft was appended because keyboard Select All/Backspace did not replace the editable root | Strict gate correctly prevents Send. Archive the pre-send failure; never type again in that operation. Use a fresh authorized operation only after the repaired verified-selection/delete/empty/caret/click-time contract is loaded. |
| `review_composer_clear_failed` or `review_composer_caret_unavailable` | Full selection, native delete, draft-state synchronization, empty proof, focus, or collapsed insertion caret could not be proven | Pre-insert and pre-send terminal. Do not append, send, or retry inside the operation. |
| `review_user_message_not_observed_after_click` / `click_no_turn` | The unique click occurred, but no new visible turn appeared before the observation deadline | No turn anchor may be fabricated. This is still post-click ambiguity and never permits resend inside the operation. |
| `review_user_message_identity_unreadable` / `turn_unreadable` | Exactly one new visible turn ID exists, but its structural content serializer failed | Require durable `observedUserMessageId` and safe structure diagnostics; never infer content or resend. |
| Rendered turn reports `PRE` / `CODE` structural unreadability | The old serializer rejected a transparent raw-text wrapper or selected a nested code fragment instead of its outer content node | The historical operation is permanently ambiguous. Use no page action and never resend it. `9679872` applies outermost-candidate plus exact PRE/CODE extraction; this improves display diagnostics but does not make rendered Markdown a raw-source oracle. |
| Rendered length differs from the frozen Markdown length | Provider rendering removed or structurally represented source syntax; for the 132/124 canary, ten fence characters disappeared and two block newlines were added | Never reconstruct delimiters, trim, or use semantic equivalence. If the committed runtime has a valid persisted causal receipt plus one new turn/concrete identity, store `lossy_mismatch` as display fidelity and continue by the durable turn ID. Otherwise remain `SUBMITTED_UNVERIFIED`; never resend. |
| `review_user_message_content_mismatch` / `turn_content_mismatch` | Exactly one readable new turn exists, but narrow exact comparison failed and no valid causal receipt can promote it | Preserve observed length/hash/mismatch metadata when available; never trim, broaden normalization, or resend. |
| `review_content_rebind_unavailable_for_lossy_rendering` | The durable user-turn ID disappeared and lossy display cannot collision-resistently identify the source turn | Stop observation and fail closed. Do not use Markdown reconstruction or content similarity to rebind. |
| `review_composer_identity_mismatch_at_send` | Composer changed after initial identity receipt but before the Send boundary | Atomic check performed zero clicks. Archive pre-send; do not reuse the closed operation. |
| `blocked=true`, login/CAPTCHA | A diagnostic/status hint; a human/access gate is established only by exact native tab/page DOM evidence | Reconcile via `agentify_tabs` then exact-tab `agentify_read_page`/DOM. If the gate is directly observed, do not send; archive the pre-send terminal and return `INCIDENT_REPORTED`. A status-only result or URL-observation refusal is `UNOBSERVED`, not logout proof. |
| `looks403=true` with usable conversation/composer | Possible false positive from bare `403` text | Treat as evidence conflict, not permission to send. Archive conflict; source fix required. |
| Actual access-denied/403 shell | Provider page is blocked | Pre-send terminal if no operation; verify existing only if ledger says already submitted. Restarting Agentify is not a repair. |
| `review_idempotency_conflict` | Same operation key, different fingerprint | Restore original exact fields or choose a genuinely new authorized operation. Never mutate existing identity. |
| `review_observation_unavailable` | No persisted provider user-message anchor | No `verifyExisting` possible. Inspect ledger/live page without input and fail closed. |
| `SUBMITTED_UNVERIFIED` | Send action or provider turn may exist but completion is absent | Never resend. Use exact `verifyExisting` only when validated `userMessageId` exists; `observedUserMessageId` alone is commitment evidence, not an observation capability. |
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
- [ ] Composer is usable; strict replacement will verify full selection, send
      at most one native delete, prove empty twice, verify insertion caret,
      insert once, and atomically recheck at Send even if an old draft exists.
- [ ] No active query/generation or forbidden response control exists.
- [ ] Stable key, new operation key, exact URL/ID, model, SHA, timeout, and
      first-binding flag are frozen.
- [ ] No previous turn/identity/operation makes this a possible resend.

## 13. Terminal checklist

- [ ] Commitment classified from visible turn + concrete identity, not click.
- [ ] Any exactly-one visible new turn was durably recorded as
      `observedUserMessageId` before content acceptance or failure.
- [ ] `click_no_turn`, `turn_unreadable`, and `turn_content_mismatch` were not
      collapsed or treated as resend permission.
- [ ] The durable Send receipt includes valid replacement and atomic click-time
      identity evidence.
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
| `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/root/agentify_post_9679872_causal_identity_synthetic_canary/gemini_3_1_pro_extended_new_first_binding/results.json` | `f0f48ef` compared the whole `3.1 Pro` menu-item text, including its localized description, against the exact model label; the strict gate failed safely before Send | Read the one visible semantic `.label`, reject focus-only `active` state, and prove `3.1 Pro` plus separately selected `Extended thinking`/`扩展思考`; retain the historical operation as zero-commit and use only one owner-authorized fresh recovery after the fixed instance is loaded |
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
Packets A-L are implemented through Agentify commit `f0f48ef`, and packet M is
implemented in current source/runtime commit `b6d9bbf`, in
`chatgpt-controller.mjs`, `review-composer-replacement.mjs`,
`review-transport.mjs`, `state.mjs`, `tab-manager.mjs`, `main.mjs`, and
`http-api.mjs`, with offline fixture coverage in the corresponding tests.
Transport operators must not patch Agentify during a provider assignment and
must not assume the fixes exist in an older running build.

Current source behavior is:

| Packet | Enforced behavior |
|---|---|
| A | exact composer serialization before the only Send; source identity is never inferred from rendered HTML |
| B | Gemini evidence is visible, scoped, selected, and derived from two distinct controls; plan/hidden/synthetic evidence is excluded |
| C | the shared adapter independently selects exact `3.1 Pro` and `Extended thinking`, returns canonical `Gemini 3.1 Pro extended`, and is used by strict and ordinary entry points |
| D | scoped status reconciles only a valid same-origin live URL into the selected tab's registry row |
| E | bare `403` is not an access error; structured access wording is not blocking when the genuine composer remains usable |
| F | a fresh strict request fails `review_tab_busy` on a prior active turn; only observer recovery uses a persisted `userMessageId`; completion requires `sendActionCount===1` |
| G | strict and ordinary send-capable entry points share one global inflight governor; exact existing observers do not reserve a second slot |
| H | composer and click-bound text use one collision-resistant plain-text receipt; only narrowly reversible Blink space rebalance is accepted |
| I | strict composer replacement clears once, proves empty and caret state before one insertion, then atomically revalidates identity with the unique Send click; persisted drafts cannot be appended or race the send boundary |
| J | the first exactly-one visible post-click user-turn ID is durably persisted before display inspection; no-turn, unreadable-turn, and readable-mismatch evidence remain distinct and never permit resend |
| K | rendered display serialization chooses outermost non-control content and reads only an exact transparent PRE/CODE wrapper; nested fragments, malformed structure and controls remain fail-closed |
| L | exact click-bound source identity, provider turn acceptance, and lossy rendered display are separate; a persisted causal receipt may bind one turn without pretending rendered Markdown reproduces source bytes |
| M | Gemini picker selection and verification use the unique visible semantic item label, never parent description text or focus-only `active`; exact selected `3.1 Pro` and selected `Extended thinking` remain separate evidence |

The “observed source defect” and “reproduction” bullets below describe the
pre-fix implementation retained for audit provenance. The invariant and fix
bullets are the current acceptance contract.

### A. Strict prompt DOM identity is enforced before Send

- **File/symbol:** `chatgpt-controller.mjs`, `#typePrompt`,
  `inspectReviewComposerIdentity`, and `reviewQuery`, lines 750-900 and
  2065-2139; `review-transport.mjs`, `onComposerVerified`, lines 499-528.
- **Invariant:** strict review must prove the active composer serializes exactly
  to the frozen prompt under the named review text model before its sole Send
  action. Provider acceptance is subsequently bound by the causal receipt and
  unique turn identity; rendered display is not reused as source identity.
- **Pre-fix defect:** `reviewQuery` called
  `#typePrompt(prompt, { human: false })`; `verifyExact` defaults false. It then
  clicks Send. The post-send new-user-message path identifies a new turn but
  does not require that turn text to equal the prompt.
- **Implemented fix:** call
  `#typePrompt(prompt, { human:false, verifyExact:true })`; persist the verified
  composer receipt before Send; after one new user turn appears, require the
  same collision-resistant text identity plus exact conversation identity
  before `onSubmitted`. On unreadable/mismatch, persist ambiguous submission
  and never resend. Section H specifies the only browser representation that
  this exact comparison may reverse.
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

### H. Browser source-text identity is unified across composer and exact-display paths

- **File/symbol:** `review-text-identity.mjs`,
  `REVIEW_PLAIN_TEXT_MODEL`, `canonicalizeReviewPlainText`,
  `compareReviewPlainTextIdentity`, and `safeReviewPlainTextComparison`, lines
  3-183; `chatgpt-controller.mjs`, `inspectReviewComposerIdentity`,
  `#waitForReviewUserMessage`, `#resolveReviewUserAnchor`,
  `inspectReviewSubmissionIdentity`, and `recoverReviewSubmission`, lines
  764-900,1755-1930,2195-2299; `review-transport.mjs`, operation prompt identity,
  `onSubmitted`, and `onComposerVerified`, lines 380-526.
- **Invariant:** every surface claimed to preserve frozen source text is checked
  by `agentify_review_plain_text_v1`; acceptance requires recovered canonical
  text to equal the canonical source exactly and its SHA-256 to match. Rendered
  HTML that does not preserve Markdown source is explicitly display evidence,
  not such a surface. The raw frozen source SHA remains separately bound to the
  request and operation.
- **Observed source defect:** Blink represented leading/repeated ASCII spaces in
  the 7,024-character strict prompt with NBSP. The former raw serializer
  equality failed before Send even though the structural prompt was intact.
  After an initial repair, content rebind first accepted the safe receipt and
  then applied a second line-ending-only hash to raw rendered text, rejecting
  the very same legal Blink representation.
- **Implemented fix:** canonicalize only CRLF/lone CR to LF; reverse only
  expected-ASCII-space/observed-NBSP mismatches at leading, trailing, or
  repeated ASCII-space runs when the source has no NBSP and has non-whitespace
  content. Require exact recovered text and equal canonical SHA. Use the same
  safe receipt for composer verification and exact-display diagnostics/rebind;
  remove contradictory raw equality/hash gates. Defect L later separates lossy
  display from the causal submission receipt rather than broadening this text
  model.
- **Regression:** `tests/chatgpt-controller.test.mjs:118-199` covers line
  endings, narrowly reversible space rebalance, blank lines, code/list shape,
  source NBSP, ordinary single-space NBSP, NFC/NFD, astral and zero-width
  distinctions, a synthetic 7,024-character prompt, and content-rebind receipt
  parity. `tests/review-transport.test.mjs:103-128,528-550` proves the same
  receipt is durable and bound to the raw prompt SHA.

### I. Persisted drafts are replaced and verified before strict Send

- **File/symbol:** `review-composer-replacement.mjs`,
  `locateReviewComposer`, `prepareReviewComposerClearSelection`,
  `inspectReviewComposerEmptyElement`, and `positionReviewComposerCaret`;
  `chatgpt-controller.mjs`, `#clearReviewComposerOnce`,
  `#verifyReviewComposerEmpty`, `#prepareReviewComposerInsertion`,
  `#replacePrompt`, and `#clickReviewSendOnce`; `review-transport.mjs`,
  `onComposerVerified` and `onSendAction`. These symbol locators are the stable
  source references for commit `d94ee4b`; line numbers are intentionally omitted
  because surrounding controller and transport code can move independently.
- **Invariant:** strict review clears the resolved primary composer once,
  dispatches provider-observable input state, proves stable emptiness and a
  collapsed caret before inserting the frozen prompt once, then performs its
  final collision-resistant identity check and unique Send click in one
  synchronous page task. The ledger accepts Send only with both replacement and
  click-time identity receipts.
- **Observed source defect:** `#typePrompt` clicked near the lower composer,
  issued OS-dependent Select All and Backspace, and immediately called
  `insertText(prompt)`. It neither proved which editable root owned the
  selection nor verified empty state. The first repaired canary left the
  7,024-character draft unsent; the next canary serialized 14,048 characters,
  299 elements and 220 text nodes versus the earlier 151 elements and 110 text
  nodes, with zero Send/action/user-turn facts. This is exact mechanical
  evidence of append-after-failed-replacement, not prompt corruption or a
  provider turn.
- **Implemented fix:** the current v2 primitive verifies a selection covering
  the entire contenteditable root or form-control value, dispatches one real
  Backspace, then proves empty twice. Caret verification catches focus and
  insertion-selection failures, insertion occurs once, and the final text check
  plus click is atomic. Every failure before click carries safe non-content
  metadata and `noClickProven=true`; no branch types a second copy. Section J
  records why direct DOM/value mutation from the first repair was retired.
- **Regression:** `tests/review-composer-replacement.test.mjs` covers verified
  full selection for contenteditable/textarea, delayed DOM and textarea
  rehydration, and failed selection. Focused controller fixtures
  cover the 7,024-shape persisted-draft replacement contract, zero insertion on
  rehydration/caret failure, mutation after the initial receipt with zero click,
  and legal click-time NBSP rebalance with exactly one click.
  `tests/review-transport.test.mjs` requires durable replacement and click-time
  receipts before accepting `sendActionCount=1`.

### J. Post-click visible-turn evidence is durable before content validation

- **File/symbol:** `chatgpt-controller.mjs`, `#waitForReviewUserMessage` and
  `reviewQuery`; `review-transport.mjs`, `onUserTurnObserved`, `onSubmitted`,
  and terminal error persistence; `state.mjs`, observed-turn validation;
  `review-composer-replacement.mjs`, `prepareReviewComposerClearSelection`.
  These symbol locators are the stable source references for commit `d94ee4b`;
  line numbers are intentionally omitted.
- **Invariant:** after the atomic unique Send click, the first exactly-one new
  visible user-turn identity is persisted before any rendered-content error.
  `turn_unreadable` and `turn_content_mismatch` retain that anchor and are
  permanently non-resendable. `click_no_turn` records no fabricated anchor.
  In `d94ee4b`/`9679872`, only `turn_exact` became
  `userMessageId`/`sendCount=1`; defect L replaces that rendered-source
  assumption with a persisted causal receipt without weakening non-resend.
- **Observed source defect:** operation
  `SCDMP-B2-R02-MATH-CLOSURE-ce3f4a3c-551d-4b93-8040-149fa7790203`
  had one successful click-time exact receipt, then entered the branch guarded
  by `newUserMessages.length === 1`. Its safe error showed
  `readableCandidateCount=0`, so the rendered turn was structurally unreadable,
  not a proven readable text mismatch. The controller kept its ID only in a
  local variable and threw before `onSubmitted`; the transport catch then
  replaced the error's count of one with absent `op.newUserMessageCount || 0`.
  The resulting ledger/archive therefore incorrectly suggested that no turn
  was observed and lacked the safe serializer structure.
- **Historical classification:** the continuation snapshot had already passed
  exact URL/ID assertion for
  `https://chatgpt.com/c/6a7ce86f-c34c-83e8-94b2-d06c2a833561`.
  Local evidence cannot recover the discarded user-turn ID, rendered length,
  hash, unsupported tag, or actual submitted bytes after the tab was closed.
  It therefore cannot decide whether provider content was old, empty,
  duplicated, attachment-backed, or semantically exact. The historical
  operation remains `SUBMITTED_UNVERIFIED` and must never be resent; its
  archive's `prompt_sent=false` is not authoritative against the source-proven
  exactly-one visible-turn observation.
- **Implemented fix:** `onUserTurnObserved` atomically persists the observed ID,
  timestamp, URL/ID, class, and sanitized non-content evidence before the
  controller can throw. The error catch preserves the actual observed count
  instead of overwriting it. The composer replacement model advances to
  `agentify_review_composer_replace_v2`: it uses a verified full selection and
  one real Backspace before empty proof and single insertion, avoiding direct
  DOM/value mutation that could diverge from provider editor state. Atomic
  click-time identity remains unchanged. Because the historical rendered
  structure was discarded, the user-message serializer is not broadened;
  unsupported or ambiguous normalizations still fail closed with richer safe
  fingerprints.
- **Regression:** focused controller fixtures prove durable callback ordering
  for readable mismatch and unreadable structure, distinct no-turn error, and
  no `onSubmitted` promotion. Transport fixtures prove observed anchors survive
  terminal failure, safe length/hash or structure metadata is retained only
  when available, repeated operation use cannot resend, and no-turn fabricates
  no ID. State fixtures enforce deterministic observed evidence and reject
  incomplete or conflicting anchors. Replacement fixtures cover verified full
  selection for contenteditable and textarea, one-key clearing, asynchronous
  draft rehydration, and selection failure.

### K. PRE/CODE rendered wrappers are structurally readable display evidence

- **File/symbol:** `chatgpt-controller.mjs`, `serializeReviewComposer`,
  `serializeReviewUserMessage`, `#reviewSnapshot`,
  `#waitForReviewUserMessage`, `#resolveReviewUserAnchor`,
  `inspectReviewSubmissionIdentity`, and `recoverReviewSubmission`. Symbol
  locators are normative; line numbers are intentionally omitted.
- **Invariant:** content discovery uses outermost non-control candidates. An
  exact `PRE > CODE` wrapper is transparent rendered text, not permission to
  infer Markdown syntax, reconstruct source, or accept semantic equivalence.
- **Observed source defect:** synthetic first-binding operation
  `AGENTIFY-D94EE4B-SYNTHETIC-CHATGPT-PRO-ea06ff38-1ed3-4640-a1e5-f90731e3e19f`
  atomically verified and clicked the 121-character frozen prompt once, then
  durably observed user turn `61e57ab3-6544-4438-ae9a-e2471faf75b7` and a
  concrete `/c/` identity. The safe fingerprint was one candidate with root
  `PRE`, histogram `{PRE:1,CODE:1}`, two elements, one text node and depth two.
  `serializeReviewComposer` rejected PRE before reading that text. Separately,
  `serializeReviewUserMessage` retained only selector matches having no matching
  descendants, so an inner code block could shadow a complete outer candidate.
- **Historical classification:** the serializer stopped before returning text,
  length, or hash. Local evidence therefore cannot prove whether the PRE/CODE
  text was the complete raw prompt or only its fenced-code fragment. The
  operation remains `SUBMITTED_UNVERIFIED`, its observed turn remains durable,
  and it must never be resent or promoted from the new rule after the fact.
- **Implemented fix:** select outermost candidates by actual DOM
  containment. Accept PRE only when it has exactly one CODE element child, then
  serialize the CODE subtree with the same exact text-node/inline allowlist and
  no normalization beyond the downstream named plain-text model. A fragment
  fails full-prompt comparison; malformed PRE, controls, unsupported nodes and
  distinct candidates fail closed. Agentify commit `9679872` implements this
  rule, and active runtime commit `b6d9bbf` retains it.
  Defect L establishes that even a readable wrapper may be a lossy Markdown
  display and must not be treated as raw-source identity.
- **Regression:** `tests/chatgpt-controller.test.mjs` proves the exact synthetic
  heading, blank line, nested two-space list, fenced block and U+2014 payload
  survives `PRE > CODE` serialization; U+2014 mutation fails by code point; an
  outer candidate cannot be shadowed by its nested PRE; and malformed PRE
  diagnostics reveal no content. The complete controller strict suite plus
  review-transport/state suites retain mismatch, unreadable, observed-anchor,
  submission-diagnostic, recovery, content-rebind, raw-SHA and exact-one
  invariants.

### L. Causal submission identity is separate from rendered display fidelity

- **File/symbol:** `review-text-identity.mjs`,
  `REVIEW_CAUSAL_SUBMISSION_MODEL`, `reviewBaselineMessageIdsSha256`, and
  `validateReviewCausalSubmissionReceipt`; `chatgpt-controller.mjs`,
  `#clickReviewSendOnce`, `#waitForReviewUserMessage`, `reviewQuery`,
  `observeReviewResponse`, `#resolveReviewUserAnchor`, and
  `recoverReviewSubmission`; `review-transport.mjs`, `onSendAction`,
  `onUserTurnObserved`, `onSubmitted`, and `observePersistedReview`;
  `state.mjs`, causal-receipt/submission/display validation. Symbol locators are
  normative for active source/runtime commit `b6d9bbf`.
- **Invariant:** exact frozen-source identity, exact browser text at the unique
  click boundary, provider acceptance of exactly one baseline-new turn in a
  concrete conversation, and rendered display fidelity are four distinct facts.
  The first three may form `agentify_review_causal_submission_v1`; the fourth is
  diagnostic only. No semantic Markdown equivalence, delimiter reconstruction,
  trimming, contains/length/hash bypass, or provider-specific payload guess may
  bridge them.
- **Observed source defect:** operation
  `AGENTIFY-RENDERED-PRECODE-V1-CHATGPT-1c83cef6-ae16-49e4-9fa9-a6bdc9423f92`
  atomically verified and clicked the 132-character frozen prompt once, durably
  observed exactly one user turn
  `38001de2-55b1-4d41-bf39-1cf40a9eb423`, and recorded
  `/c/WEB:27879e24-aefb-4093-a414-e61164c47982`. Agentify's own
  `provisionalChatgptConversationId` classifies that `WEB:` value as provisional,
  not a canonical concrete first-binding identity. The rendered serializer was
  readable but returned length 124. The
  frozen source contains ten fence-token characters; Markdown display removes
  them while structural PRE block serialization contributes two newlines, which
  mechanically explains the net loss of eight. This is display transformation,
  not evidence that the click-bound prompt was corrupted.
- **Raw-anchor audit:** the current provider-neutral page architecture has no
  authoritative raw request-body anchor. `chrome-cdp-backend.mjs` enables Page,
  Runtime and DOM but does not capture Network request bodies;
  `electron-browser-backend.mjs` exposes executeJavaScript/input primitives but
  no webRequest interception; `#reviewSnapshot` reads turn IDs and rendered DOM.
  A provider-private endpoint, React-state probe, or network-payload parser would
  be provider-specific and unstable, so none is introduced.
- **Implemented fix:** after the atomic click, `onSendAction`
  persists a receipt bound to operation ID, exact source/canonical hashes,
  baseline-ID digest, `clickCount=1`, and `sendActionCount=1`, and returns that
  persisted receipt to the controller. Exactly one new visible turn plus the
  concrete URL/ID may then promote the durable anchor while rendered display is
  separately stored as `exact`, `lossy_mismatch`, or `unreadable`. A lossy turn
  can be observed only by its persisted ID; if that ID disappears, content rebind
  fails closed. Historical operations without this receipt are never promoted or
  resent retroactively.
- **Regression:** `tests/chatgpt-controller.test.mjs` reproduces the exact
  132-to-124 structural canary, requires one persisted causal receipt, one click,
  one visible turn and a concrete identity, and retains failure without that
  receipt. `tests/review-transport.test.mjs` proves the causal receipt and lossy
  display remain separate in a COMPLETE ledger. `tests/state.test.mjs` proves
  deterministic round-trip and rejects conflated source identity. Existing
  exact-one, composer mutation, no-turn, ambiguity, content-rebind, observer and
  never-resend regressions remain green.

### M. Gemini picker evidence uses semantic labels, not description or focus state

- **File/symbol:** `chatgpt-controller.mjs`,
  `geminiMenuItemSemanticLabel`, `geminiMenuItemSelected`,
  `geminiThinkingLabelMatches`, `canonicalizeGeminiModelEvidence`,
  `#readExpectedModelState`, `#ensureGeminiExpectedModel`, and
  `#reviewSnapshot`. Symbol locators are normative for active source/runtime
  commit `b6d9bbf`; line numbers are intentionally omitted.
- **Invariant:** Gemini model proof consists of two distinct, visible, selected
  menu items whose unique visible semantic labels are exactly `3.1 Pro` and
  `Extended thinking`/the localized label meaning “Extended thinking”. Parent
  abbreviations, focus/roving-tabindex state, hidden nodes, and account text are
  not model identity.
- **Live observation:** one disposable diagnostic tab was created at exactly
  `https://gemini.google.com/app` and closed without prompt input or Send. The
  genuine visible root was `GEM-MENU[role=menu][data-test-id=gem-mode-menu]`.
  Its `GEM-MENU-ITEM[role=menuitem]` model node had parent text
  `3.1 Pro` plus a localized description, while its visible `.label` was exactly
  `3.1 Pro` and its selected state was class/descendant-marker based. The
  thinking node likewise had a localized description while its `.label` was
  the exact localized “Extended thinking” label. Before thinking selection, the
  carried `data-active=true` although the 3.1 Pro item was selected; therefore
  `data-active` and class `active` are proven focus signals. After selection the
  closed trigger abbreviated the state as localized `Pro + extended`, not the exact model and
  mode labels. The tab remained at the root with zero user/assistant turns, an
  empty composer, and no Stop/Continue/Retry/Answer-now control.
- **Observed source defect:** `f0f48ef` used each menu item's complete
  `textContent` in both selection and evidence. Exact
  `geminiModelLabelMatches` therefore compared `3.1 Pro <localized
  description>` to `3.1 Pro` and could never choose or verify that live option.
  It also treated `data-active`/class `active` as selected and treated a trigger
  as selected evidence. Operation
  `AGENTIFY-CAUSAL-DISPLAY-V1-GEMINI-b9d214ee-76f5-4cb2-bb5f-064e9042d8b3`
  consequently failed `expected_model_unavailable` before Send with
  `sendActionCount=0`, `sendCount=0`, no turn, no concrete `/app/<id>`, and no
  generation. It is an explicit zero-commit historical operation, not evidence
  of account/model unavailability.
- **Implemented fix:** all Gemini adapter surfaces read the unique
  visible `.label` (or an unambiguous accessible label when no semantic label
  exists), require real selected state, and match the thinking label exactly.
  Full parent text is diagnostic only. Trigger records cannot satisfy canonical
  evidence. Selection, strict preflight, snapshots, and the ordinary entry
  point share the same adapter; production still has no ordinary fallback.
  Ambiguous/missing semantic labels fail closed with safe available-label data.
- **Regression:** `tests/chatgpt-controller.test.mjs` reproduces the live
  localized parent/label shape, proves `active`/`data-active` cannot select an
  option, rejects ambiguous labels and description-bearing full text, accepts
  the visible localized thinking label, and retains the strict composite
  selection path with exactly one Send boundary.

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
- Review plain-text identity, narrowly reversible Blink space mapping, and safe
  hash/causal receipts:
  `C:/Projects/agentify-desktop/review-text-identity.mjs:
  REVIEW_PLAIN_TEXT_MODEL,REVIEW_CAUSAL_SUBMISSION_MODEL,
  compareReviewPlainText,reviewBaselineMessageIdsSha256,
  validateReviewCausalSubmissionReceipt`.
- Composer replacement, draft-state synchronization, empty/caret proof:
  `C:/Projects/agentify-desktop/review-composer-replacement.mjs`.
- Live challenge, model, Gemini adapter DOM, send, and completion mechanics:
  `C:/Projects/agentify-desktop/chatgpt-controller.mjs:9-83,299-520,593-1086,1106-1930,2065-2299`.
- Gemini semantic picker label and real selected-state evidence:
  `C:/Projects/agentify-desktop/chatgpt-controller.mjs:
  geminiMenuItemSemanticLabel,geminiMenuItemSelected,
  geminiThinkingLabelMatches,canonicalizeGeminiModelEvidence,
  #readExpectedModelState,#ensureGeminiExpectedModel,#reviewSnapshot`.
- Rendered user-turn outermost candidate selection and exact PRE/CODE text
  extraction: `C:/Projects/agentify-desktop/chatgpt-controller.mjs:
  serializeReviewComposer,serializeReviewUserMessage,#reviewSnapshot`.
- Provider-neutral backend capabilities and absence of a raw request-body
  anchor: `C:/Projects/agentify-desktop/chrome-cdp-backend.mjs:
  ChromeCdpPageAdapter.initialize,evaluate`; `C:/Projects/agentify-desktop/
  electron-browser-backend.mjs:ElectronPageAdapter.evaluate,insertText`.
- Causal submission persistence and display-fidelity separation:
  `C:/Projects/agentify-desktop/review-transport.mjs:onSendAction,
  onUserTurnObserved,onSubmitted,observePersistedReview`;
  `C:/Projects/agentify-desktop/state.mjs:validateReviewTransportState`.
- Ledger schema and atomic persistence:
  `C:/Projects/agentify-desktop/state.mjs:6-15,34-155,257-272`.
- Default tab/status construction:
  `C:/Projects/agentify-desktop/main.mjs:254-266,639-652`.
