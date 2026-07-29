# Reconciliation — the branch stands, the interpretation does not

Pro's ruling is `21_PRO_OPEN_RAW.md`, archived byte-exact. This file records what
the execution side does about it. The scientific decisions below are Pro's, not
mine; what is mine is the code-side consequence and the corrections to my own
record.

## The ruling, as it binds work here

```text
5a  neither invalidation nor cosmetic mask
    PART_A_CONTRADICTION stands as emitted and is not relabelled
    the eight R4 topologies MAY NOT carry a successor confirmatory result
5b  (ii) INSTRUMENT VERDICT
defect  Part-A control CONSTRUCTION, not the margin anchor
        MATERIALITY_MARGIN = 5.0 stands; changing it now would be metric rescue
next    ZERO-COMPUTE derivation of an exposure-certified control
        "This review authorizes neither a corrected implementation nor further compute."
D7.3/D8 both remain blocked
```

The interpretive disposition attached to the immutable artifact is
`PART_A_CONTROL_NON_IDENTIFYING_FOR_FORCED_INDIVIDUAL_RENEWAL`. It is **not**
written back into the artifact JSON and does not replace the branch.

## The defect, stated so it can be checked against source

`full_sync_SET` was supposed to remove individual persistence. It removes only
*explicit incumbent protection*: it takes current duty positions and current
airborne positions, greedily assigns the nearest remaining UAV to each duty, and
receives no incumbent map and no prohibition on reassigning a duty to its
current holder. A from-scratch recomputation can return the incumbent
assignment unchanged.

The surrounding comment claims the schedule "never preserves any incumbent". The
executable meaning is only "no incumbent is explicitly locked", which is a
different statement. That gap is the whole finding.

`conformance.ok` did not close it. Its arm-distinctness check compares
`constructive_mixed`'s post-LEAVE map against the pre-LEAVE ownership map — it
establishes that `constructive_mixed` rematched a vacancy. It never compares
`full_sync_SET` against `constructive_mixed`, and it measures no incumbent
retention, no duty-map Hamming distance, no target displacement, no action
divergence and no realized assignment lifetime.

Pro also names a second, smaller realization gap: `step_once` synthesizes and
executes actions from the *incoming* duty map and only afterwards calls
`update_duty_map_on_transitions`, so at `step_index=0` the first primitive action
of the alleged full-sync check runs on the pre-existing map. Pro judges this
unlikely to explain the equivalence on its own.

**Both claims are Pro's readings of source and are load-bearing. Verifying them
against the actual implementation is the first execution-side task, before any
design work rests on them.**

## What I got wrong, corrected rather than edited away

Two claims in `20_PRO_OPEN_QUESTION.md` §4 were overstated. The question invited
falsification of exactly this one, and it was falsified.

1. **Topology cancellation as the reason for the tight interval — overstated.**
   All eight topology point estimates are themselves inside `±5`, so the result
   is not mainly large effects cancelling to zero. Sign cancellation helps place
   the pooled point near `0.484`; it does not explain the interval width, and
   between-topology heterogeneity generally *widens* an interval rather than
   narrowing it. I supplied no variance decomposition and so established nothing
   about which term dominates.
2. **"The source-control contrast appears systematically near zero" — too
   strong.** The defensible statement is that every observed topology-level point
   contrast was under five G-units in magnitude and the equal-topology-weighted
   population interval sat comfortably inside the margin. "Systematically near
   zero" would need topology-specific intervals, exposure measurements, and a
   definition of "near zero" independent of the registered margin.

Both corrections are appended to the evidence note rather than substituted into
it, so the record shows what was claimed and what it became.

Pro also upheld two things I had recorded correctly: the development topology did
**not** contaminate the formal population (steering synthetic branch witnesses
during the non-conclusion-bearing assembly exercise does not touch formal data),
and every registered gate did pass — the run passed the gates it had while
exposing a protected gate it lacked.

## Consequences for the code side

Nothing is implemented under this ruling. Recording what the ruling *implies*, so
the next round's design work starts from it rather than rediscovering it:

- The successor control is an **exposure-certified minimum-cost derangement**:
  at every shared check, assign every eligible active incumbent to a
  non-incumbent duty/target by one-to-one minimum-total-transit assignment under
  an incumbent-exclusion constraint.
- Held fixed: duty set, information, energy and charging policy, shared check
  clock, CRN continuation, `H_STABLE = 139`, and the five-G-unit Part-A margin.
- Replaced: greedy unconstrained recomputation, and the assumption that
  "computed from scratch" implies actual SET.
- The exposure predicate is **exact, not fractional** — zero retained eligible
  incumbents. An infeasible derangement is an explicit support/instrument
  failure, never a silent accept.
- The artifact must record incumbent-retention count, assignment Hamming
  distance, per-agent target displacement, action-vector divergence from
  `constructive_mixed`, and realized assignment run lengths.

## Population

The eight R4 topologies are now **observed**, and they informed this diagnosis.
They may be reused for artifact-only reanalysis, for control-exposure
diagnostics reconstructible from stored data, for methodological analysis of the
implemented controller, and for an explicitly labelled conditional replication.

They may **not** carry a new formal result after the control is repaired. A
conclusion-bearing successor needs a newly frozen, untouched topology panel. A
same-topology rerun is a conditional diagnostic and must never be pooled with a
successor's confirmatory population.

## The smallest retained result

Pro's wording, kept verbatim as the durable claim from run `30403322062`:

> On eight fresh S7-S3 topologies, the implemented greedy duty-map recomputation
> at every shared check was externally equivalent within five (G)-units to the
> event-driven `constructive_mixed` schedule, while the focal stable contrast was
> affirmatively nonmaterial and the focal flex contrast unresolved. Because
> actual individual-renewal exposure in the Part-A arm was neither guaranteed nor
> measured, this is an instrument/baseline result rather than evidence that
> individual persistence is unnecessary.

## Compute

The user granted successor-run compute in advance of this ruling
(`r5_reanchor_compute_grant=GRANTED_20260728`). It is **not exercised**, for two
independent reasons:

1. Pro's ruling states plainly that it authorizes neither a corrected
   implementation nor further compute, and the next action is zero-compute.
2. The grant was given against a scenario that did not occur — a margin
   re-anchor. Pro ruled the margin sound and the control defective. Spending a
   grant given for one thing on a different thing is not what the grant said.

The grant stays open and unspent. It becomes live when a successor contract is
pre-registered and frozen, on a fresh topology panel, after the derivation has
been reviewed.
