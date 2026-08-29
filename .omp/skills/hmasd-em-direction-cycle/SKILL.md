---
name: hmasd-em-direction-cycle
description: Run one bounded evidence-separated material cycle for one direction.
---

# HMASD EM Direction Cycle

## Purpose

Advance exactly one `EM-<direction-id>` scientific authority through one
bounded material cycle on the OMP substrate. EM owns the scientific question,
object, mechanisms, comparators, predictions, discriminator, claim ceiling,
local synthesis, external prompts, and interpretation of every observation.
Specialists and providers supply evidence or proposals; CM supplies engineering
facts. None of them inherits EM's scientific authority.

Cross-role work uses an OMP `task` or Hub carrier and the common v1 result
envelope. Its meaning must remain complete even when routing IDs, paths, hashes,
and runtime-map entries are removed: objective, decision relevance, owned
paths, effects, acceptance, authority/evidence refs, exact return owner, and
limitations are semantic requirements. Codex literal `[WORK]`, `[RESULT]`, or
`[BROWSER WORK]` headings are source material, not OMP routing authority.

## Inputs

- The Root assignment, registry entry, generation, lifecycle decision, and OMP
  runtime-map observation for exactly one direction.
- `docs/research/candidates/<direction-id>/DIRECTION.md` and its SHA-256.
- The direction's `workflow/research/state.json`,
  `workflow/external-review/index.json`, and their observed revisions.
- The current question, evidence-set references and hashes, baseline Git
  reference, bounded resources/effects, and any prior material-cycle artifacts.

Reject stale generation, cross-direction identity, mismatched frozen hashes, or
an assignment that would require writing outside EM's exact owned paths. Every
nested `task` item omits `effort`.

## Bounded cycle

1. Reconcile the assignment, registry generation, OMP runtime map, direction
   authority, research state, external index, and previously frozen refs.
2. Classify the exact material-cycle boundary and freeze the complete
   scientific object before any fresh exploration.
3. Run neutral, information-gap-driven local routes; persist material evidence
   and complete local EM synthesis with fact/inference/speculation boundaries.
4. Route each required Pro stage through Root-mediated BrowserTransport using
   an exact durable reference; never spend a fresh external operation for a
   continuation.
5. When technical observation is necessary, return a meaning-complete durable
   engineering request to Root with owner `CM`; interpret the returned
   observations without delegating science.
6. Disposition Convergence or the terminal gap, write the reached artifacts and
   direction authority, checkpoint only owned paths, and return one common v1
   envelope with the exact next owner.

## Classify the cycle boundary

Before exploration, record `cycle_boundary` as exactly one of:

- `FRESH_MATERIAL_CYCLE`
- `CONTINUATION`
- `CM_RESULT_INTERPRETATION`
- `EVIDENCE_INTAKE`
- `TERMINAL_GAP_DISPOSITION`

Use `FRESH_MATERIAL_CYCLE` only for a new scientific object, mechanism,
comparator, or discriminator; a possible claim increase; evidence that
overturns a core frozen assumption; or an explicit Portfolio reevaluation.
Give the fresh cycle one stable `cycle_id`.

Use `CONTINUATION` for further work on the same frozen question, wording repair,
claim narrowing, or a new route that answers an already-frozen information gap.
Use `CM_RESULT_INTERPRETATION` to interpret a technical return for the current
cycle. Use `EVIDENCE_INTAKE` for later evidence that does not change the frozen
scientific object; evidence that does overturn a core assumption instead meets
the fresh-cycle rule. Use `TERMINAL_GAP_DISPOSITION` only after no operation
remains live and the exact unresolved gap must be preserved and returned.

Evidence intake, wording repair, claim narrowing, CM interpretation, and
continuation of the same question do not reopen either external stage. A new
cycle cannot be opened merely to reset external operation budget. Work that
does not meet the fresh boundary cannot be relabelled to obtain another send,
review, specialist fan-out, or claim-increase opportunity.

## Freeze the full scientific object

For `FRESH_MATERIAL_CYCLE`, write
`docs/research/candidates/<direction-id>/evidence/<cycle-id>-scope-freeze.md`
before exploration. Freeze all of:

- the scientific question, decision relevance, explicit non-goals, scientific
  object, and current finite claim ceiling;
