"""Common FP32 recurrent Q learner for non-result-bearing online pilots."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


class LearnerValidationError(ValueError):
    """Raised when learner input or action-selection state is invalid."""


@dataclass(frozen=True)
class QStep:
    q_values: torch.Tensor
    next_hidden: torch.Tensor


@dataclass(frozen=True)
class PredictiveStep:
    action: torch.Tensor
    next_state: torch.Tensor


class RecurrentQLearner(nn.Module):
    """One-layer GRUCell Q function with an explicit FP32 boundary."""

    def __init__(self, feature_dim: int, action_count: int, hidden_dim: int) -> None:
        super().__init__()
        for name, value in (
            ("feature_dim", feature_dim),
            ("action_count", action_count),
            ("hidden_dim", hidden_dim),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise LearnerValidationError(f"{name} must be a positive integer")
        self.feature_dim = feature_dim
        self.action_count = action_count
        self.hidden_dim = hidden_dim
        self.recurrent = nn.GRUCell(feature_dim, hidden_dim, dtype=torch.float32)
        self.q_head = nn.Linear(hidden_dim, action_count, dtype=torch.float32)

    def initial_state(self, batch_size: int, device: torch.device | str | None = None) -> torch.Tensor:
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
            raise LearnerValidationError("batch_size must be a positive integer")
        target_device = device if device is not None else next(self.parameters()).device
        return torch.zeros((batch_size, self.hidden_dim), dtype=torch.float32, device=target_device)

    def forward(self, observation: torch.Tensor, hidden: torch.Tensor) -> QStep:
        self._validate_inputs(observation, hidden)
        next_hidden = self.recurrent(observation, hidden)
        return QStep(q_values=self.q_head(next_hidden), next_hidden=next_hidden)

    def epsilon_action(
        self,
        observation: torch.Tensor,
        hidden: torch.Tensor,
        *,
        epsilon: float,
        generator: torch.Generator,
    ) -> PredictiveStep:
        if not isinstance(generator, torch.Generator):
            raise LearnerValidationError("epsilon action requires an explicit torch.Generator")
        if generator.device != observation.device:
            raise LearnerValidationError("generator and observation must share one device")
        if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)) or not 0.0 <= float(epsilon) <= 1.0:
            raise LearnerValidationError("epsilon must be in [0,1]")
        step = self(observation, hidden)
        greedy = step.q_values.argmax(dim=1)
        explore = torch.rand(
            (observation.shape[0],), generator=generator, device=observation.device
        ) < float(epsilon)
        random_action = torch.randint(
            self.action_count,
            (observation.shape[0],),
            generator=generator,
            device=observation.device,
            dtype=torch.int64,
        )
        return PredictiveStep(torch.where(explore, random_action, greedy), step.next_hidden)

    def predict(self, observation: torch.Tensor, state: torch.Tensor) -> PredictiveStep:
        step = self(observation, state)
        return PredictiveStep(step.q_values.argmax(dim=1), step.next_hidden)

    def _validate_inputs(self, observation: torch.Tensor, hidden: torch.Tensor) -> None:
        if not isinstance(observation, torch.Tensor) or observation.ndim != 2:
            raise LearnerValidationError("observation must have shape [B,F]")
        if not isinstance(hidden, torch.Tensor) or hidden.ndim != 2:
            raise LearnerValidationError("hidden must have shape [B,H]")
        if observation.shape[1] != self.feature_dim:
            raise LearnerValidationError("observation feature dimension mismatch")
        if hidden.shape != (observation.shape[0], self.hidden_dim):
            raise LearnerValidationError("hidden shape mismatch")
        if observation.dtype != torch.float32 or hidden.dtype != torch.float32:
            raise LearnerValidationError("learner inputs must use torch.float32")
        parameter = next(self.parameters())
        if observation.device != parameter.device or hidden.device != parameter.device:
            raise LearnerValidationError("learner inputs and parameters must share one device")
        if not torch.isfinite(observation).all().item() or not torch.isfinite(hidden).all().item():
            raise LearnerValidationError("learner inputs must be finite")
