---
name: hmasd-agentify-transport
description: Use when an HMASD owner has frozen one file-backed ChatGPT Pro or Gemini consultation for exact-one delivery through Agentify.
---

# HMASD Agentify transport

## Purpose

Complete one provider conversation turn with the smallest safe transaction.
The Operator is an adaptive UI worker, not a fixed click script and not a
workflow-repair engineer.

The normative manual is
`C:/Projects/HMASD/docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md`.

## Assignment

The caller supplies:

```text
AGENTIFY_REVIEW_BATCH_ASSIGNMENT
batch_path=<absolute UTF-8 JSON in the caller's closed partition>
results_path=<exact output path in that partition>
```

Read only the named batch, its `context_path`, and its ordered
`question_paths`. Context is local understanding input. Only the exact question
file is provider-visible. The Operator has no scientific, technical, portfolio,
Git, user-contact, or child-spawn authority.

## Safety kernel

These invariants are the hard boundary:

- Use one disposable non-default tab; never mutate the protected default tab.
- Configure visible provider controls before inserting the question.
- Only `agentify_review_query` may cross the exact-one Send boundary.
- Bind the immutable stable key, idempotency key, question SHA, provider,
  conversation relationship, and expected model/mode.
- Derive retry authority from positive commitment, response, and generation
  evidence; a missing local answer archive is never commitment or remote-absence
  proof.
- Never activate Stop, Continue, Retry, Response Retry, Answer now, regenerate,
  or equivalent response controls.
- Archive the mechanical result before closing the inactive disposable tab.

Everything else is implementation choice or diagnostic evidence.

## Normative hot path

1. Validate the frozen files, keys, provider, conversation relationship, SHA,
   result path, and current exact-one ledger facts.
2. Create or reopen one correctly keyed disposable tab at the exact provider
   root or saved conversation URL.
3. Let the page settle. Configure the requested visible model/reasoning state
   with an adaptive `Observe -> Act -> Wait -> Observe` loop.
4. Confirm the final visible selected state: ChatGPT reasoning strength `Pro`,
   or Gemini `3.1 Pro` with `Extended thinking`.
5. Once the composer is ready and the final requested state is visible, call
   strict review immediately with the frozen question and immutable operation
   identity.
6. Observe the same operation to natural completion. Do not accelerate,
   regenerate, duplicate a committed active/unknown turn, or create another
   send route inside this call.
7. Write the canonical result once, run the result-path guard, and close only
   the inactive disposable tab.

## Adaptive visible-control rule

UI configuration is outcome-driven. Use the current visible page and native
Agentify observation/action primitives. After each action, wait for the page or
menu to settle and observe again. Menus may be nested, portaled, delayed,
localized, or reorganized. Explore the visible menu within the no-text,
no-operation, no-Send boundary until either the requested final selected state
is visible or direct evidence establishes a genuine access/credential gate.

Choose controls by visible text, accessible label, current bounds, and the
surrounding opened picker. Mouse and keyboard navigation are both legitimate
when they operate only inside the visible picker. Do not use hidden DOM,
unrelated account-plan text, or Send-family controls.

Intermediate UI trace is diagnostic, not an acceptance gate. A successful
configuration requires the final visible selected state plus the unchanged
safety kernel; it does not require one particular menu hierarchy, ARIA wrapper,
sidecar, preflight sequence, or receipt for every intermediate click.

A missing control in one observation means the page may still be loading.
Wait and re-observe before concluding that the control is absent. Do not blindly
repeat the preceding action.

Pre-send work must remain a short configuration transaction, not an open-ended
diagnostic phase. Distinguish these states:

- Page/composer/menu still changing or hydrating: wait briefly, then observe.
- Page ready and the next visible configuration action is known: act now.
- Final requested state visibly selected: send now.
- Page ready but repeated observations make no progress toward the requested
  state: archive a pre-send incident; do not spend the provider timeout on an
  idle tab.

Do not run a canary, sidecar, helper, duplicate preflight, repeated page-wide
enumeration, or recovery proof before Send. The immutable file/ledger checks,
one adaptive visible configuration loop, and final selected-state observation
are sufficient.

## Strict operation and commitment

Use strict first binding at the provider root for a new conversation and the
saved exact URL/ID for continuation. A click, composer mutation, or client
timeout alone is not proof of provider commitment. Reconcile the strict ledger,
visible user turn, concrete conversation identity, and active generation.

- `SEND_NOT_COMMITTED`: positive evidence proves no user turn, no conversation
  identity, no active generation, and no Send commitment. An exact later retry
  of the frozen prompt is allowed; never retry inside this call.
- `COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN`: a committed turn exists and
  generation is active, a response may exist, or remote state is ambiguous.
  Reconnect/observe; duplicate send is forbidden.
- `COMMITTED_TERMINAL_NO_RESPONSE_PROVED`: direct bound-conversation evidence
  proves generation inactive and no assistant response exists. Return that
  evidence. A separately owner-assigned recovery operation may issue exactly
  one provenance-linked resend of the identical frozen prompt; this call does
  not resend.
- `COMPLETE_RESPONSE_PRESENT`: require the full nonempty response, concrete
  identity, stable completion evidence, and inactive generation; archive and
  do not resend.

Bare absence of a local answer archive proves none of these classes. A recovery
resend records the prior operation identity, frozen-question hash, and its one
recovery-use consumption.

## Incident boundary

Do not repair Agentify, rewrite skills, build helpers, run canaries, or request
an application lifecycle action during a production transport. Archive direct
facts and return `INCIDENT_REPORTED`. A transport incident is not a scientific
failure, direction pause, or user request.

## Result guard and return

Before returning `COMPLETE`, run:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  C:/Projects/HMASD/.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py `
  --repo C:/Projects/HMASD `
  --expected-results-path <assigned-results-path> `
  --returned-results-path <assigned-results-path>
```

Return once:

```text
AGENTIFY_REVIEW_BATCH_RESULT
status=COMPLETE|INCIDENT_REPORTED
results_path=<exact assigned path or empty>
transport_terminal=<mechanical terminal>
error=<empty or exact error>
observed_facts=<direct facts>
actions_taken=<exact actions>
actions_not_taken=<safety-preserving omissions>
remaining_unknown=<none or exact unknown>
provider_lifecycle=<one exact evidence class above>
boundary_domain=<exact local boundary>
affected_scope=<exact operation/turn>
affected_actions=<exact fenced or allowed local actions>
unaffected_scopes=<explicit unaffected owner domains>
continuation_owner=<exact owner or none>
next_event=<exact event or none>
evidence_ref=<exact result/receipt path>
```

The transport return proposes no direction-primary-queue mutation. Only an
exact same-direction EM or Portfolio owner artifact can authorize one.
