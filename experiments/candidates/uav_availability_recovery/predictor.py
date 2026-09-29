"""Public-state, nominal native-service planner for two reserve commands."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from configs.config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from ha_ctse_process.uav_g0_geometry import actions_toward_targets


_HORIZONS = (10, 40, 80, 120)
_WEIGHTS = (10, 30, 40, 40)
_HORIZON = 500
_TIE_TOLERANCE = 1e-10


def _array(value: np.ndarray, shape: tuple[int, ...], dtype: type, name: str) -> np.ndarray:
    result = np.array(value, dtype=dtype, copy=True)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite with shape {shape}")
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class PublicSnapshot:
    """One decision boundary, in original assignment order: six primaries, two reserves."""

    positions: np.ndarray
    active: np.ndarray
    user_xy: np.ndarray
    demand_mbps: np.ndarray
    base_xy: np.ndarray
    candidate_targets: np.ndarray
    incumbent_action: int
    physical_step: int
    absence_age: int
    event_owner_index: int
    has_returned: bool
    max_speed: float
    max_vertical_speed_mps: float
    time_step: float
    area_size: float
    height_range: tuple[float, float]

    def __post_init__(self) -> None:
        for name, shape, dtype in (
            ("positions", (8, 3), np.float64),
            ("active", (8,), np.bool_),
            ("user_xy", (30, 2), np.float32),
            ("demand_mbps", (30,), np.float64),
            ("base_xy", (2,), np.float64),
            ("candidate_targets", (16, 8, 3), np.float64),
        ):
            object.__setattr__(self, name, _array(getattr(self, name), shape, dtype, name))
        if not 0 <= self.incumbent_action < 16:
            raise ValueError("incumbent_action must be a candidate index")
        if not 0 <= self.physical_step < _HORIZON:
            raise ValueError("physical_step must be a live H500 boundary")
        if not 0 <= self.event_owner_index < 6:
            raise ValueError("event_owner_index must name an original primary")
        if not 0 <= self.absence_age <= 100:
            raise ValueError("absence_age outside the declared duration support")
        if np.any(~self.active[np.arange(8) != self.event_owner_index]):
            raise ValueError("only the event owner can be unavailable")
        if self.has_returned and not self.active[self.event_owner_index]:
            raise ValueError("returned owner must be active")
        if not self.has_returned and self.absence_age and self.active[self.event_owner_index]:
            raise ValueError("absent owner cannot be active")
        if np.any(self.demand_mbps <= 0):
            raise ValueError("demands must be positive")
        low, high = self.height_range
        if not np.isfinite((low, high)).all() or low > high:
            raise ValueError("invalid height range")
        for name in ("max_speed", "max_vertical_speed_mps", "time_step", "area_size"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")


def active_probability(absence_age: int, horizon: int, has_returned: bool) -> float:
    if has_returned:
        return 1.0
    if absence_age < 0 or absence_age > 100 or horizon < 0:
        raise ValueError("invalid posterior arguments")
    first = max(80, absence_age + 1)
    if first > 100:
        raise ValueError("an absent owner cannot exceed duration support")
    return float(np.clip(absence_age + horizon - first + 1, 0, 101 - first) / (101 - first))


def truncated_horizons(physical_step: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    remaining = _HORIZON - physical_step
    if not 1 <= remaining <= _HORIZON:
        raise ValueError("physical_step must be a live H500 boundary")
    horizons, weights = [], []
    previous = 0
    for endpoint, full_weight in zip(_HORIZONS, _WEIGHTS):
        interval = min(endpoint, remaining) - previous
        if interval <= 0:
            break
        horizons.append(min(endpoint, remaining))
        weights.append(min(full_weight, interval))
        previous = endpoint
    return tuple(horizons), tuple(weights)


class _PublicServiceEnv(UAVEnergyAwareRelayEnv):
    """An S7-S1 radio model whose only changing inputs are public snapshot fields."""

    def __init__(self) -> None:
        self._public_active = np.ones(8, dtype=np.bool_)
        super().__init__(config=Config("S7-S1"), seed=0)
        if (self.n_uavs, self.n_users, self.n_ground_bs, self.max_steps) != (8, 30, 1, 500):
            raise ValueError("S7-S1 inventory changed")
        if self.battery_enabled or self.charging_enabled or self.failure_enabled:
            raise ValueError("S7-S1 availability configuration changed")
        self.sinr_matrix = np.zeros((self.n_uavs, self.n_users), dtype=np.float64)
        self.uav_connections = np.zeros((self.n_uavs, self.n_uavs), dtype=np.bool_)
        self.uav_bs_connections = np.zeros((self.n_uavs, self.n_ground_bs), dtype=np.bool_)

    def _is_uav_unavailable(self, uav_idx: int) -> bool:
        return not bool(self._public_active[int(uav_idx)]) or super()._is_uav_unavailable(uav_idx)

    def _communication_unavailable_mask(self) -> np.ndarray:
        return super()._communication_unavailable_mask() | ~self._public_active

    def snapshot_qos(
        self, snapshot: PublicSnapshot, positions: np.ndarray, active: np.ndarray
    ) -> float:
        if (
            float(self.max_speed) != snapshot.max_speed
            or float(self.max_vertical_speed_mps) != snapshot.max_vertical_speed_mps
            or float(self.time_step) != snapshot.time_step
            or float(self.area_size) != snapshot.area_size
            or tuple(map(float, self.height_range)) != tuple(snapshot.height_range)
        ):
            raise ValueError("public physics differ from S7-S1")
        self.uav_positions = np.array(positions, dtype=np.float64, copy=True)
        self.user_positions = np.column_stack(
            (snapshot.user_xy.astype(np.float64), np.full(30, 1.5))
        )
        self.ground_bs_positions = np.array([[*snapshot.base_xy, 30.0]], dtype=np.float64)
        self._public_active = np.array(active, dtype=np.bool_, copy=True)
        self.current_step = snapshot.physical_step
        self.connections.fill(False)
        self.sinr_matrix.fill(0.0)
        self.uav_connections.fill(False)
        self.uav_bs_connections.fill(False)
        self.user_serving_uav.fill(-1)
        self.user_serving_sets = [[] for _ in range(self.n_users)]
        self.routing_paths = {}
        self._step_communication_cache = None
        self._relay_geometry_state = None
        self._update_channel_state()
        self._update_uav_connections()
        self._compute_routing_paths()
        rates_bps, _, _ = self._calculate_end_to_end_user_rates()
        return float(np.mean(np.minimum(rates_bps / (snapshot.demand_mbps * 1e6), 1.0)))


def _project_positions(
    snapshot: PublicSnapshot, targets: np.ndarray, horizon: int, active: np.ndarray
) -> np.ndarray:
    positions = snapshot.positions.copy()
    for _ in range(horizon):
        actions = actions_toward_targets(
            physical_positions=positions,
            target_positions=targets,
            active_mask=active,
            max_speed=snapshot.max_speed,
            max_vertical_speed=snapshot.max_vertical_speed_mps,
            time_step=snapshot.time_step,
        )
        horizontal = actions[:, :2].astype(np.float64)
        norm = np.linalg.norm(horizontal, axis=1)
        scale = np.where(norm > 1e-8, np.minimum(norm, 1.0) / np.maximum(norm, 1e-8), 0.0)
        positions[:, :2] += horizontal * scale[:, None] * snapshot.max_speed * snapshot.time_step
        positions[:, 2] += actions[:, 2] * snapshot.max_vertical_speed_mps * snapshot.time_step
        positions[:, :2] = np.clip(positions[:, :2], 0.0, snapshot.area_size)
        positions[:, 2] = np.clip(positions[:, 2], *snapshot.height_range)
    return positions


@dataclass(frozen=True)
class PredictorDecision:
    action: int
    scores: np.ndarray
    horizons: tuple[int, ...]
    weights: tuple[int, ...]
    active_probabilities: tuple[float, ...]
    predictions: np.ndarray
    active_predictions: np.ndarray
    absent_predictions: np.ndarray
    travel: np.ndarray
    snapshot_calls: int

    def to_dict(self) -> dict:
        def branch(values: np.ndarray) -> list[list[float | None]]:
            return [
                [float(value) if np.isfinite(value) else None for value in row]
                for row in values
            ]

        return {
            "action": self.action,
            "scores": self.scores.tolist(),
            "horizons": list(self.horizons),
            "weights": list(self.weights),
            "active_probabilities": list(self.active_probabilities),
            "predictions": self.predictions.tolist(),
            "active_predictions": branch(self.active_predictions),
            "absent_predictions": branch(self.absent_predictions),
            "travel": self.travel.tolist(),
            "snapshot_calls": self.snapshot_calls,
            "nominal_active_from_boundary": True,
            "association_recomputed_without_history": True,
            "future_guard_approximated": True,
        }


class PublicPredictor:
    def __init__(self) -> None:
        self._env: _PublicServiceEnv | None = None
        self.snapshot_calls = 0

    def score(self, snapshot: PublicSnapshot) -> PredictorDecision:
        if self._env is None:
            self._env = _PublicServiceEnv()
        horizons, weights = truncated_horizons(snapshot.physical_step)
        probabilities = tuple(
            active_probability(snapshot.absence_age, horizon, snapshot.has_returned)
            for horizon in horizons
        )
        predictions = np.empty((16, len(horizons)), dtype=np.float64)
        active_predictions = np.full_like(predictions, np.nan)
        absent_predictions = np.full_like(predictions, np.nan)
        travel = np.linalg.norm(
            snapshot.candidate_targets[:, 6:8] - snapshot.positions[None, 6:8], axis=2
        ).sum(axis=1)
        absent_mask = snapshot.active.copy()
        active_mask = snapshot.active.copy()
        active_mask[snapshot.event_owner_index] = True
        for action in range(16):
            targets = snapshot.candidate_targets[action]
            for column, (horizon, probability) in enumerate(zip(horizons, probabilities)):
                if probability > 0.0:
                    positions = _project_positions(snapshot, targets, horizon, active_mask)
                    active_predictions[action, column] = self._env.snapshot_qos(
                        snapshot, positions, active_mask
                    )
                    self.snapshot_calls += 1
                if probability < 1.0:
                    positions = _project_positions(snapshot, targets, horizon, absent_mask)
                    absent_predictions[action, column] = self._env.snapshot_qos(
                        snapshot, positions, absent_mask
                    )
                    self.snapshot_calls += 1
                predictions[action, column] = (
                    probability * active_predictions[action, column]
                    if probability > 0.0 else 0.0
                ) + (
                    (1.0 - probability) * absent_predictions[action, column]
                    if probability < 1.0 else 0.0
                )
        scores = predictions @ np.asarray(weights, dtype=np.float64) / sum(weights)
        best = float(np.max(scores))
        tied = np.flatnonzero(scores >= best - _TIE_TOLERANCE)
        if snapshot.incumbent_action in tied:
            action = snapshot.incumbent_action
        else:
            action = min((int(index) for index in tied), key=lambda index: (travel[index], index))
        return PredictorDecision(
            action=action,
            scores=scores,
            horizons=horizons,
            weights=weights,
            active_probabilities=probabilities,
            predictions=predictions,
            active_predictions=active_predictions,
            absent_predictions=absent_predictions,
            travel=travel,
            snapshot_calls=self.snapshot_calls,
        )
