"""Single-event coupled relay host for coupled_host_replan_timing R1-lite.

``EventCoupledRelayHost`` subclasses D2's ``CoupledRelayHost`` (host.py, frozen) and changes one
thing: at one step ``t_e`` of the episode one of the five user clusters is re-drawn by the host's
own cluster law (``envs/pettingzoo/uav_env.py`` 541-555: centre uniform in ``[0, area]^2``, each
member ``centre + N(0, area/10)`` per axis, clipped to the arena).  Everything else (UAVs, the
other 40 users, BS, constants, reward, action clip) is the parent's.

Cluster membership.  The base env does not store it; it is exact by index
(``_generate_user_positions``): ``n_clusters = min(5, n_users // 10 + 1) = 5``, users
``10c .. 10c + 9`` belong to cluster ``c``.  D2's ``planner.cluster_layout`` implements that rule
and recovers the generator's own centres by replaying ``RandomState(seed_val)`` through the base
reset (``centre_source == "generator_replay"`` when the replay reproduces ``user_positions`` bit for
bit); it is reused here for the pre-event centres and the gate's ``far_cluster``.

Event draw (per world, independent of every other stream): ``rng =
numpy.random.default_rng([world_seed, 3])``; in this order ``t_e = rng.integers(150, 351)``,
``cluster = rng.integers(0, 5)``, ``centre = rng.uniform(0, area, 2)``, then for each member
``j`` of the cluster in index order ``clip(centre + rng.normal(0, area / 10, 2), 0, area)``.  The
whole event (including the ten new user positions) is drawn at ``reset()``; ``world_seed`` is the
host's ``seed_val`` after the reset (the reset seed, D2's ``_run_episode`` always passes it).  A
test-only ``event_override`` may replace ``t_e`` and/or ``cluster`` after the two draws, so the
centre and member draws are unchanged by an override.

Timing (exact).  ``current_step`` counts completed ``step()`` calls.  The event is applied inside
``step()`` of the call with ``current_step == t_e`` (the call whose returned reward is series
index ``t_e``), *before* that call's actions are applied and before the parent step runs:
``user_positions`` is replaced by a fresh array (not mutated in place: ``get_info`` hands out the
old array by reference) whose cluster rows are the new positions.  The parent step then moves the
UAVs and calls ``_begin_path_loss_step`` (uav_env.py 319, 677-688), which clears every
user-position-keyed path-loss cache, so no further invalidation is needed.  Consequences:

* series indices ``0 .. t_e - 1`` are pre-event and bitwise equal to the parent's; index ``t_e``
  is the first value computed with the new users (``first_affected_step = t_e``);
* the observation returned by call ``t_e - 1`` is pre-event; the host's own observation first
  shows the new users after call ``t_e`` (``host_observation_shows_event_after_step = t_e``);
* the full-information rules read the post-event users from ``event_info`` at their decision
  for step ``t_e`` (``first_reaction_step = t_e``, the information rule of R1-lite).
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import (
    HOST_CONTRACT_KWARGS,
    CoupledRelayHost,
    check_contract,
)
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    cluster_layout,
    user_association,
)

DIRECTION = "coupled_host_replan_timing"
EVENT_RNG_STREAM = 3
EVENT_STEP_LOW = 150
EVENT_STEP_HIGH_INCLUSIVE = 350
N_CLUSTERS = 5
EVENT_DRAW_ORDER = ("t_e = rng.integers(150, 351)", "cluster = rng.integers(0, 5)",
                    "centre = rng.uniform(0, area, 2)",
                    "per member j in index order: clip(centre + rng.normal(0, area/10, 2), 0, area)")


def draw_event(world_seed: int, area_size: float, n_users: int,
               override: dict[str, Any] | None = None) -> dict[str, Any]:
    """The world's event, drawn from ``default_rng([world_seed, 3])`` in the documented order."""
    n_clusters = min(5, int(n_users) // 10 + 1)
    if n_clusters != N_CLUSTERS:
        raise ValueError(f"the event law assumes {N_CLUSTERS} clusters, host has {n_clusters}")
    per = int(n_users) // n_clusters
    rng = np.random.default_rng([int(world_seed), EVENT_RNG_STREAM])
    t_e = int(rng.integers(EVENT_STEP_LOW, EVENT_STEP_HIGH_INCLUSIVE + 1))
    cluster = int(rng.integers(0, N_CLUSTERS))
    drawn = {"t_e": t_e, "cluster": cluster}
    if override:
        unknown = set(override) - {"t_e", "cluster"}
        if unknown:
            raise ValueError(f"unknown event override keys {sorted(unknown)}")
        t_e = int(override.get("t_e", t_e))
        cluster = int(override.get("cluster", cluster))
        if not 0 <= cluster < N_CLUSTERS or t_e < 0:
            raise ValueError("event override out of range")
    area = float(area_size)
    std = area / 10.0
    centre = rng.uniform(0.0, area, 2)
    start = cluster * per
    end = (cluster + 1) * per if cluster < n_clusters - 1 else int(n_users)
    members = np.arange(start, end)
    new_users = np.zeros((members.size, 2), dtype=float)
    for row in range(members.size):
        new_users[row] = np.clip(centre + rng.normal(0.0, std, 2), 0.0, area)
    return {"world_seed": int(world_seed), "t_e": t_e, "cluster": cluster,
            "drawn": drawn, "override": dict(override) if override else None,
            "members": members, "new_centre_xy": centre, "new_user_positions": new_users,
            "rng": f"numpy.random.default_rng([world_seed, {EVENT_RNG_STREAM}])",
            "draw_order": list(EVENT_DRAW_ORDER)}


class EventCoupledRelayHost(CoupledRelayHost):
    """``CoupledRelayHost`` with one cluster relocation applied inside ``step()`` at ``t_e``."""

    def __init__(self, *args: Any, event_override: dict[str, Any] | None = None,
                 **kwargs: Any) -> None:
        # The parent constructor calls reset(); the override must exist before it.
        self.event_override = dict(event_override) if event_override else None
        self.event: dict[str, Any] | None = None
        self.event_applied = False
        super().__init__(*args, **kwargs)

    def reset(self, seed: Any = None, options: Any = None):
        result = super().reset(seed=seed, options=options)
        world = getattr(self, "seed_val", None)
        if world is None:
            raise ValueError("the event host needs an integer world seed")
        self.event = draw_event(int(world), self.area_size, self.n_users, self.event_override)
        layout = cluster_layout(self)
        c = self.event["cluster"]
        members = self.event["members"]
        if not np.array_equal(np.flatnonzero(layout["membership"] == c), members):
            raise AssertionError("cluster membership by index disagrees with cluster_layout")
        bs_xy = np.asarray(self.ground_bs_positions[0, :2], dtype=float)
        users = np.asarray(self.user_positions, dtype=float)
        self.event.update({
            "old_centre_xy": np.asarray(layout["centres"][c], dtype=float).copy(),
            "old_centre_source": layout["centre_source"],
            "old_member_mean_xy": users[members].mean(axis=0),
            "old_user_positions": users[members].copy(),
            "old_centre_distance_to_bs_m": float(np.linalg.norm(layout["centres"][c] - bs_xy)),
            "new_centre_distance_to_bs_m": float(np.linalg.norm(self.event["new_centre_xy"] - bs_xy)),
            "gate_far_cluster": int(layout["far_cluster"]),
            "cluster_is_gate_far": bool(int(layout["far_cluster"]) == c),
            "first_affected_step": int(self.event["t_e"]),
            "host_observation_shows_event_after_step": int(self.event["t_e"]),
            "first_reaction_step": int(self.event["t_e"]),
        })
        post = np.array(users, dtype=float, copy=True)
        post[members] = self.event["new_user_positions"]
        self._post_event_users = post
        self.event_applied = False
        return result

    def post_event_user_positions(self) -> np.ndarray:
        """All users after the event (full information; the rules' view at decision t_e)."""
        return np.array(self._post_event_users, dtype=float, copy=True)

    def step(self, actions: Any):
        if not self.event_applied and int(self.current_step) == int(self.event["t_e"]):
            self.user_positions = self.post_event_user_positions()
            self.event_applied = True
            self.event["applied_in_step_call"] = int(self.current_step)
        return super().step(actions)

    @property
    def event_info(self) -> dict[str, Any]:
        """JSON-ready copy of the event record (arrays as lists)."""
        out: dict[str, Any] = {}
        for key, value in copy.deepcopy(self.event or {}).items():
            out[key] = value.tolist() if isinstance(value, np.ndarray) else value
        out["applied"] = bool(self.event_applied)
        return out


def make_event_host(world_seed: int, area_size: int = 5000,
                    event_override: dict[str, Any] | None = None) -> EventCoupledRelayHost:
    """The R1-lite host for one world: D2's contract kwargs, reset seed = world seed, contract checked."""
    if isinstance(world_seed, bool) or not isinstance(world_seed, (int, np.integer)):
        raise TypeError("world_seed must be an integer")
    env = EventCoupledRelayHost(area_size=area_size, seed=int(world_seed),
                                event_override=event_override, **HOST_CONTRACT_KWARGS)
    check_contract(env)
    return env


# ------------------------------------------------------------------------------ routing facts


def uav_cluster_plurality(env: CoupledRelayHost, membership: np.ndarray) -> np.ndarray:
    """Per UAV: the cluster holding most of its connected users (ties: lower cluster), -1 if none."""
    connections = np.asarray(env.connections, dtype=bool)
    out = np.full(env.n_uavs, -1, dtype=int)
    for i in range(env.n_uavs):
        users = np.flatnonzero(connections[i])
        if users.size:
            counts = np.bincount(membership[users], minlength=N_CLUSTERS)
            out[i] = int(np.argmax(counts))
    return out


def relay_nodes(path: list[Any]) -> list[int]:
    """Interior UAV nodes of a scenario-2 routing path ``[("uav", i), ..., ("ground_bs", b)]``."""
    return [int(node) for kind, node in path[1:-1] if kind == "uav"]


def cluster_routing_facts(env: CoupledRelayHost, cluster: int,
                          membership: np.ndarray) -> dict[str, Any]:
    """Actual association/routing of ``cluster``'s users in the env's *current* state.

    Rule (documented for warm SET's movable set):

    * servers = UAVs with >= 1 connected user of the cluster; a server is *movable* iff the
      cluster is the plurality cluster of its connected users (ties: lower cluster index);
      a server that mainly serves another cluster is shared and held;
    * relays = interior UAV nodes of the movable servers' routing paths; a relay is movable iff
      it has no connected user and lies on no routing path of a non-movable UAV that has >= 1
      connected user (a relay also used by another cluster is shared and held);
    * primary server = the movable server with most of the cluster's users (ties: lower index);
    * class: ``chain`` (primary server routed through >= 1 relay), ``direct`` (routed, no
      relay), ``unrouted`` (primary server has no backhaul path), ``shared_only`` (the cluster's
      users are connected only to servers of other clusters), ``unserved`` (no user connected).
      ``shared_only`` and ``unserved`` give an empty movable set; ``rules.warm_rule`` then runs
      its single-UAV fallback (each UAV in turn re-placed for the new cluster, adopted only if it
      beats the held layout's static reward; otherwise warm == KEEP, recorded with the reason).
    """
    connections = np.asarray(env.connections, dtype=bool)
    members = np.flatnonzero(np.asarray(membership) == int(cluster))
    association = user_association(env)
    plurality = uav_cluster_plurality(env, np.asarray(membership))
    paths = {int(k): list(v) for k, v in env.routing_paths.items()}
    per_server: dict[int, int] = {}
    for j in members:
        if association[j] >= 0:
            per_server[int(association[j])] = per_server.get(int(association[j]), 0) + 1
    servers = sorted(per_server)
    movable_servers = [i for i in servers if plurality[i] == int(cluster)]
    shared_servers = [i for i in servers if plurality[i] != int(cluster)]
    has_users = connections.any(axis=1)
    held_users_paths = set()
    for i, path in paths.items():
        if i not in movable_servers and has_users[i]:
            held_users_paths.update(relay_nodes(path))
    relays: list[int] = []
    for i in movable_servers:
        for node in relay_nodes(paths.get(i, [])):
            if node not in relays and node not in movable_servers:
                relays.append(node)
    movable_relays = sorted(r for r in relays if not has_users[r] and r not in held_users_paths)
    shared_relays = sorted(r for r in relays if r not in movable_relays)
    primary = (max(movable_servers, key=lambda i: (per_server[i], -i)) if movable_servers else None)
    if not servers:
        klass = "unserved"
    elif primary is None:
        klass = "shared_only"
    elif primary not in paths:
        klass = "unrouted"
    elif relay_nodes(paths[primary]):
        klass = "chain"
    else:
        klass = "direct"
    backhauled = {i for i in paths}
    chain_users = sum(per_server[i] for i in servers if i in paths and relay_nodes(paths[i]))
    direct_users = sum(per_server[i] for i in servers if i in paths and not relay_nodes(paths[i]))
    return {
        "class": klass,
        "chain_served": klass == "chain",
        "servers": servers,
        "users_per_server": {str(i): int(per_server[i]) for i in servers},
        "movable_servers": movable_servers,
        "shared_servers": shared_servers,
        "primary_server": primary,
        "primary_relays": relay_nodes(paths[primary]) if primary in paths else [],
        "movable_relays": movable_relays,
        "shared_relays": shared_relays,
        "movable_uavs": sorted(set(movable_servers) | set(movable_relays)),
        "users_connected": int(sum(per_server.values())),
        "users_backhauled": int(sum(per_server[i] for i in servers if i in backhauled)),
        "users_backhauled_via_relay": int(chain_users),
        "users_backhauled_direct": int(direct_users),
        "n_members": int(members.size),
    }
