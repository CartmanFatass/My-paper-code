"""One frozen legal-observation energy cost for B03 target allocation."""

from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy,
    own_positions,
    station_records,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    _assign,
)

from .b02_controller import B02Controller, TimedAvailableHeuristic
from .configuration import AvailableLayoutHeuristic


@dataclass(frozen=True)
class S4EnergyModel:
    """S4's published propulsion constants and B03's fixed planning assumptions."""

    p0_w: float = 79.86
    pi_w: float = 88.63
    u_tip_mps: float = 120.0
    v0_mps: float = 4.03
    d0: float = 0.6
    rho_kg_m3: float = 1.225
    rotor_solidity: float = 0.05
    rotor_area_m2: float = 0.503
    vertical_w_per_mps: float = 15.0
    horizontal_speed_mps: float = 30.0
    vertical_speed_mps: float = 5.0
    limp_home_speed_mps: float = 3.0
    battery_capacity_wh: float = 160.0
    reserve_ratio: float = 0.10
    service_seconds: float = 30.0

    @property
    def k3(self) -> float:
        return 0.5 * self.d0 * self.rho_kg_m3 * self.rotor_solidity * self.rotor_area_m2

    def power_w(self, horizontal_mps, vertical_mps):
        horizontal = np.asarray(horizontal_mps, dtype=np.float64)
        vertical = np.asarray(vertical_mps, dtype=np.float64)
        profile = self.p0_w * (1.0 + 3.0 * horizontal**2 / self.u_tip_mps**2)
        term = np.sqrt(1.0 + horizontal**4 / (4.0 * self.v0_mps**4)) \
            - horizontal**2 / (2.0 * self.v0_mps**2)
        induced = self.pi_w * np.sqrt(np.maximum(0.0, term))
        parasitic = self.k3 * horizontal**3
        vertical_power = self.vertical_w_per_mps * np.abs(vertical)
        return profile + induced + parasitic + vertical_power

    def outbound_wh(self, own_xyz: np.ndarray, target_xyz: np.ndarray) -> np.ndarray:
        """Discrete one-second H1 flight energy, with horizontal/vertical caps applied."""
        own = np.asarray(own_xyz, dtype=np.float64)
        target = np.asarray(target_xyz, dtype=np.float64)
        if own.ndim != 2 or own.shape[1] != 3:
            raise ValueError("own_xyz must have shape (n_uavs, 3)")
        if target.ndim != 2 or target.shape[1] != 3:
            raise ValueError("target_xyz must have shape (n_targets, 3)")
        delta = target[None, :, :] - own[:, None, :]
        remaining_xy = np.linalg.norm(delta[:, :, :2], axis=2)
        remaining_z = np.abs(delta[:, :, 2])
        vertical_sign = np.sign(delta[:, :, 2])
        max_steps = max(
            int(np.ceil(float(remaining_xy.max(initial=0.0)) / self.horizontal_speed_mps)),
            int(np.ceil(float(remaining_z.max(initial=0.0)) / self.vertical_speed_mps)),
        )
        result = np.zeros_like(remaining_xy, dtype=np.float64)
        for _ in range(max_steps):
            active = (remaining_xy > 1e-9) | (remaining_z > 1e-9)
            vxy = np.minimum(remaining_xy, self.horizontal_speed_mps)
            vz_abs = np.minimum(remaining_z, self.vertical_speed_mps)
            vz = vertical_sign * vz_abs
            result += np.where(active, self.power_w(vxy, vz), 0.0) / 3600.0
            remaining_xy = np.maximum(0.0, remaining_xy - vxy)
            remaining_z = np.maximum(0.0, remaining_z - vz_abs)
        return result

    def target_missions(self, own_xyz: np.ndarray, battery_ratio: np.ndarray,
                        targets_xy: np.ndarray, station_xyz: np.ndarray,
                        target_height_m: float) -> dict[str, np.ndarray | float]:
        """Predict target + one clock of hover + least-cost legal-station return."""
        own = np.asarray(own_xyz, dtype=np.float64)
        battery = np.asarray(battery_ratio, dtype=np.float64)
        xy = np.asarray(targets_xy, dtype=np.float64)
        stations = np.asarray(station_xyz, dtype=np.float64)
        if own.ndim != 2 or own.shape[1] != 3:
            raise ValueError("own_xyz must have shape (n_uavs, 3)")
        if battery.shape != (len(own),) or not np.isfinite(battery).all():
            raise ValueError("battery_ratio must have one finite value per UAV")
        if np.any((battery < 0.0) | (battery > 1.0)):
            raise ValueError("battery_ratio must be in [0, 1]")
        if xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all():
            raise ValueError("targets_xy must have shape (n_targets, 2) and be finite")
        if stations.ndim != 2 or stations.shape[1] != 3 or len(stations) == 0:
            raise ValueError("station_xyz must have at least one valid (x, y, z) station")
        if not (np.isfinite(own).all() and np.isfinite(stations).all()):
            raise ValueError("positions must be finite")
        target_xyz = np.column_stack((xy, np.full(len(xy), float(target_height_m))))
        outbound = self.outbound_wh(own, target_xyz)
        service = float(self.service_seconds * self.power_w(0.0, 0.0) / 3600.0)
        return_distance = np.linalg.norm(
            target_xyz[:, None, :] - stations[None, :, :], axis=2)
        return_wh_by_station = (
            return_distance / self.limp_home_speed_mps
            * float(self.power_w(self.limp_home_speed_mps, 0.0)) / 3600.0
        )
        chosen_station = np.argmin(return_wh_by_station, axis=1)
        return_wh = return_wh_by_station[np.arange(len(target_xyz)), chosen_station]
        mission = outbound + service + return_wh[None, :]
        usable = np.maximum(
            0.0,
            battery * self.battery_capacity_wh
            - self.reserve_ratio * self.battery_capacity_wh,
        )
        denominator = np.maximum(usable, 1e-6)
        fraction = mission / denominator[:, None]
        slack = usable[:, None] - mission
        return {
            "target_xyz": target_xyz,
            "outbound_wh": outbound,
            "service_wh": service,
            "return_wh_by_station": return_wh_by_station,
            "return_wh": return_wh,
            "chosen_station": chosen_station.astype(np.int64),
            "mission_wh": mission,
            "usable_wh": usable,
            "cost_fraction": fraction,
            "predicted_reserve_slack_wh": slack,
            "hysteresis_wh": float(
                10.0 * self.power_w(self.horizontal_speed_mps, 0.0) / 3600.0),
        }


