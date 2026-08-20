"""Matched SGSP actors, custom reset-before-matrix GRU, and team critic."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Literal

import torch
from torch import nn
from torch.nn import functional as F

from .authorization import ProductionPermit, require_active_permit
from .config import (
    ACTION_DIM,
    ACTOR_HIDDEN_DIM,
    ACTOR_INPUT_DIM,
    CRITIC_HIDDEN_DIM,
    CRITIC_INPUT_DIM,
    EDGE_BETA_BOUND,
    KERNEL_EPSILON,
    LATENCY,
    LOAD_LOGIT_SLOPE,
    MESSAGE_DIM,
    MESSAGE_HIDDEN_DIM,
    OBSERVATION_DIM,
    P0,
    PHY_BETA_BOUND,
    POLICY_SOFTMAX_WEIGHT,
    POLICY_UNIFORM_WEIGHT,
    ROLE_MULTIPLICITIES,
    ROTATED_PHYSICAL_COLUMN_SOURCE,
    Role,
    TRAINING_DTYPE,
    legal_action_indices,
)
from .rng import CounterRNG


KernelCondition = Literal["intact", "rotated"]
ArmName = Literal["PHY-TRUST", "EDGE-FLEX"]


class ExactLinear(nn.Module):
    """An affine layer with no implicit library RNG or delegated initializer."""

    def __init__(self, in_features: int, out_features: int) -> None:
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(
            torch.zeros((out_features, in_features), dtype=TRAINING_DTYPE)
        )
        self.bias = nn.Parameter(torch.zeros(out_features, dtype=TRAINING_DTYPE))

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return F.linear(value, self.weight, self.bias)


@dataclass(frozen=True)
class ActorStep:
    probabilities: torch.Tensor
    hidden: torch.Tensor
    messages: torch.Tensor
    role_denominators: torch.Tensor


class SemanticActor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder_input = ExactLinear(OBSERVATION_DIM, MESSAGE_HIDDEN_DIM)
        self.encoder_output = ExactLinear(MESSAGE_HIDDEN_DIM, MESSAGE_DIM)

        self.W_z = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM, ACTOR_INPUT_DIM))
        self.W_r = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM, ACTOR_INPUT_DIM))
        self.W_n = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM, ACTOR_INPUT_DIM))
        self.U_z = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM, ACTOR_HIDDEN_DIM))
        self.U_r = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM, ACTOR_HIDDEN_DIM))
        self.U_n = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM, ACTOR_HIDDEN_DIM))
        self.b_z = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM))
        self.b_r = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM))
        self.b_n = nn.Parameter(torch.zeros(ACTOR_HIDDEN_DIM))
        self.actor_output = ExactLinear(ACTOR_HIDDEN_DIM, ACTION_DIM)
        self.beta = nn.Parameter(torch.zeros(3, 3, 2, dtype=TRAINING_DTYPE))

        self.register_buffer("physical_p0", torch.tensor(P0, dtype=TRAINING_DTYPE))
        self.register_buffer("physical_latency", torch.tensor(LATENCY, dtype=TRAINING_DTYPE))

    def zero_hidden(self, n_agents: int) -> torch.Tensor:
        return torch.zeros((n_agents, ACTOR_HIDDEN_DIM), dtype=TRAINING_DTYPE)

    def encode_messages(self, observations: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.encoder_output(torch.tanh(self.encoder_input(observations))))

    @staticmethod
    def _v(sender_count: int) -> float:
        return (2.0 * math.log(sender_count) - math.log(14.0)) / math.log(7.0 / 2.0)

    def _physical_kernel(
        self, receiver_role: int, sender_role: int, sender_count: int, condition: KernelCondition
    ) -> torch.Tensor:
        physical_sender = (
            sender_role if condition == "intact"
            else ROTATED_PHYSICAL_COLUMN_SOURCE[sender_role]
        )
        p0 = self.physical_p0[receiver_role, physical_sender]
        probability = torch.sigmoid(
            torch.logit(p0) - LOAD_LOGIT_SLOPE * float(sender_count - 1)
        )
        return probability / self.physical_latency[receiver_role, physical_sender]

    def role_summary(
        self,
        messages: torch.Tensor,
        roles: torch.Tensor,
        condition: KernelCondition = "intact",
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if condition not in ("intact", "rotated"):
            raise ValueError(f"unknown kernel condition: {condition}")
        counts = [int(torch.sum(roles == role).item()) for role in range(3)]
        if any(count not in ROLE_MULTIPLICITIES for count in counts) or len(set(counts)) != 1:
            raise ValueError("kernel summaries require one registered balanced roster")
        role_sums = torch.stack(
            [torch.sum(messages[roles == role], dim=0) for role in range(3)], dim=0
        )

        summaries: list[torch.Tensor] = []
        denominators: list[torch.Tensor] = []
        for receiver_role in range(3):
            numerator = torch.zeros(MESSAGE_DIM, dtype=messages.dtype, device=messages.device)
            denominator = torch.zeros((), dtype=messages.dtype, device=messages.device)
            for sender_role in range(3):
                count = counts[sender_role]
                residual = (
                    self.beta[receiver_role, sender_role, 0]
                    + self.beta[receiver_role, sender_role, 1] * self._v(count)
                )
                omega = self._physical_kernel(
                    receiver_role, sender_role, count, condition
                ) * torch.exp(residual)
                numerator = numerator + omega * role_sums[sender_role]
                denominator = denominator + count * omega
            summaries.append(numerator / (denominator + KERNEL_EPSILON))
            denominators.append(denominator)

        role_summary = torch.stack(summaries, dim=0)
        role_denominator = torch.stack(denominators, dim=0)
        return role_summary[roles], role_denominator[roles]

    def gru_step(self, actor_input: torch.Tensor, previous_hidden: torch.Tensor) -> torch.Tensor:
        z = torch.sigmoid(
            F.linear(actor_input, self.W_z, self.b_z)
            + F.linear(previous_hidden, self.U_z, None)
        )
        r = torch.sigmoid(
            F.linear(actor_input, self.W_r, self.b_r)
            + F.linear(previous_hidden, self.U_r, None)
        )
        candidate = torch.tanh(
            F.linear(actor_input, self.W_n, self.b_n)
            + F.linear(r * previous_hidden, self.U_n, None)
        )
        return (1.0 - z) * candidate + z * previous_hidden

    def _legal_probabilities(self, logits: torch.Tensor, roles: torch.Tensor) -> torch.Tensor:
        legal = torch.zeros_like(logits, dtype=torch.bool)
        for role in Role:
            role_rows = roles == int(role)
            for action in legal_action_indices(role):
                legal[role_rows, action] = True
        masked_logits = logits.masked_fill(~legal, -torch.inf)
        softmax = torch.softmax(masked_logits, dim=-1)
        legal_count = legal.sum(dim=-1, keepdim=True).to(logits.dtype)
        floor = legal.to(logits.dtype) * (POLICY_UNIFORM_WEIGHT / legal_count)
        probabilities = POLICY_SOFTMAX_WEIGHT * softmax + floor
        return probabilities.masked_fill(~legal, 0.0)

    def forward_step(
        self,
        observations: torch.Tensor,
        roles: torch.Tensor,
        previous_hidden: torch.Tensor,
        condition: KernelCondition = "intact",
    ) -> ActorStep:
        messages = self.encode_messages(observations)
        summary, denominator = self.role_summary(messages, roles, condition)
        actor_input = torch.cat((observations, summary, denominator.unsqueeze(-1)), dim=-1)
        hidden = self.gru_step(actor_input, previous_hidden)
        probabilities = self._legal_probabilities(self.actor_output(hidden), roles)
        return ActorStep(probabilities, hidden, messages, denominator)

    def shadow_rotated_probabilities(
        self,
        observations: torch.Tensor,
        roles: torch.Tensor,
        incoming_hidden: torch.Tensor,
    ) -> torch.Tensor:
        # The incoming state and intact predecision local observations remain
        # fixed; the one alternative update is not propagated by this method.
        return self.forward_step(
            observations, roles, incoming_hidden, condition="rotated"
        ).probabilities


class TeamCritic(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.hidden_1 = ExactLinear(CRITIC_INPUT_DIM, CRITIC_HIDDEN_DIM)
        self.hidden_2 = ExactLinear(CRITIC_HIDDEN_DIM, CRITIC_HIDDEN_DIM)
        self.output = ExactLinear(CRITIC_HIDDEN_DIM, 1)

    @staticmethod
    def team_state(observations: torch.Tensor, roles: torch.Tensor) -> torch.Tensor:
        means = [torch.mean(observations[roles == role], dim=0) for role in range(3)]
        return torch.cat(means, dim=0)

    def forward(self, team_state: torch.Tensor) -> torch.Tensor:
        hidden = torch.tanh(self.hidden_1(team_state))
        hidden = torch.tanh(self.hidden_2(hidden))
        return self.output(hidden).squeeze(-1)


class ArmModel(nn.Module):
    def __init__(self, arm_name: ArmName) -> None:
        super().__init__()
        if arm_name not in ("PHY-TRUST", "EDGE-FLEX"):
            raise ValueError(f"unknown learned arm: {arm_name}")
        self.arm_name: ArmName = arm_name
        self.actor = SemanticActor()
        self.critic = TeamCritic()

    @property
    def beta_bound(self) -> float:
        return PHY_BETA_BOUND if self.arm_name == "PHY-TRUST" else EDGE_BETA_BOUND

    def project_beta_(self) -> None:
        with torch.no_grad():
            self.actor.beta.clamp_(-self.beta_bound, self.beta_bound)


def _fill_affine(
    layer: ExactLinear,
    rng: CounterRNG,
    seed: int,
    name: str,
    gain: float,
) -> None:
    bound = gain * math.sqrt(6.0 / (layer.in_features + layer.out_features))
    with torch.no_grad():
        layer.weight.copy_(
            rng.uniform_tensor(
                layer.weight.shape,
                -bound,
                bound,
                "phase", "initialization",
                "training_seed", seed,
                "parameter", name,
                "random-variable-kind", "affine-uniform",
            )
        )
        layer.bias.zero_()


def _fill_gru_matrix(
    parameter: nn.Parameter,
    rng: CounterRNG,
    seed: int,
    name: str,
    recurrent: bool,
) -> None:
    with torch.no_grad():
        if recurrent:
            matrix = rng.normal_tensor(
                parameter.shape,
                "phase", "initialization",
                "training_seed", seed,
                "parameter", name,
                "random-variable-kind", "orthogonal-normal",
            )
            q, r = torch.linalg.qr(matrix)
            diagonal = torch.diagonal(r)
            signs = torch.where(diagonal < 0.0, -torch.ones_like(diagonal), torch.ones_like(diagonal))
            parameter.copy_(q * signs.unsqueeze(0))
        else:
            fan_out, fan_in = parameter.shape
            bound = math.sqrt(6.0 / (fan_in + fan_out))
            parameter.copy_(
                rng.uniform_tensor(
                    parameter.shape,
                    -bound,
                    bound,
                    "phase", "initialization",
                    "training_seed", seed,
                    "parameter", name,
                    "random-variable-kind", "affine-uniform",
                )
            )


def initialize_model_(
    permit: ProductionPermit,
    model: ArmModel,
    seed: int,
    rng: CounterRNG | None = None,
) -> None:
    """Materialize the frozen addressed initialization for one common model."""
    require_active_permit(permit)
    permit.require_seed(seed)
    rng = rng or CounterRNG(permit)
    rng.require_same_permit(permit)
    actor = model.actor
    _fill_affine(actor.encoder_input, rng, seed, "encoder-input", 1.0)
    _fill_affine(actor.encoder_output, rng, seed, "encoder-output", 1.0)
    _fill_affine(actor.actor_output, rng, seed, "actor-output", 0.01)
    for gate in ("z", "r", "n"):
        _fill_gru_matrix(getattr(actor, f"W_{gate}"), rng, seed, f"gru-W-{gate}", False)
        _fill_gru_matrix(getattr(actor, f"U_{gate}"), rng, seed, f"gru-U-{gate}", True)
    _fill_affine(model.critic.hidden_1, rng, seed, "critic-hidden-1", 1.0)
    _fill_affine(model.critic.hidden_2, rng, seed, "critic-hidden-2", 1.0)
    _fill_affine(model.critic.output, rng, seed, "critic-output", 1.0)
    with torch.no_grad():
        actor.b_z.zero_()
        actor.b_r.zero_()
        actor.b_n.zero_()
        actor.beta.zero_()


def make_paired_models(
    permit: ProductionPermit,
    seed: int,
    rng: CounterRNG | None = None,
) -> tuple[ArmModel, ArmModel]:
    """Initialize once, then bitwise-copy into separately owned learned arms."""
    require_active_permit(permit)
    permit.require_seed(seed)
    template = ArmModel("PHY-TRUST")
    initialize_model_(permit, template, seed, rng)
    edge = copy.deepcopy(template)
    edge.arm_name = "EDGE-FLEX"
    return template, edge
