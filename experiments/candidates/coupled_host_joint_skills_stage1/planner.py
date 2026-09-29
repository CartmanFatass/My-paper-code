"""Ordinary placement planner, closed-loop executor and floors (coupled_host_joint_skills_stage1 b01).

Same-information planner (ground-truth user and BS positions; the env's own connection,
routing and reward functions via ``host.static_evaluate``).  T2b design (DM decision after
the T2 plateau finding):

* Candidates (all evaluated statically, in this order, until the budget):
  1. plain k-means candidates (k in {4, 5, 6}; k-means++ seeding from ``rng``): service
     UAVs at the k centres, the remaining 6 - k UAVs at the midpoints of the BS -> centre
     lines of the farthest centres (the T2 rule, kept as a candidate family);
  2. range-aware served-subset candidates for the k = 5, 4, 6 centres.  Relay family
     (``allow_a2a=True``): a centre at horizontal distance d from the BS needs
     ``ceil(max(0, d - R_direct) / 1100)`` relays; the service UAV sits at the centre and the
     relays on the BS -> centre line (``relay_distances``); centres needing more relays than
     the router can chain (``max_routable_relays`` = max_hops) are excluded and recorded.
     Flat family (``allow_a2a=False``, DM amendment): every centre is served by one UAV
     parked at ``min(d, R_direct - 1 m)`` along the BS -> centre line (direct backhaul kept),
     no relays.  For every non-empty subset of servable centres whose total need (1 service
     + its relays, no relay sharing) is <= n_uavs a candidate is built; leftover UAVs go to
     the largest unserved cluster (relay: its centre; flat: its parked point), else above
     the BS.  All heights 100 m.
* Multi-start coordinate descent from the top-3 evaluated candidates (contract reward
  descending, ties by candidate index), the remaining budget split equally (remainder to the
  first starts; budget a converged start leaves is not passed on).  Per start: for each UAV
  in index order try +x, -x, +y, -y by the stage step (100 -> 50 -> 25 m; a stage ends
  after a full sweep without an accepted move, convergence after the 25 m sweep) and +z, -z
  by 50 m at every stage (heights clipped to the host range, 50-150 m) (T2c); accept a strict improvement of the contract reward
  (``stage="descent"``) or, when the reward is equal within ``IMPROVEMENT_TOL``, a strict
  decrease of the plateau potential (``stage="plateau"``).  The potential is the sum over
  unrouted UAVs of the 3-D distance to the nearest node they could route through: the BS,
  plus routed UAVs when A2A is enabled.  The best start's result is returned (ties: the
  earlier start).
* ``P_relay`` = ``allow_a2a=True``; ``P_flat`` = ``allow_a2a=False`` (UAV-UAV links disabled
  in the evaluator), same budget and descent; given equal rng states the k-means centres and
  plain candidates are equal.  The relay search's candidate list is plain + relay-family +
  flat-family subsets (the flat layouts evaluated with A2A on), the flat search's is plain +
  flat-family subsets: the flat set is contained in the relay set, so the static gate
  ``G = P_relay - P_flat`` cannot be negative through candidate coverage alone (descent from
  the top-3 starts can still differ).  Duplicate layouts are removed before ranking, so the
  three starts are distinct layouts.  T2c: ``extra_candidates`` (``run_gate.py`` passes the
  flat search's found layout, kind ``flat_result_incumbent``) are evaluated after the
  generated candidates inside the same budget and are eligible as starts, so ``G >= 0``
  holds by construction (A2A can only add routes; association does not depend on it).
  Incumbent rewards are snapshotted at cumulative evaluations 1,000 / 2,000 / 3,000.

* ``closed_loop_execute(env, targets, max_steps)``: reset to the world's initial positions
  (``reset(seed=env.world_seed)``), assign targets to UAVs (default: the permutation that
  minimises the largest straight-line distance, then the sum), fly straight at max_speed and
  hold on arrival.  The normalised action is clipped to the unit ball, so the executed 3-D
  speed never exceeds max_speed (the env itself does not clip actions, uav_env.py 283).

* ``retargeting_closed_loop_execute(env, targets, correction, period)``: the same executor
  (``straight_line_actions``) whose assigned targets a caller-supplied correction may move
  every ``period`` steps (T-G headroom gate, ``run_headroom_gate.py``); an identity correction
  reproduces ``closed_loop_execute`` bit for bit.

* ``stationary_floor(env)`` (zero actions) and ``random_floor(env, rng)`` (uniform
  normalised actions in [-1, 1]^3 each step).

All episode functions run in the host env with ``a2a_enabled=True`` by default (the host
contract the learners act in); pass ``allow_a2a`` to override.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import (
    CoupledRelayHost,
    static_evaluate,
)

SERVICE_HEIGHT_M = 100.0
K_CANDIDATES = (4, 5, 6)
K_SUBSET_ORDER = (5, 4, 6)
RELAY_SPACING_M = 1100.0
PARK_MARGIN_M = 1.0
N_STARTS = 3
XY_STEPS_M = (100.0, 50.0, 25.0)
Z_STEP_M = 50.0
SNAPSHOT_MARKS = (1000, 2000, 3000)
IMPROVEMENT_TOL = 1e-12
POTENTIAL_TOL = 1e-9
FINAL_WINDOW = 100
ARRIVAL_TOL_M = 1e-6


# ------------------------------------------------------------------------------ k-means


def kmeans(points: np.ndarray, k: int, rng: np.random.Generator, max_iter: int = 100):
    """Lloyd k-means with k-means++ seeding; deterministic given ``rng``.

    Returns (centres [k, d], labels [n]).  An empty cluster is re-seeded at the point
    farthest from its assigned centre.
    """
    points = np.asarray(points, dtype=float)
    n = points.shape[0]
    if not 1 <= k <= n:
        raise ValueError(f"k={k} must be in [1, {n}]")
    centres = np.empty((k, points.shape[1]), dtype=float)
    centres[0] = points[int(rng.integers(n))]
    closest = np.sum((points - centres[0]) ** 2, axis=1)
    for c in range(1, k):
        total = float(closest.sum())
        if total <= 0.0:
            index = int(rng.integers(n))
        else:
            index = int(rng.choice(n, p=closest / total))
        centres[c] = points[index]
        closest = np.minimum(closest, np.sum((points - centres[c]) ** 2, axis=1))

    labels = np.full(n, -1, dtype=int)
    for _ in range(max_iter):
        distances = np.sum((points[:, None, :] - centres[None, :, :]) ** 2, axis=2)
        new_labels = np.argmin(distances, axis=1)
        own = distances[np.arange(n), new_labels]
        for c in range(k):
            if not np.any(new_labels == c):
                far = int(np.argmax(own))
                new_labels[far] = c
                own[far] = -np.inf
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for c in range(k):
            centres[c] = points[labels == c].mean(axis=0)
    return centres, labels


# ------------------------------------------------------------------------------ geometry


def link_ranges(env: CoupledRelayHost) -> dict[str, float]:
    """Free-space link ranges at the 3 dB threshold, derived from the host's constants.

    ``r_link_uav_m``: 3-D range of a UAV-UAV link (tx_power); ``r_link_bs_m``: 3-D range of
    the UAV-BS link (ground_bs_tx_power); ``r_direct_horizontal_m``: horizontal distance at
    which a UAV at SERVICE_HEIGHT_M reaches the BS directly.
    """
    if env.channel_model != "free_space":
        raise ValueError("link_ranges assumes the free-space channel")
    constant_db = 20.0 * math.log10(4.0 * math.pi * env.carrier_frequency / 3e8)

    def reach(tx_dbm: float) -> float:
        return 10.0 ** ((tx_dbm - env.noise_power - env.min_sinr - constant_db) / 20.0)

    r_uav = reach(env.tx_power)
    r_bs = reach(env.ground_bs_tx_power)
    dz = SERVICE_HEIGHT_M - float(env.ground_bs_positions[0, 2])
    if r_bs <= abs(dz):
        raise ValueError("the BS is out of range at the service height")
    if RELAY_SPACING_M > r_uav:
        raise ValueError("relay spacing exceeds the UAV-UAV link range")
    return {
        "r_link_uav_m": r_uav,
        "r_link_bs_m": r_bs,
        "r_direct_horizontal_m": math.sqrt(r_bs ** 2 - dz ** 2),
        "relay_spacing_m": RELAY_SPACING_M,
    }


def relays_needed(distance_m: float, r_direct_m: float, spacing_m: float = RELAY_SPACING_M) -> int:
    """ceil(max(0, d - R_direct) / spacing)."""
    excess = float(distance_m) - float(r_direct_m)
    return 0 if excess <= 0.0 else int(math.ceil(excess / float(spacing_m)))


def relay_distances(distance_m: float, n_relays: int, spacing_m: float = RELAY_SPACING_M) -> list[float]:
    """Distances from the BS of the n relays on the BS -> centre line (service UAV at d).

    As even as the spacing allows: the first leg is ``a = max(d / (n + 1), d - n * spacing)``
    and the n remaining legs are equal, ``(d - a) / n`` (<= spacing).  With ``n`` from
    ``relays_needed`` the first leg is <= R_direct, so every link is inside range.
    """
    d = float(distance_m)
    n = int(n_relays)
    if n <= 0:
        return []
    first = max(d / (n + 1), d - n * float(spacing_m))
    leg = (d - first) / n
    return [first + m * leg for m in range(n)]


def _clip_positions(env: CoupledRelayHost, positions: np.ndarray) -> np.ndarray:
    clipped = np.array(positions, dtype=float)
    clipped[:, 0] = np.clip(clipped[:, 0], 0.0, env.area_size)
    clipped[:, 1] = np.clip(clipped[:, 1], 0.0, env.area_size)
    clipped[:, 2] = np.clip(clipped[:, 2], *env.height_range)
    return clipped


# ------------------------------------------------------------------------------ candidates


def kmeans_centres(env: CoupledRelayHost, rng: np.random.Generator) -> dict[int, dict[str, Any]]:
    """k-means on user xy for k in K_CANDIDATES (in that order, consuming ``rng``)."""
    users = np.asarray(env.user_positions, dtype=float)[:, :2]
    out = {}
    for k in K_CANDIDATES:
        if k > env.n_uavs:
            continue
        centres, labels = kmeans(users, k, rng)
        out[k] = {"centres": centres, "labels": labels,
                  "sizes": np.bincount(labels, minlength=k)}
    return out


def _plain_candidate(env: CoupledRelayHost, k: int, centres: np.ndarray) -> dict[str, Any]:
    bs_xy = np.asarray(env.ground_bs_positions[0, :2], dtype=float)
    order = np.argsort(-np.linalg.norm(centres - bs_xy, axis=1), kind="stable")
    positions = np.zeros((env.n_uavs, 3), dtype=float)
    positions[:k, :2] = centres
    for r in range(env.n_uavs - k):
        positions[k + r, :2] = 0.5 * (bs_xy + centres[order[r % k]])
    positions[:, 2] = SERVICE_HEIGHT_M
    return {
        "kind": "kmeans_plain",
        "k": int(k),
        "positions_xyz": _clip_positions(env, positions),
        "relay_targets": [int(order[r % k]) for r in range(env.n_uavs - k)],
    }


def max_routable_relays(env: CoupledRelayHost) -> int:
    """Relays the scenario-2 router can chain between a UAV and the BS.

    ``_bfs_shortest_path`` (scenario2.py 397-450) skips expanding a node whose UAV prefix has
    ``len(path) >= max_hops`` but still checks that node's own BS link first, so the longest
    routable chain is start -> r1 -> ... -> r_{max_hops} -> BS: ``max_hops`` relays.
    """
    return int(env.max_hops)


def _subset_candidates(env: CoupledRelayHost, k: int, clusters: dict[str, Any],
                       family: str, ranges: dict[str, float],
                       report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Served-centre subset candidates for one k-means solution, ``family`` in {"relay", "flat"}.

    Relay family: service UAV at the centre, ``relays_needed`` relays on the BS -> centre
    line; a centre needing more relays than ``max_routable_relays`` is excluded (recorded in
    ``report["excluded_centres"]``), never built and scored zero.  Flat family: every centre
    is servable by one UAV parked at ``min(d, R_direct - PARK_MARGIN_M)`` along the BS ->
    centre line (direct backhaul kept); no relays.  Leftover UAVs: relay family -> the
    largest unserved cluster's centre; flat family -> the largest unserved cluster's parked
    point; otherwise above the BS.  The family is a layout rule; the evaluation mode
    (``allow_a2a``) is chosen by the caller: the relay search evaluates both families with
    A2A on (DM T2b decision: the flat layouts are a subset of the relay search's candidates,
    so G >= 0 by construction), the flat search evaluates the flat family with A2A off.
    """
    if family not in ("relay", "flat"):
        raise ValueError(f"unknown candidate family {family!r}")
    allow_a2a = family == "relay"
    centres, sizes = clusters["centres"], clusters["sizes"]
    bs_xy = np.asarray(env.ground_bs_positions[0, :2], dtype=float)
    distance = np.linalg.norm(centres - bs_xy, axis=1)
    r_direct = ranges["r_direct_horizontal_m"]
    park = r_direct - PARK_MARGIN_M
    max_relays = max_routable_relays(env)
    report = {} if report is None else report
    report.setdefault("excluded_centres", [])
    report.setdefault("subsets_over_uav_budget", 0)
    report.setdefault("subsets_built", 0)

    def unit(c: int) -> np.ndarray:
        return (centres[c] - bs_xy) / distance[c] if distance[c] > 0 else np.zeros(2)

    def service_point(c: int) -> np.ndarray:
        if allow_a2a:
            return centres[c]
        return bs_xy + min(float(distance[c]), park) * unit(c)

    need: dict[int, int] = {}
    for c in range(k):
        if not allow_a2a:
            need[c] = 0
            continue
        n = relays_needed(distance[c], r_direct)
        if n > max_relays:
            report["excluded_centres"].append({
                "k": int(k), "centre": int(c), "distance_m": float(distance[c]),
                "relays_needed": int(n), "max_routable_relays": max_relays,
                "reason": "chain longer than the router's max_hops"})
            continue
        need[c] = n
    servable = sorted(need)
    out = []
    for size in range(1, len(servable) + 1):
        for subset in itertools.combinations(servable, size):
            total = sum(1 + need[c] for c in subset)
            if total > env.n_uavs:
                report["subsets_over_uav_budget"] += 1
                continue
            rows: list[list[float]] = []
            roles: list[str] = []
            for c in subset:
                point = service_point(c)
                rows.append([point[0], point[1], SERVICE_HEIGHT_M])
                roles.append(f"service:{c}")
                assert need[c] <= max_relays
                for m, along in enumerate(relay_distances(distance[c], need[c])):
                    xy = bs_xy + along * unit(c)
                    rows.append([xy[0], xy[1], SERVICE_HEIGHT_M])
                    roles.append(f"relay:{c}:{m}")
            leftover = env.n_uavs - total
            pool = [c for c in range(k) if c not in subset]
            if pool:
                target = max(pool, key=lambda c: (int(sizes[c]), -c))
                spot, role = service_point(target), f"extra_service:{target}"
            else:
                target, spot, role = None, bs_xy, "above_bs"
            for _ in range(leftover):
                rows.append([spot[0], spot[1], SERVICE_HEIGHT_M])
                roles.append(role)
            report["subsets_built"] += 1
            out.append({
                "kind": f"subset_{family}",
                "k": int(k),
                "served": [int(c) for c in subset],
                "relays": {int(c): int(need[c]) for c in subset},
                "leftover_target": None if target is None else int(target),
                "roles": roles,
                "positions_xyz": _clip_positions(env, np.asarray(rows, dtype=float)),
            })
    return out


