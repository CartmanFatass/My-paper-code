"""Adaptation-free evaluation over supplied transition tapes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

import torch
from torch import nn

from .learner import PredictiveStep
from .performance import PERFORMANCE_DISPOSITION, PERFORMANCE_LIMITATIONS
from .tape import TapeValidationError, PotentialOutcomeTape, VectorizedPotentialOutcomeBatch


@runtime_checkable
class PredictivePolicy(Protocol):
    def state_dict(self) -> Mapping[str, torch.Tensor]: ...

    def initial_state(self, batch_size: int, device: torch.device | str | None = None) -> torch.Tensor: ...

    def predict(self, observation: torch.Tensor, state: torch.Tensor) -> PredictiveStep: ...


@dataclass(frozen=True)
class EvaluationReceipt:
    returns: torch.Tensor
    interactions: int
    final_state: torch.Tensor
    model_unchanged: bool
    input_state_unchanged: bool
    performance_disposition: str = PERFORMANCE_DISPOSITION
    performance_limitations: tuple[str, ...] = PERFORMANCE_LIMITATIONS


def evaluate_adaptation_free(
    tape: PotentialOutcomeTape,
    policy: PredictivePolicy,
    *,
    initial_state: torch.Tensor | None = None,
) -> EvaluationReceipt:
    """Evaluate without gradient, parameter, buffer, or caller-state mutation."""

    if not isinstance(tape, PotentialOutcomeTape):
        raise TapeValidationError("tape must be PotentialOutcomeTape")
    if not isinstance(policy, PredictivePolicy):
        raise TypeError("policy must implement initial_state and predict")
    raw_policy_state = policy.state_dict()
    if not isinstance(raw_policy_state, Mapping) or not all(
        isinstance(name, str) and isinstance(value, torch.Tensor)
        for name, value in raw_policy_state.items()
    ):
        raise TypeError("policy.state_dict must map string names to tensors")
    policy_snapshot = {
        name: value.detach().clone() for name, value in raw_policy_state.items()
    }
    prior_training: bool | None = None
    if isinstance(policy, nn.Module):
        prior_training = policy.training
    try:
        if isinstance(policy, nn.Module):
            policy.eval()
        if initial_state is None:
            state = policy.initial_state(tape.batch_size, tape.observation.device)
            caller_snapshot = None
        else:
            if not isinstance(initial_state, torch.Tensor):
                raise TypeError("initial_state must be a torch.Tensor")
            caller_snapshot = initial_state.clone()
            state = initial_state.clone()
        if state.ndim != 2 or state.shape[0] != tape.batch_size or state.dtype != torch.float32:
            raise TapeValidationError("predictive policy state must have FP32 shape [B,H]")
        if state.device != tape.observation.device or not torch.isfinite(state).all().item():
            raise TapeValidationError("predictive policy state must be finite and share the tape device")

        host = VectorizedPotentialOutcomeBatch(tape)
        returns = torch.zeros((tape.batch_size,), dtype=torch.float32, device=tape.observation.device)
        with torch.no_grad():
            while not host.exhausted:
                prediction = policy.predict(host.observation(), state)
                if not isinstance(prediction, PredictiveStep):
                    raise TypeError("policy.predict must return PredictiveStep")
                transition = host.step(prediction.action)
                if (
                    prediction.next_state.shape != state.shape
                    or prediction.next_state.dtype != torch.float32
                    or prediction.next_state.device != state.device
                    or not torch.isfinite(prediction.next_state).all().item()
                ):
                    raise TapeValidationError("policy next_state shape, dtype, device, or finiteness is invalid")
                returns.add_(transition.reward)
                state = torch.where(
                    transition.terminated.unsqueeze(1),
                    torch.zeros_like(prediction.next_state),
                    prediction.next_state,
                )
    finally:
        if isinstance(policy, nn.Module) and prior_training is not None:
            policy.train(prior_training)

    after = policy.state_dict()
    model_unchanged = set(after) == set(policy_snapshot) and all(
        isinstance(after[name], torch.Tensor) and torch.equal(after[name], value)
        for name, value in policy_snapshot.items()
    )
    if not model_unchanged:
        raise RuntimeError("adaptation-free evaluation mutated policy state")
    input_unchanged = caller_snapshot is None or torch.equal(initial_state, caller_snapshot)
    if not input_unchanged:
        raise RuntimeError("adaptation-free evaluation mutated caller state")
    return EvaluationReceipt(
        returns=returns,
        interactions=tape.batch_size * tape.horizon,
        final_state=state.clone(),
        model_unchanged=model_unchanged,
        input_state_unchanged=input_unchanged,
    )
