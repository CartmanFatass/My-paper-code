# HMASD External Review Workflow

Canonical authority is in `AGENTS.md` and `.agents/roles/`. This file describes
the compact artifact and transport sequence only.

## Research Operations Manager sequence

1. Research Operations Manager follows the active grant or exact clarification
   request and authors the reviewer-visible brief, allow-list and question.
2. Research Operations Manager commits and pushes that exact boundary.
3. In the same task, `$hmasd-review-round` and
   `$browser:control-in-app-browser` reuse the registered Pro conversation and
   submit one freshness-fenced question.
4. The exact natural response is archived, reread for equality, and accompanied
   by a provenance-only intake record. No semantic relay or second reviewer is
   created.
5. Research Operations Manager mechanically records the External-Pro
   disposition and continues the exact in-scope operations sequence.

External Pro owns its exact question-scoped scientific answer. Research
Operations Manager owns packaging, transport, archival and operational use.
Code Project Manager owns implementation and technical acceptance. Review does
not itself authorize code or compute.

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

Research Operations Manager first inspects visible user turns. An exact existing fence is
resumed and never resubmitted. Natural completion requires two stable snapshots
at least three seconds apart, no active generation/stop control, and no current
retry/error/continue control. A stale `Thinking` label is not sufficient to keep
the round pending.

If Pro explicitly reports that question-listed repository evidence was
unavailable, that response is a transport diagnostic, not scientific raw.
Research Operations Manager materializes only the question allow-list from `stage_commit`
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
  50_MECHANICAL_INTAKE_RECORD.md
```

Historical files retain their original authorship markers. New rounds use
Research Operations Manager direct transport. There is no Controller, Exchange
task, dispatcher, separate persistent transport task or completion callback.
