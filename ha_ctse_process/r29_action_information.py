"""Support-native counterfactual action-information target for R29."""

from __future__ import annotations

from dataclasses import dataclass
from math import log

import numpy as np
import torch


EXPERIMENT_ID = "EXP-20260713-r29-g0-counterfactual-action-information"
SCHEMA = "r29-counterfactual-action-information-v1"
ACTIVE_MEAN_MIN = 0.01
PER_SKILL_MEAN_MIN = 0.005
INACTIVE_ABS_MAX = 1e-6
LABEL_ENTROPY_MIN = 0.8
MIN_ROWS = 5_000
MIN_RESETS = 48


@dataclass(frozen=True)
class ActionInformationEvaluation:
    active_reward: np.ndarray
    sham_reward: np.ndarray
    active_by_row: np.ndarray
    sham_by_row: np.ndarray
    active_by_skill: np.ndarray


@dataclass(frozen=True)
class ExecutedActionInformation:
    reward: torch.Tensor
    squashed_actual_log_prob: torch.Tensor
    candidate_raw_log_prob: torch.Tensor


def normalized_label_entropy(labels: np.ndarray, num_skills: int) -> float:
    values = np.asarray(labels, dtype=np.int64).reshape(-1)
    if int(num_skills) < 2 or values.size == 0:
        raise ValueError("at least two skills and one label are required")
    if np.any(values < 0) or np.any(values >= int(num_skills)):
        raise ValueError("labels fall outside the skill range")
    counts = np.bincount(values, minlength=int(num_skills)).astype(np.float64)
    probabilities = counts[counts > 0.0] / counts.sum()
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return entropy / log(int(num_skills))


def evaluate_action_information(
    means: torch.Tensor,
    log_stds: torch.Tensor,
    *,
    epsilon: torch.Tensor,
) -> ActionInformationEvaluation:
    """Estimate a uniform-prior action density ratio on fixed policy states.

    ``means`` and ``log_stds`` have shape ``[rows, skills, action_dim]``.
    ``epsilon`` has shape ``[samples, rows, skills, action_dim]``. Each source
    skill samples its own raw Gaussian action. The tanh Jacobian cancels in the
    likelihood ratio because every candidate scores the same transformed action.
    """

    mean = torch.as_tensor(means, dtype=torch.float32)
    log_std = torch.as_tensor(log_stds, dtype=torch.float32, device=mean.device)
    noise = torch.as_tensor(epsilon, dtype=torch.float32, device=mean.device)
    if mean.ndim != 3 or log_std.shape != mean.shape:
        raise ValueError("means and log_stds must share [rows, skills, action] shape")
    rows, skills, action_dim = mean.shape
    if skills < 2:
        raise ValueError("at least two skills are required")
    if noise.ndim != 4 or noise.shape[1:] != (rows, skills, action_dim):
        raise ValueError("epsilon must have [samples, rows, skills, action] shape")
    if not (
        torch.isfinite(mean).all()
        and torch.isfinite(log_std).all()
        and torch.isfinite(noise).all()
    ):
        raise ValueError("action-information inputs must be finite")

    raw_action = mean.unsqueeze(0) + torch.exp(log_std).unsqueeze(0) * noise
    residual = (
        raw_action.unsqueeze(3) - mean.unsqueeze(0).unsqueeze(2)
    ) / torch.exp(log_std).unsqueeze(0).unsqueeze(2)
    candidate_log_prob = -0.5 * (
        residual.square()
        + 2.0 * log_std.unsqueeze(0).unsqueeze(2)
        + log(2.0 * np.pi)
    ).sum(dim=-1)
    log_mixture = torch.logsumexp(candidate_log_prob, dim=-1) - log(skills)

    source_index = torch.arange(skills, device=mean.device)
    active_log_prob = candidate_log_prob.diagonal(dim1=2, dim2=3)
    sham_index = (source_index + 1) % skills
    sham_log_prob = candidate_log_prob.gather(
        3,
        sham_index.view(1, 1, skills, 1).expand(
            noise.shape[0], rows, skills, 1
        ),
    ).squeeze(3)
    active = active_log_prob - log_mixture
    sham = sham_log_prob - log_mixture
    if not (torch.isfinite(active).all() and torch.isfinite(sham).all()):
        raise ValueError("action-information rewards must be finite")

    return ActionInformationEvaluation(
        active_reward=active.detach().cpu().numpy(),
        sham_reward=sham.detach().cpu().numpy(),
        active_by_row=active.mean(dim=(0, 2)).detach().cpu().numpy(),
        sham_by_row=sham.mean(dim=(0, 2)).detach().cpu().numpy(),
        active_by_skill=active.mean(dim=(0, 1)).detach().cpu().numpy(),
    )


