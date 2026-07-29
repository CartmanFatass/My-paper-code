# D7.S R5 obligation B — real source-state feasibility

Closes obligation **B** of Pro's R5 ruling: record, at every relevant check on
development topology `20260725`, the total duties, covered duties, airborne
UAVs, action-bearing incumbents, eligible matching size, whether a full
derangement exists, and the reason for every exclusion.

Probe: `scripts/d7_s_r5_obligation_b_feasibility.py`. It rolls
`constructive_mixed` exactly as the audit does and only **observes** what a
derangement would face at each shared check — it never applies one, never alters
a duty map, and writes nothing into the audit path. Development topology only;
not conclusion-bearing.

```text
topology       20260725 (dev), coord_hash 37b1a44987839dfd...
DELTA          10
duties         8  (N_RELAY_DUTIES 2 + N_SERVICE_DUTIES 6)
episodes       8, 1500 steps each
checks         1200
```

## Result

```text
full_derangement_exists    1200 / 1200   (100.0%)
infeasible                 0
infeasibility witnesses    none
```

**The comparator is routinely executable on this source.** Pro required the
exercise to show that, rather than that one hand-picked state passes; 1200
consecutive check boundaries across eight episodes did.

### Eligible matching size

```text
n_eligible = 2   22 checks     n_eligible = 6   215
n_eligible = 3   50            n_eligible = 7   196
n_eligible = 4   79            n_eligible = 8   513
n_eligible = 5  125
```

**It never fell below 2**, which is the floor below which full derangement is
impossible. But 22 checks sat exactly on that floor, so the margin is thin
rather than comfortable — see the caveat below.

### Covered duties

```text
covered = 8   1071 checks
covered = 7    129 checks     (10.8%)
```

**This confirms Pro's correction empirically, and refutes my original
formulation.** `covered = 8` is not invariant: after a charging LEAVE the
covered set drops to 7, exactly as `constructive_mixed` is written to behave.
The earlier derivation mapped the *full* duty set and would have declared all
129 of those checks infeasible — 10.8% of the run — when they are entirely
ordinary states.

### Exclusions

```text
duty_overridden_by_station_return   1170 agent-checks
no_incumbent_duty                    529
```

**Eligibility condition 5 is load-bearing, not decorative.** It fired 1170
times: UAVs that are airborne and hold a duty, but whose action is driven by the
energy controller heading to a charging station rather than by their duty
target. My original three-part definition — airborne, not charging, holds a
duty — would have counted every one of those as eligible and tried to derange an
agent that is not serving its duty at all. Pro added the condition; the source
exercises it constantly.

`no_incumbent_duty` is the post-LEAVE complement: UAVs carrying no duty in the
incoming map, correctly outside the retention denominator.

Zero checks were excluded for `no_geometrically_distinct_alternative`, so the
duty targets stayed geometrically separated throughout on this topology. That is
a property of this topology, not a guarantee.

## What this does not establish

1. **One topology.** `20260725` is the development topology. Feasibility here
   does not transfer to a fresh confirmatory panel, and obligation G's panel
   selection is not licensed by this result.
2. **The `n_eligible = 2` tail is thin.** 22 of 1200 checks sat on the
   feasibility floor. No check fell below it here, but nothing in this exercise
   bounds the rate at which a different topology would. The contract's support
   rule must therefore stay a per-event feasibility test with a Hall witness —
   obligation A already showed a cardinality test is not sufficient — and the
   infeasibility path must be exercised deliberately rather than waited for.
3. **No exposure claim.** This measures only whether a derangement *exists*. It
   says nothing about whether applying one produces the four `EXPOSURE_OK`
   conjuncts, which is obligation E.
4. **No physical realization.** Nothing here was stepped under a derangement, so
   the same-support and cadence witnesses (C and D) remain open.

## Status

**B closes.** A and B are done. **C–G remain open**, and no confirmatory panel is
frozen. The next obligations require applying a derangement rather than
observing feasibility, which is where the "no implementation authorized"
boundary needs Pro's word before it is crossed — raised in the next round rather
than assumed here.
