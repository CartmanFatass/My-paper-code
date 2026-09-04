"""The two frozen 32-scalar critics."""

from __future__ import annotations

import torch
from torch import nn

from . import config as C


def _indices(content: torch.Tensor, action: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    return ((content + 1) // 2).long(), ((action + 1) // 2).long()


class GenericPair(nn.Module):
    name = "GENERIC_PAIR"
    layout = C.GENERIC_LAYOUT
    arithmetic_per_row = {"scalar_components": 2, "multiplies": 1, "adds": 1}

    def __init__(self, initial: torch.Tensor) -> None:
        super().__init__()
        self.theta = nn.Parameter(initial.detach().clone().to(dtype=torch.float32))

    def forward(self, source: torch.Tensor, content: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        content_index, action_index = _indices(content, action)
        t1 = self.theta[:16].view(4, 2, 2)
        t2 = self.theta[16:32].view(4, 2, 2)
        return 0.5 * (t1[source.long(), content_index, action_index] + t2[source.long(), content_index, action_index])


class AssociationFactor(nn.Module):
    name = "ASSOCIATION_FACTOR"
    layout = C.FACTOR_LAYOUT
    arithmetic_per_row = {"scalar_components": 2, "multiplies": 3, "adds": 4}

    def __init__(self, initial: torch.Tensor) -> None:
        super().__init__()
        self.theta = nn.Parameter(initial.detach().clone().to(dtype=torch.float32))

    def forward(self, source: torch.Tensor, content: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        content_index, action_index = _indices(content, action)
        u1 = self.theta[0:8].view(4, 2)
        v1 = self.theta[8:12].view(2, 2)
        u2 = self.theta[12:20].view(4, 2)
        v2 = self.theta[20:24].view(2, 2)
        b = self.theta[24:28]
        d = self.theta[28:30]
        e = self.theta[30:32]
        s = source.long()
        return (
            0.5
            * (
                u1[s, action_index] * v1[content_index, action_index]
                + u2[s, action_index] * v2[content_index, action_index]
            )
            + b[s]
            + d[content_index]
            + e[action_index]
        )
