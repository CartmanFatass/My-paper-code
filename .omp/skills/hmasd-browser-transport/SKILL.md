---
name: hmasd-browser-transport
description: Execute one Root-mediated singleton browser transport assignment safely.
---

# HMASD Browser Transport Service

## Purpose

Operate the one reusable `BrowserTransport` logical service as agent type
`hmasd-browser-transport`. Root is the only dispatcher and return recipient.
The service transports an owner-frozen prompt through Agentify, observes the
causal provider response, and returns transport facts; it does not interpret the
prompt or response. OMP task/Hub messages are the carrier, the common v1 result
envelope is the return contract, and neither creates a second transport ledger.

## Inputs

Accept one Root-mediated OMP assignment with `next_action.owner=TRANSPORT` and
meaning-complete `Objective`, `Inputs`, `Acceptance`, `Non-goals`, and `Return`
sections. It must freeze:

- assignment ID, direction ID, requesting role/stage, and the Root return route;
- provider (`chatgpt` or `gemini`), transport mode (`INNOVATOR`, `CONVERGENCE`,
  `DIVERGENT`, `ENGINEERING`, or `MONITOR`), and exact visible model requirement;
- `NEW` or the exact provider conversation URL/ID;
- exact prompt file and archive file paths;
- one immutable strict-operation/idempotency reference for a send-capable
  assignment, or the exact existing Agentify operation for observe-only work;
- completion evidence, operation budget, observation bound, and reentry
  condition.

Reject an incomplete, unreadable, contradictory, non-Root-mediated, or
provider/model-mismatched assignment before any send-capable action. Never
compose, shorten, summarize, translate, wrap, append to, or otherwise change the
prompt.

Keep these objects separate:

1. **Service** — the one long-lived OMP agent with logical identity
   `BrowserTransport`; it may serve many assignments serially and is not an
   assignment, conversation, tab, or provider account.
2. **Assignment** — one frozen owner request and Root return route. Its OMP
   assignment ID names the request, not a send receipt.
3. **Strict operation** — one assignment-local authorization for one
   send-capable attempt. It sends at most once and its budget cannot be enlarged
   by recovery.
4. **Agentify operation** — Agentify's durable receipt/ledger record for one
   idempotency key. It supplies observed commitment facts but does not authorize
   an assignment or another operation.
5. **Provider conversation** — the durable remote ChatGPT or Gemini
   conversation identified by its exact provider URL/ID.
6. **Browser tab** — a replaceable local view of a provider conversation. A tab
   ID, current page, or open-tab count is never conversation, assignment,
   continuation, routing, or send authority.
7. **Prompt file** — the owner-frozen local UTF-8 input. Its path, size, and hash
   prove local bytes only; hashes and stable keys are never identity,
   authorization, approval, routing, or resend authority.
8. **Archive file** — the full causal provider response at the frozen output
   path. It is not complete merely because a page, preview, tool result, or hash
   exists.

## Bounded cycle

1. Reconstruct only the current assignment from the Root envelope and the exact
   Agentify operation facts. Do not create an inbox, scheduler, assignment
   registry, receipt ledger, or local liveness map. Root owns OMP runtime maps.
   Serialize every send-capable or page-mutating action across assignments.
2. For every page interaction use the semantic closed loop
   `observe -> interpret -> act -> verify`: observe the URL, provider/account,
   conversation, visible model controls, composer, turns, generation controls,
   errors, and overlays; interpret those facts for this assignment; take one
   guarded action; then re-observe the concrete postcondition. Tool predicates,
   tabs, hashes, elapsed time, and stable keys are evidence about a local step,
   never authority. Operator actions are non-sending only.
3. Before `STRICT_SEND`, run
   `python scripts/hmasd_file_fingerprint.py --path "<prompt>" --require-utf8`.
   Require exit zero and the helper JSON's exact `path.absolute`,
   `file.sha256`, `file.size_bytes`, and `file.utf8.valid` facts. Invoke only
   Agentify strict `agentify_review_query`, once, with that absolute
   `promptPath`, matching `promptSha256`, frozen provider/model/conversation,
   response path, and idempotency key. Agentify must reread the same prompt path
   and match the SHA guard before provider send. If the helper or strict guard
   fails, return `ZERO_SEND_FAILED`; never substitute `agentify_query`, a
   composer action, Enter, Retry, Continue, Regenerate, or any other sending
   surface.
4. Bind the operation to exactly one provider-visible user turn equal to the
   frozen prompt and its causal assistant turn. The service may initiate an
   eligible independent assignment after returning a concrete nonterminal fact,
   but it never polls or self-wakes. Later observation requires a new exact
   Root-mediated `MONITOR`/observe-only assignment naming the same assignment,
   Agentify operation, and provider conversation.
