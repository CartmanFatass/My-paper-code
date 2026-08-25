"""Reward-off team-conditioned q_d probe for HA-CTSE R24.

The probe asks whether the local effect of an executed individual skill carries
recoverable skill-label information beyond the current team/assignment context:

    q_full(z_i | local_behavior_window_i, Z, xi_context_i, c, omega)
    q_prior(z_i | Z, xi_context_i, c, omega)

``xi_context_i`` must exclude the focal executed skill label ``z_i``.  It may
include teammate assignments, duration/phase/context, and detached policy
context.  The behavior window is represented as two streams so action
distribution changes and state/effect dynamics can be audited separately.

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
    "r24_qd_loss_behavior",
    "r24_qd_loss_pre",
    "r24_qd_acc_full",
    "r24_qd_acc_prior",
    "r24_qd_acc_behavior",
    "r24_qd_acc_pre",
    "r24_qd_acc_majority",
    "r24_qd_residual_gain",
    "r24_qd_residual_mean",
    "r24_qd_positive_frac",
    "r24_qd_behavior_gain_over_prior",
    "r24_qd_pre_gain_over_prior",
    "r24_qd_full_minus_behavior_acc",
    "r24_qd_full_minus_pre_acc",
    "r24_qd_pre_valid_frac",
    "r24_qd_label_entropy",
    "r24_qd_label_max_frac",
    "r24_qd_shuffle_residual_mean",
    "r24_qd_shuffle_positive_frac",
    "r24_qd_shuffle_acc_gap",
    "r24_qd_shuffle_label_changed_frac",
    "r24_qd_fake_residual_mean",
    "r24_qd_fake_positive_frac",
    "r24_qd_fake_acc_gap",
    "r24_qd_fake_label_changed_frac",
    "r24_qd_export_rows",
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
    """q_d_full(z_i | action_stream, effect_stream, context) vs q_d_prior."""

    def __init__(
        self,
        action_dim: int,
        effect_dim: int,
        condition_dim: int,
        num_skills: int,
        hidden_dim: int = 128,
    ):
        super().__init__()
        self.action_dim = int(max(action_dim, 0))
        self.effect_dim = int(max(effect_dim, 0))
        self.condition_dim = int(max(condition_dim, 0))
        self.num_skills = int(max(num_skills, 1))
        hidden = int(max(hidden_dim, 1))
        self._action_eff = int(max(self.action_dim, 1))
        self._effect_eff = int(max(self.effect_dim, 1))
        self._condition_eff = int(max(self.condition_dim, 1))
        self.action_encoder = _mlp(self._action_eff, hidden, hidden)
        self.effect_encoder = _mlp(self._effect_eff, hidden, hidden)
        self.q_full = _mlp(hidden * 2 + self._condition_eff, hidden, self.num_skills)
        self.q_behavior = _mlp(hidden * 2, hidden, self.num_skills)
        self.q_pre = _mlp(hidden * 2 + self._condition_eff, hidden, self.num_skills)
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

    def _prep(
        self,
        action: torch.Tensor,
        effect: torch.Tensor,
        condition: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        action = self._as_rows(action, "action")
        effect = self._as_rows(effect, "effect")
        condition = self._as_rows(condition, "condition")
        if action.shape[0] != effect.shape[0] or action.shape[0] != condition.shape[0]:
            raise ValueError("action, effect, and condition batch sizes must match")

        if self.action_dim == 0:
            action = self._pad_zero_width(action, self._action_eff)
        elif action.shape[-1] != self.action_dim:
            raise ValueError(f"action_dim mismatch: expected {self.action_dim}, got {action.shape[-1]}")

        if self.effect_dim == 0:
            effect = self._pad_zero_width(effect, self._effect_eff)
        elif effect.shape[-1] != self.effect_dim:
            raise ValueError(f"effect_dim mismatch: expected {self.effect_dim}, got {effect.shape[-1]}")

        if self.condition_dim == 0:
            condition = self._pad_zero_width(condition, self._condition_eff)
        elif condition.shape[-1] != self.condition_dim:
            raise ValueError(f"condition_dim mismatch: expected {self.condition_dim}, got {condition.shape[-1]}")

        return action, effect, condition

    def _behavior_repr(
        self,
        action: torch.Tensor,
        effect: torch.Tensor,
        condition: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        action, effect, condition = self._prep(action, effect, condition)
        action_repr = self.action_encoder(action)
        effect_repr = self.effect_encoder(effect)
        return torch.cat([action_repr, effect_repr], dim=-1), condition

    def _logits(
        self,
        action: torch.Tensor,
        effect: torch.Tensor,
        condition: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        behavior_repr, condition = self._behavior_repr(action, effect, condition)
        full = self.q_full(torch.cat([behavior_repr, condition], dim=-1))
        behavior = self.q_behavior(behavior_repr)
        prior = self.q_prior(condition)
        return full, prior, behavior

    def _pre_logits(
        self,
        pre_action: torch.Tensor,
        pre_effect: torch.Tensor,
        condition: torch.Tensor,
    ) -> torch.Tensor:
        behavior_repr, condition = self._behavior_repr(pre_action, pre_effect, condition)
        return self.q_pre(torch.cat([behavior_repr, condition], dim=-1))

    @staticmethod
    def _label_log_probs(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        row = torch.arange(labels.shape[0], device=logits.device)
        return F.log_softmax(logits, dim=-1)[row, labels]

    @staticmethod
    def _accuracy(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return (logits.argmax(dim=-1) == labels).float().mean()

    def _null_metrics(
        self,
        full: torch.Tensor,
        prior: torch.Tensor,
        labels: torch.Tensor,
        prefix: str,
    ) -> dict[str, torch.Tensor]:
        log_q_full = self._label_log_probs(full, labels)
        log_q_prior = self._label_log_probs(prior, labels)
        residual = log_q_full - log_q_prior
        return {
            f"{prefix}_residual_mean": residual.mean(),
            f"{prefix}_positive_frac": (residual > 0.0).float().mean(),
            f"{prefix}_acc_gap": self._accuracy(full, labels) - self._accuracy(prior, labels),
        }

    def losses(
        self,
        action: torch.Tensor,
        effect: torch.Tensor,
        condition: torch.Tensor,
        labels: torch.Tensor,
        pre_action: torch.Tensor | None = None,
        pre_effect: torch.Tensor | None = None,
        pre_mask: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        full, prior, behavior = self._logits(action, effect, condition)
        labels = labels.detach().long().reshape(-1).clamp(0, self.num_skills - 1).to(device=full.device)
        if labels.shape[0] != full.shape[0]:
            raise ValueError("labels batch size must match action, effect, and condition")

        loss_full = F.cross_entropy(full, labels)
        loss_prior = F.cross_entropy(prior, labels)
        loss_behavior = F.cross_entropy(behavior, labels)
        log_q_full = self._label_log_probs(full, labels)
        log_q_prior = self._label_log_probs(prior, labels)
        residual = log_q_full - log_q_prior
        acc_full = self._accuracy(full, labels)
        acc_prior = self._accuracy(prior, labels)
        acc_behavior = self._accuracy(behavior, labels)

        pre_logits = None
        pre_valid = torch.zeros(labels.shape[0], dtype=torch.bool, device=full.device)
        if pre_action is not None and pre_effect is not None:
            pre_logits = self._pre_logits(pre_action, pre_effect, condition)
            if pre_logits.shape[0] != labels.shape[0]:
                raise ValueError("pre_action/pre_effect batch size must match labels")
            if pre_mask is None:
                pre_valid = torch.ones(labels.shape[0], dtype=torch.bool, device=full.device)
            else:
                pre_valid = pre_mask.detach().reshape(-1).to(device=full.device).bool()
                if pre_valid.shape[0] != labels.shape[0]:
                    raise ValueError("pre_mask batch size must match labels")

        if pre_logits is not None and bool(pre_valid.any().item()):
            loss_pre = F.cross_entropy(pre_logits[pre_valid], labels[pre_valid])
            acc_pre = self._accuracy(pre_logits[pre_valid], labels[pre_valid])
            pre_gain_over_prior = acc_pre - self._accuracy(prior[pre_valid], labels[pre_valid])
            full_minus_pre = self._accuracy(full[pre_valid], labels[pre_valid]) - acc_pre
        else:
            loss_pre = full.new_zeros(())
            acc_pre = full.new_zeros(())
            pre_gain_over_prior = full.new_zeros(())
            full_minus_pre = full.new_zeros(())

        counts = torch.bincount(labels, minlength=self.num_skills).float()
        probs = counts / counts.sum().clamp_min(1.0)
        nz_probs = probs[probs > 0.0]
        label_entropy = -(nz_probs * nz_probs.log()).sum() if nz_probs.numel() else full.new_zeros(())
        label_max_frac = probs.max() if probs.numel() else full.new_zeros(())

        if labels.shape[0] > 1:
            shuffled = torch.roll(labels, shifts=1, dims=0)
        else:
            shuffled = labels
        fake = (labels + 1) % max(self.num_skills, 1)
        shuffle_metrics = self._null_metrics(full, prior, shuffled, "shuffle")
        fake_metrics = self._null_metrics(full, prior, fake, "fake")
        return {
            "loss_full": loss_full,
            "loss_prior": loss_prior,
            "loss_behavior": loss_behavior,
            "loss_pre": loss_pre,
            "loss": loss_full + loss_prior + loss_behavior + loss_pre,
            "logits_full": full,
            "logits_prior": prior,
            "logits_behavior": behavior,
            "log_q_full": log_q_full,
            "log_q_prior": log_q_prior,
            "residual": residual,
            "residual_mean": residual.mean(),
            "positive_frac": (residual > 0.0).float().mean(),
            "acc_full": acc_full,
            "acc_prior": acc_prior,
            "acc_behavior": acc_behavior,
            "acc_pre": acc_pre,
            "acc_majority": label_max_frac,
            "residual_gain": acc_full - acc_prior,
            "behavior_gain_over_prior": acc_behavior - acc_prior,
            "pre_gain_over_prior": pre_gain_over_prior,
            "full_minus_behavior_acc": acc_full - acc_behavior,
            "full_minus_pre_acc": full_minus_pre,
            "pre_valid_frac": pre_valid.float().mean(),
            "label_entropy": label_entropy,
            "label_max_frac": label_max_frac,
            "shuffle_residual_mean": shuffle_metrics["shuffle_residual_mean"],
            "shuffle_positive_frac": shuffle_metrics["shuffle_positive_frac"],
            "shuffle_acc_gap": shuffle_metrics["shuffle_acc_gap"],
            "shuffle_label_changed_frac": (shuffled != labels).float().mean(),
            "fake_residual_mean": fake_metrics["fake_residual_mean"],
            "fake_positive_frac": fake_metrics["fake_positive_frac"],
            "fake_acc_gap": fake_metrics["fake_acc_gap"],
            "fake_label_changed_frac": (fake != labels).float().mean(),
        }
