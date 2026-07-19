# HMASD External Review Workflow

External review is a mandatory scientific boundary. One persistent Codex
`External Review Manager` owns the complete mechanical lifecycle so the active
controller does not carry browser, CLI, heartbeat, state-machine, or archival
context.

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

The controller prepares and pushes one immutable round boundary, then sends:

```text
START_REVIEW round=<round-id> commit=<40-char-sha> state=<state-path>
```

The commit pins reviewer-visible scientific evidence, not the operating
workflow. The manager always reads its Skills, registry, and state script from
the current working tree. If an undispatched stage was blocked by an operational
condition that is now resolved, the controller sends:

```text
RESUME_REVIEW round=<round-id> evidence_commit=<40-char-sha> state=<state-path> resolved_blocker=<exact recorded blocker>
```

Completed stages are not repeated, and an externally accepted stage is never
resubmitted.

The manager returns exactly one terminal message:

```text
REVIEW_COMPLETE round=<round-id> disposition=<path>
```

or:

```text
REVIEW_BLOCKED round=<round-id> reason=<exact blocker>
```

The controller does not operate reviewer transports, create intermediate Git
boundaries, or consume intermediate review progress. The manager may commit and
push only its active round directory. The controller's only scientific input is
the completed disposition.

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
  05_REVIEW_STATE.json
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
