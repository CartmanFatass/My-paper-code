"""Periodic geometry and the registered explicit-volume port interventions."""

from __future__ import annotations

import math

import torch


def wrap_signed(delta: torch.Tensor) -> torch.Tensor:
    """Map a displacement to the frozen interval [-1/2, 1/2)."""
    return torch.remainder(delta + 0.5, 1.0) - 0.5


def periodic_geometry(gaps: torch.Tensor, rotation: torch.Tensor, handle_permutation: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return handle-indexed positions, cells, links, and the internal cyclic rank."""
    n = gaps.numel()
    cyclic_x = torch.remainder(rotation + torch.cat((gaps.new_zeros(1), torch.cumsum(gaps[:-1], 0))), 1.0)
    cyclic_v = 0.5 * (torch.roll(gaps, 1) + gaps)
    positions = torch.empty_like(cyclic_x)
    volumes = torch.empty_like(cyclic_v)
    positions[handle_permutation] = cyclic_x
    volumes[handle_permutation] = cyclic_v
    ranks_to_handle = handle_permutation
    prev = torch.empty(n, dtype=torch.long, device=gaps.device)
    nxt = torch.empty(n, dtype=torch.long, device=gaps.device)
    prev[ranks_to_handle] = torch.roll(ranks_to_handle, 1)
    nxt[ranks_to_handle] = torch.roll(ranks_to_handle, -1)
    cyclic_rank = torch.empty(n, dtype=torch.long, device=gaps.device)
    cyclic_rank[ranks_to_handle] = torch.arange(n, device=gaps.device)
    return positions, volumes, prev, nxt, cyclic_rank


def triplet_indices(prev: torch.Tensor, nxt: torch.Tensor) -> torch.Tensor:
    """Rows are receiver handles and columns are PREV, SELF, NEXT."""
    self_index = torch.arange(prev.numel(), device=prev.device)
    return torch.stack((prev, self_index, nxt), dim=-1)


def shifted_volumes(volumes: torch.Tensor, triplets: torch.Tensor, episode_index: int) -> torch.Tensor:
    """The registered forward/inverse cyclic reassociation at the weight port."""
    incoming = volumes[triplets]
    order = (2, 0, 1) if episode_index % 2 == 0 else (1, 2, 0)
    return incoming[:, order]


def restore_volumes(volumes: torch.Tensor, triplets: torch.Tensor, episode_index: int) -> torch.Tensor:
    """Exact inverse of :func:`shifted_volumes`, used only by IDENTITY-RESTORE."""
    shifted = shifted_volumes(volumes, triplets, episode_index)
    inverse = (1, 2, 0) if episode_index % 2 == 0 else (2, 0, 1)
    return shifted[:, inverse]


def rotation_matrix(x: torch.Tensor) -> torch.Tensor:
    phase = 2.0 * math.pi * x
    return torch.stack((torch.sin(phase), torch.cos(phase)), dim=-1)
