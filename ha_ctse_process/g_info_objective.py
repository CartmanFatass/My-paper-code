"""Decision-level team-code usage diagnostics for standalone HA-CTSE.

This module asks whether the compact-conditioned team code ``g`` changes the
high-level joint decision distribution under the same OPT context.  It is not a
communication reward and it does not feed ``g`` into the primitive actor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


G_INFO_METRIC_FIELDS = (
    "g_info_active",
    "g_info_objective_active",
    "g_info_samples",
    "g_info_loss",
    "g_info_coef_scale",
    "g_info_skill_mi",
    "g_info_duration_mi",
    "g_info_edit_mi",
    "g_info_total_mi",
    "g_itv_kl_skill",
    "g_itv_tv_skill",
    "g_itv_kl_duration",
    "g_itv_tv_duration",
    "g_itv_kl_edit",
    "g_itv_tv_edit",
    "g_joint_assignment_distance",
)


def empty_g_info_metrics() -> dict[str, float]:
    return {key: 0.0 for key in G_INFO_METRIC_FIELDS}


@dataclass(frozen=True)
class GInfoConfig:
    diagnostic_on: bool = True
    objective_on: bool = False
    coef_skill: float = 0.0
    coef_duration: float = 0.0
    coef_edit: float = 0.0
    warmup_steps: int = 0
    anneal_steps: int = 0
    max_segments: int = 256

    @classmethod
    def from_config(cls, config: Any) -> "GInfoConfig":
        return cls(
            diagnostic_on=bool(getattr(config, "use_g_info_diagnostic", True)),
            objective_on=bool(getattr(config, "enable_g_info_objective", False)),
            coef_skill=float(getattr(config, "g_info_coef_skill", 0.0)),
            coef_duration=float(getattr(config, "g_info_coef_duration", 0.0)),
            coef_edit=float(getattr(config, "g_info_coef_edit", 0.0)),
            warmup_steps=int(max(getattr(config, "g_info_warmup_steps", 0), 0)),
            anneal_steps=int(max(getattr(config, "g_info_anneal_steps", 0), 0)),
            max_segments=int(max(getattr(config, "g_info_max_segments", 256), 1)),
        )


class GInfoObjective(nn.Module):
    """Enumerate team codes and measure/use their effect on high-level decisions."""

    def __init__(self, config: GInfoConfig | Any):
        super().__init__()
        self.cfg = config if isinstance(config, GInfoConfig) else GInfoConfig.from_config(config)

    @staticmethod
    def _entropy(probs: torch.Tensor) -> torch.Tensor:
        probs = probs.clamp_min(1e-8)
        return -(probs * probs.log()).sum(dim=-1)

    @classmethod
    def _normalized_mi(cls, probs: torch.Tensor) -> torch.Tensor:
        """Return E_x[I(g; decision | x)] normalized by log(num_actions)."""

        if probs.ndim != 3 or probs.shape[1] <= 1 or probs.shape[2] <= 1:
            return torch.zeros((), device=probs.device, dtype=probs.dtype)
        mean_probs = probs.mean(dim=1)
        raw_mi = cls._entropy(mean_probs) - cls._entropy(probs).mean(dim=1)
        denom = float(math.log(max(int(probs.shape[2]), 2)))
        return raw_mi.mean() / max(denom, 1e-8)

    @staticmethod
    def _pairwise_stats(probs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Mean off-diagonal pairwise KL and total variation over team codes."""

        if probs.ndim != 3 or probs.shape[1] <= 1:
            zero = torch.zeros((), device=probs.device, dtype=probs.dtype)
            return zero, zero
        probs = probs.clamp_min(1e-8)
        p = probs.unsqueeze(2)
        q = probs.unsqueeze(1)
        kl = (p * (p.log() - q.log())).sum(dim=-1)
        tv = 0.5 * torch.abs(p - q).sum(dim=-1)
        n_codes = int(probs.shape[1])
        mask = ~torch.eye(n_codes, dtype=torch.bool, device=probs.device).unsqueeze(0)
        mask = mask.expand(int(probs.shape[0]), -1, -1)
        return kl[mask].mean(), tv[mask].mean()

    def _coef_scale(self, total_steps: int) -> float:
        if int(total_steps) < int(self.cfg.warmup_steps):
            return 0.0
        if int(self.cfg.anneal_steps) <= 0:
            return 1.0
        elapsed = int(total_steps) - int(self.cfg.warmup_steps)
        return float(max(0.0, 1.0 - elapsed / float(max(int(self.cfg.anneal_steps), 1))))

    def forward(
        self,
        *,
        high_policy,
        bridge,
        high_obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        total_steps: int = 0,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        metrics = empty_g_info_metrics()
        zero_loss = torch.zeros((), device=compact.device, dtype=compact.dtype)
        if not self.cfg.diagnostic_on:
            return zero_loss, metrics
        if getattr(bridge, "bridge_type", "none") != "stochastic":
            return zero_loss, metrics
        n_codes = int(getattr(bridge, "num_team_codes", 1))
        if n_codes <= 1 or high_obs.shape[0] <= 0:
            return zero_loss, metrics

        batch_size = int(high_obs.shape[0])
        if batch_size > int(self.cfg.max_segments):
            # Deterministic striding keeps diagnostics stable across repeated reads.
            chosen = torch.linspace(
                0,
                batch_size - 1,
                steps=int(self.cfg.max_segments),
                device=high_obs.device,
            ).long()
            high_obs = high_obs.index_select(0, chosen)
            prev_skills = prev_skills.index_select(0, chosen)
            ages = ages.index_select(0, chosen)
            compact = compact.index_select(0, chosen)
            batch_size = int(high_obs.shape[0])

        codes = torch.arange(n_codes, dtype=torch.long, device=compact.device)
        team_vectors = bridge.code_embedding(codes)
        team_vectors = team_vectors.unsqueeze(0).expand(batch_size, n_codes, -1)

        high_obs_x = high_obs.unsqueeze(1).expand(batch_size, n_codes, -1).reshape(batch_size * n_codes, -1)
        prev_x = prev_skills.unsqueeze(1).expand(batch_size, n_codes).reshape(batch_size * n_codes)
        ages_x = ages.unsqueeze(1).expand(batch_size, n_codes).reshape(batch_size * n_codes)
        compact_x = compact.unsqueeze(1).expand(batch_size, n_codes, -1).reshape(batch_size * n_codes, -1)
        team_x = team_vectors.reshape(batch_size * n_codes, -1)
        omega_x = None
        if omega is not None:
            omega_x = omega.unsqueeze(1).expand(batch_size, n_codes, -1).reshape(batch_size * n_codes, -1)
        rel_x = None
        if agent_relevance is not None:
            rel_x = agent_relevance.unsqueeze(1).expand(batch_size, n_codes, -1).reshape(batch_size * n_codes, -1)

        skill_logits, duration_logits, _values = high_policy.logits(
            high_obs_x,
            prev_x,
            ages_x,
            compact_x,
            team_x,
            omega=omega_x,
            agent_relevance=rel_x,
        )
        skill_probs = F.softmax(skill_logits, dim=-1).reshape(batch_size, n_codes, -1)
        duration_probs = F.softmax(duration_logits, dim=-1).reshape(batch_size, n_codes, -1)

        skill_kl, skill_tv = self._pairwise_stats(skill_probs)
        duration_kl, duration_tv = self._pairwise_stats(duration_probs)
        skill_mi = self._normalized_mi(skill_probs)
        duration_mi = self._normalized_mi(duration_probs)
        edit_mi = torch.zeros((), device=compact.device, dtype=compact.dtype)
        edit_kl = torch.zeros((), device=compact.device, dtype=compact.dtype)
        edit_tv = torch.zeros((), device=compact.device, dtype=compact.dtype)
        total_mi = skill_mi + duration_mi + edit_mi

        coef_scale = self._coef_scale(int(total_steps))
        objective_on = bool(
            self.cfg.objective_on
            and coef_scale > 0.0
            and (
                abs(float(self.cfg.coef_skill)) > 0.0
                or abs(float(self.cfg.coef_duration)) > 0.0
                or abs(float(self.cfg.coef_edit)) > 0.0
            )
        )
        if objective_on:
            loss = -float(coef_scale) * (
                float(self.cfg.coef_skill) * skill_mi
                + float(self.cfg.coef_duration) * duration_mi
                + float(self.cfg.coef_edit) * edit_mi
            )
        else:
            loss = zero_loss

        def scalar(x: torch.Tensor) -> float:
            return float(x.detach().cpu().item())

        metrics.update(
            {
                "g_info_active": 1.0,
                "g_info_objective_active": 1.0 if objective_on else 0.0,
                "g_info_samples": float(batch_size),
                "g_info_loss": scalar(loss),
                "g_info_coef_scale": float(coef_scale),
                "g_info_skill_mi": scalar(skill_mi),
                "g_info_duration_mi": scalar(duration_mi),
                "g_info_edit_mi": scalar(edit_mi),
                "g_info_total_mi": scalar(total_mi),
                "g_itv_kl_skill": scalar(skill_kl),
                "g_itv_tv_skill": scalar(skill_tv),
                "g_itv_kl_duration": scalar(duration_kl),
                "g_itv_tv_duration": scalar(duration_tv),
                "g_itv_kl_edit": scalar(edit_kl),
                "g_itv_tv_edit": scalar(edit_tv),
                "g_joint_assignment_distance": scalar(0.5 * (skill_tv + duration_tv)),
            }
        )
        return loss, metrics
