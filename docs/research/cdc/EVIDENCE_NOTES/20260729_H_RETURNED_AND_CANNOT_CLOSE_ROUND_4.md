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

### What is established, and what is not

- **Established.** H predates the repair. Charging -- the precondition for
  REJOIN -- occurred 49 times. H is otherwise mechanically clean.
- **NOT established.** That a double assignment actually occurred during H's
  episodes. The shard artifacts record `leaves`, `planned_leaves_observed`,
  `leaves_before_deadline`, `uav_charging` and `last_charging_arrival`, and **no
  rejoin field at all**, so the artifact cannot answer this about itself.

The burden runs the other way. A conclusion-bearing artifact must be able to show
the invariant held, and this one cannot; "the defect probably did not fire" is not
a property an immutable JSON can be given after the fact. This is the same
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
count of duty-map injectivity checks performed and violations found, would let
the next R4 artifact answer this question about itself in one field.
