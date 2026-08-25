"""Future cooperation outcome residual probes for HA-CTSE.

This module tests whether a realized skill segment carries incremental
predictive information about future cooperation outcomes beyond context,
duration, phase, agent id, and reward shortcuts.  It is intentionally a probe
first; reward injection is controlled separately by the trainer.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ha_ctse_process.process_outcomes import MaskedRunningMeanStd


FUTURE_COOPERATION_OUTCOME_FIELDS = (
    "coverage_delta_h",
    "qos_delta_h",
    "full_disconnect_improvement_h",
    "relay_margin_delta_h",
    "connected_components_improvement_h",
    "teammate_service_gain_h",
    "bottleneck_link_gain_h",
)


def _mlp(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.Tanh(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.Tanh(),
        nn.Linear(hidden_dim, output_dim),
    )


class FutureCooperationOutcomeExtractor:
    """Build masked H-step cooperation outcome deltas from reward_info_seq."""

    field_names = FUTURE_COOPERATION_OUTCOME_FIELDS

    def __init__(self, horizon_steps: int = 50, normalize: bool = True):
        self.horizon_steps = int(max(horizon_steps, 1))
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

    def _series(self, segment, aliases) -> list[float]:
        values: list[float] = []
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

    def _delta_h(self, segment, aliases, sign: float = 1.0) -> tuple[float, bool]:
        values = self._series(segment, aliases)
        if len(values) < 2:
            return 0.0, False
        end_idx = min(self.horizon_steps - 1, len(values) - 1)
        return float(sign) * float(values[end_idx] - values[0]), True

    def extract_raw(self, segment) -> tuple[np.ndarray, np.ndarray]:
        vector = np.zeros(self.num_outcomes, dtype=np.float32)
        mask = np.zeros(self.num_outcomes, dtype=np.bool_)
        field_index = {name: idx for idx, name in enumerate(self.field_names)}

        def set_field(name: str, result: tuple[float, bool]) -> None:
            value, available = result
            idx = field_index[name]
            if available and np.isfinite(value):
                vector[idx] = float(value)
                mask[idx] = True

        set_field("coverage_delta_h", self._delta_h(segment, ("coverage_ratio",)))
        set_field(
            "qos_delta_h",
            self._delta_h(
                segment,
                (
                    "qos_satisfaction_ratio",
                    "qos_met_fraction",
                    "demand_satisfaction_ratio",
                    "qos_satisfaction",
                    "qos_score",
                ),
            ),
        )
        set_field(
            "full_disconnect_improvement_h",
            self._delta_h(
                segment,
                (
                    "full_network_disconnect",
                    "network_fully_disconnected",
                    "is_fully_disconnected",
                    "full_disconnect",
                ),
                sign=-1.0,
            ),
        )

        relay_margin = self._delta_h(
            segment,
            (
                "min_serving_backhaul_bottleneck_mbps",
                "avg_serving_backhaul_bottleneck_mbps",
                "backhaul_margin",
            ),
        )
        if not relay_margin[1]:
            relay_margin = self._delta_h(segment, ("backhaul_margin_penalty_raw",), sign=-1.0)
        set_field("relay_margin_delta_h", relay_margin)

        components = self._delta_h(
            segment,
            ("connected_components", "num_connected_components", "network_connected_components"),
            sign=-1.0,
        )
        if not components[1]:
            components = self._delta_h(segment, ("uavs_with_backhaul", "connected_uavs", "backhaul_connected_uavs"))
        set_field("connected_components_improvement_h", components)

        set_field(
            "teammate_service_gain_h",
            self._delta_h(
                segment,
                (
                    "current_backhaul_served_users",
                    "effective_connected_users",
                    "connected_users",
                    "served_users",
                ),
            ),
        )

        bottleneck = self._delta_h(
            segment,
            (
                "min_serving_backhaul_bottleneck_mbps",
                "avg_serving_backhaul_bottleneck_mbps",
                "serving_backhaul_bottleneck_mbps",
            ),
        )
        if not bottleneck[1]:
            bottleneck = relay_margin
        set_field("bottleneck_link_gain_h", bottleneck)
        return vector, mask

    def transform(self, segment, update: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        raw, mask = self.extract_raw(segment)
        if self.normalize and update:
            self.normalizer.update(raw, mask)
        normalized = self.normalizer.normalize(raw, mask) if self.normalize else raw.copy()
        return raw, mask, normalized


class OutcomeResidualProbe(nn.Module):
    """Full-vs-baseline future outcome residual predictor."""

    def __init__(
        self,
        embedding_dim: int,
        obs_dim: int,
        n_skills: int,
        num_team_codes: int,
        n_agents: int,
        num_phase_bins: int,
        num_duration_bins: int,
        outcome_dim: int,
        hidden_dim: int,
    ):
        super().__init__()
        self.n_skills = int(max(n_skills, 1))
        self.num_team_codes = int(max(num_team_codes, 1))
        self.n_agents = int(max(n_agents, 1))
        self.num_phase_bins = int(max(num_phase_bins, 1))
        self.num_duration_bins = int(max(num_duration_bins, 1))
        self.outcome_dim = int(outcome_dim)

        self.baseline_dim = (
            int(obs_dim)
            + self.num_team_codes
            + self.n_agents
            + self.num_phase_bins
            + self.num_duration_bins
            + 2
        )
        full_dim = int(embedding_dim) + self.n_skills + self.baseline_dim
        self.full_predictor = _mlp(full_dim, hidden_dim, self.outcome_dim)
        self.baseline_predictor = _mlp(self.baseline_dim, hidden_dim, self.outcome_dim)

    @staticmethod
    def _batch_standardize(values: torch.Tensor) -> torch.Tensor:
        values = values.float().reshape(-1, 1)
        if values.numel() <= 1:
            return torch.zeros_like(values)
        return (values - values.mean()) / values.std(unbiased=False).clamp_min(1e-6)

    def baseline_features(
        self,
        start_obs: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
        phase_bins: torch.Tensor,
        durations: torch.Tensor,
        lengths: torch.Tensor,
        reward_sums: torch.Tensor,
    ) -> torch.Tensor:
        team = F.one_hot(team_codes.long().clamp(0, self.num_team_codes - 1), self.num_team_codes).float()
        agent = F.one_hot(agent_ids.long().clamp(0, self.n_agents - 1), self.n_agents).float()
        phase = F.one_hot(phase_bins.long().clamp(0, self.num_phase_bins - 1), self.num_phase_bins).float()
        duration = F.one_hot(durations.long().clamp(0, self.num_duration_bins - 1), self.num_duration_bins).float()
        return torch.cat(
            [
                start_obs.float(),
                team,
                agent,
                phase,
                duration,
                self._batch_standardize(lengths),
                self._batch_standardize(reward_sums),
            ],
            dim=-1,
        )

    def forward(
        self,
        emb: torch.Tensor,
        labels: torch.Tensor,
        start_obs: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
        phase_bins: torch.Tensor,
        durations: torch.Tensor,
        lengths: torch.Tensor,
        reward_sums: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        baseline = self.baseline_features(
            start_obs,
            team_codes,
            agent_ids,
            phase_bins,
            durations,
            lengths,
            reward_sums,
        )
        skill = F.one_hot(labels.long().clamp(0, self.n_skills - 1), self.n_skills).float()
        full = torch.cat([emb.float(), skill, baseline], dim=-1)
        return self.full_predictor(full), self.baseline_predictor(baseline)

    def losses(
        self,
        full_pred: torch.Tensor,
        baseline_pred: torch.Tensor,
        targets: torch.Tensor,
        masks: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        masks = masks.float()
        full_sq = torch.square(full_pred - targets.float()) * masks
        base_sq = torch.square(baseline_pred - targets.float()) * masks
        denom = masks.sum().clamp_min(1.0)
        per_sample_denom = masks.sum(dim=-1).clamp_min(1.0)
        full_err = full_sq.sum(dim=-1) / per_sample_denom
        base_err = base_sq.sum(dim=-1) / per_sample_denom
        gain = base_err - full_err
        field_gain = (base_sq - full_sq).sum(dim=0) / masks.sum(dim=0).clamp_min(1.0)
        return {
            "full_loss": full_sq.sum() / denom,
            "baseline_loss": base_sq.sum() / denom,
            "gain": gain,
            "field_gain": field_gain,
            "available": (masks.sum(dim=-1) > 0.0).float(),
        }
