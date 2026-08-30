---
name: hmasd-scientific-external-review
description: Run one frozen, at-most-once scientific external-review round.
---

# HMASD Scientific External Review

## Purpose

Coordinate exactly one Pro Innovator before or alongside neutral local work and
exactly one Pro Convergence after local EM synthesis for one fresh material
cycle. Review is evidence, not permission: provider binding, one attempted send
per operation, exact archive bytes, scientific interpretation, and tracked
direction authority remain separate.

All provider work uses the singleton `BrowserTransport`; Root routes the frozen
request and returns the receipt without adding an approval step. EM and CM never
invoke the browser transport directly. Shared carriers, common v2 envelopes,
hard boundaries, liveness, and transport mechanics are defined by
`.omp/AGENTS.md`, `.omp/RULES.md`, and `hmasd-browser-transport`.

## Frozen inputs

Use the direction ID; frozen question and evidence-set SHA-256s; exact
`workflow_version`; canonical deterministic `round_id`; `review_stage` in
`pro_innovator` or `pro_convergence`; provider; exact prompt, raw response, and
operation-receipt refs; separate `product_model` and `reasoning_effort`; the
immutable Agentify operation/idempotency/fingerprint/stable key; target
conversation; minimal receipt facts; observed external-index revision; and
local synthesis ref before Convergence. Current ChatGPT requests require
product model `GPT-5.6 Sol` and reasoning effort `Pro`. Every `TRANSPORT`
`next_actions` item is already authorized and meaning-complete.

## Stage-safe prompt registration

1. Freeze question and evidence identities and create one deterministic round
   ID. Author only the current stage's cohesive natural-language prompt as a
   disposable file outside the canonical round path. The Innovator prompt comes
   from the neutral scope without EM conclusions, favored answers, local
   results, or another provider result.
2. Validate one disposable stage prompt before canonical immutable registration.
   Failed validation creates no journal, canonical prompt, canonical path,
   round, or external-index fact. Innovator validation and registration occur
   before local synthesis. Its registration creates the canonical Innovator
   prompt reference and leaves the canonical Convergence prompt reference null.
3. Registration first fsyncs one content-addressed transaction journal under
   ignored `.omp/runtime`. The immutable transaction binds the writer, stage,
   round, expected revision, canonical paths, exact old/new index hashes and
   staged bytes, and exact prompt hash and staged bytes. Only then may it
   publish the canonical prompt and replace the v4 index. Every publication,
   verification, cleanup, and terminal boundary is phase-recorded and fsynced.
   Entry to the same exact registration recovers its journal idempotently.
   Exact old index plus no canonical prompt rolls back; any observed exact
   canonical publication rolls forward using only the journal-bound bytes.
   Wrong bytes, a content-address collision, or an irreconcilable observation
   becomes `UNKNOWN` and never rewrites canonical bytes.
4. Return one `INNOVATOR` request through Root before or alongside mutually
   blind neutral local work. Bind `provider: chatgpt`, `review_stage:
   pro_innovator`, `product_model: GPT-5.6 Sol`, `reasoning_effort: Pro`, the
   registered prompt, immutable operation/idempotency/fingerprint/stable key,
   exact target conversation, canonical round, and stage-owned raw response
   path. Only the current strict Agentify review surface may send.
5. BrowserTransport executes directly. Before `send_attempted`, reversible
   errors retry automatically on the same immutable operation. Immediately
   before the one native Send activation it persists `send_attempted: true`.
   After that fact is set, it only observes the same provider turn and never
   sends again. Root returns the minimal receipt and validated raw-response and
   operation-receipt refs to EM. EM interprets readable content as evidence
   without transferring scientific authority.
6. EM completes local synthesis. No Convergence prompt may be authored,
   validated, registered, or requested before its durable ref exists, and
   Innovator output cannot substitute for synthesis. Convergence validation and
   registration additionally require canonical Innovator prompt references.
7. Validate and durably register the separate natural-language Convergence
   prompt from the synthesized evidence packet, then return one `CONVERGENCE`
   request through Root, bound to ChatGPT product model `GPT-5.6 Sol`, reasoning
   effort `Pro`, `review_stage: pro_convergence`, and its own exact Agentify
   operation and stage-owned raw response path.
