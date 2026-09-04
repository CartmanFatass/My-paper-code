"""Stateless raw and calibrated residual packet views."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .config import PACKET_DIM, PREDICTOR_TARGET_DIM
from .contracts import ArrayRecord, PanelRow, canonical_array


_ADVERSE_SIGN = np.asarray((1, 1, 1, 1, -1, -1, -1, 1), dtype=np.float32)


def whitened_residual(target: np.ndarray, mean: np.ndarray, cholesky: np.ndarray) -> np.ndarray:
    target = np.asarray(target, dtype=np.float32)
    mean = np.asarray(mean, dtype=np.float32)
    factor = np.asarray(cholesky, dtype=np.float32)
    if target.shape != mean.shape or target.shape[-1] != PREDICTOR_TARGET_DIM:
        raise ValueError("target and mean must have equal [...,8] shapes")
    if factor.shape != (*target.shape, PREDICTOR_TARGET_DIM):
        raise ValueError("factor must have shape [...,8,8]")
    if not np.all(np.isfinite(target)) or not np.all(np.isfinite(mean)) or not np.all(np.isfinite(factor)):
        raise ValueError("predictor packet math requires finite inputs")
    # Preserve the cited legacy packet equation exactly: incoming FP32 dtype,
    # lower-triangular solve, and no jitter or precision promotion.
    target_tensor = torch.from_numpy(np.array(target, dtype=np.float32, order="C", copy=True))
    mean_tensor = torch.from_numpy(np.array(mean, dtype=np.float32, order="C", copy=True))
    factor_tensor = torch.from_numpy(np.array(factor, dtype=np.float32, order="C", copy=True))
    solved = torch.linalg.solve_triangular(
        factor_tensor, (target_tensor - mean_tensor).unsqueeze(-1), upper=False,
    ).squeeze(-1)
    return solved.numpy()


@dataclass(frozen=True)
class CalibrationTable:
    """Sorted per-coordinate residual support fit outside train/evaluation splits."""

    sorted_residuals: np.ndarray

    def __post_init__(self) -> None:
        values = np.asarray(self.sorted_residuals, dtype=np.float32).copy()
        if values.ndim != 2 or values.shape[0] != PREDICTOR_TARGET_DIM or values.shape[1] < 1:
            raise ValueError("calibration table must have shape [8,positive_n]")
        if not np.all(np.isfinite(values)) or np.any(values[:, 1:] < values[:, :-1]):
            raise ValueError("calibration residuals must be finite and sorted per coordinate")
        values.setflags(write=False)
        object.__setattr__(self, "sorted_residuals", values)

    def cdf(self, residual: np.ndarray) -> np.ndarray:
        values = np.asarray(residual, dtype=np.float32)
        if values.shape[-1] != PREDICTOR_TARGET_DIM or not np.all(np.isfinite(values)):
            raise ValueError("calibration CDF requires finite [...,8] residuals")
        flat = values.reshape(-1, PREDICTOR_TARGET_DIM)
        result = np.empty_like(flat)
        for coordinate in range(PREDICTOR_TARGET_DIM):
            support = self.sorted_residuals[coordinate]
            below = np.searchsorted(support, flat[:, coordinate], side="left")
            at_or_below = np.searchsorted(support, flat[:, coordinate], side="right")
            ties = at_or_below - below
            result[:, coordinate] = (below + 0.5 * ties + 0.5) / float(support.size + 1)
        return result.reshape(values.shape)

    @property
    def canonical_record(self) -> ArrayRecord:
        return canonical_array(self.sorted_residuals)


def fit_calibration(rows: tuple[PanelRow, ...] | list[PanelRow]) -> CalibrationTable:
    """Fit a table on a caller-supplied population (currently an inherited assumption)."""
    if not rows:
        raise ValueError("cannot fit calibration from an empty split")
    residuals = np.stack([whitened_residual(row.target, row.mean, row.cholesky) for row in rows])
    return CalibrationTable(np.sort(residuals.T, axis=1))


def raw_packet(target: np.ndarray, mean: np.ndarray, cholesky: np.ndarray) -> np.ndarray:
    target = np.asarray(target, dtype=np.float32)
    mean = np.asarray(mean, dtype=np.float32)
    factor = np.asarray(cholesky, dtype=np.float32)
    rows, cols = np.tril_indices(PREDICTOR_TARGET_DIM)
    packet = np.concatenate((target, mean, factor[..., rows, cols]), axis=-1)
    if packet.shape[-1] != PACKET_DIM or not np.all(np.isfinite(packet)):
        raise ValueError("raw packet must be a finite 52-vector")
    return packet.astype(np.float32, copy=False)


def residual_packet(
    target: np.ndarray,
    mean: np.ndarray,
    cholesky: np.ndarray,
    calibration: CalibrationTable,
) -> np.ndarray:
    residual = whitened_residual(target, mean, cholesky)
    clipped = np.clip(residual, -6.0, 6.0)
    rank = 2.0 * calibration.cdf(residual) - 1.0
    signed = _ADVERSE_SIGN * residual
    # Match torch.clamp_min exactly, including its preservation of -0.0.
    adverse = np.where(signed < 0.0, np.float32(0.0), signed)
    zeros = np.zeros((*residual.shape[:-1], 28), dtype=np.float32)
    packet = np.concatenate((clipped, rank, adverse, zeros), axis=-1).astype(np.float32)
    if packet.shape[-1] != PACKET_DIM or not np.all(np.isfinite(packet)):
        raise ValueError("residual packet must be a finite padded 52-vector")
    return packet


@dataclass(frozen=True)
class PacketViews:
    row_keys: tuple[str, ...]
    raw: np.ndarray
    true_residual: np.ndarray

    def __post_init__(self) -> None:
        raw = np.asarray(self.raw, dtype=np.float32).copy()
        true = np.asarray(self.true_residual, dtype=np.float32).copy()
        expected = (len(self.row_keys), PACKET_DIM)
        if raw.shape != expected or true.shape != expected:
            raise ValueError(f"packet matrices must have shape {expected}")
        if not np.all(np.isfinite(raw)) or not np.all(np.isfinite(true)):
            raise ValueError("packet matrices must be finite")
        raw.setflags(write=False)
        true.setflags(write=False)
        object.__setattr__(self, "raw", raw)
        object.__setattr__(self, "true_residual", true)

    @property
    def raw_dataset(self) -> "PacketDataset":
        return PacketDataset(self.row_keys, self.raw)

    @property
    def true_residual_dataset(self) -> "PacketDataset":
        return PacketDataset(self.row_keys, self.true_residual)


@dataclass(frozen=True)
class PacketDataset:
    """A packet matrix positionally bound to panel rows."""

    row_keys: tuple[str, ...]
    values: np.ndarray

    def __post_init__(self) -> None:
        values = np.asarray(self.values, dtype=np.float32).copy()
        if values.shape != (len(self.row_keys), PACKET_DIM) or not np.all(np.isfinite(values)):
            raise ValueError("keyed packets must have finite shape [rows,52]")
        if len(self.row_keys) != len(set(self.row_keys)):
            raise ValueError("packet row keys must be unique")
        values.setflags(write=False)
        object.__setattr__(self, "values", values)

    @property
    def canonical_record(self) -> tuple[object, ...]:
        return self.row_keys, canonical_array(self.values)

    def require_rows(self, rows: tuple[PanelRow, ...]) -> None:
        expected = tuple(row.key.text for row in rows)
        if self.row_keys != expected:
            raise ValueError("packet row-key order does not exactly match panel row order")


def construct_packet_views(rows: tuple[PanelRow, ...], calibration: CalibrationTable) -> PacketViews:
    return PacketViews(
        row_keys=tuple(row.key.text for row in rows),
        raw=np.stack([raw_packet(row.target, row.mean, row.cholesky) for row in rows]),
        true_residual=np.stack([
            residual_packet(row.target, row.mean, row.cholesky, calibration) for row in rows
        ]),
    )
