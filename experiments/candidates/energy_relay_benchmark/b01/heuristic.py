"""Executed layout heuristic acting from legal observations only.

Every ``replan_period`` calls: pool the users observed by any UAV, run the S7 feasibility
estimator's k-means (seeds at ``np.linspace(0, n-1, k, dtype=int)``, 30 iterations, squared
distance, empty cluster keeps its centroid, ``np.allclose`` stop) with ``n_service`` centroids,
place ``n_relay = n_uavs - n_service`` relay targets at fractions (i+1)/(n_relay+1) on the line
from the observed BS to the mean of the centroids, and assign available UAVs (caller's mode
array False) to targets: relays first, then centroids by descending user count.

Information modes:
- ``"central"`` (H1-H3): at each replan the evaluator supplies ``plan_inputs`` = ground-truth
  user xy (n_users, 2) and BS xy (n_bs, 2) from the raw environment; k-means seeds on the env's
  user indices exactly as the estimator does and the relay line starts at the BS mean.  This
  is a central-information reference ("central-positions"), not a legal-observation controller.
- ``"local"`` (Hlocal): plan inputs from the legal observations only, pooled over the eight
  UAVs in one planner (a pooled central planner, not a per-UAV local controller).  Users =
  union over the UAVs of the decoded user slots (absolute xy = own xy + rel xy), de-duplicated within
  ``dedup_tolerance_m``; BS xy from the legal BS slots (in-radius or cached); station 1's xy
  from the always-present station records of the energy suffix.  At a replan with fewer than
  ``n_service`` distinct visible users the plan uses k = (visible users) centroids, relays only
  if >= 1 centroid and a BS are observed, and every available UAV left without a target goes
  to a search waypoint on a ``search_radius_m`` ring around station 1 (``n_uavs`` equally
  spaced angles from 0 rad, same assignment routine).  With >= ``n_service`` visible users and
  an observed BS this is exactly the normal plan and the ring is unused.  ``UnobservedRegime``
  is raised only when neither a BS nor station 1 is decodable, or the ring is needed and
  station 1 is not decodable (does not occur on S7-S2).
Own position, modes and (in the evaluator) batteries, stations and the shield always come from
the legal observation.

``FixedWaypointHeuristic`` (Stage 0 references H_spawn / H_park2) plans once, at the first
``act`` call of a world (the reset observation), and never again; it moves with the same
per-step primitive as the layout heuristic (``LayoutHeuristic.act``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np

from .observation import (
    S7S2_LAYOUT,
    ObservationLayout,
    bs_records,
    own_positions,
    station_records,
    user_records,
)

try:  # scipy is optional; greedy nearest assignment is the fallback.
    from scipy.optimize import linear_sum_assignment as _lsa
except Exception:  # pragma: no cover - depends on the interpreter
    _lsa = None

UNOBSERVED_RULES = ("station-ring",)
INFORMATION_MODES = ("central", "local")
CONTROLLER_INFORMATION = {"central": "central-positions",
                          "local": ("legal-observation pooled central planner "
                                    "(station-1 ring search prior)")}
SEARCH_STATION = 1   # index of the station record whose xy centres the search ring


class UnobservedRegime(RuntimeError):
    """Local plan impossible: neither BS nor station 1 decodable, or ring needed without station 1."""


@dataclass(frozen=True)
class HeuristicParams:
    n_service: int = 6
    height_m: float = 100.0
    cruise_mps: float = 30.0
    replan_period: int = 30
    switch_margin_m: float = 300.0
    kmeans_iterations: int = 30
    vertical_cap_mps: float = 5.0
    horizontal_speed_mps: float = 30.0   # action scale (B06)
    vertical_speed_mps: float = 5.0      # action scale (B06)
    time_step_s: float = 1.0
    dedup_tolerance_m: float = 0.5
    n_uavs: int = 8
    unobserved: str = "station-ring"
    information: str = "central"
    search_radius_m: float = 1000.0

    def __post_init__(self) -> None:
        if not 1 <= int(self.n_service) <= int(self.n_uavs):
            raise ValueError("n_service must be in [1, n_uavs]")
        if self.replan_period < 1 or self.kmeans_iterations < 1:
            raise ValueError("replan_period and kmeans_iterations must be positive")
        if self.cruise_mps <= 0 or self.vertical_cap_mps <= 0:
            raise ValueError("speed caps must be positive")
        if self.unobserved not in UNOBSERVED_RULES:
            raise ValueError(f"unobserved rule must be one of {UNOBSERVED_RULES}")
        if self.information not in INFORMATION_MODES:
            raise ValueError(f"information must be one of {INFORMATION_MODES}")
        if not self.search_radius_m > 0:
            raise ValueError("search_radius_m must be positive")

    @property
    def n_relay(self) -> int:
        return int(self.n_uavs) - int(self.n_service)

    def record(self) -> dict:
        return asdict(self) | {"n_relay": self.n_relay,
                               "controller_information": CONTROLLER_INFORMATION[self.information]}


VARIANTS = {
    "H1": HeuristicParams(n_service=6, height_m=100.0, cruise_mps=30.0),
    "H2": HeuristicParams(n_service=5, height_m=100.0, cruise_mps=30.0),
    "H3": HeuristicParams(n_service=6, height_m=100.0, cruise_mps=10.0),
}


def variant(name: str, **overrides) -> HeuristicParams:
    return replace(VARIANTS[name], **overrides)


def estimator_kmeans(points: np.ndarray, k: int, iterations: int = 30):
    """Copy of the k-means in ``UAVEnergyAwareRelayEnv.estimate_heuristic_qos_feasibility``.

    Returns (centroids, member counts under the final centroids).
    """
    points = np.asarray(points, dtype=np.float64)
    seed_indices = np.linspace(0, len(points) - 1, int(k), dtype=int)
    centroids = points[seed_indices].copy()
    for _ in range(int(iterations)):
        distances = np.sum((points[:, None, :] - centroids[None, :, :]) ** 2, axis=2)
        labels = np.argmin(distances, axis=1)
        updated = np.array([
            np.mean(points[labels == cluster], axis=0) if np.any(labels == cluster)
            else centroids[cluster]
            for cluster in range(int(k))
        ])
        if np.allclose(updated, centroids):
            break
        centroids = updated
    labels = np.argmin(np.sum((points[:, None, :] - centroids[None, :, :]) ** 2, axis=2), axis=1)
    counts = np.bincount(labels, minlength=int(k))
    return centroids, counts


def pooled_users(observations, layout: ObservationLayout, tolerance_m: float) -> np.ndarray:
    """Union of users seen by any UAV; duplicates (same user, several observers) merged.

    Observations carry no user identity: two reconstructions closer than ``tolerance_m`` are
    treated as one user (first observer in UAV order kept).  Output is sorted by (x, y) so
    the estimator's index seeding is deterministic.
    """
    records = user_records(observations, layout)
    points = records["xy_m"][records["present"]]
    kept: list[np.ndarray] = []
    for point in points:
        if all(np.linalg.norm(point - other) > tolerance_m for other in kept):
            kept.append(point)
    if not kept:
        return np.zeros((0, 2), dtype=np.float64)
    result = np.asarray(kept, dtype=np.float64)
    return result[np.lexsort((result[:, 1], result[:, 0]))]


def observed_bs_xy(observations, layout: ObservationLayout):
    """First present BS slot in UAV order (S7-S2 has one BS), or None."""
    records = bs_records(observations, layout)
    present = np.argwhere(records["present"])
    if present.size == 0:
        return None
    observer, slot = present[0]
    return records["xyz_m"][observer, slot, :2].copy()


def observed_station_xy(observations, layout: ObservationLayout, index: int = SEARCH_STATION):
    """Absolute xy of station ``index`` from the first observer whose record is valid, or None."""
    records = station_records(observations, layout)
    valid = np.flatnonzero(records["valid"][:, index])
    if valid.size == 0:
        return None
    return records["xyz_m"][valid[0], index, :2].copy()


def search_ring(centre_xy: np.ndarray, radius_m: float, count: int) -> np.ndarray:
    """``count`` equally spaced points on a circle around ``centre_xy``, angles from 0 rad."""
    angles = 2.0 * np.pi * np.arange(int(count)) / int(count)
    return np.asarray(centre_xy, dtype=np.float64)[None, :] + float(radius_m) * np.stack(
        (np.cos(angles), np.sin(angles)), axis=1)


def _assign(cost: np.ndarray) -> list[tuple[int, int]]:
    if cost.size == 0:
        return []
    if _lsa is not None:
        rows, cols = _lsa(cost)
        return [(int(r), int(c)) for r, c in zip(rows, cols)]
    pairs, remaining = [], cost.astype(np.float64).copy()
    for _ in range(min(cost.shape)):
        row, col = np.unravel_index(np.argmin(remaining), remaining.shape)
        pairs.append((int(row), int(col)))
        remaining[row, :] = np.inf
        remaining[:, col] = np.inf
    return sorted(pairs)


class LayoutHeuristic:
    """Stateful controller: ``reset()`` per world, ``act(observations, modes)`` per step."""

    def __init__(self, params: HeuristicParams, layout: ObservationLayout = S7S2_LAYOUT):
        self.params = params
        self.layout = layout
        self.reset()

    def reset(self) -> None:
        self.calls = 0
        self.targets_xy = np.full((self.params.n_uavs, 2), np.nan)  # per UAV, NaN = none
        self.last_plan: dict | None = None

    def replans_next(self) -> bool:
        """True when the next ``act`` call replans (the evaluator supplies inputs only then)."""
        return self.calls % self.params.replan_period == 0

    def plan(self, observations: np.ndarray, modes: np.ndarray, plan_inputs=None) -> dict:
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
        used = priority[: len(available)]
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
        """Assign ``uavs`` to ``points`` (min cost, previous-target hysteresis) into ``targets``."""
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
        for row, col in _assign(cost):
            targets[uavs[row]] = points[col]
            assigned.add(int(uavs[row]))
        return assigned

    def act(self, observations: np.ndarray, modes: np.ndarray, plan_inputs=None) -> np.ndarray:
        params = self.params
        obs = np.asarray(observations)
        if obs.shape != (params.n_uavs, self.layout.dim):
            raise ValueError(f"observations must have shape {(params.n_uavs, self.layout.dim)}")
        if self.replans_next():
            self.plan(obs, modes, plan_inputs)
        elif plan_inputs is not None:
            raise ValueError("plan_inputs may be supplied only at replan steps")
        self.calls += 1
        own = own_positions(obs, self.layout)
        actions = np.zeros((params.n_uavs, 4), dtype=np.float32)
        for uav in range(params.n_uavs):
            target = self.targets_xy[uav]
            # UAVs without a target (unavailable at the last replan) hold their xy.
            delta = (target - own[uav, :2]) if np.all(np.isfinite(target)) else np.zeros(2)
            velocity = delta / params.time_step_s
            speed = float(np.linalg.norm(velocity))
            if speed > params.cruise_mps:
                velocity = velocity * (params.cruise_mps / speed)
            vertical = float(np.clip((params.height_m - own[uav, 2]) / params.time_step_s,
                                     -params.vertical_cap_mps, params.vertical_cap_mps))
            actions[uav] = np.clip(np.asarray((
                velocity[0] / params.horizontal_speed_mps,
                velocity[1] / params.horizontal_speed_mps,
                vertical / params.vertical_speed_mps,
                0.0,
            )), -1.0, 1.0)
        return actions


FIXED_WAYPOINT_KINDS = ("spawn", "park2")
PARK_STATIONS = (0, 1)   # station 0 (relay anchor) first, then station 1 (service centre)


def park_assignment(own_xy: np.ndarray, stations_xy) -> list[list[int]]:
    """[[uav, station], ...]: for each station in order, the nearest not-yet-assigned UAV by
    horizontal distance to the station xy (exact ties -> lower UAV index)."""
    own_xy = np.asarray(own_xy, dtype=np.float64)
    free = list(range(len(own_xy)))
    result = []
    for station, xy in zip(PARK_STATIONS, stations_xy):
        distances = np.linalg.norm(own_xy[free] - np.asarray(xy, dtype=np.float64), axis=1)
        uav = free[int(np.argmin(distances))]   # argmin: first occurrence = lower index
        result.append([int(uav), int(station)])
        free.remove(uav)
    return result


class FixedWaypointHeuristic(LayoutHeuristic):
    """Fixed waypoints from the reset observation, held for the whole world.

    ``spawn``: every UAV's target is its own reset xy (legal-observation decode).  ``park2``:
    the same, except the UAVs chosen by ``park_assignment`` take the xy of stations 0 and 1
    (station records of the energy suffix, first valid observer, as ``absolute_station_xy``).
    Altitude, speed caps and the action mapping are ``params``' (``LayoutHeuristic.act``).
    Every UAV has a target at all times, including while the shield holds it in F mode, so it
    resumes the same waypoint after release.
    """

    def __init__(self, params: HeuristicParams, kind: str,
                 layout: ObservationLayout = S7S2_LAYOUT):
        if kind not in FIXED_WAYPOINT_KINDS:
            raise ValueError(f"kind must be one of {FIXED_WAYPOINT_KINDS}")
        self.kind = kind
        super().__init__(params, layout)

    def reset(self) -> None:
        super().reset()
        self.park_assignment: list[list[int]] = []

    def replans_next(self) -> bool:
        return self.calls == 0

    def plan(self, observations: np.ndarray, modes: np.ndarray, plan_inputs=None) -> dict:
        if plan_inputs is not None:
            raise ValueError("fixed-waypoint heuristic takes no central plan_inputs")
        own_xy = own_positions(observations, self.layout)[:, :2].astype(np.float64)
        targets = own_xy.copy()
        assignment: list[list[int]] = []
        stations = []
        if self.kind == "park2":
            for index in PARK_STATIONS:
                xy = observed_station_xy(observations, self.layout, index)
                if xy is None:
                    raise UnobservedRegime(f"station {index} not decodable at reset")
                stations.append(np.asarray(xy, dtype=np.float64))
            assignment = park_assignment(own_xy, stations)
            for uav, station in assignment:
                targets[uav] = stations[station]
        self.targets_xy = targets
        self.park_assignment = assignment
        plan = {"call": self.calls, "information": f"fixed-{self.kind}", "own_xy": own_xy,
                "stations_xy": stations, "park_assignment": assignment,
                "targets": targets.copy(), "search": False}
        self.last_plan = plan
        return plan
