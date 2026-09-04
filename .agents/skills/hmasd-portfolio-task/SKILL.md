---
name: hmasd-portfolio-task
description: Use when Root is comparing or changing HMASD direction priority, lifecycle, capacity, fusion, separation, or the next research investment.
---

# HMASD Portfolio Decisions

## Core principle

Choose the smallest investment that can change a direction decision without confusing scientific
value with execution convenience or strength of claim with strength of ceremony.

Read `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` before comparing evidence or changing a
direction. Apply its A, B, C-BENCH, C-TRANSFER, and C-FORMAL burdens. General mathematical proof is
not the default admission condition for empirical MARL: structural motivation plus bounded toy or
benchmark evidence is scientifically legitimate when the claim ceiling is bounded to that evidence.

## Portfolio responsibilities

Before investing or making a material lifecycle recommendation, Root identifies:

- the exact Portfolio decision question;
- the lowest evidence class able to answer it;
- the strongest claim that class can support and the material non-goals;
- the smallest valid implementation, derivation, counterexample, or experiment that separates the
  live choices; and
- the contrary observation that would change the recommendation.

Executing every already `ACTIVE`, independently admitted direction under the current unbounded
capacity policy is ordinary sequencing, not a new Portfolio decision. Runtime availability and
dependency ownership may change launch order, but Root must not silently turn scheduling into a
priority, lifecycle, exclusion, fusion, separation, or investment decision. If scarce resources
force a choice among directions rather than a queue in which all remain admitted, use the
Portfolio decision path below.

Execution placement is remote-first under `.codex/hmasd-compute.toml`. Route new portable
result-bearing invocations to the enabled remote node while the local machine retains the control
plane and acts as a prospectively authorized fallback. This is capacity routing, not evidence or a
direction-priority signal. A node change must preserve the card's declared host/device semantics,
must occur before question-relevant output, and requires a fresh admission on the destination.

Compare directions at their honest claim ceilings. Do not reward a direction merely for producing
more formal artifacts, and do not penalize a bounded empirical direction for lacking a theorem,
exact support census, bit identity, transfer evidence, or deployment assurance that its current
claim does not require. When the project objective is performant MARL, prioritize real algorithm
implementation and decision-relevant empirical evidence unless the proposed claim itself requires
C-FORMAL work.

Distinguish technical success, bounded task competence, comparative algorithm advantage,
cross-scenario transfer, safety, and deployment. Evidence for an earlier claim does not silently
promote a later one.

## Investment policy (owner decision 2026-09-04)

Controlling record: `docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`;
rule text: evidence spec §11.7 and `AGENTS.md` §2. These are investment rules, not launch gates.

- **Headroom floor 5%.** A direction opens a mechanism B family only with a recorded headroom
  measurement on its host (upper reference minus tuned same-information baseline) of at least 5%
  of the baseline return. A direction without one has, as its smallest next investment, that
  A/RECON measurement; Root sequences those first when comparing investments.
- **Closure share 25%.** Compare B signals across directions by the share of recorded headroom
  they close, not by absolute edge.
- **Recast budget one.** A direction at its second Convergence `RECAST` continues (the Pro
  decision is final for its node) but takes the lowest sequencing priority among ACTIVE
  directions: Root admits every other ACTIVE direction's work first. It appears in the owner
  digest as `second-recast`; Root does not mutate the lifecycle field, and an owner reply may PARK
  it. Nothing waits for that reply.
- **Usage per valid result.** `PORTFOLIO.md` carries one column per direction: usage consumed
  per valid result (`AGENTS.md` §5 currency), filled from run summaries where wall time is
  recorded and `unmeasured` otherwise. Root refreshes it with every snapshot and cites it in every
  cross-direction proposal.
- **Digest.** Every Portfolio proposal awaiting ratification, and every direction recommendation
  a DM returns, is one row of `docs/research/portfolio/owner/digest/<YYYY-MM-DD>.md` with kind
  `portfolio` (schema in `docs/research/portfolio/owner/README.md`). Root reads the `owner`
  cells there at every clean boundary; a filled cell is the owner's ratification or refusal.

