"""Stateless helpers owned by the variable-roster event runtime."""

from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn


ORDINARY_BOUNDARY = "ordinary_opportunity"
ROLLOUT_TRUNCATION = "rollout_truncation"
TEMPORARY_BOUNDARY = "temporary_pre_removal_leave"
TERMINAL_BOUNDARY = "terminal_boundary"
BOUNDARY_KINDS = (
    ORDINARY_BOUNDARY,
    ROLLOUT_TRUNCATION,
    TEMPORARY_BOUNDARY,
    TERMINAL_BOUNDARY,
)


def _state_dict_shapes(module: nn.Module) -> dict[str, tuple[int, ...]]:
    return {name: tuple(tensor.shape) for name, tensor in module.state_dict().items()}


def parameter_count(module: nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in module.parameters()))


def normalized_log_age(ages: torch.Tensor) -> torch.Tensor:
    return torch.log1p(torch.clamp(ages.float(), min=0.0)) / math.log1p(500.0)


def make_pcg64_rng(master_seed: int, episode_id: int, stream_id: int) -> np.random.Generator:
    """Construct one frozen ledger stream without folding or secondary seeding."""

    return np.random.Generator(
        np.random.PCG64(
            np.random.SeedSequence(
                [int(master_seed), int(episode_id), int(stream_id)]
            )
        )
    )


def inverse_cdf_action(probabilities: np.ndarray, uniform: float) -> int:
    values = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if values.size <= 0 or not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError("categorical probabilities are invalid")
    total = float(values.sum())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("categorical probability mass must be positive")
    normalized = values / total
    draw = float(uniform)
    if not 0.0 <= draw < 1.0:
        raise ValueError("inverse-CDF uniform must lie in [0,1)")
    return min(int(np.searchsorted(np.cumsum(normalized), draw, side="right")), values.size - 1)
