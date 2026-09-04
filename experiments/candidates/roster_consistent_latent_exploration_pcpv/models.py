"""Exact 26,545-scalar float64 KEEP/FLEX policy architecture."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import torch
from torch import nn

from . import rng
from .config import beacon_positions, demands
from .host import PublicState, circular_displacement, sector_encoding

torch.set_default_dtype(torch.float64)


class MLP(nn.Module):
    def __init__(self, widths: Iterable[int], activate_last: bool = False):
        super().__init__()
        values = tuple(widths)
        self.layers = nn.ModuleList(nn.Linear(a, b, dtype=torch.float64)
                                    for a, b in zip(values, values[1:]))
        self.activate_last = activate_last

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        for index, layer in enumerate(self.layers):
            value = layer(value)
            if index < len(self.layers) - 1 or self.activate_last:
                value = torch.tanh(value)
        return value


class PCPVPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.agent_encoder = MLP((6, 32, 32), activate_last=True)
        self.beacon_encoder = MLP((3, 32, 32), activate_last=True)
        self.manager_body = MLP((68, 64, 64), activate_last=True)
        self.manager_mean = nn.Linear(64, 4, dtype=torch.float64)
        self.manager_raw_scale = nn.Linear(64, 4, dtype=torch.float64)
        self.pointer = MLP((84, 64, 64, 1))
        self.common_event = MLP((72, 32, 4))
        self.agent_event = MLP((84, 32, 4))

    def public_summary(self, state: PublicState) -> torch.Tensor:
        agent = torch.as_tensor(state.agent_elements(), dtype=torch.float64)
        agent_pool = self.agent_encoder(agent).mean(0)
        beacons = torch.as_tensor([
            (*sector_encoding(q), d / 3.0)
            for q, d in zip(beacon_positions(state.tick), demands(state.n, state.tick))
        ], dtype=torch.float64)
        beacon_pool = self.beacon_encoder(beacons).mean(0)
        flags = torch.tensor((state.n / 10.0, state.tick / 56.0,
                              state.roster_event, state.post_boundary),
                             dtype=torch.float64)
        return torch.cat((agent_pool, beacon_pool, flags))

    def manager(self, summary: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self.manager_body(summary)
        mean = self.manager_mean(hidden)
        raw = self.manager_raw_scale(hidden)
        log_scale = -2.0 + 2.0 * torch.sigmoid(raw)
        return mean, log_scale

    def action_logits(self, state: PublicState, key: int, summary: torch.Tensor,
                      plan: torch.Tensor) -> torch.Tensor:
        pooled = summary[:64]
        own = torch.as_tensor(state.own_features(key), dtype=torch.float64)
        flags = summary[64:]
        candidates = []
        for beacon, (q, d) in enumerate(zip(beacon_positions(state.tick),
                                             demands(state.n, state.tick))):
            candidate = torch.tensor((
                *sector_encoding(q), d / 3.0,
                circular_displacement(state.entities[key].position, q) / 40.0,
            ), dtype=torch.float64)
            # The manager draw is already stopped when it is created.  Do not
            # detach here: FLEX event deltas must retain their downstream
            # score-function connectivity to the pointer likelihood.
            candidates.append(torch.cat((pooled, own, flags, candidate, plan)))
        return self.pointer(torch.stack(candidates)).squeeze(-1)

    def event_plan(self, summary: torch.Tensor, own: torch.Tensor,
                   old_plan: torch.Tensor, noise: torch.Tensor,
                   clamp: bool = False) -> torch.Tensor:
        if clamp:
            return old_plan
        common = self.common_event(torch.cat((old_plan.detach(), summary)))
        agent = self.agent_event(torch.cat((old_plan.detach(), summary, own, noise)))
        return old_plan + common + agent


def initialize(policy: PCPVPolicy, root: int) -> None:
    label = rng.root_label(root)
    event_outputs = {
        "common_event.layers.1.weight", "agent_event.layers.1.weight"
    }
    with torch.no_grad():
        for name, parameter in policy.named_parameters():
            if name.endswith("bias") or name in event_outputs:
                parameter.zero_()
                continue
            fan_out, fan_in = parameter.shape
            bound = math.sqrt(6.0 / (fan_in + fan_out))
            flat = parameter.view(-1)
            for index in range(flat.numel()):
                u = rng.uniform(label, "common", "parameter", name, "entry", index)
                flat[index] = (2.0 * u - 1.0) * bound


def paired_policies(root: int) -> tuple[PCPVPolicy, PCPVPolicy]:
    keep = PCPVPolicy()
    initialize(keep, root)
    flex = PCPVPolicy()
    flex.load_state_dict(keep.state_dict())
    return keep, flex


def parameter_count(policy: nn.Module) -> int:
    return sum(parameter.numel() for parameter in policy.parameters())


def inverse_cdf_action(probabilities: torch.Tensor, u: float) -> int:
    cumulative = torch.cumsum(probabilities.detach(), dim=-1).cpu().numpy()
    return int(np.searchsorted(cumulative, u, side="right").clip(0, 3))
