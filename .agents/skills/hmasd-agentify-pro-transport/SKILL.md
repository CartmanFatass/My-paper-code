---
name: hmasd-agentify-pro-transport
description: Optional receipt-bearing Agentify transport for one HMASD External Pro review turn, selected before submission and isolated from the browser sentinel path.
---

# HMASD Agentify Pro Transport

This Skill is a mechanical wrapper contract. It grants no review, scientific,
runtime, code, Git or project-state authority. The registered transport owner
must first freeze `transport_backend=agentify` for the current round under
`$hmasd-review-round`; otherwise this Skill is not active. Existing browser
transport remains an alternative that may be chosen only before the immutable
backend-selection record exists. It is never a post-send fallback and is never
run in parallel for the same round.

## Runtime binding

Use the locally installed Agentify endpoint and the HMASD conda interpreter:

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
wrapper=.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py
runtime_contract=docs/project/AGENTIFY_PRO_TRANSPORT.md
required_agentify_source_commit=917c5328695b4546e8c7e548878b00a07f45af91
```

Read the runtime contract before use. The wrapper requires the live Agentify
`/health` identity to report this exact source commit with
`sourceDirty=false`; missing or conflicting source identity blocks before a
send.

The request must provide a fixed role-owned `stable_key`:

```text
hmasd-formal-pro
hmasd-independent-research-pro
hmasd-explorer-validation-pro
```

Conversation ID, exact URL, endpoint token and the selected Pro model are
runtime values. They must be read from the live Agentify binding and must not
be invented, committed, copied into a question, or obtained from repository
history. The wrapper rejects a stable-key binding whose provider, conversation
or model is missing or conflicts with the current round.

Keep runtime request and receipt files in the owner boundary: ROM uses the
applicable `logs/` review root and IRRO uses
`local_research/pro_reviews/`. Prompt and raw-output files remain in ROM's
`docs/external-review/` or IRRO's `local_research/pro_reviews/` root. Do not
place credentials, Agentify state or live conversation registrations in Git.

## Request and one-send contract

Run `prepare` once from the exact prompt file. The wrapper computes the prompt
SHA-256 itself and creates the immutable backend selection plus UTF-8 request;
the operator never calculates, copies or edits the hash. The generated request
contains exactly these fields (the wrapper rejects unknown or missing identity
fields):

```json
{
  "schema_version": 1,
  "transport_backend": "agentify",
  "transport_owner": "independent_research_review_operator",
  "stable_key": "hmasd-independent-research-pro",
  "provider": "chatgpt",
  "model": "<live-pro-model>",
  "conversation_url": "<live-runtime-url>",
  "conversation_id": "<live-runtime-id>",
  "idempotency_key": "<round-unique-key>",
  "assignment_identity": "<exact-round-or-assignment-identity>",
  "backend_selection_path": "<absolute-immutable-TRANSPORT_BACKEND.json>",
  "prompt_path": "<absolute-immutable-prompt>",
  "prompt_sha256": "<sha256-of-exact-utf8-prompt>",
  "timeout_ms": 2700000
}
```

`backend_selection_path` must be a new role-owned runtime file containing
exactly `schema_version=1`, the same `assignment_identity`, and
`transport_backend=agentify`; its `operation_key` must equal the request's
`idempotency_key`, and its `prompt_sha256` must equal the request prompt hash.
It is the restart-stable cross-backend and same-assignment operation freeze and
is never overwritten. `assignment_identity` must occur in the exact prompt
bytes at `prompt_path`. `timeout_ms` is between 3000 and 2700000 inclusive. Agentify
owns its durable ledger and send idempotency; the HMASD wrapper validates the
request, calls Agentify, and writes a new role-owned receipt. The wrapper does
not persist send intent or claim to click UI controls. No automatic Continue,
Retry, ResponseRetry, Answer now, duplicate submission, cross-conversation
fallback or response synthesis is allowed. A conflicting existing
idempotency record, identity mismatch or unreadable content terminates as a
transport blocker.

## Mechanical commands

All paths are absolute at invocation. Agentify owns the durable ledger; the
wrapper owns request preparation, validation and the new role-owned receipt.
The caller supplies no prompt hash, assembled monitor command or opaque token.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  prepare --owner <registered-owner> --stable-key <owner-key> `
  --model <live-pro-model> --conversation-url <live-exact-url> `
  --conversation-id <live-id> --assignment-identity <exact-assignment> `
  --operation-key <round-unique-key> --prompt-path <absolute-prompt> `
  --timeout-ms 2700000 --selection <new-absolute-TRANSPORT_BACKEND.json> `
  --request <new-absolute-request.json>
```

`prepare` is idempotent only for byte-identical outputs. It verifies that the
prompt is exact UTF-8 and contains the assignment identity, computes its hash,
and validates the generated pair before returning. A changed prompt, model,
conversation or operation identity cannot overwrite the pair.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  submit --request <absolute-request.json> --receipt <new-absolute-receipt.json> `
  [--state-dir <absolute-agentify-state-dir>] [--verify-existing]
```

`submit` returns one terminal operation identity. Do not submit a second time
after an exception; use `--verify-existing` only for the same idempotency key
when an existing Agentify operation must be observed. To inspect the same
operation after restart:

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  verify --request <absolute-request.json> --receipt <absolute-receipt.json>
```

`verify` is local receipt validation only and never sends. If `submit` cannot
return a terminal receipt, do not infer failure or submit again. A later
`submit --verify-existing` may observe only the same Agentify ledger operation
and idempotency key. Natural completion requires the exact same assistant
message identity and complete text in two stable snapshots at least three
seconds apart and no active generation or continuation control. A visible
Answer now control is never activated and is not completion
evidence. Long Pro reasoning remains inside the original absolute operation
deadline; the wrapper does not create a short-watch terminal state.

After `verify` returns a complete receipt, archive the exact response bytes
without rewriting and bind the archive to the receipt:

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  archive --request <absolute-request.json> --receipt <absolute-receipt.json> `
  --raw-output <absolute-role-owned-raw-path>
```

`archive` is permitted only for a complete receipt and reread byte equality.
For ROM, the raw-output path is under `docs/external-review`; for IRRO it is
under `local_research/pro_reviews`. Mechanical intake remains the applicable
owner's normal next step. No response interpretation is performed here.

## Required receipt and failure semantics

The receipt must contain, at minimum:

```text
stableKey
provider
conversationId
conversationUrl
model
modelEvidence
idempotencyKey
promptSha256
sendCount=1
userMessageId
assistantMessageId
snapshots=2_same_identity_and_hash_with_gap_ms>=3000
responseSha256
clickedControls=[]
terminalState=NATURAL_COMPLETION_VERIFIED
```

The two snapshots must be tied to the same exact assistant identity and the
same round. Missing or conflicting fields, `sendCount != 1`, a duplicate
message, a model/conversation mismatch, incomplete generation or unreadable
identity yields `AGENTIFY_TRANSPORT_BLOCKED`. It never authorizes a browser
fallback, a second Agentify send or a scientific iteration. Restart recovery
is observe-only for the same request, Agentify operation and receipt.

On success, the wrapper output returns the receipt path or raw path plus the
validated stable `operationId` to
the registered transport owner. Keep secrets,
credentials, endpoint state and live conversation registration outside Git.
