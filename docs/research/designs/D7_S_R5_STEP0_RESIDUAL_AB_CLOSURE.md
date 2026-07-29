# D7.S R5 Step 0 — residual A/B reconciliation

`D7_S_R5_DEVELOPMENT_OBLIGATIONS_NOT_A_RESULT`

Closes the five residual items Pro required before any derangement is applied
(`docs/external-review/rounds/20260729_d7_s_r5_obligations_ab/21_PRO_OPEN_RAW.md`,
§5 Step 0). No new source run was needed for any of it.

## 1. Forbidden edges — logical, not numerical

The design said `+inf`; the obligation-A harness used a large finite sentinel and
explained why `inf` cannot carry infeasibility. **The design contradicted its own
proof.** Frozen wording now in
`D7_S_R5_EXPOSURE_CERTIFIED_DERANGEMENT_CONTROL.md`:

> Forbidden edges are logically absent. The implementation must use a
> representation that preserves the legal optimum and must reject any returned
> forbidden edge.

A finite sentinel is admissible **only when proved larger than every possible
legal total cost for the registered geometry**, and that is now asserted
per-geometry rather than assumed: `BIG > n · max(C)`, checked inside every sparse
trial and reported at `n = 8`. Infeasibility is owned by the Hall witness, never
by a sentinel-valued solver output.

## 2. Sparse-graph coverage for A

The earlier exhaustive tests used the **complete** non-incumbent graph. The real
control has sparse graphs after geometric exclusion, so the technical certificate
did not cover the shape it will actually meet.

```text
sparse trials      300     (n = 3..6, keep-fraction 0.34 / 0.50 / 0.75)
feasible           180
infeasible         120
disagreements        0
witness/enumeration disagreements   0
sparse + exact ties (sparsified rings, n = 4,5,6)   disagreements 0
```

In every feasible case the canonical solver matched brute force on cost **and**
on assignment, and never returned a forbidden edge. In every infeasible case it
refused, and the Hall witness agreed with exhaustive enumeration. The two
independent notions of feasibility — a witness computed from the adjacency, and
an exhaustive search over legal permutations — never disagreed.

## 3. The witness describes the graph the solver was handed

A witness computed from a parallel model of the graph proves nothing about the
graph actually solved. Now checked explicitly on the `n = 3` construction:

```text
every non-allowed pair reached the solver as a forbidden cell     True
N(S) covers every allowed edge out of S                           True
witness = {S: [0,1], N_S: [2], abs_S: 2, abs_N_S: 1}
```

The refusal carries `S`, `N(S)`, `|S|` and `|N(S)|` — Pro's requirement, replacing
the neighbourhood *size* the earlier probe recorded. A size alone cannot be
checked against the graph that produced it.

## 4. The eligibility rule is frozen — and which one was chosen matters

Pro offered two interpretations and required one be frozen rather than left as
B's undocumented two-pass pruning. **Option 2 is chosen:**

> The eligible set is established **once** from the six conditions. A later empty
> adjacency is **matching infeasibility**, not a reason to shrink the treated set.

**Why not the fixed-point iteration.** Iterating the pruning loop until the set
is self-consistent chooses *whom to treat on the basis of feasibility*. It would
quietly drop exactly those incumbents that are hardest to derange and keep the
easy ones — the same selection effect that the post-start topology-abort rule
exists to prevent, relocated to event admission where it would be harder to see.
A comparator that treats only the agents it finds convenient is not a forced
renewal control.

Under the frozen rule an unsatisfiable agent surfaces as a Hall violation with
singleton `S` and empty `N(S)`, which refuses the event instead of reshaping it.

The retained covered-duty set — what condition 6 is evaluated against — is the
set of duties held by action-bearing incumbents, which is what the derangement
permutes. That resolves the apparent circularity in one pass.

### Invariance, rechecked rather than assumed

Pro noted no such exclusion fired in the observed 1200 checks and said the
invariance should be rechecked. Re-run under the frozen rule:

```text
checks 1200   feasible 1200   infeasible 0
n_eligible  2:22  3:50  4:79  5:125  6:215  7:196  8:513
covered     7:129   8:1071
exclusions  duty_overridden_by_station_return 1170   no_incumbent_duty 529
```

**Identical to the pre-freeze run in every figure.** The frozen rule changes no
observation on this sample; it changes what happens in the case this sample
never produced.

## 5. Conditions 1 and 3 asserted, not assumed

"Present and active", "not failed, terminal or otherwise non-acting" were
previously satisfied by those states simply not arising. The registered
Scenario 7 environment exposes no per-UAV failure or termination flag, so the
check probes optionally across plausible attribute names and treats a positive
failure signal as ineligible. A future environment that gains such a flag is
handled rather than silently read as healthy.

## 6. B's claims narrowed, and its dependence recorded

Both corrections are in `D7_S_R5_OBLIGATION_B_SOURCE_FEASIBILITY.md`: B is a
**dependent** probe — it imports `audit_d7_s_event_aligned` and steps real
environments through its helpers — and it was **development compute**, not
zero-compute. The supported claim is feasibility along eight
`constructive_mixed` trajectories on `20260725`, not source-wide executability,
and never post-treatment totality.

## Status

Step 0 closes. **Next is Step 1 — F, the branch semantics, synthetically and
before any treatment data exists**, so that a development observation cannot
acquire an interpretation the comparator does not support.
