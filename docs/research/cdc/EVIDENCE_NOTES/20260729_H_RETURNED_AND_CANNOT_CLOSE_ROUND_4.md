# Step H returned, mechanically clean, and it still cannot close round 4

Date: 2026-07-29
Run: `30403322062`, tag `d7s-audit-3`, head `a00612ad`, branch `d7s-audit-3`
Artifacts: 8 shard artifacts `d7s-shard-20260734 .. 20260741`

`CURRENT_WORK.md` recorded H as `RUNNING` and said "Round 4 cannot close until H
returns". H returned at 2026-07-29T00:14:58Z, **success, 8/8 shards**, while the
session that launched it was working on the source-assignment repair. The
`RUNNING` line was stale, not wrong when written.

## What it says

Pooled locally with the registered pooler over the eight shard artifacts.

```text
smoke                      False
topology_seeds             20260734..20260741   (all eight, one shard each)
topology_records           8
support.ok                 True    calibration 8/8   audit 8/8
conformance.ok             True    invalidated_pairs 0  topology_hash_ok  arm_distinct_ok
all_seed_controlled        True
r4_population_namespace    D7_S_R4_ABSOLUTE_FOCAL_MARGIN
branch                     PART_A_CONTRADICTION
limb_states                stable AFFIRMATIVE_NONMATERIAL     flex UNRESOLVED
u_star_stable              point -1.0920   CI [-3.1781, +1.3401]
u_star_flex                point -0.1644   CI [-8.1859, +7.4558]
part_a                     d_a_point 0.4839
                           lower_contrast_lcb 4.3190  ucb 6.6860
                           upper_contrast_lcb 3.3140
```

**The R4 freshness sentinel ran and passed.** The seed union equals
`TOPOLOGY_SEEDS_R4`, so `_pooling_r4_population` is true and the pooler puts the
artifact through `r4_freshness_sentinel`, which raises `SystemExit` on failure.
It did not raise. This is the executable closure that step D found missing (B1)
and D' installed; H is the first whole-population artifact to go through it.

`r4_freshness_sentinel` and `r4_artifact_identity` read as `None` on the pooled
JSON. That is not a defect: the sentinel is a **gate**, not a recorded field, and
only `r4_contract` and `r4_population_namespace` are in `R4_IDENTITY_FIELDS` and
written through. Both are present. Do not read those `None`s as a missing check.

## Why it cannot close round 4

H ran at `a00612ad`. The source-assignment repair is `23fecff3`. Measured:

```text
git merge-base --is-ancestor 23fecff3 a00612ad   ->  NO
```

So every episode in H was rolled by a `constructive_mixed` whose REJOIN branch
can give one UAV two executable duties -- the defect ruled in round
`20260729_d7_s_duty_map_injectivity`, measured at ~33% of check boundaries on the
development topology, and **present in exactly one of the two arms `D_A`
contrasts**. An arm-specific invariant violation inside a contrast is not a
perturbation of a value; it changes which agents are certified.

### The escape that does not apply

The defect fires in the REJOIN branch, and REJOIN follows charging. R4's
registered horizon is short relative to the ~900-step charging onset measured on
the development topology, so it was worth asking whether the mechanism could fire
at all -- if it never fires, H would be untouched by this defect.

It can. Counted across the eight shard artifacts:

```text
uav_charging TRUE entries            49
last_charging_arrival >= 0 entries   49
```

Charging occurs 49 times across the R4 population within the registered horizon.

### MEASURED, 2026-07-29: the branch fires on this population

`scripts/d7_s_r4_rejoin_exposure_probe.py` settles it without a formal re-run.
The repair's scope is Pro's (b1), the REJOIN branch, plus a universal final
assertion, so **a roll with zero REJOIN events runs identical code before and
after the repair.** A nonzero is therefore decisive about H.

Full R4 population, 2 episodes per block, 950 steps each, 30400 steps rolled:

```text
topology    rejoins  leaves  charging_steps
20260734          0       4             381
20260735          0       2              94
20260736          0       4             366
20260737          0       4             137
20260738          0       2             176
20260739          2       6             441
20260740          0       4             610
20260741          1       5             673
------------------------------------------------
totals            3      31            2878     injectivity_checks 60800
                                                refusals 0
R4_REJOIN_PROBE_FIRED
```

**The REJOIN branch is reached on the R4 population.** H therefore ran code that
could double-assign at exactly those boundaries, and its contamination is now
measured rather than inferred from the commit graph.

`refusals = 0` says the repaired branch handled those three events without
violating the invariant -- which is the repair working, and precisely the
divergence: the historical code took the double-assigning path at the same three
boundaries.

