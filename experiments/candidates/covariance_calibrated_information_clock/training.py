"""Frozen snapshot construction and exact-order float64 optimization."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Callable

import numpy as np

from .config import (
    ACTOR_BATCH,
    ACTOR_UPDATES,
    FUSION_BATCH,
    FUSION_UPDATES,
    MODULE_IDS,
    MU,
    OVERLAP,
    Phase,
    REGIMES,
    STREAMS,
    TRAIN_K,
    TRAIN_N,
    TRAIN_ROWS,
    analytic_information,
)
from .core import analytic_q_j, hmm_transition, snapshot_residual
from .models import CCICModel, ESSScalarModel, InfoFlexModel, RIStrongV2Model, SharedActor
from .reference import NumericalReference
from .rng import uniform


@dataclass(frozen=True)
class Snapshot:
    cell_index: int
    row_index: int
    n: int
    k: int
    regime: str
    t: int
    ell: float
    y: int
    residual: np.ndarray
    z: np.ndarray
    overlap: np.ndarray
    quality: np.ndarray
    exact_q: float
    exact_j: float
    ell_minus: float
    exact_posterior: float


@dataclass
class TrainedSeed:
    seed: int
    ccic: CCICModel
    ess: ESSScalarModel
    ri: RIStrongV2Model
    info: InfoFlexModel
    actor: SharedActor
    final_losses: dict[str, float]

    def state(self) -> dict:
        return {
            "seed": self.seed,
            "CCIC": self.ccic.state(),
            "ESS-SCALAR": self.ess.state(),
            "RI-STRONG-v2": self.ri.state(),
            "INFO-FLEX": self.info.state(),
            "actor": self.actor.state(),
            "final_losses": self.final_losses,
        }


def build_snapshot_bank(seed: int) -> list[Snapshot]:
    bank: list[Snapshot] = []
    cell_index = 0
    for n in TRAIN_N:
        for k in TRAIN_K:
            for regime in REGIMES:
                t_count = floor(30 / k)
                for j in range(24):
                    t = k * floor(((j + 0.5) * t_count) / 24)
                    capture_tick = t + k
                    for m_index in range(32):
                        row_index = 32 * j + m_index
                        ell = -15.5 + m_index
                        y = 1 if (j + m_index) % 2 == 0 else -1
                        residual = snapshot_residual(seed, cell_index, row_index, capture_tick, n, regime)
                        z = MU * y + residual
                        overlap = np.full(z.size, OVERLAP[regime], dtype=np.float64)
                        quality = np.ones(z.size, dtype=np.float64)
                        exact_q, exact_j = analytic_q_j(z, regime)
                        ell_minus = hmm_transition(ell, k)
                        bank.append(
                            Snapshot(
                                cell_index,
                                row_index,
                                n,
                                k,
                                regime,
                                t,
                                ell,
                                y,
                                residual,
                                z,
                                overlap,
                                quality,
                                exact_q,
                                exact_j,
                                ell_minus,
                                ell_minus + 2.0 * exact_q,
                            )
                        )
                cell_index += 1
    if len(bank) != TRAIN_ROWS:
        raise AssertionError("snapshot bank must contain exactly 9,216 rows")
    return bank


def _minibatch_indices(seed: int, module_name: str, update: int, batch_size: int) -> list[int]:
    module_id = MODULE_IDS[module_name]
    return [
        floor(
            TRAIN_ROWS
            * uniform(
                seed,
                Phase.TRAIN_OPT,
                STREAMS["TRAIN_OPT_MINIBATCH"],
                module_id * 1500 + update,
                slot,
            )
        )
        for slot in range(batch_size)
    ]


def train_seed(
    seed: int,
    fine_reference: NumericalReference,
    on_activity_start: Callable[[], None] | None = None,
    resource_check: Callable[[], None] | None = None,
) -> TrainedSeed:
    bank = build_snapshot_bank(seed)
    final_losses: dict[str, float] = {}

    ccic = CCICModel(seed)
    for update in range(FUSION_UPDATES):
        if resource_check is not None and update % 16 == 0:
            resource_check()
        if update == 0 and on_activity_start is not None:
            on_activity_start()
        batch = [bank[index] for index in _minibatch_indices(seed, "CCIC", update, FUSION_BATCH)]
        final_losses["CCIC"] = ccic.train_batch([(row.residual, row.overlap, row.quality) for row in batch])

    ess = ESSScalarModel()
    for update in range(FUSION_UPDATES):
        if resource_check is not None and update % 16 == 0:
            resource_check()
        batch = [bank[index] for index in _minibatch_indices(seed, "ESS-SCALAR", update, FUSION_BATCH)]
        final_losses["ESS-SCALAR"] = ess.train_batch([(row.residual, OVERLAP[row.regime]) for row in batch])

    ri = RIStrongV2Model(seed)
    for update in range(FUSION_UPDATES):
        if resource_check is not None and update % 16 == 0:
            resource_check()
        batch = [bank[index] for index in _minibatch_indices(seed, "RI-STRONG-v2", update, FUSION_BATCH)]
        final_losses["RI-STRONG-v2"] = ri.train_batch(
            [(row.z, OVERLAP[row.regime], row.t, row.k, 2.0 * row.exact_q, row.exact_j) for row in batch]
        )

    # CCIC is frozen before this head is constructed and trained. Its outputs
    # are features only; INFO-FLEX gradients never enter the covariance model.
    info = InfoFlexModel(seed)
    for update in range(FUSION_UPDATES):
        if resource_check is not None and update % 16 == 0:
            resource_check()
        batch = [bank[index] for index in _minibatch_indices(seed, "INFO-FLEX", update, FUSION_BATCH)]
        examples = []
        for row in batch:
            q_hat, j_hat = ccic.fusion(row.z, row.overlap, row.quality)
            examples.append((row.ell_minus, q_hat, j_hat, row.k, row.exact_posterior, row.exact_j))
        final_losses["INFO-FLEX"] = info.train_batch(examples)

    actor = SharedActor(seed)
    labels = [
        fine_reference.action(row.n, row.k, row.regime, row.t, row.ell)
        for row in bank
    ]
    for update in range(ACTOR_UPDATES):
        if resource_check is not None and update % 16 == 0:
            resource_check()
        indices = _minibatch_indices(seed, "actor", update, ACTOR_BATCH)
        batch_examples = [
            (bank[index].ell, analytic_information(bank[index].n, bank[index].regime), bank[index].t, bank[index].k, labels[index])
            for index in indices
        ]
        final_losses["actor"] = actor.train_batch(batch_examples)

    return TrainedSeed(seed, ccic, ess, ri, info, actor, final_losses)
