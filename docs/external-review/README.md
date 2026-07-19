# HMASD External Review Workflow

External review is a mandatory scientific boundary. One persistent Codex
`External Review Manager` owns mechanical sequencing, Git-boundary requests,
reconciliation, and disposition. The controller alone owns commit and push.
Three additional persistent exchange sessions
are each bound to exactly one reviewer: Gemini divergent, Open-Pro divergent,
or Convergent Pro. Each exchange alone owns its reviewer transport, raw capture,
and heartbeat, so neither the controller nor manager carries browser or CLI
state.

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

The commit pins reviewer-visible scientific evidence. The manager writes later
active-round question, reconciliation, and disposition files, while each raw
has exactly one writer: its registered reviewer exchange. When those files need
a reviewer-visible boundary, the manager sends `REVIEW_GIT_PUSH_REQUIRED` with
the exact paths; the controller alone inspects, commits, pushes, and resends
`START_REVIEW` with the new commit. This is a stateless Git handoff, not a review
state machine. The controller never contacts a reviewer exchange directly. A
raw artifact becomes immutable only after its
exchange verifies natural response completion, all question-required fields,
and exact captured-text equality after rereading the file; nonempty alone is not
completion. An externally accepted stage is never resubmitted.

The manager may return this mechanical boundary request before completion:

```text
REVIEW_GIT_PUSH_REQUIRED role=external_review_manager handoff_id=<stable-id> round=<round-id> paths=<exact-paths> next=<next-stage>
```

It ultimately returns exactly one terminal message:

```text
REVIEW_COMPLETE role=external_review_manager handoff_id=<stable-id> round=<round-id> disposition=<path> commit=<sha>
```

or:

```text
REVIEW_BLOCKED role=external_review_manager handoff_id=<stable-id> round=<round-id> reason=<exact blocker>
```

The controller does not operate reviewer transports or intermediate review
progress. Its only scientific input is the completed disposition. Manager and
exchange lifecycle mechanics remain isolated in their respective Skills.

The manager has no heartbeat. It wakes only for controller or reviewer-exchange
messages, performs one bounded transition, sends the next message, and ends.
Each reviewer exchange independently owns a 5-minute heartbeat only while its
external response or callback is pending.

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
exchange behavior lives only in
`.agents/skills/hmasd-review-exchange/SKILL.md`. Codex task IDs and role bindings
live only in the router's `session-roles.json`; external reviewer conversations
and URLs live only in `REVIEWER_CONVERSATIONS.json`.
