"""Ordinary placement planner, closed-loop executor and floors (coupled_host_joint_skills_stage1 b01).

Same-information planner (ground-truth user and BS positions; the env's own connection,
routing and reward functions via ``host.static_evaluate``):

* ``search_placement(env, allow_a2a, budget, rng)``: initial candidates from k-means service
  centroids (k in {4, 5, 6}, own numpy k-means with k-means++ seeding from ``rng``); for
  k < 6 the remaining UAVs are relays at the midpoints of the BS -> centroid lines of the
  farthest centroids (one relay per line, farthest first); height 100 m.  Then coordinate
  descent from the best candidate: for each UAV in index order try +x, -x, +y, -y by the
  step (100 m, shrinking once to 50 m after a full sweep without improvement), accept strict
  improvements of the contract reward (first improvement), stop at the evaluation budget or
  after a 50 m sweep without improvement (``converged``).  Candidate evaluations count
  toward the budget; a move clipped to no displacement is skipped without an evaluation.
  ``P_relay`` = ``allow_a2a=True``; ``P_flat`` = ``allow_a2a=False`` (UAV-UAV links disabled
  in the evaluator), same budget and, given equal rng states, the same candidates.

* ``closed_loop_execute(env, targets, max_steps)``: reset to the world's initial positions
  (``reset(seed=env.world_seed)``), assign targets to UAVs (default: the permutation that
  minimises the largest straight-line distance, then the sum), fly straight at max_speed
  (normalised velocity action = unit direction; the final partial stride lands exactly) and
  hold on arrival.

* ``stationary_floor(env)`` (zero actions) and ``random_floor(env, rng)`` (uniform
  normalised actions in [-1, 1]^3 each step).

All episode functions run in the host env with ``a2a_enabled=True`` by default (the host
contract the learners act in); pass ``allow_a2a`` to override.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import (
    CoupledRelayHost,
    static_evaluate,
)

SERVICE_HEIGHT_M = 100.0
K_CANDIDATES = (4, 5, 6)
INITIAL_STEP_M = 100.0
FINAL_STEP_M = 50.0
IMPROVEMENT_TOL = 1e-12
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


# ------------------------------------------------------------------------------ candidates


def _clip_positions(env: CoupledRelayHost, positions: np.ndarray) -> np.ndarray:
    clipped = np.array(positions, dtype=float)
    clipped[:, 0] = np.clip(clipped[:, 0], 0.0, env.area_size)
    clipped[:, 1] = np.clip(clipped[:, 1], 0.0, env.area_size)
    clipped[:, 2] = np.clip(clipped[:, 2], *env.height_range)
    return clipped


def build_candidates(env: CoupledRelayHost, rng: np.random.Generator) -> list[dict[str, Any]]:
    """One candidate per k in K_CANDIDATES: service UAVs at centroids, relays at midpoints."""
    users = np.asarray(env.user_positions, dtype=float)[:, :2]
    bs_xy = np.asarray(env.ground_bs_positions[0, :2], dtype=float)
    candidates = []
    for k in K_CANDIDATES:
        if k > env.n_uavs:
            continue
        centres, _labels = kmeans(users, k, rng)
        order = np.argsort(-np.linalg.norm(centres - bs_xy, axis=1), kind="stable")
        positions = np.zeros((env.n_uavs, 3), dtype=float)
        positions[:k, :2] = centres
        for r in range(env.n_uavs - k):
            target = centres[order[r % k]]
            positions[k + r, :2] = 0.5 * (bs_xy + target)
        positions[:, 2] = SERVICE_HEIGHT_M
        candidates.append({
            "k": int(k),
            "positions_xyz": _clip_positions(env, positions),
            "relay_targets": [int(order[r % k]) for r in range(env.n_uavs - k)],
        })
    return candidates


# ------------------------------------------------------------------------------ search


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
    start_candidate_k: int
    candidates: list[dict[str, Any]] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)
    max_uav_connections_seen: int = 0

    def to_json(self) -> dict[str, Any]:
        return {
            "positions_xyz": self.positions_xyz.tolist(),
            "contract_reward": self.contract_reward,
            "coverage_backhauled": self.coverage_backhauled,
            "evaluations": self.evaluations,
            "budget": self.budget,
            "allow_a2a": self.allow_a2a,
            "converged": self.converged,
            "start_candidate_k": self.start_candidate_k,
            "candidates": [
                {"k": c["k"], "contract_reward": c["contract_reward"],
                 "coverage_backhauled": c["coverage_backhauled"],
                 "positions_xyz": np.asarray(c["positions_xyz"]).tolist()}
                for c in self.candidates
            ],
            "history": self.history,
            "info": self.info,
            "max_uav_connections_seen": self.max_uav_connections_seen,
        }


def search_placement(
    env: CoupledRelayHost,
    allow_a2a: bool,
    budget: int = 3000,
    rng: np.random.Generator | None = None,
) -> PlacementResult:
    """Static placement search; never uses more than ``budget`` static evaluations.

    The env is left at the last evaluated trial (not necessarily the best placement) and
    with ``a2a_enabled = allow_a2a``; callers that step the env must reset it.
    """
    if rng is None:
        raise ValueError("search_placement needs an explicit rng")
    budget = int(budget)
    candidates = build_candidates(env, rng)
    if budget < len(candidates):
        raise ValueError(f"budget {budget} is smaller than the {len(candidates)} candidates")

    evaluations = 0
    max_links = 0
    history: list[dict[str, Any]] = []

    def evaluate(positions: np.ndarray) -> dict[str, Any]:
        nonlocal evaluations, max_links
        info = static_evaluate(env, positions, allow_a2a=allow_a2a)
        evaluations += 1
        max_links = max(max_links, int(info["uav_connection_count"]))
        return info

    best_index = -1
    best_info: dict[str, Any] = {}
    for index, candidate in enumerate(candidates):
        info = evaluate(candidate["positions_xyz"])
        candidate["contract_reward"] = float(info["contract_reward"])
        candidate["coverage_backhauled"] = float(info["coverage_backhauled"])
        if best_index < 0 or info["contract_reward"] > best_info["contract_reward"] + IMPROVEMENT_TOL:
            best_index, best_info = index, info
    position = np.array(candidates[best_index]["positions_xyz"], dtype=float)
    best_reward = float(best_info["contract_reward"])
    history.append({"evaluations": evaluations, "contract_reward": best_reward,
                    "stage": "candidates", "k": candidates[best_index]["k"]})

    step = INITIAL_STEP_M
    converged = False
    moves = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))
    while evaluations < budget:
        improved = False
        for uav in range(env.n_uavs):
            for dx, dy in moves:
                if evaluations >= budget:
                    break
                trial = position.copy()
                trial[uav, 0] += dx * step
                trial[uav, 1] += dy * step
                trial = _clip_positions(env, trial)
                if np.array_equal(trial, position):
                    continue
                info = evaluate(trial)
                if info["contract_reward"] > best_reward + IMPROVEMENT_TOL:
                    position, best_info = trial, info
                    best_reward = float(info["contract_reward"])
                    improved = True
                    history.append({"evaluations": evaluations, "contract_reward": best_reward,
                                    "stage": "descent", "uav": uav, "step_m": step,
                                    "move": [dx * step, dy * step]})
            if evaluations >= budget:
                break
        if evaluations >= budget:
            break
        if not improved:
            if step > FINAL_STEP_M:
                step = FINAL_STEP_M
            else:
                converged = True
                break

    return PlacementResult(
        positions_xyz=position,
        contract_reward=best_reward,
        coverage_backhauled=float(best_info["coverage_backhauled"]),
        evaluations=evaluations,
        history=history,
        allow_a2a=bool(allow_a2a),
        budget=budget,
        converged=converged,
        start_candidate_k=int(candidates[best_index]["k"]),
        candidates=candidates,
        info=dict(best_info),
        max_uav_connections_seen=max_links,
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
        if all(terminations.values()):
            break

    final = dict(env.reward_info)
    result = {
        "steps": len(series["contract_reward"]),
        "allow_a2a": bool(allow_a2a),
        "initial_positions_xyz": initial.tolist(),
        "final_positions_xyz": env.uav_positions.tolist(),
        "series": series,
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
        delta = state["assigned"] - host.uav_positions
        distance = np.linalg.norm(delta, axis=1)
        actions = np.zeros((host.n_uavs, 3), dtype=float)
        for i in range(host.n_uavs):
            if distance[i] <= ARRIVAL_TOL_M:
                continue
            if distance[i] <= stride:
                actions[i] = delta[i] / stride
            else:
                actions[i] = delta[i] / distance[i]
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
