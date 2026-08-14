---
name: hmasd-agentify-transport
description: Execute one HMASD file-backed ChatGPT Pro or Gemini consultation through Agentify's unified strict exact-one transport, archive the mechanical result, and return it to the invoking L1 owner.
---

# HMASD Agentify transport

```text
agentify_transport_child=parent-specific_registered_leaf
transport_core=agentify_review_query
providers=chatgpt|gemini
manual=C:/Projects/HMASD/docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md
```

Read the canonical manual completely before any Agentify action. The manual is
normative for page, tab, provider, model, identity, strict-send, recovery,
archive, and cleanup mechanics. Provider-specific skills or historical notes
cannot weaken it. Gemini is a provider adapter of the same strict transport;
do not route it through ordinary query, a parallel workflow, hidden DOM
evidence, or provider-special-case folklore.

## Assignment and authority

The requester supplies exactly:

```text
AGENTIFY_REVIEW_BATCH_ASSIGNMENT
batch_path=<absolute UTF-8 JSON in the requester's closed partition>
results_path=<exact assignment-specific output path in that partition>
```

Allowed requester partitions are:

```text
temp/sessions/agentify_transport_operator/root/<assignment>/
temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/
temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/
```

Read the exact batch once, then its exact `context_path` and ordered
`question_paths`. Do not scan temporary directories, infer paths, regroup
questions, or cross requester partitions. The context is local understanding
input; only the exact UTF-8 question file is provider-visible. Reject a prompt
containing a local absolute path, `file://` URI, requester temp path, workspace
path, shell/tool wrapper, hash/receipt block, or code/runtime-review request.

This leaf has mechanical transport authority only. It does not choose,
interpret, approve, rank, implement, or accept science or code; contact the
user; use Git; write canonical project state; or spawn.

## Deterministic procedure

For every ordered question:

1. **Validate locally.** Freeze provider, exact new-versus-continuation
   relationship, immutable conversation `stableKey`, new immutable
   `idempotencyKey`, exact expected visible model, exact URL/ID, question bytes,
   lowercase SHA-256, result path, and `2700000` ms timeout.
2. **Use L1 admission.** Proceed only inside the invoking L1's shared
   `max_inflight` admission. Root does not poll or schedule the leaf. Agentify's
   unified ordinary/strict governor is only the last safety barrier: a fresh
   strict capacity rejection is pre-send `rate_limited` with
   `reason=max_inflight`, `operationKind=strict-review`, and
   `sendActionCount=0`. Do not retry inside the call. Exact existing-operation
   observation/`verifyExisting` does not reserve a second send slot.
3. **Bind one disposable tab.** Preserve the protected default. Create the
   provider tab with `key=name=stableKey`. For a continuation, navigate by
   `tabId` to the saved exact URL. Require live status URL and registry-row URL
   to equal the intended URL before strict review.
4. **Confirm live preflight.** Require idle composer, no active generation,
   correct conversation relationship, and genuine visible model controls.
   ChatGPT requires visible Pro. For Gemini, pass
   `Gemini 3.1 Pro extended`; the strict shared adapter independently selects
   and visibly verifies exact `3.1 Pro` plus selected `Extended thinking`
   before baseline capture. Account-plan text, generic `Pro`, menu availability,
   synthetic/hidden DOM, and helper-injected evidence are invalid.
5. **Call strict review once.** Use only `agentify_review_query` with the exact
   `promptPath`, SHA, stable key, idempotency key, provider/model, URL/ID,
   `existingTabId`, timeout, and correct `firstBinding` flag. New ChatGPT uses
   `https://chatgpt.com/` plus `__new__`; new Gemini uses
   `https://gemini.google.com/app` plus `__new__`. A continuation uses its saved
   concrete `/c/<id>` or `/app/<id>` and `firstBinding=false`.
6. **Classify commitment from postconditions.** Composer typing, a click, or
   `sendActionCount` is not a provider turn. Before Send require exact composer
   serialization; afterward require exactly one new readable user turn whose
   rendered text equals the frozen prompt, plus concrete provider identity. An
   unreadable/mismatched post-click turn is ambiguous and must never be resent.
   If Gemini stabilizes at zero turns, no `/app/`
   ID, the full prompt retained, and no generation, archive
   `SEND_NOT_COMMITTED` with `prompt_sent=false` and
   `response_received=false`; do not retry in this call. Any turn, identity,
   `sendCount=1`, or ambiguity means never resend.
7. **Observe naturally.** Never activate Stop, Continue, Retry, Response Retry,
   Answer now, regenerate, or acceleration controls. `IN_PROGRESS` means keep
   observing the same operation. After a client/fetch failure, inspect the
   durable strict operation. Use `verifyExisting=true` only for the exact
   original fingerprint and only as observation; never change a field or call
   another send route.
