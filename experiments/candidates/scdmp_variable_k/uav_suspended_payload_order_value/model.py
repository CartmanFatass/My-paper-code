"""Identity-free model contract for the frozen SCDMP UAV controller.

Importing this module and inspecting its schemas never creates trainable
parameters or consumes random state.  Materialization is deliberately behind
an injected activity/identity permit owned by a future authorized runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Final, Protocol, Sequence, runtime_checkable

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .config import ACTION_COUNT, CARD_REVISION, decode_action


OBSERVATION_DIM: Final[int] = 14
CHRONOLOGY_DIM: Final[int] = 1
ACTOR_WIDTHS: Final[tuple[int, int]] = (64, 64)
RISK_WIDTH: Final[int] = 32
CRITIC_WIDTHS: Final[tuple[int, int]] = (64, 64)
RESIDUAL_WIDTHS: Final[tuple[int, int]] = (64, 64)

TREAT_PARAMETER_COUNT: Final[int] = 12_637
FREE_PARAMETER_COUNT: Final[int] = 19_576
SET_PARAMETER_COUNT: Final[int] = 19_576
ACTION_UNIFORM_BITS: Final[int] = 24
ACTION_UNIFORM_DENOMINATOR: Final[int] = 1 << ACTION_UNIFORM_BITS
ACTION_UNIFORM_MAX: Final[float] = (
    ACTION_UNIFORM_DENOMINATOR - 1
) / ACTION_UNIFORM_DENOMINATOR

LEXICOGRAPHIC_ACTIONS: Final[tuple[tuple[int, int, int], ...]] = tuple(
    decode_action(index) for index in range(ACTION_COUNT)
)


class LearnedArm(str, Enum):
    TREAT = "TREAT"
    FREE = "FREE"
    SET = "SET"


@runtime_checkable
class InitializationUniformSource(Protocol):
    """Lease-bound adapter for the future initialization HMAC domain."""

    def initialization_uniforms(
        self,
        *,
        replicate: int,
        arm: str,
        tensor_group: str,
        shared_across_arms: bool,
        count: int,
    ) -> tuple[float, ...]:
        """Return address-stable exact float32 uniforms in row-major order."""


@runtime_checkable
class ModelActivityIdentityPermit(Protocol):
    """Future-runner authority boundary; this package never issues permits."""

    def require_model_initialization(
        self,
        *,
        card_revision: str,
        replicate: int,
        arm: str,
        initialization_source: InitializationUniformSource,
    ) -> None:
        """Raise unless this exact model initialization identity is authorized."""

    def require_training(self, *, card_revision: str, arm: str) -> None:
        """Raise unless training of this exact model identity is authorized."""


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    shape: tuple[int, ...]
    initialization: str
    identity_stream: str

    @property
    def count(self) -> int:
        return math.prod(self.shape)


@dataclass(frozen=True)
class InitializationRequest:
    arm: str
    tensor_group: str
    shared_across_arms: bool
    count: int


@dataclass(frozen=True)
class ModelSchema:
    arm: LearnedArm
    observation_dim: int
    action_count: int
    base_widths: tuple[int, int]
    risk_width: int
    critic_widths: tuple[int, int]
    residual_widths: tuple[int, int] | None
    parameter_count: int
    chronology_law: str
    actor_law: str
    critic_input_dim: int
    action_order: tuple[tuple[int, int, int], ...]


def _arm(value: LearnedArm | str) -> LearnedArm:
    try:
        return value if isinstance(value, LearnedArm) else LearnedArm(value)
    except ValueError as exc:
        raise ValueError("learned arm must be TREAT, FREE, or SET") from exc


def _affine_specs(
    prefix: str,
    dims: Sequence[int],
    *,
    identity_stream: str,
    zero_output: bool = False,
) -> tuple[ParameterSpec, ...]:
    specs: list[ParameterSpec] = []
    final_layer = len(dims) - 2
    for layer, (fan_in, fan_out) in enumerate(zip(dims, dims[1:])):
        weight_init = "zeros" if zero_output and layer == final_layer else "xavier_uniform_row_major"
        specs.extend(
            (
                ParameterSpec(
                    f"{prefix}.{layer}.weight",
                    (fan_out, fan_in),
                    weight_init,
                    identity_stream,
                ),
                ParameterSpec(
                    f"{prefix}.{layer}.bias", (fan_out,), "zeros", identity_stream
                ),
            )
        )
    return tuple(specs)


def parameter_schema(arm: LearnedArm | str) -> tuple[ParameterSpec, ...]:
    """Return the complete named tensor schema without materializing a model."""

    learned_arm = _arm(arm)
    specs = (
        _affine_specs(
            "base.layers", (14, 64, 64, 27), identity_stream="paired_shared"
        )
        + _affine_specs("risk.layers", (14, 32, 1), identity_stream="paired_shared")
        + _affine_specs(
            "critic.layers", (15, 64, 64, 1), identity_stream="paired_shared"
        )
    )
    if learned_arm in (LearnedArm.FREE, LearnedArm.SET):
        specs += _affine_specs(
            "residual.layers",
            (15, 64, 64, 27),
            identity_stream="arm_disjoint_residual",
            zero_output=True,
        )
    return specs


def initialization_requests(arm: LearnedArm | str) -> tuple[InitializationRequest, ...]:
    """Return every RNG-consuming tensor address; zero tensors are absent."""

    learned_arm = _arm(arm)
    requests: list[InitializationRequest] = []
    for spec in parameter_schema(learned_arm):
        if spec.initialization != "xavier_uniform_row_major":
            continue
        shared = spec.identity_stream == "paired_shared"
        requests.append(
            InitializationRequest(
                arm="SHARED" if shared else learned_arm.value,
                tensor_group=spec.name,
                shared_across_arms=shared,
                count=spec.count,
            )
        )
    return tuple(requests)


def row_major_xavier_from_uniforms(
    uniforms: Sequence[float],
    *,
    fan_in: int,
    fan_out: int,
) -> Tensor:
    """Map exact U[0,1) values to one float32 row-major Xavier matrix."""

    if (
        isinstance(fan_in, bool)
        or isinstance(fan_out, bool)
        or not isinstance(fan_in, int)
        or not isinstance(fan_out, int)
        or fan_in <= 0
        or fan_out <= 0
    ):
        raise ValueError("Xavier fan sizes must be positive integers")
    expected = fan_in * fan_out
    values = tuple(uniforms)
    if len(values) != expected:
        raise ValueError("initialization provider returned the wrong uniform count")
    if any(isinstance(value, bool) or not isinstance(value, float) for value in values):
        raise TypeError("initialization uniforms must be Python floats")
    tensor = torch.tensor(values, dtype=torch.float32)
    if not bool(torch.isfinite(tensor).all()) or not bool(torch.all((tensor >= 0.0) & (tensor < 1.0))):
        raise ValueError("initialization uniforms must be finite and lie in [0,1)")
    # HMAC adapters must return exactly float32-representable values, not values
    # that silently change when the frozen arithmetic receives them.
    if any(float(encoded) != value for encoded, value in zip(tensor, values)):
        raise ValueError("initialization uniforms must be exactly float32-representable")
    bound = torch.tensor(math.sqrt(6.0 / float(fan_in + fan_out)), dtype=torch.float32)
    flat = (tensor * 2.0 - 1.0) * bound
    return flat.reshape(fan_out, fan_in).contiguous()


def model_schema(arm: LearnedArm | str) -> ModelSchema:
    learned_arm = _arm(arm)
    count = sum(spec.count for spec in parameter_schema(learned_arm))
    expected = {
        LearnedArm.TREAT: TREAT_PARAMETER_COUNT,
        LearnedArm.FREE: FREE_PARAMETER_COUNT,
        LearnedArm.SET: SET_PARAMETER_COUNT,
    }[learned_arm]
    if count != expected:
        raise RuntimeError(f"static parameter schema drifted: {count} != {expected}")
    return ModelSchema(
        arm=learned_arm,
        observation_dim=OBSERVATION_DIM,
        action_count=ACTION_COUNT,
        base_widths=ACTOR_WIDTHS,
        risk_width=RISK_WIDTH,
        critic_widths=CRITIC_WIDTHS,
        residual_widths=None if learned_arm is LearnedArm.TREAT else RESIDUAL_WIDTHS,
        parameter_count=count,
        chronology_law="q_true_in_{0,1}" if learned_arm is not LearnedArm.SET else "q_SET=0.5",
        actor_law=(
            "B(o)-q*softplus(g(o))*rho"
            if learned_arm is LearnedArm.TREAT
            else "B(o)-q*softplus(g(o))*rho+R(o,q)"
        ),
        critic_input_dim=OBSERVATION_DIM + CHRONOLOGY_DIM,
        action_order=LEXICOGRAPHIC_ACTIONS,
    )


def validate_static_model_contract() -> dict[str, int]:
    counts = {arm.value: model_schema(arm).parameter_count for arm in LearnedArm}
    if LEXICOGRAPHIC_ACTIONS != tuple(
        (u1, u2, u3) for u1 in range(3) for u2 in range(3) for u3 in range(3)
    ):
        raise RuntimeError("joint-action order is not lexicographic")
    if counts != {"TREAT": 12_637, "FREE": 19_576, "SET": 19_576}:
        raise RuntimeError("frozen model parameter counts drifted")
    return counts


def chronology_q_scalar(arm: LearnedArm | str, true_q: float) -> float:
    """Apply the frozen per-arm chronology law without constructing a model."""

    learned_arm = _arm(arm)
    if true_q not in (0.0, 1.0):
        raise ValueError("physical chronology q must be exactly 0 or 1")
    return 0.5 if learned_arm is LearnedArm.SET else true_q


def _chronology_tensor(arm: LearnedArm, true_q: Tensor, batch_shape: torch.Size) -> Tensor:
    if true_q.dtype != torch.float32:
        raise TypeError("chronology tensor must use float32")
    q = true_q
    if q.shape == batch_shape:
        q = q.unsqueeze(-1)
    if q.shape != batch_shape + (1,):
        raise ValueError("chronology tensor must have shape observation.shape[:-1] or that shape plus one")
    if not bool(torch.all((q == 0.0) | (q == 1.0))):
        raise ValueError("physical chronology q must be exactly 0 or 1")
    if arm is LearnedArm.SET:
        return torch.full_like(q, 0.5)
    return q


def risk_vector(*, dtype: torch.dtype = torch.float32, device: torch.device | str | None = None) -> Tensor:
    values = []
    for command in LEXICOGRAPHIC_ACTIONS:
        mean = sum(command) / 3.0
        imbalance = max(abs(value - mean) for value in command)
        values.append(0.75 * (mean / 2.0) + 0.25 * (imbalance / (4.0 / 3.0)))
    return torch.tensor(values, dtype=dtype, device=device)


class _ExactAffine(nn.Module):
    """Affine map initialized without invoking PyTorch's implicit RNG path."""

    def __init__(
        self,
        fan_in: int,
        fan_out: int,
        *,
        initialization_source: InitializationUniformSource,
        replicate: int,
        address_arm: str,
        tensor_group: str,
        shared_across_arms: bool,
        zero_weight: bool = False,
    ) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.empty((fan_out, fan_in), dtype=torch.float32))
        self.bias = nn.Parameter(torch.empty((fan_out,), dtype=torch.float32))
        with torch.no_grad():
            if zero_weight:
                self.weight.zero_()
            else:
                uniforms = initialization_source.initialization_uniforms(
                    replicate=replicate,
                    arm=address_arm,
                    tensor_group=tensor_group,
                    shared_across_arms=shared_across_arms,
                    count=fan_in * fan_out,
                )
                self.weight.copy_(
                    row_major_xavier_from_uniforms(
                        uniforms, fan_in=fan_in, fan_out=fan_out
                    )
                )
            self.bias.zero_()
        if not self.weight.is_contiguous():
            raise RuntimeError("affine weight must be contiguous row-major")

    def forward(self, value: Tensor) -> Tensor:
        return F.linear(value, self.weight, self.bias)


