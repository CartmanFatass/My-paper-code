"""Prototype-response skill discriminator for HA-CTSE R14/R15.

This module is deliberately separate from the older transition-skill
discriminator.  It estimates whether the active prototype-response skill
changes primitive next-observation distributions after conditioning on the
recognized situation substrate.  The R15 default residual uses the stored
assignment null log-probability supplied by the coordinator.  The old learned
condition-only prior remains available only as an explicit fallback ablation.
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
    "proto_disc_null_logp_mean",
    "proto_assignment_logp_mean",
    "proto_assignment_logp_std",
    "proto_ar_parallel_kl",
    "roster_ar_kl_zeroed",
    "roster_ar_kl_shuffled",
    "selection_independence_available",
    "selection_same_skill_rate",
    "selection_independence_null_rate",
    "selection_independence_deficit",
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
    use_learned_prior: bool = False
    prior_coef: float = 1.0


class PrototypeResponseDiscriminator(nn.Module):
    """Per-step q(z | o_next, cond) with stored-null residuals by default."""

    def __init__(
        self,
        obs_dim: int,
        n_skills: int,
        condition_dim: int,
        hidden_dim: int = 128,
        use_learned_prior: bool = False,
        prior_coef: float = 1.0,
    ):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_skills = int(max(n_skills, 1))
        self.condition_dim = int(max(condition_dim, 0))
        self.prior_input_dim = max(self.condition_dim, 1)
        self.use_learned_prior = bool(use_learned_prior)
        self.prior_coef = float(prior_coef)
        self.q_head = nn.Sequential(
            nn.LayerNorm(self.obs_dim + self.condition_dim),
            nn.Linear(self.obs_dim + self.condition_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, self.n_skills),
        )
        self.prior_head = (
            nn.Sequential(
                nn.LayerNorm(self.prior_input_dim),
                nn.Linear(self.prior_input_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, self.n_skills),
            )
            if self.use_learned_prior
            else None
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

    def forward(self, next_obs: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
        next_obs = next_obs.float()
        if self.condition_dim > 0:
            condition = condition.float()
            q_input = torch.cat([next_obs, condition], dim=-1)
        else:
            condition = torch.zeros(next_obs.shape[0], 0, dtype=next_obs.dtype, device=next_obs.device)
            q_input = next_obs
        return self.q_head(q_input)

    def forward_with_prior(self, next_obs: torch.Tensor, condition: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        q_logits = self.forward(next_obs, condition)
        if self.prior_head is None:
            raise RuntimeError("learned prior head is disabled; pass null_logp instead")
        return q_logits, self.prior_head(self._prior_input(condition))

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
        null_logp: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        labels = labels.long().clamp(0, self.n_skills - 1)
        q_logits = self.forward(next_obs, condition)
        q_loss = F.cross_entropy(q_logits, labels)
        q_logp = F.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)

        prior_loss = torch.zeros((), dtype=q_loss.dtype, device=q_loss.device)
        prior_acc = torch.zeros((), dtype=q_loss.dtype, device=q_loss.device)
        if self.use_learned_prior:
            _, prior_logits = self.forward_with_prior(next_obs, condition)
            prior_loss = F.cross_entropy(prior_logits, labels)
            prior_logp = F.log_softmax(prior_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
            prior_acc = self._accuracy(prior_logits, labels)
            null_logp_t = prior_logp.detach()
        else:
            if null_logp is None:
                raise ValueError("null_logp is required when learned prior is disabled")
            null_logp_t = null_logp.to(device=q_logp.device, dtype=q_logp.dtype).reshape_as(q_logp)

        total_loss = q_loss + float(self.prior_coef) * prior_loss
        residual = q_logp - null_logp_t.detach()

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
                "proto_disc_prior_acc": scalar(prior_acc),
                "proto_disc_null_logp_mean": scalar(null_logp_t.mean()),
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
        null_logp: torch.Tensor | None = None,
        clip: float = 2.0,
    ) -> torch.Tensor:
        labels = labels.long().clamp(0, self.n_skills - 1)
        q_logits = self.forward(next_obs, condition)
        q_logp = F.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        if self.use_learned_prior:
            _, prior_logits = self.forward_with_prior(next_obs, condition)
            baseline_logp = F.log_softmax(prior_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
        else:
            if null_logp is None:
                raise ValueError("null_logp is required when learned prior is disabled")
            baseline_logp = null_logp.to(device=q_logp.device, dtype=q_logp.dtype).reshape_as(q_logp)
        reward = q_logp - baseline_logp
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
        use_learned_prior=bool(getattr(agent, "prototype_disc_use_learned_prior", False)),
        prior_coef=float(getattr(agent, "prototype_disc_prior_coef", 1.0)),
    )
