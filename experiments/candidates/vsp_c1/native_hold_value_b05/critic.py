"""Ordinary 136->128->133->1 critic with the common initial value function."""
import copy
import math

import torch
from torch import nn


class WideCritic(nn.Module):
    def __init__(self, source, extra_init_seed):
        super().__init__()
        self.network = copy.deepcopy(source.network)
        rng = torch.Generator(device="cpu").manual_seed(extra_init_seed)
        bound = 1 / math.sqrt(128)
        rows = torch.empty(5, 128, dtype=torch.float32).uniform_(-bound, bound, generator=rng)
        biases = torch.empty(5, dtype=torch.float32).uniform_(-bound, bound, generator=rng)
        second, output = self.network[2], self.network[4]
        second.weight = nn.Parameter(torch.cat((second.weight.detach(), rows)))
        second.bias = nn.Parameter(torch.cat((second.bias.detach(), biases)))
        second.out_features = 133
        output.weight = nn.Parameter(torch.cat((output.weight.detach(), torch.zeros(1, 5)), dim=1))
        output.in_features = 133

    def forward(self, inputs):
        return self.network(inputs).squeeze(-1)
