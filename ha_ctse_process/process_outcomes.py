"""Process outcome extraction for the standalone HA-CTSE process core."""

from __future__ import annotations

import numpy as np


PROCESS_OUTCOME_FIELDS = (
    "delta_coverage_ratio",
    "delta_effective_connected_users",
    "delta_system_throughput_mbps",
    "delta_qos_satisfaction",
    "delta_backhaul_margin",
    "delta_energy_ratio",
    "delta_distance_to_nearest_charger",
    "charging_progress",
    "return_pressure_change",
    "fallback_obs_delta_l2",
    "fallback_obs_delta_mean_abs",
    "fallback_reward_return",
)


class MaskedRunningMeanStd:
    def __init__(self, size: int, eps: float = 1e-8):
        self.size = int(size)
        self.eps = float(eps)
        self.mean = np.zeros(self.size, dtype=np.float64)
        self.var = np.ones(self.size, dtype=np.float64)
        self.count = np.zeros(self.size, dtype=np.float64)
        self._m2 = np.zeros(self.size, dtype=np.float64)

    def update(self, values, mask) -> None:
        values = np.asarray(values, dtype=np.float64).reshape(self.size)
        mask = np.asarray(mask, dtype=np.bool_).reshape(self.size)
        finite = mask & np.isfinite(values)
        for idx in np.flatnonzero(finite):
            old_count = self.count[idx]
            new_count = old_count + 1.0
            delta = values[idx] - self.mean[idx]
            self.mean[idx] += delta / new_count
            delta2 = values[idx] - self.mean[idx]
            self._m2[idx] += delta * delta2
            self.count[idx] = new_count
            self.var[idx] = self._m2[idx] / max(new_count - 1.0, 1.0)

    def normalize(self, values, mask):
        values = np.asarray(values, dtype=np.float32).reshape(self.size)
        mask = np.asarray(mask, dtype=np.bool_).reshape(self.size)
        normalized = np.zeros(self.size, dtype=np.float32)
        std = np.sqrt(np.maximum(self.var, self.eps)).astype(np.float32)
        normalized[mask] = (values[mask] - self.mean.astype(np.float32)[mask]) / std[mask]
        return normalized


class ProcessOutcomeExtractor:
    """Extract masked Scenario 7 process outcomes from a closed segment."""

    field_names = PROCESS_OUTCOME_FIELDS

    def __init__(self, normalize: bool = True):
        self.normalize = bool(normalize)
        self.normalizer = MaskedRunningMeanStd(len(self.field_names))

    @property
    def num_outcomes(self) -> int:
        return len(self.field_names)

    @staticmethod
    def _scalar(value):
        if value is None:
            return None
        try:
            arr = np.asarray(value, dtype=np.float64)
        except (TypeError, ValueError):
            return None
        if arr.size == 0:
            return None
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            return None
        return float(np.mean(finite))

    def _series(self, segment, aliases):
        values = []
        for info in getattr(segment, "reward_info_seq", []):
            if not isinstance(info, dict):
                continue
            for key in aliases:
                if key in info:
                    scalar = self._scalar(info.get(key))
                    if scalar is not None:
                        values.append(scalar)
                    break
        return values

    def _delta(self, segment, aliases, sign=1.0):
        values = self._series(segment, aliases)
        if len(values) < 2:
            return 0.0, False
        return float(sign) * float(values[-1] - values[0]), True

    def _mean(self, segment, aliases, sign=1.0):
        values = self._series(segment, aliases)
        if not values:
            return 0.0, False
        return float(sign) * float(np.mean(values)), True

    def extract_raw(self, segment):
        vector = np.zeros(self.num_outcomes, dtype=np.float32)
        mask = np.zeros(self.num_outcomes, dtype=np.bool_)
        field_index = {name: idx for idx, name in enumerate(self.field_names)}

        def set_field(name, result):
            value, available = result
            idx = field_index[name]
            if available and np.isfinite(value):
                vector[idx] = float(value)
                mask[idx] = True

        set_field("delta_coverage_ratio", self._delta(segment, ("coverage_ratio",)))
        set_field(
            "delta_effective_connected_users",
            self._delta(segment, ("effective_connected_users", "connected_users", "served_users")),
        )
        set_field(
            "delta_system_throughput_mbps",
            self._delta(
                segment,
                (
                    "system_throughput_mbps",
                    "effective_end_to_end_throughput_mbps",
                    "capacity_limited_throughput_mbps",
                ),
            ),
        )
        set_field(
            "delta_qos_satisfaction",
            self._delta(
                segment,
                (
                    "qos_satisfaction_ratio",
                    "qos_met_fraction",
                    "demand_satisfaction_ratio",
                    "qos_score",
                ),
            ),
        )
        backhaul = self._delta(segment, ("min_serving_backhaul_bottleneck_mbps", "backhaul_margin"))
        if not backhaul[1]:
            backhaul = self._delta(segment, ("backhaul_margin_penalty_raw",), sign=-1.0)
        if not backhaul[1]:
            backhaul = self._delta(segment, ("backhaul_potential_reward",))
        set_field("delta_backhaul_margin", backhaul)

        energy = self._delta(segment, ("battery_min_ratio", "battery_mean_ratio"))
        if not energy[1]:
            energy = self._delta(segment, ("normalized_propulsion_energy", "energy_penalty"), sign=-1.0)
        set_field("delta_energy_ratio", energy)

        set_field(
            "delta_distance_to_nearest_charger",
            self._delta(segment, ("distance_to_nearest_charger", "nearest_charger_distance"), sign=-1.0),
        )

        charging = self._delta(segment, ("episode_energy_charged_wh", "energy_charged_wh", "step_net_energy_charged_wh"))
        if not charging[1]:
            charging = self._mean(segment, ("charging_uav_count", "effective_charging_session_count"))
        set_field("charging_progress", charging)

        pressure = self._delta(segment, ("return_constraint_cost", "return_risk_penalty"), sign=-1.0)
        if not pressure[1]:
            pressure = self._delta(segment, ("low_battery_distance_penalty", "energy_failure_penalty"), sign=-1.0)
        set_field("return_pressure_change", pressure)

        if segment.obs and segment.end_obs is not None:
            start = np.asarray(segment.obs[0], dtype=np.float32)
            end = np.asarray(segment.end_obs, dtype=np.float32)
            delta = (end - start).reshape(-1)
            set_field("fallback_obs_delta_l2", (float(np.linalg.norm(delta)), True))
            set_field("fallback_obs_delta_mean_abs", (float(np.mean(np.abs(delta))), True))

        if segment.rewards:
            set_field("fallback_reward_return", (float(np.sum(segment.rewards)), True))

        return vector, mask

    def transform(self, segment, update: bool = True):
        raw, mask = self.extract_raw(segment)
        if self.normalize and update:
            self.normalizer.update(raw, mask)
        normalized = self.normalizer.normalize(raw, mask) if self.normalize else raw.copy()
        return raw, mask, normalized

