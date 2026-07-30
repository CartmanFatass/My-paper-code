# Reconciliation -- R4 rerun disposition

Ruling: `21_PRO_OPEN_RAW.md`, stage `45d876b9`.
Round outcome: **both of my headline conclusions are refuted.** Neither H nor the
re-run is rehabilitated, and the provenance defect is claim-blocking.

```text
4a  retract H's invalid disposition           NO
4b  retract it for the earlier R4 artifact    NO
6a  does the rerun carry R4's conclusion      NO
6b  missing property   reproducible evidence-population identity
6c  classification     EXPLORATORY_BRANCH_ROBUSTNESS_UNDER_UNREGISTERED_WORLD_VARIATION
D3  severity           claim-blocking repair before any formal or published R4 claim
```

## The mechanism I missed, verified in source before accepting it

Pro's Challenge 1 is the one that kills the exoneration, and I checked it rather
than taking it:

`scripts/audit_d7_s_event_aligned.py:3681-3687`, inside `fork_continuation`:

```python
if focal_uav is not None and t == int(delta_steps) - 1:
    duty_map = constructive_mixed_update(
        duty_map=duty_map, duty_positions=step["duty_positions"],
        airborne_positions=airborne_positions, event="REJOIN",
        event_uav=focal_uav, locked_duties=locked_duties)
```

**Every focal SET continuation invokes the REJOIN branch directly, once, at
`t = DELTA - 1`.** That is precisely the branch the repair `23fecff3` changed --
its early return fires when the rejoining UAV already appears in the duty map,
which is exactly the state a virtual LEAVE plus re-match among survivors can
produce. So the repaired code is executed on conclusion-bearing paths *even when
`roll_power.rejoin_events` is zero*, because my counter only sees environment
falling-edge REJOINs inside `roll_prefix_and_find_event`.

Also verified: `REJOIN_BATTERY_RATIO = 0.80` (line 95), `H_STABLE = 139`,
`H_FLEX = 550` (lines 102-103).

My claim "the repaired branch never executed" was false. The instrument I built
answers a narrower question than the one I used it to answer, and I did not check
its coverage against the code paths that produce the estimates.

## My own probe then falsified my other claim, without help

I had written that the horizon argument was the claim I most wanted attacked, and
set the corrected probe up as a falsification test with a stated prediction: it
rolls a fixed 950 steps, 950 < 1167, therefore it *must* return
`ZERO_WITH_POWER`.

It returned **`R4_REJOIN_PROBE_FIRED`**, under the correct namespace
`D7_S_R4_ABSOLUTE_FOCAL_MARGIN`:

```text
32 rolls x 950 steps = 30,400 steps   leaves 31   rejoins 3
                                      charging_steps 2475   refusals 0
                                      injectivity_checks 60,800
  20260734 calibration ep0   rejoins=1   charging_steps=113
  20260736 audit       ep1   rejoins=1   charging_steps=28
  20260739 audit       ep0   rejoins=1   charging_steps=79
```

**Environment REJOINs occur on R4 episodes inside 950 steps.** The structural
unreachability claim is dead by measurement, on the right population, exactly as
Pro's Challenge 3 predicted and for Pro's stated reason: the controller releases
at `REJOIN_BATTERY_RATIO = 0.80`, so my 2%-to-100% arithmetic used the wrong
terminal condition. 2% to 80% is ~449 steps, and the earliest capture at 602 puts
a release at ~1051 -- still past the prefix cap, which is why the prefix count is
zero, and *not* past the continuation windows.

`20260734 calibration ep0` is the sharpest case: the formal run reports zero
rejoins for that block, and the probe finds one in that very episode. The formal
roll truncates at the first qualifying LEAVE -- 7108 steps over 8 episodes, ~888
average against a 950 cap -- so it stops before the rejoin. That is Pro's
Challenge 2 demonstrated on a single episode: `steps_rolled` is prefix-only and
excludes the 139- and 550-step continuations that actually produce `D_A` and
`U*`.

## What survives

- Zero **environment falling-edge REJOINs on the main prefix paths** of the
  re-run, with 225,048 injectivity checks and zero refusals. A real measurement of
  a narrower quantity than I claimed.
- `roll_power.leave_events` equals `len(report["leaves"])` in all sixteen blocks,
  so the new counter is corroborated by an independent pre-existing field.