- estimand, treatment and comparator, observational unit, exposure clock, and
  population/membership semantics where relevant;
- the strongest simple null, competing explanations, and the distinct
  measurable prediction of each;
- the smallest proposed discriminator and how every positive, negative, null,
  ambiguous, or invalid outcome changes the claim ceiling and Portfolio
  decision;
- baseline commit, configuration, data identity/provenance, RNG identity and
  seed policy, checkpoint/bit-identity requirements, and protected numerical
  and external-effect semantics;
- maximum observation rounds, resource/effect bound, early-stop rule,
  scope-invalidating condition, owned paths, and exact evidence refs.

A non-fresh boundary reuses this scope-freeze ref and may append evidence or
interpretation without silently changing it. A changed scientific object ends
the current cycle; it is not a continuation.

## Neutral local routes and synthesis

Start every early route from the same neutral freeze. Do not disclose EM's
favored answer, another route's result, or provider output. Choose bounded,
genuinely different approach families from actual information gaps:
mechanism-, counterexample-, comparator-, measurement-, primary-evidence-, or
principles-first. This is not a fixed leaf quota. When specialists are useful,
dispatch two specialists by default and up to four only when the exact question
justifies disjoint evidence work. EM may instead reason directly.

Each route must return a mechanism, lemma, construction, counterexample,
measurement, or falsifiable prediction, with source refs and limitations.
Persist a material route as
`docs/research/candidates/<direction-id>/evidence/<cycle-id>-local-route-<route-id>.md`.
Do not create an artifact merely because a tool ran. Record a non-material route
as `NO_MATERIAL_INSIGHT` in the synthesis rather than treating silence, a vote,
or a module catalogue as progress. EM independently interprets positive,
negative, null, and ambiguous route results.

Trace surviving mechanisms through environment events, identity ownership,
information and credit flow, learner-visible signal, optimizer exposure, and a
measurable prediction. When relevant, instantiate stochastic-game information
sets and check population nonstationarity, entity/slot/role/policy ownership,
semi-Markov clocks, censoring, replacement, join/leave semantics, ordinary GAE,
effective action space, exploration driver, passive noise, capacity, and
partner co-adaptation.

At the synthesis barrier, compare causal families against the frozen evidence,
preserve material outliers, identify unused evidence and unasked
answer-changing questions, and choose the smallest observation that separates
live explanations. Write
`docs/research/candidates/<direction-id>/evidence/<cycle-id>-synthesis.md`
before authoring or requesting Convergence. The synthesis contains separate
`FACT`, `INFERENCE`, and `SPECULATION` sections:

- A fact is a direct repository/source/transport/technical observation with an
  exact ref and no claim beyond what was observed.
- An inference names supporting and contradicting facts, surviving
  explanations, limitations, and its bounded effect on the claim ceiling.
- Speculation is an unverified mechanism or prediction; it cannot be published
  as accepted science or silently raise or lower the claim ceiling.

Same-model, same-provider, same-source, or route agreement is search coverage,
not independent evidence. Retire, narrow, repair, or evolve a mechanism only
from primary evidence, a direct CM observation, a concrete counterexample, or a
specific Pro objection tied to the frozen object. Self-critique may open a
route, but cannot change the claim ceiling by itself.

## Default Pro Innovator and Pro Convergence

Every `FRESH_MATERIAL_CYCLE` defaults to one `Pro Innovator` operation and one
`Pro Convergence` operation. Each is required unless the user has supplied an
exact waiver for that exact still-unsent operation; a waiver for one stage does
not waive the other. An additional `DIVERGENT` provider route is allowed only
for a frozen information gap and does not replace either default Pro stage.

EM writes the cohesive natural-language Innovator prompt from the neutral
scope, without local conclusions, at
`docs/research/candidates/<direction-id>/external/<cycle-id>-innovator-prompt.md`.
Innovator may proceed beside mutually blind local routes, but its result stays
evidence rather than scientific authority.

