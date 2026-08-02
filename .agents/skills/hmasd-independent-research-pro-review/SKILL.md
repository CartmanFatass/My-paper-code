---
name: hmasd-independent-research-pro-review
description: Use from the persistent Independent Research Explorer for one exact Pro or Gemini direction or methodology review sent directly with Agentify.
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

## Direct review

1. Freeze one concise local execution plan and one standalone UTF-8
   `RAW_QUESTION`. The question contains only natural-language scientific
   content; assignment, authority, session, Git/path, provider and transport
   fields remain local. The local assignment identity begins with exactly
   `IR_DIRECTION_REVIEW:` or `IR_METHODOLOGY_REVIEW:` and declares either
   `PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW`,
   `PRO_ADVERSARIAL_SCIENTIFIC_REVIEW`, or the bounded methodology-audit mode.
2. Invoke Agentify directly with that question and the intended provider page.
3. Wait for the returned response. Never interrupt an active generation.
4. Archive the raw response in `local_research/pro_reviews/<review-id>/`, then
   reconcile it scientifically. If the call fails, confirm no generation is
   active and retry the same question when useful.

When one paired protocol includes a common follow-up, freeze that follow-up as
a second standalone natural-language question. Send it in each provider's
existing conversation through the same direct call. Sequential observation is allowed for attribution; it does
not create a second workflow or permit provider-specific prompt metadata.

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
operator. Research children remain available for
source, innovation, principles and critique work; no child performs Pro
transport or monitoring.
