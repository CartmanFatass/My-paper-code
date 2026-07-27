# The first full sweep of Scenario-7: a reward term can be deleted outright

Five anchors on `envs/pettingzoo/scenario7_energy_aware.py` had ever been
mutated. This is the first mechanical sweep of the file — constants, guard
clauses, quantifiers and formula terms.

Swept at `b67e824e`, suite baseline **45 passed**. Every finding below was
re-run by the Project Manager on the main tree, not only in the sweeper's
worktree. Each mutation was reverted with `git checkout --` and each revert
proven with `git diff --quiet`.

## The headline: the return-safety penalty is not in any test's reach

`_calculate_constrained_safety_reward` (`:808-814`) composes the reward for the
default arm-C configuration:

```python
else:
    safety_reward_before_pbrs = (
        qos_satisfaction_ratio
        - return_risk_penalty
        - cutoff_penalty
        - depletion_penalty
    )
```

**Deleting `- return_risk_penalty` leaves 45 passed.**

This is not a diagnostic. `scenario7_reward = safety_reward_before_pbrs +
potential_delta` (`:815`) → `shared_reward = float(reward_metrics["scenario7_reward"])`
→ `rewards = {agent: shared_reward for agent in self.agents}` (`:592-593`). It is
the literal per-step reward `env.step()` returns to every agent.

Three tests name this quantity —
`test_v2_return_risk_is_bounded_even_for_severe_deficit`,
`test_return_constraint_is_zero_for_positive_margins_and_uses_worst_uav`, and
`test_runtime_safety_dual_changes_only_adaptive_return_penalty`. All three assert
the standalone diagnostic field `metrics["return_risk_penalty"]`, which is
written independently of whether the term is ever summed into the reward. None
constructs a fixture where the term is non-zero *at the point the reward is
composed*: the ablation fixture pins margins to `+0.5`, safely inside the
feasible region, so `return_constraint_cost == 0` there.

This is the **bystander assertion** shape, on the reward itself. The guard is on
the sibling; the field that reaches the result has no test.

## The metrics-exposure test is a two-copies trap, confirmed

`test_constrained_safety_reward_metrics_are_exposed` was flagged as a possible
second copy of the production formula. It is. Its only substantive assertion:

```python
assert np.isclose(
    reward_info["scenario7_reward"],
    reward_info["safety_reward_before_pbrs"] + reward_info["graph_potential_delta"],
)
```

It does catch an **asymmetric** break — dropping `+ potential_delta` at one of
the three write sites reddens it. It does **not** catch a **consistent** one:
scaling the shared source variable

```python
potential_delta = self._graph_potential_reward(...) * 2.0
```

leaves **45 passed**. Both sides of the `==` derive from the same production
variable, so they move together and still agree.

A 2× error in the PBRS shaping term — reward-bearing, reaching the same `rewards`
dict — is invisible to the entire file. *Two copies of one formula agreeing prove
nothing*, on its second confirmed instance in this repository.

## The two heaviest reward weights are free to drift

| Constant | Mutation | Live value after | Suite |
|---|---|---|---|
| `cutoff_event_penalty` | `5.0 → 8.0` | `8.0` (read back through a constructed env) | **45 passed** |
| `depletion_event_penalty` | `10.0 → 15.0` | — | **45 passed** |

Both are live, not shadowed — the read-back is recorded because an inert mutation
already produced one false finding on this file today. Every ablation-arm
expectation reads `env.cutoff_event_penalty` back **as an attribute** rather than
pinning a literal, so both weights are self-referential in every assertion that
mentions them. These are the heaviest terms in the composed reward.

The acceptance-gate rule applies directly: *a table of expected values read out
of the code is a restatement, not a guard.*

## A failed UAV can be credited with charge

`_charging_candidates_by_station` (`:1780-1781`):

```python
if self.uav_failed[uav_idx]:
    continue
```

Deleting it leaves **45 passed**. No charging test sets `uav_failed=True` for a
candidate — every one sets `env.uav_failed[:] = False` explicitly, so the clause
is never exercised. A non-operational UAV recovering battery it should not have
reaches battery state → `_energy_failure_mask` → cutoff/depletion counts → the
5.0/10.0-weighted reward terms.

## Further unguarded constants, by reach

