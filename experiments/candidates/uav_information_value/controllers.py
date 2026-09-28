"""Fixed H1 controllers for the B01 position-source comparison."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    LayoutHeuristic,
    SEARCH_STATION,
    UnobservedRegime,
    estimator_kmeans,
    observed_bs_xy,
    observed_station_xy,
    search_ring,
    variant,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions, user_records


ARMS = ("L", "U", "B", "F", "R", "H_BS")


def _canonical_users(points: np.ndarray, tolerance_m: float) -> np.ndarray:
    """Anonymous full-source points, in deterministic geometric rather than env order."""
    points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    points = points[np.lexsort((points[:, 1], points[:, 0]))]
    kept: list[np.ndarray] = []
    for point in points:
        if all(np.linalg.norm(point - other) > tolerance_m for other in kept):
            kept.append(point)
    return np.asarray(kept, dtype=np.float64).reshape(-1, 2)


def canonical_legal_users(observations, layout, tolerance_m):
    records = user_records(observations, layout)
    return _canonical_users(records["xy_m"][records["present"]], tolerance_m)


class PointSetHeuristic(LayoutHeuristic):
    """Original H1 motion and assignment with explicitly supplied anonymous point sets."""

    def plan(self, observations, modes, plan_inputs=None) -> dict:
        if plan_inputs is None:
            raise ValueError("point-set planner requires plan_inputs at each replan")
        params = self.params
        users = plan_inputs["users_xy"]
        bs_xy = plan_inputs["bs_xy"]
        station_xy = observed_station_xy(observations, self.layout)
        if bs_xy is None and station_xy is None:
            raise UnobservedRegime(
                f"replan at call {self.calls}: no BS and no station {SEARCH_STATION} decodable")

        n_centroids = min(int(params.n_service), len(users))
        if n_centroids:
            centroids, counts = estimator_kmeans(users, n_centroids, params.kmeans_iterations)
        else:
            centroids, counts = np.zeros((0, 2)), np.zeros(0, dtype=np.int64)
        n_relay = params.n_relay if (n_centroids and bs_xy is not None) else 0
        if n_relay:
            centre = centroids.mean(axis=0)
            relays = np.asarray([
                bs_xy + (index + 1) / (n_relay + 1) * (centre - bs_xy)
                for index in range(n_relay)
            ]).reshape(n_relay, 2)
        else:
            relays = np.zeros((0, 2))
        order = np.argsort(-counts, kind="stable")
        priority = np.concatenate((relays, centroids[order]), axis=0)
        kinds = ["relay"] * n_relay + ["service"] * n_centroids

        own_xy = own_positions(observations, self.layout)[:, :2]
        available = np.flatnonzero(~np.asarray(modes, dtype=bool))
        used = priority[: len(available)]
        targets = np.full((params.n_uavs, 2), np.nan)
        assigned = self._assign_targets(own_xy, available, used, targets)
        leftover = np.asarray([uav for uav in available if uav not in assigned], dtype=np.int64)
        ring = np.zeros((0, 2))
        if leftover.size:
            if station_xy is None:
                raise UnobservedRegime(
                    f"replan at call {self.calls}: {leftover.size} UAVs need the search ring "
                    f"but station {SEARCH_STATION} is not decodable")
            ring = search_ring(station_xy, params.search_radius_m, params.n_uavs)
            self._assign_targets(own_xy, leftover, ring, targets)
        self.targets_xy = targets
        plan = {"call": self.calls, "information": params.information,
                "users": users, "bs_xy": bs_xy, "station_xy": station_xy,
                "centroids": centroids, "counts": counts, "relays": relays,
                "priority": priority, "kinds": kinds, "targets": targets.copy(),
                "search": bool(leftover.size), "search_uavs": leftover.tolist(),
                "search_waypoints": ring}
        self.last_plan = plan
        return plan


class SourceController:
    """Supply selected position sources only at H1 replans; observe legal BS every call."""

    def __init__(self, arm: str, env=None):
        self.arm = arm
        self.heuristic = PointSetHeuristic(variant("H1", information="local"))
        if arm in ("U", "B", "F"):
            if env is None:
                raise ValueError(f"arm {arm} requires the environment")
            self.env = env
        self.reset()

    def reset(self) -> None:
        self.heuristic.reset()
        self._seen_bs_xy: np.ndarray | None = None
        self.diagnostics: list[dict] = []
        self.plan_input_steps: list[int] = []
        self.search_replan_steps: list[int] = []

    def propose(self, observations, state, step, previous_done, modes):
        current_bs = observed_bs_xy(observations, self.heuristic.layout)
        if current_bs is not None:
            self._seen_bs_xy = current_bs.copy()
        replans = self.heuristic.replans_next()
        inputs = None
        if replans:
            params = self.heuristic.params
            if self.arm in ("U", "F"):
                raw = getattr(self.env, "env", self.env)
                users = _canonical_users(np.asarray(raw.user_positions)[:, :2],
                                         params.dedup_tolerance_m)
            else:
                users = canonical_legal_users(observations, self.heuristic.layout,
                                              params.dedup_tolerance_m)
            if self.arm in ("B", "F"):
                raw = getattr(self.env, "env", self.env)
                bs_xy = np.asarray(raw.ground_bs_positions, dtype=np.float64)[:, :2].mean(axis=0)
            elif self.arm == "H_BS" and current_bs is None:
                bs_xy = None if self._seen_bs_xy is None else self._seen_bs_xy.copy()
            else:
                bs_xy = current_bs
            inputs = {"users_xy": users, "bs_xy": bs_xy}
        actions = self.heuristic.act(observations, modes, inputs)
        if replans:
            plan = self.heuristic.last_plan
            self.diagnostics.append({
                "call": plan["call"], "supplied_user_count": len(inputs["users_xy"]),
                "current_bs_present": current_bs is not None,
                "seen_bs_so_far": self._seen_bs_xy is not None,
                "memory_used": self.arm == "H_BS" and current_bs is None and bs_xy is not None,
                "search": plan["search"],
                "user_source": "true" if self.arm in ("U", "F") else "legal",
                "bs_source": ("true" if self.arm in ("B", "F") else
                              "legal-memory" if self.arm == "H_BS" else "legal"),
            })
            if self.arm in ("U", "B", "F"):
                self.plan_input_steps.append(int(step))
            if plan["search"]:
                self.search_replan_steps.append(int(step))
        return actions

    @property
    def targets_xy(self) -> np.ndarray:
        return self.heuristic.targets_xy.copy()


def make_controller(arm: str, env=None):
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    if arm == "R":
        return HeuristicController(variant("H1", information="central"), env)
    return SourceController(arm, env)
