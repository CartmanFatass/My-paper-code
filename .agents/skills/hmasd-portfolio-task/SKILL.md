---
name: hmasd-portfolio-task
description: Use when the independent Portfolio session plans Root commands, handles execution returns, or compares HMASD direction priority, lifecycle, capacity, fusion, separation, or research investment.
---

# HMASD Portfolio Decisions

OWNER_DIRECT 2026-09-07: this skill belongs to the independent Astra Portfolio (effort selected by the owner)
session in `.codex/hmasd-portfolio.toml`, directly on main. Portfolio plans concrete tasks,
dependencies and return branches; Luna/xhigh Root executes the issued commands, integration,
monitoring and Pro transport. See docs/project/ROOT_OPERATIONS.md.
Portfolio writes its scientific files on main and pushes immediately; coordinate overlapping
Root integrations. Existing Pro/owner authority is unchanged. Portfolio is not a launch gate.

## Delegated specification changes

Apply AGENTS §4.7 to complete Pro-directed specification plans within delegated scope.
Read/archive the full decision, implement its exact authorized plan, and trace the relevant
P1/P2 item through item.py with actual authority, source, affected files and application state.
No additional per-item approval is needed within that delegation. Do not fabricate owner
replies, accept code solely from a rule change or broaden unrelated dispositions.
Use `$hmasd-owner-item` for the maintained item classes and review procedure.

## Core principle

Apply evidence-spec §11.8 to the chosen research question as well as its implementation.
Do not treat exact headroom, full policy-class maxima or complete causal explanation as
eligibility for ordinary learning investment. Compare proposed diagnostic value and known
work with a minimal B; finite/zero-learner is not a cost argument. Cost refusal reopens
the adequacy of the question, not only its execution design. In the existing intake,
return any concrete Pro/spec conflict to that node before applying the affected clause;
a complete answer cannot silently supersede owner instructions or specs. Explicit changes
use the existing authority. No new reviewer layer, approval or launch condition follows.

Choose the smallest investment that can change a direction decision without confusing scientific
value with execution convenience or strength of claim with strength of ceremony.

Keep classification, management grouping, investment, and execution capacity separate. The owner's
two-line framework (`flexible agents` and `flexible skill duration`) classifies research; it does
not imply one retained route per line or a two-route budget. Offer complementary routes when they
share useful learners, controls, interventions or diagnostics. Similar families can share one
agenda with named subdirections without claiming their scientific objects or results are equivalent.
Explain each proposed PARK by its marginal decision value, cost and concrete re-entry condition,
not by a target direction count. An owner follow-up that changes scope reopens that question;
preserve the prior answer and wait for the revised proposal before applying its dispositions.

