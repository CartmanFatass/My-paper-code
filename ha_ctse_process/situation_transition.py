"""Team situation-transition residual heads for HA-CTSE R19.

The module is deliberately small and domain-agnostic: it only sees a current
situation id, a permutation-invariant active-skill count vector, and the next
situation id.  The residual ``log q(kappa' | kappa, xi) - log p(kappa' | kappa)``
is a high-level intrinsic signal; callers decide whether and where to inject it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


TEAM_TRANSITION_METRIC_FIELDS = (
    "team_transition_active",
    "team_transition_samples",
    "team_transition_loss",
    "team_transition_prior_loss",
    "team_transition_mi_mean",
    "team_transition_mi_on_self",
    "team_transition_mi_on_change",
    "team_transition_self_frac",
    "team_transition_missing_frac",
    "team_transition_reward_high_mean",
    "team_transition_reward_applied_steps",
    "team_transition_reward_env_ratio",
    "team_transition_reward_renewal_corr",
)


def empty_team_transition_metrics() -> dict[str, float]:
    return {key: 0.0 for key in TEAM_TRANSITION_METRIC_FIELDS}


@dataclass
class TeamTransitionInterval:
    env_id: int
    start_step: int
    end_step: int
    kappa: int
    xi: np.ndarray
    kappa_next: int


def skill_count_vector(active_skills: np.ndarray, n_skills: int) -> np.ndarray:
    """Return raw active-skill counts, ignoring invalid skill ids."""

    counts = np.zeros(int(n_skills), dtype=np.float32)
    if int(n_skills) <= 0:
        return counts
    skills = np.asarray(active_skills, dtype=np.int64).reshape(-1)
    for skill in skills:
        if 0 <= int(skill) < int(n_skills):
            counts[int(skill)] += 1.0
    return counts


def valid_transition_mask(kappa, kappa_next, num_situations: int) -> np.ndarray:
    current = np.asarray(kappa, dtype=np.int64).reshape(-1)
    nxt = np.asarray(kappa_next, dtype=np.int64).reshape(-1)
    n = int(num_situations)
    return (current >= 0) & (current < n) & (nxt >= 0) & (nxt < n)


def scaled_clipped_residual(residual: torch.Tensor, coef: float, clip: float) -> torch.Tensor:
    clipped = torch.clamp(residual.float(), -float(clip), float(clip))
    return float(coef) * clipped


def reward_is_active(
    probe_enabled: bool,
    reward_enabled: bool,
    total_steps: int,
    warmup_steps: int,
    coef: float,
) -> bool:
    return (
        bool(probe_enabled)
        and bool(reward_enabled)
        and int(total_steps) >= int(warmup_steps)
        and abs(float(coef)) > 0.0
    )


def attribute_interval_rewards_to_segments(
    intervals: list[TeamTransitionInterval],
    interval_rewards: np.ndarray,
    segments: list[Any],
) -> tuple[np.ndarray, int]:
    """Accumulate per-interval team rewards onto overlapping high-level segments.

    A team interval is shared by all agents in an environment.  A segment receives
    the interval reward if at least one of its primitive rollout indices lies in
    ``[interval.start_step, interval.end_step)``.  This keeps injection aligned
    to the existing per-segment high-level return path.
    """

    segment_rewards = np.zeros(len(segments), dtype=np.float32)
    applied = 0
    rewards = np.asarray(interval_rewards, dtype=np.float32).reshape(-1)
    for interval_idx, interval in enumerate(intervals):
        if interval_idx >= rewards.size:
            break
        reward = float(rewards[interval_idx])
        if not np.isfinite(reward):
            continue
        start = int(interval.start_step)
        end = int(interval.end_step)
        if end <= start:
            continue
        for seg_idx, segment in enumerate(segments):
            if int(getattr(segment, "env_id", -1)) != int(interval.env_id):
                continue
            rollout_indices = np.asarray(getattr(segment, "rollout_indices", []), dtype=np.int64).reshape(-1)
            if rollout_indices.size == 0:
                continue
            if bool(np.any((rollout_indices >= start) & (rollout_indices < end))):
                segment_rewards[seg_idx] += reward
                applied += 1
    return segment_rewards, applied


def pearson_corr(x, y) -> float:
    x_arr = np.asarray(x, dtype=np.float64).reshape(-1)
    y_arr = np.asarray(y, dtype=np.float64).reshape(-1)
    if x_arr.size < 2 or y_arr.size != x_arr.size:
        return 0.0
    if float(np.std(x_arr)) <= 1e-12 or float(np.std(y_arr)) <= 1e-12:
        return 0.0
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


class SituationTransitionPredictor(nn.Module):
    """Predict kappa transitions with and without active-skill count context."""

    def __init__(self, num_situations: int, n_skills: int, hidden_dim: int = 128):
        super().__init__()
        self.num_situations = int(max(num_situations, 1))
        self.n_skills = int(max(n_skills, 1))
        hidden = int(max(hidden_dim, 1))
        self.kappa_embedding = nn.Embedding(self.num_situations, hidden)
        self.prior_head = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, self.num_situations),
        )
        self.posterior_head = nn.Sequential(
            nn.LayerNorm(hidden + self.n_skills),
            nn.Linear(hidden + self.n_skills, hidden),
            nn.GELU(),
            nn.Linear(hidden, self.num_situations),
        )

    def forward(self, kappa: torch.Tensor, xi: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        kappa = kappa.detach().long().clamp(0, self.num_situations - 1)
        xi = xi.detach().float()
        if xi.dim() == 1:
            xi = xi.unsqueeze(0)
        if xi.shape[-1] != self.n_skills:
            raise ValueError(f"xi last dimension must be n_skills={self.n_skills}, got {xi.shape[-1]}")
        emb = self.kappa_embedding(kappa)
        prior_logits = self.prior_head(emb)
        posterior_logits = self.posterior_head(torch.cat([emb, xi], dim=-1))
        return posterior_logits, prior_logits

    def losses(self, kappa: torch.Tensor, xi: torch.Tensor, kappa_next: torch.Tensor) -> dict[str, torch.Tensor]:
        target = kappa_next.detach().long().clamp(0, self.num_situations - 1)
        posterior_logits, prior_logits = self.forward(kappa, xi)
        posterior_loss = F.cross_entropy(posterior_logits, target)
        prior_loss = F.cross_entropy(prior_logits, target)
        row = torch.arange(target.shape[0], device=target.device)
        log_q = F.log_softmax(posterior_logits, dim=-1)[row, target]
        log_p = F.log_softmax(prior_logits, dim=-1)[row, target]
        mi = log_q - log_p
        self_mask = target == kappa.detach().long().clamp(0, self.num_situations - 1)
        change_mask = ~self_mask
        zero = torch.zeros((), dtype=mi.dtype, device=mi.device)
        return {
            "posterior_loss": posterior_loss,
            "prior_loss": prior_loss,
            "posterior_logits": posterior_logits,
            "prior_logits": prior_logits,
            "log_q": log_q,
            "log_p": log_p,
            "mi": mi,
            "mi_on_self": mi[self_mask].mean() if torch.any(self_mask) else zero,
            "mi_on_change": mi[change_mask].mean() if torch.any(change_mask) else zero,
            "self_frac": self_mask.float().mean() if self_mask.numel() else zero,
            "posterior_acc": (posterior_logits.argmax(dim=-1) == target).float().mean(),
            "prior_acc": (prior_logits.argmax(dim=-1) == target).float().mean(),
        }

    @torch.no_grad()
    def reward(
        self,
        kappa: torch.Tensor,
        xi: torch.Tensor,
        kappa_next: torch.Tensor,
        coef: float,
        clip: float,
    ) -> torch.Tensor:
        terms = self.losses(kappa, xi, kappa_next)
        return scaled_clipped_residual(terms["mi"], coef=coef, clip=clip)