**One topology lied.** The first run of this probe was `20260734` alone: zero
rejoins over 1900 steps with 322 charging steps, reported as
`R4_REJOIN_PROBE_ZERO_WITH_POWER`. Taken as the answer it would have argued for
rehabilitating H. It is one of the six topologies that genuinely show zero; the
signal lives in the other two. Two samples cannot separate a cause from a coin,
and eight topologies cost forty minutes.

**Do not read this as "six of eight shards are clean."** This probe rolls 2
episodes per block and H ran 8, so a topology showing zero here can still carry a
rejoin in the episodes not rolled. What is established is reachability on the
population, which is all that is needed: a topology is indivisible and the pooled
estimate spans all eight.

### What is established, and what is not

- **Established.** H predates the repair. Charging occurred 49 times. The REJOIN
  branch is reachable and reached on the R4 population -- 3 events across
  20260739 and 20260741 under the probe above. H is otherwise mechanically clean.
- **NOT established.** That a double assignment produced a *different recorded
  number* in H. Reaching the branch is not the same as the duplication surviving
  into a certified limb; establishing that would need the pre-repair code re-run
  under instrumentation, which is not worth it when the re-run is needed anyway.

The burden runs the other way regardless. A conclusion-bearing artifact must be
able to show the invariant held, and this one cannot -- it records `leaves`,
`planned_leaves_observed`, `leaves_before_deadline`, `uav_charging` and
`last_charging_arrival`, and **no rejoin field at all**. "The defect probably did
not fire" is not a property an immutable JSON can be given after the fact, and
here the measurement says it very likely did. This is the same
disposition `CURRENT_WORK` already carries for the earlier R4 artifact --
`INVALID_R4_REALIZATION: DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`, citable
only as a descriptive external-return observation of the historical code paths --
reached here independently, from the commit graph and the artifacts, rather than
inherited.

`PART_A_CONTRADICTION` is not rewritten and the shard JSONs stay immutable.

## What closing round 4 now needs

A re-run of the R4 measurement at a commit that includes `23fecff3`, on the same
frozen population `20260734..20260741`, with no pooling across the boundary --
the provenance rule created by D' already forbids mixing shards produced before
and after a contract-namespace change, and this is a stronger break than that.

That is conclusion-bearing compute and therefore user authority.

**One instrument gap worth closing in the same change.** The artifact records
leaves and charging but not rejoins, which is why this note has to argue from the
commit graph instead of from the measurement. A rejoin counter, and a recorded
count of duty-map injectivity checks performed, would let the next R4 artifact
answer this question about itself in one field.

The natural choke points already exist and are single: `assert_partial_injection`
for the check count, and `step_once`'s `rejoin_uavs` for the event count -- the
same key obligation B's power guard now reads.

**CLOSED at `e6e585a9` as `roll_power`, and its first measurement is a signal
about H.** A `--smoke` run on the development topology under `--workers 4`:

```text
calibration   rejoin_events 0   leave_events 1   injectivity_checks 1678   steps_rolled 829
audit         rejoin_events 0   leave_events 1   injectivity_checks 1828   steps_rolled 904
```

The check counts are nonzero across the worker boundary, which is the plumbing
working. The interesting number is **`rejoin_events` = 0 over ~900 rolled
steps**, consistent with the ~900 charging onset measured for obligation B: a
roll of this length can complete with the defective branch never entered.

**This does NOT rehabilitate H.** It is a smoke, with reduced episode counts, on
development topology 20260725 rather than the R4 population, and H's charging
count of 49 says charging DID occur there. What it changes is the prior: "the
REJOIN branch never fired in H" is now a live possibility rather than a
hand-wave, and it is no longer answerable by argument in either direction.

That is precisely the point of the instrument. The re-run will record
`rejoin_events` per topology block, and the question that forced this note to
argue from the commit graph becomes a field in the artifact. If the re-run
reports zero rejoins across the population, that is also the evidence that would
have retrospectively cleared H -- but it has to be measured on the R4
configuration, not inferred from a smoke.

**The trap in implementing it.** `run_topology_audit` takes `workers` and the
episode work runs under `ProcessPoolExecutor`. A module-level counter incremented
inside `assert_partial_injection` lives in the WORKER process and is discarded
when that process exits, so the parent would record zero checks on a run that
performed thousands -- a counter reading zero for the same reason a rate reads
zero over an empty set, and indistinguishable in the artifact from a guard that
never ran. The count has to travel back in the per-episode return payload and be
accumulated by the parent, exactly as `_accumulate_episode_leave_stats` already
does for leaves. Verify it against a `--workers 4` run, not a serial one:
`--workers 1` would pass while the shipped configuration silently recorded zero.