S4_ENERGY_MODEL = S4EnergyModel()
B03_ARMS = ("distance_hysteresis", "energy_fraction")


def _legal_energy_context(observations, layout, model: S4EnergyModel) -> dict:
    obs = np.asarray(observations)
    positions = own_positions(obs, layout)
    energy = own_energy(obs, layout)
    stations = station_records(obs, layout)
    valid = np.asarray(stations["valid"], dtype=bool)
    if valid.shape != (len(obs), 2):
        raise ValueError("B03 requires the fixed two-station S4 legal suffix")
    known_xyz = []
    station_indices = []
    for index in range(valid.shape[1]):
        views = np.asarray(stations["xyz_m"])[valid[:, index], index]
        if not len(views):
            continue
        if np.max(np.linalg.norm(views - views[0], axis=1), initial=0.0) > 0.02:
            raise ValueError("legal observers disagree on a station's decoded position")
        known_xyz.append(views[0])
        station_indices.append(index)
    if not known_xyz:
        raise ValueError("no legally valid charging station is visible")
    return {"own_xyz": positions,
            "battery_ratio": energy["battery"],
            "return_margin": energy["return_margin"],
            "station_xyz": np.asarray(known_xyz, dtype=np.float64),
            "station_indices": np.asarray(station_indices, dtype=np.int64),
            "model": model}


