"""Fixed FP64 stochastic targets and the shared FP64 soft cross entropy.

The 27-way normalization tolerance covers FP64 softmax/mixture rounding and
is deliberately stricter than the inherited decoder's generic 1e-12 check.
Accepted tiny score endpoint excursions are used unchanged, never clipped.
"""
from numbers import Integral

import numpy as np
import torch


TAU = .014
MIX = .1
MASS_ATOL = 5e-14
SCORE_ATOL = 1e-14


def _vector(value, name):
    if (not isinstance(value, np.ndarray) or value.shape != (27,)
            or value.dtype != np.dtype(np.float64) or not np.isfinite(value).all()):
        raise ValueError(name + " requires a finite NumPy FP64 vector27")


def _probabilities(value, name):
    _vector(value, name)
    if np.any(value < 0.) or abs(float(value.sum(dtype=np.float64)) - 1.) > MASS_ATOL:
        raise ValueError(name + " requires nonnegative normalized mass")


def build_targets(p, scores, c_index):
    """Return (T, H) without mutating the parent or broadening T's support.

    T = .9*p + .1*normalize(p*exp((scores-max(scores))/.014)).
    An exactly flat score vector returns p.copy() as T, bit for bit.
    H = .9*p + .1*one_hot(C), including when the parent's C mass is zero.
    """
    _probabilities(p, "parent")
    _vector(scores, "scores")
    if np.any(scores < -SCORE_ATOL) or np.any(scores > 1. + SCORE_ATOL):
        raise ValueError("scores require lawful [0,1] values within FP64 rounding")
    if (isinstance(c_index, (bool, np.bool_)) or not isinstance(c_index, Integral)
            or not 0 <= c_index < 27):
        raise ValueError("C index requires an integer in 0..26")
    if np.all(scores == scores[0]):
        target_t = p.copy()
    else:
        tilted = p * np.exp((scores - np.max(scores)) / TAU)
        total = float(tilted.sum(dtype=np.float64))
        if not np.isfinite(total) or total <= 0.:
            raise FloatingPointError("tilted parent has invalid mass")
        target_t = (1. - MIX) * p + MIX * (tilted / total)
    target_h = (1. - MIX) * p
    target_h[int(c_index)] += MIX
    _probabilities(target_t, "T")
    _probabilities(target_h, "H")
    return target_t, target_h


def soft_cross_entropy(logits, targets):
    """Mean row CE: FP32 CPU logits -> FP64 log_softmax with FP64 targets.

    Autograd casts the gradient back through the logits' FP32 conversion.
    Both arms use this same kernel; old FP32 hard CE is a different kernel.
    """
    if (not isinstance(logits, torch.Tensor) or logits.device.type != "cpu"
            or logits.dtype != torch.float32 or logits.ndim != 2
            or logits.shape[0] == 0 or logits.shape[1] != 27
            or not torch.isfinite(logits).all()):
        raise ValueError("logits require finite nonempty CPU FP32 Bx27")
    if (not isinstance(targets, torch.Tensor) or targets.device.type != "cpu"
            or targets.dtype != torch.float64 or targets.shape != logits.shape
            or not torch.isfinite(targets).all() or (targets < 0.).any()
            or ((targets.sum(dim=1) - 1.).abs() > MASS_ATOL).any()):
        raise ValueError("targets require normalized nonnegative CPU FP64 Bx27")
    log_probabilities = torch.log_softmax(logits.to(dtype=torch.float64), dim=1)
    loss = -(targets * log_probabilities).sum(dim=1).mean()
    if not torch.isfinite(loss):
        raise FloatingPointError("nonfinite soft cross entropy")
    return loss
