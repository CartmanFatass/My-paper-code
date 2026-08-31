"""Fresh FRRIE Torch actor/critic and semantic-column intervention.

Torch is deliberately optional at package-import time.  The structural
constants and rotation helpers remain inspectable without it; construction of
the production learned policy fails closed when Torch is unavailable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final, Mapping

import numpy as np

from .arms import LAYER_SHAPES, PROJECTION_BOXES, LearnedArm, architecture_parameter_count
from .contracts.core import ContractError, MODEL_PARAMETER_COUNT

try:  # Optional production dependency, never an import-time package gate.
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - exercised in the non-Torch test job
    torch = None
    nn = None


TORCH_AVAILABLE: Final[bool] = torch is not None
ROLE_NAMES: Final[tuple[str, ...]] = (
    "WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY",
)
ACTION_NAMES: Final[tuple[str, ...]] = (
    "SCAN", "UPLINK", "LISTEN_WEST", "LISTEN_EAST", "FORWARD_BASE", "HOLD",
)
LEGAL_ACTION_INDICES: Final[tuple[tuple[int, ...], ...]] = (
    (0, 1, 5), (0, 1, 5), (2, 3, 4, 5),
)
P0: Final[np.ndarray] = np.asarray(
    ((0.92, 0.48, 0.88), (0.48, 0.92, 0.82), (0.86, 0.78, 0.90)),
    dtype=np.float32,
)
LATENCY: Final[np.ndarray] = np.asarray(
    ((1.0, 2.0, 1.0), (2.0, 1.0, 1.0), (1.0, 1.0, 1.0)),
    dtype=np.float32,
)
SEMANTIC_COLUMN_ROTATION: Final[tuple[int, int, int]] = (2, 0, 1)


class TorchUnavailableError(RuntimeError):
    """Raised when the authorized learned actor cannot be constructed."""


def require_torch() -> None:
    if not TORCH_AVAILABLE:
        raise TorchUnavailableError(
            "FRRIE production learned execution requires Torch; no Python policy fallback exists"
        )


def semantic_column_permutation(rotated: bool = True) -> tuple[int, int, int]:
    """Return the physical sender-column source order for the policy summary.

    Under the cut, old WEST moves to EAST, old EAST moves to RELAY, and old
    RELAY moves to WEST.  Residual beta indices, messages, counts, observations,
    recurrence, simulator physics, and randomness are not permuted.
    """

    return SEMANTIC_COLUMN_ROTATION if rotated else (0, 1, 2)


def legal_action_mask_array() -> np.ndarray:
    mask = np.zeros((3, 6), dtype=np.bool_)
    for role, indices in enumerate(LEGAL_ACTION_INDICES):
        mask[role, list(indices)] = True
    return mask


def expected_parameter_names() -> tuple[str, ...]:
    return tuple(name for name, _ in LAYER_SHAPES)


def _validate_arm(arm: LearnedArm) -> None:
    if not isinstance(arm, LearnedArm):
        raise ContractError("FRRIE actor construction requires a fresh LearnedArm")
    if arm.parameter_count != MODEL_PARAMETER_COUNT:
        raise ContractError("FRRIE actor parameter count drift")


@dataclass(frozen=True)
class ActorStep:
    """One factual or non-propagating shadow actor step."""

    logits: Any
    probabilities: Any
    hidden: Any
    messages: Any
    summary: Any
    denominator: Any


if TORCH_AVAILABLE:

    class _MessageEncoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight_ih = nn.Parameter(torch.empty((64, 22), dtype=torch.float32))
            self.bias_ih = nn.Parameter(torch.empty((64,), dtype=torch.float32))
            self.weight_ho = nn.Parameter(torch.empty((32, 64), dtype=torch.float32))
            self.bias_ho = nn.Parameter(torch.empty((32,), dtype=torch.float32))

        def forward(self, observations: torch.Tensor) -> torch.Tensor:
            hidden = torch.tanh(
                torch.nn.functional.linear(observations, self.weight_ih, self.bias_ih)
            )
            return torch.tanh(
                torch.nn.functional.linear(hidden, self.weight_ho, self.bias_ho)
            )


    class _ExactGRU(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight_input_zrn = nn.Parameter(torch.empty((192, 55), dtype=torch.float32))
            self.weight_hidden_zrn = nn.Parameter(torch.empty((192, 64), dtype=torch.float32))
            self.bias_zrn = nn.Parameter(torch.empty((192,), dtype=torch.float32))

        def forward(self, actor_input: torch.Tensor, incoming: torch.Tensor) -> torch.Tensor:
            input_zrn = torch.nn.functional.linear(
                actor_input, self.weight_input_zrn, self.bias_zrn
            )
            wz, wr, wn = input_zrn.chunk(3, dim=-1)
            uz, ur, un = self.weight_hidden_zrn.chunk(3, dim=0)
            z = torch.sigmoid(wz + torch.nn.functional.linear(incoming, uz))
            r = torch.sigmoid(wr + torch.nn.functional.linear(incoming, ur))
            candidate = torch.tanh(wn + torch.nn.functional.linear(r * incoming, un))
            return (1.0 - z) * candidate + z * incoming


    class _Affine(nn.Module):
        def __init__(self, output_size: int, input_size: int) -> None:
            super().__init__()
            self.weight = nn.Parameter(torch.empty((output_size, input_size), dtype=torch.float32))
            self.bias = nn.Parameter(torch.empty((output_size,), dtype=torch.float32))

        def forward(self, value: torch.Tensor) -> torch.Tensor:
            return torch.nn.functional.linear(value, self.weight, self.bias)


    class _Critic(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.input = _Affine(64, 66)
            self.hidden = _Affine(64, 64)
            self.output = _Affine(1, 64)

        def forward(self, team_state: torch.Tensor) -> torch.Tensor:
            value = torch.tanh(self.input(team_state))
            value = torch.tanh(self.hidden(value))
            return self.output(value).squeeze(-1)


    class FRRIEActorCritic(nn.Module):
        """Exact 35,513-parameter CPU/FP32 FRRIE shared actor and critic."""

        def __init__(self, arm: LearnedArm) -> None:
            super().__init__()
            _validate_arm(arm)
            self.arm_id = arm.arm_id
            self.message_encoder = _MessageEncoder()
            self.gru = _ExactGRU()
            self.action_head = _Affine(6, 64)
            self.beta = nn.Parameter(torch.empty((3, 3, 2), dtype=torch.float32))
            self.critic = _Critic()
            self.register_buffer("_p0", torch.from_numpy(P0.copy()), persistent=False)
            self.register_buffer("_latency", torch.from_numpy(LATENCY.copy()), persistent=False)
            self.register_buffer(
                "_legal_masks", torch.from_numpy(legal_action_mask_array()), persistent=False
            )
            self.load_learned_arm(arm)
            self._validate_inventory()

        def named_parameters(
            self, prefix: str = "", recurse: bool = True, remove_duplicate: bool = True
        ):
            """Yield the frozen interleaved actor/beta/critic inventory order."""

            del recurse, remove_duplicate
            ordered = (
                ("message_encoder.weight_ih", self.message_encoder.weight_ih),
                ("message_encoder.bias_ih", self.message_encoder.bias_ih),
                ("message_encoder.weight_ho", self.message_encoder.weight_ho),
                ("message_encoder.bias_ho", self.message_encoder.bias_ho),
                ("gru.weight_input_zrn", self.gru.weight_input_zrn),
                ("gru.weight_hidden_zrn", self.gru.weight_hidden_zrn),
                ("gru.bias_zrn", self.gru.bias_zrn),
                ("action_head.weight", self.action_head.weight),
                ("action_head.bias", self.action_head.bias),
                ("beta", self.beta),
                ("critic.input.weight", self.critic.input.weight),
                ("critic.input.bias", self.critic.input.bias),
                ("critic.hidden.weight", self.critic.hidden.weight),
                ("critic.hidden.bias", self.critic.hidden.bias),
                ("critic.output.weight", self.critic.output.weight),
                ("critic.output.bias", self.critic.output.bias),
            )
            leader = f"{prefix}." if prefix else ""
            for name, parameter in ordered:
                yield leader + name, parameter

        def _validate_inventory(self) -> None:
            actual = tuple((name, tuple(parameter.shape)) for name, parameter in self.named_parameters())
            if actual != LAYER_SHAPES:
                raise ContractError(f"Torch parameter inventory differs from LAYER_SHAPES: {actual!r}")
            if sum(parameter.numel() for parameter in self.parameters()) != MODEL_PARAMETER_COUNT:
                raise ContractError("Torch architecture does not contain exactly 35,513 parameters")
            if any(parameter.dtype != torch.float32 or parameter.device.type != "cpu"
                   for parameter in self.parameters()):
                raise ContractError("FRRIE production parameters must be CPU FP32")

        def ordered_parameters(self) -> tuple[torch.nn.Parameter, ...]:
            mapping = dict(self.named_parameters())
            return tuple(mapping[name] for name, _ in LAYER_SHAPES)

        def load_learned_arm(self, arm: LearnedArm) -> None:
            _validate_arm(arm)
            if hasattr(self, "arm_id") and self.arm_id != arm.arm_id:
                raise ContractError("cannot load a different projection arm into the actor")
            mapping = dict(self.named_parameters())
            with torch.no_grad():
                for name, shape in LAYER_SHAPES:
                    value = arm.parameters[name]
                    if tuple(value.shape) != shape or value.dtype != np.dtype("<f4"):
                        raise ContractError("LearnedArm tensor mapping drift")
                    mapping[name].copy_(torch.from_numpy(value.copy()))

        def parameter_bytes(self) -> bytes:
            self._validate_inventory()
            chunks: list[bytes] = []
            for parameter in self.ordered_parameters():
                value = parameter.detach().numpy()
                if not np.isfinite(value).all():
                    raise ContractError("FRRIE actor contains nonfinite parameters")
                chunks.append(np.asarray(value, dtype="<f4", order="C").tobytes(order="C"))
            data = b"".join(chunks)
            if len(data) != architecture_parameter_count() * 4:
                raise ContractError("FRRIE actor byte length drift")
            return data

        def project_beta(self) -> None:
            low, high = PROJECTION_BOXES[self.arm_id]
            with torch.no_grad():
                self.beta.clamp_(low, high)

        @staticmethod
        def initial_hidden(agent_count: int) -> torch.Tensor:
            if type(agent_count) is not int or agent_count <= 0:
                raise ContractError("positive integer agent count required")
            return torch.zeros((agent_count, 64), dtype=torch.float32)

        def _validate_actor_inputs(
            self, observations: torch.Tensor, roles: torch.Tensor, incoming_hidden: torch.Tensor
        ) -> None:
            if observations.device.type != "cpu" or observations.dtype != torch.float32:
                raise ContractError("actor observations must be CPU FP32")
            if observations.ndim != 2 or observations.shape[1] != 22:
                raise ContractError("actor observations must have shape [agents,22]")
            if roles.device.type != "cpu" or roles.dtype != torch.int64 or roles.ndim != 1:
                raise ContractError("public roles must be CPU int64 [agents]")
            if roles.shape[0] != observations.shape[0] or roles.numel() == 0:
                raise ContractError("role and observation agent axes differ or are empty")
            if bool(((roles < 0) | (roles > 2)).any().item()):
                raise ContractError("public role indices must be in {0,1,2}")
            if incoming_hidden.device.type != "cpu" or incoming_hidden.dtype != torch.float32:
                raise ContractError("incoming recurrent state must be CPU FP32")
            if incoming_hidden.shape != (observations.shape[0], 64):
                raise ContractError("incoming recurrent state must have shape [agents,64]")
            counts = torch.bincount(roles, minlength=3)
            if bool((counts == 0).any().item()):
                raise ContractError("all three public roles must be present")
            if not bool(torch.isfinite(observations).all().item()) or not bool(
                torch.isfinite(incoming_hidden).all().item()
            ):
                raise ContractError("actor inputs must be finite")

        def _role_aggregation(
            self, messages: torch.Tensor, roles: torch.Tensor, *, rotate_columns: bool
        ) -> tuple[torch.Tensor, torch.Tensor]:
            counts_i64 = torch.bincount(roles, minlength=3)
            counts = counts_i64.to(dtype=torch.float32)
            role_sums = torch.zeros((3, 32), dtype=torch.float32)
            role_sums.index_add_(0, roles, messages)

            p0 = self._p0
            latency = self._latency
            if rotate_columns:
                permutation = torch.tensor(
                    semantic_column_permutation(True), dtype=torch.int64
                )
                p0 = p0.index_select(1, permutation)
                latency = latency.index_select(1, permutation)

            logits = torch.log(p0) - torch.log1p(-p0)
            loaded = torch.sigmoid(logits - 0.22 * (counts.unsqueeze(0) - 1.0))
            k0 = loaded / latency
            v = (2.0 * torch.log(counts) - math.log(14.0)) / math.log(3.5)
            residual = self.beta[:, :, 0] + self.beta[:, :, 1] * v.unsqueeze(0)
            omega = k0 * torch.exp(residual)
            denominator = (omega * counts.unsqueeze(0)).sum(dim=1)
            role_summary = torch.matmul(omega, role_sums) / (denominator[:, None] + 1.0e-12)
            return role_summary.index_select(0, roles), denominator.index_select(0, roles)

        def actor_step(
            self,
            observations: torch.Tensor,
            roles: torch.Tensor,
            incoming_hidden: torch.Tensor,
            *,
            rotate_columns: bool = False,
        ) -> ActorStep:
            self._validate_actor_inputs(observations, roles, incoming_hidden)
            messages = self.message_encoder(observations)
            summary, denominator = self._role_aggregation(
                messages, roles, rotate_columns=rotate_columns
            )
            actor_input = torch.cat((observations, summary, denominator[:, None]), dim=1)
            hidden = self.gru(actor_input, incoming_hidden)
            logits = self.action_head(hidden)
            legal = self._legal_masks.index_select(0, roles)
            masked_logits = logits.masked_fill(~legal, -torch.inf)
            legal_softmax = torch.softmax(masked_logits, dim=1)
            legal_count = legal.sum(dim=1, keepdim=True).to(torch.float32)
            probabilities = 0.96 * legal_softmax + legal.to(torch.float32) * (0.04 / legal_count)
            if not bool(torch.isfinite(probabilities).all().item()):
                raise ContractError("actor produced nonfinite probabilities")
            return ActorStep(logits, probabilities, hidden, messages, summary, denominator)

        def shadow_step(
            self, observations: torch.Tensor, roles: torch.Tensor, incoming_hidden: torch.Tensor
        ) -> ActorStep:
            """One rotated-summary step; caller state and episode state are untouched."""

            return self.actor_step(
                observations, roles, incoming_hidden, rotate_columns=True
            )

        def actions_from_uniforms(
            self, probabilities: torch.Tensor, uniforms: torch.Tensor
        ) -> torch.Tensor:
            if probabilities.ndim != 2 or probabilities.shape[1] != 6:
                raise ContractError("action probabilities must have shape [agents,6]")
            if uniforms.shape != (probabilities.shape[0],) or uniforms.dtype != torch.float32:
                raise ContractError("inverse-CDF uniforms must be CPU FP32 [agents]")
            if uniforms.device.type != "cpu" or bool(
                ((uniforms < 0.0) | (uniforms >= 1.0)).any().item()
            ):
                raise ContractError("action uniforms must lie in [0,1)")
            cumulative = probabilities.cumsum(dim=1)
            actions = (uniforms[:, None] >= cumulative).sum(dim=1).clamp(max=5)
            return actions.to(torch.int64)

        def critic_values(self, observations: torch.Tensor, roles: torch.Tensor) -> torch.Tensor:
            if observations.dtype != torch.float32 or observations.device.type != "cpu":
                raise ContractError("critic observations must be CPU FP32")
            if observations.ndim not in (2, 3) or observations.shape[-1] != 22:
                raise ContractError("critic observations must be [agents,22] or [slots,agents,22]")
            if observations.ndim == 2:
                observations = observations.unsqueeze(0)
                squeeze = True
            else:
                squeeze = False
            slots, agents, _ = observations.shape
            if roles.ndim == 1:
                if roles.shape != (agents,):
                    raise ContractError("critic role axis differs from observations")
                roles = roles.unsqueeze(0).expand(slots, -1)
            if roles.shape != (slots, agents) or roles.dtype != torch.int64:
                raise ContractError("critic roles must have shape [agents] or [slots,agents]")
            means: list[torch.Tensor] = []
            for role in range(3):
                mask = roles == role
                counts = mask.sum(dim=1)
                if bool((counts == 0).any().item()):
                    raise ContractError("every critic state must contain all public roles")
                role_sum = (observations * mask[:, :, None]).sum(dim=1)
                means.append(role_sum / counts[:, None].to(torch.float32))
            result = self.critic(torch.cat(means, dim=1))
            return result.squeeze(0) if squeeze else result


else:

    class FRRIEActorCritic:  # type: ignore[no-redef]
        """Fail-closed placeholder when the optional Torch runtime is absent."""

        def __init__(self, arm: LearnedArm) -> None:
            del arm
            require_torch()


def make_actor_critic(arm: LearnedArm) -> FRRIEActorCritic:
    require_torch()
    return FRRIEActorCritic(arm)
