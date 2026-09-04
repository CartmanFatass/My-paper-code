"""Persistable whole-packet derangement within frozen common-history cells."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .config import counter_rng
from .contracts import PanelRow
from .packets import PacketDataset


@dataclass(frozen=True)
class DerangementPlan:
    recipient_keys: tuple[str, ...]
    donor_indices: tuple[int, ...]
    cells: tuple[tuple[str, str, int, float], ...]

    def __post_init__(self) -> None:
        size = len(self.recipient_keys)
        if len(self.donor_indices) != size or len(self.cells) != size:
            raise ValueError("derangement plan fields have inconsistent length")
        if sorted(self.donor_indices) != list(range(size)):
            raise ValueError("donors must form one bijection over all rows")
        if any(index == donor for index, donor in enumerate(self.donor_indices)):
            raise ValueError("derangement contains a fixed point")
        if any(self.cells[index] != self.cells[donor] for index, donor in enumerate(self.donor_indices)):
            raise ValueError("derangement crossed a frozen cell")
    def to_json(self) -> dict[str, object]:
        return {
            "recipient_keys": list(self.recipient_keys),
            "donor_indices": list(self.donor_indices),
            "cells": [list(cell) for cell in self.cells],
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, object]) -> "DerangementPlan":
        plan = cls(
            recipient_keys=tuple(str(value) for value in payload["recipient_keys"]),  # type: ignore[arg-type]
            donor_indices=tuple(int(value) for value in payload["donor_indices"]),  # type: ignore[arg-type]
            cells=tuple(
                (str(cell[0]), str(cell[1]), int(cell[2]), float(cell[3]))
                for cell in payload["cells"]  # type: ignore[union-attr]
            ),
        )
        if set(payload) != {"recipient_keys", "donor_indices", "cells"}:
            raise ValueError("serialized derangement plan has unexpected fields")
        return plan

    def apply(self, rows: tuple[PanelRow, ...], source: PacketDataset) -> PacketDataset:
        """Revalidate a persisted plan against its rows and source packet bytes."""

        source.require_rows(rows)
        expected_keys = tuple(row.key.text for row in rows)
        expected_cells = tuple(row.derangement_cell for row in rows)
        if self.recipient_keys != expected_keys or self.cells != expected_cells:
            raise ValueError("persisted derangement plan is not bound to these rows/cells")
        values = source.values[np.asarray(self.donor_indices, dtype=np.int64)].copy()
        expected = source.values[np.asarray(self.donor_indices, dtype=np.int64)]
        if not np.array_equal(values, expected):
            raise RuntimeError("derangement application changed packet bytes")
        if not _same_packet_multiset(values, source.values):
            raise ValueError("derangement did not preserve the exact packet multiset")
        return PacketDataset(self.recipient_keys, values)


def _same_packet_multiset(left: np.ndarray, right: np.ndarray) -> bool:
    """Compare row multisets using exact array equality, including duplicates."""

    left = np.asarray(left)
    right = np.asarray(right)
    if left.shape != right.shape or left.dtype != right.dtype:
        return False
    used = np.zeros(right.shape[0], dtype=np.bool_)
    for row in left:
        match = next(
            (index for index, candidate in enumerate(right)
             if not used[index] and np.array_equal(row, candidate)),
            None,
        )
        if match is None:
            return False
        used[match] = True
    return bool(np.all(used))


def build_derangement(
    rows: tuple[PanelRow, ...],
    true_packets: PacketDataset,
    *,
    replicate: int,
) -> tuple[PacketDataset, DerangementPlan]:
    """Derange intact rows independently inside split/regime/horizon/cost cells."""

    if not isinstance(true_packets, PacketDataset):
        raise TypeError("derangement requires a row-keyed PacketDataset")
    true_packets.require_rows(rows)
    packets = true_packets.values
    if any(row.key.replicate != replicate for row in rows):
        raise ValueError("one derangement plan may cover only one replicate")
    groups: dict[tuple[str, str, int, float], list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(row.derangement_cell, []).append(index)
    donors = np.full(len(rows), -1, dtype=np.int64)
    for ordinal, (cell, indices) in enumerate(sorted(groups.items())):
        if len(indices) < 2:
            raise ValueError(f"derangement cell {cell!r} has fewer than two rows")
        fixed_positions = np.arange(len(indices), dtype=np.int64)
        rng = counter_rng("derangement", replicate, ordinal)
        for _ in range(10_000):
            permutation = rng.permutation(len(indices))
            if np.all(permutation != fixed_positions):
                break
        else:
            raise RuntimeError("no fixed-point-free cell permutation in 10,000 draws")
        for local_recipient, local_donor in enumerate(permutation):
            donors[indices[local_recipient]] = indices[int(local_donor)]
    if np.any(donors < 0):
        raise RuntimeError("derangement plan left an unassigned row")
    deranged = packets[donors].copy()
    if not _same_packet_multiset(packets, deranged):
        raise RuntimeError("derangement did not preserve the exact packet multiset")
    plan = DerangementPlan(
        recipient_keys=tuple(row.key.text for row in rows),
        donor_indices=tuple(int(value) for value in donors),
        cells=tuple(row.derangement_cell for row in rows),
    )
    return plan.apply(rows, true_packets), plan
