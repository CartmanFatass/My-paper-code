"""Paired recurrent learned arms for exact CRTO-B1 v4.

The two arms have byte-identical tensors at construction and differ only in the
semantic type of the 52-coordinate adapter packet supplied by their caller.
There is intentionally no packet bypass, normalization, or dropout path.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


REVISION = "CRTO-B1-SCIENCE-20260812-04"
OPTION_COUNT = 7
PACKET_DIM = 52
HIDDEN_DIM = 64
ADAPTER_DIM = 32
KEEP_ACTION = 0


class ArmKind(str, Enum):
    CRTO = "CRTO"
    FULL_HISTORY_AUX_TERM = "FULL-HISTORY-AUX-TERM"


class DecisionKind(IntEnum):
    NONE = 0
    INITIAL = 1
    DISCRETIONARY = 2
    FORCED_RENEWAL = 3


def _xavier_uniform(parameter: torch.Tensor, rng: np.random.Generator) -> None:
    if parameter.ndim != 2:
        raise ValueError("registered Xavier initialization requires a matrix")
    fan_out, fan_in = int(parameter.shape[0]), int(parameter.shape[1])
    gain = nn.init.calculate_gain("tanh")
    bound = gain * math.sqrt(6.0 / float(fan_in + fan_out))
    values = rng.uniform(-bound, bound, size=tuple(parameter.shape))
    with torch.no_grad():
        parameter.copy_(torch.as_tensor(values, dtype=parameter.dtype, device=parameter.device))


def _orthogonal_gate(parameter: torch.Tensor, rng: np.random.Generator) -> None:
    if parameter.ndim != 2 or parameter.shape[0] != parameter.shape[1]:
        raise ValueError("GRU recurrent gate must be square")
    raw = rng.standard_normal(tuple(parameter.shape))
    q, r = np.linalg.qr(raw)
    signs = np.sign(np.diag(r))
    signs[signs == 0.0] = 1.0
    q *= signs
    with torch.no_grad():
        parameter.copy_(torch.as_tensor(q, dtype=parameter.dtype, device=parameter.device))


def _initialize_gru_cell(cell: nn.GRUCell, rng: np.random.Generator) -> None:
    _xavier_uniform(cell.weight_ih, rng)
    for gate in range(3):
        _orthogonal_gate(cell.weight_hh[gate * HIDDEN_DIM:(gate + 1) * HIDDEN_DIM], rng)
    with torch.no_grad():
        cell.bias_ih.zero_()
        cell.bias_hh.zero_()


class PacketAdapter(nn.Module):
    """Exact 52 -> 64 -> 32 tanh adapter with no alternate path."""

    def __init__(self) -> None:
        super().__init__()
        self.input_layer = nn.Linear(PACKET_DIM, 64)
        self.output_layer = nn.Linear(64, ADAPTER_DIM)

    def forward(self, packet: torch.Tensor) -> torch.Tensor:
        if packet.shape[-1] != PACKET_DIM:
            raise ValueError("adapter packet must have exactly 52 coordinates")
        return torch.tanh(self.output_layer(torch.tanh(self.input_layer(packet))))


class DecodabilityProbe(nn.Module):
    """Scripted-support-only 52 -> 64 -> 32 -> 24 probe."""

    def __init__(self, algorithm_seed: int) -> None:
        super().__init__()
        self.algorithm_seed = int(algorithm_seed)
        self.layer1 = nn.Linear(52, 64)
        self.layer2 = nn.Linear(64, 32)
        self.layer3 = nn.Linear(32, 24)
        rng = np.random.Generator(np.random.PCG64(610000 + self.algorithm_seed))
        for layer in (self.layer1, self.layer2, self.layer3):
            _xavier_uniform(layer.weight, rng)
            with torch.no_grad():
                layer.bias.zero_()

    def forward(self, raw_packet: torch.Tensor) -> torch.Tensor:
        if raw_packet.shape[-1] != 52:
            raise ValueError("probe input must be the raw 52-coordinate packet")
        hidden64 = torch.tanh(self.layer1(raw_packet))
        hidden32 = torch.tanh(self.layer2(hidden64))
        return self.layer3(hidden32)


@dataclass(frozen=True)
class ActorStep:
    hidden: torch.Tensor
    q: torch.Tensor
    residual_contribution: torch.Tensor
    value: torch.Tensor


class RecurrentOptionActorCritic(nn.Module):
    """Shared 64-GRU option actor, exact adapter head, and centralized value."""

    def __init__(
        self,
        observation_dim: int,
        centralized_state_dim: int,
        algorithm_seed: int,
        arm: ArmKind,
    ) -> None:
        super().__init__()
        if observation_dim <= 0 or centralized_state_dim <= 0:
            raise ValueError("model input dimensions must be positive")
        self.observation_dim = int(observation_dim)
        self.centralized_state_dim = int(centralized_state_dim)
        self.algorithm_seed = int(algorithm_seed)
        self.arm = ArmKind(arm)
        self.actor_gru = nn.GRUCell(self.observation_dim, HIDDEN_DIM)
        self.option_value_head = nn.Linear(HIDDEN_DIM, OPTION_COUNT)
        self.adapter = PacketAdapter()
        self.option_embedding = nn.Parameter(torch.empty(OPTION_COUNT, ADAPTER_DIM))
        self.residual_intercept = nn.Parameter(torch.zeros(()))
        self.central_value_hidden = nn.Linear(self.centralized_state_dim, HIDDEN_DIM)
        self.central_value_output = nn.Linear(HIDDEN_DIM, 1)
        self._initialize_registered()

    def _initialize_registered(self) -> None:
        rng = np.random.Generator(np.random.PCG64(800000 + self.algorithm_seed))
        _initialize_gru_cell(self.actor_gru, rng)
        _xavier_uniform(self.option_value_head.weight, rng)
        _xavier_uniform(self.adapter.input_layer.weight, rng)
        _xavier_uniform(self.adapter.output_layer.weight, rng)
        _xavier_uniform(self.option_embedding, rng)
        _xavier_uniform(self.central_value_hidden.weight, rng)
        _xavier_uniform(self.central_value_output.weight, rng)
        with torch.no_grad():
            self.option_value_head.bias.zero_()
            self.adapter.input_layer.bias.zero_()
            self.adapter.output_layer.bias.zero_()
            self.residual_intercept.zero_()
            self.central_value_hidden.bias.zero_()
            self.central_value_output.bias.zero_()

    def initial_hidden(
        self, agents: int, *, dtype: torch.dtype | None = None, device: torch.device | None = None,
    ) -> torch.Tensor:
        parameter = next(self.parameters())
        return torch.zeros(
            agents,
            HIDDEN_DIM,
            dtype=parameter.dtype if dtype is None else dtype,
            device=parameter.device if device is None else device,
        )

    def forward_step(
        self,
        deployable_observation: torch.Tensor,
        previous_hidden: torch.Tensor,
        centralized_state: torch.Tensor,
        adapter_packet: torch.Tensor,
    ) -> ActorStep:
        if deployable_observation.ndim < 2 or deployable_observation.shape[-1] != self.observation_dim:
            raise ValueError("deployable observation must have shape [...,agents,observation_dim]")
        agent_shape = tuple(deployable_observation.shape[:-1])
        if previous_hidden.shape != (*agent_shape, HIDDEN_DIM):
            raise ValueError("previous actor hidden state must have shape [...,agents,64]")
        if adapter_packet.shape != (*agent_shape, PACKET_DIM):
            raise ValueError("adapter packet must have shape [...,agents,52]")
        batch_shape = agent_shape[:-1]
        if centralized_state.shape != (*batch_shape, self.centralized_state_dim):
            raise ValueError("centralized state has the wrong batch or feature width")
        flat_observation = deployable_observation.reshape(-1, self.observation_dim)
        flat_previous_hidden = previous_hidden.reshape(-1, HIDDEN_DIM)
        hidden = self.actor_gru(flat_observation, flat_previous_hidden).reshape(*agent_shape, HIDDEN_DIM)
        q = self.option_value_head(hidden)
        adapted = self.adapter(adapter_packet)
        residual_contribution = adapted @ self.option_embedding.transpose(0, 1)
        residual_contribution = residual_contribution + self.residual_intercept
        value = self.central_value_output(
            torch.tanh(self.central_value_hidden(centralized_state))
        ).squeeze(-1)
        return ActorStep(hidden, q, residual_contribution, value)

    @staticmethod
    def initial_logits(q: torch.Tensor, legal_mask: torch.Tensor) -> torch.Tensor:
        if q.shape[-1] != OPTION_COUNT or legal_mask.shape != q.shape:
            raise ValueError("initial decision requires matching [...,7] q and mask")
        if not bool(torch.all(legal_mask.any(dim=-1))):
            raise ValueError("initial decision has no legal option")
        return q.masked_fill(~legal_mask.to(torch.bool), -torch.inf)

    @staticmethod
    def discretionary_logits(
        q: torch.Tensor,
        residual_contribution: torch.Tensor,
        current_option: torch.Tensor,
        legal_mask: torch.Tensor,
        replanning_cost: torch.Tensor,
    ) -> torch.Tensor:
        """Return [KEEP, option-0, ..., option-6] relative logits."""

        if q.ndim != 2 or q.shape[1] != OPTION_COUNT or residual_contribution.shape != q.shape:
            raise ValueError("q and residual contribution must have shape [agents,7]")
        agents = q.shape[0]
        if current_option.shape != (agents,) or legal_mask.shape != q.shape:
            raise ValueError("current option/mask shape mismatch")
        if replanning_cost.shape != (agents,):
            raise ValueError("replanning cost must have shape [agents]")
        current = current_option.to(torch.int64)
        if bool(torch.any((current < 0) | (current >= OPTION_COUNT))):
            raise ValueError("current option outside frozen option order")
        current_q = q.gather(1, current.unsqueeze(1))
        replacement = q - current_q - (0.05 + replanning_cost).unsqueeze(1) + residual_contribution
        replacement_mask = legal_mask.to(torch.bool).clone()
        replacement_mask.scatter_(1, current.unsqueeze(1), False)
        replacement = replacement.masked_fill(~replacement_mask, -torch.inf)
        return torch.cat((q.new_zeros((agents, 1)), replacement), dim=1)

    @staticmethod
    def forced_renewal_logits(
        q: torch.Tensor,
        residual_contribution: torch.Tensor,
        current_option: torch.Tensor,
        legal_mask: torch.Tensor,
        replanning_cost: torch.Tensor,
    ) -> torch.Tensor:
        if q.ndim != 2 or q.shape[1] != OPTION_COUNT or residual_contribution.shape != q.shape:
            raise ValueError("q and residual contribution must have shape [agents,7]")
        agents = q.shape[0]
        if current_option.shape != (agents,) or legal_mask.shape != q.shape:
            raise ValueError("current option/mask shape mismatch")
        if replanning_cost.shape != (agents,):
            raise ValueError("replanning cost must have shape [agents]")
        current = current_option.to(torch.int64)
        option_indices = torch.arange(OPTION_COUNT, device=q.device).expand(agents, -1)
        changed = option_indices != current.unsqueeze(1)
        logits = q - 0.05 - changed.to(q.dtype) * replanning_cost.unsqueeze(1) + residual_contribution
        if not bool(torch.all(legal_mask.any(dim=-1))):
            raise ValueError("forced renewal has no legal option")
        return logits.masked_fill(~legal_mask.to(torch.bool), -torch.inf)

    @staticmethod
    def log_probability_and_entropy(
        logits: torch.Tensor, action_index: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if logits.ndim != 2 or action_index.shape != (logits.shape[0],):
            raise ValueError("categorical action shape mismatch")
        log_probabilities = F.log_softmax(logits, dim=-1)
        selected = log_probabilities.gather(1, action_index.to(torch.int64).unsqueeze(1)).squeeze(1)
        if not bool(torch.isfinite(selected).all()):
            raise ValueError("recorded action is illegal under the supplied decision state")
        probabilities = torch.softmax(logits, dim=-1)
        entropy = -(probabilities * torch.where(
            torch.isfinite(log_probabilities), log_probabilities, torch.zeros_like(log_probabilities)
        )).sum(dim=-1)
        return selected, entropy

    @staticmethod
    def locked_action(logits: torch.Tensor, kind: DecisionKind) -> torch.Tensor:
        """Fixed-order argmax; discretionary index zero is KEEP and wins ties."""

        if kind not in (DecisionKind.INITIAL, DecisionKind.DISCRETIONARY, DecisionKind.FORCED_RENEWAL):
            raise ValueError("locked action requires an actual decision kind")
        return torch.argmax(logits, dim=-1)

    @staticmethod
    def sample_action(logits: torch.Tensor, generator: torch.Generator) -> torch.Tensor:
        """Temperature-one categorical draw from an explicitly isolated stream."""

        return torch.multinomial(torch.softmax(logits, dim=-1), 1, generator=generator).squeeze(1)


def build_paired_models(
    observation_dim: int,
    centralized_state_dim: int,
    algorithm_seed: int,
) -> tuple[RecurrentOptionActorCritic, RecurrentOptionActorCritic]:
    """Construct CRTO/FULL with byte-identical corresponding learned tensors."""

    crto = RecurrentOptionActorCritic(
        observation_dim, centralized_state_dim, algorithm_seed, ArmKind.CRTO
    )
    full = copy.deepcopy(crto)
    full.arm = ArmKind.FULL_HISTORY_AUX_TERM
    for name, crto_tensor in crto.state_dict().items():
        full_tensor = full.state_dict()[name]
        if not torch.equal(crto_tensor, full_tensor):
            raise RuntimeError(f"paired initialization diverged at tensor {name}")
    return crto, full


def assert_paired_architecture(
    crto: RecurrentOptionActorCritic, full: RecurrentOptionActorCritic,
) -> None:
    if crto.arm is not ArmKind.CRTO or full.arm is not ArmKind.FULL_HISTORY_AUX_TERM:
        raise ValueError("paired arms have incorrect semantic labels")
    if list(crto.state_dict()) != list(full.state_dict()):
        raise ValueError("paired arms do not have identical parameter structure")
    if sum(p.numel() for p in crto.parameters()) != sum(p.numel() for p in full.parameters()):
        raise ValueError("paired learned arms do not have equal trainable parameter counts")


def trainable_parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def decision_action_index(kind: DecisionKind, selected_option: int, current_option: int) -> int:
    """Map an environment option result to the matching categorical coordinate."""

    if not 0 <= selected_option < OPTION_COUNT:
        raise ValueError("selected option outside frozen option order")
    if kind is DecisionKind.DISCRETIONARY:
        return KEEP_ACTION if selected_option == current_option else selected_option + 1
    if kind in (DecisionKind.INITIAL, DecisionKind.FORCED_RENEWAL):
        return selected_option
    raise ValueError("NONE has no categorical action coordinate")


def exact_immediate_charge(
    kind: DecisionKind,
    selected_option: int,
    current_option: int,
    replanning_cost: float,
) -> float:
    """The indivisible initial/discretionary/forced renewal charge law."""

    if replanning_cost not in (0.25, 4.0):
        raise ValueError("replanning cost must be the frozen low or high value")
    if kind is DecisionKind.INITIAL:
        return 0.0
    if kind is DecisionKind.DISCRETIONARY:
        return 0.0 if selected_option == current_option else 0.05 + replanning_cost
    if kind is DecisionKind.FORCED_RENEWAL:
        return 0.05 + (replanning_cost if selected_option != current_option else 0.0)
    if kind is DecisionKind.NONE:
        return 0.0
    raise ValueError("unknown decision kind")