## Lifecycle semantics

Update the smallest implicated unit:

- a technical or instrumentation failure has no scientific polarity;
- a valid negative may close its exact implementation, benchmark-comparator pair, or frozen object;
- `PARKED` means a valuable question may remain but no sufficiently specified or feasible
  decision-relevant object currently merits investment, or a named dependency is unresolved;
- `CLOSED` requires no valuable independent question at an appropriate evidence class, absorption
  by another direction, structural impossibility/equivalence, sufficient independent bounded
  failures, or a documented Portfolio judgment that all plausible narrower/recast objects are
  dominated; and
- failure of one confirmatory object does not by itself close a direction.

PARKED does not mean "waiting for a theorem" or "waiting for user authorization" unless that is the
actual named dependency. Absence of a general proof or of real-UAV validation is not itself a reason
to park or close a direction whose declared target is exploratory or bounded benchmark performance.
Use explicit `CLOSE_OBJECT`, `PARK_DIRECTION`, `CLOSE_DIRECTION`, fusion, and absorption reasoning
rather than treating them as synonyms.

A direction Pro node may conclude that direction-local execution should stop at a clean boundary
or recommend `PARK_DIRECTION`. That conclusion does not by itself mutate the lifecycle field in
`PORTFOLIO.md`; an `ACTIVE`/`PARKED`/`CLOSED` Portfolio mutation remains a Portfolio-tier action and
requires the owner-ratified path below.

## Persistent Pro decision node

Before changing direction priority, capacity, lifecycle, fusion, separation, registering a new
direction, or selecting the next cross-direction investment, Root must use
`$hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision`. Every packet binds to
the single persistent conversation key `portfolio:cross_direction`, lists every direction in scope,
and includes the current Portfolio snapshot, this evidence specification, the selected evidence
class and claim ceiling, plus the exact direction/evidence paths needed for the decision. The
project-shared registry creates or binds the provider conversation on first use under the stable
conversation binding key and reuses that exact provider conversation for later Portfolio rounds.
Each handoff reuses the one project Transport task declared in `.codex/hmasd-transport.toml` and
sends exactly one completion or terminal-blocker receipt back to the handoff author's declared
`parent_thread_id`. Dispatch passes `model=gpt-5.6-luna` and `thinking=xhigh` explicitly; it never
calls `create_thread` or selects a replacement task. The singleton task ID is an execution endpoint,
never a provider-conversation binding or receipt destination.

A complete archived Pro response that decides the posed question at its declared evidence class is
the Portfolio proposal. Root records it with its evidence and bounded rationale in a decision record
for the owner to ratify. No Portfolio action takes effect before owner ratification, including a
reversible action, and `PORTFOLIO.md` is updated only with the ratified disposition. Root does not
replace or override the proposal with a local-model judgment. If Pro reports missing connector
access or insufficient evidence, Transport has not archived a complete response, or the answer
rejects bounded empirical work solely for lacking an unrequested stronger class, no class-correct
Portfolio decision exists:
the question parks (AGENTS.md section 3), Root drives other directions, and nothing is decided
provisionally at this tier. Root may continue reversible evidence collection or request a
class-corrected answer but must not convert the mismatch into scientific polarity.

Read `docs/research/portfolio/PORTFOLIO.md` for current state and the relevant `DIRECTION.md` files
for scientific authority. Compare claim ceiling, decision relevance, complementarity, substitution,
reversibility, cost, live external effects, and the smallest discriminating observation.

Transport, implementation, and process status may change sequencing or feasibility; they do not by
themselves determine scientific polarity or lifecycle. Preserve uncertainty and state why the
recommended action would change under a contrary result.

Root records the Pro proposal, obtains the owner's ratification, and integrates the ratified
disposition in `PORTFOLIO.md`. Outside the Prompt Author and Transport packet boundary, use ordinary
language; no additional response schema is required.
