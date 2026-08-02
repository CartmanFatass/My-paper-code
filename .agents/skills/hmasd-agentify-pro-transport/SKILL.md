---
name: hmasd-agentify-pro-transport
description: Receipt-bearing Agentify transport for one HMASD external-review turn through ChatGPT or Gemini.
---

# HMASD Agentify External Review Transport

This Skill is a mechanical transport interface. It grants no scientific,
workflow, code, compute, Git or project-state authority. The owning persistent
CPM or Explorer session runs it directly; no transport child, monitor,
heartbeat or browser fallback participates.

## Unified interface and binding

ChatGPT and Gemini use the same lifecycle:

```text
prepare -> submit once -> verify natural completion -> archive exact response
provider=chatgpt|gemini
terminal=NATURAL_COMPLETION_VERIFIED|AGENTIFY_TRANSPORT_BLOCKED
```

Provider adapters may differ only in URL parsing, selectors, visible-model
evidence and message-identity extraction. ChatGPT Pro is canonical and Gemini
advisory only in local intake metadata; neither label enters the question.

```text
code_project_manager/chatgpt -> hmasd-formal-pro
code_project_manager/chatgpt -> hmasd-uav-formal-pro
code_project_manager/chatgpt -> hmasd-explorer-validation-pro
independent_research_explorer/chatgpt -> hmasd-independent-research-explorer-pro
independent_research_explorer/gemini -> hmasd-independent-research-explorer-gemini
```

Conversation URL, ID, model and credentials are live runtime values. A stable
key is immutable after its first persisted binding and later turns reuse the
same page. `/health` must report the wrapper's pinned Agentify commit with
`sourceDirty=false`. Before a normal send, authenticated `/tabs` and scoped
`/status` must show one exact, idle, unblocked and prompt-visible page. When
that exact already-live page is still registered only as Agentify's `default`
tab, one explicit `submit --adopt-existing-tab` may assign the durable stable
key in place. Adoption requires one exact URL/provider match and performs no
create, show, navigation, refresh or binding change.

## Plan first and RAW_QUESTION only

Before touching Agentify, freeze a concise local execution plan containing the
question path, provider instances and pages, operation keys and maximum sends,
preflight/status observations, archives, verify-existing recovery and
completion criteria. This is not a new user gate inside an active grant.

The reviewer-facing UTF-8 file is a standalone `RAW_QUESTION`: only the
natural-language scientific question, including intrinsic equations, headings
and treatment labels. Local authorization, session, role, campaign/candidate/
review/operation identity, Git locator, filesystem path, provenance state,
transport/recovery/archive instruction and provider labels remain only in the
local plan, selection, request and receipt.

The strict `/review-query` path performs one direct `insertText` of the whole
question, verifies the composer and performs one send action. Generic `/query`,
per-character human typing, attachments, keyboard/computer-use fallback,
placeholder messages and UI response controls are forbidden.

## Request and first binding

`prepare` records local owner, provider, binding, operation and archive
identity. None of those local fields is added to the question. Existing
bindings supply explicit provider, live model, URL and conversation ID.

For the first ChatGPT binding only, begin from one authenticated blank
`https://chatgpt.com/` page and use `prepare --first-binding` without caller
URL/ID. The single persisted question produces the real `/c/<id>` identity,
which Agentify binds durably before response observation continues. No
placeholder, discovery send or historical binding reassignment is used.
Gemini begins from its existing `https://gemini.google.com/app/<id>` page and
uses the identical lifecycle.

`--allow-tab-creation` is limited to first ChatGPT binding or reopening the
same durable page after Agentify restart. It never substitutes or reassigns a
conversation. A persisted user-message identity is the irreversible boundary:
once present, never terminate, resend or switch pages; observe that operation
through natural completion.

## Minimal recovery

If evidence invalidates the local plan, stop the affected branch and return to
read-only status and durable-ledger diagnosis. Run
`submit --verify-existing` on the same request. `present=true` resumes
observation without sending. Only `present=false`, no persisted user message
and an unchanged question allow one fresh operation key and at most one fresh
send under the active grant.

Never switch tools, interfaces or transport strategy during recovery. A second
failure returns `AGENTIFY_TRANSPORT_BLOCKED` with exact local predicates; it is
not a scientific result and consumes no scientific iteration.

## Mechanical commands

All paths are absolute at invocation. Agentify owns the durable ledger; the
wrapper owns request preparation, validation and the new role-owned receipt.
The caller supplies no content digest, fingerprint, monitor or heartbeat
command, or opaque token.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  prepare --owner <registered-owner> --stable-key <owner-key> `
  --provider <chatgpt|gemini> --model <live-model> --conversation-url <live-exact-url> `
  --conversation-id <live-id> --assignment-identity <exact-assignment> `
  --operation-key <round-unique-key> --prompt-path <absolute-RAW_QUESTION> `
  --timeout-ms 2700000 --selection <new-absolute-TRANSPORT_BACKEND.json> `
  --request <new-absolute-request.json>
```

For first ChatGPT binding, replace URL and ID with `--first-binding`.
`prepare` verifies a nonempty UTF-8 question and validates the local request;
it never requires local assignment metadata to appear in the question.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  submit --request <absolute-request.json> --receipt <new-absolute-receipt.json> `
  [--state-dir <absolute-agentify-state-dir>] [--verify-existing] `
  [--adopt-existing-tab]
```

`submit` proves the exact ready page, calls strict `/review-query` once and
observes the durable operation. Process existence is never send evidence.
`--verify-existing` only observes. Neither mode clicks response controls or
uses an alternate transport.
`--adopt-existing-tab` is limited to one unique exact existing-binding page
whose current Agentify key is `default` or empty; it changes only that in-memory
key before the same strict send path.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  verify --request <absolute-request.json> --receipt <absolute-receipt.json>
```

`verify` is local receipt validation only. Natural completion requires the same
assistant message and text in two snapshots at least three seconds apart, with
no active generation or continuation control. Long reasoning remains inside
the original operation deadline.

After `verify`, archive the exact response without rewriting:

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  archive --request <absolute-request.json> --receipt <absolute-receipt.json> `
  --raw-output <absolute-role-owned-raw-path>
```

`archive` requires exact local reread equality. CPM writes under
`docs/external-review`; Explorer writes under `local_research/pro_reviews`.
Mechanical intake and all scientific interpretation stay with the owner.

## Required receipt and failure semantics

The receipt must contain, at minimum:

```text
stableKey
provider
conversationId
conversationUrl
model
idempotencyKey
sendCount=1
sendActionCount=1
userMessageId
submittedAt
assistantMessageId
snapshots=2_same_assistant_identity_with_gap_ms>=3000
clickedControls=[]
terminalState=NATURAL_COMPLETION_VERIFIED
```

The snapshots use the same assistant identity. Missing or conflicting fields,
`sendCount != 1`, conversation mismatch or incomplete generation yields
`AGENTIFY_TRANSPORT_BLOCKED`. No digest, byte count or fingerprint is a
workflow admission field.

On success, the wrapper returns the receipt/raw path and stable `operationId`
to the owner. Keep credentials, endpoint state and live bindings outside Git.