Confirmed by the sweep; reach as stated. Not individually re-run by the Project
Manager — recorded as sweep findings pending repair, not as verified record.

- `charging_hover_speed_threshold` `1.0 → 5.0` — the gate *value*, distinct from
  the gate *clause* repaired earlier today. The clause now has a guard; the
  threshold it compares against does not.
- `dock_request_threshold` `0.5 → 0.9` — `action[3] > threshold` (`:1558`), the
  actual gate deciding whether a UAV requests docking.
- `emergency_return_threshold` `0.05 → 0.15` — `_is_uav_in_limp_home` (`:1602`),
  which overrides the policy's commanded velocity.
- `return_threshold_min` `0.25 → 0.40` and `return_threshold_max` `0.60 → 0.80` —
  both unguarded. Note this is **not** an asymmetric pair but a full miss: the
  discrimination guard repaired earlier pins *far > near*, which no absolute
  bound change violates.
- `charging_power_w` `1000.0 → 500.0` — the charging rate itself; the test naming
  it computes its expectation from `env.charging_power_w`.
- `docking_vertical_speed_mps`, `charging_station_margin_ratio` — trajectory.
- `energy_reward_delta_min`, `w_energy_motion`, `w_energy_efficiency` — real but
  narrow, reaching only the `legacy_engineering` variant. `w_energy_efficiency`
  is largely a bystander and is recorded as such.

## Structural: a whole class of config fields is dead code

`_build_profile_overrides` (`:208-297`) unconditionally hardcodes a literal for
each of these keys, and `_EnergyAwareConfigProxy.__getattr__` (`:14-19`) consults
that dict **before** falling through to the base `Config`. Proven by forcing each
field to a `999.0` sentinel and reading it back through a constructed env — none
moved:

`charging_station_margin_ratio`, `charging_hover_speed_threshold`,
`charging_capture_radius_m`, `charging_power_w`, `docking_horizontal_speed_mps`,
`docking_vertical_speed_mps`, `max_vertical_speed_mps`, `dock_request_threshold`,
`limp_home_speed_mps`, `energy_reward_delta_min`, `energy_reward_delta_max`,
`w_energy_motion`.

`w_energy_motion` is the clearest case: `config_1.py`'s class default is `0.0`
and its S7 preset resets it to `0.0`, yet the constructed env reads `0.02`.

A second, different shadowing mechanism affects `battery_capacity_wh` and
`return_cost_cap`: `_apply_scenario7_energy_preset` calls
`apply_scenario7_experiment_arm`, and arm `"C"` — the default — re-sets both at
`config_1.py:632-633`, 139 lines after their first assignment.

**Consequence for method, not just for code.** Editing `config_1.py` for any of
these is inert, so any sweep that mutates there and reads green produces a *false
gap*. That already happened once today with `docking_horizontal_speed_mps`. The
standing rule now requires reading the value back through the object under test,
and this note is the enumeration that makes the rule cheap to apply.

## What came back clean

Genuine paired-negative coverage, confirmed by breaking it rather than by reading
it: the S4 minimum-active-fleet guard; `np.max → np.mean` on the worst-UAV
return-constraint reduction; the lowest-battery charging-slot selection under
inversion; and both of today's earlier repairs (the per-UAV cutoff/depletion
latch and the docking-speed clamp), which still hold.

## Not swept — read this before assuming the file is covered

- Eight communication/caching tests, three reward/potential tests, and two
  energy-bookkeeping tests were enumerated but not mutated.
- `test_legacy_ablation_restores_original_reward_weights` — the actual
  `legacy_engineering` reward path was not exercised end to end.
- `_apply_energy_dynamics` beyond the hover gate and the two guards above;
  `_get_state`/`_get_observation` beyond the repaired per-slot identity;
  `estimate_heuristic_qos_feasibility` and `estimate_rotation_charging_feasibility`
  internals.
- `n_charging_stations`, `max_energy_charging_stations`,
  `charging_station_capacity` — identified as shadowed, not mutated at their true
  location.
- **The "seven tests an earlier sweep never mutated" could not be recovered.**
  That list is referenced in the round record but never enumerated in any file,
  and appears to have existed only in a prior child's transcript. It is reported
  missing rather than guessed at.
