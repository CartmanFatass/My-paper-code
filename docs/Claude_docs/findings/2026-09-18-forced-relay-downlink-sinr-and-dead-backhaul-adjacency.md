# Finding: `UAVForcedRelayEnv` base-to-UAV SINR is ~146 dB below the uplink, leaving `uav_bs_connections` identically False

**Date:** 2026-09-18
**Discovered by:** Claude session, while implementing scene capture for the research support suite
**Status:** REPORTED, NOT FIXED. No change to environment dynamics, observations or reward was made.
**Base commit:** `ef6cb091a621bf04a734878346dbd8860a1ebe59`
**Scope note:** this was found incidentally. It is a scientific-semantics question about a shared
environment, so it is recorded here instead of being repaired under a visualization patch.

## What was observed

`envs/pettingzoo/relay/forced_relay.py` computes the UAV-to-ground-station link in both
directions. For the *same* UAV, at the *same* position, with the *same* recorded path loss, the two
directions disagree by about 146 dB, and the direction with the **stronger** transmitter is the one
that fails.

Reproduction (scenario alias `base` via `ha_ctse_process.env_factory`, `seed=17`, an explicit
move-toward-users rule controller for 40 steps, config overrides `area_size=2000, n_agents=6,
n_users=24, n_clusters=3, cluster_std=120, uav_start_area_size=400, observation_radius=1200`):

```
ground_bs_tx_power = 30 dBm      uav tx_power = 23 dBm      min_sinr = 3 dB

base_path_loss   (dB)  [ 99.07 100.96 101.07 100.51 102.32  99.01]
uav_to_base_sinr (dB)  [ 17.90  16.01  15.89  16.45  14.64  17.96]
base_to_uav_sinr (dB)  [-128.60 -130.49 -130.60 -130.04 -131.85 -128.54]
```

Same path loss, transmitter 7 dB stronger, result 146 dB worse. That is not a propagation
asymmetry; it points at a unit or denominator error in the `base_to_uav_sinr` computation.

## Consequences that reach science, not just display

1. **`uav_bs_connections` is identically `False`.**
   `_update_uav_connections` (`forced_relay.py:2543-2557`) requires *both* directions to have
   `_get_link_capacity(...) > 0`, and `_get_link_capacity` returns `0` whenever
   `sinr_db < self.min_sinr` . Because the downlink is always ~-130 dB, the matrix never
   contains a `True` for any UAV, at any position, in any episode of this scenario.

   Verified directly:
   ```
   uav0: a2g=1.886e+07  g2a=0.000e+00  adjacency=False  in_routing=True
   uav1: a2g=1.857e+07  g2a=0.000e+00  adjacency=False  in_routing=True
   ...   (all six UAVs identical in kind)
   ```

2. **A policy observation feature is a dead constant.**
   `forced_relay.py:3090` builds an observation entry as
   `connection_status = 1.0 if self.uav_bs_connections[agent_idx, bs_idx] else 0.0`.
   Given (1), that feature is `0.0` for every agent on every step. Any run on this scenario has
   been training against a constant input in that slot.

3. **Two backhaul criteria in the same environment disagree by construction.**
   `_compute_routing_paths` → `_find_widest_path_to_ground_bs` (`forced_relay.py:3344`, `3606`)
   admits an edge on `_get_link_capacity(current, neighbour) > 0` — the *uplink* direction only —
   and never consults `uav_bs_connections`. So routes to the ground station exist (all six UAVs
   get one, bottleneck ~1.9e7) while the adjacency matrix says no UAV can reach the station.

4. **The `routing.py` hop-map routing variants cannot produce a path on this scenario.**
   `envs/pettingzoo/relay/routing.py:60-67` seeds its first BFS layer from
   `self.env.uav_bs_connections[uav_idx, bs_idx]`. With that matrix identically `False`,
   `_compute_hop_map` returns `inf` everywhere and `_reconstruct_all_hggr_paths` yields nothing.
   Only the in-env widest-path method produces routes here.

## What the visualization does about it

Nothing corrective. The scene capture in
`tools/research_support/capture/legacy_uav.py` reports **both** criteria, each labelled with what
admitted it, and counts the disagreement into every frame:

* link records carry `sinr_adjacency_and_widest_path_route`,
  `widest_path_route_only_not_in_sinr_adjacency`, or `sinr_adjacency_only_no_route_uses_it`;
* `interval_metrics.backhaul_route_edges_without_sinr_adjacency` and
  `backhaul_sinr_adjacency_edges_without_route` are per-frame counts.

Deriving "this UAV has backhaul" from either criterion alone would have produced a
self-consistent-looking picture that hides the disagreement, so neither is used alone.

## Suggested minimal investigation, for the owner to schedule

Not performed here.

1. Compare the noise/interference term used for `base_to_uav_sinr` against the one used for
   `uav_to_base_sinr` in the retained-radio backend (`envs/pettingzoo/uav_cpp_backend.py`,
   `compute_relay_radio_batch`) and in the Python fallback `_compute_link_sinr`. A ~146 dB offset
   with equal path loss is the size of a linear-versus-dB or a mW-versus-W mix-up.
2. Decide whether `uav_bs_connections` is meant to be bidirectional at all. If the scenario's
   intent is an uplink relay, requiring the downlink may be the bug rather than the SINR.
3. Whichever way it resolves, changing it changes observations on scenario `base`, so it is a
   protected-semantics change that needs its own review and its own record. Historical runs on this
   scenario were produced with the constant feature and should keep their recorded semantics.

## Evidence locations

| Claim | Source |
|---|---|
| Both-direction requirement | `envs/pettingzoo/relay/forced_relay.py:2543-2557` |
| SINR threshold gate returning 0 | `envs/pettingzoo/relay/forced_relay.py` `_get_link_capacity`, the `if sinr_db < self.min_sinr: return 0` branch |
| Constant observation feature | `envs/pettingzoo/relay/forced_relay.py:3090` |
| Widest-path route criterion | `envs/pettingzoo/relay/forced_relay.py:3344-3362`, `3606+` |
| Hop-map seeding from the dead matrix | `envs/pettingzoo/relay/routing.py:60-67` |
| Scenario alias -> this class | `ha_ctse_process/env_factory.py:28-31`, `126-128` (`base`/`4`/`s4` -> `UAVForcedRelayEnv`; `routed_core` is not reachable through this factory) |
