# D7.S R5 — the exposure-certified Part-A control

**Status: DERIVATION, not a frozen contract.** Nothing here is registered until
Pro rules on it. This is the zero-compute successor work Pro scheduled in
`docs/external-review/rounds/20260729_d7_s_r4_formal_result/21_PRO_OPEN_RAW.md`.

## Why the old control has to go

`full_sync_SET` was supposed to remove individual persistence. It removes only
explicit incumbent *protection*: `full_sync_set_update`
(`scripts/audit_d7_s_event_aligned.py:941`) never receives an incumbent map, so
it cannot exclude one, and greedy nearest-assignment tends to hand each duty
straight back to the UAV already converging on it. Verified against source in
`docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_THE_FULL_SYNC_ARM_CAN_HAND_A_DUTY_BACK.md`.

The consequence is that `D_A` compared `constructive_mixed` against something
that may be close to a no-op, and no recorded quantity can tell us how close.

## The control

At every shared check boundary — `step_index % DELTA == 0`, `DELTA = 10`,
unchanged — replace greedy unconstrained recomputation with:

> **Minimum-cost full derangement.** Assign duties to airborne UAVs one-to-one,
> minimising total transit distance, subject to: no eligible active incumbent
> may be reassigned to the duty it currently holds.

Formally, with `D` the duty set, `U` the airborne UAV set, `m₀` the incoming duty
map and `c(d,u) = ‖pos(u)[:2] − dutypos(d)[:2]‖`:

```text
minimise   Σ_d c(d, m(d))
subject to m injective on D
           m(d) ≠ m₀(d)  for every eligible d
```

This is a rectangular linear assignment problem with forbidden pairs. The
forbidden set is exactly the incoming assignment — one forbidden cell per
eligible duty.

### Held fixed from R4, deliberately

`DELTA = 10`; `H_STABLE = 139`; `MATERIALITY_MARGIN = 5.0`; the duty set; the
information available to the controller (duty positions and airborne positions,
plus the incoming map, which is new *input* but not new *information* — it is
state the runner already holds); the energy and charging policy; the shared check
clock; CRN continuation and the paired-contrast stream discipline; and the
stable-limb-only scope of the Part-A block.

`MATERIALITY_MARGIN` stays at `5.0` because Pro ruled the anchor sound and the
control defective. Moving it now would be metric rescue.

### Replaced

Greedy unconstrained recomputation, and the assumption that "computed from
scratch" implies actual SET.

## Exposure, which is the whole point

The control must **certify** what it claims to do rather than assert it. The
predicate is exact, not fractional:

```text
EXPOSURE_OK  iff  retained_eligible_incumbents == 0
```

No empirical fraction threshold is invented. "Most agents moved" is the failure
mode this control exists to eliminate, so it cannot be the acceptance criterion.

Recorded per check and aggregated per episode:

| Quantity | Why it is here |
|---|---|
| `incumbent_retention_count` | the predicate itself; must be 0 at every check |
| `assignment_hamming_distance` | how much of the map actually moved |
| `target_displacement_per_agent` | a different duty can still be the same place |
| `action_divergence_vs_constructive_mixed` | the physical realization, not the bookkeeping |
| `realized_assignment_run_lengths` | whether lifetime is actually one check |

`target_displacement` is measured against the existing target-identity tolerance
(`legal_set_targets`' `1e-6` geometric dedup, of which `_target_id`'s 6-decimal
key is the tighter reader). A reassignment onto a geometrically identical target
is **not** exposure, and this table is what makes that visible instead of
inferable.

### Infeasibility is a failure, never a silent accept

A full derangement can be infeasible — fewer airborne UAVs than duties, or a
degenerate single-agent case. When it is, the control reports an explicit
support/instrument failure and the affected unit is refused. It never falls back
to the greedy assignment, and it never accepts a partial derangement. **The
fallback is what killed R4; a control with a quiet degraded mode is a control
that certifies nothing.**

## The phase shift has to be repaired too, and it is claim-bearing

`step_once` synthesizes actions from the *incoming* map (`:2494`), steps the env
(`:2507`), and only then updates the map (`:2510`). The recomputed map therefore
governs steps `1..DELTA` of the window rather than `0..DELTA-1` — a uniform
one-step lag at every check, not the step-0 artifact it was first described as.

Repairing it means applying the check-boundary recomputation *before* action
synthesis on that step. That changes when the intervention takes effect, and the
R4 record already establishes that this control's cadence can decide whether
`PART_A_CONTRADICTION` fires. **So this is claim-bearing and goes to Pro, not
into an implementation binding.**

## Population

The eight R4 topologies may not carry the successor's confirmatory result. They
are observed, and they informed this diagnosis. A conclusion-bearing successor
needs a newly frozen, untouched topology panel; a same-topology rerun is a
labelled conditional diagnostic and is never pooled with the confirmatory
population.

The R4 artifact records none of the exposure quantities above, so the retention
rate on run `30403322062` cannot be recovered from it. Measuring it would need a
diagnostic re-run on the observed topologies — permitted, but it buys a
diagnostic rather than a result, and that trade is not made here.

## Development obligation before any conclusion-bearing run

Pro requires a proof-sized exercise establishing that the intervention genuinely
produces one-check individual lifetimes. Concretely: on a development topology,
show `incumbent_retention_count == 0` at every check and
`realized_assignment_run_lengths` concentrated at one check. A control that
cannot demonstrate its own exposure on a development topology has no business on
a confirmatory panel.

That exercise must include a **paired negative**: a deliberately weakened
derangement that retains one incumbent, shown to trip `EXPOSURE_OK`. A guard that
has never gone red is a comment, and a comment is precisely what certified the
last control.

## Implementation bindings — PM-decided, disclosed, none claim-defining

1. **Solver.** Rectangular linear assignment with forbidden cells set to `+inf`.
   Deterministic given inputs.
2. **Tie-break.** Optimal assignments can tie. Resolution is lexicographic by
   `(duty_id, uav_id)` among optimal solutions, so the control is reproducible
   independent of dict ordering — the same property `full_sync_set_update`'s
   ascending-duty-id walk was written for. Ties are measure-zero in continuous
   positions; this exists for reproducibility, not for behaviour.
3. **Eligibility.** An eligible active incumbent is an airborne (non-charging)
   UAV holding a duty in the incoming map. Charging UAVs are not eligible — they
   hold no duty to renew.

Binding 3 is the one I am least sure belongs here rather than with Pro, and it is
raised in the question for that reason.

## What goes to Pro

Round 5 touchpoint 1. The claim-defining questions, tree-structured:

1. Is minimum-cost derangement the right comparator, or does incumbent exclusion
   itself alter the intervention's physical support enough to break comparability
   with `constructive_mixed`?
2. The phase-shift repair — same registered cadence, or a new intervention
   requiring re-registration?
3. Infeasibility scope — episode-level invalidation, or topology-level instrument
   abort?

Eligibility (binding 3) rides on question 1 as a sub-branch rather than a fourth
question.
