"""Reporting-only exact immediate ring oracle with constant action width."""

from __future__ import annotations

import itertools

import torch


def immediate_ring_oracle_batched(volumes: torch.Tensor, signals: torch.Tensor, successor: torch.Tensor) -> torch.Tensor:
    """Exact O(N*3^3) ring DP vectorized across independent ticks (or batch rows)."""
    n = volumes.numel()
    order = [0]
    for _ in range(1, n):
        order.append(int(successor[order[-1]].item()))
    v, s = volumes[order], signals[:, order]
    effort = volumes.new_tensor((0.0, 0.5, 1.0))

    def term(index: int, left: int, centre: int, right: int) -> torch.Tensor:
        service = effort[centre] + 0.5 * effort[left] + 0.5 * effort[right]
        return v[index] * s[:, index] * (1.0 - torch.exp(-service)) - 0.08 * v[index] * effort[centre].square()

    optimum: torch.Tensor | None = None
    for first, second in itertools.product(range(3), repeat=2):
        states: dict[tuple[int, int], torch.Tensor] = {(first, second): s.new_zeros((s.shape[0],))}
        for right_index in range(2, n):
            updated: dict[tuple[int, int], torch.Tensor] = {}
            for (left, centre), value in states.items():
                for right in range(3):
                    candidate = value + term(right_index - 1, left, centre, right)
                    state = (centre, right)
                    updated[state] = candidate if state not in updated else torch.maximum(updated[state], candidate)
            states = updated
        for (left, centre), value in states.items():
            candidate = value + term(n - 1, left, centre, first) + term(0, centre, first, second)
            optimum = candidate if optimum is None else torch.maximum(optimum, candidate)
    assert optimum is not None
    return optimum


def immediate_ring_oracle(volumes: torch.Tensor, signal: torch.Tensor, successor: torch.Tensor) -> torch.Tensor:
    """One-tick compatibility wrapper around the batched exact dynamic program."""
    return immediate_ring_oracle_batched(volumes, signal.unsqueeze(0), successor).squeeze(0)
