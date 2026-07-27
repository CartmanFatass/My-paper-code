---
name: hmasd-acceptance-gate
description: Use when deciding what proof a change needs, when Stage A or Stage B triggers, how a guard test must be written, and how to read a result without overclaiming. The acceptance side of the loop.
---

# Acceptance, audits, and reading a result

Project Manager only. Load this at a gate — before accepting a diff, before a
Stage A freeze, before Stage B, or when a run returns.

## Acceptance, tests, and review

Every artifact has one acceptance owner. Project Manager accepts project code,
tests, contracts, workflow artifacts, review packages, and reconciliations.
External Pro owns its scoped scientific answer. The experiment operator accepts
nothing; it reports mechanical terminal facts.

Use the smallest proof that can change the decision:

- a helper or schema change gets one focused check;
- a durable bug repair gets one reproducer/regression and focused rerun;
- a runner/analyzer path gets a focused suite and one bounded nonformal exercise;
- protected cross-file work may receive at most one risk-triggered advisory
  review, with another review only after a concrete failure or anomaly.

There is no review-of-review, mandatory independent review for every child,
compatibility suite, coverage target, or paperwork gate. Tests enforce actual
scientific and operational invariants; they do not create another authority.

#### A guard test needs a paired negative

Adopted 2026-07-27 after an internal sweep found six unfailable guards on the
D7.S instrument, on top of the two external review had already named. Every one
shared a cause: **the tests were written from the implementation, so both sides
of the comparison came from the same code path.**

A test claiming a guard protects `X` must carry a perturbation of `X` that
drives the guard **red**. A positive assertion alone is not a guard.

- `assert f(x) == f(x)` may not stand alone. It needs `assert f(x) != f(x')`,
  and `x'` must be drawn from `X`'s **whole declared domain** — every field the
  digest enumerates, not the one the author had in mind.
- **Never assert a post-condition the code structurally guarantees.** A clamped
  value lying inside its own clamp, a sorted list being sorted, a normalized
  vector having unit norm. These read as property checks and are tautologies
  about the code's *shape* rather than its *correctness*. Found 2026-07-27 in
  `test_dynamic_return_threshold_...`: `min <= x <= max` on the output of
  `np.clip(..., min, max)` stayed green while the dynamic return threshold was
  replaced by a constant, across 42 + 197 tests. The replacement must
  **discriminate** — a far UAV's threshold strictly exceeding a near one's is a
  property no constant satisfies.
- **Two copies of one formula agreeing prove nothing.** Where the same arithmetic
  is written twice in production — as `_update_return_energy_state` and
  `_raw_return_energy_margins` both were — comparing them looks like an
  independent check and is not. Both sides move together under a wrong formula.
  Recompute from literals, or from an input pinned by a *different* test.
- **Read the test's own name as a specification and check the quantifier.**
  "once **per uav**" that drives one UAV, "**every** field" that mutates one,
  "across **processes**" run in one interpreter. Found 2026-07-27:
  `test_cutoff_and_depletion_events_fire_once_per_uav` exercised only UAV 0, so a
  fleet-**global** latch passed it — 214/214 green — while undercounting the
  `-5·cutoff -10·depletion` terms, the heaviest in primary `G`, the moment a
  second UAV crossed. This sweep is cheap: it compares the name against the body
  and needs no reasoning about the implementation.
- Fixtures made degenerate or randomness-free for tractability delete exactly
  the variance the property is about. An environment whose `step()` draws no
  randomness cannot witness a determinism claim.
- Use realistic values, not `42`. A seed small enough that the production
  reduction is the identity never exercises the reduction.
- Anything the artifact calls **registered, stable or reproducible** must be
  observed reproducing **across a process boundary**. That is what the word
  means to a reader of the paper, and single-interpreter tests assume it rather
  than check it — including against `PYTHONHASHSEED` salting, which is invisible
  inside one process and fatal across pooled shards.

The failure this prevents is specific: a guard that cannot fail reads as
coverage forever after, so the defect it was meant to catch is not merely
undetected, it is recorded as checked.

**Corollary for this repository — pin the construction-time layout.** Env
construction sets `np_random = RandomState(seed_val)` with `seed_val` defaulting
to `None`, so it seeds from **OS entropy**, and `reset(seed=)` does not
re-derive `ground_bs_positions`. With `randomize_bs` true, the ground-BS layout
is therefore drawn from entropy at construction and is not reproducible from any
seed the test passes later.

Any test whose outcome depends on the construction-time layout is a coin flip
unless it pins coordinates explicitly. On 2026-07-27 one such test read as
order-dependent and consumed a full investigation — bisecting pairs, a matched
control at the parent commit, and a whole-suite comparison — before repeated
isolated runs showed it failing ~20% of the time on its own. Every pairing
result had been a coin flip. **Two samples cannot separate a cause from a 20%
coin**; measure the rate before concluding anything about ordering.

The entropy default itself is left standing deliberately: changing it moves the
estimand, so it is a Project Manager or External Pro decision, never an
implementer's.

### Stage A and Stage B — the only two audits, both triggered

