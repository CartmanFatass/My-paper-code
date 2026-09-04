"""Matched-exposure gate training and fresh predictor fitting."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np
import torch

from .config import (
    ADAM_BETAS, ADAM_EPSILON, BATCH_SIZE, BUDGETS, GRADIENT_NORM_CAP,
    LEARNING_RATE, RNG_NAMESPACE, counter_rng_for_namespace,
)
from .contracts import Budget, ExposureAudit, PanelRow, PredictorExample, Representation
from .models import CommonHistoryGate, FORECAST_HORIZONS, FreshPredictor, canonical_state, gaussian_nll
from .packets import PacketDataset


def canonical_example_order(
    row_count: int,
    *,
    replicate: int,
    updates: int = BUDGETS["LONG"],
    rng_namespace: int = RNG_NAMESPACE,
) -> np.ndarray:
    if row_count <= 0:
        raise ValueError("training requires at least one retained row")
    permutation = counter_rng_for_namespace(
        rng_namespace, "gate_order", replicate,
    ).permutation(row_count).astype(np.int64)
    order = np.resize(permutation, updates * BATCH_SIZE)
    order.setflags(write=False)
    return order


def _collate(
    rows: Sequence[PanelRow], packets: np.ndarray, indices: np.ndarray,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    selected = [rows[int(index)] for index in indices]
    lengths = torch.tensor([row.history.shape[0] for row in selected], dtype=torch.int64)
    histories = torch.zeros((len(selected), int(lengths.max()), 42), dtype=torch.float32)
    for index, row in enumerate(selected):
        histories[index, :row.history.shape[0]] = torch.from_numpy(np.array(row.history, copy=True))
    packet = torch.from_numpy(np.asarray(packets[indices], dtype=np.float32).copy())
    legal = torch.from_numpy(np.stack([row.legal_mask for row in selected]).copy())
    targets = torch.from_numpy(np.stack([row.g16 for row in selected]).astype(np.float32))
    targets = torch.nan_to_num(targets, nan=0.0)
    return histories, lengths, packet, legal, targets


def legal_masked_mse(prediction: torch.Tensor, target: torch.Tensor, legal: torch.Tensor) -> torch.Tensor:
    if prediction.shape != target.shape or legal.shape != prediction.shape:
        raise ValueError("prediction, target, and legal mask must have equal shapes")
    if legal.dtype is not torch.bool or not bool(torch.all(torch.any(legal, dim=1))):
        raise ValueError("each training state requires at least one legal action")
    squared = (prediction - target).square()
    return squared.masked_select(legal).mean()


@dataclass(frozen=True)
class TrainedPath:
    representation: Representation
    checkpoints: Mapping[Budget, CommonHistoryGate]
    audits: Mapping[Budget, ExposureAudit]
    final_parameters: tuple[tuple[str, tuple[str, tuple[int, ...], bytes]], ...]


def train_one_path(
    rows: tuple[PanelRow, ...],
    packets: PacketDataset,
    *,
    replicate: int,
    representation: Representation,
    order: np.ndarray,
    short_updates: int = BUDGETS["SHORT"],
    long_updates: int = BUDGETS["LONG"],
    rng_namespace: int = RNG_NAMESPACE,
    capture_short: bool = True,
    resource_monitor: Callable[[], None] | None = None,
) -> TrainedPath:
    """Continue one unchanged Adam trajectory through both frozen checkpoints."""

    representation = Representation(representation)
    monitor = resource_monitor or (lambda: None)
    monitor()
    if not isinstance(packets, PacketDataset):
        raise TypeError("training requires a row-keyed PacketDataset")
    packets.require_rows(rows)
    if short_updates <= 0 or long_updates < short_updates:
        raise ValueError("checkpoint updates are incoherent")
    required = long_updates * BATCH_SIZE
    if order.shape != (required,):
        raise ValueError("canonical order has the wrong processed-example length")
    model = CommonHistoryGate(counter_rng_for_namespace(
        rng_namespace, "gate_initialization", replicate,
    ))
    initialization_state = canonical_state(model)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=LEARNING_RATE, betas=ADAM_BETAS,
        eps=ADAM_EPSILON, weight_decay=0.0,
    )
    row_records = tuple(row.canonical_record for row in rows)
    checkpoints: dict[Budget, CommonHistoryGate] = {}
    audits: dict[Budget, ExposureAudit] = {}
    model.train()
    for update in range(1, long_updates + 1):
        monitor()
        begin = (update - 1) * BATCH_SIZE
        batch = order[begin:begin + BATCH_SIZE]
        histories, lengths, packet, legal, target = _collate(rows, packets.values, batch)
        prediction = model(histories, lengths, packet)
        loss = legal_masked_mse(prediction, target, legal)
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("gate loss became non-finite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_NORM_CAP)
        optimizer.step()
        monitor()
        budget = (
            Budget.SHORT
            if capture_short and update == short_updates
            else Budget.LONG if update == long_updates else None
        )
        if budget is not None:
            snapshot = deepcopy(model).eval()
            checkpoints[budget] = snapshot
            audits[budget] = ExposureAudit(
                initialization_state=initialization_state,
                order=tuple(int(value) for value in order[:update * BATCH_SIZE]),
                rows=row_records,
                packets=packets.canonical_record,
                updates=update,
                batch_size=BATCH_SIZE,
                processed_examples=update * BATCH_SIZE,
                logical_work=update * BATCH_SIZE,
            )
    return TrainedPath(
        representation=representation,
        checkpoints=checkpoints,
        audits=audits,
        final_parameters=canonical_state(model),
    )


def train_matched_paths(
    rows: tuple[PanelRow, ...],
    packets: Mapping[Representation, PacketDataset],
    *,
    replicate: int,
    rng_namespace: int = RNG_NAMESPACE,
    resource_monitor: Callable[[], None] | None = None,
) -> dict[Representation, TrainedPath]:
    """Train all three paths with byte-identical initialization/order/work."""

    expected = set(Representation)
    if set(packets) != expected:
        raise ValueError("matched training requires exactly the three frozen representations")
    order = canonical_example_order(
        len(rows), replicate=replicate, rng_namespace=rng_namespace,
    )
    paths = {
        representation: train_one_path(
            rows, packets[representation], replicate=replicate,
            representation=representation, order=order,
            rng_namespace=rng_namespace,
            resource_monitor=resource_monitor,
        )
        for representation in Representation
    }
    for budget in Budget:
        audits = [paths[representation].audits[budget] for representation in Representation]
        reference = audits[0]
        if not all(audit.initialization_state == reference.initialization_state for audit in audits[1:]):
            raise RuntimeError("representation paths did not share initialization bytes")
        if not all(
            audit.order == reference.order
            and audit.rows == reference.rows
            and audit.updates == reference.updates
            and audit.processed_examples == reference.processed_examples
            and audit.logical_work == reference.logical_work
            for audit in audits[1:]
        ):
            raise RuntimeError("representation paths did not receive matched exposure")
        for representation, audit in zip(Representation, audits):
            if audit.packets != packets[representation].canonical_record:
                raise RuntimeError("training packet record changed within a representation path")
    return paths


@dataclass(frozen=True)
class PredictorFitAudit:
    examples: int
    updates: int
    processed_examples: int
    order: tuple[int, ...]
    parameters: tuple[tuple[str, tuple[str, tuple[int, ...], bytes]], ...]


def _collate_predictor(
    examples: Sequence[PredictorExample], indices: np.ndarray,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    selected = [examples[int(index)] for index in indices]
    lengths = torch.tensor([row.origin_history.shape[0] for row in selected], dtype=torch.int64)
    histories = torch.zeros((len(selected), int(lengths.max()), 42), dtype=torch.float32)
    for index, row in enumerate(selected):
        histories[index, :row.origin_history.shape[0]] = torch.from_numpy(
            np.array(row.origin_history, copy=True)
        )
    return (
        histories, lengths,
        torch.tensor([row.option for row in selected], dtype=torch.int64),
        torch.tensor([row.k for row in selected], dtype=torch.int64),
        torch.tensor([row.target_age for row in selected], dtype=torch.int64),
        torch.from_numpy(np.stack([row.target for row in selected]).copy()),
    )


def fit_fresh_predictor(
    examples: tuple[PredictorExample, ...], *, replicate: int,
    updates: int = 400, batch_size: int = 256,
    rng_namespace: int = RNG_NAMESPACE,
    resource_monitor: Callable[[], None] | None = None,
) -> tuple[FreshPredictor, PredictorFitAudit]:
    """Fit a fresh predictor without any historical state or artifact route."""

    if not examples:
        raise ValueError("fresh predictor fit requires examples")
    monitor = resource_monitor or (lambda: None)
    monitor()
    ordered = tuple(sorted(examples, key=lambda row: row.canonical_key))
    model = FreshPredictor(counter_rng_for_namespace(
        rng_namespace, "predictor_initialization", replicate,
    ))
    optimizer = torch.optim.Adam(
        model.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-5,
    )
    permutation = counter_rng_for_namespace(
        rng_namespace, "predictor_order", replicate,
    ).permutation(len(ordered))
    order = np.resize(permutation, updates * batch_size).astype(np.int64)
    horizon_to_index = {value: index for index, value in enumerate(FORECAST_HORIZONS)}
    model.train()
    for update in range(updates):
        monitor()
        indices = order[update * batch_size:(update + 1) * batch_size]
        histories, lengths, option, k, horizon, target = _collate_predictor(ordered, indices)
        distribution = model(histories, lengths, option, k, FORECAST_HORIZONS)
        selected_horizon = torch.tensor(
            [horizon_to_index[int(value)] for value in horizon], dtype=torch.int64
        )
        batch_index = torch.arange(target.shape[0], dtype=torch.int64)
        loss = gaussian_nll(
            target, distribution.mean[batch_index, selected_horizon],
            distribution.cholesky[batch_index, selected_horizon],
        ).mean()
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("fresh predictor NLL became non-finite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        monitor()
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model, PredictorFitAudit(
        examples=len(ordered), updates=updates, processed_examples=updates * batch_size,
        order=tuple(int(value) for value in order), parameters=canonical_state(model),
    )