- The withdrawal of the original probe verdict stands on its own grounds: it did
  roll the wrong seed namespace, and that finding is unaffected by the fact that
  the corrected probe reaches the same qualitative verdict. Right conclusion from
  a wrong measurement is still a wrong measurement.
- The re-run is preserved as a conditional within-run observation and as
  `EXPLORATORY_BRANCH_ROBUSTNESS_UNDER_UNREGISTERED_WORLD_VARIATION`. It carries
  no confirmatory weight.
- H and the earlier R4 artifact keep `INVALID_R4_REALIZATION:
  DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`, with Pro's sharpened reason: H
  does not establish that its complete conclusion-bearing assignment paths are
  equivalent to the repaired realization.

## What I got wrong, named plainly

1. **Coverage.** I read `rejoin_events = 0` as "the branch never ran" without
   checking which code paths the counter spans. It spans the prefix only.
2. **Terminal condition.** I used full charge where the controller uses 0.80.
3. **Horizon.** I treated `T_E_MAX = 950` as the end of the measurement. It bounds
   the event search; 139 or 550 continuation steps follow.
4. **Event identity as trajectory identity.** Identical `audit_events` do not
   imply identical `audit_units_*` / `calibration_units_d_a`; those are serialized
   separately and are what the estimates are computed from. The measured fact that
   events agreed while point estimates moved was sitting in my own comparison
   table, and I treated it as a puzzle about provenance instead of as
   counter-evidence to the equivalence claim.
5. **Cross-run lending.** I let a zero from one run speak for an unrecorded field
   in another, across worlds now known to differ on 3 of 8 topologies.

The pattern in 1-4 is one thing: I measured something real, then reported the
conclusion I wanted rather than the conclusion the measurement's scope supported.

## Required repair, as ruled

Severity is **claim-blocking**. Disclosure is insufficient, and re-scoping the
provenance contract to within-run identity after seeing the result is a post-hoc
change to evidence semantics.

Selected repair family -- **persist and replay the complete world manifest**:

1. generate the episode world once under a registered generator;
2. persist the complete initial user/cluster manifest, not only its hash;
3. make every formal episode load that manifest;
4. verify its canonical digest before stepping;
5. separate manifest identity, episode/continuation RNG, topology identity and
   energy permutation.

Live alternative: a deterministic pure seed-to-world generator, gated by a
**cross-process and cross-machine** conformance check -- one machine is
insufficient, because one machine is exactly where the current generator looks
stable. Parked: machine as a registered random factor.

## Scheduled next action, and the constraint on step 1

The next artifact is an **episode-world provenance correction and root-cause
localization**, not another R4 run:

1. compare component digests and identify the first differing world array;
2. identify every writer and random source for that array;
3. freeze either manifest replay or deterministic generation;
4. define a cross-machine fail-closed conformance gate;
5. only then design fresh confirmatory evidence.

**Step 1 cannot be done from the artifacts in hand.** `component_digests` was
added after both runs, so H and the re-run record only the combined fingerprint.
Locally the digests are stable -- measured, including under perturbed global RNG
state, all nine arrays identical -- so a local comparison cannot localize a
cross-machine divergence. Step 1 therefore needs component digests for a frozen
set of episode keys from a second machine, which is small apparatus compute rather
than a result run.

Pro's Challenge 6 is explicit that "machine-dependent construction state" must not
be frozen as the causal conclusion until the digest comparison names the first
differing surface. I have recorded it as the surviving hypothesis, not the cause.

## Documentation reconciliation ordered by Challenge 7

Two stale reproducibility claims remain and are corrected separately from the
generator:

- `user_world_seed` still says the seed makes the draw reproducible and recorded;
- `full_state_fingerprint` still says `episode_world_fingerprint` reproduces
  across constructions.

Neither repairs the generator; both currently assert the property Pro just ruled
unestablished.

## Unchanged

No threshold, no R4 topology, no result branch, no historical JSON. `D7.3` and
`D8` remain blocked. This round authorizes neither a new formal run nor
publication of the current R4 branch as a confirmatory result.

## Disclosed: one number in the question was corrected after the fence

§2 of the question said "charging onset sits near step 900", imported from the
development topology. After the fence I measured it on R4 itself -- earliest
capture 602, median 873 over 109 leaves -- and committed that at `c7db6127`. Pro
read the pre-correction number. The correction makes no difference to the ruling:
the argument it supported is refuted on its terminal condition and its horizon,
not on its onset, and both 900 and 602 lead to the same refuted conclusion.
