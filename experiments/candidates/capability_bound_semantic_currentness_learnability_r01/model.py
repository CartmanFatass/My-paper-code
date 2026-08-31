"""Common dense FP32 learner shape for all CBSC-LR01 arms."""

from __future__ import annotations

import torch
from torch import nn

from .contract import ACTIVE_PARAMETERS, HIDDEN_WIDTHS, INPUT_BITS, OUTPUTS


class DenseLearner(nn.Module):
    """The sole 112→160→128→32→16→3 ReLU architecture."""

    def __init__(self) -> None:
        super().__init__()
        widths = (INPUT_BITS, *HIDDEN_WIDTHS, OUTPUTS)
        self.layers = nn.ModuleList(
            nn.Linear(left, right, bias=True, dtype=torch.float32)
            for left, right in zip(widths, widths[1:])
        )
        if sum(parameter.numel() for parameter in self.parameters()) != ACTIVE_PARAMETERS:
            raise RuntimeError("CBSC-LR01 learner parameter count changed")

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        value = inputs.to(dtype=torch.float32)
        for layer in self.layers[:-1]:
            value = torch.relu(layer(value))
        return self.layers[-1](value)

    def zero_output_head(self) -> None:
        with torch.no_grad():
            self.layers[-1].weight.zero_()
            self.layers[-1].bias.zero_()


__all__ = ["DenseLearner"]