Before comparing evidence or changing a direction, read the relevant class and decision sections
of `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, with section 11 controlling. Apply the
burden of the evidence class being considered; do not preload unrelated classes or cited history. General mathematical proof is
not the default admission condition for empirical MARL: structural motivation plus bounded toy or
benchmark evidence is scientifically legitimate when the claim ceiling is bounded to that evidence.

## Portfolio responsibilities

Before investing or making a material lifecycle recommendation, Portfolio identifies:

- the exact Portfolio decision question;
- the lowest evidence class able to answer it;
- the strongest claim that class can support and the material non-goals;
- the smallest valid implementation, derivation, counterexample, or experiment that separates the
  live choices; and
- the contrary observation that would change the recommendation.

Every `ACTIVE` direction remains admitted to the research queue. Portfolio plans the target
working set of five concurrently advancing direction/DM chains and names the tasks Root will
dispatch. Root reports actual recipients, status and external facts. Portfolio decides readiness,
ordering, replacement and the next action from the current evidence. This scheduling does not
change lifecycle, priority, scientific meaning or experiment budgets. A queued direction is not
`PARKED`. OWNER_DIRECT 2026-09-07 counts active native work, running experiments and accepted
Pro generation together, once per direction. Unresolved waits and completed returns yield a
slot; accepted Pro generation remains counted. The goal targets two formally entered UAV
validation directions under concrete decision/card references, not a new universal launch gate.

Execution remains remote-first under `.codex/hmasd-compute.toml` within the frozen host/device
boundary. CM owns technical feasibility and exact execution bindings. Root does not invent an
execution alternative or select another direction after a failed admission.

## Plan before dispatch

Use `$hmasd-loop-dispatch` at `.agents/skills/hmasd-loop-dispatch/SKILL.md` for every
Root command, completion/exception return and working-set refill. Its Portfolio section
is the single dispatch procedure: process the whole working set, send all justified
independent commands together and confirm actual native acceptance. This skill retains
scientific comparison, investment, lifecycle and proper-node judgment; Root receives
concrete tasks rather than those judgments to make. Known collection/intake and selected
execution routes continue without an extra Portfolio vote. New scientific choices retain
the existing DM/Pro decision ladder.

Compare directions at their honest claim ceilings. Do not reward a direction merely for producing
more formal artifacts, and do not penalize a bounded empirical direction for lacking a theorem,
exact support census, bit identity, transfer evidence, or deployment assurance that its current
claim does not require. When the project objective is performant MARL, prioritize real algorithm
implementation and decision-relevant empirical evidence unless the proposed claim itself requires
C-FORMAL work.

Distinguish technical success, bounded task competence, comparative algorithm advantage,
cross-scenario transfer, safety, and deployment. Evidence for an earlier claim does not silently
promote a later one.

## Investment fields (owner decision 2026-09-04, revised the same day)

Controlling records: `docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`
and its execution-parallelism clarification,
`docs/research/portfolio/decisions/2026-09-04-five-direction-execution-parallelism.md`; field text:
evidence spec §11.7 and `AGENTS.md` §2. These are comparison inputs and sequencing rules, not launch
gates, exclusion rules, or lifecycle dispositions. All `ACTIVE` directions remain admitted, while
the five-chain direction working set controls which ones advance concurrently; sequencing orders
work and never parks a direction by itself.

- **Headroom record.** Every Portfolio proposal states each in-scope direction's headroom record
  on its host or its absence. A missing record sequences that measurement early (A/RECON when
  computed from existing results, a declared B when a baseline must be trained); it is never a
  reason to stop investing. When compute is contended, a direction with a record sequences ahead
  of one without.
- **Declared MEI.** Compare B signals across directions against each card's own declared minimum
  effect of interest (absolute, relative, or both), not against a repository-wide number and not
  by absolute edge alone. The declared MEI never rewrites a card's result branches.
- **Recast budget one.** A direction at its second Convergence `RECAST` continues (the Pro
  decision is final for its node) but takes the lowest sequencing priority among ACTIVE
  directions: Portfolio sequences other ACTIVE directions first and sends Root the selected commands. It appears in the owner
  digest as `second-recast`; Root does not mutate the lifecycle field, and an owner reply may PARK
  it. Nothing waits for that reply.
- **Usage per valid result, two measures.** `PORTFOLIO.md` carries two columns per direction:
  the compute of each valid result itself, and the total compute of all accepted attempts divided
  by the number of valid results. Each value names its node and device and is `unmeasured` where
  the summary lacks it; a single wall-time number is not used because it mixes hardware, technical
  failure and scientific cost. Portfolio refreshes both with every snapshot and cites them in every
  cross-direction proposal.
- **Fusion and shared assets.** Directions on one host share baseline sets and evidence
  interfaces without fusing. Fusion is proposed only when question, comparator, estimand and next
  object are shown to be materially the same.
- **Owner items.** Every Portfolio proposal awaiting ratification, and every direction
  recommendation a DM returns, is one owner item of kind `portfolio` written with
  `python tools/owner_console/item.py add --direction portfolio --tier portfolio --kind portfolio ...`
  (`$hmasd-owner-item`; never by hand). At every clean boundary Portfolio runs
  `python tools/owner_console/item.py reviews`: a `ratify` instruction is the owner's
  ratification, `refuse` or `amend` is not; then `mark-answered`. Nothing waits for it.

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
direction, or selecting the next cross-direction investment, Portfolio must use
`$hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision`. Every packet binds to
the single persistent conversation key `portfolio:cross_direction`, lists every direction in scope,
and includes the current Portfolio snapshot, this evidence specification, the selected evidence
class and claim ceiling, plus the exact direction/evidence paths needed for the decision. The
project-shared registry creates or binds the provider conversation on first use under the stable
conversation binding key and reuses that exact provider conversation for later Portfolio rounds.
Each default handoff goes to integrated Root, the one Transport execution endpoint declared in `.codex/hmasd-transport.toml` and
sends exactly one completion or terminal-blocker receipt back to the handoff author's declared
`parent_thread_id`. App dispatch omits `model` and `thinking`, preserving the recipient settings; it never
calls `create_thread` or selects a replacement task. The singleton task ID is an execution endpoint,
never a provider-conversation binding. Set the scientific receipt parent to this Portfolio task; Root records its own receipts locally when it is also parent.
The configured provider model is separate from that executor. Honor an explicit owner request
for a new provider conversation or caller-direct execution using the Prompt Author/Transport
exceptions; do not send through both routes or repeat an accepted provider request.

A complete archived Pro response that decides the posed question at its declared evidence class is
the Portfolio proposal. Portfolio records it with its evidence and bounded rationale in a decision record
for the owner to ratify. Existing explicit owner authorization applies within its stated scope;
record it as `OWNER_DIRECT` rather than asking the owner to authorize the same action again.
Discretionary dispositions not covered by that instruction still need owner ratification, and
`PORTFOLIO.md` is updated only with the authorized disposition. Portfolio does not
replace or override the proposal with a local-model judgment. If Pro reports missing connector
access or insufficient evidence, Transport has not archived a complete response, or the answer
rejects bounded empirical work solely for lacking an unrequested stronger class, no class-correct
Portfolio decision exists:
the question parks (AGENTS.md section 3), Portfolio commands independent work through Root, and nothing is decided
provisionally at this tier. Portfolio may commission reversible evidence collection through Root or request a
class-corrected answer but must not convert the mismatch into scientific polarity.

Read the current rows in `docs/research/portfolio/PORTFOLIO.md` and relevant current sections of
`DIRECTION.md` for scientific authority. Follow historical evidence only when the decision needs
it. Root-to-DM/CM handoffs use AGENTS focused-reading guidance: precise section/code pointers and
concise deliverables, not a copied research history. Compare claim ceiling, decision relevance, complementarity, substitution,
reversibility, cost, live external effects, and the smallest discriminating observation.

Transport, implementation, and process status may change sequencing or feasibility; they do not by
themselves determine scientific polarity or lifecycle. Preserve uncertainty and state why the
recommended action would change under a contrary result.

Portfolio records the Pro proposal, obtains the owner's ratification, and integrates the ratified
disposition in `PORTFOLIO.md`. Outside the Prompt Author and Transport packet boundary, use ordinary
language; no additional response schema is required.
