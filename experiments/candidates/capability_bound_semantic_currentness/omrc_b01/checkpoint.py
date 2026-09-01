"""Checkpoint-complete recurrent PPO state with no episode-local state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

import torch

from .model import OBJECT_ID, model_parameter_digest
from .ppo import PPOCounters, PPOValidationError, RecurrentPPOTrainer, config_digest


CHECKPOINT_SCHEMA = "cbsc_omrc_b01_recurrent_ppo_checkpoint_v1"
_PAYLOAD_KEYS = frozenset(
    {
        "schema",
        "identity",
        "digests",
        "counters",
        "model_state",
        "optimizer_state",
        "minibatch_order_chain",
    }
)


class CheckpointValidationError(ValueError):
    """Raised when checkpoint state is incomplete or identity-inconsistent."""


@dataclass(frozen=True)
class CheckpointIdentity:
    run_name: str
    arm: str
    seed: int
    completed_rollout_updates: int
    object_id: str = OBJECT_ID

    def __post_init__(self) -> None:
        if self.object_id != OBJECT_ID:
            raise CheckpointValidationError("checkpoint object identity is not CBSC-OMRC-B01")
        if not self.run_name or not self.arm or type(self.seed) is not int:
            raise CheckpointValidationError("run, arm, and integer seed are required")
        if type(self.completed_rollout_updates) is not int or self.completed_rollout_updates < 0:
            raise CheckpointValidationError("completed rollout updates must be nonnegative")


@dataclass(frozen=True)
class CheckpointDigests:
    parameter_initialization: str
    training_tape: str
    action_uniform: str
    minibatch_order: str
    configuration: str

    def __post_init__(self) -> None:
        for name, digest in vars(self).items():
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise CheckpointValidationError(f"{name} must be a lowercase SHA-256 digest")


def _clone_tensor_mapping(mapping: Mapping[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in mapping.items()}


def capture_checkpoint(
    trainer: RecurrentPPOTrainer,
    *,
    arm: str,
    training_tape_digest: str,
    action_uniform_digest: str,
) -> dict[str, Any]:
    """Capture every persistent state component and no episode-local state."""

    trainer.counters.validate()
    identity = CheckpointIdentity(
        trainer.run_name,
        arm,
        trainer.seed,
        trainer.counters.rollout_updates,
    )
    digests = CheckpointDigests(
        parameter_initialization=trainer.model.initialization_digest,
        training_tape=training_tape_digest,
        action_uniform=action_uniform_digest,
        minibatch_order=trainer.minibatch_order_digest,
        configuration=config_digest(trainer.config),
    )
    optimizer_state = deepcopy(trainer.optimizer.state_dict())
    payload: dict[str, Any] = {
        "schema": CHECKPOINT_SCHEMA,
        "identity": asdict(identity),
        "digests": asdict(digests),
        "counters": asdict(trainer.counters),
        "model_state": _clone_tensor_mapping(trainer.model.state_dict()),
        "optimizer_state": optimizer_state,
        "minibatch_order_chain": trainer.minibatch_order_digest,
    }
    _validate_payload(payload)
    return payload


def _validate_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping) or frozenset(payload) != _PAYLOAD_KEYS:
        raise CheckpointValidationError("checkpoint has an incomplete or extended top-level schema")
    if payload["schema"] != CHECKPOINT_SCHEMA:
        raise CheckpointValidationError("checkpoint schema mismatch")
    try:
        identity = CheckpointIdentity(**payload["identity"])
        digests = CheckpointDigests(**payload["digests"])
        counters = PPOCounters(**payload["counters"])
        counters.validate()
    except (TypeError, PPOValidationError) as error:
        raise CheckpointValidationError("checkpoint metadata is invalid") from error
    if identity.completed_rollout_updates != counters.rollout_updates:
        raise CheckpointValidationError("checkpoint identity/update counter mismatch")
    if payload["minibatch_order_chain"] != digests.minibatch_order:
        raise CheckpointValidationError("checkpoint minibatch-order state/digest mismatch")
    if not isinstance(payload["model_state"], Mapping) or not all(
        isinstance(name, str) and isinstance(value, torch.Tensor)
        for name, value in payload["model_state"].items()
    ):
        raise CheckpointValidationError("checkpoint model state is invalid")
    if not isinstance(payload["optimizer_state"], Mapping):
        raise CheckpointValidationError("checkpoint optimizer state is invalid")
    prohibited = ("hidden", "adapter_state", "recurrent_state")
    if any(any(term in key.lower() for term in prohibited) for key in payload):
        raise CheckpointValidationError("episode-local hidden/adapter state is forbidden")


def restore_checkpoint(
    payload: Mapping[str, Any],
    trainer: RecurrentPPOTrainer,
    *,
    expected_arm: str,
    expected_training_tape_digest: str,
    expected_action_uniform_digest: str,
) -> None:
    """Restore model, Adam, counters and order chain after all identity checks."""

    _validate_payload(payload)
    identity = CheckpointIdentity(**payload["identity"])
    digests = CheckpointDigests(**payload["digests"])
    expected = CheckpointDigests(
        parameter_initialization=trainer.model.initialization_digest,
        training_tape=expected_training_tape_digest,
        action_uniform=expected_action_uniform_digest,
        minibatch_order=digests.minibatch_order,
        configuration=config_digest(trainer.config),
    )
    if (
        identity.run_name != trainer.run_name
        or identity.arm != expected_arm
        or identity.seed != trainer.seed
    ):
        raise CheckpointValidationError("checkpoint run/arm/seed identity mismatch")
    if digests != expected:
        raise CheckpointValidationError("checkpoint parameter/tape/action/config digest mismatch")

    trainer.model.load_state_dict(payload["model_state"], strict=True)
    trainer.optimizer.load_state_dict(payload["optimizer_state"])
    trainer.counters = PPOCounters(**payload["counters"])
    trainer.counters.validate()
    trainer.restore_minibatch_order_digest(payload["minibatch_order_chain"])
    if model_parameter_digest(trainer.model) != model_parameter_digest_from_state(
        payload["model_state"]
    ):
        raise CheckpointValidationError("model parameter bytes changed during restore")


def model_parameter_digest_from_state(state: Mapping[str, torch.Tensor]) -> str:
    """Use the model digest law against a state mapping without a second serializer."""

    # A tiny holder makes this function share the one canonical byte-digest law
    # in model.py instead of restating that law here.
    class _StateHolder:
        def named_parameters(self):
            return state.items()

    return model_parameter_digest(_StateHolder())  # type: ignore[arg-type]


def save_checkpoint(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Atomically persist a validated checkpoint without overwriting an existing one."""

    _validate_payload(payload)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"checkpoint already exists: {destination}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as stream:
            torch.save(dict(payload), stream)
            stream.flush()
            os.fsync(stream.fileno())
        # Atomic create-only publication: a hard-link claim fails rather than
        # replacing a destination that appears after the earlier check.
        os.link(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    with Path(path).open("rb") as stream:
        try:
            payload = torch.load(stream, map_location="cpu", weights_only=True)
        except TypeError:  # pragma: no cover - compatibility with older PyTorch
            stream.seek(0)
            payload = torch.load(stream, map_location="cpu")
    _validate_payload(payload)
    return dict(payload)
