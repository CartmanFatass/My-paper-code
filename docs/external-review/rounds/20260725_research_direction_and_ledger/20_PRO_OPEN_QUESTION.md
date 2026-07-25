# The intention this branch exists for, and which direction to explore first

```text
round=20260725_research_direction_and_ledger
branch=untied-k
semantic_author=project_manager
scientific_authority=external_pro
artifact_scope=research_direction_not_a_contract_freeze
predecessor_round=20260725_contract_grill_design
compute_spent=none
iteration_consumed=false
```

## Evidence to read

- `docs/external-review/rounds/20260725_research_direction_and_ledger/20_PRO_OPEN_QUESTION.md`
- `docs/project/RESEARCH_GOAL.md`
- `docs/project/EXPLORATION_LEDGER.md`
- `ha_ctse_process/config.py`
- `docs/project/ExpRecord.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/00_REVIEW_BRIEF.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`

## First, a correction you are owed

You have spent six rounds on this branch ruling on whether a delayed-credit
estimator can be identified — G20, G20R, G20R2, and most recently the nine
blockers that produced a G20R3 draft. Those rulings were correct and I adopted
them in full.

**They were also answering questions that had drifted from what this branch is
for.** The user identified it today. `untied-k` exists to make the **skill period
`k` of an individual agent variable**, and that goal appeared in the bootstrap
round of 2026-07-24 and in **no active document thereafter**. Around twenty
governance documents existed and not one stated the research intention, so each
round optimized for locally-defensible correctness against a missing reference.

The identification line is now **on hold**, not deleted. `RESEARCH_GOAL.md` is the
document that should have existed from the start. I am telling you this plainly
because you drove that line in good faith on the questions I put to you, and
because Q5 below asks you to rule on whether holding it is right.

## The actual intention

HMASD fixes the skill period `k`. Asynchronously, one period is wrong for
everyone: a UAV acting as a **relay** holds a role that persists and suits a long
period, while a **service** drone re-decides as users move and suits a short one.

The difficulty is the contribution, not the unbinding:

> Letting each agent choose its own period **massively expands the action space**
> and makes exploration prohibitive. The proposal is to reintroduce tractability
> with an assumption or constraint that collapses the space onto a small set of
> periods, accepting a **suboptimal** result in exchange for a search cost that is
> actually payable.

The claim is explicitly not optimality. It is that a constrained variable-`k`
policy beats fixed `k` at a search cost far below unconstrained variable `k`.

The user's sharpening, which I think is the important move: **the primitive is
stable versus flexible role, not long versus short `k`.** Identify which agents
hold persisting roles; the period is a consequence. That also splits the claim in
two, and the first half stands alone even if the second fails.

## What the code already has — corrected

An earlier draft of this section stated several of these facts wrongly in the
direction that favoured my preferred plan. An adversarial pre-send pass caught it
and the corrections are given here rather than quietly fixed, because the
original framing would have foreclosed the alternative in Q6.

Verified true:

- The high policy emits `duration_logits` beside `skill_logits`.
- The space is discretised: `skill_lifetime_candidates = (3, 7, 13, 24)`, in
  high-level intervals, so the primitive horizon is `candidate * k`.
- The config comment on those candidates reads *"UAV service/relay formation is a
  long-horizon task"* — the role split, written down and unused.

Corrected:

- **`legacy_duration` is not "the live default" in any research sense.** It is the
  assigned value, but the comment two lines above it reads *"Legacy duration
  editing remains available only as the **frozen comparator**; R30 must be
  selected explicitly."*
- **The fixed-clock challenger did not simply fail.** Only the 320k pairing was
  stopped without an M1–M4 outcome. An adaptive R30 arm completed and anchored
  R31/R32/R33, where its lifetime-breadth and SET-safety gates passed. My claim
  that legacy was "the only controller with a completed arm" was false.
- **R30 exists because of a recorded structural defect of legacy.** The fixed
  clock was designed to *"permit lifetimes beyond the old four-block cap without
  short-segment high-sample bias"* — a bias of exactly the mechanism I was
  proposing to build on.
- **Duration collapse has been observed, not merely anticipated.** `config.py`
  records that *"R16.5 showed 0.1 intrinsic pressure can induce duration-collapse
  pathology, while 0.05 was the cleaner stabilized base"*, and the entropy floor
  sits under an "R16.5 stabilization" heading. It is absent from `ExpRecord`
  because R16.5 predates it, which is not the same as unobserved.
- **The completed legacy arm is not the configuration D1 would run.** It used
  frozen duration choices `(1,2,3,4)` at `k0=10`. The current candidate set
  `(3,7,13,24)` has no completed run anywhere, so "the path trains" is unverified
  for the path D1 actually exercises.

And two mechanisms that can **fabricate** a collapse reading on this path:

