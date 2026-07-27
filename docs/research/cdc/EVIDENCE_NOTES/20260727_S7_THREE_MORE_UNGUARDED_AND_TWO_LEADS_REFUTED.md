# Three more Scenario-7 guards cannot fail; two reported ones can

A sweep on 2026-07-27 reported seven unfailable guards in
`tests/scenario7_energy_aware_test.py`. Two were reproduced by the Project
Manager at the time and are now **repaired** (`f4e4053f`). The remaining five
were carried forward as *the child's claims, explicitly not record*. This note
closes them.

Audited at `ec6c79ca`, suite baseline **44 passed** (42 plus the two guards added
by the repair above). Every mutation below was applied to the current tree by the
Project Manager, not only by the sweeping child, and every restore was proven
with `git diff --quiet` rather than a string compare.

**Three of five confirmed, two refuted.** A refuted lead is a result: it removes
an item from the repair list, so it was verified in the same direction as the
confirmations rather than taken on trust.

## Confirmed — the docking speed is a clamp tautology

`config_1.py:504`, `self.docking_horizontal_speed_mps = 3.0` → `1.0`.
Measured: **44 passed**. A threefold change in a commanded velocity, undetected.

The guard reads

```python
assert np.linalg.norm(velocities[0, :2]) <= env.docking_horizontal_speed_mps + 1e-6
```

against a production clamp of `min(self.docking_horizontal_speed_mps, ...)`. It
asserts the same live attribute the clamp uses, so the bound moves with the
value and the assertion is true for every setting. This is the *clamped value
inside its own clamp* shape, on its second instance in this file.

**It is trajectory-changing.** The speed gates the commanded velocity in
`_docking_velocity` (`scenario7_energy_aware.py:1577`) and `_limp_home_velocity`
(`:1612`), which is the velocity actually applied to `uav_positions` each step.
It changes travel time to station, therefore battery consumption, therefore the
cutoff and depletion events that carry the heaviest terms in `G`. It also feeds
the charging-schedule ETA estimator (`:1370-1398`).

## Confirmed — a reward term can be deleted outright

`scenario7_energy_aware.py:807`:

```python
safety_reward_before_pbrs = qos_satisfaction_ratio - depletion_penalty
```

Deleting `- depletion_penalty` leaves **44 passed**.

This is the `qos_depletion_penalty` ablation arm's defining term, and
`safety_reward_before_pbrs` feeds `scenario7_reward = safety_reward_before_pbrs
+ potential_delta` (`:815`) — the per-step reward returned to the agent, not a
diagnostic.

The cause is measured, not inferred. At the fixture's seed the five parametrized
reward-ablation variants realize **two** distinct numbers:

```text
qos_only                          0.0
qos_depletion_penalty             0.0
qos_fixed_safety                  0.0
qos_fixed_safety_graph_pbrs      -0.006723152043473513
qos_adaptive_safety_graph_pbrs   -0.006723152043473513
```

`depletion_penalty` is `0.0` at this seed and step, so subtracting it is the
identity and three of five parametrizations discriminate nothing. This is the
*fixture made degenerate for tractability deletes exactly the variance the
property is about* shape: the ablation is a parametrization in form and a single
case in fact.

`test_reward_ablation_variants_have_explicit_objectives` also recomputes its
expected value from metrics drawn from the same run's info dict, so even the
arms that do differ numerically compare the code against itself.

## Confirmed — every per-slot observation can be re-bound

`scenario7_energy_aware.py:2190`, reversing the slot offset:

```python
start = (min(self.n_uavs, self.max_energy_observed_uavs) - 1 - uav_idx) * self.energy_uav_obs_dim
```

Measured: **44 passed**. Every UAV's 13-field per-slot record — relative
position, battery ratio, charging flag, availability, load, target station, wait
time, return-threshold ratio, return-energy margin — is silently bound to the
wrong UAV and nothing notices.

**Reach is observation only, and that is recorded as the lower severity it is.**
The array is concatenated into `observation["obs"]` (`_get_observation`,
`:2146-2153`) and consumed by the policy every step; it is not read by
`compute_G`. The only test touching this structure,
`test_observation_and_state_use_fixed_team_and_station_identity` (`:316`), checks
dimensions (`energy_obs_extra_dim == 8*13 + 2*8`) and never a field's content.
A shape assertion cannot see a permutation.

## Refuted — `set_scenario7_safety_dual` is guarded

The lead held that no test observes the setter's effect, making its name the
only assertion. Making the setter a no-op (`:627`) gives **1 failed, 43 passed** —
`test_runtime_safety_dual_changes_only_adaptive_return_penalty` goes red. That
test asserts `return_risk_penalty == 3.0 * return_constraint_cost`, and
`return_risk_penalty` is subtracted from `scenario7_reward` (`:811`), so it
asserts a reward-relevant field rather than a bystander. The guard works.

## Refuted — the station layout does reproduce, for what the guard claims

The lead held that the charging-station layout does not reproduce across
processes. Split into the two cases it was conflating:

- **The pattern the test actually uses** — `make_env("S7-S3", seed=123)` then
  `reset(seed=123)` — produced **byte-identical** `charging_station_positions`
  across three separate interpreter processes.
- **Construction with no seed**, then `reset(seed=999)`, differed across three
  processes (station 0 at `[3034.38, 6420.37]`, `[4489.60, 1647.53]`,
  `[4835.65, 1597.32]`).

The second is the **already-documented entropy default**, not a new gap:
`np_random = RandomState(seed_val)` with `seed_val` defaulting to `None` draws
`ground_bs_positions` from OS entropy at construction, and the service-anchored
station layout inherits it because `_sample_service_anchored_station_xy`
(`:370-383`) anchors on `_charging_station_anchor_points()` (`:385-401`), which
reads `ground_bs_positions`. `reset(seed=)` does not re-derive it. No test in
this file claims coverage of the unseeded path.

The existing guard was additionally shown to be failable: replacing the seeded
draw with `np.random.uniform` gives **3 failed, 39 passed**, with
`test_s7_s3_uses_load_balance_and_seeded_station_layout` among them.

**This is the case the standing rule exists for** — a documented modelling choice
reported as a defect. Filing it would have sent an implementer to "fix" a
deliberate semantic, which is the exact failure that made verification mandatory
on 2026-07-27.

## What this run of the method says

Five leads, three real. The two refutations were both *plausible* — a setter with
no visible observer, and a layout that genuinely is unreproducible under a
neighbouring construction path. Neither survived a mutation. The sweep's value is
that it is mechanical in both directions: it cannot be talked into a finding by a
suspicious-looking test, and it cannot be talked out of one by a reassuring name.

The three confirmed instances bring this file to five known unfailable guards,
against twelve in the D7.S line. Both totals are still rising per sweep, which is
the argument for sweeping mechanically before reading.

## Not swept

Only the five named anchors were mutated. A full mechanical enumeration of the
2,287-line environment — every guard clause, every registered constant, every
quantified tuple — has **not** been run on this file. The earlier sweep also
named seven tests it never mutated, plus the observation that
`test_constrained_safety_reward_metrics_are_exposed` is a second copy of the
production formula. None of that is covered here, and the file must not be read
as audited.