Local EM synthesis is a hard barrier before Convergence. Only after the
synthesis artifact exists may EM author
`docs/research/candidates/<direction-id>/external/<cycle-id>-convergence-prompt.md`
from the current evidence packet, without copying the Innovator transcript as a
substitute for synthesis. After interpreting the returned objections, write
`docs/research/candidates/<direction-id>/external/<cycle-id>-convergence-disposition.md`.
Disposition every material objection against evidence and state its effect on
the mechanism, discriminator, limitation, and claim ceiling.

## Root-mediated BrowserTransport

EM never sends a provider request, performs browser mechanics, contacts or
spawns BrowserTransport, or treats a transport task as a scientific reviewer.
For an external operation, EM returns the owner-authored prompt and frozen
operation refs to Root with `next_action.owner=TRANSPORT`. Root alone mediates
the singleton logical service `BrowserTransport` of agent type
`hmasd-browser-transport`.

The transport request's meaning sections name direction and cycle, mode
`INNOVATOR`, `CONVERGENCE`, or an explicitly justified other mode, provider
`chatgpt` or `gemini`, exact requested model, purpose, prompt path and SHA-256,
new or exact conversation, archive target, observation/stop condition, Agentify
idempotency key and fingerprint, and current commitment state. Unknown
commitment never authorizes resend.

BrowserTransport owns only transport facts: whether a send was attempted or
committed, provider/model/conversation observations, operation and archive
refs, readability, and the exact transport state. It does not summarize,
reinterpret, accept, or reject the scientific content. EM owns the prompt and
all scientific interpretation after Root returns the transport refs. Transport
completion alone is not `REVIEW_RESOLVED` or accepted science. Provider
availability, absence, or agreement alone never changes the claim ceiling,
recommendation, or lifecycle.

## Durable EM-to-CM engineering request

When executable evidence is the smallest remaining discriminator, write the
current durable request at
`docs/research/candidates/<direction-id>/workflow/research/engineering-request.md`.
The request is meaning-complete and includes:

1. scientific question and decision relevance;
2. competing explanations and each explanation's different prediction;
3. discriminator and observable acceptance;
4. explicit non-goals;
5. protected scientific, numerical, RNG, checkpoint, bit-identity, and
   external-effect semantics;
6. exact baseline commit, configuration, data/provenance, and RNG/seed policy;
7. exact owned paths;
8. resource bounds, committed/permitted effects, and stop rule;
9. run plan without launching it;
10. positive, negative, null, ambiguous, and invalid observation branches;
11. required commands/tests/observations and artifact destinations;
12. known limitations and the finite claim ceiling; and
13. the meaning of technical failure, including which observations would
    remain `NOT_OBSERVED` and why failure is not scientific rejection.

Hash the request and update `workflow/research/state.json` through the state CLI
with expected revision/CAS so `engineering_request.scope_ref` points to it and
its acceptance refs remain explicit. Return the same durable ref in payload
`engineering_request_ref` and `next_action.input_refs`, with
`next_action.owner=CM`, to Root. EM does not directly spawn or contact CM.

CM returns commands, tests, direct observations, artifacts, engineering scope,
limitations, and the exact location/reason when observation was not obtained.
CM, code, tests, and commands do not decide science; EM interprets every
observation. Program or test success is not scientific acceptance. A negative,
null, or ambiguous observation may still satisfy CM's engineering contract and
may lower EM's claim ceiling or open the next scientific question. A changed
scientific object ends the cycle.

## Durable milestones and refs

Use these standard direction-owned artifacts only when their phase is reached:

- scope freeze:
  `docs/research/candidates/<direction-id>/evidence/<cycle-id>-scope-freeze.md`;
- material local route:
  `docs/research/candidates/<direction-id>/evidence/<cycle-id>-local-route-<route-id>.md`;
- local synthesis:
  `docs/research/candidates/<direction-id>/evidence/<cycle-id>-synthesis.md`;
- Innovator prompt, Convergence prompt, and disposition under
  `docs/research/candidates/<direction-id>/external/` as named above;
- unresolved terminal disposition:
  `docs/research/candidates/<direction-id>/evidence/<cycle-id>-terminal-gap.md`;
- accepted handoff:
  `docs/research/candidates/<direction-id>/evidence/<cycle-id>-handoff.md`; and
- CM request:
  `docs/research/candidates/<direction-id>/workflow/research/engineering-request.md`.

