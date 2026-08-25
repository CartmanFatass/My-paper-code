"""Packet, lineage, HMM, analytic GLS, and potential-tape primitives."""

from __future__ import annotations

from dataclasses import dataclass
from math import atanh, sqrt, tanh
from typing import Iterable

import numpy as np

from .config import FLIP_HAZARD, MU, OVERLAP, Phase, QUALITY, RHO, STREAMS
from .rng import standard_normal, uniform


@dataclass(frozen=True, order=True)
class OriginKey:
    origin_id: int
    capture_tick: int


@dataclass(frozen=True)
class Packet:
    z: float
    origin_id: int
    capture_tick: int
    overlap_code: float
    valid_check: int = 1

    @property
    def key(self) -> OriginKey:
        return OriginKey(self.origin_id, self.capture_tick)

    @property
    def is_valid(self) -> bool:
        return self.valid_check in (1, 2)

    @property
    def is_null(self) -> bool:
        return self.valid_check == 2

    @classmethod
    def null(cls, overlap_code: float) -> "Packet":
        # Check code 2 is a valid, explicitly null row. It is transmitted and
        # counted but carries no evidence origin; code 0 remains invalid.
        return cls(0.0, 0, 0, overlap_code, 2)


class InvalidPacketTable(ValueError):
    pass


def quotient_new_rows(rows: Iterable[Packet], ledger: set[OriginKey]) -> tuple[list[Packet], set[OriginKey]]:
    """Quotient by immutable composite lineage, rejecting inconsistent copies."""
    by_key: dict[OriginKey, Packet] = {}
    for row in rows:
        if not row.is_valid or row.is_null:
            continue
        if not (0 <= row.origin_id <= 0xFFFFFFFF and 0 <= row.capture_tick <= 0xFFFF):
            raise InvalidPacketTable("lineage field outside fixed-width metadata range")
        prior = by_key.get(row.key)
        if prior is not None and (
            prior.z != row.z
            or prior.overlap_code != row.overlap_code
            or prior.valid_check != row.valid_check
        ):
            raise InvalidPacketTable("same origin_key has inconsistent payload")
        by_key[row.key] = row
    ordered = [by_key[key] for key in sorted(by_key) if key not in ledger]
    return ordered, ledger | {row.key for row in ordered}


def hmm_transition(ell: float, k: int) -> float:
    return 2.0 * atanh((1.0 - 2.0 * FLIP_HAZARD) ** k * tanh(ell / 2.0))


def analytic_q_j(values: np.ndarray, regime: str) -> tuple[float, float]:
    m = int(values.size)
    if m == 0:
        return 0.0, 0.0
    rho = 0.0 if m == 1 else RHO[regime]
    denominator = 1.0 + (m - 1) * rho
    return MU * float(np.sum(values)) / denominator, MU * MU * m / denominator


def batch_rows(
    seed: int,
    episode: int,
    physical_tick: int,
    n: int,
    regime: str,
    hidden_y: int,
) -> list[Packet]:
    """Create the nested potential batch without N/k/rho/arm in RNG addresses."""
    common = standard_normal(seed, Phase.EVAL, STREAMS["EVAL_COMMON"], episode, physical_tick)
    idios = [
        standard_normal(
            seed,
            Phase.EVAL,
            STREAMS["EVAL_IDIO"],
            episode,
            physical_tick * 16 + origin_index,
        )
        for origin_index in range(n)
    ]
    if regime == "DUP":
        z = MU * hidden_y + idios[0]
        return [Packet(z, 0, physical_tick, OVERLAP[regime]) for _ in range(n)]
    if regime == "CORR":
        values = [MU * hidden_y + sqrt(0.5) * common + sqrt(0.5) * value for value in idios]
    elif regime == "IND":
        values = [MU * hidden_y + value for value in idios]
    else:
        raise ValueError(f"unknown regime {regime}")
    return [Packet(value, i, physical_tick, OVERLAP[regime]) for i, value in enumerate(values)]


def latent_tape(seed: int, episode: int) -> tuple[int, ...]:
    y = 1 if uniform(seed, Phase.EVAL, STREAMS["EVAL_Y0"], episode, 0) >= 0.5 else -1
    values = [y]
    for tick in range(1, 31):
        if uniform(seed, Phase.EVAL, STREAMS["EVAL_FLIP"], episode, tick) < FLIP_HAZARD:
            y = -y
        values.append(y)
    return tuple(values)


def snapshot_residual(seed: int, cell_index: int, row_index: int, physical_tick: int, n: int, regime: str) -> np.ndarray:
    item = 768 * cell_index + row_index
    common = standard_normal(seed, Phase.TRAIN_SNAPSHOT, STREAMS["TRAIN_SNAPSHOT_COMMON"], item, physical_tick * 16)
    m = 1 if regime == "DUP" else n
    idios = np.asarray(
        [
            standard_normal(
                seed,
                Phase.TRAIN_SNAPSHOT,
                STREAMS["TRAIN_SNAPSHOT_IDIO"],
                item,
                physical_tick * 16 + origin_index,
            )
            for origin_index in range(m)
        ],
        dtype=np.float64,
    )
    if regime == "DUP":
        return idios
    if regime == "CORR":
        return sqrt(0.5) * common + sqrt(0.5) * idios
    return idios


def select_public_action(probabilities: np.ndarray, u: float, legal_indices: tuple[int, ...]) -> int:
    legal_probs = np.asarray([probabilities[index] for index in legal_indices], dtype=np.float64)
    legal_probs /= float(legal_probs.sum())
    cumulative = 0.0
    for index, probability in zip(legal_indices, legal_probs):
        cumulative += float(probability)
        if u < cumulative:
            return index
    return legal_indices[-1]


def normalized_loss(commit_sign: int, hidden_y: int, tick: int, senses: int, relays: int) -> float:
    loss = float(commit_sign != hidden_y) + 0.20 * tick / 30.0 + 0.02 * senses + 0.01 * relays
    return loss / 1.8
