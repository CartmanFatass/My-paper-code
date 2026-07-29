# D7.S R5 obligation A — mathematical support derivation

Closes obligation **A** of Pro's R5 ruling
(`docs/external-review/rounds/20260729_d7_s_r5_derangement_control/21_PRO_OPEN_RAW.md`).
Zero-compute and proof-sized: no environment is stepped, no episode is run, and
nothing in the audit path is touched.

Harness: `scripts/d7_s_r5_obligation_a_proof.py`. Run with the registered
interpreter; it prints every figure quoted here.

## The six required properties

### A1 — the assignment domain is the current covered-duty set

By construction. `m0 : D ⇀ U` is the *incoming partial* map; `U_e` is the set of
eligible action-bearing incumbents; and

```text
D_e = { d : m0(d) ∈ U_e }
```

`D_e` is defined as the image-preimage of `U_e` under `m0`, so no duty outside
the covered set can enter the problem. Uncovered duties are unreachable by
definition rather than excluded by a check.

### A2 — non-eligible incumbent pairs are fixed

Also by construction: any `d` with `m0(d) ∉ U_e` is absent from `D_e`, so no
variable represents it and the solver cannot move it.

### A3 — `|U_e| = |D_e|` — **INVALID, 2026-07-29**

> **The premise below is false for this source and the step does not hold.**
> Left in place, not edited away: the claim was submitted to review and the
> correction belongs beside it.
>
> `constructive_mixed_update`'s REJOIN branch can give one UAV a second duty, so
> `m0` is **not** injective — measured at 33% of check boundaries on the
> development topology. Evidence:
> `docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES.md`.
>
> The generator that produced the 2000-sample check below built injective maps,
> so it could not have found this. It confirmed the arithmetic of a premise
> instead of the premise.
>
> No replacement is written here. A derangement is a permutation of a set, and
> which set that is once ownership is non-injective is a scientific decision --
> round `20260729_d7_s_duty_map_injectivity`, §5.

`m0` is injective on its domain (a UAV holds at most one duty). Restricting an
injection to the preimage of a set gives a bijection onto that set, so
`|D_e| = |U_e|` identically — the problem is square by construction, never by
assertion.

**Checked**: 2000 randomised covered/eligible configurations, duties 2–8,
airborne 1–|D|. `|U_e| == |D_e|` held on every sample.

### A4 — every forbidden incumbent edge is absent

The forbidden set is exactly `{ (u, d0(u)) : u ∈ U_e }` — one cell per eligible
agent, i.e. a perfect matching of the square problem. Nothing else is forbidden
by the derangement constraint itself; eligibility condition 6 may remove further
edges, which A6 handles.

### A5 — the solver returns the true minimum-distance derangement

**Cost: verified.** Forbidden cells set to a large finite sentinel (not `inf`,
which makes the solver raise rather than report infeasibility and would hide the
case A6 exists to witness), then rectangular LAP. Against exhaustive enumeration
of all derangements: **360 trials, n = 2…7, random geometry, zero cost
mismatches, and no solution ever used a forbidden edge.**

**Tie-break: NOT verified as originally specified — and this is a defect in my
own binding, found here.**

Implementation binding 2 of the derivation registered a tie-break
"lexicographic by `(duty_id, uav_id)` among optimal solutions." The bare solver
does not honour it. Concrete counterexample: the symmetric ring at `n = 4`,
where every single-rotation derangement costs `56.568542` exactly.
`linear_sum_assignment` returns an optimal assignment that is **not** the
lexicographically smallest one.

The binding claimed a property the chosen tool does not provide. Ties are
measure-zero in continuous positions, which is why random trials never surfaced
it — the counterexample had to be constructed. **A guard that only fires on
inputs you never generate is not a guard.**

**The repair, verified.** Canonicalise after solving: take the optimal cost, then
walk duties in ascending order and fix the smallest agent id whose forced
completion still attains that cost.

```text
symmetric rings      n = 3,4,5,6,7   canonical == brute-force lexicographic optimum
integer lattice      n = 3,4,5       match
random geometry      n = 2…6, 200 cases   0 mismatches
determinism          20 repeated solves of one tied input → 1 distinct result
ALL_CHECKS_PASS = True
```

### A6 — a failed matching carries an explicit infeasibility witness

The witness is a Hall violator: a set `S ⊆ U_e` with `|N(S)| < |S|`, reported as
`S` and its neighbourhood.

**With every non-incumbent edge legal**, the graph is `K_{n,n}` minus a perfect
matching, and a full derangement exists **iff `n ≥ 2`**:

```text
n = 1   derangement_exists = False   witness {S: [0], neighbourhood: []}
n = 2   True     n = 3   True     n = 4   True
```

This is what makes "fewer than two eligible incumbents is a support miss"
correct.

**But `n ≥ 2` is not sufficient**, and the derivation implied it was. Eligibility
condition 6 — each incumbent needs a legal, geometrically distinct
non-incumbent target — removes edges, and Hall's condition can then fail at any
size:

```text
n = 3, allowed = [{2}, {2}, {0,1}]
witness {S: [0,1], neighbourhood: [2]}     two agents, one shared option
```

Two eligible incumbents whose only distinct alternative is the same duty cannot
both be deranged, however many agents are present.

**Consequence for the contract.** The support rule must be *"no full derangement
exists, with a Hall witness"*, tested per event. A cardinality test (`n < 2`) is
necessary but not sufficient, and a contract that gates on cardinality alone
would silently admit structurally infeasible events.

## What obligation A changed

1. **Implementation binding 2 is amended.** The tie-break requires an explicit
   canonicalisation pass; the solver alone does not deliver it. Recorded as a
   binding that was unimplementable as written rather than quietly rewritten.
2. **The infeasibility predicate is amended** from a cardinality check to a
   feasibility check with a Hall witness. `n ≥ 2` is retained as a fast
   pre-filter and an early support miss, never as the decision.

Both were found by doing the enumeration Pro asked for, on constructed
degenerate inputs rather than random ones.

## Not closed here

A is the mathematics. **B** (real source-state feasibility on development
topology `20260725`), **C**–**F** (same-support, pre-action cadence, exact
exposure and branch-semantic witnesses, each with its paired negatives) and
**G** (fresh-population procedure) remain open, and no confirmatory panel is
frozen until they close.
