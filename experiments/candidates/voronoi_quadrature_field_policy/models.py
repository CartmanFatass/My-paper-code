"""Exact 40,996-parameter policy/critic definitions for both frozen arms."""

from __future__ import annotations

from enum import Enum
import math

import torch
from torch import nn
from torch.nn import functional as F

from .geometry import wrap_signed


class Arm(str, Enum):
    VQFP = "vqfp"
    LEARNED = "learned"


def _xavier(weight: torch.Tensor) -> None:
    nn.init.xavier_uniform_(weight, gain=1.0)


class ResetAfterGRU(nn.Module):
    """The exact PyTorch-style reset-after GRU equation frozen by the card."""

    def __init__(self) -> None:
        super().__init__()
        self.W_ir = nn.Parameter(torch.empty(64, 39))
        self.W_iz = nn.Parameter(torch.empty(64, 39))
        self.W_in = nn.Parameter(torch.empty(64, 39))
        self.W_hr = nn.Parameter(torch.empty(64, 64))
        self.W_hz = nn.Parameter(torch.empty(64, 64))
        self.W_hn = nn.Parameter(torch.empty(64, 64))
        self.b_ir = nn.Parameter(torch.zeros(64))
        self.b_iz = nn.Parameter(torch.zeros(64))
        self.b_in = nn.Parameter(torch.zeros(64))
        self.b_hr = nn.Parameter(torch.zeros(64))
        self.b_hz = nn.Parameter(torch.zeros(64))
        self.b_hn = nn.Parameter(torch.zeros(64))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for matrix in (self.W_ir, self.W_iz, self.W_in):
            _xavier(matrix)
        for matrix in (self.W_hr, self.W_hz, self.W_hn):
            nn.init.orthogonal_(matrix, gain=1.0)
        for bias in (self.b_ir, self.b_iz, self.b_in, self.b_hr, self.b_hz, self.b_hn):
            nn.init.zeros_(bias)

    def forward(self, x: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
        r = torch.sigmoid(F.linear(x, self.W_ir, self.b_ir) + F.linear(u, self.W_hr, self.b_hr))
        z = torch.sigmoid(F.linear(x, self.W_iz, self.b_iz) + F.linear(u, self.W_hz, self.b_hz))
        n = torch.tanh(F.linear(x, self.W_in, self.b_in) + r * F.linear(u, self.W_hn, self.b_hn))
        return (1.0 - z) * n + z * u


class VQFPModel(nn.Module):
    """Shared-parameter actor and centralized training-only critic for one arm."""

    def __init__(self, arm: Arm) -> None:
        super().__init__()
        self.arm = Arm(arm)
        self.edge_q = nn.Linear(11, 64)
        self.edge_value = nn.Linear(64, 31)
        self.edge_gate = nn.Linear(64, 1)
        self.gru = ResetAfterGRU()
        self.actor_trunk = nn.Linear(64, 64)
        self.actor_head = nn.Linear(64, 3)
        self.critic_embed1 = nn.Linear(8, 64)
        self.critic_embed2 = nn.Linear(64, 64)
        self.critic_global1 = nn.Linear(72, 64)
        self.critic_global2 = nn.Linear(64, 64)
        self.critic_head = nn.Linear(64, 1)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for layer in (
            self.edge_q, self.edge_value, self.actor_trunk, self.actor_head,
            self.critic_embed1, self.critic_embed2, self.critic_global1,
            self.critic_global2, self.critic_head,
        ):
            _xavier(layer.weight)
            nn.init.zeros_(layer.bias)
        # The executed gate is the deliberately zero-initialized nested-rule port.
        nn.init.zeros_(self.edge_gate.weight)
        nn.init.zeros_(self.edge_gate.bias)

    @property
    def nominal_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def assert_frozen_parameter_count(self) -> None:
        if self.nominal_parameter_count != 40_996:
            raise RuntimeError(f"expected 40,996 nominal parameters, found {self.nominal_parameter_count}")

    @staticmethod
    def effort_token(previous: torch.Tensor) -> torch.Tensor:
        """Encode START=-1 and effort indices 0,1,2 as the registered four-way token."""
        return F.one_hot((previous + 1).long(), num_classes=4).to(dtype=torch.float32)

    def edge_inputs(self, positions: torch.Tensor, gaps: torch.Tensor, predecessor: torch.Tensor,
                    triplets: torch.Tensor, signal: torch.Tensor, previous: torch.Tensor) -> torch.Tensor:
        """Construct receiver/sender edges in the fixed PREV, SELF, NEXT order."""
        sender = triplets
        n = positions.numel()
        recv = torch.arange(n, device=positions.device)[:, None].expand_as(sender)
        sender_x = positions[sender]
        displacement = wrap_signed(sender_x - positions[recv]).unsqueeze(-1)
        # For each sender j the two geometry terms are g_(j-1) and g_j.
        predecessor_gap = gaps[predecessor[sender]]
        s = signal[sender].unsqueeze(-1)
        prev_token = self.effort_token(previous[sender])
        slots = F.one_hot(torch.arange(3, device=positions.device), num_classes=3).to(torch.float32).unsqueeze(0).expand(n, -1, -1)
        return torch.cat((s, prev_token, displacement, predecessor_gap.unsqueeze(-1), gaps[sender].unsqueeze(-1), slots), dim=-1)

    def aggregate(self, edge_input: torch.Tensor, incoming_volumes: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return weighted message, raw mass coordinate and residual gate output."""
        q = torch.tanh(self.edge_q(edge_input))
        w = torch.tanh(self.edge_value(q))
        h = torch.cat((edge_input[..., :1], w), dim=-1)
        ell = self.edge_gate(q).squeeze(-1)  # executed in both arms; VQFP has no loss route from it.
        local_volume = incoming_volumes.sum(dim=-1, keepdim=True)
        if self.arm is Arm.VQFP:
            alpha = incoming_volumes / local_volume
        else:
            alpha = torch.softmax(torch.log(incoming_volumes) + ell, dim=-1)
        message = local_volume * torch.sum(alpha.unsqueeze(-1) * h, dim=-2)
        return message, message[..., 0], ell

    def actor(self, edge_input: torch.Tensor, incoming_volumes: torch.Tensor, n: int,
              hidden: torch.Tensor, *, self_signal: torch.Tensor | None = None,
              self_previous: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        message, raw_mass, gate = self.aggregate(edge_input, incoming_volumes)
        # These receiver-local observations are not part of the permuted sender set.
        self_signal = edge_input[:, 1, 0:1] if self_signal is None else self_signal
        self_previous = edge_input[:, 1, 1:5] if self_previous is None else self_previous
        local_volume = incoming_volumes.sum(dim=-1, keepdim=True)
        n_context = torch.full_like(local_volume, float(n) / 16.0)
        actor_input = torch.cat((message, local_volume, n_context, self_signal, self_previous), dim=-1)
        next_hidden = self.gru(actor_input, hidden)
        logits = self.actor_head(torch.tanh(self.actor_trunk(next_hidden)))
        return logits, next_hidden, raw_mass, gate

    def critic(self, positions: torch.Tensor, volumes: torch.Tensor, signal: torch.Tensor,
               previous: torch.Tensor, n: int, tick: int, phi1: torch.Tensor, phi2: torch.Tensor,
               omega1: float, omega2: float) -> torch.Tensor:
        position_features = torch.stack((torch.sin(2 * math.pi * positions), torch.cos(2 * math.pi * positions)), -1)
        local = torch.cat((position_features, volumes[:, None], signal[:, None], self.effort_token(previous)), -1)
        embedded = torch.tanh(self.critic_embed2(torch.tanh(self.critic_embed1(local))))
        pooled = torch.sum(volumes[:, None] * embedded, dim=0)
        theta1, theta2 = phi1 + omega1 * tick, phi2 + omega2 * tick
        global_input = torch.cat((pooled, pooled.new_tensor((n / 16.0, tick / 31.0,
            math.sin(2 * math.pi * float(theta1)), math.cos(2 * math.pi * float(theta1)),
            math.sin(2 * math.pi * float(theta2)), math.cos(2 * math.pi * float(theta2)),
            128.0 * omega1, 256.0 * omega2))), dim=0)
        return self.critic_head(torch.tanh(self.critic_global2(torch.tanh(self.critic_global1(global_input))))).squeeze(-1)


def copy_common_initialization(source: VQFPModel, destination: VQFPModel) -> None:
    """Pair arms at initialization, including the two zero gate parameters."""
    destination.load_state_dict(source.state_dict())
