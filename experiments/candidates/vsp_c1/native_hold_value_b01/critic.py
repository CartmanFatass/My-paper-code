"""Full source MLP plus a zero-initialized remaining-hold gate."""
import copy

import torch
from torch import nn
from torch.nn import functional as F

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import arm_copy, exposure

R_COLUMNS = (119, 123, 127, 131, 135)
X_COLUMNS = tuple(i for i in range(136) if i not in R_COLUMNS)


class GatedCritic(nn.Module):
    def __init__(self, source):
        super().__init__()
        self.network = copy.deepcopy(source.network)
        # Construct the parameter directly: no random Linear initializer is called.
        self.gate = nn.Parameter(torch.zeros(128, 5))

    def forward(self, inputs):
        first = self.network[0]
        r = inputs[..., R_COLUMNS]
        z = F.linear(inputs[..., X_COLUMNS], first.weight[:, X_COLUMNS], first.bias)
        br = F.linear(r, first.weight[:, R_COLUMNS])
        hidden = torch.tanh(z * (1 + F.linear(r, self.gate)) + br)
        return self.network[4](torch.tanh(self.network[2](hidden))).squeeze(-1)


def models(common, arm, second_mlp_width=128, extra_init_seed=None):
    actor, critic = arm_copy(common, True)
    if arm == "GATED-V":
        critic = GatedCritic(critic)
    elif second_mlp_width == 133:
        from experiments.candidates.vsp_c1.native_hold_value_b05.critic import WideCritic
        critic = WideCritic(critic, extra_init_seed)
    return actor, critic


def movement(initial, actor, critic):
    result = exposure(initial, actor, critic)
    if isinstance(critic, GatedCritic):
        norm = float(critic.gate.detach().norm())
        result["gate"] = dict(parameters=640, initial_norm=0., final_norm=norm,
                              displacement=norm, relative_displacement=None,
                              reason="undefined: gate initial norm is zero")
    return result
