"""Binary, action-marginalized PPO credit and its factual comparator.

These functions do not construct environments, load weights, or optimize models.
Returns include the whole suffix on EACH branch's own subsequent history. They
must not be obtained by replaying one branch's future commands on the other.
"""

from __future__ import annotations

import math

import torch
from torch.nn import functional as F


def _validate(
    new_logits: torch.Tensor,
    old_logits: torch.Tensor,
    eligible: torch.Tensor,
    clip: float,
    multiplier: float,
) -> None:
    if new_logits.ndim != 1 or new_logits.numel() == 0:
        raise ValueError("one logit per scheduled pair is required")
    if old_logits.shape != new_logits.shape or eligible.shape != new_logits.shape:
        raise ValueError("logits and eligibility must have the same shape")
    if eligible.dtype != torch.bool:
        raise TypeError("eligibility must be boolean")
    if not math.isfinite(clip) or not 0 < clip < 1:
        raise ValueError("clip must be finite and between zero and one")
    if not math.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("sampling multiplier must be finite and positive")
    for name, tensor in (("new logits", new_logits), ("old logits", old_logits)):
        if not tensor.is_floating_point() or not bool(torch.isfinite(tensor).all()):
            raise ValueError(f"{name} must be finite floating point values")
        if tensor.device != new_logits.device or tensor.dtype != new_logits.dtype:
            raise TypeError("both logit arrays must share dtype and device")
    if eligible.device != new_logits.device:
        raise ValueError("eligibility and logits must share a device")
    old_p = old_logits.detach().sigmoid()
    if not bool(((old_p > 0) & (old_p < 1)).all()):
        raise ValueError("old policy has numerically lost binary support")


def _target(value: torch.Tensor, like: torch.Tensor, shape: tuple[int, ...]) -> torch.Tensor:
    if value.shape != shape or value.dtype != like.dtype or value.device != like.device:
        raise ValueError("target shape, dtype and device must match the stated contract")
    if not bool(torch.isfinite(value).all()):
        raise ValueError("targets must be finite")
    return value.detach()


def _clipped(ratio: torch.Tensor, advantage: torch.Tensor, clip: float) -> torch.Tensor:
    return torch.minimum(ratio * advantage, ratio.clamp(1 - clip, 1 + clip) * advantage)


def paired_surrogate(
    new_logits: torch.Tensor,
    old_logits: torch.Tensor,
    keep_minus_end: torch.Tensor,
    eligible: torch.Tensor,
    *,
    clip: float = 0.2,
    multiplier: float = 1.0,
) -> torch.Tensor:
    """Return a maximization objective, averaging over ALL scheduled pairs.

    Old probabilities, suffix differences and eligibility are fixed targets.
    At new == old its derivative with respect to the logit is p(1-p) delta,
    times multiplier / number of scheduled pairs. Ineligible rows contribute
    zero but stay in the denominator. Repeated clipped epochs are a surrogate,
    not an unbiased policy-gradient or policy-improvement guarantee.
    """
    _validate(new_logits, old_logits, eligible, clip, multiplier)
    old = old_logits.detach()
    delta = _target(keep_minus_end, new_logits, tuple(new_logits.shape))
    probability = old.sigmoid()
    keep_advantage = (1 - probability) * delta
    end_advantage = -probability * delta
    keep_ratio = torch.exp(F.logsigmoid(new_logits) - F.logsigmoid(old))
    end_ratio = torch.exp(F.logsigmoid(-new_logits) - F.logsigmoid(-old))
    objective = (
        probability * _clipped(keep_ratio, keep_advantage, clip)
        + (1 - probability) * _clipped(end_ratio, end_advantage, clip)
    )
    return multiplier * torch.where(eligible, objective, 0.0).mean()


def factual_surrogate(
    new_logits: torch.Tensor,
    old_logits: torch.Tensor,
    sampled_keep: torch.Tensor,
    suffix_returns: torch.Tensor,
    baseline: torch.Tensor,
    eligible: torch.Tensor,
    *,
    clip: float = 0.2,
    multiplier: float = 1.0,
) -> torch.Tensor:
    """Two factual rollouts per pair, with independent focal Bernoulli draws.

    A common action-independent baseline is evaluated before either rollout's
    outcomes train the critic. All other policy coins are common within the
    pair. This has the same first-update expectation as paired_surrogate;
    its clipped later-epoch objective need not be the same.
    """
    _validate(new_logits, old_logits, eligible, clip, multiplier)
    shape = (new_logits.numel(), 2)
    returns = _target(suffix_returns, new_logits, shape)
    value = _target(baseline, new_logits, tuple(new_logits.shape))
    if sampled_keep.shape != shape or sampled_keep.dtype != torch.bool:
        raise TypeError("two boolean factual decisions are required per pair")
    if sampled_keep.device != new_logits.device:
        raise ValueError("factual decisions and logits must share a device")
    new = new_logits[:, None]
    old = old_logits.detach()[:, None]
    logp = torch.where(sampled_keep, F.logsigmoid(new), F.logsigmoid(-new))
    old_logp = torch.where(sampled_keep, F.logsigmoid(old), F.logsigmoid(-old))
    ratio = torch.exp(logp - old_logp)
    objective = _clipped(ratio, returns - value[:, None], clip).mean(dim=1)
    return multiplier * torch.where(eligible, objective, 0.0).mean()
