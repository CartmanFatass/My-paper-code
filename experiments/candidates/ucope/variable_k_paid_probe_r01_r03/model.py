"""Exact-shaped ordinary-FP32 scorer and baseline for retained S0/S1 use."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import torch
from torch import nn

from . import native_backend


class ActionScorer(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(13, 64, bias=True),
            nn.ReLU(),
            nn.Linear(64, 64, bias=True),
            nn.ReLU(),
            nn.Linear(64, 1, bias=True),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        if features.dtype != torch.float32 or features.shape[-1] != 13:
            raise TypeError("scorer features must be ordinary FP32 with final width 13")
        return self.network(features).squeeze(-1)


class StateBaseline(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(9, 32, bias=True),
            nn.ReLU(),
            nn.Linear(32, 1, bias=True),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        if features.dtype != torch.float32 or features.shape[-1] != 9:
            raise TypeError("baseline features must be ordinary FP32 with final width 9")
        return self.network(features).squeeze(-1)


@dataclass
class LearnerBundle:
    scorer: ActionScorer
    baseline: StateBaseline
    optimizer: torch.optim.AdamW

    def parameters(self) -> Iterable[torch.nn.Parameter]:
        return tuple(self.scorer.parameters()) + tuple(self.baseline.parameters())


def _initialize_network(
    module: nn.Module, *, seed: int, panel: int, network: int,
    build_root: Path | None,
) -> None:
    draw_count = sum(
        layer.weight.numel() for layer in module.modules() if isinstance(layer, nn.Linear)
    )
    draws = native_backend.init_uniforms(
        seed=seed, panel=panel, network=network, count=draw_count,
        build_root=build_root,
    )
    coordinate = 0
    with torch.no_grad():
        for layer in module.modules():
            if not isinstance(layer, nn.Linear):
                continue
            limit = np.float32(math.sqrt(6.0 / (layer.in_features + layer.out_features)))
            values = np.empty(layer.weight.numel(), dtype=np.float32)
            for index in range(values.size):
                draw = draws[coordinate]
                values[index] = np.float32((np.float32(2.0) * draw - np.float32(1.0)) * limit)
                coordinate += 1
            layer.weight.copy_(torch.from_numpy(values.reshape(tuple(layer.weight.shape))))
            layer.bias.zero_()


def make_paired_bundles(
    *, seed: int, panel: int, arm_count: int = 3,
    build_root: Path | None = None,
) -> list[LearnerBundle]:
    scorer_template = ActionScorer().to(dtype=torch.float32)
    baseline_template = StateBaseline().to(dtype=torch.float32)
    _initialize_network(
        scorer_template, seed=seed, panel=panel, network=0,
        build_root=build_root,
    )
    _initialize_network(
        baseline_template, seed=seed, panel=panel, network=1,
        build_root=build_root,
    )
    if sum(parameter.numel() for parameter in scorer_template.parameters()) != 5121:
        raise RuntimeError("scorer parameter shape drift")
    if sum(parameter.numel() for parameter in baseline_template.parameters()) != 353:
        raise RuntimeError("baseline parameter shape drift")
    bundles: list[LearnerBundle] = []
    for _ in range(arm_count):
        scorer = ActionScorer().to(dtype=torch.float32)
        baseline = StateBaseline().to(dtype=torch.float32)
        scorer.load_state_dict(scorer_template.state_dict())
        baseline.load_state_dict(baseline_template.state_dict())
        parameters = list(scorer.parameters()) + list(baseline.parameters())
        optimizer = torch.optim.AdamW(
            parameters, lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4
        )
        bundles.append(LearnerBundle(scorer, baseline, optimizer))
    return bundles


def update_bundle(
    bundle: LearnerBundle, *, root_features: torch.Tensor, root_baseline: torch.Tensor,
    root_actions: torch.Tensor, root_returns: torch.Tensor,
    tail_features: torch.Tensor, tail_baseline: torch.Tensor,
    tail_actions: torch.Tensor, tail_returns: torch.Tensor,
    probe_mask: torch.Tensor, batch_number: int,
) -> dict[str, float]:
    # Compatibility seam for the retained S0 coupon; S1 owns the frozen law.
    from .training import frozen_update

    return frozen_update(
        bundle,
        root_features=root_features,
        root_baseline=root_baseline,
        root_actions=root_actions,
        root_returns=root_returns,
        tail_features=tail_features,
        tail_baseline=tail_baseline,
        tail_actions=tail_actions,
        tail_returns=tail_returns,
        probe_mask=probe_mask,
        batch_number=batch_number,
    )
