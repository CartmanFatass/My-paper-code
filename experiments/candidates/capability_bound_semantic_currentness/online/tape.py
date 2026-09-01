"""Typed vectorized potential-outcome transition tapes.

This is a transition substrate, not a complete dynamic scientific host.  An
EM-supplied row provides the action potential outcomes for the current state.
The substrate carries the chosen next state forward on nonterminal lanes and
uses the following row's observation only as a terminal-lane reset state.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import torch


class TapeValidationError(ValueError):
    """Raised when a transition tape or host action violates its contract."""


@dataclass(frozen=True)
class PotentialOutcomeTape:
    """A batch of exogenously supplied transition opportunities.

    No reward, transition, population, or arm schedule is generated here.
    Each ``(batch, time)`` row supplies outcomes for every discrete action.
    ``observation[:, 0]`` is the initial state; later observation rows are
    reset states consumed only for lanes terminated by the preceding action.
    """

    observation: torch.Tensor
    action_reward: torch.Tensor
    next_observation: torch.Tensor
    terminated: torch.Tensor

    def __post_init__(self) -> None:
        tensors = (self.observation, self.action_reward, self.next_observation, self.terminated)
        if not all(isinstance(value, torch.Tensor) for value in tensors):
            raise TapeValidationError("all tape fields must be torch.Tensor instances")
        if self.observation.ndim != 3:
            raise TapeValidationError("observation must have shape [B,T,F]")
        if self.action_reward.ndim != 3:
            raise TapeValidationError("action_reward must have shape [B,T,A]")
        if self.next_observation.ndim != 4:
            raise TapeValidationError("next_observation must have shape [B,T,A,F]")
        if self.terminated.ndim != 3:
            raise TapeValidationError("terminated must have shape [B,T,A]")
        batch, horizon, features = self.observation.shape
        if min(batch, horizon, features) <= 0:
            raise TapeValidationError("B, T, and F must be positive")
        action_shape = self.action_reward.shape
        if action_shape[:2] != (batch, horizon) or action_shape[2] <= 0:
            raise TapeValidationError("action_reward leading dimensions must match observation")
        actions = action_shape[2]
        if self.next_observation.shape != (batch, horizon, actions, features):
            raise TapeValidationError("next_observation must have shape [B,T,A,F]")
        if self.terminated.shape != (batch, horizon, actions):
            raise TapeValidationError("terminated must have shape [B,T,A]")
        devices = {value.device for value in tensors}
        if len(devices) != 1:
            raise TapeValidationError("all tape tensors must share one device")
        for name, value in (
            ("observation", self.observation),
            ("action_reward", self.action_reward),
            ("next_observation", self.next_observation),
        ):
            if value.dtype != torch.float32:
                raise TapeValidationError(f"{name} must use torch.float32")
            if not torch.isfinite(value).all().item():
                raise TapeValidationError(f"{name} must contain only finite values")
        if self.terminated.dtype != torch.bool:
            raise TapeValidationError("terminated must use torch.bool")

    @property
    def batch_size(self) -> int:
        return self.observation.shape[0]

    @property
    def horizon(self) -> int:
        return self.observation.shape[1]

    @property
    def feature_dim(self) -> int:
        return self.observation.shape[2]

    @property
    def action_count(self) -> int:
        return self.action_reward.shape[2]

    @property
    def content_digest(self) -> str:
        """Stable SHA-256 over field names, shapes, dtypes, and CPU bytes."""

        digest = hashlib.sha256(b"cbsc-potential-outcome-tape-v1\0")
        for name, value in (
            ("observation", self.observation),
            ("action_reward", self.action_reward),
            ("next_observation", self.next_observation),
            ("terminated", self.terminated),
        ):
            digest.update(name.encode("ascii"))
            digest.update(b"\0")
            digest.update(str(value.dtype).encode("ascii"))
            digest.update(b"\0")
            digest.update(",".join(str(size) for size in value.shape).encode("ascii"))
            digest.update(b"\0")
            digest.update(value.detach().to(device="cpu").contiguous().numpy().tobytes(order="C"))
            digest.update(b"\0")
        return digest.hexdigest()


@dataclass(frozen=True)
class StepBatch:
    observation: torch.Tensor
    action: torch.Tensor
    reward: torch.Tensor
    next_observation: torch.Tensor
    terminated: torch.Tensor


class VectorizedPotentialOutcomeBatch:
    """Open-loop batch whose action selection is one batched gather.

    ``terminated`` masks Bellman bootstrap and resets recurrent state.  It does
    not remove a lane from later, independent open-loop opportunities.
    """

    def __init__(self, tape: PotentialOutcomeTape) -> None:
        self.tape = tape
        self.cursor = 0
        self.current_observation = tape.observation[:, 0].clone()

    @property
    def exhausted(self) -> bool:
        return self.cursor >= self.tape.horizon

    def observation(self) -> torch.Tensor:
        if self.exhausted:
            raise TapeValidationError("transition tape is exhausted")
        return self.current_observation

    def step(self, action: torch.Tensor) -> StepBatch:
        if self.exhausted:
            raise TapeValidationError("transition tape is exhausted")
        if not isinstance(action, torch.Tensor) or action.shape != (self.tape.batch_size,):
            raise TapeValidationError("action must have shape [B]")
        if action.dtype != torch.int64:
            raise TapeValidationError("action must use torch.int64")
        if action.device != self.tape.observation.device:
            raise TapeValidationError("action and tape must be on the same device")
        if not torch.all((action >= 0) & (action < self.tape.action_count)).item():
            raise TapeValidationError("action index is out of bounds")

        time = self.cursor
        reward_row = self.tape.action_reward[:, time]
        next_row = self.tape.next_observation[:, time]
        done_row = self.tape.terminated[:, time]
        scalar_index = action.unsqueeze(1)
        feature_index = scalar_index.unsqueeze(2).expand(-1, 1, self.tape.feature_dim)
        reward = reward_row.gather(1, scalar_index).squeeze(1)
        next_observation = next_row.gather(1, feature_index).squeeze(1)
        terminated = done_row.gather(1, scalar_index).squeeze(1)
        result = StepBatch(
            observation=self.current_observation,
            action=action,
            reward=reward,
            next_observation=next_observation,
            terminated=terminated,
        )
        self.cursor += 1
        if not self.exhausted:
            reset_observation = self.tape.observation[:, self.cursor]
            self.current_observation = torch.where(
                terminated.unsqueeze(1), reset_observation, next_observation
            ).clone()
        else:
            self.current_observation = next_observation.clone()
        return result

    def state_dict(self) -> dict[str, object]:
        return {"cursor": self.cursor, "current_observation": self.current_observation.clone()}

    def load_state_dict(self, state: dict[str, object]) -> None:
        if set(state) != {"cursor", "current_observation"}:
            raise TapeValidationError("host state must contain cursor and current_observation")
        cursor = state["cursor"]
        if isinstance(cursor, bool) or not isinstance(cursor, int) or not 0 <= cursor <= self.tape.horizon:
            raise TapeValidationError("host cursor is invalid for this tape")
        current = state["current_observation"]
        if (
            not isinstance(current, torch.Tensor)
            or current.shape != (self.tape.batch_size, self.tape.feature_dim)
            or current.dtype != torch.float32
            or current.device != self.tape.observation.device
            or not torch.isfinite(current).all().item()
        ):
            raise TapeValidationError("host current_observation is invalid for this tape")
        self.cursor = cursor
        self.current_observation = current.clone()
