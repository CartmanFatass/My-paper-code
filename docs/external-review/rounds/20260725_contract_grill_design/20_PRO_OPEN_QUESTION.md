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
pre_send_adversarial_pass=applied_eight_findings_incorporated
```

## Evidence to read

- `docs/external-review/rounds/20260725_contract_grill_design/20_PRO_OPEN_QUESTION.md`
- `docs/project/CONTRACT_GRILL_DESIGN.md`
- `docs/external-review/rounds/20260725_g20r2_prefreeze_grill/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260725_g20r2_prefreeze_grill/21_PRO_OPEN_RAW.md`
- `docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md`
- `AGENTS.md`
- `docs/project/AGENT_CONTEXT.md`
- `docs/project/PRO_FIRST_LOOP_PROPOSAL.md`
- `docs/project/IMPLEMENTER_TIER_TEST.md`
- `.claude/agents/hmasd-implementer.md`
- `.claude/agents/hmasd-reviewer.md`

## Why you are being asked this

Your last ruling was `CHANGES_REQUIRED` on a contract I had already built ~5,700
lines against. The user has frozen scientific advancement until the **process**
that allowed that is fixed.

The diagnosis: our pre-freeze check is a fixed five-question checklist, and it
**passed** the G20R2 contract while that contract held all nineteen findings you
and an independent adversarial reader later produced. A checklist asks what its
author thought to ask, and the author was making the errors.

The proposed fix is `CONTRACT_GRILL_DESIGN.md`. A `fable`-class adversarial reader
discovers unasked decisions and establishes repository facts; you retain all
scientific authority; the grill moves ahead of implementation.

**One correction to my own framing before you start.** An earlier draft of this
question claimed that archetypes you add would be "by construction" out-of-
distribution test material. That is false and the pre-send pass caught it: you
authored nine of the nineteen findings, and you will have read the sixteen
archetypes before adding any. Your additions are conditioned on both. I no longer
claim they give us clean holdout material — which makes **Q5's** question about
what V2 is actually measured against more important, not less.

Answer everything in one reply; follow-ups are conditional on your own rulings.

---

## Q1. Is the archetype set right — and is the coverage matrix?

Sixteen archetypes are proposed, each anchored to a real failure. Twelve derive
from the G20R2 nineteen; four were added by the adversarial reader (13 initial-
state reachability, 14 decision-time availability and leakage, 15 comparator
exposure matching, 16 intervention-versus-natural-policy transport).

Separately and less visibly, the design carries a **thirteen-row coverage matrix**
— a different list from the archetypes. It is the scope over which the reader may
claim *"within the listed scope, nothing further found"*. A missing row would make
a whole dimension's absence truthfully reportable as exhaustion.

**Q1. Which question classes are missing from the sixteen, and which are redundant
or low-yield enough to cut?**

- **Q1a — for each class you add.** Give one concrete instance from this project's
  history if one exists, so it can be encoded as the others are. If none exists
  here, say so: that class then belongs in holdout material rather than the casebook.
- **Q1b — for each you would cut.** Redundant with another, or genuinely low-yield?
  A redundant class inflates your burden; a low-yield one merely wastes reader time.
- **Q1c.** Is archetype 13 correctly separated from archetype 10? My claim is that
  "is this threshold reachable given estimator noise" does not cover "does the
  learning dynamics have an absorbing state". Confirm or correct.
- **Q1d.** Are the thirteen coverage-matrix rows the right exhaustion scope for the
  "nothing further found" claim, and which row is missing?

## Q2. Which archetypes belong at which gate?

Gate A runs before any implementation exists; Gate B-core after a proof-sized
skeleton; Gate B-delta on the shell's semantic increment.

**Q2. Assign the archetypes to gates. Which must be answered before any
implementation, and which cannot be answered until code exists?**

- **Q2a.** Ranking within Gate A: if burden forces a cut, which classes are
  load-bearing enough that a contract must not proceed without them?
- **Q2b.** What must Gate B-core be able to **observe** in the skeleton? Stated as
  observables rather than as a module list, so a later engineering restructure
  cannot read as violating your ruling.
- **Q2c.** Is Gate B-delta justified as a separate gate, or does a correctly
  specified assembled-path exercise subsume it? My argument for separation: the
  exercise proves reachability, while a shell can change a conclusion-bearing
  quantity with every path still reachable.

## Q3. What closes a gate — the question the design has no answer to at all

The design says when each gate fires and what it reads. **It states no pass
criterion for any of them.** The decision ledger admits an `open` ruling state,
and nothing says whether implementation may begin while entries are `open`, or who
declares the reader's coverage sufficient.

This is the most dangerous omission in the proposal, because if I close the gate
on my own judgement that enough has been checked, the mechanism reproduces the
original failure exactly. G20R2 entered implementation because its author decided
the checking was done.

**Q3. What state must the decision ledger be in for a gate to close?**

- **Q3a.** May implementation begin while any entry is `open`? If some may remain
  open, which kinds?
- **Q3b.** Who declares the reader's coverage sufficient — you against the coverage
  matrix, a mechanical rule, or me? If me, what constrains it?
- **Q3c.** Should the ledger distinguish *awaiting your ruling* from *decided under
  my own authority and never sent*? As specified it cannot, so the standing sweep
  for unregistered protected choices cannot tell a pending decision from one that
  silently bypassed you — the exact class this mechanism exists to police.
- **Q3d.** Certificate voiding as written is asymmetric: only **your** change to a
  protected decision voids prior certificates, so a change I make leaves them
  standing. Should my amendments void them too, and should the ledger record
  inter-decision dependencies so a re-review trigger can name "the ruling on
  decision A changed" rather than voiding everything?

## Q4. Do the reader's findings reach you unfiltered?

The division of labour has the reader discover and you rule. But `AGENTS.md`
requires the Project Manager to author every question sent, so **I sit between the
reader and you**, and the design never says whether I may triage, merge or drop
items before they reach you. That is a filter operated by the party whose blind
spots the mechanism exists to compensate for — the one channel through which a
discovered defect can die unruled.

Relatedly, the architecture assigns discovery to the reader alone. Our overlap on
G20R2 was roughly five of nineteen, and Blocker 1 — the suffix-noise slice that
invalidated Stages A, B1 and B2 — you found by reading code, not by answering a
question. A question-mediated-only channel loses that.

**Q4. Should reader findings reach you unfiltered, and should you retain your own
unmediated read?**

- **Q4a.** If I may triage, what rule governs what I am permitted to drop, and must
  dropped items still be listed so you can overrule the omission?
- **Q4b.** Should Gate A carry a standing open invitation for your own unmediated
  read of each contract, in addition to rulings on reader-raised items?

## Q5. Acceptance thresholds, and who grades

Validation is three tiers: V1 known-case regression on G20R2, V2 out-of-
distribution holdout on older contracts, V3 negative and metamorphic control.
Metrics: critical recall, holdout recall, precision, reviewer burden.

I ceded threshold-setting to you because I designed the mechanism and have seen
the case it will be graded on. The pre-send pass observed that **me grading recall
against your thresholds is the same conflict**, and it is right.

**Q5. What must this mechanism achieve before it may be trusted, what would mean
abandoning rather than tuning it, and who grades?**

- **Q5a.** Required **critical recall** — over findings that invalidate an estimand,
  make a branch unreachable, or change the conditioning history — at V1, and at V2.
- **Q5b.** What false-positive or burden level makes it a net loss? A reader that
  reaches fifteen of nineteen by asking fifty questions has handed you thirty-five
  irrelevant rulings.
- **Q5c.** Who adjudicates whether a reader finding **matches** a known defect,
  especially a disputed "same archetype, unencoded instance" claim? A lenient
  matcher certifies a bad mechanism at any threshold you set.
- **Q5d.** Who selects the V2 holdout contracts and what constitutes their ground
  truth? Selection by me, after seeing what the mechanism is good at, biases the
  one tier the adoption gate rests on. Note the concession made for V3 applies
  here too: every contract we have examined contained defects.
- **Q5e.** Is "V1 proves wiring, only V2 shows transfer, stay experimental until
  V2 passes" the right adoption gate? And **what does a pass license while
  experimental** — the frozen G20R2 rework will pass through this grill before V2
  can exist. If V2 later fails, are experimental-period certificates revoked and
  their contracts regrilled?
- **Q5f.** Is the metamorphic pair — a defective contract and a snapshot repaired
  *only* in that defect — a sound substitute for a clean negative control?

## Q6. The authority boundary

The reader may establish facts, trace control flow, construct zero-compute
counterexamples and run read-only diagnostics; it may not decide scientific
acceptance, candidate retirement, branch semantics, experiment authorization or a
successor. An earlier draft said "asks but never answers", corrected because a
reader that has *measured* noise at ~`1e-3` against a `1e-8` threshold should not
hide that and force you to redo the diagnostic.

**Q6. Is that line drawn correctly?**

- **Q6a.** Are there fact-establishing operations that should nonetheless be
  withheld as pre-digested, because seeing raw evidence yourself changes your ruling?
- **Q6b.** Is the five-field per-item output shape the right form for one reply of
  yours, or does it obstruct you?

## Q7. What this mechanism still cannot catch

**Q7. With Q1–Q6 applied, what class of defect would still reach a bounded screen
undetected?**

I can name one and expect others: grilling protects the science and measurement
protects the realization, but a numerical method can be specified correctly,
implemented to match the specification, and still be the wrong method for the
estimand.

## Boundary

Not asking you to rule on file layout, factoring, naming, test construction, the
per-item field order, the number of reader passes per gate, or the mechanics of
constructing a metamorphic pair. Those are mine.

I am **no longer** excluding the choice of reader architecture. An earlier draft
excluded "the choice of model for the adversarial reader", which the pre-send pass
correctly identified as shielding the *single-reader architecture* behind a
model-choice exclusion. The model is mine; whether discovery should rest on one
reader is yours, and it is asked at Q4b.
