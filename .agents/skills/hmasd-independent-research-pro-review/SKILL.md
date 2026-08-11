---
name: hmasd-independent-research-pro-review
description: Use from the task-scoped Root-owned Independent Research Explorer L1 to send exact Pro or Gemini direction or methodology review questions through the registered Explorer Agentify transport leaf.
---

# HMASD Independent Research External Review

## Boundary

This Skill is invoked only by the task-scoped Root-owned
`INDEPENDENT_RESEARCH_EXPLORER` L1. The Explorer owns both independent-research
direction reviews and methodology audits; the Skill is non-spawnable and there
is no separate review-operator task or manager-session continuity.

This Skill grants no workflow-design, code, runtime, compute, Git, formal
science or project-state authority. The response is advisory input to the
Explorer's local research portfolio only. The Explorer freezes the exact
question, mode, candidate or methodology assignment, source allow-list and item
root before sending.

## Review request

1. Freeze one concise local execution plan and one standalone UTF-8
   `RAW_QUESTION`. The question contains only natural-language scientific
   content; assignment, authority, session, Git/path, provider and transport
   fields remain local. The local assignment identity begins with exactly
   `IR_DIRECTION_REVIEW:`, `IR_METHODOLOGY_REVIEW:`, or
   `EXPLORER_PROJECT_ALIGNMENT_AUDIT:` and declares either
   `PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW`,
   `PRO_ADVERSARIAL_SCIENTIFIC_REVIEW`, the bounded methodology-audit mode, or
   the project-alignment mode defined below.
   Before dispatch, write one self-contained natural-language context brief
   that states for each question whether it starts clean, continues an
   exact prior conversation URL, may run concurrently with named other
   questions, or must remain independent. Explorer alone decides whether prior
   memory helps or contaminates the requested judgment and whether a returned
   conversation will be reused. This is semantic task meaning, not a
   `conversation_mode`, grouping field or other schema.
2. Write one minimal JSON batch retaining the existing
   `provider|context_path|question_paths` contract for all currently eligible
   frozen questions. The existing `context_path` anchor points to the local
   brief for transport realization; it adds no mandatory field, and transport
   does not include the local brief in provider payload. Choose one exact
   `results_path` under
   `temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/`
   and dispatch one self-contained `AGENTIFY_REVIEW_BATCH_ASSIGNMENT` to the
   registered `hmasd-explorer-agentify-transport` child with `fork_turns=1`, naming only
   `batch_path|results_path`. Confirm once that the raw question contains no
   local filesystem path, task history or unrelated corpus; use a public remote
   GitHub URL for a reviewer-facing source locator. Do not send a review whose
   scientific barrier has not yet completed.
3. Continue unrelated research. Agentify transport exclusively performs page,
   model, send, wait, recovery and tab-cleanup mechanics. It may use
   operational judgment to realize the frozen brief but cannot infer
   same-direction grouping, scientific relationship, independence or future
   reuse. The child is silent while live and returns exactly once through its
   native final response with one `AGENTIFY_REVIEW_BATCH_RESULT` carrying
   `status|results_path|error` and terminal status `COMPLETE|ERROR`. Read the
   named result only after that terminal final return. Before reading it,
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
   titles. An item `ERROR` affects only that review. Retrying transport reuses
   the same batch file and requires no Explorer file change.

When one paired protocol includes a common follow-up, freeze that follow-up as
a second standalone natural-language question only after its prerequisite
review is reconciled. Send it later for each provider only when the context
brief explicitly chooses continuation and names the exact archived conversation
URL; otherwise start clean. This does not create a second workflow or permit
provider-specific prompt metadata.

An incomplete call affects only that review and is not scientific evidence.

## Project-alignment branch

`EXPLORER_PROJECT_ALIGNMENT_AUDIT` is a third, separate review branch. It does
not rename, continue, or borrow the local/raw archival mechanics of
`IR_DIRECTION_REVIEW` or `IR_METHODOLOGY_REVIEW`; those two remain independent
branches with their existing local source and archival rules.

EM selects the project-alignment question and retains its scientific intake. It
may use this branch only after a named project-alignment trigger, or after an
`OVERNIGHT_BRANCH_BLOCKER_REVIEW` trigger has been confirmed. Ordinary B never
creates this trigger. The overnight trigger is available only after applicable
in-scope recovery and legal owner relay are exhausted on the same overnight
project branch.

Before dispatch, Root must have completed `publication`: an owner-accepted exact
path set has been ordinarily, non-force pushed to the configured upstream. The
review brief supplies GitHub-readable remote,
branch, exact pushed **aggressive** revision, and repository-relative paths.
A local-only archive, unpushed revision, or filesystem-only locator is not a
project-alignment input. External Pro uses its connector to inspect precisely
that remote revision and paths.

The Explorer uses only its parent-specific registered transport to send the
frozen alignment question. Root manages the complete raw-response archive. Once
the owner accepts its exact archive path, Root performs the local commit and
ordinary non-force push of that archive before Root returns it to the original
same-direction EM. The external side effect and its archive are evidence, never
a permission, token, queue, ledger, gate, state machine, or transfer of owner
authority.

Neither Pro nor Root authors EM science, intakes CM's technical result, accepts
CM code, or performs Operator mechanics. Within an already authorized overnight
boundary, a legal owner may continue, revise, or stop; `user decision required`
pauses only this review branch. The result returns to EM for its own
direction-local scientific reconciliation and does not make a project,
technical, or formal acceptance claim.

## Item records and packet semantics

Each item keeps the frozen question, raw response and typed advisory packet
required by its mode. Keep runtime credentials outside the repository.

For a direction review, archive the complete response before producing the
`INDEPENDENT_RESEARCH_DIRECTION_PACKET`. A constructive review must complete
before the Explorer applies, rejects or parks its corrections in a new
advisory version; only that version may receive a separate adversarial review.
For a methodology audit, return the exact format-complete methodology packet
to the Explorer's local FIFO without adding sources, claims or project
instructions. Neither mode promotes a direction into formal project state. For
the project-alignment branch, Root-owned archival and publication occur as
described above; EM alone reconciles the returned scientific answer.

The Explorer alone selects the next review and continues the authorized
campaign. Research children remain available for source, innovation, principles
and critique work. The registered transport child performs no research judgment.