def _dedupe(candidates: list[dict[str, Any]], report: dict[str, Any]) -> list[dict[str, Any]]:
    """Drop candidates whose clipped positions repeat an earlier candidate (first kept)."""
    seen: set[bytes] = set()
    kept = []
    for candidate in candidates:
        key = np.round(np.asarray(candidate["positions_xyz"], dtype=float), 6).tobytes()
        if key in seen:
            report["duplicates_removed"] = report.get("duplicates_removed", 0) + 1
            continue
        seen.add(key)
        kept.append(candidate)
    report.setdefault("duplicates_removed", 0)
    return kept


def build_candidates(env: CoupledRelayHost, rng: np.random.Generator,
                     allow_a2a: bool = True,
                     report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Plain k-means candidates, then range-aware served-subset candidates (k = 5, 4, 6).

    ``allow_a2a=True`` (relay search): plain + relay-family subsets + flat-family subsets, so
    the flat search's candidate set is contained in the relay search's.  ``allow_a2a=False``
    (flat search): plain + flat-family subsets.  Duplicate layouts are removed (first kept).
    ``report`` (optional dict) receives the candidate summary: counts per family, excluded
    centres with reasons, subsets over the UAV budget, duplicates removed.
    """
    report = {} if report is None else report
    ranges = link_ranges(env)
    clusters = kmeans_centres(env, rng)
    candidates = [_plain_candidate(env, k, clusters[k]["centres"]) for k in clusters]
    families = ("relay", "flat") if allow_a2a else ("flat",)
    for family in families:
        for k in K_SUBSET_ORDER:
            if k in clusters:
                candidates.extend(_subset_candidates(env, k, clusters[k], family, ranges, report))
    candidates = _dedupe(candidates, report)
    for index, candidate in enumerate(candidates):
        candidate["index"] = index
    report["plain"] = sum(c["kind"] == "kmeans_plain" for c in candidates)
    report["subset_relay"] = sum(c["kind"] == "subset_relay" for c in candidates)
    report["subset_flat"] = sum(c["kind"] == "subset_flat" for c in candidates)
    report["subset"] = report["subset_relay"] + report["subset_flat"]
    report["total"] = len(candidates)
    report["excluded_centre_count"] = len(report.get("excluded_centres", []))
    return candidates


# ------------------------------------------------------------------------------ search


def plateau_potential(env: CoupledRelayHost, allow_a2a: bool) -> float:
    """Sum over unrouted UAVs of the 3-D distance to the nearest node they could route via."""
    routed = set(int(i) for i in env.routing_paths)
    nodes = [np.asarray(env.ground_bs_positions[b], dtype=float) for b in range(env.n_ground_bs)]
    if allow_a2a:
        nodes.extend(np.asarray(env.uav_positions[i], dtype=float) for i in sorted(routed))
    nodes_array = np.stack(nodes)
    total = 0.0
    for i in range(env.n_uavs):
        if i in routed:
            continue
        total += float(np.min(np.linalg.norm(nodes_array - env.uav_positions[i], axis=1)))
    return total


@dataclass
class PlacementResult:
    positions_xyz: np.ndarray
    contract_reward: float
    coverage_backhauled: float
    evaluations: int
    history: list[dict[str, Any]]
    allow_a2a: bool
    budget: int
    converged: bool
    best_start: dict[str, Any]
    starts: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    candidates_evaluated: int = 0
    ranges: dict[str, float] = field(default_factory=dict)
    candidate_report: dict[str, Any] = field(default_factory=dict)
    incumbent_at: dict[str, Any] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    max_uav_connections_seen: int = 0
    xy_steps_m: tuple[float, ...] = XY_STEPS_M

    def to_json(self) -> dict[str, Any]:
        start_indices = {s["candidate_index"] for s in self.starts}
        return {
            "positions_xyz": self.positions_xyz.tolist(),
            "contract_reward": self.contract_reward,
            "coverage_backhauled": self.coverage_backhauled,
            "evaluations": self.evaluations,
            "budget": self.budget,
            "allow_a2a": self.allow_a2a,
            "converged": self.converged,
            "best_start": self.best_start,
            "starts": self.starts,
            "candidates_total": len(self.candidates),
            "candidates_evaluated": self.candidates_evaluated,
            "candidate_report": self.candidate_report,
            "incumbent_at": self.incumbent_at,
            "candidates": [
                {key: c.get(key) for key in ("index", "kind", "k", "served", "relays",
                                             "leftover_target", "roles", "contract_reward",
                                             "coverage_backhauled", "duplicate_of")}
                | {"positions_xyz": np.asarray(c["positions_xyz"]).tolist(),
                   "descent_start": c["index"] in start_indices}
                for c in self.candidates[: self.candidates_evaluated]
            ],
            "ranges": self.ranges,
            "history": self.history,
            "info": self.info,
            "max_uav_connections_seen": self.max_uav_connections_seen,
        } | ({} if tuple(self.xy_steps_m) == tuple(XY_STEPS_M)
             else {"xy_steps_m": [float(v) for v in self.xy_steps_m]})


def search_placement(
    env: CoupledRelayHost,
    allow_a2a: bool,
    budget: int = 3000,
    rng: np.random.Generator | None = None,
    n_starts: int = N_STARTS,
    extra_candidates: list[Any] | None = None,
    extra_kind: str = "flat_result_incumbent",
    xy_steps_m: tuple[float, ...] | None = None,
) -> PlacementResult:
    """Static placement search; never uses more than ``budget`` static evaluations.

    ``xy_steps_m`` (default ``XY_STEPS_M``) is the descent's xy step schedule; a schedule that
    extends the default as a prefix (e.g. ``(100, 50, 25, 10)``) reproduces the default
    trajectory of every start up to the default's convergence and then continues it.

    Candidates are evaluated in order until the budget (all of them at the declared budget);
    the rest of the budget goes to the multi-start descent.  The env is left at the last
    evaluated trial (not necessarily the best placement) and with ``a2a_enabled =
    allow_a2a``; callers that step the env must reset it.
    """
    if rng is None:
        raise ValueError("search_placement needs an explicit rng")
    budget = int(budget)
    if budget < 1:
        raise ValueError("budget must be >= 1")
    xy_steps = XY_STEPS_M if xy_steps_m is None else tuple(float(v) for v in xy_steps_m)
    if not xy_steps or any(not v > 0.0 for v in xy_steps):
        raise ValueError("xy_steps_m must be a non-empty sequence of positive steps")
    candidate_report: dict[str, Any] = {}
    candidates = build_candidates(env, rng, allow_a2a, report=candidate_report)
    extras = []
    for position in extra_candidates or []:
        extra_positions = np.array(position, dtype=float).reshape(env.n_uavs, 3)
        if not np.array_equal(_clip_positions(env, extra_positions), extra_positions):
            raise ValueError("extra candidate outside the arena or height range")
        key = np.round(extra_positions, 6).tobytes()
        duplicate = next((c["index"] for c in candidates
                          if np.round(np.asarray(c["positions_xyz"], dtype=float), 6).tobytes()
                          == key), None)
        extras.append({"kind": extra_kind, "k": None, "positions_xyz": extra_positions,
                       "duplicate_of": duplicate})
    if extras and budget < len(extras):
        raise ValueError("budget smaller than the extra candidates")
    # Extras are always evaluated: the generated list is truncated first if the budget is short.
    generated_room = min(len(candidates), budget - len(extras))
    candidates = candidates[:generated_room] + extras + candidates[generated_room:]
    for index, candidate in enumerate(candidates):
        candidate["index"] = index
    candidate_report["extra_candidates"] = len(extras)

    evaluations = 0
    max_links = 0
    history: list[dict[str, Any]] = []

    def evaluate(positions: np.ndarray) -> tuple[dict[str, Any], float]:
        nonlocal evaluations, max_links
        info = static_evaluate(env, positions, allow_a2a=allow_a2a)
        evaluations += 1
        max_links = max(max_links, int(info["uav_connection_count"]))
        return info, plateau_potential(env, allow_a2a)

    # Snapshots at cumulative evaluation marks (taken after the mark-th evaluation is processed).
    marks = [m for m in SNAPSHOT_MARKS]
    overall_at: dict[str, float | None] = {}
    tracker: dict[str, Any] = {"overall": -np.inf, "start": None, "start_reward": None}
    start_at: list[dict[str, float | None]] = []

    def snapshot() -> None:
        if evaluations in marks:
            key = str(evaluations)
            overall_at[key] = float(tracker["overall"])
            if tracker["start"] is not None:
                start_at[tracker["start"]][key] = float(tracker["start_reward"])

    evaluated = candidates[: min(len(candidates), budget)]
    for candidate in evaluated:
        info, potential = evaluate(candidate["positions_xyz"])
        candidate["contract_reward"] = float(info["contract_reward"])
        candidate["coverage_backhauled"] = float(info["coverage_backhauled"])
        candidate["_info"] = info
        candidate["potential"] = potential
        tracker["overall"] = max(tracker["overall"], candidate["contract_reward"])
        snapshot()
    ranked = sorted(range(len(evaluated)),
                    key=lambda i: (-evaluated[i]["contract_reward"], i))[: max(1, int(n_starts))]
    history.append({"evaluations": evaluations, "stage": "candidates",
                    "contract_reward": evaluated[ranked[0]]["contract_reward"],
                    "candidate_index": ranked[0]})

    remaining = budget - evaluations
    shares = [remaining // len(ranked) + (1 if s < remaining % len(ranked) else 0)
              for s in range(len(ranked))]
    starts: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for s, index in enumerate(ranked):
        candidate = evaluated[index]
        position = np.array(candidate["positions_xyz"], dtype=float)
        current_info = candidate["_info"]
        reward = float(current_info["contract_reward"])
        potential = float(candidate["potential"])
        limit = evaluations + shares[s]
        start_at.append({})
        tracker["start"], tracker["start_reward"] = s, reward
        start_began = evaluations
        history.append({"evaluations": evaluations, "stage": "start", "start": s,
                        "candidate_index": index, "contract_reward": reward,
                        "potential": potential})
        stage_index = 0
        converged = False
        accepted = {"descent": 0, "plateau": 0}
        used_before = evaluations
        while evaluations < limit:
            moved = False
            step = xy_steps[stage_index]
            moves = ((step, 0.0, 0.0), (-step, 0.0, 0.0), (0.0, step, 0.0), (0.0, -step, 0.0),
                     (0.0, 0.0, Z_STEP_M), (0.0, 0.0, -Z_STEP_M))
            for uav in range(env.n_uavs):
                for move in moves:
                    if evaluations >= limit:
                        break
                    trial = position.copy()
                    trial[uav] += move
                    trial = _clip_positions(env, trial)
                    if np.array_equal(trial, position):
                        continue
                    info, trial_potential = evaluate(trial)
                    trial_reward = float(info["contract_reward"])
                    stage = None
                    if trial_reward > reward + IMPROVEMENT_TOL:
                        stage = "descent"
                    elif (abs(trial_reward - reward) <= IMPROVEMENT_TOL
                          and trial_potential < potential - POTENTIAL_TOL):
                        stage = "plateau"
                    if stage is not None:
                        position, current_info = trial, info
                        reward, potential = trial_reward, trial_potential
                        moved = True
                        accepted[stage] += 1
                        tracker["start_reward"] = reward
                        tracker["overall"] = max(tracker["overall"], reward)
                        history.append({"evaluations": evaluations, "stage": stage, "start": s,
                                        "contract_reward": reward, "potential": potential,
                                        "uav": uav, "step_m": step,
                                        "move": [float(v) for v in move]})
                    snapshot()
                if evaluations >= limit:
                    break
            if evaluations >= limit:
                break
            if not moved:
                if stage_index + 1 < len(xy_steps):
                    stage_index += 1
                else:
                    converged = True
                    break
        record = {"start": s, "candidate_index": index, "kind": candidate["kind"],
                  "k": candidate["k"], "start_reward": float(candidate["contract_reward"]),
                  "final_reward": reward, "share": shares[s],
                  "evaluations": evaluations - used_before, "converged": converged,
                  "accepted_descent": accepted["descent"],
                  "accepted_plateau": accepted["plateau"],
                  "final_xy_step_m": xy_steps[stage_index],
                  "began_at_evaluation": start_began, "ended_at_evaluation": evaluations,
                  "incumbent_at": start_at[s]}
        starts.append(record)
        if best is None or reward > best["reward"] + IMPROVEMENT_TOL:
            best = {"reward": reward, "position": position, "info": current_info,
                    "record": record}

    for candidate in candidates:
        candidate.pop("_info", None)
    assert best is not None
    # Marks the search never reached take the final value; a start that had not begun at a
    # mark records None, one that had ended records its final reward.
    final_overall = max(tracker["overall"], float(best["reward"]))
    for m in marks:
        key = str(m)
        overall_at.setdefault(key, final_overall)
        for record in starts:
            if key in record["incumbent_at"]:
                continue
            record["incumbent_at"][key] = (
                None if record["began_at_evaluation"] >= m and m <= evaluations
                else record["final_reward"])
    for record in starts:
        record["incumbent_at"] = {str(m): record["incumbent_at"][str(m)] for m in marks}
    return PlacementResult(
        positions_xyz=best["position"],
        contract_reward=float(best["reward"]),
        coverage_backhauled=float(best["info"]["coverage_backhauled"]),
        evaluations=evaluations,
        history=history,
        allow_a2a=bool(allow_a2a),
        budget=budget,
        converged=all(s["converged"] for s in starts),
        best_start=best["record"],
        starts=starts,
        candidates=candidates,
        candidates_evaluated=len(evaluated),
        ranges=link_ranges(env),
        candidate_report=candidate_report,
        incumbent_at={str(m): overall_at[str(m)] for m in marks},
        info=dict(best["info"]),
        max_uav_connections_seen=max_links,
        xy_steps_m=tuple(xy_steps),
    )


# ------------------------------------------------------------------------------ episodes


def cluster_layout(env: CoupledRelayHost) -> dict[str, Any]:
    """Users' generating clusters (uav_env.py 516-532) and their centres.

    Membership is exact by index: ``n_clusters = min(5, n_users // 10 + 1)``, user ``j`` in
    cluster ``min(j // users_per_cluster, n_clusters - 1)``.  Centres are the generator's own
    centres when replaying ``RandomState(env.seed_val)`` through the base reset reproduces
    ``env.user_positions`` bit for bit (``centre_source = "generator_replay"``); otherwise the
    members' mean (``"member_mean"``).
    """
    if env.user_distribution != "cluster":
        raise ValueError("cluster_layout needs user_distribution == 'cluster'")
    n_users = int(env.n_users)
    n_clusters = min(5, n_users // 10 + 1)
    per = n_users // n_clusters
    membership = np.minimum(np.arange(n_users) // per, n_clusters - 1)

    centres = None
    source = "member_mean"
    seed = getattr(env, "seed_val", None)
    if seed is not None:
        replay = np.random.RandomState(seed)
        for _ in range(env.n_uavs):
            replay.uniform(0, env.area_size)
            replay.uniform(0, env.area_size)
            replay.uniform(*env.height_range)
        generated = replay.uniform(0, env.area_size, (n_clusters, 2))
        std = env.area_size / 10
        users = np.zeros((n_users, 2))
        for c in range(n_clusters):
            start = c * per
            end = (c + 1) * per if c < n_clusters - 1 else n_users
            for j in range(start, end):
                users[j] = np.clip(generated[c] + replay.normal(0, std, 2), 0, env.area_size)
        if np.array_equal(users, np.asarray(env.user_positions)):
            centres, source = generated, "generator_replay"
    if centres is None:
        users_xy = np.asarray(env.user_positions, dtype=float)[:, :2]
        centres = np.stack([users_xy[membership == c].mean(axis=0) for c in range(n_clusters)])
    bs_xy = np.asarray(env.ground_bs_positions[0, :2], dtype=float)
    distance = np.linalg.norm(centres - bs_xy, axis=1)
    return {
        "membership": membership,
        "centres": centres,
        "centre_source": source,
        "centre_distance_to_bs_m": distance,
        "far_cluster": int(np.argmax(distance)),
    }


def backhauled_users_mask(env: CoupledRelayHost) -> np.ndarray:
    routed = np.zeros(env.n_uavs, dtype=bool)
    for i in env.routing_paths:
        routed[int(i)] = True
    return np.any(np.asarray(env.connections, dtype=bool) & routed[:, None], axis=0)


def user_association(env: CoupledRelayHost) -> np.ndarray:
    """Serving UAV index per user (-1 if unconnected); the base assignment is one-to-one."""
    connections = np.asarray(env.connections, dtype=bool)
    served = connections.any(axis=0)
    return np.where(served, np.argmax(connections, axis=0), -1)


def far_cluster_backhauled_share(env: CoupledRelayHost, layout: dict[str, Any] | None = None) -> float:
    layout = cluster_layout(env) if layout is None else layout
    members = layout["membership"] == layout["far_cluster"]
    return float(np.mean(backhauled_users_mask(env)[members]))


def assign_targets(initial_xyz: np.ndarray, targets_xyz: np.ndarray) -> np.ndarray:
    """perm with UAV i -> targets[perm[i]], minimising the largest distance, then the sum."""
    initial_xyz = np.asarray(initial_xyz, dtype=float)
    targets_xyz = np.asarray(targets_xyz, dtype=float)
    n = initial_xyz.shape[0]
    distance = np.linalg.norm(initial_xyz[:, None, :] - targets_xyz[None, :, :], axis=2)
    best_key, best_perm = None, None
    for perm in itertools.permutations(range(n)):
        values = distance[np.arange(n), perm]
        key = (float(values.max()), float(values.sum()))
        if best_key is None or key < best_key:
            best_key, best_perm = key, perm
    return np.asarray(best_perm, dtype=int)


def _summarise(series: dict[str, list[float]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, values in series.items():
        array = np.asarray(values, dtype=float)
        tail = array[-FINAL_WINDOW:]
        out[f"{name}_mean_all"] = float(array.mean()) if array.size else None
        out[f"{name}_mean_final100"] = float(tail.mean()) if tail.size else None
    return out


def _run_episode(
    env: CoupledRelayHost,
    action_fn: Callable[[CoupledRelayHost, int], np.ndarray],
    max_steps: int | None,
    allow_a2a: bool,
) -> dict[str, Any]:
    if env.world_seed is None:
        raise ValueError("the host has no world seed; construct it with make_host")
    env.a2a_enabled = bool(allow_a2a)
    env.reset(seed=int(env.world_seed))
    initial = env.uav_positions.copy()
    layout = cluster_layout(env)
    horizon = int(env.max_steps if max_steps is None else max_steps)

    series: dict[str, list[float]] = {"contract_reward": [], "coverage_backhauled": [],
                                      "frontend_capacity_with_path_mbps": [],
                                      "mean_relays_per_routed_uav": []}
    # Association (serving UAV per user, -1 if none) and backhauled mask; the reset state is
    # the t = 0 baseline.
    association = user_association(env)
    backhauled = backhauled_users_mask(env)
    association_changes: list[int] = []
    backhaul_losses: list[int] = []
    for t in range(horizon):
        actions_array = np.asarray(action_fn(env, t), dtype=float).reshape(env.n_uavs, 3)
        actions = {agent: actions_array[i] for i, agent in enumerate(env.agents)}
        _obs, rewards, terminations, _truncations, _infos = env.step(actions)
        info = env.reward_info
        team = sum(float(rewards[agent]) for agent in env.agents)
        if not np.isclose(team, info["contract_reward"], rtol=0, atol=1e-9):
            raise AssertionError(
                f"step {t}: returned team reward {team} != reward_info {info['contract_reward']}")
        for name in series:
            series[name].append(float(info[name]))
        new_association = user_association(env)
        new_backhauled = backhauled_users_mask(env)
        association_changes.append(int(np.sum(new_association != association)))
        backhaul_losses.append(int(np.sum(backhauled & ~new_backhauled)))
        association, backhauled = new_association, new_backhauled
        if all(terminations.values()):
            break

    final = dict(env.reward_info)
    result = {
        "steps": len(series["contract_reward"]),
        "allow_a2a": bool(allow_a2a),
        "initial_positions_xyz": initial.tolist(),
        "final_positions_xyz": env.uav_positions.tolist(),
        "series": series,
        "association_change_count": int(sum(association_changes)),
        "backhaul_loss_events": int(sum(backhaul_losses)),
        "association_changes_per_step": association_changes,
        "backhaul_losses_per_step": backhaul_losses,
        "final": {
            "contract_reward": final["contract_reward"],
            "coverage_backhauled": final["coverage_backhauled"],
            "frontend_capacity_with_path_mbps": final["frontend_capacity_with_path_mbps"],
            "mean_relays_per_routed_uav": final["mean_relays_per_routed_uav"],
            "avg_hops": final["avg_hops"],
            "routed_uavs": final["routed_uavs"],
            "far_cluster_backhauled_share": far_cluster_backhauled_share(env, layout),
        },
        "far_cluster": {"index": layout["far_cluster"], "centre_source": layout["centre_source"],
                        "centre_distance_to_bs_m": float(
                            layout["centre_distance_to_bs_m"][layout["far_cluster"]])},
    }
    result.update(_summarise(series))
    return result


def straight_line_actions(positions_xyz: np.ndarray, assigned_xyz: np.ndarray,
                          stride: float) -> tuple[np.ndarray, np.ndarray]:
    """The closed-loop action rule: fly straight at max_speed, land exactly, hold on arrival.

    Returns (normalised actions [n, 3], distance to the assigned target [n]).  A UAV within
    ``stride`` (= max_speed * time_step) of its target moves exactly onto it; the actions are
    clipped to the unit ball, so the executed 3-D speed never exceeds max_speed (the env does
    not clip actions, uav_env.py 283).
    """
    delta = assigned_xyz - positions_xyz
    distance = np.linalg.norm(delta, axis=1)
    n = delta.shape[0]
    actions = np.zeros((n, 3), dtype=float)
    for i in range(n):
        if distance[i] <= ARRIVAL_TOL_M:
            continue
        if distance[i] <= stride:
            actions[i] = delta[i] / stride
        else:
            actions[i] = delta[i] / distance[i]
    norms = np.linalg.norm(actions, axis=1)
    over = norms > 1.0
    actions[over] /= norms[over][:, None]
    return actions, distance


def closed_loop_execute(
    env: CoupledRelayHost,
    target_positions_xyz: Any,
    max_steps: int | None = None,
    allow_a2a: bool = True,
    assignment: str = "min_makespan",
) -> dict[str, Any]:
    """Straight-line flight at max_speed from the world's initial positions to the targets."""
    targets = np.array(target_positions_xyz, dtype=float).reshape(env.n_uavs, 3)
    if assignment not in ("min_makespan", "identity"):
        raise ValueError(f"unknown assignment {assignment!r}")
    stride = float(env.max_speed) * float(env.time_step)
    state: dict[str, Any] = {}

    def action_fn(host: CoupledRelayHost, t: int) -> np.ndarray:
        if t == 0:
            perm = (assign_targets(host.uav_positions, targets) if assignment == "min_makespan"
                    else np.arange(host.n_uavs))
            state["perm"] = perm
            state["assigned"] = targets[perm]
            state["arrival_step"] = None
        actions, distance = straight_line_actions(host.uav_positions, state["assigned"], stride)
        if state["arrival_step"] is None and np.all(distance <= ARRIVAL_TOL_M):
            state["arrival_step"] = t
        return actions

    result = _run_episode(env, action_fn, max_steps, allow_a2a)
    final_gap = np.linalg.norm(np.asarray(result["final_positions_xyz"]) - state["assigned"], axis=1)
    arrival = state["arrival_step"]
    if arrival is None and np.all(final_gap <= ARRIVAL_TOL_M):
        arrival = result["steps"]
    distance0 = np.linalg.norm(np.asarray(result["initial_positions_xyz"]) - state["assigned"], axis=1)
    result.update({
        "reference": "closed_loop",
        "assignment": assignment,
        "target_permutation": state["perm"].tolist(),
        "targets_xyz": targets.tolist(),
        "max_travel_distance_m": float(distance0.max()),
        "arrival_step": arrival,
        "final_max_distance_to_target_m": float(final_gap.max()),
    })
    return result


def retargeting_closed_loop_execute(
    env: CoupledRelayHost,
    target_positions_xyz: Any,
    correction: Callable[[int, np.ndarray], np.ndarray],
    period: int,
    max_steps: int | None = None,
    allow_a2a: bool = True,
    assignment: str = "min_makespan",
) -> dict[str, Any]:
    """``closed_loop_execute`` whose assigned targets a ``correction`` may move during flight.

    Same reset, target-to-UAV assignment (fixed at t = 0) and action rule
    (``straight_line_actions``).  At every step ``t`` with ``t % period == 0`` (t = 0 included,
    before that step's action) ``correction(t, assigned)`` receives a copy of the current
    assigned targets (row i = UAV i's target) and returns the new ones; it must not touch
    ``env``.  With a correction that returns its input unchanged the episode equals
    ``closed_loop_execute`` bit for bit.  ``arrival_step`` is the first step at which every UAV
    sat on its then-current target.
    """
    targets = np.array(target_positions_xyz, dtype=float).reshape(env.n_uavs, 3)
    if assignment not in ("min_makespan", "identity"):
        raise ValueError(f"unknown assignment {assignment!r}")
    period = int(period)
    if period < 1:
        raise ValueError("period must be >= 1")
    stride = float(env.max_speed) * float(env.time_step)
    state: dict[str, Any] = {"decisions": []}

    def action_fn(host: CoupledRelayHost, t: int) -> np.ndarray:
        if t == 0:
            perm = (assign_targets(host.uav_positions, targets) if assignment == "min_makespan"
                    else np.arange(host.n_uavs))
            state["perm"] = perm
            state["assigned"] = targets[perm]
            state["arrival_step"] = None
        if t % period == 0:
            before = state["assigned"].copy()
            after = np.array(correction(t, before.copy()), dtype=float).reshape(host.n_uavs, 3)
            if not np.all(np.isfinite(after)):
                raise ValueError(f"step {t}: correction returned non-finite targets")
            state["assigned"] = after
            state["decisions"].append({"t": int(t), "moved_uavs": int(np.sum(np.any(after != before, axis=1)))})
        actions, distance = straight_line_actions(host.uav_positions, state["assigned"], stride)
        if state["arrival_step"] is None and np.all(distance <= ARRIVAL_TOL_M):
            state["arrival_step"] = t
        return actions

    result = _run_episode(env, action_fn, max_steps, allow_a2a)
    final_gap = np.linalg.norm(np.asarray(result["final_positions_xyz"]) - state["assigned"], axis=1)
    anchor = targets[state["perm"]]
    drift = np.linalg.norm(state["assigned"] - anchor, axis=1)
    result.update({
        "reference": "closed_loop_retargeted",
        "assignment": assignment,
        "target_permutation": state["perm"].tolist(),
        "targets_xyz": targets.tolist(),
        "final_assigned_xyz": state["assigned"].tolist(),
        "final_target_drift_from_anchor_m": drift.tolist(),
        "correction_period": period,
        "decisions": state["decisions"],
        "arrival_step": state["arrival_step"],
        "final_max_distance_to_target_m": float(final_gap.max()),
    })
    return result


def stationary_floor(env: CoupledRelayHost, max_steps: int | None = None,
                     allow_a2a: bool = True) -> dict[str, Any]:
    result = _run_episode(env, lambda host, t: np.zeros((host.n_uavs, 3)), max_steps, allow_a2a)
    result["reference"] = "stationary_floor"
    return result


def random_floor(env: CoupledRelayHost, rng: np.random.Generator, max_steps: int | None = None,
                 allow_a2a: bool = True) -> dict[str, Any]:
    result = _run_episode(env, lambda host, t: rng.uniform(-1.0, 1.0, (host.n_uavs, 3)),
                          max_steps, allow_a2a)
    result["reference"] = "random_floor"
    return result
