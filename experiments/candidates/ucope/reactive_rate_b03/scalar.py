"""Input-independent learned KEEP/END probabilities for the B arm."""

import copy

import torch
from torch import nn


class ScalarGate(nn.Module):
    """Two global trainable logits broadcast over any eligible input rows."""

    def __init__(self):
        super().__init__()
        self.logits = nn.Parameter(torch.zeros(2))

    def forward(self, inputs):
        return self.logits.expand(*inputs.shape[:-1], 2)


def scalar_actor(common):
    """Copy common actor/critic state and add only the two scalar logits."""
    actor, critic = copy.deepcopy(common)
    actor.duration_conditioned = True
    actor.duration = ScalarGate()
    return actor, critic