8. **Accept only strict natural completion.** Require `status=COMPLETE`, full
   nonempty `responseText`, exact concrete URL/ID, visible model evidence,
   `sendCount=1`, `sendActionCount=1`, matching `promptSha256`, two stable
   snapshots, no active forbidden controls, and
   `terminalState=NATURAL_COMPLETION_VERIFIED`.
9. **Archive before cleanup.** Write the canonical schema defined in the manual
   once at the exact `results_path`, preserving question order and any completed
   earlier rows. Copy response and receipt only from the structured strict
   result. A stale/missing archive may be restored only from a valid authoritative
   local strict ledger operation and without page action; never overwrite an
   existing archive.
10. **Close safely.** After complete response or terminal error is durably
    archived and generation is inactive, close the disposable tab. Never close
    an active answer or keep an idle tab to preserve remote memory. Report close
    failure.

Do not fall back to `agentify_query`. Do not restart/reload Agentify while any
provider generation or submitted-unverified operation may exist. A status,
registry, model, URL, or archive conflict is a reason to reconcile or fail
closed, never permission to send.

### Incident observation and authority boundary

A transport incident is a mechanical report, never a goal or thread conclusion.
Inspect the native Agentify surface first: use `agentify_tabs` to identify the
exact tab, then exact-tab `agentify_read_page`/DOM evidence. Scoped status and
`loginLike` are diagnostic hints only. A Computer Use/Chrome safety refusal to
capture the URL is `UNOBSERVED`, not login/logout evidence; user observation is
evidence to reconcile, not automatic replacement for the native record.

For any non-complete terminal, archive the exact-one mechanical state without
another send, then return `INCIDENT_REPORTED`, never generic `BLOCKED` or a
claim that the thread, goal, production, unrelated work, or user is blocked.
The report must include observed facts, observation method, actions taken,
actions not taken, remaining unknown, causal hypotheses, and the smallest
next authority/action. `ERROR`, `BLOCKED`, or similar values retained inside a
strict ledger or results archive remain mechanical terminal facts; they do not
become the leaf's routing or goal status.

The transport return is evidence only, never a command to CM, Root, EM, or the
portfolio session. An exact-one terminal, exhausted fresh-tab allowance,
non-resend boundary, absent response, or resource limit must not be phrased as
the scientific treatment being consumed, non-resumable, paused, retired, or
limited to a binary next choice. Without complete question-relevant data, the
invoking L1 routes unchanged-science repair/completion to CM. Only a
same-direction EM's prospective definition of finite compute as causal can
give that budget scientific force. Preserve the strict ledger's internal status
facts and exact-one/no-resend protections while retaining a resumable blinded
atomic frontier whenever the frozen transport semantics allow it.

Pending user adjudication, one-attempt/no-retry, CM-recommend-park, fixed
wall-cap, terminal/`ERROR`, archive/commit/push-before-intake, and stale
Pro/Gemini retry schemas are not transport authority to pause, retire, or
scientifically route a direction. They remain mechanical facts. Do not infer
permission for a resend: the exact no-resend boundary remains absolute after a
visible/provider turn or concrete conversation identity. A transport failure
without that commitment still cannot pause the scientific direction; the
invoking L1/CM retains same-coordinate, semantics-preserving atomic completion
while a resource slice pauses only its lease.

If the invoking L1's protocol/workflow-design recovery explicitly authorizes
source repair, diagnostics, runtime control, and bounded live validation, an
old transport primitive, stale Skill, or one exhausted observation surface is
internal design evidence. The L1 must construct and use the next constrained
observation/input primitive within its authorized validation budget; the leaf's
incident report cannot convert it into a user/Root/portfolio boundary. This
does not authorize a second provider turn after the exact no-resend predicate.
Only a directly required user-exclusive credential or physical action, an
irreversible external risk, or an unapproved external side effect is a genuine
external boundary.

## Result guard and return

Before returning `COMPLETE`, run:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  C:/Projects/HMASD/.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py `
  --repo C:/Projects/HMASD `
  --expected-results-path <assigned-results-path> `
  --returned-results-path <assigned-results-path>
```

On guard failure return `INCIDENT_REPORTED` with an empty `results_path`; do
not move, copy, rewrite, or read another result file. Return exactly once to the invoker,
conclusion first, then:

```text
AGENTIFY_REVIEW_BATCH_RESULT
status=COMPLETE|INCIDENT_REPORTED
results_path=<exact assigned path or empty>
transport_terminal=<COMPLETE|ERROR|SEND_NOT_COMMITTED|SUBMITTED_UNVERIFIED|other exact mechanical terminal>
error=<empty or actual mechanical error>
observed_facts=<direct facts only>
observation_method=<native exact-tab method, ledger/archive, or UNOBSERVED>
actions_taken=<exact actions>
actions_not_taken=<no resend/other safety-preserving omissions>
remaining_unknown=<none or exact unknown>
causal_hypotheses=<evidence-backed alternatives>
next_authority_or_action=<smallest owner/action, or none>
```
