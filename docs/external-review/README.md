# HMASD External Review Workflow

Canonical authority is in `AGENTS.md`. This file describes
the compact artifact and transport sequence only.

Browser (claude-in-chrome) transport retired 2026-08-01; the Agentify receipt
transport is the sole backend — see `$hmasd-review-round`; history in Git.

## Direct Project Manager sequence

1. Project Manager decides whether a question-scoped External Pro judgment is
   useful and authors the reviewer-visible brief, allow-list, and question.
2. Project Manager commits and pushes that exact boundary.
3. `$hmasd-review-round` drives the transport through the Agentify Desktop
   local HTTP API: `prepare` freezes one operation, `submit` performs one
   `POST /review-query` against the registered Pro conversation (single send,
   never clicks Continue/Retry/Answer-now) and blocks until the receipt proves
   natural completion with two stable snapshots, `verify` re-validates the
   receipt locally, `archive` writes the response bytes once.
4. The exact natural response is archived, digest-bonded against the receipt's
   SHA-256, and accompanied by a provenance-only intake record. No semantic
   relay or second reviewer is created.
5. Project Manager reconciles the raw, updates the smallest implicated research
   unit, and selects the next action inside user authority.

External Pro owns its exact question-scoped scientific answer. Project Manager
owns review need, package semantics, direct transport, archival, reconciliation,
workflow use, implementation, and acceptance. Review does not itself authorize
code or compute.

## Transport identity

The registered conversation lives in `REVIEWER_CONVERSATIONS.json`, bound to
its Agentify `stable_key`. A reviewer whose `registration_status` is not
`registered` blocks transport; a `retired_registrations` entry is never a
fallback. Every new round's fence operation carries the round's `10_FENCE.txt`
verbatim as the prompt:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=<branch under review; each branch has its own conversation>
round=<round-id>
stage_commit=<40-character pushed SHA>
question=docs/external-review/rounds/<round-id>/20_PRO_OPEN_QUESTION.md
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

One fence operation key exists per round; the Agentify ledger proves whether it
sent, and an accepted fence is never resubmitted. Natural completion is proven
by the receipt: two snapshots at least three seconds apart with the same
assistant message id and text SHA-256, no active stop/retry/continue control,
`sendCount=1`, terminal state `NATURAL_COMPLETION_VERIFIED`.

If Pro explicitly reports that question-listed repository evidence was
unavailable, that response is a transport diagnostic, not scientific raw. The
Project Manager materializes only the question allow-list from `stage_commit`
(`git show <stage_commit>:<path>`), pastes it inline into one continuation
artifact under the same fence, and archives the subsequent receipt-verified
answer. No current-worktree or extra evidence is added; the strict endpoint has
no attachments.

## Round files

```text
rounds/YYYYMMDD_topic/
  10_FENCE.txt
  11_CONTINUATION_<n>.txt          (convergence / recovery turns, if any)
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  22_PRO_CONVERGENCE.md            (if the round converged over turns)
  30_PM_SCIENTIFIC_RECONCILIATION.md
  40_ADJUDICATION_QUESTION.md / 41_ADJUDICATION_RAW.md   (adjudicator only)
  50_MECHANICAL_INTAKE_RECORD.md
```

Runtime transport files (`TRANSPORT_BACKEND.json`, `request.json`,
`receipt.json`) live under `logs/review_transport/<round>/` and are never
committed. Historical files retain their original authorship markers. There is
no Controller, Exchange task, dispatcher, cross-task callback, or persistent
review session owned by HMASD.
