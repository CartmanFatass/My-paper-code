from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .authorization import ProductionPermit, require_active_permit
from .config import ALL_SIZES, GRAPHON, REGIMES, ROLE_COORDINATES
from .rng import action_uniform, gaussian_member, orientation_uniform


@dataclass(frozen=True)
class World:
    phase: str
    seed: int
    n: int
    regime: str
    episode: int
    x: np.ndarray
    roles: np.ndarray
    coordinates: np.ndarray
    slots: np.ndarray
    handles: tuple[str, ...]
    targets: np.ndarray

    def permuted(self, order: np.ndarray) -> "World":
        idx = np.asarray(order, dtype=np.int64)
        return World(
            self.phase, self.seed, self.n, self.regime, self.episode,
            self.x[idx].copy(), self.roles[idx].copy(), self.coordinates[idx].copy(),
            self.slots[idx].copy(), tuple(self.handles[int(i)] for i in idx),
            self.targets[idx].copy(),
        )

    def action_uniforms(self, permit: ProductionPermit) -> np.ndarray:
        require_active_permit(permit)
        return np.asarray([
            action_uniform(
                permit, self.phase, self.seed, self.n, self.regime, self.episode,
                int(role), int(slot),
            )
            for role, slot in zip(self.roles, self.slots, strict=True)
        ], dtype=np.float64)


def nominal_handle(
    phase: str, seed: int, n: int, regime: str, episode: int,
    role: int, within_role_slot: int,
) -> str:
    """Deterministic equality-only record; never a draw or policy input."""
    return (
        f"Handle({phase},{seed},{n},{regime},{episode},{role},{within_role_slot})"
    )


def physical_dense_target_reference(x: np.ndarray, roles: np.ndarray) -> np.ndarray:
    """Fixed-small simulator truth only; never imported by a deployed policy."""
    n = int(x.shape[0])
    if n not in ALL_SIZES or roles.shape != (n,):
        raise ValueError("physical dense reference is confined to registered N<=16")
    field = np.zeros(n, dtype=np.float64)
    for i in range(n):
        for j in range(n):  # The registered self edge j == i is included.
            field[i] += float(GRAPHON[int(roles[i])][int(roles[j])]) * float(x[j])
        field[i] /= float(n)
    return (field >= 0.0).astype(np.int64)


def generate_world(
    permit: ProductionPermit, phase: str, seed: int, n: int, regime: str, episode: int,
) -> World:
    require_active_permit(permit)
    if phase not in ("training", "evaluation"):
        raise ValueError("phase must be training or evaluation")
    if n not in ALL_SIZES or n % 2:
        raise ValueError("SGSP B1 accepts exactly the registered even roster sizes")
    if regime not in REGIMES:
        raise ValueError(f"unknown regime: {regime}")
    if phase == "evaluation" and episode not in range(256):
        raise ValueError("evaluation episode must be 0..255")
    if phase == "training" and episode not in range(16 * 480):
        raise ValueError("training episode must be 0..7679")

    orientation = -1.0 if orientation_uniform(
        permit, phase, seed, n, regime, episode,
    ) < 0.5 else 1.0
    centers = (orientation, orientation if regime == "SAME" else -orientation)
    # Canonical base rows are deterministic lexicographic (role,slot).
    roles = np.repeat(np.asarray((0, 1), dtype=np.int64), n // 2)
    slots = np.tile(np.arange(n // 2, dtype=np.int64), 2)
    x = np.asarray([
        0.6 * centers[int(role)] + gaussian_member(
            permit, phase, seed, n, regime, episode, int(role), int(slot),
        )
        for role, slot in zip(roles, slots, strict=True)
    ], dtype=np.float64)
    coordinates = np.asarray([ROLE_COORDINATES[int(role)] for role in roles], dtype=np.float64)
    handles = tuple(
        nominal_handle(phase, seed, n, regime, episode, int(role), int(slot))
        for role, slot in zip(roles, slots, strict=True)
    )
    targets = physical_dense_target_reference(x, roles)
    return World(
        phase, seed, n, regime, episode, x, roles, coordinates, slots, handles, targets,
    )


def team_return(actions: np.ndarray, targets: np.ndarray) -> float:
    if actions.shape != targets.shape:
        raise ValueError("actions and targets must have identical agent shape")
    return float(np.mean(actions == targets, dtype=np.float64))
