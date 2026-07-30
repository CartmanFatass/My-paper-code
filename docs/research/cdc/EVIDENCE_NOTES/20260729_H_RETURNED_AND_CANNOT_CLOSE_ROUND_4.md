# Step H returned, mechanically clean, and it still cannot close round 4

> **THIS NOTE'S ORIGINAL DISPOSITION STANDS. Ruled 2026-07-30 --
> `docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/`.**
>
> A withdrawal notice sat here for part of 2026-07-29 claiming the contamination
> charge against H was withdrawn. **That withdrawal was wrong and is itself
> withdrawn.** H keeps `INVALID_R4_REALIZATION:
> DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`, with a sharpened reason: H does
> not establish that its complete conclusion-bearing assignment paths are
> equivalent to the repaired realization.
>
> One thing in this note IS still void, on its own grounds: the probe in
> "MEASURED: the branch fires on this population" rolled the **wrong seed
> namespace**. A correctly namespaced re-run of that probe reaches the same
> qualitative verdict -- 3 REJOIN events on the R4 population inside 950 steps --
> so the conclusion was right, but a right conclusion from a wrong measurement is
> still a wrong measurement, and the original numbers must not be cited.
>
> What was never true: that `rejoin_events = 0` exonerated H. That counter covers
> only environment falling-edge REJOINs on the main prefix, while every focal SET
> continuation invokes the repaired REJOIN branch directly at `t = DELTA - 1`.
> See `30_PM_SCIENTIFIC_RECONCILIATION.md`.

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

### WITHDRAWN, 2026-07-29: this probe measured the wrong population

**Everything from here to the end of this section is void.** The probe derived
its episode, energy and user-world seeds without passing `contract_id`.
`_derived_seed` and `user_world_seed` both default to the module `CONTRACT_ID`
(R3's namespace), while every R4 driver passes `R4_POPULATION_NAMESPACE`
explicitly. The probe therefore rolled **R3-namespace episodes at R4 topology
coordinates** -- a different population. Measured, all three seeds, topology
20260739 / audit / episode 0:

```text
                 default (R3) namespace   R4 namespace
episode_seed     1688249791               37629764
energy_seed      978540538                1548591420
user_world_seed  6943297548021737841      2189845897274172325
```

Not a near miss: every derived seed differs. The three REJOIN events it found
are real events in episodes **no R4 artifact contains**, so they say nothing
about whether the branch fires on the R4 population.

Nothing caught it because the namespace was never printed and derived seeds are
opaque integers either way. Closed in
`scripts/d7_s_r4_rejoin_exposure_probe.py`: the R4 namespace is now the default,
rolling the R4 population under any other namespace is REFUSED, the namespace is
printed and recorded in `--out`, and `tests/d7_s_r4_probe_namespace_test.py`
pins all of it -- both guards watched failing under paired-negative mutation.

The corrected answer, and H's actual disposition, is in
`20260729_R4_RERUN_CLOSES_THE_INJECTIVITY_CHARGE.md`. In short:
`rejoin_events = 0` across the whole R4 population over 111,433 rolled steps,
and H's recorded focal events are bit-identical to the post-repair re-run's on
all eight topologies. **The contamination charge against H is withdrawn** -- by
measurement, not by argument.

The reasoning the void section rests on was not wrong, and is worth keeping: a
roll with zero REJOIN events runs identical code before and after the repair, so
a count IS decisive about H. Only the population it was counted on was wrong.

### VOID -- original claim, retained because it is cited above

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

**CORRECTED TWICE. The current statement is the third one, ruled 2026-07-30.**
The intermediate version claimed the contamination charge was withdrawn; that was
wrong. As it stands:

- **Established.** H predates the repair, and charging occurred 49 times. The
  REJOIN branch **is** reached on the R4 population: a correctly namespaced probe
  found 3 environment REJOIN events inside 950-step rolls (20260734 calibration
  ep0, 20260736 audit ep1, 20260739 audit ep0). Separately and independently,
  every focal SET continuation invokes the repaired branch directly at
  `t = DELTA - 1` via `fork_continuation`, so it executes on conclusion-bearing
  paths regardless of any environment edge.
- **NOT established.** That a double assignment produced a *different recorded
  number* in H. Reaching the branch is not the same as the duplication surviving
  into a certified limb. The disposition is fail-closed evidentiary, not a claim
  that a differing value has been found.
- **Void, superseded, or wrong at various points on 2026-07-29:** the original
  probe's numbers (wrong seed namespace); the claim that the re-run's
  `rejoin_events = 0` showed the branch unreached (that counter covers only
  environment edges on the main prefix); and the withdrawal of the contamination
  charge that followed from it.

The intermediate wrong version, for the record:

> - **Established.** ... the REJOIN branch is **not** reached on the R4
>   population: the re-run measured `rejoin_events = 0` ...
> - **Therefore.** The defective branch never executed on these episodes, so H's
>   trajectories are the trajectories the repaired code produces. The
>   contamination charge is withdrawn.

One paragraph of the original reasoning survives intact and is worth keeping,
because it is why the re-run was right to launch regardless of how the charge
resolved: a conclusion-bearing artifact must be able to show the invariant held,
and H cannot -- it records `leaves`, `planned_leaves_observed`,
`leaves_before_deadline`, `uav_charging` and `last_charging_arrival`, and **no
rejoin field at all**. "The defect did not fire" is not a property an immutable
JSON can be given after the fact. It took a *different* artifact, carrying the
instrument, to answer it. That the answer exonerates H does not mean H could have
been read as exonerated on its own.

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
