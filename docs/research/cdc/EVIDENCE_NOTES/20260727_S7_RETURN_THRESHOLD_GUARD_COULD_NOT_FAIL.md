# The dynamic return threshold had no guard that could fail

External review found unfailable guards on this project in three consecutive
rounds. Two sweeps had covered the D7.S audit and pooler test files. This one
covers the **environment** the audit measures, on the reasoning that a
Scenario-7 guard that cannot fail lets an environment defect through into the
result — which is exactly how the world-replacement defect got as far as it did.

Audited 2026-07-27 at `dc83085c`.

## The finding

`test_dynamic_return_threshold_and_service_cutoff_are_separate`
(`tests/scenario7_energy_aware_test.py`) made two assertions about
`uav_return_threshold_ratios`, and neither could fail.

**1. The clamp asserting its own bounds.**

```python
assert env.return_threshold_min <= env.uav_return_threshold_ratios[0] <= env.return_threshold_max
```

The production code ends with `np.clip(..., return_threshold_min,
return_threshold_max)`. The assertion is therefore true for **every**
implementation that clamps, including one that ignores distance entirely.

**2. Two copies of one formula agreeing with each other.**

```python
assert np.isclose(env.uav_return_energy_margins[0], env._raw_return_energy_margins()[0])
```

`_update_return_energy_state` and `_raw_return_energy_margins` each write out
`battery - required_ratio - reserve` independently — the same arithmetic, twice.
Both sides of the comparison come from the code and neither from an independent
source of truth, so a wrong formula moves both together and the test stays green.

## The green-leaving mutation

Replacing the threshold with the constant `return_threshold_min`, so it no longer
depends on distance at all:

```python
thresholds[uav_idx] = np.clip(self.return_threshold_min,
                              self.return_threshold_min, self.return_threshold_max)
```

Measured: **42/42 green** in the scenario-7 file, **197/197 green** across the
D7.S set. Nothing in the repository catches it. (Four failures in
`run_uav_temp_loss_g1_test.py` are pre-existing — the same four fail with the
mutation reverted — and belong to another line.)

## Does it reach a claim?

**Not directly, and the distinction matters.** `compute_G` includes
`- 2·return_constraint_cost`, but `return_constraint_cost` is computed from
`_raw_return_energy_margins()`, **not** from the threshold. The threshold does
not enter primary `G` as a term.

**It is nonetheless behaviour-bearing**, on two paths:

- `scenario7_energy_aware.py:1908` and `:2035` — `battery <= threshold` is the
  return-to-charge trigger, so a constant threshold changes when UAVs return and
  therefore the trajectory the audit measures;
- `:2250` — it is observation feature 7, so the policy sees it.

Because the audit measures trajectories under scripted source control across
SET/KEEP limbs, a wrong threshold moves the thing being measured even though it
is not a term in the estimator. Recording the indirect path as indirect: over-
accepting a plausible finding is the same failure as under-checking a test.

## The repair, and both reds observed

- **Discrimination on distance.** A UAV in the far corner must carry a strictly
  higher threshold than one parked at a station. No constant satisfies it, and
  it re-derives no physics. Observed RED against the constant mutation:
  `got far=0.25 near=0.25`.
- **An independent arithmetic path for the margin.** The test now recomputes
  `battery − (distance/speed · power/3600)/capacity − reserve` from its own
  literals rather than calling the production helper. The power figure is a
  pinned input, separately fixed by
  `test_power_model_hover_endurance_matches_current_defaults`. Observed RED
  against dropping the reserve from **both** copies of the formula — the exact
  shape the old assertion was blind to: `0.3830 vs 0.2830`.

239 tests green after the repair.

## Second finding, same file, heavier: the latch was never tested per-UAV

`test_cutoff_and_depletion_events_fire_once_per_uav` is otherwise a good test —
it drives the real `_calculate_constrained_safety_reward` and asserts
`first == 1, repeated == 0`, which no always-latch and no never-latch
implementation satisfies.

**But every assertion drives UAV 0 alone**, so the "per uav" in its name was
untested. A **fleet-global** latch — one flag for all eight UAVs — passes it.

Green-leaving mutation:

```python
new_cutoff    = cutoff_mask   & (not bool(self.cutoff_event_seen.any()))
new_depletion = depleted_mask & (not bool(self.depletion_event_seen.any()))
```

Measured: **214/214 green** across the scenario-7 and D7.S audit files. The
production implementation is correctly per-UAV (`cutoff_event_seen` is a boolean
array); nothing proved it.

**This one is directly claim-bearing, and it is the heaviest term.** `compute_G`
subtracts `5·new_cutoff_count + 10·new_depletion_count`. A global latch
undercounts both the moment a *second* UAV crosses a threshold — the ordinary
case in an eight-UAV fleet under energy stress — so `G` comes out systematically
high. D7.S's window-local latching counts exactly these events. Unlike the return
threshold above, this needs no behavioural path: it is arithmetic straight into
the primary quantity.

Repaired by exercising a second UAV and asserting its first event counts despite
UAV 0 having latched, plus that it then latches too. Two reds observed:

- global latch → `UAV 1's first cutoff must count …` fails;
- latch removed entirely → the repeat assertions fail, so the repair cannot be
  satisfied by deleting the latch.

## The pattern, on its fourth and fifth instances

Most cases share one cause: **the test was written from the implementation, so
both sides of the comparison come from the same code path.** These two add
variants worth naming separately:

- *asserting a post-condition the code structurally guarantees* — a clamped value
  inside its clamp, a sorted list being sorted, a normalized vector having unit
  norm. Reads as a property check; is a tautology about the code's shape rather
  than its correctness.
- *the name quantifies over a domain the test never varies* — "once **per uav**"
  driving one UAV, "for **every** field" mutating one field, "across
  **processes**" run in one. The claim is in the name and the coverage is not.
  Read the test's own name as a specification and check the quantifier.

The second is the cheaper sweep and probably the higher yield: it needs no
reasoning about the implementation at all, only a comparison between what a test
is called and what it does.
