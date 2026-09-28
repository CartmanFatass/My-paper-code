"""Legal-observation H1 deployment with a common one-scout action library."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy, variant
from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy, own_positions
from experiments.candidates.uav_information_value.controllers import (
    PointSetHeuristic,
    canonical_legal_users,
)


N_ACTIONS = 257
ARENA_M = 8000.0
SURVEY_CELL_M = 250.0
SENSOR_RANGE_M = 1500.0
USER_HEIGHT_M = 1.5
USER_SPEED_MPS = 3.0
REPLAN_STEPS = 30
WAYPOINTS_XY = np.asarray(
    [(x, y) for x in np.arange(250.0, ARENA_M, 500.0)
     for y in np.arange(250.0, ARENA_M, 500.0)], dtype=np.float64)
SURVEY_XY = np.asarray(
    [(x, y) for x in np.arange(125.0, ARENA_M, SURVEY_CELL_M)
     for y in np.arange(125.0, ARENA_M, SURVEY_CELL_M)], dtype=np.float64)
SURVEY_HALF_DIAGONAL_M = SURVEY_CELL_M / np.sqrt(2.0)
FEATURE_DIM = 8 * 365 + 3 + 1024 + 1024 + 512 + 1 + 8 + 16 + 1


class _PreparedHeuristic(PointSetHeuristic):
    """Use an externally prepared plan once, preserving the original H1 call count."""

    def reset(self) -> None:
        super().reset()
        self._prepared = False

    def replans_next(self) -> bool:
        return not self._prepared and super().replans_next()

    def act(self, observations, modes, plan_inputs=None):
        try:
            return super().act(observations, modes, plan_inputs)
        finally:
            self._prepared = False


def _prior(bs_xy: np.ndarray) -> np.ndarray:
    xy = SURVEY_XY
    central = np.all((xy >= 2000.0) & (xy < 6000.0), axis=1)
    remote_x = (xy[:, 0] >= 6400.0) if bs_xy[0] < 4000.0 else (xy[:, 0] < 1600.0)
    remote_y = (xy[:, 1] >= 6400.0) if bs_xy[1] < 4000.0 else (xy[:, 1] < 1600.0)
    remote = remote_x & remote_y
    return (.95 * (.8 * central / central.sum() + .2 * remote / remote.sum())
            + .05 / len(xy))


def _tour(bs_xy: np.ndarray) -> np.ndarray:
    # A waypoint belongs to the higher-priority support when its center lies there.
    xy = WAYPOINTS_XY
    central = np.all((xy >= 2000.0) & (xy < 6000.0), axis=1)
    remote_x = (xy[:, 0] >= 6400.0) if bs_xy[0] < 4000.0 else (xy[:, 0] < 1600.0)
    remote_y = (xy[:, 1] >= 6400.0) if bs_xy[1] < 4000.0 else (xy[:, 1] < 1600.0)
    groups = (np.flatnonzero(central | (remote_x & remote_y)),
              np.flatnonzero(~(central | (remote_x & remote_y))))
    remaining = [set(map(int, group)) for group in groups]
    order: list[int] = []
    cursor = np.asarray((4000.0, 4000.0))
    for group in remaining:
        while group:
            index = min(group, key=lambda i: (np.linalg.norm(xy[i] - cursor), i))
            order.append(index)
            cursor = xy[index]
            group.remove(index)
    assert len(order) == N_ACTIONS - 1
    return np.asarray(order, dtype=np.int64)


class SensingController:
    """One controller per world. No simulator object or RNG is retained."""

    feature_dim = FEATURE_DIM

    def __init__(self, mode: str, policy=None):
        if mode not in ("H", "P", "A", "L"):
            raise ValueError(f"unknown sensing mode {mode!r}")
        self.mode = mode
        self.policy = policy
        self.heuristic = _PreparedHeuristic(variant("H1", information="local"))
        self.reset()

    def reset(self) -> None:
        self.heuristic.reset()
        self._step = 0
        self._prepared_step: int | None = None
        self._seen_bs_xy: np.ndarray | None = None
        self._survey_expiry = np.full(len(SURVEY_XY), -np.inf, dtype=np.float64)
        self._prior_mass = np.full(len(SURVEY_XY), 1.0 / len(SURVEY_XY))
        self._tour_order: np.ndarray | None = None
        self._tour_visited: set[int] = set()
        self._scout: int | None = None
        self._eligible = False
        self._choice = 0
        self._previous_waypoint: int | None = None
        self._own_xyz = np.zeros((8, 3), dtype=np.float64)
        self._effective_targets = self.heuristic.targets_xy.copy()
        self.diagnostics: list[dict] = []

    @property
    def targets_xy(self) -> np.ndarray:
        return self._effective_targets.copy()

    def _assimilate(self, observations, *, survey: bool = False) -> None:
        obs = np.asarray(observations)
        if obs.shape != (8, self.heuristic.layout.dim):
            raise ValueError(f"observations must have shape {(8, self.heuristic.layout.dim)}")
        bs = observed_bs_xy(obs, self.heuristic.layout)
        if bs is not None:
            self._seen_bs_xy = bs.copy()
        self._own_xyz = own_positions(obs, self.heuristic.layout)
        if not survey:
            return
        horizontal = np.linalg.norm(
            self._own_xyz[:, None, :2] - SURVEY_XY[None, :, :], axis=2)
        vertical = self._own_xyz[:, None, 2] - USER_HEIGHT_M
        clearance = SENSOR_RANGE_M - np.sqrt(
            (horizontal + SURVEY_HALF_DIAGONAL_M) ** 2 + vertical ** 2)
        expiry = self._step + np.maximum(clearance, 0.0) / USER_SPEED_MPS
        self._survey_expiry = np.maximum(
            self._survey_expiry, np.max(np.where(clearance >= 0.0, expiry, -np.inf), axis=0))

    def prepare(self, observations, modes, step: int) -> np.ndarray:
        if step != self._step or step % REPLAN_STEPS or self._prepared_step is not None:
            raise ValueError("prepare requires the next unprepared 30-step boundary")
        modes = np.asarray(modes, dtype=bool)
        if modes.shape != (8,):
            raise ValueError("modes must have shape (8,)")
        self._assimilate(observations, survey=True)
        users = canonical_legal_users(observations, self.heuristic.layout,
                                      self.heuristic.params.dedup_tolerance_m)
        bs = None if self._seen_bs_xy is None else self._seen_bs_xy.copy()
        plan = self.heuristic.plan(observations, modes, {"users_xy": users, "bs_xy": bs})
        self.heuristic._prepared = True
        self._effective_targets = self.heuristic.targets_xy.copy()
        self._scout = None
        if bs is not None and 6 <= len(users) < 30:
            energy = own_energy(observations, self.heuristic.layout)
            relays = plan["relays"]
            services = plan["centroids"]
            candidates = []
            for uav, target in enumerate(plan["targets"]):
                if (modes[uav] or not energy["available"][uav]
                        or energy["return_margin"][uav] <= np.float32(.20)):
                    continue
                if not np.all(np.isfinite(target)):
                    continue
                if len(relays) and np.any(np.linalg.norm(relays - target, axis=1) < 1e-3):
                    continue
                if len(services) and np.any(np.linalg.norm(services - target, axis=1) < 1e-3):
                    candidates.append(uav)
            if candidates:
                self._scout = min(candidates, key=lambda i: (-float(energy["return_margin"][i]), i))
        self._eligible = self._scout is not None
        self._prior_mass = _prior(bs) if bs is not None else np.full(len(SURVEY_XY), 1.0 / len(SURVEY_XY))
        if bs is not None and self._tour_order is None:
            self._tour_order = _tour(bs)
        self._choice = 0
        self._prepared_step = step
        self.diagnostics.append({"step": int(step), "users": int(len(users)),
                                 "bs_known": bs is not None, "scout": self._scout,
                                 "eligible": self._eligible, "requested": None,
                                 "executed": None, "fallback": False})
        seen = np.isfinite(self._survey_expiry)
        freshness = np.zeros(len(SURVEY_XY), dtype=np.float64)
        freshness[seen] = np.clip((self._survey_expiry[seen] - step) / 500.0, 0.0, 1.0)
        targets = np.nan_to_num(plan["targets"], nan=-1.0) / ARENA_M
        scout_onehot = np.zeros(8, dtype=np.float32)
        if self._scout is not None:
            scout_onehot[self._scout] = 1.0
        features = np.concatenate((
            np.asarray(observations, dtype=np.float32).ravel(),
            np.asarray([float(bs is not None), *(bs / ARENA_M if bs is not None else (0.0, 0.0))]),
            freshness, self._prior_mass, (WAYPOINTS_XY / ARENA_M).ravel(),
            np.asarray([float(self._eligible)]), scout_onehot, targets.ravel(),
            np.asarray([step / self.heuristic.layout.max_steps]),
        )).astype(np.float32)
        assert features.shape == (FEATURE_DIM,)
        return features

    def _sensed_waypoints(self) -> np.ndarray:
        horizontal = np.linalg.norm(self._own_xyz[:, None, :2] - WAYPOINTS_XY[None, :, :], axis=2)
        vertical = self._own_xyz[:, None, 2] - USER_HEIGHT_M
        return np.any(horizontal ** 2 + vertical ** 2 <= SENSOR_RANGE_M ** 2, axis=0)

    def choose_default(self) -> int:
        if self._prepared_step != self._step:
            raise RuntimeError("choose_default requires prepare")
        if self.mode in ("H", "L") or not self._eligible:
            return 0
        if self.mode == "P":
            sensed = self._sensed_waypoints()
            self._tour_visited.update(map(int, np.flatnonzero(sensed)))
            for _ in range(2):
                for index in self._tour_order:
                    if int(index) not in self._tour_visited:
                        return int(index) + 1
                self._tour_visited.clear()
                self._tour_visited.update(map(int, np.flatnonzero(sensed)))
            return 0
        distance = np.linalg.norm(WAYPOINTS_XY - self._own_xyz[self._scout, :2], axis=1)
        adjusted = distance.copy()
        if self._previous_waypoint is not None:
            adjusted[self._previous_waypoint] = max(0.0, adjusted[self._previous_waypoint] - 300.0)
        arrival = distance / self.heuristic.params.cruise_mps
        cost = adjusted / self.heuristic.params.cruise_mps
        horizontal = np.linalg.norm(WAYPOINTS_XY[:, None, :] - SURVEY_XY[None, :, :], axis=2)
        vertical = self.heuristic.params.height_m - USER_HEIGHT_M
        footprint = ((horizontal + SURVEY_HALF_DIAGONAL_M) ** 2 + vertical ** 2
                     <= SENSOR_RANGE_M ** 2)
        stale = self._survey_expiry[None, :] <= self._step + arrival[:, None]
        scores = (footprint * stale * self._prior_mass[None, :]).sum(axis=1) / (1.0 + cost)
        best = int(np.argmax(scores))
        return best + 1 if scores[best] > 0.0 else 0

    def apply_choice(self, choice: int) -> dict:
        if self._prepared_step != self._step:
            raise RuntimeError("apply_choice requires prepare")
        if (isinstance(choice, (bool, np.bool_)) or not isinstance(choice, (int, np.integer))
                or not 0 <= int(choice) < N_ACTIONS):
            raise ValueError(f"choice must be an integer in [0, {N_ACTIONS - 1}]")
        requested = int(choice)
        executed = requested if self._eligible and self.mode != "H" else 0
        self._choice = executed
        self._effective_targets = self.heuristic.targets_xy.copy()
        if executed:
            index = executed - 1
            self._effective_targets[self._scout] = WAYPOINTS_XY[index]
            self._previous_waypoint = index
        else:
            self._previous_waypoint = None
        row = self.diagnostics[-1]
        row.update({"requested": requested, "executed": executed,
                    "fallback": requested != executed})
        return row.copy()

    def act(self, observations) -> np.ndarray:
        if self._step % REPLAN_STEPS == 0 and self._prepared_step != self._step:
            raise RuntimeError("act requires prepare at each 30-step boundary")
        if self._step % REPLAN_STEPS == 0 and self.diagnostics[-1]["executed"] is None:
            raise RuntimeError("act requires apply_choice at each 30-step boundary")
        self._assimilate(observations)
        nominal = self.heuristic.targets_xy.copy()
        try:
            self.heuristic.targets_xy = self._effective_targets.copy()
            actions = self.heuristic.act(observations, np.zeros(8, dtype=bool))
        finally:
            self.heuristic.targets_xy = nominal
        self._step += 1
        if self._step % REPLAN_STEPS == 0:
            self._prepared_step = None
        return actions

    def propose(self, observations, state, step, previous_done, modes):
        if step != self._step:
            raise ValueError("external step disagrees with controller clock")
        if step % REPLAN_STEPS == 0:
            features = self.prepare(observations, modes, step)
            if self.mode == "L":
                if self.policy is None:
                    raise ValueError("L requires a policy")
                choice, _ = self.policy.predict(features, deterministic=True)
                choice = int(np.asarray(choice).item())
            else:
                choice = self.choose_default()
            self.apply_choice(choice)
        return self.act(observations)
