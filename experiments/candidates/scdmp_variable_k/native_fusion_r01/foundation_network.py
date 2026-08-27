"""Order-erased actor/critic construction under deterministic S1 fixtures."""

from __future__ import annotations

import math

import torch
from torch import Tensor, nn

from .foundation_contract import ACTOR_WIDTHS, CRITIC_WIDTHS, OBSERVATION_WIDTH


class _OrderErasedMLP(nn.Module):
    def __init__(self, widths: tuple[int, ...], *, scalar_output: bool) -> None:
        super().__init__()
        self.widths = widths
        self.scalar_output = scalar_output
        self.layers = nn.ModuleList(
            nn.Linear(source, target, bias=True, dtype=torch.float32)
            for source, target in zip(widths, widths[1:])
        )
        self._initialize_from_midpoint_fixture()

    def _initialize_from_midpoint_fixture(self) -> None:
        with torch.no_grad():
            for layer in self.layers:
                count = layer.weight.numel()
                fractions = (
                    torch.arange(count, dtype=torch.float32) + torch.tensor(0.5)
                ) / float(count)
                bound = math.sqrt(6.0 / (layer.in_features + layer.out_features))
                values = (2.0 * fractions - 1.0) * bound
                layer.weight.copy_(values.reshape_as(layer.weight))
                layer.bias.zero_()

    def forward(self, observation: Tensor) -> Tensor:
        if observation.dtype is not torch.float32:
            raise ValueError("foundation input must be float32")
        if observation.ndim < 1 or observation.shape[-1] != OBSERVATION_WIDTH:
            raise ValueError("foundation requires exactly 14 order-erased inputs")
        value = observation
        for layer in self.layers[:-1]:
            value = torch.nn.functional.silu(layer(value))
        value = self.layers[-1](value)
        return value.squeeze(-1) if self.scalar_output else value


class FoundationActor(_OrderErasedMLP):
    def __init__(self) -> None:
        super().__init__(ACTOR_WIDTHS, scalar_output=False)


class FoundationCritic(_OrderErasedMLP):
    def __init__(self) -> None:
        super().__init__(CRITIC_WIDTHS, scalar_output=True)


class TechnicalFoundation(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.actor = FoundationActor()
        self.critic = FoundationCritic()


def build_technical_foundation() -> TechnicalFoundation:
    """Build nonregistered construction-fixture tensors without RNG activity."""

    return TechnicalFoundation()
