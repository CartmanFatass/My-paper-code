"""Reward-off team-conditioned q_d probe for HA-CTSE R24.

The probe asks whether the local effect of an executed individual skill carries
recoverable skill-label information beyond the current team/assignment context:

    q_full(z_i | local_effect_i, Z, xi, c, omega)
    q_prior(z_i | Z, xi, c, omega)

It owns only diagnostic classifiers. Inputs are detached so this module cannot
become a reward or policy-gradient path by accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F


TEAM_CONDITIONED_QD_METRIC_FIELDS = (
    "r24_qd_active",
    "r24_qd_samples",
    "r24_qd_loss_full",
    "r24_qd_loss_prior",
    "r24_qd_acc_full",
    "r24_qd_acc_prior",
    "r24_qd_residual_gain",
    "r24_qd_residual_mean",
    "r24_qd_positive_frac",
)


def empty_team_conditioned_qd_metrics() -> dict[str, float]:
    return {key: 0.0 for key in TEAM_CONDITIONED_QD_METRIC_FIELDS}


@dataclass(frozen=True)
class TeamConditionedQDConfig:
    probe_on: bool = False
    hidden_dim: int = 128
    lr: float = 1e-3
    min_samples: int = 64

    @classmethod
    def from_config(cls, config: Any) -> "TeamConditionedQDConfig":
        probe_on = bool(
            getattr(config, "enable_team_conditioned_qd_probe", False)
            or getattr(config, "enable_r24_team_conditioned_qd_probe", False)
        )
        hidden_dim = int(
            max(
                getattr(
                    config,
                    "team_conditioned_qd_hidden_dim",
                    getattr(config, "r24_qd_hidden_dim", 128),
                ),
                1,
            )
        )
        min_samples = int(
            max(
                getattr(
                    config,
                    "team_conditioned_qd_min_samples",
                    getattr(config, "r24_qd_min_samples", 64),
                ),
                1,
            )
        )
        lr = float(getattr(config, "team_conditioned_qd_lr", getattr(config, "r24_qd_lr", 1e-3)))
        return cls(probe_on=probe_on, hidden_dim=hidden_dim, lr=lr, min_samples=min_samples)


def _mlp(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(input_dim),
        nn.Linear(input_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, output_dim),
    )


class TeamConditionedQDProbe(nn.Module):
    """q_d_full(z_i | effect, condition) vs q_d_prior(z_i | condition)."""

    def __init__(self, effect_dim: int, condition_dim: int, num_skills: int, hidden_dim: int = 128):
        super().__init__()
        self.effect_dim = int(max(effect_dim, 0))
        self.condition_dim = int(max(condition_dim, 0))
        self.num_skills = int(max(num_skills, 1))
        hidden = int(max(hidden_dim, 1))
        self._effect_eff = int(max(self.effect_dim, 1))
        self._condition_eff = int(max(self.condition_dim, 1))
        self.q_full = _mlp(self._effect_eff + self._condition_eff, hidden, self.num_skills)
        self.q_prior = _mlp(self._condition_eff, hidden, self.num_skills)

    @staticmethod
    def _as_rows(values: torch.Tensor, name: str) -> torch.Tensor:
        if not isinstance(values, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        values = values.detach().float()
        if values.dim() == 1:
            values = values.unsqueeze(0)
        if values.dim() != 2:
            raise ValueError(f"{name} must be a 2D tensor")
        return values

    @staticmethod
    def _pad_zero_width(values: torch.Tensor, effective_dim: int) -> torch.Tensor:
        return torch.zeros(values.shape[0], effective_dim, device=values.device, dtype=values.dtype)

    def _prep(self, effect: torch.Tensor, condition: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        effect = self._as_rows(effect, "effect")
        condition = self._as_rows(condition, "condition")
        if effect.shape[0] != condition.shape[0]:
            raise ValueError("effect and condition batch sizes must match")

        if self.effect_dim == 0:
            effect = self._pad_zero_width(effect, self._effect_eff)
        elif effect.shape[-1] != self.effect_dim:
            raise ValueError(f"effect_dim mismatch: expected {self.effect_dim}, got {effect.shape[-1]}")

        if self.condition_dim == 0:
            condition = self._pad_zero_width(condition, self._condition_eff)
        elif condition.shape[-1] != self.condition_dim:
            raise ValueError(f"condition_dim mismatch: expected {self.condition_dim}, got {condition.shape[-1]}")

        return effect, condition

    def _logits(self, effect: torch.Tensor, condition: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        effect, condition = self._prep(effect, condition)
        full = self.q_full(torch.cat([effect, condition], dim=-1))
        prior = self.q_prior(condition)
        return full, prior

    def losses(
        self,
        effect: torch.Tensor,
        condition: torch.Tensor,
        labels: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        full, prior = self._logits(effect, condition)
        labels = labels.detach().long().reshape(-1).clamp(0, self.num_skills - 1).to(device=full.device)
        if labels.shape[0] != full.shape[0]:
            raise ValueError("labels batch size must match effect and condition")

        loss_full = F.cross_entropy(full, labels)
        loss_prior = F.cross_entropy(prior, labels)
        row = torch.arange(labels.shape[0], device=full.device)
        log_q_full = F.log_softmax(full, dim=-1)[row, labels]
        log_q_prior = F.log_softmax(prior, dim=-1)[row, labels]
        residual = log_q_full - log_q_prior
        acc_full = (full.argmax(dim=-1) == labels).float().mean()
        acc_prior = (prior.argmax(dim=-1) == labels).float().mean()
        return {
            "loss_full": loss_full,
            "loss_prior": loss_prior,
            "loss": loss_full + loss_prior,
            "logits_full": full,
            "logits_prior": prior,
            "log_q_full": log_q_full,
            "log_q_prior": log_q_prior,
            "residual": residual,
            "residual_mean": residual.mean(),
            "positive_frac": (residual > 0.0).float().mean(),
            "acc_full": acc_full,
            "acc_prior": acc_prior,
            "residual_gain": acc_full - acc_prior,
        }
