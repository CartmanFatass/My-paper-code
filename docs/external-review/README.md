# HMASD External Review Workflow

External review is a mandatory scientific boundary. One persistent Codex
`External Review Manager` owns the complete mechanical lifecycle so the active
controller does not carry browser, CLI, heartbeat, or archival context.

## Scientific sequence

1. Gemini 3.1 Pro (High) performs a blind divergent review with the shared
   evidence and allowlisted local sources.
2. GPT-5.6 Pro performs an independent blind divergent review from the same
   Git-visible evidence.
3. The Review Manager writes a factual reconciliation without selecting a
   route.
4. A separate GPT-5.6 Pro conversation performs convergent synthesis and
   chooses the next evidence source or stop.
5. The Review Manager writes `50_DISPOSITION.md` from that convergent decision.

The controller may not replace a missing external decision with its own
scientific choice. External review does not authorize code execution or
training.

## Controller interface

The controller prepares and pushes one immutable round boundary, then sends one
compact assignment through the communication Skill:

```text
START_REVIEW role_skill=.agents/skills/hmasd-review-round/SKILL.md round=<round-id> evidence_commit=<40-char-sha> round_path=docs/external-review/rounds/<round-id>
```

The commit pins reviewer-visible scientific evidence. The manager owns all
later active-round question/raw/reconciliation/disposition commits and pushes;
the controller does not perform intermediate handshakes. Completed nonempty raw
artifacts are immutable, and an externally accepted stage is never resubmitted.

The manager returns exactly one terminal message:

```text
REVIEW_COMPLETE role=external_review_manager handoff_id=<stable-id> round=<round-id> disposition=<path> commit=<sha>
```

or:

```text
REVIEW_BLOCKED role=external_review_manager handoff_id=<stable-id> round=<round-id> reason=<exact blocker>
```

The controller does not operate reviewer transports or intermediate review
progress. Its only scientific input is the completed disposition. All session
lifecycle mechanics live only in the manager Skill.

A terminal callback exists only after the manager invokes the common
communication Skill and receives a tool result identifying the controller task.
Text written only in the manager task is not delivery.

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

Raw responses are byte-preserved and precede downstream use. Detailed manager
behavior lives only in `.agents/skills/hmasd-review-round/SKILL.md`; registered
task IDs, reviewer conversations, roles, and URLs live only in
`REVIEWER_CONVERSATIONS.json`.
