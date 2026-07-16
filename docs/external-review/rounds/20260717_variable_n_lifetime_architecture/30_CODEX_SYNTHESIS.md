# Codex Evidence-Weighted Synthesis

## Scope and status

This synthesis compares two blind divergent reviews without assigning authority
by model identity:

- `11_GEMINI_DIVERGENT_RAW.md`, supplemented by the bounded original-PDF audit
  in `13_GEMINI_PDF_AUDIT_RAW.md`;
- `21_PRO_OPEN_RAW.md`.

It is an architecture disposition, not an experiment authorization. R55 remains
paused. No reward, environment, threshold, training budget or intrinsic term is
changed here.

## High-confidence convergence

Both reviewers independently converge on five useful points.

1. **Variable membership and variable skill lifetime should share one runtime
   object.** The natural state is an active set of member commitments rather
   than a fixed `[time, slot]` tensor. Membership changes open/close member
   lifecycles; skill decisions open, continue or close skill commitments.
2. **Lifecycle ownership is not policy-visible identity.** The collector needs
   an opaque key to route survivor/rejoin recurrent state, active skill, age and
   open credit. That key must not become an agent-ID or slot feature of the
   policy.
3. **Probability and time credit must be event-owned.** Executed policy factors,
   their actual masks/prefixes, real elapsed time and bootstrap boundary belong
   to the same ledger. Physical-time discounting must use `gamma^Delta`; macro
   trace depth must not advance through fabricated high-level decisions.
4. **Set/graph/field/slot mechanisms are representation candidates, not separate
   algorithms.** A design should select the smallest sufficient active-set
   representation instead of stacking global attention, slots, residuals,
   sparse graphs and a team latent.
5. **R55 should not run as drafted.** Its fixed-membership, fixed-horizon direct
   edge cannot distinguish the final joint variable-`N` plus variable-lifetime
   architectures.

The event ledger is a correctness spine and a useful unifying abstraction. It
is not, by itself, an algorithmic contribution: a strong ordinary-MARL baseline
can and should use the same lifecycle table, ragged packing and duration-correct
credit.

## Claims that require correction

### Gemini review

The following Gemini claims are too strong for the cited evidence.

- **Anonymous dynamic sets do not fundamentally preclude autoregression.** A
  uniformly sampled, identity-free permutation of the current event frontier
  can be recorded and teacher-forced. Its order probability is external and
  parameter-independent; a learned pointer is only one option, not the only
  mathematically valid option. A deterministic observation-derived order with
  recorded random tie-breaking is another possible contract. The real risk is
  order-induced semantic leakage or variance, not probability impossibility.
- **The R49 result already weakens the impossibility claim.** It established
  permutation/padding invariance, exact replay and prefix-gradient support at
  the interface level. It did not establish usefulness, but it shows that
  anonymous active-set representation and an applied prefix can coexist.
- **ACAC is not a definitive solution.** It is strong evidence for separating
  physical-time `gamma` from event-depth `lambda` under a fixed roster. It does
  not solve episode-internal join/leave/rejoin, policy-owned event-time
  likelihood, survivor state, or HMASD skill semantics.
- **IARO does not prove that barriers destroy heterogeneous-lifetime utility.**
  Its synchronous joint-option contract is a relevant counterexample/design
  warning, not a causal impossibility theorem for this project.
- **Hybrid Field-Slot is not currently justified as the default encoder.** R54
  failed the full-set prerequisite and quarantined the fixed-slot hybrid. The
  literature makes sparse/local representations plausible, but does not revive
  that specific compression path.
- The proposed fixed-`N`, variable-delay test would again isolate only one half
  of the final target. It may characterize asynchronous anti-coordination, but
  it should not become another successor gate that postpones joint `N_t + T_i`
  evidence.

### Open Pro review

The open Pro review is stronger on reduction baselines and evidential caution,
but three points need modification.

- **H0 must be strengthened, but named honestly.** Active-only ragged packing,
  survivor state, per-agent scheduling and an agent-centric SMDP ledger are a
  strong ordinary-MARL reduction. They are not the naive fixed-`N_max` padded
  baseline described in the common brief. This baseline absorbs most execution
  infrastructure, leaving joint conditional assignment as the real algorithmic
  distinction.
- **Sparse relational encoding is not yet a required default.** R54 rules out
  one full-set model and one quarantined compression arm, not all global pooling
  or attention. Start with the smallest permutation-compatible encoder that is
  adequate at the intended active-`N`; make sparsification a scaling response,
  not a preinstalled mechanism.
- **The proposed R53 no-training reanalysis is not executable from retained
  artifacts.** `logs/r53_rcma_20260717_010744/` contains only
  `seed/progress.json` and `result/r53_rcma.json`. There is no retained final
  checkpoint or per-decision ledger from which alternate-prefix logits can be
  recomputed. The result JSON records that replay checks passed but does not
  contain weights, contexts or alternate-prefix distributions. Reconstructing
  them would require a new training/replay run and therefore is not the claimed
  zero-run reanalysis.

The open review's self-critique is accepted: event ownership, exchangeability
and duration-correct credit are correctness invariants, not proof that a learned
event editor, autoregressive prefix or discrete skill ontology is irreducible.
However, this project's declared target remains skill-based MARL, so a
non-skill recurrent policy is a reduction baseline, not an automatic replacement
for the research objective.

## Reconstructed portfolio

### F0 — active-set scheduled MARL reduction

**Retains:** shared recurrent actor/critic, anonymous active-set encoder,
survivor/rejoin state table, skill-conditioned low actor when used, and the same
event/SMDP ledger.

