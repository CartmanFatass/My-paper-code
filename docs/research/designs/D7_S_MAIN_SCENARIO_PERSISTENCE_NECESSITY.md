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

**It preserves none of them.** The main scenario carries per-UAV state that
relabelling cannot move:

```text
uav_positions[n_uavs, 3]        uav_env.py:188 init, :250 written per agent from
                                that agent's own action; persists across steps
uav_battery_ratios[n_uavs]      scenario7:156, reset per UAV from a random range
                                (:472), depletes with that UAV's own motion
last_motion_energy_wh[n_uavs]   per-UAV motion cost
uav_charging[n_uavs]            per-UAV charging state
charging_wait_steps[n_uavs]     per-UAV queue wait at a station
uav_target_stations[n_uavs]     per-UAV docking commitment
uav_failure_timers / uav_failed  per-UAV failure state
uav_return_energy_margins        per-UAV return feasibility
last_actual_velocities[n_uavs,3] per-UAV kinematic state
```

And the external return depends on position through the physics, not through a
label:

```text
scenario7:1147   user_positions - uav_positions   -> access SINR -> capacity -> served rate
scenario7:1156   uav_positions - ground_bs_positions -> backhaul capacity
```

So for two UAVs `i` at `(p_i, b_i)` and `j` at `(p_j, b_j)`, having `i` take over
`j`'s duty is **not** the same joint state as `j` continuing it. Reaching `j`'s
position costs motion energy and elapsed steps, during which service degrades and
both battery margins move. The exchange is lossy in return, in energy, and in time.

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

**External-return horizon.** `H` is one slow window of the source, to be read from
the registered scenario-7 configuration rather than chosen here, with the
one-check-interval `Δ` retained as the secondary localization (D0 §3).

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