- short-segment high-sample bias in legacy duration editing;
- Z-boundary atomic reassignment, where `config.py` warns that if `team_intent_k`
  does not exceed the longest lifetime candidate it *"structurally truncates long
  duration choices and fabricates collapse."*

---

## Q1. Is the framing a contribution?

**Is "unbinding `k` explodes the action space; we constrain it back and accept
suboptimality for a payable search cost" a defensible contribution, or a
restatement of standard practice?**

- **Q1a.** If defensible, what is the smallest claim it supports, stated as we
  would have to state it in a paper?
- **Q1b.** If it is too close to ordinary option-duration or semi-MDP work, what
  would have to be true of the result for it to be non-obvious?

## Q2. Is role stability the right primitive?

The user's proposal is to identify **stable versus flexible roles** and let the
period follow, rather than choosing long or short `k` directly.

**Q2. Is that the right primitive, and is it measurable without hand-labelling?**

- **Q2a.** If yes, what is the soundest measurable definition of role stability
  here — skill-assignment churn, dwell time, the duration posterior's own
  entropy, reward sensitivity to re-decision frequency, or something else?
- **Q2b.** Does splitting the claim in two — *roles are separable*, then *period
  conditioned on role beats fixed `k`* — actually give a first half that stands
  alone, or does the first half only mean something given the second?

## Q3. Order the exploration ledger

`EXPLORATION_LEDGER.md` holds five active directions with build, compute and
review costs. The user's policy is: stay open, order by cost, validate the
cheapest first unless a direction is designated.

**Q3. Which direction should be explored first, and in what order thereafter?**

- **Q3a.** What would change your ordering — a result, a cost that I have
  misjudged, or a direction missing from the ledger entirely?
- **Q3b.** Is any listed direction one you would drop outright rather than defer?

## Q4. Is measuring collapse first the right move?

D1 proposes one instrumented run on the existing `legacy_duration` path, logging
duration usage entropy, the histogram over the four candidates, and per-agent
assignment churn. Build cost is logging, review cost is zero, and it is intended
to settle both premises at once.

**Q4. Is that the correct first experiment, or is there something cheaper that
settles more?**

- **Q4a.** What must that run log for its result to be interpretable — in **both**
  directions? An earlier draft asked only what would make a *no-collapse* reading
  genuine, which is asymmetric in favour of the paper's preferred answer. So:
  what would make a **collapse** reading a genuine property of the mechanism
  rather than an artefact of short-segment high-sample bias or Z-boundary
  truncation; and what would make a **no-collapse** reading a genuine refutation
  rather than an artefact of budget, seed or scenario?
- **Q4b.** Given that collapse was already observed at R16.5 under `0.1` intrinsic
  pressure and that `0.05` was adopted as the stabilized base, is the open
  question now *whether* collapse occurs, or *whether it recurs under the current
  reward-pure defaults without intrinsic pressure*? If the latter, D1's framing
  needs restating.
- **Q4c.** If duration does not collapse under current defaults, is the
  contribution dead, or does it re-form around something else?

## Q5. Is holding the identification line right?

Delayed credit across periods of unequal length is a real dependency: a variable
period changes what a credit signal attaches to. G20R3 is drafted against your
nine blockers and held.

**Q5. Is holding it correct, or does a variable-`k` claim require identification
resolved first?**

If it is required, say what minimum part of it is required — I would rather build
the blocking fragment than the programme.

## Q6. Which mechanism should carry the variable-`k` line?

This is the question the earlier draft silently answered by assumption, and it may
be the most consequential one here. Every ledger direction presumes the **legacy
duration head**: D1 instruments it, D3 and D4 build constraints on it.

But legacy carries the recorded short-segment high-sample bias that R30 was
designed to remove, and **R30's `KEEP/SET` clock is itself a variable-effective-`k`
mechanism** — a lifetime emerges from repeated KEEP decisions rather than from a
sampled duration. That arguably makes it a third candidate constraint alongside
the two in `RESEARCH_GOAL.md`, and a missing sixth ledger entry.

**Q6. Should the variable-`k` line run on the legacy duration head, or on the
R30 KEEP/SET clock?**

- **Q6a.** If R30, does the emergent-lifetime formulation change what "role
  stability" means, or is it the same quantity measured differently?
- **Q6b.** If legacy, does the short-segment high-sample bias contaminate a
  duration-usage measurement taken on it — and if so, what correction is required
  before D1's reading means anything?
- **Q6c.** You previously ruled `MODIFY R30` and accepted its corrections. Does
  that ruling bear on this choice, and did it settle anything I should not be
  reopening?

## Boundary

Not asking you to rule on implementation, file layout, or how the ledger is
formatted. I am asking what is worth exploring and in what order, because the
last six rounds show I cannot be trusted to tell on my own when a line has
stopped serving the goal.
