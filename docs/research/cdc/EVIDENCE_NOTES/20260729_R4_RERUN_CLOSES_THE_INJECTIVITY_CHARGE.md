# The R4 re-run: the defect never fired, and H is exonerated by measurement

Date: 2026-07-29
Run: `30479940700`, tag `d7s-audit-4`, stage commit `56a64c3c`, branch `untied-k`
Result: success, 8/8 shards, 18:26:42Z -> 20:20:35Z (114 min)
Artifacts: `d7s-shard-20260734 .. 20260741`, pooled locally with the registered
pooler (exit 0, so `r4_freshness_sentinel` ran and passed)

This is the first R4 artifact containing BOTH the source-assignment repair
`23fecff3` and the `roll_power` instrument `e6e585a9`, so unlike step H it can
answer about itself the question that forced H's disposition.

It answers it, and the answer is not the one the record predicted.

## The instrument reading, first

`roll_power`, whole population, both blocks, all eight topologies:

```text
topology     rejoin_events  leave_events  injectivity_checks  steps_rolled
20260734           0             11              28,904          14,337
20260735           0             14              27,600          13,667
20260736           0             13              27,590          13,662
20260737           0             13              29,094          14,423
20260738           0             14              29,280          14,498
20260739           0             14              27,424          13,570
20260740           0             16              27,318          13,499
20260741           0             14              27,838          13,777
-------------------------------------------------------------------------
totals             0            109             225,048         111,433
                                               refusals 0
```

**Zero REJOIN events on the R4 population, over 111,433 rolled steps.** The
repaired branch never executed. The 225,048 injectivity checks say the guard
itself ran, so this is a measurement and not a silent instrument failure -- the
`--workers 4` counter-loss trap the instrument was designed around did not fire.

### Why zero is expected here, and why that matters more than the zero

A REJOIN is a FALLING edge of `uav_charging`. The 109 leaves prove the
precondition -- charging -- occurred 109 times, so this is not arithmetic over an
empty set. Charging ends by one of two routes:

- **Full charge.** Measured from the env: `charging_power_w` 1000 W, `time_step`
  1 s, `battery_capacity_wh` 160 -> 0.2778 Wh/step = 0.174% of capacity per step.
  From the 2% service cutoff to full is **~565 steps**.

  **MEASURED ON THIS POPULATION, not inherited.** An earlier draft of this note
  said "charging onset sits near step 900", carried over from the development
  topology -- a number for a different population doing load-bearing work. The
  re-run's own 109 recorded leaves, read from the eight shards:

  ```text
  capture_step (charging capture)   min 602   p10 755   median 873   max 951
  departure_step (dock request)     min 306   p10 533   median 728   max 891
  leaves with capture_step + 565 <= 950            0 of 109
  ```

  The earliest capture anywhere in the population is step **602**, so the
  earliest a full charge could complete is step **1167** against a prefix capped
  at `T_E_MAX = 950` -- 217 steps beyond the cap, and that is the best case out of
  109. A full charge cannot complete inside the prefix, by measurement on the
  population the claim is about.

  **Count these from the shards only.** A first pass globbed the shard directory
  and the pooled artifact together and reported 218 leaves -- every shard counted
  twice. The quantiles above are unaffected (duplicating every value preserves
  min, median and max, which is exactly why the error survived a sanity check),
  but the population total is 109.

  **The counter is corroborated independently.** `roll_power.leave_events` equals
  `len(report["leaves"])` in all sixteen blocks, exactly. The new counter and the
  pre-existing per-leave diagnostic list agree, which is the cross-check the
  counter itself could not provide.
- **Losing station selection** to contention. Needs no full charge, and did not
  occur across all 109 charging entries.

So the honest statement is not "the defect is harmless". It is:

> **The R4 measurement is insensitive to the source-assignment repair, because
> R4's registered horizon ends before any REJOIN can occur.**

The repair remains correct and necessary -- the defect was measured at ~33% of
check boundaries on the development topology, which runs long enough to reach the
branch. R4 simply cannot exercise it. Any successor contract with a longer
horizon **will** enter that branch, and will need this artifact's `roll_power`
to be read rather than assumed.

## H is exonerated, by measurement rather than argument