8. EM dispositions every material Convergence objection against evidence. Root
   validates exact archive bytes at the archive boundary; EM performs
   expected-revision CAS updates of external-index pointers.

One fresh cycle has only these two Pro operations. Continuation, evidence
intake, wording repair, claim narrowing, and CM-result interpretation reopen
neither. A later wake resumes the same frozen round and follows each operation's
`send_attempted` fact directly.

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
do not modify provider response bytes, archive bytes, common v2 transport facts,
Agentify receipt facts, or authority. A transport failure produces no
scientific product or update.

## External-review index v4

`scripts/schemas/hmasd_external_review_index.schema.json` is the exact field and
value-shape authority. Current workflow accepts v4 only. Active workflow lives
in `rounds`; under both `prompt_refs` and `providers`, a round has exactly
`pro_innovator` and `pro_convergence` slots. Durable Innovator registration is
the only creation of a new active round: it inserts only the Innovator prompt
reference and leaves the Convergence prompt reference null. Durable Convergence
registration later inserts only the Convergence prompt reference after durable
synthesis and canonical Innovator references exist. Provider slots are nullable
and may contain the exact minimal operation receipt returned through Root.

Historical bytes and layouts may remain tracked as inert evidence, but the
current index has no historical-record collection or loader. Historical bytes
cannot be loaded, registered, imported, transitioned, emitted, or used as
active rounds, provider dispositions, prompt-registration authority, transport
facts, or resend authority.

The only active-round statuses are `INNOVATOR_PENDING`, `INNOVATOR_RUNNING`,
`LOCAL_RESEARCH`, `SYNTHESIS_READY`, `CONVERGENCE_RUNNING`, `COMPLETE`, and
`BLOCKED`. Use the stage actually reached. `COMPLETE` requires disposition of
both stages; `BLOCKED` preserves the unresolved stage and reentry. Never invent
prompt, provider, operation, synthesis, round, or historical archive facts.

## Ownership and failure boundaries

Agentify is the sole submission ledger. BrowserTransport owns only the minimal
receipt facts, fingerprints and rereads the exact assigned raw response, and
writes no tracked scientific state. Root validates the exact requester, mode,
provider target, product model and reasoning effort, immutable operation
identity, prompt/response identity, raw response bytes, and separate operation
receipt. EM writes only CAS external-index pointers and scientific disposition
after Root returns. Raw provider response bytes gain no workflow fields and are
never treated as a JSON transport envelope.

Prompt validation and registration preserve this same boundary: validation is
disposable and has no tracked-state effect; registration is the sole journaled
canonical-path publication and expected-revision prompt-slot update. Recovery
observes only the exact journal/index/prompt/staged-byte transaction and
deterministically completes or restores it; it never sends, authors science,
changes a semantic stage, or rewrites irreconcilable canonical bytes.

Current operation refs use snake-case schema version `4` and bind the exact
workflow version, supported review stage, round ID, provider target,
`product_model`, `reasoning_effort`, immutable operation/idempotency/fingerprint/
stable key, prompt and response paths, timestamps, `send_attempted`, observed
conversation and provider user/assistant message IDs, nullable one-code error,
and nullable exact archive receipt. Current stage-owned files are:

`docs/external-review/directions/<direction>/<canonical-round>/<review-stage>/<provider>/response.md`

and separate `operation_ref.json`. The receipt's archive projection is exactly
`exact` and its SHA/size must match a fingerprint and reread of `response.md`.
The two stages never share a destination. Historical paths and JSON response
envelopes are inert bytes and never pass current validation.

Operations, tabs, conversations, raw responses, receipts, and hashes are not
scientific or workflow authority; provider completion is not accepted science.
A pre-Send error retries automatically while `send_attempted` is false. Once
`send_attempted` is true, the same operation may only observe its user turn,
assistant turn, and response; it never activates Send again. Reject changed
immutable identities, a regressing send fact, removed or changed observed IDs
or archive, an archive without the assistant ID, Convergence without synthesis,
wrong provider/product model/reasoning effort, duplicate operation or round, an
ordinary send surface, invalid or unreadable raw response/receipt bytes, and
stale index revisions.
Preserve the scientific stage reached. Missing transport or Advisor output is an
evidence gap, not an approval failure; transport failure changes no scientific
conclusion, claim ceiling, engineering status, Portfolio action, or lifecycle.
