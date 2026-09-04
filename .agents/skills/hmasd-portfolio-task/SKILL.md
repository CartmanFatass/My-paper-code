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

Compare directions at their honest claim ceilings. Do not reward a direction merely for producing
more formal artifacts, and do not penalize a bounded empirical direction for lacking a theorem,
exact support census, bit identity, transfer evidence, or deployment assurance that its current
claim does not require. When the project objective is performant MARL, prioritize real algorithm
implementation and decision-relevant empirical evidence unless the proposed claim itself requires
C-FORMAL work.

Distinguish technical success, bounded task competence, comparative algorithm advantage,
cross-scenario transfer, safety, and deployment. Evidence for an earlier claim does not silently
promote a later one.

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

## Persistent Pro decision node

Before changing direction priority, capacity, lifecycle, fusion, separation, registering a new
direction, or selecting the next cross-direction investment, Root must use
`$hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision`. Every packet binds to
the single persistent conversation key `portfolio:cross_direction`, lists every direction in scope,
and includes the current Portfolio snapshot, this evidence specification, the selected evidence
class and claim ceiling, plus the exact direction/evidence paths needed for the decision. The fixed
Transport task creates the provider conversation on first use and reuses its exact conversation ID
for all later Portfolio rounds.

A complete archived Pro response that decides the posed question at its declared evidence class is
the Portfolio proposal. Root records it with its evidence and bounded rationale in a decision record
and in `PORTFOLIO.md`; the owner ratifies it from that record (an unratified proposal whose actions
are reversible takes effect after the audit window stated in the record). Root does not replace or
override it with a local-model judgment. If Pro reports missing connector access or insufficient
evidence, Transport has not archived a complete response, or the answer rejects bounded empirical
work solely for lacking an unrequested stronger class, no class-correct Portfolio decision exists:
the question parks (AGENTS.md section 3), Root drives other directions, and nothing is decided
provisionally at this tier. Root may continue reversible evidence collection or request a
class-corrected answer but must not convert the mismatch into scientific polarity.

Read `docs/research/portfolio/PORTFOLIO.md` for current state and the relevant `DIRECTION.md` files
for scientific authority. Compare claim ceiling, decision relevance, complementarity, substitution,
reversibility, cost, live external effects, and the smallest discriminating observation.

Transport, implementation, and process status may change sequencing or feasibility; they do not by
themselves determine scientific polarity or lifecycle. Preserve uncertainty and state why the
recommended action would change under a contrary result.

Root records and integrates the final Pro decision in `PORTFOLIO.md`. Outside the Prompt Author and
Transport packet boundary, use ordinary language; no additional response schema is required.