def evaluate_executed_action_information(
    means: torch.Tensor,
    log_stds: torch.Tensor,
    actions: torch.Tensor,
    skills: torch.Tensor,
    *,
    epsilon: float = 1e-6,
) -> ExecutedActionInformation:
    """Score collected tanh actions under every counterfactual skill policy."""

    mean = torch.as_tensor(means, dtype=torch.float32)
    log_std = torch.as_tensor(log_stds, dtype=torch.float32, device=mean.device)
    bounded = torch.as_tensor(actions, dtype=torch.float32, device=mean.device)
    labels = torch.as_tensor(skills, dtype=torch.long, device=mean.device)
    if mean.ndim != 3 or log_std.shape != mean.shape:
        raise ValueError("means and log_stds must share [rows, skills, action] shape")
    rows, num_skills, action_dim = mean.shape
    if bounded.shape != (rows, action_dim) or labels.shape != (rows,):
        raise ValueError("actions or skills do not align with actor parameters")
    if torch.any(labels < 0) or torch.any(labels >= num_skills):
        raise ValueError("skills fall outside the counterfactual policy set")
    if not (
        torch.isfinite(mean).all()
        and torch.isfinite(log_std).all()
        and torch.isfinite(bounded).all()
    ):
        raise ValueError("executed-action inputs must be finite")

    clipped = torch.clamp(bounded, -1.0 + float(epsilon), 1.0 - float(epsilon))
    raw_action = torch.atanh(clipped)
    residual = (raw_action.unsqueeze(1) - mean) / torch.exp(log_std)
    candidate_log_prob = -0.5 * (
        residual.square() + 2.0 * log_std + log(2.0 * np.pi)
    ).sum(dim=-1)
    actual_log_prob = candidate_log_prob.gather(1, labels[:, None]).squeeze(1)
    log_mixture = torch.logsumexp(candidate_log_prob, dim=1) - log(num_skills)
    jacobian = torch.log(1.0 - clipped.square() + float(epsilon)).sum(dim=-1)
    reward = actual_log_prob - log_mixture
    squashed_actual = actual_log_prob - jacobian
    if not (
        torch.isfinite(reward).all() and torch.isfinite(squashed_actual).all()
    ):
        raise ValueError("executed-action score is non-finite")
    return ExecutedActionInformation(
        reward=reward,
        squashed_actual_log_prob=squashed_actual,
        candidate_raw_log_prob=candidate_log_prob,
    )


def classify_checkpoint(
    *,
    rows: int,
    resets: int,
    label_entropy: float,
    active_mean: float,
    minimum_skill_mean: float,
    active_minus_sham_lower: float,
    inactive_max_abs: float,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    values = (
        label_entropy,
        active_mean,
        minimum_skill_mean,
        active_minus_sham_lower,
        inactive_max_abs,
    )
    if not np.isfinite(values).all():
        return "INVALID", ["non-finite checkpoint evidence"]
    if int(rows) < MIN_ROWS or int(resets) < MIN_RESETS:
        return "UNDERPOWERED", [
            f"requires at least {MIN_ROWS} rows and {MIN_RESETS} reset groups"
        ]
    if float(label_entropy) < LABEL_ENTROPY_MIN:
        reasons.append(
            f"normalized label entropy {label_entropy:.6f} is below {LABEL_ENTROPY_MIN}"
        )
    if float(active_mean) < ACTIVE_MEAN_MIN:
        reasons.append(
            f"active mean {active_mean:.6f} is below {ACTIVE_MEAN_MIN} nats"
        )
    if float(minimum_skill_mean) < PER_SKILL_MEAN_MIN:
        reasons.append(
            f"minimum skill mean {minimum_skill_mean:.6f} is below "
            f"{PER_SKILL_MEAN_MIN} nats"
        )
    if float(active_minus_sham_lower) <= 0.0:
        reasons.append("active-minus-sham bootstrap lower bound is not positive")
    if abs(float(inactive_max_abs)) > INACTIVE_ABS_MAX:
        reasons.append(
            f"inactive control {inactive_max_abs:.3e} exceeds {INACTIVE_ABS_MAX:.1e}"
        )
    return ("PASS" if not reasons else "FAIL"), reasons


def classify_family(reports: list[dict[str, object]]) -> tuple[str, str, str]:
    by_id = {str(report.get("checkpoint_id")): report for report in reports}
    required = {"arm0_update25", "arm0_update30", "arm0_final"}
    if set(by_id) != required:
        return "INVALID", "INVALID_CHECKPOINT_FAMILY", "repair report membership only"
    statuses = [str(by_id[name].get("status")) for name in sorted(required)]
    if "INVALID" in statuses:
        return "INVALID", "INVALID_CHECKPOINT_EVIDENCE", "repair invalid evidence only"
    if "UNDERPOWERED" in statuses:
        return (
            "UNDERPOWERED",
            "UNDERPOWERED_ACTION_INFORMATION",
            "add support under the unchanged contract",
        )
    pass_count = statuses.count("PASS")
    if pass_count >= 2 and str(by_id["arm0_final"].get("status")) == "PASS":
        return (
            "PASS",
            "PASS_COUNTERFACTUAL_ACTION_INFORMATION_TARGET",
            "design a bounded PPO integration smoke for the density-ratio reward",
        )
    return (
        "FAIL",
        "FAIL_WEAK_ACTION_INFORMATION_TARGET",
        "retire the individual action-information target family",
    )
