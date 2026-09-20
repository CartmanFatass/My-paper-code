"""Gate-only checkpoints at completed episode/update boundaries.

Saved state comprises the actor, critic, their Adam optimizers, the explicit
gate sampler, the policy's supported private samplers, and PPO's minibatch
generator. Environment/foundation RNG, global RNG, foundation state, and
mid-episode GRU state are outside this format.

Loading requires an exact expected binding and returns fresh learner objects;
a failed load never partially mutates a caller's live learner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, TypeVar

import torch

from .policy import MaskPolicy, PPOUpdater, PolicyMode, ValueCritic


_FORMAT = "team-conditioned-termination-gate-v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SOURCE_SHA = re.compile(r"[0-9a-f]{40}")
_T = TypeVar("_T")


def _canonical_json(name: str, value: Mapping[str, Any]) -> str:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")

    def check(item: Any, path: str) -> None:
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError(f"{path} must contain only finite floats")
            return
        if isinstance(item, list):
            for index, child in enumerate(item):
                check(child, f"{path}[{index}]")
            return
        if isinstance(item, Mapping):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise TypeError(f"{path} keys must be strings")
                check(child, f"{path}.{key}")
            return
        raise TypeError(f"{path} contains unsupported metadata type {type(item).__name__}")

    check(value, name)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _validated_json(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"checkpoint {name} must be canonical JSON text")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"checkpoint {name} is not valid JSON") from error
    canonical = _canonical_json(name, decoded)
    if canonical != value:
        raise ValueError(f"checkpoint {name} is not canonical JSON")
    return value


@dataclass(frozen=True)
class GateArchitecture:
    """Exact actor/critic shape and policy sampler initialization."""

    context_dim: int
    n_agents: int
    policy_hidden_size: int
    critic_hidden_size: int
    end_probability: float
    policy_sample_seed: int

    def validated(self) -> GateArchitecture:
        for name in ("context_dim", "n_agents", "policy_hidden_size", "critic_hidden_size"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not math.isfinite(self.end_probability) or not 0.0 < self.end_probability < 1.0:
            raise ValueError("end_probability must be finite and strictly between zero and one")
        if isinstance(self.policy_sample_seed, bool) or not isinstance(
            self.policy_sample_seed, int
        ):
            raise TypeError("policy_sample_seed must be an integer")
        return self


@dataclass(frozen=True)
class GateTrainingConfig:
    """All PPO settings currently exposed by :class:`PPOUpdater`."""

    learning_rate: float
    critic_learning_rate: float
    clip_epsilon: float
    entropy_coef: float
    value_coef: float
    max_grad_norm: float
    epochs: int
    minibatch_size: int

    def validated(self) -> GateTrainingConfig:
        for name in (
            "learning_rate",
            "critic_learning_rate",
            "clip_epsilon",
            "value_coef",
            "max_grad_norm",
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(self.entropy_coef) or self.entropy_coef < 0.0:
            raise ValueError("entropy_coef must be finite and nonnegative")
        for name in ("epochs", "minibatch_size"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        return self


@dataclass(frozen=True)
class GateCheckpointBinding:
    """Immutable identity and configuration expected by a checkpoint consumer."""

    arm: str
    mode: PolicyMode
    foundation_sha256: str
    source_sha: str
    feature_config_json: str
    rule_config_json: str
    architecture: GateArchitecture
    training: GateTrainingConfig

    @classmethod
    def create(
        cls,
        *,
        arm: str,
        mode: PolicyMode,
        foundation_sha256: str,
        source_sha: str,
        feature_config: Mapping[str, Any],
        rule_config: Mapping[str, Any],
        architecture: GateArchitecture,
        training: GateTrainingConfig,
    ) -> GateCheckpointBinding:
        return cls(
            arm=arm,
            mode=mode,
            foundation_sha256=foundation_sha256,
            source_sha=source_sha,
            feature_config_json=_canonical_json("feature_config", feature_config),
            rule_config_json=_canonical_json("rule_config", rule_config),
            architecture=architecture,
            training=training,
        ).validated()

    def validated(self) -> GateCheckpointBinding:
        if not isinstance(self.arm, str) or not self.arm:
            raise ValueError("arm must be a nonempty string")
        if self.mode not in ("joint", "independent"):
            raise ValueError("mode must be 'joint' or 'independent'")
        if not isinstance(self.foundation_sha256, str) or not _SHA256.fullmatch(
            self.foundation_sha256
        ):
            raise ValueError("foundation_sha256 must be 64 lowercase hexadecimal characters")
        if not isinstance(self.source_sha, str) or not _SOURCE_SHA.fullmatch(self.source_sha):
            raise ValueError("source_sha must be 40 lowercase hexadecimal characters")
        _validated_json("feature_config", self.feature_config_json)
        _validated_json("rule_config", self.rule_config_json)
        if not isinstance(self.architecture, GateArchitecture) or not isinstance(
            self.training, GateTrainingConfig
        ):
            raise TypeError("architecture and training must use checkpoint config types")
        self.architecture.validated()
        self.training.validated()
        return self


@dataclass(frozen=True)
class GateProgress:
    completed_episodes: int
    completed_updates: int

    def validated(self) -> GateProgress:
        for name in ("completed_episodes", "completed_updates"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        return self


@dataclass(frozen=True)
class RestoredGateCheckpoint:
    policy: MaskPolicy
    critic: ValueCritic
    updater: PPOUpdater
    gate_sampler: torch.Generator
    binding: GateCheckpointBinding
    progress: GateProgress


def _plain_dataclass(cls: type[_T], value: Any, name: str) -> _T:
    if not isinstance(value, dict) or set(value) != {field.name for field in fields(cls)}:
        raise ValueError(f"checkpoint {name} has unexpected fields")
    try:
        return cls(**value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"checkpoint {name} is malformed") from error


def _binding_from_payload(value: Any) -> GateCheckpointBinding:
    if not isinstance(value, dict) or set(value) != {
        field.name for field in fields(GateCheckpointBinding)
    }:
        raise ValueError("checkpoint binding has unexpected fields")
    raw = dict(value)
    raw["architecture"] = _plain_dataclass(
        GateArchitecture, raw["architecture"], "architecture"
    )
    raw["training"] = _plain_dataclass(
        GateTrainingConfig, raw["training"], "training"
    )
    try:
        return GateCheckpointBinding(**raw).validated()
    except (TypeError, ValueError) as error:
        raise ValueError("checkpoint binding is malformed") from error


_ADAM_DEFAULTS = {
    "betas": (0.9, 0.999),
    "eps": 1e-8,
    "weight_decay": 0,
    "amsgrad": False,
    "maximize": False,
    "foreach": None,
    "capturable": False,
    "differentiable": False,
    "fused": None,
    "decoupled_weight_decay": False,
}


def _check_optimizer(
    name: str,
    optimizer: torch.optim.Optimizer,
    parameters: list[torch.nn.Parameter],
    learning_rate: float,
) -> None:
    if not isinstance(optimizer, torch.optim.Adam) or len(optimizer.param_groups) != 1:
        raise TypeError(f"{name} must be one-group Adam")
    group = optimizer.param_groups[0]
    if group["lr"] != learning_rate or any(
        group.get(key) != expected for key, expected in _ADAM_DEFAULTS.items()
    ):
        raise ValueError(f"{name} Adam configuration does not match PPOUpdater")
    if len(group["params"]) != len(parameters) or any(
        actual is not expected for actual, expected in zip(group["params"], parameters)
    ):
        raise ValueError(f"{name} optimizer parameters do not match its module")


def _check_live(
    policy: MaskPolicy,
    critic: ValueCritic,
    updater: PPOUpdater,
    binding: GateCheckpointBinding,
) -> None:
    architecture, training = binding.architecture, binding.training
    if updater.policy is not policy or updater.critic is not critic:
        raise ValueError("updater must own the supplied policy and critic")
    if (
        policy.context_dim != architecture.context_dim
        or critic.context_dim != architecture.context_dim
        or policy.n_agents != architecture.n_agents
        or policy.hidden_size != architecture.policy_hidden_size
        or critic.hidden_size != architecture.critic_hidden_size
        or policy._sample_seed != architecture.policy_sample_seed
        or policy.mode != binding.mode
    ):
        raise ValueError("live learner architecture does not match checkpoint binding")
    logit = torch.tensor(
        math.log(architecture.end_probability / (1.0 - architecture.end_probability)),
        dtype=policy.actor.initial_logit.dtype,
        device=policy.actor.initial_logit.device,
    )
    if not torch.equal(policy.actor.initial_logit, logit):
        raise ValueError("live policy end probability does not match checkpoint binding")
    if (
        updater.epochs,
        updater.minibatch_size,
        updater.clip_epsilon,
        updater.entropy_coef,
        updater.value_coef,
        updater.max_grad_norm,
    ) != (
        training.epochs,
        training.minibatch_size,
        training.clip_epsilon,
        training.entropy_coef,
        training.value_coef,
        training.max_grad_norm,
    ):
        raise ValueError("live updater settings do not match checkpoint binding")
    _check_optimizer(
        "actor", updater.actor_optimizer, list(policy.parameters()), training.learning_rate
    )
    _check_optimizer(
        "critic",
        updater.critic_optimizer,
        list(critic.parameters()),
        training.critic_learning_rate,
    )


def _rng_state(name: str, generator: torch.Generator) -> torch.Tensor:
    if str(generator.device) != "cpu":
        raise ValueError(f"{name} checkpoint supports a CPU generator only")
    return generator.get_state()


def _validated_rng_state(name: str, state: Any) -> torch.Tensor:
    if (
        not isinstance(state, torch.Tensor)
        or state.device.type != "cpu"
        or state.dtype != torch.uint8
        or state.ndim != 1
    ):
        raise ValueError(f"checkpoint {name} is not a CPU generator state")
    try:
        torch.Generator(device="cpu").set_state(state)
    except RuntimeError as error:
        raise ValueError(f"checkpoint {name} is not a valid generator state") from error
    return state


def _cpu_module_state(name: str, module: torch.nn.Module) -> dict[str, torch.Tensor]:
    state = module.state_dict()
    if any(tensor.device.type != "cpu" for tensor in state.values()):
        raise ValueError(f"{name} checkpoint supports CPU tensor state only")
    return state


def save_gate_checkpoint(
    path: str | Path,
    *,
    policy: MaskPolicy,
    critic: ValueCritic,
    updater: PPOUpdater,
    gate_sampler: torch.Generator,
    binding: GateCheckpointBinding,
    progress: GateProgress,
) -> None:
    """Save all gate-owned state without consuming any RNG stream."""

    binding.validated()
    progress.validated()
    _check_live(policy, critic, updater, binding)
    policy_samplers: dict[str, torch.Tensor] = {}
    for device, generator in policy._sample_generators.items():
        if device != "cpu" or str(generator.device) != device:
            raise ValueError("policy checkpoint supports CPU private samplers only")
        policy_samplers[device] = _rng_state("policy sampler", generator)
    torch.save(
        {
            "format": _FORMAT,
            "binding": asdict(binding),
            "progress": asdict(progress),
            "policy_state": _cpu_module_state("policy", policy),
            "critic_state": _cpu_module_state("critic", critic),
            "actor_optimizer_state": updater.actor_optimizer.state_dict(),
            "critic_optimizer_state": updater.critic_optimizer.state_dict(),
            "gate_sampler_state": _rng_state("gate sampler", gate_sampler),
            "policy_sampler_states": policy_samplers,
            "shuffle_generator_state": _rng_state(
                "minibatch shuffle generator", updater._shuffle_generator
            ),
        },
        Path(path),
    )


def _module_state(name: str, saved: Any, module: torch.nn.Module) -> dict[str, torch.Tensor]:
    template = module.state_dict()
    if not isinstance(saved, dict) or set(saved) != set(template):
        raise ValueError(f"checkpoint {name} state keys do not match the architecture")
    for key, expected in template.items():
        value = saved[key]
        if (
            not isinstance(value, torch.Tensor)
            or value.device.type != "cpu"
            or value.shape != expected.shape
            or value.dtype != expected.dtype
        ):
            raise ValueError(f"checkpoint {name}.{key} tensor metadata does not match")
    return saved


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return left.dtype == right.dtype and left.shape == right.shape and torch.equal(left, right)
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(_same(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def _restore_optimizer(name: str, optimizer: torch.optim.Optimizer, saved: Any) -> None:
    if not isinstance(saved, dict):
        raise ValueError(f"checkpoint {name} optimizer state is malformed")
    try:
        optimizer.load_state_dict(saved)
    except (TypeError, ValueError, RuntimeError, KeyError) as error:
        raise ValueError(f"checkpoint {name} optimizer state is malformed") from error
    if not _same(saved, optimizer.state_dict()):
        raise ValueError(f"checkpoint {name} optimizer state changed during strict restore")
    parameters = {parameter for group in optimizer.param_groups for parameter in group["params"]}
    expected_fields = {"step", "exp_avg", "exp_avg_sq"}
    if optimizer.param_groups[0]["amsgrad"]:
        expected_fields.add("max_exp_avg_sq")
    if not set(optimizer.state).issubset(parameters):
        raise ValueError(f"checkpoint {name} optimizer references an unknown parameter")
    for parameter, state in optimizer.state.items():
        if not isinstance(state, dict) or set(state) != expected_fields:
            raise ValueError(f"checkpoint {name} Adam moment fields are malformed")
        step = state["step"]
        if (
            not isinstance(step, torch.Tensor)
            or step.device.type != "cpu"
            or step.ndim != 0
            or not bool(torch.isfinite(step))
            or float(step) < 0.0
        ):
            raise ValueError(f"checkpoint {name} Adam step is malformed")
        for field in expected_fields - {"step"}:
            moment = state[field]
            if (
                not isinstance(moment, torch.Tensor)
                or moment.device != parameter.device
                or moment.dtype != parameter.dtype
                or moment.shape != parameter.shape
                or not bool(torch.isfinite(moment).all())
            ):
                raise ValueError(f"checkpoint {name} Adam {field} is malformed")


def load_gate_checkpoint(
    path: str | Path, *, expected_binding: GateCheckpointBinding
) -> RestoredGateCheckpoint:
    """Restore fresh gate objects after validating the complete caller binding."""

    expected_binding.validated()
    payload = torch.load(Path(path), map_location="cpu", weights_only=True)
    expected_fields = {
        "format",
        "binding",
        "progress",
        "policy_state",
        "critic_state",
        "actor_optimizer_state",
        "critic_optimizer_state",
        "gate_sampler_state",
        "policy_sampler_states",
        "shuffle_generator_state",
    }
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise ValueError("checkpoint payload has unexpected fields")
    if payload["format"] != _FORMAT:
        raise ValueError("unsupported gate checkpoint format")
    binding = _binding_from_payload(payload["binding"])
    if binding != expected_binding:
        raise ValueError("checkpoint binding does not match expected binding")
    progress = _plain_dataclass(GateProgress, payload["progress"], "progress").validated()

    architecture, training = binding.architecture, binding.training
    policy = MaskPolicy(
        architecture.context_dim,
        architecture.n_agents,
        binding.mode,
        hidden_size=architecture.policy_hidden_size,
        seed=architecture.policy_sample_seed,
        end_probability=architecture.end_probability,
    )
    critic = ValueCritic(
        architecture.context_dim, hidden_size=architecture.critic_hidden_size, seed=0
    )
    updater = PPOUpdater(
        policy,
        critic,
        learning_rate=training.learning_rate,
        critic_learning_rate=training.critic_learning_rate,
        clip_epsilon=training.clip_epsilon,
        entropy_coef=training.entropy_coef,
        value_coef=training.value_coef,
        max_grad_norm=training.max_grad_norm,
        epochs=training.epochs,
        minibatch_size=training.minibatch_size,
        seed=0,
    )
    policy.load_state_dict(_module_state("policy", payload["policy_state"], policy), strict=True)
    critic.load_state_dict(_module_state("critic", payload["critic_state"], critic), strict=True)
    _restore_optimizer("actor", updater.actor_optimizer, payload["actor_optimizer_state"])
    _restore_optimizer("critic", updater.critic_optimizer, payload["critic_optimizer_state"])

    gate_state = _validated_rng_state("gate_sampler_state", payload["gate_sampler_state"])
    shuffle_state = _validated_rng_state(
        "shuffle_generator_state", payload["shuffle_generator_state"]
    )
    sampler_states = payload["policy_sampler_states"]
    if not isinstance(sampler_states, dict) or set(sampler_states) - {"cpu"}:
        raise ValueError("checkpoint policy sampler states contain unsupported devices")
    sampler_states = {
        device: _validated_rng_state(f"policy_sampler_states.{device}", state)
        for device, state in sampler_states.items()
    }
    gate_sampler = torch.Generator(device="cpu")
    gate_sampler.set_state(gate_state)
    updater._shuffle_generator.set_state(shuffle_state)
    policy._sample_generators.clear()
    for device, state in sampler_states.items():
        generator = torch.Generator(device=device)
        generator.set_state(state)
        policy._sample_generators[device] = generator
    _check_live(policy, critic, updater, binding)
    return RestoredGateCheckpoint(policy, critic, updater, gate_sampler, binding, progress)
