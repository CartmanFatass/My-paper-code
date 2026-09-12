"""Identically informed DENSE actors, with one selected capability residual."""
import math

import torch
from torch import nn

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Critic, snapshot


class DenseEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.raw = nn.Linear(118, 64)
        self.hidden = nn.Linear(118, 16)
        self.context = nn.Linear(16, 64, bias=False)
        nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.context.weight)

    def forward(self, observations):
        return self.raw(observations) + self.context(torch.tanh(self.hidden(observations)))


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = DenseEncoder()
        self.gru = nn.GRU(64, 64)
        self.mean = nn.Linear(64, 3)
        self.log_std = nn.Parameter(torch.zeros(3))
        self.duration = None
        self.duration_conditioned = False
        self.adapter_a = None
        self.adapter_b = None

    def forward(self, observations, hidden):
        # Collector layout: native104, capability5, own-ID5, command3, remaining1.
        # Both DENSE paths receive the same canonical native108 + public10 layout.
        canonical = torch.cat((observations[..., :104], observations[..., 114:],
                               observations[..., 104:114]), dim=-1)
        output, hidden = self.gru(torch.tanh(self.encoder(canonical)), hidden)
        mean = self.mean(output)
        if self.adapter_a is not None:
            own_capability = (observations[..., 104:109] * observations[..., 109:114]).sum(-1)
            index = ((own_capability - .5) * 4).long()
            projected = torch.einsum("...ij,...j->...i", self.adapter_b[index], output)
            mean = mean + torch.einsum("...ij,...j->...i", self.adapter_a[index], projected.tanh())
        return mean, output, hidden


def build_arm(master, arm):
    # Each distinct invocation constructs exactly one actor and one critic.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 11)
        actor, critic = Actor(), Critic()
    if arm == "ACPS":
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(100000 * master + 12)
            actor.adapter_b = nn.Parameter(torch.empty(5, 4, 64).uniform_(
                -1 / math.sqrt(64), 1 / math.sqrt(64)))
            actor.adapter_a = nn.Parameter(torch.zeros(5, 3, 4))
    elif arm != "SHARED":
        raise ValueError(arm)
    return actor, critic


def parameter_snapshot(actor, critic):
    values = snapshot(actor, critic)
    if actor.adapter_a is not None:
        values["adapter_a"] = actor.adapter_a.detach().flatten().clone()
        values["adapter_b"] = actor.adapter_b.detach().flatten().clone()
    return values


def movement(initial, actor, critic):
    final = parameter_snapshot(actor, critic)
    result = {}
    for name, start in initial.items():
        norm = float(start.norm())
        displacement = float((final[name] - start).norm())
        result[name] = dict(parameters=start.numel(), initial_norm=norm,
                            final_norm=float(final[name].norm()), displacement=displacement,
                            relative_displacement=displacement / norm if norm else None)
    return result