**Replaces:** joint autoregressive editing with conditionally independent
per-member continuation/selection given an invariant active-set context.

**Purpose:** the strongest ordinary-MARL explanation. It prevents lifecycle,
ragged batching or `gamma^Delta` accounting from being misreported as the new
algorithm.

### F1 — exchangeable event-frontier commitment editor

**Retains:** the HMASD individual skill bottleneck; applied working-roster
prefix; later-on-earlier conditional assignment; exact behavior probability;
environment-agnostic skill-semantic pressure where already justified.

**Replaces:** fixed roster slots, full-team synchronous renewal, decorative team
latent, explicit discrete duration action and full-roster decoding when only a
small event frontier changes.

**Adds:** one active commitment set; explicit external `JOIN/LEAVE/REJOIN`
lifecycle events; identity-free recorded order over the policy-owned event
frontier; continuation/termination plus new-skill marks; survivor continuity;
duration-aware event returns.

This is the leading architectural family, not yet a proven algorithm. Its
algorithmic content over F0 is the learned joint conditional distribution over
concurrent commitment edits, not the ledger or encoder.

### F2 — decentralized skill-hazard alternative

**Retains:** the same active commitment state, skill bottleneck, lifecycle table,
active-skill context and duration-aware credit.

**Replaces:** event-frontier autoregression with per-member independent
continuation/termination/skill factors. Any capacity conflict must be removed by
a pre-sampling feasibility mask or by an explicitly probabilistic joint resolver;
a post-sampling unlogged repair is invalid.

**Purpose:** tests whether shared context is sufficient and whether the F1
prefix carries real cooperative information.

### Deferred — learned continuous-time point process

A marked point-process controller is structurally distinct, but it adds
integrated hazard, survival likelihood, censoring and competing-risk machinery.
It should remain deferred until a discrete event-frontier formulation shows that
fixed opportunity quanta, rather than coordination or credit, are the binding
limitation.

## One unifying architecture principle

The literature should be absorbed as one principle rather than a module list:

> Represent the anonymous active commitment set once; route lifecycle state in
> the runner; let a single policy distribution own every policy-controlled
> continuation or edit; and derive replay probability and duration-aware credit
> from the same event record.

Under this principle:

- ACE contributes event readiness/execution semantics;
- ACAC contributes agent-centric duration-aware return semantics;
- InforMARL/ExpoComm contribute alternative active-set relation encoders;
- HMASD contributes executable individual skills and applied-prefix cooperative
  assignment;
- R30 contributes exact KEEP/SET teacher forcing;
- R49 contributes the feasibility of anonymous incremental set/prefix
  interfaces;
- slots, mean fields, team latents and sparse graphs are admitted only after a
  demonstrated information or scaling need.

No new intrinsic reward is implied. Intrinsic input remains environment-agnostic
and cannot use task goals, contacts, phases, distances, success predicates or
external reward.

## Correctness question neither review fully closes

The event-time owner must be explicit.

- If edit opportunities are **exogenous**, silent physical steps have no policy
  probability; the policy owns only KEEP/SET at the opportunity.
- If the agent **learns when to terminate/request**, the probability of surviving
  without an event is also policy-owned. The ledger must store either every
  continue factor or its exact aggregated log-survival, followed by termination
  hazard and skill-mark probability. Omitting these factors makes the realized
  lifetime likelihood wrong.

Gemini's “agent triggers independently” and the open review's “no fabricated
rows” are compatible only after this distinction is fixed. The final convergent
review must choose a minimal discrete contract and state where each likelihood
factor and return lives.

## Evidence strategy and R55

`R55-ABRP-G0` should be **REPURPOSED conceptually and remain unexecuted**. Its
underlying question—whether later assignments use earlier applied decisions
beyond deterministic support—remains relevant, but the proposed R53 artifact
reanalysis is unavailable.

Do not replace it immediately with another isolated gate. The preferred next
boundary is an architecture contract followed by one shared evidence-bearing
testbed that actually contains both:

1. episode-internal anonymous join/leave/rejoin with survivor continuity; and
2. naturally different per-member useful commitment durations.

F0 and F1 should share the lifecycle table, encoder, low actor, skill semantics,
reward, budget and event-credit implementation; the intended intervention is
only conditionally independent versus prefix-conditioned concurrent edits. If a
cheaper existing analysis becomes available, it is admissible only if its
artifacts really exist and at least two outcomes cause a portfolio integration
or stop decision.

This avoids two previous failure patterns: treating execution plumbing as the
innovation, and serially generating toy gates that never expose the final joint
capability.

## Questions for the convergent reviewer

1. Is F1 the correct leading architecture, or can F0/F2 express the same joint
   coordination without a load-bearing prefix?
2. What is the minimal exact discrete event-time contract: exogenous staggered
   opportunities, learned discrete hazard with aggregated survival likelihood,
   or another option? State all behavior-probability factors.
3. How should an identity-free event-frontier order be sampled and replayed
   without turning lifecycle keys into semantic slots?
4. Which HMASD cooperative function must be preserved after retiring a
   decorative team latent: applied-prefix assignment, a team semantic objective,
   or both? Do not add an ungrounded reward.
5. Given that the R53 checkpoint/ledger are absent, should the project proceed
   directly to one joint-capability testbed/implementation contract, or is there
   a genuinely available existing evidence source that changes an integration
   decision?
6. Return one architecture disposition and one executable next boundary, not a
   chain of successor gates.
