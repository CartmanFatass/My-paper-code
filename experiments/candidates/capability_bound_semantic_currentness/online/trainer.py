"""Bounded replay and online recurrent Q training for pilot use only."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import torch
from torch import nn

from .learner import RecurrentQLearner
from .performance import PERFORMANCE_DISPOSITION, PERFORMANCE_LIMITATIONS
from .tape import PotentialOutcomeTape, VectorizedPotentialOutcomeBatch


class TrainerValidationError(ValueError):
    """Raised when trainer state does not satisfy the frozen pilot contract."""


@dataclass(frozen=True)
class TrainerConfig:
    """Engineering-fixture parameters supplied explicitly by the caller."""

    replay_capacity: int
    batch_size: int
    warmup_interactions: int
    learning_rate: float
    gamma: float
    epsilon: float
    gradient_clip_norm: float

    def __post_init__(self) -> None:
        for name, value in (
            ("replay_capacity", self.replay_capacity),
            ("batch_size", self.batch_size),
            ("warmup_interactions", self.warmup_interactions),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise TrainerValidationError(f"{name} must be a positive integer")
        if self.batch_size > self.replay_capacity:
            raise TrainerValidationError("batch_size cannot exceed replay_capacity")
        if self.warmup_interactions > self.replay_capacity:
            raise TrainerValidationError("warmup_interactions cannot exceed replay_capacity")
        if not 0.0 < float(self.learning_rate):
            raise TrainerValidationError("learning_rate must be positive")
        if not 0.0 <= float(self.gamma) <= 1.0:
            raise TrainerValidationError("gamma must be in [0,1]")
        if not 0.0 <= float(self.epsilon) <= 1.0:
            raise TrainerValidationError("epsilon must be in [0,1]")
        if not 0.0 < float(self.gradient_clip_norm):
            raise TrainerValidationError("gradient_clip_norm must be positive")


@dataclass(frozen=True)
class TrainingReceipt:
    interactions: int
    updates: int
    mean_loss: float | None
    cursor: int
    performance_disposition: str = PERFORMANCE_DISPOSITION
    performance_limitations: tuple[str, ...] = PERFORMANCE_LIMITATIONS


class BoundedReplay:
    """Preallocated CPU FP32 ring buffer with vectorized batch insertion."""

    _TENSOR_KEYS = (
        "observation",
        "hidden",
        "action",
        "reward",
        "next_observation",
        "terminated",
    )

    def __init__(self, capacity: int, feature_dim: int, hidden_dim: int) -> None:
        for name, value in (("capacity", capacity), ("feature_dim", feature_dim), ("hidden_dim", hidden_dim)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise TrainerValidationError(f"{name} must be a positive integer")
        self.capacity = capacity
        self.feature_dim = feature_dim
        self.hidden_dim = hidden_dim
        self._storage = {
            "observation": torch.empty((capacity, feature_dim), dtype=torch.float32),
            "hidden": torch.empty((capacity, hidden_dim), dtype=torch.float32),
            "action": torch.empty((capacity,), dtype=torch.int64),
            "reward": torch.empty((capacity,), dtype=torch.float32),
            "next_observation": torch.empty((capacity, feature_dim), dtype=torch.float32),
            "terminated": torch.empty((capacity,), dtype=torch.bool),
        }
        self.size = 0
        self.position = 0

    def add_batch(
        self,
        *,
        observation: torch.Tensor,
        hidden: torch.Tensor,
        action: torch.Tensor,
        reward: torch.Tensor,
        next_observation: torch.Tensor,
        terminated: torch.Tensor,
    ) -> None:
        batch = observation.shape[0] if isinstance(observation, torch.Tensor) and observation.ndim == 2 else -1
        expected = {
            "observation": ((batch, self.feature_dim), torch.float32),
            "hidden": ((batch, self.hidden_dim), torch.float32),
            "action": ((batch,), torch.int64),
            "reward": ((batch,), torch.float32),
            "next_observation": ((batch, self.feature_dim), torch.float32),
            "terminated": ((batch,), torch.bool),
        }
        values = {
            "observation": observation,
            "hidden": hidden,
            "action": action,
            "reward": reward,
            "next_observation": next_observation,
            "terminated": terminated,
        }
        if batch <= 0:
            raise TrainerValidationError("replay insertion batch must be nonempty")
        for name, value in values.items():
            shape, dtype = expected[name]
            if not isinstance(value, torch.Tensor) or value.shape != shape or value.dtype != dtype:
                raise TrainerValidationError(f"replay {name} has wrong shape or dtype")
            if dtype == torch.float32 and not torch.isfinite(value).all().item():
                raise TrainerValidationError(f"replay {name} must be finite")
        if batch > self.capacity:
            values = {name: value[-self.capacity :] for name, value in values.items()}
            batch = self.capacity
        indices = (torch.arange(batch, dtype=torch.int64) + self.position) % self.capacity
        for name, value in values.items():
            self._storage[name].index_copy_(0, indices, value.detach().to(device="cpu"))
        self.position = (self.position + batch) % self.capacity
        self.size = min(self.capacity, self.size + batch)

    def sample(self, batch_size: int, generator: torch.Generator) -> dict[str, torch.Tensor]:
        if not isinstance(generator, torch.Generator):
            raise TrainerValidationError("replay sampling requires an explicit torch.Generator")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or not 0 < batch_size <= self.size:
            raise TrainerValidationError("sample batch_size must be in [1,replay size]")
        indices = torch.randperm(self.size, generator=generator)[:batch_size]
        return {name: value.index_select(0, indices) for name, value in self._storage.items()}

    def state_dict(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "feature_dim": self.feature_dim,
            "hidden_dim": self.hidden_dim,
            "size": self.size,
            "position": self.position,
            "storage": {name: value.clone() for name, value in self._storage.items()},
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        for name in ("capacity", "feature_dim", "hidden_dim"):
            if state.get(name) != getattr(self, name):
                raise TrainerValidationError(f"replay {name} mismatch")
        size, position = state.get("size"), state.get("position")
        if isinstance(size, bool) or not isinstance(size, int) or not 0 <= size <= self.capacity:
            raise TrainerValidationError("invalid replay size")
        if isinstance(position, bool) or not isinstance(position, int) or not 0 <= position < self.capacity:
            raise TrainerValidationError("invalid replay position")
        storage = state.get("storage")
        if not isinstance(storage, dict) or set(storage) != set(self._TENSOR_KEYS):
            raise TrainerValidationError("invalid replay storage keys")
        for name, destination in self._storage.items():
            source = storage[name]
            if not isinstance(source, torch.Tensor) or source.shape != destination.shape or source.dtype != destination.dtype:
                raise TrainerValidationError(f"invalid replay storage tensor {name}")
            destination.copy_(source)
        self.size = size
        self.position = position


class OnlineQTrainer:
    """Stateful online pilot trainer with checkpoint-complete RNG and replay."""

    def __init__(
        self,
        learner: RecurrentQLearner,
        config: TrainerConfig,
        generator: torch.Generator,
    ) -> None:
        if not isinstance(learner, RecurrentQLearner):
            raise TrainerValidationError("learner must be RecurrentQLearner")
        if not isinstance(generator, torch.Generator):
            raise TrainerValidationError("trainer requires an explicit torch.Generator")
        if next(learner.parameters()).device.type != "cpu":
            raise TrainerValidationError("pilot replay/trainer currently requires a CPU learner")
        self.learner = learner
        self.config = config
        self.generator = generator
        self.optimizer = torch.optim.Adam(self.learner.parameters(), lr=config.learning_rate)
        self.replay = BoundedReplay(config.replay_capacity, learner.feature_dim, learner.hidden_dim)
        self.interaction_count = 0
        self.update_count = 0
        self.cursor = 0
        self.hidden: torch.Tensor | None = None
        self.current_observation: torch.Tensor | None = None
        self._tape_shape: tuple[int, int, int, int] | None = None
        self._tape_digest: str | None = None

    def reset_tape(self, tape: PotentialOutcomeTape) -> None:
        self._validate_tape(tape)
        self.cursor = 0
        self.hidden = self.learner.initial_state(tape.batch_size)
        self.current_observation = tape.observation[:, 0].clone()
        self._tape_shape = (tape.batch_size, tape.horizon, tape.feature_dim, tape.action_count)
        self._tape_digest = tape.content_digest

    def run(self, tape: PotentialOutcomeTape, *, max_steps: int | None = None) -> TrainingReceipt:
        self._validate_tape(tape)
        tape_shape = (tape.batch_size, tape.horizon, tape.feature_dim, tape.action_count)
        if self.hidden is None:
            self.reset_tape(tape)
        elif self._tape_shape != tape_shape:
            raise TrainerValidationError("cannot resume trainer on a different tape shape")
        elif self._tape_digest != tape.content_digest:
            raise TrainerValidationError("cannot resume trainer on different tape content")
        if max_steps is not None and (
            isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps <= 0
        ):
            raise TrainerValidationError("max_steps must be a positive integer or None")

        host = VectorizedPotentialOutcomeBatch(tape)
        assert self.current_observation is not None
        host.load_state_dict(
            {"cursor": self.cursor, "current_observation": self.current_observation}
        )
        available = tape.horizon - self.cursor
        steps = available if max_steps is None else min(available, max_steps)
        before_interactions, before_updates = self.interaction_count, self.update_count
        losses: list[float] = []
        assert self.hidden is not None
        for _ in range(steps):
            observation = host.observation()
            hidden_in = self.hidden
            with torch.no_grad():
                prediction = self.learner.epsilon_action(
                    observation,
                    hidden_in,
                    epsilon=self.config.epsilon,
                    generator=self.generator,
                )
            transition = host.step(prediction.action)
            self.replay.add_batch(
                observation=transition.observation,
                hidden=hidden_in,
                action=transition.action,
                reward=transition.reward,
                next_observation=transition.next_observation,
                terminated=transition.terminated,
            )
            self.interaction_count += tape.batch_size
            zeros = torch.zeros_like(prediction.next_state)
            self.hidden = torch.where(
                transition.terminated.unsqueeze(1), zeros, prediction.next_state.detach()
            )
            if self.replay.size >= max(self.config.warmup_interactions, self.config.batch_size):
                losses.append(self._update())
        self.cursor = host.cursor
        self.current_observation = host.current_observation.clone()
        return TrainingReceipt(
            interactions=self.interaction_count - before_interactions,
            updates=self.update_count - before_updates,
            mean_loss=(sum(losses) / len(losses)) if losses else None,
            cursor=self.cursor,
        )

    def _update(self) -> float:
        batch = self.replay.sample(self.config.batch_size, self.generator)
        current = self.learner(batch["observation"], batch["hidden"])
        chosen_q = current.q_values.gather(1, batch["action"].unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            # The recurrent state presented to the target is detached from the
            # current path; terminal rows are masked out of the Bellman target.
            target_step = self.learner(batch["next_observation"], current.next_hidden.detach())
            bootstrap = target_step.q_values.max(dim=1).values
            target = batch["reward"] + self.config.gamma * (~batch["terminated"]).to(torch.float32) * bootstrap
        loss = nn.functional.smooth_l1_loss(chosen_q, target)
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(self.learner.parameters(), self.config.gradient_clip_norm)
        self.optimizer.step()
        self.update_count += 1
        return float(loss.detach())

    def state_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "config": self.config,
            "learner": copy.deepcopy(self.learner.state_dict()),
            "optimizer": copy.deepcopy(self.optimizer.state_dict()),
            "replay": self.replay.state_dict(),
            "generator_state": self.generator.get_state().clone(),
            "interaction_count": self.interaction_count,
            "update_count": self.update_count,
            "cursor": self.cursor,
            "hidden": None if self.hidden is None else self.hidden.clone(),
            "current_observation": (
                None if self.current_observation is None else self.current_observation.clone()
            ),
            "tape_shape": self._tape_shape,
            "tape_digest": self._tape_digest,
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        if state.get("version") != 1 or state.get("config") != self.config:
            raise TrainerValidationError("trainer checkpoint version or config mismatch")
        self.learner.load_state_dict(state["learner"], strict=True)
        self.optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
        self.replay.load_state_dict(state["replay"])
        generator_state = state.get("generator_state")
        if not isinstance(generator_state, torch.Tensor) or generator_state.dtype != torch.uint8:
            raise TrainerValidationError("invalid generator state")
        self.generator.set_state(generator_state)
        for name in ("interaction_count", "update_count", "cursor"):
            value = state.get(name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise TrainerValidationError(f"invalid checkpoint counter {name}")
            setattr(self, name, value)
        hidden = state.get("hidden")
        if hidden is not None and (
            not isinstance(hidden, torch.Tensor)
            or hidden.ndim != 2
            or hidden.shape[1] != self.learner.hidden_dim
            or hidden.dtype != torch.float32
            or hidden.device.type != "cpu"
            or not torch.isfinite(hidden).all().item()
        ):
            raise TrainerValidationError("invalid checkpoint hidden state")
        current_observation = state.get("current_observation")
        if current_observation is not None and (
            not isinstance(current_observation, torch.Tensor)
            or current_observation.ndim != 2
            or current_observation.shape[1] != self.learner.feature_dim
            or current_observation.dtype != torch.float32
            or current_observation.device.type != "cpu"
            or not torch.isfinite(current_observation).all().item()
        ):
            raise TrainerValidationError("invalid checkpoint current observation")
        tape_shape = state.get("tape_shape")
        if tape_shape is not None and (
            not isinstance(tape_shape, tuple)
            or len(tape_shape) != 4
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in tape_shape)
        ):
            raise TrainerValidationError("invalid checkpoint tape shape")
        if hidden is not None and tape_shape is not None and hidden.shape[0] != tape_shape[0]:
            raise TrainerValidationError("checkpoint hidden batch does not match tape shape")
        if current_observation is not None and tape_shape is not None and current_observation.shape[0] != tape_shape[0]:
            raise TrainerValidationError("checkpoint observation batch does not match tape shape")
        if (hidden is None) != (current_observation is None):
            raise TrainerValidationError("checkpoint recurrent and observation state must co-exist")
        if tape_shape is not None and self.cursor > tape_shape[1]:
            raise TrainerValidationError("checkpoint cursor exceeds tape horizon")
        tape_digest = state.get("tape_digest")
        if tape_digest is not None and (
            not isinstance(tape_digest, str)
            or len(tape_digest) != 64
            or any(character not in "0123456789abcdef" for character in tape_digest)
        ):
            raise TrainerValidationError("invalid checkpoint tape digest")
        if (tape_shape is None) != (tape_digest is None):
            raise TrainerValidationError("checkpoint tape shape and digest must co-exist")
        self.hidden = None if hidden is None else hidden.clone()
        self.current_observation = (
            None if current_observation is None else current_observation.clone()
        )
        self._tape_shape = tape_shape
        self._tape_digest = tape_digest

    def _validate_tape(self, tape: PotentialOutcomeTape) -> None:
        if not isinstance(tape, PotentialOutcomeTape):
            raise TrainerValidationError("tape must be PotentialOutcomeTape")
        if tape.feature_dim != self.learner.feature_dim or tape.action_count != self.learner.action_count:
            raise TrainerValidationError("tape dimensions do not match learner")
        if tape.observation.device.type != "cpu":
            raise TrainerValidationError("pilot replay/trainer currently requires a CPU tape")
