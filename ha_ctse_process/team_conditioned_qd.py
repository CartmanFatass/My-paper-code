"""R24 team-conditioned individual q_d reward-off probe.

Question: does local effect recover executed individual skill ``z_i`` beyond a
condition-only prior that already sees ``(Z, xi, c, omega)``? This is the
individual discoverer bridge after ``q_A`` established ``Z -> xi``. It is
diagnostic-only.
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
    return {k: 0.0 for k in TEAM_CONDITIONED_QD_METRIC_FIELDS}


@dataclass(frozen=True)
class TeamConditionedQDConfig:
    probe_on: bool = False
    hidden_dim: int = 128
    lr: float = 1e-3
    min_samples: int = 64

    @classmethod
    def from_config(cls, config: Any) -> "TeamConditionedQDConfig":
        return cls(
            probe_on=bool(getattr(config, "enable_team_conditioned_qd_probe", False)),
            hidden_dim=int(max(getattr(config, "team_conditioned_qd_hidden_dim", 128), 1)),
            lr=float(getattr(config, "team_conditioned_qd_lr", 1e-3)),
            min_samples=int(max(getattr(config, "team_conditioned_qd_min_samples", 64), 1)),
        )


def _mlp(in_dim: int, hidden_dim: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(in_dim),
        nn.Linear(in_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, out_dim),
    )


class TeamConditionedQDProbe(nn.Module):
    """Small residual probe for individual skill recoverability."""

    def __init__(self, effect_dim: int, cond_dim: int, num_skills: int, hidden_dim: int = 128):
        super().__init__()
        self.effect_dim = int(max(effect_dim, 1))
        self.cond_dim = int(max(cond_dim, 1))
        self.num_skills = int(max(num_skills, 1))
        hidden = int(max(hidden_dim, 1))
        self.q_full = _mlp(self.effect_dim + self.cond_dim, hidden, self.num_skills)
        self.q_prior = _mlp(self.cond_dim, hidden, self.num_skills)

    def _prep(self, effect: torch.Tensor, condition: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        effect = effect.detach().to(dtype=torch.float32)
        condition = condition.detach().to(dtype=torch.float32)
        if effect.dim() == 1:
            effect = effect.unsqueeze(0)
        if condition.dim() == 1:
            condition = condition.unsqueeze(0)
        return effect, condition

    def losses(self, effect: torch.Tensor, condition: torch.Tensor, labels: torch.Tensor) -> dict[str, torch.Tensor]:
        effect, condition = self._prep(effect, condition)
        labels = labels.detach().to(dtype=torch.long).clamp(0, self.num_skills - 1)
        full_logits = self.q_full(torch.cat([effect, condition], dim=-1))
        prior_logits = self.q_prior(condition)
        loss_full = F.cross_entropy(full_logits, labels)
        loss_prior = F.cross_entropy(prior_logits, labels)

        row = torch.arange(labels.shape[0], device=labels.device)
        log_full = F.log_softmax(full_logits, dim=-1)[row, labels]
        log_prior = F.log_softmax(prior_logits, dim=-1)[row, labels]
        residual = log_full - log_prior

        acc_full = (full_logits.argmax(dim=-1) == labels).float().mean()
        acc_prior = (prior_logits.argmax(dim=-1) == labels).float().mean()
        return {
            "loss_full": loss_full,
            "loss_prior": loss_prior,
            "acc_full": acc_full,
            "acc_prior": acc_prior,
            "residual": residual,
            "residual_gain": acc_full - acc_prior,
            "residual_mean": residual.mean(),
            "positive_frac": (residual > 0).float().mean(),
        }
