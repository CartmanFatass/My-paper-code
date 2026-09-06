---
name: hmasd-portfolio-task
description: Use when Root is comparing or changing HMASD direction priority, lifecycle, capacity, fusion, separation, or the next research investment.
---

# HMASD Portfolio Decisions

## Current owner boundary — 2026-09-05 explicit renewal

The owner's latest instruction approved the complete CBSC/N3 Pro specification plan and
explicitly delegated future changes of this kind, including their specified Portfolio and
AGENTS updates, to complete final decisions at the proper Pro node. Apply AGENTS §4.7 and
`docs/research/portfolio/decisions/2026-09-05-pro-directed-spec-delegation.md`.
No additional per-item approval is required inside that explicit scope. Read/archive the full
Pro decision, implement its exact plan, and highlight/trace the existing P1/P2 item through
item.py with owner delegation, exact Pro source, affected files and actual status. Do not
fabricate replies, accept code solely from a rule change or broaden unrelated dispositions.
Missing/ambiguous/out-of-scope decisions retain their actual boundary; P3/P4 remain retired.


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

Every `ACTIVE` direction remains admitted to the research queue. Root ordinarily schedules that
queue through a target working set of five concurrently advancing top-level DM chains; choosing
which admitted direction occupies a slot is sequencing, not a new lifecycle decision. Runtime
availability and dependency ownership may change launch order, but Root must not silently turn
scheduling into a priority, lifecycle, exclusion, fusion, separation, or investment decision. A
queued `ACTIVE` direction is not `PARKED`.

Execution placement is remote-first under `.codex/hmasd-compute.toml`. Route new portable
result-bearing invocations to the enabled remote node while the local machine retains the control
plane and acts as a prospectively authorized fallback. This is capacity routing, not evidence or a
direction-priority signal. A node change must preserve the card's declared host/device semantics,
must occur before question-relevant output, and requires a fresh admission on the destination.

## Direction execution working set

The target parallelism is five direction-level DM chains. Count neither Root nor Transport,
CM/implementer/reviewer/critic/verifier/operator children, nor detached result processes as extra
direction slots.

The independent Luna/low experiment monitor is declared in `.codex/hmasd-monitor.toml`.
Follow `docs/project/EXPERIMENT_MONITOR.md`: DM/CM dispatch directly to its app task;
monitor sends ACKs/events to Root, which forwards/wakes the current native DM/CM.
Its own heartbeat replaces the removed Root research heartbeat. It consumes no direction
slot. Integrate meaningful tracking commits; do not poll the same accepted handle in Root.
Preserve owner pause and resolve current child identities before forwarding.

- Refill an open slot at a clean boundary with the most promising runnable `ACTIVE` direction.
  Compare decision relevance, the smallest sufficient evidence class, honest claim ceiling,
  expected information gain, cost/reversibility, current dependency state, and contrary evidence.
- Prefer real algorithm implementation and decision-relevant evidence over ceremony when the
  claim does not require a stronger class. A direction waiting on a Direction- or Portfolio-tier
  dependency yields its slot when another admitted direction can advance.
- Do not interrupt live work to correct temporary overlap above five. Let chains reach clean
  boundaries and do not refill until the working set returns to five.
- Queue membership has no lifecycle or priority effect. Five is not a target count for `ACTIVE`
  directions and does not authorize batch `PARK`, closure, fusion, or absorption.
- Refilling a slot under this recorded owner policy is ordinary sequencing and does not itself
  require a Portfolio Pro round. Any proposed priority, investment, lifecycle, fusion, separation,
  or registration change still uses the Portfolio decision path.
- Consider fusion only on demand, through the Portfolio decision path, after showing that question,
  comparator, estimand, and next object are materially the same. Similar vocabulary, host, or
  reusable baselines is insufficient.

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
  directions: Root admits every other ACTIVE direction's work first. It appears in the owner
  digest as `second-recast`; Root does not mutate the lifecycle field, and an owner reply may PARK
  it. Nothing waits for that reply.
- **Usage per valid result, two measures.** `PORTFOLIO.md` carries two columns per direction:
  the compute of each valid result itself, and the total compute of all accepted attempts divided
  by the number of valid results. Each value names its node and device and is `unmeasured` where
  the summary lacks it; a single wall-time number is not used because it mixes hardware, technical
  failure and scientific cost. Root refreshes both with every snapshot and cites them in every
  cross-direction proposal.
- **Fusion and shared assets.** Directions on one host share baseline sets and evidence
  interfaces without fusing. Fusion is proposed only when question, comparator, estimand and next
  object are shown to be materially the same.
- **Owner items.** Every Portfolio proposal awaiting ratification, and every direction
  recommendation a DM returns, is one owner item of kind `portfolio` written with
  `python tools/owner_console/item.py add --direction portfolio --tier portfolio --kind portfolio ...`
  (`$hmasd-owner-item`; never by hand). At every clean boundary Root runs
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
direction, or selecting the next cross-direction investment, Root must use
`$hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision`. Every packet binds to
the single persistent conversation key `portfolio:cross_direction`, lists every direction in scope,
and includes the current Portfolio snapshot, this evidence specification, the selected evidence
class and claim ceiling, plus the exact direction/evidence paths needed for the decision. The
project-shared registry creates or binds the provider conversation on first use under the stable
conversation binding key and reuses that exact provider conversation for later Portfolio rounds.
Each default handoff reuses the one project Transport task declared in `.codex/hmasd-transport.toml` and
sends exactly one completion or terminal-blocker receipt back to the handoff author's declared
`parent_thread_id`. Dispatch passes `model=gpt-5.6-luna` and `thinking=xhigh` explicitly; it never
calls `create_thread` or selects a replacement task. The singleton task ID is an execution endpoint,
never a provider-conversation binding or receipt destination.
The configured provider model is separate from that executor. Honor an explicit owner request
for a new provider conversation or caller-direct execution using the Prompt Author/Transport
exceptions; do not send through both routes or repeat an accepted provider request.

A complete archived Pro response that decides the posed question at its declared evidence class is
the Portfolio proposal. Root records it with its evidence and bounded rationale in a decision record
for the owner to ratify. Existing explicit owner authorization applies within its stated scope;
record it as `OWNER_DIRECT` rather than asking the owner to authorize the same action again.
Discretionary dispositions not covered by that instruction still need owner ratification, and
`PORTFOLIO.md` is updated only with the authorized disposition. Root does not
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
