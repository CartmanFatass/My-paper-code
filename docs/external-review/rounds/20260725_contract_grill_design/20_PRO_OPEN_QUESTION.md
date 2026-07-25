# Rule on the contract-grill mechanism itself

```text
round=20260725_contract_grill_design
branch=untied-k
semantic_author=project_manager
scientific_authority=external_pro
artifact_scope=workflow_governance_not_science
predecessor_round=20260725_g20r2_prefreeze_grill
science_status=FROZEN_by_user_pending_your_CHANGES_REQUIRED_rework
compute_spent=none
iteration_consumed=false
```

## Evidence to read

- `docs/external-review/rounds/20260725_contract_grill_design/20_PRO_OPEN_QUESTION.md`
- `docs/project/CONTRACT_GRILL_DESIGN.md`
- `docs/external-review/rounds/20260725_g20r2_prefreeze_grill/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260725_g20r2_prefreeze_grill/21_PRO_OPEN_RAW.md`
- `docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md`
- `AGENTS.md`
- `docs/project/AGENT_CONTEXT.md`
- `.claude/agents/hmasd-implementer.md`
- `.claude/agents/hmasd-reviewer.md`
- `docs/project/IMPLEMENTER_TIER_TEST.md`
- `docs/project/PRO_FIRST_LOOP_PROPOSAL.md`

## Why you are being asked this

Your last ruling was `CHANGES_REQUIRED` on a contract I had already built ~5,700
lines against. The user has frozen scientific advancement until the **process**
that allowed that is fixed.

The diagnosis: our pre-freeze check is a fixed five-question checklist, and it
**passed** the G20R2 contract while that contract contained all nineteen findings
you and an independent adversarial reader later produced. A checklist asks what
its author thought to ask, and the author was making the errors.

The proposed fix is in `CONTRACT_GRILL_DESIGN.md`: a `fable`-class adversarial
reader discovers unasked decisions and establishes repository facts; you retain
all scientific authority; the grill moves ahead of implementation.

**This document is a governance artifact, not science.** But its content is
scientific — a claim about which questions matter for an identification-screen
contract — and I have no basis for asserting that set is right. Two further
points make this your question rather than mine:

- Archetypes **you** add are by construction not derived from the nineteen
  findings, so they are the only genuine out-of-distribution test material we can
  obtain. Without them the "true holdout" layer of our validation is empty and
  the whole exercise is circular.
- I must not set the acceptance thresholds for a mechanism I designed, having
  already seen the case it will be graded on.

Answer everything in one reply; follow-ups are conditional on your own rulings.

---

## Q1. Is the archetype set right?

Sixteen archetypes are proposed in `CONTRACT_GRILL_DESIGN.md`, each anchored to a
real failure. Twelve are derived from the G20R2 nineteen; four were added by
review (13 initial-state reachability, 14 decision-time availability and leakage,
15 comparator exposure matching, 16 intervention-versus-natural-policy transport).

**Q1. For a contract that freezes an estimand, gates, data roles and a first-match
result system, which question classes are missing, and which are redundant or
low-yield enough to cut?**

- **Q1a — for each class you add.** Give the archetype and one concrete instance
  from this project's history if one exists, so it can be encoded the way the
  others are. If no instance exists here, say so — that class then belongs in the
  holdout set rather than the casebook.
- **Q1b — for each you would cut.** Is it redundant with another, or genuinely
  low-yield? These differ: a redundant class inflates reviewer burden, a low-yield
  one merely wastes reader time.
- **Q1c.** Is archetype 13 correctly separated from archetype 10? My claim is that
  "is this threshold reachable given estimator noise" does not cover "does the
  learning dynamics have an absorbing state", and that conflating them is what let
  the original zero fixed point through. Confirm or correct.

## Q2. Which archetypes belong at which gate?

Gate A runs before any implementation exists; Gate B-core after a proof-sized
skeleton; Gate B-delta on the shell's semantic increment.

**Q2. Assign the archetypes to gates. Which must be answered before any
implementation, and which cannot be answered until code exists?**

- **Q2a.** Ranking within Gate A: if reviewer burden forces a cut, which classes
  are load-bearing enough that a contract must not proceed without them?
- **Q2b.** Is the proof-sized skeleton's contents right — estimand calculators,
  data-role split, branch selector, initialization and gradient path, paired
  replay, failure path, serialization? What is missing, and what is in it that
  does not need to be?
- **Q2c.** Is Gate B-delta justified as a separate gate, or does a correctly
  specified assembled-path exercise subsume it? My argument for separation is that
  the exercise proves reachability while a shell can change a conclusion-bearing
  quantity with every path still reachable.

## Q3. Acceptance thresholds — yours to set, not mine

Validation is three tiers: V1 known-case regression on G20R2, V2 out-of-
distribution holdout on older contracts, V3 negative and metamorphic control.
Metrics are critical recall, holdout recall, precision, and reviewer burden.

**Q3. What must this mechanism achieve before it may be trusted, and what result
would mean it should be abandoned rather than tuned?**

- **Q3a.** What **critical recall** — over findings that invalidate an estimand,
  make a branch unreachable, or change the conditioning history — is required at
  V1, and separately at V2?
- **Q3b.** What **false-positive or reviewer-burden** level makes the mechanism a
  net loss? A reader that reaches fifteen of nineteen by asking fifty questions
  has handed you thirty-five irrelevant rulings.
- **Q3c.** Is "V1 proves wiring, only V2 shows transfer, stay experimental until
  V2 passes" the right adoption gate, or should the bar be elsewhere?
- **Q3d.** Every contract we have examined contained defects, so a "clean"
  contract for V3 may not exist and apparent false positives there may be true
  positives nobody found. Is the metamorphic pair — a defective contract and a
  snapshot repaired *only* in that defect — a sound substitute?

## Q4. The authority boundary

The reader may establish facts, trace control flow, construct zero-compute
counterexamples and run read-only diagnostics; it may not decide scientific
acceptance, candidate retirement, branch semantics, experiment authorization or a
successor. An earlier draft said "asks but never answers", which I corrected
because a reader that has *measured* noise at ~`1e-3` against a `1e-8` threshold
should not hide that and force you to redo the diagnostic.

**Q4. Is that line drawn correctly?**

- **Q4a.** Are there fact-establishing operations that should nonetheless be
  withheld from you as pre-digested, because seeing the raw evidence yourself
  materially changes your ruling?
- **Q4b.** Is the five-field per-item output shape the right form for a single
  reply of yours, or does it obstruct you?

## Q5. What this mechanism still cannot catch

**Q5. With Q1–Q4 applied, what class of defect would still reach a bounded screen
undetected?**

I can name one and expect there are others: grilling protects the science and
measurement protects the realization, but a numerical method can be *specified*
correctly, *implemented* to match the specification, and still be the wrong method
for the estimand — and your Blocker 1 last round (the suffix-noise slice) was
found by you reading code, not by any gate we have proposed.

## Boundary

Not asking you to review file layout, factoring, naming, test construction, or
the choice of model for the adversarial reader. Those are mine. Everything above
is asked because it determines what questions ever reach you — which is
upstream of every scientific ruling you will make on this project.