```text
review_stack=false
routine_preimplementation_code_science_review=forbidden
audit_model=two_stage_triggered
code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

**Stage A (design assertion audit)** triggers before freezing a contract that
creates or changes an estimand, benchmark source, control or null, a
reward/credit/gradient/initialization mechanism, a normalization, threshold,
confidence procedure or result branch, or the interpretation connecting a
behavior to a capability. Its content is step 3 of the loop and
`ALGORITHM_PRINCIPLES.md` section 4 — including asking Pro which load-bearing
decision the contract makes without asking, which is the whole surviving
function of the former standalone grill stage. It is decided on paper, without
training; it does not certify a design as sound, it retires the defect class
that is provable before compute.

**Stage B (code-science alignment audit)** triggers after implementation
acceptance and before formal compute, when code newly realizes or materially
changes a claim-bearing element. One question to Pro naming the exact pushed
commit and asking only: does the code instantiate the frozen contract; could a
test pass through the wrong mechanism; could an alternate implementation
explanation change the registered conclusion. Pro returns exactly `ALIGNED`,
`MISMATCH` (naming the frozen assertion and the conflicting code path) or
`SCIENTIFIC_AMBIGUITY` (naming one previously unstated result-changing
choice) — never a new design, controller, search, threshold or evidence
volume, and no style, taste, coverage or generic bug hunting. An unchanged
reviewed commit is never resubmitted; there is no review of the review.

Neither stage triggers for operational repair, logging/schema mechanics, or
mechanical refactors. If a repair changes only one stage, repeat only that
stage.

#### Retained lemma — persistence necessity under anonymous reward

Positive-control necessity is now `ALGORITHM_PRINCIPLES.md` section 4; the
D7.2B failure that taught it is in the round archive. The project-specific
retained lemma, load-bearing for the D7.S line:

> At a supported mixed-urgency history, if reward **and transition** are equivariant
> under agent permutation, the relevant agent states and capabilities are
> exchangeable at zero cost, the joint action support is closed under that
> permutation, and every optimal post-check allocation is reachable by a full-sync
> permutation **with the same future state and return**, then individual persistence
> is not necessary.

The broad converse ("permutation-invariant reward makes role exchange free")
was ruled false: position, energy, queue state, internal memory, transition
latency and non-transferable service state all make persistence necessary
under an anonymous reward. The margin estimand is in
`D0_CARRIER_AND_ESTIMAND.md`: `U*_stable,src / B_H <= -0.10`,
`U*_flex,src / B_H >= +0.10`.

#### Question form for Stage A rounds

Write dependent questions as a **decision tree with the branches pre-walked**
(*if you rule A on Q3, also answer Q3a; if B, Q3c instead*) so one reply
traverses what an iterative interview would discover turn by turn. Carry exact
paths in the `## Evidence to read` allow-list, never file contents — Pro reads
the repository at `stage_commit`. Where a code choice is entailed by a
scientific decision, Pro's preference governs; everything that does not change
a registered quantity or branch stays with Project Manager. Pro's answer is
authoritative **after full reasoning, not before** — never curtail a round.

## Result interpretation

Result semantics — smallest implicated unit, mixed/underpowered handling, the
prohibition on rescuing a valid negative, and what a broad retirement requires
— are `docs/project/ALGORITHM_PRINCIPLES.md` section 6, and bind every result
read in this repository.

**Scenario-7 world provenance (Pro ruling 2026-07-26, Stage B).** The topology
rule below was correct and incomplete. The *user* population is also fixed by
construction-time state that `reset(seed=)` does not re-derive: two freshly
constructed environments carrying the same seed differ in user positions by
kilometres. Equal coordinate hashes therefore do **not** imply a shared episode
world.

The standing rule is consequently:

> Any prior result reused as a causal comparator or paper-level premise must
> establish that its compared arms shared the **complete episode world**, not
> merely the same coordinate topology.

Audited on reuse; no repository-wide retrospective audit is required. The ep64
single-topology diagnostic is retired as causal evidence under this rule — its
environment was constructed fresh per arm, and because the construction-time
worlds were never recorded, no unpaired reanalysis can recover the comparison
either. Topology identity itself is unchanged: it remains the ground-BS and
charging-station geometry, with the user world a nested episode-level random
factor carried by a registered `user_world_seed` rather than by OS entropy.

**Scenario-7 topology provenance (Pro ruling 2026-07-26).** The environment
draws its ground-BS and charging-station layout at construction from an
unseeded RNG, so two runs share a topology only if that was explicitly
arranged. Any Scenario-7 result reused as a causal comparator or paper-level
premise must first establish whether its compared arms shared one topology;
when that is unprovable, the artifact is preserved but its conclusion is
scoped to its realized/unknown topology and it is never used as a matched
causal control. Audited on reuse — no global invalidation, no blocking of
unrelated lines.

Ordinary recurrent MARL is a comparator and an access diagnostic, never an
admission gate. A superiority claim must be matched against it; its failure on
one benchmark does not bar research into a stronger mechanism.

