"""Stage 2-0 assignment modes of H_central's target step (zero-fit stake sizing).

``AssignmentModeHeuristic`` is B01's ``LayoutHeuristic`` with the target step replaced by one
of three rules (declared in NOTES, Stage 2-0; ``priority`` = relays first, then centroids by
descending user count; ``available`` = UAVs whose shield mode is False, ascending index):

- ``hungarian``: the base ``plan`` and ``_assign_targets`` unchanged (distance cost minus the
  previous-target hysteresis, ``_assign`` = Hungarian over ``priority[:len(available)]``); the
  recorded H_central.
- ``identity``: available UAV i takes priority slot i of the full priority list; an unavailable
  UAV's slot stays empty (served by nobody) and that UAV has no target; no cost is used.
- ``independent_nearest``: the base cost matrix over ``priority[:len(available)]`` (hysteresis
  included, built exactly as the base does), then every available UAV takes its own row-wise
  cheapest point; duplicates allowed, unclaimed points unserved.

Mechanism: ``identity`` overrides ``plan`` with a copy of ``LayoutHeuristic.plan`` whose only
change is that ``_assign_targets`` receives the full ``priority`` instead of
``priority[:len(available)]``; ``hungarian`` and ``independent_nearest`` run the base ``plan``.
Everything else (planning, movement, information, shield) is H_central's; ``b01/`` is unchanged.
"""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    SEARCH_STATION,
    HeuristicParams,
    LayoutHeuristic,
    UnobservedRegime,
    estimator_kmeans,
    observed_bs_xy,
    observed_station_xy,
    pooled_users,
    search_ring,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT,
    ObservationLayout,
    own_positions,
)

ASSIGNMENT_MODES = ("hungarian", "identity", "independent_nearest")


class AssignmentModeHeuristic(LayoutHeuristic):
    """``LayoutHeuristic`` whose target step uses one of ``ASSIGNMENT_MODES``."""

    def __init__(self, params: HeuristicParams, mode: str,
                 layout: ObservationLayout = S7S2_LAYOUT):
        if mode not in ASSIGNMENT_MODES:
            raise ValueError(f"assignment mode must be one of {ASSIGNMENT_MODES}")
        self.mode = mode
        super().__init__(params, layout)

    def plan(self, observations: np.ndarray, modes: np.ndarray, plan_inputs=None) -> dict:
        if self.mode != "identity":
            return super().plan(observations, modes, plan_inputs)
        # Copy of LayoutHeuristic.plan; the one change is marked below.
        params = self.params
        station_xy = None
        if params.information == "central":
            if plan_inputs is None:
                raise ValueError("central heuristic requires plan_inputs at every replan")
            users = np.asarray(plan_inputs["users_xy"], dtype=np.float64).copy()
            bs = np.asarray(plan_inputs["bs_xy"], dtype=np.float64).reshape(-1, 2)
            if users.ndim != 2 or users.shape[1] != 2 or len(users) == 0 or len(bs) == 0:
                raise ValueError("plan_inputs must hold (n_users, 2) user xy and (n_bs, 2) BS xy")
            bs_xy = np.mean(bs, axis=0)   # estimator: np.mean(ground_bs_positions[:, :2], axis=0)
        else:
            if plan_inputs is not None:
                raise ValueError("local heuristic must not receive central plan_inputs")
            users = pooled_users(observations, self.layout, params.dedup_tolerance_m)
            bs_xy = observed_bs_xy(observations, self.layout)
            station_xy = observed_station_xy(observations, self.layout)
            if bs_xy is None and station_xy is None:
                raise UnobservedRegime(
                    f"replan at call {self.calls}: no BS and no station {SEARCH_STATION} decodable")
        n_centroids = min(int(params.n_service), len(users))
        if n_centroids >= 1:
            centroids, counts = estimator_kmeans(users, n_centroids, params.kmeans_iterations)
        else:
            centroids, counts = np.zeros((0, 2)), np.zeros(0, dtype=np.int64)
        n_relay = params.n_relay if (n_centroids >= 1 and bs_xy is not None) else 0
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
        used = priority   # CHANGED (identity): full priority list, slot i belongs to UAV i
        targets = np.full((params.n_uavs, 2), np.nan)
        assigned = self._assign_targets(own_xy, available, used, targets)
        # Search prior: available UAVs left without a planned target go to the station-1 ring.
        leftover = np.asarray([uav for uav in available if uav not in assigned], dtype=np.int64)
        ring = np.zeros((0, 2))
        if leftover.size:
            if params.information == "central":   # central plans always cover every UAV
                raise RuntimeError("central plan left available UAVs without a target")
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

    def _assign_targets(self, own_xy, uavs, points, targets) -> set[int]:
        if self.mode == "hungarian":
            return super()._assign_targets(own_xy, uavs, points, targets)
        if self.mode == "identity":
            # Pairs by UAV index: UAV i -> points[i]; no cost.
            assigned = set()
            for uav in uavs:
                if int(uav) < len(points):
                    targets[uav] = points[int(uav)]
                    assigned.add(int(uav))
            return assigned
        # independent_nearest: the base cost matrix (verbatim), then a row-wise argmin.
        params = self.params
        if len(uavs) == 0 or len(points) == 0:
            return set()
        cost = np.linalg.norm(own_xy[uavs][:, None, :] - points[None, :, :], axis=2)
        # Hysteresis: the target continuing a UAV's previous target is cheaper by the margin,
        # so the UAV switches only if another target is closer by more than switch_margin_m.
        for row, uav in enumerate(uavs):
            previous = self.targets_xy[uav]
            if np.all(np.isfinite(previous)):
                continuing = int(np.argmin(np.linalg.norm(points - previous, axis=1)))
                cost[row, continuing] -= params.switch_margin_m
        assigned = set()
        for row, uav in enumerate(uavs):
            col = int(np.argmin(cost[row]))
            targets[uav] = points[col]
            assigned.add(int(uav))
        return assigned


class AssignmentModeController(HeuristicController):
    """``HeuristicController`` driving an ``AssignmentModeHeuristic`` (central plan inputs)."""

    def __init__(self, params: HeuristicParams, env, mode: str):
        super().__init__(params, env)
        self.heuristic = AssignmentModeHeuristic(params, mode)
        self.mode = mode
