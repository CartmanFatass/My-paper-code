# HMASD External Review Workflow

Canonical authority is in `AGENTS.md` and `.agents/roles/`. This file describes
the compact artifact and transport sequence only.

## Direct Project Manager sequence

1. Project Manager decides whether a question-scoped External Pro judgment is
   useful and authors the reviewer-visible brief, allow-list, and question.
2. Project Manager commits and pushes that exact boundary.
3. In the same Project Manager task, `$hmasd-review-round` and
   `$browser:control-in-app-browser` reuse the registered Pro conversation and
   submit one freshness-fenced question.
4. The exact natural response is archived, reread for equality, and accompanied
   by a provenance-only intake record. No semantic relay or second reviewer is
   created.
5. Project Manager reconciles the raw, updates the smallest implicated research
   unit, and selects the next action inside user authority.

External Pro owns its exact question-scoped scientific answer. Project Manager
owns review need, package semantics, direct transport, archival, reconciliation,
workflow use, implementation, and acceptance. Review does not itself authorize
code or compute.

## Transport identity

The registered conversation lives in `REVIEWER_CONVERSATIONS.json`. Every new
submission carries:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=<round-id>
stage_commit=<40-character pushed SHA>
question=docs/external-review/rounds/<round-id>/20_PRO_OPEN_QUESTION.md
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

Project Manager first inspects visible user turns. An exact existing fence is
resumed and never resubmitted. Natural completion requires two stable snapshots
at least three seconds apart, no active generation/stop control, and no current
retry/error/continue control. A stale `Thinking` label is not sufficient to keep
the round pending.

If Pro explicitly reports that question-listed repository evidence was
unavailable, that response is a transport diagnostic, not scientific raw.
Project Manager materializes only the question allow-list from `stage_commit`
with the deterministic archive builder, attaches it under the same fence, and
archives the subsequent stable answer. No current-worktree or extra evidence is
added.

## Round files

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_PM_CODE_SIDE_RECONCILIATION.md
  50_MECHANICAL_INTAKE_RECORD.md
```

Historical files retain their original authorship markers. New rounds use
Project Manager direct transport. There is no Controller, Exchange task,
dispatcher, cross-task callback, or persistent review session owned by HMASD.