`20260729_H_RETURNED_AND_CANNOT_CLOSE_ROUND_4.md` recorded H as contaminated on
two grounds: H predates `23fecff3` (true, and unchanged), and a probe that
claimed the REJOIN branch fires on the R4 population (**wrong** -- it rolled the
R3 seed namespace; see that note's withdrawal). Three independent measurements
now settle it.

**1. The audit module's changes are numerically inert on these episodes.** H's
`scripts/audit_d7_s_event_aligned.py` at `a00612ad` and HEAD's were both loaded
into one process and rolled the same R4 episodes from the same derived seeds:

```text
topology 20260734 / audit / ep0     topology 20260739 / audit / ep0
  seeds        identical              seeds        identical
  n_steps      873 == 873             n_steps      872 == 872
  event t_e    873 == 873             event t_e    872 == 872
  leaves         1 ==   1             leaves         1 ==   1
  action digest  d47ce027... == d47ce027...   7925cd63... == 7925cd63...
```

Bit-identical recorded action prefixes. This is what "the repair never fired"
looks like from the other direction.

**2. H's focal events are identical to the re-run's on all eight topologies.**
SHA-256 over each shard's `audit_events`:

```text
20260734 SAME   20260735 SAME   20260736 SAME   20260737 SAME
20260738 SAME   20260739 SAME   20260740 SAME   20260741 SAME
```

The focal-event records -- battery, station occupancy and queue, positions,
`return_energy_margin`, capture edge, charging state -- are the same bytes in
both runs. The pre-repair and post-repair code produced the same events.

**3. The per-episode reports differ only by the added field.** A structural diff
of `audit_reports` and `calibration_reports`, H vs re-run, on every topology,
returns exactly one difference: `roll_power`, present only in the re-run. Nothing
else in those reports moved.

The reasoning that made a count decisive was sound and is worth preserving: the
repair's scope is the REJOIN branch plus a universal final assertion that can
only raise, so **a roll with zero REJOIN events and zero refusals executes
identical code before and after it.** Both counts are zero here. H's trajectories
are the trajectories the repaired code produces.

`INVALID_R4_REALIZATION: DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED` does not
apply to H. H remains unusable as *the* round-4 artifact for the separate reason
it always had -- it carries no rejoin field, so it cannot show the invariant held
without this artifact standing behind it -- but it was not measuring the wrong
thing.

## The pooled result

```text
smoke                      False
topology_seeds             20260734..20260741   (all eight, one shard each)
topology_records           8
r4_contract                docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
r4_population_namespace    D7_S_R4_ABSOLUTE_FOCAL_MARGIN
support.ok                 True    calibration 8/8   audit 8/8
conformance.ok             True    invalidated_pairs 0  topology_hash_ok  arm_distinct_ok
episode_world_provenance   all_seed_controlled True   128 episodes   0 not controlled
primary_g                  degenerate False, component_invariance_evaluated True,
                           components_invariant_stable False, flex False
branch                     PART_A_CONTRADICTION
limb_states                stable AFFIRMATIVE_NONMATERIAL     flex UNRESOLVED
u_star_stable              point -0.9790   CI [-3.0497, +1.4857]
u_star_flex                point -1.0662   CI [-8.8934, +7.1659]
part_a                     d_a_point 0.5108
                           lower_contrast_lcb 4.3555  ucb 6.7021
                           upper_contrast_lcb 3.2979
```

As with H, `r4_freshness_sentinel` is a GATE and not a stored field: the pooler
exits non-zero if it fails, and it exited 0. Do not read its absence from the
JSON as a missing check.

### Against H, with the pooler held constant

H's shards were re-downloaded and re-pooled with today's pooler (which has not
changed since H -- `git log a00612ad..HEAD` on it is empty), so the comparison
below varies only the run:

```text
                       H            re-run       moved
branch                 PART_A_CONTRADICTION  (same)
limb_states            stable AFFIRMATIVE_NONMATERIAL / flex UNRESOLVED  (same)
d_a_point              0.4839       0.5108     +0.027
lower_contrast_lcb     4.3190       4.3555     +0.037
upper_contrast_lcb     3.3140       3.2979     -0.016
u_star_stable_point    -1.0920      -0.9790    +0.113
u_star_flex_point      -0.1644      -1.0662    -0.902
```

**The branch and both limb states are identical, and every u\* interval still
covers zero.** Two runs, across the repair and built on partially different user
worlds (below), reach the same conclusion. That is an unplanned replication and it
is the strongest thing in this note.

The point estimates moved, and they moved for a reason worth its own finding.

## A reproducibility defect, found while explaining the movement

If the focal events are identical, the point estimates should be too. They are
not, and running that down produced this:

**Same pinned topology, same user-world seed, three different worlds.** For
topology 20260736, calibration episode 0, all three of these agree on
`pinned_coordinate_hash = cd081d5c...`, `user_world_seed = 7782383802093937592`,
`episode_seed`, `n_users = 30`, and `seed_controls_generation = True`:

```text
local (numpy 1.26.3, python 3.10.20)   d700a69e7d23bd5a4a82b87b
H            (30403322062)             b5007214ae3e902783f6576d
re-run       (30479940700)             6307c329373ae9b30adaa741
```

Three different `episode_world_fingerprint` values. Between the two cloud runs it
affects **3 of 8 topologies** (20260736, 20260739, 20260740) on nearly every
episode, and the other 5 are identical. `requirements_d7s_audit.txt` hard-pins
`numpy==1.26.3` / `scipy==1.15.2` and the workflow pins python 3.10, so this is
not dependency drift between runs.

Ruled out by measurement, not by argument:

- **Code change.** `episode_world_fingerprint` returns the same value under H's
  module and HEAD's, for the same seed. `envs/pettingzoo/scenario7_energy_aware.py`
  is untouched between the two commits.
- **Construction order / worker scheduling.** Building episodes 0-3 forward, then
  building episode 3 first, gives identical fingerprints for every episode.
- **String-hash randomization.** `PYTHONHASHSEED` 0, 1 and 42 all give the same
  fingerprint.
- **Global RNG state.** Two successive constructions in one process, with
  different intervening RNG state, agree.
- **The pooler.** Re-pooling the same shards reproduces every summary field
  exactly, so pooling is deterministic; the difference is in the shards.

Locally it is stable across processes and orderings. What remains is
construction-time state that varies across machines -- and `ubuntu-latest` is not
one machine.

**The field that should have caught this asserts more than it tests.**
`seed_controls_generation`'s own docstring says True means "rebuilding this
episode at the same pinned topology and the same `user_world_seed` reproduces
this fingerprint". What it actually computes is
`int(applied) == int(seed_value)` and non-null -- that the seed was *applied*.
Both runs report `all_seed_controlled = True` over 128/128 episodes while
disagreeing about 3 topologies' worlds. A reproduction claim tested by a
seed-application check is the same shape of defect as a guard that cannot go red.

### What this does and does not touch

- **Does not touch** the focal events (bit-identical on 8/8), the branch, the
  limb states, support, conformance, `invalidated_pairs`, or the topology hashes.
- **Does touch** `selection_diagnostic` (differs on all eight; the re-run's flex
  selection is markedly more concentrated -- e.g. 20260739 flex[0] HHI 0.235 ->
  0.884), the point estimates above, and the credibility of
  `episode_world_fingerprint` as a cross-machine reproduction key.

The provenance fingerprint still does the job it was built for: proving **which**
world an episode ran in within a run. It does not support **regenerating** that
world on another machine, and the artifact currently claims it does.

## What is open, and whose call it is

Both of the following are scientific calls and are not settled here:

1. **Whether this closes round 4.** The re-run is a mechanically clean,
   post-repair, whole-population R4 artifact that passed the freshness sentinel
   and reproduces H's branch. What remains is whether an artifact whose point
   estimates are not bit-reproducible across machines can carry the R4
   conclusion, given that its branch and limb states are.
2. **The severity of the reproducibility defect** -- whether it is a disclosure,
   a required repair before any R4 claim is published, or grounds to re-scope the
   provenance contract.

Recorded for the next Pro touchpoint. `PART_A_CONTRADICTION` is not rewritten and
every shard JSON stays immutable.

## Apparatus repairs landed alongside this reading

- `scripts/d7_s_r4_rejoin_exposure_probe.py` -- the R4 seed namespace is now the
  default, rolling the R4 population under any other namespace is REFUSED, and
  the namespace is printed and recorded in `--out`. The silent default is what
  produced a void verdict that reached an evidence note.
- `tests/d7_s_r4_probe_namespace_test.py` -- six tests, including the premise
  test that keeps the guard from going vacuous if the two namespaces ever
  converge. Both guards were watched failing under paired-negative mutation and
  the source restored byte-identically.
