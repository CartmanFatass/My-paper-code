# HMASD External Review Workflow

External reviewers have different contexts, but no fixed hierarchy of
intellectual authority. Claims are weighted by evidence, reasoning and fit to
the HMASD contract rather than by model identity.

## Roles

1. **Gemini divergent reviewer.** A persistent local Antigravity CLI
   conversation using Gemini 3.1 Pro (High). It reads the shared evidence pack
   plus explicitly allowlisted local papers and may propose, replace or reject
   architecture hypotheses.
2. **GPT-5.6 Pro open reviewer.** A dedicated persistent conversation,
   separate from the convergent reviewer. It receives the shared Git-visible
   evidence pack but not Gemini's response. It performs an independent open
   architecture review and has equal standing with Gemini.
3. **Codex controller.** It compares the two raw reviews, checks them against
   repository evidence and writes a synthesis without selecting by model name.
4. **GPT-5.6 Pro convergent reviewer.** The existing `HMASD Algorithm
   Consultation` role in its own registered persistent conversation. It receives
   the evidence pack, both raw reviews and the Codex synthesis, then ranks and
   stress-tests a portfolio of two to four live candidates and recommends the
   next serialized evidence source or an explicit stop. Only the controller
   adopts or rejects that recommendation.

The two divergent reviews are blind on their first pass. Neither output is an
experiment authorization. The convergent reviewer may add an omitted candidate
only by identifying a concrete omission in the evidence pack. It must not turn
one scheduled experiment into a claim that only one research direction exists.

## Execution default

Communication is automatic once a round exists. Gemini uses one bounded
Antigravity transport subagent against its registered persistent conversation.
The two role-specific Luna Exchange tasks use only the Codex in-app browser to
operate their fixed Pro conversations. Reuse the sessions in
`REVIEWER_CONVERSATIONS.json`; never substitute or mix roles. Submit external
roles serially and archive each completed raw before using it.

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
PTY. Pro routes are sent to the matching Luna Exchange using only `hostId`,
`threadId`, `model`, `thinking`, and `prompt`. The registered target `model` and
`thinking` are mandatory and exact; omission can overwrite the Exchange's
routing with the sender's model. The terminal return likewise includes the
controller's exact registered model and thinking. Both directions are checked
against live task metadata before dispatch; the registry mirrors but never
selects the user-configured controller model. The Exchange uses no Chrome,
Computer Use, external browser, plugin, MCP, heartbeat, automation, shell
sleep, response-control button or replacement conversation. A transport error
is a blocker, not reviewer evidence.

Before Gemini dispatch, verify write access only for its registered conversation
database, `agentapi.bat`, `cache/last_conversations.json`, and the auxiliary
files those stores create atomically. A missing precondition blocks before the
single dispatch; it never authorizes broader `.gemini` access.

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
  30_CONTROLLER_SYNTHESIS.md
  40_PRO_CONVERGENT_QUESTION.md
  41_PRO_CONVERGENT_RAW.md
  50_DISPOSITION.md
```

The brief, manifests and initial review state are written once. Reviewer-specific questions
contain only role and requested-output differences. Raw responses are archived
before synthesis. Accepted algorithm design moves to `docs/research/`; current
ownership stays in `docs/project/CURRENT_WORK.md`; runtime evidence stays in
`logs/`.

`05_REVIEW_STATE.json` is the sole progress authority. Run `show` once on
resume; transition only after a real dispatch, completed artifact or actionable
blocker. A completed raw is immutable and its prompt is never resubmitted.

This workflow supports only the current state schema and transports. Old state
formats, receipts, Exchange tasks and migration paths remain historical
evidence and are never executed or validated by the active workflow.
