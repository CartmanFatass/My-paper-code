"""Skill effect discovery and forcing diagnostics for HA-CTSE.

P3 Stage A tests whether skill identity improves prediction of short-horizon
effects beyond context and simple shortcuts.  It deliberately does not inject
reward unless the explicit P3 forcing-reward gate is enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ha_ctse_process.process_outcomes import MaskedRunningMeanStd


SKILL_EFFECT_FIELDS = (
    "delta_position_x",
    "delta_position_y",
    "delta_position_z",
    "delta_position_l2",
    "delta_battery",
    "delta_charging",
    "delta_local_service",
    "delta_local_access_count",
    "delta_uav_degree",
    "delta_bs_link",
    "delta_soft_topology",
    "delta_coverage_ratio",
    "delta_qos_satisfaction",
    "delta_system_throughput_mbps",
    "end_local_service",
    "end_local_access_count",
    "end_uav_degree",
    "end_bs_link",
    "end_soft_topology",
    "end_coverage_ratio",
    "end_qos_satisfaction",
    "end_system_throughput_mbps",
    "mean_local_service",
    "mean_uav_degree",
    "mean_bs_link",
    "mean_backhaul_connected_flag",
    "mean_full_disconnect",
)

MOTION_FIELDS = (0, 1, 2, 3)
ENERGY_FIELDS = (4, 5)
SERVICE_FIELDS = (6, 7, 11, 12, 13, 14, 15, 19, 20, 21, 22)
TOPOLOGY_FIELDS = (8, 9, 10, 16, 17, 18, 23, 24, 25, 26)
ENDSTATE_FIELDS = (14, 15, 16, 17, 18, 19, 20, 21)
WINDOW_MEAN_FIELDS = (22, 23, 24, 25, 26)
EFFECT_FIELD_GROUPS = (MOTION_FIELDS, ENERGY_FIELDS, SERVICE_FIELDS, TOPOLOGY_FIELDS)
FORCING_EFFECT_FIELDS = tuple(sorted(set(MOTION_FIELDS + ENERGY_FIELDS)))
SKILL_EFFECT_MAX_HORIZON_METRICS = 4
SKILL_EFFECT_HORIZON_METRIC_FIELDS = tuple(
    name
    for idx in range(SKILL_EFFECT_MAX_HORIZON_METRICS)
    for name in (
        f"effect_gain_horizon_{idx}",
        f"effect_gain_positive_frac_horizon_{idx}",
        f"effect_horizon_count_{idx}",
    )
)
SKILL_EFFECT_FIELD_GAIN_METRIC_FIELDS = tuple(
    f"effect_field_gain_{name}" for name in SKILL_EFFECT_FIELDS
)
SKILL_FORCE_METRIC_FIELDS = (
    "force_reward_low_mean",
    "force_reward_applied_steps",
    "force_disc_loss",
    "force_disc_acc",
    "force_disc_logp_mean",
    "force_disc_residual_mean",
    "force_effect_residual_mean",
    "force_shortcut_best_acc",
    "force_shortcut_best_logp_mean",
    "force_shortcut_margin",
    "force_shortcut_duration_acc",
    "force_shortcut_reward_acc",
    "force_shortcut_context_acc",
    "force_shortcut_phase_agent_acc",
    "force_gate_active",
    "force_gate_reason",
    "force_reward_unclipped_mean",
    "force_duration_entropy_bonus",
    "force_feature_dim",
)

SKILL_EFFECT_METRIC_FIELDS = (
    "effect_windows",
    "effect_loss_full",
    "effect_loss_base",
    "effect_loss_duration",
    "effect_loss_reward",
    "effect_loss_full_raw",
    "effect_loss_base_raw",
    "effect_loss_duration_raw",
    "effect_loss_reward_raw",
    "effect_gain_mean",
    "effect_gain_group_balanced_mean",
    "effect_gain_nonmotion",
    "effect_gain_positive_frac",
    "effect_gain_motion",
    "effect_gain_service",
    "effect_gain_energy",
    "effect_gain_topology",
    "effect_gain_minus_duration_baseline",
    "effect_gain_minus_reward_baseline",
    "effect_target_available_frac",
    "effect_skill_usage_entropy",
    "effect_skill_usage_max_frac",
    "effect_action_skill_eta2",
    "effect_target_skill_eta2",
    "effect_gain_skill_std",
    "effect_action_abs_mean",
    "effect_action_dim",
    "effect_observed_target_skill_l2_mean",
    "effect_observed_target_skill_l2_nonmotion",
    "effect_observed_action_skill_l2_mean",
    "effect_observed_action_target_corr",
    "effect_endstate_available_frac",
    "effect_window_mean_available_frac",
    "effect_reward_low_mean",
    "effect_reward_applied_steps",
    "effect_intervention_active",
    "effect_intervention_samples",
    "effect_intervention_action_l2_mean",
    "effect_intervention_action_l2_max",
    "effect_intervention_action_pairwise_std",
    "effect_intervention_pred_effect_l2_mean",
    "effect_intervention_pred_effect_l2_max",
    "effect_intervention_best_skill_gap",
    "effect_intervention_low_entropy_mean",
) + SKILL_FORCE_METRIC_FIELDS + SKILL_EFFECT_HORIZON_METRIC_FIELDS + SKILL_EFFECT_FIELD_GAIN_METRIC_FIELDS


def empty_skill_effect_metrics() -> dict[str, float]:
    return {name: 0.0 for name in SKILL_EFFECT_METRIC_FIELDS}


def _safe_scalar(value: Any) -> float | None:
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


def _pick_scalar(info: dict[str, Any] | None, aliases: tuple[str, ...]) -> float | None:
    if not isinstance(info, dict):
        return None
    for key in aliases:
        if key in info:
            value = _safe_scalar(info.get(key))
            if value is not None:
                return value
    return None


def _agent_array_value(info: dict[str, Any] | None, key: str, agent_id: int) -> float | None:
    if not isinstance(info, dict) or key not in info:
        return None
    try:
        arr = np.asarray(info.get(key), dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    flat = arr.reshape(-1)
    if agent_id < 0 or agent_id >= flat.size:
        return None
    value = flat[agent_id]
    if not np.isfinite(value):
        return None
    return float(value)


def _agent_position(info: dict[str, Any] | None, agent_id: int) -> np.ndarray | None:
    if not isinstance(info, dict):
        return None
    for key in ("uav_positions", "uav_position", "agent_positions"):
        if key not in info:
            continue
        try:
            arr = np.asarray(info.get(key), dtype=np.float64)
        except (TypeError, ValueError):
            continue
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2 or agent_id < 0 or agent_id >= arr.shape[0]:
            continue
        pos = arr[agent_id, : min(3, arr.shape[1])]
        if pos.size == 0 or not np.all(np.isfinite(pos)):
            continue
        out = np.zeros(3, dtype=np.float32)
        out[: pos.size] = pos.astype(np.float32)
        return out
    return None


def _row_sum(info: dict[str, Any] | None, key: str, agent_id: int) -> float | None:
    if not isinstance(info, dict) or key not in info:
        return None
    try:
        arr = np.asarray(info.get(key), dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.ndim < 2 or agent_id < 0 or agent_id >= arr.shape[0]:
        return None
    row = arr[agent_id]
    finite = row[np.isfinite(row)]
    if finite.size == 0:
        return None
    return float(np.sum(finite > 0.0))


def _local_service_count(info: dict[str, Any] | None, agent_id: int) -> float | None:
    for key in ("connections", "uav_user_connections", "user_connections"):
        value = _row_sum(info, key, agent_id)
        if value is not None:
            return value
    return None


def _soft_topology_value(info: dict[str, Any] | None, n_agents: int) -> float | None:
    if not isinstance(info, dict):
        return None
    coverage = _pick_scalar(info, ("coverage_ratio", "coverage"))
    throughput = _pick_scalar(info, ("system_throughput_mbps", "throughput_mbps", "throughput"))
    qos = _pick_scalar(info, ("qos_satisfaction", "qos_satisfaction_ratio", "qos"))
    backhaul = _pick_scalar(info, ("uavs_with_backhaul", "connected_uavs", "backhaul_connected_uavs"))
    outage = _pick_scalar(info, ("backhaul_outage_ratio", "service_drop_ratio"))
    disconnect = _pick_scalar(info, ("full_network_disconnect", "full_disconnect"))
    parts = []
    if coverage is not None:
        parts.append(float(np.clip(coverage, 0.0, 1.0)))
    if qos is not None:
        parts.append(float(np.clip(qos, 0.0, 1.0)))
    if throughput is not None:
        parts.append(float(np.tanh(max(throughput, 0.0) / 20.0)))
    if backhaul is not None:
        denom = max(float(n_agents), 1.0)
        parts.append(float(np.clip(backhaul / denom, 0.0, 1.0)))
    if outage is not None:
        parts.append(float(1.0 - np.clip(outage, 0.0, 1.0)))
    if disconnect is not None:
        parts.append(float(1.0 - np.clip(disconnect, 0.0, 1.0)))
    if not parts:
        return None
    return float(np.mean(parts))


@dataclass
class EffectWindowBatch:
    obs: np.ndarray
    action: np.ndarray
    target: np.ndarray
    mask: np.ndarray
    skill: np.ndarray
    duration: np.ndarray
    team_code: np.ndarray
    agent_id: np.ndarray
    horizon_id: np.ndarray
    phase_bin: np.ndarray
    age: np.ndarray
    reward_sum: np.ndarray
    rollout_indices: list[np.ndarray]

    @property
    def size(self) -> int:
        return int(self.skill.shape[0])


class EffectWindowExtractor:
    """Extract micro-windows from completed stochastic skill segments."""

    field_names = SKILL_EFFECT_FIELDS

    def __init__(
        self,
        obs_dim: int,
        n_agents: int,
        horizons: tuple[int, ...] = (5, 10, 20),
        stride: int = 5,
        max_windows: int = 8192,
        phase_bins: int = 8,
        normalize: bool = True,
        seed: int = 0,
    ):
        self.obs_dim = int(obs_dim)
        self.n_agents = int(max(n_agents, 1))
        self.horizons = tuple(int(h) for h in horizons if int(h) > 0) or (5, 10, 20)
        self.stride = int(max(stride, 1))
        self.max_windows = int(max(max_windows, 1))
        self.phase_bins = int(max(phase_bins, 1))
        self.normalize = bool(normalize)
        self.normalizer = MaskedRunningMeanStd(len(self.field_names))
        self.rng = np.random.default_rng(int(seed))

    @property
    def num_effects(self) -> int:
        return len(self.field_names)

    def state_dict(self) -> dict[str, Any]:
        return {
            "mean": self.normalizer.mean.astype(float).tolist(),
            "var": self.normalizer.var.astype(float).tolist(),
            "count": self.normalizer.count.astype(float).tolist(),
            "m2": self.normalizer._m2.astype(float).tolist(),
        }

    def load_state_dict(self, state: dict[str, Any] | None) -> None:
        if not isinstance(state, dict):
            return
        for key, attr in (("mean", "mean"), ("var", "var"), ("count", "count"), ("m2", "_m2")):
            if key in state:
                value = np.asarray(state[key], dtype=np.float64).reshape(-1)
                if value.size != self.num_effects:
                    continue
                setattr(self.normalizer, attr, value.copy())

    def _fit_obs(self, obs: Any) -> np.ndarray:
        vec = np.zeros(self.obs_dim, dtype=np.float32)
        try:
            arr = np.asarray(obs, dtype=np.float32).reshape(-1)
        except (TypeError, ValueError):
            return vec
        n = min(arr.size, self.obs_dim)
        if n > 0:
            vec[:n] = arr[:n]
        return vec

    def _state_at(self, segment: Any, step_idx: int) -> dict[str, Any] | None:
        if step_idx <= 0:
            start = getattr(segment, "start_state_info", None)
            if isinstance(start, dict) and start:
                return start
        seq = getattr(segment, "state_info_seq", [])
        idx = min(max(int(step_idx) - 1, 0), len(seq) - 1)
        if 0 <= idx < len(seq) and isinstance(seq[idx], dict):
            return seq[idx]
        return None

    def _reward_info_at(self, segment: Any, step_idx: int) -> dict[str, Any] | None:
        if step_idx <= 0:
            start = getattr(segment, "start_reward_info", None)
            if isinstance(start, dict) and start:
                return start
        seq = getattr(segment, "reward_info_seq", [])
        idx = min(max(int(step_idx) - 1, 0), len(seq) - 1)
        if 0 <= idx < len(seq) and isinstance(seq[idx], dict):
            return seq[idx]
        return None

    def _obs_at(self, segment: Any, step_idx: int) -> np.ndarray:
        if step_idx < len(getattr(segment, "obs", [])):
            return self._fit_obs(segment.obs[step_idx])
        if getattr(segment, "end_obs", None) is not None:
            return self._fit_obs(segment.end_obs)
        if getattr(segment, "obs", []):
            return self._fit_obs(segment.obs[-1])
        return np.zeros(self.obs_dim, dtype=np.float32)

    @staticmethod
    def _pad_vectors(rows: list[np.ndarray], indices: np.ndarray) -> np.ndarray:
        selected = [np.asarray(rows[int(i)], dtype=np.float32).reshape(-1) for i in indices]
        dim = max((row.size for row in selected), default=1)
        dim = max(int(dim), 1)
        out = np.zeros((len(selected), dim), dtype=np.float32)
        for row_idx, row in enumerate(selected):
            n = min(row.size, dim)
            if n > 0:
                out[row_idx, :n] = row[:n]
        return out

    def _action_window(self, segment: Any, start: int, end: int) -> np.ndarray:
        rows = []
        actions = getattr(segment, "actions", [])
        for idx in range(start, min(end, len(actions))):
            try:
                arr = np.asarray(actions[idx], dtype=np.float32).reshape(-1)
            except (TypeError, ValueError):
                continue
            if arr.size > 0 and np.all(np.isfinite(arr)):
                rows.append(arr)
        if not rows:
            return np.zeros(1, dtype=np.float32)
        dim = max(row.size for row in rows)
        padded = np.zeros((len(rows), dim), dtype=np.float32)
        for row_idx, row in enumerate(rows):
            padded[row_idx, : row.size] = row
        return np.mean(padded, axis=0).astype(np.float32)

    @staticmethod
    def _set_delta(vector, mask, field_to_idx, name, start_value, end_value) -> None:
        if start_value is None or end_value is None:
            return
        value = float(end_value) - float(start_value)
        if not np.isfinite(value):
            return
        idx = field_to_idx[name]
        vector[idx] = value
        mask[idx] = True

    @staticmethod
    def _set_value(vector, mask, field_to_idx, name, value) -> None:
        if value is None:
            return
        value = float(value)
        if not np.isfinite(value):
            return
        idx = field_to_idx[name]
        vector[idx] = value
        mask[idx] = True

    def _window_mean(self, segment: Any, start: int, end: int, getter) -> float | None:
        values = []
        # Use post-transition states/reward_info for the primitive steps inside the micro-window.
        for step_idx in range(int(start) + 1, int(end) + 1):
            value = getter(self._state_at(segment, step_idx), self._reward_info_at(segment, step_idx))
            if value is None:
                continue
            value = float(value)
            if np.isfinite(value):
                values.append(value)
        return float(np.mean(values)) if values else None

    def _effect_vector(self, segment: Any, start: int, end: int) -> tuple[np.ndarray, np.ndarray]:
        vector = np.zeros(self.num_effects, dtype=np.float32)
        mask = np.zeros(self.num_effects, dtype=np.bool_)
        field_to_idx = {name: idx for idx, name in enumerate(self.field_names)}
        agent_id = int(getattr(segment, "agent_id", 0))
        start_state = self._state_at(segment, start)
        end_state = self._state_at(segment, end)
        start_reward = self._reward_info_at(segment, start)
        end_reward = self._reward_info_at(segment, end)

        pos0 = _agent_position(start_state, agent_id)
        pos1 = _agent_position(end_state, agent_id)
        if pos0 is None or pos1 is None:
            obs0 = self._obs_at(segment, start)
            obs1 = self._obs_at(segment, end)
            dims = min(3, obs0.size, obs1.size)
            if dims > 0:
                pos0 = np.zeros(3, dtype=np.float32)
                pos1 = np.zeros(3, dtype=np.float32)
                pos0[:dims] = obs0[:dims]
                pos1[:dims] = obs1[:dims]
        if pos0 is not None and pos1 is not None:
            delta = np.asarray(pos1, dtype=np.float32) - np.asarray(pos0, dtype=np.float32)
            for axis, name in enumerate(("delta_position_x", "delta_position_y", "delta_position_z")):
                idx = field_to_idx[name]
                vector[idx] = float(delta[axis])
                mask[idx] = True
            idx = field_to_idx["delta_position_l2"]
            vector[idx] = float(np.linalg.norm(delta))
            mask[idx] = True

        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_battery",
            _agent_array_value(start_state, "uav_battery_ratios", agent_id),
            _agent_array_value(end_state, "uav_battery_ratios", agent_id),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_charging",
            _agent_array_value(start_state, "uav_charging", agent_id),
            _agent_array_value(end_state, "uav_charging", agent_id),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_local_service",
            _local_service_count(start_state, agent_id),
            _local_service_count(end_state, agent_id),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_local_access_count",
            _pick_scalar(start_reward, ("effective_connected_users", "connected_users", "served_users")),
            _pick_scalar(end_reward, ("effective_connected_users", "connected_users", "served_users")),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_uav_degree",
            _row_sum(start_state, "uav_connections", agent_id),
            _row_sum(end_state, "uav_connections", agent_id),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_bs_link",
            _row_sum(start_state, "uav_bs_connections", agent_id),
            _row_sum(end_state, "uav_bs_connections", agent_id),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_soft_topology",
            _soft_topology_value({**(start_reward or {}), **(start_state or {})}, self.n_agents),
            _soft_topology_value({**(end_reward or {}), **(end_state or {})}, self.n_agents),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_coverage_ratio",
            _pick_scalar(start_reward, ("coverage_ratio", "coverage")),
            _pick_scalar(end_reward, ("coverage_ratio", "coverage")),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_qos_satisfaction",
            _pick_scalar(start_reward, ("qos_satisfaction", "qos_satisfaction_ratio", "qos")),
            _pick_scalar(end_reward, ("qos_satisfaction", "qos_satisfaction_ratio", "qos")),
        )
        self._set_delta(
            vector,
            mask,
            field_to_idx,
            "delta_system_throughput_mbps",
            _pick_scalar(start_reward, ("system_throughput_mbps", "throughput_mbps", "throughput")),
            _pick_scalar(end_reward, ("system_throughput_mbps", "throughput_mbps", "throughput")),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_local_service",
            _local_service_count(end_state, agent_id),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_local_access_count",
            _pick_scalar(end_reward, ("effective_connected_users", "connected_users", "served_users")),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_uav_degree",
            _row_sum(end_state, "uav_connections", agent_id),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_bs_link",
            _row_sum(end_state, "uav_bs_connections", agent_id),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_soft_topology",
            _soft_topology_value({**(end_reward or {}), **(end_state or {})}, self.n_agents),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_coverage_ratio",
            _pick_scalar(end_reward, ("coverage_ratio", "coverage")),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_qos_satisfaction",
            _pick_scalar(end_reward, ("qos_satisfaction", "qos_satisfaction_ratio", "qos")),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "end_system_throughput_mbps",
            _pick_scalar(end_reward, ("system_throughput_mbps", "throughput_mbps", "throughput")),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "mean_local_service",
            self._window_mean(segment, start, end, lambda state, _reward: _local_service_count(state, agent_id)),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "mean_uav_degree",
            self._window_mean(segment, start, end, lambda state, _reward: _row_sum(state, "uav_connections", agent_id)),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "mean_bs_link",
            self._window_mean(segment, start, end, lambda state, _reward: _row_sum(state, "uav_bs_connections", agent_id)),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "mean_backhaul_connected_flag",
            self._window_mean(
                segment,
                start,
                end,
                lambda _state, reward: _pick_scalar(reward, ("backhaul_connected_flag", "backhaul_connected")),
            ),
        )
        self._set_value(
            vector,
            mask,
            field_to_idx,
            "mean_full_disconnect",
            self._window_mean(
                segment,
                start,
                end,
                lambda _state, reward: _pick_scalar(reward, ("full_network_disconnect", "full_disconnect")),
            ),
        )
        return vector, mask

    def extract(self, segments: list[Any], update_norm: bool = True) -> EffectWindowBatch | None:
        obs_rows: list[np.ndarray] = []
        action_rows: list[np.ndarray] = []
        target_rows: list[np.ndarray] = []
        mask_rows: list[np.ndarray] = []
        skill_rows: list[int] = []
        duration_rows: list[int] = []
        team_rows: list[int] = []
        agent_rows: list[int] = []
        horizon_rows: list[int] = []
        phase_rows: list[int] = []
        age_rows: list[float] = []
        reward_rows: list[float] = []
        rollout_rows: list[np.ndarray] = []

        for segment in segments:
            length = int(getattr(segment, "length", 0))
            if length <= 0:
                continue
            for start in range(0, length, self.stride):
                for horizon_id, horizon in enumerate(self.horizons):
                    end = start + int(horizon)
                    if end > length:
                        continue
                    raw, mask = self._effect_vector(segment, start, end)
                    if not np.any(mask):
                        continue
                    if update_norm and self.normalize:
                        self.normalizer.update(raw, mask)
                    target = self.normalizer.normalize(raw, mask) if self.normalize else raw.astype(np.float32)
                    obs_rows.append(self._obs_at(segment, start))
                    action_rows.append(self._action_window(segment, start, end))
                    target_rows.append(target)
                    mask_rows.append(mask.astype(np.float32))
                    skill_rows.append(int(getattr(segment, "skill", 0)))
                    duration_rows.append(int(getattr(segment, "duration_idx", 0)))
                    team_rows.append(int(getattr(segment, "team_code", 0)))
                    agent_rows.append(int(getattr(segment, "agent_id", 0)))
                    horizon_rows.append(int(horizon_id))
                    step = int(getattr(segment, "start_step", 0)) + int(start)
                    phase_rows.append(int(step % self.phase_bins))
                    age_rows.append(float(int(getattr(segment, "skill_age_prev", 0)) + int(start)))
                    rewards = getattr(segment, "rewards", [])[start:end]
                    reward_rows.append(float(np.sum(rewards)) if rewards else 0.0)
                    rollout_rows.append(np.asarray(getattr(segment, "rollout_indices", [])[start:end], dtype=np.int64))

        count = len(obs_rows)
        if count <= 0:
            return None
        indices = np.arange(count, dtype=np.int64)
        if count > self.max_windows:
            indices = self.rng.choice(indices, size=self.max_windows, replace=False)
            indices.sort()

        return EffectWindowBatch(
            obs=np.asarray(obs_rows, dtype=np.float32)[indices],
            action=self._pad_vectors(action_rows, indices),
            target=np.asarray(target_rows, dtype=np.float32)[indices],
            mask=np.asarray(mask_rows, dtype=np.float32)[indices],
            skill=np.asarray(skill_rows, dtype=np.int64)[indices],
            duration=np.asarray(duration_rows, dtype=np.int64)[indices],
            team_code=np.asarray(team_rows, dtype=np.int64)[indices],
            agent_id=np.asarray(agent_rows, dtype=np.int64)[indices],
            horizon_id=np.asarray(horizon_rows, dtype=np.int64)[indices],
            phase_bin=np.asarray(phase_rows, dtype=np.int64)[indices],
            age=np.asarray(age_rows, dtype=np.float32)[indices],
            reward_sum=np.asarray(reward_rows, dtype=np.float32)[indices],
            rollout_indices=[rollout_rows[int(i)] for i in indices],
        )


class _EffectPredictorBase(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        target_dim: int,
        hidden_dim: int,
        n_skills: int,
        n_agents: int,
        num_team_codes: int,
        num_durations: int,
        num_horizons: int,
        num_phase_bins: int,
        include_skill: bool,
        mode: str = "context",
    ):
        super().__init__()
        self.include_skill = bool(include_skill)
        self.mode = str(mode)
        embed_dim = max(4, min(int(hidden_dim), 32))
        self.n_skills = max(int(n_skills), 1)
        self.n_agents = max(int(n_agents), 1)
        self.num_team_codes = max(int(num_team_codes), 1)
        self.num_durations = max(int(num_durations), 1)
        self.num_horizons = max(int(num_horizons), 1)
        self.num_phase_bins = max(int(num_phase_bins), 1)
        self.skill_embed = nn.Embedding(self.n_skills, embed_dim) if include_skill else None
        self.agent_embed = nn.Embedding(self.n_agents, embed_dim)
        self.team_embed = nn.Embedding(self.num_team_codes, embed_dim)
        self.duration_embed = nn.Embedding(self.num_durations, embed_dim)
        self.horizon_embed = nn.Embedding(self.num_horizons, embed_dim)
        self.phase_embed = nn.Embedding(self.num_phase_bins, embed_dim)
        if self.mode == "context":
            input_dim = int(obs_dim) + (5 * embed_dim) + 2
            if include_skill:
                input_dim += embed_dim
        elif self.mode == "duration":
            input_dim = (2 * embed_dim) + 1
        elif self.mode == "reward":
            input_dim = embed_dim + 1
        else:
            raise ValueError(f"unknown skill-effect predictor mode: {self.mode}")
        self.net = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, target_dim),
        )

    @staticmethod
    def _idx(values: torch.Tensor, size: int) -> torch.Tensor:
        return values.long().clamp(min=0, max=max(int(size) - 1, 0))

    def forward(
        self,
        obs: torch.Tensor,
        skill: torch.Tensor,
        duration: torch.Tensor,
        team_code: torch.Tensor,
        agent_id: torch.Tensor,
        horizon_id: torch.Tensor,
        phase_bin: torch.Tensor,
        age: torch.Tensor,
        reward_sum: torch.Tensor,
    ) -> torch.Tensor:
        if self.mode == "context":
            parts = [
                obs.float(),
                self.agent_embed(self._idx(agent_id, self.n_agents)),
                self.team_embed(self._idx(team_code, self.num_team_codes)),
                self.duration_embed(self._idx(duration, self.num_durations)),
                self.horizon_embed(self._idx(horizon_id, self.num_horizons)),
                self.phase_embed(self._idx(phase_bin, self.num_phase_bins)),
                torch.log1p(age.float().clamp_min(0.0)).unsqueeze(-1),
                reward_sum.float().unsqueeze(-1),
            ]
            if self.skill_embed is not None:
                parts.append(self.skill_embed(self._idx(skill, self.n_skills)))
        elif self.mode == "duration":
            parts = [
                self.duration_embed(self._idx(duration, self.num_durations)),
                self.horizon_embed(self._idx(horizon_id, self.num_horizons)),
                torch.log1p(age.float().clamp_min(0.0)).unsqueeze(-1),
            ]
        else:
            parts = [
                self.horizon_embed(self._idx(horizon_id, self.num_horizons)),
                reward_sum.float().unsqueeze(-1),
            ]
        return self.net(torch.cat(parts, dim=-1))


class ConditionalEffectPredictor(_EffectPredictorBase):
    """Predict p_full(y_i | x_i, z_i)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, include_skill=True, mode="context", **kwargs)


