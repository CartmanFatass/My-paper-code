"""Intrinsic reward composition for the standalone HA-CTSE process path.

The standalone algorithm does not inherit HMASD's discriminator/discoverer
targets directly.  This module centralizes the replacement logic so semantic
pressure, high-level quality gates, and warmup/clip behavior are explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch


@dataclass(frozen=True)
class IntrinsicGateResult:
    active: bool
    score: float
    posterior_minus_shortcut: float
    residual_mi: float
    segment_count: int
    reason_code: int

    def metrics(self, prefix: str) -> dict[str, float]:
        return {
            f"{prefix}_active": float(self.active),
            f"{prefix}_score": float(self.score),
            f"{prefix}_posterior_minus_shortcut": float(self.posterior_minus_shortcut),
            f"{prefix}_residual_mi": float(self.residual_mi),
            f"{prefix}_segment_count": float(self.segment_count),
            f"{prefix}_reason_code": float(self.reason_code),
        }


class RunningRewardNormalizer:
    """Small running normalizer for auxiliary reward streams."""

    def __init__(self, epsilon: float = 1e-4, clip: float = 5.0):
        self.epsilon = float(epsilon)
        self.clip = float(clip)
        self.count = 0.0
        self.mean = 0.0
        self.var = 1.0

    def normalize(self, values: torch.Tensor, update: bool = True) -> torch.Tensor:
        if values.numel() == 0:
            return values
        if update:
            flat = values.detach().float().reshape(-1)
            batch_count = float(flat.numel())
            batch_mean = float(flat.mean().cpu().item())
            batch_var = float(flat.var(unbiased=False).cpu().item()) if flat.numel() > 1 else 0.0
            if self.count <= 0.0:
                self.mean = batch_mean
                self.var = max(batch_var, self.epsilon)
                self.count = batch_count
            else:
                delta = batch_mean - self.mean
                total = self.count + batch_count
                new_mean = self.mean + delta * batch_count / max(total, self.epsilon)
                m_a = self.var * self.count
                m_b = batch_var * batch_count
                m2 = m_a + m_b + delta * delta * self.count * batch_count / max(total, self.epsilon)
                self.mean = new_mean
                self.var = max(m2 / max(total, self.epsilon), self.epsilon)
                self.count = total
        normalized = (values - self.mean) / float(np.sqrt(max(self.var, self.epsilon)))
        return torch.clamp(normalized, -self.clip, self.clip)


class IntrinsicRewardComposer:
    """Compose low/high intrinsic rewards and gate noisy high-level signals."""

    # Gate reason codes keep log output numeric and CSV-friendly.
    REASON_ACTIVE = 0
    REASON_DISABLED = 1
    REASON_WARMUP = 2
    REASON_TOO_FEW_SEGMENTS = 3
    REASON_LOW_POSTERIOR_GAP = 4
    REASON_LOW_RESIDUAL_MI = 5
    REASON_LOW_POSTERIOR_ACC = 6

    def __init__(self, config: Any):
        self.segment_gate_enabled = bool(getattr(config, "intrinsic_segment_gate_enabled", True))
        self.segment_gate_margin = float(getattr(config, "intrinsic_segment_gate_margin", 0.05))
        self.segment_gate_min_segments = int(max(getattr(config, "intrinsic_segment_gate_min_segments", 64), 1))
        self.segment_gate_min_residual_mi = float(
            getattr(config, "intrinsic_segment_gate_min_residual_mi", 0.0)
        )
        self.segment_gate_min_posterior_acc = float(
            getattr(config, "intrinsic_segment_gate_min_posterior_acc", 0.0)
        )
        self.reward_normalize = bool(getattr(config, "intrinsic_reward_normalize", False))
        self.transition_normalizer = RunningRewardNormalizer()
        self.segment_normalizer = RunningRewardNormalizer()

    def segment_quality_gate(
        self,
        *,
        enabled: bool,
        warmup_active: bool,
        segment_count: int,
        posterior_acc: float,
        shortcut_acc: float,
        residual_mi_mean: float,
    ) -> IntrinsicGateResult:
        posterior_minus_shortcut = float(posterior_acc) - float(shortcut_acc)
        score = min(
            posterior_minus_shortcut - self.segment_gate_margin,
            float(residual_mi_mean) - self.segment_gate_min_residual_mi,
        )
        if not enabled or not self.segment_gate_enabled:
            reason = self.REASON_DISABLED
            active = not self.segment_gate_enabled and enabled and not warmup_active
        elif warmup_active:
            reason = self.REASON_WARMUP
            active = False
        elif int(segment_count) < self.segment_gate_min_segments:
            reason = self.REASON_TOO_FEW_SEGMENTS
            active = False
        elif posterior_minus_shortcut < self.segment_gate_margin:
            reason = self.REASON_LOW_POSTERIOR_GAP
            active = False
        elif float(residual_mi_mean) < self.segment_gate_min_residual_mi:
            reason = self.REASON_LOW_RESIDUAL_MI
            active = False
        elif float(posterior_acc) < self.segment_gate_min_posterior_acc:
            reason = self.REASON_LOW_POSTERIOR_ACC
            active = False
        else:
            reason = self.REASON_ACTIVE
            active = True
        return IntrinsicGateResult(
            active=bool(active),
            score=float(score),
            posterior_minus_shortcut=posterior_minus_shortcut,
            residual_mi=float(residual_mi_mean),
            segment_count=int(segment_count),
            reason_code=int(reason),
        )

    def transition_rewards(
        self,
        transition_mi: torch.Tensor,
        *,
        coef: float,
        clip: float,
        warmup_active: bool,
        enabled: bool,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        if transition_mi.numel() == 0:
            return transition_mi, {
                "active": 0.0,
                "warmup_active": float(warmup_active),
                "unclipped_mean": 0.0,
            }
        raw = float(coef) * torch.relu(transition_mi)
        if self.reward_normalize:
            raw = self.transition_normalizer.normalize(raw, update=bool(enabled and not warmup_active))
        reward = raw if enabled and not warmup_active else torch.zeros_like(raw)
        if clip > 0.0:
            reward = torch.clamp(reward, 0.0, float(clip))
        return reward, {
            "active": float(bool(enabled and not warmup_active)),
            "warmup_active": float(warmup_active),
            "unclipped_mean": float(raw.detach().mean().cpu().item()),
        }

    def split_segment_rewards(
        self,
        candidate_rewards: np.ndarray,
        *,
        injection: str,
        high_gate: IntrinsicGateResult | None,
        low_gate_active: bool = True,
    ) -> tuple[np.ndarray, np.ndarray]:
        candidate_rewards = np.asarray(candidate_rewards, dtype=np.float32)
        high_gate_active = True if high_gate is None else bool(high_gate.active)
        if str(injection).lower() in {"high_only", "high_and_low"} and high_gate_active:
            high_rewards = candidate_rewards.copy()
        else:
            high_rewards = np.zeros_like(candidate_rewards)
        if str(injection).lower() in {"low_only", "high_and_low"} and bool(low_gate_active):
            low_rewards = candidate_rewards.copy()
        else:
            low_rewards = np.zeros_like(candidate_rewards)
        return high_rewards, low_rewards
