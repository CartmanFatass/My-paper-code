# D7.S R5 — obligations A and B are closed, and C onward needs a boundary I do not own

You scheduled obligations A–G as the zero-compute next action. **A and B are
closed.** Both found errors in my own derivation, which is reported below as
claims to falsify rather than as progress.

**The decision I need is §4.** Everything before it is evidence.

Discarding this question's framing is a legitimate answer.

## Frozen inputs — not review surface

- Your R5 ruling in full: one-sided falsification control; `V_D <= V*_notP`;
  equivalence refutes necessity while materially-worse does not establish it;
  the R4-style "full-sync worse => Part A passes" rule is not retained.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`. No threshold moves.
- The matched formulation over the **currently covered** duty set, the six-part
  eligibility definition, the four-way `EXPOSURE_OK` conjunction, and the
  pre-action cadence registered as a new R5 intervention. All adopted as ruled.
- The eight R4 topologies may not carry a successor confirmatory result.
- D7.3 and D8 remain blocked. Nothing here asks to unblock them.

## 1. Provenance

**Repository fact** unless marked. `[INFERENCE]` marks my own reading.
Harnesses: `scripts/d7_s_r5_obligation_a_proof.py`,
`scripts/d7_s_r5_obligation_b_feasibility.py`. Both are standalone: they import
nothing from the audit path, are imported by nothing, and mutate no duty map.

## 2. Obligation A — the enumeration found two defects in my own derivation

**A1–A4 hold by construction.** `D_e` is the preimage of `U_e` under the partial
map `m0`, so uncovered duties are unreachable rather than excluded, non-eligible
pairs have no variable, and restricting an injection to a preimage gives a
bijection — `|U_e| = |D_e|` identically. Checked on 2000 randomised
covered/eligible configurations.

**A5 cost holds.** Forbidden-diagonal LAP against exhaustive enumeration: 360
trials, `n = 2…7`, zero cost mismatches, and no returned solution ever used a
forbidden edge.

**A5 tie-break FAILED as registered.** Implementation binding 2 registered
"lexicographic by `(duty_id, uav_id)` among optimal solutions".
`linear_sum_assignment` does not honour it. Counterexample: the symmetric ring at
`n = 4`, where every single-rotation derangement costs `56.568542` exactly and
the solver returns an optimal assignment that is not the lexicographically
smallest. The binding named a property the tool does not provide.

Repaired by an explicit canonicalisation pass — take the optimal cost, walk
duties ascending, fix the smallest agent id whose forced completion still
attains it. Verified on rings `n = 3…7`, integer lattices, 200 random cases, and
20 repeated solves of one tied input returning a single result.

`[INFERENCE]` Ties are measure-zero in continuous positions, which is why random
trials never surfaced this and the case had to be constructed. I report it
because a reproducibility binding that only fails on inputs nobody generates is
indistinguishable from a working one right up until an artifact disagrees with
itself.

**A6: `n >= 2` is necessary but NOT sufficient.** With every non-incumbent edge
legal the graph is `K_{n,n}` minus a perfect matching and a derangement exists
iff `n >= 2`. But eligibility condition 6 removes edges, and Hall's condition can
then fail at any size — witness at `n = 3` with `allowed = [{2}, {2}, {0,1}]`,
two incumbents whose only geometrically distinct alternative is the same duty.

So the support rule became *"no full derangement exists, with a Hall witness"*,
tested per event, with cardinality demoted to a fast pre-filter.

## 3. Obligation B — feasible at every observed check, on one topology

Development topology `20260725`, `DELTA = 10`, 8 episodes x 1500 steps,
**1200 check boundaries**.

```text
full_derangement_exists   1200 / 1200   (100.0%)
infeasibility witnesses   none

n_eligible = 2   22 checks       n_eligible = 6   215
n_eligible = 3   50              n_eligible = 7   196
n_eligible = 4   79              n_eligible = 8   513
n_eligible = 5  125

covered = 8   1071 checks
covered = 7    129 checks   (10.8%)

exclusions: duty_overridden_by_station_return  1170 agent-checks
            no_incumbent_duty                   529
            no_geometrically_distinct_alternative  0
```

**Your two corrections are confirmed by measurement, not by my agreement.**
`covered = 8` is not invariant — it drops to 7 after a charging LEAVE in 10.8% of
checks, so my all-duty formulation would have declared those infeasible.
Eligibility condition 5 fired 1170 times: airborne UAVs holding a duty whose
action is driven by the energy controller heading to a station. My three-part
definition would have tried to derange every one of them.

## 4. The decision

**4a. Does closing C–G require an authorization I do not have?**

C, D, E and F cannot be observed. A same-support witness, a pre-action cadence
witness with the delayed R4 ordering as a paired negative, and the exact exposure
witness with its five paired negatives all require **applying** a derangement and
stepping the environment under it. A and B were observation-only, which is why
they were unambiguously inside "zero-compute".

Your ruling says it "authorizes neither implementation nor compute", and also
schedules A–G as the next action. I read those as consistent only if a
development-only harness is not the "corrected implementation" being withheld —
but that is a reading, and reading around an explicit prohibition is how a
boundary gets moved by whoever is standing next to it. So I am asking rather than
assuming.

If it is authorized, I would like the boundary stated: development topology only,
no conclusion-bearing artifact, no seed namespace registered, harness outside the
audit module.

**4b. Do A's two amendments stand?**

The canonicalisation tie-break, and the support rule becoming a per-event
feasibility test with a Hall witness rather than a cardinality test. Both change
the contract surface. I made them because the enumeration you required is what
exposed them, but they are amendments to a design you ruled on.

**4c. Does B meet the "routinely executable" bar you set?**

1200/1200 on one topology, but 22 checks sat exactly on the `n_eligible = 2`
feasibility floor, and nothing in this exercise bounds that rate on an unobserved
topology. `[INFERENCE]` I suspect the honest reading is that B establishes
executability on `20260725` and **not** a general property of the source, which
would mean the fresh-panel procedure in G needs its own feasibility precondition
rather than inheriting B's result.

## 5. Confidence

- **Verified by construction and enumeration**: A1–A6, including the two
  failures, all reproducible from the committed harness.
- **Measured**: every figure in §3.
- **Not established**: that feasibility transfers off `20260725`; that a
  derangement, once applied, satisfies any of the four `EXPOSURE_OK` conjuncts.
  Nothing in A or B touches exposure — the whole point of the R4 post-mortem was
  that existence of a control is not evidence it does anything, and I do not want
  to repeat that error one obligation later. **Point your scepticism at §3's
  100% first**: it is the number most likely to be read as more general than it
  is.

## Evidence to read

- `docs/research/designs/D7_S_R5_OBLIGATION_A_SUPPORT_DERIVATION.md`
- `docs/research/designs/D7_S_R5_OBLIGATION_B_SOURCE_FEASIBILITY.md`
- `docs/research/designs/D7_S_R5_EXPOSURE_CERTIFIED_DERANGEMENT_CONTROL.md`
- `scripts/d7_s_r5_obligation_a_proof.py`
- `scripts/d7_s_r5_obligation_b_feasibility.py`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`

## Required response sections

1. **4a** — is a development-only derangement harness authorized, and if so what
   is its boundary?
2. **4b** — do the canonicalisation tie-break and the Hall-witness support rule
   stand as amendments?
3. **4c** — does B meet the bar, and does G need its own feasibility
   precondition?
4. Anything in §2 or §3 you judge false, especially the generality of the 100%.
5. What closes C–G, in the order you want them closed.
