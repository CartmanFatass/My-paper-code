---
name: hmasd-independent-research-pro-review
description: Use from the task-scoped Root-owned Independent Research Explorer L1 to send one exact ChatGPT External Pro direction, methodology, result-convergence, or authoritative mathematical-closure review through the registered Explorer Agentify transport leaf. External Gemini uses the separate hmasd-external-gemini skill and never satisfies this Pro review.
---

# HMASD Independent Research External Review

## Boundary

This Skill is invoked only by the task-scoped Root-owned
`INDEPENDENT_RESEARCH_EXPLORER` L1. The Explorer owns both independent-research
direction reviews and methodology audits; the Skill is non-spawnable and there
is no separate review-operator task or manager-session continuity.

This Skill grants no workflow-design, code, runtime, compute, Git, result-
interpretation, technical-acceptance, production, or project-state authority.
Most responses are advisory input to the Explorer. One explicit exception is an
owner-frozen pure-theory or science-definition request whose declared mode is
`PRO_MATHEMATICAL_CLOSURE_REVIEW`: for that exact revision, Pro owns the final
mathematical/causal disposition `CLOSED|REVISION_REQUIRED`. The Explorer freezes
the exact question, mode, candidate or methodology assignment, source
allow-list and item root before sending.

For every eligible active algorithm direction, this dedicated ChatGPT External
Pro review exists beside a separate default External Gemini innovator request.
Use Pro for rigorous causal/mathematical scrutiny, matched-control and shortcut
adequacy, claim boundaries, adversarial result challenge, and convergence. Use
the separate Gemini route only for broad world/domain-informed divergent
mechanisms, analogies, regimes, counterexamples, scenarios, controls, and
toy-to-UAV bridges. Freeze them independently from the same direction state;
neither provider sees the other's current answer by default. Gemini never
counts as or replaces this Pro conversation.

For mathematical closure, do not require a local Principles Analyst or Research
Critic packet. They are optional context only when EM judges them useful. A Pro
`CLOSED` ruling plus same-direction EM intake completes the mathematical-review
boundary for the named complete revision. A `REVISION_REQUIRED` ruling returns
the exact defect and claim ceiling to EM; any accepted science-bearing repair
must be frozen as a new complete composite and reviewed again in the same Pro
conversation. Pro closure never authors the scientific object, accepts code or
runtime, authorizes production, interprets results for EM, or selects the
portfolio.

For the exact closure question and response headings, read
`references/22_MATHEMATICAL_CLOSURE_REVIEW.md`.

## Review request

1. Freeze one concise local execution plan and one standalone UTF-8
   `RAW_QUESTION`. The question contains only natural-language scientific
   content; assignment, authority, session, Git/path, provider and transport
   fields remain local. The local assignment identity begins with exactly
   `IR_DIRECTION_REVIEW:`, `IR_METHODOLOGY_REVIEW:`, or
   `EXPLORER_PROJECT_ALIGNMENT_AUDIT:` and declares either
   `PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW`,
   `PRO_ADVERSARIAL_SCIENTIFIC_REVIEW`,
   `PRO_MATHEMATICAL_CLOSURE_REVIEW`, the bounded methodology-audit mode, or the
   project-alignment mode defined below. A closure question names the exact
   complete owner-frozen revision, asks for the literal decision
   `CLOSED|REVISION_REQUIRED`, requests exact mathematical/causal defects and
   the maximum defensible claim, and excludes code, tests, runtime, receipts,
   provider mechanics, and portfolio selection.
   Before dispatch, write one self-contained natural-language context brief
   that states for each question whether it starts clean, continues an
   exact prior conversation URL, may run concurrently with named other
   questions, or must remain independent. Explorer alone decides whether prior
   memory helps or contaminates the requested judgment and whether a returned
   conversation will be reused. This is semantic task meaning, not a
   `conversation_mode`, grouping field or other schema.
2. Write one minimal JSON batch retaining the existing
   `provider|context_path|question_paths` contract for all currently eligible
   frozen ChatGPT Pro questions and set `provider` to `chatgpt`. The existing
   `context_path` anchor points to the local
   brief for transport realization; it adds no mandatory field, and transport
   does not include the local brief in provider payload. Choose one exact
   `results_path` under
   `temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/`
   and dispatch one self-contained `AGENTIFY_REVIEW_BATCH_ASSIGNMENT` to the
   registered `hmasd-explorer-agentify-transport` child with `fork_turns=1`, naming only
   `batch_path|results_path`. Confirm once that the raw question contains no
   local filesystem path, task history or unrelated corpus; use a public remote
   GitHub URL for a reviewer-facing source locator. Do not send a review whose
   owner-frozen scientific object is incomplete. Mathematical closure has no
   local Principles/Critic prerequisite.
3. Continue unrelated research. Agentify transport exclusively performs page,
   model, send, wait, recovery and tab-cleanup mechanics. It may use
   operational judgment to realize the frozen brief but cannot infer
   same-direction grouping, scientific relationship, independence or future
   reuse. The child is silent while live and returns exactly once through the
   canonical `AGENTIFY_REVIEW_BATCH_RESULT` with
   `status=COMPLETE|INCIDENT_REPORTED`, the exact assigned `results_path` only on
   complete validation, and the mechanical `transport_terminal`. Read the named
   result only after a `COMPLETE` final return. Before reading it,
   invoke `.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py`
   with the repository, the assignment's expected `results_path` and the
   returned terminal anchor. Reject any mismatch, redirect, root-level generic
   path or missing/non-regular file; do not infer a fallback path. Explorer
   performs no polling, progress handling or parent-task result relay.
