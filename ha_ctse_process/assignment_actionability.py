"""q_A residual actionability discriminator for HA-CTSE R23 (Option-B).

Asks: given OPT context (c, omega), does the executed joint assignment xi carry
extra information that recovers the sampled team intent Z, beyond the context prior?
Two heads q_A_full(Z|xi,c,omega) and q_A_prior(Z|c,omega); residual = log q_full - log q_prior.

This is the cross-entropy successor to the self-stalling normalized-MI g-info objective
(R23 gradient audit 2026-07-06: g-info grad into the Z path was <2% of PPO and MI never
moved). A discriminator gives a first-order gradient that does not vanish at low MI.

Contract: discriminator-only (inputs detached, own optimizer, high-level only). The reward
is clipped and no_grad, added to the high-level assignment path only, and gated by a probe
pass elsewhere. It is NOT a communication reward and never reads raw communication fields.
Double-count rule (PR-1): q_A may read xi; the team-effect discriminator q_D must NOT.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F


ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS = (
    "q_a_active",
    "q_a_reward_active",
    "q_a_samples",
    "q_a_loss_full",
    "q_a_loss_prior",
    "q_a_acc_full",
    "q_a_acc_prior",
    "q_a_residual_gain",
    "q_a_residual_mean",
    "q_a_prior_entropy",
    "q_a_reward_mean",
    "q_a_reward_applied_steps",
)


def empty_assignment_actionability_metrics() -> dict[str, float]:
    return {k: 0.0 for k in ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS}


@dataclass(frozen=True)
class AssignmentActionabilityConfig:
    probe_on: bool = False
    reward_on: bool = False
    coef: float = 0.05
    clip: float = 1.0
    warmup_steps: int = 20000
    include_soft: bool = True
    hidden_dim: int = 128

    @classmethod
    def from_config(cls, config: Any) -> "AssignmentActionabilityConfig":
        reward_on = bool(getattr(config, "enable_assignment_actionability_reward", False))
        probe_on = bool(getattr(config, "enable_assignment_actionability_probe", False)) or reward_on
        return cls(
            probe_on=probe_on,
            reward_on=reward_on,
            coef=float(getattr(config, "assignment_actionability_coef", 0.05)),
            clip=float(getattr(config, "assignment_actionability_clip", 1.0)),
            warmup_steps=int(max(getattr(config, "assignment_actionability_warmup_steps", 20000), 0)),
            include_soft=bool(getattr(config, "assignment_actionability_include_soft", True)),
            hidden_dim=int(max(getattr(config, "assignment_actionability_hidden_dim", 128), 1)),
        )


def _mlp(in_dim: int, hidden: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(in_dim),
        nn.Linear(in_dim, hidden),
        nn.GELU(),
        nn.Linear(hidden, hidden),
        nn.GELU(),
        nn.Linear(hidden, out_dim),
    )


class AssignmentActionabilityDiscriminator(nn.Module):
    """q_A_full(Z | xi, c, omega) vs q_A_prior(Z | c, omega); residual = log q_full - log q_prior."""

    def __init__(self, xi_dim: int, context_dim: int, num_team_codes: int, hidden_dim: int = 128):
        super().__init__()
        self.xi_dim = int(xi_dim)
        self.context_dim = int(context_dim)
        # A zero-width context is padded to a single zero column so both heads always
        # have a well-defined input; keep the effective width consistent everywhere.
        self._ctx_eff = int(max(context_dim, 1))
        self.num_team_codes = int(max(num_team_codes, 1))
        hidden = int(max(hidden_dim, 1))
        self.q_full = _mlp(self.xi_dim + self._ctx_eff, hidden, self.num_team_codes)
        self.q_prior = _mlp(self._ctx_eff, hidden, self.num_team_codes)

    def _prep(self, xi: torch.Tensor, context: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        xi = xi.detach().float()
        if xi.dim() == 1:
            xi = xi.unsqueeze(0)
        context = context.detach().float()
        if context.dim() == 1:
            context = context.unsqueeze(0)
        if context.shape[-1] != self._ctx_eff:
            # Pad (or a zero-width context) up to the effective width used at construction.
            pad = torch.zeros(
                xi.shape[0], self._ctx_eff - context.shape[-1], device=xi.device, dtype=xi.dtype
            )
            context = torch.cat([context, pad], dim=-1) if context.shape[-1] > 0 else pad
        return xi, context

    def _logits(self, xi: torch.Tensor, context: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        xi, context = self._prep(xi, context)
        full = self.q_full(torch.cat([xi, context], dim=-1))
        prior = self.q_prior(context)
        return full, prior

    def losses(
        self,
        xi: torch.Tensor,
        context: torch.Tensor,
        labels: torch.Tensor,
        prior_probs: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        labels = labels.detach().long().clamp(0, self.num_team_codes - 1)
        prior_probs = prior_probs.detach().float().clamp_min(1e-8)
        prior_probs = prior_probs / prior_probs.sum().clamp_min(1e-8)
        full, prior = self._logits(xi, context)
        loss_full = F.cross_entropy(full, labels)
        loss_prior = F.cross_entropy(prior, labels)
        row = torch.arange(labels.shape[0], device=labels.device)
        log_qf = F.log_softmax(full, dim=-1)[row, labels]
        log_qp = F.log_softmax(prior, dim=-1)[row, labels]
        residual = log_qf - log_qp
        acc_full = (full.argmax(dim=-1) == labels).float().mean()
        acc_prior = (prior.argmax(dim=-1) == labels).float().mean()
        return {
            "loss_full": loss_full,
            "loss_prior": loss_prior,
            "acc_full": acc_full,
            "acc_prior": acc_prior,
            "residual": residual,
            "residual_gain": acc_full - acc_prior,
            "prior_entropy": -torch.sum(prior_probs * torch.log(prior_probs)),
        }

    @torch.no_grad()
    def reward(
        self,
        xi: torch.Tensor,
        context: torch.Tensor,
        labels: torch.Tensor,
        prior_probs: torch.Tensor,
        coef: float,
        clip: float,
    ) -> torch.Tensor:
        residual = self.losses(xi, context, labels, prior_probs)["residual"]
        return float(coef) * torch.clamp(residual, -float(clip), float(clip))
