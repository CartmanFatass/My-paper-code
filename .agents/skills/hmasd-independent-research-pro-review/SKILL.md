---
name: hmasd-independent-research-pro-review
description: Use from the persistent Independent Research Explorer to send exact Pro or Gemini direction or methodology review questions through the registered Agentify transport child.
---

# HMASD Independent Research External Review

## Boundary

This Skill is invoked only by the persistent `INDEPENDENT_RESEARCH_EXPLORER`.
The Explorer owns both independent-research direction reviews and methodology
audits; there is no separate persistent review-operator session.

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
   `IR_DIRECTION_REVIEW:` or `IR_METHODOLOGY_REVIEW:` and declares either
   `PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW`,
   `PRO_ADVERSARIAL_SCIENTIFIC_REVIEW`, or the bounded methodology-audit mode.
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
   `results_path` and dispatch
   one self-contained `AGENTIFY_REVIEW_BATCH_ASSIGNMENT` to the registered
   `hmasd-agentify-transport` child with `fork_turns=none`, naming only
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
4. Copy each named successful raw response and returned conversation URL into
   `local_research/pro_reviews/<review-id>/`, then reconcile it scientifically.
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

## Item records and packet semantics

Each item keeps the frozen question, raw response and typed advisory packet
required by its mode. Keep runtime credentials outside the repository.

For a direction review, archive the complete response before producing the
`INDEPENDENT_RESEARCH_DIRECTION_PACKET`. A constructive review must complete
before the Explorer applies, rejects or parks its corrections in a new
advisory version; only that version may receive a separate adversarial review.
For a methodology audit, return the exact format-complete methodology packet
to the Explorer's local FIFO without adding sources, claims or project
instructions. Neither mode promotes a direction into formal project state.

The Explorer alone selects the next review and continues the authorized
campaign. Workflow Design Manager is not a campaign approver or transport
operator. Research children remain available for source, innovation, principles
and critique work. The registered transport child performs no research judgment.