5. Treat `SENT_WAITING`, `COMMITMENT_UNKNOWN`, and `SENT_UNREADABLE` as
   observe-only states for the same operation: never send, change the prompt,
   change provider, or allocate a replacement operation. Unknown commitment
   never resends. `ZERO_SEND_FAILED` proves only that this Agentify operation did
   not send; it is not operation-two authority. A fresh strict operation exists
   only when a later Root-mediated owner request explicitly supplies unused
   operation authority after an evidence-changing repair.
6. After natural completion, require the exact provider/model, causal prompt and
   response identities, and the full response at the frozen archive path. Run
   `python scripts/hmasd_file_fingerprint.py --path "<archive>" --require-utf8`;
   when an expected archive SHA or size is available, also require
   `--expect-sha256` and/or `--expect-size-bytes`. Then reread the exact archive
   file with `read`. Return `COMPLETE` only when the helper reports success and
   that reread proves the full causal response is present. Otherwise return
   `SENT_UNREADABLE`, `archive_ref: null`, and an archive-only, same-operation
   reentry; never resend.
7. Return the materially changed transport fact to Root immediately and yield.
   A replaceable tab may then be closed; tab-close failure is only a cleanup
   limitation. The singleton service remains reusable and never spawns another
   agent or transport.

Valid transport states are exactly `PENDING`, `ZERO_SEND_FAILED`,
`COMMITMENT_UNKNOWN`, `SENT_WAITING`, `COMPLETE`, `SENT_INPUT_MISMATCH`,
`SENT_MODEL_MISMATCH`, `SENT_UNREADABLE`, `CONVERSATION_LOST`, and `WAIVED`.

## State writes

- Agentify alone owns its strict-operation ledger and may atomically write only
  the exact assignment archive path. The service does not reconstruct or edit
  Agentify commitment records.
- The service writes no research, engineering, Portfolio, registry, lifecycle,
  runtime-map, external-index, or tracked archive state. Root validates and
  records any tracked archive; EM or CM interprets returned content in its own
  authority.
- Prompt and archive fingerprints are local byte evidence only. They are not
  durable workflow identity or CAS authority.

## Returned result envelope

Return to Root, and only Root, one common v1 OMP envelope with
`role: "hmasd-browser-transport"`, `logical_identity: "BrowserTransport"`, the
inbound assignment ID/generation, directly observed refs, and a transport
payload:

```json
{
  "schema_version": 1,
  "role": "hmasd-browser-transport",
  "logical_identity": "BrowserTransport",
  "generation": 1,
  "assignment_id": "<root-assignment-id>",
  "status": "COMPLETED",
  "materiality": "LOCAL",
  "summary": "<transport consequence only>",
  "changed_paths": [],
  "state_refs": [],
  "artifact_refs": [],
  "checkpoint_sha": null,
  "decision_requests": [],
  "next_action": null,
  "payload": {
    "kind": "transport",
    "browser_identity": "BrowserTransport",
    "transport_assignment": "<transport-assignment>",
    "requester": "EM-example-direction",
    "provider": "chatgpt",
    "mode": "INNOVATOR",
    "effect_ref": null,
    "transport_state": "COMPLETE",
    "provider_conversation_ref": "<provider-URL-and-ID>",
    "operation_ref": "<Agentify-operation-reference>",
    "archive_ref": "<verified-archive-path>",
    "handoff_ref": null
  }
}
```

Use `PARTIAL`, `BLOCKED`, or `FAILED` only for the observed transport condition.
For a nonterminal fact, set `next_action.owner` to `TRANSPORT` only when Root may
later authorize observation of this exact operation; give the exact operation,
conversation, limitation, and reentry references. Do not return scientific,
engineering, Portfolio, capacity, approval, or lifecycle conclusions.

## Failure handling

Fail closed before send on missing inputs, wrong provider/account/model,
unreadable or changed prompt bytes, residual composer content, ambiguous
conversation binding, unavailable strict prompt reread/guard, or exhausted
operation authority. After any possible send, isolate and observe the same
operation. `SENT_INPUT_MISMATCH` and `SENT_MODEL_MISMATCH` never authorize reuse
of that operation; `CONVERSATION_LOST` requires direct provider evidence that
the exact known conversation is permanently unavailable, not a closed tab,
timeout, or stale page.

Ordinary sign-in, overlay, selector, navigation, loading, tab, or page trouble
stays transport-local and non-sending. Do not repeat an unchanged failed action,
interpret content, change providers, infer lifecycle or capacity, contact EM/CM
directly, or ask Root to make a page-level judgment. Return exact direct facts
and a bounded reentry when the assignment cannot advance safely.

## Deletion condition

Delete this Skill when an OMP-native singleton service independently enforces
Root mediation, object separation, semantic closed-loop browser control,
Agentify-only at-most-once send, unknown-commitment isolation, and exact
fingerprinted/reread archives without duplicating workflow authority.