class EnergyTimedAvailableHeuristic(TimedAvailableHeuristic):
    """B02 H_local clock30 with only its assignment cost replaced by B03's rule."""

    def __init__(self, params, model: S4EnergyModel = S4_ENERGY_MODEL):
        super().__init__(params)
        self.model = model
        self.assignment_records: list[dict] = []
        self._energy_context: dict | None = None
        self._assignment_subcall = 0

    def reset(self) -> None:
        super().reset()
        self.assignment_records = []
        self._energy_context = None
        self._assignment_subcall = 0

    def plan(self, observations, modes, plan_inputs=None):
        if self.params.information != "local" or plan_inputs is not None:
            raise ValueError("B03 energy allocation uses H_local legal observations only")
        wall = time.perf_counter()
        cpu = time.process_time()
        self._energy_context = _legal_energy_context(observations, self.layout, self.model)
        self._assignment_subcall = 0
        try:
            return AvailableLayoutHeuristic.plan(self, observations, modes, plan_inputs)
        finally:
            self._energy_context = None
            self.last_plan_wall_seconds = time.perf_counter() - wall
            self.last_plan_cpu_seconds = time.process_time() - cpu

    def _assign_targets(self, own_xy, uavs, points, targets) -> set[int]:
        if len(uavs) == 0 or len(points) == 0:
            return set()
        context = self._energy_context
        if context is None:
            raise RuntimeError("B03 assignment requested without a legal energy snapshot")
        target_xy = np.asarray(points, dtype=np.float64)
        energy = self.model.target_missions(
            context["own_xyz"], context["battery_ratio"], target_xy,
            context["station_xyz"], self.params.height_m)
        usable = np.asarray(energy["usable_wh"], dtype=np.float64)
        denominator = np.maximum(usable, 1e-6)
        cost = np.asarray(energy["cost_fraction"], dtype=np.float64)[uavs].copy()
        previous_targets = self.targets_xy
        hysteresis = np.asarray(energy["hysteresis_wh"], dtype=np.float64)
        continuation_indices = {}
        for row, uav in enumerate(uavs):
            previous = previous_targets[uav]
            if np.all(np.isfinite(previous)):
                continuing = int(np.argmin(np.linalg.norm(target_xy - previous, axis=1)))
                continuation_indices[int(uav)] = continuing
                cost[row, continuing] -= float(hysteresis) / denominator[uav]
        if not np.isfinite(cost).all():
            raise FloatingPointError("B03 assignment cost is nonfinite")
        assignments = _assign(cost)
        assigned = set()
        chosen = []
        for row, col in assignments:
            uav = int(uavs[row])
            targets[uav] = target_xy[col]
            assigned.add(uav)
            chosen.append({
                "uav": uav,
                "target_index": int(col),
                "target_xy_m": target_xy[col].tolist(),
                "outbound_wh": float(np.asarray(energy["outbound_wh"])[uav, col]),
                "service_wh": float(energy["service_wh"]),
                "return_wh": float(np.asarray(energy["return_wh"])[col]),
                "mission_wh": float(np.asarray(energy["mission_wh"])[uav, col]),
                "usable_wh": float(usable[uav]),
                "cost_fraction": float(np.asarray(energy["cost_fraction"])[uav, col]),
                "assignment_cost_after_hysteresis": float(cost[row, col]),
                "continuation_bonus_applied": continuation_indices.get(uav) == col,
                "continuation_bonus_fraction": (
                    float(hysteresis) / float(denominator[uav])
                    if uav in continuation_indices else 0.0),
                "predicted_reserve_slack_wh": float(
                    np.asarray(energy["predicted_reserve_slack_wh"])[uav, col]),
                "station_index": int(
                    context["station_indices"][np.asarray(energy["chosen_station"])[col]]),
            })
        self.assignment_records.append({
            "plan_call": int(self.calls),
            "assignment_subcall": int(self._assignment_subcall),
            "uavs": [int(index) for index in uavs],
            "targets_xy_m": target_xy.tolist(),
            "selected": chosen,
            "hysteresis_wh": float(hysteresis),
        })
        self._assignment_subcall += 1
        return assigned


class B03Controller(B02Controller):
    """Distance arm is the pinned B02 clock30 path; candidate swaps only the cost."""

    def __init__(self, arm: str):
        if arm not in B03_ARMS:
            raise ValueError(f"B03 arm must be one of {B03_ARMS}")
        super().__init__("clock30")
        self.b03_arm = arm
        if arm == "energy_fraction":
            self.heuristic = EnergyTimedAvailableHeuristic(self.heuristic.params)
            self.reset()

    @property
    def assignment_records(self) -> list[dict]:
        return list(getattr(self.heuristic, "assignment_records", []))
