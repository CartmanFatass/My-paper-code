# The pinned environment's complete-state identity is within-process only

Two `build_pinned_env` calls with **identical** `episode_seed`, `coords`,
`coord_hash` and `user_world_seed` produce **different** `full_state_fingerprint`
values. Measured 2026-07-27 at `344b6ce9`: 4 distinct fingerprints in 4 fresh
constructions, and they never converge — still distinct after 1, 5 and 20 steps.

This was found by asking what the rewritten fingerprint actually certifies before
quoting it in a review round, not by a failing test. No test asserts this
property, in either direction.

## Mechanism

`build_pinned_env` runs `reset()` (step 4) and only then overwrites
`charging_station_positions` with the registered coordinates (step 5). `reset()`
has by then already derived the station-relative logistics quantities from the
**construction-time** layout, which `scenario_base.py:328` draws from OS entropy
(`RandomState(self.seed_val)`, `seed_val=None`). Steps 6 and 8 rebuild channel,
routing and the user world; they do not recompute those logistics.

Six attributes diverge at step 0:

| Attribute | Behaviour |
|---|---|
| `last_min_station_distance_before` / `_after` | stale: distance to a discarded station layout |
| `uav_return_threshold_ratios` | stale — measured `0.56` vs `0.27`, a 2× spread |
| `uav_return_energy_margins` | stale |
| `current_graph_potential` | stale |
| `state` | contains the above |

`uav_positions` and `user_positions` are **identical** across constructions, which
is why the divergence is not visible as an obvious world difference.

**The first `step()` recomputes all six.** After one step the logistics agree
exactly. What survives is one step's worth of contaminated potential difference:
`Φ(s₁) − Φ(s₀)` with `Φ(s₀)` stale. That offset is accumulated permanently, and
after 20 steps exactly two attributes still differ:

```text
episode_graph_pbrs_sum          A=-0.1684488362014125   B=-0.0797471384862988
last_constrained_reward_metrics dict, 62 keys, carries the same term
```

## What this does not reach

- **The estimand.** `compute_G` is analyzer-computed from component fields and
  its docstring states it "never reuses `safety_reward_before_pbrs`"
  (`audit_d7_s_event_aligned.py:622`). The contaminated quantity is a PBRS
  accumulator, so it does not enter `G`, `U*` or `B_m`.
- **The SET/KEEP contrast**, on a second and independent ground. Both
  conclusion-bearing call sites — `:2926` calibration, `:3239` audit episode —
  build **one** env per episode and clone every limb from it, so all limbs of an
  event share one offset and it cancels in `mean(eval_set) − mean(eval_keep)`.
- **`episode_world_fingerprint`.** It digests only the nine user/cluster arrays,
  every one of which was measured identical. The R3 §E provenance record
  reproduces.
- **Cross-shard pooling.** `pool_d7_s_event_aligned_shards.py` asserts no
  fingerprint equality between shards; it keys on the seed set.
- **`replay_prefix_to_te` (`:2271`)**, the one call site that *does* compare a
  freshly-built env against an original rollout. It asserts `compute_state_hash`,
  whose seven keys exclude all six contaminated attributes.

## What it does mean

`full_state_fingerprint` certifies **within-process** identity — one live
environment against its own clones — and not reproducibility of a pinned
environment across invocations. Every current use is within-process, so nothing
in the instrument is wrong today.

It is written down because the name and the docstring both invite the wider
reading, and R3 §C calls it the complete-state identity surface. A future reader
comparing two shards' fingerprints would get a mismatch and conclude the wrong
thing.

## Standing

Not a Stage B blocker: no frozen R3 assertion is violated, and the estimand is
untouched. Recorded as a scope statement on the fingerprint, plus one more piece
of evidence for the `scenario_base.py:328` loose end already open in
`20260727_D7_S_WORLD_REPLACEMENT_BOOKED_AS_HANDOVER.md` — construction-time OS
entropy keeps surfacing wherever a construction-time quantity is load-bearing,
and this is its third instance.

Reordering `build_pinned_env` to recompute the logistics after pinning is an
implementation binding, not a contract change: it would make step-0 state
reproducible and remove the PBRS offset, at the cost of a slightly different
step-0 state than every measurement taken so far. Not done here, because it moves
the trajectory and no result depends on it either way.
