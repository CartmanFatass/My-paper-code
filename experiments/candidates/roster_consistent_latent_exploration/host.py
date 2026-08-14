from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .authorization import ProductionPermit, require_active_permit
from .config import EVAL_SIZES, REGISTERED
from .rng import generator, uniform


@dataclass(frozen=True)
class Roster:
    xi: float
    x: np.ndarray
    mu: float
    bins: np.ndarray
    row_permutation: np.ndarray
    proposal_count: int


@dataclass(frozen=True)
class Outcome:
    routes: np.ndarray
    rotations: np.ndarray
    fractions: np.ndarray
    valid: bool
    winning_rotation: int | None
    agreement: float
    reward: int
    max_tie: bool


def relative_bins(x: np.ndarray, mu: float | None = None) -> np.ndarray:
    values = np.asarray(x, dtype=np.float64)
    center = float(values.mean(dtype=np.float64)) if mu is None else float(mu)
    return np.select(
        (values < center / 2.0, values < center, values < (1.0 + center) / 2.0),
        (0, 1, 2),
        default=3,
    ).astype(np.int64)


def roster_accepted(bins: np.ndarray) -> bool:
    counts = np.bincount(np.asarray(bins, dtype=np.int64), minlength=4)
    return bool(counts.max(initial=0) <= len(bins) / 2.0)


def make_roster(
    permit: ProductionPermit, phase: str, seed: int, n: int, *coordinate: object,
) -> Roster:
    require_active_permit(permit)
    if n not in EVAL_SIZES:
        raise ValueError("N must be one of 4, 8, 12")
    xi = 0.3 + 0.4 * uniform(permit, phase, seed, n, *coordinate, "xi")
    accepted_x: np.ndarray | None = None
    accepted_bins: np.ndarray | None = None
    proposal_count = 0
    for proposal in range(REGISTERED.max_roster_proposals):
        proposal_count = proposal + 1
        draw = generator(
            permit, phase, seed, n, *coordinate, "roster_proposal", proposal,
        ).beta(8.0 * xi, 8.0 * (1.0 - xi), size=n).astype(np.float64, copy=False)
        mu = float(draw.mean(dtype=np.float64))
        bins = relative_bins(draw, mu)
        if roster_accepted(bins):
            accepted_x, accepted_bins = draw, bins
            break
    if accepted_x is None or accepted_bins is None:
        raise RuntimeError("accepted roster absent after 4096 proposals")
    mu = float(accepted_x.mean(dtype=np.float64))
    order = generator(
        permit, phase, seed, n, *coordinate, "row_permutation",
    ).permutation(n).astype(np.int64, copy=False)
    return Roster(
        xi=xi,
        x=accepted_x[order].copy(),
        mu=mu,
        bins=accepted_bins[order].copy(),
        row_permutation=order.copy(),
        proposal_count=proposal_count,
    )


def evaluate_actions(
    bins: np.ndarray, first_actions: np.ndarray, second_actions: np.ndarray, hidden_lock: int,
) -> Outcome:
    base = np.asarray(bins, dtype=np.int64)
    a1 = np.asarray(first_actions, dtype=np.int64)
    a2 = np.asarray(second_actions, dtype=np.int64)
    if not (base.shape == a1.shape == a2.shape):
        raise ValueError("bins and both action phases must have identical shape")
    if hidden_lock not in range(4) or np.any((a1 < 0) | (a1 > 1) | (a2 < 0) | (a2 > 1)):
        raise ValueError("invalid action or lock")
    routes = 2 * a1 + a2
    rotations = (routes - base) % 4
    counts = np.bincount(rotations, minlength=4)
    fractions = counts.astype(np.float64) / float(len(base))
    maximum = float(fractions.max(initial=0.0))
    winners = np.flatnonzero(fractions == maximum)
    valid = maximum >= 0.75
    winner = int(winners[0]) if valid else None
    return Outcome(
        routes=routes,
        rotations=rotations,
        fractions=fractions,
        valid=valid,
        winning_rotation=winner,
        agreement=maximum,
        reward=int(valid and winner == hidden_lock),
        max_tie=len(winners) > 1,
    )


def scripted_codebook_actions(bins: np.ndarray, latent: int) -> tuple[np.ndarray, np.ndarray]:
    routes = (np.asarray(bins, dtype=np.int64) + int(latent)) % 4
    return routes // 2, routes % 2


def scripted_collapse_actions(bins: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    routes = np.asarray(bins, dtype=np.int64)
    return routes // 2, routes % 2
