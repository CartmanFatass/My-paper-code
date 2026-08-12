"""The frozen noise-free one-dimensional periodic field-service host."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

import torch

from .geometry import periodic_geometry, triplet_indices
from .rng import CounterRNG

Regime = Literal["IID", "CLUSTER", "EQUAL"]
EFFORTS = torch.tensor((0.0, 0.5, 1.0), dtype=torch.float32)


@dataclass(slots=True)
class Episode:
    """Episode exogenous state.  Positions and graph never change within it."""

    n: int
    regime: Regime
    positions: torch.Tensor
    volumes: torch.Tensor
    predecessor: torch.Tensor
    successor: torch.Tensor
    cyclic_rank: torch.Tensor
    phi1: torch.Tensor
    phi2: torch.Tensor
    omega1: float
    omega2: float
    conflict: bool = False
    constant_field: bool = False
    t: int = 0

    @property
    def triplets(self) -> torch.Tensor:
        return triplet_indices(self.predecessor, self.successor)

    @property
    def gaps(self) -> torch.Tensor:
        # g_i is the clockwise gap from agent i to its cyclic successor.
        return torch.remainder(self.positions[self.successor] - self.positions, 1.0)

    def _ordinary_density(self, x: torch.Tensor, tick: int) -> torch.Tensor:
        theta1 = self.phi1 + self.omega1 * tick
        theta2 = self.phi2 + self.omega2 * tick
        return (0.55 + 0.25 * torch.cos(2 * math.pi * (x - theta1))
                + 0.15 * torch.cos(4 * math.pi * (x - theta2)))

    def _conflict_centers(self) -> tuple[torch.Tensor, torch.Tensor]:
        # Exact comparison comes first; cyclic rank resolves only an exact numerical tie.
        largest_value, smallest_value = self.volumes.max(), self.volumes.min()
        largest_rank = torch.where(self.volumes == largest_value, self.cyclic_rank,
                                   torch.full_like(self.cyclic_rank, self.n)).min()
        smallest_rank = torch.where(self.volumes == smallest_value, self.cyclic_rank,
                                    torch.full_like(self.cyclic_rank, self.n)).min()
        largest = torch.nonzero(self.cyclic_rank == largest_rank, as_tuple=False).squeeze()
        smallest = torch.nonzero(self.cyclic_rank == smallest_rank, as_tuple=False).squeeze()
        # C_i runs between adjacent midpoints, so its exact midpoint is x_i+(g_i-g_(i-1))/4.
        centers = torch.remainder(self.positions + 0.25 * (self.gaps - self.gaps[self.predecessor]), 1.0)
        return centers[largest], centers[smallest]

    def density(self, x: torch.Tensor, tick: int | None = None) -> torch.Tensor:
        tick = self.t if tick is None else tick
        if self.constant_field:
            return torch.full_like(x, 0.55)
        if self.conflict:
            c_max, c_min = self._conflict_centers()
            return (0.55 + 0.30 * torch.cos(2 * math.pi * (x - c_max))
                    - 0.15 * torch.cos(2 * math.pi * (x - c_min)))
        return self._ordinary_density(x, tick)

    def cell_averages(self, tick: int | None = None) -> torch.Tensor:
        """Analytic interval averages using the periodic sine antiderivative."""
        tick = self.t if tick is None else tick
        left = self.positions - 0.5 * self.gaps[self.predecessor]
        right = self.positions + 0.5 * self.gaps
        if self.constant_field:
            return torch.full_like(self.volumes, 0.55)
        if self.conflict:
            c_max, c_min = self._conflict_centers()
            integral = (0.55 * (right - left)
                        + 0.30 * (torch.sin(2 * math.pi * (right - c_max)) - torch.sin(2 * math.pi * (left - c_max))) / (2 * math.pi)
                        - 0.15 * (torch.sin(2 * math.pi * (right - c_min)) - torch.sin(2 * math.pi * (left - c_min))) / (2 * math.pi))
        else:
            theta1 = self.phi1 + self.omega1 * tick
            theta2 = self.phi2 + self.omega2 * tick
            integral = (0.55 * (right - left)
                        + 0.25 * (torch.sin(2 * math.pi * (right - theta1)) - torch.sin(2 * math.pi * (left - theta1))) / (2 * math.pi)
                        + 0.15 * (torch.sin(4 * math.pi * (right - theta2)) - torch.sin(4 * math.pi * (left - theta2))) / (4 * math.pi))
        return integral / self.volumes

    def reward(self, efforts: torch.Tensor, tick: int | None = None) -> torch.Tensor:
        s = self.cell_averages(tick)
        service = efforts + 0.5 * efforts[self.predecessor] + 0.5 * efforts[self.successor]
        return torch.sum(self.volumes * s * (1.0 - torch.exp(-service))) - 0.08 * torch.sum(self.volumes * efforts.square())

    def oracle_reward(self, tick: int | None = None) -> torch.Tensor:
        """Exact width-three ring DP, never exposed to actor or optimizer."""
        # Local import avoids a host/oracle import cycle at module initialization.
        from .oracle import immediate_ring_oracle
        return immediate_ring_oracle(self.volumes, self.cell_averages(tick), self.successor)

    def oracle_rewards(self) -> torch.Tensor:
        """All 32 reporting-only oracle values, one vectorized ring-DP invocation."""
        from .oracle import immediate_ring_oracle_batched
        signals = torch.stack([self.cell_averages(tick) for tick in range(32)])
        return immediate_ring_oracle_batched(self.volumes, signals, self.successor)


def make_episode(n: int, regime: Regime, rng: CounterRNG, *, conflict: bool = False, constant_field: bool = False, device: torch.device | None = None) -> Episode:
    """Draw the exact once-per-episode geometry, field phase, and opaque handles."""
    if regime == "EQUAL":
        gaps = torch.full((n,), 1.0 / n, dtype=torch.float32, device=device)
    else:
        alpha = 1.0 if regime == "IID" else 0.25
        raw = rng.gamma((n,), alpha, "raw_gaps", device=device)
        gaps = 0.05 / n + 0.95 * raw / raw.sum()
    rotation = rng.uniform((), "rotation", device=device)
    handles = rng.permutation(n, "handle_permutation", device=device)
    positions, volumes, prev, nxt, cyclic_rank = periodic_geometry(gaps, rotation, handles)
    if not bool(torch.all(volumes > 0.0)) or not bool(torch.isclose(volumes.sum(), volumes.new_tensor(1.0), atol=1e-6, rtol=1e-6)):
        raise RuntimeError("registered periodic Voronoi volume identity failed")
    phi1 = rng.uniform((), "phi1", device=device)
    phi2 = rng.uniform((), "phi2", device=device)
    omega1 = -1.0 / 128.0 if rng.numpy("omega1").integers(2) == 0 else 1.0 / 128.0
    omega2 = -1.0 / 256.0 if rng.numpy("omega2").integers(2) == 0 else 1.0 / 256.0
    return Episode(n, regime, positions, volumes, prev, nxt, cyclic_rank, phi1, phi2, omega1, omega2, conflict, constant_field)
