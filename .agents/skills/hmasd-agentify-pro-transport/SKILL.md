---
name: hmasd-agentify-pro-transport
description: Sole receipt-bearing Agentify transport for one HMASD External Pro review turn.
---

# HMASD Agentify Pro Transport

This Skill is a mechanical wrapper contract. It grants no review, scientific,
runtime, code, Git or project-state authority. The registered transport owner
uses this Skill for every External Pro transport turn.

## Runtime binding

Use the locally installed Agentify endpoint and the HMASD conda interpreter:

```text
python=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
wrapper=.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py
runtime_contract=docs/project/AGENTIFY_PRO_TRANSPORT.md
required_agentify_source_commit=read_AGENTIFY_REQUIRED_COMMIT_from_wrapper
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

Run `prepare` once from the prompt file. The wrapper creates the backend
selection plus UTF-8 request. The generated request
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
  "prompt_path": "<absolute-prompt>",
  "timeout_ms": 2700000
}
```

`backend_selection_path` must be a new role-owned runtime file containing
exactly `schema_version=1`, the same `assignment_identity`, and
`transport_backend=agentify`; its `operation_key` must equal the request's
`idempotency_key`. It is the restart-stable cross-backend and same-assignment
operation record and is never overwritten. `assignment_identity` must occur in
the UTF-8 prompt at `prompt_path`. `timeout_ms` is between 3000 and 2700000 inclusive. Agentify
owns its durable ledger and send idempotency; the HMASD wrapper validates the
request, calls Agentify, and writes a new role-owned receipt. The wrapper does
not click UI controls. No automatic
Continue, Retry, ResponseRetry, Answer now, duplicate submission,
cross-conversation fallback or response synthesis is allowed. A conflicting existing
idempotency record or unavailable conversation terminates as a
transport blocker.

## Minimal recovery

The adapter waits without sending while the conversation generates. Before recovery, run `submit --verify-existing` on the failed operation.
Only no recorded user message permits one fresh unchanged-question operation; otherwise observe and verify/archive the original, never resend it.

The adapter never clicks Stop, Continue, Retry or Answer now. A second recovery
resend requires a new user instruction.

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
prompt is UTF-8 and contains the assignment identity, then validates the
generated pair before returning. A changed prompt, model,
conversation or operation identity cannot overwrite the pair.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  submit --request <absolute-request.json> --receipt <new-absolute-receipt.json> `
  [--state-dir <absolute-agentify-state-dir>] [--verify-existing]
```

`submit` returns one terminal operation identity. `--verify-existing` probes the
same failed operation for a recorded user message and never sends.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py `
  verify --request <absolute-request.json> --receipt <absolute-receipt.json>
```

`verify` is local receipt validation only and never sends. Natural completion
requires the same assistant
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

Every prompt carries its full 40-hex `stage_commit`; a prefix is rejected, and this Skill's allow-list scripts archive only that committed source.
The receipt must contain, at minimum:

```text
stableKey
provider
conversationId
conversationUrl
model
idempotencyKey
sendCount=1
userMessageId
assistantMessageId
snapshots=2_same_identity_and_hash_with_gap_ms>=3000
responseSha256
clickedControls=[]
terminalState=NATURAL_COMPLETION_VERIFIED
```

The two snapshots must be tied to the same assistant identity. Missing or
conflicting fields, `sendCount != 1`, a conversation mismatch or incomplete
generation yields `AGENTIFY_TRANSPORT_BLOCKED`; recovery follows `Minimal recovery`.

On success, the wrapper output returns the receipt path or raw path plus the
validated stable `operationId` to
the registered transport owner. Keep secrets,
credentials, endpoint state and live conversation registration outside Git.
