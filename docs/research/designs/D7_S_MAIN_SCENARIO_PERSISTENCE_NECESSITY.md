# D7.S — main-scenario persistence-necessity audit

```text
id=D7.S
status=part A complete (structural, repository fact); part B frozen, not yet computed
cost=zero compute
ordered_by=rounds/20260725_d7_2b_source_persistence_necessity/21_PRO_OPEN_RAW.md  (order 1)
source=envs/pettingzoo/scenario7_energy_aware.py  (UAVEnergyAwareRelayEnv)
        envs/pettingzoo/uav_env.py                (base motion and positions)
gate=AGENTS.md, "A positive control must make its target behaviour necessary"
estimand=D0_CARRIER_AND_ESTIMAND.md, U*_{i,src}
```

D7.2B was retired because its source admitted an optimal policy in which no
commitment persists. This audit asks the same question of the source the paper
actually claims about, **before** anything else is built. Pro ordered it as the
immediate successor rather than a replacement toy, because a positive control
cannot rescue a main benchmark that does not require individual persistence.

The audit splits in two, and the split matters:

| Part | Question | Depends on a freeze? |
|---|---|---|
| **A** | Does a full-sync role permutation preserve the state carried over `H`? | **No** — it is a repository fact about the transition function |
| **B** | Is the persistence margin **material**, `U*_stable,src/B_H <= -0.10` and `U*_flex,src/B_H >= +0.10`? | **Yes** — it is an estimand and must be frozen first |

Part A is answered below. Part B is frozen below and not computed, so no branch is
claimed yet.

## Part A — the permutation test, answered

Pro's instruction was to test explicitly whether a full-sync role permutation
preserves external return, physical state, energy, position, queue/service state,
communication or topology state, and anything else carried across the horizon.

**It preserves none of them** — but the list below is **stage-gated**, and the
correction matters enough to state before the evidence rather than after.

`_build_profile_overrides` sets `battery_enabled: False` and
`charging_enabled: False` in the base profile, and the default stage is **S1**
(`scenario7:42`), where `w_energy_failure` is also `0.0`. So **at S1 the energy
state does not bind at all**, and every battery, charging, docking and failure term
below is inert. They become symmetry breakers only at the stages that enable them.

Independently: the endurance numbers say energy would not bind at S1 even if
enabled. Hover power is `P0 + Pi = 79.86 + 88.63 = 168.49 W`
(`scenario_base.py:504-529`, parasitic and vertical vanish at rest), against
`battery_capacity_wh = 160.0` and `time_step = 1.0 s` — about **3,419 steps of
hover endurance against a 500-step episode**.

**What survives at every stage is position**, and it is sufficient on its own:

```text
ALWAYS ACTIVE
uav_positions[n_uavs, 3]        uav_env.py:188 init, :250 written per agent from
                                that agent's own action; persists across steps
last_actual_velocities[n_uavs,3] per-UAV kinematic state

ONLY WHEN battery_enabled / charging_enabled  (not at the default stage S1)
uav_battery_ratios[n_uavs]      scenario7:156, reset per UAV from a random range
                                (:472), depletes with that UAV's own motion
last_motion_energy_wh[n_uavs]   per-UAV motion cost
uav_charging[n_uavs]            per-UAV charging state
charging_wait_steps[n_uavs]     per-UAV queue wait at a station
uav_target_stations[n_uavs]     per-UAV docking commitment
uav_failure_timers / uav_failed per-UAV failure state
uav_return_energy_margins       per-UAV return feasibility
```

And the external return depends on position through the physics, not through a
label:

```text
scenario7:1147   user_positions - uav_positions   -> access SINR -> capacity -> served rate
scenario7:1156   uav_positions - ground_bs_positions -> backhaul capacity
```

So for two UAVs `i` at `p_i` and `j` at `p_j`, having `i` take over `j`'s duty is
**not** the same joint state as `j` continuing it. Reaching `j`'s position takes
elapsed steps at a bounded speed, and during those steps the served rate is
whatever the *in-transit* geometry gives, not the settled one. The exchange is
lossy in return and in time at every stage, and additionally in energy wherever the
battery is enabled.

**And the flexible duty is real.** Users are **not** static: `_move_users()` runs
every step (`scenario_base.py:3172`) as RPGM cluster mobility or random walk, with
cluster pause times. So the source genuinely contains the two timescales the paper
describes — a backhaul/relay geometry that wants to persist, and a service
assignment that wants to re-decide as users move. That is the mixed-urgency
structure the toy was supposed to stand in for, present here in the source itself.

*(A previous note in this line stated users were static. That was wrong — it came
from grepping only `uav_env.py`, where the mobility update does not live.)*

**Consequence.** The specific failure that retired the toy —
`ZERO_COST_ROLE_EXCHANGE_SOURCE` — is **structurally absent here**. The toy's
degeneracy came from a reward that read only the unordered pair of duties, with no
agent-local state at all; this source is the opposite case, and it is exactly the
case Pro's narrowed class statement carves out as still usable:

> An anonymous source stays usable when assignment history is non-transferable.

