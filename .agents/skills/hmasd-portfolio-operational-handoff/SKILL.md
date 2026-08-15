---
name: hmasd-portfolio-operational-handoff
description: Keep HMASD direction stages, operational Root, and the dedicated portfolio session reconciled. Use when a direction EM/CM completes or changes a stage, when a direction needs Root authority, when Root receives a portfolio decision, or when stale pending/released state could misrepresent current work.
---

# HMASD portfolio–operational handoff

Use one durable anchor:

`docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md`

Root owns its pair/stage/lease/reporting columns. The dedicated portfolio owner
owns portfolio allocation and its canonical decision records. Do not duplicate
the anchor or use an owner log, a sibling message, or a runtime stream as a
substitute for it.

## Direction-to-Root closure

Every EM or CM must send Root a direct compact milestone when its current stage
reaches technical acceptance, scientific intake/convergence, a completed
result, a science-bearing ambiguity, a lease/authority need, or a genuine
cross-scope conflict. A same-direction sibling receipt is insufficient.

Use this shape:

```text
DIRECTION_TO_ROOT_MILESTONE
direction_id=<exact direction>
stage_objective=<completed or changed stage>
conclusion=<direction-local conclusion>
key_observation=<decision-relevant fact>
strongest_alternative=<live alternative>
claim_ceiling=<exact boundary>
portfolio_effect=<none or exact question>
next_discriminator=<if any>
root_action_requested=<exact action or none>
applies_to=<exact object of any limitation, if present>
does_not_imply=<direction/portfolio actions that remain live>
continuation_owner=<owner and next authorized work>
root_decision_class=<none|recovery|lease/resource|science change|portfolio>
```

For an ordinary non-core workflow anomaly, use
`hmasd-workflow-anomaly-routing` instead. Never use `pending`, `done`, or a
sibling-only message as a completion protocol.

The fields above are a semantic alignment check, not a status taxonomy. An
operation-level no-resend, unknown observation, lease pause, or recovery
boundary must stay attached to its exact object. Root must not record it as a
direction pause or portfolio gate unless an authorized owner explicitly made
that broader decision.

## Root closure and stable anchor

When the milestone arrives, Root must first report the conclusion to the main
session, then update the anchor's exact direction row in the same active turn.
The row states the factual completed object, the next exact stage or released
pair, and lease/activity facts. It must not leave a completed stage described
as awaiting/reviewing/pending. Root keeps an event wait active while any
direction owner is working, so this closure occurs on the owner event rather
than a later heartbeat.

For every row that records a restriction, write both sides: `local fence` and
`direction continuation`. Example: “old provider operation no-resend;
recovery/EM continues the current frozen direction.” Never let a child-local
prohibition silently replace the portfolio allocation or stage envelope.

If the milestone changes allocation, competition, claim ceiling, successor, or
prospective cost, Root sends the dedicated portfolio thread one packet:

```text
ROOT_TO_PORTFOLIO
bounded_objective=<...>
conclusion=<...>
key_observation=<...>
strongest_alternative=<...>
claim_ceiling=<...>
possible_portfolio_effect=<...>
next_discriminator=<...>
exact_decision_requested=<...>
```

Do not send runtime, PID, tab, hash, receipt, or partial-result streams. A
portfolio return is recorded in the anchor before Root opens/reuses the next
pair or lease.

### Direct-thread delivery and recovery

Treat `codex_app__send_message_to_thread` as asynchronous transport, not as a
complete delivery receipt. Never infer either delivery or failure from one
caller timeout/absent return.

For every new `ROOT_TO_PORTFOLIO` packet:

1. Give the packet a stable unique marker and first read the target thread's
   latest compact turns. If that exact marker is already visible, do not send a
   duplicate; record `DELIVERED_VISIBLE_TARGET`.
2. If absent, submit one exact packet. Allow a bounded transport wait (up to
   60 seconds) for its return; a non-return is `SUBMISSION_UNCERTAIN`, not a
   decision or a failed relay.
3. Re-read the target thread after submission. If the marker is visible,
   record `DELIVERED_VISIBLE_TARGET`; this proves queue visibility only, not
   portfolio processing or agreement.
4. If still absent, retry the same exact packet only after that negative
   target-side read. Keep the same marker, preserve a compact provenance note,
   and use later heartbeat turns for additional bounded reconciliation rather
   than a long Root wait loop.
5. Mark `ACKNOWLEDGED_BY_PORTFOLIO` only when the target produces an explicit
   response or durable target-side acknowledgment. Then record the portfolio
   decision separately; do not equate delivery with a decision.

The durable anchor records the precise transport fact:
`SUBMISSION_UNCERTAIN`, `DELIVERED_VISIBLE_TARGET`, or
`ACKNOWLEDGED_BY_PORTFOLIO`. None of these states reopens, pauses, or changes
the completed scientific direction.

## Direction request to Root

When a direction needs a new stage, a compute lease, a new provider
conversation, an external authority expansion, or a science-bearing change,
send Root directly:

```text
DIRECTION_TO_ROOT_REQUEST
direction_id=<...>
exact_object=<...>
why_current_envelope_is_insufficient=<...>
requested_root_action=<...>
science_impact=<...>
live_semantics_preserving_options=<...>
```

Root records the request and response in the direction row; it does not infer
deferral from the absence of a new pair. A portfolio decision is required only
for a cross-direction allocation change, never for routine in-envelope work.

## Portfolio-to-Root application

On an owner decision, Root reads the controlling portfolio record, applies only
the named pair/stage/lease actions, and sends a compact applied-envelope
acknowledgment. Update the anchor so it identifies the controlling record, the
active pairs, released pairs, and the next decision-level event. Do not create
an action from evidence-only maps or historical records.
