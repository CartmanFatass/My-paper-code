"""Factorized G36 donor-column intervention for the exact G35 CS checkpoints."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import torch

from ha_ctse_process import continuous_roster_history_proxy_free_cs_g36 as g36
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


ALGORITHM_ID = "CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37"
SOURCE_ID = "CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0"
FACTORIZED_PROXY_SEED_BASE = 10_363_000
NONFORMAL_SEED_OFFSET = 900_000
BUNDLE_WIDTH = 4


def _column_draw(
    bank: g36.G36HistoryProxyDonorBank,
    *,
    seed: int,
    capacity: int,
    episode_id: int,
    physical_call_position: int,
    active_count: int,
    coordinate: int,
) -> np.ndarray:
    """Draw one complete donor column from independent snapshot/permutation streams."""
    address = [
        int(seed),
        int(capacity),
        int(episode_id),
        int(physical_call_position),
        int(active_count),
    ]
    source = bank.snapshots(active_count)
    snapshot_rng = np.random.default_rng(
        np.random.SeedSequence([*address, 2 * int(coordinate)])
    )
    permutation_rng = np.random.default_rng(
        np.random.SeedSequence([*address, 2 * int(coordinate) + 1])
    )
    selected = source[int(snapshot_rng.integers(0, len(source)))]
    return selected[permutation_rng.permutation(active_count), coordinate].copy()


class G37FactorizedHistoryProxyTape:
    """Four independently addressed G36 donor columns, cached by target tape address."""

    def __init__(
        self,
        bank: g36.G36HistoryProxyDonorBank,
        *,
        replicate: int,
        capacity: int,
        formal: bool,
    ) -> None:
        if not 0 <= int(replicate) < 3 or capacity not in g34.CAPACITIES:
            raise ValueError("G37 factorized tape identity outside registered support")
        self.bank = bank
        self.replicate = int(replicate)
        self.capacity = int(capacity)
        self.seed = (
            FACTORIZED_PROXY_SEED_BASE
            + self.replicate
            + (0 if formal else NONFORMAL_SEED_OFFSET)
        )
        self._cache: dict[tuple[int, int, int], np.ndarray] = {}
        self.target_history_read_count = 0

    def bundle_for(
        self,
        *,
        episode_id: int,
        physical_call_position: int,
        active_mask: np.ndarray,
    ) -> np.ndarray:
        mask = np.asarray(active_mask, dtype=bool)
        if mask.shape != (self.capacity,):
            raise ValueError("G37 factorized tape active-mask shape mismatch")
        active_count = int(mask.sum())
        if active_count not in self.bank.supported_active_counts:
            raise ValueError("G37 factorized tape donor bank missing active count")
        key = (int(episode_id), int(physical_call_position), active_count)
        cached = self._cache.get(key)
        if cached is None:
            cached = np.column_stack(
                [
                    _column_draw(
                        self.bank,
                        seed=self.seed,
                        capacity=self.capacity,
                        episode_id=key[0],
                        physical_call_position=key[1],
                        active_count=key[2],
                        coordinate=coordinate,
                    )
                    for coordinate in range(BUNDLE_WIDTH)
                ]
            ).astype(np.float32, copy=False)
            self._cache[key] = cached
        result = np.zeros((self.capacity, BUNDLE_WIDTH), dtype=np.float32)
        result[np.flatnonzero(mask)] = cached
        return result


def validate_g37_factorized_marginals(
    bank: g36.G36HistoryProxyDonorBank,
    bundle: np.ndarray,
    *,
    episode_id: int,
    physical_call_position: int,
    active_mask: np.ndarray,
    replicate: int,
    capacity: int,
    formal: bool,
) -> bool:
    """Certify exact selected/permuted G36 columns with no postprocessing."""
    mask = np.asarray(active_mask, dtype=bool)
    observed = np.asarray(bundle, dtype=np.float32)
    tape = G37FactorizedHistoryProxyTape(
        bank, replicate=replicate, capacity=capacity, formal=formal
    )
    expected = tape.bundle_for(
        episode_id=episode_id,
        physical_call_position=physical_call_position,
        active_mask=mask,
    )
    return bool(observed.shape == expected.shape and np.array_equal(observed, expected))


def evaluate_g37_factorized_history_proxy(
    model: ContinuousRosterPolicy,
    *,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    process_kind: str,
    deterministic: bool,
    tape: G37FactorizedHistoryProxyTape,
    device: torch.device = torch.device("cpu"),
) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
    """Reuse the corrected G36 actor-only evaluator with a factorized tape."""
    return g36.evaluate_g36_history_proxy(
        model,
        processes=processes,
        action_seed=action_seed,
        process_kind=process_kind,
        deterministic=deterministic,
        tape=tape,
        device=device,
    )
