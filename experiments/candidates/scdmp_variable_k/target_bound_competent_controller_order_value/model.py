"""Exact controller models for the SCDMP TBCC revision-02 empirical service.

Importing this module is preactivity-safe: schemas allocate no parameters and
materialization is possible only through caller-supplied permit and uniform
interfaces.  The module owns no random generator, empirical identity, file, or
checkpoint path.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
import hashlib
import math
from typing import Final, Protocol, Sequence, runtime_checkable

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .contracts import (
    ACTION_COUNT,
    FOUNDATION_ACTOR_PARAMETER_COUNT,
    FOUNDATION_CRITIC_PARAMETER_COUNT,
    FOUNDATION_PARAMETER_COUNT,
    FREE_RESIDUAL_PARAMETER_COUNT,
    FREE_TRAINABLE_PARAMETER_COUNT,
    K_TARGET,
    K_TRAIN,
    ORDER_CRITIC_PARAMETER_COUNT,
    SET_TRAINABLE_PARAMETER_COUNT,
    TREAT_SCALE_PARAMETER_COUNT,
    TREAT_TRAINABLE_PARAMETER_COUNT,
)
from .controller_conformance import graph_slack_scores, set_scores


CARD_REVISION: Final[str] = "SCDMP-TBCC-ORDER-VALUE-SCIENCE-20260821-02"
OBSERVATION_WIDTH: Final[int] = 18
FOUNDATION_WIDTH: Final[int] = 96
SCALE_WIDTH: Final[int] = 32
ORDER_WIDTH: Final[int] = 64
ALLOWED_CURRENT_K: Final[frozenset[int]] = frozenset((5, 7, 11, 13))


class ModelContractError(ValueError):
    """A materialized controller differs from revision 02."""


class LearnedOrderArm(str, Enum):
    TREAT = "TREAT"
    FREE = "FREE"
    SET = "SET"


@runtime_checkable
class InitializationUniformSource(Protocol):
    """Caller-owned address-stable initialization stream."""

    def initialization_uniforms(
        self,
        *,
        replicate: int,
        arm: str,
        tensor_name: str,
        count: int,
    ) -> Sequence[float]:
        """Return exactly ``count`` fresh U[0,1) values in row-major order."""


@runtime_checkable
class ModelMaterializationPermit(Protocol):
    """Authority adapter issued by a future runner; this package issues none."""

    def require_model_materialization(
        self,
        *,
        card_revision: str,
        replicate: int,
        arm: str,
        initialization_source: InitializationUniformSource,
    ) -> None:
        """Raise unless this exact materialization is authorized."""

    def require_foundation_clone(
        self,
        *,
        card_revision: str,
        replicate: int,
        arm: str,
        foundation_digest: str,
    ) -> None:
        """Raise unless this immutable foundation clone is authorized."""


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    shape: tuple[int, ...]
    initialization: str

    @property
    def count(self) -> int:
        return math.prod(self.shape)


@dataclass(frozen=True)
class ModelSchema:
    arm: str
    parameter_count: int
    trainable_parameter_count: int
    frozen_foundation_parameter_count: int
    chronology_input: str
    per_k_heads: int = 0
    recurrent_state: bool = False


@dataclass(frozen=True)
class FoundationOutput:
    logits: Tensor
    value: Tensor


@dataclass(frozen=True)
class OrderOutput:
    logits: Tensor
    value: Tensor
    alpha: Tensor
    physical_q: Tensor
    compositor_q: Tensor
    scores: Tensor


def _affine_specs(
    prefix: str,
    dimensions: Sequence[int],
    *,
    final_initialization: str = "row_major_xavier_uniform",
) -> tuple[ParameterSpec, ...]:
    rows: list[ParameterSpec] = []
    last = len(dimensions) - 2
    for index, (fan_in, fan_out) in enumerate(zip(dimensions, dimensions[1:])):
        initialization = final_initialization if index == last else "row_major_xavier_uniform"
        rows.extend(
            (
                ParameterSpec(f"{prefix}.{index}.weight", (fan_out, fan_in), initialization),
                ParameterSpec(
                    f"{prefix}.{index}.bias",
                    (fan_out,),
                    "constant_0.001" if initialization == "zero_weight_bias_0.001" else "zeros",
                ),
            )
        )
    return tuple(rows)


def parameter_schema(arm: str | LearnedOrderArm) -> tuple[ParameterSpec, ...]:
    """Return a complete schema without allocating a controller."""

    name = arm.value if isinstance(arm, LearnedOrderArm) else str(arm)
    if name == "FOUNDATION":
        return _affine_specs("actor.layers", (18, 96, 96, 18)) + _affine_specs(
            "critic.layers", (18, 96, 96, 1)
        )
    try:
        learned = LearnedOrderArm(name)
    except ValueError as exc:
        raise ModelContractError("arm must be FOUNDATION, TREAT, FREE, or SET") from exc
    rows = _affine_specs(
        "scale.layers", (18, 32, 1), final_initialization="zero_weight_bias_0.001"
    ) + _affine_specs("critic.layers", (19, 64, 64, 1))
    if learned in (LearnedOrderArm.FREE, LearnedOrderArm.SET):
        rows += _affine_specs(
            "residual.layers", (19, 64, 64, 18), final_initialization="zeros"
        )
    return rows


def model_schema(arm: str | LearnedOrderArm) -> ModelSchema:
    name = arm.value if isinstance(arm, LearnedOrderArm) else str(arm)
    count = sum(row.count for row in parameter_schema(name))
    expected = {
        "FOUNDATION": FOUNDATION_PARAMETER_COUNT,
        "TREAT": TREAT_TRAINABLE_PARAMETER_COUNT,
        "FREE": FREE_TRAINABLE_PARAMETER_COUNT,
        "SET": SET_TRAINABLE_PARAMETER_COUNT,
    }[name]
    if count != expected:
        raise RuntimeError(f"static {name} parameter schema drifted: {count} != {expected}")
    return ModelSchema(
        arm=name,
        parameter_count=count if name == "FOUNDATION" else count + FOUNDATION_ACTOR_PARAMETER_COUNT,
        trainable_parameter_count=count,
        frozen_foundation_parameter_count=0 if name == "FOUNDATION" else FOUNDATION_ACTOR_PARAMETER_COUNT,
        chronology_input=(
            "absent" if name == "FOUNDATION" else "q_SET=0.5" if name == "SET" else "true_q"
        ),
    )


def validate_static_model_contract() -> dict[str, int]:
    counts = {name: model_schema(name).trainable_parameter_count for name in ("FOUNDATION", "TREAT", "FREE", "SET")}
    expected = {
        "FOUNDATION": FOUNDATION_PARAMETER_COUNT,
        "TREAT": TREAT_TRAINABLE_PARAMETER_COUNT,
        "FREE": FREE_TRAINABLE_PARAMETER_COUNT,
        "SET": SET_TRAINABLE_PARAMETER_COUNT,
    }
    if counts != expected:
        raise RuntimeError("revision-02 model parameter counts differ")
    if FOUNDATION_PARAMETER_COUNT != FOUNDATION_ACTOR_PARAMETER_COUNT + FOUNDATION_CRITIC_PARAMETER_COUNT:
        raise RuntimeError("foundation actor/critic total differs")
    if TREAT_TRAINABLE_PARAMETER_COUNT != TREAT_SCALE_PARAMETER_COUNT + ORDER_CRITIC_PARAMETER_COUNT:
        raise RuntimeError("TREAT scale/critic total differs")
    if FREE_TRAINABLE_PARAMETER_COUNT != TREAT_TRAINABLE_PARAMETER_COUNT + FREE_RESIDUAL_PARAMETER_COUNT:
        raise RuntimeError("FREE total differs")
    if SET_TRAINABLE_PARAMETER_COUNT != FREE_TRAINABLE_PARAMETER_COUNT:
        raise RuntimeError("SET and FREE trainable sizes differ")
    return counts


def row_major_xavier_from_uniforms(
    uniforms: Sequence[float], *, fan_in: int, fan_out: int
) -> Tensor:
    values = tuple(uniforms)
    if len(values) != fan_in * fan_out:
        raise ModelContractError("initialization uniform count differs from affine shape")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ModelContractError("initialization uniforms must be real scalars")
    tensor = torch.tensor(values, dtype=torch.float32)
    if not bool(torch.isfinite(tensor).all()) or not bool(torch.all((tensor >= 0.0) & (tensor < 1.0))):
        raise ModelContractError("initialization uniforms must be finite and lie in [0,1)")
    bound = torch.tensor(math.sqrt(6.0 / float(fan_in + fan_out)), dtype=torch.float32)
    return ((tensor * 2.0 - 1.0) * bound).reshape(fan_out, fan_in).contiguous()


class _ExactAffine(nn.Module):
    def __init__(
        self,
        fan_in: int,
        fan_out: int,
        *,
        source: InitializationUniformSource,
        replicate: int,
        arm: str,
        tensor_name: str,
        initialization: str = "row_major_xavier_uniform",
    ) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.empty((fan_out, fan_in), dtype=torch.float32))
        self.bias = nn.Parameter(torch.empty((fan_out,), dtype=torch.float32))
        with torch.no_grad():
            if initialization in ("zeros", "zero_weight_bias_0.001"):
                self.weight.zero_()
            elif initialization == "row_major_xavier_uniform":
                self.weight.copy_(
                    row_major_xavier_from_uniforms(
                        source.initialization_uniforms(
                            replicate=replicate,
                            arm=arm,
                            tensor_name=f"{tensor_name}.weight",
                            count=fan_in * fan_out,
                        ),
                        fan_in=fan_in,
                        fan_out=fan_out,
                    )
                )
            else:  # pragma: no cover - internal schema guard
                raise RuntimeError("unknown initialization law")
            self.bias.fill_(0.001 if initialization == "zero_weight_bias_0.001" else 0.0)

    def forward(self, value: Tensor) -> Tensor:
        return F.linear(value, self.weight, self.bias)


class _ExactMlp(nn.Module):
    def __init__(
        self,
        dimensions: Sequence[int],
        *,
        source: InitializationUniformSource,
        replicate: int,
        arm: str,
        prefix: str,
        final_initialization: str = "row_major_xavier_uniform",
    ) -> None:
        super().__init__()
        last = len(dimensions) - 2
        self.layers = nn.ModuleList(
            _ExactAffine(
                fan_in,
                fan_out,
                source=source,
                replicate=replicate,
                arm=arm,
                tensor_name=f"{prefix}.{index}",
                initialization=final_initialization if index == last else "row_major_xavier_uniform",
            )
            for index, (fan_in, fan_out) in enumerate(zip(dimensions, dimensions[1:]))
        )

    def forward(self, value: Tensor) -> Tensor:
        for layer in self.layers[:-1]:
            value = F.silu(layer(value))
        return self.layers[-1](value)


def _validate_observation(observation: Tensor) -> None:
    if observation.dtype != torch.float32 or observation.ndim < 2 or observation.shape[-1] != OBSERVATION_WIDTH:
        raise ModelContractError("observation must be finite float32 [...,18]")
    if not bool(torch.isfinite(observation).all()):
        raise ModelContractError("observation must be finite float32 [...,18]")


def _validate_replicate(replicate: int) -> None:
    if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 24:
        raise ModelContractError("replicate must be an integer in [0,24)")


class FoundationActor(nn.Module):
    def __init__(self, *, source: InitializationUniformSource, replicate: int) -> None:
        super().__init__()
        self.network = _ExactMlp(
            (18, 96, 96, 18), source=source, replicate=replicate, arm="FOUNDATION", prefix="actor.layers"
        )

    def forward(self, observation: Tensor) -> Tensor:
        _validate_observation(observation)
        return self.network(observation)


class FoundationActorCritic(nn.Module):
    """One order-erased foundation actor/critic with one shared k parameterization."""

    def __init__(
        self,
        *,
        permit: ModelMaterializationPermit,
        replicate: int,
        initialization_source: InitializationUniformSource,
    ) -> None:
        super().__init__()
        _validate_replicate(replicate)
        if not isinstance(permit, ModelMaterializationPermit):
            raise TypeError("foundation materialization requires an explicit permit")
        if not isinstance(initialization_source, InitializationUniformSource):
            raise TypeError("foundation materialization requires an explicit uniform source")
        permit.require_model_materialization(
            card_revision=CARD_REVISION,
            replicate=replicate,
            arm="FOUNDATION",
            initialization_source=initialization_source,
        )
        self.replicate = replicate
        self.materialization_permit = permit
        self.actor = FoundationActor(source=initialization_source, replicate=replicate)
        self.critic = _ExactMlp(
            (18, 96, 96, 1),
            source=initialization_source,
            replicate=replicate,
            arm="FOUNDATION",
            prefix="critic.layers",
        )
        count = sum(parameter.numel() for parameter in self.parameters())
        if count != FOUNDATION_PARAMETER_COUNT:
            raise RuntimeError("materialized foundation parameter count differs")

    def forward(self, observation: Tensor) -> FoundationOutput:
        _validate_observation(observation)
        return FoundationOutput(self.actor(observation), self.critic(observation).squeeze(-1))


def _tensor_digest(module: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in module.state_dict().items():
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


class FrozenFoundationActor(nn.Module):
    """Byte-identical immutable actor clone used by every order-stage arm."""

    def __init__(self, actor: FoundationActor, *, replicate: int) -> None:
        super().__init__()
        self.replicate = replicate
        self.actor = copy.deepcopy(actor)
        self.actor.requires_grad_(False)
        self.actor.eval()
        self.digest = _tensor_digest(self.actor)

    def forward(self, observation: Tensor) -> Tensor:
        return self.actor(observation)

    def validate_immutable(self) -> None:
        if _tensor_digest(self.actor) != self.digest:
            raise RuntimeError("frozen foundation actor changed")
        if any(parameter.requires_grad for parameter in self.actor.parameters()):
            raise RuntimeError("frozen foundation actor became trainable")


def clone_frozen_foundation_actor(
    foundation: FoundationActorCritic,
    *,
    permit: ModelMaterializationPermit,
    arm: str | LearnedOrderArm,
) -> FrozenFoundationActor:
    learned = arm if isinstance(arm, LearnedOrderArm) else LearnedOrderArm(str(arm))
    source_digest = _tensor_digest(foundation.actor)
    permit.require_foundation_clone(
        card_revision=CARD_REVISION,
        replicate=foundation.replicate,
        arm=learned.value,
        foundation_digest=source_digest,
    )
    clone = FrozenFoundationActor(foundation.actor, replicate=foundation.replicate)
    if clone.digest != source_digest:
        raise RuntimeError("foundation actor clone is not byte-identical")
    return clone


def _q_tensor(value: Tensor, batch_shape: torch.Size) -> Tensor:
    if value.dtype != torch.float32:
        raise ModelContractError("physical q must be float32")
    if value.shape == batch_shape + (1,):
        value = value.squeeze(-1)
    if value.shape != batch_shape or not bool(torch.all((value == 0.0) | (value == 1.0))):
        raise ModelContractError("physical q must be binary and match the observation batch")
    return value


def _k_tensor(value: Tensor, batch_shape: torch.Size) -> Tensor:
    if value.shape == batch_shape + (1,):
        value = value.squeeze(-1)
    if value.shape != batch_shape or value.dtype not in (torch.int32, torch.int64):
        raise ModelContractError("announced k must be an integer tensor matching the observation batch")
    if not all(int(item) in ALLOWED_CURRENT_K for item in value.detach().cpu().reshape(-1).tolist()):
        raise ModelContractError("announced k is outside the registered fixed/switch periods")
    return value


class OrderActorCritic(nn.Module):
    """TREAT/FREE/SET adapter over one immutable foundation actor."""

    def __init__(
        self,
        arm: str | LearnedOrderArm,
        *,
        frozen_foundation: FrozenFoundationActor,
        permit: ModelMaterializationPermit,
        initialization_source: InitializationUniformSource,
    ) -> None:
        super().__init__()
        self.arm = arm if isinstance(arm, LearnedOrderArm) else LearnedOrderArm(str(arm))
        if not isinstance(frozen_foundation, FrozenFoundationActor):
            raise TypeError("order stage requires an exact frozen foundation actor clone")
        if not isinstance(permit, ModelMaterializationPermit):
            raise TypeError("order-stage materialization requires an explicit permit")
        if not isinstance(initialization_source, InitializationUniformSource):
            raise TypeError("order-stage materialization requires an explicit uniform source")
        frozen_foundation.validate_immutable()
        self.replicate = frozen_foundation.replicate
        permit.require_model_materialization(
            card_revision=CARD_REVISION,
            replicate=self.replicate,
            arm=self.arm.value,
            initialization_source=initialization_source,
        )
        self.materialization_permit = permit
        self.foundation = frozen_foundation
        self.foundation_digest = frozen_foundation.digest
        self.scale = _ExactMlp(
            (18, 32, 1),
            source=initialization_source,
            replicate=self.replicate,
            arm=self.arm.value,
            prefix="scale.layers",
            final_initialization="zero_weight_bias_0.001",
        )
        self.critic = _ExactMlp(
            (19, 64, 64, 1),
            source=initialization_source,
            replicate=self.replicate,
            arm=self.arm.value,
            prefix="critic.layers",
        )
        self.residual: _ExactMlp | None = None
        if self.arm in (LearnedOrderArm.FREE, LearnedOrderArm.SET):
            self.residual = _ExactMlp(
                (19, 64, 64, 18),
                source=initialization_source,
                replicate=self.replicate,
                arm=self.arm.value,
                prefix="residual.layers",
                final_initialization="zeros",
            )
        self._validate_materialized()

    def _validate_materialized(self) -> None:
        self.foundation.validate_immutable()
        trainable = sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)
        if trainable != model_schema(self.arm).trainable_parameter_count:
            raise RuntimeError("materialized order-stage trainable parameter count differs")
        if any(parameter.requires_grad for parameter in self.foundation.parameters()):
            raise RuntimeError("order-stage foundation is not frozen")
        if self.residual is not None:
            output = self.residual.layers[-1]
            if bool(torch.any(output.weight != 0.0)) or bool(torch.any(output.bias != 0.0)):
                raise RuntimeError("FREE/SET residual output must initialize exactly to zero")
        scale_output = self.scale.layers[-1]
        if bool(torch.any(scale_output.weight != 0.0)) or not bool(torch.all(scale_output.bias == 0.001)):
            raise RuntimeError("treatment scale output initialization differs")

    def forward_with_compositor(
        self,
        observation: Tensor,
        physical_q: Tensor,
        announced_k: Tensor,
        *,
        compositor_q: Tensor | None = None,
    ) -> OrderOutput:
        _validate_observation(observation)
        batch_shape = observation.shape[:-1]
        physical = _q_tensor(physical_q, batch_shape)
        announced = _k_tensor(announced_k, batch_shape)
        supplied = physical if compositor_q is None else _q_tensor(compositor_q, batch_shape)
        effective = torch.full_like(physical, 0.5) if self.arm is LearnedOrderArm.SET else supplied
        flat_observation = observation.reshape(-1, OBSERVATION_WIDTH)
        flat_k = announced.reshape(-1)
        if self.arm is LearnedOrderArm.SET:
            score = set_scores(flat_observation, flat_k).reshape(batch_shape + (ACTION_COUNT,))
        else:
            score = graph_slack_scores(flat_observation, effective.reshape(-1), flat_k).reshape(
                batch_shape + (ACTION_COUNT,)
            )
        foundation_logits = self.foundation(observation)
        alpha = torch.relu(self.scale(observation)).squeeze(-1)
        logits = foundation_logits + alpha.unsqueeze(-1) * score
        joined = torch.cat((observation, effective.unsqueeze(-1)), dim=-1)
        if self.residual is not None:
            logits = logits + self.residual(joined)
        value = self.critic(joined).squeeze(-1)
        self.foundation.validate_immutable()
        return OrderOutput(logits, value, alpha, physical, effective, score)

    def forward(self, observation: Tensor, physical_q: Tensor, announced_k: Tensor) -> OrderOutput:
        return self.forward_with_compositor(observation, physical_q, announced_k)


class TiedReversedController(nn.Module):
    """Parameter-tied REVERSED view; it owns no optimizer or copied weights."""

    def __init__(self, treatment: OrderActorCritic) -> None:
        super().__init__()
        if treatment.arm is not LearnedOrderArm.TREAT:
            raise ModelContractError("REVERSED must tie the final TREAT controller")
        self.treatment = treatment

    def forward(self, observation: Tensor, physical_q: Tensor, announced_k: Tensor) -> OrderOutput:
        physical = _q_tensor(physical_q, observation.shape[:-1])
        return self.treatment.forward_with_compositor(
            observation, physical, announced_k, compositor_q=1.0 - physical
        )


def categorical_log_prob(logits: Tensor, actions: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.shape[-1] != ACTION_COUNT or not bool(torch.isfinite(logits).all()):
        raise ModelContractError("logits must be finite float32 [...,18]")
    if actions.dtype != torch.int64 or actions.shape != logits.shape[:-1]:
        raise ModelContractError("actions must be int64 and match the logits batch")
    if bool(torch.any((actions < 0) | (actions >= ACTION_COUNT))):
        raise ModelContractError("action index is outside the lexicographic 18-action table")
    return torch.log_softmax(logits, dim=-1).gather(-1, actions.unsqueeze(-1)).squeeze(-1)


def categorical_entropy(logits: Tensor) -> Tensor:
    log_probability = torch.log_softmax(logits, dim=-1)
    probability = torch.exp(log_probability)
    return -(probability * log_probability).sum(dim=-1)


def lexicographic_argmax(logits: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.shape[-1] != ACTION_COUNT or not bool(torch.isfinite(logits).all()):
        raise ModelContractError("logits must be finite float32 [...,18]")
    return torch.argmax(logits, dim=-1)


def frozen_foundation_digest(model: OrderActorCritic) -> str:
    model.foundation.validate_immutable()
    return model.foundation.digest


def shared_parameterization_contract() -> dict[str, object]:
    return {
        "train_k": K_TRAIN,
        "target_schedules": K_TARGET,
        "one_parameter_vector_across_k": True,
        "per_k_heads": 0,
        "per_k_initializers": 0,
        "per_k_optimizers": 0,
        "per_k_checkpoints": 0,
        "switch_resets": False,
        "recurrent_state": False,
    }


validate_static_model_contract()


__all__ = [
    "CARD_REVISION",
    "FoundationActorCritic",
    "FoundationOutput",
    "FrozenFoundationActor",
    "InitializationUniformSource",
    "LearnedOrderArm",
    "ModelContractError",
    "ModelMaterializationPermit",
    "ModelSchema",
    "OrderActorCritic",
    "OrderOutput",
    "ParameterSpec",
    "TiedReversedController",
    "categorical_entropy",
    "categorical_log_prob",
    "clone_frozen_foundation_actor",
    "frozen_foundation_digest",
    "lexicographic_argmax",
    "model_schema",
    "parameter_schema",
    "row_major_xavier_from_uniforms",
    "shared_parameterization_contract",
    "validate_static_model_contract",
]