class _SiLUMlp(nn.Module):
    def __init__(
        self,
        dims: Sequence[int],
        *,
        initialization_source: InitializationUniformSource,
        replicate: int,
        address_arm: str,
        tensor_prefix: str,
        shared_across_arms: bool,
        zero_output: bool = False,
    ) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            _ExactAffine(
                fan_in,
                fan_out,
                initialization_source=initialization_source,
                replicate=replicate,
                address_arm=address_arm,
                tensor_group=f"{tensor_prefix}.{layer}.weight",
                shared_across_arms=shared_across_arms,
                zero_weight=zero_output and layer == len(dims) - 2,
            )
            for layer, (fan_in, fan_out) in enumerate(zip(dims, dims[1:]))
        )

    def forward(self, value: Tensor) -> Tensor:
        for layer in self.layers[:-1]:
            value = F.silu(layer(value))
        return self.layers[-1](value)


@dataclass(frozen=True)
class ActorCriticOutput:
    logits: Tensor
    value: Tensor
    alpha: Tensor
    effective_q: Tensor


class SCDMPUAVActorCritic(nn.Module):
    """Frozen TREAT/FREE/SET actor-critic; construction requires authority."""

    def __init__(
        self,
        arm: LearnedArm | str,
        *,
        permit: ModelActivityIdentityPermit,
        replicate: int,
        initialization_source: InitializationUniformSource,
    ) -> None:
        super().__init__()
        self.arm = _arm(arm)
        if not isinstance(permit, ModelActivityIdentityPermit):
            raise TypeError("model initialization requires an explicit activity/identity permit")
        if not isinstance(initialization_source, InitializationUniformSource):
            raise TypeError("model initialization requires an explicit uniform source")
        if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 18:
            raise ValueError("replicate must be an integer in [0,18)")
        permit.require_model_initialization(
            card_revision=CARD_REVISION,
            replicate=replicate,
            arm=self.arm.value,
            initialization_source=initialization_source,
        )
        self._activity_permit = permit

        # Shared modules are always materialized first and in the same order.
        shared = {
            "initialization_source": initialization_source,
            "replicate": replicate,
            "address_arm": "SHARED",
            "shared_across_arms": True,
        }
        self.base = _SiLUMlp(
            (14, 64, 64, 27), tensor_prefix="base.layers", **shared
        )
        self.risk = _SiLUMlp(
            (14, 32, 1), tensor_prefix="risk.layers", **shared
        )
        self.critic = _SiLUMlp(
            (15, 64, 64, 1), tensor_prefix="critic.layers", **shared
        )
        self.residual: _SiLUMlp | None = None
        if self.arm in (LearnedArm.FREE, LearnedArm.SET):
            self.residual = _SiLUMlp(
                (15, 64, 64, 27),
                initialization_source=initialization_source,
                replicate=replicate,
                address_arm=self.arm.value,
                tensor_prefix="residual.layers",
                shared_across_arms=False,
                zero_output=True,
            )
        self.register_buffer("rho", risk_vector(), persistent=True)
        self._validate_materialized_schema()

    @property
    def activity_permit(self) -> ModelActivityIdentityPermit:
        return self._activity_permit

    def _validate_materialized_schema(self) -> None:
        if any(parameter.dtype != torch.float32 for parameter in self.parameters()):
            raise RuntimeError("all model parameters must be float32")
        count = sum(parameter.numel() for parameter in self.parameters())
        if count != model_schema(self.arm).parameter_count:
            raise RuntimeError("materialized model parameter count drifted")
        if self.residual is not None:
            output = self.residual.layers[-1]
            if bool(torch.any(output.weight != 0.0)) or bool(torch.any(output.bias != 0.0)):
                raise RuntimeError("FREE/SET residual output must start exactly at zero")

    def forward(self, observation: Tensor, true_q: Tensor) -> ActorCriticOutput:
        if observation.dtype != torch.float32:
            raise TypeError("observation tensor must use float32")
        if observation.ndim < 1 or observation.shape[-1] != OBSERVATION_DIM:
            raise ValueError("observation must end in the frozen 14-vector")
        if not bool(torch.isfinite(observation).all()):
            raise ValueError("observation must be finite")
        q = _chronology_tensor(self.arm, true_q, observation.shape[:-1])
        base = self.base(observation)
        alpha = F.softplus(self.risk(observation))
        logits = base - q * alpha * self.rho
        joined = torch.cat((observation, q), dim=-1)
        if self.residual is not None:
            logits = logits + self.residual(joined)
        value = self.critic(joined).squeeze(-1)
        return ActorCriticOutput(
            logits=logits,
            value=value,
            alpha=alpha.squeeze(-1),
            effective_q=q.squeeze(-1),
        )


