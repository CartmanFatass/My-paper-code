# HMASD External Review Workflow

External reviewers have different contexts. Gemini and open Pro are equal blind
divergent sources; convergent Pro is the designated scientific decision source
after both raws and a factual Codex evidence reconciliation exist.

## Roles

1. **Gemini divergent reviewer.** A persistent local Antigravity CLI
   conversation using Gemini 3.1 Pro (High). It reads the shared evidence pack
   plus explicitly allowlisted local papers and may propose, replace or reject
   architecture hypotheses.
2. **GPT-5.6 Pro open reviewer.** A dedicated persistent Pro conversation,
   separate from the convergent Pro conversation. It receives the shared Git-visible
   evidence pack but not Gemini's response. It performs an independent open
   architecture review and has equal standing with Gemini.
3. **Codex evidence controller.** It compares the two raw reviews against
   repository evidence and writes a factual reconciliation of supported claims,
   contradictions and missing inputs. It does not rank routes or choose the
   next evidence source.
4. **GPT-5.6 Pro convergent reviewer.** The existing `HMASD Algorithm
   Consultation` role in its own registered persistent Pro conversation. It
   receives the evidence pack, both raw reviews and the Codex reconciliation,
   then owns scientific synthesis, portfolio weighting, and the next serialized
   evidence source or explicit stop.

The two divergent reviews are blind on their first pass. No review output is an
experiment authorization. Codex operationalizes the convergent decision unless
it conflicts with registered evidence, an explicit user/project constraint, or
operational feasibility; it does not replace it with local research judgment.
The convergent reviewer may add an omitted candidate
only by identifying a concrete omission in the evidence pack. It must not turn
one scheduled experiment into a claim that only one research direction exists.

## Execution default

Communication is automatic once a round exists. Gemini uses one bounded
Antigravity transport subagent against its registered persistent conversation.
One persistent Luna Exchange task uses only the Codex in-app browser and
switches between the two fixed role-specific Pro pages. Reuse the task and the
two Pro conversations in `REVIEWER_CONVERSATIONS.json`; never create a second
Exchange, substitute a page, or mix roles. Submit external roles serially and
archive each completed raw before using it.

Before a Pro submission, verify one remote-reachable 40-character commit, its
question and every `Repository files to inspect` path with
`verify_pro_review_boundary.ps1`. Then use the registered URL, require visible
`Pro`, submit once, and read the same response until natural completion:

```text
verify remote evidence boundary
-> open the registered Pro conversation
-> submit the neutral handoff once
-> bounded same-thread wait/read
-> exact raw archive
```

Gemini receives one single-line document pointer in its interactive Antigravity
PTY. Every controller-to-Exchange and Exchange-to-controller Codex task message
uses `$hmasd-task-router`; ad hoc sends are forbidden. That Skill resolves both
endpoints from live task metadata and supplies the exact five-field route. The
registry mirrors but never selects user-configured models. The Exchange uses no
Chrome, Computer Use, external browser, plugin, MCP, heartbeat, automation,
shell sleep, response-control button or replacement conversation. A transport
error is a blocker, not reviewer evidence.

Before Gemini dispatch, verify write access only for its registered conversation
database, `bin/agentapi.bat`, `cache/last_conversations.json`, Antigravity's own
`log/` and `crashes/` runtime-output directories, and the auxiliary files those
stores require. These are transport-state writes, not evidence-read scope. A
missing precondition blocks before the single dispatch; it never authorizes
broader `.gemini` access.

## Round ownership

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

The brief, manifests and initial review state are written once. Reviewer-specific questions
contain only role and requested-output differences. Raw responses are archived
before reconciliation. Accepted algorithm design moves to `docs/research/`; current
ownership stays in `docs/project/CURRENT_WORK.md`; runtime evidence stays in
`logs/`.

`05_REVIEW_STATE.json` is the sole progress authority. Run `show` once on
resume; transition only after a real dispatch, completed artifact or actionable
blocker. A completed raw is immutable and its prompt is never resubmitted.

This workflow supports only the current state schema and transports. Old state
formats, receipts, Exchange tasks and migration paths remain historical
evidence and are never executed or validated by the active workflow.
