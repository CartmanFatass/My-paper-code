# HMASD External Review Workflow

External review is a mandatory scientific boundary. The active controller owns
round sequencing, factual reconciliation, disposition, and every Git-visible
boundary. Three persistent Exchange sessions are each bound to exactly one
reviewer: Gemini divergent, Open-Pro divergent, or Convergent Pro. Each Exchange
alone owns its reviewer transport, raw capture, validation, and heartbeat, so
the controller carries no browser or Antigravity state.

## Scientific sequence

1. Gemini 3.1 Pro (High) performs a blind divergent review with the shared
   evidence, allowlisted local sources, and `OPEN_REVIEW_PRINCIPLES.md`.
2. GPT-5.6 Pro performs an independent blind divergent review from the same
   Git-visible evidence under the same open-review principles.
3. The controller writes a factual reconciliation without selecting a route.
4. A separate GPT-5.6 Pro conversation performs convergent synthesis and
   follows `CONVERGENT_REVIEW_PRINCIPLES.md`, then chooses the next evidence
   source or stop while preserving valuable unselected ideas.
5. The controller writes `50_DISPOSITION.md` from that convergent decision and
   updates the project boundary once.

The controller may not replace a missing external decision with its own
scientific choice. External review does not authorize code execution or
training.

`docs/project/ALGORITHM_PRINCIPLES.md` is the common scientific contract.
`OPEN_REVIEW_PRINCIPLES.md` and `CONVERGENT_REVIEW_PRINCIPLES.md` specialize
the two reviewer modes. Every new question lists the base file and exactly one
matching role file; historical rounds are not rewritten.

## Direct Exchange interface

The controller prepares and pushes each immutable reviewer-visible boundary,
then resolves and sends one compact stage assignment directly to the registered
Exchange session:

```text
REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=<GEMINI_DIVERGENT|OPEN_DIVERGENT|CONVERGENT>
round=<round-id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<round-id>
question=<round-relative question path>
raw=<round-relative raw path>
```

Gemini and Open Pro may run concurrently. Their Exchange sessions return
`REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED` directly to the controller
through the task router. After both divergent raws are verified, the controller
writes and pushes reconciliation plus the convergent question before dispatching
the convergent Exchange.

Each raw has exactly one writer: its registered Exchange. A raw becomes
immutable only after that Exchange verifies natural response completion, every
question-required field, and exact captured-text equality after rereading the
file; nonempty alone is not completion. An externally accepted stage is never
resubmitted.

The workflow uses no intermediate persistent session, Git handoff callback, or
review state file. The controller has no review heartbeat. Each Exchange
independently owns one 5-minute heartbeat only while its external response or
direct callback is pending, and deletes it after callback delivery is
confirmed.

## Round files

New multi-review work lives under one round directory:

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  02_GEMINI_LOCAL_SOURCE_MANIFEST.md
  10_GEMINI_DIVERGENT_QUESTION.md
  11_GEMINI_DIVERGENT_RAW.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_EVIDENCE_RECONCILIATION.md
  40_PRO_CONVERGENT_QUESTION.md
  41_PRO_CONVERGENT_RAW.md
  50_DISPOSITION.md
```

Raw responses are byte-preserved and precede downstream use. Controller round
behavior lives in `.agents/skills/hmasd-review-round/SKILL.md`; registered
Exchange behavior lives in `.agents/skills/hmasd-review-exchange/SKILL.md`.
Codex task IDs and role bindings live only in the router's
`session-roles.json`; external reviewer conversations and URLs live only in
`REVIEWER_CONVERSATIONS.json`.