Anonymity is intact — the environment names no relay or service role in any
observation the controller reads — while free exchange is not available.

**What Part A does not establish.** Lossy exchange is necessary for persistence to
matter, not sufficient. A source can make exchange costly and still leave the
persistence margin negligible — for instance if UAVs are dense enough that any
neighbour substitutes at trivial cost, or if the horizon is short enough that the
motion penalty never materializes. **Claiming `PERSISTENCE_NECESSARY_SOURCE` from
Part A alone would be exactly the inference error that cost D7.2B a run**: reasoning
from structure to a margin without computing the margin.

## Part B — frozen before computation

Frozen here, per Pro's list, and not yet evaluated.

**Mixed-urgency history class.** A history at a shared check where at least one
active commitment is *stable* — its served-user assignment and backhaul role are
unchanged over the next slow window — and at least one is *flexible* — its served
users have moved or its access link has degraded enough that a different skill is
preferable now. Both determined **in the evaluator only**, from realized user
motion and link state, never from a role name.

**External-return horizon — resolved 2026-07-25, and it is not "one slow window".**

Unlike the toy, this source has **no finite slow period**. `ground_bs_positions` is
written at reset only (`scenario_base.py:583-586`; `randomize_bs` acts there and
nowhere else), so the backhaul geometry is static for the whole episode and the
relay duty's *target never changes*. "One slow window" is therefore ill-defined
here, and D0 §3 already anticipates that case: *"For the main scenario `H` is frozen
from its causal duty window before the audit runs."*

The causal duty window is the **transit time of a duty exchange**, because that is
the interval over which the exchange's cost is realized. From the registered
constants (`config_1.py`):

```text
area_size      8000 m        max_speed  30 m/s      time_step  1.0 s
k = Delta      10 steps      episode    500 steps   n_ground_bs 1
user_max_speed 15 m/s

mean separation of two uniform points in a square   0.5214 * 8000  = 4171 m
characteristic transit                              4171 / 30      = 139 s
                                                                   = 139 steps
```

So **`H = 139` steps**, read from the source rather than chosen, with `Δ = 10`
retained as the secondary localization.

**The scale is the finding.** A duty exchange costs about **14 check intervals** and
more than a quarter of a 500-step episode. Even a close pair 1000 m apart costs 33
steps, still 3.3 check intervals. The decision cadence is an order of magnitude
faster than the exchange it would have to pay for: by the time a swap completes,
roughly fourteen further decisions have been offered. With `n_ground_bs = 1` there
is a single backhaul anchor, so a relay abandoning its bridging position is not
substituting one equivalent geometry for another — it is vacating a bottleneck.

**What this still does not establish.** The margin is normalized:
`U*_stable,src / B_H <= -0.10`. A large transit cost in *steps* does not by itself
clear a *normalized return* threshold — that depends on return lost per step of
degraded geometry against the constructive-minus-null gap `B_H`, which is not yet
measured. The remaining work for part B is exactly `B_H` and the two margins;
everything else in this freeze is now fixed from repository facts.

**Legal joint continuation.** All agents other than the focal one, and all later
decisions, take their **best legal continuation** in both terms. This is what makes
`U*_src` a source property rather than a policy artifact, and it is the difference
from `U_max_pi`.

**Source-level oracle / constructive controls.** A constructive controller that
holds a stable assignment while renewing a flexible one, and a full-sync
alternative that reassigns every duty at each check. Both must respect the real
transition function — motion, energy, charging queues — so the full-sync arm pays
the physical cost of the exchange rather than teleporting.

**Normalized persistence margin.**

```text
U*_stable,src / B_H  <=  -0.10        U*_flex,src / B_H  >=  +0.10
```

`B_H` is the constructive-minus-null gap measured from source controls before the
comparison, averaged over windows starting at check boundaries — never from a
step-0 window, which on the toy collapsed `B_5` to exactly zero.

**Branch meanings.**

| Branch | Meaning | Consequence |
|---|---|---|
| `PERSISTENCE_NECESSARY_SOURCE` | material margin on both sides | proceed to D7.3; the replacement toy is unnecessary |
| `ZERO_COST_ROLE_EXCHANGE_SOURCE` | full-sync exchange reaches the optimum | main source is non-identifying; requalify it, keep D8 blocked |
| `SOURCE_NECESSITY_UNRESOLVED` | margin not established either way | tenure control advances carrier capacity only; D8 stays blocked |

Part A rules out the middle branch structurally. The remaining question is whether
the margin clears `0.10`, i.e. `PERSISTENCE_NECESSARY_SOURCE` versus
`SOURCE_NECESSITY_UNRESOLVED`.

## What this changes now

`D8` remains blocked in every branch until Part B resolves. Nothing here authorizes
implementation or compute — the ruling that ordered this audit authorizes neither.

The cheapest route to Part B is a derivation or an exhaustive/constructive control
on a small registered scenario-7 instance, not a training run. Per
`AGENTS.md`, *Result interpretation*: derivation, then counterexample construction,
then reanalysis, before any toy or formal compute.
