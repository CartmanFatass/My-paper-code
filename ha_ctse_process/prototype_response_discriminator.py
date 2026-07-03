"""Prototype-response skill discriminator for HA-CTSE R14.

This module is deliberately separate from the older transition-skill
discriminator.  It estimates whether the active prototype-response skill
changes primitive next-observation distributions after conditioning on the
recognized situation substrate.  The prior head is conditioned only on the
situation inputs, never on next observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F


PROTOTYPE_DISC_METRIC_FIELDS = (
    "proto_disc_active",
    "proto_disc_samples",
    "proto_disc_loss",
    "proto_disc_q_loss",
    "proto_disc_prior_loss",
    "proto_disc_acc",
    "proto_disc_prior_acc",
    "proto_disc_residual_mean",
    "proto_disc_residual_positive_frac",
    "proto_disc_acc_by_skill_std",
    "proto_disc_reward_mean",
    "proto_disc_reward_unclipped_mean",
    "proto_disc_reward_applied_steps",
    "proto_disc_reward_env_ratio",
)


def empty_prototype_disc_metrics() -> dict[str, float]:
    return {key: 0.0 for key in PROTOTYPE_DISC_METRIC_FIELDS}


@dataclass(frozen=True)
class PrototypeDiscConfig:
    obs_dim: int
    n_skills: int
    condition_dim: int
    hidden_dim: int = 128
    prior_coef: float = 1.0


class PrototypeResponseDiscriminator(nn.Module):
    """Per-step q(z | o_next, cond) with p(z | cond) baseline prior."""

    def __init__(
        self,
        obs_dim: int,
        n_skills: int,
        condition_dim: int,
        hidden_dim: int = 128,
        prior_coef: float = 1.0,
    ):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_skills = int(max(n_skills, 1))
        self.condition_dim = int(max(condition_dim, 0))
        self.prior_input_dim = max(self.condition_dim, 1)
        self.prior_coef = float(prior_coef)
        self.q_head = nn.Sequential(
            nn.LayerNorm(self.obs_dim + self.condition_dim),
            nn.Linear(self.obs_dim + self.condition_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, self.n_skills),
        )
        self.prior_head = nn.Sequential(
            nn.LayerNorm(self.prior_input_dim),
            nn.Linear(self.prior_input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, self.n_skills),
        )

    def _prior_input(self, condition: torch.Tensor) -> torch.Tensor:
        if self.condition_dim <= 0:
            return torch.zeros(
                int(condition.shape[0]),
                1,
                dtype=condition.dtype,
                device=condition.device,
            )
        return condition.float()

    def forward(self, next_obs: torch.Tensor, condition: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        next_obs = next_obs.float()
        if self.condition_dim > 0:
            condition = condition.float()
            q_input = torch.cat([next_obs, condition], dim=-1)
        else:
            condition = torch.zeros(next_obs.shape[0], 0, dtype=next_obs.dtype, device=next_obs.device)
            q_input = next_obs
        return self.q_head(q_input), self.prior_head(self._prior_input(condition))

    @staticmethod
    def _accuracy(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        if labels.numel() == 0:
            return torch.zeros((), device=logits.device, dtype=logits.dtype)
        return (torch.argmax(logits, dim=-1) == labels.long()).float().mean()

    @staticmethod
    def _acc_by_skill_std(logits: torch.Tensor, labels: torch.Tensor, n_skills: int) -> torch.Tensor:
        if labels.numel() == 0:
            return torch.zeros((), device=logits.device, dtype=logits.dtype)
        preds = torch.argmax(logits, dim=-1)
        values = []
        for skill_id in range(int(max(n_skills, 1))):
            mask = labels.long() == int(skill_id)
            if bool(mask.any()):
                values.append((preds[mask] == labels.long()[mask]).float().mean())
        if len(values) <= 1:
            return torch.zeros((), device=logits.device, dtype=logits.dtype)
        return torch.std(torch.stack(values), unbiased=False)

    def loss_and_metrics(
        self,
        next_obs: torch.Tensor,
        condition: torch.Tensor,
        labels: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        q_logits, prior_logits = self.forward(next_obs, condition)
        labels = labels.long().clamp(0, self.n_skills - 1)
        q_loss = F.cross_entropy(q_logits, labels)
        prior_loss = F.cross_entropy(prior_logits, labels)
        total_loss = q_loss + float(self.prior_coef) * prior_loss
        q_logp = F.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        prior_logp = F.log_softmax(prior_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        residual = q_logp - prior_logp

        def scalar(value: torch.Tensor) -> float:
            return float(value.detach().cpu().item())

        metrics = empty_prototype_disc_metrics()
        metrics.update(
            {
                "proto_disc_active": 1.0,
                "proto_disc_samples": float(labels.numel()),
                "proto_disc_loss": scalar(total_loss),
                "proto_disc_q_loss": scalar(q_loss),
                "proto_disc_prior_loss": scalar(prior_loss),
                "proto_disc_acc": scalar(self._accuracy(q_logits, labels)),
                "proto_disc_prior_acc": scalar(self._accuracy(prior_logits, labels)),
                "proto_disc_residual_mean": scalar(residual.mean()),
                "proto_disc_residual_positive_frac": scalar((residual > 0.0).float().mean()),
                "proto_disc_acc_by_skill_std": scalar(self._acc_by_skill_std(q_logits, labels, self.n_skills)),
            }
        )
        return total_loss, metrics

    @torch.no_grad()
    def residual_reward(
        self,
        next_obs: torch.Tensor,
        condition: torch.Tensor,
        labels: torch.Tensor,
        *,
        clip: float = 2.0,
    ) -> torch.Tensor:
        q_logits, prior_logits = self.forward(next_obs, condition)
        labels = labels.long().clamp(0, self.n_skills - 1)
        q_logp = F.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        prior_logp = F.log_softmax(prior_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        reward = q_logp - prior_logp
        if float(clip) > 0.0:
            reward = reward.clamp(-float(clip), float(clip))
        return reward


def prototype_disc_config_from_agent(agent: Any) -> PrototypeDiscConfig:
    """Small helper used by tests and checkpoint diagnostics."""

    return PrototypeDiscConfig(
        obs_dim=int(agent.obs_dim),
        n_skills=int(agent.n_skills),
        condition_dim=int(getattr(agent, "prototype_disc_condition_dim", 0)),
        hidden_dim=int(getattr(agent, "prototype_disc_hidden_dim", 128)),
        prior_coef=float(getattr(agent, "prototype_disc_prior_coef", 1.0)),
    )