class ContextBaselinePredictor(_EffectPredictorBase):
    """Predict p_base(y_i | x_i), excluding skill identity."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, include_skill=False, mode="context", **kwargs)


class ResidualSkillDiscriminator(nn.Module):
    """Predict skill from behavior/effect windows, controlling for simple context."""

    def __init__(
        self,
        feature_dim: int,
        hidden_dim: int,
        n_skills: int,
        n_agents: int,
        num_team_codes: int,
        num_durations: int,
        num_horizons: int,
        num_phase_bins: int,
        embed_dim: int = 16,
    ):
        super().__init__()
        self.n_skills = int(max(n_skills, 1))
        self.n_agents = int(max(n_agents, 1))
        self.num_team_codes = int(max(num_team_codes, 1))
        self.num_durations = int(max(num_durations, 1))
        self.num_horizons = int(max(num_horizons, 1))
        self.num_phase_bins = int(max(num_phase_bins, 1))
        self.agent_embed = nn.Embedding(self.n_agents, embed_dim)
        self.team_embed = nn.Embedding(self.num_team_codes, embed_dim)
        self.duration_embed = nn.Embedding(self.num_durations, embed_dim)
        self.horizon_embed = nn.Embedding(self.num_horizons, embed_dim)
        self.phase_embed = nn.Embedding(self.num_phase_bins, embed_dim)
        input_dim = int(feature_dim) + 5 * embed_dim + 2
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, self.n_skills),
        )

    @staticmethod
    def _idx(values: torch.Tensor, size: int) -> torch.Tensor:
        return values.long().clamp(min=0, max=max(int(size) - 1, 0))

    def forward(
        self,
        features: torch.Tensor,
        duration: torch.Tensor,
        team_code: torch.Tensor,
        agent_id: torch.Tensor,
        horizon_id: torch.Tensor,
        phase_bin: torch.Tensor,
        age: torch.Tensor,
        reward_sum: torch.Tensor,
    ) -> torch.Tensor:
        parts = [
            features.float(),
            self.agent_embed(self._idx(agent_id, self.n_agents)),
            self.team_embed(self._idx(team_code, self.num_team_codes)),
            self.duration_embed(self._idx(duration, self.num_durations)),
            self.horizon_embed(self._idx(horizon_id, self.num_horizons)),
            self.phase_embed(self._idx(phase_bin, self.num_phase_bins)),
            torch.log1p(age.float().clamp_min(0.0)).unsqueeze(-1),
            reward_sum.float().unsqueeze(-1),
        ]
        return self.net(torch.cat(parts, dim=-1))


class ShortcutSkillHeads(nn.Module):
    """Skill predictors that should not by themselves justify intrinsic reward."""

    def __init__(
        self,
        obs_dim: int,
        hidden_dim: int,
        n_skills: int,
        n_agents: int,
        num_team_codes: int,
        num_durations: int,
        num_horizons: int,
        num_phase_bins: int,
        embed_dim: int = 16,
    ):
        super().__init__()
        self.n_skills = int(max(n_skills, 1))
        self.n_agents = int(max(n_agents, 1))
        self.num_team_codes = int(max(num_team_codes, 1))
        self.num_durations = int(max(num_durations, 1))
        self.num_horizons = int(max(num_horizons, 1))
        self.num_phase_bins = int(max(num_phase_bins, 1))
        self.agent_embed = nn.Embedding(self.n_agents, embed_dim)
        self.team_embed = nn.Embedding(self.num_team_codes, embed_dim)
        self.duration_embed = nn.Embedding(self.num_durations, embed_dim)
        self.horizon_embed = nn.Embedding(self.num_horizons, embed_dim)
        self.phase_embed = nn.Embedding(self.num_phase_bins, embed_dim)

        def head(input_dim: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.SiLU(),
                nn.Linear(hidden_dim, self.n_skills),
            )

        self.duration_head = head(2 * embed_dim + 1)
        self.reward_head = head(embed_dim + 1)
        self.context_head = head(int(obs_dim) + 3 * embed_dim)
        self.phase_agent_head = head(3 * embed_dim)

    @staticmethod
    def _idx(values: torch.Tensor, size: int) -> torch.Tensor:
        return values.long().clamp(min=0, max=max(int(size) - 1, 0))

    def forward(
        self,
        obs: torch.Tensor,
        duration: torch.Tensor,
        team_code: torch.Tensor,
        agent_id: torch.Tensor,
        horizon_id: torch.Tensor,
        phase_bin: torch.Tensor,
        age: torch.Tensor,
        reward_sum: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        agent_e = self.agent_embed(self._idx(agent_id, self.n_agents))
        team_e = self.team_embed(self._idx(team_code, self.num_team_codes))
        duration_e = self.duration_embed(self._idx(duration, self.num_durations))
        horizon_e = self.horizon_embed(self._idx(horizon_id, self.num_horizons))
        phase_e = self.phase_embed(self._idx(phase_bin, self.num_phase_bins))
        log_age = torch.log1p(age.float().clamp_min(0.0)).unsqueeze(-1)
        reward = reward_sum.float().unsqueeze(-1)
        return {
            "duration": self.duration_head(torch.cat([duration_e, horizon_e, log_age], dim=-1)),
            "reward": self.reward_head(torch.cat([horizon_e, reward], dim=-1)),
            "context": self.context_head(torch.cat([obs.float(), agent_e, team_e, phase_e], dim=-1)),
            "phase_agent": self.phase_agent_head(torch.cat([agent_e, team_e, phase_e], dim=-1)),
        }


class SkillEffectIntrinsicComposer:
    """Compose bounded micro-window intrinsic rewards from residual signals."""

    def __init__(
        self,
        disc_coef: float,
        effect_coef: float,
        duration_entropy_coef: float,
        clip: float,
    ):
        self.disc_coef = float(disc_coef)
        self.effect_coef = float(effect_coef)
        self.duration_entropy_coef = float(duration_entropy_coef)
        self.clip = float(max(clip, 0.0))

    @staticmethod
    def _center(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float64).reshape(-1)
        finite = np.isfinite(arr)
        if not np.any(finite):
            return np.zeros_like(arr, dtype=np.float64)
        centered = np.zeros_like(arr, dtype=np.float64)
        centered[finite] = arr[finite] - float(np.mean(arr[finite]))
        return centered

    def compose(
        self,
        disc_residual: np.ndarray,
        effect_residual: np.ndarray,
    ) -> np.ndarray:
        reward = (
            self.disc_coef * self._center(disc_residual)
            + self.effect_coef * self._center(effect_residual)
        )
        if self.clip > 0.0:
            reward = np.clip(reward, -self.clip, self.clip)
        reward[~np.isfinite(reward)] = 0.0
        return reward.astype(np.float32)


class SkillEffectDiscoveryModule(nn.Module):
    """Train reward-off effect predictors and emit Stage-A diagnostics."""

    def __init__(
        self,
        config: Any,
        obs_dim: int,
        n_skills: int,
        n_agents: int,
        num_team_codes: int,
        num_duration_bins: int,
        device: str | torch.device,
        action_feature_dim: int = 1,
    ):
        super().__init__()
        self.enabled = bool(getattr(config, "skill_effect_discovery_on", False))
        self.reward_on = bool(getattr(config, "skill_effect_reward_on", False))
        self.force_probe_on = bool(
            getattr(config, "skill_force_probe_on", False)
            or getattr(config, "enable_skill_forcing_probe", False)
        )
        self.force_reward_on = bool(
            getattr(config, "enable_skill_forcing_reward", False)
            or getattr(config, "skill_forcing_reward_on", False)
        )
        self.force_train_on = bool(self.force_probe_on or self.force_reward_on)
        if self.force_train_on:
            self.enabled = True
        self.device = torch.device(device)
        self.group_balanced_loss = bool(getattr(config, "skill_effect_group_balanced_loss", True))
        self.intervention_enabled = bool(getattr(config, "skill_effect_intervention_probe_on", False))
        self.intervention_max_samples = int(max(getattr(config, "skill_effect_intervention_max_samples", 256), 1))
        self.force_warmup_steps = int(max(getattr(config, "skill_force_warmup_steps", 80000), 0))
        self.force_shortcut_margin = float(getattr(config, "skill_force_shortcut_margin", 0.0))
        self.force_kill_on_shortcut = bool(getattr(config, "skill_force_kill_on_shortcut", True))
        self.force_reward_injection = str(getattr(config, "skill_force_reward_injection", "low_only")).lower()
        self.force_action_dim = int(max(action_feature_dim, 1))
        self.force_effect_indices = tuple(
            int(idx)
            for idx in getattr(config, "skill_force_effect_fields", FORCING_EFFECT_FIELDS)
            if 0 <= int(idx) < len(SKILL_EFFECT_FIELDS)
        ) or FORCING_EFFECT_FIELDS
        if not bool(getattr(config, "skill_force_use_comm_fields", False)):
            forbidden = set(SERVICE_FIELDS + TOPOLOGY_FIELDS)
            self.force_effect_indices = tuple(idx for idx in self.force_effect_indices if idx not in forbidden)
            if not self.force_effect_indices:
                self.force_effect_indices = FORCING_EFFECT_FIELDS
        horizons = tuple(int(h) for h in getattr(config, "skill_effect_horizons", (5, 10, 20)))
        hidden_dim = int(getattr(config, "skill_effect_hidden_dim", 256))
        phase_bins = int(getattr(config, "intrinsic_phase_bins", 8))
        self.extractor = EffectWindowExtractor(
            obs_dim=int(obs_dim),
            n_agents=int(n_agents),
            horizons=horizons,
            stride=int(getattr(config, "skill_effect_stride", 5)),
            max_windows=int(getattr(config, "skill_effect_max_windows", 8192)),
            phase_bins=phase_bins,
            normalize=True,
            seed=int(getattr(config, "seed", 0)),
        )
        target_dim = self.extractor.num_effects
        common = dict(
            obs_dim=int(obs_dim),
            target_dim=target_dim,
            hidden_dim=hidden_dim,
            n_skills=int(n_skills),
            n_agents=int(n_agents),
            num_team_codes=int(num_team_codes),
            num_durations=int(num_duration_bins),
            num_horizons=len(self.extractor.horizons),
            num_phase_bins=phase_bins,
        )
        self.full = ConditionalEffectPredictor(**common)
        self.base = ContextBaselinePredictor(**common)
        self.duration_base = _EffectPredictorBase(**common, include_skill=False, mode="duration")
        self.reward_base = _EffectPredictorBase(**common, include_skill=False, mode="reward")
        force_feature_dim = self.force_action_dim + len(self.force_effect_indices)
        self.force_disc = ResidualSkillDiscriminator(
            feature_dim=force_feature_dim,
            hidden_dim=hidden_dim,
            n_skills=int(n_skills),
            n_agents=int(n_agents),
            num_team_codes=int(num_team_codes),
            num_durations=int(num_duration_bins),
            num_horizons=len(self.extractor.horizons),
            num_phase_bins=phase_bins,
        )
        self.force_shortcuts = ShortcutSkillHeads(
            obs_dim=int(obs_dim),
            hidden_dim=hidden_dim,
            n_skills=int(n_skills),
            n_agents=int(n_agents),
            num_team_codes=int(num_team_codes),
            num_durations=int(num_duration_bins),
            num_horizons=len(self.extractor.horizons),
            num_phase_bins=phase_bins,
        )
        self.force_composer = SkillEffectIntrinsicComposer(
            disc_coef=float(getattr(config, "skill_force_disc_coef", 0.02)),
            effect_coef=float(getattr(config, "skill_force_effect_coef", 0.0)),
            duration_entropy_coef=float(getattr(config, "skill_force_duration_entropy_coef", 0.0)),
            clip=float(getattr(config, "skill_force_clip", 0.05)),
        )
        lr = float(getattr(config, "lr_process_encoder", 1e-4))
        self.opt = torch.optim.Adam(self.parameters(), lr=lr)
        self.to(self.device)

    def get_extra_state(self) -> dict[str, Any]:
        return {"extractor": self.extractor.state_dict()}

    def set_extra_state(self, state: dict[str, Any]) -> None:
        if isinstance(state, dict):
            self.extractor.load_state_dict(state.get("extractor"))

    @staticmethod
    def _masked_mse(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return (((pred - target) ** 2) * mask).sum() / mask.sum().clamp_min(1.0)

    @staticmethod
    def _masked_group_mse(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        losses = []
        for group in EFFECT_FIELD_GROUPS:
            indices = [idx for idx in group if idx < pred.shape[-1]]
            if not indices:
                continue
            idx_tensor = torch.as_tensor(indices, dtype=torch.long, device=pred.device)
            group_mask = mask.index_select(dim=-1, index=idx_tensor)
            denom = group_mask.sum().clamp_min(1.0)
            if float(group_mask.sum().detach().cpu().item()) <= 0.0:
                continue
            group_pred = pred.index_select(dim=-1, index=idx_tensor)
            group_target = target.index_select(dim=-1, index=idx_tensor)
            losses.append((((group_pred - group_target) ** 2) * group_mask).sum() / denom)
        if not losses:
            return SkillEffectDiscoveryModule._masked_mse(pred, target, mask)
        return torch.stack(losses).mean()

    @staticmethod
    def _sample_logp(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        err = ((pred - target) ** 2) * mask
        return -0.5 * err.sum(dim=-1) / mask.sum(dim=-1).clamp_min(1.0)

    @staticmethod
    def _ce_acc_logp(logits: torch.Tensor, labels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        loss = F.cross_entropy(logits, labels)
        pred = torch.argmax(logits, dim=-1)
        acc = (pred == labels).float().mean()
        logp = F.log_softmax(logits, dim=-1).gather(1, labels.view(-1, 1)).squeeze(1)
        return loss, acc, logp

    def _fit_action_features(self, action: np.ndarray) -> np.ndarray:
        arr = np.asarray(action, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        out = np.zeros((arr.shape[0], self.force_action_dim), dtype=np.float32)
        if arr.size:
            n = min(arr.shape[1], self.force_action_dim)
            if n > 0:
                out[:, :n] = arr[:, :n]
        return out

    def _force_features(self, batch: EffectWindowBatch) -> np.ndarray:
        actions = self._fit_action_features(batch.action)
        indices = [idx for idx in self.force_effect_indices if idx < batch.target.shape[1]]
        if indices:
            effect = batch.target[:, indices].astype(np.float32, copy=True)
            mask = batch.mask[:, indices].astype(np.float32, copy=False)
            effect *= mask
        else:
            effect = np.zeros((batch.size, 0), dtype=np.float32)
        return np.concatenate([actions, effect], axis=1).astype(np.float32)

    @staticmethod
    def _group_gain(field_gain: np.ndarray, masks: np.ndarray, indices: tuple[int, ...]) -> float:
        vals = []
        for idx in indices:
            if idx >= field_gain.size:
                continue
            if np.any(masks[:, idx] > 0.0) and np.isfinite(field_gain[idx]):
                vals.append(float(field_gain[idx]))
        return float(np.mean(vals)) if vals else 0.0

    @staticmethod
    def _entropy_and_max_frac(labels: np.ndarray, size: int) -> tuple[float, float]:
        labels = np.asarray(labels, dtype=np.int64).reshape(-1)
        if labels.size <= 0 or size <= 0:
            return 0.0, 0.0
        counts = np.bincount(np.clip(labels, 0, size - 1), minlength=size).astype(np.float64)
        total = counts.sum()
        if total <= 0.0:
            return 0.0, 0.0
        probs = counts / total
        nz = probs[probs > 0.0]
        entropy = -float(np.sum(nz * np.log(nz)))
        norm_entropy = entropy / np.log(max(size, 2))
        return float(np.clip(norm_entropy, 0.0, 1.0)), float(np.max(probs))

    @staticmethod
    def _categorical_eta2(values: np.ndarray, labels: np.ndarray, mask: np.ndarray | None = None) -> float:
        values = np.asarray(values, dtype=np.float64)
        labels = np.asarray(labels, dtype=np.int64).reshape(-1)
        if values.ndim == 1:
            values = values.reshape(-1, 1)
        if values.shape[0] == 0 or labels.size != values.shape[0]:
            return 0.0
        mask_arr = None
        if mask is not None:
            mask_arr = np.asarray(mask, dtype=np.float64)
            if mask_arr.ndim == 1:
                mask_arr = mask_arr.reshape(-1, 1)
            if mask_arr.shape != values.shape:
                mask_arr = None
        out = []
        for dim in range(values.shape[1]):
            vals = values[:, dim]
            valid = np.isfinite(vals)
            if mask_arr is not None:
                valid &= mask_arr[:, dim] > 0.0
            if int(np.sum(valid)) < 2:
                continue
            vals = vals[valid]
            labs = labels[valid]
            total_ss = float(np.sum((vals - float(np.mean(vals))) ** 2))
            if total_ss <= 1e-12:
                continue
            between = 0.0
            for label in np.unique(labs):
                group_vals = vals[labs == label]
                if group_vals.size <= 0:
                    continue
                between += float(group_vals.size) * (float(np.mean(group_vals)) - float(np.mean(vals))) ** 2
            out.append(float(np.clip(between / total_ss, 0.0, 1.0)))
        return float(np.mean(out)) if out else 0.0

    @staticmethod
    def _mean_by_label_std(values: np.ndarray, labels: np.ndarray) -> float:
        values = np.asarray(values, dtype=np.float64).reshape(-1)
        labels = np.asarray(labels, dtype=np.int64).reshape(-1)
        if values.size <= 0 or values.size != labels.size:
            return 0.0
        means = []
        for label in np.unique(labels):
            group = values[(labels == label) & np.isfinite(values)]
            if group.size > 0:
                means.append(float(np.mean(group)))
        return float(np.std(means)) if len(means) >= 2 else 0.0

    @staticmethod
    def _pairwise_l2_stats(values: np.ndarray) -> tuple[float, float, float, np.ndarray]:
        arr = np.asarray(values, dtype=np.float64)
        if arr.ndim != 3 or arr.shape[0] <= 0 or arr.shape[1] < 2:
            return 0.0, 0.0, 0.0, np.zeros(0, dtype=np.float64)
        dists = []
        for left in range(arr.shape[1]):
            for right in range(left + 1, arr.shape[1]):
                diff = arr[:, left, :] - arr[:, right, :]
                dists.append(np.sqrt(np.sum(diff * diff, axis=-1)))
        if not dists:
            return 0.0, 0.0, 0.0, np.zeros(0, dtype=np.float64)
        stacked = np.stack(dists, axis=1)
        finite = stacked[np.isfinite(stacked)]
        if finite.size <= 0:
            return 0.0, 0.0, 0.0, stacked
        return float(np.mean(finite)), float(np.max(finite)), float(np.std(finite)), stacked

    @staticmethod
    def _pairwise_l2_vector(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float64)
        if arr.ndim != 2 or arr.shape[0] < 2:
            return np.zeros(0, dtype=np.float64)
        dists = []
        for left in range(arr.shape[0]):
            for right in range(left + 1, arr.shape[0]):
                diff = arr[left] - arr[right]
                val = float(np.sqrt(np.sum(diff * diff)))
                if np.isfinite(val):
                    dists.append(val)
        return np.asarray(dists, dtype=np.float64)

    @staticmethod
    def _label_centroids(
        values: np.ndarray,
        labels: np.ndarray,
        mask: np.ndarray | None = None,
        indices: tuple[int, ...] | None = None,
    ) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float64)
        labs = np.asarray(labels, dtype=np.int64).reshape(-1)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if arr.shape[0] == 0 or labs.size != arr.shape[0]:
            return np.zeros((0, 1), dtype=np.float64)
        if indices is not None:
            valid_indices = [idx for idx in indices if 0 <= int(idx) < arr.shape[1]]
            if not valid_indices:
                return np.zeros((0, 1), dtype=np.float64)
            arr = arr[:, valid_indices]
            if mask is not None:
                mask = np.asarray(mask, dtype=np.float64)
                if mask.ndim == 1:
                    mask = mask.reshape(-1, 1)
                mask = mask[:, valid_indices] if mask.shape[1] >= max(valid_indices) + 1 else None
        elif mask is not None:
            mask = np.asarray(mask, dtype=np.float64)
            if mask.ndim == 1:
                mask = mask.reshape(-1, 1)
            if mask.shape != arr.shape:
                mask = None
        centroids = []
        for label in np.unique(labs):
            rows = labs == label
            if not np.any(rows):
                continue
            vals = arr[rows]
            if mask is None:
                finite = np.isfinite(vals)
                denom = finite.sum(axis=0)
                if int(np.sum(denom > 0)) <= 0:
                    continue
                centroid = np.divide(
                    np.where(finite, vals, 0.0).sum(axis=0),
                    np.maximum(denom, 1),
                )
            else:
                m = mask[rows]
                valid = (m > 0.0) & np.isfinite(vals)
                denom = valid.sum(axis=0)
                if int(np.sum(denom > 0)) <= 0:
                    continue
                centroid = np.divide(
                    np.where(valid, vals, 0.0).sum(axis=0),
                    np.maximum(denom, 1),
                )
                centroid[denom <= 0] = 0.0
            if np.any(np.isfinite(centroid)):
                centroids.append(np.nan_to_num(centroid, nan=0.0, posinf=0.0, neginf=0.0))
        if len(centroids) < 2:
            return np.zeros((0, arr.shape[1]), dtype=np.float64)
        return np.stack(centroids, axis=0)

    @staticmethod
    def _safe_corr(left: np.ndarray, right: np.ndarray) -> float:
        a = np.asarray(left, dtype=np.float64).reshape(-1)
        b = np.asarray(right, dtype=np.float64).reshape(-1)
        valid = np.isfinite(a) & np.isfinite(b)
        if int(np.sum(valid)) < 2:
            return 0.0
        a = a[valid]
        b = b[valid]
        if float(np.std(a)) <= 1e-12 or float(np.std(b)) <= 1e-12:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    def intervention_audit(self, segments: list[Any], action_probe_fn) -> dict[str, float]:
        metrics = empty_skill_effect_metrics()
        if not self.enabled or not self.intervention_enabled or action_probe_fn is None:
            return {key: metrics[key] for key in metrics if key.startswith("effect_intervention_")}
        batch = self.extractor.extract(segments, update_norm=False)
        if batch is None or batch.size <= 0:
            return {key: metrics[key] for key in metrics if key.startswith("effect_intervention_")}

        sample_count = min(int(batch.size), self.intervention_max_samples)
        if sample_count <= 0:
            return {key: metrics[key] for key in metrics if key.startswith("effect_intervention_")}
        indices = np.arange(batch.size, dtype=np.int64)
        if batch.size > sample_count:
            indices = self.extractor.rng.choice(indices, size=sample_count, replace=False)
            indices.sort()

        obs_np = batch.obs[indices].astype(np.float32, copy=False)
        duration_np = batch.duration[indices].astype(np.int64, copy=False)
        team_np = batch.team_code[indices].astype(np.int64, copy=False)
        agent_np = batch.agent_id[indices].astype(np.int64, copy=False)
        horizon_np = batch.horizon_id[indices].astype(np.int64, copy=False)
        phase_np = batch.phase_bin[indices].astype(np.int64, copy=False)
        age_np = batch.age[indices].astype(np.float32, copy=False)
        reward_np = batch.reward_sum[indices].astype(np.float32, copy=False)
        mask_np = batch.mask[indices].astype(np.float32, copy=False)

        n_skills = int(self.full.n_skills)
        forced_skills = np.tile(np.arange(n_skills, dtype=np.int64), sample_count)
        obs_rep = np.repeat(obs_np, n_skills, axis=0)
        duration_rep = np.repeat(duration_np, n_skills, axis=0)
        team_rep = np.repeat(team_np, n_skills, axis=0)
        agent_rep = np.repeat(agent_np, n_skills, axis=0)
        horizon_rep = np.repeat(horizon_np, n_skills, axis=0)
        phase_rep = np.repeat(phase_np, n_skills, axis=0)
        age_rep = np.repeat(age_np, n_skills, axis=0)
        reward_rep = np.repeat(reward_np, n_skills, axis=0)

        action_values, entropy_values = action_probe_fn(
            obs_rep,
            forced_skills,
            team_rep,
            agent_rep,
        )
        action_arr = np.asarray(action_values, dtype=np.float64)
        if action_arr.ndim == 1:
            action_arr = action_arr.reshape(-1, 1)
        if action_arr.shape[0] != sample_count * n_skills:
            action_arr = np.zeros((sample_count * n_skills, 1), dtype=np.float64)
        action_arr = action_arr.reshape(sample_count, n_skills, -1)
        entropy_arr = np.asarray(entropy_values, dtype=np.float64).reshape(-1)
        if entropy_arr.size != sample_count * n_skills:
            entropy_arr = np.zeros(sample_count * n_skills, dtype=np.float64)

        with torch.no_grad():
            obs_t = torch.as_tensor(obs_rep, dtype=torch.float32, device=self.device)
            skill_t = torch.as_tensor(forced_skills, dtype=torch.long, device=self.device)
            duration_t = torch.as_tensor(duration_rep, dtype=torch.long, device=self.device)
            team_t = torch.as_tensor(team_rep, dtype=torch.long, device=self.device)
            agent_t = torch.as_tensor(agent_rep, dtype=torch.long, device=self.device)
            horizon_t = torch.as_tensor(horizon_rep, dtype=torch.long, device=self.device)
            phase_t = torch.as_tensor(phase_rep, dtype=torch.long, device=self.device)
            age_t = torch.as_tensor(age_rep, dtype=torch.float32, device=self.device)
            reward_t = torch.as_tensor(reward_rep, dtype=torch.float32, device=self.device)
            pred = self.full(obs_t, skill_t, duration_t, team_t, agent_t, horizon_t, phase_t, age_t, reward_t)
            pred_np = pred.detach().cpu().numpy().astype(np.float64).reshape(sample_count, n_skills, -1)

        action_mean, action_max, action_std, _action_pairwise = self._pairwise_l2_stats(action_arr)
        masked_pred = pred_np * mask_np[:, None, :]
        pred_mean, pred_max, _pred_std, _pred_pairwise = self._pairwise_l2_stats(masked_pred)
        pred_norm = np.sqrt(np.sum(masked_pred * masked_pred, axis=-1))
        best_gap = pred_norm.max(axis=1) - pred_norm.min(axis=1) if pred_norm.size else np.zeros(0)
        finite_gap = best_gap[np.isfinite(best_gap)]
        finite_entropy = entropy_arr[np.isfinite(entropy_arr)]
        return {
            "effect_intervention_active": 1.0,
            "effect_intervention_samples": float(sample_count),
            "effect_intervention_action_l2_mean": action_mean,
            "effect_intervention_action_l2_max": action_max,
            "effect_intervention_action_pairwise_std": action_std,
            "effect_intervention_pred_effect_l2_mean": pred_mean,
            "effect_intervention_pred_effect_l2_max": pred_max,
            "effect_intervention_best_skill_gap": float(np.mean(finite_gap)) if finite_gap.size else 0.0,
            "effect_intervention_low_entropy_mean": float(np.mean(finite_entropy)) if finite_entropy.size else 0.0,
        }

    def update(self, segments: list[Any], total_steps: int = 0) -> tuple[dict[str, float], dict[str, Any]]:
        metrics = empty_skill_effect_metrics()
        empty_rewards = {"rollout_indices": [], "agent_ids": np.zeros(0, dtype=np.int64), "rewards": np.zeros(0)}
        if not self.enabled:
            return metrics, empty_rewards
        batch = self.extractor.extract(segments, update_norm=True)
        if batch is None or batch.size <= 0:
            return metrics, empty_rewards

        obs = torch.as_tensor(batch.obs, dtype=torch.float32, device=self.device)
        target = torch.as_tensor(batch.target, dtype=torch.float32, device=self.device)
        mask = torch.as_tensor(batch.mask, dtype=torch.float32, device=self.device)
        skill = torch.as_tensor(batch.skill, dtype=torch.long, device=self.device)
        duration = torch.as_tensor(batch.duration, dtype=torch.long, device=self.device)
        team_code = torch.as_tensor(batch.team_code, dtype=torch.long, device=self.device)
        agent_id = torch.as_tensor(batch.agent_id, dtype=torch.long, device=self.device)
        horizon_id = torch.as_tensor(batch.horizon_id, dtype=torch.long, device=self.device)
        phase_bin = torch.as_tensor(batch.phase_bin, dtype=torch.long, device=self.device)
        age = torch.as_tensor(batch.age, dtype=torch.float32, device=self.device)
        reward_sum = torch.as_tensor(batch.reward_sum, dtype=torch.float32, device=self.device)

        pred_full = self.full(obs, skill, duration, team_code, agent_id, horizon_id, phase_bin, age, reward_sum)
        pred_base = self.base(obs, skill, duration, team_code, agent_id, horizon_id, phase_bin, age, reward_sum)
        pred_duration = self.duration_base(
            obs,
            skill,
            duration,
            team_code,
            agent_id,
            horizon_id,
            phase_bin,
            age,
            reward_sum,
        )
        pred_reward = self.reward_base(
            obs,
            skill,
            duration,
            team_code,
            agent_id,
            horizon_id,
            phase_bin,
            age,
            reward_sum,
        )

        force_features_np = self._force_features(batch)
        force_features = torch.as_tensor(force_features_np, dtype=torch.float32, device=self.device)
        force_disc_loss = torch.zeros((), dtype=torch.float32, device=self.device)
        force_shortcut_loss = torch.zeros((), dtype=torch.float32, device=self.device)
        force_disc_acc = torch.zeros((), dtype=torch.float32, device=self.device)
        force_disc_logp = torch.zeros(batch.size, dtype=torch.float32, device=self.device)
        force_shortcut_accs: dict[str, torch.Tensor] = {}
        force_shortcut_logps: dict[str, torch.Tensor] = {}
        if self.force_train_on:
            force_logits = self.force_disc(
                force_features,
                duration,
                team_code,
                agent_id,
                horizon_id,
                phase_bin,
                age,
                reward_sum,
            )
            force_disc_loss, force_disc_acc, force_disc_logp = self._ce_acc_logp(force_logits, skill)
            shortcut_logits = self.force_shortcuts(
                obs,
                duration,
                team_code,
                agent_id,
                horizon_id,
                phase_bin,
                age,
                reward_sum,
            )
            shortcut_losses = []
            for name, logits in shortcut_logits.items():
                sc_loss, sc_acc, sc_logp = self._ce_acc_logp(logits, skill)
                shortcut_losses.append(sc_loss)
                force_shortcut_accs[name] = sc_acc
                force_shortcut_logps[name] = sc_logp
            if shortcut_losses:
                force_shortcut_loss = torch.stack(shortcut_losses).mean()

        loss_full_raw = self._masked_mse(pred_full, target, mask)
        loss_base_raw = self._masked_mse(pred_base, target, mask)
        loss_duration_raw = self._masked_mse(pred_duration, target, mask)
        loss_reward_raw = self._masked_mse(pred_reward, target, mask)
        if self.group_balanced_loss:
            loss_full = self._masked_group_mse(pred_full, target, mask)
            loss_base = self._masked_group_mse(pred_base, target, mask)
            loss_duration = self._masked_group_mse(pred_duration, target, mask)
            loss_reward = self._masked_group_mse(pred_reward, target, mask)
        else:
            loss_full = loss_full_raw
            loss_base = loss_base_raw
            loss_duration = loss_duration_raw
            loss_reward = loss_reward_raw
        loss = loss_full + loss_base + 0.5 * (loss_duration + loss_reward)
        if self.force_train_on:
            loss = loss + force_disc_loss + 0.5 * force_shortcut_loss
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()

        with torch.no_grad():
            logp_full = self._sample_logp(pred_full, target, mask)
            logp_base = self._sample_logp(pred_base, target, mask)
            logp_duration = self._sample_logp(pred_duration, target, mask)
            logp_reward = self._sample_logp(pred_reward, target, mask)
            gain = logp_full - logp_base
            gain_duration = logp_full - logp_duration
            gain_reward = logp_full - logp_reward
            field_gain = (
                -0.5 * ((pred_full - target) ** 2)
                + 0.5 * ((pred_base - target) ** 2)
            ) * mask
            field_gain_np = (
                field_gain.sum(dim=0) / mask.sum(dim=0).clamp_min(1.0)
            ).detach().cpu().numpy().astype(np.float64)

        gain_np = gain.detach().cpu().numpy().astype(np.float64)
        duration_np = gain_duration.detach().cpu().numpy().astype(np.float64)
        reward_np = gain_reward.detach().cpu().numpy().astype(np.float64)
        masks_np = batch.mask.astype(np.float64)
        finite_gain = gain_np[np.isfinite(gain_np)]
        force_reward_np = np.zeros(batch.size, dtype=np.float32)
        force_disc_logp_np = np.zeros(batch.size, dtype=np.float64)
        force_shortcut_best_logp_np = np.zeros(batch.size, dtype=np.float64)
        force_disc_residual_np = np.zeros(batch.size, dtype=np.float64)
        force_shortcut_best_acc = 0.0
        force_duration_acc = 0.0
        force_reward_acc = 0.0
        force_context_acc = 0.0
        force_phase_agent_acc = 0.0
        force_disc_acc_value = 0.0
        force_disc_loss_value = 0.0
        force_gate_active = 0.0
        force_gate_reason = 4.0
        force_duration_entropy, _duration_max_frac = self._entropy_and_max_frac(
            batch.duration,
            self.force_disc.num_durations,
        )
        force_duration_entropy_bonus = self.force_composer.duration_entropy_coef * force_duration_entropy
        if self.force_train_on:
            force_disc_acc_value = float(force_disc_acc.detach().cpu().item())
            force_disc_loss_value = float(force_disc_loss.detach().cpu().item())
            force_disc_logp_np = force_disc_logp.detach().cpu().numpy().astype(np.float64)
            shortcut_logps = []
            if "duration" in force_shortcut_accs:
                force_duration_acc = float(force_shortcut_accs["duration"].detach().cpu().item())
            if "reward" in force_shortcut_accs:
                force_reward_acc = float(force_shortcut_accs["reward"].detach().cpu().item())
            if "context" in force_shortcut_accs:
                force_context_acc = float(force_shortcut_accs["context"].detach().cpu().item())
            if "phase_agent" in force_shortcut_accs:
                force_phase_agent_acc = float(force_shortcut_accs["phase_agent"].detach().cpu().item())
            for sc_logp in force_shortcut_logps.values():
                shortcut_logps.append(sc_logp.detach().cpu().numpy().astype(np.float64))
            if shortcut_logps:
                shortcut_stack = np.stack(shortcut_logps, axis=0)
                force_shortcut_best_logp_np = np.max(shortcut_stack, axis=0)
            force_shortcut_best_acc = max(
                force_duration_acc,
                force_reward_acc,
                force_context_acc,
                force_phase_agent_acc,
            )
            force_disc_residual_np = force_disc_logp_np - force_shortcut_best_logp_np
            force_margin = force_disc_acc_value - force_shortcut_best_acc
            force_gate_reason = 1.0
            if self.force_reward_on:
                force_gate_reason = 2.0
                if int(total_steps) >= self.force_warmup_steps:
                    force_gate_reason = 5.0
                    if self.force_reward_injection == "low_only":
                        force_gate_reason = 3.0
                        if (not self.force_kill_on_shortcut) or force_margin > self.force_shortcut_margin:
                            force_gate_active = 1.0
                            force_gate_reason = 0.0
                            force_reward_np = self.force_composer.compose(
                                force_disc_residual_np,
                                gain_np,
                            )
            else:
                force_margin = force_disc_acc_value - force_shortcut_best_acc
        else:
            force_margin = 0.0
        group_gain_values = [
            self._group_gain(field_gain_np, masks_np, group)
            for group in EFFECT_FIELD_GROUPS
        ]
        nonmotion_values = [
            self._group_gain(field_gain_np, masks_np, group)
            for group in (ENERGY_FIELDS, SERVICE_FIELDS, TOPOLOGY_FIELDS)
        ]
        action_centroids = self._label_centroids(batch.action, batch.skill)
        target_centroids = self._label_centroids(batch.target, batch.skill, batch.mask)
        target_nonmotion_centroids = self._label_centroids(
            batch.target,
            batch.skill,
            batch.mask,
            tuple(idx for group in (ENERGY_FIELDS, SERVICE_FIELDS, TOPOLOGY_FIELDS) for idx in group),
        )
        action_pairwise = self._pairwise_l2_vector(action_centroids)
        target_pairwise = self._pairwise_l2_vector(target_centroids)
        target_nonmotion_pairwise = self._pairwise_l2_vector(target_nonmotion_centroids)
        action_target_corr = self._safe_corr(action_pairwise, target_pairwise)
        endstate_indices = [idx for idx in ENDSTATE_FIELDS if idx < masks_np.shape[1]]
        window_indices = [idx for idx in WINDOW_MEAN_FIELDS if idx < masks_np.shape[1]]
        endstate_available = (
            float(np.mean(masks_np[:, endstate_indices] > 0.0)) if endstate_indices and masks_np.size else 0.0
        )
        window_available = (
            float(np.mean(masks_np[:, window_indices] > 0.0)) if window_indices and masks_np.size else 0.0
        )
        skill_entropy, skill_max_frac = self._entropy_and_max_frac(batch.skill, self.full.n_skills)
        metrics.update(
            {
                "effect_windows": float(batch.size),
                "effect_loss_full": float(loss_full.detach().cpu().item()),
                "effect_loss_base": float(loss_base.detach().cpu().item()),
                "effect_loss_duration": float(loss_duration.detach().cpu().item()),
                "effect_loss_reward": float(loss_reward.detach().cpu().item()),
                "effect_loss_full_raw": float(loss_full_raw.detach().cpu().item()),
                "effect_loss_base_raw": float(loss_base_raw.detach().cpu().item()),
                "effect_loss_duration_raw": float(loss_duration_raw.detach().cpu().item()),
                "effect_loss_reward_raw": float(loss_reward_raw.detach().cpu().item()),
                "effect_gain_mean": float(np.mean(finite_gain)) if finite_gain.size else 0.0,
                "effect_gain_group_balanced_mean": float(np.mean(group_gain_values)) if group_gain_values else 0.0,
                "effect_gain_nonmotion": float(np.mean(nonmotion_values)) if nonmotion_values else 0.0,
                "effect_gain_positive_frac": float(np.mean(finite_gain > 0.0)) if finite_gain.size else 0.0,
                "effect_gain_motion": self._group_gain(field_gain_np, masks_np, MOTION_FIELDS),
                "effect_gain_service": self._group_gain(field_gain_np, masks_np, SERVICE_FIELDS),
                "effect_gain_energy": self._group_gain(field_gain_np, masks_np, ENERGY_FIELDS),
                "effect_gain_topology": self._group_gain(field_gain_np, masks_np, TOPOLOGY_FIELDS),
                "effect_gain_minus_duration_baseline": float(np.mean(duration_np[np.isfinite(duration_np)]))
                if np.any(np.isfinite(duration_np))
                else 0.0,
                "effect_gain_minus_reward_baseline": float(np.mean(reward_np[np.isfinite(reward_np)]))
                if np.any(np.isfinite(reward_np))
                else 0.0,
                "effect_target_available_frac": float(np.mean(masks_np > 0.0)) if masks_np.size else 0.0,
                "effect_skill_usage_entropy": skill_entropy,
                "effect_skill_usage_max_frac": skill_max_frac,
                "effect_action_skill_eta2": self._categorical_eta2(batch.action, batch.skill),
                "effect_target_skill_eta2": self._categorical_eta2(batch.target, batch.skill, batch.mask),
                "effect_gain_skill_std": self._mean_by_label_std(gain_np, batch.skill),
                "effect_action_abs_mean": float(np.mean(np.abs(batch.action))) if batch.action.size else 0.0,
                "effect_action_dim": float(batch.action.shape[1]) if batch.action.ndim == 2 else 0.0,
                "effect_observed_target_skill_l2_mean": float(np.mean(target_pairwise))
                if target_pairwise.size
                else 0.0,
                "effect_observed_target_skill_l2_nonmotion": float(np.mean(target_nonmotion_pairwise))
                if target_nonmotion_pairwise.size
                else 0.0,
                "effect_observed_action_skill_l2_mean": float(np.mean(action_pairwise))
                if action_pairwise.size
                else 0.0,
                "effect_observed_action_target_corr": action_target_corr,
                "effect_endstate_available_frac": endstate_available,
                "effect_window_mean_available_frac": window_available,
                # Stage A is reward-off by contract.
                "effect_reward_low_mean": 0.0,
                "effect_reward_applied_steps": 0.0,
                "force_reward_low_mean": float(np.mean(force_reward_np)) if force_reward_np.size else 0.0,
                "force_reward_applied_steps": float(
                    sum(len(row) for row, value in zip(batch.rollout_indices, force_reward_np) if abs(float(value)) > 0.0)
                )
                if force_gate_active > 0.0
                else 0.0,
                "force_disc_loss": force_disc_loss_value,
                "force_disc_acc": force_disc_acc_value,
                "force_disc_logp_mean": float(np.mean(force_disc_logp_np))
                if force_disc_logp_np.size
                else 0.0,
                "force_disc_residual_mean": float(np.mean(force_disc_residual_np))
                if force_disc_residual_np.size
                else 0.0,
                "force_effect_residual_mean": float(np.mean(finite_gain)) if finite_gain.size else 0.0,
                "force_shortcut_best_acc": force_shortcut_best_acc,
                "force_shortcut_best_logp_mean": float(np.mean(force_shortcut_best_logp_np))
                if force_shortcut_best_logp_np.size
                else 0.0,
                "force_shortcut_margin": float(force_margin),
                "force_shortcut_duration_acc": force_duration_acc,
                "force_shortcut_reward_acc": force_reward_acc,
                "force_shortcut_context_acc": force_context_acc,
                "force_shortcut_phase_agent_acc": force_phase_agent_acc,
                "force_gate_active": force_gate_active,
                "force_gate_reason": force_gate_reason,
                "force_reward_unclipped_mean": float(
                    np.mean(
                        self.force_composer.disc_coef
                        * SkillEffectIntrinsicComposer._center(force_disc_residual_np)
                        + self.force_composer.effect_coef
                        * SkillEffectIntrinsicComposer._center(gain_np)
                    )
                )
                if self.force_train_on and gain_np.size
                else 0.0,
                "force_duration_entropy_bonus": float(force_duration_entropy_bonus),
                "force_feature_dim": float(force_features_np.shape[1]) if force_features_np.ndim == 2 else 0.0,
            }
        )
        for idx in range(SKILL_EFFECT_MAX_HORIZON_METRICS):
            horizon_mask = batch.horizon_id == idx
            horizon_gain = gain_np[horizon_mask & np.isfinite(gain_np)]
            metrics[f"effect_horizon_count_{idx}"] = float(horizon_gain.size)
            metrics[f"effect_gain_horizon_{idx}"] = float(np.mean(horizon_gain)) if horizon_gain.size else 0.0
            metrics[f"effect_gain_positive_frac_horizon_{idx}"] = (
                float(np.mean(horizon_gain > 0.0)) if horizon_gain.size else 0.0
            )
        for idx, field_name in enumerate(SKILL_EFFECT_FIELDS):
            metric_name = f"effect_field_gain_{field_name}"
            metrics[metric_name] = float(field_gain_np[idx]) if idx < field_gain_np.size else 0.0
        if force_gate_active > 0.0:
            rewards = {
                "rollout_indices": batch.rollout_indices,
                "agent_ids": np.asarray(batch.agent_id, dtype=np.int64),
                "rewards": force_reward_np.astype(np.float32),
            }
            return metrics, rewards
        return metrics, empty_rewards
