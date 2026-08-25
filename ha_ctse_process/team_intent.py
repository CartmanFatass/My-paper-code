"""Sampled team-intent discriminator for HA-CTSE R21.

The team intent Z is a sampled high-level coordination variable.  This module
keeps the discriminator independent from policy modules: it learns
``q_D(Z | s_next)`` from detached rollout states, and exposes the prior-corrected
residual used as low-level intrinsic reward.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


TEAM_INTENT_METRIC_FIELDS = (
    "team_intent_enabled",
    "z_usage_entropy",
    "z_usage_max_frac",
    "z_dwell",
    "z_age_check_mean",
    "z_boundary_count",
    "z_decisions_per_update",
    "z_boundary_trunc_rate",
    "z_boundary_trunc_rate_dur3",
    "z_boundary_trunc_rate_dur7",
    "z_boundary_trunc_rate_dur13",
    "z_boundary_trunc_rate_dur24",
    "z_advantage_mean",
    "z_advantage_std",
    "z_advantage_var",
    "z_assignment_itv",
    "z_entropy_floor_active",
    "z_entropy_floor_gap",
    "z_entropy_floor_loss",
    "z_entropy_floor_coef_active",
    "z_policy_entropy",
    "z_policy_entropy_norm",
    "team_disc_active",
    "team_disc_samples",
    "team_disc_loss",
    "team_disc_acc",
    "team_disc_prior_entropy",
    "team_disc_residual_mean",
    "team_disc_residual_positive_frac",
    "team_disc_reward_mean",
    "team_disc_reward_unclipped_mean",
    "team_disc_reward_applied_steps",
    "team_disc_reward_env_ratio",
    "team_disc_reward_env_ratio_over05_count",
    "team_disc_reward_env_ratio_guard_active",
    "team_disc_reward_env_ratio_kill_triggered",
    "team_disc_reward_gated_off",
    "team_disc_forced_z_kl",
    "combined_intrinsic_env_ratio",
    "combined_intrinsic_env_ratio_over05_count",
    "combined_intrinsic_env_ratio_guard_active",
    "combined_intrinsic_env_ratio_kill_triggered",
)


def empty_team_intent_metrics() -> dict[str, float]:
    return {key: 0.0 for key in TEAM_INTENT_METRIC_FIELDS}


def label_entropy(labels, num_classes: int) -> tuple[float, float]:
    labels_arr = np.asarray(labels, dtype=np.int64).reshape(-1)
    num_classes = int(max(num_classes, 1))
    if labels_arr.size == 0:
        return 0.0, 0.0
    labels_arr = labels_arr[(labels_arr >= 0) & (labels_arr < num_classes)]
    if labels_arr.size == 0:
        return 0.0, 0.0
    counts = np.bincount(labels_arr, minlength=num_classes).astype(np.float64)
    probs = counts / max(float(np.sum(counts)), 1.0)
    active = probs[probs > 0.0]
    denom = float(np.log(max(num_classes, 2)))
    entropy = -float(np.sum(active * np.log(active + 1e-12))) / denom
    return entropy, float(np.max(probs)) if probs.size else 0.0


class TeamIntentDiscriminator(nn.Module):
    """Predict sampled team intent Z from post-step global state."""

    def __init__(self, state_dim: int, num_team_codes: int, hidden_dim: int = 128):
        super().__init__()
        self.state_dim = int(state_dim)
        self.num_team_codes = int(max(num_team_codes, 1))
        hidden = int(max(hidden_dim, 1))
        self.net = nn.Sequential(
            nn.LayerNorm(self.state_dim),
            nn.Linear(self.state_dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, self.num_team_codes),
        )

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        states = states.detach().float()
        if states.dim() == 1:
            states = states.unsqueeze(0)
        if states.shape[-1] != self.state_dim:
            raise ValueError(f"state_dim mismatch: expected {self.state_dim}, got {states.shape[-1]}")
        return self.net(states)

    def losses(
        self,
        states: torch.Tensor,
        labels: torch.Tensor,
        prior_probs: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        labels = labels.detach().long().clamp(0, self.num_team_codes - 1)
        prior_probs = prior_probs.detach().float().clamp_min(1e-8)
        prior_probs = prior_probs / prior_probs.sum().clamp_min(1e-8)
        logits = self.forward(states)
        loss = F.cross_entropy(logits, labels)
        row = torch.arange(labels.shape[0], device=labels.device)
        log_q = F.log_softmax(logits, dim=-1)[row, labels]
        log_p = torch.log(prior_probs.to(device=labels.device, dtype=log_q.dtype))[labels]
        residual = log_q - log_p
        return {
            "loss": loss,
            "logits": logits,
            "log_q": log_q,
            "log_p": log_p,
            "residual": residual,
            "acc": (logits.argmax(dim=-1) == labels).float().mean(),
            "prior_entropy": -torch.sum(prior_probs * torch.log(prior_probs)),
        }

    @torch.no_grad()
    def reward(
        self,
        states: torch.Tensor,
        labels: torch.Tensor,
        prior_probs: torch.Tensor,
        coef: float,
        clip: float,
    ) -> torch.Tensor:
        terms = self.losses(states, labels, prior_probs)
        residual = torch.clamp(terms["residual"], -float(clip), float(clip))
        return float(coef) * residual
