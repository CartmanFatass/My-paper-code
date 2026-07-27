# A world replacement was booked as a handover transition

`env.uav_leaves_count` was non-zero before the episode had stepped — 6 leaves,
12 joins, 18 serving-set changes. A UAV cannot leave a serving set before step
zero, so the counter was recording something that never happened.

## Mechanism

`build_pinned_env` calls `reset()` and then `regenerate_user_world()` by design.
Each runs a channel/connection/routing rebuild triple:

```text
scenario_base.py:2185-2186   reset()                 leaves 0 -> 0
scenario_base.py:2254-2255   regenerate_user_world() leaves 0 -> 6
```

The second pass is **not** the bug. The bug is that it diffed two *pair-disjoint*
user worlds and booked the entire outgoing serving cluster as departures.
`_update_channel_state` snapshots `old_connections = self.connections.copy()` and
hands it to `_update_soft_handover_stats` (`:2990`), which books
`len(old_set - current_set)` as leaves. Replacing the world is not a handover,
but the counter cannot tell the difference.

Always 0 or 6 because `randomize_bs` places the ground BS on boundaries, fixing
the reachable cluster size.

**Fix:** `_reset_connection_baseline()` extracted from `reset()` and called from
`regenerate_user_world()` before its rebuild. `reset()` behaviour is byte
identical. The test assertion was correct and was not weakened.

## Why it matters

Serving-set state at `t_e` is exactly what the D7.S event fingerprint covers. A
phantom leave before step zero corrupts the captured event state the result rests
on.

## Two corrections worth keeping

**The docstring pointed the wrong way.** The failing test named
`_update_uav_connections` and `previous_connections_snapshot`. Both are wrong —
`_update_uav_connections` writes UAV↔UAV and UAV↔BS links and touches no counter,
and the diff is against `self.connections`. That sent the first investigation to
four `scenario7_energy_aware.py` call sites which never execute.

**The failure was never order-dependent.** It was first diagnosed as order- or
global-state-dependent, from a bisect plus a matched control at the parent
commit. Measured afterwards: **8 passed, 2 failed over ten isolated runs** at the
unfixed parent. Every pairing in that bisect was a coin flip. Two samples cannot
separate a cause from a 20% coin — the rule this produced is in `AGENTS.md`.

Ruled out by test rather than argument: global `numpy`/`random` stream
contamination does not reproduce it; import-time side effects do not reproduce
it; a shared or class-level `Config` mutation is refuted, since `update_env_dims`
writes only instance attributes.

## Loose end, deliberately open

`scenario_base.py:328` — `self.np_random = RandomState(self.seed_val)` with
`seed_val` defaulting to `None`, so **every env seeds from OS entropy**, and
`reset(seed=)` does not re-derive `ground_bs_positions`. With `randomize_bs`
true, the ground-BS layout is drawn from entropy at construction and is not
reproducible from any seed passed later.

This is the same root fact task 14 worked around by pinning coordinates, and it
will keep producing luck-dependent tests wherever the construction-time layout is
load-bearing. Not fixed: changing it moves the estimand, so it is a Project
Manager or External Pro decision.

Verified: 10/10 isolated runs green with the fix versus 8/10 without; 219 passed
across the five-file D7.S set; full suite back to its pre-existing failures only.
