---
name: hmasd-scientific-external-review
description: Run one frozen, at-most-once scientific external-review round.
---

# HMASD Scientific External Review

## Purpose

Coordinate exactly one Pro Innovator before or alongside neutral local work and
exactly one Pro Convergence after local EM synthesis for one fresh material
cycle. Either exact still-unsent stage may be waived only by the user. Review is
evidence, not permission: provider binding, at-most-once effects, exact archive
bytes, scientific interpretation, and tracked direction authority remain
separate.

All provider work uses the singleton Root-mediated `BrowserTransport`; EM and CM
never spawn, contact, or invoke it directly. Shared carriers, common v1
envelopes, hard boundaries, liveness, and transport mechanics are defined by
`.omp/AGENTS.md`, `.omp/RULES.md`, and `hmasd-browser-transport`.

## Frozen inputs

Use the direction ID; stable cycle/round ID; frozen question and evidence-set
SHA-256s; exact prompt and archive refs; required ChatGPT Pro model; existing
Agentify operation, commitment, and transport facts; observed external-index
revision; and local synthesis ref before Convergence. Every request returned
through Root with `next_action.owner=TRANSPORT` remains meaning-complete under
`.omp/AGENTS.md`.

## Two-stage round

1. Freeze question and evidence identities and create one deterministic round
   ID. Author the new round's cohesive natural-language Innovator prompt from
   the neutral scope without EM conclusions, favored answers, local results, or
   another provider result.
2. Unless exactly waived, return one `INNOVATOR` request through Root before or
   alongside mutually blind neutral local work. Bind `provider: chatgpt`, the
   exact Pro model, prompt hash, operation, conversation, archive target,
   idempotency key, fingerprint, and commitment state. Only the strict Agentify
   review surface may send.
3. Root returns the common v1 transport fact and validated archive ref to EM. A
   committed or uncertain operation is observe-only through the same strict
   Agentify operation and is never resent. EM interprets readable content as
   evidence without transferring scientific authority.
4. EM completes local synthesis. No Convergence prompt may be authored or
   requested before its durable ref exists, and Innovator output cannot
   substitute for synthesis.
5. Unless exactly waived, author a separate natural-language Convergence prompt
   from the synthesized evidence packet and return one new `CONVERGENCE`
   request through Root, bound to ChatGPT Pro and its own exact Agentify
   operation.
6. EM dispositions every material Convergence objection against evidence. Root
   validates and records archive bytes through the external-review CLI; EM
   performs expected-revision CAS updates of external-index pointers.

One fresh cycle has only these two Pro operations. Continuation, evidence
intake, wording repair, claim narrowing, and CM-result interpretation reopen
neither. A later wake observes the same live operation or resumes the same
frozen round; it never creates a replacement sender or automatic resend.

## Scientific finding product

The Innovator and Convergence prompts request scientific findings that EM can
synthesize beside local analytical products. For each material finding or
bounded no-finding, the scientific product records:

- assignment or evidence-gap ID and task family, including the review stage;
- the claim or attacked claim/link;
- exact evidence references and locators, with verified fact, external
  evidence, inference, speculation, and contradiction kept distinct;
- assumptions, applicability boundaries, and any surviving alternative;
- a falsifier or counterexample, or the bounded search that did not find one;
- uncertainty, limitations, reviewed scope, and the exact residual gap;
- consequence and decision relevance, including the conditional effect on the
  claim ceiling or other EM-owned variable; and
- a recommendation, such as a next discriminator, claim correction, or no
  change.

Label the product `MATERIAL_INSIGHT` or `NO_MATERIAL_INSIGHT`.
`NO_MATERIAL_INSIGHT` is a successful negative-complete product within the
frozen reviewed scope. It records the sources inspected, methods attempted, why
no answer-changing result follows, and residual uncertainty. It is not
technical failure, approval, negative evidence, evidence of absence, or
scientific rejection, and it produces no claim delta. A scientifically adverse,
negative, or null finding can instead be material when it supports an
answer-changing conclusion. Reopen the same no-insight scope only after a new
mechanism, source, observation, premise, or corrected defect.

These fields organize the scientific interpretation and EM disposition; they
do not modify provider response bytes, archive bytes, common v1 transport facts,
Agentify commitment state, or authority. A transport failure produces no
scientific product or update.

## External-review index v2

`scripts/schemas/hmasd_external_review_index.schema.json` is the exact field and
value-shape authority. Under both `prompt_refs` and `providers`, a v2 round has
exactly `pro_innovator` and `pro_convergence`. The Innovator prompt is required
for a new round; the Convergence prompt remains null until synthesis and
prompt authorship. Provider slots are nullable and may contain the exact
in-flight or terminal operation fact returned through Root. A waiver fabricates
no provider result.

The only statuses are `INNOVATOR_PENDING`, `INNOVATOR_RUNNING`,
`LOCAL_RESEARCH`, `SYNTHESIS_READY`, `CONVERGENCE_RUNNING`, `COMPLETE`, and
`BLOCKED`. Use the phase actually reached. `COMPLETE` requires disposition of
every non-waived stage; `BLOCKED` preserves the unresolved stage and reentry.
Migrate historical empty indexes mechanically; never invent prompt, provider,
operation, waiver, or synthesis facts for a partial historical round.

## State and failure boundaries

Agentify is the sole submission ledger. BrowserTransport owns only transport
facts, fingerprints and rereads the exact assigned response, and writes no
tracked scientific state. Root validates requester, mode, model, operation,
commitment, and archive bytes and alone invokes the external-review CLI. EM
writes only CAS external-index pointers and scientific disposition after Root
returns. Immutable natural-completion archive bytes gain no workflow fields.
Operations, tabs, conversations, archives, and hashes are not scientific or
workflow authority; provider completion is not accepted science.

Unknown commitment is terminal for sending: observe the same exact Agentify
operation and never resend. `SENT_WAITING`, `COMMITMENT_UNKNOWN`, and
`SENT_UNREADABLE` are observe-only. `ZERO_SEND_FAILED` proves no send for that
operation but does not itself authorize another operation.

Reject changed frozen hashes, Convergence without synthesis, wrong provider or
model, duplicate operation or round, an ordinary send surface, non-natural
completion, invalid or unreadable archive bytes, and stale index revisions.
Preserve the scientific stage reached. Missing transport or Advisor output is an
evidence gap, not an approval failure; transport failure changes no scientific
conclusion, claim ceiling, engineering status, Portfolio action, or lifecycle.