4. Dispatch the Research Artifact Writer to copy each named successful raw
   response and returned conversation URL as exact bytes into
   `local_research/pro_reviews/<review-id>/`; the Writer cannot write
   `local_research/RESEARCH_CONTINUITY.md`. Then reconcile the archived response
   scientifically.
   Explorer names an exact archived URL in a later brief when it chooses
   continuation; if no continuation is stated, the child must not guess from
   titles. An `INCIDENT_REPORTED` return affects only that transport assignment,
   supplies no scientific evidence and cannot pause the direction. A later send
   is an EM-owned prospective decision: it is allowed only when the prior record
   proves no provider turn, no conversation identity and no active generation,
   and it uses a new idempotency key. Never infer resend permission from
   `ERROR`, a terminal label, a reused batch path or an attempt count.

When a Pro protocol includes a follow-up, freeze it as a second standalone
natural-language question only after its prerequisite review is reconciled.
Continue the exact direction Pro conversation only when the context brief names
its archived URL; otherwise start clean. The independent Gemini request and any
Gemini follow-up use `.agents/skills/hmasd-external-gemini/SKILL.md`, a separate
requester partition, and a separate conversation. A shared Agentify capacity may
serialize the two providers but never merges their scientific identities.

A mathematical-closure follow-up always continues the saved direction Pro
conversation when one exists. If transport cannot establish that exact
conversation and visible Pro before send, return an unsent error and never open
a substitute. If closure is the direction's first Pro request, start exactly one
clean direction conversation and retain it for every corrected-composite ruling
and later result convergence.

An incomplete call affects only that review and is not scientific evidence.

## Project-alignment branch

`EXPLORER_PROJECT_ALIGNMENT_AUDIT` is a third, separate review branch. It does
not rename, continue, or borrow the local/raw archival mechanics of
`IR_DIRECTION_REVIEW` or `IR_METHODOLOGY_REVIEW`; those two remain independent
branches with their existing local source and archival rules.

EM selects the project-alignment question and retains its scientific intake. A
named scientific trigger or optional `OVERNIGHT_BRANCH_BLOCKER_REVIEW` may
justify this branch. Ordinary B does not create a mandatory review gate, and
engineering recovery need not be declared exhausted before EM asks one exact
scientific question.

When the provider must inspect repository-visible artifacts, Root publishes the
owner-accepted exact path set by an ordinary non-force push and the review brief
supplies the GitHub-readable remote, branch, exact pushed **aggressive**
revision, and repository-relative paths. A self-contained science-only question
that does not require repository inspection may proceed without publication.
Publication never gates local EM intake or direction continuation.

The Explorer uses only its parent-specific registered Pro transport to send the
frozen alignment question. Return the complete raw response immediately to the
same-direction EM for scientific intake after canonical transport validation.
Root may later commit and publish the owner-accepted archive as non-gating audit
work. The external side effect and its archive are evidence, never a permission,
token, queue, ledger, gate, state machine, or transfer of owner authority.

Neither Pro nor Root authors EM science, intakes CM's technical result, accepts
CM code, or performs Operator mechanics. Pro supplies a disposition or advisory
answer and never commands continue, revise, pause or stop. A user decision
pauses only the exact external action requiring that authority. The result
returns to EM for its own
direction-local scientific reconciliation and does not make a project,
technical, or formal acceptance claim.

## Item records and packet semantics

Each item keeps the frozen question, raw response and typed advisory packet
required by its mode. Keep runtime credentials outside the repository.

For `PRO_MATHEMATICAL_CLOSURE_REVIEW`, archive the complete response and retain
the exact revision plus literal `CLOSED|REVISION_REQUIRED` disposition. Treat an
ambiguous, partial, interrupted, or transport-only answer as no closure. EM
intakes the ruling and either preserves the closed object or freezes a corrected
complete composite for the same conversation. The ruling is authoritative only
for mathematical/causal closure of that exact revision; every other scientific,
technical, runtime, portfolio, and production boundary remains with its named
local owner.

For a direction review, preserve the complete response in the canonical
transport result before producing the `INDEPENDENT_RESEARCH_DIRECTION_PACKET`.
A constructive review must complete before the Explorer applies or rejects its
corrections in a new advisory version; only that version may receive a separate
adversarial review. Later repository archival is non-gating audit work.
For a methodology audit, return the exact format-complete methodology packet
to the Explorer's local FIFO without adding sources, claims or project
instructions. Neither mode promotes a direction into formal project state. For
the project-alignment branch, EM reconciles the returned scientific answer
without waiting for later Root-owned archival or publication.

The Explorer alone selects the next Pro review and continues the authorized
campaign. Research children remain available for optional source, innovation,
principles and critique work; none is required to co-sign mathematical closure.
The registered Pro transport child performs no research
judgment, and the separate Gemini transport supplies no convergence or
acceptance authority.
