"""Current-time, age-free logistic veto used by the VSP-05 B1 toy experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import torch
import torch.nn.functional as F


FEATURE_DIM = 8
SKILL_COUNT = 3
REJECT_THRESHOLD = 0.80
HARD_POSITION_THRESHOLD = 1.0 / 8.0
TRUTH_POSITION_THRESHOLD = 0.25
HARD_VELOCITY_THRESHOLD = 0.25
TRUTH_VELOCITY_THRESHOLD = 1.0 / 16.0
LEARNING_RATE = 0.05
ADAM_BETAS = (0.9, 0.999)
ADAM_EPS = 1.0e-8
L2_COEFFICIENT = 1.0e-3


def _skill(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} must be an integer skill ID")
    selected = int(value)
    if selected != value or not 0 <= selected < SKILL_COUNT:
        raise ValueError(f"{name} must lie in {{0,1,2}}")
    return selected


def semantic_feature(
    position: float,
    velocity: float,
    current_skill: int,
    proposed_skill: int,
) -> np.ndarray:
    """Return exactly the registered current-time eight-dimensional feature."""

    position_value = float(position)
    velocity_value = float(velocity)
    if not np.isfinite(position_value) or not np.isfinite(velocity_value):
        raise ValueError("position and velocity must be finite")
    current = _skill(current_skill, "current_skill")
    proposed = _skill(proposed_skill, "proposed_skill")
    feature = np.zeros(FEATURE_DIM, dtype=np.float32)
    feature[0] = position_value
    feature[1] = velocity_value
    feature[2 + current] = 1.0
    feature[5 + proposed] = 1.0
    return feature


@dataclass(frozen=True)
class ReceiptClassification:
    gate: bool
    truth: bool
    label: int | None


@dataclass(frozen=True)
class VetoDecision:
    selected_skill: int
    rejected: bool


def select_semantic_action(
    *,
    current_skill: int,
    proposed_skill: int,
    receipt: ReceiptClassification,
    learned_veto: bool,
    alias_probability: float | None,
) -> VetoDecision:
    """Apply G_SEM, deterministic handoff, and the fixed reject threshold."""

    current = _skill(current_skill, "current_skill")
    proposed = _skill(proposed_skill, "proposed_skill")
    if proposed == current or not receipt.gate:
        return VetoDecision(current, False)
    if not learned_veto:
        if alias_probability is not None:
            raise ValueError("DET selection cannot receive a learner probability")
        return VetoDecision(proposed, False)
    if alias_probability is None or not np.isfinite(float(alias_probability)):
        raise ValueError("learned selection requires a finite alias probability")
    rejected = float(alias_probability) >= REJECT_THRESHOLD
    return VetoDecision(current if rejected else proposed, rejected)


def classify_receipt(
    proposed_skill: int,
    position: float,
    velocity: float,
) -> ReceiptClassification:
    """Apply the frozen symmetric hard-receipt and stricter-truth predicates."""

    proposed = _skill(proposed_skill, "proposed_skill")
    position_value = float(position)
    velocity_value = float(velocity)
    if not np.isfinite(position_value) or not np.isfinite(velocity_value):
        raise ValueError("position and velocity must be finite")
    if proposed == 0:
        gate = position_value <= -HARD_POSITION_THRESHOLD
        truth = position_value <= -TRUTH_POSITION_THRESHOLD
    elif proposed == 2:
        gate = position_value >= HARD_POSITION_THRESHOLD
        truth = position_value >= TRUTH_POSITION_THRESHOLD
    else:
        gate = abs(velocity_value) <= HARD_VELOCITY_THRESHOLD
        truth = abs(velocity_value) <= TRUTH_VELOCITY_THRESHOLD
    return ReceiptClassification(
        gate=bool(gate),
        truth=bool(truth),
        label=(0 if truth else 1) if gate else None,
    )


class LogisticSemanticVeto(torch.nn.Module):
    """One zero-initialized nonrecursive logistic residual."""

    def __init__(self) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(FEATURE_DIM, 1)
        with torch.no_grad():
            self.linear.weight.zero_()
            self.linear.bias.zero_()

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        if not isinstance(features, torch.Tensor):
            raise TypeError("features must be a torch.Tensor")
        if features.dtype != torch.float32:
            raise TypeError("features must use torch.float32")
        if features.ndim != 2 or features.shape[1] != FEATURE_DIM:
            raise ValueError("features must have shape [batch, 8]")
        if not bool(torch.isfinite(features).all().item()):
            raise ValueError("features must be finite")
        return self.linear(features).squeeze(-1)

    def alias_probability(self, feature: np.ndarray) -> float:
        value = np.asarray(feature)
        if value.dtype != np.float32 or value.shape != (FEATURE_DIM,):
            raise ValueError("one feature must be float32 with shape (8,)")
        with torch.no_grad():
            logits = self(torch.from_numpy(value.reshape(1, FEATURE_DIM)))
            return float(torch.sigmoid(logits)[0].item())


@dataclass(frozen=True)
class LearnerDiagnostics:
    records: int
    positive_labels: int
    optimizer_updates: int
    initial_loss: float
    final_loss: float
    weight_l2: float
    bias: float


def deterministic_sham_labels(labels: Sequence[int], seed: int) -> np.ndarray:
    values = np.asarray(tuple(labels), dtype=np.int64)
    if values.ndim != 1 or any(int(item) not in (0, 1) for item in values):
        raise ValueError("labels must be one-dimensional binary values")
    order = np.random.Generator(np.random.PCG64(int(seed))).permutation(len(values))
    return values[order].copy()


def train_logistic_veto(
    features: np.ndarray,
    labels: Sequence[int],
    *,
    optimizer_steps: int,
) -> tuple[LogisticSemanticVeto, LearnerDiagnostics]:
    matrix = np.asarray(features)
    target_values = np.asarray(tuple(labels), dtype=np.int64)
    if matrix.dtype != np.float32 or matrix.ndim != 2 or matrix.shape[1] != FEATURE_DIM:
        raise ValueError("training features must be float32 with shape [records, 8]")
    if len(matrix) != len(target_values):
        raise ValueError("training features and labels must be aligned")
    if not np.all(np.isfinite(matrix)) or any(
        int(item) not in (0, 1) for item in target_values
    ):
        raise ValueError("training data must be finite and binary")
    steps = int(optimizer_steps)
    if steps <= 0:
        raise ValueError("optimizer_steps must be positive")

    model = LogisticSemanticVeto()
    inputs = torch.from_numpy(matrix)
    targets = torch.from_numpy(target_values.astype(np.float32, copy=False))
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        betas=ADAM_BETAS,
        eps=ADAM_EPS,
        weight_decay=0.0,
    )

    def objective() -> torch.Tensor:
        logits = model(inputs)
        penalty = sum(parameter.square().sum() for parameter in model.parameters())
        # A support-poor fixed run remains executable without fabricating a
        # row or extending its budget.  The zero-record objective is exactly
        # the registered L2 term on the zero-initialized logistic model.
        data_loss = (
            F.binary_cross_entropy_with_logits(logits, targets)
            if len(targets)
            else logits.sum() * 0.0
        )
        return data_loss + L2_COEFFICIENT * penalty

    with torch.no_grad():
        initial_loss = float(objective().item())
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = objective()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        final_loss = float(objective().item())
        weight_l2 = float(model.linear.weight.square().sum().sqrt().item())
        bias = float(model.linear.bias.item())
    return model, LearnerDiagnostics(
        records=len(target_values),
        positive_labels=int(target_values.sum()),
        optimizer_updates=steps,
        initial_loss=initial_loss,
        final_loss=final_loss,
        weight_l2=weight_l2,
        bias=bias,
    )
