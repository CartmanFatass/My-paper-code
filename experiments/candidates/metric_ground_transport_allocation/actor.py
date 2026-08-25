"""Frozen equal-class MGTAP actors."""

from __future__ import annotations

import math

import numpy as np
import torch

from .config import DISPLAYED_COORDINATES, ROLE_COORDINATES


HADAMARD = np.asarray([
    [1,1,1,1,1,1,1,1], [1,-1,1,-1,1,-1,1,-1],
    [1,1,-1,-1,1,1,-1,-1], [1,-1,-1,1,1,-1,-1,1],
    [1,1,1,1,-1,-1,-1,-1], [1,-1,1,-1,-1,1,-1,1],
    [1,1,-1,-1,-1,-1,1,1], [1,-1,-1,1,-1,1,1,-1],
], dtype=np.float64) / math.sqrt(8.0)


def metric_map(binding: str) -> np.ndarray:
    descriptors = [(x, z) for x in ROLE_COORDINATES for z in DISPLAYED_COORDINATES[binding]]
    s = np.zeros((8, 8), dtype=np.float64)
    for i, (x, z) in enumerate(descriptors):
        for j, (xx, zz) in enumerate(descriptors):
            if i != j:
                s[i, j] = 2.0 ** (-(abs(x - xx) + abs(z - zz)))
    g = s / s.sum(axis=1).max()
    return np.eye(8, dtype=np.float64) + 0.5 * g


def edge_map(arm: str, binding: str) -> np.ndarray:
    return metric_map(binding) if arm == "METRIC" else HADAMARD.copy()


class Actor(torch.nn.Module):
    def __init__(self, arm: str, binding: str) -> None:
        super().__init__()
        self.arm = arm
        self.binding = binding
        self.W = torch.nn.Parameter(torch.zeros((8, 6), dtype=torch.float64))
        self.V = torch.nn.Parameter(torch.zeros((2, 6), dtype=torch.float64))
        self.register_buffer("B", torch.as_tensor(edge_map(arm, binding), dtype=torch.float64))

    def scores(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        raw = features @ self.W.T
        mapped = raw @ self.B.T
        idle = features @ self.V.T
        return raw, mapped, idle

    def parameter_vector(self) -> np.ndarray:
        return np.concatenate((self.W.detach().cpu().numpy().ravel(), self.V.detach().cpu().numpy().ravel()))

    def load_parameter_vector(self, vector: np.ndarray) -> None:
        if vector.shape != (60,):
            raise ValueError(vector.shape)
        with torch.no_grad():
            self.W.copy_(torch.as_tensor(vector[:48].reshape(8, 6), dtype=torch.float64))
            self.V.copy_(torch.as_tensor(vector[48:].reshape(2, 6), dtype=torch.float64))
