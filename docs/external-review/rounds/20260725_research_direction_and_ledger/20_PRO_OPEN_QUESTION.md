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

## What the code already has, checked rather than assumed

- `high_controller = "legacy_duration"` is the **variable-duration mode and the
  live default**; the alternative `r30_fixed_clock_ar_edit` is the fixed-clock
  challenger.
- The high policy already emits `duration_logits` beside `skill_logits`.
- The space is already discretised: `skill_lifetime_candidates = (3, 7, 13, 24)`,
  in high-level intervals, so the primitive horizon is `candidate * k`.
- The config comment on those candidates already reads *"UAV service/relay
  formation is a long-horizon task"* — the role split, written down and unused.
- `EXP-20260714-r30-fixed-clock-paired-320k` is recorded **stopped, superseded
  before completion**: the legacy arm completed, the treatment was stopped, and
  **no M1–M4 outcome exists**. The fixed-clock challenger never won.

And one gap that decides the paper's shape:

- `duration_entropy_floor_*` exists, default-off, described in-code as *"a
  one-variable guard for duration collapse"* — so collapse is **anticipated by the
  engineering and observed nowhere in `ExpRecord`.**

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

- **Q4a.** What must that run log for its result to be interpretable — and what
  would make a "no collapse" reading a genuine refutation of the premise rather
  than an artefact of budget, seed, or scenario?
- **Q4b.** If duration does **not** collapse, is the contribution dead, or does it
  re-form around something else?

## Q5. Is holding the identification line right?

Delayed credit across periods of unequal length is a real dependency: a variable
period changes what a credit signal attaches to. G20R3 is drafted against your
nine blockers and held.

**Q5. Is holding it correct, or does a variable-`k` claim require identification
resolved first?**

If it is required, say what minimum part of it is required — I would rather build
the blocking fragment than the programme.

## Boundary

Not asking you to rule on implementation, file layout, or how the ledger is
formatted. I am asking what is worth exploring and in what order, because the
last six rounds show I cannot be trusted to tell on my own when a line has
stopped serving the goal.
