"""Masked native action selection and equal-regime regret evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import torch

from .contracts import Budget, PanelRow, Representation
from .models import CommonHistoryGate
from .packets import PacketDataset


def select_printed_action(values: np.ndarray, legal_mask: np.ndarray) -> int:
    """Select the legal maximum; NumPy's first maximum fixes printed-order ties."""

    scores = np.asarray(values, dtype=np.float64)
    legal = np.asarray(legal_mask, dtype=np.bool_)
    if scores.shape != (8,) or legal.shape != (8,) or not np.any(legal):
        raise ValueError("selection requires eight scores and a nonempty legal mask")
    if not np.all(np.isfinite(scores[legal])):
        raise ValueError("legal action scores must be finite")
    masked = np.where(legal, scores, -np.inf)
    return int(np.argmax(masked))


def native_regret(g16: np.ndarray, legal_mask: np.ndarray, selected_action: int) -> float:
    labels = np.asarray(g16, dtype=np.float64)
    legal = np.asarray(legal_mask, dtype=np.bool_)
    if not 0 <= selected_action < 8 or not legal[selected_action]:
        raise ValueError("selected action must be legal")
    oracle = float(np.max(labels[legal]))
    regret = oracle - float(labels[selected_action])
    if regret < -1e-12:
        raise RuntimeError("native regret became negative")
    return max(0.0, regret)


def _collate_all(
    rows: tuple[PanelRow, ...], packets: np.ndarray,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    lengths = torch.tensor([row.history.shape[0] for row in rows], dtype=torch.int64)
    histories = torch.zeros((len(rows), int(lengths.max()), 42), dtype=torch.float32)
    for index, row in enumerate(rows):
        histories[index, :row.history.shape[0]] = torch.from_numpy(np.array(row.history, copy=True))
    return histories, lengths, torch.from_numpy(np.asarray(packets, dtype=np.float32).copy())


@dataclass(frozen=True)
class EvaluationSummary:
    representation: Representation
    budget: Budget
    regime_mean_regret: Mapping[str, float]
    target_equal_weight_regret: float
    k8_mean_regret: float
    row_count_by_regime: Mapping[str, int]
    target_action_headroom_count: int
    keep_optimal_count: int
    zero_regret_oracle_count: int
    logged_action_count: int
    logged_scripted_mean_regret: float
    logged_scripted_regret_by_regime: Mapping[str, float]
    oracle_regret_max_abs: float
    target_action_headroom_by_regime: Mapping[str, int]
    keep_optimal_by_regime: Mapping[str, int]


def evaluate_checkpoint(
    model: CommonHistoryGate,
    rows: tuple[PanelRow, ...],
    packets: PacketDataset,
    *,
    representation: Representation,
    budget: Budget,
    target_regimes: tuple[str, ...] = ("K16", "K4_TO_16", "K16_TO_4"),
) -> EvaluationSummary:
    if not rows:
        raise ValueError("evaluation panel is empty")
    if not isinstance(packets, PacketDataset):
        raise TypeError("evaluation requires a row-keyed PacketDataset")
    packets.require_rows(rows)
    histories, lengths, packet_tensor = _collate_all(rows, packets.values)
    model.eval()
    with torch.no_grad():
        predictions = model(histories, lengths, packet_tensor).cpu().numpy()
    regrets: dict[str, list[float]] = {}
    headroom = keep_optimal = zero_regret = logged = 0
    logged_regrets: dict[str, list[float]] = {}
    headroom_by_regime: dict[str, int] = {}
    keep_by_regime: dict[str, int] = {}
    oracle_regret_max_abs = 0.0
    for row, prediction in zip(rows, predictions):
        selected = select_printed_action(prediction, row.legal_mask)
        regret = native_regret(row.g16, row.legal_mask, selected)
        regrets.setdefault(row.key.regime, []).append(regret)
        logged_regret = native_regret(row.g16, row.legal_mask, row.logged_action)
        logged_regrets.setdefault(row.key.regime, []).append(logged_regret)
        legal_values = row.g16[row.legal_mask]
        oracle = float(np.max(legal_values))
        keep_witness = int(abs(float(row.g16[0]) - oracle) <= 1e-12)
        keep_optimal += keep_witness
        keep_by_regime[row.key.regime] = keep_by_regime.get(row.key.regime, 0) + keep_witness
        zero_regret += int(regret <= 1e-12)
        logged += int(selected == row.logged_action)
        oracle_action = select_printed_action(row.g16, row.legal_mask)
        oracle_regret_max_abs = max(
            oracle_regret_max_abs, abs(native_regret(row.g16, row.legal_mask, oracle_action))
        )
        headroom_witness = int(any(
            row.legal_mask[index] and row.g16[index] > row.g16[0] + 1e-12
            for index in range(1, 8)
        ))
        headroom += headroom_witness
        headroom_by_regime[row.key.regime] = (
            headroom_by_regime.get(row.key.regime, 0) + headroom_witness
        )
    missing = [regime for regime in target_regimes if regime not in regrets]
    if missing:
        raise ValueError(f"evaluation panel lacks target regimes: {missing}")
    means = {regime: float(np.mean(values)) for regime, values in regrets.items()}
    return EvaluationSummary(
        representation=Representation(representation), budget=Budget(budget),
        regime_mean_regret=means,
        target_equal_weight_regret=float(np.mean([means[regime] for regime in target_regimes])),
        k8_mean_regret=float(means.get("K8", np.nan)),
        row_count_by_regime={regime: len(values) for regime, values in regrets.items()},
        target_action_headroom_count=headroom,
        keep_optimal_count=keep_optimal,
        zero_regret_oracle_count=zero_regret,
        logged_action_count=logged,
        logged_scripted_mean_regret=float(np.mean([
            value for values in logged_regrets.values() for value in values
        ])),
        logged_scripted_regret_by_regime={
            regime: float(np.mean(values)) for regime, values in logged_regrets.items()
        },
        oracle_regret_max_abs=oracle_regret_max_abs,
        target_action_headroom_by_regime=headroom_by_regime,
        keep_optimal_by_regime=keep_by_regime,
    )