def build_model(
    arm: LearnedArm | str,
    *,
    permit: ModelActivityIdentityPermit,
    replicate: int,
    initialization_source: InitializationUniformSource,
) -> SCDMPUAVActorCritic:
    return SCDMPUAVActorCritic(
        arm,
        permit=permit,
        replicate=replicate,
        initialization_source=initialization_source,
    )


def categorical_log_prob(logits: Tensor, actions: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.shape[-1] != ACTION_COUNT:
        raise ValueError("logits must be float32 with final dimension 27")
    if actions.dtype != torch.int64 or actions.shape != logits.shape[:-1]:
        raise ValueError("actions must be int64 and match the logits batch shape")
    if bool(torch.any((actions < 0) | (actions >= ACTION_COUNT))):
        raise ValueError("actions must index the lexicographic 27-action table")
    return torch.log_softmax(logits, dim=-1).gather(-1, actions.unsqueeze(-1)).squeeze(-1)


def categorical_entropy(logits: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.shape[-1] != ACTION_COUNT:
        raise ValueError("logits must be float32 with final dimension 27")
    log_prob = torch.log_softmax(logits, dim=-1)
    probability = torch.exp(log_prob)
    return -(probability * log_prob).sum(dim=-1)


def inverse_cdf_action(logits: Tensor, uniform: Tensor) -> Tensor:
    """Sample from the registered uint24/2^24 grid in lexicographic order."""

    if logits.dtype != torch.float32 or logits.shape[-1] != ACTION_COUNT:
        raise ValueError("logits must be float32 with final dimension 27")
    if uniform.dtype != torch.float32 or uniform.shape != logits.shape[:-1]:
        raise ValueError("uniform must be float32 and match the logits batch shape")
    if not bool(torch.all((uniform >= 0.0) & (uniform <= ACTION_UNIFORM_MAX))):
        raise ValueError("action variates must lie on the registered [0,1) uint24 grid")
    scaled = uniform * float(ACTION_UNIFORM_DENOMINATOR)
    if not bool(torch.all(scaled == torch.floor(scaled))):
        raise ValueError("action variates must equal an exact uint24 / 2^24 value")
    cdf = torch.softmax(logits, dim=-1).cumsum(dim=-1)
    # searchsorted-like comparison preserves the registered first-index rule.
    return torch.sum(uniform.unsqueeze(-1) >= cdf, dim=-1).clamp_max(ACTION_COUNT - 1)


def lexicographic_argmax(logits: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.shape[-1] != ACTION_COUNT:
        raise ValueError("logits must be float32 with final dimension 27")
    return torch.argmax(logits, dim=-1)


__all__ = [
    "ACTION_UNIFORM_BITS",
    "ACTION_UNIFORM_DENOMINATOR",
    "ACTION_UNIFORM_MAX",
    "ACTOR_WIDTHS",
    "ActorCriticOutput",
    "FREE_PARAMETER_COUNT",
    "LEXICOGRAPHIC_ACTIONS",
    "LearnedArm",
    "InitializationRequest",
    "InitializationUniformSource",
    "ModelActivityIdentityPermit",
    "ModelSchema",
    "OBSERVATION_DIM",
    "ParameterSpec",
    "SCDMPUAVActorCritic",
    "SET_PARAMETER_COUNT",
    "TREAT_PARAMETER_COUNT",
    "build_model",
    "categorical_entropy",
    "categorical_log_prob",
    "chronology_q_scalar",
    "inverse_cdf_action",
    "initialization_requests",
    "lexicographic_argmax",
    "model_schema",
    "parameter_schema",
    "risk_vector",
    "row_major_xavier_from_uniforms",
    "validate_static_model_contract",
]
