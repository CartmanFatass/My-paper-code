"""Frozen RSCF actor and terminal-critic operators.

This module deliberately has no parameter initializer.  Construction requires
caller-supplied float32 tensors so importing or instantiating the implementation
cannot bind a scientific initialization coordinate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch
from torch import Tensor, nn
from torch.nn import functional as F


ROLE_NAMES = ("WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY")
ACTION_NAMES = (
    "SCAN",
    "UPLINK",
    "LISTEN_WEST",
    "LISTEN_EAST",
    "FORWARD_BASE",
    "HOLD",
)
LEGAL_ACTION_MASK = torch.tensor(
    (
        (True, True, False, False, False, True),
        (True, True, False, False, False, True),
        (False, False, True, True, True, True),
    ),
    dtype=torch.bool,
)
P0 = torch.tensor(
    ((0.92, 0.48, 0.88), (0.48, 0.92, 0.82), (0.86, 0.78, 0.90)),
    dtype=torch.float32,
)
LATENCY = torch.tensor(
    ((1.0, 2.0, 1.0), (2.0, 1.0, 1.0), (1.0, 1.0, 1.0)),
    dtype=torch.float32,
)
REGISTERED_ROLE_MULTIPLICITIES = (2, 3, 5, 7)


ACTOR_PARAMETER_SHAPES: dict[str, tuple[int, ...]] = {
    "encoder_w1": (64, 22),
    "encoder_b1": (64,),
    "encoder_w2": (32, 64),
    "encoder_b2": (32,),
    "w_z": (64, 55),
    "u_z": (64, 64),
    "b_z": (64,),
    "w_r": (64, 55),
    "u_r": (64, 64),
    "b_r": (64,),
    "w_n": (64, 55),
    "u_n": (64, 64),
    "b_n": (64,),
    "actor_w": (6, 64),
    "actor_b": (6,),
    "beta": (3, 3, 2),
}

CRITIC_PARAMETER_SHAPES: dict[str, tuple[int, ...]] = {
    "critic_w1": (64, 66),
    "critic_b1": (64,),
    "critic_w2": (64, 64),
    "critic_b2": (64,),
    "critic_w3": (1, 64),
    "critic_b3": (1,),
}


def _require_parameter_tensors(
    supplied: Mapping[str, Tensor], expected: Mapping[str, tuple[int, ...]]
) -> dict[str, Tensor]:
    missing = sorted(set(expected) - set(supplied))
    extra = sorted(set(supplied) - set(expected))
    if missing or extra:
        raise ValueError(f"parameter schema mismatch: missing={missing}, extra={extra}")
    checked: dict[str, Tensor] = {}
    for name, shape in expected.items():
        value = supplied[name]
        if not isinstance(value, Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        if tuple(value.shape) != shape:
            raise ValueError(f"{name} shape {tuple(value.shape)} != {shape}")
        if value.dtype is not torch.float32:
            raise TypeError(f"{name} must be IEEE-754 float32, got {value.dtype}")
        if not bool(torch.isfinite(value.detach()).all().item()):
            raise ValueError(f"{name} contains a nonfinite value")
        checked[name] = value.detach().clone(memory_format=torch.contiguous_format)
    return checked


@dataclass(frozen=True)
class PolicyStep:
    """One same-slot recurrent actor result with structural audit tensors."""

    probabilities: Tensor
    logits: Tensor
    hidden: Tensor
    messages: Tensor
    role_summary: Tensor
    role_denominator: Tensor
    legal_mask: Tensor


class RSCFActor(nn.Module):
    """Exact shared actor used by both nested projection classes."""

    def __init__(self, parameters: Mapping[str, Tensor]) -> None:
        super().__init__()
        for name, value in _require_parameter_tensors(
            parameters, ACTOR_PARAMETER_SHAPES
        ).items():
            self.register_parameter(name, nn.Parameter(value))

    @staticmethod
    def parameter_count() -> int:
        return sum(
            int(torch.tensor(shape).prod().item())
            for shape in ACTOR_PARAMETER_SHAPES.values()
        )

    def encode_messages(self, observations: Tensor) -> Tensor:
        self._validate_observations(observations)
        hidden = torch.tanh(F.linear(observations, self.encoder_w1, self.encoder_b1))
        return torch.tanh(F.linear(hidden, self.encoder_w2, self.encoder_b2))

    def physical_role_summary(
        self, messages: Tensor, roles: Tensor
    ) -> tuple[Tensor, Tensor]:
        """Compute exact three-role physical/residual aggregation.

        ``messages`` is ``[..., N, 32]`` and ``roles`` is either ``[N]`` or
        ``[..., N]`` with integer public-role labels 0, 1, 2.  Registered
        rosters require equal role multiplicity in ``{2,3,5,7}``.
        """

        if messages.ndim < 2 or messages.shape[-1] != 32:
            raise ValueError("messages must have shape [..., N, 32]")
        if messages.dtype is not torch.float32:
            raise TypeError("messages must be float32")
        flat_messages = messages.reshape(-1, messages.shape[-2], 32)
        flat_roles = self._broadcast_roles(roles, messages.shape[:-1]).reshape(
            -1, messages.shape[-2]
        )
        batch, agents, _ = flat_messages.shape
        role_one_hot = F.one_hot(flat_roles, num_classes=3).to(dtype=torch.float32)
        counts = role_one_hot.sum(dim=1)
        if not bool((counts[:, :1] == counts).all().item()):
            raise ValueError("every roster must contain equal counts of all three roles")
        allowed = torch.zeros_like(counts[:, 0], dtype=torch.bool)
        for multiplicity in REGISTERED_ROLE_MULTIPLICITIES:
            allowed |= counts[:, 0] == float(multiplicity)
        if not bool(allowed.all().item()):
            raise ValueError(
                "role multiplicity must be one of the registered values {2,3,5,7}"
            )

        role_sums = torch.einsum("bnr,bnd->brd", role_one_hot, flat_messages)
        p0 = P0.to(device=messages.device)
        latency = LATENCY.to(device=messages.device)
        logit_p0 = torch.log(p0) - torch.log1p(-p0)
        sender_counts = counts[:, None, :]
        link_probability = torch.sigmoid(
            logit_p0[None, :, :] - 0.22 * (sender_counts - 1.0)
        )
        k0 = link_probability / latency[None, :, :]
        v = (2.0 * torch.log(counts) - torch.log(messages.new_tensor(14.0))) / torch.log(
            messages.new_tensor(3.5)
        )
        residual = self.beta[None, :, :, 0] + self.beta[None, :, :, 1] * v[:, None, :]
        omega = k0 * torch.exp(residual)
        denominator = (omega * sender_counts).sum(dim=-1)
        summary_by_receiver = torch.einsum("brs,bsd->brd", omega, role_sums) / (
            denominator[..., None] + 1.0e-12
        )
        gather_index = flat_roles[..., None].expand(batch, agents, 32)
        per_agent_summary = summary_by_receiver.gather(1, gather_index)
        per_agent_denominator = denominator.gather(1, flat_roles)[..., None]
        lead = messages.shape[:-2]
        return (
            per_agent_summary.reshape(*lead, agents, 32),
            per_agent_denominator.reshape(*lead, agents, 1),
        )

    def forward_step(
        self, observations: Tensor, roles: Tensor, prior_hidden: Tensor
    ) -> PolicyStep:
        """Run message formation, aggregation, frozen z/r/n GRU and policy head."""

        self._validate_observations(observations)
        if tuple(prior_hidden.shape) != (*observations.shape[:-1], 64):
            raise ValueError("prior_hidden must have shape [..., N, 64]")
        if prior_hidden.dtype is not torch.float32:
            raise TypeError("prior_hidden must be float32")
        if prior_hidden.device != observations.device:
            raise ValueError("prior_hidden and observations must share a device")
        messages = self.encode_messages(observations)
        summary, denominator = self.physical_role_summary(messages, roles)
        actor_input = torch.cat((observations, summary, denominator), dim=-1)
        z = torch.sigmoid(
            F.linear(actor_input, self.w_z, self.b_z)
            + F.linear(prior_hidden, self.u_z, None)
        )
        r = torch.sigmoid(
            F.linear(actor_input, self.w_r, self.b_r)
            + F.linear(prior_hidden, self.u_r, None)
        )
        candidate = torch.tanh(
            F.linear(actor_input, self.w_n, self.b_n)
            + F.linear(r * prior_hidden, self.u_n, None)
        )
        hidden = (1.0 - z) * candidate + z * prior_hidden
        logits = F.linear(hidden, self.actor_w, self.actor_b)
        expanded_roles = self._broadcast_roles(roles, observations.shape[:-1])
        legal = LEGAL_ACTION_MASK.to(device=logits.device)[expanded_roles]
        masked_logits = logits.masked_fill(~legal, float("-inf"))
        legal_softmax = torch.softmax(masked_logits, dim=-1)
        legal_count = legal.sum(dim=-1, keepdim=True).to(dtype=torch.float32)
        probabilities = 0.96 * legal_softmax + 0.04 * legal.to(
            dtype=torch.float32
        ) / legal_count
        return PolicyStep(
            probabilities=probabilities,
            logits=logits,
            hidden=hidden,
            messages=messages,
            role_summary=summary,
            role_denominator=denominator,
            legal_mask=legal,
        )

    @staticmethod
    def action_log_probability_and_entropy(
        probabilities: Tensor, actions: Tensor, legal_mask: Tensor
    ) -> tuple[Tensor, Tensor]:
        if probabilities.shape != legal_mask.shape or probabilities.shape[-1] != 6:
            raise ValueError("probabilities/legal_mask must share shape [..., 6]")
        if tuple(actions.shape) != tuple(probabilities.shape[:-1]):
            raise ValueError("actions must match the non-action probability dimensions")
        if actions.dtype not in (torch.int32, torch.int64):
            raise TypeError("actions must use an integer dtype")
        chosen_legal = legal_mask.gather(-1, actions.to(torch.int64)[..., None]).squeeze(-1)
        if not bool(chosen_legal.all().item()):
            raise ValueError("an action is illegal for its public role")
        chosen = probabilities.gather(-1, actions.to(torch.int64)[..., None]).squeeze(-1)
        log_probability = torch.log(chosen)
        entropy = -(probabilities * torch.where(
            legal_mask, torch.log(probabilities.clamp_min(torch.finfo(torch.float32).tiny)),
            torch.zeros_like(probabilities),
        )).sum(dim=-1)
        return log_probability, entropy

    @staticmethod
    def _validate_observations(observations: Tensor) -> None:
        if observations.ndim < 2 or observations.shape[-1] != 22:
            raise ValueError("observations must have shape [..., N, 22]")
        if observations.dtype is not torch.float32:
            raise TypeError("observations must be float32")
        if not bool(torch.isfinite(observations).all().item()):
            raise ValueError("observations contain a nonfinite value")

    @staticmethod
    def _broadcast_roles(roles: Tensor, target_shape: torch.Size) -> Tensor:
        if roles.dtype not in (torch.int32, torch.int64):
            raise TypeError("roles must use an integer dtype")
        if roles.ndim == 1:
            if roles.shape[0] != target_shape[-1]:
                raise ValueError("one-dimensional roles must have length N")
            roles = roles.reshape(*([1] * (len(target_shape) - 1)), roles.shape[0])
        try:
            expanded = roles.expand(target_shape)
        except RuntimeError as exc:
            raise ValueError("roles are not broadcastable to [..., N]") from exc
        if not bool(((expanded >= 0) & (expanded < 3)).all().item()):
            raise ValueError("role labels must be 0, 1, or 2")
        return expanded.to(dtype=torch.int64)


class TerminalCritic(nn.Module):
    """Training-only team critic; absent from actor execution inputs."""

    def __init__(self, parameters: Mapping[str, Tensor]) -> None:
        super().__init__()
        for name, value in _require_parameter_tensors(
            parameters, CRITIC_PARAMETER_SHAPES
        ).items():
            self.register_parameter(name, nn.Parameter(value))

    @staticmethod
    def parameter_count() -> int:
        return sum(
            int(torch.tensor(shape).prod().item())
            for shape in CRITIC_PARAMETER_SHAPES.values()
        )

    def forward(self, rolewise_observation_means: Tensor) -> Tensor:
        if rolewise_observation_means.shape[-1] != 66:
            raise ValueError("critic input must have final dimension 66")
        if rolewise_observation_means.dtype is not torch.float32:
            raise TypeError("critic input must be float32")
        if not bool(torch.isfinite(rolewise_observation_means).all().item()):
            raise ValueError("critic input contains a nonfinite value")
        hidden = torch.tanh(
            F.linear(rolewise_observation_means, self.critic_w1, self.critic_b1)
        )
        hidden = torch.tanh(F.linear(hidden, self.critic_w2, self.critic_b2))
        return F.linear(hidden, self.critic_w3, self.critic_b3).squeeze(-1)


def build_rolewise_critic_input(observations: Tensor, roles: Tensor) -> Tensor:
    """Concatenate three rolewise means without adding private information."""

    if observations.ndim < 2 or observations.shape[-1] != 22:
        raise ValueError("observations must have shape [..., N, 22]")
    expanded_roles = RSCFActor._broadcast_roles(roles, observations.shape[:-1])
    means = []
    for role in range(3):
        mask = (expanded_roles == role).to(dtype=observations.dtype)[..., None]
        count = mask.sum(dim=-2)
        if not bool((count > 0).all().item()):
            raise ValueError("each public role must be present")
        means.append((observations * mask).sum(dim=-2) / count)
    return torch.cat(means, dim=-1)


def policy_contract_audit() -> dict[str, object]:
    """Return deterministic, value-free implementation facts for certificates."""

    return {
        "observation_width": 22,
        "message_width": 32,
        "hidden_width": 64,
        "actor_input_width": 55,
        "union_action_width": 6,
        "role_names": ROLE_NAMES,
        "action_names": ACTION_NAMES,
        "legal_action_indices": ((0, 1, 5), (0, 1, 5), (2, 3, 4, 5)),
        "legal_uniform_floor_mass": 0.04,
        "softmax_mass": 0.96,
        "gru_gate_order": ("z", "r", "n"),
        "gru_reset_before_recurrent_candidate": True,
        "actor_parameter_count": RSCFActor.parameter_count(),
        "critic_parameter_count": TerminalCritic.parameter_count(),
        "joint_parameter_count": RSCFActor.parameter_count()
        + TerminalCritic.parameter_count(),
        "critic_execution_input": False,
        "beta_shape": (3, 3, 2),
    }