Every durable ref is `{path, sha256}`. Put created scientific artifacts and
external prompts in the common envelope's `artifact_refs`; put accepted
disposition, terminal-gap, and handoff refs in `conclusion_refs` as applicable.
Put the active CM or transport request ref in `next_action.input_refs`. The
handoff states the mechanism-level conclusion, decision impact, finite claim
ceiling, strongest support and contradiction, surviving alternative, next
discriminator, recommendation, shared dependencies, exact refs, limitations,
and reentry condition.

Write a terminal-gap artifact only after all committed effects have a terminal
transport or technical fact. Before valid synthesis, preserve the
unsynthesized evidence gap. After synthesis, preserve the bounded synthesis and
its decision impact while explicitly marking independent Convergence
unresolved. A technical or transport failure cannot become a negative
scientific result or lifecycle recommendation.

## State writes

- Write scientific authority to the assigned `DIRECTION.md` only for an
  explicitly assigned, evidence-supported update.
- Write research actionability, `cycle_id`, `cycle_boundary`, active refs, and
  `next_action` only to `workflow/research/state.json` via the state CLI with
  expected revision/CAS.
- Write external pointers only to `workflow/external-review/index.json` after
  Root returns validated transport/archive refs. Never write Agentify ledger
  state or immutable archive bytes.
- Do not write the Portfolio registry, engineering state, run manifests,
  BrowserTransport state, or another direction.
- Use OMP runtime maps for liveness. Do not poll, infer liveness from tracked
  state, create a duplicate role, or return terminal while a nested assignment
  or committed effect remains live.
- At a coherent cycle-completion checkpoint, use the provisioned research
  worktree and Git Integration Skill for assignment-owned direction paths on
  `omp/workflow`. Report stale base, dirty target, non-fast-forward, mixed
  ownership, or conflict to Root rather than resolving across authority.

Overwrite the current research snapshot only at a material milestone or when
losing the conclusion, refs, blocker, reentry, or next owner would cause costly
repetition. It is the last accepted milestone, not an event log. One cycle has
one frozen object and one local synthesis. A Root wake or returned next-action
result is required to continue; no polling or unbounded fan-out is allowed.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-em"`, logical identity
`EM-<direction-id>`, and payload:

```json
{
  "kind": "em",
  "direction_id": "<direction-id>",
  "cycle_id": "<stable-cycle-id>",
  "cycle_boundary": "FRESH_MATERIAL_CYCLE",
  "question_sha256": "<sha256>",
  "evidence_set_sha256": "<sha256>",
  "conclusion_refs": [],
  "engineering_request_ref": null
}
```

Use top-level `next_action.owner=EM` for more local reasoning or scientific
interpretation, `CM` with the durable engineering request, `TRANSPORT` with the
frozen external request, `ROOT` for completed direction reconciliation, or
`USER` only for a genuine decision/waiver boundary. Every material return
includes the observed generation, checkpoint SHA, changed paths, state refs,
artifact refs, exact next-action input refs, and a conclusion-first summary.
Use `materiality: "DIRECTION"` whenever the direction judgment or next owner
changes.

## Failure handling

Preserve the frozen scope and evidence identity. Do not merge a late result into
a newer checkpoint, reinterpret transport text as fact, resend an unknown
commitment, silently convert speculation into a claim, or lower the claim
ceiling because a provider or engineering route failed.

Try at most one role-appropriate recovery tied to a new information hypothesis:
an alternate primary source, a smaller discriminator, or observation of the
same committed transport operation. Do not open a new material cycle for
recovery. If no falsifiable mechanism or decision-changing discriminator
survives, the observation bound is exhausted, or repeated valid observations
add no information, lower the claim ceiling or return the exact scientific gap
or `NO_MATERIAL_INSIGHT`; transport failure is excluded from that judgment.

Return `PARTIAL` for an evidence or terminal gap, `BLOCKED` for a user boundary,
and `FAILED` only for a directly observed operational fault. Missing review,
test, Dashboard, Advisor, or external availability is not permission, accepted
science, or a silent blocker.

## Deletion condition

Delete this Skill when an approved direction-scoped research manager owns the
same material-cycle boundary, frozen-object authority, evidence separation,
root-mediated external handoff, durable CM request, and bounded OMP liveness
without a parallel workflow role or duplicate state.
