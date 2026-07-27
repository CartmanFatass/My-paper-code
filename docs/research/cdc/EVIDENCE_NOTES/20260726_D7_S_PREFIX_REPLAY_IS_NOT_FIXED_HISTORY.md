# The frozen "bit-identical prefix replay" was never bit-identical

Date: 2026-07-26 · branch `untied-k` · zero-compute + one bounded conformance
exercise (~4 min) · **no scientific result is read here**

## Claim

The superseded D7.S contract's fixed-history mechanism — *"bit-identical prefix
replay from reset — identical topology coordinates, initial-energy permutation,
**user-motion and channel streams**, source-control decisions before `t_e` …
asserted by a state hash before forking"* — **does not hold in the
implementation**, and the state hash it names structurally cannot detect the
failure.

Discovered before launch by `scripts/d7_s_clone_conformance_check.py`, written
to prove the shared-prefix clone path against the real environment rather than
against the test suite's fake env.

## Measured facts

Registered environment, Scenario-7 `S7-S3`, `user_distribution =
forced_relay_cluster`, `randomize_users = True`.

| Observation | Result |
|---|---|
| `reset(seed=S)` twice on the **same** env object | user positions **identical** |
| Two **fresh** env objects, **same** `seed=S` | user positions differ, `max|Δ| = 6547 m` |
| Two `build_pinned_env(...)` with identical args | user layout, cluster centres, waypoints, velocities all differ before a single step |
| UAV positions, `np_random` token after construction | **identical** |
| Two independent `replay_prefix(...)` to the same `t_e` | 24 attributes differ: `user_positions` (`max|Δ| = 4193 m`), `sinr_matrix`, `connections`, `last_user_rates_mbps`, `cluster_*`, `serving_set_changes`, `uav_joins_count`, `packet_id_counter`, … |

So the user population is fixed by **construction-time** state that
`reset(seed=…)` does not re-derive. `build_pinned_env` constructs a fresh env on
every call, so every call produced a different user world.

## Why the guard could not catch it

`compute_state_hash` hashes exactly: UAV positions, battery ratios, charging
mask, station occupancy, station queue, lifecycle mask, duty map.

It contains **no user state, no cluster state, no channel state**. The
assertion that was supposed to enforce the fixed-history guarantee was computed
over the one surface that stayed identical, while the surface that diverged by
kilometres was never inspected. The hash passed on every fork.

This is the same defect class as the already-ruled topology-provenance issue
(ground-BS and charging-station layout drawn from an unseeded RNG at
construction, Pro ruling 2026-07-26). The section 9 pinning procedure restores
BS and station coordinates after reset for exactly this reason. **Nobody
extended that reasoning to the user population.**

## What this invalidates

Under the superseded replay-every-prefix realization, each replicate — KEEP,
and every candidate's selection and evaluation streams — called `replay_prefix`
independently and therefore ran **against a different user population**.

`U*_m,src = V_SET − V_KEEP` would then have been dominated by user-layout
variance rather than by the focal intervention, and the contract's requirement
that *"SET and KEEP remain CRN-paired"* was not met at the prefix level. That is
a validity failure of the frozen design, not a cost or power problem. The 2-4
day projection that got the run cancelled was, in hindsight, buying a broken
comparison.

## What this vindicates

The R2 shared-prefix realization is **not merely an optimization**. One
canonical replay materialized as an immutable snapshot, with every continuation
cloned from it, is the first realization in which all arms of an event actually
share one user world. Correctness was the stronger reason for the change than
cost, and neither the ruling nor the Project Manager knew it at the time.

## Consequence for Stage-B condition 1

Condition 1 requires a clone continuation to be *"byte- or exact-numerically
identical to one obtained by the previous independent replay route under the
same continuation seed."*

As written it is **unsatisfiable, and inverted**: the reference route is
nondeterministic across calls, so the condition asks the correct mechanism to
reproduce the broken one. `verify_clone_equivalence_against_replay` returns
`equivalent=False` for this reason and not because cloning is faulty —
conditions 2-5 all pass on the real environment (mutation isolation, RNG
isolation, topology preservation, complete-state restoration), and `deepcopy`
of the real env costs 4 ms.

The scientifically meaningful restatement, for External Pro to rule on:

> Two continuations cloned from the **same** snapshot under the same
> `stream_seed` must be identical, and two clones under **different**
> `stream_seed` must differ only through the continuation stream.

That is checkable, and it tests the property the estimand actually needs.

## Open questions for External Pro (Stage B)

1. Does the restated condition 1 replace the original, given the reference route
   is nondeterministic by construction?
2. Two Scenario-7 episodes sharing a topology hash do **not** share a user
   population. Does topology identity remain the right comparability unit, or
   must the user layout be pinned and recorded alongside the coordinate hash?
3. Which previously closed Scenario-7 results compared arms built from separate
   env constructions, and are they affected? The ep64 single-topology diagnostic
   is the first to audit — it is already scoped to one realized topology, but
   its arms' user populations have not been checked.

## Status

No result is retired or rescued by this note. It records a repository fact and
the questions it forces. The D7.S audit does not launch until Pro rules on
question 1.

---

## Append 2026-07-26 (after the Stage B fence was sent, so not visible at that `stage_commit`) — the ep64 diagnostic shares the mechanism

Established by reading `scripts/audit_d7_s_persistence_margin.py`, zero compute.

`env = build_env()` sits **inside** the per-arm loop (`:495`, within
`for arm in arms:` at `:491`). Every arm of every episode therefore runs on a
**separately constructed** environment.

`build_env()` (`:419-452`) already documents this defect class from
2026-07-25 — topology drawn at construction before any seed exists, two
constructions differing by 2125 m in `ground_bs_positions` and 1487 m in
`charging_station_positions` — and fixes it by calling `_init_ground_bs()` and
`_init_charging_stations()` after `reset(seed=topology_seed)`, regenerating the
topology deterministically.

**It does nothing about the user population.** So the 2026-07-25 repair pinned
exactly the two surfaces it had measured and left the third moving. Every arm
comparison in that diagnostic —

```text
B_H       = mean(constructive) - mean(null)
U_stable  = mean(set_stable)   - mean(keep_stable)
U_flex    = mean(set_flex)     - mean(keep_flex)
```

— is therefore a comparison across **different user worlds**.

### The distinction that decides how bad this is

Because each arm gets its own independent fresh construction, the user layout is
independent and identically distributed across `(episode, arm)`. That is
**variance, not a directional bias**: the difference of means stays unbiased,
but the design is unpaired where it was believed to be paired.

The consequence is therefore entirely about the interval, not the point:

- if ep64's confidence procedure estimated dispersion **empirically from the
  observed arm samples**, the interval already absorbs the extra variance and
  the reported exclusions of zero remain usable, merely underpowered;
- if it assumed pairing or common random numbers anywhere, the interval is **too
  narrow** and `B_H = +65.965` / `U_stable = -40.602` "CI excludes zero" is
  false confidence.

That is a question about the registered confidence procedure's meaning, so it is
External Pro's, and it is exactly what Q2(c) of the Stage B round asks. This
append sharpens that question; it does not answer it, and it retires nothing.

Note the pattern worth carrying: the 2026-07-25 repair was correct about
everything it measured and silently incomplete about what it had not thought to
measure. The same shape recurred here. A fix that pins *the surfaces we
happened to check* is not a fix for *construction-time nondeterminism*.
